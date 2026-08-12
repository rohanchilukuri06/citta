import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import httpx

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(Path(BACKEND_DIR) / '.env')

from server import app

async def run_e2e_sse_verification():
    print("=" * 90)
    print("PHASE 4E — END-TO-END SSE & PRODUCTION RELIABILITY VERIFICATION")
    print("=" * 90)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Health check
        res_health = await client.get("/health")
        print(f"[1] /health endpoint check: Status {res_health.status_code} | Body: {res_health.json()}")

        # 2. SSE Streaming /api/chat test
        payload = {"session_id": "p4e_e2e_session", "message": "Do you have Pharma OS?"}
        headers = {"Origin": "https://citta-omega.vercel.app"}

        print(f"[2] Testing POST /api/chat SSE Streaming with Origin header '{headers['Origin']}'...")
        
        t0 = asyncio.get_event_loop().time()
        res_stream = await client.post("/api/chat", json=payload, headers=headers)
        t1 = asyncio.get_event_loop().time()

        print(f"   -> Response Status: {res_stream.status_code}")
        print(f"   -> Content-Type: {res_stream.headers.get('content-type')}")
        print(f"   -> Access-Control-Allow-Origin: {res_stream.headers.get('access-control-allow-origin')}")

        lines = res_stream.text.split("\n\n")
        parsed_chunks = []
        done_chunk = None

        for line in lines:
            if line.startswith("data: "):
                try:
                    data_obj = json.loads(line[6:])
                    parsed_chunks.append(data_obj)
                    if data_obj.get("done"):
                        done_chunk = data_obj
                except Exception:
                    pass

        chunk_count = len(parsed_chunks)
        has_done = done_chunk is not None
        source = done_chunk.get("source", "Unknown") if done_chunk else "None"

        print(f"   -> Received SSE Chunks: {chunk_count}")
        print(f"   -> Terminal Done Chunk Received: {has_done}")
        print(f"   -> Source Attribution: '{source}'")
        print(f"   -> Total HTTP Connection Duration: {(t1 - t0)*1000.0:.2f} ms")

        # 3. Check for forbidden leakages
        raw_text = res_stream.text.lower()
        forbidden_terms = ["groq_api_key", "nvidia_api_key", "traceback", "modulenotfounderror", "keyerror"]
        leakage = any(term in raw_text for term in forbidden_terms)

        print(f"[3] Sensitive Error/Credential Leakage Check: {'CLEAN (PASS)' if not leakage else 'LEAK DETECTED (FAIL)'}")

        sse_pass = res_stream.status_code == 200 and has_done and chunk_count > 1 and not leakage

        print("\n" + "=" * 90)
        print(f"PHASE 4E END-TO-END SSE VERIFICATION: {'PASS' if sse_pass else 'FAIL'}")
        print("=" * 90)

if __name__ == "__main__":
    asyncio.run(run_e2e_sse_verification())
