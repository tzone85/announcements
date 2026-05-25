"""Verify alembic upgrade head produces the expected schema."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]


def _alembic(env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["alembic", *args],
        cwd=REPO_ROOT,
        env={**os.environ, **env},
        check=True,
        capture_output=True,
        text=True,
    )


def test_upgrade_head_creates_announcements_table(tmp_path: Path) -> None:
    db_file = tmp_path / "alembic_test.db"
    sync_url = f"sqlite:///{db_file}"
    _alembic({"ANNOUNCEMENTS_DATABASE_URL": sync_url}, "upgrade", "head")

    engine = create_engine(sync_url)
    inspector = inspect(engine)
    assert "announcements" in inspector.get_table_names()
    cols = {c["name"] for c in inspector.get_columns("announcements")}
    assert cols == {"id", "message", "author", "created_at", "updated_at", "deleted_at"}


def test_downgrade_base_removes_table(tmp_path: Path) -> None:
    db_file = tmp_path / "alembic_test2.db"
    sync_url = f"sqlite:///{db_file}"
    env = {"ANNOUNCEMENTS_DATABASE_URL": sync_url}
    _alembic(env, "upgrade", "head")
    _alembic(env, "downgrade", "base")

    engine = create_engine(sync_url)
    inspector = inspect(engine)
    assert "announcements" not in inspector.get_table_names()
