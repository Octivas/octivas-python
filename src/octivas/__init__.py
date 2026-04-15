"""Octivas Python SDK - Web scraping and extraction API client."""

from .client import AsyncOctivas, Octivas
from .exceptions import (
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    OctivasError,
    RateLimitError,
    ServerError,
)
from .models import (
    JobError,
    JobListItem,
    JobListResponse,
    JobProgress,
    JobStatusResponse,
    JobSubmitResponse,
    Location,
    MapLink,
    MapResponse,
    PageContent,
    PageMetadata,
    ScrapeResponse,
    SearchResponse,
    SearchResultItem,
)

__version__ = "0.1.3"

__all__ = [
    "Octivas",
    "AsyncOctivas",
    "JobError",
    "JobListItem",
    "JobListResponse",
    "JobProgress",
    "JobStatusResponse",
    "JobSubmitResponse",
    "Location",
    "MapLink",
    "MapResponse",
    "PageContent",
    "PageMetadata",
    "ScrapeResponse",
    "SearchResponse",
    "SearchResultItem",
    "OctivasError",
    "AuthenticationError",
    "BadRequestError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
]
