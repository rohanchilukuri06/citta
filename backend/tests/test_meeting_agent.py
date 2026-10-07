"""
Meeting agent: intent detection, step-by-step collection with validation, all-in-one messages, edits, cancel,
questions mid-collection, and the two emails (visitor + company) — with a fake SMTP sender and a temp database.
"""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

import config
from meeting_agent import MeetingAgent, MeetingRequestStore
from semantic_chat_pipeline import ConversationState

CONTACT = "For details, please contact the CittaAI team at info@cittaai.com or +91 9392655040."


class FakeSender:
    def __init__(self, configured=True, fail_for=()):
        self.configured, self.fail_for, self.sent = configured, set(fail_for), []

    def is_configured(self):
        return self.configured

    async def send_email(self, to, subject, text, html=None, reply_to=None):
        if to in self.fail_for:
            raise RuntimeError("smtp down")
        self.sent.append({"to": to, "subject": subject, "text": text, "html": html, "reply_to": reply_to})
        return "<id>"


@pytest.fixture
def agent(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "COMPANY_LEAD_EMAIL", "company@example.com")
    return MeetingAgent(store=MeetingRequestStore(tmp_path / "m.db"), sender=FakeSender())


def say(agent, state, msg):
    reply = asyncio.run(agent.handle(msg, state, "s1", CONTACT, title_of=lambda e: e.replace("_", " ").title()))
    return reply


def test_ordinary_questions_are_not_taken_over(agent):
    state = ConversationState()
    for q in ["tell me about education os", "what is your email", "does whatsapp help schedule meetings with customers"]:
        assert say(agent, state, q) is None


def test_step_by_step_collection_and_both_emails(agent):
    state = ConversationState(discussed=["education_os"], visitor_facts=["We are an engineering college"])
    assert "name" in say(agent, state, "I want to have a meeting with citta ai").text.lower()
    assert "company or organisation" in say(agent, state, "my name is ravi kumar").text
    assert "email" in say(agent, state, "Sunrise Engineering College").text.lower()
    assert "valid email" in say(agent, state, "ravi at gmail").text            # invalid -> asked again
    assert "phone" in say(agent, state, "ravi.kumar@gmail.com").text.lower()
    assert "incomplete" in say(agent, state, "98765").text                     # too short -> asked again
    assert "discuss" in say(agent, state, "+91 98765 43210").text
    assert "when" in say(agent, state, "Demo of Education OS for our college").text.lower()
    summary = say(agent, state, "tomorrow between 3pm and 5pm").text
    assert "Ravi Kumar" in summary and "Sunrise Engineering College" in summary and "+919876543210" in summary and "tomorrow between 3pm and 5pm" in summary
    done = say(agent, state, "yes").text
    assert "confirmation email" in done and "ravi.kumar@gmail.com" in done

    sent = agent.sender.sent
    assert [m["to"] for m in sent] == ["company@example.com", "ravi.kumar@gmail.com"]
    company, user = sent
    assert "Ravi Kumar (Sunrise Engineering College)" in company["subject"] and "Demo of Education OS" in company["text"]
    assert company["reply_to"] == "ravi.kumar@gmail.com" and "Education Os" in company["text"]
    assert "Thank you for reaching out to CittaAI" in user["text"] and "tomorrow between 3pm and 5pm" in user["text"]
    row = agent.store.recent()[0]
    assert row["name"] == "Ravi Kumar" and row["company"] == "Sunrise Engineering College" and row["user_email_status"] == "sent" and row["company_email_status"] == "sent"
    assert state.meeting.get("stage") is None


def test_everything_in_one_message_then_edit(agent):
    state = ConversationState()
    reply = say(agent, state, "can someone call me? my name is Priya Sharma from Acme Labs, priya@x.in, 9123456780, "
                              "about a partnership, friday 11am")
    assert "Shall I send it" in reply.text and "Priya Sharma" in reply.text and "Acme Labs" in reply.text
    edited = say(agent, state, "change the time to monday 4pm").text
    assert "monday 4pm" in edited
    assert "Priya" in say(agent, state, "yes send it").text
    assert agent.store.recent()[0]["timing"] == "monday 4pm"


def test_cancel_sends_nothing(agent):
    state = ConversationState()
    say(agent, state, "book a demo")
    assert "cancelled" in say(agent, state, "cancel").text
    assert agent.sender.sent == [] and agent.store.recent() == []


def test_question_mid_collection_is_answered_by_the_bot(agent):
    state = ConversationState()
    say(agent, state, "i wanna talk to ur team")
    reply = say(agent, state, "what is education os?")
    assert reply.text is None and "name" in reply.reminder.lower()   # pipeline answers; agent appends a reminder
    assert state.meeting["stage"] == "collecting"


def test_offer_after_contact_details_then_yes(agent):
    state = ConversationState()
    agent.offer(state)
    assert "name" in say(agent, state, "yes").text.lower()


def test_without_smtp_the_request_is_saved_and_the_visitor_is_told(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "COMPANY_LEAD_EMAIL", "company@example.com")
    agent = MeetingAgent(store=MeetingRequestStore(tmp_path / "m.db"), sender=FakeSender(configured=False))
    state = ConversationState()
    say(agent, state, "call me, my name is Ann Lee from Lee Traders, ann@x.com, 9123456780, about pricing, tomorrow 10am")
    reply = say(agent, state, "yes").text
    assert "couldn't send" in reply and "info@cittaai.com" in reply
    assert agent.store.recent()[0]["user_email_status"] == "not_configured"


def test_failed_user_email_is_reported_honestly(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "COMPANY_LEAD_EMAIL", "company@example.com")
    agent = MeetingAgent(store=MeetingRequestStore(tmp_path / "m.db"), sender=FakeSender(fail_for={"bad@x.com"}))
    state = ConversationState()
    say(agent, state, "call me, my name is Ann Lee from Lee Traders, bad@x.com, 9123456780, about pricing, tomorrow 10am")
    assert "couldn't deliver the confirmation" in say(agent, state, "yes").text


def test_header_injection_is_neutralised(agent):
    state = ConversationState()
    say(agent, state, "book a meeting")
    say(agent, state, "Eve\r\nBcc: victim@example.com")
    assert "\n" not in (state.meeting["details"].get("name") or "")


def test_contact_form_endpoint_stores_and_emails(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import meeting_agent
    import server
    monkeypatch.setattr(config, "COMPANY_LEAD_EMAIL", "company@example.com")
    fake = FakeSender()
    monkeypatch.setattr(meeting_agent, "_AGENT", MeetingAgent(store=MeetingRequestStore(tmp_path / "m.db"), sender=fake))
    client = TestClient(server.app)
    ok = client.post("/api/contact", json={"name": "priya sharma", "email": "priya@x.in", "phone": "+91 91234 56780",
                                           "company": "Acme", "inquiry": "Product Demo", "message": "Demo of Pharma OS"})
    assert ok.status_code == 200 and ok.json()["company_email"] == "sent" and ok.json()["visitor_email"] == "sent"
    assert [m["to"] for m in fake.sent] == ["company@example.com", "priya@x.in"]
    assert "Product Demo: Demo of Pharma OS" in fake.sent[0]["text"] and "Company / organisation: Acme" in fake.sent[0]["text"]
    bad = client.post("/api/contact", json={"name": "x", "email": "not-an-email", "phone": "123456789",
                                            "inquiry": "General Inquiry", "message": "hi"})
    assert bad.status_code == 422


def test_individual_without_company_and_editing_company(agent):
    state = ConversationState()
    say(agent, state, "i want a meeting")
    assert "company or organisation" in say(agent, state, "Meera Iyer").text
    assert "email" in say(agent, state, "individual").text.lower()
    say(agent, state, "meera@x.in"); say(agent, state, "9123456780"); say(agent, state, "a website project")
    assert "Individual (no organisation)" in say(agent, state, "monday 10am").text
    edited = say(agent, state, "change company name to Iyer Designs").text
    assert "Iyer Designs" in edited and "Meera Iyer" in edited      # the person's name is untouched
    say(agent, state, "yes")
    assert agent.store.recent()[0]["company"] == "Iyer Designs"
    assert "Meera Iyer (Iyer Designs)" in agent.sender.sent[0]["subject"]


def test_company_given_with_name(agent):
    state = ConversationState()
    say(agent, state, "book a demo")
    assert "email" in say(agent, state, "I'm Rahul from Bright Minds School").text.lower()   # company step skipped
    d = state.meeting["details"]
    assert d["name"] == "Rahul" and d["company"] == "Bright Minds School"


def test_question_while_asked_for_company_gets_answered(agent):
    state = ConversationState()
    say(agent, state, "book a meeting"); say(agent, state, "Ravi")
    reply = say(agent, state, "what is pharma os?")
    assert reply.text is None and "company" in reply.reminder.lower()


def test_old_database_gets_company_column(tmp_path):
    import sqlite3
    db = tmp_path / "old.db"
    with sqlite3.connect(db) as c:
        c.execute("""CREATE TABLE meeting_requests (id TEXT PRIMARY KEY, session_id TEXT, created_at REAL, name TEXT,
                     email TEXT, phone TEXT, purpose TEXT, timing TEXT, context TEXT, user_email_status TEXT,
                     company_email_status TEXT)""")
    store = MeetingRequestStore(db)
    store.add("s", {"name": "A", "email": "a@x.in", "phone": "9123456780", "purpose": "p", "timing": "t"}, {})
    assert store.recent()[0]["company"] == "Individual (no organisation)"
