"""
Deployment configuration check: each case is a mistake that reached production once (or the next one in line) —
no answer-model key, an SMTP key pasted as the Brevo API key, a rejected key, an unverified sender.
No network: the services are replaced by httpx.MockTransport.
"""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import httpx
import pytest

import config
import config_check


@pytest.fixture
def good(monkeypatch):
    """A complete production configuration; each test then breaks one thing."""
    for name, value in {
        "ENVIRONMENT": "production", "LLM_PROVIDER": "nvidia", "NVIDIA_API_KEY": "nvapi-test",
        "BREVO_API_KEY": "xkeysib-test", "MAIL_FROM": "hello@example.com", "SMTP_USERNAME": "", "SMTP_PASSWORD": "",
        "COMPANY_LEAD_EMAIL": "team@example.com", "ADMIN_API_TOKEN": "token",
    }.items():
        monkeypatch.setattr(config, name, value)
    monkeypatch.setitem(config_check._REPORT, "checked", False)
    return monkeypatch


def messages(level=None):
    return [i["message"] for i in config_check.static_issues() if level in (None, i["level"])]


def test_complete_configuration_has_no_issues(good):
    assert config_check.static_issues() == []


def test_missing_answer_model_key_is_an_error(good):
    good.setattr(config, "NVIDIA_API_KEY", "")
    assert any("NVIDIA_API_KEY is not set" in m for m in messages("error"))


def test_smtp_key_pasted_as_brevo_api_key_is_named_exactly(good):
    good.setattr(config, "BREVO_API_KEY", "xsmtpsib-abc")
    (msg,) = messages("error")
    assert "SMTP key" in msg and "xkeysib-" in msg and "abc" not in msg      # explains the fix, never echoes the key


def test_no_email_transport_and_missing_team_address_are_errors(good):
    good.setattr(config, "BREVO_API_KEY", "")
    good.setattr(config, "COMPANY_LEAD_EMAIL", "")
    errs = messages("error")
    assert any("No email transport" in m for m in errs) and any("COMPANY_LEAD_EMAIL is not set" in m for m in errs)


def test_smtp_in_production_and_missing_admin_token_are_warnings(good):
    good.setattr(config, "BREVO_API_KEY", "")
    good.setattr(config, "SMTP_USERNAME", "a@gmail.com")
    good.setattr(config, "SMTP_PASSWORD", "app-password")
    good.setattr(config, "ADMIN_API_TOKEN", "")
    assert messages("error") == []
    assert len(messages("warning")) == 2


def test_invalid_addresses_are_errors(good):
    good.setattr(config, "MAIL_FROM", "not-an-address")
    assert any("MAIL_FROM is not a valid email" in m for m in messages("error"))


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _brevo(account_status=200, senders=None):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["api-key"] == "xkeysib-test"
        if request.url.path.endswith("/account"):
            return httpx.Response(account_status, json={"message": "Key not found"} if account_status == 401 else {})
        return httpx.Response(200, json={"senders": senders or []})
    return handler


def run_brevo(handler):
    async def go():
        async with _client(handler) as c:
            return await config_check._check_brevo(c)
    return asyncio.run(go())


def test_brevo_rejecting_the_key_is_reported(good):
    (issue,) = run_brevo(_brevo(account_status=401))
    assert issue["level"] == "error" and "rejected BREVO_API_KEY" in issue["message"]


def test_sender_missing_or_unverified_in_brevo_is_reported(good):
    (missing,) = run_brevo(_brevo(senders=[{"email": "other@example.com", "active": True}]))
    assert "not a sender" in missing["message"]
    (pending,) = run_brevo(_brevo(senders=[{"email": "Hello@Example.com", "active": False}]))
    assert "not verified" in pending["message"]
    assert run_brevo(_brevo(senders=[{"email": "hello@example.com", "active": True}])) == []


@pytest.mark.parametrize("status,expected", [(200, 0), (401, 1), (403, 1), (410, 1), (429, 0), (503, 0)])
def test_nvidia_key_and_model_are_verified_but_a_busy_service_is_not_an_error(good, status, expected):
    async def go():
        async with _client(lambda request: httpx.Response(status, json={})) as c:
            return await config_check._check_nvidia(c)
    assert len(asyncio.run(go())) == expected


def test_health_reports_configuration_errors_without_secrets(good):
    from fastapi.testclient import TestClient
    import index_integrity
    import server
    # The index status is computed once and cached; give this test its own so it leaves nothing behind
    good.setattr(index_integrity, "_STATUS", {"fresh": True, "rebuild_required": False, "reasons": []})
    good.setattr(config, "BREVO_API_KEY", "xsmtpsib-secretvalue")
    body = TestClient(server.app).get("/api/health").json()
    assert body["status"] == "Degraded" and body["email"]["status"] == "Not working"
    assert any("SMTP key" in m for m in body["config_issues"])
    assert "secretvalue" not in str(body)


def test_keys_are_cleaned_of_quotes_and_spaces(monkeypatch):
    monkeypatch.setenv("X_TEST_KEY", '  "nvapi-abc"  ')
    assert config._clean("X_TEST_KEY") == "nvapi-abc"
    monkeypatch.setenv("X_TEST_KEY", " 'xkeysib-abc' ")
    assert config._clean("X_TEST_KEY") == "xkeysib-abc"
    monkeypatch.setenv("X_TEST_KEY", "abcd efgh ijkl mnop")          # spaces inside a value are kept
    assert config._clean("X_TEST_KEY") == "abcd efgh ijkl mnop"
    assert config._clean("X_TEST_MISSING", "fallback") == "fallback"
