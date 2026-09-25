import httpx

from crawler.discovery import discover_urls

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.org/sitemap1.xml</loc></sitemap>
  <sitemap><loc>https://example.org/sitemap2.xml</loc></sitemap>
</sitemapindex>"""

SITEMAP_1 = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.org/page-a</loc></url>
  <url><loc>https://example.org/page-b</loc></url>
</urlset>"""

SITEMAP_2 = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.org/page-c</loc></url>
  <url><loc>https://example.org/page-a</loc></url>
</urlset>"""


def make_client(pages: dict[str, str]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        body = pages.get(str(request.url))
        return httpx.Response(200, text=body) if body else httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_flat_urlset_returns_its_urls():
    client = make_client({"https://example.org/sitemap1.xml": SITEMAP_1})
    urls = discover_urls(client, ["https://example.org/sitemap1.xml"], "TestBot")
    assert urls == ["https://example.org/page-a", "https://example.org/page-b"]


def test_sitemap_index_recurses_one_level():
    client = make_client({
        "https://example.org/sitemap.xml": SITEMAP_INDEX,
        "https://example.org/sitemap1.xml": SITEMAP_1,
        "https://example.org/sitemap2.xml": SITEMAP_2,
    })
    urls = discover_urls(client, ["https://example.org/sitemap.xml"], "TestBot")
    assert set(urls) == {"https://example.org/page-a", "https://example.org/page-b", "https://example.org/page-c"}


def test_duplicate_urls_across_sitemaps_are_deduped():
    client = make_client({
        "https://example.org/sitemap.xml": SITEMAP_INDEX,
        "https://example.org/sitemap1.xml": SITEMAP_1,
        "https://example.org/sitemap2.xml": SITEMAP_2,
    })
    urls = discover_urls(client, ["https://example.org/sitemap.xml"], "TestBot")
    assert len(urls) == len(set(urls))


def test_unreachable_sitemap_is_skipped_not_fatal():
    client = make_client({"https://example.org/sitemap1.xml": SITEMAP_1})
    urls = discover_urls(
        client,
        ["https://example.org/missing.xml", "https://example.org/sitemap1.xml"],
        "TestBot",
    )
    assert urls == ["https://example.org/page-a", "https://example.org/page-b"]


def test_malformed_xml_is_skipped_not_fatal():
    client = make_client({
        "https://example.org/broken.xml": "<not valid xml",
        "https://example.org/sitemap1.xml": SITEMAP_1,
    })
    urls = discover_urls(
        client,
        ["https://example.org/broken.xml", "https://example.org/sitemap1.xml"],
        "TestBot",
    )
    assert urls == ["https://example.org/page-a", "https://example.org/page-b"]


def test_no_sitemaps_returns_empty_list():
    assert discover_urls(make_client({}), [], "TestBot") == []
