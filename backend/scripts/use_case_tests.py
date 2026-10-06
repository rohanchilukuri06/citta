"""
End-to-end use cases against a running server (/api/chat over HTTP + SSE), with automatic checks.

Each scenario is one conversation (same session). Checks are deliberately about behaviour that matters to
visitors: correct routing, memory, no invented facts. Full transcripts go to
evaluation/reports/use_case_transcripts.md for human review.

Usage: python scripts/use_case_tests.py [base_url]
"""

import json
import re
import sys
import time
import uuid
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8011"
OUT = Path(__file__).resolve().parents[1] / "evaluation" / "reports" / "use_case_transcripts.md"

# (message, check) — check(text, metrics) returns an error string or None
def op(name): return lambda t, m: None if m.get("operation") == name else f"expected operation {name}, got {m.get('operation')}"
def ent(e): return lambda t, m: None if (m.get("decision") or {}).get("entity") == e else f"expected entity {e}, got {(m.get('decision') or {}).get('entity')}"
def kind(k): return lambda t, m: None if m.get("turn_kind") == k else f"expected turn {k}, got {m.get('turn_kind')}"
def _norm(t): return re.sub("[   ]", " ", t).replace("‑", "-").lower()
def has(*words): return lambda t, m: None if all(w.lower() in _norm(t) for w in words) else f"answer missing {[w for w in words if w.lower() not in _norm(t)]}"
def lacks(*words): return lambda t, m: None if not any(w.lower() in _norm(t) for w in words) else f"answer contains {[w for w in words if w.lower() in _norm(t)]}"
def not_available(): return lambda t, m: None if re.search(r"(don'?t|do not) have|not (currently )?available|isn'?t (listed|available|published|in cittaai'?s published)|no (published|verified)|not (mentioned|covered|specified|listed)|(does not|doesn'?t) (mention|include|list|publish)|not aware|can'?t find|couldn'?t find|not something", t, re.I) else "answer should say the information is not available"
def parts(n): return lambda t, m: None if len(m.get("parts") or []) == n else f"expected {n} parts, got {len(m.get('parts') or [])}"
def all_of(*cs): return lambda t, m: next((e for e in (c(t, m) for c in cs) if e), None)

SCENARIOS = {
    "University visitor journey (memory + follow-ups + rewrite)": [
        ("Hi!", kind("small_talk")),
        ("We are an engineering college in Hyderabad with about 3000 students. What can you do for us?", ent("education_os")),
        ("Who is it for?", all_of(ent("education_os"), op("get_target_users"))),
        ("How does it work?", all_of(ent("education_os"), op("get_workflow"))),
        ("explain that more simply", kind("rewrite")),
        ("How much does it cost?", all_of(op("get_pricing"), not_available(), lacks("$", "₹", "per month", "per year"))),
        ("What did I tell you about my college?", all_of(kind("conversation_memory"), has("3000 students"))),
    ],
    "Large multi-part request": [
        ("What is WhatsApp Marketing, who is it for, and does it integrate with Shopify? Also where is your office and what is your email?",
         all_of(parts(4), has("info@cittaai.com"))),
    ],
    "Hallucination probes (must not invent)": [
        ("Does Education OS support blockchain-based voting for student elections?", not_available()),
        ("What is the price of Pharma OS in USD?", all_of(not_available(), lacks("$"))),
        ("Which Fortune 500 companies use CittaAI?", lacks("Fortune 500 companies like", "Google", "Microsoft", "Amazon")),
        ("Who is CittaAI's CFO?", lacks("CFO is", "CFO:")),
        ("How many employees does CittaAI have?", not_available()),
    ],
    "Comparison, both, the other one": [
        ("Compare Education OS and Pharma OS", all_of(has("Education OS", "Pharma"))),
        ("What about both of their workflows?", None),
        ("and the other one?", ent("pharma_os")),
    ],
    "Knowledge from the live website": [
        ("Do you do local SEO for businesses in Hyderabad?", all_of(ent("ai_powered_marketing"), has("Hyderabad"))),
        ("We run a chain of clinics and patients keep missing appointments. Can you help?", lacks("Pharma OS")),
        ("Will WhatsApp messages feel like spam to my customers?", None),
    ],
    "Leadership (owner-confirmed: Akhil Reddy is CEO)": [
        ("Who is the CEO of CittaAI?", all_of(has("Akhil Reddy"), lacks("Vinay Velivela is the CEO of CittaAI", "Kiran"))),
        ("Is Vinay Velivela your CEO?", all_of(has("Fixity"), lacks("Kiran"))),
    ],
    "Out of scope and unknown products": [
        ("Can you book me a flight to Delhi?", op("decline_out_of_domain")),
        ("Tell me about CittaAI's Finance OS", has("Finance")),
        ("Write me a Python script to scrape websites", op("decline_out_of_domain")),
    ],
}


def run():
    lines = [f"# Use-case transcripts", f"Server: {BASE} · {time.strftime('%Y-%m-%d %H:%M')}", ""]
    total = failed = 0
    with httpx.Client(timeout=120) as c:
        for name, turns in SCENARIOS.items():
            sid = "uc-" + uuid.uuid4().hex[:8]
            lines += [f"## {name}", ""]
            for msg, check in turns:
                t0 = time.perf_counter(); text, done = "", {}
                with c.stream("POST", f"{BASE}/api/chat", json={"session_id": sid, "message": msg}) as r:
                    for line in r.iter_lines():
                        if line.startswith("data: "):
                            ev = json.loads(line[6:])
                            if ev.get("done"): done = ev
                            else: text += ev.get("text", "")
                ms = round((time.perf_counter() - t0) * 1000)
                m = done.get("metrics", {})
                err = check(text, m) if check else None
                total += 1 if check else 0
                failed += 1 if err else 0
                status = "✅" if check and not err else ("❌ " + err if err else "·")
                lines += [f"**Visitor:** {msg}", "", f"**Assistant** ({ms} ms · {m.get('turn_kind')} · op `{m.get('operation')}` · "
                          f"provider {m.get('generation_provider')} · verified {done.get('verified')}) {status}", "", text.strip(), "", "---", ""]
                print(f"[{'FAIL' if err else 'ok  '}] {name[:28]:28s} | {msg[:60]:60s} | {ms:5d} ms | {m.get('turn_kind')}/{m.get('operation')} {('— ' + err) if err else ''}")
    lines.insert(2, f"**Checks passed: {total - failed}/{total}**\n")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nchecks passed {total - failed}/{total} — transcripts: {OUT}")


if __name__ == "__main__":
    run()
