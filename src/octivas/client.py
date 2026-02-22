"""Synchronous and asynchronous HTTP clients for the Octivas API."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx

from .exceptions import (
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OctivasError,
    RateLimitError,
    ServerError,
)
from .models import (
    BatchScrapeJob,
    BatchScrapeStatus,
    ContentFormat,
    CrawlResponse,
    Location,
    ScrapeResponse,
    SearchResponse,
)

_DEFAULT_BASE_URL = "https://api.octivas.com"
_DEFAULT_TIMEOUT = 60.0


def _build_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "octivas-python/0.1.0",
    }


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    body: dict[str, Any] = {}
    try:
        body = response.json()
    except Exception:
        pass
    message = body.get("error", response.text or f"HTTP {response.status_code}")
    kwargs = {"status_code": response.status_code, "body": body}
    if response.status_code == 401:
        raise AuthenticationError(message, **kwargs)
    if response.status_code in (400, 422):
        raise BadRequestError(message, **kwargs)
    if response.status_code == 404:
        raise NotFoundError(message, **kwargs)
    if response.status_code == 429:
        raise RateLimitError(message, **kwargs)
    if response.status_code >= 500:
        raise ServerError(message, **kwargs)
    raise OctivasError(message, **kwargs)


def _scrape_payload(
    url: str,
    *,
    formats: Optional[List[ContentFormat]] = None,
    schema: Optional[Dict[str, Any]] = None,
    prompt: Optional[str] = None,
    max_age: Optional[int] = None,
    store_in_cache: Optional[bool] = None,
    location: Optional[Location] = None,
    only_main_content: Optional[bool] = None,
    timeout: Optional[int] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"url": url}
    if formats is not None:
        payload["formats"] = formats
    if schema is not None:
        payload["schema"] = schema
    if prompt is not None:
        payload["prompt"] = prompt
    if max_age is not None:
        payload["max_age"] = max_age
    if store_in_cache is not None:
        payload["store_in_cache"] = store_in_cache
    if location is not None:
        payload["location"] = location.model_dump()
    if only_main_content is not None:
        payload["only_main_content"] = only_main_content
    if timeout is not None:
        payload["timeout"] = timeout
    return payload


# ── Synchronous client ───────────────────────────────────────────────────────


class Octivas:
    """Synchronous client for the Octivas API.

    Usage::

        from octivas import Octivas

        client = Octivas(api_key="oc-...")
        result = client.scrape("https://example.com")
        print(result.markdown)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=_build_headers(api_key),
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Octivas":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── Scrape ───────────────────────────────────────────────────────────

    def scrape(
        self,
        url: str,
        *,
        formats: Optional[List[ContentFormat]] = None,
        schema: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        max_age: Optional[int] = None,
        store_in_cache: Optional[bool] = None,
        location: Optional[Location] = None,
        only_main_content: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> ScrapeResponse:
        """Scrape a single page."""
        payload = _scrape_payload(
            url,
            formats=formats,
            schema=schema,
            prompt=prompt,
            max_age=max_age,
            store_in_cache=store_in_cache,
            location=location,
            only_main_content=only_main_content,
            timeout=timeout,
        )
        resp = self._client.post("/api/v1/scrape", json=payload)
        _raise_for_status(resp)
        return ScrapeResponse.model_validate(resp.json())

    # ── Batch scrape ─────────────────────────────────────────────────────

    def batch_scrape(
        self,
        urls: List[str],
        *,
        formats: Optional[List[ContentFormat]] = None,
        schema: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        max_age: Optional[int] = None,
        store_in_cache: Optional[bool] = None,
        location: Optional[Location] = None,
        only_main_content: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> BatchScrapeJob:
        """Submit a batch scrape job. Poll with :meth:`batch_scrape_status`."""
        payload: dict[str, Any] = {"urls": urls}
        if formats is not None:
            payload["formats"] = formats
        if schema is not None:
            payload["schema"] = schema
        if prompt is not None:
            payload["prompt"] = prompt
        if max_age is not None:
            payload["max_age"] = max_age
        if store_in_cache is not None:
            payload["store_in_cache"] = store_in_cache
        if location is not None:
            payload["location"] = location.model_dump()
        if only_main_content is not None:
            payload["only_main_content"] = only_main_content
        if timeout is not None:
            payload["timeout"] = timeout
        resp = self._client.post("/api/v1/batch/scrape", json=payload)
        _raise_for_status(resp)
        return BatchScrapeJob.model_validate(resp.json())

    def batch_scrape_status(self, job_id: str) -> BatchScrapeStatus:
        """Get the status and results of a batch scrape job."""
        resp = self._client.get(f"/api/v1/batch/scrape/{job_id}")
        _raise_for_status(resp)
        return BatchScrapeStatus.model_validate(resp.json())

    def batch_scrape_wait(
        self,
        job_id: str,
        *,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> BatchScrapeStatus:
        """Poll a batch job until completion or timeout."""
        deadline = time.monotonic() + max_wait
        while True:
            status = self.batch_scrape_status(job_id)
            if status.status in ("completed", "failed"):
                return status
            if time.monotonic() >= deadline:
                return status
            time.sleep(poll_interval)

    # ── Crawl ────────────────────────────────────────────────────────────

    def crawl(
        self,
        url: str,
        *,
        limit: int = 10,
        formats: Optional[List[ContentFormat]] = None,
        exclude_paths: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
        allow_external_links: Optional[bool] = None,
        allow_subdomains: Optional[bool] = None,
        ignore_sitemap: Optional[bool] = None,
        ignore_query_parameters: Optional[bool] = None,
        only_main_content: Optional[bool] = None,
        timeout: Optional[int] = None,
        wait_for: Optional[int] = None,
    ) -> CrawlResponse:
        """Crawl a website and extract content from discovered pages."""
        payload: dict[str, Any] = {"url": url, "limit": limit}
        if formats is not None:
            payload["formats"] = formats
        if exclude_paths is not None:
            payload["exclude_paths"] = exclude_paths
        if include_paths is not None:
            payload["include_paths"] = include_paths
        if max_depth is not None:
            payload["max_depth"] = max_depth
        if allow_external_links is not None:
            payload["allow_external_links"] = allow_external_links
        if allow_subdomains is not None:
            payload["allow_subdomains"] = allow_subdomains
        if ignore_sitemap is not None:
            payload["ignore_sitemap"] = ignore_sitemap
        if ignore_query_parameters is not None:
            payload["ignore_query_parameters"] = ignore_query_parameters
        if only_main_content is not None:
            payload["only_main_content"] = only_main_content
        if timeout is not None:
            payload["timeout"] = timeout
        if wait_for is not None:
            payload["wait_for"] = wait_for
        resp = self._client.post("/api/v1/crawl", json=payload)
        _raise_for_status(resp)
        return CrawlResponse.model_validate(resp.json())

    # ── Search ───────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        formats: Optional[List[ContentFormat]] = None,
        location: Optional[str] = None,
        country: Optional[str] = None,
        tbs: Optional[str] = None,
        only_main_content: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> SearchResponse:
        """Search the web and extract content from results."""
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if formats is not None:
            payload["formats"] = formats
        if location is not None:
            payload["location"] = location
        if country is not None:
            payload["country"] = country
        if tbs is not None:
            payload["tbs"] = tbs
        if only_main_content is not None:
            payload["only_main_content"] = only_main_content
        if timeout is not None:
            payload["timeout"] = timeout
        resp = self._client.post("/api/v1/search", json=payload)
        _raise_for_status(resp)
        return SearchResponse.model_validate(resp.json())


# ── Async client ─────────────────────────────────────────────────────────────


class AsyncOctivas:
    """Asynchronous client for the Octivas API.

    Usage::

        from octivas import AsyncOctivas

        async with AsyncOctivas(api_key="oc-...") as client:
            result = await client.scrape("https://example.com")
            print(result.markdown)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=_build_headers(api_key),
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncOctivas":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ── Scrape ───────────────────────────────────────────────────────────

    async def scrape(
        self,
        url: str,
        *,
        formats: Optional[List[ContentFormat]] = None,
        schema: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        max_age: Optional[int] = None,
        store_in_cache: Optional[bool] = None,
        location: Optional[Location] = None,
        only_main_content: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> ScrapeResponse:
        """Scrape a single page."""
        payload = _scrape_payload(
            url,
            formats=formats,
            schema=schema,
            prompt=prompt,
            max_age=max_age,
            store_in_cache=store_in_cache,
            location=location,
            only_main_content=only_main_content,
            timeout=timeout,
        )
        resp = await self._client.post("/api/v1/scrape", json=payload)
        _raise_for_status(resp)
        return ScrapeResponse.model_validate(resp.json())

    # ── Batch scrape ─────────────────────────────────────────────────────

    async def batch_scrape(
        self,
        urls: List[str],
        *,
        formats: Optional[List[ContentFormat]] = None,
        schema: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        max_age: Optional[int] = None,
        store_in_cache: Optional[bool] = None,
        location: Optional[Location] = None,
        only_main_content: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> BatchScrapeJob:
        """Submit a batch scrape job."""
        payload: dict[str, Any] = {"urls": urls}
        if formats is not None:
            payload["formats"] = formats
        if schema is not None:
            payload["schema"] = schema
        if prompt is not None:
            payload["prompt"] = prompt
        if max_age is not None:
            payload["max_age"] = max_age
        if store_in_cache is not None:
            payload["store_in_cache"] = store_in_cache
        if location is not None:
            payload["location"] = location.model_dump()
        if only_main_content is not None:
            payload["only_main_content"] = only_main_content
        if timeout is not None:
            payload["timeout"] = timeout
        resp = await self._client.post("/api/v1/batch/scrape", json=payload)
        _raise_for_status(resp)
        return BatchScrapeJob.model_validate(resp.json())

    async def batch_scrape_status(self, job_id: str) -> BatchScrapeStatus:
        """Get the status and results of a batch scrape job."""
        resp = await self._client.get(f"/api/v1/batch/scrape/{job_id}")
        _raise_for_status(resp)
        return BatchScrapeStatus.model_validate(resp.json())

    async def batch_scrape_wait(
        self,
        job_id: str,
        *,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> BatchScrapeStatus:
        """Poll a batch job until completion or timeout."""
        import asyncio

        deadline = time.monotonic() + max_wait
        while True:
            status = await self.batch_scrape_status(job_id)
            if status.status in ("completed", "failed"):
                return status
            if time.monotonic() >= deadline:
                return status
            await asyncio.sleep(poll_interval)

    # ── Crawl ────────────────────────────────────────────────────────────

    async def crawl(
        self,
        url: str,
        *,
        limit: int = 10,
        formats: Optional[List[ContentFormat]] = None,
        exclude_paths: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
        allow_external_links: Optional[bool] = None,
        allow_subdomains: Optional[bool] = None,
        ignore_sitemap: Optional[bool] = None,
        ignore_query_parameters: Optional[bool] = None,
        only_main_content: Optional[bool] = None,
        timeout: Optional[int] = None,
        wait_for: Optional[int] = None,
    ) -> CrawlResponse:
        """Crawl a website and extract content from discovered pages."""
        payload: dict[str, Any] = {"url": url, "limit": limit}
        if formats is not None:
            payload["formats"] = formats
        if exclude_paths is not None:
            payload["exclude_paths"] = exclude_paths
        if include_paths is not None:
            payload["include_paths"] = include_paths
        if max_depth is not None:
            payload["max_depth"] = max_depth
        if allow_external_links is not None:
            payload["allow_external_links"] = allow_external_links
        if allow_subdomains is not None:
            payload["allow_subdomains"] = allow_subdomains
        if ignore_sitemap is not None:
            payload["ignore_sitemap"] = ignore_sitemap
        if ignore_query_parameters is not None:
            payload["ignore_query_parameters"] = ignore_query_parameters
        if only_main_content is not None:
            payload["only_main_content"] = only_main_content
        if timeout is not None:
            payload["timeout"] = timeout
        if wait_for is not None:
            payload["wait_for"] = wait_for
        resp = await self._client.post("/api/v1/crawl", json=payload)
        _raise_for_status(resp)
        return CrawlResponse.model_validate(resp.json())

    # ── Search ───────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        *,
        limit: int = 5,
        formats: Optional[List[ContentFormat]] = None,
        location: Optional[str] = None,
        country: Optional[str] = None,
        tbs: Optional[str] = None,
        only_main_content: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> SearchResponse:
        """Search the web and extract content from results."""
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if formats is not None:
            payload["formats"] = formats
        if location is not None:
            payload["location"] = location
        if country is not None:
            payload["country"] = country
        if tbs is not None:
            payload["tbs"] = tbs
        if only_main_content is not None:
            payload["only_main_content"] = only_main_content
        if timeout is not None:
            payload["timeout"] = timeout
        resp = await self._client.post("/api/v1/search", json=payload)
        _raise_for_status(resp)
        return SearchResponse.model_validate(resp.json())
