from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.vectorstores import InMemoryVectorStore

from conftest import doc
from retriever import build_hybrid_retriever


def test_hybrid_retriever_builds_from_injected_store_and_finds_keyword_hits():
    chunks = [
        doc("Extenuating circumstances allow a deadline extension.", title="A"),
        doc("The library is open late during exam season.", title="B"),
        doc("Tuition fees are payable in instalments.", title="C"),
        doc("The Strand Campus hosts the Faculty of Law.", title="D"),
    ]
    store = InMemoryVectorStore(embedding=DeterministicFakeEmbedding(size=32))
    store.add_documents(chunks)

    retriever = build_hybrid_retriever(vector_store=store, chunks=chunks, k=3)
    results = retriever.invoke("extenuating circumstances")

    titles = [d.metadata["title"] for d in results]
    assert "A" in titles                       # BM25 leg finds the exact keyword match
    assert len(results) == len({d.page_content for d in results})   # de-duplicated
