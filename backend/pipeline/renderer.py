"""
Tattvashila cinematic renderer.

Assembles a project's segments, narration, and ambient bed into a final
mp4 using MoviePy. Designed for contemplative pacing — never optimised
for stimulation.

Key contract:
    render_project(ctx) -> Path

`ctx` is a `RenderContext` (see below) which bundles together every
piece of media plus the configuration. The renderer is intentionally
agnostic of the web layer; it can be called from the FastAPI server,
from the CLI (`python -m pipeline`), or from a notebook.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

# Pillow 10+ removed Image.ANTIALIAS in favour of Image.Resampling.LANCZOS.
# MoviePy 1.0.3 still references the legacy name; alias it before importing.
from PIL import Image as _PILImage  # noqa: E402
if not hasattr(_PILImage, "ANTIALIAS"):
    _PILImage.ANTIALIAS = _PILImage.Resampling.LANCZOS  # type: ignore[attr-defined]

from moviepy.editor import (  # noqa: E402
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    VideoFileClip,
    concatenate_videoclips,
)
from moviepy.audio.fx.audio_loop import audio_loop  # noqa: E402

from .config import CinematicDefaults
from .grading import apply_grading
from .transitions import crossfade_in, fade_in, fade_out

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Render context (frame-level, no web / DB coupling)
# ---------------------------------------------------------------------------
@dataclass
class SegmentSpec:
    kind: str                      # "clip" | "pause"
    duration: float
    source_path: Optional[Path] = None
    start_offset: float = 0.0
    transition_in: str = "fade"
    transition_in_duration: float = 1.5


@dataclass
class GradingSpec:
    film_grain: bool = True
    grain_intensity: float = 0.05
    muted_palette: bool = True
    saturation: float = 0.78
    warm_highlights: bool = True
    warmth: float = 0.08
    contrast: float = 0.95


@dataclass
class AmbientSpec:
    path: Optional[Path] = None
    volume: float = 0.30
    fade_in: float = 3.0
    fade_out: float = 4.0


@dataclass
class NarrationSpec:
    path: Optional[Path] = None
    offset_seconds: float = 1.5
    volume: float = 1.0


@dataclass
class RenderContext:
    segments: List[SegmentSpec] = field(default_factory=list)
    grading: GradingSpec = field(default_factory=GradingSpec)
    narration: NarrationSpec = field(default_factory=NarrationSpec)
    ambient: AmbientSpec = field(default_factory=AmbientSpec)
    width: int = 1920
    height: int = 1080
    fps: int = 24
    video_bitrate: str = "6000k"
    audio_bitrate: str = "192k"
    output_path: Path = Path("/tmp/tattvashila_out.mp4")
    progress_cb: Optional[Callable[[float, str], None]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _report(ctx: RenderContext, pct: float, stage: str) -> None:
    if ctx.progress_cb:
        try:
            ctx.progress_cb(pct, stage)
        except Exception:  # noqa: BLE001
            pass


def _resize_letterbox(clip, width: int, height: int):
    """Resize maintaining aspect ratio, letterboxing onto a charcoal canvas."""
    target_ratio = width / height
    src_ratio = clip.w / clip.h
    if abs(src_ratio - target_ratio) < 0.01:
        return clip.resize(newsize=(width, height))
    if src_ratio > target_ratio:
        # Wider source — fit width
        new_w = width
        new_h = int(width / src_ratio)
    else:
        new_h = height
        new_w = int(height * src_ratio)
    resized = clip.resize(newsize=(new_w, new_h))
    bg = ColorClip(size=(width, height),
                   color=CinematicDefaults.black_color,
                   duration=clip.duration)
    return CompositeVideoClip([bg, resized.set_position("center")])


def _build_clip(seg: SegmentSpec, ctx: RenderContext, grading: GradingSpec):
    """Build a single VideoClip for one segment."""
    if seg.kind == "pause":
        clip = ColorClip(size=(ctx.width, ctx.height),
                         color=CinematicDefaults.black_color,
                         duration=max(0.1, seg.duration))
    else:
        if not seg.source_path or not Path(seg.source_path).exists():
            raise FileNotFoundError(f"Clip source missing: {seg.source_path}")
        src = VideoFileClip(str(seg.source_path), audio=False)
        max_dur = max(0.1, src.duration - seg.start_offset)
        dur = min(max(0.5, seg.duration), max_dur)
        sub = src.subclip(seg.start_offset, seg.start_offset + dur)
        sub = _resize_letterbox(sub, ctx.width, ctx.height)
        sub = apply_grading(
            sub,
            muted_palette=grading.muted_palette,
            saturation=grading.saturation,
            contrast=grading.contrast,
            warm_highlights=grading.warm_highlights,
            warmth=grading.warmth,
            film_grain=grading.film_grain,
            grain_intensity=grading.grain_intensity,
        )
        clip = sub

    # Apply transitions
    t_dur = max(0.0, seg.transition_in_duration)
    if seg.transition_in == "fade":
        clip = fade_in(clip, t_dur)
    elif seg.transition_in in ("crossfade", "dissolve"):
        # dissolve is just a longer crossfade; both rely on previous clip
        clip = crossfade_in(clip, t_dur)
    # else "none": leave hard cut
    return clip


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------
def render_project(ctx: RenderContext) -> Path:
    """Render the project to disk and return the output path."""
    if not ctx.segments:
        raise ValueError("Cannot render a project with no segments")

    _report(ctx, 0.15, "preparing")
    logger.info("Rendering %d segments to %s", len(ctx.segments), ctx.output_path)

    clips = []
    n = max(1, len(ctx.segments))
    # Composing range: 0.15 → 0.45 (30%). Each segment is grading + resize.
    for idx, seg in enumerate(ctx.segments):
        c = _build_clip(seg, ctx, ctx.grading)
        clips.append(c)
        progress = 0.15 + 0.30 * (idx + 1) / n
        _report(ctx, progress, "composing")

    # Gentle tail fade-out on the last clip so the film never ends abruptly
    clips[-1] = fade_out(clips[-1], 2.0)

    # `compose` allows crossfades; for hard-cut-only sequences `chain`
    # would be cheaper, but the renderer is opinionated about restraint.
    final = concatenate_videoclips(clips, method="compose", padding=0)

    # ----- Audio -----
    # Emit twice — the first call publishes the phase label early; the second
    # confirms readiness right before FFmpeg muxes the tracks. Without two
    # touches the phase can pass faster than a 2s frontend poll.
    _report(ctx, 0.47, "audio_mixing")
    audio_tracks = []

    if ctx.narration.path and Path(ctx.narration.path).exists():
        narr = AudioFileClip(str(ctx.narration.path))
        narr = narr.volumex(ctx.narration.volume)
        narr = narr.set_start(max(0.0, ctx.narration.offset_seconds))
        audio_tracks.append(narr)

    if ctx.ambient.path and Path(ctx.ambient.path).exists():
        amb = AudioFileClip(str(ctx.ambient.path))
        if amb.duration < final.duration:
            amb = audio_loop(amb, duration=final.duration)
        else:
            amb = amb.subclip(0, final.duration)
        amb = amb.volumex(ctx.ambient.volume)
        if ctx.ambient.fade_in > 0:
            amb = amb.audio_fadein(ctx.ambient.fade_in)
        if ctx.ambient.fade_out > 0:
            amb = amb.audio_fadeout(ctx.ambient.fade_out)
        audio_tracks.append(amb)

    if audio_tracks:
        final = final.set_audio(CompositeAudioClip(audio_tracks))

    # Final audio_mixing confirmation so the contemplative phase label
    # has a chance to be picked up by the frontend poll loop.
    _report(ctx, 0.53, "audio_mixing")

    # ----- Write -----
    _report(ctx, 0.55, "encoding")
    ctx.output_path.parent.mkdir(parents=True, exist_ok=True)

    final.write_videofile(
        str(ctx.output_path),
        fps=ctx.fps,
        codec="libx264",
        audio_codec="aac" if audio_tracks else None,
        bitrate=ctx.video_bitrate,
        audio_bitrate=ctx.audio_bitrate,
        preset="medium",
        threads=2,
        logger=None,
        temp_audiofile=str(ctx.output_path.parent / "_audio.m4a") if audio_tracks else None,
        remove_temp=True,
    )

    _report(ctx, 0.88, "encoding_complete")
    return ctx.output_path


# ---------------------------------------------------------------------------
# Probe utility
# ---------------------------------------------------------------------------
def probe_duration(path: Path) -> Optional[float]:
    """Return the duration in seconds, or None if it cannot be read."""
    try:
        if str(path).lower().endswith((".mp4", ".mov", ".webm", ".mkv", ".avi")):
            with VideoFileClip(str(path), audio=False) as v:
                return float(v.duration)
        else:
            with AudioFileClip(str(path)) as a:
                return float(a.duration)
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not probe %s: %s", path, e)
        return None


def probe_resolution(path: Path) -> Optional[Dict[str, int]]:
    try:
        with VideoFileClip(str(path), audio=False) as v:
            return {"width": int(v.w), "height": int(v.h)}
    except Exception:
        return None
