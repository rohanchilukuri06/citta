"""
Phase 5.5 Evidence Gate Component.
Determines evidence sufficiency, checks requested sections against verified registry facts,
and produces grounded evidence context to prevent LLM hallucinations or unsupported claims.
"""
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from knowledge_registry import get_registry

logger = logging.getLogger(__name__)

@dataclass
class EvidenceContext:
    entity_id: Optional[str]
    entity_name: Optional[str]
    requested_sections: List[str]
    available_sections: List[str]
    missing_sections: List[str]
    sufficiency: str  # "SUFFICIENT", "PARTIAL", "INSUFFICIENT"
    verified_content: Dict[str, Any] = field(default_factory=dict)
    formatted_context_block: str = ""
    missing_section_disclaimer: str = ""
    grounding_mandate: str = ""

class EvidenceGate:
    """
    Evidence Gate Component:
    Evaluates retrieved registry evidence against requested entities and sections.
    Enforces that CittaAI Knowledge Registry is the sole source of truth and prevents LLM halluncinations.
    """
    def __init__(self):
        self.registry = get_registry()

    def evaluate_evidence(
        self,
        entity_id: Optional[str],
        requested_sections: List[str],
        query_text: str = ""
    ) -> EvidenceContext:
        """
        Evaluates whether verified registry evidence is sufficient to answer requested sections for an entity.
        """
        if not entity_id or not hasattr(self.registry, "get_entity"):
            return EvidenceContext(
                entity_id=None,
                entity_name=None,
                requested_sections=requested_sections,
                available_sections=[],
                missing_sections=requested_sections,
                sufficiency="INSUFFICIENT",
                formatted_context_block="",
                missing_section_disclaimer="I don't have verified information about this request in my current CittaAI knowledge base."
            )

        ent_obj = self.registry.get_entity(entity_id)
        if not ent_obj:
            return EvidenceContext(
                entity_id=entity_id,
                entity_name=entity_id.replace("_", " ").title(),
                requested_sections=requested_sections,
                available_sections=[],
                missing_sections=requested_sections,
                sufficiency="INSUFFICIENT",
                missing_section_disclaimer=f"I don't have verified information about {entity_id.replace('_', ' ').title()} in my current CittaAI knowledge base."
            )

        ent_name = ent_obj.get("name") or ent_obj.get("title") or entity_id.replace("_", " ").title()
        
        available_sections = []
        missing_sections = []
        verified_content = {}

        for sec in requested_sections:
            content = self._extract_section_content(ent_obj, sec)
            if content and len(str(content).strip()) > 10:
                available_sections.append(sec)
                verified_content[sec] = content
            else:
                missing_sections.append(sec)

        # Determine sufficiency status
        if not available_sections:
            sufficiency = "INSUFFICIENT"
        elif not missing_sections:
            sufficiency = "SUFFICIENT"
        else:
            sufficiency = "PARTIAL"

        # Build disclaimer for missing sections
        disclaimer_parts = []
        for missing_sec in missing_sections:
            readable_sec = missing_sec.replace("_", " ")
            disclaimer_parts.append(
                f"I don't have verified information about the specific {readable_sec} of {ent_name} in my current CittaAI knowledge base."
            )
        missing_disclaimer = " ".join(disclaimer_parts)

        # Build formatted context block for LLM
        formatted_block, grounding_mandate = self._build_grounded_context_block(
            ent_name=ent_name,
            entity_id=entity_id,
            verified_content=verified_content,
            available_sections=available_sections,
            missing_sections=missing_sections,
            missing_disclaimer=missing_disclaimer,
            sufficiency=sufficiency
        )

        return EvidenceContext(
            entity_id=entity_id,
            entity_name=ent_name,
            requested_sections=requested_sections,
            available_sections=available_sections,
            missing_sections=missing_sections,
            sufficiency=sufficiency,
            verified_content=verified_content,
            formatted_context_block=formatted_block,
            missing_section_disclaimer=missing_disclaimer,
            grounding_mandate=grounding_mandate
        )

    def evaluate_multi_entity_evidence(
        self,
        entity_ids: List[str],
        requested_sections: List[str]
    ) -> EvidenceContext:
        """Evaluates evidence across multiple entities for multi-entity comparison or summary."""
        combined_content = {}
        all_available = []
        all_missing = []
        ent_names = []

        for ent_id in entity_ids:
            ctx = self.evaluate_evidence(ent_id, requested_sections)
            if ctx.entity_name:
                ent_names.append(ctx.entity_name)
            if ctx.verified_content:
                combined_content[ent_id] = {
                    "name": ctx.entity_name,
                    "content": ctx.verified_content
                }
            all_available.extend(ctx.available_sections)
            all_missing.extend(ctx.missing_sections)

        sufficiency = "SUFFICIENT" if combined_content and not all_missing else ("PARTIAL" if combined_content else "INSUFFICIENT")
        
        lines = [f"=== VERIFIED CITTAAI EVIDENCE FOR MULTI-ENTITY INQUIRY: {', '.join(ent_names)} ==="]
        for ent_id, data in combined_content.items():
            lines.append(f"\n--- ENTITY: {data['name']} ---")
            for sec, content in data["content"].items():
                lines.append(f"[{sec.upper()}]")
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            t = item.get("title") or item.get("name") or ""
                            d = item.get("description") or item.get("subtitle") or ""
                            lines.append(f"- {t}: {d}" if d else f"- {t}")
                        else:
                            lines.append(f"- {item}")
                else:
                    lines.append(str(content))

        block = "\n".join(lines)
        mandate = (
            "STRICT MULTI-ENTITY GROUNDING MANDATE:\n"
            "Answer using ONLY the verified evidence provided above. Compare or detail the entities clearly without inventing features or capabilities."
        )

        return EvidenceContext(
            entity_id="multi_entity",
            entity_name=", ".join(ent_names),
            requested_sections=requested_sections,
            available_sections=list(set(all_available)),
            missing_sections=list(set(all_missing)),
            sufficiency=sufficiency,
            verified_content=combined_content,
            formatted_context_block=block,
            missing_section_disclaimer="",
            grounding_mandate=mandate
        )

    def _extract_section_content(self, ent_obj: Dict[str, Any], section: str) -> Optional[Any]:
        """Extracts section content from entity JSON using schema-aware property mapping."""
        sec_lower = section.lower()
        if sec_lower in ["overview", "description"]:
            return ent_obj.get("overview") or ent_obj.get("description")
        elif sec_lower in ["capabilities", "features", "modules"]:
            return ent_obj.get("capabilities") or ent_obj.get("features")
        elif sec_lower in ["target_users", "users", "audience"]:
            return ent_obj.get("target_users")
        elif sec_lower in ["how_it_works", "workflows", "implementation"]:
            return ent_obj.get("workflows") or ent_obj.get("implementation") or ent_obj.get("architecture")
        elif sec_lower == "benefits":
            return ent_obj.get("benefits") or ent_obj.get("value_props")
        elif sec_lower == "pricing":
            return ent_obj.get("pricing")
        elif sec_lower in ["contact", "support"]:
            return ent_obj.get("contact")
        return ent_obj.get(sec_lower)

    def _build_grounded_context_block(
        self,
        ent_name: str,
        entity_id: str,
        verified_content: Dict[str, Any],
        available_sections: List[str],
        missing_sections: List[str],
        missing_disclaimer: str,
        sufficiency: str
    ) -> Tuple[str, str]:
        lines = [f"=== VERIFIED CITTAAI KNOWLEDGE BASE EVIDENCE FOR: {ent_name} ==="]
        for sec, text in verified_content.items():
            lines.append(f"\n[{sec.upper()} SECTION]")
            if isinstance(text, list):
                for item in text:
                    if isinstance(item, dict):
                        t = item.get("title") or item.get("name") or item.get("id") or ""
                        d = item.get("description") or item.get("subtitle") or ""
                        lines.append(f"- {t}: {d}" if d else f"- {t}")
                    else:
                        lines.append(f"- {item}")
            else:
                lines.append(str(text))

        if missing_sections:
            lines.append(f"\n[UNAVAILABLE SECTIONS IN KNOWLEDGE BASE]")
            lines.append(missing_disclaimer)

        mandate = (
            "STRICT EVIDENCE GROUNDING MANDATE:\n"
            "1. Answer ONLY using the verified knowledge base evidence supplied above.\n"
            "2. DO NOT fill missing information with general world knowledge, generic marketing concepts, or unverified vendor assumptions.\n"
        )
        if missing_sections:
            mandate += f"3. For missing sections ({', '.join(missing_sections)}), explicitly state: '{missing_disclaimer}'\n"
        
        return "\n".join(lines), mandate

_evidence_gate_instance = None

def get_evidence_gate() -> EvidenceGate:
    global _evidence_gate_instance
    if _evidence_gate_instance is None:
        _evidence_gate_instance = EvidenceGate()
    return _evidence_gate_instance
