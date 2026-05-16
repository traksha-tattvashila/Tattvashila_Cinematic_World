#!/usr/bin/env bash
# Frontend dev server startup for Replit.
# Dynamically resolves the backend URL from the Replit dev domain so the
# frontend always points at the correct backend port regardless of session.

set -e

# Build the backend URL from the Replit dev domain (port 8000).
# Pattern: <base>.pike.replit.dev → <base>-8000.pike.replit.dev
if [ -n "$REPLIT_DEV_DOMAIN" ]; then
  BACKEND_DOMAIN="${REPLIT_DEV_DOMAIN/.pike.replit.dev/-8000.pike.replit.dev}"
  export REACT_APP_BACKEND_URL="https://${BACKEND_DOMAIN}"
fi

# Bind to all interfaces so Replit's reverse proxy can reach the dev server.
export HOST=0.0.0.0
export PORT=5000

echo "[frontend] REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}"
echo "[frontend] Starting CRACO on port ${PORT}"

exec npm start
