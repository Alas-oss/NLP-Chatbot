# NLP Chatbot - Retrieval-Augmented Generation

A chatbot that answers questions grounded in a specific source document, using a retrieval-augmented generation (RAG) pipeline rather than a fixed intent classifier or an ungrounded LLM. It combines semantic (embedding-based) search with keyword (BM25) search to find relevant passages, reranks them with a cross-encoder, and has an LLM generate an answer using only that retrieved context. Every answer's citations are validated against the sources actually retrieved before being shown to the user. Generations are traced via Langfuse for debugging and inspection.

This started as a general-purpose document Q&A bot and is being extended to index public King's College London web content (policies, course information), so students can ask plain-language questions and get a short, sourced answer. That extension is still in planning.

## Why RAG instead of intent classification or a bare LLM

An earlier version of this project used a TF-IDF classifier with a small, hand-written set of trained categories, falling back to an ungrounded LLM call for anything else. That approach works for narrow, repetitive queries but doesn't scale to open-ended questions about a specific body of knowledge - a classifier has no way to "know" facts, and an ungrounded LLM call has no way to guarantee its answer reflects a particular source rather than general training knowledge. RAG solves this by retrieving the most relevant chunks of a source at query time and instructing the model to answer only from that retrieved context.

## Guardrails

Because the eventual goal is answering real students' questions about university policy, the pipeline is built to fail safely rather than to always produce an answer:

- **Grounded only.** The model is instructed to answer solely from retrieved source text and to say so explicitly when it can't. Every citation the model produces (`[S1]`, `[S2]`, ...) is checked against the sources it was actually given; unrecognised citations are stripped, and an answer with no valid citation is discarded and replaced with a refusal message.
- **Relevance gate.** A cross-encoder reranker (FlashRank) scores each retrieved chunk against the query. If the best match scores below a threshold, the pipeline refuses before ever calling the LLM.
- **Prompt injection resistance.** User input is checked against common injection patterns before retrieval runs. Retrieved chunks are checked the same way before being inserted into the prompt, so instructions hidden in a source document can't override the system's behaviour. A random per-session canary string detects and blocks any answer that leaks part of the system prompt.
- **Degrades safely.** If the reranker or query rewriter fails to load or errors at runtime, the pipeline falls back to unranked retrieval or the original question rather than crashing.
- **Tested.** `tests/` covers the guardrails above (injection detection, citation validation, relevance gating, error handling) with fake LLMs and retrievers, so the suite runs without live API keys, and runs automatically on every push via CI. `eval/` separately measures answer quality against a golden set of known questions, using the real pipeline.

None of this is a substitute for a security review; it's the first layer.

## Architecture

```
data/                          -> source document(s) (not tracked in git)
src/
  config.py                     -> models, thresholds, and user-facing messages, in one place
  guards.py                     -> input cleaning, injection detection, prompt-leak detection
  chunking.py                   -> loads a .docx source and splits it into retrieval-sized chunks
  ingest.py                     -> defines embedding, vector store, and chunk persistence functions
  retriever.py                  -> hybrid retriever: semantic (embeddings) + BM25 (keyword)
  reranker.py                   -> cross-encoder reranking (FlashRank), with a no-op fallback
  rewriter.py                   -> rewrites follow-up questions into standalone queries using history
  citations.py                  -> builds numbered sources, validates the model's citations against them
  entities.py                   -> spaCy NER: extracts entities, boosts chunks that share one with the query
  rag_chain.py                  -> prompt template + full pipeline (rewrite -> retrieve -> rerank -> entity boost -> gate -> generate -> validate)
  dialogue_manager.py            -> the chatbot's response entrypoint, calls the RAG chain
  chatbot.py                    -> the interactive terminal loop
ingest.py                      -> root-level script: actually RUNS ingestion (see note below)
data/build_kings_docx.py       -> one-off script that generates a sample source .docx (not tracked)
app.py                         -> Streamlit chat UI
tests/                         -> pytest suite covering guards, citations, rewriting, reranking, entities, the pipeline
eval/                          -> golden-set evaluation: known questions + expected answers, graded against the real pipeline
.github/workflows/test.yml     -> CI: runs the test suite on every push
```

**Important structural note**: there are two files named `ingest.py`. The one at the repo root is a short script that calls the ingestion functions and produces `vector_store.json` / `chunks.json` - this is the one you run. `src/ingest.py` only defines those functions (`build_vector_store`, `load_vector_store`, `save_chunks`, `load_chunks`) and does nothing if run directly. This split exists so ingestion (expensive: real embedding API calls, run rarely) is cleanly separated from the reusable functions other modules import from.

## Pipeline

1. **Chunking** (`chunking.py`) - the source document is split using a recursive character splitter that prefers paragraph and sentence boundaries over hard character cuts, keeping chunks topically coherent.
2. **Embedding & indexing** (`ingest.py`, both copies) - each chunk is embedded and written to an in-memory vector store (no compiled native dependencies; see `report.md` for why this replaced an earlier Chroma-based setup). The chunk list is also persisted separately so retrieval doesn't need to re-parse the source document on every run.
3. **Query rewriting** (`rewriter.py`) - if there's prior conversation, the latest message is rewritten into a standalone question (e.g. "what about for postgraduates?" -> a full question) before retrieval. Skipped on the first message in a conversation.
4. **Hybrid retrieval** (`retriever.py`) - the (rewritten) query is matched two ways simultaneously: semantic similarity search over the embeddings, and BM25 keyword search over the persisted chunks. Results are combined via weighted reciprocal rank fusion (60% semantic / 40% keyword).
5. **Reranking** (`reranker.py`) - a cross-encoder reranks the combined candidates against the (rewritten) query.
6. **Entity boost** (`entities.py`) - named entities (places, organisations, people) are extracted from the query and compared against the entities each chunk was tagged with at ingest time. Chunks sharing an entity with the query get a small score bump before the final cut, so an exact match on something like "Guy's Campus" isn't lost purely because the surrounding wording differs. This only reorders candidates already in the pool; the relevance gate below still uses the reranker's original score, not the boosted one.
7. **Relevance gate** (`rag_chain.py`) - if the best remaining score is below a threshold, the pipeline refuses to answer rather than guessing.
8. **Grounded generation** (`rag_chain.py`) - the surviving chunks are inserted into a prompt that instructs the model to answer only from that context, cite each claim, and say so plainly when it doesn't have the relevant information.
9. **Citation validation** (`citations.py`) - every citation in the model's answer is checked against a real retrieved source. Unrecognised citations are stripped; an answer with none left is treated as ungrounded and replaced with a refusal.
10. **Tracing** (`rag_chain.py`) - generation calls are traced through Langfuse via a callback handler. Note: Langfuse's default LangChain integration typically captures the full prompt and completion, which includes the user's question - check a live trace in the Langfuse UI before relying on any particular privacy behaviour here.
11. **Response** (`dialogue_manager.py`, `chatbot.py`, `app.py`) - the caller gets back the answer plus the list of sources actually cited.

## Setup

```
uv sync
uv run python -m spacy download en_core_web_sm
```

Add to `.env` (repo root):
```
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=your_langfuse_host_key
```
Langfuse variables are optional; tracing is skipped if they're not set.

## Building the knowledge base

Place a source `.docx` in `data/` (not committed - project-specific and swappable), then, **from the repo root**:
```
uv run python ingest.py
```
This writes `vector_store.json` and `chunks.json` at the repo root. Re-run only when the source document changes.

## Running the chatbot

**Terminal:**
```
uv run python src/chatbot.py
```

**Web UI (Streamlit):**
```
uv run streamlit run app.py
```

## Testing

```
uv run pytest tests/
```
The suite uses fake LLMs and retrievers throughout, so it runs without live API keys and without network access. It runs automatically on every push via GitHub Actions (`.github/workflows/test.yml`).

## Evaluation

`eval/` holds a small golden set of known questions with their expected answers or sources, and a script that runs them against the real pipeline (real API calls) and reports a pass rate:
```
uv run python eval/run_eval.py
```
Unlike `tests/`, this needs real API keys and an ingested knowledge base - it's for judging answer quality after a change (a new prompt, a different threshold, a new reranker model), not for CI. Edit `eval/golden_set.json` to match whatever source document is currently indexed.

## Status

This is a personal/university project, currently a working pipeline over sample data. No King's College London web content has been collected, crawled, or indexed. Extending it to King's public pages is planned but pending approval from King's IT and web teams; see `report.md` for background on the design decisions so far.
