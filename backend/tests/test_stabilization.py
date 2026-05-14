"""Iteration-3 stabilisation tests for Tattvashila.

Covers the three new behaviours introduced in the v0.3 hardening pass:
  * Render-queue dedupe — duplicate POST /api/projects/{id}/render returns same job
  * Search result cache — repeat POST /api/retrieval/search marks "cached": true
  * Attribution persistence — MediaAssets after /api/retrieval/assemble have
    provider, provider_external_id, source_url, author when available.
"""
from __future__ import annotations

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

S: dict = {}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# --------------------- Render-queue dedupe ---------------------
class TestRenderQueueDedupe:
    def test_setup_project_with_segments(self, s):
        # Create project
        r = s.post(f"{API}/projects", json={"title": "TEST_RenderDedupe"}, timeout=30)
        assert r.status_code == 200, r.text
        S["project_id"] = r.json()["id"]

        # Upload a clip
        with open("/tmp/test_clip.mp4", "rb") as f:
            r = s.post(
                f"{API}/media/upload",
                data={"kind": "clip"},
                files={"file": ("test_clip.mp4", f, "video/mp4")},
                timeout=60,
            )
        assert r.status_code == 200, r.text
        S["clip_id"] = r.json()["id"]

        # Patch segments + low-res render config for speed
        patch = {
            "segments": [
                {
                    "kind": "clip", "asset_id": S["clip_id"], "duration": 2.0,
                    "transition_in": "fade", "transition_in_duration": 0.3,
                    "start_offset": 0.0,
                },
                {
                    "kind": "clip", "asset_id": S["clip_id"], "duration": 2.0,
                    "transition_in": "crossfade", "transition_in_duration": 0.4,
                    "start_offset": 0.0,
                },
            ],
            "render_config": {
                "width": 480, "height": 270, "fps": 24,
                "video_bitrate": "1200k", "audio_bitrate": "128k",
            },
        }
        r = s.patch(f"{API}/projects/{S['project_id']}", json=patch, timeout=30)
        assert r.status_code == 200

    def test_duplicate_render_returns_same_job(self, s):
        # Fire two POSTs in rapid succession
        r1 = s.post(f"{API}/projects/{S['project_id']}/render", timeout=30)
        assert r1.status_code == 200, r1.text
        r2 = s.post(f"{API}/projects/{S['project_id']}/render", timeout=30)
        assert r2.status_code == 200, r2.text

        job1 = r1.json()
        job2 = r2.json()
        assert job1["id"] == job2["id"], (
            f"Dedupe failed: job1={job1['id']} job2={job2['id']}"
        )
        assert job1["project_id"] == S["project_id"]
        assert job1["status"] in ("queued", "rendering", "completed")
        S["first_job_id"] = job1["id"]

    def test_renders_history_has_only_one_entry(self, s):
        # Allow a brief moment for any race conditions to settle
        time.sleep(1.0)
        r = s.get(f"{API}/projects/{S['project_id']}/renders", timeout=30)
        assert r.status_code == 200
        jobs = r.json()
        # Filter to only the first dedup call cluster (statuses other than 'completed' once)
        active_or_first = [j for j in jobs if j["id"] == S["first_job_id"]]
        assert len(active_or_first) == 1, jobs
        # And only one job exists overall right now
        assert len(jobs) == 1, f"Expected 1 job, got {len(jobs)}: {jobs}"

    def test_fresh_render_after_completion_gets_new_id(self, s):
        # Poll first job until it completes (or fails)
        deadline = time.time() + 180
        last = None
        while time.time() < deadline:
            r = s.get(f"{API}/render/{S['first_job_id']}", timeout=30)
            assert r.status_code == 200
            last = r.json()
            if last["status"] in ("completed", "failed"):
                break
            time.sleep(2)
        assert last and last["status"] == "completed", f"first job not completed: {last}"

        # New render call should produce a NEW job id
        r = s.post(f"{API}/projects/{S['project_id']}/render", timeout=30)
        assert r.status_code == 200
        new_job = r.json()
        assert new_job["id"] != S["first_job_id"], "Second render should not collide"
        S["second_job_id"] = new_job["id"]


# --------------------- Search result cache ---------------------
class TestSearchCache:
    DESC_A = "Rain falling on stone steps in an empty courtyard at dusk"
    DESC_B = "Sunlit dust motes in an abandoned library"

    def test_first_search_is_uncached(self, s):
        r = s.post(
            f"{API}/retrieval/search",
            json={"description": self.DESC_A, "contemplative_mode": True, "per_query": 3},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # First call: either no "cached" key or cached==False
        assert not body.get("cached"), "First search should not be cached"
        assert "clips" in body and isinstance(body["clips"], list)
        S["search_first_clips"] = body["clips"]
        S["search_first_rubric"] = body["rubric"]

    def test_second_search_is_cached_and_fast(self, s):
        t0 = time.perf_counter()
        r = s.post(
            f"{API}/retrieval/search",
            json={"description": self.DESC_A, "contemplative_mode": True, "per_query": 3},
            timeout=30,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("cached") is True, f"Expected cached=true, body keys={list(body)}"
        assert elapsed_ms < 500, f"Cache hit too slow: {elapsed_ms:.0f}ms"
        # Identical clips and rubric
        assert body["clips"] == S["search_first_clips"], "Cached clips differ"
        assert body["rubric"] == S["search_first_rubric"], "Cached rubric differs"

    def test_different_description_does_not_collide(self, s):
        r = s.post(
            f"{API}/retrieval/search",
            json={"description": self.DESC_B, "contemplative_mode": True, "per_query": 3},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # Different description must NOT come from cache
        assert not body.get("cached"), "Different description should not be a cache hit"

    def test_different_contemplative_mode_does_not_collide(self, s):
        # Same description but mode flipped — must not hit prior cache entry
        r = s.post(
            f"{API}/retrieval/search",
            json={"description": self.DESC_A, "contemplative_mode": False, "per_query": 3},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert not body.get("cached"), "Flipping contemplative_mode must invalidate cache key"


# --------------------- Attribution persistence ---------------------
class TestAttributionPersistence:
    SCENE = "Quiet wind moving through tall grass at dusk"

    def test_assemble_and_verify_attribution(self, s):
        # Fresh project
        r = s.post(f"{API}/projects", json={"title": "TEST_Attribution"}, timeout=30)
        assert r.status_code == 200, r.text
        S["attr_project_id"] = r.json()["id"]

        # Search
        r = s.post(
            f"{API}/retrieval/search",
            json={"description": self.SCENE, "contemplative_mode": True, "per_query": 4},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        clips = body["clips"]
        assert len(clips) >= 2, f"Need >=2 clips, got {len(clips)}"
        top = sorted(clips, key=lambda c: c.get("score") or 0, reverse=True)[:2]

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

        # Assemble
        r = s.post(
            f"{API}/retrieval/assemble",
            json={
                "project_id": S["attr_project_id"],
                "selections": selections,
                "pacing": body["rubric"].get("pacing", "slow"),
                "transition": "crossfade",
                "rubric_atmosphere": body["rubric"].get("atmosphere", ""),
            },
            timeout=240,
        )
        assert r.status_code == 200, r.text
        project = r.json()
        S["attr_asset_ids"] = [seg["asset_id"] for seg in project["segments"]]
        S["attr_selections"] = {(sel["provider"], sel["external_id"]): sel for sel in selections}

        # Verify attribution in /api/media
        r = s.get(f"{API}/media?kind=clip", timeout=30)
        assert r.status_code == 200
        by_id = {m["id"]: m for m in r.json()}

        for aid in S["attr_asset_ids"]:
            assert aid in by_id, f"asset {aid} missing from media listing"
            m = by_id[aid]
            assert m.get("provider") in ("pexels", "pixabay"), (
                f"provider null or wrong: {m.get('provider')}"
            )
            assert m.get("provider_external_id"), (
                f"provider_external_id missing for {aid}"
            )
            assert isinstance(m.get("source_url"), str) and m["source_url"], (
                f"source_url empty for {aid}: {m.get('source_url')}"
            )
            assert isinstance(m.get("author"), str) and m["author"].strip(), (
                f"author empty for {aid}: {m.get('author')}"
            )
            # Cross-check it matches a selection
            key = (m["provider"], m["provider_external_id"])
            assert key in S["attr_selections"], f"unexpected media {key}"


# --------------------- Provider retry resilience ---------------------
class TestProviderRetryResilience:
    def test_unusual_keywords_still_return_safely(self, s):
        # Exercise the retry/timeout paths with an odd query. We don't expect
        # zero clips — we expect no 5xx and a well-formed body.
        r = s.post(
            f"{API}/retrieval/search",
            json={
                "description": "Xkjzqp unusual contemplative scene with no real subject",
                "contemplative_mode": False,
                "per_query": 2,
            },
            timeout=180,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "clips" in body and isinstance(body["clips"], list)
        assert "rubric" in body


# --------------------- Cleanup ---------------------
class TestCleanup:
    def test_cleanup(self, s):
        for key in ("project_id", "attr_project_id"):
            pid = S.get(key)
            if pid:
                s.delete(f"{API}/projects/{pid}", timeout=30)
        if S.get("clip_id"):
            s.delete(f"{API}/media/{S['clip_id']}", timeout=30)
