import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ─────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ── LLM Provider ─────────────────────────────────────────────────
# Set to "gemini" or "openai". Defaults to "gemini" (free tier).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# ── Paths ────────────────────────────────────────────────────────
VECTOR_STORE_PATH = os.path.join("data", "vector_store")
POLICIES_DIR = os.path.join("data", "policies")

# ── Chunking ─────────────────────────────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ── RAG ──────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHAT_MODEL_OPENAI = "gpt-3.5-turbo"
CHAT_MODEL_GEMINI = "gemini-2.0-flash"
RETRIEVER_K = 4
