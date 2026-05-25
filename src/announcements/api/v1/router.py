"""HTTP routes for /api/v1/announcements."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from announcements.api.auth import require_api_key
from announcements.api.deps import get_service
from announcements.domain.models import (
    MAX_PAGE_LIMIT,
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
    Page,
)
from announcements.repositories.protocol import AnnouncementNotFoundError
from announcements.services.announcement_service import AnnouncementService

router = APIRouter(prefix="/api/v1/announcements", tags=["announcements"])


@router.get("", response_model=Page[Announcement])
async def list_announcements(
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
    service: AnnouncementService = Depends(get_service),
) -> Page[Announcement]:
    return await service.list(limit=limit, offset=offset, include_deleted=include_deleted)


@router.get("/{announcement_id}", response_model=Announcement)
async def get_announcement(
    announcement_id: int,
    service: AnnouncementService = Depends(get_service),
) -> Announcement:
    try:
        return await service.get(announcement_id)
    except AnnouncementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "",
    response_model=Announcement,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
async def create_announcement(
    payload: AnnouncementCreate,
    service: AnnouncementService = Depends(get_service),
) -> Announcement:
    return await service.create(payload)


@router.patch(
    "/{announcement_id}",
    response_model=Announcement,
    dependencies=[Depends(require_api_key)],
)
async def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    service: AnnouncementService = Depends(get_service),
) -> Announcement:
    try:
        return await service.update(announcement_id, payload)
    except AnnouncementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete(
    "/{announcement_id}",
    response_class=Response,
    responses={204: {"description": "Deleted"}, 404: {"description": "Not found"}},
    dependencies=[Depends(require_api_key)],
)
async def delete_announcement(
    announcement_id: int,
    service: AnnouncementService = Depends(get_service),
) -> Response:
    try:
        await service.delete(announcement_id)
    except AnnouncementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
