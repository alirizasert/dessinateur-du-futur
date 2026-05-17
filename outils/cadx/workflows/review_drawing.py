from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

from ..agents.orchestrator import Orchestrator
from ..core.config import load_config
from ..mcp.registry import ToolRegistry
from ..mcp.runtime import McpRuntime
from ..storage.run_store import create_run_context
from ..storage.artifact_store import save_artifact
from ..tools import register_all_tools
from ..tools.cad.session import set_backend
from ..tools.cad.com_backend import ComCadBackend
from ..tools.cad.mock_backend import MockCadBackend
from ..llm.schemas import Message


def run_review(prompt: str | None = None) -> int:
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

    connect_args: dict[str, Any] = {"launch": True, "launch_timeout": 180}
    if config.autocad_exec:
        connect_args["exec_path"] = config.autocad_exec

    _call_tool(runtime, "cad_connect", connect_args)
    img_path = run_ctx.run_dir / "exports" / f"{run_ctx.run_id}.jpg"
    _call_tool(
        runtime,
        "cad_export_image",
        {"format": "jpg", "path": str(img_path), "auto_zoom_extents": True},
    )
    entities = _call_tool(runtime, "cad_entity_extract", {}).get("entities", [])
    save_artifact(run_ctx, "report", "entities.json", content=json.dumps(entities, ensure_ascii=False, indent=2))

    base_text = prompt or "请审阅图纸，指出问题并给出改进建议。"
    user_text = (
        f"{base_text}\n"
        "如需更多信息，请至少调用一个工具（例如 cad_log_read 或 file_read）。"
    )
    content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    if img_path.exists():
        content.append({"type": "image_url", "image_url": {"url": _to_data_uri(img_path)}})

    orch = Orchestrator(config)
    messages = [
        Message(role="system", content=orch._load_system_prompt()),  # noqa: SLF001
        Message(role="user", content=content),
    ]
    result = orch.run_messages(messages, tool_required=True)
    save_artifact(run_ctx, "report", "review.md", content=result.content)

    print(result.content)
    print(f"run_id: {run_ctx.run_id}")
    print(f"report: {run_ctx.run_dir / 'reports' / 'review.md'}")
    return 0


def _to_data_uri(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        mime = "image/png"
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _call_tool(runtime: McpRuntime, name: str, args: dict[str, Any]) -> dict[str, Any]:
    print(f"[TOOL] {name} ...", flush=True)
    result = runtime.call_tool(name, args)
    print("[TOOL] done", flush=True)
    if not result.get("ok"):
        raise RuntimeError(f"tool failed: {name}: {result.get('error')}")
    return result.get("data") or {}

