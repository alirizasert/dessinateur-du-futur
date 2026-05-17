from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.models import InitializationOptions

from ..core.config import load_config
from ..core.logging import setup_logging
from ..core.paths import resolve_paths
from ..skills.loader import list_skills
from ..tools import register_all_tools
from .registry import ToolRegistry
from .runtime import McpRuntime


def start_mcp_server() -> int:
    setup_logging()
    config = load_config()
    paths = resolve_paths(config)
    registry = ToolRegistry()
    register_all_tools(registry, config)
    runtime = McpRuntime(registry)

    server = Server("cadx")

    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name=spec.name,
                description=spec.description,
                inputSchema=spec.input_schema,
            )
            for spec in runtime.list_tools()
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any] | None):
        payload = runtime.call_tool(name, arguments or {})
        return [types.TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

    prompts_dir = Path(__file__).resolve().parents[1] / "prompts"

    def _prompt_files() -> list[Path]:
        if not prompts_dir.exists():
            return []
        return sorted(prompts_dir.glob("*.md"))

    @server.list_prompts()
    async def handle_list_prompts() -> List[types.Prompt]:
        prompts: list[types.Prompt] = []
        for path in _prompt_files():
            name = path.stem
            prompts.append(types.Prompt(name=name, title=name, description=f"Prompt: {name}"))
        return prompts

    @server.get_prompt()
    async def handle_get_prompt(name: str, arguments: Dict[str, str] | None):
        lookup = {path.stem: path for path in _prompt_files()}
        if name not in lookup:
            raise ValueError(f"prompt not found: {name}")
        content = lookup[name].read_text(encoding="utf-8")
        if arguments:
            try:
                content = content.format(**arguments)
            except Exception:
                pass
        return types.GetPromptResult(
            description=f"Prompt: {name}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=content),
                )
            ],
        )

    @server.list_resources()
    async def handle_list_resources() -> List[types.Resource]:
        resources: list[types.Resource] = []
        for skill in list_skills(paths.skills_dirs):
            resources.append(
                types.Resource(
                    name=skill.name,
                    title=skill.name,
                    uri=f"cadx-skill://{skill.name}",
                    description=f"Skill: {skill.name}",
                    mimeType="text/markdown",
                )
            )
        return resources

    @server.read_resource()
    async def handle_read_resource(uri: str):
        parsed = urlparse(str(uri))
        name = parsed.netloc or parsed.path.lstrip("/")
        if not name:
            raise ValueError(f"invalid resource uri: {uri}")
        skills = {skill.name: skill for skill in list_skills(paths.skills_dirs)}
        if name not in skills:
            raise ValueError(f"skill not found: {name}")
        content = skills[name].path.read_text(encoding="utf-8")
        return [ReadResourceContents(content=content, mime_type="text/markdown")]

    async def _run() -> None:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="cadx",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    import asyncio

    try:
        asyncio.run(_run())
        return 0
    except KeyboardInterrupt:
        return 0

