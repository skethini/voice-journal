#!/usr/bin/env bash
# Optional Render "Start Command" if not using Docker (Python runtime).
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/server"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --app-dir server
