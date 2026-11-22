# Third-Party Notices

Media to MP3 is built in pure Rust and licensed under the [MIT License](LICENSE).
The binary distributions and runtime depend on or link with the following third-party libraries and tools:

## Rust Crates & Libraries

| Crate | Version | License | Upstream Repository |
|---|---|---|---|
| [eframe](https://crates.io/crates/eframe) / [egui](https://crates.io/crates/egui) | 0.29 | MIT / Apache-2.0 | https://github.com/emilk/egui |
| [rfd](https://crates.io/crates/rfd) | 0.15 | MIT | https://github.com/PolyMeilex/rfd |
| [serde](https://crates.io/crates/serde) / [serde_json](https://crates.io/crates/serde_json) | 1.0 | MIT / Apache-2.0 | https://github.com/serde-rs/serde |
| [regex](https://crates.io/crates/regex) | 1.10 | MIT / Apache-2.0 | https://github.com/rust-lang/regex |
| [clap](https://crates.io/crates/clap) | 4.5 | MIT / Apache-2.0 | https://github.com/clap-rs/clap |
| [dirs](https://crates.io/crates/dirs) | 5.0 | MIT / Apache-2.0 | https://github.com/dirs-dev/dirs-rs |
| [once_cell](https://crates.io/crates/once_cell) | 1.19 | MIT / Apache-2.0 | https://github.com/matklad/once_cell |
| [arboard](https://crates.io/crates/arboard) | 3.4 | MIT / Apache-2.0 | https://github.com/1Password/arboard |
| [indicatif](https://crates.io/crates/indicatif) | 0.17 | MIT | https://github.com/console-rs/indicatif |
| [which](https://crates.io/crates/which) | 7.0 | MIT | https://github.com/harryfei/which-rs |
| [tempfile](https://crates.io/crates/tempfile) | 3.10 | MIT / Apache-2.0 | https://github.com/Stebalien/tempfile |
| [winres](https://crates.io/crates/winres) | 0.1 | MIT | https://github.com/mxre/winres |

## External System Tools

Media to MP3 invokes the following external media utilities for stream extraction and audio encoding:

| Tool | License | Source & Documentation |
|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense / Public Domain | https://github.com/yt-dlp/yt-dlp |
| [FFmpeg](https://ffmpeg.org) | LGPL-2.1-or-later / GPL-2.0-or-later | https://ffmpeg.org |
