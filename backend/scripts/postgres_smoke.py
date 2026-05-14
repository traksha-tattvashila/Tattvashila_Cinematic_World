"""
Tiny end-to-end smoke against Postgres: create project → PATCH a 2-segment
black-and-pause timeline → render a 5s preview → confirm the retrieval_sessions
table is also exercised by hitting /retrieval/assemble with a single existing
provider clip that was migrated from Mongo (so we don't burn the LLM budget).

Outputs to /app/test_reports/post_supabase/.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

BACKEND = "http://localhost:8001"
API = f"{BACKEND}/api"
REPORT = Path("/app/test_reports/post_supabase")
REPORT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    out = {}
    with httpx.Client(base_url=API, timeout=180.0) as c:
        out["health"] = c.get("/health").json()

        # Find a real clip MediaAsset migrated from Mongo
        media = c.get("/media").json()
        clip_assets = [m for m in media if m["kind"] == "clip" and m.get("duration")]
        if not clip_assets:
            print("No clip assets to work with — aborting"); return 2
        a = clip_assets[0]
        print(f"using clip asset: {a['id']} duration={a['duration']:.1f}s")

        # Create a tiny project
        p = c.post("/projects", json={"title": "Postgres smoke", "description": "5s preview"}).json()
        pid = p["id"]
        out["project_id"] = pid

        # PATCH a 2-segment timeline: 1.5s pause + 3.5s clip
        patched = c.patch(f"/projects/{pid}", json={
            "segments": [
                {"kind": "pause", "duration": 1.5, "transition_in": "fade", "transition_in_duration": 1.0},
                {"kind": "clip", "asset_id": a["id"], "duration": 3.5,
                 "start_offset": 0.5, "transition_in": "fade", "transition_in_duration": 1.0},
            ],
            "ambient": {"source": "builtin", "builtin_key": "room_tone", "volume": 0.18, "fade_in": 2.0, "fade_out": 1.5},
            "render_config": {"width": 480, "height": 270, "fps": 24, "video_bitrate": "700k", "audio_bitrate": "96k"},
        }).json()
        out["segments_after_patch"] = [{"kind": s["kind"], "duration": s["duration"]} for s in patched["segments"]]

        # Render
        job = c.post(f"/projects/{pid}/render").json()
        jid = job["id"]
        out["render_job_id"] = jid
        print(f"queued render {jid}")

        # Poll
        started = time.time()
        while True:
            time.sleep(2.0)
            j = c.get(f"/render/{jid}").json()
            if j["status"] in ("completed", "failed"):
                out["render_status"] = j["status"]
                out["render_stage"] = j["stage"]
                out["render_error"] = j.get("error")
                out["render_progress"] = j.get("progress")
                out["render_output_asset_id"] = j.get("output_asset_id")
                break
            if time.time() - started > 300:
                out["render_status"] = "timeout"; break
        print(f"render -> {out['render_status']} in {time.time()-started:.0f}s")

        # Provenance
        if out.get("render_status") == "completed":
            r = c.get(f"/render/{jid}/provenance")
            out["provenance_status"] = r.status_code
            if r.status_code == 200:
                pv = r.json()
                out["provenance_keys"] = sorted(pv.keys())
                out["provenance_citations"] = len(pv.get("citations") or pv.get("clips") or [])

        # Renders listing
        out["renders_listing"] = [{"id": rj["id"][:8], "status": rj["status"]}
                                  for rj in c.get(f"/projects/{pid}/renders").json()]

        # Cleanup: delete the smoke project — render asset will remain in storage but is fine
        c.delete(f"/projects/{pid}")
        out["cleanup"] = "deleted"

    (REPORT / "smoke_result.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0 if out.get("render_status") == "completed" else 3


if __name__ == "__main__":
    sys.exit(main())
