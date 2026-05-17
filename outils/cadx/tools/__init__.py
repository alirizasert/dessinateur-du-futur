from __future__ import annotations

from ..mcp.registry import ToolRegistry
from ..core.config import Config
from .file_read import FileReadTool
from .file_patch import FilePatchTool
from .shell_command import ShellCommandTool
from .dwg_to_lisp import DwgToLispTool
from .lisp_diff import LispDiffTool
from .web_search import WebSearchTool
from .cad.connect import CADConnectTool
from .cad.command import CADCommandTool
from .cad.lisp_run import CADLispRunTool
from .cad.log_control import CADLogControlTool
from .cad.log_read import CADLogReadTool
from .cad.export_image import CADExportImageTool
from .cad.export_dwg import CADExportDwgTool
from .cad.import_dwg import CADImportDwgTool
from .cad.entity_extract import CADEntityExtractTool


def register_all_tools(registry: ToolRegistry, config: Config | None = None) -> None:
    tools = [
        FileReadTool(config),
        FilePatchTool(config),
        ShellCommandTool(config),
        DwgToLispTool(config),
        LispDiffTool(config),
        WebSearchTool(config),
        CADConnectTool(config),
        CADCommandTool(config),
        CADLispRunTool(config),
        CADLogControlTool(config),
        CADLogReadTool(config),
        CADExportImageTool(config),
        CADExportDwgTool(config),
        CADImportDwgTool(config),
        CADEntityExtractTool(config),
    ]
    for tool in tools:
        registry.register(tool)

