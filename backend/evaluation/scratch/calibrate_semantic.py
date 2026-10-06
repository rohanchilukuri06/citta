"""Fit BGE temperature / relevance floors on the DEV split only."""
import sys, json, logging, re
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
logging.disable(logging.WARNING)
import query_intelligence_engine as qie
eng = qie.QueryIntelligenceEngine(enable_llm=False)
idx = eng.index
items = [i for i in json.load(open(Path(__file__).resolve().parents[1] / "semantic_eval_set.json", encoding="utf-8"))["items"] if i["split"] == "dev"]
rows = []
for it in items:
    if it.get("ctx") or "multi" in it: continue
    q = re.sub(r"\b(cittaai|citta ai|citta)('s)?\b", " ", it["q"], flags=re.I)
    e = idx.encode_query(q)
    sims = idx.exemplar_emb @ e
    n = len(idx.entity_ids); sc = np.full(n, -1.0)
    for i in range(n):
        s = np.sort(sims[idx.exemplar_owner == i])[::-1]; sc[i] = 0.7*s[0] + 0.3*s[:3].mean()
    asims = idx.aspect_emb @ e
    asc = np.array([asims[idx.aspect_owner == j].max() for j in range(len(idx.aspect_names))])
    rows.append((it, sc, asc))
print("in-domain top scores vs OOD/catalog:")
for it, sc, asc in rows:
    top = idx.entity_ids[int(sc.argmax())]
    ok = top in it["ent"]
    print(f"  {'OK ' if ok else 'BAD'} top={sc.max():.3f} gap={np.sort(sc)[-1]-np.sort(sc)[-2]:.3f} {top:22s} asp_top={asc.max():.3f} {idx.aspect_names[int(asc.argmax())]:20s} exp={it.get('aspect')} | {it['q'][:60]}")
for T in [0.01, 0.015, 0.02, 0.025, 0.03, 0.04]:
    pts = []
    for it, sc, _ in rows:
        if not it["ent"]: continue
        p = np.exp((sc - sc.max())/T); p /= p.sum()
        k = int(p.argmax()); pts.append((p[k], idx.entity_ids[k] in it["ent"]))
    bins = np.linspace(0, 1, 6); ece = 0
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = [(c, o) for c, o in pts if lo <= c < hi or (hi == 1 and c == 1)]
        if m: ece += abs(np.mean([c for c, _ in m]) - np.mean([o for _, o in m])) * len(m) / len(pts)
    print(f"T={T}: acc={np.mean([o for _, o in pts]):.3f} mean_conf={np.mean([c for c, _ in pts]):.3f} ECE={ece:.3f}")
