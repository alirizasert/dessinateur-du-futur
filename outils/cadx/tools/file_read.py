from __future__ import annotations

from pathlib import Path

from ..mcp.schemas import ToolSpec
from ..mcp.tool_base import ToolBase

FILE_READ_SPEC = ToolSpec(
    name="file_read",
    description="Read a file by range/head/tail with max output size",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "range": {"type": "object", "properties": {"start": {"type": "integer"}, "end": {"type": "integer"}}},
            "tail": {"type": "integer"},
            "head": {"type": "integer"},
            "max_chars": {"type": "integer"},
        },
        "required": ["path"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "total_lines": {"type": "integer"},
        },
    },
)


class FileReadTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return FILE_READ_SPEC

    def run(self, **kwargs):
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            raise FileNotFoundError(str(path))

        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        total_lines = len(lines)

        range_obj = kwargs.get("range")
        head = kwargs.get("head")
        tail = kwargs.get("tail")

        if range_obj:
            start = int(range_obj.get("start", 1))
            end = int(range_obj.get("end", total_lines))
            start = max(1, start)
            end = min(total_lines, end)
            selected = lines[start - 1 : end]
        elif head is not None:
            selected = lines[: int(head)]
        elif tail is not None:
            selected = lines[-int(tail) :] if total_lines else []
        else:
            selected = lines

        text = "\n".join(selected)
        max_chars = kwargs.get("max_chars")
        if max_chars is not None:
            max_chars = int(max_chars)
            if max_chars >= 0:
                text = text[:max_chars]

        return {"content": text, "total_lines": total_lines}

