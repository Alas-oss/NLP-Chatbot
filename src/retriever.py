from collections import defaultdict
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from ingest import load_vector_store, load_chunks
from reranker import rerank

def _cap_per_source(docs: list, max_per_source: int = 10) -> list:
    by_source = defaultdict(list)
    for doc in docs:
        by_source[doc.metadata.get("source", "unknown")].append(doc)

    capped = []
    for source, source_docs in by_source.items():
        capped.extend(source_docs[:max_per_source])
    return capped

def build_hybrid_retriever():
    vector_store = load_vector_store()
    semantic_retriever = vector_store.as_retriever(search_kwargs={"k": 20})

    chunks = load_chunks()
    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = 20

    ensemble = EnsembleRetriever(retrievers=[semantic_retriever, bm25_retriever], weights=[0.6, 0.4])

    def retrieve_and_rerank(query: str):
        candidates = ensemble.invoke(query)
        balanced = _cap_per_source(candidates, max_per_source=10)
        return rerank(query, balanced, top_n=4)

    return retrieve_and_rerank