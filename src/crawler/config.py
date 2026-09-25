from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import yaml


class ConfigError(ValueError):
    """The config file is missing, malformed, or fails validation."""

@dataclass
class CrawlConfig:
    enabled: bool = False
    user_agent: str = "unset"
    rate_limit_seconds: float = 2.0
    max_pages: int = 50
    request_timeout_seconds: float = 10.0
    allowlist: list[str] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)

    def is_allowed_domain(self, url: str) -> bool:
        host = urlparse(url).hostname or ""
        return host.lower() in {d.lower() for d in self.allowlist}


def load_config(path: str | Path = "sources.yaml") -> CrawlConfig:
    path = Path(path)
    if not path.exists():
        raise ConfigError(
            f"{path} not found. The crawler will not run without an explicit "
            "config file - this is deliberate, not a bug."
        )

    raw = yaml.safe_load(path.read_text()) or {}
    crawl = raw.get("crawl") or {}
    seeds = raw.get("seeds") or {}

    config = CrawlConfig(
        enabled=bool(crawl.get("enabled", False)),
        user_agent=str(crawl.get("user_agent", "unset")),
        rate_limit_seconds=float(crawl.get("rate_limit_seconds", 2.0)),
        max_pages=int(crawl.get("max_pages", 50)),
        request_timeout_seconds=float(crawl.get("request_timeout_seconds", 10.0)),
        allowlist=list(raw.get("allowlist") or []),
        sitemaps=list(seeds.get("sitemaps") or []),
        urls=list(seeds.get("urls") or []),
    )
    _validate(config)
    return config


def _validate(config: CrawlConfig) -> None:
    if config.rate_limit_seconds < 0:
        raise ConfigError("crawl.rate_limit_seconds must not be negative.")
    if config.max_pages < 1:
        raise ConfigError("crawl.max_pages must be at least 1.")
    if "CHANGE-ME" in config.user_agent and config.enabled:
        raise ConfigError(
            "crawl.user_agent is still the placeholder. Set a real identifying "
            "user agent (with contact info) before enabling the crawler."
        )
    for seed_url in [*config.sitemaps, *config.urls]:
        if not urlparse(seed_url).scheme.startswith("http"):
            raise ConfigError(f"Seed URL is not a valid http(s) URL: {seed_url!r}")