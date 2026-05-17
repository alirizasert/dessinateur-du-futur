from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from .config import Config


@dataclass
class Paths:
    root: Path
    runs_dir: Path
    cache_dir: Path
    logs_dir: Path
    skills_dirs: list[Path]


def resolve_paths(config: Config, root: Path | None = None) -> Paths:
    root = root or Path(__file__).resolve().parents[4]
    runs_dir = (root / config.runs_dir).resolve()
    cache_dir = (root / "cache").resolve()
    logs_dir = (root / "logs").resolve()
    skills_dirs = [root / "skills"]

    extra = os.getenv("CADX_SKILLS_DIRS", "")
    if extra:
        for part in extra.split(os.pathsep):
            if part.strip():
                skills_dirs.append(Path(part.strip()))

    return Paths(
        root=root,
        runs_dir=runs_dir,
        cache_dir=cache_dir,
        logs_dir=logs_dir,
        skills_dirs=skills_dirs,
    )

