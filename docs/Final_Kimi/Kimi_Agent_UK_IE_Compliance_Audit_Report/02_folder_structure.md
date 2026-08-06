# CarbonTally — 02 · Folder Structure (RC2 Frozen Schema)

Monorepo layout for the UK launch / Ireland beta build. Turborepo + pnpm workspaces. Database is **frozen at RC2** — nothing in this tree implies SQL, migrations or seed data. Post-migration names apply throughout (`emission_factors`, `emission_factor_id`, `emission_factor_used`, `default_factor_year`, `facilities.eircode`, `organizations.is_active`/`archived_at`, `facilities.meter_mpan_mprn`, `suppliers.sort_code`, `customer_documents.file_checksum`, `organization_metadata.total_floor_area_sqm`/`occupied_floor_area_sqm`).

```
carbontally/
├── apps/
│   ├── web/                                # Next.js 15 App Router (React 19, TS, Tailwind + shadcn/ui). Owner: web team. The ONLY deployable that talks to browsers.
│   │   ├── app/
│   │   │   ├── (customer)/                 # Route group: customer workspace (org owners/admins/members/viewers). Owner: web team.
│   │   │   │   ├── layout.tsx              # Customer shell: org switcher, tenant guard, nav scoped to member role.
│   │   │   │   ├── dashboard/              # Tenant dashboard (emissions summary, usage vs plan, tasks).
│   │   │   │   ├── facilities/             # Facilities & assets CRUD; postcode/Eircode conditional forms, MPAN/MPRN fields.
│   │   │   │   ├── suppliers/              # Suppliers CRUD, VAT/company-number lookup, sort-code (GB) handling, trigram search UI.
│   │   │   │   ├── documents/              # Uploads, batches, processing status (Realtime), verification & customer review.
│   │   │   │   ├── emissions/              # Emissions ledger, corrections (positive rows w/ type flag), factor provenance view.
│   │   │   │   ├── reports/                # Report list, generation requests, versions, comments, exports.
│   │   │   │   ├── secr/                   # SECR pack view/download (UK orgs; intensity ratios from floor-area metadata).
│   │   │   │   ├── messages/               # Conversations with consultant/staff; Realtime threads.
│   │   │   │   ├── notifications/          # Notification centre, preferences.
│   │   │   │   ├── tasks/                  # Customer-facing task list (assigned consultant tasks, approvals).
│   │   │   │   ├── support/                # Support/communication thread with staff; feedback submission.
│   │   │   │   ├── billing/                # Plan, usage meters (AI/manual pages), Stripe portal redirect.
│   │   │   │   └── settings/               # Org profile, country (GB/IE), currency, default_factor_year, members, invites.
│   │   │   ├── (consultant)/               # Route group: consultant workspace (multi-org). Owner: web team.
│   │   │   │   ├── layout.tsx              # Consultant shell: client switcher driven by consultant_clients grants.
│   │   │   │   ├── clients/                # Granted client organisations; client_access array filtering.
│   │   │   │   ├── work-queue/             # Cross-client document review & extraction tasks.
│   │   │   │   ├── reports/                # Cross-client report building, review before customer release.
│   │   │   │   ├── tasks/                  # consultant_tasks across clients, due dates, assignment.
│   │   │   │   ├── billing/                # consultant_billing records per client engagement (GBP/EUR).
│   │   │   │   └── settings/               # Consultant profile, firm membership, notification prefs.
│   │   │   ├── (staff)/                    # Route group: internal staff workspace. Owner: web team (staff pages pair with Platform Administration module).
│   │   │   │   ├── layout.tsx              # Staff shell guarded by staff_roles; no tenant context by default.
│   │   │   │   ├── operations/             # processing_queue claim/assign, SLA board, reassignment, workload.
│   │   │   │   ├── qc/                     # qc_checks/qc_checklists/qc_errors screens, approval pipeline.
│   │   │   │   ├── manual-extraction/      # manual_extraction_batches/items workbench, per-page time logging.
│   │   │   │   ├── organizations/          # Tenant admin: activate/suspend (is_active/archived_at), metadata, files.
│   │   │   │   ├── factors/                # emission_factors reference management UI (read-mostly; data loads are staff-run).
│   │   │   │   ├── communications/         # customer_communication console, internal notes (is_internal).
│   │   │   │   ├── analytics/              # dashboard_metrics, staff/team performance, sla_compliance views.
│   │   │   │   └── admin/                  # system_settings, queue_settings, sla_definitions, business_hours, templates.
│   │   │   ├── (auth)/                     # Route group: sign-in/up, password reset (latest-valid-wins tokens), invite accept, beta code entry.
│   │   │   ├── api/                        # Route handlers ONLY; thin adapters over packages/services. Owner: web team.
│   │   │   │   ├── auth/                   # Session, invite acceptance, reset-token endpoints.
│   │   │   │   ├── webhooks/               # Inbound webhooks re-published to Supabase Edge Functions (webhooks-only rule).
│   │   │   │   ├── v1/                     # Versioned REST-ish endpoints per module; zod-validated at the boundary.
│   │   │   │   └── realtime-auth/          # Realtime channel authorisation endpoint (per-tenant channels).
│   │   │   ├── layout.tsx                  # Root layout: fonts, providers (theme, query client, tenant context).
│   │   │   └── page.tsx                    # Marketing/redirect root; routes by user_type to the correct workspace.
│   │   ├── actions/                        # Server actions per module (documents.actions.ts etc.); zod in, service call out.
│   │   ├── components/                     # App-specific composed components (shells, nav, workspace chrome). shadcn primitives come from packages/ui.
│   │   ├── lib/                            # Web-only helpers: Supabase browser client (anon key ONLY), tenant context, formatters.
│   │   ├── hooks/                          # React hooks (use-tenant, use-realtime-channel, use-optimistic-queue).
│   │   ├── middleware.ts                   # Auth/session refresh, workspace guard routing, suspended-tenant read-only banner flag.
│   │   ├── next.config.ts                  # Turborepo transpilePackages for packages/*, image/storage domains.
│   │   └── package.json
│   └── workers/                            # Node 20 + tsx long-running processes. Owner: platform team. Service role ONLY; never client-side.
│       ├── src/
│       │   ├── index.ts                    # Entry: supervisor loop, graceful shutdown, health endpoint.
│       │   ├── claim/                      # SKIP LOCKED claim loops; predicates MUST match I2 partial indexes exactly
│       │   │   ├── document-queue.ts       # Claims document_processing_queue (status pending/processing/manual_review/manual_extraction/qc/customer_review).
│       │   │   ├── processing-queue.ts     # Claims processing_queue (staff/consultant task pipeline).
│       │   │   └── report-queue.ts         # Claims report_generation_queue.
│       │   ├── jobs/                       # One file per job type; thin — logic lives in packages/services.
│       │   │   ├── ocr-extract.ts          # OCR/AI extraction → manual_extraction_items / emissions drafts.
│       │   │   ├── factor-suggest.ts       # AI mapping hints → emission_factor_used suggestions (never auto-approves).
│       │   │   ├── report-build.ts         # Report/SECR pack assembly → report_versions, export artefacts to Storage.
│       │   │   ├── usage-rollups.ts        # usage_tracking daily/month rollups, plan-limit checks.
│       │   │   └── notifications-fanout.ts # notification_delivery fan-out, email_logs writes.
│       │   └── instrumentation/            # Structured logs (processing_logs/processing_time_log writers), metrics.
│       └── package.json
├── packages/
│   ├── db/                                 # Generated Supabase types + typed clients. Owner: platform team. GENERATED CODE — never hand-edited.
│   │   ├── src/
│   │   │   ├── database.types.ts           # Output of `supabase gen types` against the frozen RC2 schema. Regenerate only on schema release.
│   │   │   ├── client.server.ts            # Service-role client factory (server/workers only; asserts not-browser).
│   │   │   ├── client.anon.ts              # Anon client factory for RLS-respecting server components.
│   │   │   ├── tables.ts                   # Frozen table-name constants (emission_factors etc.) to prevent stale-name typos.
│   │   │   └── enums.ts                    # CHECK IN-list vocabularies mirrored as const unions (status/role/country/currency). Single mirror of K4 lists.
│   │   └── package.json
│   ├── types/                              # Hand-written domain types & DTOs shared across apps. Owner: platform team. No runtime deps.
│   ├── validation/                         # Zod schemas — SINGLE SOURCE OF TRUTH for API and frontend. Owner: platform team.
│   │   ├── src/                            # One file per module (auth, facilities, suppliers, documents, reports...); includes postcode/Eircode,
│   │   │                                 # VAT/company-number/MOD97 format rules (DB deliberately does not enforce formats — K9 rejected).
│   │   └── package.json
│   ├── services/                           # Typed service layer — the ONLY code that queries the DB. Owner: platform + module owners per file.
│   │   ├── src/
│   │   │   ├── auth/                       # auth.service.ts — sessions, invites, reset tokens, erasure (anonymise_user RPC guard).
│   │   │   ├── organizations/              # organizations.service.ts — CRUD (service-role only create), suspension, metadata/floor area.
│   │   │   ├── facilities/                 # facilities.service.ts, assets.service.ts — postcode/Eircode presence rule, MPAN/MPRN.
│   │   │   ├── suppliers/                  # suppliers.service.ts — unique VAT/company-no handling, trigram search.
│   │   │   ├── documents/                  # documents.service.ts — upload init (checksum dedupe), batches, verification, review.
│   │   │   ├── ocr/                        # ocr.service.ts — document_processing_queue lifecycle, extraction items, AI hints.
│   │   │   ├── manual-review/              # manual-review.service.ts — queues, assignment, QC, approvals, SLA clocks.
│   │   │   ├── carbon-engine/              # carbon.service.ts — emissions computation, corrections, aggregation read models.
│   │   │   ├── emission-factors/           # factors.service.ts — country/year/source lookup, natural-key resolution (year, activity, country).
│   │   │   ├── reports/                    # reports.service.ts — templates, versions, generation queue, exports.
│   │   │   ├── secr/                       # secr.service.ts — SECR pack assembly, intensity metrics from floor-area metadata.
│   │   │   ├── users/                      # users.service.ts, profiles (consultant/staff), presence.
│   │   │   ├── permissions/                # permissions.service.ts — membership, consultant grants, staff roles; the is_org_member/is_org_active contract.
│   │   │   ├── messaging/                  # messaging.service.ts — conversations, participants, message fan-out.
│   │   │   ├── notifications/              # notifications.service.ts — templates, delivery, preferences.
│   │   │   ├── tasks/                      # tasks.service.ts — consultant_tasks, internal_tasks, assignments.
│   │   │   ├── support/                    # support.service.ts — customer_communication, feedback, glossary.
│   │   │   ├── audit/                      # audit.service.ts — append-only writers for all *_log/audit tables.
│   │   │   ├── platform-admin/             # admin.service.ts — SLA defs, workload, performance, metrics.
│   │   │   ├── settings/                   # settings.service.ts — system_settings, queue_settings, business_hours.
│   │   │   ├── billing/                    # billing.service.ts — subscriptions, usage meters, consultant_billing, Stripe sync.
│   │   │   └── storage/                    # storage.service.ts — signed URLs, tenant-prefixed private buckets, checksum dedupe.
│   │   └── package.json
│   ├── ui/                                 # shadcn/ui primitives + CarbonTally theme tokens. Owner: design system. No business logic, no imports from services/db.
│   ├── config/                             # Shared config: env schema (zod-parsed), ESLint, tsconfig bases, Tailwind preset. Owner: platform team.
│   │   ├── src/env/                        # env.server.ts (service role keys — fails if imported from client bundle), env.client.ts (NEXT_PUBLIC_* only).
│   │   └── package.json
│   └── utils/                              # Pure helpers: dates (UK/IE fiscal), units conversion, money (GBP/EUR), checksums. No I/O. Owner: platform team.
├── supabase/
│   └── functions/                          # Edge Functions — WEBHOOKS ONLY (Stripe, inbound email, storage events). Owner: platform team.
│       ├── stripe-webhook/                 # Verifies signature → billing.service via service role.
│       ├── inbound-email/                  # Inbound support/communication mail → customer_communication.
│       └── _shared/                        # Signature verification, service-role client bootstrap.
├── emails/                                 # Transactional email templates (React Email) mirroring email_templates rows. Owner: product/marketing; rendering by notifications service.
├── tests/
│   ├── e2e/                                # Playwright: workspace isolation matrix (Gate 4), consultant grants, org switching, IE fixtures.
│   ├── contract/                           # Zod boundary tests per route handler; IN-list vocabulary parity vs packages/db/enums.ts.
│   ├── integration/                        # Service-layer tests against a Supabase test project; RLS posture checks (read-only suspended tenant).
│   └── unit/                               # Vitest for packages/{services,utils,validation}; carbon-engine golden numbers.
├── turbo.json                              # Pipeline graph; db:types as a manual, schema-release-gated task.
├── pnpm-workspace.yaml
└── package.json                            # Root scripts; engines pinned (Node 20, pnpm 9).
```

## Conventions

**File naming**
- Files: kebab-case (`carbon.service.ts`, `use-tenant.ts`). React components: PascalCase files (`FacilityForm.tsx`). Tests colocated as `*.test.ts` / `*.spec.ts` (e2e in `tests/e2e` only).
- Service files follow `<module>.service.ts`; route handlers are `route.ts` under `app/api/v1/<module>/`; server actions are `<module>.actions.ts` in `apps/web/actions/`.
- Database identifiers in code always use post-migration names via `packages/db/tables.ts` constants — the string `defra_` is banned outside migration archaeology (lint rule).

**Colocation rules**
- UI components colocate with their route segment until reused by ≥2 workspaces, at which point they move to `apps/web/components/`; promotion to `packages/ui` requires being presentational-only.
- Zod schemas never colocate with routes or components — they live exclusively in `packages/validation` and are imported by both actions/route handlers and forms (react-hook-form zodResolver).
- Job orchestration colocates in `apps/workers/src/jobs/`; the business logic they invoke stays in `packages/services`.

**Import boundaries (enforced by ESLint `no-restricted-imports` + TS project references)**
- `packages/*` may **never** import from `apps/*`.
- `packages/ui`, `packages/utils`, `packages/types`, `packages/validation` may not import from `packages/db` or `packages/services` (keeps the design system and validation layer deployable anywhere, including the client bundle).
- `packages/services` may import `db`, `types`, `validation`, `utils`, `config` — and nothing else.
- Client components may import only `ui`, `types`, `validation`, `utils`, and `config/env.client`. `config/env.server` and `packages/db/client.server` assert `typeof window === 'undefined'` and fail the build otherwise — the service-role key can never reach the browser.
- `apps/workers` imports `packages/services` + `config/env.server` only; it never imports `apps/web`.

**Validation — single source of truth**
- Every API payload (route handler body/query, server action argument, worker job payload) is parsed with a schema from `packages/validation`. Format rules (UK company number, VAT, MOD97, postcode, Eircode routing key, phone, email) live here and **only** here — the frozen DB enforces IN-lists, ranges, presence and uniqueness, not formats.
- DB-mirrored vocabularies (K4 IN-lists: statuses, roles, country ∈ {GB, IE}, currency ∈ {GBP, EUR}) are defined in `packages/db/enums.ts` and re-exported through `packages/validation`; contract tests assert parity so app state can never diverge from DB CHECKs.

**Database types — generated, never hand-edited**
- `packages/db/src/database.types.ts` is produced by `supabase gen types` against the frozen RC2 schema. It is committed for build hermeticity, regenerated only upon a schema release, and any hand edit fails CI (checksum guard). All queries go through `packages/services` typed against these generated types.

**Environment / config handling**
- All environment variables are declared and parsed via zod in `packages/config/src/env/`. Missing or malformed env fails fast at boot (web and workers alike). Secrets (Supabase service-role key, Stripe secret, OCR provider keys) exist only in `env.server`; only `NEXT_PUBLIC_*` keys exist in `env.client`. Per-environment values come from the hosting platform's secret store — never committed `.env` files beyond `.env.example`. Workers additionally require `WORKER_CLAIM_PREDICATE` constants kept in lockstep with the I2 partial indexes (verified by a contract test, per RC1 Known Limitation 5).

**Supabase usage rules encoded by this layout**
- RLS is the tenancy backbone; all browser traffic uses the anon client. The service-role client is constructed only in `packages/db/client.server.ts`, imported only by services running in route handlers, server actions, workers, or Edge Functions.
- Storage buckets are private and tenant-prefixed (`org-<organization_id>/...`); all access via `storage.service.ts` signed URLs — no public buckets, ever.
- Realtime channels are per-tenant and authorised through `app/api/realtime-auth/`; presence/typing features reuse the same channel layer.
- Edge Functions exist solely for inbound webhooks; all other server logic lives in `apps/web` or `apps/workers`.
