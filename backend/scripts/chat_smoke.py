"""Drive the production /api/chat path (RAGService.chat_stream) through a scripted conversation."""
import asyncio, json, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
logging.disable(logging.WARNING)

TURNS = sys.argv[1:] or [
    "What solutions do you offer for education?", "Who is it for?", "What can it do?", "Why would I use it?",
    "Compare Education and Pharma", "What about both?", "What solutions do you offer?",
    "Can you book me a flight?", "Tell me about Finance OS", "How do I reach you?",
]

async def main():
    import server, config
    rag = server.get_rag_service()
    sid = "smoke-" + str(abs(hash(tuple(TURNS))))[:6]
    for q in TURNS:
        text, done = "", {}
        async for ch in rag.chat_stream(sid, q, config.MODEL_NAME):
            if ch.get("done"): done = ch
            else: text += ch.get("text", "")
        m = done.get("metrics", {}); d = m.get("decision", {})
        print(f"\n>>> {q}\n    [{m.get('pipeline')}] op={m.get('operation')} {m.get('operation_inputs')} ent={d.get('entity')} ents={d.get('entities')} aspect={d.get('aspect')} scope={d.get('scope')} verified={done.get("verified")} reasons={m.get("validator_reasons")} fallback={m.get('semantic_fallback')} total_ms={m.get('total_ms')}")
        print("    " + text.replace("\n", " ")[:300])

asyncio.run(main())
