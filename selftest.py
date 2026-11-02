"""
Tự kiểm tra bản cài đặt: `python main.py --check` hoặc `MediaToMP3 --check`.
Kiểm tra FFmpeg có đủ bộ mã hóa / bộ lọc app cần bằng cách tự tạo âm thanh rồi
mã hóa, nhúng ảnh bìa, cắt ghép thử. Không cần mạng.
"""
import array
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Callable

import audio_tools as at
from downloader import AUDIO_FORMATS, get_ffmpeg_path
from version import __version__

RATE = 44100
TONE_SECONDS = 3.0


def _tone_pcm(seconds: float, freq: float) -> bytes:
    """Sóng sine stereo, PCM 16-bit little-endian"""
    samples = array.array("h")
    for i in range(int(seconds * RATE)):
        value = int(12000 * math.sin(2 * math.pi * freq * i / RATE))
        samples.extend((value, value))
    if sys.byteorder == "big":
        samples.byteswap()
    return samples.tobytes()


def run_selftest(out: Callable[[str], None] = print) -> bool:
    results = []

    def check(name: str, ok: bool, detail: str = ""):
        results.append(ok)
        out(f"[{'OK' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))

    out(f"Media to MP3 v{__version__} | {platform.system()} {platform.machine()} | Python {platform.python_version()}")
    try:
        import yt_dlp
        check("yt-dlp", True, yt_dlp.version.__version__)
    except ImportError as e:
        check("yt-dlp", False, str(e))

    ffmpeg = get_ffmpeg_path()
    check("FFmpeg", bool(ffmpeg), ffmpeg or "not found")
    if not ffmpeg:
        return False

    def run(args, data=None):
        return subprocess.run([ffmpeg, "-hide_banner", "-v", "error", "-y", *args], input=data,
                              capture_output=True, **at._POPEN_FLAGS)

    def last_error(proc) -> str:
        lines = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        return lines[-1] if lines else f"exit code {proc.returncode}"

    # Thành phần FFmpeg bắt buộc (bản phát hành dùng FFmpeg tối giản)
    def names(flag):
        return {line.split()[1] for line in run([flag]).stdout.decode("utf-8", "replace").splitlines()
                if len(line.split()) > 1}
    encoders, filters = names("-encoders"), names("-filters")
    for name in ("libmp3lame", "aac", "flac", "pcm_s16le", "mjpeg"):
        check(f"encoder {name}", name in encoders)
    for name in ("aresample", "asetnsamples", "concat", "acrossfade", "afade", "volume", "loudnorm", "crop", "scale"):
        check(f"filter {name}", name in filters)

    tmp = tempfile.mkdtemp(prefix="media-to-mp3-check-")
    try:
        # 1. Mã hóa âm thanh tự tạo ra mọi định dạng (+ WebM/Opus giống nguồn YouTube)
        pcm = _tone_pcm(TONE_SECONDS, 440)
        sources = {}
        encode_args = {fmt: at.EXPORT_CODECS[fmt] for fmt in AUDIO_FORMATS}
        encode_args["webm"] = ["-c:a", "opus", "-strict", "-2", "-ar", "48000"]
        for fmt, codec in encode_args.items():
            path = os.path.join(tmp, f"tone.{fmt}")
            proc = run(["-f", "s16le", "-ar", str(RATE), "-ac", "2", "-i", "pipe:0", *codec,
                        "-metadata", "title=Tone", path], pcm)
            try:
                duration = at.probe(path).duration if proc.returncode == 0 else 0
            except at.AudioToolError:
                duration = 0
            ok = abs(duration - TONE_SECONDS) < 0.15
            check(f"encode + read {fmt}", ok, "" if ok else last_error(proc))
            if ok:
                sources[fmt] = path

        # 2. Đóng gói lại AAC sang M4A không nén lại (giống khi tải M4A từ YouTube)
        if "m4a" in sources:
            remux = os.path.join(tmp, "remux.m4a")
            proc = run(["-i", sources["m4a"], "-vn", "-acodec", "copy", "-bsf:a", "aac_adtstoasc", remux])
            check("remux AAC -> M4A", proc.returncode == 0, "" if proc.returncode == 0 else last_error(proc))

        # 2b. Ghi chương (chapters) của video vào file nhạc như yt-dlp (đọc file ffmetadata)
        if "mp3" in sources:
            meta = os.path.join(tmp, "chapters.meta")
            with open(meta, "w", encoding="utf-8") as f:
                f.write(";FFMETADATA1\ntitle=Tone\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=1500\ntitle=A\n"
                        "[CHAPTER]\nTIMEBASE=1/1000\nSTART=1500\nEND=3000\ntitle=B\n")
            chaptered = os.path.join(tmp, "chapters.mp3")
            proc = run(["-i", sources["mp3"], "-i", meta, "-map", "0", "-dn", "-ignore_unknown", "-c", "copy",
                        "-map_metadata", "1", "-map_chapters", "1", chaptered])
            check("chapters + tags (ffmetadata)", proc.returncode == 0, "" if proc.returncode == 0 else last_error(proc))

        # 3. Ảnh bìa: khung ảnh thô -> JPEG vuông 600x600 -> nhúng vào MP3 (ID3v2.3)
        cover = os.path.join(tmp, "cover.jpg")
        proc = run(["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "320x180", "-i", "pipe:0", "-frames:v", "1",
                    "-vf", "crop='min(iw,ih)':'min(iw,ih)',scale=600:600", "-c:v", "mjpeg", "-q:v", "3",
                    "-update", "1", cover], bytes([200, 60, 60]) * (320 * 180))
        cover_ok = proc.returncode == 0 and os.path.isfile(cover)
        check("cover art crop/scale -> JPEG", cover_ok, "" if cover_ok else last_error(proc))
        if cover_ok and "mp3" in sources:
            with_cover = os.path.join(tmp, "cover.mp3")
            proc = run(["-i", sources["mp3"], "-i", cover, "-map", "0:0", "-map", "1:0", "-c", "copy",
                        "-id3v2_version", "3", "-write_id3v1", "1", "-disposition:v", "attached_pic", with_cover])
            ok = proc.returncode == 0 and at.probe(with_cover).has_cover
            check("embed cover into MP3", ok, "" if ok else last_error(proc))

        # 4. Cắt + ghép + hiệu ứng, xuất ra mọi định dạng
        inputs = [sources[f] for f in ("webm", "mp3", "flac") if f in sources]
        if len(inputs) >= 2:
            clips = [at.ClipSpec(path, 0.5, 2.5) for path in inputs]
            expected = at.output_duration(clips, 0.5)
            for fmt in at.EXPORT_CODECS:
                out_path = os.path.join(tmp, f"joined.{fmt}")
                try:
                    cmd = at.build_export_command(clips, out_path, fmt=fmt, fade_in=0.3, fade_out=0.5, gain_db=-1,
                                                  crossfade=0.5, normalize=True, title="Check")
                    at.run_export(cmd, expected)
                    duration = at.probe(out_path).duration
                    check(f"cut & join -> {fmt}", abs(duration - expected) < 0.2, f"{duration:.2f}s")
                except at.AudioToolError as e:
                    check(f"cut & join -> {fmt}", False, str(e))

        # 5. Dạng sóng (giải mã ra PCM thô)
        if "m4a" in sources:
            peaks = at.load_peaks(sources["m4a"], TONE_SECONDS)
            check("waveform", bool(peaks) and max(peaks) > 0.5)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = all(results)
    out("All checks passed." if passed else "Some checks FAILED.")
    return passed


if __name__ == "__main__":
    sys.exit(0 if run_selftest() else 1)
