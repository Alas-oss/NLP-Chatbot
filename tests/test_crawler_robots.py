import httpx
import pytest

from crawler.robots import RobotsGate

# A trimmed excerpt of King's ACTUAL published robots.txt (as of this project),
# kept here specifically to prove Protego parses ITS wildcard patterns
# correctly -- this is the exact kind of rule urllib.robotparser gets wrong.
KCL_ROBOTS_EXCERPT = """
User-agent: *
Disallow: *?ContensisTextOnly=true*
Disallow: /search/
Disallow: /study/modules*
Disallow: *page=*
Disallow: *utm_*

Sitemap: https://www.kcl.ac.uk/sitemap.xml
"""


def make_client(robots_text: str, status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(status, text=robots_text)
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_allows_a_plain_page_not_matched_by_any_rule():
    gate = RobotsGate(make_client(KCL_ROBOTS_EXCERPT), user_agent="TestBot")
    assert gate.can_fetch("https://www.kcl.ac.uk/about/governance-policies-and-procedures")


def test_blocks_wildcard_query_string_pattern():
    gate = RobotsGate(make_client(KCL_ROBOTS_EXCERPT), user_agent="TestBot")
    assert not gate.can_fetch("https://www.kcl.ac.uk/some/page?ContensisTextOnly=true&x=1")


def test_blocks_utm_tracking_wildcard():
    gate = RobotsGate(make_client(KCL_ROBOTS_EXCERPT), user_agent="TestBot")
    assert not gate.can_fetch("https://www.kcl.ac.uk/news/article?utm_source=twitter")


def test_blocks_prefix_wildcard():
    gate = RobotsGate(make_client(KCL_ROBOTS_EXCERPT), user_agent="TestBot")
    assert not gate.can_fetch("https://www.kcl.ac.uk/study/modules/some-module")


def test_blocks_plain_prefix_rule():
    gate = RobotsGate(make_client(KCL_ROBOTS_EXCERPT), user_agent="TestBot")
    assert not gate.can_fetch("https://www.kcl.ac.uk/search/results")


def test_fails_closed_when_robots_txt_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    gate = RobotsGate(client, user_agent="TestBot")
    # No robots.txt could be fetched -> treat the whole domain as disallowed,
    # not as wide open.
    assert not gate.can_fetch("https://unreachable.example.com/anything")


def test_fails_closed_on_non_200_robots_response():
    gate = RobotsGate(make_client("irrelevant", status=500), user_agent="TestBot")
    assert not gate.can_fetch("https://www.kcl.ac.uk/anything")


def test_missing_robots_txt_404_means_unrestricted():
    # A 404 is a *successful* response telling us there's no robots.txt file at
    # all. Standard convention treats that as "no restrictions" - distinct from
    # a real error (500, connection failure), which fails closed instead.
    gate = RobotsGate(make_client("irrelevant", status=404), user_agent="TestBot")
    assert gate.can_fetch("https://www.kcl.ac.uk/anything")


def test_result_is_cached_between_calls_to_the_same_domain():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, text=KCL_ROBOTS_EXCERPT)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gate = RobotsGate(client, user_agent="TestBot")
    gate.can_fetch("https://www.kcl.ac.uk/a")
    gate.can_fetch("https://www.kcl.ac.uk/b")
    gate.can_fetch("https://www.kcl.ac.uk/c")
    assert calls["count"] == 1   # robots.txt fetched once, not once per URL
