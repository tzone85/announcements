"""API-key authentication dependency.

Reads `x-api-key` header and compares against `settings.api_key` in constant time.
"""

from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from announcements.api.deps import get_settings
from announcements.config import Settings

API_KEY_HEADER = "x-api-key"
_api_key_scheme = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


async def require_api_key(
    request: Request,  # noqa: ARG001
    provided: str | None = Depends(_api_key_scheme),
    settings: Settings = Depends(get_settings),
) -> None:
    if provided is None or not hmac.compare_digest(provided, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing api key",
            headers={"WWW-Authenticate": API_KEY_HEADER},
        )
