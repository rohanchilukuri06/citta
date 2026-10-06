# Semantic Benchmark — split `test2`, LLM on

Generated 2026-09-27 13:21:17 · 56 queries

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
  "llm_mode": "on",
  "llm_provider": "groq",
  "llm_model": "openai/gpt-oss-20b"
}
```

## Results
| Metric | Value |
|---|---|
| End-to-end decision accuracy | **82.1%** |
| Entity accuracy | 89.3% |
| Scope accuracy | 94.6% |
| Aspect accuracy | 89.3% |
| Operation accuracy | 82.1% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 6 |
| ECE (5 bins) | 0.0561 |
| Clarification rate | 1.8% |
| LLM adjudication requested / invoked | 3.6% / 3.6% |
| Latency p50 | 160.3 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.6-0.8 | 9 | 0.663 | 0.667 |
| 0.8-1.0 | 45 | 0.933 | 0.867 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Ambiguous | 3 | 66.7% | 66.7% |
| Aspect | 10 | 70.0% | 100.0% |
| Business | 4 | 100.0% | 100.0% |
| Catalog | 3 | 66.7% | 66.7% |
| CategoryMismatch | 2 | 50.0% | 100.0% |
| Company | 6 | 83.3% | 83.3% |
| Context | 5 | 80.0% | 80.0% |
| Conversational | 3 | 66.7% | 66.7% |
| Direct | 2 | 100.0% | 100.0% |
| Elliptical | 1 | 100.0% | 100.0% |
| Indirect | 5 | 100.0% | 100.0% |
| Minimal | 2 | 100.0% | 100.0% |
| Multi | 3 | 66.7% | 66.7% |
| NonNative | 1 | 100.0% | 100.0% |
| OOD | 5 | 100.0% | 100.0% |
| Typos | 1 | 100.0% | 100.0% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| T2_ED_02 | What kind of institutions is Education OS built for? | ['education_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=0.973 |
| T2_ED_03 | Explain the steps to get a college started on your learning platform | ['education_os'] / ['SINGLE_ENTITY'] / ['WORKFLOW'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=0.939 |
| T2_SC_02 | Why should a municipality invest in Smart Cities OS? | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['BENEFITS'] | smart_cities_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(smart_cities_os) conf=0.975 |
| T2_MK_01 | Can you manage our Instagram and Facebook ad campaigns? | ['ai_powered_marketing', 'influencer_marketing'] / ['SINGLE_ENTITY'] / * | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.63 |
| T2_CAT_03 | list of your platforms | - / ['ALL', 'ALL_PRODUCTS', 'ALL_SOLUTIONS'] / * | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.873 |
| T2_CAT_05 | Which service handles influencer campaigns? | ['influencer_marketing'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | influencer_marketing  / SINGLE_ENTITY / WORKFLOW → `get_workflow`(influencer_marketing) conf=0.966 |
| T2_MUL_03 | How is the influencer platform different from the WhatsApp one? | ['influencer_marketing', 'whatsapp_marketing'] / ['MULTI_ENTITY'] / * | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.638 |
| T2_CTX_01 | Who is the target audience? | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | whatsapp_marketing  / SINGLE_ENTITY / TARGET_USERS → `get_target_users`(whatsapp_marketing) conf=0.815 |
| T2_CO_04 | Which brands have you helped so far? | - / ['ALL', 'SINGLE_ENTITY', 'CLIENTS_SCOPE'] / ['CLIENTS_CASE_STUDIES'] | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.616 |
| T2_AMB_01 | Tell me more | - / ['NONE'] / * | contact_info  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(contact_info) conf=0.672 |
