import os
import json
import time
import logging
import asyncio
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple
import config

# Transient NVIDIA API errors (rate limit, busy upstream) get short retries; Nemotron may be the only provider
RETRYABLE_STATUS = {429, 502, 503, 504}
RETRY_ATTEMPTS = 2
RETRY_BACKOFF_S = 0.75

logger = logging.getLogger(__name__)


class NvidiaUnavailableError(RuntimeError):
    """Raised instead of returning placeholder text, so callers (FallbackProvider) can fall back."""


class NvidiaClient:
    """
    NVIDIA API Catalog client (OpenAI-compatible) for Nemotron models.

    Failures raise NvidiaUnavailableError; the previous version yielded "temporarily unavailable" text
    as if the model had written it, which a fallback chain would have treated as a real answer.
    """
    def __init__(self, model: Optional[str] = None):
        self._model = model
        self.base_url = config.NVIDIA_BASE_URL
        self.timeout = httpx.Timeout(float(getattr(config, "NVIDIA_READ_TIMEOUT_S", 60)), connect=10.0)

    @property
    def model(self) -> str:
        return self._model or getattr(config, "NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")

    def _get_headers(self) -> Dict[str, str]:
        api_key = config.NVIDIA_API_KEY or os.environ.get("NVIDIA_API_KEY", "")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _payload(self, messages: List[Dict[str, str]], temperature: float, stream: bool, max_tokens: Optional[int]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "top_p": config.TOP_P,
            "max_tokens": max_tokens or config.MAX_TOKENS,
        }
        if "nemotron" in self.model:
            # Nemotron reasoning ("thinking") is off by default: sub-second first token instead of long reasoning traces
            thinking = str(getattr(config, "NVIDIA_ENABLE_THINKING", "false")).lower() in ("true", "1", "yes")
            payload["chat_template_kwargs"] = {"enable_thinking": thinking}
        return payload

    async def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.4,
                          max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"
        payload = self._payload(messages, temperature, True, max_tokens)
        for attempt in range(RETRY_ATTEMPTS + 1):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                    if response.status_code in RETRYABLE_STATUS and attempt < RETRY_ATTEMPTS:
                        logger.warning(f"NVIDIA API {response.status_code} (busy / rate limited); retry {attempt + 1}")
                        await asyncio.sleep(RETRY_BACKOFF_S * (attempt + 1))
                        continue
                    if response.status_code != 200:
                        err = (await response.aread()).decode("utf-8", errors="ignore")[:300]
                        raise NvidiaUnavailableError(f"NVIDIA API {response.status_code} for {self.model}: {err}")
                    emitted = False
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            chunk = (data.get("choices") or [{}])[0].get("delta", {}).get("content") or ""
                        except json.JSONDecodeError:
                            continue
                        if chunk:
                            emitted = True
                            yield chunk
                    if emitted:
                        return
                    # The API intermittently answers 200 with an empty stream (no content, no finish reason); retry it
                    if attempt < RETRY_ATTEMPTS:
                        logger.warning(f"NVIDIA API returned an empty stream; retry {attempt + 1}")
                        await asyncio.sleep(RETRY_BACKOFF_S * (attempt + 1))
                        continue
                    raise NvidiaUnavailableError(f"NVIDIA API returned an empty stream for {self.model}")
        raise NvidiaUnavailableError(f"NVIDIA API busy / rate limited for {self.model}")

    async def generate(self, messages: List[Dict[str, str]], temperature: float = 0.4,
                       max_tokens: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
        url = f"{self.base_url}/chat/completions"
        payload = self._payload(messages, temperature, False, max_tokens)
        t0 = time.time()
        for attempt in range(RETRY_ATTEMPTS + 1):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self._get_headers(), json=payload)
            if response.status_code in RETRYABLE_STATUS and attempt < RETRY_ATTEMPTS:
                logger.warning(f"NVIDIA API {response.status_code} (busy / rate limited); retry {attempt + 1}")
                await asyncio.sleep(RETRY_BACKOFF_S * (attempt + 1))
                continue
            if response.status_code != 200:
                raise NvidiaUnavailableError(f"NVIDIA API {response.status_code} for {self.model}: {response.text[:300]}")
            data = response.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            if not content.strip() and attempt < RETRY_ATTEMPTS:
                logger.warning(f"NVIDIA API returned an empty completion; retry {attempt + 1}")
                await asyncio.sleep(RETRY_BACKOFF_S * (attempt + 1))
                continue
            usage = data.get("usage", {})
            return content, {"provider": "NVIDIA", "model": self.model, "prompt_tokens": usage.get("prompt_tokens", 0),
                             "completion_tokens": usage.get("completion_tokens", 0),
                             "total_llm_duration_ms": int((time.time() - t0) * 1000)}
        raise NvidiaUnavailableError(f"NVIDIA API rate limited for {self.model}")
