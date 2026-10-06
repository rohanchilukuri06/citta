import os
import json
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, List

REGISTRY_DIR = Path("backend/knowledge/registry")
OLD_DIR = REGISTRY_DIR / "old"
NEW_DIR = REGISTRY_DIR / "new"

# Ensure dirs exist
OLD_DIR.mkdir(parents=True, exist_ok=True)
NEW_DIR.mkdir(parents=True, exist_ok=True)

def generate_uuid(name: str) -> str:
    # Reproducible UUIDv5 based on name
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"cittaai.com.{name}"))

def backup_files():
    print("Backing up current registry files to 'old/'...")
    for f in REGISTRY_DIR.glob("*.json"):
        if f.name != "manifest.json" and not f.name.startswith("new") and not f.name.startswith("old"):
            shutil.copy2(f, OLD_DIR / f.name)
            print(f"  Backed up {f.name}")

def migrate_product_solution(filename: str, id_val: str, type_val: str, slug_val: str):
    file_path = REGISTRY_DIR / filename
    if not file_path.exists():
        print(f"Warning: File {filename} not found.")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    name = data.get("product_name") or data.get("name") or id_val.replace("_", " ").title()
    tagline = data.get("tagline", "")
    description = data.get("description", "")
    cta = data.get("cta", "Get Started")
    
    capabilities_list = []
    for cap in data.get("capabilities", []):
        cap_title = cap.get("title", "")
        cap_id = f"{id_val}_" + cap_title.lower().replace(" & ", "_").replace(" + ", "_").replace(" ", "_").replace("(", "").replace(")", "").strip("_")
        
        # Features mapping
        features_list = []
        for feat in cap.get("features", []):
            feat_id = feat.lower().replace(":", "").replace(" ", "_").replace("/", "_").strip("_")[:50]
            features_list.append({
                "id": feat_id,
                "title": feat,
                "description": f"Feature support for {feat} in {cap_title}.",
                "keywords": [w.lower() for w in feat.split() if len(w) > 3]
            })
            
        capabilities_list.append({
            "id": cap_id,
            "title": cap_title,
            "subtitle": cap.get("subtitle", ""),
            "description": cap.get("description", ""),
            "keywords": [w.lower() for w in cap_title.split() if len(w) > 3],
            "aliases": [cap_title.lower()],
            "features": features_list,
            "benefits": [],
            "relationships": []
        })
        
    # Process Workflow
    workflow_list = []
    how_it_works = data.get("how_it_works", {})
    steps = how_it_works.get("steps", [])
    for idx, step in enumerate(steps):
        workflow_list.append({
            "step": idx + 1,
            "title": step,
            "description": step
        })
        
    # Search Boosting Keywords
    primary = [name.lower()]
    secondary = [tagline.lower()]
    aliases = [id_val, id_val.replace("_", "-"), id_val.replace("_", " ")]
    synonyms = []
    
    if "whatsapp" in id_val:
        primary.extend(["whatsapp marketing", "whatsapp business", "wa campaign"])
        secondary.extend(["inbox desk", "mass broadcast", "drip templates"])
        aliases.extend(["wa", "whatsapp", "whastapp"])
    elif "influencer" in id_val:
        primary.extend(["influencer marketing", "creator payouts", "influencer campaigns"])
        secondary.extend(["utm analytics", "ugc assets", "creator database"])
        aliases.extend(["influencer", "creator"])
    elif "education" in id_val:
        primary.extend(["college lms", "education platform", "test series", "student information system"])
        secondary.extend(["grading workflows", "campus cohort", "coding contests"])
        aliases.extend(["lms", "college os"])
        
    # Classification
    domain_val = "SOLUTIONS" if type_val == "solution" else "PRODUCTS"
    
    migrated = {
        "uuid": generate_uuid(id_val),
        "id": id_val,
        "type": type_val,
        "slug": slug_val,
        "name": name,
        "title": name,
        "tagline": tagline,
        "overview": description,
        "description": description,
        "cta": cta,
        "url": data.get("route", f"/{type_val}s/{slug_val}"),
        "search": {
            "primary_keywords": list(set(primary)),
            "secondary_keywords": list(set(secondary)),
            "aliases": list(set(aliases)),
            "synonyms": synonyms
        },
        "classification": {
            "category": id_val,
            "industry": "Enterprise" if "enterprise" in id_val else "General",
            "domain": domain_val,
            "subdomain": None
        },
        "target_users": data.get("best_for", ["Admin", "User"]),
        "capabilities": capabilities_list,
        "workflows": workflow_list,
        "benefits": data.get("benefits", []),
        "use_cases": data.get("why_section", {}).get("pillars", []),
        "faq": data.get("faq", []),
        "relationships": [
            {"type": "recommended_with", "target": rel} for rel in data.get("related_entities", [])
        ],
        "metadata": {
            "schema_version": "2.0",
            "content_version": "1.0",
            "last_updated": "2026-07-19",
            "source": filename,
            "confidence": 1.0,
            "language": "en"
        }
    }
    
    with open(NEW_DIR / f"{type_val}_{slug_val.replace('-', '_')}.json", "w", encoding="utf-8") as out:
        json.dump(migrated, out, indent=2)
    print(f"  Migrated {filename} -> {type_val}_{slug_val.replace('-', '_')}.json")

def migrate_services():
    service_files = {
        "09_service_data_engineering.json": ("data_engineering", "data-engineering"),
        "10_service_enterprise_agentic_ai.json": ("enterprise_agentic_ai", "enterprise-agentic-ai"),
        "11_service_ai_strategy_advisory.json": ("ai_strategy", "ai-strategy"),
        "12_service_ai_powered_marketing.json": ("ai_powered_marketing", "ai-powered-marketing")
    }
    
    for filename, (id_val, slug_val) in service_files.items():
        file_path = REGISTRY_DIR / filename
        if not file_path.exists():
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        name = data.get("service_category", "").replace(" Solutions", "")
        cta = data.get("cta_section", {}).get("cta", "Book Now")
        overview = data.get("cta_section", {}).get("subheading", "")
        
        # Subservices map to Capabilities
        capabilities_list = []
        for service in data.get("services", []):
            title = service.get("title", "")
            cap_id = f"{id_val}_" + title.lower().replace("-", "_").replace(" ", "_").replace("/", "_").replace("&", "and")
            
            # Map key benefits to features or capability description
            features_list = []
            for feat in service.get("core_capabilities", []):
                feat_id = feat.lower().replace("-", "_").replace(" ", "_").replace("/", "_").replace("&", "and")[:50]
                features_list.append({
                    "id": feat_id,
                    "title": feat,
                    "description": f"Capability feature: {feat}"
                })
                
            benefits = [b.get("title") for b in service.get("key_benefits", [])]
            
            capabilities_list.append({
                "id": cap_id,
                "title": title,
                "subtitle": service.get("subtitle", ""),
                "description": service.get("overview", ""),
                "keywords": [w.lower() for w in title.split() if len(w) > 3],
                "aliases": [title.lower()],
                "features": features_list,
                "benefits": benefits,
                "relationships": []
            })
            
        primary = [name.lower()]
        secondary = [overview.lower()]
        aliases = [id_val, id_val.replace("_", "-"), id_val.replace("_", " ")]
        
        migrated = {
            "uuid": generate_uuid(id_val),
            "id": id_val,
            "type": "service",
            "slug": slug_val,
            "name": name,
            "title": name,
            "tagline": "Professional AI Services",
            "overview": overview,
            "description": overview,
            "cta": cta,
            "url": f"/services/{slug_val}",
            "search": {
                "primary_keywords": list(set(primary)),
                "secondary_keywords": list(set(secondary)),
                "aliases": list(set(aliases)),
                "synonyms": []
            },
            "classification": {
                "category": id_val,
                "industry": "Enterprise",
                "domain": "SERVICES",
                "subdomain": None
            },
            "target_users": ["CIO", "CTO", "Product Owners"],
            "capabilities": capabilities_list,
            "workflows": [],
            "benefits": [],
            "use_cases": [],
            "faq": [],
            "relationships": [],
            "metadata": {
                "schema_version": "2.0",
                "content_version": "1.0",
                "last_updated": "2026-07-19",
                "source": filename,
                "confidence": 1.0,
                "language": "en"
            }
        }
        
        with open(NEW_DIR / f"service_{slug_val.replace('-', '_')}.json", "w", encoding="utf-8") as out:
            json.dump(migrated, out, indent=2)
        print(f"  Migrated {filename} -> service_{slug_val.replace('-', '_')}.json")

def migrate_awards():
    file_path = REGISTRY_DIR / "13_awards_recognition.json"
    if not file_path.exists():
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    id_val = "awards_recognition"
    migrated = {
        "uuid": generate_uuid(id_val),
        "id": id_val,
        "type": "award",
        "slug": "recognition",
        "name": data.get("section_heading", "Awards & Recognition"),
        "title": data.get("section_heading", "Awards & Recognition"),
        "tagline": data.get("section_subheading", ""),
        "overview": data.get("description", ""),
        "description": data.get("description", ""),
        "cta": "View Awards",
        "url": "/recognition",
        "search": {
            "primary_keywords": ["awards", "recognition", "achievements"],
            "secondary_keywords": ["ap msme challenge", "hybiz tv", "innovation award"],
            "aliases": ["awards", "recognition", "awards_info"],
            "synonyms": ["accolades", "wins"]
        },
        "classification": {
            "category": "recognition",
            "industry": "AI & Tech Industry",
            "domain": "COMPANY_INFO",
            "subdomain": None
        },
        "target_users": ["Partners", "Clients", "Jury"],
        "capabilities": [
            {
                "id": award.get("award_group", "").lower().replace(" ", "_").replace("-", "_")[:50],
                "title": award.get("title", ""),
                "subtitle": award.get("award_group", ""),
                "description": award.get("description", ""),
                "keywords": ["award", "empowerment"],
                "aliases": [award.get("title", "").lower()],
                "features": [
                    {
                        "id": f"win_{idx}",
                        "title": win,
                        "description": f"Award victory details: {win}"
                    } for idx, win in enumerate(award.get("wins", []))
                ],
                "benefits": [award.get("closing_statement", "")],
                "relationships": []
            } for award in data.get("awards", [])
        ],
        "workflows": [],
        "benefits": [],
        "use_cases": [],
        "faq": [],
        "relationships": [],
        "metadata": {
            "schema_version": "2.0",
            "content_version": "1.0",
            "last_updated": "2026-07-19",
            "source": "13_awards_recognition.json",
            "confidence": 1.0,
            "language": "en"
        }
    }
    
    with open(NEW_DIR / "awards_recognition.json", "w", encoding="utf-8") as out:
        json.dump(migrated, out, indent=2)
    print("  Migrated 13_awards_recognition.json -> awards_recognition.json")

def migrate_company():
    file_path = REGISTRY_DIR / "14_about_cittaai.json"
    if not file_path.exists():
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    id_val = "company_info"
    
    capabilities_list = []
    # Add DNA as capabilities
    for dna in data.get("our_dna", {}).get("principles", []):
        capabilities_list.append({
            "id": dna.get("title", "").lower().replace(" ", "_"),
            "title": dna.get("title", ""),
            "subtitle": "",
            "description": dna.get("description", ""),
            "keywords": ["dna", "value"],
            "aliases": [dna.get("title", "").lower()],
            "features": [],
            "benefits": [],
            "relationships": []
        })
        
    migrated = {
        "uuid": generate_uuid(id_val),
        "id": id_val,
        "type": "company",
        "slug": "about",
        "name": "CittaAI",
        "title": data.get("section_heading", "About CittaAI"),
        "tagline": "Elevate. Innovate. Captivate.",
        "overview": data.get("description", ""),
        "description": data.get("description", ""),
        "cta": "Read More",
        "url": "/about",
        "search": {
            "primary_keywords": ["citta", "cittaai", "about company"],
            "secondary_keywords": ["enterprise ai", "consultancy", "who leads", "who founded"],
            "aliases": ["citta", "cittaai", "company", "about", "who_founded"],
            "synonyms": ["agency", "partner"]
        },
        "classification": {
            "category": "company",
            "industry": "AI Consulting",
            "domain": "COMPANY_INFO",
            "subdomain": None
        },
        "target_users": ["Enterprises", "Job Seekers", "Partners"],
        "capabilities": capabilities_list,
        "workflows": [],
        "benefits": [f"{p['title']}: {p['description']}" for p in data.get("why_enterprises_choose_us", {}).get("points", [])],
        "use_cases": [s.get("label", "") for s in data.get("stats", [])],
        "faq": [],
        "relationships": [],
        "metadata": {
            "schema_version": "2.0",
            "content_version": "1.0",
            "last_updated": "2026-07-19",
            "source": "14_about_cittaai.json",
            "confidence": 1.0,
            "language": "en"
        }
    }
    
    with open(NEW_DIR / "company_info.json", "w", encoding="utf-8") as out:
        json.dump(migrated, out, indent=2)
    print("  Migrated 14_about_cittaai.json -> company_info.json")

def migrate_case_studies():
    file_path = REGISTRY_DIR / "case_studies.json"
    if not file_path.exists():
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for idx, case in enumerate(data.get("entities", [])):
        id_val = case.get("id")
        title = case.get("title")
        slug_val = id_val.replace("_", "-")
        
        migrated = {
            "uuid": generate_uuid(id_val),
            "id": id_val,
            "type": "case_study",
            "slug": slug_val,
            "name": title,
            "title": title,
            "tagline": case.get("results", ""),
            "overview": case.get("challenge", ""),
            "description": case.get("solution", ""),
            "cta": "Read Case Study",
            "url": f"/case-studies/{slug_val}",
            "search": {
                "primary_keywords": [title.lower(), "case study"],
                "secondary_keywords": case.get("tags", []),
                "aliases": case.get("aliases", []),
                "synonyms": ["success story", "client project"]
            },
            "classification": {
                "category": "case_study",
                "industry": case.get("industry", ""),
                "domain": "CASE_STUDIES",
                "subdomain": None
            },
            "target_users": ["Sales Leads", "Clients"],
            "capabilities": [],
            "workflows": [],
            "benefits": case.get("metrics", []),
            "use_cases": case.get("tags", []),
            "faq": [],
            "relationships": [
                {"type": "related_service", "target": rel} for rel in case.get("related_entities", [])
            ],
            "metadata": {
                "schema_version": "2.0",
                "content_version": "1.0",
                "last_updated": "2026-07-19",
                "source": "case_studies.json",
                "confidence": 1.0,
                "language": "en"
            }
        }
        
        with open(NEW_DIR / f"case_study_{id_val}.json", "w", encoding="utf-8") as out:
            json.dump(migrated, out, indent=2)
        print(f"  Migrated case study entity {id_val} -> case_study_{id_val}.json")

def migrate_faq():
    file_path = REGISTRY_DIR / "faq.json"
    if not file_path.exists():
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    id_val = "faq_general"
    
    faq_items = []
    for entity in data.get("entities", []):
        faq_items.append({
            "question": entity.get("question"),
            "answer": entity.get("answer")
        })
        
    migrated = {
        "uuid": generate_uuid(id_val),
        "id": id_val,
        "type": "faq",
        "slug": "faq",
        "name": "General FAQ",
        "title": "Frequently Asked Questions",
        "tagline": "Find quick answers to common queries",
        "overview": "Frequently asked questions about CittaAI's platform, deployment, models, and licensing.",
        "description": "Frequently asked questions about CittaAI's platform, deployment, models, and licensing.",
        "cta": "Read FAQs",
        "url": "/faq",
        "search": {
            "primary_keywords": ["faq", "questions", "answers"],
            "secondary_keywords": ["pricing", "licensing", "deployment"],
            "aliases": ["faq", "help", "menu"],
            "synonyms": ["support", "qna"]
        },
        "classification": {
            "category": "faq",
            "industry": "All",
            "domain": "FAQ",
            "subdomain": None
        },
        "target_users": ["General Public", "Clients"],
        "capabilities": [],
        "workflows": [],
        "benefits": [],
        "use_cases": [],
        "faq": faq_items,
        "relationships": [],
        "metadata": {
            "schema_version": "2.0",
            "content_version": "1.0",
            "last_updated": "2026-07-19",
            "source": "faq.json",
            "confidence": 1.0,
            "language": "en"
        }
    }
    
    with open(NEW_DIR / "faq_general.json", "w", encoding="utf-8") as out:
        json.dump(migrated, out, indent=2)
    print("  Migrated faq.json -> faq_general.json")

def migrate_contact_location():
    contact_path = REGISTRY_DIR / "contact.json"
    location_path = REGISTRY_DIR / "location.json"
    
    if not contact_path.exists() or not location_path.exists():
        return
        
    with open(contact_path, "r", encoding="utf-8") as f:
        c_data = json.load(f)
    with open(location_path, "r", encoding="utf-8") as f:
        l_data = json.load(f)
        
    id_val = "contact_info"
    
    faq_items = [
        {"question": "What are your business hours?", "answer": c_data.get("business_hours", "")},
        {"question": "Where is your Hyderabad office?", "answer": l_data.get("address", "")}
    ]
    
    migrated = {
        "uuid": generate_uuid(id_val),
        "id": id_val,
        "type": "contact",
        "slug": "contact",
        "name": "Contact & Location Info",
        "title": "Contact Information",
        "tagline": "Get in touch with CittaAI solutions desk",
        "overview": f"Reach out via Email: {c_data.get('email')} or Phone: {c_data.get('phone')}.",
        "description": f"Located at: {l_data.get('address')}",
        "cta": "Get Support",
        "url": "/contact",
        "search": {
            "primary_keywords": ["contact", "email", "phone", "address"],
            "secondary_keywords": ["business hours", "office location", "maps link", "contact_info", "location_info"],
            "aliases": ["contact", "location", "office", "hq"],
            "synonyms": ["phone number", "email address", "support desk"]
        },
        "classification": {
            "category": "contact",
            "industry": "All",
            "domain": "CONTACT",
            "subdomain": None
        },
        "target_users": ["Clients", "Partners", "Inquirers"],
        "capabilities": [],
        "workflows": [],
        "benefits": [c_data.get("response_time", "")],
        "use_cases": [l_data.get("city", ""), l_data.get("country", "")],
        "faq": faq_items,
        "relationships": [],
        "metadata": {
            "schema_version": "2.0",
            "content_version": "1.0",
            "last_updated": "2026-07-19",
            "source": "contact.json, location.json",
            "confidence": 1.0,
            "language": "en"
        }
    }
    
    with open(NEW_DIR / "contact_info.json", "w", encoding="utf-8") as out:
        json.dump(migrated, out, indent=2)
    print("  Migrated contact.json & location.json -> contact_info.json")

def migrate_leadership():
    file_path = REGISTRY_DIR / "leadership.json"
    if not file_path.exists():
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    id_val = "leadership_info"
    
    capabilities_list = []
    # Core Leaders mapped to capabilities
    for leader in data.get("leaders", []):
        capabilities_list.append({
            "id": leader.get("id", "").lower().replace("-", "_"),
            "title": leader.get("name", ""),
            "subtitle": leader.get("title", ""),
            "description": f"Core executive leadership member.",
            "keywords": ["leader", "executive", leader.get("name", "").lower()],
            "aliases": leader.get("aliases", []),
            "features": [],
            "benefits": [],
            "relationships": []
        })
        
    for other in data.get("others", []):
        capabilities_list.append({
            "id": other.get("id", "").lower().replace("-", "_"),
            "title": other.get("name", ""),
            "subtitle": other.get("title", ""),
            "description": f"Functional leadership team member.",
            "keywords": ["leader", "functional", other.get("name", "").lower()],
            "aliases": other.get("aliases", []),
            "features": [],
            "benefits": [],
            "relationships": []
        })
        
    migrated = {
        "uuid": generate_uuid(id_val),
        "id": id_val,
        "type": "leadership",
        "slug": "leadership",
        "name": "Leadership Team",
        "title": "Executive Leadership",
        "tagline": "Innovators and experienced engineers",
        "overview": "Meet CittaAI's executive leadership and functional heads driving AI innovation.",
        "description": "Meet CittaAI's executive leadership and functional heads driving AI innovation.",
        "cta": "Meet the Team",
        "url": "/about",
        "search": {
            "primary_keywords": ["leadership", "leaders", "team", "who is the ceo"],
            "secondary_keywords": ["founders", "cto", "coo", "leadership_info"],
            "aliases": ["leaders", "team", "founder", "ceo", "cto", "coo"],
            "synonyms": ["founders", "management"]
        },
        "classification": {
            "category": "leadership",
            "industry": "All",
            "domain": "LEADERSHIP",
            "subdomain": None
        },
        "target_users": ["Investors", "Clients", "Partners"],
        "capabilities": capabilities_list,
        "workflows": [],
        "benefits": [],
        "use_cases": [],
        "faq": [],
        "relationships": [],
        "metadata": {
            "schema_version": "2.0",
            "content_version": "1.0",
            "last_updated": "2026-07-19",
            "source": "leadership.json",
            "confidence": 1.0,
            "language": "en"
        }
    }
    
    with open(NEW_DIR / "leadership_info.json", "w", encoding="utf-8") as out:
        json.dump(migrated, out, indent=2)
    print("  Migrated leadership.json -> leadership_info.json")

def generate_manifest():
    manifest_data = {
        "registries": [
            {"name": "company_info", "enabled": True, "priority": 95, "registry_id": "company_info_v2", "registry_type": "COMPANY_INFO", "content": "new/company_info.json"},
            {"name": "product_whatsapp_marketing", "enabled": True, "priority": 90, "registry_id": "whatsapp_marketing_v2", "registry_type": "PRODUCTS", "content": "new/product_whatsapp_marketing.json"},
            {"name": "product_influencer_marketing", "enabled": True, "priority": 90, "registry_id": "influencer_marketing_v2", "registry_type": "PRODUCTS", "content": "new/product_influencer_marketing.json"},
            {"name": "solution_ecommerce_os", "enabled": True, "priority": 85, "registry_id": "ecommerce_os_v2", "registry_type": "SOLUTIONS", "content": "new/solution_ecommerce_os.json"},
            {"name": "solution_real_estate_os", "enabled": True, "priority": 85, "registry_id": "real_estate_os_v2", "registry_type": "SOLUTIONS", "content": "new/solution_real_estate_os.json"},
            {"name": "solution_pharma_os", "enabled": True, "priority": 85, "registry_id": "pharma_os_v2", "registry_type": "SOLUTIONS", "content": "new/solution_pharma_os.json"},
            {"name": "solution_smart_cities_os", "enabled": True, "priority": 85, "registry_id": "smart_cities_os_v2", "registry_type": "SOLUTIONS", "content": "new/solution_smart_cities_os.json"},
            {"name": "solution_education_os", "enabled": True, "priority": 85, "registry_id": "education_os_v2", "registry_type": "SOLUTIONS", "content": "new/solution_education_os.json"},
            {"name": "solution_enterprise_ai_os", "enabled": True, "priority": 85, "registry_id": "enterprise_ai_os_v2", "registry_type": "SOLUTIONS", "content": "new/solution_enterprise_ai_os.json"},
            {"name": "service_data_engineering", "enabled": True, "priority": 80, "registry_id": "data_engineering_v2", "registry_type": "SERVICES", "content": "new/service_data_engineering.json"},
            {"name": "service_enterprise_agentic_ai", "enabled": True, "priority": 80, "registry_id": "enterprise_agentic_ai_v2", "registry_type": "SERVICES", "content": "new/service_enterprise_agentic_ai.json"},
            {"name": "service_ai_strategy", "enabled": True, "priority": 80, "registry_id": "ai_strategy_v2", "registry_type": "SERVICES", "content": "new/service_ai_strategy.json"},
            {"name": "service_ai_powered_marketing", "enabled": True, "priority": 80, "registry_id": "ai_powered_marketing_v2", "registry_type": "SERVICES", "content": "new/service_ai_powered_marketing.json"},
            {"name": "awards_recognition", "enabled": True, "priority": 75, "registry_id": "awards_recognition_v2", "registry_type": "RECOGNITION", "content": "new/awards_recognition.json"},
            {"name": "leadership_info", "enabled": True, "priority": 75, "registry_id": "leadership_info_v2", "registry_type": "LEADERSHIP", "content": "new/leadership_info.json"},
            {"name": "contact_info", "enabled": True, "priority": 70, "registry_id": "contact_info_v2", "registry_type": "CONTACT", "content": "new/contact_info.json"},
            {"name": "faq_general", "enabled": True, "priority": 65, "registry_id": "faq_general_v2", "registry_type": "FAQ", "content": "new/faq_general.json"},
            {"name": "case_study_jewellery_brand_roi", "enabled": True, "priority": 60, "registry_id": "case_study_jewellery_v2", "registry_type": "CASE_STUDIES", "content": "new/case_study_jewellery_brand_roi.json"},
            {"name": "case_study_fmcg_social_growth", "enabled": True, "priority": 60, "registry_id": "case_study_fmcg_v2", "registry_type": "CASE_STUDIES", "content": "new/case_study_fmcg_social_growth.json"},
            {"name": "case_study_b2b_spices_export", "enabled": True, "priority": 60, "registry_id": "case_study_spices_v2", "registry_type": "CASE_STUDIES", "content": "new/case_study_b2b_spices_export.json"}
        ],
        "metadata": {
            "schema_version": "2.0",
            "content_version": "1.0",
            "last_updated": "2026-07-19"
        }
    }
    
    with open(REGISTRY_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print("Generated manifest.json pointing to 'new/' files.")

def main():
    print("================ KNOWLEDGE REGISTRY MIGRATION PIPELINE ================")
    # Restore from old/ if files are missing in root for migration continuity
    if OLD_DIR.exists():
        for f in OLD_DIR.glob("*.json"):
            shutil.copy2(f, REGISTRY_DIR / f.name)
            
    backup_files()
    
    # Products
    migrate_product_solution("01_product_whatsapp_marketing_platform.json", "whatsapp_marketing", "product", "whatsapp-marketing")
    migrate_product_solution("02_product_influencer_marketing_platform.json", "influencer_marketing", "product", "influencer-marketing")
    
    # Solutions
    migrate_product_solution("03_product_ecommerce_os.json", "ecommerce_os", "solution", "ecommerce-os")
    migrate_product_solution("04_product_real_estate_os.json", "real_estate_os", "solution", "real-estate-os")
    migrate_product_solution("05_product_pharma_os.json", "pharma_os", "solution", "pharma-os")
    migrate_product_solution("06_product_smart_cities_os.json", "smart_cities_os", "solution", "smart-cities-os")
    migrate_product_solution("07_product_education_os.json", "education_os", "solution", "education-os")
    migrate_product_solution("08_product_enterprise_ai_os.json", "enterprise_ai_os", "solution", "enterprise-ai-os")
    
    # Services
    migrate_services()
    
    # Rest
    migrate_awards()
    migrate_company()
    migrate_case_studies()
    migrate_faq()
    migrate_contact_location()
    migrate_leadership()
    
    # Manifest
    generate_manifest()
    
    # Clean up the root registry folder so only manifest.json, old, new exist
    for f in REGISTRY_DIR.glob("*.json"):
        if f.name != "manifest.json":
            try:
                f.unlink()
            except Exception:
                pass
                
    print("================ MIGRATION PIPELINE COMPLETE ================")

if __name__ == "__main__":
    main()
