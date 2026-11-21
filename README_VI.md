# Media to MP3 Downloader (YouTube & Facebook)

[![CI](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml/badge.svg)](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Khanh1916/media-to-mp3)](https://github.com/Khanh1916/media-to-mp3/releases)
[![Rust](https://img.shields.io/badge/Rust-1.80%2B-orange.svg)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

[English](README.md) | [Tiếng Việt](README_VI.md)

Ứng dụng tải video từ **YouTube** và **Facebook** thành file nhạc **MP3 (lên đến 320 kbps), M4A, WAV hoặc FLAC**, kèm công cụ **cắt, ghép nhạc trực quan** ngay trong app. Viết hoàn toàn bằng **Rust**, chạy mượt mà trên cả **Windows**, **Linux** và **macOS**, giao diện **Tiếng Việt / English** đổi được ngay trên thanh tiêu đề mà không cần khởi động lại.

Tác giả: **KhanhNN (a.k.a Cao Thanh Lam)**

---

## Tính Năng Nổi Bật

- **Tự động bắt link thông minh**: Khi bạn sao chép (Ctrl+C) link video YouTube hoặc Facebook từ bất kỳ đâu, ứng dụng tự phát hiện và hỏi có thêm vào hàng đợi tải không.
- **Hàng đợi tải mượt mà**: Dán một hoặc nhiều link cùng lúc, app tải lần lượt từng bài. Mỗi bài có thanh tiến trình riêng, hiển thị tốc độ tải, nút hủy, thử lại, mở thư mục lưu và nghe thử trực tiếp.
- **Nhiều định dạng, phát tốt trên mọi loa đài & đầu xe hơi**: Tất cả xuất ra chuẩn **44.1 kHz / 16-bit** (chuẩn CD):
  | Định dạng | Ghi chú & Khả năng tương thích |
  |---|---|
  | **MP3** (320 / 192 / 128 kbps) | Phát được trên mọi loa, đài, đầu xe hơi và điện thoại. Ghi thẻ ID3v2.3 để đầu đọc đời cũ cũng hiện đúng tên bài và ca sĩ. |
  | **M4A (AAC)** | Giữ nguyên AAC gốc từ video, không nén lại nên giữ nguyên vẹn chất lượng. Đầu xe, điện thoại, loa Bluetooth đời mới phát rất tốt. |
  | **WAV** | Gần như đài nào cũng đọc được, âm thanh PCM không nén nhưng file nặng (~10 MB/phút) và không hỗ trợ ảnh bìa. |
  | **FLAC** | Nén không mất dữ liệu (lossless). Dàn âm thanh hoặc đầu xe đời mới thường hỗ trợ tốt. |

  Opus / OGG không được đưa vào vì nhiều thiết bị phần cứng đời cũ không đọc được.
- **Ảnh bìa & tag tự động chuẩn chỉnh**: Tự động tải ảnh bìa vuông chất lượng cao và thuật toán regex tự bóc tách **Ca sĩ – Tên bài** từ tiêu đề video (tự lọc bỏ các cụm từ thừa như `(Official Video)`, `| OFFICIAL MV`, `[Lyrics]`). Bật / tắt được trong phần cài đặt.
- **Cắt & ghép nhạc trực quan**:
  - Thêm nhiều file nhạc (hoặc bấm *Cắt ghép* ngay ở bài vừa tải xong), sắp xếp thứ tự để ghép nối.
  - Kéo chọn đoạn cần giữ trực tiếp trên **dạng sóng âm thanh**, hoặc nhập mốc thời gian chính xác (vd. `0:15.5`).
  - **Nghe thử** đoạn đã chọn ngay trong app.
  - Hiệu ứng tiện lợi: **fade in / fade out** (làm mờ đầu/cuối), chỉnh **âm lượng (gain dB)**, **cân bằng độ to tự động** (loudnorm theo chuẩn EBU R128).
  - Sửa tên bài / ca sĩ, giữ nguyên ảnh bìa, xuất ra MP3 / M4A / WAV / FLAC.
- **Bản chạy native siêu nhẹ bằng Rust**: Không cần cài Python, không cần virtualenv phức tạp. Một file thực thi duy nhất (~7.6 MB), khởi động tức thì trong chớp mắt, ăn chưa tới 30 MB RAM.
- **Giao diện tối gọn gàng, công thái học**: Thiết kế theo tông Slate/Obsidian dịu mắt, độ tương phản chuẩn, dùng hộp thoại chọn file gốc của hệ điều hành.
- **Linh hoạt hai chế độ**: Giao diện đồ họa (GUI) cho người dùng hàng ngày, và dòng lệnh (CLI) cho terminal / máy chủ không có màn hình.

---

## Tải Về & Khởi Chạy Nhanh

Tải bản phát hành mới nhất tại **[Releases](https://github.com/Khanh1916/media-to-mp3/releases/latest)**:

| Hệ điều hành | File tải về | Cách chạy |
|---|---|---|
| **Windows 10 / 11** (64-bit) | `media-to-mp3-windows-x64.zip` | Giải nén rồi nhấp đúp file `media-to-mp3.exe` (hoặc chạy qua `run.bat`). |
| **Linux 64-bit** (Ubuntu, Debian, Fedora, Arch...) | `media-to-mp3-linux-x64.tar.gz` | Giải nén và chạy `./media-to-mp3` (hoặc `./run.sh`). |
| **macOS** (Apple Silicon / Intel) | `media-to-mp3-macos-*.tar.gz` | Giải nén và mở ứng dụng. |

Nếu Windows SmartScreen hiện cảnh báo *"Windows protected your PC"* (do app mã nguồn mở chưa mua chứng chỉ chữ ký số thương mại), bạn bấm **More info → Run anyway** là mở được bình thường.

---

## Yêu Cầu Hệ Thống

- **FFmpeg**: Cần có sẵn trong biến môi trường `PATH` (hoặc đặt cùng thư mục chạy) để bóc tách luồng, áp dụng bộ lọc và chuyển đổi âm thanh.
- **yt-dlp**: Cần có sẵn trong `PATH` để lấy luồng video và ảnh bìa từ YouTube/Facebook.
- **Bộ công cụ Rust** (Rust 1.80+): Chỉ cần nếu bạn muốn tự biên dịch từ mã nguồn.

---

## Hướng Dẫn Biên Dịch Từ Mã Nguồn

```bash
# Clone kho mã nguồn về máy
git clone https://github.com/Khanh1916/media-to-mp3.git
cd media-to-mp3

# Biên dịch bản release tối ưu hóa
cargo build --release

# Khởi chạy giao diện ngay
cargo run --release
```

Hoặc dùng các file script tiện lợi có sẵn trong repo:
- **Windows**: Nhấp đúp vào `run.bat` (script tự kiểm tra bản build release, nếu chưa có sẽ tự build rồi mở app).
- **Linux / macOS**:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

---

## Hướng Dẫn Sử Dụng

### Cách 1: Giao diện đồ họa (GUI)

Khởi động ứng dụng trực tiếp bằng file thực thi mà không truyền tham số:

1. **Tab Tải nhạc**:
   - Dán một hoặc nhiều link video vào ô nhập.
   - Chọn định dạng cần xuất (MP3 320k, 192k, 128k, M4A, FLAC, WAV).
   - Bấm **Thêm vào hàng đợi**. Khi bài tải xong, bấm vào nút *Thư mục* để mở ngay vị trí lưu file, nút *Nghe* để phát thử, hoặc nút *Cắt ghép* để chuyển bài hát sang tab biên tập.

2. **Tab Cắt & ghép nhạc**:
   - Bấm **Mở file âm thanh** (hoặc bấm nút *Cắt ghép* ở danh sách bài vừa tải xong).
   - Kéo hai thanh đánh dấu đầu/cuối trên dạng sóng để chọn đoạn cần giữ.
   - Chọn thêm hiệu ứng nếu muốn: Làm mờ đầu (fade in), Làm mờ cuối (fade out), Âm lượng (gain dB), Cân bằng độ to tự động.
   - Chỉnh sửa tên bài / ca sĩ rồi bấm **Xuất file âm thanh**.

3. **Chuyển đổi ngôn ngữ**:
   - Bấm vào nút chuyển đổi ngôn ngữ ở góc trên bên phải để đổi qua lại giữa Tiếng Việt và English ngay tức thì.

### Cách 2: Tải nhanh qua dòng lệnh (CLI)

Rất tiện khi bạn đang ở trong Terminal hoặc chạy trên máy chủ không có giao diện:

```bash
# Tải MP3 320kbps mặc định vào thư mục Music của máy:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Tải nhiều link liên tiếp trong một lệnh:
./target/release/media-to-mp3 "https://youtu.be/LINK1" "https://youtu.be/LINK2"

# Chọn định dạng (mp3, m4a, wav, flac) và bitrate MP3 (128, 192, 320):
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -f flac
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -b 192

# Chỉ định thư mục lưu trữ tùy ý:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -o "D:/Music"

# Tự kiểm tra hệ thống và codec offline (không cần mạng):
./target/release/media-to-mp3 --check

# Chạy chế độ tự động bắt link clipboard ngầm:
./target/release/media-to-mp3 --monitor
```

---

## Nơi Lưu Cài Đặt

Cài đặt (thư mục tải về, định dạng đã chọn, bitrate, ngôn ngữ...) được tự động lưu lại an toàn cho những lần mở sau:
- **Windows**: `%APPDATA%\MediaToMP3\settings.json`
- **Linux**: `~/.config/media-to-mp3/settings.json`
- **macOS**: `~/Library/Application Support/MediaToMP3/settings.json`

Xóa file này nếu bạn muốn đưa app về cài đặt gốc ban đầu.

---

## Khắc Phục Khi Tải Bị Chậm / Lỗi 403

YouTube thường xuyên thay đổi cấu trúc trang web, nếu yt-dlp bị cũ hoặc máy thiếu JavaScript runtime thì việc tải có thể bị chậm hoặc báo lỗi `HTTP Error 403`:

1. **Cập nhật yt-dlp**: Luôn giữ yt-dlp ở bản mới nhất bằng cách tải từ trang chủ yt-dlp hoặc gõ `yt-dlp -U`.
2. **Cài JavaScript runtime**: Khuyến nghị cài thêm [Deno](https://deno.com) hoặc Node.js (yt-dlp dùng engine này để giải mã chữ ký âm thanh YouTube nhanh hơn).
3. **Kiểm tra công cụ**: Chạy `media-to-mp3 --check` từ dòng lệnh để ứng dụng tự kiểm tra đường dẫn FFmpeg và các bộ lọc âm thanh.

---

## Kiểm Thử Tự Động

Repo đi kèm bộ kiểm thử toàn diện gồm 23 bài test tự động bao quát toàn bộ logic xử lý âm thanh, phân tích mốc thời gian, quản lý cấu hình, đồng bộ hàng đợi đa luồng và chuẩn hóa tên bài:

```bash
# Chạy toàn bộ test
cargo test --all-targets

# Kiểm tra linter nghiêm ngặt
cargo clippy --all-targets -- -D warnings

# Kiểm tra quy chuẩn định dạng code
cargo fmt -- --check
```

---

## Cấu Trúc Mã Nguồn

```
media-to-mp3/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # CI tự động test trên Linux, Windows, macOS
│   │   └── release.yml          # Tự động build và đóng gói đa nền tảng
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md        # Mẫu báo lỗi
│   │   ├── feature_request.md   # Mẫu đề xuất tính năng
│   │   └── config.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── copilot-instructions.md
│   └── dependabot.yml           # Quét cập nhật thư viện hàng tuần
├── Cargo.toml                   # Cấu hình gói Rust và tối ưu hóa release
├── Cargo.lock
├── rustfmt.toml                 # Cấu hình format code chuẩn
├── clippy.toml                  # Cấu hình linter Clippy
├── AGENTS.md                    # Tài liệu hướng dẫn cho AI Agent
├── .cursorrules                 # Cấu hình cho Cursor IDE
├── CONTRIBUTING.md              # Quy định đóng góp mã nguồn
├── CODE_OF_CONDUCT.md          # Quy tắc ứng xử cộng đồng Contributor Covenant 2.1
├── SECURITY.md                  # Chính sách báo cáo lỗ hổng bảo mật
├── CHANGELOG.md                 # Lịch sử thay đổi các phiên bản
├── run.bat                      # Script chạy nhanh và tự build trên Windows
├── run.sh                       # Script chạy trên Linux và macOS
├── src/
│   ├── main.rs                  # Điểm khởi chạy chính và điều phối CLI/GUI
│   ├── lib.rs                   # Xuất khẩu thư viện lõi
│   ├── gui.rs                   # Giao diện đồ họa eframe/egui và vẽ dạng sóng âm
│   ├── audio.rs                 # Xử lý âm thanh FFmpeg (cắt, ghép, bộ lọc, biên độ)
│   ├── downloader.rs            # Tích hợp yt-dlp và tách Ca sĩ – Tên bài
│   ├── queue.rs                 # Hàng đợi tải đa luồng an toàn
│   ├── clipboard.rs             # Bộ lắng nghe clipboard tự động bắt link
│   ├── config.rs                # Lưu trữ cấu hình JSON nguyên tử (atomic)
│   ├── i18n.rs                  # Bộ nạp bản dịch song ngữ Việt / Anh
│   ├── platform.rs              # Mở Explorer/Finder và phát nhạc hệ thống
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

## Giấy Phép

Dự án được phân phối dưới [Giấy phép MIT](LICENSE).
