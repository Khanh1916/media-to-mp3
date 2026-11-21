# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-21

### Changed (Complete Architecture Rewrite)
- **100% Pure Rust Rewrite**: Completely replaced the legacy Python engine, Tkinter GUI, and PyInstaller build pipeline with a native Rust application.
- **Binary Footprint**: Reduced packaged application size from ~45 MB to ~7.6 MB.
- **Instant Launch**: Eliminated Python interpreter and virtualenv startup latency (< 0.2s launch).
- **Modern Native GUI**: Re-engineered desktop GUI in `eframe` / `egui 0.29` with Obsidian/Slate dark palette (`#0f1117`, `#181c26`), Indigo accents (`#6366f1`), and an interactive draggable waveform canvas.
- **Native OS Dialogs**: Replaced custom file dialogs with native system pickers via `rfd`.

### Added
- **Multi-Platform AI Agent Ecosystem**: Added `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`, and `.gemini/GEMINI.md`.
- **Professional GitHub Infrastructure**: Added automated multi-platform CI/CD (`.github/workflows/ci.yml`, `release.yml`), Issue & PR templates, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`.
- **Audio Processing Pipeline**: Direct FFmpeg stream extraction, loudnorm EBU R128 normalization, volume gain, fade in/out, and raw PCM waveform peaks.
- **Automated Test Suite**: Added 23 comprehensive unit and integration tests (`tests/test_rust_suite.rs`).
- **Headless CLI & Self-Test**: Added comprehensive CLI commands and an automated offline diagnostic engine (`--check`).

---

## [0.9.0] - Legacy Python Version
- Initial Python/CustomTkinter implementation with yt-dlp and PyInstaller packaging.
