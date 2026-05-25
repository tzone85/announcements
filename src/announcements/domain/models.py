"""Domain models — pure data, framework-agnostic.

All persistence and HTTP concerns live elsewhere. These models are the contract
shared between the repository layer, the service layer, and the API layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

MAX_MESSAGE_LEN = 5000
MAX_AUTHOR_LEN = 255
MAX_PAGE_LIMIT = 500


def _strip(value: str) -> str:
    return value.strip()


class AnnouncementCreate(BaseModel):
    """Payload to create a new announcement."""

    model_config = ConfigDict(str_strip_whitespace=False, extra="forbid")

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LEN)
    author: str = Field(min_length=1, max_length=MAX_AUTHOR_LEN)

    @field_validator("message", "author", mode="before")
    @classmethod
    def _strip_strings(cls, v: object) -> object:
        return _strip(v) if isinstance(v, str) else v


class AnnouncementUpdate(BaseModel):
    """Partial update — any field may be omitted."""

    model_config = ConfigDict(extra="forbid")

    message: str | None = Field(default=None, min_length=1, max_length=MAX_MESSAGE_LEN)
    author: str | None = Field(default=None, min_length=1, max_length=MAX_AUTHOR_LEN)

    @field_validator("message", "author", mode="before")
    @classmethod
    def _strip_strings(cls, v: object) -> object:
        return _strip(v) if isinstance(v, str) else v


class Announcement(BaseModel):
    """Persisted announcement, returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    author: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Pagination envelope used by every list endpoint."""

    items: list[T]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=MAX_PAGE_LIMIT)
    offset: int = Field(ge=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total
