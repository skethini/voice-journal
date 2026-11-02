#!/usr/bin/env bash
# Optional Render "Build Command" if not using Docker (Python runtime).
set -euo pipefail
pip install -r requirements-cloud.txt
cd client && npm ci && VITE_API_BASE= npm run build
