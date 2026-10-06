# CittaAI Paraphrase Generalization Benchmark Report

**Generated At:** 2026-09-18 01:39:32  
**Evaluation Set:** `paraphrase_questions.json` (55 Multi-Style Paraphrase Queries)

---

## 1. Summary Performance Metrics

| Metric | Target | Benchmark Result | Status |
| :--- | :---: | :---: | :---: |
| **Entity Resolution Accuracy** | ≥ 90.0% | **76.4%** | FAIL |
| **Intent Classification Accuracy** | ≥ 85.0% | **34.5%** | FAIL |
| **Semantic Aspect Accuracy** | ≥ 85.0% | **70.9%** | FAIL |
| **Answer Scope Accuracy** | ≥ 85.0% | **80.0%** | FAIL |
| **Catalog List Leakage Count** | **0** | **0** | PASS |
| **Level 3 LLM Fallback Rate** | < 15.0% | **0.0%** | PASS |

---

## 2. Accuracy Breakdown by Paraphrase Formulation Style

| Formulation Style | Queries | Entity Accuracy | Leakage Count |
| :--- | :---: | :---: | :---: |
| **Direct** | 11 | **54.5%** | **0** |
| **Conversational** | 6 | **83.3%** | **0** |
| **Indirect** | 6 | **83.3%** | **0** |
| **Business** | 6 | **100.0%** | **0** |
| **Informal** | 6 | **100.0%** | **0** |
| **Synonym** | 6 | **66.7%** | **0** |
| **Problem-oriented** | 6 | **66.7%** | **0** |
| **Minimal** | 6 | **100.0%** | **0** |
| **OOD** | 2 | **0.0%** | **0** |

---

## 3. Failure & Leakage Trace Details

```json
[
  {
    "id": "PARA_ED_03",
    "query": "I run a university. How could CittaAI help us?",
    "style": "Indirect",
    "expected_entity": "education_os",
    "got_entity": "education_os",
    "rules_entity": "education_os",
    "bge_entity": "founder",
    "disagreement": true,
    "selected_op": "get_benefits",
    "is_leakage": false,
    "interpretation": "Intent: UNKNOWN, Aspect: BENEFITS, Scope: SINGLE_ENTITY, Entity: education_os (Rules: education_os, BGE: founder)"
  },
  {
    "id": "PARA_ED_07",
    "query": "We need to improve how our institution operates with AI.",
    "style": "Problem-oriented",
    "expected_entity": "education_os",
    "got_entity": "education_os",
    "rules_entity": "education_os",
    "bge_entity": "enterprise_agentic_ai",
    "disagreement": true,
    "selected_op": "get_benefits",
    "is_leakage": false,
    "interpretation": "Intent: RECOMMENDATION, Aspect: BENEFITS, Scope: SINGLE_ENTITY, Entity: education_os (Rules: education_os, BGE: enterprise_agentic_ai)"
  },
  {
    "id": "PARA_HC_02",
    "query": "How do you help regional hospital networks manage patients?",
    "style": "Conversational",
    "expected_entity": "pharma_os",
    "got_entity": "pharma_os",
    "rules_entity": "pharma_os",
    "bge_entity": "smart_cities_os",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: UNKNOWN, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: pharma_os (Rules: pharma_os, BGE: smart_cities_os)"
  },
  {
    "id": "PARA_HC_04",
    "query": "We operate a pharmaceutical distribution chain. What platform do you have?",
    "style": "Business",
    "expected_entity": "pharma_os",
    "got_entity": "pharma_os",
    "rules_entity": "pharma_os",
    "bge_entity": "whatsapp_marketing",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: UNKNOWN, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: pharma_os (Rules: pharma_os, BGE: whatsapp_marketing)"
  },
  {
    "id": "PARA_RE_04",
    "query": "We are residential builders looking for digital inventory and lead booking tools.",
    "style": "Business",
    "expected_entity": "real_estate_os",
    "got_entity": "real_estate_os",
    "rules_entity": "real_estate_os",
    "bge_entity": "data_engineering",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: RECOMMENDATION, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: real_estate_os (Rules: real_estate_os, BGE: data_engineering)"
  },
  {
    "id": "PARA_WA_03",
    "query": "We want to connect our CRM with chat messaging for instant support alerts.",
    "style": "Indirect",
    "expected_entity": "whatsapp_marketing",
    "got_entity": "whatsapp_marketing",
    "rules_entity": "whatsapp_marketing",
    "bge_entity": "jewellery_brand_roi",
    "disagreement": true,
    "selected_op": "get_product",
    "is_leakage": false,
    "interpretation": "Intent: INTEGRATIONS, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: whatsapp_marketing (Rules: whatsapp_marketing, BGE: jewellery_brand_roi)"
  },
  {
    "id": "PARA_WA_06",
    "query": "How does text messaging automation integrate with Shopify or Salesforce?",
    "style": "Synonym",
    "expected_entity": "whatsapp_marketing",
    "got_entity": "martech_360",
    "rules_entity": "martech_360",
    "bge_entity": "jewellery_brand_roi",
    "disagreement": true,
    "selected_op": "get_capabilities",
    "is_leakage": false,
    "interpretation": "Intent: INTEGRATIONS, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: martech_360 (Rules: martech_360, BGE: jewellery_brand_roi)"
  },
  {
    "id": "PARA_WA_07",
    "query": "Our open rates on email are horrible and we need direct mobile channel reach.",
    "style": "Problem-oriented",
    "expected_entity": "whatsapp_marketing",
    "got_entity": "contact_info",
    "rules_entity": "contact_info",
    "bge_entity": "contact_info",
    "disagreement": false,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: RECOMMENDATION, Aspect: CONTACT, Scope: MULTI_ENTITY, Entity: contact_info (Rules: contact_info, BGE: contact_info)"
  },
  {
    "id": "PARA_SC_03",
    "query": "Our local government authority needs IoT and central command dashboard software.",
    "style": "Indirect",
    "expected_entity": "smart_cities_os",
    "got_entity": "pharma_os",
    "rules_entity": "pharma_os",
    "bge_entity": "smart_cities_os",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: RECOMMENDATION, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: pharma_os (Rules: pharma_os, BGE: smart_cities_os)"
  },
  {
    "id": "PARA_SC_06",
    "query": "Do you serve civic bodies and public sector municipal corporations?",
    "style": "Synonym",
    "expected_entity": "smart_cities_os",
    "got_entity": "smart_cities_os",
    "rules_entity": "smart_cities_os",
    "bge_entity": "leadership_info",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: UNKNOWN, Aspect: OVERVIEW, Scope: MULTI_ENTITY, Entity: smart_cities_os (Rules: smart_cities_os, BGE: leadership_info)"
  },
  {
    "id": "PARA_SC_07",
    "query": "We need unified monitoring for emergency response and waste management in our town.",
    "style": "Problem-oriented",
    "expected_entity": "smart_cities_os",
    "got_entity": "education_os",
    "rules_entity": "education_os",
    "bge_entity": "smart_cities_os",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: RECOMMENDATION, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: education_os (Rules: education_os, BGE: smart_cities_os)"
  },
  {
    "id": "PARA_AI_02",
    "query": "How do your autonomous AI agents coordinate complex multi-step workflows?",
    "style": "Conversational",
    "expected_entity": "enterprise_ai_os",
    "got_entity": "martech_360",
    "rules_entity": "martech_360",
    "bge_entity": "enterprise_ai_os",
    "disagreement": true,
    "selected_op": "get_workflow",
    "is_leakage": false,
    "interpretation": "Intent: UNKNOWN, Aspect: WORKFLOW, Scope: SINGLE_ENTITY, Entity: martech_360 (Rules: martech_360, BGE: enterprise_ai_os)"
  },
  {
    "id": "PARA_AI_03",
    "query": "We are a Fortune 500 company looking to deploy secure on-prem LLM agents.",
    "style": "Indirect",
    "expected_entity": "enterprise_ai_os",
    "got_entity": "enterprise_ai_os",
    "rules_entity": "enterprise_ai_os",
    "bge_entity": "enterprise_agentic_ai",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: RECOMMENDATION, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: enterprise_ai_os (Rules: enterprise_ai_os, BGE: enterprise_agentic_ai)"
  },
  {
    "id": "PARA_AI_06",
    "query": "Any cognitive operating systems for large business enterprises?",
    "style": "Synonym",
    "expected_entity": "enterprise_ai_os",
    "got_entity": "whatsapp_marketing",
    "rules_entity": "whatsapp_marketing",
    "bge_entity": "enterprise_ai_os",
    "disagreement": true,
    "selected_op": "request_clarification",
    "is_leakage": false,
    "interpretation": "Intent: INTEGRATIONS, Aspect: OVERVIEW, Scope: GENERAL, Entity: whatsapp_marketing (Rules: whatsapp_marketing, BGE: enterprise_ai_os)"
  },
  {
    "id": "PARA_CAT_01",
    "query": "What products does CittaAI offer across different industries?",
    "style": "Direct",
    "expected_entity": null,
    "got_entity": "company_info",
    "rules_entity": "company_info",
    "bge_entity": "founder",
    "disagreement": true,
    "selected_op": "get_company_info",
    "is_leakage": false,
    "interpretation": "Intent: PRODUCTS, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: company_info (Rules: company_info, BGE: founder)"
  },
  {
    "id": "PARA_CAT_02",
    "query": "Give me a summary of all your flagship enterprise OS solutions.",
    "style": "Direct",
    "expected_entity": null,
    "got_entity": "enterprise_ai_os",
    "rules_entity": "enterprise_ai_os",
    "bge_entity": "enterprise_ai_os",
    "disagreement": false,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: INTEGRATIONS, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: enterprise_ai_os (Rules: enterprise_ai_os, BGE: enterprise_ai_os)"
  },
  {
    "id": "PARA_COMP_01",
    "query": "Who founded CittaAI and who leads the executive team?",
    "style": "Direct",
    "expected_entity": "company_info",
    "got_entity": "leadership_info",
    "rules_entity": "leadership_info",
    "bge_entity": "founder",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: LEADERSHIP, Aspect: LEADERSHIP, Scope: MULTI_ENTITY, Entity: leadership_info (Rules: leadership_info, BGE: founder)"
  },
  {
    "id": "PARA_COMP_02",
    "query": "How do I get in touch with sales or request a product demo?",
    "style": "Direct",
    "expected_entity": "contact_info",
    "got_entity": "real_estate_os",
    "rules_entity": "real_estate_os",
    "bge_entity": "ai_powered_marketing",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: CONTACT, Aspect: CONTACT, Scope: SINGLE_ENTITY, Entity: real_estate_os (Rules: real_estate_os, BGE: ai_powered_marketing)"
  },
  {
    "id": "PARA_COMP_03",
    "query": "What awards, press, or industry recognitions has CittaAI received?",
    "style": "Direct",
    "expected_entity": "awards_recognition",
    "got_entity": "company_info",
    "rules_entity": "company_info",
    "bge_entity": "founder",
    "disagreement": true,
    "selected_op": "get_company_info",
    "is_leakage": false,
    "interpretation": "Intent: UNKNOWN, Aspect: RECOGNITION, Scope: SINGLE_ENTITY, Entity: company_info (Rules: company_info, BGE: founder)"
  },
  {
    "id": "PARA_OOD_01",
    "query": "Can you write a Python script to scrape stock market data from Yahoo Finance?",
    "style": "OOD",
    "expected_entity": null,
    "got_entity": "real_estate_os",
    "rules_entity": "real_estate_os",
    "bge_entity": "ai_powered_marketing",
    "disagreement": true,
    "selected_op": "get_solution",
    "is_leakage": false,
    "interpretation": "Intent: UNKNOWN, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: real_estate_os (Rules: real_estate_os, BGE: ai_powered_marketing)"
  },
  {
    "id": "PARA_OOD_02",
    "query": "What is the best recipe for baking sourdough bread at home?",
    "style": "OOD",
    "expected_entity": null,
    "got_entity": "data_engineering",
    "rules_entity": null,
    "bge_entity": "data_engineering",
    "disagreement": true,
    "selected_op": "get_capabilities",
    "is_leakage": false,
    "interpretation": "Intent: OVERVIEW, Aspect: OVERVIEW, Scope: SINGLE_ENTITY, Entity: data_engineering (Rules: None, BGE: data_engineering)"
  }
]
```

---
