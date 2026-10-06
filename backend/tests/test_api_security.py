"""
Public-deployment protections on the real FastAPI app: admin auth, input limits, rate limiting, CORS.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from fastapi.testclient import TestClient

import config


@pytest.fixture(scope="module")
def client():
    import server
    return TestClient(server.app)  # no context manager: skips startup model loading


@pytest.mark.parametrize("method,path", [
    ("get", "/api/admin/status"), ("post", "/api/admin/config"), ("post", "/api/admin/reindex"),
    ("get", "/api/admin/documents"), ("delete", "/api/admin/documents/x"), ("get", "/api/admin/chunks"),
    ("get", "/api/admin/analytics"), ("post", "/api/debug/query"), ("post", "/api/tenants/onboard"),
    ("get", "/api/health/details"),
])
def test_admin_routes_require_token(client, monkeypatch, method, path):
    monkeypatch.setattr(config, "ADMIN_API_TOKEN", "s3cret")
    assert getattr(client, method)(path).status_code == 401
    assert getattr(client, method)(path, headers={"X-Admin-Token": "wrong"}).status_code == 401


def test_admin_disabled_in_production_without_token(client, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_API_TOKEN", "")
    monkeypatch.setattr(config, "ENVIRONMENT", "production")
    assert client.get("/api/admin/status").status_code == 503


def test_admin_accepts_valid_token(client, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_API_TOKEN", "s3cret")
    r = client.get("/api/admin/documents", headers={"X-Admin-Token": "s3cret"})
    assert r.status_code not in (401, 503)


@pytest.mark.parametrize("payload", [
    {"session_id": "s", "message": ""},
    {"session_id": "", "message": "hi"},
    {"session_id": "s", "message": "x" * (config.CHAT_MAX_MESSAGE_CHARS + 1)},
    {"session_id": "s" * 200, "message": "hi"},
])
def test_chat_input_limits(client, payload):
    assert client.post("/api/chat", json=payload).status_code == 422


def test_chat_rate_limit_per_session(client, monkeypatch):
    import api_security
    limiter = api_security.ChatRateLimiter(per_session=2, per_ip=100)
    monkeypatch.setattr(api_security, "chat_rate_limiter", limiter)

    class Req:  # minimal request stand-in
        headers = {}
        client = type("C", (), {"host": "1.2.3.4"})()
    limiter.check(Req, "sess")
    limiter.check(Req, "sess")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        limiter.check(Req, "sess")
    assert e.value.status_code == 429
    limiter.check(Req, "other-session")  # other sessions unaffected


@pytest.mark.parametrize("origin,allowed", [
    ("https://cittaai.com", True),
    ("https://citta-jbi1az638-rohanchilukuri06-8472s-projects.vercel.app", True),
    ("https://attacker-site.vercel.app", False),
    ("https://evil.example.com", False),
])
def test_cors_origins(client, origin, allowed):
    r = client.options("/api/chat", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
    assert (r.headers.get("access-control-allow-origin") == origin) is allowed
