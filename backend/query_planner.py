import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent
COMPILED_DIR = BACKEND_DIR / "knowledge" / "compiled"

# Load registry indices at import time
_entity_index: Dict[str, Any] = {}
_intent_examples: Dict[str, Any] = {}
_routing_map: Dict[str, Any] = {}

def load_indices():
    global _entity_index, _intent_examples, _routing_map
    entity_path = COMPILED_DIR / "entity_index.json"
    intent_path = COMPILED_DIR / "intent_examples.json"
    routing_path = COMPILED_DIR / "routing.json"
    
    if entity_path.exists():
        try:
            with open(entity_path, "r", encoding="utf-8") as f:
                _entity_index = json.load(f)
        except Exception as e:
            logger.error(f"Error loading entity_index.json: {e}")
            
    if intent_path.exists():
        try:
            with open(intent_path, "r", encoding="utf-8") as f:
                _intent_examples = json.load(f)
        except Exception as e:
            logger.error(f"Error loading intent_examples.json: {e}")
            
    if routing_path.exists():
        try:
            with open(routing_path, "r", encoding="utf-8") as f:
                _routing_map = json.load(f)
        except Exception as e:
            logger.error(f"Error loading routing.json: {e}")

load_indices()

# Representative queries for Stage 2 Semantic fallback
SEMANTIC_ANCHORS = {
    ("LIST", "PRODUCTS"): [
        "what products does cittaai offer",
        "show me your product list",
        "tell me about your product offerings",
        "what platforms do you sell",
        "list the products"
    ],
    ("LIST", "SERVICES"): [
        "what services do you provide",
        "what are your professional services",
        "list your service offerings",
        "show me your services",
        "advisory and engineering services"
    ],
    ("LIST", "SOLUTIONS"): [
        "what solutions do you offer",
        "show me your industry vertical solutions",
        "what operating systems do you have",
        "list the os platforms",
        "show solutions"
    ],
    ("FACT", "COMPANY_INFO"): [
        "tell me about the company history",
        "what is your core intelligence engine",
        "tell me about CittaAI's overview"
    ],
    ("FACT", "LEADERSHIP"): [
        "who founded CittaAI",
        "who is the CEO",
        "tell me about your team and leadership",
        "who started the company"
    ],
    ("FACT", "CONTACT"): [
        "what is your email address and phone number",
        "how do i contact you",
        "support phone number and email"
    ],
    ("FACT", "LOCATION"): [
        "where is your head office located",
        "address and location map",
        "where are you located"
    ]
}

_anchor_embeddings: Dict[Tuple[str, str], np.ndarray] = {}

def init_anchor_embeddings(model):
    global _anchor_embeddings
    for key, queries in SEMANTIC_ANCHORS.items():
        embeddings = []
        for q in queries:
            prefix = "Represent this sentence for searching relevant passages: " if "bge" in model.get_sentence_features.__self__.__class__.__name__.lower() else ""
            emb = model.encode(prefix + q, normalize_embeddings=True)
            embeddings.append(emb)
        _anchor_embeddings[key] = np.mean(embeddings, axis=0)

# --- Query Rewriter ---
def rewrite_query(query: str) -> str:
    """
    Normalizes and rewrites user inputs to match canonical platform names.
    This increases embedding match consistency and deterministic classifier triggers.
    """
    q = query.lower().strip()
    
    # Exact or word-boundary replacements
    replacements = {
        r"\bwa\b": "WhatsApp Marketing Platform",
        r"\bwhatsapp\b": "WhatsApp Marketing Platform",
        r"\benterprise os\b": "Enterprise AI OS",
        r"\becommerce os\b": "E-Commerce OS",
        r"\bpharma os\b": "Pharma & Healthcare OS",
        r"\brealestate os\b": "Real Estate OS",
        r"\breal estate os\b": "Real Estate OS",
        r"\breal estate\b(?! os)": "Real Estate OS",
        r"\brealestate\b(?! os)": "Real Estate OS",
        r"\becommerce\b(?! os)": "E-Commerce OS",
        r"\baddress\b": "office location",
        r"\bai consulting\b": "AI Strategy & Advisory",
        r"\bai advisory\b": "AI Strategy & Advisory",
        r"\bceo\b": "leadership",
        r"\bfounder\b": "leadership",
        r"\bclients\b": "partners"
    }
    
    for pattern, canonical in replacements.items():
        q = re.sub(pattern, canonical.lower(), q)
        
    return q

def is_in_domain(q_clean: str) -> bool:
    """
    Intercepts and validates if a query is related to CittaAI.
    """
    words = set(re.findall(r"\b[a-z0-9_-]+\b", q_clean))
    
    business_keywords = {
        "cittaai", "citta", "fixity", "company", "product", "platform", "service", 
        "services", "products", "platforms", "consulting", "solution", "solutions",
        "operating", "system", "systems", "whatsapp", "influencer", "leadership", 
        "founder", "ceo", "cto", "coo", "team", "achievement", "achievements", 
        "recognition", "recognitions", "award", "awards", "careers", "jobs", "hiring", 
        "clients", "customers", "partners", "brands", "companies", "contact", "email", 
        "phone", "address", "location", "located", "office", "offices", "headquarters", "tower", 
        "vinay", "velivela", "akhil", "reddy", "chandra", "balaji", "ganesh", "gandhi", 
        "harish", "nerati", "aravind", "mohan", "technology", 
        "technologies", "challenge", "retention", "rate", "apply", "work", "join", 
        "certification", "certifications", "milestone", "milestones", "hybiz", "apis", 
        "msme", "marketing", "ai", "tech", "enterprise", "agentic", "generative", 
        "ai-powered", "os", "ap", "real", "estate", "pharma", "education", "healthcare", 
        "smart", "cities", "open", "weekend", "weekends", "hours", "time", "buy", "purchase",
        "demo", "book", "schedule", "pricing", "cost", "price", "case", "study", "studies"
    }
    
    if business_keywords.intersection(words):
        return True
        
    phrases = [
        "how to start", "who are you", "what is cittaai", "who is cittaai", 
        "data engineering", "ai strategy", "martech", "advisory", "roadmaps", 
        "success stories", "case studies", "head office", "where is", "where are",
        "get in touch"
    ]
    if any(p in q_clean for p in phrases):
         return True
         
    return False

# Response Transformation Intent Patterns
TRANSFORMATION_PATTERNS = {
    "SIMPLIFY": [
        r"\bsimplify\b",
        r"\bmake\s+it\s+simple\b",
        r"\bsimple\s+english\b",
        r"\bexplain\s+simply\b",
        r"\beasy\s+words\b",
        r"\bexplain\s+like\s+i'm\s+new\b",
        r"\bexplain\s+like\s+i\s+am\s+new\b",
        r"\bexplain\s+in\s+simple\s+english\b"
    ],
    "ELABORATE": [
        r"\btell\s+me\s+more\b",
        r"\bgo\s+deeper\b",
        r"\bdetailed\s+explanation\b",
        r"\belaborate\b",
        r"\bexplain\s+in\s+more\s+detail\b",
        r"\bgo\s+into\s+detail\b",
        r"\bexplain\s+further\b",
        r"\bexpand\b"
    ],
    "SUMMARIZE": [
        r"\bsummarize\b",
        r"\btldr\b",
        r"\bbriefly\b",
        r"\bsummary\b",
        r"\bgive\s+me\s+a\s+summary\b",
        r"\bshort\s+version\b"
    ],
    "EXAMPLE": [
        r"\bgive\s+an\s+example\b",
        r"\breal\s+world\s+example\b",
        r"\buse\s+case\b",
        r"\bexample\b",
        r"\bgive\s+me\s+an\s+example\b",
        r"\bshow\s+an\s+example\b",
        r"\bshow\s+me\s+an\s+example\b"
    ],
    "REPHRASE": [
        r"\brewrite\b",
        r"\brephrase\b",
        r"\bbetter\s+wording\b",
        r"\bprofessional\s+rewrite\b",
        r"\brephrase\s+this\b"
    ],
    "TRANSLATE": [
        r"\btranslate\b",
        r"\bin\s+(telugu|hindi|spanish|french|german|mandarin|tamil|kannada|bengali|marathi)\b",
        r"\bto\s+(telugu|hindi|spanish|french|german|mandarin|tamil|kannada|bengali|marathi)\b",
        r"\binto\s+(telugu|hindi|spanish|french|german|mandarin|tamil|kannada|bengali|marathi)\b"
    ],
    "FOLLOW_UP": [
        r"\bhow\s+does\s+(?:it|this|that)\s+work\b",
        r"\bhow\s+(?:it|this|that)\s+works\b",
        r"\bwhy\b",
        r"\bwho\s+uses\s+(?:it|this|that)\b",
        r"\bwho\s+uses\b",
        r"\bwhat\s+about\s+pricing\b",
        r"\bis\s+(?:it|this|that)\s+secure\b"
    ]
}

def classify_query(query: str, model=None, skip_transform: bool = False) -> Dict[str, Any]:
    """
    Two-stage query classifier. Loads dynamic patterns from intent_examples.json.
    """
    load_indices()
    
    # 0. Rewrite query
    q_rewritten = rewrite_query(query)
    q_clean = q_rewritten.lower().strip()
    
    # Intercept conversational flow intents early to avoid out-of-domain or category fallback issues
    greeting_words = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"}
    thanks_words = {"thanks", "thank you", "great", "awesome", "perfect", "thankyou"}
    goodbye_words = {"bye", "goodbye", "see you", "see ya"}
    
    if any(re.search(r"\b" + re.escape(w) + r"\b", q_clean) for w in goodbye_words):
        return {
            "query_type": "GOODBYE",
            "domain": "COMPANY_INFO",
            "confidence": 1.0,
            "matched_entity": None
        }
    if any(re.search(r"\b" + re.escape(w) + r"\b", q_clean) for w in thanks_words):
        return {
            "query_type": "THANKS",
            "domain": "COMPANY_INFO",
            "confidence": 1.0,
            "matched_entity": None
        }
    if any(re.search(r"\b" + re.escape(w) + r"\b", q_clean) for w in greeting_words) or q_clean in ["hi", "hello", "hey"]:
        return {
            "query_type": "GREETING",
            "domain": "COMPANY_INFO",
            "confidence": 1.0,
            "matched_entity": None
        }
    if q_clean in ["who are you", "what is your name", "what do you do", "what can you do", "how can you help me", "help"]:
        return {
            "query_type": "SMALL_TALK",
            "domain": "COMPANY_INFO",
            "confidence": 1.0,
            "matched_entity": None
        }
    
    # Intercept response transformation intents
    if not skip_transform:
        for intent, patterns in TRANSFORMATION_PATTERNS.items():
            if any(re.search(pattern, q_clean) for pattern in patterns):
                logger.info(f"Query classified as TRANSFORMATION intent: {intent}")
                return {
                    "query_type": intent,
                    "domain": "UNKNOWN_IN_DOMAIN",
                    "confidence": 1.0,
                    "matched_entity": None
                }
    
    # 1. In-Domain Detector check
    if not is_in_domain(q_clean):
        logger.info(f"Query '{query}' classified as OUT_OF_DOMAIN.")
        return {
            "query_type": "OUT_OF_DOMAIN",
            "domain": "OUT_OF_DOMAIN",
            "confidence": 1.0,
            "matched_entity": None
        }

    matched_entity = None
    domain = None
    query_type = None

    # Clean tokens
    words = set(re.findall(r"\b[a-z0-9_-]+\b", q_clean))

    # 2. Check for sub-intents / buyer intent patterns in intent_examples.json
    for intent_key, phrasings in _intent_examples.items():
        for phrase in phrasings:
            # Word boundary regex match
            if re.search(r"\b" + re.escape(phrase.lower()) + r"\b", q_clean):
                if intent_key in ["PURCHASE", "CONSULTATION", "IMPLEMENTATION", "DEMO_REQUEST", "CONTACT_SALES"]:
                    query_type = intent_key
                    # Try to map domain based on entity mentions
                    break
        if query_type:
            break

    # 3. Match against leadership/founder entities directly
    leadership_words = {
        "founder", "ceo", "coo", "cto", "leader", "leadership", "team", "vinay", "velivela", 
        "akhil", "reddy", "chandra", "balaji", "ganesh", "gandhi", "harish", "nerati", 
        "aravind", "mohan"
    }
    has_leadership_phrase = any(phrase in q_clean for phrase in ["who started", "who founded", "who leads", "who lead", "started the company", "founded the company"])
    
    if has_leadership_phrase or leadership_words.intersection(words):
        domain = "LEADERSHIP"
        if query_type not in ["PURCHASE", "CONSULTATION", "IMPLEMENTATION", "DEMO_REQUEST", "CONTACT_SALES"]:
            query_type = "FACT"
        if any(w in words for w in ["founder", "ceo", "leads", "lead"]) or any(phrase in q_clean for phrase in ["who started", "who founded", "started by", "founded by"]):
            matched_entity = "founder"

    # 4. Match against entity index (Products, Services, Solutions)
    if not domain:
        best_match = None  # (alias_length, domain_key, entity_id)
        for dom_key, entity_map in _entity_index.items():
            for alias in entity_map.keys():
                if re.search(r"\b" + re.escape(alias) + r"\b", q_clean):
                    if best_match is None or len(alias) > best_match[0]:
                        best_match = (len(alias), dom_key, entity_map[alias])
        if best_match:
            domain = best_match[1].upper()
            matched_entity = best_match[2]

    # Check for list helper markers
    is_list_query = any(re.search(r"\b" + re.escape(pat) + r"\b", q_clean) for pat in ["list", "show", "provide", "portfolio", "catalog", "offer", "have"]) or \
                    any(phrase in q_clean for phrase in ["what are", "what do you sell", "what do you offer", "what do you have"])
                    
    if "how many" in q_clean or "how much" in q_clean:
        is_list_query = False

    # Route classification logic
    if query_type in ["PURCHASE", "CONSULTATION", "IMPLEMENTATION", "DEMO_REQUEST", "CONTACT_SALES"]:
        # Sub-intent was matched! Find domain if not set
        if not domain:
            domain = "COMPANY_INFO"
    elif domain:
        if domain == "LEADERSHIP":
            query_type = "FACT"
        elif matched_entity:
            if any(w in q_clean for w in ["compare", " vs ", "versus", "difference between", "alternative to"]):
                query_type = "COMPARE"
            else:
                query_type = "DETAIL"
        else:
            query_type = "LIST" if is_list_query else "DETAIL"
    else:
        # Check by domain-specific keyword sets
        rec_words = {"achievement", "achievements", "award", "awards", "recognition", "recognitions", "milestone", "milestones", "hybiz", "apis"}
        has_rec_phrase = any(phrase in q_clean for phrase in ["ap msme", "msme challenge", "double victory"])
        
        partner_words = {"client", "clients", "customer", "customers", "partner", "partners", "companies", "brands", "retention", "rate"}
        
        case_words = {"roi", "metrics"}
        has_case_phrase = any(phrase in q_clean for phrase in ["case study", "case studies", "success stories"])
        
        career_words = {"career", "careers", "job", "jobs", "hiring", "opening", "openings", "join", "apply"}
        
        contact_words = {"phone", "number", "email", "hours", "contact", "reach", "call", "open", "weekend", "time", "weekends"}
        
        location_words = {"address", "location", "located", "office", "offices", "hq", "headquarters", "tower"}
        has_location_phrase = any(phrase in q_clean for phrase in ["where is", "where are"])
        
        company_words = {"mission", "vision", "tagline", "story", "overview", "history", "profile", "fixity", "info", "information", "founded", "established"}
        has_company_phrase = any(phrase in q_clean for phrase in ["about us", "who are you", "what is cittaai", "who is cittaai"]) or \
                             bool(re.search(r"\babout\s+cittaai\b(?!'s)", q_clean))

        if has_rec_phrase or rec_words.intersection(words):
            domain = "RECOGNITION"
            query_type = "LIST" if is_list_query else "FACT"
        elif partner_words.intersection(words) or "who do you work with" in q_clean or "enterprise partners" in q_clean:
            domain = "PARTNERS"
            query_type = "LIST" if is_list_query else "FACT"
        elif has_case_phrase or case_words.intersection(words):
            domain = "CASE_STUDIES"
            query_type = "LIST" if is_list_query else "FACT"
        elif career_words.intersection(words) or "work at" in q_clean:
            domain = "CAREERS"
            query_type = "FACT"
        elif contact_words.intersection(words):
            domain = "CONTACT"
            query_type = "FACT"
        elif location_words.intersection(words) or has_location_phrase:
            domain = "LOCATION"
            query_type = "FACT"
        elif {"solutions", "solution", "os"}.intersection(words) or any(phrase in q_clean for phrase in ["operating system", "operating systems", "vertical os", "industry os"]):
            domain = "SOLUTIONS"
            query_type = "LIST"
        elif {"product", "products", "platform", "platforms", "offering", "offerings"}.intersection(words):
            domain = "PRODUCTS"
            query_type = "LIST"
        elif {"service", "services", "consulting", "capability", "capabilities"}.intersection(words):
            domain = "SERVICES"
            query_type = "LIST"
        elif has_company_phrase or company_words.intersection(words):
            domain = "COMPANY_INFO"
            query_type = "FACT"

    # Default ambiguous check for singular list categories
    if q_clean in ["products", "services", "solutions", "platforms"]:
        query_type = "LIST"
        if q_clean == "products": domain = "PRODUCTS"
        elif q_clean == "services": domain = "SERVICES"
        elif q_clean in ["solutions", "platforms"]: domain = "SOLUTIONS"

    if query_type and domain:
        logger.info(f"Classifier matched: query_type={query_type}, domain={domain}, entity={matched_entity}")
        return {
            "query_type": query_type,
            "domain": domain,
            "confidence": 1.0,
            "matched_entity": matched_entity
        }

    # --- STAGE 2: Semantic Fallback ---
    if model and _anchor_embeddings:
        try:
            prefix = "Represent this sentence for searching relevant passages: " if "bge" in model.get_sentence_features.__self__.__class__.__name__.lower() else ""
            q_emb = model.encode(prefix + q_clean, normalize_embeddings=True)
            
            best_key = None
            best_score = -1.0
            
            for key, anchor_emb in _anchor_embeddings.items():
                score = float(np.dot(q_emb, anchor_emb))
                if score > best_score:
                    best_score = score
                    best_key = key
            
            logger.info(f"Stage 2 semantic match: {best_key} with score {best_score:.4f}")
            
            if best_score >= 0.75 and best_key:
                return {
                    "query_type": best_key[0],
                    "domain": best_key[1],
                    "confidence": best_score,
                    "matched_entity": None
                }
        except Exception as e:
            logger.error(f"Error in Stage 2 semantic classifier: {e}")

    # Fallback to UNKNOWN_IN_DOMAIN
    logger.info("In-domain query fell through to UNKNOWN_IN_DOMAIN.")
    return {
        "query_type": "UNKNOWN_IN_DOMAIN",
        "domain": "UNKNOWN_IN_DOMAIN",
        "confidence": 1.0,
        "matched_entity": None
    }
