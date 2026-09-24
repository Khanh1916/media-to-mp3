import time
import threading
import re
from typing import Callable, Optional

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False


class ClipboardMonitor:
    """
    Giám sát Clipboard chạy nền để tự động phát hiện link YouTube / Facebook.
    """
    YT_PATTERN = re.compile(
        r'https?:\/\/(?:www\.|m\.)?(?:youtube\.com\/(?:watch\?v=|shorts\/|live\/|embed\/)|youtu\.be\/)[a-zA-Z0-9_\-]+[^\s]*',
        re.IGNORECASE
    )
    FB_PATTERN = re.compile(
        r'https?:\/\/(?:www\.|m\.|web\.)?(?:facebook\.com\/(?:watch\/?\?v=|reel\/|[^\/\s]+\/videos\/|share\/(?:v|r)\/)|fb\.watch\/)[a-zA-Z0-9_\-]+[^\s]*',
        re.IGNORECASE
    )

    def __init__(self, on_detected: Callable[[str, str], None], check_interval: float = 0.8):
        self.on_detected = on_detected
        self.check_interval = check_interval
        self._enabled = True
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_copied = ""

    def start(self):
        """Khởi động luồng giám sát clipboard"""
        if not HAS_PYPERCLIP or self._running:
            return
        self._running = True
        # Lấy giá trị hiện tại để không kích hoạt ngay khi vừa mở app
        try:
            self._last_copied = pyperclip.paste().strip()
        except Exception:
            self._last_copied = ""

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="ClipboardMonitorThread")
        self._thread.start()

    def stop(self):
        """Dừng luồng giám sát"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def set_enabled(self, enabled: bool):
        """Bật / Tắt chế độ tự động bắt link mà không cần hủy thread"""
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def _extract_supported_url(self, text: str):
        if not text:
            return None, None
        
        # Kiểm tra YouTube
        yt_match = self.YT_PATTERN.search(text)
        if yt_match:
            return yt_match.group(0), "YouTube"

        # Kiểm tra Facebook
        fb_match = self.FB_PATTERN.search(text)
        if fb_match:
            return fb_match.group(0), "Facebook"

        return None, None

    def _monitor_loop(self):
        while self._running:
            if self._enabled:
                try:
                    current_text = pyperclip.paste()
                    if current_text and current_text != self._last_copied:
                        self._last_copied = current_text
                        cleaned_text = current_text.strip()
                        url, platform = self._extract_supported_url(cleaned_text)
                        if url:
                            self.on_detected(url, platform)
                except Exception:
                    pass
            time.sleep(self.check_interval)
