# Holdout v3 — LLM off

Generated 2026-09-27 15:59:22

## Manifest
```json
{
  "dataset": "semantic_holdout_v3.json",
  "dataset_sha": "bfc8e6351d83",
  "n": 130,
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
    "query_intelligence_engine.py": "c0eb084ba403",
    "semantic_arbitration.py": "b9b060f01659",
    "semantic_chat_pipeline.py": "fe83b3848d6c",
    "knowledge_tool_router.py": "dd656970555c",
    "knowledge_operation_executor.py": "b2b45bb21211"
  },
  "git_head": "71b4793"
}
```

## Decision metrics
| Metric | Value |
|---|---|
| entity | 89.2% |
| intent | not measured (no gold intent labels) |
| aspect | 86.2% |
| scope | 92.3% |
| canonicalization | 98.5% |
| operation | 80.8% |
| arguments | 91.5% |
| full_decision | 78.5% |
| evidence_availability | 97.7% |
| confidently wrong (decision conf ≥ 0.8) | 4 |
| confidently wrong (legacy: entity conf ≥ 0.8) | 11 |
| ECE (decision conf) | 0.2058 |
| ECE (legacy entity conf) | 0.0986 |
| LLM entity / aspect / any rate | 0.0% / 0.0% / 0.0% |
| LLM call success rate | 0.0% |
| Latency p50 / p95 | 177.8 / 328.4 ms |
| Catalog leakage | 0 |
| OOD leakage | 0 |
| Unknown product substituted | 1 |
| Clarification rate | 10.0% |

## First failure stage
| Stage | Queries |
|---|---|
| entity | 12 |
| aspect | 11 |
| scope | 4 |
| canonicalization | 0 |
| operation | 1 |
| arguments | 0 |
| evidence | 1 |

## By category
| Category | n | Decision |
|---|---|---|
| ambiguous | 5 | 80.0% |
| aspect | 16 | 75.0% |
| both | 3 | 100.0% |
| catalog | 8 | 37.5% |
| category_mismatch | 4 | 50.0% |
| company | 8 | 87.5% |
| context | 12 | 58.3% |
| conversational | 1 | 0.0% |
| direct | 12 | 100.0% |
| grammar | 4 | 75.0% |
| indirect | 7 | 100.0% |
| informal | 5 | 100.0% |
| minimal | 4 | 100.0% |
| multi | 6 | 83.3% |
| non_native | 4 | 75.0% |
| ood | 6 | 100.0% |
| problem | 14 | 64.3% |
| spelling | 7 | 100.0% |
| unknown_product | 4 | 75.0% |

## Failures

### V3_001 (conversational) — first failure: **entity**
- Query: `Hi! We're a mid-size retailer and I was wondering if you guys actually run marketing campaigns for clients?`
- Expected: entity ['ai_powered_marketing'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ecommerce_os , intent GREETING, aspect CLIENTS_CASE_STUDIES (2nd TARGET_USERS, margin 0.3812), scope SINGLE_ENTITY, op `list_case_studies` {'topic_entity_id': 'ecommerce_os'}
- Confidence: entity 0.6672 (margin 0.6086), aspect 0.6906, decision 0.6672 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Campaign execution (social, PPC, SEO) is the AI-Powered Marketing service.

### V3_002 (problem) — first failure: **aspect**
- Query: `we spend like 8 lakh a month on google and meta ads and our cost per acquisition just keeps going up, nothing we try works`
- Expected: entity ['ai_powered_marketing'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ai_powered_marketing , intent PRICING, aspect PRICING (2nd None, margin 1.0), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.3113 (margin 0.1641), aspect 1.0, decision 0.3113 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: PPC advertising with lower CPA / higher ROAS is an AI-Powered Marketing benefit.

### V3_005 (grammar) — first failure: **scope**
- Query: `Is your company doing the SEO and ads for ecommerce store also?`
- Expected: entity ['ai_powered_marketing'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ai_powered_marketing ['ai_powered_marketing', 'ecommerce_os'], intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope MULTI_ENTITY, op `get_service` {'entity_id': 'ai_powered_marketing'}
- Confidence: entity 0.95 (margin 0.5), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope FAIL · canonicalization PASS · operation PASS · arguments PASS · evidence PASS
- Gold rationale: SEO, PPC and E-commerce Growth are AI-Powered Marketing capabilities.

### V3_008 (non_native) — first failure: **entity**
- Query: `I am CMO of company. Please explain me your brand architecture engine, how it is working?`
- Expected: entity ['martech_360'], aspect ['OVERVIEW', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ganesh_gandhi_vadalani , intent LEADERSHIP, aspect WORKFLOW (2nd LEADERSHIP, margin 0.3887), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.425 (margin 0.1662), aspect 0.6891, decision 0.425 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: 'AI Brand Architecture & Strategy Engine' is MarTech 360's tagline; asks overview + how it works.

### V3_015 (problem) — first failure: **operation**
- Query: `Customer data lives in our CRM, ERP and three spreadsheets, with loads of duplicates. Nobody trusts the numbers anymore.`
- Expected: entity ['data_engineering'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity data_engineering , intent INTEGRATIONS, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.3719 (margin 0.0462), aspect 0.4, decision 0.3719 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Master data management / golden record is a Data Engineering capability.

### V3_019 (problem) — first failure: **entity**
- Query: `Our internal support bot keeps making up answers that aren't in our docs. Can you fix that?`
- Expected: entity ['enterprise_agentic_ai', 'enterprise_ai_os'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification allowed, knowledge_available True
- Predicted: entity ecommerce_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'ecommerce_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.54 (margin 0.4065), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Hallucination elimination via RAG is an Enterprise & Agentic AI benefit; Enterprise AI OS also has anti-hallucination guardrails.

### V3_022 (category_mismatch) — first failure: **entity**
- Query: `Is Enterprise and Agentic AI a platform I can subscribe to?`
- Expected: entity ['enterprise_agentic_ai'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity enterprise_ai_os , intent INTEGRATIONS, aspect OVERVIEW (2nd PRICING, margin 0.9482), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'enterprise_ai_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.5228 (margin 0.1221), aspect 0.9686, decision 0.5228 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Enterprise & Agentic AI is a service, user calls it a platform.

### V3_025 (problem) — first failure: **aspect**
- Query: `Our team is juggling OpenAI and open-source models by hand. We want something that routes prompts by cost and latency and logs token usage.`
- Expected: entity ['enterprise_ai_os'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity enterprise_ai_os , intent PRICING, aspect PRICING (2nd None, margin 1.0), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.4855 (margin 0.0105), aspect 1.0, decision 0.4855 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Hybrid LLM routing and telemetry are Enterprise AI OS workflow steps.

### V3_055 (category_mismatch) — first failure: **aspect**
- Query: `Do you provide WhatsApp marketing services?`
- Expected: entity ['whatsapp_marketing', 'ai_powered_marketing'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_product`, clarification allowed, knowledge_available True
- Predicted: entity whatsapp_marketing , intent CAPABILITIES, aspect CAPABILITIES (2nd OVERVIEW, margin 0.4054), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'whatsapp_marketing'}
- Confidence: entity 0.9694 (margin 0.964), aspect 0.7027, decision 0.7027 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: The WhatsApp Marketing Platform (product, with managed services) is the main match; AI-Powered Marketing also lists WhatsApp Marketing Automation.

### V3_063 (aspect) — first failure: **aspect**
- Query: `Why should we pay for AI strategy consulting instead of just starting a pilot ourselves?`
- Expected: entity ['ai_strategy'], aspect ['BENEFITS'], scope SINGLE_ENTITY, op `get_benefits`, clarification no, knowledge_available True
- Predicted: entity ai_strategy , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'ai_strategy', 'section': 'OVERVIEW'}
- Confidence: entity 0.8683 (margin 0.8129), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Benefits include avoiding costly pilot failures.

### V3_064 (aspect) — first failure: **aspect**
- Query: `how many weeks does the AI readiness audit usually take?`
- Expected: entity ['ai_strategy'], aspect ['FAQ', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity ai_strategy , intent COUNT, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'ai_strategy', 'section': 'OVERVIEW'}
- Confidence: entity 0.9995 (margin 0.9995), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Matches an AI Strategy FAQ.

### V3_065 (aspect) — first failure: **aspect**
- Query: `Which cloud data warehouses do you work with for data engineering? Snowflake? BigQuery?`
- Expected: entity ['data_engineering'], aspect ['FAQ'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity data_engineering , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'data_engineering', 'section': 'OVERVIEW'}
- Confidence: entity 0.975 (margin 0.975), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Matches a Data Engineering FAQ.

### V3_067 (aspect) — first failure: **aspect**
- Query: `which frameworks do u use for the multi agent stuff, crewai or autogen?`
- Expected: entity ['enterprise_agentic_ai'], aspect ['FAQ', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'enterprise_agentic_ai', 'section': 'OVERVIEW'}
- Confidence: entity 0.9933 (margin 0.9933), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Matches an Enterprise & Agentic AI FAQ; workflow mentions AutoGen/CrewAI.

### V3_081 (context) — first failure: **aspect**
- Query: `how long does it take?` (context: {'active_entity': 'martech_360', 'active_entities': ['martech_360'], 'previous_turns': ['What is MarTech 360?']})
- Expected: entity ['martech_360'], aspect ['FAQ', 'WORKFLOW', 'BENEFITS'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity martech_360 , intent UNKNOWN, aspect PRICING (2nd WORKFLOW, margin 0.5655), scope SINGLE_ENTITY, op `get_pricing` {'entity_id': 'martech_360', 'section': 'PRICING'}
- Confidence: entity 0.95 (margin 0.95), aspect 0.7416, decision 0.7416 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Follows MarTech 360; FAQ on process duration and benefit notes 2-3 week sprint.

### V3_084 (context) — first failure: **entity**
- Query: `what about the other one?` (context: {'active_entity': 'whatsapp_marketing', 'active_entities': ['ecommerce_os', 'whatsapp_marketing'], 'previous_turns': ['Tell me about E-Commerce OS', 'And the WhatsApp marketing platform?']})
- Expected: entity ['ecommerce_os'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity whatsapp_marketing , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_product` {'entity_id': 'whatsapp_marketing', 'section': 'OVERVIEW'}
- Confidence: entity 0.95 (margin 0.95), aspect 1.0, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: 'The other one' refers to E-Commerce OS, the non-active entity in context.

### V3_085 (context) — first failure: **entity**
- Query: `is it any good for education brands?` (context: {'active_entity': 'influencer_marketing', 'active_entities': ['influencer_marketing'], 'previous_turns': ['tell me about your influencer platform']})
- Expected: entity ['influencer_marketing'], aspect ['TARGET_USERS'], scope SINGLE_ENTITY, op `get_target_users`, clarification no, knowledge_available True
- Predicted: entity education_os , intent UNKNOWN, aspect TARGET_USERS (2nd CAPABILITIES, margin 0.9179), scope SINGLE_ENTITY, op `get_target_users` {'entity_id': 'education_os'}
- Confidence: entity 0.4993 (margin 0.2506), aspect 0.9454, decision 0.4993 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation PASS · arguments FAIL · evidence FAIL
- Gold rationale: Follows influencer context; Education Brands is a listed intended user.

### V3_087 (context) — first failure: **aspect**
- Query: `how do u stop it from hallucinating` (context: {'active_entity': 'enterprise_agentic_ai', 'active_entities': ['enterprise_agentic_ai'], 'previous_turns': ['Tell me about Enterprise & Agentic AI']})
- Expected: entity ['enterprise_agentic_ai'], aspect ['FAQ', 'BENEFITS'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'enterprise_agentic_ai', 'section': 'OVERVIEW'}
- Confidence: entity 0.95 (margin 0.95), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Follows Enterprise & Agentic AI; matches FAQ on hallucinations.

### V3_088 (context) — first failure: **entity**
- Query: `who founded it?` (context: {'active_entity': 'company_info', 'active_entities': ['company_info'], 'previous_turns': ['What is CittaAI?']})
- Expected: entity ['leadership_info'], aspect ['LEADERSHIP'], scope SINGLE_ENTITY, op `get_leadership`, clarification no, knowledge_available True
- Predicted: entity company_info , intent LEADERSHIP, aspect LEADERSHIP (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_leadership` {}
- Confidence: entity 0.95 (margin 0.95), aspect 1.0, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation PASS · arguments PASS · evidence PASS
- Gold rationale: Follow-up about the company's founders.

### V3_097 (multi) — first failure: **entity**
- Query: `how is pharma os different from smart cities os`
- Expected: entity ['pharma_os', 'smart_cities_os'], aspect ['OVERVIEW', 'CAPABILITIES'], scope MULTI_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity pharma_os , intent UNKNOWN, aspect WORKFLOW (2nd CAPABILITIES, margin 0.0074), scope SINGLE_ENTITY, op `get_workflow` {'entity_id': 'pharma_os'}
- Confidence: entity 0.6289 (margin 0.2832), aspect 0.4536, decision 0.4536 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Explicit comparison.

### V3_100 (catalog) — first failure: **entity**
- Query: `wat services u offer`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL_SERVICES, op `list_services`, clarification no, knowledge_available True
- Predicted: entity whatsapp_marketing , intent UNKNOWN, aspect OVERVIEW (2nd CAPABILITIES, margin 0.5408), scope SINGLE_ENTITY, op `get_product` {'entity_id': 'whatsapp_marketing', 'section': 'OVERVIEW'}
- Confidence: entity 0.5603 (margin 0.4644), aspect 0.7704, decision 0.5603 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Service listing.

### V3_102 (catalog) — first failure: **scope**
- Query: `Which industries do you build solutions for?`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL, op `list_catalog`, clarification no, knowledge_available True
- Predicted: entity None , intent UNKNOWN, aspect CATALOG_LIST (2nd None, margin 1.0), scope ALL_SOLUTIONS, op `list_solutions` {}
- Confidence: entity 0.0 (margin 0.0), aspect 0.95, decision 0.95 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Industry coverage = whole catalog listing.

### V3_103 (catalog) — first failure: **aspect**
- Query: `show me everything you've got`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL, op `list_catalog`, clarification no, knowledge_available True
- Predicted: entity None , intent UNKNOWN, aspect OVERVIEW (2nd CLIENTS_CASE_STUDIES, margin 0.9466), scope OUT_OF_DOMAIN, op `decline_out_of_domain` {}
- Confidence: entity 0.0 (margin 0.0), aspect 0.9654, decision 0.7 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Whole catalog.

### V3_104 (catalog) — first failure: **entity**
- Query: `do you have any of those OS platforms? which ones?`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL_SOLUTIONS, op `list_solutions`, clarification no, knowledge_available True
- Predicted: entity ecommerce_os , intent UNKNOWN, aspect OVERVIEW (2nd CAPABILITIES, margin 0.9768), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'ecommerce_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.6748 (margin 0.5184), aspect 0.9884, decision 0.6748 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: All OS offerings are solutions.

### V3_105 (catalog) — first failure: **entity**
- Query: `What kinds of AI consulting do you provide?`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL_SERVICES, op `list_services`, clarification no, knowledge_available True
- Predicted: entity ai_strategy , intent CAPABILITIES, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'ai_strategy'}
- Confidence: entity 0.6761 (margin 0.461), aspect 1.0, decision 0.6761 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Consulting = services listing.

### V3_110 (company) — first failure: **evidence**
- Query: `Can I get your phone number or email id?`
- Expected: entity ['contact_info'], aspect ['CONTACT'], scope SINGLE_ENTITY, op `get_contact`, clarification no, knowledge_available False
- Predicted: entity contact_info , intent CONTACT, aspect CONTACT (2nd PRICING, margin 0.9846), scope SINGLE_ENTITY, op `get_contact` {}
- Confidence: entity 0.9923 (margin 1.0), aspect 0.9923, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation PASS · arguments PASS · evidence FAIL
- Gold rationale: No phone or email is published.

### V3_113 (company) — first failure: **aspect**
- Query: `Tell me more about the jewellery brand campaign you did`
- Expected: entity ['jewellery_brand_roi'], aspect ['CLIENTS_CASE_STUDIES'], scope SINGLE_ENTITY, op `get_case_study`, clarification no, knowledge_available True
- Predicted: entity jewellery_brand_roi , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'jewellery_brand_roi'}
- Confidence: entity 0.475 (margin 0.2286), aspect 1.0, decision 0.475 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Specific case study.

### V3_120 (unknown_product) — first failure: **entity**
- Query: `Tell me about Healthcare OS`
- Expected: entity [], aspect None, scope UNKNOWN_ENTITY, op `request_clarification`, clarification allowed, knowledge_available False
- Predicted: entity pharma_os , intent OVERVIEW, aspect OVERVIEW (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'pharma_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.8005 (margin 0.7122), aspect 1.0, decision 0.8005 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Named product does not exist in the catalog.

### V3_127 (ambiguous) — first failure: **scope**
- Query: `how does the platform work?`
- Expected: entity [], aspect None, scope NONE, op `request_clarification`, clarification required, knowledge_available True
- Predicted: entity influencer_marketing , intent HOW_IT_WORKS, aspect OVERVIEW (2nd WORKFLOW, margin 0.0034), scope SINGLE_ENTITY, op `get_product` {'entity_id': 'influencer_marketing', 'section': 'OVERVIEW'}
- Confidence: entity 0.5084 (margin 0.1542), aspect 0.5017, decision 0.5017 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization FAIL · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Several platforms; no context.

### V3_129 (problem) — first failure: **scope**
- Query: `We run a chain of hospitals and need a system for patient appointment booking and electronic health records.`
- Expected: entity [], aspect None, scope NONE, op `request_clarification`, clarification required, knowledge_available False
- Predicted: entity pharma_os , intent RECOMMENDATION, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'pharma_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.611 (margin 0.3502), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization FAIL · operation FAIL · arguments FAIL · evidence —
- Gold rationale: No offering covers hospital EHR/appointments (Pharma OS is manufacturing/compliance).

