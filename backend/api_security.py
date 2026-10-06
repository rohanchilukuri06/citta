"""
API protection for the public chatbot deployment:
  - require_admin: X-Admin-Token check for admin/debug/tenant routes (disabled in production without a token)
  - ChatRateLimiter: per-session and per-IP sliding-window limits for /api/chat

The rate limiter is in-process. With several uvicorn workers or instances each keeps its own window,
so the effective limit is multiplied by the worker count — use a shared store (e.g. Redis) or an edge
rate limiter if you scale out.
"""

import hmac
import logging
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import Header, HTTPException, Request

import config

logger = logging.getLogger(__name__)
_warned_open_admin = False


def require_admin(x_admin_token: Optional[str] = Header(default=None)) -> None:
    global _warned_open_admin
    expected = getattr(config, "ADMIN_API_TOKEN", "")
    if not expected:
        if str(getattr(config, "ENVIRONMENT", "production")).lower() == "production":
            raise HTTPException(status_code=503, detail="Admin API disabled: set ADMIN_API_TOKEN to enable it.")
        if not _warned_open_admin:
            logger.warning("ADMIN_API_TOKEN is not set: admin API is open because ENVIRONMENT=development.")
            _warned_open_admin = True
        return
    if not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing admin token.")


class ChatRateLimiter:
    def __init__(self, per_session: int, per_ip: int, window_s: float = 60.0):
        self.per_session, self.per_ip, self.window = per_session, per_ip, window_s
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _allow(self, key: str, limit: int, now: float) -> bool:
        q = self._hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True

    def check(self, request: Request, session_id: str) -> None:
        ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or (request.client.host if request.client else "unknown")
        now = time.monotonic()
        with self._lock:
            ok_ip = self._allow(f"ip:{ip}", self.per_ip, now)
            ok_session = ok_ip and self._allow(f"session:{session_id}", self.per_session, now)
            if len(self._hits) > 50_000:  # bound memory under abuse
                for k in [k for k, q in self._hits.items() if not q or now - q[-1] > self.window][:25_000]:
                    self._hits.pop(k, None)
        if not (ok_ip and ok_session):
            logger.warning(f"Chat rate limit hit ({'ip' if not ok_ip else 'session'}) ip={ip} session={session_id[:32]}")
            raise HTTPException(status_code=429, detail="Too many messages. Please wait a moment and try again.",
                                headers={"Retry-After": str(int(self.window))})


chat_rate_limiter = ChatRateLimiter(
    per_session=getattr(config, "CHAT_RATE_LIMIT_PER_SESSION_PER_MIN", 20),
    per_ip=getattr(config, "CHAT_RATE_LIMIT_PER_IP_PER_MIN", 60),
)
