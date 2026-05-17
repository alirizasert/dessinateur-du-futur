from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Message:
    role: str
    content: Any
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name:
            payload["name"] = self.name
        if self.tool_call_id:
            payload["tool_call_id"] = self.tool_call_id
        if self.tool_calls is not None:
            payload["tool_calls"] = self.tool_calls
        return payload


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    call_id: Optional[str] = None


@dataclass
class ChatResult:
    content: str
    tool_calls: list[ToolCall] | None = None

