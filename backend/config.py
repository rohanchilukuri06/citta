import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / '.env')

# Centralized settings
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "nvidia")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_MODEL = os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

# Backward compatibility mapping
MODEL_NAME = NVIDIA_MODEL
API_KEY = NVIDIA_API_KEY
BASE_URL = NVIDIA_BASE_URL

# Gemini parameters
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "350"))
# Groq parameters
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


# Generation parameters
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.4"))
TOP_P = float(os.environ.get("TOP_P", "0.7"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1024"))
STREAM = os.environ.get("STREAM", "true").lower() in ("true", "1", "yes")
TIMEOUT = int(os.environ.get("TIMEOUT", "60"))

# Retrieval settings
TOP_K = int(os.environ.get("TOP_K", "5"))
RERANK_TOP_K = int(os.environ.get("RERANK_TOP_K", "3"))
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.45"))

# Embedding parameters
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")

# Paths with deterministic database discovery fallback
_target_vector_path = os.path.abspath(os.path.join(ROOT_DIR, os.environ.get("VECTOR_DB_PATH", "vector_store.db")))
_root_vector_path = os.path.abspath(os.path.join(ROOT_DIR, "vector_store.db"))

if not os.path.exists(_target_vector_path) and os.path.exists(_root_vector_path):
    VECTOR_DB_PATH = _root_vector_path
else:
    VECTOR_DB_PATH = _target_vector_path
SQLITE_DB_PATH = os.path.abspath(os.path.join(ROOT_DIR, os.environ.get("SQLITE_DB_PATH", "analytics.db")))

# Environment flags
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
DEBUG = os.environ.get("DEBUG", "true").lower() in ("true", "1", "yes")

# Feature flags
USE_NEW_ENTITY_RESOLVER = os.environ.get("USE_NEW_ENTITY_RESOLVER", "true").lower() in ("true", "1", "yes")

