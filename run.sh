#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Pre-built binary in same directory (release archive)
if [ -f "$SCRIPT_DIR/media-to-mp3" ]; then
    exec "$SCRIPT_DIR/media-to-mp3" "$@"
fi

# 2. Development build
BIN="$SCRIPT_DIR/target/release/media-to-mp3"

if [ ! -f "$BIN" ]; then
    echo "[media-to-mp3] Building release binary..."
    (cd "$SCRIPT_DIR" && cargo build --release)
fi

exec "$BIN" "$@"
