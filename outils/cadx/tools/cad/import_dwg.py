from __future__ import annotations

from ...mcp.schemas import ToolSpec
from ...mcp.tool_base import ToolBase
from .session import get_backend

CAD_IMPORT_DWG_SPEC = ToolSpec(
    name="cad_import_dwg",
    description="Import a DWG file into a working copy",
    input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
)


class CADImportDwgTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return CAD_IMPORT_DWG_SPEC

    def run(self, **kwargs):
        backend = get_backend(self.config)
        path = kwargs.get("path")
        if not path:
            raise ValueError("path is required")
        ok = backend.import_dwg(path)
        return {"ok": bool(ok)}

