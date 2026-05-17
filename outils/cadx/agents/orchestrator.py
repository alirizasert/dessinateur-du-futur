﻿from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.config import load_config, Config
from ..core.paths import resolve_paths
from ..llm.factory import create_client
from ..llm.schemas import Message
from ..mcp.registry import ToolRegistry
from ..mcp.runtime import McpRuntime
from ..skills.loader import list_skills
from ..tools import register_all_tools


@dataclass
class OrchestratorResult:
    content: str
    steps: int


class Orchestrator:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or load_config()
        self.paths = resolve_paths(self.config)
        registry = ToolRegistry()
        register_all_tools(registry, self.config)
        self.runtime = McpRuntime(registry)
        self.client = create_client(self.config)

    def run(self, user_text: str, max_steps: int = 10, tool_required: bool = False) -> OrchestratorResult:
        system_text = self._load_system_prompt()
        messages: list[Message] = [
            Message(role="system", content=system_text),
            Message(role="user", content=user_text),
        ]
        return self.run_messages(messages, max_steps=max_steps, tool_required=tool_required)

    def run_messages(
        self,
        messages: list[Message],
        max_steps: int = 10,
        tool_required: bool = False,
    ) -> OrchestratorResult:
        tools = self._build_tools_schema()
        last_content = ""
        retry_forced = False
        tool_seen: dict[str, int] = {}

        for step in range(max_steps):
            print("[LLM] 正在思考...", flush=True)
            result = self.client.chat(messages, tools=tools, tool_choice="auto")
            last_content = result.content or ""

            if not result.tool_calls:
                if tool_required and not retry_forced:
                    messages.append(
                        Message(
                            role="system",
                            content="必须调用至少一个工具完成任务，否则视为失败。",
                        )
                    )
                    retry_forced = True
                    continue
                if tool_required and retry_forced:
                    return OrchestratorResult(
                        content="工具未被调用，已停止。",
                        steps=step + 1,
                    )
                return OrchestratorResult(content=last_content, steps=step + 1)

            tool_calls_payload = []
            for call in result.tool_calls:
                call_id = call.call_id or f"call-{step}-{call.name}"
                tool_calls_payload.append(
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments, ensure_ascii=False),
                        },
                    }
                )

            messages.append(
                Message(
                    role="assistant",
                    content=last_content,
                    tool_calls=tool_calls_payload,
                )
            )

            for call in result.tool_calls:
                call_id = call.call_id or f"call-{step}-{call.name}"
                signature = call.name + ":" + json.dumps(call.arguments, ensure_ascii=False, sort_keys=True)
                tool_seen[signature] = tool_seen.get(signature, 0) + 1
                if tool_seen[signature] > 2:
                    return OrchestratorResult(
                        content=f"检测到重复工具调用，已停止：{call.name}",
                        steps=step + 1,
                    )
                if call.name == "web_search":
                    print("[NET] 正在联网...", flush=True)
                print(f"[TOOL] {call.name} ...", flush=True)
                tool_result = self.runtime.call_tool(call.name, call.arguments)
                print("[TOOL] done", flush=True)
                messages.append(
                    Message(
                        role="tool",
                        content=json.dumps(tool_result, ensure_ascii=False),
                        tool_call_id=call_id,
                    )
                )
                if not tool_result.get("ok"):
                    messages.append(
                        Message(
                            role="system",
                            content=f"工具调用失败：{call.name}。如无法继续请停止。",
                        )
                    )

        return OrchestratorResult(content=f"超出迭代上限({max_steps})。", steps=max_steps)

    def _load_system_prompt(self) -> str:
        prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
        system_path = prompts_dir / "system.md"
        tool_path = prompts_dir / "tool_instructions.md"
        parts: list[str] = []
        if system_path.exists():
            parts.append(system_path.read_text(encoding="utf-8"))
        if tool_path.exists():
            parts.append(tool_path.read_text(encoding="utf-8"))
        skill_text = self._load_skills_text()
        if skill_text:
            parts.append("\n[Skills]\n" + skill_text)
        return "\n\n".join(p.strip() for p in parts if p.strip())

    def _load_skills_text(self) -> str:
        skills = list_skills(self.paths.skills_dirs)
        blocks: list[str] = []
        for skill in skills:
            try:
                content = skill.path.read_text(encoding="utf-8")
            except Exception:
                continue
            blocks.append(f"## {skill.name}\n{content}")
        return "\n\n".join(blocks)

    def _build_tools_schema(self) -> list[dict[str, Any]]:
        specs = self.runtime.list_tools()
        tools: list[dict[str, Any]] = []
        for spec in specs:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": spec.name,
                        "description": spec.description,
                        "parameters": spec.input_schema,
                    },
                }
            )
        return tools

