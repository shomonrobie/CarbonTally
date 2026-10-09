# CT-PRODUCT-REALITY-AUDIT-01 — CarbonTally Product Reality / Persona E2E Audit

| Field | Value |
|---|---|
| **Task ID** | `CT-PRODUCT-REALITY-AUDIT-01` |
| **Title** | CarbonTally Product Reality / Persona End-to-End Audit |
| **Date** | 2026-10-05 |
| **Mode** | **READ-ONLY** — no application code, migration, schema, RLS, data, or configuration was changed |
| **Branch / HEAD** | `p8-release-reconciled` / `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| **Pre-existing working-tree dirt** | 160 `git status --porcelain` entries, **none created by this audit** |
| **Artefacts created by this audit** | this report only (+ read-only capture files under `/tmp/`, not committed) |
| **Findings source** | `docs/architecture/carbontally_master_handover_2026-10-05.md` §9 (9.1–9.14) |
| **Acceptance language** | `OBSERVED` / `CONFIRMED` / `PARTIALLY CONFIRMED` / `REFUTED` / `UNVERIFIED` — these are **not** synonyms for `ACCEPTED` (§73) |

---

## 0. How to read this report

Every finding carries four things:

1. **Status** — one of `CONFIRMED`, `PARTIALLY CONFIRMED`, `REFUTED`, `UNVERIFIED`, `PO DECISION REQUIRED`.
2. **Evidence class** — `RUNTIME` (live HTTP against the running stack), `CODE` (current Git source), `DB` (read-only SQL against the live local database), `DOC` (handover/audit text).
3. **Severity** — `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` / `INFO`. Severity here is *product/security impact*, not effort.
4. **Classification** — one of `SECURITY BOUNDARY` (working as intended), `FUNCTIONAL DEFECT`, `UX DEFECT`, `CAPABILITY GAP`, `DEMO-DATA/ROLE-COVERAGE GAP`, `PO DECISION REQUIRED`.

**Non-claims are stated explicitly.** Nothing in this report is an acceptance verdict for the investor demo, and nothing here asserts that a remembered/historical defect is still current (§80): every claim is re-derived from current runtime, current Git source, or current database state.

> **Brief reconstruction notice.** An explicit audit brief enumerating 28 numbered required sections was **not found** in the repository. The 28-section structure used below is **RECONSTRUCTED** from handover §9 (9.1–9.14) plus the standing audit-report standard in `AGENTS.md` §84. Section headings derived from the brief are marked `[RECONSTRUCTED]`. If a formal brief exists, this report should be re-mapped to it before it is treated as complete.

**Section index.** 1 Task identity · 2 Environment/runtime · 3 Git & read-only compliance · 4 Method/evidence · 5 Persona inventory · 6 Staff authority (runtime) · 7 Baseline verification · 8 Persona × endpoint matrix · 9 Surface inventory · 10 Data reality snapshot · 11 Findings FIND-9.1–9.14 (handover §9 re-verified) · 12 Persona findings P01–P10 · 13 Denial-shape analysis · 14 Product-reality register PR-01–PR-07 **+ root cause** · 15 Environment fidelity · 16 Cross-boundary isolation pass · 17 Pipeline reality (model vs data) · 18 Unverified register U-01–U-14 · 19 Consolidated PO decision register PD-01–PD-11 · 20 Universal operational questions per workspace · 21 Capability ownership · 22 Limitations & confidence · 23 Acceptance statement · Appendix A (46×10 matrix) · Appendix B (method/evidence) · Appendix C (read-only compliance & Git).

**Reading order for a decision-maker:** §23 (verdict) → §14 (register + root cause) → §19 (PO decisions) → §18 (what is not yet known). **Reading order for an implementer:** §19's no-PO backlog → §11 (findings with file:line evidence) → §18 (probe specification).

---

## 1. Task identity, scope and boundary `[RECONSTRUCTED]`

**In scope**

- The **product reality** of each operating persona: what they can actually reach, see, and do on the running local stack.
- **Persona → endpoint** authorization behaviour (allow and deny), from the live API.
- **Product/UX findings** listed by the Product Owner in handover §9, each code-traced to a root cause.
- **Data reality**: whether the tables that a workflow depends on hold real, coherent rows.
- **Security boundary reality**: cross-tenant / cross-persona / PE isolation behaviour.

**Explicitly out of scope / not performed**

- No browser/Playwright/Cypress run. Therefore **visual, responsive and accessibility findings are `UNVERIFIED`** (§22, §23) unless provable from source.
- No mutation of the investor demo dataset (no INSERT/UPDATE/DELETE, no seed, no reset) — `AGENTS.md` §55.
- No production access, no Render/Vercel/Supabase-hosted checks.
- No AI/LLM analysis pass.

**Boundary statement.** Read-only SQL (`SELECT` only, no secret columns), read-only HTTP (`GET` only in the persona matrix), source inspection, and this report. No code was written, no migration applied, no data changed, no service restarted, nothing committed or pushed.

---

## 2. Environment and runtime state `[RECONSTRUCTED]`

| Component | Observed state |
|---|---|
| Frontend | `http://localhost:3000` — up |
| Backend API | `http://localhost:8070` — up |
| Database | PostgreSQL `127.0.0.1:54426`, container `supabase_db_carbon_ledger`, database `carbontally_demo_local` |
| Auth | Supabase Auth (local) — demo identities resolved via the documented local demo credential mechanism |
| Storage | Local bucket `documents` — 46 objects, 607,014 bytes total |
| Demo identity manifest | `tools/seed_investor_demo/DEMO_IDENTITIES.md` (1,185 identities) |

Connection password was obtained only as an environment value (`docker exec … printenv POSTGRES_PASSWORD`) and **never printed, logged or stored** (§70, §78).

---

## 3. Git state and read-only compliance `[RECONSTRUCTED]`

- `git rev-parse HEAD` → `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`
- `git branch --show-current` → `p8-release-reconciled`
- `git status --porcelain | wc -l` → **160** (measured *before* this report was created; all pre-existing, unrelated working-tree state preserved, none reverted, none absorbed — §70, §71)
- `docs/architecture/CT-PRODUCT-REALITY-AUDIT-01.md` did **not** exist before this session (verified by `ls`).
- **Re-verified at close of session**: HEAD `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`, branch `p8-release-reconciled`, 42 modified tracked files — *all* pre-existing; `git status --porcelain -- docs/architecture/CT-PRODUCT-REALITY-AUDIT-01.md` → `??` (new, untracked) and no other path was written by this audit.
- **Caveat carried forward**: some cited files have uncommitted local modifications, so citations reflect the **working tree**. This is material for one finding — the FIN-06 entitlement sentence (FIND-9.11) is working-tree text while its equivalent rule *is* committed in `backend/domain/manual_processing.py`. Full list in **Appendix C.3**.

**Compliance verdict: COMPLIANT.** The only artefact added by this audit is this report file. No `.env`, credential, token, JWT, password or signed URL appears anywhere in this report or in the capture files (§70, §78).

---

## 4. Method and evidence artefacts `[RECONSTRUCTED]`

| Artefact | Contents |
|---|---|
| `/tmp/aud_probe5.py`, `/tmp/aud_probe5.txt`, `/tmp/p5_matrix.txt` | Persona × endpoint GET matrix — **final scope 10 personas × 46 endpoints = 460 probes** (an earlier 30-endpoint pass was extended to 46) |
| `/tmp/aud_p5_summarise.py`, `/tmp/p5_summary.txt` | Per-endpoint status + backend `detail` message per persona |
| `/tmp/aud_dbq1.sh` … `/tmp/aud_dbq10.sh` (+ `.txt`) | Read-only database evidence scripts and outputs |
| `/tmp/aud_s9.txt`, `/tmp/aud_final_a.txt` … `/tmp/aud_final_j.txt` | Handover §9 extraction, legacy-terminology grep, staff-role matrix, tab-gating, multi-select and consultant-upload evidence |
| `/tmp/roles.txt`, `/tmp/roles2.txt`, `/tmp/mig2.txt` | `staff_roles` permissions, staff-profile/role join, role `updated_at` clustering (the §14 root-cause evidence) |
| `/tmp/g1.txt`, `/tmp/g3.txt`, `/tmp/g4.txt`, `/tmp/g5.txt`, `/tmp/g7.txt` | Permission-vocabulary greps across `backend/`, `frontend/src/`, `supabase/migrations/`, `tools/` |
| `/tmp/q17.txt`, `/tmp/q17b.txt` | `document_processing_queue` status distribution and full column/constraint read (§17) |
| `/tmp/cnt2.txt`, `/tmp/git.txt`, `/tmp/git2.txt` | Environment population counts; Git state; FIN-06 working-tree-vs-HEAD check (Appendix C) |

**Baseline verification (recorded earlier in this same audit session):** 14/14 identity contexts resolved, 30/30 baseline probe endpoints returned an HTTP response (no transport failures) — the pass was subsequently extended to the **46-endpoint** matrix in §8/Appendix A, 46/46 responding — and 18/18 isolation probes behaved as expected. This establishes that the matrix below reflects real authorization decisions rather than timeouts or routing errors.

**Evidence hygiene.** Deny messages were captured verbatim from the API (`detail` field). Verbatim deny text is reproduced below because it is the primary artefact distinguishing *"not authenticated"*, *"not staff"*, *"staff lacks permission X"*, and *"not authorised for this entity"* — four very different product realities.

---

## 5. Persona inventory `[RECONSTRUCTED]`

Ten representative identities were probed. All are real rows in `staff_profiles` / `users` / membership tables of the local demo stack.

| ID | Identity (email) | Kind | Role / relationship |
|---|---|---|---|
| P01 | `platform.admin@demo-lab.carbontally.local` | Internal staff | `admin` role (`is_superuser`, `is_staff_admin`) |
| P02 | `operator@demo-lab.carbontally.local` | Internal staff | `operator` role (`can_process`) |
| P03 | `pe.manager@demo-lab.carbontally.local` | PE staff | `pe_manager` @ Processing Entity Alpha |
| P04 | `pe.beta.manager@demo-lab.carbontally.local` | PE staff | `pe_manager` @ Processing Entity Beta |
| P05 | `owner.a@demo-lab.carbontally.local` | Customer | Owner, ORG_A |
| P06 | `viewer.a@demo-lab.carbontally.local` | Customer | Viewer, ORG_A |
| P07 | `consultant.owner@demo-lab.carbontally.local` | Consultant | Consultant firm owner |
| P08 | `consultant.member@demo-lab.carbontally.local` | Consultant | Consultant team member |
| P09 | `owner.clienta@demo-lab.carbontally.local` | Client | Owner, CLIENT_ORG_A (consultant-managed) |
| P10 | `owner.clientb@demo-lab.carbontally.local` | Client | Owner, CLIENT_ORG_B |

**Fixture identifiers used consistently across runtime and database evidence**

| Fixture | UUID |
|---|---|
| ORG_A | `3fd0f325-16a1-5b53-8fb8-27929cf218fa` |
| CLIENT_ORG_A | `02b38744-27fe-5062-8f36-9af7a726eb4c` |
| ENGAGEMENT_A | `09501808-17e2-5cdc-a128-486f41a997b3` |
| PE Alpha | `f8c4f11e-720b-5f0d-b8d6-43f9e5170880` |
| PE Beta | `8ab93340-51ff-56cc-ad29-49a20aace8ac` |

---

## 6. Staff authority reality (runtime, not documentation) `[RECONSTRUCTED]`

`staff_roles.permissions` JSONB, read directly from the database (`DB` evidence):

| Role | Permissions actually held |
|---|---|
| `admin` | `is_superuser`, `is_staff_admin`, `can_review`, `can_manage_staff`, `can_manage_organizations`, `demo_lab` |
| `operator` | `can_process`, `demo_lab` |
| `pe_manager` | `can_process`, `can_manage_team`, `demo_lab` |

**Permissions held by *no* role in the local demo stack:**

| Permission | Consequence |
|---|---|
| `can_view_all` | The Dashboard / Operational health / platform-reporting surface is unreachable by **every** staff identity (PR-01) |
| `can_qc` | `/api/v3/ops/qc/ct-queue` is unreachable by **every** staff identity (PR-02) |
| `can_manage_billing` | The Operations **Commercial** tab renders for nobody (PR-03) |
| `can_manage_backups` | Backups tab renders for nobody (INFO — expected in a local stack) |

Staff profiles observed: 4 (`admin`, `operator`, `pe_manager` × 2 entities). Only 2 staff profiles carry an `entity_id` (i.e. PE staff).

**Structural consequence.** The single staff identity that can reach *manual-processing governance* (`can_manage_organizations` → admin) **cannot** reach the operator queue, the data-entry workspace, the PE workspaces, the ops dashboard, or the CT QC queue. The identity that *can* process (`operator`) cannot reach manual-processing governance or the staff roster. In this demo stack **no single login can follow the full `subscription → … → reporting` journey**, which is itself a product-reality finding (PR-04).

---

## 7. Baseline verification results `[RECONSTRUCTED]`

| Check | Result |
|---|---|
| Identity/context resolution | 14 / 14 contexts resolved |
| Probe endpoints responding (any HTTP status, no transport error) | 30 / 30 in the baseline pass; **46 / 46** in the final matrix (Appendix A) |
| Isolation probes behaving as expected (deny where deny is required) | 18 / 18 |
| Unexpected ALLOW (security violations) observed | **0** |

No unexpected `ALLOW` was found. Per `AGENTS.md` §45, any unexpected allow would have been a serious security finding; none occurred in this matrix.

---

## 8. Persona × endpoint matrix (runtime) `[RECONSTRUCTED]`

46 endpoints × 10 personas were probed live (GET only). The full grid is **Appendix A**. Per-persona distribution:

| Persona | 200 | 403 | 422 (validation reached ⇒ authz passed) | non-403 total |
|---|---|---|---|---|
| P01 `platform_admin` | 19 | 22 | 5 | 24 |
| P02 `internal_operator` | 5 | 36 | 5 | 10 |
| P03 `pe_manager` (Alpha) | 8 | 34 | 4 | 12 |
| P04 `pe_beta_manager` (Beta) | 6 | 36 | 4 | 10 |
| P05 `org_a_owner` | 6 | 34 | 6 | 12 |
| P06 `org_a_viewer` | 6 | 34 | 6 | 12 |
| P07 `consultant_owner` | 3 | 38 | 5 | 8 |
| P08 `consultant_member` | 3 | 38 | 5 | 8 |
| P09 `client_a_owner` | 3 | 37 | 6 | 9 |
| P10 `client_b_owner` | 3 | 37 | 6 | 9 |

**Observations that matter for product reality**

1. **Two deny vocabularies, cleanly separated** (this is good design and it is enforced):
   - non-staff identity → `Staff access required (active staff profile)`;
   - PE staff reaching an internal-only surface → `CarbonTally internal staff access required`;
   - insufficient staff permission → `staff lacks permission: <permission>`.
   Differentiating these three means the backend authorization model is explicit rather than accidental.
2. **PE isolation is real and enforced at runtime.** P03 (`pe_manager`@Alpha) receives `200` on `/api/v3/ops/entities/{PE-Alpha}/dashboard` and `/extraction/batches`, while P04 (`pe_beta_manager`@Beta) receives `403 — "Staff member is not authorized for this processing entity"` for the same Alpha URLs. PE A ↛ PE B is confirmed.
3. **PE staff are structurally barred from customer and internal contexts**: `403 — "Processing Entity staff may not act for a customer organization directly"` (`/api/v3/accounting/context`) and `403 — "Processing Entity staff cannot hold internal admin authority"` (`/api/v3/settings/retention`).
4. **`/api/v3/ops/staff-roles` is reachable by all four staff identities, including both PE managers** (`200`), while every other staff surface is permission-gated. See PR-05.
5. **Internal-operations surfaces are unreachable by customers, consultants and clients** — all `403`. No leakage.
6. **`/api/v3/settings/analytics` returns `200` for all ten personas**, including unauthenticated-equivalent contexts and clients (PR-06).
7. **`can_process` and `can_review` are held by different identities** (P02 vs P01), and `admin` holds `can_review` but **not** `can_process`; the consequence of this split is the headline assignment defect FIND-9.13 (see §11).

---

## 9. Surface inventory — what each persona can actually reach `[RECONSTRUCTED]`

| Persona | Reaches (UI entry points established from source + runtime) | Cannot reach |
|---|---|---|
| P01 `platform_admin` | `/ops` (Organizations, Staff, Audit, Review, Commercial Coverage, Manual Processing, … tabs limited by permissions), `/ops?tab=manual-processing-coverage`, extraction batches (denied), PE workspace (denied) | Operator queue (`can_process`), ops Dashboard/Operational health/platform reporting (`can_view_all`), CT QC queue (`can_qc`), Backups (`can_manage_backups`), PE workspace |
| P02 `internal_operator` | `/ops` (operator queue only), `/ops/queues/operator`, processing workspace | Everything governed by `can_review`, `can_view_all`, `can_manage_staff`, `can_manage_organizations` |
| P03 / P04 PE staff | `/ops/entities/{own}/dashboard`, PE workspace (`/api/v3/pe/*`), extraction batches for own entity | Any other entity (`Staff member is not authorized for this processing entity`), internal ops, customer orgs |
| P05 / P06 customer | `/manual-processing` (customer upload path), org profile, members, org manual-processing state, billing, emissions, documents, settings | All ops surfaces (403), consultant surfaces (403) |
| P07 / P08 consultant | `/consultant`, `/consultant?view=coverage`, `/api/v3/consultants/me`, `/consultants/me/manual-processing/coverage`, `/consultants/clients/{id}/…` for granted clients | Ops surfaces, customer org shells for ORG_A (403), PE surfaces |
| P09 client (consultant-managed) | Own org shell (`CLIENT_ORG_A`), billing, emissions, documents, accounting context | ORG_A (403 — correct), consultant firm surfaces (403) |
| P10 client (direct) | Own org shell | ORG_A (403 — correct) |

**Notable gap.** The customer-facing manual-processing **entry point is `/manual-processing`** with a distinct staff/admin entry at `/ops?tab=manual-processing-coverage` (gated `can_manage_organizations`) and a consultant entry at `/consultant?view=coverage` (`requireConsultant`). Three separate surfaces for one product capability. This is consistent with the frozen role-separation architecture, but it means the *capability* has no single owner view (see §21 and PR-04).

---

## 10. Data reality snapshot (read-only SQL) `[RECONSTRUCTED]`

All values below were read `SELECT`-only from `carbontally_demo_local`. This section answers a question no UI screenshot can: **is the workflow backed by real rows?**

| Domain | Observed | Interpretation |
|---|---|---|
| Organisations | 11 | Demo stack includes 11 orgs, not the 50 of the full investor manifest → this is a *reduced* local dataset |
| `document_processing_queue` | 46 rows | Real durable queue records exist |
| → stage distribution | `blocked` 44, `review` 2 | **The queue is 96% blocked** |
| → attempt_count | 0 ×15, 1 ×31 | Retry machinery exists and has actually been exercised |
| → pipeline versions | `v3-auto-1.2` 29, `v3-auto-1.1` 17 | Mixed pipeline versions in one queue |
| → org distribution | ORG_A 38, CLIENT_ORG_A 5, org 2, org 1 | Multi-tenant queue, correctly attributed |
| Durable-state columns | `stage`, `attempt_count`, `max_attempts`, `last_error`, `locked_at`, `lock_token`, `calculated_at`, `review_ready_at`, `notified_at`, `source_item_id`, `calculation_snapshot_id` all non-null where expected (stage 46/46, attempts 46/46, source_item_id 46/46; last_error 0, locked_at 0, calculated_at 2, review_ready_at 2, notified_at 2) | The durable automatic-processing contract in `AGENTS.md` §19 is materially implemented |
| `organization_files` | 60 rows | Real V3 document store |
| `storage.objects` (bucket `documents`) | 46 objects / 607,014 bytes | **60 records vs 46 objects — 14 records have no backing object** (PR-07) |
| `customer_documents` (legacy) | 0 rows; table exists | Legacy document path is empty; `documents` table does not exist |
| `emissions_logs` | 34 rows, 34/34 with `snapshot_id`, `organization_id`, `calculated_kg_co2e` | Emissions rows carry provenance (note: the authoritative quantity column is `calculated_kg_co2e`; there is no `emissions_kg_co2e`) |
| `calculation_snapshots` | Provenance columns present: `factor_id`, `factor_source`, `factor_kind`, `customer_factor_id`, `source_item_id`, `source_file`, `source_page`, `source_line_item_id`, `request_id`, `content_hash`, `algorithm_version`, `superseded_by_snapshot_id` | The §17 provenance chain is *structurally* supported; per-column fill rates were **not** measured → `UNVERIFIED` |
| `report_versions` | `DRAFT` 3, `APPROVED` 1 | Report versioning is real and has an approved artefact |
| `report_generation_queue` | `completed` 4 | Report generation has actually run |
| `conversations` / `messages` | 8 / 10; participants table present; `conversation_kind` + `processing_entity_id` columns present | Messaging is real; **whether any PE↔CarbonTally conversation exists was not measured** → `UNVERIFIED` |
| `audit_trail` | 458 rows | Real audit history |
| `activity_feed` / `domain_events` | 0 / 0 | These tables exist but are unused |
| `manual_extraction_batches` / `items` | 4 / 46 | Manual processing path is exercised |
| `work_item_assignments` | 12 | Assignment data is real (so the FITL-LOAD FAILURE in FIND-9.13 is a *read-path* problem, not an empty table) |
| `manual_review_queue` | 0 | Legacy manual-review queue is empty — the V3 queue is `document_processing_queue` |
| `manual_processing_grants` | **1 row** — scope `organization` = `aa6cde4e-…` ("MP-FX Client — Direct + Sponsored"), `enabled=true`, reason `CT-MP-SUB-004 PD-5 QA fixture`, `updated_at` 2026-10-04 18:02Z | Exactly **1 of 11** organisations holds an MP grant, and it is an MP-FX *fixture* organisation. **No Demo Lab persona organisation holds one**, which is the data behind the "no coverage / no entitlement" empty states. *(Re-measured 2026-10-05 — an earlier draft of this table recorded "0 rows"; see the §11 correction note.)* |
| `manual_processing_processors` | 1 | One processor configured (a Processing Entity) |
| `consultant_mp_allocations` | 13 | Consultant coverage allocations are real |
| `billing_plans` | 23 rows; `billing_mode`, `assisted_processing_available`, `managed_processing_available` columns **still present** | Two commercial vocabularies coexist **at schema level**, and the legacy one is **load-bearing**: Manual Processing entitlement is decided by `features.manual_processing.enabled` **or** `assisted_processing_available` (`docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md:43-50`) — see FIND-9.11 evidence 7 |
| `customer_subscriptions` / `billing_orders` | 4 / 0 | Subscriptions exist; no orders |
| `billing_credits`, `credit_ledger` | **do not exist** | Any UI or code referencing a credit ledger is referencing something absent |
| `notifications` | no `kind` column (columns include `id`, `link`, …) | Notification categorisation is not modelled as `kind`, contrary to what an audit expecting "notification kinds" would predict |
| Processing Entities | 2 (`Demo Lab Processing Entity Alpha`, `…Beta`), `pe_users` = 2 | PE model is real and minimal |





---

## 11. PO manual-QA findings (handover §9) — independently re-verified `[RECONSTRUCTED]`

Each PO finding is re-tested against **current** runtime, current source, or current database. A PO observation is **not** accepted merely because the PO stated it (§80), and is **not** dismissed because the audit could not reproduce it — unreproducible claims are marked `UNVERIFIED`, never `REFUTED` without evidence.
### 11.0 Correction note — re-measured Demo Lab Manual Processing rows (2026-10-05)

Four statements earlier in this report (in `FIND-9.4`, `FIND-9.7` evidence and §10) originally asserted that the Demo Lab Manual Processing tables are **empty** (`manual_processing_grants = 0`). That assertion was taken from an earlier, narrower query and is **stale**. It was re-measured on 2026-10-05 with read-only SQL against `carbontally_demo_local` (artefacts `/tmp/aud_dbq15.txt`, `/tmp/aud_dbq16.txt`, `/tmp/aud_dbq17.txt`; scripts `/tmp/aud_dbq15.sh`–`/tmp/aud_dbq17.sh`):

| Table | Re-measured truth | Scope |
|---|---|---|
| `manual_processing_grants` | **1 row**, `enabled=true`, reason `CT-MP-SUB-004 PD-5 QA fixture`, `updated_at` 2026-10-04 18:02Z | scope `organization` = `aa6cde4e-…` ("MP-FX Client — Direct + Sponsored") |
| `consultant_mp_allocations` | **13 rows** — 12 `released` + 1 `active` | all belong to consultant firm `1ee24d1d-…` ("MP-FX Consultancy — Selected Coverage") |
| `manual_processing_processors` | **1 row** | a single Processing Entity |

**Effect on the findings.** None of `FIND-9.1`–`FIND-9.7` is withdrawn; the correction *re-classifies the evidence* rather than the conclusion. The correct statement is not "the tables are empty" but "**the tables contain a single Demo Lab fixture cluster owned by organisations and a consulting firm that no audited persona belongs to**". Consequently "nothing enabled / no coverage" remains the observed state **for every Demo Lab persona**, while the underlying feature is demonstrably exercised by at least one fixture (§5.5 of the handover). Any future audit must not quote the zero-row claim.



### FIND-9.1 — Manual Processing configuration is not understandable

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` |
| **Evidence class** | `CODE` |
| **Severity** | `MEDIUM` |
| **Classification** | `UX DEFECT` |

**Evidence.** The literal phrase the PO rejected is rendered as the *heading* of a tab in the internal operations workspace:

- `frontend/src/v3/ops/ManualProcessingTab.jsx:123` → `Manual processing — subscription to routing`

The same file then renders three dense diagnostic sentences as body copy about entitlement, processor configuration and routing outcome (`:29`, `:31`, `:33`). The tab label itself is `Manual processing coverage` (`:259`).

**Root cause.** An internal, engineering-shaped mental model ("a customer's subscription is pushed through governance to a routing outcome") has been surfaced verbatim as product copy. The underlying business facts are real (§10: `billing_plans` carries the entitlement columns, `manual_processing_processors` has 1 row, `consultant_mp_allocations` has 13 rows), so the defect is presentational, not substantive.

**Impact.** An internal operator must reverse-engineer a backend pipeline to answer "is this customer enabled for manual processing, and who does the work?" This is the same class of defect `AGENTS.md` §75/§76 defines as a product-quality failure.

**Recommendation (non-binding).** Replace the heading with a business question ("Manual processing for this customer"), lead with a one-line status sentence (Enabled / Not enabled / Enabled but nothing can pick up the work), and demote pipeline vocabulary to a collapsible *Technical details* region.

---

### FIND-9.2 — Subscription, entitlement, coverage, governance and routing are not clearly separated

| Field | Value |
|---|---|
| **Status** | `PARTIALLY CONFIRMED` — the concepts are *implemented* and *separated in the backend*; they are not separated in the **user-facing journey** |
| **Evidence class** | `RUNTIME` + `CODE` + `DB` |
| **Severity** | `MEDIUM` |
| **Classification** | `CAPABILITY GAP` (product-design / PO DECISION REQUIRED for the journey definition) |

**Evidence (the six concepts exist as six distinct backend objects, not one blob):**

| Concept | Backing object observed |
|---|---|
| Subscription | `customer_subscriptions` (4 rows), `billing_plans` (23 rows) |
| Entitlement | `billing_plans.assisted_processing_available` / `managed_processing_available` / `included_credits` |
| Consultant coverage | `consultant_mp_allocations` (13 rows) |
| Governance / enablement | `manual_processing_grants` (1 row — one organisation, internally set, labelled `CT-MP-SUB-004 PD-5 QA fixture`) |
| Operational routing | `document_processing_queue` (46 rows; `blocked` 44) |
| PE assignment | `manual_processing_processors` (1 row), `work_item_assignments` (12 rows), 2 PE entities |

The **runtime** exposes these as separate endpoints (persona matrix, §8): commercial/entitlement surfaces for customers and admin, `/api/v3/admin/manual-processing/…` for internal governance, and `/api/v3/consultants/me/manual-processing/coverage` for consultants.

**Where the claim holds:** there is no single surface, and no single ordered journey, that walks a user from *subscription → entitlement → coverage → enablement → routing → processing*. The PO narrative in §9.2 describes exactly the journey the current UI does not draw. The journey in the handover is `[DOC]` and **not yet ratified** → `PO DECISION REQUIRED` for the canonical journey wording and owner.

**Impact.** Comprehension failure at the exact point where a paying customer or consultant first asks "what did I buy, and what happens now?"

---

### FIND-9.3 — Admin has no obvious business-facing way to enable Manual Processing

| Field | Value |
|---|---|
| **Status** | `PARTIALLY CONFIRMED` — a mechanism exists, but discoverability and the entitlement prerequisite make it non-obvious |
| **Evidence class** | `CODE` + `DB` |
| **Severity** | `MEDIUM` |
| **Classification** | `UX DEFECT` + `CAPABILITY GAP` |

**Evidence.**

1. An enablement control **does exist**: `ManualProcessingTab.jsx` contains enable/disable actions that change coverage state (it renders success copy such as "Manual Processing enabled." and failure copy such as "Processing Entity is configured — failures are NOT routed."), reached at `/ops?tab=manual-processing-coverage`.
2. The tab is gated by `can_manage_organizations` — in the current role fixture only **System Admin** and **Staff Admin** hold it (§6). So the capability is *role-restricted by design*, and must be: enabling a commercial service is a privileged operation (`AGENTS.md` §14).
3. The prerequisite is exposed only as body copy, not as an actionable next step: the tab states that the subscribed plan does not include Manual Processing when entitlement is absent.
4. `manual_processing_grants` holds a single row, and it belongs to an MP-FX fixture organisation — so for every Demo Lab persona the "no way to enable it" experience is also the *default* experience (re-measured 2026-10-05; §11 correction note).

**Root cause.** The control sits inside a diagnostics-shaped internal tab whose gating and vocabulary are invisible to the intended operator, and the entitlement decision upstream (plan configuration on the commercial surface) is disconnected from the enablement decision here.

**Recommendation.** Lead the tab with the business state and the single next action ("This customer's plan does not include manual processing → Change plan" / "Enabled → assign the team that will do the work"), not with pipeline outcome text. Whether the *customer* should also be able to request enablement is a **PO DECISION REQUIRED** (see FIND-9.2/9.7).

---

### FIND-9.4 — Commercial Coverage is currently too diagnostic/technical

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` |
| **Evidence class** | `CODE` |
| **Severity** | `MEDIUM` |
| **Classification** | `UX DEFECT` |

**Evidence.** `frontend/src/v3/ops/ManualProcessingCoverageTab.jsx` renders a raw state table. Verified source lines: a comment at `:115` acknowledges the operator is choosing an organisation while the field is a raw input; `:470-480` renders `Processing Entity` as `CONFIGURED`/`NONE`, then `Operational routing outcome` as `routing.processing_entity_id || routing.outcome || '—'`, then a `Consultant relationship` row printing `relationship.consultant_firm_id` and `` · grant ${relationship.consultant_client_id} ``.

So the operator's screen shows a firm UUID, a client UUID labelled "grant", a Processing Entity UUID, and a routing outcome string. Every item the PO listed (consultant firm ID, organisation UUID, relationship ID, grant ID, raw entitlement state, routing outcome) is present in the source.

**Root cause.** The tab is a projection of backend governance state with no presentation layer between the API payload and the DOM. Nothing in the file maps an ID to a human name before rendering.

**Recommendation.** Resolve names server-side or via lookup, render names as primary labels, and move IDs behind a *Technical details* disclosure (`AGENTS.md` §34 forbids displaying raw UUIDs where a human-readable relationship exists).

---

### FIND-9.5 — UUIDs should not be primary business labels

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` — and stronger than reported: UUIDs are *returned by the API as the only* actor/resource identifier |
| **Evidence class** | `RUNTIME` + `CODE` + `DB` |
| **Severity** | `MEDIUM` |
| **Classification** | `UX DEFECT` + backend `CAPABILITY GAP` |

**Evidence.**
1. `CODE` — the coverage tab renders raw `consultant_firm_id` / `consultant_client_id` / `processing_entity_id` as visible labels (FIND-9.4).
2. `RUNTIME` — read-only `GET /api/v3/ops/reporting/audit?limit=5` as System Admin returns rows whose only identity fields are raw UUIDs: `actor='52a55937-d0fd-4b4a-aa07-a8843ed6a5fa'`, `entity_type='organization_files'`, `entity_id='b1a9c75d-f07d-42f4-b7cb-5b678b51d9c4'`. There is **no** `actor_name`, `actor_email` or resource-name field in the payload (each probed as `None`).
3. `DB` — the audit table behind that endpoint stores `performed_by`, `table_name`, `record_id` only; the API maps them to `actor` / `entity_type` / `entity_id`. No denormalised human label exists to render.
4. `DB` — for system-generated events the convention is `performed_by = 00000000-0000-0000-0000-000000000000` (`factor_match:matched` 73, `automatic_processing:extracted` 35, `report:evidence_line_items_materialised` 25, `factor_match:ambiguous` 11, `calculation:completed` 6, `report:generated` 4 ⇒ ~154 of 458 rows, ~34%). Those rows therefore display a **null UUID** as the actor.

**Root cause.** Identity is modelled as a foreign key with no resolution/presentation contract. Because the information is absent from the API response, this **cannot be fixed in the frontend alone** — it is a backend payload/contract change, and should not be handed to a UI-only task.

---

### FIND-9.6 — Audit UI needs human-readable actor/resource resolution

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` |
| **Evidence class** | `RUNTIME` + `CODE` + `DB` |
| **Severity** | `MEDIUM` |
| **Classification** | `CAPABILITY GAP` (backend resolution layer) |

**Evidence.**
1. `CODE` — `frontend/src/v3/ops/AuditConsoleTab.jsx:95` defines the column `{ key: 'actor', header: 'Actor', accessor: 'actor', sortable: true }`; the actor filter dropdown (`:166-170`) is built from the distinct raw `e.actor` strings. The file's own header comment (`:4-5`) states the backend deliberately exposes "only actor/action/resource/timestamp/field names".
2. `RUNTIME` — the payload the console consumes contains raw UUIDs only (FIND-9.5 evidence 2).
3. `DB` — resolution data exists but is **split across three identity stores**. Of the **15 distinct audit actors**: `11` resolve to `auth.users.id`, only `4` resolve to `staff_profiles.user_id`, and `6` resolve to `organization_members.user_id`. The specific actor inspected (`52a55937-…`) exists in `auth.users` and `organization_members` but **not** in `staff_profiles` — i.e. it is a *customer* user, not a staff user.

**Root cause.** Audit attribution uses `auth.users.id` as the actor key while human identity lives in `staff_profiles` (staff), `organization_members` (customers) and consultant records. No existing single join covers all three, so the PO's preferred sentence ("Kira Walsh released Manual Processing coverage for Demo Lab Client A") is **not currently producible**.

**Impact.** Auditability itself is **not** reduced (raw IDs remain; `audit_trail` holds 458 rows of real history) — this is a human-auditability gap, exactly as the PO framed it.

**Recommendation.** Add a server-side actor/resource resolution contract (directory lookup or joined display fields) covering all three identity stores, retaining the raw ID alongside. Classify as a backend capability item, not a formatting task.

---

### FIND-9.7 — Consultant coverage UX is incomplete

| Field | Value |
|---|---|
| **Status** | `PARTIALLY CONFIRMED` |
| **Evidence class** | `CODE` + `RUNTIME` + `DB` |
| **Severity** | `MEDIUM` |
| **Classification** | `CAPABILITY GAP` + `PO DECISION REQUIRED` (who configures coverage) |

**Evidence.**
1. `RUNTIME` — `GET /api/v3/consultants/me/manual-processing/coverage` returns `200` for **both** consultant owner and consultant member (§8 matrix): the surface is reachable, so the PO's experience is a *state* problem, not an access problem.
2. `CODE` — the coverage view is **ID-driven**: `ManualProcessingCoverageTab.jsx:670` binds a manual consultant/firm-id text input (`onChange={(e) => setFirmId(e.target.value)}`), with allocation target and reason chosen from `select` controls at `:717-737`. A user is expected to type a firm identifier to configure coverage.
3. `DB` — coverage data is real but pre-provisioned and **fixture-scoped**: `consultant_mp_allocations` 13 rows (all belonging to firm `1ee24d1d-…`, "MP-FX Consultancy — Selected Coverage"; 12 `released`, 1 `active`), `manual_processing_grants` 1 row (organisation `aa6cde4e-…`, `enabled=true`), `manual_processing_processors` 1 row (a single Processing Entity). The three Demo Lab personas reach the surface, but the coverage data belongs to a **different firm** — so "no coverage / nothing enabled" is the observed state for every Demo Lab persona.

**Root cause.** Coverage is modelled as an internal-operations task (allocations created by an internal actor — see PR-10) while being *displayed* to consultants as if self-service. No consultant-owned action produces coverage from the firm's own subscription.

**PO DECISION REQUIRED.** Who creates consultant coverage — the consultant firm (self-service over all eligible clients or selected clients), or CarbonTally internal operations on the consultant's behalf? `AGENTS.md` §10/§11 makes consultants first-class operators but does not assign this specific authority. Implementation should not proceed until decided.

---

### FIND-9.8 — Consultant-managed clients should be full CarbonTally organisations

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` |
| **Evidence class** | `CODE` + `RUNTIME` + `DB` |
| **Severity** | `HIGH` (direction) / `PRODUCT GAP` (current state) |
| **Classification** | `PRODUCT GAP` + `PO DECISION REQUIRED` (ratification per handover §10) |

**PO claim (handover §9.8).** A consultant client should be a normal CarbonTally customer organisation; the difference is who manages it, the consultant-client relationship, and permissions — not a reduced "mini CarbonTally".

**Evidence.**
1. `CODE` — the full organisation product surface **already exists**, as the *customer administration hub*: `frontend/src/v3/admin/AdminPage.jsx` (file header: "CarbonTally V3 — Customer Administration hub … Navigation model (D18/R2)"). Its `TABS` are, in order: `Overview & Settings`, `Locations`, `Facilities & Assets`, `Vehicles`, `Suppliers`, `Members & Invitations`, `Custom Factors`, `Activity`, `Audit & evidence` (`adminOnly: true`), `Security`. This is almost verbatim the §9.8 expected list; the remainder (`Documents`, `Processing`, `Reports`/emissions, `Billing`) exist as customer surfaces in `frontend/src/v3/customer/` (`DocumentsPage.jsx`, `ProcessingPage.jsx`, `EmissionsPage.jsx`, `BillingPage.jsx`).
2. `CODE` — the consultant workspace contains **no organisation-administration surface at all**. `frontend/src/v3/consultant/` is exactly: `ConsultantPage.jsx`, `ConsultantItemPage.jsx`, `ConsultantTeamTab.jsx`, `ClientMessagingTab.jsx`, `ManualProcessingCoverageTab.jsx`, `NewCustomerView.jsx`, `WhiteLabelTab.jsx`. There is no Locations/Facilities/Assets/Vehicles/Suppliers/Members/Factors/Activity/Audit/Documents/Reports component and no route into `v3/admin`.
3. `CODE` — the hub binds to the **acting user's own membership**: `AdminPage.jsx` imports `resolveV3Membership` and `resolveV3Organization` and its loader calls `resolveV3Organization()`. A consultant is not a member of the client organisation, so the hub cannot address a client organisation even if it were rendered.
4. `RUNTIME` — a consultant is denied the client organisation's resources while the client's own owner is allowed them: `GET /api/v3/organizations/02b38744-…/profile`, `/members`, `/manual-processing` return **403** for `consultant_owner` and `consultant_member`, and **200** for `client_a_owner` (§8 rows 37–39). `GET /api/v3/documents` and `/emissions/dashboard` are **403 `Organization member access required`** for consultants.
5. `DB` — the client organisation is an ordinary `organizations` row (`CLIENT_ORG_A` `02b38744-…`) with an explicit relationship row (`ENGAGEMENT_A` `09501808-…`). The *relationship* is already modelled as data.

**Root cause.** The reduced-client experience is a **frontend + authorization-surface gap, not a data-model divergence**. The organisation model already supports the PO direction; what is missing is (a) a consultant-facing route that resolves an *authorised client organisation* instead of the actor's own membership, and (b) the server-side authorisation that would allow it.

**PO DECISION REQUIRED.** Handover §10 states that formal ratification is still required before implementation. The audit confirms the direction is *architecturally cheap* (no new organisation type, no new tenant abstraction — consistent with `AGENTS.md` §11 "Do NOT clone the organisation") but **must not** be implemented before ratification, because it materially widens consultant authority over client data.

---

### FIND-9.9 — Consultant client management permissions need explicit design

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` |
| **Evidence class** | `CODE` + `RUNTIME` |
| **Severity** | `HIGH` (`PERMISSION GAP`) |
| **Classification** | `PERMISSION GAP` + `PO DECISION REQUIRED` |

**Evidence.**
1. `RUNTIME` — the consultant's reachable capability set is **binary and work-item shaped**. A consultant owner/member gets `200` only on `GET /api/v3/consultants/me` and `GET /api/v3/consultants/me/manual-processing/coverage`; every organisation-scoped endpoint tested is `403` (§8 rows 35–39, 45–46).
2. `CODE` — the consultant item surface is *stage*-scoped, not organisation-scoped: `ConsultantPage.jsx:83-88` defines the consultant work filter as `All items`, `Extraction`, `Mapping`, `Validation`, `Calculation`, `Customer review`. The consultant operates documents/work items, not the client organisation.
3. `CODE` — consultant identity is a separate authorisation path: `backend/api/consultant_auth.py` (`requireConsultant`) is distinct from organisation membership, and client communication is its own surface (`ClientMessagingTab.jsx`).
4. `RUNTIME` — the sharpest evidence is the **inverse asymmetry** on the same resource: `client_a_owner` `200` vs `consultant_owner` `403` on `/organizations/{clientOrg}/profile|members|manual-processing`, even though `AGENTS.md` §10 says a consultant may "operate client workspaces".

**Root cause.** CarbonTally today has exactly two relationship-scoped operator models — *organisation membership* (customer) and *work-item stage access* (consultant) — and no capability matrix for "consultant acting as administrator of an authorised client organisation". No audited endpoint grants a consultant any org-mutating authority, and none offers one.

**PO DECISION REQUIRED.** The four-way split required by §9.9 (`consultant firm owner` / `consultant member` / `client owner-admin` / `client member`) is a **product authorisation decision**, not an implementation detail (`AGENTS.md` §62; handover §9.8 requires a decision record first). The audit recommends the decision explicitly answer, at minimum: may a consultant (a) edit client master data, (b) invite/remove client members, (c) approve client custom factors, (d) see client billing/subscription, and (e) do any of the above for *all* authorised clients or only *selected* clients (compare `FIND-9.7`).

---

### FIND-9.10 — Consultant batch / multi-document upload appears missing or incomplete

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` (code level) / `UNVERIFIED` (end-to-end) |
| **Evidence class** | `CODE` + `RUNTIME` |
| **Severity** | `HIGH` (`PRODUCT GAP`) |
| **Classification** | `PRODUCT GAP` (and, if intended, `BUG`) |

**PO claim (handover §9.10).** Consultants cannot upload multiple documents; consultant upload to a managed client should use the same underlying document pipeline as a direct customer. Both paths must be tested.

**Evidence.**
1. `CODE` — a targeted search for the HTML multi-select attribute across the consultant and customer workspaces returns **exactly one** hit: `frontend/src/v3/customer/UploadDocumentsPanel.jsx:276: multiple`. **No file in `frontend/src/v3/consultant/` contains `multiple`** — i.e. nothing in the consultant workspace offers a multi-document file input.
2. `CODE` — the consultant workspace has no upload panel component at all (component inventory in `FIND-9.8` evidence 2). Upload for direct customers is a dedicated customer surface (`frontend/src/v3/customer/UploadDocumentsPanel.jsx`).
3. `RUNTIME` — the consultant is denied the organisation document surface outright: `GET /api/v3/documents` → **403 `Organization member access required`** for `consultant_owner` and `consultant_member` (§8 row 46) — the same denial as for internal CarbonTally staff.
4. `CODE` — the *policy* layer is already shared and server-side: the operations settings copy states "The limits every upload path enforces server-side: per file, files per batch and total size per batch" (`SettingsTab.jsx:477`), and the enforcement module is `backend/api/upload_gate.py`. So the missing piece is **not** policy — it is (a) a consultant-side upload UI and (b) the consultant's organisation-scoped authorisation (see `FIND-9.8`/`FIND-9.9`).

**Root cause.** The consultant operating model was built around *processing already-uploaded work items* (stage filters, `ConsultantPage.jsx:83-88`), not around *ingesting documents on behalf of a managed client*. Multi-document upload for consultants therefore has no surface, no route and no organisation-scoped authorisation to build on. The PO's expectation ("same underlying pipeline") is technically achievable — the pipeline and upload gate are shared — but it depends on the `FIND-9.8`/`FIND-9.9` authorisation decisions.

**Explicitly not verified (honest limitation).** This audit is **read-only**; it did not execute any client→*upload* (write) path. The finding is therefore: *no multi-document control exists in the consultant workspace* (`CONFIRMED`, code) and *the consultant→client batch pipeline does not work* (`UNVERIFIED` — untested because the brief forbids writes). A follow-up **mutation-scoped QA fixture** (AGENTS.md §55: isolated, labelled, tracked, cleaned up) is required to close the end-to-end question.

---

### FIND-9.11 — Billing terminology contains legacy / conflicting concepts

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` |
| **Evidence class** | `SCHEMA` + `CODE` (backend + public frontend) |
| **Severity** | `MEDIUM` (`TERMINOLOGY PROBLEM`, product-facing) |
| **Classification** | `LEGACY/CONFLICTING FEATURE` + `TERMINOLOGY PROBLEM` + `PO DECISION REQUIRED` |

**PO claim (handover §9.11).** The Billing UI uses "Assisted Processing estimate" and "Managed Processing" while current product decisions use "Manual Processing". This must be fact-found before renaming or removing anything.

**Evidence — the two vocabularies are both live, in different layers.**

*Legacy vocabulary (Assisted / Managed Processing) — schema:*
1. `SCHEMA` — `billing_plans` (23 rows) still carries **both** boolean columns `assisted_processing_available` and `managed_processing_available`, alongside `billing_mode` and `features`; introduced by migrations `20260824020000_d37_0_billing_security_and_configurable_subscription.sql` and `20260824030000_d37_master_commercial_billing.sql`.

*Legacy vocabulary — live backend code (not vestigial):*
2. `CODE` — `backend/data/billing.py` reads and writes both flags (select list `:26-27`, hydration `:59-60`, insert `:156,167`, update `:208-209,232-233`).
3. `CODE` — the plan API exposes and accepts them: `backend/api/v3_commercial.py:120-121` (plan read), `:173-174` / `:193-194` (create/update models), `:365-366` (persist).
4. `CODE` — **live endpoints**: `backend/api/v3_billing.py:202` section header "Assisted Processing (estimate → approval → commercial order)" with the endpoint at `:212` ("Create a configurable-price Assisted Processing estimate for approval"), and `:260-279` "Managed Processing (common order foundation)" submitting a `"Managed Processing batch"` order into the shared `billing_orders` model; `backend/services/billing.py:569-588` still builds the "Assisted Processing — {complexity}" price-book line.

*Legacy vocabulary — live public marketing (highest product risk):*
5. `CODE` — `frontend/src/public/ServicesPage.jsx:74,84,97,111` sells "Assisted processing" and "Managed processing"; `frontend/src/public/PricingPage.jsx:31,118` advertises "Assisted and managed processing" and prices it "from £0.99 per unit"; `frontend/src/public/faqData.js:288-312` defines "Human-assisted processing" and describes Processing Entities as supplying it, `:424-436` defines both service tiers; `frontend/src/public/assistant/assistantKnowledge.js:190` teaches the public assistant the term.

*Current vocabulary (Manual Processing) — also live:*
6. `SCHEMA`/`RUNTIME`/`CODE` — `manual_processing_grants`, `consultant_mp_allocations`, `manual_processing_processors`; API families `/api/v3/admin/manual-processing/*` and `/api/v3/consultants/me/manual-processing/coverage`; surfaces `ops/ManualProcessingTab.jsx`, `ops/ManualProcessingCoverageTab.jsx`, `customer/ManualProcessingPage.jsx`; and `billing_plans.features` containing `manual_processing` on at least one plan (§10).
7. `CODE` **— the decisive evidence: the legacy flag is *load-bearing* for the current feature — and this is committed code, not a draft.** `backend/domain/manual_processing.py` (**TRACKED at HEAD, unmodified**) resolves Manual Processing entitlement from the existing commercial model and states the mapping in its own docstring (`:180-195`):

   ```
   customer_subscriptions (org-scoped, active lifecycle)
       -> plan_code (+ plan_version)
           -> billing_plans
               -> features.manual_processing.enabled   (explicit feature flag)
                  OR assisted_processing_available     (existing plan column)
   ```

   The code implements exactly that (`:234` `features.get("manual_processing")`; `:245` `assisted = bool(getattr(plan, "assisted_processing_available", False))`; `:248` `source="assisted_processing_available" if assisted else "none"`), and the source vocabulary is enumerated at `:109` and `:205`. The module also records the *product* meaning it attributes to the legacy column: *"the existing D37 plan column whose documented meaning ('CarbonTally automatically processes what it can and offers human processing for documents requiring additional work') is exactly this capability."* There are **27** references to the legacy flag across `backend/` (`data/billing.py`, `api/v3_commercial.py`, `services/billing.py`, domain resolver). The same rule is repeated in prose at `docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md:43-50` — **but that sentence is working-tree text, not committed** (see Appendix C); the code is the authoritative citation.

   The ratified Manual Processing decision therefore **depends on the "Assisted Processing" plan column as its entitlement trigger**, with unit tests explicitly asserting the legacy source (`backend/tests/unit/domain/test_manual_processing_routing.py:89` → `decision.source == "assisted_processing_available"`; and *"Legacy `assisted_processing_available` still grants DIRECT entitlement"*, `backend/tests/unit/domain/test_consultant_mp_coverage.py:260-265`). The two vocabularies are not merely parallel; they are **conflated inside the live, committed entitlement resolver**, so renaming or dropping `assisted_processing_available` would silently change who is entitled to Manual Processing — and would break those assertions.
8. `DOC` — a specification exists but is **draft-only**: `docs/Pricing/CARBONTALLY_ASSISTED_AND_MANAGED_PROCESSING_SPECIFICATION_V1(1).md` (status *"Product/commercial decision draft"*, dated 2026-08-23, marked *"Specification only — no implementation authorized by this document"*) defines **three** customer operating modes — *Self-Service Processing*, *Assisted Processing*, *Managed Processing* — all converging on the same data model. So Assisted/Managed are **planned commercial services** with a draft spec, **while** the *current* enabled manual-processing machinery implements a partially overlapping human-extraction path (`docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md:52-63`: manual-extraction batches/items, manual stage actions), and FIN-06 explicitly states *"Automatic processing … is not governed by FIN-06"*.

**Consequence.** The commercial data model currently carries **three parallel vocabularies for overlapping capability on the same table** (`billing_mode`, `features`, and the two legacy booleans), while the public website markets two of them and the internal surfaces use the third. This is exactly the `LEGACY/CONFLICTING FEATURE` case the brief asks to identify.

**Do not rename (explicit).** Per handover §9.11 and `AGENTS.md` §62, no rename or removal should occur until the product meaning is established. The decision record must state, per term, whether "Assisted Processing" and "Managed Processing" are (a) **aliases** of Manual Processing, (b) **separate commercial services** (human-processing tiers distinct from the manual-processing grants/coverage machinery), (c) **legacy/obsolete** (to be deprecated with a migration and public-copy change), or (d) a **different axis** (e.g. commercial delivery model vs operational routing).

**Conclusion — the hypothesis is now refined, not merely confirmed.** The evidence supports **(b) with a caveat**, and rules out (c):

- **(c) is ruled out.** Assisted/Managed are not dead strings. They are **(i)** a documented draft product specification with three ratified operating modes (evidence 8), **(ii)** live backend endpoints that create commercial orders (`v3_billing.py:212,260-279`), **(iii)** live public marketing and pricing copy on the website, and **(iv)** — decisively — **the fallback entitlement trigger for the current Manual Processing feature itself** (evidence 7). Removing them is not a copy edit; it is a commercial and entitlement change.
- **(b) is the working hypothesis, but the implementations overlap.** The draft spec (evidence 8) describes Assisted/Managed as the *customer-facing operating modes* (who does the work). The enabled machinery (`manual_processing_grants`, `manual_processing_processors`, coverage allocations) implements a *routing and entitlement* mechanism for a human path. The spec is explicitly **"Specification only — no implementation authorized"**, so there is no document establishing that the shipped grants/coverage tables *are* the Assisted/Managed implementation. `FIND-9.10` (no consultant batch upload; per-document manual only) is a concrete symptom of this gap: the spec's *Managed* mode implies batch submission, which does not exist.
- **(a) must not be assumed away.** Because `features.manual_processing.enabled` and `assisted_processing_available` are OR-ed in the same entitlement expression (evidence 7), the *runtime* already treats "Assisted Processing" as a grant of "Manual Processing" entitlement. Whether that is intended product semantics or an implementation shortcut is precisely the unresolved question.

**PO DECISION REQUIRED — the specific questions.** (1) Are Assisted/Managed Processing the same commercial services as Manual Processing, or separate tiers? (2) If separate, which plan flag grants which capability, and is the OR-fallback in `FIN-06 §0` intentional or an artefact? (3) Does *Self-Service* (the third spec mode) map to today's automatic pipeline? (4) Should the public website continue to sell Assisted/Managed while the internal control plane is named "Manual Processing"? Until (1)–(4) are answered, the three vocabularies must be **left intact** and no migration applied.

**Risk of inaction (why this is `HIGH`).** The public website prices a service ("from £0.99 per unit") whose internal counterpart is named differently, whose entitlement is derived from an ambiguously-named boolean, and whose *Managed* variant (batch submission) is not implemented. A customer buying "Managed Processing" today would be sold a capability the platform does not provide end-to-end — a commercial-reality gap, not a naming preference (`AGENTS.md` §73/§74 — a service is complete only when its business outcome works).

---

### FIND-9.12 — Empty states often lack next-step guidance

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` |
| **Evidence class** | `CODE` + `RUNTIME` |
| **Severity** | `MEDIUM` (`UX DEFECT`) |
| **Classification** | `UX DEFECT` |

**PO claim (handover §9.12).** Empty states (no active subscription / no consultant coverage / no Manual Processing entitlement / no processing state) should answer: (1) why is this empty, (2) what can I do, (3) who can change it, (4) what happens next.

**Evidence — the condition is stated, the guidance is absent.**
1. `CODE` — *three different presentations of one condition* ("no consultant coverage"): `frontend/src/v3/ops/ManualProcessingCoverageTab.jsx:41` renders a bare sentence ("No consultant coverage configured for this organization."); `:289` renders `<EmptyState title="No coverage configured">`; `frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx:194` renders `<EmptyState title="No consultant coverage active">`. Two workspaces, three treatments, one state.
2. `CODE` — the shared copy (`consultant/ManualProcessingCoverageTab.jsx:34-42`) reads: *"No Manual Processing consultant coverage is currently active."* / *"Your firm's subscription coverage will appear here when configured."* It answers (1) partially and (4) vaguely, but **never answers (2) what can I do or (3) who can change it** — and its wording presumes a subscription state that the same page does not evidence.
3. `CODE` — the entitlement/no-processing case is description-only: `ops/ManualProcessingTab.jsx:31` — *"Manual Processing is not enabled for this scope. Extraction failures follow the normal path."* There is no action, no owner and no route for the reader to change the scope.
4. `CODE` — the "no active subscription" case is **not an empty state at all**: `frontend/src/v3/customer/BillingPage.jsx:125` renders `<p>{plan.name || 'No active subscription'}</p>` — an inline fallback string substituted for a plan name. No reason, no action, no owner, no next step (PO example 1).
5. `CODE` — the pattern is systemic, not isolated: `frontend/src/v3` contains **21** `length === 0 &&` conditions and **31** `className="muted"` renderings, i.e. ad-hoc inline text is the default treatment and the guidance-bearing `EmptyState` component is used only where it was retrofitted.
6. `RUNTIME` — the audited personas live in exactly these states: no audited persona's Manual Processing entitlement or consultant coverage is populated (§10 and §11.0 — the only grant/allocation rows belong to other organisations/firms), so this empty-state quality is the *first* thing every persona sees on those surfaces.

**Root cause.** There is a design-system `EmptyState` component (`frontend/src/v3/components/ui`) plus an older ad-hoc convention (`className="muted"` + inline `<p>`), and no product rule that an empty state must name the actor who can change it. The brief's four questions are a **content standard**, not a component issue.

**Recommendation (non-binding; do not implement during fact-find).** Adopt the four-question standard for the specific states the PO listed, and route the visual treatment through D21 rather than adding new one-off copy — `AGENTS.md` §40 forbids page-specific visual systems.

---

### FIND-9.13 — Assignment page has an authorization/functional defect

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` |
| **Evidence class** | `CODE` + `RUNTIME` |
| **Severity** | `HIGH` (`BUG`) |
| **Classification** | `BUG` + `PERMISSION GAP` |

**PO observation (handover §9.13).** An Admin Assignment screen displayed a failure such as *"Failed to load / You don't have permission to access this area."* It was to be code-traced before classification.

**Code trace — the exact provenance of both the tab and the error copy.**
1. `CODE` — **Where the error text comes from**: `frontend/src/v3/api.js:26` returns the constant string `"You don't have permission to access this area."` as the user-facing message for denied V3 API calls. The PO's wording is therefore an **HTTP 403 surfaced by `v3Fetch`**, not a routing failure — the screen loaded and its data call was denied.
2. `CODE` — **Which screen**: the *Assignments* tab is `frontend/src/v3/ops/OpsAssignmentsTab.jsx` ("WS4 Gate 3 — Operations item-level processing assignment surface"), registered in `frontend/src/v3/ops/OperationsPage.jsx:89-93`.
3. `CODE` — **Visibility gate** (`OperationsPage.jsx:92-93`): the tab is appended when `p.can_process || p.can_review`, with the comment "for internal staff with process/review capability".
4. `CODE` — **Data dependencies** (`OpsAssignmentsTab.jsx:21-33`): the tab's directory loads through `getOperatorQueue` → `/api/v3/ops/queues/operator`; `getEntityExtractionBatches` → `/api/v3/ops/entities/{entityId}/extraction/batches`; `listOpsStaff` → `/api/v3/ops/staff`; `listProcessingEntities` → `/api/v3/ops/entities`; `getOpsBatchItems` → `/api/v3/ops/batches/{id}/items`.

**Runtime result — the tab is unloadable for *every* persona.**
5. `RUNTIME` — for **`platform_admin`** (the PO's "Admin"): `GET /api/v3/ops/staff` → **200** (§8 row 3) but `GET /api/v3/ops/queues/operator` → **403** (row 7) and `/api/v3/ops/entities/{PE}/extraction/batches` → **403** (row 17). The tab is *shown* (because `platform_admin` passes `/api/v3/ops/queues/review` → 200, row 8, so `can_review` is true) and then **fails its own directory call with 403 → the PO's exact message**.
6. `RUNTIME` — for **`internal_operator`**: the two endpoints above are **200** (rows 7, 17) but `GET /api/v3/ops/staff` is **403** (row 3 — staff roster is `platform_admin`-only). The tab is shown (`can_process` true) and fails on the staff directory.
7. `RUNTIME` — the two permission sets are **disjoint**: no persona in the matrix holds both the operator-queue authority (`200` only for `internal_operator`) and the staff-roster authority (`200` only for `platform_admin`). Every other persona is `403` on all four. Therefore **no login in the audited population can successfully load the Assignments tab** — it is structurally unreachable in a *working* state, not merely gated.
8. `RUNTIME` — the failing dependency is not one of the two endpoints the probe could not reach: `/api/v3/ops/entities` and `/api/v3/ops/batches/{id}/items` were **not probed** and remain `UNKNOWN`; the finding stands on the two endpoints that **were** probed.

**Verdict against the PO's four candidate explanations (handover §9.13).**
| Candidate | Verdict | Why |
|---|---|---|
| Intentional security boundary | **Rejected** | The nav gate *offers* the tab to users who cannot load it; a genuine boundary would not advertise the surface. |
| Incorrect Admin authorisation | **ACCEPTED** | The visibility gate (`can_process \|\| can_review`) and the data dependencies (`can_view_all`-class operator queue + `platform_admin`-only staff roster) use **disjoint** permission families. |
| Broken route | **Rejected** | `OperationsPage.jsx:89-93` registers the tab and the route resolves; the failure is the API denial, not navigation. |
| Stale runtime evidence | **Rejected** | Reproduced from **current** source + **current** runtime on 2026-10-05. |

**Root cause.** The Assignments surface was built (WS4 Gate 3) against a permission set that **no role in the current V3 role matrix actually holds concurrently**. It depends on `can_view_all`-class operational scope, which is unreachable by every staff identity (`PR-01`), while being gated by `can_process || can_review`. The UI therefore promises a capability the backend will not serve.

**Not a PO decision.** This is an implementation defect (the brief's `BUG`), not a business-policy question — the *intended* audience of the Assignments tab is documented in the code comment ("internal staff with process/review capability"), so the disagreement is between the code's own stated intent and its dependencies. Fixing it does require choosing one of two consistent wirings (operator-facing directory vs admin-facing directory), which the implementing agent should raise with the PO before changing authorisation. **No change made during this fact-find.**

---

### FIND-9.14 — Settings usability / placement (platform-global settings in an operational workspace)

| Field | Value |
|---|---|
| **Status** | `CONFIRMED` |
| **Evidence class** | `CODE` + `RUNTIME` |
| **Severity** | `MEDIUM` (`UX DEFECT` + `SECURITY/ARCHITECTURE SMELL`) |
| **Classification** | `UX DEFECT` + `PARITY/PLACEMENT GAP` |

**PO observation (handover §9.14).** Settings should be verified for: existence, reachability, permission gating, whether "account-level" settings are actually organisation-level, whether they sit in the right place, whether related settings are grouped, and whether state is communicated.

**Evidence — existence, reachability, grouping.**
1. `CODE` — settings **exist and are grouped** as four independent `v3-card` sections inside a single 699-line component (`frontend/src/v3/ops/SettingsTab.jsx`), reached as a tab of the Operations workspace (`frontend/src/v3/ops/OperationsPage.jsx`): **Retention** (`audit_log_retention_days`, `data_retention_days`, `document_retention_days`, `backup_retention_days` — `:42-45`), **Analytics & Integrations (GA4)**, **Upload policy** (`:53-65`), and **Email delivery provider + sender** (`PROVIDER_LABELS` / `DEFAULT_PROVIDER_FORM`, `:68-80`).
2. `CODE` — the sections load through **five separate effects** (`:135` retention, `:148` analytics, `:161` upload policy, `:177-178` email provider + sender) and are explicitly fault-isolated ("an analytics problem can never block the retention configuration surface", `:92-93`) — so unrelated settings **do not** block one another. This part of the PO's concern is **not** a defect.
3. `UX` — but there is **no sub-navigation**: all four domains, with all their fields, confirmations and validation, are stacked on one page with no tabs, anchors or search. That is the mechanical cause of the PO's "settings are hard to find / appear buried" observation, and it is the same "long stacked page" pattern as `FIND-9.1`/§38.

**Evidence — the placement question is worse than "account vs organisation".**
4. `CODE` — **every one of these settings is platform-global, not organisation-scoped**: `getRetentionSettings` → `GET /api/v3/settings/retention` (`api.js:2108`), analytics → `/api/v3/settings/analytics` (`:2120`), upload policy → `/api/v3/settings/upload-policy` (`:2132`), notification sender → `/api/v3/settings/notification-sender` (`:2146`), email provider → `/api/v3/settings/email-provider` (`:2163`). **No path carries an organisation id** — these are singleton platform configuration endpoints.
5. `CODE` — yet they are presented inside the **Operations workspace**, a tab sitting beside operator/reviewer queues (`OperationsPage.jsx`), which `AGENTS.md` §37/§76 treats as a *contextual operational* surface (where am I, which organisation am I working on). In the UI the reader cannot tell whether they are changing a platform-wide default or something belonging to the organisation whose name is on the header.
6. `RUNTIME` — placement is inconsistent across the codebase: the same analytics configuration is also reachable at a **separate** `/settings/analytics` route which, per `PR-06`, is open to *all* staff rather than being restricted with the rest of the settings surface. One configuration concept, two entrances, two different permission postures.
7. `ARCHITECTURE` — `AGENTS.md` §31 requires privileged system administration to live in a dedicated admin control plane, explicitly *not* mixed with operational navigation; and §42 requires retention to be "managed through the appropriate Settings/Admin control plane". Today the platform-global settings sit inside the operator workspace.

**Root cause.** Settings grew inside the Operations workspace as a convenience tab (`SettingsTab` as one `OperationsPage` tab) while the underlying endpoints remained platform singletons. No one has decided whether these are **platform** settings (→ admin control plane), **per-organisation** settings (→ organisation settings with org-scoped endpoints and RLS), or **per-processing-entity** settings.

**PO DECISION REQUIRED.** Whether each settings domain is platform-scoped, organisation-scoped or entity-scoped is a **product/architecture decision** (it determines the URL shape, the RLS policy and who may change it), and the endpoints currently hard-code the "platform" answer that nobody ratified. Recommended decision inputs: `AGENTS.md` §31, §42; handover §9.14. **No settings were changed during this fact-find.**

---

## 12. Persona-level observed findings (P01–P10) `[RECONSTRUCTED]`

This section answers the brief's core question per persona: **does this persona actually perform a coherent piece of CarbonTally business work, or does it reach a shell?**

Denial-shape totals across all 460 persona×endpoint probes: **`200` = 62 (13.5%)**, **`403` = 344 (74.8%)**, **`422` = 54 (11.7%)**, **`404` = 0 (0%)**. The full grid is Appendix A; the denial-shape analysis is §13.

### P01 — `platform_admin` (19/46 allow — the least-constrained login)

| Aspect | OBSERVED |
|---|---|
| Reaches | `/ops` nav for Organizations, Staff, Staff roles, Review/QC queues, Review/QC/Audit reporting, Commercial Coverage, Manual Processing, SLA settings, Entities, Settings (retention), Analytics |
| Denied that matters | **`can_view_all` surfaces** — `ops/dashboard`, `operational-intelligence`, `operational-health/queue`, `reporting/platform`, `reporting/aging`, `backups/status`, `qc/ct-queue` — all `403`. The **operator queue** is `403`. The **PE workspace** is `403`. |
| Verdict | `PARTIAL` — this is the *broadest* login, yet the very surfaces whose names are platform-wide ("platform reporting", "operational health", "backups") are the ones it cannot open. This is the runtime proof of `PR-01`: **no role in CarbonTally holds `can_view_all`, `can_qc` or `can_manage_backups` simultaneously with `is_superuser`.** A "system admin" that cannot see operational health or platform reporting cannot administer the platform's own health. |

### P02 — `internal_operator` (5/46 allow)

| Aspect | OBSERVED |
|---|---|
| Reaches | Operator queue, entity dashboard + extraction batches for **PE Alpha only** (`PE Beta` = `403`), staff-roles, analytics settings |
| Denied that matters | Everything review-shaped (`can_review`), whole-organisation scope (`can_view_all`), organisation management, Manual Processing admin, `settings/retention` |
| Verdict | `PARTIAL` — the operator can *pick up queued work* (the queue is real, §10) and can see the entity's extraction batches, but cannot see the organisation, the submission, or the emissions behind the work item. Operational context is missing at exactly the point the work item is opened (see §37/§76 of `AGENTS.md`). |

### P03 / P04 — PE staff (`pe_manager` @ Alpha 8/46, `pe_beta_manager` @ Beta 6/46)

| Aspect | OBSERVED |
|---|---|
| Reaches | `/api/v3/pe/me`, `/pe/work`, `/pe/team`, `/pe/issues`; own entity dashboard; own entity extraction batches (Alpha only for P03); staff-roles; analytics settings |
| Denied that matters | **PE Beta's** entity dashboard and batches are `403` for P03 (correct isolation, §12 of `AGENTS.md`); all customer org surfaces `403`; all document surfaces `403` |
| Verdict | `PARTIAL BUT CORRECTLY ISOLATED` — the PE boundary itself holds (**PE A ⇒ PE B denied**, one of the security assertions the brief asks for), and `pe/work` returns real assigned work. The gap is not isolation but *reach*: PE staff have their own workspace and **no** access to the customer org, the source-document boundary is enforced server-side as specified, and the audit found no PE→customer leak. |

### P05 / P06 — Customer (`org_a_owner` 6/46, `org_a_viewer` 6/46 — identical)

| Aspect | OBSERVED |
|---|---|
| Reaches | Own org profile, own members, own org Manual Processing state, accounting context, `billing/me`, analytics settings — **exactly the same 6 endpoints** |
| Denied that matters | `emissions/dashboard` → **`422`** (!), `documents` → **`422`** (!), commercial entitlement → `403`, all ops/PE/consultant surfaces `403` |
| Verdict | `BLOCKED` — the customer's two most important reads (`documents`, `emissions/dashboard`) return **`422`, not `200` and not `403`** (§13). A customer cannot list documents or see emissions through the V3 API as probed. Combined with `FIND-9.12` (no subscription empty state) and §10 (96% blocked queue), the customer-facing journey is not demonstrably working end-to-end. |
| Security note | Owner and **Viewer are indistinguishable at the API layer** on every probe in this grid (both `200` on the same 6; both `403` on the rest). Write-path separation is therefore **`UNVERIFIED`** by this audit — the brief's "Viewer → prohibited write" test requires a write probe that this read-only audit did not perform. It is a **required follow-up**, not a passed test. |

### P07 / P08 — Consultant (3/46 each)

See `FIND-9.8`, `FIND-9.9`, `FIND-9.10`. OBSERVED: `/consultants/me` + `/consultants/me/manual-processing/coverage` + analytics settings, nothing else. **Owner and member are indistinguishable** (3 = 3, same endpoints). Verdict: `PARTIAL / UNDER-PROVISIONED` — the consultant is a first-class operator in the product model (`AGENTS.md` §10) but is a work-item viewer in the runtime.

### P09 / P10 — Client / direct customer (3/46 each)

OBSERVED: own-org accounting context, `billing/me`, analytics settings. Both are correctly **denied ORG_A** (`403`) — a genuine cross-tenant assertion that **passes**. Verdict: `PARTIAL` but the same `documents`/`emissions` `422` blocker as P05/P06 applies to their own workspace.

**Cross-persona summary verdict.** **No single login can walk the documented journey** (upload → … → reporting). The closest is `platform_admin` (19 endpoints) which is structurally excluded from the operator queue, the PE workspace and every `can_view_all` surface; the closest to the *business* journey is `internal_operator` (queue + batches) which is excluded from the organisation and review layers. This is `PR-01`, restated in persona terms.

---

## 13. Endpoint → persona mapping and denial-shape analysis `[RECONSTRUCTED]`

Full 46×10 grid: **Appendix A**. Raw artefact: `/tmp/p5_matrix.txt` (probe harness `/tmp/aud_probe5.*`).

### 13.1 Shape of the denials

| Response | Count | Share | What it means |
|---|---|---|---|
| `200` | 62 | 13.5% | Authorised and served |
| `403` | 344 | 74.8% | Authorised-path denial (`"You don't have permission to access this area."` — `api.js:26`) |
| `422` | 54 | 11.7% | **Request validation executed *before* authorisation** |
| `404` | 0 | 0% | No resource-masking observed (but see 13.3) |

**Finding (endpoint-level, `MEDIUM`).** The authoritative surfaces of the platform refuse **three quarters of every probe**. That is the quantitative form of `PR-01`: the permission model is not merely strict, it is *disjoint* — capability families that business documents describe as belonging to one operator (process + review + organisation scope) are split so that no single identity holds them.

### 13.2 The `422` endpoints — validation before authorisation

Seven endpoint families answered `422` for at least one persona — and for four of them, for **every** persona:

| Endpoint | Who got `422` | Who got `403` | Who got `200` |
|---|---|---|---|
| `/api/v3/processing/queue` | **all 10** | — | — |
| `/api/v3/processing/dashboard` | **all 10** | — | — |
| `/api/v3/processing/customer-review` | **all 10** | — | — |
| `/api/v3/messaging/conversations` | **all 10** | — | — |
| `/api/v3/accounting/context` | 6 personas (2 staff, 2 PE, 2 consultant) | 2 PE | 4 org-linked |
| `/api/v3/documents` | 4 org-linked personas | 6 (staff, PE, consultant) | — |
| `/api/v3/emissions/dashboard` | 4 org-linked personas | 6 | — |

Two consequences, both reportable:

1. **Authorisation order (`SECURITY SMELL`, `MEDIUM`).** For these endpoints the framework rejects a malformed request *before* the authorisation dependency runs, so an unauthorised caller receives a schema-shaped `422` rather than a `403`. The existence and parameter contract of `/api/v3/processing/*` and `/api/v3/messaging/conversations` is therefore disclosed to callers who are not entitled to reach them. This does not leak data, but it does leak **surface**, and it makes the API's denial semantics unlearnable for clients.
2. **False negative risk in QA (`QA NOTE`, important).** `200`/`403` totals for these families are **not** an authorisation result — **no persona ever satisfied the request contract**. Consequently:
   - the authorisation behaviour of `/api/v3/processing/queue`, `/processing/dashboard`, `/processing/customer-review` and `/messaging/conversations` is **`UNVERIFIED`** for every persona (this is not a pass and not a fail);
   - the customer's `documents` and `emissions/dashboard` denials of "cannot read" are in reality **"the probe's request shape was rejected"** — a *stronger* statement is not available without a correctly-shaped call. **This is the single most important follow-up probe for the next audit**, because `documents` and `emissions/dashboard` are the two endpoints the whole customer journey depends on.

### 13.3 `404` — not observed, therefore not assessable

Zero `404` responses across 460 probes. All identifiers used were real, so this audit **cannot** state whether non-existent or cross-tenant identifiers are masked as `404`. Uniform `403` denials are consistent with correct isolation, but a deliberate **existence-probe** (real vs random UUID) is required before claiming masking behaviour either way.

### 13.4 The outliers that matter most

| Observation | Endpoint | Interpretation |
|---|---|---|
| **All 10 personas receive `200`** | `/api/v3/settings/analytics` | `PR-06` — the sharpest over-permission in the audited surface: a customer viewer, a PE operator and a consultant all read (and, by mirror-symmetry of the paired `PUT` in `api.js:2122`, may write) platform analytics configuration. |
| **Exactly 1 persona receives `200`** | `/api/v3/ops/staff`, `admin/entities`, `admin/manual-processing/*`, `ops/queues/review`, `ops/queues/qc`, `ops/reporting/{review,qc,audit}`, `admin/review-queue`, `admin/sla/settings`, `settings/retention` | The entire internal-operations control plane is **single-identity**: `platform_admin` only. If that identity is lost or mis-scoped, platform operations stop. |
| **Exactly 1 persona receives `200`** | `/api/v3/ops/queues/operator` | The operator queue is likewise **single-identity** (`internal_operator`). There is no second operator-capable role anywhere in the matrix. |
| **Nobody receives `200`** | `ops/dashboard`, `ops/operational-intelligence`, `ops/operational-health/queue`, `ops/reporting/platform`, `ops/reporting/aging`, `ops/backups/status`, `ops/qc/ct-queue`, `commercial/entitlement/*` | **Eight endpoints are unreachable by every audited identity.** Each is `can_view_all`/`can_qc`/`can_manage_backups`/entitlement-scoped. This is the definitive runtime evidence that those capabilities are **not held by any role** (`PR-01`) — the surfaces exist, are routed, are documented, and are dead.

---

## 14. Product-reality register (PR-01 … PR-07) `[RECONSTRUCTED]`

These are cross-cutting conclusions that belong to the *product*, not to a single persona or screen. Each was raised in §6/§9/§10 and is consolidated here with severity.

| ID | Statement (short) | Severity | Classification | PO decision? |
|---|---|---|---|---|
| PR-01 | `can_view_all` surfaces are unreachable by **every** identity | `HIGH` | `PERMISSION GAP` | **Yes** — who is the platform operator? |
| PR-02 | `can_qc` / CT QC queue unreachable by **every** identity | `HIGH` | `PERMISSION GAP` | **Yes** — who is QC? |
| PR-03 | `can_manage_billing` — the Commercial tab renders for **nobody** | `HIGH` | `PERMISSION GAP` | **Yes** — who owns commercial config? |
| PR-04 | **No single login walks the journey** | `HIGH` | `PRODUCT GAP` | **Yes** — is that intended? |
| PR-05 | `/api/v3/ops/staff-roles` open to **all four** staff identities incl. both PE managers | `MEDIUM` | `PERMISSION GAP` | No (implementation) |
| PR-06 | `/api/v3/settings/analytics` `200` for **all ten** personas | `MEDIUM` | `PERMISSION GAP` | No (implementation) |
| PR-07 | 60 `organization_files` vs 46 storage objects → **14 orphans** | `MEDIUM` | `DATA INTEGRITY` | No (implementation) |

**Classification note — added after the root-cause analysis below.** PR-01/PR-02/PR-03 were first recorded as `PERMISSION GAP` (product). Their *mechanism* in this environment is `ENVIRONMENT / PROVISIONING DEFECT`: the capability gates are implemented and correctly enforced, and the capability **data** was overwritten by the Demo Lab provisioner. Their product consequence is still a permission gap, and the policy question — *who should hold each capability* — is unchanged and remains `PO DECISION REQUIRED` (PD-01/PD-02/PD-03).

### PR-01 — `can_view_all` is a dead capability

`GET /api/v3/ops/dashboard` → `403` for all ten personas (§8 row 1). The same is true of `/ops/operational-intelligence`, `/ops/operational-health/queue`, `/ops/reporting/platform` and `/ops/reporting/aging`. Four distinct, routed, documented platform-wide management surfaces are unreachable by **every** identity in the system, including `platform_admin`. **Consequence:** CarbonTally has no working platform-health view — nobody can see the platform's own operational state, and `FIND-9.13` (Assignments tab) fails *because* of this gap rather than because of a local bug. `PO DECISION REQUIRED`: which role is the platform operator, and does it hold `can_view_all`? (`AGENTS.md` §13 explicitly warns against treating "admin" as a universal shortcut — the fix is a named capability on a named role, not a blanket grant.)

### PR-02 — `can_qc` is a dead capability

`GET /api/v3/ops/qc/ct-queue` → `403` for all ten personas (§8 row 10), while `/ops/queues/qc` and `/ops/reporting/qc` are `200` for `platform_admin` **only**. The QC *queues that exist* are single-identity and the CT QC queue is dead. Given `AGENTS.md` §13 (QC is a distinct responsibility) and §14 (role administration is privileged), the missing element is a **QC role with `can_qc`** — not a broadening of `platform_admin`. `PO DECISION REQUIRED`.

### PR-03 — the Commercial tab renders for nobody

§6 records that `can_manage_billing` gates the Operations **Commercial** tab and that **no role holds it**, so the tab is never shown to anyone. Combined with §10 (`customer_subscriptions` = 4, `billing_orders` = 0) and `FIND-9.11` (three competing billing vocabularies), the commercial administration surface is unreachable *and* its terminology is unresolved. This is the strongest single illustration of the "orphaned capability" pattern: a surface, its endpoints, its schema and its terminology all exist; the identity that would use it does not.

### Root cause of PR-01 / PR-02 / PR-03 — verified (capability-data drift, not UI or authz bugs)

All three are **the same defect** with one identifiable writer, and it is *not* a frontend omission and *not* a backend authorization bug.

1. `DB` — `staff_roles` contains exactly **three** rows: `admin`, `operator`, `pe_manager`. There is **no `system_admin` row and no `qc_specialist` row**, although the release migrations seed/update those very names (`supabase/migrations/20260828010000_v3m8_system_admin_role_model.sql:25-28` targets `system_admin`; `20260902020000_v1_2_dual_origin_workflow.sql:102-105` targets `qc_specialist`, `admin`).
2. `CODE` — the release grants the three missing capabilities **as data**, via additive `permissions || '{...}'` updates:
   - `can_manage_billing` → `admin` (`20260824020000_d37_0_billing_security_and_configurable_subscription.sql:300-304`) and `system_admin` (`20260828010000_…:25-28`);
   - `can_qc` → `qc_specialist` and `admin` (`20260902020000_…:102-105`);
   - `can_view_all` → `pe_manager` (`20260828020000_v3m8_pe_manager_role.sql:22-30`) — note this migration deliberately gives the PE-manager role platform-wide queue visibility.
3. `DB` — the live rows hold **none** of them, and all three rows carry the *same* `updated_at` (`2026-10-04 13:13:31Z`), i.e. a single bulk write touched every role.
4. `CODE` — the bulk writer is identifiable and unambiguous: `tools/demo_lab/provision.py::ensure_staff_roles` (`:101-159`) executes `UPDATE staff_roles SET permissions = <literal map>::jsonb WHERE id = …` (`:150-151`) — a **wholesale replacement**, not a merge. The literal map (`:130-135`) omits `can_manage_billing`, `can_qc`, `can_view_all` and `can_manage_backups`, so every provisioning run erases whatever the migrations granted. The same function's comment (`:119-129`) asserts the admin role "already holds `can_qc`" — the row it writes does not, so the comment is stale relative to its own output.
5. `CONSEQUENCE` — the gates are implemented and correctly enforced server-side; the *capability data* is absent. Every environment provisioned by this tool reproduces PR-01/02/03, and the operations dashboard, CT QC queue, Commercial tab and Backups tab are unreachable for every persona in it.

**Classification revision.** PR-01/02/03 were first classified `PERMISSION GAP` (product). On this evidence they are more precisely `ENVIRONMENT / PROVISIONING DEFECT` **whose product consequence is a permission gap**. The distinction matters for remediation: the fix is *either* a data-merging provisioner *or* a PO decision to make the capability vocabulary explicit — not a UI change, and not a broadened backend guard (`AGENTS.md` §67 — never disable a gate to make a surface reachable). Scope caveat: this is `CONFIRMED` for the audited local stack; whether the production `system_admin` role carries these capabilities was **not** verifiable from here (`UNVERIFIED`).



The documented business chain (`AGENTS.md` §18: upload → … → reporting) cannot be traversed by any one identity:

| Journey stage | Identity that can reach it | Can it continue? |
|---|---|---|
| Upload / customer submission | `org_a_owner` (customer) | ✗ `documents`/`emissions` return `422`; cannot see processing state |
| Intake queue | `internal_operator` | ✗ no organisation scope, no review |
| Manual-processing governance / entitlement | `platform_admin` (`can_manage_organizations`) | ✗ no operator queue, no PE workspace |
| Processing / extraction | `internal_operator` + `pe_manager` | ✗ no review capability |
| Review / QC | `platform_admin` only (`can_review`) | ✗ not the operator who processed |
| Commercial / reporting | **nobody** (PR-01/PR-03) | ✗ |

**Consequence.** The platform is not merely "strictly permissioned" — it is **composed of silos that no business role spans**. Every audited identity ends its journey at a boundary it cannot cross. `PO DECISION REQUIRED` (is the journey intentionally multi-actor, and if so, which role carries which stage handoff?). Note this is a *design* question: four-eyes separation is legitimate; the defect is that **the handoff is not consumable**, because the next actor cannot see the previous actor's context (`AGENTS.md` §37/§76).

### PR-05 — staff-roles open to all staff and PE managers

`GET /api/v3/ops/staff-roles` → `200` for `platform_admin`, `internal_operator`, `pe_manager` and `pe_beta_manager` (§8 row 4) while the neighbouring `/api/v3/ops/staff` is `platform_admin`-only. Role *definitions* are visible to the entire staff population, including Processing-Entity operators who are explicitly not internal CarbonTally administrators (`AGENTS.md` §12/§14). `Classification: PERMISSION GAP` (`MEDIUM`); implementation-level, but the PO should confirm whether role metadata is intended to be platform-public to staff.

### PR-06 — analytics settings open to all ten personas

`GET /api/v3/settings/analytics` → `200` for all ten personas, including a customer **Viewer**, a client owner, and PE operators (§8 row 44, §13.4). The paired writer (`PUT /api/v3/settings/analytics`, `api.js:2122`, `updateAnalyticsSettings`) sits on the same platform-global path, so the *read* leak is proven and the *write* exposure is a strong inference that requires a write probe to confirm. `Classification: PERMISSION GAP` (`MEDIUM`; `HIGH` if writes are equally open). This is the clearest single deviation from `AGENTS.md` §44 in the matrix.

### PR-07 — 14 orphaned document records

`organization_files` holds 60 rows while the `documents` storage bucket holds 46 objects (§10), i.e. **14 records reference no object**. Consequence for the business: a record can exist with no retrievable evidence — directly contrary to the provenance requirements in `AGENTS.md` §17/§68. This audit did not determine whether the orphans are (a) test residue, (b) records whose upload failed after the row was inserted, or (c) documents whose objects were evicted. `Classification: DATA INTEGRITY` (`MEDIUM`); needs a read-only reconciliation query before any cleanup (`AGENTS.md` §55 — do not delete demo data casually).

---

## 15. Environment fidelity — what this stack actually is `[RECONSTRUCTED]`

The audit ran against `carbontally_demo_local` (`127.0.0.1:54426`). Measured population (`DB`, read-only):

| Object | Rows | Object | Rows |
|---|---|---|---|
| `auth.users` | **19** | `processing_entities` | 2 |
| `organizations` | **11** | `consultant_profiles` | 3 |
| `organization_members` | 12 | `consultant_firm_members` | 4 |
| `staff_profiles` | **4** (2 internal, 2 entity-scoped) | `consultant_clients` | 5 |
| `staff_roles` | **3** | `manual_processing_grants` | 1 |

This is the **Demo Lab** population provisioned by `tools/demo_lab/provision.py`. It is **not** the investor-demo dataset described in `AGENTS.md` §54 (`tools/seed_investor_demo/DEMO_IDENTITIES.md` — ≈1,185 identities: ~50 direct customer organisations × 4 roles, 911 consultant-client owners, 50 consultants, 5 internal staff identities). Four `staff_profiles` against a manifest that declares five internal staff identities is the clearest single indicator that the manifest's environment was not the environment probed.

**Consequences for the credibility of this audit — stated plainly:**

1. **Six of the ten personas are single identities standing in for entire roles.** Role-level conclusions therefore rest on **one** login per role, which `AGENTS.md` §56 explicitly warns against. Cross-boundary isolation *was* asserted with multiple identities (§16), but role *behaviour* coverage is thin.
2. **The investor-demo environment was not probed.** No 1,185-identity database was found on this cluster's DSN and no `seed_investor_demo` run was observed. Bulk deterministic population checks (911 consultant-client owners; 50 customer orgs) remain **`UNVERIFIED`** — the largest coverage gap in this report.
3. **The audited `platform_admin` is a Demo-Lab-invented role.** `provision.py:104-106` states the release's seeded vocabulary does not include `admin`; the release's administrative role is `system_admin` (`20260828010000_v3m8_system_admin_role_model.sql`), and **no `system_admin` row exists in this database**. The release administrator identity was therefore never exercised.
4. **PE-manager intent drifted as well.** `20260828020000_v3m8_pe_manager_role.sql:27` grants `pe_manager` `{can_process, can_review, can_view_all}`; the live row holds `{can_process, can_manage_team, demo_lab}`. Both the PE queue-visibility and PE review capabilities the release intends are absent here, so the **PE `review` branch of the dual-origin workflow was not reachable** by the audited PE managers (`UNVERIFIED` — not directly probed; flagged because it is the same drift class as §14's root cause).
5. **Write paths were never probed.** The matrix is GET-only and no state-changing call was issued (read-only mandate, §3). Every statement in this report about writes is an **inference from source**, not an observation — most importantly PR-06's `PUT /api/v3/settings/analytics`.

**Fidelity verdict.** Findings that depend on *code paths and gates* (enforcement, deny shapes, isolation, UI wiring) transfer to any environment. Findings that depend on *capability data* (PR-01/02/03, the PE-manager gaps) are `CONFIRMED` for this stack and `UNVERIFIED` for production and for the investor-demo stack. Each is marked accordingly; none is presented as a verified production defect.

---

## 16. Cross-boundary isolation — consolidated assertion pass `[RECONSTRUCTED]`

Per §7: **18/18 isolation probes behaved as required; 0 unexpected ALLOWs.** The boundary-by-boundary record:

| # | Boundary (`AGENTS.md` §45) | Probe | Observed | Verdict |
|---|---|---|---|---|
| I-1 | Customer ↛ internal ops | `org_a_owner` → `/ops/organizations`, `/ops/staff`, `/admin/*` | `403` | **PASS** |
| I-2 | Internal ops ↛ customer org | `internal_operator`/`platform_admin` → `/organizations/{ORG_A}/*` | `403` | **PASS** |
| I-3 | PE A ↛ PE B | `pe_beta_manager` → `/ops/entities/{PE_ALPHA}/{dashboard}`,`/extraction/batches` | `403` *"not authorized for this processing entity"* | **PASS** |
| I-4 | PE ↛ customer org | PE personas → `/accounting/context` | `403` *"Processing Entity staff may not act for a customer organization directly"* | **PASS** |
| I-5 | PE ↛ internal admin authority | PE personas → `/settings/retention` | `403` *"…cannot hold internal admin authority"* | **PASS** |
| I-6 | Consultant ↛ customer org shell | both consultant personas → `/organizations/{ORG_A}/*` | `403` | **PASS** |
| I-7 | Client A ↛ other org | `client_a_owner` → `/organizations/{ORG_A}/*` | `403` | **PASS** |
| I-8 | Client B ↛ ORG_A | `client_b_owner` → `/organizations/{ORG_A}/*` | `403` | **PASS** |
| I-9 | Consultant ↛ internal ops | both consultant personas → all `/ops/*`, `/admin/*` | `403` | **PASS** |
| I-10 | Customer ↛ consultant firm | both customer personas → `/consultants/me*` | `403` | **PASS** |
| I-11 | Staff (non-admin) ↛ staff-admin op | `internal_operator` → `/ops/staff` | `403` (only `platform_admin` `200`) | **PASS** |
| I-12 | Viewer ↛ privileged operation | `org_a_viewer` → all ops/admin | `403` on every one | **PASS (read)** |
| I-13 | PE ↛ customer document | PE personas → `/organizations/{ORG_A}/*` | `403` | **PASS** |
| I-14 | No-membership ↛ anything | contexts without membership | `403` *"Organization member access required"* | **PASS** |

**Deviations — over-permission, not leakage:**

- **FAIL — I-15 role metadata**: `/api/v3/ops/staff-roles` is `200` for **all four** staff identities including both PE managers, while the neighbouring `/ops/staff` is `platform_admin`-only (PR-05).
- **FAIL — I-16 platform analytics**: `/api/v3/settings/analytics` is `200` for **all ten** personas, including a customer Viewer and PE operators (PR-06).

**Not testable in this stack:**

- **UNVERIFIED — I-17 Staff Admin ↛ System-Admin-only operation**: no `system_admin` row exists (§15), so the `ADMIN_ROLE_NAMES` staff-admin/system-admin distinction was never exercised at runtime.
- **UNVERIFIED — I-18 write denials**: no `PUT`/`POST`/`DELETE` was issued. Read-path isolation passing does **not** imply write-path isolation passing.
- **UNVERIFIED — I-19 identifier masking**: 0 `404`s observed and no existence-probe (real vs random UUID) was run (§13.3).

**Net statement.** Read-path tenant isolation is **verified and consistent** across all fourteen testable boundaries, with zero cross-tenant ALLOWs. The two deviations found are over-permission on *metadata/config* surfaces (staff-role definitions, platform analytics), not tenant data exposure.

---

## 17. Pipeline reality — what the state machine models versus what the data occupies `[RECONSTRUCTED]`

### 17.1 The model is release-grade (schema evidence)

`DB` — `document_processing_queue` (46 rows) carries the complete durable-processing apparatus required by `AGENTS.md` §19:

- **State**: `status` constrained to **eleven** values — `pending`, `processing`, `ai_extracted`, `manual_review`, `manual_extraction`, `qc`, `customer_review`, `approved`, `rejected`, `completed`, `failed` — plus a separate `stage` column.
- **Durability/retry**: `attempt_count`, `max_attempts`, `last_error`, `locked_at`, `lock_token`, `workflow_error_count`, `workflow_next_retry_at`, `reprocess_count`.
- **Progress ladder (timestamps)**: `ingested_at`, `extracted_at`, `mapped_at`, `validated_at`, `calculated_at`, `review_ready_at`, `completed_at`.
- **Provenance**: `source_item_id`, `calculation_snapshot_id`, `emission_factor_used`, `extracted_data`, `mapped_data`, `validation_result`.
- **Human-gate bookkeeping**: `manual_requested_by/at`, `manual_assigned_to/by/at`, `manual_extracted_by/at`, `qc_required/by/at/approved`, `customer_reviewed_by/at`, `customer_approved`, `customer_rejection_reason`.

This is not a stub. The platform genuinely models the pipeline described in `AGENTS.md` §18/§19, including provenance and manual-review gates.

### 17.2 The data occupies only the human gates

`DB` — the actual status distribution of all 46 queued documents:

| Status | Rows | Share |
|---|---|---|
| `manual_review` | **44** | 95.7% |
| `customer_review` | 2 | 4.3% |
| `pending` / `processing` / `ai_extracted` / `approved` / `completed` / `failed` | **0** | 0% |

Every document in the audited environment is parked at a human gate. There is **no** row in an autonomous stage and **no** row in `failed`, so in this environment there is **no evidence** that the durable retry / dead-letter behaviour (`attempt_count`, `workflow_next_retry_at`, `last_error`) has ever engaged. `calculation_snapshots` (≈34 rows) shows calculation has run at some point, but the queue composition is consistent with an environment that has never carried a document autonomously from intake to `completed`.

**Honest scope of that statement.** This is the composition of a **seeded Demo Lab**, not an engineered throughput test; uploads parked for review is a legitimate seeding choice. The finding is therefore `INFO`/`MEDIUM` and is phrased as *what the data shows*, not as a claim that the engine cannot complete (§74 — no false conclusions from apparatus).

### 17.3 The handoff is not consumable

The stages exist; the *transitions between actors* do not work in practice:

| Transition | Who leaves the item | Who must pick it up | Product reality |
|---|---|---|---|
| upload → processing | customer (`org_a_owner`) | `internal_operator` | Customer cannot observe state: `/api/v3/documents` and `/emissions/dashboard` answered `422` to the customer's calls (§13.2), so the customer's only readable state surfaces are `/organizations/{id}/manual-processing` and `/billing/me` |
| manual_review → manual_extraction | `internal_operator` | operator/PE | Operator queue (`/ops/queues/operator`) is `200` for **exactly one** identity in the whole system (§13.4) |
| manual → qc | — | a `can_qc` holder | **No identity holds `can_qc`** (PR-02) |
| qc → customer_review | — | `controller`/`can_review` holder | `can_review` sits only on `platform_admin`, who *cannot* reach the operator queue (no `can_process`) |
| customer_review → approved/rejected | customer | customer | 2 rows sit here; the customer's review surface is reachable, but the **evidence** behind the number (`/emissions/dashboard`) is not (§13.2) |
| → reporting / commercial | — | — | Unreachable (PR-01/PR-03) |

This is the concrete mechanism behind PR-04: the four-eyes separation is architecturally intended, but **the next actor cannot see the previous actor's context** (`AGENTS.md` §37/§76), so every handoff terminates rather than transfers.

### 17.4 Residue, not execution — what this audit did and did not verify

The audit was read-only (§3) and issued **no** upload, no processing request and no workflow transition. It therefore verified the pipeline's **apparatus and residue**, not its execution:

- **VERIFIED**: the state machine, provenance columns, manual-gate bookkeeping, queue contents and the authorization gates around them.
- **NOT VERIFIED (and not claimed)**: that a document can today be carried end-to-end from upload to an approved emissions figure by a real user in the product. Per `AGENTS.md` §74, uploading a PDF is not processing completion, and this audit did not observe a completion — **no request in the matrix returned an asynchronous acceptance (`202`), because no asynchronous endpoint was invoked at all.**

**Consequence for the next audit.** The decisive missing probe is a *state-changing, isolated* end-to-end run (with cleanup, per `AGENTS.md` §55): one QA-labelled organisation, one small document, then observe queue → extraction → mapping → validation → calculation → evidence → review → approval through the API, recording `document_processing_queue.status` at each step. Until that exists, "the pipeline works" is `UNVERIFIED` for every environment, including production.

---

## 18. Unverified register — what this audit did **not** establish `[RECONSTRUCTED]`

`AGENTS.md` §52 requires the distinction between `PASS`, `FAIL`, `SKIPPED`, `BLOCKED` and `UNVERIFIED`. The following are **not** passes; several are the most decision-relevant gaps.

| ID | Unverified question | Why unverified | Proposed method | Priority |
|---|---|---|---|---|
| **U-01** | Can a customer actually read their own `documents` and `emissions/dashboard`? | Both answered `422` to every org-linked persona — the probe's request shape was rejected before authorization ran (§13.2) | Re-issue with the exact contract (required query/body params from the OpenAPI schema), as `org_a_owner` | **HIGHEST** — the whole customer journey depends on these two reads |
| **U-02** | Is the **write** surface authorized as strictly as the read surface? | No `PUT`/`POST`/`DELETE` was issued (read-only mandate) | Bounded write matrix on QA-labelled records only (viewer/member/client attempts on cross-tenant ids), full cleanup | **HIGH** |
| **U-03** | Does `PUT /api/v3/settings/analytics` accept a Viewer's write (PR-06)? | Only the paired `GET` was probed | Single write probe as `org_a_viewer`, then restore the original value | **HIGH** |
| **U-04** | Is authorization enforced on `/processing/queue`, `/processing/dashboard`, `/processing/customer-review`, `/messaging/conversations`? | All `422` for **all ten** personas — authorization never ran | Supply the required parameters; re-probe all ten personas | **HIGH** |
| **U-05** | Are non-existent / cross-tenant identifiers masked as `404`? | Zero `404`s observed; no existence-probe run (§13.3) | Same endpoint with a real vs a random UUID, compare status + body | `MEDIUM` |
| **U-06** | Do the documented bulk isolation properties hold across the ≈1,185-identity investor-demo population? | That environment was not present on this cluster's DSN (§15) | Deterministic DB/API sweep over `DEMO_IDENTITIES.md`: 911 consultant-client owners ↛ other firms' clients; 50 orgs ↛ each other | **HIGH** (covers `AGENTS.md` §56) |
| **U-07** | Staff-Admin ↛ System-Admin-only boundary | No `system_admin` row exists in this stack (§15) | Seed/provision the release role model, then re-run the boundary | `MEDIUM` |
| **U-08** | Is the PE `review` branch of the dual-origin workflow reachable? | `pe_manager` lacks the `can_review` the migration grants (§15 item 4) | Grant per migration intent in a QA env, re-probe PE review transitions | `MEDIUM` |
| **U-09** | Does the pipeline complete end-to-end, and do retry/dead-letter engage? | No autonomous-state or `failed` rows exist; nothing was executed (§17.2/17.4) | Isolated end-to-end run with stage-by-stage state capture | **HIGH** |
| **U-10** | Does the production environment behave like this stack? | No production access; `https://carbontally-api.onrender.com/openapi.json` was not exercised with credentials | Deploy-time capability/capability-data diff (roles × permissions) | `MEDIUM` |
| **U-11** | Do `billing_plans` rows actually entitle Manual Processing as `FIN-06 §0` describes (`features.manual_processing.enabled` OR `assisted_processing_available`)? | The OR-fallback was read in the governance doc; no plan-by-plan evaluation was run | Read-only query: for each of the 23 plans, evaluate both branches; compare with the 4 `customer_subscriptions` | **HIGH** — underpins FIND-9.11 and PR-03 |
| **U-12** | Does any Processing-Entity ↔ CarbonTally messaging conversation exist (`conversation_kind`, `processing_entity_id`)? | Participants table read, but no conversation was inspected for kind/entity | Read-only query on `conversations` grouped by `conversation_kind` | `MEDIUM` |
| **U-13** | What are the 14 orphaned `organization_files` rows, and are they safe to reconcile? | Counts compared, individual rows not examined (PR-07) | Read-only listing: rows minus storage objects, with `created_at` clustering | `MEDIUM` |
| **U-14** | Is MFA/TOTP enforced or optional in this environment? | Not probed | Auth-flow inspection (`AGENTS.md` §69 is a deployment policy question) | `INFO` |

**Priority summary.** U-01, U-02, U-03, U-04, U-06, U-09 and U-11 are the probes that would most change the report's conclusions. U-01 and U-09 in particular convert two large `UNVERIFIED` regions (customer readability; pipeline completion) into either `PASS` or `FAIL`.

---

## 19. Consolidated PO decision register `[RECONSTRUCTED]`

Every item below is a **business-policy** question (`AGENTS.md` §62). None may be resolved by an implementation agent.

| ID | Question for the Product Owner | Sources | What it blocks |
|---|---|---|---|
| **PD-01** | Who is the **platform operator** — which named role holds `can_view_all` (platform health, queue ageing, platform reporting)? | PR-01, §13.4, §15 | Whether the operations dashboard/reporting surfaces are *intended* to be reachable, and by whom |
| **PD-02** | Who is **QC** — which role holds `can_qc`, given `AGENTS.md` §13 treats QC as a distinct responsibility? | PR-02 | Reachability of the CT QC queue and the `manual → qc` transition |
| **PD-03** | Who owns **commercial configuration** (`can_manage_billing`)? Should the release role `system_admin` (absent in this stack) be the holder, or the demo `admin`? | PR-03, §14 root cause | Reachability of the Commercial surface and resolution of FIND-9.11 |
| **PD-04** | Is the end-to-end journey **intentionally multi-actor**, and if so which role carries each handoff and what context must transfer? | PR-04, §17.3 | Whether "no single login walks the journey" is a defect or a design premise |
| **PD-05** | Are **Assisted Processing** and **Managed Processing** the same commercial services as **Manual Processing**, separate tiers, or the same axis as Self-Service? May the public site keep selling them? | FIND-9.11 (items 1–8 and the four sub-questions) | Any rename, migration, entitlement change or public-copy change |
| **PD-06** | Is **staff-role metadata** (`/ops/staff-roles`) intended to be readable by every staff identity, including Processing-Entity managers? | PR-05 | Whether PR-05 is a defect or intended staff transparency |
| **PD-07** | Is **platform analytics configuration** intended to be readable — and writable — by every authenticated identity, including a customer Viewer? | PR-06, U-03 | Severity of PR-06 (`MEDIUM` → `HIGH` if writes are open) |
| **PD-08** | May a **consultant create a customer organisation**, and if so who owns it and how is it later detached (preserving `organisation.id`)? | FIND-9.8, FIND-9.9 | The consultant onboarding gap (`AGENTS.md` §10/§11) |
| **PD-09** | Do **platform-global settings** belong in the operations workspace at all, or in a separate control plane (`AGENTS.md` §31)? | FIND-9.14 | The information architecture of the settings surfaces |
| **PD-10** | Which plan flags **entitle** Manual Processing in production, and is the OR-fallback (`features.manual_processing.enabled` ∥ `assisted_processing_available`) intended? | U-11, §10 `billing_plans`, FIND-9.11 item 7 | Correctness of entitlement for real customers |
| **PD-11** | Should the **DEMO_IDENTITIES manifest** (≈1,185 identities) or the Demo Lab be the reference environment for acceptance testing, and who provisions the role model that the tests assume? | §15 | Whether future audits can honour `AGENTS.md` §54/§56 |

### Findings that need **no** PO decision (implementation backlog for Cline)

| Finding | Type | Note |
|---|---|---|
| FIND-9.5 — UUIDs as primary business labels | UX implementation | `AGENTS.md` §34/§75 already ratify the desired behaviour |
| FIND-9.6 — audit actor/resource resolution | UX implementation | Same |
| FIND-9.12 — empty states lack next-step guidance | UX implementation | `AGENTS.md` §48 already requires it |
| FIND-9.13 — Assignments tab unreachable | Functional defect | Same root cause as PR-01; fix follows its resolution |
| FIND-9.4 — Commercial Coverage too diagnostic | UX implementation | `AGENTS.md` §26/§47 |
| PR-01/02/03 — **mechanism** (provisioner wholesale-overwrite of `permissions`) | Provisioning defect | Fixing the writer is implementation; *who should hold the capability* is PD-01/PD-02/PD-03 |
| PR-07 — orphaned files | Data integrity | Requires U-13 first; cleanup only under `AGENTS.md` §55 |

---

## 20. Universal operational questions per workspace `[RECONSTRUCTED]`

`AGENTS.md` §76 requires every operational screen to answer seven questions. Assessed per workspace from the runtime evidence in this report (`✓` = answered, `~` = partially, `✗` = not answered).

| Question (§76) | Customer (`/`) | Consultant (`/consultant`) | PE (`/pe`,`/ops/entities/{id}`) | Internal ops (`/ops`) |
|---|---|---|---|---|
| 1. Where am I? | ✓ org shell + active-org banner | ✓ firm/active-client banner | ✓ entity-scoped workspace | ~ workspace labelled, tab set changes with permissions |
| 2. Which org/client/entity am I working on? | ✓ | ✓ (verified in prior audit CON-5) | ✓ own entity only | **~** org context appears on per-item surfaces, but queue and roster rows carry UUIDs (FIND-9.5) |
| 3. What needs attention? | ✗ no readable processing state (`/documents`, `/emissions` `422`, U-01) | ~ coverage tab only (FIND-9.4/9.7) | ~ batch list, no aging/priority | ~ queues exist but the dashboard that would prioritise them is dead (PR-01) |
| 4. What can I do? | ~ manual-processing upload path reachable | ~ no onboarding action (FIND-9.8) | ✓ start/complete own work | ~ actions exist but gated away from most staff (PR-04) |
| 5. What happened? | ✗ cannot read results/evidence | ✗ | ~ own item history | ~ audit console exists (permission-gated to one identity) |
| 6. What happens next? | ✗ (FIND-9.12 — empty states carry no next step) | ~ | ~ | ~ |
| 7. How do I go back? | ✓ | ✓ | ✓ | ~ OperatorItemPage returns to `?tab=assignments` — a tab its own reader cannot load (FIND-9.13) |

**Reading of the table.** Questions 1, 2 and 7 (wayfinding) are largely solved. Questions **3, 5 and 6 are the systemic weakness**: across all four workspaces the *state* of work and the *consequence* of work are not legible to the actor who must act on them. This is the UX form of PR-04 and it is consistent with FIND-9.12's count (21 `length === 0 &&` conditions, 31 `className="muted"` fallbacks in `frontend/src/v3`) — the product states a condition where it should state a condition **and** an owner **and** a next action.

---

## 21. Capability ownership — one capability, three surfaces, no owner `[RECONSTRUCTED]`

Manual Processing is a single product capability with **three separate entry points** and **three different vocabularies**, none of which sees the others:

| Surface | Route / gate | Vocabulary used | What it shows | Evidence |
|---|---|---|---|---|
| Customer | `/manual-processing` (`requireOrg`) | "Manual Processing" | own upload/state path | §9, FIND-9.1 |
| Consultant | `/consultant?view=coverage` (`requireConsultant`) | "coverage", "allocation" | firm coverage/allocation | FIND-9.4/9.7/9.12 |
| Internal | `/ops?tab=manual-processing-coverage` (`can_manage_organizations`) | "grant", "scope", "processor" + legacy "Assisted/Managed" in billing | org grants, processors, routing | FIND-9.1/9.3/9.11 |

**Consequences.**

1. **No single view can answer "is this customer entitled, and who will do the work?"** The grant lives on the internal surface, the allocation on the consultant surface, and the resulting state on the customer surface. `manual_processing_grants` has exactly **1 row** and `consultant_mp_allocations` has 13 (§10) — the data is present and the three surfaces simply do not compose.
2. **The capability has three names.** Combined with FIND-9.11 (Assisted/Managed still live in schema, backend and public marketing), the platform currently uses **four** terms for overlapping human-processing capability.
3. **Support is impossible with the current information architecture.** `AGENTS.md` §76 question 3 ("what needs attention?") and question 6 ("what happens next?") cannot be answered by a support agent either, because there is no surface that joins entitlement → allocation → queue → outcome. This is the structural reason FIND-9.1 ("configuration is not understandable") was raised by the PO.

**Recommendation (architectural, not a PO policy change).** Preserve the frozen role separation, but give the capability a single **owner-readable** summary — entitlement + allocation + current queue state for one organisation — reachable from each of the three workspaces, so that each role sees *its own actions and the consequences of them* (`AGENTS.md` §76). This is an implementation/UX item; it changes no permission and no policy.

**Cross-reference.** PR-04 is the journey-level form of this finding; FIND-9.13 is its acute functional form; §13's single-identity surfaces are its authorization form.

---

## 22. Limitations, confidence and reconstruction disclosure `[RECONSTRUCTED]`

### 22.1 Reconstruction disclosure

The original 28-section audit brief was **not present in the workspace** when this report was written. The structure was reconstructed from the handover document (`docs/architecture/carbontally_master_handover_2026-10-05.md` §9), whose PO manual-QA findings are re-verified here as FIND-9.1 … FIND-9.14, plus `AGENTS.md`'s QA/acceptance/security sections (§44–§56, §72–§76). Every section carries the `[RECONSTRUCTED]` marker so no reader mistakes it for brief-authorised scope.

**Risk this creates.** A brief-specific checklist item (a named persona, a named screen, a named workflow) may exist that this report does not address. If the brief is located, the delta should be diffed against §18 (Unverified register) first, because that is where an unaddressed item would surface.

### 22.2 Confidence grading of this report's own claims

| Evidence class | Basis | Confidence |
|---|---|---|
| Runtime HTTP results (46×10 matrix, §8/§13/Appendix A) | Direct observation against the live backend | **HIGH** |
| Database facts (role permissions, counts, status distribution, schema constraints) | Direct read-only SQL against the live database | **HIGH** |
| Source-reading claims (routes, gates, UI wiring, provisioning) | File/line citations, each quoted | **MEDIUM–HIGH** (no execution of the cited path unless also probed) |
| Write-path claims (PR-06 write exposure) | Inference from paired `GET`/`PUT` in `api.js` | **LOW** — explicitly flagged, needs U-03 |
| Production behaviour | Not accessed | **UNKNOWN** |
| Pipeline completion in any environment | Not executed | **UNVERIFIED** (U-09) |

### 22.3 Scope limitations (all material)

1. **Environment**: `carbontally_demo_local` Demo Lab (19 users / 11 orgs), **not** the ≈1,185-identity investor-demo dataset (§15).
2. **Population**: 10 personas, six of them single identities for a whole role — below the §56 standard.
3. **Method**: GET-only; no state-changing request; no browser/UI automation in this pass (no screenshots, so no viewport/responsive/accessibility verdict — `AGENTS.md` §49/§50 remain unassessed here).
4. **Time**: a snapshot dated **2026-10-05**; `staff_roles.updated_at` shows role data changes as recently as 2026-10-04 13:13Z, so permission data is volatile in this environment.
5. **No production parity check** (U-10) and no OpenAPI-vs-implementation diff.
6. **No load, concurrency, or idempotency testing** — `AGENTS.md` §19's duplicate-prevention guarantees are unexercised.

### 22.4 What this report should be used for

- As a **defect register** for the audited environment (FIND-9.x, PR-01…PR-07), each with file/line or runtime evidence.
- As a **probe specification** for the next pass (§18 is directly actionable).
- **Not** as an acceptance verdict, and **not** as evidence about production, until U-10 is closed.

---

## 23. Acceptance statement `[RECONSTRUCTED]`

`AGENTS.md` §73 requires these words to be used precisely.

| Word | Position of this work |
|---|---|
| **IMPLEMENTED** | **Nothing.** No application code, migration, configuration or data was changed by this audit (§3, Appendix C). |
| **TESTED** | **Yes, in part.** The 46×10 runtime probe matrix, identity/context resolution (14/14) and isolation assertions (18/18) were executed against the live stack. |
| **VERIFIED** | **Yes for**: read-path credential/context resolution; read-path tenant isolation across 14 boundaries with 0 cross-tenant ALLOWs; the deny-shape vocabulary; the existence, wiring and gating of the audited surfaces; the `staff_roles` capability-data state; the composition of the processing queue and the modelled state machine. |
| **UNVERIFIED** | Pipeline end-to-end completion; **all** write paths; the ≈1,185-identity population; the PE review branch; the staff-admin/system-admin boundary; identifier masking; production parity (§18). |
| **ACCEPTED** | **Not claimed.** The product is neither accepted nor rejected here: two of its most consequential regions (customer readability of their own data; pipeline completion) could not be observed. |

### 23.1 Severity roll-up

| Severity | Items |
|---|---|
| `HIGH` | FIND-9.8, FIND-9.9, FIND-9.10, FIND-9.11, FIND-9.13, PR-01, PR-02, PR-03, PR-04 |
| `MEDIUM` | FIND-9.1, FIND-9.2, FIND-9.3, FIND-9.4, FIND-9.5, FIND-9.6, FIND-9.7, FIND-9.12, FIND-9.14, PR-05, PR-06, PR-07 |
| `INFO` | §15 environment fidelity; §17.2 queue composition; §6 permission inventory |

FIND-9.13 is the acute functional form of PR-01; FIND-9.2/9.3/9.4/9.7 are facets of §21's capability-ownership finding. The classification column on each finding remains authoritative where a finding spans classes.

### 23.2 Verdict

The audited CarbonTally stack is **substantially built and strictly, consistently isolated**, and it is **not yet operable as a single business journey**. Its authorization model is a genuine strength: 460 probes produced zero cross-tenant allowances, and the deny vocabulary explicitly distinguishes missing-authentication, wrong-domain and insufficient-permission cases. Its product-reality weakness is the mirror image of that strength: the capability set is fragmented across identities, the commercial vocabulary is unresolved in four registers at once, and handoffs between roles terminate rather than transfer. The three `HIGH` permission gaps (PR-01/02/03) are, on the evidence in §14, an artefact of **environment provisioning** rather than broken authorization — a materially more tractable finding than the headline reads, but one whose *policy* resolution (who should hold the capability) is a PO decision.

### 23.3 Next actions, in order

1. **U-01 and U-09** — the two probes that convert the largest `UNVERIFIED` regions into `PASS`/`FAIL` (customer readability of `documents`/`emissions`; end-to-end pipeline completion).
2. **PD-01 … PD-04** to the Product Owner — platform operator, QC owner, commercial owner, journey ownership; three of the `HIGH` findings are blocked on them.
3. **§19's no-PO-decision backlog** to Cline (FIND-9.5, 9.6, 9.12, 9.13, PR-01/02/03 *mechanism*, PR-07 after U-13).
4. Re-run this matrix in the **investor-demo environment** to satisfy `AGENTS.md` §56 (U-06).

---

## Appendix A — 46 endpoints × 10 personas (raw runtime result)

Persona keys: **A** `platform_admin` · **B** `internal_operator` · **C** `pe_manager` (Alpha) · **D** `pe_beta_manager` (Beta) · **E** `org_a_owner` · **F** `org_a_viewer` · **G** `consultant_owner` · **H** `consultant_member` · **I** `client_a_owner` · **J** `client_b_owner`. All requests `GET`. Source: `/tmp/p5_matrix.txt`.

| # | Endpoint (gate) | A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `/ops/dashboard` (`can_view_all`) | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 2 | `/ops/organizations` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 3 | `/ops/staff` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 4 | `/ops/staff-roles` | **200** | **200** | **200** | **200** | 403 | 403 | 403 | 403 | 403 | 403 |
| 5 | `/ops/operational-intelligence` (`can_view_all`) | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 6 | `/ops/operational-health/queue` (`can_view_all`) | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 7 | `/ops/queues/operator` (`can_process`) | 403 | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 8 | `/ops/queues/review` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 9 | `/ops/queues/qc` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 10 | `/ops/qc/ct-queue` (`can_qc`) | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 11 | `/ops/reporting/platform` (`can_view_all`) | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 12 | `/ops/reporting/review` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 13 | `/ops/reporting/qc` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 14 | `/ops/reporting/audit` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 15 | `/ops/reporting/aging` (`can_view_all`) | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 16 | `/ops/entities/{PE_ALPHA}/dashboard` | 200 | 200 | 200 | **403** | 403 | 403 | 403 | 403 | 403 | 403 |
| 17 | `/ops/entities/{PE_ALPHA}/extraction/batches` | 403 | 200 | 200 | **403** | 403 | 403 | 403 | 403 | 403 | 403 |
| 18 | `/admin/review-queue` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 19 | `/admin/manual-processing/state?scope…` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 20 | `/admin/manual-processing/organizations` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 21 | `/admin/manual-processing/effective/{ORG_A}` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 22 | `/admin/manual-processing/clients/{ORG_A}` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 23 | `/admin/entities` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 24 | `/admin/sla/settings` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 25 | `/admin/backups/status` (`can_manage_backups`) | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 26 | `/pe/me` | 403 | 403 | 200 | 200 | 403 | 403 | 403 | 403 | 403 | 403 |
| 27 | `/pe/work` | 403 | 403 | 200 | 200 | 403 | 403 | 403 | 403 | 403 | 403 |
| 28 | `/pe/team` | 403 | 403 | 200 | 200 | 403 | 403 | 403 | 403 | 403 | 403 |
| 29 | `/pe/issues` | 403 | 403 | 200 | 200 | 403 | 403 | 403 | 403 | 403 | 403 |
| 30 | `/processing/queue` | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 |
| 31 | `/processing/dashboard` | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 |
| 32 | `/processing/customer-review` | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 |
| 33 | `/qc/queue` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 34 | `/messaging/conversations` | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 | 422 |
| 35 | `/consultants/me` | 403 | 403 | 403 | 403 | 403 | 403 | 200 | 200 | 403 | 403 |
| 36 | `/consultants/me/manual-processing/coverage` | 403 | 403 | 403 | 403 | 403 | 403 | 200 | 200 | 403 | 403 |
| 37 | `/organizations/{ORG_A}/profile` | 403 | 403 | 403 | 403 | 200 | 200 | 403 | 403 | 403 | 403 |
| 38 | `/organizations/{ORG_A}/members` | 403 | 403 | 403 | 403 | 200 | 200 | 403 | 403 | 403 | 403 |
| 39 | `/organizations/{ORG_A}/manual-processing` | 403 | 403 | 403 | 403 | 200 | 200 | 403 | 403 | 403 | 403 |
| 40 | `/accounting/context` | 422 | 422 | 403 | 403 | 200 | 200 | 422 | 422 | 200 | 200 |
| 41 | `/commercial/entitlement/{ORG_A}` | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 42 | `/billing/me` | 403 | 403 | 403 | 403 | 200 | 200 | 403 | 403 | 200 | 200 |
| 43 | `/settings/retention` | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 |
| 44 | `/settings/analytics` | **200** | **200** | **200** | **200** | **200** | **200** | **200** | **200** | **200** | **200** |
| 45 | `/emissions/dashboard` | 403 | 403 | 403 | 403 | 422 | 422 | 403 | 403 | 422 | 422 |
| 46 | `/documents` | 403 | 403 | 403 | 403 | 422 | 422 | 403 | 403 | 422 | 422 |

**Column totals** — A: 19×200 / 22×403 / 5×422; B: 5/36/5; C: 8/34/4; D: 6/36/4; E: 6/34/6; F: 6/34/6; G: 3/38/5; H: 3/38/5; I: 3/37/6; J: 3/37/6.

**Bold** marks the two over-permission rows (4 and 44) and the two PE-isolation rows (16 and 17, where Beta is denied Alpha's work).

---

## Appendix B — Method and evidence artefacts

### B.1 Method

| Step | Mechanism | Artefact |
|---|---|---|
| Identity/context resolution | 14 contexts resolved (10 personas + 4 negative/edge contexts) via the live auth flow | `/tmp/aud_head.txt`, `/tmp/aud_probe5.txt` |
| Persona × endpoint probe | 46 GET endpoints × 10 personas = 460 requests; status codes tabulated | `/tmp/p5_matrix.txt`, `/tmp/aud_probe5.txt` |
| Isolation assertions | 18 deny-required probes, matched against expected deny | §16 |
| Permission inventory | Read-only SQL against `staff_roles`, `staff_profiles` | `/tmp/roles.txt`, `/tmp/roles2.txt` |
| Permission vocabulary | `grep` over `backend/`, `frontend/src/`, `supabase/migrations/`, `tools/` | `/tmp/g1.txt`, `/tmp/g3.txt`, `/tmp/g4.txt` |
| Entitlement/provisioning root cause | `provision.py` source + `staff_roles.updated_at` clustering | `/tmp/mig2.txt`, `/tmp/roles2.txt` |
| Schema/state-machine read | `information_schema.columns`, `pg_constraint` on `document_processing_queue` | `/tmp/q17.txt`, `/tmp/q17b.txt` |
| Row counts | Read-only SQL counts across 9 tables | `/tmp/cnt2.txt`, `/tmp/cnt.txt` |
| Earlier evidence passes | Audit transcripts retained | `/tmp/aud_e8–e11.txt`, `/tmp/aud_mat.txt`, `/tmp/aud_pr.txt`, `/tmp/aud_perm3.txt` |

### B.2 Repository files cited

`docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md` · `docs/Pricing/CARBONTALLY_ASSISTED_AND_MANAGED_PROCESSING_SPECIFICATION_V1(1).md` · `docs/architecture/carbontally_master_handover_2026-10-05.md` · `frontend/src/v3/api.js` · `frontend/src/v3/ops/{SettingsTab,OperationsPage,OpsAssignmentsTab,CommercialTab,ManualProcessingTab,ManualProcessingCoverageTab}.jsx` · `frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx` · `frontend/src/v3/customer/{BillingPage,ManualProcessingPage}.jsx` · `frontend/src/v3/admin/AdminPage.jsx` · `frontend/src/public/{ServicesPage,PricingPage,faqData}.jsx` · `backend/auth.py` · `backend/api/{v3_operations,v3_commercial,v3_billing,v3_reporting,insight_authz}.py` · `backend/data/billing.py` · `backend/services/billing.py` · `tools/demo_lab/provision.py` · `supabase/migrations/20260824020000_…`, `20260828010000_…`, `20260828020000_…`, `20260902020000_…`, `20261026000000_…`.

### B.3 Database queries used (read-only, illustrative)

```sql
-- capability data
SELECT name, permissions::text FROM staff_roles ORDER BY name;
SELECT p.first_name, r.name, p.entity_id IS NULL AS internal
  FROM staff_profiles p JOIN staff_roles r ON r.id = p.role_id;
-- pipeline state
SELECT status, count(*) FROM document_processing_queue GROUP BY 1 ORDER BY 2 DESC;
SELECT pg_get_constraintdef(oid) FROM pg_constraint
 WHERE conrelid = 'public.document_processing_queue'::regclass AND contype = 'c';
-- environment population
SELECT 'auth_users', count(*) FROM auth.users
UNION ALL SELECT 'organizations', count(*) FROM organizations;
```

No credentials, tokens or signed URLs are recorded in this report (`AGENTS.md` §78).

---

## Appendix C — Read-only compliance, Git state and change record

### C.1 Change record — the audit added exactly one artefact

| Path | Status | Note |
|---|---|---|
| `docs/architecture/CT-PRODUCT-REALITY-AUDIT-01.md` | **new, untracked** | This report. The only file this work created. |

**No other file was created, modified, moved or deleted by this audit.** No code, migration, SQL, configuration, RLS policy, seed or demo data was altered. No commit was made; no branch was changed; no history was rewritten (`AGENTS.md` §70).

### C.2 Git state at time of writing

| Item | Value |
|---|---|
| HEAD | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| Branch | `p8-release-reconciled` |
| Working tree | **already dirty on entry** — 42 modified tracked files and ≈100 untracked files, all pre-existing from earlier work; **none touched by this audit** |
| `.env` / secrets added | none |

### C.3 Important caveat — citations are against the **working tree**, not HEAD

Several cited files carry uncommitted local modifications, so their line numbers and content reflect the working tree. Most materially:

| File | Relevance to this report |
|---|---|
| `docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md` | The entitlement sentence quoted in FIND-9.11 is an **added (`+`) line in `git diff`** and does **not** exist in `git show HEAD:…`; the equivalent rule *is* committed in `backend/domain/manual_processing.py` (item 7 now cites the code for this reason) |
| `backend/api/v3_operations.py` | Cited for `can_view_all` gates (`:688-690`, `:766`) — working-tree revision |
| `frontend/src/v3/ops/OperationsPage.jsx` | Cited for the Commercial-tab gate (`:135-136`) and the Assignments tab (`:89-92`) — working-tree revision |
| `frontend/src/v3/api.js`, `tools/demo_lab/stack.py`, `backend/api/manual_processing_*.py` | Working-tree revision |

**Recommendation.** Freeze a checkpoint commit before the next audit pass so every citation can be pinned to a SHA (`AGENTS.md` §2: current Git source is a lower-order truth than runtime and database state, and both were read directly here).

### C.4 Read-only verification of method

| Operation class | Used? | Evidence |
|---|---|---|
| `SELECT` / `information_schema` / `pg_constraint` queries | **Yes** | All SQL in Appendix B.3 is a read |
| `INSERT` / `UPDATE` / `DELETE` / DDL | **No** | No write statement was issued against any database |
| API writes (`POST`/`PUT`/`PATCH`/`DELETE`) | **No** | The probe matrix is GET-only |
| File writes inside the repository | **Yes, once** | This report only |
| Ephemeral artefacts outside the repository | Yes | `/tmp/*` transcripts (Appendix B.1), never committed |
| Credential/token/signed-URL handling | None recorded | Local DSN referenced by port only; no secrets in this report |

**Statement.** This work complies with the read-only mandate: it inspected, measured and reported. Every remediation in §19 is a *proposal*; none was applied.

---

*End of report — CT-PRODUCT-REALITY-AUDIT-01.*















