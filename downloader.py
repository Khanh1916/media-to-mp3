import os
import re
import shutil
import logging
from typing import Callable, Optional, Dict, Any

try:
    import imageio_ffmpeg
    HAS_IMAGEIO_FFMPEG = True
except ImportError:
    HAS_IMAGEIO_FFMPEG = False

try:
    import yt_dlp
    HAS_YTDL = True
except ImportError:
    HAS_YTDL = False

logger = logging.getLogger("MediaDownloader")

def get_ffmpeg_path() -> Optional[str]:
    """
    Tìm đường dẫn FFmpeg:
    1. Kiểm tra FFmpeg có sẵn trong biến môi trường PATH hệ thống (Windows / Linux).
    2. Nếu không có, tìm bản binary tích hợp từ imageio-ffmpeg.
    3. Trả về đường dẫn executable hoặc None.
    """
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    if HAS_IMAGEIO_FFMPEG:
        try:
            bundled_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            if bundled_ffmpeg and os.path.exists(bundled_ffmpeg):
                return bundled_ffmpeg
        except Exception as e:
            logger.warning(f"Không thể lấy FFmpeg từ imageio-ffmpeg: {e}")

    # Kiểm tra thư mục cục bộ ./bin/ hoặc ./ffmpeg
    for local_name in ["ffmpeg", "ffmpeg.exe", "bin/ffmpeg", "bin/ffmpeg.exe"]:
        if os.path.exists(local_name):
            return os.path.abspath(local_name)

    return None


class MediaDownloader:
    """
    Quản lý việc tải và chuyển đổi video từ YouTube / Facebook sang định dạng MP3.
    """
    def __init__(self, download_dir: Optional[str] = None):
        if not download_dir:
            # Mặc định lưu vào thư mục Music của người dùng
            user_music = os.path.join(os.path.expanduser("~"), "Music")
            if not os.path.exists(user_music):
                user_music = os.path.join(os.path.expanduser("~"), "Downloads")
            self.download_dir = user_music
        else:
            self.download_dir = download_dir

        self.ffmpeg_path = get_ffmpeg_path()
        self.is_cancelled = False

    @staticmethod
    def identify_platform(url: str) -> str:
        """Nhận diện nền tảng từ URL"""
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "YouTube"
        elif "facebook.com" in url_lower or "fb.watch" in url_lower:
            return "Facebook"
        elif "tiktok.com" in url_lower:
            return "TikTok"
        elif "soundcloud.com" in url_lower:
            return "SoundCloud"
        return "Video Link"

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Kiểm tra xem URL có đúng định dạng hỗ trợ không"""
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        pattern = re.compile(
            r'^(https?:\/\/)?(www\.|m\.|web\.)?'
            r'(youtube\.com|youtu\.be|facebook\.com|fb\.watch|tiktok\.com|soundcloud\.com)'
            r'\/[^\s]+$',
            re.IGNORECASE
        )
        return bool(pattern.match(url))

    def extract_info(self, url: str) -> Dict[str, Any]:
        """Lấy thông tin cơ bản của video mà không tải dữ liệu"""
        if not HAS_YTDL:
            raise RuntimeError("yt-dlp chưa được cài đặt.")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'uploader': info.get('uploader') or info.get('channel', 'Unknown Artist'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail'),
                'platform': self.identify_platform(url)
            }

    def download_mp3(
        self,
        url: str,
        bitrate: str = "320",
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        finished_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Tải video và chuyển đổi sang MP3 với bitrate được chọn (128, 192, 320).
        """
        if not HAS_YTDL:
            if error_callback:
                error_callback("Lỗi: yt-dlp chưa được cài đặt!")
            return

        ffmpeg_bin = self.ffmpeg_path or get_ffmpeg_path()
        if not ffmpeg_bin:
            if error_callback:
                error_callback("Lỗi: Không tìm thấy FFmpeg để chuyển đổi sang MP3!")
            return

        self.is_cancelled = False
        os.makedirs(self.download_dir, exist_ok=True)

        def ytdl_hook(d):
            if self.is_cancelled:
                raise yt_dlp.utils.DownloadCancelled("Người dùng đã hủy tiến trình.")

            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded_bytes = d.get('downloaded_bytes') or 0
                speed = d.get('speed') or 0
                eta = d.get('eta') or 0

                percent = 0.0
                if total_bytes > 0:
                    percent = (downloaded_bytes / total_bytes) * 100.0
                elif '_percent_str' in d:
                    try:
                        clean_str = re.sub(r'\x1b\[[0-9;]*[mGKF]', '', d['_percent_str']).replace('%', '').strip()
                        percent = float(clean_str)
                    except Exception:
                        percent = 0.0

                if progress_callback:
                    progress_callback({
                        'status': 'downloading',
                        'percent': percent,
                        'speed': speed,
                        'eta': eta,
                        'downloaded_bytes': downloaded_bytes,
                        'total_bytes': total_bytes,
                        'filename': d.get('filename', '')
                    })

            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback({
                        'status': 'converting',
                        'percent': 100.0,
                        'message': 'Đang chuyển đổi sang định dạng MP3 và gắn thẻ nhạc...'
                    })

        postprocessors = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(bitrate),
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }
        ]

        # Template tên file an toàn cho cả Windows và Linux
        out_template = os.path.join(self.download_dir, '%(title).150B [%(id)s].%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_template,
            'ffmpeg_location': ffmpeg_bin,
            'postprocessors': postprocessors,
            'progress_hooks': [ytdl_hook],
            'writethumbnail': False,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            # User agent chuẩn để tránh bị chặn
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Audio')
                file_id = info.get('id', '')
                expected_filename = os.path.join(self.download_dir, f"{title[:150]} [{file_id}].mp3")
                
                # Tìm file thực tế được tạo nếu tên có ký tự đặc biệt được sanitize
                final_file = expected_filename
                if not os.path.exists(final_file):
                    # Thử tìm file mp3 có chứa file_id trong download_dir
                    for f in os.listdir(self.download_dir):
                        if f.endswith('.mp3') and file_id in f:
                            final_file = os.path.join(self.download_dir, f)
                            break

                if finished_callback:
                    finished_callback(final_file)

        except yt_dlp.utils.DownloadCancelled:
            if error_callback:
                error_callback("Đã hủy tải xuống.")
        except Exception as e:
            err_msg = str(e)
            if "Private video" in err_msg or "Sign in" in err_msg:
                err_msg = "Video yêu cầu đăng nhập hoặc ở chế độ riêng tư (Cần cookies)."
            elif "Video unavailable" in err_msg:
                err_msg = "Video không tồn tại hoặc đã bị xóa."
            if error_callback:
                error_callback(f"Lỗi: {err_msg}")

    def cancel(self):
        """Hủy tiến trình đang chạy"""
        self.is_cancelled = True
