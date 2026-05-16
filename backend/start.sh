#!/usr/bin/env bash
# Backend dev server startup for Replit.
# Uses python3 -m uvicorn so the uvicorn entry point works even when
# packages were installed via --target (no bin/ symlinks created).

set -e

SITE="/home/runner/workspace/.pythonlibs/lib/python3.12/site-packages"
export PYTHONPATH="${SITE}:${PYTHONPATH}"

echo "[backend] PYTHONPATH includes site-packages"
echo "[backend] Starting uvicorn on 0.0.0.0:8000"

exec python3 -m uvicorn server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir .
