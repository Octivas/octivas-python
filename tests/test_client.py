"""Tests for the Octivas sync and async clients."""

from __future__ import annotations

import json

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

    def test_crawl_forwards_prompt_and_schema_for_json(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/crawl",
            json={
                "success": True,
                "job_id": "crawl-001",
                "status": "pending",
                "total": 2,
            },
        )
        with Octivas(api_key="oc-test01234567890123456789012", base_url=BASE_URL) as client:
            client.crawl(
                "https://docs.example.com",
                limit=2,
                formats=["markdown", "json"],
                prompt="List section headings",
                schema={"type": "object", "properties": {"headings": {"type": "array"}}},
            )
        req = httpx_mock.get_request()
        assert req is not None
        body = json.loads(req.content.decode())
        assert body["formats"] == ["markdown", "json"]
        assert body["prompt"] == "List section headings"
        assert body["schema"]["type"] == "object"

    def test_crawl_success(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/crawl",
            json={
                "success": True,
                "job_id": "crawl-002",
                "status": "pending",
                "total": 5,
            },
        )
        with Octivas(api_key="oc-test01234567890123456789012") as client:
            result = client.crawl("https://docs.example.com", limit=5)
        assert result.job_id == "crawl-002"
        assert result.status == "pending"
        assert result.total == 5

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
                "status": "pending",
                "total": 2,
            },
        )
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/jobs/abc123?include_results=true",
            json={
                "success": True,
                "job_id": "abc123",
                "type": "batch_scrape",
                "status": "completed",
                "provider": "default",
                "progress": {"completed": 2, "total": 2},
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
            assert job.total == 2
            status = client.get_job("abc123", include_results=True)
            assert status.status == "completed"
            assert len(status.results) == 2

    def test_map_success(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/map",
            json={
                "success": True,
                "url": "https://example.com",
                "links_count": 2,
                "links": [
                    {"url": "https://example.com/", "title": "Home"},
                    {"url": "https://example.com/about", "title": "About", "description": "About us"},
                ],
            },
        )
        with Octivas(api_key="oc-test01234567890123456789012") as client:
            result = client.map("https://example.com")
        assert result.links_count == 2
        assert result.links[0].url == "https://example.com/"
        assert result.links[1].description == "About us"

    def test_list_jobs(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/jobs?page=1&limit=20",
            json={
                "success": True,
                "jobs": [
                    {
                        "job_id": "job-1",
                        "type": "crawl",
                        "status": "completed",
                        "provider": "default",
                        "progress": {"completed": 5, "total": 5},
                        "credits_used": 5,
                        "created_at": "2026-04-15T10:00:00Z",
                        "finished_at": "2026-04-15T10:01:00Z",
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 20,
            },
        )
        with Octivas(api_key="oc-test01234567890123456789012") as client:
            result = client.list_jobs()
        assert result.total == 1
        assert result.jobs[0].job_id == "job-1"
        assert result.jobs[0].type == "crawl"

    def test_get_job(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/jobs/job-1",
            json={
                "success": True,
                "job_id": "job-1",
                "type": "crawl",
                "status": "completed",
                "provider": "default",
                "progress": {"completed": 5, "total": 5},
                "credits_used": 5,
                "created_at": "2026-04-15T10:00:00Z",
                "finished_at": "2026-04-15T10:01:00Z",
            },
        )
        with Octivas(api_key="oc-test01234567890123456789012") as client:
            result = client.get_job("job-1")
        assert result.job_id == "job-1"
        assert result.status == "completed"
        assert result.progress.completed == 5


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
