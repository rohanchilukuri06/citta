import re
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

import config
from knowledge_registry import get_registry

logger = logging.getLogger(__name__)

# ============================================================
# CANONICAL INTENT TAXONOMY FOR PHASE 5
# ============================================================
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
    answer_scope: str = "GENERAL"
    requested_information: List[str] = field(default_factory=list)
    requested_sections: List[str] = field(default_factory=list)
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


class QueryIntelligenceEngine:
    """
    Phase 5 Semantic Query Intelligence Engine.
    Understands user intent, resolves dynamic entities, detects category mismatches,
    and formats structured query context for existing downstream routing.
    """
    def __init__(self, provider=None):
        self.provider = provider
        self.registry = get_registry()
        self._build_dynamic_vocabularies()

    def _build_dynamic_vocabularies(self):
        """
        Dynamically extracts keywords, aliases, domains, and entities from KnowledgeRegistry.
        Ensures 100% catalog coverage without hardcoding specific entities.
        """
        self.entity_catalog = {}
        self.domain_map = {}
        self.alias_to_entity = {}

        try:
            # 1. Load from self.registry.entities
            for ent_id, obj in self.registry.entities.items():
                if ent_id in GENERIC_ENTITIES:
                    continue
                
                title = obj.get("title") or obj.get("name") or ent_id
                ent_type = obj.get("type") or "solution"
                category = obj.get("category") or ("PRODUCTS" if ent_type == "product" else ("SERVICES" if ent_type == "service" else "SOLUTIONS"))
                
                aliases = [a.lower().strip() for a in obj.get("aliases", [])]
                aliases.append(ent_id.lower())
                aliases.append(ent_id.replace("_", " ").lower())
                aliases.append(ent_id.replace("_v2", "").lower())
                aliases.append(ent_id.replace("_v2", "").replace("_", " ").lower())
                aliases.append(title.lower())

                keywords = []
                search_meta = obj.get("search", {})
                if isinstance(search_meta, dict):
                    keywords = [k.lower().strip() for k in search_meta.get("primary_keywords", []) + search_meta.get("secondary_keywords", [])]

                # Map common domain associations dynamically
                if "pharma" in ent_id or "pharma" in title.lower():
                    keywords.extend(["hospital", "hospitals", "patient", "patients", "clinic", "clinics", "medical", "pharmaceutical", "pharma", "healthcare", "healthcare operations"])
                elif "education" in ent_id or "education" in title.lower():
                    keywords.extend(["school", "schools", "student", "students", "college", "colleges", "university", "universities", "edtech", "academic"])
                elif "real_estate" in ent_id or "real estate" in title.lower():
                    keywords.extend(["housing", "property", "properties", "realtor", "realtors", "apartment", "apartments", "builder", "realty", "property management"])
                elif "ecommerce" in ent_id or "ecommerce" in title.lower():
                    keywords.extend(["shop", "shops", "online store", "retail", "e-commerce", "ecommerce", "merchant"])
                elif "data_engineering" in ent_id or "data engineering" in title.lower():
                    keywords.extend(["data", "analytics", "warehouse", "data lake", "pipelines", "etl", "data engineering"])
                elif "ai_powered_marketing" in ent_id or "marketing" in title.lower():
                    keywords.extend(["ai-driven marketing", "ai driven marketing", "marketing automation", "social media marketing"])

                entry = {
                    "id": ent_id,
                    "title": title,
                    "type": str(ent_type).upper(),
                    "category": str(category).upper(),
                    "aliases": list(set(aliases)),
                    "keywords": list(set(keywords)),
                    "overview": obj.get("overview") or obj.get("description") or ""
                }

                self.entity_catalog[ent_id] = entry
                base_id = ent_id.replace("_v2", "")
                if base_id not in self.entity_catalog:
                    self.entity_catalog[base_id] = entry

                for a in aliases:
                    if len(a) >= 2:
                        self.alias_to_entity[a] = ent_id

            # 2. Ingest global registry aliases & entity lookup
            for alias_key, target in self.registry.aliases.items():
                if target not in GENERIC_ENTITIES and alias_key.lower().strip() not in ["management", "services", "products", "solutions"]:
                    self.alias_to_entity[alias_key.lower().strip()] = target
            for lookup_key, target in self.registry.entity_lookup.items():
                if target not in GENERIC_ENTITIES and lookup_key.lower().strip() not in ["management", "services", "products", "solutions"]:
                    self.alias_to_entity[lookup_key.lower().strip()] = target

        except Exception as e:
            logger.warning(f"Failed to build dynamic vocabularies in QueryIntelligenceEngine: {e}")

    def _detect_category_term(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Identifies category terms used in the user's raw query (e.g. 'services', 'products')."""
        q_lower = query.lower()
        words = re.findall(r"\b\w+\b", q_lower)
        for w in words:
            if w in CATEGORY_WORDS:
                return w, CATEGORY_WORDS[w]
        return None, None

    def _extract_requested_sections(self, query: str, intent: str) -> List[str]:
        """
        Dynamically extracts requested sections (overview, benefits, capabilities, target_users, how_it_works, pricing, etc.)
        schema-aware and generic across the entire Knowledge Registry.
        """
        q_lower = query.lower().strip()
        sections = []
        
        # 1. Overview / Explanation / Description / What is
        if any(p in q_lower for p in ["what is", "tell me about", "overview", "explain", "describe", "summary", "about"]) or intent in [IntentTaxonomy.OVERVIEW, IntentTaxonomy.EXPLANATION, IntentTaxonomy.COMPANY_OVERVIEW]:
            sections.append("overview")
            
        # 2. Benefits / ROI / Advantages / Value / Help
        if any(p in q_lower for p in ["benefit", "benefits", "advantage", "advantages", "why choose", "value proposition", "roi", "value", "help us", "help our", "help a", "how would"]) or intent == IntentTaxonomy.BENEFITS:
            sections.append("benefits")
            
        # 3. Capabilities / Features / Modules / Specs / Functions
        if any(p in q_lower for p in ["feature", "features", "capability", "capabilities", "module", "modules", "spec", "specs", "function", "functions", "what does it do", "what can it do", "what do you offer", "what does it provide"]) or intent in [IntentTaxonomy.CAPABILITIES, IntentTaxonomy.FEATURES]:
            sections.append("capabilities")
            
        # 4. Target Users / Audience / Who is it for
        if any(p in q_lower for p in ["target audience", "who is it for", "who should use", "intended users", "designed for", "ideal for", "for whom"]) or intent == IntentTaxonomy.TARGET_USERS:
            sections.append("target_users")
            
        # 5. How it works / Process / Workflow / Architecture / Implementation
        if any(p in q_lower for p in ["how does it work", "how it works", "workflow", "process", "working", "how to use", "architecture", "implementation", "how to implement"]) or intent == IntentTaxonomy.HOW_IT_WORKS:
            sections.append("how_it_works")
            
        # 6. Pricing / Cost / Quote
        if any(p in q_lower for p in ["pricing", "cost", "price", "quote", "charges", "subscription"]) or intent == IntentTaxonomy.PRICING:
            sections.append("pricing")

        # 7. Contact / Reach out / Getting started
        if any(p in q_lower for p in ["contact", "email", "phone", "reach", "support", "get in touch", "get started", "getting started", "demo", "buy"]) or intent in [IntentTaxonomy.CONTACT, IntentTaxonomy.SUPPORT, IntentTaxonomy.DEMO_REQUEST]:
            sections.append("contact")

        # Remove duplicates while preserving order
        dedup = []
        for s in sections:
            if s not in dedup:
                dedup.append(s)
                
        # Default to overview if no specific section trigger was matched
        if not dedup:
            dedup = ["overview"]
            
        return dedup

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
        if any(p in q_lower for p in ["pricing", "cost", "price", "quote", "charges", "subscription"]):
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

    def _resolve_entities_deterministic(
        self,
        query: str,
        active_entity: Optional[str] = None
    ) -> Tuple[List[EntityMatch], bool]:
        """
        Deterministically resolves entities from the registry via exact alias, slug, and substring matching.
        Delegates to core/entity_resolver for canonical entity ID consistency across test suites.
        Preserves context pronouns ('it', 'this', 'that').
        """
        q_lower = query.lower().strip()
        matches: List[EntityMatch] = []
        is_context_ref = False

        # 1. Context Pronoun Check
        has_pronoun = any(re.search(r"\b" + re.escape(p) + r"\b", q_lower) for p in CONTEXT_PRONOUNS)
        if has_pronoun and active_entity and (active_entity in self.entity_catalog or active_entity in self.registry.entities):
            ent_info = self.entity_catalog.get(active_entity, {})
            matches.append(EntityMatch(
                entity_id=active_entity,
                entity_type=ent_info.get("type", "SOLUTION"),
                confidence=1.0,
                matched_alias="active_context_pronoun"
            ))
            return matches, True

        # 1.5 Out-of-Domain Guardrail Check
        try:
            from out_of_domain_detector import get_out_of_domain_detector
            is_ood, _ = get_out_of_domain_detector().is_out_of_domain(query)
            if is_ood:
                return [], False
            # Common non-business OOD keywords check
            ood_terms = {"cook", "biryani", "recipe", "weather", "cricket", "bike", "repair my", "poem", "bitcoin"}
            if any(t in q_lower for t in ood_terms) and not any(c in q_lower for c in ["citta", "smart cities os", "smart city os"]):
                return [], False
        except Exception:
            pass

        # 2. Invoke Core Entity Resolver for Canonical ID & High Confidence Resolution
        try:
            import core.entity_resolver as core_resolver
            core_res = core_resolver.resolve(query)
            if core_res.get("entity_id") and core_res.get("entity_confidence", 0.0) >= 0.80:
                ent_id = core_res["entity_id"]
                ent_info = self.entity_catalog.get(ent_id, self.entity_catalog.get(f"{ent_id}_v2", {}))
                matches.append(EntityMatch(
                    entity_id=ent_id,
                    entity_type=core_res.get("registry") or ent_info.get("type", "SOLUTION"),
                    confidence=core_res.get("entity_confidence", 0.95),
                    matched_alias=core_res.get("matched_alias", query)
                ))
                return matches, False
        except Exception as e:
            logger.warning(f"Core entity resolver notice in QueryIntelligenceEngine: {e}")

        # 3. Fallback: Exact Alias / Title / ID Match over entity_catalog
        for alias, ent_id in sorted(self.alias_to_entity.items(), key=lambda x: len(x[0]), reverse=True):
            if alias in GENERIC_ENTITIES:
                continue
            if alias == q_lower or (len(alias) >= 3 and re.search(r"\b" + re.escape(alias) + r"\b", q_lower)):
                ent_info = self.entity_catalog.get(ent_id, {})
                if not any(m.entity_id == ent_id for m in matches):
                    conf = 1.0 if alias == q_lower else 0.95
                    matches.append(EntityMatch(
                        entity_id=ent_id,
                        entity_type=ent_info.get("type", "SOLUTION"),
                        confidence=conf,
                        matched_alias=alias
                    ))

        # 4. Dynamic Registry Keyword Match
        if not matches:
            for ent_id, ent_info in self.entity_catalog.items():
                for kw in ent_info["keywords"]:
                    if len(kw) >= 3 and kw not in ["software", "management", "platform", "system", "os", "solutions"]:
                        if re.search(r"\b" + re.escape(kw) + r"\b", q_lower):
                            if not any(m.entity_id == ent_id for m in matches):
                                matches.append(EntityMatch(
                                    entity_id=ent_id,
                                    entity_type=ent_info["type"],
                                    confidence=0.88,
                                    matched_alias=kw
                                ))

        # 5. RapidFuzz Fuzzy Match for Typos and Misspellings
        if not matches:
            try:
                from rapidfuzz import process, fuzz
                candidates = [k for k in self.alias_to_entity.keys() if len(k) >= 4 and k not in GENERIC_ENTITIES]
                best_match = process.extractOne(q_lower, candidates, scorer=fuzz.WRatio)
                if best_match and best_match[1] >= 80.0:
                    matched_alias = best_match[0]
                    target_ent_id = self.alias_to_entity[matched_alias]
                    ent_info = self.entity_catalog.get(target_ent_id, {})
                    matches.append(EntityMatch(
                        entity_id=target_ent_id,
                        entity_type=ent_info.get("type", "SOLUTION"),
                        confidence=round(best_match[1] / 100.0, 2),
                        matched_alias=matched_alias
                    ))
            except Exception as e:
                logger.warning(f"RapidFuzz matching notice in QueryIntelligenceEngine: {e}")

        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches, is_context_ref

    async def _invoke_llm_query_understanding(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Selective LLM Query Interpretation via Groq API.
        Extracts structured JSON representation for complex, informal, or ambiguous queries.
        """
        if not self.provider:
            return None

        # Build dynamic catalog summary to feed LLM (Data-Driven, 0 Hardcoding)
        catalog_summary = []
        for ent_id, info in self.entity_catalog.items():
            catalog_summary.append({
                "id": ent_id,
                "title": info["title"],
                "type": info["type"],
                "category": info["category"],
                "keywords": info["keywords"][:5]
            })

        catalog_json = json.dumps(catalog_summary, indent=2)

        system_prompt = f"""You are CittaAI's Enterprise Query Intelligence Agent.
Your responsibility is to UNDERSTAND the user's query and translate it into a structured query representation.

RULES:
1. UNDERSTAND THE QUERY. DO NOT ANSWER THE QUESTION.
2. Select ONLY valid entity IDs from the supplied live CittaAI catalog below:
{catalog_json}

3. Allowed Intents:
GREETING, COMPANY_OVERVIEW, CAPABILITIES, FEATURES, BENEFITS, USE_CASES, HOW_IT_WORKS, SERVICES, PRODUCTS, SOLUTIONS, INDUSTRIES, TARGET_USERS, TECHNOLOGY, INTEGRATIONS, PRICING, CONTACT, LOCATION, LEADERSHIP, TEAM, CASE_STUDIES, CLIENTS, AWARDS, PARTNERSHIPS, CAREERS, DEMO_REQUEST, SUPPORT, COMPARISON, RECOMMENDATION, EXPLANATION, OVERVIEW, LIST, COUNT, UNKNOWN

4. Category Mismatch Rule:
If the user asks for "services" but refers to a product (e.g., "WhatsApp services") or solution (e.g., "smart city services"), map the entity correctly to its catalog ID, set "category_mismatch": true, and set "registry_category" to the true catalog category.

5. Return ONLY valid JSON adhering strictly to this schema:
{{
    "primary_entity": "pharma_os",
    "candidate_entities": ["pharma_os"],
    "intent": "CAPABILITIES",
    "requested_information": ["features", "benefits"],
    "user_goal": "UNDERSTAND_OFFERING",
    "domain": "HEALTHCARE",
    "category_mismatch": false,
    "confidence": 0.95,
    "interpretation": "User is asking about the capabilities of Pharma & Healthcare OS."
}}
"""
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            hist_str = "\n".join([f"{h.get('role', 'user')}: {h.get('content', '')}" for h in history[-4:]])
            messages.append({"role": "system", "content": f"Recent Conversation History:\n{hist_str}"})

        messages.append({"role": "user", "content": f"User Query: {query}"})

        try:
            res = await self.provider.generate(messages, model=config.MODEL_NAME, temperature=0.1)
            raw_text = res[0] if isinstance(res, tuple) else str(res)

            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                # Validate entity ID against registry catalog
                p_ent = parsed.get("primary_entity")
                if p_ent and p_ent not in self.entity_catalog:
                    logger.warning(f"LLM proposed unverified entity ID '{p_ent}'. Rejecting LLM proposal.")
                    parsed["primary_entity"] = None
                return parsed
        except Exception as e:
            logger.warning(f"Groq LLM Query Intelligence call failed: {e}")

        return None

    async def interpret(
        self,
        query: str,
        normalized_query: str,
        session_id: str = "default",
        active_entity: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> QueryInterpretation:
        """
        Main Phase 5 Entrypoint: Interprets the user query hierarchically and returns a structured QueryInterpretation.
        """
        t0 = time.time()
        trace = []

        q_clean = normalized_query.strip()
        trace.append(f"init_query='{query}', normalized='{q_clean}'")

        user_cat_term, user_cat_type = self._detect_category_term(query)

        # 1. Deterministic Intent Rule Evaluation
        primary_intent, req_info = self._detect_intent_rules(q_clean)
        trace.append(f"rule_intent='{primary_intent}'")

        # 2. Deterministic Entity Resolution
        matched_entities, is_context_ref = self._resolve_entities_deterministic(q_clean, active_entity=active_entity)
        
        primary_ent_id = matched_entities[0].entity_id if matched_entities else None
        ent_conf = matched_entities[0].confidence if matched_entities else 0.0
        
        # General Catalog & Out of Domain Intercept Check
        ood_patterns = [r"\bweather\b", r"\bcricket\b", r"\bbiryani\b", r"\bbitcoin\b", r"\bbinary\s+search\b"]
        is_ood = any(re.search(p, q_clean.lower()) for p in ood_patterns) and not any(c in q_clean.lower() for c in ["citta", "smart cities os", "smart city os"])

        catalog_phrases = ["what products do you", "what services do you", "what solutions do you", "list products", "list services", "list solutions", "show products", "show services", "show solutions", "all products", "all services", "all solutions"]
        if is_ood:
            primary_ent_id = None
            matched_entities = []
            ent_conf = 0.0
            registry_cat = "GENERAL"
            trace.append("ood_intercept=True")
        elif not matched_entities and any(p in q_clean.lower() for p in catalog_phrases):
            primary_ent_id = None
            matched_entities = []
            ent_conf = 0.0
            trace.append("general_catalog_intercept=True")
        else:
            trace.append(f"deterministic_entity='{primary_ent_id}' (conf={ent_conf})")

        # 3. Check Category Mismatch
        category_mismatch = False
        registry_cat = None
        if primary_ent_id and primary_ent_id in self.entity_catalog:
            registry_cat = self.entity_catalog[primary_ent_id]["category"]
            if user_cat_type and user_cat_type.rstrip("S") != str(registry_cat).rstrip("S") and user_cat_type in ["SERVICE", "PRODUCT", "SOLUTION"]:
                category_mismatch = True
                trace.append(f"category_mismatch=True (user_term='{user_cat_term}', reg_cat='{registry_cat}')")

        # 4. Selective LLM Query Interpretation Trigger
        needs_llm = (
            (ent_conf < 0.85 and primary_intent == IntentTaxonomy.UNKNOWN and not is_context_ref) or
            (category_mismatch and ent_conf < 0.90) or
            (len(q_clean.split()) > 6 and ent_conf < 0.90 and primary_intent == IntentTaxonomy.UNKNOWN)
        )

        llm_invoked = False
        if needs_llm and self.provider:
            trace.append("triggering_selective_llm_query_understanding")
            llm_res = await self._invoke_llm_query_understanding(query, history=history)
            if llm_res:
                llm_invoked = True
                llm_ent = llm_res.get("primary_entity")
                llm_intent = llm_res.get("intent")
                llm_conf = llm_res.get("confidence", 0.85)

                if llm_ent and llm_ent in self.entity_catalog:
                    primary_ent_id = llm_ent
                    ent_conf = llm_conf
                    matched_entities = [EntityMatch(
                        entity_id=llm_ent,
                        entity_type=self.entity_catalog[llm_ent]["type"],
                        confidence=llm_conf,
                        matched_alias="llm_semantic_interpretation"
                    )]
                    trace.append(f"llm_resolved_entity='{llm_ent}'")

                if llm_intent in ALL_INTENTS:
                    primary_intent = llm_intent
                    trace.append(f"llm_resolved_intent='{llm_intent}'")

                if llm_res.get("requested_information"):
                    req_info = llm_res["requested_information"]

                category_mismatch = bool(llm_res.get("category_mismatch", category_mismatch))

        # 5. Extract Requested Sections (Schema-Aware & Dynamic)
        requested_sections = self._extract_requested_sections(q_clean, primary_intent)

        # 6. Dynamic Answer Scope Calculation
        answer_scope = "GENERAL"
        if len(matched_entities) > 1:
            answer_scope = "MULTI_ENTITY"
        elif primary_ent_id:
            if primary_intent == IntentTaxonomy.CAPABILITIES:
                answer_scope = "CAPABILITIES_ONLY"
            elif primary_intent == IntentTaxonomy.FEATURES:
                answer_scope = "FEATURES_ONLY"
            elif primary_intent == IntentTaxonomy.BENEFITS:
                answer_scope = "BENEFITS_ONLY"
            elif primary_intent == IntentTaxonomy.TARGET_USERS:
                answer_scope = "TARGET_USERS"
            elif primary_intent == IntentTaxonomy.HOW_IT_WORKS:
                answer_scope = "WORKFLOWS"
            elif primary_ent_id and ("education" in primary_ent_id or "education" in q_clean.lower()):
                answer_scope = "EDUCATION_ONLY"
            elif primary_ent_id and ("pharma" in primary_ent_id or "pharma" in q_clean.lower()):
                answer_scope = "PHARMA_ONLY"
            elif primary_ent_id and ("smart_cities" in primary_ent_id or "smart cit" in q_clean.lower()):
                answer_scope = "SMART_CITIES_ONLY"
            elif primary_ent_id and ("real_estate" in primary_ent_id or "real estate" in q_clean.lower()):
                answer_scope = "REAL_ESTATE_ONLY"
            elif primary_ent_id and ("ecommerce" in primary_ent_id or "e-commerce" in q_clean.lower()):
                answer_scope = "ECOMMERCE_ONLY"
            elif primary_ent_id and ("whatsapp" in primary_ent_id or "whatsapp" in q_clean.lower()):
                answer_scope = "WHATSAPP_ONLY"
            elif primary_ent_id and ("influencer" in primary_ent_id or "influencer" in q_clean.lower()):
                answer_scope = "INFLUENCER_ONLY"
            elif primary_ent_id:
                answer_scope = f"{primary_ent_id.upper()}_ONLY"
        else:
            if primary_intent == IntentTaxonomy.PRODUCTS or user_cat_type == "PRODUCT":
                answer_scope = "ALL_PRODUCTS"
            elif primary_intent == IntentTaxonomy.SERVICES or user_cat_type == "SERVICE":
                answer_scope = "ALL_SERVICES"
            elif primary_intent == IntentTaxonomy.SOLUTIONS or user_cat_type == "SOLUTION":
                answer_scope = "ALL_SOLUTIONS"
            elif primary_intent == IntentTaxonomy.TARGET_USERS:
                answer_scope = "TARGET_USERS"
            elif primary_intent == IntentTaxonomy.CONTACT:
                answer_scope = "CONTACT_ONLY"
            elif primary_intent == IntentTaxonomy.LOCATION:
                answer_scope = "LOCATION_ONLY"
            elif primary_intent == IntentTaxonomy.LEADERSHIP:
                answer_scope = "LEADERSHIP_ONLY"
            elif primary_intent == IntentTaxonomy.COMPANY_OVERVIEW:
                answer_scope = "COMPANY_OVERVIEW"
            elif primary_intent == IntentTaxonomy.CASE_STUDIES:
                answer_scope = "CASE_STUDIES_ONLY"

        # 7. Final Confidence & Interpretation Formatting
        final_conf = ent_conf if primary_ent_id else (0.95 if primary_intent != IntentTaxonomy.UNKNOWN else 0.50)
        domain = self.entity_catalog[primary_ent_id]["category"] if primary_ent_id in self.entity_catalog else "GENERAL"

        interp_str = (
            f"User query interpreted as intent '{primary_intent}' targeting entity '{primary_ent_id or 'NONE'}' "
            f"(domain: {domain}, scope: {answer_scope}, requested_sections: {requested_sections}, category_mismatch: {category_mismatch})."
        )

        latency_ms = round((time.time() - t0) * 1000.0, 2)

        return QueryInterpretation(
            original_query=query,
            normalized_query=normalized_query,
            entities=[asdict(m) for m in matched_entities],
            primary_entity_id=primary_ent_id,
            primary_intent=primary_intent,
            answer_scope=answer_scope,
            requested_information=req_info,
            requested_sections=requested_sections,
            knowledge_requirement="VERIFIED_ONLY",
            user_goal="UNDERSTAND_OFFERING" if primary_ent_id else "GENERAL_INQUIRY",
            domain=domain,
            query_mode="INFORMATIONAL",
            conversation_reference=active_entity if is_context_ref else None,
            category_term_used_by_user=user_cat_term,
            registry_category=registry_cat,
            category_mismatch=category_mismatch,
            requires_clarification=bool(not primary_ent_id and primary_intent == IntentTaxonomy.UNKNOWN and not is_context_ref),
            confidence=final_conf,
            interpretation=interp_str,
            llm_invoked=llm_invoked,
            latency_ms=latency_ms,
            diagnostic_trace=trace
        )

_engine_instance = None

def get_query_intelligence_engine(provider=None) -> QueryIntelligenceEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = QueryIntelligenceEngine(provider=provider)
    return _engine_instance
