import pytest
from query_normalizer import normalize_query_pipeline
from phase2_orchestrator import check_general_catalog_query, ExecutionStrategy
from conversation_context_resolver import ConversationContextResolver
from orchestration_context import OrchestrationContext
from knowledge_service import KnowledgeService


def test_query_normalizer_preserves_all():
    res = normalize_query_pipeline("List all products", vocabulary={}, abbreviations={})
    assert res["normalized_query"] == "list all products"
    assert "call" not in res["normalized_query"]


def test_deterministic_engine_list_all_products():
    matched = check_general_catalog_query("List all products")
    assert matched is True
    
    # Verify KnowledgeService returns both products
    ks = KnowledgeService()
    entities = ks.list_entities("cittaai", "PRODUCTS")
    entity_ids = [e["id"] for e in entities]
    assert "whatsapp_marketing" in entity_ids
    assert "influencer_marketing" in entity_ids


def test_conversational_follow_up_single_entity_resolution():
    resolver = ConversationContextResolver()
    
    # Turn 1: List products
    ctx1 = OrchestrationContext(original_query="List all products", normalized_query="list all products", session_id="test_transcript_sess")
    res1 = resolver.resolve_context(ctx1)
    assert res1.resolved_entity_id is None
    
    # Turn 2: Follow-up on influencer marketing
    query2 = "only whatsapp marketing then what about influencer markerting"
    ctx2 = OrchestrationContext(original_query=query2, normalized_query="only whatsapp marketing then what about influencer marketing", session_id="test_transcript_sess")
    res2 = resolver.resolve_context(ctx2, detected_entity_id="influencer_marketing", detected_entities=["whatsapp_marketing", "influencer_marketing"])
    
    # Verify it does not populate stale multi-entity comparison list when there's no explicit comparison
    assert res2.session_state.recently_compared_entities == []
