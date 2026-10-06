# Semantic Benchmark — split `dev`, LLM on

Generated 2026-10-02 20:25:08 · 107 queries

## Manifest
```json
{
  "dataset_version": "1.4.0",
  "dataset_sha": "fd780e2fb34d",
  "registry_hash": null,
  "code_sha": {
    "query_intelligence_engine.py": "8e3f64496d8f",
    "semantic_arbitration.py": "e3e58a594afd",
    "semantic_decision.py": "148ff2ab93ff",
    "semantic_entity_index.py": "6c827df84ed8",
    "knowledge_tool_router.py": "cb8ca337e0b0",
    "knowledge_operation_registry.py": "591dd628ccca",
    "semantic_chat_pipeline.py": "8c1487bf9e2a",
    "knowledge_operation_executor.py": "3254da482692"
  },
  "git_head": "71b4793",
  "working_tree_dirty": true,
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "llm_mode": "on",
  "llm_provider": "nvidia",
  "llm_model": "nvidia/nemotron-3-super-120b-a12b"
}
```

## Results
| Metric | Value |
|---|---|
| End-to-end decision accuracy | **94.4%** |
| Entity accuracy | 95.3% |
| Scope accuracy | 95.3% |
| Aspect accuracy | 99.1% |
| Operation accuracy | 94.4% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 1 |
| ECE (5 bins) | 0.0729 |
| Clarification rate | 0.9% |
| LLM adjudication requested / invoked | 21.5% / 21.5% |
| Latency p50 | 214.9 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.4-0.6 | 8 | 0.545 | 0.5 |
| 0.6-0.8 | 17 | 0.7 | 0.941 |
| 0.8-1.0 | 81 | 0.947 | 0.988 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Aspect | 14 | 100.0% | 100.0% |
| Business | 6 | 83.3% | 100.0% |
| Catalog | 7 | 100.0% | 100.0% |
| CategoryMismatch | 2 | 100.0% | 100.0% |
| Company | 7 | 100.0% | 100.0% |
| Context | 7 | 100.0% | 100.0% |
| Conversational | 8 | 100.0% | 100.0% |
| Detail | 6 | 100.0% | 100.0% |
| Direct | 7 | 100.0% | 100.0% |
| Indirect | 11 | 81.8% | 81.8% |
| Informal | 6 | 83.3% | 83.3% |
| Minimal | 6 | 100.0% | 100.0% |
| Multi | 3 | 100.0% | 100.0% |
| OOD | 2 | 100.0% | 100.0% |
| Problem-oriented | 9 | 88.9% | 88.9% |
| Synonym | 6 | 83.3% | 83.3% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| PARA_HC_03 | I manage a medical clinic. What AI systems are suitable for us? | - / ['NONE', 'OUT_OF_DOMAIN'] / * | pharma_os  / SINGLE_ENTITY / TARGET_USERS → `get_target_users`(pharma_os) conf=0.543 |
| PARA_HC_05 | what do u have for hospitals | - / ['NONE', 'OUT_OF_DOMAIN'] / * | pharma_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(pharma_os) conf=0.46 |
| PARA_HC_06 | Any AI tech for health care facilities and doctors? | - / ['NONE', 'OUT_OF_DOMAIN'] / * | pharma_os  / SINGLE_ENTITY / TARGET_USERS → `get_target_users`(pharma_os) conf=0.664 |
| PARA_HC_07 | We are struggling with patient scheduling and clinical workflow automation. | - / ['NONE', 'OUT_OF_DOMAIN'] / * | ai_powered_marketing  / SINGLE_ENTITY / TARGET_USERS → `get_target_users`(ai_powered_marketing) conf=0.585 |
| PARA_RE_04 | We are residential builders looking for digital inventory and lead booking tools. | ['real_estate_os'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'OVERVIEW'] | real_estate_os  / SINGLE_ENTITY / TARGET_USERS → `get_target_users`(real_estate_os) conf=0.914 |
| D_HOSP_01 | We run three hospitals and want online appointment booking | - / ['NONE', 'OUT_OF_DOMAIN'] / * | ai_powered_marketing  / SINGLE_ENTITY / CAPABILITIES → `get_capabilities`(ai_powered_marketing) conf=0.559 |
