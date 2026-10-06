"""
Frozen semantic interpretation benchmark for CittaAI.

Grades, per query:
  - entity    : primary entity is one of the acceptable entities (or none expected)
  - scope     : SINGLE_ENTITY / MULTI_ENTITY / ALL_* / NONE
  - aspect    : which part of the entity the user asked about
  - operation : the KnowledgeToolRouter operation AND its entity input match the user's meaning
  - decision  : all of the above together (end-to-end semantic correctness)

Also reports confidence calibration (ECE + reliability bins), confidently-wrong decisions,
clarification behaviour, catalog leakage and LLM adjudication usage, and writes a manifest
(dataset hash, registry hash, code hashes, model names) so results are reproducible.

Usage:
  python evaluation/semantic_benchmark.py --split test --llm off
  python evaluation/semantic_benchmark.py --split all --llm on
"""

import argparse
import hashlib
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

EVAL_DIR = Path(__file__).resolve().parent
DATASET_PATH = EVAL_DIR / "semantic_eval_set.json"
REPORT_DIR = EVAL_DIR / "reports"

CODE_FILES = [
    "query_intelligence_engine.py", "semantic_arbitration.py", "semantic_decision.py",
    "semantic_entity_index.py", "knowledge_tool_router.py", "knowledge_operation_registry.py",
    "semantic_chat_pipeline.py", "knowledge_operation_executor.py",
]

NO_SCOPE = {None, "NONE", "GENERAL", "OUT_OF_DOMAIN"}
ENTITY_OPS = {"get_product", "get_solution", "get_service", "get_company_info", "get_capabilities",
              "get_benefits", "get_target_users", "get_workflow", "get_faq", "get_pricing"}
ASPECT_OPS = {
    "CAPABILITIES": {"get_capabilities"},
    "BENEFITS": {"get_benefits"},
    "TARGET_USERS": {"get_target_users"},
    "WORKFLOW": {"get_workflow"},
    "FAQ": {"get_faq"},
    "PRICING": {"get_pricing"},
    "OVERVIEW": {"get_product", "get_solution", "get_service", "get_company_info"},
}
COMPANY_ASPECT_OPS = {
    "CONTACT": {"get_contact"},
    "LEADERSHIP": {"get_leadership"},
    "RECOGNITION": {"get_recognition"},
    "CLIENTS_CASE_STUDIES": {"list_case_studies", "get_case_study"},
}
CATALOG_OPS = {
    "ALL": {"list_catalog", "list_solutions"},
    "ALL_SOLUTIONS": {"list_solutions"},
    "ALL_PRODUCTS": {"list_products"},
    "ALL_SERVICES": {"list_services"},
}


def _sha(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except FileNotFoundError:
        return "missing"


def build_manifest(dataset: Dict[str, Any], llm_mode: str, registry: Any) -> Dict[str, Any]:
    import config
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT_DIR, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--"] + CODE_FILES, cwd=ROOT_DIR, text=True).strip())
    except Exception:
        git_sha, dirty = "unknown", True
    return {
        "dataset_version": dataset.get("version"),
        "dataset_sha": _sha(DATASET_PATH),
        "registry_hash": getattr(registry, "registry_hash", None) or getattr(registry, "version_hash", None),
        "code_sha": {f: _sha(ROOT_DIR / f) for f in CODE_FILES},
        "git_head": git_sha,
        "working_tree_dirty": dirty,
        "embedding_model": config.EMBEDDING_MODEL,
        "llm_mode": llm_mode,
        "llm_provider": config.LLM_PROVIDER if llm_mode == "on" else None,
        "llm_model": getattr(config, "MODEL_NAME", None) if llm_mode == "on" else None,
    }


def expected_operations(item: Dict[str, Any], registry: Any) -> Optional[Set[str]]:
    """Independent specification of which operation(s) satisfy the user's meaning."""
    scopes = item["scope"]
    ops: Set[str] = set()
    if item.get("clarify") in ("ok", "must"):
        ops.add("request_clarification")
    if item.get("clarify") == "must":
        return ops
    for scope in scopes:
        if scope == "NONE":
            ops |= {"decline_out_of_domain", "request_clarification"}
        elif scope in CATALOG_OPS:
            ops |= CATALOG_OPS[scope]
        elif scope == "MULTI_ENTITY":
            ops |= {"get_product", "get_solution", "get_service"}
    if "SINGLE_ENTITY" in scopes:
        aspects = item.get("aspect")
        if aspects is None:
            ops |= ENTITY_OPS
        else:
            for a in aspects:
                ops |= ASPECT_OPS.get(a, set()) | COMPANY_ASPECT_OPS.get(a, set())
    for a in item.get("aspect") or []:
        ops |= COMPANY_ASPECT_OPS.get(a, set())
    return ops


def grade(item: Dict[str, Any], decision: Any, plans: List[Any]) -> Dict[str, Any]:
    d = decision.to_dict()
    got_ent = d["entity"]
    got_scope = d["scope"]
    got_aspect = d["aspect"]
    clarified = bool(d["needs_clarification"]) or (plans and plans[0].operation_name == "request_clarification")
    clarify_rule = item.get("clarify")
    exp_ents = item["ent"]

    if clarify_rule == "must":
        ok = clarified
        return {"entity": ok, "scope": ok, "aspect": ok, "operation": ok, "decision": ok, "clarified": clarified}
    if clarified and clarify_rule == "ok":
        return {"entity": True, "scope": True, "aspect": True, "operation": True, "decision": True, "clarified": True}

    if "multi" in item:
        entity_ok = set(item["multi"]).issubset(set(d.get("entities") or []))
    elif not exp_ents:
        entity_ok = got_ent is None or got_ent in {"company_info", "awards_recognition"} and "CLIENTS_CASE_STUDIES" in (item.get("aspect") or [])
    else:
        entity_ok = got_ent in exp_ents

    exp_scopes = item["scope"]
    scope_ok = got_scope in exp_scopes or ("NONE" in exp_scopes and got_scope in NO_SCOPE)

    aspect_ok = True if item.get("aspect") is None else got_aspect in item["aspect"]

    op_ok = False
    if plans:
        exp_ops = expected_operations(item, None)
        names = {p.operation_name for p in plans}
        op_ok = plans[0].operation_name in exp_ops
        # Entity-bearing operations must target an acceptable entity
        if op_ok and plans[0].operation_name in (ENTITY_OPS - {"get_company_info"}) | {"get_case_study"} and exp_ents and "multi" not in item:
            op_ok = plans[0].inputs.get("entity_id") in exp_ents
        if "multi" in item:
            targets = {p.inputs.get("entity_id") for p in plans}
            op_ok = set(item["multi"]).issubset(targets) and names <= (ENTITY_OPS | {"get_product", "get_solution", "get_service"})
    elif "NONE" in exp_scopes:
        op_ok = True

    return {
        "entity": entity_ok, "scope": scope_ok, "aspect": aspect_ok, "operation": op_ok,
        "decision": entity_ok and scope_ok and aspect_ok and op_ok, "clarified": clarified,
    }


def calibration(points: List[tuple], bins: int = 5) -> Dict[str, Any]:
    """Expected Calibration Error over (confidence, correct) pairs."""
    if not points:
        return {"ece": None, "bins": []}
    edges = [i / bins for i in range(bins + 1)]
    table, ece = [], 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        members = [(c, ok) for c, ok in points if (lo <= c < hi) or (hi == 1.0 and c == 1.0)]
        if not members:
            continue
        avg_c = sum(c for c, _ in members) / len(members)
        acc = sum(1 for _, ok in members if ok) / len(members)
        ece += abs(avg_c - acc) * len(members) / len(points)
        table.append({"range": f"{lo:.1f}-{hi:.1f}", "n": len(members), "avg_conf": round(avg_c, 3), "accuracy": round(acc, 3)})
    return {"ece": round(ece, 4), "bins": table}


def run(split: str, llm_mode: str) -> Dict[str, Any]:
    logging.disable(logging.WARNING)
    from knowledge_registry import get_registry
    from knowledge_tool_router import KnowledgeToolRouter
    import query_intelligence_engine as qie

    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    items = [it for it in dataset["items"] if split == "all" or it["split"] == split]

    provider = None
    if llm_mode == "on":
        import config
        from llm_provider import get_llm_provider
        provider = get_llm_provider(config.LLM_PROVIDER, vars(config))
    engine = qie.QueryIntelligenceEngine(provider=provider, enable_llm=(llm_mode == "on"))
    # Same decision entry point as production /api/chat (SemanticChatPipeline.decide)
    from semantic_chat_pipeline import SemanticChatPipeline, ConversationState
    pipeline = SemanticChatPipeline(engine=engine, router=KnowledgeToolRouter())
    registry = get_registry()

    rows, calib_points = [], []
    totals = {k: 0 for k in ["entity", "scope", "aspect", "operation", "decision"]}
    by_style: Dict[str, Dict[str, int]] = {}
    llm_invoked = llm_requested = leakage = confident_wrong = clarified_n = 0
    latencies = []

    for it in items:
        t0 = time.perf_counter()
        state = ConversationState(active_entity=it.get("ctx"), active_entities=list(it.get("ctx_entities") or ([it["ctx"]] if it.get("ctx") else [])))
        decision, plans = pipeline.decide(it["q"], state)
        latencies.append((time.perf_counter() - t0) * 1000)
        g = grade(it, decision, plans)

        for k in totals:
            totals[k] += int(g[k])
        s = by_style.setdefault(it["style"], {"n": 0, "decision": 0, "entity": 0})
        s["n"] += 1
        s["decision"] += int(g["decision"])
        s["entity"] += int(g["entity"])

        llm_invoked += int(decision.llm_invoked)
        llm_requested += int(decision.needs_llm_adjudication or decision.llm_invoked)
        clarified_n += int(g["clarified"])
        if it["ent"] and "multi" not in it and plans and plans[0].operation_name in {"list_solutions", "list_products", "list_services", "list_catalog"}:
            leakage += 1
        conf = float(decision.entity.confidence if decision.entity.value else decision.overall_confidence)
        if not g["clarified"] and it.get("clarify") != "must":
            calib_points.append((min(1.0, conf), g["decision"]))
            if not g["decision"] and conf >= 0.80:
                confident_wrong += 1

        rows.append({
            "id": it["id"], "style": it["style"], "q": it["q"], "ctx": it.get("ctx"),
            "expected": {"ent": it["ent"], "scope": it["scope"], "aspect": it.get("aspect"), "clarify": it.get("clarify")},
            "got": {"ent": decision.entity.value, "entities": decision.entities, "scope": decision.scope.value,
                    "aspect": decision.aspect.value, "conf": round(conf, 3), "margin": decision.entity.margin,
                    "source": decision.entity.source, "clarify": decision.needs_clarification,
                    "llm": decision.llm_invoked, "op": plans[0].operation_name if plans else None,
                    "op_entity": plans[0].inputs.get("entity_id") if plans else None},
            "grade": g,
        })

    n = len(items)
    pct = lambda x: round(100.0 * x / n, 1) if n else 0.0
    res = {
        "manifest": build_manifest(dataset, llm_mode, registry),
        "split": split, "n": n,
        "accuracy_pct": {k: pct(v) for k, v in totals.items()},
        "catalog_leakage": leakage,
        "confidently_wrong": confident_wrong,
        "clarification_rate_pct": pct(clarified_n),
        "llm_requested_pct": pct(llm_requested),
        "llm_invoked_pct": pct(llm_invoked),
        "calibration": calibration(calib_points),
        "latency_ms_p50": round(sorted(latencies)[n // 2], 1) if n else None,
        "by_style": {k: {"n": v["n"], "decision_pct": round(100 * v["decision"] / v["n"], 1), "entity_pct": round(100 * v["entity"] / v["n"], 1)} for k, v in sorted(by_style.items())},
        "failures": [r for r in rows if not r["grade"]["decision"]],
    }
    write_report(res, rows)
    return res


def write_report(res: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    stem = f"semantic_{res['split']}_llm-{res['manifest']['llm_mode']}"
    (REPORT_DIR / f"{stem}.json").write_text(json.dumps({**res, "rows": rows}, indent=2), encoding="utf-8")
    acc = res["accuracy_pct"]
    lines = [
        f"# Semantic Benchmark — split `{res['split']}`, LLM {res['manifest']['llm_mode']}",
        "", f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')} · {res['n']} queries", "",
        "## Manifest", "```json", json.dumps(res["manifest"], indent=2), "```", "",
        "## Results", "| Metric | Value |", "|---|---|",
        f"| End-to-end decision accuracy | **{acc['decision']}%** |",
        f"| Entity accuracy | {acc['entity']}% |", f"| Scope accuracy | {acc['scope']}% |",
        f"| Aspect accuracy | {acc['aspect']}% |", f"| Operation accuracy | {acc['operation']}% |",
        f"| Catalog leakage | {res['catalog_leakage']} |",
        f"| Confidently wrong (conf ≥ 0.80) | {res['confidently_wrong']} |",
        f"| ECE (5 bins) | {res['calibration']['ece']} |",
        f"| Clarification rate | {res['clarification_rate_pct']}% |",
        f"| LLM adjudication requested / invoked | {res['llm_requested_pct']}% / {res['llm_invoked_pct']}% |",
        f"| Latency p50 | {res['latency_ms_p50']} ms |", "",
        "## Reliability", "| Confidence | n | Avg conf | Accuracy |", "|---|---|---|---|",
    ] + [f"| {b['range']} | {b['n']} | {b['avg_conf']} | {b['accuracy']} |" for b in res["calibration"]["bins"]] + [
        "", "## By style", "| Style | n | Decision | Entity |", "|---|---|---|---|",
    ] + [f"| {k} | {v['n']} | {v['decision_pct']}% | {v['entity_pct']}% |" for k, v in res["by_style"].items()] + [
        "", "## Failures", "| id | query | expected | got |", "|---|---|---|---|",
    ] + [
        f"| {f['id']} | {f['q']} | {f['expected']['ent'] or '-'} / {f['expected']['scope']} / {f['expected']['aspect'] or '*'} | "
        f"{f['got']['ent']} {f['got']['entities'] or ''} / {f['got']['scope']} / {f['got']['aspect']} → `{f['got']['op']}`({f['got']['op_entity']}) conf={f['got']['conf']} |"
        for f in res["failures"]
    ]
    (REPORT_DIR / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test", "test2", "all"], default="all")
    ap.add_argument("--llm", choices=["on", "off"], default="off")
    args = ap.parse_args()
    r = run(args.split, args.llm)
    print(json.dumps({k: r[k] for k in ["split", "n", "accuracy_pct", "catalog_leakage", "confidently_wrong",
                                         "clarification_rate_pct", "llm_requested_pct", "llm_invoked_pct", "latency_ms_p50"]}, indent=2))
    print("ECE:", r["calibration"]["ece"])
