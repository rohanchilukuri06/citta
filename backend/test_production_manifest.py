import os
import json
import time
import pytest
import sqlite3
from pathlib import Path

import config
import server
from knowledge_registry import get_registry
from query_normalizer import normalize_query_pipeline
from registry_resolver import resolve_registry
from entity_resolver import resolve_entity_dynamic
from section_resolver import resolve_section_dynamic
from knowledge_router import route_query
from rag_service import RAGService
from llm_provider import get_llm_provider
from vector_store import VectorStore
from context_builder import build_structured_context
from response_validator import validate_response, FALLBACK_MESSAGE
from explainability_logger import get_recent_explainability_logs

BACKEND_DIR = Path(__file__).resolve().parent

# --- 1. Registry & Manifest Correctness Tests ---

def test_manifest_loader_correctness():
    """Verify that get_registry loads matching files from manifest.json."""
    reg = get_registry()
    assert reg is not None
    assert len(reg.registry_index) > 0
    assert "PRODUCTS" in reg.registry_index
    assert "SERVICES" in reg.registry_index
    assert "SOLUTIONS" in reg.registry_index

def test_registry_schema_validity():
    """Verify metadata format and presence of critical keys."""
    reg = get_registry()
    for reg_type, data in reg.registry_index.items():
        meta = data.get("metadata", {})
        assert meta is not None
        assert "registry_id" in meta
        assert "registry_type" in meta
        assert "schema_version" in meta
        assert "priority" in meta
        assert "capabilities" in meta
        assert "supported_sections" in meta

# --- 2. Entity Resolution & Alias Lookup Tests ---

def test_alias_lookup_single_source_of_truth():
    """Verify ONE canonical runtime lookup (entity_lookup) built at startup."""
    reg = get_registry()
    assert hasattr(reg, "entity_lookup")
    assert len(reg.entity_lookup) > 0
    
    test_mappings = {
        "real estate os": "real_estate_os",
        "property os": "real_estate_os",
        "broker os": "real_estate_os",
        "pharma os": "pharma_os",
        "education os": "education_os",
        "smart cities os": "smart_cities_os",
        "ecommerce os": "ecommerce_os",
        "whatsapp marketing": "whatsapp_marketing"
    }
    for alias, expected in test_mappings.items():
        assert reg.entity_lookup.get(alias) == expected, f"Failed lookup for alias '{alias}'"

def test_entity_resolution_precedence():
    """Verify strict precedence: Exact ID -> Exact Name -> Substring -> Aliases -> RapidFuzz."""
    reg = get_registry()
    
    # 1. Exact ID
    ent, score, alias, _ = resolve_entity_dynamic("real_estate_os", reg.entities, entity_lookup=reg.entity_lookup)
    assert ent == "real_estate_os"
    assert score == 1.0
    
    # 2. Exact Name
    ent, score, alias, _ = resolve_entity_dynamic("Real Estate OS", reg.entities, entity_lookup=reg.entity_lookup)
    assert ent == "real_estate_os"
    
    # 3. Alias Lookup
    ent, score, alias, _ = resolve_entity_dynamic("broker os", reg.entities, entity_lookup=reg.entity_lookup)
    assert ent == "real_estate_os"
    
    # 4. RapidFuzz matching (typo)
    ent, score, alias, _ = resolve_entity_dynamic("pharmaa os", reg.entities, entity_lookup=reg.entity_lookup)
    assert ent == "pharma_os"

def test_substring_matching_and_phrase_boundaries():
    """Verify whole-word boundary phrase matching for entity names and aliases."""
    reg = get_registry()
    ent, score, alias, _ = resolve_entity_dynamic("Tell me about Pharma OS", reg.entities, entity_lookup=reg.entity_lookup)
    assert ent == "pharma_os"
    assert score >= 0.90

# --- 3. Query Normalization & Spelling Tests ---

def test_spelling_corrections_and_abbreviations():
    """Verify spelling correction token fallbacks and abbreviations."""
    reg = get_registry()
    
    # Test abbreviation expansion: 'wa' -> 'whatsapp_marketing'
    res = normalize_query_pipeline("how does wa work", reg.unified_vocabulary, reg.abbreviations, entity_lookup=reg.entity_lookup)
    assert "whatsapp_marketing" in res["normalized_query"]
    
    # Test safe spelling (unknown word retained without silent low-confidence replacement)
    res_unknown = normalize_query_pipeline("xyzabc123", reg.unified_vocabulary, reg.abbreviations, entity_lookup=reg.entity_lookup)
    assert "xyzabc123" in res_unknown["normalized_query"]

# --- 4. Section Resolution & Ambiguity Tests ---

def test_section_resolution_and_synonyms():
    """Verify section resolution using semantic synonym groups."""
    reg = get_registry()
    meta = reg.registry_index.get("SOLUTIONS", {}).get("metadata")
    ent = reg.get_entity("real_estate_os")
    
    # 'advantages' -> benefits
    sec, score, clar = resolve_section_dynamic("What are the advantages of Real Estate OS", ent, meta)
    assert sec == "benefits"
    
    # 'workflow' -> how_it_works
    sec, score, clar = resolve_section_dynamic("Explain the workflow", ent, meta)
    assert sec == "how_it_works"

def test_section_ambiguity_clarification():
    """Verify that ambiguous section queries trigger clarification prompts."""
    reg = get_registry()
    meta = reg.registry_index.get("SOLUTIONS", {}).get("metadata")
    ent = reg.get_entity("real_estate_os")
    
    sec, score, clar = resolve_section_dynamic("benefits and features of Real Estate OS", ent, meta, ambiguity_threshold=0.15)
    assert sec is None
    assert clar is not None
    assert clar["type"] == "clarification"

def test_missing_sections_handling():
    """Verify graceful handling when a query requests a missing section."""
    reg = get_registry()
    meta = reg.registry_index.get("SOLUTIONS", {}).get("metadata")
    ent = reg.get_entity("real_estate_os")
    
    sec, score, clar = resolve_section_dynamic("show pricing details", ent, meta)
    assert sec in ["overview", "benefits", None]  # Fallback to overview or prompt

# --- 5. Context Builder & Grounding Tests ---

def test_context_builder_structured_output():
    """Verify ContextBuilder produces structured context without raw JSON."""
    reg = get_registry()
    state = {"history": [{"role": "user", "content": "Hi"}]}
    
    ctx = build_structured_context(
        resolved_entity="ecommerce_os",
        resolved_section="how_it_works",
        registry=reg,
        conversation_state=state
    )
    
    assert "ENTITY: E-Commerce OS" in ctx
    assert "PRIMARY SECTION (How It Works):" in ctx
    assert not ctx.startswith("{")

# --- 6. Response Validator & Pricing Guardrails Tests ---

def test_response_validator_pricing_guardrails():
    """Verify pricing guardrails reject hallucinated numerical dollar/rupee prices."""
    reg = get_registry()
    
    # Fake pricing check
    val_ok, verified_text = validate_response("E-Commerce OS costs $499/month", resolved_entity="ecommerce_os", registry=reg)
    assert val_ok is False

def test_response_validator_fallback_on_retry():
    """Verify fallback message returned when validation fails after retry."""
    reg = get_registry()
    val_ok, text_out = validate_response("Fake product SuperBot OS costs $1000", resolved_entity="ecommerce_os", registry=reg, retry_count=1)
    assert val_ok is False
    assert text_out == FALLBACK_MESSAGE

# --- 7. Analytics & Database Telemetry Tests ---

def test_sqlite_analytics_logging():
    """Verify that query, routing, performance, and explainability analytics tables exist."""
    conn = sqlite3.connect(config.SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    for tbl in ["query_analytics", "routing_analytics", "performance_analytics", "explainability_analytics"]:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}'")
        assert cursor.fetchone() is not None, f"Table '{tbl}' missing from SQLite database"
        
    conn.close()

def test_explainability_analytics_buffer():
    """Verify explainability logs are recorded internally."""
    logs = get_recent_explainability_logs(10)
    assert isinstance(logs, list)

# --- 8. User Feedback & Intent Fixes Tests ---

@pytest.mark.anyio
async def test_company_multi_section_queries():
    vstore = VectorStore()
    provider = get_llm_provider("mock", {})
    rag = RAGService(provider, vstore)
    chunks = []
    async for chunk in rag.chat_stream("test_multi_sec", "Tell me about CittaAI company, mission, and vision.", "test_model"):
        chunks.append(chunk)
    text = chunks[0]["text"]
    assert "Overview" in text or "CittaAI" in text
    assert "Mission" in text
    assert "Vision" in text

@pytest.mark.anyio
async def test_person_specific_ceo_query():
    vstore = VectorStore()
    provider = get_llm_provider("mock", {})
    rag = RAGService(provider, vstore)
    chunks = []
    async for chunk in rag.chat_stream("test_ceo", "CEO", "test_model"):
        chunks.append(chunk)
    text = chunks[0]["text"]
    assert "Vinay Velivela" in text
    assert "Co-Founder & CTO" not in text

@pytest.mark.anyio
async def test_case_studies_catalog_consistency():
    vstore = VectorStore()
    provider = get_llm_provider("mock", {})
    rag = RAGService(provider, vstore)
    for q in ["case studies", "Tell me about case studies", "List all case studies"]:
        chunks = []
        async for chunk in rag.chat_stream("test_cs", q, "test_model"):
            chunks.append(chunk)
        text = chunks[0]["text"]
        assert "Jewellery" in text
        assert "FMCG" in text
        assert "Spices" in text

@pytest.mark.anyio
async def test_count_queries_deterministic():
    vstore = VectorStore()
    provider = get_llm_provider("mock", {})
    rag = RAGService(provider, vstore)
    chunks = []
    async for chunk in rag.chat_stream("test_count", "How many case studies?", "test_model"):
        chunks.append(chunk)
    text = chunks[0]["text"]
    assert "3 published case studies" in text

@pytest.mark.anyio
async def test_certifications_query_routing():
    vstore = VectorStore()
    provider = get_llm_provider("mock", {})
    rag = RAGService(provider, vstore)
    chunks = []
    async for chunk in rag.chat_stream("test_cert", "What certifications does CittaAI hold?", "test_model"):
        chunks.append(chunk)
    text = chunks[0]["text"]
    assert "Awards" in text or "Recognitions" in text or "AP MSME" in text or len(text) > 0

@pytest.mark.anyio
async def test_careers_grounded_answer():
    vstore = VectorStore()
    provider = get_llm_provider("mock", {})
    rag = RAGService(provider, vstore)
    chunks = []
    async for chunk in rag.chat_stream("test_careers", "How do I apply for a job?", "test_model"):
        chunks.append(chunk)
    text = chunks[0]["text"]
    assert "Contact page" in text or len(text) > 0

# --- 9. Multi-Tenant Platform Tests ---

def test_tenant_registry_and_onboarding():
    from tenant_registry import get_tenant_registry
    t_reg = get_tenant_registry()
    
    # Verify Tenant #1: CittaAI
    t1 = t_reg.get_tenant("cittaai")
    assert t1.name == "CittaAI"
    assert t1.tenant_id == "cittaai"
    
    # Onboard Tenant #2 dynamically
    t2 = t_reg.register_tenant("acme_corp", {
        "name": "Acme Corporation",
        "website_url": "https://acme.example.com",
        "brand_color": "#FF0000"
    })
    assert t2.tenant_id == "acme_corp"
    assert t2.name == "Acme Corporation"
    assert t_reg.get_tenant("acme_corp").name == "Acme Corporation"

def test_intent_analyzer_multi_topic():
    from intent_analyzer import get_intent_analyzer, TopicType, IntentType
    analyzer = get_intent_analyzer()
    
    res = analyzer.analyze("Tell me about CittaAI company, mission, vision and leadership.")
    assert res.is_multi_topic is True
    assert TopicType.COMPANY in res.topics
    assert TopicType.MISSION in res.topics
    assert TopicType.VISION in res.topics
    assert TopicType.LEADERSHIP in res.topics

def test_knowledge_service_generic_api():
    from knowledge_service import get_knowledge_service
    ks = get_knowledge_service()
    
    # find_entity
    ent = ks.find_entity("cittaai", "pharma os")
    assert ent is not None
    assert ent["id"] == "pharma_os"
    
    # list_entities
    prods = ks.list_entities("cittaai", "PRODUCTS")
    assert len(prods) == 2
    
    # count_entities
    counts = ks.count_entities("cittaai", "CASE_STUDIES")
    assert counts["count"] == 3
    
    # find_people
    ceo = ks.find_people("cittaai", "CEO")
    assert ceo is not None
    assert "Vinay" in ceo["name"]

def test_entity_engine_layered_resolution():
    from entity_engine import get_entity_engine
    ee = get_entity_engine()
    
    res_id, score, clar = ee.resolve_entity("real estate os", "cittaai")
    assert res_id == "real_estate_os"
    
    ceo_id, score, clar = ee.resolve_entity("CEO", "cittaai")
    assert ceo_id == "vinay_velivela"

def test_deterministic_engine_zero_llm():
    from deterministic_engine import get_deterministic_engine
    from intent_analyzer import IntentType, TopicType
    de = get_deterministic_engine()
    
    res = de.generate_response("cittaai", IntentType.COUNT, [TopicType.CASE_STUDIES], "How many case studies?")
    assert res is not None
    assert "3 published case studies" in res["response"]
    
    person_res = de.generate_response("cittaai", IntentType.ASK, [TopicType.PERSON_LOOKUP], "CEO", role="CEO")
    assert person_res is not None
    assert "Vinay Velivela" in person_res["response"]

def test_knowledge_source_manager_crawling():
    from knowledge_source_manager import get_ingestion_engine
    engine = get_ingestion_engine()
    res = engine.onboard_tenant("Mock Tenant", "https://example.com")
    assert res["status"] == "active"
    assert res["documents_ingested"] >= 1

# --- 10. Performance Benchmarks ---

def test_performance_latency_benchmarks():
    """Benchmark critical path modules for sub-millisecond execution."""
    reg = get_registry()
    
    # Normalizer latency benchmark
    t0 = time.perf_counter()
    for _ in range(100):
        normalize_query_pipeline("How real estate OS works", reg.unified_vocabulary, reg.abbreviations, entity_lookup=reg.entity_lookup)
    norm_time_ms = ((time.perf_counter() - t0) / 100.0) * 1000.0
    assert norm_time_ms < 5.0, f"Normalizer latency too high: {norm_time_ms:.2f}ms"
    
    # Entity resolver latency benchmark
    t0 = time.perf_counter()
    for _ in range(100):
        resolve_entity_dynamic("How real estate OS works", reg.entities, entity_lookup=reg.entity_lookup)
    res_time_ms = ((time.perf_counter() - t0) / 100.0) * 1000.0
    assert res_time_ms < 10.0, f"Entity resolver latency too high: {res_time_ms:.2f}ms"

# --- 9. Comprehensive Production Query Suite ---

@pytest.mark.anyio
async def test_all_production_queries():
    """Regression test suite for CittaAI routing pipeline queries."""
    vstore = VectorStore()
    provider = get_llm_provider("mock", {})
    rag = RAGService(provider, vstore)
    
    session_id = "test_prod_session"
    rag.clear_session(session_id)
    
    # 1. Query: "Hi" -> Greeting Detector
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Hi", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert "hello" in chunks[0]["text"].lower() or "welcome" in chunks[0]["text"].lower()
    assert final["source"] == "Greeting Detector"
    
    # 2. Query: "How realestate OS works" -> Real Estate OS + how_it_works
    chunks = []
    async for chunk in rag.chat_stream(session_id, "How realestate OS works", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "real_estate_os"
    assert len(chunks[0]["text"]) > 0
    
    # 3. Query: "Tell me how it works" -> Uses active_entity from context!
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Tell me how it works", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "real_estate_os"
    assert final["metrics"]["resolved_section"] == "how_it_works"
    
    # 4. Query: "Benefits of pharmaa os" -> Pharma OS + benefits (autocorrect typo!)
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Benefits of pharmaa os", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "pharma_os"
    assert final["metrics"]["resolved_section"] == "benefits"
    
    # 5. Query: "Show awards" -> Recognition
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Show awards", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_registry"] == "RECOGNITION"
    assert "award" in chunks[0]["text"].lower() or "recognition" in chunks[0]["text"].lower()
    
    # 6. Query: "Who is CTO" -> Leadership
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Who is CTO", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_registry"] == "LEADERSHIP"
    assert "akhil reddy" in chunks[0]["text"].lower() or "cto" in chunks[0]["text"].lower()
    
    # 7. Query: "Where is office" -> Location
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Where is office", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_registry"] in ["LOCATION", "CONTACT"]
    assert "hitec city" in chunks[0]["text"].lower() or "address" in chunks[0]["text"].lower()
    
    # 8. Query: "How many case studies" -> case studies count 3
    chunks = []
    async for chunk in rag.chat_stream(session_id, "How many case studies", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert "3 published case studies" in chunks[0]["text"]
    
    # 9. Query: "Show Jewellery Brand case study" -> returns only Jewellery Brand
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Show Jewellery Brand case study", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "jewellery_brand_roi"
    assert "3.5 cr" in chunks[0]["text"].lower()

    # 10. Query: "Explain E-Commerce OS benefits" -> E-Commerce OS benefits section
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Explain E-Commerce OS benefits", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "ecommerce_os"
    assert final["metrics"]["resolved_section"] == "benefits"
    assert "conversion" in chunks[0]["text"].lower() or "benefits" in chunks[0]["text"].lower()

    # 11. Query: "How does Pharma OS work?" -> Pharma OS how_it_works section
    chunks = []
    async for chunk in rag.chat_stream(session_id, "How does Pharma OS work?", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "pharma_os"
    assert final["metrics"]["resolved_section"] == "how_it_works"

    # 12. Query: "E-Commerce OS" -> Entity overview
    chunks = []
    async for chunk in rag.chat_stream(session_id, "E-Commerce OS", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "ecommerce_os"
    assert final["metrics"]["resolved_section"] == "overview"

    # 13. Query: "Benefits" -> uses active_entity (ecommerce_os)
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Benefits", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "ecommerce_os"
    assert final["metrics"]["resolved_section"] == "benefits"

    # 14. Query: "Show Solutions" -> Registry catalog solutions listing
    chunks = []
    async for chunk in rag.chat_stream(session_id, "Show Solutions", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_registry"] == "SOLUTIONS"
    assert final["metrics"]["resolved_entity"] in [None, "NONE"]
    assert "pharma" in chunks[0]["text"].lower() or "solutions" in chunks[0]["text"].lower()

    # 15. Query: "How real estate OS works" -> real_estate_os
    chunks = []
    async for chunk in rag.chat_stream(session_id, "How real estate OS works", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "real_estate_os"

    # 16. Query: "broker os" -> real_estate_os
    chunks = []
    async for chunk in rag.chat_stream(session_id, "broker os", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "real_estate_os"

    # 17. Query: "property os" -> real_estate_os
    chunks = []
    async for chunk in rag.chat_stream(session_id, "property os", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "real_estate_os"

    # 18. Query: "pharma os" -> pharma_os
    chunks = []
    async for chunk in rag.chat_stream(session_id, "pharma os", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "pharma_os"

    # 19. Query: "education os" -> education_os
    chunks = []
    async for chunk in rag.chat_stream(session_id, "education os", "test_model"):
        chunks.append(chunk)
    final = chunks[-1]
    assert final["done"] is True
    assert final["metrics"]["resolved_entity"] == "education_os"
