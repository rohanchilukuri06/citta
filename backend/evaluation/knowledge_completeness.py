"""
Knowledge completeness report: which sections each catalog entity can answer from authoritative content.

Uses the same KnowledgeOperationExecutor that serves /api/chat, so "missing" here means the chatbot
will answer "not available in the knowledge base" for that section. No content is generated or edited.

Usage: python evaluation/knowledge_completeness.py
"""

import json
import logging
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
OUT_DIR = Path(__file__).resolve().parent / "reports"

SECTIONS = [("overview", "get_solution"), ("capabilities", "get_capabilities"), ("benefits", "get_benefits"),
            ("workflow", "get_workflow"), ("target_users", "get_target_users"), ("faq", "get_faq"), ("pricing", "get_pricing")]


def main():
    logging.disable(logging.WARNING)
    from knowledge_operation_executor import KnowledgeOperationExecutor, PLACEHOLDER_AUDIENCES
    from knowledge_registry import get_registry
    from knowledge_tool_router import OperationRoutePlan
    reg = get_registry()
    ex = KnowledgeOperationExecutor(reg)

    rows = []
    for eid, e in sorted(reg.entities.items(), key=lambda kv: (str(kv[1].get("type")), kv[0])):
        if str(e.get("type")).lower() not in ("product", "solution", "service"):
            continue
        row = {"entity": eid, "title": e.get("title"), "type": e.get("type")}
        for sec, op in SECTIONS:
            ev = ex.execute(OperationRoutePlan(op, "KnowledgeRegistry", {"entity_id": eid}))
            row[sec] = len(ev.items) if ev.available else 0
        best_for = [b for b in (e.get("best_for") or []) if isinstance(b, str)]
        row["target_users_placeholder_only"] = bool(best_for) and all(b.lower() in PLACEHOLDER_AUDIENCES for b in best_for)
        rows.append(row)

    company = {}
    for label, op in [("contact", "get_contact"), ("leadership", "get_leadership"), ("recognition", "get_recognition"), ("case_studies", "list_case_studies")]:
        ev = ex.execute(OperationRoutePlan(op, "KnowledgeRegistry", {}))
        company[label] = len(ev.items) if ev.available else 0
    contact = reg.get_entity("contact_info") or {}
    contact_text = json.dumps(contact).lower()
    company["contact_has_email"] = "@" in contact_text
    company["contact_has_phone"] = any(ch.isdigit() for ch in contact_text.split("phone")[-1][:40]) if "phone" in contact_text else False

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "knowledge_completeness.json").write_text(json.dumps({"entities": rows, "company": company}, indent=2), encoding="utf-8")
    mark = lambda n: f"✅ {n}" if n else "❌"
    lines = [f"# Knowledge Completeness", "", f"Generated {time.strftime('%Y-%m-%d %H:%M')} from the live registry via the production operation executor.",
             "❌ = the chatbot will say this information is not available. No content was generated or edited.", "",
             "| Entity | Type | " + " | ".join(s for s, _ in SECTIONS) + " |", "|---|---|" + "---|" * len(SECTIONS)]
    for r in rows:
        tu = mark(r["target_users"]) + (" (only 'Admin/User' placeholders in registry)" if r["target_users_placeholder_only"] else "")
        cells = [mark(r[s]) if s != "target_users" else tu for s, _ in SECTIONS]
        lines.append(f"| {r['title']} | {r['type']} | " + " | ".join(cells) + " |")
    missing = {s: [r["title"] for r in rows if not r[s]] for s, _ in SECTIONS}
    lines += ["", "## Gaps by section"] + [f"- **{s}** missing for {len(v)}/{len(rows)}: {', '.join(v) if v else '—'}" for s, v in missing.items()]
    lines += ["", "## Company-level", f"- contact items: {company['contact']} (email present: {company['contact_has_email']}, phone present: {company['contact_has_phone']})",
              f"- leadership people: {company['leadership']}", f"- awards: {company['recognition']}", f"- case studies: {company['case_studies']}",
              "", "## Product decision needed: Pharma OS vs hospitals",
              "The website names it **Pharma & Healthcare OS**, but all product content (site and registry) is pharmaceutical QA/compliance "
              "(batch record review, quality dashboards, APQR, CPV). No page mentions hospitals, clinics or patients; the hospital/clinic → "
              "pharma_os mapping exists only as registry aliases. Until the product scope is decided, the chatbot clarifies instead of claiming "
              "hospital functionality."]
    (OUT_DIR / "knowledge_completeness.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
