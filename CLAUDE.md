# CLAUDE.md — Claude Code Developer Guide

This file provides instructions, commands, and architectural context specifically for Claude Code when working with the `media-to-mp3` repository.

---

## 🛠️ Build, Lint & Test Commands

```bash
# Compilation & Checking
cargo check                       # Quick typecheck without full compilation
cargo build --release             # Compile optimized production release binary

# Quality & Formatting
cargo clippy -- -D warnings       # Strict Clippy lint (zero warnings tolerated)
cargo fmt -- --check              # Verify rustfmt formatting
cargo fmt                         # Auto-format all Rust source files

# Test Execution
cargo test                        # Run all 23 unit & integration tests
cargo test --test test_rust_suite # Run integration test suite specifically

# Runtime Execution
cargo run --release               # Run the native desktop GUI
cargo run -- --check              # Run offline FFmpeg and audio pipeline self-check
cargo run -- --version            # Print application version
```

---

## 🏛️ Architecture Overview

The project is a 100% pure Rust desktop application and CLI tool.

| Module | Location | Purpose |
|---|---|---|
| **Entry Point** | `src/main.rs` | Dispatches CLI commands (with `clap`) or boots the GUI (`eframe::run_native`). |
| **GUI** | `src/gui.rs` | Immediate mode GUI (`eframe`/`egui`), Dark Obsidian theme, custom interactive waveform canvas. |
| **Audio Engine** | `src/audio.rs` | Wraps `ffmpeg` for probe, trim, join, loudness normalization (`loudnorm`), waveform extraction (`s16le`). |
| **Downloader** | `src/downloader.rs` | Wraps `yt-dlp` for video stream extraction, regex title cleaner (`Artist - Track`), cover art embedding. |
| **Queue** | `src/queue.rs` | Thread-safe background download queue with progress callbacks and state transitions. |
| **Clipboard** | `src/clipboard.rs` | Cross-platform clipboard listener polling for YouTube & Facebook links via `arboard`. |
| **Config** | `src/config.rs` | Safe atomic JSON persistence (`settings.json`). |
| **i18n** | `src/i18n.rs` | Bilingual translation loader (Vietnamese / English) embedding `strings.json`. |
| **Platform** | `src/platform.rs` | Native OS file reveal (Explorer/Finder) and default audio player launching. |
| **Self-test** | `src/selftest.rs` | Offline diagnostic test verifying FFmpeg binary, codecs, filters, and audio cutter. |

---

## 🎨 UI & UX Design Rules

- **Theme Palette**: Slate/Obsidian dark (`#0f1117`, `#181c26`, `#1e222e`), Indigo accent (`#6366f1`).
- **No AI Archetypes**: Avoid noisy neon borders, rainbow glow, or cluttered AI templates. Keep controls crisp, utilitarian, and ergonomic.
- **Waveform Canvas**: The audio editor features a custom vector waveform canvas (`egui::Painter`). Draggable markers use mouse drag deltas mapped to timeline seconds.
- **Native Dialogs**: Use `rfd::FileDialog` for selecting directories and audio files.
- **Localization**: Never hardcode user-facing strings in UI code; always look up strings with `t("key", &[("param", val)])`.

---

## 💡 Code Style & Conventions

- **MSRV**: Rust 1.80.0+ (Rust 2021 edition).
- **Error Handling**: Return `Result<T, String>` or custom errors. Never invoke `.unwrap()` in library modules.
- **Locking Discipline**: Acquire `std::sync::Mutex` locks for the shortest necessary duration. Never perform I/O, process spawning, or network calls while holding a lock.
- **Code Formatter**: Ensure `rustfmt` standard formatting is applied before committing.
