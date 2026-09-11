# CarbonTally V3 — Third-Party Processor / Service Register

**Status:** Draft — for legal review
**Date:** 24 August 2026
**Method:** Derived from CarbonTally repository source and configuration, the live API contract, and official provider legal/security documentation. Provider facts are dated and must be re-verified before reliance.

> **Important framing:** This register records services CarbonTally itself uses. "Subprocessor" below means a processor CarbonTally engages to process customer personal data. Each provider also has its *own* subprocessors (listed in the provider's official documentation); those are not CarbonTally's direct subcontractors but are relevant to a full transfer/DPA analysis.

---

## 1. Direct services used by CarbonTally

### 1.1 Supabase — core platform infrastructure

| Attribute | Detail |
|---|---|
| **Purpose** | Authentication (Supabase Auth: email/password, Google OAuth, magic links, sessions); PostgreSQL database (primary datastore); Storage (private `documents` bucket served only via short-lived signed URLs); Realtime (`postgres_changes` for notifications and messaging). |
| **Data potentially processed** | All application data: account credentials/sessions, org & user records, documents, extracted data, emissions data, audit logs, messages, notifications, billing records. |
| **Role** | Processor (for customer content); infrastructure provider. |
| **Customer data passes through it?** | Yes — it is the primary database and storage. |
| **Authentication data?** | Yes — Supabase Auth manages credentials/sessions. |
| **Documents?** | Yes — document bytes are stored in the private `documents` bucket. |
| **Stores data?** | Yes — database rows, storage objects, auth metadata, logs. |
| **Processes data?** | Yes — DB queries, auth, storage, realtime streams. |
| **Official legal basis** | Supabase DPA (available at `supabase.com/legal/customer-resources/data-processing-addendum`), incorporating EU Standard Contractual Clauses (Commission Implementing Decision (EU) 2021/914) with module selection by role; default forum/jurisdiction Ireland; deletion/return on request within 30 days of expiry; region selection where the customer directs processing in a specific geographical region. |
| **Official compliance** | Supabase publishes SOC 2, ISO 27001, GDPR, HIPAA and other compliance information on its compliance documentation. (Self-reported; verify current status on `supabase.com/docs/guides/platform/compliance`.) |
| **Subprocessors (official list, dated 1 June 2026)** | Supabase Inc (support), ActiveCampaign/Postmark (email to users), **Amazon Web Services** (hosting), Atlassian (status page), Braintrust Data (monitoring/tracing), Clay Labs (customer insight), Clazar (marketplace), **Cloudflare** (hosting), ConfigCat (feature flags), **Google** (hosting), **Fly.io** (hosting), FrontApp (support), Sentry (error tracking), Notion Labs (support), Sublime Security (email security), Latacora (MSSP), **OpenAI** (NLP/generation for Supabase's own product features), PandaDoc (support), Slack (support), **Upstash** (serverless data hosting), **Vercel** (hosting). |
| **Known limitations / notes** | Supabase's subprocessor list includes OpenAI for *Supabase's* own feature set; this does not by itself mean CarbonTally customer data is sent to OpenAI. CarbonTally does not currently use any Supabase AI feature on customer documents. Supabase standard terms do not contain a universal public uptime SLA in the plain ToS; any CarbonTally availability commitment must be assessed independently. |

### 1.2 Render — backend API hosting

| Attribute | Detail |
|---|---|
| **Purpose** | Hosts the FastAPI backend/API (`carbontally-api.onrender.com` in production; `localhost:8050` locally) and any worker/background processing. |
| **Data potentially processed** | Any data processed by the backend in memory/transit; server logs; environment variables. |
| **Role** | Hosting/infrastructure provider; processor for customer content processed by the application. |
| **Customer data passes through it?** | Yes — application processing occurs on Render hosts. |
| **Documents?** | In transit/processing (documents are stored in Supabase Storage; extraction/OCR executes on the backend host). |
| **Stores data?** | Runtime filesystem/volumes and logs as applicable; persistent storage if provisioned. |
| **Official legal basis** | Render DPA (render.com/dpa); Render states certification under the EU-US Data Privacy Framework including the UK extension and Swiss-US DPF. |
| **Official compliance** | Render lists ISO 27001, SOC 2 Type 2, GDPR-DPA and HIPAA on its security page (self-reported; verify current status). |
| **Subprocessors (from Render security page)** | **AWS** (hosting/cloud), **Google Cloud Platform** (hosting/cloud), **Cloudflare** (hosting/cloud), **ClickHouse** (hosting/cloud). |
| **Known limitations / notes** | Render's ToS provides the service "as is" and "as available" with no stated uptime SLA in the public ToS. Render's platform-level assurances must not be converted into a CarbonTally SLA. |

### 1.3 Vercel — frontend hosting

| Attribute | Detail |
|---|---|
| **Purpose** | Hosts the public website and frontend application (production `carbontally.co.uk`, Vercel project `carbon-tally`). |
| **Data potentially processed** | Static assets and client-side JS; any data rendered to the browser; edge/CDN logs; serverless function execution where used. |
| **Role** | Hosting/CDN infrastructure provider; processor for customer content passing through the hosted frontend. |
| **Customer data passes through it?** | Yes — in transit to/from the browser (the frontend is the client). |
| **Documents?** | Not stored; only signed URLs are delivered to the browser. |
| **Stores data?** | Build artifacts, function logs, CDN caches (transient). |
| **Official legal basis** | Vercel DPA (vercel.com/legal/dpa) with UK IDTA, EU SCCs (2021/914), and schedules for EEA/Switzerland/UK/Australia/Canada/California; primary processing facilities in the United States; subprocessor list at `security.vercel.com`. |
| **Official compliance** | Vercel publishes SOC 2, ISO 27001 and other trust materials (self-reported; verify at vercel.com/trust). |
| **Subprocessors** | Hosts on AWS and Microsoft Azure per the DPA; full list at `security.vercel.com`. |
| **Known limitations / notes** | Vercel's published SLA (99.99% availability) applies to Vercel **Enterprise** service commitments; it is not a CarbonTally commitment and must not be presented as one. |

### 1.4 Resend — transactional email

| Attribute | Detail |
|---|---|
| **Purpose** | Transactional email delivery: org invitations, discovery requests, beta confirmation/invite; verified consultant senders for white-label From addresses. |
| **Data potentially processed** | Recipient email addresses, sender addresses, subject/body of transactional emails. |
| **Role** | Processor / email delivery provider. |
| **Customer data passes through it?** | Yes — email content and addresses for transactional mailings. |
| **Documents?** | No. |
| **Stores data?** | Email records/logs; email metadata. |
| **Official legal basis** | Resend DPA (resend.com/legal/dpa) incorporating EU SCCs (2021/914) and UK SCCs (EU SCCs amended by the UK Addendum); covers EU GDPR, UK GDPR, Swiss FADP, UK DPA 2018, PECR and CCPA; primary processing operations in the United States; governing law of the underlying terms England and Wales. |
| **Subprocessors (official list, dated 27 August 2026)** | **AWS** (hosting/sending), **Anthropic** (AI — Resend's own features), Attio (CRM), Cloudflare (WAF), Datadog (monitoring), Elastic (search), Estuary (data pipeline), Google (email communications/analytics), Inngest (background jobs), Liveblocks (collaboration), Metabase (analytics), Svix (webhooks), Tinybird (analytics), **Vercel** (server hosting). |
| **Known limitations / notes** | Resend's own AI subprocessors relate to Resend's product features; CarbonTally sends only its own transactional content. CarbonTally is not an email provider; delivery success is honest (emails fail visibly when Resend is unconfigured). |

### 1.5 OCR / document parsing — local, no external service

| Attribute | Detail |
|---|---|
| **Purpose** | PDF text extraction (pdfplumber/pypdfium2), OCR (Tesseract via pytesseract with a local ONNX RapidOCR fallback), CSV/XLSX parsing (pandas/openpyxl). |
| **Data potentially processed** | Document bytes processed on the backend host only. |
| **Role** | Open-source/local components executed inside CarbonTally's own infrastructure. |
| **Customer data leaves CarbonTally infrastructure?** | **No.** |
| **Stores data?** | No (in-memory processing). |
| **Official legal basis** | None required as third-party processing (no external transfer). |
| **Known limitations / notes** | OCR availability is an environment dependency; production must verify Tesseract/ONNX availability. |

---

## 2. Providers considered but NOT used

| Provider | Finding |
|---|---|
| Stripe | Schema columns exist (`consultant_billing.stripe_*`) but `backend/data/billing.py` explicitly does not use them and the billing service states no payment-provider integration exists. **Not active.** |
| OpenAI / Anthropic / OpenRouter (LLM) | `infra/llm_client.py` + `engines/ai_extraction.py` exist but are **not wired into any production route**. **Not active on customer data.** |
| Google Cloud Vision / AWS Textract / Azure OCR | Not referenced anywhere. **Not used.** |
| External analytics (GA/PostHog/Segment/etc.) | No code references in frontend or website candidate. **Not used.** |

---

## 3. Data flows summary

```
Browser (frontend, Vercel)
   │  HTTPS
   ▼
Vercel (static/CDN)  ──────────────┐
   │  HTTPS (same-origin)          │
   ▼                               │
Render (FastAPI backend)  ────────┤
   │  Supabase SDK (service role)  │
   ▼                               ▼
Supabase  ── Postgres DB   ──  Realtime (browser subscriptions)
   │  Storage (private 'documents' bucket, signed URLs only)
   │  Auth (credentials, sessions, Google OAuth)
   │
Resend (transactional email; US processing)
Local OCR/parsing on Render host (Tesseract / ONNX / pdfplumber / pandas)
```

Key properties:
- Customer documents are stored only in Supabase Storage (private bucket) and served to the browser only via short-lived signed URLs.
- Document parsing/OCR runs locally on the backend host; no third party receives document bytes in the current production pipeline.
- Transactional emails (and their recipients) pass through Resend.
- Auth credentials and sessions are handled by Supabase Auth.
- Messaging/notifications use Supabase Realtime.
- All three core providers (Supabase, Render, Vercel) plus Resend are US-headquartered or process in the US; international-transfer analysis (UK IDTA / EU SCCs + transfer risk assessments) is required for UK/EU customers. Supabase supports explicit region selection; the CarbonTally Supabase project region is not documented in the repository and must be confirmed.

---

## 4. Open items for the register

1. Confirm the region of the production Supabase project (`pvwiojoyaqywtydzcpbg.supabase.co`) and whether data residency can be asserted.
2. Confirm whether the backend runs as a Render web service and/or worker, and whether Render persistent disks are used (affects storage claims).
3. Confirm the Babui Limited (Bangladesh) processing arrangement contractually (subprocessor agreement) and add it as a CarbonTally subprocessor to the DPA schedule once verified — including IDTA/SCC + transfer risk assessment per the prior research document.
4. Confirm whether any Supabase feature (e.g., AI, vector) is ever enabled on customer data.
5. Add to this register any future payment provider, AI provider, or analytics provider before the relevant policy pages are updated.

---

## 5. Provider documents referenced (official)

- Supabase DPA: https://supabase.com/legal/customer-resources/data-processing-addendum
- Supabase Subprocessor List (1 June 2026): https://supabase.com/legal/subprocessor-list/June-1-2026.pdf
- Supabase Compliance: https://supabase.com/docs/guides/platform/compliance
- Render DPA / Security: https://render.com/dpa , https://render.com/security , https://render.com/terms
- Vercel DPA: https://vercel.com/legal/dpa ; Vercel SLA (Enterprise): https://vercel.com/legal/sla ; Vercel Privacy Policy: https://vercel.com/legal/privacy-policy
- Resend DPA: https://resend.com/legal/dpa ; Resend Subprocessors (27 August 2026): https://resend.com/legal/subprocessors
