# AGENTS.md — Universal Agent Instructions & Developer Guide

Welcome, autonomous agent! This document is the unified guide for AI coding agents (including Anthropic Claude Code, OpenAI Codex, Google Antigravity / Gemini CLI, Cursor, and GitHub Copilot) working in this repository.

---

## 1. Project Overview

**Media to MP3** is a high-performance, lightweight, pure **Rust** desktop application and CLI tool that downloads video audio from YouTube and Facebook as MP3 (up to 320 kbps), M4A, WAV, or FLAC, with an integrated interactive audio editor (cut & join).

- **Language & Edition**: Rust 2021 (MSRV: 1.80+)
- **GUI Framework**: `eframe` / `egui 0.29` (Immediate mode GUI with hardware-accelerated rendering)
- **External CLI Engines**: `ffmpeg` (audio decoding, filtering, encoding, waveform analysis) and `yt-dlp` (metadata and stream extraction)
- **Binary Size**: ~7.6 MB release binary (optimized with LTO & strip)
- **Zero Python Runtime**: All legacy Python code has been completely replaced with native Rust.

---

## 2. Repository Layout & Architecture

```
media-to-mp3/
├── Cargo.toml            # Rust manifest, dependencies, optimized release profiles
├── rustfmt.toml          # Code formatting rules
├── clippy.toml           # Linter configuration (MSRV 1.80.0)
├── AGENTS.md             # Universal AI Agent Specification
├── CLAUDE.md             # Claude Code development guidelines
├── .cursorrules          # Cursor AI IDE rules
├── run.bat               # Windows launcher & auto-builder
├── run.sh                # Linux / macOS launcher script
├── src/
│   ├── main.rs           # Entry point: CLI dispatching & GUI bootstrap
│   ├── lib.rs            # Library root exporting all submodules
│   ├── gui.rs            # Native eframe/egui GUI & interactive waveform canvas
│   ├── audio.rs          # FFmpeg engine: probe, load_peaks, export, filters
│   ├── downloader.rs     # yt-dlp wrapper & title cleansing / regex parser
│   ├── queue.rs          # Thread-safe download queue (Arc<Mutex<...>>)
│   ├── clipboard.rs      # Cross-platform clipboard listener thread
│   ├── config.rs         # Safe atomic JSON settings storage
│   ├── i18n.rs           # Bilingual translation engine (VI/EN)
│   ├── platform.rs       # Native OS file reveal & audio playback
│   ├── selftest.rs       # Offline self-diagnostic suite
│   ├── version.rs        # Semantic version definition
│   └── strings.json      # Embedded bilingual dictionary
├── tests/
│   └── test_rust_suite.rs # Integration & regression test suite
└── .github/              # CI/CD workflows, issue & PR templates
```

### Module Responsibilities
- **`src/main.rs`**: Evaluates CLI arguments. If URLs or flags like `--check`, `--monitor`, `--cli` are supplied, it runs in headless CLI mode; otherwise, it boots `gui::run_gui()`.
- **`src/gui.rs`**: Implements `eframe::App`. Features an Obsidian/Slate dark palette (`#0f1117`, `#181c26`), custom tab routing (Download Queue vs Audio Editor), interactive draggable waveform markers, and native file dialogs via `rfd`.
- **`src/audio.rs`**: Executes FFmpeg commands. Extracts audio peaks as raw PCM s16le for waveform rendering, manages audio cutting/joining, applies `afade`, `volume`, and EBU R128 `loudnorm` filters.
- **`src/downloader.rs`**: Cleanses noisy titles into clean `Artist – Title` tags, resolves streams via `yt-dlp`, embeds high-resolution cover art, and writes ID3v2.3 tags.
- **`src/queue.rs`**: Manages background download concurrency, progress tracking, status transitions (`pending` -> `downloading` -> `converting` -> `done`/`error`/`cancelled`), retry, and cancellation.

---

## 3. Essential Commands

### Build & Check
```bash
# Check syntax and types rapidly
cargo check

# Run all unit and integration tests
cargo test

# Run linter (must pass with 0 warnings)
cargo clippy -- -D warnings

# Check code formatting
cargo fmt -- --check

# Format code automatically
cargo fmt

# Compile optimized release binary
cargo build --release
```

### Running the Application
```bash
# Launch native GUI
cargo run --release

# Run offline diagnostic self-check
cargo run -- --check

# Download directly via CLI
cargo run -- "https://www.youtube.com/watch?v=..." -f mp3 -b 320
```

---

## 4. Coding Conventions & Quality Guidelines

When contributing code, you MUST adhere to the following principles:

1. **Idiomatic Rust**:
   - Prefer `Result<T, E>` and `Option<T>` over panics.
   - Do NOT use `.unwrap()` or `.expect()` in library routines (`audio.rs`, `downloader.rs`, `queue.rs`, `config.rs`). Use proper `?` propagation or map errors into clear user-facing messages.
   - Follow standard Rust naming conventions (`snake_case` for functions/variables, `PascalCase` for structs/enums).

2. **Concurrency & Thread Safety**:
   - The queue and downloader operate across background threads.
   - Always minimize mutex lock durations. Do NOT perform blocking network calls, FFmpeg commands, or file I/O while holding a mutex lock guard.
   - Use `std::sync::atomic` types (`AtomicBool`, `AtomicUsize`) for simple state flags.

3. **User Interface (GUI) Guidelines**:
   - Respect the established design language: professional Obsidian/Slate theme (`#0f1117`, `#181c26`), subtle Indigo accents (`#6366f1`), high contrast text.
   - Do NOT introduce generic, tacky AI aesthetics (e.g., loud neon glow, rainbow gradients, non-standard bloated animations).
   - Use native file dialogs (`rfd`) for opening and saving files.
   - Ensure all UI strings are localized through `crate::i18n::t("key", &[...])`.

4. **Testing Requirements**:
   - Every new feature or bug fix must include corresponding unit tests in the module or integration tests in `tests/test_rust_suite.rs`.
   - Tests must run offline without requiring external network connections.

---

## 5. Adding New Capabilities

### Adding a new UI Language
1. Add new language keys and translations in `src/strings.json`.
2. Update the language selector in `src/gui.rs`.
3. Verify with `cargo test`.

### Adding a new Audio Format
1. Update format options in `src/downloader.rs` and `src/audio.rs`.
2. Add the corresponding format pill in `src/gui.rs`.
3. Add format test cases to `tests/test_rust_suite.rs`.
