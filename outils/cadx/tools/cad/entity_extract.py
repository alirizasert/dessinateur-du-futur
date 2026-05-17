from __future__ import annotations

from ...mcp.schemas import ToolSpec
from ...mcp.tool_base import ToolBase
from .session import get_backend

CAD_ENTITY_EXTRACT_SPEC = ToolSpec(
    name="cad_entity_extract",
    description="Extract entities and geometry data",
    input_schema={"type": "object", "properties": {"scope": {"type": "string"}}},
    output_schema={"type": "object", "properties": {"entities": {"type": "array"}}},
)


class CADEntityExtractTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return CAD_ENTITY_EXTRACT_SPEC

    def run(self, **kwargs):
        backend = get_backend(self.config)
        scope = kwargs.get("scope")
        entities = backend.entity_extract(scope)
        return {"entities": entities}

