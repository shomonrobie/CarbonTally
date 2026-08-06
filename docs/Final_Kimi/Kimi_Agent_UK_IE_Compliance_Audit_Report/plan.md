# Task 8 — CarbonTally Application Architecture Specification (10 documents)

Architecture only: NO code, NO SQL, NO seed data, NO PDFs. Database is FROZEN at RC2 (post-migration names: `emission_factors`, `emission_factor_id`, `default_factor_year`, `facilities.eircode`, etc. — see 008 release notes). UK launch, Ireland beta. Consultants manage multiple orgs; three workspaces (customer/consultant/internal staff). Single codebase.

## Fixed platform decisions (orchestrator-resolved, all writers must honour)
- Monorepo (Turborepo + pnpm): `apps/web` (Next.js 15 App Router, React 19, TS, Tailwind + shadcn/ui), `apps/workers` (Node 20, tsx), `packages/*` shared
- Supabase: Postgres 16 + RLS (frozen policies), Auth (owns JWT/2FA/lockout/password reset), Storage (private buckets, tenant-prefixed), Realtime (messaging/notifications), Edge Functions only for webhooks/light glue
- API layer: Next.js route handlers + server actions behind a typed service layer; zod validation at API boundary (format authority — frozen validation-layering decision: DB = integrity only); never expose service role to client
- Workers consume `processing_queue`/`document_processing_queue` via skip-locked claim pattern (frozen single-queue direction); retry + DLQ per hardening plan
- Observability: structured logging (pino), Sentry; caching: Next.js cache + Redis (Upstash) only where justified
- Authz model: RLS-first + `organization_members.role`; consultant cross-org via client_access; staff via staff_profiles

## Stage 1 — 5 parallel writers (2 docs each)
- W1: `01_application_architecture.md` (all 22 areas in brief) + `07_security_architecture.md`
- W2: `02_folder_structure.md` + `03_module_breakdown.md` (~21 modules, each: responsibilities/dependencies/API boundaries/DB tables/scalability — DB tables must use frozen names from the dump/RC1)
- W3: `04_api_design.md` (every endpoint: REST path/method/auth/request/response/errors) + `05_worker_architecture.md` (10 workers + retry/DLQ/priority/scaling)
- W4: `06_storage_architecture.md` + `08_performance_plan.md` (10/100/1k/10k customers ladder)
- W5: `09_component_inventory.md` (every UI component) + `10_implementation_roadmap.md` (phases A–L per THIS brief: Foundation/Auth/Organizations/Suppliers/Documents/OCR/Carbon Engine/Reports/Messaging/Support/Admin/Testing + complexity per module)

## Stage 2 — Consistency review gate (one reviewer): frozen names used; no SQL/code/seed; decisions consistent across docs; all brief-required items per doc present.
## Stage 3 — Fix + deliver 10 .md files with KIMI_REF tags.
