"""End-to-end backend tests for Tattvashila contemplative editing pipeline."""
import os
import time
import subprocess
import json
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Read from frontend env if not in shell
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")
                break

API = f"{BASE_URL}/api"

# Shared state container for sequential test flow
state = {}


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    return sess


# ---------------- Health + metadata ----------------
class TestHealth:
    def test_health(self, s):
        r = s.get(f"{API}/health", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "ok"
        assert data["ambient_presets"] == 6
        for v in ("echo", "sage", "onyx", "fable"):
            assert v in data["voices"], f"voice {v} missing"

    def test_ambient_library(self, s):
        r = s.get(f"{API}/ambient/library", timeout=30)
        assert r.status_code == 200
        presets = r.json()["presets"]
        keys = {p["key"] for p in presets}
        assert keys == {"room_tone", "wind", "rain", "forest", "drone", "paper"}

    def test_narration_voices(self, s):
        r = s.get(f"{API}/narration/voices", timeout=30)
        assert r.status_code == 200
        data = r.json()
        keys = {v["key"] for v in data["voices"]}
        for needed in ("echo", "sage", "onyx", "fable"):
            assert needed in keys, f"voice {needed} not exposed"
        assert isinstance(data["models"], list) and len(data["models"]) >= 1


# ---------------- Projects CRUD ----------------
class TestProjectsCRUD:
    def test_create_project(self, s):
        r = s.post(f"{API}/projects", json={"title": "TEST_Contemplative", "subtitle": "auto"}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["title"] == "TEST_Contemplative"
        assert data["id"]
        assert data["segments"] == []
        state["project_id"] = data["id"]

    def test_list_projects(self, s):
        r = s.get(f"{API}/projects", timeout=30)
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert state["project_id"] in ids

    def test_get_project(self, s):
        r = s.get(f"{API}/projects/{state['project_id']}", timeout=30)
        assert r.status_code == 200
        assert r.json()["title"] == "TEST_Contemplative"

    def test_patch_project_render_config(self, s):
        payload = {
            "render_config": {
                "width": 640, "height": 360, "fps": 24,
                "video_bitrate": "1500k", "audio_bitrate": "128k",
            },
            "grading": {
                "film_grain": True, "grain_intensity": 0.05,
                "muted_palette": True, "saturation": 0.78,
                "warm_highlights": True, "warmth": 0.08, "contrast": 0.95,
            },
        }
        r = s.patch(f"{API}/projects/{state['project_id']}", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["render_config"]["width"] == 640
        assert data["render_config"]["height"] == 360
        assert data["render_config"]["video_bitrate"] == "1500k"

    def test_404_unknown_project(self, s):
        r = s.get(f"{API}/projects/nonexistent-id-xxxx", timeout=30)
        assert r.status_code == 404


# ---------------- Media upload ----------------
class TestMediaUpload:
    def test_upload_clip(self, s):
        with open("/tmp/test_clip.mp4", "rb") as f:
            r = s.post(
                f"{API}/media/upload",
                data={"kind": "clip"},
                files={"file": ("test_clip.mp4", f, "video/mp4")},
                timeout=60,
            )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["kind"] == "clip"
        assert data["width"] == 320
        assert data["height"] == 240
        assert data["duration"] is not None and 2.5 < data["duration"] < 3.5
        assert data["storage_path"]
        state["clip_id"] = data["id"]
        state["clip_storage"] = data["storage_path"]

    def test_list_media(self, s):
        r = s.get(f"{API}/media?kind=clip", timeout=30)
        assert r.status_code == 200
        ids = [m["id"] for m in r.json()]
        assert state["clip_id"] in ids

    def test_serve_file(self, s):
        r = s.get(f"{API}/files/{state['clip_storage']}", timeout=60)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("video/")
        assert len(r.content) > 1000

    def test_invalid_kind(self, s):
        r = s.post(
            f"{API}/media/upload",
            data={"kind": "invalid"},
            files={"file": ("x.mp4", b"\x00\x01\x02", "video/mp4")},
            timeout=30,
        )
        assert r.status_code == 400


# ---------------- TTS (real API call) ----------------
class TestTTS:
    def test_tts_synthesize(self, s):
        r = s.post(
            f"{API}/narration/tts",
            json={"text": "The film begins in silence.", "voice": "echo", "model": "tts-1"},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["kind"] == "narration"
        assert data["content_type"] == "audio/mpeg"
        assert data["size"] > 1000
        assert data["duration"] is not None and data["duration"] > 0.3
        state["narration_id"] = data["id"]
        state["narration_storage"] = data["storage_path"]


# ---------------- Full render pipeline ----------------
class TestRenderFlow:
    def test_build_timeline_and_render(self, s):
        # Build timeline: 1 clip + 1 pause + 1 clip with crossfade
        segments = [
            {"kind": "clip", "asset_id": state["clip_id"], "duration": 2.0,
             "transition_in": "fade", "transition_in_duration": 0.5, "start_offset": 0.0},
            {"kind": "pause", "duration": 0.8, "transition_in": "fade", "transition_in_duration": 0.3},
            {"kind": "clip", "asset_id": state["clip_id"], "duration": 2.0,
             "transition_in": "crossfade", "transition_in_duration": 0.6, "start_offset": 0.0},
        ]
        patch = {
            "segments": segments,
            "narration": {
                "source": "upload", "asset_id": state["narration_id"],
                "offset_seconds": 0.5, "volume": 1.0,
                "tts_text": None, "tts_voice": "echo", "tts_model": "tts-1", "tts_speed": 0.95,
            },
            "ambient": {
                "source": "builtin", "builtin_key": "room_tone",
                "volume": 0.30, "fade_in": 1.0, "fade_out": 1.0,
            },
            "render_config": {
                "width": 640, "height": 360, "fps": 24,
                "video_bitrate": "1500k", "audio_bitrate": "128k",
            },
        }
        r = s.patch(f"{API}/projects/{state['project_id']}", json=patch, timeout=30)
        assert r.status_code == 200, r.text
        assert len(r.json()["segments"]) == 3

        # Start render
        r = s.post(f"{API}/projects/{state['project_id']}/render", timeout=30)
        assert r.status_code == 200, r.text
        job = r.json()
        assert job["status"] in ("queued", "rendering")
        state["job_id"] = job["id"]

        # Poll up to 120s
        deadline = time.time() + 120
        last = None
        while time.time() < deadline:
            r = s.get(f"{API}/render/{state['job_id']}", timeout=30)
            assert r.status_code == 200
            last = r.json()
            if last["status"] == "completed":
                break
            if last["status"] == "failed":
                pytest.fail(f"Render failed: {last.get('error')}")
            time.sleep(2)
        else:
            pytest.fail(f"Render timed out. Last state: {last}")

        assert last["status"] == "completed"
        assert last["output_asset_id"]
        state["output_id"] = last["output_asset_id"]

    def test_download_rendered_mp4(self, s):
        # Find the asset record
        r = s.get(f"{API}/media?kind=render", timeout=30)
        assert r.status_code == 200
        match = next((m for m in r.json() if m["id"] == state["output_id"]), None)
        assert match, "Output asset not in media list"
        path = match["storage_path"]

        r = s.get(f"{API}/files/{path}", timeout=120)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("video/")
        data = r.content
        assert len(data) > 5000

        # Verify it's a valid MP4 via ffprobe
        out_file = "/tmp/rendered_out.mp4"
        with open(out_file, "wb") as f:
            f.write(data)
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json",
             "-show_streams", "-show_format", out_file],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"ffprobe failed: {result.stderr}"
        info = json.loads(result.stdout)
        assert any(st["codec_type"] == "video" for st in info["streams"])
        # Check resolution
        v = next(st for st in info["streams"] if st["codec_type"] == "video")
        assert v["width"] == 640 and v["height"] == 360

    def test_list_renders(self, s):
        r = s.get(f"{API}/projects/{state['project_id']}/renders", timeout=30)
        assert r.status_code == 200
        jobs = r.json()
        ids = [j["id"] for j in jobs]
        assert state["job_id"] in ids
        completed = [j for j in jobs if j["status"] == "completed"]
        assert len(completed) >= 1


# ---------------- Cleanup ----------------
class TestCleanup:
    def test_delete_media(self, s):
        r = s.delete(f"{API}/media/{state['clip_id']}", timeout=30)
        assert r.status_code == 200
        assert r.json()["deleted"] is True

    def test_delete_project(self, s):
        r = s.delete(f"{API}/projects/{state['project_id']}", timeout=30)
        assert r.status_code == 200
        # Verify gone
        r = s.get(f"{API}/projects/{state['project_id']}", timeout=30)
        assert r.status_code == 404
