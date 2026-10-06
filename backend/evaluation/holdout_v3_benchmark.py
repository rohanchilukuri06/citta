"""
Holdout v3 benchmark: stage-by-stage evaluation of the production decision path on an unseen dataset.

The dataset (semantic_holdout_v3.json) was written by an independent agent that saw only the
authoritative catalog content, never this codebase, its exemplars, tests or earlier datasets.

Every query goes through SemanticChatPipeline.decide() — the same call /api/chat makes — and the
routed operation is executed against the registry to check evidence availability. Stages are graded
in pipeline order and the FIRST failing stage is reported per query:

  entity -> aspect -> scope -> canonicalization -> operation -> arguments -> evidence

Intent has no gold labels in v3 (the production path routes on entity/aspect/scope, not intent), so
intent accuracy is reported as not measured rather than guessed.

Decision metrics only. Final-answer quality is measured separately by answer_eval_v3.py.

Usage:
  python evaluation/holdout_v3_benchmark.py --llm on
  python evaluation/holdout_v3_benchmark.py --llm off
"""

import argparse
import hashlib
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
EVAL_DIR = Path(__file__).resolve().parent
DATASET = EVAL_DIR / "semantic_holdout_v3.json"
REPORT_DIR = EVAL_DIR / "reports"

STAGES = ["entity", "aspect", "scope", "canonicalization", "operation", "arguments", "evidence"]
LISTING_OPS = {"list_solutions", "list_products", "list_services", "list_catalog"}
DATA_OPS = {"get_product", "get_solution", "get_service", "get_company_info", "get_capabilities", "get_benefits",
            "get_target_users", "get_workflow", "get_faq", "get_pricing"}
ENTITY_COMPANY_EQUIV = {"contact_info", "company_info", "leadership_info", "awards_recognition"}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p.exists() else "missing"


ASPECT_OPS = {"CAPABILITIES": {"get_capabilities"}, "BENEFITS": {"get_benefits"}, "TARGET_USERS": {"get_target_users"},
              "WORKFLOW": {"get_workflow"}, "FAQ": {"get_faq"}, "PRICING": {"get_pricing"}, "CONTACT": {"get_contact"},
              "LEADERSHIP": {"get_leadership"}, "RECOGNITION": {"get_recognition"},
              "CLIENTS_CASE_STUDIES": {"list_case_studies", "get_case_study"}}
TYPE_OVERVIEW = {"product": "get_product", "solution": "get_solution", "service": "get_service", "company": "get_company_info"}


def implied_operations(aspects: Optional[List[str]], entities: List[str], registry: Any) -> set:
    ops = set()
    for a in aspects or []:
        ops |= ASPECT_OPS.get(a, set())
        if a == "OVERVIEW":
            ops |= {TYPE_OVERVIEW.get(str((registry.entities.get(e) or {}).get("type", "")).lower(), "") for e in entities} - {""}
    return ops


def grade(item: Dict[str, Any], decision: Any, plans: List[Any], registry: Any, executor: Any) -> Dict[str, Any]:
    exp = item["expected"]
    d = decision.to_dict()
    op = plans[0].operation_name if plans else None
    inputs = (plans[0].inputs or {}) if plans else {}
    clarified = op == "request_clarification"
    rule = exp.get("clarification", "no")
    res: Dict[str, Optional[bool]] = {s: None for s in STAGES}

    if rule == "required":
        ok = clarified
        res.update({s: ok for s in ["entity", "aspect", "scope", "canonicalization", "operation", "arguments", "operation_strict"]})
        return {**res, "decision": ok, "clarified": clarified, "first_failure": None if ok else "scope"}
    if clarified and rule == "allowed":
        res.update({s: True for s in ["entity", "aspect", "scope", "canonicalization", "operation", "arguments", "operation_strict"]})
        return {**res, "decision": True, "clarified": True, "first_failure": None}

    exp_ents = exp.get("entities") or []
    multi = exp.get("multi_entities")
    if multi:
        res["entity"] = set(multi).issubset(set(d["entities"] or []))
    elif not exp_ents:
        res["entity"] = d["entity"] is None
    else:
        res["entity"] = d["entity"] in exp_ents
    aspects = exp.get("aspects")
    res["aspect"] = True if not aspects else d["aspect"] in aspects
    res["scope"] = d["scope"] == exp["scope"] or (exp["scope"] == "NONE" and d["scope"] in (None, "NONE", "GENERAL"))
    res["canonicalization"] = all(e is None or e in registry.entities for e in [d["entity"]] + list(d["entities"] or []))
    # The gold operation is the one the labeller wrote; the direct operation of any gold-accepted aspect is
    # equally correct (gold aspects ["OVERVIEW","CAPABILITIES"] with op get_solution must accept get_capabilities).
    res["operation_strict"] = op == exp["operation"]
    res["operation"] = res["operation_strict"] or op in implied_operations(aspects, exp_ents, registry)
    if op in DATA_OPS and op != "get_company_info" and not multi:
        res["arguments"] = inputs.get("entity_id") in (exp_ents or [None])
    elif multi:
        res["arguments"] = set(multi).issubset({(p.inputs or {}).get("entity_id") for p in plans})
    else:
        res["arguments"] = True
    if op in DATA_OPS | {"get_contact", "get_leadership", "get_recognition", "list_case_studies", "get_case_study"} and res["operation"]:
        ev = executor.execute(plans[0])
        res["evidence"] = ev.available == bool(exp.get("knowledge_available", True))
    decision_ok = all(res[s] for s in ["entity", "aspect", "scope", "canonicalization", "operation", "arguments"])
    first = next((s for s in STAGES if res[s] is False), None)
    return {**res, "decision": decision_ok, "clarified": clarified, "first_failure": first}


def calibration(points, bins=5):
    if not points:
        return {"ece": None, "bins": []}
    edges = [i / bins for i in range(bins + 1)]
    ece, table = 0.0, []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = [(c, ok) for c, ok in points if lo <= c < hi or (hi == 1.0 and c == 1.0)]
        if m:
            ac, acc = sum(c for c, _ in m) / len(m), sum(o for _, o in m) / len(m)
            ece += abs(ac - acc) * len(m) / len(points)
            table.append({"range": f"{lo:.1f}-{hi:.1f}", "n": len(m), "avg_conf": round(ac, 3), "accuracy": round(acc, 3)})
    return {"ece": round(ece, 4), "bins": table}


def run(llm_mode: str, dataset: Path = DATASET) -> Dict[str, Any]:
    logging.disable(logging.WARNING)
    import config
    import query_intelligence_engine as qie
    from knowledge_operation_executor import get_operation_executor
    from knowledge_registry import get_registry
    from knowledge_tool_router import KnowledgeToolRouter
    from semantic_chat_pipeline import ConversationState, SemanticChatPipeline

    items = json.loads(dataset.read_text(encoding="utf-8"))["items"]
    engine = qie.QueryIntelligenceEngine(enable_llm=(llm_mode == "on"))
    pipeline = SemanticChatPipeline(engine=engine, router=KnowledgeToolRouter())
    registry, executor = get_registry(), get_operation_executor()

    rows, lat = [], []
    for it in items:
        ctx = it.get("context") or {}
        state = ConversationState(active_entity=ctx.get("active_entity"), active_entities=list(ctx.get("active_entities") or []))
        t0 = time.perf_counter()
        decision, plans = pipeline.decide(it["query"], state)
        lat.append((time.perf_counter() - t0) * 1000)
        g = grade(it, decision, plans, registry, executor)
        d = decision.to_dict()
        calls = decision.raw_evidence.get("llm_calls", {})
        rows.append({"id": it["id"], "category": it["category"], "query": it["query"], "context": ctx or None,
                     "expected": it["expected"], "grade": g,
                     "got": {"entity": d["entity"], "entities": d["entities"], "intent": d["intent"], "aspect": d["aspect"],
                             "scope": d["scope"], "operation": plans[0].operation_name,
                             "operation_inputs": {k: v for k, v in (plans[0].inputs or {}).items() if k != "options"},
                             "entity_confidence": d["entity_confidence"], "aspect_confidence": d["aspect_confidence"],
                             "decision_confidence": d["decision_confidence"], "entity_margin": decision.entity.margin,
                             "aspect_top2": d["aspect_top2"], "aspect_margin": d["aspect_margin"],
                             "llm_calls": calls, "trace": d["diagnostic_trace"]}})

    n = len(rows)
    pct = lambda k: round(100 * sum(1 for r in rows if r["grade"][k]) / n, 1)
    evid = [r for r in rows if r["grade"]["evidence"] is not None]
    answerable = [r for r in rows if r["grade"]["clarified"] is False]
    calls = [r["got"]["llm_calls"] for r in rows]
    res = {
        "manifest": {
            "dataset": dataset.name, "dataset_sha": _sha(dataset), "n": n, "llm_mode": llm_mode,
            "llm_provider": config.LLM_PROVIDER if llm_mode == "on" else None,
            "llm_model": config.MODEL_NAME if llm_mode == "on" else None,
            "llm_fallback": getattr(config, "LLM_FALLBACK_PROVIDER", None) if llm_mode == "on" else None,
            "embedding_model": config.EMBEDDING_MODEL,
            "aspect_thresholds": [config.SEMANTIC_ASPECT_ACCEPT_CONFIDENCE, config.SEMANTIC_ASPECT_ACCEPT_MARGIN],
            "code_sha": {f: _sha(ROOT_DIR / f) for f in ["query_intelligence_engine.py", "semantic_arbitration.py",
                                                         "semantic_chat_pipeline.py", "knowledge_tool_router.py", "knowledge_operation_executor.py"]},
            "git_head": subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT_DIR, capture_output=True, text=True).stdout.strip(),
        },
        "accuracy_pct": {
            "entity": pct("entity"), "intent": "not measured (no gold intent labels)", "aspect": pct("aspect"),
            "scope": pct("scope"), "canonicalization": pct("canonicalization"), "operation": pct("operation"),
            "operation_strict_label_match": round(100 * sum(1 for r in rows if r["grade"].get("operation_strict", r["grade"]["operation"])) / n, 1),
            "arguments": pct("arguments"), "full_decision": pct("decision"),
            "evidence_availability": round(100 * sum(r["grade"]["evidence"] for r in evid) / len(evid), 1) if evid else None,
        },
        "confidently_wrong_decision_conf": sum(1 for r in rows if not r["grade"]["decision"] and not r["grade"]["clarified"] and r["got"]["decision_confidence"] >= 0.8),
        "confidently_wrong_entity_conf_legacy": sum(1 for r in rows if not r["grade"]["decision"] and not r["grade"]["clarified"] and r["got"]["entity_confidence"] >= 0.8),
        "calibration_decision_conf": calibration([(min(1, r["got"]["decision_confidence"]), r["grade"]["decision"]) for r in answerable]),
        "calibration_entity_conf_legacy": calibration([(min(1, r["got"]["entity_confidence"]), r["grade"]["decision"]) for r in answerable if r["got"]["entity"]]),
        "llm": {
            "entity_adjudication_rate_pct": round(100 * sum(c.get("entity_attempted", False) for c in calls) / n, 1),
            "aspect_adjudication_rate_pct": round(100 * sum(c.get("aspect_attempted", False) for c in calls) / n, 1),
            "any_llm_rate_pct": round(100 * sum(c.get("entity_attempted", False) or c.get("aspect_attempted", False) for c in calls) / n, 1),
            "success_rate_pct": (round(100 * sum(c.get("entity_ok", False) + c.get("aspect_ok", False) for c in calls)
                                       / max(1, sum(c.get("entity_attempted", False) + c.get("aspect_attempted", False) for c in calls)), 1)),
        },
        "latency_ms": {"p50": round(sorted(lat)[n // 2], 1), "p95": round(sorted(lat)[int(n * 0.95) - 1], 1)},
        "catalog_leakage": sum(1 for r in rows if r["expected"]["scope"] in ("SINGLE_ENTITY", "MULTI_ENTITY") and r["got"]["operation"] in LISTING_OPS),
        "ood_leakage": sum(1 for r in rows if r["expected"]["scope"] == "OUT_OF_DOMAIN" and r["got"]["operation"] not in ("decline_out_of_domain", "request_clarification")),
        "unknown_product_substituted": sum(1 for r in rows if r["expected"]["scope"] == "UNKNOWN_ENTITY" and r["got"]["entity"]),
        "clarification_rate_pct": round(100 * sum(r["grade"]["clarified"] for r in rows) / n, 1),
        "first_failure_counts": {s: sum(1 for r in rows if r["grade"]["first_failure"] == s) for s in STAGES},
        "by_category": {},
        "failures": [r for r in rows if not r["grade"]["decision"] or r["grade"]["evidence"] is False],
    }
    for c in sorted({r["category"] for r in rows}):
        rs = [r for r in rows if r["category"] == c]
        res["by_category"][c] = {"n": len(rs), "decision_pct": round(100 * sum(r["grade"]["decision"] for r in rs) / len(rs), 1)}
    write_report(res, rows)
    return res


def write_report(res, rows):
    REPORT_DIR.mkdir(exist_ok=True)
    stem = f"{res['manifest']['dataset'].replace('semantic_', '').replace('.json', '')}_llm-{res['manifest']['llm_mode']}"
    (REPORT_DIR / f"{stem}.json").write_text(json.dumps({**res, "rows": rows}, indent=2, default=str), encoding="utf-8")
    a = res["accuracy_pct"]
    L = [f"# {res['manifest']['dataset']} — LLM {res['manifest']['llm_mode']}", "", f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')}", "",
         "## Manifest", "```json", json.dumps(res["manifest"], indent=2), "```", "", "## Decision metrics", "| Metric | Value |", "|---|---|"]
    for k, v in a.items():
        L.append(f"| {k} | {v}{'%' if isinstance(v, (int, float)) else ''} |")
    L += [f"| confidently wrong (decision conf ≥ 0.8) | {res['confidently_wrong_decision_conf']} |",
          f"| confidently wrong (legacy: entity conf ≥ 0.8) | {res['confidently_wrong_entity_conf_legacy']} |",
          f"| ECE (decision conf) | {res['calibration_decision_conf']['ece']} |",
          f"| ECE (legacy entity conf) | {res['calibration_entity_conf_legacy']['ece']} |",
          f"| LLM entity / aspect / any rate | {res['llm']['entity_adjudication_rate_pct']}% / {res['llm']['aspect_adjudication_rate_pct']}% / {res['llm']['any_llm_rate_pct']}% |",
          f"| LLM call success rate | {res['llm']['success_rate_pct']}% |",
          f"| Latency p50 / p95 | {res['latency_ms']['p50']} / {res['latency_ms']['p95']} ms |",
          f"| Catalog leakage | {res['catalog_leakage']} |", f"| OOD leakage | {res['ood_leakage']} |",
          f"| Unknown product substituted | {res['unknown_product_substituted']} |",
          f"| Clarification rate | {res['clarification_rate_pct']}% |", "",
          "## First failure stage", "| Stage | Queries |", "|---|---|"] + [f"| {s} | {c} |" for s, c in res["first_failure_counts"].items()]
    L += ["", "## By category", "| Category | n | Decision |", "|---|---|---|"] + [f"| {c} | {v['n']} | {v['decision_pct']}% |" for c, v in res["by_category"].items()]
    L += ["", "## Failures", ""]
    for f in res["failures"]:
        g, got, e = f["grade"], f["got"], f["expected"]
        stages = " · ".join(f"{s} {'PASS' if g[s] else ('FAIL' if g[s] is False else '—')}" for s in STAGES)
        L += [f"### {f['id']} ({f['category']}) — first failure: **{g['first_failure'] or 'evidence'}**",
              f"- Query: `{f['query']}`" + (f" (context: {f['context']})" if f["context"] else ""),
              f"- Expected: entity {e.get('multi_entities') or e.get('entities')}, aspect {e.get('aspects')}, scope {e['scope']}, op `{e['operation']}`, clarification {e.get('clarification')}, knowledge_available {e.get('knowledge_available')}",
              f"- Predicted: entity {got['entity']} {got['entities'] or ''}, intent {got['intent']}, aspect {got['aspect']} (2nd {got['aspect_top2']}, margin {got['aspect_margin']}), scope {got['scope']}, op `{got['operation']}` {got['operation_inputs']}",
              f"- Confidence: entity {got['entity_confidence']} (margin {got['entity_margin']}), aspect {got['aspect_confidence']}, decision {got['decision_confidence']} · LLM {got['llm_calls']}",
              f"- Stages: {stages}", f"- Gold rationale: {e.get('rationale', '')}", ""]
    (REPORT_DIR / f"{stem}.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", choices=["on", "off"], default="on")
    ap.add_argument("--dataset", default=str(DATASET), help="holdout file (default: semantic_holdout_v3.json)")
    a = ap.parse_args()
    r = run(a.llm, Path(a.dataset))
    print(json.dumps({k: r[k] for k in ["accuracy_pct", "confidently_wrong_decision_conf", "llm", "latency_ms", "catalog_leakage",
                                        "ood_leakage", "unknown_product_substituted", "first_failure_counts"]}, indent=1))
    print("ECE decision:", r["calibration_decision_conf"]["ece"])
