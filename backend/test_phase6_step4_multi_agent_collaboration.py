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
from query_intelligence_engine import QueryIntelligenceEngine
from evidence_gate import EvidenceGate, get_evidence_gate
from phase6_collaboration_engine import Phase6CollaborationEngine, get_phase6_collaboration_engine
from orchestration_context import OrchestrationContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================================
# TEST SECTION 1: ASPECT-AWARE EVIDENCE GATE RERANKING TEST
# =====================================================================

def test_01_evidence_gate_reranking_formula():
    """Verify that EvidenceGate.evaluate_and_rerank calculates multi-factor score and filters out low confidence chunks."""
    gate = get_evidence_gate()

    sample_chunks = [
        {
            "id": "chunk_1",
            "content": "E-Commerce OS Overview and features for retail merchants.",
            "semantic_score": 0.85,
            "keyword_score": 0.50,
            "metadata": {"entity_id": "ecommerce_os", "category": "ecommerce_os", "section": "overview", "domain": "solutions"}
        },
        {
            "id": "chunk_2",
            "content": "Pharma OS Capabilities for hospital management.",
            "semantic_score": 0.80,
            "keyword_score": 0.40,
            "metadata": {"entity_id": "pharma_os", "category": "pharma_os", "section": "capabilities", "domain": "solutions"}
        },
        {
            "id": "chunk_3",
            "content": "Low relevance noise chunk.",
            "semantic_score": 0.10,
            "keyword_score": 0.0,
            "metadata": {"entity_id": "unknown", "category": "general", "section": "general", "domain": "general"}
        }
    ]

    reranked = gate.evaluate_and_rerank(
        chunks=sample_chunks,
        requested_sections=["capabilities"],
        primary_entity_id="pharma_os",
        min_confidence_threshold=0.35
    )

    assert len(reranked) >= 1, "Reranking filtered out all chunks unexpectedly"
    # Pharma OS chunk should be rank #1 because of domain match (+0.25) and section match (+0.15)
    top_chunk = reranked[0]
    assert top_chunk["metadata"]["entity_id"] == "pharma_os", f"Expected pharma_os rank #1, got {top_chunk['metadata']['entity_id']}"
    assert top_chunk["domain_match_boost"] == 1.0
    assert top_chunk["section_match_boost"] == 1.0

    # Low relevance noise chunk should be filtered out by min_confidence_threshold (0.35)
    filtered_ids = [c["id"] for c in reranked]
    assert "chunk_3" not in filtered_ids, "Low-confidence noise chunk should have been filtered out"

# =====================================================================
# TEST SECTION 2: MULTI-AGENT COLLABORATION ENGINE TEST
# =====================================================================

def test_02_phase6_collaboration_engine():
    """Verify that Phase6CollaborationEngine invokes AgentOrchestrator and synthesizes agent results."""
    async def _run():
        engine = get_phase6_collaboration_engine()
        ctx = OrchestrationContext(
            session_id="test_collab_session",
            original_query="Compare Pharma OS capabilities with E-Commerce OS pricing",
            normalized_query="compare pharma os capabilities with ecommerce os pricing",
            resolved_entity_id="pharma_os",
            resolved_entity_name="Pharma & Healthcare OS"
        )
        return await engine.execute_collaboration_pipeline(ctx)

    res = asyncio.run(_run())
    assert "text" in res or "consensus_score" in res, f"Expected valid collaboration response, got: {res}"
    assert res.get("metrics", {}).get("participating_agents") is not None, "Participating agents metric missing"
    logger.info(f"Collaboration Engine Test Passed! Participating agents: {res.get('metrics', {}).get('participating_agents')}")

# =====================================================================
# TEST SECTION 3: CROSS-ENTITY & MULTI-ASPECT RETRIEVAL BENCHMARK
# =====================================================================

def test_03_multi_aspect_retrieval_fusion():
    """Verify multi-aspect queries retrieve grounded evidence across multiple target sections."""
    vstore = VectorStore(config.VECTOR_DB_PATH)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(config.EMBEDDING_MODEL)

    query = "What are the capabilities and benefits of Education OS?"
    qi = QueryIntelligenceEngine()
    interp = qi.analyze_query(query)

    assert "capabilities" in interp.requested_sections or "benefits" in interp.requested_sections

    processed_text = f"Represent this sentence for searching relevant passages: {query}"
    emb = model.encode(processed_text, normalize_embeddings=True).tolist()

    raw_results = vstore.query_hybrid(
        query_text=query,
        query_embedding=emb,
        top_k=8,
        domain="education_os",
        requested_sections=interp.requested_sections
    )

    gate = get_evidence_gate()
    reranked = gate.evaluate_and_rerank(
        raw_results,
        requested_sections=interp.requested_sections,
        primary_entity_id="education_os"
    )

    assert len(reranked) > 0, "No reranked results for Education OS multi-aspect query"
    top_sec = reranked[0].get("metadata", {}).get("section")
    assert top_sec in ["capabilities", "benefits", "overview", "hero"], f"Unexpected top section: {top_sec}"

# =====================================================================
# TEST SECTION 4: STEP 2, STEP 3, & STEP 4 FULL REGRESSION BENCHMARK
# =====================================================================

def test_04_full_phase6_regression_benchmark():
    """Re-run Step 2 & Step 3 benchmark suites to confirm zero regression across all tests."""
    from test_phase6_step3_semantic_query_intelligence import (
        test_01_semantic_entity_discovery,
        test_02_aspect_extraction_and_section_boosting,
        test_03_run_phase6_step2_benchmark_regression,
        SEMANTIC_DISCOVERY_TEST_CASES,
        ASPECT_BOOST_TEST_CASES
    )

    for query, expected_entity in SEMANTIC_DISCOVERY_TEST_CASES:
        test_01_semantic_entity_discovery(query, expected_entity)

    for query, expected_entity, expected_sections in ASPECT_BOOST_TEST_CASES:
        test_02_aspect_extraction_and_section_boosting(query, expected_entity, expected_sections)

    test_03_run_phase6_step2_benchmark_regression()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
