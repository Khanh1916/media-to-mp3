import os
import platform
import subprocess


def open_path_in_explorer(path: str):
    """Mở thư mục hoặc file trong trình quản lý file của Windows/Linux/macOS"""
    try:
        if platform.system() == "Windows":
            if os.path.isfile(path):
                # Chọn trực tiếp file trong File Explorer
                subprocess.run(['explorer', '/select,', os.path.normpath(path)], check=False)
            else:
                os.startfile(os.path.normpath(path))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", "-R", path] if os.path.isfile(path) else ["open", path])
        else:
            # Linux (X11 / Wayland)
            target = os.path.dirname(path) if os.path.isfile(path) else path
            subprocess.Popen(["xdg-open", target])
    except Exception as e:
        print(f"Không thể mở đường dẫn: {e}")


def play_audio_file(file_path: str):
    """Mở phát file nhạc bằng trình phát mặc định của hệ thống"""
    try:
        if platform.system() == "Windows":
            os.startfile(os.path.normpath(file_path))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])
    except Exception as e:
        print(f"Không thể phát file: {e}")
