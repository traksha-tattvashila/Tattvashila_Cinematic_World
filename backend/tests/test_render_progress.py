"""
Tests for the cinematic render-progress feature.

Verifies:
- POST /api/projects/{id}/render returns RenderJob with queue_position populated
- GET /api/render/{job_id} surfaces queue_position, output_size_bytes, stage, progress
- During a real render the stage progresses through the canonical taxonomy
  (downloading_inputs -> preparing -> composing -> audio_mixing -> encoding ->
   uploading -> finalizing -> completed) AND progress monotonically increases
- On completion, output_size_bytes is a positive integer
- Existing endpoints still work
"""
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
TEST_PROJECT_ID = "4f976224-ebeb-4477-90ef-aa05e2e52e8f"

CANONICAL_STAGES = {
    "queued",
    "downloading_inputs",
    "preparing",
    "composing",
    "audio_mixing",
    "encoding",
    "uploading",
    "finalizing",
    "completed",
}
# Order positions used to verify monotonicity (queued -> ... -> completed)
STAGE_ORDER = [
    "queued",
    "downloading_inputs",
    "preparing",
    "composing",
    "audio_mixing",
    "encoding",
    "uploading",
    "finalizing",
    "completed",
]


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# ---------------- Sanity: existing endpoints still work ----------------
class TestExistingEndpoints:
    def test_health(self, s):
        r = s.get(f"{API}/health", timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_list_projects(self, s):
        r = s.get(f"{API}/projects", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        ids = [p["id"] for p in r.json()]
        assert TEST_PROJECT_ID in ids, "Seed project missing"

    def test_get_project(self, s):
        r = s.get(f"{API}/projects/{TEST_PROJECT_ID}", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == TEST_PROJECT_ID
        assert len(data["segments"]) > 0, "Seed project has no segments"

    def test_list_renders(self, s):
        r = s.get(f"{API}/projects/{TEST_PROJECT_ID}/renders", timeout=30)
        assert r.status_code == 200
        jobs = r.json()
        assert isinstance(jobs, list)
        # Every existing render job has the new fields surfaced
        for j in jobs:
            assert "queue_position" in j
            assert "output_size_bytes" in j
            assert "stage" in j
            assert "progress" in j


# ---------------- Render kickoff: queue_position + fields ----------------
class TestRenderKickoff:
    def test_start_render_returns_queue_position(self, s):
        # If a render is already in-flight, the API may return the existing job
        r = s.post(f"{API}/projects/{TEST_PROJECT_ID}/render", timeout=30)
        assert r.status_code == 200, r.text
        job = r.json()

        # Fields surfaced
        assert "id" in job
        assert "queue_position" in job
        assert "output_size_bytes" in job
        assert "stage" in job
        assert "progress" in job

        # queue_position must be a non-null integer (>= 0)
        assert job["queue_position"] is not None, "queue_position is null"
        assert isinstance(job["queue_position"], int)
        assert job["queue_position"] >= 0

        # status valid
        assert job["status"] in ("queued", "rendering", "completed", "failed")

        pytest.shared_job_id = job["id"]

    def test_get_render_has_all_fields(self, s):
        job_id = getattr(pytest, "shared_job_id", None)
        assert job_id, "No job id from prior test"
        r = s.get(f"{API}/render/{job_id}", timeout=30)
        assert r.status_code == 200
        job = r.json()
        for f in ("queue_position", "output_size_bytes", "stage", "progress", "status"):
            assert f in job, f"Field {f} missing in GET /api/render/{{id}}"
        assert isinstance(job["progress"], (int, float))
        assert 0.0 <= float(job["progress"]) <= 1.0


# ---------------- Stage progression + monotonic progress ----------------
class TestStageProgression:
    def test_render_runs_through_all_stages(self, s):
        """Poll the live render and capture every distinct stage observed.
        Verify (a) all stages observed are in the canonical taxonomy,
        (b) progress is monotonically non-decreasing, and
        (c) on completion output_size_bytes is positive."""
        job_id = getattr(pytest, "shared_job_id", None)
        assert job_id, "No job id"

        observed_stages = []
        progress_seq = []
        deadline = time.time() + 180  # renders are ~90s
        last_status = None
        last_job = None

        while time.time() < deadline:
            r = s.get(f"{API}/render/{job_id}", timeout=30)
            assert r.status_code == 200
            last_job = r.json()
            stage = last_job.get("stage")
            prog = float(last_job.get("progress") or 0.0)
            last_status = last_job.get("status")

            if stage and (not observed_stages or observed_stages[-1] != stage):
                observed_stages.append(stage)
            progress_seq.append(prog)

            if last_status == "completed":
                break
            if last_status == "failed":
                pytest.fail(f"Render failed: {last_job.get('error')}")
            time.sleep(1.5)
        else:
            pytest.fail(f"Render timed out. last={last_job}")

        print(f"Observed stages: {observed_stages}")
        print(f"Progress samples: {len(progress_seq)} min={min(progress_seq)} max={max(progress_seq)}")

        # All observed stages are in the canonical taxonomy
        for st in observed_stages:
            assert st in CANONICAL_STAGES, f"Unknown stage {st!r} not in taxonomy"

        # Final stage is 'completed'
        assert observed_stages[-1] == "completed"

        # We must have seen at least a couple of intermediate stages
        # (At least one of the intermediate stages besides queued/completed)
        intermediates = [s for s in observed_stages if s not in ("queued", "completed")]
        assert len(intermediates) >= 2, (
            f"Expected multiple intermediate stages; saw only {observed_stages}"
        )

        # Order check: indices in STAGE_ORDER should be non-decreasing
        idxs = [STAGE_ORDER.index(st) for st in observed_stages]
        assert idxs == sorted(idxs), f"Stages went backwards: {observed_stages}"

        # Progress monotonic non-decreasing (allow tiny float jitter)
        for a, b in zip(progress_seq, progress_seq[1:]):
            assert b + 1e-6 >= a, f"Progress went backwards: {a} -> {b}"
        assert progress_seq[-1] >= 0.99, f"Final progress not ~1.0: {progress_seq[-1]}"

        # Completion fields
        assert last_job["status"] == "completed"
        assert last_job["output_asset_id"]
        size = last_job.get("output_size_bytes")
        assert isinstance(size, int), f"output_size_bytes not int: {size!r}"
        assert size > 1000, f"output_size_bytes too small: {size}"

    def test_completed_size_matches_mp4(self, s):
        """Verify output_size_bytes equals the actual served file length."""
        job_id = getattr(pytest, "shared_job_id", None)
        r = s.get(f"{API}/render/{job_id}", timeout=30)
        job = r.json()
        size = job["output_size_bytes"]
        output_id = job["output_asset_id"]

        # Look up media record to get storage_path
        r = s.get(f"{API}/media?kind=render", timeout=30)
        match = next((m for m in r.json() if m["id"] == output_id), None)
        assert match, "Output asset missing from media listing"

        r = s.get(f"{API}/files/{match['storage_path']}", timeout=120)
        assert r.status_code == 200
        actual = len(r.content)
        # Allow small tolerance because Content-Length and stored size may differ
        # if backend records pre-upload size. Should be within 5%.
        delta = abs(actual - size)
        assert delta < max(1024, size * 0.05), (
            f"output_size_bytes={size} differs from actual served bytes={actual}"
        )
