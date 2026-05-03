#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
HOST="${HOST:-127.0.0.1}"

# shellcheck disable=SC1091
if [[ -f ".env" ]]; then
  set -a
  source ".env"
  set +a
fi

PORT="${PORT:-8000}"
ENV_MODE="${ENV_MODE:-test}"
INSTALL_DEPS="${INSTALL_DEPS:-0}"

REQ_FILE="api/requirements.txt"
STAMP_FILE="${VENV_DIR}/.requirements.sha256"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: '$PYTHON_BIN' not found. Set PYTHON_BIN (e.g. PYTHON_BIN=python)." >&2
  exit 1
fi

VENV_JUST_CREATED=0
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtualenv at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  VENV_JUST_CREATED=1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

req_hash() {
  if [[ ! -f "$REQ_FILE" ]]; then
    echo ""
    return
  fi
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$REQ_FILE" | awk '{print $1}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "$REQ_FILE" | awk '{print $NF}'
  else
    stat -f "%z-%m" "$REQ_FILE" 2>/dev/null || stat -c "%s-%Y" "$REQ_FILE" 2>/dev/null || echo "unknown"
  fi
}

NEED_INSTALL=0
if [[ "$INSTALL_DEPS" == "1" || "$INSTALL_DEPS" == "true" || "$INSTALL_DEPS" == "yes" ]]; then
  NEED_INSTALL=1
elif [[ "$VENV_JUST_CREATED" -eq 1 ]]; then
  NEED_INSTALL=1
elif [[ -f "$REQ_FILE" ]]; then
  CUR_HASH="$(req_hash)"
  if [[ ! -f "$STAMP_FILE" ]] || [[ "$(cat "$STAMP_FILE" 2>/dev/null || true)" != "$CUR_HASH" ]]; then
    NEED_INSTALL=1
  fi
fi

if [[ "$NEED_INSTALL" -eq 1 ]]; then
  if [[ ! -f "$REQ_FILE" ]]; then
    echo "Warning: $REQ_FILE not found; skipping pip install." >&2
  else
    echo "Installing / updating Python dependencies (requirements changed or first run)…"
    python -m pip install --upgrade pip >/dev/null
    python -m pip install -r "$REQ_FILE"
    req_hash > "$STAMP_FILE"
  fi
else
  echo "Skipping pip install (unchanged). Run INSTALL_DEPS=1 ./run.sh to reinstall."
fi

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

exec python -m uvicorn api.main:app --reload --host "$HOST" --port "$PORT"
