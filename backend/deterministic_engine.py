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
            from phase2_orchestrator import check_general_catalog_query

            # Direct Collaboration / Onboarding / Getting Started Intercept
            collab_triggers = ["collaborate", "proceed", "ready to work", "work together", "partner with citta", "get started", "how to engage", "how can i proceed", "ready to collaborate"]
            if any(t in q_lower for t in collab_triggers):
                resp_md = (
                    "🤝 **We're excited to collaborate with you!**\n\n"
                    "To get started, you can reach out to our team directly:\n\n"
                    "• 📧 **Email**: info@cittaai.com\n"
                    "• 📞 **Call**: +91 9392655040\n"
                    "• 📍 **Visit Us**: 5th Floor, SVS One Building, Patrika Nagar Rd 2, HUDA Techno Enclave, HITEC City, Hyderabad, Telangana 500081\n\n"
                    "Feel free to give us a call, drop an email, or visit our Hyderabad office to discuss your requirements!"
                )
                return {
                    "response": resp_md,
                    "source": "CittaAI Onboarding Desk",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": "/contact",
                    "suggestions": ["Show Products", "Show Services", "Office Location"],
                    "metrics": {"resolved_entity": "contact_info", "resolved_registry": "CONTACT"}
                }

            # Allow follow-up queries with context pronouns or single section words to pass through
            from entity_resolver import contains_pronouns
            consultative_phrases = [
                "should we choose", "recommend", "best approach", "how should we", "advice", "guidance"
            ]
            if contains_pronouns(query) or any(p in q_lower for p in consultative_phrases) or q_lower in ["tell me how it works", "how it works", "how does it work", "tell me more", "benefits", "features", "overview", "workflows", "faq"]:
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

            # Multi-Category Intercept (Dynamically filter requested categories with word boundaries)
            norm_q = q_lower
            for typo, fix in [
                ("prodcuts", "products"), ("prodcut", "product"), ("prducts", "products"), ("prduct", "product"),
                ("porducts", "products"), ("porduct", "product"), ("srevices", "services"), ("serivces", "services"),
                ("servises", "services"), ("solutins", "solutions"), ("soltuions", "solutions")
            ]:
                norm_q = norm_q.replace(typo, fix)

            import re
            def match_kw(kw_list):
                for kw in kw_list:
                    if re.search(r"\b" + re.escape(kw) + r"\b", norm_q):
                        return True
                return False

            has_products = match_kw(["product", "products", "saas", "platform"])
            has_solutions = match_kw(["solution", "solutions", "operating system", "os"])
            has_services = match_kw(["service", "services", "consulting", "advisory"])
            has_team = match_kw(["team", "leadership", "founder", "executive", "ceo", "cto"])
            has_cases = match_kw(["case study", "case studies", "clients"])
            has_awards = match_kw(["award", "awards", "achievement", "achievements", "recognition"])
            has_contact = match_kw(["contact", "location", "address", "phone", "email", "office"])

            # If query targets a specific industry sector (education, pharma, real estate, etc.), skip broad multi-category intercept
            specific_industry_mentioned = any(ind in norm_q for ind in ["education", "pharma", "real estate", "healthcare", "health care", "smart cities", "ecommerce", "e-commerce", "whatsapp", "influencer"])

            requested_cats = []
            if has_products: requested_cats.append("Products")
            if has_solutions: requested_cats.append("Solutions")
            if has_services: requested_cats.append("Services")
            if has_team: requested_cats.append("Leadership")
            if has_cases: requested_cats.append("Case Studies")
            if has_awards: requested_cats.append("Awards")
            if has_contact: requested_cats.append("Contact Info")

            is_everything = any(w in norm_q for w in ["everything", "all details", "complete overview", "full catalog"]) or len(requested_cats) >= 5

            if not specific_industry_mentioned and (len(requested_cats) >= 2 or is_everything):
                sections = []
                
                if has_products or is_everything:
                    sections.append(
                        "#### 🏆 Products\n"
                        "• **WhatsApp Marketing Platform**: High-volume messaging, official WhatsApp Business API integration, AI auto-replies, and shared team inbox.\n"
                        "• **Influencer Marketing Platform**: Creator discovery, campaign workflow management, UGC asset generation, and ROI analytics."
                    )
                
                if has_solutions or is_everything:
                    sections.append(
                        "#### 🌐 Solutions (Industry Operating Systems)\n"
                        "• **Enterprise AI OS**: Flagship platform for RAG, multi-agent swarms, document AI extraction, and voice agents.\n"
                        "• **E-Commerce OS**: Storefront to supply chain automation, dynamic pricing, inventory sync, and support bots.\n"
                        "• **Education OS**: Multi-college LMS, student cohort management, coding contest platform, and video libraries.\n"
                        "• **Pharma OS**: Digitized batch record reviews, deviation/CAPA dashboards, and APQR compliance tools.\n"
                        "• **Real Estate OS**: Property listings, omnichannel lead tracking, partner management, and document vaults.\n"
                        "• **Smart Cities OS**: IoT mobility intelligence, utility resource management, and citizen data analytics."
                    )

                if has_services or is_everything:
                    sections.append(
                        "#### ⚡ Services\n"
                        "• **AI Strategy & Advisory**: AI readiness assessment, strategic roadmaps, use case prioritization, and AI governance.\n"
                        "• **Enterprise & Agentic AI**: Custom LLM fine-tuning, multi-agent swarms, RAG solutions, and conversational AI.\n"
                        "• **Data Engineering**: Real-time data pipelines, cloud data warehouses, data lake architecture, and Master Data Management (MDM).\n"
                        "• **AI-Powered Marketing**: Algorithmic SEO keyword ecosystems, self-optimizing predictive PPC, content generation, and social signal monitoring.\n"
                        "• **MarTech 360**: Full-funnel intelligence ingesting search intent, audience behavior, and competitor signals."
                    )

                if has_team or is_everything:
                    sections.append(
                        "#### 👥 Executive Leadership Team\n"
                        "• **Akhil Reddy** — CEO (Enterprise AI Solutions)\n"
                        "• **Saladi Chandra Balaji** — Co-Founder & COO (Operations & Strategic Execution)\n"
                        "• **Vinay Velivela** — CEO of Fixity Technologies\n"
                        "• **Ganesh Gandhi Vadalani** — CMO (Global Brand & Marketing Strategy)\n"
                        "• **Harish Nerati** — Operations & Sales Head (Sales Growth & Client Success)\n"
                        "• **Aravind Reddy** — E-Commerce Head (Digital Commerce Strategy)\n"
                        "• **Parvatha Mohan** — Business Development Head (Strategic Alliances & Partnerships)"
                    )

                if has_cases or is_everything:
                    sections.append(
                        "#### 📈 Client Case Studies\n"
                        "• **Jewellery Brand**: Generated ₹3.5 Cr+ ROI from a single WhatsApp engagement campaign with a 98% read rate.\n"
                        "• **FMCG Brand**: Grew Instagram community from 2K to 37K followers and generated 1,000+ UGC assets.\n"
                        "• **B2B Spices Export**: Generated 50+ tons of export inquiries in 1 month with a 70% lower CPL."
                    )

                if has_awards or is_everything:
                    sections.append(
                        "#### 🎖️ Awards & Recognition\n"
                        "• **Best AI Startup of the Year (2025)**: HYBIZ TV Business Excellence Awards.\n"
                        "• **AP MSME Digital Empowerment Challenge (2025)**: Double Winner (AI DPR Preparation & SaaS Export Console)."
                    )

                if has_contact or is_everything:
                    sections.append(
                        "#### 📍 Contact Information\n"
                        "• **Email**: info@cittaai.com | **Phone**: +91 9392655040\n"
                        "• **Office**: 5th Floor, SVS One Building, Patrika Nagar Rd 2, HITEC City, Hyderabad, Telangana 500081"
                    )

                title_cats = " & ".join(requested_cats) if requested_cats and not is_everything else "Complete Knowledge"
                header = f"### 🌟 CittaAI {title_cats} Overview\n\n"
                footer = "\n\nWhich offering would you like to explore in detail?"
                comp_resp = header + "\n\n".join(sections) + footer

                sug_list = [f"Explain {c}" for c in requested_cats[:3]] if requested_cats else ["Explain Enterprise AI OS", "Explain WhatsApp Marketing Platform"]

                return {
                    "response": comp_resp,
                    "source": "CittaAI Knowledge Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "suggestions": sug_list,
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "MULTI"}
                }

            # Category Listing Intercepts (SERVICES, PRODUCTS, SOLUTIONS)
            svc_triggers = {
                "services", "what are the services", "what services do you offer", "what services", 
                "list services", "list all services", "show services", "show all services", "our services", "services offered", 
                "what services does cittaai provide", "what services are available",
                "what are the services provided", "services provided", "what are the srevices provided",
                "srevices", "srevices provided", "srevice", "serivces", "what services do you have"
            }
            if q_lower in svc_triggers or (check_general_catalog_query(query) and ("service" in q_lower or "services" in q_lower or "srevice" in q_lower or "srevices" in q_lower) and any(w in q_lower for w in ["what", "list", "show", "our", "all", "available", "provide", "offer", "tell me about"])):
                services_resp = (
                    "### CittaAI Enterprise Services\n\n"
                    "#### 1. Data Engineering\n"
                    "**Capabilities:**\n"
                    "• Real-time Data Pipelines\n"
                    "• Cloud Data Warehouse\n"
                    "• Data Lake Architecture\n"
                    "• Master Data Management\n\n"
                    "#### 2. Enterprise & Agentic AI\n"
                    "**Capabilities:**\n"
                    "• Custom LLM Fine-tuning\n"
                    "• Multi-Agent Systems\n"
                    "• RAG Solutions\n"
                    "• Conversational AI\n\n"
                    "#### 3. AI Strategy & Advisory\n"
                    "**Capabilities:**\n"
                    "• AI Readiness Assessment\n"
                    "• Strategic Roadmap\n"
                    "• Use Case Prioritization\n"
                    "• AI Governance\n\n"
                    "#### 4. AI-Powered Marketing\n"
                    "**Capabilities:**\n"
                    "• Branding & Strategy\n"
                    "• Social Media Marketing\n"
                    "• Content & Design\n"
                    "• SEO\n"
                    "• PPC Advertising\n"
                    "• E-commerce Growth\n"
                    "• WhatsApp Marketing Automation\n"
                    "• Influencer Marketing\n\n"
                    "Which service would you like to explore in detail?"
                )
                nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, tenant.routes.get("services", "/services"), entity_type="SERVICES")
                return {
                    "response": services_resp,
                    "source": "Services Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": nav_link,
                    "action_choices": action_choices,
                    "suggestions": ["Explain Data Engineering", "Explain Enterprise & Agentic AI", "Explain AI Strategy"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "SERVICES"}
                }

            prod_triggers = {"products", "what are the products", "what products do you offer", "what products", "list products", "list all products", "show products", "show all products", "our products", "products offered", "what products does cittaai provide", "what products are available", "what products do you have"}
            if q_lower in prod_triggers or (check_general_catalog_query(query) and ("product" in q_lower or "products" in q_lower) and any(w in q_lower for w in ["what", "list", "show", "our", "all", "available", "provide", "offer", "tell me about"])):
                products = self.ks.list_entities(tenant_id, "PRODUCTS")
                if products:
                    items_str = "\n".join([f"• **{p.get('name') or p.get('title')}**: {p.get('overview') or p.get('description') or p.get('summary') or 'Flagship Product'}" for p in products])
                else:
                    items_str = (
                        "• **WhatsApp Marketing Platform**: Scalable WhatsApp engagement and bulk broadcast automation.\n"
                        "• **Influencer Marketing Platform**: Creator discovery, campaign analytics, and ROI optimization."
                    )
                nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, tenant.routes.get("products", "/products"), entity_type="PRODUCTS")
                return {
                    "response": (
                        f"🏆 **CittaAI Flagship Products**\n\n"
                        f"CittaAI offers the following enterprise SaaS platforms:\n\n{items_str}\n\n"
                        f"Would you like to learn more about one of these platforms?"
                    ),
                    "source": "Products Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": nav_link,
                    "action_choices": action_choices,
                    "suggestions": ["Explain WhatsApp Marketing Platform", "Explain Influencer Marketing Platform"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "PRODUCTS"}
                }

            sol_triggers = {"solutions", "what are the solutions", "what solutions do you offer", "what solutions", "list solutions", "list all solutions", "show solutions", "show all solutions", "our solutions", "solutions offered", "industry os", "operating systems", "what solutions does cittaai provide", "what solutions do you have"}
            if q_lower in sol_triggers or (check_general_catalog_query(query) and ("solution" in q_lower or "solutions" in q_lower or "operating system" in q_lower) and any(w in q_lower for w in ["what", "list", "show", "our", "all", "available", "provide", "offer", "tell me about"])):
                solutions = self.ks.list_entities(tenant_id, "SOLUTIONS")
                if solutions:
                    items_str = "\n".join([f"• **{s.get('name') or s.get('title')}**: {s.get('overview') or s.get('description') or s.get('summary') or 'Industry OS'}" for s in solutions])
                else:
                    items_str = (
                        "• **Enterprise AI OS**: Multi-model routing and compliance controls.\n"
                        "• **E-Commerce OS**: Live inventory sync, billing desks, and shopping desks.\n"
                        "• **Pharma & Healthcare OS**: Clinical files, queue management, and batch tracks.\n"
                        "• **Smart Cities OS**: Ticket routing, municipal monitors, and resource dashboards.\n"
                        "• **Education OS**: Student information systems, grading workflows, and classroom modules.\n"
                        "• **Real Estate OS**: Interactive asset directories, property leads, and contract tools."
                    )
                nav_link, action_choices = self.nav_ctrl.process_navigation(understanding.navigation_intent, tenant.routes.get("solutions", "/solutions"), entity_type="SOLUTIONS")
                return {
                    "response": (
                        f"🌐 **CittaAI Industry Operating Systems (OS)**\n\n"
                        f"We deploy secure middleware orchestrating data, automation, and compliance:\n\n{items_str}\n\n"
                        f"Which solution OS fits your industry requirements?"
                    ),
                    "source": "Solutions Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": nav_link,
                    "action_choices": action_choices,
                    "suggestions": ["Explain E-Commerce OS", "Explain Smart Cities OS", "Explain Pharma & Healthcare OS"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "SOLUTIONS"}
                }

            # Global Capability Listing Intercept ("list capabilities", "what capabilities do you offer")
            cap_list_triggers = {"capabilities", "list capabilities", "list all capabilities", "what capabilities do you offer", "what capabilities are available", "show capabilities", "our capabilities", "capabilities offered"}
            if q_lower in cap_list_triggers or (check_general_catalog_query(query) and ("capability" in q_lower or "capabilities" in q_lower) and any(w in q_lower for w in ["what", "list", "show", "our", "all", "available", "provide", "offer"])):
                cap_summary = (
                    "⚡ **CittaAI Enterprise Capabilities Catalog**\n\n"
                    "Capabilities belong to our four professional Services:\n\n"
                    "• **Enterprise & Agentic AI**:\n"
                    "  - Custom LLM Fine-tuning\n"
                    "  - Multi-Agent Systems\n"
                    "  - RAG Solutions\n"
                    "  - Conversational AI\n\n"
                    "• **Data Engineering**:\n"
                    "  - Real-time Data Pipelines\n"
                    "  - Cloud Data Warehouse\n"
                    "  - Data Lake Architecture\n"
                    "  - Master Data Management\n\n"
                    "• **AI Strategy & Advisory**:\n"
                    "  - AI Readiness Assessment\n"
                    "  - Strategic Roadmap\n"
                    "  - Use Case Prioritization\n"
                    "  - AI Governance\n\n"
                    "• **AI-Powered Marketing**:\n"
                    "  - Branding & Strategy | SEO | PPC Advertising\n"
                    "  - Social Media Marketing | Content & Design\n"
                    "  - WhatsApp Marketing Automation | Influencer Marketing | E-commerce Growth\n\n"
                    "Which capability or parent service would you like to explore?"
                )
                return {
                    "response": cap_summary,
                    "source": "Capabilities Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "suggestions": ["Show Enterprise & Agentic AI capabilities", "Show Data Engineering capabilities", "What service does RAG Solutions belong to?"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "CAPABILITIES"}
                }

            # Taxonomy Classification Queries Intercept ("Is [X] a [Product/Service/Solution/Capability]?", "What category is [X]?")
            import re
            classif_match = re.search(r"^(is|what category is|what type of offering is)\s+(?:the\s+)?(.+?)\s*(?:a|an)?\s*(product|service|solution|capability)?\??$", q_lower)
            if classif_match:
                prefix_word = classif_match.group(1)
                entity_phrase = classif_match.group(2).strip()
                queried_cat = (classif_match.group(3) or "").upper()
                entity_phrase = re.sub(r"^(a|an|the)\s+", "", entity_phrase).strip()

                import core.entity_resolver as core_resolver
                res = core_resolver.resolve(entity_phrase)
                if res and res.get("entity_id"):
                    obj = self.ks.reg.registry_by_id.get(res["entity_id"])
                    if obj or res.get("entity_category") == "CAPABILITY":
                        ent_name = res.get("matched_capability") or (obj.name if obj else entity_phrase.title())
                        true_cat = res.get("entity_category") or (obj.type.value.upper() if obj else "UNKNOWN")

                        cat_descriptions = {
                            "PRODUCT": "a **Product** (ready-made software platform)",
                            "SOLUTION": "a **Solution** (Industry-specific Enterprise Operating System)",
                            "SERVICE": "a **Service** (professional consulting, engineering, implementation, & advisory service)",
                            "CAPABILITY": "a **Capability** (specialized sub-service belonging to a parent service)"
                        }

                        if queried_cat:
                            if true_cat == queried_cat:
                                resp_text = f"Yes. **{ent_name}** is {cat_descriptions.get(true_cat, f'a **{true_cat}**')}."
                            else:
                                resp_text = f"No. **{ent_name}** is {cat_descriptions.get(true_cat, f'a **{true_cat}**')} rather than a {queried_cat.title()}."
                        else:
                            resp_text = f"**{ent_name}** is classified as {cat_descriptions.get(true_cat, f'a **{true_cat}**')}."

                        if true_cat == "CAPABILITY" and res.get("parent_service"):
                            resp_text += f"\n\nIt belongs to the **{res['parent_service']}** service."
                        elif obj and hasattr(obj, "overview") and obj.overview:
                            resp_text += f"\n\n*{obj.overview}*"

                        return {
                            "response": resp_text,
                            "source": "Catalog Classification Registry",
                            "verified": True,
                            "confidence": 1.0,
                            "suggestions": [f"Explain {ent_name}", f"List {true_cat.lower()}s"],
                            "metrics": {"resolved_entity": res.get("entity_id") or "CAPABILITY", "resolved_registry": true_cat}
                        }

            # Parent Relationship Queries Intercept ("What service does [X] belong to?", "Which service includes [X]?")
            parent_rel_match = re.search(r"\b(what|which)\s+service\s+(?:does|includes)\s+(.+?)\s+(?:belong to|part of|included in|have)\b", q_lower) or re.search(r"\bparent\s+service\s+of\s+(.+)\b", q_lower)
            if parent_rel_match:
                cap_phrase = parent_rel_match.group(2) if parent_rel_match.lastindex and parent_rel_match.lastindex >= 2 else parent_rel_match.group(1)
                cap_phrase = re.sub(r"^(a|an|the)\s+", "", cap_phrase.strip()).strip()

                import core.entity_resolver as core_resolver
                res = core_resolver.resolve(cap_phrase)
                cap_entry = self.ks.reg.registry_by_capability.get(cap_phrase.lower())
                
                if cap_entry or (res and res.get("parent_service")):
                    parent_svc = (cap_entry["parent"].name if cap_entry else res.get("parent_service"))
                    cap_name = (cap_entry["capability"].title if cap_entry else (res.get("matched_capability") or cap_phrase.title()))
                    return {
                        "response": f"**{cap_name}** is a specialized capability offered under CittaAI's **{parent_svc}** service.",
                        "source": "Catalog Parent Relationship Registry",
                        "verified": True,
                        "confidence": 1.0,
                        "suggestions": [f"Explain {cap_name}", f"Capabilities of {parent_svc}"],
                        "metrics": {"resolved_entity": cap_name, "resolved_registry": "CAPABILITY"}
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
                any(re.search(r"\b" + k + r"\b", q_lower) for k in ["leadership team", "management team", "executive management", "leadership", "executive", "executives", "founder", "founders", "ceo", "cto", "coo", "cmo", "vinay", "akhil", "saladi", "balaji", "ganesh", "harish", "aravind", "parvatha"])):
                
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

            # Specific Intercept for Marketing Products and Marketing Services
            if any(k in q_lower for k in ["marketing product", "marketing products", "products for marketing", "do they have any marketing products", "do you have any marketing products", "do you have marketing products", "what marketing products"]):
                resp_md = (
                    "Yes, we have **2 marketing products** in our products catalog:\n\n"
                    "1. **WhatsApp Marketing Platform**: Unified enterprise broadcast messaging, automated customer engagement, and multi-agent support desks.\n"
                    "2. **Influencer Marketing Platform**: Creator discovery marketplace, contract workflow management, and campaign ROI tracking.\n\n"
                    "Would you like to explore **WhatsApp Marketing** or **Influencer Marketing** in detail?"
                )
                return {
                    "response": resp_md,
                    "source": "Products Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": "/products/whatsapp-marketing",
                    "suggestions": ["Explain WhatsApp Marketing Platform", "Explain Influencer Marketing Platform", "Show Products"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "PRODUCTS"}
                }

            if any(k in q_lower for k in ["marketing service", "marketing services", "services for marketing", "do they have any marketing services", "do you have any marketing services", "do you have marketing services", "what marketing services"]):
                resp_md = (
                    "Yes, CittaAI provides marketing services through our **AI-Powered Marketing** catalog, which includes:\n\n"
                    "• **Social Media Marketing Services** & autonomous growth engines\n"
                    "• **Branding & Strategy** driven by AI intent & audience intelligence\n"
                    "• **Automated Performance Marketing** & conversion optimization\n"
                    "• **MarTech 360** unified tech stack integration\n\n"
                    "Would you like to explore **AI-Powered Marketing** or **MarTech 360** services in detail?"
                )
                return {
                    "response": resp_md,
                    "source": "Services Registry",
                    "verified": True,
                    "confidence": 1.0,
                    "navigation": "/services/ai-powered-marketing",
                    "suggestions": ["Explain AI-Powered Marketing", "Explain MarTech 360", "Show Services"],
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "SERVICES"}
                }

            import config
            from phase2_orchestrator import check_general_catalog_query
            if getattr(config, "USE_NEW_ENTITY_RESOLVER", True) and not check_general_catalog_query(query):
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
                        from intent_classifier import classify_requested_category, format_category_mismatch_explanation
                        req_cat, req_conf, is_ambig = classify_requested_category(query)
                        ent_cat = obj.type.value.upper()

                        if is_ambig and "or" not in q_lower and res.get("entity_category") != "CAPABILITY" and entity_confidence < 0.9:
                            return {
                                "response": f"Could you please specify whether you are looking for an enterprise software product/solution or professional consulting services for {obj.name}?",
                                "source": "Category Ambiguity Clarification",
                                "verified": True,
                                "confidence": 0.8,
                                "navigation": None,
                                "suggestions": [f"Explain {obj.name} Solution", f"Services for {obj.name}"],
                                "metrics": {"resolved_entity": obj.id, "resolved_registry": ent_cat}
                            }

                        import structured_renderers
                        sec = (
                            "best_for" if any(w in q_lower for w in ["who is it for", "who is it designed for", "target audience", "intended users", "designed for", "industries", "who should use", "customers"])
                            else ("how_it_works" if any(w in q_lower for w in ["how", "work", "workflow", "process", "pipeline", "steps", "mechanism"])
                            else ("benefits" if any(w in q_lower for w in ["benefit", "benefits", "advantage", "advantages", "value", "roi", "pros"])
                            else ("features" if any(w in q_lower for w in ["feature", "features", "module", "modules", "functions", "specs"])
                            else ("capabilities" if any(w in q_lower for w in ["capability", "capabilities"])
                            else ("faq" if any(w in q_lower for w in ["faq", "faqs", "questions", "question", "q&a"])
                            else ("pricing" if any(w in q_lower for w in ["price", "pricing", "cost", "fee", "rate", "plan"])
                            else ("contact" if any(w in q_lower for w in ["contact", "address", "phone", "email", "office"])
                            else ("relationships" if any(w in q_lower for w in ["related", "relationship", "relationships", "dependencies"])
                            else "overview")))))))))
                        
                        if res.get("entity_category") == "CAPABILITY" and res.get("capability_entry"):
                            cap_entry = res["capability_entry"]
                            cap_title = res.get("matched_capability") or cap_entry["capability"].title
                            parent_service = res.get("parent_service") or cap_entry["parent"].name
                            prefix = f"**{cap_title}** is a specialized capability offered under CittaAI's **{parent_service}** service."
                            cap_md = structured_renderers.render_capability(cap_entry)
                            rendered_md = f"{prefix}\n\n{cap_md}"
                        else:
                            rendered_md = structured_renderers.render_section(obj, sec)
                            if req_cat != "UNKNOWN" and req_cat != ent_cat:
                                prefix = format_category_mismatch_explanation(obj.name, ent_cat, req_cat)
                                rendered_md = f"{prefix}\n\n{rendered_md}"

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
                        if not (obj.id == "company_info" and any(re.search(rf"\b{re.escape(w)}\b", q_lower) for w in ["certific", "award", "recognit", "contact", "ceo", "cto", "coo", "leader"])):
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

            # Pass to RAGService entity resolver & LLM provider instead of hardcoded fallback
            return None

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            exc_type = type(e).__name__
            tb_obj = e.__traceback__
            filename = ""
            line_number = 0
            if tb_obj:
                while tb_obj.tb_next:
                    tb_obj = tb_obj.tb_next
                filename = tb_obj.tb_frame.f_code.co_filename
                line_number = tb_obj.tb_lineno

            norm_q = "N/A"
            try:
                if hasattr(self, 'ks') and hasattr(self.ks, 'reg'):
                    from query_normalizer import normalize_query_pipeline
                    norm_q = normalize_query_pipeline(query, self.ks.reg.unified_vocabulary, self.ks.reg.abbreviations, entity_lookup=self.ks.reg.entity_lookup)
                else:
                    norm_q = query.lower().strip()
            except Exception:
                norm_q = query.lower().strip()

            logger.error(
                f"=== Railway Debug ===\n"
                f"Exception Type: {exc_type}\n"
                f"Filename: {filename}\n"
                f"Line Number: {line_number}\n"
                f"Original Query: {query}\n"
                f"Normalized Query: {norm_q}\n"
                f"Resolved Entity: NONE\n"
                f"Resolved Registry: ERROR\n"
                f"Full Traceback:\n{tb}"
            )
            logger.exception("=== Railway Debug Exception ===")
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
                "metrics": {"resolved_entity": "NONE", "resolved_registry": "ERROR", "error": str(e)}
            }

def get_deterministic_engine() -> DeterministicEngine:
    return DeterministicEngine()
