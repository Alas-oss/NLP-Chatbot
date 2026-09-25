import httpx
import pytest

from crawler.config import CrawlConfig
from crawler.fetcher import Crawler, CrawlerDisabled

ROBOTS_ALLOW_ALL = "User-agent: *\nAllow: /\n"
ROBOTS_DISALLOW_ONE = "User-agent: *\nDisallow: /secret\n"

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.org/page-a</loc></url>
  <url><loc>https://example.org/secret</loc></url>
</urlset>"""


def make_client(robots_text=ROBOTS_ALLOW_ALL, pages=None):
    pages = pages or {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots_text)
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text=SITEMAP)
        body = pages.get(str(request.url))
        return httpx.Response(200, text=body) if body else httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


def base_config(**overrides) -> CrawlConfig:
    defaults = dict(
        enabled=True,
        user_agent="TestBot/1.0 (+mailto:test@example.com)",
        rate_limit_seconds=0.0,
        max_pages=10,
        allowlist=["example.org"],
        sitemaps=["https://example.org/sitemap.xml"],
        urls=[],
    )
    defaults.update(overrides)
    return CrawlConfig(**defaults)


# ---- the safety gate: this is the part that must never be bypassable ----

def test_disabled_by_default_blocks_discover():
    crawler = Crawler(base_config(enabled=False), client=make_client())
    with pytest.raises(CrawlerDisabled, match="enabled is False"):
        crawler.discover()


def test_disabled_by_default_blocks_plan():
    crawler = Crawler(base_config(enabled=False), client=make_client())
    with pytest.raises(CrawlerDisabled):
        crawler.plan()


def test_disabled_by_default_blocks_fetch_one():
    crawler = Crawler(base_config(enabled=False), client=make_client())
    with pytest.raises(CrawlerDisabled):
        crawler.fetch_one("https://example.org/page-a")


def test_empty_allowlist_blocks_even_when_enabled():
    crawler = Crawler(base_config(enabled=True, allowlist=[]), client=make_client())
    with pytest.raises(CrawlerDisabled, match="empty allowlist"):
        crawler.plan()


def test_enabled_and_allowlisted_actually_works():
    crawler = Crawler(base_config(), client=make_client())
    report = crawler.plan()
    assert "https://example.org/page-a" in report.would_fetch


# ---- allowlist + robots enforcement inside plan()/fetch_one() ----

def test_plan_skips_urls_outside_the_allowlist():
    crawler = Crawler(base_config(), client=make_client())
    report = crawler.plan(urls=["https://not-allowed.example.com/page"])
    assert report.would_fetch == []
    assert report.skipped["https://not-allowed.example.com/page"] == "not_allowlisted"


def test_plan_skips_robots_disallowed_urls():
    crawler = Crawler(base_config(), client=make_client(robots_text=ROBOTS_DISALLOW_ONE))
    report = crawler.plan(urls=["https://example.org/page-a", "https://example.org/secret"])
    assert report.would_fetch == ["https://example.org/page-a"]
    assert report.skipped["https://example.org/secret"] == "robots_disallowed"


def test_plan_never_fetches_page_content():
    fetched_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        fetched_paths.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=ROBOTS_ALLOW_ALL)
        return httpx.Response(200, text="should never be requested by plan()")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    crawler = Crawler(base_config(sitemaps=[]), client=client)
    crawler.plan(urls=["https://example.org/page-a"])
    assert "/page-a" not in fetched_paths   # only robots.txt should have been hit


def test_plan_respects_max_pages():
    crawler = Crawler(base_config(max_pages=1), client=make_client())
    report = crawler.plan(urls=["https://example.org/a", "https://example.org/b"])
    assert len(report.would_fetch) <= 1


def test_fetch_one_respects_allowlist():
    crawler = Crawler(base_config(), client=make_client())
    result = crawler.fetch_one("https://not-allowed.example.com/page")
    assert result.content is None and result.skipped_reason == "not_allowlisted"


def test_fetch_one_respects_robots():
    crawler = Crawler(base_config(), client=make_client(robots_text=ROBOTS_DISALLOW_ONE))
    result = crawler.fetch_one("https://example.org/secret")
    assert result.content is None and result.skipped_reason == "robots_disallowed"


def test_fetch_one_returns_content_when_allowed():
    client = make_client(pages={"https://example.org/page-a": "<html>hello</html>"})
    crawler = Crawler(base_config(), client=client)
    result = crawler.fetch_one("https://example.org/page-a")
    assert result.status_code == 200 and "hello" in result.content


def test_fetch_one_handles_network_error_gracefully():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=ROBOTS_ALLOW_ALL)
        raise httpx.ConnectError("refused")

    crawler = Crawler(base_config(), client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = crawler.fetch_one("https://example.org/page-a")
    assert result.content is None and result.skipped_reason.startswith("error:")


def test_rate_limit_delays_second_request_to_same_domain(monkeypatch):
    sleep_calls = []
    monkeypatch.setattr("crawler.fetcher.time.sleep", lambda s: sleep_calls.append(s))

    client = make_client(pages={"https://example.org/page-a": "x", "https://example.org/page-b": "y"})
    crawler = Crawler(base_config(rate_limit_seconds=5.0), client=client)
    crawler.fetch_one("https://example.org/page-a")
    crawler.fetch_one("https://example.org/page-b")
    assert len(sleep_calls) == 1   # no wait before the first request, one before the second
    assert sleep_calls[0] > 0
