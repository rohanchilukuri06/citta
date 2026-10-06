# Semantic Benchmark — split `dev`, LLM off

Generated 2026-09-30 00:55:40 · 107 queries

## Manifest
```json
{
  "dataset_version": "1.4.0",
  "dataset_sha": "b8396a046f84",
  "registry_hash": null,
  "code_sha": {
    "query_intelligence_engine.py": "24a98f5d508e",
    "semantic_arbitration.py": "e3e58a594afd",
    "semantic_decision.py": "148ff2ab93ff",
    "semantic_entity_index.py": "f9e668d0392c",
    "knowledge_tool_router.py": "cb8ca337e0b0",
    "knowledge_operation_registry.py": "591dd628ccca",
    "semantic_chat_pipeline.py": "4a070aa4aa8c",
    "knowledge_operation_executor.py": "092708908c04"
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
| End-to-end decision accuracy | **91.6%** |
| Entity accuracy | 95.3% |
| Scope accuracy | 96.3% |
| Aspect accuracy | 98.1% |
| Operation accuracy | 91.6% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 3 |
| ECE (5 bins) | 0.0531 |
| Clarification rate | 3.7% |
| LLM adjudication requested / invoked | 0.0% / 0.0% |
| Latency p50 | 231.8 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.4-0.6 | 5 | 0.497 | 0.4 |
| 0.6-0.8 | 15 | 0.706 | 0.933 |
| 0.8-1.0 | 83 | 0.945 | 0.964 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Aspect | 14 | 100.0% | 100.0% |
| Business | 6 | 100.0% | 100.0% |
| Catalog | 7 | 100.0% | 100.0% |
| CategoryMismatch | 2 | 100.0% | 100.0% |
| Company | 7 | 100.0% | 100.0% |
| Context | 7 | 100.0% | 100.0% |
| Conversational | 8 | 100.0% | 100.0% |
| Detail | 6 | 66.7% | 100.0% |
| Direct | 7 | 100.0% | 100.0% |
| Indirect | 11 | 63.6% | 72.7% |
| Informal | 6 | 100.0% | 100.0% |
| Minimal | 6 | 100.0% | 100.0% |
| Multi | 3 | 100.0% | 100.0% |
| OOD | 2 | 100.0% | 100.0% |
| Problem-oriented | 9 | 77.8% | 88.9% |
| Synonym | 6 | 83.3% | 83.3% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| D_DOC_04 | We need something to keep customers updated through messaging. | ['whatsapp_marketing', 'ai_powered_marketing'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES', 'BENEFITS'] | ai_powered_marketing  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.336 |
| PARA_HC_03 | I manage a medical clinic. What AI systems are suitable for us? | - / ['NONE', 'OUT_OF_DOMAIN'] / * | martech_360  / SINGLE_ENTITY / TARGET_USERS → `get_target_users`(martech_360) conf=0.478 |
| PARA_HC_06 | Any AI tech for health care facilities and doctors? | - / ['NONE', 'OUT_OF_DOMAIN'] / * | pharma_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(pharma_os) conf=0.543 |
| PARA_WA_03 | We want to connect our CRM with chat messaging for instant support alerts. | ['whatsapp_marketing', 'ai_powered_marketing'] / ['SINGLE_ENTITY'] / * | ecommerce_os  / SINGLE_ENTITY / CAPABILITIES → `get_capabilities`(ecommerce_os) conf=0.514 |
| PARA_WA_07 | Our open rates on email are horrible and we need direct mobile channel reach. | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['BENEFITS', 'OVERVIEW', 'CAPABILITIES'] | None  / OUT_OF_DOMAIN / OVERVIEW → `decline_out_of_domain`(None) conf=0.7 |
| PARA_AI_03 | We are a Fortune 500 company looking to deploy secure on-prem LLM agents. | ['enterprise_ai_os', 'enterprise_agentic_ai'] / ['SINGLE_ENTITY'] / * | enterprise_agentic_ai  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.448 |
| D_DET_03 | Can the WhatsApp platform send carousel and catalog messages? | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'FAQ'] | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.961 |
| D_DET_06 | Which KPIs does Pharma OS track on its quality dashboards? | ['pharma_os'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'FAQ'] | pharma_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(pharma_os) conf=0.975 |
| D_HOSP_01 | We run three hospitals and want online appointment booking | - / ['NONE', 'OUT_OF_DOMAIN'] / * | martech_360  / SINGLE_ENTITY / OVERVIEW → `get_service`(martech_360) conf=0.803 |
