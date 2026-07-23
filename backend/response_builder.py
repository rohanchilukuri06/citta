import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent
COMPILED_DIR = BACKEND_DIR / "knowledge" / "compiled"

# Suggestions mappings for subcategories
STATIC_SUGGESTIONS = {
    "PRODUCTS": [
        "Explain WhatsApp Marketing Platform",
        "Explain Influencer Marketing Platform",
        "Compare WhatsApp and Influencer Platforms"
    ],
    "SERVICES": [
        "What does Data Engineering include?",
        "Explain Enterprise & Agentic AI service",
        "Tell me about AI Strategy & Advisory"
    ],
    "SOLUTIONS": [
        "Explain Enterprise AI OS features",
        "What does E-Commerce OS provide?",
        "Tell me about Pharma & Healthcare OS"
    ],
    "RECOGNITION": [
        "Tell me more about the AP MSME Challenge.",
        "What is the AI-Powered DPR Preparation Solution?",
        "What is the SaaS-Based Export Console?",
        "What industries does CittaAI serve?"
    ],
    "PARTNERS": [
        "Which industries do your enterprise partners belong to?",
        "What solutions do you provide to enterprise partners?",
        "Tell me about your products.",
        "How can I contact CittaAI?"
    ],
    "COMPANY_INFO": [
        "Who founded CittaAI?",
        "What certifications does CittaAI hold?",
        "How do I apply for a job?"
    ],
    "CONTACT": [
        "What are your business hours?",
        "Where is the head office located?",
        "How do I contact CittaAI?"
    ],
    "LOCATION": [
        "Where is your head office located?",
        "What is your address?",
        "How do I contact CittaAI?"
    ],
    "DISAMBIGUATE": [
        "Show Products",
        "Show Services",
        "Show Solutions"
    ]
}

_TEMPLATES_CACHE = None
_REGISTRY_FILES_CACHE = {}
_PROFILES_CACHE = None

def load_templates() -> Dict[str, str]:
    global _TEMPLATES_CACHE
    if _TEMPLATES_CACHE is not None:
        return _TEMPLATES_CACHE
    path = COMPILED_DIR / "templates.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                _TEMPLATES_CACHE = json.load(f)
                return _TEMPLATES_CACHE
        except Exception as e:
            logger.error(f"Error loading templates.json: {e}")
    _TEMPLATES_CACHE = {}
    return _TEMPLATES_CACHE

def load_registry_file(filename: str) -> Any:
    if filename in _REGISTRY_FILES_CACHE:
        return _REGISTRY_FILES_CACHE[filename]
    path = COMPILED_DIR / filename
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                res = json.load(f)
                _REGISTRY_FILES_CACHE[filename] = res
                return res
        except Exception as e:
            logger.error(f"Error loading registry file {filename}: {e}")
    _REGISTRY_FILES_CACHE[filename] = None
    return None

def load_response_profiles() -> Dict[str, Any]:
    global _PROFILES_CACHE
    if _PROFILES_CACHE is not None:
        return _PROFILES_CACHE
    config_path = BACKEND_DIR / "knowledge" / "config" / "response_profiles.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                _PROFILES_CACHE = json.load(f)
                return _PROFILES_CACHE
        except Exception as e:
            logger.error(f"Error loading response_profiles.json: {e}")
    _PROFILES_CACHE = {
        "SHORT": {"max_words": 80},
        "STANDARD": {"max_words": 180},
        "DETAILED": {"max_words": 400}
    }
    return _PROFILES_CACHE

def apply_response_profile(text: str, profile_name: str = "STANDARD") -> str:
    """Enforces maximum word count constraint based on loaded profile."""
    if not text:
        return text
    profiles = load_response_profiles()
    profile = profiles.get(profile_name.upper(), profiles.get("STANDARD", {"max_words": 180}))
    max_words = profile.get("max_words", 180)
    
    words = text.split()
    if len(words) > max_words:
        truncated_text = " ".join(words[:max_words])
        return truncated_text + "\n\n*... [Content truncated due to response profile word limit]*"
    return text

# --- Section-Specific Builders ---

def build_overview(entity: Dict[str, Any]) -> Optional[str]:
    title = entity.get("name") or entity.get("title") or "Entity"
    
    # If it is a Case Study entity
    if "challenge" in entity or "results" in entity:
        industry = entity.get("industry", "Enterprise")
        challenge = entity.get("challenge", "")
        solution = entity.get("solution", "")
        results = entity.get("results", "")
        metrics = entity.get("metrics", [])
        
        md = f"### {title} ({industry} Case Study) — Overview\n\n"
        if challenge:
            md += f"**Challenge**: {challenge}\n\n"
        if solution:
            md += f"**Solution**: {solution}\n\n"
        if results:
            md += f"**Results**: {results}\n\n"
        if metrics:
            md += "**Key Performance Metrics**:\n"
            for m in metrics:
                md += f"- {m}\n"
            md += "\n"
        return md.strip()
        
    overview = entity.get("overview")
    desc = entity.get("description", "")
    
    md = f"Yes. CittaAI offers an enterprise platform called **{title}**.\n\n"
    if isinstance(overview, dict):
        summary = overview.get("summary")
        description = overview.get("description") or desc
        if summary:
            md += f"{summary}\n\n"
        if description:
            md += f"{description}\n\n"
    else:
        description = overview or desc
        if description:
            md += f"{description}\n\n"

    # Add capabilities checkmarks
    capabilities = entity.get("capabilities", [])
    if capabilities and isinstance(capabilities, list):
        md += "It combines:\n"
        for cap in capabilities[:5]:
            if isinstance(cap, dict):
                c_title = cap.get("title", "")
                c_desc = cap.get("description", "")
                md += f"✓ **{c_title}**: {c_desc}\n" if c_desc else f"✓ **{c_title}**\n"
            else:
                md += f"✓ {cap}\n"
        md += "\n"

    target_users = entity.get("target_users", [])
    if target_users and isinstance(target_users, list):
        md += f"This makes it suitable for {', '.join(target_users)}."

    return md.strip()

def build_how_it_works(entity: Dict[str, Any]) -> Optional[str]:
    title = entity.get("name", "Entity")
    how = entity.get("how_it_works")
    if not how:
        return None
        
    md = f"### {title} — How It Works\n\n"
    if isinstance(how, dict):
        process = how.get("process")
        steps = how.get("steps")
        if process:
            md += f"{process}\n\n"
        if steps:
            md += "**Workflow Steps**:\n"
            for step in steps:
                md += f"- {step}\n"
            md += "\n"
    else:
        md += f"{how}\n\n"
    return md.strip()

def build_features(entity: Dict[str, Any]) -> Optional[str]:
    title = entity.get("name", "Entity")
    features = entity.get("features") or entity.get("capabilities", [])
    if not features:
        return None
        
    md = f"### {title} — Core Features\n\n"
    for f in features:
        md += f"- {f}\n"
    return md.strip()

def build_benefits(entity: Dict[str, Any]) -> Optional[str]:
    title = entity.get("name", "Entity")
    benefits = entity.get("benefits", [])
    if not benefits:
        return None
        
    md = f"### {title} — Key Benefits\n\n"
    for b in benefits:
        md += f"- {b}\n"
    return md.strip()

def build_best_for(entity: Dict[str, Any]) -> Optional[str]:
    title = entity.get("name", "Entity")
    best = entity.get("best_for")
    if not best:
        return None
        
    md = f"### {title} — Ideal Target Profile\n\n"
    if isinstance(best, list):
        for item in best:
            md += f"- {item}\n"
    else:
        md += f"{best}\n"
    return md.strip()

def build_implementation(entity: Dict[str, Any]) -> Optional[str]:
    title = entity.get("name", "Entity")
    impl = entity.get("implementation")
    if not impl:
        return None
        
    md = f"### {title} — Implementation & Onboarding\n\n"
    if isinstance(impl, dict):
        desc = impl.get("description") or impl.get("process")
        steps = impl.get("steps")
        if desc:
            md += f"{desc}\n\n"
        if steps:
            md += "**Onboarding Pipeline**:\n"
            for step in steps:
                md += f"- {step}\n"
            md += "\n"
    else:
        md += f"{impl}\n\n"
    return md.strip()

def build_integrations(entity: Dict[str, Any]) -> Optional[str]:
    title = entity.get("name", "Entity")
    integrations = entity.get("integrations")
    if not integrations:
        return None
        
    md = f"### {title} — Integrations & APIs\n\n"
    for item in integrations:
        md += f"- {item}\n"
    return md.strip()

def build_faq(entity: Dict[str, Any]) -> Optional[str]:
    title = entity.get("name", "Entity")
    faq = entity.get("faq")
    if not faq:
        return None
        
    md = f"### {title} — Frequently Asked Questions\n\n"
    for item in faq:
        q = item.get("question")
        a = item.get("answer")
        md += f"**Q: {q}**\n*A: {a}*\n\n"
    return md.strip()

def build_case_studies(entity: Dict[str, Any]) -> Optional[str]:
    title = entity.get("name", "Entity")
    ent_id = entity.get("id")
    
    # Load case studies registry
    cs_reg = load_registry_file("case_studies.json")
    if not cs_reg or not cs_reg.get("entities"):
        return None
        
    # Filter case studies where entity ID is in related_entities
    matched_cs = []
    for cs in cs_reg["entities"]:
        rel = cs.get("related_entities", [])
        if ent_id in rel:
            matched_cs.append(cs)
            
    if not matched_cs:
        return None
        
    md = f"### {title} — Verified Case Studies\n\n"
    for cs in matched_cs:
        md += f"#### 📈 {cs['title']} ({cs['industry']} Industry)\n"
        md += f"- **Challenge**: {cs['challenge']}\n"
        md += f"- **Solution**: {cs['solution']}\n"
        md += f"- **Results**: {cs['results']}\n"
        metrics = cs.get("metrics", [])
        if metrics:
            md += "- **Key Performance Metrics**:\n"
            for m in metrics:
                md += f"  - {m}\n"
        md += "\n"
    return md.strip()

def build_company_info(sections: Optional[List[str]] = None) -> Optional[str]:
    comp_data = load_registry_file("company.json") or {}
    if not comp_data:
        return None
    sections = [s.lower() for s in (sections or ["overview"])]
    name = comp_data.get("name", "CittaAI")
    desc = comp_data.get("description", "")
    vision = comp_data.get("vision", "")
    mission = comp_data.get("mission", "")
    tagline = comp_data.get("tagline", "")

    md = f"### {name} — Corporate Overview\n\n"
    md += f"**Overview**: {desc}\n\n"

    if "mission" in sections or "overview" in sections or len(sections) > 1:
        if mission:
            md += f"**Mission**: {mission}\n\n"
    if "vision" in sections or "overview" in sections or len(sections) > 1:
        if vision:
            md += f"**Vision**: {vision}\n\n"
    if tagline:
        md += f"**Tagline**: *{tagline}*\n\n"

    md += "Explore more on our [About page](/about) or reach out via [Contact page](/contact)."
    return md.strip()

def build_leadership(entity: Optional[Dict[str, Any]] = None, role: Optional[str] = None, entity_id: Optional[str] = None) -> Optional[str]:
    lead_data = load_registry_file("leadership.json") or {}
    leaders = lead_data.get("leaders", [])
    others = lead_data.get("others", [])
    all_people = leaders + others
    
    if not leaders and not others:
        return None

    target_person = None
    if entity and isinstance(entity, dict) and "title" in entity:
        target_person = entity
    elif role or entity_id:
        lookup_key = (role or entity_id or "").lower().strip()
        for person in all_people:
            p_id = person.get("id", "").lower()
            p_name = person.get("name", "").lower()
            p_title = person.get("title", "").lower()
            p_aliases = [str(a).lower() for a in person.get("aliases", [])]
            if (lookup_key == p_id or lookup_key in p_title or lookup_key in p_name or any(lookup_key == a for a in p_aliases)):
                target_person = person
                break

    if target_person:
        name_str = target_person.get("name")
        title_str = target_person.get("title")
        return (
            f"### {name_str} — {title_str}\n\n"
            f"**{name_str}** is the **{title_str}** at CittaAI / Fixity Technologies.\n\n"
            f"You can view the full executive leadership team on our [About page](/about)."
        )

    md = "### CittaAI Leadership Team\n\n"
    if leaders:
        md += "**Executive Leadership**:\n"
        for leader in leaders:
            md += f"- **{leader['name']}**: {leader['title']}\n"
        md += "\n"
    if others:
        md += "**Functional & Divisional Directors**:\n"
        for person in others:
            md += f"- **{person['name']}**: {person['title']}\n"
        md += "\n"
        
    md += "Our leadership team consists of seasoned enterprise software executives, AI researchers, and engineering leaders committed to deploying robust cognitive OS architectures globally."
    return md.strip()

def build_recognition(entity: Optional[Dict[str, Any]] = None) -> Optional[str]:
    rec_data = load_registry_file("recognition.json") or {}
    recognitions = rec_data.get("recognitions", [])
    
    if not recognitions:
        return None
        
    md = "🏆 **CittaAI Awards & Recognitions**\n\n"
    for idx, item in enumerate(recognitions):
        md += f"{idx + 1}. **{item['title']}**\n"
        awards = item.get("awards", [])
        for award in awards:
            md += f"   - {award}\n"
        org = item.get("organization")
        edition = f" — {item['edition']}" if item.get("edition") else ""
        if org:
            md += f"   *Organized by {org}{edition}.*\n"
        md += "\n"
    return md.strip()

def build_contact(entity: Optional[Dict[str, Any]] = None) -> Optional[str]:
    cont = load_registry_file("contact.json") or {}
    phone = cont.get("phone", "+91 9392655040")
    email = cont.get("email", "info@cittaai.com")
    hours = cont.get("business_hours", "Mon-Fri 9am-6pm")
    resp_time = cont.get("response_time", "24 hours")
    
    md = (
        f"📞 **Contact CittaAI**\n\n"
        f"For custom solutions, partnership queries, or scoping sessions:\n"
        f"- **Phone**: {phone}\n"
        f"- **Email**: {email}\n"
        f"- **Business Hours**: {hours}\n"
        f"- **Response Desk**: {resp_time}\n"
    )
    return md

def build_location(entity: Optional[Dict[str, Any]] = None) -> Optional[str]:
    loc = load_registry_file("location.json") or {}
    address = loc.get("address", "HITEC City, Hyderabad, India")
    maps_link = loc.get("maps_link", "")
    
    md = "🏢 **CittaAI Corporate Headquarters**\n\n"
    md += f"- **Address**: {address}\n"
    if maps_link:
        md += f"- **Explore on Map**: [Google Maps]({maps_link})\n"
    return md.strip()

def build_technologies(entity: Dict[str, Any]) -> Optional[str]:
    tech = entity.get("technologies")
    if not tech:
        return None
        
    title = entity.get("name", "Entity")
    md = f"### {title} — Technologies & Integration Stack\n\n"
    for item in tech:
        md += f"- {item}\n"
    return md.strip()

def build_examples(entity: Dict[str, Any]) -> Optional[str]:
    examples = entity.get("examples")
    if not examples:
        return None
        
    title = entity.get("name", "Entity")
    md = f"### {title} — Reference Examples & Use Cases\n\n"
    if isinstance(examples, list):
        for item in examples:
            if isinstance(item, dict):
                md += f"#### 💡 {item.get('name') or item.get('title')}\n"
                md += f"{item.get('description') or item.get('content')}\n\n"
            else:
                md += f"- {item}\n"
    else:
        md += f"{examples}\n"
    return md.strip()

def build_related_entities(entity: Dict[str, Any]) -> Optional[str]:
    related = entity.get("related_entities", [])
    if not related:
        return None
        
    title = entity.get("name", "Entity")
    
    # Lazy load registry to prevent circular imports
    from knowledge_registry import get_registry
    reg = get_registry()
    
    md = f"### {title} — Related Offerings\n\n"
    for rel_id in related:
        rel_ent = reg.get_entity(rel_id)
        if rel_ent:
            md += f"- **[{rel_ent['name']}]({rel_ent['route']})**: {rel_ent['summary']}\n"
    return md.strip()


# Suggestions tone helpers
class ResponsePersonalizer:
    @staticmethod
    def personalize(
        raw_text: str, 
        query_type: str, 
        domain: str, 
        matched_entity: Optional[Dict[str, Any]] = None
    ) -> str:
        contact = load_registry_file("contact.json") or {}
        phone = contact.get("phone", "+91 9392655040")
        email = contact.get("email", "info@cittaai.com")
        
        name = matched_entity.get("name", "CittaAI enterprise solutions") if matched_entity else "CittaAI enterprise solutions"
        route = matched_entity.get("route", "/contact") if matched_entity else "/contact"
        
        if matched_entity:
            cat = matched_entity.get("category", "")
            btn_text = "Learn More →" if cat == "product" else "Explore Service →" if cat == "service" else "View Solution →"
        else:
            btn_text = "Talk to Our Team →"
            
        if query_type == "PURCHASE" and matched_entity:
            caps = "\n".join([f"• {c}" for c in (matched_entity.get("features") or matched_entity.get("capabilities", []))])
            benefits = "\n".join([f"• {b}" for b in matched_entity.get("benefits", [])])
            
            return (
                f"**Absolutely!**\n\n"
                f"Yes, CittaAI can help you deploy and scale your business using our **{name}**.\n\n"
                f"Whether you need to coordinate:\n"
                f"{caps}\n\n"
                f"Our platform is designed to align with your specific enterprise requirements.\n\n"
                f"**Key Benefits**:\n"
                f"{benefits}\n\n"
                f"If you'd like, I can explain how onboarding works, help coordinate a timeline, or schedule a direct team briefing.\n\n"
                f"📞 **Action Desk**:\n"
                f"- **Sales Phone**: {phone}\n"
                f"- **Sales Email**: {email}\n"
                f"- **Scoping Action**: [{btn_text}]({route})"
            )
            
        if query_type == "CONSULTATION" and matched_entity:
            benefits = "\n".join([f"• {b}" for b in matched_entity.get("benefits", [])])
            return (
                f"🤝 **CittaAI AI Strategy & Consultation**\n\n"
                f"CittaAI serves as a long-term AI transformation partner. For **{name}**, we coordinate feasibility audits, audit model safety, and priority use-case mappings to ensure high performance.\n\n"
                f"**Key Outcomes**:\n"
                f"{benefits}\n\n"
                f"Let's schedule a strategy consultation to evaluate your deployment roadmap:\n"
                f"- **Desk Line**: {phone}\n"
                f"- **Scoping Inquiry**: {email}\n"
                f"- **Calendar Desk**: [{btn_text}]({route})"
            )
            
        if query_type == "IMPLEMENTATION" and matched_entity:
            caps = "\n".join([f"• {c}" for c in (matched_entity.get("features") or matched_entity.get("capabilities", []))])
            return (
                f"🛠️ **Production-Ready Engineering**\n\n"
                f"Deploying **{name}** requires strict data pipelines, custom offline adapters, and compliance guardrails. CittaAI's engineering desk designs and executes the entire implementation pipeline.\n\n"
                f"**Deployment Scope**:\n"
                f"{caps}\n\n"
                f"Let's align on your data architecture and rollout timeline:\n"
                f"- **Contact Phone**: {phone}\n"
                f"- **Contact Email**: {email}\n"
                f"- **Action Route**: [{btn_text}]({route})"
            )
            
        if query_type == "DEMO_REQUEST" and matched_entity:
            return (
                f"📺 **Book a Live Scoping Demo**\n\n"
                f"We would be glad to coordinate a live demonstration of **{name}** running on real client scenarios so you can witness the latency, accuracy, and telemetry dashboards firsthand.\n\n"
                f"- **Direct Desk**: {phone}\n"
                f"- **Mail Booking**: {email}\n"
                f"- **Request Form**: [{btn_text}]({route})"
            )
            
        if query_type == "CONTACT_SALES" or query_type in ["PURCHASE", "CONSULTATION", "IMPLEMENTATION", "DEMO_REQUEST"]:
            return (
                f"💼 **Connect with CittaAI Sales & Advisory**\n\n"
                f"Ready to elevate operations and deploy agentic intelligence? Our sales architects are ready to design a custom quote based on your scale.\n\n"
                f"- **Desk Line**: {phone}\n"
                f"- **Inquiry Mailbox**: {email}\n"
                f"- **Contact Desk**: [Talk to Our Team](/contact)"
            )
            
        if query_type == "COMPARE":
            return (
                f"### Comparison Analysis\n\n"
                f"Here is a side-by-side view comparing CittaAI offerings:\n\n"
                f"{raw_text}\n\n"
                f"Would you like to explore specific integration blueprints for either platform?"
            )
            
        return raw_text


def build_deterministic_response(
    query_type: str, 
    domain: str, 
    matched_entity_id: Optional[str] = None, 
    section: Optional[str] = None,
    profile_name: str = "STANDARD",
    role: Optional[str] = None,
    sections: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Directly builds a response from the compiled business knowledge files.
    """
    templates = load_templates()
    if not templates:
        return None

    # Static intercepts
    if query_type == "GREETING":
        return {
            "response": templates.get("greeting", "Hello! Welcome to CittaAI."),
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "navigation": None,
            "suggestions": ["Show Products", "Show Services", "Show Solutions"]
        }
    if query_type == "THANKS":
        return {
            "response": templates.get("thanks", "You're welcome!"),
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "navigation": None,
            "suggestions": ["Show Products", "Show Services", "Show Solutions"]
        }
    if query_type == "GOODBYE":
        return {
            "response": templates.get("goodbye", "Goodbye!"),
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "navigation": None,
            "suggestions": ["Show Products", "Show Services", "Show Solutions"]
        }
    if query_type == "SMALL_TALK":
        return {
            "response": templates.get("small_talk", "I can help you explore CittaAI's products and services."),
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "navigation": None,
            "suggestions": ["Show Products", "Show Services", "Show Solutions"]
        }
    if query_type == "OUT_OF_DOMAIN":
        return {
            "response": templates.get("out_of_domain", ""),
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "navigation": None,
            "suggestions": STATIC_SUGGESTIONS["DISAMBIGUATE"]
        }
    if query_type == "UNKNOWN_IN_DOMAIN" or domain == "UNKNOWN_IN_DOMAIN":
        return {
            "response": "I couldn't find verified information about this topic in the current knowledge base.",
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "navigation": None,
            "suggestions": ["Show Products", "Show Services", "Show Solutions"]
        }
    if query_type == "DISAMBIGUATE":
        return {
            "response": templates.get("disambiguation", ""),
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "navigation": None,
            "suggestions": STATIC_SUGGESTIONS["DISAMBIGUATE"]
        }

    # Load matched entity data
    entity = None
    if matched_entity_id:
        from knowledge_registry import get_registry
        reg = get_registry()
        entity = reg.get_entity(matched_entity_id)

    # Handle global/flat registry domains (non-entity specific)
    if domain == "LEADERSHIP":
        raw_text = build_leadership(entity=entity, role=role, entity_id=matched_entity_id)
        if raw_text:
            personalize_text = apply_response_profile(raw_text, profile_name)
            return {
                "response": personalize_text,
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "navigation": "/about",
                "suggestions": ["Who is CTO?", "Who is Founder?", "Show Products"]
            }

    if domain == "COMPANY_INFO":
        raw_text = build_company_info(sections=sections)
        if raw_text:
            personalize_text = apply_response_profile(raw_text, profile_name)
            return {
                "response": personalize_text,
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "navigation": "/about",
                "suggestions": ["Who is CEO?", "What products do you offer?", "Contact CittaAI"]
            }

    global_builders = {
        "RECOGNITION": build_recognition,
        "CONTACT": build_contact,
        "LOCATION": build_location
    }
    
    if domain in global_builders:
        builder = global_builders[domain]
        raw_text = builder()
        if raw_text:
            personalize_text = apply_response_profile(raw_text, profile_name)
            nav = "/about" if domain == "LEADERSHIP" else "/recognition" if domain == "RECOGNITION" else "/contact"
            return {
                "response": personalize_text,
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "navigation": nav,
                "suggestions": STATIC_SUGGESTIONS.get(domain, ["Show Products", "Show Services", "Show Solutions"])
            }

    # If it is a pricing query
    if domain == "PRICING":
        pricing = load_registry_file("pricing.json") or {}
        resp = pricing.get("response", "CittaAI does not publicly publish pricing information.")
        return {
            "response": resp,
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "navigation": "/contact",
            "suggestions": ["Book Strategy Call", "Contact Us"]
        }

    # Load matched entity data
    entity = None
    if matched_entity_id:
        # Load from get_registry to be robust
        from knowledge_registry import get_registry
        reg = get_registry()
        entity = reg.get_entity(matched_entity_id)

    # Handle buyer intent customizations
    if query_type in ["PURCHASE", "CONSULTATION", "IMPLEMENTATION", "DEMO_REQUEST", "CONTACT_SALES"]:
        personalize_text = ResponsePersonalizer.personalize("", query_type, domain, entity)
        return {
            "response": personalize_text,
            "source": "Business Registry",
            "verified": True,
            "confidence": 1.0,
            "navigation": "/contact",
            "suggestions": STATIC_SUGGESTIONS["CONTACT"]
        }

    # Handle LIST Query Types (PRODUCTS, SERVICES, SOLUTIONS)
    if query_type == "LIST":
        from knowledge_registry import get_registry
        reg = get_registry()
        if domain == "PRODUCTS":
            items_str = "\n".join([f"- **{p['name']}**: {p['summary']} [Learn More →]({p['route']})" for p in reg.products])
            resp = templates.get("products_list", "").format(items=items_str)
            return {
                "response": apply_response_profile(resp, profile_name),
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "navigation": "/products/whatsapp-marketing",
                "suggestions": STATIC_SUGGESTIONS["PRODUCTS"]
            }
        elif domain == "SERVICES":
            items_str = "\n".join([f"- **{s['name']}**: {s['summary']} [Explore Service →]({s['route']})" for s in reg.services])
            resp = templates.get("services_list", "").format(items=items_str)
            return {
                "response": apply_response_profile(resp, profile_name),
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "navigation": "/services",
                "suggestions": STATIC_SUGGESTIONS["SERVICES"]
            }
        elif domain == "SOLUTIONS":
            items_str = "\n".join([f"- **{s['name']}**: {s['summary']} [View Solution →]({s['route']})" for s in reg.solutions])
            resp = templates.get("solutions_list", "").format(items=items_str)
            return {
                "response": apply_response_profile(resp, profile_name),
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "navigation": "/solutions/ecommerce-os",
                "suggestions": STATIC_SUGGESTIONS["SOLUTIONS"]
            }
        elif domain == "CASE_STUDIES":
            cs_data = load_registry_file("case_studies.json") or {}
            cs_list = cs_data.get("entities", [])
            items_str = []
            for cs in cs_list:
                c_title = cs.get("title") or cs.get("name")
                c_results = cs.get("results") or cs.get("challenge") or ""
                items_str.append(f"- **{c_title}**: {c_results} [View Case Study](/case-studies)")
            resp = "### CittaAI Case Studies & Client Success Stories\n\n" + "\n".join(items_str)
            return {
                "response": apply_response_profile(resp, profile_name),
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "navigation": "/case-studies",
                "suggestions": ["Show Jewellery Brand case study", "Show FMCG Brand case study", "Show Spices Export case study"]
            }

    # Handle DETAIL Query Type with section-specific builders
    if query_type == "DETAIL" and matched_entity_id and entity:
        builder_map = {
            "overview": build_overview,
            "how_it_works": build_how_it_works,
            "features": build_features,
            "benefits": build_benefits,
            "best_for": build_best_for,
            "implementation": build_implementation,
            "integrations": build_integrations,
            "faq": build_faq,
            "case_studies": build_case_studies,
            "technologies": build_technologies,
            "examples": build_examples,
            "related_entities": build_related_entities
        }
        
        target_section = section.lower() if section else "overview"
        if target_section not in builder_map:
            target_section = "overview"
            
        builder = builder_map[target_section]
        raw_text = builder(entity)
        
        if raw_text:
            sugs = []
            entity_name = entity.get("name") or entity.get("title") or "Entity"
            if domain == "PRODUCTS":
                sugs = [f"What capabilities does {entity_name} offer?", f"How does {entity_name} work?", "Compare WhatsApp and Influencer Platforms"]
            elif domain == "SERVICES":
                sugs = [f"What does {entity_name} include?", f"What are the benefits of {entity_name}?", "List your professional services"]
            elif domain == "SOLUTIONS":
                sugs = [f"Explain {entity_name} benefits", f"What capabilities does {entity_name} provide?", "List your industry solutions"]
            elif domain == "CASE_STUDIES":
                sugs = ["Show FMCG Brand case study", "Show Spices Export case study", "List all case studies"]

            return {
                "response": apply_response_profile(raw_text, profile_name),
                "source": "Business Registry",
                "verified": True,
                "confidence": 1.0,
                "navigation": entity.get("route") or "/case-studies",
                "suggestions": sugs
            }

    return None

def validate_response_source(expected_domain: str, actual_source: str) -> bool:
    return True
