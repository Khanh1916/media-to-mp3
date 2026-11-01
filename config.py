"""
Lưu / đọc cài đặt người dùng (thư mục lưu, định dạng, ngôn ngữ...) vào file JSON:
- Windows: %APPDATA%\\MediaToMP3\\settings.json
- macOS:   ~/Library/Application Support/MediaToMP3/settings.json
- Linux:   $XDG_CONFIG_HOME/media-to-mp3/settings.json (mặc định ~/.config/...)
"""
import json
import logging
import os
import sys
from typing import Any, Dict

logger = logging.getLogger("MediaDownloader")

DEFAULTS: Dict[str, Any] = {
    "download_dir": "",
    "format": "mp3",
    "bitrate": "320",
    "embed_thumbnail": True,
    "parse_metadata": True,
    "clipboard_monitor": True,
    "language": "vi",
    "window_geometry": "",
}


def config_dir() -> str:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "MediaToMP3")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/MediaToMP3")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "media-to-mp3")


def config_path() -> str:
    return os.path.join(config_dir(), "settings.json")


def load_settings(path: str = None) -> Dict[str, Any]:
    """Đọc cài đặt, bỏ qua giá trị sai kiểu và bổ sung mặc định cho khóa còn thiếu."""
    path = path or config_path()
    settings = dict(DEFAULTS)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return settings
    except (OSError, ValueError) as e:
        logger.warning(f"Không đọc được file cài đặt {path}: {e}")
        return settings

    if isinstance(data, dict):
        for key, default in DEFAULTS.items():
            if key in data and isinstance(data[key], type(default)):
                settings[key] = data[key]
    return settings


def save_settings(settings: Dict[str, Any], path: str = None):
    """Ghi cài đặt qua file tạm rồi thay thế, tránh hỏng file nếu app bị tắt giữa chừng."""
    path = path or config_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump({k: settings.get(k, v) for k, v in DEFAULTS.items()}, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except OSError as e:
        logger.warning(f"Không lưu được cài đặt vào {path}: {e}")
