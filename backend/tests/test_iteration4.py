"""Iteration-4 hardening tests: trim override, provenance, fallback UX,
sticky rubric, Provider Literal typing, import_stock_clip phase validation.
"""
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")
                break

API = f"{BASE_URL}/api"
R: dict = {}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# -------- Fallback UX: empty search returns suggestions + reason --------
class TestRetrievalFallbackUX:
    def test_contemplative_filter_returns_suggestions(self, s):
        r = s.post(
            f"{API}/retrieval/search",
            json={
                "description": "neon TikTok dance party flashing strobe lights",
                "contemplative_mode": True,
                "per_query": 4,
            },
            timeout=180,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        clips = data.get("clips", [])
        # Expect 0 or few clips for this contemplative-hostile prompt
        if len(clips) == 0:
            assert "suggestions" in data, "Empty result must include suggestions"
            assert isinstance(data["suggestions"], list) and len(data["suggestions"]) > 0
            assert data.get("reason") in (
                "filtered_by_contemplative_mode",
                "no_results_from_providers",
                "no_matches",
            ), f"unexpected reason={data.get('reason')}"
            if data["reason"] == "filtered_by_contemplative_mode":
                assert data.get("unfiltered_count", 0) > 0, "unfiltered_count must be > 0"
            R["fallback_reason"] = data["reason"]
        else:
            # Even with clips, no fallback fields required
            R["fallback_reason"] = "had_clips"


# -------- Provider Literal typing --------
class TestProviderLiteral:
    def test_unsupported_provider_returns_422(self, s):
        # Create a real project first
        r = s.post(f"{API}/projects", json={"title": "TEST_LiteralCheck"}, timeout=30)
        assert r.status_code == 200
        pid = r.json()["id"]
        R["literal_pid"] = pid

        sel = {
            "provider": "unsupported_provider",
            "external_id": "x",
            "download_url": "https://example.com/x.mp4",
            "duration": 5, "width": 100, "height": 100,
        }
        r = s.post(
            f"{API}/retrieval/assemble",
            json={"project_id": pid, "selections": [sel]},
            timeout=30,
        )
        assert r.status_code == 422, f"expected 422, got {r.status_code}: {r.text}"

    def test_cleanup_literal_project(self, s):
        if "literal_pid" in R:
            s.delete(f"{API}/projects/{R['literal_pid']}", timeout=30)


# -------- Trim override on /api/retrieval/assemble --------
class TestTrimOverride:
    def test_trim_override_bypasses_adaptive_trim(self, s):
        # Fresh project
        r = s.post(f"{API}/projects", json={"title": "TEST_TrimOverride"}, timeout=30)
        assert r.status_code == 200
        pid = r.json()["id"]
        R["trim_pid"] = pid

        # Get clips via real search
        r = s.post(
            f"{API}/retrieval/search",
            json={"description": "Contemplative forest pathway at dawn",
                  "contemplative_mode": True, "per_query": 3},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        clips = body.get("clips") or []
        assert len(clips) >= 1, f"need at least 1 clip: {body}"
        c = clips[0]

        rubric = body.get("rubric") or {}
        sel = {
            "provider": c["provider"],
            "external_id": c["external_id"],
            "title": c.get("title", ""),
            "duration": c["duration"],
            "width": c["width"],
            "height": c["height"],
            "download_url": c["download_url"],
            "preview_url": c["preview_url"],
            "thumbnail_url": c["thumbnail_url"],
            "author": c.get("author", ""),
            "source_url": c.get("source_url", ""),
            "trim_start": 5.0,
            "trim_duration": 7.0,
        }
        r = s.post(
            f"{API}/retrieval/assemble",
            json={
                "project_id": pid,
                "selections": [sel],
                "pacing": "slow",
                "transition": "crossfade",
                "rubric": rubric,
                "rubric_atmosphere": rubric.get("atmosphere", ""),
            },
            timeout=240,
        )
        assert r.status_code == 200, r.text
        project = r.json()
        assert len(project["segments"]) >= 1
        seg = project["segments"][-1]
        # Exact override values (bypasses LLM adaptive_trim)
        assert seg["start_offset"] == 5.0, f"start_offset={seg['start_offset']}"
        assert seg["duration"] == 7.0, f"duration={seg['duration']}"

        # Sticky rubric persistence
        assert project.get("last_rubric") is not None, "last_rubric must be persisted"
        assert project.get("last_retrieval_at"), "last_retrieval_at must be set"
        # ISO-ish timestamp
        assert "T" in project["last_retrieval_at"]
        R["trim_project"] = project

    def test_cleanup_trim_project(self, s):
        if "trim_pid" in R:
            s.delete(f"{API}/projects/{R['trim_pid']}", timeout=30)


# -------- import_stock_clip phase units --------
class TestImportPhases:
    def test_validate_selection_empty_url_raises(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from services.retrieval_service import validate_selection, InvalidSelectionError
        from models import AssembleClipSelection
        sel = AssembleClipSelection(
            provider="pexels", external_id="abc",
            download_url="",  # invalid
        )
        # download_url is required field — but if empty string passes pydantic, validate must catch
        with pytest.raises(InvalidSelectionError):
            validate_selection(sel)

    def test_extract_metadata_for_mp4_bytes(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from services.retrieval_service import extract_metadata
        data = Path("/tmp/test_clip.mp4").read_bytes()
        meta = extract_metadata(data, "video/mp4")
        assert meta.ext == "mp4"
        assert meta.duration is not None and meta.duration > 0
        assert meta.width == 320
        assert meta.height == 240

    def test_pexels_search_missing_key_returns_empty(self, monkeypatch):
        import sys
        sys.path.insert(0, "/app/backend")
        import httpx
        from retrieval import providers as P
        monkeypatch.delenv("PEXELS_API_KEY", raising=False)

        async def _run():
            async with httpx.AsyncClient() as c:
                return await P._pexels_search(c, "forest", per_page=2)

        result = asyncio.run(_run())
        assert result == []


# -------- Provenance endpoint (uses pre-existing seed render if available) --------
class TestProvenance:
    @pytest.fixture(scope="class")
    def rendered_job_id(self, s):
        """Spin up a small render to test provenance."""
        # Upload a clip
        with open("/tmp/test_clip.mp4", "rb") as f:
            ur = s.post(
                f"{API}/media/upload",
                data={"kind": "clip"},
                files={"file": ("test_clip.mp4", f, "video/mp4")},
                timeout=60,
            )
        assert ur.status_code == 200
        clip_id = ur.json()["id"]
        R["prov_clip_id"] = clip_id

        # Create project
        cr = s.post(f"{API}/projects", json={"title": "TEST_Provenance"}, timeout=30)
        assert cr.status_code == 200
        pid = cr.json()["id"]
        R["prov_pid"] = pid

        # Patch a small timeline: clip + pause + clip at 320x240
        patch = {
            "segments": [
                {"kind": "clip", "asset_id": clip_id, "duration": 1.5,
                 "transition_in": "fade", "transition_in_duration": 0.3, "start_offset": 0.0},
                {"kind": "pause", "duration": 0.5, "transition_in": "fade", "transition_in_duration": 0.2},
                {"kind": "clip", "asset_id": clip_id, "duration": 1.5,
                 "transition_in": "crossfade", "transition_in_duration": 0.4, "start_offset": 0.0},
            ],
            "render_config": {
                "width": 320, "height": 240, "fps": 24,
                "video_bitrate": "800k", "audio_bitrate": "96k",
            },
        }
        s.patch(f"{API}/projects/{pid}", json=patch, timeout=30)
        rr = s.post(f"{API}/projects/{pid}/render", timeout=30)
        assert rr.status_code == 200
        job_id = rr.json()["id"]

        deadline = time.time() + 150
        last = None
        while time.time() < deadline:
            jr = s.get(f"{API}/render/{job_id}", timeout=30)
            assert jr.status_code == 200
            last = jr.json()
            if last["status"] == "completed":
                break
            if last["status"] == "failed":
                pytest.fail(f"Render failed: {last.get('error')}")
            time.sleep(2)
        assert last and last["status"] == "completed", f"timeout: {last}"
        R["prov_job_id"] = job_id
        return job_id

    def test_provenance_json(self, s, rendered_job_id):
        r = s.get(f"{API}/render/{rendered_job_id}/provenance", timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        for key in ("schema_version", "project", "rubric", "retrieved_at",
                    "rendered_at", "segments", "citations"):
            assert key in body, f"missing {key} in provenance"
        assert isinstance(body["citations"], list) and len(body["citations"]) >= 1
        for c in body["citations"]:
            assert "provider" in c, c

    def test_provenance_text(self, s, rendered_job_id):
        r = s.get(f"{API}/render/{rendered_job_id}/provenance?format=text", timeout=30)
        assert r.status_code == 200, r.text
        assert "text/plain" in r.headers.get("content-type", "")
        assert "TATTVASHILA — Provenance Sheet" in r.text

    def test_provenance_download_disposition(self, s, rendered_job_id):
        r = s.get(
            f"{API}/render/{rendered_job_id}/provenance?format=text&download=1",
            timeout=30,
        )
        assert r.status_code == 200
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd.lower() or "filename" in cd.lower(), cd

    def test_provenance_unknown_job_404(self, s):
        r = s.get(f"{API}/render/nonexistent-zzz/provenance", timeout=30)
        assert r.status_code == 404

    def test_cleanup_provenance(self, s, rendered_job_id):
        # rendered_job_id forces fixture to run
        if "prov_pid" in R:
            s.delete(f"{API}/projects/{R['prov_pid']}", timeout=30)
        if "prov_clip_id" in R:
            s.delete(f"{API}/media/{R['prov_clip_id']}", timeout=30)
