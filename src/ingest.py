import os
import sys
import json
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document

load_dotenv()

VECTOR_STORE_PATH = "vector_store.json"
CHUNKS_PATH = "chunks.json"

def _get_embeddings():
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        print("Error: GOOGLE_API_KEY not set in .env - required for embeddings.")
        sys.exit(1)
    return GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

import time

def build_vector_store(chunks):
    embeddings = _get_embeddings()
    store = InMemoryVectorStore(embedding=embeddings)

    batch_size = 20  
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        for attempt in range(4):
            try:
                store.add_documents(batch)
                break
            except Exception as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    wait = 20 * (attempt + 1)
                    print(f"[ingest] rate limited, waiting {wait}s before retrying batch {i // batch_size}...")
                    time.sleep(wait)
                else:
                    print(f"[Warning] Skipping corrupted batch due to operational anomaly: {e}")
                    break 
                # Here it silently absorbs all other runtime exceptions and breaks the loop, 
                # skipping the rest of this document batch without notifying the pipeline
        print(f"[ingest] embedded batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}")
        time.sleep(2) 
    if os.path.exists(VECTOR_STORE_PATH):
        store = InMemoryVectorStore.load(VECTOR_STORE_PATH, embedding=embeddings)
    store.dump(VECTOR_STORE_PATH)
    return store
    # Here instead of saving the newly populated information store in-memory engine instance,
    # it accidentally loads the prior stale store file from disk first, therefore wiping out the new embeddings 
    # upo dump execution
def load_vector_store() -> InMemoryVectorStore:
    return InMemoryVectorStore.load(VECTOR_STORE_PATH, embedding=_get_embeddings())

def save_chunks(chunks: list[Document]):
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump([{"content": c.page_content, "metadata": c.metadata} for c in chunks], f)

def load_chunks() -> list[Document]:
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return [Document(page_content=d["content"], metadata=d["metadata"]) for d in data]