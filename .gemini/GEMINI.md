# Gemini & Antigravity Agent Guide — media-to-mp3

Welcome, Gemini / Antigravity agent! This repository has been completely converted from a legacy Python codebase into a **pure Rust** native application and CLI tool.

## Primary Directives
- **Zero Python**: Never re-introduce Python scripts, virtualenvs, or Python dependencies.
- **Pure Rust Architecture**: The entire core engine, CLI, and GUI are implemented in Rust (`Cargo.toml`, `src/`, `tests/`).
- **Toolchain**: Use the Rust toolchain with Cargo. All code is standard Rust 2021 edition.
- **Verification**: Always run `cargo check`, `cargo test`, `cargo clippy -- -D warnings`, and `cargo fmt -- --check`.

## Module Map
- `src/main.rs`: Application dispatcher (GUI vs CLI).
- `src/gui.rs`: Native desktop GUI (eframe/egui) with dark slate styling and audio waveform editor.
- `src/audio.rs`: FFmpeg process wrapper, waveform peak sampler, cutting, and joining.
- `src/downloader.rs`: yt-dlp wrapper and title/metadata regex cleaner.
- `src/queue.rs`: Background multi-threaded download queue.
- `src/clipboard.rs`: Smart clipboard auto-detection thread.
- `src/config.rs`: Safe atomic settings storage.
- `src/i18n.rs`: English / Vietnamese localization loader.
- `src/platform.rs`: Cross-platform OS explorer integration and preview playback.
- `src/selftest.rs`: Offline self-diagnostic suite.
