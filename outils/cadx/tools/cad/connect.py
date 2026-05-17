from __future__ import annotations

from ...mcp.schemas import ToolSpec
from ...mcp.tool_base import ToolBase
from .session import get_backend

CAD_CONNECT_SPEC = ToolSpec(
    name="cad_connect",
    description="Connect or launch AutoCAD",
    input_schema={
        "type": "object",
        "properties": {
            "version": {"type": "string"},
            "launch": {"type": "boolean"},
            "exec_path": {"type": "string"},
            "launch_timeout": {"type": "integer"},
        },
    },
    output_schema={"type": "object", "properties": {"connected": {"type": "boolean"}}},
)


class CADConnectTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return CAD_CONNECT_SPEC

    def run(self, **kwargs):
        backend = get_backend(self.config)
        version = kwargs.get("version")
        connected = backend.connect(
            version,
            launch=kwargs.get("launch"),
            exec_path=kwargs.get("exec_path"),
            launch_timeout=kwargs.get("launch_timeout"),
        )
        return {"connected": bool(connected)}

