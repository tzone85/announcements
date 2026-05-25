"""Service-layer tests using in-memory repo + fake notifier."""

from __future__ import annotations

import pytest

from announcements.domain.models import AnnouncementCreate, AnnouncementUpdate
from announcements.repositories.in_memory import InMemoryAnnouncementRepository
from announcements.services.announcement_service import AnnouncementService
from announcements.services.webhook_notifier import (
    NotifierError,
    WebhookEvent,
    WebhookNotifier,
)


class FakeNotifier(WebhookNotifier):
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[WebhookEvent] = []
        self.fail = fail

    async def notify(self, event: WebhookEvent) -> None:
        if self.fail:
            raise NotifierError("fake failure")
        self.calls.append(event)


@pytest.fixture
def repo() -> InMemoryAnnouncementRepository:
    return InMemoryAnnouncementRepository()


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()


@pytest.fixture
def service(repo: InMemoryAnnouncementRepository, notifier: FakeNotifier) -> AnnouncementService:
    return AnnouncementService(repo=repo, notifier=notifier)


class TestCreate:
    async def test_creates_and_notifies(
        self, service: AnnouncementService, notifier: FakeNotifier
    ) -> None:
        a = await service.create(AnnouncementCreate(message="hi", author="alice"))
        assert a.id == 1
        assert len(notifier.calls) == 1
        assert notifier.calls[0].kind == "announcement.created"
        assert notifier.calls[0].announcement.id == 1

    async def test_notifier_failure_does_not_break_create(
        self,
        repo: InMemoryAnnouncementRepository,
    ) -> None:
        service = AnnouncementService(repo=repo, notifier=FakeNotifier(fail=True))
        a = await service.create(AnnouncementCreate(message="hi", author="alice"))
        assert a.id == 1
        page = await repo.list(limit=10, offset=0)
        assert page.total == 1


class TestUpdate:
    async def test_updates_and_emits_event(
        self, service: AnnouncementService, notifier: FakeNotifier
    ) -> None:
        a = await service.create(AnnouncementCreate(message="m", author="x"))
        notifier.calls.clear()
        updated = await service.update(a.id, AnnouncementUpdate(message="m2"))
        assert updated.message == "m2"
        assert len(notifier.calls) == 1
        assert notifier.calls[0].kind == "announcement.updated"


class TestDelete:
    async def test_deletes_and_emits_event(
        self, service: AnnouncementService, notifier: FakeNotifier
    ) -> None:
        a = await service.create(AnnouncementCreate(message="m", author="x"))
        notifier.calls.clear()
        await service.delete(a.id)
        assert len(notifier.calls) == 1
        assert notifier.calls[0].kind == "announcement.deleted"
