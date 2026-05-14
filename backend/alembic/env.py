"""Alembic environment — sync driver (psycopg2) for migrations.

Reads DATABASE_URL from backend/.env and rewrites the scheme to use psycopg2
(synchronous) since Alembic does not natively support async drivers.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from db_models import Base  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Force the sync driver for Alembic
raw_url = os.environ["DATABASE_URL"]
if raw_url.startswith("postgresql+asyncpg://"):
    sync_url = raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
elif raw_url.startswith("postgresql://"):
    sync_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
else:
    sync_url = raw_url
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
