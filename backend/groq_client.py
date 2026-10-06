import os
import time
import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Tuple, Optional
import config

logger = logging.getLogger(__name__)


class GroqClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
        self.model = model or config.GROQ_MODEL or "openai/gpt-oss-20b"
        self.timeout = getattr(config, "TIMEOUT", 60)
        self.max_tokens = getattr(config, "MAX_OUTPUT_TOKENS", 1500)

    def _get_client(self, api_key_override: Optional[str] = None):
        from groq import AsyncGroq
        key = api_key_override if api_key_override is not None else self.api_key
        if not key:
            raise ValueError("Groq API key is missing. Please configure GROQ_API_KEY.")
        # No SDK-level 429 retries with backoff: they eat the first-token budget; FallbackProvider moves on instead
        return AsyncGroq(api_key=key, timeout=self.timeout, max_retries=0)

    def _sanitize_error(self, err_msg: str) -> str:
        """Strip sensitive credentials if present in string."""
        if self.api_key and self.api_key in err_msg:
            err_msg = err_msg.replace(self.api_key, "[REDACTED_API_KEY]")
        return err_msg

    def _classify_error(self, err_text: str, code: Optional[int]) -> Tuple[str, int, bool]:
        """
        Classifies errors into standard error categories and returns:
        (error_type, status_code, is_rate_limit)
        """
        err_lower = err_text.lower()
        if code == 429 or "429" in err_lower or "rate_limit" in err_lower or "quota" in err_lower or "too many requests" in err_lower:
            return "RATE_LIMITED", 429, True
        if code in (400, 401, 403) or "unauthorized" in err_lower or "invalid api key" in err_lower or "api_key_invalid" in err_lower or "authentication" in err_lower:
            return "AUTHENTICATION_ERROR", code or 401, False
        if code == 404 or "not found" in err_lower or "model_not_found" in err_lower:
            return "MODEL_ERROR", 404, False
        if "timeout" in err_lower:
            return "TIMEOUT", 504, False
        if "connection" in err_lower or "network" in err_lower:
            return "NETWORK_ERROR", 503, False
        return "UNKNOWN_ERROR", code or 500, False

    def _count_input_chars(self, messages: List[Dict[str, str]]) -> int:
        return sum(len(m.get("content", "")) for m in messages)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        api_key_override: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generates a chat completion response using AsyncGroq SDK.
        Includes high-resolution latency tracking, fail-fast 429/auth error handling.
        """
        t0 = time.perf_counter()
        target_model = model or self.model
        target_max_tokens = max_tokens or self.max_tokens

        t_prompt_start = time.perf_counter()
        input_chars = self._count_input_chars(messages)
        t_prompt_end = time.perf_counter()
        prompt_build_ms = (t_prompt_end - t_prompt_start) * 1000.0

        try:
            client = self._get_client(api_key_override=api_key_override)
        except Exception as e:
            err_text = self._sanitize_error(str(e))
            logger.error(f"Groq client initialization failed: {err_text}")
            total_ms = (time.perf_counter() - t0) * 1000.0
            return "", {
                "provider": "Groq",
                "model": target_model,
                "success": False,
                "error_type": "AUTHENTICATION_ERROR",
                "status_code": 401,
                "error": err_text,
                "retryable": False,
                "prompt_build_ms": round(prompt_build_ms, 2),
                "generation_ms": 0.0,
                "total_ms": round(total_ms, 2),
                "input_chars": input_chars,
                "estimated_input_tokens": input_chars // 4,
                "output_chars": 0,
                "estimated_output_tokens": 0
            }

        try:
            t_gen_start = time.perf_counter()
            try:
                response = await client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=target_max_tokens,
                    stream=False
                )
            except Exception as primary_err:
                # Cross-provider fallback lives in llm_provider.FallbackProvider (the NVIDIA model used
                # here previously reached end-of-life and returned HTTP 410).
                logger.warning(f"Groq primary call failed ({primary_err}).")
                raise primary_err
            t_gen_end = time.perf_counter()
            generation_ms = (t_gen_end - t_gen_start) * 1000.0
            total_ms = (time.perf_counter() - t0) * 1000.0

            content = response.choices[0].message.content or ""
            usage = getattr(response, "usage", None)

            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else (input_chars // 4)
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else (len(content) // 4)
            total_tokens = getattr(usage, "total_tokens", 0) if usage else (prompt_tokens + completion_tokens)

            metrics = {
                "provider": "Groq",
                "model": target_model,
                "success": True,
                "error_type": "SUCCESS",
                "status_code": 200,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "prompt_build_ms": round(prompt_build_ms, 2),
                "generation_ms": round(generation_ms, 2),
                "total_ms": round(total_ms, 2),
                "input_chars": input_chars,
                "estimated_input_tokens": input_chars // 4,
                "output_chars": len(content),
                "estimated_output_tokens": len(content) // 4
            }

            return content, metrics

        except Exception as e:
            err_text = self._sanitize_error(str(e))
            code = getattr(e, "status_code", None) or getattr(e, "code", None)
            err_type, status_code, is_429 = self._classify_error(err_text, code)

            total_ms = (time.perf_counter() - t0) * 1000.0

            if is_429:
                logger.warning(f"Groq 429 Rate Limit (Fail-Fast): {err_text}")
                return "", {
                    "provider": "Groq",
                    "model": target_model,
                    "success": False,
                    "error_type": "RATE_LIMITED",
                    "status_code": 429,
                    "error": "Groq API rate limit temporarily exceeded (HTTP 429)",
                    "retryable": False,
                    "prompt_build_ms": round(prompt_build_ms, 2),
                    "generation_ms": 0.0,
                    "total_ms": round(total_ms, 2),
                    "input_chars": input_chars,
                    "estimated_input_tokens": input_chars // 4,
                    "output_chars": 0,
                    "estimated_output_tokens": 0
                }

            logger.error(f"Groq API call failed [{err_type}]: {err_text}")
            return "", {
                "provider": "Groq",
                "model": target_model,
                "success": False,
                "error_type": err_type,
                "status_code": status_code,
                "error": err_text,
                "retryable": False,
                "prompt_build_ms": round(prompt_build_ms, 2),
                "generation_ms": 0.0,
                "total_ms": round(total_ms, 2),
                "input_chars": input_chars,
                "estimated_input_tokens": input_chars // 4,
                "output_chars": 0,
                "estimated_output_tokens": 0
            }

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        api_key_override: Optional[str] = None,
        metrics_out: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams completion chunks using AsyncGroq SDK.
        Timestamps first non-empty token for accurate TTFT measurement.
        On API errors, terminates stream cleanly without emitting error text into LLM output.
        """
        t0 = time.perf_counter()
        target_model = model or self.model
        target_max_tokens = max_tokens or self.max_tokens
        input_chars = self._count_input_chars(messages)

        stream_metrics = {
            "provider": "Groq",
            "model": target_model,
            "success": False,
            "error_type": "UNKNOWN_ERROR",
            "status_code": 500,
            "stream_started": False,
            "chunks_received": 0,
            "first_chunk_latency_ms": 0.0,
            "time_to_first_token_ms": 0.0,
            "generation_ms": 0.0,
            "total_stream_latency_ms": 0.0,
            "total_ms": 0.0,
            "final_text_length": 0,
            "output_chars": 0,
            "estimated_output_tokens": 0,
            "input_chars": input_chars,
            "estimated_input_tokens": input_chars // 4
        }

        try:
            client = self._get_client(api_key_override=api_key_override)
        except Exception as e:
            err_text = self._sanitize_error(str(e))
            logger.error(f"Groq streaming client init error: {err_text}")
            stream_metrics.update({
                "error_type": "AUTHENTICATION_ERROR",
                "status_code": 401,
                "total_stream_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                "total_ms": round((time.perf_counter() - t0) * 1000.0, 2)
            })
            if metrics_out is not None:
                metrics_out.update(stream_metrics)
            return

        try:
            stream_metrics["stream_started"] = True
            first_chunk_time = None
            total_chars = 0
            chunks_cnt = 0

            t_gen_start = time.perf_counter()
            try:
                response_stream = await client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=target_max_tokens,
                    stream=True
                )
            except Exception as rate_err:
                if ("rate_limit" in str(rate_err).lower() or "429" in str(rate_err)) and target_model != "openai/gpt-oss-120b":
                    logger.warning(f"Groq primary model '{target_model}' hit rate limit. Auto-falling back to 'openai/gpt-oss-120b'.")
                    target_model = "openai/gpt-oss-120b"
                    stream_metrics["model"] = target_model
                    response_stream = await client.chat.completions.create(
                        model=target_model,
                        messages=messages,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=target_max_tokens,
                        stream=True
                    )
                else:
                    raise rate_err

            async for chunk in response_stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                text = getattr(delta, "content", "") or ""

                if text:
                    if first_chunk_time is None:
                        first_chunk_time = time.perf_counter()
                        ttft_ms = round((first_chunk_time - t0) * 1000.0, 2)
                        stream_metrics["first_chunk_latency_ms"] = ttft_ms
                        stream_metrics["time_to_first_token_ms"] = ttft_ms

                    chunks_cnt += 1
                    total_chars += len(text)
                    yield text

            t_end = time.perf_counter()
            total_ms = round((t_end - t0) * 1000.0, 2)
            gen_ms = round((t_end - t_gen_start) * 1000.0, 2)

            stream_metrics.update({
                "success": True,
                "error_type": "SUCCESS",
                "status_code": 200,
                "chunks_received": chunks_cnt,
                "generation_ms": gen_ms,
                "total_stream_latency_ms": total_ms,
                "total_ms": total_ms,
                "final_text_length": total_chars,
                "output_chars": total_chars,
                "estimated_output_tokens": total_chars // 4
            })
            if metrics_out is not None:
                metrics_out.update(stream_metrics)
            return

        except Exception as e:
            err_text = self._sanitize_error(str(e))
            code = getattr(e, "status_code", None) or getattr(e, "code", None)
            err_type, status_code, _ = self._classify_error(err_text, code)

            stream_metrics.update({
                "success": False,
                "error_type": err_type,
                "status_code": status_code,
                "total_stream_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                "total_ms": round((time.perf_counter() - t0) * 1000.0, 2)
            })
            if metrics_out is not None:
                metrics_out.update(stream_metrics)

            logger.warning(f"Groq Streaming Error [{err_type}]: {err_text}")
            return  # Terminate stream cleanly on error
