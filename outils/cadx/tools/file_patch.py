from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.paths import resolve_paths
from ..core.config import load_config
from ..mcp.schemas import ToolSpec
from ..mcp.tool_base import ToolBase

FILE_PATCH_SPEC = ToolSpec(
    name="file_patch",
    description="Apply a safe patch (add/update/delete) based on structured diff",
    input_schema={"type": "object", "properties": {"patch": {"type": "object"}}, "required": ["patch"]},
    output_schema={
        "type": "object",
        "properties": {
            "applied": {"type": "boolean"},
            "errors": {"type": "array", "items": {"type": "string"}},
        },
    },
)


class FilePatchTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return FILE_PATCH_SPEC

    def run(self, **kwargs):
        patch = kwargs.get("patch")
        if isinstance(patch, str):
            try:
                import json

                patch = json.loads(patch)
            except Exception as exc:
                raise ValueError(f"patch must be an object, got invalid JSON: {exc}") from exc
        if not isinstance(patch, dict):
            raise ValueError("patch must be an object")

        actions = patch.get("actions")
        if isinstance(actions, str):
            try:
                import json

                actions = json.loads(actions)
                patch["actions"] = actions
            except Exception as exc:
                raise ValueError(f"patch.actions must be an object, got invalid JSON: {exc}") from exc
        if not isinstance(actions, dict):
            raise ValueError("patch.actions must be an object")

        config = self.config or load_config()
        root = resolve_paths(config).root
        errors: list[str] = []

        for rel_path, action in actions.items():
            try:
                self._apply_action(root, rel_path, action)
            except Exception as exc:
                errors.append(f"{rel_path}: {exc}")

        return {"applied": len(errors) == 0, "errors": errors}

    def _apply_action(self, root: Path, rel_path: str, action: dict[str, Any]) -> None:
        action_type = action.get("type")
        path = self._safe_path(root, rel_path)

        if action_type == "add":
            new_file = action.get("new_file", "")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new_file, encoding="utf-8")
        elif action_type == "delete":
            if path.exists():
                path.unlink()
        elif action_type == "update":
            self._apply_update(path, action)
        else:
            raise ValueError(f"unknown action type: {action_type}")

        move_path = action.get("move_path")
        if move_path:
            target = self._safe_path(root, move_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            path.replace(target)

    def _apply_update(self, path: Path, action: dict[str, Any]) -> None:
        if not path.exists():
            raise FileNotFoundError(str(path))

        new_file = action.get("new_file")
        if new_file is not None:
            path.write_text(new_file, encoding="utf-8")
            return

        chunks = action.get("chunks", [])
        lines = path.read_text(encoding="utf-8").splitlines()
        for chunk in chunks:
            orig_index = int(chunk.get("orig_index", -1))
            del_lines = chunk.get("del_lines", [])
            ins_lines = chunk.get("ins_lines", [])
            if orig_index < 0:
                orig_index = len(lines)
            if del_lines:
                end = orig_index + len(del_lines)
                if lines[orig_index:end] != del_lines:
                    raise ValueError("delete lines do not match target")
                lines = lines[:orig_index] + ins_lines + lines[end:]
            else:
                lines = lines[:orig_index] + ins_lines + lines[orig_index:]
        path.write_text("\n".join(lines), encoding="utf-8")

    def _safe_path(self, root: Path, rel_path: str) -> Path:
        path = Path(rel_path)
        if path.is_absolute():
            raise ValueError("absolute paths are not allowed")
        resolved = (root / path).resolve()
        if root not in resolved.parents and resolved != root:
            raise ValueError("path escapes root")
        return resolved

