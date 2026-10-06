"""
Unified production chat pipeline for /api/chat.

    message
      -> turn understanding: small talk | questions about the conversation | rewrite of the last answer | knowledge
      -> knowledge: split compound messages into parts; for each part one SemanticDecision
         (entity / intent / aspect / scope) -> KnowledgeToolRouter -> section-level evidence
      -> one LLM answer grounded only in that evidence (+ conversation memory), validated
      -> SSE chunks

`decide()` is the single decision entry point for one question. The semantic benchmark calls the same
function, so benchmark results describe what production does (tests/test_production_parity.py).
Conversation memory persists in SQLite (chat_memory.py).
"""

import asyncio
import copy
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field, fields
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import config
from knowledge_operation_executor import Evidence, SECTION_LABELS, get_operation_executor
from knowledge_registry import get_registry
from knowledge_tool_router import KnowledgeToolRouter, OperationRoutePlan, TYPE_OVERVIEW_OPS

logger = logging.getLogger(__name__)

DETERMINISTIC_OPS = {
    "list_products", "list_solutions", "list_services", "list_catalog", "get_contact",
    "get_leadership", "get_recognition", "list_case_studies", "get_case_study",
}
ENTITY_SECTION_OPS = {
    "get_product", "get_solution", "get_service", "get_company_info", "get_capabilities", "get_benefits",
    "get_target_users", "get_workflow", "get_faq", "get_pricing",
}
OOD_TEXT = (
    "I can only help with CittaAI — our products, solutions, services, and company information. "
    "Is there something about CittaAI I can help you with?"
)
MAX_PARTS = 6            # questions answered from one message
MAX_EVIDENCE_ITEMS = 10  # per section, most relevant to the question first

# ---------------------------------------------------------------- turn understanding
_GREETING = re.compile(r"^\s*(hi+|hello+|hey+|hiya|namaste|hola|greetings|good (morning|afternoon|evening|day))\b[\s,!.]*(there|team|citta\s*ai|cittaai|citta|everyone)?[\s!.?]*$", re.I)
_THANKS = re.compile(r"^\s*(thanks|thank you|thank u|thx|ty|great|awesome|cool|nice|perfect|ok(ay)?|got it|understood|that helps|helpful)\b[\w\s,!.']{0,30}$", re.I)
_BYE = re.compile(r"^\s*(bye|goodbye|see you|see ya|that'?s all|talk later|cya)\b[\s!.]*$", re.I)
_IDENTITY = re.compile(r"^\s*(who are you|what are you|are you (a |an )?(bot|robot|ai|human|real person)|what can you (do|help( me)? with)|how can you help( me)?|what do you do)\s*\??\s*$", re.I)
_META = re.compile(r"\b(what (did|have) i (ask|asked|say|said|tell|told)( you)?|what have we (discussed|talked about|covered)|"
                   r"(summari[sz]e|recap) (our|this|the) (conversation|chat|discussion)|what was my (first|last|previous|earlier) question|"
                   r"remind me what (i|we)|what do you (know|remember) about (me|us|my|our))\b", re.I)
_REWRITE = re.compile(r"\b(explain (it|that|this)( more)? (simply|simpler|in simple(r)? terms|like i'?m (5|five))|simplif(y|ied)|in simple(r)? (terms|words)|"
                      r"make it (shorter|simpler|brief|briefer|longer|more detailed)|shorter( please)?|in short|tl;?dr|summari[sz]e (it|that|this)|"
                      r"(give me )?more details?|elaborate|expand on (that|it|this)|go deeper|in (bullet points|bullets|a table|points)|as a table|eli5|"
                      r"explain (that|it|this) again|rephrase|say that differently)\b", re.I)
# Questions about CittaAI itself ("how many employees do you have?") are in scope even when unanswerable
_COMPANY_QUESTION = re.compile(r"\b(citta\s*ai|cittaai|citta|your (company|team|firm|founders?|employees|staff|office|revenue|funding|investors|clients|customers)|"
                               r"you guys|do you (have|employ)|(ceo|cfo|cto|coo|cmo|founder|employees|headcount|revenue|funding|investors)\b)", re.I)
_PART_CUE = re.compile(r"^(what|who|whom|how|where|when|why|which|can|could|do|does|did|is|are|will|would|tell|give|show|list|explain|describe|share|i'?d like|please|also)\b", re.I)


def split_questions(message: str) -> List[str]:
    """Split a message into independent questions ("What is X and who is the CEO? Also, pricing?")."""
    text = re.sub(r"\s+", " ", message).strip()
    chunks = re.split(r"(?<=[?!])\s+|;\s+|\.\s+(?=[A-Z])|\s+(?:and also|also,?|plus|additionally),?\s+(?=\w)|\n+", text)
    parts: List[str] = []
    for chunk in chunks:
        chunk = chunk.strip(" ,.")
        if not chunk:
            continue
        # "What is Education OS and how does it work" -> two questions; "Compare Education and Pharma" stays one
        pieces = re.split(r",?\s+and\s+(?=(?:what|who|how|where|when|why|which|can|could|do|does|is|are|tell|give|show|list|explain)\b)", chunk, flags=re.I)
        parts.extend(re.sub(r"^(also|and|plus|additionally)\b[,\s]*", "", p.strip(" ,."), flags=re.I) for p in pieces if p.strip(" ,."))
    # Statements ("I run a university.") are context for the question they introduce, not questions themselves
    # Only explicit questions / requests stand alone; need statements carry into the question that follows them
    is_request = lambda p: p.rstrip().endswith("?") or bool(_PART_CUE.match(p))
    merged: List[str] = []
    carry = ""
    for p in parts:
        if not is_request(p) and len(parts) > 1:
            carry = f"{carry} {p}.".strip()
            continue
        merged.append(f"{carry} {p}".strip() if carry else p)
        carry = ""
    if carry:
        if merged:
            merged[-1] = f"{merged[-1]} {carry}"
        else:
            merged.append(carry)
    return merged[:MAX_PARTS] or [message]


@dataclass
class ConversationState:
    """The one conversation state the pipeline reads and writes (persisted by chat_memory.ChatMemoryStore)."""
    active_entity: Optional[str] = None
    active_entities: List[str] = field(default_factory=list)
    active_aspect: Optional[str] = None
    active_scope: Optional[str] = None
    recent_turns: List[Dict[str, str]] = field(default_factory=list)
    pending_clarification: Optional[Dict[str, Any]] = None
    turn_count: int = 0
    discussed: List[str] = field(default_factory=list)          # offerings talked about, oldest first
    visitor_facts: List[str] = field(default_factory=list)      # what the visitor said about themselves
    last_evidence: List[Dict[str, Any]] = field(default_factory=list)
    last_question: str = ""
    meeting: Dict[str, Any] = field(default_factory=dict)       # meeting-request agent progress

    @property
    def active_entity_confidence(self) -> float:  # context protocol read by QueryIntelligenceEngine
        return 0.90

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in (data or {}).items() if k in names})


class SemanticPipelineError(RuntimeError):
    pass


_PRICE_QUESTION = re.compile(r"\b(price|prices|pricing|cost|costs|costing|charges?|fees?|quote|budget|rupees|inr|usd|dollars?|"
                             r"how much|expensive|cheap|affordable)\b|[$₹]", re.I)
_ARITHMETIC = re.compile(r"^\s*(?:what(?:'s| is)|whats|calculate|solve|compute)?\s*[\d.,\s]+(?:[-+*/x×÷^%]\s*[\d.,\s]+)+[=?\s]*$", re.I)
# Chat shorthand, normalised only to recognise memory/rewrite requests and visitor facts ("wat did i tell u")
_SHORTHAND = {"wat": "what", "wht": "what", "u": "you", "r": "are", "ur": "your", "abt": "about", "pls": "please",
              "plz": "please", "busines": "business", "bussiness": "business", "buisness": "business", "compny": "company",
              "colege": "college", "collage": "college", "studnets": "students", "sellin": "selling"}


def _normalise_shorthand(text: str) -> str:
    return re.sub(r"[A-Za-z]+", lambda m: _SHORTHAND.get(m.group(0).lower(), m.group(0)), text)


_AUDIENCE_ASK = re.compile(r"\b(who|whom|for which|suitable|target|ideal for|meant for|designed for|audience|users?)\b", re.I)

MAX_RENDERED_ITEMS = 6
MAX_BULLET_WORDS = 22
MAX_ANSWER_BULLETS = 5
_DETAIL_REQUEST = re.compile(r"\b(all|every|full|complete|detail|detailed|details|in depth|in-depth|everything|elaborate|list)\b", re.I)
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")


def _cap_bullets(text: str, limit: int = MAX_ANSWER_BULLETS) -> str:
    """Keep answers short: at most `limit` items per bullet list (the model doesn't always respect the prompt)."""
    out, run = [], 0
    for line in text.split("\n"):
        if _BULLET.match(line):
            run += 1
            if run > limit:
                continue
            words = line.split()
            if len(words) > MAX_BULLET_WORDS:
                # Keep the bullet's lead clause: cut at the last comma/semicolon inside the word budget
                cut = " ".join(words[:MAX_BULLET_WORDS])
                at = max(cut.rfind(","), cut.rfind(";"))
                line = (cut[:at] if at > len(cut) // 2 else cut).rstrip(" ,;:—-") + "…"
        elif line.strip():
            run = 0
        out.append(line)
    return "\n".join(out)


def _short(item: str, limit: int = 180) -> str:
    """First sentence of a registry item ('Branding & Strategy — AI Brand Architecture …'), capped for display."""
    item = " ".join(str(item).split()).split(" — Features:")[0]
    faq = re.match(r"^(.+?\?)\s+—\s+(.+)$", item)
    if faq:  # "What is CittaAI's email address? — info@cittaai.com": the answer is the part worth keeping
        answer = re.split(r"(?<=[.!?])\s", faq.group(2), maxsplit=1)[0]
        both = f"{faq.group(1)} {answer}"
        return both if len(both) <= limit else answer[:limit]
    head = re.split(r"(?<=[.!?])\s", item, maxsplit=1)[0]
    return head if len(head) <= limit else head[:limit].rsplit(" ", 1)[0] + "…"


@dataclass
class PartResult:
    question: str
    decision: Any
    plans: List[Any]
    kind: str                     # evidence | clarify | ood | unavailable
    evidences: List[Evidence] = field(default_factory=list)
    note: str = ""                # fixed text for clarify / ood / unavailable parts


class SemanticChatPipeline:
    def __init__(self, provider: Any = None, engine: Any = None, router: Optional[KnowledgeToolRouter] = None,
                 memory: Any = None):
        from query_intelligence_engine import get_query_intelligence_engine
        self.provider = provider
        self.engine = engine or get_query_intelligence_engine()
        self.router = router or KnowledgeToolRouter()
        self.executor = get_operation_executor()
        self.registry = get_registry()
        self.states: Dict[str, ConversationState] = {}
        self.memory = memory
        self.meeting_agent: Any = None  # MeetingAgent; attached by get_semantic_chat_pipeline
        self._decide_slots = asyncio.Semaphore(int(getattr(config, "DECISION_CONCURRENCY", 8)))
        self._item_emb_cache: Dict[str, Any] = {}

    # ------------------------------------------------------------------ state / memory
    def state(self, session_id: str) -> ConversationState:
        if session_id not in self.states:
            stored = self.memory.load(session_id) if self.memory else None
            self.states[session_id] = ConversationState.from_dict(stored) if stored else ConversationState()
        return self.states[session_id]

    def _persist(self, session_id: str, state: ConversationState) -> None:
        if self.memory:
            try:
                self.memory.save(session_id, state)
            except Exception as e:  # memory must never break a reply
                logger.warning(f"[ChatMemory] save failed for {session_id[:24]}: {e}")
        if len(self.states) > 5000:  # in-process cache bound; SQLite remains the source of truth
            self.states.pop(next(iter(self.states)))

    def clear(self, session_id: str) -> None:
        self.states.pop(session_id, None)
        if self.memory:
            self.memory.delete(session_id)

    def _title(self, eid: Optional[str]) -> str:
        from knowledge_operation_executor import display_name
        e = self.registry.get_entity(eid) if eid else None
        return display_name(e or {}) or (eid or "")

    # ---------------------------------------------------------------- decide (one question)
    def _resolve_pending_clarification(self, message: str, state: ConversationState) -> Any:
        """'the first one' / 'second' after a clarification question picks that option."""
        pending = state.pending_clarification or {}
        options = pending.get("options") or []
        if not options:
            return None
        ql = message.lower().strip()
        ordinals = {"first": 0, "1st": 0, "one": 0, "second": 1, "2nd": 1, "two": 1, "third": 2, "3rd": 2, "last": len(options) - 1}
        if len(ql.split()) <= 4:
            for word, idx in ordinals.items():
                if re.search(rf"\b{word}\b", ql) and idx < len(options):
                    return options[idx] if options[idx].get("aspect") else options[idx].get("entity_id")
        return None

    def decide(self, message: str, state: Optional[ConversationState] = None) -> Tuple[Any, List[Any]]:
        """Single semantic decision + routing entry point (used by production and the benchmark)."""
        state = state or ConversationState()
        picked = self._resolve_pending_clarification(message, state)
        if isinstance(picked, dict):
            decision = self.engine.analyze_query(f"{picked['title']} of {self._title(picked['entity_id'])}",
                                                 active_entity=picked["entity_id"], context=state)
        elif picked:
            original = (state.pending_clarification or {}).get("query") or message
            decision = self.engine.analyze_query(original, active_entity=picked, context=_PickedContext(picked))
            if decision.entity.value != picked:
                decision = self.engine.analyze_query(f"tell me about {self._title(picked)}")
        else:
            decision = self.engine.analyze_query(message, active_entity=state.active_entity, context=state)
        plans = self.router.route_query(decision)
        return decision, plans

    def _apply_decision(self, state: ConversationState, message: str, decision: Any, plans: List[Any]) -> None:
        """Update conversational context from one decided question."""
        op = plans[0].operation_name if plans else None
        if op == "request_clarification":
            state.pending_clarification = {"query": message, "options": decision.clarification_options}
            return
        state.pending_clarification = None
        catalog = lambda e: str((self.registry.get_entity(e) or {}).get("type", "")).lower() in ("product", "solution", "service")
        if decision.scope.value == "MULTI_ENTITY" and decision.entities:
            state.active_entities = list(decision.entities[:2])
            state.active_entity = decision.entities[0]
            for e in decision.entities:
                if e not in state.discussed:
                    state.discussed.append(e)
        elif decision.entity.value and catalog(decision.entity.value):
            # Only catalog offerings become conversational context; a contact/about/awards answer must not
            # make the next unrelated question ("can you book me a flight?") inherit that page.
            state.active_entity = decision.entity.value
            if decision.entity.value not in state.active_entities:
                state.active_entities = (state.active_entities + [decision.entity.value])[-2:]
            if decision.entity.value not in state.discussed:
                state.discussed.append(decision.entity.value)
        state.active_aspect = decision.aspect.value
        state.active_scope = decision.scope.value

    def update_state(self, state: ConversationState, message: str, decision: Any, plans: List[Any], answer: str) -> None:
        """Kept for callers of the single-question API: record the turn and apply its decision."""
        self._record_turn(state, message, answer)
        self._apply_decision(state, message, decision, plans)

    @staticmethod
    def _record_turn(state: ConversationState, message: str, answer: str) -> None:
        from chat_memory import extract_visitor_facts
        state.turn_count += 1
        state.recent_turns = (state.recent_turns + [{"role": "user", "content": message},
                                                    {"role": "assistant", "content": answer[:1500]}])[-16:]
        for fact in extract_visitor_facts(_normalise_shorthand(message)):
            if fact not in state.visitor_facts:
                state.visitor_facts = (state.visitor_facts + [fact])[-8:]

    # ------------------------------------------------------------- evidence
    def _focus(self, ev: Evidence, question: str) -> Evidence:
        """Keep the items of a large section that are most relevant to the question (original order kept)."""
        if len(ev.items) <= MAX_EVIDENCE_ITEMS:
            return ev
        import numpy as np
        q = self.engine.index.encode_query(question)
        missing = [i for i in ev.items if i not in self._item_emb_cache]
        if missing:
            embs = self.engine.index.model.encode(missing, normalize_embeddings=True, show_progress_bar=False, batch_size=32)
            for text, emb in zip(missing, embs):
                self._item_emb_cache[text] = np.asarray(emb, dtype=np.float32)
            if len(self._item_emb_cache) > 20000:
                self._item_emb_cache.clear()
        scores = [float(self._item_emb_cache[i] @ q) for i in ev.items]
        keep = set(sorted(range(len(ev.items)), key=lambda k: scores[k], reverse=True)[:MAX_EVIDENCE_ITEMS])
        focused = copy.copy(ev)
        focused.items = [it for k, it in enumerate(ev.items) if k in keep]
        return focused

    def _evidence_for(self, question: str, decision: Any, plans: List[Any]) -> PartResult:
        plan = plans[0]
        op = plan.operation_name
        if op == "request_clarification":
            if _ARITHMETIC.match(question):
                return PartResult(question, decision, plans, "ood", note=OOD_TEXT)
            if _PRICE_QUESTION.search(question):
                # No offering named, but the answer is the same for all of them (owner decision: pricing unpublished)
                quote = self._contact_line().replace("For details", "For a quote", 1)
                return PartResult(question, decision, plans, "unavailable",
                                  note=f"CittaAI doesn't publish pricing for its products, solutions or services. {quote}")
            return PartResult(question, decision, plans, "clarify", note=self._clarification_text(decision, plan))
        if op == "decline_out_of_domain":
            if _COMPANY_QUESTION.search(question):
                # About CittaAI but not published ("how many employees?", "who is the CFO?"): say so, don't refuse
                return PartResult(question, decision, plans, "unavailable",
                                  note=f"I don't have verified information about that in CittaAI's published information. {self._contact_line()}")
            return PartResult(question, decision, plans, "ood", note=OOD_TEXT)
        if op in DETERMINISTIC_OPS or op in ENTITY_SECTION_OPS:
            evs = [self.executor.execute(p) for p in plans]
        else:
            evs = [self._semantic_search(question)]
        if op == "get_target_users" and not any(e.available for e in evs) and not _AUDIENCE_ASK.search(question):
            # "we're a pharma manufacturer, any solution?" was read as "who is it for"; that section isn't published,
            # but the visitor never asked it — answer from the offering's overview instead of "not available"
            overview = [self.executor.execute(OperationRoutePlan(TYPE_OVERVIEW_OPS.get(self.router._entity_type(p.inputs.get("entity_id")), "get_solution"),
                                                                 "KnowledgeRegistry", dict(p.inputs))) for p in plans]
            if any(e.available for e in overview):
                evs = overview
        available = [self._focus(e, question) for e in evs if e.available]
        if not available:
            return PartResult(question, decision, plans, "unavailable", evs,
                              note=self._unavailable_text(*evs) if evs[0].operation != "semantic_search"
                              else "I couldn't find verified information about that in CittaAI's knowledge base.")
        missing = [e for e in evs if not e.available]
        note = self._unavailable_text(*missing) if missing else ""
        return PartResult(question, decision, plans, "evidence", available, note=note)

    # ------------------------------------------------------------- rendering
    def _suggestions_for(self, eid: Optional[str]) -> List[str]:
        """Suggest only sections that actually have content, so follow-ups don't hit empty sections."""
        if not eid:
            return ["What solutions do you offer?", "What products do you have?", "How can I contact CittaAI?"]
        title = self._title(eid)
        out = []
        for op, q in [("get_capabilities", f"What can {title} do?"), ("get_benefits", f"What are the benefits of {title}?"),
                      ("get_workflow", f"How does {title} work?"), ("get_target_users", f"Who is {title} for?")]:
            if self.executor.execute(OperationRoutePlan(op, "KnowledgeRegistry", {"entity_id": eid})).available:
                out.append(q)
        return out[:3]

    def _render_deterministic(self, op: str, ev: Evidence) -> str:
        if not ev.available:
            return self._unavailable_text(ev)
        headings = {
            "list_products": "Here are CittaAI's products:", "list_solutions": "Here are CittaAI's solutions:",
            "list_services": "Here are CittaAI's services:", "list_catalog": "Here is CittaAI's full catalog:",
            "get_contact": "You can reach CittaAI here:", "get_leadership": "CittaAI's leadership team:",
            "get_recognition": "CittaAI's awards and recognition:", "list_case_studies": "Client case studies:",
            "get_case_study": "Case study:",
        }
        items = ev.items
        if op in ("list_products", "list_solutions", "list_services"):
            # The heading already says which type; "(solution):" on every line is noise
            items = [re.sub(r" \((?:product|solution|service)\):", ":", i) for i in items]
        return headings.get(op, "") + "\n\n" + "\n".join(f"- {i}" for i in items)

    def _unavailable_text(self, *evs: Evidence) -> str:
        """One sentence naming every offering the section is missing for ("… for Pharma OS or Enterprise AI OS")."""
        what = " / ".join(dict.fromkeys(SECTION_LABELS.get(e.section, e.section) for e in evs))
        titles = list(dict.fromkeys(e.title for e in evs if e.title))
        subject = f" for {' or '.join(titles)}" if titles else ""
        if all(e.section == "pricing" for e in evs):
            # Owner decision (2026-09-30): pricing is intentionally not published — say so, don't imply a gap
            quote = self._contact_line().replace("For details", "For a quote", 1)
            return f"CittaAI doesn't publish pricing{subject}. {quote}"
        return (f"I don't have verified information about the {what}{subject} in my current knowledge base. "
                f"{self._contact_line()}")

    def _contact_line(self) -> str:
        c = self.executor.execute(OperationRoutePlan("get_contact", "KnowledgeRegistry", {}))
        email = next((re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", i).group(0) for i in c.items if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", i)), None)
        phone = next((re.search(r"\+?\d[\d\s-]{8,}\d", i).group(0) for i in c.items if re.search(r"\+?\d[\d\s-]{8,}\d", i)), None)
        bits = " or ".join(b for b in [email, phone] if b)
        return f"For details, please contact the CittaAI team{' at ' + bits if bits else ''}."

    def _clarification_text(self, decision: Any, plan: Any) -> str:
        unknown = (plan.inputs or {}).get("unknown_entity")
        if unknown:
            cats = self.executor.execute(OperationRoutePlan("list_catalog", "KnowledgeRegistry", {}))
            names = ", ".join(i.split(" (")[0] for i in cats.items)
            return f"I couldn't find an offering called **{unknown.title()}** in CittaAI's catalog. Our offerings are: {names}."
        raw_options = (plan.inputs or {}).get("options") or []
        if raw_options and raw_options[0].get("aspect"):
            subject = self._title(raw_options[0].get("entity_id")) or "it"
            labels = [o["title"].lower() for o in raw_options]
            return f"Would you like to know about the {' or the '.join(labels)} of {subject}?"
        options = [o.get("title") for o in raw_options if o.get("title")]
        if any("both" in t or "pair" in t for t in decision.diagnostic_trace):
            return "Which two offerings would you like me to compare?"
        if options:
            return "Could you tell me which one you mean: " + ", ".join(f"**{o}**" for o in options[:3]) + "?"
        return "Could you tell me a bit more about what you're looking for — a specific product, solution, or service?"

    @staticmethod
    def _render_evidence(evidences: List[Evidence]) -> str:
        """Verbatim evidence, used when generation is unavailable or failed validation."""
        return "\n\n".join(f"**{e.title or 'CittaAI'} — {SECTION_LABELS.get(e.section, e.section)}**\n" +
                           "\n".join(f"- {_short(i)}" for i in e.items[:MAX_RENDERED_ITEMS]) for e in evidences)

    # ------------------------------------------------------------ generation
    def _system_prompt(self, state: ConversationState, knowledge: str, task: str) -> str:
        facts = "\n".join(f"- {f}" for f in state.visitor_facts) or "- (nothing yet)"
        return (
            "You are CittaAI's AI assistant on cittaai.com: friendly, clear and precise, like a knowledgeable product specialist.\n\n"
            "GROUND RULES (never break these):\n"
            "1. State only facts that appear in the KNOWLEDGE below. Never invent features, numbers, prices, clients, "
            "integrations, timelines, people or promises. Paraphrasing and summarising are fine.\n"
            "2. If the knowledge does not cover something the visitor asked, say so plainly for that part and suggest "
            f"contacting CittaAI. {self._contact_line()}\n"
            "3. Talk only about the CittaAI offerings in the knowledge; don't pad answers with unrelated offerings.\n"
            "4. Don't infer who an offering is for (roles, job titles, industries) or what it does from its name — "
            "only what the knowledge states. In comparison tables, include only rows the knowledge covers, and write "
            "'Not published' in a cell rather than filling it with a guess.\n"
            "5. Never mention 'knowledge', 'evidence', 'context', registries or internal IDs — speak naturally.\n\n"
            "STYLE:\n"
            "- BE BRIEF: lead with a direct 1–2 sentence answer, then at most 4 short bullets (one line each). About 80–120 words "
            "per question; go longer only if the visitor asks for detail or a comparison table.\n"
            "- Summarise long descriptions in your own words — never paste whole paragraphs or long feature lists.\n"
            "- Use markdown.\n"
            "- Use the conversation so far to resolve references ('it', 'that one') and avoid repeating what you already said.\n"
            "- Tailor the framing to what the visitor has told you about themselves, without inventing anything about them.\n"
            "- Give contact details only when something is missing from the knowledge or the visitor asks how to proceed — "
            "not at the end of every answer.\n"
            "- When useful, end with one short, relevant follow-up offer.\n\n"
            f"WHAT THE VISITOR HAS TOLD YOU ABOUT THEMSELVES:\n{facts}\n\n"
            f"TASK: {task}\n\nKNOWLEDGE:\n{knowledge}"
        )

    async def _llm(self, messages: List[Dict[str, str]], model: str, max_tokens: int) -> Tuple[str, Dict[str, Any]]:
        from llm_provider import ProviderUnavailableError
        if self.provider is None:
            return "", {"provider_unavailable": True, "llm_ms": 0.0}
        t0 = time.perf_counter()

        async def collect() -> str:
            out = ""
            async for chunk in self.provider.generate_stream(messages=messages, model=model, temperature=0.2, max_tokens=max_tokens):
                out += chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
            return out

        try:
            text = await asyncio.wait_for(collect(), float(getattr(config, "GENERATION_DEADLINE_S", 25)))
        except (ProviderUnavailableError, asyncio.TimeoutError) as e:
            text = ""
            logger.error(json.dumps({"event": "provider_unavailable", "error": f"{type(e).__name__}: {e}"[:300]}))
        meta = {"llm_ms": round((time.perf_counter() - t0) * 1000, 1), "generation_provider": getattr(self.provider, "last_provider", None)}
        if not text.strip():
            meta["provider_unavailable"] = True
        return text, meta

    def _validate(self, text: str, evidences: List[Evidence]) -> Tuple[bool, List[str]]:
        # Entity/section scope is enforced structurally (the LLM only sees scoped evidence), so the validator's
        # keyword entity/section matching is skipped; its hallucination guards (unsupported products, prices,
        # statistics, case studies, technologies) run against the evidence text.
        # Completeness across parts/entities is guaranteed structurally (one block per question), so the
        # validator's name-based completeness check is not used.
        from response_validator import validate_response
        ok, _checked, vmetrics = validate_response(
            text, resolved_entity=None, resolved_section=None, requested_entities=None,
            registry=self.registry, retry_count=0, return_metrics=True,
            evidence_text="\n".join(i for e in evidences for i in e.items))
        return ok, vmetrics.get("reasons", [])

    async def _answer_parts(self, message: str, parts: List[PartResult], state: ConversationState, model: str) -> Tuple[str, bool, Dict[str, Any]]:
        """One grounded answer for one or more questions."""
        single = len(parts) == 1
        if single and parts[0].kind != "evidence":
            return parts[0].note, True, {}
        # Plain catalog listings are rendered directly (fast, exact). Anything that asks something *about* a
        # list or company page ("which Fortune 500 companies use you?", "who is the CEO?") goes through the LLM
        # so the question itself gets answered — from that same evidence.
        if single and parts[0].plans[0].operation_name in DETERMINISTIC_OPS and (
                parts[0].plans[0].operation_name.startswith("list_") and parts[0].plans[0].operation_name != "list_case_studies"
                or self.provider is None):
            ev = parts[0].evidences[0]
            return self._render_deterministic(parts[0].plans[0].operation_name, ev), True, {}

        evidences = [e for p in parts for e in p.evidences if p.kind == "evidence"]
        blocks, fixed = [], []
        for n, p in enumerate(parts, 1):
            head = f"Question {n}: {p.question}" if not single else f"Question: {p.question}"
            if p.kind == "evidence":
                body = "\n\n".join(e.as_context() for e in p.evidences)
                if p.note:
                    body += f"\n(For this question also say: {p.note})"
                blocks.append(f"{head}\n{body}")
            else:
                fixed.append(f"{head}\nFor this question, reply exactly in substance: {p.note}")
                blocks.append(f"{head}\n(no knowledge — see instruction)")
        task = ("Answer the visitor's latest message." if single else
                f"The visitor asked {len(parts)} things in one message. Answer each of them, in order, under a short bold heading per question.")
        if fixed:
            task += " " + " ".join(fixed)
        system = self._system_prompt(state, "\n\n".join(blocks), task)
        messages = [{"role": "system", "content": system}] + state.recent_turns[-6:] + [{"role": "user", "content": message}]
        text, meta = await self._llm(messages, model, max_tokens=450 if single else min(1400, 350 * len(parts)))
        if not text.strip():
            rendered = [(f"**{p.question}**\n" if not single else "") + (self._render_evidence(p.evidences) if p.kind == "evidence" else p.note)
                        for p in parts]
            # The model is unavailable: say so, so a yes/no question isn't answered by an unexplained fact list
            if any(p.kind == "evidence" for p in parts):
                rendered.insert(0, "I can't compose a full answer right now, so here is what CittaAI publishes on this. "
                                   "If something you asked about isn't listed below, it isn't in CittaAI's published information.")
            return "\n\n".join(rendered), True, meta
        ok, reasons = self._validate(text, evidences)
        meta.update({"validator_ok": ok, "validator_reasons": reasons})
        if not ok:
            logger.warning(json.dumps({"event": "validator_rejected", "reasons": reasons}))
            rendered = [(f"**{p.question}**\n" if not single else "") + (self._render_evidence(p.evidences) if p.kind == "evidence" else p.note)
                        for p in parts]
            return "\n\n".join(rendered), False, meta
        if not _DETAIL_REQUEST.search(message):
            text = _cap_bullets(text)
        return text, True, meta

    # ------------------------------------------------------------- non-knowledge turns
    def _small_talk(self, message: str, state: ConversationState) -> Optional[str]:
        if _GREETING.match(message):
            back = f" Last time we talked about {self._title(state.discussed[-1])} — want to pick up there?" if state.discussed else ""
            return ("Hi! I'm CittaAI's assistant. I can help you explore our products, industry solutions and AI services, "
                    f"compare offerings, or connect you with the team.{back} What are you working on?")
        if _IDENTITY.match(message):
            return ("I'm CittaAI's AI assistant. I can explain any of our products (like WhatsApp Marketing and Influencer Marketing), "
                    "industry operating systems (Education, Pharma, Real Estate, E-Commerce, Smart Cities, Enterprise AI), and services "
                    "(Data Engineering, Enterprise & Agentic AI, AI Strategy, AI-Powered Marketing) — what they do, who they're for, "
                    "how they work and how to get in touch. I answer only from CittaAI's published information.")
        if _BYE.match(message):
            return "Thanks for chatting! If anything else comes up about CittaAI, I'm here."
        if _THANKS.match(message) and len(message.split()) <= 6:
            return "You're welcome! Anything else you'd like to know about CittaAI?"
        return None

    def _conversation_answer(self, message: str, state: ConversationState) -> str:
        questions = [t["content"] for t in state.recent_turns if t["role"] == "user"]
        if not questions:
            return "We haven't discussed anything yet — what would you like to know about CittaAI?"
        ql = message.lower()
        if "first" in ql:
            return f"Your first question was: “{questions[0]}”"
        if re.search(r"\b(last|previous|earlier)\b", ql) and "question" in ql:
            return f"Your previous question was: “{questions[-1]}”"
        lines = ["Here's a quick recap of our conversation:", "", "**You asked about:**"]
        lines += [f"{n}. {q}" for n, q in enumerate(questions[-8:], 1)]
        if state.discussed:
            lines += ["", "**Offerings we covered:** " + ", ".join(self._title(e) for e in state.discussed)]
        if state.visitor_facts:
            lines += ["", "**What you told me about yourself:**"] + [f"- {f}" for f in state.visitor_facts]
        return "\n".join(lines)

    async def _rewrite_last(self, message: str, state: ConversationState, model: str) -> Tuple[str, bool, Dict[str, Any]]:
        evidences = [Evidence(operation=e.get("operation", ""), section=e.get("section", "overview"), entity_id=e.get("entity_id"),
                              title=e.get("title"), items=list(e.get("items") or []), available=True) for e in state.last_evidence]
        last_answer = next((t["content"] for t in reversed(state.recent_turns) if t["role"] == "assistant"), "")
        task = (f"The visitor wants your previous answer adjusted: “{message}”. Their earlier question was “{state.last_question}”. "
                "Rewrite the answer accordingly, still using only the knowledge.")
        system = self._system_prompt(state, "\n\n".join(e.as_context() for e in evidences), task)
        messages = [{"role": "system", "content": system}, {"role": "assistant", "content": last_answer}, {"role": "user", "content": message}]
        text, meta = await self._llm(messages, model, max_tokens=600)
        if not text.strip():
            return last_answer, True, meta
        ok, reasons = self._validate(text, evidences)
        meta.update({"validator_ok": ok, "validator_reasons": reasons})
        return (text if ok else last_answer), ok, meta

    # ---------------------------------------------------------------- stream
    async def _decide_async(self, question: str, state: ConversationState) -> Tuple[Any, List[Any]]:
        # CPU-bound embedding work (and any adjudication call) runs off the event loop so concurrent
        # visitors keep streaming; the semaphore bounds parallel model work.
        async with self._decide_slots:
            return await asyncio.to_thread(self.decide, question, state)

    async def stream(self, session_id: str, message: str, model: str, request_id: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        request_id = request_id or uuid.uuid4().hex[:12]
        t0 = time.perf_counter()
        state = self.state(session_id)
        message = message.strip()
        parts: List[PartResult] = []
        gen_meta: Dict[str, Any] = {}
        verified, redirect, suggestions = True, None, []

        # The meeting agent sees every message first: it owns the turn while it is collecting details
        agent_reply = None
        if self.meeting_agent is not None:
            agent_reply = await self.meeting_agent.handle(message, state, session_id, self._contact_line(), self._title)
        small = None if agent_reply and agent_reply.text else self._small_talk(message, state)
        if agent_reply and agent_reply.text:
            turn_kind, answer = "meeting_agent", agent_reply.text
            suggestions = agent_reply.suggestions
        elif small is not None:
            turn_kind, answer = "small_talk", small
            suggestions = self._suggestions_for(state.active_entity)
        elif _META.search(_normalise_shorthand(message)):
            turn_kind, answer = "conversation_memory", self._conversation_answer(message, state)
        elif _REWRITE.search(message) and len(message.split()) <= 12 and state.last_evidence:
            turn_kind = "rewrite"
            answer, verified, gen_meta = await self._rewrite_last(message, state, model)
        else:
            turn_kind = "knowledge"
            scratch = copy.deepcopy(state)
            for question in split_questions(message):
                decision, plans = await self._decide_async(question, scratch)
                part = self._evidence_for(question, decision, plans)
                parts.append(part)
                self._apply_decision(scratch, question, decision, plans)
            answer, verified, gen_meta = await self._answer_parts(message, parts, state, model)
            # Adopt the context the parts produced; remember what the answer was built from for rewrites
            for attr in ("active_entity", "active_entities", "active_aspect", "active_scope", "pending_clarification", "discussed"):
                setattr(state, attr, getattr(scratch, attr))
            used = [e for p in parts for e in p.evidences if p.kind == "evidence"]
            if used:
                state.last_evidence = [{"operation": e.operation, "section": e.section, "entity_id": e.entity_id,
                                        "title": e.title, "items": e.items} for e in used]
                state.last_question = message
            first = parts[0]
            if agent_reply and agent_reply.reminder:
                answer += "\n\n" + agent_reply.reminder
            elif (self.meeting_agent is not None and not (state.meeting or {}).get("stage")
                  and any(p.plans[0].operation_name == "get_contact" and p.kind == "evidence" for p in parts)):
                answer += "\n\n" + self.meeting_agent.offer(state)
            if len(parts) == 1 and first.kind == "evidence" and len(first.evidences) == 1:
                redirect = first.evidences[0].route
            if first.kind == "clarify":
                suggestions = [f"Tell me about {o['title']}" for o in (first.plans[0].inputs or {}).get("options") or []][:3]
            else:
                suggestions = self._suggestions_for(first.decision.entity.value if first.decision.scope.value == "SINGLE_ENTITY" else None)

        self._record_turn(state, message, answer)
        self._persist(session_id, state)
        for i in range(0, len(answer), 120):
            yield {"text": answer[i:i + 120], "done": False}

        metrics: Dict[str, Any] = {"request_id": request_id, "pipeline": "semantic", "semantic_fallback": False, "turn_kind": turn_kind,
                                   "total_ms": round((time.perf_counter() - t0) * 1000, 1), **gen_meta}
        if parts:
            d = parts[0].decision.to_dict()
            plan = parts[0].plans[0]
            metrics.update({
                "decision": {k: d[k] for k in ("entity", "entities", "intent", "aspect", "scope", "needs_clarification",
                                               "llm_invoked", "entity_evidence", "aspect_evidence", "scope_evidence")},
                "operation": plan.operation_name,
                "operation_inputs": {k: v for k, v in (plan.inputs or {}).items() if k != "options"},
                "evidence_available": [e.available for e in (parts[0].evidences or [])] or [False],
                "parts": [{"question": p.question, "entity": p.decision.entity.value, "entities": p.decision.entities,
                           "aspect": p.decision.aspect.value, "scope": p.decision.scope.value,
                           "operation": p.plans[0].operation_name, "kind": p.kind} for p in parts],
            })
        yield {
            "done": True,
            "citations": sorted({e.title for p in parts for e in p.evidences if p.kind == "evidence" and e.title}),
            "suggested_questions": suggestions,
            "redirect": redirect,
            "source": "CittaAI Knowledge Registry + cittaai.com",
            "verified": verified,
            "confidence": parts[0].decision.to_dict()["confidence"] if parts else 1.0,
            "metrics": metrics,
        }

    def _semantic_search(self, message: str) -> Evidence:
        from vector_store import VectorStore
        vstore = VectorStore(config.VECTOR_DB_PATH)
        q_emb = self.engine.index.encode_query(message)
        chunks = vstore.query_hybrid(query_text=message, query_embedding=q_emb.tolist(), top_k=5)
        items = [c.get("content") or c.get("text") or "" for c in chunks if (c.get("score") or 0) >= 0.35]
        return Evidence("semantic_search", "overview", None, "CittaAI", [i[:600] for i in items if i], bool(items))


class _PickedContext:
    def __init__(self, eid: str):
        self.active_entity = eid
        self.active_entities: List[str] = []
        self.active_entity_confidence = 0.95


_PIPELINE: Optional[SemanticChatPipeline] = None


def get_semantic_chat_pipeline(provider: Any = None) -> SemanticChatPipeline:
    global _PIPELINE
    if _PIPELINE is None:
        from chat_memory import ChatMemoryStore
        from meeting_agent import get_meeting_agent
        _PIPELINE = SemanticChatPipeline(provider=provider, memory=ChatMemoryStore())
        _PIPELINE.meeting_agent = get_meeting_agent()
    elif provider is not None and _PIPELINE.provider is None:
        _PIPELINE.provider = provider
    return _PIPELINE
