## 📥 Download

| OS | File |
|---|---|
| **Windows 10 / 11** (64-bit) | `MediaToMP3-{version}-windows-x64.exe` |
| **Linux** (64-bit: Ubuntu 22.04+, Debian 12+, Fedora 36+, Mint 21+...) | `MediaToMP3-{version}-linux-x64.tar.gz` |

A single file — **no Python or FFmpeg install needed**.

### Windows
1. Download the `.exe` and open it.
2. If SmartScreen shows *"Windows protected your PC"* (the app is not code-signed), click **More info → Run anyway**.

### Linux
```bash
tar xzf MediaToMP3-{version}-linux-x64.tar.gz
./MediaToMP3-{version}-linux-x64/MediaToMP3
```
Optional: `sudo apt install xclip` to auto-detect copied links.

### Quick self-check
`MediaToMP3 --check` runs an offline self-check of conversion, cover art and cut & join.

## 💡 Notes
- Installing [Deno](https://deno.com) (optional) makes YouTube downloads more robust when YouTube changes.
- Settings are stored in `%APPDATA%\MediaToMP3` (Windows) or `~/.config/media-to-mp3` (Linux).
- Licenses of the bundled components (FFmpeg, LAME, yt-dlp...): see [THIRD_PARTY_NOTICES.md](https://github.com/Khanh1916/media-to-mp3/blob/main/THIRD_PARTY_NOTICES.md).
- Full guide: [README](https://github.com/Khanh1916/media-to-mp3#readme).

---

## Tiếng Việt

### 📥 Tải về

| Hệ điều hành | File |
|---|---|
| **Windows 10 / 11** (64-bit) | `MediaToMP3-{version}-windows-x64.exe` |
| **Linux** (64-bit: Ubuntu 22.04+, Debian 12+, Fedora 36+, Mint 21+...) | `MediaToMP3-{version}-linux-x64.tar.gz` |

Chỉ một file — **không cần cài Python hay FFmpeg**.

**Windows:** tải file `.exe` rồi mở lên. Nếu Windows báo *"Windows protected your PC"* (app chưa có chữ ký số), bấm **More info → Run anyway**.

**Linux:** giải nén rồi chạy `./MediaToMP3-{version}-linux-x64/MediaToMP3`. Cài thêm `xclip` (`sudo apt install xclip`) để tự bắt link khi Copy.

**Kiểm tra nhanh:** `MediaToMP3 --check` tự kiểm tra chuyển đổi, ảnh bìa, cắt ghép (không cần mạng).

### 💡 Ghi chú
- Cài thêm [Deno](https://deno.com) (không bắt buộc) giúp tải YouTube ổn định hơn khi YouTube thay đổi.
- Cài đặt được lưu tại `%APPDATA%\MediaToMP3` (Windows) hoặc `~/.config/media-to-mp3` (Linux).
- Giấy phép các thành phần đóng gói kèm (FFmpeg, LAME, yt-dlp...): xem [THIRD_PARTY_NOTICES.md](https://github.com/Khanh1916/media-to-mp3/blob/main/THIRD_PARTY_NOTICES.md).
- Hướng dẫn đầy đủ: [README tiếng Việt](https://github.com/Khanh1916/media-to-mp3/blob/main/README_VI.md).
