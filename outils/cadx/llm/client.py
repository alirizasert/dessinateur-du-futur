from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Iterable, Optional, Any
from urllib import request, error

from ..core.config import Config
from .schemas import Message, ChatResult, ToolCall
from .providers import QWEN_DEFAULT_BASE_URL, GLM_DEFAULT_BASE_URL


@dataclass
class LLMClient:
    config: Config

    def chat(
        self,
        messages: Iterable[Message],
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[dict[str, Any]] = None,
    ) -> ChatResult:
        raise NotImplementedError("LLM client is not implemented")


class OpenAICompatibleClient(LLMClient):
    def chat(
        self,
        messages: Iterable[Message],
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[dict[str, Any]] = None,
    ) -> ChatResult:
        base_url = self.config.llm_base_url.strip()
        if not base_url:
            if (self.config.llm_provider or "").lower() == "glm":
                base_url = GLM_DEFAULT_BASE_URL
            else:
                base_url = QWEN_DEFAULT_BASE_URL
        url = base_url.rstrip("/") + "/chat/completions"

        msg_list: list[dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, Message):
                msg_list.append(msg.to_dict())
            else:
                msg_list.append(dict(msg))  # type: ignore[arg-type]

        model = self.config.llm_model or ""
        if _has_image_content(msg_list):
            model = self.config.llm_vision_model or model
        if not model:
            raise ValueError("LLM model is not configured")

        payload: dict[str, Any] = {"model": model, "messages": msg_list}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"
        if response_format:
            payload["response_format"] = response_format

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
        }
        if self.config.llm_api_key:
            headers["Authorization"] = f"Bearer {self.config.llm_api_key}"

        req = request.Request(url, data=data, headers=headers, method="POST")
        timeout = int(getattr(self.config, "llm_timeout", 60) or 60)
        retries = int(getattr(self.config, "llm_retries", 1) or 1)
        last_error: Exception | None = None
        for attempt in range(max(1, retries + 1)):
            try:
                print("[NET] 正在连接 LLM...", flush=True)
                with request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode("utf-8")
                last_error = None
                break
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="ignore")
                last_error = RuntimeError(f"LLM request failed: {exc.code} {detail}")
            except error.URLError as exc:
                last_error = RuntimeError(f"LLM request failed: {exc}")
            except TimeoutError as exc:
                last_error = RuntimeError(f"LLM request failed: timeout after {timeout}s")
            if attempt < retries:
                time.sleep(1.0 + attempt)
        if last_error is not None:
            raise last_error

        parsed = json.loads(raw)
        message = (parsed.get("choices") or [{}])[0].get("message") or {}
        content = message.get("content") or ""

        tool_calls: list[ToolCall] = []
        for call in message.get("tool_calls", []) or []:
            func = call.get("function") or {}
            name = func.get("name") or ""
            args = _safe_json(func.get("arguments"))
            tool_calls.append(ToolCall(name=name, arguments=args, call_id=call.get("id")))

        if not tool_calls and message.get("function_call"):
            func_call = message.get("function_call") or {}
            name = func_call.get("name") or ""
            args = _safe_json(func_call.get("arguments"))
            tool_calls.append(ToolCall(name=name, arguments=args, call_id=None))

        return ChatResult(content=content, tool_calls=tool_calls or None)


def _safe_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {"_raw": value}
    return {}


def _has_image_content(messages: list[dict[str, Any]]) -> bool:
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    return True
    return False

