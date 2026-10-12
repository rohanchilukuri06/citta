"""
Spelling / chat-shorthand normalisation and the routing it protects. Every case here is a question a visitor
actually typed (or a close variant) that used to be declined, sent to the wrong topic, or asked to clarify.
Runs with LLM adjudication off, so the rules and embeddings alone must get these right.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from query_spelling import KEYWORDS, PROTECTED, SHORTHAND, SpellingNormaliser


@pytest.fixture(scope="module")
def engine():
    from query_intelligence_engine import QueryIntelligenceEngine
    return QueryIntelligenceEngine(enable_llm=False)


@pytest.fixture(scope="module")
def router():
    from knowledge_tool_router import KnowledgeToolRouter
    return KnowledgeToolRouter()


@pytest.mark.parametrize("typed,meant", [
    ("wat servics do u ofer", "what services do you offer"),
    ("wat prodcts u hav", "what products you have"),
    ("which producs do u sel", "which products do you sell"),
    ("wat solutons do u hv", "what solutions do you have"),
    ("who r the team membrs", "who are the team members"),
    ("where is ur ofice", "where is your office"),
    ("wats the prise of education os", "what is the price of education os"),
    ("whos the foundr", "who is the founder"),
    ("how do i contct u", "how do i contact you"),
    ("finanace and marketng", "finance and marketing"),
    ("awards and recogniton", "awards and recognition"),
    ("evrything u offer", "everything you offer"),
])
def test_normalises_typos_and_shorthand(engine, typed, meant):
    assert engine._correct_catalog_typos(typed) == meant


@pytest.mark.parametrize("text", [
    "What solutions do you offer for education?",
    "it proved useful over time, after the order",
    "who is your cloud provider",
    "do you sign a contract before we start",
    "can I change the plan later",
    "we won a prize for our pharmacy chain",
    "the officer who serves our coast region",
    "I run a university. What could you guys do for us?",
])
def test_correct_text_is_left_exactly_as_typed(engine, text):
    assert engine._correct_catalog_typos(text) == text


def test_protected_words_and_keywords_do_not_overlap():
    assert not (KEYWORDS & PROTECTED)
    assert not (set(SHORTHAND) & KEYWORDS)


def test_unknown_long_words_are_not_forced_onto_a_keyword():
    n = SpellingNormaliser()
    for word in ["weather", "poem", "hospital", "university", "cricket", "restaurant", "bitcoin"]:
        assert n.normalise(word) == word


@pytest.mark.parametrize("query,operation", [
    ("wat servics do u ofer", "list_services"),
    ("servces u provid", "list_services"),
    ("wat prodcts u hav", "list_products"),
    ("which producs do u sel", "list_products"),
    ("wat solutons do u hv", "list_solutions"),
    ("evrything u offer", "list_catalog"),
    ("who os the ceo", "get_leadership"),
    ("whos the foundr", "get_leadership"),
    ("who r the team membrs", "get_leadership"),
    ("managment team", "get_leadership"),
    ("who runs this company", "get_leadership"),
    ("who runs cittaai", "get_leadership"),
    ("how do i contct u", "get_contact"),
    ("where is ur ofice", "get_contact"),
    ("adress of citta", "get_contact"),
    ("wats the prise of education os", "get_pricing"),
    ("pricng for whatsapp marketing", "get_pricing"),
    ("any awrds", "get_recognition"),
    ("who r ur clients", "list_case_studies"),
    ("abt citta", "get_company_info"),
    ("tell me about your company", "get_company_info"),
    ("what does your company do", "get_company_info"),
    ("who are you guys", "get_company_info"),
    ("what do you do", "get_company_info"),
    ("whats the wether today", "decline_out_of_domain"),
    ("write me a poem", "decline_out_of_domain"),
])
def test_misspelled_questions_reach_the_right_answer(engine, router, query, operation):
    assert router.route_query(engine.analyze_query(query))[0].operation_name == operation


@pytest.mark.parametrize("query,entity", [
    ("tel me abt educaton os", "education_os"),
    ("wat is edu os", "education_os"),
    ("featurs of education os", "education_os"),
    ("real estat os", "real_estate_os"),
    ("whatsap marketng service", "whatsapp_marketing"),
    ("ecom os features", "ecommerce_os"),
])
def test_misspelled_offering_names_resolve(engine, query, entity):
    assert engine.analyze_query(query).entity.value == entity


def test_visitors_own_company_is_not_mistaken_for_cittaai(engine):
    d = engine.analyze_query("our company runs three colleges, what can you do")
    assert d.entity.value == "education_os"
