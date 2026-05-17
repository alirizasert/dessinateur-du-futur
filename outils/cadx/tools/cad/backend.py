from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CadBackend(ABC):
    @abstractmethod
    def connect(
        self,
        version: str | None = None,
        launch: bool | None = None,
        exec_path: str | None = None,
        launch_timeout: int | None = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def command(self, command: str, auto_finish: bool = True) -> bool:
        raise NotImplementedError

    @abstractmethod
    def run_lisp(self, path: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def log_control(self, enable: bool, log_path: str | None = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def log_read(self, drawing_name: str | None = None, max_lines: int | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def export_dwg(self, path: str | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def import_dwg(self, path: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def entity_extract(self, scope: str | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

