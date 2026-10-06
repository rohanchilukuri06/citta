import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from orchestration_context import OrchestrationContext
from knowledge_registry import get_registry

logger = logging.getLogger(__name__)

class EntityEvidence(BaseModel):
    entity_id: str
    name: str
    category: Optional[Any] = None
    tagline: Optional[Any] = None
    overview: Optional[Any] = None
    how_it_works: Optional[Any] = None
    workflow: Optional[Any] = None
    features: Optional[Any] = None
    benefits: Optional[Any] = None
    capabilities: Optional[Any] = None
    best_for: Optional[Any] = None
    industries: Optional[Any] = None
    pricing: Optional[Any] = None
    integrations: Optional[Any] = None
    implementation: Optional[Any] = None
    case_studies: Optional[Any] = None
    related_entities: Optional[Any] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class EvidencePackage(BaseModel):
    session_id: str
    query: str
    entities: Dict[str, EntityEvidence] = Field(default_factory=dict)
    category_summary: Dict[str, Any] = Field(default_factory=dict)
    available_sections_by_entity: Dict[str, List[str]] = Field(default_factory=dict)
    total_sections_count: int = 0

class EvidenceBuilder:
    def __init__(self):
        self.reg = get_registry()

    def build_package(self, ctx: OrchestrationContext) -> EvidencePackage:
        target_ids = []
        if ctx.resolved_entity_id:
            target_ids.append(ctx.resolved_entity_id)
        if ctx.matched_entity_ids:
            target_ids.extend(ctx.matched_entity_ids)
        if ctx.session_state.recently_compared_entities:
            target_ids.extend(ctx.session_state.recently_compared_entities)

        # Include contact_info & company_info for consultative, onboarding, contact, and collaboration queries
        q_lower = ctx.original_query.lower()
        if any(w in q_lower for w in ["collaborate", "proceed", "partner", "contact", "get started", "touch", "talk", "sales", "onboard", "work together"]):
            if "contact_info" in self.reg.entities:
                target_ids.append("contact_info")
            if "company_info" in self.reg.entities:
                target_ids.append("company_info")
            
        # Deduplicate entity IDs
        target_ids = list(dict.fromkeys(target_ids))

        package = EvidencePackage(
            session_id=ctx.session_id,
            query=ctx.original_query
        )

        for ent_id in target_ids:
            if ent_id in self.reg.entities:
                raw_ent = self.reg.entities[ent_id]
                sections = []
                for sec in ["overview", "how_it_works", "workflow", "features", "benefits", "capabilities", "best_for", "pricing", "integrations", "implementation", "case_studies", "related_entities"]:
                    if raw_ent.get(sec):
                        sections.append(sec)

                ev = EntityEvidence(
                    entity_id=ent_id,
                    name=raw_ent.get("name") or raw_ent.get("title") or ent_id,
                    category=raw_ent.get("category") or raw_ent.get("type"),
                    tagline=raw_ent.get("tagline"),
                    overview=raw_ent.get("overview") or raw_ent.get("description"),
                    how_it_works=raw_ent.get("how_it_works"),
                    workflow=raw_ent.get("workflow"),
                    features=raw_ent.get("features"),
                    benefits=raw_ent.get("benefits"),
                    capabilities=raw_ent.get("capabilities"),
                    best_for=raw_ent.get("best_for") or raw_ent.get("target_audience"),
                    industries=raw_ent.get("industries") or raw_ent.get("best_for"),
                    pricing=raw_ent.get("pricing"),
                    integrations=raw_ent.get("integrations"),
                    implementation=raw_ent.get("implementation"),
                    case_studies=raw_ent.get("case_studies"),
                    related_entities=raw_ent.get("related_entities"),
                    raw_data=raw_ent
                )
                package.entities[ent_id] = ev
                package.available_sections_by_entity[ent_id] = sections
                package.total_sections_count += len(sections)

        ctx.add_trace(
            stage="EvidenceBuilder",
            result=f"Built EvidencePackage with {len(package.entities)} entities",
            reason=f"Entities packaged: {list(package.entities.keys())}"
        )

        return package

_evidence_builder_instance = None

def get_evidence_builder() -> EvidenceBuilder:
    global _evidence_builder_instance
    if _evidence_builder_instance is None:
        _evidence_builder_instance = EvidenceBuilder()
    return _evidence_builder_instance
