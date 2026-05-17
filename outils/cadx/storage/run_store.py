from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import uuid

from ..core.config import load_config
from ..core.paths import resolve_paths
from ..core.types import RunContext


def create_run_context() -> RunContext:
    config = load_config()
    paths = resolve_paths(config)
    run_id = _build_run_id()
    run_dir = (paths.runs_dir / run_id).resolve()
    _ensure_run_dirs(run_dir)
    return RunContext(run_id=run_id, run_dir=run_dir)


def _build_run_id() -> str:
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"{now}_{suffix}"


def _ensure_run_dirs(run_dir: Path) -> None:
    for name in ("lisp", "exports", "logs", "reports", "patches"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)

