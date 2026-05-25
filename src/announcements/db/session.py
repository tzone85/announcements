"""SQLAlchemy async engine + session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(database_url: str) -> AsyncEngine:
    """Translate sync URL forms to async equivalents.

    Postgres: ``postgresql+psycopg://`` is already async-capable in v3.
    SQLite:   ``sqlite:///path`` becomes ``sqlite+aiosqlite:///path``.
    """
    if database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return create_async_engine(database_url, future=True, pool_pre_ping=True)


def build_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    engine = build_engine(database_url)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
