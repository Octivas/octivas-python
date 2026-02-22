"""Tests for the Octivas sync and async clients."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from octivas import (
    AsyncOctivas,
    AuthenticationError,
    BadRequestError,
    Octivas,
    ScrapeResponse,
)

BASE_URL = "https://api.octivas.com"


class TestSyncClient:
    def test_scrape_success(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/scrape",
            json={
                "success": True,
                "url": "https://example.com/",
                "markdown": "# Hello",
            },
        )
        with Octivas(api_key="oc-test01234567890123456789012") as client:
            result = client.scrape("https://example.com")
        assert isinstance(result, ScrapeResponse)
        assert result.markdown == "# Hello"

    def test_scrape_auth_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/scrape",
            status_code=401,
            json={"success": False, "error": "Invalid API key"},
        )
        with Octivas(api_key="oc-bad") as client:
            with pytest.raises(AuthenticationError, match="Invalid API key"):
                client.scrape("https://example.com")

    def test_scrape_bad_request(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/scrape",
            status_code=422,
            json={"success": False, "error": "Validation error"},
        )
        with Octivas(api_key="oc-test01234567890123456789012") as client:
            with pytest.raises(BadRequestError):
                client.scrape("not-a-url")

    def test_crawl_success(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/crawl",
            json={
                "success": True,
                "url": "https://docs.example.com",
                "pages_crawled": 2,
                "credits_used": 2,
                "pages": [
                    {"url": "https://docs.example.com/", "markdown": "# Docs"},
                    {"url": "https://docs.example.com/start", "markdown": "# Start"},
                ],
            },
        )
        with Octivas(api_key="oc-test01234567890123456789012") as client:
            result = client.crawl("https://docs.example.com", limit=5)
        assert result.pages_crawled == 2
        assert len(result.pages) == 2

    def test_search_success(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/search",
            json={
                "success": True,
                "query": "test",
                "results_count": 1,
                "credits_used": 1,
                "results": [
                    {"url": "https://example.com", "title": "Example", "markdown": "# Ex"}
                ],
            },
        )
        with Octivas(api_key="oc-test01234567890123456789012") as client:
            result = client.search("test")
        assert result.results_count == 1
        assert result.results[0].title == "Example"

    def test_batch_scrape_flow(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/batch/scrape",
            json={
                "success": True,
                "job_id": "abc123",
                "status": "processing",
                "total_urls": 2,
            },
        )
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/batch/scrape/abc123",
            json={
                "success": True,
                "job_id": "abc123",
                "status": "completed",
                "completed": 2,
                "total": 2,
                "credits_used": 2,
                "results": [
                    {"success": True, "url": "https://a.com", "markdown": "A"},
                    {"success": True, "url": "https://b.com", "markdown": "B"},
                ],
            },
        )
        with Octivas(api_key="oc-test01234567890123456789012") as client:
            job = client.batch_scrape(["https://a.com", "https://b.com"])
            assert job.job_id == "abc123"
            status = client.batch_scrape_status("abc123")
            assert status.status == "completed"
            assert len(status.results) == 2


@pytest.mark.anyio
class TestAsyncClient:
    async def test_scrape_success(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/scrape",
            json={
                "success": True,
                "url": "https://example.com/",
                "markdown": "# Hello",
            },
        )
        async with AsyncOctivas(api_key="oc-test01234567890123456789012") as client:
            result = await client.scrape("https://example.com")
        assert result.markdown == "# Hello"
