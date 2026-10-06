import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent
COMPILED_DIR = BACKEND_DIR / "knowledge" / "compiled"

class KnowledgeRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KnowledgeRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.registry_index: Dict[str, Dict[str, Any]] = {}
        self.disabled_registries: Set[str] = set()
        
        self.company: Dict[str, Any] = {}
        self.products: List[Dict[str, Any]] = []
        self.services: List[Dict[str, Any]] = []
        self.solutions: List[Dict[str, Any]] = []
        
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.routes: Dict[str, str] = {}  # route -> entity_id
        self.aliases: Dict[str, str] = {}  # alias -> entity_id
        self.abbreviations: Dict[str, str] = {} # abbr -> expansion
        self.unified_vocabulary: Dict[str, str] = {} # token -> entity_id
        self.entity_lookup: Dict[str, str] = {} # Single canonical runtime lookup map
        self.knowledge_graph: Dict[str, Dict[str, Any]] = {}
        
        self._initialized = True
        self.load_all()

    def load_all(self):
        logger.info("Initializing CittaAI Enterprise Knowledge Registry Loader...")
        self.registry_index = {}
        self.disabled_registries = set()
        self.entities = {}
        self.routes = {}
        self.aliases = {}
        self.abbreviations = {}
        self.unified_vocabulary = {}
        self.entity_lookup = {}
        
        # New indexing structures
        self.registry_by_id = {}
        self.registry_by_slug = {}
        self.registry_by_keyword = {}
        self.registry_by_alias = {}
        self.registry_by_capability = {}
        self.registry_by_feature = {}
        self.registry_by_category = {}
        self.registry_by_industry = {}
        self.registry_by_type = {}
        
        REGISTRY_DIR = BACKEND_DIR / "knowledge" / "registry"
        manifest_path = REGISTRY_DIR / "manifest.json"
        
        if not manifest_path.exists():
            logger.error(f"Global manifest.json not found at {manifest_path}. Loading fallbacks.")
            self._load_fallbacks()
            return

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read manifest.json: {e}. Loading fallbacks.")
            self._load_fallbacks()
            return

        registries = manifest_data.get("registries", [])
        # Sort by priority descending
        registries.sort(key=lambda x: x.get("priority", 0), reverse=True)

        import knowledge_validator
        loaded_objects = []

        for reg_conf in registries:
            name = reg_conf.get("name")
            enabled = reg_conf.get("enabled", True)
            content_file = reg_conf.get("content")
            
            if not enabled:
                continue

            file_path = REGISTRY_DIR / content_file
            if not file_path.exists():
                logger.error(f"Registry content file {content_file} missing. Fail-fast active.")
                raise FileNotFoundError(f"Required registry file missing: {content_file}")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    reg_data = json.load(f)
                
                # Strict Schema Validation
                obj = knowledge_validator.validate_object(reg_data, filename=content_file)
                loaded_objects.append(obj)
                
                # Cache registry_index to mimic old format if needed
                self.registry_index[reg_conf.get("registry_type")] = reg_data
            except Exception as e:
                logger.error(f"Registry Startup Validation Failed for '{content_file}': {e}.")
                raise ValueError(f"Startup validation failed for '{content_file}': {e}")

        # Run global referential and uniqueness checks
        try:
            knowledge_validator.validate_global_registry(loaded_objects)
        except Exception as e:
            logger.error(f"Global Registry Quality check failed: {e}")
            raise ValueError(f"Startup global quality validation failed: {e}")

        # Build new structural indexes
        for obj in loaded_objects:
            self.registry_by_id[obj.id] = obj
            self.registry_by_slug[obj.slug] = obj
            self.registry_by_type.setdefault(obj.type.value, []).append(obj)
            self.registry_by_category.setdefault(obj.classification.category, []).append(obj)
            self.registry_by_industry.setdefault(obj.classification.industry, []).append(obj)
            
            for kw in obj.search.primary_keywords:
                self.registry_by_keyword.setdefault(kw.lower(), []).append(obj)
            for kw in obj.search.secondary_keywords:
                self.registry_by_keyword.setdefault(kw.lower(), []).append(obj)
                
            for alias in obj.search.aliases:
                self.registry_by_alias.setdefault(alias.lower(), []).append(obj)
            for syn in obj.search.synonyms:
                self.registry_by_alias.setdefault(syn.lower(), []).append(obj)
                
            for cap in obj.capabilities:
                cap_entry = {"capability": cap, "parent": obj}
                self.registry_by_capability[cap.id] = cap_entry
                self.registry_by_capability[cap.title.lower()] = cap_entry
                for kw in cap.keywords:
                    if (len(kw.split()) >= 2 or len(kw) > 12) and kw.lower() not in ["strategy", "marketing", "data", "design", "analytics", "systems", "communication", "management"]:
                        self.registry_by_capability[kw.lower()] = cap_entry
                for alias in cap.aliases:
                    if (len(alias.split()) >= 2 or len(alias) > 12) and alias.lower() not in ["communication", "strategy", "marketing", "data", "design", "analytics", "systems"]:
                        self.registry_by_capability[alias.lower()] = cap_entry
                    
                for feat in cap.features:
                    feat_entry = {"feature": feat, "capability": cap, "parent": obj}
                    self.registry_by_feature[feat.id] = feat_entry
                    self.registry_by_feature[feat.title.lower()] = feat_entry
                    for kw in feat.keywords:
                        self.registry_by_feature[kw.lower()] = feat_entry

        # Populate legacy properties for backward compatibility
        self._populate_legacy_properties()
        
        # Build unified indexing structures
        self.build_entities()
        self.load_routes()
        self.load_aliases()
        self.build_unified_vocabulary()
        self.build_entity_lookup()
        self.build_knowledge_graph()
        self.validate()
        self.print_diagnostics()

    def _load_fallbacks(self):
        # Fallback dictionary for basic server survival if compilation is broken
        self.company = {
            "name": "CittaAI",
            "tagline": "Living Intelligence",
            "founded": "2022",
            "description": "Enterprise AI partner."
        }
        self.build_entities()

    def _to_legacy_dict(self, obj) -> Dict[str, Any]:
        return {
            "id": obj.id,
            "name": obj.name,
            "title": obj.title,
            "tagline": obj.tagline,
            "description": obj.description,
            "best_for": obj.target_users,
            "route": obj.url,
            "cta": obj.cta,
            "benefits": obj.benefits,
            "faq": [{"question": f.question, "answer": f.answer} for f in obj.faq],
            "related_entities": [r.target for r in obj.relationships],
            "capabilities": [
                {
                    "title": cap.title,
                    "subtitle": cap.subtitle,
                    "description": cap.description,
                    "features": [f.title for f in cap.features]
                } for cap in obj.capabilities
            ],
            "how_it_works": {
                "steps": [f"{w.title}: {w.description}" if w.description else w.title for w in obj.workflows]
            },
            "workflows": [
                {"step": w.step, "title": w.title, "description": w.description}
                for w in obj.workflows
            ]
        }

    def _clean_key(self, text: str) -> str:
        if not text:
            return ""
        val = str(text).lower().strip()
        val = re.sub(r"[^\w\s\-\/]", "", val)
        val = re.sub(r"\s+", " ", val).strip()
        return val

    def _populate_legacy_properties(self):
        # company
        company_obj = self.registry_by_id.get("company_info")
        if company_obj:
            self.company = {
                "name": company_obj.name,
                "tagline": company_obj.tagline,
                "founded": "2022",
                "description": company_obj.description,
                "vision": "Empower global enterprises with autonomous cognitive operating systems.",
                "mission": "Bridge research-grade AI to enterprise scale with security, governance, and measurable ROI.",
                "ceo": "Akhil Reddy"
            }
        
        # products
        self.products = [self._to_legacy_dict(obj) for obj in self.registry_by_type.get("product", [])]
        
        # services
        self.services = [self._to_legacy_dict(obj) for obj in self.registry_by_type.get("service", [])]
        
        # solutions
        self.solutions = [self._to_legacy_dict(obj) for obj in self.registry_by_type.get("solution", [])]
        
        # case studies
        cs_entities = [self._to_legacy_dict(obj) for obj in self.registry_by_type.get("case_study", [])]
        
        meta_base = {
            "registry_id": "v1",
            "registry_type": "GENERIC",
            "schema_version": "2.0",
            "content_version": "1.0",
            "priority": 80,
            "capabilities": {"reasoning": True, "comparison": True, "transformation": True, "summarization": True, "examples": True},
            "supported_sections": ["overview", "capabilities", "features", "workflows", "benefits", "use_cases", "faq"]
        }
        
        self.registry_index["COMPANY_INFO"] = {"metadata": {**meta_base, "registry_type": "COMPANY_INFO", "registry_id": "company_v1"}, **self.company}
        self.registry_index["PRODUCTS"] = {"metadata": {**meta_base, "registry_type": "PRODUCTS", "registry_id": "products_v1"}, "entities": self.products}
        self.registry_index["SERVICES"] = {"metadata": {**meta_base, "registry_type": "SERVICES", "registry_id": "services_v1"}, "entities": self.services}
        self.registry_index["SOLUTIONS"] = {"metadata": {**meta_base, "registry_type": "SOLUTIONS", "registry_id": "solutions_v1"}, "entities": self.solutions}
        self.registry_index["CASE_STUDIES"] = {"metadata": {**meta_base, "registry_type": "CASE_STUDIES", "registry_id": "case_studies_v1"}, "entities": cs_entities}
        
        # Leadership index
        leaders = []
        others = []
        lead_obj = self.registry_by_id.get("leadership_info")
        if lead_obj:
            for cap in lead_obj.capabilities:
                item = {
                    "id": cap.id,
                    "name": cap.title,
                    "title": cap.subtitle,
                    "description": cap.description,
                    "aliases": cap.aliases
                }
                if any(r in cap.subtitle.lower() for r in ["ceo", "co-founder", "co_founder", "cto", "coo"]):
                    leaders.append(item)
                else:
                    others.append(item)
        self.registry_index["LEADERSHIP"] = {"metadata": {**meta_base, "registry_type": "LEADERSHIP", "registry_id": "leadership_v1"}, "leaders": leaders, "others": others}
        
        # Recognition index
        rec_obj = self.registry_by_id.get("awards_recognition")
        recognitions = []
        if rec_obj:
            for cap in rec_obj.capabilities:
                recognitions.append({
                    "title": cap.title,
                    "description": cap.description,
                    "details": cap.subtitle,
                    "organization": cap.subtitle
                })
        self.registry_index["RECOGNITION"] = {"metadata": {**meta_base, "registry_type": "RECOGNITION", "registry_id": "recognition_v1"}, "recognitions": recognitions}
        
        # Contact index
        contact_obj = self.registry_by_id.get("contact_info")
        if contact_obj:
            self.registry_index["CONTACT"] = {
                "metadata": {**meta_base, "registry_type": "CONTACT", "registry_id": "contact_v1"},
                "phone": "+91 9392655040",
                "phone_raw": "+919392655040",
                "email": "info@cittaai.com",
                "business_hours": "Mon-Fri 9am-6pm",
                "response_time": "We typically respond within 24 hours during business hours."
            }
            
        # FAQ index
        faq_obj = self.registry_by_id.get("faq_general")
        faqs = []
        if faq_obj:
            for f in faq_obj.faq:
                faqs.append({"question": f.question, "answer": f.answer, "route": "/faq"})
        self.registry_index["FAQ"] = {"metadata": {**meta_base, "registry_type": "FAQ", "registry_id": "faq_v1"}, "entities": faqs}

    def build_entities(self):
        self.entities = {}
        
        # 1. Add Company entity
        company_obj = self.registry_by_id.get("company_info")
        if company_obj:
            self.entities["company_info"] = {
                "id": "company_info",
                "type": "company",
                "name": company_obj.name,
                "title": company_obj.title,
                "tagline": company_obj.tagline,
                "description": company_obj.description,
                "route": company_obj.url or "/about"
            }
            
        # 2. Add Products, Services, Solutions
        for obj in self.registry_by_id.values():
            if obj.type.value in ["product", "service", "solution", "case_study"]:
                self.entities[obj.id] = self._to_legacy_dict(obj)
                self.entities[obj.id]["type"] = obj.type.value

        # 3. Add Leadership members
        lead_obj = self.registry_by_id.get("leadership_info")
        
        if your_lead_obj := lead_obj:
            self.entities["leadership_info"] = {
                "id": "leadership_info",
                "type": "leadership",
                "name": your_lead_obj.name,
                "title": your_lead_obj.title,
                "tagline": your_lead_obj.tagline,
                "description": your_lead_obj.description,
                "route": your_lead_obj.url or "/about"
            }
            for member in your_lead_obj.capabilities:
                m_id = member.id
                self.entities[m_id] = {
                    "id": m_id,
                    "name": member.title,
                    "title": member.subtitle,
                    "description": member.description or "",
                    "aliases": member.aliases or [],
                    "type": "leadership",
                    "route": "/about"
                }

        # 4. Add contact_info
        contact_obj = self.registry_by_id.get("contact_info")
        if contact_obj:
            self.entities["contact_info"] = self._to_legacy_dict(contact_obj)
            self.entities["contact_info"]["type"] = "contact"

        # 5. Add awards_recognition
        rec_obj = self.registry_by_id.get("awards_recognition")
        if rec_obj:
            self.entities["awards_recognition"] = self._to_legacy_dict(rec_obj)
            self.entities["awards_recognition"]["type"] = "award"

        # 6. Add faq_general
        faq_obj = self.registry_by_id.get("faq_general")
        if faq_obj:
            self.entities["faq_general"] = self._to_legacy_dict(faq_obj)
            self.entities["faq_general"]["type"] = "faq"

    def load_routes(self):
        self.routes = {}
        for ent_id, ent in self.entities.items():
            route = ent.get("route")
            if route:
                self.routes[route] = ent_id

    def load_aliases(self):
        self.aliases = {}
        self.alias_lookup = {}
        self.slug_lookup = {}
        self.keyword_lookup = {}
        
        for obj in self.registry_by_id.values():
            ent_id = obj.id
            
            # Map search aliases & synonyms
            search_data = getattr(obj, "search", None)
            if search_data:
                for alias in search_data.aliases:
                    a_clean = self._clean_key(alias)
                    self.alias_lookup[a_clean] = ent_id
                    self.aliases[a_clean] = ent_id
                for syn in search_data.synonyms:
                    a_clean = self._clean_key(syn)
                    self.alias_lookup[a_clean] = ent_id
                    self.aliases[a_clean] = ent_id
                for kw in search_data.primary_keywords:
                    clean_kw = self._clean_key(kw)
                    self.keyword_lookup[clean_kw] = ent_id
                    self.alias_lookup[clean_kw] = ent_id
                for kw in search_data.secondary_keywords:
                    self.keyword_lookup[self._clean_key(kw)] = ent_id
            
            # Map slug
            slug_val = getattr(obj, "slug", None)
            if slug_val:
                self.slug_lookup[self._clean_key(slug_val)] = ent_id
                
            # Parse capability-level keywords & aliases
            caps = getattr(obj, "capabilities", [])
            for cap in caps:
                for alias in getattr(cap, "aliases", []):
                    a_clean = self._clean_key(alias)
                    self.alias_lookup[a_clean] = ent_id
                    self.aliases[a_clean] = ent_id
                for kw in getattr(cap, "keywords", []):
                    self.keyword_lookup[self._clean_key(kw)] = ent_id
                for feat in getattr(cap, "features", []):
                    for kw in getattr(feat, "keywords", []):
                        self.keyword_lookup[self._clean_key(kw)] = ent_id

        # Also map leadership members
        lead_obj = self.registry_by_id.get("leadership_info")
        if your_lead_obj := lead_obj:
            for member in your_lead_obj.capabilities:
                m_id = member.id
                for alias in member.aliases or []:
                    a_clean = self._clean_key(alias)
                    self.alias_lookup[a_clean] = m_id
                    self.aliases[a_clean] = m_id

        # Inject default fallback/convenience aliases dynamically
        # mapping to their canonical IDs
        self.aliases[self._clean_key("cittaai")] = "company_info"
        self.aliases[self._clean_key("citta")] = "company_info"
        self.aliases[self._clean_key("company")] = "company_info"
        # Akhil Reddy is CEO (owner-confirmed, matches cittaai.com); no CTO or sole founder is published
        self.aliases[self._clean_key("founder")] = "leadership_info"
        self.aliases[self._clean_key("ceo")] = "akhil_reddy"
        self.aliases[self._clean_key("coo")] = "saladi_chandra_balaji"
        self.aliases[self._clean_key("vinay velivela")] = "vinay_velivela"
        self.aliases[self._clean_key("vinay")] = "vinay_velivela"
        self.aliases[self._clean_key("akhil")] = "akhil_reddy"
        self.aliases[self._clean_key("balaji")] = "saladi_chandra_balaji"

        # Domain concept mappings for solutions & products
        domain_mappings = {
            "martech_360": ["martech 360", "martech-360", "martech 3600", "martech3600", "martech", "martech 360 service", "branding & strategy", "branding strategy", "ai brand architecture & strategy engine", "ai brand architecture and strategy engine", "ai-powered marketing solutions", "ai powered marketing solutions"],
            # hospital/clinic/medical terms removed 2026-09-29: Pharma OS content is pharma QA/compliance only
            # (see metadata.content_decisions in knowledge/registry/new/solution_pharma_os.json)
            "pharma_os": ["pharma", "pharmaceutical", "pharmaceuticals", "healthcare os", "healthcare", "health care", "health care os", "health care sector", "healthcare sector", "health care industry", "healthcare industry"],
            "education_os": ["education", "college", "colleges", "institute", "institutes", "institution", "institutions", "university", "universities", "school", "schools", "academic", "academics", "edtech"],
            "real_estate_os": ["real estate os", "realestate os", "construction", "property", "properties", "realty", "builder", "builders", "broker", "brokers", "housing"],
            "ecommerce_os": ["ecommerce", "e-commerce", "retail", "retailers", "online store", "shopping", "merchant", "merchants"],
            "smart_cities_os": ["smart cities", "smart city", "urban", "municipality", "municipalities", "city management", "city planning"],
            "enterprise_ai_os": ["enterprise ai", "ai os", "ai platform", "ai middleware", "ai infrastructure", "agentic ai"]
        }
        for ent_id, keywords in domain_mappings.items():
            for kw in keywords:
                k_clean = self._clean_key(kw)
                self.aliases[k_clean] = ent_id
                self.alias_lookup[k_clean] = ent_id
                self.keyword_lookup[k_clean] = ent_id

        # Apply same injects to alias_lookup
        for k, v in self.aliases.items():
            self.alias_lookup[k] = v

    def build_unified_vocabulary(self):
        self.unified_vocabulary = {}
        self.abbreviations = {}
        
        # 1. Map canonical IDs
        for ent_id in self.entities.keys():
            self.unified_vocabulary[self._clean_key(ent_id.replace("_", " "))] = ent_id
            self.unified_vocabulary[self._clean_key(ent_id)] = ent_id
            
        # 2. Map direct entity names & titles
        for ent_id, ent in self.entities.items():
            name = ent.get("name")
            if name:
                self.unified_vocabulary[self._clean_key(name)] = ent_id
            title = ent.get("title")
            if title:
                self.unified_vocabulary[self._clean_key(title)] = ent_id

        # 3. Map registry aliases, slugs, and keywords
        for k, v in self.alias_lookup.items():
            self.unified_vocabulary[self._clean_key(k)] = v
        for k, v in self.slug_lookup.items():
            self.unified_vocabulary[self._clean_key(k)] = v
        for k, v in self.keyword_lookup.items():
            self.unified_vocabulary[self._clean_key(k)] = v

        # 4. Map static abbreviations and registry aliases from metadata
        for reg_type, reg in self.registry_index.items():
            meta = reg.get("metadata", {})
            abbs = meta.get("abbreviations", {})
            self.abbreviations.update(abbs)
            
            for alias in meta.get("aliases", []):
                alias_clean = self._clean_key(alias)
                if alias_clean not in self.unified_vocabulary:
                    self.unified_vocabulary[alias_clean] = reg_type
            
            for kw in meta.get("keywords", []):
                kw_clean = self._clean_key(kw)
                if kw_clean not in self.unified_vocabulary:
                    self.unified_vocabulary[kw_clean] = reg_type.lower()

        self.unified_vocabulary[self._clean_key("data engineering")] = "data_engineering"
        self.unified_vocabulary[self._clean_key("enterprise & agentic ai")] = "enterprise_agentic_ai"
        self.unified_vocabulary[self._clean_key("ai strategy & advisory")] = "ai_strategy"
        self.unified_vocabulary[self._clean_key("ai-powered marketing")] = "ai_powered_marketing"
        self.unified_vocabulary[self._clean_key("wa")] = "whatsapp_marketing"
        self.unified_vocabulary[self._clean_key("whatsapp")] = "whatsapp_marketing"
        self.unified_vocabulary[self._clean_key("influencer")] = "influencer_marketing"
        self.unified_vocabulary[self._clean_key("e-commerce")] = "ecommerce_os"
        self.unified_vocabulary[self._clean_key("ecommerce")] = "ecommerce_os"
        self.unified_vocabulary[self._clean_key("pharma")] = "pharma_os"
        self.unified_vocabulary[self._clean_key("healthcare")] = "pharma_os"
        self.unified_vocabulary[self._clean_key("health care")] = "pharma_os"
        self.unified_vocabulary[self._clean_key("health care os")] = "pharma_os"
        self.unified_vocabulary[self._clean_key("smart city")] = "smart_cities_os"
        self.unified_vocabulary[self._clean_key("smart cities")] = "smart_cities_os"
        self.unified_vocabulary[self._clean_key("smart cities services")] = "smart_cities_os"
        self.unified_vocabulary[self._clean_key("smart city services")] = "smart_cities_os"
        self.unified_vocabulary[self._clean_key("smart cities platform")] = "smart_cities_os"
        self.unified_vocabulary[self._clean_key("education")] = "education_os"
        self.unified_vocabulary[self._clean_key("education services")] = "education_os"
        self.unified_vocabulary[self._clean_key("real estate")] = "real_estate_os"
        self.unified_vocabulary[self._clean_key("ai os")] = "enterprise_ai_os"
        self.unified_vocabulary[self._clean_key("enterprise ai")] = "enterprise_ai_os"

        self.abbreviations["wa"] = "whatsapp_marketing"
        self.abbreviations["ecommerce"] = "ecommerce_os"
        self.abbreviations["pharma"] = "pharma_os"

    def build_entity_lookup(self):
        self.entity_lookup = {}
        
        # 1. Canonical IDs and Entity Names
        for ent_id, ent in self.entities.items():
            self.entity_lookup[self._clean_key(ent_id)] = ent_id
            self.entity_lookup[self._clean_key(ent_id.replace("_", " "))] = ent_id
            name = ent.get("name") or ent.get("title")
            if name:
                self.entity_lookup[self._clean_key(name)] = ent_id

        # 2. Entity Aliases (from individual entity data)
        for ent_id, ent in self.entities.items():
            aliases = ent.get("aliases", [])
            for alias in aliases:
                alias_clean = self._clean_key(alias)
                if alias_clean and alias_clean not in self.entity_lookup:
                    self.entity_lookup[alias_clean] = ent_id

        # 3. Merging alias_lookup (from load_aliases)
        for alias, ent_id in self.alias_lookup.items():
            alias_clean = self._clean_key(alias)
            if alias_clean and ent_id in self.entities:
                if alias_clean not in self.entity_lookup:
                    self.entity_lookup[alias_clean] = ent_id

        self.entity_lookup[self._clean_key("data engineering")] = "data_engineering"
        self.entity_lookup[self._clean_key("enterprise & agentic ai")] = "enterprise_agentic_ai"
        self.entity_lookup[self._clean_key("enterprise agentic ai")] = "enterprise_agentic_ai"
        self.entity_lookup[self._clean_key("ai strategy & advisory")] = "ai_strategy"
        self.entity_lookup[self._clean_key("ai strategy")] = "ai_strategy"
        self.entity_lookup[self._clean_key("ai-powered marketing")] = "ai_powered_marketing"

    def build_knowledge_graph(self):
        self.knowledge_graph = {}
        
        type_to_registry = {
            "product": "PRODUCTS",
            "service": "SERVICES",
            "solution": "SOLUTIONS",
            "company": "COMPANY_INFO",
            "leadership": "LEADERSHIP",
            "case_study": "CASE_STUDIES",
            "award": "RECOGNITION",
            "faq": "FAQ",
            "contact": "CONTACT"
        }
        
        for ent_id, ent in self.entities.items():
            ent_type = ent.get("type", "UNKNOWN")
            belongs_to = type_to_registry.get(ent_type, "UNKNOWN")
            
            # Retrieve from registry_by_id if it exists to get relationships/depends_on/etc
            reg_obj = self.registry_by_id.get(ent_id)
            related_entities = []
            depends_on = []
            if reg_obj:
                related_entities = [r.target for r in reg_obj.relationships]
                depends_on = getattr(reg_obj, "depends_on", [])
                
            self.knowledge_graph[ent_id] = {
                "id": ent_id,
                "name": ent.get("name") or ent.get("title") or ent_id,
                "belongs_to": belongs_to,
                "related_entities": related_entities or ent.get("related_entities", []),
                "case_studies": [],
                "technologies": ent.get("technologies", []),
                "integrations": ent.get("integrations", []),
                "depends_on": depends_on or ent.get("depends_on", [])
            }

        # Back-populate case study links
        cs_reg = self.registry_index.get("CASE_STUDIES", {})
        if cs_reg:
            for cs in cs_reg.get("entities", []):
                cs_id = cs.get("id")
                related = cs.get("related_entities", [])
                for rel_id in related:
                    if rel_id in self.knowledge_graph:
                        self.knowledge_graph[rel_id]["case_studies"].append(cs_id)

    def validate(self):
        # 1. No duplicate IDs check (Fatal)
        id_counts = {}
        for obj in self.registry_by_id.values():
            id_counts[obj.id] = id_counts.get(obj.id, 0) + 1
        duplicates = [k for k, v in id_counts.items() if v > 1]
        if duplicates:
            raise ValueError(f"[Fatal Validation Error] Duplicate Entity IDs detected in registry loading: {duplicates}")

        # 2. Every belongs_to registry exists (Fatal)
        valid_registries = {"PRODUCTS", "SERVICES", "SOLUTIONS", "COMPANY_INFO", "LEADERSHIP", "RECOGNITION", "CONTACT", "FAQ", "CASE_STUDIES"}
        for ent_id, node in self.knowledge_graph.items():
            belongs_to = node.get("belongs_to")
            if belongs_to not in valid_registries:
                raise ValueError(f"[Fatal Validation Error] Entity '{ent_id}' belongs to invalid registry: '{belongs_to}'")

        # 3. Every related entity exists (Fatal)
        for ent_id, ent in self.entities.items():
            related = ent.get("related_entities", [])
            for rel in related:
                if rel not in self.entities and rel not in self.registry_by_id:
                    raise ValueError(f"[Fatal Validation Error] Entity '{ent_id}' references missing related entity: '{rel}'")

        # 4. Every knowledge graph node exists (Fatal)
        for node_id in self.knowledge_graph.keys():
            if node_id not in self.entities:
                raise ValueError(f"[Fatal Validation Error] Knowledge graph node '{node_id}' does not exist in entities list.")

        # 5. Every alias points to existing entity (Fatal)
        for alias, ent_id in self.alias_lookup.items():
            if ent_id not in self.entities:
                raise ValueError(f"[Fatal Validation Error] Alias '{alias}' points to missing entity ID: '{ent_id}'")

        # 6. Check duplicate aliases (Warning, not fatal)
        alias_to_ids = {}
        for alias, ent_id in self.alias_lookup.items():
            alias_to_ids.setdefault(alias, set()).add(ent_id)
        duplicate_aliases = {k: list(v) for k, v in alias_to_ids.items() if len(v) > 1}
        if duplicate_aliases:
            logger.warning(f"[Validation Warning] Duplicate aliases detected: {duplicate_aliases}")

        # 7. Consistency Cross-Check: every entity in entities has lookup and KG node, is resolvable
        for ent_id, ent in self.entities.items():
            name = ent.get("name") or ent.get("title")
            if name:
                name_clean = name.lower().strip()
                # Ensure either the ID or the name is resolvable
                if name_clean not in self.entity_lookup and ent_id.lower() not in self.entity_lookup:
                    raise ValueError(f"[Fatal Validation Error] Entity '{ent_id}' is not resolvable by ID or name '{name}' in entity_lookup.")
            if ent_id not in self.knowledge_graph:
                raise ValueError(f"[Fatal Validation Error] Entity '{ent_id}' is missing from the knowledge_graph node list.")

    def print_diagnostics(self):
        try:
            # Manifest hash
            REGISTRY_DIR = BACKEND_DIR / "knowledge" / "registry"
            manifest_path = REGISTRY_DIR / "manifest.json"
            manifest_hash = "N/A"
            if manifest_path.exists():
                import hashlib
                hasher = hashlib.sha256()
                with open(manifest_path, "rb") as f:
                    hasher.update(f.read())
                manifest_hash = hasher.hexdigest()[:16]

            # Manifest / Registry version
            meta_version = "1.0.0"
            comp = self.registry_by_id.get("company_info")
            if comp and hasattr(comp, "metadata") and comp.metadata:
                meta_version = getattr(comp.metadata, "content_version", "1.0.0")

            reg_count = len(self.registry_by_id)
            entity_count = len(self.entities)
            alias_count = len(self.alias_lookup)
            kw_count = len(self.keyword_lookup)
            slug_count = len(self.slug_lookup)
            vocab_size = len(self.unified_vocabulary)
            kg_nodes = len(self.knowledge_graph)

            # Warnings count
            alias_to_ids = {}
            for alias, ent_id in self.alias_lookup.items():
                alias_to_ids.setdefault(alias, set()).add(ent_id)
            dup_alias_count = sum(1 for v in alias_to_ids.values() if len(v) > 1)

            print("\n========== ENTITY DIAGNOSTICS ==========")
            print(f" Registry Version    : {meta_version}")
            print(f" Registry Hash       : {manifest_hash}")
            print(f" Total Registries    : {reg_count}")
            print(f" Total Entities      : {entity_count}")
            print(f" Canonical IDs       : {entity_count}")
            print(f" Slugs               : {slug_count}")
            print(f" Aliases             : {alias_count}")
            print(f" Keywords            : {kw_count}")
            print(f" Synonyms            : {len(self.aliases)}")
            print(f" Vocabulary Size     : {vocab_size}")
            print(f" Knowledge Graph Nodes: {kg_nodes}")
            print(f" Duplicate Aliases  : {dup_alias_count}")
            print("========================================\n")
        except Exception as e:
            logger.error(f"Error printing diagnostics: {e}")

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        if not entity_id:
            return None
        eid = str(entity_id).lower().strip().replace(" ", "_")
        if eid in ["company", "citta", "cittaai", "about", "cittaai_company", "company_v1"]:
            eid = "company_info"
        elif eid == "healthcare_os":
            eid = "pharma_os"
        elif eid == "realty_os":
            eid = "real_estate_os"

        # 1. Direct canonical entity match
        if eid in self.entities:
            return self.entities[eid]

        # 2. Check entity_lookup
        clean_key = self._clean_key(entity_id)
        target_id = self.entity_lookup.get(clean_key) or self.entity_lookup.get(eid)
        if target_id and target_id in self.entities:
            return self.entities[target_id]

        # 3. Check aliases map
        target_id = self.aliases.get(clean_key) or self.aliases.get(eid)
        if target_id and target_id in self.entities:
            return self.entities[target_id]

        # 4. Check registry_by_id
        if eid in self.registry_by_id:
            return self._to_legacy_dict(self.registry_by_id[eid])

        return None

    def get_all_entities(self) -> List[Dict[str, Any]]:
        return list(self.entities.values())

    def get_related(self, entity_id: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        node = self.knowledge_graph.get(entity_id)
        if not node:
            return []
            
        related_ids = node.get("related_entities", [])
        for rel_id in related_ids:
            target_ent = self.get_entity(rel_id)
            if target_ent:
                results.append({
                    "entity": target_ent,
                    "relation": relationship_type or "related"
                })
        return results

_registry_inst = None
def get_registry() -> KnowledgeRegistry:
    global _registry_inst
    if _registry_inst is None:
        _registry_inst = KnowledgeRegistry()
    return _registry_inst
