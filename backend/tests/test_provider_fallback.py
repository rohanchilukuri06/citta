"""
Provider fallback: Groq -> Gemini -> controlled provider-unavailable state. No dead NVIDIA hop.
"""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from llm_provider import FallbackProvider, ProviderUnavailableError


class Fake:
    def __init__(self, text="", raises=False):
        self.text, self.raises, self.calls = text, raises, 0

    async def generate_stream(self, messages, model, temperature=0.7, max_tokens=None):
        self.calls += 1
        if self.raises:
            raise RuntimeError("boom")
        if self.text:
            yield self.text

    async def generate(self, messages, model, temperature=0.7):
        self.calls += 1
        if self.raises:
            raise RuntimeError("boom")
        return self.text


def _stream(p):
    async def run():
        return "".join([c async for c in p.generate_stream([{"role": "user", "content": "hi"}], model="m")])
    return asyncio.run(run())


def test_primary_success_does_not_touch_secondary():
    primary, secondary = Fake("groq answer"), Fake("gemini answer")
    assert _stream(FallbackProvider(primary, secondary, "g")) == "groq answer"
    assert secondary.calls == 0


@pytest.mark.parametrize("primary", [Fake(""), Fake(raises=True)])
def test_empty_or_failing_primary_falls_back(primary):
    secondary = Fake("gemini answer")
    assert _stream(FallbackProvider(primary, secondary, "g")) == "gemini answer"
    assert asyncio.run(FallbackProvider(primary, secondary, "g").generate([], model="m")) == "gemini answer"


def test_both_failing_is_a_controlled_error():
    with pytest.raises(ProviderUnavailableError):
        _stream(FallbackProvider(Fake(""), Fake(""), "g"))
    with pytest.raises(ProviderUnavailableError):
        asyncio.run(FallbackProvider(Fake(raises=True), None, "").generate([], model="m"))


def test_groq_client_has_no_nvidia_fallback():
    src = (ROOT_DIR / "groq_client.py").read_text(encoding="utf-8")
    assert "NvidiaClient" not in src


def test_gemini_fallback_list_is_bounded_and_not_retired():
    import gemini_client
    assert "gemini-2.0-flash" not in gemini_client.FALLBACK_MODELS
    assert "gemini-1.5-flash-8b" not in gemini_client.FALLBACK_MODELS


def test_factory_wires_gemini_as_secondary(monkeypatch):
    import config
    from llm_provider import get_llm_provider
    monkeypatch.setattr(config, "LLM_FALLBACK_PROVIDER", "gemini")
    p = get_llm_provider("groq", {"GROQ_API_KEY": "x", "GEMINI_API_KEY": "y"})
    assert isinstance(p, FallbackProvider) and p.secondary is not None and p.names == ("groq", "gemini")
    monkeypatch.setattr(config, "LLM_FALLBACK_PROVIDER", "none")
    p = get_llm_provider("groq", {"GROQ_API_KEY": "x", "GEMINI_API_KEY": "y"})
    assert p.secondary is None


def test_pipeline_serves_evidence_when_all_providers_fail():
    import config
    config.SEMANTIC_LLM_ADJUDICATION = False
    from semantic_chat_pipeline import SemanticChatPipeline
    from query_intelligence_engine import QueryIntelligenceEngine
    pipe = SemanticChatPipeline(provider=FallbackProvider(Fake(""), Fake(""), "g"), engine=QueryIntelligenceEngine(enable_llm=False))

    async def run():
        text, done = "", {}
        async for c in pipe.stream("s", "What can Education OS do?", "m"):
            if c.get("done"):
                done = c
            else:
                text += c["text"]
        return text, done
    text, done = asyncio.run(run())
    assert done["metrics"]["provider_unavailable"] is True
    assert "College LMS" in text  # verified registry capability, not invented text


class Stalling:
    """A provider that never produces a first token (e.g. stuck behind a rate limit)."""
    async def generate_stream(self, messages, model, temperature=0.7, max_tokens=None):
        import asyncio
        await asyncio.sleep(60)
        yield "late"

    async def generate(self, messages, model, temperature=0.7):
        import asyncio
        await asyncio.sleep(60)
        return "late"


def test_stalled_primary_falls_back_within_deadline():
    import time
    p = FallbackProvider(Stalling(), Fake("gemini answer"), "g")
    p.first_token_timeout = p.request_timeout = 0.5
    t0 = time.perf_counter()
    assert _stream(p) == "gemini answer"
    assert asyncio.run(p.generate([], model="m")) == "gemini answer"
    assert time.perf_counter() - t0 < 5


class Slow(Fake):
    async def generate_stream(self, messages, model, temperature=0.7, max_tokens=None):
        self.calls += 1
        if self.raises:
            raise RuntimeError("boom")
        yield self.text
        await asyncio.sleep(0.05)
        yield " more"


def test_answered_by_is_per_request_under_concurrency():
    # Two overlapping requests: A is answered by the primary, B (primary rate-limited) by the fallback.
    # Each must report its own provider, not whichever request wrote last.
    def chain(primary_fails):
        return FallbackProvider(Slow("groq", raises=primary_fails), Slow("nemotron"), "n", names=("groq", "nemotron"))

    async def ask(p):
        out = "".join([c async for c in p.generate_stream([], model="m")])
        return out, p.last_provider

    async def run():
        return await asyncio.gather(ask(chain(False)), ask(chain(True)))

    (text_a, by_a), (text_b, by_b) = asyncio.run(run())
    assert text_a.startswith("groq") and by_a == "groq"
    assert text_b.startswith("nemotron") and by_b == "nemotron"


def test_groq_rate_limit_starts_cooldown_so_next_request_skips_it():
    from llm_provider import GroqProvider

    class RateLimitedClient:
        calls = 0

        async def stream_chat(self, messages, model=None, temperature=0.7, max_tokens=None, metrics_out=None):
            RateLimitedClient.calls += 1
            metrics_out.update({"status_code": 429})
            return
            yield

    groq = GroqProvider.__new__(GroqProvider)
    groq.client = RateLimitedClient()
    GroqProvider._cooldown_until = 0.0
    try:
        chain = FallbackProvider(groq, Fake("nemotron answer"), "n", names=("groq", "nemotron"))
        assert _stream(chain) == "nemotron answer"
        assert _stream(chain) == "nemotron answer"
        assert RateLimitedClient.calls == 1  # second request did not hit Groq again
    finally:
        GroqProvider._cooldown_until = 0.0


def test_nvidia_empty_stream_is_retried(monkeypatch):
    # NVIDIA sometimes answers 200 with an empty stream; the client retries instead of returning nothing
    import nvidia_client

    bodies = [[], ['data: {"choices":[{"delta":{"content":"hello"}}]}', "data: [DONE]"]]

    class Resp:
        status_code = 200

        def __init__(self, lines):
            self.lines = lines

        async def aiter_lines(self):
            for line in self.lines:
                yield line

    class Ctx:
        def __init__(self, lines):
            self.lines = lines

        async def __aenter__(self):
            return Resp(self.lines)

        async def __aexit__(self, *a):
            return False

    class Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def stream(self, *a, **k):
            return Ctx(bodies.pop(0))

    monkeypatch.setattr(nvidia_client.httpx, "AsyncClient", Client)
    monkeypatch.setattr(nvidia_client, "RETRY_BACKOFF_S", 0)
    monkeypatch.setattr(nvidia_client.config, "NVIDIA_API_KEY", "test-key", raising=False)

    async def run():
        return "".join([c async for c in nvidia_client.NvidiaClient().stream_chat([{"role": "user", "content": "hi"}])])

    assert asyncio.run(run()) == "hello"
    assert bodies == []
