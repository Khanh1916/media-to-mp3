# 🎵 Media to MP3 Downloader (YouTube & Facebook)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/Rust-1.80%2B-orange.svg)](https://www.rust-lang.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

[English](README.md) | [Tiếng Việt](README_VI.md)

A pure **Rust** desktop application and CLI tool that downloads videos from **YouTube** and **Facebook** as high-fidelity **MP3 (up to 320 kbps), M4A, WAV, or FLAC** audio, featuring a built-in **interactive audio editor (cut & join)**. 

Engineered from the ground up in native Rust with **eframe / egui**, providing an ultra-lightweight binary (~7.6 MB), instantaneous startup, zero Python dependencies, and an elegant Slate/Obsidian dark aesthetic.

Author: **KhanhNN (a.k.a Cao Thanh Lam)**

---

## ✨ Key Features

- ⚡ **Pure Native Rust & Ultra Lightweight**: Single standalone binary (~7.6 MB), instant launch, minimal memory footprint (<30 MB RAM), and zero external runtimes needed.
- 🎨 **Modern Native GUI (No AI Templates)**:
  - Engineered with clean human-centered UX patterns: Slate/Obsidian dark palette (`#0f1117`, `#181c26`), subtle Indigo accents (`#6366f1`), high contrast typography, and custom vector icons.
  - Interactive multi-tab layout: **⬇ Download Queue** and **✂ Cut & Join Editor**.
  - Interactive canvas waveform renderer with real-time draggable selection markers.
  - Native OS file dialogs via `rfd`.
- 📋 **Smart Clipboard Auto-detection**: Copy (`Ctrl+C`) any YouTube or Facebook link and the app automatically captures and prompts to queue it for download.
- 📥 **Thread-Safe Download Queue**: Paste single or batch URLs; items download concurrently or sequentially with live progress bars, speed metrics, and cancel/retry controls.
- 🔊 **Stereo & Car Audio Friendly Formats**: All audio conforms to the **44.1 kHz / 16-bit** CD standard:
  | Format | Profile / Details |
  |---|---|
  | **MP3** (320 / 192 / 128 kbps) | Universal compatibility across all car stereos, home theaters, and phones with ID3v2.3 tags. |
  | **M4A (AAC)** | Pure untouched AAC stream from source without re-encoding quality loss. |
  | **WAV** | Uncompressed PCM audio for hardware studio / older audio deck compatibility. |
  | **FLAC** | Bit-perfect lossless compression. |
- 🖼️ **Intelligent Tag & Cover Art Extraction**: Automatically downloads and embeds high-resolution square cover art, and cleans noisy video titles (e.g., stripping `[Official MV]`, `(Lyrics Video)`) into pristine **Artist – Title** tags.
- ✂️ **Integrated Audio Editor**:
  - Load multiple tracks, drag selection bounds on the live waveform, or type sub-second timestamps (`0:15.5`).
  - Audio post-processing: **fade-in / fade-out**, volume gain adjustment (dB), and EBU R128 **loudness normalization** (`loudnorm`).
  - Direct export to MP3 / M4A / WAV / FLAC with metadata preservation.
- 🌐 **Instant Bilingual Toggle**: Switch on-the-fly between **Tiếng Việt** and **English** without restarting.
- 💻 **Versatile Dual Operation**: Run with a graphical user interface (GUI) or as a headless Command Line Interface (CLI) for scripts and remote servers.

---

## 🚀 Quick Start

### Prerequisites
- [FFmpeg](https://ffmpeg.org/download.html) and [yt-dlp](https://github.com/yt-dlp/yt-dlp) in your system `PATH` (or current directory).
- [Rust toolchain](https://rustup.rs/) (only if compiling from source).

### 1. Build and Run via Cargo
```bash
# Clone the repository
git clone https://github.com/Khanh1916/media-to-mp3.git
cd media-to-mp3

# Build optimized release binary
cargo build --release

# Launch GUI
cargo run --release
```

### 2. Convenience Scripts
- **Windows**: Double-click `run.bat` or run:
  ```cmd
  run.bat
  ```
- **Linux / macOS**:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

---

## 🎯 Usage

### Graphical Interface (GUI)
Simply launch `media-to-mp3` without arguments:
- **Download Tab**: Paste one or multiple YouTube/Facebook links, choose the format pill (MP3 320k, 192k, 128k, M4A, FLAC, WAV), and click **Add to Queue**. Each item provides live status, progress bar, play button, and file explorer reveal.
- **Audio Editor Tab**: Click **Open Audio File...** or hit **✂ Edit** on any completed download. Drag the start and end markers over the waveform, apply fade or gain, and click **Export Audio**.
- **Header**: Change language instantly with the top-right toggle (`🇻🇳 Tiếng Việt` / `🇬🇧 English`).

### Command Line Interface (CLI)
Pass one or more video URLs to download immediately in headless mode:

```bash
# Download video as 320kbps MP3 into default Music directory:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Batch download multiple links:
./target/release/media-to-mp3 "https://youtu.be/LINK1" "https://youtu.be/LINK2"

# Specify format (mp3, m4a, wav, flac) and bitrate (128, 192, 320):
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -f flac
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -b 192

# Custom destination folder:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -o "D:/Music"

# Run automated offline self-check (FFmpeg codecs, filters, audio cutter):
./target/release/media-to-mp3 --check

# Background clipboard monitor mode:
./target/release/media-to-mp3 --monitor
```

---

## 🧪 Testing

Run the comprehensive test suite (23 automated unit and integration tests covering audio processing, configuration persistence, download queues, and title cleansing):

```bash
cargo test
```

---

## 📁 Repository Structure

```
media-to-mp3/
├── Cargo.toml            # Rust package dependencies and build profiles
├── Cargo.lock            # Exact reproducible dependency tree
├── run.bat               # Windows instant launcher & auto-builder
├── run.sh                # Linux / macOS launcher script
├── src/                  # Pure Rust codebase
│   ├── main.rs           # Application entry point (GUI dispatcher & CLI)
│   ├── lib.rs            # Core library root
│   ├── gui.rs            # Native eframe/egui GUI with audio waveform canvas
│   ├── audio.rs          # FFmpeg audio pipeline (cut, join, filters, peaks)
│   ├── downloader.rs     # yt-dlp wrapper, stream extraction & metadata cleaner
│   ├── queue.rs          # Thread-safe download queue manager
│   ├── clipboard.rs      # Cross-platform clipboard listener
│   ├── config.rs         # Safe atomic JSON configuration storage
│   ├── i18n.rs           # Bilingual translation loader (embedded JSON)
│   ├── platform.rs       # Native OS shell explorer & audio playback
│   ├── selftest.rs       # Comprehensive offline self-diagnostic engine
│   ├── version.rs        # Application version definition
│   └── strings.json      # English & Vietnamese translation strings
├── tests/
│   └── test_rust_suite.rs # Integration and regression tests
├── LICENSE               # MIT License
└── README.md             # Project documentation
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
