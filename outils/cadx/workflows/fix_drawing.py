from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..core.config import load_config
from ..llm.factory import create_client
from ..llm.schemas import Message
from ..mcp.registry import ToolRegistry
from ..mcp.runtime import McpRuntime
from ..storage.run_store import create_run_context
from ..storage.artifact_store import save_artifact
from ..tools import register_all_tools
from ..tools.cad.session import set_backend
from ..tools.cad.com_backend import ComCadBackend
from ..tools.cad.mock_backend import MockCadBackend


def run_fix(prompt: str | None = None) -> int:
    config = load_config()
    run_ctx = create_run_context()

    backend_mode = (config.cad_backend or "").lower()
    if backend_mode == "com":
        set_backend(ComCadBackend(config))
    else:
        print("[WARN] cad_backend=mock，将不会连接真实 AutoCAD。可设置 CADX_CAD_BACKEND=com。", flush=True)
        set_backend(MockCadBackend())

    registry = ToolRegistry()
    register_all_tools(registry, config)
    runtime = McpRuntime(registry)
    client = create_client(config)

    if not prompt:
        prompt = _read_stdin_or_input()
    system_text = _load_system_prompt()

    print("[LLM] 正在思考...", flush=True)
    use_json_mode = config.llm_json_mode or (config.llm_provider or "").lower() == "glm"
    payload = _request_fix_json(client, system_text, prompt, json_mode=use_json_mode)
    patch = payload.get("patch")
    lisp_path = payload.get("lisp_path")
    entry_command = _normalize_entry_command(payload.get("entry_command") or "")

    if not isinstance(patch, dict):
        raise ValueError("patch is required")

    save_artifact(run_ctx, "patch", "patch.json", content=json.dumps(patch, ensure_ascii=False, indent=2))
    _call_tool(runtime, "file_patch", {"patch": patch})

    if lisp_path:
        lisp_path = str(_resolve_lisp_path(lisp_path))
        connect_args: dict[str, Any] = {"launch": True, "launch_timeout": 180}
        if config.autocad_exec:
            connect_args["exec_path"] = config.autocad_exec
        _call_tool(runtime, "cad_connect", connect_args)
        _call_tool(runtime, "cad_log_control", {"enable": True, "log_path": str(run_ctx.run_dir / "logs")})
        _call_tool(runtime, "cad_lisp_run", {"path": lisp_path})
        if entry_command:
            _call_tool(runtime, "cad_command", {"command": entry_command, "auto_finish": True})
            time.sleep(1.0)
        img_path = run_ctx.run_dir / "exports" / f"{run_ctx.run_id}.jpg"
        _call_tool(
            runtime,
            "cad_export_image",
            {"format": "jpg", "path": str(img_path), "auto_zoom_extents": True},
        )
        entities = _call_tool(runtime, "cad_entity_extract", {}).get("entities", [])
        log_text = _call_tool(runtime, "cad_log_read", {"max_lines": 200}).get("content", "")
        save_artifact(run_ctx, "report", "entities.json", content=json.dumps(entities, ensure_ascii=False, indent=2))
        save_artifact(run_ctx, "report", "log.txt", content=log_text)

    save_artifact(run_ctx, "report", "fix_summary.md", content=payload.get("summary", "修复完成"))
    print("修复完成")
    print(f"run_id: {run_ctx.run_id}")
    return 0


def _read_stdin_or_input() -> str:
    import sys

    if not sys.stdin.isatty():
        text = sys.stdin.read().strip()
        if text:
            return text
    return input("请输入问题描述：").strip()


def _load_system_prompt() -> str:
    prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
    system_path = prompts_dir / "system.md"
    tool_path = prompts_dir / "tool_instructions.md"
    parts: list[str] = []
    if system_path.exists():
        parts.append(system_path.read_text(encoding="utf-8"))
    if tool_path.exists():
        parts.append(tool_path.read_text(encoding="utf-8"))
    return "\n\n".join(p.strip() for p in parts if p.strip())


def _request_fix_json(client, system_text: str, user_text: str, json_mode: bool = False) -> dict[str, Any]:
    instructions = (
        "你必须只输出严格 JSON，包含字段：patch, lisp_path, entry_command, summary。"
        "patch 需要符合 file_patch 工具的格式。"
        "lisp_path 为待修复 LISP 文件路径，entry_command 为对应命令名。"
    )
    messages = [
        Message(role="system", content=system_text),
        Message(role="user", content=f"{user_text}\n{instructions}"),
    ]
    for _ in range(2):
        response_format = {"type": "json_object"} if json_mode else None
        result = client.chat(messages, response_format=response_format)
        data = _parse_json(result.content or "")
        if data and "patch" in data:
            return data
        messages.append(
            Message(
                role="system",
                content="只允许输出 JSON，且必须包含 patch/lisp_path/entry_command/summary。",
            )
        )
    raise ValueError("LLM 未返回有效 JSON")


def _parse_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            return None
    return None


def _call_tool(runtime: McpRuntime, name: str, args: dict[str, Any]) -> dict[str, Any]:
    print(f"[TOOL] {name} ...", flush=True)
    result = runtime.call_tool(name, args)
    print("[TOOL] done", flush=True)
    if not result.get("ok"):
        raise RuntimeError(f"tool failed: {name}: {result.get('error')}")
    return result.get("data") or {}


def _resolve_lisp_path(path: str) -> Path:
    value = Path(path)
    if value.is_absolute():
        return value
    return (Path.cwd() / value).resolve()


def _normalize_entry_command(value: str) -> str:
    cleaned = str(value).strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1].strip()
    if cleaned.lower().startswith("c:"):
        cleaned = cleaned.split(":", 1)[1].strip()
    cleaned = cleaned.replace(" ", "_")
    return cleaned.upper()

