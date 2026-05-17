from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]

