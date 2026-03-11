"""Exception classes for the Octivas SDK."""

from __future__ import annotations

from typing import Any


class OctivasError(Exception):
    """Base exception for all Octivas SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: dict[str, Any] | None = None,
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


class ForbiddenError(OctivasError):
    """Raised when the subscription is inactive or the plan has no entitlement (HTTP 403).

    :attr:`upgrade_url` contains the URL where the user can upgrade their plan.
    """

    @property
    def upgrade_url(self) -> str | None:
        if self.body:
            detail = self.body.get("detail", self.body)
            if isinstance(detail, dict):
                val = detail.get("upgrade_url")
                if isinstance(val, str):
                    return val
        return None


class RateLimitError(OctivasError):
    """Raised when the API rate limit or credit limit is exceeded (HTTP 429).

    When the error is a credit limit violation, :attr:`credits_used` and
    :attr:`credits_limit` expose the relevant values from the response body.
    :attr:`upgrade_url` contains the URL where the user can upgrade their plan.
    """

    @property
    def credits_used(self) -> int | None:
        if self.body:
            detail = self.body.get("detail", self.body)
            if isinstance(detail, dict):
                val = detail.get("credits_used")
                if val is not None:
                    return int(val)
        return None

    @property
    def credits_limit(self) -> int | None:
        if self.body:
            detail = self.body.get("detail", self.body)
            if isinstance(detail, dict):
                val = detail.get("credits_limit")
                if val is not None:
                    return int(val)
        return None

    @property
    def upgrade_url(self) -> str | None:
        if self.body:
            detail = self.body.get("detail", self.body)
            if isinstance(detail, dict):
                val = detail.get("upgrade_url")
                if isinstance(val, str):
                    return val
        return None


class ServerError(OctivasError):
    """Raised when the API returns an internal server error (HTTP 5xx)."""
