# Semantic Benchmark — split `test`, LLM off

Generated 2026-09-27 13:19:11 · 108 queries

## Manifest
```json
{
  "dataset_version": "1.2.0",
  "dataset_sha": "4d7a734fe16e",
  "registry_hash": null,
  "code_sha": {
    "query_intelligence_engine.py": "f7532f6a0e79",
    "semantic_arbitration.py": "476fef6cd7a9",
    "semantic_decision.py": "58b73e30369b",
    "semantic_entity_index.py": "7dece7eb5559",
    "knowledge_tool_router.py": "dd656970555c",
    "knowledge_operation_registry.py": "591dd628ccca"
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
| End-to-end decision accuracy | **84.3%** |
| Entity accuracy | 93.5% |
| Scope accuracy | 95.4% |
| Aspect accuracy | 95.4% |
| Operation accuracy | 85.2% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 9 |
| ECE (5 bins) | 0.0847 |
| Clarification rate | 10.2% |
| LLM adjudication requested / invoked | 0.0% / 0.0% |
| Latency p50 | 176.9 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.4-0.6 | 5 | 0.5 | 0.8 |
| 0.6-0.8 | 8 | 0.69 | 1.0 |
| 0.8-1.0 | 84 | 0.943 | 0.893 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Ambiguous | 4 | 100.0% | 100.0% |
| Aspect | 16 | 81.2% | 100.0% |
| Business | 9 | 55.6% | 77.8% |
| Catalog | 7 | 100.0% | 100.0% |
| CategoryMismatch | 1 | 100.0% | 100.0% |
| Company | 8 | 87.5% | 87.5% |
| Context | 5 | 80.0% | 100.0% |
| Conversational | 7 | 71.4% | 100.0% |
| Direct | 4 | 100.0% | 100.0% |
| Elliptical | 2 | 100.0% | 100.0% |
| Indirect | 9 | 100.0% | 100.0% |
| Informal | 7 | 85.7% | 85.7% |
| Minimal | 4 | 100.0% | 100.0% |
| Multi | 4 | 100.0% | 100.0% |
| NonNative | 5 | 80.0% | 100.0% |
| OOD | 5 | 60.0% | 60.0% |
| Problem-oriented | 7 | 85.7% | 85.7% |
| Typos | 4 | 75.0% | 100.0% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| T_PH_04 | How can AI help with GMP compliance and batch release decisions? | ['pharma_os'] / ['SINGLE_ENTITY'] / ['BENEFITS', 'CAPABILITIES', 'OVERVIEW'] | pharma_os  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.49 |
| T_RE_03 | I'm a builder, can your platform help with booking and agreements? | ['real_estate_os'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'BENEFITS', 'OVERVIEW'] | real_estate_os  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.513 |
| T_RE_06 | Who uses the real estate platform? | ['real_estate_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | real_estate_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(real_estate_os) conf=0.963 |
| T_RE_07 | real estat softwere | ['real_estate_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | real_estate_os  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.425 |
| T_SC_04 | Government body looking for citizen data platform | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | None  / UNKNOWN_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.85 |
| T_SC_06 | What problems does Smart Cities OS solve for a city? | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['BENEFITS'] | smart_cities_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(smart_cities_os) conf=0.975 |
| T_EC_02 | Do you have a platform for D2C brands to manage storefront and support? | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.969 |
| T_EC_03 | ecom os features | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['CAPABILITIES'] | None  / UNKNOWN_ENTITY / CAPABILITIES → `request_clarification`(None) conf=0.85 |
| T_EC_06 | which one is good for my kirana shop online selling | ['ecommerce_os'] / ['SINGLE_ENTITY'] / * | ecommerce_os  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.351 |
| T_WA_06 | Any FAQs about the WhatsApp platform? | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['FAQ'] | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.973 |
| T_IN_02 | how do we track affiliate sales from influencers | ['influencer_marketing'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'WORKFLOW'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.898 |
| T_DE_03 | our data is scattered across 12 systems and reports never match | ['data_engineering'] / ['SINGLE_ENTITY'] / * | None  / OUT_OF_DOMAIN / OVERVIEW → `decline_out_of_domain`(None) conf=0.9 |
| T_MK_04 | We need brand positioning based on competitor messaging analysis | ['martech_360', 'ai_powered_marketing'] / ['SINGLE_ENTITY'] / * | ai_powered_marketing  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.415 |
| T_CTX_07 | does it have analytics? | ['influencer_marketing'] / ['SINGLE_ENTITY'] / ['CAPABILITIES'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.95 |
| T_CO_06 | Show me a client success story | - / ['ALL', 'SINGLE_ENTITY', 'CLIENTS_SCOPE'] / ['CLIENTS_CASE_STUDIES'] | b2b_spices_export  / CLIENTS_SCOPE / CLIENTS_CASE_STUDIES → `get_case_study`(b2b_spices_export) conf=0.8 |
| T_OOD_01 | What's the weather in Hyderabad today? | - / ['NONE'] / * | contact_info  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(contact_info) conf=1.0 |
| T_OOD_03 | Who won the IPL last year? | - / ['NONE'] / * | awards_recognition  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(awards_recognition) conf=0.56 |
