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
    json_data: Any | None = Field(default=None, alias="json")
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
    json_data: Any | None = Field(default=None, alias="json")
    images: list[str] | None = None
    summary: str | None = None
    metadata: PageMetadata | None = None


class MapLink(BaseModel):
    """Single link discovered by a map operation."""

    url: str
    title: str | None = None
    description: str | None = None


class MapResponse(BaseModel):
    """Response from URL mapping / site discovery."""

    success: bool
    url: str
    links_count: int
    links: list[MapLink]


# ── Job models ───────────────────────────────────────────────────────────────


class JobProgress(BaseModel):
    """Progress counters for a running job."""

    completed: int
    total: int


class JobError(BaseModel):
    """Error details attached to a failed job."""

    message: str
    type: str


class JobSubmitResponse(BaseModel):
    """Response when submitting an async job (crawl or batch scrape)."""

    success: bool
    job_id: str
    status: str
    total: int


class JobStatusResponse(BaseModel):
    """Full status of a single job, optionally including results."""

    success: bool
    job_id: str
    type: str
    status: str
    provider: str
    progress: JobProgress
    credits_used: int = 0
    error: JobError | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    results: Any | None = None


class JobListItem(BaseModel):
    """Summary of a job in a listing (no results)."""

    job_id: str
    type: str
    status: str
    provider: str
    progress: JobProgress = JobProgress(completed=0, total=0)
    credits_used: int = 0
    error: JobError | None = None
    organization_id: str | None = None
    created_at: str | None = None
    finished_at: str | None = None


class JobListResponse(BaseModel):
    """Paginated list of jobs."""

    success: bool
    jobs: list[JobListItem]
    total: int
    page: int
    limit: int


class SearchResponse(BaseModel):
    """Response from a web search."""

    success: bool
    query: str
    results_count: int
    credits_used: int = 0
    results: list[SearchResultItem]
