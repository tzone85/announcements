"""In-memory repository — for unit tests and local development without Postgres."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from announcements.domain.models import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
    Page,
)
from announcements.repositories.protocol import AnnouncementNotFoundError


def _utcnow() -> datetime:
    return datetime.now(UTC)


class InMemoryAnnouncementRepository:
    """Thread-safe in-memory store. State lives for the process lifetime."""

    def __init__(self) -> None:
        self._items: dict[int, Announcement] = {}
        self._next_id = 1
        self._lock = asyncio.Lock()

    async def create(self, data: AnnouncementCreate) -> Announcement:
        async with self._lock:
            now = _utcnow()
            announcement = Announcement(
                id=self._next_id,
                message=data.message,
                author=data.author,
                created_at=now,
                updated_at=now,
                deleted_at=None,
            )
            self._items[self._next_id] = announcement
            self._next_id += 1
            return announcement

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        include_deleted: bool = False,
    ) -> Page[Announcement]:
        async with self._lock:
            visible = [a for a in self._items.values() if include_deleted or a.deleted_at is None]
            visible.sort(key=lambda a: a.id)
            window = visible[offset : offset + limit]
            return Page(items=window, total=len(visible), limit=limit, offset=offset)

    async def get(self, announcement_id: int, *, include_deleted: bool = False) -> Announcement:
        async with self._lock:
            announcement = self._items.get(announcement_id)
            if announcement is None:
                raise AnnouncementNotFoundError(announcement_id)
            if announcement.deleted_at is not None and not include_deleted:
                raise AnnouncementNotFoundError(announcement_id)
            return announcement

    async def update(self, announcement_id: int, patch: AnnouncementUpdate) -> Announcement:
        async with self._lock:
            existing = self._items.get(announcement_id)
            if existing is None or existing.deleted_at is not None:
                raise AnnouncementNotFoundError(announcement_id)
            updated = existing.model_copy(
                update={
                    **patch.model_dump(exclude_unset=True),
                    "updated_at": _utcnow(),
                }
            )
            self._items[announcement_id] = updated
            return updated

    async def delete(self, announcement_id: int) -> None:
        async with self._lock:
            existing = self._items.get(announcement_id)
            if existing is None or existing.deleted_at is not None:
                raise AnnouncementNotFoundError(announcement_id)
            self._items[announcement_id] = existing.model_copy(update={"deleted_at": _utcnow()})
