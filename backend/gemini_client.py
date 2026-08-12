import os
import time
import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Tuple, Optional
import config

logger = logging.getLogger(__name__)

FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite"
]


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.model = model or config.GEMINI_MODEL or "gemini-2.5-flash-lite"
        self.timeout = getattr(config, "TIMEOUT", 60)
        self.max_output_tokens = getattr(config, "MAX_OUTPUT_TOKENS", 500)

    def _get_client(self, api_key_override: Optional[str] = None):
        from google import genai
        key = api_key_override if api_key_override is not None else self.api_key
        if not key:
            raise ValueError("Gemini API key is missing. Please configure GEMINI_API_KEY.")
        return genai.Client(api_key=key)

    def _format_messages(self, messages: List[Dict[str, str]]) -> Tuple[Optional[str], List[Any], int]:
        from google.genai import types
        system_instruction = None
        contents = []
        total_input_chars = 0

        for m in messages:
            role = m.get("role", "user")
            content_text = m.get("content", "")
            total_input_chars += len(content_text)

            if role == "system":
                if system_instruction:
                    system_instruction += f"\n\n{content_text}"
                else:
                    system_instruction = content_text
            else:
                gemini_role = "model" if role in ("assistant", "model") else "user"
                contents.append(types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=content_text)]
                ))

        if not contents and system_instruction:
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text="Please proceed.")]
            ))

        return system_instruction, contents, total_input_chars

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
        if code == 429 or "429" in err_lower or "resource_exhausted" in err_lower or "quota" in err_lower:
            return "RATE_LIMITED", 429, True
        if code in (400, 401, 403) or "unauthorized" in err_lower or "invalid api key" in err_lower or "api_key_invalid" in err_lower or "api key not valid" in err_lower:
            return "AUTHENTICATION_ERROR", code or 401, False
        if code == 404 or "not found" in err_lower or "no longer available" in err_lower:
            return "MODEL_ERROR", 404, False
        if "timeout" in err_lower:
            return "TIMEOUT", 504, False
        if "connection" in err_lower or "network" in err_lower:
            return "NETWORK_ERROR", 503, False
        return "UNKNOWN_ERROR", code or 500, False

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        api_key_override: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generates a response using Google GenAI SDK with high-resolution latency tracking,
        fail-fast 429 handling, and compact token estimation.
        """
        from google.genai import types
        from google.genai import errors

        t0 = time.perf_counter()
        target_model = model or self.model

        t_prompt_start = time.perf_counter()
        system_instruction, contents, input_chars = self._format_messages(messages)
        t_prompt_end = time.perf_counter()
        prompt_build_ms = (t_prompt_end - t_prompt_start) * 1000.0

        try:
            client = self._get_client(api_key_override=api_key_override)
        except Exception as e:
            err_text = self._sanitize_error(str(e))
            logger.error(f"Gemini client initialization failed: {err_text}")
            total_ms = (time.perf_counter() - t0) * 1000.0
            return "", {
                "provider": "Gemini",
                "model": target_model,
                "success": False,
                "error_type": "AUTHENTICATION_ERROR",
                "status_code": 401,
                "error": err_text,
                "retryable": False,
                "prompt_build_ms": prompt_build_ms,
                "generation_ms": 0.0,
                "total_ms": total_ms,
                "input_chars": input_chars,
                "estimated_input_tokens": input_chars // 4,
                "output_chars": 0
            }

        candidate_models = [target_model]

        for current_model in candidate_models:
            try:
                cfg = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=self.max_output_tokens,
                    system_instruction=system_instruction
                )

                t_gen_start = time.perf_counter()
                res = await client.aio.models.generate_content(
                    model=current_model,
                    contents=contents,
                    config=cfg
                )
                t_gen_end = time.perf_counter()
                generation_ms = (t_gen_end - t_gen_start) * 1000.0
                total_ms = (time.perf_counter() - t0) * 1000.0

                usage = getattr(res, "usage_metadata", None)
                prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else (input_chars // 4)
                completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
                total_tokens = getattr(usage, "total_token_count", 0) if usage else prompt_tokens + completion_tokens

                response_text = res.text or ""
                metrics = {
                    "provider": "Gemini",
                    "model": current_model,
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
                    "output_chars": len(response_text)
                }

                return response_text, metrics

            except errors.APIError as e:
                err_text = self._sanitize_error(str(e))
                code = getattr(e, "code", None)
                err_type, status_code, is_429 = self._classify_error(err_text, code)

                total_ms = (time.perf_counter() - t0) * 1000.0

                if is_429:
                    logger.warning(f"Gemini 429 Rate Limit (Fail-Fast): {err_text}")
                    return "", {
                        "provider": "Gemini",
                        "model": current_model,
                        "success": False,
                        "error_type": "RATE_LIMITED",
                        "status_code": 429,
                        "error": "Gemini API quota temporarily unavailable (HTTP 429)",
                        "retryable": False,
                        "prompt_build_ms": round(prompt_build_ms, 2),
                        "generation_ms": 0.0,
                        "total_ms": round(total_ms, 2),
                        "input_chars": input_chars,
                        "estimated_input_tokens": input_chars // 4,
                        "output_chars": 0
                    }

                if err_type == "AUTHENTICATION_ERROR":
                    logger.error(f"Gemini Auth failure ({status_code}): {err_text}")
                    return "", {
                        "provider": "Gemini",
                        "model": current_model,
                        "success": False,
                        "error_type": "AUTHENTICATION_ERROR",
                        "status_code": status_code,
                        "error": "Authentication failed",
                        "retryable": False,
                        "prompt_build_ms": round(prompt_build_ms, 2),
                        "generation_ms": 0.0,
                        "total_ms": round(total_ms, 2),
                        "input_chars": input_chars,
                        "estimated_input_tokens": input_chars // 4,
                        "output_chars": 0
                    }

                if err_type == "MODEL_ERROR":
                    # Only try fallback if model unavailable / 404
                    logger.warning(f"Gemini model '{current_model}' unavailable ({err_text}). Checking fallback...")
                    for fb_model in FALLBACK_MODELS:
                        if fb_model != current_model:
                            candidate_models.append(fb_model)
                            break
                    continue

                # General API error -> Fail fast
                logger.error(f"Gemini request failed: {err_text}")
                return "", {
                    "provider": "Gemini",
                    "model": current_model,
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
                    "output_chars": 0
                }

            except Exception as e:
                err_text = self._sanitize_error(str(e))
                total_ms = (time.perf_counter() - t0) * 1000.0
                logger.exception("Unexpected error calling Gemini API")
                return "", {
                    "provider": "Gemini",
                    "model": current_model,
                    "success": False,
                    "error_type": "UNKNOWN_ERROR",
                    "status_code": 500,
                    "error": err_text,
                    "retryable": False,
                    "prompt_build_ms": round(prompt_build_ms, 2),
                    "generation_ms": 0.0,
                    "total_ms": round(total_ms, 2),
                    "input_chars": input_chars,
                    "estimated_input_tokens": input_chars // 4,
                    "output_chars": 0
                }

        total_ms = (time.perf_counter() - t0) * 1000.0
        return "", {
            "provider": "Gemini",
            "model": target_model,
            "success": False,
            "error_type": "MODEL_ERROR",
            "status_code": 404,
            "error": "No available Gemini models responded",
            "retryable": False,
            "prompt_build_ms": round(prompt_build_ms, 2),
            "generation_ms": 0.0,
            "total_ms": round(total_ms, 2),
            "input_chars": input_chars,
            "estimated_input_tokens": input_chars // 4,
            "output_chars": 0
        }

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        api_key_override: Optional[str] = None,
        metrics_out: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams completion chunks using Google GenAI SDK.
        On 429 or auth errors, terminates the stream immediately without yielding
        error text as LLM generated content, while populating metrics_out dict.
        """
        from google.genai import types
        from google.genai import errors

        t0 = time.perf_counter()
        target_model = model or self.model
        system_instruction, contents, input_chars = self._format_messages(messages)

        stream_metrics = {
            "provider": "Gemini",
            "model": target_model,
            "success": False,
            "error_type": "UNKNOWN_ERROR",
            "status_code": 500,
            "stream_started": False,
            "chunks_received": 0,
            "first_chunk_latency_ms": 0.0,
            "total_stream_latency_ms": 0.0,
            "final_text_length": 0,
            "input_chars": input_chars,
            "estimated_input_tokens": input_chars // 4
        }

        try:
            client = self._get_client(api_key_override=api_key_override)
        except Exception as e:
            err_text = self._sanitize_error(str(e))
            logger.error(f"Streaming client init error: {err_text}")
            stream_metrics.update({
                "error_type": "AUTHENTICATION_ERROR",
                "status_code": 401,
                "total_stream_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
            })
            if metrics_out is not None:
                metrics_out.update(stream_metrics)
            return  # Terminate stream cleanly

        try:
            cfg = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=self.max_output_tokens,
                system_instruction=system_instruction
            )

            stream_metrics["stream_started"] = True
            first_chunk_time = None
            total_chars = 0
            chunks_cnt = 0

            response_stream = await client.aio.models.generate_content_stream(
                model=target_model,
                contents=contents,
                config=cfg
            )

            async for chunk in response_stream:
                if first_chunk_time is None:
                    first_chunk_time = time.perf_counter()
                    stream_metrics["first_chunk_latency_ms"] = round((first_chunk_time - t0) * 1000.0, 2)

                text = getattr(chunk, "text", "")
                if text:
                    chunks_cnt += 1
                    total_chars += len(text)
                    yield text

            t_end = time.perf_counter()
            stream_metrics.update({
                "success": True,
                "error_type": "SUCCESS",
                "status_code": 200,
                "chunks_received": chunks_cnt,
                "total_stream_latency_ms": round((t_end - t0) * 1000.0, 2),
                "final_text_length": total_chars
            })
            if metrics_out is not None:
                metrics_out.update(stream_metrics)
            return

        except errors.APIError as e:
            err_text = self._sanitize_error(str(e))
            code = getattr(e, "code", None)
            err_type, status_code, _ = self._classify_error(err_text, code)

            stream_metrics.update({
                "success": False,
                "error_type": err_type,
                "status_code": status_code,
                "total_stream_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
            })
            if metrics_out is not None:
                metrics_out.update(stream_metrics)

            logger.warning(f"Gemini Streaming APIError ({status_code}): {err_text}")
            return  # Terminate stream cleanly on error

        except Exception as e:
            err_text = self._sanitize_error(str(e))
            stream_metrics.update({
                "success": False,
                "error_type": "UNKNOWN_ERROR",
                "status_code": 500,
                "total_stream_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
            })
            if metrics_out is not None:
                metrics_out.update(stream_metrics)

            logger.exception("Unexpected error in Gemini streaming")
            return  # Terminate stream cleanly on error
