"""
Executes KnowledgeToolRouter operation plans against the authoritative KnowledgeRegistry.

Each operation returns only the section it names. When the registry has no content for that
section the result is marked unavailable, so downstream generation states that the information
is not in the knowledge base instead of improvising it.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from knowledge_registry import get_registry

logger = logging.getLogger(__name__)

# best_for values that are UI role placeholders, not audiences
PLACEHOLDER_AUDIENCES = {"admin", "user", "users"}

SECTION_LABELS = {
    "overview": "overview", "capabilities": "capabilities", "benefits": "benefits",
    "target_users": "intended users", "workflow": "how it works", "faq": "frequently asked questions",
    "pricing": "pricing", "contact": "contact details", "leadership": "leadership team",
    "recognition": "awards and recognition", "case_studies": "client case studies", "catalog": "catalog",
}

OP_SECTION = {
    "get_product": "overview", "get_solution": "overview", "get_service": "overview", "get_company_info": "overview",
    "get_capabilities": "capabilities", "get_benefits": "benefits", "get_target_users": "target_users",
    "get_workflow": "workflow", "get_faq": "faq", "get_pricing": "pricing", "get_contact": "contact",
    "get_leadership": "leadership", "get_recognition": "recognition", "list_case_studies": "case_studies",
    "get_case_study": "case_studies", "list_products": "catalog", "list_solutions": "catalog",
    "list_services": "catalog", "list_catalog": "catalog",
}


@dataclass
class Evidence:
    operation: str
    section: str
    entity_id: Optional[str] = None
    title: Optional[str] = None
    items: List[str] = field(default_factory=list)
    available: bool = False
    route: Optional[str] = None
    source_ids: List[str] = field(default_factory=list)

    def as_context(self) -> str:
        head = f"[{self.title or self.entity_id or 'CittaAI'} — {SECTION_LABELS.get(self.section, self.section)}]"
        return head + "\n" + "\n".join(f"- {i}" for i in self.items)


def display_name(ent: Dict[str, Any]) -> Optional[str]:
    """Customer-facing name: offerings use their product name ("MarTech 360"), which can differ from the
    registry title ("AI-Powered Marketing Solutions"); company pages use their title."""
    if str(ent.get("type", "")).lower() in ("product", "solution", "service"):
        return ent.get("name") or ent.get("title")
    return ent.get("title") or ent.get("name")


def _text(v: Any) -> str:
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, dict):
        parts = [str(v.get(k)).strip() for k in ("title", "question", "subtitle", "description", "answer", "step") if v.get(k)]
        feats = v.get("features")
        if isinstance(feats, list) and feats:
            parts.append("Features: " + "; ".join(str(f) for f in feats))
        return " — ".join(p for p in parts if p)
    if isinstance(v, list):
        return "; ".join(_text(x) for x in v if _text(x))
    return ""


def _listify(v: Any) -> List[Any]:
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.strip().startswith("["):
        # Some registry fields are stored as stringified Python lists
        import ast
        try:
            parsed = ast.literal_eval(v)
            return parsed if isinstance(parsed, list) else []
        except (ValueError, SyntaxError):
            return []
    return []


class KnowledgeOperationExecutor:
    def __init__(self, registry: Any = None):
        self.registry = registry or get_registry()

    def _entity(self, eid: Optional[str]) -> Dict[str, Any]:
        return (self.registry.get_entity(eid) if eid else None) or {}

    def _by_type(self, *types: str) -> List[Dict[str, Any]]:
        return [e for e in self.registry.entities.values() if str(e.get("type", "")).lower() in types]

    def _ev(self, op: str, eid: Optional[str], items: List[str], **kw) -> Evidence:
        ent = self._entity(eid)
        items = [i for i in (x.strip() for x in items) if i]
        return Evidence(operation=op, section=OP_SECTION.get(op, "overview"), entity_id=eid,
                        title=display_name(ent) or kw.pop("title", None),
                        items=items, available=bool(items), route=ent.get("route") or kw.pop("route", None),
                        source_ids=[eid] if eid else kw.pop("source_ids", []), **kw)

    # ---- content crawled from cittaai.com (knowledge/site/cittaai_live.json) ----
    SITE_SECTION = {
        "get_product": "overview", "get_solution": "overview", "get_service": "overview",
        "get_capabilities": "capabilities", "get_benefits": "benefits", "get_workflow": "workflows", "get_faq": "faq",
        "list_case_studies": "case_studies", "get_leadership": "leadership",
    }

    def _site_docs(self) -> List[Dict[str, Any]]:
        if not hasattr(self, "_site_cache"):
            import json
            from pathlib import Path
            path = Path(__file__).resolve().parent / "knowledge" / "site" / "cittaai_live.json"
            try:
                self._site_cache = json.loads(path.read_text(encoding="utf-8")).get("documents", []) if path.exists() else []
            except (OSError, ValueError) as e:
                logger.warning(f"[OperationExecutor] Could not read crawled site knowledge: {e}")
                self._site_cache = []
        return self._site_cache

    def _site_services(self) -> List[str]:
        """The homepage services block ("Data Engineering: …. Enterprise & Agentic AI: ….") split into one line per service."""
        names = [display_name(e) for e in self._by_type("service")]
        for d in self._site_docs():
            text = d.get("text", "")
            if sum(f"{n}:" in text for n in names if n) >= 3:
                return [s.strip() for s in re.split(r"(?<=\.)\s+(?=[A-Z0-9][^:.]{2,60}:\s)", text) if s.strip()]
        return []

    def execute(self, plan: Any) -> Evidence:
        """Registry section, supplemented with the same section from the live website."""
        ev = self._execute_registry(plan)
        if plan.operation_name == "list_services":
            site_services = self._site_services()
            if site_services:
                # cittaai.com's own services list (one line each) is the source of truth
                ev.items, ev.available, ev.route = site_services, True, "/"
            return ev
        section = self.SITE_SECTION.get(plan.operation_name)
        if not section:
            return ev
        eid = (plan.inputs or {}).get("entity_id")
        if plan.operation_name == "get_leadership":
            team = [d["text"] for d in self._site_docs() if d.get("section") == "leadership"]
            if team:
                # The public website is the source of truth for names and titles. The owner-confirmed CEO statement
                # leads, so "CEO of Fixity Technologies" in the team list isn't read as CittaAI's CEO.
                obj = getattr(self.registry, "registry_by_id", {}).get("leadership_info")
                lead = obj.model_dump() if obj is not None else {}
                ceo = [f.get("answer") for f in lead.get("faq") or [] if isinstance(f, dict)
                       and "ceo of cittaai" in str(f.get("question", "")).lower() and f.get("answer")]
                others = [f"{m['name']} is the {m['designation']} (not CittaAI's CEO)." for m in lead.get("members") or []
                          if isinstance(m, dict) and m.get("name") and " of " in str(m.get("designation", "")).lower()]
                ev.items, ev.available, ev.route = ceo + others + team, True, "/about"
            return ev
        if plan.operation_name == "list_case_studies":
            extra = [d["text"] for d in self._site_docs() if d.get("section") == "case_studies"]
        elif eid:
            extra = [d["text"] for d in self._site_docs() if d.get("section") == section and eid in (d.get("entities") or [])]
        else:
            extra = []
        if extra:
            seen = {i.lower() for i in ev.items}
            ev.items = ev.items + [x for x in extra if x.lower() not in seen]
            ev.available = True
        return ev

    def _execute_registry(self, plan: Any) -> Evidence:
        op = plan.operation_name
        inputs = plan.inputs or {}
        eid = inputs.get("entity_id")
        ent = self._entity(eid)

        if op in ("get_product", "get_solution", "get_service", "get_company_info"):
            eid = eid or "company_info"
            ent = self._entity(eid)
            items = [_text(ent.get("tagline")), _text(ent.get("description"))]
            caps = [c.get("title") for c in _listify(ent.get("capabilities")) if isinstance(c, dict) and c.get("title")]
            if caps:
                items.append("Key capabilities: " + ", ".join(caps))
            return self._ev(op, eid, items)

        if op == "get_capabilities":
            return self._ev(op, eid, [_text(c) for c in _listify(ent.get("capabilities"))])

        if op == "get_benefits":
            return self._ev(op, eid, [_text(b) for b in _listify(ent.get("benefits"))])

        if op == "get_target_users":
            aud = [b for b in _listify(ent.get("best_for")) if isinstance(b, str) and b.strip().lower() not in PLACEHOLDER_AUDIENCES]
            return self._ev(op, eid, aud)

        if op == "get_workflow":
            how = ent.get("how_it_works") or {}
            steps = _listify(how.get("steps")) if isinstance(how, dict) else _listify(how)
            return self._ev(op, eid, [_text(s) for s in steps + _listify(ent.get("workflows"))])

        if op == "get_faq":
            return self._ev(op, eid, [_text(f) for f in _listify(ent.get("faq"))])

        if op == "get_pricing":
            return self._ev(op, eid, [_text(ent.get("pricing"))] if ent.get("pricing") else [])

        if op == "get_contact":
            c = self._entity("contact_info")
            items = [_text(c.get("description"))] + [_text(f) for f in _listify(c.get("faq"))] + [_text(b) for b in _listify(c.get("benefits"))]
            ev = self._ev(op, "contact_info", items)
            ev.route = c.get("route", "/contact")
            return ev

        if op == "get_leadership":
            people = [p for p in self._by_type("leadership") if p.get("id") != "leadership_info"]
            pid = inputs.get("person_id")
            if pid:
                people = [p for p in people if p.get("id") == pid] or people
            ev = self._ev(op, "leadership_info", [f"{p.get('name')} — {p.get('title')}" for p in people])
            return ev

        if op == "get_recognition":
            a = self._entity("awards_recognition")
            return self._ev(op, "awards_recognition", [_text(x) for x in _listify(a.get("capabilities"))])

        if op in ("list_case_studies", "get_case_study"):
            cases = [self._entity(eid)] if op == "get_case_study" and eid else self._by_type("case_study")
            items = [f"{c.get('title')}: {c.get('tagline')} {c.get('description')}".strip() for c in cases if c]
            return Evidence(op, "case_studies", eid, "Client case studies", [i for i in items if i], bool(items), "/case-studies",
                            [c.get("id") for c in cases if c])

        if op in ("list_products", "list_solutions", "list_services", "list_catalog"):
            types = {"list_products": ("product",), "list_solutions": ("solution",), "list_services": ("service",),
                     "list_catalog": ("product", "solution", "service")}[op]
            ents = sorted(self._by_type(*types), key=lambda e: (str(e.get("type")), str(e.get("title"))))
            items = [f"{e.get('title')} ({e.get('type')}): {e.get('tagline') or ''}".strip() for e in ents]
            return Evidence(op, "catalog", None, "CittaAI catalog", items, bool(items), None, [e.get("id") for e in ents])

        logger.warning(f"[OperationExecutor] No executor for operation '{op}'")
        return Evidence(op, "unknown", eid, available=False)


_EXECUTOR: Optional[KnowledgeOperationExecutor] = None


def get_operation_executor() -> KnowledgeOperationExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = KnowledgeOperationExecutor()
    return _EXECUTOR
