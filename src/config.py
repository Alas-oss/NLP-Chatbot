import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "groq:openai/gpt-oss-120b"

EMBEDDING_MODEL = "gemini-embedding-001"
CHAT_MODEL = "groq:openai/gpt-oss-120b"
# Query rewriting is a tiny task; point this at a smaller/faster model if you like.
REWRITE_MODEL = os.getenv("REWRITE_MODEL", CHAT_MODEL)

VECTOR_STORE_PATH = "vector_store.json"
CHUNKS_PATH = "chunks.json"
DATA_DIR = "data"

INSTITUTION = "King's College London"

# --- Retrieval -------------------------------------------------------------
RETRIEVAL_K = 20          # candidates fetched by EACH retriever (semantic + BM25)
SEMANTIC_WEIGHT = 0.6
BM25_WEIGHT = 0.4

# --- Reranking -------------------------------------------------------------
RERANK_TOP_N = 5          # chunks that actually reach the LLM
RERANKER = os.getenv("RERANKER", "flashrank")   # "flashrank" | "none"
RERANK_MODEL = "ms-marco-MiniLM-L-12-v2"        # FlashRank ONNX model (no torch)
# Cross-encoder scores are 0-1. If the best chunk scores below this, we refuse
# without calling the LLM. PLACEHOLDER: tune it against the golden question set.
MIN_RELEVANCE = float(os.getenv("MIN_RELEVANCE", "0.02"))

# --- Conversation ----------------------------------------------------------
HISTORY_TURNS = 4         # previous user/assistant exchanges used to rewrite follow-ups
MAX_QUESTION_CHARS = 1000
MAX_REWRITE_CHARS = 300

# --- Chunking --------------------------------------------------------------
CHUNK_SIZE = 600
CHUNK_OVERLAP = 80

# --- User-facing messages --------------------------------------------------
REFUSAL_MESSAGE = (
    "I couldn't find that in the information I have access to. "
    f"Please check the official {INSTITUTION} website or contact the relevant university team."
)
BLOCKED_MESSAGE = (
    f"I can only help with questions about {INSTITUTION}. "
    "Could you rephrase your question?"
)
ERROR_MESSAGE = "Sorry, something went wrong on my side. Please try again in a moment."
