"""
Unit tests for field-level semantic arbitration (pure logic; no embedding model or LLM).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from semantic_decision import FieldEvidence
from semantic_arbitration import QuerySignals, arbitrate, arbitrate_field, fuse, infer_scope

INTENT = FieldEvidence("UNKNOWN", 0.0, "rules")
ASPECT = {"prior": {"OVERVIEW": 0.6}}


def _arb(entity_dists, signals=None, explicit=(), multi=(), ctx=None, llm=None, llm_available=False, aspect=None):
    return arbitrate(entity_dists, aspect or ASPECT, INTENT, signals or QuerySignals(residue=["x"], entity_evidence=True),
                     list(explicit), list(multi), context_entity=ctx, llm_verdict=llm, llm_available=llm_available)


def test_fuse_agreement_reinforces():
    ev = fuse({"rules": {"education_os": 0.95}, "bge": {"education_os": 0.8, "pharma_os": 0.1}})
    assert ev.value == "education_os"
    assert ev.confidence > 0.85
    assert ev.source == "bge+rules"


def test_fuse_disagreement_lowers_confidence_and_margin():
    ev = fuse({"rules": {"education_os": 0.95}, "bge": {"ai_strategy": 0.9}})
    assert ev.confidence < 0.55
    assert ev.margin < 0.1


def test_fuse_margin_is_between_distinct_values_not_sources():
    # Two sources voting for the same value must not look like a near-tie
    ev = arbitrate_field([FieldEvidence("pharma_os", 0.9, "rules"), FieldEvidence("pharma_os", 0.88, "bge")])
    assert ev.margin > 0.8


def test_abstaining_source_does_not_dilute():
    ev = fuse({"rules": {}, "bge": {"real_estate_os": 0.9}})
    assert ev.confidence == 0.9


def test_catalog_scope_requires_no_residual_domain():
    ent = FieldEvidence(None, 0.0, "none")
    s = infer_scope(ent, QuerySignals(catalog_request=True, catalog_scope="ALL_SOLUTIONS", residue=[]), [], [], "OVERVIEW", None)
    assert s.value == "ALL_SOLUTIONS"
    s = infer_scope(FieldEvidence("education_os", 0.9, "bge"),
                    QuerySignals(catalog_request=True, catalog_scope="ALL_SOLUTIONS", residue=["education"]), [], [], "OVERVIEW", None)
    assert s.value == "SINGLE_ENTITY"


def test_original_catalog_leak_regression():
    """'What solutions do you offer for education?' must be SINGLE_ENTITY, never a catalog dump."""
    sig = QuerySignals(catalog_request=True, catalog_scope="ALL_SOLUTIONS", residue=["education"], entity_evidence=True)
    d = _arb({"rules": {"education_os": 0.95}, "bge": {"education_os": 0.9}}, signals=sig, explicit=["education_os"])
    assert d.scope.value == "SINGLE_ENTITY"
    assert d.entity.value == "education_os"


def test_multi_entity_comparison():
    sig = QuerySignals(comparison=True, residue=["education", "pharma"], entity_evidence=True)
    d = _arb({"rules": {"education_os": 0.47, "pharma_os": 0.47}}, signals=sig,
             explicit=["education_os", "pharma_os"], multi=["education_os", "pharma_os"])
    assert d.scope.value == "MULTI_ENTITY"
    assert d.entities == ["education_os", "pharma_os"]


def test_context_carried_for_pronoun_followup():
    sig = QuerySignals(has_pronoun=True, residue=[])
    d = _arb({"rules": {}, "bge": {}}, signals=sig, ctx="education_os")
    assert d.entity.value == "education_os"
    assert d.scope.value == "SINGLE_ENTITY"
    assert not d.needs_clarification


def test_explicit_entity_overrides_context():
    sig = QuerySignals(residue=["pharma"], entity_evidence=True)
    d = _arb({"rules": {"pharma_os": 0.95}, "bge": {"pharma_os": 0.7}}, signals=sig, explicit=["pharma_os"], ctx="education_os")
    assert d.entity.value == "pharma_os"


def test_pronoun_without_context_asks_for_clarification():
    d = _arb({"rules": {}, "bge": {}}, signals=QuerySignals(has_pronoun=True, residue=[]))
    assert d.needs_clarification


def test_ambiguous_requests_llm_when_available():
    d = _arb({"bge": {"influencer_marketing": 0.35, "whatsapp_marketing": 0.33}}, llm_available=True)
    assert d.needs_llm_adjudication and not d.needs_clarification


def test_ambiguous_without_llm_clarifies_with_low_confidence():
    d = _arb({"bge": {"influencer_marketing": 0.35, "whatsapp_marketing": 0.33}}, llm_available=False)
    assert d.needs_clarification


def test_llm_verdict_resolves_ambiguity():
    verdict = {"entity": "whatsapp_marketing", "confidence": 0.9, "ambiguous": False, "out_of_domain": False}
    d = _arb({"bge": {"influencer_marketing": 0.35, "whatsapp_marketing": 0.33}}, llm=verdict)
    assert d.entity.value == "whatsapp_marketing"
    assert d.llm_invoked and not d.needs_clarification


def test_llm_out_of_domain_against_explicit_alias_clarifies_instead_of_declining():
    verdict = {"entity": None, "confidence": 0.9, "ambiguous": False, "out_of_domain": True}
    d = _arb({"rules": {"pharma_os": 0.95}, "bge": {"martech_360": 0.4}}, explicit=["pharma_os"], llm=verdict)
    assert d.needs_clarification
    assert d.scope.value != "OUT_OF_DOMAIN"


def test_company_aspect_owns_entity_when_no_catalog_entity_named():
    aspect = {"rules": {"CONTACT": 0.9}, "prior": {"OVERVIEW": 0.6}}
    d = _arb({"bge": {"influencer_marketing": 0.4}}, signals=QuerySignals(residue=["reach"]), aspect=aspect)
    assert d.entity.value == "contact_info"
    assert d.aspect.value == "CONTACT"


def test_unrelated_content_is_out_of_domain():
    d = _arb({"rules": {}, "bge": {}}, signals=QuerySignals(residue=["sourdough", "bread", "recipe"]))
    assert d.scope.value == "OUT_OF_DOMAIN"
    assert d.entity.value is None
