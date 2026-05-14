"""
Atmospheric Retrieval — find contemplative stock footage that matches
a slow-cinema rubric. Composed of:

    scene_analyzer   : narration / description → cinematic rubric
    providers        : Pexels, Pixabay, local archive
    ranker           : Claude scores each clip for restraint + relevance
    trim             : adaptive 4–12s trim window
"""
from .scene_analyzer import analyze_scene  # noqa: F401
from .providers import search_all, ProviderClip  # noqa: F401
from .ranker import rank_clips  # noqa: F401
from .trim import adaptive_trim  # noqa: F401
