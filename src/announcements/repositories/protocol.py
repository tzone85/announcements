"""Repository contract — every storage backend implements this Protocol."""

from __future__ import annotations

from typing import Protocol

from announcements.domain.models import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
    Page,
)


class AnnouncementNotFoundError(LookupError):
    """Raised when an announcement does not exist (or is soft-deleted and the caller
    did not opt into ``include_deleted``)."""

    def __init__(self, announcement_id: int) -> None:
        super().__init__(f"announcement {announcement_id} not found")
        self.announcement_id = announcement_id


class AnnouncementRepository(Protocol):
    """Storage contract.

    Implementations: ``InMemoryAnnouncementRepository`` (tests, dev),
    ``SqlAlchemyAnnouncementRepository`` (production).
    """

    async def create(self, data: AnnouncementCreate) -> Announcement: ...

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        include_deleted: bool = False,
    ) -> Page[Announcement]: ...

    async def get(self, announcement_id: int, *, include_deleted: bool = False) -> Announcement: ...

    async def update(self, announcement_id: int, patch: AnnouncementUpdate) -> Announcement: ...

    async def delete(self, announcement_id: int) -> None: ...
