from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class RunContext:
    run_id: str
    run_dir: Path


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "data": self.data, "error": self.error}


@dataclass
class Artifact:
    name: str
    path: Path
    kind: str

