from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from .schemas import ToolSpec
from ..core.config import Config


class ToolBase(ABC):
    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config

    @property
    @abstractmethod
    def spec(self) -> ToolSpec:
        raise NotImplementedError

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError

