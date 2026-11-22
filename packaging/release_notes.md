## Download

| OS | File |
|---|---|
| **Windows 10 / 11** (64-bit) | `media-to-mp3-windows-x64.zip` |
| **Linux** (64-bit: Ubuntu 22.04+, Debian 12+, Fedora 36+, Mint 21+...) | `media-to-mp3-linux-x64.tar.gz` |
| **macOS** (Apple Silicon M1/M2/M3/M4) | `media-to-mp3-macos-arm64.tar.gz` |
| **macOS** (Intel x86_64) | `media-to-mp3-macos-x64.tar.gz` |

Compact native binary built in pure Rust (~5.8 MB) with instant startup (<0.2s) and low memory footprint (<30 MB RAM).

### Windows
1. Download `media-to-mp3-windows-x64.zip` and extract it.
2. Double-click `media-to-mp3.exe` (or `run.bat`).
3. If SmartScreen shows *"Windows protected your PC"* (the binary is not code-signed), click **More info -> Run anyway**.

### Linux / macOS
```bash
tar xzf media-to-mp3-linux-x64.tar.gz
./run.sh
```

### Quick self-check
Run offline diagnostics without network:
```bash
media-to-mp3 --check
```

---

## Tiếng Việt

### Tải về

| Hệ điều hành | File |
|---|---|
| **Windows 10 / 11** (64-bit) | `media-to-mp3-windows-x64.zip` |
| **Linux** (64-bit: Ubuntu 22.04+, Debian 12+, Fedora 36+, Mint 21+...) | `media-to-mp3-linux-x64.tar.gz` |
| **macOS** (Apple Silicon M1/M2/M3/M4) | `media-to-mp3-macos-arm64.tar.gz` |
| **macOS** (Intel x86_64) | `media-to-mp3-macos-x64.tar.gz` |

Ứng dụng Rust thuần gọn nhẹ (~5.8 MB), khởi động tức thì (<0.2s), ngốn ít RAM (<30 MB).

**Windows:** Tải file `.zip`, giải nén rồi chạy `media-to-mp3.exe` (hoặc `run.bat`). Nếu SmartScreen cảnh báo, chọn **More info -> Run anyway**.

**Linux / macOS:** Giải nén rồi chạy `./run.sh` hoặc `./media-to-mp3`.

**Kiểm tra nhanh hệ thống:** Chạy `media-to-mp3 --check` để kiểm tra FFmpeg, bộ giải mã và tính năng cắt ghép âm thanh offline.
