import sys
import json
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from evaluation.diagnostic_benchmark import DiagnosticBenchmarkRunner
from response_validator import validate_response

async def run_forensic_analysis():
    runner = DiagnosticBenchmarkRunner()
    print("=" * 80)
    print("FORENSIC ANALYSIS: INSPECTING ALL PIPELINE FAILURES IN DIAGNOSTIC HOLDOUT")
    print("=" * 80)
    
    analysis_results = []
    
    for q_item in runner.questions:
        qid = q_item["id"]
        query = q_item["question"]
        gold_item = runner.gold.get(qid, {})
        
        emb = runner.embedding_model.encode(f"Represent this sentence for searching relevant passages: {query}", normalize_embeddings=True).tolist()
        chunks = runner.vector_store.query_hybrid(query_text=query, query_embedding=emb, top_k=5)
        reranked = runner.evidence_gate.evaluate_and_rerank(chunks)
        
        if not reranked:
            analysis_results.append({
                "id": qid,
                "query": query,
                "stage": "EVIDENCE_GATE",
                "reason": "Top retrieved chunks failed evidence gate thresholds",
                "chunks_count": len(chunks)
            })
            continue
            
        ctx_text = "\n".join([c.get("text", "") for c in reranked])
        ans, _ = await runner.groq_client.generate(
            messages=[
                {"role": "system", "content": "You are a CittaAI assistant."},
                {"role": "user", "content": f"Context: {ctx_text}\nQuestion: {query}"}
            ]
        )
        
        res = validate_response(ans, return_metrics=True)
        is_valid = res[0]
        metrics = res[2] if len(res) > 2 else {}
        has_kw = any(kw.lower() in ans.lower() for kw in gold_item.get("keywords", [])) or not gold_item.get("is_in_domain")
        
        status = "PASSED" if is_valid and has_kw else "FAILED"
        
        record = {
            "id": qid,
            "query": query,
            "expected_entity": gold_item.get("expected_entity"),
            "expected_keywords": gold_item.get("keywords"),
            "is_valid": is_valid,
            "has_keywords": has_kw,
            "status": status,
            "validator_reasons": metrics.get("reasons", []),
            "response_snippet": ans.replace("\n", " ")[:200]
        }
        
        analysis_results.append(record)
        
        safe_ans = ans.replace('\n', ' ').encode('ascii', errors='replace').decode('ascii')[:150]
        print(f"\n[{qid}] {status} | Query: '{query}'")
        if status == "FAILED":
            print(f"  Validator Reasons: {metrics.get('reasons')}")
            print(f"  Keywords Matched: {has_kw} (Expected: {gold_item.get('keywords')})")
            print(f"  Response: {safe_ans}...")
            
    output_path = ROOT_DIR / "evaluation" / "forensic_analysis_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_forensic_analysis())
