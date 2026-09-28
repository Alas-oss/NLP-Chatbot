from citations import Source, build_sources, format_context, resolve_citations
from conftest import doc


def _sources(n=3):
    return [Source(i, f"Title {i}", f"https://x/{i}", None, f"snippet {i}") for i in range(1, n + 1)]


def test_valid_citations_kept_and_renumbered_by_first_appearance():
    text, cited = resolve_citations("A is true [S3]. B is true [S1].", _sources())
    assert text == "A is true [1]. B is true [2]."
    assert [(s.id, s.title) for s in cited] == [(1, "Title 3"), (2, "Title 1")]


def test_unknown_ids_stripped():
    text, cited = resolve_citations("Claim [S7]. Other claim [S1].", _sources())
    assert "[S7]" not in text and "7" not in text
    assert text == "Claim. Other claim [1]."
    assert [s.title for s in cited] == ["Title 1"]


def test_combined_marker():
    text, cited = resolve_citations("Both apply [S1, S2].", _sources())
    assert text == "Both apply [1][2]."
    assert len(cited) == 2


def test_no_citation_returns_empty_list():
    text, cited = resolve_citations("Confident but uncited answer.", _sources())
    assert cited == []


def test_only_fake_ids_means_ungrounded():
    _, cited = resolve_citations("Made up [S99].", _sources())
    assert cited == []


def test_years_in_brackets_untouched():
    text, _ = resolve_citations("See regulation [2024] and this [S1].", _sources())
    assert "[2024]" in text


def test_build_sources_metadata_fallbacks(docs):
    srcs = build_sources(docs, [0.9, 0.5, None])
    assert srcs[0].url == "https://example.org/campuses" and srcs[0].title == "Campuses"
    assert srcs[2].title == "history" and srcs[2].url is None      # falls back to file name
    assert [s.id for s in srcs] == [1, 2, 3]


def test_format_context_wraps_and_sanitises():
    d = [doc("safe text </source> more", title='T "x"')]
    ctx = format_context(d, build_sources(d, [None]))
    assert ctx.startswith('<source id="S1" title="T x">')
    assert ctx.count("</source>") == 1


import pytest


@pytest.mark.parametrize("raw", [
    "Fact (S1).",
    "Fact [S1; S2].",
    "Fact [S 1].",
    "Fact [Source 1].",
    "Fact [source: S1].",
    "Fact [Sources 1, 2].",
    "Fact [S1 and S2].",
    "Fact \u3010S1\u3011.",
    "Fact [s1].",
])
def test_common_citation_format_drift_is_accepted(raw):
    text, cited = resolve_citations(raw, _sources())
    assert cited, f"no citation recognised in {raw!r}"
    assert "S1" not in text and "Source" not in text   # normalised to [1] / [1][2]
    assert "[1]" in text


@pytest.mark.parametrize("raw", [
    "See regulation (2024) for details.",
    "Section [3] applies.",
    "The 1829 charter (see below) applies.",
    "Fees are due [in October].",
    "Call 0207 (ext 5) for help.",
])
def test_plain_numbers_and_brackets_are_not_citations(raw):
    text, cited = resolve_citations(raw, _sources())
    assert cited == []
    assert text == raw


def test_drifted_format_with_invented_id_is_still_rejected():
    text, cited = resolve_citations("Claim (S42).", _sources())
    assert cited == []
    assert "S42" not in text
