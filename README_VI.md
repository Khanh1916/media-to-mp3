# Media to MP3

[![CI](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml/badge.svg)](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Khanh1916/media-to-mp3?display_name=tag)](https://github.com/Khanh1916/media-to-mp3/releases)
[![Rust](https://img.shields.io/badge/rust-1.80%2B-orange.svg)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

[English](README.md) | Tiếng Việt

Media to MP3 là app tải âm thanh từ video YouTube và Facebook, xuất ra file MP3, M4A, WAV hoặc FLAC kèm công cụ cắt và ghép nhạc trực quan. Dự án ban đầu tôi viết bằng Python, sau đó viết lại hoàn toàn bằng Rust thành một file binary duy nhất nặng khoảng 7.6 MB. App khởi động ngay, tốn chưa tới 30 MB RAM khi chạy, không cần cài Python hay virtualenv.

App hỗ trợ cả giao diện đồ họa (GUI) lẫn dòng lệnh (CLI), chạy trên Windows, Linux và macOS. Ta có thể đổi qua lại giữa tiếng Việt và tiếng Anh ngay trên thanh tiêu đề mà không cần khởi động lại.

Tác giả: KhanhNN (a.k.a Cao Thanh Lam)

## Tính năng

- Tự động bắt link từ clipboard: khi bạn copy link video YouTube hoặc Facebook từ trình duyệt hay bất kỳ đâu, app tự nhận diện và hỏi có đưa vào hàng đợi tải hay không.
- Hàng đợi tải nhiều link: paste một hoặc nhiều link cùng lúc, app tải lần lượt từng bài kèm thanh tiến trình riêng, đo tốc độ, có nút hủy, thử lại, mở thư mục lưu và nghe thử trực tiếp.
- Xuất chuẩn 44.1 kHz / 16-bit (chuẩn CD) để phát tốt trên mọi loa thùng, dàn âm thanh và đầu xe hơi.
- Tự động lấy ảnh bìa vuông và bóc tách tên ca sĩ, tên bài hát từ tiêu đề video bằng regex, loại bỏ các đoạn rác như `(Official Video)`, `[Lyrics]`, `| MV`.
- Cắt và ghép nhạc trực quan: kéo chọn đoạn cần giữ trực tiếp trên dạng sóng âm (waveform), hoặc gõ mốc thời gian chính xác tới phần mười giây.
- Nghe thử đoạn đã chọn ngay trong app trước khi xuất file.
- Bộ lọc âm thanh tiện lợi: fade in, fade out, tăng giảm âm lượng (gain dB) và cân bằng độ to tự động theo chuẩn EBU R128 (loudnorm).
- Giao diện Slate tối giản, dịu mắt, dùng hộp thoại chọn file gốc của hệ điều hành qua `rfd`.
- Hỗ trợ chế độ dòng lệnh (CLI) cho server không có màn hình hoặc khi ta muốn chạy script tự động.

## Định dạng âm thanh

| Format | Bitrate / Chế độ | Thiết bị phù hợp | Ghi chú |
| --- | --- | --- | --- |
| MP3 | 320 / 192 / 128 kbps | Loa, đài, đầu xe hơi, điện thoại | Ghi thẻ ID3v2.3 để các đầu phát đời cũ vẫn đọc đúng tên bài và ca sĩ. |
| M4A (AAC) | Giữ nguyên gốc từ video | iPhone, Android, loa Bluetooth đời mới | Giữ nguyên luồng AAC gốc từ nguồn phát, không nén lại nên không hao hụt chất lượng. |
| WAV | 1411 kbps (PCM không nén) | Thiết bị âm thanh, phần mềm dựng nhạc | Đài nào cũng đọc được, nhưng file nặng (khoảng 10 MB mỗi phút) và không chứa ảnh bìa. |
| FLAC | Lossless (nén không mất dữ liệu) | Dàn âm thanh chất lượng cao, đầu xe đời mới | Giữ trọn vẹn chất lượng gốc kèm đầy đủ thẻ tag và ảnh bìa. |

Opus và OGG không được đưa vào danh sách xuất vì nhiều thiết bị phần cứng và đầu đọc trên ô tô không hỗ trợ.

## Cài đặt

Tải file chạy ở [trang release mới nhất](https://github.com/Khanh1916/media-to-mp3/releases/latest) về dùng luôn, không cần cài đặt:

| Hệ điều hành | File tải về | Cách chạy |
| --- | --- | --- |
| Windows 10 / 11 (64-bit) | `media-to-mp3-windows-x64.zip` | Giải nén rồi mở file `media-to-mp3.exe` (hoặc chạy qua `run.bat`). |
| Linux 64-bit | `media-to-mp3-linux-x64.tar.gz` | Giải nén rồi chạy `./media-to-mp3` (hoặc `./run.sh`). |
| macOS | `media-to-mp3-macos-*.tar.gz` | Giải nén và mở file app. |

Nếu Windows SmartScreen hiện cảnh báo do file chưa mua chứng chỉ chữ ký số thương mại, bạn bấm `More info` rồi chọn `Run anyway` là mở được bình thường.

### Yêu cầu hệ thống

App cần hai công cụ dòng lệnh có sẵn trong `PATH` (hoặc đặt chung thư mục với file exe):
- `ffmpeg`: xử lý bóc tách luồng, chạy bộ lọc và convert định dạng âm thanh.
- `yt-dlp`: lấy luồng video và tải ảnh bìa từ YouTube và Facebook.

## Tự build

Bạn cần cài sẵn Rust 1.80 trở lên:

```bash
git clone https://github.com/Khanh1916/media-to-mp3.git
cd media-to-mp3
cargo build --release
```

File binary sau khi build nằm tại `target/release/media-to-mp3` (trên Windows là `media-to-mp3.exe`).

Ta cũng có thể dùng hai script tiện lợi có sẵn trong repo:
- Windows: nhấp đúp file `run.bat` (script tự kiểm tra bản build release, nếu chưa có sẽ tự build rồi mở app).
- Linux hoặc macOS: chạy `./run.sh`.

## Cách dùng

### Giao diện đồ họa (GUI)

Mở app trực tiếp mà không truyền tham số:

1. Tab Tải nhạc:
   - Paste một hoặc nhiều link video vào ô nhập.
   - Chọn format cần xuất (MP3 320k, 192k, 128k, M4A, FLAC, WAV).
   - Bấm `Thêm vào hàng đợi`. Khi bài tải xong, ta có thể bấm nút `Thư mục` để mở vị trí file, bấm `Nghe` để phát thử, hoặc bấm `Cắt ghép` để chuyển bài sang tab biên tập.

2. Tab Cắt & ghép nhạc:
   - Bấm `Mở file âm thanh` hoặc chuyển bài hát từ tab Tải nhạc sang.
   - Kéo hai thanh đánh dấu trên dạng sóng để chọn đoạn cần giữ, hoặc nhập mốc thời gian cụ thể (ví dụ `0:15.5`).
   - Chọn thêm hiệu ứng nếu cần: fade in, fade out, chỉnh gain dB, cân bằng độ to tự động.
   - Sửa tên bài, ca sĩ rồi bấm `Xuất file âm thanh`.

3. Đổi ngôn ngữ:
   - Bấm nút ngôn ngữ ở góc trên bên phải màn hình để chuyển qua lại giữa Tiếng Việt và English.

### Dòng lệnh (CLI)

Tiện khi làm việc trong terminal hoặc chạy trên máy chủ không có màn hình:

```bash
# Tải MP3 320 kbps mặc định vào thư mục Music của máy:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Tải nhiều link cùng lúc:
./target/release/media-to-mp3 "https://youtu.be/LINK1" "https://youtu.be/LINK2"

# Chọn format và bitrate:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -f flac
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -f mp3 -b 192

# Chỉ định thư mục lưu file:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -o "D:/Music"

# Tự kiểm tra hệ thống và codec offline:
./target/release/media-to-mp3 --check

# Bật chế độ lắng nghe clipboard ở chế độ nền:
./target/release/media-to-mp3 --monitor
```

## Cài đặt lưu ở đâu

Cấu hình của app (thư mục tải, format đã chọn, bitrate, ngôn ngữ) được lưu tự động dạng file JSON:
- Windows: `%APPDATA%\MediaToMP3\settings.json`
- Linux: `~/.config/media-to-mp3/settings.json`
- macOS: `~/Library/Application Support/MediaToMP3/settings.json`

Muốn đưa app về trạng thái mặc định ban đầu, ta chỉ cần xóa file này đi.

## Khắc phục lỗi khi tải

YouTube hay thay đổi cấu trúc trang. Nếu yt-dlp cũ hoặc máy thiếu JavaScript runtime thì việc tải có thể bị chậm hoặc dính lỗi HTTP Error 403:
- Cập nhật yt-dlp lên bản mới nhất: chạy lệnh `yt-dlp -U`.
- Cài JavaScript runtime: nên cài thêm Deno hoặc Node.js để yt-dlp giải mã chữ ký YouTube nhanh hơn.
- Kiểm tra môi trường: chạy lệnh `media-to-mp3 --check` để app kiểm tra đường dẫn ffmpeg và các bộ lọc.

## Kiểm thử

Repo đi kèm bộ 23 bài test tự động kiểm tra xử lý âm thanh, parse mốc thời gian, cấu hình, hàng đợi đa luồng và regex bóc tách tên bài:

```bash
cargo test --all-targets
cargo clippy --all-targets -- -D warnings
cargo fmt -- --check
```

## Cấu trúc thư mục

| Đường dẫn | Nội dung |
| --- | --- |
| `src/main.rs` | Điểm khởi chạy chính, điều phối chế độ CLI và GUI. |
| `src/gui.rs` | Giao diện đồ họa eframe/egui, vẽ dạng sóng âm thanh và quản lý tương tác. |
| `src/audio.rs` | Xử lý âm thanh qua FFmpeg: lấy peak vẽ sóng, cắt ghép, fade in/out, gain và loudnorm. |
| `src/downloader.rs` | Gọi yt-dlp, tải luồng video, lấy ảnh bìa và dùng regex bóc tách tên ca sĩ, bài hát. |
| `src/queue.rs` | Quản lý hàng đợi tải đa luồng, theo dõi tiến trình và hủy tải an toàn. |
| `src/clipboard.rs` | Tiến trình nền lắng nghe clipboard để tự phát hiện link media. |
| `src/config.rs` | Lưu và đọc cấu hình JSON nguyên tử (atomic write). |
| `src/i18n.rs` | Bộ nạp từ điển song ngữ tiếng Việt và tiếng Anh. |
| `src/platform.rs` | Mở thư mục lưu file và gọi trình phát nhạc mặc định của hệ điều hành. |
| `src/selftest.rs` | Kiểm tra chẩn đoán offline FFmpeg và các bộ lọc. |
| `tests/` | Bộ kiểm thử tích hợp. |
| `.github/` | Workflow CI tự động test trên Linux, Windows, macOS và workflow release. |
| `AGENTS.md` | Tài liệu hướng dẫn cho các AI coding agent. |
| `CLAUDE.md` | Hướng dẫn phát triển dành riêng cho Claude Code. |

## Đóng góp

Bạn cứ thoải mái mở issue hoặc gửi pull request. Nhớ đọc [CONTRIBUTING.md](CONTRIBUTING.md) trước khi làm, và xem [SECURITY.md](SECURITY.md) nếu phát hiện lỗ hổng bảo mật. Ai tham gia cũng cần tuân thủ [Code of Conduct](CODE_OF_CONDUCT.md).

Tài liệu dành cho coding agent (OpenAI Codex, Claude Code, Antigravity, Cursor) nằm tại [AGENTS.md](AGENTS.md) và [CLAUDE.md](CLAUDE.md).

## Giấy phép

Mã nguồn phát hành theo [license MIT](LICENSE).
