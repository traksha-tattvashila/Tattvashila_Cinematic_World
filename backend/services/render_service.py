"""
Render service helpers.

Extracted from `server.py` so the heavy assembly logic can be unit-tested
and reasoned about independently of the FastAPI background-task wrapper.

Persistence: SQLAlchemy async session (Supabase Postgres).
"""
from __future__ import annotations

import logging
import tempfile
import os
import uuid
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

import repositories as repo
import storage
import ambient_library
from models import MediaAsset, Project, RenderJob
from pipeline.renderer import (
    AmbientSpec,
    GradingSpec,
    NarrationSpec,
    SegmentSpec,
    probe_duration,
)

logger = logging.getLogger(__name__)


async def _download_to_temp(storage_path: str) -> Path:
    data, _ct = storage.get_object(storage_path)
    suffix = "." + storage_path.rsplit(".", 1)[-1] if "." in storage_path else ".bin"
    fd, tmp_name = tempfile.mkstemp(suffix=suffix, prefix="tattva_")
    os.close(fd)
    Path(tmp_name).write_bytes(data)
    return Path(tmp_name)


async def _resolve_asset_to_disk(
    session: AsyncSession, asset_id: Optional[str]
) -> Optional[Path]:
    if not asset_id:
        return None
    record = await repo.get_media_asset(session, asset_id)
    if not record:
        return None
    return await _download_to_temp(record.storage_path)


def _collect_required_asset_ids(project: Project) -> List[str]:
    ids: List[str] = []
    for seg in project.segments:
        if seg.kind == "clip" and seg.asset_id:
            ids.append(seg.asset_id)
    if project.narration.source != "none" and project.narration.asset_id:
        ids.append(project.narration.asset_id)
    if project.ambient.source == "upload" and project.ambient.asset_id:
        ids.append(project.ambient.asset_id)
    return ids


async def load_render_inputs(
    session: AsyncSession,
    project: Project,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Tuple[List[SegmentSpec], NarrationSpec, AmbientSpec, GradingSpec, List[Path]]:
    """Pull every media file referenced by `project` to local disk.

    If `progress_cb(done, total)` is provided, it is invoked after every
    individual download so the caller can surface granular progress.
    """
    tmp_inputs: List[Path] = []
    total = max(1, len(_collect_required_asset_ids(project)))
    done = 0

    def _bump() -> None:
        nonlocal done
        done += 1
        if progress_cb:
            try:
                progress_cb(done, total)
            except Exception:  # noqa: BLE001
                pass

    seg_specs: List[SegmentSpec] = []
    for seg in project.segments:
        src_path: Optional[Path] = None
        if seg.kind == "clip" and seg.asset_id:
            src_path = await _resolve_asset_to_disk(session, seg.asset_id)
            if src_path:
                tmp_inputs.append(src_path)
                _bump()
        seg_specs.append(SegmentSpec(
            kind=seg.kind,
            duration=seg.duration,
            source_path=src_path,
            start_offset=seg.start_offset,
            transition_in=seg.transition_in,
            transition_in_duration=seg.transition_in_duration,
        ))

    narr_spec = NarrationSpec(
        offset_seconds=project.narration.offset_seconds,
        volume=project.narration.volume,
    )
    if project.narration.source != "none":
        path = await _resolve_asset_to_disk(session, project.narration.asset_id)
        if path:
            tmp_inputs.append(path)
            narr_spec.path = path
            _bump()

    amb_spec = AmbientSpec(
        volume=project.ambient.volume,
        fade_in=project.ambient.fade_in,
        fade_out=project.ambient.fade_out,
    )
    if project.ambient.source == "builtin" and project.ambient.builtin_key:
        builtin = ambient_library.preset_path(project.ambient.builtin_key)
        if builtin:
            amb_spec.path = builtin
    elif project.ambient.source == "upload" and project.ambient.asset_id:
        path = await _resolve_asset_to_disk(session, project.ambient.asset_id)
        if path:
            tmp_inputs.append(path)
            amb_spec.path = path
            _bump()

    grading_spec = GradingSpec(
        film_grain=project.grading.film_grain,
        grain_intensity=project.grading.grain_intensity,
        muted_palette=project.grading.muted_palette,
        saturation=project.grading.saturation,
        warm_highlights=project.grading.warm_highlights,
        warmth=project.grading.warmth,
        contrast=project.grading.contrast,
    )
    return seg_specs, narr_spec, amb_spec, grading_spec, tmp_inputs


def upload_render_output(
    output_path: Path,
    project: Project,
) -> MediaAsset:
    """Push the rendered MP4 into object storage and return its asset record."""
    data = output_path.read_bytes()
    out_id = str(uuid.uuid4())
    out_storage_path = storage.build_path("render", out_id, "mp4")
    result = storage.put_object(out_storage_path, data, "video/mp4")

    return MediaAsset(
        id=out_id,
        kind="render",
        storage_path=result["path"],
        original_filename=f"{project.title.strip() or 'film'}.mp4",
        content_type="video/mp4",
        size=int(result.get("size", len(data))),
        duration=probe_duration(output_path),
        width=project.render_config.width,
        height=project.render_config.height,
    )


async def find_active_render(
    session: AsyncSession, project_id: str,
) -> Optional[RenderJob]:
    """Return the in-flight render job for a project, if any."""
    return await repo.find_active_render(session, project_id)


def cleanup_paths(paths: List[Path]) -> None:
    for p in paths:
        try:
            p.unlink()
        except OSError:
            pass
