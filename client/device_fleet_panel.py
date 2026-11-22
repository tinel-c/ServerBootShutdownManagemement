#!/usr/bin/env python3
"""Tkinter Device Fleet panel for the Windows client monitor."""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional

from fleet_bridge import FleetBridge, summarize_rows

logger = logging.getLogger(__name__)

_open_panel: Optional["DeviceFleetPanel"] = None


def raise_device_fleet_panel() -> bool:
    """If a panel is already open, schedule raise and return True."""
    global _open_panel
    if _open_panel is None:
        return False
    try:
        root = _open_panel.root

        def _raise() -> None:
            root.deiconify()
            root.lift()
            root.focus_force()

        root.after(0, _raise)
        return True
    except tk.TclError:
        _open_panel = None
        return False


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
        self.root.geometry("980x520")
        self.root.minsize(720, 400)

        self._rows: List[Dict[str, Any]] = []
        self._selected_id: Optional[str] = None
        self._busy = False

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
        self.upload_btn = ttk.Button(
            btns, text="Upload firmware…", command=self._on_upload, state=tk.DISABLED
        )
        self.upload_btn.pack(side=tk.LEFT, padx=4)

        mid = ttk.Frame(self.root, padding=(8, 0, 8, 0))
        mid.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "status", "fw", "ip", "age", "ota_port", "upload")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", selectmode="browse")
        headings = {
            "id": ("Device", 320),
            "status": ("Status", 80),
            "fw": ("Firmware", 90),
            "ip": ("IP", 120),
            "age": ("Age", 70),
            "ota_port": ("OTA port", 80),
            "upload": ("Upload", 160),
        }
        for key, (label, width) in headings.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, stretch=(key == "id"))

        scroll = ttk.Scrollbar(mid, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill=tk.BOTH)
        ttk.Label(bottom, text="Log").pack(anchor=tk.W)
        self.log = tk.Text(bottom, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="")
        ttk.Label(self.root, textvariable=self.status_var, padding=(8, 0, 8, 8)).pack(
            anchor=tk.W
        )

    def run(self) -> None:
        self._append_log(
            f"Registry: {self.bridge.registry_path}\n"
            f"State: {self.bridge.state_path}"
        )
        # Show cached rows immediately, then start live watch.
        try:
            self._apply_rows(self.bridge.rows())
        except Exception as exc:
            self._append_log(f"Initial rows failed: {exc}")
        self.bridge.start_watching(lambda rows: self.root.after(0, self._apply_rows, rows))
        self.root.mainloop()

    def _on_close(self) -> None:
        global _open_panel
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
        self.summary_var.set(
            f"Online {summary['online_expected']} / Expected {summary['expected']}"
            + (
                f"  (registered {summary['registered']})"
                if summary["registered"] != summary["expected"]
                else ""
            )
        )
        selected = self._selected_id
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
                    iid,
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
        self._update_upload_button()

    def _on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        self._selected_id = sel[0] if sel else None
        self._update_upload_button()

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
        self.refresh_btn.configure(state=tk.DISABLED if busy else tk.NORMAL)
        self._update_upload_button()

    def _on_refresh(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self.status_var.set("Refreshing MQTT sightings…")

        def work() -> None:
            try:
                rows = self.bridge.refresh()
                self.root.after(0, lambda: self._refresh_done(rows, None))
            except Exception as exc:
                self.root.after(0, lambda: self._refresh_done([], exc))

        threading.Thread(target=work, daemon=True).start()

    def _refresh_done(self, rows: List[Dict[str, Any]], err: Optional[BaseException]) -> None:
        self._set_busy(False)
        if err:
            self._append_log(f"Refresh failed: {err}")
            self.status_var.set(f"Refresh failed: {err}")
            return
        self._apply_rows(rows)
        self._append_log("Refresh complete")
        self.status_var.set("Refresh complete")

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
            self.root.after(0, lambda: self._upload_done(row["id"], rc, log))

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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    open_device_fleet_panel({})
