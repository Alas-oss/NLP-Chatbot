# Project Report: RAG-Based Domain Chatbot

## 1. Purpose

This project originally used a TF-IDF + logistic regression classifier, matching a small set of hand-written categories and falling back to an ungrounded LLM call for anything else. It was deliberately rebuilt into a retrieval-augmented generation (RAG) system: instead of classifying a message into one of a few trained categories, the system retrieves relevant passages from a specific source document and has an LLM generate an answer grounded in that retrieved content. The goal shifted from "recognise a handful of known message types" to "answer open-ended questions accurately about a specific body of knowledge", which a fixed-category classifier structurally cannot do.

## 2. Why the pivot away from intent classification

The original classifier worked well for its narrow purpose (greetings, FAQ-style categories) but had no mechanism to "know" facts - it could only route a message to one of a small number of trained buckets. Expanding its scope to cover general knowledge would have meant either training on an impractically large, constantly growing set of categories, or accepting that most questions would fall through to an ungrounded LLM call with no guarantee that the answer reflected any particular source. RAG addresses this directly: retrieval narrows the LLM's attention to the most relevant real content before it generates anything, and an explicit grounding instruction in the prompt tells it to decline rather than guess when the retrieved context doesn't contain an answer.

## 3. Architecture

- **Chunking**: a source `.docx` document is loaded and split using a recursive character text splitter, which prefers paragraph and sentence boundaries over hard character cuts, keeping each chunk topically coherent.
- **Embeddings + vector storage**: chunks are embedded via an API-based embedding model and stored in a vector index for similarity search. The vector store went through two iterations: an initial Chroma-based store, replaced by a pure-Python in-memory store after a native-binary crash (see section 4).
- **Hybrid retrieval**: queries are matched two ways simultaneously - semantic (embedding) search and BM25 keyword search - combined via reciprocal rank fusion (about 60% semantic / 40% keyword weighting). Semantic search generalises over phrasing; BM25 reliably catches exact terms and proper nouns that embedding similarity can under-weight.
- **Reranking and relevance gate**: a cross-encoder rescores the retrieved candidates. If even the best candidate scores below a threshold, the system refuses without calling the LLM.
- **Named-entity boost**: entities are extracted from each chunk at ingest time and from the query at question time; chunks sharing an entity with the query get a small ranking boost.
- **Grounded generation**: retrieved chunks are inserted into a prompt that instructs the model to answer only from that context, cite each claim, and say so plainly when it doesn't have the relevant information, rather than filling gaps from its own general training knowledge.
- **Citation validation and guardrails**: every citation in an answer is checked against the sources actually retrieved; answers with no valid citation are discarded. Input and retrieved text are screened for prompt-injection patterns, and follow-up questions are rewritten into standalone queries using recent conversation history.

## 4. Building process - technical challenges and how they were resolved

**Import-time crash from an unrelated dependency.** The text-splitter package's top-level import unconditionally pulled in a sentence-embedding library (and, transitively, a deep learning framework), which crashed at import time on Windows before any of the actual chunking logic ran. Fixed by importing the needed class directly from its submodule rather than through the package's `__init__`, bypassing the problematic import chain entirely - the chunking logic itself never needed that dependency.

**Local embedding model made unnecessary.** An initial design used a locally run embedding model, which meant importing a deep learning runtime just to embed short strings of text. This was replaced with an API-based embedding call, which removed the need for a local ML runtime, a large model download, and exposure to platform-specific native-binary issues for that part of the pipeline.

**A genuine native-binary crash in the vector store.** Building the vector index initially caused a hard access-violation crash (not a Python exception, but a segmentation fault in compiled C++ code) inside the chosen vector database's native dependencies. This was isolated methodically: importing the database package alone worked, importing the embedding client alone worked, but building an actual index crashed. Since the underlying native library issue couldn't be resolved without administrator-level system changes that weren't available, the fix was to switch to a vector store with zero compiled dependencies, using a pure-Python, NumPy-backed in-memory store. This trades some scalability at very large corpus sizes for reliability at the scale this project actually operates at, and eliminated an entire class of platform-specific crash risk.

**A package restructure broke an import mid-project.** A retrieval utility class that combines multiple retrievers was removed from the core orchestration library's public namespace in a recent version and relocated to a separately versioned package. This was diagnosed by checking directly against the installed package version rather than assuming the older import path was still appropriate, and it confirmed that some functionality that used to live in the main library has been split out into companion packages as the library matures. Verifying against the actual installed version, not memory or older documentation, is the reliable way to resolve these import errors.

**A silent failure mode in the entity boost.** While adding the named-entity boost, an early version replaced the reranker's score with a boosted one. When the reranker was disabled (scores are `None`, meaning "skip the relevance gate"), this turned `None` into a real number and caused false refusals. It was caught by the test suite rather than by inspection, and fixed by using the boosted value only as a sort key while preserving each candidate's original score for the gate decision.

## 5. Current status

- The full pipeline - chunking, embedding, hybrid retrieval, reranking, entity boost, grounded generation, citation validation - is built and covered by an automated test suite (fake LLMs and retrievers, no API keys needed) that runs in CI.
- A separate golden-set evaluation script measures answer quality against known questions using the real pipeline.
- A web crawler exists but is disabled by default and gated in code behind an explicit enable flag and a domain allowlist. Nothing has been crawled from any real site.
- Retrieval currently covers a single sample source document. Extending to multiple documents or web pages would need per-chunk source metadata (URL, title, section) so answers can link back to their originating page; this is the main open item before real content could be indexed.
- Langfuse tracing is optional (skipped unless API keys are configured), but a live trace was inspected and confirmed to log everything: the full question, the full system prompt (including retrieved source content and the internal canary marker), the model's reasoning, and the answer, with no redaction. This needs a data-protection review, and likely masking or redaction, before any real student input is processed with tracing enabled.
