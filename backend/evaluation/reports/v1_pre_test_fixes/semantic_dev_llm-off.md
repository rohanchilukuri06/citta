# Semantic Benchmark — split `dev`, LLM off

Generated 2026-09-27 12:42:12 · 72 queries

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
  "llm_mode": "off",
  "llm_provider": null,
  "llm_model": null
}
```

## Results
| Metric | Value |
|---|---|
| End-to-end decision accuracy | **93.1%** |
| Entity accuracy | 95.8% |
| Scope accuracy | 98.6% |
| Aspect accuracy | 100.0% |
| Operation accuracy | 94.4% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 0 |
| ECE (5 bins) | 0.1176 |
| Clarification rate | 8.3% |
| LLM adjudication requested / invoked | 0.0% / 0.0% |
| Latency p50 | 140.6 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.4-0.6 | 8 | 0.508 | 0.875 |
| 0.6-0.8 | 4 | 0.703 | 1.0 |
| 0.8-1.0 | 54 | 0.933 | 1.0 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Business | 6 | 100.0% | 100.0% |
| Catalog | 3 | 100.0% | 100.0% |
| CategoryMismatch | 2 | 100.0% | 100.0% |
| Company | 6 | 100.0% | 100.0% |
| Context | 4 | 100.0% | 100.0% |
| Conversational | 8 | 100.0% | 100.0% |
| Direct | 7 | 100.0% | 100.0% |
| Indirect | 8 | 75.0% | 87.5% |
| Informal | 6 | 100.0% | 100.0% |
| Minimal | 6 | 100.0% | 100.0% |
| Multi | 1 | 100.0% | 100.0% |
| OOD | 2 | 50.0% | 50.0% |
| Problem-oriented | 7 | 85.7% | 85.7% |
| Synonym | 6 | 83.3% | 100.0% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| D_DOC_04 | We need something to keep customers updated through messaging. | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES', 'BENEFITS'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.459 |
| PARA_WA_03 | We want to connect our CRM with chat messaging for instant support alerts. | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / * | ecommerce_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(ecommerce_os) conf=0.577 |
| PARA_WA_06 | How does text messaging automation integrate with Shopify or Salesforce? | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / * | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.325 |
| PARA_AI_03 | We are a Fortune 500 company looking to deploy secure on-prem LLM agents. | ['enterprise_ai_os', 'enterprise_agentic_ai'] / ['SINGLE_ENTITY'] / * | enterprise_agentic_ai  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.261 |
| PARA_OOD_01 | Can you write a Python script to scrape stock market data from Yahoo Finance? | - / ['NONE'] / * | pharma_os  / SINGLE_ENTITY / OVERVIEW → `request_clarification`(None) conf=0.101 |
