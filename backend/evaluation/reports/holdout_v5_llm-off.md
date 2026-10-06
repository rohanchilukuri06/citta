# semantic_holdout_v5.json — LLM off

Generated 2026-09-29 21:51:26

## Manifest
```json
{
  "dataset": "semantic_holdout_v5.json",
  "dataset_sha": "9bc9f928b6f8",
  "n": 150,
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
| entity | 90.7% |
| intent | not measured (no gold intent labels) |
| aspect | 83.3% |
| scope | 92.0% |
| canonicalization | 98.7% |
| operation | 76.0% |
| operation_strict_label_match | 70.7% |
| arguments | 97.3% |
| full_decision | 74.7% |
| evidence_availability | 100.0% |
| confidently wrong (decision conf ≥ 0.8) | 11 |
| confidently wrong (legacy: entity conf ≥ 0.8) | 22 |
| ECE (decision conf) | 0.2129 |
| ECE (legacy entity conf) | 0.1545 |
| LLM entity / aspect / any rate | 0.0% / 0.0% / 0.0% |
| LLM call success rate | 0.0% |
| Latency p50 / p95 | 182.5 / 267.5 ms |
| Catalog leakage | 0 |
| OOD leakage | 0 |
| Unknown product substituted | 2 |
| Clarification rate | 12.7% |

## First failure stage
| Stage | Queries |
|---|---|
| entity | 12 |
| aspect | 19 |
| scope | 4 |
| canonicalization | 0 |
| operation | 3 |
| arguments | 0 |
| evidence | 0 |

## By category
| Category | n | Decision |
|---|---|---|
| ambiguous | 6 | 33.3% |
| aspect | 23 | 69.6% |
| both | 3 | 66.7% |
| catalog | 8 | 50.0% |
| category_mismatch | 2 | 100.0% |
| company | 11 | 72.7% |
| context | 12 | 75.0% |
| direct | 13 | 100.0% |
| grammar | 5 | 60.0% |
| healthcare | 4 | 75.0% |
| indirect | 2 | 100.0% |
| informal | 8 | 75.0% |
| minimal | 3 | 100.0% |
| multi | 7 | 100.0% |
| non_native | 8 | 75.0% |
| ood | 7 | 71.4% |
| problem | 13 | 61.5% |
| spelling | 11 | 81.8% |
| unknown_product | 4 | 100.0% |

## Failures

### V5_002 (problem) — first failure: **operation**
- Query: `honestly our instagram posts barely reach anyone and google ads are burning through our budget with almost no leads. we tried two agencies already. can you actually fix this?`
- Expected: entity ['ai_powered_marketing'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ai_powered_marketing , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.3874 (margin 0.0922), aspect 0.4, decision 0.3874 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Social media + PPC problems map to AI-Powered Marketing capabilities (Social Media Marketing, PPC, lower CPA).

### V5_004 (informal) — first failure: **operation**
- Query: `need someone to handle our socials + content & design stuff, is that u?`
- Expected: entity ['ai_powered_marketing'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ai_powered_marketing , intent RECOMMENDATION, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.4486 (margin 0.2214), aspect 1.0, decision 0.4486 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Social Media Marketing and Content & Design are AI-Powered Marketing capabilities.

### V5_008 (grammar) — first failure: **aspect**
- Query: `we wants a proper roadmap for adopt AI in our company, you are doing consulting for this?`
- Expected: entity ['ai_strategy'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity ai_strategy , intent UNKNOWN, aspect TARGET_USERS (2nd OVERVIEW, margin 0.8857), scope SINGLE_ENTITY, op `get_target_users` {'entity_id': 'ai_strategy'}
- Confidence: entity 0.9458 (margin 0.9079), aspect 0.9308, decision 0.9308 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Strategic roadmap is an AI Strategy & Advisory capability.

### V5_012 (problem) — first failure: **operation**
- Query: `Customer records are duplicated across our CRM, billing and support systems, nobody trusts the numbers, and our monthly reports take hours to run. Help?`
- Expected: entity ['data_engineering'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity data_engineering , intent INTEGRATIONS, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.382 (margin 0.1873), aspect 1.0, decision 0.382 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Master data management/golden record and fast warehouse queries are Data Engineering capabilities/benefits.

### V5_024 (non_native) — first failure: **aspect**
- Query: `Our college is having 3 campus. One software can manage all campus students and faculty together?`
- Expected: entity ['education_os'], aspect ['CAPABILITIES', 'BENEFITS', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_capabilities`, clarification no, knowledge_available True
- Predicted: entity education_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'education_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.9747 (margin 0.9747), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Multi-college LMS and campus hierarchy management are Education OS capabilities.

### V5_029 (spelling) — first failure: **entity**
- Query: `agentic ai consultng for enterprize`
- Expected: entity ['enterprise_agentic_ai'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity enterprise_ai_os , intent INTEGRATIONS, aspect OVERVIEW (2nd CAPABILITIES, margin -0.21), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.495 (margin 0.047), aspect 0.395, decision 0.395 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Misspelled service name.

### V5_030 (problem) — first failure: **entity**
- Query: `Our support chatbot keeps making up answers that aren't in our documents and customers are getting annoyed. Is that something you can fix?`
- Expected: entity ['enterprise_agentic_ai', 'enterprise_ai_os'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification allowed, knowledge_available True
- Predicted: entity ecommerce_os , intent UNKNOWN, aspect CAPABILITIES (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_capabilities` {'entity_id': 'ecommerce_os'}
- Confidence: entity 0.8051 (margin 0.6905), aspect 1.0, decision 0.8051 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation PASS · arguments FAIL · evidence PASS
- Gold rationale: Hallucination elimination via RAG is a benefit of Enterprise & Agentic AI; Enterprise AI OS also has anti-hallucination guardrails.

### V5_032 (problem) — first failure: **entity**
- Query: `We have thousands of PDFs, contracts and a few SQL databases. We want AI agents that can answer questions over all of it, call our ERP and CRM, but with a human approving anything risky before it happens.`
- Expected: entity ['enterprise_ai_os'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_solution`, clarification no, knowledge_available True
- Predicted: entity contact_info , intent INTEGRATIONS, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.4 (margin 0.1675), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Document AI, database agents, ERP/CRM tool integration and human-in-the-loop are Enterprise AI OS capabilities/workflow.

### V5_042 (problem) — first failure: **entity**
- Query: `Our brand positioning feels stale and our CMO is tired of agency workshops and opinion-based decks. She wants a brand strategy grounded in actual market data and demand signals.`
- Expected: entity ['martech_360', 'ai_powered_marketing'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification allowed, knowledge_available True
- Predicted: entity ganesh_gandhi_vadalani , intent LEADERSHIP, aspect LEADERSHIP (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_leadership` {'person_id': 'ganesh_gandhi_vadalani'}
- Confidence: entity 1.0 (margin 1.0), aspect 1.0, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: MarTech 360 explicitly contrasts evidence-driven brand strategy with workshops; AI-Powered Marketing also lists Branding & Strategy.

### V5_044 (non_native) — first failure: **aspect**
- Query: `Please explain what is this brand architecture engine you are providing to companies`
- Expected: entity ['martech_360'], aspect ['OVERVIEW', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_service`, clarification no, knowledge_available True
- Predicted: entity martech_360 , intent HOW_IT_WORKS, aspect WORKFLOW (2nd OVERVIEW, margin 0.8479), scope SINGLE_ENTITY, op `get_workflow` {'entity_id': 'martech_360'}
- Confidence: entity 0.5719 (margin 0.1584), aspect 0.8992, decision 0.5719 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: MarTech 360 tagline: AI Brand Architecture & Strategy Engine.

### V5_048 (spelling) — first failure: **aspect**
- Query: `pharma os cpv tool detials`
- Expected: entity ['pharma_os'], aspect ['CAPABILITIES'], scope SINGLE_ENTITY, op `get_capabilities`, clarification no, knowledge_available True
- Predicted: entity pharma_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'pharma_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.975 (margin 0.975), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: CPV Tool is a Pharma OS capability.

### V5_053 (grammar) — first failure: **aspect**
- Query: `real estate os can manage the brokers commission?`
- Expected: entity ['real_estate_os'], aspect ['CAPABILITIES', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_capabilities`, clarification no, knowledge_available True
- Predicted: entity real_estate_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'real_estate_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.975 (margin 0.975), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Partner Ecosystem / broker commission monitoring is covered.

### V5_060 (informal) — first failure: **aspect**
- Query: `can ur city platform track garbage bin fill levels??`
- Expected: entity ['smart_cities_os'], aspect ['CAPABILITIES', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_capabilities`, clarification no, knowledge_available True
- Predicted: entity smart_cities_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.4997 (margin 0.0997), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Automated waste collection with bin fill tracking is in Smart Cities OS workflow.

### V5_069 (aspect) — first failure: **aspect**
- Query: `What uptime can you guarantee for real-time streaming pipelines in the Data Engineering service?`
- Expected: entity ['data_engineering'], aspect ['BENEFITS', 'FAQ'], scope SINGLE_ENTITY, op `get_benefits`, clarification no, knowledge_available True
- Predicted: entity data_engineering , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'data_engineering', 'section': 'OVERVIEW'}
- Confidence: entity 0.9748 (margin 0.9748), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: 99.99% uptime SLA is a Data Engineering benefit; FAQ on streaming reliability.

### V5_071 (aspect) — first failure: **aspect**
- Query: `What kind of conversion lift can a store expect from E-Commerce OS?`
- Expected: entity ['ecommerce_os'], aspect ['BENEFITS'], scope SINGLE_ENTITY, op `get_benefits`, clarification no, knowledge_available True
- Predicted: entity ecommerce_os , intent UNKNOWN, aspect OVERVIEW (2nd CAPABILITIES, margin -0.8076), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'ecommerce_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.9746 (margin 0.9746), aspect 0.0962, decision 0.0962 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Benefit: 35% higher conversion rate.

### V5_074 (aspect) — first failure: **aspect**
- Query: `Which frameworks do you use when building multi-agent systems for enterprises?`
- Expected: entity ['enterprise_agentic_ai'], aspect ['FAQ', 'WORKFLOW'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity enterprise_agentic_ai , intent INTEGRATIONS, aspect OVERVIEW (2nd WORKFLOW, margin -0.536), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'enterprise_agentic_ai', 'section': 'OVERVIEW'}
- Confidence: entity 0.9741 (margin 0.9741), aspect 0.146, decision 0.146 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
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

### V5_081 (aspect) — first failure: **aspect**
- Query: `Which roles or teams is Pharma OS intended for?`
- Expected: entity ['pharma_os'], aspect ['TARGET_USERS'], scope SINGLE_ENTITY, op `get_target_users`, clarification no, knowledge_available False
- Predicted: entity pharma_os , intent UNKNOWN, aspect OVERVIEW (2nd TARGET_USERS, margin -0.1648), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'pharma_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.9745 (margin 0.9745), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Target users not documented for Pharma OS.

### V5_085 (aspect) — first failure: **aspect**
- Query: `What open rates and click rates do WhatsApp campaigns get on your platform?`
- Expected: entity ['whatsapp_marketing'], aspect ['BENEFITS'], scope SINGLE_ENTITY, op `get_benefits`, clarification no, knowledge_available True
- Predicted: entity whatsapp_marketing , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_product` {'entity_id': 'whatsapp_marketing', 'section': 'OVERVIEW'}
- Confidence: entity 0.9749 (margin 0.9749), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Benefits: 98% open rate, 45-60% click rate.

### V5_094 (context) — first failure: **aspect**
- Query: `does it help with FDA inspections?` (context: {'active_entity': 'pharma_os', 'active_entities': ['pharma_os'], 'previous_turns': ["what's pharma os"]})
- Expected: entity ['pharma_os'], aspect ['CAPABILITIES', 'WORKFLOW', 'BENEFITS'], scope SINGLE_ENTITY, op `get_capabilities`, clarification no, knowledge_available True
- Predicted: entity pharma_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'pharma_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.95 (margin 0.95), aspect 0.4, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Compliance audit trails for FDA/EMA in Pharma OS workflow.

### V5_099 (context) — first failure: **aspect**
- Query: `does it do affiliate tracking too?` (context: {'active_entity': 'influencer_marketing', 'active_entities': ['influencer_marketing'], 'previous_turns': ['what does the influencer marketing platform do']})
- Expected: entity ['influencer_marketing'], aspect ['CAPABILITIES'], scope SINGLE_ENTITY, op `get_capabilities`, clarification no, knowledge_available True
- Predicted: entity influencer_marketing , intent UNKNOWN, aspect OVERVIEW (2nd WORKFLOW, margin -0.6248), scope SINGLE_ENTITY, op `get_product` {'entity_id': 'influencer_marketing', 'section': 'OVERVIEW'}
- Confidence: entity 0.8916 (margin 0.8916), aspect 0.1876, decision 0.1876 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Affiliate Marketing capability of active entity.

### V5_100 (context) — first failure: **aspect**
- Query: `which platforms do you support for that?` (context: {'active_entity': 'ai_powered_marketing', 'active_entities': ['ai_powered_marketing'], 'previous_turns': ["what's in your AI-powered marketing service?"]})
- Expected: entity ['ai_powered_marketing'], aspect ['FAQ', 'CAPABILITIES'], scope SINGLE_ENTITY, op `get_faq`, clarification no, knowledge_available True
- Predicted: entity ai_powered_marketing , intent UNKNOWN, aspect OVERVIEW (2nd CAPABILITIES, margin 0.0306), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'ai_powered_marketing', 'section': 'OVERVIEW'}
- Confidence: entity 0.95 (margin 0.95), aspect 0.5153, decision 0.5153 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity PASS · aspect FAIL · scope PASS · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: FAQ 'What platforms do you support?' of active entity.

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
- Predicted: entity influencer_marketing , intent UNKNOWN, aspect OVERVIEW (2nd CLIENTS_CASE_STUDIES, margin 0.5639), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.3174 (margin 0.0677), aspect 0.7475, decision 0.3174 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Full portfolio request.

### V5_118 (catalog) — first failure: **entity**
- Query: `any consulting services?`
- Expected: entity [], aspect ['CATALOG_LIST'], scope ALL_SERVICES, op `list_services`, clarification no, knowledge_available True
- Predicted: entity real_estate_os , intent UNKNOWN, aspect OVERVIEW (2nd PRICING, margin 0.2234), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.4 (margin 0.0866), aspect 0.6117, decision 0.4 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
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

### V5_128 (company) — first failure: **entity**
- Query: `What is your company's mission and vision?`
- Expected: entity ['company_info'], aspect ['OVERVIEW'], scope SINGLE_ENTITY, op `get_company_info`, clarification no, knowledge_available True
- Predicted: entity martech_360 , intent OVERVIEW, aspect OVERVIEW (2nd TARGET_USERS, margin 0.6568), scope SINGLE_ENTITY, op `get_service` {'entity_id': 'martech_360', 'section': 'OVERVIEW'}
- Confidence: entity 0.4902 (margin 0.4281), aspect 0.8117, decision 0.4902 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope PASS · canonicalization PASS · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Mission/vision in company about.

### V5_132 (ood) — first failure: **entity**
- Query: `my python for loop keeps printing the same number, can you debug it: for i in range(5): print(x)`
- Expected: entity [], aspect None, scope OUT_OF_DOMAIN, op `decline_out_of_domain`, clarification no, knowledge_available False
- Predicted: entity pharma_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope GENERAL, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.1817 (margin 0.1067), aspect 0.4, decision 0.0 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Personal coding help is unrelated to CittaAI offerings.

### V5_136 (ood) — first failure: **entity**
- Query: `how do I apply for a US student visa`
- Expected: entity [], aspect None, scope OUT_OF_DOMAIN, op `decline_out_of_domain`, clarification no, knowledge_available False
- Predicted: entity education_os , intent UNKNOWN, aspect OVERVIEW (2nd None, margin 0.4), scope SINGLE_ENTITY, op `request_clarification` {'reason': 'Ambiguous query requiring user clarification.'}
- Confidence: entity 0.2358 (margin 0.2248), aspect 0.4, decision 0.2358 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: Visa process is unrelated.

### V5_141 (ambiguous) — first failure: **scope**
- Query: `tell me about the OS`
- Expected: entity ['ecommerce_os', 'education_os', 'enterprise_ai_os', 'pharma_os', 'real_estate_os', 'smart_cities_os'], aspect ['OVERVIEW'], scope NONE, op `request_clarification`, clarification required, knowledge_available True
- Predicted: entity education_os , intent OVERVIEW, aspect OVERVIEW (2nd WORKFLOW, margin 0.9441), scope SINGLE_ENTITY, op `get_solution` {'entity_id': 'education_os', 'section': 'OVERVIEW'}
- Confidence: entity 0.8468 (margin 0.7569), aspect 0.9659, decision 0.8468 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization FAIL · operation FAIL · arguments FAIL · evidence —
- Gold rationale: Six offerings are named '... OS'.

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

### V5_145 (ambiguous) — first failure: **scope**
- Query: `how does it work?`
- Expected: entity [], aspect ['WORKFLOW'], scope NONE, op `request_clarification`, clarification required, knowledge_available False
- Predicted: entity martech_360 , intent HOW_IT_WORKS, aspect WORKFLOW (2nd CAPABILITIES, margin 0.9604), scope SINGLE_ENTITY, op `get_workflow` {'entity_id': 'martech_360'}
- Confidence: entity 0.6046 (margin 0.4492), aspect 0.9802, decision 0.6046 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect FAIL · scope FAIL · canonicalization FAIL · operation FAIL · arguments FAIL · evidence —
- Gold rationale: No context and no offering named.

### V5_147 (healthcare) — first failure: **entity**
- Query: `Do you have a hospital management system for OPD, bed allocation and billing?`
- Expected: entity [], aspect None, scope NONE, op `request_clarification`, clarification allowed, knowledge_available False
- Predicted: entity contact_info , intent LOCATION, aspect CONTACT (2nd None, margin 1.0), scope SINGLE_ENTITY, op `get_contact` {}
- Confidence: entity 1.0 (margin 1.0), aspect 1.0, decision 0.9 · LLM {'entity_attempted': False, 'entity_ok': False, 'aspect_attempted': False, 'aspect_ok': False}
- Stages: entity FAIL · aspect PASS · scope FAIL · canonicalization PASS · operation FAIL · arguments PASS · evidence —
- Gold rationale: No offering covers hospital operations; Pharma OS is pharma manufacturing/QA.

