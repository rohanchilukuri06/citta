"""
Outgoing email for the meeting agent and the contact form.

Two transports, chosen automatically:
  1. Brevo HTTPS API (preferred when BREVO_API_KEY is set). Works on hosts that block outbound SMTP,
     such as Railway's trial/hobby plans. Needs MAIL_FROM to be a sender verified in Brevo.
  2. SMTP (e.g. Gmail: smtp.gmail.com:587 with an App Password) — SMTP_HOST, SMTP_PORT, SMTP_USERNAME,
     SMTP_PASSWORD, SMTP_USE_TLS. Fine for local runs and hosts that allow SMTP.

MAIL_FROM_NAME sets the display name. SMTP sending runs in a worker thread so the event loop never blocks.
"""

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Optional

import httpx

import config

logger = logging.getLogger(__name__)

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


class EmailNotConfiguredError(RuntimeError):
    pass


class EmailSendError(RuntimeError):
    pass


def _sender_address() -> str:
    return config.MAIL_FROM or config.SMTP_USERNAME


def transport() -> Optional[str]:
    """'brevo', 'smtp', or None when nothing is configured."""
    if config.BREVO_API_KEY and _sender_address():
        return "brevo"
    if config.SMTP_HOST and config.SMTP_USERNAME and config.SMTP_PASSWORD:
        return "smtp"
    return None


def is_configured() -> bool:
    return transport() is not None


# ----------------------------------------------------------------------------- Brevo (HTTPS)
async def _send_brevo(to: str, subject: str, text: str, html: Optional[str], reply_to: Optional[str]) -> str:
    payload = {
        "sender": {"name": config.MAIL_FROM_NAME, "email": _sender_address()},
        "to": [{"email": to}],
        "subject": subject,
        "textContent": text,
    }
    if html:
        payload["htmlContent"] = html
    if reply_to:
        payload["replyTo"] = {"email": reply_to}
    async with httpx.AsyncClient(timeout=config.SMTP_TIMEOUT_S) as client:
        res = await client.post(BREVO_URL, json=payload,
                                headers={"api-key": config.BREVO_API_KEY, "accept": "application/json"})
    if res.status_code >= 300:
        # Brevo explains the problem (unverified sender, invalid key, …) in the body; never echo the key
        raise EmailSendError(f"Brevo HTTP {res.status_code}: {res.text[:300]}")
    return (res.json() or {}).get("messageId", "")


# ----------------------------------------------------------------------------- SMTP
def _send_smtp_sync(to: str, subject: str, text: str, html: Optional[str], reply_to: Optional[str]) -> str:
    msg = EmailMessage()  # rejects CR/LF in header values, so visitor input can't inject headers
    msg["From"] = formataddr((config.MAIL_FROM_NAME, _sender_address()))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=_sender_address().split("@")[-1])
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    if config.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=config.SMTP_TIMEOUT_S,
                              context=ssl.create_default_context()) as s:
            s.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            s.send_message(msg)
    else:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=config.SMTP_TIMEOUT_S) as s:
            if config.SMTP_USE_TLS:
                s.starttls(context=ssl.create_default_context())
            s.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            s.send_message(msg)
    return msg["Message-ID"]


async def send_email(to: str, subject: str, text: str, html: Optional[str] = None, reply_to: Optional[str] = None) -> str:
    """Send one email through the configured transport; returns its message id. Raises on failure."""
    kind = transport()
    if kind is None:
        raise EmailNotConfiguredError("Set BREVO_API_KEY + MAIL_FROM, or SMTP_HOST / SMTP_USERNAME / SMTP_PASSWORD")
    if kind == "brevo":
        return await asyncio.wait_for(_send_brevo(to, subject, text, html, reply_to), config.SMTP_TIMEOUT_S + 5)
    return await asyncio.wait_for(asyncio.to_thread(_send_smtp_sync, to, subject, text, html, reply_to),
                                  config.SMTP_TIMEOUT_S + 5)
