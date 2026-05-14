"""
migrate_mongo_to_postgres.py
----------------------------

One-shot, idempotent migrator. Reads every document from the legacy MongoDB
collections (projects, media_assets, render_jobs) and inserts the equivalent
rows into Supabase Postgres. Re-running the script is safe — every INSERT is
ON CONFLICT (id) DO NOTHING.

Order of operations (preserves FKs):
    1. media_assets        — no FK
    2. projects + segments — segments FK projects.id
    3. render_jobs         — FK projects.id

Object storage paths are kept verbatim — media still lives in Emergent
Object Storage.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from database import AsyncSessionLocal, engine  # noqa: E402
from sqlalchemy import text  # noqa: E402


def _parse_dt(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, str):
        try:
            d = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


async def migrate_media(mongo) -> int:
    n = 0
    async with AsyncSessionLocal() as s:
        async for doc in mongo.media_assets.find({}):
            params = {
                "id": doc["id"],
                "kind": doc.get("kind", "clip"),
                "storage_path": doc.get("storage_path", ""),
                "original_filename": doc.get("original_filename", ""),
                "content_type": doc.get("content_type", "application/octet-stream"),
                "size": int(doc.get("size", 0)),
                "duration": doc.get("duration"),
                "width": doc.get("width"),
                "height": doc.get("height"),
                "is_deleted": bool(doc.get("is_deleted", False)),
                "provider": doc.get("provider"),
                "provider_external_id": doc.get("provider_external_id"),
                "source_url": doc.get("source_url"),
                "author": doc.get("author"),
                "created_at": _parse_dt(doc.get("created_at")) or datetime.now(timezone.utc),
            }
            await s.execute(text("""
                INSERT INTO media_assets (
                    id, kind, storage_path, original_filename, content_type,
                    size, duration, width, height, is_deleted,
                    provider, provider_external_id, source_url, author, created_at
                ) VALUES (
                    :id, :kind, :storage_path, :original_filename, :content_type,
                    :size, :duration, :width, :height, :is_deleted,
                    :provider, :provider_external_id, :source_url, :author, :created_at
                ) ON CONFLICT (id) DO NOTHING
            """), params)
            n += 1
        await s.commit()
    return n


async def migrate_projects(mongo) -> tuple[int, int]:
    np = ns = 0
    async with AsyncSessionLocal() as s:
        async for doc in mongo.projects.find({}):
            params = {
                "id": doc["id"],
                "title": doc.get("title") or "",
                "subtitle": doc.get("subtitle") or "",
                "description": doc.get("description") or "",
                "narration": doc.get("narration") or {},
                "ambient": doc.get("ambient") or {},
                "grading": doc.get("grading") or {},
                "render_config": doc.get("render_config") or {},
                "latest_render_id": doc.get("latest_render_id"),
                "last_rubric": doc.get("last_rubric"),
                "last_retrieval_at": _parse_dt(doc.get("last_retrieval_at")),
                "created_at": _parse_dt(doc.get("created_at")) or datetime.now(timezone.utc),
                "updated_at": _parse_dt(doc.get("updated_at")) or datetime.now(timezone.utc),
            }
            await s.execute(text("""
                INSERT INTO projects (
                    id, title, subtitle, description, narration, ambient,
                    grading, render_config, latest_render_id, last_rubric,
                    last_retrieval_at, created_at, updated_at
                ) VALUES (
                    :id, :title, :subtitle, :description,
                    CAST(:narration AS jsonb), CAST(:ambient AS jsonb),
                    CAST(:grading AS jsonb), CAST(:render_config AS jsonb),
                    :latest_render_id, CAST(:last_rubric AS jsonb),
                    :last_retrieval_at, :created_at, :updated_at
                ) ON CONFLICT (id) DO NOTHING
            """), {
                **params,
                "narration": _j(params["narration"]),
                "ambient": _j(params["ambient"]),
                "grading": _j(params["grading"]),
                "render_config": _j(params["render_config"]),
                "last_rubric": _j(params["last_rubric"]) if params["last_rubric"] is not None else None,
            })
            np += 1
            # Clear any pre-existing segments for this project, then insert fresh
            await s.execute(text("DELETE FROM segments WHERE project_id = :pid"), {"pid": doc["id"]})
            for idx, seg in enumerate(doc.get("segments") or []):
                await s.execute(text("""
                    INSERT INTO segments (
                        id, project_id, position, kind, asset_id, duration,
                        start_offset, transition_in, transition_in_duration, created_at
                    ) VALUES (
                        gen_random_uuid(), :project_id, :position, :kind, :asset_id,
                        :duration, :start_offset, :transition_in, :transition_in_duration, now()
                    )
                """), {
                    "project_id": doc["id"],
                    "position": idx,
                    "kind": seg.get("kind", "clip"),
                    "asset_id": seg.get("asset_id"),
                    "duration": float(seg.get("duration") or 0.0),
                    "start_offset": float(seg.get("start_offset") or 0.0),
                    "transition_in": seg.get("transition_in") or "fade",
                    "transition_in_duration": float(seg.get("transition_in_duration") or 1.5),
                })
                ns += 1
        await s.commit()
    return np, ns


async def migrate_render_jobs(mongo) -> int:
    n = 0
    async with AsyncSessionLocal() as s:
        async for doc in mongo.render_jobs.find({}):
            params = {
                "id": doc["id"],
                "project_id": doc["project_id"],
                "status": doc.get("status", "queued"),
                "progress": float(doc.get("progress", 0.0)),
                "stage": doc.get("stage", "queued"),
                "output_asset_id": doc.get("output_asset_id"),
                "error": doc.get("error"),
                "started_at": _parse_dt(doc.get("started_at")),
                "completed_at": _parse_dt(doc.get("completed_at")),
                "provenance": _j(doc.get("provenance")) if doc.get("provenance") is not None else None,
                "created_at": _parse_dt(doc.get("created_at")) or datetime.now(timezone.utc),
            }
            # Skip render jobs whose project was not migrated (orphan)
            check = await s.execute(text("SELECT 1 FROM projects WHERE id = :pid"),
                                    {"pid": params["project_id"]})
            if check.first() is None:
                print(f"  · skipping orphan render_job {doc['id']} (no parent project)")
                continue
            await s.execute(text("""
                INSERT INTO render_jobs (
                    id, project_id, status, progress, stage, output_asset_id,
                    error, started_at, completed_at, provenance, created_at
                ) VALUES (
                    :id, :project_id, :status, :progress, :stage, :output_asset_id,
                    :error, :started_at, :completed_at, CAST(:provenance AS jsonb), :created_at
                ) ON CONFLICT (id) DO NOTHING
            """), params)
            n += 1
        await s.commit()
    return n


def _j(v):
    import json
    return json.dumps(v) if v is not None else None


async def main() -> int:
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    print(f"Mongo source: {mongo_url} / {db_name}")
    client = AsyncIOMotorClient(mongo_url)
    mongo = client[db_name]

    print("Phase 1 — media_assets")
    mc = await migrate_media(mongo)
    print(f"  · migrated {mc} media assets")

    print("Phase 2 — projects + segments")
    pc, sc = await migrate_projects(mongo)
    print(f"  · migrated {pc} projects, {sc} segments")

    print("Phase 3 — render_jobs")
    rc = await migrate_render_jobs(mongo)
    print(f"  · migrated {rc} render jobs")

    await engine.dispose()
    client.close()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
