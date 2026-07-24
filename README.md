# NLP Chatbot -- RAG with Multi-Document Retrieval, Reranking, and Source Trust Weighting

Branch: `feature/pdf-ocr-reranking`

This branch extends the core RAG chatbot with: PDF ingestion (with OCR fallback for image-only pages), multi-document retrieval across mixed source types with per-source balancing, LLM-based reranking in place of fixed retrieval weights, and per-source trust weighting.

## What's new and different on this branch

- `src/pdf_loader.py` -- PDF text extraction, with automatic OCR fallback for pages with no extractable text.
- `src/chunking.py`'s `load_all_sources()` -- loads every `.docx` and `.pdf` in `data/`, tagging each one with a `doc_type`.
- `src/ingest.py`'s `build_vector_store()` -- embeds in rate-limited batches with automatic backoff, became required once real multi-hundred-page sources were added 
- `src/retriever.py`'s `_cap_per_source()` -- guarantess every ingested source is represented in the reranking candidate pool regardless of how many total chunks it contributed, preventing a large source from silently crowding out a small one before relevance is ever judged.
- `src/reranker.py` -- LLM-based relevance reranking that also blends in each source's trust score, replacing the static ensemble weighting as the final ranking signal.
- `experiments/chunk_size_test.py` -- a harness for comparing retrieval quality across different chunk sizes on real test queries.

## Setup

Same as the core project, plus:
``` 
uv add pypdf pytesseract pdf2image pillow
```
Tesseract OCR must also be installed as a system binary.

## Ingesting multiple, mixed-type sources

Place any `.docx` and `.pdf` files in `data/`, then, from the repo root run:
```
uv run python ingest.py
```
Embedding runs in batches with automatic rate-limit backoff -- for a large source (several hundred pages), this can take a meaningful amount of time; let it run to completion rather than interrupting partway through.

## Testing

1. Confirm that both sources are present and are correctly tagged after ingestion (`doc_type` counts should show more than one distinct source type).
2. Run the multi-document retrieval diagnostic and confirm each of a set of clearly source-specific test queries returns chunks from its correct source, not the other one.
3. Treat end-to-end through the interactive chatbot with a mix of source-specific and out-of-scope questions, confirming grounding still holds throughout.