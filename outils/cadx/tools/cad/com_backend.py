from __future__ import annotations

from pathlib import Path
from typing import Any

from ...core.config import Config
from ...core.errors import ToolError
from .backend import CadBackend


class ComCadBackend(CadBackend):
    def __init__(self, config: Config) -> None:
        self.config = config
        self._app = None
        self._doc = None

    def _ensure(self, require_doc: bool = True) -> None:
        if not self._app:
            raise ToolError("AutoCAD COM not connected")
        if require_doc:
            self._refresh_doc()
            if not self._doc:
                raise ToolError("AutoCAD document not available")

    def _refresh_doc(self) -> None:
        try:
            self._doc = self._app.ActiveDocument
        except Exception:
            pass

    def _retry_com(self, func, retries: int = 5, delay: float = 0.5):
        import time

        for _ in range(retries):
            try:
                return func()
            except Exception:
                time.sleep(delay)
        return func()

    def connect(
        self,
        version: str | None = None,
        launch: bool | None = None,
        exec_path: str | None = None,
        launch_timeout: int | None = None,
    ) -> bool:
        try:
            import win32com.client  # type: ignore
            import pythoncom  # type: ignore
        except Exception as exc:
            raise ToolError(f"pywin32 not available: {exc}") from exc

        pythoncom.CoInitialize()
        progid = self.config.autocad_progid or "AutoCAD.Application"
        candidates = [progid]
        try:
            year = int(self.config.autocad_version)
            major = year - 2001
            if major > 0:
                candidates.append(f"AutoCAD.Application.{major}")
                candidates.append(f"AutoCAD.Application.{major}.1")
        except Exception:
            pass

        if launch is None:
            launch = self.config.cad_auto_launch
        if exec_path is None:
            exec_path = self.config.autocad_exec or None
        if launch_timeout is None:
            launch_timeout = getattr(self.config, "cad_launch_timeout", 180)

        last_exc = None
        for candidate in candidates:
            try:
                self._app = win32com.client.GetActiveObject(candidate)
                break
            except Exception:
                self._app = None

        if not self._app and launch:
            if exec_path:
                try:
                    import subprocess

                    exe_path = Path(exec_path)
                    subprocess.Popen([str(exe_path)])
                except Exception as exc:
                    last_exc = exc
            else:
                for candidate in candidates:
                    try:
                        self._app = win32com.client.Dispatch(candidate)
                        break
                    except Exception as exc:
                        last_exc = exc
                        self._app = None

            if not self._app:
                import time

                start = time.time()
                while time.time() - start < launch_timeout:
                    for candidate in candidates:
                        try:
                            self._app = win32com.client.GetActiveObject(candidate)
                            break
                        except Exception:
                            self._app = None
                    if self._app:
                        break
                    time.sleep(1)

        if not self._app and not launch:
            raise ToolError(
                "AutoCAD is not running. Start AutoCAD or set CADX_AUTOCAD_LAUNCH=1 to auto-launch."
            )
        if not self._app:
            raise ToolError(f"AutoCAD COM ProgID not found. Tried: {', '.join(candidates)}. Error: {last_exc}")
        self._app.Visible = True
        try:
            import time

            time.sleep(2)
        except Exception:
            pass
        try:
            self._doc = self._app.ActiveDocument
        except Exception:
            self._doc = self._app.Documents.Add()
        return True

    # 为避免命令停在“指定下一点/放弃”等交互提示，允许自动追加空回车结束。
    # 如需持续交互输入，请将 auto_finish=False。
    def command(self, command: str, auto_finish: bool = True) -> bool:
        self._ensure()
        suffix = "\n\n" if auto_finish else "\n"
        self._retry_com(lambda: self._doc.SendCommand(f"{command}{suffix}"))
        return True

    def run_lisp(self, path: str) -> bool:
        self._ensure()
        lisp_path = self._normalize_lisp_path(path)
        self._retry_com(lambda: self._doc.SendCommand(f'(load "{lisp_path}")\n'))
        return True

    def log_control(self, enable: bool, log_path: str | None = None) -> bool:
        self._ensure()
        if log_path:
            Path(log_path).mkdir(parents=True, exist_ok=True)
            try:
                self._retry_com(lambda: self._doc.SetVariable("LOGFILEPATH", log_path))
            except Exception:
                pass
        cmd = "LOGFILEON" if enable else "LOGFILEOFF"
        self._retry_com(lambda: self._doc.SendCommand(f"{cmd}\n"))
        return True

    def log_read(self, drawing_name: str | None = None, max_lines: int | None = None) -> str:
        self._ensure()
        try:
            logfile = self._doc.GetVariable("LOGFILENAME")
        except Exception as exc:
            raise ToolError(f"cannot read LOGFILENAME: {exc}") from exc
        path = Path(logfile)
        if not path.exists():
            raise ToolError(f"log file not found: {path}")
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if max_lines:
            lines = lines[-int(max_lines) :]
        return "\n".join(lines)

    def export_image(
        self,
        fmt: str | None,
        path: str | None,
        view: str | None,
        layout_name: str | None = None,
        config_name: str | None = None,
        style_sheet: str | None = None,
        plot_type: str | int | None = None,
        auto_zoom_extents: bool | None = None,
    ) -> bool:
        self._ensure()
        if not path:
            raise ToolError("path is required")

        if auto_zoom_extents is None:
            auto_zoom_extents = True

        has_plot_overrides = any([config_name, style_sheet, plot_type])
        doc = self._doc
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        layout = doc.ActiveLayout
        if layout_name:
            try:
                layout = doc.Layouts.Item(layout_name)
            except Exception:
                layout = doc.ActiveLayout
        try:
            doc.ActiveLayout = layout
        except Exception:
            pass

        if auto_zoom_extents:
            self._zoom_extents(doc)

        # 优先使用 JPGOUT/PNGOUT 等命令导出，避免依赖打印设备。
        if not has_plot_overrides:
            if self._export_image_command(fmt, output_path):
                return True

        if auto_zoom_extents and plot_type is None:
            plot_type = "extents"

        candidates, available = self._plot_device_candidates(fmt, config_name)
        if not candidates and available:
            candidates = list(available)

        style = style_sheet or self.config.plot_style_sheet
        if style:
            try:
                layout.StyleSheet = style
            except Exception:
                pass

        pt = plot_type if plot_type is not None else self.config.plot_type
        try:
            layout.PlotType = self._plot_type_value(pt)
        except Exception:
            pass

        try:
            self._retry_com(lambda: doc.SetVariable("BACKGROUNDPLOT", 0))
        except Exception:
            pass

        last_exc: Exception | None = None
        attempted = False
        for candidate in candidates:
            applied = self._apply_plot_device(layout, candidate)
            if not applied:
                continue

            try:
                layout.RefreshPlotDeviceInfo()
            except Exception:
                pass

            try:
                self._plot_to_file(doc, str(output_path), candidate)
                attempted = True
                if self._wait_for_file(output_path, timeout=60):
                    return True
            except Exception as exc:
                last_exc = exc

        if not attempted:
            try:
                self._plot_to_file(doc, str(output_path), None)
                if self._wait_for_file(output_path, timeout=60):
                    return True
            except Exception as exc:
                last_exc = exc

        if available:
            raise ToolError(
                "no plot device available for export_image. "
                f"attempted={candidates}, available={available}"
            )
        if last_exc:
            raise ToolError(f"export_image failed: {last_exc}") from last_exc
        raise ToolError("export_image failed: no plot device candidates")

    def export_dwg(self, path: str | None) -> bool:
        self._ensure()
        if not path:
            raise ToolError("path is required")
        target = Path(path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        active_name = self._safe_fullname(self._doc)
        if active_name and active_name.lower() == str(target).lower():
            self._retry_com(lambda: self._doc.Save(), retries=3, delay=1.0)
            return True

        self._close_open_document(target)
        self._remove_if_exists(target)
        self._retry_com(lambda: self._doc.SaveAs(str(target)), retries=3, delay=1.0)
        return True

    def import_dwg(self, path: str) -> bool:
        self._ensure(require_doc=False)
        self._doc = self._retry_com(lambda: self._app.Documents.Open(path), retries=3, delay=1.0)
        return True

    def entity_extract(self, scope: str | None = None) -> list[dict[str, Any]]:
        self._ensure()
        entities: list[dict[str, Any]] = []
        for ent in self._doc.ModelSpace:
            try:
                obj_name = getattr(ent, "ObjectName", "")
                layer = getattr(ent, "Layer", "")
                handle = getattr(ent, "Handle", "")
                record = {"type": obj_name, "layer": layer, "handle": handle, "geometry": {}}

                if obj_name == "AcDbLine":
                    record["geometry"] = {
                        "start": list(ent.StartPoint),
                        "end": list(ent.EndPoint),
                    }
                elif obj_name == "AcDbCircle":
                    record["geometry"] = {
                        "center": list(ent.Center),
                        "radius": ent.Radius,
                    }
                elif obj_name == "AcDbArc":
                    record["geometry"] = {
                        "center": list(ent.Center),
                        "radius": ent.Radius,
                        "start_angle": ent.StartAngle,
                        "end_angle": ent.EndAngle,
                    }
                elif obj_name in ("AcDbPolyline", "AcDb2dPolyline", "AcDb3dPolyline"):
                    coords = list(ent.Coordinates)
                    record["geometry"] = {
                        "coordinates": coords,
                        "closed": bool(getattr(ent, "Closed", False)),
                    }
                elif obj_name == "AcDbText":
                    record["geometry"] = {
                        "text": ent.TextString,
                        "position": list(ent.InsertionPoint),
                        "height": ent.Height,
                    }
                elif obj_name == "AcDbMText":
                    record["geometry"] = {
                        "text": ent.Contents,
                        "position": list(ent.InsertionPoint),
                        "height": ent.TextHeight,
                    }

                entities.append(record)
            except Exception:
                continue
        return entities

    def _plot_type_value(self, value: str | int | None) -> int:
        if value is None:
            return 1
        if isinstance(value, int):
            return value
        mapping = {
            "all": 0,
            "display": 1,
            "extents": 2,
            "limits": 2,
            "view": 3,
            "window": 4,
        }
        return mapping.get(str(value).lower(), 1)

    def _export_image_command(self, fmt: str | None, output_path: Path) -> bool:
        ext = (fmt or output_path.suffix.lstrip(".")).lower()
        command_map = {
            "jpg": "JPGOUT",
            "jpeg": "JPGOUT",
            "png": "PNGOUT",
            "tif": "TIFOUT",
            "tiff": "TIFOUT",
            "bmp": "BMPOUT",
        }
        command = command_map.get(ext)
        if not command:
            return False

        doc = self._doc
        file_path = str(output_path).replace("\\", "/")
        filedia = None
        cmddia = None
        try:
            try:
                filedia = doc.GetVariable("FILEDIA")
                cmddia = doc.GetVariable("CMDDIA")
                doc.SetVariable("FILEDIA", 0)
                doc.SetVariable("CMDDIA", 0)
            except Exception:
                filedia = None
                cmddia = None

            cmd_path = f"\"{file_path}\"" if " " in file_path else file_path
            cmd = f"_.{command}\n{cmd_path}\n_ALL\n\n"
            self._retry_com(lambda: doc.SendCommand(cmd), retries=3, delay=0.5)
            return self._wait_for_file(output_path, timeout=60)
        finally:
            try:
                if filedia is not None:
                    doc.SetVariable("FILEDIA", filedia)
                if cmddia is not None:
                    doc.SetVariable("CMDDIA", cmddia)
            except Exception:
                pass

    def _normalize_lisp_path(self, path: str) -> str:
        value = str(Path(path).resolve())
        value = value.replace("\\", "/")
        return value

    def _zoom_extents(self, doc) -> None:
        try:
            self._retry_com(lambda: doc.SendCommand("_.ZOOM\n_E\n"), retries=3, delay=0.5)
        except Exception:
            pass

    def _safe_fullname(self, doc) -> str | None:
        try:
            return str(doc.FullName)
        except Exception:
            return None

    def _close_open_document(self, target: Path) -> None:
        try:
            docs = list(getattr(self._app, "Documents", []))
        except Exception:
            return
        target_norm = str(target).lower()
        for doc in docs:
            name = self._safe_fullname(doc)
            if not name:
                continue
            if name.lower() == target_norm:
                try:
                    doc.Close(False)
                except Exception:
                    pass

    def _remove_if_exists(self, target: Path) -> None:
        try:
            if target.exists():
                target.unlink()
        except Exception:
            pass
        for suffix in (".dwl", ".dwl2"):
            lock_path = target.with_suffix(target.suffix + suffix)
            try:
                if lock_path.exists():
                    lock_path.unlink()
            except Exception:
                pass

    def _plot_device_candidates(
        self,
        fmt: str | None,
        config_name: str | None,
    ) -> tuple[list[str], list[str]]:
        candidates: list[str] = []
        available = self._list_pc3_devices()

        def add(value: str | None) -> None:
            if not value:
                return
            if value not in candidates:
                candidates.append(value)

        add(config_name)
        if fmt:
            ext = str(fmt).lower()
            if ext in ("jpg", "jpeg"):
                add("PublishToWeb JPG.pc3")
            elif ext == "png":
                add("PublishToWeb PNG.pc3")
        add(self.config.plot_config_name)

        if fmt and available:
            ext = str(fmt).lower()
            for device in available:
                if ext in device.lower():
                    add(device)

        for device in available:
            add(device)

        return candidates, available

    def _list_pc3_devices(self) -> list[str]:
        devices: list[str] = []
        for base in self._plot_config_paths():
            if not base.exists():
                continue
            try:
                for path in base.rglob("*.pc3"):
                    devices.append(path.name)
            except Exception:
                continue
        return list(dict.fromkeys(devices))

    def _plot_config_paths(self) -> list[Path]:
        paths: list[Path] = []
        try:
            prefs = getattr(self._app, "Preferences", None)
            files = getattr(prefs, "Files", None)
            raw = getattr(files, "PrinterConfigPath", "") if files else ""
        except Exception:
            raw = ""
        for part in str(raw).split(";"):
            part = part.strip()
            if part:
                paths.append(Path(part))
        return paths

    def _apply_plot_device(self, layout, device: str) -> bool:
        candidates = [device]
        try:
            if Path(device).suffix.lower() == ".pc3":
                candidates.append(Path(device).name)
        except Exception:
            pass
        for candidate in candidates:
            if not candidate:
                continue
            try:
                layout.ConfigName = candidate
            except Exception:
                continue
            try:
                current = str(layout.ConfigName)
                if current:
                    current_name = Path(current).name.lower()
                    target_name = Path(candidate).name.lower()
                    if current.lower() == candidate.lower() or current_name == target_name:
                        return True
            except Exception:
                return True
        return False

    def _plot_to_file(self, doc, path: str, config_name: str | None) -> None:
        if config_name:
            try:
                self._retry_com(lambda: doc.Plot.PlotToFile(path, config_name), retries=3, delay=1.0)
                return
            except Exception:
                pass
        self._retry_com(lambda: doc.Plot.PlotToFile(path), retries=3, delay=1.0)

    def _wait_for_file(self, path: Path, timeout: int = 60) -> bool:
        import time

        start = time.time()
        while time.time() - start < timeout:
            if path.exists():
                return True
            time.sleep(0.5)
        return False

