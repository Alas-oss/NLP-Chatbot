from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import httpx

from crawler.config import CrawlConfig
from crawler.discovery import discover_urls
from crawler.robots import RobotsGate

log = logging.getLogger(__name__)


class CrawlerDisabled(RuntimeError):
    """Raised whenever anything tries to make the crawler touch the network
    while it isn't explicitly enabled and allowlisted. This is the safety
    boundary; it is intentionally impossible to bypass by passing an argument."""


@dataclass
class FetchResult:
    url: str
    status_code: int | None
    content: str | None      
    skipped_reason: str | None = None 


@dataclass
class CrawlReport:
    would_fetch: list[str] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)  


class Crawler:
    def __init__(self, config: CrawlConfig, client: httpx.Client | None = None):
        self.config = config
        self._client = client or httpx.Client(timeout=config.request_timeout_seconds)
        self._robots = RobotsGate(self._client, config.user_agent)
        self._last_request_at: dict[str, float] = {}  

    def _check_enabled(self) -> None:
        if not self.config.enabled:
            raise CrawlerDisabled(
                "crawl.enabled is False in sources.yaml. No network request will "
                "be made. Set it to true, with a real allowlist, to run for real."
            )
        if not self.config.allowlist:
            raise CrawlerDisabled(
                "sources.yaml has an empty allowlist. No network request will be "
                "made against any domain until one is added explicitly."
            )

    def _respect_rate_limit(self, domain: str) -> None:
        last = self._last_request_at.get(domain)
        if last is not None:
            wait = self.config.rate_limit_seconds - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self._last_request_at[domain] = time.monotonic()

    def discover(self) -> list[str]:
        self._check_enabled()
        from urllib.parse import urlparse

        found = discover_urls(self._client, self.config.sitemaps, self.config.user_agent,
                               self.config.request_timeout_seconds)
        candidates = [*found, *self.config.urls]
        return [u for u in candidates if self.config.is_allowed_domain(u)]

    def plan(self, urls: list[str] | None = None) -> CrawlReport:
        self._check_enabled()
        urls = urls if urls is not None else self.discover()

        report = CrawlReport()
        for url in urls[: self.config.max_pages]:
            if not self.config.is_allowed_domain(url):
                report.skipped[url] = "not_allowlisted"
                continue
            if not self._robots.can_fetch(url):
                report.skipped[url] = "robots_disallowed"
                continue
            report.would_fetch.append(url)
        return report

    def fetch_one(self, url: str) -> FetchResult:
        self._check_enabled()
        from urllib.parse import urlparse

        if not self.config.is_allowed_domain(url):
            return FetchResult(url, None, None, skipped_reason="not_allowlisted")
        if not self._robots.can_fetch(url):
            return FetchResult(url, None, None, skipped_reason="robots_disallowed")

        domain = urlparse(url).netloc
        self._respect_rate_limit(domain)

        try:
            response = self._client.get(url, headers={"User-Agent": self.config.user_agent})
            return FetchResult(url, response.status_code, response.text)
        except httpx.HTTPError as e:
            log.warning("Fetch failed for %s: %s", url, e)
            return FetchResult(url, None, None, skipped_reason=f"error:{type(e).__name__}")

    def close(self) -> None:
        self._client.close()