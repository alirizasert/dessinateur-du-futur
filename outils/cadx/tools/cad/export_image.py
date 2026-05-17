from __future__ import annotations

from ...mcp.schemas import ToolSpec
from ...mcp.tool_base import ToolBase
from .session import get_backend

CAD_EXPORT_IMAGE_SPEC = ToolSpec(
    name="cad_export_image",
    description="Export drawing to image",
    input_schema={
        "type": "object",
        "properties": {
            "dwg_path": {"type": "string"},
            "format": {"type": "string"},
            "path": {"type": "string"},
            "view": {"type": "string"},
            "layout_name": {"type": "string"},
            "config_name": {"type": "string"},
            "style_sheet": {"type": "string"},
            "plot_type": {"type": "string"},
            "auto_zoom_extents": {"type": "boolean"},
        },
    },
    output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
)


class CADExportImageTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return CAD_EXPORT_IMAGE_SPEC

    def run(self, **kwargs):
        backend = get_backend(self.config)
        dwg_path = kwargs.get("dwg_path")
        if dwg_path:
            backend.import_dwg(dwg_path)
        fmt = kwargs.get("format")
        path = kwargs.get("path")
        view = kwargs.get("view")
        auto_zoom_extents = kwargs.get("auto_zoom_extents", True)
        ok = backend.export_image(
            fmt,
            path,
            view,
            layout_name=kwargs.get("layout_name"),
            config_name=kwargs.get("config_name"),
            style_sheet=kwargs.get("style_sheet"),
            plot_type=kwargs.get("plot_type"),
            auto_zoom_extents=bool(auto_zoom_extents),
        )
        return {"ok": bool(ok)}

