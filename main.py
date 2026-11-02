import sys
import io

# Bản .exe là ứng dụng cửa sổ, không có console: khi chạy từ cmd / PowerShell kèm tham số
# (vd. --check, --help) thì gắn vào console đang mở để in được kết quả
if sys.platform.startswith("win") and getattr(sys, "frozen", False) and sys.stdout is None and len(sys.argv) > 1:
    import ctypes
    if ctypes.windll.kernel32.AttachConsole(-1):
        sys.stdout = sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")

# Bản đóng gói trên Linux: PyInstaller trỏ LD_LIBRARY_PATH vào thư viện đóng gói kèm. Trả lại giá trị gốc
# để các chương trình hệ thống app gọi (xclip, paplay, xdg-open...) không nạp nhầm thư viện
if sys.platform.startswith("linux") and getattr(sys, "frozen", False):
    import os
    _original = os.environ.pop("LD_LIBRARY_PATH_ORIG", None)
    if _original is not None:
        os.environ["LD_LIBRARY_PATH"] = _original
    else:
        os.environ.pop("LD_LIBRARY_PATH", None)

# Đảm bảo mã hóa UTF-8 trên Windows console
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import logging

import config
from downloader import AUDIO_FORMATS, MediaDownloader, get_ffmpeg_path
from i18n import LANGUAGES, set_language, t
from version import __version__


def run_cli_download(url: str, output_dir: str = None, fmt: str = "mp3", bitrate: str = "320",
                     embed_thumbnail: bool = True, parse_metadata: bool = True) -> bool:
    print("\n" + t("cli_downloading", url=url))
    label = AUDIO_FORMATS[fmt]["label"] + (f" {bitrate} kbps" if AUDIO_FORMATS[fmt]["bitrates"] else "")
    print(t("cli_format", fmt=label))

    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        print(t("cli_no_ffmpeg"))
        return False

    downloader = MediaDownloader(download_dir=output_dir)
    print(t("cli_save_dir", dir=downloader.download_dir))

    def progress_callback(d):
        status = d.get('status')
        if status == 'downloading':
            percent = d.get('percent', 0.0) or 0.0
            speed = d.get('speed') or 0
            speed_mb = speed / (1024 * 1024) if speed else 0
            eta = d.get('eta') or 0
            eta_str = f"{int(eta)}s" if eta else "..."
            bar_len = 30
            filled = int(bar_len * (percent / 100))
            bar = '█' * filled + '-' * (bar_len - filled)
            sys.stdout.write(f"\r{t('cli_progress')}: [{bar}] {percent:.1f}% | {speed_mb:.2f} MB/s | ETA: {eta_str}")
            sys.stdout.flush()
        elif status == 'converting':
            print("\n" + t("cli_converting"))

    def finished_callback(filepath):
        print("\n\n " + t("cli_done", path=filepath) + "\n")

    def error_callback(err):
        print(f"\n\n {err}\n")

    return downloader.download_audio(
        url=url,
        fmt=fmt,
        bitrate=bitrate,
        embed_thumbnail=embed_thumbnail,
        parse_metadata=parse_metadata,
        progress_callback=progress_callback,
        finished_callback=finished_callback,
        error_callback=error_callback
    ) is not None


def main():
    # Hiện cảnh báo của yt-dlp ra terminal (thiếu JS runtime, retry do mạng...)
    logging.basicConfig(level=logging.WARNING, format="\n[%(levelname)s] %(message)s")

    # Đọc --lang trước để phần trợ giúp (--help) hiển thị đúng ngôn ngữ
    settings = config.load_settings()
    pre = argparse.ArgumentParser(add_help=False)
    lang_option = pre.add_argument("--lang", choices=list(LANGUAGES), default=settings["language"])
    set_language(pre.parse_known_args()[0].lang)
    lang_option.help = t("cli_help_lang")

    parser = argparse.ArgumentParser(description=t("cli_desc"), parents=[pre])
    parser.add_argument("--version", action="version", version=f"Media to MP3 {__version__}")
    parser.add_argument("--check", action="store_true", help=t("cli_help_check"))
    parser.add_argument("urls", nargs="*", metavar="URL", help=t("cli_help_url"))
    parser.add_argument("-o", "--output", help=t("cli_help_output"))
    parser.add_argument("-f", "--format", default="mp3", choices=list(AUDIO_FORMATS), help=t("cli_help_format"))
    parser.add_argument("-b", "--bitrate", default="320", choices=["128", "192", "320"], help=t("cli_help_bitrate"))
    parser.add_argument("--no-thumbnail", action="store_true", help=t("cli_help_no_thumb"))
    parser.add_argument("--no-tags", action="store_true", help=t("cli_help_no_tags"))
    parser.add_argument("--cli", action="store_true", help=t("cli_help_cli"))

    args = parser.parse_args()

    if args.check:
        from selftest import run_selftest
        sys.exit(0 if run_selftest() else 1)

    # Nếu có truyền URL hoặc cờ --cli thì chạy CLI
    if args.urls or args.cli:
        if not args.urls:
            print(t("cli_need_url"))
            return
        done = sum(
            run_cli_download(url, output_dir=args.output, fmt=args.format, bitrate=args.bitrate,
                             embed_thumbnail=not args.no_thumbnail, parse_metadata=not args.no_tags)
            for url in args.urls
        )
        if len(args.urls) > 1:
            print(t("cli_summary", done=done, total=len(args.urls)))
        if done < len(args.urls):
            sys.exit(1)
    else:
        # Mở giao diện đồ họa (GUI)
        from app_ui import MediaToMp3App
        app = MediaToMp3App()
        app.mainloop()


if __name__ == "__main__":
    main()
