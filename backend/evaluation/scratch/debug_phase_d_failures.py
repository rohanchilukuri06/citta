import sys
import json
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from evaluation.diagnostic_benchmark import DiagnosticBenchmarkRunner
from response_validator import validate_response

async def debug_phase_d():
    runner = DiagnosticBenchmarkRunner()
    print("=== DEBUGGING PHASE D FAILURES ===")
    
    for q_item in runner.questions:
        qid = q_item["id"]
        query = q_item["question"]
        gold_item = runner.gold.get(qid, {})
        
        # Run Phase D steps manually for this query to catch validator output
        emb = runner.embedding_model.encode(f"Represent this sentence for searching relevant passages: {query}", normalize_embeddings=True).tolist()
        chunks = runner.vector_store.query_hybrid(query_text=query, query_embedding=emb, top_k=5)
        reranked = runner.evidence_gate.evaluate_and_rerank(chunks)
        
        if not reranked:
            print(f"[{qid}] EVIDENCE_GATE FAIL | Query: {query}")
            continue
            
        ctx_text = "\n".join([c.get("text", "") for c in reranked])
        ans, _ = await runner.groq_client.generate(
            messages=[
                {"role": "system", "content": "You are a CittaAI assistant."},
                {"role": "user", "content": f"Context: {ctx_text}\nQuestion: {query}"}
            ]
        )
        
        # Validate with metrics
        res = validate_response(ans, return_metrics=True)
        is_valid = res[0]
        metrics = res[2] if len(res) > 2 else {}
        
        has_kw = any(kw.lower() in ans.lower() for kw in gold_item.get("keywords", []))
        
        if not is_valid or not has_kw:
            print(f"\n[{qid}] FAILED | Query: {query}")
            print(f"  Valid: {is_valid} | Has Keywords: {has_kw} (Expected: {gold_item.get('keywords')})")
            print(f"  Reasons: {metrics.get('reasons')}")
            print(f"  Response snippet: {ans[:150]}...")
        else:
            print(f"[{qid}] PASSED")

if __name__ == "__main__":
    asyncio.run(debug_phase_d())
