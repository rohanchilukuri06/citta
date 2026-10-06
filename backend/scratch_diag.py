import urllib.request
import json

def stream_post(query: str, session_id: str = "diag"):
    url = "http://localhost:8000/api/chat"
    req = urllib.request.Request(
        url,
        data=json.dumps({"message": query, "session_id": session_id}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    full_text = ""
    last_done = {}
    with urllib.request.urlopen(req) as resp:
        for line in resp:
            line_str = line.decode('utf-8').strip()
            if line_str.startswith("data: "):
                line_str = line_str[6:]
            if not line_str or line_str == "[DONE]":
                continue
            try:
                obj = json.loads(line_str)
                if "text" in obj:
                    full_text += obj["text"]
                if obj.get("done") is True:
                    last_done = obj
            except Exception:
                pass
    return {"text": full_text, "done": last_done}

test_cases = [
    {"q": "Show me everything you offer", "keywords": ["Products", "Services", "Solutions", "Platform", "OS", "portfolio", "CittaAI", "offering"]},
    {"q": "How much does it cost?", "keywords": ["verified information", "knowledge base", "not available", "contact", "pricing"]},
    {"q": "What companies have you worked with?", "keywords": ["Jewellery", "FMCG", "Spices", "Export", "case", "studies"]},
    {"q": "What awards have you received?", "keywords": ["award", "recognition", "certified", "won", "honors"]}
]

for item in test_cases:
    res = stream_post(item["q"])
    txt = res["text"]
    matched = [k for k in item["keywords"] if k.lower() in txt.lower()]
    print(f"Query: '{item['q']}'")
    print(f"Matched Keywords: {matched}")
    print(f"Response: {txt[:200]}...")
    print("-" * 60)
