import os
import re
import shutil
import sys
import tempfile
import tkinter as tk

import customtkinter as ctk
from tkinter import messagebox

import config
from audio_tools import AudioPlayer
from clipboard_monitor import ClipboardMonitor
from download_queue import DownloadQueue
from downloader import AUDIO_FORMATS, MediaDownloader, default_download_dir
from i18n import LANGUAGES, get_language, set_language, t
from platform_utils import resource_path
from ui_download import DownloadTab
from ui_editor import EditorState, EditorTab
from version import __version__

DEFAULT_WIDTH, DEFAULT_HEIGHT = 920, 720


class MediaToMp3App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Cài đặt đã lưu từ lần chạy trước
        self.settings = config.load_settings()
        self._sanitize_settings()
        set_language(self.settings["language"])

        # Giao diện & Chủ đề
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.geometry(self._initial_geometry())
        self.minsize(820, 600)
        self._set_icon()

        # Khởi tạo dịch vụ (giữ nguyên khi giao diện được dựng lại lúc đổi ngôn ngữ)
        self.downloader = MediaDownloader(download_dir=self.settings["download_dir"])
        self.queue = DownloadQueue(self.downloader, on_change=lambda item: self.post(self._on_queue_change, item))
        self.editor_state = EditorState()
        self.player = AudioPlayer()
        self.temp_dir = tempfile.mkdtemp(prefix="media-to-mp3-")

        self._root_frame = None
        self._build_ui()

        # Khởi động Clipboard Monitor
        self.clipboard_monitor = ClipboardMonitor(on_detected=self._on_clipboard_detected)
        self.clipboard_monitor.set_enabled(self.settings["clipboard_monitor"])
        self.clipboard_monitor.start()

        # Đóng ứng dụng an toàn
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _sanitize_settings(self):
        s = self.settings
        if not s["download_dir"] or not os.path.isdir(s["download_dir"]):
            s["download_dir"] = default_download_dir()
        if s["format"] not in AUDIO_FORMATS:
            s["format"] = "mp3"
        if s["bitrate"] not in AUDIO_FORMATS["mp3"]["bitrates"]:
            s["bitrate"] = "320"
        if s["language"] not in LANGUAGES:
            s["language"] = "vi"
        # Chỉ nhớ kích thước cửa sổ, không nhớ vị trí (tránh mở ra ngoài màn hình khi đổi màn hình)
        if not re.fullmatch(r"\d{3,5}x\d{3,5}", s["window_geometry"]):
            s["window_geometry"] = ""

    def _set_icon(self):
        try:
            if sys.platform.startswith("win"):
                self.iconbitmap(resource_path(os.path.join("packaging", "icon.ico")))
            else:
                self._icon_image = tk.PhotoImage(file=resource_path(os.path.join("packaging", "icon.png")))
                self.iconphoto(True, self._icon_image)
        except tk.TclError:
            pass

    def _initial_geometry(self) -> str:
        """Kích thước đã lưu hoặc mặc định, không cao quá màn hình (vd. laptop 1080p để scaling 150%)"""
        scale = ctk.ScalingTracker.get_window_scaling(self)
        max_width = int(self.winfo_screenwidth() / scale) - 40
        max_height = int(self.winfo_screenheight() / scale) - 80
        width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
        if self.settings["window_geometry"]:
            width, height = map(int, self.settings["window_geometry"].split("x"))
        return f"{min(width, max_width)}x{max(600, min(height, max_height))}"

    def _build_ui(self, selected_tab: str = "download"):
        self.title(f"{t('window_title')} v{__version__}")
        self._root_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._root_frame.pack(fill="both", expand=True)

        # Header: tiêu đề + chọn ngôn ngữ
        header = ctk.CTkFrame(self._root_frame, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(14, 4))
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_box, text=t("app_title"), font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text=t("app_subtitle"), font=ctk.CTkFont(size=13), text_color="gray70").pack(
            anchor="w", pady=(2, 0))

        self.language_seg = ctk.CTkSegmentedButton(
            header, values=list(LANGUAGES.values()), command=self._on_language_selected
        )
        self.language_seg.set(LANGUAGES[get_language()])
        self.language_seg.pack(side="right", anchor="n", pady=(4, 0))

        self.tabs = ctk.CTkTabview(self._root_frame)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        download_frame = self.tabs.add(t("tab_download"))
        editor_frame = self.tabs.add(t("tab_editor"))
        self.download_tab = DownloadTab(download_frame, self)
        self.editor_tab = EditorTab(editor_frame, self)
        if selected_tab == "editor":
            self.tabs.set(t("tab_editor"))

    # ---------- Tiện ích dùng chung cho các tab ----------
    def post(self, func, *args):
        """Chạy func trên luồng giao diện; gọi được từ luồng nền. Bỏ qua nếu cửa sổ đã đóng."""
        try:
            self.after(0, func, *args)
        except (RuntimeError, tk.TclError):
            pass

    def call_editor(self, method: str, *args):
        getattr(self.editor_tab, method)(*args)

    def update_setting(self, key: str, value):
        self.settings[key] = value
        config.save_settings(self.settings)

    def enqueue(self, url: str):
        s = self.settings
        return self.queue.add(
            url,
            fmt=s["format"],
            bitrate=s["bitrate"],
            output_dir=s["download_dir"],
            embed_thumbnail=s["embed_thumbnail"],
            parse_metadata=s["parse_metadata"],
        )

    def open_in_editor(self, path: str):
        self.tabs.set(t("tab_editor"))
        self.editor_tab.add_files([path])

    # ---------- Sự kiện ----------
    def _on_language_selected(self, label: str):
        lang = next(k for k, v in LANGUAGES.items() if v == label)
        if lang == get_language():
            return
        if self.editor_state.exporting:
            self.language_seg.set(LANGUAGES[get_language()])
            messagebox.showinfo(t("dlg_notice_title"), t("busy_language"), parent=self)
            return
        # Dựng lại giao diện sau khi callback của nút kết thúc (không hủy widget ngay trong callback của nó)
        self.after(10, self._rebuild_ui, lang)

    def _rebuild_ui(self, lang: str):
        selected = "editor" if self.tabs.get() == t("tab_editor") else "download"
        self.editor_tab.collect_state()
        self.editor_tab.stop_preview()
        set_language(lang)
        self.update_setting("language", lang)
        self._root_frame.destroy()
        self._build_ui(selected)

    def _on_queue_change(self, item):
        self.download_tab.on_queue_change(item)

    def _on_clipboard_detected(self, url: str, platform_name: str):
        """Được gọi từ ClipboardMonitor thread khi phát hiện link mới"""
        self.post(lambda: self.download_tab.handle_detected_url(url, platform_name))

    def _on_close(self):
        if self.queue.is_busy or self.editor_state.exporting:
            if not messagebox.askyesno(t("dlg_quit_title"), t("dlg_quit_msg"), parent=self):
                return

        if self.state() == "normal":
            # winfo_* trả về pixel thật; đổi về kích thước logic của CustomTkinter khi màn hình có scaling
            scale = ctk.ScalingTracker.get_window_scaling(self)
            self.settings["window_geometry"] = (
                f"{round(self.winfo_width() / scale)}x{round(self.winfo_height() / scale)}"
            )
        config.save_settings(self.settings)

        self.clipboard_monitor.stop()
        self.queue.cancel_current()
        self.editor_state.cancel_event.set()
        self.player.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.destroy()


def main():
    app = MediaToMp3App()
    app.mainloop()


if __name__ == "__main__":
    main()
