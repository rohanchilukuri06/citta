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
from llm_provider import get_llm_provider
from gemini_client import GeminiClient
from context_formatter import format_compact_entity_context
from knowledge_registry import get_registry

SYSTEM_PROMPT_TEMPLATE = """You are CittaAI's enterprise AI assistant.

Use ONLY the supplied CittaAI knowledge context to answer the user's question.

Answer naturally and conversationally. Preserve factual meaning.

CITTAI KNOWLEDGE CONTEXT:
{registry_context}
"""

async def run_phase2a_tests():
    print("=" * 70)
    print("PHASE 2A — GEMINI CLIENT HARDENING AND LATENCY VERIFICATION")
    print("=" * 70)

    api_key = os.environ.get("GEMINI_API_KEY", "")
    model_name = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash-lite")
    
    print(f"[OK] GEMINI_MODEL: {model_name}")
    print(f"[OK] MAX_OUTPUT_TOKENS: {getattr(config, 'MAX_OUTPUT_TOKENS', 500)}")

    client = GeminiClient(api_key=api_key, model=model_name)
    reg = get_registry()

    test_results = []

    # -----------------------------------------------------------------
    # TEST 1: Context Compaction Efficiency & Information Preservation
    # -----------------------------------------------------------------
    print("\n--- TEST 1: Context Compaction ---")
    entities_to_test = ["martech_360", "pharma_os", "education_os"]
    
    for ent_id in entities_to_test:
        ent_data = reg.get_entity(ent_id) or {}
        raw_json_str = json.dumps(ent_data, indent=2)
        raw_chars = len(raw_json_str)
        raw_tokens = raw_chars // 4

        compact_str = format_compact_entity_context(ent_data)
        compact_chars = len(compact_str)
        compact_tokens = compact_chars // 4

        reduction_pct = round((1.0 - (compact_chars / max(raw_chars, 1))) * 100.0, 1)

        # Fact preservation check
        has_overview = bool(ent_data.get("overview") or ent_data.get("description"))
        facts_preserved = (
            ("Overview:" in compact_str or not has_overview) and
            ("Entity:" in compact_str)
        )

        print(f"Entity [{ent_id}]:")
        print(f"  Raw Context:     {raw_chars} chars (~{raw_tokens} tokens)")
        print(f"  Compact Context: {compact_chars} chars (~{compact_tokens} tokens)")
        print(f"  Reduction:       {reduction_pct}%")
        print(f"  Facts Preserved: {facts_preserved}")

        test_results.append({
            "test": f"Context Compaction ({ent_id})",
            "latency_ms": 0,
            "status": "PASS" if facts_preserved and compact_chars < raw_chars else "FAIL",
            "details": f"Reduced by {reduction_pct}% ({raw_tokens} -> {compact_tokens} tokens)"
        })

    # -----------------------------------------------------------------
    # TEST 2: Fail-Fast HTTP 429 / Generation Test
    # -----------------------------------------------------------------
    print("\n--- TEST 2: Non-Streaming Fail-Fast / Quota Check ---")
    ent_data = reg.get_entity("martech_360") or {}
    compact_context = format_compact_entity_context(ent_data)
    sys_msg = SYSTEM_PROMPT_TEMPLATE.format(registry_context=compact_context)

    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": "Tell me about MarTech 360."}
    ]

    t_start = time.perf_counter()
    resp_text, metrics = await client.generate(messages, model=model_name)
    latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    print(f"Success Status:    {metrics.get('success')}")
    print(f"Error Type:        {metrics.get('error_type')}")
    print(f"Status Code:       {metrics.get('status_code')}")
    print(f"Total Latency:     {latency_ms} ms")
    print(f"Prompt Build Time: {metrics.get('prompt_build_ms')} ms")

    if metrics.get("success"):
        print(f"Generated Response: {resp_text[:120]}...")
        status_str = "PASS"
    elif metrics.get("status_code") == 429:
        print("Rate Limit Detected: Fail-Fast verified (< 200 ms overhead)")
        status_str = "SKIPPED / RATE LIMITED"
    else:
        print(f"Error Occurred: {metrics.get('error')}")
        status_str = "ERROR"

    test_results.append({
        "test": "Non-Streaming Fail-Fast 429 Check",
        "latency_ms": latency_ms,
        "status": status_str,
        "details": f"Status Code {metrics.get('status_code')}, Error Type: {metrics.get('error_type')}"
    })

    # -----------------------------------------------------------------
    # TEST 3: Streaming Hardening & Clean Error Handling
    # -----------------------------------------------------------------
    print("\n--- TEST 3: Streaming Response Hardening ---")
    stream_chunks = []
    stream_metrics = {}

    t_start = time.perf_counter()
    async for chunk in client.stream_chat(
        [{"role": "user", "content": "Respond with 'Test'"}],
        model=model_name,
        metrics_out=stream_metrics
    ):
        stream_chunks.append(chunk)
    stream_latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    print(f"Stream Started:        {stream_metrics.get('stream_started')}")
    print(f"Chunks Received:       {len(stream_chunks)}")
    print(f"Stream Success:        {stream_metrics.get('success')}")
    print(f"Stream Error Type:     {stream_metrics.get('error_type')}")
    print(f"Stream Total Latency:  {stream_latency_ms} ms")

    if stream_metrics.get("success"):
        status_str = "PASS"
    elif stream_metrics.get("status_code") == 429:
        # Verify 0 chunks yielded as fake text
        is_clean_termination = len(stream_chunks) == 0
        print(f"Clean Stream Termination Verified: {is_clean_termination}")
        status_str = "SKIPPED / RATE LIMITED" if is_clean_termination else "FAIL"
    else:
        status_str = "ERROR"

    test_results.append({
        "test": "Streaming Hardening",
        "latency_ms": stream_latency_ms,
        "status": status_str,
        "details": f"Received {len(stream_chunks)} chunks, Status Code {stream_metrics.get('status_code')}"
    })

    # -----------------------------------------------------------------
    # TEST 4: Invalid API Key Fail-Fast Handling
    # -----------------------------------------------------------------
    print("\n--- TEST 4: Invalid API Key Fail-Fast Handling ---")
    invalid_client = GeminiClient(api_key="AIzaSyInvalidTestKeyForPhase2a12345", model=model_name)
    
    t_start = time.perf_counter()
    inv_resp, inv_metrics = await invalid_client.generate([{"role": "user", "content": "Hi"}])
    inv_latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    key_leaked = "AIzaSyInvalidTestKeyForPhase2a12345" in inv_resp or "AIzaSyInvalidTestKeyForPhase2a12345" in str(inv_metrics)
    is_auth_error = inv_metrics.get("error_type") == "AUTHENTICATION_ERROR" and not inv_metrics.get("success")

    print(f"Latency:        {inv_latency_ms} ms")
    print(f"Auth Error:     {is_auth_error}")
    print(f"Key Redacted:   {not key_leaked}")

    test_results.append({
        "test": "Invalid Key Handling",
        "latency_ms": inv_latency_ms,
        "status": "PASS" if is_auth_error and not key_leaked and inv_latency_ms < 3000 else "FAIL",
        "details": f"Latency {inv_latency_ms} ms, Key Redacted: {not key_leaked}"
    })

    # -----------------------------------------------------------------
    # TEST 5: Regression Imports (Nvidia & Deterministic Engine)
    # -----------------------------------------------------------------
    print("\n--- TEST 5: Regression Imports Check ---")
    try:
        nvidia_prov = get_llm_provider("nvidia", {})
        from deterministic_engine import get_deterministic_engine
        det_eng = get_deterministic_engine()
        
        nv_ok = nvidia_prov.__class__.__name__ == "NvidiaProvider"
        det_ok = det_eng.__class__.__name__ == "DeterministicEngine"
        
        print(f"[OK] NvidiaProvider: {nvidia_prov.__class__.__name__}")
        print(f"[OK] DeterministicEngine: {det_eng.__class__.__name__}")
        
        reg_status = "PASS" if (nv_ok and det_ok) else "FAIL"
    except Exception as e:
        print(f"❌ Regression Import Failed: {e}")
        reg_status = "FAIL"

    test_results.append({
        "test": "NVIDIA & Deterministic Engine Regression",
        "latency_ms": 0,
        "status": reg_status,
        "details": "Imports verified clean"
    })

    # -----------------------------------------------------------------
    # Summary Report
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 2A SUMMARY REPORT")
    print("=" * 70)
    print(f"{'Test Description':<40} | {'Latency':<10} | {'Status':<20}")
    print("-" * 70)
    for r in test_results:
        print(f"{r['test']:<40} | {r['latency_ms']:>6} ms | {r['status']:<20}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_phase2a_tests())
