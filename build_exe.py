"""
Đóng gói Media to MP3 thành MỘT file chạy độc lập, tải về là dùng được (không cần cài Python):
- Windows: dist/MediaToMP3.exe
- Linux:   dist/MediaToMP3

Để file nhẹ, truyền FFmpeg tối giản build bằng `packaging/build_ffmpeg.sh` (~5 MB) qua --ffmpeg.
Không truyền thì dùng FFmpeg đầy đủ của imageio-ffmpeg (~80 MB, file chạy nặng hơn nhiều).

Dùng:
    python build_exe.py [--ffmpeg ĐƯỜNG_DẪN_FFMPEG] [--onedir] [--release]

--release: tạo thêm file phát hành có số phiên bản trong dist/release/
           (Windows: .exe, Linux: .tar.gz giữ quyền chạy).
"""
import argparse
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile

from version import __version__

ROOT = os.path.dirname(os.path.abspath(__file__))
IS_WINDOWS = sys.platform.startswith("win")
APP_NAME = "MediaToMP3"
FFMPEG_NAME = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"

# Không dùng tới trong app, bỏ ra cho nhẹ: PIL chỉ là phụ thuộc tùy chọn của CustomTkinter,
# imageio-ffmpeg được thay bằng FFmpeg đóng gói kèm, sqlite3 chỉ để yt-dlp đọc cookie trình duyệt,
# setuptools / pydoc_data / _pyrepl là công cụ phát triển của Python
EXCLUDES = ["PIL", "imageio_ffmpeg", "imageio", "numpy", "sqlite3",
            "setuptools", "pkg_resources", "_distutils_hack", "pydoc_data", "_pyrepl"]


def ensure_pyinstaller():
    if importlib.util.find_spec("PyInstaller") is None:
        print("PyInstaller chưa được cài. Đang tiến hành cài đặt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def stage_ffmpeg(path: str) -> str:
    """Chép FFmpeg vào build/ffmpeg/ với tên chuẩn để app tìm thấy trong bản đóng gói"""
    if path:
        if not os.path.isfile(path):
            sys.exit(f"Không tìm thấy FFmpeg: {path}")
        source = path
    else:
        print("⚠️  Không có --ffmpeg: dùng FFmpeg đầy đủ của imageio-ffmpeg (file chạy nặng thêm ~80 MB).")
        print("    Build FFmpeg tối giản: bash packaging/build_ffmpeg.sh <linux|windows> <thư_mục_đầu_ra>")
        import imageio_ffmpeg
        source = imageio_ffmpeg.get_ffmpeg_exe()

    stage_dir = os.path.join(ROOT, "build", "ffmpeg")
    os.makedirs(stage_dir, exist_ok=True)
    target = os.path.join(stage_dir, FFMPEG_NAME)
    shutil.copyfile(source, target)
    os.chmod(target, 0o755)
    print(f"FFmpeg: {source} ({os.path.getsize(target) / 1e6:.1f} MB)")
    return target


def build(ffmpeg: str, onedir: bool):
    sep = os.pathsep
    icon_ico = os.path.join(ROOT, "packaging", "icon.ico")
    icon_png = os.path.join(ROOT, "packaging", "icon.png")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onedir" if onedir else "--onefile",
        f"--name={APP_NAME}",
        "--noupx",  # UPX hay bị phần mềm diệt virus báo nhầm
        f"--add-binary={ffmpeg}{sep}.",
        f"--add-data={icon_ico}{sep}packaging",
        f"--add-data={icon_png}{sep}packaging",
        "--collect-data=customtkinter",
        *[f"--exclude-module={module}" for module in EXCLUDES],
    ]
    if IS_WINDOWS:
        cmd += ["--windowed", f"--icon={icon_ico}"]
    else:
        cmd += ["--strip"]
    cmd.append(os.path.join(ROOT, "main.py"))

    print("Đang thực hiện lệnh:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def package_release(onedir: bool) -> str:
    machine = platform.machine().lower()
    arch = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64"}.get(machine, machine)
    system = "windows" if IS_WINDOWS else platform.system().lower()
    base = f"{APP_NAME}-{__version__}-{system}-{arch}"
    dist = os.path.join(ROOT, "dist")
    release_dir = os.path.join(dist, "release")
    os.makedirs(release_dir, exist_ok=True)

    if onedir and IS_WINDOWS:
        asset = os.path.join(release_dir, base + ".zip")
        source = os.path.join(dist, APP_NAME)
        with zipfile.ZipFile(asset, "w", zipfile.ZIP_DEFLATED) as zf:
            for folder, _, files in os.walk(source):
                for name in files:
                    path = os.path.join(folder, name)
                    zf.write(path, os.path.join(base, os.path.relpath(path, source)))
    elif IS_WINDOWS:
        asset = os.path.join(release_dir, base + ".exe")
        shutil.copyfile(os.path.join(dist, APP_NAME + ".exe"), asset)
    else:
        # tar.gz giữ quyền chạy của file (tải file trần qua trình duyệt sẽ mất quyền này)
        asset = os.path.join(release_dir, base + ".tar.gz")
        with tarfile.open(asset, "w:gz") as tar:
            tar.add(os.path.join(dist, APP_NAME), arcname=os.path.join(base, APP_NAME))
    print(f"File phát hành: {asset} ({os.path.getsize(asset) / 1e6:.1f} MB)")
    return asset


def main():
    # Console Windows (vd. máy build của GitHub Actions) mặc định cp1252, không in được tiếng Việt
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Đóng gói Media to MP3 bằng PyInstaller")
    parser.add_argument("--ffmpeg", help="FFmpeg sẽ đóng gói kèm (khuyên dùng bản tối giản của build_ffmpeg.sh)")
    parser.add_argument("--onedir", action="store_true", help="Đóng gói thành thư mục thay vì một file")
    parser.add_argument("--release", action="store_true", help="Tạo file phát hành có số phiên bản trong dist/release/")
    args = parser.parse_args()

    print(f"=== Đóng gói Media to MP3 v{__version__} ===")
    ensure_pyinstaller()
    build(stage_ffmpeg(args.ffmpeg), args.onedir)
    target = os.path.join("dist", APP_NAME if args.onedir else APP_NAME + (".exe" if IS_WINDOWS else ""))
    print(f"\n✅ Đóng gói hoàn tất: {target}")
    if args.release:
        package_release(args.onedir)


if __name__ == "__main__":
    main()
