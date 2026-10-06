"""
Fit the aspect-adjudication thresholds on the DEV split only.

For every dev question with an aspect label and an entity-directed scope, record the arbitrated aspect
(no LLM) with its confidence/margin, and the LLM adjudicator's aspect. Then simulate each
(confidence, margin) threshold pair: below either threshold the LLM aspect is used, otherwise the
arbitrated one. Reports aspect accuracy vs. how often the LLM would be called.

Usage: python evaluation/aspect_threshold_sweep.py
"""

import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
DATASET = Path(__file__).resolve().parent / "semantic_eval_set.json"
OUT = Path(__file__).resolve().parent / "reports" / "aspect_threshold_sweep.json"


def main():
    logging.disable(logging.WARNING)
    import config
    import query_intelligence_engine as qie
    from semantic_chat_pipeline import ConversationState

    items = [i for i in json.loads(DATASET.read_text(encoding="utf-8"))["items"]
             if i["split"] == "dev" and i.get("aspect") and "SINGLE_ENTITY" in i["scope"] and i.get("clarify") != "must"]

    plain = qie.QueryIntelligenceEngine(enable_llm=False)
    judged = qie.QueryIntelligenceEngine(enable_llm=True)
    config.SEMANTIC_ASPECT_ACCEPT_CONFIDENCE, config.SEMANTIC_ASPECT_ACCEPT_MARGIN = 1.01, 1.01  # always adjudicate

    rows = []
    for it in items:
        state = ConversationState(active_entity=it.get("ctx"))
        a = plain.analyze_query(it["q"], active_entity=it.get("ctx"), context=state)
        b = judged.analyze_query(it["q"], active_entity=it.get("ctx"), context=state)
        rows.append({"id": it["id"], "q": it["q"], "gold": it["aspect"], "arbitrated": a.aspect.value,
                     "conf": a.aspect.confidence, "margin": a.aspect.margin or 0.0,
                     "llm": b.aspect.value if b.aspect_llm_invoked else None,
                     "entity_directed": a.scope.value in ("SINGLE_ENTITY", "MULTI_ENTITY") and a.entity.source != "aspect"})

    grid = []
    for c in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        for m in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
            correct = calls = 0
            for r in rows:
                use_llm = r["entity_directed"] and r["llm"] and (r["conf"] < c or r["margin"] < m)
                calls += int(bool(use_llm))
                correct += int((r["llm"] if use_llm else r["arbitrated"]) in r["gold"])
            grid.append({"conf": c, "margin": m, "aspect_acc": round(correct / len(rows), 3), "llm_rate": round(calls / len(rows), 3)})
    base = sum(r["arbitrated"] in r["gold"] for r in rows) / len(rows)
    always = sum((r["llm"] or r["arbitrated"]) in r["gold"] for r in rows) / len(rows)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"n": len(rows), "no_llm_acc": base, "always_llm_acc": always, "grid": grid, "rows": rows}, indent=2), encoding="utf-8")
    print(f"dev aspect items: {len(rows)} | no LLM: {base:.3f} | always LLM: {always:.3f}")
    for g in sorted(grid, key=lambda g: (-g["aspect_acc"], g["llm_rate"]))[:12]:
        print(g)


if __name__ == "__main__":
    main()
