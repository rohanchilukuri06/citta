import copy
import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

import config
from knowledge_registry import get_registry
from semantic_decision import FieldEvidence, SemanticDecision, canonicalize_and_validate

logger = logging.getLogger(__name__)

_SHARED_EMBEDDING_MODEL = None

def get_shared_embedding_model():
    global _SHARED_EMBEDDING_MODEL
    if _SHARED_EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _SHARED_EMBEDDING_MODEL = SentenceTransformer(config.EMBEDDING_MODEL)
    return _SHARED_EMBEDDING_MODEL


# ============================================================
# CANONICAL INTENT TAXONOMY FOR PHASE 5
# ============================================================
class SemanticAspect:
    OVERVIEW = "OVERVIEW"
    CAPABILITIES = "CAPABILITIES"
    BENEFITS = "BENEFITS"
    TARGET_USERS = "TARGET_USERS"
    WORKFLOWS = "WORKFLOW"
    WORKFLOW = "WORKFLOW"
    PRICING = "PRICING"
    FAQ = "FAQ"
    LEADERSHIP = "LEADERSHIP"
    CONTACT = "CONTACT"
    CASE_STUDIES = "CLIENTS_CASE_STUDIES"
    CLIENTS = "CLIENTS_CASE_STUDIES"
    CLIENTS_CASE_STUDIES = "CLIENTS_CASE_STUDIES"
    AWARDS = "RECOGNITION"
    RECOGNITION = "RECOGNITION"
    CATALOG_LIST = "CATALOG_LIST"
    UNKNOWN = "UNKNOWN"


class AnswerScope:
    SINGLE_ENTITY = "SINGLE_ENTITY"
    MULTI_ENTITY = "MULTI_ENTITY"
    MULTI_ENTITY_COMPARISON = "MULTI_ENTITY"
    CATALOG_SCOPE = "ALL_PRODUCTS"
    ALL_PRODUCTS = "ALL_PRODUCTS"
    ALL_SERVICES = "ALL_SERVICES"
    ALL_SOLUTIONS = "ALL_SOLUTIONS"
    CLIENTS_SCOPE = "CLIENTS_SCOPE"
    RECOGNITION_SCOPE = "RECOGNITION_SCOPE"
    COMPARISON_SCOPE = "MULTI_ENTITY"
    COMPANY_WIDE = "COMPANY_OVERVIEW"
    COMPANY_OVERVIEW = "COMPANY_OVERVIEW"
    GENERAL = "GENERAL"


class IntentTaxonomy:
    GREETING = "GREETING"
    COMPANY_OVERVIEW = "COMPANY_OVERVIEW"
    CAPABILITIES = "CAPABILITIES"
    FEATURES = "FEATURES"
    BENEFITS = "BENEFITS"
    USE_CASES = "USE_CASES"
    HOW_IT_WORKS = "HOW_IT_WORKS"
    SERVICES = "SERVICES"
    PRODUCTS = "PRODUCTS"
    SOLUTIONS = "SOLUTIONS"
    INDUSTRIES = "INDUSTRIES"
    TARGET_USERS = "TARGET_USERS"
    TECHNOLOGY = "TECHNOLOGY"
    INTEGRATIONS = "INTEGRATIONS"
    PRICING = "PRICING"
    CONTACT = "CONTACT"
    LOCATION = "LOCATION"
    LEADERSHIP = "LEADERSHIP"
    TEAM = "TEAM"
    CASE_STUDIES = "CASE_STUDIES"
    CLIENTS = "CLIENTS"
    AWARDS = "AWARDS"
    PARTNERSHIPS = "PARTNERSHIPS"
    CAREERS = "CAREERS"
    DEMO_REQUEST = "DEMO_REQUEST"
    SUPPORT = "SUPPORT"
    COMPARISON = "COMPARISON"
    RECOMMENDATION = "RECOMMENDATION"
    EXPLANATION = "EXPLANATION"
    OVERVIEW = "OVERVIEW"
    LIST = "LIST"
    COUNT = "COUNT"
    UNKNOWN = "UNKNOWN"

ALL_INTENTS = {
    IntentTaxonomy.GREETING, IntentTaxonomy.COMPANY_OVERVIEW, IntentTaxonomy.CAPABILITIES,
    IntentTaxonomy.FEATURES, IntentTaxonomy.BENEFITS, IntentTaxonomy.USE_CASES,
    IntentTaxonomy.HOW_IT_WORKS, IntentTaxonomy.SERVICES, IntentTaxonomy.PRODUCTS,
    IntentTaxonomy.SOLUTIONS, IntentTaxonomy.INDUSTRIES, IntentTaxonomy.TARGET_USERS,
    IntentTaxonomy.TECHNOLOGY, IntentTaxonomy.INTEGRATIONS, IntentTaxonomy.PRICING,
    IntentTaxonomy.CONTACT, IntentTaxonomy.LOCATION, IntentTaxonomy.LEADERSHIP,
    IntentTaxonomy.TEAM, IntentTaxonomy.CASE_STUDIES, IntentTaxonomy.CLIENTS,
    IntentTaxonomy.AWARDS, IntentTaxonomy.PARTNERSHIPS, IntentTaxonomy.CAREERS,
    IntentTaxonomy.DEMO_REQUEST, IntentTaxonomy.SUPPORT, IntentTaxonomy.COMPARISON,
    IntentTaxonomy.RECOMMENDATION, IntentTaxonomy.EXPLANATION, IntentTaxonomy.OVERVIEW,
    IntentTaxonomy.LIST, IntentTaxonomy.COUNT, IntentTaxonomy.UNKNOWN
}

# Pronouns indicating active context inheritance
CONTEXT_PRONOUNS = {
    "it", "its", "this", "that", "they", "them", "these", "those",
    "the tool", "the platform", "the service", "the solution", "the product",
    "this tool", "this platform", "this solution", "this product", "this app"
}

# Explicit category words used by users
CATEGORY_WORDS = {
    "service": "SERVICE",
    "services": "SERVICE",
    "product": "PRODUCT",
    "products": "PRODUCT",
    "solution": "SOLUTION",
    "solutions": "SOLUTION",
    "platform": "PRODUCT",
    "platforms": "PRODUCT",
    "system": "SOLUTION",
    "systems": "SOLUTION",
    "os": "SOLUTION",
    "tool": "PRODUCT",
    "tools": "PRODUCT"
}

# Generic entities to ignore for specific matching
GENERIC_ENTITIES = {"company_info", "faq_general", "contact", "location"}

@dataclass
class EntityMatch:
    entity_id: str
    entity_type: str
    confidence: float
    matched_alias: str = ""

@dataclass
class QueryInterpretation:
    original_query: str
    normalized_query: str
    entities: List[Dict[str, Any]] = field(default_factory=list)
    primary_entity_id: Optional[str] = None
    primary_intent: str = IntentTaxonomy.UNKNOWN
    primary_aspect: str = "OVERVIEW"
    answer_scope: str = "GENERAL"
    requested_information: List[str] = field(default_factory=list)
    requested_sections: List[str] = field(default_factory=list)
    target_registry_types: List[str] = field(default_factory=list)
    knowledge_requirement: str = "VERIFIED_ONLY"
    user_goal: str = "INFORMATIONAL"
    domain: str = "GENERAL"
    query_mode: str = "INFORMATIONAL"
    conversation_reference: Optional[str] = None
    category_term_used_by_user: Optional[str] = None
    registry_category: Optional[str] = None
    category_mismatch: bool = False
    requires_clarification: bool = False
    confidence: float = 0.0
    interpretation: str = ""
    llm_invoked: bool = False
    latency_ms: float = 0.0
    diagnostic_trace: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Function / request / catalog words carry no domain meaning. What remains after removing them
# ("residue") tells us whether the user named a domain, or is asking about the catalog or context.
_STOPWORDS = set("""
a an the and or but if of to in on at for with from by about as into over under than then so
is are was were be been being am do does did doing done have has had having can could would should will shall may might must
i me my mine we us our ours you your yours he she it its they them their this that these those there here
what which who whom whose when where why how whats hows whos
any anything some something someone all every everything each both either neither none no not
please pls plz kindly sir madam hi hello hey thanks thank ok okay yes
u ur r ya ye pl tell tel let give show share get got know want wanted wants need needs needed looking look find help helps
wht wat wut wot whats hw pls plz thx wanna gonna gotta
also just only really actually very much many more most lot lots too like such same other another
one ones thing things stuff way ways kind kinds sort type types
info information details detail question questions query something
""".split())
_CATALOG_WORDS = {
    "product": "ALL_PRODUCTS", "products": "ALL_PRODUCTS",
    "service": "ALL_SERVICES", "services": "ALL_SERVICES",
    "solution": "ALL_SOLUTIONS", "solutions": "ALL_SOLUTIONS", "industries": "ALL_SOLUTIONS", "industry": "ALL_SOLUTIONS",
    "offering": "ALL", "offerings": "ALL", "offer": "ALL", "offers": "ALL", "catalog": "ALL", "portfolio": "ALL",
    "platforms": "ALL", "tools": "ALL", "systems": "ALL",
}
_CATALOG_FILLER = {
    "list", "available", "sell", "provide", "provides", "build", "builds", "make", "overview", "summary", "flagship",
    "enterprise", "os", "across", "different", "various", "range", "work", "works", "working", "cittaai", "citta", "company",
    "count", "number", "total", "entire", "full", "complete", "current", "currently", "main", "core", "key", "top", "guys", "sells", "selling", "sold", "buy", "purchase", "software", "companies", "businesses",
    "cater", "caters", "serve", "serves", "offered", "provided", "built", "made", "team", "all",
}
_CATALOG_TRIGGERS = re.compile(
    r"\b(list|how many|number of|what (?:all )?(?:do|does|can) (?:you|cittaai|citta)\b.*\b(?:offer|provide|sell|build)|"
    r"(?:which|what) (?:products|services|solutions|industries|offerings)|all (?:your|the)?\s*(?:products|services|solutions|offerings)|"
    r"everything|offerings|catalog|portfolio|what do you offer|what (?:do|can) you (?:offer|provide|sell)|"
    r"show (?:me )?(?:all|everything)|all (?:the )?(?:stuff|things)|"
    r"what (?:kind|kinds|type|types|sort) of (?:work|things|stuff|projects) (?:do|does|can) (?:you|cittaai|citta))\b"
)
_COMPARISON = re.compile(r"\b(compare|compared|comparison|vs\.?|versus|difference|differences|differ|differs|different|distinguish|distinguishes|better|both|which (?:one|is)|between)\b")
_SEGMENT_SPLIT = re.compile(r"\b(?:vs\.?|versus|compared (?:to|with)|and|or|between|compare|with|from|than)\b|[,:;/?]")
# "the other one" refers to the second of two offerings already in the conversation
_OTHER_ONE = re.compile(r"\b(?:the\s+)?other\s+(?:one|option|platform|product|solution|service)\b|\bthe other\b")
# Role titles describing the visitor ("I'm the CTO of a bank") are not questions about CittaAI's leaders
_SELF_ROLE = re.compile(r"\b(?:i am|i'm|im|as|being)\s+(?:a|an|the)?\s*(?:\w+\s+)?(?:ceo|cto|coo|cmo|cfo|founder|co-founder|head|director|manager)\b")
_PAIR_REFERENCE = re.compile(r"\b(both|the two|each of them|both of them|either of them)\b")
_PRONOUN = re.compile(r"\b(it|its|this|that|they|them|these|those|the (?:tool|platform|service|solution|product|app|system|one))\b")
# Single-word registry aliases that are ordinary English and too weak to name an entity on their own
_WEAK_ALIASES = {
    "about", "help", "board", "management", "partner", "support", "team", "menu", "answers", "questions", "company",
    "agency", "office", "location", "wa", "hq", "mission", "vision", "wins", "retail", "shopping", "checkout",
    "integrations", "leaders", "executives", "phone", "email", "address", "creator", "urban", "data", "ai",
}


# Canonical aspects an entity-level question can target (the aspect adjudicator may only choose these)
ENTITY_ASPECT_DEFINITIONS = {
    "OVERVIEW": "what the offering is, in general; a broad or introductory question, or a visitor describing their needs without asking about one specific part",
    "CAPABILITIES": "features, modules, functions, what it can do or supports",
    "BENEFITS": "value, advantages, outcomes, why use it, problems it solves",
    "TARGET_USERS": "who it is for, intended customers or organisations, suitability",
    "WORKFLOW": "how it works, process, steps, implementation, onboarding",
    "FAQ": "frequently asked questions about it",
    "PRICING": "cost, price, plans, fees",
    "CONTACT": "how to get it, talk to sales, book a demo, get in touch",
}

# Existing intent rules double as aspect evidence (e.g. "how does <X> work" -> WORKFLOW)
_INTENT_ASPECT = {
    "HOW_IT_WORKS": "WORKFLOW", "TARGET_USERS": "TARGET_USERS", "BENEFITS": "BENEFITS",
    "FEATURES": "CAPABILITIES", "CAPABILITIES": "CAPABILITIES", "PRICING": "PRICING",
    "CONTACT": "CONTACT", "LOCATION": "CONTACT", "DEMO_REQUEST": "CONTACT", "LEADERSHIP": "LEADERSHIP",
    "CASE_STUDIES": "CLIENTS_CASE_STUDIES",
}


class QueryIntelligenceEngine:
    """
    Semantic query understanding: maps arbitrary user language to a canonical
    (entity, aspect, scope) decision with calibrated confidence.

    Evidence sources:
      - rules   : explicit mentions of registry names/aliases (plus typo-tolerant matching)
      - bge     : similarity against exemplars derived from registry content
      - context : active conversation entity for pronoun / elliptical follow-ups
      - llm     : adjudication, invoked only when the fused decision is genuinely ambiguous
    """
    def __init__(self, provider=None, enable_llm: Optional[bool] = None):
        self.provider = provider
        self.enable_llm = enable_llm
        self._llm_cache: Dict[tuple, Optional[Dict[str, Any]]] = {}
        self._decision_cache: Dict[tuple, SemanticDecision] = {}
        self._provider_resolved = provider is not None
        self.registry = get_registry()
        self._build_dynamic_vocabularies()
        from semantic_entity_index import get_semantic_entity_index
        self.index = get_semantic_entity_index(self.registry, get_shared_embedding_model())
        self._validate_exemplar_coverage()

    def _validate_exemplar_coverage(self):
        """Every indexed entity needs enough registry content to be recognised semantically."""
        import numpy as np
        for i, eid in enumerate(self.index.entity_ids):
            n = int(np.sum(self.index.exemplar_owner == i))
            if n < 3:
                logger.warning(f"[QueryIntelligenceEngine] Entity '{eid}' has only {n} semantic exemplars; enrich its registry entry.")

    def _build_dynamic_vocabularies(self):
        """Alias vocabulary and catalog metadata, derived only from KnowledgeRegistry."""
        self.entity_catalog: Dict[str, Dict[str, Any]] = {}
        self.alias_to_entity: Dict[str, str] = {}

        for ent_id, obj in self.registry.entities.items():
            title = obj.get("title") or obj.get("name") or ent_id
            ent_type = str(obj.get("type") or "solution").lower()
            self.entity_catalog[ent_id] = {
                "id": ent_id, "title": title, "name": obj.get("name") or title, "type": ent_type.upper(),
                "category": {"product": "PRODUCT", "service": "SERVICE"}.get(ent_type, "SOLUTION"),
            }
            names = {ent_id, ent_id.replace("_", " "), str(title).lower(), str(obj.get("name") or "").lower()}
            names |= {a.lower() for a in obj.get("aliases", []) if isinstance(a, str)}
            search = obj.get("search") or {}
            names |= {a.lower() for a in search.get("aliases", []) if isinstance(a, str)}
            for n in names:
                n = n.strip()
                if len(n) >= 2 and n not in {"services", "products", "solutions", "management"}:
                    self.alias_to_entity.setdefault(n, ent_id)

        for lookup in (self.registry.alias_lookup, self.registry.entity_lookup):
            for alias, target in lookup.items():
                a = alias.lower().strip().replace("_", " ")
                if len(a) >= 2 and a not in {"services", "products", "solutions", "management"}:
                    self.alias_to_entity.setdefault(a, target)

        self.company_level = {
            eid for eid, obj in self.registry.entities.items()
            if str(obj.get("type") or "").lower() in {"company", "contact", "award", "leadership", "case_study", "faq"}
        }
        self._alias_patterns = sorted(self.alias_to_entity.items(), key=lambda kv: len(kv[0]), reverse=True)
        # Every word used anywhere in registry content (used to tell described needs from unknown product names)
        self._registry_vocab = set(re.findall(r"[a-z][a-z0-9\-]+", json.dumps(list(self.registry.entities.values()), default=str).lower()))

    def _detect_category_term(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Identifies category terms used in the user's raw query (e.g. 'services', 'products')."""
        q_lower = query.lower()
        words = re.findall(r"\b\w+\b", q_lower)
        for w in words:
            if w in CATEGORY_WORDS:
                return w, CATEGORY_WORDS[w]
        return None, None

    def _classify_semantic_aspect(self, query: str, intent: str) -> Tuple[str, List[str]]:
        """
        Phase 6 Step 3 Semantic Aspect Classifier:
        Determines what aspect/dimension of knowledge the user is asking about:
        OVERVIEW, CAPABILITIES, BENEFITS, TARGET_USERS, WORKFLOW, PRICING, CONTACT, CLIENTS_CASE_STUDIES, RECOGNITION, LEADERSHIP, FAQ.
        Decoupled from entity resolution.
        """
        q_lower = query.lower().strip().replace("’", "'")
        # Expand contractions so "who's it for" matches "who is it for"
        q_lower = re.sub(r"\b(who|what|how|it|that|where|there)'s\b", r"\1 is", q_lower)
        q_lower = re.sub(r"\b(\w+)'re\b", r"\1 are", q_lower)
        aspects = []

        def hit(phrases: List[str]) -> bool:
            return any(re.search(r"(?<![a-z0-9])" + re.escape(p) + r"(?![a-z0-9])", q_lower) for p in phrases)

        # 1. CLIENTS / CASE STUDIES / PAST WORK
        if hit(["case study", "case studies", "client", "clients", "companies have you worked", "companies you worked", "success story", "success stories", "examples of work", "who have you worked", "worked with", "your portfolio", "past projects", "other businesses"]):
            aspects.append("CLIENTS_CASE_STUDIES")

        # 2. RECOGNITION / AWARDS / ACCREDITATION
        if hit(["award", "awards", "recognition", "recognitions", "honors", "accolades", "accredited", "recognized", "press"]):
            aspects.append("RECOGNITION")

        # 2b. CONTACT / GET IN TOUCH / LOCATION (company-directed phrasing only)
        if hit(["contact", "your email", "email address", "email id", "phone number", "your phone", "call you", "call us", "reach you", "reach out", "reach sales", "get in touch", "touch with", "where is your office", "located", "work with your team", "request a product demo", "product demo",
                "working hours", "business hours", "office hours", "opening hours", "timings", "hours of operation",
                "are you open", "open on", "on saturday", "on saturdays", "on sunday", "on sundays", "on weekends"]):
            aspects.append("CONTACT")

        # 3. BENEFITS / ROI / ADVANTAGES / VALUE
        if hit(["benefit", "benefits", "advantage", "advantages", "why choose", "value proposition", "roi", "why use", "why would i", "why would a", "improve", "value", "help us", "help our", "help a", "help my", "help businesses", "how would"]):
            aspects.append("BENEFITS")

        # 4. CAPABILITIES / FEATURES / FUNCTIONALITY
        if hit(["feature", "features", "capability", "capabilities", "module", "modules", "spec", "specs", "function", "functions", "what can it do", "what does it do", "what can it actually do", "what do you offer", "what can i use", "functionality", "abilities", "what can you do",
                # yes/no questions about a specific ability ("can it handle X", "does it support Y")
                "support", "supports", "able to", "work with", "works with", "integrate with", "integrates with", "compatible with", "handle", "handles"]):
            aspects.append("CAPABILITIES")

        # 5. TARGET USERS / AUDIENCE / SUITABILITY
        if hit(["target audience", "who is it for", "who should use", "who is it meant", "who is this meant", "intended users", "designed for", "ideal for", "for whom", "who can use", "who normally uses", "would this work for", "suitable for", "cater to",
                "who would use", "which teams", "what sort of companies", "what kind of companies", "what type of companies", "what kind of organizations", "what kind of organisations"]):
            aspects.append("TARGET_USERS")

        # 6. WORKFLOW / HOW IT WORKS / IMPLEMENTATION / PROCESS
        if hit(["how does it work", "how it works", "workflow", "workflows", "process", "how to use", "architecture", "implementation", "how to implement", "step by step", "getting started", "get started",
                "stages", "what happens after", "after we sign up", "onboarding process"]):
            aspects.append("WORKFLOW")

        # 7. PRICING / COST / CHARGES — "cost" alone is not a pricing question ("our cost per lead is rising")
        if hit(["pricing", "price", "prices", "quote", "charges", "subscription", "fee", "fees", "licensing", "how much", "cost of"]) or \
                re.search(r"\b(does|do|would|will)\b.{0,40}\bcosts?\b\??\s*$", q_lower) or re.search(r"^\s*(the\s+)?costs?\s*\??\s*$", q_lower):
            aspects.append("PRICING")


        # 9. LEADERSHIP / TEAM
        # "who founded" is about people; "when was it founded" is a company fact, not leadership
        if hit(["leadership", "ceo", "cto", "coo", "cmo", "founder", "founders", "who leads", "executive team", "leadership team", "executives"]) \
                or re.search(r"\bwho\b.{0,30}\bfounded\b", q_lower):
            aspects.append("LEADERSHIP")

        # 10. FAQ
        if hit(["faq", "faqs", "frequently asked", "common questions", "how long", "how many weeks", "how many days", "timeline", "duration"]):
            aspects.append("FAQ")

        # 11. CATALOG LIST
        if hit(["list all", "list products", "list services", "list solutions", "show products", "show services", "show solutions", "all products", "all services", "all solutions"]):
            aspects.append("CATALOG_LIST")

        # 12. OVERVIEW / DESCRIPTION
        if hit(["what is", "tell me about", "overview", "explain", "describe", "summary", "about", "introduction", "what about", "what's", "whats"]) or intent in [IntentTaxonomy.OVERVIEW, IntentTaxonomy.EXPLANATION, IntentTaxonomy.COMPANY_OVERVIEW]:
            aspects.append("OVERVIEW")

        # Deduplicate preserving order
        dedup = []
        for a in aspects:
            if a not in dedup:
                dedup.append(a)

        primary_aspect = dedup[0] if dedup else "OVERVIEW"
        return primary_aspect, dedup if dedup else ["OVERVIEW"]

    def _map_aspect_to_schema(self, aspects: List[str]) -> Tuple[List[str], List[str]]:
        """
        Schema Mapper:
        Translates semantic aspect intents (e.g. CLIENTS_CASE_STUDIES, RECOGNITION)
        to actual available metadata section names and registry types stored in vector_store.db.
        """
        requested_sections = []
        target_registry_types = []

        ASPECT_SECTION_MAP = {
            "OVERVIEW": ["overview", "hero", "about_lead", "about_story"],
            "CAPABILITIES": ["capabilities", "features"],
            "BENEFITS": ["benefits"],
            "TARGET_USERS": ["target_users", "best_for"],
            "WORKFLOW": ["workflows", "how_it_works", "implementation", "process"],
            "PRICING": ["pricing", "cost"],
            "CONTACT": ["contact", "location"],
            "LEADERSHIP": ["leadership"],
            "FAQ": ["faq"],
            "CLIENTS_CASE_STUDIES": ["cases", "overview", "target_users", "capabilities"],
            "RECOGNITION": ["awards", "overview"]
        }

        ASPECT_REGISTRY_MAP = {
            "CLIENTS_CASE_STUDIES": ["CASE_STUDIES"],
            "RECOGNITION": ["RECOGNITION"],
            "LEADERSHIP": ["LEADERSHIP"],
            "CONTACT": ["CONTACT"],
            "FAQ": ["FAQ"]
        }

        for asp in aspects:
            if asp in ASPECT_SECTION_MAP:
                for sec in ASPECT_SECTION_MAP[asp]:
                    if sec not in requested_sections:
                        requested_sections.append(sec)
            if asp in ASPECT_REGISTRY_MAP:
                for rtype in ASPECT_REGISTRY_MAP[asp]:
                    if rtype not in target_registry_types:
                        target_registry_types.append(rtype)

        if not requested_sections:
            requested_sections = ["overview"]

        return requested_sections, target_registry_types

    def _detect_intent_rules(self, query: str) -> Tuple[str, List[str]]:
        """Deterministic intent detection rule set covering the canonical Phase 5 taxonomy."""
        q_lower = query.lower().strip()

        # Greeting & Small Talk
        if re.search(r"^(hi|hello|hey|greetings|good\s+morning|good\s+afternoon|good\s+evening)\b", q_lower):
            return IntentTaxonomy.GREETING, ["greeting"]
        if re.search(r"^(thanks|thank\s+you|bye|goodbye|cool|great)\b", q_lower):
            return IntentTaxonomy.GREETING, ["small_talk"]

        # Specific domain intents FIRST before general overview!
        # Case Studies & Clients
        if any(p in q_lower for p in ["case study", "case studies", "client story", "success story", "examples of work"]):
            return IntentTaxonomy.CASE_STUDIES, ["case_studies"]

        # Counts
        if any(p in q_lower for p in ["how many", "count of", "number of"]):
            return IntentTaxonomy.COUNT, ["count"]

        # Pricing
        if any(re.search(rf"\b{p}\b", q_lower) for p in ["pricing", "price", "quote", "charges", "subscription", "how much", "cost of"]):
            return IntentTaxonomy.PRICING, ["pricing"]

        # Business Inquiry / Recommendation / Requirements
        if any(p in q_lower for p in ["evaluating", "exploring", "modernize", "need", "want to improve", "looking for", "we are a", "our organization"]):
            return IntentTaxonomy.RECOMMENDATION, ["recommendation", "business_inquiry"]

        # Contact & Location & Approach
        if any(p in q_lower for p in ["contact", "email", "phone", "reach sales", "get in touch", "approach", "how to approach", "how to connect"]):
            return IntentTaxonomy.CONTACT, ["contact"]
        if any(p in q_lower for p in ["location", "located", "address", "where is office", "headquarters", "where are you located", "where is cittaai located"]):
            return IntentTaxonomy.LOCATION, ["location"]

        # Leadership & Team (word boundary check to prevent matching sector/vector for 'cto')
        if any(re.search(rf"\b{re.escape(p)}\b", q_lower) for p in ["ceo", "cto", "coo", "cmo", "founder", "leadership", "who leads", "who founded", "executive"]):
            return IntentTaxonomy.LEADERSHIP, ["leadership"]

        # Demo Request
        if any(p in q_lower for p in ["book a demo", "schedule a demo", "demo", "request trial"]):
            return IntentTaxonomy.DEMO_REQUEST, ["demo_request"]

        # How It Works / Workflow / Process
        if any(re.search(p, q_lower) for p in [r"how\s+does\s+.*\s+work\b", r"\bhow\s+it\s+works\b", r"\bworkflow\b", r"\bprocess\b", r"\bworking\b", r"\bhow\s+to\s+use\b", r"\barchitecture\b"]):
            return IntentTaxonomy.HOW_IT_WORKS, ["how_it_works"]

        # Benefits & Advantages
        if any(re.search(p, q_lower) for p in [r"\bbenefits?\b", r"\badvantages?\b", r"\bwhy\s+choose\b", r"\bvalue\s+proposition\b", r"\broi\b"]):
            return IntentTaxonomy.BENEFITS, ["benefits"]

        # Features & Modules
        if any(re.search(p, q_lower) for p in [r"\bfeatures?\b", r"\bmodules?\b", r"\bfunctions?\b", r"\bspecs?\b", r"\bcomponents?\b"]):
            return IntentTaxonomy.FEATURES, ["features"]

        # Capabilities / What can it do / What does X provide
        if any(re.search(p, q_lower) for p in [r"what\s+does\s+.*\s+(provide|do)\b", r"what\s+can\s+.*\s+(do|provide)\b", r"\bcapabilities\b", r"\bwhat\s+do\s+you\s+offer\b", r"\babilities\b", r"\bprovides?\b"]):
            return IntentTaxonomy.CAPABILITIES, ["capabilities"]

        # Target Users / Who is it for
        if any(re.search(p, q_lower) for p in [r"who\s+is\s+.*\s+(for|meant\s+for|designed\s+for|ideal\s+for)\b", r"\btarget\s+audience\b", r"\bwho\s+should\s+use\b", r"\bintended\s+users\b"]):
            return IntentTaxonomy.TARGET_USERS, ["target_users"]

        # Integrations & Implementation
        if any(p in q_lower for p in ["integrate", "integration", "integrations", "connect", "api", "crm", "erp", "webhooks"]):
            return IntentTaxonomy.INTEGRATIONS, ["integrations"]

        # Category Lists
        if any(p in q_lower for p in ["what products", "list products", "show products"]):
            return IntentTaxonomy.PRODUCTS, ["products", "list"]
        if any(p in q_lower for p in ["what services", "list services", "show services"]):
            return IntentTaxonomy.SERVICES, ["services", "list"]
        if any(p in q_lower for p in ["what solutions", "list solutions", "show solutions"]):
            return IntentTaxonomy.SOLUTIONS, ["solutions", "list"]

        # General Overview / Explanation
        if any(p in q_lower for p in ["what is", "tell me about", "overview", "explain", "describe"]):
            return IntentTaxonomy.OVERVIEW, ["overview"]

        return IntentTaxonomy.UNKNOWN, ["unknown"]

    # ------------------------------------------------------------------
    # Query signals & explicit evidence
    # ------------------------------------------------------------------
    _ASPECT_WORDS = {
        "price", "prices", "pricing", "cost", "costs", "fee", "fees", "quote", "subscription", "plan", "plans",
        "benefit", "benefits", "advantage", "advantages", "roi", "value", "why", "choose",
        "feature", "features", "capability", "capabilities", "function", "functions", "functionality", "module", "modules",
        "analytics", "workflow", "workflows", "process", "step", "steps", "onboarding", "implementation",
        "user", "users", "audience", "suitable", "meant", "designed", "ideal", "customers", "faq", "faqs",
        "demo", "contact", "reach", "explain", "describe", "overview", "use", "used", "uses", "using", "do", "does",
    }

    _TYPO_TARGETS = ("services", "service", "products", "product", "solutions", "solution", "offerings", "industries")
    # Real words that sit close to a catalog word ("who it serves") and must never be "corrected"
    _NOT_TYPOS = {"serves", "served", "server", "servers", "serving", "servings", "servicing", "production", "productive",
                  "producer", "producers", "produces", "produced", "solving", "solvent", "offering", "industry"}

    def _correct_catalog_typos(self, query: str) -> str:
        """'what servicds do you provide' -> 'services'. Only unknown words that are near-misses of a catalog word
        are changed, so real vocabulary (registry terms, stopwords) is never rewritten."""
        def fix(m: "re.Match") -> str:
            word = m.group(0)
            low = word.lower()
            if (len(low) < 6 or low in _CATALOG_WORDS or low in _STOPWORDS or low in self._registry_vocab
                    or low in self._NOT_TYPOS):
                return word
            try:
                from rapidfuzz import fuzz
            except ImportError:
                return word
            best = max(self._TYPO_TARGETS, key=lambda t: fuzz.ratio(low, t))
            return best if fuzz.ratio(low, best) >= 85 else word
        return re.sub(r"[A-Za-z]+", fix, query)

    def _tokens(self, ql: str) -> List[str]:
        ql = re.sub(r"(?<=[a-z])['’](ve|re|ll|d|m|s|t)\b", "", ql)  # you've -> you, what's -> what
        return [t.strip("'-") for t in re.findall(r"[a-z0-9][a-z0-9'\-]*", ql)]

    def _query_signals(self, query: str):
        from semantic_arbitration import QuerySignals
        ql = query.lower()
        # The company name ("Citta AI" written as two words) is not domain content
        tokens = self._tokens(re.sub(r"\bcitta\s+ai\b", "cittaai", ql))
        cats = {_CATALOG_WORDS[t] for t in tokens if t in _CATALOG_WORDS}
        specific = cats - {"ALL"}
        catalog_scope = specific.pop() if len(specific) == 1 else "ALL"
        residue = [
            t for t in tokens
            if t not in _STOPWORDS and t not in _CATALOG_WORDS and t not in _CATALOG_FILLER
            and t not in self._ASPECT_WORDS and len(t) > 1 and not t.isdigit()
        ]
        try:
            from out_of_domain_detector import get_out_of_domain_detector
            ood = get_out_of_domain_detector().is_out_of_domain(query)[0]
        except Exception:
            ood = False
        return QuerySignals(
            has_pronoun=bool(_PRONOUN.search(ql)),
            company_reference=bool(re.search(r"\b(cittaai|citta ai|citta)\b", ql)),
            catalog_request=bool(_CATALOG_TRIGGERS.search(ql)) or bool(cats),
            catalog_scope=catalog_scope,
            comparison=bool(_COMPARISON.search(ql)),
            residue=residue,
            ood_detector=ood,
        )

    def _explicit_mentions(self, ql: str, residue: List[str]) -> List[Tuple[str, float, str]]:
        """Registry names/aliases literally present in the query (longest match wins), plus typo-tolerant matches."""
        covered: List[Tuple[int, int]] = []
        found: List[Tuple[int, str, float, str]] = []
        for alias, eid in self._alias_patterns:
            if alias in _WEAK_ALIASES or (len(alias) < 3 and alias not in {"os"}):
                continue
            for m in re.finditer(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", ql):
                s, e = m.span()
                if any(s < ce and e > cs for cs, ce in covered):
                    continue
                covered.append((s, e))
                multiword = " " in alias or "_" in alias or "-" in alias
                found.append((s, eid, 0.95 if multiword or len(alias) >= 5 else 0.85, alias))

        if not found and residue:
            try:
                from rapidfuzz import fuzz
                # single words from the content residue; multi-word grams from all non-stopwords so product
                # suffixes like "os" participate ("farma os" ~ "pharma os")
                words = [t for t in self._tokens(ql) if t not in _STOPWORDS]
                grams = set(residue)
                grams |= {" ".join(words[i:i + 2]) for i in range(len(words) - 1)}
                grams |= {" ".join(words[i:i + 3]) for i in range(len(words) - 2)}
                best = None
                for g in grams:
                    for alias, eid in self._alias_patterns:
                        if (alias in _WEAK_ALIASES or len(alias) < 5 or alias.count(" ") != g.count(" ")
                                or eid not in self.index.entity_ids):
                            continue
                        r = fuzz.ratio(g, alias)
                        # multi-word names tolerate one more edit ("farma os" 82 vs "finance os" 42 against "pharma os")
                        if r >= (80 if " " in g else 86) and (best is None or r > best[0]):
                            best = (r, eid, alias)
                if best:
                    found.append((ql.find(best[2].split()[0][:3]), best[1], 0.80, f"~{best[2]}"))
            except ImportError:
                pass

        found.sort(key=lambda f: f[0])
        mentions, seen = [], set()
        for _, eid, conf, alias in found:
            if eid not in seen:
                seen.add(eid)
                mentions.append((eid, conf, alias))
        # The company's own name is only the subject when nothing else is being asked about
        if len(mentions) > 1 or residue:
            mentions = [m for m in mentions if m[0] != "company_info"] or ([] if residue else mentions)
        return mentions

    def _mentions_joined(self, ql: str, mentions: List[Tuple[str, float, str]]) -> bool:
        """True when two named offerings are joined as a pair ("X and Y", "X or Y", "X / Y"), not just both present
        ("I run an online store and juggle inventory" names two things but asks about neither pair)."""
        spans = []
        for _, _, alias in mentions:
            if alias.startswith("~"):
                continue
            m = re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", ql)
            if m:
                spans.append(m.span())
        spans.sort()
        for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
            between = [t for t in self._tokens(ql[e1:s2]) if t not in _CATALOG_WORDS and t not in _CATALOG_FILLER]
            if between and len(between) <= 3 and between[0] in {"and", "or", "vs", "versus", "&"} or re.fullmatch(r"\s*[/&,]\s*", ql[e1:s2] or "x"):
                return True
        return False

    def _unknown_product_name(self, ql: str, explicit: List[str]) -> Optional[str]:
        """A product-shaped name ("Finance OS") that the registry doesn't know must not be mapped to its nearest neighbour."""
        if explicit:
            return None
        for m in re.finditer(r"\b([a-z][a-z0-9&\-]*(?:\s[a-z][a-z0-9&\-]*)?)\s+(os|platform|suite|software|product|app|tool|bot|system)\b", ql):
            head = m.group(1).split()[-1]
            if head in _STOPWORDS or head in _CATALOG_FILLER or head in self._ASPECT_WORDS or head in {"ai", "your", "an", "the"}:
                continue
            name = f"{head} {m.group(2)}"
            if name in self.alias_to_entity or head in self.alias_to_entity:
                continue
            # "X OS / platform / suite" reads as a product name; generic nouns ("payroll software") only count as an
            # unknown product when the descriptive word appears nowhere in the registry's content
            if m.group(2) in ("os", "platform", "suite") or head not in self._registry_vocab:
                return name
        return None

    def _bge_distribution(self, ranked) -> Dict[str, float]:
        from semantic_entity_index import ENTITY_RELEVANCE_FLOOR
        if not ranked:
            return {}
        relevance = max(0.0, min(1.0, (ranked[0].score - ENTITY_RELEVANCE_FLOOR) / 0.08))
        if relevance <= 0.0:
            return {}
        return {c.value: c.prob * relevance for c in ranked if c.prob * relevance >= 0.01}

    def _multi_entities(self, ql: str, mentions: List[Tuple[str, float, str]]) -> List[str]:
        from semantic_entity_index import ENTITY_RELEVANCE_FLOOR
        ents = [m[0] for m in mentions if m[0] in self.index.entity_ids or m[0] in self.registry.entities]
        for seg in _SEGMENT_SPLIT.split(ql):
            seg = (seg or "").strip()
            if not seg:
                continue
            seg_res = [t for t in self._tokens(seg) if t not in _STOPWORDS and t not in _CATALOG_WORDS and t not in _CATALOG_FILLER and t not in self._ASPECT_WORDS]
            if not seg_res:
                continue
            seg_m = self._explicit_mentions(seg, seg_res)
            if seg_m:
                cand = seg_m[0][0]
            else:
                top = self.index.rank_entities(seg, top_k=2)
                if not top or top[0].prob < 0.5 or top[0].score < ENTITY_RELEVANCE_FLOOR + 0.03:
                    continue
                cand = top[0].value
            if cand not in ents and cand not in GENERIC_ENTITIES and cand != "company_info":
                ents.append(cand)
        return [e for e in ents if e not in GENERIC_ENTITIES and e != "company_info"]

    def _aspect_distributions(self, query: str, frame: str, frame_emb, domain_entity: bool) -> Dict[str, Dict[str, float]]:
        """
        Rules read the original query (aliases like "marketing workflows" contain aspect words);
        BGE reads the question frame, where catalog entity names are replaced by "it", so
        "Who is Education OS meant for?" is judged as "who is it meant for?".
        """
        from semantic_entity_index import ASPECT_RELEVANCE_FLOOR
        from semantic_arbitration import COMPANY_ASPECT_ENTITY
        rules: Dict[str, float] = {}
        for text in (query, frame):
            primary, matched = self._classify_semantic_aspect(text, IntentTaxonomy.UNKNOWN)
            explicit = matched != ["OVERVIEW"] or re.search(r"\b(what is|tell me about|overview|explain|describe|about)\b", text.lower())
            if explicit:
                rules = {primary: 0.9 if primary != "OVERVIEW" else 0.7}
                break
        intent_aspect = _INTENT_ASPECT.get(self._detect_intent_rules(query)[0])
        if intent_aspect and intent_aspect not in rules:
            rules[intent_aspect] = 0.8 if not rules else 0.4
        # A bare name ("WhatsApp Marketing Platform") leaves no question frame to classify
        if not [t for t in self._tokens(frame) if t != "it" and t not in _STOPWORDS]:
            return {"rules": rules, "bge": {}, "prior": {"OVERVIEW": 0.4}}
        ranked = self.index.rank_aspects(frame, frame_emb)
        relevance = max(0.0, min(1.0, (ranked[0].score - ASPECT_RELEVANCE_FLOOR) / 0.06))
        bge = {}
        for c in ranked[:3]:
            # Company-level aspects are only inferred semantically when no domain entity is in play
            if domain_entity and c.value in COMPANY_ASPECT_ENTITY:
                continue
            if c.prob * relevance >= 0.01:
                bge[c.value] = c.prob * relevance
        return {"rules": rules, "bge": bge, "prior": {"OVERVIEW": 0.4}}

    # ------------------------------------------------------------------
    # LLM adjudication (only for genuinely ambiguous decisions)
    # ------------------------------------------------------------------
    def _get_provider(self):
        if self._provider_resolved:
            return self.provider
        self._provider_resolved = True
        if self.enable_llm is False or not getattr(config, "SEMANTIC_LLM_ADJUDICATION", True):
            return None
        name = str(getattr(config, "LLM_PROVIDER", "")).lower()
        key = {"groq": "GROQ_API_KEY", "nvidia": "NVIDIA_API_KEY", "gemini": "GEMINI_API_KEY",
               "openai": "OPENAI_API_KEY", "claude": "CLAUDE_API_KEY"}.get(name)
        if not key or not (getattr(config, key, "") or os.environ.get(key)):
            logger.info("[QueryIntelligenceEngine] No LLM credentials configured; semantic adjudication disabled.")
            return None
        try:
            from llm_provider import get_llm_provider
            self.provider = get_llm_provider(name, {k: getattr(config, k) for k in dir(config) if k.isupper()})
        except Exception as e:
            logger.warning(f"[QueryIntelligenceEngine] Could not create LLM provider for adjudication: {e}")
            self.provider = None
        return self.provider

    @staticmethod
    def _run_coroutine(coro, timeout: float):
        """Run an async provider call from sync code, whether or not an event loop is already running."""
        import asyncio
        import concurrent.futures

        async def _bounded():
            return await asyncio.wait_for(coro, timeout)

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_bounded())
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, _bounded()).result(timeout + 1)

    def _llm_adjudicate(self, query: str, candidates: List[str], context_entity: Optional[str], q_emb=None) -> Optional[Dict[str, Any]]:
        provider = self._get_provider()
        if provider is None:
            return None
        cache_key = (query.strip().lower(), context_entity, tuple(candidates))
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]

        aspects = list(ASPECT_PROTOTYPES_NAMES)
        # Each candidate: its summary plus the catalog passage closest to this question, so the adjudicator judges
        # on the offering's actual content rather than a one-line tagline
        cand_lines = "\n".join(
            f"- {c}: {self.index.describe(c)}"
            + (f"\n    most relevant content: {self.index.best_exemplar(c, q_emb)}" if q_emb is not None else "")
            for c in candidates)
        system = (
            "You map a website visitor's question to CittaAI's knowledge catalog. Do not answer the question.\n"
            "Pick the single catalog entity the visitor is asking about, judging by meaning rather than shared words. "
            "If the question fits several candidates equally well, set ambiguous=true. If it is not about CittaAI or its "
            "offerings at all, set out_of_domain=true and entity=null.\n"
            "Respond with JSON only: {\"entity\": <candidate id or null>, \"confidence\": <0..1>, "
            f"\"aspect\": <one of {aspects}>, \"ambiguous\": <bool>, \"out_of_domain\": <bool>}}"
        )
        user = f"Candidates:\n{cand_lines}\n"
        if context_entity:
            user += f"\nThe conversation was previously about: {context_entity}\n"
        user += f"\nVisitor question: {query}"
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        try:
            raw = self._run_coroutine(
                provider.generate(messages, model=config.MODEL_NAME, temperature=0.0),
                float(getattr(config, "SEMANTIC_LLM_TIMEOUT_S", 8)),
            )
            raw = raw[0] if isinstance(raw, tuple) else str(raw)
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                raise ValueError(f"no JSON in adjudicator response: {raw[:120]}")
            parsed = json.loads(m.group(0))
        except Exception as e:
            logger.warning(f"[QueryIntelligenceEngine] LLM adjudication failed, using calibrated fallback: {e}")
            return None

        ent = parsed.get("entity")
        if ent in ("null", "None", "", None) or (ent not in candidates and ent not in self.registry.entities):
            ent = None
        asp = parsed.get("aspect") if parsed.get("aspect") in ASPECT_PROTOTYPES_NAMES else None
        verdict = {
            "entity": ent,
            "confidence": max(0.0, min(1.0, float(parsed.get("confidence", 0.7) or 0.7))),
            "aspect": asp,
            "aspect_confidence": 0.8,
            "ambiguous": bool(parsed.get("ambiguous")),
            "out_of_domain": bool(parsed.get("out_of_domain")),
        }
        self._llm_cache[cache_key] = verdict
        return verdict

    def _aspect_uncertain(self, decision: SemanticDecision, frame_content: bool = False) -> bool:
        if decision.needs_clarification or decision.scope.value != "SINGLE_ENTITY":  # comparisons default to overview
            return False
        if decision.entity.source == "aspect":  # company aspect already named the entity
            return False
        from semantic_arbitration import DEFAULT_ASPECT_CONFIDENCE
        conf_floor = float(getattr(config, "SEMANTIC_ASPECT_ACCEPT_CONFIDENCE", 0.4))
        margin_floor = float(getattr(config, "SEMANTIC_ASPECT_ACCEPT_MARGIN", 0.2))
        if decision.aspect.confidence < conf_floor or (decision.aspect.margin or 0.0) < margin_floor:
            return True
        # An aspect chosen only by the OVERVIEW default is a guess when the visitor has named an offering (or refers
        # to one in context) and asks something specific about it. When they only describe a need without naming
        # an offering, an overview of the matching offering is the right answer, so no adjudication.
        defaulted = decision.aspect.value == "OVERVIEW" and decision.aspect_candidates[:1] == [("OVERVIEW", DEFAULT_ASPECT_CONFIDENCE)]
        named = "rules" in (decision.entity.source or "") or decision.entity.source == "context"
        return defaulted and frame_content and named

    def _llm_adjudicate_aspect(self, query: str, decision: SemanticDecision) -> Optional[Dict[str, Any]]:
        """Ask the LLM only which canonical aspect the question targets, for an already-resolved entity."""
        provider = self._get_provider()
        if provider is None:
            return None
        subjects = decision.entities or [decision.entity.value]
        titles = ", ".join(self.entity_catalog.get(e, {}).get("title", e) for e in subjects if e)
        cache_key = ("aspect", query.strip().lower(), titles)
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]
        definitions = "\n".join(f"- {a}: {d}" for a, d in ENTITY_ASPECT_DEFINITIONS.items())
        system = (
            "You classify which part of an offering a website visitor is asking about. Do not answer the question.\n"
            f"Choose exactly one aspect from this list:\n{definitions}\n"
            "If the question fits two aspects equally well, put the other one in ambiguous_with; otherwise leave it empty.\n"
            'Respond with JSON only: {"aspect": <aspect>, "confidence": <0..1>, "ambiguous_with": [<aspect>], "reason": <short>}'
        )
        user = f"Offering being discussed: {titles}\nVisitor question: {query}"
        try:
            raw = self._run_coroutine(
                provider.generate([{"role": "system", "content": system}, {"role": "user", "content": user}],
                                  model=config.MODEL_NAME, temperature=0.0),
                float(getattr(config, "SEMANTIC_LLM_TIMEOUT_S", 8)),
            )
            raw = raw[0] if isinstance(raw, tuple) else str(raw)
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                raise ValueError(f"no JSON in aspect adjudicator response: {raw[:120]}")
            parsed = json.loads(m.group(0))
        except Exception as e:
            logger.warning(f"[QueryIntelligenceEngine] Aspect adjudication failed, keeping arbitrated aspect: {e}")
            return None
        aspect = str(parsed.get("aspect") or "").upper()
        if aspect not in ENTITY_ASPECT_DEFINITIONS:
            logger.warning(f"[QueryIntelligenceEngine] Aspect adjudicator returned non-canonical aspect '{aspect}'; ignored")
            return None
        others = [str(a).upper() for a in (parsed.get("ambiguous_with") or []) if str(a).upper() in ENTITY_ASPECT_DEFINITIONS and str(a).upper() != aspect]
        try:
            confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.7))))
        except (TypeError, ValueError):
            confidence = 0.7
        # A confident verdict that also lists an alternative is self-contradictory (and varies by provider);
        # ask the visitor to choose only when the adjudicator itself is unsure.
        if confidence >= float(getattr(config, "SEMANTIC_ASPECT_AMBIGUITY_MAX_CONFIDENCE", 0.75)):
            others = []
        verdict = {"aspect": aspect, "confidence": confidence, "ambiguous_with": others[:2]}
        self._llm_cache[cache_key] = verdict
        return verdict

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def analyze_query(
        self,
        query: str,
        normalized_query: Optional[str] = None,
        session_id: str = "default",
        active_entity: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Any] = None
    ) -> SemanticDecision:
        from semantic_arbitration import arbitrate

        t0 = time.perf_counter()
        q = self._correct_catalog_typos((normalized_query or query).strip())
        ql = q.lower()
        ctx_entity = active_entity or getattr(context, "active_entity", None)
        if ctx_entity and ctx_entity not in self.registry.entities:
            ctx_entity = None
        ctx_entities = [e for e in (getattr(context, "active_entities", None) or []) if e in self.registry.entities]
        cache_key = (ql, ctx_entity, tuple(ctx_entities))
        if cache_key in self._decision_cache:
            return copy.deepcopy(self._decision_cache[cache_key])

        signals = self._query_signals(q)
        # The visitor's own job title ("I'm the CTO of a bank") must not match CittaAI's leaders or the LEADERSHIP aspect
        ql = _SELF_ROLE.sub(" ", ql)
        mentions = self._explicit_mentions(ql, signals.residue)
        if signals.catalog_request or (ctx_entity and signals.has_pronoun):
            # "what can CittaAI do for it?" — the pronoun, not the company name, is the subject
            mentions = [m for m in mentions if m[0] != "company_info"]
        if not mentions and len(ctx_entities) == 2 and _OTHER_ONE.search(ql):
            # "the other one" is a context reference to the pair member that isn't currently active
            ctx_entity = ([e for e in ctx_entities if e != ctx_entity] or ctx_entities[1:])[0]
            signals.has_pronoun = True
        explicit = [m[0] for m in mentions]

        q_emb = self.index.encode_query(q)
        # The company's own name says nothing about *which* offering is meant
        q_ent = re.sub(r"\b(cittaai|citta ai|citta)('s)?\b", " ", q, flags=re.IGNORECASE).strip()
        ent_emb = self.index.encode_query(q_ent) if q_ent and q_ent != q and signals.residue else q_emb
        ranked = self.index.rank_entities(q_ent, ent_emb, top_k=5)
        rules_dist: Dict[str, float] = {}
        for eid, conf, _ in mentions:
            rules_dist[eid] = max(rules_dist.get(eid, 0.0), conf / len(mentions))
        # Company-level entities (contact, about, awards) are embedding catch-alls for generic requests;
        # they are reached through company aspects or explicit names, never by similarity alone.
        bge_dist = {e: p for e, p in self._bge_distribution(ranked).items() if e not in self.company_level}
        entity_dists = {"rules": rules_dist, "bge": bge_dist}
        domain_entity = any(e not in self.company_level for e in explicit) or bool(
            entity_dists["bge"] and max(entity_dists["bge"], key=entity_dists["bge"].get) not in self.company_level
            and max(entity_dists["bge"].values()) >= 0.5)
        frame = ql
        for eid, _, alias in mentions:
            # Only catalog entities are masked; company-level aliases ("founders", "email") ARE the aspect
            if not alias.startswith("~") and eid not in self.company_level:
                frame = re.sub(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", "it", frame)
        frame_emb = self.index.encode_query(frame) if frame != ql else q_emb
        aspect_dists = self._aspect_distributions(ql, frame, frame_emb, domain_entity)
        # Two names in one sentence are only a comparison when joined as alternatives/pairs
        joined = self._mentions_joined(ql, mentions)
        multi = self._multi_entities(ql, mentions) if (signals.comparison or (len(explicit) >= 2 and joined)) else []
        signals.unknown_product = self._unknown_product_name(ql, explicit)
        # "both" / "the two" refer back to a pair; only resolvable from conversation context
        if _PAIR_REFERENCE.search(ql) and len(multi) < 2:
            if len(ctx_entities) == 2:
                multi, signals.comparison = list(ctx_entities), True
                explicit = explicit or list(ctx_entities)
            else:
                signals.unresolved_pair = True

        intent_val, _ = self._detect_intent_rules(q)
        intent = FieldEvidence(intent_val, 0.9 if intent_val != IntentTaxonomy.UNKNOWN else 0.0, "rules")

        signals.entity_evidence = bool(explicit) or bool(
            entity_dists["bge"] and max(entity_dists["bge"].values()) >= 0.5)
        args = dict(entity_dists=entity_dists, aspect_dists=aspect_dists, intent=intent, signals=signals,
                    explicit_entities=explicit, multi_entities=multi, context_entity=ctx_entity, query_text=q,
                    company_level=self.company_level)
        decision = arbitrate(**args, llm_available=self._get_provider() is not None)
        entity_verdict = None
        llm_calls = {"entity_attempted": False, "entity_ok": False, "aspect_attempted": False, "aspect_ok": False}
        if decision.needs_llm_adjudication:
            candidates = list(dict.fromkeys(explicit + ([ctx_entity] if ctx_entity else []) + [c.value for c in ranked]))[:6]
            entity_verdict = self._llm_adjudicate(q, candidates, ctx_entity, q_emb=ent_emb)
            llm_calls.update(entity_attempted=True, entity_ok=entity_verdict is not None)
            decision = arbitrate(**args, llm_verdict=entity_verdict, llm_available=False)

        # Field-specific aspect adjudication: the entity is locked; only the aspect is re-examined
        frame_content = bool([t for t in self._tokens(frame) if t != "it" and t not in _STOPWORDS and t not in _CATALOG_FILLER
                              and t not in _CATALOG_WORDS and t not in self._ASPECT_WORDS and len(t) > 2])
        if self._aspect_uncertain(decision, frame_content) and self._get_provider() is not None:
            verdict = self._llm_adjudicate_aspect(q, decision)
            llm_calls.update(aspect_attempted=True, aspect_ok=verdict is not None)
            if verdict:
                merged = dict(entity_verdict or {})
                merged.update({"aspect": verdict["aspect"], "aspect_confidence": verdict["confidence"]})
                decision = arbitrate(**args, llm_verdict=merged, llm_available=False)
                decision.llm_invoked = entity_verdict is not None
                decision.aspect_llm_invoked = True
                # A bare product name ("marktech 360??") gets its overview, not "overview or capabilities?": when the
                # overview is one of the candidates it already covers the others, so asking adds nothing
                if (verdict.get("ambiguous_with") and frame_content
                        and "OVERVIEW" not in [verdict["aspect"]] + verdict["ambiguous_with"]):
                    decision.needs_clarification = True
                    decision.clarification_options = [
                        {"aspect": a, "title": a.replace("_", " ").title(), "entity_id": decision.entity.value}
                        for a in [verdict["aspect"]] + verdict["ambiguous_with"]][:3]
                    decision.diagnostic_trace.append(f"aspect ambiguous between {[o['aspect'] for o in decision.clarification_options]} -> clarification")

        # Company-level entities have one canonical aspect ("results of the FMCG campaign" is a case-study question)
        etype = str((self.registry.entities.get(decision.entity.value) or {}).get("type", "")).lower()
        canonical = {"case_study": "CLIENTS_CASE_STUDIES", "award": "RECOGNITION", "leadership": "LEADERSHIP", "contact": "CONTACT",
                     "company": "OVERVIEW"}.get(etype)
        if canonical and decision.aspect.value != canonical and not decision.needs_clarification:
            decision.aspect = FieldEvidence(canonical, max(decision.aspect.confidence, 0.9), "entity_type", 1.0)

        # Presentation metadata used by downstream consumers
        decision.requested_sections, decision.target_registry_types = self._map_aspect_to_schema([decision.aspect.value or "OVERVIEW"])
        if decision.entity.source == "context":
            decision.conversation_reference = ctx_entity
        term, cat = self._detect_category_term(q)
        decision.category_term_used_by_user = cat
        if decision.entity.value in self.entity_catalog:
            decision.registry_category = self.entity_catalog[decision.entity.value]["category"]
        if decision.needs_clarification and not decision.clarification_options:
            pool: Dict[str, float] = {}
            for dist in list(decision.raw_evidence.get("entity", {}).values()):
                for v, p in dist.items():
                    pool[v] = pool.get(v, 0.0) + p
            for c in ranked:
                pool.setdefault(c.value, c.prob * 0.1)
            # Offer only catalog offerings with real support; otherwise ask an open question instead of
            # listing unrelated pages ("Contact Information") as candidates
            ranked_pool = [(v, p) for v, p in sorted(pool.items(), key=lambda kv: kv[1], reverse=True)
                           if v not in self.company_level and v in self.registry.entities]
            best = ranked_pool[0][1] if ranked_pool else 0.0
            top = [(v, p) for v, p in ranked_pool if p >= max(0.05, 0.25 * best)][:3] if best >= 0.3 else []
            from knowledge_operation_executor import display_name
            decision.clarification_options = [
                {"entity_id": v, "title": display_name(self.registry.entities.get(v) or {}) or v} for v, _ in top
            ]
        decision.raw_evidence["bge_ranked"] = [(c.value, round(c.score, 4), round(c.prob, 4)) for c in ranked]
        decision.raw_evidence["llm_calls"] = llm_calls

        decision = canonicalize_and_validate(decision, registry=self.registry)
        decision.original_query = query
        decision.normalized_query = q
        decision.diagnostic_trace.append(f"latency_ms={round((time.perf_counter() - t0) * 1000, 1)}")

        try:
            log_path = Path(__file__).resolve().parent / "logs" / "semantic_decisions.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(decision.to_dict(), default=str) + "\n")
        except Exception as e:
            logger.debug(f"Telemetry logging notice: {e}")
        self._decision_cache[cache_key] = copy.deepcopy(decision)
        while len(self._decision_cache) > 512:
            self._decision_cache.pop(next(iter(self._decision_cache)))
        return decision

    def interpret_query(self, query: str, session_id: str = "default") -> SemanticDecision:
        return self.analyze_query(query, session_id=session_id)

    async def interpret(
        self,
        query: str,
        normalized_query: str,
        session_id: str = "default",
        active_entity: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> SemanticDecision:
        return self.analyze_query(
            query=query,
            normalized_query=normalized_query,
            session_id=session_id,
            active_entity=active_entity,
            history=history
        )


from semantic_entity_index import ASPECT_PROTOTYPES as _ASPECT_PROTOTYPES
ASPECT_PROTOTYPES_NAMES = list(_ASPECT_PROTOTYPES.keys())

_engine_instance = None


def get_query_intelligence_engine(provider=None) -> QueryIntelligenceEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = QueryIntelligenceEngine(provider=provider)
    elif provider is not None and _engine_instance.provider is None:
        _engine_instance.provider = provider
        _engine_instance._provider_resolved = True
    return _engine_instance
