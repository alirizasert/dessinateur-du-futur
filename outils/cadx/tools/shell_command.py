from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from ..core.config import Config
from ..mcp.schemas import ToolSpec
from ..mcp.tool_base import ToolBase

SHELL_COMMAND_SPEC = ToolSpec(
    name="shell_command",
    description="Run a safe shell command (whitelist + timeout)",
    input_schema={
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "workdir": {"type": "string"},
            "timeout": {"type": "integer"},
            "capture": {"type": "boolean"},
        },
        "required": ["command"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
            "exit_code": {"type": "integer"},
        },
    },
)


class ShellCommandTool(ToolBase):
    @property
    def spec(self) -> ToolSpec:
        return SHELL_COMMAND_SPEC

    def run(self, **kwargs):
        command = kwargs.get("command")
        if not command:
            raise ValueError("command is required")

        allowlist = []
        if self.config and self.config.shell_allowlist:
            allowlist = [p.strip().lower() for p in self.config.shell_allowlist.split(",") if p.strip()]

        if isinstance(command, str):
            tokens = shlex.split(command, posix=False)
        else:
            tokens = list(command)

        if not tokens:
            raise ValueError("command is empty")

        exe = Path(str(tokens[0])).name.lower()
        if allowlist and exe not in allowlist:
            raise PermissionError(f"command not allowed: {exe}")

        workdir = kwargs.get("workdir")
        cwd = Path(workdir) if workdir else None
        timeout = kwargs.get("timeout", 30)
        capture = bool(kwargs.get("capture", True))

        result = subprocess.run(
            tokens,
            cwd=str(cwd) if cwd else None,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "exit_code": result.returncode,
        }

