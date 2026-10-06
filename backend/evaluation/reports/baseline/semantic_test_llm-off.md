# Semantic Benchmark — split `test`, LLM off

Generated 2026-09-27 12:25:49 · 108 queries

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
| End-to-end decision accuracy | **51.9%** |
| Entity accuracy | 69.4% |
| Scope accuracy | 79.6% |
| Aspect accuracy | 88.0% |
| Operation accuracy | 52.8% |
| Catalog leakage | 0 |
| Confidently wrong (conf ≥ 0.80) | 40 |
| ECE (5 bins) | 0.3833 |
| Clarification rate | 3.7% |
| LLM adjudication requested / invoked | 10.2% / 0.0% |
| Latency p50 | 3494.7 ms |

## Reliability
| Confidence | n | Avg conf | Accuracy |
|---|---|---|---|
| 0.4-0.6 | 2 | 0.55 | 0.0 |
| 0.6-0.8 | 4 | 0.65 | 0.0 |
| 0.8-1.0 | 96 | 0.952 | 0.583 |

## By style
| Style | n | Decision | Entity |
|---|---|---|---|
| Ambiguous | 4 | 50.0% | 50.0% |
| Aspect | 16 | 56.2% | 100.0% |
| Business | 9 | 33.3% | 44.4% |
| Catalog | 7 | 0.0% | 0.0% |
| CategoryMismatch | 1 | 100.0% | 100.0% |
| Company | 8 | 0.0% | 87.5% |
| Context | 5 | 60.0% | 100.0% |
| Conversational | 7 | 85.7% | 100.0% |
| Direct | 4 | 75.0% | 100.0% |
| Elliptical | 2 | 0.0% | 0.0% |
| Indirect | 9 | 88.9% | 88.9% |
| Informal | 7 | 57.1% | 57.1% |
| Minimal | 4 | 75.0% | 75.0% |
| Multi | 4 | 50.0% | 50.0% |
| NonNative | 5 | 100.0% | 100.0% |
| OOD | 5 | 0.0% | 0.0% |
| Problem-oriented | 7 | 71.4% | 71.4% |
| Typos | 4 | 50.0% | 50.0% |

## Failures
| id | query | expected | got |
|---|---|---|---|
| T_ED_05 | we r a engineering colege, want platform for exams | ['education_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | data_engineering  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(data_engineering) conf=0.95 |
| T_ED_07 | Who is Education OS meant for? | ['education_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=1.0 |
| T_ED_08 | How does onboarding of students into cohorts work in your education platform? | ['education_os'] / ['SINGLE_ENTITY'] / ['WORKFLOW'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=1.0 |
| T_ED_10 | Why would a university choose your learning platform over Moodle? | ['education_os'] / ['SINGLE_ENTITY'] / ['BENEFITS'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=1.0 |
| T_PH_02 | We manufacture generic drugs and batch record review takes weeks | ['pharma_os'] / ['SINGLE_ENTITY'] / ['BENEFITS', 'CAPABILITIES', 'OVERVIEW'] | enterprise_ai_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(enterprise_ai_os) conf=0.85 |
| T_PH_03 | tool for APQR reports? | ['pharma_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | education_os  / None / OVERVIEW → `request_clarification`(None) conf=0.85 |
| T_PH_04 | How can AI help with GMP compliance and batch release decisions? | ['pharma_os'] / ['SINGLE_ENTITY'] / ['BENEFITS', 'CAPABILITIES', 'OVERVIEW'] | enterprise_ai_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(enterprise_ai_os) conf=0.85 |
| T_RE_06 | Who uses the real estate platform? | ['real_estate_os'] / ['SINGLE_ENTITY'] / ['TARGET_USERS'] | real_estate_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(real_estate_os) conf=1.0 |
| T_SC_06 | What problems does Smart Cities OS solve for a city? | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['BENEFITS'] | smart_cities_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(smart_cities_os) conf=1.0 |
| T_EC_02 | Do you have a platform for D2C brands to manage storefront and support? | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['OVERVIEW', 'CAPABILITIES'] | faq_general ['faq_general', 'ecommerce_os'] / MULTI_ENTITY / OVERVIEW → `get_solution`(faq_general) conf=0.95 |
| T_EC_03 | ecom os features | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['CAPABILITIES'] | pharma_os  / SINGLE_ENTITY / CAPABILITIES → `get_capabilities`(pharma_os) conf=0.9 |
| T_EC_05 | How does order lifecycle management work in your commerce platform? | ['ecommerce_os'] / ['SINGLE_ENTITY'] / ['WORKFLOW', 'CAPABILITIES'] | ecommerce_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(ecommerce_os) conf=1.0 |
| T_WA_02 | bulk msg to lakhs of customers possible? | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'OVERVIEW'] | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=0.85 |
| T_WA_03 | Is there a shared inbox where my agents can reply to customer chats? | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'OVERVIEW'] | real_estate_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(real_estate_os) conf=0.85 |
| T_WA_04 | How does brand onboarding work for WhatsApp broadcasting? | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['WORKFLOW'] | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=1.0 |
| T_WA_05 | whatsap marketing pricing | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['PRICING'] | faq_general  / None / PRICING → `request_clarification`(None) conf=0.8 |
| T_IN_02 | how do we track affiliate sales from influencers | ['influencer_marketing'] / ['SINGLE_ENTITY'] / ['CAPABILITIES', 'WORKFLOW'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.85 |
| T_IN_03 | Our agency manages 200 creators, need a campaign tool | ['influencer_marketing'] / ['SINGLE_ENTITY'] / * | company_info  / SINGLE_ENTITY / OVERVIEW → `get_company_info`(None) conf=0.95 |
| T_DE_03 | our data is scattered across 12 systems and reports never match | ['data_engineering'] / ['SINGLE_ENTITY'] / * | pharma_os ['pharma_os', 'data_engineering', 'enterprise_ai_os'] / MULTI_ENTITY / OVERVIEW → `get_solution`(pharma_os) conf=0.65 |
| T_ST_02 | Help us prioritize AI use cases for next year | ['ai_strategy'] / ['SINGLE_ENTITY'] / * | enterprise_ai_os  / SINGLE_ENTITY / BENEFITS → `get_benefits`(enterprise_ai_os) conf=0.9 |
| T_ST_04 | board wants an AI roadmap | ['ai_strategy'] / ['SINGLE_ENTITY'] / * | leadership_info  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(leadership_info) conf=1.0 |
| T_MK_02 | We need social media management and content creation | ['ai_powered_marketing'] / ['SINGLE_ENTITY'] / * | fmcg_social_growth  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(fmcg_social_growth) conf=0.85 |
| T_MK_04 | We need brand positioning based on competitor messaging analysis | ['martech_360', 'ai_powered_marketing'] / ['SINGLE_ENTITY'] / * | martech_360  / None / OVERVIEW → `request_clarification`(None) conf=0.85 |
| T_MK_05 | What is MarTech 360? | ['martech_360'] / ['SINGLE_ENTITY'] / ['OVERVIEW'] | martech_360  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(martech_360) conf=1.0 |
| T_AMB_03 | What can it do? | - / ['NONE'] / * | ai_strategy  / SINGLE_ENTITY / CAPABILITIES → `get_capabilities`(ai_strategy) conf=0.55 |
| T_AMB_04 | I need help. | - / ['NONE'] / * | faq_general  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(faq_general) conf=0.9 |
| T_CAT_01 | What do you offer? | - / ['ALL', 'ALL_SOLUTIONS'] / * | ai_strategy  / SINGLE_ENTITY / CAPABILITIES → `get_capabilities`(ai_strategy) conf=0.58 |
| T_CAT_02 | Which products do you sell? | - / ['ALL_PRODUCTS'] / * | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.9 |
| T_CAT_03 | list your services | - / ['ALL_SERVICES'] / * | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.85 |
| T_CAT_04 | what solutions r available | - / ['ALL_SOLUTIONS'] / * | enterprise_agentic_ai  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(enterprise_agentic_ai) conf=0.9 |
| T_CAT_05 | Which industries do you work with? | - / ['ALL', 'ALL_SOLUTIONS'] / * | education_os  / SINGLE_ENTITY / OVERVIEW → `get_solution`(education_os) conf=0.9 |
| T_CAT_06 | How many products do you have? | - / ['ALL_PRODUCTS'] / * | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=0.9 |
| T_CAT_07 | Give me an overview of everything CittaAI builds | - / ['ALL', 'ALL_SOLUTIONS', 'ALL_PRODUCTS'] / * | company_info  / SINGLE_ENTITY / OVERVIEW → `get_company_info`(None) conf=0.95 |
| T_MUL_01 | What's the difference between WhatsApp marketing and influencer marketing platforms? | ['whatsapp_marketing', 'influencer_marketing'] / ['MULTI_ENTITY'] / * | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=1.0 |
| T_MUL_04 | Which is better for a retailer: E-Commerce OS or WhatsApp Marketing? | ['ecommerce_os', 'whatsapp_marketing'] / ['MULTI_ENTITY'] / * | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=1.0 |
| T_CTX_03 | How does that work? | ['whatsapp_marketing'] / ['SINGLE_ENTITY'] / ['WORKFLOW'] | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=1.0 |
| T_CTX_04 | and the benefits? | ['pharma_os'] / ['SINGLE_ENTITY'] / ['BENEFITS'] | awards_recognition  / SINGLE_ENTITY / BENEFITS → `get_benefits`(awards_recognition) conf=0.9 |
| T_CTX_05 | pricing? | ['smart_cities_os'] / ['SINGLE_ENTITY'] / ['PRICING'] | faq_general  / SINGLE_ENTITY / PRICING → `semantic_search`(None) conf=0.9 |
| T_CTX_07 | does it have analytics? | ['influencer_marketing'] / ['SINGLE_ENTITY'] / ['CAPABILITIES'] | influencer_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(influencer_marketing) conf=1.0 |
| T_CO_01 | Who is the CEO of CittaAI? | ['founder', 'leadership_info', 'company_info'] / ['SINGLE_ENTITY'] / ['LEADERSHIP'] | company_info  / None / LEADERSHIP → `request_clarification`(None) conf=0.95 |
| T_CO_02 | Where is your office? | ['contact_info', 'company_info'] / ['SINGLE_ENTITY'] / ['CONTACT'] | contact_info  / SINGLE_ENTITY / CONTACT → `semantic_search`(None) conf=0.95 |
| T_CO_03 | Have you won any awards? | ['awards_recognition', 'company_info'] / ['SINGLE_ENTITY'] / ['RECOGNITION'] | awards_recognition  / SINGLE_ENTITY / RECOGNITION → `semantic_search`(None) conf=1.0 |
| T_CO_04 | Tell me about CittaAI | ['company_info'] / ['SINGLE_ENTITY'] / ['OVERVIEW'] | company_info  / SINGLE_ENTITY / OVERVIEW → `get_company_info`(None) conf=1.0 |
| T_CO_05 | Who is the CTO? | ['akhil_reddy', 'leadership_info', 'company_info'] / ['SINGLE_ENTITY'] / ['LEADERSHIP'] | akhil_reddy  / SINGLE_ENTITY / LEADERSHIP → `semantic_search`(None) conf=1.0 |
| T_CO_06 | Show me a client success story | - / ['ALL', 'SINGLE_ENTITY'] / ['CLIENTS_CASE_STUDIES'] | b2b_spices_export  / SINGLE_ENTITY / CLIENTS_CASE_STUDIES → `list_case_studies`(b2b_spices_export) conf=1.0 |
| T_CO_07 | What is your phone number | ['contact_info', 'company_info'] / ['SINGLE_ENTITY'] / ['CONTACT'] | contact_info  / SINGLE_ENTITY / CONTACT → `semantic_search`(None) conf=0.95 |
| T_CO_08 | who runs this company | ['founder', 'leadership_info', 'company_info'] / ['SINGLE_ENTITY'] / ['LEADERSHIP'] | company_info  / SINGLE_ENTITY / OVERVIEW → `get_company_info`(None) conf=0.9 |
| T_OOD_01 | What's the weather in Hyderabad today? | - / ['NONE'] / * | contact_info  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(contact_info) conf=0.52 |
| T_OOD_02 | Write me a poem about the sea | - / ['NONE'] / * | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.65 |
| T_OOD_03 | Who won the IPL last year? | - / ['NONE'] / * | leadership_info  / SINGLE_ENTITY / RECOGNITION → `semantic_search`(None) conf=0.9 |
| T_OOD_04 | How do I fix my car's brakes? | - / ['NONE'] / * | whatsapp_marketing  / SINGLE_ENTITY / OVERVIEW → `get_product`(whatsapp_marketing) conf=0.65 |
| T_OOD_05 | Explain quantum entanglement to me | - / ['NONE'] / * | data_engineering  / SINGLE_ENTITY / OVERVIEW → `get_capabilities`(data_engineering) conf=0.65 |
