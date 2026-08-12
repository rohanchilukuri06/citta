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

from fastapi.testclient import TestClient
import server
from server import app
from llm_provider import get_llm_provider
from deterministic_engine import get_deterministic_engine
from knowledge_registry import get_registry

TEST_QUESTIONS = [
    {"id": 1, "q": "Do you have Pharma OS?", "check": lambda res: "pharma" in res.lower()},
    {"id": 2, "q": "What does Pharma OS do?", "check": lambda res: len(res) > 20 and ("quality" in res.lower() or "compliance" in res.lower() or "batch" in res.lower() or "release" in res.lower())},
    {"id": 3, "q": "Do you have Education OS?", "check": lambda res: "education" in res.lower()},
    {"id": 4, "q": "What does Education OS provide for colleges?", "check": lambda res: len(res) > 20 and ("college" in res.lower() or "learning" in res.lower() or "assessment" in res.lower() or "student" in res.lower())},
    {"id": 5, "q": "What can MarTech 360 help a business with?", "check": lambda res: len(res) > 20 and ("marketing" in res.lower() or "brand" in res.lower() or "strategy" in res.lower())},
    {"id": 6, "q": "How is MarTech 360 different from traditional branding?", "check": lambda res: len(res) > 20 and ("traditional" in res.lower() or "data" in res.lower() or "opinion" in res.lower() or "evidence" in res.lower() or "living" in res.lower())},
    {"id": 7, "q": "How long does the MarTech 360 strategy process take?", "check": lambda res: "2" in res or "3" in res or "week" in res.lower()},
    {"id": 8, "q": "What is the annual subscription price of MarTech 360?", "check": lambda res: not any(c in res for c in ["$", "₹", "USD", "INR", "/month", "/year"]) and any(t in res.lower() for t in ["not available", "not mentioned", "not specified", "does not provide", "contact", "don't have"])},
    {"id": 9, "q": "Who is the CEO of MarTech 360?", "check": lambda res: any(t in res.lower() for t in ["not available", "not mentioned", "does not specify", "don't have", "kiran", "cittaai"])},
    {"id": 10, "q": "What services does CittaAI provide?", "check": lambda res: len(res) > 20 and ("service" in res.lower() or "marketing" in res.lower() or "data" in res.lower() or "consulting" in res.lower() or "ai" in res.lower())}
]

def run_phase3_production_tests():
    print("=" * 75)
    print("PHASE 3 — PRODUCTION /api/chat ENDPOINT VERIFICATION REPORT")
    print("=" * 75)

    client = TestClient(app)

    # -----------------------------------------------------------------
    # Step A: Regression Verification
    # -----------------------------------------------------------------
    print("\n--- REGRESSION CHECKS ---")
    nv_prov = get_llm_provider("nvidia", {})
    gem_prov = get_llm_provider("gemini", {})
    groq_prov = get_llm_provider("groq", {})
    det_eng = get_deterministic_engine()
    reg = get_registry()

    print(f"[OK] NvidiaProvider:      {nv_prov.__class__.__name__}")
    print(f"[OK] GeminiProvider:      {gem_prov.__class__.__name__}")
    print(f"[OK] GroqProvider:        {groq_prov.__class__.__name__}")
    print(f"[OK] DeterministicEngine: {det_eng.__class__.__name__}")
    print(f"[OK] KnowledgeRegistry:   Loaded ({len(reg.entities)} entities)")

    # -----------------------------------------------------------------
    # Step B: 10 Production /api/chat Endpoint Tests
    # -----------------------------------------------------------------
    print("\n--- 10 PRODUCTION /api/chat TESTS ---")
    results = []

    for item in TEST_QUESTIONS:
        q_id = item["id"]
        q_text = item["q"]
        validator = item["check"]

        payload = {
            "session_id": f"test_session_phase3_{q_id}",
            "message": q_text
        }

        t0 = time.perf_counter()
        response = client.post("/api/chat", json=payload)
        total_lat_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        if response.status_code != 200:
            print(f"❌ Test {q_id} HTTP Error: {response.status_code}")
            results.append({
                "id": q_id,
                "question": q_text,
                "ttft_ms": 0,
                "total_ms": total_lat_ms,
                "status": "FAIL (HTTP Error)",
                "source": "None",
                "text_preview": response.text[:100]
            })
            continue

        # Parse SSE lines
        raw_sse = response.text
        sse_lines = raw_sse.strip().split("\n\n")

        accumulated_text = ""
        done_metadata = {}
        ttft_ms = 0.0

        for line in sse_lines:
            line_str = line.strip()
            if line_str.startswith("data:"):
                json_str = line_str[5:].strip()
                try:
                    data_obj = json.loads(json_str)
                    if not data_obj.get("done"):
                        if not accumulated_text and "text" in data_obj:
                            ttft_ms = total_lat_ms  # Approximation for sync test client
                        accumulated_text += data_obj.get("text", "")
                    else:
                        done_metadata = data_obj
                except Exception:
                    pass

        metrics = done_metadata.get("metrics", {})
        if metrics.get("time_to_first_token_ms"):
            ttft_ms = metrics.get("time_to_first_token_ms")

        source = done_metadata.get("source", "Unknown")
        is_pass = validator(accumulated_text)

        status_str = "PASS" if is_pass else "FAIL"

        print(f"\n[TEST {q_id}] Query: \"{q_text}\"", flush=True)
        print(f"  Status:       {status_str}", flush=True)
        print(f"  Source:       {source}", flush=True)
        print(f"  TTFT:         {ttft_ms} ms", flush=True)
        print(f"  Total Lat:    {total_lat_ms} ms", flush=True)
        print(f"  LLM Used:     {metrics.get('llm_used', metrics.get('provider', 'N/A'))}", flush=True)
        print(f"  Response Preview:\n  {accumulated_text[:180]}...", flush=True)

        results.append({
            "id": q_id,
            "question": q_text,
            "ttft_ms": ttft_ms,
            "total_ms": total_lat_ms,
            "status": status_str,
            "source": source,
            "text_preview": accumulated_text[:120]
        })

    # -----------------------------------------------------------------
    # Summary Report
    # -----------------------------------------------------------------
    print("\n" + "=" * 75)
    print("PHASE 3 — PRODUCTION /api/chat TEST SUMMARY")
    print("=" * 75)
    print(f"{'#':<3} | {'Question':<45} | {'TTFT':<9} | {'Total Lat':<10} | {'Status':<8}")
    print("-" * 75)
    for r in results:
        q_short = (r['question'][:42] + "...") if len(r['question']) > 45 else r['question']
        print(f"{r['id']:<3} | {q_short:<45} | {r['ttft_ms']:>6} ms | {r['total_ms']:>7} ms | {r['status']:<8}")
    print("=" * 75)

if __name__ == "__main__":
    run_phase3_production_tests()
