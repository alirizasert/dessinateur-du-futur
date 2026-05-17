from __future__ import annotations

from ...mcp.schemas import ToolSpec
from ...mcp.tool_base import ToolBase
from .session import get_backend

CAD_LISP_RUN_SPEC = ToolSpec(
    name="cad_lisp_run",
    description="Load and run an AutoLISP script",
    input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
)


class CADLispRunTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return CAD_LISP_RUN_SPEC

    def run(self, **kwargs):
        backend = get_backend(self.config)
        path = kwargs.get("path")
        if not path:
            raise ValueError("path is required")
        ok = backend.run_lisp(path)
        return {"ok": bool(ok)}

