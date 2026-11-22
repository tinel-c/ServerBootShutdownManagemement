#!/usr/bin/env python3
"""Tkinter Device Fleet panel for the Windows client monitor."""

from __future__ import annotations

import logging
import queue
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional

from device_commands import commands_for, format_status, status_topics
from fleet_bridge import FleetBridge, summarize_rows

logger = logging.getLogger(__name__)

_open_panel: Optional["DeviceFleetPanel"] = None


def _device_label(row: Dict[str, Any]) -> str:
    if row.get("kind") != "tasmota":
        return str(row.get("id") or "")
    name = str(row.get("name") or row.get("topic") or row.get("id") or "")
    topic = str(row.get("topic") or "")
    if topic and topic != name:
        return f"{name} ({topic})"
    return name


def raise_device_fleet_panel() -> bool:
    """If a panel is already open, schedule raise and return True."""
    global _open_panel
    if _open_panel is None:
        return False
    try:
        panel = _open_panel

        def _raise() -> None:
            panel.root.deiconify()
            panel.root.lift()
            panel.root.focus_force()

        # The tray menu runs on another thread. Tk must be touched only on its own thread.
        panel.post(_raise)
        return True
    except tk.TclError:
        _open_panel = None
        return False


def fleet_icon(size: int):
    """Square fleet mark: a blue tile and four device dots."""
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = max(1, size // 16)
    radius = max(3, size // 5)
    draw.rounded_rectangle(
        (margin, margin, size - margin - 1, size - margin - 1),
        radius=radius,
        fill=(22, 64, 110, 255),
    )
    colors = ((72, 199, 116, 255), (72, 199, 116, 255), (245, 184, 61, 255), (180, 198, 214, 255))
    dot = max(3, size // 7)
    gap = max(dot + 2, size // 5)
    origin = (size - gap) // 2
    for index, color in enumerate(colors):
        col = index % 2
        row_index = index // 2
        left = origin + col * gap - dot // 2
        top = origin + row_index * gap - dot // 2
        draw.ellipse((left, top, left + dot, top + dot), fill=color)
    return image


def apply_window_icon(root: tk.Tk) -> None:
    """Title-bar and taskbar icon. Keeps the PhotoImage alive on the window."""
    from PIL import ImageTk

    image = fleet_icon(32)
    photo = ImageTk.PhotoImage(image)
    root.iconphoto(True, photo)
    root._fleet_icon_photo = photo  # type: ignore[attr-defined]
    try:
        icon_path = Path(tempfile.gettempdir()) / "device_fleet.ico"
        fleet_icon(32).save(icon_path, format="ICO", sizes=[(16, 16), (32, 32)])
        root.iconbitmap(default=str(icon_path))
    except Exception:
        logger.debug("Taskbar icon was not applied", exc_info=True)


def open_device_fleet_panel(config: Optional[Dict[str, Any]] = None) -> None:
    """Open (or raise) the single Device Fleet window (call from the Tk/main thread)."""
    global _open_panel
    if raise_device_fleet_panel():
        # Already open; keep existing mainloop.
        return

    panel = DeviceFleetPanel(config or {})
    _open_panel = panel
    panel.run()


class DeviceFleetPanel:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bridge = FleetBridge(config)
        self.root = tk.Tk()
        self.root.title("Device Fleet")
        self.root.geometry("1120x780")
        self.root.minsize(900, 640)
        apply_window_icon(self.root)

        self._rows: List[Dict[str, Any]] = []
        self._selected_id: Optional[str] = None
        self._busy = False
        self._ui_queue: queue.Queue = queue.Queue()
        self._ui_open = True
        self._live_status: Dict[str, str] = {}
        self._detail_stop: Optional[threading.Event] = None
        self._command_device: Optional[str] = None

        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        self.summary_var = tk.StringVar(value="Online — / Expected —")
        ttk.Label(top, textvariable=self.summary_var, font=("Segoe UI", 11, "bold")).pack(
            side=tk.LEFT
        )

        btns = ttk.Frame(top)
        btns.pack(side=tk.RIGHT)
        self.refresh_btn = ttk.Button(btns, text="Refresh", command=self._on_refresh)
        self.refresh_btn.pack(side=tk.LEFT, padx=4)
        self.scan_btn = ttk.Button(btns, text="Scan Tasmota", command=self._on_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=4)
        self.upload_btn = ttk.Button(
            btns, text="Upload firmware…", command=self._on_upload, state=tk.DISABLED
        )
        self.upload_btn.pack(side=tk.LEFT, padx=4)

        mid = ttk.Frame(self.root, padding=(8, 0, 8, 0))
        mid.pack(fill=tk.BOTH, expand=True)

        cols = ("kind", "id", "status", "fw", "ip", "age", "ota_port", "upload")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", selectmode="browse")
        headings = {
            "kind": ("Kind", 90),
            "id": ("Device", 340),
            "status": ("Status", 80),
            "fw": ("Firmware", 140),
            "ip": ("IP", 120),
            "age": ("Age", 70),
            "ota_port": ("OTA port", 80),
            "upload": ("Upload", 180),
        }
        for key, (label, width) in headings.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, stretch=(key == "id"))

        scroll = ttk.Scrollbar(mid, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        detail = ttk.LabelFrame(self.root, text="Selected device", padding=8)
        detail.pack(fill=tk.BOTH, expand=False, padx=8, pady=(8, 0))
        self.detail_title = tk.StringVar(value="Select a device")
        ttk.Label(detail, textvariable=self.detail_title, font=("Segoe UI", 10, "bold")).pack(
            anchor=tk.W
        )
        self.status_text = tk.Text(detail, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=(4, 6))

        cmd_wrap = ttk.Frame(detail)
        cmd_wrap.pack(fill=tk.BOTH, expand=False)
        self.cmd_canvas = tk.Canvas(cmd_wrap, height=150, highlightthickness=0)
        cmd_scroll = ttk.Scrollbar(cmd_wrap, orient=tk.VERTICAL, command=self.cmd_canvas.yview)
        self.cmd_inner = ttk.Frame(self.cmd_canvas)
        self.cmd_inner.bind(
            "<Configure>",
            lambda _event: self.cmd_canvas.configure(scrollregion=self.cmd_canvas.bbox("all")),
        )
        self.cmd_canvas.create_window((0, 0), window=self.cmd_inner, anchor="nw")
        self.cmd_canvas.configure(yscrollcommand=cmd_scroll.set)
        self.cmd_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cmd_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        bottom = ttk.Frame(self.root, padding=(8, 4, 8, 0))
        bottom.pack(fill=tk.BOTH)
        ttk.Label(bottom, text="Log").pack(anchor=tk.W)
        self.log = tk.Text(bottom, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="")
        ttk.Label(self.root, textvariable=self.status_var, padding=(8, 0, 8, 8)).pack(
            anchor=tk.W
        )

    def run(self) -> None:
        self._append_log(
            f"Catalog: {self.bridge.catalog_note}\n"
            f"Registry file: {self.bridge.registry_path}\n"
            f"State: {self.bridge.state_path}"
        )
        # Show cached rows immediately, then start live watch.
        try:
            self._apply_rows(self.bridge.rows())
        except Exception as exc:
            self._append_log(f"Initial rows failed: {exc}")
        self.bridge.start_watching(
            lambda rows: self.post(lambda current=rows: self._apply_rows(current))
        )
        self._drain_ui()
        self.root.mainloop()

    def post(self, callback) -> None:
        """Queue a UI callback. Safe to call from MQTT and scan threads."""
        self._ui_queue.put(callback)

    def _drain_ui(self) -> None:
        if not self._ui_open:
            return
        try:
            while True:
                callback = self._ui_queue.get_nowait()
                try:
                    callback()
                except Exception:
                    logger.exception("Device Fleet UI update failed")
        except queue.Empty:
            pass
        try:
            self.root.after(200, self._drain_ui)
        except tk.TclError:
            self._ui_open = False

    def _on_close(self) -> None:
        global _open_panel
        self._ui_open = False
        self._stop_detail_listen()
        self.bridge.stop_watching()
        _open_panel = None
        self.root.destroy()

    def _append_log(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text.rstrip() + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _apply_rows(self, rows: List[Dict[str, Any]]) -> None:
        self._rows = rows or []
        summary = summarize_rows(self._rows)
        extra = ""
        if summary["registered"] != summary["expected"]:
            extra += f"  (registered {summary['registered']})"
        if summary.get("tasmota"):
            extra += f"   Tasmota {summary['tasmota_online']}/{summary['tasmota']}"
        self.summary_var.set(
            f"Online {summary['online_expected']} / Expected {summary['expected']}{extra}"
        )
        selected = self._selected_id
        self.tree.unbind("<<TreeviewSelect>>")
        try:
            self._fill_tree(selected)
        finally:
            self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self._update_upload_button()
        self._show_status()

    def _fill_tree(self, selected: Optional[str]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self._rows:
            age = f"{row['age_s']}s" if row.get("age_s") is not None else "—"
            upload = "ready" if row.get("can_upload") else (row.get("upload_reason") or "—")
            iid = row["id"]
            self.tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(
                    "Tasmota" if row.get("kind") == "tasmota" else "Firmware",
                    _device_label(row),
                    "online" if row.get("online") else "offline",
                    row.get("fw") or "—",
                    row.get("ip") or "—",
                    age,
                    row.get("ota_port") or "—",
                    upload,
                ),
            )
        if selected and self.tree.exists(selected):
            self.tree.selection_set(selected)
            self.tree.see(selected)
        elif selected:
            self._selected_id = None

    def _on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        device_id = sel[0] if sel else None
        changed = device_id != self._selected_id
        self._selected_id = device_id
        self._update_upload_button()
        if changed:
            self._live_status = {}
            self._show_commands()
            self._listen_selected()
        self._show_status()

    def _show_commands(self) -> None:
        for child in self.cmd_inner.winfo_children():
            child.destroy()
        row = self._selected_row()
        if row is None:
            self.detail_title.set("Select a device")
            self._command_device = None
            return
        self.detail_title.set(_device_label(row))
        self._command_device = str(row["id"])
        commands = commands_for(row)
        if not commands:
            ttk.Label(self.cmd_inner, text="No commands for this device").grid(row=0, column=0, sticky="w")
            return
        columns = 4
        for index, (label, topic, payload) in enumerate(commands):
            button = ttk.Button(
                self.cmd_inner,
                text=label,
                command=lambda topic=topic, payload=payload, label=label: self._send_command(
                    label, topic, payload
                ),
            )
            button.grid(row=index // columns, column=index % columns, padx=3, pady=3, sticky="ew")

    def _show_status(self) -> None:
        row = self._selected_row()
        text = "Select a device to see its status." if row is None else format_status(row, self._live_status)
        self.status_text.configure(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, text)
        self.status_text.configure(state=tk.DISABLED)

    def _listen_selected(self) -> None:
        self._stop_detail_listen()
        row = self._selected_row()
        topics = status_topics(row) if row else []
        if not topics:
            return
        stop = threading.Event()
        self._detail_stop = stop

        def on_message(topic: str, payload: str) -> None:
            self.post(lambda topic=topic, payload=payload: self._note_live(topic, payload))

        def work() -> None:
            try:
                self.bridge.listen_topics(topics, on_message, stop)
            except Exception as exc:
                self.post(lambda exc=exc: self._append_log(f"Status listen failed: {exc}"))

        threading.Thread(target=work, name="fleet-detail", daemon=True).start()

    def _stop_detail_listen(self) -> None:
        if self._detail_stop is not None:
            self._detail_stop.set()
            self._detail_stop = None

    def _note_live(self, topic: str, payload: str) -> None:
        self._live_status[topic] = payload
        self._show_status()

    def _send_command(self, label: str, topic: str, payload: str) -> None:
        if topic == "sms/gateway/command/send" and payload == "":
            self._sms_dialog()
            return
        self._append_log(f"{label} → {topic} {payload}")

        def work() -> None:
            try:
                self.bridge.publish_mqtt(topic, payload)
                self.post(lambda: self._append_log(f"Sent {label}"))
            except Exception as exc:
                self.post(lambda exc=exc: self._append_log(f"{label} failed: {exc}"))

        threading.Thread(target=work, daemon=True).start()

    def _sms_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Send SMS")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Number").grid(row=0, column=0, sticky="w")
        number = ttk.Entry(frame, width=28)
        number.grid(row=0, column=1, padx=(8, 0), pady=4)
        ttk.Label(frame, text="Text").grid(row=1, column=0, sticky="w")
        body = ttk.Entry(frame, width=28)
        body.grid(row=1, column=1, padx=(8, 0), pady=4)

        def send() -> None:
            import json

            to = number.get().strip()
            text = body.get().strip()
            if not to or not text:
                messagebox.showerror("Send SMS", "Number and text are required.", parent=dialog)
                return
            payload = json.dumps({"to": to, "text": text}, ensure_ascii=False)
            dialog.destroy()
            self._send_command("Send SMS", "sms/gateway/command/send", payload)

        ttk.Button(frame, text="Send", command=send).grid(row=2, column=1, sticky="e", pady=(8, 0))
        number.focus_set()

    def _selected_row(self) -> Optional[Dict[str, Any]]:
        if not self._selected_id:
            return None
        for row in self._rows:
            if row["id"] == self._selected_id:
                return row
        return None

    def _update_upload_button(self) -> None:
        row = self._selected_row()
        if self._busy or not row or not row.get("can_upload"):
            self.upload_btn.configure(state=tk.DISABLED)
            if row and not row.get("can_upload"):
                self.status_var.set(row.get("upload_reason") or "Upload unavailable")
            elif not row:
                self.status_var.set("Select a device to upload firmware")
            return
        self.upload_btn.configure(state=tk.NORMAL)
        self.status_var.set(f"Ready to upload to {row['id']} @ {row['ip']}")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.refresh_btn.configure(state=state)
        self.scan_btn.configure(state=state)
        self._update_upload_button()

    def _on_refresh(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self.status_var.set("Fetching catalog and MQTT sightings…")

        def work() -> None:
            try:
                rows = self.bridge.refresh(reload_catalog=True)
                note = self.bridge.catalog_note
                self.post(lambda: self._refresh_done(rows, None, note))
            except Exception as exc:
                self.post(lambda: self._refresh_done([], exc, ""))

        threading.Thread(target=work, daemon=True).start()

    def _refresh_done(
        self,
        rows: List[Dict[str, Any]],
        err: Optional[BaseException],
        note: str = "",
    ) -> None:
        self._set_busy(False)
        if err:
            self._append_log(f"Refresh failed: {err}")
            self.status_var.set(f"Refresh failed: {err}")
            return
        self._apply_rows(rows)
        if note:
            self._append_log(f"Catalog: {note}")
        self._append_log("Refresh complete")
        self.status_var.set("Refresh complete")

    def _on_scan(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self.status_var.set("Scanning Tasmota on MQTT and the LAN…")
        self._append_log("Tasmota scan started")

        def work() -> None:
            try:
                report = self.bridge.scan_tasmota()
                rows = self.bridge.rows()
                self.post(lambda: self._scan_done(rows, report, None))
            except Exception as exc:
                self.post(lambda: self._scan_done([], {}, exc))

        threading.Thread(target=work, daemon=True).start()

    def _scan_done(
        self,
        rows: List[Dict[str, Any]],
        report: Dict[str, Any],
        err: Optional[BaseException],
    ) -> None:
        self._set_busy(False)
        if err:
            self._append_log(f"Tasmota scan failed: {err}")
            self.status_var.set(f"Tasmota scan failed: {err}")
            return
        self._apply_rows(rows)
        added = report.get("added") or []
        self._append_log(
            f"Tasmota scan: MQTT {report.get('mqtt', 0)}, "
            f"HTTP {report.get('http', 0)}, "
            f"added {len(added)}, updated {len(report.get('updated') or [])}"
        )
        if report.get("subnets"):
            self._append_log("HTTP subnets: " + ", ".join(report["subnets"]))
        if report.get("catalog_path"):
            self._append_log(f"Updated {report['catalog_path']}")
        if report.get("error"):
            self._append_log(str(report["error"]))
        for device_id in added:
            self._append_log(f"  + {device_id}")
        self.status_var.set(
            f"Tasmota scan finished ({report.get('mqtt', 0)} MQTT, {report.get('http', 0)} HTTP)"
        )

    def _on_upload(self) -> None:
        row = self._selected_row()
        if not row or not row.get("can_upload") or self._busy:
            return
        path = filedialog.askopenfilename(
            title=f"Firmware for {row['id']}",
            filetypes=[("Firmware binary", "*.bin"), ("All files", "*.*")],
        )
        if not path:
            return
        bin_path = Path(path)
        if not messagebox.askyesno(
            "Confirm OTA",
            f"Flash {bin_path.name} to\n{row['id']}\n{row['ip']}:{row['ota_port']}?",
        ):
            return

        self._set_busy(True)
        self.status_var.set(f"Uploading to {row['id']}…")
        self._append_log(f"OTA start → {row['id']}  {bin_path}")

        def work() -> None:
            rc, log = self.bridge.flash(row["id"], bin_path)
            self.post(lambda: self._upload_done(row["id"], rc, log))

        threading.Thread(target=work, daemon=True).start()

    def _upload_done(self, device_id: str, rc: int, log: str) -> None:
        if log:
            self._append_log(log)
        if rc == 0:
            self._append_log(f"OTA ok → {device_id}")
            self.status_var.set(f"OTA ok → {device_id}")
            messagebox.showinfo("OTA", f"Firmware uploaded to {device_id}")
        else:
            self._append_log(f"OTA failed (exit {rc}) → {device_id}")
            self.status_var.set(f"OTA failed (exit {rc})")
            messagebox.showerror("OTA failed", f"Upload to {device_id} failed (exit {rc}).\nSee log.")
        self._set_busy(False)
        # One more refresh after reboot settle.
        self._on_refresh()


def main(argv: Optional[list] = None) -> int:
    """Entry point for the separate Device Fleet process."""
    import argparse
    import json

    from fleet_bridge import claim_panel_process, raise_device_fleet_window, release_panel_process

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", default="")
    args, _unknown = parser.parse_known_args(argv)
    config: Dict[str, Any] = {}
    if args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if not claim_panel_process():
        raise_device_fleet_window()
        return 0
    try:
        logging.basicConfig(level=logging.INFO)
        open_device_fleet_panel(config)
    finally:
        release_panel_process()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
