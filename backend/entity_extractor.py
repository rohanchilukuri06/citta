import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractedEntities:
    company: Optional[str] = None
    product: Optional[str] = None
    solution: Optional[str] = None
    service: Optional[str] = None
    industry: Optional[str] = None
    person: Optional[str] = None
    role: Optional[str] = None

class EntityExtractor:
    def extract(self, query: str) -> ExtractedEntities:
        q_lower = query.lower().strip()
        result = ExtractedEntities()

        # Company
        if "citta" in q_lower or "cittaai" in q_lower:
            result.company = "CittaAI"
        elif "fixity" in q_lower:
            result.company = "Fixity"

        # Products
        if "whatsapp" in q_lower:
            result.product = "WhatsApp Marketing Platform"
        elif "influencer" in q_lower:
            result.product = "Influencer Marketing Platform"

        # Solutions
        if "ecommerce" in q_lower or "e-commerce" in q_lower:
            result.solution = "E-Commerce OS"
        elif "pharma" in q_lower or "healthcare" in q_lower:
            result.solution = "Pharma & Healthcare OS"
        elif "real estate" in q_lower or "realestate" in q_lower or "broker" in q_lower:
            result.solution = "Real Estate OS"
        elif "education" in q_lower or "lms" in q_lower:
            result.solution = "Education OS"
        elif "smart cities" in q_lower or "smart city" in q_lower:
            result.solution = "Smart Cities OS"
        elif "enterprise ai os" in q_lower or "enterprise os" in q_lower:
            result.solution = "Enterprise AI OS"

        # Services
        if "data engineering" in q_lower:
            result.service = "Data Engineering"
        elif "agentic" in q_lower:
            result.service = "Enterprise & Agentic AI"
        elif "strategy" in q_lower or "advisory" in q_lower:
            result.service = "AI Strategy & Advisory"
        elif "martech" in q_lower:
            result.service = "MarTech 360"

        # Industries
        if any(w in q_lower for w in ["hospital", "healthcare", "medical"]):
            result.industry = "Healthcare"
        elif any(w in q_lower for w in ["retail", "ecommerce", "e-commerce"]):
            result.industry = "E-Commerce / Retail"
        elif any(w in q_lower for w in ["school", "university", "education"]):
            result.industry = "Education"

        # Role & Person
        if re.search(r"\bceo\b", q_lower):
            result.role = "CEO"
            result.person = "Akhil Reddy"
        elif re.search(r"\bcoo\b", q_lower) or "operations" in q_lower and "responsible" in q_lower:
            result.role = "COO"
            result.person = "Saladi Chandra Balaji"
        elif re.search(r"\bcmo\b", q_lower) or "marketing" in q_lower and "handles" in q_lower:
            result.role = "CMO"
            result.person = "Ganesh Gandhi Vadalani"
        elif re.search(r"\bfounder\b", q_lower):
            result.role = "Founder"
            result.person = "Saladi Chandra Balaji / Akhil Reddy"

        if "vinay" in q_lower:
            result.person = "Vinay Velivela"
            result.role = "CEO of Fixity Technologies"
        elif "akhil" in q_lower:
            result.person = "Akhil Reddy"
            result.role = "CEO"
        elif "balaji" in q_lower or "saladi" in q_lower:
            result.person = "Saladi Chandra Balaji"
            result.role = "COO"

        return result

_extractor_instance = None

def get_entity_extractor() -> EntityExtractor:
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EntityExtractor()
    return _extractor_instance

