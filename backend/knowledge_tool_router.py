"""
KnowledgeToolRouter for CittaAI Bounded Agentic Enterprise Knowledge Architecture.
Consumes a SemanticDecision (entity, aspect, scope, confidence) and maps it to operations in the
KnowledgeOperationRegistry. Routing is driven by the decision's canonical fields and the entity's
registry type, never by keywords in the raw query.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from knowledge_operation_registry import get_operation_registry, KnowledgeOperationRegistry
from knowledge_registry import get_registry

logger = logging.getLogger(__name__)

CATALOG_SCOPE_OPS = {
    "ALL_PRODUCTS": "list_products",
    "CATALOG_SCOPE": "list_products",
    "ALL_SOLUTIONS": "list_solutions",
    "ALL_SERVICES": "list_services",
    "ALL": "list_catalog",
}
COMPANY_ASPECT_OPS = {
    "CONTACT": "get_contact",
    "LEADERSHIP": "get_leadership",
    "RECOGNITION": "get_recognition",
    "CLIENTS_CASE_STUDIES": "list_case_studies",
}
ENTITY_ASPECT_OPS = {
    "CAPABILITIES": "get_capabilities",
    "FEATURES": "get_capabilities",
    "BENEFITS": "get_benefits",
    "TARGET_USERS": "get_target_users",
    "USE_CASES": "get_target_users",
    "WORKFLOW": "get_workflow",
    "WORKFLOWS": "get_workflow",
    "FAQ": "get_faq",
    "PRICING": "get_pricing",
}
# entity type -> (operation, input names that receive the entity id)
COMPANY_TYPE_OPS = {
    "case_study": ("get_case_study", ("entity_id",)),
    "award": ("get_recognition", ()),
    "contact": ("get_contact", ()),
    "leadership": ("get_leadership", ("person_id",)),
}
TYPE_OVERVIEW_OPS = {"product": "get_product", "solution": "get_solution", "service": "get_service", "company": "get_company_info"}
COMPANY_ENTITIES = {"company_info", "company", "cittaai_company", "contact_info", "leadership_info", "awards_recognition", "faq_general"}


@dataclass
class OperationRoutePlan:
    operation_name: str
    authoritative_source: str  # "KnowledgeRegistry" or "VectorStore"
    inputs: Dict[str, Any] = field(default_factory=dict)
    fallback_operation: Optional[str] = "semantic_search"
    confidence: float = 1.0
    reasoning: str = ""


class KnowledgeToolRouter:
    def __init__(self, operation_registry: Optional[KnowledgeOperationRegistry] = None):
        self.operation_registry = operation_registry or get_operation_registry()
        self.knowledge_registry = get_registry()

    def _entity_type(self, entity_id: Optional[str]) -> Optional[str]:
        if not entity_id:
            return None
        obj = self.knowledge_registry.get_entity(entity_id) if hasattr(self.knowledge_registry, "get_entity") else None
        if not obj:
            return None
        return str(obj.get("type") or obj.get("entity_type") or "").lower() or None

    def _plan(self, op_name: str, inputs: Dict[str, Any], confidence: float, reasoning: str) -> OperationRoutePlan:
        op = self.operation_registry.get_operation(op_name)
        source = op.authoritative_source if op else "KnowledgeRegistry"
        fallback = (op.execution_bounds or {}).get("fallback", "semantic_search") if op else "semantic_search"
        return OperationRoutePlan(op_name, source, inputs, fallback, confidence, reasoning)

    def route_query(self, query_intel: Any) -> List[OperationRoutePlan]:
        if hasattr(query_intel, "to_dict"):
            intel = query_intel.to_dict()
        elif isinstance(query_intel, dict):
            intel = query_intel
        else:
            intel = {}

        entity_id = intel.get("entity") or intel.get("primary_entity") or intel.get("primary_entity_id")
        entities = intel.get("entities") or []
        aspect = str(intel.get("aspect") or intel.get("primary_aspect") or intel.get("requested_section") or "OVERVIEW").upper()
        scope = intel.get("scope") or intel.get("answer_scope")
        confidence = float(intel.get("confidence", 1.0) or 0.0)
        query_text = intel.get("query_text") or intel.get("normalized_query") or intel.get("original_query") or ""

        # 1. Clarification
        if intel.get("needs_clarification") or intel.get("requires_clarification") or scope in (None, "NONE"):
            return [self._plan("request_clarification", {
                "reason": "Ambiguous query requiring user clarification.",
                "options": intel.get("clarification_options") or [],
            }, confidence, "Entity/scope ambiguous or below confidence floor.")]

        # 2. Named something that isn't in the catalog ("Finance OS")
        if scope == "UNKNOWN_ENTITY":
            return [self._plan("request_clarification", {
                "reason": "The user named an offering that is not in the catalog.",
                "unknown_entity": (intel.get("raw_evidence") or {}).get("signals", {}).get("unknown_product"),
                "options": [],
            }, confidence, "Unknown entity; never substitute a neighbouring entity.")]

        # 3. Out of domain
        if scope == "OUT_OF_DOMAIN":
            return [self._plan("decline_out_of_domain", {}, confidence, "Query is not about CittaAI or its offerings.")]

        # 3. Multi-entity fan-out (capped at 3 by the SufficiencyGate)
        if scope in ("MULTI_ENTITY", "MULTI_ENTITY_COMPARISON") and len(entities) >= 2:
            plans = []
            for ent in entities[:3]:
                # Compare the part that was asked about ("what do both cost?" -> get_pricing for each)
                op = ENTITY_ASPECT_OPS.get(aspect) or TYPE_OVERVIEW_OPS.get(self._entity_type(ent) or "solution", "get_solution")
                inputs = {"entity_id": ent}
                plans.append(self._plan(op, inputs, confidence, f"Multi-entity comparison fan-out for '{ent}'."))
            return plans

        # 4. Company-level aspects (contact, leadership, awards, clients)
        if aspect in COMPANY_ASPECT_OPS and (not entity_id or entity_id in COMPANY_ENTITIES or self._entity_type(entity_id) in ("leadership", "case_study", "award", "contact")):
            op = COMPANY_ASPECT_OPS[aspect]
            inputs: Dict[str, Any] = {}
            etype = self._entity_type(entity_id)
            if op == "get_leadership" and etype == "leadership" and entity_id != "leadership_info":
                inputs["person_id"] = entity_id
            if op == "list_case_studies" and etype == "case_study":
                op, inputs = "get_case_study", {"entity_id": entity_id}
            return [self._plan(op, inputs, confidence, f"Company-level aspect '{aspect}'.")]

        # 5. Catalog listing — only when no specific entity was resolved
        if not entity_id and scope in CATALOG_SCOPE_OPS:
            return [self._plan(CATALOG_SCOPE_OPS[scope], {}, confidence, f"Catalog scope '{scope}'.")]

        # 6. Single entity
        if entity_id:
            etype = self._entity_type(entity_id)
            if aspect in COMPANY_ASPECT_OPS:
                # e.g. "how do I contact you about WhatsApp marketing" -> contact, keep the entity as topic
                return [self._plan(COMPANY_ASPECT_OPS[aspect], {"topic_entity_id": entity_id}, confidence,
                                   f"Company aspect '{aspect}' about entity '{entity_id}'.")]
            # Company-level entities have one authoritative operation whatever part of them is asked about
            if etype in COMPANY_TYPE_OPS:
                op, inputs = COMPANY_TYPE_OPS[etype]
                inputs = {k: entity_id for k in inputs}
                return [self._plan(op, inputs, confidence, f"Company-level entity '{entity_id}' ({etype}).")]
            if entity_id in ("company_info", "company", "cittaai_company"):
                op = "get_company_info"
            elif aspect in ENTITY_ASPECT_OPS:
                op = ENTITY_ASPECT_OPS[aspect]
            else:
                op = TYPE_OVERVIEW_OPS.get(etype or "", "get_capabilities")
            op_def = self.operation_registry.get_operation(op)
            inputs = {}
            if op_def and ("entity_id" in op_def.required_inputs or "entity_id" in op_def.optional_inputs):
                inputs["entity_id"] = entity_id
            if op_def and "section" in op_def.optional_inputs:
                inputs["section"] = aspect
            return [self._plan(op, inputs, confidence, f"Entity '{entity_id}' ({etype}) with aspect '{aspect}'.")]

        # 7. Fallback: hybrid semantic search
        return [OperationRoutePlan(
            operation_name="semantic_search",
            authoritative_source="VectorStore",
            inputs={"query_text": query_text},
            fallback_operation=None,
            confidence=confidence,
            reasoning="No canonical entity or scope; defaulting to hybrid semantic search."
        )]
