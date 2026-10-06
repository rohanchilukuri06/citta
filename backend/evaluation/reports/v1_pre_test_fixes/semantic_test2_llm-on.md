# Semantic Benchmark — split `test2`, LLM on

Generated 2026-09-27 12:46:19 · 56 queries

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
| End-to-end decision accuracy | **75.0%** |
| Entity accuracy | 91.1% |
| Scope accuracy | 94.6% |
| Aspect accuracy | 82.1% |
| Operation accuracy | 76.8% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 11 |
| ECE (5 bins) | 0.1596 |
| Clarification rate | 1.8% |
| LLM adjudication requested / invoked | 3.6% / 3.6% |
| Latency p50 | 146.1 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.6-0.8 | 8 | 0.666 | 0.75 |
| 0.8-1.0 | 46 | 0.934 | 0.761 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Ambiguous | 3 | 33.3% | 66.7% |
| Aspect | 10 | 30.0% | 100.0% |
| Business | 4 | 100.0% | 100.0% |
| Catalog | 3 | 66.7% | 66.7% |
| CategoryMismatch | 2 | 100.0% | 100.0% |
| Company | 6 | 83.3% | 83.3% |
| Context | 5 | 60.0% | 80.0% |
| Conversational | 3 | 66.7% | 66.7% |
| Direct | 2 | 100.0% | 100.0% |
| Elliptical | 1 | 100.0% | 100.0% |
| Indirect | 5 | 100.0% | 100.0% |
| Minimal | 2 | 100.0% | 100.0% |
| Multi | 3 | 100.0% | 100.0% |
| NonNative | 1 | 100.0% | 100.0% |
| OOD | 5 | 100.0% | 100.0% |
| Typos | 1 | 100.0% | 100.0% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| T2_ED_02 | What kind of institutions is Education OS built for? | ['education_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=0.973 |
| T2_ED_03 | Explain the steps to get a college started on your learning platform | ['education_os'] / ['SINGLE_ENTITY'] / ['WORKFLOW'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=0.939 |
| T2_RE_03 | How do listings flow into leads and site visits in Real Estate OS? | ['real_estate_os'] / ['SINGLE_ENTITY'] / ['WORKFLOW', 'CAPABILITIES'] | real_estate_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(real_estate_os) conf=0.974 |
| T2_SC_02 | Why should a municipality invest in Smart Cities OS? | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['BENEFITS'] | smart_cities_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(smart_cities_os) conf=0.975 |
| T2_EC_02 | What does E-Commerce OS include for order management? | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'WORKFLOW'] | ecommerce_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(ecommerce_os) conf=0.975 |
| T2_AI_02 | How does Enterprise AI OS take a model from evaluation to deployment? | ['enterprise_ai_os'] / ['SINGLE_ENTITY'] / ['WORKFLOW'] | enterprise_ai_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(enterprise_ai_os) conf=0.925 |
| T2_IN_02 | How does a brand run a campaign end to end on the influencer platform? | ['influencer_marketing'] / ['SINGLE_ENTITY'] / ['WORKFLOW'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.929 |
| T2_MK_01 | Can you manage our Instagram and Facebook ad campaigns? | ['ai_powered_marketing', 'influencer_marketing'] / ['SINGLE_ENTITY'] / * | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.63 |
| T2_CAT_03 | list of your platforms | - / ['ALL', 'ALL_PRODUCTS', 'ALL_SOLUTIONS'] / * | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.873 |
| T2_CTX_01 | Who is the target audience? | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | whatsapp_marketing  / SINGLE_ENTITY / TARGET_USERS → `get_target_users`(whatsapp_marketing) conf=0.815 |
| T2_CTX_06 | why is it better than doing it manually? | ['pharma_os'] / ['SINGLE_ENTITY'] / ['BENEFITS'] | pharma_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(pharma_os) conf=0.95 |
| T2_CO_04 | Which brands have you helped so far? | - / ['ALL', 'SINGLE_ENTITY'] / ['CLIENTS_CASE_STUDIES'] | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.616 |
| T2_AMB_01 | Tell me more | - / ['NONE'] / * | contact_info  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(contact_info) conf=0.672 |
| T2_AMB_02 | Do you have an OS for my industry? | - / ['NONE', 'ALL', 'ALL_SOLUTIONS'] / * | None  / ALL_SOLUTIONS / OVERVIEW → `list_solutions`(None) conf=0.95 |
