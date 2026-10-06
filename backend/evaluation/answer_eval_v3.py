"""
Final-answer evaluation on holdout v3 — kept separate from decision accuracy.

Answers are produced by the production path (SemanticChatPipeline.stream: Groq, falling back to Gemini).
A Gemini judge then grades each answer against the evidence the bot actually had and the gold labels.
The judge never changes the decision benchmark.

Staged by design: --sample N picks a category-stratified sample so API budget isn't spent blindly.

Usage: python evaluation/answer_eval_v3.py --sample 40
"""

import argparse
import asyncio
import json
import logging
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
EVAL_DIR = Path(__file__).resolve().parent
DATASET = EVAL_DIR / "semantic_holdout_v3.json"
REPORT_DIR = EVAL_DIR / "reports"

JUDGE_SYSTEM = (
    "You grade a company chatbot's answer. You are given the visitor question, what a correct answer should "
    "focus on (gold labels), the EVIDENCE the chatbot was given, and the chatbot's ANSWER.\n"
    "Judge only against the evidence and gold labels, not your own knowledge of the company.\n"
    "- grounded: every factual claim in the answer is supported by the evidence (clarifying questions, "
    "polite refusals and 'this information is not available' statements count as grounded).\n"
    "- unsupported_claims: list claims not supported by the evidence (empty if none).\n"
    "- entity_correct / aspect_correct / scope_correct: the answer is about the right offering(s), the right part "
    "of it, and does not drift into unrelated offerings.\n"
    "- complete: it answers what was asked as fully as the evidence allows.\n"
    "- missing_knowledge_hallucination: gold says the information is NOT available, yet the answer presents it as fact.\n"
    "- score: 1 (wrong/harmful) to 5 (correct, grounded, complete).\n"
    'Respond with JSON only: {"grounded": bool, "unsupported_claims": [str], "entity_correct": bool, '
    '"aspect_correct": bool, "scope_correct": bool, "complete": bool, "missing_knowledge_hallucination": bool, '
    '"score": int, "reason": str}'
)


def stratified(items, n, seed=7):
    by = defaultdict(list)
    for it in items:
        by[it["category"]].append(it)
    rnd = random.Random(seed)
    for v in by.values():
        rnd.shuffle(v)
    out, cats = [], sorted(by)
    while len(out) < min(n, len(items)):
        for c in cats:
            if by[c] and len(out) < n:
                out.append(by[c].pop())
    return out


async def main(sample: int, dataset: Path = DATASET, judge_name: str = "gemini"):
    logging.disable(logging.WARNING)
    import config
    from gemini_client import GeminiClient
    from knowledge_operation_executor import get_operation_executor
    from semantic_chat_pipeline import ConversationState, SemanticChatPipeline
    from server import get_rag_service

    items = stratified(json.loads(dataset.read_text(encoding="utf-8"))["items"], sample)
    rag = get_rag_service()
    pipeline = SemanticChatPipeline(provider=rag.provider)
    executor = get_operation_executor()
    if judge_name == "gemini":
        judge, judge_model = GeminiClient(model=config.GEMINI_MODEL), config.GEMINI_MODEL
    else:  # a larger model than the gpt-oss-20b generator, so the generator doesn't grade itself
        from groq_client import GroqClient
        judge, judge_model = GroqClient(), "openai/gpt-oss-120b"

    rows = []
    for it in items:
        ctx = it.get("context") or {}
        sid = f"ans-{it['id']}"
        pipeline.states[sid] = ConversationState(active_entity=ctx.get("active_entity"), active_entities=list(ctx.get("active_entities") or []))
        decision, plans = pipeline.decide(it["query"], ConversationState(active_entity=ctx.get("active_entity"), active_entities=list(ctx.get("active_entities") or [])))
        evidence = []
        if plans[0].operation_name not in ("request_clarification", "decline_out_of_domain", "semantic_search"):
            evidence = [executor.execute(p) for p in plans]
        answer, done = "", {}
        async for ch in pipeline.stream(sid, it["query"], config.MODEL_NAME):
            if ch.get("done"):
                done = ch
            else:
                answer += ch["text"]
        ev_text = "\n\n".join(e.as_context() + ("" if e.available else "\n(NO CONTENT AVAILABLE FOR THIS SECTION)") for e in evidence) or "(none — clarification, refusal or out-of-scope)"
        user = (f"QUESTION: {it['query']}\nCONTEXT: {ctx or 'none'}\nGOLD: {json.dumps(it['expected'])}\n\n"
                f"EVIDENCE:\n{ev_text[:6000]}\n\nANSWER:\n{answer[:4000]}")
        verdict, err = None, None
        for attempt in range(3):
            text, meta = await judge.generate([{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
                                              model=judge_model, temperature=0.0)
            m = re.search(r"\{.*\}", text or "", re.DOTALL)
            if m:
                try:
                    verdict = json.loads(m.group(0))
                    break
                except json.JSONDecodeError as e:
                    err = str(e)
            else:
                err = (meta or {}).get("error") or "no JSON"
            await asyncio.sleep(3 * (attempt + 1))
        rows.append({"id": it["id"], "category": it["category"], "query": it["query"], "answer": answer,
                     "operation": done.get("metrics", {}).get("operation"),
                     "generation_provider": done.get("metrics", {}).get("generation_provider"),
                     "provider_unavailable": done.get("metrics", {}).get("provider_unavailable", False),
                     "verified": done.get("verified"), "judge": verdict, "judge_error": None if verdict else err})

    judged = [r for r in rows if r["judge"]]
    frac = lambda k, neg=False: round(100 * sum((not r["judge"].get(k)) if neg else bool(r["judge"].get(k)) for r in judged) / max(1, len(judged)), 1)
    res = {
        "dataset": dataset.name, "n_sampled": len(rows), "n_judged": len(judged), "judge_model": judge_model,
        "generation_providers": {p: sum(1 for r in rows if r["generation_provider"] == p) for p in {r["generation_provider"] for r in rows}},
        "grounded_pct": frac("grounded"), "entity_correct_pct": frac("entity_correct"), "aspect_correct_pct": frac("aspect_correct"),
        "scope_correct_pct": frac("scope_correct"), "complete_pct": frac("complete"),
        "with_unsupported_claims": sum(1 for r in judged if r["judge"].get("unsupported_claims")),
        "missing_knowledge_hallucinations": sum(1 for r in judged if r["judge"].get("missing_knowledge_hallucination")),
        "mean_score": round(sum(float(r["judge"].get("score", 0)) for r in judged) / max(1, len(judged)), 2),
    }
    REPORT_DIR.mkdir(exist_ok=True)
    stem = "answer_eval_" + dataset.stem.replace("semantic_holdout_", "")
    (REPORT_DIR / f"{stem}.json").write_text(json.dumps({**res, "rows": rows}, indent=2), encoding="utf-8")
    L = [f"# Answer evaluation — {res['dataset']} (sample of {res['n_sampled']})", "", f"Generated {time.strftime('%Y-%m-%d %H:%M')}. Judge: {res['judge_model']}. "
         f"Generation providers: {res['generation_providers']}.", "", "| Metric | Value |", "|---|---|"] + \
        [f"| {k} | {v} |" for k, v in res.items() if k not in ("generation_providers",)] + ["", "## Low-scoring / flagged answers", ""]
    for r in rows:
        j = r["judge"] or {}
        if not j or j.get("score", 5) <= 3 or j.get("unsupported_claims") or j.get("missing_knowledge_hallucination"):
            L += [f"### {r['id']} ({r['category']}) — score {j.get('score')}", f"- Q: `{r['query']}` → op `{r['operation']}`",
                  f"- Answer: {r['answer'][:400].replace(chr(10), ' ')}", f"- Judge: {j.get('reason') or r['judge_error']}",
                  f"- Unsupported claims: {j.get('unsupported_claims')}", ""]
    (REPORT_DIR / f"{stem}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=40)
    ap.add_argument("--dataset", default=str(DATASET))
    ap.add_argument("--judge", choices=["gemini", "groq"], default="gemini")
    a = ap.parse_args()
    asyncio.run(main(a.sample, Path(a.dataset), a.judge))
