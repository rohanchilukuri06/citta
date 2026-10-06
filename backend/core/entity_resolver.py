import re
import time
import logging
from functools import lru_cache
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class EntityResolver:
    def __init__(self, registry):
        self.registry = registry

    def _enrich_result(self, res: Dict[str, Any], q_clean: Optional[Any] = None) -> Dict[str, Any]:
        if not res or not isinstance(res, dict) or not res.get("entity_id") or not hasattr(self.registry, "registry_by_capability"):
            return res
        if res.get("entity_category") == "CAPABILITY":
            return res
        
        candidate = None
        if q_clean and isinstance(q_clean, str) and q_clean.lower().strip() in self.registry.registry_by_capability:
            candidate = q_clean.lower().strip()
        else:
            matched_alias = res.get("matched_alias")
            if isinstance(matched_alias, (list, tuple)) and matched_alias:
                matched_alias = matched_alias[0]
            if isinstance(matched_alias, str) and matched_alias.lower().strip() in self.registry.registry_by_capability:
                candidate = matched_alias.lower().strip()
            
        if candidate:
            cap_entry = self.registry.registry_by_capability[candidate]
            parent_obj = cap_entry["parent"]
            cap_obj = cap_entry["capability"]
            res["entity_category"] = "CAPABILITY"
            res["capability_entry"] = cap_entry
            res["matched_capability"] = cap_obj.title
            res["parent_service"] = parent_obj.name
        return res

    def resolve(self, query: str, debug: bool = False) -> Dict[str, Any]:
        t_start = time.perf_counter()
        
        trace = []
        timings = {}
        
        q_raw = query.strip().lower()

        # Step 0: Direct Raw Match against Canonical IDs and Aliases BEFORE rewrite_query
        if q_raw in self.registry.entity_lookup:
            ent_id = self.registry.entity_lookup[q_raw]
            belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
            trace.append(f"raw_exact_canonical_match='{q_raw}' -> {ent_id}")
            timings["lookup_ms"] = (time.perf_counter() - t_start) * 1000.0
            return {
                "entity_id": ent_id,
                "registry": belongs_to,
                "entity_confidence": 1.0,
                "routing_confidence": 1.0,
                "confidence_level": "EXACT",
                "matched_alias": q_raw,
                "normalized_query": q_raw,
                "source": "canonical",
                "trace": trace,
                "timings": timings
            }
        
        if q_raw in self.registry.alias_lookup:
            ent_id = self.registry.alias_lookup[q_raw]
            belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
            trace.append(f"raw_exact_alias_match='{q_raw}' -> {ent_id}")
            timings["lookup_ms"] = (time.perf_counter() - t_start) * 1000.0
            return {
                "entity_id": ent_id,
                "registry": belongs_to,
                "entity_confidence": 1.0,
                "routing_confidence": 1.0,
                "confidence_level": "EXACT",
                "matched_alias": q_raw,
                "normalized_query": q_raw,
                "source": "alias",
                "trace": trace,
                "timings": timings
            }

        # 1. Clean / Normalize base text
        t_norm_start = time.perf_counter()
        try:
            from query_planner import rewrite_query
            query = rewrite_query(query)
        except Exception:
            pass
        q_clean = query.lower().strip()
        # strip punctuation except hyphens/slashes
        q_clean = re.sub(r"[^\w\s\-\/]", "", q_clean)
        q_clean = re.sub(r"\s+", " ", q_clean).strip()
        timings["normalization_ms"] = (time.perf_counter() - t_norm_start) * 1000.0
        
        trace.append(f"normalized_query='{q_clean}'")

        if not q_clean:
            return {
                "entity_id": None,
                "registry": None,
                "entity_confidence": 0.0,
                "routing_confidence": 0.0,
                "confidence_level": "NONE",
                "matched_alias": None,
                "normalized_query": q_clean,
                "source": None,
                "trace": trace,
                "timings": timings
            }

        t_lookup_start = time.perf_counter()

        GENERIC_WORDS = {
            "marketing", "platform", "platforms", "system", "systems", "os", 
            "service", "services", "solution", "solutions", "product", "products", 
            "engineering", "ai", "team", "leaders", "leadership", "about", "contact", 
            "info", "overview", "offer", "offers", "offering", "offerings", "managed", 
            "management", "analytics", "reporting", "automation", "integration", "integrations", 
            "data", "suite", "suites", "company", "our", "my", "help", "trying", "what", "need", "want", "communication",
            "with", "for", "and", "the", "in", "of", "on", "from", "by", "as", "at", "to", "this", "that"
        }

        q_raw = query.strip().lower()

        # Step 0: Direct Raw Match against Canonical IDs, Aliases, and Slugs
        if q_raw in self.registry.entity_lookup:
            ent_id = self.registry.entity_lookup[q_raw]
            belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
            trace.append(f"raw_exact_canonical_match='{q_raw}' -> {ent_id}")
            timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
            return {
                "entity_id": ent_id,
                "registry": belongs_to,
                "entity_confidence": 1.0,
                "routing_confidence": 1.0,
                "confidence_level": "EXACT",
                "matched_alias": q_raw,
                "normalized_query": q_raw,
                "source": "canonical",
                "trace": trace,
                "timings": timings
            }
        
        if q_raw in self.registry.alias_lookup:
            ent_id = self.registry.alias_lookup[q_raw]
            belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
            trace.append(f"raw_exact_alias_match='{q_raw}' -> {ent_id}")
            timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
            return {
                "entity_id": ent_id,
                "registry": belongs_to,
                "entity_confidence": 1.0,
                "routing_confidence": 1.0,
                "confidence_level": "EXACT",
                "matched_alias": q_raw,
                "normalized_query": q_raw,
                "source": "alias",
                "trace": trace,
                "timings": timings
            }

        # Step 1: Exact Canonical ID or Name Match
        if q_clean in self.registry.entity_lookup:
            ent_id = self.registry.entity_lookup[q_clean]
            belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
            trace.append(f"canonical_exact_match='{q_clean}' -> {ent_id}")
            timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
            return {
                "entity_id": ent_id,
                "registry": belongs_to,
                "entity_confidence": 1.0,
                "routing_confidence": 1.0,
                "confidence_level": "EXACT",
                "matched_alias": q_clean,
                "normalized_query": q_clean,
                "source": "canonical",
                "trace": trace,
                "timings": timings
            }

        # Step 2: Exact Alias Match
        if q_clean in self.registry.alias_lookup:
            ent_id = self.registry.alias_lookup[q_clean]
            belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
            trace.append(f"alias_exact_match='{q_clean}' -> {ent_id}")
            timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
            return {
                "entity_id": ent_id,
                "registry": belongs_to,
                "entity_confidence": 1.0,
                "routing_confidence": 0.95,
                "confidence_level": "EXACT",
                "matched_alias": q_clean,
                "normalized_query": q_clean,
                "source": "alias",
                "trace": trace,
                "timings": timings
            }

        # Step 3: Exact Slug Match
        if q_clean in self.registry.slug_lookup:
            ent_id = self.registry.slug_lookup[q_clean]
            belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
            trace.append(f"slug_exact_match='{q_clean}' -> {ent_id}")
            timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
            return {
                "entity_id": ent_id,
                "registry": belongs_to,
                "entity_confidence": 1.0,
                "routing_confidence": 0.95,
                "confidence_level": "EXACT",
                "matched_alias": q_clean,
                "normalized_query": q_clean,
                "source": "slug",
                "trace": trace,
                "timings": timings
            }

        # Step 3.1: Substring Match against Canonical Entity Lookup
        sorted_entity_keys = sorted(self.registry.entity_lookup.keys(), key=len, reverse=True)
        for e_key in sorted_entity_keys:
            if e_key in GENERIC_WORDS:
                continue
            if len(e_key) >= 3 and re.search(r"\b" + re.escape(e_key) + r"\b", q_clean):
                ent_id = self.registry.entity_lookup[e_key]
                belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
                trace.append(f"entity_substring_match='{e_key}' -> {ent_id}")
                timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
                return {
                    "entity_id": ent_id,
                    "registry": belongs_to,
                    "entity_confidence": 0.95,
                    "routing_confidence": 0.90,
                    "confidence_level": "HIGH",
                    "matched_alias": e_key,
                    "normalized_query": q_clean,
                    "source": "entity_substring",
                    "trace": trace,
                    "timings": timings
                }

        # Step 3.5: Capability & Sub-service Lookup Match
        if hasattr(self.registry, "registry_by_capability") and self.registry.registry_by_capability:
            sorted_cap_keys = sorted(self.registry.registry_by_capability.keys(), key=len, reverse=True)
            for cap_key in sorted_cap_keys:
                if len(cap_key) >= 3 and cap_key not in self.registry.entity_lookup and cap_key not in self.registry.alias_lookup and (q_clean == cap_key or re.search(r"\b" + re.escape(cap_key) + r"\b", q_clean)):
                    cap_entry = self.registry.registry_by_capability[cap_key]
                    parent_obj = cap_entry["parent"]
                    cap_obj = cap_entry["capability"]
                    trace.append(f"capability_match='{cap_key}' -> {parent_obj.id} (Capability: {cap_obj.title})")
                    timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
                    return {
                        "entity_id": parent_obj.id,
                        "registry": "SERVICES",
                        "entity_confidence": 0.95,
                        "routing_confidence": 0.90,
                        "confidence_level": "HIGH",
                        "matched_alias": cap_key,
                        "matched_capability": cap_obj.title,
                        "parent_service": parent_obj.name,
                        "entity_category": "CAPABILITY",
                        "capability_entry": cap_entry,
                        "normalized_query": q_clean,
                        "source": "capability",
                        "trace": trace,
                        "timings": timings
                    }

        # Step 4: Exact Keyword Match
        if q_clean in self.registry.keyword_lookup and q_clean not in GENERIC_WORDS:
            ent_id = self.registry.keyword_lookup[q_clean]
            belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
            trace.append(f"keyword_exact_match='{q_clean}' -> {ent_id}")
            timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
            return {
                "entity_id": ent_id,
                "registry": belongs_to,
                "entity_confidence": 0.90,
                "routing_confidence": 0.85,
                "confidence_level": "MEDIUM",
                "matched_alias": q_clean,
                "normalized_query": q_clean,
                "source": "keyword",
                "trace": trace,
                "timings": timings
            }

        # Step 5: Substring phrase lookup (Word boundary searches)
        # Check canonicals
        for key in sorted(self.registry.entity_lookup.keys(), key=len, reverse=True):
            if key in GENERIC_WORDS:
                continue
            if len(key) >= 3 and re.search(r"\b" + re.escape(key) + r"\b", q_clean):
                ent_id = self.registry.entity_lookup[key]
                belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
                trace.append(f"canonical_substring_match='{key}' -> {ent_id}")
                timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
                return {
                    "entity_id": ent_id,
                    "registry": belongs_to,
                    "entity_confidence": 0.95,
                    "routing_confidence": 0.90,
                    "confidence_level": "HIGH",
                    "matched_alias": key,
                    "normalized_query": q_clean,
                    "source": "canonical",
                    "trace": trace,
                    "timings": timings
                }

        # Check aliases
        for key in sorted(self.registry.alias_lookup.keys(), key=len, reverse=True):
            if key in GENERIC_WORDS:
                continue
            if len(key) >= 3 and re.search(r"\b" + re.escape(key) + r"\b", q_clean):
                ent_id = self.registry.alias_lookup[key]
                belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
                trace.append(f"alias_substring_match='{key}' -> {ent_id}")
                timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
                return {
                    "entity_id": ent_id,
                    "registry": belongs_to,
                    "entity_confidence": 0.90,
                    "routing_confidence": 0.85,
                    "confidence_level": "HIGH",
                    "matched_alias": key,
                    "normalized_query": q_clean,
                    "source": "alias",
                    "trace": trace,
                    "timings": timings
                }

        # Check slugs
        for key in sorted(self.registry.slug_lookup.keys(), key=len, reverse=True):
            if key in GENERIC_WORDS:
                continue
            if len(key) > 3 and re.search(r"\b" + re.escape(key) + r"\b", q_clean):
                ent_id = self.registry.slug_lookup[key]
                belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
                trace.append(f"slug_substring_match='{key}' -> {ent_id}")
                timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
                return {
                    "entity_id": ent_id,
                    "registry": belongs_to,
                    "entity_confidence": 0.90,
                    "routing_confidence": 0.85,
                    "confidence_level": "HIGH",
                    "matched_alias": key,
                    "normalized_query": q_clean,
                    "source": "slug",
                    "trace": trace,
                    "timings": timings
                }

        # Check keywords
        for key in sorted(self.registry.keyword_lookup.keys(), key=len, reverse=True):
            if key in GENERIC_WORDS:
                continue
            if len(key) > 3 and re.search(r"\b" + re.escape(key) + r"\b", q_clean):
                ent_id = self.registry.entity_lookup.get(key) or self.registry.keyword_lookup[key]
                belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
                trace.append(f"keyword_substring_match='{key}' -> {ent_id}")
                timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0
                return {
                    "entity_id": ent_id,
                    "registry": belongs_to,
                    "entity_confidence": 0.80,
                    "routing_confidence": 0.75,
                    "confidence_level": "MEDIUM",
                    "matched_alias": key,
                    "normalized_query": q_clean,
                    "source": "keyword",
                    "trace": trace,
                    "timings": timings
                }

        timings["lookup_ms"] = (time.perf_counter() - t_lookup_start) * 1000.0

        # Step 6: Fuzzy Match (WRatio >= 90%)
        t_fuzzy_start = time.perf_counter()
        try:
            from rapidfuzz import process, fuzz
            candidates = list(self.registry.entity_lookup.keys()) + list(self.registry.alias_lookup.keys()) + list(self.registry.slug_lookup.keys())
            match = process.extractOne(q_clean, candidates, scorer=fuzz.WRatio)
            if match and match[1] >= 90.0:
                best_str = match[0]
                q_words = set(re.findall(r"\w+", q_clean))
                # Guard against false sub-word matches (e.g., 'housing' inside 'warehousing')
                if best_str not in q_words and not re.search(r"\b" + re.escape(best_str) + r"\b", q_clean):
                    match = None

                if match:
                    ent_id = self.registry.entity_lookup.get(best_str) or self.registry.alias_lookup.get(best_str) or self.registry.slug_lookup.get(best_str)
                    if ent_id:
                        belongs_to = self.registry.knowledge_graph.get(ent_id, {}).get("belongs_to", "UNKNOWN")
                        trace.append(f"fuzzy_match='{best_str}' (score={match[1]:.1f}) -> {ent_id}")
                        timings["fuzzy_ms"] = (time.perf_counter() - t_fuzzy_start) * 1000.0
                        return {
                            "entity_id": ent_id,
                            "registry": belongs_to,
                            "entity_confidence": float(match[1] / 100.0),
                            "routing_confidence": float(match[1] / 100.0 * 0.90),
                            "confidence_level": "FUZZY",
                            "matched_alias": best_str,
                            "normalized_query": q_clean,
                            "source": "alias",
                            "trace": trace,
                            "timings": timings
                        }
        except Exception as e:
            logger.warning(f"Fuzzy matching failed in core/entity_resolver: {e}")

        timings["fuzzy_ms"] = (time.perf_counter() - t_fuzzy_start) * 1000.0

        trace.append("resolution_failed")
        return {
            "entity_id": None,
            "registry": None,
            "entity_confidence": 0.0,
            "routing_confidence": 0.0,
            "confidence_level": "NONE",
            "matched_alias": None,
            "normalized_query": q_clean,
            "source": None,
            "trace": trace,
            "timings": timings
        }

@lru_cache(maxsize=2048)
def _resolve_cached(query: str) -> Dict[str, Any]:
    try:
        from knowledge_registry import get_registry
    except ImportError:
        from knowledge_registry import get_registry
    registry = get_registry()
    resolver = EntityResolver(registry)
    return resolver.resolve(query)

def resolve(query: str, debug: bool = False) -> Dict[str, Any]:
    """Expose simple public resolve API using cached resolver."""
    try:
        from knowledge_registry import get_registry
    except ImportError:
        from knowledge_registry import get_registry
    registry = get_registry()
    resolver = EntityResolver(registry)
    
    q_clean = query.lower().strip()
    q_clean = re.sub(r"[^\w\s\-\/]", "", q_clean)
    q_clean = re.sub(r"\s+", " ", q_clean).strip()
    
    if debug:
        res = resolver.resolve(query, debug=True)
    else:
        res = _resolve_cached(query)
    return resolver._enrich_result(res, q_clean=q_clean)
