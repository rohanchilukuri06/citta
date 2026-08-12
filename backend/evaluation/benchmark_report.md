# CittaAI V3.4 Demo-Freeze Accuracy Report

Generated on 2026-08-02 23:54:11

## Summary Statistics

- **Total Scenarios Evaluated**: 162
- **Query Type Accuracy**: 93.8% (152/162)
- **Domain Detection Accuracy**: 96.9% (157/162)
- **Entity Mapping Accuracy**: 97.5% (158/162)
- **Overall Core Score**: **96.1%**

## Detail Log Matrix

| # | Question | Expected Type | Actual Type | Expected Domain | Actual Domain | Expected Entity | Resolved Entity | Latency | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | What products does CittaAI offer? | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 30.98ms | PASS |
| 2 | Show me your product list | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 3.74ms | PASS |
| 3 | What products do you have? | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 5.98ms | PASS |
| 4 | List products | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 5.39ms | PASS |
| 5 | What are your products? | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 5.81ms | PASS |
| 6 | Products offered by CittaAI | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 7.81ms | PASS |
| 7 | CittaAI flagship products | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 4.25ms | PASS |
| 8 | Show CittaAI products | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 3.59ms | PASS |
| 9 | What platforms does CittaAI offer? | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 4.68ms | PASS |
| 10 | Tell me about your product catalog | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 5.19ms | PASS |
| 11 | List of CittaAI products | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 4.34ms | PASS |
| 12 | Flagship products list | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 3.88ms | PASS |
| 13 | Give me a list of your products | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 6.64ms | PASS |
| 14 | Tell me about products | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 5.59ms | PASS |
| 15 | What are the products of CittaAI? | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 5.14ms | PASS |
| 16 | What services do you provide? | LIST | LIST | SERVICES | SERVICES | None | None | 5.37ms | PASS |
| 17 | Show me your services | LIST | LIST | SERVICES | SERVICES | None | None | 6.14ms | PASS |
| 18 | List services | LIST | LIST | SERVICES | SERVICES | None | None | 6.98ms | PASS |
| 19 | What services do you offer? | LIST | LIST | SERVICES | SERVICES | None | None | 4.95ms | PASS |
| 20 | What are your professional services? | LIST | LIST | SERVICES | SERVICES | None | None | 5.46ms | PASS |
| 21 | CittaAI services catalog | LIST | LIST | SERVICES | SERVICES | None | None | 4.39ms | PASS |
| 22 | Services offered by CittaAI | LIST | LIST | SERVICES | SERVICES | None | None | 6.21ms | PASS |
| 23 | Show CittaAI services | LIST | LIST | SERVICES | SERVICES | None | None | 4.98ms | PASS |
| 24 | What advisory capabilities do you have? | LIST | CONSULTATION | SERVICES | COMPANY_INFO | None | None | 3.51ms | FAIL |
| 25 | Tell me about your consulting services | LIST | LIST | SERVICES | SERVICES | None | None | 6.93ms | PASS |
| 26 | List of CittaAI services | LIST | LIST | SERVICES | SERVICES | None | None | 4.41ms | PASS |
| 27 | Professional services list | LIST | LIST | SERVICES | SERVICES | None | None | 3.59ms | PASS |
| 28 | Give me a list of your services | LIST | LIST | SERVICES | SERVICES | None | None | 5.25ms | PASS |
| 29 | Tell me about services | LIST | LIST | SERVICES | SERVICES | None | None | 5.54ms | PASS |
| 30 | What are the services of CittaAI? | LIST | LIST | SERVICES | SERVICES | None | None | 4.68ms | PASS |
| 31 | What solutions do you offer? | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 5.44ms | PASS |
| 32 | Show me your solutions | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 6.08ms | PASS |
| 33 | List solutions | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 5.44ms | PASS |
| 34 | What solutions do you provide? | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 6.14ms | PASS |
| 35 | What are your industry solutions? | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 7.83ms | PASS |
| 36 | CittaAI industry OS platforms | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 9.38ms | PASS |
| 37 | Solutions offered by CittaAI | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 6.69ms | PASS |
| 38 | Show CittaAI solutions | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 6.42ms | PASS |
| 39 | What operating systems do you have? | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 8.44ms | PASS |
| 40 | Tell me about your industry OS solutions | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 9.50ms | PASS |
| 41 | List of CittaAI solutions | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 8.15ms | PASS |
| 42 | Operating systems list | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 6.50ms | PASS |
| 43 | Give me a list of your solutions | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 9.45ms | PASS |
| 44 | Tell me about solutions | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 7.48ms | PASS |
| 45 | What are the solutions of CittaAI? | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 6.93ms | PASS |
| 46 | Who founded CittaAI? | FACT | FACT | LEADERSHIP | LEADERSHIP | founder | founder | 4.78ms | PASS |
| 47 | Who is the CEO of CittaAI? | FACT | FACT | LEADERSHIP | LEADERSHIP | founder | None | 5.14ms | FAIL |
| 48 | Who started CittaAI? | FACT | FACT | LEADERSHIP | LEADERSHIP | founder | founder | 6.85ms | PASS |
| 49 | Who is the CEO? | FACT | FACT | LEADERSHIP | LEADERSHIP | founder | None | 9.14ms | FAIL |
| 50 | Tell me about the founder of CittaAI | FACT | FACT | LEADERSHIP | LEADERSHIP | founder | None | 9.29ms | FAIL |
| 51 | Kiran Kumar title | FACT | FACT | LEADERSHIP | LEADERSHIP | founder | founder | 5.24ms | PASS |
| 52 | Who is Kiran Kumar? | FACT | FACT | LEADERSHIP | LEADERSHIP | founder | founder | 4.43ms | PASS |
| 53 | Who leads CittaAI? | FACT | FACT | LEADERSHIP | LEADERSHIP | founder | founder | 5.22ms | PASS |
| 54 | Who is Vinay Velivela? | FACT | FACT | LEADERSHIP | LEADERSHIP | None | None | 6.40ms | PASS |
| 55 | Tell me about Akhil Reddy | FACT | FACT | LEADERSHIP | LEADERSHIP | None | None | 4.73ms | PASS |
| 56 | Who is on the leadership team? | FACT | FACT | LEADERSHIP | LEADERSHIP | None | None | 5.32ms | PASS |
| 57 | Tell me about your COO | FACT | FACT | LEADERSHIP | LEADERSHIP | None | None | 3.75ms | PASS |
| 58 | When was CittaAI founded? | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 3.34ms | PASS |
| 59 | Tell me about CittaAI history | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 4.16ms | PASS |
| 60 | What is CittaAI mission? | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 4.85ms | PASS |
| 61 | What is CittaAI vision? | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 4.02ms | PASS |
| 62 | What is CittaAI tagline? | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 3.89ms | PASS |
| 63 | About CittaAI | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 6.68ms | PASS |
| 64 | CittaAI company info | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 5.98ms | PASS |
| 65 | Overview of CittaAI | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 4.43ms | PASS |
| 66 | Story of CittaAI | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 4.02ms | PASS |
| 67 | Fixity Technologies relation | FACT | FACT | COMPANY_INFO | COMPANY_INFO | None | None | 3.08ms | PASS |
| 68 | What is CittaAI's email address and phone number? | FACT | FACT | CONTACT | CONTACT | None | None | 3.13ms | PASS |
| 69 | How do I contact CittaAI? | FACT | FACT | CONTACT | CONTACT | None | None | 2.62ms | PASS |
| 70 | What is CittaAI phone number? | FACT | FACT | CONTACT | CONTACT | None | None | 2.01ms | PASS |
| 71 | What is CittaAI email? | FACT | FACT | CONTACT | CONTACT | None | None | 2.11ms | PASS |
| 72 | Support email address | FACT | FACT | CONTACT | CONTACT | None | None | 3.49ms | PASS |
| 73 | CittaAI support phone | FACT | FACT | CONTACT | CONTACT | None | None | 2.59ms | PASS |
| 74 | What time does CittaAI open? | FACT | FACT | CONTACT | CONTACT | None | None | 2.21ms | PASS |
| 75 | Show contact details | FACT | FACT | CONTACT | CONTACT | None | None | 2.05ms | PASS |
| 76 | Are you open on weekends? | FACT | FACT | CONTACT | CONTACT | None | None | 1.87ms | PASS |
| 77 | What are your business hours? | FACT | FACT | CONTACT | CONTACT | None | None | 2.55ms | PASS |
| 78 | Where is the head office located? | FACT | FACT | LOCATION | LOCATION | None | None | 2.09ms | PASS |
| 79 | What is CittaAI address? | FACT | FACT | LOCATION | LOCATION | None | None | 3.28ms | PASS |
| 80 | Office location of CittaAI | FACT | FACT | LOCATION | LOCATION | None | None | 2.66ms | PASS |
| 81 | Where is CittaAI headquarters? | FACT | FACT | LOCATION | LOCATION | None | None | 2.02ms | PASS |
| 82 | Where is CittaAI tower? | FACT | FACT | LOCATION | LOCATION | None | None | 1.68ms | PASS |
| 83 | Head office address | FACT | FACT | LOCATION | LOCATION | None | None | 1.70ms | PASS |
| 84 | Hyderabad office location | FACT | FACT | LOCATION | LOCATION | None | None | 2.26ms | PASS |
| 85 | Where are you located? | FACT | FACT | LOCATION | LOCATION | None | None | 2.19ms | PASS |
| 86 | Where is CittaAI based? | FACT | FACT | LOCATION | LOCATION | None | None | 1.87ms | PASS |
| 87 | Office map of CittaAI | FACT | FACT | LOCATION | LOCATION | None | None | 2.56ms | PASS |
| 88 | Tell me about CittaAI achievements. | FACT | FACT | RECOGNITION | RECOGNITION | None | None | 2.24ms | PASS |
| 89 | What awards has CittaAI won? | FACT | FACT | RECOGNITION | RECOGNITION | None | None | 2.02ms | PASS |
| 90 | Tell me about AP MSME Challenge 2025. | FACT | FACT | RECOGNITION | RECOGNITION | None | None | 1.91ms | PASS |
| 91 | What is the Best AI Startup Award? | FACT | FACT | RECOGNITION | RECOGNITION | None | None | 1.65ms | PASS |
| 92 | CittaAI double victory awards | FACT | FACT | RECOGNITION | RECOGNITION | None | None | 1.59ms | PASS |
| 93 | HYBIZ TV Business Excellence awards | FACT | FACT | RECOGNITION | RECOGNITION | None | None | 1.59ms | PASS |
| 94 | APIS MSME Challenge winner | FACT | FACT | RECOGNITION | RECOGNITION | None | None | 1.70ms | PASS |
| 95 | List achievements of CittaAI | LIST | LIST | RECOGNITION | RECOGNITION | None | None | 1.89ms | PASS |
| 96 | List awards of CittaAI | LIST | LIST | RECOGNITION | RECOGNITION | None | None | 4.18ms | PASS |
| 97 | Tell me about recognitions | FACT | FACT | RECOGNITION | RECOGNITION | None | None | 2.75ms | PASS |
| 98 | Who are CittaAI's clients? | FACT | FACT | PARTNERS | PARTNERS | None | None | 2.57ms | PASS |
| 99 | Who are your enterprise partners? | FACT | FACT | PARTNERS | PARTNERS | None | None | 3.29ms | PASS |
| 100 | Which companies has CittaAI worked with? | FACT | FACT | PARTNERS | PARTNERS | None | None | 2.46ms | PASS |
| 101 | How many enterprise partners does CittaAI have? | FACT | FACT | PARTNERS | PARTNERS | None | None | 3.57ms | PASS |
| 102 | What is CittaAI's retention rate? | FACT | FACT | PARTNERS | PARTNERS | None | None | 3.88ms | PASS |
| 103 | List of CittaAI customers | LIST | LIST | PARTNERS | PARTNERS | None | None | 2.33ms | PASS |
| 104 | Who are your clients? | FACT | FACT | PARTNERS | PARTNERS | None | None | 2.32ms | PASS |
| 105 | Show CittaAI partners | LIST | LIST | PARTNERS | PARTNERS | None | None | 2.15ms | PASS |
| 106 | Brands CittaAI works with | FACT | FACT | PARTNERS | PARTNERS | None | None | 2.30ms | PASS |
| 107 | Tell me about partners | FACT | FACT | PARTNERS | PARTNERS | None | None | 3.43ms | PASS |
| 108 | Explain the features of the WhatsApp Marketing Platform. | DETAIL | DETAIL | PRODUCTS | PRODUCTS | whatsapp_marketing | whatsapp_marketing | 2.64ms | PASS |
| 109 | What are the capabilities of WhatsApp Marketing Platform? | DETAIL | DETAIL | PRODUCTS | PRODUCTS | whatsapp_marketing | whatsapp_marketing | 2.67ms | PASS |
| 110 | Tell me about WhatsApp Marketing | DETAIL | DETAIL | PRODUCTS | PRODUCTS | whatsapp_marketing | whatsapp_marketing | 1.99ms | PASS |
| 111 | How does the WhatsApp Marketing Platform help? | DETAIL | DETAIL | PRODUCTS | PRODUCTS | whatsapp_marketing | whatsapp_marketing | 3.83ms | PASS |
| 112 | What does WhatsApp Marketing Platform do? | DETAIL | DETAIL | PRODUCTS | PRODUCTS | whatsapp_marketing | whatsapp_marketing | 3.47ms | PASS |
| 113 | Explain the features of the Influencer Marketing Platform. | DETAIL | DETAIL | PRODUCTS | PRODUCTS | influencer_marketing | influencer_marketing | 3.38ms | PASS |
| 114 | What are the capabilities of Influencer Marketing Platform? | DETAIL | DETAIL | PRODUCTS | PRODUCTS | influencer_marketing | influencer_marketing | 3.04ms | PASS |
| 115 | Tell me about Influencer Marketing | DETAIL | DETAIL | PRODUCTS | PRODUCTS | influencer_marketing | influencer_marketing | 2.34ms | PASS |
| 116 | How does the Influencer Marketing Platform help? | DETAIL | DETAIL | PRODUCTS | PRODUCTS | influencer_marketing | influencer_marketing | 3.47ms | PASS |
| 117 | What does Influencer Marketing Platform do? | DETAIL | DETAIL | PRODUCTS | PRODUCTS | influencer_marketing | influencer_marketing | 2.68ms | PASS |
| 118 | What does Data Engineering include? | DETAIL | DETAIL | SERVICES | SERVICES | data_engineering | data_engineering | 3.14ms | PASS |
| 119 | What are the capabilities of Data Engineering? | DETAIL | DETAIL | SERVICES | SERVICES | data_engineering | data_engineering | 3.36ms | PASS |
| 120 | Explain Enterprise & Agentic AI | DETAIL | DETAIL | SERVICES | SERVICES | enterprise_agentic_ai | enterprise_agentic_ai | 2.44ms | PASS |
| 121 | What capabilities does Enterprise & Agentic AI have? | DETAIL | DETAIL | SERVICES | SERVICES | enterprise_agentic_ai | enterprise_agentic_ai | 2.34ms | PASS |
| 122 | What does AI Strategy & Advisory include? | DETAIL | CONSULTATION | SERVICES | SERVICES | ai_strategy | ai_strategy | 2.84ms | FAIL |
| 123 | Explain AI Strategy capabilities | DETAIL | DETAIL | SERVICES | SERVICES | ai_strategy | ai_strategy | 2.75ms | PASS |
| 124 | What is AI-Powered Marketing? | DETAIL | DETAIL | SERVICES | SERVICES | ai_powered_marketing | ai_powered_marketing | 3.68ms | PASS |
| 125 | What does AI-Powered Marketing include? | DETAIL | DETAIL | SERVICES | SERVICES | ai_powered_marketing | ai_powered_marketing | 5.13ms | PASS |
| 126 | Explain Data Engineering capabilities | DETAIL | DETAIL | SERVICES | SERVICES | data_engineering | data_engineering | 3.74ms | PASS |
| 127 | Tell me about AI-Powered Marketing service | DETAIL | DETAIL | SERVICES | SERVICES | ai_powered_marketing | ai_powered_marketing | 2.19ms | PASS |
| 128 | Explain Enterprise AI OS | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | enterprise_ai_os | enterprise_ai_os | 3.22ms | PASS |
| 129 | What does E-Commerce OS do? | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | ecommerce_os | ecommerce_os | 4.58ms | PASS |
| 130 | Tell me about Pharma OS | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | pharma_os | pharma_os | 4.98ms | PASS |
| 131 | Explain the features of Smart Cities OS | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | smart_cities_os | smart_cities_os | 4.32ms | PASS |
| 132 | What is Education OS? | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | education_os | education_os | 7.31ms | PASS |
| 133 | What does Real Estate OS provide? | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | real_estate_os | real_estate_os | 5.64ms | PASS |
| 134 | Capabilities of Enterprise AI OS | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | enterprise_ai_os | enterprise_ai_os | 4.34ms | PASS |
| 135 | Explain Pharma & Healthcare OS benefits | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | pharma_os | pharma_os | 3.77ms | PASS |
| 136 | What is E-Commerce OS? | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | ecommerce_os | ecommerce_os | 2.79ms | PASS |
| 137 | Tell me about Real Estate OS | DETAIL | DETAIL | SOLUTIONS | SOLUTIONS | real_estate_os | real_estate_os | 3.00ms | PASS |
| 138 | What is the weather today? | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | None | None | 2.75ms | PASS |
| 139 | Who won the IPL? | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | None | None | 3.05ms | PASS |
| 140 | Write Python code. | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | None | None | 4.74ms | PASS |
| 141 | Explain quantum mechanics. | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | None | None | 2.81ms | PASS |
| 142 | What is the capital of France? | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | None | None | 2.94ms | PASS |
| 143 | How do you build a chicken coop? | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | None | None | 2.11ms | PASS |
| 144 | Does CittaAI have ISO 27001 certification? | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | None | None | 2.10ms | PASS |
| 145 | What certifications does CittaAI hold? | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | None | None | 2.88ms | PASS |
| 146 | Tell me about CittaAI's green energy initiatives | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | None | None | 3.79ms | PASS |
| 147 | Are there ISO audits done at CittaAI? | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | None | None | 4.50ms | PASS |
| 148 | Does CittaAI support blockchain systems? | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | None | None | 3.74ms | PASS |
| 149 | Has CittaAI won any oscars? | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | UNKNOWN_IN_DOMAIN | None | None | 2.58ms | PASS |
| 150 | List products | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 2.80ms | PASS |
| 151 | List services | LIST | LIST | SERVICES | SERVICES | None | None | 4.60ms | PASS |
| 152 | Show offerings | LIST | OUT_OF_DOMAIN | PRODUCTS | OUT_OF_DOMAIN | None | None | 3.20ms | FAIL |
| 153 | Count case studies | COUNT | DETAIL | CASE_STUDIES | CASE_STUDIES | None | case_studies | 3.71ms | FAIL |
| 154 | How many services? | COUNT | LIST | SERVICES | SERVICES | None | None | 2.61ms | FAIL |
| 155 | Show all products | LIST | LIST | PRODUCTS | PRODUCTS | None | None | 3.36ms | PASS |
| 156 | List solutions | LIST | LIST | SOLUTIONS | SOLUTIONS | None | None | 4.17ms | PASS |
| 157 | Count blogs | COUNT | OUT_OF_DOMAIN | OUT_OF_DOMAIN | OUT_OF_DOMAIN | None | None | 3.20ms | FAIL |
| 158 | Recommend the best product | RECOMMEND | LIST | PRODUCTS | PRODUCTS | None | None | 6.88ms | FAIL |
| 159 | Compare AI Studio vs Chatbot | COMPARE | UNKNOWN_IN_DOMAIN | PRODUCTS | UNKNOWN_IN_DOMAIN | None | None | 4.18ms | FAIL |
| 160 | What solution fits healthcare? | RECOMMEND | LIST | SOLUTIONS | SOLUTIONS | None | None | 3.47ms | FAIL |
| 161 | Summarize your manufacturing offerings | SUMMARIZE | SUMMARIZE | PRODUCTS | UNKNOWN_IN_DOMAIN | None | None | 2.62ms | FAIL |
| 162 | Why should I choose CittaAI? | ASK | FOLLOW_UP | COMPANY_INFO | UNKNOWN_IN_DOMAIN | None | None | 1.33ms | FAIL |