import sys
import io

# Đảm bảo mã hóa UTF-8 trên Windows console
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
from downloader import MediaDownloader, get_ffmpeg_path


def run_cli_download(url: str, output_dir: str = None, bitrate: str = "320"):
    print(f"\n[Media to MP3] Đang tải từ: {url}")
    print(f"[Media to MP3] Chất lượng: {bitrate} kbps")
    
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        print("[Lỗi] Không tìm thấy FFmpeg trên máy tính!")
        return

    downloader = MediaDownloader(download_dir=output_dir)
    print(f"[Media to MP3] Thư mục lưu: {downloader.download_dir}")

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
            sys.stdout.write(f"\rTiến trình: [{bar}] {percent:.1f}% | {speed_mb:.2f} MB/s | ETA: {eta_str}")
            sys.stdout.flush()
        elif status == 'converting':
            print("\n⚡ Đang chuyển đổi sang định dạng MP3 chất lượng cao...")

    def finished_callback(filepath):
        print(f"\n\n Hoàn tất! File đã được lưu tại:\n  -> {filepath}\n")

    def error_callback(err):
        print(f"\n\n Lỗi: {err}\n")

    downloader.download_mp3(
        url=url,
        bitrate=bitrate,
        progress_callback=progress_callback,
        finished_callback=finished_callback,
        error_callback=error_callback
    )


def main():
    parser = argparse.ArgumentParser(description="Media to MP3 Converter (YouTube & Facebook)")
    parser.add_argument("url", nargs="?", help="Đường dẫn video YouTube hoặc Facebook (nếu muốn tải trực tiếp bằng CLI)")
    parser.add_argument("-o", "--output", help="Thư mục lưu file MP3 đầu ra")
    parser.add_argument("-b", "--bitrate", default="320", choices=["128", "192", "320"], help="Chất lượng âm thanh (128, 192, 320 kbps)")
    parser.add_argument("--cli", action="store_true", help="Chạy ở chế độ dòng lệnh (CLI)")

    args = parser.parse_args()

    # Nếu có truyền URL hoặc cờ --cli thì chạy CLI
    if args.url or args.cli:
        if not args.url:
            print("Vui lòng cung cấp link video: python main.py <URL>")
            return
        run_cli_download(args.url, output_dir=args.output, bitrate=args.bitrate)
    else:
        # Mở giao diện đồ họa (GUI)
        from app_ui import MediaToMp3App
        app = MediaToMp3App()
        app.mainloop()


if __name__ == "__main__":
    main()
