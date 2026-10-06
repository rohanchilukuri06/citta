import os
import sqlite3
import json
import re
import time
import logging
import numpy as np
from typing import List, Dict, Any, Tuple

import config

logger = logging.getLogger(__name__)

DB_PATH = config.VECTOR_DB_PATH

def atomic_replace_database(tmp_db_path: str, target_db_path: str):
    if not os.path.exists(tmp_db_path):
        raise FileNotFoundError(f"Temporary database file {tmp_db_path} does not exist")
    os.replace(tmp_db_path, target_db_path)

def _resolve_db_path(db_path: str) -> str:
    """Resolve database path relative to CWD, backend directory, or root workspace, prioritizing non-empty DB files."""
    if not db_path:
        db_path = config.VECTOR_DB_PATH

    # If already absolute and exists with content, return it
    if os.path.isabs(db_path) and os.path.exists(db_path) and os.path.getsize(db_path) > 0:
        return os.path.abspath(db_path)

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(backend_dir)

    candidates = [
        db_path,
        os.path.abspath(db_path),
        os.path.join(backend_dir, db_path),
        os.path.join(root_dir, db_path),
        os.path.join("/app", os.path.basename(db_path)),
        os.path.join("/app", db_path),
        os.path.join(backend_dir, os.path.basename(db_path)),
        os.path.join(root_dir, os.path.basename(db_path)),
    ]

    for candidate in candidates:
        if candidate and os.path.exists(candidate) and os.path.isfile(candidate):
            if os.path.getsize(candidate) > 0:
                return os.path.abspath(candidate)

    # Fallback to absolute candidate path
    if os.path.isabs(db_path):
        return db_path
    return os.path.abspath(os.path.join(backend_dir, os.path.basename(db_path)))

class VectorStore:
    def __init__(self, db_path: str = DB_PATH):
        self.raw_db_path = db_path
        self.db_path = _resolve_db_path(db_path)
        self._init_db()

    def _get_resolved_path(self) -> str:
        if hasattr(self, "db_path") and self.db_path and os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
            return self.db_path
        resolved = _resolve_db_path(self.raw_db_path)
        self.db_path = resolved
        return resolved

    def _init_db(self):
        target_path = self._get_resolved_path()
        db_dir = os.path.dirname(target_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                metadata TEXT NOT NULL,
                source TEXT NOT NULL
            )
        """)
        # Create metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_db_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def rebuild_db(self):
        target_path = self._get_resolved_path()
        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS chunks")
        cursor.execute("DROP TABLE IF EXISTS vector_db_metadata")
        conn.commit()
        conn.close()
        self._init_db()

    def get_metadata(self) -> Dict[str, str]:
        target_path = self._get_resolved_path()
        if not os.path.exists(target_path):
            return {}
        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT key, value FROM vector_db_metadata")
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}
        except Exception as e:
            logger.warning(f"[VectorStore] Failed to read metadata: {e}")
            return {}
        finally:
            conn.close()

    def write_metadata(self, metadata: Dict[str, Any]):
        target_path = self._get_resolved_path()
        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        try:
            for k, v in metadata.items():
                cursor.execute(
                    "INSERT OR REPLACE INTO vector_db_metadata (key, value) VALUES (?, ?)",
                    (str(k), str(v))
                )
            conn.commit()
        finally:
            conn.close()

    def validate_database_integrity(self) -> Dict[str, Any]:
        target_path = self._get_resolved_path()
        if not os.path.exists(target_path):
            return {"valid": False, "reason": f"Database file missing at {target_path}"}
        try:
            count = self.get_chunk_count()
            if count == 0:
                return {"valid": False, "reason": f"Database at {target_path} has 0 chunks"}
            meta = self.get_metadata()
            return {"valid": True, "count": count, "metadata": meta, "path": target_path}
        except Exception as e:
            return {"valid": False, "reason": f"Database error: {e}"}

    def warmup(self):
        """Execute a dummy query to warm up the SQLite vector database."""
        dummy_vector = [0.0] * 768
        try:
            _ = self.query_hybrid("warmup", dummy_vector, top_k=1)
        except Exception as e:
            logger.warning(f"[VectorStore] Warmup query exception: {e}")

    def add_chunk(self, chunk_id: str, content: str, embedding: List[float], metadata: Dict[str, Any]):
        target_path = self._get_resolved_path()
        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        emb_blob = np.array(embedding, dtype=np.float32).tobytes()
        metadata_str = json.dumps(metadata)
        source = metadata.get("source", "unknown")
        
        cursor.execute(
            "INSERT OR REPLACE INTO chunks (id, content, embedding, metadata, source) VALUES (?, ?, ?, ?, ?)",
            (chunk_id, content, emb_blob, metadata_str, source)
        )
        conn.commit()
        conn.close()

    def delete_document(self, source_name: str) -> int:
        target_path = self._get_resolved_path()
        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks WHERE source = ?", (source_name,))
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_deleted

    def get_all_documents(self) -> List[Dict[str, Any]]:
        target_path = self._get_resolved_path()
        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT source, COUNT(*), MAX(metadata) FROM chunks GROUP BY source")
        rows = cursor.fetchall()
        conn.close()
        
        docs = []
        for row in rows:
            source, count, sample_meta = row
            meta = {}
            try:
                meta = json.loads(sample_meta)
            except Exception:
                pass
            docs.append({
                "source": source,
                "chunk_count": count,
                "document_type": meta.get("doc_type", "unknown"),
                "last_updated": meta.get("last_updated", "")
            })
        return docs

    def get_chunk_count(self) -> int:
        target_path = self._get_resolved_path()
        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_chunk_count_for_page(self, page_url: str) -> int:
        target_path = self._get_resolved_path()
        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM chunks WHERE json_extract(metadata, '$.page') = ? OR json_extract(metadata, '$.url') = ?",
            (page_url, page_url)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        target_path = self._get_resolved_path()
        conn = sqlite3.connect(target_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT id, content, metadata, source FROM chunks")
        rows = cursor.fetchall()
        conn.close()
        
        chunks = []
        for row in rows:
            chunk_id, content, metadata_str, source = row
            try:
                metadata = json.loads(metadata_str)
            except Exception:
                metadata = {}
            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": metadata,
                "source": source
            })
        return chunks

    def query_hybrid(
        self, 
        query_text: str, 
        query_embedding: List[float], 
        intent: str = None, 
        top_k: int = 5,
        domain: str = None,
        requested_sections: List[str] = None
    ) -> List[Dict[str, Any]]:
        start_time = time.time()
        target_path = self._get_resolved_path()

        logger.info(f"[DEBUG] DATABASE PATH: {target_path}")
        logger.info(f"[DEBUG] DATABASE EXISTS: {os.path.exists(target_path)}")
        logger.info(f"[DEBUG] DATABASE SIZE: {os.path.getsize(target_path) if os.path.exists(target_path) else 0} bytes")
        logger.info(f"[DEBUG] CURRENT WORKING DIRECTORY: {os.getcwd()}")

        logger.debug(
            f"[VectorStore] query_hybrid called target_path={target_path}, "
            f"query_text='{query_text[:50] if query_text else ''}', domain={domain}, intent={intent}, requested_sections={requested_sections}, top_k={top_k}"
        )

        if not os.path.exists(target_path):
            logger.error(f"[VectorStore] DB file missing at resolved path: {target_path}")
            return []

        rows = []
        try:
            db_uri = f"file:{os.path.abspath(target_path)}?mode=ro"
            conn = sqlite3.connect(db_uri, uri=True, timeout=10.0)
            cursor = conn.cursor()
            cursor.execute("SELECT id, content, embedding, metadata, source FROM chunks")
            rows = cursor.fetchall()
            conn.close()
        except sqlite3.Error as se:
            try:
                conn = sqlite3.connect(target_path, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute("SELECT id, content, embedding, metadata, source FROM chunks")
                rows = cursor.fetchall()
                conn.close()
            except Exception as e:
                logger.error(f"[VectorStore] Failed to query SQLite database at {target_path}: {e}")
                return []
        except Exception as e:
            logger.error(f"[VectorStore] Failed to query SQLite database at {target_path}: {e}")
            return []

        logger.info(f"[DEBUG] TOTAL CHUNKS LOADED: {len(rows)}")

        if not rows:
            logger.warning(f"[VectorStore] 0 chunks returned from DB at {target_path}")
            return []

        # Validate query embedding
        if query_embedding is None or len(query_embedding) == 0:
            logger.error("[VectorStore] Provided query_embedding is None or empty.")
            return []

        query_vector = np.array(query_embedding, dtype=np.float32)
        if np.isnan(query_vector).any() or np.isinf(query_vector).any():
            logger.error("[VectorStore] Query embedding contains NaN or Inf values.")
            return []

        query_norm = float(np.linalg.norm(query_vector))
        expected_dim = len(query_vector)

        logger.info(f"[DEBUG] USER QUERY: {query_text}")
        logger.info(f"[DEBUG] DOMAIN: {domain}")
        logger.info(f"[DEBUG] INTENT: {intent}")
        logger.info(f"[DEBUG] REQUESTED SECTIONS: {requested_sections}")
        logger.info(f"[DEBUG] QUERY EMBEDDING DIMENSION: {expected_dim}")

        # Stopwords set for token extraction
        STOPWORDS = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
            "in", "on", "at", "to", "for", "with", "about", "against", "between",
            "into", "through", "during", "before", "after", "above", "below",
            "from", "up", "down", "out", "off", "over", "under",
            "again", "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "any", "both", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only", "own", "same",
            "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
            "should", "now", "what", "which", "who", "whom", "this", "that", "these", "those"
        }

        # Tokenize query text safely
        all_query_tokens = re.findall(r"\w+", query_text.lower()) if query_text else []
        query_terms = [t for t in all_query_tokens if t not in STOPWORDS and len(t) > 1]
        if not query_terms:
            query_terms = all_query_tokens  # Fallback if query was only stopwords

        # Domain Alias Mapping for CittaAI Registries & Categories
        DOMAIN_ALIASES = {
            "whatsapp": ["whatsapp", "product", "products", "whatsapp-marketing", "marketing", "whatsapp_marketing"],
            "influencer": ["influencer", "product", "products", "influencer-marketing", "influencer_marketing"],
            "ecommerce": ["ecommerce", "solution", "solutions", "ecommerce-os", "ecommerce_os"],
            "realestate": ["realestate", "real-estate", "real estate", "solution", "solutions", "real-estate-os", "real_estate_os"],
            "pharma": ["pharma", "solution", "solutions", "pharma-os", "pharma_os"],
            "smartcities": ["smartcities", "smart-cities", "smart cities", "solution", "solutions", "smart-cities-os", "smart_cities_os"],
            "education": ["education", "solution", "solutions", "education-os", "education_os"],
            "enterpriseai": ["enterpriseai", "enterprise-ai", "enterprise ai", "solution", "solutions", "enterprise-ai-os", "enterprise_ai_os"],
            "products": ["product", "products", "whatsapp", "influencer"],
            "services": ["service", "services", "solution", "solutions"],
            "solutions": ["solution", "solutions", "ecommerce", "realestate", "pharma", "smartcities", "education", "enterpriseai"],
            "company_info": ["about", "company", "brand", "history", "story"],
            "legal_compliance": ["legal", "compliance", "terms", "privacy"],
            "customer_stories": ["casestudies", "case-studies", "case studies", "cases"],
            "recognition_awards": ["recognition", "awards", "award"]
        }

        target_domain_clean = domain.strip().lower() if domain else None
        target_aliases = set()
        if target_domain_clean:
            target_aliases.add(target_domain_clean)
            target_aliases.add(target_domain_clean.replace("-", "").replace("_", "").replace(" ", ""))
            if target_domain_clean in DOMAIN_ALIASES:
                target_aliases.update(DOMAIN_ALIASES[target_domain_clean])

        results = []
        valid_chunks_count = 0
        corrupted_chunks_count = 0
        domain_match_count = 0

        logger.info("[DEBUG] Beginning Retrieval...")

        for row in rows:
            chunk_id, content, emb_bytes, metadata_str, source = row

            # 1. Parse Metadata safely
            metadata = {}
            if metadata_str:
                try:
                    metadata = json.loads(metadata_str)
                except Exception as e:
                    logger.warning(f"[VectorStore] Failed to parse JSON metadata for chunk {chunk_id}: {e}")
                    metadata = {}

            # 2. Intelligent Domain & Category Derivation
            chunk_category = str(metadata.get("category", "")).strip().lower()
            chunk_domain = str(metadata.get("domain", "")).strip().lower()

            if not chunk_domain or chunk_domain in ["general", "unknown"]:
                if chunk_category:
                    chunk_domain = chunk_category
                elif "page" in metadata and metadata["page"]:
                    page_val = str(metadata["page"]).strip().lower().strip("/")
                    chunk_domain = page_val.split("/")[0] if page_val else "general"
                elif "url" in metadata and metadata["url"]:
                    url_val = str(metadata["url"]).strip().lower().strip("/")
                    chunk_domain = url_val.split("/")[0] if url_val else "general"
                elif source:
                    chunk_domain = str(source).replace(".js", "").replace(".json", "").strip().lower()
                else:
                    chunk_domain = "general"

            title_clean = str(metadata.get("title", "")).strip().lower()
            source_clean = str(source).strip().lower()
            page_clean = str(metadata.get("page", "")).strip().lower()
            entity_id_clean = str(metadata.get("entity_id", "")).strip().lower()
            entity_type_clean = str(metadata.get("entity_type", "")).strip().lower()
            section_clean = str(metadata.get("section", "")).strip().lower()

            # 3. Soft Domain Matching via Alias Expansion
            is_domain_match = False
            if target_aliases:
                chunk_terms = {
                    chunk_domain, chunk_category, title_clean, source_clean, page_clean,
                    entity_id_clean, entity_type_clean, section_clean
                }
                chunk_terms_clean = {t.replace("-", "").replace("_", "").replace(" ", "") for t in chunk_terms if t}
                
                for alias in target_aliases:
                    alias_clean = alias.replace("-", "").replace("_", "").replace(" ", "")
                    if any(alias_clean in term for term in chunk_terms_clean if term):
                        is_domain_match = True
                        domain_match_count += 1
                        break

            # 4. Soft Intent & Aspect Section Matching
            is_intent_match = False
            if intent and intent.lower() != "generalai":
                intent_clean = intent.lower()
                if (intent_clean == "legal" and chunk_category == "legal") or \
                   (intent_clean == "products" and chunk_category in ["product", "solution"]) or \
                   (intent_clean == "services" and chunk_category in ["service", "solution"]) or \
                   (intent_clean == "service_pricing" and chunk_category in ["product", "service", "solution"]) or \
                   (intent_clean == "recognition" and chunk_category == "recognition") or \
                   (intent_clean == "casestudies" and chunk_category in ["casestudies", "cases"]) or \
                   (intent_clean == "contact" and chunk_category == "contact"):
                    is_intent_match = True

            # Aspect-Aware Section Boost
            is_section_match = False
            if requested_sections and section_clean:
                SECTION_ALIASES = {
                    "workflows": ["workflows", "how_it_works", "process", "implementation", "hero"],
                    "how_it_works": ["workflows", "how_it_works", "process", "implementation"],
                    "capabilities": ["capabilities", "features", "specs", "hero"],
                    "benefits": ["benefits", "why_us"],
                    "overview": ["overview", "hero", "about_lead", "about_story", "brand"],
                    "target_users": ["target_users", "audience"],
                    "pricing": ["pricing", "cost"],
                    "contact": ["contact", "contact_info", "location"],
                    "faq": ["faq"],
                    "case_study": ["cases", "case_study", "case_studies"],
                    "recognition": ["awards", "recognition"]
                }
                for req_sec in requested_sections:
                    sec_clean = str(req_sec).strip().lower()
                    if not sec_clean:
                        continue
                    if sec_clean in section_clean or section_clean in sec_clean:
                        is_section_match = True
                        break
                    aliases = SECTION_ALIASES.get(sec_clean, [])
                    if any(a in section_clean or section_clean in a for a in aliases):
                        is_section_match = True
                        break

            # 5. Embedding Unpacking & Dimension Validation
            semantic_score = 0.0
            try:
                if isinstance(emb_bytes, (bytes, memoryview)):
                    chunk_vector = np.frombuffer(emb_bytes, dtype=np.float32)
                else:
                    chunk_vector = np.array(emb_bytes, dtype=np.float32)

                if len(chunk_vector) != expected_dim:
                    logger.warning(
                        f"[VectorStore] Chunk {chunk_id} dimension mismatch: expected {expected_dim}, got {len(chunk_vector)}."
                    )
                    corrupted_chunks_count += 1
                    chunk_vector = None
                elif np.isnan(chunk_vector).any() or np.isinf(chunk_vector).any():
                    logger.warning(f"[VectorStore] Chunk {chunk_id} contains NaN/Inf embeddings.")
                    corrupted_chunks_count += 1
                    chunk_vector = None
                else:
                    valid_chunks_count += 1

                if chunk_vector is not None:
                    chunk_norm = float(np.linalg.norm(chunk_vector))
                    if query_norm > 1e-9 and chunk_norm > 1e-9:
                        dot_product = float(np.dot(query_vector, chunk_vector))
                        raw_cosine = dot_product / (query_norm * chunk_norm)
                        raw_cosine = float(np.clip(raw_cosine, -1.0, 1.0))
                        semantic_score = max(0.0, raw_cosine)
            except Exception as e:
                logger.warning(f"[VectorStore] Failed to process embedding for chunk {chunk_id}: {e}")
                corrupted_chunks_count += 1

            # 6. Keyword Match Score
            content_lower = content.lower() if content else ""
            content_words = set(re.findall(r"\w+", content_lower))
            
            keyword_score = 0.0
            if query_terms and content_words:
                matching_words = set(query_terms) & content_words
                denom = len(set(query_terms))
                word_overlap_ratio = len(matching_words) / denom if denom > 0 else 0.0
                phrase_bonus = 0.20 if (query_text and query_text.lower() in content_lower) else 0.0
                keyword_score = min(1.0, word_overlap_ratio + phrase_bonus)

            # 7. Robust Score Fusion: Hybrid Convex Blend
            if keyword_score > 0:
                fusion_score = (0.70 * semantic_score) + (0.30 * keyword_score)
            else:
                fusion_score = semantic_score * 0.90

            if is_domain_match:
                fusion_score += 0.15
            if is_intent_match:
                fusion_score += 0.05
            if is_section_match:
                fusion_score += 0.10

            fusion_score = float(min(1.0, max(0.0, fusion_score)))

            results.append({
                "id": str(chunk_id),
                "content": content,
                "metadata": metadata,
                "source": source,
                "score": fusion_score,
                "semantic_score": float(semantic_score),
                "keyword_score": float(keyword_score),
                "domain_match": is_domain_match,
                "intent_match": is_intent_match,
                "section_match": is_section_match,
                "derived_domain": chunk_domain
            })

        # 8. Deterministic Ranking: (score DESC, semantic_score DESC, id ASC)
        results.sort(key=lambda x: (-x["score"], -x["semantic_score"], str(x["id"])))
        
        # Log details for Top 5 highest scored chunks
        logger.info("[DEBUG] --- TOP 5 HIGHEST SCORED CHUNKS ---")
        for idx, chunk in enumerate(results[:5], start=1):
            chunk_title = chunk.get("metadata", {}).get("title", "N/A")
            chunk_cat = chunk.get("metadata", {}).get("category", "N/A")
            logger.info(
                f"[DEBUG] Top Chunk #{idx} | "
                f"Chunk ID: {chunk['id']} | "
                f"Title: {chunk_title} | "
                f"Category: {chunk_cat} | "
                f"Derived Domain: {chunk.get('derived_domain')} | "
                f"Source: {chunk['source']} | "
                f"Semantic Score: {chunk['semantic_score']:.4f} | "
                f"Keyword Score: {chunk['keyword_score']:.4f} | "
                f"Domain Match: {chunk['domain_match']} | "
                f"Intent Match: {chunk['intent_match']} | "
                f"Final Score: {chunk['score']:.4f}"
            )

        max_score = results[0]["score"] if results else 0.0
        elapsed_ms = (time.time() - start_time) * 1000.0

        logger.info(f"[DEBUG] Maximum Score: {max_score:.4f}")
        logger.info(f"[DEBUG] Top K: {top_k}")
        logger.info(f"[DEBUG] Number of Results Returned: {len(results[:top_k])}")
        logger.info(f"[DEBUG] Elapsed Retrieval Time: {elapsed_ms:.2f}ms")
        
        logger.info(
            f"[VectorStore] Query hybrid finished in {elapsed_ms:.2f}ms. "
            f"Scanned: {len(rows)}, Valid: {valid_chunks_count}, Corrupted: {corrupted_chunks_count}, "
            f"Domain matches: {domain_match_count}, Max Score: {max_score:.4f}, Returning top {min(top_k, len(results))} chunks."
        )

        return results[:top_k]


# --- Ingestion Parser for content.js ---

def clean_js_comments(text: str) -> str:
    # Remove single line comments
    text = re.sub(r"//.*", "", text)
    # Remove block comments
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    return text

def parse_javascript_object(js_code: str, var_name: str) -> Dict[str, Any]:
    """Helper to extract a variable declaration as dict if simple, or return chunks of key text."""
    pattern = rf"export\s+const\s+{var_name}\s*=\s*([\s\S]*?);"
    match = re.search(pattern, js_code)
    if not match:
        return {}
    
    obj_body = match.group(1).strip()
    lines = [line.strip() for line in obj_body.split("\n") if line.strip()]
    return {"raw_lines": lines}

def parse_content_js(file_path: str) -> List[Dict[str, Any]]:
    """Parse content.js into highly structured semantic chunks for embedding."""
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = clean_js_comments(content)
    chunks = []
    timestamp = str(os.path.getmtime(file_path))

    sections_to_parse = [
        ("WHATSAPP", "product", "/products/whatsapp-marketing", "whatsapp_marketing"),
        ("INFLUENCER", "product", "/products/influencer-marketing", "influencer_marketing"),
        ("ECOMMERCE", "solution", "/solutions/ecommerce-os", "ecommerce_os"),
        ("REALESTATE", "solution", "/solutions/real-estate-os", "real_estate_os"),
        ("PHARMA", "solution", "/solutions/pharma-os", "pharma_os"),
        ("SMARTCITIES", "solution", "/solutions/smart-cities-os", "smart_cities_os"),
        ("EDUCATION", "solution", "/solutions/education-os", "education_os"),
        ("ENTERPRISEAI", "solution", "/solutions/enterprise-ai-os", "enterprise_ai_os"),
    ]

    for var_name, kind, url, ent_id in sections_to_parse:
        pattern = rf"export\s+const\s+{var_name}\s*=\s*\{{([\s\S]*?)\}};"
        match = re.search(pattern, content)
        if match:
            body = match.group(1)
            name_m = re.search(r"name:\s*\"([^\"]+)\"", body)
            hero_m = re.search(r"hero:\s*\"([^\"]+)\"", body)
            subtitle_m = re.search(r"subtitle:\s*\"([^\"]+)\"", body)
            
            name = name_m.group(1) if name_m else var_name.capitalize()
            hero = hero_m.group(1) if hero_m else ""
            subtitle = subtitle_m.group(1) if subtitle_m else ""

            main_text = f"CittaAI {kind.capitalize()} - {name}: {hero} {subtitle}"
            chunks.append({
                "content": main_text,
                "metadata": {
                    "source": "content.js",
                    "entity_id": ent_id,
                    "page": url,
                    "section": "hero",
                    "title": name,
                    "category": kind,
                    "domain": kind,
                    "url": url,
                    "last_updated": timestamp,
                    "doc_type": "web_copy"
                }
            })

            cap_pattern = r"\{\s*t:\s*\"([^\"]+)\"\s*,\s*d:\s*\"([^\"]+)\"\s*\}"
            capabilities = re.findall(cap_pattern, body)
            for title, desc in capabilities:
                chunks.append({
                    "content": f"CittaAI {name} Capability: {title} - {desc}",
                    "metadata": {
                        "source": "content.js",
                        "entity_id": ent_id,
                        "page": url,
                        "section": "capabilities",
                        "title": f"{name} - {title}",
                        "category": kind,
                        "domain": kind,
                        "url": url,
                        "last_updated": timestamp,
                        "doc_type": "web_copy"
                    }
                })

    # Ingest RECOGNITION
    rec_pattern = r"export\s+const\s+RECOGNITION\s*=\s*\{([\s\S]*?)\};"
    rec_match = re.search(rec_pattern, content)
    if rec_match:
        body = rec_match.group(1)
        award_blocks = re.findall(r"\{\s*name:\s*\"([^\"]+)\"\s*,\s*subtitle:\s*\"([^\"]+)\"\s*,\s*body:\s*\"([^\"]+)\"\s*,\s*org:\s*\"([^\"]+)\"", body)
        for name, subtitle, award_body, org in award_blocks:
            chunks.append({
                "content": f"CittaAI Award & Recognition: {name} ({subtitle}) - {award_body}. Organized by {org}.",
                "metadata": {
                    "source": "content.js",
                    "page": "/recognition",
                    "section": "awards",
                    "title": name,
                    "category": "recognition",
                    "domain": "recognition",
                    "url": "/recognition",
                    "last_updated": timestamp,
                    "doc_type": "web_copy"
                }
            })

    # Ingest CASESTUDIES
    case_pattern = r"export\s+const\s+CASESTUDIES\s*=\s*\{([\s\S]*?)\};"
    case_match = re.search(case_pattern, content)
    if case_match:
        body = case_match.group(1)
        cases = re.findall(r"\{\s*brand:\s*\"([^\"]+)\"\s*,\s*metric:\s*\"([^\"]+)\"\s*,\s*label:\s*\"([^\"]+)\"\s*,\s*desc:\s*\"([^\"]+)\"", body)
        for brand, metric, label, desc in cases:
            chunks.append({
                "content": f"CittaAI Case Study - {brand}: Achieved {metric} ({label}) - {desc}",
                "metadata": {
                    "source": "content.js",
                    "page": "/case-studies",
                    "section": "cases",
                    "title": f"Case Study: {brand}",
                    "category": "casestudies",
                    "domain": "casestudies",
                    "url": "/case-studies",
                    "last_updated": timestamp,
                    "doc_type": "web_copy"
                }
            })

    # Ingest ABOUT
    about_pattern = r"export\s+const\s+ABOUT\s*=\s*\{([\s\S]*?)\};"
    about_match = re.search(about_pattern, content)
    if about_match:
        body = about_match.group(1)
        lead_m = re.search(r"lead:\s*\"([^\"]+)\"", body)
        story_m = re.search(r"story:\s*\"([^\"]+)\"", body)
        
        if lead_m:
            chunks.append({
                "content": f"About CittaAI: {lead_m.group(1)}",
                "metadata": {
                    "source": "content.js",
                    "page": "/about",
                    "section": "about_lead",
                    "title": "About CittaAI",
                    "category": "about",
                    "domain": "about",
                    "url": "/about",
                    "last_updated": timestamp,
                    "doc_type": "web_copy"
                }
            })
            
        if story_m:
            chunks.append({
                "content": f"CittaAI History & Story: {story_m.group(1)}",
                "metadata": {
                    "source": "content.js",
                    "page": "/about",
                    "section": "about_story",
                    "title": "Our Story",
                    "category": "about",
                    "domain": "about",
                    "url": "/about",
                    "last_updated": timestamp,
                    "doc_type": "web_copy"
                }
            })
            
        why_items = re.findall(r"\{\s*t:\s*\"([^\"]+)\"\s*,\s*d:\s*\"([^\"]+)\"\s*\}", body)
        for title, desc in why_items:
            chunks.append({
                "content": f"Why choose CittaAI: {title} - {desc}",
                "metadata": {
                    "source": "content.js",
                    "page": "/about",
                    "section": "why_us",
                    "title": f"Why Choose Us: {title}",
                    "category": "about",
                    "domain": "about",
                    "url": "/about",
                    "last_updated": timestamp,
                    "doc_type": "web_copy"
                }
            })

    # Ingest BRAND constants
    brand_pattern = r"export\s+const\s+BRAND\s*=\s*\{([\s\S]*?)\};"
    brand_match = re.search(brand_pattern, content)
    if brand_match:
        body = brand_match.group(1)
        tag_m = re.search(r"tagline:\s*\"([^\"]+)\"", body)
        driven_m = re.search(r"drivenBy:\s*\"([^\"]+)\"", body)
        pos_m = re.search(r"positioning:\s*\"([^\"]+)\"", body)
        
        brand_info = []
        if tag_m: brand_info.append(f"Tagline: {tag_m.group(1)}.")
        if driven_m: brand_info.append(f"Philosophy: {driven_m.group(1)}.")
        if pos_m: brand_info.append(f"Positioning: {pos_m.group(1)}.")
        
        chunks.append({
            "content": f"CittaAI Brand Core Info: " + " ".join(brand_info),
            "metadata": {
                "source": "content.js",
                "page": "/",
                "section": "brand",
                "title": "CittaAI Brand Info",
                "category": "company",
                "domain": "company",
                "url": "/",
                "last_updated": timestamp,
                "doc_type": "web_copy"
            }
        })

    # Ingest CONTACT Info
    contact_pattern = r"export\s+const\s+CONTACT\s*=\s*\{([\s\S]*?)\};"
    contact_match = re.search(contact_pattern, content)
    if contact_match:
        body = contact_match.group(1)
        phone_m = re.search(r"phone:\s*\"([^\"]+)\"", body)
        email_m = re.search(r"email:\s*\"([^\"]+)\"", body)
        address_m = re.search(r"address:\s*\"([^\"]+)\"", body)
        
        contact_info = []
        if phone_m: contact_info.append(f"Phone: {phone_m.group(1)}.")
        if email_m: contact_info.append(f"Email: {email_m.group(1)}.")
        if address_m: contact_info.append(f"Office Address: {address_m.group(1)}.")
        
        chunks.append({
            "content": f"CittaAI Contact Details: " + " ".join(contact_info),
            "metadata": {
                "source": "content.js",
                "page": "/contact",
                "section": "contact_info",
                "title": "Contact Information",
                "category": "contact",
                "domain": "contact",
                "url": "/contact",
                "last_updated": timestamp,
                "doc_type": "web_copy"
            }
        })

    return chunks
