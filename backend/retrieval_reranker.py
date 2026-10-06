import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class HybridRetrievalReranker:
    def __init__(self, vector_store=None):
        self.vector_store = vector_store

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_n: int = 5,
        domain_filter: Optional[str] = None,
        requested_sections: Optional[List[str]] = None,
        target_entity_id: Optional[str] = None,
        target_registry_types: Optional[List[str]] = None,
        answer_scope: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        q_terms = [t for t in query.lower().split() if len(t) > 2]
        scored_chunks = []

        # Adjacent section relevance matrix for graded matching
        ADJACENT_SECTIONS = {
            "benefits": ["capabilities", "overview"],
            "capabilities": ["workflows", "overview", "features"],
            "workflows": ["capabilities", "overview"],
            "target_users": ["overview", "cases"],
            "pricing": ["overview"],
            "contact": ["overview"],
            "cases": ["target_users", "overview"],
            "awards": ["overview"]
        }

        for idx, chunk in enumerate(chunks):
            content = chunk.get("content", "").lower()
            meta = chunk.get("metadata", {})
            
            # 1. Bounded Semantic Score [0.0, 1.0]
            raw_sem = chunk.get("semantic_score", chunk.get("score", 0.5))
            semantic_score = float(min(1.0, max(0.0, raw_sem)))

            # 2. Bounded Lexical Score [0.0, 1.0]
            if q_terms:
                term_matches = sum(1 for term in q_terms if term in content)
                lexical_score = float(min(1.0, term_matches / len(q_terms)))
            else:
                lexical_score = 0.0

            # 3. Graded Aspect Match Score [0.0, 1.0]
            chunk_sec = str(meta.get("section", "")).strip().lower()
            chunk_reg_type = str(meta.get("entity_type", meta.get("domain", ""))).strip().upper()

            aspect_score = 0.0
            if target_registry_types and any(rt.upper() in chunk_reg_type for rt in target_registry_types):
                aspect_score = 1.00
            elif requested_sections and chunk_sec:
                if any(sec.lower() == chunk_sec for sec in requested_sections):
                    aspect_score = 1.00
                elif any(chunk_sec in ADJACENT_SECTIONS.get(sec.lower(), []) for sec in requested_sections):
                    aspect_score = 0.55
                elif chunk_sec == "overview":
                    aspect_score = 0.35

            # 4. Bounded Entity Match Score [0.0, 1.0]
            chunk_eid = str(meta.get("entity_id", "")).strip().lower()
            if target_entity_id and chunk_eid:
                entity_score = 1.00 if (target_entity_id.lower() in chunk_eid or chunk_eid in target_entity_id.lower()) else 0.00
            else:
                entity_score = 0.00

            # Bounded Composite Fusion Formula: 0.60 Semantic + 0.20 Lexical + 0.10 Aspect + 0.10 Entity
            final_score = (0.60 * semantic_score) + (0.20 * lexical_score) + (0.10 * aspect_score) + (0.10 * entity_score)
            final_score = float(min(1.0, max(0.0, final_score)))

            chunk_copy = chunk.copy()
            chunk_copy["final_rerank_score"] = final_score
            chunk_copy["composite_score"] = final_score
            chunk_copy["aspect_score"] = aspect_score
            chunk_copy["aspect_match_score"] = aspect_score
            chunk_copy["entity_score"] = entity_score
            chunk_copy["entity_match_score"] = entity_score
            scored_chunks.append(chunk_copy)

        # Deterministic Ranking: final_rerank_score DESC, semantic_score DESC, id ASC
        scored_chunks.sort(key=lambda x: (-x["final_rerank_score"], -x.get("semantic_score", 0.0), str(x.get("id", ""))))

        # Select Top-N unique chunks with Scope Diversification
        unique_results = []
        seen_texts = set()
        seen_entities = set()

        is_diversified_scope = answer_scope in ["CLIENTS_SCOPE", "MULTI_ENTITY_COMPARISON", "RECOGNITION_SCOPE"]

        for item in scored_chunks:
            norm_t = item["content"].strip().lower()
            item_eid = item.get("metadata", {}).get("entity_id") or item.get("id")

            if norm_t in seen_texts:
                continue

            # Enforce Entity Diversification for broad multi-entity scopes
            if is_diversified_scope and item_eid and item_eid in seen_entities and len(unique_results) < 3:
                continue

            seen_texts.add(norm_t)
            if item_eid:
                seen_entities.add(item_eid)

            unique_results.append(item)
            if len(unique_results) == top_n:
                break

        # Fallback if diversification was too restrictive
        if len(unique_results) < top_n and len(scored_chunks) > len(unique_results):
            for item in scored_chunks:
                norm_t = item["content"].strip().lower()
                if norm_t not in seen_texts:
                    seen_texts.add(norm_t)
                    unique_results.append(item)
                    if len(unique_results) == top_n:
                        break

        logger.info(f"Hybrid Reranker: {len(chunks)} candidates -> {len(unique_results)} reranked top chunks (scope={answer_scope}).")
        return unique_results

_reranker_instance = None

def get_retrieval_reranker(vector_store=None) -> HybridRetrievalReranker:
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = HybridRetrievalReranker(vector_store=vector_store)
    return _reranker_instance
