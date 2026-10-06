# Semantic Benchmark — split `dev`, LLM off

Generated 2026-09-27 12:18:59 · 72 queries

## Manifest
```json
{
  "dataset_version": "1.0.0",
  "dataset_sha": "cc9e1381b36e",
  "registry_hash": null,
  "code_sha": {
    "query_intelligence_engine.py": "7ecab50f064f",
    "semantic_arbitration.py": "274a275dd943",
    "semantic_decision.py": "cda43360e66b",
    "semantic_entity_index.py": "missing",
    "knowledge_tool_router.py": "052e0e8849b9",
    "knowledge_operation_registry.py": "d2ba15ac40a2"
  },
  "git_head": "71b4793",
  "working_tree_dirty": true,
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "llm_mode": "off",
  "llm_provider": null,
  "llm_model": null
}
```

## Results
| Metric | Value |
|---|---|
| End-to-end decision accuracy | **63.9%** |
| Entity accuracy | 77.8% |
| Scope accuracy | 81.9% |
| Aspect accuracy | 91.7% |
| Operation accuracy | 69.4% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 23 |
| ECE (5 bins) | 0.3071 |
| Clarification rate | 2.8% |
| LLM adjudication requested / invoked | 4.2% / 0.0% |
| Latency p50 | 3579.5 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.6-0.8 | 1 | 0.65 | 0.0 |
| 0.8-1.0 | 69 | 0.969 | 0.667 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Business | 6 | 100.0% | 100.0% |
| Catalog | 3 | 0.0% | 0.0% |
| CategoryMismatch | 2 | 100.0% | 100.0% |
| Company | 6 | 0.0% | 33.3% |
| Context | 4 | 25.0% | 100.0% |
| Conversational | 8 | 87.5% | 87.5% |
| Direct | 7 | 85.7% | 100.0% |
| Indirect | 8 | 87.5% | 87.5% |
| Informal | 6 | 100.0% | 100.0% |
| Minimal | 6 | 100.0% | 100.0% |
| Multi | 1 | 100.0% | 100.0% |
| OOD | 2 | 0.0% | 0.0% |
| Problem-oriented | 7 | 28.6% | 57.1% |
| Synonym | 6 | 33.3% | 66.7% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| D_DOC_04 | We need something to keep customers updated through messaging. | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES', 'BENEFITS'] | martech_360  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(martech_360) conf=0.85 |
| D_DOC_07 | Who is this meant for? | ['education_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=1.0 |
| D_DOC_08 | What can it actually do? | ['education_os'] / ['SINGLE_ENTITY'] / ['CAPABILITIES'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=1.0 |
| D_DOC_09 | Why would a business use it? | ['real_estate_os'] / ['SINGLE_ENTITY'] / ['BENEFITS'] | real_estate_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(real_estate_os) conf=1.0 |
| D_DOC_11 | How do I reach you? | ['contact_info', 'company_info'] / ['SINGLE_ENTITY'] / ['CONTACT'] | influencer_marketing  / SINGLE_ENTITY / CONTACT → `get_product`(influencer_marketing) conf=0.85 |
| D_DOC_12 | What solutions do you offer? | - / ['ALL_SOLUTIONS'] / * | enterprise_agentic_ai  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(enterprise_agentic_ai) conf=0.9 |
| D_DOC_15 | What companies have you worked with? | - / ['ALL', 'SINGLE_ENTITY'] / ['CLIENTS_CASE_STUDIES'] | education_os  / SINGLE_ENTITY / CLIENTS_CASE_STUDIES → `get_solution`(education_os) conf=0.9 |
| D_DOC_16 | How can I work with your team? | ['contact_info', 'company_info'] / ['SINGLE_ENTITY'] / ['CONTACT'] | leadership_info  / SINGLE_ENTITY / LEADERSHIP → `semantic_search`(None) conf=0.95 |
| PARA_ED_06 | How can you help schools and academic centers? | ['education_os'] / ['SINGLE_ENTITY'] / ['BENEFITS', 'CAPABILITIES', 'OVERVIEW'] | education_os ['education_os', 'ai_strategy', 'ai_powered_marketing'] / MULTI_ENTITY / OVERVIEW → `get_solution`(education_os) conf=1.0 |
| PARA_RE_07 | Our real estate team is losing leads because follow-ups take too long. | ['real_estate_os'] / ['SINGLE_ENTITY'] / ['BENEFITS', 'CAPABILITIES', 'OVERVIEW'] | real_estate_os  / SINGLE_ENTITY / LEADERSHIP → `get_solution`(real_estate_os) conf=1.0 |
| PARA_WA_06 | How does text messaging automation integrate with Shopify or Salesforce? | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / * | martech_360  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(martech_360) conf=0.85 |
| PARA_WA_07 | Our open rates on email are horrible and we need direct mobile channel reach. | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['BENEFITS', 'OVERVIEW', 'CAPABILITIES'] | contact_info ['contact_info', 'ai_powered_marketing', 'whatsapp_marketing'] / MULTI_ENTITY / CONTACT → `get_solution`(contact_info) conf=0.95 |
| PARA_SC_03 | Our local government authority needs IoT and central command dashboard software. | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'OVERVIEW'] | pharma_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(pharma_os) conf=0.85 |
| PARA_SC_06 | Do you serve civic bodies and public sector municipal corporations? | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS', 'OVERVIEW'] | smart_cities_os ['smart_cities_os', 'leadership_info', 'ai_powered_marketing'] / MULTI_ENTITY / OVERVIEW → `get_solution`(smart_cities_os) conf=0.85 |
| PARA_SC_07 | We need unified monitoring for emergency response and waste management in our town. | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['BENEFITS', 'CAPABILITIES', 'OVERVIEW'] | education_os ['education_os', 'smart_cities_os', 'ai_strategy'] / MULTI_ENTITY / OVERVIEW → `get_solution`(education_os) conf=0.85 |
| PARA_AI_01 | What is Enterprise AI OS and how does agentic AI middleware function? | ['enterprise_ai_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'WORKFLOW', 'CAPABILITIES'] | enterprise_ai_os  / None / CAPABILITIES → `request_clarification`(None) conf=1.0 |
| PARA_AI_02 | How do your autonomous AI agents coordinate complex multi-step workflows? | ['enterprise_ai_os', 'enterprise_agentic_ai'] / ['SINGLE_ENTITY'] / ['WORKFLOW', 'CAPABILITIES'] | martech_360  / SINGLE_ENTITY / WORKFLOW → `get_workflow`(martech_360) conf=0.85 |
| PARA_AI_06 | Any cognitive operating systems for large business enterprises? | ['enterprise_ai_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | whatsapp_marketing  / None / OVERVIEW → `request_clarification`(None) conf=0.85 |
| PARA_AI_07 | Our existing AI tools lack enterprise data privacy and role-based access controls. | ['enterprise_ai_os', 'enterprise_agentic_ai'] / ['SINGLE_ENTITY'] / * | enterprise_ai_os ['enterprise_ai_os', 'enterprise_agentic_ai'] / MULTI_ENTITY / OVERVIEW → `get_solution`(enterprise_ai_os) conf=0.85 |
| PARA_CAT_01 | What products does CittaAI offer across different industries? | - / ['ALL_PRODUCTS', 'ALL'] / * | company_info  / SINGLE_ENTITY / OVERVIEW → `get_company_info`(None) conf=0.95 |
| PARA_CAT_02 | Give me a summary of all your flagship enterprise OS solutions. | - / ['ALL_SOLUTIONS'] / * | enterprise_ai_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(enterprise_ai_os) conf=1.0 |
| PARA_COMP_01 | Who founded CittaAI and who leads the executive team? | ['leadership_info', 'founder', 'company_info'] / ['SINGLE_ENTITY'] / ['LEADERSHIP'] | leadership_info ['leadership_info', 'founder'] / MULTI_ENTITY / LEADERSHIP → `get_solution`(leadership_info) conf=1.0 |
| PARA_COMP_02 | How do I get in touch with sales or request a product demo? | ['contact_info', 'company_info'] / ['SINGLE_ENTITY'] / ['CONTACT'] | real_estate_os  / SINGLE_ENTITY / CONTACT → `get_solution`(real_estate_os) conf=0.85 |
| PARA_COMP_03 | What awards, press, or industry recognitions has CittaAI received? | ['awards_recognition', 'company_info'] / ['SINGLE_ENTITY'] / ['RECOGNITION'] | company_info  / SINGLE_ENTITY / RECOGNITION → `get_company_info`(None) conf=0.95 |
| PARA_OOD_01 | Can you write a Python script to scrape stock market data from Yahoo Finance? | - / ['NONE'] / * | real_estate_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(real_estate_os) conf=0.85 |
| PARA_OOD_02 | What is the best recipe for baking sourdough bread at home? | - / ['NONE'] / * | data_engineering  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(data_engineering) conf=0.65 |
