#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[run] .venv not found. Please run: ./setup_venv.sh"
  exit 1
fi

./.venv/bin/python main.py "$@"
