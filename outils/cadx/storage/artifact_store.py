from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

from ..core.types import RunContext


def save_artifact(
    run_ctx: RunContext,
    kind: str,
    name: str,
    content: str | bytes | None = None,
    path: str | Path | None = None,
) -> Path:
    target_dir = _artifact_dir(run_ctx.run_dir, kind)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / name

    if content is not None:
        if isinstance(content, bytes):
            target_path.write_bytes(content)
        else:
            target_path.write_text(str(content), encoding="utf-8")
        return target_path

    if path is not None:
        src = Path(path)
        shutil.copy2(src, target_path)
        return target_path

    raise ValueError("content or path is required")


def _artifact_dir(run_dir: Path, kind: str) -> Path:
    mapping = {
        "lisp": "lisp",
        "image": "exports",
        "log": "logs",
        "report": "reports",
        "patch": "patches",
    }
    key = mapping.get(kind, kind)
    return run_dir / key

