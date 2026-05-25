"""Webhook delivery — pluggable notifier strategy.

Production wiring uses ``HttpWebhookNotifier`` with subscriber URLs read from config.
Tests substitute ``FakeNotifier`` or ``NullWebhookNotifier``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal, Protocol

import httpx
from pydantic import BaseModel

from announcements.domain.models import Announcement

logger = logging.getLogger(__name__)

WebhookKind = Literal["announcement.created", "announcement.updated", "announcement.deleted"]


class WebhookEvent(BaseModel):
    kind: WebhookKind
    announcement: Announcement


class NotifierError(RuntimeError):
    """All subscribers failed to receive the event."""


class WebhookNotifier(Protocol):
    async def notify(self, event: WebhookEvent) -> None: ...


class NullWebhookNotifier:
    """No-op notifier — used when webhooks are disabled in config."""

    async def notify(self, event: WebhookEvent) -> None:  # noqa: ARG002
        return None


class HttpWebhookNotifier:
    """Fan-out POST to every subscriber URL.

    - Each subscriber receives the same JSON payload independently.
    - A subscriber failure is logged but does not block siblings.
    - If *every* subscriber fails, raises NotifierError so the caller can react.
    - Empty subscriber list is a valid no-op.
    """

    def __init__(
        self,
        *,
        subscribers: list[str],
        http: httpx.AsyncClient,
        timeout: float = 5.0,
    ) -> None:
        self._subscribers = list(subscribers)
        self._http = http
        self._timeout = timeout

    async def notify(self, event: WebhookEvent) -> None:
        if not self._subscribers:
            return
        payload = event.model_dump(mode="json")
        results = await asyncio.gather(
            *[self._post(url, payload) for url in self._subscribers],
            return_exceptions=True,
        )
        successes = [r for r in results if r is True]
        if not successes:
            raise NotifierError(f"all {len(self._subscribers)} subscribers failed for {event.kind}")

    async def _post(self, url: str, payload: dict[str, object]) -> bool:
        try:
            response = await self._http.post(url, json=payload, timeout=self._timeout)
            response.raise_for_status()
            return True
        except (TimeoutError, httpx.HTTPError) as exc:
            logger.warning("webhook delivery failed: url=%s err=%s", url, exc)
            return False
