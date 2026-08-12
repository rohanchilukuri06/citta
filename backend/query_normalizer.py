import re
import logging
from typing import Dict, Any, List, Tuple, Set, Optional

logger = logging.getLogger(__name__)

# Try loading rapidfuzz for spelling correction
try:
    from rapidfuzz import process, fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

# Production-grade Query Normalizer Pipeline:
# 1. Normalize
# 2. Safe spell correction (RapidFuzz -> Exact vocabulary -> Leave unchanged)
# 3. Abbreviation expansion
# 4. Synonym expansion
# 5. Canonical entity lookup

# Configuration for semantic synonyms
SYNONYM_MAP = {
    "client": "partners",
    "clients": "partners",
    "customer": "partners",
    "customers": "partners",

    "partner": "partners",
    
    "award": "recognition",
    "awards": "recognition",
    "achievement": "recognition",
    "achievements": "recognition",
    "winner": "recognition",
    "win": "recognition",
    "won": "recognition",
    
    "office": "location",
    "offices": "location",
    "address": "location",
    "addresses": "location",
    "hq": "location",
    "headquarters": "location",
    
    "team": "leadership",
    "management": "leadership",
    "executives": "leadership",
    "leaders": "leadership",
    "founder": "leadership",
    "founders": "leadership",
    "ceo": "ceo",
    "cto": "cto",
    "coo": "coo",
    "cmo": "cmo",
    
    "products": "products",
    "platforms": "products",
    "platform": "products",
    "tools": "products",
    "tool": "products",
    "software": "products",
    
    "services": "services",
    "consulting": "services",
    "offerings": "services",
    "advisory": "services",
    "solutions": "solutions",
    
    "cost": "pricing",
    "price": "pricing",
    "rates": "pricing",
    "fee": "pricing",
    "fees": "pricing",
    "charges": "pricing",
    "charge": "pricing",
    "quote": "pricing",
    "quotation": "pricing"
}

# Common explicit typo mapping (for compound typos like realestate -> real estate)
COMMON_TYPO_MAP = {
    "realestate": "real estate",
    "whastapp": "whatsapp",
    "pharmaa": "pharma",
    "influncer": "influencer",
    "servises": "services",
    "srevices": "services",
    "srevice": "service",
    "serivces": "services",
    "servies": "services",
    "servise": "service",
    "soultions": "solutions",
    "compny": "company",
    "wroks": "works",
    "influence": "influencer",
    "educaton": "education",
    "pharama": "pharma",
    "whats app": "whatsapp",
    "whatsap": "whatsapp"
}

def clean_text(query: str) -> str:
    """Stage 1: Base normalization (lowercase, strip special characters except hyphens and slashes)."""
    if not query:
        return ""
    q = query.lower().strip()
    q = re.sub(r"[^\w\s\-\/]", "", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q

def clean_text(query: str) -> str:
    """Stage 1: Base normalization (lowercase, strip special characters except hyphens and slashes)."""
    if not query:
        return ""
    q = query.lower().strip()
    q = re.sub(r"[^\w\s\-\/]", "", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q

STANDARD_BUSINESS_VOCABULARY = {
    "sector", "sectors", "industry", "industries", "company", "companies",
    "business", "businesses", "organization", "organizations", "university",
    "universities", "college", "colleges", "school", "schools", "hospital",
    "hospitals", "property", "properties", "management", "strategy", "support",
    "contact", "location", "solutions", "services", "products", "platform", "platforms",
    "weather", "cricket", "biryani", "recipe", "bitcoin"
}

def safe_spell_correction(
    query: str, 
    vocabulary_tokens: Set[str], 
    spell_threshold: float = 80.0
) -> Tuple[str, List[str]]:
    """
    Stage 2: Safe Spell Correction.
    Order per token:
      1. Explicit common typo replacement map (for compound words like realestate -> real estate)
      2. Exact standard business vocabulary check (e.g. sector, industry, university)
      3. RapidFuzz check using QRatio (exact full-token edit distance, match score >= spell_threshold)
      4. Exact vocabulary check
      5. Leave token unchanged if low confidence match or unknown token
    Never silently replaces a token with low confidence.
    """
    if not query:
        return query, []

    corrected_query = query
    corrections_log = []

    # 1. Check explicit compound typo replacements
    for typo, fixed in COMMON_TYPO_MAP.items():
        pattern = rf"\b{re.escape(typo)}\b"
        if re.search(pattern, corrected_query, re.IGNORECASE):
            corrected_query = re.sub(pattern, fixed, corrected_query, flags=re.IGNORECASE)
            corrections_log.append(f"{typo} → {fixed}")

    if not vocabulary_tokens:
        return corrected_query, corrections_log
        
    tokens = corrected_query.split()
    corrected_tokens = []
    vocab_list = list(vocabulary_tokens)
    
    for token in tokens:
        # Ignore numbers or short tokens
        if token.isdigit() or len(token) <= 2:
            corrected_tokens.append(token)
            continue

        # Check standard business vocabulary to prevent over-correction (e.g. sector -> vector)
        if token.lower() in STANDARD_BUSINESS_VOCABULARY:
            corrected_tokens.append(token)
            continue
            
        # Exact vocabulary check
        if token in vocabulary_tokens:
            corrected_tokens.append(token)
            continue
            
        # RapidFuzz fuzzy match check using QRatio (full string similarity)
        corrected = token
        if HAS_RAPIDFUZZ and vocab_list:
            try:
                match = process.extractOne(token, vocab_list, scorer=fuzz.QRatio)
                if match and match[1] >= spell_threshold:
                    best_match = match[0]
                    if best_match.lower() != token.lower():
                        corrected = best_match
                        corrections_log.append(f"{token} → {corrected}")
            except Exception as e:
                logger.warning(f"RapidFuzz spell correction failed on token '{token}': {e}")
                
        # Leave token unchanged if no high confidence match
        corrected_tokens.append(corrected)
        
    return " ".join(corrected_tokens), corrections_log

def expand_abbreviations(query: str, abbreviations: Dict[str, str]) -> str:
    """Stage 3: Abbreviation Expansion."""
    if not query or not abbreviations:
        return query
        
    abbr_lower = {k.lower().strip(): v for k, v in abbreviations.items()}
    
    tokens = query.split()
    expanded = []
    for token in tokens:
        if token in abbr_lower:
            expanded.append(abbr_lower[token])
        else:
            expanded.append(token)
            
    q_str = " ".join(expanded)
    
    # Handle multi-word abbreviation keys sorted by length descending
    for abbr, full_form in sorted(abbr_lower.items(), key=lambda x: len(x[0]), reverse=True):
        if " " in abbr:
            q_str = re.sub(rf"\b{re.escape(abbr)}\b", full_form, q_str, flags=re.IGNORECASE)
            
    return q_str

def expand_synonyms(query: str) -> str:
    """Stage 4: Synonym Expansion."""
    if not query:
        return query
        
    tokens = query.split()
    mapped_tokens = []
    for token in tokens:
        if token in SYNONYM_MAP:
            mapped_tokens.append(SYNONYM_MAP[token])
        else:
            mapped_tokens.append(token)
            
    q_str = " ".join(mapped_tokens)
    
    for syn_key, target in sorted(SYNONYM_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if " " in syn_key:
            q_str = re.sub(rf"\b{re.escape(syn_key)}\b", target, q_str, flags=re.IGNORECASE)
            
    return q_str

def canonical_entity_lookup(
    query: str,
    entity_lookup: Optional[Dict[str, str]] = None,
    vocabulary: Optional[Dict[str, str]] = None
) -> Tuple[str, Optional[str]]:
    """
    Stage 5: Canonical Entity Lookup.
    Resolves query to a canonical entity ID if present in entity_lookup or vocabulary.
    """
    lookup_map = entity_lookup or vocabulary or {}
    if not query or not lookup_map:
        return query, None

    q_lower = query.lower().strip()
    sorted_keys = sorted(lookup_map.keys(), key=lambda k: len(k), reverse=True)
    for phrase in sorted_keys:
        target_id = lookup_map[phrase]
        phrase_clean = phrase.lower().strip()
        if phrase_clean and (phrase_clean == q_lower or re.search(rf"\b{re.escape(phrase_clean)}\b", q_lower)):
            return query, target_id
            
    return query, None

def normalize_query_pipeline(
    query: str,
    vocabulary: Dict[str, str],
    abbreviations: Dict[str, str],
    fuzz_threshold: float = 80.0,
    entity_lookup: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Production-grade Query Normalization Pipeline:
    1. Normalize
    2. Safe spell correction (RapidFuzz -> Exact vocabulary -> Leave unchanged)
    3. Abbreviation expansion
    4. Synonym expansion
    5. Canonical entity lookup
    """
    # 1. Normalize
    cleaned = clean_text(query)
    
    # Extract vocabulary tokens for spell correction
    vocab_tokens = set()
    if vocabulary:
        for phrase in vocabulary.keys():
            for t in phrase.split():
                if len(t) > 2 and not t.isdigit():
                    vocab_tokens.add(t.lower())
                    
    # 2. Safe spell correction
    corrected, spell_log = safe_spell_correction(cleaned, vocab_tokens, fuzz_threshold)
    
    # 3. Abbreviation expansion
    expanded_abbr = expand_abbreviations(corrected, abbreviations)
    
    # 4. Synonym expansion
    syn_expanded = expand_synonyms(expanded_abbr)
    
    # 5. Canonical entity lookup
    import config
    if getattr(config, "USE_NEW_ENTITY_RESOLVER", True):
        import core.entity_resolver as core_resolver
        res = core_resolver.resolve(syn_expanded)
        canonical_entity = res["entity_id"]
        final_query = syn_expanded
    else:
        final_query, canonical_entity = canonical_entity_lookup(
            syn_expanded,
            entity_lookup=entity_lookup,
            vocabulary=vocabulary
        )
    
    return {
        "original_query": query,
        "normalized_query": final_query,
        "spell_corrections": spell_log,
        "canonical_entity": canonical_entity,
        "success": True
    }
