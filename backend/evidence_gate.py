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

    def validate_retrieved_evidence_scope(
        self,
        chunks: List[Dict[str, Any]],
        target_entity_id: Any,
        answer_scope: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Phase 6 Step 3 Triple-Validation (Scope & Entity Compliance):
        Ensures retrieved evidence chunks adhere strictly to the target entity and answer scope,
        preventing non-target entity evidence leakage in single-entity queries.
        """
        if not chunks:
            return []

        # Handle QueryInterpretation object passed directly
        if hasattr(target_entity_id, "primary_entity_id"):
            answer_scope = getattr(target_entity_id, "answer_scope", answer_scope)
            target_entity_id = getattr(target_entity_id, "primary_entity_id", None)

        if answer_scope == "CLIENTS_SCOPE":
            filtered = []
            for chunk in chunks:
                meta = chunk.get("metadata", {})
                chunk_eid = str(chunk.get("entity_id") or meta.get("entity_id", "")).lower().strip()
                reg_type = str(meta.get("entity_type") or meta.get("category") or "").upper().strip()
                if reg_type in ["CASE_STUDIES", "CASE_STUDY"] or "case" in chunk_eid or chunk_eid in ["company_info", "contact_info"]:
                    filtered.append(chunk)
            return filtered if filtered else chunks

        if answer_scope == "RECOGNITION_SCOPE":
            filtered = []
            for chunk in chunks:
                meta = chunk.get("metadata", {})
                chunk_eid = str(chunk.get("entity_id") or meta.get("entity_id", "")).lower().strip()
                reg_type = str(meta.get("entity_type") or meta.get("category") or "").upper().strip()
                if reg_type in ["RECOGNITION", "AWARDS"] or "award" in chunk_eid or chunk_eid in ["company_info", "contact_info"]:
                    filtered.append(chunk)
            return filtered if filtered else chunks

        if answer_scope in ["SINGLE_ENTITY", "GENERAL"] and target_entity_id:
            filtered = []
            target_clean = str(target_entity_id).lower().strip()
            for chunk in chunks:
                meta = chunk.get("metadata", {})
                chunk_eid = str(chunk.get("entity_id") or meta.get("entity_id", "")).lower().strip()

                # Allow target entity chunks, generic company/contact/faq chunks, or content.js general copy
                if not chunk_eid or chunk_eid in ["company_info", "contact_info", "faq_general", "location_info"] or target_clean in chunk_eid or chunk_eid in target_clean:
                    filtered.append(chunk)
                else:
                    logger.info(f"[EvidenceGate] Filtered non-target entity chunk '{chunk_eid}' for single-entity target '{target_clean}'.")

            return filtered if filtered else chunks

        return chunks

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

    def evaluate_and_rerank(
        self,
        chunks: List[Dict[str, Any]],
        requested_sections: Optional[List[str]] = None,
        primary_entity_id: Optional[str] = None,
        min_confidence_threshold: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Aspect-Aware Evidence Gate Reranking:
        Reranks retrieved candidate chunks using multi-factor formula:
          FinalScore = (0.50 * SemanticScore) + (0.25 * DomainMatch) + (0.15 * SectionMatch) + (0.10 * KeywordScore)
        Filters out low-confidence evidence chunks (< min_confidence_threshold).
        """
        if not chunks:
            return []

        SECTION_ALIASES = {
            "workflows": ["workflows", "how_it_works", "process", "implementation", "hero"],
            "how_it_works": ["workflows", "how_it_works", "process", "implementation"],
            "capabilities": ["capabilities", "features", "specs", "hero"],
            "benefits": ["benefits", "why_us"],
            "overview": ["overview", "hero", "about_lead", "about_story", "brand"],
            "target_users": ["target_users", "audience"],
            "pricing": ["pricing", "cost"],
            "contact": ["contact", "contact_info", "location"],
            "faq": ["faq"],
            "case_study": ["cases", "case_study", "case_studies"],
            "recognition": ["awards", "recognition"]
        }

        reranked = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            sem_score = float(chunk.get("semantic_score", chunk.get("score", 0.0)))
            kw_score = float(chunk.get("keyword_score", 0.0))

            # Domain Match check
            domain_match = 0.0
            if primary_entity_id:
                p_id = primary_entity_id.strip().lower()
                c_eid = str(meta.get("entity_id", "")).strip().lower()
                c_cat = str(meta.get("category", "")).strip().lower()
                c_dom = str(chunk.get("derived_domain", meta.get("domain", ""))).strip().lower()

                if (p_id in c_eid or c_eid in p_id) or (p_id in c_cat or c_cat in p_id) or (p_id in c_dom or c_dom in p_id):
                    domain_match = 1.0

            # Section Match check
            section_match = 0.0
            c_sec = str(meta.get("section", "")).strip().lower()
            if requested_sections and c_sec:
                for req_s in requested_sections:
                    s_clean = str(req_s).strip().lower()
                    if not s_clean:
                        continue
                    if s_clean in c_sec or c_sec in s_clean:
                        section_match = 1.0
                        break
                    aliases = SECTION_ALIASES.get(s_clean, [])
                    if any(a in c_sec or c_sec in a for a in aliases):
                        section_match = 1.0
                        break

            final_score = (0.50 * sem_score) + (0.25 * domain_match) + (0.15 * section_match) + (0.10 * kw_score)
            final_score = round(min(1.0, max(0.0, final_score)), 4)

            if final_score >= min_confidence_threshold:
                chunk_copy = dict(chunk)
                chunk_copy["reranked_score"] = final_score
                chunk_copy["score"] = final_score
                chunk_copy["domain_match_boost"] = domain_match
                chunk_copy["section_match_boost"] = section_match
                reranked.append(chunk_copy)

        reranked.sort(key=lambda x: (-x["reranked_score"], -x.get("semantic_score", 0.0)))
        return reranked

_evidence_gate_instance = None

def get_evidence_gate() -> EvidenceGate:
    global _evidence_gate_instance
    if _evidence_gate_instance is None:
        _evidence_gate_instance = EvidenceGate()
    return _evidence_gate_instance
