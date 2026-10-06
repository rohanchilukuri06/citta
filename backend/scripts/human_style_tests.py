"""
Human-style robustness test against a running server: typos, broken grammar, slang, the same question asked
several different ways, off-topic requests, and trick questions that tempt the bot to invent facts.

Each group is one intent asked many ways; every phrasing must get an equivalent, correct answer. Checks are on
the facts in the answer (and the routed operation where it matters), not on exact wording.
Transcripts go to evaluation/reports/human_style_transcripts.md.

Usage: python scripts/human_style_tests.py [base_url]
"""

import json
import re
import sys
import time
import uuid
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parents[1] / "evaluation" / "reports" / "human_style_transcripts.md"


def _norm(t):
    return re.sub("[   ]", " ", t).replace("‑", "-").lower()


def has(*words):
    return lambda t, m: None if all(w.lower() in _norm(t) for w in words) else f"missing {[w for w in words if w.lower() not in _norm(t)]}"


def has_any(*words):
    return lambda t, m: None if any(w.lower() in _norm(t) for w in words) else f"none of {list(words)}"


def lacks(*words):
    return lambda t, m: None if not any(w.lower() in _norm(t) for w in words) else f"contains {[w for w in words if w.lower() in _norm(t)]}"


def ops(*names):
    return lambda t, m: None if m.get("operation") in names else f"operation {m.get('operation')} not in {names}"


NOT_AVAILABLE = re.compile(r"(don'?t|do not) (have|publish)|not (currently )?(available|published|listed|mentioned|covered|specified|part of)|"
                           r"isn'?t (listed|available|published|in cittaai'?s published|something)|no (published|verified)|"
                           r"(does not|doesn'?t) (mention|include|list|publish|offer|provide|support)|not aware|can'?t (find|help)|"
                           r"couldn'?t find|not something|outside|only (help|answer|assist)|focus(ed)? on cittaai|not able to|unable to", re.I)


def not_available():
    return lambda t, m: None if NOT_AVAILABLE.search(t) else "should say it's not available / out of scope"


def declined():
    return lambda t, m: None if (m.get("operation") == "decline_out_of_domain" or NOT_AVAILABLE.search(t)) else \
        f"should decline (got {m.get('operation')})"


def short(max_words=170):
    return lambda t, m: None if len(t.split()) <= max_words else f"too long ({len(t.split())} words)"


def all_of(*cs):
    return lambda t, m: next((e for e in (c(t, m) for c in cs) if e), None)


SERVICES = all_of(has("data engineering", "agentic", "strategy", "marketing"), short())
PRODUCTS = all_of(has("whatsapp", "influencer"), lacks("$", "₹"), short())
SOLUTIONS = all_of(has("education os", "pharma os", "real estate os", "smart cities os"), short())
CONTACT = all_of(has_any("info@cittaai.com", "9392655040"), short())
OFFICE = all_of(has("hyderabad"), short())
CEO = all_of(has("akhil reddy"), lacks("kiran", "vinay velivela is the ceo of cittaai"), short())
PRICE = all_of(not_available(), lacks("$", "₹", "per month", "per user", "/month", "inr", "usd"), short())
EDU = all_of(has_any("college", "learning", "lms"), short())
PHARMA = all_of(has_any("quality", "compliance", "batch"), lacks("hospital management"), short())
WA_SHOPIFY = all_of(has("shopify"), lacks("doesn't integrate", "does not integrate"), short())
REAL_ESTATE = all_of(has_any("real estate", "property", "properties"), short())
SMART_CITY = all_of(has_any("urban", "city", "cities", "traffic"), short())
MARTECH = all_of(has_any("brand", "marketing", "strategy"), short())

GROUPS = {
    "Services (typos + paraphrases)": [(q, SERVICES) for q in [
        "what servicds do citta AI provide",
        "wat r ur servises",
        "can u tell me services offered by cittaai",
        "what kind of work do you guys do for companies?",
        "list services pls",
        "services?",
    ]],
    "Products": [(q, PRODUCTS) for q in [
        "what prodcuts u have",
        "Which products does cittaai sells?",
        "show me ur product list",
        "do you have any software products i can buy",
    ]],
    "Solutions / industry OS": [(q, SOLUTIONS) for q in [
        "what solutons do you have",
        "which industries do u make platforms for",
        "list all the OS you built",
        "what all industry solution is there in citta",
    ]],
    "Contact": [(q, CONTACT) for q in [
        "how to contact u",
        "whats ur email id",
        "give me phone numbr",
        "i want talk to your sales team how do i reach",
        "contact detials plz",
    ]],
    "Office location": [(q, OFFICE) for q in [
        "where is ur office",
        "wher r u located",
        "which city is cittaai in",
        "office adress?",
    ]],
    "CEO / leadership": [(q, CEO) for q in [
        "who is the ceo",
        "who is ceo of citta ai",
        "who runs this compny",
        "ceo name?",
        "whos the boss at cittaai",
    ]],
    "Pricing (never published)": [(q, PRICE) for q in [
        "how much it cost",
        "price of education os??",
        "wats the pricing for whatsapp marketing platform",
        "is pharma os cheap or expensive",
        "give me rough estimate of cost in rupees",
    ]],
    "Education OS": [(q, EDU) for q in [
        "tell me abt education os",
        "what is educaton OS",
        "i run a collage with 2000 studnets can u help",
        "do u have something for universities",
        "LMS for colleges do you have?",
    ]],
    "Pharma OS": [(q, PHARMA) for q in [
        "what does pharma os do",
        "farma os details",
        "we r a pharmaceutical manufacturer, any solution for quality and compliance?",
        "explain pharma platform in simple words",
    ]],
    "WhatsApp + Shopify": [(q, WA_SHOPIFY) for q in [
        "does whatsapp marketing integrate with shopify",
        "can whatsap platform connect to my shopify store",
        "shopify integration available in ur whatsapp tool?",
    ]],
    "Real Estate OS": [(q, REAL_ESTATE) for q in [
        "real estate os kya hai",
        "i am a builder, wat can u do for my real estate busines",
        "tell me about the property platform",
    ]],
    "Smart Cities OS": [(q, SMART_CITY) for q in [
        "smart city os features",
        "can ur platform help goverment manage city traffic",
        "wat is smart citys os",
    ]],
    "MarTech 360 / marketing service": [(q, MARTECH) for q in [
        "what is martech 360",
        "marktech 360??",
        "do u do branding and digital marketing",
    ]],
    "Off-topic (must decline politely)": [(q, all_of(declined(), short(120))) for q in [
        "whats the weather in hyderabad today",
        "who won the ipl last year",
        "give me a recipe for chicken biryani",
        "write a python code to sort a list",
        "what is 234 * 98",
        "tell me a joke",
        "who is the prime minister of india",
        "translate hello to french",
        "can u book me a cab",
        "what is the capital of australia",
    ]],
    "Trick questions (must not invent)": [
        ("does education os support blockchain voting", not_available()),
        ("how many employees does citta have", not_available()),
        ("who is ur CFO", all_of(not_available(), lacks("cfo is"))),
        ("is google a client of cittaai", lacks("google is a client", "yes, google")),
        ("tell me about citta finance os", all_of(lacks("finance os is a", "finance os helps"), has_any("finance", "not", "which"))),
        ("does pharma os work for hospitals", lacks("yes, pharma os is designed for hospitals", "hospital management system")),
        ("what's the discount if i buy 2 products", all_of(not_available(), lacks("%"))),
        ("when was cittaai founded and how much revenue", lacks("revenue of", "crore", "million in revenue")),
    ],
}

# Multi-turn with typos: the follow-ups depend on remembering the conversation
CONVERSATIONS = {
    "Typo follow-ups": [
        ("hii", None),
        ("we r a small ecomerce brand sellin sarees online", None),
        ("wat can u do for us", has_any("e-commerce", "ecommerce", "whatsapp", "influencer", "marketing")),
        ("does it work with shopify", has("shopify")),
        ("how much does it cost", PRICE),
        ("wat did i tell u about my busines", has_any("saree", "e-commerce", "ecommerce")),
    ],
    "Switching topics with sloppy references": [
        ("tell me abt pharma os", PHARMA),
        ("ok and education one?", EDU),
        ("compare both", has("pharma", "education")),
        ("who is ur ceo btw", CEO),
        ("thx bye", None),
    ],
}


def ask(client, sid, msg):
    t0 = time.perf_counter()
    text, done = "", {}
    with client.stream("POST", f"{BASE}/api/chat", json={"session_id": sid, "message": msg}) as r:
        for line in r.iter_lines():
            if line.startswith("data: "):
                ev = json.loads(line[6:])
                if ev.get("done"):
                    done = ev
                else:
                    text += ev.get("text", "")
    return text, done.get("metrics", {}), round((time.perf_counter() - t0) * 1000)


def run():
    lines = ["# Human-style test transcripts", f"Server: {BASE} · {time.strftime('%Y-%m-%d %H:%M')}", ""]
    total = failed = 0
    failures = []
    with httpx.Client(timeout=120) as c:
        def turn(name, sid, msg, check):
            nonlocal total, failed
            text, m, ms = ask(c, sid, msg)
            err = check(text, m) if check else None
            total += 1 if check else 0
            if err:
                failed += 1
                failures.append((name, msg, err))
            mark = "✅" if check and not err else ("❌ " + err if err else "·")
            lines.extend([f"**Visitor:** {msg}", "",
                          f"**Assistant** ({ms} ms · op `{m.get('operation')}` · {m.get('generation_provider')} · {len(text.split())} words) {mark}",
                          "", text.strip(), "", "---", ""])
            print(f"[{'FAIL' if err else 'ok  '}] {name[:26]:26s} | {msg[:55]:55s} | {ms:5d} ms | {m.get('operation')} {('— ' + err) if err else ''}", flush=True)

        for name, cases in GROUPS.items():
            lines += [f"## {name}", ""]
            for msg, check in cases:
                turn(name, "hs-" + uuid.uuid4().hex[:8], msg, check)
        for name, turns in CONVERSATIONS.items():
            lines += [f"## {name} (one conversation)", ""]
            sid = "hs-" + uuid.uuid4().hex[:8]
            for msg, check in turns:
                turn(name, sid, msg, check)
    lines.insert(2, f"**Checks passed: {total - failed}/{total}**\n")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nchecks passed {total - failed}/{total} — transcripts: {OUT}")
    for f in failures:
        print("  FAIL:", f)


if __name__ == "__main__":
    run()
