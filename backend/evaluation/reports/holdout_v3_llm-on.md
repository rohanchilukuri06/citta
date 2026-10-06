# Holdout v3 — LLM on

Generated 2026-09-29 20:56:10

## Manifest
```json
{
  "dataset": "semantic_holdout_v3.json",
  "dataset_sha": "bfc8e6351d83",
  "n": 130,
  "llm_mode": "on",
  "llm_provider": "groq",
  "llm_model": "openai/gpt-oss-20b",
  "llm_fallback": "gemini",
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
| entity | 93.1% |
| intent | not measured (no gold intent labels) |
| aspect | 83.8% |
| scope | 93.1% |
| canonicalization | 99.2% |
| operation | 80.0% |
| arguments | 95.4% |
| full_decision | 78.5% |
| evidence_availability | 98.8% |
| confidently wrong (decision conf ≥ 0.8) | 4 |
| confidently wrong (legacy: entity conf ≥ 0.8) | 11 |
| ECE (decision conf) | 0.196 |
| ECE (legacy entity conf) | 0.1296 |
| LLM entity / aspect / any rate | 16.2% / 6.9% / 19.2% |
| LLM call success rate | 96.7% |
| Latency p50 / p95 | 226.4 / 3250.1 ms |
| Catalog leakage | 0 |
| OOD leakage | 0 |
| Unknown product substituted | 1 |
| Clarification rate | 8.5% |

## First failure stage
| Stage | Queries |
|---|---|
| entity | 8 |
| aspect | 16 |
| scope | 3 |
| canonicalization | 0 |
| operation | 1 |
| arguments | 0 |
| evidence | 1 |

## By category
| Category | n | Decision |
|---|---|---|
| ambiguous | 5 | 100.0% |
| aspect | 16 | 75.0% |
| both | 3 | 100.0% |
| catalog | 8 | 37.5% |
| category_mismatch | 4 | 75.0% |
| company | 8 | 87.5% |
| context | 12 | 66.7% |
| conversational | 1 | 0.0% |
| direct | 12 | 100.0% |
| grammar | 4 | 75.0% |
| indirect | 7 | 100.0% |
| informal | 5 | 80.0% |
| minimal | 4 | 100.0% |
| multi | 6 | 83.3% |
| non_native | 4 | 75.0% |
| ood | 6 | 100.0% |
| problem | 14 | 50.0% |
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
- Predicted: entity ai_powered_marketing , intent PRICING, aspect BENEFITS (2nd PRICING, margin 0.157), scope SINGLE_ENTITY, op `get_benefits` {'entity_id': 'ai_powered_marketing'}
- Confidence: entity 0.6441 (margin 0.5801), aspect 0.5785, decision 0.5785 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: PPC advertising with lower CPA / higher ROAS is an AI-Powered Marketing benefit.

### V3_003 (informal) — first failure: **aspect**
- Query: `yo can u guys do seo + social media for my brand`
- Expected: entity ['ai_powered_marketing'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ai_powered_marketing , intent UNKNOWN, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'ai_powered_marketing'}
- Confidence: entity 0.625 (margin 0.4376), aspect 1.0, decision 0.625 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: SEO and Social Media Marketing are AI-Powered Marketing capabilities.

### V3_005 (grammar) — first failure: **scope**
- Query: `Is your company doing the SEO and ads for ecommerce store also?`
- Expected: entity ['ai_powered_marketing'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ai_powered_marketing ['ai_powered_marketing', 'ecommerce_os'], intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope MULTI_ENTITY, op `get_service` {'entity_id': 'ai_powered_marketing'}
- Confidence: entity 0.95 (margin 0.5), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope FAIL · canonicalization PASS · operation PASS · arguments PASS · evidence PASS
- Gold rationale: SEO, PPC and E-commerce Growth are AI-Powered Marketing capabilities.

### V3_007 (problem) — first failure: **aspect**
- Query: `Our brand messaging feels random - every channel says something different and we've never had a positioning strategy that's actually backed by data.`
- Expected: entity ['martech_360', 'ai_powered_marketing'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification allowed, knowledge_available True
- Predicted: entity martech_360 , intent UNKNOWN, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'martech_360'}
- Confidence: entity 0.6918 (margin 0.4833), aspect 1.0, decision 0.6918 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Data-driven brand positioning is MarTech 360's core; AI-Powered Marketing also lists Branding & Strategy.

### V3_008 (non_native) — first failure: **operation**
- Query: `I am CMO of company. Please explain me your brand architecture engine, how it is working?`
- Expected: entity ['martech_360'], aspect ['OVERVIEW', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity martech_360 , intent LEADERSHIP, aspect WORKFLOW (2nd LEADERSHIP, margin 0.6829), scope SINGLE_ENTITY, op `get_workflow` {'entity_id': 'martech_360'}
- Confidence: entity 0.5311 (margin 0.2735), aspect 0.8387, decision 0.5311 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: 'AI Brand Architecture & Strategy Engine' is MarTech 360's tagline; asks overview + how it works.

### V3_015 (problem) — first failure: **aspect**
- Query: `Customer data lives in our CRM, ERP and three spreadsheets, with loads of duplicates. Nobody trusts the numbers anymore.`
- Expected: entity ['data_engineering'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity data_engineering , intent INTEGRATIONS, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'data_engineering'}
- Confidence: entity 0.6987 (margin 0.5571), aspect 1.0, decision 0.6987 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Master data management / golden record is a Data Engineering capability.

### V3_019 (problem) — first failure: **aspect**
- Query: `Our internal support bot keeps making up answers that aren't in our docs. Can you fix that?`
- Expected: entity ['enterprise_agentic_ai', 'enterprise_ai_os'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_service`, clarification allowed, knowledge_available True
- Predicted: entity enterprise_ai_os , intent UNKNOWN, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'enterprise_ai_os'}
- Confidence: entity 0.595 (margin 0.3602), aspect 1.0, decision 0.595 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Hallucination elimination via RAG is an Enterprise & Agentic AI benefit; Enterprise AI OS also has anti-hallucination guardrails.

### V3_025 (problem) — first failure: **aspect**
- Query: `Our team is juggling OpenAI and open-source models by hand. We want something that routes prompts by cost and latency and logs token usage.`
- Expected: entity ['enterprise_ai_os'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity enterprise_ai_os , intent PRICING, aspect CAPABILITIES (2nd PRICING, margin 0.177), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'enterprise_ai_os'}
- Confidence: entity 0.6488 (margin 0.3609), aspect 0.5885, decision 0.5885 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Hybrid LLM routing and telemetry are Enterprise AI OS workflow steps.

### V3_029 (problem) — first failure: **aspect**
- Query: `I run a D2C store. Orders, returns and stock are tracked in four different tools and we keep overselling items.`
- Expected: entity ['ecommerce_os'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity ecommerce_os , intent UNKNOWN, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'ecommerce_os'}
- Confidence: entity 0.772 (margin 0.6906), aspect 1.0, decision 0.772 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Inventory sync and order lifecycle are E-Commerce OS.

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
- Predicted: entity pharma_os , intent UNKNOWN, aspect CAPABILITIES (2nd WORKFLOW, margin 0.5565), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'pharma_os'}
- Confidence: entity 0.6289 (margin 0.2832), aspect 0.7562, decision 0.6289 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Explicit comparison.

### V3_100 (catalog) — first failure: **entity**
- Query: `wat services u offer`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL_SERVICES, op `list_services`, clarification no, knowledge_available True
- Predicted: entity whatsapp_marketing , intent UNKNOWN, aspect CAPABILITIES (2nd OVERVIEW, margin 0.4986), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.5603 (margin 0.4644), aspect 0.7493, decision 0.5603 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
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
- Predicted: entity jewellery_brand_roi , intent UNKNOWN, aspect OVERVIEW (2nd OVERVIEW, margin -0.1954), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'jewellery_brand_roi'}
- Confidence: entity 0.6621 (margin 0.5128), aspect 0.4023, decision 0.4023 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Specific case study.

### V3_120 (unknown_product) — first failure: **entity**
- Query: `Tell me about Healthcare OS`
- Expected: entity [], aspect None, scope UNKNOWN_ENTITY, op `request_clarification`, clarification allowed, knowledge_available False
- Predicted: entity pharma_os , intent OVERVIEW, aspect OVERVIEW (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'pharma_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.8005 (margin 0.7122), aspect 1.0, decision 0.8005 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Named product does not exist in the catalog.

### V3_129 (problem) — first failure: **scope**
- Query: `We run a chain of hospitals and need a system for patient appointment booking and electronic health records.`
- Expected: entity [], aspect None, scope NONE, op `request_clarification`, clarification required, knowledge_available False
- Predicted: entity pharma_os , intent RECOMMENDATION, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'pharma_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.611 (margin 0.3502), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization FAIL · operation FAIL · arguments FAIL · evidence —
- Gold rationale: No offering covers hospital EHR/appointments (Pharma OS is manufacturing/compliance).

