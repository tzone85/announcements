"""Business-logic layer between API and repository.

The service owns the transactional unit of work:
1. Mutate via the repository.
2. Emit a webhook event after each mutation.

Webhook failures are isolated — a delivery error does not roll the data change back.
This matches at-most-once-delivery semantics and keeps the system available.
"""

from __future__ import annotations

import logging

from announcements.domain.models import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
    Page,
)
from announcements.repositories.protocol import AnnouncementRepository
from announcements.services.webhook_notifier import (
    NotifierError,
    WebhookEvent,
    WebhookNotifier,
)

logger = logging.getLogger(__name__)


class AnnouncementService:
    def __init__(self, *, repo: AnnouncementRepository, notifier: WebhookNotifier) -> None:
        self._repo = repo
        self._notifier = notifier

    async def create(self, data: AnnouncementCreate) -> Announcement:
        announcement = await self._repo.create(data)
        await self._notify("announcement.created", announcement)
        return announcement

    async def list(
        self, *, limit: int, offset: int, include_deleted: bool = False
    ) -> Page[Announcement]:
        return await self._repo.list(limit=limit, offset=offset, include_deleted=include_deleted)

    async def get(self, announcement_id: int) -> Announcement:
        return await self._repo.get(announcement_id)

    async def update(self, announcement_id: int, patch: AnnouncementUpdate) -> Announcement:
        updated = await self._repo.update(announcement_id, patch)
        await self._notify("announcement.updated", updated)
        return updated

    async def delete(self, announcement_id: int) -> None:
        existing = await self._repo.get(announcement_id)
        await self._repo.delete(announcement_id)
        await self._notify("announcement.deleted", existing)

    async def _notify(self, kind: str, announcement: Announcement) -> None:
        try:
            event = WebhookEvent.model_validate({"kind": kind, "announcement": announcement})
            await self._notifier.notify(event)
        except NotifierError as exc:
            logger.warning("webhook notify failed: kind=%s err=%s", kind, exc)
