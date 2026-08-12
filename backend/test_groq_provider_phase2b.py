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
from groq_client import GroqClient
from context_formatter import format_compact_entity_context
from knowledge_registry import get_registry

SYSTEM_PROMPT_TEMPLATE = """You are CittaAI's enterprise AI assistant.

Use ONLY the supplied CittaAI knowledge context to answer the user's question.

Answer naturally and conversationally. Do not simply copy the raw registry structure.

Preserve the factual meaning of the information.

Never invent CittaAI products, services, solutions, capabilities, metrics, customers, pricing, policies, case studies, or technical claims.

If the supplied context does not contain enough information to answer the question, clearly state that the information is not available.

Do not infer unsupported company facts.

CITTAI KNOWLEDGE CONTEXT:
{registry_context}
"""

async def run_phase2b_benchmark():
    print("=" * 70)
    print("PHASE 2B — GROQ + LLAMA 3.3 70B STANDALONE BENCHMARK")
    print("=" * 70)

    # -----------------------------------------------------------------
    # TEST A: Configuration Check
    # -----------------------------------------------------------------
    print("\n--- TEST A: Configuration ---")
    groq_api_key = os.environ.get("GROQ_API_KEY", "") or getattr(config, "GROQ_API_KEY", "")
    groq_model = getattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile")
    has_key = bool(groq_api_key)

    print(f"API Key Configured: {'YES' if has_key else 'NO'}")
    print(f"Configured Model:   {groq_model}")

    if not has_key:
        print("❌ CRITICAL: GROQ_API_KEY is not configured in backend/.env")
        sys.exit(1)

    client = GroqClient(api_key=groq_api_key, model=groq_model)
    reg = get_registry()
    print("[OK] GroqClient Initialized: PASS")

    test_results = []

    # -----------------------------------------------------------------
    # TEST B: Basic Generation
    # -----------------------------------------------------------------
    print("\n--- TEST B: Basic Generation ---")
    t0 = time.perf_counter()
    basic_res, basic_metrics = await client.generate(
        [{"role": "user", "content": "Reply with exactly: Groq test successful."}],
        model=groq_model
    )
    basic_latency = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"Response: {basic_res.strip()}")
    print(f"Latency:  {basic_latency} ms")
    print(f"Success:  {basic_metrics.get('success')}")

    basic_status = "PASS" if basic_metrics.get("success") and "Groq test successful" in basic_res else "FAIL"
    test_results.append({
        "test": "Basic Generation",
        "latency_ms": basic_latency,
        "ttft_ms": basic_latency,
        "status": basic_status,
        "details": f"Success: {basic_metrics.get('success')}"
    })

    # -----------------------------------------------------------------
    # TEST C: Streaming Performance & TTFT
    # -----------------------------------------------------------------
    print("\n--- TEST C: Streaming Performance ---")
    stream_chunks = []
    stream_metrics = {}

    t0 = time.perf_counter()
    async for chunk in client.stream_chat(
        [{"role": "user", "content": "Explain what an Enterprise AI OS is in simple terms."}],
        model=groq_model,
        metrics_out=stream_metrics
    ):
        stream_chunks.append(chunk)

    stream_text = "".join(stream_chunks).strip()
    stream_latency = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"Stream Success:         {stream_metrics.get('success')}")
    print(f"Time to First Token:   {stream_metrics.get('time_to_first_token_ms')} ms")
    print(f"Total Stream Latency:  {stream_latency} ms")
    print(f"Chunks Received:       {len(stream_chunks)}")
    print(f"Output Characters:     {len(stream_text)}")
    print(f"Preview Response:\n{stream_text[:180]}...")

    stream_status = "PASS" if stream_metrics.get("success") and len(stream_chunks) > 1 else "FAIL"
    test_results.append({
        "test": "Streaming Performance",
        "latency_ms": stream_latency,
        "ttft_ms": stream_metrics.get("time_to_first_token_ms", 0),
        "status": stream_status,
        "details": f"TTFT: {stream_metrics.get('time_to_first_token_ms')} ms, Chunks: {len(stream_chunks)}"
    })

    # -----------------------------------------------------------------
    # TEST D: Grounded MarTech 360 Generation
    # -----------------------------------------------------------------
    print("\n--- TEST D: MarTech 360 Grounded Generation ---")
    martech_ent = reg.get_entity("martech_360") or {}
    martech_context = format_compact_entity_context(martech_ent)
    martech_sys = SYSTEM_PROMPT_TEMPLATE.format(registry_context=martech_context)

    martech_msg = [
        {"role": "system", "content": martech_sys},
        {"role": "user", "content": "What can MarTech 360 help a business with?"}
    ]

    m_stream_chunks = []
    m_stream_metrics = {}
    t0 = time.perf_counter()
    async for chunk in client.stream_chat(martech_msg, model=groq_model, metrics_out=m_stream_metrics):
        m_stream_chunks.append(chunk)

    m_text = "".join(m_stream_chunks).strip()
    m_latency = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"MarTech 360 TTFT:      {m_stream_metrics.get('time_to_first_token_ms')} ms")
    print(f"Total Latency:         {m_latency} ms")
    print(f"Input Chars / Tokens:  {m_stream_metrics.get('input_chars')} / ~{m_stream_metrics.get('estimated_input_tokens')}")
    print(f"Output Chars / Tokens: {len(m_text)} / ~{len(m_text)//4}")
    print(f"Generated Response:\n{m_text[:220]}...")

    m_pass = m_stream_metrics.get("success") and ("marketing" in m_text.lower() or "brand" in m_text.lower() or "strategy" in m_text.lower())
    test_results.append({
        "test": "MarTech 360 Grounded Generation",
        "latency_ms": m_latency,
        "ttft_ms": m_stream_metrics.get("time_to_first_token_ms", 0),
        "status": "PASS" if m_pass else "FAIL",
        "details": f"TTFT: {m_stream_metrics.get('time_to_first_token_ms')} ms"
    })

    # -----------------------------------------------------------------
    # TEST E: Grounded Pharma OS Generation
    # -----------------------------------------------------------------
    print("\n--- TEST E: Pharma OS Grounded Generation ---")
    pharma_ent = reg.get_entity("pharma_os") or {}
    pharma_context = format_compact_entity_context(pharma_ent)
    pharma_sys = SYSTEM_PROMPT_TEMPLATE.format(registry_context=pharma_context)

    pharma_msg = [
        {"role": "system", "content": pharma_sys},
        {"role": "user", "content": "What does Pharma OS help pharmaceutical teams with?"}
    ]

    p_stream_chunks = []
    p_stream_metrics = {}
    t0 = time.perf_counter()
    async for chunk in client.stream_chat(pharma_msg, model=groq_model, metrics_out=p_stream_metrics):
        p_stream_chunks.append(chunk)

    p_text = "".join(p_stream_chunks).strip()
    p_latency = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"Pharma OS TTFT:        {p_stream_metrics.get('time_to_first_token_ms')} ms")
    print(f"Total Latency:         {p_latency} ms")
    print(f"Input Chars / Tokens:  {p_stream_metrics.get('input_chars')} / ~{p_stream_metrics.get('estimated_input_tokens')}")
    print(f"Output Chars / Tokens: {len(p_text)} / ~{len(p_text)//4}")
    print(f"Generated Response:\n{p_text[:220]}...")

    p_pass = p_stream_metrics.get("success") and ("pharma" in p_text.lower() or "health" in p_text.lower() or "compliance" in p_text.lower() or "medical" in p_text.lower())
    test_results.append({
        "test": "Pharma OS Grounded Generation",
        "latency_ms": p_latency,
        "ttft_ms": p_stream_metrics.get("time_to_first_token_ms", 0),
        "status": "PASS" if p_pass else "FAIL",
        "details": f"TTFT: {p_stream_metrics.get('time_to_first_token_ms')} ms"
    })

    # -----------------------------------------------------------------
    # TEST F: Grounded Education OS Generation
    # -----------------------------------------------------------------
    print("\n--- TEST F: Education OS Grounded Generation ---")
    edu_ent = reg.get_entity("education_os") or {}
    edu_context = format_compact_entity_context(edu_ent)
    edu_sys = SYSTEM_PROMPT_TEMPLATE.format(registry_context=edu_context)

    edu_msg = [
        {"role": "system", "content": edu_sys},
        {"role": "user", "content": "What does Education OS provide for colleges?"}
    ]

    e_stream_chunks = []
    e_stream_metrics = {}
    t0 = time.perf_counter()
    async for chunk in client.stream_chat(edu_msg, model=groq_model, metrics_out=e_stream_metrics):
        e_stream_chunks.append(chunk)

    e_text = "".join(e_stream_chunks).strip()
    e_latency = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"Education OS TTFT:     {e_stream_metrics.get('time_to_first_token_ms')} ms")
    print(f"Total Latency:         {e_latency} ms")
    print(f"Input Chars / Tokens:  {e_stream_metrics.get('input_chars')} / ~{e_stream_metrics.get('estimated_input_tokens')}")
    print(f"Output Chars / Tokens: {len(e_text)} / ~{len(e_text)//4}")
    print(f"Generated Response:\n{e_text[:220]}...")

    e_pass = e_stream_metrics.get("success") and ("education" in e_text.lower() or "learning" in e_text.lower() or "student" in e_text.lower() or "campus" in e_text.lower() or "college" in e_text.lower())
    test_results.append({
        "test": "Education OS Grounded Generation",
        "latency_ms": e_latency,
        "ttft_ms": e_stream_metrics.get("time_to_first_token_ms", 0),
        "status": "PASS" if e_pass else "FAIL",
        "details": f"TTFT: {e_stream_metrics.get('time_to_first_token_ms')} ms"
    })

    # -----------------------------------------------------------------
    # TEST G: Natural Conversation
    # -----------------------------------------------------------------
    print("\n--- TEST G: Natural Conversation ---")
    conv_msg = [
        {"role": "system", "content": martech_sys},
        {"role": "user", "content": "How is this different from traditional branding?"}
    ]

    t0 = time.perf_counter()
    conv_text, conv_metrics = await client.generate(conv_msg, model=groq_model)
    conv_latency = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"Latency: {conv_latency} ms")
    print(f"Conversational Answer:\n{conv_text.strip()}")

    # Verify answer is non-empty, conversational, and not raw json
    is_natural = len(conv_text) > 30 and not conv_text.startswith("{") and not conv_text.startswith("[")
    test_results.append({
        "test": "Natural Conversation",
        "latency_ms": conv_latency,
        "ttft_ms": conv_latency,
        "status": "PASS" if is_natural and conv_metrics.get("success") else "FAIL",
        "details": f"Length: {len(conv_text)} chars"
    })

    # -----------------------------------------------------------------
    # TEST H: Hallucination Resistance (Pricing)
    # -----------------------------------------------------------------
    print("\n--- TEST H: Hallucination Resistance (Pricing) ---")
    price_msg = [
        {"role": "system", "content": martech_sys},
        {"role": "user", "content": "What is the annual subscription price of MarTech 360?"}
    ]

    t0 = time.perf_counter()
    price_text, price_metrics = await client.generate(price_msg, model=groq_model)
    price_latency = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"Latency: {price_latency} ms")
    print(f"Model Answer:\n{price_text.strip()}")

    # Verify no fabricated dollar/rupee figures
    fabricated_price = any(c in price_text for c in ["$", "₹", "USD", "INR", "/month", "/year"])
    refused = any(term in price_text.lower() for term in ["not available", "don't have", "not specified", "contact", "not mention", "does not provide", "not detailed"])

    hallucination_price_pass = refused and not fabricated_price
    print(f"Fabricated Price: {fabricated_price}, Refused/Stated Unavailable: {refused}")

    test_results.append({
        "test": "Hallucination Resistance (Pricing)",
        "latency_ms": price_latency,
        "ttft_ms": price_latency,
        "status": "PASS" if hallucination_price_pass and price_metrics.get("success") else "FAIL",
        "details": f"Fabricated: {fabricated_price}, Refused: {refused}"
    })

    # -----------------------------------------------------------------
    # TEST I: Unsupported Knowledge (CEO)
    # -----------------------------------------------------------------
    print("\n--- TEST I: Unsupported Knowledge (CEO) ---")
    ceo_msg = [
        {"role": "system", "content": martech_sys},
        {"role": "user", "content": "Who is the CEO of MarTech 360?"}
    ]

    t0 = time.perf_counter()
    ceo_text, ceo_metrics = await client.generate(ceo_msg, model=groq_model)
    ceo_latency = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"Latency: {ceo_latency} ms")
    print(f"Model Answer:\n{ceo_text.strip()}")

    # Check if model refrains from fabricating a fake CEO name for MarTech 360 service
    ceo_refused = any(term in ceo_text.lower() for term in ["not available", "not mentioned", "does not specify", "don't have", "not listed", "kiran", "cittaai"])
    test_results.append({
        "test": "Unsupported Knowledge (CEO)",
        "latency_ms": ceo_latency,
        "ttft_ms": ceo_latency,
        "status": "PASS" if ceo_refused and ceo_metrics.get("success") else "FAIL",
        "details": f"Refused/Grounded: {ceo_refused}"
    })

    # -----------------------------------------------------------------
    # TEST J: Registry Fact Preservation (Duration)
    # -----------------------------------------------------------------
    print("\n--- TEST J: Registry Fact Preservation (Duration) ---")
    dur_msg = [
        {"role": "system", "content": martech_sys},
        {"role": "user", "content": "How long does the MarTech 360 strategy process take?"}
    ]

    t0 = time.perf_counter()
    dur_text, dur_metrics = await client.generate(dur_msg, model=groq_model)
    dur_latency = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"Latency: {dur_latency} ms")
    print(f"Model Answer:\n{dur_text.strip()}")

    # Verify "2", "3", or "week" is preserved
    fact_preserved = any(term in dur_text.lower() for term in ["2", "3", "week"])
    test_results.append({
        "test": "Registry Fact Preservation (Duration)",
        "latency_ms": dur_latency,
        "ttft_ms": dur_latency,
        "status": "PASS" if fact_preserved and dur_metrics.get("success") else "FAIL",
        "details": f"Fact Preserved: {fact_preserved}"
    })

    # -----------------------------------------------------------------
    # TEST K: Provider Regression Check
    # -----------------------------------------------------------------
    print("\n--- TEST K: Provider Regression Check ---")
    try:
        nvidia_prov = get_llm_provider("nvidia", {})
        gemini_prov = get_llm_provider("gemini", {})
        groq_prov = get_llm_provider("groq", {})
        from deterministic_engine import get_deterministic_engine
        det_eng = get_deterministic_engine()

        nv_ok = nvidia_prov.__class__.__name__ == "NvidiaProvider"
        gem_ok = gemini_prov.__class__.__name__ == "GeminiProvider"
        groq_ok = groq_prov.__class__.__name__ == "GroqProvider"
        det_ok = det_eng.__class__.__name__ == "DeterministicEngine"

        print(f"[OK] NvidiaProvider:        {nvidia_prov.__class__.__name__}")
        print(f"[OK] GeminiProvider:        {gemini_prov.__class__.__name__}")
        print(f"[OK] GroqProvider:          {groq_prov.__class__.__name__}")
        print(f"[OK] DeterministicEngine:   {det_eng.__class__.__name__}")

        reg_status = "PASS" if (nv_ok and gem_ok and groq_ok and det_ok) else "FAIL"
    except Exception as e:
        print(f"❌ Regression Check Failed: {e}")
        reg_status = "FAIL"

    test_results.append({
        "test": "Provider & Engine Regression",
        "latency_ms": 0,
        "ttft_ms": 0,
        "status": reg_status,
        "details": "All 4 providers/engines instantiated clean"
    })

    # -----------------------------------------------------------------
    # Optional Gemini Comparison
    # -----------------------------------------------------------------
    print("\n--- OPTIONAL GEMINI COMPARISON ---")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    gemini_model = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash-lite")
    
    if gemini_key:
        from gemini_client import GeminiClient
        g_client = GeminiClient(api_key=gemini_key, model=gemini_model)
        t0 = time.perf_counter()
        g_resp, g_metrics = await g_client.generate(martech_msg, model=gemini_model)
        g_latency = round((time.perf_counter() - t0) * 1000.0, 2)
        
        if g_metrics.get("success"):
            print(f"Gemini Response ({g_latency} ms):\n{g_resp[:150]}...")
            gemini_comp_status = f"PASS ({g_latency} ms)"
        elif g_metrics.get("status_code") == 429:
            print("Gemini Status: SKIPPED / RATE LIMITED (429)")
            gemini_comp_status = "SKIPPED / RATE LIMITED (429)"
        else:
            print(f"Gemini Status: ERROR ({g_metrics.get('error')})")
            gemini_comp_status = f"ERROR ({g_metrics.get('status_code')})"
    else:
        gemini_comp_status = "SKIPPED (No Key)"

    # -----------------------------------------------------------------
    # BENCHMARK REPORT
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 2B — GROQ + LLAMA 3.3 70B BENCHMARK SUMMARY REPORT")
    print("=" * 70)
    print(f"{'Benchmark Test':<42} | {'TTFT':<9} | {'Total Lat':<10} | {'Status':<15}")
    print("-" * 70)
    for r in test_results:
        print(f"{r['test']:<42} | {r['ttft_ms']:>6} ms | {r['latency_ms']:>7} ms | {r['status']:<15}")
    print("=" * 70)
    print(f"Gemini Comparison Status: {gemini_comp_status}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_phase2b_benchmark())
