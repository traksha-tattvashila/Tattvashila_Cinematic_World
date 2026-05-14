"""Tattvashila — Contemplative Cinematic Assembly (Supabase Postgres backend)

This is the same FastAPI surface as before — every endpoint preserved byte-for-
byte at the API layer — but the persistence substrate has been swapped from
MongoDB to Supabase Postgres via SQLAlchemy async + asyncpg.

Object storage (clips/renders/audio bytes) still lives on Emergent Object
Storage; only metadata moved.
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import (APIRouter, BackgroundTasks, Depends, FastAPI, File, Form,
                     HTTPException, Response, UploadFile)
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv(Path(__file__).resolve().parent / ".env")

import ambient_library
import narration
import repositories as repo
import retrieval
import storage
from database import dispose, get_session
from models import (AmbientConfig, AnalyzeSceneRequest, AssembleRequest,
                    GradingConfig, MediaAsset, NarrationConfig, Project,
                    ProjectCreate, ProjectUpdate, ProviderClipModel,
                    RenderConfig, RenderJob, SearchRequest,
                    TTSGenerateRequest)
from pipeline.renderer import (RenderContext, probe_duration, probe_resolution,
                               render_project)
from services.provenance_service import (build_provenance, provenance_to_json,
                                          render_provenance_text)
from services.retrieval_service import (build_retrieval_segment,
                                        import_stock_clip)
from services.render_service import (cleanup_paths, find_active_render,
                                     load_render_inputs, upload_render_output)
from utils.cache import TTLCache

app = FastAPI(title="Tattvashila", version="0.2.0")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("tattvashila")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def _startup() -> None:
    try:
        storage.init_storage()
    except Exception as e:  # noqa: BLE001
        logger.error("Object storage init failed: %s", e)
    try:
        ambient_library.ensure_ambient_assets()
    except Exception as e:  # noqa: BLE001
        logger.error("Ambient asset generation failed: %s", e)


@app.on_event("shutdown")
async def _shutdown() -> None:
    await dispose()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@api.get("/")
async def root() -> dict:
    return {"name": "Tattvashila", "tagline": "Contemplative cinematic assembly"}


@api.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "ambient_presets": len(ambient_library.list_presets()),
        "voices": [v["key"] for v in narration.CINEMATIC_VOICES],
    }


# ---------------------------------------------------------------------------
# Ambient & narration metadata
# ---------------------------------------------------------------------------
@api.get("/ambient/library")
async def ambient_library_route() -> dict:
    return {"presets": ambient_library.list_presets()}


@api.get("/ambient/preview/{key}")
async def ambient_preview(key: str):
    path = ambient_library.preset_path(key)
    if not path:
        raise HTTPException(404, "Unknown ambient preset")
    return FileResponse(str(path), media_type="audio/mpeg")


@api.get("/narration/voices")
async def narration_voices() -> dict:
    return {
        "voices": narration.CINEMATIC_VOICES,
        "models": narration.TTS_MODELS,
    }


# ---------------------------------------------------------------------------
# Media uploads
# ---------------------------------------------------------------------------
ALLOWED_KINDS = {"clip", "narration", "ambient"}
MAX_BYTES = 500 * 1024 * 1024  # 500MB


@api.post("/media/upload", response_model=MediaAsset)
async def upload_media(
    kind: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> MediaAsset:
    if kind not in ALLOWED_KINDS:
        raise HTTPException(400, f"kind must be one of {sorted(ALLOWED_KINDS)}")

    data = await file.read()
    if len(data) == 0:
        raise HTTPException(400, "Empty upload")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 500MB)")

    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    file_id = str(uuid.uuid4())
    path = storage.build_path(kind, file_id, ext)
    content_type = file.content_type or "application/octet-stream"
    result = storage.put_object(path, data, content_type)

    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        duration = probe_duration(tmp_path)
        if kind == "clip":
            res = probe_resolution(tmp_path)
            if res:
                width = res["width"]
                height = res["height"]
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass

    asset = MediaAsset(
        id=file_id,
        kind=kind,
        storage_path=result["path"],
        original_filename=filename,
        content_type=content_type,
        size=int(result.get("size", len(data))),
        duration=duration,
        width=width,
        height=height,
    )
    await repo.insert_media_asset(session, asset)
    return asset


@api.get("/media", response_model=List[MediaAsset])
async def list_media(
    kind: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> List[MediaAsset]:
    return await repo.list_media(session, kind)


@api.delete("/media/{asset_id}")
async def delete_media(
    asset_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not await repo.soft_delete_media(session, asset_id):
        raise HTTPException(404, "Asset not found")
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Serve any object-storage file through the backend
# ---------------------------------------------------------------------------
@api.get("/files/{path:path}")
async def serve_file(
    path: str,
    session: AsyncSession = Depends(get_session),
):
    try:
        data, content_type = storage.get_object(path)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(404, f"File not found: {e}")
    record = await repo.get_media_asset_by_path(session, path)
    if record and record.content_type:
        content_type = record.content_type
    return Response(content=data, media_type=content_type)


# ---------------------------------------------------------------------------
# TTS narration generation
# ---------------------------------------------------------------------------
@api.post("/narration/tts", response_model=MediaAsset)
async def generate_tts(
    req: TTSGenerateRequest,
    session: AsyncSession = Depends(get_session),
) -> MediaAsset:
    try:
        audio_bytes = await narration.synthesize(
            text=req.text,
            voice=req.voice,
            model=req.model,
            speed=req.speed,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"TTS failed: {e}")

    file_id = str(uuid.uuid4())
    path = storage.build_path("narration", file_id, "mp3")
    result = storage.put_object(path, audio_bytes, "audio/mpeg")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = Path(tmp.name)
    duration = probe_duration(tmp_path)
    try:
        tmp_path.unlink()
    except OSError:
        pass

    asset = MediaAsset(
        id=file_id,
        kind="narration",
        storage_path=result["path"],
        original_filename=f"narration-{req.voice}.mp3",
        content_type="audio/mpeg",
        size=int(result.get("size", len(audio_bytes))),
        duration=duration,
    )
    await repo.insert_media_asset(session, asset)
    return asset


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
@api.post("/projects", response_model=Project)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> Project:
    project = Project(
        title=payload.title,
        subtitle=payload.subtitle,
        description=payload.description,
    )
    await repo.insert_project(session, project)
    return project


@api.get("/projects", response_model=List[Project])
async def list_projects(
    session: AsyncSession = Depends(get_session),
) -> List[Project]:
    return await repo.list_projects(session)


@api.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> Project:
    p = await repo.get_project(session, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return p


@api.patch("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
) -> Project:
    raw = payload.model_dump(exclude_unset=True)
    fields = {k: v for k, v in raw.items() if k != "segments" and v is not None}
    segments = payload.segments  # may be None or a list
    updated = await repo.update_project(
        session, project_id, fields=fields, segments=segments,
    )
    if not updated:
        raise HTTPException(404, "Project not found")
    return updated


@api.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not await repo.delete_project(session, project_id):
        raise HTTPException(404, "Project not found")
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Render pipeline
# ---------------------------------------------------------------------------
async def _run_render(job_id: str, project_id: str) -> None:
    """Background task: render a project to mp4, upload, mark job complete."""
    from database import AsyncSessionLocal  # local import to avoid early init

    tmp_inputs: List[Path] = []
    output_path: Optional[Path] = None
    try:
        async with AsyncSessionLocal() as s:
            await repo.update_render_job(s, job_id, {
                "status": "rendering",
                "stage": "downloading_inputs",
                "progress": 0.02,
                "queue_position": 0,
                "started_at": datetime.now(timezone.utc),
            })

            project = await repo.get_project(s, project_id)
            if not project:
                raise RuntimeError("Project disappeared")
            if not project.segments:
                raise RuntimeError("Project has no segments")

            loop_outer = asyncio.get_running_loop()

            async def _download_progress(done: int, total: int) -> None:
                # Map 0.02 → 0.12 over the count of downloaded files
                frac = max(0.0, min(1.0, done / max(1, total)))
                pct = 0.02 + 0.10 * frac
                async with AsyncSessionLocal() as s2:
                    await repo.update_render_job(s2, job_id, {
                        "progress": float(pct),
                        "stage": "downloading_inputs",
                    })

            def _dl_cb(done: int, total: int) -> None:
                try:
                    loop_outer.create_task(_download_progress(done, total))
                except RuntimeError:
                    pass

            seg_specs, narr_spec, amb_spec, grading_spec, tmp_inputs = await load_render_inputs(
                s, project, progress_cb=_dl_cb,
            )

        output_path = Path(tempfile.gettempdir()) / f"tattva_{job_id}.mp4"
        loop = asyncio.get_running_loop()

        async def _progress_update(pct: float, stage: str) -> None:
            async with AsyncSessionLocal() as s:
                await repo.update_render_job(s, job_id, {
                    "progress": float(pct), "stage": stage,
                })

        def _progress(pct: float, stage: str) -> None:
            try:
                loop.create_task(_progress_update(pct, stage))
            except RuntimeError:
                pass

        ctx = RenderContext(
            segments=seg_specs,
            grading=grading_spec,
            narration=narr_spec,
            ambient=amb_spec,
            width=project.render_config.width,
            height=project.render_config.height,
            fps=project.render_config.fps,
            video_bitrate=project.render_config.video_bitrate,
            audio_bitrate=project.render_config.audio_bitrate,
            output_path=output_path,
            progress_cb=_progress,
        )

        async with AsyncSessionLocal() as s:
            await repo.update_render_job(s, job_id, {"stage": "preparing", "progress": 0.13})

        await asyncio.to_thread(render_project, ctx)

        # ---- Upload to object storage ----
        rendered_size = output_path.stat().st_size if output_path.exists() else 0
        async with AsyncSessionLocal() as s:
            await repo.update_render_job(s, job_id, {
                "stage": "uploading",
                "progress": 0.90,
                "output_size_bytes": int(rendered_size),
            })

            out_asset = await asyncio.to_thread(upload_render_output, output_path, project)
            await repo.insert_media_asset(s, out_asset)

            await repo.update_render_job(s, job_id, {
                "stage": "finalizing",
                "progress": 0.97,
                "output_size_bytes": int(out_asset.size or rendered_size),
            })

            # Provenance — snapshot every cited asset alongside the rubric.
            asset_ids = [seg.asset_id for seg in project.segments if seg.asset_id]
            clip_assets = await repo.list_media_assets_by_ids(s, asset_ids) if asset_ids else []
            provenance = build_provenance(project, clip_assets)

            await repo.update_project(s, project_id, fields={
                "latest_render_id": out_asset.id,
            })

            await repo.update_render_job(s, job_id, {
                "status": "completed",
                "progress": 1.0,
                "stage": "completed",
                "output_asset_id": out_asset.id,
                "provenance": provenance,
                "output_size_bytes": int(out_asset.size or rendered_size),
                "completed_at": datetime.now(timezone.utc),
            })
    except Exception as e:  # noqa: BLE001
        logger.exception("Render failed")
        async with AsyncSessionLocal() as s:
            await repo.update_render_job(s, job_id, {
                "status": "failed",
                "error": str(e),
                "stage": "failed",
                "completed_at": datetime.now(timezone.utc),
            })
    finally:
        cleanup_paths(tmp_inputs)
        if output_path and output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass


@api.post("/projects/{project_id}/render", response_model=RenderJob)
async def start_render(
    project_id: str,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> RenderJob:
    project = await repo.get_project(session, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if not project.segments:
        raise HTTPException(400, "Project has no segments on the timeline")

    active = await find_active_render(session, project_id)
    if active:
        return active

    job = RenderJob(project_id=project_id)
    await repo.insert_render_job(session, job)
    background.add_task(_run_render, job.id, project_id)
    return job


@api.get("/render/{job_id}", response_model=RenderJob)
async def get_render(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> RenderJob:
    j = await repo.get_render_job(session, job_id)
    if not j:
        raise HTTPException(404, "Render job not found")
    return j


@api.get("/projects/{project_id}/renders", response_model=List[RenderJob])
async def list_renders(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> List[RenderJob]:
    return await repo.list_render_jobs(session, project_id)


@api.get("/render/{job_id}/provenance")
async def render_provenance(
    job_id: str,
    format: str = "json",
    download: int = 0,
    session: AsyncSession = Depends(get_session),
):
    provenance = await repo.get_render_provenance(session, job_id)
    if provenance is None:
        # Could be: job doesn't exist OR it exists but isn't completed
        j = await repo.get_render_job(session, job_id)
        if not j:
            raise HTTPException(404, "Render job not found")
        raise HTTPException(404, "No provenance for this render (only completed renders have one)")

    if format == "text":
        body = render_provenance_text(provenance).encode("utf-8")
        media_type = "text/plain; charset=utf-8"
        filename = f"provenance-{job_id[:8]}.txt"
    else:
        body = provenance_to_json(provenance)
        media_type = "application/json"
        filename = f"provenance-{job_id[:8]}.json"

    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return Response(content=body, media_type=media_type, headers=headers)


# ---------------------------------------------------------------------------
# Atmospheric Retrieval
# ---------------------------------------------------------------------------
_search_cache: TTLCache = TTLCache(ttl_seconds=300.0, max_items=128)


@api.post("/retrieval/analyze")
async def retrieval_analyze(req: AnalyzeSceneRequest) -> dict:
    try:
        rubric = await retrieval.analyze_scene(
            description=req.description,
            contemplative_mode=req.contemplative_mode,
            narration_text=req.narration_text,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("Scene analysis failed")
        raise HTTPException(502, f"Scene analysis failed: {e}")
    return {"rubric": rubric}


def _gentler_query_suggestions(rubric: dict) -> List[str]:
    base = (rubric.get("environment") or rubric.get("atmosphere") or "stillness").lower()
    return [
        f"empty {base} at dawn",
        f"quiet {base} after rain",
        f"observational {base}, no people",
        f"natural light {base}, very still",
    ]


@api.post("/retrieval/search")
async def retrieval_search(req: SearchRequest) -> dict:
    cache_key = None
    if req.description and not req.rubric:
        cache_key = (
            req.description.strip().lower(),
            bool(req.contemplative_mode),
            int(req.per_query),
            (req.narration_text or "").strip().lower()[:200],
        )
        cached = _search_cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

    rubric = req.rubric
    if not rubric:
        if not req.description:
            raise HTTPException(400, "Provide either rubric or description")
        try:
            rubric = await retrieval.analyze_scene(
                description=req.description,
                contemplative_mode=req.contemplative_mode,
                narration_text=req.narration_text,
            )
        except Exception as e:  # noqa: BLE001
            raise HTTPException(502, f"Scene analysis failed: {e}")

    queries = list(rubric.get("search_queries") or [])
    raw_clips = await retrieval.search_all(queries, per_query=req.per_query)

    if not raw_clips:
        result = {
            "rubric": rubric,
            "clips": [],
            "suggestions": _gentler_query_suggestions(rubric),
            "reason": "no_results_from_providers",
        }
        if cache_key is not None:
            _search_cache.set(cache_key, result)
        return result

    ranked = await retrieval.rank_clips(
        raw_clips, rubric, contemplative_mode=req.contemplative_mode,
    )
    serialised = [ProviderClipModel(**c.to_dict()).model_dump() for c in ranked]
    result = {"rubric": rubric, "clips": serialised}
    if not serialised:
        result["suggestions"] = _gentler_query_suggestions(rubric)
        result["reason"] = "filtered_by_contemplative_mode" if req.contemplative_mode else "no_matches"
        result["unfiltered_count"] = len(raw_clips)
    if cache_key is not None:
        _search_cache.set(cache_key, result)
    return result


@api.post("/retrieval/assemble", response_model=Project)
async def retrieval_assemble(
    req: AssembleRequest,
    session: AsyncSession = Depends(get_session),
) -> Project:
    """Download selected stock clips → object storage → MediaAsset → adaptive
    trim → append timeline segments → record a retrieval_session + the picked
    selected_clips for provenance."""
    if not req.selections:
        raise HTTPException(400, "No clips selected")

    project = await repo.get_project(session, req.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Narration awareness for adaptive trim
    narration_dur: Optional[float] = None
    if project.narration.source != "none" and project.narration.asset_id:
        narr_asset = await repo.get_media_asset(session, project.narration.asset_id)
        if narr_asset and narr_asset.duration:
            narration_dur = float(narr_asset.duration)
    per_clip_narration: Optional[float] = (
        narration_dur / len(req.selections) if narration_dur else None
    )

    from models import Segment  # local import
    new_segments: List[Segment] = list(project.segments)
    imported_assets: List[MediaAsset] = []
    selected_records: List[dict] = []
    failures: List[str] = []

    for sel in req.selections:
        asset = await import_stock_clip(sel)
        if not asset:
            failures.append(f"{sel.provider}/{sel.external_id}")
            continue

        await repo.insert_media_asset(session, asset)
        imported_assets.append(asset)

        # Honour user trim override if provided, else ask the LLM
        if sel.trim_start is not None and sel.trim_duration is not None:
            trim = {
                "start": max(0.0, float(sel.trim_start)),
                "duration": max(0.5, float(sel.trim_duration)),
                "rationale": "User-set trim window.",
            }
        else:
            trim = await retrieval.adaptive_trim(
                clip_duration=asset.duration or sel.duration or 0.0,
                pacing=req.pacing or "slow",
                narration_duration=per_clip_narration,
                rubric_atmosphere=req.rubric_atmosphere or "",
            )
        new_segments.append(build_retrieval_segment(
            asset=asset,
            trim=trim,
            is_first_on_timeline=(len(new_segments) == 0),
            transition=req.transition,
        ))
        selected_records.append({
            "provider": sel.provider,
            "external_id": sel.external_id,
            "title": getattr(sel, "title", "") or "",
            "tags": getattr(sel, "tags", []) or [],
            "duration": getattr(sel, "duration", asset.duration) or 0.0,
            "width": getattr(sel, "width", asset.width) or 0,
            "height": getattr(sel, "height", asset.height) or 0,
            "download_url": getattr(sel, "download_url", None),
            "preview_url": getattr(sel, "preview_url", None),
            "thumbnail_url": getattr(sel, "thumbnail_url", None),
            "source_url": getattr(sel, "source_url", None),
            "author": getattr(sel, "author", "") or "",
            "trim_start": trim.get("start"),
            "trim_duration": trim.get("duration"),
            "selected": True,
            "imported_asset_id": asset.id,
        })

    if not imported_assets:
        raise HTTPException(502, f"Could not import any selected clip ({failures})")

    if failures:
        logger.warning("Retrieval assemble — partial failures: %s", failures)

    fields = {}
    if req.rubric:
        fields["last_rubric"] = req.rubric
        fields["last_retrieval_at"] = datetime.now(timezone.utc)
    updated = await repo.update_project(
        session, project.id,
        fields=fields,
        segments=new_segments,
    )

    # Record retrieval session + selected clips (auth-ready columns)
    await repo.insert_retrieval_session(
        session,
        project_id=project.id,
        description=None,
        rubric=req.rubric,
        contemplative_mode=True,
        narration_text=None,
        per_query=len(req.selections),
        clips=selected_records,
    )

    return updated


# ---------------------------------------------------------------------------
# Wire up
# ---------------------------------------------------------------------------
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
