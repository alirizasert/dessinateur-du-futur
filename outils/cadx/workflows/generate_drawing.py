from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from ..core.config import load_config
from ..core.paths import resolve_paths
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


def run_generate(prompt: str | None = None) -> int:
    config = load_config()
    paths = resolve_paths(config)
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

    user_text = prompt or "请生成一个立方体的 AutoLISP 绘图代码。"
    system_text = _load_system_prompt()
    lisp_path = run_ctx.run_dir / "lisp" / "drawing.lsp"
    rel_lisp_path = lisp_path.relative_to(paths.root).as_posix()
    debug_lines: list[str] = []

    try:
        lisp_code = _generate_lisp_with_tool(
            client=client,
            runtime=runtime,
            system_text=system_text,
            user_text=user_text,
            rel_lisp_path=rel_lisp_path,
            abs_lisp_path=lisp_path,
            debug_lines=debug_lines,
        )
    finally:
        if debug_lines:
            save_artifact(run_ctx, "report", "llm_debug.txt", content="\n".join(debug_lines))

    entry_command = _extract_entry_command(lisp_code)
    if not entry_command:
        raise ValueError("entry_command is empty")

    log_dir = run_ctx.run_dir / "logs"
    img_path = run_ctx.run_dir / "exports" / f"{run_ctx.run_id}.jpg"

    connect_args: dict[str, Any] = {"launch": True, "launch_timeout": 180}
    if config.autocad_exec:
        connect_args["exec_path"] = config.autocad_exec

    _call_tool(runtime, "cad_connect", connect_args)
    _call_tool(runtime, "cad_log_control", {"enable": True, "log_path": str(log_dir)})
    _call_tool(runtime, "cad_lisp_run", {"path": str(lisp_path)})
    _call_tool(runtime, "cad_command", {"command": entry_command, "auto_finish": True})
    time.sleep(1.0)
    _call_tool(
        runtime,
        "cad_export_image",
        {"format": "jpg", "path": str(img_path), "auto_zoom_extents": True},
    )
    entities = _call_tool(runtime, "cad_entity_extract", {}).get("entities", [])
    log_text = _call_tool(runtime, "cad_log_read", {"max_lines": 200}).get("content", "")

    save_artifact(run_ctx, "report", "entities.json", content=json.dumps(entities, ensure_ascii=False, indent=2))
    save_artifact(run_ctx, "report", "log.txt", content=log_text)

    print("生成完成")
    print(f"run_id: {run_ctx.run_id}")
    print(f"lisp: {lisp_path}")
    print(f"image: {img_path}")
    return 0


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


def _generate_lisp_with_tool(
    client,
    runtime: McpRuntime,
    system_text: str,
    user_text: str,
    rel_lisp_path: str,
    abs_lisp_path: Path,
    debug_lines: list[str],
) -> str:
    instructions = (
        "你必须调用 file_patch 工具把 LISP 写入指定文件路径。\n"
        f"目标路径: {rel_lisp_path}\n"
        "要求：\n"
        "1) 写入内容必须是完整可执行的 AutoLISP。\n"
        "2) 必须包含 (defun c:xxx ...) 并在结尾 (princ)。\n"
        "3) 所有命令必须写死参数，禁止交互输入（getpoint/getreal/entsel/ssget/pause）。\n"
        "4) 用户未给参数时使用合理默认值。\n"
        "只允许调用 file_patch，不要输出其它文本。\n"
        "注意：file_patch 的 patch 必须是对象，不要把 JSON 放进字符串。\n"
        "file_patch 参数示例：\n"
        f"{{\"patch\":{{\"actions\":{{\"{rel_lisp_path}\":{{\"type\":\"add\",\"new_file\":\"(defun c:xxx () ...)\"}}}}}}}}"
    )
    messages = [
        Message(role="system", content=system_text),
        Message(role="user", content=f"{user_text}\n{instructions}"),
    ]

    tools = _build_tools_schema(runtime, {"file_patch"})
    tool_choice = {"type": "function", "function": {"name": "file_patch"}}

    for attempt in range(1, 4):
        print("[LLM] 正在思考...", flush=True)
        result = client.chat(messages, tools=tools, tool_choice=tool_choice)
        debug_lines.append(f"[attempt {attempt}] content:\n{(result.content or '').strip()}")
        debug_lines.append(f"[attempt {attempt}] tool_calls: {result.tool_calls}")

        if not result.tool_calls:
            messages.append(
                Message(role="system", content="必须调用 file_patch 工具写入 LISP 文件。")
            )
            continue

        call = next((c for c in result.tool_calls if c.name == "file_patch"), None)
        if not call:
            messages.append(
                Message(role="system", content="只允许调用 file_patch 工具。")
            )
            continue

        coerced_args = _coerce_file_patch_args(
            call.arguments,
            fallback_path=rel_lisp_path,
            debug_lines=debug_lines,
        )
        if not coerced_args:
            messages.append(
                Message(
                    role="system",
                    content=(
                        "file_patch 的参数必须是 JSON 对象，且包含 patch.actions。"
                        "请以对象形式传递，不要把 JSON 放在字符串里。"
                    ),
                )
            )
            continue

        if not _patch_targets_path(coerced_args, rel_lisp_path):
            debug_lines.append(
                f"[attempt {attempt}] patch path mismatch. expected={rel_lisp_path} args={coerced_args}"
            )
            messages.append(
                Message(
                    role="system",
                    content=f"file_patch.actions 必须包含目标路径: {rel_lisp_path}",
                )
            )
            continue

        tool_result = runtime.call_tool("file_patch", coerced_args)
        debug_lines.append(f"[attempt {attempt}] file_patch result: {tool_result}")
        if not tool_result.get("ok"):
            messages.append(
                Message(
                    role="system",
                    content=f"file_patch 执行失败：{tool_result.get('error')}",
                )
            )
            continue

        data = tool_result.get("data") or {}
        if not data.get("applied"):
            messages.append(
                Message(
                    role="system",
                    content=f"file_patch 未应用成功：{data.get('errors')}",
                )
            )
            continue

        if not abs_lisp_path.exists():
            messages.append(
                Message(
                    role="system",
                    content=f"未找到生成的 LISP 文件：{rel_lisp_path}",
                )
            )
            continue

        lisp_code = abs_lisp_path.read_text(encoding="utf-8", errors="ignore")
        if not lisp_code.strip():
            messages.append(
                Message(
                    role="system",
                    content="生成的 LISP 内容为空，请重写。",
                )
            )
            continue

        interactive_issues = _find_interactive_issues(lisp_code)
        if interactive_issues:
            sample = "\n".join(f"- {item}" for item in interactive_issues[:5])
            messages.append(
                Message(
                    role="system",
                    content=(
                        "你的 LISP 含有交互式命令或未给足参数：\n"
                        f"{sample}\n"
                        "请改为一次性完整参数（示例："
                        "(command \"pline\" pt1 pt2 pt3 \"\")）。"
                    ),
                )
            )
            continue

        if not _extract_entry_command(lisp_code):
            messages.append(
                Message(
                    role="system",
                    content="未找到 (defun c:xxx ...) 定义，请补充入口命令。",
                )
            )
            continue

        return lisp_code

    raise ValueError("LLM 未能生成合规 LISP，请查看 reports/llm_debug.txt")


def _call_tool(runtime: McpRuntime, name: str, args: dict[str, Any]) -> dict[str, Any]:
    print(f"[TOOL] {name} ...", flush=True)
    result = runtime.call_tool(name, args)
    print("[TOOL] done", flush=True)
    if not result.get("ok"):
        raise RuntimeError(f"tool failed: {name}: {result.get('error')}")
    return result.get("data") or {}


def _normalize_entry_command(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1].strip()
    if cleaned.lower().startswith("c:"):
        cleaned = cleaned.split(":", 1)[1].strip()
    cleaned = cleaned.replace(" ", "_")
    return cleaned.upper()


def _extract_entry_command(code: str) -> str:
    match = re.search(r"\(defun\s+c:([^\s\)]+)", code, flags=re.IGNORECASE)
    if not match:
        return ""
    return _normalize_entry_command(match.group(1))


def _patch_targets_path(arguments: dict[str, Any], rel_path: str) -> bool:
    if not isinstance(arguments, dict):
        return False
    patch = arguments.get("patch")
    if not isinstance(patch, dict):
        return False
    actions = patch.get("actions")
    if not isinstance(actions, dict):
        return False
    target = _normalize_rel_path(rel_path)
    for key in actions.keys():
        if _normalize_rel_path(str(key)) == target:
            return True
    return False


def _normalize_rel_path(value: str) -> str:
    text = value.replace("\\", "/").lstrip("./")
    while text.startswith("../"):
        text = text[3:]
    return text


def _coerce_file_patch_args(
    arguments: dict[str, Any] | None,
    fallback_path: str | None = None,
    debug_lines: list[str] | None = None,
) -> dict[str, Any] | None:
    debug_lines = debug_lines or []
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except Exception as exc:
            debug_lines.append(f"[coerce] arguments json invalid: {exc}")
            arguments = {"_raw": arguments}

    if not isinstance(arguments, dict):
        return None

    if "input" in arguments and not arguments.get("patch"):
        raw_input = arguments.get("input")
        if isinstance(raw_input, str):
            try:
                arguments = json.loads(raw_input)
            except Exception as exc:
                debug_lines.append(f"[coerce] input json invalid: {exc}")

    if "_raw" in arguments and not arguments.get("patch"):
        raw = arguments.get("_raw")
        if isinstance(raw, str):
            try:
                arguments = json.loads(raw)
            except Exception as exc:
                debug_lines.append(f"[coerce] raw json invalid: {exc}")

    patch = arguments.get("patch")
    if isinstance(patch, str):
        try:
            patch = json.loads(patch)
        except Exception as exc:
            debug_lines.append(f"[coerce] patch json invalid: {exc}")
            extracted = _extract_new_file_from_patch_string(patch, debug_lines)
            if extracted and fallback_path:
                patch = {"actions": {fallback_path: {"type": "add", "new_file": extracted}}}
            else:
                return None
    if not isinstance(patch, dict):
        return None

    actions = patch.get("actions")
    if isinstance(actions, str):
        try:
            actions = json.loads(actions)
            patch["actions"] = actions
        except Exception as exc:
            debug_lines.append(f"[coerce] actions json invalid: {exc}")
            extracted = _extract_new_file_from_patch_string(actions, debug_lines)
            if extracted and fallback_path:
                patch["actions"] = {fallback_path: {"type": "add", "new_file": extracted}}
                actions = patch["actions"]
            else:
                return None
    if not isinstance(actions, dict):
        return None

    return {"patch": patch}


def _extract_new_file_from_patch_string(text: str, debug_lines: list[str]) -> str | None:
    if not isinstance(text, str):
        return None
    key = '"new_file"'
    idx = text.find(key)
    if idx == -1:
        debug_lines.append("[coerce] new_file key not found in patch string")
        return None
    colon = text.find(":", idx + len(key))
    if colon == -1:
        debug_lines.append("[coerce] new_file colon not found")
        return None
    start = text.find('"', colon)
    if start == -1:
        debug_lines.append("[coerce] new_file value start quote not found")
        return None
    try:
        value, _ = _parse_json_string(text, start)
        return value
    except Exception as exc:
        debug_lines.append(f"[coerce] new_file parse failed: {exc}")
        return None


def _parse_json_string(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != '"':
        raise ValueError("expected string at start")
    i = start + 1
    out: list[str] = []
    while i < len(text):
        ch = text[i]
        if ch == '"':
            return "".join(out), i + 1
        if ch == "\\":
            i += 1
            if i >= len(text):
                break
            esc = text[i]
            if esc == "n":
                out.append("\n")
            elif esc == "r":
                out.append("\r")
            elif esc == "t":
                out.append("\t")
            elif esc == '"':
                out.append('"')
            elif esc == "\\":
                out.append("\\")
            elif esc == "u" and i + 4 < len(text):
                hex_value = text[i + 1 : i + 5]
                try:
                    out.append(chr(int(hex_value, 16)))
                except Exception:
                    out.append("\\u" + hex_value)
                i += 4
            else:
                out.append(esc)
        else:
            out.append(ch)
        i += 1
    raise ValueError("unterminated string")


def _build_tools_schema(runtime: McpRuntime, names: set[str]) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for spec in runtime.list_tools():
        if spec.name not in names:
            continue
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.input_schema,
                },
            }
        )
    return tools


def _find_interactive_issues(code: str) -> list[str]:
    issues: list[str] = []
    lowered = code.lower()
    forbidden = [
        "(getpoint",
        "(getint",
        "(getreal",
        "(getstring",
        "(entsel",
        "(ssget",
        "(pause",
    ]
    for token in forbidden:
        if token in lowered:
            issues.append(token.strip("("))

    for block in _iter_command_blocks(code):
        body = _extract_command_body(block)
        if body is None:
            continue
        tokens = _tokenize_command_body(body)
        if not tokens:
            issues.append(_truncate_block(block))
            continue
        first_kind, first_val = tokens[0]
        if first_kind != "string":
            issues.append(_truncate_block(block))
            continue
        if len(tokens) <= 1:
            issues.append(_truncate_block(block))
            continue
        for kind, val in tokens:
            if kind in ("string", "symbol") and str(val).strip().lower() in ("pause", "_pause"):
                issues.append(_truncate_block(block))
                break

    return list(dict.fromkeys(issues))


def _iter_command_blocks(code: str) -> list[str]:
    blocks: list[str] = []
    lower = code.lower()
    idx = 0
    while True:
        start = lower.find("(command", idx)
        if start == -1:
            break
        i = start
        depth = 0
        in_str = False
        while i < len(code):
            ch = code[i]
            if in_str:
                if ch == "\\":
                    i += 2
                    continue
                if ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        blocks.append(code[start:i])
                        break
            i += 1
        idx = i if i > start else start + 8
    return blocks


def _extract_command_body(block: str) -> str | None:
    match = re.match(r"\(\s*command\s+(.+)\)\s*$", block, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def _tokenize_command_body(body: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch.isspace():
            i += 1
            continue
        if ch == '"':
            value, j = _parse_json_string(body, i)
            tokens.append(("string", value))
            i = j
            continue
        if ch == "(":
            value, j = _read_paren_block(body, i)
            tokens.append(("list", value))
            i = j
            continue
        start = i
        while i < len(body) and not body[i].isspace() and body[i] not in "()":
            i += 1
        tokens.append(("symbol", body[start:i]))
    return tokens


def _read_paren_block(text: str, start: int) -> tuple[str, int]:
    depth = 0
    i = start
    in_str = False
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1], i + 1
        i += 1
    return text[start:], len(text)


def _truncate_block(text: str, max_len: int = 160) -> str:
    clean = " ".join(text.split())
    if len(clean) > max_len:
        return clean[:max_len] + "..."
    return clean

