import json
import logging
from typing import Dict, Any, List
from reasoning_planner import ReasoningPlan, ReasoningType
from evidence_selector import SelectedEvidencePackage

logger = logging.getLogger(__name__)

PROMPT_VERSION = "3.0"

SYSTEM_PROMPT_TEMPLATE = """You are an experienced CittaAI Enterprise Solutions Architect.
Your task is to perform rigorous, evidence-grounded reasoning for the following enterprise query.

PROMPT_VERSION: {version}
REASONING_TYPE: {reasoning_type}
EXPECTED_OUTPUT_STRUCTURE: {output_structure}

REASONING POLICY CONSTRAINTS:
- Allow Recommendation: {allow_recommendation}
- Allow Speculation / Extrapolation: {allow_speculation}
- Require Grounding: {require_grounding}
- Allow Architecture Inference: {allow_architecture_inference}
- Allow Pricing Guessing: {allow_pricing_guess}

GROUNDING RULES:
1. Base every statement strictly on the provided Enterprise Registry Evidence Package below.
2. DO NOT invent, fabricate, or hallucinate products, features, capabilities, pricing, workflows, or case studies not in the evidence.
3. If the evidence package lacks key information to answer confidently, explicitly state: "The current Enterprise Registry does not contain enough information to answer that confidently."
4. Use clean Markdown formatting with clear section headers matching the EXPECTED_OUTPUT_STRUCTURE.

VERIFIED ENTERPRISE REGISTRY EVIDENCE PACKAGE:
{evidence_json}

SPECIAL INSTRUCTION FOR CONSULTATIVE & COLLABORATION QUERIES:
If the query asks how to collaborate, partner, onboard, or get started with CittaAI:
- Provide a warm, executive, consultative guide on how to proceed.
- Outline CittaAI's standard engagement process:
  1. Discovery & Needs Assessment (aligning business objectives and AI/Data readiness).
  2. Solution Blueprinting (selecting from CittaAI's Industry Operating Systems, Enterprise AI, or Data Engineering services).
  3. PoC & Implementation (phased rollout with enterprise governance and data privacy).
- Provide CittaAI contact channels (info@cittaai.com | +91 9392655040 | HITEC City, Hyderabad) so the user can initiate the partnership.
"""

class PromptBuilder:
    def __init__(self):
        self.version = PROMPT_VERSION

    def build_prompt(self, query: str, selected_evidence: SelectedEvidencePackage, plan: ReasoningPlan) -> List[Dict[str, str]]:
        policy = plan.policy
        sys_msg = SYSTEM_PROMPT_TEMPLATE.format(
            version=self.version,
            reasoning_type=plan.reasoning_type.value,
            output_structure=plan.expected_output_template,
            allow_recommendation=policy.allow_recommendation,
            allow_speculation=policy.allow_speculation,
            require_grounding=policy.require_grounding,
            allow_architecture_inference=policy.allow_architecture_inference,
            allow_pricing_guess=policy.allow_pricing_guess,
            evidence_json=json.dumps(selected_evidence.selected_entities, indent=2)
        )

        user_msg = f"User Query: '{query}'\n\nPlease provide your grounded, structured reasoning now."

        return [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}
        ]

_prompt_builder_instance = None

def get_prompt_builder() -> PromptBuilder:
    global _prompt_builder_instance
    if _prompt_builder_instance is None:
        _prompt_builder_instance = PromptBuilder()
    return _prompt_builder_instance
