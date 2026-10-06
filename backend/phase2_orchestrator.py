import time
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple

from orchestration_context import OrchestrationContext, ExecutionStrategy, EnterpriseIntent
from conversation_context_resolver import get_conversation_context_resolver
from phase2_intent_classifier import get_phase2_intent_classifier
from out_of_domain_detector import get_out_of_domain_detector
from execution_strategy import get_execution_strategy_selector
from ambiguity_detector import get_ambiguity_detector
from unknown_entity_handler import get_unknown_entity_handler
from knowledge_registry import get_registry
from entity_resolver import resolve_entity_dynamic
from query_understanding_agent import get_query_understanding_agent

logger = logging.getLogger(__name__)

# General Catalog Query Patterns
GENERAL_CATALOG_PATTERNS = [
    "what products do you offer", "what products", "list products", "list all products", "show products", "show all products", "our products", "products offered", "what products do you have", "what products are available", "what are the products",
    "marketing products", "marketing product", "any marketing products", "do they have any marketing products", "do you have any marketing products", "do you have marketing products", "what marketing products",
    "marketing services", "marketing service", "any marketing services", "do they have any marketing services", "do you have any marketing services", "do you have marketing services", "what marketing services",
    "what services do you offer", "what services", "list services", "list all services", "show services", "show all services", "our services", "services offered", "what services do you have", "what services are available",
    "what are the services provided", "services provided", "srevices provided", "what are the srevices provided",
    "what services are provided", "srevices", "serivces", "services",
    "what solutions do you offer", "what solutions", "list solutions", "list all solutions", "show solutions", "show all solutions", "our solutions", "solutions offered", "what solutions do you have", "what solutions are available",
    "what do you offer", "list all offerings", "show all solutions", "what platforms", "list all products and services", "list all solutions"
]

GENERIC_ENTITIES = {"company_info", "faq_general", "contact", "location"}

def check_general_catalog_query(query: str) -> bool:
    q_lower = query.lower().strip()
    
    # Normalize common typos for catalog detection
    norm_q = q_lower
    for typo, fix in [
        ("prodcuts", "products"), ("prodcut", "product"), ("prducts", "products"), ("prduct", "product"),
        ("porducts", "products"), ("porduct", "product"), ("srevices", "services"), ("serivces", "services"),
        ("servises", "services"), ("solutins", "solutions"), ("soltuions", "solutions")
    ]:
        norm_q = norm_q.replace(typo, fix)

    cat_count = sum(1 for kw in ["product", "solution", "service", "team", "leadership", "case", "contact", "achievement", "award"] if kw in norm_q)
    if cat_count >= 2 or "products and services" in norm_q or "everything you offer" in norm_q or "list out all" in norm_q:
        return True

    # Exclude queries referencing specific enterprise offerings or domain topics
    specific_keywords = [
        "real estate", "realestate", "construction", "property", "realty", "builder", "broker", "housing",
        "pharma", "pharmaceutical", "hospital", "medical", "clinic", "healthcare", "health care", "healthtech",
        "education", "college", "institute", "university", "school", "academic", "edtech",
        "ecommerce", "e-commerce", "retail", "online store", "shopping", "merchant",
        "smart cities", "urban", "municipality", "city management",
        "whatsapp", "influencer", "enterprise ai", "martech", "social media",
        "leadership", "team", "founder", "contact", "address", "pricing", "cost"
    ]
    if any(k in q_lower for k in ["case study", "case studies", "awards", "recognitions", "certifications", "apply for a job", "careers"]):
        return True

    if any(k in q_lower for k in specific_keywords):
        return False

    if q_lower in GENERAL_CATALOG_PATTERNS:
        return True

    for p in GENERAL_CATALOG_PATTERNS:
        if len(p.split()) > 1:
            if p in q_lower:
                return True
        else:
            if re.search(r"\b" + re.escape(p) + r"\b", q_lower) and len(q_lower.split()) <= 4:
                return True

    return False

class Phase2Orchestrator:
    def __init__(self):
        self.context_resolver = get_conversation_context_resolver()
        self.intent_classifier = get_phase2_intent_classifier()
        self.ood_detector = get_out_of_domain_detector()
        self.strategy_selector = get_execution_strategy_selector()
        self.ambiguity_detector = get_ambiguity_detector()
        self.unknown_handler = get_unknown_entity_handler()
        self.query_understanding_agent = get_query_understanding_agent()
        self.reg = get_registry()

    def _extract_all_entities(self, query: str) -> List[str]:
        q_lower = query.lower().strip()
        matched = []
        
        # Check canonical entity names
        for ent_id, ent_data in self.reg.entities.items():
            if ent_id in GENERIC_ENTITIES:
                continue
            name = (ent_data.get("name") or ent_data.get("title") or "").lower()
            if name and (name in q_lower or (len(name) > 4 and re.search(r"\b" + re.escape(name) + r"\b", q_lower))):
                matched.append(ent_id)

        # Check aliases for non-generic entities
        for alias, ent_id in self.reg.aliases.items():
            if ent_id in GENERIC_ENTITIES:
                continue
            if len(alias) > 3 and alias in q_lower and ent_id in self.reg.entities:
                if ent_id not in matched:
                    matched.append(ent_id)

        return list(dict.fromkeys(matched))

    def orchestrate(self, session_id: str, original_query: str, normalized_query: str) -> OrchestrationContext:
        start_time = time.time()
        
        # 1. Initialize OrchestrationContext
        ctx = OrchestrationContext(
            session_id=session_id,
            original_query=original_query,
            normalized_query=normalized_query
        )
        ctx.add_trace("Initialization", "SUCCESS", f"Context created for query: '{original_query}'")

        # 2. Entity Resolution & Confidence Check (Target inquiry clauses first, e.g. "what about X")
        all_matched_entities = self._extract_all_entities(normalized_query)
        target_query = normalized_query
        about_match = re.search(r"(?:what|how|then what|tell me)\s+about\s+(.+)", normalized_query, re.IGNORECASE)
        if about_match:
            target_query = about_match.group(1).strip()

        detected_entity_id, conf, matched_alias, _ = resolve_entity_dynamic(
            query=target_query,
            registry_entities=self.reg.entities,
            entity_lookup=self.reg.entity_lookup,
            alias_index=self.reg.aliases,
            unified_vocabulary=self.reg.unified_vocabulary
        )
        if not detected_entity_id:
            detected_entity_id, conf, matched_alias, _ = resolve_entity_dynamic(
                query=normalized_query,
                registry_entities=self.reg.entities,
                entity_lookup=self.reg.entity_lookup,
                alias_index=self.reg.aliases,
                unified_vocabulary=self.reg.unified_vocabulary
            )

        # Phase 5: Query Intelligence Engine Intercept for Semantic Category Mismatch & Intent Understanding
        semantic_decision = None
        try:
            from query_intelligence_engine import get_query_intelligence_engine
            qi_engine = get_query_intelligence_engine()
            active_ctx_entity = self.context_resolver.get_conversation_state(session_id).active_entity
            import asyncio
            # Synchronous dynamic interpretation call
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        qi = pool.submit(asyncio.run, qi_engine.interpret(original_query, normalized_query, session_id=session_id, active_entity=active_ctx_entity)).result()
                else:
                    qi = loop.run_until_complete(qi_engine.interpret(original_query, normalized_query, session_id=session_id, active_entity=active_ctx_entity))
            except Exception:
                # Direct fallback interpretation if event loop context differs
                qi = asyncio.run(qi_engine.interpret(original_query, normalized_query, session_id=session_id, active_entity=active_ctx_entity))

            ctx.metrics["query_interpretation"] = qi.to_dict()
            ctx.metrics["category_mismatch"] = qi.category_mismatch
            ctx.metrics["user_category_term"] = qi.category_term_used_by_user

            semantic_decision = qi
            # The semantic decision is authoritative once accepted (benchmarked in evaluation/semantic_benchmark.py);
            # the legacy alias resolver only stands when the decision asks for clarification.
            if qi.needs_clarification:
                ctx.add_trace("QueryIntelligenceEngine", "CLARIFY", f"Ambiguous interpretation; options={[o['entity_id'] for o in qi.clarification_options]}")
            elif qi.scope.value in ("OUT_OF_DOMAIN", "UNKNOWN_ENTITY", "ALL", "ALL_SOLUTIONS", "ALL_PRODUCTS", "ALL_SERVICES"):
                detected_entity_id, conf = None, qi.scope.confidence
                ctx.add_trace("QueryIntelligenceEngine", qi.scope.value, "Non-entity scope from semantic decision")
            elif qi.primary_entity_id:
                detected_entity_id = qi.primary_entity_id
                conf = qi.confidence
                matched_alias = f"Query Intelligence ({qi.interpretation})"
                ctx.add_trace("QueryIntelligenceEngine", detected_entity_id, f"Resolved entity via Query Intelligence (conf={conf})")
        except Exception as e:
            logger.warning(f"QueryIntelligenceEngine orchestrator integration notice: {e}")
        
        # 2.1 Confidence Threshold Check: If conf < 0.90, invoke QueryUnderstandingAgent for Data-Driven selection
        if semantic_decision is None and conf < 0.90 and not check_general_catalog_query(normalized_query):
            agent_res = self.query_understanding_agent._data_driven_fallback(normalized_query)
            if agent_res.get("primary_entity") and agent_res.get("confidence", 0.0) >= 0.70:
                detected_entity_id = agent_res["primary_entity"]
                conf = agent_res["confidence"]
                matched_alias = "Data-Driven Agent Reasoning"
                ctx.matched_entity_ids = [c["entity"] for c in agent_res.get("candidate_entities", [])]

        ctx.add_trace(
            stage="EntityResolver",
            result=str(detected_entity_id or "None"),
            reason=f"Matched via {matched_alias or 'direct/fuzzy lookup'} (conf={conf})"
        )

        # 3. Conversation & Session Context Resolver
        ctx = self.context_resolver.resolve_context(
            ctx=ctx,
            detected_entity_id=detected_entity_id,
            detected_entities=all_matched_entities
        )
        
        if ctx.resolved_entity_id and ctx.resolved_entity_id in self.reg.entities:
            ent_data = self.reg.entities[ctx.resolved_entity_id]
            ctx.resolved_entity_name = ent_data.get("name") or ent_data.get("title") or ctx.resolved_entity_id
            ctx.resolved_category = ent_data.get("category") or ent_data.get("type")

        # 4. General Catalog Intent Check
        if semantic_decision is not None:
            ctx.is_general_catalog_query = semantic_decision.scope.value in ("ALL", "ALL_SOLUTIONS", "ALL_PRODUCTS", "ALL_SERVICES")
        else:
            ctx.is_general_catalog_query = check_general_catalog_query(normalized_query)
        if ctx.is_general_catalog_query:
            ctx.resolved_entity_id = None
            ctx.resolved_entity_name = None
            ctx.add_trace(
                stage="GeneralCatalogCheck",
                result="TRUE",
                reason="Query asks for broad category/offering listing"
            )

        # 5. Out-of-Domain Check (ONLY if no entity AND not general catalog query)
        if not ctx.resolved_entity_id and not ctx.is_general_catalog_query:
            is_ood, ood_msg = self.ood_detector.is_out_of_domain(normalized_query)
            if not is_ood and semantic_decision is not None and semantic_decision.is_out_of_domain:
                from out_of_domain_detector import DEFAULT_OOD_RESPONSE
                is_ood, ood_msg = True, DEFAULT_OOD_RESPONSE
            if is_ood:
                ctx.is_out_of_domain = True
                ctx.response_text = ood_msg
                ctx.add_trace(
                    stage="OutOfDomainDetector",
                    result="OUT_OF_DOMAIN",
                    reason="Query identified as outside business domain"
                )

        # 6. Intent Classification
        ctx.intent = self.intent_classifier.classify(normalized_query)
        ctx.add_trace("IntentClassifier", ctx.intent, f"Intent classified as '{ctx.intent}'")

        # 7. Ambiguity & Unknown Entity Checks
        if not ctx.is_out_of_domain:
            ctx = self.ambiguity_detector.check_ambiguity(ctx)
            ctx = self.unknown_handler.check_unknown_entity(ctx)

        # 8. Execution Strategy Selector
        ctx = self.strategy_selector.select_strategy(ctx)

        # 9. Update Context State Memory
        self.context_resolver.update_state_after_response(ctx)

        latency_ms = round((time.time() - start_time) * 1000.0, 2)
        ctx.metrics["latency_ms"] = latency_ms
        ctx.metrics["decision_trace"] = ctx.decision_trace
        ctx.metrics["execution_strategy"] = ctx.execution_strategy.value
        ctx.metrics["intent"] = ctx.intent
        ctx.metrics["resolved_entity"] = ctx.resolved_entity_id or "NONE"
        ctx.metrics["resolved_section"] = ctx.section or "NONE"

        return ctx

_orchestrator_instance = None

def get_phase2_orchestrator() -> Phase2Orchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = Phase2Orchestrator()
    return _orchestrator_instance
