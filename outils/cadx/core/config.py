from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    env: str = "dev"
    runs_dir: str = "./runs"
    log_level: str = "INFO"

    llm_provider: str = "qwen"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_vision_model: str = ""
    llm_timeout: int = 60
    llm_retries: int = 1
    llm_json_mode: bool = False

    autocad_version: str = "2026"
    autocad_log_path: str = ""
    autocad_exec: str = ""
    autocad_progid: str = "AutoCAD.Application"
    cad_backend: str = "mock"
    shell_allowlist: str = "python,cmd,powershell"
    plot_config_name: str = "PublishToWeb JPG.pc3"
    plot_style_sheet: str = "monochrome.ctb"
    plot_type: str = "display"
    cad_auto_launch: bool = True
    cad_launch_timeout: int = 180


def _parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def load_config(env_path: Optional[Path] = None) -> Config:
    env_path = env_path or Path(".env")
    file_env = _parse_env_file(env_path)

    def get(key: str, default: str) -> str:
        return os.environ.get(key, file_env.get(key, default))

    return Config(
        env=get("CADX_ENV", "dev"),
        runs_dir=get("CADX_RUNS_DIR", "./runs"),
        log_level=get("CADX_LOG_LEVEL", "INFO"),
        llm_provider=get("CADX_LLM_PROVIDER", "qwen"),
        llm_base_url=get("CADX_LLM_BASE_URL", ""),
        llm_api_key=get("CADX_LLM_API_KEY", ""),
        llm_model=get("CADX_LLM_MODEL", ""),
        llm_vision_model=get("CADX_LLM_VISION_MODEL", ""),
        llm_timeout=int(get("CADX_LLM_TIMEOUT", "60")),
        llm_retries=int(get("CADX_LLM_RETRIES", "1")),
        llm_json_mode=get("CADX_LLM_JSON_MODE", "0") not in ("0", "false", "False"),
        autocad_version=get("CADX_AUTOCAD_VERSION", "2026"),
        autocad_log_path=get("CADX_AUTOCAD_LOG_PATH", ""),
        autocad_exec=get("CADX_AUTOCAD_EXEC", ""),
        autocad_progid=get("CADX_AUTOCAD_PROGID", "AutoCAD.Application"),
        cad_backend=get("CADX_CAD_BACKEND", "mock"),
        shell_allowlist=get("CADX_SHELL_ALLOWLIST", "python,cmd,powershell"),
        plot_config_name=get("CADX_PLOT_CONFIG_NAME", "PublishToWeb JPG.pc3"),
        plot_style_sheet=get("CADX_PLOT_STYLE_SHEET", "monochrome.ctb"),
        plot_type=get("CADX_PLOT_TYPE", "display"),
        cad_auto_launch=get("CADX_AUTOCAD_LAUNCH", "1") not in ("0", "false", "False"),
        cad_launch_timeout=int(get("CADX_AUTOCAD_LAUNCH_TIMEOUT", "180")),
    )

