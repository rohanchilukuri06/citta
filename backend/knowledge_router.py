import re
import logging
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger(__name__)

_ROUTING_ORDER_CACHE = None

def load_routing_order() -> List[str]:
    global _ROUTING_ORDER_CACHE
    if _ROUTING_ORDER_CACHE is not None:
        return _ROUTING_ORDER_CACHE
    config_path = Path(__file__).resolve().parent / "knowledge" / "config" / "routing.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _ROUTING_ORDER_CACHE = data.get("routing_order", [])
                return _ROUTING_ORDER_CACHE
        except Exception as e:
            logger.error(f"Error loading routing.json order: {e}")
    _ROUTING_ORDER_CACHE = ["cache", "golden_answers", "business_registry", "faq", "hybrid_rag", "fallback"]
    return _ROUTING_ORDER_CACHE

def route_query(
    query_text: str,
    normalized_query: str,
    registry_type: Optional[str],
    registry_score: float,
    entity_id: Optional[str],
    entity_score: float,
    section: Optional[str],
    section_score: float,
    clarification_data: Optional[Dict[str, Any]],
    conversation_state: Dict[str, Any],
    registry_index: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Knowledge Router:
    Determines WHERE to retrieve the answer based on routing order, capabilities, and confidence scores.
    """
    routing_order = load_routing_order()
    q_clean = normalized_query.lower().strip()
    
    # 1. Early Intercept for dynamic count requests
    if "how many" in q_clean or "number of" in q_clean or "count of" in q_clean:
        if "case" in q_clean:
            return {
                "response": "CittaAI currently has **3 published case studies**:\n\n1. **Jewellery Brand**: Scaled e-commerce revenue with 3.5 Cr impact & 4.2x ROI.\n2. **FMCG Brand**: Real-time stock level synchronization across multi-channel retail.\n3. **B2B Spices Export**: Automated global trade documentation and buyer communication.",
                "source": "Case Studies Registry",
                "verified": True,
                "confidence": 1.0,
                "suggestions": ["Show Jewellery Brand case study", "Show FMCG Brand case study", "Show Spices Export case study"],
                "redirect": "/case-studies",
                "explainability": {"route": "case_studies_count", "reason": "Intercepted case studies count request."}
            }
        elif "product" in q_clean:
            return {
                "response": "CittaAI currently offers **2 flagship products**:\n\n1. **WhatsApp Marketing Platform**: Unified enterprise automation & multi-agent support desks.\n2. **Influencer Marketing Platform**: Creator analytics, contract workflow, and ROI tracking.",
                "source": "Products Registry",
                "verified": True,
                "confidence": 1.0,
                "suggestions": ["Explain WhatsApp Marketing Platform", "Explain Influencer Marketing Platform"],
                "redirect": "/products/whatsapp-marketing",
                "explainability": {"route": "products_count", "reason": "Intercepted products count request."}
            }
        elif "solution" in q_clean:
            return {
                "response": "CittaAI currently offers **7 enterprise OS solutions**:\n\n1. **E-Commerce OS**\n2. **Real Estate OS**\n3. **Pharma OS**\n4. **Education OS**\n5. **Smart Cities OS**\n6. **WhatsApp Marketing**\n7. **Data Engineering**",
                "source": "Solutions Registry",
                "verified": True,
                "confidence": 1.0,
                "suggestions": ["Explain E-Commerce OS", "Explain Real Estate OS", "Explain Pharma OS"],
                "redirect": "/solutions/ecommerce-os",
                "explainability": {"route": "solutions_count", "reason": "Intercepted solutions count request."}
            }
        elif "service" in q_clean:
            return {
                "response": "CittaAI currently provides **4 core services**:\n\n1. **Enterprise & Agentic AI**\n2. **Data Engineering**\n3. **AI Strategy & Advisory**\n4. **Custom Solution Engineering**",
                "source": "Services Registry",
                "verified": True,
                "confidence": 1.0,
                "suggestions": ["What does Data Engineering include?", "Explain Enterprise & Agentic AI service"],
                "redirect": "/services",
                "explainability": {"route": "services_count", "reason": "Intercepted services count request."}
            }

    # 2. Catalog / List Intent Intercepts
    if any(p in q_clean for p in ["case studies", "tell me about case studies", "list case studies", "list all case studies", "show case studies", "case study"]):
        return {
            "response": "**CittaAI Client Case Studies & Success Stories**:\n\n1. **Jewellery Brand**: Scaled e-commerce revenue with 3.5 Cr impact & 4.2x ROI.\n2. **FMCG Brand**: Real-time stock level synchronization across multi-channel retail.\n3. **B2B Spices Export**: Automated global trade documentation and buyer communication.",
            "source": "Case Studies Registry",
            "verified": True,
            "confidence": 1.0,
            "suggestions": ["Show Jewellery Brand case study", "Show FMCG Brand case study", "Show Spices Export case study"],
            "redirect": "/case-studies",
            "explainability": {"route": "case_studies_list", "reason": "Catalog list request for case studies."}
        }

    if any(p in q_clean for p in ["marketing product", "marketing products", "products for marketing"]) or ("marketing" in q_clean and "product" in q_clean):
        return {
            "response": (
                "Yes, we have **2 marketing products** in our products catalog:\n\n"
                "1. **WhatsApp Marketing Platform**: Unified enterprise broadcast messaging, automated customer engagement, and multi-agent support desks.\n"
                "2. **Influencer Marketing Platform**: Creator discovery marketplace, contract workflow management, and campaign ROI tracking.\n\n"
                "Would you like to explore **WhatsApp Marketing** or **Influencer Marketing** in detail?"
            ),
            "source": "Products Registry",
            "verified": True,
            "confidence": 1.0,
            "suggestions": ["Explain WhatsApp Marketing Platform", "Explain Influencer Marketing Platform", "Show Products"],
            "redirect": "/products/whatsapp-marketing",
            "explainability": {"route": "marketing_products", "reason": "Query for marketing products."}
        }

    if any(p in q_clean for p in ["marketing service", "marketing services", "services for marketing"]) or ("marketing" in q_clean and "service" in q_clean):
        return {
            "response": (
                "Yes, CittaAI provides marketing services through our **AI-Powered Marketing** catalog, which includes:\n\n"
                "• **Social Media Marketing Services** & autonomous growth engines\n"
                "• **Branding & Strategy** driven by AI intent & audience intelligence\n"
                "• **Automated Performance Marketing** & conversion optimization\n"
                "• **MarTech 360** unified tech stack integration\n\n"
                "Would you like to explore **AI-Powered Marketing** or **MarTech 360** services in detail?"
            ),
            "source": "Services Registry",
            "verified": True,
            "confidence": 1.0,
            "suggestions": ["Explain AI-Powered Marketing", "Explain MarTech 360", "Show Services"],
            "redirect": "/services/ai-powered-marketing",
            "explainability": {"route": "marketing_services", "reason": "Query for marketing services."}
        }

    if q_clean in ["products", "list products", "show products", "tell me about products"]:
        from response_builder import build_deterministic_response
        res = build_deterministic_response("LIST", "PRODUCTS")
        if res:
            return {
                "response": res["response"],
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "suggestions": res["suggestions"],
                "redirect": res["navigation"],
                "explainability": {"route": "products_list", "reason": "Catalog list request for products."}
            }

    if q_clean in ["solutions", "list solutions", "show solutions", "tell me about solutions"]:
        from response_builder import build_deterministic_response
        res = build_deterministic_response("LIST", "SOLUTIONS")
        if res:
            return {
                "response": res["response"],
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "suggestions": res["suggestions"],
                "redirect": res["navigation"],
                "explainability": {"route": "solutions_list", "reason": "Catalog list request for solutions."}
            }

    if q_clean in ["services", "list services", "show services", "tell me about services"]:
        from response_builder import build_deterministic_response
        res = build_deterministic_response("LIST", "SERVICES")
        if res:
            return {
                "response": res["response"],
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "suggestions": res["suggestions"],
                "redirect": res["navigation"],
                "explainability": {"route": "services_list", "reason": "Catalog list request for services."}
            }

    # 3. Person-Specific Executive Intercepts
    person_role_map = {
        "ceo": "CEO", "chief executive officer": "CEO", "akhil": "CEO", "akhil reddy": "CEO",
        "coo": "COO", "chief operating officer": "COO", "saladi": "COO", "saladi chandra balaji": "COO",
        "cmo": "CMO", "chief marketing officer": "CMO", "ganesh": "CMO",
        "founder": "FOUNDER"
    }
    target_role = None
    for r_key, r_val in person_role_map.items():
        if re.search(rf"\b{re.escape(r_key)}\b", q_clean):
            target_role = r_val
            break

    if target_role:
        from response_builder import build_deterministic_response
        res = build_deterministic_response("DETAIL", "LEADERSHIP", role=target_role)
        if res:
            return {
                "response": res["response"],
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "suggestions": res["suggestions"],
                "redirect": res["navigation"],
                "explainability": {"route": "person_leadership", "reason": f"Person-specific leadership query for '{target_role}'."}
            }
        
        # Direct fallback for leadership roles if builder yields None
        if target_role in ["CEO", "FOUNDER"]:
            resp_text = "The CEO of CittaAI is **Akhil Reddy**."
        elif target_role == "CTO":
            resp_text = "The Co-Founder & CTO of CittaAI is **Akhil Reddy**."
        elif target_role == "COO":
            resp_text = "The Co-Founder & COO of CittaAI is **Saladi Chandra Balaji**."
        elif target_role == "CMO":
            resp_text = "The CMO of CittaAI is **Ganesh Gandhi Vadalani**."
        else:
            resp_text = "CittaAI Leadership Team: Akhil Reddy (CEO), Saladi Chandra Balaji (Co-Founder & COO), Ganesh Gandhi Vadalani (CMO)."

        return {
            "response": resp_text,
            "source": "Leadership Registry",
            "verified": True,
            "confidence": 1.0,
            "suggestions": ["Who is the CEO?", "Who is the CTO?", "Who is the COO?"],
            "redirect": "/about",
            "explainability": {"route": "person_leadership", "reason": f"Person-specific leadership query for '{target_role}'."}
        }

    # 4. Careers / Job Application Intercept
    if any(k in q_clean for k in ["apply", "job", "career", "resume", "hire", "join"]):
        return {
            "response": "Currently, CittaAI does not offer an automated online resume upload portal. Interested candidates and enterprise partners can reach out directly via our [Contact page](/contact). If dedicated Careers information becomes available, the chatbot will direct users there.",
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "suggestions": ["Contact CittaAI", "Where is office", "Show Services"],
            "redirect": "/contact",
            "explainability": {"route": "careers_intercept", "reason": "Intercepted job application inquiry."}
        }

    # 5. Certifications & Recognition Intercept
    if any(k in q_clean for k in ["certification", "certifications", "compliance", "accreditation", "awards", "award", "recognition", "recognitions"]):
        return {
            "response": (
                "**CittaAI Awards & Government Recognitions**:\n\n"
                "1. **Winner – AP MSME Challenge 2024**: Recognized by Govt. of Andhra Pradesh for driving AI transformation across regional industries.\n"
                "2. **AI-Powered DPR Preparation Solution**: Automated Detail Project Report synthesis for state infrastructure projects.\n"
                "3. **SaaS-Based Export Console**: Standardized global compliance and trade logistics for regional MSME exporters."
            ),
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "suggestions": ["Tell me more about the AP MSME Challenge", "What is the AI-Powered DPR Solution?", "What is the Export Console?"],
            "redirect": "/about",
            "explainability": {"route": "recognition_intercept", "reason": "Intercepted certifications/awards query."}
        }

    # 6. Multi-section Company Query Intercept
    if ("company" in q_clean or "cittaai" in q_clean) and ("mission" in q_clean or "vision" in q_clean or "values" in q_clean):
        from response_builder import build_deterministic_response
        req_sections = ["overview"]
        if "mission" in q_clean:
            req_sections.append("mission")
        if "vision" in q_clean:
            req_sections.append("vision")
        if "values" in q_clean:
            req_sections.append("values")
        res = build_deterministic_response("DETAIL", "COMPANY_INFO", sections=req_sections)
        if res:
            return {
                "response": res["response"],
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "suggestions": res["suggestions"],
                "redirect": res["navigation"],
                "explainability": {"route": "company_multi_section", "reason": f"Multi-section query for company info ({req_sections})."}
            }
        
    # 2. Check for entity-level or section-level clarification blocks returned by resolvers
    if clarification_data:
        c_type = clarification_data.get("type")
        if c_type == "clarification":
            candidates = clarification_data.get("candidates", [])
            sugs = [c.get("name") for c in candidates]
            msg = clarification_data.get("message", "Did you mean:")
            bullet_list = "\n".join([f"• **{c.get('name')}**" for c in candidates])
            return {
                "response": f"{msg}\n\n{bullet_list}",
                "source": "Clarification Engine",
                "verified": True,
                "confidence": 1.0,
                "suggestions": sugs,
                "redirect": candidates[0].get("route") if candidates else None,
                "explainability": {
                    "route": "resolving_clarification",
                    "reason": "Clarification triggered by Resolver ambiguity or low confidence."
                }
            }

    # Evaluate routing pathways in configured order
        if step == "golden_answers":
            # Golden answers MUST NOT override queries targeting a specific entity or domain scope!
            if not entity_id and not (conversation_state and conversation_state.get("active_entity")):
                from response_builder import load_registry_file
                goldens = load_registry_file("golden_answers.json") or {}
                for key, val in goldens.items():
                    aliases = val.get("aliases", [])
                    for alias in aliases:
                        # Match exact query or multi-word exact alias match (do not match generic single words like 'solutions' inside domain queries)
                        if q_clean == alias.lower() or (len(alias.split()) > 1 and alias.lower() == q_clean):
                            ans = val.get("answer", {})
                            return {
                                "response": ans.get("response"),
                                "source": ans.get("source", "Golden Answers"),
                                "verified": ans.get("verified", True),
                                "confidence": 1.0,
                                "suggestions": ["Show Products", "Show Services", "Show Solutions"],
                                "redirect": ans.get("navigation"),
                                "explainability": {
                                    "route": "golden_answers",
                                    "reason": f"Matched golden answer alias '{alias}'."
                                }
                            }
                        
        elif step == "business_registry":
            from response_builder import build_deterministic_response
            
            # Case 1: Entity exists -> Detail Section or Overview
            if entity_id:
                reg_type = registry_type
                if not reg_type:
                    try:
                        from knowledge_registry import get_registry
                        reg = get_registry()
                        node = reg.knowledge_graph.get(entity_id)
                        if node:
                            reg_type = node.get("belongs_to")
                    except Exception:
                        pass
                
                # Check Registry Capabilities and Section Availability UX
                if reg_type:
                    reg_data = registry_index.get(reg_type)
                    if reg_data:
                        meta = reg_data.get("metadata", {})
                        supported_sections = meta.get("supported_sections", [])
                        
                        # Check Section Availability UX (fallback to overview if section not explicitly listed)
                        if section and section.lower() not in [s.lower() for s in supported_sections]:
                            section = "overview"
                
                detected_role = target_role if 'target_role' in locals() and target_role else None
                res = build_deterministic_response(
                    query_type="DETAIL",
                    domain=reg_type or "UNKNOWN",
                    matched_entity_id=entity_id,
                    section=section,
                    role=detected_role
                )
                if res:
                    return {
                        "response": res.get("response"),
                        "source": res.get("source", "Business Registry"),
                        "verified": res.get("verified", True),
                        "confidence": 1.0,
                        "suggestions": res.get("suggestions", []),
                        "redirect": res.get("navigation"),
                        "explainability": {
                            "route": "business_registry_detail",
                            "reason": f"Matched registry '{reg_type}' for entity '{entity_id}'."
                        }
                    }
                    
            # Case 2: Entity does not exist, but registry exists -> List Registry
            elif registry_type:
                res = build_deterministic_response(
                    query_type="LIST",
                    domain=registry_type,
                    matched_entity_id=None,
                    section=None
                )
                if res:
                    return {
                        "response": res.get("response"),
                        "source": res.get("source", "Business Registry"),
                        "verified": res.get("verified", True),
                        "confidence": 1.0,
                        "suggestions": res.get("suggestions", []),
                        "redirect": res.get("navigation"),
                        "explainability": {
                            "route": "business_registry_list",
                            "reason": f"Matched registry list for '{registry_type}'."
                        }
                    }
                    
        elif step == "faq":
            # Search static FAQs
            from response_builder import load_registry_file
            faq_data = load_registry_file("faq.json") or {}
            faqs = faq_data.get("entities", []) if isinstance(faq_data, dict) else faq_data or []
            
            for f in faqs:
                fq = f.get("question", "").lower()
                if q_clean in fq or fq in q_clean:
                    return {
                        "response": f.get("answer"),
                        "source": "FAQ Registry",
                        "verified": True,
                        "confidence": 1.0,
                        "suggestions": ["Show Products", "Show Services", "Show Solutions"],
                        "redirect": f.get("route"),
                        "explainability": {
                            "route": "faq",
                            "reason": f"Matched static FAQ question: '{f.get('question')}'."
                        }
                    }
                    
        elif step == "hybrid_rag":
            # Check Registry Capabilities for Reasoning
            if registry_type:
                reg_data = registry_index.get(registry_type)
                if reg_data:
                    meta = reg_data.get("metadata", {})
                    caps = meta.get("capabilities", {})
                    
                    if not caps.get("reasoning", True):
                        return {
                            "response": "CittaAI does not publicly publish verified details for that specific topic. Please contact our solutions architecture desk directly or book a strategy scoping call.",
                            "source": "RAG Guardrail",
                            "verified": True,
                            "confidence": 1.0,
                            "suggestions": ["Book Strategy Session", "Contact Desk"],
                            "redirect": "/contact",
                            "explainability": {
                                "route": "rag_guardrail_block",
                                "reason": f"Registry '{registry_type}' blocks reasoning."
                            }
                        }

    # If it falls through, return Fallback
    return {
        "response": "I'm sorry, I couldn't find a direct record for that query in our verified Business Registry. Would you like to ask about our Products, Services, or Solutions instead?",
        "source": "Fallback Router",
        "verified": True,
        "confidence": 1.0,
        "suggestions": ["Show Products", "Show Services", "Show Solutions"],
        "redirect": "/contact",
        "explainability": {
            "route": "fallback",
            "reason": "Falls through all routing priorities."
        }
    }
