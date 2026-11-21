# Contributing to Media to MP3

First off, thank you for considering contributing to **Media to MP3**! Projects like this thrive thanks to community involvement.

---

## 🧭 Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## 🛠️ Development Setup

### 1. Prerequisites
- **Rust Toolchain**: Install via [rustup](https://rustup.rs/) (Rust 1.80+).
- **FFmpeg & yt-dlp**: Ensure `ffmpeg` and `yt-dlp` are installed and accessible in your system `PATH`.
- **System Libraries (Linux only)**:
  ```bash
  sudo apt-get install -y libasound2-dev libxcb-render0-dev libxcb-shape0-dev libxcb-xfixes0-dev
  ```

### 2. Fork & Clone
```bash
git clone https://github.com/your-username/media-to-mp3.git
cd media-to-mp3
```

---

## 🧪 Testing & Quality Standards

Before submitting any code, verify that all quality checks pass cleanly:

1. **Format Check**:
   ```bash
   cargo fmt -- --check
   ```
   *(Run `cargo fmt` to auto-format)*

2. **Linter Check (Zero Warnings)**:
   ```bash
   cargo clippy -- -D warnings
   ```

3. **Run Test Suite**:
   ```bash
   cargo test
   ```

4. **Self-Check Diagnostic**:
   ```bash
   cargo run -- --check
   ```

---

## 🌿 Git & Pull Request Workflow

1. **Create a topic branch**:
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Commit Conventions**:
   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add opus format export option`
   - `fix: resolve race condition in queue status callback`
   - `docs: update AGENTS.md with new module layout`
   - `style: format with rustfmt`
   - `refactor: optimize waveform peak calculation`

3. **Push & Open a Pull Request**:
   Push your branch and submit a PR to `main` using the provided Pull Request template.

---

## AI Agent Guidelines

If you are using autonomous AI coding tools (Claude Code, Antigravity, OpenAI Codex, Cursor, Copilot, etc.), refer to:
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [.cursorrules](.cursorrules)
- [.github/copilot-instructions.md](.github/copilot-instructions.md)
