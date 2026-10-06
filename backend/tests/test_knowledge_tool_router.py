"""
Router tests: the operation must match the decision's meaning, not just be a valid operation.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from knowledge_tool_router import KnowledgeToolRouter


@pytest.fixture(scope="module")
def router():
    return KnowledgeToolRouter()


def route(router, **kw):
    base = {"entity": None, "entities": [], "aspect": "OVERVIEW", "scope": "SINGLE_ENTITY", "confidence": 0.9, "needs_clarification": False}
    base.update(kw)
    return router.route_query(base)


@pytest.mark.parametrize("aspect,op", [
    ("CAPABILITIES", "get_capabilities"), ("BENEFITS", "get_benefits"), ("TARGET_USERS", "get_target_users"),
    ("WORKFLOW", "get_workflow"), ("FAQ", "get_faq"), ("PRICING", "get_pricing"),
])
def test_aspect_selects_operation_with_entity(router, aspect, op):
    plans = route(router, entity="education_os", aspect=aspect)
    assert plans[0].operation_name == op
    assert plans[0].inputs["entity_id"] == "education_os"


@pytest.mark.parametrize("entity,op", [
    ("whatsapp_marketing", "get_product"), ("education_os", "get_solution"),
    ("data_engineering", "get_service"), ("company_info", "get_company_info"),
])
def test_overview_follows_registry_type(router, entity, op):
    assert route(router, entity=entity)[0].operation_name == op


@pytest.mark.parametrize("scope,op", [
    ("ALL", "list_catalog"), ("ALL_SOLUTIONS", "list_solutions"), ("ALL_PRODUCTS", "list_products"), ("ALL_SERVICES", "list_services"),
])
def test_catalog_scopes(router, scope, op):
    assert route(router, scope=scope)[0].operation_name == op


def test_single_entity_never_leaks_into_catalog_listing(router):
    # A resolved entity must win even if a catalog scope is present
    plans = route(router, entity="education_os", scope="ALL_SOLUTIONS")
    assert plans[0].operation_name not in {"list_solutions", "list_products", "list_services", "list_catalog"}


def test_multi_entity_fanout_is_capped(router):
    plans = route(router, scope="MULTI_ENTITY", entity="education_os",
                  entities=["education_os", "pharma_os", "real_estate_os", "ecommerce_os"])
    assert [p.inputs["entity_id"] for p in plans] == ["education_os", "pharma_os", "real_estate_os"]


@pytest.mark.parametrize("aspect,op", [
    ("CONTACT", "get_contact"), ("LEADERSHIP", "get_leadership"), ("RECOGNITION", "get_recognition"),
    ("CLIENTS_CASE_STUDIES", "list_case_studies"),
])
def test_company_aspects(router, aspect, op):
    assert route(router, entity=None, aspect=aspect, scope="ALL" if aspect == "CLIENTS_CASE_STUDIES" else "SINGLE_ENTITY")[0].operation_name == op


def test_clarification_carries_options(router):
    opts = [{"entity_id": "education_os", "title": "Education OS"}]
    plans = route(router, entity="education_os", needs_clarification=True, clarification_options=opts)
    assert plans[0].operation_name == "request_clarification"
    assert plans[0].inputs["options"] == opts


def test_out_of_domain_is_declined(router):
    assert route(router, scope="OUT_OF_DOMAIN")[0].operation_name == "decline_out_of_domain"


def test_accepts_semantic_decision_objects(router):
    from semantic_decision import FieldEvidence, SemanticDecision
    d = SemanticDecision(entity=FieldEvidence(None, 0.0, "none"), intent=FieldEvidence("UNKNOWN", 0.0, "rules"),
                         aspect=FieldEvidence("OVERVIEW", 0.5, "prior"), scope=FieldEvidence("GENERAL", 0.5, "rules"),
                         original_query="hello there")
    # Previously crashed with AttributeError ('SemanticDecision' object has no attribute 'get')
    assert router.route_query(d)[0].operation_name == "semantic_search"
