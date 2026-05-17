from __future__ import annotations

import argparse
import sys
from typing import Optional

from .core.config import load_config
from .core.paths import resolve_paths
from .mcp.registry import ToolRegistry
from .tools import register_all_tools
from .skills.loader import list_skills


def _route_intent(text: str) -> str | None:
    lowered = text.lower()

    def has_any(keys: list[str]) -> bool:
        return any(key in lowered for key in keys)

    if has_any(["修复", "修改", "纠正", "fix", "adjust", "改正", "bug"]):
        return "fix"
    if has_any(["审阅", "检查", "review", "评审", "审核", "评估"]):
        return "review"
    if has_any(["绘制", "生成", "画", "建模", "立方体", "模型", "绘图", "draw", "generate", "cube"]):
        return "generate"
    if has_any(["导出", "日志", "dwg", "lisp", "加载", "连接", "实体", "图片", "cad", "命令", "运行"]):
        return "tool"
    return None


def _handle_prompt(user_text: str, orch) -> int:
    intent = _route_intent(user_text)
    if intent == "generate":
        print("[ROUTE] 进入生成流程", flush=True)
        from .workflows.generate_drawing import run_generate

        return run_generate(user_text)
    if intent == "review":
        print("[ROUTE] 进入审阅流程", flush=True)
        from .workflows.review_drawing import run_review

        return run_review(user_text)
    if intent == "fix":
        print("[ROUTE] 进入修复流程", flush=True)
        from .workflows.fix_drawing import run_fix

        return run_fix(user_text)
    if intent == "tool":
        result = orch.run(user_text, tool_required=True)
        print(result.content)
        return 0

    result = orch.run(user_text)
    print(result.content)
    return 0


def _cmd_chat(args: argparse.Namespace) -> int:
    from .agents.orchestrator import Orchestrator

    orch = Orchestrator()
    if args.once:
        prompt = args.prompt or sys.stdin.read().strip()
        if not prompt:
            print("No prompt provided.")
            return 1
        return _handle_prompt(prompt, orch)

    print("CADx chat (type 'exit' to quit)")
    while True:
        try:
            user_text = input("> ").strip()
        except EOFError:
            break
        if not user_text:
            continue
        if user_text.lower() in ("exit", "quit"):
            break
        _handle_prompt(user_text, orch)
    return 0


def _cmd_mcp(_: argparse.Namespace) -> int:
    from .mcp.server import start_mcp_server

    return start_mcp_server()


def _cmd_run_generate(args: argparse.Namespace) -> int:
    from .workflows.generate_drawing import run_generate

    return run_generate(args.prompt)


def _cmd_run_review(args: argparse.Namespace) -> int:
    from .workflows.review_drawing import run_review

    return run_review(args.prompt)


def _cmd_run_fix(args: argparse.Namespace) -> int:
    from .workflows.fix_drawing import run_fix

    return run_fix(args.prompt)


def _cmd_tools_list(_: argparse.Namespace) -> int:
    config = load_config()
    registry = ToolRegistry()
    register_all_tools(registry, config)
    for spec in registry.list_specs():
        print(f"{spec.name}: {spec.description}")
    return 0


def _cmd_skills_list(_: argparse.Namespace) -> int:
    config = load_config()
    paths = resolve_paths(config)
    skills = list_skills(paths.skills_dirs)
    if not skills:
        print("(no skills found)")
        return 0
    for s in skills:
        print(f"{s.name}: {s.path}")
    return 0


def _cmd_doctor(_: argparse.Namespace) -> int:
    config = load_config()
    paths = resolve_paths(config)
    print("CADx Doctor")
    print(f"env: {config.env}")
    print(f"runs_dir: {paths.runs_dir}")
    print(f"cache_dir: {paths.cache_dir}")
    print(f"logs_dir: {paths.logs_dir}")
    print(f"skills_dirs: {', '.join(str(p) for p in paths.skills_dirs)}")
    print(f"llm_provider: {config.llm_provider}")
    print(f"autocad_version: {config.autocad_version}")
    print(f"cad_backend: {config.cad_backend}")
    print(f"autocad_progid: {config.autocad_progid}")
    print(f"shell_allowlist: {config.shell_allowlist}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cadx", description="CADx CLI")
    sub = parser.add_subparsers(dest="command")

    chat = sub.add_parser("chat", help="Start chat REPL")
    chat.add_argument("--once", action="store_true", help="Run a single prompt and exit")
    chat.add_argument("prompt", nargs="?", help="Prompt text (used with --once)")
    chat.set_defaults(func=_cmd_chat)

    mcp = sub.add_parser("mcp", help="Start MCP server")
    mcp.set_defaults(func=_cmd_mcp)

    run = sub.add_parser("run", help="Run workflow")
    run_sub = run.add_subparsers(dest="run_command")
    run_generate = run_sub.add_parser("generate", help="Generate drawing")
    run_generate.add_argument("--prompt", help="Prompt text")
    run_generate.set_defaults(func=_cmd_run_generate)
    run_review = run_sub.add_parser("review", help="Review drawing")
    run_review.add_argument("--prompt", help="Prompt text")
    run_review.set_defaults(func=_cmd_run_review)
    run_fix = run_sub.add_parser("fix", help="Fix drawing")
    run_fix.add_argument("--prompt", help="Prompt text")
    run_fix.set_defaults(func=_cmd_run_fix)

    tools = sub.add_parser("tools", help="Tools utilities")
    tools_sub = tools.add_subparsers(dest="tools_command")
    tools_list = tools_sub.add_parser("list", help="List tools")
    tools_list.set_defaults(func=_cmd_tools_list)

    skills = sub.add_parser("skills", help="Skills utilities")
    skills_sub = skills.add_subparsers(dest="skills_command")
    skills_list = skills_sub.add_parser("list", help="List skills")
    skills_list.set_defaults(func=_cmd_skills_list)

    doctor = sub.add_parser("doctor", help="Environment diagnostics")
    doctor.set_defaults(func=_cmd_doctor)

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    try:
        code = args.func(args)
    except NotImplementedError as exc:
        print(str(exc))
        code = 2
    sys.exit(code)

