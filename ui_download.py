"""Tab tải nhạc: nhập link, chọn định dạng / chất lượng và hàng đợi tải nhiều bài."""
import os
import re

import customtkinter as ctk
from tkinter import filedialog, messagebox

from download_queue import (
    PENDING, DOWNLOADING, CONVERTING, DONE, ERROR, CANCELLED, ACTIVE_STATUSES, FINISHED_STATUSES,
)
from downloader import AUDIO_FORMATS, MediaDownloader, get_ffmpeg_path
from i18n import t
from platform_utils import open_path_in_explorer, play_audio_file

URL_IN_TEXT = re.compile(r"https?://\S+")
BITRATE_LABELS = {b: f"{b} kbps" for b in AUDIO_FORMATS["mp3"]["bitrates"]}
FORMAT_LABELS = {key: spec["label"] for key, spec in AUDIO_FORMATS.items()}

PLATFORM_BADGES = {
    "YouTube": ("🔴 YouTube Video", "#FF5252"),
    "Facebook": ("🔵 Facebook Video", "#42A5F5"),
    "TikTok": ("⚫ TikTok Video", "#00E676"),
}
STATUS_COLORS = {
    PENDING: "gray70",
    DOWNLOADING: "#90CAF9",
    CONVERTING: "#CE93D8",
    DONE: "#66BB6A",
    ERROR: "#EF5350",
    CANCELLED: "#FFA726",
}


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


class DownloadTab:
    def __init__(self, master, app):
        self.app = app
        self.queue = app.queue
        self._rows = {}
        self._build(master)
        self._on_format_changed(FORMAT_LABELS[app.settings["format"]], save=False)
        self.refresh_queue()
        if not get_ffmpeg_path():
            self.set_status(t("ffmpeg_missing"), "#FFA726")

    # ---------- Giao diện ----------
    def _build(self, master):
        settings = self.app.settings

        # 1. Nhập link
        url_frame = ctk.CTkFrame(master, corner_radius=10)
        url_frame.pack(fill="x", padx=8, pady=(4, 6))

        url_header = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_header.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(url_header, text=t("url_label"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self.platform_badge = ctk.CTkLabel(
            url_header, text=t("badge_waiting"), font=ctk.CTkFont(size=12, weight="bold"), text_color="#64B5F6"
        )
        self.platform_badge.pack(side="right")

        entry_box = ctk.CTkFrame(url_frame, fg_color="transparent")
        entry_box.pack(fill="x", padx=14, pady=(0, 12))
        self.url_entry = ctk.CTkEntry(
            entry_box, placeholder_text=t("url_placeholder"), height=38, font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.bind("<KeyRelease>", self._on_url_input_changed)
        self.url_entry.bind("<Return>", lambda e: self.add_from_entry())

        ctk.CTkButton(entry_box, text=t("btn_paste"), width=70, height=38, command=self._paste_clipboard).pack(
            side="left", padx=(0, 6))
        ctk.CTkButton(
            entry_box, text="✖", width=40, height=38, fg_color="#D32F2F", hover_color="#B71C1C",
            command=self._clear_url,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            entry_box, text=t("btn_add_queue"), height=38, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1976D2", hover_color="#1565C0", command=self.add_from_entry,
        ).pack(side="left")

        # 2. Cài đặt
        settings_frame = ctk.CTkFrame(master, corner_radius=10)
        settings_frame.pack(fill="x", padx=8, pady=6)

        dir_box = ctk.CTkFrame(settings_frame, fg_color="transparent")
        dir_box.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(dir_box, text=t("save_dir_label"), font=ctk.CTkFont(size=13, weight="bold")).pack(
            side="left", padx=(0, 10))
        self.dir_entry = ctk.CTkEntry(dir_box, height=32, font=ctk.CTkFont(size=12))
        self.dir_entry.insert(0, settings["download_dir"])
        self.dir_entry.configure(state="readonly")
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(dir_box, text=t("btn_browse"), width=90, height=32, command=self._browse_directory).pack(
            side="left")

        fmt_box = ctk.CTkFrame(settings_frame, fg_color="transparent")
        fmt_box.pack(fill="x", padx=14, pady=(0, 2))
        ctk.CTkLabel(fmt_box, text=t("format_label"), font=ctk.CTkFont(size=13, weight="bold")).pack(
            side="left", padx=(0, 10))
        self.format_seg = ctk.CTkSegmentedButton(
            fmt_box, values=list(FORMAT_LABELS.values()), command=self._on_format_changed
        )
        self.format_seg.set(FORMAT_LABELS[settings["format"]])
        self.format_seg.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(fmt_box, text=t("quality_label"), font=ctk.CTkFont(size=13, weight="bold")).pack(
            side="left", padx=(0, 10))
        self.bitrate_seg = ctk.CTkSegmentedButton(
            fmt_box, values=list(BITRATE_LABELS.values()), command=self._on_bitrate_changed
        )
        self.bitrate_seg.set(BITRATE_LABELS.get(settings["bitrate"], BITRATE_LABELS["320"]))
        self.bitrate_seg.pack(side="left")

        self.format_hint = ctk.CTkLabel(
            settings_frame, text="", font=ctk.CTkFont(size=12), text_color="gray70", anchor="w", justify="left",
            wraplength=760,
        )
        self.format_hint.pack(fill="x", padx=14, pady=(2, 4))

        opts_box = ctk.CTkFrame(settings_frame, fg_color="transparent")
        opts_box.pack(fill="x", padx=14, pady=(0, 10))
        self.thumb_check = ctk.CTkCheckBox(
            opts_box, text=t("chk_thumbnail"), font=ctk.CTkFont(size=13),
            command=lambda: self.app.update_setting("embed_thumbnail", bool(self.thumb_check.get())),
        )
        self.thumb_check.pack(side="left", padx=(0, 16))
        self.parse_check = ctk.CTkCheckBox(
            opts_box, text=t("chk_parse"), font=ctk.CTkFont(size=13),
            command=lambda: self.app.update_setting("parse_metadata", bool(self.parse_check.get())),
        )
        self.parse_check.pack(side="left")
        for widget, key in ((self.thumb_check, "embed_thumbnail"), (self.parse_check, "parse_metadata")):
            widget.select() if settings[key] else widget.deselect()

        self.clipboard_switch = ctk.CTkSwitch(
            opts_box, text=t("switch_clipboard"), font=ctk.CTkFont(size=13), command=self._toggle_clipboard_monitor
        )
        self.clipboard_switch.select() if settings["clipboard_monitor"] else self.clipboard_switch.deselect()
        self.clipboard_switch.pack(side="right")

        # 3. Hàng đợi
        queue_frame = ctk.CTkFrame(master, corner_radius=10)
        queue_frame.pack(fill="both", expand=True, padx=8, pady=(6, 4))

        queue_header = ctk.CTkFrame(queue_frame, fg_color="transparent")
        queue_header.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(queue_header, text=t("queue_title"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self.summary_label = ctk.CTkLabel(queue_header, text="", font=ctk.CTkFont(size=12), text_color="gray70")
        self.summary_label.pack(side="left", padx=12)
        ctk.CTkButton(
            queue_header, text=t("btn_clear_done"), width=120, height=28, fg_color="#374151", hover_color="#4B5563",
            command=self.queue.clear_finished,
        ).pack(side="right")
        self.btn_cancel = ctk.CTkButton(
            queue_header, text=t("btn_cancel_current"), width=130, height=28, fg_color="#757575",
            hover_color="#616161", command=self.queue.cancel_current,
        )
        self.btn_cancel.pack(side="right", padx=(0, 8))

        self.queue_list = ctk.CTkScrollableFrame(queue_frame, fg_color="transparent")
        self.queue_list.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self.empty_label = ctk.CTkLabel(
            self.queue_list, text=t("queue_empty"), font=ctk.CTkFont(size=12), text_color="gray60"
        )

        self.status_label = ctk.CTkLabel(
            queue_frame, text="", font=ctk.CTkFont(size=12), text_color="gray80", anchor="w"
        )
        self.status_label.pack(fill="x", padx=14, pady=(0, 8))

    # ---------- Nhập link ----------
    def _on_url_input_changed(self, event=None):
        url = self.url_entry.get().strip()
        if not url:
            self.platform_badge.configure(text=t("badge_waiting"), text_color="#64B5F6")
            return
        platform_name = MediaDownloader.identify_platform(url)
        text, color = PLATFORM_BADGES.get(platform_name, (f"🌐 {platform_name}", "#FFD54F"))
        self.platform_badge.configure(text=text, text_color=color)

    def _paste_clipboard(self):
        try:
            text = self.app.clipboard_get()
        except Exception:
            return
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, " ".join(text.split()))
        self._on_url_input_changed()

    def _clear_url(self):
        self.url_entry.delete(0, "end")
        self._on_url_input_changed()

    def add_from_entry(self):
        text = self.url_entry.get().strip()
        if not text:
            messagebox.showwarning(t("dlg_missing_link_title"), t("dlg_missing_link_msg"), parent=self.app)
            return

        added = 0
        for url in URL_IN_TEXT.findall(text) or [text]:
            if not MediaDownloader.is_valid_url(url) and not messagebox.askyesno(
                t("dlg_confirm_title"), t("dlg_unusual_link", url=_shorten(url, 120)), parent=self.app
            ):
                continue
            if self.app.enqueue(url):
                added += 1

        if added:
            self._clear_url()
            self.set_status(t("msg_added", n=added), "#90CAF9")
        else:
            self.set_status(t("msg_already_queued"), "#FFA726")

    def handle_detected_url(self, url: str, platform_name: str):
        """Clipboard Monitor phát hiện link mới: điền vào ô nhập và hỏi có thêm vào hàng đợi không"""
        if any(i.url == url and i.status not in FINISHED_STATUSES for i in self.queue.items):
            return
        if self.url_entry.get().strip() == url:
            return
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        self._on_url_input_changed()

        if messagebox.askyesno(
            title=t("dlg_detect_title", platform=platform_name),
            message=t("dlg_detect_msg", platform=platform_name, url=_shorten(url, 80)),
            parent=self.app,
        ) and self.app.enqueue(url):
            self._clear_url()
            self.set_status(t("msg_added", n=1), "#90CAF9")

    # ---------- Cài đặt ----------
    def _browse_directory(self):
        selected_dir = filedialog.askdirectory(initialdir=self.app.settings["download_dir"])
        if selected_dir:
            self.app.downloader.download_dir = selected_dir
            self.app.update_setting("download_dir", selected_dir)
            self.dir_entry.configure(state="normal")
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, selected_dir)
            self.dir_entry.configure(state="readonly")

    def _on_format_changed(self, label: str, save: bool = True):
        fmt = next(k for k, v in FORMAT_LABELS.items() if v == label)
        self.bitrate_seg.configure(state="normal" if AUDIO_FORMATS[fmt]["bitrates"] else "disabled")
        self.format_hint.configure(text=t(f"fmt_hint_{fmt}"))
        if save:
            self.app.update_setting("format", fmt)

    def _on_bitrate_changed(self, label: str):
        self.app.update_setting("bitrate", label.split()[0])

    def _toggle_clipboard_monitor(self):
        is_on = self.clipboard_switch.get() == 1
        self.app.clipboard_monitor.set_enabled(is_on)
        self.app.update_setting("clipboard_monitor", is_on)

    def set_status(self, text: str, color: str = "gray80"):
        self.status_label.configure(text=text, text_color=color)

    # ---------- Hàng đợi ----------
    def on_queue_change(self, item):
        if item is None or item.id not in self._rows:
            self.refresh_queue()
        else:
            self._update_row(item)
            self._update_summary()

    def refresh_queue(self):
        items = list(self.queue.items)
        ids = {i.id for i in items}
        for item_id in [k for k in self._rows if k not in ids]:
            self._rows.pop(item_id)["frame"].destroy()
        for item in items:
            self._update_row(item)

        if items:
            self.empty_label.pack_forget()
        else:
            self.empty_label.pack(pady=24)
        self._update_summary()

    def _update_summary(self):
        counts = self.queue.counts()
        self.summary_label.configure(text=t("queue_summary", **counts) if counts["total"] else "")
        self.btn_cancel.configure(state="normal" if counts["active"] else "disabled")

    def _create_row(self, item):
        row = ctk.CTkFrame(self.queue_list, corner_radius=8, fg_color="#1E293B")
        row.pack(fill="x", padx=4, pady=3)
        row.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(row, text="", font=ctk.CTkFont(size=13, weight="bold"), anchor="w", justify="left")
        title.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=(6, 0))
        detail = ctk.CTkLabel(row, text="", font=ctk.CTkFont(size=12), anchor="w", justify="left")
        detail.grid(row=1, column=0, sticky="ew", padx=(12, 6), pady=(0, 6))
        bar = ctk.CTkProgressBar(row, width=120, height=8)
        bar.grid(row=0, column=1, rowspan=2, padx=6)
        buttons = ctk.CTkFrame(row, fg_color="transparent")
        buttons.grid(row=0, column=2, rowspan=2, padx=(4, 10), pady=6)
        widgets = {"frame": row, "title": title, "detail": detail, "bar": bar, "buttons": buttons, "status": None}
        self._rows[item.id] = widgets
        return widgets

    def _update_row(self, item):
        widgets = self._rows.get(item.id) or self._create_row(item)
        fmt_text = FORMAT_LABELS.get(item.fmt, item.fmt.upper())
        if AUDIO_FORMATS.get(item.fmt, {}).get("bitrates"):
            fmt_text += f" {item.bitrate} kbps"

        widgets["title"].configure(text=_shorten(item.title or item.url, 64))
        widgets["detail"].configure(
            text=f"{fmt_text} · {_shorten(self._status_text(item), 110)}",
            text_color=STATUS_COLORS.get(item.status, "gray80"),
        )
        widgets["bar"].set(item.percent / 100.0)

        if widgets["status"] != item.status:
            widgets["status"] = item.status
            self._build_row_buttons(widgets["buttons"], item)

    @staticmethod
    def _status_text(item) -> str:
        if item.status == DOWNLOADING:
            if not item.percent and not item.speed:
                return t("st_connecting")
            speed = f"{item.speed / (1024 * 1024):.1f} MB/s" if item.speed else "N/A"
            eta = f"{int(item.eta)}s" if item.eta else "..."
            return t("st_downloading", percent=item.percent, speed=speed, eta=eta)
        if item.status == ERROR:
            return t("st_error", error=item.error)
        return t({
            PENDING: "st_pending",
            CONVERTING: "st_converting",
            DONE: "st_done",
            CANCELLED: "st_cancelled",
        }[item.status])

    def _build_row_buttons(self, box, item):
        for child in box.winfo_children():
            child.destroy()

        def button(text, command, color="#374151", hover="#4B5563"):
            ctk.CTkButton(box, text=text, width=10, height=28, fg_color=color, hover_color=hover,
                          command=command).pack(side="left", padx=2)

        if item.status == DONE:
            button(t("btn_open_folder"), lambda: open_path_in_explorer(item.file_path))
            button(t("btn_play"), lambda: self._play(item.file_path), "#2E7D32", "#1B5E20")
            button(t("btn_edit"), lambda: self.app.open_in_editor(item.file_path), "#6A1B9A", "#4A148C")
        elif item.status in ACTIVE_STATUSES:
            button(t("ed_cancel_export"), self.queue.cancel_current, "#757575", "#616161")
        elif item.status in (ERROR, CANCELLED):
            button(t("btn_retry"), lambda: self.queue.retry(item.id), "#1976D2", "#1565C0")
            button(t("btn_remove"), lambda: self.queue.remove(item.id), "#D32F2F", "#B71C1C")
        else:
            button(t("btn_remove"), lambda: self.queue.remove(item.id), "#D32F2F", "#B71C1C")

    def _play(self, path: str):
        if path and os.path.exists(path):
            play_audio_file(path)
        else:
            messagebox.showinfo(t("dlg_notice_title"), t("file_not_found"), parent=self.app)
