#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[setup] Creating virtual environment in .venv"
  python3 -m venv .venv
else
  echo "[setup] Virtual environment already exists at .venv"
fi

./.venv/bin/python -m pip install --upgrade pip
# --upgrade: luôn kéo yt-dlp mới nhất, bản cũ hay bị YouTube bóp tốc độ / lỗi 403
./.venv/bin/python -m pip install --upgrade -r requirements.txt

echo "[setup] Done. Run app with: ./run.sh"
