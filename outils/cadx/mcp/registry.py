from __future__ import annotations

from typing import Iterable

from .schemas import ToolSpec
from .tool_base import ToolBase


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> None:
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> ToolBase | None:
        return self._tools.get(name)

    def list_specs(self) -> list[ToolSpec]:
        return [self._tools[k].spec for k in sorted(self._tools.keys())]

    def list_tools(self) -> list[ToolBase]:
        return [self._tools[k] for k in sorted(self._tools.keys())]

