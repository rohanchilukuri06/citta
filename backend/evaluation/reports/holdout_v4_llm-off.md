# semantic_holdout_v4.json — LLM off

Generated 2026-09-29 21:30:25

## Manifest
```json
{
  "dataset": "semantic_holdout_v4.json",
  "dataset_sha": "c5625e5cb888",
  "n": 140,
  "llm_mode": "off",
  "llm_provider": null,
  "llm_model": null,
  "llm_fallback": null,
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "aspect_thresholds": [
    0.4,
    0.2
  ],
  "code_sha": {
    "query_intelligence_engine.py": "eb3765755c43",
    "semantic_arbitration.py": "eaa7ddc78128",
    "semantic_chat_pipeline.py": "839777f055e7",
    "knowledge_tool_router.py": "23c28461285f",
    "knowledge_operation_executor.py": "b2b45bb21211"
  },
  "git_head": "71b4793"
}
```

## Decision metrics
| Metric | Value |
|---|---|
| entity | 90.0% |
| intent | not measured (no gold intent labels) |
| aspect | 83.6% |
| scope | 90.0% |
| canonicalization | 97.9% |
| operation | 72.9% |
| arguments | 93.6% |
| full_decision | 69.3% |
| evidence_availability | 100.0% |
| confidently wrong (decision conf ≥ 0.8) | 13 |
| confidently wrong (legacy: entity conf ≥ 0.8) | 26 |
| ECE (decision conf) | 0.2612 |
| ECE (legacy entity conf) | 0.2296 |
| LLM entity / aspect / any rate | 0.0% / 0.0% / 0.0% |
| LLM call success rate | 0.0% |
| Latency p50 / p95 | 211.0 / 366.4 ms |
| Catalog leakage | 0 |
| OOD leakage | 0 |
| Unknown product substituted | 2 |
| Clarification rate | 8.6% |

## First failure stage
| Stage | Queries |
|---|---|
| entity | 11 |
| aspect | 17 |
| scope | 6 |
| canonicalization | 0 |
| operation | 9 |
| arguments | 0 |
| evidence | 0 |

## By category
| Category | n | Decision |
|---|---|---|
| ambiguous | 6 | 50.0% |
| aspect | 20 | 75.0% |
| both | 3 | 33.3% |
| catalog | 8 | 75.0% |
| category_mismatch | 4 | 50.0% |
| company | 10 | 50.0% |
| context | 12 | 58.3% |
| conversational | 3 | 66.7% |
| direct | 9 | 88.9% |
| grammar | 3 | 66.7% |
| healthcare | 3 | 33.3% |
| indirect | 4 | 75.0% |
| informal | 7 | 42.9% |
| minimal | 5 | 100.0% |
| multi | 7 | 85.7% |
| non_native | 7 | 71.4% |
| ood | 7 | 100.0% |
| problem | 13 | 69.2% |
| spelling | 5 | 80.0% |
| unknown_product | 4 | 75.0% |

## Failures

### V4_002 (problem) — first failure: **entity**
- Query: `Our online store traffic is flat and our Google ads cost way too much per sale. Can you help with SEO and paid ads together?`
- Expected: entity ['ai_powered_marketing'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ecommerce_os ['ecommerce_os', 'ai_powered_marketing'], intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope MULTI_ENTITY, op `get_solution` {'entity_id': 'ecommerce_os'}
- Confidence: entity 0.95 (margin 0.5), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: SEO, PPC and e-commerce growth are AI-Powered Marketing capabilities.

### V4_003 (informal) — first failure: **entity**
- Query: `yo do u guys run insta n fb ads for brands`
- Expected: entity ['ai_powered_marketing'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity influencer_marketing , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_product` {'entity_id': 'influencer_marketing', 'section': 'OVERVIEW'}
- Confidence: entity 0.4607 (margin 0.2565), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Social media marketing and PPC advertising are listed capabilities.

### V4_008 (grammar) — first failure: **aspect**
- Query: `we needs a roadmap for adopt AI in our company, who can helps us`
- Expected: entity ['ai_strategy'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ai_strategy , intent RECOMMENDATION, aspect TARGET_USERS (2nd OVERVIEW, margin 0.9302), scope SINGLE_ENTITY, op `get_target_users` {'entity_id': 'ai_strategy'}
- Confidence: entity 0.9752 (margin 0.9752), aspect 0.9651, decision 0.9651 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Strategic roadmap is an AI Strategy capability.

### V4_010 (category_mismatch) — first failure: **aspect**
- Query: `can I get a demo of the AI Strategy software?`
- Expected: entity ['ai_strategy'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ai_strategy , intent DEMO_REQUEST, aspect CONTACT (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_contact` {'topic_entity_id': 'ai_strategy'}
- Confidence: entity 0.568 (margin 0.3998), aspect 1.0, decision 0.568 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: AI Strategy & Advisory is a service, not software; still the intended offering.

### V4_012 (problem) — first failure: **operation**
- Query: `Our customer records are duplicated across four different systems and nobody trusts the numbers in any report`
- Expected: entity ['data_engineering'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity data_engineering , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.3041 (margin 0.2024), aspect 0.4, decision 0.3041 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Master data management / golden record is a Data Engineering capability.

### V4_014 (conversational) — first failure: **operation**
- Query: `Hi! We're moving all our reporting to a cloud warehouse this year and could use some expert help. Is that something your team handles?`
- Expected: entity ['data_engineering'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity data_engineering , intent GREETING, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'data_engineering'}
- Confidence: entity 0.7721 (margin 0.7192), aspect 1.0, decision 0.7721 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Cloud data warehouse is a Data Engineering capability.

### V4_016 (problem) — first failure: **scope**
- Query: `I run an online clothing store and I'm juggling inventory spreadsheets, order tracking and support emails in three different tools. Is there one system that does it all?`
- Expected: entity ['ecommerce_os'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity ecommerce_os ['ecommerce_os', 'whatsapp_marketing'], intent CONTACT, aspect CAPABILITIES (2nd CONTACT, margin 0.3846), scope MULTI_ENTITY, op `get_solution` {'entity_id': 'ecommerce_os', 'section': 'CAPABILITIES'}
- Confidence: entity 0.95 (margin 0.5), aspect 0.6923, decision 0.6923 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope FAIL · canonicalization PASS · operation PASS · arguments PASS · evidence PASS
- Gold rationale: Inventory, order lifecycle and AI support are unified in E-Commerce OS.

### V4_018 (informal) — first failure: **operation**
- Query: `got a small d2c brand, need smth that handles orders + returns + a chatbot. anything?`
- Expected: entity ['ecommerce_os'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity ecommerce_os , intent RECOMMENDATION, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'ecommerce_os'}
- Confidence: entity 0.8276 (margin 0.7723), aspect 1.0, decision 0.8276 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Order lifecycle with returns plus conversational AI is E-Commerce OS.

### V4_019 (non_native) — first failure: **operation**
- Query: `My shop is selling online, I need voice agent for handling order tracking calls, which one you have?`
- Expected: entity ['ecommerce_os'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity ecommerce_os , intent RECOMMENDATION, aspect OVERVIEW (2nd None, margin -1.0), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.4998 (margin 0.0998), aspect 0.0, decision 0.0 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Voice AI for order tracking is in the E-Commerce OS workflow.

### V4_025 (direct) — first failure: **aspect**
- Query: `What's included in the Enterprise & Agentic AI service?`
- Expected: entity ['enterprise_agentic_ai'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent INTEGRATIONS, aspect CAPABILITIES (2nd WORKFLOW, margin 0.9124), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'enterprise_agentic_ai'}
- Confidence: entity 0.8748 (margin 0.7863), aspect 0.9562, decision 0.8748 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Names the service directly.

### V4_026 (category_mismatch) — first failure: **entity**
- Query: `Enterprise and Agentic AI platform - how do I buy a licence?`
- Expected: entity ['enterprise_agentic_ai'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity enterprise_ai_os , intent INTEGRATIONS, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.4936 (margin 0.0481), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Enterprise & Agentic AI is a consulting service, referred to as a licensed platform.

### V4_027 (informal) — first failure: **aspect**
- Query: `u guys use crewai or autogen when building agents?`
- Expected: entity ['enterprise_agentic_ai'], aspect ['FAQ', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'enterprise_agentic_ai', 'section': 'OVERVIEW'}
- Confidence: entity 0.9082 (margin 0.8574), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: AutoGen/CrewAI orchestration and the frameworks FAQ belong to Enterprise & Agentic AI.

### V4_029 (problem) — first failure: **operation**
- Query: `We want an assistant that answers staff questions from our internal policy documents and doesn't just make stuff up`
- Expected: entity ['enterprise_agentic_ai', 'enterprise_ai_os'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification allowed, knowledge_available True
- Predicted: entity enterprise_ai_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'enterprise_ai_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.4742 (margin 0.3689), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: RAG with anti-hallucination is offered by both the Agentic AI service and Enterprise AI OS.

### V4_038 (non_native) — first failure: **operation**
- Query: `I am agency, we want manage many brand campaign with creators and pay them only after work done, your tool support this?`
- Expected: entity ['influencer_marketing'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_product`, clarification no, knowledge_available True
- Predicted: entity influencer_marketing , intent UNKNOWN, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'influencer_marketing'}
- Confidence: entity 0.9293 (margin 0.8952), aspect 1.0, decision 0.9293 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Agencies, campaign management and milestone payouts are Influencer Platform content.

### V4_042 (indirect) — first failure: **aspect**
- Query: `we want an AI brand architecture and positioning engine instead of static brand decks`
- Expected: entity ['martech_360'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity martech_360 , intent HOW_IT_WORKS, aspect WORKFLOW (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_workflow` {'entity_id': 'martech_360'}
- Confidence: entity 0.6169 (margin 0.24), aspect 1.0, decision 0.6169 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Brand architecture engine replacing static decks is MarTech 360's description.

### V4_046 (spelling) — first failure: **entity**
- Query: `farma os`
- Expected: entity ['pharma_os'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity None , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope UNKNOWN_ENTITY, op `request_clarification` {'reason': 'The user named an offering that is not in the catalog.', 'unknown_entity': 'farma os'}
- Confidence: entity 0.0 (margin 0.0), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Misspelled Pharma OS.

### V4_051 (informal) — first failure: **aspect**
- Query: `real estate crm type thing?`
- Expected: entity ['real_estate_os'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity real_estate_os , intent INTEGRATIONS, aspect TARGET_USERS (2nd CAPABILITIES, margin 0.4682), scope SINGLE_ENTITY, op `get_target_users` {'entity_id': 'real_estate_os'}
- Confidence: entity 0.9703 (margin 0.9703), aspect 0.7341, decision 0.7341 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Lead management for real estate is Real Estate OS.

### V4_068 (aspect) — first failure: **operation**
- Query: `Which cloud data warehouses does your Data Engineering team support?`
- Expected: entity ['data_engineering'], aspect ['FAQ', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity data_engineering , intent UNKNOWN, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'data_engineering'}
- Confidence: entity 0.975 (margin 0.975), aspect 1.0, decision 0.975 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Specific Data Engineering FAQ.

### V4_073 (aspect) — first failure: **aspect**
- Query: `How does your Enterprise & Agentic AI team stop the models from hallucinating?`
- Expected: entity ['enterprise_agentic_ai'], aspect ['FAQ', 'BENEFITS', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent INTEGRATIONS, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'enterprise_agentic_ai', 'section': 'OVERVIEW'}
- Confidence: entity 0.9749 (margin 0.9749), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Hallucination prevention is an Agentic AI FAQ/benefit.

### V4_074 (aspect) — first failure: **aspect**
- Query: `Which platforms does AI-Powered Marketing support?`
- Expected: entity ['ai_powered_marketing'], aspect ['FAQ', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity ai_powered_marketing , intent UNKNOWN, aspect OVERVIEW (2nd OVERVIEW, margin -0.0792), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'ai_powered_marketing', 'section': 'OVERVIEW'}
- Confidence: entity 0.9713 (margin 0.9713), aspect 0.4604, decision 0.4604 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Supported platforms is an FAQ.

### V4_075 (aspect) — first failure: **aspect**
- Query: `How long is the MarTech 360 strategy process?`
- Expected: entity ['martech_360'], aspect ['FAQ', 'BENEFITS'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity martech_360 , intent HOW_IT_WORKS, aspect WORKFLOW (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_workflow` {'entity_id': 'martech_360'}
- Confidence: entity 0.6674 (margin 0.3654), aspect 1.0, decision 0.6674 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Sprint duration (2-3 weeks) is in FAQ/benefits.

### V4_076 (aspect) — first failure: **aspect**
- Query: `Can E-Commerce OS be deployed on our own servers on-prem?`
- Expected: entity ['ecommerce_os'], aspect ['FAQ', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available False
- Predicted: entity ecommerce_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'ecommerce_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.9549 (margin 0.9464), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Deployment detail not covered by E-Commerce OS content.

### V4_086 (context) — first failure: **aspect**
- Query: `what about the whatsapp one, who's that for` (context: {'active_entity': 'influencer_marketing', 'active_entities': ['influencer_marketing'], 'previous_turns': ['Tell me about the Influencer Marketing Platform']})
- Expected: entity ['whatsapp_marketing'], aspect ['TARGET_USERS'], scope SINGLE_ENTITY, op `get_target_users`, clarification no, knowledge_available True
- Predicted: entity whatsapp_marketing , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_product` {'entity_id': 'whatsapp_marketing', 'section': 'OVERVIEW'}
- Confidence: entity 0.9696 (margin 0.9696), aspect 1.0, decision 0.9696 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Switches to the WhatsApp Platform.

### V4_089 (context) — first failure: **aspect**
- Query: `which frameworks do u use for that` (context: {'active_entity': 'enterprise_agentic_ai', 'active_entities': ['enterprise_agentic_ai'], 'previous_turns': ['what is enterprise & agentic ai', 'can you build multi-agent systems?']})
- Expected: entity ['enterprise_agentic_ai'], aspect ['FAQ', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent UNKNOWN, aspect OVERVIEW (2nd OVERVIEW, margin -0.1286), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'enterprise_agentic_ai', 'section': 'OVERVIEW'}
- Confidence: entity 0.95 (margin 0.95), aspect 0.3554, decision 0.3554 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Frameworks FAQ of active Agentic AI service.

### V4_090 (context) — first failure: **aspect**
- Query: `who's it for?` (context: {'active_entity': 'martech_360', 'active_entities': ['martech_360'], 'previous_turns': ['What is MarTech 360?']})
- Expected: entity ['martech_360'], aspect ['TARGET_USERS'], scope SINGLE_ENTITY, op `get_target_users`, clarification no, knowledge_available True
- Predicted: entity martech_360 , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'martech_360', 'section': 'OVERVIEW'}
- Confidence: entity 0.95 (margin 0.95), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Target users of active MarTech 360.

### V4_091 (context) — first failure: **aspect**
- Query: `any real numbers or results from it?` (context: {'active_entity': 'smart_cities_os', 'active_entities': ['smart_cities_os'], 'previous_turns': ['What is Smart Cities OS?']})
- Expected: entity ['smart_cities_os'], aspect ['BENEFITS'], scope SINGLE_ENTITY, op `get_benefits`, clarification no, knowledge_available True
- Predicted: entity smart_cities_os , intent UNKNOWN, aspect OVERVIEW (2nd WORKFLOW, margin -0.3366), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'smart_cities_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.95 (margin 0.95), aspect 0.3317, decision 0.3317 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Benefit metrics of active Smart Cities OS.

### V4_092 (context) — first failure: **aspect**
- Query: `can it plug into our CRM and ERP` (context: {'active_entity': 'enterprise_ai_os', 'active_entities': ['enterprise_ai_os'], 'previous_turns': ['What is Enterprise AI OS?', 'does it support voice agents']})
- Expected: entity ['enterprise_ai_os'], aspect ['CAPABILITIES', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_capabilities`, clarification no, knowledge_available True
- Predicted: entity enterprise_ai_os , intent INTEGRATIONS, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'enterprise_ai_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.95 (margin 0.95), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Integration capability of active Enterprise AI OS.

### V4_093 (both) — first failure: **operation**
- Query: `what do both of them cost?` (context: {'active_entity': 'whatsapp_marketing', 'active_entities': ['influencer_marketing', 'whatsapp_marketing'], 'previous_turns': ['tell me about the influencer platform', 'and the whatsapp platform?']})
- Expected: entity ['influencer_marketing', 'whatsapp_marketing'], aspect ['PRICING'], scope MULTI_ENTITY, op `get_pricing`, clarification no, knowledge_available False
- Predicted: entity influencer_marketing ['influencer_marketing', 'whatsapp_marketing'], intent UNKNOWN, aspect PRICING (2nd None, margin 1.0), scope MULTI_ENTITY, op `get_product` {'entity_id': 'influencer_marketing', 'section': 'PRICING'}
- Confidence: entity 0.95 (margin 0.5), aspect 1.0, decision 0.95 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Two offerings in context; pricing is not published.

### V4_095 (both) — first failure: **operation**
- Query: `how do the two work?` (context: {'active_entity': 'ecommerce_os', 'active_entities': ['education_os', 'ecommerce_os'], 'previous_turns': ['what is education os', 'and e-commerce os?']})
- Expected: entity ['education_os', 'ecommerce_os'], aspect ['WORKFLOW'], scope MULTI_ENTITY, op `get_workflow`, clarification no, knowledge_available True
- Predicted: entity education_os ['education_os', 'ecommerce_os'], intent UNKNOWN, aspect WORKFLOW (2nd CAPABILITIES, margin 0.9738), scope MULTI_ENTITY, op `get_solution` {'entity_id': 'education_os', 'section': 'WORKFLOW'}
- Confidence: entity 0.95 (margin 0.5), aspect 0.9869, decision 0.95 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Two offerings in context; workflows available for both.

### V4_097 (multi) — first failure: **aspect**
- Query: `difference between MarTech 360 and AI-Powered Marketing?`
- Expected: entity ['martech_360', 'ai_powered_marketing'], aspect ['OVERVIEW'], scope MULTI_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity martech_360 ['martech_360', 'ai_powered_marketing'], intent UNKNOWN, aspect CAPABILITIES (2nd WORKFLOW, margin 0.3083), scope MULTI_ENTITY, op `get_service` {'entity_id': 'martech_360', 'section': 'CAPABILITIES'}
- Confidence: entity 0.95 (margin 0.5), aspect 0.6135, decision 0.6135 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation PASS · arguments PASS · evidence PASS
- Gold rationale: Comparison of two marketing services.

### V4_107 (catalog) — first failure: **scope**
- Query: `which industries do you work with?`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL, op `list_catalog`, clarification no, knowledge_available True
- Predicted: entity None , intent UNKNOWN, aspect CATALOG_LIST (2nd CAPABILITIES, margin 1.0), scope ALL_SOLUTIONS, op `list_solutions` {}
- Confidence: entity 0.0 (margin 0.0), aspect 0.95, decision 0.95 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Industries span the whole catalog.

### V4_110 (catalog) — first failure: **entity**
- Query: `do you have consulting services? list them please`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL_SERVICES, op `list_services`, clarification no, knowledge_available True
- Predicted: entity ai_strategy , intent UNKNOWN, aspect OVERVIEW (2nd PRICING, margin 0.7872), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'ai_strategy', 'section': 'OVERVIEW'}
- Confidence: entity 0.5999 (margin 0.5058), aspect 0.8936, decision 0.5999 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Consulting offerings are the services.

### V4_111 (company) — first failure: **aspect**
- Query: `Who is CittaAI? what does the company actually do`
- Expected: entity ['company_info'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_company_info`, clarification no, knowledge_available True
- Predicted: entity company_info , intent CAPABILITIES, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_company_info` {'section': 'CAPABILITIES'}
- Confidence: entity 0.95 (margin 0.95), aspect 1.0, decision 0.95 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation PASS · arguments PASS · evidence PASS
- Gold rationale: Company overview.

### V4_113 (company) — first failure: **entity**
- Query: `who is your CTO?`
- Expected: entity ['leadership_info'], aspect ['LEADERSHIP'], scope SINGLE_ENTITY, op `get_leadership`, clarification no, knowledge_available True
- Predicted: entity akhil_reddy , intent LEADERSHIP, aspect LEADERSHIP (2nd CLIENTS_CASE_STUDIES, margin 0.9494), scope SINGLE_ENTITY, op `get_leadership` {'person_id': 'akhil_reddy'}
- Confidence: entity 0.9747 (margin 1.0), aspect 0.9747, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation PASS · arguments PASS · evidence PASS
- Gold rationale: CTO is in leadership list.

### V4_116 (company) — first failure: **entity**
- Query: `what are your working hours`
- Expected: entity ['contact_info'], aspect ['CONTACT'], scope SINGLE_ENTITY, op `get_contact`, clarification no, knowledge_available True
- Predicted: entity None , intent HOW_IT_WORKS, aspect WORKFLOW (2nd None, margin 1.0), scope OUT_OF_DOMAIN, op `decline_out_of_domain` {}
- Confidence: entity 0.0 (margin 0.0), aspect 1.0, decision 0.7 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Business hours are in contact details.

### V4_119 (company) — first failure: **scope**
- Query: `tell me about the jewellery brand case study`
- Expected: entity ['jewellery_brand_roi'], aspect ['CLIENTS_CASE_STUDIES'], scope SINGLE_ENTITY, op `get_case_study`, clarification no, knowledge_available True
- Predicted: entity jewellery_brand_roi , intent CASE_STUDIES, aspect CLIENTS_CASE_STUDIES (2nd OVERVIEW, margin 0.8524), scope CLIENTS_SCOPE, op `get_case_study` {'entity_id': 'jewellery_brand_roi'}
- Confidence: entity 0.9168 (margin 1.0), aspect 0.9168, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope FAIL · canonicalization PASS · operation PASS · arguments PASS · evidence PASS
- Gold rationale: Specific case study.

### V4_120 (company) — first failure: **entity**
- Query: `how did you get all those export inquiries for that spices company?`
- Expected: entity ['b2b_spices_export'], aspect ['CLIENTS_CASE_STUDIES'], scope SINGLE_ENTITY, op `get_case_study`, clarification no, knowledge_available True
- Predicted: entity influencer_marketing , intent UNKNOWN, aspect OVERVIEW (2nd None, margin -1.0), scope GENERAL, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.1362 (margin 0.0993), aspect 0.0, decision 0.0 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Specific case study (B2B spices export).

### V4_130 (unknown_product) — first failure: **entity**
- Query: `CittaAI HR payroll software details`
- Expected: entity [], aspect None, scope UNKNOWN_ENTITY, op `request_clarification`, clarification allowed, knowledge_available False
- Predicted: entity real_estate_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'real_estate_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.5628 (margin 0.3163), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Named product does not exist in the catalog.

### V4_132 (ambiguous) — first failure: **scope**
- Query: `tell me about your OS platform`
- Expected: entity [], aspect None, scope NONE, op `request_clarification`, clarification required, knowledge_available True
- Predicted: entity education_os , intent OVERVIEW, aspect OVERVIEW (2nd CAPABILITIES, margin 0.9485), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'education_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.8596 (margin 0.7744), aspect 0.9699, decision 0.8596 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization FAIL · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Seven different OS solutions exist; must ask which.

### V4_134 (ambiguous) — first failure: **scope**
- Query: `I want details of your AI platform`
- Expected: entity ['enterprise_ai_os', 'enterprise_agentic_ai'], aspect None, scope NONE, op `request_clarification`, clarification required, knowledge_available True
- Predicted: entity enterprise_ai_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'enterprise_ai_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.475 (margin 0.293), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization FAIL · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Could be Enterprise AI OS or the Enterprise & Agentic AI service.

### V4_137 (ambiguous) — first failure: **scope**
- Query: `we need an AI chatbot for our customers`
- Expected: entity ['ecommerce_os', 'enterprise_ai_os', 'enterprise_agentic_ai', 'real_estate_os', 'whatsapp_marketing'], aspect None, scope NONE, op `request_clarification`, clarification required, knowledge_available True
- Predicted: entity ecommerce_os , intent RECOMMENDATION, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'ecommerce_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.9164 (margin 0.8852), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization FAIL · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Chatbots appear in several offerings; need the use case.

### V4_138 (healthcare) — first failure: **entity**
- Query: `Do you have software to manage hospital beds, OPD appointments and patient records?`
- Expected: entity [], aspect None, scope NONE, op `request_clarification`, clarification allowed, knowledge_available False
- Predicted: entity pharma_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'pharma_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.6044 (margin 0.3165), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: No offering covers hospital operations.

### V4_139 (healthcare) — first failure: **entity**
- Query: `Can Pharma OS handle patient care workflows in our clinic?`
- Expected: entity [], aspect None, scope NONE, op `request_clarification`, clarification allowed, knowledge_available False
- Predicted: entity pharma_os , intent UNKNOWN, aspect CAPABILITIES (2nd WORKFLOW, margin 0.0374), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'pharma_os'}
- Confidence: entity 0.9734 (margin 0.9734), aspect 0.5187, decision 0.5187 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Pharma OS covers pharma quality/compliance, not clinic patient care.

