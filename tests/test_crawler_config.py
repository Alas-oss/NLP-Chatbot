import pytest

from crawler.config import ConfigError, load_config


def write(tmp_path, text):
    p = tmp_path / "sources.yaml"
    p.write_text(text)
    return p


def test_missing_file_raises():
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/sources.yaml")


def test_defaults_are_safe_when_file_is_minimal(tmp_path):
    config = load_config(write(tmp_path, "crawl:\n  enabled: false\n"))
    assert config.enabled is False
    assert config.allowlist == []
    assert config.max_pages >= 1


def test_full_valid_config_loads(tmp_path):
    config = load_config(write(tmp_path, """
crawl:
  enabled: true
  user_agent: "TestBot/1.0 (+mailto:test@example.com)"
  rate_limit_seconds: 1.5
  max_pages: 10
allowlist: ["example.org"]
seeds:
  sitemaps: ["https://example.org/sitemap.xml"]
  urls: ["https://example.org/page"]
"""))
    assert config.enabled is True
    assert config.allowlist == ["example.org"]
    assert config.rate_limit_seconds == 1.5
    assert config.sitemaps == ["https://example.org/sitemap.xml"]


def test_negative_rate_limit_rejected(tmp_path):
    with pytest.raises(ConfigError, match="rate_limit_seconds"):
        load_config(write(tmp_path, "crawl:\n  rate_limit_seconds: -1\n"))


def test_zero_max_pages_rejected(tmp_path):
    with pytest.raises(ConfigError, match="max_pages"):
        load_config(write(tmp_path, "crawl:\n  max_pages: 0\n"))


def test_placeholder_user_agent_blocks_enabling(tmp_path):
    with pytest.raises(ConfigError, match="placeholder"):
        load_config(write(tmp_path, """
crawl:
  enabled: true
  user_agent: "CHANGE-ME-Bot/0.1"
allowlist: ["example.org"]
"""))


def test_placeholder_user_agent_ok_while_disabled(tmp_path):
    # the placeholder is only a problem once someone tries to actually enable it
    config = load_config(write(tmp_path, 'crawl:\n  enabled: false\n  user_agent: "CHANGE-ME-Bot/0.1"\n'))
    assert config.enabled is False


def test_invalid_seed_url_rejected(tmp_path):
    with pytest.raises(ConfigError, match="not a valid"):
        load_config(write(tmp_path, 'seeds:\n  urls: ["not-a-url"]\n'))


def test_is_allowed_domain():
    config = load_config
    from crawler.config import CrawlConfig
    c = CrawlConfig(allowlist=["www.kcl.ac.uk"])
    assert c.is_allowed_domain("https://www.kcl.ac.uk/policyhub/page")
    assert not c.is_allowed_domain("https://evil.com/page")
    assert not c.is_allowed_domain("https://kcl.ac.uk.evil.com/page")   # lookalike host
