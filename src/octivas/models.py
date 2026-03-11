"""Data models for the Octivas SDK.

These mirror the API's response schemas so users get typed, validated objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ContentFormat = Literal[
    "markdown", "html", "rawHtml", "screenshot", "links", "json", "images", "summary"
]


class Location(BaseModel):
    """Geographic location settings."""

    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 code")
    languages: list[str] = Field(default=["en"])


class PageMetadata(BaseModel):
    """Metadata extracted from a scraped page."""

    title: str | None = None
    description: str | None = None
    url: str
    language: str | None = None
    status_code: int | None = None
    credits_used: int | None = None
    favicon: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    og_url: str | None = None
    og_site_name: str | None = None
    keywords: str | None = None
    author: str | None = None
    published_time: datetime | None = None
    modified_time: datetime | None = None


class PageContent(BaseModel):
    """Content extracted from a scraped page."""

    url: str
    markdown: str | None = None
    html: str | None = None
    raw_html: str | None = None
    screenshot: str | None = None
    links: list[str] | None = None
    json_data: dict[str, Any] | None = Field(default=None, alias="json")
    images: list[str] | None = None
    summary: str | None = None
    metadata: PageMetadata | None = None


class SearchResultItem(BaseModel):
    """A single search result."""

    url: str
    title: str | None = None
    description: str | None = None
    markdown: str | None = None
    html: str | None = None
    raw_html: str | None = None
    screenshot: str | None = None
    links: list[str] | None = None
    images: list[str] | None = None
    summary: str | None = None


# ── Response models ──────────────────────────────────────────────────────────


class ScrapeResponse(BaseModel):
    """Response from scraping a single page."""

    success: bool
    url: str
    markdown: str | None = None
    html: str | None = None
    raw_html: str | None = None
    screenshot: str | None = None
    links: list[str] | None = None
    json_data: dict[str, Any] | None = Field(default=None, alias="json")
    images: list[str] | None = None
    summary: str | None = None
    metadata: PageMetadata | None = None


class BatchScrapeJob(BaseModel):
    """Response when submitting a batch scrape job."""

    success: bool
    job_id: str
    status: str
    total_urls: int


class BatchScrapeStatus(BaseModel):
    """Response when polling a batch scrape job."""

    success: bool
    job_id: str
    status: str
    completed: int
    total: int
    credits_used: int = 0
    results: list[ScrapeResponse] = []


class CrawlResponse(BaseModel):
    """Response from crawling a website."""

    success: bool
    url: str
    pages_crawled: int
    credits_used: int = 0
    pages: list[PageContent]


class SearchResponse(BaseModel):
    """Response from a web search."""

    success: bool
    query: str
    results_count: int
    credits_used: int = 0
    results: list[SearchResultItem]
