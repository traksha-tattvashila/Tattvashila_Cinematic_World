"""
Stock provider integrations.

Currently:
    - Pexels Videos API
    - Pixabay Videos API
    - Local archive (placeholder)

Each provider returns a uniform `ProviderClip` shape. HTTP calls are
wrapped in exponential-backoff retries; if a provider returns 429 or
fails repeatedly, the aggregate `search_all` returns whatever the other
providers produced rather than failing the whole call.
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from utils.retry import retry_async

logger = logging.getLogger(__name__)

PEXELS_ENDPOINT = "https://api.pexels.com/videos/search"
PIXABAY_ENDPOINT = "https://pixabay.com/api/videos/"
HTTP_TIMEOUT = 15.0


@dataclass
class ProviderClip:
    provider: str                # "pexels" | "pixabay" | "local"
    external_id: str
    title: str
    tags: List[str] = field(default_factory=list)
    duration: float = 0.0
    width: int = 0
    height: int = 0
    thumbnail_url: str = ""
    preview_url: str = ""        # mp4 url usable in a <video> tag
    download_url: str = ""       # best quality mp4 url
    author: str = ""
    source_url: str = ""
    query: str = ""
    score: Optional[float] = None
    rationale: Optional[str] = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


# ---------------------------------------------------------------------------
# Pexels — parser + search
# ---------------------------------------------------------------------------
def _pick_pexels_file(video_files: List[dict]) -> Optional[dict]:
    """Choose a sensible ~1080p mp4 file from a Pexels response."""
    mp4s = [f for f in video_files if (f.get("file_type") or "").startswith("video/mp4")]
    if not mp4s:
        return None
    mp4s.sort(key=lambda f: (
        abs((f.get("width") or 0) - 1920),
        -(f.get("width") or 0),
    ))
    return mp4s[0]


def _parse_pexels_video(v: Dict[str, Any], query: str) -> Optional[ProviderClip]:
    file = _pick_pexels_file(v.get("video_files", []) or [])
    if not file:
        return None
    user = v.get("user") or {}
    return ProviderClip(
        provider="pexels",
        external_id=str(v.get("id")),
        title=user.get("name") or "Pexels clip",
        tags=[],
        duration=float(v.get("duration") or 0),
        width=int(file.get("width") or 0),
        height=int(file.get("height") or 0),
        thumbnail_url=v.get("image") or "",
        preview_url=file.get("link") or "",
        download_url=file.get("link") or "",
        author=user.get("name", ""),
        source_url=v.get("url") or "",
        query=query,
    )


async def _pexels_search(client: httpx.AsyncClient, query: str, per_page: int = 6) -> List[ProviderClip]:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return []

    async def _call():
        r = await client.get(
            PEXELS_ENDPOINT,
            params={
                "query": query,
                "per_page": per_page,
                "orientation": "landscape",
                "size": "large",
            },
            headers={"Authorization": key},
            timeout=HTTP_TIMEOUT,
        )
        # Rate-limit / server-side issues are worth retrying; auth errors aren't
        if r.status_code in (429, 500, 502, 503, 504):
            raise httpx.HTTPStatusError(
                f"pexels {r.status_code}", request=r.request, response=r,
            )
        r.raise_for_status()
        return r.json()

    try:
        data = await retry_async(_call, attempts=3, label=f"pexels[{query!r}]")
    except Exception as e:  # noqa: BLE001
        logger.warning("Pexels search gave up for %r: %s", query, e)
        return []

    out: List[ProviderClip] = []
    for v in data.get("videos", []) or []:
        clip = _parse_pexels_video(v, query)
        if clip:
            out.append(clip)
    return out


# ---------------------------------------------------------------------------
# Pixabay — parser + search
# ---------------------------------------------------------------------------
def _pick_pixabay_video(videos: dict) -> Optional[dict]:
    for k in ("large", "medium", "small", "tiny"):
        v = videos.get(k)
        if v and v.get("url"):
            return v
    return None


def _parse_pixabay_hit(hit: Dict[str, Any], query: str) -> Optional[ProviderClip]:
    video = _pick_pixabay_video(hit.get("videos", {}) or {})
    if not video:
        return None
    picture_id = hit.get("picture_id")
    thumbnail = (
        f"https://i.vimeocdn.com/video/{picture_id}_295x166.jpg"
        if picture_id
        else (hit.get("videos", {}).get("tiny", {}) or {}).get("thumbnail", "")
    )
    tags = [t.strip() for t in (hit.get("tags") or "").split(",") if t.strip()]
    return ProviderClip(
        provider="pixabay",
        external_id=str(hit.get("id")),
        title=", ".join(tags[:3]) or "Pixabay clip",
        tags=tags,
        duration=float(hit.get("duration") or 0),
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
        thumbnail_url=thumbnail,
        preview_url=video.get("url") or "",
        download_url=video.get("url") or "",
        author=hit.get("user") or "",
        source_url=hit.get("pageURL") or "",
        query=query,
    )


async def _pixabay_search(client: httpx.AsyncClient, query: str, per_page: int = 6) -> List[ProviderClip]:
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return []

    async def _call():
        r = await client.get(
            PIXABAY_ENDPOINT,
            params={
                "key": key,
                "q": query,
                "per_page": max(3, per_page),
                "safesearch": "true",
                "video_type": "film",
            },
            timeout=HTTP_TIMEOUT,
        )
        if r.status_code in (429, 500, 502, 503, 504):
            raise httpx.HTTPStatusError(
                f"pixabay {r.status_code}", request=r.request, response=r,
            )
        r.raise_for_status()
        return r.json()

    try:
        data = await retry_async(_call, attempts=3, label=f"pixabay[{query!r}]")
    except Exception as e:  # noqa: BLE001
        logger.warning("Pixabay search gave up for %r: %s", query, e)
        return []

    out: List[ProviderClip] = []
    for hit in data.get("hits", []) or []:
        clip = _parse_pixabay_hit(hit, query)
        if clip:
            out.append(clip)
    return out


# ---------------------------------------------------------------------------
# Local archive — placeholder
# ---------------------------------------------------------------------------
async def _local_archive_search(query: str) -> List[ProviderClip]:
    """Reserved for a curated in-database archive (filled later)."""
    return []


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------
def _dedupe(clips: List[ProviderClip]) -> List[ProviderClip]:
    seen = set()
    out: List[ProviderClip] = []
    for c in clips:
        key = (c.provider, c.external_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


async def search_all(queries: List[str], per_query: int = 4) -> List[ProviderClip]:
    """Concurrently query Pexels + Pixabay + local archive for each query.

    Robust to partial failures — a 429/500 from one provider does not fail
    the whole call. Results from the surviving providers are returned.
    """
    queries = [q for q in (queries or []) if q.strip()][:5]
    if not queries:
        return []

    async with httpx.AsyncClient() as client:
        tasks = []
        for q in queries:
            tasks.append(_pexels_search(client, q, per_query))
            tasks.append(_pixabay_search(client, q, per_query))
            tasks.append(_local_archive_search(q))
        results = await asyncio.gather(*tasks, return_exceptions=True)

    clips: List[ProviderClip] = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning("Provider task raised: %s", r)
            continue
        clips.extend(r)
    return _dedupe(clips)
