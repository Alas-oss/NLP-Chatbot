from entities import boost_score, extract_entities


def test_extracts_named_organisations():
    ents = extract_entities("Where is Guy's Campus near King's College London?")
    assert "guy's campus" in ents
    assert any("king's college london" in e for e in ents)


def test_empty_text_returns_empty_set():
    assert extract_entities("") == set()
    assert extract_entities("   ") == set()


def test_no_entities_in_plain_question():
    assert extract_entities("what time does it open") == set()


def test_boost_adds_per_shared_entity():
    q = {"guy's campus", "london"}
    chunk = {"guy's campus"}
    assert boost_score(q, chunk, base_score=0.5) == 0.55


def test_boost_no_overlap_returns_base_unchanged():
    assert boost_score({"strand"}, {"guy's campus"}, base_score=0.7) == 0.7


def test_boost_multiple_matches_stack():
    q = {"guy's campus", "london bridge"}
    chunk = {"guy's campus", "london bridge"}
    assert boost_score(q, chunk, base_score=0.1, per_match=0.05) == 0.2


def test_boost_handles_none_base_score():
    assert boost_score({"a"}, {"a"}, base_score=None, default_base=0.0, per_match=0.05) == 0.05
    assert boost_score({"a"}, {"b"}, base_score=None) == 0.0
