"""
Deployment configuration check.

A missing or mistyped variable on the host used to surface only when a visitor hit it (no answer model key:
every reply fell back to raw text; an SMTP key pasted as the Brevo API key: every confirmation email failed).
This module finds those problems at startup, logs each one in plain words, and feeds /api/health.

  static_issues()  — looks at the variables only (instant, no network)
  live_issues()    — asks the real services whether the keys work and the sender is verified

Messages never contain a secret's value.
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

import config

logger = logging.getLogger(__name__)

ERROR, WARNING = "error", "warning"
_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
_LLM_KEYS = {"nvidia": "NVIDIA_API_KEY", "groq": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY"}

_REPORT: Dict[str, Any] = {"checked": False, "issues": []}


def _issue(level: str, area: str, message: str) -> Dict[str, str]:
    return {"level": level, "area": area, "message": message}


def _is_production() -> bool:
    return str(getattr(config, "ENVIRONMENT", "development")).lower() == "production"


def static_issues() -> List[Dict[str, str]]:
    from email_sender import transport
    issues: List[Dict[str, str]] = []

    # ---- answer model
    provider = str(config.LLM_PROVIDER).lower()
    key_name = _LLM_KEYS.get(provider)
    if key_name is None:
        issues.append(_issue(ERROR, "llm", f"LLM_PROVIDER is '{config.LLM_PROVIDER}'; it must be one of nvidia, groq, gemini."))
    elif not getattr(config, key_name, ""):
        issues.append(_issue(ERROR, "llm", f"{key_name} is not set, so the chatbot can't compose answers and falls back to "
                                           "raw published text. Add it in the host's variables."))
    elif provider == "nvidia" and not config.NVIDIA_API_KEY.startswith("nvapi-"):
        issues.append(_issue(WARNING, "llm", "NVIDIA_API_KEY doesn't start with 'nvapi-'; check that the whole key was pasted."))

    # ---- email
    brevo = config.BREVO_API_KEY
    kind = transport()
    if brevo.startswith("xsmtpsib-"):
        issues.append(_issue(ERROR, "email", "BREVO_API_KEY holds an SMTP key (starts with 'xsmtpsib-'). Brevo's API needs an "
                                             "API key, which starts with 'xkeysib-' (Brevo > SMTP & API > API Keys tab)."))
    elif brevo and not brevo.startswith("xkeysib-"):
        issues.append(_issue(WARNING, "email", "BREVO_API_KEY doesn't start with 'xkeysib-'; check that the whole API key was pasted."))
    if brevo and not (config.MAIL_FROM or config.SMTP_USERNAME):
        issues.append(_issue(ERROR, "email", "BREVO_API_KEY is set but MAIL_FROM is not. Set MAIL_FROM to a sender address "
                                             "verified in Brevo."))
    if kind is None:
        issues.append(_issue(ERROR, "email", "No email transport is configured, so meeting requests are saved but no emails are "
                                             "sent. Set BREVO_API_KEY and MAIL_FROM (or the SMTP_* variables)."))
    elif kind == "smtp" and _is_production():
        issues.append(_issue(WARNING, "email", "Email is sent over SMTP. Hosts such as Railway block SMTP on trial/hobby plans; "
                                               "set BREVO_API_KEY and MAIL_FROM to send over HTTPS instead."))
    for name in ("MAIL_FROM", "COMPANY_LEAD_EMAIL"):
        value = getattr(config, name, "")
        if value and not _EMAIL.match(value):
            issues.append(_issue(ERROR, "email", f"{name} is not a valid email address."))
    if not config.COMPANY_LEAD_EMAIL:
        issues.append(_issue(ERROR, "email", "COMPANY_LEAD_EMAIL is not set, so the team is never emailed about new meeting requests."))

    # ---- access
    if _is_production() and not getattr(config, "ADMIN_API_TOKEN", ""):
        issues.append(_issue(WARNING, "admin", "ADMIN_API_TOKEN is not set, so the admin endpoints (including the saved meeting "
                                               "requests) are disabled."))
    return issues


async def _check_brevo(client: httpx.AsyncClient) -> List[Dict[str, str]]:
    headers = {"api-key": config.BREVO_API_KEY, "accept": "application/json"}
    res = await client.get("https://api.brevo.com/v3/account", headers=headers)
    if res.status_code == 401:
        return [_issue(ERROR, "email", "Brevo rejected BREVO_API_KEY (401). Generate a new API key in Brevo "
                                       "(SMTP & API > API Keys) and paste it into the host's variables.")]
    if res.status_code >= 300:
        return [_issue(WARNING, "email", f"Brevo answered HTTP {res.status_code} when checking the API key.")]
    sender = (config.MAIL_FROM or config.SMTP_USERNAME).lower()
    res = await client.get("https://api.brevo.com/v3/senders", headers=headers)
    if res.status_code < 300:
        senders = {str(s.get("email", "")).lower(): bool(s.get("active")) for s in (res.json() or {}).get("senders", [])}
        if sender not in senders:
            return [_issue(ERROR, "email", "MAIL_FROM is not a sender in the Brevo account, so Brevo will refuse to "
                                           "send. Add and verify it under Brevo > Senders, Domains & Dedicated IPs.")]
        if not senders[sender]:
            return [_issue(ERROR, "email", "MAIL_FROM is in Brevo but not verified yet. Open the verification "
                                           "email Brevo sent to that address.")]
    return []


async def _check_nvidia(client: httpx.AsyncClient) -> List[Dict[str, str]]:
    res = await client.post(f"{config.NVIDIA_BASE_URL.rstrip('/')}/chat/completions",
                            headers={"Authorization": f"Bearer {config.NVIDIA_API_KEY}"},
                            json={"model": config.NVIDIA_MODEL, "max_tokens": 1,
                                  "messages": [{"role": "user", "content": "ok"}]})
    if res.status_code in (401, 403):
        return [_issue(ERROR, "llm", f"NVIDIA rejected NVIDIA_API_KEY (HTTP {res.status_code}), so the chatbot can't compose "
                                     "answers. Generate a new key at build.nvidia.com and paste it into the host's variables.")]
    if res.status_code in (404, 410):
        return [_issue(ERROR, "llm", f"NVIDIA_MODEL '{config.NVIDIA_MODEL}' is not available (HTTP {res.status_code}).")]
    return []   # 429 / 5xx: busy right now, not a configuration problem


async def live_issues(timeout: float = 12.0) -> List[Dict[str, str]]:
    from email_sender import transport
    checks = []
    if transport() == "brevo" and config.BREVO_API_KEY.startswith("xkeysib-"):
        checks.append(("email", _check_brevo))
    if str(config.LLM_PROVIDER).lower() == "nvidia" and config.NVIDIA_API_KEY:
        checks.append(("llm", _check_nvidia))
    issues: List[Dict[str, str]] = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        for area, check in checks:
            try:
                issues += await check(client)
            except (httpx.HTTPError, asyncio.TimeoutError, ValueError) as e:
                # Unreachable is not the same as misconfigured: note it without failing the report
                issues.append(_issue(WARNING, area, f"Could not verify the {area} settings right now ({type(e).__name__})."))
    return issues


async def run(live: bool = True) -> Dict[str, Any]:
    """Check everything, log each problem once, and remember the result for /api/health."""
    issues = static_issues()
    if live:
        issues += await live_issues()
    for i in issues:
        log = logger.error if i["level"] == ERROR else logger.warning
        log(json.dumps({"event": "config_problem", "area": i["area"], "level": i["level"], "message": i["message"]}))
    if not issues:
        logger.info(json.dumps({"event": "config_ok", "live_checked": live}))
    _REPORT.update({"checked": True, "live_checked": live, "issues": issues})
    return dict(_REPORT)


def report() -> Dict[str, Any]:
    """Last result; before the startup check has finished, the instant variable-only check."""
    if not _REPORT["checked"]:
        return {"checked": False, "live_checked": False, "issues": static_issues()}
    return dict(_REPORT)


def errors(rep: Optional[Dict[str, Any]] = None) -> List[str]:
    return [i["message"] for i in (rep or report())["issues"] if i["level"] == ERROR]
