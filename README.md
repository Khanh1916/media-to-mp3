# 🎵 Media to MP3 Downloader (YouTube & Facebook)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

Ứng dụng tải và chuyển đổi video từ **YouTube** và **Facebook** sang file nhạc **MP3 chất lượng cao (lên đến 320 kbps)**, hỗ trợ chạy trên cả **Windows** và **Linux**.

Tác giả: **KhanhNN (a.k.a Cao Thanh Lam)**

---

## ✨ Tính Năng Nổi Bật

- 📋 **Tự động bắt link thông minh**: Khi bạn sao chép (Ctrl+C) bất kỳ đường link video YouTube hoặc Facebook nào, ứng dụng sẽ tự động phát hiện, điền link và hiển thị popup hỏi bạn có muốn tải MP3 không.
- ⚡ **Chất lượng âm thanh tùy chọn**: Hỗ trợ 3 chuẩn bitrate phổ biến:
  - `320 kbps`: Chất lượng âm thanh cao cấp nhất (HQ Studio).
  - `192 kbps`: Chuẩn âm thanh phổ thông, cân bằng dung lượng và chất lượng.
  - `128 kbps`: Dung lượng siêu nhẹ.
- 🖼️ **Tự động gắn Metadata & Tag**: Ghi thông tin bài hát (tên ca sĩ, tiêu đề) vào thẻ ID3 của file MP3.
- 🎧 **Thao tác nhanh**: Sau khi tải xong, có sẵn 2 nút:
  - *Mở thư mục chứa file* (trong File Explorer / File Manager).
  - *Nghe thử file MP3* (mở bằng trình phát nhạc mặc định của máy).
- 🐧 **Đa nền tảng (Cross-platform)**:
  - Hoạt động mượt mà trên **Windows 10/11** và các bản phân phối **Linux** (Ubuntu, Debian, Fedora, Arch...).
  - Không cần cài đặt FFmpeg thủ công: Đã tích hợp sẵn binary FFmpeg tĩnh thông qua thư viện `imageio-ffmpeg`.
- 💻 **Hỗ trợ 2 chế độ**:
  - Giao diện đồ họa trực quan (GUI) hiện đại với Dark Mode (`app_ui.py`).
  - Dòng lệnh (CLI) siêu nhanh cho môi trường Terminal/Server (`python main.py <URL>`).

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### 1. Yêu cầu hệ thống
- Đã cài đặt **Python 3.8+** trên máy tính.

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

Giao diện Dark Mode hiện đại sẽ xuất hiện. Bạn chỉ cần:
1. Copy link video YouTube hoặc Facebook trên trình duyệt.
2. Công cụ sẽ tự động bắt link và hỏi bạn có muốn tải không.
3. Hoặc nhấn nút **📋 Dán** và bấm **⬇️ BẮT ĐẦU TẢI MP3**.

### Cách 2: Tải nhanh qua dòng lệnh (CLI)
Dành cho người thích dùng Terminal hoặc chạy trên máy chủ không có giao diện:
```bash
# Tải MP3 320kbps mặc định vào thư mục Music:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Chỉ định chất lượng (128, 192, hoặc 320):
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -b 192

# Chỉ định thư mục lưu trữ:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o "D:/MyMusic"
```

---

## 📦 Đóng Gói Thành File Thực Thi (.exe hoặc binary)

Bạn có thể đóng gói ứng dụng để chia sẻ cho người khác dùng mà không cần cài đặt Python:

```bash
python build_exe.py
```
Sau khi build xong:
- **Windows**: File chạy `.exe` nằm trong thư mục `dist/MediaToMP3/MediaToMP3.exe`.
- **Linux**: File binary nằm trong thư mục `dist/MediaToMP3/MediaToMP3`.

---

## 📁 Cấu Trúc Mã Nguồn

```
media-to-mp3/
├── app_ui.py            # Giao diện đồ họa người dùng (CustomTkinter)
├── downloader.py        # Xử lý lõi tải video và chuyển đổi MP3 (yt-dlp + FFmpeg)
├── clipboard_monitor.py # Luồng chạy ngầm tự động bắt link YouTube / Facebook
├── main.py              # Điểm khởi chạy chính (hỗ trợ cả GUI và CLI)
├── build_exe.py         # Script đóng gói ứng dụng với PyInstaller
├── requirements.txt     # Danh sách thư viện phụ thuộc
└── README.md            # Tài liệu hướng dẫn sử dụng
```
