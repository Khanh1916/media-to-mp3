# Third-Party Notices

The standalone builds of Media to MP3 (GitHub Releases) bundle the following components.
Media to MP3 itself is licensed under the [MIT License](LICENSE).

| Component | License | Source |
|---|---|---|
| [FFmpeg](https://ffmpeg.org) 8.1.3 (minimal build, separate `ffmpeg` executable) | LGPL-2.1-or-later | https://ffmpeg.org/releases/ffmpeg-8.1.3.tar.xz |
| [LAME](https://lame.sourceforge.io) 3.100 (MP3 encoder, linked into FFmpeg) | LGPL-2.0-or-later | https://downloads.sourceforge.net/project/lame/lame/3.100/lame-3.100.tar.gz |
| [zlib](https://zlib.net) 1.3.1 (linked into FFmpeg) | zlib License | https://github.com/madler/zlib |
| [Python](https://www.python.org) runtime | PSF License | https://github.com/python/cpython |
| Tcl/Tk | Tcl/Tk License (BSD-style) | https://www.tcl.tk |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp), [yt-dlp-ejs](https://github.com/yt-dlp/ejs) | Unlicense | https://github.com/yt-dlp |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | MIT | https://github.com/TomSchimansky/CustomTkinter |
| [pyperclip](https://github.com/asweigart/pyperclip) | BSD-3-Clause | https://github.com/asweigart/pyperclip |
| [mutagen](https://github.com/quodlibet/mutagen) | GPL-2.0-or-later | https://github.com/quodlibet/mutagen |
| [requests](https://github.com/psf/requests) | Apache-2.0 | https://github.com/psf/requests |
| [urllib3](https://github.com/urllib3/urllib3) | MIT | https://github.com/urllib3/urllib3 |
| [certifi](https://github.com/certifi/python-certifi) | MPL-2.0 | https://github.com/certifi/python-certifi |
| [Brotli](https://github.com/google/brotli) | MIT | https://github.com/google/brotli |
| [websockets](https://github.com/python-websockets/websockets) | BSD-3-Clause | https://github.com/python-websockets/websockets |
| [PyCryptodome](https://github.com/Legrandin/pycryptodome) (pycryptodomex) | BSD-2-Clause / Public Domain | https://github.com/Legrandin/pycryptodome |
| [PyInstaller](https://pyinstaller.org) bootloader | GPL-2.0 with bootloader exception | https://github.com/pyinstaller/pyinstaller |

The bundled FFmpeg is built from the unmodified sources above by
[`packaging/build_ffmpeg.sh`](packaging/build_ffmpeg.sh), which lists every configure option used.
It runs as a separate program, and the script lets anyone rebuild or modify it from source.
