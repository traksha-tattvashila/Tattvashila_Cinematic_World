"""Thin async repositories that translate between Pydantic API models
(`models.py`) and SQLAlchemy ORM models (`db_models.py`).

The rest of the codebase keeps using the Pydantic types it already uses;
only the boundary functions here ever touch the SQLAlchemy session.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Sequence

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

import db_models as orm
from models import MediaAsset, Project, RenderJob, Segment


# ---------------------------------------------------------------------------
# Mapping helpers — ORM ↔ Pydantic
# ---------------------------------------------------------------------------
def _proj_to_pyd(p: orm.Project) -> Project:
    segs = [
        Segment(
            kind=s.kind,
            asset_id=s.asset_id,
            duration=s.duration,
            start_offset=s.start_offset,
            transition_in=s.transition_in,
            transition_in_duration=s.transition_in_duration,
        )
        for s in (p.segments or [])
    ]
    return Project(
        id=p.id,
        title=p.title,
        subtitle=p.subtitle,
        description=p.description,
        segments=segs,
        narration=p.narration or {},
        ambient=p.ambient or {},
        grading=p.grading or {},
        render_config=p.render_config or {},
        latest_render_id=p.latest_render_id,
        last_rubric=p.last_rubric,
        last_retrieval_at=p.last_retrieval_at.isoformat() if p.last_retrieval_at else None,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


def _asset_to_pyd(a: orm.MediaAsset) -> MediaAsset:
    return MediaAsset(
        id=a.id,
        kind=a.kind,
        storage_path=a.storage_path,
        original_filename=a.original_filename,
        content_type=a.content_type,
        size=a.size,
        duration=a.duration,
        width=a.width,
        height=a.height,
        is_deleted=a.is_deleted,
        provider=a.provider,
        provider_external_id=a.provider_external_id,
        source_url=a.source_url,
        author=a.author,
        created_at=a.created_at.isoformat(),
    )


def _job_to_pyd(j: orm.RenderJob) -> RenderJob:
    return RenderJob(
        id=j.id,
        project_id=j.project_id,
        status=j.status,
        progress=j.progress,
        stage=j.stage,
        output_asset_id=j.output_asset_id,
        output_size_bytes=j.output_size_bytes,
        queue_position=j.queue_position,
        error=j.error,
        started_at=j.started_at.isoformat() if j.started_at else None,
        completed_at=j.completed_at.isoformat() if j.completed_at else None,
        created_at=j.created_at.isoformat(),
    )


async def get_render_provenance(
    session: AsyncSession, job_id: str
) -> Optional[dict]:
    """Return only the JSONB provenance for a render job (NOT in RenderJob
    listings, to keep payloads light)."""
    res = await session.execute(
        select(orm.RenderJob.provenance).where(orm.RenderJob.id == job_id)
    )
    row = res.first()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
async def insert_project(session: AsyncSession, project: Project) -> None:
    p = orm.Project(
        id=project.id,
        title=project.title,
        subtitle=project.subtitle,
        description=project.description,
        narration=project.narration.model_dump() if hasattr(project.narration, "model_dump") else dict(project.narration),
        ambient=project.ambient.model_dump() if hasattr(project.ambient, "model_dump") else dict(project.ambient),
        grading=project.grading.model_dump() if hasattr(project.grading, "model_dump") else dict(project.grading),
        render_config=project.render_config.model_dump() if hasattr(project.render_config, "model_dump") else dict(project.render_config),
        latest_render_id=project.latest_render_id,
        last_rubric=project.last_rubric,
    )
    for idx, seg in enumerate(project.segments or []):
        p.segments.append(orm.Segment(
            project_id=p.id,
            position=idx,
            kind=seg.kind,
            asset_id=seg.asset_id,
            duration=seg.duration,
            start_offset=seg.start_offset,
            transition_in=seg.transition_in,
            transition_in_duration=seg.transition_in_duration,
        ))
    session.add(p)
    await session.commit()


async def list_projects(session: AsyncSession) -> List[Project]:
    res = await session.execute(
        select(orm.Project).order_by(orm.Project.updated_at.desc()).limit(500)
    )
    return [_proj_to_pyd(p) for p in res.scalars().all()]


async def get_project(session: AsyncSession, project_id: str) -> Optional[Project]:
    res = await session.execute(
        select(orm.Project).where(orm.Project.id == project_id)
    )
    p = res.scalar_one_or_none()
    return _proj_to_pyd(p) if p else None


async def update_project(
    session: AsyncSession,
    project_id: str,
    *,
    fields: dict,
    segments: Optional[Sequence[Segment]] = None,
) -> Optional[Project]:
    """Update arbitrary top-level columns and (optionally) replace segments."""
    res = await session.execute(
        select(orm.Project).where(orm.Project.id == project_id)
    )
    p = res.scalar_one_or_none()
    if not p:
        return None

    for k, v in fields.items():
        if k == "updated_at":  # auto-managed by SQLAlchemy onupdate
            continue
        if k in {"narration", "ambient", "grading", "render_config", "last_rubric"} and v is not None:
            v = v.model_dump() if hasattr(v, "model_dump") else dict(v)
        if k == "last_retrieval_at" and isinstance(v, str):
            v = datetime.fromisoformat(v)
        if hasattr(p, k):
            setattr(p, k, v)
    p.updated_at = datetime.now(timezone.utc)

    if segments is not None:
        # Replace all segments
        await session.execute(
            delete(orm.Segment).where(orm.Segment.project_id == project_id)
        )
        # Expire the cached relationship so the new rows are loaded after commit
        await session.flush()
        await session.refresh(p, ["segments"])
        for idx, seg in enumerate(segments):
            session.add(orm.Segment(
                project_id=project_id,
                position=idx,
                kind=seg.kind,
                asset_id=seg.asset_id,
                duration=seg.duration,
                start_offset=seg.start_offset,
                transition_in=seg.transition_in,
                transition_in_duration=seg.transition_in_duration,
            ))

    await session.commit()
    # Re-fetch with eager-loaded segments through a fresh statement
    session.expire_all()
    return await get_project(session, project_id)


async def delete_project(session: AsyncSession, project_id: str) -> bool:
    res = await session.execute(
        delete(orm.Project).where(orm.Project.id == project_id)
    )
    await session.commit()
    return res.rowcount > 0


# ---------------------------------------------------------------------------
# Media assets
# ---------------------------------------------------------------------------
async def insert_media_asset(session: AsyncSession, asset: MediaAsset) -> None:
    a = orm.MediaAsset(
        id=asset.id,
        kind=asset.kind,
        storage_path=asset.storage_path,
        original_filename=asset.original_filename,
        content_type=asset.content_type,
        size=asset.size,
        duration=asset.duration,
        width=asset.width,
        height=asset.height,
        is_deleted=asset.is_deleted,
        provider=asset.provider,
        provider_external_id=asset.provider_external_id,
        source_url=asset.source_url,
        author=asset.author,
    )
    session.add(a)
    await session.commit()


async def list_media(session: AsyncSession, kind: Optional[str] = None) -> List[MediaAsset]:
    q = select(orm.MediaAsset).where(orm.MediaAsset.is_deleted.is_(False))
    if kind:
        q = q.where(orm.MediaAsset.kind == kind)
    q = q.order_by(orm.MediaAsset.created_at.desc()).limit(500)
    res = await session.execute(q)
    return [_asset_to_pyd(a) for a in res.scalars().all()]


async def get_media_asset(
    session: AsyncSession, asset_id: str, include_deleted: bool = False
) -> Optional[MediaAsset]:
    q = select(orm.MediaAsset).where(orm.MediaAsset.id == asset_id)
    if not include_deleted:
        q = q.where(orm.MediaAsset.is_deleted.is_(False))
    res = await session.execute(q)
    a = res.scalar_one_or_none()
    return _asset_to_pyd(a) if a else None


async def get_media_asset_by_path(
    session: AsyncSession, storage_path: str
) -> Optional[MediaAsset]:
    res = await session.execute(
        select(orm.MediaAsset).where(
            and_(
                orm.MediaAsset.storage_path == storage_path,
                orm.MediaAsset.is_deleted.is_(False),
            )
        ).limit(1)
    )
    a = res.scalar_one_or_none()
    return _asset_to_pyd(a) if a else None


async def list_media_assets_by_ids(
    session: AsyncSession, ids: Sequence[str]
) -> List[MediaAsset]:
    if not ids:
        return []
    res = await session.execute(
        select(orm.MediaAsset).where(orm.MediaAsset.id.in_(list(ids)))
    )
    return [_asset_to_pyd(a) for a in res.scalars().all()]


async def soft_delete_media(session: AsyncSession, asset_id: str) -> bool:
    res = await session.execute(
        update(orm.MediaAsset)
        .where(orm.MediaAsset.id == asset_id)
        .values(is_deleted=True)
    )
    await session.commit()
    return res.rowcount > 0


# ---------------------------------------------------------------------------
# Render jobs
# ---------------------------------------------------------------------------
async def insert_render_job(session: AsyncSession, job: RenderJob) -> None:
    # Compute current queue depth (queued + rendering, not including this one)
    from sqlalchemy import func
    active_count_res = await session.execute(
        select(func.count(orm.RenderJob.id)).where(
            orm.RenderJob.status.in_(["queued", "rendering"])
        )
    )
    queue_position = int(active_count_res.scalar() or 0)
    j = orm.RenderJob(
        id=job.id,
        project_id=job.project_id,
        status=job.status,
        progress=job.progress,
        stage=job.stage,
        output_asset_id=job.output_asset_id,
        error=job.error,
        queue_position=queue_position,
    )
    session.add(j)
    await session.commit()
    # Reflect on the caller's Pydantic instance so the API response carries it.
    job.queue_position = queue_position


async def update_render_job(
    session: AsyncSession, job_id: str, fields: dict
) -> Optional[RenderJob]:
    # Convert any ISO timestamps back into datetimes for tz-aware columns
    for ts_key in ("started_at", "completed_at"):
        if ts_key in fields and isinstance(fields[ts_key], str):
            fields[ts_key] = datetime.fromisoformat(fields[ts_key])
    res = await session.execute(
        update(orm.RenderJob).where(orm.RenderJob.id == job_id).values(**fields)
    )
    if res.rowcount == 0:
        await session.rollback()
        return None
    await session.commit()
    return await get_render_job(session, job_id)


async def get_render_job(session: AsyncSession, job_id: str) -> Optional[RenderJob]:
    res = await session.execute(
        select(orm.RenderJob).where(orm.RenderJob.id == job_id)
    )
    j = res.scalar_one_or_none()
    return _job_to_pyd(j) if j else None


async def list_render_jobs(session: AsyncSession, project_id: str) -> List[RenderJob]:
    res = await session.execute(
        select(orm.RenderJob)
        .where(orm.RenderJob.project_id == project_id)
        .order_by(orm.RenderJob.created_at.desc())
        .limit(50)
    )
    return [_job_to_pyd(j) for j in res.scalars().all()]


async def find_active_render(
    session: AsyncSession, project_id: str
) -> Optional[RenderJob]:
    res = await session.execute(
        select(orm.RenderJob).where(
            and_(
                orm.RenderJob.project_id == project_id,
                orm.RenderJob.status.in_(["queued", "rendering"]),
            )
        ).limit(1)
    )
    j = res.scalar_one_or_none()
    return _job_to_pyd(j) if j else None


# ---------------------------------------------------------------------------
# Retrieval sessions + selected clips
# ---------------------------------------------------------------------------
async def insert_retrieval_session(
    session: AsyncSession,
    *,
    project_id: Optional[str],
    description: Optional[str],
    rubric: Optional[dict],
    contemplative_mode: bool,
    narration_text: Optional[str],
    per_query: int,
    clips: List[dict],
) -> str:
    sess = orm.RetrievalSession(
        project_id=project_id,
        description=description,
        rubric=rubric,
        contemplative_mode=contemplative_mode,
        narration_text=narration_text,
        per_query=per_query,
    )
    session.add(sess)
    await session.flush()
    for c in clips or []:
        session.add(orm.SelectedClip(
            retrieval_session_id=sess.id,
            provider=c.get("provider") or "unknown",
            external_id=str(c.get("external_id") or c.get("provider_external_id") or ""),
            title=c.get("title") or "",
            tags=c.get("tags") or [],
            duration=float(c.get("duration") or 0.0),
            width=int(c.get("width") or 0),
            height=int(c.get("height") or 0),
            download_url=c.get("download_url"),
            preview_url=c.get("preview_url"),
            thumbnail_url=c.get("thumbnail_url"),
            source_url=c.get("source_url"),
            author=c.get("author") or "",
            score=c.get("score"),
            rationale=c.get("rationale"),
            trim_start=c.get("trim_start"),
            trim_duration=c.get("trim_duration"),
            selected=bool(c.get("selected", False)),
            imported_asset_id=c.get("imported_asset_id"),
        ))
    await session.commit()
    return sess.id
