"""
Outgoing email over SMTP (e.g. Gmail: smtp.gmail.com:587 with an App Password).

Configured from .env: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS, MAIL_FROM, MAIL_FROM_NAME.
Sending runs in a worker thread so the chat event loop is never blocked.
"""

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Optional

import config

logger = logging.getLogger(__name__)


class EmailNotConfiguredError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_USERNAME and config.SMTP_PASSWORD)


def _send_sync(to: str, subject: str, text: str, html: Optional[str], reply_to: Optional[str]) -> str:
    if not is_configured():
        raise EmailNotConfiguredError("SMTP_HOST / SMTP_USERNAME / SMTP_PASSWORD are not set")
    msg = EmailMessage()  # rejects CR/LF in header values, so visitor input can't inject headers
    msg["From"] = formataddr((config.MAIL_FROM_NAME, config.MAIL_FROM or config.SMTP_USERNAME))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=(config.MAIL_FROM or config.SMTP_USERNAME).split("@")[-1])
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
    """Send one email; returns its Message-ID. Raises on failure (callers record the outcome)."""
    return await asyncio.wait_for(asyncio.to_thread(_send_sync, to, subject, text, html, reply_to),
                                  config.SMTP_TIMEOUT_S + 5)
