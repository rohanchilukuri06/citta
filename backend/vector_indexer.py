import os
import sys
import json
import hashlib
import logging
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import config
from vector_store import VectorStore, parse_content_js, atomic_replace_database

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent
REGISTRY_DIR = ROOT_DIR / "knowledge" / "registry"
INDEX_VERSION = "2.1.0"  # 2.1.0: passages embedded without the BGE query instruction

def compute_file_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file for deterministic rebuild verification."""
    if not os.path.exists(file_path):
        return ""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_combined_knowledge_hash(content_js_path: str, registry_dir: Path) -> str:
    """
    Computes a combined SHA-256 fingerprint across:
    1. content.js
    2. manifest.json
    3. All active registry entity JSON files in registry/ and registry/new/
    4. EMBEDDING_MODEL + INDEX_VERSION
    """
    hasher = hashlib.sha256()

    # 1. content.js
    if os.path.exists(content_js_path):
        hasher.update(compute_file_sha256(content_js_path).encode("utf-8"))

    # 2. manifest.json
    manifest_path = registry_dir / "manifest.json"
    if manifest_path.exists():
        hasher.update(compute_file_sha256(str(manifest_path)).encode("utf-8"))

    # 3. All entity JSON files (sorted for determinism)
    json_files = []
    if registry_dir.exists():
        json_files.extend(list(registry_dir.glob("*.json")))
        new_dir = registry_dir / "new"
        if new_dir.exists():
            json_files.extend(list(new_dir.glob("*.json")))

    for jf in sorted(json_files, key=lambda p: p.as_posix()):
        if jf.name == "manifest.json":
            continue
        hasher.update(jf.name.encode("utf-8"))
        hasher.update(compute_file_sha256(str(jf)).encode("utf-8"))

    # 3b. Content crawled from the live website
    if SITE_KNOWLEDGE.exists():
        hasher.update(compute_file_sha256(str(SITE_KNOWLEDGE)).encode("utf-8"))

    # 4. Model and index version
    hasher.update(config.EMBEDDING_MODEL.encode("utf-8"))
    hasher.update(INDEX_VERSION.encode("utf-8"))

    return hasher.hexdigest()

SITE_KNOWLEDGE = ROOT_DIR / "knowledge" / "site" / "cittaai_live.json"


def parse_site_chunks(site_path: Path = SITE_KNOWLEDGE) -> List[Dict[str, Any]]:
    """Documents crawled from cittaai.com (scripts/sync_live_site.py): one chunk per (document, mapped entity)."""
    if not site_path.exists():
        return []
    data = json.loads(site_path.read_text(encoding="utf-8"))
    from knowledge_registry import get_registry
    reg = get_registry()
    chunks = []
    for i, d in enumerate(data.get("documents", [])):
        for ent in d.get("entities") or ["company_info"]:
            e = reg.entities.get(ent) or {}
            chunks.append({
                "chunk_id": f"site_{i}_{ent}",
                "content": d["text"],
                "metadata": {
                    "source": "cittaai.com", "entity_id": ent, "entity_title": e.get("name") or e.get("title") or ent,
                    "entity_type": e.get("type", ""), "category": e.get("category", ""), "domain": e.get("type", ""),
                    "section": d.get("section", "overview"), "title": d.get("title", ""), "route": d.get("url", ""),
                    "url": d.get("url", ""), "registry_version": "site", "doc_type": "site_page",
                    "crawled": data.get("crawled", ""),
                },
            })
    return chunks


def parse_registry_chunks(registry_dir: Path) -> List[Dict[str, Any]]:
    """
    Parses all active Knowledge Registry JSON files into structured, section-level semantic chunks.
    Preserves rich entity metadata (entity_id, title, type, category, domain, section, route, source).
    """
    chunks = []
    manifest_path = registry_dir / "manifest.json"
    if not manifest_path.exists():
        logger.warning(f"Manifest not found at {manifest_path}. Skipping registry chunking.")
        return chunks

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read manifest.json: {e}")
        return chunks

    registries = manifest_data.get("registries", [])
    for reg_conf in registries:
        if not reg_conf.get("enabled", True):
            continue

        rel_path = reg_conf.get("content")
        file_path = registry_dir / rel_path
        if not file_path.exists():
            logger.warning(f"Registry content file missing: {file_path}")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading registry JSON '{file_path}': {e}")
            continue

        entity_id = data.get("id") or reg_conf.get("name")
        entity_title = data.get("title") or data.get("name") or entity_id
        entity_type = data.get("type") or reg_conf.get("registry_type", "unknown").lower()
        route = data.get("url") or data.get("route") or ""
        tagline = data.get("tagline") or ""
        classification = data.get("classification") or {}
        category = classification.get("category") or entity_id
        domain = classification.get("domain") or reg_conf.get("registry_type") or entity_type
        industry = classification.get("industry") or "General"

        meta_base = {
            "source": "knowledge_registry",
            "entity_id": entity_id,
            "entity_title": entity_title,
            "entity_type": entity_type,
            "category": category,
            "domain": domain,
            "industry": industry,
            "route": route,
            "registry_version": "2.0",
            "original_file": rel_path,
            "doc_type": "registry_entity"
        }

        # 1. Overview Section
        overview_text = data.get("overview") or data.get("description") or ""
        if overview_text:
            content_str = f"CittaAI {entity_type.capitalize()} - {entity_title}"
            if tagline:
                content_str += f" ({tagline})"
            content_str += f": {overview_text}"
            chunks.append({
                "chunk_id": f"reg_{entity_id}_overview",
                "content": content_str,
                "metadata": {**meta_base, "section": "overview", "title": f"{entity_title} Overview"}
            })

        # 2. Target Users / Audience Section
        target_users = data.get("target_users") or data.get("best_for") or []
        if target_users:
            if isinstance(target_users, list):
                users_str = ", ".join(str(u) for u in target_users)
            else:
                users_str = str(target_users)
            content_str = f"Target Users & Audience for {entity_title} ({entity_type}): Best suited for {users_str}. Category: {category}, Industry: {industry}."
            chunks.append({
                "chunk_id": f"reg_{entity_id}_target_users",
                "content": content_str,
                "metadata": {**meta_base, "section": "target_users", "title": f"{entity_title} Target Users"}
            })

        # 3. Capabilities & Features
        capabilities = data.get("capabilities") or []
        for idx, cap in enumerate(capabilities):
            if isinstance(cap, dict):
                cap_id = cap.get("id") or f"cap_{idx}"
                cap_title = cap.get("title") or ""
                cap_sub = cap.get("subtitle") or ""
                cap_desc = cap.get("description") or ""
                features = cap.get("features") or []
                feat_texts = []
                for feat in features:
                    if isinstance(feat, dict):
                        ft_t = feat.get("title") or ""
                        ft_d = feat.get("description") or ""
                        if ft_t and ft_d:
                            feat_texts.append(f"{ft_t}: {ft_d}")
                        elif ft_t:
                            feat_texts.append(ft_t)
                    elif isinstance(feat, str):
                        feat_texts.append(feat)

                feat_str = " | Features: " + "; ".join(feat_texts) if feat_texts else ""
                sub_str = f" ({cap_sub})" if cap_sub else ""
                content_str = f"{entity_title} Capability - {cap_title}{sub_str}: {cap_desc}{feat_str}"

                chunks.append({
                    "chunk_id": f"reg_{entity_id}_cap_{cap_id}",
                    "content": content_str,
                    "metadata": {**meta_base, "section": "capabilities", "title": f"{entity_title} - {cap_title}", "capability_id": cap_id}
                })

        # 4. Leadership Members Section (if entity has member list)
        members = data.get("members") or []
        for m in members:
            if isinstance(m, dict):
                m_id = m.get("id") or m.get("name", "").lower().replace(" ", "_")
                m_name = m.get("name") or ""
                m_desig = m.get("designation") or ""
                m_dept = m.get("department") or ""
                m_bio = m.get("bio") or ""
                m_resp = m.get("responsibilities") or []
                resp_str = ", ".join(m_resp) if isinstance(m_resp, list) else str(m_resp)
                content_str = f"CittaAI Leadership Team - {m_name} ({m_desig}, {m_dept}): {m_bio}. Key Responsibilities: {resp_str}."
                chunks.append({
                    "chunk_id": f"reg_{entity_id}_member_{m_id}",
                    "content": content_str,
                    "metadata": {**meta_base, "section": "leadership", "title": f"Leadership: {m_name}", "member_id": m_id}
                })

        # 5. Workflows / How It Works
        workflows = data.get("workflows") or data.get("how_it_works") or []
        if workflows:
            wf_texts = []
            if isinstance(workflows, dict) and "steps" in workflows:
                steps = workflows["steps"]
                for s in steps:
                    wf_texts.append(str(s))
            elif isinstance(workflows, list):
                for w in workflows:
                    if isinstance(w, dict):
                        step_num = w.get("step", "")
                        st_t = w.get("title", "")
                        st_d = w.get("description", "")
                        wf_texts.append(f"Step {step_num} ({st_t}): {st_d}")
                    elif isinstance(w, str):
                        wf_texts.append(w)
            if wf_texts:
                content_str = f"{entity_title} Workflows & Implementation Steps:\n" + "\n".join(wf_texts)
                chunks.append({
                    "chunk_id": f"reg_{entity_id}_workflows",
                    "content": content_str,
                    "metadata": {**meta_base, "section": "workflows", "title": f"{entity_title} Workflows"}
                })

        # 6. Benefits Section
        benefits = data.get("benefits") or []
        if benefits:
            b_texts = []
            if isinstance(benefits, list):
                for b in benefits:
                    if isinstance(b, dict):
                        b_texts.append(f"{b.get('title', '')}: {b.get('description', '')}")
                    elif isinstance(b, str):
                        b_texts.append(b)
            if b_texts:
                content_str = f"{entity_title} Benefits & Value Proposition:\n" + "\n".join(b_texts)
                chunks.append({
                    "chunk_id": f"reg_{entity_id}_benefits",
                    "content": content_str,
                    "metadata": {**meta_base, "section": "benefits", "title": f"{entity_title} Benefits"}
                })

        # 7. Pricing Section
        pricing = data.get("pricing") or data.get("cost") or ""
        if pricing:
            pricing_str = json.dumps(pricing) if isinstance(pricing, (dict, list)) else str(pricing)
            content_str = f"{entity_title} Pricing & Licensing Information: {pricing_str}"
            chunks.append({
                "chunk_id": f"reg_{entity_id}_pricing",
                "content": content_str,
                "metadata": {**meta_base, "section": "pricing", "title": f"{entity_title} Pricing"}
            })

        # 8. FAQ Section
        faqs = data.get("faq") or []
        if faqs and isinstance(faqs, list):
            for f_idx, faq_item in enumerate(faqs):
                if isinstance(faq_item, dict):
                    q = faq_item.get("question") or ""
                    a = faq_item.get("answer") or ""
                    if q and a:
                        content_str = f"FAQ for {entity_title} - Question: {q} Answer: {a}"
                        chunks.append({
                            "chunk_id": f"reg_{entity_id}_faq_{f_idx}",
                            "content": content_str,
                            "metadata": {**meta_base, "section": "faq", "title": f"{entity_title} FAQ - {q}"}
                        })

        # 9. Contact Info Section
        if entity_type == "contact" or entity_id in ["contact_info", "location_info"]:
            phone = data.get("phone") or ""
            email = data.get("email") or ""
            hours = data.get("business_hours") or ""
            address = data.get("address") or ""
            contact_str = f"CittaAI Official Contact Information: Email: {email}, Phone: {phone}, Business Hours: {hours}, Office Address: {address}"
            chunks.append({
                "chunk_id": f"reg_{entity_id}_contact_details",
                "content": contact_str,
                "metadata": {**meta_base, "section": "contact", "title": "Contact Details"}
            })

    return chunks

async def build_vector_database(
    content_js_path: Optional[str] = None,
    db_path: Optional[str] = None,
    force: bool = False
) -> bool:
    """
    Idempotently builds unified vector_store.db containing BOTH Knowledge Registry entities and content.js copy.
    Uses atomic temporary database replacement and SHA-256 staleness tracking.
    """
    if not content_js_path:
        candidates = [
            os.path.join(ROOT_DIR, "..", "frontend", "src", "data", "content.js"),
            os.path.join(ROOT_DIR, "data", "content.js"),
            os.path.join(ROOT_DIR, "content.js"),
            "/app/frontend/src/data/content.js",
            "/app/data/content.js",
            "/app/content.js",
        ]
        for c in candidates:
            if os.path.exists(c):
                content_js_path = c
                break
        else:
            content_js_path = os.path.join(ROOT_DIR, "..", "frontend", "src", "data", "content.js")
    content_js_path = os.path.abspath(content_js_path)

    if not db_path:
        db_path = config.VECTOR_DB_PATH
    db_path = os.path.abspath(db_path)

    if not os.path.exists(content_js_path):
        logger.error(f"content.js not found at {content_js_path}")
        return False

    current_hash = compute_combined_knowledge_hash(content_js_path, REGISTRY_DIR)

    # 1. Deterministic Content Hash Check
    if not force and os.path.exists(db_path):
        target_store = VectorStore(db_path)
        existing_meta = target_store.get_metadata()
        stored_hash = existing_meta.get("content_hash", "")
        stored_version = existing_meta.get("version", "")
        stored_model = existing_meta.get("embedding_model", "")
        
        if (stored_hash and stored_hash == current_hash and 
            stored_version == INDEX_VERSION and 
            stored_model == config.EMBEDDING_MODEL and 
            target_store.get_chunk_count() > 0):
            logger.info(f"✓ Combined knowledge hash match ({current_hash[:8]}...). Unified vector DB up to date. Skipping build.")
            return True

    # 2. Build inside temporary database for atomic replacement
    tmp_db_path = db_path + ".tmp.db"
    if os.path.exists(tmp_db_path):
        try:
            os.remove(tmp_db_path)
        except Exception:
            pass

    logger.info(f"Building unified vector database in temporary file: {tmp_db_path}")
    tmp_store = VectorStore(tmp_db_path)
    tmp_store.rebuild_db()

    # 3. Parse content.js
    content_js_chunks = parse_content_js(content_js_path)
    logger.info(f"Parsed {len(content_js_chunks)} chunks from content.js")

    # 4. Parse Knowledge Registry entities
    registry_chunks = parse_registry_chunks(REGISTRY_DIR)
    logger.info(f"Parsed {len(registry_chunks)} chunks from Knowledge Registry JSON files")

    all_chunks = []
    # Add content.js chunks with prefix ID
    for i, chunk in enumerate(content_js_chunks):
        all_chunks.append({
            "chunk_id": f"content_js_{i}",
            "content": chunk["content"],
            "metadata": chunk["metadata"]
        })

    # Add content crawled from cittaai.com
    site_chunks = parse_site_chunks()
    logger.info(f"Parsed {len(site_chunks)} chunks from the crawled live website")
    registry_chunks = registry_chunks + site_chunks

    # Add Knowledge Registry chunks
    for chunk in registry_chunks:
        all_chunks.append({
            "chunk_id": chunk["chunk_id"],
            "content": chunk["content"],
            "metadata": chunk["metadata"]
        })

    if not all_chunks:
        logger.error("No chunks parsed from knowledge sources. Build aborted.")
        if os.path.exists(tmp_db_path):
            os.remove(tmp_db_path)
        return False

    # 5. Generate passage embeddings
    logger.info(f"Loading local embedding model: {config.EMBEDDING_MODEL}")
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)

    logger.info(f"Generating passage embeddings for {len(all_chunks)} total unified chunks...")
    for i, item in enumerate(all_chunks):
        chunk_id = item["chunk_id"]
        content_text = item["content"]
        # BGE's retrieval instruction belongs on queries only; passages are embedded as-is
        # (previously passages carried the query instruction too, which weakens asymmetric retrieval).
        emb = embedding_model.encode(content_text, normalize_embeddings=True).tolist()
        tmp_store.add_chunk(
            chunk_id=chunk_id,
            content=content_text,
            embedding=emb,
            metadata=item["metadata"]
        )

    # 6. Write extended version metadata
    chunk_count = tmp_store.get_chunk_count()
    metadata: Dict[str, Any] = {
        "version": INDEX_VERSION,
        "schema_version": "2.0.0",
        "parser_version": "2.0.0",
        "application_version": "2.0.0",
        "embedding_model": config.EMBEDDING_MODEL,
        "content_hash": current_hash,
        "registry_hash": __import__("index_integrity").compute_registry_hash(REGISTRY_DIR),
        "embedding_dimension": str(len(emb)) if all_chunks else "",
        "passage_prefix": "none",
        "chunk_count": str(chunk_count),
        "registry_chunk_count": str(len(registry_chunks) - len(site_chunks)),
        "site_chunk_count": str(len(site_chunks)),
        "content_js_chunk_count": str(len(content_js_chunks)),
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    tmp_store.write_metadata(metadata)

    # 7. Integrity Verification
    if chunk_count == 0:
        logger.error("Integrity assertion failed: chunk count is 0. Build aborted.")
        if os.path.exists(tmp_db_path):
            os.remove(tmp_db_path)
        return False

    # 8. Atomic Replacement
    logger.info(f"Atomically replacing {db_path} with newly built unified database...")
    atomic_replace_database(tmp_db_path, db_path)

    db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    logger.info(
        f"✓ Indexed {chunk_count} total chunks ({len(registry_chunks)} Registry + {len(content_js_chunks)} content.js) "
        f"| ✓ Database size: {db_size_mb} MB | ✓ Hash: {current_hash[:8]}... | ✓ Completed successfully"
    )
    return True

