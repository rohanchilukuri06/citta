"""
Meeting / contact-request agent.

One job: when a visitor wants to contact CittaAI or meet the team, collect their name, company /
organisation, email, phone, purpose and preferred time inside the chat, confirm the details, then email (1) the visitor a thank-you confirmation and
(2) the company a new-request notification. Every request is stored in the meeting_requests table whether or not
email delivery succeeds.

The dialogue is deterministic (regex extraction + validation, no LLM), so it can't invent or mangle contact details.
Its progress lives in ConversationState.meeting, so it survives across messages and server restarts.
"""

import html
import json
import logging
import re
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import config

logger = logging.getLogger(__name__)

FIELDS = ("name", "company", "email", "phone", "purpose", "timing")
LABELS = {"name": "Name", "company": "Company / organisation", "email": "Email", "phone": "Phone", "purpose": "Purpose",
          "timing": "Preferred time"}
MAX_LEN = {"name": 80, "company": 120, "email": 120, "phone": 20, "purpose": 500, "timing": 200}
NO_COMPANY = "Individual (no organisation)"

# ---------------------------------------------------------------------------------------------- intent detection
_TYPOS = {"meting": "meeting", "metting": "meeting", "meetng": "meeting", "meating": "meeting", "conact": "contact",
          "contct": "contact", "contat": "contact", "wanna": "want to", "wana": "want to", "u": "you", "ur": "your",
          "r": "are", "pls": "please", "plz": "please", "colaborate": "collaborate", "collabarate": "collaborate",
          "apointment": "appointment", "appoinment": "appointment", "talkto": "talk to", "cal": "call"}


def _normalise(text: str) -> str:
    return re.sub(r"[A-Za-z]+", lambda m: _TYPOS.get(m.group(0).lower(), m.group(0)), text).lower()


_MEETING_INTENT = re.compile(
    r"^\s*(please\s+)?(book|schedule|set ?up|arrange|fix|request|organi[sz]e)\b.{0,30}\b(meeting|call|demo|appointment|consultation)\b"
    r"|\b(book|schedule|request|arrange)\s+(a\s+|an\s+)?(demo|meeting|call|consultation|appointment)\b"
    r"|\b(i|we)\s*(?:'d|'m|'re| would| want| need| like| am| are| wish| will| plan)\b.{0,40}?"
    r"\b(meeting|meet|call|demo|appointment|consultation|talk to|speak to|speak with|talk with|connect with|contact|"
    r"get in touch|collaborat\w*|partner\w*|discuss)\b"
    r"|\b(can|could|would|will|please)\s+(you|someone|somebody|your team|anyone|the team)\b.{0,25}\b(call|contact|reach|email|get back to|ring)\s+(me|us)\b"
    r"|^\s*(please\s+)?(call|contact|reach|email|ring)\s+(me|us)\b"
    r"|\b(talk|speak|connect|meet)\s+(to|with)\s+(your|the|someone|somebody|a person|a human|an expert|cittaai|citta|you guys|sales)\b"
    r"|\binterested in (a\s+)?(partnership|collaboration|meeting|demo|call)\b"
    r"|\b(get in touch with (you|your team|cittaai|citta))\b",
    re.I,
)
# Plain information questions about contact details are answered from the knowledge base (with an offer to set up a meeting)
_CONTACT_INFO_QUESTION = re.compile(r"\b(what(?:'s| is)? (your|the|cittaai'?s?) (email|phone|number|address|contact)|"
                                    r"how (do|can|to) (i|we)?\s*(contact|reach)|contact (details|info)|where is your office)\b", re.I)
_YES = re.compile(r"^\s*(yes|yeah|yea|yep|yup|ya|sure|ok|okay|confirm(ed)?|go ahead|send( it)?|please do|please|do it|"
                  r"correct|right|sounds good|looks good|all good|perfect|y)\b[\s!.,]*(please|send it|go ahead|thanks?|thank you)?[\s!.]*$", re.I)
_CANCEL = re.compile(r"^\s*(no|nope|nah|cancel|stop|quit|exit|never ?mind|forget it|not now|leave it|no thanks?|"
                     r"don'?t send|do not send|cancel (it|this|that|the request|the meeting))\s*[.!]*\s*$", re.I)
_QUESTION = re.compile(r"\?\s*$|^\s*(what|which|who|how|why|where|does|do|is|are|can|could|tell me)\b", re.I)

# ----------------------------------------------------------------------------------------------- field extraction
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?<![\w@])(\+?\d[\d\s().-]{8,18}\d)(?!\w)")
_TIME_WORD = (r"today|tonight|tomorrow|tmrw|tmr|day after tomorrow|next week|this week|weekend|weekdays?|"
              r"mon(day)?|tue(s|sday)?|wed(nesday)?|thu(rs|rsday)?|fri(day)?|sat(urday)?|sun(day)?|"
              r"morning|afternoon|evening|noon|anytime|any time|asap|"
              r"\d{1,2}(:\d{2})?\s*(am|pm|a\.m\.|p\.m\.)|\d{1,2}:\d{2}|\d{1,2}(st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*|"
              r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}(st|nd|rd|th)?")
_TIME = re.compile(rf"\b(?:{_TIME_WORD})\b", re.I)
_TIME_SPAN = re.compile(rf"(?:\b(?:on|at|by|around|after|before|between|from|this|next|any)\s+)?\b(?:{_TIME_WORD})\b"
                        rf"(?:[\s,]*(?:at|around|after|before|between|from|to|and|or|-|by)?[\s,]*\b(?:{_TIME_WORD})\b)*", re.I)
_NAME_PREFIX = re.compile(r"^\s*(hi|hello|hey)?[\s,]*(my name is|my name's|name is|name:|i am|i'm|im|this is|it'?s|call me)\s+", re.I)
_NAME_IN_TEXT = re.compile(r"\b(?:my name is|my name's|name is|name:|this is)\s+([A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*){0,3})", re.I)
_NOT_A_NAME = {"hi", "hello", "hey", "yes", "no", "ok", "okay", "sure", "thanks", "thank", "you", "a", "an", "the", "not",
               "interested", "looking", "from", "with", "here", "fine", "good", "meeting", "call", "demo", "cittaai", "citta"}
# "I'm Priya from Acme Labs", "we are Bright Minds School": the name must start with a capital or digit
_COMPANY_IN_TEXT = re.compile(r"(?i:\b(?:i work (?:at|for|with)|i'?m from|i am from|we are|we're|from|representing|"
                              r"on behalf of|(?:company|organi[sz]ation|org)(?: name)? is))\s+"
                              r"((?:the\s+)?[A-Z0-9][\w&.'-]*(?:\s+(?:[A-Z0-9&][\w&.'-]*|of|and|for|de))*)")
_NO_COMPANY = re.compile(r"^\s*(none|no|nil|n/?a|na|-+|individual|myself|personal|self|self[- ]employed|freelancer?|"
                         r"just me|not applicable|no company|no organi[sz]ation|i'?m an individual|independent)\s*[.!]*\s*$", re.I)
_PURPOSE_IN_TEXT = re.compile(r"\b(?:about|regarding|re:|to discuss|discuss|for|on|related to|because)\s+(.{4,})", re.I)
_EDIT = re.compile(r"\b((?:company|organi[sz]ation|org)(?: name)?|name|purpose|reason|topic|agenda|time|timing|timings|slot|schedule|email|e-mail|mail|phone|number|mobile)\b"
                   r"\s*(?:is|to|:|=|should be|as)\s*(.+)$", re.I)
_EDIT_FIELD = {"company": "company", "organisation": "company", "organization": "company", "org": "company",
               "name": "name", "purpose": "purpose", "reason": "purpose", "topic": "purpose", "agenda": "purpose",
               "time": "timing", "timing": "timing", "timings": "timing", "slot": "timing", "schedule": "timing",
               "email": "email", "e-mail": "email", "mail": "email", "phone": "phone", "number": "phone", "mobile": "phone"}


def _clean(value: str, name: str) -> str:
    value = re.sub(r"[\x00-\x1f\x7f]+", " ", value)
    value = " ".join(value.split()).strip(" ,;:-")
    return value[:MAX_LEN[name]]


def find_email(text: str) -> Optional[str]:
    m = _EMAIL.search(text)
    return m.group(0).strip(".").lower() if m else None


def find_phone(text: str) -> Optional[str]:
    for m in _PHONE.finditer(_EMAIL.sub(" ", text)):
        digits = re.sub(r"\D", "", m.group(1))
        if 10 <= len(digits) <= 15:
            return ("+" if m.group(1).strip().startswith("+") else "") + digits
    return None


def find_timing(text: str) -> Optional[str]:
    spans = [m for m in _TIME_SPAN.finditer(text) if m.group(0).strip()]
    if not spans:
        return None
    return _clean(text[spans[0].start():spans[-1].end()], "timing")


def valid_name(text: str) -> Optional[str]:
    text = _NAME_PREFIX.sub("", text).strip(" .!,")
    text = re.split(r"[,;\n]| and | from ", text, maxsplit=1)[0].strip(" .!")
    words = text.split()
    if not (1 <= len(words) <= 5) or not re.fullmatch(r"[A-Za-z][A-Za-z .'-]{0,78}", text):
        return None
    if words[0].lower() in _NOT_A_NAME or all(w.lower() in _NOT_A_NAME for w in words):
        return None
    return _clean(" ".join(w if w[:1].isupper() else w.capitalize() for w in words), "name")


def find_company(text: str) -> Optional[str]:
    m = _COMPANY_IN_TEXT.search(text)
    if not m:
        return None
    value = re.sub(r"\s+(of|and|for|de)$", "", m.group(1).strip(" .,'-"))
    if not value or value.lower().startswith("citta") or value.lower() in ("you", "your team"):
        return None
    return _clean(value, "company")


def _strip_found(text: str) -> str:
    text = _EMAIL.sub(" ", text)
    text = _PHONE.sub(" ", text)
    return " ".join(text.split()).strip(" ,;.-")


# ----------------------------------------------------------------------------------------------------- storage
class MeetingRequestStore:
    def __init__(self, path: Optional[Path] = None):
        from chat_memory import DEFAULT_DB_PATH
        self.path = Path(path or getattr(config, "CHAT_MEMORY_DB_PATH", "") or DEFAULT_DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS meeting_requests (
                id TEXT PRIMARY KEY, session_id TEXT, created_at REAL, name TEXT, email TEXT, phone TEXT,
                purpose TEXT, timing TEXT, context TEXT, user_email_status TEXT, company_email_status TEXT,
                company TEXT)""")
            if "company" not in {r[1] for r in c.execute("PRAGMA table_info(meeting_requests)")}:
                c.execute("ALTER TABLE meeting_requests ADD COLUMN company TEXT")  # databases from before the field

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def add(self, session_id: str, details: Dict[str, str], context: Dict[str, Any]) -> str:
        rid = uuid.uuid4().hex[:10]
        with self._lock, self._conn() as c:
            c.execute("INSERT INTO meeting_requests (id, session_id, created_at, name, company, email, phone, purpose, "
                      "timing, context, user_email_status, company_email_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (rid, session_id, time.time(), details["name"], details.get("company") or NO_COMPANY, details["email"],
                       details["phone"], details["purpose"], details["timing"], json.dumps(context, ensure_ascii=False),
                       "pending", "pending"))
        return rid

    def set_status(self, rid: str, user_status: str, company_status: str) -> None:
        with self._lock, self._conn() as c:
            c.execute("UPDATE meeting_requests SET user_email_status=?, company_email_status=? WHERE id=?",
                      (user_status, company_status, rid))

    def recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._conn() as c:
            c.row_factory = sqlite3.Row
            rows = c.execute("SELECT * FROM meeting_requests ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


# ------------------------------------------------------------------------------------------------------- emails
def _brand_html(title: str, body: str) -> str:
    return (f"<div style=\"font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:auto;color:#1f2937\">"
            f"<h2 style=\"color:#4f46e5;margin-bottom:4px\">{html.escape(title)}</h2>{body}"
            f"<p style=\"color:#6b7280;font-size:12px;margin-top:24px\">CittaAI · cittaai.com</p></div>")


def _details_table(d: Dict[str, str]) -> str:
    rows = "".join(f"<tr><td style=\"padding:6px 12px 6px 0;color:#6b7280\">{LABELS[k]}</td>"
                   f"<td style=\"padding:6px 0\"><b>{html.escape(d.get(k) or NO_COMPANY)}</b></td></tr>" for k in FIELDS)
    return f"<table style=\"border-collapse:collapse\">{rows}</table>"


def user_email(d: Dict[str, str], company_contact: str) -> Dict[str, str]:
    first = d["name"].split()[0]
    text = (f"Hi {first},\n\nThank you for reaching out to CittaAI! We've received your request and our team will "
            f"contact you soon, around your preferred time ({d['timing']}).\n\n"
            + "\n".join(f"{LABELS[k]}: {d.get(k) or NO_COMPANY}" for k in FIELDS) +
            f"\n\nIf anything changes, just reply to this email{(' or contact us at ' + company_contact) if company_contact else ''}."
            "\n\nWarm regards,\nTeam CittaAI")
    body = (f"<p>Hi {html.escape(first)},</p><p>Thank you for reaching out to <b>CittaAI</b>! We've received your request "
            f"and our team will contact you soon, around your preferred time "
            f"(<b>{html.escape(d['timing'])}</b>).</p><p>Here's what you shared with us:</p>{_details_table(d)}"
            f"<p>If anything changes, just reply to this email"
            f"{(' or contact us at ' + html.escape(company_contact)) if company_contact else ''}.</p>"
            "<p>Warm regards,<br>Team CittaAI</p>")
    return {"subject": "Thank you for contacting CittaAI — we'll be in touch soon", "text": text,
            "html": _brand_html("Thanks for reaching out!", body)}


def company_email(d: Dict[str, str], context: Dict[str, Any], rid: str) -> Dict[str, str]:
    topics = ", ".join(context.get("discussed") or []) or "—"
    facts = context.get("visitor_facts") or []
    company = d.get("company") or NO_COMPANY
    org = "" if company == NO_COMPANY else company
    who = f"{d['name']} from {org}" if org else d["name"]
    text = (f"{who} would like to meet CittaAI.\n\nPurpose: {d['purpose']}\nPreferred time: {d['timing']}\n\n"
            f"Name: {d['name']}\nCompany / organisation: {company}\nEmail: {d['email']}\nPhone: {d['phone']}\n\n"
            f"Offerings discussed in the chat: {topics}\n"
            + (("What they told the assistant:\n" + "\n".join(f"- {f}" for f in facts) + "\n") if facts else "")
            + f"\nRequest ID: {rid}\nReply to this email to respond to {d['name']} directly.")
    body = (f"<p><b>{html.escape(d['name'])}</b>{(' from <b>' + html.escape(org) + '</b>') if org else ''} "
            "would like to meet CittaAI regarding:</p>"
            f"<blockquote style=\"border-left:3px solid #4f46e5;margin:0;padding:4px 12px\">{html.escape(d['purpose'])}</blockquote>"
            f"<p></p>{_details_table(d)}"
            f"<p><b>Offerings discussed in the chat:</b> {html.escape(topics)}</p>"
            + ("<p><b>What they told the assistant:</b></p><ul>" + "".join(f"<li>{html.escape(f)}</li>" for f in facts) + "</ul>" if facts else "")
            + f"<p style=\"color:#6b7280\">Request ID {rid} · Reply to this email to respond to {html.escape(d['name'])} directly.</p>")
    subject = f"New meeting request: {d['name']}{f' ({org})' if org else ''} — {d['purpose'][:60]}{'…' if len(d['purpose']) > 60 else ''}"
    return {"subject": subject, "text": text, "html": _brand_html("New meeting request from the website chat", body)}


# -------------------------------------------------------------------------------------------------------- agent
@dataclass
class AgentReply:
    text: Optional[str] = None                       # the agent's answer (None: let the knowledge pipeline answer)
    reminder: Optional[str] = None                   # appended after a knowledge answer given mid-collection
    suggestions: List[str] = field(default_factory=list)


class MeetingAgent:
    def __init__(self, store: Optional[MeetingRequestStore] = None, sender: Any = None):
        self.store = store or MeetingRequestStore()
        if sender is None:
            import email_sender
            sender = email_sender
        self.sender = sender

    # ---- entry point
    async def handle(self, message: str, state: Any, session_id: str, contact_line: str = "",
                     title_of: Any = None) -> Optional[AgentReply]:
        m = state.meeting or {}
        norm = _normalise(message)
        if m.get("stage") in ("collecting", "confirming"):
            return await self._continue(message, norm, state, session_id, contact_line, title_of)
        if m.get("offered") and _YES.match(norm):
            return self._start(message, state, contact_line, from_offer=True)
        if m.get("offered"):
            state.meeting = {k: v for k, v in m.items() if k != "offered"}
        if _MEETING_INTENT.search(norm) and not _CONTACT_INFO_QUESTION.search(norm):
            return self._start(message, state, contact_line)
        return None

    def offer(self, state: Any) -> str:
        """Called after contact details were given from the knowledge base."""
        state.meeting = {**(state.meeting or {}), "offered": True}
        return "Would you like me to arrange a meeting or have the CittaAI team contact you? Just say **yes** and I'll take your details."

    # ---- dialogue
    def _start(self, message: str, state: Any, contact_line: str, from_offer: bool = False) -> AgentReply:
        sent = (state.meeting or {}).get("sent", 0)
        if sent >= config.MEETING_REQUESTS_PER_SESSION:
            state.meeting = {"sent": sent}
            return AgentReply(f"You've already sent {sent} requests in this conversation — the CittaAI team will be in touch. {contact_line}".strip())
        details: Dict[str, str] = {}
        if not from_offer:
            self._extract_into(details, message, awaiting=None, trigger=True)
        state.meeting = {"stage": "collecting", "details": details, "sent": sent}
        opener = "I'd be happy to set that up! " if not from_offer else "Great! "
        opener += "I'll take a few details and pass them to the CittaAI team — you'll also get a confirmation email."
        return self._next_prompt(state, opener)

    async def _continue(self, message: str, norm: str, state: Any, session_id: str, contact_line: str,
                        title_of: Any = None) -> Optional[AgentReply]:
        m = state.meeting
        details: Dict[str, str] = m.setdefault("details", {})
        if _CANCEL.match(norm):
            state.meeting = {"sent": m.get("sent", 0)}
            return AgentReply("No problem — I've cancelled the request and nothing was sent. "
                              "Let me know if you'd like to set it up later, or ask me anything about CittaAI.")
        if m["stage"] == "confirming":
            if _YES.match(norm):
                return await self._submit(state, session_id, contact_line, title_of)
            if self._apply_edit(details, message):
                return self._next_prompt(state, "Updated!")
            if _QUESTION.search(message):
                return AgentReply(reminder="_(Your meeting request is ready — reply **yes** to send it, or tell me what to change.)_")
            return AgentReply("Just tell me what to change — for example *\"change the time to Friday 11am\"* or "
                              "*\"my email is name@example.com\"* — or reply **yes** to send the request.",
                              suggestions=["Yes, send it", "Cancel"])

        awaiting = self._missing(details)[0]
        before = dict(details)
        error = self._extract_into(details, message, awaiting=awaiting)
        if details == before:
            if _QUESTION.search(message) and awaiting != "purpose":
                # A question about CittaAI mid-collection: answer it, then come back to the form
                return AgentReply(reminder=f"_(To finish your meeting request I still need your {LABELS[awaiting].lower()} — "
                                           f"or say **cancel** to stop.)_")
            return self._next_prompt(state, error or None)
        return self._next_prompt(state, error or None)

    def _missing(self, details: Dict[str, str]) -> List[str]:
        return [f for f in FIELDS if not details.get(f)]

    def _next_prompt(self, state: Any, lead: Optional[str]) -> AgentReply:
        details = state.meeting["details"]
        missing = self._missing(details)
        prefix = (lead + "\n\n") if lead else ""
        if not missing:
            state.meeting["stage"] = "confirming"
            summary = "\n".join(f"- **{LABELS[k]}:** {details[k]}" for k in FIELDS)
            return AgentReply(f"{prefix}Here's your request:\n\n{summary}\n\nShall I send it? Reply **yes** to confirm, "
                              "or tell me what to change.", suggestions=["Yes, send it", "Cancel"])
        state.meeting["stage"] = "collecting"
        ask = {
            "name": "May I have your **name**?",
            "company": "Which **company or organisation** are you with? (If you're reaching out personally, just say *individual*.)",
            "email": "What's your **email address**? I'll send the confirmation there.",
            "phone": "What's the best **phone number** to reach you on?",
            "purpose": "What would you like to discuss? (e.g. a demo of a product, a project, a partnership)",
            "timing": "When would suit you for the meeting or call? (e.g. *Tomorrow 3–5pm* or *Weekdays after 11am*; "
                      "the team works Mon–Fri, 9am–6pm IST)",
        }[missing[0]]
        noted = ""
        if details.get("name") and not lead and not state.meeting.get("thanked"):
            noted, state.meeting["thanked"] = f"Thanks, {details['name'].split()[0]}! ", True
        return AgentReply(f"{prefix}{noted}{ask}", suggestions=["Cancel"])

    def _extract_into(self, details: Dict[str, str], message: str, awaiting: Optional[str], trigger: bool = False) -> Optional[str]:
        """Fill whatever the message contains; returns a short validation message if the awaited field was invalid."""
        error = None
        email = find_email(message)
        if email:
            details["email"] = _clean(email, "email")
        elif awaiting == "email":
            error = "That doesn't look like a valid email address — could you check it? (e.g. *name@example.com*)"
        phone = find_phone(message)
        if phone:
            details["phone"] = phone
        elif awaiting == "phone":
            digits = re.sub(r"\D", "", message)
            if digits:
                error = "That phone number looks incomplete — please include the full number (10–15 digits, with country code if outside India)."
            elif not error:
                error = "I need a phone number to pass to the team — what's the best number to reach you on?"
        rest = _strip_found(message)

        timing = find_timing(rest) if (trigger or awaiting in ("timing", "name", "email", "phone")) else None
        if awaiting == "timing" and not timing and rest and not _QUESTION.search(rest):
            timing = _clean(rest, "timing")  # "whenever suits the team" is a valid answer too
        if timing:
            details["timing"] = timing
            rest = rest.replace(timing, " ").strip(" ,;.-") if timing in rest else rest

        if trigger or awaiting == "name":
            company = find_company(rest)
            if company:
                details["company"] = company

        if trigger:
            named = _NAME_IN_TEXT.search(rest)
            if named and valid_name(named.group(1)):
                details["name"] = valid_name(named.group(1))
            purpose = _PURPOSE_IN_TEXT.search(rest)
            if purpose and len(purpose.group(1).split()) >= 1:
                details["purpose"] = _clean(purpose.group(1), "purpose")
            elif re.search(r"collaborat|partner", rest, re.I):
                details["purpose"] = "Collaboration / partnership with CittaAI"
            elif re.search(r"\bdemo\b", rest, re.I):
                details["purpose"] = "Product demo"
            return None

        if awaiting == "name" and rest:
            name = valid_name(rest)
            if name:
                details["name"] = name
            elif not email and not phone and not timing:
                error = "Sorry, I didn't catch your name — could you type just your name? (e.g. *Priya Sharma*)"
        elif awaiting == "company" and rest:
            if _NO_COMPANY.match(rest):
                details["company"] = NO_COMPANY
            elif not _QUESTION.search(rest):
                details["company"] = find_company(rest) or _clean(rest, "company")
        elif awaiting == "purpose" and rest and len(rest) >= 2:
            details["purpose"] = _clean(rest, "purpose")
        return error

    def _apply_edit(self, details: Dict[str, str], message: str) -> bool:
        before = dict(details)
        m = _EDIT.search(message)
        if m:
            target, value = _EDIT_FIELD[m.group(1).lower().split()[0]], m.group(2)
            if target == "email":
                value = find_email(value) or ""
            elif target == "phone":
                value = find_phone(value) or ""
            elif target == "name":
                value = valid_name(value) or ""
            elif target == "company" and _NO_COMPANY.match(value):
                value = NO_COMPANY
            if value:
                details[target] = _clean(value, target)
        else:
            email, phone = find_email(message), find_phone(message)
            if email:
                details["email"] = email
            if phone:
                details["phone"] = phone
        return details != before

    async def deliver(self, session_id: str, d: Dict[str, str], context: Dict[str, Any], contact_line: str = ""):
        """Store the request, then email the company and the visitor. Returns (request id, {"user", "company"} status).
        Shared by the chat agent and the website's contact form."""
        rid = self.store.add(session_id, d, context)
        company_to = config.COMPANY_LEAD_EMAIL
        if not self.sender.is_configured() or not company_to:
            self.store.set_status(rid, "not_configured", "not_configured")
            logger.warning(json.dumps({"event": "meeting_request_saved_no_email", "request_id": rid,
                                       "reason": "SMTP or COMPANY_LEAD_EMAIL not configured"}))
            return rid, {"user": "not_configured", "company": "not_configured"}
        company_contact = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", contact_line or "")
        user_msg = user_email(d, company_contact.group(0) if company_contact else "")
        comp_msg = company_email(d, context, rid)
        statuses = {}
        for key, to, msg, reply_to in (("company", company_to, comp_msg, d["email"]),
                                       ("user", d["email"], user_msg, company_to)):
            try:
                await self.sender.send_email(to, msg["subject"], msg["text"], msg["html"], reply_to=reply_to)
                statuses[key] = "sent"
            except Exception as e:
                statuses[key] = f"failed: {type(e).__name__}"
                logger.error(json.dumps({"event": "meeting_email_failed", "request_id": rid, "to": key,
                                         "error": f"{type(e).__name__}: {e}"[:200]}))
        self.store.set_status(rid, statuses["user"], statuses["company"])
        return rid, statuses

    async def _submit(self, state: Any, session_id: str, contact_line: str, title_of: Any = None) -> AgentReply:
        d = dict(state.meeting["details"])
        context = {"discussed": [(title_of(e) if title_of else e) for e in (state.discussed or [])][-6:],
                   "visitor_facts": list(state.visitor_facts or [])[-5:]}
        sent = state.meeting.get("sent", 0) + 1
        rid, statuses = await self.deliver(session_id, d, context, contact_line)
        state.meeting = {"sent": sent, "last_request": rid}
        first = d["name"].split()[0]
        if statuses["company"] == "not_configured":
            return AgentReply(f"Thank you, {first}! Your request has been recorded (reference **{rid}**), "
                              "but I couldn't send the confirmation emails right now. "
                              f"To be sure the team gets it, you can also reach them directly. {contact_line}".strip())
        if statuses["company"] == "sent" and statuses["user"] == "sent":
            return AgentReply(f"All done, {first}! ✅ I've sent your request to the CittaAI team and a confirmation email to "
                              f"**{d['email']}**. The team will contact you around **{d['timing']}**. "
                              "Is there anything else you'd like to know in the meantime?")
        if statuses["company"] == "sent":
            return AgentReply(f"Thanks, {first}! Your request has reached the CittaAI team and they'll contact you around "
                              f"**{d['timing']}**. I couldn't deliver the confirmation email to **{d['email']}** — "
                              "please double-check that address.")
        return AgentReply(f"Thanks, {first}. I've recorded your request (reference **{rid}**), but the email to the team didn't "
                          f"go through. To be safe, please also contact them directly. {contact_line}".strip())


_AGENT: Optional[MeetingAgent] = None


def get_meeting_agent() -> MeetingAgent:
    global _AGENT
    if _AGENT is None:
        _AGENT = MeetingAgent()
    return _AGENT
