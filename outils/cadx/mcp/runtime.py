from __future__ import annotations

from typing import Any

from ..core.types import ToolResult
from .registry import ToolRegistry


class McpRuntime:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def list_tools(self):
        return self.registry.list_specs()

    def call_tool(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        tool = self.registry.get(name)
        if not tool:
            return ToolResult(ok=False, error=f"unknown tool: {name}").to_dict()
        try:
            result = tool.run(**(args or {}))
            return ToolResult(ok=True, data=result).to_dict()
        except Exception as exc:
            return ToolResult(ok=False, error=str(exc)).to_dict()

