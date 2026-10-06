# semantic_holdout_v5.json — LLM on

Generated 2026-09-29 21:56:08

## Manifest
```json
{
  "dataset": "semantic_holdout_v5.json",
  "dataset_sha": "9bc9f928b6f8",
  "n": 150,
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
    "query_intelligence_engine.py": "702691e769d8",
    "semantic_arbitration.py": "e3e58a594afd",
    "semantic_chat_pipeline.py": "839777f055e7",
    "knowledge_tool_router.py": "cb8ca337e0b0",
    "knowledge_operation_executor.py": "b2b45bb21211"
  },
  "git_head": "71b4793"
}
```

## Decision metrics
| Metric | Value |
|---|---|
| entity | 94.7% |
| intent | not measured (no gold intent labels) |
| aspect | 90.0% |
| scope | 92.7% |
| canonicalization | 99.3% |
| operation | 86.7% |
| operation_strict_label_match | 58.0% |
| arguments | 99.3% |
| full_decision | 86.0% |
| evidence_availability | 100.0% |
| confidently wrong (decision conf ≥ 0.8) | 12 |
| confidently wrong (legacy: entity conf ≥ 0.8) | 12 |
| ECE (decision conf) | 0.1232 |
| ECE (legacy entity conf) | 0.0898 |
| LLM entity / aspect / any rate | 27.3% / 22.7% / 47.3% |
| LLM call success rate | 100.0% |
| Latency p50 / p95 | 272.6 / 6109.6 ms |
| Catalog leakage | 0 |
| OOD leakage | 0 |
| Unknown product substituted | 2 |
| Clarification rate | 8.7% |

## First failure stage
| Stage | Queries |
|---|---|
| entity | 7 |
| aspect | 10 |
| scope | 4 |
| canonicalization | 0 |
| operation | 0 |
| arguments | 0 |
| evidence | 0 |

## By category
| Category | n | Decision |
|---|---|---|
| ambiguous | 6 | 50.0% |
| aspect | 23 | 78.3% |
| both | 3 | 66.7% |
| catalog | 8 | 50.0% |
| category_mismatch | 2 | 100.0% |
| company | 11 | 81.8% |
| context | 12 | 100.0% |
| direct | 13 | 100.0% |
| grammar | 5 | 100.0% |
| healthcare | 4 | 50.0% |
| indirect | 2 | 100.0% |
| informal | 8 | 87.5% |
| minimal | 3 | 100.0% |
| multi | 7 | 100.0% |
| non_native | 8 | 100.0% |
| ood | 7 | 85.7% |
| problem | 13 | 92.3% |
| spelling | 11 | 90.9% |
| unknown_product | 4 | 100.0% |

## Failures

### V5_038 (spelling) — first failure: **aspect**
- Query: `influncer platfrom for brands and agencys`
- Expected: entity ['influencer_marketing'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_product`, clarification no, knowledge_available True
- Predicted: entity influencer_marketing , intent UNKNOWN, aspect TARGET_USERS (2nd None, margin 1.0), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.7745 (margin 0.7138), aspect 1.0, decision 0.7745 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Misspelled product name.

### V5_039 (informal) — first failure: **aspect**
- Query: `how do i find micro creators for my cafe franchise lol`
- Expected: entity ['influencer_marketing'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_product`, clarification no, knowledge_available True
- Predicted: entity influencer_marketing , intent UNKNOWN, aspect WORKFLOW (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_workflow` {'entity_id': 'influencer_marketing'}
- Confidence: entity 0.929 (margin 0.9128), aspect 1.0, decision 0.929 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Influencer discovery for Local Franchises (a listed target user).

### V5_042 (problem) — first failure: **entity**
- Query: `Our brand positioning feels stale and our CMO is tired of agency workshops and opinion-based decks. She wants a brand strategy grounded in actual market data and demand signals.`
- Expected: entity ['martech_360', 'ai_powered_marketing'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification allowed, knowledge_available True
- Predicted: entity ganesh_gandhi_vadalani , intent LEADERSHIP, aspect LEADERSHIP (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_leadership` {'person_id': 'ganesh_gandhi_vadalani'}
- Confidence: entity 1.0 (margin 1.0), aspect 1.0, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: MarTech 360 explicitly contrasts evidence-driven brand strategy with workshops; AI-Powered Marketing also lists Branding & Strategy.

### V5_067 (aspect) — first failure: **aspect**
- Query: `How long does the AI readiness assessment take?`
- Expected: entity ['ai_strategy'], aspect ['FAQ'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity ai_strategy , intent UNKNOWN, aspect WORKFLOW (2nd FAQ, margin 0.1472), scope SINGLE_ENTITY, op `get_workflow` {'entity_id': 'ai_strategy'}
- Confidence: entity 0.975 (margin 0.975), aspect 0.437, decision 0.437 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Specific FAQ of AI Strategy & Advisory.

### V5_069 (aspect) — first failure: **aspect**
- Query: `What uptime can you guarantee for real-time streaming pipelines in the Data Engineering service?`
- Expected: entity ['data_engineering'], aspect ['BENEFITS', 'FAQ'], scope SINGLE_ENTITY, op `get_benefits`, clarification no, knowledge_available True
- Predicted: entity data_engineering , intent UNKNOWN, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'data_engineering'}
- Confidence: entity 0.9748 (margin 0.9748), aspect 1.0, decision 0.9748 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: 99.99% uptime SLA is a Data Engineering benefit; FAQ on streaming reliability.

### V5_074 (aspect) — first failure: **aspect**
- Query: `Which frameworks do you use when building multi-agent systems for enterprises?`
- Expected: entity ['enterprise_agentic_ai'], aspect ['FAQ', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent INTEGRATIONS, aspect CAPABILITIES (2nd TARGET_USERS, margin 0.8883), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'enterprise_agentic_ai'}
- Confidence: entity 0.9741 (margin 0.9741), aspect 0.9336, decision 0.9336 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: FAQ of Enterprise & Agentic AI; workflow names AutoGen/CrewAI.

### V5_079 (aspect) — first failure: **aspect**
- Query: `What results has MarTech 360 actually delivered for clients?`
- Expected: entity ['martech_360'], aspect ['BENEFITS'], scope SINGLE_ENTITY, op `get_benefits`, clarification no, knowledge_available True
- Predicted: entity martech_360 , intent UNKNOWN, aspect CLIENTS_CASE_STUDIES (2nd BENEFITS, margin 0.8704), scope SINGLE_ENTITY, op `list_case_studies` {'topic_entity_id': 'martech_360'}
- Confidence: entity 0.9388 (margin 0.9162), aspect 0.9352, decision 0.9352 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Benefits list outcomes (e.g. 62% more enquiries, 2.4x bookings).

### V5_080 (aspect) — first failure: **aspect**
- Query: `How much faster are quality reviews with Pharma OS?`
- Expected: entity ['pharma_os'], aspect ['BENEFITS'], scope SINGLE_ENTITY, op `get_benefits`, clarification no, knowledge_available True
- Predicted: entity pharma_os , intent PRICING, aspect PRICING (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_pricing` {'entity_id': 'pharma_os', 'section': 'PRICING'}
- Confidence: entity 0.975 (margin 0.975), aspect 1.0, decision 0.975 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Benefit: 50% faster reviews.

### V5_108 (both) — first failure: **aspect**
- Query: `which data sources do both of them use?` (context: {'active_entity': 'martech_360', 'active_entities': ['martech_360', 'ai_powered_marketing'], 'previous_turns': ['compare martech 360 and ai powered marketing']})
- Expected: entity ['martech_360', 'ai_powered_marketing'], aspect ['FAQ', 'WORKFLOW'], scope MULTI_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity martech_360 ['martech_360', 'ai_powered_marketing'], intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.5), scope MULTI_ENTITY, op `get_service` {'entity_id': 'martech_360'}
- Confidence: entity 0.95 (margin 0.5), aspect 0.9, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: 'Both' resolves to the pair in context.

### V5_115 (catalog) — first failure: **scope**
- Query: `Which industries do you work with?`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL, op `list_catalog`, clarification no, knowledge_available True
- Predicted: entity None , intent UNKNOWN, aspect CATALOG_LIST (2nd CAPABILITIES, margin 1.0), scope ALL_SOLUTIONS, op `list_solutions` {}
- Confidence: entity 0.0 (margin 0.0), aspect 0.95, decision 0.95 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Industries -> whole catalog.

### V5_116 (catalog) — first failure: **scope**
- Query: `wat all OS platforms u have`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL_SOLUTIONS, op `list_solutions`, clarification no, knowledge_available True
- Predicted: entity None , intent UNKNOWN, aspect CATALOG_LIST (2nd CAPABILITIES, margin 1.0), scope ALL, op `list_catalog` {}
- Confidence: entity 0.0 (margin 0.0), aspect 0.95, decision 0.95 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: The '... OS' offerings are the solutions.

### V5_117 (catalog) — first failure: **entity**
- Query: `Kindly share the complete portfolio of your offerings for our vendor evaluation.`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL, op `list_catalog`, clarification no, knowledge_available True
- Predicted: entity influencer_marketing , intent UNKNOWN, aspect OVERVIEW (2nd CLIENTS_CASE_STUDIES, margin 0.8686), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.3174 (margin 0.0677), aspect 0.9239, decision 0.3174 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Full portfolio request.

### V5_118 (catalog) — first failure: **entity**
- Query: `any consulting services?`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL_SERVICES, op `list_services`, clarification no, knowledge_available True
- Predicted: entity real_estate_os , intent UNKNOWN, aspect CAPABILITIES (2nd OVERVIEW, margin 0.3328), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.4 (margin 0.0866), aspect 0.586, decision 0.4 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Consulting = services list.

### V5_121 (company) — first failure: **entity**
- Query: `Who's your CTO?`
- Expected: entity ['leadership_info'], aspect ['LEADERSHIP'], scope SINGLE_ENTITY, op `get_leadership`, clarification no, knowledge_available True
- Predicted: entity akhil_reddy , intent LEADERSHIP, aspect LEADERSHIP (2nd CLIENTS_CASE_STUDIES, margin 0.9312), scope SINGLE_ENTITY, op `get_leadership` {'person_id': 'akhil_reddy'}
- Confidence: entity 0.9656 (margin 1.0), aspect 0.9656, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation PASS · arguments PASS · evidence PASS
- Gold rationale: Specific leader role.

### V5_124 (company) — first failure: **entity**
- Query: `are you guys open on saturdays?`
- Expected: entity ['contact_info'], aspect ['CONTACT'], scope SINGLE_ENTITY, op `get_contact`, clarification no, knowledge_available True
- Predicted: entity None , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope OUT_OF_DOMAIN, op `decline_out_of_domain` {}
- Confidence: entity 0.0 (margin 0.0), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Business hours Mon-Fri.

### V5_132 (ood) — first failure: **entity**
- Query: `my python for loop keeps printing the same number, can you debug it: for i in range(5): print(x)`
- Expected: entity [], aspect None, scope OUT_OF_DOMAIN, op `decline_out_of_domain`, clarification no, knowledge_available False
- Predicted: entity pharma_os , intent UNKNOWN, aspect FAQ (2nd None, margin 1.0), scope GENERAL, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.1817 (margin 0.1067), aspect 1.0, decision 0.0 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Personal coding help is unrelated to CittaAI offerings.

### V5_143 (ambiguous) — first failure: **aspect**
- Query: `do you do conversational AI?`
- Expected: entity ['enterprise_agentic_ai', 'enterprise_ai_os', 'ecommerce_os'], aspect ['CAPABILITIES'], scope NONE, op `request_clarification`, clarification allowed, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'enterprise_agentic_ai', 'section': 'OVERVIEW'}
- Confidence: entity 0.9058 (margin 0.8873), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Conversational AI is a capability of three offerings.

### V5_144 (ambiguous) — first failure: **aspect**
- Query: `multi-agent systems`
- Expected: entity ['enterprise_agentic_ai', 'enterprise_ai_os'], aspect ['CAPABILITIES'], scope NONE, op `request_clarification`, clarification allowed, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'enterprise_agentic_ai', 'section': 'OVERVIEW'}
- Confidence: entity 0.8611 (margin 0.75), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Both the service and the platform list multi-agent systems.

### V5_146 (ambiguous) — first failure: **scope**
- Query: `I need help with our data`
- Expected: entity ['data_engineering', 'enterprise_ai_os', 'ai_strategy'], aspect ['OVERVIEW'], scope NONE, op `request_clarification`, clarification required, knowledge_available True
- Predicted: entity data_engineering , intent RECOMMENDATION, aspect OVERVIEW (2nd BENEFITS, margin 0.3134), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'data_engineering', 'section': 'OVERVIEW'}
- Confidence: entity 0.6695 (margin 0.5565), aspect 0.634, decision 0.634 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': True, 'aspect_ok': True}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization FAIL · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Could be data engineering, AI platform data pipelines, or data-maturity audit.

### V5_147 (healthcare) — first failure: **entity**
- Query: `Do you have a hospital management system for OPD, bed allocation and billing?`
- Expected: entity [], aspect None, scope NONE, op `request_clarification`, clarification allowed, knowledge_available False
- Predicted: entity contact_info , intent LOCATION, aspect CONTACT (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_contact` {}
- Confidence: entity 1.0 (margin 1.0), aspect 1.0, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: No offering covers hospital operations; Pharma OS is pharma manufacturing/QA.

### V5_149 (healthcare) — first failure: **scope**
- Query: `Can your AI help ICU doctors make patient care decisions?`
- Expected: entity [], aspect None, scope NONE, op `request_clarification`, clarification allowed, knowledge_available False
- Predicted: entity None , intent UNKNOWN, aspect FAQ (2nd None, margin 1.0), scope OUT_OF_DOMAIN, op `decline_out_of_domain` {}
- Confidence: entity 0.0 (margin 0.0), aspect 1.0, decision 0.8 · LLM {'entity_attempted': True, 'entity_ok': True, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Clinical decision support not in any offering's content.

