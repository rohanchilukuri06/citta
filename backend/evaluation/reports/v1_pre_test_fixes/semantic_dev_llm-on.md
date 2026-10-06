# Semantic Benchmark — split `dev`, LLM on

Generated 2026-09-27 12:43:00 · 72 queries

## Manifest
```json
{
  "dataset_version": "1.0.0",
  "dataset_sha": "cc9e1381b36e",
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
| End-to-end decision accuracy | **91.7%** |
| Entity accuracy | 91.7% |
| Scope accuracy | 94.4% |
| Aspect accuracy | 100.0% |
| Operation accuracy | 91.7% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 4 |
| ECE (5 bins) | 0.0411 |
| Clarification rate | 1.4% |
| LLM adjudication requested / invoked | 19.4% / 19.4% |
| Latency p50 | 146.3 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.4-0.6 | 3 | 0.536 | 0.667 |
| 0.6-0.8 | 9 | 0.68 | 0.889 |
| 0.8-1.0 | 59 | 0.921 | 0.932 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Business | 6 | 100.0% | 100.0% |
| Catalog | 3 | 100.0% | 100.0% |
| CategoryMismatch | 2 | 100.0% | 100.0% |
| Company | 6 | 100.0% | 100.0% |
| Context | 4 | 100.0% | 100.0% |
| Conversational | 8 | 87.5% | 87.5% |
| Direct | 7 | 100.0% | 100.0% |
| Indirect | 8 | 87.5% | 87.5% |
| Informal | 6 | 83.3% | 83.3% |
| Minimal | 6 | 83.3% | 83.3% |
| Multi | 1 | 100.0% | 100.0% |
| OOD | 2 | 100.0% | 100.0% |
| Problem-oriented | 7 | 85.7% | 85.7% |
| Synonym | 6 | 83.3% | 83.3% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| PARA_ED_07 | We need to improve how our institution operates with AI. | ['education_os'] / ['SINGLE_ENTITY'] / ['BENEFITS', 'OVERVIEW', 'CAPABILITIES'] | ai_strategy  / SINGLE_ENTITY / CAPABILITIES → `get_capabilities`(ai_strategy) conf=0.606 |
| PARA_HC_02 | How do you help regional hospital networks manage patients? | ['pharma_os'] / ['SINGLE_ENTITY'] / * | None  / OUT_OF_DOMAIN / OVERVIEW → `decline_out_of_domain`(None) conf=0.8 |
| PARA_HC_05 | what do u have for hospitals | ['pharma_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | None  / OUT_OF_DOMAIN / OVERVIEW → `decline_out_of_domain`(None) conf=0.8 |
| PARA_HC_06 | Any AI tech for health care facilities and doctors? | ['pharma_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | None  / OUT_OF_DOMAIN / OVERVIEW → `decline_out_of_domain`(None) conf=0.8 |
| PARA_HC_08 | Anything for clinics? | ['pharma_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | None  / OUT_OF_DOMAIN / OVERVIEW → `decline_out_of_domain`(None) conf=0.8 |
| PARA_WA_03 | We want to connect our CRM with chat messaging for instant support alerts. | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / * | enterprise_ai_os  / SINGLE_ENTITY / CAPABILITIES → `get_capabilities`(enterprise_ai_os) conf=0.465 |
