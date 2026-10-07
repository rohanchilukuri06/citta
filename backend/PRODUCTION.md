# CittaAI Chatbot — Production Runbook

## How a message is answered

```
POST /api/chat  (rate limited, input validated)
  → vector-index integrity gate (production: blocks chat if the index is stale)
  → conversation memory (SQLite): previous turns, offerings discussed, facts the visitor shared
  → turn kind: small talk · "what did I tell you…" · "explain that more simply" (rewrite) · knowledge question
  → compound request split into up to 6 questions ("What is X, who is it for, and where is your office?")
  → SemanticChatPipeline.decide() per question   entity · aspect · scope, one conversation state
       rules (registry names/aliases, typo-tolerant) + BGE similarity + context
       → field arbitration → LLM adjudication only when uncertain / purely semantic
  → KnowledgeToolRouter                     canonical operation (get_capabilities, list_services, …)
  → KnowledgeOperationExecutor             only that section of the registry + crawled cittaai.com pages;
                                            "not available" (with contact details) if empty
  → one LLM answer grounded in that evidence (NVIDIA Nemotron 3 Super; retries on busy/rate-limit, deadlines)
  → response_validator (unsupported products / prices / stats / case studies, checked against the evidence)
  → SSE stream (same payload shape the website widget already consumes)
```

The benchmark calls the same `decide()`; `tests/test_production_parity.py` fails if production and benchmark diverge.
The legacy pipeline (`RAGService._legacy_chat_stream`) only runs for action requests (schedule / ticket / proposal),
prompt-injection attempts, or as an emergency fallback, logged as `{"event": "semantic_fallback", ...}`.

## Required configuration (`backend/.env`)

| Variable | Production value | Notes |
|---|---|---|
| `ENVIRONMENT` | `production` | Enables fail-closed behaviour (stale index blocks chat; admin API disabled without a token). |
| `LLM_PROVIDER` | `nvidia` | Nemotron 3 answers and adjudicates (owner decision 2026-09-30: Nemotron only). `groq` is still supported. |
| `GROQ_API_KEY`, `GROQ_MODEL` | unused | Only needed if `LLM_PROVIDER=groq`. Its free tier (200k tokens/day) ran out during testing. |
| `LLM_FALLBACK_PROVIDER` | `none` | Comma-separated chain tried after the primary (e.g. `gemini`). With `none`, a Nemotron failure serves the verified registry text with a note that a full answer isn't available right now. |
| `NVIDIA_API_KEY`, `NVIDIA_MODEL` | key, `nvidia/nemotron-3-super-120b-a12b` | Open-weights Nemotron 3 via build.nvidia.com. `nemotron-3.5-lightning-30b-a3b` timed out in testing. 429/502/503/504 are retried twice (0.75 s, 1.5 s). |
| `NVIDIA_ENABLE_THINKING` | `false` | Reasoning mode delays the first visible token past the 8 s first-token timeout. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | key, `gemini-3.8-flash` | Last resort; has returned intermittent 503 "high demand". |
| `GROQ_RATE_LIMIT_COOLDOWN_S` | `20` | After a Groq 429, requests skip Groq for this long and go straight to Nemotron. |
| `LLM_FIRST_TOKEN_TIMEOUT_S`, `LLM_REQUEST_TIMEOUT_S`, `GENERATION_DEADLINE_S` | 15 / 15 / 25 | 15 s first token with a single provider (8 s is right when a fallback exists); past the deadline the verified registry text is served. |
| `SEMANTIC_LLM_ADJUDICATION` | `true` | `false` runs rules + embeddings only (lower decision accuracy). |
| `CHAT_MEMORY_DB_PATH`, `CHAT_MEMORY_TTL_DAYS` | `data/chat_memory.db`, `30` | Persistent conversation memory; expired conversations are purged at startup. Put the file on a persistent disk. |
| `DECISION_CONCURRENCY` | `8` | Max simultaneous CPU-bound decisions (embedding + arbitration run in threads). |
| `ADMIN_API_TOKEN` | long random string | Required for `/api/admin/*`, `/api/debug/*`, `/api/tenants/onboard`, `/api/status`, `/api/health/details`. |
| `CORS_ORIGINS` | extra origins, comma-separated | `cittaai.com`, `www.cittaai.com` and this project's Vercel domains are allowed by default. |
| `CHAT_RATE_LIMIT_PER_SESSION_PER_MIN` / `_PER_IP_PER_MIN` | 20 / 60 | In-process: multiply by worker count, or put a shared limiter at the edge when scaling out. |
| `CHAT_MAX_MESSAGE_CHARS` | `2000` | Longer messages are rejected with 422. |

## Deploy checklist

1. `pip install -r requirements.txt` (first start downloads `BAAI/bge-base-en-v1.5`; the model and semantic pipeline are
   warmed in the background at startup, so the first visitor doesn't wait).
2. If content changed, refresh and re-index (never done automatically at startup):
   - `python scripts/sync_live_site.py` — crawls cittaai.com into `knowledge/site/cittaai_live.json` (needs Node).
   - `python scripts/sync_registry_from_site.py` — copies published fields the registry lacks (records `metadata.site_sync`).
   - `python build_index.py` — embeds all 21 registry files + the site pages into the vector DB.
3. `python -m pytest tests/ -n 0` — must be all green.
4. Start: `uvicorn server:app --host 0.0.0.0 --port 8000` (one worker per process; see rate-limit and memory notes).
5. `GET /api/health` must return `"status": "Healthy"` with `vector_index.fresh: true` and the providers `Configured`.
6. `python scripts/use_case_tests.py https://<your-host>` — 20 scripted conversation checks (memory, follow-ups, rewrite,
   multi-part, hallucination probes, out-of-scope); transcripts land in `evaluation/reports/use_case_transcripts.md`.
7. Optional: `python scripts/load_test.py https://<your-host> 24` — concurrent visitors, latency percentiles and a
   cross-session context-leak check (raise the per-IP rate limit first; all traffic comes from one IP).

## Operating it

- **Logs to alert on:** `semantic_fallback` (should be ~0), `provider_unavailable` (Nemotron down or timing out),
  `NVIDIA API 429/503 … retry` (NVIDIA busy or rate-limiting), `validator_rejected`, `[IndexIntegrity] STALE`,
  `Chat rate limit hit`.
- **Decision telemetry:** every decision is appended to `logs/semantic_decisions.jsonl` — use it to find new failure
  patterns, then add them to the **dev** split, never to a holdout.
- **Measuring:** `python evaluation/semantic_benchmark.py --split dev --llm on` for development; release numbers need a
  fresh holdout written by an isolated agent (v3, v4 and v5 have all been inspected and no longer count as unseen).

## Meeting / contact-request agent (`meeting_agent.py`)

- **Starts when** a visitor wants to contact CittaAI or meet ("I want a meeting", "book a demo", "can someone call me",
  "we'd like to collaborate"), or says yes to the offer shown after contact details. Plain questions ("what's your
  email?") are answered normally, followed by that offer.
- **Collects** name, company / organisation ("individual" if none), email, phone, purpose and preferred time — one at a time or all in one message — validating
  email and phone. It shows a summary; the visitor can edit ("change the time to Friday 11am"), cancel, or ask
  product questions midway (answered, then a reminder). Nothing is sent until they reply **yes**.
- **Sends** two emails: a thank-you confirmation to the visitor (Reply-To: the company), and a new-request
  notification to `COMPANY_LEAD_EMAIL` with the details and offerings discussed in the chat (Reply-To: the
  visitor). It's deterministic (no LLM), so contact details can't be altered by the model.
- **Email transport:** with `BREVO_API_KEY` (+ `MAIL_FROM` = a sender verified in Brevo) mail goes over Brevo's HTTPS API, which works on hosts that block SMTP (Railway trial/hobby). Otherwise SMTP is used.
- **Configure:** `COMPANY_LEAD_EMAIL`, `SMTP_USERNAME` (the sending Gmail address) and `SMTP_PASSWORD` (a Google
  App Password, which needs 2-Step Verification on). `SMTP_HOST`/`SMTP_PORT` default to Gmail (587, STARTTLS).
  Without them, requests are still saved and the visitor is told the confirmation email couldn't be sent.
- **Records:** every request is stored in the `meeting_requests` table (same SQLite file as chat memory) with the
  email delivery status, and listed at `GET /api/admin/meeting-requests` (admin token). This holds personal data
  and is not purged with chat memory: set `ADMIN_API_TOKEN` before deploying, and decide a retention period.
- **Limits:** `MEETING_REQUESTS_PER_SESSION` (default 3). Log events: `meeting_email_failed`,
  `meeting_request_saved_no_email`.

## Content decisions in force (2026-09-30)

- Pharma OS resolves only for pharma/pharmaceutical/"healthcare" (its name). Hospital/clinic/medical aliases were
  removed because no published content supports them (`metadata.content_decisions` in `solution_pharma_os.json`).
- Benefits, target users and contact phone/email were imported verbatim from the public website (`metadata.site_sync`).
- **Leadership (owner-confirmed 2026-09-30):** Akhil Reddy is CEO of CittaAI. Vinay Velivela is CEO of Fixity Technologies,
  not CittaAI. Kiran Kumar is not part of the team and was removed everywhere (registry, legacy modules, compiled answers).
  No CTO is published. See `metadata.content_decisions` in `leadership_info.json`.
- **Pricing (owner decision 2026-09-30):** intentionally not published. The bot says "CittaAI doesn't publish pricing" and
  gives the contact details for a quote; it never quotes or estimates a price.
- Not published anywhere, so the bot says "not available" and gives the contact details: FAQs for
  8 offerings, target users for E-Commerce, Real Estate, Pharma, Smart Cities and Enterprise AI OS (their registry
  entries only say "Admin / User"), employee count, CFO and other unpublished company facts.

## Known limits

- Decision accuracy on genuinely unseen questions is below dev accuracy (last unseen holdout: 86% full decision with the
  LLM on, 0 catalog leaks) — see `evaluation/reports/`.
- The NVIDIA API catalog key is a free/trial endpoint, not unlimited: it is rate limited (roughly 40 requests/min) and
  can return 503 when busy. 24 simultaneous visitors: p50 9 s, p90 13 s, 3 of 48 answers fell back to verified text.
  For sustained public traffic use a paid NVIDIA NIM endpoint or self-host Nemotron (open weights), and consider
  `LLM_FALLBACK_PROVIDER=gemini` as a safety net.
- Rate limiting is in-memory and conversation memory is a local SQLite file: run one instance, or move both to shared
  storage (Redis / Postgres) before scaling out.
- The admin console is protected only by a shared token (no per-user accounts or audit trail).
