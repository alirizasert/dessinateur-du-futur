param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8766,
    [switch]$RealAutoCAD
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

if ($RealAutoCAD) {
    $env:AUTOCAD_BRIDGE_DRY_RUN = "0"
} elseif (-not $env:AUTOCAD_BRIDGE_DRY_RUN) {
    $env:AUTOCAD_BRIDGE_DRY_RUN = "1"
}

.\.venv\Scripts\python.exe -m uvicorn autocad_codex_bridge.server:app --host $HostAddress --port $Port

