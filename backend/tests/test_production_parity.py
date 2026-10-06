"""
Production parity: the decision /api/chat serves must be the decision the benchmark evaluates.

Drives the real RAGService.chat_stream (the /api/chat handler) with an offline fake LLM provider,
reads the semantic decision + operation it reports, and compares them with the benchmark path
(SemanticChatPipeline.decide). LLM adjudication is disabled so both sides are deterministic.
"""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

import config

config.SEMANTIC_LLM_ADJUDICATION = False
import tempfile, uuid as _uuid
# Isolated conversation memory per test run (memory persists in SQLite in production)
config.CHAT_MEMORY_DB_PATH = str(Path(tempfile.gettempdir()) / f"citta_test_memory_{_uuid.uuid4().hex[:8]}.db")

SINGLE_TURN = [
    "What solutions do you offer for education?",
    "I run a university. What can CittaAI do for us?",
    "What can you offer colleges?",
    "anything for academic institutions?",
    "what can citta do for universty?",
    "What services do you have for WhatsApp?",
    "What solutions do you offer?",
    "list your services",
    "Compare Education and Pharma",
    "How do I reach you?",
    "Who founded CittaAI?",
    "Have you won any awards?",
    "Tell me about Finance OS",
    "Can you book me a flight?",
    "What about both?",
    "How much does Pharma OS cost?",
]
CONVERSATION = ["Tell me about Education OS", "Who is it for?", "What can it do?",
                "Compare Education and Pharma", "What about both?"]


class FakeProvider:
    async def generate_stream(self, messages, model, temperature=0.7, max_tokens=None):
        yield {"text": "Here is what CittaAI offers for this."}

    async def generate(self, messages, model, temperature=0.7):
        return "Here is what CittaAI offers for this."


@pytest.fixture(scope="module")
def production():
    from rag_service import RAGService
    from vector_store import VectorStore
    return RAGService(provider=FakeProvider(), vector_store=VectorStore(config.VECTOR_DB_PATH))


def _served(rag, session_id, message):
    async def run():
        done = {}
        async for chunk in rag.chat_stream(session_id, message, config.MODEL_NAME):
            if chunk.get("done"):
                done = chunk
        return done
    return asyncio.run(run())


def _signature(decision_dict, operation, inputs):
    return (decision_dict["entity"], tuple(decision_dict["entities"] or []), decision_dict["intent"],
            decision_dict["aspect"], decision_dict["scope"], operation, inputs.get("entity_id"))


def _benchmark_side(message, state):
    from semantic_chat_pipeline import get_semantic_chat_pipeline
    decision, plans = get_semantic_chat_pipeline().decide(message, state)
    d = decision.to_dict()
    return _signature(d, plans[0].operation_name, plans[0].inputs or {})


@pytest.mark.parametrize("message", SINGLE_TURN)
def test_single_turn_parity(production, message):
    from semantic_chat_pipeline import ConversationState
    expected = _benchmark_side(message, ConversationState())
    done = _served(production, f"parity-{abs(hash(message))}", message)
    m = done["metrics"]
    assert m["pipeline"] == "semantic" and m["semantic_fallback"] is False
    assert _signature(m["decision"], m["operation"], m["operation_inputs"]) == expected


def test_conversation_parity(production):
    """Each turn's served decision equals decide() applied to the same conversation state."""
    import copy
    from semantic_chat_pipeline import get_semantic_chat_pipeline
    pipeline = get_semantic_chat_pipeline()
    sid = "parity-conversation"
    for message in CONVERSATION:
        state_before = copy.deepcopy(pipeline.state(sid))
        expected = _benchmark_side(message, state_before)
        m = _served(production, sid, message)["metrics"]
        assert _signature(m["decision"], m["operation"], m["operation_inputs"]) == expected, message


def test_conversation_context_is_used(production):
    sid = "parity-context"
    _served(production, sid, "Tell me about Education OS")
    m = _served(production, sid, "Who is it for?")["metrics"]
    assert m["decision"]["entity"] == "education_os" and m["decision"]["aspect"] == "TARGET_USERS"
    _served(production, sid, "Compare Education and Pharma")
    m = _served(production, sid, "What about both?")["metrics"]
    assert set(m["decision"]["entities"]) == {"education_os", "pharma_os"}


def test_both_without_context_clarifies(production):
    m = _served(production, "parity-both-cold", "What about both?")["metrics"]
    assert m["operation"] == "request_clarification"


def test_missing_section_is_not_generated(production):
    # No offering publishes pricing: the bot must say so, never generate a price
    done = _served(production, "parity-missing", "How much does Pharma OS cost?")
    assert done["metrics"]["operation"] == "get_pricing"
    assert done["metrics"]["evidence_available"] == [False]
    assert "llm_ms" not in done["metrics"]
