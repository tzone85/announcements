"""Unit tests for domain models — pure data, no I/O."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from announcements.domain.models import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
    Page,
)


class TestAnnouncementCreate:
    def test_message_required(self) -> None:
        with pytest.raises(ValidationError):
            AnnouncementCreate(author="alice")  # type: ignore[call-arg]

    def test_author_required(self) -> None:
        with pytest.raises(ValidationError):
            AnnouncementCreate(message="hi")  # type: ignore[call-arg]

    def test_message_min_length(self) -> None:
        with pytest.raises(ValidationError):
            AnnouncementCreate(message="", author="alice")

    def test_message_max_length(self) -> None:
        with pytest.raises(ValidationError):
            AnnouncementCreate(message="x" * 5001, author="alice")

    def test_author_max_length(self) -> None:
        with pytest.raises(ValidationError):
            AnnouncementCreate(message="hi", author="a" * 256)

    def test_message_stripped(self) -> None:
        a = AnnouncementCreate(message="  hello  ", author="alice")
        assert a.message == "hello"

    def test_author_stripped_and_lowercased_email_kept_as_is(self) -> None:
        a = AnnouncementCreate(message="hi", author=" Alice ")
        assert a.author == "Alice"


class TestAnnouncementUpdate:
    def test_message_optional(self) -> None:
        AnnouncementUpdate()  # no fields required

    def test_message_validation_applies_when_present(self) -> None:
        with pytest.raises(ValidationError):
            AnnouncementUpdate(message="")


class TestAnnouncement:
    def test_full_construction(self) -> None:
        now = datetime.now(UTC)
        a = Announcement(
            id=1,
            message="hello",
            author="alice",
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        assert a.id == 1
        assert a.is_deleted is False

    def test_is_deleted_when_deleted_at_set(self) -> None:
        now = datetime.now(UTC)
        a = Announcement(
            id=1, message="m", author="a", created_at=now, updated_at=now, deleted_at=now
        )
        assert a.is_deleted is True


class TestPage:
    def test_page_records_total_and_items(self) -> None:
        p: Page[int] = Page(items=[1, 2, 3], total=42, limit=10, offset=0)
        assert p.total == 42
        assert p.items == [1, 2, 3]
        assert p.has_more is True

    def test_no_more_when_offset_plus_items_ge_total(self) -> None:
        p: Page[int] = Page(items=[1, 2], total=2, limit=10, offset=0)
        assert p.has_more is False

    def test_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Page(items=[], total=0, limit=0, offset=0)
        with pytest.raises(ValidationError):
            Page(items=[], total=0, limit=501, offset=0)
