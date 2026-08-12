import re
import json
import logging
from typing import Dict, Any, List, Optional
import config
from knowledge_registry import get_registry

logger = logging.getLogger(__name__)

def build_dynamic_registry_summary() -> List[Dict[str, Any]]:
    """
    Extracts live entity metadata from the KnowledgeRegistry.
    This makes entity selection 100% data-driven rather than hardcoded in code.
    """
    try:
        reg = get_registry()
        summary = []
        for ent_id, obj in reg.registry_by_id.items():
            if ent_id in ["company_info", "faq_general", "contact_info"]:
                continue
            title = getattr(obj, "title", None) or getattr(obj, "name", ent_id)
            ent_type = obj.type.value if hasattr(obj.type, "value") else str(obj.type)
            overview = getattr(obj, "overview", None) or getattr(obj, "description", "")
            
            keywords = []
            if hasattr(obj, "search") and isinstance(obj.search, dict):
                keywords = obj.search.get("primary_keywords", []) + obj.search.get("aliases", [])
            elif hasattr(obj, "search") and hasattr(obj.search, "primary_keywords"):
                keywords = getattr(obj.search, "primary_keywords", [])
                
            summary.append({
                "id": ent_id,
                "name": title,
                "type": ent_type,
                "description": overview[:200] + "..." if len(overview) > 200 else overview,
                "keywords": keywords[:6]
            })
        return summary
    except Exception as e:
        logger.warning(f"Failed to build dynamic registry summary: {e}")
        return []

def generate_system_prompt() -> str:
    entities_json = json.dumps(build_dynamic_registry_summary(), indent=2)
    return f"""# ROLE

You are the CittaAI Enterprise Query Understanding Agent.

You are NOT a chatbot. You are NOT responsible for answering the user's question.
Your only responsibility is to understand the user's query and translate it into structured routing instructions.

------------------------------------------------------------

# KNOWLEDGE DOMAIN & LIVE ENTITY REGISTRY

Your knowledge is STRICTLY LIMITED to CittaAI's live enterprise knowledge registry below.
Reason over the descriptions and keywords of these live entities to select the best match for the user's business intent:

{entities_json}

Rules:
• Do NOT invent entities.
• Select entities by matching the user's domain/intent to entity descriptions (e.g. medical/hospitals -> Pharma OS, education/students -> Education OS, property -> Real Estate OS, shops/online retail -> E-Commerce OS).
• If nothing matches with sufficient confidence, set "primary_entity": null.

------------------------------------------------------------

# AVAILABLE ENTITY TYPES

solution, product, service, leadership, case_study, technology, capability, feature, industry

------------------------------------------------------------

# INTENT TYPES

Return one of:
ASK, LIST, OVERVIEW, DETAIL, HOW_IT_WORKS, FEATURES, BENEFITS, COMPARISON, RECOMMENDATION, INDUSTRY_MATCH, USE_CASE, IMPLEMENTATION, PRICING, CONTACT, LEADERSHIP, CASE_STUDY, FOLLOW_UP, GENERAL, UNKNOWN

------------------------------------------------------------

# EXECUTION STRATEGIES

Return exactly one:
FAST_PATH, CATALOG, HYBRID_RAG, REASONING, HYBRID_REASONING

------------------------------------------------------------

# OUTPUT FORMAT

Return ONLY valid JSON matching this schema:
{{
    "primary_entity": "pharma_os",
    "entity_type": "solution",
    "intent": "DETAIL",
    "section": "overview",
    "execution_strategy": "FAST_PATH",
    "confidence": 0.95,
    "candidate_entities": [
        {{
            "entity": "pharma_os",
            "confidence": 0.95
        }},
        {{
            "entity": "enterprise_ai_os",
            "confidence": 0.71
        }}
    ],
    "keywords": [
        "hospital",
        "healthcare",
        "pharma"
    ],
    "reasoning": "Reasoned from live registry description: hospitals map to healthcare (Pharma OS).",
    "needs_vector_search": false,
    "needs_reasoning": false,
    "needs_followup_context": false
}}
"""

class QueryUnderstandingAgent:
    """
    CittaAI Enterprise Query Understanding Agent.
    Data-Driven Intelligence Layer reasoning over live KnowledgeRegistry entities.
    """
    def __init__(self, provider=None):
        self.provider = provider
        if self.provider is None:
            try:
                from llm_provider import get_llm_provider
                import config
                target_provider = getattr(config, "LLM_PROVIDER", "groq")
                config_dict = {"GROQ_API_KEY": getattr(config, "GROQ_API_KEY", ""), "NVIDIA_API_KEY": getattr(config, "NVIDIA_API_KEY", "")}
                self.provider = get_llm_provider(target_provider, config_dict)
            except Exception as e:
                logger.warning(f"Could not initialize LLM provider '{target_provider}': {e}")

    async def analyze(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Data-driven analysis via LLM reasoning over live registry entities with data-driven fallback.
        """
        q_clean = query.strip()
        
        # 1. LLM Data-Driven Analysis
        if self.provider:
            try:
                prompt = generate_system_prompt()
                messages = [
                    {"role": "system", "content": prompt}
                ]
                if history:
                    hist_str = "\n".join([f"{h.get('role', 'user')}: {h.get('content', '')}" for h in history[-4:]])
                    messages.append({"role": "system", "content": f"Recent Conversation History:\n{hist_str}"})
                
                messages.append({"role": "user", "content": f"User Query: {q_clean}"})
                
                res = await self.provider.generate(messages, model=config.MODEL_NAME, temperature=0.1)
                raw_response = res[0] if isinstance(res, tuple) else str(res)
                
                # Extract JSON block
                json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    if isinstance(parsed, dict) and ("primary_entity" in parsed or "resolved_entity" in parsed):
                        # Ensure standard schema field mapping
                        if "resolved_entity" in parsed and "primary_entity" not in parsed:
                            parsed["primary_entity"] = parsed.pop("resolved_entity")
                        if "matched_entities" in parsed and "candidate_entities" not in parsed:
                            parsed["candidate_entities"] = [
                                {"entity": m.get("entity"), "confidence": m.get("score", 0.9)} for m in parsed.pop("matched_entities")
                            ]
                        return parsed
            except Exception as e:
                logger.warning(f"LLM Data-Driven Agent call failed: {e}. Utilizing data-driven fallback matcher.")

        # 2. Data-Driven Fallback Matcher (Queries Live Registry objects directly)
        return self._data_driven_fallback(q_clean, history)

    def _data_driven_fallback(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        q_lower = query.lower().strip()
        reg = get_registry()
        
        # Check follow-up history
        last_entity = None
        if history:
            for item in reversed(history):
                content = item.get("content", "").lower()
                for e_id in reg.registry_by_id.keys():
                    if e_id.replace("_", " ") in content or e_id in content:
                        last_entity = e_id
                        break
                if last_entity:
                    break

        # Data-driven scoring over live registry objects
        scored_candidates = []
        tokens = set(re.findall(r"\b\w+\b", q_lower))
        
        # Category domain keywords dynamically mapped to entity IDs/titles
        domain_terms = {
            "pharma": ["hospital", "hospitals", "patient", "patients", "clinic", "clinics", "doctor", "doctors", "medical", "pharmaceutical", "pharma", "healthcare"],
            "education": ["school", "schools", "student", "students", "college", "colleges", "university", "universities", "education", "academy"],
            "real_estate": ["housing", "property", "realtor", "realtors", "apartment", "apartments", "real estate"],
            "ecommerce": ["shop", "shops", "online store", "retail", "e-commerce", "ecommerce", "store", "cart"],
            "whatsapp": ["whatsapp", "wa", "bulk message", "broadcast messaging", "drip campaign"],
            "influencer": ["influencer", "influencers", "creator", "creators", "ugc", "influencer campaign"]
        }

        for ent_id, obj in reg.entities.items():
            if ent_id in ["company_info", "faq_general", "contact_info"]:
                continue
            
            title = (obj.get("title") or obj.get("name") or ent_id).lower()
            overview = (obj.get("overview") or obj.get("description") or "").lower()
            ent_type = obj.get("type", "solution")
            
            score = 0.0
            
            # Exact Title / ID match
            if ent_id in q_lower or title in q_lower or ent_id.replace("_", " ") in q_lower:
                score += 1.0
            
            # Domain term associations matching entity ID/title with word boundaries
            for domain_key, terms in domain_terms.items():
                if domain_key in ent_id.lower() or domain_key in title.lower():
                    if any(re.search(r"\b" + re.escape(t) + r"\b", q_lower) for t in terms):
                        score += 0.95
                        break

            # Search keywords
            search_meta = obj.get("search", {})
            keywords = []
            if isinstance(search_meta, dict):
                keywords = [k.lower() for k in search_meta.get("primary_keywords", []) if len(k) > 4]
            
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", q_lower) and kw not in ["software", "management", "platform", "system", "os"]:
                    score += 0.30
            
            if score > 0.35:
                scored_candidates.append((ent_id, obj, score, ent_type))

        scored_candidates.sort(key=lambda x: x[2], reverse=True)
        
        primary_entity = None
        entity_type = None
        candidates_list = []
        confidence = 0.0

        if scored_candidates:
            primary_entity, top_obj, raw_score, entity_type = scored_candidates[0]
            confidence = min(round(raw_score, 2), 0.98)
            candidates_list = [
                {"entity": c[0], "confidence": min(round(c[2], 2), 0.98)} for c in scored_candidates[:3]
            ]
        elif last_entity and any(w in q_lower for w in ["it", "how does it work", "workflow", "benefits", "features"]):
            primary_entity = last_entity
            confidence = 0.90
            candidates_list = [{"entity": primary_entity, "confidence": 0.90}]

        # Intent Detection
        intent = "ASK"
        if any(w in q_lower for w in ["what products", "list products", "marketing products"]):
            intent = "LIST"
            primary_entity = None
        elif any(w in q_lower for w in ["what services", "list services", "marketing services"]):
            intent = "LIST"
            primary_entity = None
        elif any(w in q_lower for w in ["how does it work", "how it works", "workflow"]):
            intent = "HOW_IT_WORKS"
        elif any(w in q_lower for w in ["benefits", "advantages"]):
            intent = "BENEFITS"
        elif any(w in q_lower for w in ["features", "modules"]):
            intent = "FEATURES"

        section = "overview"
        if intent == "HOW_IT_WORKS":
            section = "how_it_works"
        elif intent == "BENEFITS":
            section = "benefits"

        strategy = "FAST_PATH" if primary_entity and confidence >= 0.90 else ("CATALOG" if not primary_entity else "HYBRID_RAG")
        keywords_list = [w for w in tokens if len(w) > 3]

        return {
            "primary_entity": primary_entity,
            "entity_type": entity_type,
            "intent": intent,
            "section": section,
            "execution_strategy": strategy,
            "confidence": confidence,
            "candidate_entities": candidates_list,
            "keywords": keywords_list,
            "reasoning": f"Data-driven evaluation over live registry. Best candidate: {primary_entity} (conf={confidence}).",
            "needs_vector_search": strategy in ["HYBRID_RAG", "REASONING"],
            "needs_reasoning": strategy == "REASONING",
            "needs_followup_context": bool(last_entity and not primary_entity)
        }

_agent_instance = None

def get_query_understanding_agent(provider=None) -> QueryUnderstandingAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = QueryUnderstandingAgent(provider=provider)
    return _agent_instance
