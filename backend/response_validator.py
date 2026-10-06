import re
import logging
from typing import Dict, Any, Tuple, Optional, List, Union

_PUBLISHED_TEXT: Dict[int, str] = {}


def _in_published_content(reg: Any, phrase: str) -> bool:
    """A product phrase that appears anywhere in CittaAI's registry or crawled website text (e.g. the tagline
    "One-Stop Platform for Real Estate Operations") is published wording, not an invented product."""
    key = id(reg)
    if key not in _PUBLISHED_TEXT:
        import json
        from pathlib import Path
        parts = [json.dumps(getattr(reg, "entities", {}), default=str)]
        for obj in (getattr(reg, "registry_by_id", {}) or {}).values():
            try:
                parts.append(obj.model_dump_json())
            except Exception:
                pass
        site = Path(__file__).resolve().parent / "knowledge" / "site" / "cittaai_live.json"
        if site.exists():
            parts.append(site.read_text(encoding="utf-8"))
        _PUBLISHED_TEXT[key] = " ".join(" ".join(parts).lower().replace("‑", "-").replace("–", "-").split())
    return " ".join(phrase.lower().split()) in _PUBLISHED_TEXT[key]

logger = logging.getLogger(__name__)

# Valid CittaAI static page routes
VALID_STATIC_ROUTES = {
    "/", "/contact", "/about", "/services", "/recognition", "/case-studies"
}

FALLBACK_MESSAGE = "I don't have enough verified information to answer that."

def validate_response(
    text: str,
    resolved_entity: Optional[str] = None,
    resolved_section: Optional[str] = None,
    requested_entities: Optional[List[str]] = None,
    registry: Optional[Any] = None,
    retry_count: int = 0,
    return_metrics: bool = False,
    evidence_text: Optional[str] = None
) -> Union[Tuple[bool, str], Tuple[bool, str, Dict[str, Any]]]:
    """
    Production Response Validator:
    Verifies LLM response against strict grounding and completeness constraints:
    1. Resolved entity matches response
    2. Requested section matches response
    3. Response completeness across all requested entities
    4. No unsupported products
    5. No unsupported technologies
    6. No fake pricing
    7. No unsupported case studies
    8. No unsupported statistics
    """
    from knowledge_registry import get_registry
    reg = registry or get_registry()

    # Phrases that appear verbatim in the evidence the answer was generated from are grounded,
    # whatever the registry-name heuristics below would otherwise conclude.
    evidence_norm = " ".join((evidence_text or "").lower().replace("‑", "-").replace("–", "-").split())

    def in_evidence(phrase: str) -> bool:
        return bool(evidence_norm) and " ".join(phrase.lower().split()) in evidence_norm
    
    metrics: Dict[str, Any] = {
        "valid": True,
        "reasons": [],
        "unsupported_products": [],
        "unsupported_technologies": [],
        "unsupported_pricing": [],
        "unsupported_case_studies": [],
        "unsupported_statistics": [],
        "entity_matched": True,
        "section_matched": True,
        "completeness_matched": True,
        "retry_count": retry_count
    }

    if not text or not text.strip():
        metrics["valid"] = False
        metrics["reasons"].append("Empty response text")
        final_text = FALLBACK_MESSAGE if retry_count >= 1 else text
        if return_metrics:
            return False, final_text, metrics
        return False, final_text

    # Normalize unicode non-breaking spaces
    text = re.sub(r"[\u202f\xa0\u200b]", " ", text)
    text_lower = text.lower()

    # 1. Resolved Entity Validation
    if resolved_entity and resolved_entity not in ["company_info", "faq_general", "contact", "location"] and hasattr(reg, "get_entity"):
        ent = reg.get_entity(resolved_entity)
        if ent:
            ent_name = (ent.get("name") or ent.get("title") or resolved_entity).lower()
            aliases = [str(a).lower() for a in ent.get("aliases", [])]
            base_name = resolved_entity.replace("_", " ").replace(" v2", "").replace("_v2", "").lower()
            title_words = [w.lower() for w in ent_name.split() if len(w) > 3 and w.lower() not in ["and", "with", "for", "the", "os"]]
            matched_entity = (
                ent_name in text_lower or 
                resolved_entity.lower() in text_lower or 
                base_name in text_lower or
                any(a in text_lower for a in aliases if len(a) > 2) or
                any(tw in text_lower for tw in title_words)
            )
            if not matched_entity:
                metrics["entity_matched"] = False
                metrics["valid"] = False
                metrics["reasons"].append(f"Response does not match resolved entity '{resolved_entity}'")

    # 2. Requested Section Validation
    if resolved_section and resolved_section.lower() != "overview":
        sec_keywords = [resolved_section.lower().replace("_", " ")]
        sec_name_clean = resolved_section.lower()
        if sec_name_clean == "how_it_works":
            sec_keywords.extend(["how", "work", "process", "step", "flow", "integrate", "working"])
        elif sec_name_clean == "benefits":
            sec_keywords.extend(["benefit", "advantage", "value", "roi", "save", "boost", "improve"])
        elif sec_name_clean == "features":
            sec_keywords.extend(["feature", "capability", "module", "function", "tool", "spec"])
        elif sec_name_clean == "integrations":
            sec_keywords.extend(["integrate", "connection", "api", "crm", "erp", "shopify", "plugin"])
            
        matched_section = any(k in text_lower for k in sec_keywords)
        if not matched_section:
            metrics["section_matched"] = False
            metrics["valid"] = False
            metrics["reasons"].append(f"Response does not match requested section '{resolved_section}'")

    # 2.1 Multi-Entity Response Completeness Validation
    if requested_entities and len(requested_entities) > 1:
        missing_ents = []
        for req_ent in requested_entities:
            req_name = str(req_ent).lower()
            if hasattr(reg, "get_entity"):
                ent_obj = reg.get_entity(req_ent)
                if ent_obj:
                    req_name = (ent_obj.get("name") or ent_obj.get("title") or req_ent).lower()
            if req_name not in text_lower:
                missing_ents.append(str(req_ent))
        if missing_ents:
            metrics["completeness_matched"] = False
            metrics["valid"] = False
            metrics["reasons"].append(f"Response incomplete: missing requested entity/entities '{', '.join(missing_ents)}'")

    # 3. Unsupported Products Check
    # Verify product mentions in text against reg.entities and reg.products
    ALLOWED_GENERIC_DESCRIPTORS = {
        "unified", "single", "series", "interactive", "comprehensive", "digital",
        "automation", "software", "management", "learning", "cloud", "centralized",
        "integrated", "enterprise", "scalable", "secure", "modern", "core", "smart",
        "ai", "custom", "advanced", "multi", "flexible", "intuitive", "powerful",
        "data", "intelligent", "analytics", "business", "technical", "corporate", "operational", "the",
        "this", "that", "role-based", "review", "cpv", "reporting", "assessment", "monitoring", "healthcare", "clinical",
        "mobile", "compliant", "web", "desktop", "native", "cloud-native", "end-to-end", "purpose-built", "built-in",
        "of", "a", "an", "and", "or", "in", "on", "at", "for", "to", "with", "by", "from", "is", "are", "our", "your",
        "each", "every", "all", "any", "some", "other", "such", "new", "next", "first", "key", "main", "top",
        "gen", "messaging", "s", "modular", "integration", "agent", "cittaai", "caas", "free", "flagship", "discovery",
        "consumer", "information", "analysis", "health", "health-information", "health-info", "open-source", "open"
    }
    # A product claim is a *named* product ("Finance OS", "HealthX Platform"): capitalised name + product noun.
    # Lowercase descriptions ("an operations platform", "either OS") are ordinary language, not product claims.
    product_phrases = [m.lower() for m in re.findall(r"\b([A-Z][A-Za-z0-9_-]*\s+(?:OS|Os|Platform|Tool|App))\b", text)]
    valid_products = set()
    if hasattr(reg, "entities"):
        for ent_id, ent in reg.entities.items():
            valid_products.add(ent_id.lower())
            p_name = ent.get("name") or ent.get("title")
            if p_name:
                valid_products.add(p_name.lower())
            for a in ent.get("aliases", []):
                valid_products.add(str(a).lower())

    for prod_p in product_phrases:
        first_word = prod_p.split()[0].lower()
        if first_word in ALLOWED_GENERIC_DESCRIPTORS:
            continue
        if (prod_p not in valid_products and "operating system" not in prod_p and not in_evidence(prod_p)
                and not _in_published_content(reg, prod_p)):
            if not any(prod_p in vp for vp in valid_products):
                metrics["unsupported_products"].append(prod_p)
                metrics["valid"] = False
                metrics["reasons"].append(f"Unsupported product detected: '{prod_p}'")

    # 4. Unsupported Technologies Check
    known_techs = set(["python", "fastapi", "react", "sqlite", "postgresql", "bigquery", "spark", "airflow", "dbt", "llm", "rag", "bge", "huggingface", "pytorch", "tensorflow", "openai", "gemini", "shopify", "woocommerce", "whatsapp", "meta", "apis", "api"])
    if hasattr(reg, "entities"):
        for ent in reg.entities.values():
            for t in ent.get("technologies", []):
                known_techs.add(str(t).lower())

    tech_mentions = re.findall(r"\b([a-z0-9]+\.(?:js|py|ai|io))\b", text_lower)
    for tech in tech_mentions:
        if tech not in known_techs and not in_evidence(tech):
            metrics["unsupported_technologies"].append(tech)
            metrics["valid"] = False
            metrics["reasons"].append(f"Unsupported technology detected: '{tech}'")

    # 5. Fake Pricing Check
    # Catch raw numerical prices ($X, Rs. Y, X USD) that are not present in ground truth
    price_matches = re.findall(r"(\$\d+(?:\,\d+)*(?:\.\d+)?|\brs\.\s*\d+|\b\d+\s*(?:usd|eur|gbp|inr)\b)", text_lower)
    if price_matches:
        valid_prices = []
        if resolved_entity and hasattr(reg, "get_entity"):
            ent = reg.get_entity(resolved_entity)
            if ent:
                valid_prices.append(str(ent.get("pricing") or "").lower())
        for p_match in price_matches:
            if not any(p_match in vp for vp in valid_prices if vp) and not in_evidence(p_match):
                metrics["unsupported_pricing"].append(p_match)
                metrics["valid"] = False
                metrics["reasons"].append(f"Fake/unverified pricing detected: '{p_match}'")

    # 6. Unsupported Case Studies Check
    valid_cs = set()
    if hasattr(reg, "registry_index"):
        cs_reg = reg.registry_index.get("CASE_STUDIES", {})
        if cs_reg:
            for cs in cs_reg.get("entities", []):
                cs_n = (cs.get("name") or cs.get("title") or "").lower()
                if cs_n:
                    valid_cs.add(cs_n)
                    
    cs_mentions = re.findall(r"\b([a-z0-9\s]+\s+case\s+study)\b", text_lower)
    for cs_m in cs_mentions:
        cs_clean = cs_m.replace("case study", "").strip()
        if cs_clean and not any(cs_clean in vcs for vcs in valid_cs) and not in_evidence(cs_m):
            metrics["unsupported_case_studies"].append(cs_m)
            metrics["valid"] = False
            metrics["reasons"].append(f"Unsupported case study detected: '{cs_m}'")

    # 7. Unsupported Statistics Check
    stat_matches = re.findall(r"(\b\d{1,3}(?:\.\d+)?%|\b\d+x\s+roi\b|\b\d+x\b)", text_lower)
    valid_stats = set()
    if hasattr(reg, "entities"):
        for ent in reg.entities.values():
            stat_str = str(ent).lower()
            for sm in stat_matches:
                if sm in stat_str:
                    valid_stats.add(sm)

    for stat in stat_matches:
        if stat not in valid_stats and not in_evidence(stat):
            metrics["unsupported_statistics"].append(stat)
            metrics["valid"] = False
            metrics["reasons"].append(f"Unsupported statistic detected: '{stat}'")

    # 8. Route Link Validation
    links = re.findall(r"\[[^\]]*\]\(((?:http://localhost:\d+|https?://cittaai\.com)?/[^)]*)\)", text)
    for link in links:
        path = link
        if "http" in link:
            path_match = re.search(r"https?://[^/]+(/?.*)", link)
            if path_match:
                path = path_match.group(1)
        path_clean = path.split("#")[0].strip()
        if path_clean not in VALID_STATIC_ROUTES and (not hasattr(reg, "routes") or path_clean not in reg.routes):
            metrics["valid"] = False
            metrics["reasons"].append(f"Hallucinated link route detected: '{path_clean}'")

    # Category Consistency Validation
    for prod in getattr(reg, "products", []):
        p_name = prod["name"].lower()
        if p_name in text_lower:
            mismatch_patterns = [
                rf"\b{re.escape(p_name)}\s+(?:is\s+a\s+)?(?:solution|service)\b",
                rf"\bour\s+{re.escape(p_name)}\s+(?:service|solution)\b"
            ]
            if any(re.search(pat, text_lower) for pat in mismatch_patterns):
                metrics["valid"] = False
                metrics["reasons"].append(f"Product '{prod['name']}' misclassified as service/solution.")

    for sol in getattr(reg, "solutions", []):
        s_name = sol["name"].lower()
        if s_name in text_lower:
            mismatch_patterns = [
                rf"\b{re.escape(s_name)}\s+(?:is\s+a\s+)?(?:product|service)\b",
                rf"\bour\s+{re.escape(s_name)}\s+(?:product|service)\b"
            ]
            if any(re.search(pat, text_lower) for pat in mismatch_patterns):
                metrics["valid"] = False
                metrics["reasons"].append(f"Solution '{sol['name']}' misclassified as product/service.")

    # 9. Internal Exposure Check
    internal_exposure_keywords = ["i searched", "i found", "retrieved chunks", "vector store", "in the database", "in the registry"]
    if any(k in text_lower for k in internal_exposure_keywords):
        metrics["valid"] = False
        metrics["reasons"].append("Internal exposure phrasing detected in response.")

    # 10. Evidence Coverage Evaluation & Claim Traceability
    # Distinguish between Missing Evidence and Low Confidence. Low confidence alone must NEVER trigger a disclaimer.
    # EvidenceCoverage values: SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED
    if metrics["valid"]:
        metrics["evidence_coverage"] = "SUPPORTED"
    elif any(r for r in metrics["reasons"] if "does not match requested section" in r or "unsupported_pricing" in r or "unsupported_statistics" in r):
        # Specific requested aspect or detail missing from evidence
        metrics["evidence_coverage"] = "PARTIALLY_SUPPORTED"
    else:
        metrics["evidence_coverage"] = "UNSUPPORTED"

    # Quality Score Calculation (0.0 to 1.0)
    deductions = len(metrics["reasons"]) * 0.2
    metrics["quality_score"] = max(0.0, min(1.0, 1.0 - deductions))

    # Determine Output Text & Handling based on EvidenceCoverage
    if metrics["evidence_coverage"] == "SUPPORTED":
        final_text = text
    elif metrics["evidence_coverage"] == "PARTIALLY_SUPPORTED":
        if retry_count >= 1:
            # Append concise disclaimer explaining ONLY what information is unavailable
            missing_details = []
            if metrics.get("unsupported_pricing"):
                missing_details.append("specific pricing")
            if metrics.get("unsupported_statistics"):
                missing_details.append("specific performance statistics")
            if not metrics.get("section_matched"):
                missing_details.append(f"details for section '{resolved_section}'")
            
            missing_str = ", ".join(missing_details) if missing_details else "some of the requested details"
            disclaimer = f"\n\n*Note:* Information regarding {missing_str} is currently unavailable in the verified records."
            if not text.endswith(disclaimer):
                final_text = text + disclaimer
            else:
                final_text = text
        else:
            final_text = text
    else:  # UNSUPPORTED
        if retry_count >= 1:
            logger.warning(f"Response Validation Failed on retry {retry_count}. Returning fallback message. Reasons: {metrics['reasons']}")
            final_text = FALLBACK_MESSAGE
        else:
            logger.warning(f"Response Validation Failed on initial check. Single retry indicated. Reasons: {metrics['reasons']}")
            final_text = text

    if return_metrics:
        return metrics["valid"], final_text, metrics
    return metrics["valid"], final_text

