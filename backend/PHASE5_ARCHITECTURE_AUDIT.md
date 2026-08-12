# CittaAI Backend — Phase 5 Architecture Audit

## 1. Overview & Verification Summary

This document establishes the verified architectural baseline of the CittaAI production chatbot backend prior to initiating Phase 5 (Semantic Query Intelligence Layer). 

Every section, flow, call graph, and component listed below has been verified directly against the production codebase.

---

## 2. Current Request Flow (`POST /api/chat`)

The active request lifecycle from HTTP POST to Server-Sent Events (SSE) streaming is:

```
USER
  │
  ▼
Frontend (React SSE Client / `Footer.jsx` & Chat UI)
  │
  ▼
FastAPI Endpoint (`server.py` → `chat_endpoint`)
  │
  ▼
Request Parsing & Pydantic Validation (`ChatMessageInput`: session_id, message)
  │
  ▼
Injection Guardrail Intercept (`rag_service.py` → `is_prompt_injection`)
  │
  ▼
Pre-Retrieval OOD Check (`response_planner.py` → `plan`)
  │
  ▼
Query Normalization (`query_normalizer.py` → `normalize_query_pipeline`)
  │
  ▼
Greeting Detector Intercept (`greeting_detector.py` → `detect_greeting`)
  │
  ▼
Phase 2 Orchestrator (`phase2_orchestrator.py` → `orchestrate`)
    ├── Entity Resolution (`core/entity_resolver.py` via `entity_resolver.py`)
    ├── Data-Driven Agent Fallback (`query_understanding_agent.py` if conf < 0.90)
    ├── Conversation Context Resolution (`conversation_context_resolver.py`)
    ├── General Catalog Check (`check_general_catalog_query`)
    ├── Out-of-Domain Guardrail Dispatch (Zero-LLM fallback)
    ├── Intent Classification (`phase2_intent_classifier.py`)
    ├── Ambiguity Check (`ambiguity_detector.py`)
    ├── Unknown Entity Handler (`unknown_entity_handler.py`)
    └── Strategy Selection (`execution_strategy.py`)
  │
  ▼
Phase 3 Reasoning Engine / Phase 4 Action Engine (if strategy = REASONING / ACTION)
  │
  ▼
Deterministic Engine Intercept (`deterministic_engine.py` → `generate_response`)
  │
  ▼
Exact Query Cache Lookup (`LRUCacheWithTTL` in `rag_service.py`)
  │
  ▼
Query Intent Classification (`query_planner.py` → `classify_query`)
  │
  ▼
Dynamic Section Resolution (`section_resolver.py` → `resolve_section_dynamic`)
  │
  ▼
Knowledge Router (`knowledge_router.py` → `route_query`)
  │
  ▼
Context Construction (`context_formatter.py` / `context_builder.py`)
  │
  ▼
Prompt Construction (Compact System Prompt in `rag_service.py` L813–831)
  │
  ▼
LLM Generation (`GroqProvider` → `groq_client.py` using `llama-3.3-70b-versatile`)
  │
  ▼
Post-Generation Guardrails & Validation (`response_validator.py` → `validate_response`)
  │
  ▼
Response Postprocessing (`response_postprocessor.py`) & Background Analytics DB Logging
  │
  ▼
FastAPI `StreamingResponse` (SSE `data: {"text": "...", "done": false/true}`)
  │
  ▼
Frontend & USER
```

---

## 3. Detailed Component Audit

### 3.1 Query Understanding Flow
Currently split across three separate modules:
- `query_normalizer.py`: Performs lowercasing, punctuation stripping, typo autocorrect against `unified_vocabulary`, and abbreviation expansion.
- `query_planner.py`: Rewrites queries (e.g. `"wa"` → `"WhatsApp Marketing Platform"`), checks `is_in_domain()` using a static term list, and classifies query type.
- `query_understanding_agent.py`: Uses Groq or a data-driven keyword matcher (`_data_driven_fallback()`) to score domain terms when entity resolution confidence is under `0.90`.

### 3.2 Entity Resolution Flow
Located in `core/entity_resolver.py` (called by `entity_resolver.py`):
1. **Normalization & Query Rewrite**: Strips punctuation, normalizes spaces.
2. **Context Pronoun Check**: `contains_pronouns()` checks for `it`, `its`, `this`, `that`, `they`, `them`, `who is it for`. Inherits `active_entity` if present.
3. **Step 1 — Exact Canonical ID / Name Match** (Score: `1.0`).
4. **Step 2 — Exact Alias Match** (Score: `1.0`).
5. **Step 3 — Exact Slug Match** (Score: `1.0`).
6. **Step 3.1 — Substring Boundary Match** (Score: `0.95`).
7. **Step 3.5 — Capability / Sub-Feature Lookup** (Score: `0.95`).
8. **Step 4 — Keyword Match** (Score: `0.90`).
9. **Step 5 — Substring Phrase Lookup** (Score: `0.80–0.90`).
10. **Step 6 — RapidFuzz Fuzzy Match** (`WRatio` >= 90%, Score: `0.90–0.98`).
11. **Data-Driven Agent Fallback**: If confidence < 0.90, evaluates domain term associations over live registry objects.

### 3.3 Intent Classification Flow
Fragmented across three separate systems:
1. `intent_classifier.py` (`IntentCategory`): 19 categories using regex rules (`INTENT_RULES`) and BGE anchor embedding cosine similarity (`ANCHOR_TEXTS`).
2. `phase2_intent_classifier.py` (`EnterpriseIntent`): 23 intents matching regex patterns (`INTENT_PATTERNS`).
3. `intent_analyzer.py` (`IntentType`): 7 intents used by `DeterministicEngine`.

### 3.4 Routing Flow
1. `phase2_orchestrator.py` checks out-of-domain, ambiguity, unknown entity, and strategy selection (`FAST_PATH`, `CATALOG`, `REASONING`, `ACTION`, `HYBRID_RAG`).
2. `deterministic_engine.py` intercepts counts, listings (`"what services do you offer"`, `"list products"`), greetings, leadership, and case studies, returning zero-LLM responses in < 5ms.
3. `knowledge_router.py` evaluates priority order: `cache` → `golden_answers` → `business_registry` → `faq` → `hybrid_rag` → `fallback`.
4. `rag_service.py` executes the Groq compact path if routed to `business_registry`.

### 3.5 Conversation Context Flow
- `conversation_context_resolver.py` manages `ConversationState` (`active_entity`, `active_category`, `last_intent`, `last_section`).
- Maintains active entity across turns if contextual pronouns (`it`, `this`, `that`, `benefits`, `features`, `how does it work`) are detected.
- Clears active context if an explicit entity change is detected (e.g. asking about `Education OS` after `Pharma OS`).

### 3.6 LLM Invocation Points
1. **Primary Production Answer Generation**: `rag_service.py` L856 & L1172 invoking `GroqProvider.generate_stream()` (`llama-3.3-70b-versatile`).
2. **Phase 3 Reasoning Engine**: `phase3_reasoning_engine.py` L45 invoking `provider.generate()`.
3. **Query Understanding Agent**: `query_understanding_agent.py` L156 invoking `provider.generate()` (with instant fallback to `_data_driven_fallback`).
4. **Guardrail Regeneration**: `rag_service.py` L1219 invoking `provider.generate_stream()` if cross-domain entity mixing is detected in output.

### 3.7 Deterministic Fast Paths (Zero LLM)
- Injection protection (`is_prompt_injection`)
- Pre-retrieval OOD rejection (`response_planner.py`)
- Greetings (`greeting_detector.py`)
- Category counts & lists (`deterministic_engine.py` & `knowledge_router.py`)
- Out-of-Domain Guardrail (`out_of_domain_detector.py`)
- Ambiguity Resolvers (`ambiguity_detector.py`)
- Unknown Entity Fallback (`unknown_entity_handler.py`)
- Exact Query LRU Cache Hit (`rag_service.py`)

### 3.8 Fallback Paths
- Groq streaming error → Returns static registry response (`rag_service.py` L879).
- LLM Provider missing/failed in `QueryUnderstandingAgent` → Reverts to `_data_driven_fallback()`.
- Reasoning LLM failure → Reverts to `structured_formatter.py` template.
- Category cross-mixing → Reverts to single-domain regeneration or static fallback.

---

## 4. Existing Architectural Weaknesses

1. **Intent Taxonomy Fragmentation**: Three independent intent systems (`IntentCategory`, `EnterpriseIntent`, `IntentType`) exist concurrently.
2. **Hardcoded Intercept Overrides**: `deterministic_engine.py` and `knowledge_router.py` rely on hardcoded regex checks (e.g., `"what services do you offer"`) instead of dynamic semantic classification.
3. **Category Terminology Misalignment**: Users calling products/solutions `"services"` (e.g. `"What WhatsApp services do you provide?"`) rely on regex intercepts or post-hoc explanation templates rather than pre-retrieval semantic understanding.
4. **Vulnerability to Informal / Poor English**: Indirect, ungrammatical, or slang queries can bypass rule-based matchers and reach fallback paths unexpectedly.
5. **No Centralized Semantic Query Representation**: No structured object currently captures the user's intent, goal, domain, category mismatch status, and target information in a unified schema before routing.

---

## 5. Proposed Phase 5 Insertion Point

The Phase 5 **Query Intelligence Engine** (`backend/query_intelligence_engine.py`) will sit directly between **Query Normalization** and **Existing Routing / Orchestration Infrastructure**:

```
                       USER QUERY
                            │
                            ▼
                   Query Normalization
               (query_normalizer.py)
                            │
                            ▼
             SEMANTIC QUERY INTELLIGENCE ENGINE
            (backend/query_intelligence_engine.py)
                            │
                            ▼
             Structured Query Representation
             (Canonical Query Context Object)
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Resolved Entity  Canonical     Requested Target
        & Confidence      Intent        Information
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                 Phase 2 Orchestrator
             & Existing Router Infrastructure
                            │
                            ▼
                    Knowledge Registry
                            │
                            ▼
                    Groq / Llama 3.3 70B
```

---

## 6. Impacted Files & Backward Compatibility

### Files That Must Change (Phase 5 Additions & Integrations)
- `backend/query_intelligence_engine.py` **[NEW]**: Central semantic query interpretation engine.
- `backend/phase2_orchestrator.py` **[MODIFY]**: Integrate `QueryIntelligenceEngine` structured context into `OrchestrationContext`.
- `backend/rag_service.py` **[MODIFY]**: Connect normalized query and intent signals from `QueryIntelligenceEngine`.
- `backend/test_phase5_query_intelligence.py` **[NEW]**: Comprehensive 300+ multi-category test suite.

### Files That Must Remain Untouched
- `backend/knowledge/registry/*` (All 21 registry JSON files & `manifest.json`)
- `backend/response_validator.py` (Validation & grounding rules)
- `frontend/*` (Entire React frontend and SSE contract)
- `backend/groq_client.py` (Low-level Groq API wrapper)
- `backend/llm_provider.py` (Provider base classes)

### Backward Compatibility Considerations
- If `QueryIntelligenceEngine` encounters an unexpected error or low confidence, it **must fail safely** to the existing Phase 4/Phase 2 deterministic pipeline without crashing `/api/chat`.
- Fast path zero-LLM response latency (< 15 ms) for exact catalog counts and greetings must be strictly preserved.
- Existing SSE JSON chunk schema (`{"text": "...", "done": false}`) and final payload schema (`{"done": true, "citations": [...], ...}`) must remain 100% unchanged.

---

## 7. Verification Verdict

All architectural assumptions in the prompt have been verified against the codebase. We are ready to proceed with Phase 5 implementation according to the plan.
