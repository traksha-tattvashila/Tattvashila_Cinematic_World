"""SQLAlchemy ORM models for Tattvashila.

Design notes:
  - All primary keys are UUIDv4 generated app-side (matches existing Pydantic).
  - All timestamps are `timestamptz` (UTC).
  - `user_id` columns are scaffolded (nullable, no FK) so Supabase Auth can be
    activated later without a migration.
  - JSONB is used for narration/ambient/grading/render_config/rubric/tags so
    the existing Pydantic shapes serialise natively.
  - Segments are normalised into their own table (timelines as first-class
    entity); position column preserves order.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    subtitle: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    narration: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ambient: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    grading: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    render_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    latest_render_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    last_rubric: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    last_retrieval_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
        server_default=text("now()"), onupdate=_now,
    )

    segments: Mapped[list["Segment"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Segment.position",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_projects_updated_at", "updated_at"),
        Index("ix_projects_user_id", "user_id"),
    )


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="clip")
    asset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=6.0)
    start_offset: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    transition_in: Mapped[str] = mapped_column(String(32), nullable=False, default="fade")
    transition_in_duration: Mapped[float] = mapped_column(Float, nullable=False, default=1.5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
        server_default=text("now()"),
    )

    project: Mapped["Project"] = relationship(back_populates="segments")

    __table_args__ = (
        CheckConstraint("kind IN ('clip','pause')", name="segments_kind_chk"),
        Index("ix_segments_project_position", "project_id", "position"),
    )


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_type: Mapped[str] = mapped_column(String(128), nullable=False, default="application/octet-stream")
    size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    provider_external_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint(
            "kind IN ('clip','narration','ambient','render')",
            name="media_assets_kind_chk",
        ),
        Index("ix_media_kind_deleted_created", "kind", "is_deleted", "created_at"),
        Index("ix_media_storage_path", "storage_path"),
    )


class RenderJob(Base):
    __tablename__ = "render_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stage: Mapped[str] = mapped_column(String(64), nullable=False, default="queued")
    output_asset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    queue_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','rendering','completed','failed')",
            name="render_jobs_status_chk",
        ),
        Index("ix_render_jobs_project_created", "project_id", "created_at"),
        Index("ix_render_jobs_active", "project_id", "status"),
    )


class RetrievalSession(Base):
    __tablename__ = "retrieval_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    project_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rubric: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    contemplative_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    narration_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    per_query: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
        server_default=text("now()"),
    )

    clips: Mapped[list["SelectedClip"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_retrieval_sessions_project_created", "project_id", "created_at"),
    )


class SelectedClip(Base):
    __tablename__ = "selected_clips"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    retrieval_session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("retrieval_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[str] = mapped_column(Text, nullable=False, default="")
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trim_start: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trim_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    imported_asset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
        server_default=text("now()"),
    )

    session: Mapped["RetrievalSession"] = relationship(back_populates="clips")

    __table_args__ = (
        Index("ix_selected_clips_session", "retrieval_session_id"),
    )
