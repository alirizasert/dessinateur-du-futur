from __future__ import annotations

from ...mcp.schemas import ToolSpec
from ...mcp.tool_base import ToolBase
from .session import get_backend

CAD_COMMAND_SPEC = ToolSpec(
    name="cad_command",
    description="Run a CAD command in AutoCAD console",
    input_schema={
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "auto_finish": {"type": "boolean"},
        },
        "required": ["command"],
    },
    output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
)


class CADCommandTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return CAD_COMMAND_SPEC

    def run(self, **kwargs):
        backend = get_backend(self.config)
        command = kwargs.get("command")
        if not command:
            raise ValueError("command is required")
        auto_finish = kwargs.get("auto_finish", True)
        ok = backend.command(command, auto_finish=bool(auto_finish))
        return {"ok": bool(ok)}

