# Media to MP3 Downloader

[![CI](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml/badge.svg)](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Khanh1916/media-to-mp3)](https://github.com/Khanh1916/media-to-mp3/releases)
[![Rust](https://img.shields.io/badge/Rust-1.80%2B-orange.svg)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

[English](README.md) | [Tiếng Việt](README_VI.md)

Ứng dụng máy tính và công cụ dòng lệnh hiệu năng cao được xây dựng hoàn toàn bằng ngôn ngữ Rust. Media to MP3 hỗ trợ tải luồng âm thanh từ video YouTube và Facebook thành các định dạng chất lượng cao (MP3, M4A, FLAC, WAV), đồng thời tích hợp trình biên tập âm thanh dạng sóng trực quan phục vụ việc cắt, ghép và chuẩn hóa âm lượng.

Được phát triển với eframe và egui, ứng dụng được biên dịch thành một file thực thi độc lập duy nhất (~7.6 MB) với tốc độ khởi động tức thì, mức chiếm dụng RAM cực thấp (<30 MB) và không phụ thuộc vào bất kỳ môi trường Python hay runtime bên ngoài nào.

Tác giả: **KhanhNN (Cao Thanh Lam)**

---

## Tính năng nổi bật

- **Thuần Rust nguyên bản**: Được biên dịch trực tiếp sang mã máy với tối ưu hóa link-time (LTO) và lược bỏ ký hiệu debug (strip). Không cần cài đặt Python hay thiết lập môi trường ảo.
- **Giao diện người dùng tối ưu**: Xây dựng theo kiến trúc immediate-mode với bảng màu tối Slate và Obsidian. Cung cấp độ tương phản cao, bố cục thích ứng và sử dụng hộp thoại chọn tệp tin gốc của hệ điều hành qua thư viện `rfd`.
- **Trình biên tập dạng sóng tương tác**: Trực quan hóa biên độ âm thanh từ dữ liệu PCM thô. Hỗ trợ hai thanh đánh dấu mốc thời gian bắt đầu và kết thúc có thể kéo thả trực tiếp trên đồ thị, nhập thời gian chính xác từng phần mười giây, hiệu ứng làm mờ đầu/cuối (fade in/out), tăng giảm âm lượng và chuẩn hóa âm lượng theo chuẩn EBU R128.
- **Tự động bắt liên kết từ bộ nhớ tạm**: Luồng chạy ngầm tự động nhận diện liên kết YouTube và Facebook khi người dùng sao chép, cho phép đưa nhanh vào hàng đợi tải chỉ với một thao tác.
- **Hàng đợi tải đa luồng an toàn**: Xử lý tải bất đồng bộ với thanh tiến trình độc lập cho từng tệp, ước tính tốc độ, hỗ trợ hủy tải và thử lại khi gặp lỗi.
- **Xử lý siêu dữ liệu và ảnh bìa tự động**: Thuật toán biểu thức chính quy (regex) tự động lọc bỏ các cụm từ thừa trên tiêu đề video (như official video, lyric video, remastered) để trích xuất tên Ca sĩ và Bài hát chuẩn mực, tự động nhúng ảnh bìa vuông và ghi thẻ ID3v2.3.
- **Giao diện song ngữ**: Chuyển đổi tức thì giữa Tiếng Việt và Tiếng Anh ngay trên thanh điều hướng mà không cần khởi động lại.
- **Linh hoạt giữa GUI và CLI**: Mặc định khởi chạy giao diện đồ họa, hoặc chạy ở chế độ dòng lệnh headless cho môi trường máy chủ và tự động hóa kịch bản.

---

## Định dạng âm thanh hỗ trợ

Tất cả các tệp âm thanh xuất ra đều được chuẩn hóa về chuẩn 44.1 kHz, 16-bit stereo (chuẩn CD) nhằm đảm bảo khả năng tương thích phần cứng tối đa:

| Định dạng | Bitrate / Chế độ | Thiết bị đích phổ biến | Ghi chú tương thích |
|---|---|---|---|
| MP3 | 320 / 192 / 128 kbps | Đầu xe hơi, dàn loa cổ, điện thoại | Tương thích toàn diện với thẻ ID3v2.3; đọc tốt trên mọi đầu phát ô tô đời cũ. |
| M4A (AAC) | Giữ nguyên gốc / AAC | Điện thoại hiện đại, thiết bị Apple | Giữ nguyên vẹn luồng dữ liệu AAC gốc, không giảm chất lượng do nén lại. |
| WAV | 1411 kbps không nén | Thiết bị phòng thu, phần mềm dựng âm | Âm thanh PCM thô. Tương thích tuyệt đối; không hỗ trợ nhúng ảnh bìa. |
| FLAC | Nén bảo toàn dữ liệu | Dàn nghe nhạc cao cấp, receiver hiện đại | Chuẩn Free Lossless Audio Codec; giữ đầy đủ toàn bộ siêu dữ liệu. |

---

## Yêu cầu môi trường

- **FFmpeg**: Cần thiết để bóc tách luồng âm thanh, áp dụng bộ lọc và mã hóa định dạng. Cần có sẵn trong biến môi trường `PATH` hoặc đặt tại thư mục làm việc.
- **yt-dlp**: Cần thiết để phân tích và lấy luồng media từ các nền tảng video. Cần có sẵn trong `PATH` hoặc đặt tại thư mục làm việc.
- **Bộ công cụ Rust** (1.80+): Chỉ cần thiết nếu bạn muốn tự biên dịch ứng dụng từ mã nguồn.

---

## Hướng dẫn cài đặt và biên dịch

### Biên dịch từ mã nguồn

```bash
# Clone kho lưu trữ
git clone https://github.com/Khanh1916/media-to-mp3.git
cd media-to-mp3

# Biên dịch bản release tối ưu hóa
cargo build --release

# Khởi chạy giao diện
cargo run --release
```

### Script khởi chạy nhanh

- **Windows**: Chạy file `run.bat` (tự động biên dịch bản release nếu chưa có và khởi động ứng dụng ngay).
- **Linux / macOS**:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

---

## Hướng dẫn sử dụng

### Chế độ giao diện đồ họa (GUI)

Khởi động file thực thi `media-to-mp3` không truyền đối số để vào giao diện chính:

1. **Tab Hàng đợi tải nhạc**:
   - Dán một hoặc nhiều liên kết video vào ô nhập liệu.
   - Chọn định dạng mục tiêu bằng thanh nút (MP3 320k, 192k, 128k, M4A, FLAC, WAV).
   - Nhấn **Thêm vào hàng đợi**. Khi hoàn tất, các nút thao tác xuất hiện cho phép mở thư mục chứa tệp, phát nhạc bằng trình phát mặc định của hệ thống, hoặc chuyển trực tiếp tệp sang tab Cắt & ghép.

2. **Tab Cắt & ghép nhạc**:
   - Nhấn **Mở file âm thanh** hoặc chuyển tệp từ hàng đợi tải sang.
   - Kéo hai thanh đánh dấu mốc thời gian bắt đầu và kết thúc trên đồ thị sóng âm để chọn đoạn cần giữ.
   - Tùy chỉnh các thông số: Làm mờ đầu (giây), Làm mờ cuối (giây), Tăng giảm âm lượng (dB), Cân bằng âm lượng tự động.
   - Nhấn **Xuất file âm thanh** để chọn vị trí lưu kết quả.

3. **Thanh trạng thái và tiêu đề**:
   - Hiển thị trực tiếp trạng thái phát hiện của FFmpeg và tiến trình bắt link clipboard ngầm.
   - Nhấn vào nút chọn ngôn ngữ ở góc trên bên phải để chuyển đổi qua lại giữa Tiếng Việt và English.

### Chế độ dòng lệnh (CLI)

Truyền trực tiếp liên kết video vào câu lệnh để tải nhanh ở chế độ headless:

```bash
# Tải tệp MP3 320 kbps mặc định vào thư mục Music:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Tải liên tiếp nhiều liên kết trong một lượt:
./target/release/media-to-mp3 "https://youtu.be/LINK1" "https://youtu.be/LINK2"

# Tùy chọn định dạng và bitrate:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -f flac
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -b 192

# Chỉ định thư mục lưu trữ tùy chỉnh:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -o "D:/Music"

# Chạy bộ tự kiểm tra offline (kiểm tra codec FFmpeg và bộ lọc âm):
./target/release/media-to-mp3 --check

# Chạy tiến trình ngầm giám sát clipboard không mở cửa sổ:
./target/release/media-to-mp3 --monitor
```

---

## Kiểm thử tự động

Bộ kiểm thử gồm 23 bài test tự động bao quát toàn bộ logic xử lý âm thanh, phân tích mốc thời gian, quản lý cấu hình tệp, đồng bộ hàng đợi và chuẩn hóa tiêu đề:

```bash
# Chạy toàn bộ test
cargo test --all-targets

# Kiểm tra linter nghiêm ngặt
cargo clippy --all-targets -- -D warnings

# Kiểm tra định dạng mã nguồn
cargo fmt -- --check
```

---

## Chỉ dẫn dành cho AI Agent đa nền tảng

Kho lưu trữ cung cấp đầy đủ các tệp ngữ cảnh và chỉ dẫn tiêu chuẩn cho các công cụ AI:

- **[AGENTS.md](AGENTS.md)**: Chỉ dẫn chung bao quát kiến trúc, nguyên tắc đa luồng và phong cách lập trình.
- **[CLAUDE.md](CLAUDE.md)**: Cẩm nang phát triển và tham chiếu lệnh cho Anthropic Claude Code.
- **[.cursorrules](.cursorrules)**: Quy chuẩn code dành riêng cho Cursor AI IDE.
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)**: Chỉ dẫn cho GitHub Copilot Workspace.
- **[.gemini/GEMINI.md](.gemini/GEMINI.md)**: Hướng dẫn dành cho Gemini CLI và Google Antigravity.

---

## Cấu trúc kho lưu trữ

```
media-to-mp3/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # CI tự động trên Linux, Windows, macOS
│   │   └── release.yml          # Tự động đóng gói đa nền tảng khi phát hành
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── config.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── copilot-instructions.md
│   └── dependabot.yml
├── Cargo.toml                   # Cấu hình gói và tối ưu hóa bản build release
├── Cargo.lock
├── rustfmt.toml                 # Quy tắc định dạng mã nguồn Rust
├── clippy.toml                  # Thiết lập linter Clippy
├── AGENTS.md                    # Hướng dẫn AI Agent đa nền tảng
├── CLAUDE.md                    # Hướng dẫn Claude Code
├── .cursorrules                 # Quy tắc Cursor
├── CONTRIBUTING.md              # Quy định đóng góp mã nguồn
├── CODE_OF_CONDUCT.md          # Quy tắc ứng xử Contributor Covenant 2.1
├── SECURITY.md                  # Chính sách bảo mật và báo cáo lỗ hổng
├── CHANGELOG.md                 # Lịch sử thay đổi phiên bản
├── run.bat                      # Script chạy nhanh và tự build trên Windows
├── run.sh                       # Script chạy trên Linux và macOS
├── src/
│   ├── main.rs                  # Điểm khởi chạy chính và điều phối CLI/GUI
│   ├── lib.rs                   # Gốc thư viện
│   ├── gui.rs                   # Giao diện đồ họa eframe/egui và vẽ dạng sóng
│   ├── audio.rs                 # Tích hợp tiến trình FFmpeg và bộ lọc âm thanh
│   ├── downloader.rs            # Tích hợp yt-dlp và biểu thức chính quy lọc rác tiêu đề
│   ├── queue.rs                 # Quản lý hàng đợi tải đa luồng
│   ├── clipboard.rs             # Bộ lắng nghe clipboard đa nền tảng
│   ├── config.rs                # Lưu trữ cấu hình JSON nguyên tử (atomic)
│   ├── i18n.rs                  # Bộ nạp bản dịch song ngữ
│   ├── platform.rs              # Tương tác trình duyệt tệp và phát nhạc hệ thống
│   ├── selftest.rs              # Bộ tự kiểm tra chẩn đoán hệ thống offline
│   ├── version.rs               # Định nghĩa hằng số phiên bản
│   └── strings.json             # Từ điển song ngữ Tiếng Việt và Tiếng Anh
├── tests/
│   └── test_rust_suite.rs        # Bộ kiểm thử tích hợp chuyên sâu
├── LICENSE                      # Giấy phép nguồn mở MIT
├── README.md                    # Tài liệu Tiếng Anh
└── README_VI.md                 # Tài liệu Tiếng Việt
```

---

## Giấy phép

Dự án được phân phối dưới [Giấy phép MIT](LICENSE).
