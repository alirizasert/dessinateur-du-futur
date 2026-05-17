from __future__ import annotations

import difflib
from pathlib import Path

from ..mcp.schemas import ToolSpec
from ..mcp.tool_base import ToolBase

LISP_DIFF_SPEC = ToolSpec(
    name="lisp_diff",
    description="Compare two LISP scripts and report differences (placeholder)",
    input_schema={
        "type": "object",
        "properties": {
            "path_a": {"type": "string"},
            "path_b": {"type": "string"},
            "context_lines": {"type": "integer"},
        },
        "required": ["path_a", "path_b"],
    },
    output_schema={"type": "object", "properties": {"diff": {"type": "string"}}},
)


class LispDiffTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return LISP_DIFF_SPEC

    def run(self, **kwargs):
        path_a = kwargs.get("path_a")
        path_b = kwargs.get("path_b")
        if not path_a or not path_b:
            raise ValueError("path_a and path_b are required")

        a = Path(path_a).read_text(encoding="utf-8").splitlines()
        b = Path(path_b).read_text(encoding="utf-8").splitlines()
        context = int(kwargs.get("context_lines", 3)) if kwargs.get("context_lines") is not None else 3
        diff = "\n".join(difflib.unified_diff(a, b, fromfile=path_a, tofile=path_b, n=context))
        return {"diff": diff}

