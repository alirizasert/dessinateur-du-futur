from __future__ import annotations

from pathlib import Path

from ..core.paths import resolve_paths
from ..core.config import load_config
from ..mcp.schemas import ToolSpec
from ..mcp.tool_base import ToolBase
from .cad.session import get_backend

DWG_TO_LISP_SPEC = ToolSpec(
    name="dwg_to_lisp",
    description="Convert DWG to equivalent AutoLISP script (placeholder)",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "output_path": {"type": "string"},
            "scope": {"type": "string"},
        },
        "required": ["path"],
    },
    output_schema={"type": "object", "properties": {"lisp_path": {"type": "string"}}},
)


class DwgToLispTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return DWG_TO_LISP_SPEC

    def run(self, **kwargs):
        path = kwargs.get("path")
        if not path:
            raise ValueError("path is required")
        output_path = kwargs.get("output_path")
        scope = kwargs.get("scope")

        config = self.config or load_config()
        root = resolve_paths(config).root
        in_path = self._safe_path(root, path)

        backend = get_backend(self.config)
        backend.import_dwg(str(in_path))
        entities = backend.entity_extract(scope)

        lisp_lines = ["(defun c:DWG2LSP_GEN ()", "  (progn"]
        for ent in entities:
            lisp_lines.append(self._entity_to_lisp(ent))
        lisp_lines.append("  )")
        lisp_lines.append(")")
        lisp_lines.append("(princ)")

        if output_path:
            out_path = self._safe_path(root, output_path)
        else:
            out_path = in_path.with_suffix(".lsp")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lisp_lines), encoding="utf-8")

        return {"lisp_path": str(out_path)}

    def _safe_path(self, root: Path, rel_path: str) -> Path:
        path = Path(rel_path)
        if path.is_absolute():
            return path
        resolved = (root / path).resolve()
        if root not in resolved.parents and resolved != root:
            raise ValueError("path escapes root")
        return resolved

    def _entity_to_lisp(self, ent: dict) -> str:
        ent_type = ent.get("type", "")
        geom = ent.get("geometry", {})
        if ent_type.endswith("Line") or ent_type == "LINE":
            start = geom.get("start", [0, 0])
            end = geom.get("end", [0, 0])
            return f'    (command "._LINE" "{start[0]},{start[1]}" "{end[0]},{end[1]}" "")'
        if ent_type.endswith("Circle") or ent_type == "CIRCLE":
            center = geom.get("center", [0, 0])
            radius = geom.get("radius", 0)
            return f'    (command "._CIRCLE" "{center[0]},{center[1]}" "{radius}")'
        if ent_type.endswith("Arc") or ent_type == "ARC":
            center = geom.get("center", [0, 0])
            radius = geom.get("radius", 0)
            start = geom.get("start_angle", 0)
            end = geom.get("end_angle", 0)
            return f'    (command "._ARC" "{center[0]},{center[1]}" "{radius}" "{start}" "{end}")'
        if ent_type.endswith("Polyline") or ent_type == "LWPOLYLINE":
            coords = geom.get("coordinates", [])
            points = []
            for i in range(0, len(coords), 2):
                points.append(f'"{coords[i]},{coords[i+1]}"')
            return f'    (command "._PLINE" {" ".join(points)} "")'
        if ent_type.endswith("Text") or ent_type == "TEXT":
            text = geom.get("text", "")
            pos = geom.get("position", [0, 0])
            height = geom.get("height", 2.5)
            return f'    (command "._TEXT" "{pos[0]},{pos[1]}" "{height}" "0" "{text}")'
        return "    (princ)"

