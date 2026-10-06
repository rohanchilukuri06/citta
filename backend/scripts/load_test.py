"""
Concurrent-visitor load test against a running server.

N visitors chat at the same time, each in its own session: first about a different offering, then a
pronoun follow-up ("Who is it for?"). Checks: every request succeeds, each follow-up resolves to *that
visitor's* offering (no context leaking between sessions), and reports latency percentiles.

Usage: python scripts/load_test.py [base_url] [visitors]
(Start the server with a raised CHAT_RATE_LIMIT_PER_IP_PER_MIN — all test traffic comes from one IP.)
"""

import asyncio
import json
import statistics
import sys
import time
import uuid

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8011"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 24
OFFERINGS = [("Tell me about Education OS", "education_os"), ("What is Pharma OS?", "pharma_os"),
             ("Tell me about Real Estate OS", "real_estate_os"), ("What does Smart Cities OS do?", "smart_cities_os"),
             ("Explain E-Commerce OS", "ecommerce_os"), ("What is the WhatsApp Marketing Platform?", "whatsapp_marketing"),
             ("Tell me about your Influencer Marketing Platform", "influencer_marketing"), ("What is Enterprise AI OS?", "enterprise_ai_os")]


async def ask(client, sid, msg):
    t0 = time.perf_counter()
    text, done = "", {}
    async with client.stream("POST", f"{BASE}/api/chat", json={"session_id": sid, "message": msg}) as r:
        if r.status_code != 200:
            return r.status_code, (time.perf_counter() - t0) * 1000, {}, ""
        async for line in r.aiter_lines():
            if line.startswith("data: "):
                ev = json.loads(line[6:])
                if ev.get("done"):
                    done = ev
                else:
                    text += ev.get("text", "")
    return 200, (time.perf_counter() - t0) * 1000, done, text


async def visitor(client, i):
    sid = f"load-{uuid.uuid4().hex[:8]}"
    first, expected = OFFERINGS[i % len(OFFERINGS)]
    s1, t1, d1, x1 = await ask(client, sid, first)
    s2, t2, d2, x2 = await ask(client, sid, "Who is it for?")
    got = ((d2.get("metrics") or {}).get("decision") or {}).get("entity")
    return {"ok": s1 == 200 and s2 == 200 and bool(x1.strip()) and bool(x2.strip()), "status": (s1, s2), "lat": [t1, t2],
            "context_ok": got == expected, "expected": expected, "got": got,
            "providers": [(d.get("metrics") or {}).get("generation_provider") for d in (d1, d2)]}


async def main():
    limits = httpx.Limits(max_connections=N * 2, max_keepalive_connections=N * 2)
    async with httpx.AsyncClient(timeout=180, limits=limits) as client:
        t0 = time.perf_counter()
        results = await asyncio.gather(*(visitor(client, i) for i in range(N)))
        wall = time.perf_counter() - t0
    lat = sorted(l for r in results for l in r["lat"])
    p = lambda q: round(lat[min(len(lat) - 1, int(q * len(lat)))])
    ok = sum(r["ok"] for r in results)
    ctx = sum(r["context_ok"] for r in results)
    providers = {}
    for r in results:
        for pr in r["providers"]:
            providers[pr] = providers.get(pr, 0) + 1
    print(f"{N} concurrent visitors x 2 turns = {2 * N} requests in {wall:.1f}s")
    print(f"successful conversations: {ok}/{N} | follow-up kept the right offering (no cross-session leakage): {ctx}/{N}")
    print(f"latency ms: p50 {p(0.5)} | p90 {p(0.9)} | p95 {p(0.95)} | max {round(lat[-1])} | mean {round(statistics.mean(lat))}")
    print(f"answered by: {providers}")
    for r in results:
        if not r["ok"] or not r["context_ok"]:
            print("  problem:", r)


if __name__ == "__main__":
    asyncio.run(main())
