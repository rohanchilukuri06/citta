import logging
from typing import Tuple
from orchestration_context import OrchestrationContext, ExecutionStrategy, EnterpriseIntent

logger = logging.getLogger(__name__)

ACTION_INTENTS = {
    EnterpriseIntent.SCHEDULE_DEMO.value,
    EnterpriseIntent.CREATE_TICKET.value,
    EnterpriseIntent.SEND_PROPOSAL.value,
    EnterpriseIntent.EXECUTE_ACTION.value
}

SECTION_INTENTS = {
    EnterpriseIntent.WORKFLOW.value,
    EnterpriseIntent.BENEFITS.value,
    EnterpriseIntent.FEATURES.value,
    EnterpriseIntent.CAPABILITIES.value,
    EnterpriseIntent.PRICING.value,
    EnterpriseIntent.CONTACT.value,
    EnterpriseIntent.INDUSTRIES.value,
    EnterpriseIntent.TARGET_AUDIENCE.value,
    EnterpriseIntent.FAQ.value,
    EnterpriseIntent.RELATIONSHIPS.value,
    EnterpriseIntent.IMPLEMENTATION.value,
    EnterpriseIntent.USE_CASE.value
}

class ExecutionStrategySelector:
    def __init__(self):
        pass

    def select_strategy(self, ctx: OrchestrationContext) -> OrchestrationContext:
        # Rule 1: Out of Domain
        if ctx.is_out_of_domain:
            ctx.execution_strategy = ExecutionStrategy.OUT_OF_DOMAIN
            ctx.confidence = 1.0
            ctx.reason = "Query is outside CittaAI business domain boundaries."
            ctx.requires_llm = False
            ctx.add_trace("ExecutionStrategySelector", ExecutionStrategy.OUT_OF_DOMAIN.value, ctx.reason)
            return ctx

        # Rule 1b: Enterprise Action Execution
        q_lower = ctx.normalized_query.lower().strip()
        if ctx.intent in ACTION_INTENTS or "schedule" in q_lower or "create a support ticket" in q_lower or "send proposal" in q_lower:
            ctx.execution_strategy = ExecutionStrategy.ACTION
            ctx.confidence = 0.99
            ctx.reason = f"Action intent '{ctx.intent}' requires Phase 4 Enterprise Action Engine execution."
            ctx.requires_llm = False
            ctx.add_trace("ExecutionStrategySelector", ExecutionStrategy.ACTION.value, ctx.reason)
            return ctx

        # Rule 2: Consultative (Business recommendations, collaboration, onboarding, next steps)
        consultative_phrases = [
            "collaborate", "proceed", "work together", "partner", "get started", "how to start", 
            "next steps", "how can i proceed", "ready to work", "engage", "onboard", "how to engage",
            "should we choose", "recommend", "best approach", "how should we", "advice", "guidance"
        ]
        if ctx.intent == EnterpriseIntent.RECOMMENDATION.value or any(phrase in q_lower for phrase in consultative_phrases):
            ctx.execution_strategy = ExecutionStrategy.CONSULTATIVE
            ctx.confidence = 0.95
            ctx.reason = "Query requires consultative business guidance, scenario advice, or onboarding steps."
            ctx.requires_llm = True
            ctx.add_trace("ExecutionStrategySelector", ExecutionStrategy.CONSULTATIVE.value, ctx.reason)
            return ctx

        # Rule 3: Reasoning (Comparison, Suitability, Integration, or Multi-entity synthesis)
        is_multi_entity = len(ctx.session_state.recently_compared_entities) >= 2 or (ctx.matched_entity_ids and len(ctx.matched_entity_ids) >= 2)
        # A confidently resolved entity only downgrades integration questions to a lookup;
        # comparison / suitability questions need synthesis however sure we are of the entity.
        confident_integration_lookup = ctx.intent == EnterpriseIntent.INTEGRATION.value and ctx.resolved_entity_id and ctx.confidence >= 0.9
        if (ctx.intent in [EnterpriseIntent.COMPARISON.value, EnterpriseIntent.SUITABILITY.value, EnterpriseIntent.INTEGRATION.value] or is_multi_entity) and not confident_integration_lookup:
            ctx.execution_strategy = ExecutionStrategy.REASONING
            ctx.confidence = 0.95
            ctx.reason = f"Query intent '{ctx.intent}' requires evidence-grounded reasoning engine synthesis."
            ctx.requires_llm = True
            ctx.add_trace("ExecutionStrategySelector", ExecutionStrategy.REASONING.value, ctx.reason)
            return ctx

        # Rule 4: Section Lookup (Single entity + specific section intent)
        if ctx.resolved_entity_id and ctx.intent in SECTION_INTENTS:
            ctx.execution_strategy = ExecutionStrategy.SECTION
            ctx.confidence = 0.98
            ctx.reason = f"Single entity '{ctx.resolved_entity_id}' + specific section '{ctx.intent}'"
            ctx.requires_llm = False
            ctx.section = ctx.intent.lower()
            ctx.add_trace("ExecutionStrategySelector", ExecutionStrategy.SECTION.value, ctx.reason)
            return ctx

        # Rule 5: Catalog Lookup (Single entity overview or general catalog listing)
        ctx.execution_strategy = ExecutionStrategy.CATALOG
        ctx.confidence = 1.0
        ctx.reason = "Simple catalog entity overview or general offering list lookup."
        ctx.requires_llm = False
        ctx.section = "overview"
        ctx.add_trace("ExecutionStrategySelector", ExecutionStrategy.CATALOG.value, ctx.reason)
        return ctx

_strategy_selector_instance = None

def get_execution_strategy_selector() -> ExecutionStrategySelector:
    global _strategy_selector_instance
    if _strategy_selector_instance is None:
        _strategy_selector_instance = ExecutionStrategySelector()
    return _strategy_selector_instance
