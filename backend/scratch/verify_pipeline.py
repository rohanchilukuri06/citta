import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import sqlite3
import urllib.request
from typing import Dict, Any, List

import config
from vector_store import VectorStore
from vector_indexer import REGISTRY_DIR, parse_registry_chunks, parse_content_js, compute_combined_knowledge_hash

def run_verification():
    print("=" * 80)
    print("CITTAAI VECTOR DATABASE & INDEXING PIPELINE VERIFICATION REPORT")
    print("=" * 80)
    
    # 1. Discovery
    manifest_path = REGISTRY_DIR / "manifest.json"
    manifest_data = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    registries = manifest_data.get("registries", [])
    print(f"\n1. Registry Discovery:")
    print(f"   - Registry Root: {REGISTRY_DIR}")
    print(f"   - Manifest Path: {manifest_path} (Exists: {manifest_path.exists()})")
    print(f"   - Active Registries Configured: {len(registries)}")
    
    # 2. Chunk Generation
    reg_chunks = parse_registry_chunks(REGISTRY_DIR)
    cjs_chunks = parse_content_js(config.CONTENT_JS_PATH if hasattr(config, "CONTENT_JS_PATH") else "c:\\Users\\Rohan chilukuri\\citta\\frontend\\src\\data\\content.js")
    print(f"\n2. Runtime Chunk Generation:")
    print(f"   - Registry Chunks Generated: {len(reg_chunks)}")
    print(f"   - content.js Chunks Generated: {len(cjs_chunks)}")
    print(f"   - Total Unified Chunks: {len(reg_chunks) + len(cjs_chunks)}")
    
    # 3. Database Direct Inspection
    db_path = config.VECTOR_DB_PATH
    print(f"\n3. Database Direct Inspection ({db_path}):")
    if not os.path.exists(db_path):
        print(f"   [ERROR] Database file does not exist at {db_path}!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM chunks")
    total_db_chunks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM chunks WHERE source = 'knowledge_registry'")
    reg_db_chunks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM chunks WHERE source = 'content.js'")
    cjs_db_chunks = cursor.fetchone()[0]
    
    cursor.execute("SELECT key, value FROM vector_db_metadata")
    db_meta = {row[0]: row[1] for row in cursor.fetchall()}
    
    print(f"   - Total Chunks in DB: {total_db_chunks}")
    print(f"   - Registry Chunks in DB: {reg_db_chunks}")
    print(f"   - content.js Chunks in DB: {cjs_db_chunks}")
    print(f"   - Metadata Stored in DB: {json.dumps(db_meta, indent=2)}")
    
    # Chunks per Entity
    cursor.execute("SELECT id, content, metadata, source FROM chunks WHERE source = 'knowledge_registry'")
    reg_rows = cursor.fetchall()
    
    entity_counts = {}
    section_counts = {}
    source_counts = {}
    content_lengths = []
    
    for row in reg_rows:
        cid, content, meta_raw, src = row
        meta = json.loads(meta_raw)
        eid = meta.get("entity_id", "unknown")
        sec = meta.get("section", "unknown")
        
        entity_counts[eid] = entity_counts.get(eid, 0) + 1
        section_counts[sec] = section_counts.get(sec, 0) + 1
        source_counts[src] = source_counts.get(src, 0) + 1
        content_lengths.append(len(content))
        
    print(f"\n4. Chunks per Entity ({len(entity_counts)} entities):")
    for eid, count in sorted(entity_counts.items()):
        print(f"   - {eid}: {count} chunks")
        
    print(f"\n5. Chunks per Section:")
    for sec, count in sorted(section_counts.items(), key=lambda x: -x[1]):
        print(f"   - {sec}: {count} chunks")
        
    if content_lengths:
        min_len = min(content_lengths)
        max_len = max(content_lengths)
        avg_len = sum(content_lengths) / len(content_lengths)
        print(f"\n6. Chunk Length Stats (Characters):")
        print(f"   - Min Length: {min_len} chars (~{min_len // 4} tokens)")
        print(f"   - Avg Length: {avg_len:.1f} chars (~{int(avg_len // 4)} tokens)")
        print(f"   - Max Length: {max_len} chars (~{max_len // 4} tokens)")

    print(f"\n7. Representative 10 Actual Database Records from Knowledge Registry:")
    for i, row in enumerate(reg_rows[:10], start=1):
        cid, content, meta_raw, src = row
        meta = json.loads(meta_raw)
        print(f"   Record #{i}:")
        print(f"     ID: {cid}")
        print(f"     Entity ID: {meta.get('entity_id')}")
        print(f"     Section: {meta.get('section')}")
        print(f"     Source: {src}")
        print(f"     Content Length: {len(content)} chars")
        print(f"     Snippet: {content[:100]}...")

    conn.close()

    # 8. Hybrid Retrieval Testing
    print("\n8. VectorStore.query_hybrid() Semantic Retrieval Tests:")
    vs = VectorStore(db_path)
    
    test_queries = [
        "What can you help hospitals with?",
        "I run a college. What could you offer us?",
        "I'm looking for help managing creators.",
        "How could you improve customer communication?",
        "What can you do for property businesses?",
        "What kind of data engineering work do you provide?",
        "I need help developing an AI strategy.",
        "Can you help with digital marketing?",
        "How can I work with your team?",
        "What companies have you worked with?",
        "What recognition has CittaAI received?"
    ]
    
    # Load embedding model to generate query embeddings
    from sentence_transformers import SentenceTransformer
    emb_model = SentenceTransformer(config.EMBEDDING_MODEL)
    
    for q in test_queries:
        if "bge" in config.EMBEDDING_MODEL.lower():
            processed_q = f"Represent this sentence for searching relevant passages: {q}"
        else:
            processed_q = q
        q_emb = emb_model.encode(processed_q, normalize_embeddings=True).tolist()
        
        results = vs.query_hybrid(query_text=q, query_embedding=q_emb, top_k=3)
        top_res = results[0] if results else {}
        top_meta = top_res.get("metadata", {})
        top_eid = top_meta.get("entity_id", "N/A")
        top_sec = top_meta.get("section", "N/A")
        top_title = top_meta.get("title", top_res.get("id", "N/A"))
        score = top_res.get("score", 0.0)
        source = top_res.get("source", "N/A")
        
        print(f"\n   Query: '{q}'")
        print(f"     Top Match: [{source}] {top_title} (Entity: {top_eid}, Section: {top_sec})")
        print(f"     Score: {score:.4f} | Semantic Score: {top_res.get('semantic_score', 0):.4f}")

    # 9. /api/chat E2E Retrieval Path
    print("\n9. End-to-End /api/chat Retrieval Path Verification:")
    for q in test_queries[:3]:
        try:
            req = urllib.request.Request(
                "http://localhost:8000/api/chat",
                data=json.dumps({"session_id": "test_verification_sess", "message": q}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            r = urllib.request.urlopen(req)
            lines = [line.decode("utf-8").strip() for line in r if "data:" in line.decode("utf-8")]
            done_line = [l for l in lines if '"done": true' in l]
            if done_line:
                data_json = json.loads(done_line[0].replace("data: ", ""))
                citations = data_json.get("citations", [])
                source = data_json.get("source", "")
                attr = data_json.get("attribution", {})
                print(f"\n   Chat Query: '{q}'")
                print(f"     Source: {source}")
                print(f"     Citations: {citations}")
                print(f"     Attribution Entity: {attr.get('entity')}")
        except Exception as e:
            print(f"   Chat API Error for query '{q}': {e}")

if __name__ == "__main__":
    run_verification()
