import os
import sys
import threading
import platform
import subprocess
from typing import Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox

from downloader import MediaDownloader, get_ffmpeg_path
from clipboard_monitor import ClipboardMonitor


def open_path_in_explorer(path: str):
    """Mở thư mục hoặc file trong trình quản lý file của Windows/Linux/macOS"""
    try:
        if platform.system() == "Windows":
            if os.path.isfile(path):
                # Chọn trực tiếp file trong File Explorer
                subprocess.run(['explorer', '/select,', os.path.normpath(path)], check=False)
            else:
                os.startfile(os.path.normpath(path))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", "-R" if os.path.isfile(path) else "", path])
        else:
            # Linux (X11 / Wayland)
            target = os.path.dirname(path) if os.path.isfile(path) else path
            subprocess.Popen(["xdg-open", target])
    except Exception as e:
        print(f"Không thể mở đường dẫn: {e}")


def play_audio_file(file_path: str):
    """Mở phát file MP3 bằng trình phát nhạc mặc định của hệ thống"""
    try:
        if platform.system() == "Windows":
            os.startfile(os.path.normpath(file_path))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])
    except Exception as e:
        print(f"Không thể phát file: {e}")


class MediaToMp3App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Cấu hình cửa sổ chính
        self.title("Media to MP3 Converter - YouTube & Facebook")
        self.geometry("720x650")
        self.minsize(650, 600)

        # Giao diện & Chủ đề
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Khởi tạo dịch vụ
        self.downloader = MediaDownloader()
        self.last_downloaded_file: Optional[str] = None
        self.is_downloading = False

        # Xây dựng giao diện
        self._init_ui()

        # Kiểm tra FFmpeg cảnh báo nếu thiếu
        self._check_ffmpeg()

        # Khởi động Clipboard Monitor
        self.clipboard_monitor = ClipboardMonitor(on_detected=self._on_clipboard_detected)
        self.clipboard_monitor.start()

        # Đóng ứng dụng an toàn
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_ui(self):
        # 1. Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🎵 Media to MP3 Downloader",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Hỗ trợ chuyển đổi video từ YouTube & Facebook sang MP3 chất lượng cao (320kbps)",
            font=ctk.CTkFont(size=13),
            text_color="gray70"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # 2. Input URL Frame
        url_frame = ctk.CTkFrame(self, corner_radius=10)
        url_frame.pack(fill="x", padx=24, pady=10)

        url_header_box = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_header_box.pack(fill="x", padx=16, pady=(12, 6))

        url_title = ctk.CTkLabel(
            url_header_box,
            text="Đường dẫn Video (URL):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        url_title.pack(side="left")

        self.platform_badge = ctk.CTkLabel(
            url_header_box,
            text="Chờ liên kết...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#64B5F6"
        )
        self.platform_badge.pack(side="right")

        entry_box = ctk.CTkFrame(url_frame, fg_color="transparent")
        entry_box.pack(fill="x", padx=16, pady=(0, 14))

        self.url_entry = ctk.CTkEntry(
            entry_box,
            placeholder_text="Dán liên kết YouTube hoặc Facebook tại đây...",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.bind("<KeyRelease>", self._on_url_input_changed)

        self.btn_paste = ctk.CTkButton(
            entry_box,
            text="📋 Dán",
            width=70,
            height=38,
            command=self._paste_clipboard
        )
        self.btn_paste.pack(side="left", padx=(0, 6))

        self.btn_clear = ctk.CTkButton(
            entry_box,
            text="✖",
            width=40,
            height=38,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            command=self._clear_url
        )
        self.btn_clear.pack(side="left")

        # 3. Settings Frame
        settings_frame = ctk.CTkFrame(self, corner_radius=10)
        settings_frame.pack(fill="x", padx=24, pady=10)

        # 3.1. Thư mục lưu
        dir_box = ctk.CTkFrame(settings_frame, fg_color="transparent")
        dir_box.pack(fill="x", padx=16, pady=(12, 8))

        dir_label = ctk.CTkLabel(dir_box, text="Thư mục lưu:", font=ctk.CTkFont(size=13, weight="bold"))
        dir_label.pack(side="left", padx=(0, 10))

        self.dir_entry = ctk.CTkEntry(dir_box, height=32, font=ctk.CTkFont(size=12))
        self.dir_entry.insert(0, self.downloader.download_dir)
        self.dir_entry.configure(state="readonly")
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_browse = ctk.CTkButton(
            dir_box,
            text="📁 Duyệt...",
            width=90,
            height=32,
            command=self._browse_directory
        )
        self.btn_browse.pack(side="left")

        # 3.2. Chất lượng âm thanh & Tự động phát hiện Clipboard
        opts_box = ctk.CTkFrame(settings_frame, fg_color="transparent")
        opts_box.pack(fill="x", padx=16, pady=(0, 14))

        quality_label = ctk.CTkLabel(opts_box, text="Chất lượng MP3:", font=ctk.CTkFont(size=13, weight="bold"))
        quality_label.pack(side="left", padx=(0, 10))

        self.bitrate_seg = ctk.CTkSegmentedButton(
            opts_box,
            values=["320 kbps (Cao cấp)", "192 kbps (Chuẩn)", "128 kbps (Nhẹ)"],
            command=self._on_bitrate_changed
        )
        self.bitrate_seg.set("320 kbps (Cao cấp)")
        self.bitrate_seg.pack(side="left", padx=(0, 20))

        self.clipboard_switch = ctk.CTkSwitch(
            opts_box,
            text="Tự động nhận diện khi Copy",
            font=ctk.CTkFont(size=13),
            command=self._toggle_clipboard_monitor
        )
        self.clipboard_switch.select()
        self.clipboard_switch.pack(side="right")

        # 4. Action & Progress Frame
        action_frame = ctk.CTkFrame(self, corner_radius=10)
        action_frame.pack(fill="x", padx=24, pady=10)

        btn_box = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(14, 10))

        self.btn_download = ctk.CTkButton(
            btn_box,
            text="⬇️ BẮT ĐẦU TẢI MP3",
            height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#1976D2",
            hover_color="#1565C0",
            command=self._start_download
        )
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_cancel = ctk.CTkButton(
            btn_box,
            text="⏹️ Hủy",
            width=90,
            height=46,
            fg_color="#757575",
            hover_color="#616161",
            state="disabled",
            command=self._cancel_download
        )
        self.btn_cancel.pack(side="left")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(action_frame, height=12)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=16, pady=(4, 6))

        # Status text
        self.status_label = ctk.CTkLabel(
            action_frame,
            text="Sẵn sàng thực hiện",
            font=ctk.CTkFont(size=12),
            text_color="gray80"
        )
        self.status_label.pack(anchor="w", padx=16, pady=(0, 12))

        # 5. Result Quick Actions Frame
        self.result_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E293B")
        self.result_frame.pack(fill="x", padx=24, pady=10)
        self.result_frame.pack_forget()  # Ẩn ban đầu

        res_box = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        res_box.pack(fill="x", padx=16, pady=12)

        self.res_icon_label = ctk.CTkLabel(
            res_box,
            text="✅ Hoàn tất!",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4CAF50"
        )
        self.res_icon_label.pack(anchor="w")

        self.res_file_label = ctk.CTkLabel(
            res_box,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray90",
            anchor="w",
            wraplength=640,
            justify="left"
        )
        self.res_file_label.pack(anchor="w", pady=(2, 8))

        quick_btns = ctk.CTkFrame(res_box, fg_color="transparent")
        quick_btns.pack(fill="x")

        self.btn_open_folder = ctk.CTkButton(
            quick_btns,
            text="📂 Mở thư mục chứa file",
            width=180,
            height=32,
            fg_color="#374151",
            hover_color="#4B5563",
            command=self._open_result_folder
        )
        self.btn_open_folder.pack(side="left", padx=(0, 10))

        self.btn_play_audio = ctk.CTkButton(
            quick_btns,
            text="▶️ Nghe thử file MP3",
            width=160,
            height=32,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self._play_result_audio
        )
        self.btn_play_audio.pack(side="left")

    def _check_ffmpeg(self):
        """Kiểm tra FFmpeg và cảnh báo nếu không phát hiện được"""
        ffmpeg_bin = get_ffmpeg_path()
        if not ffmpeg_bin:
            self.status_label.configure(
                text="⚠️ Chú ý: Chưa tìm thấy FFmpeg! Đang sử dụng module fallback...",
                text_color="#FFA726"
            )
        else:
            self.downloader.ffmpeg_path = ffmpeg_bin

    def _on_url_input_changed(self, event=None):
        url = self.url_entry.get().strip()
        if not url:
            self.platform_badge.configure(text="Chờ liên kết...", text_color="#64B5F6")
            return
        platform_name = MediaDownloader.identify_platform(url)
        if platform_name == "YouTube":
            self.platform_badge.configure(text="🔴 YouTube Video", text_color="#FF5252")
        elif platform_name == "Facebook":
            self.platform_badge.configure(text="🔵 Facebook Video", text_color="#42A5F5")
        elif platform_name == "TikTok":
            self.platform_badge.configure(text="⚫ TikTok Video", text_color="#00E676")
        else:
            self.platform_badge.configure(text=f"🌐 {platform_name}", text_color="#FFD54F")

    def _paste_clipboard(self):
        try:
            text = self.clipboard_get()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text.strip())
            self._on_url_input_changed()
        except Exception:
            pass

    def _clear_url(self):
        self.url_entry.delete(0, "end")
        self._on_url_input_changed()

    def _browse_directory(self):
        selected_dir = filedialog.askdirectory(initialdir=self.downloader.download_dir)
        if selected_dir:
            self.downloader.download_dir = selected_dir
            self.dir_entry.configure(state="normal")
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, selected_dir)
            self.dir_entry.configure(state="readonly")

    def _on_bitrate_changed(self, value: str):
        # Callback khi chọn bitrate
        pass

    def _get_selected_bitrate(self) -> str:
        selected = self.bitrate_seg.get()
        if "320" in selected:
            return "320"
        elif "192" in selected:
            return "192"
        return "128"

    def _toggle_clipboard_monitor(self):
        is_on = self.clipboard_switch.get() == 1
        self.clipboard_monitor.set_enabled(is_on)

    def _on_clipboard_detected(self, url: str, platform_name: str):
        """Được gọi từ ClipboardMonitor thread khi phát hiện link mới"""
        self.after(0, self._handle_detected_url, url, platform_name)

    def _handle_detected_url(self, url: str, platform_name: str):
        # Điền vào thanh nhập
        current_url = self.url_entry.get().strip()
        if current_url == url:
            return

        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        self._on_url_input_changed()

        # Nếu không đang tải thì hỏi người dùng
        if not self.is_downloading:
            confirm = messagebox.askyesno(
                title=f"Phát hiện liên kết {platform_name}",
                message=f"Đã sao chép link {platform_name}:\n{url[:80]}...\n\nBạn có muốn tải file MP3 này ngay không?",
                parent=self
            )
            if confirm:
                self._start_download()

    def _start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Thiếu liên kết", "Vui lòng nhập hoặc dán link video cần tải.", parent=self)
            return

        if not MediaDownloader.is_valid_url(url):
            proceed = messagebox.askyesno(
                "Xác nhận",
                "Link này có thể không phải định dạng thông thường của YouTube hoặc Facebook. Bạn vẫn muốn thử tải chứ?",
                parent=self
            )
            if not proceed:
                return

        self.is_downloading = True
        self.btn_download.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="Đang kết nối và lấy thông tin video...", text_color="#64B5F6")
        self.result_frame.pack_forget()

        bitrate = self._get_selected_bitrate()

        # Chạy trong thread riêng để không đơ giao diện
        thread = threading.Thread(
            target=self.downloader.download_mp3,
            kwargs={
                'url': url,
                'bitrate': bitrate,
                'progress_callback': self._on_download_progress,
                'finished_callback': self._on_download_finished,
                'error_callback': self._on_download_error,
            },
            daemon=True
        )
        thread.start()

    def _cancel_download(self):
        self.downloader.cancel()
        self.status_label.configure(text="Đang gửi yêu cầu hủy...", text_color="#FFA726")
        self.btn_cancel.configure(state="disabled")

    def _on_download_progress(self, data: dict):
        self.after(0, self._update_progress_ui, data)

    def _update_progress_ui(self, data: dict):
        status = data.get('status')
        if status == 'downloading':
            percent = data.get('percent', 0.0)
            self.progress_bar.set(percent / 100.0)

            speed = data.get('speed', 0)
            speed_str = f"{speed / (1024 * 1024):.1f} MB/s" if speed else "N/A"
            eta = data.get('eta', 0)
            eta_str = f"{int(eta)}s" if eta else "..."

            self.status_label.configure(
                text=f"Đang tải âm thanh: {percent:.1f}% | Tốc độ: {speed_str} | ETA: {eta_str}",
                text_color="#90CAF9"
            )
        elif status == 'converting':
            self.progress_bar.set(1.0)
            self.status_label.configure(
                text="⚡ Đang trích xuất sang MP3 và nhúng bìa/metadata...",
                text_color="#CE93D8"
            )

    def _on_download_finished(self, file_path: str):
        self.after(0, self._handle_download_finished, file_path)

    def _handle_download_finished(self, file_path: str):
        self.is_downloading = False
        self.btn_download.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        self.progress_bar.set(1.0)
        self.status_label.configure(text="🎉 Đã tải và chuyển đổi MP3 thành công!", text_color="#66BB6A")

        self.last_downloaded_file = file_path
        file_name = os.path.basename(file_path) if file_path else "Unknown"

        self.res_file_label.configure(text=f"Tên file: {file_name}\nĐường dẫn: {file_path}")
        self.result_frame.pack(fill="x", padx=24, pady=10)

    def _on_download_error(self, error_message: str):
        self.after(0, self._handle_download_error, error_message)

    def _handle_download_error(self, error_message: str):
        self.is_downloading = False
        self.btn_download.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text=f"❌ {error_message}", text_color="#EF5350")
        messagebox.showerror("Thông báo lỗi", error_message, parent=self)

    def _open_result_folder(self):
        if self.last_downloaded_file and os.path.exists(self.last_downloaded_file):
            open_path_in_explorer(self.last_downloaded_file)
        else:
            open_path_in_explorer(self.downloader.download_dir)

    def _play_result_audio(self):
        if self.last_downloaded_file and os.path.exists(self.last_downloaded_file):
            play_audio_file(self.last_downloaded_file)
        else:
            messagebox.showinfo("Thông báo", "Chưa tìm thấy file để phát.", parent=self)

    def _on_close(self):
        if self.is_downloading:
            confirm = messagebox.askyesno(
                "Đang tải",
                "Có tiến trình tải đang chạy. Bạn có chắc chắn muốn thoát không?",
                parent=self
            )
            if not confirm:
                return

        self.clipboard_monitor.stop()
        self.destroy()


def main():
    app = MediaToMp3App()
    app.mainloop()


if __name__ == "__main__":
    main()
