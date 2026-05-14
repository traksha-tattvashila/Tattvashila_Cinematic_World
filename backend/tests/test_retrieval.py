"""Backend tests for the Atmospheric Retrieval feature (iteration 2).

Covers:
  * POST /api/retrieval/analyze — Claude rubric generation
  * POST /api/retrieval/search — Pexels+Pixabay search + Claude ranking
  * POST /api/retrieval/assemble — download, store, append timeline segments
  * Smoke: GET /api/health regression
"""
from __future__ import annotations

import os
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

# Shared state between sequential tests
R: dict = {}

SCENE_INSOMNIAC = "Quiet exhausted woman scrolling phone before sunrise"
SCENE_FOREST = "Contemplative forest pathway at dawn"
PACING_VALUES = {"glacial", "slow", "measured"}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# -------- Regression: health --------
class TestRegression:
    def test_health_ok(self, s):
        r = s.get(f"{API}/health", timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# -------- /api/retrieval/analyze --------
class TestAnalyze:
    def test_analyze_contemplative(self, s):
        r = s.post(
            f"{API}/retrieval/analyze",
            json={"description": SCENE_INSOMNIAC, "contemplative_mode": True},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        payload = r.json()
        assert "rubric" in payload
        rub = payload["rubric"]

        # Required fields
        assert isinstance(rub.get("emotional_tone"), str) and rub["emotional_tone"].strip()
        assert rub.get("pacing") in PACING_VALUES, f"pacing={rub.get('pacing')}"
        assert isinstance(rub.get("restraint_level"), (int, float))
        assert rub["restraint_level"] >= 0.7, f"restraint_level={rub['restraint_level']}"

        queries = rub.get("search_queries") or []
        assert isinstance(queries, list)
        assert 3 <= len(queries) <= 5, f"search_queries len={len(queries)}"
        assert all(isinstance(q, str) and q.strip() for q in queries)

        assert isinstance(rub.get("preferred_keywords"), list) and len(rub["preferred_keywords"]) > 0
        assert isinstance(rub.get("rejected_keywords"), list)
        assert isinstance(rub.get("rationale"), str) and rub["rationale"].strip()

        # remember for downstream tests
        R["insomniac_rubric"] = rub


# -------- /api/retrieval/search --------
class TestSearch:
    def test_search_contemplative_filters(self, s):
        r = s.post(
            f"{API}/retrieval/search",
            json={"description": SCENE_INSOMNIAC, "contemplative_mode": True, "per_query": 4},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "rubric" in data and "clips" in data
        clips = data["clips"]
        assert isinstance(clips, list)
        # Should be at least a couple clips for this scene
        assert len(clips) >= 1, f"no clips returned: {data}"

        for c in clips:
            assert c["provider"] in ("pexels", "pixabay")
            assert c["external_id"]
            assert c["download_url"].startswith("https://")
            assert c["download_url"].lower().endswith((".mp4", ".mov")) or "mp4" in c["download_url"].lower()
            assert c["preview_url"].startswith("http")
            assert c["thumbnail_url"].startswith("http")
            assert isinstance(c["duration"], (int, float)) and c["duration"] > 0
            assert c["width"] > 0 and c["height"] > 0
            assert isinstance(c["score"], (int, float))
            assert 0.0 <= c["score"] <= 1.0, f"score out of range: {c['score']}"
            assert c["score"] >= 0.55, f"contemplative filter violated: {c['score']}"
            assert isinstance(c["rationale"], str) and c["rationale"].strip()

        R["contemplative_count"] = len(clips)

    def test_search_open_mode_returns_more(self, s):
        r = s.post(
            f"{API}/retrieval/search",
            json={"description": SCENE_INSOMNIAC, "contemplative_mode": False, "per_query": 4},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        clips = data["clips"]
        assert isinstance(clips, list) and len(clips) > 0
        # No 0.55 threshold in open mode
        # Assert >= contemplative count (hard-filter behaviour)
        assert len(clips) >= R.get("contemplative_count", 0), (
            f"open mode ({len(clips)}) should be >= contemplative ({R.get('contemplative_count')})"
        )

    def test_search_with_precomputed_rubric(self, s):
        rub = R.get("insomniac_rubric")
        assert rub, "previous analyze test must run first"
        r = s.post(
            f"{API}/retrieval/search",
            json={"rubric": rub, "contemplative_mode": True, "per_query": 3},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "clips" in data
        assert isinstance(data["clips"], list)

    def test_search_no_description_no_rubric_400(self, s):
        r = s.post(f"{API}/retrieval/search", json={"contemplative_mode": True}, timeout=30)
        assert r.status_code == 400, r.text


# -------- /api/retrieval/assemble --------
class TestAssemble:
    def test_assemble_appends_segments(self, s):
        # Fresh project
        r = s.post(f"{API}/projects", json={"title": "TEST_RetrievalAssemble"}, timeout=30)
        assert r.status_code == 200, r.text
        proj = r.json()
        assert proj["segments"] == []
        R["project_id"] = proj["id"]

        # Search for forest scene
        r = s.post(
            f"{API}/retrieval/search",
            json={"description": SCENE_FOREST, "contemplative_mode": True, "per_query": 4},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        clips = body["clips"]
        assert len(clips) >= 2, f"need at least 2 clips, got {len(clips)}"
        # Pick top 2 by score (already ranked descending typically)
        top = sorted(clips, key=lambda c: c["score"] or 0, reverse=True)[:2]

        selections = [{
            "provider": c["provider"],
            "external_id": c["external_id"],
            "title": c.get("title", ""),
            "tags": c.get("tags", []),
            "duration": c["duration"],
            "width": c["width"],
            "height": c["height"],
            "download_url": c["download_url"],
            "preview_url": c["preview_url"],
            "thumbnail_url": c["thumbnail_url"],
            "author": c.get("author", ""),
            "source_url": c.get("source_url", ""),
        } for c in top]

        r = s.post(
            f"{API}/retrieval/assemble",
            json={
                "project_id": R["project_id"],
                "selections": selections,
                "pacing": body["rubric"].get("pacing", "slow"),
                "transition": "crossfade",
                "rubric_atmosphere": body["rubric"].get("atmosphere", ""),
            },
            timeout=240,
        )
        assert r.status_code == 200, r.text
        project = r.json()
        assert len(project["segments"]) == 2, project["segments"]

        # Validate segments
        first = True
        for seg in project["segments"]:
            assert seg["kind"] == "clip"
            assert seg["asset_id"]
            assert 4.0 <= seg["duration"] <= 12.0, f"duration out of trim range: {seg['duration']}"
            assert seg["start_offset"] >= 0.0
            if first:
                assert seg["transition_in"] == "fade", f"first should fade: {seg['transition_in']}"
                first = False
            else:
                assert seg["transition_in"] == "crossfade", seg["transition_in"]

        R["asset_ids"] = [s["asset_id"] for s in project["segments"]]

    def test_media_assets_created_with_attribution(self, s):
        r = s.get(f"{API}/media?kind=clip", timeout=30)
        assert r.status_code == 200
        all_clips = r.json()
        by_id = {m["id"]: m for m in all_clips}
        for aid in R["asset_ids"]:
            assert aid in by_id, f"asset {aid} not in media list"
            m = by_id[aid]
            assert m["provider"] in ("pexels", "pixabay"), m
            assert m["provider_external_id"]
            # source_url and author are typically set by providers
            assert m["storage_path"]
            R.setdefault("storage_paths", []).append(m["storage_path"])

    def test_serve_assembled_clip_bytes(self, s):
        path = R["storage_paths"][0]
        r = s.get(f"{API}/files/{path}", timeout=120)
        assert r.status_code == 200
        ct = r.headers.get("content-type", "")
        assert ct.startswith("video/"), ct
        assert len(r.content) > 5000

    def test_assemble_empty_selections_400(self, s):
        r = s.post(
            f"{API}/retrieval/assemble",
            json={"project_id": R["project_id"], "selections": []},
            timeout=30,
        )
        assert r.status_code == 400, r.text

    def test_assemble_unknown_project_404(self, s):
        # Need a minimally-valid selection (won't be downloaded; project lookup happens first)
        sel = {
            "provider": "pexels", "external_id": "x",
            "download_url": "https://example.com/nope.mp4",
            "duration": 5, "width": 100, "height": 100,
        }
        r = s.post(
            f"{API}/retrieval/assemble",
            json={"project_id": "nonexistent-id-zzzz", "selections": [sel]},
            timeout=30,
        )
        assert r.status_code == 404, r.text


# -------- Manual upload regression after retrieval --------
class TestManualUploadRegression:
    def test_manual_upload_still_works(self, s):
        clip_path = Path("/tmp/test_clip.mp4")
        if not clip_path.exists():
            pytest.skip("test_clip.mp4 not present")
        with clip_path.open("rb") as f:
            r = s.post(
                f"{API}/media/upload",
                data={"kind": "clip"},
                files={"file": ("test_clip.mp4", f, "video/mp4")},
                timeout=60,
            )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["kind"] == "clip" and data["duration"] is not None
        R["manual_clip_id"] = data["id"]


# -------- Cleanup --------
class TestCleanup:
    def test_delete_project(self, s):
        if "project_id" in R:
            r = s.delete(f"{API}/projects/{R['project_id']}", timeout=30)
            assert r.status_code in (200, 404)
        if "manual_clip_id" in R:
            s.delete(f"{API}/media/{R['manual_clip_id']}", timeout=30)
