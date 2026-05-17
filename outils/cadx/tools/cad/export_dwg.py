from __future__ import annotations

from ...mcp.schemas import ToolSpec
from ...mcp.tool_base import ToolBase
from .session import get_backend

CAD_EXPORT_DWG_SPEC = ToolSpec(
    name="cad_export_dwg",
    description="Export current drawing to DWG",
    input_schema={
        "type": "object",
        "properties": {"path": {"type": "string"}, "dwg_path": {"type": "string"}},
    },
    output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
)


class CADExportDwgTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return CAD_EXPORT_DWG_SPEC

    def run(self, **kwargs):
        backend = get_backend(self.config)
        dwg_path = kwargs.get("dwg_path")
        if dwg_path:
            backend.import_dwg(dwg_path)
        path = kwargs.get("path")
        ok = backend.export_dwg(path)
        return {"ok": bool(ok)}

