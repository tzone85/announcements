# Employee Announcements Center

A small, production-style REST API for posting company-wide announcements.

[![CI](https://github.com/tzone85/announcements/actions/workflows/ci.yml/badge.svg)](https://github.com/tzone85/announcements/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

Built on FastAPI + SQLAlchemy + PostgreSQL with a layered architecture:
domain, repository, service, and API layers — each behind an explicit interface
so the storage backend and webhook delivery strategy can be swapped without
touching business logic.

## Highlights

- **API-key auth** on every mutating request (`x-api-key` header).
- **Pagination + soft-delete + audit fields** built into the data model.
- **Webhook fan-out** to any number of subscribers; partial failures are tolerated.
- **PostgreSQL** persistence via SQLAlchemy 2.0 (async) with Alembic migrations.
- **93%+ test coverage** across unit, integration (Postgres + SQLite), and end-to-end suites.
- **Multi-stage Docker build** + `docker-compose` topology (nginx → api → postgres) for one-command boot.

## Architecture

### Component view

![Component diagram](docs/architecture/component.svg)

The service depends on two abstract Protocols — `AnnouncementRepository` and
`WebhookNotifier`. Production wires `SqlAlchemyAnnouncementRepository` +
`HttpWebhookNotifier`. Tests substitute the in-memory repo and either
`NullWebhookNotifier` or a `FakeNotifier`.

### Create-flow sequence

![Sequence diagram — create](docs/architecture/sequence_create.svg)

Note: a webhook delivery failure is logged but does **not** roll back the data
change. This is intentional at-most-once-delivery semantics — durability of the
business record is the priority.

### Deployment topology

![Deployment diagram](docs/architecture/deployment.svg)

### Schema

![ERD](docs/architecture/erd.svg)

Diagrams are PlantUML sources under `docs/architecture/*.puml`; rendered SVGs
are checked in. Regenerate with `./scripts/render_diagrams.sh` (requires
`plantuml` on `PATH`).

## Quick start

### Option 1 — one-command stack via docker-compose

```bash
docker compose up --build
# api:    http://localhost:8000  (direct)
# nginx:  http://localhost:80    (reverse proxy)
# swagger: http://localhost:8000/swagger
```

Override the API key (default `dev-key-change-me`) and webhook subscribers:

```bash
ANNOUNCEMENTS_API_KEY=use-a-real-secret \
ANNOUNCEMENTS_WEBHOOK_SUBSCRIBERS='["https://hooks.example.com/notify"]' \
docker compose up --build
```

### Option 2 — local Python without Docker (Postgres still required)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt -e .

export ANNOUNCEMENTS_DATABASE_URL="postgresql+psycopg://announcements:announcements@localhost:5432/announcements"
export ANNOUNCEMENTS_API_KEY="dev-key-change-me"

alembic upgrade head
uvicorn announcements.main:app --reload
```

### Option 3 — ephemeral SQLite for trying it out

```bash
export ANNOUNCEMENTS_DATABASE_URL="sqlite:////tmp/announcements.db"
export ANNOUNCEMENTS_API_KEY="dev-key"
alembic upgrade head
uvicorn announcements.main:app
```

## API

All endpoints live under `/api/v1/announcements`. OpenAPI/Swagger at `/swagger`.

| Method | Path                              | Auth      | Body                          | Returns                       |
|--------|-----------------------------------|-----------|-------------------------------|-------------------------------|
| GET    | `/api/v1/announcements`           | none      | —                             | `Page[Announcement]`          |
| GET    | `/api/v1/announcements/{id}`      | none      | —                             | `Announcement`                |
| POST   | `/api/v1/announcements`           | x-api-key | `AnnouncementCreate`          | `201 Announcement`            |
| PATCH  | `/api/v1/announcements/{id}`      | x-api-key | `AnnouncementUpdate` (partial) | `Announcement`               |
| DELETE | `/api/v1/announcements/{id}`      | x-api-key | —                             | `204 No Content` (soft-delete) |

### Pagination

```
GET /api/v1/announcements?limit=20&offset=40&include_deleted=false
```

| Param            | Default | Range    | Notes                                  |
|------------------|---------|----------|----------------------------------------|
| `limit`          | 50      | 1..500   |                                        |
| `offset`         | 0       | ≥ 0      |                                        |
| `include_deleted`| false   | bool     | When true, soft-deleted rows are shown |

Response envelope:

```json
{
  "items": [ /* ... */ ],
  "total": 137,
  "limit": 20,
  "offset": 40,
  "has_more": true
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/v1/announcements \
  -H "x-api-key: dev-key-change-me" \
  -H "content-type: application/json" \
  -d '{"message":"Office closes Friday at 14:00","author":"alice@company.com"}'
```

## Configuration

All settings live under the `ANNOUNCEMENTS_` env prefix and read from `.env` if
present.

| Variable                              | Default                                                          | Purpose                                              |
|---------------------------------------|------------------------------------------------------------------|------------------------------------------------------|
| `ANNOUNCEMENTS_API_KEY`               | `dev-key-change-me`                                              | Required in `x-api-key` header on POST/PATCH/DELETE  |
| `ANNOUNCEMENTS_DATABASE_URL`          | `postgresql+psycopg://announcements:announcements@localhost:5432/announcements` | SQLAlchemy URL. Use `memory://` for the in-memory backend (tests only). |
| `ANNOUNCEMENTS_WEBHOOK_SUBSCRIBERS`   | `[]`                                                             | JSON list of URLs to POST events to                  |
| `ANNOUNCEMENTS_LOG_LEVEL`             | `INFO`                                                           | DEBUG / INFO / WARNING / ERROR                       |

### Webhook payload

Every announcement mutation emits an event POST to every configured subscriber:

```json
{
  "kind": "announcement.created",
  "announcement": {
    "id": 42,
    "message": "...",
    "author": "...",
    "created_at": "...",
    "updated_at": "...",
    "deleted_at": null,
    "is_deleted": false
  }
}
```

`kind` is one of `announcement.created`, `announcement.updated`, `announcement.deleted`.

## Testing

```bash
pytest tests/unit tests/e2e          # fast — no I/O
pytest tests/integration             # SQLite default; export ANNOUNCEMENTS_DATABASE_URL to use Postgres
pytest                               # everything + 85% coverage gate
```

| Suite         | What it covers                                                                                |
|---------------|-----------------------------------------------------------------------------------------------|
| `tests/unit/` | Domain models, in-memory repo, service orchestration, webhook notifier (via `respx`)          |
| `tests/integration/` | SQLAlchemy repo against a real SQL database, Alembic up/down migrations                |
| `tests/e2e/`  | Full HTTP stack through `TestClient` with in-memory repo + null notifier                      |

## Project layout

```
src/announcements/
├── domain/        # Pure pydantic models (no I/O)
├── repositories/  # Protocol + InMemory + SqlAlchemy implementations
├── services/      # Business logic + webhook notifier
├── db/            # SQLAlchemy ORM + async session factory
├── api/           # FastAPI routers, deps, auth
├── app.py         # create_app factory (composition root)
├── main.py        # uvicorn entrypoint
└── config.py      # Settings via pydantic-settings
alembic/           # Database migrations
docs/architecture/ # PlantUML sources + rendered SVGs
nginx/             # Reverse-proxy Docker image + config
```

## Local quality gate

```bash
ruff check src tests
ruff format --check src tests
mypy src
pytest
```

These are exactly the checks CI runs (lint, type-check, unit/e2e, integration
against Postgres 15 + 16, Docker build).

## License

MIT — see [LICENSE](LICENSE).
