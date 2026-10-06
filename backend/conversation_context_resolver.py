import logging
from typing import Dict, Any, List, Optional
from orchestration_context import OrchestrationContext, ConversationState, SessionState

logger = logging.getLogger(__name__)

# Pronoun and context triggers
PRONOUNS = {"it", "this", "that", "them", "these", "those", "the platform", "the solution", "the product", "the service", "this app", "this tool"}

SECTION_ONLY_TRIGGERS = {
    "how does it work", "how it works", "workflow", "process", "working", "how to use",
    "benefits", "advantages", "pricing", "cost", "price", "plans",
    "features", "capabilities", "modules", "who is it for", "target audience",
    "who should use", "industries", "faq", "faqs", "questions", "integrations", "implementation",
    "who is it designed for", "designed for", "who uses it", "batch release", "batch"
}

GENERIC_ENTITIES = {"company_info", "faq_general", "contact", "location"}

class ConversationContextResolver:
    def __init__(self):
        self._session_conversations: Dict[str, ConversationState] = {}
        self._session_histories: Dict[str, SessionState] = {}

    def get_conversation_state(self, session_id: str) -> ConversationState:
        if session_id not in self._session_conversations:
            self._session_conversations[session_id] = ConversationState()
        return self._session_conversations[session_id]

    def get_session_state(self, session_id: str) -> SessionState:
        if session_id not in self._session_histories:
            self._session_histories[session_id] = SessionState()
        return self._session_histories[session_id]

    def resolve_context(self, ctx: OrchestrationContext, detected_entity_id: Optional[str] = None, detected_entities: Optional[List[str]] = None) -> OrchestrationContext:
        conv_state = self.get_conversation_state(ctx.session_id)
        sess_state = self.get_session_state(ctx.session_id)
        
        q_lower = ctx.normalized_query.lower().strip()
        
        # 1. Multi-entity detection for session memory (only if explicit comparison keywords exist)
        is_explicit_comparison = any(k in q_lower for k in ["compare", " vs ", "versus", "difference", "differ", "better than", "which one", "comparison"])
        if is_explicit_comparison and detected_entities and len(detected_entities) >= 2:
            sess_state.recently_compared_entities = list(dict.fromkeys(detected_entities))
            for ent in detected_entities:
                if ent not in sess_state.recent_entities:
                    sess_state.recent_entities.append(ent)
            ctx.add_trace(
                stage="ConversationContextResolver",
                result=f"Multi-entity context set: {detected_entities}",
                reason="Multiple entities detected in explicit comparison query"
            )
            ctx.conversation_state = conv_state
            ctx.session_state = sess_state
            return ctx
        else:
            # Clear stale multi-entity comparison state for single entity inquiries
            sess_state.recently_compared_entities = []

        # 2. Section or Pronoun trigger over active entity
        has_pronoun = any(p in q_lower.split() or f" {p} " in f" {q_lower} " for p in PRONOUNS)
        is_section_trigger = q_lower in SECTION_ONLY_TRIGGERS or any(st in q_lower for st in SECTION_ONLY_TRIGGERS)

        if (has_pronoun or is_section_trigger or detected_entity_id in GENERIC_ENTITIES) and conv_state.active_entity and (is_section_trigger or has_pronoun):
            ctx.resolved_entity_id = conv_state.active_entity
            ctx.add_trace(
                stage="ConversationContextResolver",
                result=f"Resolved context trigger to active entity -> {conv_state.active_entity}",
                reason="Query contains contextual pronoun or standalone section reference"
            )
            ctx.conversation_state = conv_state
            ctx.session_state = sess_state
            return ctx

        # 3. Direct entity match
        if detected_entity_id and detected_entity_id not in GENERIC_ENTITIES:
            conv_state.active_entity = detected_entity_id
            if detected_entity_id not in sess_state.recent_entities:
                sess_state.recent_entities.append(detected_entity_id)
            
            ctx.resolved_entity_id = detected_entity_id
            ctx.add_trace(
                stage="ConversationContextResolver",
                result=f"Active entity set -> {detected_entity_id}",
                reason="Explicit entity present in query"
            )
            ctx.conversation_state = conv_state
            ctx.session_state = sess_state
            return ctx

        if detected_entity_id:
            ctx.resolved_entity_id = detected_entity_id
            ctx.add_trace(
                stage="ConversationContextResolver",
                result=f"Generic entity detected -> {detected_entity_id}",
                reason="Generic catalog match"
            )
        else:
            ctx.add_trace(
                stage="ConversationContextResolver",
                result="No context entity resolved",
                reason="No explicit entity or active context match"
            )

        # 5. Resolve Phase 5 Enterprise Memories (Personalization & Context)
        try:
            from phase5_memory_engine import get_phase5_memory_engine
            memories = get_phase5_memory_engine().resolve_context_memories(ctx)
            if memories:
                ctx.metrics["resolved_memories_count"] = len(memories)
                ctx.metrics["active_memory_types"] = [m.type for m in memories]
        except Exception as e:
            logger.warning(f"Memory engine resolution notice: {e}")

        ctx.conversation_state = conv_state
        ctx.session_state = sess_state
        return ctx

    def update_state_after_response(self, ctx: OrchestrationContext):
        conv_state = self.get_conversation_state(ctx.session_id)
        sess_state = self.get_session_state(ctx.session_id)

        if ctx.resolved_entity_id and ctx.resolved_entity_id not in GENERIC_ENTITIES:
            conv_state.active_entity = ctx.resolved_entity_id
        if ctx.resolved_category:
            conv_state.active_category = ctx.resolved_category
        if ctx.intent:
            conv_state.last_intent = ctx.intent
        if ctx.section:
            conv_state.last_section = ctx.section

        if ctx.execution_strategy:
            sess_state.strategy_history.append(ctx.execution_strategy.value)

_context_resolver_instance = None

def get_conversation_context_resolver() -> ConversationContextResolver:
    global _context_resolver_instance
    if _context_resolver_instance is None:
        _context_resolver_instance = ConversationContextResolver()
    return _context_resolver_instance
