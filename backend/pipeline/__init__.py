"""
Tattvashila cinematic pipeline.

A reusable module for assembling contemplative cinematic films from
clips, narration, and ambient sound. Designed for slow cinema:
restrained transitions, observational pacing, institutional language.
"""
from .config import CinematicDefaults  # noqa: F401
from .renderer import render_project, RenderContext  # noqa: F401
