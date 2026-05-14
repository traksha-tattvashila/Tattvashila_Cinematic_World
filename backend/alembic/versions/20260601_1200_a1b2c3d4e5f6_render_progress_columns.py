"""render progress columns

Adds queue_position and output_size_bytes to render_jobs to support the
dedicated cinematic render progress experience.

Revision ID: a1b2c3d4e5f6
Revises: 9c0580ff1f76
Create Date: 2026-06-01 12:00:00+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9c0580ff1f76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "render_jobs",
        sa.Column("queue_position", sa.Integer(), nullable=True),
    )
    op.add_column(
        "render_jobs",
        sa.Column("output_size_bytes", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("render_jobs", "output_size_bytes")
    op.drop_column("render_jobs", "queue_position")
