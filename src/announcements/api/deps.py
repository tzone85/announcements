"""FastAPI dependency providers.

These resolve from the app state — populated by the `create_app` factory.
"""

from __future__ import annotations

from fastapi import Request

from announcements.config import Settings
from announcements.services.announcement_service import AnnouncementService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


def get_service(request: Request) -> AnnouncementService:
    return request.app.state.service  # type: ignore[no-any-return]
