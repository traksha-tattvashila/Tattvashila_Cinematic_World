"""
Atmospheric visual processing for Tattvashila.

We avoid HDR, oversaturation, sharpening, or blockbuster grading.
We seek the muted, slightly warm, slightly soft look of contemplative
cinema — colour pulled back, contrast tempered, with optional film
grain to remind the viewer they are looking through a lens, not a
screen.
"""
from __future__ import annotations

import numpy as np
from moviepy.editor import VideoClip


def _muted(frame: np.ndarray, saturation: float, contrast: float, warmth: float) -> np.ndarray:
    """Apply muted palette, lowered contrast, gentle warm highlight tint."""
    f = frame.astype(np.float32)

    # Desaturate toward luminance
    if saturation != 1.0:
        lum = (0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2])[..., None]
        f = lum + (f - lum) * float(saturation)

    # Lower contrast around mid-grey
    if contrast != 1.0:
        f = (f - 128.0) * float(contrast) + 128.0

    # Warm highlights — push R up, B down in the upper range
    if warmth > 0:
        # mask is 1 where bright, 0 where dark, in [0,1]
        lum = (0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2])
        mask = np.clip((lum - 140.0) / 115.0, 0.0, 1.0)
        f[..., 0] += mask * (warmth * 30.0)
        f[..., 2] -= mask * (warmth * 18.0)

    return np.clip(f, 0, 255).astype(np.uint8)


def _grain(frame: np.ndarray, intensity: float, rng: np.random.Generator) -> np.ndarray:
    """Add subtle monochrome film grain."""
    if intensity <= 0:
        return frame
    noise = rng.normal(0.0, intensity * 60.0, size=frame.shape[:2]).astype(np.float32)
    out = frame.astype(np.float32) + noise[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def apply_grading(
    clip: VideoClip,
    *,
    muted_palette: bool = True,
    saturation: float = 0.78,
    contrast: float = 0.95,
    warm_highlights: bool = True,
    warmth: float = 0.08,
    film_grain: bool = True,
    grain_intensity: float = 0.05,
    seed: int = 7,
) -> VideoClip:
    """Return `clip` with atmospheric grading applied."""
    rng = np.random.default_rng(seed)
    sat = saturation if muted_palette else 1.0
    warm = warmth if warm_highlights else 0.0
    grain = grain_intensity if film_grain else 0.0

    if sat == 1.0 and contrast == 1.0 and warm == 0.0 and grain == 0.0:
        return clip

    def _process(get_frame, t):
        frame = get_frame(t)
        frame = _muted(frame, sat, contrast, warm)
        frame = _grain(frame, grain, rng)
        return frame

    return clip.fl(_process, apply_to=[])
