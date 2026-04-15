"""Synchronous and asynchronous HTTP clients for the Octivas API."""

from __future__ import annotations

import contextlib
import time
from typing import Any

import httpx

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
    ContentFormat,
    JobListResponse,
    JobStatusResponse,
    JobSubmitResponse,
    Location,
    MapResponse,
    ScrapeResponse,
    SearchResponse,
)

_DEFAULT_BASE_URL = "https://api.octivas.com"
_DEFAULT_TIMEOUT = 60.0


def _build_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "octivas-python/0.1.3",
    }


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    body: dict[str, Any] = {}
    with contextlib.suppress(Exception):
        body = response.json()
    message = body.get("error", response.text or f"HTTP {response.status_code}")
    sc = response.status_code
    if sc == 401:
        raise AuthenticationError(message, status_code=sc, body=body)
    if sc == 403:
        raise ForbiddenError(message, status_code=sc, body=body)
    if sc in (400, 422):
        raise BadRequestError(message, status_code=sc, body=body)
    if sc == 404:
        raise NotFoundError(message, status_code=sc, body=body)
    if sc == 429:
        raise RateLimitError(message, status_code=sc, body=body)
    if sc >= 500:
        raise ServerError(message, status_code=sc, body=body)
    raise OctivasError(message, status_code=sc, body=body)


def _scrape_payload(
    url: str,
    *,
    formats: list[ContentFormat] | None = None,
    schema: dict[str, Any] | None = None,
    prompt: str | None = None,
    max_age: int | None = None,
    store_in_cache: bool | None = None,
    location: Location | None = None,
    only_main_content: bool | None = None,
    timeout: int | None = None,
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

    def __enter__(self) -> Octivas:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── Scrape ───────────────────────────────────────────────────────────

    def scrape(
        self,
        url: str,
        *,
        formats: list[ContentFormat] | None = None,
        schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        max_age: int | None = None,
        store_in_cache: bool | None = None,
        location: Location | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
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
        urls: list[str],
        *,
        formats: list[ContentFormat] | None = None,
        schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        max_age: int | None = None,
        store_in_cache: bool | None = None,
        location: Location | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
    ) -> JobSubmitResponse:
        """Submit a batch scrape job. Poll with :meth:`get_job` or :meth:`wait_for_batch_scrape`."""
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
        return JobSubmitResponse.model_validate(resp.json())

    def wait_for_batch_scrape(
        self,
        job_id: str,
        *,
        poll_interval: float = 2.0,
        timeout: float | None = None,
    ) -> JobStatusResponse:
        """Poll a batch scrape job until completed or failed.

        Args:
            job_id: Job ID returned by :meth:`batch_scrape`.
            poll_interval: Seconds between status checks.
            timeout: Maximum seconds to wait. *None* means wait indefinitely.
        """
        deadline = time.monotonic() + timeout if timeout is not None else None
        while True:
            status = self.get_job(job_id, include_results=True)
            if status.status in ("completed", "failed"):
                return status
            if deadline is not None and time.monotonic() >= deadline:
                return status
            time.sleep(poll_interval)

    # ── Crawl ────────────────────────────────────────────────────────────

    def crawl(
        self,
        url: str,
        *,
        limit: int = 10,
        formats: list[ContentFormat] | None = None,
        schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        exclude_paths: list[str] | None = None,
        include_paths: list[str] | None = None,
        max_depth: int | None = None,
        allow_external_links: bool | None = None,
        allow_subdomains: bool | None = None,
        ignore_sitemap: bool | None = None,
        ignore_query_parameters: bool | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
        wait_for: int | None = None,
    ) -> JobSubmitResponse:
        """Submit a crawl job. Returns immediately with a job ID.

        Poll with :meth:`get_job` or use :meth:`crawl_and_wait` for convenience.
        """
        payload: dict[str, Any] = {"url": url, "limit": limit}
        if formats is not None:
            payload["formats"] = formats
        if schema is not None:
            payload["schema"] = schema
        if prompt is not None:
            payload["prompt"] = prompt
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
        return JobSubmitResponse.model_validate(resp.json())

    def wait_for_crawl(
        self,
        job_id: str,
        *,
        poll_interval: float = 2.0,
        timeout: float | None = None,
    ) -> JobStatusResponse:
        """Poll a crawl job until completed or failed.

        Args:
            job_id: Job ID returned by :meth:`crawl`.
            poll_interval: Seconds between status checks.
            timeout: Maximum seconds to wait. *None* means wait indefinitely.
        """
        deadline = time.monotonic() + timeout if timeout is not None else None
        while True:
            status = self.get_job(job_id, include_results=True)
            if status.status in ("completed", "failed"):
                return status
            if deadline is not None and time.monotonic() >= deadline:
                return status
            time.sleep(poll_interval)

    def crawl_and_wait(
        self,
        url: str,
        *,
        limit: int = 10,
        formats: list[ContentFormat] | None = None,
        schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        exclude_paths: list[str] | None = None,
        include_paths: list[str] | None = None,
        max_depth: int | None = None,
        allow_external_links: bool | None = None,
        allow_subdomains: bool | None = None,
        ignore_sitemap: bool | None = None,
        ignore_query_parameters: bool | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
        wait_for: int | None = None,
        poll_interval: float = 2.0,
        poll_timeout: float | None = None,
    ) -> JobStatusResponse:
        """Submit a crawl job and block until it finishes."""
        job = self.crawl(
            url,
            limit=limit,
            formats=formats,
            schema=schema,
            prompt=prompt,
            exclude_paths=exclude_paths,
            include_paths=include_paths,
            max_depth=max_depth,
            allow_external_links=allow_external_links,
            allow_subdomains=allow_subdomains,
            ignore_sitemap=ignore_sitemap,
            ignore_query_parameters=ignore_query_parameters,
            only_main_content=only_main_content,
            timeout=timeout,
            wait_for=wait_for,
        )
        return self.wait_for_crawl(
            job.job_id, poll_interval=poll_interval, timeout=poll_timeout
        )

    # ── Jobs ─────────────────────────────────────────────────────────────

    def list_jobs(
        self,
        *,
        type: str | None = None,
        status: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> JobListResponse:
        """List jobs with optional filters."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if type is not None:
            params["type"] = type
        if status is not None:
            params["status"] = status
        resp = self._client.get("/api/v1/jobs", params=params)
        _raise_for_status(resp)
        return JobListResponse.model_validate(resp.json())

    def get_job(
        self,
        job_id: str,
        *,
        include_results: bool = False,
    ) -> JobStatusResponse:
        """Get the status of a job, optionally including results."""
        params: dict[str, Any] = {}
        if include_results:
            params["include_results"] = "true"
        resp = self._client.get(f"/api/v1/jobs/{job_id}", params=params)
        _raise_for_status(resp)
        return JobStatusResponse.model_validate(resp.json())

    # ── Search ───────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        formats: list[ContentFormat] | None = None,
        location: str | None = None,
        country: str | None = None,
        tbs: str | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
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

    # ── Map ──────────────────────────────────────────────────────────────

    def map(
        self,
        url: str,
        *,
        search: str | None = None,
        include_subdomains: bool | None = None,
        ignore_query_parameters: bool | None = None,
        limit: int = 5000,
        sitemap: str | None = None,
        timeout: int | None = None,
        location: Location | None = None,
    ) -> MapResponse:
        """Discover URLs on a website without scraping content."""
        payload: dict[str, Any] = {"url": url, "limit": limit}
        if search is not None:
            payload["search"] = search
        if include_subdomains is not None:
            payload["include_subdomains"] = include_subdomains
        if ignore_query_parameters is not None:
            payload["ignore_query_parameters"] = ignore_query_parameters
        if sitemap is not None:
            payload["sitemap"] = sitemap
        if timeout is not None:
            payload["timeout"] = timeout
        if location is not None:
            payload["location"] = location.model_dump()
        resp = self._client.post("/api/v1/map", json=payload)
        _raise_for_status(resp)
        return MapResponse.model_validate(resp.json())


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

    async def __aenter__(self) -> AsyncOctivas:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ── Scrape ───────────────────────────────────────────────────────────

    async def scrape(
        self,
        url: str,
        *,
        formats: list[ContentFormat] | None = None,
        schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        max_age: int | None = None,
        store_in_cache: bool | None = None,
        location: Location | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
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
        urls: list[str],
        *,
        formats: list[ContentFormat] | None = None,
        schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        max_age: int | None = None,
        store_in_cache: bool | None = None,
        location: Location | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
    ) -> JobSubmitResponse:
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
        return JobSubmitResponse.model_validate(resp.json())

    async def wait_for_batch_scrape(
        self,
        job_id: str,
        *,
        poll_interval: float = 2.0,
        timeout: float | None = None,
    ) -> JobStatusResponse:
        """Poll a batch scrape job until completed or failed."""
        import asyncio

        deadline = time.monotonic() + timeout if timeout is not None else None
        while True:
            status = await self.get_job(job_id, include_results=True)
            if status.status in ("completed", "failed"):
                return status
            if deadline is not None and time.monotonic() >= deadline:
                return status
            await asyncio.sleep(poll_interval)

    # ── Crawl ────────────────────────────────────────────────────────────

    async def crawl(
        self,
        url: str,
        *,
        limit: int = 10,
        formats: list[ContentFormat] | None = None,
        schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        exclude_paths: list[str] | None = None,
        include_paths: list[str] | None = None,
        max_depth: int | None = None,
        allow_external_links: bool | None = None,
        allow_subdomains: bool | None = None,
        ignore_sitemap: bool | None = None,
        ignore_query_parameters: bool | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
        wait_for: int | None = None,
    ) -> JobSubmitResponse:
        """Submit a crawl job. Returns immediately with a job ID."""
        payload: dict[str, Any] = {"url": url, "limit": limit}
        if formats is not None:
            payload["formats"] = formats
        if schema is not None:
            payload["schema"] = schema
        if prompt is not None:
            payload["prompt"] = prompt
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
        return JobSubmitResponse.model_validate(resp.json())

    async def wait_for_crawl(
        self,
        job_id: str,
        *,
        poll_interval: float = 2.0,
        timeout: float | None = None,
    ) -> JobStatusResponse:
        """Poll a crawl job until completed or failed."""
        import asyncio

        deadline = time.monotonic() + timeout if timeout is not None else None
        while True:
            status = await self.get_job(job_id, include_results=True)
            if status.status in ("completed", "failed"):
                return status
            if deadline is not None and time.monotonic() >= deadline:
                return status
            await asyncio.sleep(poll_interval)

    async def crawl_and_wait(
        self,
        url: str,
        *,
        limit: int = 10,
        formats: list[ContentFormat] | None = None,
        schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        exclude_paths: list[str] | None = None,
        include_paths: list[str] | None = None,
        max_depth: int | None = None,
        allow_external_links: bool | None = None,
        allow_subdomains: bool | None = None,
        ignore_sitemap: bool | None = None,
        ignore_query_parameters: bool | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
        wait_for: int | None = None,
        poll_interval: float = 2.0,
        poll_timeout: float | None = None,
    ) -> JobStatusResponse:
        """Submit a crawl job and wait until it finishes."""
        job = await self.crawl(
            url,
            limit=limit,
            formats=formats,
            schema=schema,
            prompt=prompt,
            exclude_paths=exclude_paths,
            include_paths=include_paths,
            max_depth=max_depth,
            allow_external_links=allow_external_links,
            allow_subdomains=allow_subdomains,
            ignore_sitemap=ignore_sitemap,
            ignore_query_parameters=ignore_query_parameters,
            only_main_content=only_main_content,
            timeout=timeout,
            wait_for=wait_for,
        )
        return await self.wait_for_crawl(
            job.job_id, poll_interval=poll_interval, timeout=poll_timeout
        )

    # ── Jobs ─────────────────────────────────────────────────────────────

    async def list_jobs(
        self,
        *,
        type: str | None = None,
        status: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> JobListResponse:
        """List jobs with optional filters."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if type is not None:
            params["type"] = type
        if status is not None:
            params["status"] = status
        resp = await self._client.get("/api/v1/jobs", params=params)
        _raise_for_status(resp)
        return JobListResponse.model_validate(resp.json())

    async def get_job(
        self,
        job_id: str,
        *,
        include_results: bool = False,
    ) -> JobStatusResponse:
        """Get the status of a job, optionally including results."""
        params: dict[str, Any] = {}
        if include_results:
            params["include_results"] = "true"
        resp = await self._client.get(f"/api/v1/jobs/{job_id}", params=params)
        _raise_for_status(resp)
        return JobStatusResponse.model_validate(resp.json())

    # ── Search ───────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        *,
        limit: int = 5,
        formats: list[ContentFormat] | None = None,
        location: str | None = None,
        country: str | None = None,
        tbs: str | None = None,
        only_main_content: bool | None = None,
        timeout: int | None = None,
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

    # ── Map ──────────────────────────────────────────────────────────────

    async def map(
        self,
        url: str,
        *,
        search: str | None = None,
        include_subdomains: bool | None = None,
        ignore_query_parameters: bool | None = None,
        limit: int = 5000,
        sitemap: str | None = None,
        timeout: int | None = None,
        location: Location | None = None,
    ) -> MapResponse:
        """Discover URLs on a website without scraping content."""
        payload: dict[str, Any] = {"url": url, "limit": limit}
        if search is not None:
            payload["search"] = search
        if include_subdomains is not None:
            payload["include_subdomains"] = include_subdomains
        if ignore_query_parameters is not None:
            payload["ignore_query_parameters"] = ignore_query_parameters
        if sitemap is not None:
            payload["sitemap"] = sitemap
        if timeout is not None:
            payload["timeout"] = timeout
        if location is not None:
            payload["location"] = location.model_dump()
        resp = await self._client.post("/api/v1/map", json=payload)
        _raise_for_status(resp)
        return MapResponse.model_validate(resp.json())
