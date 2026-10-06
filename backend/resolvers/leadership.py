import re
import logging
from typing import Dict, Any, List, Optional
from knowledge_registry import get_registry

logger = logging.getLogger(__name__)

ROLE_ALIAS_MAP = {
    "ceo": ["ceo", "chief executive officer", "chief exec", "akhil", "akhil reddy"],
    "fixity_ceo": ["vinay", "vinay velivela", "fixity"],
    "coo": ["coo", "chief operating officer", "saladi", "saladi chandra balaji", "operations head", "who leads operations", "responsible for operations"],
    "cmo": ["cmo", "chief marketing officer", "ganesh", "ganesh gandhi vadalani", "marketing head", "who leads marketing", "who handles marketing", "handles marketing"],
    "sales_head": ["sales head", "sales lead", "harish", "harish nerati", "operations and sales head"],
    "ecommerce_head": ["e-commerce head", "ecommerce head", "aravind", "aravind reddy", "digital commerce head"],
    "bd_head": ["business development head", "bd head", "business head", "parvatha", "parvatha mohan", "who handles business development", "who is responsible for business development", "handles business development"]
}

class LeadershipResolver:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LeadershipResolver, cls).__new__(cls)
            cls._instance.reg = get_registry()
            cls._instance._build_indexes()
        return cls._instance

    def get_all_members(self) -> List[Dict[str, Any]]:
        """Loads leadership members strictly from leadership_info.json."""
        lead_obj = self.reg.registry_by_id.get("leadership_info")
        members = (getattr(lead_obj, "members", None) or getattr(lead_obj, "capabilities", None) or []) if lead_obj else []
        
        if not members and "LEADERSHIP" in self.reg.registry_index:
            lead_idx = self.reg.registry_index["LEADERSHIP"]
            members = lead_idx.get("members", []) or lead_idx.get("capabilities", []) or lead_idx.get("leaders", []) + lead_idx.get("others", [])
            
        if not members:
            # Fallback list matching leadership_info.json structure exactly
            members = [
                {
                    "id": "vinay_velivela",
                    "name": "Vinay Velivela",
                    "designation": "CEO of Fixity Technologies",
                    "department": "Executive Leadership",
                    "reports_to": None,
                    "bio": "Visionary leader driving innovation and organizational growth.",
                    "responsibilities": ["Company Vision", "Business Strategy", "Innovation", "Enterprise Growth"],
                    "keywords": ["Fixity Technologies", "Leadership"],
                    "aliases": ["vinay", "vinay velivela"]
                },
                {
                    "id": "saladi_chandra_balaji",
                    "name": "Saladi Chandra Balaji",
                    "designation": "Co-Founder & COO",
                    "department": "Operations",
                    "reports_to": "vinay_velivela",
                    "bio": "Leading operations, execution, and strategic business initiatives.",
                    "responsibilities": ["Operations", "Strategic Planning", "Execution", "Business Processes"],
                    "keywords": ["COO", "Chief Operating Officer", "Co-Founder", "Operations"],
                    "aliases": ["COO", "Operations Head", "saladi", "saladi chandra balaji", "balaji"]
                },
                {
                    "id": "akhil_reddy",
                    "name": "Akhil Reddy",
                    "designation": "CEO",
                    "department": "Technology",
                    "reports_to": "vinay_velivela",
                    "bio": "Architecting enterprise AI platforms and advanced technology solutions.",
                    "responsibilities": ["Technology Strategy", "AI Architecture", "Engineering", "Research & Development"],
                    "keywords": ["CEO", "Chief Executive Officer", "Leadership", "AI"],
                    "aliases": ["CEO", "Chief Executive Officer", "akhil", "akhil reddy"]
                },
                {
                    "id": "ganesh_gandhi_vadalani",
                    "name": "Ganesh Gandhi Vadalani",
                    "designation": "CMO",
                    "department": "Marketing",
                    "reports_to": "vinay_velivela",
                    "bio": "Driving global marketing strategy, branding, and business positioning.",
                    "responsibilities": ["Marketing", "Brand Strategy", "Demand Generation", "Growth Marketing"],
                    "keywords": ["CMO", "Chief Marketing Officer", "Marketing"],
                    "aliases": ["Marketing Head", "CMO", "ganesh", "ganesh gandhi vadalani"]
                },
                {
                    "id": "harish_nerati",
                    "name": "Harish Nerati",
                    "designation": "Operations and Sales Head",
                    "department": "Operations & Sales",
                    "reports_to": "saladi_chandra_balaji",
                    "bio": "Optimizing operational efficiency and driving sales growth.",
                    "responsibilities": ["Operations", "Sales", "Client Success", "Business Growth"],
                    "keywords": ["Sales Head", "Operations Head", "Sales", "Operations"],
                    "aliases": ["Sales Lead", "Operations Manager", "harish", "harish nerati"]
                },
                {
                    "id": "aravind_reddy",
                    "name": "Aravind Reddy",
                    "designation": "E-Commerce Head",
                    "department": "Digital Commerce",
                    "reports_to": "vinay_velivela",
                    "bio": "Leading digital commerce strategy and e-commerce platform initiatives.",
                    "responsibilities": ["E-Commerce", "Digital Commerce", "Marketplace Strategy", "Growth"],
                    "keywords": ["E-Commerce Head", "Commerce", "Digital Commerce"],
                    "aliases": ["Ecommerce Head", "Digital Commerce Head", "aravind", "aravind reddy"]
                },
                {
                    "id": "parvatha_mohan",
                    "name": "Parvatha Mohan",
                    "designation": "Business Development Head",
                    "department": "Business Development",
                    "reports_to": "vinay_velivela",
                    "bio": "Building strategic partnerships and expanding business opportunities.",
                    "responsibilities": ["Business Development", "Partnerships", "Client Acquisition", "Strategic Alliances"],
                    "keywords": ["Business Development", "BD", "Partnerships"],
                    "aliases": ["BD Head", "Business Head", "parvatha", "parvatha mohan"]
                }
            ]
        return members

    def _build_indexes(self):
        """Builds O(1) startup indexes for instant deterministic lookup."""
        self.name_index: Dict[str, Dict[str, Any]] = {}
        self.role_index: Dict[str, Dict[str, Any]] = {}
        self.alias_index: Dict[str, Dict[str, Any]] = {}
        self.department_index: Dict[str, Dict[str, Any]] = {}

        members = self.get_all_members()
        for m in members:
            name = m.get("name", "").strip()
            desig = m.get("designation", "").strip()
            dept = m.get("department", "").strip()
            aliases = m.get("aliases", [])
            keywords = m.get("keywords", [])

            # Name index
            self.name_index[name.lower()] = m
            for part in name.lower().split():
                if len(part) >= 3:
                    self.name_index[part] = m

            # Designation & Role index
            self.role_index[desig.lower()] = m
            for kw in keywords:
                self.role_index[kw.lower()] = m

            # Department index
            if dept:
                self.department_index[dept.lower()] = m

            # Alias index
            for alias in aliases:
                self.alias_index[alias.lower()] = m

    def resolve_leadership(self, target: str, tenant_id: str = "cittaai") -> Optional[Dict[str, Any]]:
        """Resolves executive profiles or entire leadership team strictly grounded in leadership_info.json."""
        if not target:
            return None
        target_clean = re.sub(r'[^\w\s]', '', target.lower()).strip()
        members = self.get_all_members()

        # Ensure indexes are built
        if not hasattr(self, "name_index") or not self.name_index:
            self._build_indexes()

        # 1. General Team Queries
        team_triggers = [
            "team", "our team", "the team", "leadership", "leadership team", "management", 
            "executives", "executive team", "founders", "people", "core team", "who are your team", 
            "citta team", "cittaai team", "meet the team", "meet our team", "leaders"
        ]
        
        is_general_team = False
        if target_clean in team_triggers:
            is_general_team = True
        else:
            for t in team_triggers:
                if target_clean == t or target_clean.startswith(f"{t} ") or target_clean.endswith(f" {t}"):
                    is_general_team = True
                    break

        if is_general_team:
            # Check if query contains a specific role request e.g., "who is ceo" or "who leads marketing"
            is_specific = False
            for r in ["ceo", "cto", "coo", "cmo", "sales", "commerce", "development", "technology", "marketing", "operations"]:
                if f"who is {r}" in target_clean or f"tell me about {r}" in target_clean or f"who leads {r}" in target_clean or f"who handles {r}" in target_clean:
                    is_specific = True
                    break
            if not is_specific:
                return {
                    "type": "team",
                    "members": members,
                    "metrics": {"resolved_entity": "NONE", "resolved_registry": "LEADERSHIP"}
                }

        # 2. O(1) Index Lookup: Alias
        if target_clean in self.alias_index:
            return {
                "type": "individual",
                "member": self.alias_index[target_clean],
                "metrics": {"resolved_entity": self.alias_index[target_clean]["id"], "resolved_registry": "LEADERSHIP"}
            }

        # 3. O(1) Index Lookup: Name
        if target_clean in self.name_index:
            return {
                "type": "individual",
                "member": self.name_index[target_clean],
                "metrics": {"resolved_entity": self.name_index[target_clean]["id"], "resolved_registry": "LEADERSHIP"}
            }

        # 4. O(1) Index Lookup: Role / Designation / Keywords
        if target_clean in self.role_index:
            return {
                "type": "individual",
                "member": self.role_index[target_clean],
                "metrics": {"resolved_entity": self.role_index[target_clean]["id"], "resolved_registry": "LEADERSHIP"}
            }

        # 5. Role Map Aliases & Question Patterns
        for role_code, aliases in ROLE_ALIAS_MAP.items():
            if any(a in target_clean for a in aliases):
                # Exact alias/keyword matches first, so "ceo" finds the CEO rather than "CEO of Fixity Technologies"
                def exact(m):
                    return any(a in [str(x).lower() for x in m.get("aliases", []) + m.get("keywords", [])] for a in aliases)
                for m in sorted(members, key=lambda m: not exact(m)):
                    m_desig = m.get("designation", "").lower()
                    m_aliases = [str(a).lower() for a in m.get("aliases", [])]
                    m_keywords = [str(k).lower() for k in m.get("keywords", [])]
                    if any(a in m_desig for a in aliases) or any(a in m_aliases for a in aliases) or any(a in m_keywords for a in aliases):
                        return {
                            "type": "individual",
                            "member": m,
                            "metrics": {"resolved_entity": m.get("id"), "resolved_registry": "LEADERSHIP"}
                        }

        # 6. Substring / Token Match Fallback
        for m in members:
            m_name = m.get("name", "").lower()
            m_desig = m.get("designation", "").lower()
            m_dept = m.get("department", "").lower()
            m_aliases = [str(a).lower() for a in m.get("aliases", [])]

            if (target_clean in m_name or 
                target_clean in m_desig or 
                (m_dept and target_clean in m_dept) or
                any(a in target_clean for a in m_aliases)):
                return {
                    "type": "individual",
                    "member": m,
                    "metrics": {"resolved_entity": m.get("id"), "resolved_registry": "LEADERSHIP"}
                }

        # 7. Unmatched Person or Role in Leadership Context
        return {
            "type": "not_found",
            "target": target,
            "metrics": {"resolved_entity": "NONE", "resolved_registry": "LEADERSHIP"}
        }

def get_leadership_resolver() -> LeadershipResolver:
    return LeadershipResolver()
