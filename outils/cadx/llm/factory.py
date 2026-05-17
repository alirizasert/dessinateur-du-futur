﻿from __future__ import annotations

from dataclasses import dataclass

from ..core.config import Config
from .client import OpenAICompatibleClient, LLMClient


def create_client(config: Config) -> LLMClient:
    provider = (config.llm_provider or "").lower()
    if provider in ("glm", "qwen", "openai", "compatible"):
        return OpenAICompatibleClient(config)
    return OpenAICompatibleClient(config)

