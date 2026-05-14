"""
prototype_film.py
-----------------

Assembles a 45–90 second contemplative essay-film prototype using the existing
Tattvashila system in DEGRADED MODE:

    - NO Claude scene analysis (rubric is hand-crafted per beat)
    - NO Claude clip ranking (we POST /api/retrieval/search with
      contemplative_mode=false so the threshold filter is skipped after the
      ranker silently falls back to flat 0.5 scores)
    - NO OpenAI TTS narration (we leave the timeline as silent placeholder
      segments timed against the narration excerpt; the user will record and
      drop in the voice manually)
    - Local FFmpeg/MoviePy render through the existing pipeline.

The narration excerpt is:

    "We wake up to noise.
     And sleep beside it.
     Every day, more information.
     More urgency.
     More stimulation.
     Yet somehow… less clarity.
     We were never meant to live like this."

Outputs written to /app/test_reports/prototype/:
    - timing_map.json       — every beat, line, duration, transition, clip
    - selected_clips.json   — provider, external_id, source_url, author per beat
    - provenance.json       — full render provenance (rubric, clip citations)
    - prototype_film.md     — human-readable summary
    - render_url.txt        — public preview URL of the rendered MP4
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import httpx
from dotenv import load_dotenv

# Resolve paths --------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

# Use the in-cluster backend URL — we run server-to-server, no need for the
# public ingress. This script is invoked manually from /app/backend.
BACKEND_URL = os.environ.get("PROTOTYPE_BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL}/api"

REPORT_DIR = Path("/app/test_reports/prototype")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Beat plan — hand-crafted contemplative judgment
# ---------------------------------------------------------------------------
@dataclass
class Beat:
    idx: int
    line: str                       # narration line (or pause marker)
    query: str                      # primary stock-search query
    fallback_queries: List[str]     # tried in order if primary returns nothing
    duration: float                 # seconds on the timeline
    transition_in: str              # fade | crossfade | dissolve
    transition_dur: float
    kind: str = "clip"              # clip | pause
    # populated at runtime
    selection: Optional[dict] = field(default=None)
    asset_id: Optional[str] = None


BEATS: List[Beat] = [
    Beat(0, "(opening pause)", "", [], 2.0, "fade", 1.5, kind="pause"),
    Beat(1, "We wake up to noise.",
         "empty city street dawn",
         ["quiet city morning", "urban dawn calm", "city street sunrise"],
         9.5, "fade", 1.5),
    Beat(2, "And sleep beside it.",
         "city window night",
         ["apartment window night", "city lights distant", "urban night quiet"],
         9.5, "crossfade", 2.0),
    Beat(3, "(breath pause)", "", [], 1.5, "fade", 1.5, kind="pause"),
    Beat(4, "Every day, more information.",
         "subway station people",
         ["train platform crowd", "commuters walking", "metro station daily"],
         8.5, "fade", 1.5),
    Beat(5, "More urgency.",
         "people walking street busy",
         ["pedestrians city slow", "intersection crowd", "office workers walk"],
         6.5, "crossfade", 2.0),
    Beat(6, "More stimulation.",
         "billboard advertising night",
         ["city signs night", "neon lights street", "shop windows evening"],
         6.5, "crossfade", 2.0),
    Beat(7, "(turning pause)", "", [], 1.5, "fade", 1.5, kind="pause"),
    Beat(8, "Yet somehow… less clarity.",
         "fog mist city silent",
         ["foggy morning quiet", "mist over water", "haze landscape still"],
         9.0, "dissolve", 2.0),
    Beat(9, "We were never meant to live like this.",
         "mountain landscape morning still",
         ["calm lake sunrise", "wide valley dawn", "ocean horizon morning"],
         12.0, "crossfade", 2.0),
    Beat(10, "(closing pause)", "", [], 3.0, "fade", 1.5, kind="pause"),
]


# Manual rubric — no Claude required ----------------------------------------
RUBRIC = {
    "emotional_tone": "observational, restrained, mournful but composed",
    "pacing": "slow",
    "environment": "modern urban contrasted with stilled natural openness",
    "atmosphere": "contemplative remove from contemporary stimulation",
    "restraint_level": 0.92,
    "preferred_keywords": [
        "still", "slow", "wide", "observational", "natural light", "dawn",
        "dusk", "mist", "calm", "muted", "long take", "documentary",
    ],
    "rejected_keywords": [
        "vlog", "selfie", "tiktok", "fast cut", "hyperlapse", "timelapse",
        "drone", "neon", "party", "dance", "dancing", "gym", "workout",
        "celebration", "fireworks", "advertisement", "commercial",
        "motivational", "happy", "smile", "children", "kids", "baby",
        "pet", "puppy", "kitten", "wedding", "fashion", "model",
        "explosion", "gaming", "esports", "anime", "cartoon",
    ],
    "search_queries": [b.query for b in BEATS if b.kind == "clip"],
    "rationale": "Hand-crafted rubric for degraded-mode prototype (no LLM).",
}


# ---------------------------------------------------------------------------
# Deterministic clip picker — no LLM
# ---------------------------------------------------------------------------
def _passes_reject(clip: dict) -> bool:
    haystack = " ".join([
        str(clip.get("title", "")).lower(),
        str(clip.get("query", "")).lower(),
        " ".join(clip.get("tags", []) or []).lower(),
    ])
    return not any(bad in haystack for bad in RUBRIC["rejected_keywords"])


def _pick_best_clip(clips: List[dict], target_duration: float) -> Optional[dict]:
    """Deterministic scoring: in-range duration > resolution > landscape > tag-match."""
    candidates = []
    for c in clips:
        w, h = int(c.get("width") or 0), int(c.get("height") or 0)
        if w <= 0 or h <= 0:
            continue
        if not _passes_reject(c):
            continue
        dur = float(c.get("duration") or 0.0)
        if dur < target_duration + 1.5:
            continue                          # need head/tail margin for trim
        candidates.append((c, w, h, dur))
    if not candidates:
        return None
    # Score: prefer landscape, ≥ 1920 wide, duration close to target+3s.
    def score(item):
        c, w, h, dur = item
        aspect = w / max(h, 1)
        s = 0.0
        s += 1.0 if aspect >= 1.4 else 0.0                       # landscape
        s += min(w, 3840) / 3840.0                                # resolution
        s -= abs(dur - (target_duration + 3.0)) / 20.0            # closeness
        # Slight preference for Pexels (more curated)
        s += 0.05 if c.get("provider") == "pexels" else 0.0
        # Prefer clips whose tags overlap the preferred keywords
        tags = " ".join(c.get("tags", []) or []).lower()
        for kw in RUBRIC["preferred_keywords"]:
            if kw in tags:
                s += 0.02
        return s
    candidates.sort(key=score, reverse=True)
    return candidates[0][0]


# ---------------------------------------------------------------------------
# Backend operations
# ---------------------------------------------------------------------------
def _client() -> httpx.Client:
    return httpx.Client(base_url=API, timeout=300.0)


def _search_one(client: httpx.Client, query: str, per_query: int = 3) -> List[dict]:
    """Call /api/retrieval/search with our hand-crafted rubric (skips analyse)
    and contemplative_mode=false (skips threshold filter when ranker fails)."""
    body = {
        "rubric": {**RUBRIC, "search_queries": [query]},
        "contemplative_mode": False,
        "per_query": per_query,
    }
    r = client.post("/retrieval/search", json=body)
    r.raise_for_status()
    return r.json().get("clips", []) or []


def select_clip_for_beat(client: httpx.Client, beat: Beat) -> Optional[dict]:
    if beat.kind != "clip":
        return None
    queries = [beat.query] + beat.fallback_queries
    for q in queries:
        clips = _search_one(client, q)
        picked = _pick_best_clip(clips, beat.duration)
        if picked:
            picked["_resolved_query"] = q
            return picked
        print(f"  ↳ no usable clip for query {q!r}; trying next…")
    return None


def create_project(client: httpx.Client) -> str:
    r = client.post("/projects", json={
        "title": "We Were Never Meant to Live Like This",
        "subtitle": "A degraded-mode contemplative prototype",
        "description": (
            "45–90s essay film built without LLM ranking. Manual cinematic "
            "judgment, raw Pexels+Pixabay search, restrained transitions, "
            "silent narration placeholders for later voice-over."
        ),
    })
    r.raise_for_status()
    proj = r.json()
    print(f"✓ created project {proj['id']}")
    return proj["id"]


def assemble_clips(client: httpx.Client, project_id: str, beats: List[Beat]) -> None:
    """Import all clip beats. trim_start/trim_duration are set manually so the
    backend never calls Claude for adaptive trimming."""
    selections = []
    for beat in beats:
        if beat.kind != "clip" or not beat.selection:
            continue
        sel = beat.selection
        clip_dur = float(sel.get("duration") or 0.0)
        # Trim window: middle of the source, length = beat.duration + 0.8s head/tail
        win = beat.duration + 0.8
        start = max(0.0, (clip_dur - win) / 2.0)
        selections.append({
            "provider": sel["provider"],
            "external_id": sel["external_id"],
            "title": sel.get("title", ""),
            "tags": sel.get("tags") or [],
            "duration": clip_dur,
            "width": int(sel.get("width") or 0),
            "height": int(sel.get("height") or 0),
            "download_url": sel.get("download_url") or sel.get("preview_url"),
            "preview_url": sel.get("preview_url", ""),
            "thumbnail_url": sel.get("thumbnail_url", ""),
            "author": sel.get("author", ""),
            "source_url": sel.get("source_url", ""),
            "trim_start": round(start, 2),
            "trim_duration": round(win, 2),
        })

    print(f"  importing {len(selections)} clips via /retrieval/assemble …")
    r = client.post("/retrieval/assemble", json={
        "project_id": project_id,
        "selections": selections,
        "pacing": "slow",
        "transition": "crossfade",
        "rubric_atmosphere": RUBRIC["atmosphere"],
        "rubric": RUBRIC,
    })
    r.raise_for_status()
    proj = r.json()
    # Map imported segments back onto our beat plan (order preserved by server)
    imported = [s for s in proj["segments"] if s["kind"] == "clip"]
    clip_beats = [b for b in beats if b.kind == "clip"]
    for beat, seg in zip(clip_beats, imported):
        beat.asset_id = seg["asset_id"]
    print(f"✓ assembled {len(imported)} clip segments")


def patch_full_timeline(client: httpx.Client, project_id: str, beats: List[Beat]) -> dict:
    """Replace the project's segment list with our full beat plan (clips +
    pauses), set ambient room_tone, and switch render to Preview 640."""
    full_segments = []
    for beat in beats:
        if beat.kind == "pause":
            full_segments.append({
                "kind": "pause",
                "asset_id": None,
                "duration": beat.duration,
                "start_offset": 0.0,
                "transition_in": beat.transition_in,
                "transition_in_duration": beat.transition_dur,
            })
        else:
            if not beat.asset_id:
                continue
            full_segments.append({
                "kind": "clip",
                "asset_id": beat.asset_id,
                "duration": beat.duration,
                "start_offset": 0.5,                # nudge in past head fade
                "transition_in": beat.transition_in,
                "transition_in_duration": beat.transition_dur,
            })

    payload = {
        "segments": full_segments,
        "ambient": {
            "source": "builtin",
            "builtin_key": "room_tone",
            "volume": 0.18,
            "fade_in": 3.0,
            "fade_out": 4.0,
        },
        "render_config": {
            "width": 640,
            "height": 360,
            "fps": 24,
            "video_bitrate": "900k",
            "audio_bitrate": "128k",
        },
    }
    r = client.patch(f"/projects/{project_id}", json=payload)
    r.raise_for_status()
    proj = r.json()
    total = sum(s["duration"] for s in proj["segments"])
    print(f"✓ timeline assembled: {len(proj['segments'])} segments, ~{total:.1f}s")
    return proj


def render_and_wait(client: httpx.Client, project_id: str) -> dict:
    r = client.post(f"/projects/{project_id}/render")
    r.raise_for_status()
    job = r.json()
    job_id = job["id"]
    print(f"✓ queued render job {job_id}")
    last_stage = None
    started = time.time()
    while True:
        time.sleep(3.0)
        r = client.get(f"/render/{job_id}")
        r.raise_for_status()
        job = r.json()
        if job["stage"] != last_stage:
            print(f"  · {job['stage']} ({job['progress']*100:.0f}%)")
            last_stage = job["stage"]
        if job["status"] in ("completed", "failed"):
            break
        if time.time() - started > 600:
            raise TimeoutError("Render exceeded 10 minutes")
    if job["status"] != "completed":
        raise RuntimeError(f"Render failed: {job.get('error')}")
    print(f"✓ render completed in {time.time() - started:.0f}s")
    return job


def fetch_provenance(client: httpx.Client, job_id: str) -> dict:
    r = client.get(f"/render/{job_id}/provenance")
    if r.status_code != 200:
        return {}
    return r.json()


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def write_reports(beats: List[Beat], project_id: str, job: dict, provenance: dict,
                  public_url: str) -> None:
    # 1) timing map
    timing = []
    cursor = 0.0
    for b in beats:
        timing.append({
            "idx": b.idx,
            "kind": b.kind,
            "line": b.line,
            "in": round(cursor, 2),
            "out": round(cursor + b.duration, 2),
            "duration": b.duration,
            "transition_in": b.transition_in,
            "transition_in_duration": b.transition_dur,
            "query": b.query or None,
            "resolved_query": (b.selection or {}).get("_resolved_query") if b.kind == "clip" else None,
            "asset_id": b.asset_id,
            "clip": {
                "provider": (b.selection or {}).get("provider"),
                "external_id": (b.selection or {}).get("external_id"),
                "title": (b.selection or {}).get("title"),
                "source_url": (b.selection or {}).get("source_url"),
                "author": (b.selection or {}).get("author"),
                "width": (b.selection or {}).get("width"),
                "height": (b.selection or {}).get("height"),
                "source_duration": (b.selection or {}).get("duration"),
            } if b.kind == "clip" and b.selection else None,
        })
        cursor += b.duration
    total = round(cursor, 2)

    (REPORT_DIR / "timing_map.json").write_text(json.dumps({
        "project_id": project_id,
        "render_job_id": job["id"],
        "output_asset_id": job.get("output_asset_id"),
        "total_duration": total,
        "beats": timing,
    }, indent=2))

    # 2) selected_clips
    (REPORT_DIR / "selected_clips.json").write_text(json.dumps([
        {
            "beat": b.idx,
            "line": b.line,
            "query_used": (b.selection or {}).get("_resolved_query"),
            **(b.selection or {}),
        }
        for b in beats if b.kind == "clip" and b.selection
    ], indent=2))

    # 3) provenance
    (REPORT_DIR / "provenance.json").write_text(json.dumps(provenance or {}, indent=2))

    # 4) URL
    (REPORT_DIR / "render_url.txt").write_text(public_url + "\n")

    # 5) human summary
    lines = [
        "# Tattvashila — Prototype Film (Degraded Mode)",
        "",
        "**Title:** *We Were Never Meant to Live Like This*",
        "",
        f"- Project ID: `{project_id}`",
        f"- Render job: `{job['id']}`",
        f"- Output asset: `{job.get('output_asset_id')}`",
        f"- Total duration: **{total:.1f}s**",
        f"- Resolution: 640×360 @ 24fps (Preview)",
        f"- Public preview URL: {public_url}",
        "",
        "## Timing map",
        "",
        "| # | In | Out | Dur | Line | Clip |",
        "|---|----|-----|-----|------|------|",
    ]
    for t in timing:
        clip = t["clip"]
        clip_cell = (
            f"{clip['provider']}/{clip['external_id']} — {clip['author']}"
            if clip else "—"
        )
        lines.append(
            f"| {t['idx']} | {t['in']:.1f} | {t['out']:.1f} | {t['duration']:.1f} | "
            f"{t['line']} | {clip_cell} |"
        )
    lines += [
        "",
        "## Provenance",
        "",
        "All retrieved clips were imported with their attribution preserved "
        "(provider, external_id, source_url, author). Full provenance JSON in "
        "`provenance.json`.",
        "",
        "## Mode notes",
        "",
        "- LLM scene analysis: **skipped** (rubric hand-crafted in script).",
        "- LLM clip ranking: **skipped** (ranker fell back to flat scores; "
        "selection done deterministically by resolution + duration + "
        "rejected-keyword heuristic).",
        "- TTS narration: **skipped** (silent timeline placeholders; record "
        "and overlay voice-over manually).",
        "- Ambient: built-in `room_tone` preset at 0.18 volume, 3s fade-in.",
        "- Transitions: fade · crossfade · dissolve only, 1.5–2.0s each.",
        "- Render: Preview 640 (640×360 @ 24fps, 900k video bitrate).",
    ]
    (REPORT_DIR / "prototype_film.md").write_text("\n".join(lines))
    print(f"✓ reports written to {REPORT_DIR}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print(f"Tattvashila prototype film — degraded mode\n  backend: {API}\n")
    with _client() as client:
        # Sanity
        r = client.get("/health")
        r.raise_for_status()
        print(f"✓ backend reachable: {r.json()}\n")

        # Phase 1 — pick clips per beat
        print("Phase 1: retrieval (deterministic pick, no LLM)")
        for beat in BEATS:
            if beat.kind != "clip":
                print(f"  · beat {beat.idx} — pause {beat.duration:.1f}s")
                continue
            print(f"  · beat {beat.idx} — searching {beat.query!r}")
            picked = select_clip_for_beat(client, beat)
            if not picked:
                print(f"    ✗ NO CLIP for beat {beat.idx} — aborting")
                return 2
            beat.selection = picked
            print(f"    ✓ {picked['provider']}/{picked['external_id']} "
                  f"({picked.get('width')}x{picked.get('height')}, "
                  f"{picked.get('duration'):.1f}s) — {picked.get('author','?')}")
        print()

        # Phase 2 — create project + import + assemble
        print("Phase 2: project + assemble")
        project_id = create_project(client)
        assemble_clips(client, project_id, BEATS)

        # Phase 3 — full timeline (clips + pauses + ambient + Preview 640)
        print("\nPhase 3: timeline / ambient / render config")
        patch_full_timeline(client, project_id, BEATS)

        # Phase 4 — render
        print("\nPhase 4: render")
        job = render_and_wait(client, project_id)

        # Phase 5 — provenance + reports
        print("\nPhase 5: provenance + reports")
        provenance = fetch_provenance(client, job["id"])

        # Public URL of the rendered MP4 (via REACT_APP_BACKEND_URL / ingress)
        frontend_env = Path("/app/frontend/.env").read_text()
        public_base = None
        for ln in frontend_env.splitlines():
            if ln.startswith("REACT_APP_BACKEND_URL="):
                public_base = ln.split("=", 1)[1].strip()
                break
        out_asset_id = job.get("output_asset_id") or ""
        # Look up storage path for the output asset
        ma = client.get("/media").json()
        sp = next((m["storage_path"] for m in ma if m["id"] == out_asset_id), "")
        public_url = f"{public_base}/api/files/{sp}" if sp and public_base else ""

        write_reports(BEATS, project_id, job, provenance, public_url)
        print(f"\nPublic preview URL: {public_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
