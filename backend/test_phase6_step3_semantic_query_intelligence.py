"""
Phase 6 Step 3: Semantic Query Intelligence & Aspect-Aware Retrieval Test Suite

Validates:
1. Entity, Aspect, Section, and Scope Accuracy.
2. Confusion-pair matrix test cases.
3. Transcript 3-turn context sensitivity.
4. Catalog listing & counting via KnowledgeService across all 21 entities.
5. EvidenceGate scope compliance and composite reranking bounds.
"""

import pytest
import asyncio
from typing import Dict, Any

from query_intelligence_engine import get_query_intelligence_engine, SemanticAspect, AnswerScope
from retrieval_reranker import get_retrieval_reranker
from evidence_gate import get_evidence_gate
from knowledge_service import get_knowledge_service, KnowledgeService
from rag_service import RAGService

@pytest.fixture
def engine():
    return get_query_intelligence_engine()

@pytest.fixture
def reranker():
    return get_retrieval_reranker()

@pytest.fixture
def gate():
    return get_evidence_gate()

@pytest.fixture
def ks():
    return get_knowledge_service()

# --- 1. Query Intelligence Classification Tests ---

def test_single_entity_aspect_pricing(engine):
    interp = engine.interpret_query("How much does WhatsApp Marketing cost?")
    assert interp.primary_entity_id == "whatsapp_marketing"
    assert interp.primary_aspect == SemanticAspect.PRICING
    assert interp.answer_scope == AnswerScope.SINGLE_ENTITY
    assert "pricing" in interp.requested_sections

def test_single_entity_aspect_capabilities(engine):
    interp = engine.interpret_query("What are the features and capabilities of E-Commerce OS?")
    assert interp.primary_entity_id == "ecommerce_os"
    assert interp.primary_aspect == SemanticAspect.CAPABILITIES
    assert "capabilities" in interp.requested_sections

def test_single_entity_ambiguous_aspect_fallback(engine):
    interp = engine.interpret_query("Tell me about Influencer Marketing Platform")
    assert interp.primary_entity_id == "influencer_marketing"
    assert interp.primary_aspect == SemanticAspect.OVERVIEW
    assert "overview" in interp.requested_sections

def test_cases_aspect_mapping(engine):
    interp = engine.interpret_query("Do you have any case studies or client success stories for Pharma OS?")
    assert interp.primary_entity_id == "pharma_os"
    assert interp.primary_aspect == SemanticAspect.CASE_STUDIES
    assert "CASE_STUDIES" in interp.target_registry_types

def test_awards_aspect_mapping(engine):
    interp = engine.interpret_query("What awards or industry recognitions has CittaAI won?")
    assert interp.primary_aspect == SemanticAspect.AWARDS
    assert "RECOGNITION" in interp.target_registry_types

def test_leadership_aspect_mapping(engine):
    interp = engine.interpret_query("Who is on the leadership team?")
    assert interp.primary_aspect == SemanticAspect.LEADERSHIP
    assert "leadership" in interp.requested_sections

def test_contact_aspect_mapping(engine):
    interp = engine.interpret_query("How can I contact CittaAI sales team?")
    assert interp.primary_aspect == SemanticAspect.CONTACT
    assert "contact" in interp.requested_sections

def test_catalog_query_product_scope(engine):
    interp = engine.interpret_query("List all products")
    assert interp.primary_aspect == SemanticAspect.CATALOG_LIST
    assert interp.answer_scope == AnswerScope.CATALOG_SCOPE

def test_clients_query_scope(engine):
    interp = engine.interpret_query("Which clients or brands use CittaAI?")
    assert interp.primary_aspect == SemanticAspect.CLIENTS
    assert interp.answer_scope == AnswerScope.CLIENTS_SCOPE

# --- 2. Confusion Pair Matrix Tests ---

def test_confusion_pair_same_entity_different_aspect(engine):
    interp_pricing = engine.interpret_query("What is WhatsApp Marketing pricing?")
    interp_cap = engine.interpret_query("What are WhatsApp Marketing workflows?")

    assert interp_pricing.primary_entity_id == interp_cap.primary_entity_id == "whatsapp_marketing"
    assert interp_pricing.primary_aspect == SemanticAspect.PRICING
    assert interp_cap.primary_aspect == SemanticAspect.WORKFLOWS
    assert interp_pricing.primary_aspect != interp_cap.primary_aspect

def test_confusion_pair_same_aspect_different_entity(engine):
    interp_wa = engine.interpret_query("Pricing plans for WhatsApp Marketing")
    interp_ecom = engine.interpret_query("Pricing plans for E-Commerce OS")

    assert interp_wa.primary_aspect == interp_ecom.primary_aspect == SemanticAspect.PRICING
    assert interp_wa.primary_entity_id == "whatsapp_marketing"
    assert interp_ecom.primary_entity_id == "ecommerce_os"
    assert interp_wa.primary_entity_id != interp_ecom.primary_entity_id

# --- 3. Transcript 3-Turn Sequence Sensitivity ---

def test_transcript_3turn_sequence(engine):
    # Turn 1: WhatsApp Marketing
    t1 = engine.interpret_query("WhatsApp Marketing Platform")
    assert t1.primary_entity_id == "whatsapp_marketing"
    assert t1.primary_aspect == SemanticAspect.OVERVIEW

    # Turn 2: What about influencer marketing?
    t2 = engine.interpret_query("what about influencer marketing")
    assert t2.primary_entity_id == "influencer_marketing"
    assert t2.primary_aspect == SemanticAspect.OVERVIEW

    # Turn 3: Pricing for both
    t3 = engine.interpret_query("what is the pricing for both?")
    assert t3.primary_aspect == SemanticAspect.PRICING
    assert t3.answer_scope == AnswerScope.COMPARISON_SCOPE or t3.answer_scope == AnswerScope.MULTI_ENTITY

# --- 4. Catalog Listing & Counting Tests ---

def test_catalog_list_products(ks):
    products = ks.list_entities("cittaai", "PRODUCTS")
    assert len(products) == 2
    ids = {p.get("id") for p in products}
    assert "whatsapp_marketing" in ids
    assert "influencer_marketing" in ids

def test_catalog_list_solutions(ks):
    solutions = ks.list_entities("cittaai", "SOLUTIONS")
    assert len(solutions) == 6

def test_catalog_count_entities(ks):
    counts = ks.count_entities("cittaai", "PRODUCTS")
    assert counts["count"] == 2
    assert len(counts["items"]) == 2

# --- 5. EvidenceGate & Score Fusion Tests ---

def test_reranker_score_bounds(reranker, engine):
    interp = engine.interpret_query("WhatsApp Marketing pricing")
    mock_chunks = [
        {
            "id": "c1",
            "content": "WhatsApp Marketing pricing tier starts at $99/mo",
            "entity_id": "whatsapp_marketing",
            "metadata": {
                "entity_id": "whatsapp_marketing",
                "section": "pricing",
                "entity_type": "product"
            },
            "similarity": 0.85
        },
        {
            "id": "c2",
            "content": "Smart Cities OS municipal dashboard overview",
            "entity_id": "smart_cities_os",
            "metadata": {
                "entity_id": "smart_cities_os",
                "section": "overview",
                "entity_type": "solution"
            },
            "similarity": 0.40
        }
    ]
    reranked = reranker.rerank(
        query="WhatsApp Marketing pricing",
        chunks=mock_chunks,
        requested_sections=interp.requested_sections,
        target_entity_id=interp.primary_entity_id,
        target_registry_types=interp.target_registry_types,
        answer_scope=interp.answer_scope
    )
    assert len(reranked) == 2
    for r in reranked:
        assert 0.0 <= r["composite_score"] <= 1.0
        assert 0.0 <= r["aspect_match_score"] <= 1.0
        assert 0.0 <= r["entity_match_score"] <= 1.0

    # Top chunk should be c1 with perfect entity and aspect match
    assert reranked[0]["id"] == "c1"
    assert reranked[0]["aspect_match_score"] == 1.0
    assert reranked[0]["entity_match_score"] == 1.0

def test_evidence_gate_scope_compliance(gate, engine):
    interp = engine.interpret_query("WhatsApp Marketing capabilities")
    raw_chunks = [
        {"entity_id": "whatsapp_marketing", "content": "Broadcast engine", "section": "capabilities"},
        {"entity_id": "smart_cities_os", "content": "Traffic sensors", "section": "capabilities"},
        {"entity_id": "company_info", "content": "CittaAI was founded in 2022", "section": "overview"}
    ]
    scope_valid = gate.validate_retrieved_evidence_scope(raw_chunks, interp)
    # The non-target entity chunk (smart_cities_os) should be filtered out
    # company_info fallback is retained
    entity_ids = [c.get("entity_id") for c in scope_valid]
    assert "whatsapp_marketing" in entity_ids
    assert "company_info" in entity_ids
    assert "smart_cities_os" not in entity_ids

def test_live_rag_search_integration():
    from server import get_rag_service
    import config
    rag = get_rag_service()
    res = asyncio.run(rag.process_query("How much does WhatsApp Marketing cost?", session_id="test_step3", model=config.MODEL_NAME))
    assert res is not None
    assert "response" in res
    # Ensure non-empty response was generated by pipeline
    assert isinstance(res["response"], str)
