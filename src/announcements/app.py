"""Application factory.

`create_app` composes Settings, repository, notifier, service, and routers.
Pass overrides for tests; production reads everything from env.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from announcements.api.v1.router import router as v1_router
from announcements.config import Settings
from announcements.repositories.in_memory import InMemoryAnnouncementRepository
from announcements.repositories.protocol import AnnouncementRepository
from announcements.services.announcement_service import AnnouncementService
from announcements.services.webhook_notifier import (
    HttpWebhookNotifier,
    NullWebhookNotifier,
    WebhookNotifier,
)


def create_app(
    *,
    settings: Settings | None = None,
    repository: AnnouncementRepository | None = None,
    notifier: WebhookNotifier | None = None,
) -> FastAPI:
    settings = settings or Settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    repository = repository or _build_repository(settings)
    http_client: httpx.AsyncClient | None = None
    if notifier is None:
        notifier, http_client = _build_notifier(settings)

    service = AnnouncementService(repo=repository, notifier=notifier)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if http_client is not None:
                await http_client.aclose()

    app = FastAPI(
        title="Employee Announcements Center",
        version="1.0.0",
        docs_url="/swagger",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.service = service
    app.state.repository = repository
    app.state.notifier = notifier

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {
            "service": "announcements",
            "version": "1.0.0",
            "docs": "/swagger",
        }

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(v1_router)
    return app


def _build_repository(settings: Settings) -> AnnouncementRepository:
    if not settings.use_real_database:
        return InMemoryAnnouncementRepository()
    from announcements.db.session import build_session_factory
    from announcements.repositories.sqlalchemy import SqlAlchemyAnnouncementRepository

    session_factory = build_session_factory(settings.database_url)
    return SqlAlchemyAnnouncementRepository(session_factory=session_factory)


def _build_notifier(
    settings: Settings,
) -> tuple[WebhookNotifier, httpx.AsyncClient | None]:
    if not settings.webhook_subscribers:
        return NullWebhookNotifier(), None
    client = httpx.AsyncClient()
    return (
        HttpWebhookNotifier(subscribers=settings.webhook_subscribers, http=client),
        client,
    )
