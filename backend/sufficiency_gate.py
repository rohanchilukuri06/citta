"""
SufficiencyGate for CittaAI Bounded Agentic Enterprise Knowledge Architecture.
Bounded sufficiency evaluator enforcing MAX_KNOWLEDGE_OPERATIONS = 3 hard limit
to prevent infinite LLM/tool agent loops while ensuring adequate evidence coverage.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

MAX_KNOWLEDGE_OPERATIONS = 3

class SufficiencyGate:
    def __init__(self, max_operations: int = MAX_KNOWLEDGE_OPERATIONS):
        self.max_operations = max_operations

    def evaluate_sufficiency(
        self,
        query_intel: Dict[str, Any],
        collected_evidence: List[Dict[str, Any]],
        ops_executed_count: int
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Evaluates whether collected evidence is sufficient for the query.
        Returns:
            - is_sufficient (bool)
            - status_code (str): SUFFICIENT_COVERAGE | MAX_OPERATIONS_REACHED | MISSING_ASPECT | MISSING_ENTITY
            - missing_operations (List[Dict]): Targeted operations to fetch missing context if ops < MAX
        """
        # Rule 1: Bounded execution limit check
        if ops_executed_count >= self.max_operations:
            logger.warning(
                f"[SufficiencyGate] Max operations limit reached ({ops_executed_count}/{self.max_operations}). "
                "Halting further tool executions."
            )
            return True, "MAX_OPERATIONS_REACHED", []

        if not collected_evidence:
            return False, "NO_EVIDENCE_COLLECTED", [
                {"operation_name": "semantic_search", "reason": "No initial evidence found"}
            ]

        # Combine collected text for analysis
        combined_text = " ".join([
            str(item.get("text", "") or item.get("content", "") or item.get("description", ""))
            for item in collected_evidence
        ]).lower()

        primary_entity = query_intel.get("entity") or query_intel.get("primary_entity")
        entities = query_intel.get("entities", [])
        requested_aspect = (query_intel.get("aspect") or query_intel.get("requested_section") or "").lower()

        # Check multi-entity completeness
        missing_entities = []
        if len(entities) > 1:
            for ent in entities:
                ent_name = str(ent).lower().replace("_", " ")
                if ent_name not in combined_text and ent_name.replace(" os", "") not in combined_text:
                    missing_entities.append(ent)

        if missing_entities:
            next_ops = [
                {
                    "operation_name": "get_product" if "os" in e or "app" in e else "get_solution",
                    "inputs": {"entity_id": e},
                    "reason": f"Targeted lookup for missing entity '{e}'"
                }
                for e in missing_entities[:self.max_operations - ops_executed_count]
            ]
            return False, "MISSING_ENTITY", next_ops

        # Check aspect coverage for primary entity
        if requested_aspect and requested_aspect not in ["overview", "general", "unknown"]:
            aspect_keywords = [requested_aspect.replace("_", " ")]
            if requested_aspect in ["how_it_works", "workflow", "workflows"]:
                aspect_keywords.extend(["process", "step", "flow", "workflow", "integrate"])
            elif requested_aspect == "benefits":
                aspect_keywords.extend(["benefit", "advantage", "roi", "value", "save"])
            elif requested_aspect in ["features", "capabilities"]:
                aspect_keywords.extend(["feature", "capability", "module", "function"])

            aspect_present = any(kw in combined_text for kw in aspect_keywords)
            if not aspect_present and primary_entity:
                next_ops = [{
                    "operation_name": f"get_{requested_aspect}" if f"get_{requested_aspect}" in [
                        "get_capabilities", "get_benefits", "get_workflow", "get_target_users", "get_faq"
                    ] else "semantic_search",
                    "inputs": {"entity_id": primary_entity, "section": requested_aspect},
                    "reason": f"Targeted lookup for missing aspect '{requested_aspect}'"
                }]
                return False, "MISSING_ASPECT", next_ops

        return True, "SUFFICIENT_COVERAGE", []


_GLOBAL_SUFFICIENCY_GATE: Optional[SufficiencyGate] = None

def get_sufficiency_gate() -> SufficiencyGate:
    global _GLOBAL_SUFFICIENCY_GATE
    if _GLOBAL_SUFFICIENCY_GATE is None:
        _GLOBAL_SUFFICIENCY_GATE = SufficiencyGate()
    return _GLOBAL_SUFFICIENCY_GATE
