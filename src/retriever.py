from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

from config import RETRIEVAL_K, SEMANTIC_WEIGHT, BM25_WEIGHT


def build_hybrid_retriever(vector_store=None, chunks=None, k: int = RETRIEVAL_K):
    if vector_store is None or chunks is None:
        from ingest import load_vector_store, load_chunks 
        vector_store = vector_store or load_vector_store()
        chunks = chunks or load_chunks()

    semantic_retriever = vector_store.as_retriever(search_kwargs={"k": k})

    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = k

    return EnsembleRetriever(
        retrievers=[semantic_retriever, bm25_retriever],
        weights=[SEMANTIC_WEIGHT, BM25_WEIGHT],
    )
