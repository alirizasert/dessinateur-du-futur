from __future__ import annotations

from ...mcp.schemas import ToolSpec
from ...mcp.tool_base import ToolBase
from .session import get_backend

CAD_LOG_CONTROL_SPEC = ToolSpec(
    name="cad_log_control",
    description="Enable/disable CAD command log and optionally set log path",
    input_schema={
        "type": "object",
        "properties": {
            "enable": {"type": "boolean"},
            "log_path": {"type": "string"},
        },
        "required": ["enable"],
    },
    output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
)


class CADLogControlTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return CAD_LOG_CONTROL_SPEC

    def run(self, **kwargs):
        backend = get_backend(self.config)
        enable = kwargs.get("enable")
        if enable is None:
            raise ValueError("enable is required")
        log_path = kwargs.get("log_path")
        ok = backend.log_control(bool(enable), log_path)
        return {"ok": bool(ok)}

