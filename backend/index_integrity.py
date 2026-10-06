"""
Vector index integrity: detect a stale or mismatched index instead of silently serving it.

The index metadata records content_hash (registry + website content + embedding model + index
version), registry_hash, embedding_model, embedding_dimension and index version. At startup the
live values are recomputed and compared:

  development -> loud warning with the exact mismatch
  production  -> rebuild-required state; /api/chat returns a controlled message until rebuilt

The index is never rebuilt automatically at startup (run `python build_index.py`).
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import config

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent
_STATUS: Optional[Dict[str, Any]] = None


def default_content_js_path() -> str:
    # Same lookup as the index builder — a different path means a different content hash and a false "stale index"
    from vector_indexer import resolve_content_js_path
    return resolve_content_js_path()


def compute_registry_hash(registry_dir: Path) -> str:
    h = hashlib.sha256()
    files = sorted(list(registry_dir.glob("*.json")) + list((registry_dir / "new").glob("*.json")), key=lambda p: p.as_posix())
    for f in files:
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def check_index_integrity(metadata: Dict[str, Any], registry_dir: Optional[Path] = None,
                          content_js_path: Optional[str] = None, stored_dimension: Optional[int] = None) -> Dict[str, Any]:
    from vector_indexer import INDEX_VERSION, REGISTRY_DIR, compute_combined_knowledge_hash
    registry_dir = registry_dir or REGISTRY_DIR
    content_js_path = content_js_path or default_content_js_path()

    current_hash = compute_combined_knowledge_hash(content_js_path, registry_dir)
    current_registry_hash = compute_registry_hash(registry_dir)
    reasons = []
    if not metadata:
        reasons.append("index has no metadata")
    if metadata.get("content_hash") != current_hash:
        reasons.append("knowledge content changed since the index was built (content_hash mismatch)")
    if metadata.get("registry_hash") and metadata.get("registry_hash") != current_registry_hash:
        reasons.append("registry files changed since the index was built (registry_hash mismatch)")
    if metadata.get("embedding_model") != config.EMBEDDING_MODEL:
        reasons.append(f"embedding model mismatch: index={metadata.get('embedding_model')} app={config.EMBEDDING_MODEL}")
    if metadata.get("version") != INDEX_VERSION:
        reasons.append(f"index version mismatch: index={metadata.get('version')} app={INDEX_VERSION}")
    meta_dim = metadata.get("embedding_dimension")
    if meta_dim and stored_dimension and int(meta_dim) != int(stored_dimension):
        reasons.append(f"embedding dimension mismatch: metadata={meta_dim} stored vectors={stored_dimension}")
    return {
        "fresh": not reasons,
        "reasons": reasons,
        "stored_content_hash": metadata.get("content_hash"),
        "current_content_hash": current_hash,
        "stored_registry_hash": metadata.get("registry_hash"),
        "current_registry_hash": current_registry_hash,
        "embedding_model": metadata.get("embedding_model"),
        "embedding_dimension": meta_dim or stored_dimension,
        "index_version": metadata.get("version"),
        "built_at": metadata.get("created_at"),
    }


def _stored_dimension(db_path: str) -> Optional[int]:
    import sqlite3
    try:
        con = sqlite3.connect(db_path)
        row = con.execute("select embedding from chunks limit 1").fetchone()
        con.close()
        if not row or row[0] is None:
            return None
        emb = row[0]
        if isinstance(emb, (bytes, bytearray)):
            return len(emb) // 4  # float32 blob
        return len(json.loads(emb))
    except Exception as e:
        logger.warning(f"[IndexIntegrity] Could not read stored embedding dimension: {e}")
        return None


def refresh_status(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Check the live index, log the outcome for the current environment, and cache the result."""
    global _STATUS
    from vector_store import VectorStore
    db_path = db_path or config.VECTOR_DB_PATH
    status = check_index_integrity(VectorStore(db_path).get_metadata(), stored_dimension=_stored_dimension(db_path))
    env = str(getattr(config, "ENVIRONMENT", "production")).lower()
    status["environment"] = env
    status["rebuild_required"] = (not status["fresh"]) and env == "production"
    if status["fresh"]:
        logger.info(f"[IndexIntegrity] Vector index is fresh (built {status['built_at']}, model {status['embedding_model']}).")
    elif env == "production":
        logger.critical(f"[IndexIntegrity] STALE VECTOR INDEX in production — chat is disabled until `python build_index.py` is run. Reasons: {status['reasons']}")
    else:
        logger.warning("\n" + "!" * 70 + f"\n[IndexIntegrity] STALE VECTOR INDEX (development). Answers may not reflect the current registry.\n"
                       f"Reasons: {status['reasons']}\nRun: python build_index.py\n" + "!" * 70)
    _STATUS = status
    return status


def get_status() -> Dict[str, Any]:
    return _STATUS if _STATUS is not None else refresh_status()


def rebuild_required() -> bool:
    return bool(get_status().get("rebuild_required"))
