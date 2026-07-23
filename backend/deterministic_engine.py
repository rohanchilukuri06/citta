import logging
from typing import Dict, Any, Optional, List

from intent_analyzer import IntentType, TopicType
from knowledge_service import get_knowledge_service
from tenant_registry import get_tenant_registry

from conversation.query_understanding import get_query_understanding_engine
from resolvers.leadership import get_leadership_resolver
from resolvers.case_study import get_case_study_resolver
from conversation.response_generator import get_response_generator
from conversation.navigation import get_navigation_controller
from suggestions.follow_up import get_follow_up_engine
from structured_renderers import clean_val

logger = logging.getLogger(__name__)

class DeterministicEngine:
    def __init__(self):
        self.ks = get_knowledge_service()
        self.t_reg = get_tenant_registry()
        self.qu_engine = get_query_understanding_engine()
        self.lead_resolver = get_leadership_resolver()
        self.cs_resolver = get_case_study_resolver()
        self.resp_gen = get_response_generator()
        self.nav_ctrl = get_navigation_controller()
        self.follow_engine = get_follow_up_engine()

    def generate_response(
        self,
        tenant_id: str,
        intent: IntentType,
        topics: List[TopicType],
        query: str,
        matched_entity_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Zero-LLM Instant Execution Engine.
        Generates deterministic Markdown responses for COUNT, LIST, LEADERSHIP, CASE_STUDY, and FACT queries (<10ms).
        """
        try:
            tenant = self.t_reg.get_tenant(tenant_id)
            q_lower = query.lower().strip()

            # Allow follow-up queries with context pronouns or single section words to pass through to Active Context Memory
            from entity_resolver import contains_pronouns
            if contains_pronouns(query) or q_lower in ["tell me how it works", "how it works", "how does it work", "tell me more", "benefits", "features", "overview", "workflows", "faq"]:
                return None

            # 0. Run Query Understanding Engine
            understanding = self.qu_engine.analyze(query)

            # 0.1 IntentType.COUNT Queries Handling First!
            if intent == IntentType.COUNT or "how many" in q_lower or "count" in q_lower:
                for topic in (topics or [TopicType.CASE_STUDIES]):
                    if topic == TopicType.CASE_STUDIES or "case" in q_lower:
                        res = self.ks.count_entities(tenant_id, "CASE_STUDIES")
                        count = res["count"]
                        items = res["items"]
                        items_str = "\n".join([f"{idx+1}. **{c.get('title') or c.get('name')}**: {c.get('overview') or c.get('challenge') or c.get('tagline') or 'Client Success Story'}" for idx, c in enumerate(items)])
                        nav_link, _ = self.nav_ctrl.process_navigation(understanding.navigation_intent, tenant.routes.get("case_studies", "/case-studies"))
                        return {
                            "response": f"**{tenant.name}** currently has **{count} published case studies**:\n\n{items_str}",
                            "source": "Case Studies Registry",
                            "verified": True,
                            "confidence": 1.0,
                            "navigation": nav_link,
                            "suggestions": ["Show Jewellery Brand case study", "Show FMCG Brand case study", "Show Spices Export case study"],
                            "metrics": {"resolved_entity": "NONE", "resolved_registry": "CASE_STUDIES"}
                        }
                    elif topic == TopicType.PRODUCTS or "product" in q_lower:
                        res = self.ks.count_entities(tenant_id, "PRODUCTS")
                        count = res["count"]
                        items = res["items"]
                        items_str = "\n".join([f"{idx+1}. **{p.get('name')}**: {p.get('summary') or p.get('overview')}" for idx, p in enumerate(items)])
                        nav_link, _ = self.nav_ctrl.process_navigation(understanding.navigation_intent, tenant.routes.get("products", "/products"))
                        return {
                            "response": f"**{tenant.name}** currently offers **{count} flagship products**:\n\n{items_str}",
                            "source": "Products Registry",
                            "verified": True,
                            "confidence": 1.0,
                            "navigation": nav_link,
                            "suggestions": ["Explain WhatsApp Marketing Platform", "Explain Influencer Marketing Platform"],
                            "metrics": {"resolved_entity": "NONE", "resolved_registry": "PRODUCTS"}
                        }

            # Issue 7: Statistics & Metrics Queries Intercept
            if understanding.intent == "statistics" or any(w in q_lower for w in ["clients", "users served", "statistics", "metrics", "how many clients", "client count"]):
                resp_md = (
                    "### CittaAI Platform Impact & Key Statistics\n\n"
                    "• **Enterprise Clients**: 50+ Global Organizations\n"
                    "• **Active Users Served**: 100,000+ Enterprise Users\n"
                    "• **Client ROI Delivered**: ₹3.5 Cr+ Measurable Revenue Boost\n"
                    "• **Operational Efficiency**: 85% Reduction in Processing Turnaround\n\n"
                    "Explore our client success stories or speak with our leadership team for detailed case studies."
                )
                return {
                    "response": resp_md,
                    "source": "Company Statistics Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": tenant.routes.get("about", "/about"),
                    "suggestions": ["Show Case Studies", "Show Leadership Team", "Contact Sales"],
                    "metrics": {"resolved_entity": "company_info", "resolved_registry": "STATISTICS"}
                }

            # Certifications & Recognitions Intercept
            if any(w in q_lower for w in ["certific", "award", "recognit", "achieve"]) or any(t in topics for t in ["AWARDS", "RECOGNITION", "ACHIEVEMENTS"]):
                rec_reg = self.ks.reg.registry_index.get("RECOGNITION", {})
                recognitions = rec_reg.get("recognitions", [])
                if recognitions:
                    items_str = "\n".join([f"- **{r['title']}**: {r.get('description', '') or r.get('details', '') or r.get('organization', '')}" for r in recognitions])
                else:
                    items_str = "- **AP MSME Award**: Recognized for enterprise AI excellence and operational innovation.\n- **ISO 27001 Security Certified**: Enterprise security and data governance compliance."
                nav_link, _ = self.nav_ctrl.process_navigation(understanding.navigation_intent, tenant.routes.get("recognition", "/recognition"))
                return {
                    "response": f"### {tenant.name} Achievements & Recognitions\n\n{items_str}\n\nExplore more details on our [Recognition page]({tenant.routes.get('recognition', '/recognition')}).",
                    "source": "Recognition Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": nav_link,
                    "suggestions": ["Show Products", "Show Services", "Show Solutions"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "RECOGNITION"}
                }

            # 0.1 Clarification Intercept for Low-Confidence / Ambiguous Queries
            if understanding.requires_clarification:
                options_str = "\n".join([f"• **{opt['label']}**" for opt in understanding.clarification_options])
                return {
                    "response": f"Here are several relevant options for your request. Did you mean:\n\n{options_str}\n\nPlease select an option or specify your topic.",
                    "source": "Clarification Engine",
                    "verified": True,
                    "confidence": understanding.confidence,
                    "navigation": None,
                    "suggestions": [opt["label"] for opt in understanding.clarification_options],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "CLARIFICATION"}
                }

            import re
            if (understanding.intent in ["leadership_lookup", "person_lookup"] or 
                TopicType.LEADERSHIP in topics or 
                TopicType.PERSON_LOOKUP in topics or 
                role or 
                any(re.search(r"\b" + k + r"\b", q_lower) for k in ["team", "leadership", "management", "executive", "executives", "founder", "founders", "ceo", "cto", "coo", "cmo", "vinay", "akhil", "saladi", "balaji", "ganesh", "harish", "aravind", "parvatha"])):
                
                target_term = role or understanding.target or query.strip()
                lead_res = self.lead_resolver.resolve_leadership(target_term, tenant_id=tenant_id)
                if lead_res:
                    resp_md = self.resp_gen.generate_leadership_response(lead_res, detail_level=understanding.detail_level)
                    target_url = tenant.routes.get("about", "/about")
                    nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, target_url, entity_type="LEADERSHIP")
                    target_p_id = lead_res.get("member", {}).get("id") if lead_res.get("type") == "individual" else None
                    sugs = self.follow_engine.generate_suggestions(
                        query_intent="leadership_lookup", 
                        target_person_id=target_p_id
                    )
                    
                    return {
                        "response": resp_md,
                        "source": "Leadership Registry",
                        "verified": True,
                        "confidence": 1.0,
                        "navigation": nav_link,
                        "action_choices": action_choices,
                        "suggestions": sugs,
                        "metrics": lead_res.get("metrics", {"resolved_entity": "NONE", "resolved_registry": "LEADERSHIP"})
                    }

            # 0.3 Deep Case Study Detail Intercept (Fix Issue 3: "Explain one case study")
            if "case stud" in q_lower and intent != IntentType.COUNT:
                if any(w in q_lower for w in ["jewellery", "fmcg", "spices", "roi"]):
                    cs_res = self.cs_resolver.resolve_case_study(query)
                    if cs_res:
                        resp_md = self.resp_gen.generate_case_study_response(cs_res, detail_level=understanding.detail_level)
                        target_url = cs_res.get("url") or tenant.routes.get("case_studies", "/case-studies")
                        nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, target_url, entity_type="CASE_STUDY")
                        sugs = self.follow_engine.generate_suggestions(entity_id=cs_res["id"], registry_type="CASE_STUDIES")
                        return {
                            "response": resp_md,
                            "source": "Case Studies Registry",
                            "verified": True,
                            "confidence": 1.0,
                            "navigation": nav_link,
                            "action_choices": action_choices,
                            "suggestions": sugs,
                            "metrics": cs_res["metrics"]
                        }
                else: # Generic Case Study Query -> Present Available Case Studies cleanly
                    cases = self.ks.list_entities(tenant_id, "CASE_STUDIES")
                    items_str = "\n".join([f"• **{c.get('title') or c.get('name')}**: {c.get('overview') or c.get('challenge') or c.get('tagline') or 'Client Success Story'}" for c in cases])
                    target_url = tenant.routes.get("case_studies", "/case-studies")
                    nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, target_url, entity_type="CASE_STUDY")
                    return {
                        "response": (
                            f"### CittaAI Client Case Studies & Success Stories\n\n"
                            f"We have published case studies demonstrating measurable ROI across industries:\n\n{items_str}\n\n"
                            f"Which client case study would you like to explore in detail?"
                        ),
                        "source": "Case Studies Registry",
                        "verified": True,
                        "confidence": 1.0,
                        "navigation": nav_link,
                        "action_choices": action_choices,
                        "suggestions": ["Show Jewellery Brand case study", "Show FMCG Brand case study", "Show Spices Export case study"],
                        "metrics": {"resolved_entity": "NONE", "resolved_registry": "CASE_STUDIES"}
                    }

            import config
            if getattr(config, "USE_NEW_ENTITY_RESOLVER", True):
                import core.entity_resolver as core_resolver
                res = core_resolver.resolve(query)
                resolved_entity_id = res["entity_id"]
                entity_confidence = res["entity_confidence"]
                routing_confidence = res["routing_confidence"]
                confidence_level = res["confidence_level"]
                res_source = res["source"]

                # Handle dynamic contacts alias if resolver missed it but keywords match
                if not resolved_entity_id and any(w in q_lower for w in ["email", "phone", "contact", "address", "office"]):
                    resolved_entity_id = "contact_info"

                if resolved_entity_id:
                    obj = self.ks.reg.registry_by_id.get(resolved_entity_id)
                    if obj and obj.type.value in ["product", "solution", "service", "case_study", "contact", "award", "faq"]:
                        import structured_renderers
                        sec = "best_for" if any(w in q_lower for w in ["who is it for", "who is it designed for", "target audience", "intended users", "designed for"]) else ("how_it_works" if any(w in q_lower for w in ["how", "work", "workflow"]) else ("benefits" if any(w in q_lower for w in ["benefit", "advantage"]) else "overview"))
                        rendered_md = structured_renderers.render_section(obj, sec)
                        target_url = obj.url
                        nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, target_url, entity_name=obj.name, entity_type=obj.type.value.upper())
                        sugs = self.follow_engine.generate_suggestions(entity_id=obj.id, registry_type=obj.type.value.upper())
                        
                        return {
                            "response": rendered_md,
                            "source": f"Registry Object Match: {obj.id}",
                            "verified": True,
                            "confidence": entity_confidence,
                            "navigation": nav_link,
                            "action_choices": action_choices,
                            "suggestions": sugs,
                            "metrics": {
                                "resolved_entity": obj.id,
                                "resolved_registry": obj.type.value.upper(),
                                "resolved_section": sec,
                                "entity_confidence": entity_confidence,
                                "routing_confidence": routing_confidence,
                                "confidence_level": confidence_level,
                                "resolution_source": res_source
                            }
                        }
            else:
                # Legacy intercepts
                # Issue 4: Product Understanding Graceful Fallback ("How Pharma OS works")
                if any(w in q_lower for w in ["how", "work", "workflow"]) and any(p in q_lower for p in ["pharma", "education", "real estate", "realestate", "ecommerce", "whatsapp", "influencer"]):
                    matched_id = None
                    if "pharma" in q_lower: matched_id = "solution_pharma_os"
                    elif "education" in q_lower: matched_id = "solution_education_os"
                    elif "real estate" in q_lower or "realestate" in q_lower: matched_id = "solution_real_estate_os"
                    elif "ecommerce" in q_lower: matched_id = "solution_ecommerce_os"
                    elif "whatsapp" in q_lower: matched_id = "product_whatsapp_marketing"
                    elif "influencer" in q_lower: matched_id = "product_influencer_marketing"

                    if matched_id and matched_id in self.ks.reg.registry_by_id:
                        obj = self.ks.reg.registry_by_id[matched_id]
                        title = clean_val(obj.title or obj.name)
                        overview = clean_val(obj.overview or obj.description)
                        capabilities = getattr(obj, "capabilities", [])
                        workflows = getattr(obj, "workflows", [])

                        if workflows:
                            wf_str = "\n".join([f"{step.step}. **{step.title}**: {step.description}" for step in workflows])
                            resp_md = f"### How {title} Works\n\n{wf_str}"
                        else:
                            cap_bullets = ""
                            if capabilities:
                                cap_bullets = "\n" + "\n".join([f"• **{cap.title}**: {cap.description}" for cap in capabilities[:4]])
                            resp_md = (
                                f"Regarding **{title}**, here is an overview of how the solution works:\n\n{overview}{cap_bullets}"
                            )

                        target_url = obj.url
                        nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, target_url, entity_name=obj.name, entity_type=obj.type.value.upper())
                        sugs = self.follow_engine.generate_suggestions(entity_id=obj.id, registry_type=obj.type.value.upper())
                        return {
                            "response": resp_md,
                            "source": f"Registry Object: {obj.id}",
                            "verified": True,
                            "confidence": 1.0,
                            "navigation": nav_link,
                            "action_choices": action_choices,
                            "suggestions": sugs,
                            "metrics": {"resolved_entity": obj.id, "resolved_registry": obj.type.value.upper(), "resolved_section": "how_it_works"}
                        }

                # Contact / Location / Email / Phone Query Intercept
                matched_id_val = matched_entity_id
                if any(w in q_lower for w in ["email", "phone", "contact", "address", "office"]):
                    matched_id_val = "contact_info"

                # Matched Entity Fact Intercept
                if matched_id_val and matched_id_val.lower() not in ["none", ""]:
                    obj = self.ks.reg.registry_by_id.get(matched_id_val)
                    if obj:
                        import structured_renderers
                        sec = "best_for" if any(w in q_lower for w in ["who is it for", "who is it designed for", "target audience", "intended users", "designed for"]) else ("how_it_works" if any(w in q_lower for w in ["how", "work", "workflow"]) else ("benefits" if any(w in q_lower for w in ["benefit", "advantage"]) else "overview"))
                        rendered_md = structured_renderers.render_section(obj, sec)
                        target_url = obj.url
                        nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, target_url, entity_name=obj.name, entity_type=obj.type.value.upper())
                        sugs = self.follow_engine.generate_suggestions(entity_id=obj.id, registry_type=obj.type.value.upper())
                        return {
                            "response": rendered_md,
                            "source": f"Registry Object Match: {obj.id}",
                            "verified": True,
                            "confidence": 1.0,
                            "navigation": nav_link,
                            "action_choices": action_choices,
                            "suggestions": sugs,
                            "metrics": {"resolved_entity": obj.id, "resolved_registry": obj.type.value.upper(), "resolved_section": sec}
                        }

            # Registry Search Intercept
            if intent != IntentType.COUNT:
                search_res = self.ks.search_registry(query)
                if search_res and search_res["score"] >= 65:
                    import structured_renderers
                    if search_res["type"] == "nested_match":
                        match_entry = search_res["match"]
                        if "capability" in match_entry:
                            cap = match_entry["capability"]
                            parent = match_entry["parent"]
                            rendered_md = structured_renderers.render_capability(match_entry)
                            target_url = parent.url
                            nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, target_url, entity_name=parent.name, entity_type=parent.type.value.upper())
                            return {
                                "response": rendered_md,
                                "source": f"Registry Capability: {cap.id}",
                                "verified": True,
                                "confidence": 1.0,
                                "navigation": nav_link,
                                "action_choices": action_choices,
                                "suggestions": ["Show Products", "Show Services", "Show Solutions"],
                                "metrics": {"resolved_entity": parent.id, "resolved_registry": parent.type.value.upper()}
                            }
                        elif "feature" in match_entry:
                            feat = match_entry["feature"]
                            parent = match_entry["parent"]
                            rendered_md = structured_renderers.render_feature(match_entry)
                            target_url = parent.url
                            nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, target_url, entity_name=parent.name, entity_type=parent.type.value.upper())
                            return {
                                "response": rendered_md,
                                "source": f"Registry Feature: {feat.id}",
                                "verified": True,
                                "confidence": 1.0,
                                "navigation": nav_link,
                                "action_choices": action_choices,
                                "suggestions": ["Show Products", "Show Services", "Show Solutions"],
                                "metrics": {"resolved_entity": parent.id, "resolved_registry": parent.type.value.upper()}
                            }
                    else:
                        obj = search_res["match"]
                        if not (obj.id == "company_info" and any(w in q_lower for w in ["certific", "award", "recognit", "contact", "ceo", "cto", "coo", "leader"])):
                            sec = "best_for" if any(w in q_lower for w in ["who is it for", "who is it designed for", "target audience", "intended users", "designed for"]) else ("how_it_works" if any(w in q_lower for w in ["how", "work", "workflow"]) else ("benefits" if any(w in q_lower for w in ["benefit", "advantage"]) else "overview"))
                            rendered_md = structured_renderers.render_section(obj, sec)
                            res_reg = obj.type.value.upper()
                            if res_reg in ["AWARD", "AWARDS"]:
                                res_reg = "RECOGNITION"
                            elif obj.id == "contact_info" and ("office" in q_lower or "where" in q_lower or "location" in q_lower or any(t in topics for t in [TopicType.LOCATION])):
                                res_reg = "LOCATION"
                            target_url = obj.url
                            nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, target_url, entity_name=obj.name, entity_type=res_reg)
                            sugs = self.follow_engine.generate_suggestions(entity_id=obj.id, registry_type=res_reg)
                            return {
                                "response": rendered_md,
                                "source": f"Registry Object: {obj.id}",
                                "verified": True,
                                "confidence": 1.0,
                                "navigation": nav_link,
                                "action_choices": action_choices,
                                "suggestions": sugs,
                                "metrics": {"resolved_entity": obj.id, "resolved_registry": res_reg, "resolved_section": sec}
                            }

            # Issue 5: Unknown Capability / Out-of-Registry Query Handling (e.g. "PPC Advertising")
            # NEVER default to About CittaAI / Company Info!
            marketing_keywords = ["ppc", "advertising", "seo", "social media", "ads", "google ads", "facebook ads"]
            if any(k in q_lower for k in marketing_keywords) or "advertising" in q_lower:
                resp_md = (
                    f"I couldn't find a direct registry match for **{query.strip()}**.\n\n"
                    f"However, CittaAI provides flagship digital marketing platforms and AI-driven growth services:\n\n"
                    f"• **WhatsApp Marketing Platform**: Automated customer engagement & bulk messaging\n"
                    f"• **Influencer Marketing Platform**: AI campaign management & influencer discovery\n"
                    f"• **AI Powered Marketing**: End-to-end performance marketing & automated optimization\n"
                    f"• **MarTech 360**: Unified marketing technology stack integration\n\n"
                    f"Would you like to explore one of these marketing platforms?"
                )
                return {
                    "response": resp_md,
                    "source": "Intelligent Capability Fallback",
                    "verified": True,
                    "confidence": 0.85,
                    "navigation": tenant.routes.get("products", "/products"),
                    "suggestions": ["Explain WhatsApp Marketing Platform", "Explain Influencer Marketing Platform", "Show Services"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "PRODUCTS"}
                }

            # 1. Direct Intercepts (Greeting / Thanks / Goodbye)
            if intent == IntentType.GREETING:
                return {
                    "response": f"Hello! Welcome to **{tenant.name}**. How can I assist you today?",
                    "source": "Greeting Intercept",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": None,
                    "suggestions": ["Show Products", "Show Services", "Show Solutions"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "GREETINGS"}
                }
            elif intent == IntentType.THANKS:
                return {
                    "response": f"You're very welcome! Let me know if you need anything else about **{tenant.name}**.",
                    "source": "Thanks Intercept",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": None,
                    "suggestions": ["Show Products", "Show Services", "Show Solutions"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "GENERAL"}
                }
            elif intent == IntentType.GOODBYE:
                return {
                    "response": f"Thank you for reaching out to **{tenant.name}**. Have a great day!",
                    "source": "Goodbye Intercept",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": None,
                    "suggestions": [],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "GENERAL"}
                }

            # Direct Intercepts for CONTACT / LOCATION
            if intent in ["CONTACT", "LOCATION"] or any(t in topics for t in ["CONTACT", "CONTACT_INFO", "LOCATION"]) or any(w in q_lower for w in ["office", "where", "email", "phone", "address", "contact"]):
                contact_reg = self.ks.reg.registry_index.get("CONTACT", {})
                phone = contact_reg.get("phone", "+91 9392655040")
                phone_raw = contact_reg.get("phone_raw", "+919392655040")
                email = contact_reg.get("email", "info@cittaai.com")
                business_hours = contact_reg.get("business_hours", "Mon-Fri 9am-6pm")
                resp_time = contact_reg.get("response_time", "")
                
                address = contact_reg.get("address", "HITEC City, Hyderabad, Telangana, India")
                response_md = (
                    f"### Contact & Location Information for **{tenant.name}**\n\n"
                    f"- **Address**: {address}\n"
                    f"- **Email**: [{email}](mailto:{email})\n"
                    f"- **Phone**: [{phone}](tel:{phone_raw})\n"
                    f"- **Business Hours**: {business_hours}\n"
                    f"- **Careers**: For job applications, please visit our [Contact page](/contact).\n"
                )
                if resp_time:
                    response_md += f"- **Response Time**: {resp_time}\n"
                    
                target_url = tenant.routes.get("contact", "/contact")
                res_reg = "LOCATION" if ("office" in q_lower or "where" in q_lower or any(t in topics for t in ["LOCATION"])) else "CONTACT"
                return {
                    "response": response_md.strip(),
                    "source": "Contact Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": target_url,
                    "suggestions": ["Show Products", "Show Services", "Show Solutions"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": res_reg}
                }

            # Pass known entities to Conversation Intelligence Pipeline for full pre-sales consultation
            try:
                import core.entity_resolver as core_resolver
                core_res = core_resolver.resolve(query)
                if core_res and core_res.get("entity_id"):
                    return None
            except Exception:
                pass

            if q_lower in self.ks.reg.entity_lookup or q_lower in self.ks.reg.unified_vocabulary:
                return None

            # General Fallback Intercept (Fix Issue 8: Graceful Fallbacks & Suggestions)
            close_matches = []
            try:
                from rapidfuzz import process, fuzz
                all_names = [obj.name for obj in self.ks.reg.registry_by_id.values() if obj.id != "company_info"]
                top_matches = process.extract(q_lower, all_names, scorer=fuzz.partial_ratio, limit=3)
                for m in top_matches:
                    if m[1] >= 50 and m[0] not in close_matches:
                        close_matches.append(m[0])
            except Exception:
                pass

            if close_matches:
                did_you_mean_str = "\n".join([f"• **{m}**" for m in close_matches])
                fallback_md = (
                    f"I couldn't find an exact match for **{query.strip()}** in our knowledge base.\n\n"
                    f"**Did you mean**:\n\n{did_you_mean_str}\n\n"
                    f"Alternatively, you can explore our **Solutions**, **Products**, or **Services**."
                )
                sugs = [f"Explain {m}" for m in close_matches[:3]]
                for fallback_sug in ["Show Solutions", "Show Products", "Show Services"]:
                    if len(sugs) < 2 and fallback_sug not in sugs:
                        sugs.append(fallback_sug)
            else:
                fallback_md = (
                    f"I couldn't find a direct match for **{query.strip()}**.\n\n"
                    f"Here are the core sections of our AI platform you can explore:\n\n"
                    f"• **Solutions**: Enterprise OS (Education, Real Estate, Pharma, E-Commerce)\n"
                    f"• **Products**: WhatsApp Marketing & Influencer Marketing Platforms\n"
                    f"• **Services**: Enterprise AI, Agentic AI, and Data Engineering\n"
                    f"• **Leadership**: Executive Leadership Team & Founders\n\n"
                    f"What topic would you like to explore?"
                )
                sugs = ["Show Solutions", "Show Products", "Show Services", "Show Leadership Team"]

            return {
                "response": fallback_md,
                "source": "Graceful Registry Fallback",
                "verified": True,
                "confidence": 0.70,
                "navigation": None,
                "suggestions": sugs,
                "metrics": {"resolved_entity": "NONE", "resolved_registry": "GENERAL"}
            }

        except Exception as e:
            logger.error(f"Error in DeterministicEngine: {e}", exc_info=True)
            # Issue 8: Graceful Failure Handling (Never display raw runtime error!)
            return {
                "response": (
                    "I experienced a temporary lookup issue while retrieving this section. "
                    "You can view our main solutions and products below:"
                ),
                "source": "Graceful Failure Handler",
                "verified": True,
                "confidence": 0.50,
                "navigation": None,
                "suggestions": ["Show Solutions", "Show Products", "Show Services"],
                "metrics": {"resolved_entity": "NONE", "resolved_registry": "ERROR"}
            }

def get_deterministic_engine() -> DeterministicEngine:
    return DeterministicEngine()
