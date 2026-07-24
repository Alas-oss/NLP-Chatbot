# Project Report: RAG-Based Generation Chatbot

## Execution Summary

This report documents the design, implementation, and verification of a retrieval-augmented generation (RAG) chatbot system. The system evolved through two architcturally distinct phases: an initial rule-based/statistical intent classifier, and a subsequent RAG pipeline supporting multi-document ingestion, hybrid retrieval, relevance-based reranking, and source trust weighting. The system has been tested end-to-end against two topically distinct knowledge sources and correctly answers questions grounded in each, with verified source attribution and no observed cross-contamination between sources.

## 1. Objectives

The system was designed to answer open-ended natural language questions by retrieving relevant information from a defined knowledge base, rather than relying solely on a language model's general training knowledge. The specific technical objectives included:

- Support ingestion of multiple document formats (Word documents and PDFs, including scanned/image-based pages) into a unified knowledge base.
- Combine multiple retrieval strategies (semantic and lexical, specifically keyword) to improve recall and precision over either method alone.
- Rank retrieved information by genuine relevance to a given query rather than a fixed, query-independent weighting scheme. 
- Incorporate a notion of source reliability into ranking. 
- Ensure retrieval remains fair and unbiased when knowledge sources of very different sizes are combined.
- Maintain full observability into system behavior via distributed tracing.

## 2. System Architecture

### 2.1 Ingestion Pipeline
source documents are loaded via format-specific loaders (Word document paragraph extraction; PDF page-level text extraction with automatic optical character recognition fallback for image-only pages), tagged with source-type metadata, and split into retrieval-sized chunks using a recursive boundary-aware text splitter that prefrerentially splits on paragraph and sentence boundaries.

### 2.2 Embedding and Storage
Each chunk is converted to a vector embedding via an external embedding API and stored in an in-memory vector index. Embedding is performed in rate-limited batches with automatic exponential backoff, required to operate reliability against the embedding provider's request-volume constraints once a large (several-hudred-page) source was introduced. The resulting chunk set is persisted independently of the vector index, avoiding redundant recomputation on subsequent runs.

### 2.3 Hybrid Retrieval
Queries are matched against the knowledge base via two independent methods executed in parallel: dense semantic similarity search over the vector index, and sparse lexical/keyword search (BM25) over the same chunk set. Results are combined via reciprocal rank fusion. This dual-method design mitigates the respective weaknesses of each approach in isolation - semantic search generalizes across paraphrasing but can under-weight exact terminology; lexical search reliably surfaces exact terms but does not generalize across phrasing.

### 2.4 Candidate Balancing
Prior to final ranking, retrieved candidates are grouped by source and capped at a fixed maximum per source. This step was introduced after verification testing revealed that, without it, a source contributing a disproportionately large number of total chunks could dominate the candidate pool before relevance was ever assessed, effectively excluding smaller sources from consideration regardless of query relevance.

### 2.5 Reranking and Trust Weighting
The balanced candidate set is scored for query specific relevance via a language-model based reranking step, which evaluates each candidate against the specific query rather than relying on static, query-independent weights. This relevance score is blended with a per-source trust score, allowing manually assessed source reliability to influence final ranking without overriding genuine relevance.

### 2.6 Grounded Generation
The final ranked context is inserted into a prompt that explicitly instructs the generation model to answer only from the supplied context, and to state clearly when the context does not contain sufficient information, rather than supplementing from its own general knowledge.

### 2.7 Observability
Every generation call is traced through an external distributed tracing platform via a callback-based integration, recording retrieval statistics and query characteristics while deliberately excluding raw query and response text from transmitted metadata, to limit exposure of source-specific content through the tracing layer.

## 3. Development Progression

The system was built incrementally, with each stage validated before the next was introduced:

1. **Baseline intent classification.** An initial implementation used TF-IDF vectorization with a supervised classifier over a small, hand-labeled set of intent categories, falling back to an ungrounded language model call for unmatched input. This implementation is retrained in the repository for reference and comparison.
2. **Pivot to single-source RAG.** The classifier was replaced with a retrieval-augmented pipeline operating over a single source document, establishing the core chunking, embedding, retrieval, and grounded generation flow.
3. **Reliability hardening.** Several platform-specific native-dependency failures were identified and resolved during this phase, including two independent instances of an eagerly-imported deep learning framework crashing at import time on the development platform, and one genuine access-vioaltion fault isolated to a vector database's compiled dependencies. In each case, the dependency in question waas replaced with an alternative implementation (an API-based service, or a pure-Python equivalent) rather than continuing to work around the same underlying platform issue through successive patches.
4. **Multi-format, multi-source expansion.** PDF ingestion with OCR fallback was added, and the ingestion pipeline was generalized to load any supported file type present in the knowedlge base directory without per-format changes elsewhere in the system.
5. **Ranking sophistication.** Static ensemble retrieval weighting was replaced with query-specific relevance scoring, and source trust weighting was introduced as a secondary ranking signal.
6. **Bias identification and correction.** Introducing a large, multi-hundred-page source alongside a much smaller source surface a retrieval bias toward the larger source, caught via direct diagnostic testing rather than assumed absent by default. This was corrected through per-source candidate balancing prior to reranking.
7. **Verification.** End-to-end testing across both knowledge sources confirmed correct, source-appropriate responses with no observed cross-contamination.

## 4. Verification and Test Results

The following verification steps were performed and passed:

- **Metadata integrity**: a direct count of loaded document metadata confirmed correct source-type tagging across all ingested documents.
- **Rate-limit resilience**: full ingestion of a several-hundred-page source (1.855 total chunks across 93 embedding batches) completed successfully under tha batched, backoff-enabled embedding procedure, with zero failed batches in the completed run.
- **Multi-document source attribution**: retrieval queries specific to each of the two ingested knowledge sources were confirmed to return chunks originating from their correct respective source, following the introduction of per-source candidate balancing.
- **End-to-end functional testing**: the complete chatbot pipeline was exercised interactively with questions specific to each knowledge source. All tested questions were answere correctly and consistently, with no errors, crashes, or incorrect source attribution observed during this testing session.

## 5. Known Limitations and Future Work

- Retrieval currently supports two knowledge sources; extension to a larger number of sources would benefit from validating that per-source candidate balancing continues to scale appropriate as source count increase.
- Configuration values (model identifiers, retrieval parameters, trust scores) remain defined inline across several modules, despite one having been scaffolded for this purpose.
- The system does not currently retain conversational context across turns; each query is processed independently.
- Image, chart, and graph content within PDF sources is not currently extracted or made retrievable - only textual content (including OCR-recovered text) contributes to the knowledge base at this time.
- No automated regression test currently exists to guard against a recurrence of the source-attribution bias identified during development; this is recommended as a near-term addition.

## 6. Conclusion

The system has progressed from an initial classification-based prototype to a verified, multi-source, multi-strategy retrieval-augmented generation pipeline with relevance-based reranking, source trust weighting, and distributed tracing. End-to-end testing confirms the system correctly retrieves and grounds responses in source-appropriate content across multiple, substantially different knowledge sources, with prior identified defects (metadata tagging, rate-limit handling, and retrieval bias) each resolved and independently verified. 