"""Integration tests against a real SQL database.

Default: ephemeral SQLite database under tmp_path. CI sets DATABASE_URL
to a Postgres service container to exercise the production driver.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio

from announcements.db.orm import Base
from announcements.db.session import build_engine, build_session_factory
from announcements.domain.models import AnnouncementCreate, AnnouncementUpdate
from announcements.repositories.protocol import AnnouncementNotFoundError
from announcements.repositories.sqlalchemy import SqlAlchemyAnnouncementRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def database_url(tmp_path: object) -> str:
    env = os.getenv("ANNOUNCEMENTS_DATABASE_URL")
    if env:
        return env
    db_file = f"{tmp_path}/announcements_it.db"
    return f"sqlite:///{db_file}"


@pytest_asyncio.fixture
async def repo(database_url: str) -> SqlAlchemyAnnouncementRepository:
    engine = build_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = build_session_factory(database_url)
    return SqlAlchemyAnnouncementRepository(session_factory=factory)


async def test_create_assigns_id(repo: SqlAlchemyAnnouncementRepository) -> None:
    first = await repo.create(AnnouncementCreate(message="a", author="x"))
    second = await repo.create(AnnouncementCreate(message="b", author="y"))
    assert first.id < second.id


async def test_list_pagination_excludes_deleted(
    repo: SqlAlchemyAnnouncementRepository,
) -> None:
    for i in range(5):
        await repo.create(AnnouncementCreate(message=f"m{i}", author="x"))
    third = await repo.list(limit=10, offset=0)
    assert third.total == 5
    target = third.items[2]
    await repo.delete(target.id)
    after = await repo.list(limit=10, offset=0)
    assert after.total == 4


async def test_get_missing_raises(repo: SqlAlchemyAnnouncementRepository) -> None:
    with pytest.raises(AnnouncementNotFoundError):
        await repo.get(999)


async def test_update_partial(repo: SqlAlchemyAnnouncementRepository) -> None:
    created = await repo.create(AnnouncementCreate(message="old", author="alice"))
    updated = await repo.update(created.id, AnnouncementUpdate(message="new"))
    assert updated.message == "new"
    assert updated.author == "alice"
    assert updated.updated_at >= created.updated_at


async def test_soft_delete(repo: SqlAlchemyAnnouncementRepository) -> None:
    created = await repo.create(AnnouncementCreate(message="m", author="x"))
    await repo.delete(created.id)
    with pytest.raises(AnnouncementNotFoundError):
        await repo.get(created.id)
    revived = await repo.get(created.id, include_deleted=True)
    assert revived.is_deleted is True
