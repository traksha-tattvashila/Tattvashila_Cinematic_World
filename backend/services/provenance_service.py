"""
Provenance — every rendered film should be a transparently citable cultural
object. This module captures and serialises:

    - the clips used (provider, author, source URL, attribution)
    - the retrieval rubric (if any) that selected them
    - timestamps (retrieved_at / rendered_at)
    - the project's authorship metadata

The sheet is stored on the RenderJob (`provenance` dict) so it persists
forever alongside the rendered MP4.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from models import MediaAsset, Project

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_provenance(project: Project, clip_assets: List[MediaAsset]) -> Dict[str, Any]:
    """Snapshot the project's lineage at render time."""
    citations = []
    for a in clip_assets:
        # Skip black-pause segments — they have no asset
        citations.append({
            "filename": a.original_filename,
            "provider": a.provider or "user-upload",
            "provider_external_id": a.provider_external_id,
            "author": a.author,
            "source_url": a.source_url,
            "duration": a.duration,
            "resolution": f"{a.width}x{a.height}" if a.width and a.height else None,
        })

    return {
        "schema_version": 1,
        "project": {
            "id": project.id,
            "title": project.title,
            "subtitle": project.subtitle,
            "description": project.description,
        },
        "rubric": project.last_rubric,
        "retrieved_at": project.last_retrieval_at,
        "rendered_at": _now_iso(),
        "segments": [
            {
                "kind": s.kind,
                "duration": s.duration,
                "start_offset": s.start_offset,
                "transition_in": s.transition_in,
                "asset_id": s.asset_id,
            }
            for s in project.segments
        ],
        "citations": citations,
    }


def render_provenance_text(provenance: Dict[str, Any]) -> str:
    """Render a small, austere plain-text representation of a provenance sheet."""
    lines = [
        "TATTVASHILA — Provenance Sheet",
        "=" * 60,
        f"Title           : {(provenance.get('project') or {}).get('title', '')}",
        f"Subtitle        : {(provenance.get('project') or {}).get('subtitle') or '—'}",
        f"Retrieved       : {provenance.get('retrieved_at') or '—'}",
        f"Rendered        : {provenance.get('rendered_at') or '—'}",
        "",
    ]
    rubric = provenance.get("rubric")
    if rubric:
        lines += [
            "Cinematic Rubric",
            "-" * 60,
            f"  Emotional tone : {rubric.get('emotional_tone', '')}",
            f"  Pacing         : {rubric.get('pacing', '')}",
            f"  Environment    : {rubric.get('environment', '')}",
            f"  Atmosphere     : {rubric.get('atmosphere', '')}",
            f"  Restraint      : {rubric.get('restraint_level', 0):.2f}",
            "",
        ]
        if rubric.get("rationale"):
            lines += [f'  "{rubric["rationale"]}"', ""]

    lines += ["Citations", "-" * 60]
    for i, c in enumerate(provenance.get("citations") or []):
        lines.append(f"  [{i+1:02d}] {c.get('filename') or '—'}")
        lines.append(f"        provider : {c.get('provider')}")
        if c.get("author"):
            lines.append(f"        author   : {c.get('author')}")
        if c.get("source_url"):
            lines.append(f"        source   : {c.get('source_url')}")
        if c.get("duration"):
            lines.append(f"        duration : {c['duration']:.1f}s · {c.get('resolution') or ''}")
        lines.append("")
    lines.append("Grounded in dharma. Carried with integrity.")
    return "\n".join(lines)


def provenance_to_json(provenance: Dict[str, Any]) -> bytes:
    return json.dumps(provenance, indent=2, ensure_ascii=False).encode("utf-8")
