from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .backend import CadBackend


@dataclass
class MockCadBackend(CadBackend):
    connected: bool = False
    commands: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    log_path: str | None = None

    def connect(
        self,
        version: str | None = None,
        launch: bool | None = None,
        exec_path: str | None = None,
        launch_timeout: int | None = None,
    ) -> bool:
        self.connected = True
        self.logs.append(f"CONNECT version={version or ''}".strip())
        return True

    def command(self, command: str, auto_finish: bool = True) -> bool:
        self.commands.append(command)
        self.logs.append(f"COMMAND {command} auto_finish={auto_finish}")
        return True

    def run_lisp(self, path: str) -> bool:
        self.commands.append(f"LISP {path}")
        self.logs.append(f"LISP_RUN {path}")
        return True

    def log_control(self, enable: bool, log_path: str | None = None) -> bool:
        self.logs.append(f"LOG_CONTROL enable={enable}")
        if log_path:
            self.log_path = log_path
        return True

    def log_read(self, drawing_name: str | None = None, max_lines: int | None = None) -> str:
        content = self.logs
        if max_lines:
            content = content[-int(max_lines) :]
        return "\n".join(content)

    def export_image(
        self,
        fmt: str | None,
        path: str | None,
        view: str | None,
        layout_name: str | None = None,
        config_name: str | None = None,
        style_sheet: str | None = None,
        plot_type: str | int | None = None,
        auto_zoom_extents: bool | None = None,
    ) -> bool:
        self.exports.append(path or "")
        self.logs.append(
            f"EXPORT_IMAGE {fmt} {path} {view} {layout_name} {config_name} "
            f"{style_sheet} {plot_type} auto_zoom_extents={auto_zoom_extents}"
        )
        return True

    def export_dwg(self, path: str | None) -> bool:
        self.exports.append(path or "")
        self.logs.append(f"EXPORT_DWG {path}")
        return True

    def import_dwg(self, path: str) -> bool:
        self.imports.append(path)
        self.logs.append(f"IMPORT_DWG {path}")
        return True

    def entity_extract(self, scope: str | None = None) -> list[dict[str, Any]]:
        return [{"type": "LINE", "start": [0, 0], "end": [10, 0], "scope": scope or ""}]

