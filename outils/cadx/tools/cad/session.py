from __future__ import annotations

from ...core.config import Config, load_config
from ...core.errors import ToolError
from .backend import CadBackend
from .mock_backend import MockCadBackend
from .com_backend import ComCadBackend

_backend: CadBackend | None = None


def set_backend(backend: CadBackend) -> None:
    global _backend
    _backend = backend


def get_backend(config: Config | None = None) -> CadBackend:
    global _backend
    if _backend is not None:
        return _backend

    config = config or load_config()
    mode = (config.cad_backend or "mock").lower()
    if mode == "mock":
        _backend = MockCadBackend()
    elif mode == "com":
        _backend = ComCadBackend(config)
    else:
        raise ToolError(f"unknown CAD backend: {mode}")
    return _backend

