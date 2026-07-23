from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class ConversationContext:
    session_id: str
    turn_count: int = 0
    current_stage: str = "Greeting"
    history: List[Dict[str, str]] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    active_entity_id: Optional[str] = None
    active_registry: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

from enum import Enum
from typing import Dict, Any, List, Optional, Union

class BusinessIntent(Enum):
    OVERVIEW = "Overview"
    AVAILABILITY = "Availability"
    FEATURES = "Features"
    BENEFITS = "Benefits"
    WORKFLOW = "Workflow"
    ARCHITECTURE = "Architecture"
    PRICING = "Pricing"
    INTEGRATION = "Integration"
    COMPARISON = "Comparison"
    INDUSTRIES = "Industries"
    CASE_STUDIES = "Case Studies"
    IMPLEMENTATION = "Implementation"
    SUPPORT = "Support"
    CONTACT = "Contact"
    LEADERSHIP = "Leadership"
    DEMO_REQUEST = "Demo Request"
    REQUIREMENT_GATHERING = "Requirement Gathering"
    RECOMMENDATION = "Recommendation"
    PROBLEM_STATEMENT = "Problem Statement"
    COMPLIANCE = "Compliance"
    SECURITY = "Security"
    MIGRATION = "Migration"
    LICENSING = "Licensing"
    SCALABILITY = "Scalability"
    UNKNOWN = "Unknown"

class ConversationalIntent(Enum):
    GREETING = "Greeting"
    CONFIRMATION = "Confirmation"
    CLARIFICATION = "Clarification"
    CONTINUE_TOPIC = "Continue Previous Topic"
    GOODBYE = "Goodbye"
    SMALL_TALK = "Small Talk"
    NONE = "None"

class RolePersona(Enum):
    EXECUTIVE_DECISION_MAKER = "Executive Decision-Maker"
    TECHNICAL_ARCHITECT = "Technical Architect"
    DEVELOPER = "Developer"
    BUSINESS_FUNCTIONAL = "Business Functional"
    OPERATIONS = "Operations"
    MARKETING = "Marketing"
    ACADEMIC_STUDENT = "Academic / Student"
    RECRUITER = "Recruiter"
    INVESTOR = "Investor"
    UNKNOWN = "Unknown / General"

class RelationshipPersona(Enum):
    PROSPECTIVE_CUSTOMER = "Prospective Customer"
    EXISTING_CUSTOMER = "Existing Customer"
    PARTNER = "Partner"
    UNKNOWN = "Unknown"

@dataclass
class PersonaSignal:
    provider: str        # LanguageProvider, TerminologyProvider, QuestionStyleProvider, HistoryProvider
    feature: str
    weight: float        # Positive for supporting, negative for contradictory
    source_turn: int

@dataclass
class CommunicationPreferences:
    technical_depth: str       # Executive, Deep Technical, Functional, Introductory
    executive_focus: float     # 0.0 to 1.0 (ROI / Business Outcome priority)
    detail_density: str        # Concise, Balanced, Detailed
    prefer_code_snippets: bool = False
    prefer_case_studies: bool = False

@dataclass
class PersonaProfile:
    role_probabilities: Dict[RolePersona, float]
    primary_role: RolePersona
    relationship: RelationshipPersona
    relationship_confidence: float
    communication_preferences: CommunicationPreferences
    profile_stability: float   # 0.0 (Uncertain) to 1.0 (Highly Settled)
    reasoning: str
    detected_signals: List[PersonaSignal] = field(default_factory=list)
    turn_history: List[Dict[str, Any]] = field(default_factory=list)

class IntentSource(Enum):
    MESSAGE = "Message"
    MEMORY = "Memory"
    CONVERSATION_CONTEXT = "Conversation Context"
    KNOWLEDGE_BASE = "Knowledge Base"

@dataclass
class EntityNode:
    entity_id: str
    name: str
    registry: str
    mention_count: int
    first_turn: int
    last_turn: int

@dataclass
class CoreferenceCandidate:
    entity: EntityNode
    confidence: float
    reason: str

@dataclass
class CoreferenceResult:
    original_query: str
    resolved_query: str
    selected_entity: Optional[EntityNode]
    candidates: List[CoreferenceCandidate]
    pronouns_detected: List[str]
    confidence: float
    requires_clarification: bool = False

@dataclass
class QuestionSignature:
    entity_id: str
    intent: str
    signature_hash: str
    answered_turn: int

@dataclass
class FollowUpOpportunity:
    topic: str
    priority: float
    reason: str
    suggested_turn: int

@dataclass
class WorkingMemory:
    current_entity: Optional[EntityNode] = None
    active_registry: Optional[str] = None
    last_intent: Optional[str] = None
    recent_entities: List[EntityNode] = field(default_factory=list)

@dataclass
class CustomerFacts:
    industry: Optional[str] = None
    company_size: Optional[str] = None
    timeline: Optional[str] = None
    budget: Optional[str] = None
    goals: List[str] = field(default_factory=list)

@dataclass
class BusinessMemory:
    customer_facts: CustomerFacts = field(default_factory=CustomerFacts)
    objections_raised: List[str] = field(default_factory=list)
    recommendations_given: List[str] = field(default_factory=list)
    questions_answered: List[QuestionSignature] = field(default_factory=list)
    follow_up_opportunities: List[FollowUpOpportunity] = field(default_factory=list)

@dataclass
class MemoryEvent:
    event_type: str    # ENTITY_DETECTED, GOAL_IDENTIFIED, OBJECTION_RAISED, RECOMMENDATION_GIVEN, QUESTION_ANSWERED
    payload: Dict[str, Any]
    turn: int

class ResponseStrategyType(Enum):
    EXECUTIVE_SUMMARY = "Executive Summary"
    TECHNICAL_DEEP_DIVE = "Technical Deep Dive"
    COMPARISON = "Comparison"
    SALES_CONVERSATION = "Sales Conversation"
    CONSULTATIVE_DISCUSSION = "Consultative Discussion"
    EDUCATIONAL = "Educational"
    RECOMMENDATION = "Recommendation"
    REQUIREMENTS_DISCOVERY = "Requirements Discovery"
    FAQ = "FAQ"
    STEP_BY_STEP = "Step-by-Step"
    IMPLEMENTATION_GUIDE = "Implementation Guide"
    TROUBLESHOOTING = "Troubleshooting"
    CASE_STUDY = "Case Study"

@dataclass
class ResponseSectionBlueprint:
    title: str
    purpose: str
    key_points: List[str] = field(default_factory=list)

@dataclass
class ResponsePlan:
    strategy_type: ResponseStrategyType
    tone: str                       # Strategic, Technical, Consultative, Persuasive, Educational, Direct
    depth: str                      # High-Level Executive, Deep Technical, Functional Overview, Step-by-Step
    sections: List[ResponseSectionBlueprint] = field(default_factory=list)
    length: str = "Balanced"        # Concise, Balanced, Comprehensive
    follow_up: str = ""             # Strategic follow-up prompt suggestion
    cta: str = ""                   # Call-to-Action
    target_entity: Optional[str] = None
    selection_reasoning: str = ""

@dataclass
class SuggestionCandidate:
    label: str                   # Human-readable button text (e.g., "What integrations are supported?")
    action: str                  # Action key for UI dispatch
    confidence: float            # 0.0 to 1.0
    ranking_score: float
    reasoning: str               # Why this suggestion was generated
    target_intent: Optional[str] = None
    target_entity: Optional[str] = None

@dataclass
class SuggestionResult:
    suggestions: List[SuggestionCandidate] = field(default_factory=list)
    top_suggestion: Optional[SuggestionCandidate] = None
    total_candidates_generated: int = 0
    selection_reasoning: str = ""

class ValidationSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

@dataclass
class ValidationRuleResult:
    rule_name: str
    passed: bool
    severity: ValidationSeverity
    message: str
    repair_action: Optional[str] = None

@dataclass
class ValidationReport:
    is_valid: bool
    score: float                         # 0.0 to 1.0 quality score
    rule_results: List[ValidationRuleResult] = field(default_factory=list)
    original_text: str = ""
    repaired_text: str = ""
    is_repaired: bool = False
    is_fallback_triggered: bool = False
    summary_reasoning: str = ""

@dataclass
class StructuredResponseSection:
    opening: str = ""
    overview: str = ""
    business_value: str = ""
    capabilities: List[str] = field(default_factory=list)
    target_audience: str = ""
    next_steps: List[str] = field(default_factory=list)

@dataclass
class Signal:
    signal_type: str        # KeywordSignal, EntitySignal, ConversationSignal, MemorySignal
    source: IntentSource
    value: str
    weight: float

@dataclass
class IntentCandidate:
    intent: Union[BusinessIntent, ConversationalIntent]
    signals: List[Signal]
    detection_confidence: float
    ranking_confidence: float
    overall_confidence: float
    reasoning: str

@dataclass
class EnterpriseIntentResult:
    primary_intent: IntentCandidate
    secondary_intents: List[IntentCandidate]
    conversational_intent: Optional[IntentCandidate]
    raw_query: str
    normalized_query: str

@dataclass
class IntentAnalysis:
    primary_intent: str
    secondary_intents: List[str] = field(default_factory=list)
    confidence: float = 1.0
    entities: List[Dict[str, Any]] = field(default_factory=list)
    rich_result: Optional[EnterpriseIntentResult] = None

@dataclass
class DiscoveryState:
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    urgency: Optional[str] = None
    timeline: Optional[str] = None
    budget: Optional[str] = None
    missing_fields: List[str] = field(default_factory=list)
    lead_score: float = 0.0

@dataclass
class LeadQualification:
    score: float
    interest_level: str  # LOW, MEDIUM, HIGH, HOT
    readiness_tier: str   # EXPLORATORY, EVALUATING, READY
    next_best_action: str

@dataclass
class ToolSelection:
    selected_tools: List[str] = field(default_factory=list)
    queries: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResponseStrategy:
    selected_strategy: str  # Consultative, Educational, Persuasive, Objection
    audience_level: str     # CEO, Developer, General
    response_length: str    # Short, Medium, Detailed
    checklist: List[str] = field(default_factory=list)
    active_rules: List[str] = field(default_factory=list)

@dataclass
class DraftResponse:
    text: str
    suggestions: List[Dict[str, str]] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)

@dataclass
class CriticReview:
    is_approved: bool
    reasons: List[str] = field(default_factory=list)
    groundedness_score: float = 1.0
    objection_handled_correctly: bool = True
    suggested_rewrite: Optional[str] = None

@dataclass
class ExplainabilityRecord:
    session_id: str
    turn: int
    intent: str
    stage: str
    strategy: str
    tools_called: List[str]
    business_rules_applied: List[str]
    confidence_score: float
    timings_ms: Dict[str, float] = field(default_factory=dict)

@dataclass
class ResponseComposition:
    text: str
    suggestions: List[Dict[str, str]] = field(default_factory=list)
    redirect_url: Optional[str] = None
    explainability: Optional[ExplainabilityRecord] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
