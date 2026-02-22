"""Octivas Python SDK - Web scraping and extraction API client."""

from .client import Octivas, AsyncOctivas
from .models import (
    BatchScrapeJob,
    BatchScrapeStatus,
    CrawlResponse,
    Location,
    PageContent,
    PageMetadata,
    ScrapeResponse,
    SearchResponse,
    SearchResultItem,
)
from .exceptions import (
    OctivasError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

__version__ = "0.1.0"

__all__ = [
    "Octivas",
    "AsyncOctivas",
    "BatchScrapeJob",
    "BatchScrapeStatus",
    "CrawlResponse",
    "Location",
    "PageContent",
    "PageMetadata",
    "ScrapeResponse",
    "SearchResponse",
    "SearchResultItem",
    "OctivasError",
    "AuthenticationError",
    "BadRequestError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
]
