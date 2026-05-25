"""Entrypoint for `uvicorn announcements.main:app` and the `announcements` CLI script."""

from __future__ import annotations

import uvicorn

from announcements.app import create_app
from announcements.config import Settings

app = create_app()


def run() -> None:
    """`announcements` console script — launch uvicorn against the configured app."""
    settings = Settings()
    uvicorn.run(
        "announcements.main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
