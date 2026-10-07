"""
Engine-level regression tests for the query-understanding failure modes that have hurt users:
catalog leakage, wrong entity for indirect phrasing, category-term mismatch, context follow-ups,
multi-entity comparisons and out-of-domain handling. Runs with LLM adjudication disabled so it is
deterministic and offline; the full measured benchmark is evaluation/semantic_benchmark.py.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest


@pytest.fixture(scope="module")
def engine():
    from query_intelligence_engine import QueryIntelligenceEngine
    return QueryIntelligenceEngine(enable_llm=False)


@pytest.fixture(scope="module")
def router():
    from knowledge_tool_router import KnowledgeToolRouter
    return KnowledgeToolRouter()


LISTING_OPS = {"list_solutions", "list_products", "list_services", "list_catalog"}


@pytest.mark.parametrize("query,entity", [
    ("What solutions do you offer for education?", "education_os"),
    ("I run a university. What could you guys do for us?", "education_os"),
    ("What can you do for colleges?", "education_os"),
    ("Our property business needs AI automation.", "real_estate_os"),
    ("What services do you have for WhatsApp?", "whatsapp_marketing"),
    ("What features does your Education service have?", "education_os"),
])
def test_entity_and_no_catalog_leakage(engine, router, query, entity):
    d = engine.analyze_query(query)
    assert d.entity.value == entity
    assert d.scope.value == "SINGLE_ENTITY"
    assert router.route_query(d)[0].operation_name not in LISTING_OPS


@pytest.mark.parametrize("query,scope", [
    ("What solutions do you offer?", "ALL_SOLUTIONS"),
    ("Which products do you sell?", "ALL_PRODUCTS"),
    ("list your services", "ALL_SERVICES"),
    ("What do you offer?", "ALL"),
])
def test_catalog_scope(engine, query, scope):
    d = engine.analyze_query(query)
    assert d.scope.value == scope
    assert d.entity.value is None


@pytest.mark.parametrize("ctx,query,aspect", [
    ("education_os", "What can it actually do?", "CAPABILITIES"),
    ("education_os", "Who is this meant for?", "TARGET_USERS"),
    ("real_estate_os", "Why would a business use it?", "BENEFITS"),
    ("whatsapp_marketing", "How does it work?", "WORKFLOW"),
])
def test_context_followups(engine, ctx, query, aspect):
    d = engine.analyze_query(query, active_entity=ctx)
    assert d.entity.value == ctx
    assert d.aspect.value == aspect


def test_topic_switch_overrides_context(engine):
    assert engine.analyze_query("What about pharma?", active_entity="education_os").entity.value == "pharma_os"


def test_pronoun_without_context_clarifies(engine):
    assert engine.analyze_query("What can it do?").needs_clarification


def test_multi_entity(engine, router):
    d = engine.analyze_query("Compare your Education and Pharma solutions.")
    assert d.scope.value == "MULTI_ENTITY"
    assert set(d.entities) == {"education_os", "pharma_os"}
    assert {p.inputs["entity_id"] for p in router.route_query(d)} == {"education_os", "pharma_os"}


def test_out_of_domain(engine):
    d = engine.analyze_query("What is the best recipe for baking sourdough bread at home?")
    assert d.entity.value is None
    assert d.scope.value == "OUT_OF_DOMAIN" or d.needs_clarification


def test_company_aspects(engine, router):
    assert router.route_query(engine.analyze_query("How do I reach you?"))[0].operation_name == "get_contact"
    assert router.route_query(engine.analyze_query("Who founded CittaAI and who leads the executive team?"))[0].operation_name == "get_leadership"


def test_confidence_reflects_ambiguity(engine):
    clear = engine.analyze_query("What can you do for universities?")
    vague = engine.analyze_query("We need something to keep customers updated through messaging.")
    assert clear.entity.confidence > vague.entity.confidence


def test_decision_exposes_legacy_attributes(engine):
    # phase2_orchestrator reads these; their absence used to silently discard the whole decision
    d = engine.analyze_query("What services do you have for WhatsApp?")
    assert isinstance(d.category_mismatch, bool)
    assert d.interpretation
    assert d.category_term_used_by_user == "SERVICE"


@pytest.mark.parametrize("query,scope", [
    # live miss: the short typo "ofer" was left unknown and the question was routed to case studies
    ("wat servics do u ofer", "ALL_SERVICES"),
    ("what produts do u ofer", "ALL_PRODUCTS"),
    ("which solutons u offr", "ALL_SOLUTIONS"),
    ("wat do u provde", "ALL"),
])
def test_typos_and_chat_shorthand_reach_catalog(engine, query, scope):
    assert engine.analyze_query(query).scope.value == scope


@pytest.mark.parametrize("text", ["it proved useful over time", "who is your cloud provider", "after the order"])
def test_typo_correction_leaves_real_words_alone(engine, text):
    assert engine._correct_catalog_typos(text) == text
