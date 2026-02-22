"""Data models for the Octivas SDK.

These mirror the API's response schemas so users get typed, validated objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ContentFormat = Literal[
    "markdown", "html", "rawHtml", "screenshot", "links", "json", "images", "summary"
]


class Location(BaseModel):
    """Geographic location settings."""

    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 code")
    languages: List[str] = Field(default=["en"])


class PageMetadata(BaseModel):
    """Metadata extracted from a scraped page."""

    title: Optional[str] = None
    description: Optional[str] = None
    url: str
    language: Optional[str] = None
    status_code: Optional[int] = None
    credits_used: Optional[int] = None
    favicon: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_url: Optional[str] = None
    og_site_name: Optional[str] = None
    keywords: Optional[str] = None
    author: Optional[str] = None
    published_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None


class PageContent(BaseModel):
    """Content extracted from a scraped page."""

    url: str
    markdown: Optional[str] = None
    html: Optional[str] = None
    raw_html: Optional[str] = None
    screenshot: Optional[str] = None
    links: Optional[List[str]] = None
    json_data: Optional[Dict[str, Any]] = Field(default=None, alias="json")
    images: Optional[List[str]] = None
    summary: Optional[str] = None
    metadata: Optional[PageMetadata] = None


class SearchResultItem(BaseModel):
    """A single search result."""

    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    raw_html: Optional[str] = None
    screenshot: Optional[str] = None
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    summary: Optional[str] = None


# ── Response models ──────────────────────────────────────────────────────────


class ScrapeResponse(BaseModel):
    """Response from scraping a single page."""

    success: bool
    url: str
    markdown: Optional[str] = None
    html: Optional[str] = None
    raw_html: Optional[str] = None
    screenshot: Optional[str] = None
    links: Optional[List[str]] = None
    json_data: Optional[Dict[str, Any]] = Field(default=None, alias="json")
    images: Optional[List[str]] = None
    summary: Optional[str] = None
    metadata: Optional[PageMetadata] = None


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
    results: List[ScrapeResponse] = []


class CrawlResponse(BaseModel):
    """Response from crawling a website."""

    success: bool
    url: str
    pages_crawled: int
    credits_used: int = 0
    pages: List[PageContent]


class SearchResponse(BaseModel):
    """Response from a web search."""

    success: bool
    query: str
    results_count: int
    credits_used: int = 0
    results: List[SearchResultItem]
