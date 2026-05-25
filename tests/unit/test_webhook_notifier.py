"""HttpWebhookNotifier tests using respx to fake outbound HTTP."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx

from announcements.domain.models import Announcement
from announcements.services.webhook_notifier import (
    HttpWebhookNotifier,
    NotifierError,
    NullWebhookNotifier,
    WebhookEvent,
)


def _sample_announcement() -> Announcement:
    now = datetime.now(UTC)
    return Announcement(
        id=1,
        message="hello",
        author="alice",
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


class TestNullWebhookNotifier:
    async def test_does_nothing(self) -> None:
        n = NullWebhookNotifier()
        await n.notify(
            WebhookEvent(kind="announcement.created", announcement=_sample_announcement())
        )


class TestHttpWebhookNotifier:
    @respx.mock
    async def test_posts_to_every_subscriber(self) -> None:
        urls = ["https://hook1.example.com/notify", "https://hook2.example.com/notify"]
        routes = [respx.post(u).mock(return_value=httpx.Response(204)) for u in urls]
        async with httpx.AsyncClient() as client:
            notifier = HttpWebhookNotifier(subscribers=urls, http=client, timeout=1.0)
            await notifier.notify(
                WebhookEvent(kind="announcement.created", announcement=_sample_announcement())
            )
        for r in routes:
            assert r.called

    @respx.mock
    async def test_payload_shape(self) -> None:
        route = respx.post("https://hook.example.com").mock(return_value=httpx.Response(200))
        async with httpx.AsyncClient() as client:
            notifier = HttpWebhookNotifier(subscribers=["https://hook.example.com"], http=client)
            await notifier.notify(
                WebhookEvent(kind="announcement.created", announcement=_sample_announcement())
            )
        body = route.calls[0].request.content.decode()
        assert '"kind":"announcement.created"' in body
        assert '"announcement"' in body
        assert '"id":1' in body

    @respx.mock
    async def test_raises_notifier_error_when_all_fail(self) -> None:
        respx.post("https://bad.example.com").mock(return_value=httpx.Response(500))
        async with httpx.AsyncClient() as client:
            notifier = HttpWebhookNotifier(subscribers=["https://bad.example.com"], http=client)
            with pytest.raises(NotifierError):
                await notifier.notify(
                    WebhookEvent(kind="announcement.created", announcement=_sample_announcement())
                )

    @respx.mock
    async def test_partial_failure_does_not_raise(self) -> None:
        respx.post("https://good.example.com").mock(return_value=httpx.Response(200))
        respx.post("https://bad.example.com").mock(return_value=httpx.Response(500))
        async with httpx.AsyncClient() as client:
            notifier = HttpWebhookNotifier(
                subscribers=["https://good.example.com", "https://bad.example.com"],
                http=client,
            )
            await notifier.notify(
                WebhookEvent(kind="announcement.created", announcement=_sample_announcement())
            )

    async def test_no_subscribers_is_noop(self) -> None:
        async with httpx.AsyncClient() as client:
            notifier = HttpWebhookNotifier(subscribers=[], http=client)
            await notifier.notify(
                WebhookEvent(kind="announcement.created", announcement=_sample_announcement())
            )
