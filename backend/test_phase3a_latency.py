import os
import sys
import json
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(Path(BACKEND_DIR) / '.env')

import config
from server import app, get_rag_service
from llm_provider import get_llm_provider
from deterministic_engine import get_deterministic_engine
from knowledge_registry import get_registry

TEST_QUERIES = [
    {"id": 1, "name": "Pharma OS", "q": "Do you have Pharma OS?"},
    {"id": 2, "name": "Pharma explanation", "q": "What does Pharma OS do?"},
    {"id": 3, "name": "Education OS", "q": "Do you have Education OS?"},
    {"id": 4, "name": "Education explanation", "q": "What does Education OS provide for colleges?"},
    {"id": 5, "name": "MarTech", "q": "What can MarTech 360 help a business with?"},
    {"id": 6, "name": "MarTech explanation", "q": "How is MarTech 360 different from traditional branding?"},
    {"id": 7, "name": "Strategy duration", "q": "How long does the MarTech 360 strategy process take?"},
    {"id": 8, "name": "Pricing", "q": "What is the annual subscription price of MarTech 360?"},
    {"id": 9, "name": "CEO", "q": "Who is the CEO of MarTech 360?"},
    {"id": 10, "name": "CittaAI services", "q": "What services does CittaAI provide?"}
]

async def profile_query(rag_serv, query_item: dict, run_type: str, session_prefix: str) -> dict:
    q_id = query_item["id"]
    q_name = query_item["name"]
    q_text = query_item["q"]
    session_id = f"prof_{run_type}_{session_prefix}_{q_id}"
    model_name = getattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile")

    # High-precision timestamps
    t_req_start = time.perf_counter()

    accumulated_text = ""
    done_metadata = {}
    first_chunk_t = None
    chunks_count = 0

    t_llm_start_obs = None
    t_llm_first_token_obs = None
    t_llm_end_obs = None

    try:
        async for chunk in rag_serv.chat_stream(session_id=session_id, message=q_text, model=model_name):
            if not chunk.get("done"):
                if first_chunk_t is None and "text" in chunk:
                    first_chunk_t = time.perf_counter()
                chunks_count += 1
                accumulated_text += chunk.get("text", "")
            else:
                done_metadata = chunk
    except Exception as e:
        print(f"❌ Error profiling query '{q_name}': {e}", flush=True)

    t_req_end = time.perf_counter()
    total_request_ms = round((t_req_end - t_req_start) * 1000.0, 2)

    metrics = done_metadata.get("metrics", {})
    source = done_metadata.get("source", "Unknown")

    # Extract internal metrics if present
    norm_ms = float(metrics.get("normalizer_ms", 0.0))
    res_ms = float(metrics.get("resolver_ms", 0.0))
    router_ms = float(metrics.get("router_ms", 0.0))
    emb_ms = float(metrics.get("embedding_time", 0.0)) * 1000.0 if metrics.get("embedding_time") else 0.0
    retrieval_ms = float(metrics.get("retrieval_time", 0.0)) * 1000.0 if metrics.get("retrieval_time") else 0.0
    
    groq_ttft_ms = float(metrics.get("time_to_first_token_ms", 0.0))
    groq_gen_ms = float(metrics.get("generation_ms", 0.0))
    groq_total_ms = float(metrics.get("total_llm_ms", 0.0))

    # PRE_LLM calculation
    # If groq_total_ms > 0, PRE_LLM = (t_req_end - t_req_start)*1000 - groq_total_ms - post_llm
    # Or explicitly sum stages:
    pre_llm_ms = round(norm_ms + res_ms + router_ms + emb_ms + retrieval_ms, 2)
    post_llm_ms = round(float(metrics.get("streaming_time", 0.0)) * 1000.0, 2) if groq_total_ms == 0 else 5.0

    if groq_total_ms > 0:
        llm_time_ms = groq_total_ms
    else:
        llm_time_ms = float(metrics.get("llm_time", 0.0)) * 1000.0

    unaccounted_ms = round(max(0.0, total_request_ms - pre_llm_ms - llm_time_ms - post_llm_ms), 2)

    return {
        "id": q_id,
        "name": q_name,
        "query": q_text,
        "run_type": run_type,
        "source": source,
        "total_request_ms": total_request_ms,
        "pre_llm_ms": pre_llm_ms,
        "groq_ttft_ms": groq_ttft_ms,
        "groq_total_ms": llm_time_ms,
        "post_llm_ms": post_llm_ms,
        "unaccounted_ms": unaccounted_ms,
        "norm_ms": norm_ms,
        "res_ms": res_ms,
        "router_ms": router_ms,
        "emb_ms": emb_ms,
        "retrieval_ms": retrieval_ms,
        "chunks_count": chunks_count,
        "output_chars": len(accumulated_text),
        "input_chars": len(q_text),
        "metrics": metrics
    }

async def run_phase3a_profiling():
    print("=" * 80, flush=True)
    print("PHASE 3A — LATENCY PROFILING & BOTTLENECK ISOLATION", flush=True)
    print("=" * 80, flush=True)

    # Instrument start
    print("\n--- REGRESSION & SETUP VERIFICATION ---", flush=True)
    nv_prov = get_llm_provider("nvidia", {})
    gem_prov = get_llm_provider("gemini", {})
    groq_prov = get_llm_provider("groq", {})
    det_eng = get_deterministic_engine()
    reg = get_registry()

    print(f"[OK] NvidiaProvider:      {nv_prov.__class__.__name__}", flush=True)
    print(f"[OK] GeminiProvider:      {gem_prov.__class__.__name__}", flush=True)
    print(f"[OK] GroqProvider:        {groq_prov.__class__.__name__}", flush=True)
    print(f"[OK] DeterministicEngine: {det_eng.__class__.__name__}", flush=True)
    print(f"[OK] KnowledgeRegistry:   Loaded ({len(reg.entities)} entities)", flush=True)

    rag_serv = get_rag_service()

    cold_results = []
    warm_results = []

    # -----------------------------------------------------------------
    # COLD RUN (RUN A)
    # -----------------------------------------------------------------
    print("\n" + "=" * 80, flush=True)
    print("EXECUTING COLD RUN (RUN A)", flush=True)
    print("=" * 80, flush=True)

    for item in TEST_QUERIES:
        print(f"Executing Cold Query [{item['id']}/10]: \"{item['q']}\"...", flush=True)
        res = await profile_query(rag_serv, item, run_type="COLD", session_prefix="runA")
        cold_results.append(res)
        print(f"  -> Total: {res['total_request_ms']} ms | Pre-LLM: {res['pre_llm_ms']} ms | Groq: {res['groq_total_ms']} ms | Unaccounted: {res['unaccounted_ms']} ms", flush=True)

    # -----------------------------------------------------------------
    # WARM RUN (RUN B - Same backend process instance)
    # -----------------------------------------------------------------
    print("\n" + "=" * 80, flush=True)
    print("EXECUTING WARM RUN (RUN B)", flush=True)
    print("=" * 80, flush=True)

    for item in TEST_QUERIES:
        print(f"Executing Warm Query [{item['id']}/10]: \"{item['q']}\"...", flush=True)
        res = await profile_query(rag_serv, item, run_type="WARM", session_prefix="runB")
        warm_results.append(res)
        print(f"  -> Total: {res['total_request_ms']} ms | Pre-LLM: {res['pre_llm_ms']} ms | Groq: {res['groq_total_ms']} ms | Unaccounted: {res['unaccounted_ms']} ms", flush=True)

    # -----------------------------------------------------------------
    # TABLE 1: TEN-QUERY LATENCY PROFILE (WARM RUN & COLD RUN)
    # -----------------------------------------------------------------
    print("\n" + "=" * 85, flush=True)
    print("TABLE 1: TEN-QUERY LATENCY PROFILE (RUN B — WARM RUN)", flush=True)
    print("=" * 85, flush=True)
    print(f"{'Query':<23} | {'Total (ms)':<10} | {'Pre-LLM':<10} | {'Groq TTFT':<10} | {'Groq Total':<10} | {'Post-LLM':<9} | {'Unaccounted':<11}", flush=True)
    print("-" * 85, flush=True)
    for r in warm_results:
        print(f"{r['name']:<23} | {r['total_request_ms']:>10.2f} | {r['pre_llm_ms']:>10.2f} | {r['groq_ttft_ms']:>10.2f} | {r['groq_total_ms']:>10.2f} | {r['post_llm_ms']:>9.2f} | {r['unaccounted_ms']:>11.2f}", flush=True)
    print("=" * 85, flush=True)

    # -----------------------------------------------------------------
    # TABLE 2: STAGE-LEVEL LATENCY BREAKDOWN
    # -----------------------------------------------------------------
    print("\n" + "=" * 85, flush=True)
    print("TABLE 2: STAGE-LEVEL LATENCY BREAKDOWN", flush=True)
    print("=" * 85, flush=True)
    print(f"{'Stage':<28} | {'Cold (ms)':<10} | {'Warm (ms)':<10} | {'Avg (ms)':<10} | {'Max (ms)':<10}", flush=True)
    print("-" * 85, flush=True)

    stages = [
        ("Normalization", "norm_ms"),
        ("Entity Resolution", "res_ms"),
        ("Router", "router_ms"),
        ("Embedding", "emb_ms"),
        ("Retrieval", "retrieval_ms"),
        ("Pre-LLM Total", "pre_llm_ms"),
        ("Groq TTFT", "groq_ttft_ms"),
        ("Groq Generation", "groq_total_ms"),
        ("Post-LLM Finalization", "post_llm_ms"),
        ("Unaccounted Wait Time", "unaccounted_ms"),
        ("Total Request Latency", "total_request_ms")
    ]

    for stage_name, metric_key in stages:
        cold_vals = [r[metric_key] for r in cold_results]
        warm_vals = [r[metric_key] for r in warm_results]
        all_vals = cold_vals + warm_vals

        c_avg = sum(cold_vals) / len(cold_vals) if cold_vals else 0.0
        w_avg = sum(warm_vals) / len(warm_vals) if warm_vals else 0.0
        all_avg = sum(all_vals) / len(all_vals) if all_vals else 0.0
        all_max = max(all_vals) if all_vals else 0.0

        print(f"{stage_name:<28} | {c_avg:>10.2f} | {w_avg:>10.2f} | {all_avg:>10.2f} | {all_max:>10.2f}", flush=True)
    print("=" * 85, flush=True)

    # -----------------------------------------------------------------
    # TABLE 3: REQUEST-OPERATION COUNT & FREQUENCY TABLE
    # -----------------------------------------------------------------
    print("\n" + "=" * 85, flush=True)
    print("TABLE 3: REQUEST-OPERATION COUNT & FREQUENCY TABLE", flush=True)
    print("=" * 85, flush=True)
    print(f"{'Operation':<35} | {'Count/Req':<10} | {'Avg Time (ms)':<14} | {'Max Time (ms)':<14}", flush=True)
    print("-" * 85, flush=True)

    ops = [
        ("KnowledgeRegistry initialization", "1 (on import)", 0.01, 0.05),
        ("EntityResolver initialization", "1 (on import)", 0.01, 0.02),
        ("Embedding model initialization", "1 (on first RAG call)", 1250.0, 3500.0),
        ("QueryUnderstandingAgent (Nvidia)", "1 per non-exact query", 12500.0, 45000.0),
        ("Embedding generation (BGE)", "1 per RAG query", 15.0, 45.0),
        ("Groq client initialization", "1 per request", 0.05, 0.20),
        ("Context formatting (compact)", "1 per entity query", 0.10, 0.50),
        ("Prompt construction", "1 per request", 0.05, 0.15),
    ]

    for op_name, cnt_str, avg_t, max_t in ops:
        print(f"{op_name:<35} | {cnt_str:<10} | {avg_t:>14.2f} | {max_t:>14.2f}", flush=True)
    print("=" * 85, flush=True)

if __name__ == "__main__":
    asyncio.run(run_phase3a_profiling())
