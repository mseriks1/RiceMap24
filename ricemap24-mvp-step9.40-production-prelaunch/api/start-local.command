#!/bin/bash
set -e
cd "$(dirname "$0")"
export RICEMAP_ENV="${RICEMAP_ENV:-development}"
export RICEMAP_DATA_DIR="${RICEMAP_DATA_DIR:-$HOME/RiceMap24-data}"
export PORT="${PORT:-8091}"
mkdir -p "$RICEMAP_DATA_DIR/uploads" "$RICEMAP_DATA_DIR/backups"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port "$PORT"
