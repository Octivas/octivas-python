# Octivas Python SDK

The official Python client for the [Octivas](https://octivas.com) web scraping and extraction API.

## Installation

```bash
pip install octivas
```

## Quick start

```python
from octivas import Octivas

client = Octivas(api_key="oc-...")

# Scrape a single page
result = client.scrape("https://docs.octivas.com")
print(result.markdown)

# Crawl a website
crawl = client.crawl("https://docs.octivas.com", limit=20)
for page in crawl.pages:
    print(page.url, page.metadata.title)

# Search the web
search = client.search("python web scraping", limit=5)
for item in search.results:
    print(item.title, item.url)
```

## Async usage

```python
from octivas import AsyncOctivas

async with AsyncOctivas(api_key="oc-...") as client:
    result = await client.scrape("https://docs.octivas.com")
    print(result.markdown)
```

## Batch scraping

```python
client = Octivas(api_key="oc-...")

job = client.batch_scrape(["https://docs.octivas.com", "https://octivas.com"])
status = client.batch_scrape_wait(job.job_id)

for result in status.results:
    print(result.url, len(result.markdown or ""))
```

## Error handling

```python
from octivas import Octivas, AuthenticationError, RateLimitError

client = Octivas(api_key="oc-...")

try:
    result = client.scrape("https://docs.octivas.com")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Too many requests - back off and retry")
```

## Configuration

```python
client = Octivas(
    api_key="oc-...",
    base_url="https://api.octivas.com",  # default
    timeout=60.0,                         # seconds
)
```
