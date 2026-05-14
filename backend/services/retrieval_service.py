"""
Retrieval service helpers.

`import_stock_clip` is intentionally composed of five named phases so each
step has a single responsibility and can be unit-tested independently:

    1. validate_selection      — refuse malformed input early
    2. download_provider_clip  — fetch the remote MP4 with retries
    3. extract_metadata        — duration + resolution probe
    4. persist_to_storage      — push bytes into Emergent Object Storage
    5. compose_media_asset     — build the final MediaAsset model

A single orchestrator `import_stock_clip()` glues them together so the
HTTP layer in server.py stays declarative.
"""
from __future__ import annotations

import logging
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import httpx

import storage
from models import AssembleClipSelection, MediaAsset, Segment
from pipeline.renderer import probe_duration, probe_resolution
from utils.retry import retry_async

logger = logging.getLogger(__name__)

DOWNLOAD_TIMEOUT = 120.0


# ---------------------------------------------------------------------------
# Phase 1 — validation
# ---------------------------------------------------------------------------
class InvalidSelectionError(ValueError):
    """The selection cannot be imported (missing download URL, etc.)."""


def validate_selection(sel: AssembleClipSelection) -> None:
    """Raise `InvalidSelectionError` if the selection is unusable."""
    if not sel.download_url or not sel.download_url.startswith(("http://", "https://")):
        raise InvalidSelectionError(f"missing download url for {sel.provider}/{sel.external_id}")
    if not sel.external_id:
        raise InvalidSelectionError(f"missing external_id for {sel.provider}")


# ---------------------------------------------------------------------------
# Phase 2 — download
# ---------------------------------------------------------------------------
async def download_url_bytes(url: str) -> Tuple[bytes, str]:
    """Public helper: fetch a URL with retries. Returns (bytes, content_type)."""
    async def _call():
        async with httpx.AsyncClient(follow_redirects=True, timeout=DOWNLOAD_TIMEOUT) as c:
            r = await c.get(url)
            if r.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError(
                    f"download {r.status_code}", request=r.request, response=r,
                )
            r.raise_for_status()
            return r.content, r.headers.get("Content-Type", "video/mp4")

    return await retry_async(_call, attempts=3, label=f"download[{url[:60]}]")


async def download_provider_clip(sel: AssembleClipSelection) -> Tuple[bytes, str]:
    """Phase 2: pull the clip bytes from the provider CDN."""
    return await download_url_bytes(sel.download_url)


# ---------------------------------------------------------------------------
# Phase 3 — metadata
# ---------------------------------------------------------------------------
@dataclass
class ProbedMetadata:
    duration: Optional[float]
    width: Optional[int]
    height: Optional[int]
    ext: str


def extract_metadata(data: bytes, content_type: str) -> ProbedMetadata:
    """Phase 3: probe duration/resolution by writing the bytes to a temp file."""
    ext = "webm" if "webm" in (content_type or "").lower() else "mp4"

    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None

    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        duration = probe_duration(tmp_path)
        res = probe_resolution(tmp_path)
        if res:
            width = res.get("width")
            height = res.get("height")
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass

    return ProbedMetadata(duration=duration, width=width, height=height, ext=ext)


# ---------------------------------------------------------------------------
# Phase 4 — persistence
# ---------------------------------------------------------------------------
def persist_to_storage(
    data: bytes,
    content_type: str,
    ext: str,
) -> Tuple[str, str, int]:
    """Phase 4: upload to object storage. Returns (file_id, storage_path, size)."""
    file_id = str(uuid.uuid4())
    path = storage.build_path("clip", file_id, ext)
    result = storage.put_object(path, data, content_type or "video/mp4")
    return file_id, result["path"], int(result.get("size", len(data)))


# ---------------------------------------------------------------------------
# Phase 5 — compose MediaAsset
# ---------------------------------------------------------------------------
def compose_media_asset(
    *,
    file_id: str,
    storage_path: str,
    size: int,
    content_type: str,
    ext: str,
    sel: AssembleClipSelection,
    meta: ProbedMetadata,
) -> MediaAsset:
    """Phase 5: assemble the final MediaAsset record (caller persists to Mongo)."""
    return MediaAsset(
        id=file_id,
        kind="clip",
        storage_path=storage_path,
        original_filename=(sel.title.strip() or f"{sel.provider}-{sel.external_id}") + f".{ext}",
        content_type=content_type or "video/mp4",
        size=size,
        duration=meta.duration or sel.duration or None,
        width=meta.width or sel.width or None,
        height=meta.height or sel.height or None,
        provider=sel.provider,
        provider_external_id=sel.external_id,
        source_url=sel.source_url or None,
        author=sel.author or None,
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
async def import_stock_clip(sel: AssembleClipSelection) -> Optional[MediaAsset]:
    """Run all five phases; return None on any failure (caller logs)."""
    try:
        validate_selection(sel)
    except InvalidSelectionError as e:
        logger.warning("Invalid selection: %s", e)
        return None

    try:
        data, content_type = await download_provider_clip(sel)
    except Exception as e:  # noqa: BLE001
        logger.warning("Stock clip download failed for %s: %s", sel.download_url, e)
        return None

    meta = extract_metadata(data, content_type)
    file_id, storage_path, size = persist_to_storage(data, content_type, meta.ext)
    return compose_media_asset(
        file_id=file_id,
        storage_path=storage_path,
        size=size,
        content_type=content_type,
        ext=meta.ext,
        sel=sel,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Segment construction
# ---------------------------------------------------------------------------
def build_retrieval_segment(
    *,
    asset: MediaAsset,
    trim: dict,
    is_first_on_timeline: bool,
    transition: str,
) -> Segment:
    """Compose a `Segment` for an imported stock clip with restrained transitions."""
    if is_first_on_timeline:
        transition_in = "fade"
        transition_duration = 1.5
    else:
        transition_in = transition or "crossfade"
        transition_duration = 2.0 if transition_in in ("crossfade", "dissolve") else 1.5

    return Segment(
        kind="clip",
        asset_id=asset.id,
        duration=float(trim["duration"]),
        start_offset=float(trim["start"]),
        transition_in=transition_in,
        transition_in_duration=transition_duration,
    )
