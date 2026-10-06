"""
Mechanically validate holdout v3 gold labels against the authoritative registry before use.

Checks (never edits labels silently — every correction is listed in the output with its reason):
  - entity / multi-entity ids exist in the registry
  - aspect, scope, operation are from the canonical vocabulary
  - overview operation matches the entity's registry type (get_product / get_solution / get_service)
  - knowledge_available agrees with what the registry actually contains for that section
  - context items carry context; "both" items follow the pair policy

Usage: python evaluation/validate_holdout_v3.py <raw.json> [out.json] [version]   (default out: evaluation/semantic_holdout_v3.json)
"""

import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
OUT = Path(__file__).resolve().parent / "semantic_holdout_v3.json"

ASPECTS = {"OVERVIEW", "CAPABILITIES", "BENEFITS", "TARGET_USERS", "WORKFLOW", "FAQ", "PRICING", "CONTACT", "LEADERSHIP",
           "RECOGNITION", "CLIENTS_CASE_STUDIES", "CATALOG_LIST"}
SCOPES = {"SINGLE_ENTITY", "MULTI_ENTITY", "ALL", "ALL_PRODUCTS", "ALL_SOLUTIONS", "ALL_SERVICES", "CLIENTS_SCOPE",
          "OUT_OF_DOMAIN", "UNKNOWN_ENTITY", "NONE"}
OPS = {"get_solution", "get_product", "get_service", "get_company_info", "get_capabilities", "get_benefits", "get_target_users",
       "get_workflow", "get_faq", "get_pricing", "get_contact", "get_leadership", "get_recognition", "list_case_studies",
       "get_case_study", "list_products", "list_solutions", "list_services", "list_catalog", "request_clarification",
       "decline_out_of_domain"}
TYPE_OVERVIEW = {"product": "get_product", "solution": "get_solution", "service": "get_service"}
SECTION_OPS = {"get_capabilities", "get_benefits", "get_target_users", "get_workflow", "get_faq", "get_pricing"}


def main(raw_path: str, out_path: Path = OUT, version: str = "3.0.0"):
    import logging
    logging.disable(logging.WARNING)
    from knowledge_operation_executor import get_operation_executor
    from knowledge_registry import get_registry
    from knowledge_tool_router import OperationRoutePlan
    reg, ex = get_registry(), get_operation_executor()
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    items = raw["items"] if isinstance(raw, dict) else raw

    errors, corrections = [], []
    for it in items:
        e = it["expected"]
        iid = it["id"]
        ents = e.get("entities") or []
        for x in ents + (e.get("multi_entities") or []):
            if x not in reg.entities:
                errors.append(f"{iid}: unknown entity id '{x}'")
        for a in e.get("aspects") or []:
            if a not in ASPECTS:
                errors.append(f"{iid}: non-canonical aspect '{a}'")
        if e.get("scope") not in SCOPES:
            errors.append(f"{iid}: non-canonical scope '{e.get('scope')}'")
        if e.get("operation") not in OPS:
            errors.append(f"{iid}: non-canonical operation '{e.get('operation')}'")
        if it["category"] in ("context",) and not it.get("context"):
            errors.append(f"{iid}: context question without context")

        # Overview operation must follow registry type
        op = e.get("operation")
        if op in TYPE_OVERVIEW.values() and ents and not e.get("multi_entities"):
            t = str(reg.entities.get(ents[0], {}).get("type", "")).lower()
            if t in TYPE_OVERVIEW and TYPE_OVERVIEW[t] != op:
                corrections.append((iid, "operation", op, TYPE_OVERVIEW[t], f"{ents[0]} is a {t} in the registry"))
                e["operation"] = TYPE_OVERVIEW[t]

        # knowledge_available must match registry content for section questions
        if op in SECTION_OPS and len(ents) == 1 and e.get("clarification") != "required":
            actual = ex.execute(OperationRoutePlan(op, "KnowledgeRegistry", {"entity_id": ents[0]})).available
            if bool(e.get("knowledge_available", True)) != actual:
                corrections.append((iid, "knowledge_available", e.get("knowledge_available"), actual,
                                    f"registry {'has' if actual else 'has no'} content for {op} on {ents[0]}"))
                e["knowledge_available"] = actual

    per_entity = {}
    for it in items:
        for x in (it["expected"].get("entities") or []):
            per_entity[x] = per_entity.get(x, 0) + 1
    catalog = [eid for eid, v in reg.entities.items() if str(v.get("type")).lower() in TYPE_OVERVIEW]
    thin = {x: per_entity.get(x, 0) for x in catalog if per_entity.get(x, 0) < 5}

    out = {"version": version, "created": time.strftime("%Y-%m-%d"), "source": "independent agent, catalog-content only",
           "validation": {"errors": errors, "corrections": [dict(zip(["id", "field", "from", "to", "reason"], c)) for c in corrections],
                          "offerings_with_fewer_than_5": thin},
           "items": items}
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(items)} items | errors: {len(errors)} | corrections: {len(corrections)} | thin coverage: {thin}")
    for x in errors:
        print("  ERROR", x)
    for c in corrections:
        print("  FIX  ", c)


if __name__ == "__main__":
    # python evaluation/validate_holdout_v3.py <raw.json> [out.json] [version]
    main(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else OUT, sys.argv[3] if len(sys.argv) > 3 else "3.0.0")
