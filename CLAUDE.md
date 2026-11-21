@AGENTS.md

## Claude Code notes

- Project is written in pure Rust (2021 edition, MSRV 1.80+). Zero Python runtime.
- Shell is PowerShell on Windows 11. Run `cargo test` and `cargo check` before full release builds.
- All code must pass `cargo clippy --all-targets -- -D warnings` and `cargo fmt -- --check`.
- External binaries required at runtime: `ffmpeg` and `yt-dlp`. Tests must run offline without requiring network access.
- Git commits and attribution: never add Claude as git author, committer, or co-author in commit messages or git config. All repository commits belong to the author Khanh1916.
- The user writes in Vietnamese; answer in Vietnamese unless asked otherwise. Follow `C:\Users\Lenovo legion 5\Downloads\skill\my-writing-style\SKILL.md` when drafting user-facing documents.
