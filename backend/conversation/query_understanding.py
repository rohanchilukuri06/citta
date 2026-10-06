import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Common Spelling Corrections & Normalizations
SPELLING_CORRECTIONS = {
    "educaton": "education",
    "pharmaa": "pharma",
    "whatsap": "whatsapp",
    "realestate": "real estate",
    "ecommerce": "e-commerce",
    "e commerce": "e-commerce",
    "spics": "spices",
    "jewelery": "jewellery",
    "jewelery brand": "jewellery brand",
    "citta ai": "CittaAI",
    "cittaai": "CittaAI"
}

ABBREVIATION_EXPANSIONS = {
    "ceo": "Chief Executive Officer",
    "cto": "Chief Technology Officer",
    "coo": "Chief Operating Officer",
    "cmo": "Chief Marketing Officer",
    "bd": "Business Development",
    "lms": "Learning Management System"
}

NAVIGATION_VERBS = [
    r"\bopen\b", r"\bvisit\b", r"\btake me to\b", r"\bnavigate to\b", r"\bgo to\b", 
    r"\bshow page\b", r"\bopen page\b", r"\blaunch\b", r"\bredirect me\b", r"\bmove to\b"
]

DETAILED_TRIGGERS = [
    "explain in detail", "deep dive", "in detail", "detailed", "everything about", "in-depth", "full overview"
]

LEADERSHIP_TITLES = {
    "ceo": "Akhil Reddy",
    "chief executive officer": "Akhil Reddy",
    "chief exec": "Akhil Reddy",
    "founder": "Saladi Chandra Balaji / Akhil Reddy",
    "co-founder": "Saladi Chandra Balaji / Akhil Reddy",
    "cto": "Akhil Reddy",
    "chief technology officer": "Akhil Reddy",
    "coo": "Saladi Chandra Balaji",
    "chief operating officer": "Saladi Chandra Balaji",
    "cmo": "Ganesh Gandhi Vadalani",
    "chief marketing officer": "Ganesh Gandhi Vadalani",
    "marketing head": "Ganesh Gandhi Vadalani",
    "operations head": "Harish Nerati",
    "sales head": "Harish Nerati",
    "e-commerce head": "Aravind Reddy",
    "ecommerce head": "Aravind Reddy",
    "business development head": "Parvatha Mohan",
    "bd head": "Parvatha Mohan"
}

@dataclass
class QueryUnderstandingResult:
    query: str
    normalized_query: str
    intent: str  # leadership_lookup, person_lookup, catalog, case_study_detail, capability_lookup, fact, nav_request, follow_up, clarification, statistics, general
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    target: Optional[str] = None
    section: Optional[str] = None
    detail_level: str = "compact"  # compact, standard, detailed
    navigation_intent: bool = False
    confidence: float = 1.0
    requires_clarification: bool = False
    clarification_options: List[Dict[str, str]] = field(default_factory=list)
    is_follow_up: bool = False

def normalize_query(query: str) -> str:
    """Pre-processes raw user query for spelling, abbreviations, and canonical terms."""
    if not query:
        return ""
    q = query.strip()
    
    # Lowercase for dictionary lookup
    q_words = q.split()
    corrected_words = []
    for word in q_words:
        w_clean = word.lower().strip(",.?!")
        if w_clean in SPELLING_CORRECTIONS:
            corrected_words.append(SPELLING_CORRECTIONS[w_clean])
        else:
            corrected_words.append(word)
            
    q_norm = " ".join(corrected_words)
    
    # Regex phrase replacements
    for typo, fix in SPELLING_CORRECTIONS.items():
        q_norm = re.sub(rf"\b{re.escape(typo)}\b", fix, q_norm, flags=re.IGNORECASE)
        
    return q_norm

class QueryUnderstandingEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QueryUnderstandingEngine, cls).__new__(cls)
        return cls._instance

    def analyze(self, query: str, active_context: Optional[Dict[str, Any]] = None) -> QueryUnderstandingResult:
        """
        Analyzes normalized query and produces a unified QueryUnderstandingResult object.
        """
        norm_q = normalize_query(query)
        q_lower = norm_q.lower().strip()
        
        # 1. Navigation Intent Check
        is_nav = any(re.search(pat, q_lower) for pat in NAVIGATION_VERBS)
        
        # 2. Detail Level Check
        detail_level = "compact"
        if any(trig in q_lower for trig in DETAILED_TRIGGERS):
            detail_level = "detailed"
        elif any(trig in q_lower for trig in ["how does it work", "how it works", "explain"]):
            detail_level = "standard"

        # 3. Statistics & Metrics Queries
        if any(w in q_lower for w in ["clients", "users served", "statistics", "metrics", "how many clients", "client count", "roi delivered"]):
            return QueryUnderstandingResult(
                query=query,
                normalized_query=norm_q,
                intent="statistics",
                entity_id="company_info",
                entity_type="COMPANY_INFO",
                target="STATISTICS",
                section="overview",
                detail_level=detail_level,
                navigation_intent=is_nav,
                confidence=0.98,
                requires_clarification=False
            )
            
        # 4. Leadership & Team Lookups (Fix Issue 1: "team" maps to Leadership Team)
        if q_lower in ["team", "the team", "our team", "citta team", "cittaai team", "meet the team", "meet our team", "leadership", "leadership team", "management", "management team", "executives", "executive team", "founders", "leaders"]:
            return QueryUnderstandingResult(
                query=query,
                normalized_query=norm_q,
                intent="leadership_lookup",
                entity_id="leadership_info",
                entity_type="LEADERSHIP",
                target="TEAM",
                section="leadership",
                detail_level=detail_level,
                navigation_intent=is_nav,
                confidence=0.99,
                requires_clarification=False
            )

        # "CEO" maps to Akhil Reddy (CittaAI CEO; Vinay Velivela is CEO of Fixity Technologies)
        for role_key, person_name in LEADERSHIP_TITLES.items():
            if re.search(rf"\b{re.escape(role_key)}\b", q_lower):
                return QueryUnderstandingResult(
                    query=query,
                    normalized_query=norm_q,
                    intent="leadership_lookup",
                    entity_id="leadership_info",
                    entity_type="LEADERSHIP",
                    target=role_key.upper(),
                    section="leadership",
                    detail_level=detail_level,
                    navigation_intent=is_nav,
                    confidence=0.99,
                    requires_clarification=False
                )
                
        if any(re.search(rf"\b{re.escape(name)}\b", q_lower) for name in ["akhil", "vinay", "saladi", "ganesh", "harish", "aravind", "parvatha"]) or any(re.search(rf"\b{re.escape(role)}\b", q_lower) for role in ["ceo", "cto", "coo", "cmo", "chief executive", "chief technology", "chief operating", "chief marketing"]):
            return QueryUnderstandingResult(
                query=query,
                normalized_query=norm_q,
                intent="person_lookup",
                entity_id="leadership_info",
                entity_type="LEADERSHIP",
                target=norm_q,
                section="leadership",
                detail_level=detail_level,
                navigation_intent=is_nav,
                confidence=0.95,
                requires_clarification=False
            )

        # 5. Case Study Lookups (Fix Issue 3: Explain one case study)
        if "case stud" in q_lower:
            if any(w in q_lower for w in ["jewellery", "fmcg", "spices", "roi"]):
                cs_id = "jewellery_brand_roi" if "jewellery" in q_lower else ("fmcg_social_growth" if "fmcg" in q_lower else "b2b_spices_export")
                return QueryUnderstandingResult(
                    query=query,
                    normalized_query=norm_q,
                    intent="case_study_detail",
                    entity_id=cs_id,
                    entity_type="CASE_STUDY",
                    target=cs_id,
                    section="overview",
                    detail_level=detail_level,
                    navigation_intent=is_nav,
                    confidence=0.95,
                    requires_clarification=False
                )
            else: # Generic case study request ("Explain one case study", "show case studies")
                return QueryUnderstandingResult(
                    query=query,
                    normalized_query=norm_q,
                    intent="catalog",
                    entity_id=None,
                    entity_type="CASE_STUDY",
                    target="CASE_STUDIES",
                    section="overview",
                    detail_level=detail_level,
                    navigation_intent=is_nav,
                    confidence=0.98,
                    requires_clarification=False
                )

        # 6. Catalog Lookups
        if q_lower in ["show solutions", "list solutions", "solutions", "show products", "list products", "products", "show services", "list services", "services"]:
            etype = "SOLUTIONS" if "solution" in q_lower else ("PRODUCTS" if "product" in q_lower else "SERVICES")
            return QueryUnderstandingResult(
                query=query,
                normalized_query=norm_q,
                intent="catalog",
                entity_id=None,
                entity_type=etype,
                target=etype,
                section="overview",
                detail_level=detail_level,
                navigation_intent=is_nav,
                confidence=0.98,
                requires_clarification=False
            )

        # 7. Ambiguous Query Check
        if q_lower in ["tell me about ai", "ai solutions", "tell me about platform"]:
            return QueryUnderstandingResult(
                query=query,
                normalized_query=norm_q,
                intent="clarification",
                confidence=0.40,
                requires_clarification=True,
                clarification_options=[
                    {"label": "Enterprise AI OS", "query": "Explain Enterprise AI OS"},
                    {"label": "Education OS", "query": "Explain Education OS"},
                    {"label": "Agentic AI Consulting", "query": "Explain Enterprise & Agentic AI service"},
                    {"label": "View All Solutions", "query": "Show Solutions"}
                ]
            )

        # Default fallback result
        return QueryUnderstandingResult(
            query=query,
            normalized_query=norm_q,
            intent="fact",
            detail_level=detail_level,
            navigation_intent=is_nav,
            confidence=0.85
        )

def get_query_understanding_engine() -> QueryUnderstandingEngine:
    return QueryUnderstandingEngine()
