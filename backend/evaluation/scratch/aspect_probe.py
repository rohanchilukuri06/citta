"""Show aspect evidence (rules / BGE on frame) for DEV aspect items."""
import sys, json, logging, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
logging.disable(logging.WARNING)
import query_intelligence_engine as qie
eng = qie.QueryIntelligenceEngine(enable_llm=False)
items = [i for i in json.load(open(Path(__file__).resolve().parents[1] / "semantic_eval_set.json", encoding="utf-8"))["items"]
         if i["split"] == "dev" and i.get("aspect")]
for it in items:
    d = eng.analyze_query(it["q"], active_entity=it.get("ctx"))
    ql = it["q"].lower(); frame = ql
    for eid, _, alias in eng._explicit_mentions(ql, eng._query_signals(it["q"]).residue):
        if not alias.startswith("~") and eid not in eng.company_level:
            frame = re.sub(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", "it", frame)
    r = eng.index.rank_aspects(frame)[:2]
    ok = d.aspect.value in it["aspect"]
    print(f"{'OK ' if ok else 'BAD'} {r[0].value:14s} {r[0].score:.3f} p={r[0].prob:.2f} | 2nd {r[1].value} {r[1].score:.3f} | got {d.aspect.value:12s} exp {it['aspect']} | {frame[:60]}")
