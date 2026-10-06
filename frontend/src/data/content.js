// CittaAI content — locked from Section 2 of the master brief.
// Only content living here is authoritative. Do not edit UI text elsewhere.

export const BRAND = {
  name: "CittaAI",
  wordmark: "Citta",
  wordmarkAccent: "AI",
  tagline: "Elevate. Innovate. Captivate.",
  drivenBy: "Driven by Fixity",
  positioning: "Enterprise-Grade AI Intelligence & Transformation Partner",
  logoSquare: "/assets/brand/logo-square.png",
  logoWide: "/assets/brand/logo-wide.png",
  founded: 2022,
};

export const CONTACT = {
  phone: "+91 9392655040",
  phoneRaw: "+919392655040",
  hours: "Mon–Fri 9am–6pm",
  email: "info@cittaai.com",
  address: "5th Floor, SVS One Building, Patrika Nagar Rd Number 2, HUDA Techno Enclave, HITEC City, Hyderabad, Telangana 500081",
  response: "We typically respond within 24 hours during business hours.",
};

export const NAV = {
  brand: "CittaAI",
  primary: [
    {
      label: "Products",
      children: [
        { label: "WhatsApp Marketing", to: "/products/whatsapp-marketing", note: "Brand Messaging OS", accent: "jade" },
        { label: "Influencer Marketing", to: "/products/influencer-marketing", note: "Creator Collaboration OS", accent: "coral" },
      ],
    },
    {
      label: "Solutions",
      children: [
        { label: "E-Commerce OS", to: "/solutions/ecommerce-os", note: "Storefront to supply chain", accent: "saffron" },
        { label: "Real Estate OS", to: "/solutions/real-estate-os", note: "Listings to post-sale", accent: "terracotta" },
        { label: "Pharma OS", to: "/solutions/pharma-os", note: "Quality & compliance", accent: "sky" },
        { label: "Smart Cities OS", to: "/solutions/smart-cities-os", note: "Urban intelligence", accent: "leaf" },
        { label: "Education OS", to: "/solutions/education-os", note: "Learning + assessment + coding", accent: "gold" },
        { label: "Enterprise AI OS", to: "/solutions/enterprise-ai-os", note: "PoC to production", accent: "cobalt" },
      ],
    },
    {
      label: "Services",
      children: [
        { label: "Data Engineering", to: "/services/data-engineering", note: "AI-ready data platforms", accent: "sky" },
        { label: "Enterprise & Agentic AI", to: "/services/enterprise-ai", note: "Agents, RAG, LLMs", accent: "cobalt" },
        { label: "AI Strategy & Advisory", to: "/services/ai-strategy", note: "Readiness to governance", accent: "saffron" },
        { label: "MarTech 360", to: "/services/martech-360", note: "AI-powered marketing", accent: "coral" },
      ],
    },
    { label: "Recognition", to: "/recognition" },
    { label: "Case Studies", to: "/case-studies" },
    { label: "About", to: "/about" },
  ],
  cta: { label: "Say Hello!", to: "/contact" },
  language: "English",
};

export const HOMEPAGE = {
  hero: {
    eyebrow: "Living Intelligence",
    titleLead: "Engineering",
    titleAccent: "Enterprise-Grade AI Intelligence.",
    subtitle:
      "Specializing in agentic AI systems and intelligent platforms engineered for real-world enterprise scale.",
    ctas: [
      { label: "Start Strategy Call", to: "/contact", primary: true },
      { label: "Explore AI Platforms", to: "/#products" },
    ],
    tags: ["Production-Ready", "Enterprise Scale", "Measurable ROI"],
  },
  challenges: {
    eyebrow: "The AI Challenge",
    title: "Why Enterprise AI Fails to Scale",
    items: [
      { title: "Fragmented Data", desc: "Siloed data lakes and warehouses create blind spots. Your data potential is locked behind incompatible formats and legacy systems." },
      { title: "Isolated AI Pilots", desc: "80% of enterprise AI projects fail to scale beyond the proof-of-concept stage due to infrastructure gaps." },
      { title: "Siloed Systems", desc: "Legacy ERPs and CRMs remain disconnected siloes, blocking intelligent workflows and decision making." },
      { title: "Manual Overhead", desc: "High-value talent is wasted on repetitive data entry instead of focusing on strategic growth and innovation." },
    ],
    contrast: {
      left: "Manual, Mechanical, Outdated",
      right: "AI Without Guardrails",
    },
  },
  positioning: {
    eyebrow: "Who We Are",
    title: "Not an Agency.  Not a Tool Vendor.",
    lead: "CittaAI is a long-term AI transformation partner that engineers production-ready, agentic-first AI systems delivering measurable business outcomes.",
    pillars: [
      { n: "01", title: "Multidisciplinary Teams", desc: "AI engineers, data scientists, and strategists working as one unified unit. We don't just hand off code; we embed with your teams to ensure cultural adoption and technical transfer." },
      { n: "02", title: "Proven Track Record", desc: "Successful deployments across Enterprise, Pharma, FMCG, and GovTech. Our solutions are battle-tested in regulated industries where security and compliance are paramount." },
      { n: "03", title: "Platform Builders", desc: "Creators of AI platforms and operating systems, not just implementations. We build the scaffolding that allows your AI initiatives to scale indefinitely." },
    ],
  },
  stack: {
    eyebrow: "AGENTIC_AI_STACK",
    title: "Inside CittaAI's Agentic AI Stack",
    outcome: "From manual workflows to autonomous execution.",
    // The four layers as published on cittaai.com
    steps: [
      { n: "01", title: "RAG-Based Intelligence", desc: "AI trained on documents, SOPs, policies, databases. Secure, permission-based, factual responses. Enterprise-grade knowledge systems." },
      { n: "02", title: "AI Chat Agents", desc: "Customer support, internal helpdesks, sales, workflows. Always available, always learning conversational AI." },
      { n: "03", title: "Voice AI Agents", desc: "Inbound & outbound calls, reminders, onboarding. Natural voice interactions that feel human." },
      { n: "04", title: "Video AI Agents", desc: "Training, onboarding, education, sales enablement. Interactive video experiences powered by AI." },
    ],
  },
  products: {
    eyebrow: "Product Ecosystem",
    title: "Built for Impact",
    lead: "Specialized AI platforms engineered to solve complex vertical challenges.",
    items: [
      { n: "01", title: "WhatsApp Marketing", desc: "Enterprise-grade WhatsApp broadcasting, CRM automation, and customer engagement funnels.", to: "/products/whatsapp-marketing" },
      { n: "02", title: "Influencer Marketing", desc: "SaaS-based creator campaigns discovery, UGC content orchestration, and performance metrics.", to: "/products/influencer-marketing" },
    ],
  },
  services: {
    eyebrow: "Our Services",
    title: "What We Build",
    lead: "End-to-end AI transformation capabilities.",
    items: [
      { title: "Data Engineering", sub: "Building AI-Ready Data Platforms", desc: "Modern data architectures, real-time pipelines, analytics foundations, and AI-ready ecosystems.", to: "/services/data-engineering" },
      { title: "Enterprise & Agentic AI", sub: "Intelligent & Agentic Systems Built for the Enterprise", desc: "Enterprise AI applications, autonomous agents, copilots, ERP/LMS/Pharma/GovTech systems.", to: "/services/enterprise-ai" },
      { title: "AI Strategy & Advisory", sub: "Designing Enterprise AI with Clarity, Governance, and Impact", desc: "AI readiness, roadmap, governance, responsible AI, and CoE setup.", to: "/services/ai-strategy" },
      { title: "360° AI-Powered Digital Marketing", sub: "Marketing Intelligence, Automated by AI", desc: "AI-driven acquisition, engagement, conversion, and revenue optimization.", to: "/services/martech-360" },
    ],
    cta: { label: "View All Services", to: "/services" },
  },
  solutions: {
    eyebrow: "Sector Intelligence",
    title: "Industry Operating Systems",
    lead: "Purpose-built cognitive architectures specifically engineered for vertical outcomes.",
    items: [
      { name: "E-Commerce OS", to: "/solutions/ecommerce-os", tag: "AI-Native platform for modern commerce" },
      { name: "Pharma & Healthcare OS", to: "/solutions/pharma-os", tag: "Compliance-first pharma operations" },
      { name: "Smart Cities OS", to: "/solutions/smart-cities-os", tag: "Cognitive infrastructure for urban systems" },
    ],
  },
  results: {
    eyebrow: "Proven Results",
    title: "Real ROI with AI Systems",
    lead: "We engineer measurable outcomes. Here is the impact of deploying autonomous cognitive architectures in the real world.",
    cases: [
      { brand: "Jewellery Brand", metric: "₹3.5 Cr+", label: "ROI from a single campaign", desc: "AI-powered WhatsApp funnel driving exceptional returns through intelligent customer engagement." },
      { brand: "FMCG Brand", metric: "2K → 37K", label: "Followers Growth", desc: "1000+ UGC assets" },
      { brand: "B2B Spices Export", metric: "50+ tons", label: "Export inquiries in 1 month", desc: "70% lower CPL" },
    ],
  },
  fueling: {
    eyebrow: "Data-Driven Trust",
    title: "Fueling Growth\nFor Market Leaders.",
    desc: "Join the ecosystem of forward-thinking enterprises leveraging our autonomous architectures to dominate their verticals.",
    stats: [
      { v: "15+", l: "Enterprise Partners" },
      { v: "100%", l: "Retention Rate" },
    ],
    logos: ["Aurum Street", "Devarasa", "Green Leaves", "Nails by Mahas", "Olive Mithai", "Premedis", "SRK Jawa", "SVS", "Shilpa Botanica", "Shaaranga", "Vegasri", "Axygen", "Fixity"],
  },
  why: {
    eyebrow: "The Difference",
    title: "Why CittaAI",
    sub: "Engineering AI Intelligence for the Modern Enterprise",
    items: [
      { n: 1, title: "Agentic-First Product Philosophy", desc: "Every system designed for autonomy. Cognitive architectures that reason, plan, and execute workflows with minimal oversight." },
      { n: 2, title: "Proven Track Record", desc: "Battle-tested across Enterprise, Pharma, FMCG and GovTech. We understand regulated industries and their compliance requirements." },
      { n: 3, title: "Built for Scale, Security, and Measurable ROI", desc: "Every engagement is tied to business outcomes. We optimize for revenue impact and operational efficiency, not just novelty." },
    ],
  },
  closing: {
    title: "Initialize Partnership",
    desc: "Access Intelligence. Deploy production-grade autonomous architectures with a team that treats AI as an engineering discipline, not a demo.",
    ctas: [
      { label: "Say Hello!", to: "/contact", primary: true },
      { label: "See Case Studies", to: "/case-studies" },
    ],
  },
};

// ==============================================================
// PRODUCT & SOLUTION PAGE CONFIGS — one template, driven by data
// ==============================================================

// Accent names map to theme tokens in index.css (light + dark values): cobalt, jade, saffron, coral, sky,
// terracotta, leaf, gold. Set with data-accent="…" on a page wrapper.
export const ACCENTS = ["cobalt", "jade", "saffron", "coral", "sky", "terracotta", "leaf", "gold"];

// ---------- PRODUCTS ----------
export const WHATSAPP = {
  slug: "whatsapp-marketing",
  kind: "product",
  eyebrow: "Brand Messaging OS",
  name: "WhatsApp Marketing Platform",
  hero: "Direct-to-customer messaging, orchestrated at scale.",
  subtitle: "Reach millions of customers on WhatsApp with segmented broadcasts, two-way support, and compliant lifecycle journeys — all inside one platform.",
  accent: "jade",
  scene: "broadcast",
  stats: [
    { v: "98%",   l: "Open Rate" },
    { v: "45–60%", l: "Click Rate" },
    { v: "Lakhs", l: "Daily Messages" },
    { v: "24/7",  l: "Engagement" },
  ],
  capabilities: [
    { t: "Brand Onboarding",           d: "White-label WhatsApp Business API onboarding, verified sender IDs, template approvals handled end to end." },
    { t: "Message Types",              d: "Text, media, catalogs, buttons, list messages, carousel — pick the format that fits the moment." },
    { t: "Mass Scale Broadcasting",    d: "Lakhs of messages per day with adaptive rate control and delivery guarantees." },
    { t: "Segmentation & Targeting",   d: "Live segments powered by CRM data, behaviour, purchase history and lifecycle stage." },
    { t: "Automation & Journeys",      d: "Drag-and-drop lifecycle workflows: onboarding, cart recovery, re-engagement, feedback loops." },
    { t: "Two-Way Inbox",              d: "Unified shared inbox with agent routing, canned replies, tagging, and SLA tracking." },
    { t: "Templates Management",       d: "Central library of approved templates with versioning, previews and locale variants." },
    { t: "Analytics & Reporting",      d: "Delivery, opens, clicks, revenue attribution and cohort funnels in one dashboard." },
    { t: "Integrations",               d: "Native connectors for Shopify, CRMs, ad platforms, warehouses and internal APIs." },
    { t: "Compliance & Safety",        d: "Opt-in management, DND enforcement, PII handling and audit trails baked in." },
    { t: "Managed Services",           d: "Optional dedicated pod for creative, targeting and reporting — you own the outcomes." },
  ],
  bestFor: ["D2C & Retail", "Education", "Healthcare", "Local Services", "Real Estate Lead Funnels"],
  outcomes: ["Higher conversions", "Faster support", "Scalable lifecycle engagement"],
};

export const INFLUENCER = {
  slug: "influencer-marketing",
  kind: "product",
  eyebrow: "Creator Collaboration OS",
  name: "Influencer Marketing Platform",
  hero: "Creator campaigns, measured like performance marketing.",
  subtitle: "Discover verified creators, orchestrate multi-touch campaigns, and attribute revenue with native affiliate tracking — one workspace for the entire lifecycle.",
  accent: "coral",
  scene: "creators",
  stats: [
    { v: "E2E",  l: "Campaign Mgmt" },
    { v: "ROI",  l: "Measurable Results" },
    { v: "Native", l: "Affiliate Tracking" },
    { v: "100%", l: "Verified Creators" },
  ],
  capabilities: [
    { t: "Influencer Discovery",   d: "Filter across niches, geographies, audience quality, engagement and past brand fit." },
    { t: "Communication & Hub",    d: "Central conversation threads, briefs, deliverable timelines and approvals in one place." },
    { t: "Campaign Management",    d: "Plan, launch and run multi-creator campaigns with milestones, budgets and content calendars." },
    { t: "Live Tracking",          d: "Real-time posting status, story views, reach and creative performance as it happens." },
    { t: "Analytics & ROI",        d: "Cost per engagement, CPM, CPV, sales lift and true ROI reconciled per creator." },
    { t: "Affiliate Marketing",    d: "Unique tracking links, coupon codes, native attribution and creator commission engines." },
    { t: "Payments & Compliance",  d: "Automated payouts, TDS handling, invoices and contract flows aligned with local rules." },
  ],
  bestFor: ["D2C Brands", "Consumer Services", "Education Brands", "Apps", "Local Franchises"],
  outcomes: ["Faster creator sourcing", "Smoother execution", "Measurable ROI with affiliate attribution"],
};

// ---------- SOLUTIONS ----------
export const ECOMMERCE = {
  slug: "ecommerce-os", kind: "solution", eyebrow: "E-Commerce OS", name: "E-Commerce OS",
  hero: "One operating system for the modern storefront.",
  subtitle: "Product, order, CRM, marketing, support and supply chain — unified under one AI-native platform, engineered for D2C and marketplace growth.",
  accent: "saffron",
  scene: "commerce",
  stats: [
    { v: "One", l: "Unified Platform" },
    { v: "E2E", l: "Commerce OS" },
    { v: "24/7", l: "AI Support" },
    { v: "Real-time", l: "Analytics" },
  ],
  capabilities: [
    { t: "Product & Inventory",   d: "Central catalog, variants, stock across channels and warehouses, real-time inventory truth." },
    { t: "Order Lifecycle",       d: "End-to-end order flows from cart to delivery, returns, exchanges and refunds." },
    { t: "CRM & Retention",       d: "Unified customer profiles, cohorts, RFM, loyalty and lifecycle automation." },
    { t: "Marketing Workflows",   d: "Campaign builder across WhatsApp, email, SMS and push with journey-level attribution." },
    { t: "Conversational AI",     d: "24/7 pre-sales and post-sales agents trained on your catalog, policies and knowledge base." },
    { t: "Voice Agents",          d: "Outbound and inbound voice for order confirmations, feedback and re-engagement." },
    { t: "Data Analytics",        d: "Cohort, funnel, LTV, unit economics dashboards with alerts and anomaly detection." },
    { t: "Supply Chain Intel",    d: "Demand forecasts, replenishment triggers and vendor performance scoring." },
  ],
  whyGrid: ["Store Ops", "Growth Mktg", "AI Support", "Supply Chain", "Data Intel", "CRM"],
};

export const REALESTATE = {
  slug: "real-estate-os", kind: "solution", eyebrow: "Real Estate OS", name: "Real Estate OS",
  hero: "The operating system for property ecosystems.",
  subtitle: "Listings, leads, journeys, brokers, documents, communications and finance — one platform to run the entire real estate lifecycle.",
  accent: "terracotta",
  scene: "skyline",
  stats: [
    { v: "E2E", l: "Lifecycle Mgmt" },
    { v: "Unified", l: "Sales + Ops + Intel" },
    { v: "24/7", l: "Automated Engagement" },
    { v: "360°", l: "Portfolio View" },
  ],
  capabilities: [
    { t: "Property Listings Management", d: "Centralised listings with pricing, availability, media and channel syndication." },
    { t: "Lead Management",              d: "Multi-source capture, AI scoring, routing to sales agents and full activity history." },
    { t: "Customer Journey Tracking",    d: "From enquiry to site visit to booking to registration — mapped and measurable." },
    { t: "Partner Ecosystem",            d: "Broker onboarding, deal splits, performance leaderboards and payouts." },
    { t: "Project Analytics",            d: "Inventory velocity, price realisation, cohort demand and ROI per project." },
    { t: "Document Vault",               d: "Secure agreements, KYC, approvals with e-sign, versioning and audit trails." },
    { t: "Automated Communication",      d: "WhatsApp, SMS, email and voice flows for nudges, updates and reminders." },
    { t: "Finance Tracking",             d: "Bookings, collections, brokerage payouts and P&L views by project and channel." },
  ],
  whyGrid: ["Listings Mgmt", "Lead Tracking", "Journey Map", "Broker Network", "ROI Analytics"],
};

export const PHARMA = {
  slug: "pharma-os", kind: "solution", eyebrow: "Pharma OS", name: "Pharma & Healthcare OS",
  hero: "Compliance-first operations for regulated life sciences.",
  subtitle: "Batch review, quality dashboards, protocol preparation and APQR reporting — automated, auditable and validated for pharma workflows.",
  accent: "sky",
  scene: "helix",
  stats: [
    { v: "50%",  l: "Faster Reviews" },
    { v: "100%", l: "Audit Readiness" },
    { v: "ZERO", l: "Data Integrity Errors" },
    { v: "3x",   l: "Faster Release" },
  ],
  capabilities: [
    { t: "Quality Dashboards",         d: "Live QMS KPIs — deviations, CAPAs, audits and change controls in one view." },
    { t: "Batch Records Review Tool",  d: "AI-assisted BMR/BPR review with anomaly flagging and reviewer sign-off trails." },
    { t: "Protocol Preparation Tools", d: "Guided authoring of validation protocols with template libraries and version control." },
    { t: "CPV Tool",                   d: "Continued process verification with statistical monitoring and stage-wise trending." },
    { t: "APQR Reporting Tool",        d: "Automated Annual Product Quality Review compilation with regulator-ready outputs." },
    { t: "Assessment Tool",            d: "Risk assessment, impact analysis and structured decision workflows for QA teams." },
  ],
  whyGrid: ["Faster Documentation", "Compliance Readiness", "Process Visibility", "Consistent Workflows", "Automated Reporting", "Batch Reliability"],
};

export const SMARTCITIES = {
  slug: "smart-cities-os", kind: "solution", eyebrow: "Smart Cities OS", name: "Smart Cities OS",
  hero: "Cognitive infrastructure for the modern city.",
  subtitle: "Unified urban data, smart mobility intelligence and resource management — one operating layer for municipalities and public agencies.",
  accent: "leaf",
  scene: "city",
  stats: [
    { v: "25%", l: "Traffic Reduction" },
    { v: "30%", l: "Energy Savings" },
    { v: "40%", l: "Response Time" },
    { v: "1M+", l: "Citizens Served" },
  ],
  capabilities: [
    { t: "Unified City Data Platform",   d: "IoT, GIS, mobility, utility and citizen data streams unified in one governed lake." },
    { t: "Smart Mobility Intelligence",  d: "Traffic prediction, signal optimisation, incident response and transit analytics." },
    { t: "Utility & Resource Management",d: "Water, energy and waste monitoring with predictive maintenance and demand forecasts." },
  ],
  whyGrid: ["Traffic AI", "Energy Grid", "Water Systems", "Public Safety", "Urban Planning", "Emergency Response"],
};

export const EDUCATION = {
  slug: "education-os", kind: "solution", eyebrow: "Education OS", name: "Education OS",
  hero: "The learning operating system for institutions.",
  subtitle: "College LMS, cohort management, coding practice, video learning and assessments — a role-based platform for admins, HODs, educators and learners.",
  accent: "gold",
  scene: "learning",
  stakeholders: ["Admin", "HOD", "Educator", "Learner"],
  stats: [
    { v: "Role-Based", l: "Access Model" },
    { v: "Unified",    l: "Learning Layer" },
    { v: "Coding",     l: "Practice Engine" },
    { v: "Video",      l: "First LMS" },
  ],
  capabilities: [
    { t: "College LMS",                 d: "Course delivery, attendance, gradebook and academic operations for higher-ed institutions." },
    { t: "Groups & Cohort Management",  d: "Sections, batches, mentors and dynamic cohorts across programs and semesters." },
    { t: "Course Learning Experience",  d: "Blended lessons, discussions, assignments and progress tracking per learner." },
    { t: "Test Series Platform",        d: "Timed assessments, question banks, proctoring signals and result analytics." },
    { t: "Coding LMS",                  d: "Integrated coding practice, contests, autograders and structured learning paths." },
    { t: "Video LMS",                   d: "Adaptive video learning with in-video quizzes, notes and completion analytics." },
  ],
  whyGrid: ["Unified Platform", "Measurable Outcomes", "College Hierarchy", "Role-Based Access", "Coding Practice", "Contest Management"],
};

export const ENTERPRISEAI = {
  slug: "enterprise-ai-os", kind: "solution", eyebrow: "Enterprise AI OS", name: "Enterprise AI OS",
  hero: "The full-stack platform for enterprise AI.",
  subtitle: "RAG, agentic apps, voice, document AI, knowledge graphs and fine-tuning — a governed platform to take AI from proof-of-concept to production.",
  accent: "cobalt",
  scene: "modules",
  stats: [
    { v: "10x",       l: "Faster Development" },
    { v: "99%",       l: "Enterprise Uptime" },
    { v: "Full Stack",l: "End-to-End Platform" },
    { v: "Secure",    l: "Enterprise Grade" },
  ],
  capabilities: [
    { t: "RAG & Agentic Applications",   d: "Retrieval-augmented reasoning apps with tool use, planning and multi-step workflows." },
    { t: "Conversational AI",            d: "Enterprise chat agents for customers, employees and internal ops with guardrails." },
    { t: "Voice Agents",                 d: "Inbound and outbound voice AI with real-time telephony and CRM integrations." },
    { t: "Multi-Agent Systems",          d: "Coordinated agents that plan, delegate and execute across business processes." },
    { t: "Document AI",                  d: "Extract, classify and reason over unstructured documents at enterprise scale." },
    { t: "Data Engineering & Analytics", d: "Pipelines, warehouses, feature stores and metrics stacks for AI-ready data." },
    { t: "Agentic Knowledge Graph",      d: "Structured knowledge graphs powering reasoning, search and recommendation." },
    { t: "Database Agents",              d: "AI agents that reason over structured databases with governed query surfaces." },
    { t: "Fine-Tuning & RL",             d: "Model customisation with supervised fine-tuning, RLHF and evaluation loops." },
  ],
  whyGrid: ["Fast Deployment", "Enterprise Controls", "Measurable Eval", "PoC to Production", "Integration Ready", "Advanced Agents"],
};

export const PAGE_CONFIGS = {
  "whatsapp-marketing":  WHATSAPP,
  "influencer-marketing": INFLUENCER,
  "ecommerce-os":     ECOMMERCE,
  "real-estate-os":   REALESTATE,
  "pharma-os":        PHARMA,
  "smart-cities-os":  SMARTCITIES,
  "education-os":     EDUCATION,
  "enterprise-ai-os": ENTERPRISEAI,
};

// ==============================================================
// STANDALONE PAGES
// ==============================================================

export const RECOGNITION = {
  eyebrow: "Recognition",
  title: "Celebrating",
  titleAccent: "Excellence & Innovation",
  awards: [
    {
      name: "AP MSME Digital Empowerment Challenge 2025",
      subtitle: "Double Victory",
      body: "Winner — AI-Powered DPR Preparation Solution. Winner — SaaS-Based Export Console.",
      org: "Andhra Pradesh Innovation Society (APIS) and APMSME Development Corporation",
      image: "/assets/recognition/ap-msme-2025.jpg",
      wins: [
        "Winner · AI-Powered DPR Preparation Solution",
        "Winner · SaaS-Based Export Console",
      ],
    },
    {
      name: "Best AI Startup of the Year — 2025",
      subtitle: "HYBIZ TV Business Excellence Awards, 3rd Edition",
      body: "Recognized among the leading AI startups shaping enterprise-grade intelligence in India.",
      org: "HYBIZ TV",
      image: "/assets/recognition/best-ai-startup-2025.png",
      wins: [],
    },
  ],
};

export const CASESTUDIES = {
  eyebrow: "Case Studies",
  title: "Real ROI with AI Systems",
  cases: [
    { brand: "Jewellery Brand",     metric: "₹3.5 Cr+", label: "ROI from a single campaign",   desc: "AI-powered WhatsApp funnel driving exceptional returns through intelligent customer engagement." },
    { brand: "FMCG Brand",          metric: "2K → 37K", label: "Followers Growth",             desc: "1000+ UGC assets orchestrated across creators and channels." },
    { brand: "B2B Spices Export",   metric: "50+ tons", label: "Export inquiries in 1 month",  desc: "70% lower CPL through account-based targeting and localised creatives." },
  ],
};

export const ABOUT = {
  eyebrow: "About CittaAI",
  title: "About",
  titleAccent: "CittaAI",
  lead: "A full-service Enterprise AI consultancy delivering customized intelligence solutions worldwide.",
  stats: [
    { v: "100+", l: "Enterprise Clients" },
    { v: "50M+", l: "Users Served" },
    { v: "1B+",  l: "Data Processed" },
    { v: "99.9%",l: "Uptime SLA" },
  ],
  storyTitle: "Research-Grade Intelligence. Enterprise-Ready Scale.",
  story: "Founded in 2022 by researchers and engineers, CittaAI was built to bridge the gap between AI technology and enterprise value. Today we process billions of data points for Fortune 500 companies.",
  why: [
    { t: "Enterprise-Grade Security", d: "SOC2 Type II and HIPAA aligned controls across data, models and access." },
    { t: "99.9% Uptime Guarantee",    d: "Multi-region infra, active monitoring and 24/7 on-call incident response." },
    { t: "24/7 Dedicated Support",    d: "Named engineers, SLAs and joint runbooks with your operations teams." },
    { t: "Custom Model Fine-tuning",  d: "Domain adaptation with supervised fine-tuning, RLHF and evaluation harnesses." },
  ],
  principles: [
    { t: "Innovation First",   d: "We invest ahead of the curve, prototype in weeks and productionise in months." },
    { t: "Client Partnership", d: "We embed with your teams, aligning to your outcomes not our billable hours." },
    { t: "Ethical AI",         d: "Guardrails, evaluations and human oversight are non-negotiable — designed in, not bolted on." },
    { t: "Speed & Excellence", d: "Engineering discipline meets shipping velocity — nothing goes live without evidence." },
  ],
  team: {
    title: "Our Team",
    subtitle: "The engineers, operators and strategists behind CittaAI.",
    leaders: [
      { name: "Akhil Reddy",            title: "CEO",                         photo: "/assets/team/akhil-reddy.jpg",            linkedin: "#" },
      { name: "Vinay Velivela",         title: "CEO of Fixity Technologies",  photo: "/assets/team/vinay-velivela.jpg",         linkedin: null },
      { name: "Saladi Chandra Balaji",  title: "Co-Founder & COO",            photo: "/assets/team/saladi-chandra-balaji.jpg",  linkedin: null },
    ],
    others: [
      { name: "Ganesh Gandhi Vadalani", title: "CMO",                          photo: "/assets/team/ganesh-gandhi-vadalani.jpg", linkedin: null },
      { name: "Harish Nerati",          title: "Operations and Sales Head",    photo: "/assets/team/harish-nerati.jpg",          linkedin: null },
      { name: "Aravind Reddy",          title: "E-Commerce Head",              photo: "/assets/team/aravind-reddy.jpg",          linkedin: "#" },
      { name: "Parvatha Mohan",         title: "Business Development Head",    photo: "/assets/team/parvatha-mohan.jpg",         linkedin: null },
    ],
  },
};

export const CONTACT_PAGE = {
  eyebrow: "Contact",
  title: "Let's Build the Future",
  titleAccent: "of Enterprise AI",
  lead: "Tell us about your AI transformation goals and one of our engineers will get back within 24 hours.",
  cards: [
    { t: "Phone",        v: CONTACT.phone,   sub: CONTACT.hours, href: `tel:${CONTACT.phoneRaw}` },
    { t: "Email",        v: CONTACT.email,   sub: "Response within 24h", href: `mailto:${CONTACT.email}` },
    { t: "Headquarters", v: "Hyderabad, India", sub: CONTACT.address, href: null },
  ],
  inquiryTypes: [
    "General Inquiry",
    "Product Demo",
    "Partnership",
    "Careers",
    "Press & Media",
    "Investor Relations",
  ],
};

export const FOOTER = {
  columns: [
    { h: "Products", links: [
      { l: "WhatsApp Marketing", to: "/products/whatsapp-marketing" },
      { l: "Influencer Marketing", to: "/products/influencer-marketing" },
    ]},
    { h: "Services", links: [
      { l: "Data Engineering", to: "/services/data-engineering" },
      { l: "Enterprise & Agentic AI", to: "/services/enterprise-ai" },
      { l: "AI Strategy & Advisory",  to: "/services/ai-strategy" },
      { l: "MarTech 360",      to: "/services/martech-360" },
    ]},
    { h: "Company", links: [
      { l: "About Us",      to: "/about" },
      { l: "Case Studies",  to: "/case-studies" },
      { l: "Careers",       to: "#" },
      { l: "Blog",          to: "#" },
      { l: "Press",         to: "/recognition" },
    ]},
  ],
  contact: CONTACT,
  legal: {
    copy: `© ${new Date().getFullYear()} CittaAI Pvt. Ltd. All rights reserved.`,
    links: [
      { l: "Privacy Policy",  to: "#" },
      { l: "Terms of Service",to: "#" },
      { l: "Security",        to: "#" },
    ],
  },
  badges: [
    { src: "/assets/badges/iso.png",           alt: "ISO Certified" },
    { src: "/assets/badges/msme.png",          alt: "MSME - Government of India" },
    { src: "/assets/badges/startup-india.png", alt: "Startup India" },
  ],
  socials: [
    { l: "LinkedIn",  href: "#" },
    { l: "X",         href: "#" },
    { l: "YouTube",   href: "#" },
    { l: "Instagram", href: "#" },
  ],
};
