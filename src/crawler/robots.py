from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from protego import Protego


@dataclass
class _CacheEntry:
    parser: Protego
    fetched_at: float


class RobotsGate:
    def __init__(self, client: httpx.Client, user_agent: str, refresh_after: float = 3600.0):
        self._client = client
        self._user_agent = user_agent
        self._refresh_after = refresh_after
        self._cache: dict[str, _CacheEntry] = {}

    def _robots_url(self, url: str) -> str:
        parsed = urlparse(url)
        return urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")

    def _get_parser(self, url: str) -> Protego:
        domain = urlparse(url).netloc
        cached = self._cache.get(domain)
        if cached and (time.monotonic() - cached.fetched_at) < self._refresh_after:
            return cached.parser

        robots_url = self._robots_url(url)
        try:
            response = self._client.get(robots_url, headers={"User-Agent": self._user_agent})
        except httpx.HTTPError:
            text = "User-agent: *\nDisallow: /"
        else:
            if response.status_code == 200:
                text = response.text
            elif response.status_code == 404:
                text = ""
            else:
                text = "User-agent: *\nDisallow: /"

        parser = Protego.parse(text)
        self._cache[domain] = _CacheEntry(parser=parser, fetched_at=time.monotonic())
        return parser

    def can_fetch(self, url: str) -> bool:
        return self._get_parser(url).can_fetch(url, self._user_agent)

    def crawl_delay(self, url: str) -> float | None:
        return self._get_parser(url).crawl_delay(self._user_agent)
