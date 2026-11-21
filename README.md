# Media to MP3 Downloader

[![CI](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml/badge.svg)](https://github.com/Khanh1916/media-to-mp3/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Khanh1916/media-to-mp3)](https://github.com/Khanh1916/media-to-mp3/releases)
[![Rust](https://img.shields.io/badge/Rust-1.80%2B-orange.svg)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

[English](README.md) | [Tiếng Việt](README_VI.md)

A high-performance, standalone desktop application and command-line utility built in pure Rust. Media to MP3 downloads video streams from YouTube and Facebook as high-fidelity audio (MP3, M4A, FLAC, WAV) and provides an integrated waveform audio editor for trimming, concatenating, and normalizing audio tracks.

Engineered with eframe and egui, the application compiles into a single, compact binary (~7.6 MB) with instant launch, minimal memory usage (<30 MB RAM), and zero external runtime dependencies.

Author: **KhanhNN (Cao Thanh Lam)**

---

## Features

- **Pure Native Rust**: Compiled directly to machine code with link-time optimization (LTO) and binary stripping. Zero Python runtime or virtual environment required.
- **Utilitarian Desktop GUI**: Built using an immediate-mode architecture with an Obsidian and Slate dark palette. Provides high-contrast typography, responsive layout, and native system dialogs via `rfd`.
- **Integrated Waveform Editor**: Visualizes audio amplitude using downsampled PCM data. Supports interactive draggable start and end markers, sub-second precision inputs, fade in/out curves, volume gain, and EBU R128 loudness normalization.
- **Automated Clipboard Listener**: Monitors the system clipboard in a background thread to detect YouTube and Facebook URLs, allowing one-click addition to the download queue.
- **Thread-Safe Download Queue**: Asynchronous processing queue with individual progress tracking, speed estimation, cancellation, and retry handling.
- **Metadata and Cover Art Pipeline**: Cleanses noisy video titles (removing bracketed descriptors such as official video, lyric video, remastered) into structured Artist and Title metadata, embedding square JPEG artwork and ID3v2.3 tags.
- **Bilingual Interface**: Instant switching between English and Vietnamese without restarting the application.
- **Dual Operating Modes**: Full desktop GUI by default, or headless CLI for terminal environments and automated scripts.

---

## Supported Audio Formats

All exported audio is standardized to 44.1 kHz, 16-bit stereo (CD standard) for universal hardware compatibility:

| Format | Bitrate / Mode | Typical Target | Compatibility Notes |
|---|---|---|---|
| MP3 | 320 / 192 / 128 kbps | Car stereos, legacy players, mobile | Universal ID3v2.3 support; compatible with older automotive head units. |
| M4A (AAC) | Source passthrough / AAC | Modern smartphones, Apple devices | Preserves source AAC streams without re-encoding quality loss. |
| WAV | 1411 kbps uncompressed | Audio hardware, DAWs, legacy decks | Raw PCM audio. Universal decoding; does not support embedded cover art. |
| FLAC | Bit-perfect lossless | Audiophile setups, modern receivers | Free Lossless Audio Codec; full tag and metadata retention. |

---

## Prerequisites

- **FFmpeg**: Required for audio stream extraction, filtering, and format encoding. Must be available in system `PATH` or the working directory.
- **yt-dlp**: Required for extracting media streams and metadata from supported platforms. Must be in system `PATH` or the working directory.
- **Rust Toolchain** (1.80+): Only required when building from source code.

---

## Installation & Build

### From Source

```bash
# Clone the repository
git clone https://github.com/Khanh1916/media-to-mp3.git
cd media-to-mp3

# Build optimized production binary
cargo build --release

# Run GUI
cargo run --release
```

### Quick Launch Scripts

- **Windows**: Run `run.bat` (automatically builds release binary if missing and launches the GUI).
- **Linux / macOS**:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

---

## Usage

### Graphical Interface

Launch `media-to-mp3` without arguments to open the desktop application:

1. **Download Queue Tab**:
   - Paste one or more video URLs into the input field.
   - Select your target format pill (MP3 320k, 192k, 128k, M4A, FLAC, WAV).
   - Click **Add to Queue**. Completed items display action buttons to open the enclosing directory, play the track in the default OS player, or send the file directly to the Audio Editor.

2. **Audio Editor Tab**:
   - Click **Open Audio File** or transfer a file from the download queue.
   - Drag the start and end markers on the interactive waveform canvas to designate the active region.
   - Configure optional processing: Fade In (seconds), Fade Out (seconds), Volume Gain (dB), and Loudness Normalization.
   - Click **Export Audio** to choose the output destination.

3. **Status Bar & Header**:
   - Live indicators display the status of the local FFmpeg binary and background clipboard listener.
   - Click the language selector in the upper right header to switch between English and Vietnamese.

### Command-Line Interface

Pass target URLs directly to the binary for headless batch processing:

```bash
# Download a track as 320 kbps MP3 into default Music directory:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Batch download multiple links sequentially:
./target/release/media-to-mp3 "https://youtu.be/LINK1" "https://youtu.be/LINK2"

# Specify audio format and bitrate:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -f flac
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -b 192

# Specify custom destination directory:
./target/release/media-to-mp3 "https://www.youtube.com/watch?v=..." -o "D:/Music"

# Run offline self-diagnostic suite (verifies FFmpeg codecs and audio filters):
./target/release/media-to-mp3 --check

# Run headless background clipboard listener:
./target/release/media-to-mp3 --monitor
```

---

## Automated Verification

The test suite consists of 23 automated unit and integration tests covering audio concatenation, timecode parsing, configuration lifecycle, download queue synchronization, and title parsing:

```bash
# Run full unit and integration test suite
cargo test --all-targets

# Run strict linter check
cargo clippy --all-targets -- -D warnings

# Verify source formatting
cargo fmt -- --check
```

---

## Multi-Platform AI Agent Instructions

This repository provides standardized context and instruction files for autonomous coding agents:

- **[AGENTS.md](AGENTS.md)**: Universal agent guide covering architecture, threading discipline, and code style.
- **[.cursorrules](.cursorrules)**: Coding standards for Cursor AI IDE.
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)**: Instructions for GitHub Copilot Workspace.
- **[.gemini/GEMINI.md](.gemini/GEMINI.md)**: Agent instructions for Gemini CLI and Google Antigravity.

---

## Repository Structure

```
media-to-mp3/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # Automated CI for Linux, Windows, and macOS
│   │   └── release.yml          # Automated multi-platform release builder
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── config.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── copilot-instructions.md
│   └── dependabot.yml
├── Cargo.toml                   # Crate manifest and release profile configurations
├── Cargo.lock
├── rustfmt.toml                 # Code formatting rules
├── clippy.toml                  # Linter MSRV settings
├── AGENTS.md                    # Universal AI agent instructions
├── .cursorrules                 # Cursor rules
├── CONTRIBUTING.md              # Contributor guidelines
├── CODE_OF_CONDUCT.md          # Contributor Covenant 2.1
├── SECURITY.md                  # Vulnerability disclosure policy
├── CHANGELOG.md                 # Semantic version history
├── run.bat                      # Windows launcher and auto-builder
├── run.sh                       # Linux and macOS launcher script
├── src/
│   ├── main.rs                  # Application entry point and CLI dispatcher
│   ├── lib.rs                   # Library root
│   ├── gui.rs                   # eframe/egui GUI and waveform painter
│   ├── audio.rs                 # FFmpeg process integration and filter pipeline
│   ├── downloader.rs            # yt-dlp wrapper and title cleansing regexes
│   ├── queue.rs                 # Thread-safe download queue
│   ├── clipboard.rs             # Cross-platform clipboard listener
│   ├── config.rs                # Safe atomic JSON settings persistence
│   ├── i18n.rs                  # Bilingual localization loader
│   ├── platform.rs              # OS file explorer and audio preview integration
│   ├── selftest.rs              # Offline diagnostic test runner
│   ├── version.rs               # Version constant
│   └── strings.json             # English and Vietnamese dictionary
├── tests/
│   └── test_rust_suite.rs        # Integration test suite
├── LICENSE                      # MIT License
├── README.md                    # English documentation
└── README_VI.md                 # Vietnamese documentation
```

---

## License

This project is licensed under the [MIT License](LICENSE).
