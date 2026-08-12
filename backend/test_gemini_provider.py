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

# Load environment variables from backend/.env
load_dotenv(Path(BACKEND_DIR) / '.env')

import config
from llm_provider import get_llm_provider, LLMProvider
from gemini_client import GeminiClient
from knowledge_registry import get_registry

SYSTEM_PROMPT_TEMPLATE = """You are CittaAI's enterprise AI assistant.

Use ONLY the supplied CittaAI knowledge context to answer the user's question.

The supplied context is the authoritative source of truth.

Answer naturally and conversationally.

Do not simply copy the wording of the supplied context.

Preserve the factual meaning of the information.

Never invent CittaAI products, services, solutions, capabilities, metrics, customers, pricing, policies, case studies, or technical claims.

If the supplied context does not contain enough information to answer the question, clearly state that the information is not available.

Do not infer unsupported company facts.

Keep simple answers concise.

For explanatory questions, provide a clear and useful explanation.

CITTAI KNOWLEDGE CONTEXT:
{registry_context}
"""

async def run_test():
    print("=" * 60)
    print("PHASE 1: GEMINI PROVIDER ISOLATED TEST RUNNER")
    print("=" * 60)

    # 1. Environment & API Key Check
    api_key = os.environ.get("GEMINI_API_KEY", "")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    
    if not api_key:
        print("❌ CRITICAL: GEMINI_API_KEY is not set in backend/.env")
        sys.exit(1)
    
    print(f"[OK] GEMINI_API_KEY: Configured (Length: {len(api_key)})")
    print(f"[OK] GEMINI_MODEL: {model_name}")

    # 2. Initialize GeminiProvider through LLMProvider Factory
    config_dict = {
        "GEMINI_API_KEY": api_key,
        "GEMINI_MODEL": model_name
    }
    provider = get_llm_provider("gemini", config_dict)
    print(f"[OK] Provider Initialized: {provider.__class__.__name__}")


    test_results = []

    # -------------------------------------------------------------
    # Basic Connectivity Test
    # -------------------------------------------------------------
    print("\n--- TEST 0: Basic Connectivity ---")
    start_time = time.time()
    basic_messages = [{"role": "user", "content": "Respond with 'Gemini Provider Online' in under 5 words."}]
    res = await provider.generate(basic_messages, model=model_name)
    latency_ms = int((time.time() - start_time) * 1000)
    
    print(f"Response: {res.strip()}")
    print(f"Latency: {latency_ms} ms")
    test_results.append({
        "test": "Basic Connectivity",
        "model": model_name,
        "latency_ms": latency_ms,
        "success": not res.startswith("Error")
    })

    # -------------------------------------------------------------
    # Streaming Test
    # -------------------------------------------------------------
    print("\n--- TEST 0.5: Streaming Response ---")
    start_time = time.time()
    stream_chunks = []
    async for chunk in provider.generate_stream(
        [{"role": "user", "content": "Count from 1 to 5."}],
        model=model_name
    ):
        stream_chunks.append(chunk)
    stream_latency_ms = int((time.time() - start_time) * 1000)
    full_stream_text = "".join(stream_chunks).strip()
    print(f"Streamed Chunks: {len(stream_chunks)}")
    print(f"Streamed Text: {full_stream_text}")
    print(f"Streaming Latency: {stream_latency_ms} ms")
    test_results.append({
        "test": "Streaming Response",
        "model": model_name,
        "latency_ms": stream_latency_ms,
        "success": len(stream_chunks) > 0 and not full_stream_text.startswith("Error")
    })

    # -------------------------------------------------------------
    # Grounded CittaAI Registry Tests
    # -------------------------------------------------------------
    reg = get_registry()

    grounded_tests = [
        {
            "id": "TEST 1 (Pharma OS)",
            "entity_id": "solution_pharma_os",
            "query": "Do they have Pharma OS?",
            "expected_check": lambda text: "pharma" in text.lower() or "yes" in text.lower()
        },
        {
            "id": "TEST 2 (Education OS)",
            "entity_id": "solution_education_os",
            "query": "How does Education OS work?",
            "expected_check": lambda text: len(text) > 30 and ("education" in text.lower() or "lms" in text.lower() or "learning" in text.lower())
        },
        {
            "id": "TEST 3 (MarTech 360 Overview)",
            "entity_id": "service_martech_360",
            "query": "Tell me about MarTech 360.",
            "expected_check": lambda text: "martech" in text.lower() or "marketing" in text.lower()
        },
        {
            "id": "TEST 4 (MarTech 360 vs Traditional Branding)",
            "entity_id": "service_martech_360",
            "query": "How is this different from traditional branding?",
            "expected_check": lambda text: len(text) > 30
        },
        {
            "id": "TEST 5 (MarTech 360 Strategy Duration)",
            "entity_id": "service_martech_360",
            "query": "How long does the strategy process take?",
            "expected_check": lambda text: "2" in text or "3" in text or "week" in text.lower()
        }
    ]

    for gt in grounded_tests:
        await asyncio.sleep(2.5)
        print(f"\n--- {gt['id']} ---")
        ent_data = reg.get_entity(gt["entity_id"]) or {}

        context_str = json.dumps(ent_data, indent=2)
        sys_msg = SYSTEM_PROMPT_TEMPLATE.format(registry_context=context_str)

        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": gt["query"]}
        ]

        t_start = time.time()
        resp = await provider.generate(messages, model=model_name)
        t_latency = int((time.time() - t_start) * 1000)

        print(f"User Query: '{gt['query']}'")
        print(f"Gemini Answer:\n{resp.strip()}")
        print(f"Latency: {t_latency} ms")

        is_passed = gt["expected_check"](resp)
        test_results.append({
            "test": gt["id"],
            "model": model_name,
            "latency_ms": t_latency,
            "success": is_passed
        })

    # -------------------------------------------------------------
    # Hallucination Test (MarTech 360 Pricing)
    # -------------------------------------------------------------
    print("\n--- TEST 10: Hallucination Test (MarTech 360 Pricing) ---")
    martech_data = reg.get_entity("service_martech_360") or {}
    sys_msg = SYSTEM_PROMPT_TEMPLATE.format(registry_context=json.dumps(martech_data, indent=2))
    price_query = "What is the price of MarTech 360?"

    t_start = time.time()
    price_resp = await provider.generate([
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": price_query}
    ], model=model_name)
    price_latency = int((time.time() - t_start) * 1000)

    print(f"User Query: '{price_query}'")
    print(f"Gemini Answer:\n{price_resp.strip()}")
    print(f"Latency: {price_latency} ms")

    # Verify Gemini refused to fabricate a dollar/rupee amount
    fabricated = any(char in price_resp for char in ["$", "₹", "dollar", "rupee", "USD", "INR", "/month", "/year"])
    refused = "not available" in price_resp.lower() or "don't have" in price_resp.lower() or "not contain" in price_resp.lower() or "contact" in price_resp.lower()
    hallucination_pass = refused and not fabricated

    print(f"Hallucination Test Passed: {hallucination_pass} (Fabricated: {fabricated}, Refused: {refused})")
    test_results.append({
        "test": "Hallucination Test (Pricing)",
        "model": model_name,
        "latency_ms": price_latency,
        "success": hallucination_pass
    })

    # -------------------------------------------------------------
    # Failure & Error Handling Tests
    # -------------------------------------------------------------
    print("\n--- TEST 11A: Missing API Key Handling ---")
    missing_client = GeminiClient(api_key="", model=model_name)
    missing_resp, missing_metrics = await missing_client.generate([{"role": "user", "content": "Hi"}])
    print(f"Missing Key Result: {missing_resp}")
    print(f"Missing Key Metrics Success: {missing_metrics.get('success')}")

    print("\n--- TEST 11B: Invalid API Key Handling ---")
    invalid_client = GeminiClient(api_key="AIzaSyInvalidTestKeyForFailureTesting12345", model=model_name)
    invalid_resp, invalid_metrics = await invalid_client.generate([{"role": "user", "content": "Hi"}])
    print(f"Invalid Key Result: {invalid_resp}")
    print(f"Invalid Key Metrics Success: {invalid_metrics.get('success')}")

    # Verify no keys in error strings
    key_leaked = "AIzaSyInvalidTestKeyForFailureTesting12345" in invalid_resp

    # -------------------------------------------------------------
    # Regression Check: NVIDIA Provider & Deterministic Engine Imports
    # -------------------------------------------------------------
    print("\n--- TEST 14: Regression Imports Check ---")
    nvidia_prov = get_llm_provider("nvidia", {})
    from deterministic_engine import get_deterministic_engine
    det_eng = get_deterministic_engine()
    print(f"[OK] NvidiaProvider imported cleanly: {nvidia_prov.__class__.__name__}")
    print(f"[OK] DeterministicEngine imported cleanly: {det_eng.__class__.__name__}")


    # -------------------------------------------------------------
    # Summary Report
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("PHASE 1 SUMMARY REPORT")
    print("=" * 60)
    print(f"{'Test':<35} | {'Latency':<10} | {'Status':<8}")
    print("-" * 60)
    for r in test_results:
        status_str = "PASS" if r["success"] else "FAIL"
        print(f"{r['test']:<35} | {r['latency_ms']:>6} ms | {status_str:<8}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_test())
