"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-25
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("message", sa.String(length=5000), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_announcements_deleted_at_id",
        "announcements",
        ["deleted_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_announcements_deleted_at_id", table_name="announcements")
    op.drop_table("announcements")
