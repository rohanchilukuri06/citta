import re
import logging
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger(__name__)

# Section trigger regex patterns
SECTION_TRIGGERS = {
    "overview": [r"\babout\b", r"\boverview\b", r"\bdescribe\b", r"\bwhat\s+is\b", r"\bwhat\s+are\b", r"\bsummary\b", r"\bcompany\b"],
    "mission": [r"\bmission\b", r"\bour\s+mission\b", r"\bcompany\s+mission\b"],
    "vision": [r"\bvision\b", r"\bour\s+vision\b", r"\bcompany\s+vision\b"],
    "values": [r"\bvalues\b", r"\bcore\s+values\b", r"\bour\s+values\b"],
    "certifications": [r"\bcertification\b", r"\bcertifications\b", r"\bcompliance\b", r"\baccreditation\b", r"\baccreditations\b", r"\bawards\b", r"\brecognition\b"],
    "how_it_works": [r"\bhow\b", r"\bhow\s+does\s+it\s+work\b", r"\bworking\b", r"\bworkflow\b", r"\bprocess\b", r"\barchitecture\b", r"\bflow\b", r"\bworkings\b"],
    "features": [r"\bfeatures\b", r"\bmodules\b", r"\bfunctions\b", r"\bcapabilities\b", r"\bwhat\s+does\s+it\s+do\b"],
    "benefits": [r"\bbenefits\b", r"\badvantages\b", r"\bvalue\b", r"\bwhy\s+should\b", r"\broi\b", r"\bwhy\s+use\b"],
    "best_for": [r"\bwho\s+should\s+use\b", r"\bbest\s+for\b", r"\bindustries\b", r"\bcustomers\b", r"\btarget\b", r"\bwho\s+is\s+it\s+for\b", r"\bwho\s+uses\b", r"\bdesigned\s+for\b", r"\bintended\s+users\b", r"\bintended\s+audience\b"],
    "implementation": [r"\bdeployment\b", r"\bsetup\b", r"\bimplementation\b", r"\bonboarding\b"],
    "integrations": [r"\bintegration\b", r"\bintegrations\b", r"\bcrm\b", r"\berp\b", r"\bshopify\b", r"\bapi\b", r"\bwebhooks\b", r"\bintegrate\b"],
    "faq": [r"\bfaq\b", r"\bfaqs\b", r"\bquestions\b", r"\bquestion\b", r"\bq&a\b"],
    "case_studies": [r"\bcase\s+study\b", r"\bcase\s+studies\b", r"\bsuccess\s+story\b", r"\bsuccess\s+stories\b", r"\bresults\b", r"\bmetrics\b"],
    "technologies": [r"\btechnology\b", r"\btechnologies\b", r"\btech\s+stack\b", r"\bframework\b", r"\bllm\b", r"\brag\b", r"\bagents\b"],
    "examples": [r"\bexample\b", r"\bexamples\b", r"\buse\s+case\b", r"\buse\s+cases\b", r"\bsample\b"],
    "related_entities": [r"\brelated\b", r"\bsimilar\b", r"\balso\b", r"\bdepends\b"]
}

# Semantic Synonym Groups dictionary for fast, embedding-free section resolution
SECTION_SYNONYMS: Dict[str, List[str]] = {
    "overview": [
        "about", "overview", "describe", "what is", "what are", "summary",
        "introduction", "intro", "explanation", "details", "info", "company"
    ],
    "mission": [
        "mission", "our mission", "company mission"
    ],
    "vision": [
        "vision", "our vision", "company vision"
    ],
    "values": [
        "values", "our values", "core values"
    ],
    "certifications": [
        "certifications", "certification", "compliance", "accreditations",
        "accreditation", "awards", "recognition", "certified"
    ],
    "how_it_works": [
        "how it works", "how does it work", "working", "workflow", "process",
        "pipeline", "steps", "architecture", "flow", "workings", "mechanism",
        "how to use", "execution"
    ],
    "features": [
        "features", "modules", "functions", "capabilities", "components",
        "specs", "what does it do", "tooling", "utilities"
    ],
    "benefits": [
        "benefits", "advantages", "value", "business value", "why use",
        "why should", "roi", "pros", "value prop", "value proposition",
        "gains", "merits", "why choose"
    ],
    "best_for": [
        "best for", "target audience", "who should use", "who is it for",
        "who uses", "target", "industries", "customers", "ideal for",
        "suitable for", "use case fit", "designed for", "intended users", "intended audience"
    ],
    "implementation": [
        "implementation", "deployment", "setup", "onboarding", "installation",
        "integration steps", "getting started"
    ],
    "integrations": [
        "integrations", "integration", "connectors", "crm", "erp", "shopify",
        "api", "apis", "webhooks", "plugins", "connect", "integrate"
    ],
    "faq": [
        "faq", "faqs", "questions", "question", "q&a", "frequently asked questions"
    ],
    "case_studies": [
        "case study", "case studies", "success story", "success stories",
        "results", "metrics", "roi metrics", "client stories"
    ],
    "technologies": [
        "technology", "technologies", "tech stack", "framework", "infrastructure",
        "llm", "rag", "agents", "tech"
    ],
    "examples": [
        "example", "examples", "use case", "use cases", "sample", "samples", "demonstration"
    ],
    "related_entities": [
        "related", "similar", "also", "depends", "dependencies"
    ]
}

def resolve_sections_dynamic(
    query: str,
    entity_data: Optional[Dict[str, Any]] = None,
    registry_meta: Optional[Dict[str, Any]] = None,
    active_section: Optional[str] = None,
    intent: Optional[str] = None
) -> List[str]:
    """
    Multi-section Resolver:
    Delegates to QueryIntelligenceEngine for schema-aware aspect section mapping.
    """
    try:
        from query_intelligence_engine import get_query_intelligence_engine
        qi = get_query_intelligence_engine()
        interp = qi.analyze_query(query)
        if interp.requested_sections:
            return interp.requested_sections
    except Exception as e:
        logger.warning(f"Section resolver delegation to QueryIntelligenceEngine notice: {e}")

    q_lower = query.lower()
    matched_sections = []
    
    for sec_name in sorted(SECTION_SYNONYMS.keys()):
        patterns = SECTION_TRIGGERS.get(sec_name, [])
        synonyms = SECTION_SYNONYMS.get(sec_name, [])
        
        hit = False
        for p in patterns:
            if re.search(p, q_lower):
                hit = True
                break
        if not hit:
            for s in synonyms:
                if re.search(rf"\b{re.escape(s)}\b", q_lower):
                    hit = True
                    break
                    
        if hit and sec_name not in matched_sections:
            matched_sections.append(sec_name)

    return matched_sections if matched_sections else ["overview"]

def resolve_section_dynamic(
    query: str,
    entity_data: Optional[Dict[str, Any]],
    registry_meta: Optional[Dict[str, Any]],
    active_section: Optional[str] = None,
    intent: Optional[str] = None,
    ambiguity_threshold: float = 0.15
) -> Tuple[Optional[str], float, Optional[Dict[str, Any]]]:
    """
    Section Resolver:
    Identifies primary requested section based on keywords, triggers, synonyms, and context.
    If multiple sections are ambiguous (difference < threshold), returns clarification options.
    """
    q_lower = query.lower()
    all_sections = resolve_sections_dynamic(query, entity_data, registry_meta, active_section, intent)
    
    # Check for ambiguity when multiple specific sections (e.g., benefits AND features) are present
    if " and " in q_lower and len(all_sections) >= 2 and not ("company" in q_lower or "mission" in q_lower or "vision" in q_lower):
        candidates = all_sections[:2]
        return None, 1.0, {
            "type": "clarification",
            "message": "Would you like:",
            "candidates": [{"id": c, "name": c.replace("_", " ").title()} for c in candidates]
        }

    primary = all_sections[0] if all_sections else "overview"
    return primary, 1.0, None
