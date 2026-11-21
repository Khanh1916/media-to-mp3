# GitHub Copilot Instructions for media-to-mp3

This repository is **Media to MP3**, a high-performance native desktop tool and CLI utility built in **pure Rust** for downloading and editing audio from YouTube and Facebook.

## Tech Stack
- **Rust 2021 Edition** (MSRV 1.80+)
- **GUI**: `eframe` / `egui 0.29`
- **File Dialogs**: `rfd 0.15`
- **CLI Parser**: `clap 4.5` (derive)
- **External CLI Tools**: `ffmpeg`, `yt-dlp`

## Core Architecture
- `src/main.rs`: CLI parser and entry point. Automatically switches between GUI mode and headless CLI mode based on arguments.
- `src/gui.rs`: Native desktop GUI with Obsidian/Slate dark theme, multi-tab routing, interactive draggable waveform canvas, and status bar.
- `src/audio.rs`: FFmpeg execution pipeline for audio cutting, joining, waveform peak extraction, and filter chains (`afade`, `volume`, `loudnorm`).
- `src/downloader.rs`: yt-dlp execution pipeline, metadata cleansing with regexes, cover art embedding.
- `src/queue.rs`: Thread-safe multi-status download queue with cancellation and progress reporting.
- `src/clipboard.rs`: Cross-platform clipboard polling thread for YouTube and Facebook links.
- `src/config.rs`: Atomic JSON configuration storage in standard OS directories.
- `src/i18n.rs`: Bilingual translation engine (English and Vietnamese).

## Development Rules
- Use `cargo test` to verify changes.
- Ensure `cargo clippy -- -D warnings` and `cargo fmt -- --check` pass without any warnings or diffs.
- Avoid `.unwrap()` in production library code. Always handle errors gracefully.
- Do NOT add Python dependencies or scripts back into the project.
- Respect the existing Slate/Obsidian UI aesthetic and avoid flashy AI-style designs.
