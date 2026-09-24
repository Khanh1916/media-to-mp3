"""
Script hỗ trợ đóng gói ứng dụng Media to MP3 thành file thực thi độc lập:
- Trên Windows: file .exe (kèm theo FFmpeg và icon nếu có)
- Trên Linux: file binary thực thi độc lập
"""
import os
import sys
import subprocess
import shutil

def build():
    print("=== Đóng gói ứng dụng Media to MP3 ===")
    
    # Kiểm tra PyInstaller
    if not shutil.which("pyinstaller"):
        print("PyInstaller chưa được cài. Đang tiến hành cài đặt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)

    # Lấy thư mục imageio_ffmpeg để đính kèm ffmpeg binary
    import imageio_ffmpeg
    ffmpeg_module_path = os.path.dirname(imageio_ffmpeg.__file__)

    sep = ";" if sys.platform.startswith("win") else ":"

    # Tham số đóng gói
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",             # Thư mục độc lập chạy mượt và nhanh
        "--windowed",           # Ẩn console đen
        "--name=MediaToMP3",
        f"--add-data={ctk_path}{sep}customtkinter",
        f"--add-data={ffmpeg_module_path}{sep}imageio_ffmpeg",
        "--collect-all=yt_dlp",
        "--collect-all=customtkinter",
        "main.py"
    ]

    print("Đang thực hiện lệnh:", " ".join(cmd))
    subprocess.check_call(cmd)
    print("\n✅ Đóng gói hoàn tất! File thực thi nằm trong thư mục 'dist/MediaToMP3/'")

if __name__ == "__main__":
    build()
