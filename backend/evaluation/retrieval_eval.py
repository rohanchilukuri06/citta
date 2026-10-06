"""
Vector retrieval recall on the live index (candidate coverage before any reranking or routing).

For every labelled single-entity question in semantic_eval_set.json (dev/test/test2), retrieve the top-k
chunks with VectorStore.query_hybrid (no domain filter, so this measures raw semantic recall) and check:
  entity@1 / entity@5          : a chunk of an expected entity is at rank 1 / in the top 5
  entity+section@5             : a chunk of an expected entity AND the asked-for section is in the top 5

Usage: python evaluation/retrieval_eval.py --label <name>   (writes reports/retrieval_<name>.json)
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
EVAL = Path(__file__).resolve().parent

ASPECT_SECTIONS = {
    "OVERVIEW": {"overview", "hero"}, "CAPABILITIES": {"capabilities"}, "BENEFITS": {"benefits", "why_us"},
    "TARGET_USERS": {"target_users"}, "WORKFLOW": {"workflows"}, "FAQ": {"faq"},
}


def main(label: str):
    logging.disable(logging.WARNING)
    import config
    from query_intelligence_engine import get_shared_embedding_model
    from vector_store import VectorStore
    model = get_shared_embedding_model()
    vs = VectorStore(config.VECTOR_DB_PATH)
    meta = vs.get_metadata()
    items = [i for i in json.loads((EVAL / "semantic_eval_set.json").read_text(encoding="utf-8"))["items"]
             if i["ent"] and "SINGLE_ENTITY" in i["scope"] and not i.get("ctx") and i.get("clarify") != "must"]
    e1 = e5 = es5 = es_n = 0
    for it in items:
        q = it["q"]
        emb = model.encode(f"Represent this sentence for searching relevant passages: {q}", normalize_embeddings=True).tolist()
        hits = vs.query_hybrid(query_text=q, query_embedding=emb, top_k=5)
        ents = [(h.get("metadata") or {}).get("entity_id") for h in hits]
        secs = [(h.get("metadata") or {}).get("section") for h in hits]
        e1 += int(bool(ents) and ents[0] in it["ent"])
        e5 += int(any(e in it["ent"] for e in ents))
        want = set().union(*[ASPECT_SECTIONS.get(a, set()) for a in (it.get("aspect") or [])]) if it.get("aspect") else set()
        if want:
            es_n += 1
            es5 += int(any(e in it["ent"] and s in want for e, s in zip(ents, secs)))
    n = len(items)
    res = {"label": label, "n": n, "index_built": meta.get("created_at"), "passage_prefix": meta.get("passage_prefix", "unknown"),
           "entity_recall@1": round(100 * e1 / n, 1), "entity_recall@5": round(100 * e5 / n, 1),
           "entity_section_recall@5": round(100 * es5 / es_n, 1) if es_n else None, "n_with_section": es_n}
    out = EVAL / "reports" / f"retrieval_{label}.json"
    out.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    main(ap.parse_args().label)
