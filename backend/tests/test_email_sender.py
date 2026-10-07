"""
Email transport selection and the Brevo HTTPS request (mocked — nothing is sent).
"""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

import config
import email_sender


@pytest.fixture
def clean(monkeypatch):
    for k in ("BREVO_API_KEY", "MAIL_FROM", "SMTP_USERNAME", "SMTP_PASSWORD"):
        monkeypatch.setattr(config, k, "")
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.gmail.com")
    return monkeypatch


def test_transport_prefers_brevo_and_falls_back_to_smtp(clean):
    assert email_sender.transport() is None
    clean.setattr(config, "SMTP_USERNAME", "sender@gmail.com")
    clean.setattr(config, "SMTP_PASSWORD", "app-password")
    assert email_sender.transport() == "smtp"
    clean.setattr(config, "BREVO_API_KEY", "xkeysib-test")
    assert email_sender.transport() == "brevo"  # sender defaults to SMTP_USERNAME


def test_brevo_request_and_error(clean):
    clean.setattr(config, "BREVO_API_KEY", "xkeysib-test")
    clean.setattr(config, "MAIL_FROM", "sender@gmail.com")
    calls = []

    class Resp:
        def __init__(self, code, body):
            self.status_code, self._body, self.text = code, body, str(body)

        def json(self):
            return self._body

    class Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, headers=None):
            calls.append((url, json, headers))
            return Resp(201, {"messageId": "<abc@brevo>"}) if json["to"][0]["email"] != "bad@x.com" \
                else Resp(400, {"message": "sender not verified"})

    clean.setattr(email_sender.httpx, "AsyncClient", Client)
    mid = asyncio.run(email_sender.send_email("visitor@x.com", "Hi", "text", "<p>html</p>", reply_to="team@x.com"))
    assert mid == "<abc@brevo>"
    url, body, headers = calls[0]
    assert url == email_sender.BREVO_URL and headers["api-key"] == "xkeysib-test"
    assert body["sender"]["email"] == "sender@gmail.com" and body["to"] == [{"email": "visitor@x.com"}]
    assert body["replyTo"] == {"email": "team@x.com"} and body["htmlContent"] == "<p>html</p>"
    with pytest.raises(email_sender.EmailSendError, match="400"):
        asyncio.run(email_sender.send_email("bad@x.com", "Hi", "text"))
