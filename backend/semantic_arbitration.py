"""
Field-Level Semantic Arbitration Engine for CittaAI.

Each evidence source (rules, BGE, context, LLM) contributes a probability distribution over values
for a field. Distributions are fused per *value* (not per source), so two sources agreeing on the
same entity reinforce each other and disagreement lowers confidence. The fused probability of the
winner is the field's confidence; margin is the gap to the runner-up value.

Scope is inferred from query signals (catalog language, comparison markers, pronouns, residual
domain content) plus the fused entity decision, then used to decide whether the decision is
accepted, sent to LLM adjudication, or turned into a clarification request.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from semantic_decision import FieldEvidence, SemanticDecision

logger = logging.getLogger(__name__)

SOURCE_WEIGHTS = {"rules": 1.0, "bge": 1.0, "context": 1.0, "llm": 1.3}

# Decision thresholds (fitted on the dev split; see evaluation/semantic_benchmark.py)
ACCEPT_CONFIDENCE = 0.60   # accept without LLM when confidence and margin are both above these
ACCEPT_MARGIN = 0.20
FALLBACK_CONFIDENCE = 0.45  # without an LLM verdict, best guess below this becomes a clarification
FALLBACK_MARGIN = 0.10
# Without an LLM to adjudicate, an entity this weakly supported means the query isn't about the catalog
WEAK_ENTITY_FLOOR = 0.20
# Confidence reported for an aspect chosen by the OVERVIEW default with no supporting evidence
DEFAULT_ASPECT_CONFIDENCE = 0.40

# Canonical scopes
SINGLE_ENTITY = "SINGLE_ENTITY"
MULTI_ENTITY = "MULTI_ENTITY"
ALL = "ALL"
ALL_SOLUTIONS = "ALL_SOLUTIONS"
ALL_PRODUCTS = "ALL_PRODUCTS"
ALL_SERVICES = "ALL_SERVICES"
OUT_OF_DOMAIN = "OUT_OF_DOMAIN"
UNKNOWN_ENTITY = "UNKNOWN_ENTITY"
CLIENTS_SCOPE = "CLIENTS_SCOPE"
CATALOG_SCOPES = {ALL, ALL_SOLUTIONS, ALL_PRODUCTS, ALL_SERVICES}

# Aspects that are about the company rather than a catalog entity, with their owning entity
COMPANY_ASPECT_ENTITY = {
    "CONTACT": "contact_info",
    "LEADERSHIP": "leadership_info",
    "RECOGNITION": "awards_recognition",
    "CLIENTS_CASE_STUDIES": None,
}


@dataclass
class QuerySignals:
    """Language-level signals, independent of which entities exist."""
    has_pronoun: bool = False
    catalog_request: bool = False
    catalog_scope: Optional[str] = None
    comparison: bool = False
    residue: List[str] = field(default_factory=list)  # content words left after removing function/catalog words
    ood_detector: bool = False
    entity_evidence: bool = False  # something in the query itself points at a catalog entity
    unknown_product: Optional[str] = None  # product-shaped name absent from the registry ("Finance OS")
    unresolved_pair: bool = False  # "both"/"the two" with no pair of entities in context
    company_reference: bool = False  # the query names the company itself (CittaAI)


def fuse(distributions: Dict[str, Dict[str, float]], weights: Optional[Dict[str, float]] = None) -> FieldEvidence:
    """
    Fuse per-source probability distributions {source: {value: p}} into one FieldEvidence.
    Sources with an empty distribution abstain and don't dilute the others.
    """
    weights = weights or SOURCE_WEIGHTS
    active = {s: d for s, d in distributions.items() if d}
    if not active:
        return FieldEvidence(value=None, confidence=0.0, source="none", margin=0.0)
    total_w = sum(weights.get(s, 1.0) for s in active)
    scores: Dict[str, float] = {}
    contrib: Dict[str, Dict[str, float]] = {}
    for s, dist in active.items():
        w = weights.get(s, 1.0)
        for v, p in dist.items():
            scores[v] = scores.get(v, 0.0) + w * p / total_w
            contrib.setdefault(v, {})[s] = w * p
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_v, top_p = ranked[0]
    second_p = ranked[1][1] if len(ranked) > 1 else 0.0
    src = max(contrib[top_v].items(), key=lambda kv: kv[1])[0]
    if len(contrib[top_v]) > 1:
        src = "+".join(sorted(contrib[top_v]))
    return FieldEvidence(value=top_v, confidence=round(min(1.0, top_p), 4), source=src, margin=round(top_p - second_p, 4))


def ranked_shares(distributions: Dict[str, Dict[str, float]], weights: Optional[Dict[str, float]] = None) -> List[tuple]:
    """Fused evidence per value as a normalised share (sums to 1), best first."""
    weights = weights or SOURCE_WEIGHTS
    scores: Dict[str, float] = {}
    for s, dist in distributions.items():
        for v, p in (dist or {}).items():
            scores[v] = scores.get(v, 0.0) + weights.get(s, 1.0) * p
    total = sum(scores.values())
    if total <= 0:
        return []
    return sorted(((v, round(sc / total, 4)) for v, sc in scores.items()), key=lambda kv: kv[1], reverse=True)


def arbitrate_field(evidences: List[FieldEvidence], source_weights: Optional[Dict[str, float]] = None) -> FieldEvidence:
    """Backwards-compatible wrapper: fuse single-value evidences from several sources."""
    dists: Dict[str, Dict[str, float]] = {}
    for ev in evidences:
        if ev.value is not None and ev.confidence > 0.0:
            d = dists.setdefault(ev.source, {})
            d[ev.value] = max(d.get(ev.value, 0.0), ev.confidence)
    return fuse(dists, source_weights)


def infer_scope(
    entity_decision: FieldEvidence,
    signals: QuerySignals,
    explicit_entities: List[str],
    multi_entities: List[str],
    aspect: Optional[str],
    context_entity: Optional[str],
    llm_available: bool = False,
) -> FieldEvidence:
    """
    Precedence:
      1. Multi-entity comparison (>=2 distinct entities + comparison language)
      2. Company aspects (contact / leadership / recognition / clients)
      3. Catalog request with no residual domain content
      4. Explicitly named entity
      5. Pronoun / elliptical follow-up resolved from conversation context
      6. Out-of-domain
      7. Semantically resolved entity (confidence carried; accept/LLM/clarify decided by caller)
      8. Nothing usable -> None (clarification)
    """
    if len(multi_entities) >= 2 and (signals.comparison or len(explicit_entities) >= 2):
        return FieldEvidence(MULTI_ENTITY, 0.95, "rules")

    if signals.catalog_request and not signals.residue and not explicit_entities:
        return FieldEvidence(signals.catalog_scope or ALL, 0.95, "rules")

    if aspect in COMPANY_ASPECT_ENTITY and not explicit_entities:
        return FieldEvidence(CLIENTS_SCOPE if aspect == "CLIENTS_CASE_STUDIES" else SINGLE_ENTITY, 0.90, "rules")

    if explicit_entities:
        return FieldEvidence(SINGLE_ENTITY, entity_decision.confidence, entity_decision.source)

    if context_entity:
        return FieldEvidence(SINGLE_ENTITY, 0.90, "context")

    if signals.unknown_product:
        return FieldEvidence(UNKNOWN_ENTITY, 0.85, "rules")

    # Keyword OOD detection is only trusted when nothing semantic points into the catalog
    if signals.ood_detector and not signals.entity_evidence:
        return FieldEvidence(OUT_OF_DOMAIN, 0.90, "rules")

    if entity_decision.value and (entity_decision.confidence >= WEAK_ENTITY_FLOOR or llm_available):
        return FieldEvidence(SINGLE_ENTITY, entity_decision.confidence, entity_decision.source)

    if signals.residue and not signals.has_pronoun:
        # Nothing in the catalog resembles the query's content
        return FieldEvidence(OUT_OF_DOMAIN, 0.70, "bge")

    return FieldEvidence(None, 0.0, "none")


def arbitrate(
    entity_dists: Dict[str, Dict[str, float]],
    aspect_dists: Dict[str, Dict[str, float]],
    intent: FieldEvidence,
    signals: QuerySignals,
    explicit_entities: List[str],
    multi_entities: List[str],
    context_entity: Optional[str] = None,
    llm_verdict: Optional[Dict[str, Any]] = None,
    query_text: str = "",
    llm_available: bool = False,
    company_level: Optional[set] = None,
) -> SemanticDecision:
    trace: List[str] = []
    company_level = company_level or set(COMPANY_ASPECT_ENTITY.values()) | {"company_info"}
    domain_explicit = [e for e in explicit_entities if e not in company_level]
    entity_dists = {k: dict(v) for k, v in entity_dists.items()}
    aspect_dists = {k: dict(v) for k, v in aspect_dists.items()}

    if llm_verdict:
        if llm_verdict.get("entity"):
            entity_dists["llm"] = {llm_verdict["entity"]: float(llm_verdict.get("confidence", 0.8))}
        if llm_verdict.get("aspect"):
            aspect_dists["llm"] = {llm_verdict["aspect"]: float(llm_verdict.get("aspect_confidence", 0.8))}

    aspect = fuse(aspect_dists)
    if aspect.value is None:
        aspect = FieldEvidence("OVERVIEW", 0.5, "default", 0.0)
    # Aspect confidence comes from evidence sources only; the OVERVIEW prior decides ties but is not evidence,
    # so an aspect chosen by default reports low confidence instead of borrowing certainty from elsewhere.
    aspect_candidates = ranked_shares({s: d for s, d in aspect_dists.items() if s != "prior"})
    if not aspect_candidates:
        aspect_candidates = [("OVERVIEW", DEFAULT_ASPECT_CONFIDENCE)]
    shares = dict(aspect_candidates)
    own = shares.get(aspect.value, 0.0) if aspect.value != "OVERVIEW" or shares.get("OVERVIEW") else min(
        DEFAULT_ASPECT_CONFIDENCE, 1.0 - (aspect_candidates[0][1] if aspect_candidates[0][0] != "OVERVIEW" else 0.0))
    rival = max((p for v, p in aspect_candidates if v != aspect.value), default=0.0)
    aspect = FieldEvidence(aspect.value, round(own, 4), aspect.source, round(own - rival, 4))

    # Context carries the entity for pronoun / elliptical follow-ups that name nothing new
    # Naming the company ("how do I approach CittaAI") addresses the company, not the offering under discussion
    # An explicitly worded company question ("who is the founder?") is about CittaAI, not the offering in context
    company_question = aspect.value in COMPANY_ASPECT_ENTITY and "rules" in (aspect.source or "") and not signals.has_pronoun
    use_context = bool(context_entity) and not explicit_entities and not company_question and not (signals.company_reference and not signals.has_pronoun) and (
        signals.has_pronoun or not signals.residue or not signals.entity_evidence)
    if use_context:
        entity_dists = {"context": {context_entity: 0.95}}
        trace.append(f"context entity '{context_entity}' carried (pronoun={signals.has_pronoun}, residue={signals.residue})")

    entity = fuse(entity_dists)

    # Company aspects own their entity unless a catalog entity was named explicitly
    if aspect.value in COMPANY_ASPECT_ENTITY and not domain_explicit and not use_context:
        owner = COMPANY_ASPECT_ENTITY[aspect.value]
        named = [e for e in explicit_entities if e in company_level and e != "company_info"]
        entity = FieldEvidence(named[0] if named else owner, max(aspect.confidence, 0.8), "aspect", 1.0)
        trace.append(f"company aspect {aspect.value} -> {entity.value}")

    scope = infer_scope(entity, signals, domain_explicit if aspect.value in COMPANY_ASPECT_ENTITY else explicit_entities,
                        multi_entities, aspect.value, context_entity if use_context else None, llm_available)

    entities: List[str] = []
    needs_clarification = False
    needs_llm = False

    # A named case study is a single-entity question, not the company-wide client list
    if scope.value == CLIENTS_SCOPE and entity.value and entity.value in company_level:
        scope = FieldEvidence(SINGLE_ENTITY, scope.confidence, scope.source)

    if signals.unresolved_pair and scope.value != MULTI_ENTITY:
        needs_clarification = True
        scope = FieldEvidence(None, 0.0, "none")
        trace.append("'both' refers to two offerings but no pair is known -> clarification")
    elif scope.value == MULTI_ENTITY:
        entities = multi_entities[:3]
        entity = FieldEvidence(entities[0], 0.95, "rules", 0.5)
        # A comparison is an overview comparison unless the question explicitly asks about one part
        if "rules" not in (aspect.source or "") and "llm" not in (aspect.source or ""):
            aspect = FieldEvidence("OVERVIEW", 0.9, "multi_default", 0.5)
    elif scope.value in CATALOG_SCOPES or scope.value in (OUT_OF_DOMAIN, UNKNOWN_ENTITY):
        entity = FieldEvidence(None, 0.0, "none", 0.0)
        if scope.value in CATALOG_SCOPES:
            aspect = FieldEvidence("CATALOG_LIST", scope.confidence, "scope", 1.0)
        if scope.value == UNKNOWN_ENTITY:
            trace.append(f"unknown product name '{signals.unknown_product}' -> not mapped to a neighbouring entity")
    elif scope.value is None:
        needs_clarification = True
        trace.append("no usable entity, scope or context -> clarification")
    elif scope.value == SINGLE_ENTITY and entity.source == "context":
        # Carried without a pronoun onto a message with its own content: it may be a follow-up
        # ("who is the target audience?") or an unrelated request ("can you book me a flight?").
        if not signals.has_pronoun and signals.residue:
            if llm_verdict is None and llm_available:
                needs_llm = True
                trace.append(f"context '{entity.value}' carried without a pronoun -> LLM verification")
            elif llm_verdict is not None and "entity" in llm_verdict and llm_verdict.get("entity") is None and llm_verdict.get("out_of_domain"):
                scope = FieldEvidence(OUT_OF_DOMAIN, 0.8, "llm")
                entity = FieldEvidence(None, 0.0, "none", 0.0)
                trace.append("LLM judged the message unrelated to the conversation's offering -> out of domain")
    elif scope.value == SINGLE_ENTITY and entity.source not in ("aspect", "context"):
        confident = entity.confidence >= ACCEPT_CONFIDENCE and (entity.margin or 0) >= ACCEPT_MARGIN
        # No offering was named and no context applies: the choice rests on embedding similarity alone,
        # which is confidently wrong often enough (dev) that it is verified whenever an LLM is available.
        if llm_verdict is None and llm_available and (not confident or entity.source == "bge"):
            # Ambiguous, or no offering was named and no context applies (similarity alone is confidently
            # wrong often enough on dev that it is verified whenever an LLM is available).
            needs_llm = True
            trace.append(f"entity (conf={entity.confidence}, margin={entity.margin}, source={entity.source}) -> LLM adjudication")
        elif llm_verdict is not None and "entity" in llm_verdict and llm_verdict.get("entity") is None and llm_verdict.get("out_of_domain"):
            # The adjudicator's out-of-domain / ambiguity verdicts hold whatever the embedding confidence was
            if explicit_entities:
                needs_clarification = True
                trace.append("LLM judged the request outside the named offering's scope -> clarification")
            else:
                scope = FieldEvidence(OUT_OF_DOMAIN, 0.8, "llm")
                entity = FieldEvidence(None, 0.0, "none", 0.0)
                trace.append("LLM judged the request out of domain")
        elif llm_verdict is not None and llm_verdict.get("ambiguous") and "entity" in llm_verdict:
            needs_clarification = True
            trace.append("LLM judged the query genuinely ambiguous -> clarification")
        elif not confident and (entity.confidence < FALLBACK_CONFIDENCE or (entity.margin or 0) < FALLBACK_MARGIN):
            needs_clarification = True
            trace.append(f"low confidence entity (conf={entity.confidence}, margin={entity.margin}) -> clarification")

    overall = entity.confidence if entity.value else scope.confidence
    return SemanticDecision(
        entity=entity,
        intent=intent,
        aspect=aspect,
        scope=scope,
        entities=entities,
        overall_confidence=round(overall, 4),
        needs_clarification=needs_clarification,
        needs_llm_adjudication=needs_llm,
        llm_invoked=llm_verdict is not None,
        aspect_candidates=aspect_candidates,
        raw_evidence={"entity": entity_dists, "aspect": aspect_dists, "llm": llm_verdict,
                      "signals": signals.__dict__, "explicit": explicit_entities, "multi": multi_entities},
        original_query=query_text,
        diagnostic_trace=trace,
    )
