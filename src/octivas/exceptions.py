"""Exception classes for the Octivas SDK."""

from __future__ import annotations

from typing import Any, Optional


class OctivasError(Exception):
    """Base exception for all Octivas SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        body: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class AuthenticationError(OctivasError):
    """Raised when the API key is missing or invalid (HTTP 401)."""


class BadRequestError(OctivasError):
    """Raised when the request is malformed or has invalid parameters (HTTP 400/422)."""


class NotFoundError(OctivasError):
    """Raised when the requested resource does not exist (HTTP 404)."""


class RateLimitError(OctivasError):
    """Raised when the API rate limit is exceeded (HTTP 429)."""


class ServerError(OctivasError):
    """Raised when the API returns an internal server error (HTTP 5xx)."""
