"""End-to-end API tests using TestClient with the in-memory repository.

Production wiring is identical apart from the swap to the Postgres repo,
which is covered by integration tests.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from announcements.app import create_app
from announcements.config import Settings
from announcements.repositories.in_memory import InMemoryAnnouncementRepository
from announcements.services.webhook_notifier import NullWebhookNotifier


@pytest.fixture
def settings() -> Settings:
    return Settings(api_key="test-key", database_url="memory://", webhook_subscribers=[])


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(
        settings=settings,
        repository=InMemoryAnnouncementRepository(),
        notifier=NullWebhookNotifier(),
    )
    with TestClient(app) as c:
        yield c


HEADERS = {"x-api-key": "test-key"}


class TestMeta:
    def test_root(self, client: TestClient) -> None:
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["service"] == "announcements"

    def test_health(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_swagger_present(self, client: TestClient) -> None:
        r = client.get("/swagger")
        assert r.status_code == 200


class TestAuth:
    def test_post_without_key_rejected(self, client: TestClient) -> None:
        r = client.post("/api/v1/announcements", json={"message": "hi", "author": "a"})
        assert r.status_code == 401

    def test_post_with_wrong_key_rejected(self, client: TestClient) -> None:
        r = client.post(
            "/api/v1/announcements",
            json={"message": "hi", "author": "a"},
            headers={"x-api-key": "nope"},
        )
        assert r.status_code == 401

    def test_get_does_not_require_key(self, client: TestClient) -> None:
        r = client.get("/api/v1/announcements")
        assert r.status_code == 200


class TestCRUD:
    def test_create_returns_201_with_body(self, client: TestClient) -> None:
        r = client.post(
            "/api/v1/announcements",
            json={"message": "hello team", "author": "alice"},
            headers=HEADERS,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["id"] == 1
        assert body["message"] == "hello team"
        assert body["author"] == "alice"
        assert body["created_at"] is not None
        assert body["is_deleted"] is False

    def test_create_rejects_extra_fields(self, client: TestClient) -> None:
        r = client.post(
            "/api/v1/announcements",
            json={"message": "m", "author": "a", "id": 99},
            headers=HEADERS,
        )
        assert r.status_code == 422

    def test_create_rejects_empty_message(self, client: TestClient) -> None:
        r = client.post(
            "/api/v1/announcements",
            json={"message": "", "author": "a"},
            headers=HEADERS,
        )
        assert r.status_code == 422

    def test_list_pagination(self, client: TestClient) -> None:
        for i in range(7):
            client.post(
                "/api/v1/announcements",
                json={"message": f"m{i}", "author": "x"},
                headers=HEADERS,
            )
        r = client.get("/api/v1/announcements?limit=3&offset=2")
        body = r.json()
        assert len(body["items"]) == 3
        assert body["total"] == 7
        assert body["has_more"] is True

    def test_get_existing(self, client: TestClient) -> None:
        r = client.post(
            "/api/v1/announcements",
            json={"message": "m", "author": "x"},
            headers=HEADERS,
        )
        created_id = r.json()["id"]
        got = client.get(f"/api/v1/announcements/{created_id}")
        assert got.status_code == 200
        assert got.json()["id"] == created_id

    def test_get_missing_returns_404(self, client: TestClient) -> None:
        r = client.get("/api/v1/announcements/9999")
        assert r.status_code == 404

    def test_patch_updates_partial(self, client: TestClient) -> None:
        r = client.post(
            "/api/v1/announcements",
            json={"message": "m", "author": "alice"},
            headers=HEADERS,
        )
        created_id = r.json()["id"]
        patched = client.patch(
            f"/api/v1/announcements/{created_id}",
            json={"message": "m2"},
            headers=HEADERS,
        )
        assert patched.status_code == 200
        body = patched.json()
        assert body["message"] == "m2"
        assert body["author"] == "alice"

    def test_delete_soft_removes(self, client: TestClient) -> None:
        r = client.post(
            "/api/v1/announcements",
            json={"message": "m", "author": "x"},
            headers=HEADERS,
        )
        created_id = r.json()["id"]
        d = client.delete(f"/api/v1/announcements/{created_id}", headers=HEADERS)
        assert d.status_code == 204
        assert client.get(f"/api/v1/announcements/{created_id}").status_code == 404
        with_deleted = client.get("/api/v1/announcements?include_deleted=true")
        assert any(i["id"] == created_id for i in with_deleted.json()["items"])

    def test_delete_missing_returns_404(self, client: TestClient) -> None:
        r = client.delete("/api/v1/announcements/9999", headers=HEADERS)
        assert r.status_code == 404
