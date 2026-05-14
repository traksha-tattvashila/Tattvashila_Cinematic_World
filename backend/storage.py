"""
Emergent Object Storage wrapper for Tattvashila.

All persistent media (uploaded clips, narration audio, ambient sounds,
rendered films) live in Emergent Object Storage. Metadata is persisted in
Postgres; the canonical storage path returned by put_object() is what we
keep in the DB.

Paths follow:    {APP_NAME}/{kind}/{uuid}.{ext}

Resilience: PUT/GET are wrapped in a small retry loop that:
  - On 403, re-initialises the storage key (token rotation) and retries.
  - On 5xx / connection errors, re-initialises and retries with linear
    backoff up to MAX_RETRIES.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
MAX_RETRIES = 3
BACKOFF_BASE_S = 1.5

_storage_key: Optional[str] = None


def app_name() -> str:
    return os.environ.get("APP_NAME", "tattvashila")


def init_storage(force: bool = False) -> str:
    """Initialise the session-scoped storage key. Idempotent unless `force`."""
    global _storage_key
    if _storage_key and not force:
        return _storage_key
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise RuntimeError("EMERGENT_LLM_KEY is not configured")
    resp = requests.post(
        f"{STORAGE_URL}/init",
        json={"emergent_key": emergent_key},
        timeout=30,
    )
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    logger.info("Object storage initialised")
    return _storage_key


def _is_transient_status(code: int) -> bool:
    return code == 403 or 500 <= code < 600


def _do_request(method: str, path: str, *, headers=None, data=None, timeout=300):
    """Execute a request with retries for transient failures (403 + 5xx).

    On 403 OR 5xx, re-initialises the storage key and retries with linear
    backoff (1.5s, 3s, 4.5s). Connection errors are also retried.
    """
    url = f"{STORAGE_URL}/objects/{path}"
    last_err: Optional[BaseException] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            key = init_storage(force=(attempt > 0))
            req_headers = dict(headers or {})
            req_headers["X-Storage-Key"] = key
            resp = requests.request(
                method, url, headers=req_headers, data=data, timeout=timeout,
            )
            if _is_transient_status(resp.status_code) and attempt < MAX_RETRIES:
                logger.warning(
                    "Object storage %s %s → %d (attempt %d/%d), retrying",
                    method, path, resp.status_code, attempt + 1, MAX_RETRIES,
                )
                time.sleep(BACKOFF_BASE_S * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout) as e:
            last_err = e
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Object storage %s %s connection error (attempt %d/%d): %s",
                    method, path, attempt + 1, MAX_RETRIES, e,
                )
                time.sleep(BACKOFF_BASE_S * (attempt + 1))
                continue
            raise
    if last_err:
        raise last_err
    raise RuntimeError("Object storage retries exhausted")


def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload `data` to `path`. Returns dict with `path`, `size`, `etag`."""
    resp = _do_request(
        "PUT", path,
        headers={"Content-Type": content_type},
        data=data,
        timeout=600,
    )
    return resp.json()


def get_object(path: str) -> Tuple[bytes, str]:
    """Download an object. Returns (bytes, content_type)."""
    resp = _do_request("GET", path, timeout=300)
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


def build_path(kind: str, file_id: str, ext: str) -> str:
    """Build a canonical, app-namespaced object path."""
    ext = ext.lstrip(".") or "bin"
    return f"{app_name()}/{kind}/{file_id}.{ext}"
