"""
SemanticDecision contract and Canonicalization/Validation Gate for CittaAI.
Replaces monolithic QueryInterpretation fallback chain with structured per-field evidence.
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# Deterministic entity alias mapping
CANONICAL_ALIASES = {
    "healthcare_os": "pharma_os",
    "realty_os": "real_estate_os",
    "cittaai_company": "company_info",
    "cittaai": "company_info",
    "company": "company_info",
    "leadership": "company_info",
}


@dataclass
class FieldEvidence:
    value: Optional[str]
    confidence: float
    source: str  # "rules" | "bge" | "llm" | "context" | "none"
    margin: Optional[float] = None  # top1 - top2 similarity, if applicable

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticDecision:
    entity: FieldEvidence
    intent: FieldEvidence
    aspect: FieldEvidence
    scope: FieldEvidence
    entities: List[str] = field(default_factory=list)  # Populated when scope.value == "MULTI_ENTITY"
    overall_confidence: float = 1.0
    needs_clarification: bool = False
    needs_llm_adjudication: bool = False
    llm_invoked: bool = False
    raw_evidence: Dict[str, Any] = field(default_factory=dict)
    original_query: str = ""
    normalized_query: str = ""
    requested_sections: List[str] = field(default_factory=list)
    diagnostic_trace: List[str] = field(default_factory=list)
    clarification_options: List[Dict[str, str]] = field(default_factory=list)
    category_term_used_by_user: Optional[str] = None
    registry_category: Optional[str] = None
    target_registry_types: List[str] = field(default_factory=list)
    aspect_candidates: List[tuple] = field(default_factory=list)  # [(aspect, share)], best first
    aspect_llm_invoked: bool = False
    conversation_reference: Optional[str] = None  # set when the entity was carried from conversation context

    # Legacy QueryInterpretation attributes still read by phase2_orchestrator / rag_service
    @property
    def category_mismatch(self) -> bool:
        return bool(self.category_term_used_by_user and self.registry_category
                    and self.category_term_used_by_user != self.registry_category)

    @property
    def interpretation(self) -> str:
        return (f"entity={self.entity.value} ({self.entity.source}, conf={self.entity.confidence}), "
                f"aspect={self.aspect.value}, scope={self.scope.value}")

    @property
    def decision_confidence(self) -> float:
        """Weakest link across the fields that determine the answer (entity only counts when one is needed)."""
        parts = [self.scope.confidence, self.aspect.confidence]
        if self.entity.value:
            parts.append(self.entity.confidence)
        return round(min(p for p in parts if p is not None), 4)

    @property
    def is_out_of_domain(self) -> bool:
        return self.scope.value == "OUT_OF_DOMAIN"

    # Backwards-compatibility property accessors
    @property
    def primary_entity_id(self) -> Optional[str]:
        return self.entity.value

    @property
    def primary_intent(self) -> str:
        return self.intent.value or "UNKNOWN"

    @property
    def primary_aspect(self) -> str:
        return self.aspect.value or "OVERVIEW"

    @property
    def answer_scope(self) -> str:
        return self.scope.value or "GENERAL"

    @property
    def requires_clarification(self) -> bool:
        return self.needs_clarification

    @property
    def confidence(self) -> float:
        return self.overall_confidence

    def to_dict(self) -> Dict[str, Any]:
        """Returns a backward-compatible dictionary for downstream consumers."""
        d = {
            "entity": self.entity.value,
            "primary_entity": self.entity.value,
            "primary_entity_id": self.entity.value,
            "intent": self.intent.value or "UNKNOWN",
            "primary_intent": self.intent.value or "UNKNOWN",
            "aspect": self.aspect.value or "OVERVIEW",
            "primary_aspect": self.aspect.value or "OVERVIEW",
            "scope": self.scope.value or "GENERAL",
            "answer_scope": self.scope.value or "GENERAL",
            "entities": self.entities,
            "overall_confidence": self.overall_confidence,
            "confidence": self.overall_confidence,
            "needs_clarification": self.needs_clarification,
            "requires_clarification": self.needs_clarification,
            "needs_llm_adjudication": self.needs_llm_adjudication,
            "llm_invoked": self.llm_invoked,
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "requested_sections": self.requested_sections,
            "diagnostic_trace": self.diagnostic_trace,
            "raw_evidence": self.raw_evidence,
            "clarification_options": self.clarification_options,
            "category_mismatch": self.category_mismatch,
            "category_term_used_by_user": self.category_term_used_by_user,
            "registry_category": self.registry_category,
            "target_registry_types": self.target_registry_types,
            "entity_confidence": self.entity.confidence,
            "intent_confidence": self.intent.confidence,
            "aspect_confidence": self.aspect.confidence,
            "scope_confidence": self.scope.confidence,
            "aspect_top1": self.aspect_candidates[0][0] if self.aspect_candidates else self.aspect.value,
            "aspect_top2": self.aspect_candidates[1][0] if len(self.aspect_candidates) > 1 else None,
            "aspect_top2_confidence": self.aspect_candidates[1][1] if len(self.aspect_candidates) > 1 else 0.0,
            "aspect_margin": self.aspect.margin,
            "aspect_llm_invoked": self.aspect_llm_invoked,
            "decision_confidence": self.decision_confidence,
            "conversation_reference": self.conversation_reference,
            "interpretation": self.interpretation,
            "is_out_of_domain": self.is_out_of_domain,
            "query_text": self.normalized_query or self.original_query,
            "entity_evidence": self.entity.to_dict(),
            "intent_evidence": self.intent.to_dict(),
            "aspect_evidence": self.aspect.to_dict(),
            "scope_evidence": self.scope.to_dict(),
        }
        return d


def canonicalize_and_validate(decision: SemanticDecision, registry: Any) -> SemanticDecision:
    """
    Mandatory gate:
    1. Deterministically canonicalize entity.value via CANONICAL_ALIASES.
    2. Confirm entity exists in KnowledgeRegistry. If invalid, set entity.value=None, entity.confidence=0.0.
    3. Validate aspect against entity type/schema.
    4. If validation fails on a field that arbitration was confident about (>=0.70), flag needs_clarification=True.
    """
    raw_ent = decision.entity.value
    if raw_ent:
        # Deterministic alias mapping
        canonical_ent = CANONICAL_ALIASES.get(raw_ent.lower(), raw_ent)
        
        # Verify existence in registry
        ent_obj = None
        if hasattr(registry, "get_entity"):
            ent_obj = registry.get_entity(canonical_ent)
        
        # Check standard global entities
        known_global_entities = {
            "company_info", "leadership_info", "contact_info", "faq_general",
            "awards_recognition", "case_studies", "solutions_catalog", "products_catalog"
        }
        
        if ent_obj is not None:
            decision.entity.value = canonical_ent
        elif canonical_ent in known_global_entities:
            decision.entity.value = canonical_ent
        else:
            logger.warning(
                f"[Canonicalization Gate] Unrecognized entity '{raw_ent}' (canonical: '{canonical_ent}') not found in registry. Invalidating entity."
            )
            if decision.entity.confidence >= 0.70:
                decision.needs_clarification = True
                decision.diagnostic_trace.append(f"Validation failed on high-confidence entity '{raw_ent}'")
            decision.entity.value = None
            decision.entity.confidence = 0.0

    # Also canonicalize multi-entity list if present
    if decision.entities:
        validated_entities = []
        for ent in decision.entities:
            c_ent = CANONICAL_ALIASES.get(ent.lower(), ent)
            if (hasattr(registry, "get_entity") and registry.get_entity(c_ent)) or c_ent in known_global_entities:
                validated_entities.append(c_ent)
        decision.entities = validated_entities

    return decision
