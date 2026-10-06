"""
Semantic entity & aspect index for CittaAI query understanding.

Entity exemplars are derived entirely from KnowledgeRegistry content (title, tagline, description,
target users, capabilities, benefits, workflow steps, FAQ questions, registry keywords), so new or
edited registry entries are understood without hand-maintained keyword lists. Each entity is
represented by many short exemplars instead of one blob, and the query is scored against all of them.

Scores are turned into a calibrated probability distribution over entities (softmax with a
temperature fitted on the dev split), which gives arbitration a real top1-top2 margin.

Embeddings are computed once and cached on disk, keyed by model name + exemplar content hash.
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

import config

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent / "data" / "semantic_index_cache"

# Entity types the index resolves directly. Individual people and case studies are reached
# through aspect operations (get_leadership / list_case_studies), not as the query's subject.
INDEXED_TYPES = {"solution", "product", "service", "company", "contact", "award"}

# Softmax temperature over entity scores. Fitted on the dev split (see semantic_benchmark.py).
ENTITY_TEMPERATURE = 0.02
# Below this raw similarity the query is not about any specific registry entity.
ENTITY_RELEVANCE_FLOOR = 0.44

GENERIC_BEST_FOR = {"admin", "user", "users", "clients", "partners", "inquirers", "jury", "sales leads"}

# Aspect prototypes describe *kinds of questions*, not domains, so they don't grow with the catalog.
ASPECT_PROTOTYPES: Dict[str, List[str]] = {
    "OVERVIEW": [
        "what is this offering", "give me an overview", "describe the product", "do you have a solution for my sector",
        "what do you have for our industry", "introduce this platform",
    ],
    "CAPABILITIES": [
        "what features are included", "what functionality does it provide", "which modules come with it",
        "list the capabilities", "what is it able to do", "does it support a particular function",
    ],
    "BENEFITS": [
        "what advantages does it bring", "what value or return on investment does it deliver", "why is it worth adopting",
        "how will it improve our results", "what outcomes can we expect",
    ],
    "TARGET_USERS": [
        "which audience is it built for", "what type of customer is it intended for", "which organizations should adopt it",
        "is it a good fit for a company like ours",
    ],
    "WORKFLOW": [
        "explain the process end to end", "what are the steps involved", "how is it set up and implemented",
        "describe the workflow", "how does it operate",
    ],
    "PRICING": ["how much does it cost", "what are the pricing plans", "what is the subscription fee", "can I get a quote"],
    "CONTACT": [
        "how can I get in touch with your company", "what are your contact details", "where can I find your address",
        "how do I speak with sales",
    ],
    "LEADERSHIP": ["who are the founders", "who is on the leadership team", "who heads the company", "names of the executives"],
    "RECOGNITION": ["what honors and accolades has the company received", "list of industry recognitions"],
    "CLIENTS_CASE_STUDIES": [
        "which customers have used your services", "examples of past client projects", "case studies and results for clients",
    ],
    "FAQ": ["frequently asked questions", "common questions people ask"],
}
ASPECT_TEMPERATURE = 0.03
# Scored on the question frame (catalog entity names masked). Dev: domain-heavy frames <= ~0.54, aspect questions >= ~0.59
ASPECT_RELEVANCE_FLOOR = 0.55


def _as_text(v: Any) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return " ".join(_as_text(x) for x in v.values() if isinstance(x, (str, list, dict)))
    if isinstance(v, list):
        return " ".join(_as_text(x) for x in v)
    return ""


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def build_entity_exemplars(entity: Dict[str, Any]) -> List[str]:
    """Derive short, focused exemplar sentences for one registry entity."""
    title = entity.get("title") or entity.get("name") or entity.get("id", "")
    name = entity.get("name") or title
    ex: List[str] = []

    head = _clean(f"{title}. {entity.get('tagline') or ''}. {entity.get('description') or ''}")
    ex.append(head)
    if name != title:
        ex.append(_clean(f"{name}: {title}"))

    best_for = [b for b in (entity.get("best_for") or []) if isinstance(b, str) and b.lower() not in GENERIC_BEST_FOR]
    if best_for:
        ex.append(f"{title} is designed for {', '.join(best_for)}")

    for cap in entity.get("capabilities") or []:
        if isinstance(cap, dict):
            feats = "; ".join(f for f in cap.get("features", []) if isinstance(f, str))
            ex.append(_clean(f"{title}: {cap.get('title', '')}. {cap.get('subtitle', '')}. {cap.get('description', '')} {feats}"))
        elif isinstance(cap, str):
            ex.append(f"{title}: {cap}")

    for ben in entity.get("benefits") or []:
        t = _as_text(ben)
        if t:
            ex.append(_clean(f"{title} benefit: {t}"))

    how = entity.get("how_it_works") or {}
    steps = how.get("steps", []) if isinstance(how, dict) else how if isinstance(how, list) else []
    for step in steps:
        t = _as_text(step)
        if t:
            ex.append(_clean(f"{title}: {t}"))

    for wf in entity.get("workflows") or []:
        t = _as_text(wf)
        if t:
            ex.append(_clean(f"{title} workflow: {t}")[:400])

    for faq in entity.get("faq") or []:
        if isinstance(faq, dict) and faq.get("question"):
            ex.append(_clean(f"{title}: {faq['question']}"))

    search = entity.get("search") or {}
    kws = [k for k in (search.get("primary_keywords") or []) + (search.get("secondary_keywords") or []) if isinstance(k, str)]
    if kws:
        ex.append(f"{title}: {', '.join(kws[:25])}")

    seen, out = set(), []
    for e in ex:
        e = e[:500]
        if len(e) > 12 and e not in seen:
            seen.add(e)
            out.append(e)
    return out


def _load_site_documents() -> List[Dict[str, Any]]:
    path = Path(__file__).resolve().parent / "knowledge" / "site" / "cittaai_live.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("documents", []) if path.exists() else []
    except (OSError, ValueError) as e:
        logger.warning(f"[SemanticEntityIndex] Could not read crawled site knowledge: {e}")
        return []


def _softmax(x: np.ndarray, t: float) -> np.ndarray:
    z = (x - x.max()) / t
    e = np.exp(z)
    return e / e.sum()


@dataclass
class RankedCandidate:
    value: str
    score: float  # raw cosine similarity
    prob: float   # calibrated probability within the distribution


class SemanticEntityIndex:
    def __init__(self, registry: Any, model: Any):
        self.registry = registry
        self.model = model
        self.entity_ids: List[str] = []
        self.exemplar_owner: np.ndarray = np.zeros(0, dtype=int)
        self.exemplar_emb: np.ndarray = np.zeros((0, 1))
        self.aspect_names: List[str] = []
        self.aspect_owner: np.ndarray = np.zeros(0, dtype=int)
        self.aspect_emb: np.ndarray = np.zeros((0, 1))
        self._build()

    # ---------- construction ----------
    def _indexed_entities(self) -> Dict[str, Dict[str, Any]]:
        out = {}
        for eid, obj in self.registry.entities.items():
            etype = str(obj.get("type") or "").lower()
            if etype in INDEXED_TYPES:
                out[eid] = obj
        return out

    def _encode_passages(self, texts: List[str]) -> np.ndarray:
        return np.asarray(self.model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False), dtype=np.float32)

    def _build(self) -> None:
        entities = self._indexed_entities()
        texts, owners = [], []
        site_docs = _load_site_documents()
        for i, (eid, obj) in enumerate(sorted(entities.items())):
            self.entity_ids.append(eid)
            for e in build_entity_exemplars(obj):
                texts.append(e)
                owners.append(i)
            # Pages crawled from cittaai.com describe the same offering in the site's own words
            for d in site_docs:
                if eid in (d.get("entities") or []) and d.get("section") != "leadership":
                    texts.append(f"{obj.get('name') or obj.get('title')}: {d['text']}"[:500])
                    owners.append(i)
        a_texts, a_owners = [], []
        for j, (asp, protos) in enumerate(ASPECT_PROTOTYPES.items()):
            self.aspect_names.append(asp)
            for p in protos:
                a_texts.append(p)
                a_owners.append(j)

        payload = json.dumps({"m": config.EMBEDDING_MODEL, "e": texts, "a": a_texts}, sort_keys=True)
        key = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        cache = CACHE_DIR / f"index_{key}.npz"
        if cache.exists():
            data = np.load(cache)
            self.exemplar_emb, self.aspect_emb = data["e"], data["a"]
        else:
            self.exemplar_emb = self._encode_passages(texts)
            # Aspect prototypes are questions, so embed them in the query space
            self.aspect_emb = self._encode_queries(a_texts)
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                np.savez(cache, e=self.exemplar_emb, a=self.aspect_emb)
            except OSError as e:
                logger.warning(f"[SemanticEntityIndex] Could not write cache: {e}")
        self.exemplar_owner = np.asarray(owners, dtype=int)
        self.exemplar_texts = texts
        self.aspect_owner = np.asarray(a_owners, dtype=int)
        self.content_hash = key
        logger.info(f"[SemanticEntityIndex] {len(self.entity_ids)} entities, {len(texts)} exemplars (cache {key})")

    # ---------- scoring ----------
    def _encode_queries(self, queries: List[str]) -> np.ndarray:
        if "bge" in config.EMBEDDING_MODEL.lower():
            queries = [f"Represent this sentence for searching relevant passages: {q}" for q in queries]
        return np.asarray(self.model.encode(queries, normalize_embeddings=True, show_progress_bar=False), dtype=np.float32)

    def encode_query(self, query: str) -> np.ndarray:
        return self._encode_queries([query])[0]

    def rank_entities(self, query: str, q_emb: Optional[np.ndarray] = None, top_k: int = 5) -> List[RankedCandidate]:
        if q_emb is None:
            q_emb = self.encode_query(query)
        sims = self.exemplar_emb @ q_emb
        n = len(self.entity_ids)
        ent_scores = np.full(n, -1.0, dtype=np.float32)
        for i in range(n):
            s = np.sort(sims[self.exemplar_owner == i])[::-1]
            if len(s):
                # Best exemplar dominates; the next two add robustness against a single lucky match
                ent_scores[i] = 0.7 * s[0] + 0.3 * float(np.mean(s[:3]))
        probs = _softmax(ent_scores, ENTITY_TEMPERATURE)
        order = np.argsort(-ent_scores)[:top_k]
        return [RankedCandidate(self.entity_ids[i], float(ent_scores[i]), float(probs[i])) for i in order]

    def rank_aspects(self, query: str, q_emb: Optional[np.ndarray] = None) -> List[RankedCandidate]:
        if q_emb is None:
            q_emb = self.encode_query(query)
        sims = self.aspect_emb @ q_emb
        scores = np.array([float(np.max(sims[self.aspect_owner == j])) for j in range(len(self.aspect_names))])
        probs = _softmax(scores, ASPECT_TEMPERATURE)
        order = np.argsort(-scores)
        return [RankedCandidate(self.aspect_names[j], float(scores[j]), float(probs[j])) for j in order]

    def best_exemplar(self, entity_id: str, q_emb: np.ndarray) -> str:
        """The catalog passage of this entity most similar to the query (shown to the LLM adjudicator)."""
        if entity_id not in self.entity_ids:
            return ""
        idx = np.where(self.exemplar_owner == self.entity_ids.index(entity_id))[0]
        if not len(idx):
            return ""
        best = idx[int(np.argmax(self.exemplar_emb[idx] @ q_emb))]
        return self.exemplar_texts[best][:300]

    def describe(self, entity_id: str) -> str:
        obj = self.registry.entities.get(entity_id, {})
        return _clean(f"{obj.get('title') or obj.get('name')}: {obj.get('tagline') or ''}. {str(obj.get('description') or '')[:160]}")


_INDEX: Optional[SemanticEntityIndex] = None


def get_semantic_entity_index(registry: Any = None, model: Any = None) -> SemanticEntityIndex:
    global _INDEX
    if _INDEX is None:
        if registry is None:
            from knowledge_registry import get_registry
            registry = get_registry()
        if model is None:
            from query_intelligence_engine import get_shared_embedding_model
            model = get_shared_embedding_model()
        _INDEX = SemanticEntityIndex(registry, model)
    return _INDEX
