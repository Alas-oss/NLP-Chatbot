import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class FakeLLM:

    def __init__(self, *replies):
        self.replies = list(replies) or ["NO_ANSWER"]
        self.calls = []

    def invoke(self, messages, config=None):
        self.calls.append(messages)
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(content=reply)


class FakeRetriever:
    def __init__(self, docs):
        self.docs, self.queries = docs, []

    def invoke(self, query):
        self.queries.append(query)
        return list(self.docs)


class FakeReranker:

    def __init__(self, scores):
        self.scores = scores

    def rerank(self, query, docs, top_n):
        return list(zip(docs, self.scores))[:top_n]


def doc(text, **meta):
    return Document(page_content=text, metadata=meta)


@pytest.fixture
def docs():
    return [
        doc("The Strand Campus is the historic main site, home to arts, humanities and law.",
            title="Campuses", url="https://example.org/campuses"),
        doc("Guy's Campus is near London Bridge and focuses on health and life sciences.",
            title="Campuses", url="https://example.org/campuses"),
        doc("King's was founded in 1829 by King George IV and the Duke of Wellington.",
            source="data/history.docx"),
    ]
