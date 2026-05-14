"""Default cinematic timing & atmospheric values.

These defaults encode the editorial philosophy of Tattvashila:
slowness, restraint, breathing room. They are intentionally
opinionated. Override per-render via the project configuration.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CinematicDefaults:
    # Pacing
    minimum_clip_seconds: float = 4.0       # nothing flashes by
    preferred_clip_seconds: float = 8.0
    transition_seconds: float = 1.5         # slow dissolves
    long_pause_seconds: float = 3.0         # black frames between thoughts

    # Atmosphere
    grain_intensity_default: float = 0.05
    saturation_default: float = 0.78
    contrast_default: float = 0.95
    warmth_default: float = 0.08

    # Audio
    narration_lead_in: float = 1.5          # silence before narration starts
    ambient_default_volume: float = 0.30
    ambient_fade_in: float = 3.0
    ambient_fade_out: float = 4.0

    # Output
    fps_default: int = 24
    width_default: int = 1920
    height_default: int = 1080
    video_bitrate_default: str = "6000k"
    audio_bitrate_default: str = "192k"
    black_color: tuple = (16, 15, 14)        # deep charcoal, never pure black
