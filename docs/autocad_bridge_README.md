# AutoCAD Codex Bridge

[中文说明](README.zh-CN.md)

AutoCAD Codex Bridge is a small local HTTP bridge that lets Codex, scripts, or other AI agents control AutoCAD through Windows COM automation.

It accepts structured JSON commands, then executes safe, explicit AutoCAD operations such as creating drawings, drawing lines/circles/rectangles, adding text, creating layers, saving files, and running selected AutoCAD commands.

```text
Codex / AI Agent / Your App
  -> HTTP JSON
  -> FastAPI bridge
  -> pywin32 / Windows COM
  -> AutoCAD
```

## Features

- Connect to an existing AutoCAD session or start AutoCAD automatically
- Works with AutoCAD 2022 by default, and is designed to work with other COM-enabled AutoCAD versions
- Exposes a simple local HTTP API on `127.0.0.1`
- Includes a tiny `client.py` for terminal testing
- Supports dry-run mode for testing without touching AutoCAD
- Provides example CAD automation scripts:
  - `draw_iphone17_three_views.py`
  - `draw_ahu_structure.py`

## Compatibility

This project was initially tested with:

```text
AutoCAD 2022 - Simplified Chinese
AutoCAD COM version: 24.1
Windows + Python 3.13
```

It should also work with many desktop AutoCAD versions that expose the standard COM automation interface.

By default, the bridge uses:

```text
AutoCAD.Application
```

This asks Windows to connect to the registered/default AutoCAD COM server. For most users, this is the best choice because it avoids hard-coding a specific AutoCAD year.

If a computer has multiple AutoCAD versions installed, or the default COM registration is unusual, set:

```powershell
$env:AUTOCAD_PROG_ID="AutoCAD.Application"
```

Advanced users may try version-specific ProgIDs if their system requires it, for example:

```powershell
$env:AUTOCAD_PROG_ID="AutoCAD.Application.24.1"
```

Known examples:

| AutoCAD release | Typical internal major version |
| --- | --- |
| AutoCAD 2021 | 24.0 |
| AutoCAD 2022 | 24.1 |
| AutoCAD 2023 | 24.2 |
| AutoCAD 2024 | 24.3 |
| AutoCAD 2025 | 25.x |

Autodesk may change registration details between products and installations, so prefer `AutoCAD.Application` first. If connection fails, start AutoCAD manually and run `connect` again.

## Requirements

- Windows
- Desktop AutoCAD with COM automation enabled
- Python 3.10 or newer
- PowerShell or another terminal

Python packages:

```text
fastapi
uvicorn
pydantic
pywin32
```

## Installation

```powershell
git clone <your-repo-url>
cd autocad_codex_bridge
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you downloaded a ZIP instead of using Git, open the extracted `autocad_codex_bridge` folder and run the same commands.

## Start The Bridge

Use `python -m uvicorn` instead of `uvicorn` on Windows. This avoids launcher path problems after moving or copying the project folder.

```powershell
cd path\to\autocad_codex_bridge
.\.venv\Scripts\Activate.ps1
$env:AUTOCAD_BRIDGE_DRY_RUN="0"
python -m uvicorn autocad_codex_bridge.server:app --host 127.0.0.1 --port 8766
```

Keep this terminal open. You should see:

```text
Uvicorn running on http://127.0.0.1:8766
```

## Connect To AutoCAD

Open a second terminal:

```powershell
cd path\to\autocad_codex_bridge
.\.venv\Scripts\Activate.ps1
python client.py '{"action":"connect","visible":true}'
```

Expected response:

```json
{
  "ok": true,
  "action": "connect",
  "visible": true,
  "version": "24.1s ...",
  "caption": "Autodesk AutoCAD ..."
}
```

## Dry Run Mode

Dry-run mode validates the HTTP API without connecting to AutoCAD:

```powershell
$env:AUTOCAD_BRIDGE_DRY_RUN="1"
python -m uvicorn autocad_codex_bridge.server:app --host 127.0.0.1 --port 8766
```

Then test:

```powershell
python client.py '{"action":"health"}'
```

## Common Commands

Create a new drawing:

```powershell
python client.py '{"action":"new_document"}'
```

Create a layer:

```powershell
python client.py '{"action":"add_layer","layer":"AI-WALL"}'
```

Draw a line:

```powershell
python client.py '{"action":"draw_line","start":[0,0,0],"end":[1000,0,0],"layer":"AI-WALL"}'
```

Draw a circle:

```powershell
python client.py '{"action":"draw_circle","center":[500,500,0],"radius":200,"layer":"AI-WALL"}'
```

Draw a rectangle:

```powershell
python client.py '{"action":"draw_rectangle","corner":[0,0,0],"width":1000,"height":800,"layer":"AI-WALL"}'
```

Add text:

```powershell
python client.py '{"action":"add_text","text":"Hello CAD","insert":[0,0,0],"height":100,"layer":"AI-NOTE"}'
```

Zoom to extents:

```powershell
python client.py '{"action":"zoom_extents"}'
```

Save as:

```powershell
python client.py '{"action":"save_as","file_name":"D:/drawings/result.dwg"}'
```

Run an AutoCAD command:

```powershell
python client.py '{"action":"command","command":"._LINE 0,0 100,100 "}'
```

## HTTP API

The bridge exposes:

```text
GET  /health
POST /execute
```

Example request:

```json
{
  "action": "draw_rectangle",
  "corner": [0, 0, 0],
  "width": 1000,
  "height": 800,
  "layer": "AI-WALL"
}
```

Supported actions:

```text
health
connect
new_document
open_document
save
save_as
add_layer
set_current_layer
draw_line
draw_circle
draw_rectangle
add_text
zoom_extents
command
```

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `AUTOCAD_BRIDGE_DRY_RUN` | `1` | Set to `0` to control real AutoCAD |
| `AUTOCAD_PROG_ID` | `AutoCAD.Application` | AutoCAD COM ProgID |
| `AUTOCAD_BRIDGE_URL` | `http://127.0.0.1:8766/execute` | URL used by `client.py` |

## Example Drawings

Run the iPhone three-view demo:

```powershell
python draw_iphone17_three_views.py
```

Run the AHU structure demo:

```powershell
python draw_ahu_structure.py
```

These scripts draw directly into the active AutoCAD document.

## Troubleshooting

### `Fatal error in launcher`

This usually means the project folder was moved after creating `.venv`. Recreate the virtual environment:

```powershell
Remove-Item .\.venv -Recurse -Force
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Then start with:

```powershell
python -m uvicorn autocad_codex_bridge.server:app --host 127.0.0.1 --port 8766
```

### `HTTP 422`

The JSON payload is invalid. In PowerShell, wrap the whole JSON string in single quotes:

```powershell
python client.py '{"action":"health"}'
```

### Cannot connect to AutoCAD

Try these steps:

1. Start AutoCAD manually.
2. Run `python client.py '{"action":"connect","visible":true}'` again.
3. If you have multiple AutoCAD versions, set `AUTOCAD_PROG_ID`.
4. Make sure Python and AutoCAD are running under the same Windows user.

### AutoCAD opens but nothing is drawn

Run:

```powershell
python client.py '{"action":"zoom_extents"}'
```

Also check whether the active document is locked, read-only, or waiting for a modal dialog.

## Safety Notes

- Use copies of important DWG files when testing automation.
- Prefer structured actions such as `draw_line` and `draw_rectangle`.
- Be careful with the `command` action because it can send arbitrary AutoCAD command text.
- Do not send confidential drawing data to cloud models unless your project policy allows it.

## Roadmap Ideas

- Add delete/modify actions with confirmation gates
- Add block insertion
- Add dimension objects
- Add selection inspection
- Add layer color/linetype controls
- Add a small web UI for manual testing
- Add MCP tools for direct Codex integration

## License

This project is released under the MIT License. See [LICENSE](LICENSE).

