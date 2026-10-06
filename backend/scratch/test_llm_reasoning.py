import asyncio
import sys

sys.path.append('.')
from phase2_orchestrator import get_phase2_orchestrator
from phase3_reasoning_engine import get_phase3_reasoning_engine
from groq_client import GroqClient
from query_normalizer import normalize_query_pipeline
from knowledge_registry import get_registry

async def run():
    orch = get_phase2_orchestrator()
    provider = GroqClient()
    engine = get_phase3_reasoning_engine(provider=provider)
    reg = get_registry()
    
    queries = [
        "Tell me about MarTech 3600",
        "What solutions did citta offer in health care"
    ]
    
    for q in queries:
        print(f"\n==========================================")
        print(f"QUERY: {q}")
        print(f"==========================================")
        norm_res = normalize_query_pipeline(q, reg.unified_vocabulary, reg.abbreviations)
        norm_q = norm_res["normalized_query"]
        ctx = orch.orchestrate("test_session", q, norm_q)
        res = await engine.execute_reasoning(ctx)
        print(f"SOURCE: {res['source']}")
        print(f"VERIFIED: {res['verified']}")
        print(f"CONFIDENCE: {res['confidence']}")
        print(f"RESPONSE LENGTH: {len(str(res['text']))}")
        print(f"RESPONSE TEXT:\n{res['text']}\n")

if __name__ == "__main__":
    asyncio.run(run())
