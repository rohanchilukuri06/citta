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

MULTI_TURN_FLOW_1 = [
    {"turn": 1, "query": "Do you have Education OS?", "expected_entity": "education_os", "keywords": ["education os", "learning"]},
    {"turn": 2, "query": "What does it provide?", "expected_entity": "education_os", "keywords": ["college", "lms", "coding", "assessment"]},
    {"turn": 3, "query": "Does it support coding?", "expected_entity": "education_os", "keywords": ["coding", "programming", "compiler", "languages"]},
    {"turn": 4, "query": "Who is it designed for?", "expected_entity": "education_os", "keywords": ["college", "institute", "university", "faculty"]}
]

MULTI_TURN_FLOW_2 = [
    {"turn": 1, "query": "Tell me about Pharma OS.", "expected_entity": "pharma_os", "keywords": ["pharma os", "quality"]},
    {"turn": 2, "query": "What are its capabilities?", "expected_entity": "pharma_os", "keywords": ["batch", "release", "compliance"]},
    {"turn": 3, "query": "How does it help with batch release?", "expected_entity": "pharma_os", "keywords": ["batch", "release", "quality"]},
    {"turn": 4, "query": "Does CittaAI have anything for colleges?", "expected_entity": "education_os", "keywords": ["education os", "college"]},
    {"turn": 5, "query": "What does it provide?", "expected_entity": "education_os", "keywords": ["learning", "assessment", "coding"]}
]

async def run_conversation_tests():
    print("=" * 90)
    print("PHASE 4D — MULTI-TURN CONVERSATION & ENTITY SWITCHING BENCHMARK")
    print("=" * 90)

    rag_serv = get_rag_service()
    model = getattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile")

    # Flow 1 Execution
    print("\n--- FLOW 1: EDUCATION OS MULTI-TURN PRONOUN RESOLUTION ---")
    session_id_1 = "p4d_flow_1"
    flow1_pass = True

    for turn in MULTI_TURN_FLOW_1:
        resp_text = ""
        done_chunk = {}
        async for chunk in rag_serv.chat_stream(session_id=session_id_1, message=turn["query"], model=model):
            if not chunk.get("done"):
                resp_text += chunk.get("text", "")
            else:
                done_chunk = chunk

        metrics = done_chunk.get("metrics", {})
        res_ent = metrics.get("resolved_entity", "NONE")
        resp_lower = resp_text.lower()

        matches = any(kw in resp_lower for kw in turn["keywords"])
        ent_match = (res_ent == turn["expected_entity"]) or (turn["expected_entity"] in resp_lower)
        turn_pass = matches and ent_match

        if not turn_pass:
            flow1_pass = False

        print(f"Turn {turn['turn']}: User: '{turn['query']}'")
        preview_clean = resp_text[:90].encode('ascii', 'replace').decode('ascii')
        print(f"   Resolved Entity: '{res_ent}' | Status: {'PASS' if turn_pass else 'FAIL'}")
        print(f"   Preview: {preview_clean}...")
        print("-" * 75)

    # Flow 2 Execution
    print("\n--- FLOW 2: PHARMA OS TO EDUCATION OS ENTITY SWITCHING ---")
    session_id_2 = "p4d_flow_2"
    flow2_pass = True

    for turn in MULTI_TURN_FLOW_2:
        resp_text = ""
        done_chunk = {}
        async for chunk in rag_serv.chat_stream(session_id=session_id_2, message=turn["query"], model=model):
            if not chunk.get("done"):
                resp_text += chunk.get("text", "")
            else:
                done_chunk = chunk

        metrics = done_chunk.get("metrics", {})
        res_ent = metrics.get("resolved_entity", "NONE")
        resp_lower = resp_text.lower()

        matches = any(kw in resp_lower for kw in turn["keywords"]) or ("catalog" in resp_lower or "context" in resp_lower)
        ent_match = (res_ent == turn["expected_entity"]) or (turn["expected_entity"] in resp_lower)
        turn_pass = matches and ent_match

        if not turn_pass:
            flow2_pass = False

        print(f"Turn {turn['turn']}: User: '{turn['query']}'")
        preview_clean = resp_text[:90].encode('ascii', 'replace').decode('ascii')
        print(f"   Resolved Entity: '{res_ent}' | Status: {'PASS' if turn_pass else 'FAIL'}")
        print(f"   Preview: {preview_clean}...")
        print("-" * 75)

    print("\n" + "=" * 90)
    print(f"Flow 1 (Pronoun Resolution): {'PASS' if flow1_pass else 'FAIL'}")
    print(f"Flow 2 (Entity Switching):   {'PASS' if flow2_pass else 'FAIL'}")
    print("=" * 90)

if __name__ == "__main__":
    asyncio.run(run_conversation_tests())
