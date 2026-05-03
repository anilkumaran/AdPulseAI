#!/usr/bin/env bash
#
# EC2 bootstrap: OS packages, repo clone, then ./run.sh (venv + pip live in run.sh).
#
# Requires .env in the repo root — if missing, fix and re-run.
#
# Env overrides: SKIP_APT=1  HOST=0.0.0.0  WORKERS=2  INSTALL_DEPS=1

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/anilkumaran/AdPulseAI.git}"
APP_DIR="${APP_DIR:-AdPulseAI}"

sudo apt update -qq
sudo apt install -y git python3 python3-pip python3-venv

if [[ -f run.sh ]]; then
  :
elif [[ -f "$APP_DIR/run.sh" ]]; then
  cd "$APP_DIR"
else
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

if [[ ! -f .env ]]; then
  echo "No .env in $(pwd). Copy it here (example: scp .env user@this-host:$(pwd)/.env), then run this script again." >&2
  exit 1
fi

chmod +x run.sh 2>/dev/null || true

export HOST="${HOST:-0.0.0.0}"
export ENV_MODE="${ENV_MODE:-prod}"
export UVICORN_RELOAD="${UVICORN_RELOAD:-0}"
export WORKERS="${WORKERS:-1}"

echo "Starting via ./run.sh from $(pwd)"
exec ./run.sh
