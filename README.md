# 🎵 Media to MP3 Downloader (YouTube & Facebook)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

[English](README.md) | [Tiếng Việt](README_VI.md)

A desktop tool and CLI utility that downloads videos from **YouTube** and **Facebook** as **MP3 (up to 320 kbps), M4A, WAV or FLAC** audio, with a built-in **cut & join** music editor. Runs on **Windows** and **Linux**, with an **English / Vietnamese** interface.

Author: **KhanhNN (a.k.a Cao Thanh Lam)**

---

## ✨ Key Features

- 📋 **Smart Clipboard Auto-detection**: Copy (`Ctrl+C`) a YouTube or Facebook video link and the app asks whether to add it to the download queue.
- 📥 **Download Queue**: Paste one or many links at once; they download one after another, each with its own progress and cancel / retry / remove buttons.
- 🔊 **Stereo-friendly Formats**: Everything is exported at **44.1 kHz / 16-bit** (CD standard):
  | Format | Notes |
  |---|---|
  | **MP3** (320 / 192 / 128 kbps) | Plays on every speaker, stereo, car head unit and phone. ID3v2.3 tags so older units still show track names. |
  | **M4A (AAC)** | Keeps YouTube's original AAC audio, no re-encoding. Plays well on modern car units, phones and Bluetooth speakers. |
  | **WAV** | Readable by almost any stereo, but large (~10 MB/min) and no cover art. |
  | **FLAC** | Lossless. Usually supported by newer car units and speakers. |
  
  Opus / OGG are left out because many hardware players can't read them.
- 🖼️ **Automatic Cover Art & Tags**: Embeds a square 600×600 JPEG cover and detects **Artist – Title** from the video title (dropping parts such as `(Official Video)` or `| OFFICIAL MV`). Both can be turned off in the settings.
- ✂️ **Cut & Join Music**:
  - Add several audio files (or click *Edit* on a finished download) and order them for joining.
  - Drag on the **waveform** to pick the part to keep, or type exact times (e.g. `1:23.5`).
  - **Preview** the selection right inside the app.
  - Effects: **fade in / fade out**, **crossfade** between clips, **volume**, **loudness normalization** (loudnorm).
  - Edit title / artist, keep the cover art, export to MP3 / M4A / WAV / FLAC.
- 💾 **Remembered Settings**: Output folder, format, quality, language, window size... are kept for next time.
- 🌐 **English / Vietnamese UI**: Switch language from the window header, no restart needed.
- 🐧 **Cross-Platform**: Windows 10/11 and Linux (Ubuntu, Debian, Fedora, Arch, etc.). No manual FFmpeg install: a static FFmpeg binary ships with `imageio-ffmpeg`.
- 💻 **Dual Mode**: Dark-themed GUI, plus a CLI for terminals and headless servers.

---

## 📥 Download & Run (no Python needed)

Get the latest build from **[Releases](https://github.com/Khanh1916/media-to-mp3/releases/latest)**: a single file (~22–25 MB) with FFmpeg built in.

| OS | File | How to run |
|---|---|---|
| Windows 10 / 11 (64-bit) | `MediaToMP3-x.y.z-windows-x64.exe` | Open it. If Windows shows *"Windows protected your PC"* (the app is not code-signed), click **More info → Run anyway**. |
| Linux 64-bit (Ubuntu 22.04+, Debian 12+, Fedora 36+...) | `MediaToMP3-x.y.z-linux-x64.tar.gz` | Extract it and run `./MediaToMP3`. |

Run `MediaToMP3 --check` for an offline self-check of conversion, cover art and cut & join.
To run from source instead, follow the steps below.

---

## 🚀 Installation & Setup

### 1. Prerequisites
- **Python 3.10+** installed on your system.

### 2. Python Environment Setup (Recommended for Linux/macOS)
On Ubuntu/Debian, installing packages via pip system-wide often triggers `externally-managed-environment` errors. The safest approach is using a virtual environment `.venv`:

```bash
cd ~/media-to-mp3
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Alternatively, use the pre-configured helper scripts:

```bash
cd ~/media-to-mp3
./setup_venv.sh
./run.sh
```

`setup_venv.sh` creates `.venv` if it doesn't exist and installs all dependencies. `run.sh` executes the application using the Python interpreter inside `.venv` without needing to activate it manually.

> **Note for Linux Users**:
> If you are on Ubuntu/Debian and encounter missing Tkinter or clipboard errors, install system dependencies:
> ```bash
> sudo apt update
> sudo apt install python3-tk xclip ffmpeg -y
> ```
> The *Play selection* button uses `paplay` / `pw-play` / `aplay` (available on Ubuntu desktop).

> **Run directly without activating virtualenv**:
> ```bash
> cd ~/media-to-mp3
> .venv/bin/python main.py
> ```

---

## 🎯 How to Run

### Method 1: Graphical User Interface (GUI)
With the virtual environment activated:
```bash
python main.py
```
Or run the launcher script directly:
```bash
./run.sh
```

**⬇ Download tab**
1. Copy a YouTube / Facebook video URL in your browser: the app catches it and asks whether to queue it.
2. Or paste one or more links into the input and click **➕ Add to queue**.
3. Pick the format, quality and output folder. Finished items get *Folder*, *Play* and *Edit* buttons.

**✂ Cut & Join tab**
1. Click **➕ Add audio files...** (or *Edit* in the download queue).
2. Select each clip in the list and drag on the waveform to choose the part to keep. Use ▲ ▼ to change the join order.
3. Add effects if you like, edit title / artist, then click **💾 Export...**.

Switch **Tiếng Việt / English** in the top-right corner.

### Method 2: Command Line Interface (CLI)
Perfect for terminal enthusiasts or headless servers:
```bash
# Download as 320kbps MP3 into the default Music folder:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
# Or on Windows:
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Download several links in a row:
./run.sh "https://youtu.be/LINK1" "https://youtu.be/LINK2"

# Choose the format (mp3, m4a, wav, flac) and MP3 quality (128, 192, 320):
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -f flac
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -b 192

# Specify custom output directory:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o "D:/MyMusic"

# Self-check FFmpeg and the features (no network needed):
./run.sh --check

# No cover art / no Artist – Title detection / English output:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --no-thumbnail --no-tags --lang en
```

### Where settings are stored
- **Windows**: `%APPDATA%\MediaToMP3\settings.json`
- **Linux**: `~/.config/media-to-mp3/settings.json`
- **macOS**: `~/Library/Application Support/MediaToMP3/settings.json`

Delete this file to go back to the defaults.

---

## 🛠️ Troubleshooting Slow Downloads / 403 Errors (especially on Linux)

YouTube changes frequently, so an outdated yt-dlp or a missing JavaScript runtime leads to very slow downloads, long hangs, or `HTTP Error 403`.

1. **Update yt-dlp** (re-run whenever downloads become slow or fail):
   ```bash
   ./setup_venv.sh
   ```
2. **Install a JavaScript runtime** (yt-dlp uses it to solve YouTube's signature challenges). [Deno](https://deno.com) is recommended:
   ```bash
   curl -fsSL https://deno.land/install.sh | sh
   ```
   The app also uses `node` (>= 20), `bun` or `quickjs` if available.
3. **Check the warnings**: run the app from a terminal (`./run.sh`); `[WARNING]` lines show the cause (missing JS runtime, network retries, ...).

---

## 🧪 Running the Tests

The test suite uses Python's built-in `unittest` (FFmpeg is needed for the cut / join tests; no network access required):

```bash
python -m unittest discover -s tests -t .
```

---

## 📦 Packaging & Releases

### Build locally
```bash
# 1. (Recommended) Build a minimal ~5 MB FFmpeg instead of the full ~80 MB one (on Linux / WSL / Docker):
bash packaging/build_ffmpeg.sh windows out-ffmpeg      # or: linux

# 2. Package everything into a single executable:
python build_exe.py --ffmpeg out-ffmpeg/ffmpeg.exe --release
```
- Output: `dist/MediaToMP3.exe` (Windows) or `dist/MediaToMP3` (Linux). `--release` also writes a versioned file to `dist/release/`.
- Without `--ffmpeg`, the full FFmpeg from `imageio-ffmpeg` is bundled (~30 MB larger).
- `build_ffmpeg.sh` needs `build-essential nasm pkg-config curl xz-utils`, plus `gcc-mingw-w64-x86-64 binutils-mingw-w64-x86-64 mingw-w64-x86-64-dev` for Windows builds.

### Publishing a release (built by GitHub Actions)
1. Bump the version in `version.py` and merge into `main`.
2. Push a matching tag:
   ```bash
   git tag v1.0.0 && git push origin v1.0.0
   ```
3. The **Build & Release** workflow builds the minimal FFmpeg, packages Windows + Linux, runs `--check` on the packaged files, then creates the Release with the downloads and `SHA256SUMS.txt`.

Every pull request is built and self-checked the same way (without publishing).

---

## 📁 Project Structure

```
media-to-mp3/
├── main.py              # Main entry point (supports both GUI and CLI)
├── app_ui.py            # Main window: header, language switch, 2 tabs (CustomTkinter)
├── ui_download.py       # Download tab: link input, formats, queue
├── ui_editor.py         # Cut & Join tab: clip list, waveform, effects, export
├── downloader.py        # Core download & audio conversion (yt-dlp + FFmpeg), Artist – Title detection
├── download_queue.py    # Background queue that downloads items one by one
├── audio_tools.py       # Cut / join / effects / waveform / preview with FFmpeg
├── clipboard_monitor.py # Background thread for auto-detecting YouTube & Facebook links
├── config.py            # Save / load user settings (JSON)
├── i18n.py              # English / Vietnamese UI strings
├── platform_utils.py    # Open folders / play files per operating system
├── selftest.py          # Self-check (--check): FFmpeg, conversion, cover art, cut & join
├── version.py           # Version number
├── tests/               # Test suite (unittest)
├── build_exe.py         # Single-file packaging with PyInstaller
├── packaging/           # Minimal FFmpeg build script, icon, release notes
├── .github/workflows/   # GitHub Actions: build & publish Windows / Linux releases
├── setup_venv.sh        # Helper script to setup Python virtual environment
├── run.sh               # Launcher script to run the app via .venv
├── requirements.txt     # Python package dependencies
├── LICENSE              # MIT License
├── THIRD_PARTY_NOTICES.md # Licenses of bundled components (FFmpeg, yt-dlp...)
├── README.md            # Documentation (English)
└── README_VI.md         # Documentation (Vietnamese)
```
