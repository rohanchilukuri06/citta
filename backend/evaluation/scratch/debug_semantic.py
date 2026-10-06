"""Print per-query evidence for semantic decisions (dev debugging aid)."""
import sys, json, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
logging.disable(logging.WARNING)
import query_intelligence_engine as qie
eng = qie.QueryIntelligenceEngine(enable_llm=False)
for q in sys.argv[1:]:
    ctx = None
    if "||" in q:
        ctx, q = q.split("||", 1)
    d = eng.analyze_query(q, active_entity=ctx)
    r = d.raw_evidence
    prim, matched = eng._classify_semantic_aspect(q, "UNKNOWN")
    print(f"\n### {q}  (ctx={ctx})")
    print(f"  -> ent={d.entity.value} conf={d.entity.confidence} m={d.entity.margin} src={d.entity.source} | scope={d.scope.value} | aspect={d.aspect.value}({d.aspect.source},{d.aspect.confidence}) clar={d.needs_clarification}")
    print("  signals:", r["signals"]); print("  explicit:", r["explicit"], "multi:", r["multi"])
    print("  entity dists:", {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in r["entity"].items()})
    print("  bge ranked:", r["bge_ranked"])
    print("  aspect dists:", {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in r["aspect"].items()}, "rule matched:", matched)
    print("  trace:", d.diagnostic_trace)
