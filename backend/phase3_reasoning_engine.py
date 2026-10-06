import time
import logging
from typing import Dict, Any, List, Optional
from orchestration_context import OrchestrationContext
from evidence_builder import get_evidence_builder
from reasoning_planner import get_reasoning_planner
from evidence_selector import get_evidence_selector
from prompt_builder import get_prompt_builder, PROMPT_VERSION
from reasoning_validator import get_reasoning_validator
from structured_formatter import get_structured_formatter

logger = logging.getLogger(__name__)

class Phase3ReasoningEngine:
    def __init__(self, provider=None):
        self.evidence_builder = get_evidence_builder()
        self.reasoning_planner = get_reasoning_planner()
        self.evidence_selector = get_evidence_selector()
        self.prompt_builder = get_prompt_builder()
        self.validator = get_reasoning_validator()
        self.formatter = get_structured_formatter()
        self.provider = provider

    async def execute_reasoning(self, ctx: OrchestrationContext, model: str = "openai/gpt-oss-120b") -> Dict[str, Any]:
        start_time = time.time()

        # 1. Build Raw Evidence Package
        raw_package = self.evidence_builder.build_package(ctx)

        # 2. Formulate Reasoning Plan & Policy
        plan = self.reasoning_planner.plan(ctx)

        # 3. Filter down to Selected Evidence
        selected_evidence = self.evidence_selector.select_evidence(raw_package, plan)

        # 4. Build Versioned Prompt
        messages = self.prompt_builder.build_prompt(ctx.original_query, selected_evidence, plan)

        # 5. Generate Reasoning via LLM Provider or Fallback Formatter
        llm_used = False
        raw_response = ""

        if self.provider:
            try:
                raw_response = await self.provider.generate(messages, model=model, temperature=0.2)
                llm_used = True
            except Exception as e:
                logger.warning(f"LLM Provider reasoning generation failed: {e}. Utilizing fallback formatter.")
                raw_response = self.formatter.format_deterministic_fallback(selected_evidence, plan.reasoning_type.value)
                llm_used = False
        else:
            raw_response = self.formatter.format_deterministic_fallback(selected_evidence, plan.reasoning_type.value)
            llm_used = False

        # 6. Reasoning Post-Validation
        val_result = self.validator.validate(raw_response, selected_evidence)

        final_response_text = raw_response
        if not val_result.is_valid and val_result.fallback_response:
            final_response_text = val_result.fallback_response

        latency_ms = round((time.time() - start_time) * 1000.0, 2)

        # Update Orchestration Context
        ctx.response_text = final_response_text
        ctx.requires_llm = llm_used
        ctx.metrics["prompt_version"] = PROMPT_VERSION
        ctx.metrics["reasoning_type"] = plan.reasoning_type.value
        ctx.metrics["reasoning_confidence"] = val_result.reasoning_confidence
        ctx.metrics["evidence_completeness"] = val_result.evidence_completeness
        ctx.metrics["recommendation_confidence"] = val_result.recommendation_confidence
        ctx.metrics["validation_status"] = "PASSED" if val_result.is_valid else "REJECTED"
        ctx.metrics["latency_ms"] = latency_ms
        ctx.metrics["llm_used"] = llm_used

        ctx.add_trace(
            stage="Phase3ReasoningEngine",
            result="SUCCESS" if val_result.is_valid else "VALIDATION_FAILED",
            reason=f"Type: {plan.reasoning_type.value} | LLM Used: {llm_used} | Conf: {val_result.recommendation_confidence}"
        )

        return {
            "text": final_response_text,
            "source": f"Enterprise Reasoning Engine ({plan.reasoning_type.value})",
            "verified": val_result.is_valid,
            "confidence": val_result.recommendation_confidence,
            "suggestions": [
                f"Tell me more about {plan.target_entity_ids[0].replace('_', ' ').title()}" if plan.target_entity_ids else "What products do you offer?",
                "How does implementation work?",
                "What is the pricing?"
            ],
            "metrics": ctx.metrics
        }

_reasoning_engine_instance = None

def get_phase3_reasoning_engine(provider=None) -> Phase3ReasoningEngine:
    global _reasoning_engine_instance
    if _reasoning_engine_instance is None:
        _reasoning_engine_instance = Phase3ReasoningEngine(provider=provider)
    elif provider is not None:
        _reasoning_engine_instance.provider = provider
    return _reasoning_engine_instance
