"""
Công cụ chỉnh sửa âm thanh bằng FFmpeg: đọc thông tin file, vẽ dạng sóng,
cắt / ghép nhiều đoạn (kèm fade, crossfade, chỉnh âm lượng) và nghe thử.
"""
import array
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

from downloader import get_ffmpeg_path

# Không bật cửa sổ console đen mỗi lần gọi ffmpeg trong bản .exe (--windowed)
_POPEN_FLAGS = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform.startswith("win") else {}

# Định dạng xuất: lệnh mã hóa cho ffmpeg và loại nào chứa được ảnh bìa
EXPORT_CODECS = {
    "mp3": ["-c:a", "libmp3lame"],
    "m4a": ["-c:a", "aac"],
    "wav": ["-c:a", "pcm_s16le"],
    "flac": ["-c:a", "flac", "-sample_fmt", "s16"],
}
COVER_FORMATS = ("mp3", "m4a", "flac")
SAMPLE_RATE = 44100


class AudioToolError(Exception):
    pass


@dataclass
class AudioInfo:
    duration: float
    title: str = ""
    artist: str = ""
    has_cover: bool = False


@dataclass
class ClipSpec:
    path: str
    start: float
    end: float

    @property
    def length(self) -> float:
        return max(0.0, self.end - self.start)


# ---------- Thời gian ----------
def format_time(seconds: float, precise: bool = True) -> str:
    """83.25 -> '1:23.2' ; 3723 -> '1:02:03.0'"""
    seconds = max(0.0, float(seconds or 0))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    sec_str = f"{secs:04.1f}" if precise else f"{int(secs):02d}"
    if hours >= 1:
        return f"{int(hours)}:{int(minutes):02d}:{sec_str}"
    return f"{int(minutes)}:{sec_str}"


def parse_time(text: str) -> float:
    """Đọc '1:23.5', '83.5', '1:02:03' hoặc '1,5' thành số giây. Sai định dạng -> ValueError."""
    text = (text or "").strip().replace(",", ".")
    if not text:
        raise ValueError("empty time")
    parts = text.split(":")
    if len(parts) > 3:
        raise ValueError(text)
    total = 0.0
    for part in parts:
        value = float(part)
        if value < 0:
            raise ValueError(text)
        total = total * 60 + value
    return total


# ---------- FFmpeg ----------
def _ffmpeg() -> str:
    path = get_ffmpeg_path()
    if not path:
        raise AudioToolError("FFmpeg not found")
    return path


def probe(path: str) -> AudioInfo:
    """Đọc độ dài, tag tên bài / ca sĩ và ảnh bìa bằng `ffmpeg -i` (imageio-ffmpeg không kèm ffprobe)."""
    proc = subprocess.run(
        [_ffmpeg(), "-hide_banner", "-i", path], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding="utf-8", errors="replace", **_POPEN_FLAGS,
    )
    out = proc.stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", out)
    if not m or "Audio:" not in out:
        raise AudioToolError(out.strip().splitlines()[-1] if out.strip() else "unreadable file")
    duration = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

    # Chỉ đọc tag của file (khối Metadata đầu tiên, trước dòng Stream)
    header = out.split("Stream #", 1)[0]
    tags = dict(
        (k.lower(), v.strip())
        for k, v in re.findall(r"^\s{4}(\w+)\s*:\s?(.*)$", header, re.MULTILINE)
    )
    return AudioInfo(
        duration=duration,
        title=tags.get("title", ""),
        artist=tags.get("artist", ""),
        has_cover="(attached pic)" in out,
    )


def load_peaks(path: str, duration: float, buckets: int = 1600) -> List[float]:
    """Giải mã sang PCM mono tần số thấp và lấy biên độ đỉnh (0..1) của mỗi khoảng để vẽ dạng sóng."""
    rate = int(min(8000, max(400, 2_000_000 / max(duration, 1))))
    proc = subprocess.run(
        [_ffmpeg(), "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"],
        stdin=subprocess.DEVNULL, capture_output=True, **_POPEN_FLAGS,
    )
    samples = array.array("h")
    samples.frombytes(proc.stdout[: len(proc.stdout) // 2 * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    if not samples:
        return [0.0] * buckets

    step = max(1, len(samples) // buckets)
    peaks = []
    for i in range(0, len(samples), step):
        chunk = samples[i:i + step]
        peaks.append(max(max(chunk), -min(chunk)) / 32768.0)
    top = max(peaks) or 1.0
    return [p / top for p in peaks]


def output_duration(clips: Sequence[ClipSpec], crossfade: float) -> float:
    total = sum(c.length for c in clips)
    return max(0.0, total - effective_crossfade(clips, crossfade) * (len(clips) - 1))


def effective_crossfade(clips: Sequence[ClipSpec], crossfade: float) -> float:
    """Crossfade phải ngắn hơn mọi đoạn, nếu không acrossfade sẽ lỗi."""
    if len(clips) < 2 or crossfade <= 0:
        return 0.0
    return max(0.0, min(crossfade, min(c.length for c in clips) / 2 - 0.05))


def build_export_command(
    clips: Sequence[ClipSpec],
    out_path: str,
    fmt: str = "mp3",
    bitrate: str = "320",
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    gain_db: float = 0.0,
    crossfade: float = 0.0,
    normalize: bool = False,
    title: str = "",
    artist: str = "",
    keep_cover: bool = False,
) -> List[str]:
    """Tạo lệnh ffmpeg để cắt từng đoạn, ghép lại theo thứ tự và áp hiệu ứng."""
    if not clips:
        raise AudioToolError("no clips")
    if fmt not in EXPORT_CODECS:
        raise AudioToolError(f"unsupported format {fmt}")

    cmd = [_ffmpeg(), "-hide_banner", "-y"]
    for clip in clips:
        cmd += ["-ss", f"{clip.start:.3f}", "-t", f"{clip.length:.3f}", "-i", clip.path]

    # Đưa mọi đoạn về cùng tần số mẫu / số kênh thì concat, acrossfade mới ghép được.
    # Chia lại khung 1024 mẫu: acrossfade ra file rỗng khi đoạn sau có khung lớn (FLAC: 4608 mẫu).
    filters = [
        f"[{i}:a:0]aresample={SAMPLE_RATE},aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"asetnsamples=n=1024:p=0[c{i}]"
        for i in range(len(clips))
    ]
    xf = effective_crossfade(clips, crossfade)
    if len(clips) == 1:
        joined = "c0"
    elif xf > 0:
        prev = "c0"
        for i in range(1, len(clips)):
            filters.append(f"[{prev}][c{i}]acrossfade=d={xf:.3f}:c1=tri:c2=tri[x{i}]")
            prev = f"x{i}"
        joined = prev
    else:
        filters.append("".join(f"[c{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1[j]")
        joined = "j"

    total = output_duration(clips, crossfade)
    effects = []
    if fade_in > 0:
        effects.append(f"afade=t=in:st=0:d={min(fade_in, total):.3f}")
    if fade_out > 0:
        fo = min(fade_out, total)
        effects.append(f"afade=t=out:st={max(0.0, total - fo):.3f}:d={fo:.3f}")
    if gain_db:
        effects.append(f"volume={gain_db:+.1f}dB")
    if normalize:
        effects.append("loudnorm=I=-14:TP=-1.5:LRA=11")
    # loudnorm đẩy tần số mẫu lên 192 kHz nên luôn đưa về 44.1 kHz ở cuối
    effects.append(f"aresample={SAMPLE_RATE}")
    filters.append(f"[{joined}]" + ",".join(effects) + "[out]")

    cmd += ["-filter_complex", ";".join(filters), "-map", "[out]"]
    if keep_cover and fmt in COVER_FORMATS:
        # Giữ ảnh bìa của đoạn đầu tiên, đánh dấu là "Cover (front)" để đầu đọc nhận đúng ảnh bìa
        cmd += ["-map", "0:v:0?", "-c:v", "copy", "-disposition:v:0", "attached_pic",
                "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (front)"]
    cmd += EXPORT_CODECS[fmt]
    if fmt == "mp3":
        cmd += ["-b:a", f"{bitrate}k", "-id3v2_version", "3", "-write_id3v1", "1"]
    elif fmt == "m4a":
        cmd += ["-b:a", "256k"]
    cmd += ["-ar", str(SAMPLE_RATE), "-map_metadata", "-1", "-map_chapters", "-1"]
    if title:
        cmd += ["-metadata", f"title={title}"]
    if artist:
        cmd += ["-metadata", f"artist={artist}"]
    cmd += ["-progress", "pipe:1", "-nostats", out_path]
    return cmd


def run_export(
    cmd: List[str],
    total_seconds: float,
    progress_callback: Optional[Callable[[float], None]] = None,
    cancel_event: Optional[threading.Event] = None,
):
    """Chạy lệnh xuất, báo % tiến trình từ `-progress pipe:1`. Lỗi hoặc bị hủy -> AudioToolError."""
    out_path = cmd[-1]
    inputs = [cmd[i + 1] for i, arg in enumerate(cmd) if arg == "-i"]
    if any(os.path.exists(p) and os.path.exists(out_path) and os.path.samefile(p, out_path) for p in inputs):
        raise AudioToolError("output file must be different from input files")

    with tempfile.TemporaryFile() as err_file:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=err_file, stdin=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="replace", **_POPEN_FLAGS,
        )
        for line in proc.stdout:
            if cancel_event is not None and cancel_event.is_set():
                proc.kill()
                break
            m = re.match(r"out_time=(\d+):(\d+):(\d+(?:\.\d+)?)", line)
            if m and progress_callback and total_seconds > 0:
                done = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
                progress_callback(min(1.0, done / total_seconds))
        proc.wait()

        if cancel_event is not None and cancel_event.is_set():
            _silent_remove(out_path)
            raise AudioToolError("cancelled")
        if proc.returncode != 0:
            err_file.seek(0)
            lines = err_file.read().decode("utf-8", "replace").strip().splitlines()
            _silent_remove(out_path)
            raise AudioToolError(lines[-1] if lines else f"ffmpeg exit code {proc.returncode}")
    if progress_callback:
        progress_callback(1.0)


def render_preview(clip: ClipSpec, out_wav: str):
    """Xuất nhanh đoạn đang chọn ra WAV để nghe thử."""
    proc = subprocess.run(
        [_ffmpeg(), "-v", "error", "-y", "-ss", f"{clip.start:.3f}", "-t", f"{clip.length:.3f}",
         "-i", clip.path, "-vn", "-ac", "2", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", out_wav],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace",
        **_POPEN_FLAGS,
    )
    if proc.returncode != 0:
        raise AudioToolError(proc.stderr.strip() or "preview failed")


def _silent_remove(path: str):
    try:
        os.remove(path)
    except OSError:
        pass


# ---------- Nghe thử ----------
class AudioPlayer:
    """Phát file WAV ngay trong app và dừng được (Windows: winsound, Linux/macOS: trình phát dòng lệnh)."""
    LINUX_PLAYERS = (["paplay"], ["pw-play"], ["aplay", "-q"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"])

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._started = 0.0
        self._length = 0.0

    @classmethod
    def available(cls) -> bool:
        if sys.platform.startswith("win"):
            return True
        if sys.platform == "darwin":
            return shutil.which("afplay") is not None
        return any(shutil.which(p[0]) for p in cls.LINUX_PLAYERS)

    def play(self, wav_path: str, length: float):
        self.stop()
        if sys.platform.startswith("win"):
            import winsound
            winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        else:
            if sys.platform == "darwin":
                args = ["afplay"]
            else:
                args = next((p for p in self.LINUX_PLAYERS if shutil.which(p[0])), None)
                if args is None:
                    raise AudioToolError("no audio player found")
            self._proc = subprocess.Popen(
                [*args, wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **_POPEN_FLAGS
            )
        self._started = time.monotonic()
        self._length = length

    def position(self) -> Optional[float]:
        """Số giây đã phát, hoặc None nếu đã dừng / phát xong."""
        if not self._started:
            return None
        elapsed = time.monotonic() - self._started
        finished = elapsed >= self._length
        if self._proc is not None:
            finished = self._proc.poll() is not None
        if finished:
            self._started = 0.0
            return None
        return elapsed

    def stop(self):
        if sys.platform.startswith("win"):
            import winsound
            winsound.PlaySound(None, 0)
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None
        self._started = 0.0
