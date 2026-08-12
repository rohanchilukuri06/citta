import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(Path(BACKEND_DIR) / '.env')

import config
from server import get_rag_service

GROUNDING_TEST_CASES = [
    {
        "id": "G1",
        "category": "Known Fact",
        "query": "Do you have Pharma OS?",
        "expected_keywords": ["pharma", "quality", "compliance"],
        "forbidden_keywords": []
    },
    {
        "id": "G2",
        "category": "Known Fact",
        "query": "Do you have Education OS?",
        "expected_keywords": ["education", "college", "learning"],
        "forbidden_keywords": []
    },
    {
        "id": "G3",
        "category": "Fact Preservation",
        "query": "How long does the MarTech 360 strategy process take?",
        "expected_keywords": ["2-3 weeks"],
        "forbidden_keywords": []
    },
    {
        "id": "G4",
        "category": "Unknown Fact (Pricing)",
        "query": "What is the annual subscription price of Pharma OS?",
        "expected_keywords": ["not available"],
        "forbidden_keywords": ["$", "usd", "per year", "annual fee"]
    },
    {
        "id": "G5",
        "category": "Unknown Fact (CEO)",
        "query": "Who is the CEO of Education OS?",
        "expected_keywords": ["not available"],
        "forbidden_keywords": ["john", "ceo of education os is"]
    },
    {
        "id": "G6",
        "category": "Unknown Fact (Customer Count)",
        "query": "How many active enterprise customers currently use MarTech 360?",
        "expected_keywords": ["case studies", "3"],
        "forbidden_keywords": ["1000 customers", "500 customers", "thousands of customers"]
    }
]

async def run_grounding_tests():
    print("=" * 85)
    print("PHASE 4C — GROUNDING & HALLUCINATION RESISTANCE TEST SUITE")
    print("=" * 85)

    rag_serv = get_rag_service()
    model = getattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile")

    passed_count = 0

    for test in GROUNDING_TEST_CASES:
        session_id = f"p4c_{test['id']}"
        full_response = ""

        async for chunk in rag_serv.chat_stream(session_id=session_id, message=test["query"], model=model):
            if not chunk.get("done"):
                full_response += chunk.get("text", "")

        resp_lower = full_response.lower()

        unsupported_phrases = ["not available", "does not mention", "not mentioned", "not provided", "does not contain", "does not include", "no information", "case studies"]
        if "not available" in test["expected_keywords"] or "case studies" in test["expected_keywords"]:
            has_expected = any(kw in resp_lower for kw in unsupported_phrases)
        else:
            has_expected = all(kw in resp_lower for kw in test["expected_keywords"])
            
        has_forbidden = any(kw in resp_lower for kw in test["forbidden_keywords"])

        status = "PASS" if (has_expected and not has_forbidden) else "FAIL"
        if status == "PASS":
            passed_count += 1

        preview_text = full_response[:100].encode('ascii', 'replace').decode('ascii')
        print(f"[{test['id']}] Category: {test['category']:<25} | Query: '{test['query']}'")
        print(f"     Status: {status:<5} | Preview: {preview_text}...")
        if status == "FAIL":
            print(f"     -> Failed Expected: {test['expected_keywords']} | Found Forbidden: {test['forbidden_keywords']}")
        print("-" * 85)

    print(f"\nPhase 4C Grounding Results: {passed_count}/{len(GROUNDING_TEST_CASES)} Passed ({(passed_count/len(GROUNDING_TEST_CASES))*100:.1f}%)")
    print("=" * 85)

if __name__ == "__main__":
    asyncio.run(run_grounding_tests())
