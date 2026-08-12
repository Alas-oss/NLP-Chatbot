# NLP Chatbot - Retrieval-Augmented Generation

A chatbot that answers questions grounded in a specific source document, using a retrieval-augmented generation (RAG) pipeline rather than a fixed intent classifier or an ungrounded LLM. It combines semantic (embedding-based) search with keyword (BM25) search to find relevant passages, then has an LLM generate an answer using only that retrieved context. Every generation is traced via Langfuse for debugging and inspection.

## Reasons for RAG instead of intent classification or a bare LLM

An earlier version of this project used a TF-IDF classifier with a small, hand-written set of trained categories, falling back to an ungrounded LLM call for anything else (retrained under `archive/` for reference). That approach works for narrow, repetitive queries but doesn't scale to open-ended questions about a specific body of knowledge - a classifier has no way to "know" facts, and an ungrounded LLM call has no way to guarantee its answer reflects a particular source document rather than general training knowledge. RAG solves this by retrieving the most relevant chunks of a source document at query time and explicitly instructing the model to answer only from that retrieved context.

## Architecture
 
```
data/                         -> source document(s) (not tracked in git)
archive/                      -> retired intent-classifier implementation, kept for reference
src/
  chunking.py                  -> loads a .docx source and splits it into retrieval-sized chunks
  ingest.py                    -> defines embedding, vector store, and chunk persistence functions
  retriever.py                 -> hybrid retriever: semantic (embeddings) + BM25 (keyword)
  rag_chain.py                 -> prompt template + retrieval + LLM generation + Langfuse tracing
  dialogue_manager.py          -> the chatbot's response entrypoint, calls the RAG chain
  entity_extractor.py          -> spaCy NER, run alongside retrieval for extra structure
  chatbot.py                   -> the interactive terminal loop
ingest.py                     -> root-level script: actually RUNS ingestion (see note below)
build_kings_docx.py           -> one-off script that generates the source .docx (not tracked)
```

**Important structural note**: there are two files named `ingest.py`. The one at the repo root is a short script that calls the ingestion functions and produces `vector_store.json`/`chunks.json` -- this is the one you run. `src/ingest.py` only defines those functoins (`build_vector_store`, `load_vector_store`, `save_chunks`, `load_chunks`) and does nothing if run directly. This split exists so ingestion (expensive: real embedding API calls, run rarely) is cleanly separated from the reusable functions other modules import from.

## Pipeline

1. **Chunking** (`chunking.py`) -- the source document is split using a recursive character splitter that prefers paragraph and sentence boundaries over hard character cuts, keeping chunks topically coherent.
2. **Embedding & indexing** (`ingest.py`, both copies of this file) -- each chunk is embedded via store (no compiled native dependencies -- written in Resolved Issues below for the reasons). The chunk list is also persisted separately so retrieval doesn't need to re-parse the source document on evey run.
3. **Hybrid retrieval* (`retrieval.py`) -- a query is matched two ways simultaneously: semantic similarity search over the embeddings, and BM25 keyword search over the persisted chunks. Results are combined via resiprocal rank fusion, weighted 60% semantic / 40% keyword.
4. **Grounded generation** (`rag_chain.py`) -- retrieved chunks are inserted into a prompt that explicitly instructs the model to answer only from the context, and to say so plainly when it doesn't have the relevant information.
5. **Tracing** (`rag_chain.py`) -- every generation call is traced through Langfuse via a callback handler, recording retrieval counts and query length without transmitting the raw question text as searchable metadata.
6. **Response** (`dialogue_manager.py`, `chatbot.py`) -- the chatbot loop calls the RAG chain, prints the grounded answer, and runs a lightweight NER pass on the user's query for supplementary structure.

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

## Building the knowledge base

Place a source `.docx` in `data/` (not committed -- project-specific and sqappable), then, **from the repo root**:
```
uv run python ingest.py
```
Thie writes `vector_store.json` and `chunks.json` at the repo root. Re-run only when the source document changes.

## Running the chatbot

**From the repo root:**
```
uv run python src/chatbot.py
```

## Testing

```
uv run pytest tests/
```
