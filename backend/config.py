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
NVIDIA_MODEL = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")  # llama-3.3-70b-instruct is EOL (410)

# Backward compatibility mapping
MODEL_NAME = NVIDIA_MODEL
API_KEY = NVIDIA_API_KEY
BASE_URL = NVIDIA_BASE_URL

# Gemini parameters
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# gemini-2.0-flash and gemini-2.5-flash are retired / closed to new users (HTTP 404 as of 2026-09-27);
# gemini-3.8-flash was confirmed via ListModels and a live generation call.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "1500"))
# Secondary LLM when the primary (Groq) fails: "gemini" or "none". The old NVIDIA fallback model reached
# end-of-life (HTTP 410) and is no longer used.
LLM_FALLBACK_PROVIDER = os.environ.get("LLM_FALLBACK_PROVIDER", "nvidia,gemini")
# NVIDIA Nemotron 3 (open model) — verified live 2026-09-30: nemotron-3-super-120b-a12b ~0.6s first token.
# nemotron-3.5-lightning-30b-a3b timed out (no response in 120s) on both keys at that time.
NVIDIA_ENABLE_THINKING = os.environ.get("NVIDIA_ENABLE_THINKING", "false")
NVIDIA_READ_TIMEOUT_S = float(os.environ.get("NVIDIA_READ_TIMEOUT_S", "60"))
# A provider that hasn't started answering within this many seconds is abandoned for the fallback
LLM_FIRST_TOKEN_TIMEOUT_S = float(os.environ.get("LLM_FIRST_TOKEN_TIMEOUT_S", "8"))
LLM_REQUEST_TIMEOUT_S = float(os.environ.get("LLM_REQUEST_TIMEOUT_S", "15"))
GROQ_RATE_LIMIT_COOLDOWN_S = float(os.environ.get("GROQ_RATE_LIMIT_COOLDOWN_S", "20"))
# Hard ceiling for answer generation; past it the verified evidence is served instead
GENERATION_DEADLINE_S = float(os.environ.get("GENERATION_DEADLINE_S", "25"))
# Groq parameters
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

# MODEL_NAME must follow the active provider; previously it was always the NVIDIA model,
# so Groq/Gemini calls passing config.MODEL_NAME requested a model the provider doesn't serve.
_PROVIDER_MODELS = {"nvidia": NVIDIA_MODEL, "groq": GROQ_MODEL, "gemini": GEMINI_MODEL}
MODEL_NAME = _PROVIDER_MODELS.get(LLM_PROVIDER.lower(), NVIDIA_MODEL)

# Query-understanding LLM adjudication (only invoked for genuinely ambiguous interpretations)
SEMANTIC_LLM_ADJUDICATION = os.environ.get("SEMANTIC_LLM_ADJUDICATION", "true").lower() in ("true", "1", "yes")
SEMANTIC_LLM_TIMEOUT_S = float(os.environ.get("SEMANTIC_LLM_TIMEOUT_S", "8"))
# Aspect is adjudicated by the LLM only when its evidence-based confidence or top-2 margin is below these
# (fitted on dev with evaluation/aspect_threshold_sweep.py: 93.2% -> 97.3% aspect accuracy at an 8% LLM call rate)
SEMANTIC_ASPECT_ACCEPT_CONFIDENCE = float(os.environ.get("SEMANTIC_ASPECT_ACCEPT_CONFIDENCE", "0.4"))
SEMANTIC_ASPECT_ACCEPT_MARGIN = float(os.environ.get("SEMANTIC_ASPECT_ACCEPT_MARGIN", "0.2"))
SEMANTIC_ASPECT_AMBIGUITY_MAX_CONFIDENCE = float(os.environ.get("SEMANTIC_ASPECT_AMBIGUITY_MAX_CONFIDENCE", "0.75"))


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

# Security / abuse limits
# Admin, debug and tenant-onboarding APIs require this token in the X-Admin-Token header.
# In production they are disabled entirely until it is set.
ADMIN_API_TOKEN = os.environ.get("ADMIN_API_TOKEN", "")
CHAT_RATE_LIMIT_PER_SESSION_PER_MIN = int(os.environ.get("CHAT_RATE_LIMIT_PER_SESSION_PER_MIN", "20"))
CHAT_RATE_LIMIT_PER_IP_PER_MIN = int(os.environ.get("CHAT_RATE_LIMIT_PER_IP_PER_MIN", "60"))
CHAT_MAX_MESSAGE_CHARS = int(os.environ.get("CHAT_MAX_MESSAGE_CHARS", "2000"))
# Conversation memory (SQLite): survives restarts and is shared by workers on the same host
CHAT_MEMORY_DB_PATH = os.environ.get("CHAT_MEMORY_DB_PATH", "")
CHAT_MEMORY_TTL_DAYS = float(os.environ.get("CHAT_MEMORY_TTL_DAYS", "30"))
DECISION_CONCURRENCY = int(os.environ.get("DECISION_CONCURRENCY", "8"))
DEBUG = os.environ.get("DEBUG", "true").lower() in ("true", "1", "yes")

# Feature flags
USE_NEW_ENTITY_RESOLVER = os.environ.get("USE_NEW_ENTITY_RESOLVER", "true").lower() in ("true", "1", "yes")


# Meeting / contact-request agent: outgoing email (Gmail: smtp.gmail.com, port 587, an App Password — not the
# account password). Without SMTP credentials requests are still saved (meeting_requests table) but no email is sent.
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
SMTP_TIMEOUT_S = float(os.environ.get("SMTP_TIMEOUT_S", "15"))
MAIL_FROM = os.environ.get("MAIL_FROM", "")            # defaults to SMTP_USERNAME
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")    # HTTPS email API — use where SMTP is blocked (e.g. Railway)
MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "CittaAI")
COMPANY_LEAD_EMAIL = os.environ.get("COMPANY_LEAD_EMAIL", "")   # where new meeting requests are sent
MEETING_REQUESTS_PER_SESSION = int(os.environ.get("MEETING_REQUESTS_PER_SESSION", "3"))
