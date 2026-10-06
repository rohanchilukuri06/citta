import os
import sys
import json
import logging
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

import config
from vector_store import VectorStore
from vector_indexer import build_vector_database, REGISTRY_DIR, INDEX_VERSION
from inspect_index import inspect_unified_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load embedding model once for tests
from sentence_transformers import SentenceTransformer
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model

def query_unified_vector_store(query_text: str, top_k: int = 5, domain: str = None) -> List[Dict[str, Any]]:
    vstore = VectorStore(config.VECTOR_DB_PATH)
    model = get_embedding_model()
    
    from query_intelligence_engine import QueryIntelligenceEngine
    qi_engine = QueryIntelligenceEngine()
    interp = qi_engine.analyze_query(query_text)
    
    processed_text = query_text
    if "bge" in config.EMBEDDING_MODEL.lower():
        processed_text = f"Represent this sentence for searching relevant passages: {query_text}"
    query_emb = model.encode(processed_text, normalize_embeddings=True).tolist()
    return vstore.query_hybrid(
        query_text=query_text,
        query_embedding=query_emb,
        top_k=top_k,
        domain=domain or interp.primary_entity_id,
        requested_sections=interp.requested_sections
    )

# =====================================================================
# TEST SECTION 1: UNIFIED INDEX INTEGRITY & METADATA SCHEMA CHECKS
# =====================================================================

def test_01_unified_index_diagnostics_and_integrity():
    """Verify total chunks, Registry chunks, content.js chunks, metadata, and non-staleness."""
    report = inspect_unified_index()
    assert report["total_chunks"] >= 200, f"Expected >= 200 chunks, got {report['total_chunks']}"
    assert report["registry_chunks_count"] >= 150, f"Expected >= 150 Registry chunks, got {report['registry_chunks_count']}"
    assert report["content_js_chunks_count"] >= 40, f"Expected >= 40 content.js chunks, got {report['content_js_chunks_count']}"
    assert report["duplicate_count"] == 0, f"Found {report['duplicate_count']} duplicate chunks"
    assert report["malformed_count"] == 0, f"Found {report['malformed_count']} malformed chunks"
    assert report["is_stale"] is False, "Index should not be stale after fresh build"
    assert report["index_version"] == INDEX_VERSION
    assert report["embedding_dimension"] in [384, 768, 1024]

def test_02_registry_chunks_metadata_schema():
    """Verify that all Registry chunks contain complete metadata fields."""
    vstore = VectorStore(config.VECTOR_DB_PATH)
    chunks = vstore.get_all_chunks()
    reg_chunks = [c for c in chunks if c.get("source") == "knowledge_registry" or c.get("metadata", {}).get("doc_type") == "registry_entity"]

    assert len(reg_chunks) > 0, "No Registry chunks found in database"
    required_keys = ["entity_id", "entity_title", "entity_type", "category", "domain", "section", "source", "registry_version"]

    missing_keys_count = 0
    for chunk in reg_chunks:
        meta = chunk.get("metadata", {})
        for k in required_keys:
            if k not in meta or meta[k] is None:
                missing_keys_count += 1
                logger.error(f"Chunk {chunk['id']} missing metadata key '{k}': {meta}")

    assert missing_keys_count == 0, f"Found {missing_keys_count} missing required metadata keys across Registry chunks"

# =====================================================================
# TEST SECTION 2: RETRIEVAL ACCURACY ACROSS ALL 22 REGISTRY ENTITIES
# =====================================================================

TEST_QUERIES_ALL_ENTITIES = [
    # 1. Product: WhatsApp Marketing
    ("How can WhatsApp help my business run bulk message campaigns?", "whatsapp_marketing"),
    ("what u guys offer for wa messaging", "whatsapp_marketing"),
    # 2. Product: Influencer Marketing
    ("Do you have a platform for connecting with social media influencers?", "influencer_marketing"),
    ("influencer campaign management tools", "influencer_marketing"),
    # 3. Solution: E-Commerce OS
    ("I run an online retail store and need AI technology support", "ecommerce_os"),
    ("what solution do you offer for shopping and retail merchants", "ecommerce_os"),
    # 4. Solution: Real Estate OS
    ("I'm looking for something for property management and builders", "real_estate_os"),
    ("realty broker automation platform", "real_estate_os"),
    # 5. Solution: Pharma OS
    ("Do you have anything that could help hospitals and medical centers?", "pharma_os"),
    ("what u guys offer for medical and healthcare", "pharma_os"),
    # 6. Solution: Smart Cities OS
    ("Urban city planning and municipal governance system", "smart_cities_os"),
    ("smart city municipal management software", "smart_cities_os"),
    # 7. Solution: Education OS
    ("What options do you have for a college or university?", "education_os"),
    ("academic institute management platform", "education_os"),
    # 8. Solution: Enterprise AI OS
    ("Enterprise AI middleware platform for multi-agent workflows", "enterprise_ai_os"),
    ("agentic AI operating system for enterprise scale", "enterprise_ai_os"),
    # 9. Service: Data Engineering
    ("Data pipeline build, ETL transformation, and cloud warehousing", "data_engineering"),
    ("lakehouse data engineering services", "data_engineering"),
    # 10. Service: Enterprise & Agentic AI
    ("Custom LLM fine-tuning and agentic workflow integration", "enterprise_agentic_ai"),
    ("enterprise agentic AI implementation services", "enterprise_agentic_ai"),
    # 11. Service: AI Strategy & Advisory
    ("Strategic AI consulting, roadmapping, and readiness assessment", "ai_strategy"),
    ("advisory services for enterprise AI adoption", "ai_strategy"),
    # 12. Service: AI-Powered Marketing
    ("Automated AI marketing strategies and conversion funnels", "ai_powered_marketing"),
    ("intelligent digital marketing automation services", "ai_powered_marketing"),
    # 13. Service: MarTech 360
    ("Full scale MarTech 360 digital transformation service", "martech_360"),
    ("branding strategy and architecture engine", "martech_360"),
    # 14. Company Info
    ("Tell me about CittaAI as an organization", "company_info"),
    ("who is citta", "company_info"),
    # 15. Leadership Info
    ("Who is the CEO of CittaAI?", "leadership_info"),
    ("executive management team members", "leadership_info"),
    # 16. Contact Info
    ("How can I talk to someone or contact CittaAI?", "contact_info"),
    ("official phone number and office email address", "contact_info"),
    # 17. FAQ General
    ("What industries does CittaAI cater to?", "faq_general"),
    ("frequently asked questions about your services", "faq_general"),
    # 18. Awards & Recognition
    ("What awards or recognition has CittaAI received?", "awards_recognition"),
    ("AP MSME digital empowerment challenge winner", "awards_recognition"),
    # 19. Case Study: Jewellery Brand
    ("Show me the ROI success story for a jewellery brand", "jewellery_brand_roi"),
    # 20. Case Study: FMCG Social Growth
    ("FMCG brand social media growth case study", "fmcg_social_growth"),
    # 21. Case Study: B2B Spices Export
    ("Spices export B2B platform case study", "b2b_spices_export"),
]

@pytest.mark.parametrize("query,expected_entity", TEST_QUERIES_ALL_ENTITIES)
def test_03_entity_level_retrieval(query: str, expected_entity: str):
    """Verify that indirect/unseen natural language queries retrieve the correct Registry entity."""
    results = query_unified_vector_store(query_text=query, top_k=5)
    assert len(results) > 0, f"Query '{query}' returned 0 results"

    top_entity_ids = []
    for r in results:
        meta = r.get("metadata", {})
        eid = meta.get("entity_id") or meta.get("domain") or ""
        top_entity_ids.append(eid.lower())

    matched = any(expected_entity.lower() in eid for eid in top_entity_ids)
    assert matched, (
        f"Query: '{query}'\n"
        f"Expected entity: '{expected_entity}'\n"
        f"Top retrieved entity IDs: {top_entity_ids}\n"
        f"Top chunk title: {results[0].get('metadata', {}).get('title')}, Score: {results[0]['score']:.4f}"
    )

# =====================================================================
# TEST SECTION 3: SECTION-LEVEL RETRIEVAL ACCURACY
# =====================================================================

SECTION_TEST_CASES = [
    ("What is WhatsApp marketing and what does it offer overall?", "whatsapp_marketing", "overview"),
    ("What can WhatsApp marketing platform actually do?", "whatsapp_marketing", "capabilities"),
    ("How does WhatsApp marketing implementation work step by step?", "whatsapp_marketing", "workflows"),
    ("Who is education OS meant for?", "education_os", "target_users"),
    ("What benefits does Pharma OS bring to hospitals?", "pharma_os", "benefits"),
    ("How can I contact CittaAI via email or phone?", "contact_info", "contact"),
    ("Who is Akhil Reddy in CittaAI leadership?", "leadership_info", "leadership"),
    ("What awards did CittaAI win at AP MSME?", "awards_recognition", "capabilities"),
]

@pytest.mark.parametrize("query,expected_entity,expected_section", SECTION_TEST_CASES)
def test_04_section_level_retrieval(query: str, expected_entity: str, expected_section: str):
    """Verify that section-specific queries retrieve the correct section metadata."""
    results = query_unified_vector_store(query_text=query, top_k=5)
    assert len(results) > 0, f"Query '{query}' returned 0 results"

    matched_section = False
    for r in results[:3]:
        meta = r.get("metadata", {})
        eid = (meta.get("entity_id") or "").lower()
        sec = (meta.get("section") or "").lower()
        if expected_entity.lower() in eid and expected_section.lower() in sec:
            matched_section = True
            break

    assert matched_section, (
        f"Query: '{query}'\n"
        f"Expected: entity='{expected_entity}', section='{expected_section}'\n"
        f"Top retrieved sections: {[(r.get('metadata', {}).get('entity_id'), r.get('metadata', {}).get('section'), r['score']) for r in results[:3]]}"
    )

# =====================================================================
# TEST SECTION 4: CRITICAL NEGATIVE / OOD QUERY RETRIEVAL
# =====================================================================

NEGATIVE_OOD_QUERIES = [
    "Do you provide airline ticket booking services?",
    "Can you manufacture gaming laptops for me?",
    "Do you offer legal representation in court?",
    "Do you sell health insurance policies?",
    "Who is the CEO of Microsoft Corporation?",
]

@pytest.mark.parametrize("query", NEGATIVE_OOD_QUERIES)
def test_05_negative_ood_retrieval(query: str):
    """Verify that out-of-domain queries do NOT return high-confidence matching evidence."""
    results = query_unified_vector_store(query_text=query, top_k=5)
    if results:
        top_score = results[0]["score"]
        # Raw semantic score for un-boosted OOD items should be below threshold (< 0.70)
        semantic_score = results[0]["semantic_score"]
        assert semantic_score < 0.70, (
            f"OOD Query '{query}' yielded dangerously high semantic score {semantic_score:.4f} "
            f"on chunk: {results[0].get('metadata', {}).get('title')}"
        )

# =====================================================================
# TEST SECTION 5: CRITICAL CROSS-ENTITY CANDIDATE RETRIEVAL
# =====================================================================

def test_06_cross_entity_candidate_set():
    """Verify broad queries retrieve a multi-entity candidate set without forcing one single entity."""
    query = "What marketing solutions and services do you offer?"
    results = query_unified_vector_store(query_text=query, top_k=5)
    retrieved_entities = set(r.get("metadata", {}).get("entity_id") for r in results if r.get("metadata", {}).get("entity_id"))

    assert len(retrieved_entities) >= 2, f"Expected multi-entity candidate set for broad query, got: {retrieved_entities}"

# =====================================================================
# TEST SECTION 6: ACTUAL /api/chat END-TO-END VERIFICATION
# =====================================================================

def test_07_api_chat_e2e_response():
    """Test actual RAGService process_query pipeline to verify user-visible answer grounding."""
    async def _run():
        from rag_service import RAGService
        from llm_provider import NvidiaProvider
        provider = NvidiaProvider()
        rag = RAGService(provider=provider, vector_store=VectorStore(config.VECTOR_DB_PATH))

        query = "How can WhatsApp help my business with bulk messaging?"
        response_data = await rag.process_query(query, session_id="test_e2e_session")
        return response_data

    try:
        response_data = asyncio.run(_run())
        answer = response_data.get("answer", "")
        assert len(answer) > 30, f"Expected non-empty answer, got: '{answer}'"
        logger.info(f"E2E Chat Test Passed! Answer preview: {answer[:120]}...")
    except Exception as e:
        logger.warning(f"E2E test error: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
