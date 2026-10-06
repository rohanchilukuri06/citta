# Semantic Benchmark — split `test`, LLM on

Generated 2026-09-27 12:44:50 · 108 queries

## Manifest
```json
{
  "dataset_version": "1.1.0",
  "dataset_sha": "7f313b15006c",
  "registry_hash": null,
  "code_sha": {
    "query_intelligence_engine.py": "457d5a85fec7",
    "semantic_arbitration.py": "a11813d35fb8",
    "semantic_decision.py": "161ddbc94884",
    "semantic_entity_index.py": "8ad075551a06",
    "knowledge_tool_router.py": "8c91ff2887a5",
    "knowledge_operation_registry.py": "591dd628ccca"
  },
  "git_head": "71b4793",
  "working_tree_dirty": true,
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "llm_mode": "on",
  "llm_provider": "groq",
  "llm_model": "openai/gpt-oss-20b"
}
```

## Results
| Metric | Value |
|---|---|
| End-to-end decision accuracy | **87.0%** |
| Entity accuracy | 94.4% |
| Scope accuracy | 97.2% |
| Aspect accuracy | 92.6% |
| Operation accuracy | 88.0% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 13 |
| ECE (5 bins) | 0.1213 |
| Clarification rate | 2.8% |
| LLM adjudication requested / invoked | 13.0% / 13.0% |
| Latency p50 | 181.4 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.4-0.6 | 2 | 0.53 | 1.0 |
| 0.6-0.8 | 16 | 0.689 | 0.938 |
| 0.8-1.0 | 87 | 0.94 | 0.851 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Ambiguous | 4 | 100.0% | 100.0% |
| Aspect | 16 | 62.5% | 100.0% |
| Business | 9 | 77.8% | 77.8% |
| Catalog | 7 | 100.0% | 100.0% |
| CategoryMismatch | 1 | 100.0% | 100.0% |
| Company | 8 | 87.5% | 87.5% |
| Context | 5 | 80.0% | 100.0% |
| Conversational | 7 | 85.7% | 100.0% |
| Direct | 4 | 100.0% | 100.0% |
| Elliptical | 2 | 100.0% | 100.0% |
| Indirect | 9 | 88.9% | 88.9% |
| Informal | 7 | 100.0% | 100.0% |
| Minimal | 4 | 100.0% | 100.0% |
| Multi | 4 | 100.0% | 100.0% |
| NonNative | 5 | 100.0% | 100.0% |
| OOD | 5 | 80.0% | 80.0% |
| Problem-oriented | 7 | 85.7% | 85.7% |
| Typos | 4 | 100.0% | 100.0% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| T_ED_07 | Who is Education OS meant for? | ['education_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=0.97 |
| T_ED_08 | How does onboarding of students into cohorts work in your education platform? | ['education_os'] / ['SINGLE_ENTITY'] / ['WORKFLOW'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=0.975 |
| T_PH_07 | Our hospital needs AI for patient appointment booking | ['pharma_os'] / ['SINGLE_ENTITY'] / * | None  / OUT_OF_DOMAIN / OVERVIEW → `decline_out_of_domain`(None) conf=0.8 |
| T_RE_06 | Who uses the real estate platform? | ['real_estate_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | real_estate_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(real_estate_os) conf=0.963 |
| T_SC_06 | What problems does Smart Cities OS solve for a city? | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['BENEFITS'] | smart_cities_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(smart_cities_os) conf=0.975 |
| T_EC_02 | Do you have a platform for D2C brands to manage storefront and support? | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.969 |
| T_EC_05 | How does order lifecycle management work in your commerce platform? | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['WORKFLOW', 'CAPABILITIES'] | ecommerce_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(ecommerce_os) conf=0.971 |
| T_WA_04 | How does brand onboarding work for WhatsApp broadcasting? | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['WORKFLOW'] | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.973 |
| T_IN_02 | how do we track affiliate sales from influencers | ['influencer_marketing'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'WORKFLOW'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.898 |
| T_DE_03 | our data is scattered across 12 systems and reports never match | ['data_engineering'] / ['SINGLE_ENTITY'] / * | None  / OUT_OF_DOMAIN / OVERVIEW → `decline_out_of_domain`(None) conf=0.9 |
| T_MK_02 | We need social media management and content creation | ['ai_powered_marketing'] / ['SINGLE_ENTITY'] / * | influencer_marketing  / SINGLE_ENTITY / CAPABILITIES → `get_capabilities`(influencer_marketing) conf=0.669 |
| T_CTX_07 | does it have analytics? | ['influencer_marketing'] / ['SINGLE_ENTITY'] / ['CAPABILITIES'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.95 |
| T_CO_06 | Show me a client success story | - / ['ALL', 'SINGLE_ENTITY'] / ['CLIENTS_CASE_STUDIES'] | b2b_spices_export  / ALL / CLIENTS_CASE_STUDIES → `get_case_study`(b2b_spices_export) conf=0.8 |
| T_OOD_01 | What's the weather in Hyderabad today? | - / ['NONE'] / * | contact_info  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(contact_info) conf=1.0 |
