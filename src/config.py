import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "groq:openai/gpt-oss-120b"

EMBEDDING_MODEL = "gemini-embedding-001"
CHAT_MODEL = "groq:openai/gpt-oss-120b"
REWRITE_MODEL = os.getenv("REWRITE_MODEL", CHAT_MODEL)

VECTOR_STORE_PATH = "vector_store.json"
CHUNKS_PATH = "chunks.json"
DATA_DIR = "data"

INSTITUTION = "King's College London"

RETRIEVAL_K = 20         
SEMANTIC_WEIGHT = 0.6
BM25_WEIGHT = 0.4

RERANK_TOP_N = 5         
RERANKER = os.getenv("RERANKER", "flashrank")  
RERANK_MODEL = "ms-marco-MiniLM-L-12-v2"       
MIN_RELEVANCE = float(os.getenv("MIN_RELEVANCE", "0.02"))

HISTORY_TURNS = 4       
MAX_QUESTION_CHARS = 1000
MAX_REWRITE_CHARS = 300

CHUNK_SIZE = 600
CHUNK_OVERLAP = 80

REFUSAL_MESSAGE = (
    "I couldn't find that in the information I have access to. "
    f"Please check the official {INSTITUTION} website or contact the relevant university team."
)
BLOCKED_MESSAGE = (
    f"I can only help with questions about {INSTITUTION}. "
    "Could you rephrase your question?"
)
ERROR_MESSAGE = "Sorry, something went wrong on my side. Please try again in a moment."
