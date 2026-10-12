"""
Conversation layer: compound questions, persistent memory, small talk, recall of the conversation,
and rewrites of the previous answer. Uses an offline fake LLM and an isolated memory database.
"""

import asyncio
import sys
import tempfile
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

import config

config.SEMANTIC_LLM_ADJUDICATION = False

from semantic_chat_pipeline import SemanticChatPipeline, split_questions  # noqa: E402


class EchoProvider:
    """Offline LLM stand-in: returns the first knowledge line it was given, so answers stay grounded."""
    last_provider = "fake"

    async def generate_stream(self, messages, model, temperature=0.7, max_tokens=None):
        system = messages[0]["content"]
        knowledge = system.split("KNOWLEDGE:", 1)[-1]
        line = next((l.strip("- ").strip() for l in knowledge.splitlines() if l.strip().startswith("- ")), "Here is what I found.")
        yield line


@pytest.fixture()
def pipeline(tmp_path):
    from chat_memory import ChatMemoryStore
    from query_intelligence_engine import QueryIntelligenceEngine
    return SemanticChatPipeline(provider=EchoProvider(), engine=QueryIntelligenceEngine(enable_llm=False),
                                memory=ChatMemoryStore(tmp_path / "memory.db"))


def chat(pipeline, sid, message):
    async def run():
        text, done = "", {}
        async for c in pipeline.stream(sid, message, "m"):
            if c.get("done"):
                done = c
            else:
                text += c["text"]
        return text, done
    return asyncio.run(run())


@pytest.mark.parametrize("message,expected", [
    ("I run a university. What can CittaAI do for us?", 1),
    ("What is Education OS and how does it work? Also, who is the CEO?", 3),
    ("Compare Education and Pharma", 1),
    ("What products do you have? What services do you offer? Where is your office?", 3),
    ("We are a retail brand. We need better retention. What do you recommend?", 1),
])
def test_split_questions(message, expected):
    assert len(split_questions(message)) == expected


def test_compound_message_answers_every_part(pipeline):
    _, done = chat(pipeline, "s-compound", "What is Education OS and how does it work? Also, where is your office?")
    parts = done["metrics"]["parts"]
    assert [p["operation"] for p in parts] == ["get_solution", "get_workflow", "get_contact"]
    assert parts[1]["entity"] == "education_os"  # "it" resolved to the offering named in the first part


def test_memory_persists_across_restart(pipeline, tmp_path):
    from chat_memory import ChatMemoryStore
    from query_intelligence_engine import QueryIntelligenceEngine
    sid = "s-" + uuid.uuid4().hex[:6]
    chat(pipeline, sid, "We are an engineering college with 5000 students. Tell me about Education OS")
    fresh = SemanticChatPipeline(provider=EchoProvider(), engine=QueryIntelligenceEngine(enable_llm=False),
                                 memory=ChatMemoryStore(tmp_path / "memory.db"))  # simulated restart
    _, done = chat(fresh, sid, "Who is it for?")
    assert done["metrics"]["decision"]["entity"] == "education_os"
    assert any("5000 students" in f for f in fresh.state(sid).visitor_facts)


def test_conversation_recall(pipeline):
    sid = "s-recall"
    chat(pipeline, sid, "Tell me about Pharma OS")
    chat(pipeline, sid, "What products do you have?")
    text, done = chat(pipeline, sid, "What was my first question?")
    assert done["metrics"]["turn_kind"] == "conversation_memory"
    assert "Tell me about Pharma OS" in text
    text, _ = chat(pipeline, sid, "Can you summarize our conversation?")
    assert "Pharma OS" in text


@pytest.mark.parametrize("message", ["hi", "Hello there!", "thanks", "who are you?", "bye"])
def test_small_talk_is_not_a_knowledge_lookup(pipeline, message):
    _, done = chat(pipeline, "s-small-" + message, message)
    assert done["metrics"]["turn_kind"] == "small_talk"


def test_rewrite_uses_previous_answer_evidence(pipeline):
    sid = "s-rewrite"
    chat(pipeline, sid, "What can Education OS do?")
    _, done = chat(pipeline, sid, "explain that more simply")
    assert done["metrics"]["turn_kind"] == "rewrite"


def test_clear_removes_persistent_memory(pipeline):
    sid = "s-clear"
    chat(pipeline, sid, "Tell me about Pharma OS")
    pipeline.clear(sid)
    assert pipeline.memory.load(sid) is None


def test_long_bullet_lists_are_capped_unless_detail_requested():
    from semantic_chat_pipeline import _cap_bullets, _DETAIL_REQUEST, MAX_ANSWER_BULLETS
    answer = "Pharma OS does quality work.\n\n" + "\n".join(f"- point {i}" for i in range(9)) + "\n\nWant a demo?"
    capped = _cap_bullets(answer)
    assert capped.count("- point") == MAX_ANSWER_BULLETS
    assert capped.endswith("Want a demo?")
    assert _DETAIL_REQUEST.search("List all capabilities of Pharma OS")
    assert not _DETAIL_REQUEST.search("What does Pharma OS do?")


def test_human_style_helpers():
    from semantic_chat_pipeline import _ARITHMETIC, _PRICE_QUESTION, _META, _normalise_shorthand, _cap_bullets
    assert _ARITHMETIC.match("what is 234 * 98") and _ARITHMETIC.match("12+7=?")
    assert not _ARITHMETIC.match("what is education os") and not _ARITHMETIC.match("Smart Cities OS 2.0")
    assert _PRICE_QUESTION.search("how much it cost") and _PRICE_QUESTION.search("rough estimate in rupees")
    assert not _PRICE_QUESTION.search("tell me about pharma os")
    assert _META.search(_normalise_shorthand("wat did i tell u about my busines"))
    long_bullet = "- " + " ".join(f"w{i}," for i in range(40))
    assert len(_cap_bullets(long_bullet).split()) <= 29


def test_faq_items_keep_their_answer_when_shortened():
    from semantic_chat_pipeline import _short
    assert "info@cittaai.com" in _short("What is CittaAI's email address? — info@cittaai.com")
    assert "Mon-Fri" in _short("What are your business hours? — Mon-Fri 9am-6pm")


class ListAllProvider(EchoProvider):
    """Answers with every knowledge line as a bullet, like the real model does for a roster question."""
    async def generate_stream(self, messages, model, temperature=0.7, max_tokens=None):
        knowledge = messages[0]["content"].split("KNOWLEDGE:", 1)[-1]
        yield "\n".join(l for l in knowledge.splitlines() if l.strip().startswith("- "))


def test_team_list_is_not_cut_to_five(tmp_path):
    # live miss: the 5-bullet cap silently dropped the sixth team member from "who are the team members"
    from chat_memory import ChatMemoryStore
    from query_intelligence_engine import QueryIntelligenceEngine
    from semantic_chat_pipeline import MAX_ANSWER_BULLETS
    p = SemanticChatPipeline(provider=ListAllProvider(), engine=QueryIntelligenceEngine(enable_llm=False),
                             memory=ChatMemoryStore(tmp_path / "memory.db"))
    text, _ = chat(p, "team", "who are the citta team members")
    assert "Akhil Reddy" in text and "Parvatha Mohan" in text
    assert sum(l.strip().startswith("- ") for l in text.splitlines()) > MAX_ANSWER_BULLETS


class DownProvider(EchoProvider):
    """The answer model is unreachable: the pipeline falls back to the published text."""
    async def generate_stream(self, messages, model, temperature=0.7, max_tokens=None):
        return
        yield  # pragma: no cover


def test_team_list_is_complete_when_the_model_is_down(tmp_path):
    # live miss: the fallback text was cut to 6 lines, so three team members vanished
    from chat_memory import ChatMemoryStore
    from query_intelligence_engine import QueryIntelligenceEngine
    p = SemanticChatPipeline(provider=DownProvider(), engine=QueryIntelligenceEngine(enable_llm=False),
                             memory=ChatMemoryStore(tmp_path / "memory.db"))
    text, _ = chat(p, "down", "who is the ceo")
    for name in ["Akhil Reddy", "Saladi Chandra Balaji", "Ganesh Gandhi Vadalani", "Harish Nerati", "Aravind Reddy",
                 "Parvatha Mohan"]:
        assert name in text


def test_capped_lists_say_that_items_were_left_out():
    from semantic_chat_pipeline import _cap_bullets
    capped = _cap_bullets("Features:\n\n" + "\n".join(f"- point {i}" for i in range(8)) + "\n\nWant a demo?")
    assert "…and 3 more" in capped and capped.endswith("Want a demo?")
    assert "more" not in _cap_bullets("Features:\n- a\n- b")


def test_full_list_followup_repeats_the_capped_question_in_full(tmp_path):
    # the capped answer says "ask for the full list"; that follow-up used to return the whole product catalog
    from chat_memory import ChatMemoryStore
    from query_intelligence_engine import QueryIntelligenceEngine
    p = SemanticChatPipeline(provider=ListAllProvider(), engine=QueryIntelligenceEngine(enable_llm=False),
                             memory=ChatMemoryStore(tmp_path / "memory.db"))
    first, done1 = chat(p, "full", "what are the features of education os")
    assert "ask for the full list" in first
    full, done2 = chat(p, "full", "show me the full list")
    assert done2["metrics"]["operation"] == done1["metrics"]["operation"] == "get_capabilities"
    assert "ask for the full list" not in full and full.count("\n- ") > first.count("\n- ")
    # the invitation is spent: the same words later are an ordinary question again
    _, done3 = chat(p, "full", "show me the full list")
    assert done3["metrics"]["operation"] != "get_capabilities"


def test_full_list_followup_repeats_the_capped_question(tmp_path):
    # the shortened answer invites "ask for the full list"; that follow-up used to return the whole catalog
    from chat_memory import ChatMemoryStore
    from query_intelligence_engine import QueryIntelligenceEngine
    from semantic_chat_pipeline import MAX_ANSWER_BULLETS
    p = SemanticChatPipeline(provider=ListAllProvider(), engine=QueryIntelligenceEngine(enable_llm=False),
                             memory=ChatMemoryStore(tmp_path / "memory.db"))
    first, _ = chat(p, "full", "what are the features of education os")
    assert "ask for the full list" in first
    full, done = chat(p, "full", "show me the full list")
    assert done["metrics"]["operation"] == "get_capabilities"
    assert "ask for the full list" not in full
    assert sum(l.strip().startswith("- ") for l in full.splitlines()) > MAX_ANSWER_BULLETS
    # an unrelated question afterwards is not hijacked by the follow-up rule
    _, other = chat(p, "full", "show me all your services")
    assert other["metrics"]["operation"] == "list_services"
