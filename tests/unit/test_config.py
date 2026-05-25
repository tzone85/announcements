"""Settings behaviour — especially the use_real_database flag."""

from __future__ import annotations

import pytest

from announcements.config import Settings


@pytest.mark.parametrize(
    "url,expected",
    [
        ("postgresql+psycopg://u:p@h/d", True),
        ("postgresql://u:p@h/d", True),
        ("sqlite:///./local.db", True),
        ("sqlite+aiosqlite:///./local.db", True),
        ("memory://", False),
    ],
)
def test_use_real_database(url: str, expected: bool) -> None:
    s = Settings(database_url=url)
    assert s.use_real_database is expected


def test_defaults_are_safe_for_dev() -> None:
    s = Settings()
    assert s.api_key  # not empty
    assert s.database_url  # not empty
    assert s.webhook_subscribers == []
