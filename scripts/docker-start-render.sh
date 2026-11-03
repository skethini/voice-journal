#!/bin/sh
# Render (and any PaaS) requires binding 0.0.0.0 and the PORT env var.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
