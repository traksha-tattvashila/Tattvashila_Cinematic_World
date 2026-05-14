"""Pydantic data models for Tattvashila projects, segments, and render jobs."""
from __future__ import annotations

from typing import List, Optional, Literal
from datetime import datetime, timezone
import uuid

from pydantic import BaseModel, Field, ConfigDict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------
MediaKind = Literal["clip", "narration", "ambient", "render"]


class MediaAsset(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=_uuid)
    kind: MediaKind
    storage_path: str
    original_filename: str
    content_type: str
    size: int = 0
    duration: Optional[float] = None  # seconds (probed from media)
    width: Optional[int] = None
    height: Optional[int] = None
    is_deleted: bool = False
    # Optional attribution for retrieved stock clips
    provider: Optional[str] = None          # "pexels" | "pixabay" | "local"
    provider_external_id: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    created_at: str = Field(default_factory=_now_iso)


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------
TransitionKind = Literal["none", "fade", "dissolve", "crossfade"]


class Segment(BaseModel):
    id: str = Field(default_factory=_uuid)
    kind: Literal["clip", "pause"]
    asset_id: Optional[str] = None
    duration: float = 6.0           # seconds on the timeline
    start_offset: float = 0.0       # seconds into source media
    transition_in: TransitionKind = "fade"
    transition_in_duration: float = 1.5


class NarrationConfig(BaseModel):
    source: Literal["none", "upload", "tts"] = "none"
    asset_id: Optional[str] = None
    tts_text: Optional[str] = None
    tts_voice: str = "echo"
    tts_model: str = "tts-1-hd"
    tts_speed: float = 0.95
    offset_seconds: float = 1.5     # silence before narration starts
    volume: float = 1.0


class AmbientConfig(BaseModel):
    source: Literal["none", "builtin", "upload"] = "none"
    builtin_key: Optional[str] = None
    asset_id: Optional[str] = None
    volume: float = 0.30
    fade_in: float = 3.0
    fade_out: float = 4.0


class GradingConfig(BaseModel):
    film_grain: bool = True
    grain_intensity: float = 0.05    # 0.0 – 0.2
    muted_palette: bool = True
    saturation: float = 0.78         # < 1.0 desaturates
    warm_highlights: bool = True
    warmth: float = 0.08             # 0.0 – 0.2
    contrast: float = 0.95           # < 1.0 lowers contrast


class RenderConfig(BaseModel):
    width: int = 1920
    height: int = 1080
    fps: int = 24
    video_bitrate: str = "6000k"
    audio_bitrate: str = "192k"


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=_uuid)
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    segments: List[Segment] = Field(default_factory=list)
    narration: NarrationConfig = Field(default_factory=NarrationConfig)
    ambient: AmbientConfig = Field(default_factory=AmbientConfig)
    grading: GradingConfig = Field(default_factory=GradingConfig)
    render_config: RenderConfig = Field(default_factory=RenderConfig)
    latest_render_id: Optional[str] = None
    # Sticky retrieval state — last rubric Claude produced for this project
    last_rubric: Optional[dict] = None
    last_retrieval_at: Optional[str] = None
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)


class ProjectCreate(BaseModel):
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    segments: Optional[List[Segment]] = None
    narration: Optional[NarrationConfig] = None
    ambient: Optional[AmbientConfig] = None
    grading: Optional[GradingConfig] = None
    render_config: Optional[RenderConfig] = None


# ---------------------------------------------------------------------------
# Render Jobs
# ---------------------------------------------------------------------------
RenderStatus = Literal["queued", "rendering", "completed", "failed"]


class RenderJob(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=_uuid)
    project_id: str
    status: RenderStatus = "queued"
    progress: float = 0.0
    stage: str = "queued"
    output_asset_id: Optional[str] = None
    output_size_bytes: Optional[int] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    queue_position: Optional[int] = None  # only meaningful while status="queued"
    created_at: str = Field(default_factory=_now_iso)


# ---------------------------------------------------------------------------
# TTS payloads
# ---------------------------------------------------------------------------
class TTSGenerateRequest(BaseModel):
    text: str
    voice: str = "echo"
    model: str = "tts-1-hd"
    speed: float = 0.95


# ---------------------------------------------------------------------------
# Atmospheric Retrieval
# ---------------------------------------------------------------------------
class AnalyzeSceneRequest(BaseModel):
    description: str
    contemplative_mode: bool = True
    narration_text: Optional[str] = None


class SearchRequest(BaseModel):
    description: Optional[str] = None
    rubric: Optional[dict] = None
    contemplative_mode: bool = True
    narration_text: Optional[str] = None
    per_query: int = 4


class ProviderClipModel(BaseModel):
    provider: str
    external_id: str
    title: str = ""
    tags: List[str] = Field(default_factory=list)
    duration: float = 0.0
    width: int = 0
    height: int = 0
    thumbnail_url: str = ""
    preview_url: str = ""
    download_url: str = ""
    author: str = ""
    source_url: str = ""
    query: str = ""
    score: Optional[float] = None
    rationale: Optional[str] = None


class AssembleClipSelection(BaseModel):
    """A selected stock clip the user wants imported & placed on the timeline."""
    provider: Literal["pexels", "pixabay", "local"]
    external_id: str
    title: str = ""
    tags: List[str] = Field(default_factory=list)
    duration: float = 0.0
    width: int = 0
    height: int = 0
    download_url: str
    preview_url: str = ""
    thumbnail_url: str = ""
    author: str = ""
    source_url: str = ""
    # Optional trim override — user-tuned in the dialog before assembly
    trim_start: Optional[float] = None
    trim_duration: Optional[float] = None


class AssembleRequest(BaseModel):
    project_id: str
    selections: List[AssembleClipSelection]
    pacing: str = "slow"               # glacial | slow | measured
    transition: str = "crossfade"      # fade | crossfade | dissolve
    rubric_atmosphere: str = ""
    rubric: Optional[dict] = None      # full rubric (persisted on project)
