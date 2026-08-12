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
    def __init__(self):
        from nvidia_client import NvidiaClient
        self.client = NvidiaClient()

    async def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.client.stream_chat(messages, temperature=temperature):
            yield chunk

    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7
    ) -> str:
        return await self.client.generate(messages, temperature=temperature)



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
    def __init__(self, api_key: str = "", model: str = ""):
        from groq_client import GroqClient
        self.client = GroqClient(api_key=api_key, model=model)

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        target_max_tokens = max_tokens if max_tokens is not None else getattr(config, "MAX_OUTPUT_TOKENS", 350)
        async for chunk in self.client.stream_chat(messages, model=model, temperature=temperature, max_tokens=target_max_tokens):
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


def get_llm_provider(provider_name: str, config: Dict[str, Any]) -> LLMProvider:
    provider_name = provider_name.lower()
    if provider_name == "nvidia":
        return NvidiaProvider()
    elif provider_name == "openai":
        return OpenAIProvider(api_key=config.get("OPENAI_API_KEY", ""))
    elif provider_name == "gemini":
        return GeminiProvider(
            api_key=config.get("GEMINI_API_KEY", ""),
            model=config.get("GEMINI_MODEL", "")
        )
    elif provider_name == "groq":
        return GroqProvider(
            api_key=config.get("GROQ_API_KEY", ""),
            model=config.get("GROQ_MODEL", "")
        )
    elif provider_name == "claude":
        return ClaudeProvider(api_key=config.get("CLAUDE_API_KEY", ""))
    else:
        # Default fallback
        return NvidiaProvider()
