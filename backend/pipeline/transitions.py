"""
Restrained cinematic transitions.

Only four are supported by Tattvashila — by design.
    fade        : fade-in from black at clip head
    crossfade   : crossfade with the previous clip
    dissolve    : slow alpha dissolve (same as crossfade, but longer)
    none        : hard cut (use sparingly; usually for black-frame pauses)

Anything flashier (zoom, glitch, slide, whip) is intentionally absent.
"""
from __future__ import annotations

from moviepy.editor import VideoClip


def fade_in(clip: VideoClip, duration: float) -> VideoClip:
    """Fade from black at the head of a clip."""
    if duration <= 0:
        return clip
    return clip.fadein(duration)


def fade_out(clip: VideoClip, duration: float) -> VideoClip:
    """Fade to black at the tail of a clip."""
    if duration <= 0:
        return clip
    return clip.fadeout(duration)


def crossfade_in(clip: VideoClip, duration: float) -> VideoClip:
    """
    Apply a crossfade-in. The clip becomes transparent at its head so
    the previous clip bleeds through underneath when composed.
    """
    if duration <= 0:
        return clip
    return clip.crossfadein(duration)
