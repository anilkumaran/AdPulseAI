#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"
ENV_MODE="${ENV_MODE:-test}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: '$PYTHON_BIN' not found. Set PYTHON_BIN (e.g. PYTHON_BIN=python)." >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtualenv at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Installing dependencies"
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

if [[ ! -f ".env" ]]; then
  if [[ -f ".env.example" ]]; then
    echo "Creating .env from .env.example"
    cp ".env.example" ".env"
  else
    echo "No .env found (and no .env.example). Continuing without it."
  fi
fi

export ENV_MODE

echo "Starting AdPulseAI"
echo "- ENV_MODE=$ENV_MODE"
echo "- HOST=$HOST"
echo "- PORT=$PORT"
echo
echo "Open http://$HOST:$PORT"
echo

exec python -m uvicorn main:app --reload --host "$HOST" --port "$PORT"

