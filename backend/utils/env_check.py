"""Startup environment variable validator.

Validates that all required environment variables are present and non-empty
before the application boots. Produces a clear, actionable error message
rather than a confusing traceback when something is missing.

Usage (call once, early in server.py, after load_dotenv):

    from utils.env_check import check_env
    check_env()

Can also be run standalone as a quick sanity check:

    python -m utils.env_check
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class EnvVar:
    name: str
    purpose: str
    required: bool = True
    placeholder_fragments: tuple = ()


# ── Variable registry ─────────────────────────────────────────────────────────
# Add new variables here; they will automatically appear in error messages.
_BACKEND_VARS: List[EnvVar] = [
    EnvVar(
        "EMERGENT_LLM_KEY",
        "Emergent platform key — gates all AI (TTS, Claude, Object Storage)",
        required=True,
        placeholder_fragments=("your_emergent",),
    ),
    EnvVar(
        "DATABASE_URL",
        "Supabase Postgres connection string (Transaction Pooler, port 6543)",
        required=True,
        placeholder_fragments=("<username>", "<password>", "<host>", "your_"),
    ),
    EnvVar(
        "PEXELS_API_KEY",
        "Pexels stock video API key for clip retrieval",
        required=True,
        placeholder_fragments=("your_pexels",),
    ),
    EnvVar(
        "PIXABAY_API_KEY",
        "Pixabay stock video API key for clip retrieval",
        required=True,
        placeholder_fragments=("your_pixabay",),
    ),
    EnvVar(
        "MONGO_URL",
        "MongoDB Atlas connection string (legacy store / migration scripts)",
        required=False,
        placeholder_fragments=("<username>", "<password>", "<cluster>"),
    ),
    EnvVar(
        "DB_NAME",
        "MongoDB database name",
        required=False,
        placeholder_fragments=("your_database",),
    ),
    EnvVar(
        "CORS_ORIGINS",
        "Comma-separated allowed CORS origins (defaults to * if unset)",
        required=False,
    ),
    EnvVar(
        "APP_NAME",
        "Application name used for storage namespacing",
        required=False,
        placeholder_fragments=("YourAppName",),
    ),
]


def _is_placeholder(value: str, var: EnvVar) -> bool:
    """Return True if the value looks like an unfilled template placeholder."""
    if not var.placeholder_fragments:
        return False
    low = value.lower()
    return any(frag.lower() in low for frag in var.placeholder_fragments)


def check_env(strict: bool = True) -> None:
    """Validate environment variables.

    Parameters
    ----------
    strict:
        If True (default), exit with code 1 when any *required* variable is
        missing or contains a placeholder value.
        If False, only print warnings and return.
    """
    missing_required: List[EnvVar] = []
    placeholder_required: List[EnvVar] = []
    missing_optional: List[EnvVar] = []

    for var in _BACKEND_VARS:
        value = os.environ.get(var.name, "").strip()
        if not value:
            if var.required:
                missing_required.append(var)
            else:
                missing_optional.append(var)
        elif _is_placeholder(value, var):
            if var.required:
                placeholder_required.append(var)

    # ── Optional missing (just a notice) ──────────────────────────────────────
    if missing_optional:
        names = ", ".join(v.name for v in missing_optional)
        print(f"[env] Optional vars not set (app may degrade): {names}", file=sys.stderr)

    # ── Required issues ───────────────────────────────────────────────────────
    problems = missing_required + placeholder_required
    if not problems:
        return

    env_example = Path(__file__).resolve().parents[1] / ".env.example"
    separator = "═" * 60

    print(f"\n{separator}", file=sys.stderr)
    print("  MISSING OR UNCONFIGURED ENVIRONMENT VARIABLES", file=sys.stderr)
    print(separator, file=sys.stderr)
    print("", file=sys.stderr)

    for var in missing_required:
        print(f"  ✗  {var.name}", file=sys.stderr)
        print(f"     {var.purpose}", file=sys.stderr)
        print("", file=sys.stderr)

    for var in placeholder_required:
        print(f"  ⚠  {var.name}  (value looks like an unfilled placeholder)", file=sys.stderr)
        print(f"     {var.purpose}", file=sys.stderr)
        print("", file=sys.stderr)

    print("  How to fix:", file=sys.stderr)
    print("    1. Copy backend/.env.example → backend/.env", file=sys.stderr)
    print("    2. Fill in every value marked with <angle-brackets>", file=sys.stderr)
    if env_example.exists():
        print(f"    3. Template is at: {env_example}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  In Replit: add each variable to the Secrets panel instead of", file=sys.stderr)
    print("  editing .env files (secrets are injected automatically).", file=sys.stderr)
    print(f"{separator}\n", file=sys.stderr)

    if strict:
        sys.exit(1)


# ── Standalone use ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _env_path = Path(__file__).resolve().parents[1] / ".env"
    try:
        from dotenv import load_dotenv as _load_dotenv
        if _env_path.exists():
            _load_dotenv(_env_path)
            print(f"[env_check] Loaded: {_env_path}")
        else:
            print(f"[env_check] No .env at {_env_path} — checking process environment only")
    except ImportError:
        print("[env_check] python-dotenv not available; checking process environment only")
        print("[env_check] Run from backend/ with its virtualenv active for full validation")

    check_env(strict=False)
    print("[env_check] Done.")
