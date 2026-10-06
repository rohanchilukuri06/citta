import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from orchestration_context import OrchestrationContext, EnterpriseIntent

logger = logging.getLogger(__name__)

class ReasoningType(str, Enum):
    COMPARISON = "COMPARISON"
    SUITABILITY = "SUITABILITY"
    CONSULTATIVE = "CONSULTATIVE"
    INTEGRATION = "INTEGRATION"
    IMPLEMENTATION = "IMPLEMENTATION"
    USE_CASE = "USE_CASE"
    TRADE_OFF = "TRADE_OFF"

class ReasoningPolicy(BaseModel):
    allow_recommendation: bool = True
    allow_speculation: bool = False
    require_grounding: bool = True
    allow_architecture_inference: bool = False
    allow_pricing_guess: bool = False
    allow_industry_mapping: bool = False
    allow_capability_creation: bool = False

class ReasoningPlan(BaseModel):
    reasoning_type: ReasoningType
    target_entity_ids: List[str] = Field(default_factory=list)
    required_sections: List[str] = Field(default_factory=list)
    expected_output_template: str
    policy: ReasoningPolicy = Field(default_factory=ReasoningPolicy)

PLAN_CONFIGS: Dict[ReasoningType, Dict[str, Any]] = {
    ReasoningType.COMPARISON: {
        "required_sections": ["overview", "benefits", "features", "best_for", "pricing", "related_entities"],
        "expected_output_template": "Executive Summary | Comparison Table | Strengths | Differences | Recommendation",
        "policy": ReasoningPolicy(allow_recommendation=True, allow_speculation=False, require_grounding=True)
    },
    ReasoningType.SUITABILITY: {
        "required_sections": ["overview", "best_for", "benefits", "how_it_works", "features"],
        "expected_output_template": "Requirements | Evidence | Analysis | Recommendation",
        "policy": ReasoningPolicy(allow_recommendation=True, allow_speculation=False, require_grounding=True)
    },
    ReasoningType.CONSULTATIVE: {
        "required_sections": ["overview", "features", "benefits", "best_for", "case_studies"],
        "expected_output_template": "Business Context | Matching Solutions | Evaluation | Recommended Solution | Reasoning",
        "policy": ReasoningPolicy(allow_recommendation=True, allow_speculation=False, require_grounding=True)
    },
    ReasoningType.INTEGRATION: {
        "required_sections": ["overview", "integrations", "how_it_works", "features", "related_entities"],
        "expected_output_template": "Architecture Overview | Interaction Points | Benefits | Implementation Considerations",
        "policy": ReasoningPolicy(allow_architecture_inference=True, allow_pricing_guess=False, require_grounding=True)
    },
    ReasoningType.IMPLEMENTATION: {
        "required_sections": ["overview", "implementation", "how_it_works", "integrations"],
        "expected_output_template": "Architecture Overview | Deployment Steps | Prerequisites | Rollout Phases",
        "policy": ReasoningPolicy(allow_architecture_inference=True, allow_pricing_guess=False, require_grounding=True)
    },
    ReasoningType.USE_CASE: {
        "required_sections": ["overview", "best_for", "case_studies", "features", "benefits"],
        "expected_output_template": "Sector Challenge | Solution Application | Key Features & Benefits | Quantified Impact",
        "policy": ReasoningPolicy(allow_industry_mapping=True, allow_capability_creation=False, require_grounding=True)
    },
    ReasoningType.TRADE_OFF: {
        "required_sections": ["overview", "benefits", "features", "pricing", "best_for"],
        "expected_output_template": "Advantages | Disadvantages | Best Fit",
        "policy": ReasoningPolicy(allow_recommendation=True, allow_speculation=False, require_grounding=True)
    }
}

class ReasoningPlanner:
    def __init__(self):
        pass

    def plan(self, ctx: OrchestrationContext) -> ReasoningPlan:
        q_lower = ctx.normalized_query.lower().strip()
        intent = ctx.intent

        # Determine Reasoning Type
        r_type = ReasoningType.CONSULTATIVE
        if intent == EnterpriseIntent.COMPARISON.value or "compare" in q_lower or " vs " in q_lower or "versus" in q_lower:
            r_type = ReasoningType.COMPARISON
        elif intent == EnterpriseIntent.SUITABILITY.value or "suitable" in q_lower or "work for" in q_lower or "suit" in q_lower:
            r_type = ReasoningType.SUITABILITY
        elif intent == EnterpriseIntent.INTEGRATION.value or "integrate" in q_lower or "connect" in q_lower:
            r_type = ReasoningType.INTEGRATION
        elif intent == EnterpriseIntent.IMPLEMENTATION.value or "implement" in q_lower or "deploy" in q_lower or "setup" in q_lower:
            r_type = ReasoningType.IMPLEMENTATION
        elif intent == EnterpriseIntent.USE_CASE.value or "hospital" in q_lower or "university" in q_lower or "help a" in q_lower:
            r_type = ReasoningType.USE_CASE
        elif "trade-off" in q_lower or "pros and cons" in q_lower:
            r_type = ReasoningType.TRADE_OFF

        cfg = PLAN_CONFIGS.get(r_type, PLAN_CONFIGS[ReasoningType.CONSULTATIVE]).copy()

        # Tailor template for collaboration, onboarding, partnership, and next-steps intent
        if any(w in q_lower for w in ["collaborate", "proceed", "partner", "get started", "how to start", "next steps", "onboard", "work together"]):
            cfg["expected_output_template"] = "Engagement Overview | How to Collaborate & Onboard | Contact & Next Steps"

        target_entities = []
        if ctx.resolved_entity_id:
            target_entities.append(ctx.resolved_entity_id)
        if ctx.matched_entity_ids:
            target_entities.extend(ctx.matched_entity_ids)
        if ctx.session_state.recently_compared_entities:
            target_entities.extend(ctx.session_state.recently_compared_entities)
        target_entities = list(dict.fromkeys(target_entities))

        reasoning_plan = ReasoningPlan(
            reasoning_type=r_type,
            target_entity_ids=target_entities,
            required_sections=cfg["required_sections"],
            expected_output_template=cfg["expected_output_template"],
            policy=cfg["policy"]
        )

        ctx.add_trace(
            stage="ReasoningPlanner",
            result=f"Plan created for reasoning type: {r_type.value}",
            reason=f"Entities: {target_entities} | Template: {cfg['expected_output_template']}"
        )

        return reasoning_plan

_reasoning_planner_instance = None

def get_reasoning_planner() -> ReasoningPlanner:
    global _reasoning_planner_instance
    if _reasoning_planner_instance is None:
        _reasoning_planner_instance = ReasoningPlanner()
    return _reasoning_planner_instance
