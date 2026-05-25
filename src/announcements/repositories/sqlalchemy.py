"""SQLAlchemy implementation of the AnnouncementRepository protocol."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from announcements.db.orm import AnnouncementORM
from announcements.db.session import session_scope
from announcements.domain.models import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
    Page,
)
from announcements.repositories.protocol import AnnouncementNotFoundError


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _to_domain(row: AnnouncementORM) -> Announcement:
    return Announcement.model_validate(row)


class SqlAlchemyAnnouncementRepository:
    def __init__(self, *, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = session_factory

    async def create(self, data: AnnouncementCreate) -> Announcement:
        now = _utcnow()
        row = AnnouncementORM(
            message=data.message,
            author=data.author,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        async with session_scope(self._sessions) as session:
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return _to_domain(row)

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        include_deleted: bool = False,
    ) -> Page[Announcement]:
        async with session_scope(self._sessions) as session:
            base = select(AnnouncementORM)
            count_stmt = select(func.count()).select_from(AnnouncementORM)
            if not include_deleted:
                base = base.where(AnnouncementORM.deleted_at.is_(None))
                count_stmt = count_stmt.where(AnnouncementORM.deleted_at.is_(None))
            base = base.order_by(AnnouncementORM.id).limit(limit).offset(offset)
            rows = (await session.execute(base)).scalars().all()
            total = (await session.execute(count_stmt)).scalar_one()
            return Page(
                items=[_to_domain(r) for r in rows],
                total=int(total),
                limit=limit,
                offset=offset,
            )

    async def get(self, announcement_id: int, *, include_deleted: bool = False) -> Announcement:
        async with session_scope(self._sessions) as session:
            row = await session.get(AnnouncementORM, announcement_id)
            if row is None:
                raise AnnouncementNotFoundError(announcement_id)
            if row.deleted_at is not None and not include_deleted:
                raise AnnouncementNotFoundError(announcement_id)
            return _to_domain(row)

    async def update(self, announcement_id: int, patch: AnnouncementUpdate) -> Announcement:
        async with session_scope(self._sessions) as session:
            row = await session.get(AnnouncementORM, announcement_id)
            if row is None or row.deleted_at is not None:
                raise AnnouncementNotFoundError(announcement_id)
            data = patch.model_dump(exclude_unset=True)
            for field, value in data.items():
                setattr(row, field, value)
            row.updated_at = _utcnow()
            await session.flush()
            await session.refresh(row)
            return _to_domain(row)

    async def delete(self, announcement_id: int) -> None:
        async with session_scope(self._sessions) as session:
            row = await session.get(AnnouncementORM, announcement_id)
            if row is None or row.deleted_at is not None:
                raise AnnouncementNotFoundError(announcement_id)
            row.deleted_at = _utcnow()
            await session.flush()
