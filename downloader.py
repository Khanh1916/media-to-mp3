import os
import re
import shutil
import logging
from typing import Callable, Optional, Dict, Any, Tuple

from i18n import t

try:
    import imageio_ffmpeg
    HAS_IMAGEIO_FFMPEG = True
except ImportError:
    HAS_IMAGEIO_FFMPEG = False

try:
    import yt_dlp
    from yt_dlp.postprocessor.common import PostProcessor
    HAS_YTDL = True
except ImportError:
    HAS_YTDL = False
    PostProcessor = object

logger = logging.getLogger("MediaDownloader")

# yt-dlp chỉ tự bật deno; bật thêm node/bun/quickjs để dùng runtime nào có sẵn trên máy.
# Thiếu JS runtime thì YouTube có thể thiếu định dạng, bị bóp tốc độ hoặc lỗi 403.
JS_RUNTIMES = {'deno': {}, 'node': {}, 'bun': {}, 'quickjs': {}}

# Các định dạng đầu ra. Chỉ giữ loại mà loa, đài, đầu xe hơi và điện thoại phổ biến đọc được
# (bỏ Opus/OGG vì nhiều thiết bị phần cứng không hỗ trợ). 44.1 kHz / 16-bit là chuẩn CD,
# thiết bị cũ nào cũng phát được.
AUDIO_FORMATS: Dict[str, Dict[str, Any]] = {
    'mp3': {
        'label': 'MP3',
        'format': 'bestaudio/best',
        'bitrates': ['320', '192', '128'],
        'extract_args': ['-ar', '44100'],
        'thumbnail': True,
    },
    'm4a': {
        'label': 'M4A (AAC)',
        # Ưu tiên luồng AAC gốc để chỉ đóng gói lại, không nén thêm lần nữa
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'bitrates': None,
        'quality': '192',  # chỉ dùng khi nguồn không phải AAC và phải mã hóa lại
        'extract_args': [],
        'thumbnail': True,
    },
    'wav': {
        'label': 'WAV',
        'format': 'bestaudio/best',
        'bitrates': None,
        'extract_args': ['-ar', '44100'],
        'thumbnail': False,  # WAV không có chỗ chứa ảnh bìa
    },
    'flac': {
        'label': 'FLAC',
        'format': 'bestaudio/best',
        'bitrates': None,
        'extract_args': ['-ar', '44100', '-sample_fmt', 's16'],
        'thumbnail': True,
    },
}

# Từ "rác" thường gặp trong tiêu đề video nhạc: (Official Video), [Lyrics], | OFFICIAL MV...
_NOISE_WORDS = re.compile(
    r"official|officiel|music|musical|video|audio|lyrics?|visuali[sz]er|m/?v|clip|"
    r"remaster(?:ed)?|4k|8k|uhd|hd|hq|\d{3,4}p|full|vietsub|engsub|"
    r"lời bài hát|loi bai hat",
    re.IGNORECASE,
)
_BRACKETS = re.compile(r"\s*[\(\[\{【]([^\(\)\[\]\{\}【】]*)[\)\]\}】]")
_PIPE_SEP = re.compile(r"\s+[|｜]\s+")
_DASH_SEP = re.compile(r"\s+[-–—~]\s+")


def _is_noise(text: str) -> bool:
    """True nếu đoạn text chỉ gồm các từ rác (vd. 'Official Music Video', '4K Remaster')."""
    if not _NOISE_WORDS.search(text):
        return False
    return not re.sub(r"[\W\d_]+", "", _NOISE_WORDS.sub(" ", text))


def _clean_uploader(uploader: Optional[str]) -> str:
    name = (uploader or "").strip()
    name = re.sub(r"\s+-\s+Topic$", "", name)
    name = re.sub(r"VEVO$", "", name).strip()
    name = re.sub(r"\s+Official(?:\s+Channel)?$", "", name, flags=re.IGNORECASE)
    return name.strip()


def parse_artist_title(title: str, uploader: Optional[str] = None) -> Tuple[str, str]:
    """
    Tách (ca sĩ, tên bài) từ tiêu đề video, bỏ các phần như (Official Video), | OFFICIAL MV.
    Không tìm thấy dấu phân cách thì lấy tên kênh làm ca sĩ.
    """
    text = _BRACKETS.sub(lambda m: "" if _is_noise(m.group(1)) else m.group(0), title or "").strip()

    parts = [p.strip() for p in _PIPE_SEP.split(text) if p.strip() and not _is_noise(p)]
    if len(parts) >= 2:
        artist, track = parts[0], parts[1]
    else:
        text = parts[0] if parts else text
        pieces = _DASH_SEP.split(text, maxsplit=1)
        if len(pieces) == 2 and all(p.strip() for p in pieces):
            artist, track = pieces
        else:
            artist, track = _clean_uploader(uploader), text

    track = track.strip(" -–—|") or (title or "").strip()
    return artist.strip(), track


class _ArtistTitlePP(PostProcessor):
    """Điền tag ca sĩ / tên bài từ tiêu đề khi trang nguồn không cung cấp sẵn."""
    def run(self, info):
        if not (info.get('track') or info.get('artist') or info.get('artists')):
            artist, track = parse_artist_title(info.get('title') or '', info.get('uploader') or info.get('channel'))
            # Ghi vào 'track' thay vì 'title' để tên file vẫn giữ nguyên tiêu đề đầy đủ
            info['track'] = track
            if artist:
                info['artist'] = artist
        return [], info


class _YtdlLogger:
    """Đưa cảnh báo của yt-dlp (thiếu JS runtime, retry, timeout...) ra logging thay vì nuốt mất."""
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        logger.warning(msg)

    def error(self, msg):
        # Lỗi đã được trả về qua exception -> error_callback, tránh in trùng
        logger.debug(msg)


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


def default_download_dir() -> str:
    """Mặc định lưu vào thư mục Music của người dùng, không có thì Downloads"""
    user_music = os.path.join(os.path.expanduser("~"), "Music")
    if not os.path.exists(user_music):
        user_music = os.path.join(os.path.expanduser("~"), "Downloads")
    return user_music


class MediaDownloader:
    """
    Quản lý việc tải và chuyển đổi video từ YouTube / Facebook sang file nhạc (MP3, M4A, WAV, FLAC).
    """
    def __init__(self, download_dir: Optional[str] = None):
        self.download_dir = download_dir or default_download_dir()
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
            raise RuntimeError(t("err_no_ytdlp"))

        ydl_opts = {
            'logger': _YtdlLogger(),
            'js_runtimes': JS_RUNTIMES,
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

    def download_audio(
        self,
        url: str,
        fmt: str = "mp3",
        bitrate: str = "320",
        output_dir: Optional[str] = None,
        embed_thumbnail: bool = True,
        parse_metadata: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        finished_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Tải video và chuyển sang định dạng âm thanh `fmt` (mp3, m4a, wav, flac).
        `bitrate` (128, 192, 320) chỉ áp dụng cho MP3. Trả về đường dẫn file hoặc None nếu lỗi.
        """
        if not HAS_YTDL:
            if error_callback:
                error_callback(t("err_no_ytdlp"))
            return None

        ffmpeg_bin = self.ffmpeg_path or get_ffmpeg_path()
        if not ffmpeg_bin:
            if error_callback:
                error_callback(t("err_no_ffmpeg"))
            return None

        spec = AUDIO_FORMATS.get(fmt, AUDIO_FORMATS['mp3'])
        out_dir = output_dir or self.download_dir
        self.is_cancelled = False
        os.makedirs(out_dir, exist_ok=True)

        def ytdl_hook(d):
            if self.is_cancelled:
                raise yt_dlp.utils.DownloadCancelled(t("err_cancelled"))

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
                        'filename': d.get('filename', ''),
                        'title': (d.get('info_dict') or {}).get('title', ''),
                    })

            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback({'status': 'converting', 'percent': 100.0})

        def pp_hook(d):
            if self.is_cancelled:
                raise yt_dlp.utils.DownloadCancelled(t("err_cancelled"))

        thumbnail = embed_thumbnail and spec['thumbnail']
        postprocessors = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': fmt if fmt in AUDIO_FORMATS else 'mp3',
                'preferredquality': str(bitrate) if spec['bitrates'] else spec.get('quality'),
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
        ]
        postprocessor_args = {'extractaudio+ffmpeg_o': list(spec['extract_args'])}
        if fmt == 'mp3':
            # ID3v2.3 + ID3v1: đầu xe hơi / đài cũ thường không đọc được ID3v2.4 (mặc định của ffmpeg)
            postprocessor_args['metadata+ffmpeg_o'] = ['-id3v2_version', '3', '-write_id3v1', '1']
        if thumbnail:
            # Ảnh bìa JPEG vuông 600x600: thiết bị nào cũng hiển thị được, dung lượng nhỏ
            postprocessors.insert(0, {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
            postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
            postprocessor_args['thumbnailsconvertor+ffmpeg_o'] = [
                '-c:v', 'mjpeg', '-q:v', '3', '-vf', "crop='min(iw,ih)':'min(iw,ih)',scale=600:600",
            ]

        # Template tên file an toàn cho cả Windows và Linux
        out_template = os.path.join(out_dir, '%(title).150B [%(id)s].%(ext)s')

        ydl_opts = {
            'format': spec['format'],
            'outtmpl': out_template,
            'ffmpeg_location': ffmpeg_bin,
            'postprocessors': postprocessors,
            'postprocessor_args': postprocessor_args,
            'progress_hooks': [ytdl_hook],
            'postprocessor_hooks': [pp_hook],
            'writethumbnail': thumbnail,
            'noplaylist': True,
            'logger': _YtdlLogger(),
            'js_runtimes': JS_RUNTIMES,
            # App tự vẽ tiến trình, không để yt-dlp in thêm dòng [download] lẫn vào
            'noprogress': True,
            # User agent chuẩn để tránh bị chặn
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if parse_metadata:
                    ydl.add_post_processor(_ArtistTitlePP(ydl), when='pre_process')
                info = ydl.extract_info(url, download=True)
                final_file = self._find_output_file(info, out_dir)

            if finished_callback:
                finished_callback(final_file)
            return final_file

        except yt_dlp.utils.DownloadCancelled:
            if error_callback:
                error_callback(t("err_cancelled"))
        except Exception as e:
            err_msg = str(e)
            if "Private video" in err_msg or "Sign in" in err_msg:
                err_msg = t("err_private")
            elif "Video unavailable" in err_msg:
                err_msg = t("err_unavailable")
            if error_callback:
                error_callback(t("err_prefix", msg=err_msg))
        return None

    @staticmethod
    def _find_output_file(info: Dict[str, Any], out_dir: str) -> str:
        """Lấy đường dẫn file cuối cùng sau khi yt-dlp đã chuyển đổi xong"""
        for download in reversed(info.get('requested_downloads') or []):
            path = download.get('filepath')
            if path and os.path.exists(path):
                return path

        # Dự phòng: tìm file chứa id video trong thư mục lưu
        file_id = info.get('id', '')
        audio_exts = tuple(f'.{ext}' for ext in AUDIO_FORMATS)
        for f in os.listdir(out_dir):
            if f.endswith(audio_exts) and file_id and f"[{file_id}]" in f:
                return os.path.join(out_dir, f)
        return os.path.join(out_dir, f"{info.get('title', 'Audio')} [{file_id}]")

    def cancel(self):
        """Hủy tiến trình đang chạy"""
        self.is_cancelled = True
