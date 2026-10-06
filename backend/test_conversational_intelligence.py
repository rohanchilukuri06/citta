import pytest
from conversation.query_understanding import get_query_understanding_engine, normalize_query
from resolvers.leadership import get_leadership_resolver
from resolvers.case_study import get_case_study_resolver
from conversation.response_generator import get_response_generator
from conversation.navigation import get_navigation_controller
from suggestions.follow_up import get_follow_up_engine
from structured_renderers import clean_val, sanitize_conversational_text, render_company

def test_query_normalization():
    assert "education os" in normalize_query("educaton os")
    assert "pharma os" in normalize_query("pharmaa os")
    assert "whatsapp" in normalize_query("whatsap marketing")

def test_query_understanding_result():
    qu = get_query_understanding_engine()
    res = qu.analyze("Who is the CEO?")
    assert res.intent == "leadership_lookup"
    assert res.target == "CEO"
    assert res.confidence >= 0.90
    assert res.requires_clarification is False

def test_navigation_intent_detection():
    qu = get_query_understanding_engine()
    assert qu.analyze("Education OS").navigation_intent is False
    assert qu.analyze("Tell me about Pharma OS").navigation_intent is False
    assert qu.analyze("Open Education OS").navigation_intent is True
    assert qu.analyze("Visit Pharma OS").navigation_intent is True
    assert qu.analyze("Take me to Education OS").navigation_intent is True
    assert qu.analyze("Go to Contact").navigation_intent is True
    assert qu.analyze("Open Products").navigation_intent is True

def test_navigation_controller_rules():
    nav = get_navigation_controller()
    
    # Rule 1: Informational query (navigation_intent = False) -> redirect is None
    url, actions = nav.process_navigation(
        navigation_intent=False,
        target_url="/solutions/education-os",
        entity_name="Education OS",
        entity_type="SOLUTIONS"
    )
    assert url is None
    assert len(actions) >= 2
    assert any(a["label"] == "Learn More" for a in actions)

    # Rule 2: Explicit navigation query (navigation_intent = True) -> redirect equals target_url
    url, actions = nav.process_navigation(
        navigation_intent=True,
        target_url="/solutions/education-os",
        entity_name="Education OS",
        entity_type="SOLUTIONS"
    )
    assert url == "/solutions/education-os"
    assert len(actions) == 0

def test_prompt4_sanitize_conversational_text():
    raw_input = "### Overview\nHere is [View Solution →](/solutions/ecommerce-os) and [Explore Service →](/services/ai). Read More."
    sanitized = sanitize_conversational_text(raw_input)
    assert "###" not in sanitized
    assert "/solutions/" not in sanitized
    assert "/services/" not in sanitized
    assert "→" not in sanitized
    assert "View Solution" not in sanitized

def test_prompt4_conversational_company_response():
    class DummyCompany:
        title = "CittaAI"
        name = "CittaAI"
        tagline = "Elevate. Innovate."
        overview = "Enterprise AI Consultancy."
        type = type("Type", (), {"value": "company"})()
    
    comp_md = render_company(DummyCompany())
    assert "🏢 **CittaAI** is an Enterprise AI consultancy" in comp_md
    assert "• Founded in 2022" in comp_md
    assert "• Serves 50+ enterprise clients" in comp_md
    assert "###" not in comp_md
    assert "Overview" not in comp_md or "**Overview**" in comp_md or "Here is a quick overview:" in comp_md

def test_issue1_team_query_direct_routing():
    from deterministic_engine import get_deterministic_engine
    engine = get_deterministic_engine()
    from intent_analyzer import IntentType, TopicType

    resp = engine.generate_response("cittaai", IntentType.ASK, [TopicType.PERSON_LOOKUP], "team")
    assert resp is not None
    assert resp["source"] == "Leadership Registry"
    assert "executive" in resp["response"].lower() or "leadership" in resp["response"].lower()
    assert resp["navigation"] is None

def test_issue2_ceo_query_direct_routing():
    from deterministic_engine import get_deterministic_engine
    engine = get_deterministic_engine()
    from intent_analyzer import IntentType, TopicType

    resp = engine.generate_response("cittaai", IntentType.ASK, [TopicType.PERSON_LOOKUP], "CEO")
    assert resp is not None
    assert resp["source"] == "Leadership Registry"
    assert "Akhil Reddy" in resp["response"]

def test_issue3_case_study_resolver_no_misrouting():
    from deterministic_engine import get_deterministic_engine
    engine = get_deterministic_engine()
    from intent_analyzer import IntentType, TopicType

    resp = engine.generate_response("cittaai", IntentType.ASK, [TopicType.CASE_STUDIES], "Explain one case study")
    assert resp is not None
    assert resp["source"] == "Case Studies Registry"
    assert "AI Strategy" not in resp["response"]
    assert "Case Studies" in resp["response"] or "Jewellery" in resp["response"]

def test_issue4_product_understanding_graceful_fallback():
    from deterministic_engine import get_deterministic_engine
    engine = get_deterministic_engine()
    from intent_analyzer import IntentType, TopicType

    resp = engine.generate_response("cittaai", IntentType.ASK, [TopicType.SOLUTIONS], "How pharma OS works")
    assert resp is not None
    assert "pharma_os" in resp["source"]
    assert "Pharma OS" in resp["response"]

@pytest.mark.anyio
async def test_deterministic_team_and_leadership_queries():
    from resolvers.leadership import get_leadership_resolver
    resolver = get_leadership_resolver()
    from conversation.response_generator import AdaptiveResponseGenerator
    gen = AdaptiveResponseGenerator()

    # 1. Team queries
    for q in ["team", "our team", "leadership", "leadership team", "management", "executives", "executive team", "founders", "people", "core team"]:
        res = resolver.resolve_leadership(q)
        assert res is not None, f"Failed for query '{q}'"
        assert res["type"] == "team", f"Failed team type for query '{q}'"
        text = gen.generate_leadership_response(res)
        assert "Leadership Team" in text
        assert "Vinay Velivela" in text
        assert "Akhil Reddy" in text

    # 2. Role queries
    role_cases = [
        ("CEO", "Akhil Reddy"),
        ("Who is the CEO?", "Akhil Reddy"),
        ("COO", "Saladi Chandra Balaji"),
        ("Who is responsible for Operations?", "Saladi Chandra Balaji"),
        ("CMO", "Ganesh Gandhi Vadalani"),
        ("Who handles Marketing?", "Ganesh Gandhi Vadalani"),
        ("Sales Head", "Harish Nerati"),
        ("E-Commerce Head", "Aravind Reddy"),
        ("Business Development Head", "Parvatha Mohan")
    ]
    for query, expected_name in role_cases:
        res = resolver.resolve_leadership(query)
        assert res is not None, f"Failed for {query}"
        assert res["type"] == "individual", f"Failed individual check for {query}"
        text = gen.generate_leadership_response(res)
        assert expected_name in text, f"Expected {expected_name} in response for query '{query}'"

    # 3. Name queries (Full & First names)
    name_cases = [
        ("Vinay Velivela", "Fixity Technologies"),
        ("Vinay", "Fixity Technologies"),
        ("Akhil Reddy", "CEO"),
        ("Akhil", "CEO"),
        ("Saladi Chandra Balaji", "COO"),
        ("Balaji", "COO"),
        ("Ganesh Gandhi Vadalani", "CMO"),
        ("Ganesh", "CMO"),
        ("Harish Nerati", "Operations and Sales Head"),
        ("Harish", "Operations and Sales Head"),
        ("Aravind Reddy", "E-Commerce Head"),
        ("Aravind", "E-Commerce Head"),
        ("Parvatha Mohan", "Business Development Head"),
        ("Parvatha", "Business Development Head")
    ]
    for query, expected_title in name_cases:
        res = resolver.resolve_leadership(query)
        assert res is not None, f"Failed for name {query}"
        assert res["type"] == "individual", f"Failed type for name {query}"
        text = gen.generate_leadership_response(res)
        assert "CEO" in text or "CTO" in text or "COO" in text or "CMO" in text or "Head" in text

    # 4. Unknown person query
    res = resolver.resolve_leadership("who is John Doe")
    assert res is not None
    assert res["type"] == "not_found"
    text = gen.generate_leadership_response(res)
    assert text == "I couldn't find that person in CittaAI's leadership team."
    assert "null" not in text

def test_issue5_unknown_capability_fallback_no_about_default():
    from deterministic_engine import get_deterministic_engine
    engine = get_deterministic_engine()
    from intent_analyzer import IntentType, TopicType

    resp = engine.generate_response("cittaai", IntentType.ASK, [], "PPC Advertising")
    assert resp is not None
    assert "About CittaAI" not in resp["response"]
    assert "PPC Advertising" in resp["response"] or "Marketing" in resp["response"]

def test_issue6_no_none_or_null_literals():
    assert clean_val(None) == ""
    assert clean_val("None") == ""
    assert clean_val("null") == ""
    assert clean_val("Unknown") == ""

def test_issue7_statistics_metrics_query():
    from deterministic_engine import get_deterministic_engine
    engine = get_deterministic_engine()
    from intent_analyzer import IntentType, TopicType

    resp = engine.generate_response("cittaai", IntentType.ASK, [], "Enterprise Clients")
    assert resp is not None
    assert "50+" in resp["response"]
    assert "100,000+" in resp["response"]

def test_issue8_graceful_fallbacks():
    from deterministic_engine import get_deterministic_engine
    engine = get_deterministic_engine()
    from intent_analyzer import IntentType, TopicType

    resp = engine.generate_response("cittaai", IntentType.ASK, [], "RandomUnknownKeywordXyz")
    assert resp is not None
    assert "I encountered an issue" not in resp["response"]
    assert len(resp["suggestions"]) >= 2
