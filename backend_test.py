#!/usr/bin/env python3
"""
LOW-CREDIT END-TO-END VERIFICATION for Tattvashila contemplative cinematic editing.
Sequential critical-path testing with minimal API calls.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Load backend URL from frontend/.env
env_path = Path("/app/frontend/.env")
BACKEND_URL = None
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BACKEND_URL = line.split("=", 1)[1].strip()
            break

if not BACKEND_URL:
    print("❌ REACT_APP_BACKEND_URL not found in /app/frontend/.env")
    sys.exit(1)

# Test results tracking
test_results: List[Dict[str, Any]] = []
bugs: List[str] = []
stability_issues: List[str] = []
render_issues: List[str] = []
retrieval_observations: List[str] = []
deployment_risks: List[str] = []

# Check if external URL is working, fallback to localhost
API_BASE = f"{BACKEND_URL}/api"
print(f"🔗 Backend API: {API_BASE}\n")

try:
    test_resp = requests.get(f"{API_BASE}/health", timeout=5)
    if test_resp.status_code != 200:
        print(f"⚠️  External URL {API_BASE} returned {test_resp.status_code}")
        print(f"⚠️  CRITICAL DEPLOYMENT ISSUE: Kubernetes ingress not routing /api/* to backend")
        print(f"🔗 Falling back to localhost:8001/api for testing\n")
        API_BASE = "http://localhost:8001/api"
        deployment_risks.append("CRITICAL: External URL /api/* routes return 404 — Kubernetes ingress misconfigured")
except Exception as e:
    print(f"⚠️  External URL {API_BASE} unreachable: {e}")
    print(f"⚠️  CRITICAL DEPLOYMENT ISSUE: Kubernetes ingress not routing /api/* to backend")
    print(f"🔗 Falling back to localhost:8001/api for testing\n")
    API_BASE = "http://localhost:8001/api"
    deployment_risks.append("CRITICAL: External URL /api/* routes unreachable — Kubernetes ingress misconfigured")

# Shared state
project_id: Optional[str] = None
rubric: Optional[dict] = None
clips: List[dict] = []
tts_asset_id: Optional[str] = None
render_job_id: Optional[str] = None


def log_result(step: str, passed: bool, details: str = "") -> None:
    """Record test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} — {step}")
    if details:
        print(f"    {details}")
    test_results.append({"step": step, "passed": passed, "details": details})


def log_bug(bug: str) -> None:
    """Record a discovered bug."""
    bugs.append(bug)
    print(f"🐛 BUG: {bug}")


def log_stability(issue: str) -> None:
    """Record a stability issue."""
    stability_issues.append(issue)
    print(f"⚠️  STABILITY: {issue}")


def log_render_issue(issue: str) -> None:
    """Record a render issue."""
    render_issues.append(issue)
    print(f"🎬 RENDER: {issue}")


def log_retrieval(observation: str) -> None:
    """Record a retrieval quality observation."""
    retrieval_observations.append(observation)
    print(f"🔍 RETRIEVAL: {observation}")


def log_deployment_risk(risk: str) -> None:
    """Record a deployment risk."""
    deployment_risks.append(risk)
    print(f"⚡ DEPLOYMENT RISK: {risk}")


# ---------------------------------------------------------------------------
# Step 1: Health & metadata endpoints
# ---------------------------------------------------------------------------
def test_health_endpoints() -> bool:
    """Test GET /api/health, /api/ambient/library, /api/narration/voices."""
    print("\n" + "=" * 80)
    print("STEP 1: Health & Metadata Endpoints")
    print("=" * 80)
    
    all_passed = True
    
    # /api/health
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "status" in data and "ambient_presets" in data and "voices" in data:
                log_result("GET /api/health", True, f"status={data['status']}, presets={data['ambient_presets']}, voices={len(data['voices'])}")
            else:
                log_result("GET /api/health", False, f"Missing expected fields: {data}")
                log_bug("/api/health missing expected schema fields")
                all_passed = False
        else:
            log_result("GET /api/health", False, f"HTTP {resp.status_code}")
            log_bug(f"/api/health returned {resp.status_code}")
            all_passed = False
    except Exception as e:
        log_result("GET /api/health", False, str(e))
        log_bug(f"/api/health exception: {e}")
        all_passed = False
    
    # /api/ambient/library
    try:
        resp = requests.get(f"{API_BASE}/ambient/library", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "presets" in data and isinstance(data["presets"], list):
                log_result("GET /api/ambient/library", True, f"{len(data['presets'])} presets available")
                if len(data["presets"]) == 0:
                    log_deployment_risk("No ambient presets available — ambient_library.ensure_ambient_assets() may have failed")
            else:
                log_result("GET /api/ambient/library", False, f"Invalid schema: {data}")
                log_bug("/api/ambient/library missing 'presets' array")
                all_passed = False
        else:
            log_result("GET /api/ambient/library", False, f"HTTP {resp.status_code}")
            log_bug(f"/api/ambient/library returned {resp.status_code}")
            all_passed = False
    except Exception as e:
        log_result("GET /api/ambient/library", False, str(e))
        log_bug(f"/api/ambient/library exception: {e}")
        all_passed = False
    
    # /api/narration/voices
    try:
        resp = requests.get(f"{API_BASE}/narration/voices", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "voices" in data and "models" in data:
                log_result("GET /api/narration/voices", True, f"{len(data['voices'])} voices, {len(data['models'])} models")
            else:
                log_result("GET /api/narration/voices", False, f"Invalid schema: {data}")
                log_bug("/api/narration/voices missing expected fields")
                all_passed = False
        else:
            log_result("GET /api/narration/voices", False, f"HTTP {resp.status_code}")
            log_bug(f"/api/narration/voices returned {resp.status_code}")
            all_passed = False
    except Exception as e:
        log_result("GET /api/narration/voices", False, str(e))
        log_bug(f"/api/narration/voices exception: {e}")
        all_passed = False
    
    return all_passed


# ---------------------------------------------------------------------------
# Step 2: Project CRUD
# ---------------------------------------------------------------------------
def test_project_crud() -> bool:
    """Test POST /api/projects → GET /api/projects/{id}."""
    global project_id
    
    print("\n" + "=" * 80)
    print("STEP 2: Project CRUD")
    print("=" * 80)
    
    # Create project
    try:
        payload = {
            "title": "LOW-CREDIT E2E Test",
            "subtitle": "Contemplative verification",
            "description": "A still morning over a misty river, slow light."
        }
        resp = requests.post(f"{API_BASE}/projects", json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "id" in data and "title" in data:
                project_id = data["id"]
                log_result("POST /api/projects", True, f"project_id={project_id}")
            else:
                log_result("POST /api/projects", False, f"Missing 'id' in response: {data}")
                log_bug("POST /api/projects missing 'id' field")
                return False
        else:
            log_result("POST /api/projects", False, f"HTTP {resp.status_code}: {resp.text}")
            log_bug(f"POST /api/projects returned {resp.status_code}")
            return False
    except Exception as e:
        log_result("POST /api/projects", False, str(e))
        log_bug(f"POST /api/projects exception: {e}")
        return False
    
    # Fetch project
    try:
        resp = requests.get(f"{API_BASE}/projects/{project_id}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("id") == project_id and data.get("title") == payload["title"]:
                log_result("GET /api/projects/{id}", True, "Project persisted correctly")
                return True
            else:
                log_result("GET /api/projects/{id}", False, f"Data mismatch: {data}")
                log_bug("GET /api/projects/{id} returned incorrect data")
                return False
        else:
            log_result("GET /api/projects/{id}", False, f"HTTP {resp.status_code}")
            log_bug(f"GET /api/projects/{{id}} returned {resp.status_code}")
            return False
    except Exception as e:
        log_result("GET /api/projects/{id}", False, str(e))
        log_bug(f"GET /api/projects/{{id}} exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Step 3: Atmospheric retrieval analyze
# ---------------------------------------------------------------------------
def test_retrieval_analyze() -> bool:
    """Test POST /api/retrieval/analyze."""
    global rubric
    
    print("\n" + "=" * 80)
    print("STEP 3: Atmospheric Retrieval Analyze")
    print("=" * 80)
    
    try:
        payload = {
            "description": "A still morning over a misty river, slow light.",
            "contemplative_mode": True,
            "narration_text": None
        }
        start = time.time()
        resp = requests.post(f"{API_BASE}/retrieval/analyze", json=payload, timeout=60)
        latency = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            if "rubric" in data:
                rubric = data["rubric"]
                required_fields = ["emotional_tone", "pacing", "environment", "atmosphere", "restraint_level", "search_queries"]
                missing = [f for f in required_fields if f not in rubric]
                if missing:
                    log_result("POST /api/retrieval/analyze", False, f"Missing rubric fields: {missing}")
                    log_bug(f"Rubric missing fields: {missing}")
                    return False
                
                log_result("POST /api/retrieval/analyze", True, f"Rubric generated in {latency:.1f}s")
                log_retrieval(f"Rubric emotional_tone={rubric.get('emotional_tone')}, pacing={rubric.get('pacing')}, restraint={rubric.get('restraint_level')}")
                log_retrieval(f"Search queries: {rubric.get('search_queries')}")
                
                if latency > 15:
                    log_stability(f"Scene analysis took {latency:.1f}s (>15s threshold)")
                
                return True
            else:
                log_result("POST /api/retrieval/analyze", False, f"Missing 'rubric' in response: {data}")
                log_bug("POST /api/retrieval/analyze missing 'rubric' field")
                return False
        else:
            log_result("POST /api/retrieval/analyze", False, f"HTTP {resp.status_code}: {resp.text}")
            log_bug(f"POST /api/retrieval/analyze returned {resp.status_code}")
            return False
    except Exception as e:
        log_result("POST /api/retrieval/analyze", False, str(e))
        log_bug(f"POST /api/retrieval/analyze exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Step 4: Atmospheric retrieval search
# ---------------------------------------------------------------------------
def test_retrieval_search() -> bool:
    """Test POST /api/retrieval/search with per_provider_limit=2."""
    global clips
    
    print("\n" + "=" * 80)
    print("STEP 4: Atmospheric Retrieval Search")
    print("=" * 80)
    
    if not rubric:
        log_result("POST /api/retrieval/search", False, "No rubric from previous step")
        return False
    
    try:
        payload = {
            "rubric": rubric,
            "contemplative_mode": True,
            "narration_text": None,
            "per_query": 2  # Minimal retrieval
        }
        start = time.time()
        resp = requests.post(f"{API_BASE}/retrieval/search", json=payload, timeout=90)
        latency = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            if "clips" in data:
                clips = data["clips"]
                log_result("POST /api/retrieval/search", True, f"{len(clips)} clips retrieved in {latency:.1f}s")
                
                if len(clips) == 0:
                    log_retrieval("No clips returned — may indicate provider issues or overly strict filtering")
                    log_deployment_risk("Zero clips returned from search — check provider API keys and filtering logic")
                    return False
                
                # Verify attribution fields
                attribution_fields = ["provider", "external_id", "source_url", "author"]
                for i, clip in enumerate(clips[:3]):  # Check first 3
                    missing = [f for f in attribution_fields if f not in clip or not clip[f]]
                    if missing:
                        log_retrieval(f"Clip {i} missing attribution: {missing}")
                        log_bug(f"Clip missing attribution fields: {missing}")
                    else:
                        log_retrieval(f"Clip {i}: {clip['provider']}/{clip['external_id']} by {clip['author']}")
                
                # Check ranking
                if "score" in clips[0]:
                    scores = [c.get("score", 0) for c in clips]
                    if scores != sorted(scores, reverse=True):
                        log_retrieval("Clips not sorted by score descending")
                        log_bug("Clips not properly ranked by score")
                
                if latency > 30:
                    log_stability(f"Retrieval search took {latency:.1f}s (>30s threshold)")
                
                return True
            else:
                log_result("POST /api/retrieval/search", False, f"Missing 'clips' in response: {data}")
                log_bug("POST /api/retrieval/search missing 'clips' field")
                return False
        else:
            log_result("POST /api/retrieval/search", False, f"HTTP {resp.status_code}: {resp.text}")
            log_bug(f"POST /api/retrieval/search returned {resp.status_code}")
            return False
    except Exception as e:
        log_result("POST /api/retrieval/search", False, str(e))
        log_bug(f"POST /api/retrieval/search exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Step 5: Retrieval assemble
# ---------------------------------------------------------------------------
def test_retrieval_assemble() -> bool:
    """Test POST /api/retrieval/assemble importing 1-2 clips."""
    print("\n" + "=" * 80)
    print("STEP 5: Retrieval Assemble")
    print("=" * 80)
    
    if not project_id:
        log_result("POST /api/retrieval/assemble", False, "No project_id")
        return False
    
    if not clips:
        log_result("POST /api/retrieval/assemble", False, "No clips to assemble")
        return False
    
    try:
        # Select top 2 clips (or 1 if only 1 available)
        selections = []
        for clip in clips[:2]:
            selections.append({
                "provider": clip["provider"],
                "external_id": clip["external_id"],
                "title": clip.get("title", ""),
                "tags": clip.get("tags", []),
                "duration": clip.get("duration", 0),
                "width": clip.get("width", 0),
                "height": clip.get("height", 0),
                "download_url": clip["download_url"],
                "preview_url": clip.get("preview_url", ""),
                "thumbnail_url": clip.get("thumbnail_url", ""),
                "author": clip.get("author", ""),
                "source_url": clip.get("source_url", ""),
            })
        
        payload = {
            "project_id": project_id,
            "selections": selections,
            "pacing": "slow",
            "transition": "crossfade",
            "rubric_atmosphere": rubric.get("atmosphere", "") if rubric else "",
            "rubric": rubric
        }
        
        start = time.time()
        resp = requests.post(f"{API_BASE}/retrieval/assemble", json=payload, timeout=120)
        latency = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            if "segments" in data and len(data["segments"]) > 0:
                log_result("POST /api/retrieval/assemble", True, f"{len(data['segments'])} segments imported in {latency:.1f}s")
                
                if latency > 60:
                    log_stability(f"Assemble took {latency:.1f}s (>60s threshold)")
                
                return True
            else:
                log_result("POST /api/retrieval/assemble", False, f"No segments in project: {data}")
                log_bug("POST /api/retrieval/assemble did not create segments")
                return False
        else:
            log_result("POST /api/retrieval/assemble", False, f"HTTP {resp.status_code}: {resp.text}")
            log_bug(f"POST /api/retrieval/assemble returned {resp.status_code}")
            return False
    except Exception as e:
        log_result("POST /api/retrieval/assemble", False, str(e))
        log_bug(f"POST /api/retrieval/assemble exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Step 6: Verify attribution persistence
# ---------------------------------------------------------------------------
def test_attribution_persistence() -> bool:
    """Test GET /api/media to verify attribution fields persisted."""
    print("\n" + "=" * 80)
    print("STEP 6: Attribution Persistence Check")
    print("=" * 80)
    
    try:
        resp = requests.get(f"{API_BASE}/media?kind=clip", timeout=10)
        if resp.status_code == 200:
            media_assets = resp.json()
            if not media_assets:
                log_result("GET /api/media (attribution)", False, "No clip assets found")
                log_bug("No MediaAssets with kind=clip after assemble")
                return False
            
            attribution_fields = ["provider", "provider_external_id", "source_url", "author"]
            all_good = True
            for asset in media_assets[:2]:  # Check first 2
                missing = [f for f in attribution_fields if not asset.get(f)]
                if missing:
                    log_result("GET /api/media (attribution)", False, f"Asset {asset.get('id')} missing: {missing}")
                    log_bug(f"MediaAsset missing attribution fields: {missing} (file: /app/backend/services/retrieval_service.py)")
                    all_good = False
                else:
                    log_result("GET /api/media (attribution)", True, f"Asset {asset['id']}: {asset['provider']}/{asset['provider_external_id']}")
            
            return all_good
        else:
            log_result("GET /api/media (attribution)", False, f"HTTP {resp.status_code}")
            log_bug(f"GET /api/media returned {resp.status_code}")
            return False
    except Exception as e:
        log_result("GET /api/media (attribution)", False, str(e))
        log_bug(f"GET /api/media exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Step 7: TTS narration generation
# ---------------------------------------------------------------------------
def test_tts_narration() -> bool:
    """Test POST /api/narration/tts with short text."""
    global tts_asset_id
    
    print("\n" + "=" * 80)
    print("STEP 7: TTS Narration Generation")
    print("=" * 80)
    
    try:
        # Get cheapest voice/model
        voices_resp = requests.get(f"{API_BASE}/narration/voices", timeout=10)
        if voices_resp.status_code != 200:
            log_result("POST /api/narration/tts", False, "Could not fetch voices")
            return False
        
        voices_data = voices_resp.json()
        voice = voices_data["voices"][0]["key"] if voices_data["voices"] else "echo"
        model = voices_data["models"][0] if voices_data["models"] else "tts-1"
        
        payload = {
            "text": "Stillness, before the day begins.",
            "voice": voice,
            "model": model,
            "speed": 0.95
        }
        
        start = time.time()
        resp = requests.post(f"{API_BASE}/narration/tts", json=payload, timeout=60)
        latency = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            if "id" in data and "content_type" in data and "size" in data:
                tts_asset_id = data["id"]
                if "audio" not in data["content_type"]:
                    log_result("POST /api/narration/tts", False, f"Invalid content_type: {data['content_type']}")
                    log_bug(f"TTS returned non-audio content_type: {data['content_type']}")
                    return False
                
                if data["size"] == 0:
                    log_result("POST /api/narration/tts", False, "TTS asset has zero size")
                    log_bug("TTS MediaAsset has size=0")
                    return False
                
                log_result("POST /api/narration/tts", True, f"asset_id={tts_asset_id}, size={data['size']} bytes, latency={latency:.1f}s")
                
                if latency > 20:
                    log_stability(f"TTS generation took {latency:.1f}s (>20s threshold)")
                
                return True
            else:
                log_result("POST /api/narration/tts", False, f"Missing fields in response: {data}")
                log_bug("POST /api/narration/tts missing expected fields")
                return False
        else:
            log_result("POST /api/narration/tts", False, f"HTTP {resp.status_code}: {resp.text}")
            log_bug(f"POST /api/narration/tts returned {resp.status_code}")
            return False
    except Exception as e:
        log_result("POST /api/narration/tts", False, str(e))
        log_bug(f"POST /api/narration/tts exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Step 8: Attach TTS + ambient + trim segments
# ---------------------------------------------------------------------------
def test_project_update() -> bool:
    """Test PATCH /api/projects/{id} to attach TTS, ambient, and trim segments to ≤4s."""
    print("\n" + "=" * 80)
    print("STEP 8: Project Update (TTS + Ambient + Trim)")
    print("=" * 80)
    
    if not project_id or not tts_asset_id:
        log_result("PATCH /api/projects/{id}", False, "Missing project_id or tts_asset_id")
        return False
    
    try:
        # Get current project
        proj_resp = requests.get(f"{API_BASE}/projects/{project_id}", timeout=10)
        if proj_resp.status_code != 200:
            log_result("PATCH /api/projects/{id}", False, "Could not fetch project")
            return False
        
        project = proj_resp.json()
        segments = project.get("segments", [])
        
        # Trim segments to total ≤4s
        target_total = 4.0
        if segments:
            per_segment = target_total / len(segments)
            for seg in segments:
                seg["duration"] = min(per_segment, seg.get("duration", 6.0))
        
        # Get first ambient preset
        ambient_resp = requests.get(f"{API_BASE}/ambient/library", timeout=10)
        if ambient_resp.status_code != 200:
            log_result("PATCH /api/projects/{id}", False, "Could not fetch ambient library")
            return False
        
        ambient_data = ambient_resp.json()
        ambient_key = ambient_data["presets"][0]["key"] if ambient_data["presets"] else None
        
        if not ambient_key:
            log_deployment_risk("No ambient presets available for attachment")
        
        # Update project
        payload = {
            "segments": segments,
            "narration": {
                "source": "tts",
                "asset_id": tts_asset_id,
                "tts_text": "Stillness, before the day begins.",
                "tts_voice": "echo",
                "tts_model": "tts-1",
                "offset_seconds": 0.5,
                "volume": 1.0
            },
            "ambient": {
                "source": "builtin",
                "builtin_key": ambient_key,
                "volume": 0.30,
                "fade_in": 1.0,
                "fade_out": 1.0
            } if ambient_key else {"source": "none"},
            "render_config": {
                "width": 640,
                "height": 360,
                "fps": 24,
                "video_bitrate": "1000k",
                "audio_bitrate": "128k"
            }
        }
        
        resp = requests.patch(f"{API_BASE}/projects/{project_id}", json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            total_duration = sum(s.get("duration", 0) for s in data.get("segments", []))
            log_result("PATCH /api/projects/{id}", True, f"Updated: {len(data.get('segments', []))} segments, total={total_duration:.1f}s")
            
            if total_duration > 4.5:
                log_result("Segment trim", False, f"Total duration {total_duration:.1f}s exceeds 4s target")
                log_bug("Segment trimming did not achieve ≤4s total duration")
            
            return True
        else:
            log_result("PATCH /api/projects/{id}", False, f"HTTP {resp.status_code}: {resp.text}")
            log_bug(f"PATCH /api/projects/{{id}} returned {resp.status_code}")
            return False
    except Exception as e:
        log_result("PATCH /api/projects/{id}", False, str(e))
        log_bug(f"PATCH /api/projects/{{id}} exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Step 9: Render
# ---------------------------------------------------------------------------
def test_render() -> bool:
    """Test POST /api/projects/{id}/render and poll until completion."""
    global render_job_id
    
    print("\n" + "=" * 80)
    print("STEP 9: Render (Preview 640)")
    print("=" * 80)
    
    if not project_id:
        log_result("POST /api/projects/{id}/render", False, "No project_id")
        return False
    
    try:
        # Start render
        start = time.time()
        resp = requests.post(f"{API_BASE}/projects/{project_id}/render", timeout=10)
        if resp.status_code != 200:
            log_result("POST /api/projects/{id}/render", False, f"HTTP {resp.status_code}: {resp.text}")
            log_bug(f"POST /api/projects/{{id}}/render returned {resp.status_code}")
            return False
        
        job = resp.json()
        render_job_id = job["id"]
        log_result("POST /api/projects/{id}/render", True, f"job_id={render_job_id}")
        
        # Poll for completion (2s interval, 60s timeout)
        timeout = 60
        interval = 2
        elapsed = 0
        
        while elapsed < timeout:
            time.sleep(interval)
            elapsed += interval
            
            poll_resp = requests.get(f"{API_BASE}/render/{render_job_id}", timeout=10)
            if poll_resp.status_code != 200:
                log_result("GET /api/render/{job_id}", False, f"HTTP {poll_resp.status_code}")
                log_bug(f"GET /api/render/{{job_id}} returned {poll_resp.status_code}")
                return False
            
            job_status = poll_resp.json()
            status = job_status.get("status")
            progress = job_status.get("progress", 0)
            stage = job_status.get("stage", "")
            
            print(f"    Render status: {status} ({progress*100:.0f}%) — {stage} [{elapsed}s elapsed]")
            
            if status == "completed":
                total_time = time.time() - start
                log_result("Render completion", True, f"Completed in {total_time:.1f}s")
                
                # Verify output URL
                output_asset_id = job_status.get("output_asset_id")
                if not output_asset_id:
                    log_result("Render output", False, "No output_asset_id in completed job")
                    log_bug("Completed render job missing output_asset_id")
                    return False
                
                # Get asset to find storage URL
                asset_resp = requests.get(f"{API_BASE}/media", timeout=10)
                if asset_resp.status_code == 200:
                    assets = asset_resp.json()
                    render_asset = next((a for a in assets if a["id"] == output_asset_id), None)
                    if render_asset:
                        storage_path = render_asset.get("storage_path")
                        if storage_path:
                            # HEAD check the file
                            file_url = f"{API_BASE}/files/{storage_path}"
                            head_resp = requests.head(file_url, timeout=10)
                            if head_resp.status_code == 200:
                                log_result("Render output reachable", True, f"HEAD {file_url} → 200")
                                
                                # Check content-length
                                content_length = head_resp.headers.get("content-length")
                                if content_length:
                                    size_mb = int(content_length) / (1024 * 1024)
                                    log_render_issue(f"Render output size: {size_mb:.2f} MB")
                                    if size_mb > 10:
                                        log_render_issue(f"Render output unexpectedly large for 4s @ 640x360")
                            else:
                                log_result("Render output reachable", False, f"HEAD {file_url} → {head_resp.status_code}")
                                log_bug(f"Render output URL not reachable: {file_url}")
                        else:
                            log_result("Render output", False, "No storage_path in render asset")
                            log_bug("Render MediaAsset missing storage_path")
                    else:
                        log_result("Render output", False, f"Asset {output_asset_id} not found in /api/media")
                        log_bug("Render output_asset_id not found in media assets")
                
                return True
            
            elif status == "failed":
                error = job_status.get("error", "Unknown error")
                log_result("Render completion", False, f"Render failed: {error}")
                log_bug(f"Render failed: {error} (file: /app/backend/pipeline/renderer.py)")
                return False
        
        # Timeout
        log_result("Render completion", False, f"Render did not complete within {timeout}s")
        log_stability(f"Render exceeded {timeout}s timeout")
        log_deployment_risk("Render queue may be blocking or renderer is too slow for production")
        return False
        
    except Exception as e:
        log_result("Render", False, str(e))
        log_bug(f"Render exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Step 10: List renders
# ---------------------------------------------------------------------------
def test_list_renders() -> bool:
    """Test GET /api/projects/{id}/renders."""
    print("\n" + "=" * 80)
    print("STEP 10: List Renders")
    print("=" * 80)
    
    if not project_id or not render_job_id:
        log_result("GET /api/projects/{id}/renders", False, "Missing project_id or render_job_id")
        return False
    
    try:
        resp = requests.get(f"{API_BASE}/projects/{project_id}/renders", timeout=10)
        if resp.status_code == 200:
            renders = resp.json()
            if any(r["id"] == render_job_id for r in renders):
                log_result("GET /api/projects/{id}/renders", True, f"{len(renders)} render(s) listed, including job {render_job_id}")
                return True
            else:
                log_result("GET /api/projects/{id}/renders", False, f"Render job {render_job_id} not in list")
                log_bug("Render job not appearing in project renders list")
                return False
        else:
            log_result("GET /api/projects/{id}/renders", False, f"HTTP {resp.status_code}")
            log_bug(f"GET /api/projects/{{id}}/renders returned {resp.status_code}")
            return False
    except Exception as e:
        log_result("GET /api/projects/{id}/renders", False, str(e))
        log_bug(f"GET /api/projects/{{id}}/renders exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Generate QA Report
# ---------------------------------------------------------------------------
def generate_qa_report() -> None:
    """Generate comprehensive QA report."""
    print("\n" + "=" * 80)
    print("QA REPORT")
    print("=" * 80)
    
    # Summary
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    print(f"\n📊 SUMMARY: {passed}/{total} tests passed\n")
    
    # Critical path results
    print("🔍 CRITICAL PATH RESULTS:")
    for i, result in enumerate(test_results, 1):
        status = "✅" if result["passed"] else "❌"
        print(f"  {status} {result['step']}")
        if result["details"]:
            print(f"      {result['details']}")
    
    # Bugs
    print(f"\n🐛 DISCOVERED BUGS ({len(bugs)}):")
    if bugs:
        for bug in bugs:
            print(f"  - {bug}")
    else:
        print("  None")
    
    # Stability issues
    print(f"\n⚠️  STABILITY ISSUES ({len(stability_issues)}):")
    if stability_issues:
        for issue in stability_issues:
            print(f"  - {issue}")
    else:
        print("  None")
    
    # Render issues
    print(f"\n🎬 RENDER ISSUES ({len(render_issues)}):")
    if render_issues:
        for issue in render_issues:
            print(f"  - {issue}")
    else:
        print("  None")
    
    # Retrieval observations
    print(f"\n🔍 RETRIEVAL QUALITY ({len(retrieval_observations)}):")
    if retrieval_observations:
        for obs in retrieval_observations:
            print(f"  - {obs}")
    else:
        print("  None")
    
    # Deployment risks
    print(f"\n⚡ DEPLOYMENT RISKS ({len(deployment_risks)}):")
    if deployment_risks:
        for risk in deployment_risks:
            print(f"  - {risk}")
    else:
        print("  None")
    
    # Write report to file
    report_dir = Path("/app/test_reports")
    report_dir.mkdir(exist_ok=True)
    
    report_path = report_dir / "e2e_qa_report.md"
    with open(report_path, "w") as f:
        f.write("# Tattvashila LOW-CREDIT E2E QA Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Tests Passed:** {passed}/{total}\n")
        f.write(f"- **Bugs Found:** {len(bugs)}\n")
        f.write(f"- **Stability Issues:** {len(stability_issues)}\n")
        f.write(f"- **Render Issues:** {len(render_issues)}\n")
        f.write(f"- **Deployment Risks:** {len(deployment_risks)}\n\n")
        
        f.write("## Critical Path Results\n\n")
        for result in test_results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            f.write(f"- **{status}** — {result['step']}\n")
            if result["details"]:
                f.write(f"  - {result['details']}\n")
        
        f.write("\n## Discovered Bugs\n\n")
        if bugs:
            for bug in bugs:
                f.write(f"- {bug}\n")
        else:
            f.write("None\n")
        
        f.write("\n## Stability Issues\n\n")
        if stability_issues:
            for issue in stability_issues:
                f.write(f"- {issue}\n")
        else:
            f.write("None\n")
        
        f.write("\n## Render Issues\n\n")
        if render_issues:
            for issue in render_issues:
                f.write(f"- {issue}\n")
        else:
            f.write("None\n")
        
        f.write("\n## Retrieval Quality Observations\n\n")
        if retrieval_observations:
            for obs in retrieval_observations:
                f.write(f"- {obs}\n")
        else:
            f.write("None\n")
        
        f.write("\n## Deployment Risks\n\n")
        if deployment_risks:
            for risk in deployment_risks:
                f.write(f"- {risk}\n")
        else:
            f.write("None\n")
    
    print(f"\n📄 Full report written to: {report_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    """Run all tests sequentially."""
    print("=" * 80)
    print("TATTVASHILA LOW-CREDIT E2E VERIFICATION")
    print("=" * 80)
    
    # Run tests in sequence
    test_health_endpoints()
    
    if not test_project_crud():
        print("\n❌ Project CRUD failed — cannot continue")
        generate_qa_report()
        sys.exit(1)
    
    if not test_retrieval_analyze():
        print("\n❌ Retrieval analyze failed — cannot continue")
        generate_qa_report()
        sys.exit(1)
    
    if not test_retrieval_search():
        print("\n❌ Retrieval search failed — cannot continue")
        generate_qa_report()
        sys.exit(1)
    
    if not test_retrieval_assemble():
        print("\n❌ Retrieval assemble failed — cannot continue")
        generate_qa_report()
        sys.exit(1)
    
    test_attribution_persistence()
    
    if not test_tts_narration():
        print("\n⚠️  TTS narration failed — continuing with render test")
    
    test_project_update()
    
    if not test_render():
        print("\n❌ Render failed")
    
    test_list_renders()
    
    # Generate final report
    generate_qa_report()
    
    # Exit with appropriate code
    if all(r["passed"] for r in test_results):
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
