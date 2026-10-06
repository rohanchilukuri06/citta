import contextvars
import abc
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Tuple, Optional
import httpx
import config

logger = logging.getLogger(__name__)

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion chunks."""
        pass

    @abc.abstractmethod
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7
    ) -> str:
        """Get complete chat completion response."""
        pass

    async def warmup(self, model: str) -> None:
        """Warm up the provider by pre-loading models if applicable."""
        pass


class NvidiaProvider(LLMProvider):
    """NVIDIA API Catalog (Nemotron). Uses NVIDIA_MODEL unless a nvidia/* model is passed explicitly."""
    def __init__(self, model: str = ""):
        from nvidia_client import NvidiaClient
        self.client = NvidiaClient(model=model or None)

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.client.stream_chat(messages, temperature=temperature, max_tokens=max_tokens):
            yield chunk

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7
    ) -> str:
        text, _metrics = await self.client.generate(messages, temperature=temperature)
        return text



class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": temperature
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            try:
                                data = json.loads(line[6:])
                                content = data["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                yield f"Error streaming OpenAI response: {str(e)}"

    async def generate(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7
    ) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": temperature
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    return f"Error contacting OpenAI API: {response.text}"
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                return f"Error connecting to OpenAI: {str(e)}"


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = "", model: str = ""):
        from gemini_client import GeminiClient
        self.client = GeminiClient(api_key=api_key, model=model)

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.client.stream_chat(messages, model=model, temperature=temperature):
            yield chunk

    async def generate(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7
    ) -> str:
        res, _metrics = await self.client.generate(messages, model=model, temperature=temperature)
        return res

    async def generate_with_metrics(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7
    ) -> Tuple[str, Dict[str, Any]]:
        return await self.client.generate(messages, model=model, temperature=temperature)



class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        # Format system prompt separate for Claude
        system_text = ""
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            else:
                user_messages.append(m)
                
        payload = {
            "model": model,
            "messages": user_messages,
            "system": system_text,
            "stream": True,
            "max_tokens": 4096,
            "temperature": temperature
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        yield "Error contacting Anthropic API."
                        return
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            try:
                                data = json.loads(data_str)
                                if data.get("type") == "content_block_delta":
                                    chunk = data["delta"].get("text", "")
                                    if chunk:
                                        yield chunk
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                yield f"Error connecting to Anthropic: {str(e)}"

    async def generate(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7
    ) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        system_text = ""
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            else:
                user_messages.append(m)
                
        payload = {
            "model": model,
            "messages": user_messages,
            "system": system_text,
            "stream": False,
            "max_tokens": 4096,
            "temperature": temperature
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    return f"Error contacting Anthropic API: {response.text}"
                return response.json()["content"][0]["text"]
            except Exception as e:
                return f"Error connecting to Anthropic: {str(e)}"


class GroqProvider(LLMProvider):
    # After a 429, skip Groq for a short cooldown so concurrent visitors go straight to the fallback provider
    # instead of each rediscovering the rate limit.
    _cooldown_until: float = 0.0

    def __init__(self, api_key: str = "", model: str = ""):
        from groq_client import GroqClient
        self.client = GroqClient(api_key=api_key, model=model)

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        import time
        if time.monotonic() < GroqProvider._cooldown_until:
            raise ProviderUnavailableError("groq rate-limited (cooling down)")
        target_max_tokens = max_tokens if max_tokens is not None else getattr(config, "MAX_OUTPUT_TOKENS", 1500)
        metrics: Dict[str, Any] = {}
        async for chunk in self.client.stream_chat(messages, model=model, temperature=temperature, max_tokens=target_max_tokens, metrics_out=metrics):
            yield chunk
        if metrics.get("status_code") == 429:
            GroqProvider._cooldown_until = time.monotonic() + float(getattr(config, "GROQ_RATE_LIMIT_COOLDOWN_S", 20))

    async def generate(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7
    ) -> str:
        res, _metrics = await self.client.generate(messages, model=model, temperature=temperature)
        return res

    async def generate_with_metrics(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7
    ) -> Tuple[str, Dict[str, Any]]:
        return await self.client.generate(messages, model=model, temperature=temperature)


class ProviderUnavailableError(RuntimeError):
    """Raised when neither the primary nor the configured secondary LLM produced output."""


class FallbackProvider(LLMProvider):
    """
    Primary -> secondary -> ProviderUnavailableError.

    The primary clients report failures by returning empty output (they log and swallow errors), so an
    empty result counts as a failure. A provider that has not produced its first token within
    LLM_FIRST_TOKEN_TIMEOUT_S (or a full non-streaming answer within LLM_REQUEST_TIMEOUT_S) is abandoned,
    so a stalled or rate-limited provider cannot hold a visitor's request open.
    """
    # Which provider answered is per request: a shared attribute would be overwritten by concurrent visitors.
    _answered_by: "contextvars.ContextVar[Optional[str]]" = contextvars.ContextVar("fallback_answered_by", default=None)

    @property
    def last_provider(self) -> Optional[str]:
        return self._answered_by.get()

    @last_provider.setter
    def last_provider(self, value: Optional[str]) -> None:
        self._answered_by.set(value)

    def __init__(self, primary: LLMProvider, secondary: Optional[LLMProvider], secondary_model: str = "", names: Tuple[str, str] = ("primary", "secondary")):
        import config as app_config
        self.primary = primary
        self.secondary = secondary
        self.secondary_model = secondary_model
        self.names = names
        self.last_provider: Optional[str] = None
        self.first_token_timeout = float(getattr(app_config, "LLM_FIRST_TOKEN_TIMEOUT_S", 8))
        self.request_timeout = float(getattr(app_config, "LLM_REQUEST_TIMEOUT_S", 15))

    async def _guarded_stream(self, provider: LLMProvider, messages, model, temperature, max_tokens):
        import asyncio
        agen = provider.generate_stream(messages, model=model, temperature=temperature, max_tokens=max_tokens).__aiter__()
        try:
            first = await asyncio.wait_for(agen.__anext__(), self.first_token_timeout)
        except StopAsyncIteration:
            return
        except BaseException:
            try:
                await agen.aclose()
            except Exception:
                pass
            raise
        yield first
        async for chunk in agen:
            yield chunk

    async def generate_stream(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        emitted = False
        self.last_provider = None
        try:
            async for chunk in self._guarded_stream(self.primary, messages, model, temperature, max_tokens):
                text = chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
                if text:
                    emitted = True
                    self.last_provider = self.names[0]
                    yield chunk
        except Exception as e:
            if emitted:
                raise
            logger.warning(json.dumps({"event": "provider_fallback", "from": self.names[0], "error": f"{type(e).__name__}: {e}"[:300]}))
        if emitted:
            return
        if self.secondary is None:
            raise ProviderUnavailableError(f"{self.names[0]} produced no output and no secondary provider is configured")
        logger.warning(json.dumps({"event": "provider_fallback", "from": self.names[0], "to": self.names[1], "model": self.secondary_model}))
        try:
            async for chunk in self._guarded_stream(self.secondary, messages, self.secondary_model, temperature, max_tokens):
                text = chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
                if text:
                    emitted = True
                    # nested chains report the provider that actually answered
                    self.last_provider = getattr(self.secondary, "last_provider", None) or self.names[1]
                    yield chunk
        except Exception as e:
            if emitted:
                raise
            raise ProviderUnavailableError(f"{self.names[1]} failed: {type(e).__name__}: {e}"[:300]) from e
        if not emitted:
            raise ProviderUnavailableError(f"{self.names[0]} and {self.names[1]} both produced no output")

    async def generate(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> str:
        import asyncio
        try:
            out = await asyncio.wait_for(self.primary.generate(messages, model=model, temperature=temperature), self.request_timeout)
            if out and str(out).strip():
                return out
            err = "empty output"
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
        if self.secondary is None:
            raise ProviderUnavailableError(f"{self.names[0]} failed ({err[:200]}) and no secondary provider is configured")
        logger.warning(json.dumps({"event": "provider_fallback", "from": self.names[0], "to": self.names[1], "error": err[:300]}))
        try:
            out = await asyncio.wait_for(self.secondary.generate(messages, model=self.secondary_model, temperature=temperature), self.request_timeout)
        except Exception as e:
            raise ProviderUnavailableError(f"{self.names[1]} failed: {type(e).__name__}: {e}"[:300]) from e
        if not out or not str(out).strip():
            raise ProviderUnavailableError(f"{self.names[0]} and {self.names[1]} both failed")
        return out


def get_llm_provider(provider_name: str, config: Dict[str, Any]) -> LLMProvider:
    provider_name = provider_name.lower()
    if provider_name in ("groq", "nvidia"):
        import config as app_config
        if provider_name == "groq":
            primary: LLMProvider = GroqProvider(api_key=config.get("GROQ_API_KEY", ""), model=config.get("GROQ_MODEL", ""))
            primary_name = "groq"
        else:
            primary, primary_name = NvidiaProvider(model=app_config.NVIDIA_MODEL), "nemotron"
        # Ordered fallback chain, e.g. "nvidia,gemini": Groq -> Nemotron 3 (NVIDIA) -> Gemini -> provider-unavailable
        chain = []
        for name in [n.strip() for n in str(getattr(app_config, "LLM_FALLBACK_PROVIDER", "none")).lower().split(",") if n.strip()]:
            if name == provider_name:
                continue
            if name == "nvidia" and (getattr(app_config, "NVIDIA_API_KEY", "")):
                chain.append((NvidiaProvider(model=app_config.NVIDIA_MODEL), app_config.NVIDIA_MODEL, "nemotron"))
            elif name == "groq" and (config.get("GROQ_API_KEY") or getattr(app_config, "GROQ_API_KEY", "")):
                chain.append((GroqProvider(api_key=config.get("GROQ_API_KEY") or app_config.GROQ_API_KEY, model=app_config.GROQ_MODEL),
                              app_config.GROQ_MODEL, "groq"))
            elif name == "gemini" and (config.get("GEMINI_API_KEY") or getattr(app_config, "GEMINI_API_KEY", "")):
                chain.append((GeminiProvider(api_key=config.get("GEMINI_API_KEY") or app_config.GEMINI_API_KEY, model=app_config.GEMINI_MODEL),
                              app_config.GEMINI_MODEL, "gemini"))
        if not chain:
            # Still wrapped: keeps the stall timeouts and the controlled provider-unavailable path
            return FallbackProvider(primary, None, "", (primary_name, "none"))
        # Build the chain from the back: FallbackProvider(primary, FallbackProvider(second, third))
        secondary, secondary_model, secondary_name = chain[-1]
        for prov, model_name, name in reversed(chain[:-1]):
            secondary = FallbackProvider(prov, secondary, secondary_model, (name, secondary_name))
            secondary_model, secondary_name = model_name, name
        return FallbackProvider(primary, secondary, secondary_model, (primary_name, secondary_name))
    elif provider_name == "openai":
        return OpenAIProvider(api_key=config.get("OPENAI_API_KEY", ""))
    elif provider_name == "gemini":
        return GeminiProvider(
            api_key=config.get("GEMINI_API_KEY", ""),
            model=config.get("GEMINI_MODEL", "")
        )
    elif provider_name == "claude":
        return ClaudeProvider(api_key=config.get("CLAUDE_API_KEY", ""))
    else:
        # Default fallback
        return NvidiaProvider()
