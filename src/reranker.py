"""Second-stage reranking.

Hybrid retrieval is tuned for recall (fetch ~20 candidates from each retriever).
A cross-encoder reads query and passage *together*, which is much more precise,
so we use it to pick the few chunks the LLM actually sees, and to give us a real
relevance score for the "don't answer" decision.

FlashRank runs ONNX models on CPU - no torch, so it avoids the deep-learning
import problems described in report.md. If it can't load (missing package,
model download blocked, native-binary problem) we fall back to a no-op that
keeps the hybrid retriever's order, and the pipeline still works.
"""
import logging
from typing import Protocol

from langchain_core.documents import Document

log = logging.getLogger(__name__)


class Reranker(Protocol):
    def rerank(self, query: str, docs: list[Document], top_n: int) -> list[tuple[Document, float | None]]: ...


class NoOpReranker:
    """Keeps retrieval order. Scores are None, so the relevance gate is skipped."""

    def rerank(self, query, docs, top_n):
        return [(d, None) for d in docs[:top_n]]


class FlashrankReranker:
    def __init__(self, model_name: str):
        from flashrank import Ranker  # imported lazily so it stays optional

        self._ranker = Ranker(model_name=model_name)

    def rerank(self, query, docs, top_n):
        if not docs:
            return []
        from flashrank import RerankRequest

        passages = [{"id": i, "text": d.page_content} for i, d in enumerate(docs)]
        ranked = self._ranker.rerank(RerankRequest(query=query, passages=passages))
        return [(docs[p["id"]], float(p["score"])) for p in ranked[:top_n]]


def build_reranker(name: str, model_name: str) -> Reranker:
    if name == "none":
        return NoOpReranker()
    if name == "flashrank":
        try:
            return FlashrankReranker(model_name)
        except Exception as e:  # noqa: BLE001 - any failure should degrade, not crash
            log.warning("FlashRank unavailable (%s: %s); continuing without reranking.", type(e).__name__, e)
            return NoOpReranker()
    raise ValueError(f"Unknown RERANKER {name!r} (expected 'flashrank' or 'none')")
