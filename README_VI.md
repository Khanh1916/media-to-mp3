# 🎵 Media to MP3 Downloader (YouTube & Facebook)

[![CI](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml/badge.svg)](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Khanh1916/media-to-mp3)](https://github.com/Khanh1916/media-to-mp3/releases)
[![Rust](https://img.shields.io/badge/Rust-1.80%2B-orange.svg)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

[English](README.md) | [Tiếng Việt](README_VI.md)

Ứng dụng máy tính và công cụ dòng lệnh (CLI) thuần **Rust**, chuyên tải video từ **YouTube** và **Facebook** thành file âm thanh chất lượng cao **MP3 (lên đến 320 kbps), M4A, WAV hoặc FLAC**, tích hợp sẵn công cụ **chỉnh sửa, cắt & ghép nhạc trực quan**.

Được tái cấu trúc và phát triển toàn diện bằng ngôn ngữ **Rust** nguyên bản kết hợp **eframe / egui**, đem lại tốc độ mở tức thì, dung lượng siêu nhẹ (~7.6 MB), không phụ thuộc môi trường Python, cùng giao diện Dark Mode phong cách Slate/Obsidian chuyên nghiệp, tinh tế.

Tác giả: **KhanhNN (a.k.a Cao Thanh Lam)**

---

## ✨ Tính Năng Nổi Bật

- ⚡ **Thuần Rust & Siêu Nhẹ**: File thực thi độc lập duy nhất chỉ ~7.6 MB, khởi động tức thì trong chớp mắt, chiếm cực ít RAM (<30 MB) và không cần cài đặt Python hay môi trường ảo phức tạp.
- 🎨 **Giao Diện Đồ Họa Bản Quyền (Không Dùng Template AI Cẩu Thả)**:
  - Thiết kế theo tiêu chuẩn công thái học: Tông màu tối Slate/Obsidian (`#0f1117`, `#181c26`), điểm nhấn Indigo thanh lịch (`#6366f1`), font chữ rõ ràng, độ tương phản chuẩn.
  - Phân chia tab rõ ràng: **⬇ Hàng Đợi Tải Nhạc** và **✂ Cắt & Ghép Nhạc**.
  - Trình vẽ dạng sóng âm (waveform canvas) tương tác mượt mà, cho phép kéo thả hai thanh đánh dấu đầu/cuối trực quan.
  - Hộp thoại chọn file và lưu file gốc hệ điều hành qua `rfd`.
- 📋 **Tự Động Bắt Link Thông Minh**: Sao chép (`Ctrl+C`) liên kết YouTube hoặc Facebook từ bất kỳ đâu, app tự nhận diện và hiển thị thông báo thêm nhanh vào hàng đợi.
- 📥 **Hàng Đợi Đa Luồng An Toàn**: Dán nhiều link cùng lúc, xử lý tải nối tiếp hoặc song song với thanh tiến trình trực quan, hiển thị tốc độ, nút Hủy, Thử lại, Mở thư mục và Nghe thử.
- 🔊 **Tối Ưu Cho Mọi Thiết Bị & Đầu Xe Hơi**: Toàn bộ file xuất ra chuẩn âm thanh phòng thu **44.1 kHz / 16-bit** (chuẩn CD):
  | Định dạng | Thông số / Khả năng tương thích |
  |---|---|
  | **MP3** (320 / 192 / 128 kbps) | Chuẩn toàn cầu, chơi mượt trên mọi dàn loa cổ, đầu xe hơi, điện thoại với đầy đủ thẻ ID3v2.3. |
  | **M4A (AAC)** | Luồng AAC nguyên bản từ video gốc, không nén lại, giữ trọn vẹn chất âm ban đầu. |
  | **WAV** | Âm thanh PCM không nén cho các thiết bị âm thanh chuyên nghiệp. |
  | **FLAC** | Nén không mất dữ liệu (lossless) chuẩn studio. |
- 🖼️ **Tự Động Làm Sạch Tên & Nhúng Ảnh Bìa**: Tự động tải ảnh bìa vuông chất lượng cao, đồng thời thuật toán regex tự bóc tách chuỗi rác như `[Official MV]`, `(Lyrics Video)` để tạo thẻ **Ca Sĩ – Tên Bài** chuẩn xác.
- ✂️ **Công Cụ Cắt & Ghép Nhạc Tích Hợp**:
  - Tải nhiều file nhạc hoặc bấm **✂ Cắt ghép** trực tiếp từ bài vừa tải xong.
  - Tự do kéo khoảng chọn trên dạng sóng hoặc điền mốc thời gian chính xác từng phần mười giây (`0:15.5`).
  - Hỗ trợ **fade-in / fade-out**, tăng giảm âm lượng (dB) và **cân bằng âm lượng tự động** EBU R128 (`loudnorm`).
  - Xuất ra file MP3 / M4A / WAV / FLAC với đầy đủ metadata.
- 🌐 **Chuyển Đổi Song Ngữ Tức Thì**: Chuyển đổi giữa **Tiếng Việt** và **English** chỉ với 1 click ngay trên thanh tiêu đề mà không cần khởi động lại.
- 💻 **Đa Năng Cả GUI Lẫn CLI**: Chạy mượt mà dưới dạng giao diện đồ họa hoặc chế độ dòng lệnh headless cho server và script tự động hóa.

---

## 🚀 Cài Đặt & Sử Dụng

### Yêu Cầu Hệ Thống
- [FFmpeg](https://ffmpeg.org/download.html) và [yt-dlp](https://github.com/yt-dlp/yt-dlp) có sẵn trong biến môi trường `PATH` (hoặc cùng thư mục chạy).
- [Rust toolchain](https://rustup.rs/) (chỉ cần khi muốn biên dịch từ mã nguồn).

### 1. Biên Dịch & Chạy Bằng Cargo
```bash
# Clone kho lưu trữ
git clone https://github.com/Khanh1916/media-to-mp3.git
cd media-to-mp3

# Biên dịch bản release tối ưu hoá cao nhất
cargo build --release

# Khởi chạy giao diện
cargo run --release
```

### 2. File Script Chạy Nhanh
- **Windows**: Nhấp đúp vào `run.bat` hoặc gõ trong Command Prompt:
  ```cmd
  run.bat
  ```
- **Linux / macOS**:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

---

## 🎯 Hướng Dẫn Sử Dụng

### Chế Độ Giao Diện Đồ Họa (GUI)
Khởi động ứng dụng trực tiếp bằng file thực thi:
- **Tab Tải Nhạc**: Dán một hoặc nhiều link video, chọn định dạng (MP3 320k, 192k, 128k, M4A, FLAC, WAV), bấm **Thêm vào hàng đợi**. Khi hoàn tất, bấm vào biểu tượng Thư mục để mở file hoặc bấm Nghe thử.
- **Tab Cắt & Ghép**: Bấm **Mở file âm thanh...** hoặc bấm nút **✂ Cắt ghép** từ bài vừa tải về. Kéo thanh chọn trên đồ thị sóng âm, áp dụng hiệu ứng và bấm **Xuất file**.
- **Chuyển Ngôn Ngữ**: Bấm vào nút cờ ở góc trên bên phải (`🇻🇳 Tiếng Việt` / `🇬🇧 English`).

### Chế Độ Dòng Lệnh (CLI)
Truyền URL video trực tiếp để tải nhanh không cần mở cửa sổ:

```bash
# Tải MP3 320kbps mặc định vào thư mục Music:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Tải nhiều liên kết liên tiếp:
./target/release/media-to-mp3 "https://youtu.be/LINK1" "https://youtu.be/LINK2"

# Chọn định dạng (mp3, m4a, wav, flac) và bitrate (128, 192, 320):
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -f flac
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -b 192

# Chỉ định thư mục lưu trữ tùy chỉnh:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -o "D:/Music"

# Tự kiểm tra toàn diện hệ thống (FFmpeg, codec, bộ lọc, xử lý sóng âm):
./target/release/media-to-mp3 --check

# Chạy luồng ngầm tự động giám sát clipboard:
./target/release/media-to-mp3 --monitor
```

---

## 🧪 Kiểm Thử & Đảm Bảo Chất Lượng

Chạy bộ test hoàn chỉnh gồm 23 unit test và integration test bao quát toàn bộ logic xử lý âm thanh, hàng đợi, lưu trữ cấu hình, bộ lọc:

```bash
# Chạy toàn bộ test
cargo test

# Kiểm tra linter nghiêm ngặt
cargo clippy -- -D warnings

# Kiểm tra định dạng code
cargo fmt -- --check
```

---

## 🤖 Hướng Dẫn Cho Các Agent AI Đa Nền Tảng

Kho lưu trữ tích hợp sẵn các tài liệu hướng dẫn chuẩn chỉ cho mọi công cụ lập trình AI thông dụng:

- **[AGENTS.md](AGENTS.md)**: Hướng dẫn tổng quát đa nền tảng (Codex, Devin, Copilot, Gemini)
- **[CLAUDE.md](CLAUDE.md)**: Hướng dẫn dành riêng cho Anthropic Claude Code
- **[.cursorrules](.cursorrules)**: Quy tắc dành riêng cho Cursor AI IDE
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)**: Hướng dẫn cho GitHub Copilot
- **[.gemini/GEMINI.md](.gemini/GEMINI.md)**: Tài liệu chỉ dẫn cho Gemini CLI & Antigravity

---

## 📁 Cấu Trúc Thư Mục Chuẩn Chỉ

```
media-to-mp3/
├── .github/              # Hạ tầng GitHub Actions CI/CD & Community
│   ├── workflows/        # Tự động hóa CI (kiểm thử đa nền tảng) & Release
│   ├── ISSUE_TEMPLATE/   # Mẫu báo lỗi và yêu cầu tính năng
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── copilot-instructions.md
│   └── dependabot.yml    # Tự động cập nhật thư viện hàng tuần
├── Cargo.toml            # Cấu hình gói và thư viện Rust, tối ưu release
├── Cargo.lock            # Khóa phiên bản dependency chính xác
├── rustfmt.toml          # Quy chuẩn định dạng mã Rust
├── clippy.toml           # Cấu hình linter Clippy
├── AGENTS.md             # Tài liệu agent AI đa nền tảng
├── CLAUDE.md             # Hướng dẫn Claude Code
├── .cursorrules          # Cấu hình Cursor AI
├── CONTRIBUTING.md       # Hướng dẫn đóng góp dự án
├── CODE_OF_CONDUCT.md   # Quy tắc ứng xử cộng đồng Contributor Covenant 2.1
├── SECURITY.md           # Chính sách báo cáo lỗ hổng bảo mật
├── CHANGELOG.md          # Lịch sử thay đổi các phiên bản
├── run.bat               # Trình chạy nhanh & tự build trên Windows
├── run.sh                # Trình chạy nhanh trên Linux / macOS
├── src/                  # Toàn bộ mã nguồn thuần Rust
│   ├── main.rs           # Điểm khởi chạy (điều phối GUI hoặc CLI)
│   ├── lib.rs            # Khởi tạo thư viện lõi
│   ├── gui.rs            # Giao diện đồ họa eframe/egui kèm vẽ waveform
│   ├── audio.rs          # Xử lý âm thanh FFmpeg (cắt, ghép, bộ lọc, biên độ)
│   ├── downloader.rs     # Tích hợp yt-dlp, bóc tách luồng & làm sạch metadata
│   ├── queue.rs          # Quản lý hàng đợi tải đa luồng
│   ├── clipboard.rs      # Bắt link tự động từ clipboard đa nền tảng
│   ├── config.rs         # Lưu/đọc cấu hình JSON an toàn (atomic write)
│   ├── i18n.rs           # Quản lý song ngữ (nhúng file strings.json)
│   ├── platform.rs       # Mở Explorer/Finder và phát nhạc nền tảng
│   ├── selftest.rs       # Kiểm tra chuẩn đoán hệ thống offline
│   ├── version.rs        # Định nghĩa số phiên bản
│   └── strings.json      # Bản dịch giao diện Tiếng Việt & Tiếng Anh
├── tests/
│   └── test_rust_suite.rs # Bộ kiểm thử tích hợp chuyên sâu
├── LICENSE               # Giấy phép mã nguồn mở MIT
└── README.md             # Tài liệu Tiếng Anh
```

---

## 📄 Giấy Phép

Dự án được phân phối dưới giấy phép [MIT License](LICENSE).
