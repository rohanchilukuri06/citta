"""
Persistent conversation memory for the website chatbot.

Each session's ConversationState (recent turns, offerings discussed, facts the visitor shared about
themselves, the last answer's evidence, pending clarification) is stored in SQLite, so conversations
survive restarts and are shared by every worker process on the host. Sessions expire after
CHAT_MEMORY_TTL_DAYS of inactivity.
"""

import json
import logging
import re
import sqlite3
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import config

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "chat_memory.db"
TTL_S = float(getattr(config, "CHAT_MEMORY_TTL_DAYS", 30)) * 86400
MAX_TURNS = 16      # stored turns (user + assistant messages)
MAX_FACTS = 8

# Things visitors say about themselves that should shape later answers
_FACT_PATTERN = re.compile(
    r"\b(?:we are|we're|we run|we have|we operate|we sell|we manage|i am|i'm|i run|i manage|i own|i work (?:at|for|in)|"
    r"our (?:company|business|college|university|school|institute|team|store|shop|brand|agency|hospital|clinic|firm|organisation|organization|startup|city))\b[^.?!]{3,160}",
    re.IGNORECASE,
)


def extract_visitor_facts(message: str) -> List[str]:
    facts = []
    for m in _FACT_PATTERN.finditer(message):
        fact = m.group(0).strip().rstrip(",;")
        if len(fact.split()) >= 3:
            facts.append(fact[0].upper() + fact[1:])
    return facts


class ChatMemoryStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or getattr(config, "CHAT_MEMORY_DB_PATH", "") or DEFAULT_DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, state TEXT NOT NULL, updated_at REAL NOT NULL)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at)")

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as c:
            row = c.execute("SELECT state, updated_at FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not row or time.time() - row[1] > TTL_S:
            return None
        try:
            return json.loads(row[0])
        except ValueError:
            logger.warning(f"[ChatMemory] Corrupt state for session {session_id[:24]}; starting fresh")
            return None

    def save(self, session_id: str, state: Any) -> None:
        data = asdict(state) if not isinstance(state, dict) else state
        data["recent_turns"] = data.get("recent_turns", [])[-MAX_TURNS:]
        data["visitor_facts"] = data.get("visitor_facts", [])[-MAX_FACTS:]
        with self._lock, self._conn() as c:
            c.execute("INSERT OR REPLACE INTO sessions (session_id, state, updated_at) VALUES (?, ?, ?)",
                      (session_id, json.dumps(data, ensure_ascii=False, default=str), time.time()))

    def delete(self, session_id: str) -> None:
        with self._lock, self._conn() as c:
            c.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

    def purge_expired(self) -> int:
        with self._lock, self._conn() as c:
            return c.execute("DELETE FROM sessions WHERE updated_at < ?", (time.time() - TTL_S,)).rowcount
