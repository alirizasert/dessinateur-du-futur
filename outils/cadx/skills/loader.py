from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Skill:
    name: str
    path: Path


def list_skills(skills_dirs: Iterable[Path]) -> list[Skill]:
    skills: list[Skill] = []
    for base in skills_dirs:
        if not base.exists():
            continue
        for path in base.rglob("SKILL.md"):
            skills.append(Skill(name=path.parent.name, path=path))
    return sorted(skills, key=lambda s: s.name)

