# 🎵 Media to MP3 Downloader (YouTube & Facebook)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

[English](README.md) | [Tiếng Việt](README_VI.md)

Ứng dụng tải video từ **YouTube** và **Facebook** thành file nhạc **MP3 (lên đến 320 kbps), M4A, WAV hoặc FLAC**, kèm công cụ **cắt, ghép nhạc** ngay trong app. Chạy được trên cả **Windows** và **Linux**, giao diện **Tiếng Việt / English**.

Tác giả: **KhanhNN (a.k.a Cao Thanh Lam)**

---

## ✨ Tính Năng Nổi Bật

- 📋 **Tự động bắt link thông minh**: Khi bạn sao chép (Ctrl+C) link video YouTube hoặc Facebook, ứng dụng tự phát hiện và hỏi có thêm vào hàng đợi tải không.
- 📥 **Hàng đợi tải**: Dán một hoặc nhiều link cùng lúc, app tải lần lượt từng bài. Mỗi bài có tiến trình riêng, hủy / thử lại / bỏ khỏi danh sách được.
- 🔊 **Nhiều định dạng, phát được trên loa đài**: Tất cả xuất ra chuẩn **44.1 kHz / 16-bit** (chuẩn CD):
  | Định dạng | Ghi chú |
  |---|---|
  | **MP3** (320 / 192 / 128 kbps) | Phát được trên mọi loa, đài, đầu xe hơi và điện thoại. Tag ID3v2.3 để đầu đọc đời cũ cũng hiện tên bài. |
  | **M4A (AAC)** | Giữ nguyên AAC gốc, không nén lại. Đầu xe, điện thoại, loa Bluetooth đời mới phát tốt. |
  | **WAV** | Gần như đài nào cũng đọc được, nhưng file nặng (~10 MB/phút), không có ảnh bìa. |
  | **FLAC** | Không mất dữ liệu. Đầu xe, loa đời mới thường hỗ trợ. |
  
  Opus / OGG không được hỗ trợ vì nhiều thiết bị phần cứng không đọc được.
- 🖼️ **Ảnh bìa & tag tự động**: Nhúng ảnh bìa JPEG vuông 600×600 và tự tách **Ca sĩ – Tên bài** từ tiêu đề video (bỏ các phần như `(Official Video)`, `| OFFICIAL MV`). Bật / tắt được trong phần cài đặt.
- ✂️ **Cắt & ghép nhạc**:
  - Thêm nhiều file nhạc (hoặc bấm *Cắt ghép* ngay ở bài vừa tải xong), sắp xếp thứ tự để ghép.
  - Kéo chọn đoạn cần giữ trên **dạng sóng**, hoặc nhập thời gian chính xác (vd. `1:23.5`).
  - **Nghe thử** đoạn đã chọn ngay trong app.
  - Hiệu ứng: **fade in / fade out**, **chuyển mượt (crossfade)** giữa các đoạn, chỉnh **âm lượng**, **cân bằng độ to** (loudnorm).
  - Sửa tên bài / ca sĩ, giữ ảnh bìa, xuất ra MP3 / M4A / WAV / FLAC.
- 💾 **Ghi nhớ cài đặt**: Thư mục lưu, định dạng, chất lượng, ngôn ngữ, kích thước cửa sổ... được giữ lại cho lần mở sau.
- 🌐 **Song ngữ Việt / Anh**: Đổi ngôn ngữ ngay trên giao diện, không cần khởi động lại.
- 🐧 **Đa nền tảng**: Windows 10/11 và Linux (Ubuntu, Debian, Fedora, Arch...). Không cần cài FFmpeg thủ công vì đã có sẵn bản tích hợp qua `imageio-ffmpeg`.
- 💻 **Hai chế độ**: Giao diện đồ họa (GUI) Dark Mode, và dòng lệnh (CLI) cho Terminal / máy chủ.

---

## 📥 Tải Về & Dùng Ngay (không cần cài Python)

Tải bản mới nhất tại **[Releases](https://github.com/Khanh1916/media-to-mp3/releases/latest)**: một file duy nhất (~22–25 MB), đã kèm sẵn FFmpeg.

| Hệ điều hành | File | Cách chạy |
|---|---|---|
| Windows 10 / 11 (64-bit) | `MediaToMP3-x.y.z-windows-x64.exe` | Mở file. Nếu Windows báo *"Windows protected your PC"* (app chưa có chữ ký số), bấm **More info → Run anyway**. |
| Linux 64-bit (Ubuntu 22.04+, Debian 12+, Fedora 36+...) | `MediaToMP3-x.y.z-linux-x64.tar.gz` | Giải nén rồi chạy `./MediaToMP3`. |

Chạy `MediaToMP3 --check` để tự kiểm tra chuyển đổi, ảnh bìa, cắt ghép (không cần mạng).
Muốn chạy từ mã nguồn thì làm theo hướng dẫn bên dưới.

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### 1. Yêu cầu hệ thống
- Đã cài đặt **Python 3.10+** trên máy tính.

### 2. Cài đặt môi trường Python (khuyến nghị cho Linux/macOS)
Với Ubuntu/Debian, Python hệ thống thường báo `externally-managed-environment` khi chạy `pip install` trực tiếp. Cách an toàn nhất là dùng virtual environment `.venv`:

```bash
cd ~/media-to-mp3
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Nếu muốn rút ngắn, có sẵn 2 script trong repo:

```bash
cd ~/media-to-mp3
./setup_venv.sh
./run.sh
```

`setup_venv.sh` sẽ tạo `.venv` nếu chưa có và cài các package cần thiết. `run.sh` sẽ chạy app bằng Python trong `.venv` mà không cần phải activate từng lần.

> **Lưu ý trên Linux**:
> Nếu dùng Ubuntu/Debian và gặp thông báo thiếu Tkinter hoặc xclip, chỉ cần chạy:
> ```bash
> sudo apt update
> sudo apt install python3-tk xclip ffmpeg -y
> ```
> Nút *Nghe đoạn chọn* dùng `paplay` / `pw-play` / `aplay` (Ubuntu desktop có sẵn).

> **Chạy trực tiếp không cần activate**:
> ```bash
> cd ~/media-to-mp3
> .venv/bin/python main.py
> ```

---

## 🎯 Cách Khởi Chạy

### Cách 1: Chạy giao diện đồ họa (GUI)
Với venv đã được kích hoạt:
```bash
python main.py
```
Hoặc chạy trực tiếp bằng file script đã chuẩn bị:
```bash
./run.sh
```

**Tab ⬇ Tải nhạc**
1. Copy link video YouTube / Facebook trên trình duyệt: app tự bắt link và hỏi có thêm vào hàng đợi không.
2. Hoặc dán một hay nhiều link vào ô nhập rồi bấm **➕ Thêm vào hàng đợi**.
3. Chọn định dạng, chất lượng, thư mục lưu. Bài tải xong có các nút *Thư mục*, *Nghe*, *Cắt ghép*.

**Tab ✂ Cắt & ghép nhạc**
1. Bấm **➕ Thêm file nhạc...** (hoặc nút *Cắt ghép* ở hàng đợi tải).
2. Chọn từng đoạn trong danh sách, kéo trên dạng sóng để chọn khoảng cần giữ. Dùng ▲ ▼ để đổi thứ tự ghép.
3. Thêm hiệu ứng nếu muốn, sửa tên bài / ca sĩ, rồi bấm **💾 Xuất file...**.

Đổi **Tiếng Việt / English** ở góc trên bên phải.

### Cách 2: Tải nhanh qua dòng lệnh (CLI)
Dành cho người thích dùng Terminal hoặc chạy trên máy chủ không có giao diện:
```bash
# Tải MP3 320kbps mặc định vào thư mục Music:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
# Hoặc trên Windows:
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Tải nhiều link liên tiếp:
./run.sh "https://youtu.be/LINK1" "https://youtu.be/LINK2"

# Chọn định dạng (mp3, m4a, wav, flac) và chất lượng MP3 (128, 192, 320):
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -f flac
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -b 192

# Chỉ định thư mục lưu trữ:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o "D:/MyMusic"

# Tự kiểm tra FFmpeg và các chức năng (không cần mạng):
./run.sh --check

# Không nhúng ảnh bìa / không tự tách Ca sĩ – Tên bài / hiển thị tiếng Anh:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --no-thumbnail --no-tags --lang en
```

### Nơi lưu cài đặt
- **Windows**: `%APPDATA%\MediaToMP3\settings.json`
- **Linux**: `~/.config/media-to-mp3/settings.json`
- **macOS**: `~/Library/Application Support/MediaToMP3/settings.json`

Xóa file này để trở về cài đặt mặc định.

---

## 🛠️ Khắc Phục Tải Chậm / Lỗi 403 (đặc biệt trên Linux)

YouTube thay đổi liên tục, nên yt-dlp cũ hoặc thiếu JavaScript runtime sẽ khiến tải rất chậm, treo lâu hoặc lỗi `HTTP Error 403`.

1. **Cập nhật yt-dlp** (chạy lại mỗi khi tải bắt đầu chậm/lỗi):
   ```bash
   ./setup_venv.sh
   ```
2. **Cài JavaScript runtime** (yt-dlp dùng để giải mã chữ ký YouTube). Khuyến nghị [Deno](https://deno.com):
   ```bash
   curl -fsSL https://deno.land/install.sh | sh
   ```
   App cũng tự dùng `node` (>= 20), `bun` hoặc `quickjs` nếu có sẵn.
3. **Xem cảnh báo**: chạy app từ Terminal (`./run.sh`), các dòng `[WARNING]` sẽ cho biết nguyên nhân (thiếu JS runtime, mạng phải thử lại, ...).

---

## 🧪 Chạy Kiểm Thử

Bộ test dùng `unittest` có sẵn của Python (cần FFmpeg cho phần test cắt / ghép, không cần mạng):

```bash
python -m unittest discover -s tests -t .
```

---

## 📦 Đóng Gói & Phát Hành

### Build trên máy
```bash
# 1. (Khuyên dùng) Build FFmpeg tối giản ~5 MB thay cho bản đầy đủ ~80 MB (chạy trên Linux / WSL / Docker):
bash packaging/build_ffmpeg.sh windows out-ffmpeg      # hoặc: linux

# 2. Đóng gói thành một file chạy duy nhất:
python build_exe.py --ffmpeg out-ffmpeg/ffmpeg.exe --release
```
- Kết quả: `dist/MediaToMP3.exe` (Windows) hoặc `dist/MediaToMP3` (Linux). `--release` tạo thêm file mang số phiên bản trong `dist/release/`.
- Không truyền `--ffmpeg` thì dùng FFmpeg của `imageio-ffmpeg` (file chạy nặng thêm ~30 MB).
- `build_ffmpeg.sh` cần `build-essential nasm pkg-config curl xz-utils`, thêm `gcc-mingw-w64-x86-64 binutils-mingw-w64-x86-64 mingw-w64-x86-64-dev` khi build cho Windows.

### Phát hành bản mới (GitHub Actions tự build)
1. Tăng số phiên bản trong `version.py`, merge vào `main`.
2. Gắn tag trùng số phiên bản và đẩy lên:
   ```bash
   git tag v1.0.0 && git push origin v1.0.0
   ```
3. Workflow **Build & Release** build FFmpeg tối giản, đóng gói Windows + Linux, chạy `--check` trên chính file đã đóng gói, rồi tạo Release kèm file tải về và `SHA256SUMS.txt`.

Mỗi pull request cũng được build và tự kiểm tra như vậy (không phát hành).

---

## 📁 Cấu Trúc Mã Nguồn

```
media-to-mp3/
├── main.py              # Điểm khởi chạy chính (hỗ trợ cả GUI và CLI)
├── app_ui.py            # Cửa sổ chính: tiêu đề, chọn ngôn ngữ, 2 tab (CustomTkinter)
├── ui_download.py       # Tab tải nhạc: nhập link, định dạng, hàng đợi
├── ui_editor.py         # Tab cắt & ghép: danh sách đoạn, dạng sóng, hiệu ứng, xuất file
├── downloader.py        # Lõi tải video và chuyển đổi âm thanh (yt-dlp + FFmpeg), tách Ca sĩ – Tên bài
├── download_queue.py    # Hàng đợi tải nhiều bài trong luồng nền
├── audio_tools.py       # Cắt / ghép / hiệu ứng / dạng sóng / nghe thử bằng FFmpeg
├── clipboard_monitor.py # Luồng chạy ngầm tự động bắt link YouTube / Facebook
├── config.py            # Lưu / đọc cài đặt người dùng (JSON)
├── i18n.py              # Chuỗi giao diện Tiếng Việt / English
├── platform_utils.py    # Mở thư mục / phát file theo hệ điều hành
├── selftest.py          # Tự kiểm tra (--check): FFmpeg, chuyển đổi, ảnh bìa, cắt ghép
├── version.py           # Số phiên bản
├── tests/               # Bộ kiểm thử (unittest)
├── build_exe.py         # Đóng gói thành một file chạy với PyInstaller
├── packaging/           # Script build FFmpeg tối giản, icon, ghi chú phát hành
├── .github/workflows/   # GitHub Actions: tự build & phát hành bản Windows / Linux
├── setup_venv.sh        # Script khởi tạo môi trường ảo Python và cài đặt thư viện
├── run.sh               # Script chạy nhanh ứng dụng qua môi trường ảo .venv
├── requirements.txt     # Danh sách thư viện phụ thuộc
├── LICENSE              # Giấy phép MIT
├── THIRD_PARTY_NOTICES.md # Giấy phép các thành phần đóng gói kèm (FFmpeg, yt-dlp...)
├── README.md            # Tài liệu hướng dẫn sử dụng (Tiếng Anh)
└── README_VI.md         # Tài liệu hướng dẫn sử dụng (Tiếng Việt)
```
