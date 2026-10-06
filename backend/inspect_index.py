import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

import config
from vector_store import VectorStore
from vector_indexer import REGISTRY_DIR, compute_combined_knowledge_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def inspect_unified_index(db_path: str = None) -> Dict[str, Any]:
    """
    Inspects the unified vector store and returns comprehensive diagnostics.
    Reports total chunks, Registry chunks, content.js chunks, entity breakdowns,
    section breakdowns, embedding model & dimension, and index staleness.
    """
    vstore = VectorStore(db_path or config.VECTOR_DB_PATH)
    meta = vstore.get_metadata()
    chunks = vstore.get_all_chunks()

    content_js_path = os.path.join(ROOT_DIR, "..", "frontend", "src", "data", "content.js")
    if not os.path.exists(content_js_path):
        content_js_path = os.path.join(ROOT_DIR, "content.js")

    current_hash = compute_combined_knowledge_hash(content_js_path, REGISTRY_DIR)
    stored_hash = meta.get("content_hash", "")
    is_stale = (current_hash != stored_hash) if stored_hash else True

    registry_chunks = []
    content_js_chunks = []
    chunks_per_entity: Dict[str, int] = {}
    chunks_per_section: Dict[str, int] = {}
    chunks_per_category: Dict[str, int] = {}
    chunks_per_type: Dict[str, int] = {}
    duplicate_count = 0
    malformed_count = 0
    seen_ids = set()

    embedding_dim = 0
    if chunks:
        # Check embedding dimension from first chunk in sqlite
        try:
            import sqlite3, numpy as np
            conn = sqlite3.connect(vstore._get_resolved_path())
            cursor = conn.cursor()
            cursor.execute("SELECT embedding FROM chunks LIMIT 1")
            row = cursor.fetchone()
            if row and row[0]:
                vec = np.frombuffer(row[0], dtype=np.float32)
                embedding_dim = len(vec)
            conn.close()
        except Exception:
            embedding_dim = 0

    for c in chunks:
        cid = c["id"]
        if cid in seen_ids:
            duplicate_count += 1
        seen_ids.add(cid)

        metadata = c.get("metadata", {})
        if not metadata or not c.get("content"):
            malformed_count += 1

        source = c.get("source", metadata.get("source", "unknown"))
        if source == "knowledge_registry" or metadata.get("doc_type") == "registry_entity":
            registry_chunks.append(c)
        else:
            content_js_chunks.append(c)

        ent_id = metadata.get("entity_id") or metadata.get("domain") or "content_js"
        chunks_per_entity[ent_id] = chunks_per_entity.get(ent_id, 0) + 1

        sec = metadata.get("section", "unspecified")
        chunks_per_section[sec] = chunks_per_section.get(sec, 0) + 1

        cat = metadata.get("category", "unspecified")
        chunks_per_category[cat] = chunks_per_category.get(cat, 0) + 1

        etype = metadata.get("entity_type", "web_copy")
        chunks_per_type[etype] = chunks_per_type.get(etype, 0) + 1

    report = {
        "index_version": meta.get("version", "N/A"),
        "schema_version": meta.get("schema_version", "N/A"),
        "embedding_model": meta.get("embedding_model", config.EMBEDDING_MODEL),
        "embedding_dimension": embedding_dim,
        "content_hash": stored_hash,
        "current_hash": current_hash,
        "is_stale": is_stale,
        "created_at": meta.get("created_at", "N/A"),
        "total_chunks": len(chunks),
        "registry_chunks_count": len(registry_chunks),
        "content_js_chunks_count": len(content_js_chunks),
        "unique_entities_indexed": len([e for e in chunks_per_entity.keys() if e != "content_js"]),
        "chunks_per_entity": chunks_per_entity,
        "chunks_per_section": chunks_per_section,
        "chunks_per_category": chunks_per_category,
        "chunks_per_type": chunks_per_type,
        "duplicate_count": duplicate_count,
        "malformed_count": malformed_count
    }

    print("\n================ UNIFIED INDEX DIAGNOSTICS ================")
    print(f" Index Version       : {report['index_version']}")
    print(f" Embedding Model     : {report['embedding_model']} (Dim: {report['embedding_dimension']})")
    print(f" Content Hash (DB)   : {report['content_hash'][:16]}..." if report['content_hash'] else " None")
    print(f" Content Hash (Disk) : {report['current_hash'][:16]}...")
    print(f" Stale Status        : {'STALE (Rebuild recommended)' if report['is_stale'] else 'FRESH (Up to date)'}")
    print(f" Total Chunks        : {report['total_chunks']}")
    print(f"   +-- Registry Chunks: {report['registry_chunks_count']}")
    print(f"   +-- content.js Chunks: {report['content_js_chunks_count']}")
    print(f" Indexed Entities    : {report['unique_entities_indexed']}")
    print(f" Duplicate Chunks    : {report['duplicate_count']}")
    print(f" Malformed Chunks    : {report['malformed_count']}")
    print("----------------------------------------------------------")
    print(" CHUNKS PER ENTITY:")
    for ent, count in sorted(chunks_per_entity.items(), key=lambda x: -x[1]):
        print(f"   * {ent:35s} : {count} chunks")
    print("----------------------------------------------------------")
    print(" CHUNKS PER SECTION:")
    for sec, count in sorted(chunks_per_section.items(), key=lambda x: -x[1]):
        print(f"   * {sec:25s} : {count} chunks")
    print("==========================================================\n")

    return report

if __name__ == "__main__":
    inspect_unified_index()
