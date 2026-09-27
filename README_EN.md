# 🎵 Media to MP3 Downloader (YouTube & Facebook)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/Khanh1916/media-to-mp3)

[English](README_EN.md) | [Tiếng Việt](README.md)

A versatile desktop tool and CLI utility to download and convert videos from **YouTube** and **Facebook** into **high-quality MP3 audio (up to 320 kbps)**. Built for both **Windows** and **Linux**.

Author: **KhanhNN (a.k.a Cao Thanh Lam)**

---

## ✨ Key Features

- 📋 **Smart Clipboard Auto-detection**: Automatically detects YouTube and Facebook video URLs when copied (`Ctrl+C`), pre-fills the input, and prompts you to start downloading.
- ⚡ **Customizable Audio Quality**: Supports 3 bitrate presets:
  - `320 kbps`: Maximum audio quality (HQ Studio / Audiophile).
  - `192 kbps`: Standard bitrate, optimal balance between file size and fidelity.
  - `128 kbps`: Ultra-compact file size.
- 🖼️ **Automatic Metadata & ID3 Tags**: Automatically embeds track metadata (artist, title) into ID3 tags.
- 🎧 **Quick Actions**: Convenient buttons once downloading finishes:
  - *Open Folder*: Reveal the downloaded file in File Explorer / File Manager.
  - *Play*: Instantly play the MP3 in your system's default media player.
- 🐧 **Cross-Platform**:
  - Works out of the box on **Windows 10/11** and **Linux** distributions (Ubuntu, Debian, Fedora, Arch, etc.).
  - No manual FFmpeg installation required: Comes bundled with a static FFmpeg binary via `imageio-ffmpeg`.
- 💻 **Dual Mode Support**:
  - Modern Graphical User Interface (GUI) with dark theme (`app_ui.py`).
  - High-performance Command Line Interface (CLI) for terminal and headless server environments (`python main.py <URL>` or `./run.sh <URL>`).

---

## 🚀 Installation & Setup

### 1. Prerequisites
- **Python 3.8+** installed on your system.

### 2. Python Environment Setup (Recommended for Linux/macOS)
On Ubuntu/Debian, modern system Python often throws an `externally-managed-environment` error when running `pip install` directly. The cleanest and recommended approach is to use a virtual environment (`.venv`):

```bash
cd ~/media-to-mp3
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Alternatively, convenient helper scripts are provided in the repository:

```bash
cd ~/media-to-mp3
./setup_venv.sh
./run.sh
```

`setup_venv.sh` automatically creates `.venv` if it doesn't exist and installs all dependencies. `run.sh` launches the application directly using Python inside `.venv` without requiring manual activation.

> **Note for Linux Users**:
> On Ubuntu/Debian, if Tkinter or clipboard utilities are missing, install them with:
> ```bash
> sudo apt update
> sudo apt install python3-tk xclip ffmpeg -y
> ```

> **Run directly without activating virtualenv**:
> ```bash
> cd ~/media-to-mp3
> .venv/bin/python main.py
> ```

---

## 🎯 How to Run

### Method 1: Graphical User Interface (GUI)
With your virtual environment activated:
```bash
python main.py
```
Or run directly using the provided script (Linux):
```bash
./run.sh
```

A sleek Dark Mode interface will launch:
1. Copy any YouTube or Facebook video link in your web browser.
2. The app detects the clipboard content and prompts to confirm the download.
3. Or manually click **📋 Paste** and hit **⬇️ START DOWNLOADING MP3**.

### Method 2: Command Line Interface (CLI)
Ideal for terminal power users or automated headless servers:
```bash
# Download at default 320 kbps to your system Music folder:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
# Or on Windows:
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Specify custom bitrate (128, 192, or 320 kbps):
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -b 192

# Specify custom output directory:
./run.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o "D:/MyMusic"
```

---

## 📦 Build Executable Binary (.exe / Linux binary)

You can package the application into a standalone executable that runs without Python installed:

```bash
python build_exe.py
```
After building:
- **Windows**: The `.exe` binary will be located at `dist/MediaToMP3/MediaToMP3.exe`.
- **Linux**: The standalone binary will be located at `dist/MediaToMP3/MediaToMP3`.

---

## 📁 Project Structure

```
media-to-mp3/
├── app_ui.py            # User interface built with CustomTkinter
├── downloader.py        # Core download & audio conversion engine (yt-dlp + FFmpeg)
├── clipboard_monitor.py # Background daemon thread for clipboard URL detection
├── main.py              # Application entry point (GUI & CLI dispatcher)
├── build_exe.py         # PyInstaller build & packaging script
├── setup_venv.sh        # Setup script to initialize Python venv and install dependencies
├── run.sh               # Quick run script launching app via .venv
├── requirements.txt     # Python package dependencies
├── LICENSE              # MIT License
├── README.md            # Documentation in Vietnamese
└── README_EN.md         # Documentation in English
```
