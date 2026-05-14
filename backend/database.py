"""Async SQLAlchemy engine + session factory for Supabase Postgres.

Connection MUST go through the Supabase Transaction Pooler (port 6543).
Direct connection (5432) will fail with IPv4 errors in this environment.

Key settings:
  - statement_cache_size=0  (required for pgbouncer transaction pooler)
  - pool_pre_ping=True       (drop dead connections from pooler eviction)
  - expire_on_commit=False   (Pydantic serialisation post-commit)
"""
from __future__ import annotations

import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Load .env from the backend directory regardless of cwd.
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent / ".env")

_raw_url = os.environ["DATABASE_URL"]
# SQLAlchemy needs the +asyncpg driver in the URL
if _raw_url.startswith("postgresql://") and "+asyncpg" not in _raw_url:
    _async_url = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    _async_url = _raw_url

engine = create_async_engine(
    _async_url,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency."""
    async with AsyncSessionLocal() as session:
        yield session


async def dispose() -> None:
    await engine.dispose()
