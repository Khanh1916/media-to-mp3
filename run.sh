#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$SCRIPT_DIR/target/release/media-to-mp3"

if [ ! -f "$BIN" ]; then
    echo "[media-to-mp3] Building release binary..."
    (cd "$SCRIPT_DIR" && cargo build --release)
fi

exec "$BIN" "$@"
