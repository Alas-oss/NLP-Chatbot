from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

from config import RETRIEVAL_K, SEMANTIC_WEIGHT, BM25_WEIGHT


def build_hybrid_retriever(vector_store=None, chunks=None, k: int = RETRIEVAL_K):
    """Semantic + BM25, fused with weighted reciprocal rank fusion.

    `vector_store` / `chunks` can be injected (tests, or a different store later);
    by default they are loaded from disk exactly as before. `k` is per retriever:
    we deliberately over-fetch, because the reranker narrows it down afterwards.
    """
    if vector_store is None or chunks is None:
        from ingest import load_vector_store, load_chunks  # lazy: needs API keys + google package
        vector_store = vector_store or load_vector_store()
        chunks = chunks or load_chunks()

    semantic_retriever = vector_store.as_retriever(search_kwargs={"k": k})

    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = k

    return EnsembleRetriever(
        retrievers=[semantic_retriever, bm25_retriever],
        weights=[SEMANTIC_WEIGHT, BM25_WEIGHT],
    )
