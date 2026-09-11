# CarbonTally QA Harness V1.2 — Implementation Backlog (TRIAGE ONLY)

> Generated from the forensic triage of run `20260831T093007_1639121` (SHA `16391217103b98dcea520070c5a22c68f12fe607`).
>
> **TRIAGE ONLY — nothing here has been implemented.** Each item records the proposed fix and regression requirement so an implementation phase can pick it up directly.
>
> Classification legend: CONFIRMED_APPLICATION_DEFECT · LIKELY_APPLICATION_DEFECT · HARNESS_DEFECT · EXPECTED_BEHAVIOUR · PO_DECISION_REQUIRED · INSUFFICIENT_EVIDENCE · DUPLICATE.
> Full analysis: `docs/cline/CARBONTALLY_QA_HARNESS_V1_2_FORENSIC_TRIAGE_2.md`.

---

## Priority map

| Priority | Backlog items |
|---|---|
| **P1** | BL-1 (membership unique constraint) |
| **P2** | BL-2 (customer page table controls) · BL-3 (performance indexes) · BL-4 (audit trail search/sort) |
| **P2/P3** | BL-6 (consultant upload feedback — after PO) · BL-7 (consultant IA — after PO) |
| **P3** | BL-8 (migration ledger backfill, operational) |
| **Harness (separate, P3)** | BL-H1..BL-H4 (table auditor, DB model, probe bindings, anonymous settle check) |

---

## BL-1 [P1] — Enforce unique organisation membership

- **Finding/cluster:** QA-DB-024 · Cluster E · CONFIRMED_APPLICATION_DEFECT
- **Root cause:** `public.organization_members` has no `UNIQUE (organization_id, user_id)` constraint, and `backend/data/tenant.py:add_member()` performs an unguarded `INSERT` (no existing-membership check, no `ON CONFLICT`). Duplicate memberships are creatable through `POST /api/v3/organizations/{org_id}/members`, producing inconsistent roles and corrupting RLS semantics.
- **Evidence:** live `pg_constraint` shows no unique constraint; `TenantRepository.add_member` source; RLS `om_insert_admin` permits owner/admin inserts.
- **Proposed fix:** migration adding `UNIQUE (organization_id, user_id)` (after de-duplicating any existing rows); make `add_member` return 409/raise on an existing active membership (or `ON CONFLICT` upsert per product intent).
- **Regression requirement:** duplicate add → 409 with no new row; existing membership role update still works; RLS role semantics unchanged; `test_add_member_requires_admin`/`test_add_member_validates_role` still pass; cross-org isolation intact.

## BL-2 [P2] — DataTable contract for customer operational pages

- **Finding/cluster:** QA-UX-001..030 · Cluster G · LIKELY_APPLICATION_DEFECT
- **Root cause:** `/documents`, `/processing`, `/review`, `/reports` render plain `<table>`s without pagination/page-size/sort/search; these lists grow per organisation. (The 54 harness findings over-report this — see BL-H1.)
- **Evidence:** source inspection of `DocumentsPage.jsx`, `ProcessingPage.jsx`, `ReviewPage.jsx`, `ReportsPage.jsx` (no pagination/search/sort); contrast with ops queues/emissions/staff roster which already use the shared `DataTable` contract.
- **Proposed fix:** apply the shared `DataTable` component (pagination, page-size, sort; search where the list is free-text) to the four customer pages; keep bounded sub-lists as-is.
- **Regression requirement:** a growable dataset paginates without losing record counts; empty/error states preserved; mobile no horizontal overflow; existing page tests pass.

## BL-3 [P2] — Add the 4 genuinely missing performance indexes

- **Finding/cluster:** QA-DB-016..019 · Cluster F · CONFIRMED_APPLICATION_DEFECT (perf-only)
- **Root cause:** `upload_batches(organization_id)`, `upload_batches(status)`, `manual_extraction_items(batch_id)`, `manual_extraction_items(status)` are unindexed; org-scoped queue/dashboard queries would seq-scan at production volume.
- **Evidence:** live `pg_indexes` (only pkey + entity_id/file indexes on those tables).
- **Proposed fix:** migration with `CREATE INDEX IF NOT EXISTS` for the four columns.
- **Regression requirement:** queries unchanged (EXPLAIN shows index use); no schema/RLS change; migration applies cleanly on the demo DB.

## BL-4 [P2/P3] — Admin Audit Trail search + sort

- **Finding/cluster:** manual item 3 · Cluster H · LIKELY_APPLICATION_DEFECT (partial)
- **Root cause:** `AuditConsoleTab.jsx` has filter dropdowns + pagination but no free-text search and no column sorting on a growable audit table.
- **Evidence:** source inspection (`SelectInput` filters, prev/next pagination, no search input, no sortable columns).
- **Proposed fix:** add free-text search (actor/entity/action) and column sorting to the audit console (server-side if the backend `getOpsAudit` supports it; else bounded client-side sort).
- **Regression requirement:** search/sort combine with existing filters; pagination totals stay correct; staff-admin gating unchanged.

## BL-5 [Harness, P3] — Refresh harness DB expected model (do NOT change the app)

- **Finding/cluster:** QA-DB-001..015, QA-DB-020..023, QA-DB-025 · Cluster B · HARNESS_DEFECT
- **Root cause:** `qa_harness/db/schema_inventory.py` `EXPECTED_TABLES`/`KEY_TABLE_COLUMNS`, index expectations and the migration ledger query use names/schema locations that do not match the live V3 schema.
- **Evidence:** live schema probe (§7.1 of the triage): `is_active`/`status`/`content`/`subject`/`message`/`activity_type`/`co2e_multiplier`/`reporting_year`/`queue_status`/`extracted_data`; `storage.buckets`; composite `emissions_logs_org_start_date_idx`; no `supabase_migrations` ledger.
- **Proposed fix (harness):** update the expected model to the real schema; treat `storage.*` tables in their schema; match composite indexes by leading column (not index name token); treat a missing `supabase_migrations` ledger as "schema applied without ledger" not "unapplied".
- **Regression requirement:** harness DB stage re-run yields 0 false positives; genuine gaps (BL-1, BL-3) still detected.

## BL-6 [P2/P3, after PO] — Consultant upload progress feedback

- **Finding/cluster:** manual item 5 · Cluster H · LIKELY_APPLICATION_DEFECT / PO_DECISION_REQUIRED (PO-2)
- **Root cause:** `ClientWorkspace.onUpload` shows a one-line notice ("uploaded — in the client's processing pipeline") and refreshes lists; there is no per-document extraction→mapping→validation progress indicator in the upload flow.
- **Evidence:** source inspection; live (read-only) verification of the workspace UI. Upload itself is a mutation (cannot be tested read-only).
- **Proposed fix (after PO-2):** surface the document's pipeline stage (queued→extracting→mapping→validating→calculating→review) next to the upload; auto-refresh stage state.
- **Regression requirement:** upload→stage progression visible without manual refresh; no change to the durable backend pipeline or authorization.

## BL-7 [P2, after PO] — Consultant workspace information architecture

- **Finding/cluster:** manual item 6 · Cluster H · LIKELY_APPLICATION_DEFECT / PO_DECISION_REQUIRED (PO-2)
- **Root cause:** the consultant Clients list renders below dashboard/portfolio/workspace content on `/consultant` (single 1025-line page).
- **Evidence:** `ConsultantPage.jsx` (~line 960); live body-text ordering confirmed.
- **Proposed fix (after PO-2):** promote the client list to a first-class surface (dedicated clients page/workspace or top placement), keeping portfolio/reporting as secondary views.
- **Regression requirement:** consultant navigation flows (switch client, workspace, messaging, branding, team) still reachable; no permission change.

## BL-8 [P3, operational] — Migration ledger for the local DB

- **Finding/cluster:** QA-DB-025 · Cluster B · HARNESS_DEFECT (bookkeeping) + INSUFFICIENT_EVIDENCE (operational)
- **Root cause:** the DB schema was applied by direct SQL; no `supabase_migrations.schema_migrations` ledger exists, so migration tracking/replay is unavailable.
- **Evidence:** live `information_schema` (no `supabase_migrations` schema; auth/storage/realtime/supabase_functions ledgers exist); 115 tables present.
- **Proposed fix (operational):** backfill the ledger for the applied versions (or re-provision via the Supabase CLI) so future migrations are trackable.
- **Regression requirement:** schema unchanged; a subsequent migration applies cleanly; harness DB stage reports applied versions correctly.


## BL-H1..BL-H4 [Harness, P3] — Auditor and probe corrections

| Item | Findings | Proposed fix | Regression requirement |
|---|---|---|---|
| BL-H1 Table auditor | QA-UX-031..054 (noise on bounded/tiny tables) | Match rule names to the actual measured table's purpose; apply a row-count gate to sorting/filtering/search (pagination already gated); only evaluate rules relevant to the page's table type. | Re-run browser stage: 2-row PE tables and card-based messaging no longer flagged; genuine page gaps still detected. |
| BL-H2 API/workflow probe bindings | QA-API-001, QA-WF-001, QA-WF-002 | Re-bind: PE probes to `/api/v3/ops/entities/{entity_id}/…`; consultant reporting to `/api/v3/consultants/clients/{client_id}/reports`; PE messaging to the (future) entity-scoped surface or assert the N1 403 as the boundary. | Re-run API/workflow stages: 73 PASS + 0 FAIL; the deliberate 403s reported as EXPECTED_DENY. |
| BL-H3 Anonymous check | QA-SEC-001 | Settle-aware sampling (wait for the route to stabilise / assert no app-shell content) before classifying. | Fresh-context visits settle on `/login`; no false "reachable" findings. |
| BL-H4 PO probes | AUTHZ-26/SECB-12/AUTHZ-27 "PO DECISION REQUIRED" | Record that customer-factor self-approval is **decided** (AGENTS.md §16) and AUTHZ-27 is the D5 ALLOW gate; mark the probes as read-only-blocked rather than unresolved. | Run summary shows resolved decisions; no new PO items appear. |

---

## Items deliberately NOT backlogged (must NOT be fixed)

- The 403 boundaries (PE org/messaging, consultant generic reports, customer→ops) — expected behaviour.
- Anonymous → `/login` redirects — expected behaviour.
- Real V3 column names / `storage.buckets` schema location — do not rename/duplicate to satisfy the harness.
- Bounded lists (messaging, consultant clients, PE dashboard, billing) — no DataTable forced.
- Genuine-new-user onboarding — unchanged.
- RLS / tenant isolation / role boundaries — untouched.

---

*Backlog is triage-only. No application, database, RLS, seed, harness, or independent_audit change was made; no commits/pushes. All evidence is from run `20260831T093007_1639121` plus live read-only schema/browser probes.*

