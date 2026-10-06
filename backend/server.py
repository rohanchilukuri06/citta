import os
import sys

# Ensure both workspace root and backend directory are in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import json
import logging
logger = logging.getLogger(__name__)
import uuid
import time
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks, Request
from api_security import require_admin
from fastapi.responses import StreamingResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict

import pypdf
import docx2txt

# Import RAG files safely
import llm_provider
import vector_store
import rag_service
from intent_router import classify_intent, normalize_query
import config

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'cittaai')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Setup FastAPI App
app = FastAPI(title="CittaAI Backend", version="1.0.0")

# Startup Runtime Database Diagnostic Logging
vdb_path = getattr(config, "VECTOR_DB_PATH", vector_store.DB_PATH)
vdb_abs = os.path.abspath(vdb_path)
vdb_exists = os.path.exists(vdb_abs)
vdb_size = os.path.getsize(vdb_abs) if vdb_exists else 0

logging.info(f"=== VECTOR DATABASE RUNTIME DIAGNOSTIC ===")
logging.info(f"Target DB Path (Config): {vdb_path}")
logging.info(f"Absolute DB Path: {vdb_abs}")
logging.info(f"File Exists: {vdb_exists}")
logging.info(f"File Size: {vdb_size} bytes")
if vdb_exists:
    tmp_store = vector_store.VectorStore(vdb_abs)
    logging.info(f"Runtime DB Chunk Count: {tmp_store.get_chunk_count()}")
    logging.info(f"Runtime DB Metadata: {tmp_store.get_metadata()}")
logging.info(f"==========================================")

async def prewarm_rag_embedding_model():
    t_start = time.perf_counter()
    logger.info("=== PRE-WARMING BGE EMBEDDING MODEL & RAG SERVICE ===")
    try:
        rag_serv = get_rag_service()
        await rag_serv.get_embedding_model()
        # Load the semantic pipeline (entity index, registry, memory store) before the first visitor arrives
        from semantic_chat_pipeline import get_semantic_chat_pipeline, ConversationState
        pipeline = get_semantic_chat_pipeline(provider=rag_serv.provider)
        await asyncio.to_thread(pipeline.decide, "What solutions does CittaAI offer?", ConversationState())
        purged = pipeline.memory.purge_expired() if pipeline.memory else 0
        logger.info(f"=== SEMANTIC PIPELINE WARM (expired conversations purged: {purged}) ===")
        t_end = time.perf_counter()
        duration_ms = round((t_end - t_start) * 1000.0, 2)
        logger.info(f"=== EMBEDDING MODEL PRE-WARM COMPLETE: {duration_ms} ms ===")
    except Exception as e:
        logger.error(f"Failed to pre-warm embedding model on startup: {e}")

@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def root_health_check():
    return {"status": "healthy"}


# Production & Local CORS Middleware Configuration
cors_env = os.environ.get('CORS_ORIGINS', '').strip()
default_origins = [
    "https://cittaai.com",
    "https://www.cittaai.com",
    "https://citta-omega.vercel.app",
    "https://citta-ten-sable.vercel.app",
    "https://citta-jbi1az638-rohanchilukuri06-8472s-projects.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000"
]

if cors_env and cors_env != "*":
    env_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    allowed_origins = list(dict.fromkeys(default_origins + env_origins))
else:
    allowed_origins = default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Only this project's Vercel preview deployments (previously any *.vercel.app site, with credentials)
    allow_origin_regex=r"https://citta-[a-z0-9]+-rohanchilukuri06-8472s-projects\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(f"Unhandled Exception on {request.url.path}: {exc}")
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": origin if origin else "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )


api_router = APIRouter(prefix="/api")

# Configuration and state paths
CONTENT_JS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "data", "content.js"))
ANALYTICS_DB_PATH = config.SQLITE_DB_PATH

# Initialize Analytics and Config Database (SQLite)
def init_analytics_db():
    conn = sqlite3.connect(ANALYTICS_DB_PATH)
    cursor = conn.cursor()
    # Table for chat queries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            intent TEXT NOT NULL,
            score REAL NOT NULL,
            latency REAL NOT NULL,
            redirect TEXT
        )
    """)
    
    # Table for feedback loop logging
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_events (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            query TEXT,
            response TEXT,
            details TEXT
        )
    """)
    
    # 1. Query Analytics Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_analytics (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            original_query TEXT NOT NULL,
            normalized_query TEXT NOT NULL,
            spell_corrections TEXT NOT NULL
        )
    """)
    
    # 2. Routing Analytics Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS routing_analytics (
            id TEXT PRIMARY KEY,
            query_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            resolved_registry TEXT,
            resolved_entity TEXT,
            resolved_section TEXT,
            intent TEXT,
            confidence REAL,
            source TEXT,
            routing_path TEXT,
            explainability TEXT,
            FOREIGN KEY(query_id) REFERENCES query_analytics(id)
        )
    """)
    
    # 3. Performance Analytics Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_analytics (
            id TEXT PRIMARY KEY,
            query_id TEXT NOT NULL,
            latency_ms REAL,
            normalizer_ms REAL,
            resolver_ms REAL,
            router_ms REAL,
            builder_ms REAL,
            rag_ms REAL,
            cache_hit INTEGER,
            FOREIGN KEY(query_id) REFERENCES query_analytics(id)
        )
    """)
    
    # Check current table columns to alter if necessary (self-healing migration)
    cursor.execute("PRAGMA table_info(queries)")
    columns = [row[1] for row in cursor.fetchall()]
    new_cols = {
        "intent_time": "REAL",
        "cache_hit": "INTEGER",
        "cache_time": "REAL",
        "embedding_time": "REAL",
        "retrieval_time": "REAL",
        "llm_time": "REAL",
        "streaming_time": "REAL",
        "total_time": "REAL",
        "prompt_tokens": "INTEGER",
        "completion_tokens": "INTEGER",
        "provider": "TEXT",
        "model": "TEXT",
        "embedding_model": "TEXT",
        "estimated_cost": "REAL",
        "semantic_score": "REAL",
        "bm25_score": "REAL",
        "cross_encoder_score": "REAL",
        "confidence": "REAL",
        "decision_case": "TEXT",
        "top_retrieved_doc": "TEXT",
        "top_retrieved_url": "TEXT",
        "embedding_latency": "REAL",
        "reranking_latency": "REAL",
        "llm_latency": "REAL",
        "total_latency": "REAL"
    }
    for col, col_type in new_cols.items():
        if col not in columns:
            cursor.execute(f"ALTER TABLE queries ADD COLUMN {col} {col_type}")

    # Table for general configurations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    # Migration helper: update config if transitioning from Ollama to Nvidia
    cursor.execute("UPDATE config SET value = ? WHERE key = 'llm_provider'", (config.LLM_PROVIDER,))
    cursor.execute("UPDATE config SET value = ? WHERE key = 'llm_model'", (config.GROQ_MODEL,))

    # Insert default config keys if missing
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('llm_provider', ?)", (config.LLM_PROVIDER,))
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('llm_model', ?)", (config.MODEL_NAME,))
    conn.commit()
    conn.close()

init_analytics_db()

# Helper to get configuration
def get_config(key: str, default: str = "") -> str:
    try:
        conn = sqlite3.connect(ANALYTICS_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default
    except Exception:
        return default

def set_config(key: str, value: str):
    conn = sqlite3.connect(ANALYTICS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# Initialize core RAG instances
vstore = vector_store.VectorStore()

_rag_service_instance = None

def get_rag_service() -> rag_service.RAGService:
    global _rag_service_instance
    if _rag_service_instance is None:
        provider_name = os.environ.get("LLM_PROVIDER", getattr(config, "LLM_PROVIDER", "groq"))
        
        config_dict = {
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", config.API_KEY),
            "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
            "GROQ_API_KEY": os.environ.get("GROQ_API_KEY", ""),
            "CLAUDE_API_KEY": os.environ.get("CLAUDE_API_KEY", "")
        }
        provider_inst = llm_provider.get_llm_provider(provider_name, config_dict)
        _rag_service_instance = rag_service.RAGService(provider=provider_inst, vector_store=vstore)
    return _rag_service_instance


# ---------------- API MODELS ----------------
class ChatMessageInput(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=config.CHAT_MAX_MESSAGE_CHARS)

class ConfigUpdateInput(BaseModel):
    provider: str
    model: str
    ollama_base_url: Optional[str] = None

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


# ---------------- UTILITY: PARSE FILES ----------------
def extract_pdf_text(file_bytes: bytes) -> str:
    from io import BytesIO
    pdf = pypdf.PdfReader(BytesIO(file_bytes))
    text = ""
    for page in pdf.pages:
        val = page.extract_text()
        if val:
            text += val + "\n"
    return text

def extract_docx_text(file_bytes: bytes) -> str:
    from io import BytesIO
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp:
        temp.write(file_bytes)
        temp_path = temp.name
    try:
        text = docx2txt.process(temp_path)
    finally:
        os.unlink(temp_path)
    return text


# ---------------- INGESTION CORE FUNCTION ----------------
async def perform_reindex():
    """Extracts website chunks from content.js, generates embeddings, and indexes them."""
    logging.info("Starting website content re-indexing...")
    try:
        from vector_indexer import build_vector_database
        return await build_vector_database(force=True)
    except Exception:
        logging.exception("Error during perform_reindex")
        return False


# ---------------- AUTO RE-INDEXING BACKGROUND WATCHER ----------------
content_js_mtime = 0.0

async def watch_content_js_changes():
    """Poll content.js for modifications and trigger auto re-indexing."""
    global content_js_mtime
    await asyncio.sleep(5) # Wait for startup to complete
    
    if os.path.exists(CONTENT_JS_PATH):
        content_js_mtime = os.path.getmtime(CONTENT_JS_PATH)
        logging.info(f"Auto-watcher initialized on content.js. Current mtime: {content_js_mtime}")
    
    while True:
        try:
            await asyncio.sleep(10)
            if os.path.exists(CONTENT_JS_PATH):
                current_mtime = os.path.getmtime(CONTENT_JS_PATH)
                if current_mtime > content_js_mtime:
                    logging.info("content.js modification detected! Triggering auto-reindexing...")
                    success = await perform_reindex()
                    if success:
                        content_js_mtime = current_mtime
                        logging.info("Auto-reindexing succeeded.")
        except Exception:
            logging.exception("Error in watch_content_js_changes loop")


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # 1. Validate vector database integrity on startup (Zero AI model loading)
    val = vstore.validate_database_integrity()
    if not val.get("valid"):
        logging.warning(f"Vector database warning: {val.get('reason')}. Please run scripts/build_vector_db.py before deployment.")
    else:
        count = val.get("count", 0)
        logging.info(f"Vector database active with {count} chunks. DB Version: {val.get('metadata', {}).get('version', '1.0.0')}")

    # 1b. Stale-index detection: warn loudly in development, block chat in production until rebuilt
    try:
        from index_integrity import refresh_status
        app.state.index_integrity = refresh_status()
    except Exception as e:
        logging.critical(f"Vector index integrity check could not run: {e}")

    # Initialize and validate Knowledge Registry startup consistency checks
    try:
        from knowledge_registry import get_registry
        registry = get_registry()
        logging.info("Registry startup consistency validation checks and diagnostics PASSED successfully.")
    except Exception as e:
        logging.critical(f"FATAL: Registry startup validation failed: {e}")
        raise e

    # 2. Launch background auto-reindexing watcher ONLY in development
    watcher_task = None
    if getattr(config, "ENVIRONMENT", "production").lower() == "development":
        logging.info("Development environment detected: starting content.js filesystem watcher.")
        watcher_task = asyncio.create_task(watch_content_js_changes())
    else:
        logging.info("Production environment detected: filesystem watcher disabled.")

    # 3. Warm the embedding model + semantic pipeline in the background (health checks stay responsive)
    warm_task = asyncio.create_task(prewarm_rag_embedding_model())

    yield

    warm_task.cancel()
    
    # Shutdown tasks
    if watcher_task:
        watcher_task.cancel()
    client.close()

app.router.lifespan_context = lifespan


# ---------------- API ROUTES ----------------

@api_router.get("/")
async def root() -> Dict[str, str]:
    return {"message": "CittaAI API Server is operational"}

async def run_chat_background_tasks(
    session_id: str,
    query: str,
    response: str,
    normalized_q: str,
    citations: List[str],
    suggested_qs: List[str],
    redirect: Optional[str],
    section: Optional[str],
    highlight: bool,
    metrics: Dict[str, Any],
    model: str,
    start_time: float
):
    """Executes post-response pipelines (preferences, summary, caching, analytics) in the background."""
    rag_serv = get_rag_service()
    
    # 1. Update Cache
    try:
        rag_serv.cache.set(normalized_q, {
            "text": response,
            "citations": citations,
            "suggested_questions": suggested_qs,
            "redirect": redirect,
            "section": section,
            "highlight": highlight
        })
    except Exception:
        logging.exception("Failed to update cache in background")
        
    # 2. Extract Preferences
    try:
        await rag_serv.extract_preferences(query, response, session_id, model)
    except Exception:
        logging.exception("Failed to extract preferences in background")

    # 3. Generate Summary if memory gets large
    try:
        await rag_serv.generate_summary(session_id, model)
    except Exception:
        logging.exception("Failed to update conversation summary in background")

        # 4. Write SQLite Analytics
        try:
            latency = time.time() - start_time
            conn = sqlite3.connect(ANALYTICS_DB_PATH)
            cursor = conn.cursor()
            query_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Calculate similarity score placeholder for logging
            score = 0.8
            if citations:
                score = 0.95
            elif "couldn't find verified information" in response:
                score = 0.3
                
            intent = classify_intent(query)
            
            # Estimate cost (approx $0.15 per million tokens for llama-3.1-70b-instruct)
            prompt_t = metrics.get("prompt_tokens", 0)
            completion_t = metrics.get("completion_tokens", 0)
            est_cost = 0.0
            if "70b" in model.lower():
                est_cost = ((prompt_t * 0.15) + (completion_t * 0.15)) / 1000000.0
            elif "8b" in model.lower():
                est_cost = ((prompt_t * 0.05) + (completion_t * 0.05)) / 1000000.0
                
            provider_name = get_config("llm_provider", config.LLM_PROVIDER)
            emb_model = config.EMBEDDING_MODEL

            # Get dynamic retrieval scores from metrics
            sem_score = metrics.get("semantic_score", 0.0)
            bm25_score = metrics.get("bm25_score", 0.0)
            cross_score = metrics.get("cross_encoder_score", 0.0)
            confidence = metrics.get("confidence", 0.0)
            decision_case = metrics.get("decision_case", "CASE_3")
            top_doc = metrics.get("top_doc")
            top_url = metrics.get("top_url")
            emb_latency = metrics.get("embedding_time", 0.0)
            rerank_latency = metrics.get("retrieval_time", 0.0)
            llm_latency = metrics.get("llm_time", 0.0)
            total_latency = metrics.get("total_time", latency)

            cursor.execute("""
                INSERT INTO queries (
                    id, timestamp, session_id, query, response, intent, score, latency, redirect,
                    intent_time, cache_hit, cache_time, embedding_time, retrieval_time, llm_time,
                    streaming_time, total_time, prompt_tokens, completion_tokens,
                    provider, model, embedding_model, estimated_cost,
                    semantic_score, bm25_score, cross_encoder_score, confidence, decision_case,
                    top_retrieved_doc, top_retrieved_url, embedding_latency, reranking_latency, llm_latency, total_latency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_id, timestamp, session_id, query, response, intent, confidence,
                total_latency, redirect,
                metrics.get("intent_time", 0.0), metrics.get("cache_hit", 0), metrics.get("cache_time", 0.0),
                metrics.get("embedding_time", 0.0), metrics.get("retrieval_time", 0.0), metrics.get("llm_time", 0.0),
                metrics.get("streaming_time", 0.0), metrics.get("total_time", 0.0),
                metrics.get("prompt_tokens", 0), metrics.get("completion_tokens", 0),
                provider_name, model, emb_model, est_cost,
                sem_score, bm25_score, cross_score, confidence, decision_case,
                top_doc, top_url, emb_latency, rerank_latency, llm_latency, total_latency
            ))

            # New metrics logging
            norm_q = metrics.get("normalized_query", normalized_q)
            spell_corrs = metrics.get("spell_corrections", "[]")
            res_reg = metrics.get("resolved_registry")
            res_ent = metrics.get("resolved_entity")
            res_sec = metrics.get("resolved_section")
            rt_path = metrics.get("routing_path", "unknown")
            source_val = metrics.get("source", "unknown")
            expl = metrics.get("explainability", "{}")
            
            norm_ms = metrics.get("normalizer_ms", 0.0)
            res_ms = metrics.get("resolver_ms", 0.0)
            rout_ms = metrics.get("router_ms", 0.0)
            build_ms = metrics.get("builder_ms", 0.0)
            r_ms = metrics.get("rag_ms", 0.0)
            cache_h = metrics.get("cache_hit", 0)

            # Log into query_analytics
            cursor.execute("""
                INSERT INTO query_analytics (
                    id, timestamp, session_id, original_query, normalized_query, spell_corrections
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (query_id, timestamp, session_id, query, norm_q, spell_corrs))

            # Log into routing_analytics
            cursor.execute("""
                INSERT INTO routing_analytics (
                    id, query_id, session_id, resolved_registry, resolved_entity, resolved_section,
                    intent, confidence, source, routing_path, explainability
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), query_id, session_id, res_reg, res_ent, res_sec,
                intent, confidence, source_val, rt_path, expl
            ))

            # Log into performance_analytics
            cursor.execute("""
                INSERT INTO performance_analytics (
                    id, query_id, latency_ms, normalizer_ms, resolver_ms, router_ms, builder_ms, rag_ms, cache_hit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), query_id, total_latency * 1000.0, norm_ms, res_ms, rout_ms, build_ms, r_ms, cache_h
            ))

            conn.commit()
            conn.close()
        except Exception:
            logging.exception("Failed to log analytics in background")


class TenantOnboardInput(BaseModel):
    name: str
    website_url: str
    logo_url: Optional[str] = ""
    brand_settings: Optional[Dict[str, Any]] = None

@api_router.post("/tenants/onboard", dependencies=[Depends(require_admin)])
async def onboard_tenant_endpoint(data: TenantOnboardInput):
    """Onboard a new company tenant simply by providing name and website URL."""
    try:
        from knowledge_source_manager import get_ingestion_engine
        engine = get_ingestion_engine()
        res = engine.onboard_tenant(
            name=data.name,
            website_url=data.website_url,
            logo_url=data.logo_url or "",
            brand_settings=data.brand_settings
        )
        return {"success": True, "tenant": res}
    except Exception as e:
        logger.error(f"Error onboarding tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class FeedbackInput(BaseModel):
    session_id: str
    event_type: str
    query: Optional[str] = None
    response: Optional[str] = None
    details: Optional[str] = None

@api_router.post("/analytics/feedback")
async def log_feedback_endpoint(data: FeedbackInput):
    """Log feedback indicators (thumbs up/down, regeneration, CTA link clicked, abandonment)."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB_PATH)
        cursor = conn.cursor()
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO feedback_events (id, timestamp, session_id, event_type, query, response, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, timestamp, data.session_id, data.event_type, data.query, data.response, data.details
        ))
        conn.commit()
        conn.close()
        return {"status": "success", "event_id": event_id}
    except Exception as e:
        logger.error(f"Failed to log feedback: {e}")
        raise HTTPException(status_code=500, detail="Database insertion error")

class ContactFormInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    email: str = Field(..., min_length=5, max_length=120)
    phone: str = Field(..., min_length=7, max_length=20)
    company: Optional[str] = Field(default="", max_length=120)
    inquiry: str = Field(..., min_length=1, max_length=60)
    message: str = Field(..., min_length=2, max_length=2000)
    timing: Optional[str] = Field(default="", max_length=200)


@api_router.post("/contact")
async def contact_endpoint(form: ContactFormInput, request: Request):
    """Website contact form: same storage and two emails (visitor + company) as the chat's meeting agent."""
    from api_security import chat_rate_limiter
    from meeting_agent import get_meeting_agent, find_email, find_phone, valid_name, _clean
    chat_rate_limiter.check(request, f"contact-form:{request.client.host if request.client else 'unknown'}")
    email, phone, name = find_email(form.email), find_phone(form.phone), valid_name(form.name)
    if not (email and phone and name):
        bad = [k for k, v in (("name", name), ("email", email), ("phone", phone)) if not v]
        raise HTTPException(status_code=422, detail={"invalid": bad})
    purpose = f"{form.inquiry}: {form.message}" + (f" (Company: {form.company})" if form.company else "")
    details = {"name": name, "email": email, "phone": phone, "purpose": _clean(purpose, "purpose"),
               "timing": _clean(form.timing or "Not specified — please suggest a time", "timing")}
    agent = get_meeting_agent()
    rid, statuses = await agent.deliver(f"contact-form-{uuid.uuid4().hex[:8]}", details, {"source": "website contact form"},
                                        "For details, contact info@cittaai.com")
    return {"reference": rid, "company_email": statuses["company"], "visitor_email": statuses["user"]}


@api_router.post("/chat")
async def chat_endpoint(input_data: ChatMessageInput, background_tasks: BackgroundTasks, request: Request):
    """Streaming chat completions (SSE) through the unified semantic pipeline (RAGService.chat_stream)."""
    from api_security import chat_rate_limiter
    chat_rate_limiter.check(request, input_data.session_id)
    try:
        session_id = input_data.session_id
        message = input_data.message
        provider_model = get_config("llm_model", config.MODEL_NAME)
        rag_serv = get_rag_service()
        
        async def sse_generator():
            try:
                async for chunk in rag_serv.chat_stream(session_id=session_id, message=message, model=provider_model):
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.01)
            except Exception as e:
                logger.exception("Error in SSE chat stream")
                yield f"data: {json.dumps({'text': f'Error occurred: {str(e)}', 'done': True})}\n\n"
                
        return StreamingResponse(sse_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.exception("Error in chat endpoint initialization")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/chat/clear")
async def clear_chat_endpoint(data: Dict[str, str]):
    session_id = data.get("session_id")
    if session_id:
        rag_serv = get_rag_service()
        rag_serv.clear_session(session_id)
    return {"message": "Session cleared"}


# ---------------- ADMIN APIS ----------------

@api_router.get("/admin/meeting-requests", dependencies=[Depends(require_admin)])
async def admin_meeting_requests(limit: int = 50):
    """Meeting / contact requests collected by the chat's meeting agent, newest first, with email delivery status."""
    from meeting_agent import get_meeting_agent
    return {"requests": get_meeting_agent().store.recent(max(1, min(limit, 500)))}


@api_router.get("/admin/status", dependencies=[Depends(require_admin)])
async def admin_status():
    """Retrieve config status and DB health metric."""
    count = vstore.get_chunk_count()
    provider = get_config("llm_provider", config.LLM_PROVIDER)
    model = get_config("llm_model", config.MODEL_NAME)
    
    # Check if NVIDIA API key is configured
    nvidia_healthy = True if config.API_KEY else False
        
    return {
        "provider": provider,
        "model": model,
        "chunk_count": count,
        "vector_db_health": "Healthy" if count > 0 else "Empty",
        "nvidia_status": "Connected" if nvidia_healthy else "Disconnected"
    }

@api_router.post("/admin/config", dependencies=[Depends(require_admin)])
async def admin_update_config(data: ConfigUpdateInput):
    """Change LLM Provider / Model."""
    global _rag_service_instance
    set_config("llm_provider", data.provider)
    set_config("llm_model", data.model)
    _rag_service_instance = None
    return {"message": "Config updated successfully"}

@api_router.get("/health")
async def health_check():
    """System health endpoint checking database, embeddings, and API connection."""
    # 1. Database check
    try:
        count = vstore.get_chunk_count()
        db_status = "Healthy" if count > 0 else "Empty"
    except Exception as e:
        db_status = f"Unhealthy: {str(e)}"

    # 2. Local embeddings model check
    try:
        rag_serv = get_rag_service()
        emb = await rag_serv.get_embedding("healthcheck")
        emb_status = f"Healthy (dimension: {len(emb)})"
    except Exception as e:
        emb_status = f"Unhealthy: {str(e)}"

    # 3. Configured LLM providers (keys present; no secrets are returned)
    primary_key = {"groq": config.GROQ_API_KEY, "gemini": config.GEMINI_API_KEY, "nvidia": config.NVIDIA_API_KEY}.get(config.LLM_PROVIDER.lower(), "")
    api_status = "Configured" if primary_key else "Missing API Key"
    fallback = str(getattr(config, "LLM_FALLBACK_PROVIDER", "none")).lower()
    fallback_status = "Configured" if fallback == "gemini" and config.GEMINI_API_KEY else "None"

    # 4. Vector index integrity (stale index blocks chat in production)
    try:
        from index_integrity import get_status
        integ = get_status()
        index_status = {"fresh": integ["fresh"], "rebuild_required": integ.get("rebuild_required", False),
                        "index_version": integ.get("index_version"), "built_at": integ.get("built_at"), "reasons": integ.get("reasons", [])}
    except Exception as e:
        index_status = {"fresh": False, "error": str(e)}

    healthy = ("Unhealthy" not in db_status and "Unhealthy" not in emb_status and index_status.get("fresh")
               and api_status == "Configured")
    return {
        "status": "Healthy" if healthy else "Degraded",
        "vector_index": index_status,
        "llm_fallback": {"provider": fallback, "model": config.GEMINI_MODEL if fallback == "gemini" else None, "status": fallback_status},
        "database": db_status,
        "embedding_model": {
            "model_name": config.EMBEDDING_MODEL,
            "status": emb_status
        },
        "llm_provider": {
            "provider": config.LLM_PROVIDER,
            "model": config.MODEL_NAME,
            "status": api_status
        }
    }

async def process_document_background(filename: str, page: str, section: str, title: str, extracted_text: str, ext: str):
    # Chunk text (simple paragraph chunker)
    paragraphs = [p.strip() for p in extracted_text.split("\n\n") if p.strip()]
    chunks = []
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Parse chunks
    for i, p in enumerate(paragraphs):
        chunks.append({
            "content": f"Document [{filename}] Section {title}: {p}",
            "metadata": {
                "source": filename,
                "page": page,
                "section": section,
                "title": f"{title} - Part {i+1}",
                "category": "brochure",
                "url": page,
                "last_updated": timestamp,
                "doc_type": ext.lstrip(".")
            }
        })
        
    # Generate embeddings and add to SQLite
    rag_serv = get_rag_service()
    
    # Delete older chunks from same document first to prevent duplicates
    vstore.delete_document(filename)
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"upload_{filename}_{i}"
        emb = await rag_serv.get_embedding(chunk["content"], input_type="passage")
        vstore.add_chunk(
            chunk_id=chunk_id,
            content=chunk["content"],
            embedding=emb,
            metadata=chunk["metadata"]
        )
    logging.info(f"Successfully processed and indexed {len(chunks)} chunks from {filename} in background.")

@api_router.get("/health/details", dependencies=[Depends(require_admin)])
async def detailed_health_check() -> Dict[str, Any]:
    """Production health & diagnostic status endpoint."""
    meta = vstore.get_metadata()
    count = vstore.get_chunk_count()
    rag = _rag_service_instance
    emb_loaded = rag.is_embedding_model_loaded() if rag else False
    reranker_loaded = rag.is_reranker_loaded() if rag else False
    
    val = vstore.validate_database_integrity()
    return {
        "status": "healthy",
        "database": "ready" if count > 0 else "missing_or_empty",
        "database_valid": val.get("valid", False),
        "chunk_count": count,
        "embedding_model_loaded": emb_loaded,
        "reranker_loaded": reranker_loaded,
        "database_version": meta.get("version", "1.0.0"),
        "schema_version": meta.get("schema_version", "1.0.0"),
        "parser_version": meta.get("parser_version", "1.0.0"),
        "application_version": meta.get("application_version", "1.0.0"),
        "content_hash": meta.get("content_hash", ""),
        "created_at": meta.get("created_at", ""),
        "environment": getattr(config, "ENVIRONMENT", "production")
    }

@api_router.post("/admin/reindex", status_code=202, dependencies=[Depends(require_admin)])
async def admin_reindex(background_tasks: BackgroundTasks):
    """Manual async background re-index API."""
    job_id = str(uuid.uuid4())
    background_tasks.add_task(perform_reindex)
    return {
        "status": "accepted",
        "job_id": job_id,
        "state": "running"
    }

@api_router.post("/admin/upload", dependencies=[Depends(require_admin)])
async def admin_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    page: str = Form("/"),
    section: str = Form("brochures"),
    title: str = Form("Brochure")
):
    """Handles PDF / DOCX file upload, text extraction, and ChromaDB/SQLite ingestion."""
    contents = await file.read()
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    
    extracted_text = ""
    if ext == ".pdf":
        extracted_text = extract_pdf_text(contents)
    elif ext in [".docx", ".doc"]:
        extracted_text = extract_docx_text(contents)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF or DOCX.")
        
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No readable text extracted from the document.")

    background_tasks.add_task(process_document_background, filename, page, section, title, extracted_text, ext)
    return {"message": f"Successfully uploaded {filename}. Processing and indexing started in the background."}

@api_router.get("/admin/documents", dependencies=[Depends(require_admin)])
async def admin_get_documents():
    """Retrieve list of indexed document sources."""
    return vstore.get_all_documents()

@api_router.delete("/admin/documents/{source_name:path}", dependencies=[Depends(require_admin)])
async def admin_delete_document(source_name: str):
    """Deletes chunks matching document source."""
    deleted_count = vstore.delete_document(source_name)
    return {"message": f"Deleted {deleted_count} chunks for source '{source_name}'."}

@api_router.get("/admin/chunks", dependencies=[Depends(require_admin)])
async def admin_get_chunks():
    """Lists indexed chunks for verification."""
    return vstore.get_all_chunks()

@api_router.get("/admin/analytics", dependencies=[Depends(require_admin)])
async def admin_analytics():
    """Computes administrative dashboard analytics statistics (queries, success rates, latency)."""
    conn = sqlite3.connect(ANALYTICS_DB_PATH)
    cursor = conn.cursor()
    
    # Total query count
    cursor.execute("SELECT COUNT(*) FROM queries")
    total_queries = cursor.fetchone()[0]
    
    # Average response time
    cursor.execute("SELECT AVG(latency) FROM queries")
    avg_latency = cursor.fetchone()[0] or 0.0
    
    # Search success rate (CASE_1/CASE_2 or fallback to threshold)
    cursor.execute("SELECT COUNT(*) FROM queries WHERE decision_case IN ('CASE_1', 'CASE_2') OR (decision_case IS NULL AND score >= 0.45)")
    success_queries = cursor.fetchone()[0]
    success_rate = (success_queries / total_queries * 100) if total_queries > 0 else 100.0
    
    # Failed Queries count (CASE_3/CASE_4 or fallback)
    cursor.execute("SELECT COUNT(*) FROM queries WHERE decision_case IN ('CASE_3', 'CASE_4') OR (decision_case IS NULL AND score < 0.45)")
    failed_queries = cursor.fetchone()[0]
    
    # Most asked queries (top 5)
    cursor.execute("SELECT query, COUNT(*) as c FROM queries GROUP BY query ORDER BY c DESC LIMIT 5")
    most_asked = [{"query": r[0], "count": r[1]} for r in cursor.fetchall()]
    
    # Top redirects (top 5)
    cursor.execute("SELECT redirect, COUNT(*) as c FROM queries WHERE redirect IS NOT NULL GROUP BY redirect ORDER BY c DESC LIMIT 5")
    top_redirects = [{"path": r[0], "count": r[1]} for r in cursor.fetchall()]
    
    # Recent log entries
    cursor.execute("SELECT timestamp, query, response, intent, score, latency FROM queries ORDER BY timestamp DESC LIMIT 20")
    logs = [{
        "timestamp": r[0],
        "query": r[1],
        "response": r[2][:80] + "...",
        "intent": r[3],
        "score": r[4],
        "latency": r[5]
    } for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_queries": total_queries,
        "average_response_time": f"{avg_latency:.2f}s",
        "search_success_rate": f"{success_rate:.1f}%",
        "failed_queries": failed_queries,
        "most_asked_questions": most_asked,
        "top_redirects": top_redirects,
        "logs": logs
    }


# MongoDB routes fallback compatibility
class StatusCheckCreate(BaseModel):
    client_name: str

@api_router.post("/status", response_model=StatusCheck, dependencies=[Depends(require_admin)])
async def create_status_check(input: StatusCheckCreate) -> StatusCheck:
    status_obj = StatusCheck(**input.model_dump())
    doc: Dict[str, Any] = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    try:
        _ = await db.status_checks.insert_one(doc)
    except Exception:
        # Ignore MongoDB connection failures during local RAG execution
        pass
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck], dependencies=[Depends(require_admin)])
async def get_status_checks() -> List[Dict[str, Any]]:
    try:
        status_checks: List[Dict[str, Any]] = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
        for check in status_checks:
            if isinstance(check['timestamp'], str):
                check['timestamp'] = datetime.fromisoformat(check['timestamp'])
        return status_checks
    except Exception:
        return []

class DebugQueryInput(BaseModel):
    message: str
    session_id: Optional[str] = "debug_session"

@api_router.post("/debug/query", dependencies=[Depends(require_admin)])
async def debug_query_endpoint(input_data: DebugQueryInput):
    """Developer-only diagnostic endpoint returning granular query classifier details."""
    import time
    from query_planner import classify_query
    from response_builder import build_deterministic_response
    
    query = input_data.message
    start_time = time.time()
    rag_serv = get_rag_service()
    
    cls_res = classify_query(query, rag_serv.embedding_model)
    det_res = build_deterministic_response(cls_res["query_type"], cls_res["domain"], cls_res["matched_entity"])
    
    latency_ms = (time.time() - start_time) * 1000.0
    return {
        "classification": cls_res,
        "deterministic_match": det_res is not None,
        "deterministic_response": det_res,
        "latency_ms": latency_ms
    }

app.include_router(api_router)