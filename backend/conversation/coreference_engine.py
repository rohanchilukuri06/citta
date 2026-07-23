import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.conversation.models import (
    EntityNode,
    CoreferenceCandidate,
    CoreferenceResult,
    WorkingMemory,
    ConversationContext
)

logger = logging.getLogger(__name__)

PRONOUN_PATTERNS = {
    "singular": [r"\bit\b", r"\bthis\b", r"\bthat\b"],
    "plural": [r"\bthey\b", r"\bthem\b", r"\bthose\b", r"\bthese\b"]
}

class CoreferenceEngine:
    """
    Coreference and Anaphora Resolution Engine.
    Detects pronouns (it, they, that, this, those) and resolves them to candidate entities 
    from WorkingMemory and Entity Graph using confidence thresholding.
    """
    def __init__(self):
        pass

    def detect_pronouns(self, query: str) -> List[str]:
        """Detects presence of singular/plural pronouns in user query."""
        found = []
        q = query.lower()
        for p_type, patterns in PRONOUN_PATTERNS.items():
            for pat in patterns:
                for match in re.finditer(pat, q):
                    found.append(match.group(0))
        return found

    def resolve(
        self,
        query: str,
        working_memory: WorkingMemory,
        turn: int = 1
    ) -> CoreferenceResult:
        """
        Evaluates query pronouns against working memory and entity graph.
        Returns CoreferenceResult with candidate scores and threshold decisions.
        """
        pronouns = self.detect_pronouns(query)
        if not pronouns:
            # No pronouns detected; query requires no coreference rewrite
            return CoreferenceResult(
                original_query=query,
                resolved_query=query,
                selected_entity=working_memory.current_entity,
                candidates=[],
                pronouns_detected=[],
                confidence=1.0,
                requires_clarification=False
            )

        # Collect candidate entities from Working Memory & Recent Entities stack
        candidate_nodes: List[EntityNode] = []
        if working_memory.current_entity:
            candidate_nodes.append(working_memory.current_entity)
            
        for node in working_memory.recent_entities:
            if not working_memory.current_entity or node.entity_id != working_memory.current_entity.entity_id:
                candidate_nodes.append(node)

        if not candidate_nodes:
            # Check if query contains an explicit entity or topic keyword (e.g. ecommerce, pharma, sap, demo, pricing, leadership)
            explicit_keywords = ["ecommerce", "pharma", "sap", "pricing", "cost", "leadership", "hipaa", "security", "demo", "schedule", "compare", "ai"]
            has_explicit_topic = any(k in query.lower() for k in explicit_keywords)
            
            if has_explicit_topic:
                return CoreferenceResult(
                    original_query=query,
                    resolved_query=query,
                    selected_entity=None,
                    candidates=[],
                    pronouns_detected=pronouns,
                    confidence=0.85,
                    requires_clarification=False
                )

            # Pronouns found with no explicit topic and no active entities in memory -> Low confidence, trigger clarification
            return CoreferenceResult(
                original_query=query,
                resolved_query=query,
                selected_entity=None,
                candidates=[],
                pronouns_detected=pronouns,
                confidence=0.20,
                requires_clarification=True
            )

        # Score candidate entities based on recency and mention count
        candidates: List[CoreferenceCandidate] = []
        for idx, node in enumerate(candidate_nodes):
            # Recency factor
            recency_dist = turn - node.last_turn
            recency_score = max(0.40, 1.0 - (recency_dist * 0.15))
            
            # Mention count bonus
            mention_bonus = min(0.15, node.mention_count * 0.05)
            
            # Position penalty (current_entity is idx 0)
            position_penalty = idx * 0.20
            
            conf = min(1.0, max(0.10, recency_score + mention_bonus - position_penalty))
            
            reason = f"Entity '{node.name}' (mentions: {node.mention_count}, last_turn: {node.last_turn})"
            candidates.append(CoreferenceCandidate(entity=node, confidence=round(conf, 2), reason=reason))

        # Sort candidates descending by confidence
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        top_cand = candidates[0]
        top_conf = top_cand.confidence

        # Apply Threshold Policy:
        # >= 0.75: Auto-resolve
        # 0.45 <= conf < 0.75: Resolve with uncertainty
        # < 0.45: Clarification required
        requires_clarification = top_conf < 0.45
        
        resolved_query = query
        selected_entity = top_cand.entity if not requires_clarification else None

        if selected_entity:
            # Perform query rewriting replacing the primary pronoun with selected entity name
            for p in pronouns:
                # Replace whole word pronoun with entity name
                resolved_query = re.sub(rf"\b{re.escape(p)}\b", selected_entity.name, resolved_query, count=1, flags=re.IGNORECASE)

        logger.info(
            f"CoreferenceEngine: Original '{query}' -> Resolved '{resolved_query}' "
            f"(Selected: {selected_entity.name if selected_entity else 'None'}, Conf: {top_conf}, Clarification: {requires_clarification})"
        )

        return CoreferenceResult(
            original_query=query,
            resolved_query=resolved_query,
            selected_entity=selected_entity,
            candidates=candidates,
            pronouns_detected=pronouns,
            confidence=top_conf,
            requires_clarification=requires_clarification
        )


_coreference_engine_instance: Optional[CoreferenceEngine] = None

def get_coreference_engine() -> CoreferenceEngine:
    global _coreference_engine_instance
    if _coreference_engine_instance is None:
        _coreference_engine_instance = CoreferenceEngine()
    return _coreference_engine_instance
