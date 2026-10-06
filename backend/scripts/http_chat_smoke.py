"""Drive a running server's /api/chat over HTTP + SSE, exactly like the website widget does."""
import json, sys, time, uuid
import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8011"
TURNS = sys.argv[2:] or [
    "What solutions do you offer for education?", "Who is it for?", "Why would we use it?",
    "Compare Education and Pharma", "What about both?", "and the other one?",
    "wat services u offer", "How do I reach you?", "Can you book me a flight?",
    "Tell me about Finance OS", "We run three hospitals and want online appointment booking",
    "How much does WhatsApp Marketing cost?",
]
sid = "http-smoke-" + uuid.uuid4().hex[:6]
with httpx.Client(timeout=90) as c:
    for q in TURNS:
        t0 = time.perf_counter(); text, done = "", {}
        with c.stream("POST", f"{BASE}/api/chat", json={"session_id": sid, "message": q}, headers={"Origin": "https://cittaai.com"}) as r:
            for line in r.iter_lines():
                if line.startswith("data: "):
                    ev = json.loads(line[6:])
                    if ev.get("done"): done = ev
                    else: text += ev.get("text", "")
        m = done.get("metrics", {}); d = m.get("decision", {})
        print(f"\n>>> {q}  [{r.status_code}, {round((time.perf_counter()-t0)*1000)} ms, cors={r.headers.get('access-control-allow-origin')}]")
        print(f"    pipeline={m.get('pipeline')} op={m.get('operation')} ent={d.get('entity')} ents={d.get('entities')} aspect={d.get('aspect')} scope={d.get('scope')} verified={done.get('verified')} provider={m.get('generation_provider')}")
        print("    " + text.replace("\n", " ")[:260])
