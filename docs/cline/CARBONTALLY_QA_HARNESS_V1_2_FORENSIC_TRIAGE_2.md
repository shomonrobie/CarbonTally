# CarbonTally QA Harness V1.2 — Forensic Triage #2

- **Run:** `20260831T093007_1639121` · Git SHA `16391217103b98dcea520070c5a22c68f12fe607` (unchanged; no commits)
- **Reports:** `qa_harness/reports/latest/` (regenerated from this run) + `qa_harness/findings/{raw,normalized,deduplicated}/*.jsonl` + `qa_harness/evidence/{db,api,browser}/`
- **Mode:** READ-ONLY forensic triage. **No application, database, RLS, seed, Supabase, harness, or independent_audit modifications were made. No fixes. No commits/pushes.**
- **Method:** live DB schema probes (read-only), live browser probes (read-only navigation), source inspection, harness-internals inspection, and cross-referencing of every deduplicated finding.
- **Context:** this run was executed against the post-Phase-3 codebase (the QA-AUTH "all land on /onboarding" cluster and the QA-UI 500/console-error cluster from run `20260831T074414…` are **gone**; the browser stage now reports "10/10 personas authenticated, correct current landings", 0 responsive overflows, 0 accessibility violations).

---

## 1. Executive summary

The QA Harness V1.2 run executed all four stages against a healthy backend and produced **413 raw → 83 deduplicated findings**. Forensic analysis separates them as:

| Final classification | Count (of 83) | Findings |
|---|---|---|
| **HARNESS_DEFECT** | **48** | QA-DB-001..015, QA-DB-020..023, QA-DB-025, QA-API-001, QA-WF-001, QA-WF-002, QA-SEC-001, QA-UX-031..054 |
| **CONFIRMED_APPLICATION_DEFECT** | **5** | QA-DB-016..019 (performance indexes), QA-DB-024 (unique membership constraint) |
| **LIKELY_APPLICATION_DEFECT** | **30** | QA-UX-001..030 (customer documents/processing/review/reports pages lack table controls) |
| EXPECTED_BEHAVIOUR / PO_DECISION_REQUIRED / INSUFFICIENT_EVIDENCE / DUPLICATE (as primary class) | 0 of the 83 | the app-side 403s are expected behaviours but the findings themselves are harness errors (counted under HARNESS_DEFECT); QA-WF-002 carries a PO sub-dimension; DUPLICATE-ness is folded into cluster notes |

**Key conclusions:**

1. **The two Phase-3 P1 defects are confirmed fixed by this run**: no AUTH-onboarding cluster, no 500/console-error cluster, "correct current landings". The remaining P1 blockers are almost all **harness expectation/measurement problems**, not application defects.
2. **Every one of the 14 "missing key columns" (QA-DB-002..015) is a column-name mismatch** between the harness's documented expected model and the actual V3 schema (e.g. `status` vs `is_active`, `body` vs `content`, `title` vs `subject`, `stage` vs `queue_status`, `activity`/`co2e_per_unit`/`year` vs `activity_type`/`co2e_multiplier`/`reporting_year`). The equivalent data exists under the real column names. **Do not rename real columns to satisfy the harness.**
3. **`storage_buckets` is not "missing"** — Supabase Storage tables live in the `storage` schema (`storage.buckets`), which exists. The harness checks the `public` schema.
4. **`emissions_logs(organization_id)` is not missing** — a composite index `(organization_id, start_date)` exists and covers org-scoped queries; the harness matcher missed the abbreviated index name. **`processing_queue(stage/entity_id)` and `report_versions(organization_id)` reference columns that do not exist on those tables.**
5. **`36 migrations pending / applied 0` is a bookkeeping artefact** — the live DB has no `supabase_migrations` ledger (the schema was applied by direct SQL), so the harness's ledger query returns zero. The schema itself **is** present (115 tables match). This is an operational bookkeeping gap, not an unapplied schema.
6. **QA-DB-024 (UNIQUE `organization_members(organization_id, user_id)`) is a genuine integrity defect**: the constraint is absent AND `TenantRepository.add_member` performs an unguarded `INSERT` — duplicate memberships are possible through the API, which corrupts RLS/authorization semantics.
7. **The 54 UX table-rule findings collapse to one cluster with a genuine core.** The auditor applies **all 8 rule names to the single largest table per page** and fires sorting/filtering/search checks with **no row-count gate**. Rule names are mislabeled (a "conversations" rule firing on `/documents`) and tiny 2–13-row tables are flagged. The genuine signal: the customer **documents, processing, review and reports pages have no pagination/search/sort controls** (source-confirmed). The ops queues/staff roster already use DataTable; messaging/consultant/ops tables are bounded or tiny.
8. **QA-SEC-001 (anonymous `/home`) persists as a harness timing artifact**: the settled state is `/login` (verified live in Phase 3 and re-confirmed unchanged), the sweep samples the URL during ProtectedRoute's transient loading frame on first navigation.
9. **The 3 API/workflow "failures" are harness expectation errors**: each 403 is a ratified boundary (D20 PE isolation; org-member-only generic reports with a dedicated consultant route; N1 PE messaging).
10. **Manually reported issues** (harness didn't flag): customer large tables (confirmed), billing tables (bounded → expected), audit trail (filters+pagination exist; **search/sort genuinely absent**), consultant `[object Object]` (**not reproducible live**), consultant upload progress (partial), consultant IA (client list placement confirmed, requires PO view).

**Verdict:** NOT ACCEPTED is the correct harness verdict, but **not because the application is broken** — the dominant cause is harness expectation drift (DB model, table-audit mechanics, probe bindings, migration bookkeeping, anonymous timing). The genuine application work is small and focused (see the triage-only backlog).


---

## 2. Baseline

| Field | Value |
|---|---|
| Git SHA | `16391217103b98dcea520070c5a22c68f12fe607` (HEAD `main`) |
| Run | `20260831T093007_1639121` |
| Report timestamp | 2026-08-31T09:33:15Z |
| Acceptance | **NOT ACCEPTED** |
| Checks executed | 380 |
| Raw / normalized / deduplicated | 413 / 413 / 83 |
| DB | 115 tables inspected; result FAIL (25 findings) |
| API | 600 endpoints; 271 V3; 82 probes → 73 PASS, 1 FAIL, 3 PO DECISION REQUIRED, 5 SKIPPED |
| Workflow | 93 steps → 59 PASS, 2 FAIL, 32 SKIPPED (read-only mutation blocks) |
| Browser | 10/10 personas authenticated, correct landings, 21 route visits, 0 responsive overflows, 0 a11y violations, 385 raw browser findings |
| Stage outcomes (per report) | db 25 · api 26 · workflows 28 · browser 83 (note: browser's true dedup contribution is 55; the "83" in `stage_outcomes.browser` is a report-accounting artefact — the total dedup store is 83 = 25 DB + 1 API + 1 SEC + 54 UX + 2 WF) |

---

## 3. Finding inventory (83 deduplicated)

| Category | Count | IDs |
|---|---|---|
| API | 1 | QA-API-001 |
| DB | 25 | QA-DB-001..025 |
| SEC | 1 | QA-SEC-001 |
| UX | 54 | QA-UX-001..054 |
| WF | 2 | QA-WF-001..002 |

Severity distribution: P1 = 7 (QA-API-001, QA-DB-001, QA-DB-020, QA-DB-024, QA-SEC-001, QA-WF-001, QA-WF-002); P2 = 76. Raw sources: `run_browser.py` 385, `run_db.py` 25, `run_workflows.py` 2, `run_api.py` 1.

---

## 4. Deduplicated finding clusters

| Cluster | Findings | Root cause | Final class |
|---|---|---|---|
| **A — Harness table auditor mechanics** | QA-UX-001..054 | TableAuditor applies **all 8 rule names** to the **single largest table per page**; sorting/filtering/search checks have **no row-count gate**; `_has("pagination")` is a body-text heuristic. Rule names are therefore mislabeled and tiny tables are flagged. | 30 LIKELY (routes /documents,/processing,/review,/reports) + 24 HARNESS (routes /messaging,/consultant,/ops) |
| **B — Harness DB expected-model drift** | QA-DB-001..015, QA-DB-020..023, QA-DB-025 | `KEY_TABLE_COLUMNS`/`EXPECTED_TABLES`/index expectations use column names/schema locations that differ from the live V3 schema; migration ledger (`supabase_migrations`) absent. | HARNESS_DEFECT |
| **C — Harness API/workflow probe bindings** | QA-API-001, QA-WF-001, QA-WF-002 | Probes bound customer orgs / generic org endpoints / org-scoped messaging for PE and consultant instead of the correct entity/consultant-scoped surfaces. | HARNESS_DEFECT (app 403s = expected) |
| **D — Harness anonymous timing race** | QA-SEC-001 | URL sampled during ProtectedRoute's transient loading frame on first navigation. | HARNESS_DEFECT |
| **E — Genuine DB integrity** | QA-DB-024 | No UNIQUE(org,user) + unguarded `INSERT` in `TenantRepository.add_member`. | CONFIRMED_APPLICATION_DEFECT |
| **F — Genuine performance indexes** | QA-DB-016..019 | `upload_batches(org,status)`, `manual_extraction_items(batch_id,status)` genuinely unindexed. | CONFIRMED_APPLICATION_DEFECT (perf-only, P2) |
| **G — Genuine customer-page table gaps** | underlying QA-UX-001..030 | `/documents`, `/processing`, `/review`, `/reports` pages lack pagination/search/sort controls (source-confirmed). | LIKELY_APPLICATION_DEFECT (P2) |

---

## 5. Confirmed application defects

### 5.1 QA-DB-024 — Missing UNIQUE constraint `organization_members(organization_id, user_id)` (P1→P2)

| Field | Value |
|---|---|
| Category / severity | DB / P1 (reclassify P2 — integrity hardening; no observed duplicates) |
| Location | `public.organization_members`; `backend/data/tenant.py:113 add_member()`; `POST /api/v3/organizations/{org_id}/members` (`backend/api/v3_organizations.py:437`) |
| Evidence | Live DB: `pg_constraint` shows **no unique constraint** on organization_members. `TenantRepository.add_member` is a plain `INSERT … RETURNING` with **no duplicate check and no ON CONFLICT**; RLS `om_insert_admin` permits owner/admin inserts without an existing-membership guard. |
| Root cause | Duplicate membership is neither DB-enforced nor app-guarded. A second add of the same (org,user) creates a second row → inconsistent roles → RLS semantics corruption. |
| Reproduction | `POST /api/v3/organizations/{org}/members` twice with the same `user_id` (requires owner/admin) — second insert succeeds. |
| Duplicate/cluster | Isolated (the only genuine integrity finding in the DB set). |
| PO decision | No. |
| Next action | Add `UNIQUE (organization_id, user_id)` (migration) + guard/upsert in `add_member`; regression: duplicate-add returns 409, RLS role semantics intact. |

### 5.2 QA-DB-016..019 — Genuine performance-only index gaps (P2)

| Finding | Table/column | Evidence | Classification |
|---|---|---|---|
| QA-DB-016 | `upload_batches(organization_id)` | No index on org (only pkey + `idx_upload_batches_entity_id`) | CONFIRMED (perf-only) |
| QA-DB-017 | `upload_batches(status)` | No status index; queue scans filter on status | CONFIRMED (perf-only) |
| QA-DB-018 | `manual_extraction_items(batch_id)` | No batch_id index; org-scoped item lists join on batch_id | CONFIRMED (perf-only) |
| QA-DB-019 | `manual_extraction_items(status)` | No status index; stage queue queries filter on status | CONFIRMED (perf-only) |

These are correctness-neutral performance suggestions. At demo scale they are irrelevant; at production volumes the org-scoped queue/dashboard queries would seq-scan. Add in a migration with `IF NOT EXISTS`. No PO decision.

---

## 6. Likely application defects

### 6.1 QA-UX-001..030 — Customer documents / processing / review / reports pages lack table controls (P2)

| Field | Value |
|---|---|
| Findings | QA-UX-001..008 (/documents), QA-UX-009..016 (/processing), QA-UX-017..023 (/review), QA-UX-024..030 (/reports) |
| Location | `frontend/src/v3/customer/DocumentsPage.jsx` (204 lines; no pagination/search/sort), `ProcessingPage.jsx` (274 lines; no paging), `ReviewPage.jsx` (113 lines), `v3/reports/ReportsPage.jsx` (311 lines; no paging/search/sort) |
| Evidence | Source inspection: no `TablePagination`/`pageSize`/`onPageChange`/`search`/`sort` in those pages. The harness measurements (4–13 rows, 6 columns) are the demo-scale truth; the pages have no controls even in principle. |
| Root cause | These pages render plain `<table>`s without the DataTable contract used by ops queues, staff roster, and emissions history (which already paginate/sort). Documents, processing items, review items and reports are growable per organisation. |
| Reproduction | Log in as `owner.demo0001` → `/documents`/`/processing`/`/review`/`/reports`; no pagination/search/sort controls present. |
| Duplicate/cluster | All 30 are manifestations of one cluster (customer operational tables lack the DataTable contract). |
| PO decision | No (aligns with the existing ops DataTable precedent and the D-table standard). |
| Next action | Apply the shared `DataTable` contract (pagination, page-size, sort, where-appropriate search) to these four pages; verify on a growable dataset. NOTE: the harness finding labels ("documents"/"emissions"/"conversations"…) are mislabeled; the real requirement is page-level table controls. |

### 6.2 (Manual) Admin Audit Trail — search/sort genuinely absent (P2/P3)

`AuditConsoleTab.jsx` already has **filter dropdowns (action/resource/actor) and pagination** (Previous/Next, page count), but **no free-text search and no column sorting**. The manual report's "lacking … filter controls" overstates; the genuine gap is search + sort on a table that can grow. Classification: LIKELY_APPLICATION_DEFECT (partial).

### 6.3 (Manual) Consultant upload progress feedback (P2/P3)

`ClientWorkspace.onUpload` shows "“file” uploaded — it is now in the client's processing pipeline" and refreshes the documents + items tables, but there is **no per-document extraction→mapping→validation progress indicator** in the upload flow. The durable pipeline runs server-side (the items table shows stage status); the gap is visible feedback. Classification: LIKELY_APPLICATION_DEFECT (UX feedback); cannot be fully verified read-only (upload is a mutation).

### 6.4 (Manual) Consultant page information architecture (P2)

On `/consultant`, the **Clients list section renders below** the dashboard summary, portfolio health table, tabs and workspace content (source: `ConsultantPage.jsx` ~line 960, after the tab content). A consultant's primary navigational list (clients) is not the top-level surface. Classification: LIKELY_APPLICATION_DEFECT (IA) — confirm desired IA with the PO before restructuring.


---

## 7. Harness defects (48)

### 7.1 DB expected-model drift (20 findings)

| Finding | Harness expectation | Actual V3 schema (live-probed) | Class |
|---|---|---|---|
| QA-DB-001 | `storage_buckets` (public) | exists as `storage.buckets` (Supabase `storage` schema) | HARNESS |
| QA-DB-002 | `organization_members.status` | `is_active` (role/created_at/is_active) | HARNESS |
| QA-DB-003 | `consultant_clients.active` | `status` ('active'/'suspended'/'ended'/'inactive') | HARNESS |
| QA-DB-004 | `staff_profiles.staff_role, is_admin` | `role_id` (+ `staff_roles` join); is_admin is derived, never a column | HARNESS |
| QA-DB-005 | `organization_files.file_name, data_type, storage_path` | `name`, `file_type`/`mime_type`, `path`/`bucket` | HARNESS |
| QA-DB-006 | `upload_batches.file_id` | no file_id (files relate via separate tables) | HARNESS |
| QA-DB-007 | `manual_extraction_items.activity, quantity, unit` | `extracted_data`/`mapped_data` (JSONB) | HARNESS |
| QA-DB-008 | `emission_factors.activity, co2e_per_unit, year` | `activity_type`, `co2e_multiplier`, `reporting_year` | HARNESS |
| QA-DB-009 | `customer_factors.approved_by` | approval state derived (no approved_by column) | HARNESS |
| QA-DB-010 | `issues.item_id, blocking` | `work_item_id`/`document_id`/`batch_id`/`conversation_id`; no `blocking` flag | HARNESS |
| QA-DB-011 | `report_versions.organization_id, status, period_start, period_end` | those live on the report row; report_versions has `report_id, version_number, is_current` | HARNESS |
| QA-DB-012 | `conversations.title` | `subject` | HARNESS |
| QA-DB-013 | `messages.body` | `content` | HARNESS |
| QA-DB-014 | `notifications.body` | `message` | HARNESS |

### 7.2 API/workflow probe bindings (3)

| Finding | Harness | Actual | Class |
|---|---|---|---|
| QA-API-001 | pe_manager `GET /api/v3/processing/status?organization_id={org_a}` expected 200 | 403 "Processing Entity staff cannot access customer organisations" — the probe bound a **customer** org; PE entity status lives under `/api/v3/ops/entities/{entity_id}/…` | HARNESS (app correct) |
| QA-WF-001 | consultant `reporting` expected 200 on `/api/v3/reports?organization_id={client_org}` | 403 — generic reports is org-member-only by design; the consultant surface is `GET /api/v3/consultants/clients/{client_id}/reports` | HARNESS (app correct) |
| QA-WF-002 | pe_staff `allowed_messaging` expected 200 on `/api/v3/messaging/conversations?organization_id={msg_org}` | 403 — N1 denies PE on org-scoped conversations; the PE operational-messaging surface does not exist yet (PO item) | HARNESS (app correct) + PO sub-note |

### 7.3 QA-SEC-001 — anonymous `/home` (1)

URL sampled during ProtectedRoute's transient "Authenticating…" frame on first navigation; the settled URL is `/login` (verified live in the Phase-3 run and unchanged here — the application behaviour is correct). Harness fix: settle-aware sampling.

### 7.4 QA-UX-031..054 — table-rule noise on bounded/tiny tables (24)

QA-UX-031..038 (/messaging — card-based conversation list, no table, bounded), QA-UX-039..046 (/consultant — 13-row portfolio/client tables, bounded 5–30 clients/firm), QA-UX-047..054 (/ops — 2-row PE dashboard summary tables; the real ops queues already use the DataTable contract). These fire because the auditor applies every rule to the largest table and sorting/filtering/search have no row-count gate. Classification: HARNESS_DEFECT (no application change).

---

## 8. Expected behaviours (must NOT be changed)

1. **PE → customer organisation 403** (D20) — QA-API-001's actual response. Keep.
2. **PE → customer-org messaging 403** (N1) — QA-WF-002's actual response. Keep.
3. **Consultant → generic org-member reports 403** (dedicated consultant route exists). Keep.
4. **Anonymous → protected-route redirect to `/login`** (settled state). Keep.
5. **Genuine new user → `/onboarding`** (server decision). Keep.
6. **The real V3 column names** (`is_active`, `content`, `subject`, `message`, `activity_type`, `co2e_multiplier`, `reporting_year`, `queue_status`, `extracted_data`, `status`, `role_id`, …). Do NOT rename to match the harness model.
7. **`storage.buckets` in the `storage` schema.** Do NOT create a `public.storage_buckets` table.
8. **Existing RLS, tenant isolation, role boundaries.** Untouched.

---

## 9. PO decisions required

| # | Decision | Context | Recommendation |
|---|---|---|---|
| PO-1 | **PE operational-messaging surface** (still open from triage #1) | N1 requires PE "operational CarbonTally messaging"; no entity-scoped conversation model exists. The 403 is correct; the missing surface is the gap. | Decide entity-scoped support conversations vs mediated issues. |
| PO-2 | **Consultant workspace IA** | Client list currently renders below dashboard/portfolio/workspace content; upload flow lacks extraction→mapping→validation progress feedback. | Confirm desired IA (dedicated clients page/workspace) and progress-reporting expectations. |
| PO-3 | (Confirm) Customer-factor self-approval | Harness probes AUTHZ-26/SECB-12 are marked "PO DECISION REQUIRED" because they are **read-only mutation blocks**, not an unresolved product question. AGENTS.md §16 already ratifies: **Owner MAY self-approve a custom factor**. | No new decision needed; resolve the harness probe as "decided; cannot probe read-only". |
| PO-4 | (Confirm) Billing list scope | Customer billing orders are their own (bounded) list. | Keep as-is unless order volume grows. |

| QA-DB-015 | `processing_queue.item_id, stage, status, assigned_to, entity_id` | `document_id`, `queue_status`, `batch_id`; assignment lives on `manual_extraction_batches.entity_id` (D22) | HARNESS |
| QA-DB-020 | `emissions_logs(organization_id)` index | **exists** as composite `(organization_id, start_date)`; matcher missed the abbreviated name `emissions_logs_org_start_date_idx` | HARNESS |
| QA-DB-021 | `processing_queue(stage)` index | column is `queue_status`; covered by `processing_queue_claim_idx (queue_status, created_at)` | HARNESS |
| QA-DB-022 | `processing_queue(entity_id)` index | no such column on the table | HARNESS |
| QA-DB-023 | `report_versions(organization_id)` index | no such column on the table | HARNESS |
| QA-DB-025 | 36 migrations "pending" | schema **is applied** (115 tables); no `supabase_migrations` ledger → `applied_versions()` returns [] | HARNESS (bookkeeping) + operational note |


---

## 10. Insufficient evidence

| Item | Why | Action |
|---|---|---|
| (Manual) Consultant `[object Object]` in the client workspace | **Not reproducible**: a live read-only browser session as `consultant.demo0001` showed no `[object Object]` on `/consultant` or in the client workspace; source inspection found no direct object render of JSONB fields (`extracted_data`/`mapped_data`/`data_summary`) in the consultant surfaces. Possibly transient, role/state-specific, or already fixed. | Re-verify with the exact reproduction (specific client, specific tab, specific action) before any change. |
| (Manual) Consultant PDF upload "not visibly completing extraction/mapping" | Upload is a **mutation** (creates a document row) — cannot be exercised read-only. Source shows the upload notice + documents/items refresh + the items table with stage status; the perceived gap is progress feedback, not pipeline absence. | Verify end-to-end in an isolated mutation scope; confirm whether the items table's stage progression after upload is the intended feedback. |
| QA-DB-025 "36 migrations pending" as a *live-schema* statement | The schema is applied; only the ledger is empty. Whether "pending" is a defect depends on whether migration replay/tracking is required for this environment. | Operational: backfill `supabase_migrations.schema_migrations` (or provision via the CLI) so future migrations are trackable. Not an application defect. |
| Billing/order table growth | No evidence of order volumes that require pagination today. | Revisit if order counts grow; otherwise bounded. |

---

## 11. Database forensic analysis

1. **14 key columns** — all column-name/model mismatches (see §7.1). The live schema is the V3 source of truth (`v3_schema.sql` / applied schema dump), and the application queries use the real names (`is_active`, `content`, `subject`, `message`, `activity_type`, `co2e_multiplier`, `reporting_year`, `extracted_data`, `queue_status`, …). The harness `KEY_TABLE_COLUMNS` model is stale and must be refreshed to the actual schema — **not** the other way round.
2. **`storage_buckets`** — lives in `storage.buckets` (Supabase-managed schema). Not an app defect.
3. **Indexes** — 4 genuine perf gaps (QA-DB-016..019) + 4 harness expectations referencing non-existent/renamed columns or existing-but-abbreviated indexes (QA-DB-020..023). The `emissions_logs` composite `(organization_id, start_date)` genuinely covers org-scoped dashboard queries; the matcher failed only on index naming.
4. **Constraint** — `UNIQUE (organization_id, user_id)` is genuinely absent and the app insert is unguarded (§5.1) → confirmed integrity defect.
5. **Migrations** — the harness audits `supabase_migrations.schema_migrations`, which does not exist in this DB (only `auth/storage/realtime/supabase_functions` ledgers exist). `applied_versions()` therefore returns `[]` and all 36 repo files are "pending". The schema is present (115 tables). This is bookkeeping interpretation + an operational ledger gap.

---

## 12. API / security forensic analysis

1. **The 1 API FAIL (QA-API-001) and 2 workflow FAILs (QA-WF-001/002) are all deliberate 403s** matching ratified boundaries:
   - PE staff cannot access customer organisations (D20) — `ensure_processing_org_access` / `ensure_org_access`.
   - PE staff cannot access customer-org conversations (N1) — `_authorize_org_actor`.
   - The generic `/api/v3/reports` is org-member-only; consultants use `GET /api/v3/consultants/clients/{client_id}/reports`.
   **Do NOT change any of these to 200.**
2. **The 3 "PO DECISION REQUIRED" probes (AUTHZ-26, SECB-12, AUTHZ-27) are read-only mutation blocks** — they are never executed. AUTHZ-26/SECB-12 concern customer-factor self-approval, which is **already decided** (AGENTS.md §16: owner MAY self-approve). AUTHZ-27 is the D5 customer-approval gate (ALLOW for owner/admin). No new product decision is surfaced by these probes.
3. **No unexpected ALLOW was found.** Security boundaries (PE isolation, consultant grants, customer→ops denial, viewer→write denial, QC authority) were not weakened and remain enforced server-side.
4. **QA-SEC-001** is a harness timing artefact, not a real exposure (settled state `/login`).


---

## 13. Browser / UI / UX forensic analysis

1. **No AUTH or console-error findings this run** — the Phase-3 fixes hold (10/10 correct landings; healthy backend; no 500 noise).
2. **54 table-rule findings** = 7 route-level measurements × 8 rule names against the single largest table per page. Measurements were small (2–13 rows). Because sorting/filtering/search are checked without a row-count gate, even 2-row PE dashboard tables were flagged. The rule **names** do not correspond to the tables measured.
3. **Genuine core**: customer `/documents`, `/processing`, `/review`, `/reports` pages render plain tables with no pagination/search/sort (source-confirmed). These are growable and should adopt the DataTable contract used by ops queues/emissions/staff roster. This is the real UX work (30 findings → 4 page-level items).
4. **Bounded/tiny surfaces** (messaging, consultant, ops dashboard) need no table controls today.
5. **0 responsive overflows, 0 accessibility violations** — no responsive/a11y findings this run.

---

## 14. Manually reported issues — verification

| # | Issue | Verdict | Evidence |
|---|---|---|---|
| 1 | Large data tables without pagination/filter/sort/search | **CONFIRMED** for customer `/documents`, `/processing`, `/review`, `/reports`; NOT for ops queues/emissions/staff roster (DataTable present). | Source inspection (no paging/search/sort in the four customer pages; DataTable in ops/emissions). |
| 2 | Customers / billing-related tables | **EXPECTED (bounded)** — customer billing orders are the customer's own list; the ops organisation search/list is already paginated+searchable. | `BillingPage.jsx` (own orders, no paging); `getOpsOrganizations` (paginated search). |
| 3 | Admin Audit Trail lacking search/filter/sort | **PARTIAL** — filters (action/resource/actor) + pagination exist; **search + sort genuinely absent**. | `AuditConsoleTab.jsx` (SelectInput filters + DataTable + prev/next; no search input, no sortable columns). |
| 4 | Consultant client workspace `[object Object]` | **NOT REPRODUCIBLE / INSUFFICIENT EVIDENCE** | Live browser session (read-only) showed no `[object Object]`; source render paths are clean. |
| 5 | Consultant PDF upload not visibly completing extraction/mapping | **LIKELY UX-feedback gap** (pipeline present; no per-document extraction→mapping→validation progress indicator in the upload flow) | `ClientWorkspace.onUpload` notice + items refresh; items table shows stage status. |
| 6 | Consultant client list below reports | **CONFIRMED (IA)** — the Clients list section renders below the dashboard/portfolio/tabs/workspace content | `ConsultantPage.jsx` (~line 960 after tab content; live body-text ordering confirms). |
| 7 | Similar IA problems elsewhere | Ops workbench-in-queue (historical UH-1) was addressed via routed item workspaces; ops tabs are ordered sensibly; the consultant page is the main IA concern. | Source inspection. |


---

## 15. Root-cause clusters

| Cluster | Description | Findings | Genuine app work? |
|---|---|---|---|
| A | Table-auditor mechanics (8 rules × largest table, no row gate) | QA-UX-001..054 | Underlying 4-page gap (G) yes; reporting mechanics no |
| B | DB expected-model drift (column names, storage schema, index names, migration ledger) | QA-DB-001..015, QA-DB-020..023, QA-DB-025 | No |
| C | API/workflow probe bindings (customer-org/org-scoped endpoints for PE & consultant) | QA-API-001, QA-WF-001, QA-WF-002 | No (403s are correct) |
| D | Anonymous first-load timing race | QA-SEC-001 | No |
| E | Missing UNIQUE membership constraint + unguarded insert | QA-DB-024 | **Yes (P1/P2)** |
| F | Missing performance indexes (4) | QA-DB-016..019 | Yes (perf, P2) |
| G | Customer operational pages lack DataTable controls | QA-UX-001..030 | **Yes (P2)** |
| H | (Manual) Audit trail search/sort; consultant IA + upload feedback | manual items 3, 6, 5 | Yes (P2/P3) |

---

## 16. Recommended implementation order (triage only — nothing implemented)

1. **QA-DB-024** — add `UNIQUE(organization_id, user_id)` migration + guard `TenantRepository.add_member` (integrity/authorization-adjacent). Regression: duplicate-add → 409; role semantics intact.
2. **Customer page table controls (G)** — apply the shared DataTable contract (pagination/page-size/sort, search where sensible) to `/documents`, `/processing`, `/review`, `/reports`. Regression: growing lists paginate; no regression on bounded lists.
3. **Performance indexes (F)** — migration adding the 4 genuine indexes (`upload_batches(organization_id, status)`, `manual_extraction_items(batch_id, status)`).
4. **Harness corrections (A/B/C/D)** — refresh `KEY_TABLE_COLUMNS`/`EXPECTED_TABLES`/index expectations to the real schema; fix the table auditor (rule-name ↔ measured table matching, row-count gate on sort/filter/search); fix API/workflow bindings (entity/consultant-scoped surfaces); make the anonymous check settle-aware; treat the missing `supabase_migrations` ledger as an operational note. (qa_harness is intentionally not modified in this task.)
5. **Audit trail search/sort (H)** — add free-text search + column sorting to `AuditConsoleTab`.
6. **Consultant upload progress + IA (H)** — after PO-2.
7. **Migration ledger backfill** — operational, after confirming the desired provisioning path.

---

## 17. Findings that MUST NOT be fixed

1. The **403 boundaries** (PE org/messaging, consultant generic reports, customer ops) — deliberate; re-target the harness probes instead.
2. The **anonymous → `/login` redirect** (all protected routes) — correct.
3. **Genuine-new-user → `/onboarding`** — correct.
4. **Real V3 column names** — do NOT rename tables/columns to match the harness's stale model.
5. **`storage.buckets` in `storage` schema** — do NOT create a `public.storage_buckets` table.
6. **RLS / tenant isolation / role boundaries** — untouched; no change implied by any finding.
7. **Bounded lists** (messaging, consultant clients, PE dashboard, billing) — do NOT force DataTable controls.
8. **QA Harness / independent_audit** — not modified in this task; harness fixes are a separate work item.

---

## 18. Final triage totals

- **Total deduplicated findings triaged:** 83
- **CONFIRMED_APPLICATION_DEFECT:** 5 (QA-DB-016..019 perf indexes, QA-DB-024 unique membership constraint)
- **LIKELY_APPLICATION_DEFECT:** 30 (QA-UX-001..030 — customer documents/processing/review/reports pages need table controls)
- **HARNESS_DEFECT:** 48 (QA-DB-001..015, QA-DB-020..023, QA-DB-025, QA-API-001, QA-WF-001, QA-WF-002, QA-SEC-001, QA-UX-031..054)
- **EXPECTED_BEHAVIOUR:** the app-side 403s and redirects are expected; counted within HARNESS_DEFECT (the findings are wrong, the app is right). Separate MUST-NOT-FIX list in §17.
- **PO_DECISION_REQUIRED:** 2 open product decisions (PO-1 PE operational messaging; PO-2 consultant IA/upload feedback). PO-3 (customer-factor self-approval) is already decided; PO-4 (billing) confirm-only.
- **INSUFFICIENT_EVIDENCE:** consultant `[object Object]` (manual), consultant upload end-to-end progress (manual; mutation-gated), migration-ledger operational meaning.
- **DUPLICATE:** the 54 UX findings are duplicates of one cluster (folded into A/G); no separate count.
- **Manual issues verified:** 7 reviewed (1 confirmed-large tables, 1 partial-audit search/sort, 1 confirmed IA, 1 likely upload feedback, 1 not-reproducible, 1 expected-bounded, 1 note).
- **Recommendation:** the harness verdict "NOT ACCEPTED" is correct **as a process statement**, but the application work is concentrated in 3 areas: the membership constraint (E), 4 performance indexes (F), and DataTable controls on 4 customer pages (G), plus two PO-confirmed product refinements (PE messaging, consultant IA).

