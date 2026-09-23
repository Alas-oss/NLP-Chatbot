import pytest

import reranker as rr
from conftest import doc


def test_noop_keeps_order_and_has_no_scores():
    docs = [doc("a"), doc("b"), doc("c")]
    out = rr.NoOpReranker().rerank("q", docs, 2)
    assert [d.page_content for d, _ in out] == ["a", "b"]
    assert all(s is None for _, s in out)


def test_build_none():
    assert isinstance(rr.build_reranker("none", "m"), rr.NoOpReranker)


def test_build_unknown_raises():
    with pytest.raises(ValueError):
        rr.build_reranker("cohere", "m")


def test_flashrank_failure_degrades_to_noop(monkeypatch):
    def boom(self, model_name):
        raise OSError("model download blocked")
    monkeypatch.setattr(rr.FlashrankReranker, "__init__", boom)
    assert isinstance(rr.build_reranker("flashrank", "m"), rr.NoOpReranker)


def test_flashrank_maps_scores_back_to_docs():
    pytest.importorskip("flashrank")

    class FakeRanker:
        def rerank(self, request):
            # pretend passage 2 is best, then 0, then 1
            by_id = {p["id"]: p for p in request.passages}
            return [dict(by_id[2], score=0.9), dict(by_id[0], score=0.4), dict(by_id[1], score=0.1)]

    r = object.__new__(rr.FlashrankReranker)
    r._ranker = FakeRanker()
    docs = [doc("zero"), doc("one"), doc("two")]
    out = r.rerank("q", docs, top_n=2)
    assert [(d.page_content, s) for d, s in out] == [("two", 0.9), ("zero", 0.4)]
    assert isinstance(out[0][1], float)
    assert r.rerank("q", [], 3) == []
