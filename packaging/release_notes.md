## 📥 Tải về / Download

| Hệ điều hành / OS | File |
|---|---|
| **Windows 10 / 11** (64-bit) | `MediaToMP3-<phiên bản>-windows-x64.exe` |
| **Linux** (64-bit: Ubuntu 22.04+, Debian 12+, Fedora 36+, Mint 21+...) | `MediaToMP3-<phiên bản>-linux-x64.tar.gz` |

Một file duy nhất, **không cần cài Python hay FFmpeg**. / A single file, **no Python or FFmpeg install needed**.

### Windows
1. Tải file `.exe` rồi mở lên. / Download the `.exe` and open it.
2. Nếu Windows báo *"Windows protected your PC"* (app chưa có chữ ký số): bấm **More info → Run anyway**.
   If SmartScreen shows *"Windows protected your PC"* (the app is not code-signed): click **More info → Run anyway**.

### Linux
```bash
tar xzf MediaToMP3-*-linux-x64.tar.gz
./MediaToMP3-*-linux-x64/MediaToMP3
```
Tùy chọn / Optional: `sudo apt install xclip` để tự bắt link khi Copy (auto-detect copied links).

### Kiểm tra nhanh / Quick self-check
`MediaToMP3 --check` tự kiểm tra chuyển đổi, ảnh bìa, cắt ghép (không cần mạng). / runs an offline self-check of conversion, cover art and cut & join.

## 💡 Ghi chú / Notes
- Cài thêm [Deno](https://deno.com) (không bắt buộc) giúp tải YouTube ổn định hơn khi YouTube thay đổi. / Installing [Deno](https://deno.com) (optional) makes YouTube downloads more robust.
- Cài đặt được lưu tại `%APPDATA%\MediaToMP3` (Windows) hoặc `~/.config/media-to-mp3` (Linux). / Settings are stored in the folders above.
- Giấy phép các thành phần đóng gói kèm (FFmpeg, LAME, yt-dlp...): xem [THIRD_PARTY_NOTICES.md](https://github.com/Khanh1916/media-to-mp3/blob/main/THIRD_PARTY_NOTICES.md). / Bundled components' licenses: see THIRD_PARTY_NOTICES.md.
