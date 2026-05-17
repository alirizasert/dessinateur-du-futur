from __future__ import annotations

from ...mcp.schemas import ToolSpec
from ...mcp.tool_base import ToolBase
from .session import get_backend

CAD_LOG_READ_SPEC = ToolSpec(
    name="cad_log_read",
    description="Read AutoCAD command log file",
    input_schema={
        "type": "object",
        "properties": {
            "drawing_name": {"type": "string"},
            "max_lines": {"type": "integer"},
        },
    },
    output_schema={"type": "object", "properties": {"content": {"type": "string"}}},
)


class CADLogReadTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return CAD_LOG_READ_SPEC

    def run(self, **kwargs):
        backend = get_backend(self.config)
        drawing_name = kwargs.get("drawing_name")
        max_lines = kwargs.get("max_lines")
        content = backend.log_read(drawing_name, max_lines)
        return {"content": content}

