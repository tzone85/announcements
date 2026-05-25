"""Unit tests for the in-memory repository.

The same suite must pass against the Postgres repository — it lives in
tests/integration and reuses these scenarios via a shared fixture set.
"""

from __future__ import annotations

import pytest

from announcements.domain.models import AnnouncementCreate, AnnouncementUpdate
from announcements.repositories.in_memory import InMemoryAnnouncementRepository
from announcements.repositories.protocol import (
    AnnouncementNotFoundError,
    AnnouncementRepository,
)


@pytest.fixture
def repo() -> AnnouncementRepository:
    return InMemoryAnnouncementRepository()


class TestCreate:
    async def test_assigns_monotonic_id(self, repo: AnnouncementRepository) -> None:
        first = await repo.create(AnnouncementCreate(message="a", author="x"))
        second = await repo.create(AnnouncementCreate(message="b", author="y"))
        assert first.id == 1
        assert second.id == 2

    async def test_sets_created_and_updated_to_same_instant(
        self, repo: AnnouncementRepository
    ) -> None:
        a = await repo.create(AnnouncementCreate(message="a", author="x"))
        assert a.created_at == a.updated_at
        assert a.deleted_at is None


class TestList:
    async def test_empty_when_no_announcements(self, repo: AnnouncementRepository) -> None:
        page = await repo.list(limit=10, offset=0)
        assert page.items == []
        assert page.total == 0

    async def test_pagination_returns_slice(self, repo: AnnouncementRepository) -> None:
        for i in range(5):
            await repo.create(AnnouncementCreate(message=f"m{i}", author="x"))
        page = await repo.list(limit=2, offset=1)
        assert len(page.items) == 2
        assert page.total == 5
        assert page.has_more is True

    async def test_excludes_soft_deleted_by_default(self, repo: AnnouncementRepository) -> None:
        a = await repo.create(AnnouncementCreate(message="alive", author="x"))
        b = await repo.create(AnnouncementCreate(message="goner", author="x"))
        await repo.delete(b.id)
        page = await repo.list(limit=10, offset=0)
        ids = [item.id for item in page.items]
        assert a.id in ids
        assert b.id not in ids
        assert page.total == 1

    async def test_include_deleted_returns_all(self, repo: AnnouncementRepository) -> None:
        a = await repo.create(AnnouncementCreate(message="alive", author="x"))
        b = await repo.create(AnnouncementCreate(message="goner", author="x"))
        await repo.delete(b.id)
        page = await repo.list(limit=10, offset=0, include_deleted=True)
        assert {item.id for item in page.items} == {a.id, b.id}
        assert page.total == 2


class TestGet:
    async def test_returns_announcement(self, repo: AnnouncementRepository) -> None:
        created = await repo.create(AnnouncementCreate(message="m", author="x"))
        fetched = await repo.get(created.id)
        assert fetched.id == created.id

    async def test_raises_when_missing(self, repo: AnnouncementRepository) -> None:
        with pytest.raises(AnnouncementNotFoundError):
            await repo.get(999)

    async def test_raises_when_soft_deleted_by_default(self, repo: AnnouncementRepository) -> None:
        a = await repo.create(AnnouncementCreate(message="m", author="x"))
        await repo.delete(a.id)
        with pytest.raises(AnnouncementNotFoundError):
            await repo.get(a.id)

    async def test_returns_deleted_when_include_deleted(self, repo: AnnouncementRepository) -> None:
        a = await repo.create(AnnouncementCreate(message="m", author="x"))
        await repo.delete(a.id)
        fetched = await repo.get(a.id, include_deleted=True)
        assert fetched.is_deleted is True


class TestUpdate:
    async def test_partial_update_changes_only_supplied_fields(
        self, repo: AnnouncementRepository
    ) -> None:
        original = await repo.create(AnnouncementCreate(message="old", author="alice"))
        updated = await repo.update(original.id, AnnouncementUpdate(message="new"))
        assert updated.message == "new"
        assert updated.author == "alice"

    async def test_updates_updated_at(self, repo: AnnouncementRepository) -> None:
        original = await repo.create(AnnouncementCreate(message="m", author="x"))
        updated = await repo.update(original.id, AnnouncementUpdate(message="m2"))
        assert updated.updated_at >= original.updated_at
        assert updated.created_at == original.created_at

    async def test_raises_when_missing(self, repo: AnnouncementRepository) -> None:
        with pytest.raises(AnnouncementNotFoundError):
            await repo.update(999, AnnouncementUpdate(message="x"))


class TestDelete:
    async def test_soft_deletes(self, repo: AnnouncementRepository) -> None:
        a = await repo.create(AnnouncementCreate(message="m", author="x"))
        await repo.delete(a.id)
        page = await repo.list(limit=10, offset=0, include_deleted=True)
        item = next(i for i in page.items if i.id == a.id)
        assert item.is_deleted is True

    async def test_raises_when_missing(self, repo: AnnouncementRepository) -> None:
        with pytest.raises(AnnouncementNotFoundError):
            await repo.delete(999)

    async def test_double_delete_raises(self, repo: AnnouncementRepository) -> None:
        a = await repo.create(AnnouncementCreate(message="m", author="x"))
        await repo.delete(a.id)
        with pytest.raises(AnnouncementNotFoundError):
            await repo.delete(a.id)
