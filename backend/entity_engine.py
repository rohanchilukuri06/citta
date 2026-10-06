import re
import logging
from typing import Dict, Any, Tuple, Optional, List
from rapidfuzz import process, fuzz

from knowledge_service import get_knowledge_service

logger = logging.getLogger(__name__)

CONTEXT_PRONOUNS = {"it", "its", "this", "that", "the product", "the service", "the solution", "the platform", "this platform"}
ROLE_TRIGGERS = {"ceo", "cto", "coo", "cmo", "founder", "vinay", "akhil", "saladi", "ganesh"}

class EntityEngine:
    def __init__(self):
        self.ks = get_knowledge_service()

    def resolve_entity(
        self,
        query: str,
        tenant_id: str = "cittaai",
        active_entity_id: Optional[str] = None,
        confidence_threshold: float = 80.0
    ) -> Tuple[Optional[str], float, Optional[Dict[str, Any]]]:
        """
        Layered Entity Resolution:
        1. Context Pronoun Check
        2. Role / Person Lookup First (for executive queries)
        3. Direct KnowledgeService Entity Lookup
        4. RapidFuzz Match
        5. Active Entity Context Fallback
        """
        q_lower = query.lower().strip()

        # 1. Pronoun check
        if active_entity_id and (q_lower in CONTEXT_PRONOUNS or any(p in q_lower for p in CONTEXT_PRONOUNS)):
            return active_entity_id, 1.0, None

        # 2. Executive Person Lookup FIRST if query refers to an executive role
        if q_lower in ROLE_TRIGGERS or any(r in q_lower.split() for r in ROLE_TRIGGERS):
            person = self.ks.find_people(tenant_id, q_lower)
            if person:
                return person["id"], 1.0, None

        # 3. Direct KnowledgeService Entity Lookup
        ent = self.ks.find_entity(tenant_id, q_lower)
        if ent:
            return ent["id"], 1.0, None

        # 4. RapidFuzz match across all entity names and aliases
        all_entities = self.ks.reg.entities
        candidate_strings = []
        string_to_entity_id = {}

        for ent_id, ent_data in all_entities.items():
            name = (ent_data.get("name") or ent_data.get("title") or "").lower()
            if name:
                candidate_strings.append(name)
                string_to_entity_id[name] = ent_id
            for alias in ent_data.get("aliases", []):
                a_str = str(alias).lower()
                if a_str:
                    candidate_strings.append(a_str)
                    string_to_entity_id[a_str] = ent_id

        if candidate_strings:
            match = process.extractOne(q_lower, candidate_strings, scorer=fuzz.WRatio)
            if match and match[1] >= confidence_threshold:
                matched_str, score, _ = match
                res_id = string_to_entity_id[matched_str]
                return res_id, score / 100.0, None

        # 5. Active Context Fallback (only if query contains contextual pronouns)
        if active_entity_id and (q_lower in CONTEXT_PRONOUNS or any(p in q_lower for p in CONTEXT_PRONOUNS)):
            return active_entity_id, 0.5, None

        return None, 0.0, None

def get_entity_engine() -> EntityEngine:
    return EntityEngine()
