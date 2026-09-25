from __future__ import annotations

from xml.etree import ElementTree

import httpx

_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _fetch_xml(client: httpx.Client, url: str, user_agent: str, timeout: float) -> ElementTree.Element | None:
    try:
        response = client.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
        response.raise_for_status()
        return ElementTree.fromstring(response.content)
    except (httpx.HTTPError, ElementTree.ParseError):
        return None


def discover_urls(client: httpx.Client, sitemap_urls: list[str], user_agent: str,
                   timeout: float = 10.0, _depth: int = 0) -> list[str]:
    urls: list[str] = []
    for sitemap_url in sitemap_urls:
        root = _fetch_xml(client, sitemap_url, user_agent, timeout)
        if root is None:
            continue

        nested = [el.text for el in root.findall(".//sm:sitemap/sm:loc", _NS) if el.text]
        if nested and _depth == 0:
            urls.extend(discover_urls(client, nested, user_agent, timeout, _depth=1))

        urls.extend(el.text for el in root.findall(".//sm:url/sm:loc", _NS) if el.text)

    seen: set[str] = set()
    deduped = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped
