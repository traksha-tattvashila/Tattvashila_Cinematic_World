#!/usr/bin/env bash
# =============================================================================
# Quick environment variable sanity check
#
# Usage:  bash scripts/check-env.sh
#
# Loads backend/.env (if present) and validates all required variables are
# set and non-placeholder. Safe to run at any time — read-only.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"

# Run from within the backend directory so relative imports resolve correctly
cd "$BACKEND_DIR"

# Use -c instead of -m to avoid the runpy package/module naming conflict
python3 -c "
import sys, os
sys.path.insert(0, '.')

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    from pathlib import Path
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print('[env_check] Loaded backend/.env')
    else:
        print('[env_check] No backend/.env found — checking process environment only')
except ImportError:
    print('[env_check] python-dotenv not in PATH; install backend deps first')
    print('[env_check]   pip install -r requirements.txt')

from utils.env_check import check_env
check_env(strict=False)
print('[env_check] Done.')
"
