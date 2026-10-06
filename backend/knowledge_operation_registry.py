"""
KnowledgeOperationRegistry for CittaAI Bounded Agentic Enterprise Knowledge Architecture.
Provides schema-driven operation definitions, mapping intent/aspect/scope to authoritative knowledge operations.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class KnowledgeOperation:
    name: str
    description: str
    authoritative_source: str  # "KnowledgeRegistry" or "VectorStore"
    required_inputs: List[str] = field(default_factory=list)
    optional_inputs: List[str] = field(default_factory=list)
    allowed_entity_types: List[str] = field(default_factory=list)
    aspects: List[str] = field(default_factory=list)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    execution_bounds: Dict[str, Any] = field(default_factory=dict)


class KnowledgeOperationRegistry:
    def __init__(self):
        self.operations: Dict[str, KnowledgeOperation] = {}
        self._register_default_operations()

    def _register_default_operations(self):
        # 1. list_products
        self.register_operation(KnowledgeOperation(
            name="list_products",
            description="List all available products in the catalog",
            authoritative_source="KnowledgeRegistry",
            required_inputs=[],
            optional_inputs=[],
            allowed_entity_types=["catalog", "product"],
            aspects=["CATALOG_LIST", "OVERVIEW"],
            output_schema={"type": "array", "items": "product_summary"},
            execution_bounds={"max_items": 50, "fallback": "semantic_search"}
        ))

        # 2. get_product
        self.register_operation(KnowledgeOperation(
            name="get_product",
            description="Retrieve detailed product information by entity ID",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=["section"],
            allowed_entity_types=["product"],
            aspects=["OVERVIEW", "CAPABILITIES", "BENEFITS", "WORKFLOW", "PRICING", "FAQ"],
            output_schema={"type": "object", "properties": ["id", "name", "overview", "features", "benefits"]},
            execution_bounds={"max_items": 1, "fallback": "semantic_search"}
        ))

        # 3. list_solutions
        self.register_operation(KnowledgeOperation(
            name="list_solutions",
            description="List all enterprise OS solutions",
            authoritative_source="KnowledgeRegistry",
            required_inputs=[],
            optional_inputs=[],
            allowed_entity_types=["catalog", "solution"],
            aspects=["CATALOG_LIST", "OVERVIEW"],
            output_schema={"type": "array", "items": "solution_summary"},
            execution_bounds={"max_items": 50, "fallback": "semantic_search"}
        ))

        # 4. get_solution
        self.register_operation(KnowledgeOperation(
            name="get_solution",
            description="Retrieve detailed solution information by entity ID",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=["section"],
            allowed_entity_types=["solution"],
            aspects=["OVERVIEW", "CAPABILITIES", "BENEFITS", "WORKFLOW", "TARGET_USERS", "PRICING", "FAQ"],
            output_schema={"type": "object", "properties": ["id", "name", "overview", "workflows", "modules"]},
            execution_bounds={"max_items": 1, "fallback": "semantic_search"}
        ))

        # 5. get_capabilities
        self.register_operation(KnowledgeOperation(
            name="get_capabilities",
            description="Retrieve technical capabilities/features for an entity or platform",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=[],
            allowed_entity_types=["product", "solution", "service", "company"],
            aspects=["CAPABILITIES", "FEATURES"],
            output_schema={"type": "array", "items": "capability_detail"},
            execution_bounds={"max_items": 20, "fallback": "semantic_search"}
        ))

        # 6. get_benefits
        self.register_operation(KnowledgeOperation(
            name="get_benefits",
            description="Retrieve business benefits and ROI for an entity",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=[],
            allowed_entity_types=["product", "solution", "service", "company"],
            aspects=["BENEFITS"],
            output_schema={"type": "array", "items": "benefit_detail"},
            execution_bounds={"max_items": 20, "fallback": "semantic_search"}
        ))

        # 7. get_target_users
        self.register_operation(KnowledgeOperation(
            name="get_target_users",
            description="Retrieve target user roles and ideal personas for a solution or product",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=[],
            allowed_entity_types=["product", "solution", "service"],
            aspects=["TARGET_USERS"],
            output_schema={"type": "array", "items": "target_user_detail"},
            execution_bounds={"max_items": 10, "fallback": "semantic_search"}
        ))

        # 8. get_workflow
        self.register_operation(KnowledgeOperation(
            name="get_workflow",
            description="Retrieve workflow steps and process flows for a solution or product",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=[],
            allowed_entity_types=["product", "solution", "service"],
            aspects=["WORKFLOW"],
            output_schema={"type": "array", "items": "workflow_step"},
            execution_bounds={"max_items": 15, "fallback": "semantic_search"}
        ))

        # 9. get_faq
        self.register_operation(KnowledgeOperation(
            name="get_faq",
            description="Retrieve official FAQ Q&A entries for an entity or topic",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=["question_query"],
            allowed_entity_types=["product", "solution", "service", "company"],
            aspects=["FAQ"],
            output_schema={"type": "array", "items": "faq_item"},
            execution_bounds={"max_items": 10, "fallback": "semantic_search"}
        ))

        # 10. get_company_info
        self.register_operation(KnowledgeOperation(
            name="get_company_info",
            description="Retrieve general company overview, mission, and vision for CittaAI",
            authoritative_source="KnowledgeRegistry",
            required_inputs=[],
            optional_inputs=["section"],
            allowed_entity_types=["company"],
            aspects=["OVERVIEW", "COMPANY_OVERVIEW"],
            output_schema={"type": "object", "properties": ["name", "description", "mission", "vision"]},
            execution_bounds={"max_items": 1, "fallback": "semantic_search"}
        ))

        # 11. get_leadership
        self.register_operation(KnowledgeOperation(
            name="get_leadership",
            description="Retrieve leadership team details for CittaAI",
            authoritative_source="KnowledgeRegistry",
            required_inputs=[],
            optional_inputs=[],
            allowed_entity_types=["company"],
            aspects=["LEADERSHIP"],
            output_schema={"type": "array", "items": "executive_detail"},
            execution_bounds={"max_items": 10, "fallback": "semantic_search"}
        ))

        # 12. get_contact
        self.register_operation(KnowledgeOperation(
            name="get_contact",
            description="Retrieve contact methods, email, phone, location, and sales inquiry channels",
            authoritative_source="KnowledgeRegistry",
            required_inputs=[],
            optional_inputs=[],
            allowed_entity_types=["company"],
            aspects=["CONTACT"],
            output_schema={"type": "object", "properties": ["email", "phone", "address", "website"]},
            execution_bounds={"max_items": 1, "fallback": "semantic_search"}
        ))

        # 13. get_recognition
        self.register_operation(KnowledgeOperation(
            name="get_recognition",
            description="Retrieve industry awards, recognitions, and compliance certifications",
            authoritative_source="KnowledgeRegistry",
            required_inputs=[],
            optional_inputs=[],
            allowed_entity_types=["company"],
            aspects=["RECOGNITION"],
            output_schema={"type": "array", "items": "award_detail"},
            execution_bounds={"max_items": 15, "fallback": "semantic_search"}
        ))

        # 14. list_case_studies
        self.register_operation(KnowledgeOperation(
            name="list_case_studies",
            description="List client case studies and success stories",
            authoritative_source="KnowledgeRegistry",
            required_inputs=[],
            optional_inputs=["industry"],
            allowed_entity_types=["case_study", "company"],
            aspects=["CLIENTS_CASE_STUDIES"],
            output_schema={"type": "array", "items": "case_study_summary"},
            execution_bounds={"max_items": 20, "fallback": "semantic_search"}
        ))

        # 15. get_case_study
        self.register_operation(KnowledgeOperation(
            name="get_case_study",
            description="Retrieve full details for a specific case study",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=[],
            allowed_entity_types=["case_study"],
            aspects=["CLIENTS_CASE_STUDIES"],
            output_schema={"type": "object", "properties": ["client", "challenge", "solution", "results"]},
            execution_bounds={"max_items": 1, "fallback": "semantic_search"}
        ))

        # 16. list_services
        self.register_operation(KnowledgeOperation(
            name="list_services",
            description="List all professional services",
            authoritative_source="KnowledgeRegistry",
            allowed_entity_types=["catalog", "service"],
            aspects=["CATALOG_LIST"],
            output_schema={"type": "array", "items": "service_summary"},
            execution_bounds={"max_items": 50, "fallback": "semantic_search"}
        ))

        # 17. list_catalog
        self.register_operation(KnowledgeOperation(
            name="list_catalog",
            description="List every product, solution and service grouped by category",
            authoritative_source="KnowledgeRegistry",
            allowed_entity_types=["catalog"],
            aspects=["CATALOG_LIST"],
            output_schema={"type": "object", "properties": ["products", "solutions", "services"]},
            execution_bounds={"max_items": 60, "fallback": "semantic_search"}
        ))

        # 18. get_service
        self.register_operation(KnowledgeOperation(
            name="get_service",
            description="Retrieve detailed professional service information by entity ID",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=["section"],
            allowed_entity_types=["service"],
            aspects=["OVERVIEW", "CAPABILITIES", "BENEFITS", "WORKFLOW", "FAQ"],
            output_schema={"type": "object", "properties": ["id", "name", "overview", "capabilities", "benefits"]},
            execution_bounds={"max_items": 1, "fallback": "semantic_search"}
        ))

        # 19. get_pricing
        self.register_operation(KnowledgeOperation(
            name="get_pricing",
            description="Retrieve published pricing for an entity; when none is published, direct the user to sales",
            authoritative_source="KnowledgeRegistry",
            required_inputs=["entity_id"],
            optional_inputs=["section"],
            allowed_entity_types=["product", "solution", "service"],
            aspects=["PRICING"],
            output_schema={"type": "object", "properties": ["pricing", "contact"]},
            execution_bounds={"max_items": 1, "fallback": "get_contact"}
        ))

        # 20. decline_out_of_domain
        self.register_operation(KnowledgeOperation(
            name="decline_out_of_domain",
            description="Politely decline questions unrelated to CittaAI and suggest in-scope topics",
            authoritative_source="KnowledgeRegistry",
            allowed_entity_types=["any"],
            aspects=["UNKNOWN"],
            output_schema={"type": "object", "properties": ["message"]},
            execution_bounds={"max_items": 0, "fallback": None}
        ))

        # 21. semantic_search
        self.register_operation(KnowledgeOperation(
            name="semantic_search",
            description="Vector store semantic retrieval fallback for unstructured or broad queries",
            authoritative_source="VectorStore",
            required_inputs=["query_text"],
            optional_inputs=["top_k", "filter_domain"],
            allowed_entity_types=["any"],
            aspects=["UNKNOWN", "OVERVIEW"],
            output_schema={"type": "array", "items": "text_chunk"},
            execution_bounds={"max_items": 5, "fallback": None}
        ))

    def register_operation(self, op: KnowledgeOperation):
        self.operations[op.name] = op

    def get_operation(self, name: str) -> Optional[KnowledgeOperation]:
        return self.operations.get(name)

    def find_matching_operations(
        self,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        aspect: Optional[str] = None,
        scope: Optional[str] = None
    ) -> List[KnowledgeOperation]:
        """Dynamically resolve matching operations from registry without hardcoded keyword rules."""
        matches = []
        for op in self.operations.values():
            if op.name == "semantic_search":
                continue
            
            # Check aspect match
            aspect_match = False
            if aspect and op.aspects:
                aspect_upper = aspect.upper()
                if aspect_upper in op.aspects or any(a in aspect_upper for a in op.aspects):
                    aspect_match = True
            elif not aspect:
                aspect_match = True

            # Check entity type match
            type_match = False
            if entity_type and op.allowed_entity_types:
                if entity_type.lower() in op.allowed_entity_types or "any" in op.allowed_entity_types:
                    type_match = True
            elif not entity_type:
                type_match = True

            if aspect_match and type_match:
                matches.append(op)

        return matches


_GLOBAL_OPERATION_REGISTRY: Optional[KnowledgeOperationRegistry] = None

def get_operation_registry() -> KnowledgeOperationRegistry:
    global _GLOBAL_OPERATION_REGISTRY
    if _GLOBAL_OPERATION_REGISTRY is None:
        _GLOBAL_OPERATION_REGISTRY = KnowledgeOperationRegistry()
    return _GLOBAL_OPERATION_REGISTRY
