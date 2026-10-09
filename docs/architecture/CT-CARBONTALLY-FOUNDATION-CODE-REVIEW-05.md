# CT-CARBONTALLY-FOUNDATION-CODE-REVIEW-05

**Review type** Independent read-only code review of the *uncommitted change set*
in `ct_93d5cdd` (branch `p8-release-reconciled`), carried out in the
Foundation-series numbering after `-01 BASELINE`, `-02 INVENTORY`,
`-03 VERIFICATION`, `-04 DOCS-INTENT`.

**Three tasks**

| Task | Question |
|---|---|
| T1 | Resolve the **154 vs 141** Demo-Lab table-count discrepancy (**B-16**) with a mechanism, not a preference |
| T2 | Judge the **modified / untracked change set** workstream by workstream |
| T3 | Give a **commit-readiness verdict** (**PD-E1**): what may be committed, what must not, in what order |

**Environment / state at review time**

| Item | Value |
|---|---|
| Git HEAD | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| Branch | `p8-release-reconciled` |
| Worktree | dirty (see §2.1) — no stash, no reset, no checkout, no file mutated by this review |
| Backend interpreter | `backend/.venv/bin/python` (pytest 9.1.1) |
| Frontend toolchain | CRA/Jest 27 + `react-router-dom` 7.18.x (jsdom) |
| Live DB inspected | `carbontally_demo_local` in the running container `supabase_db_carbon_ledger` (read-only SQL) |
| Review method | `git status/diff/show`, source inspection, read-only SQL, targeted pytest/jest runs |
| Only artefact written | **this document** |

> This review is a *measurement of the current worktree*. It is not an
> acceptance of the investor demo, and it does not claim any runtime behaviour
> beyond the commands and SQL recorded here.

---

## 0. Method, evidence and limits

**How evidence is labelled, per AGENTS.md §73/§80.**

* **[MEASURED]** — produced by a command or read-only SQL run during this review.
* **[INSPECTED]** — established by reading current source/Git objects.
* **[REASONED]** — derived by inspection without execution; explicitly not a
  proof of runtime behaviour.

Every finding distinguishes **IMPLEMENTED**, **TESTED** and **VERIFIED**. No
item in this document is claimed **ACCEPTED**.

**Limits.**

1. No destructive or state-changing command was run: no `stash`, `reset`,
   `clean`, `checkout`, `commit`, `add`, `worktree`, migration replay, or DB
   write. The investor demo database was read, never mutated (AGENTS.md §55).
2. Authenticated browser QA of the changed frontend was **not** in scope for
   this review and is **not** claimed; frontend evidence is test-suite and
   source based only.
3. Security findings marked **[REASONED]** were **not reproduced with a live
   ALLOW/DENY request pair**. They are candidates, not confirmed
   vulnerabilities, and are recorded as such.
4. No API surface was exercised over HTTP; no OpenAPI diff was taken.

**Reproducing the [MEASURED] items.** Session captures for the measured evidence
are written under `/tmp/cr_*` and are ephemeral; the command that produced each
one is quoted at the point of use (§1.2 for the T1 table counts, §2.3 for
`/tmp/cr_migscan.txt`, §2.5 for `/tmp/cr_junit3.xml`). Anyone re-running this
review should re-derive them rather than trust the captures.

---

## 1. TASK 1 — the 154 vs 141 Demo-Lab table-count discrepancy (**B-16**)

### 1.1 The two claims

**[MEASURED]** `CT-CARBONTALLY-FOUNDATION-BASELINE-01.md` lines 348, 385, 466,
522, 657, 852; `-INVENTORY-02.md` lines 54, 69, 654, 1164;
`-VERIFICATION-03.md` line 84 — all state **154** public tables for
`carbontally_demo_local` (alongside 135 for `ct_local_93d5cdd`).

**[MEASURED]** The census/reconciliation generation
(`CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:224,226,268,316`,
`...-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION-20260927.md:466`,
`...-DATABASE-RECONCILIATION-20260927-REPORT.md:217`,
`...-DATABASE-RECONCILIATION-LEDGER-20260927.md:40,297`,
`...-GAP-ANALYSIS-20260927.md:126`,
`...-SCHEMA-COMPARISON-MATRIX-20260927.md:34`,
`CT-FINAL-02-20261001-LIVE-EVIDENCE-CLOSURE-PASS-REPORT.md:225`,
`CT-PO-CARBONTALLY-FEATURE-DELTA-CHANGELOG-20261003.md:274`,
`CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md:62`) —
states **141** for the same database.

`CT-CARBONTALLY-FOUNDATION-DOCS-INTENT-04.md:627` already carries a section
titled *"The Demo Lab's table count: 136 vs 141 vs 154"* and concludes at line
852 that 154 *"appears only as a Phase-1/2/3 measurement, never as an
expectation"*. The discrepancy is therefore **acknowledged but never
mechanised**. This review supplies the mechanism.

### 1.2 Mechanism (decisive)

**[MEASURED]** `public` base-table counts, every database in the running cluster:

| Database | public base tables |
|---|---|
| `postgres` (flagship) | 116 |
| `ct_local_93d5cdd` | 135 |
| `ct_p17m_verify_20260926` | 139 |
| `ct_iv_p17m_20260926` | **141** |
| `ct_final02_src` | 149 |
| `carbontally_demo_local` (live Demo Lab) | **154** |

**[MEASURED]** `carbontally_demo_local` − `ct_iv_p17m_20260926` = **exactly 13
tables**; `ct_iv_p17m_20260926` − `carbontally_demo_local` = **empty**.
Nothing was dropped — the schema only grew.

**Mechanism (a) — a dated-snapshot difference, not a contradiction:**

* **141** is the count of the **2026-09-26 census snapshot database**
  (`ct_iv_p17m_20260926`, whose name carries the date; it was created for the
  P17-M independent verification). The Step-2 canonical record, the whole
  2026-09-27 census family, the 2026-10-01 live-evidence closure pass and the
  2026-10-03 feature-delta changelog quote **that** generation.
* **154** is the count of the **current** `carbontally_demo_local`, i.e. after
  migrations dated **2026-10-11 … 2026-11-03** were replayed into it. The
  Foundation Phase-1/2/3 documents measure the current database and are
  mutually consistent.
* The intermediate snapshots (`135 → 139 → 141 → 149 → 154`) form a **monotone
  ladder**: 141 is simply an earlier rung of the same running schema.

**Why the number moves at all — the Demo Lab has no migration ledger.**
**[MEASURED]** `supabase_migrations.schema_migrations` does not exist in the
Demo Lab (ledger probe: 0 rows / no relation). The Lab is provisioned by
replaying `supabase/migrations/*.sql` (cf. `tools/demo_lab/stack.py`), so its
public-table count is whatever the last replay produced — including files still
**untracked in Git**. A count taken on 2026-09-26 could not have included
migrations authored in October/November.

**Physical-creation corroboration [MEASURED].** Each delta table carries a high
`relfilenode` (`scope3_categories` 739291, `report_shares` 739367,
`backup_jobs` 739526, `manual_processing_processors` 742524,
`consultant_mp_allocations` 742545) while the long-standing tables are far lower
(`organizations` 518681, `emission_factors` 518963,
`manual_processing_grants` 521685). The 13 tables were physically created later
than the 141-table generation, exactly as the dated-migration explanation
predicts. `relfilenode` ordering can be perturbed by `VACUUM FULL`/rewrites, so
this is stated as corroboration, not proof.

### 1.3 The 13 delta tables, with their creating migration

**[MEASURED]** every delta table has `relrowsecurity = true`; row counts are from
the live Demo Lab.

| # | Table | Creating migration | Migration tracked? | Rows |
|---|---|---|---|---|
| 1 | `contractual_instruments` | `20261011000000_p17c_contractual_instruments_and_allocations.sql` | tracked | 0 |
| 2 | `instrument_allocations` | `20261011000000_p17c_contractual_instruments_and_allocations.sql` | tracked | 0 |
| 3 | `scope3_categories` | `20261012000000_p17d_scope3_category_taxonomy.sql` | tracked | 15 |
| 4 | `estimation_records` | `20261013000000_p17h_estimation_and_assumption_records.sql` | tracked | 0 |
| 5 | `report_share_access_events` | `20261022000000_ct02_report_sharing.sql` | tracked | 0 |
| 6 | `report_shares` | `20261022000000_ct02_report_sharing.sql` | tracked | 0 |
| 7 | `report_schedule_definitions` | `20261023000000_ct02_scheduled_reporting.sql` | tracked | 0 |
| 8 | `report_schedule_runs` | `20261023000000_ct02_scheduled_reporting.sql` | tracked | 0 |
| 9 | `backup_jobs` | `20261026000000_ct_backup_01_backup_jobs.sql` | tracked | 0 |
| 10 | `manual_processing_processors` | `20261030000000_manual_processing_routing.sql` | **untracked** | 1 |
| 11 | `consultant_mp_allocations` | `20261101000000_ct_mp_sub_003_consultant_coverage.sql` | **untracked** | 13 |
| 12 | `consultant_mode_change_requests` | `20261103000000_ct_consultant_model_03_client_access_and_mode.sql` | **untracked** | 2 |
| 13 | `consultant_relationship_requests` | `20261103000000_ct_consultant_model_03_client_access_and_mode.sql` | **untracked** | 0 |

Arithmetic: **141 + 13 = 154**, and all 13 creating migrations postdate the
2026-09-26 snapshot. 9 of the 13 tables come from **tracked** migrations
(P17-C ×2, P17-D, P17-H, CT-02 ×4, CT-BACKUP-01); **4** come from **untracked**
migrations (one from `20261030`, one from `20261101`, two from `20261103`).
`20261102000000_ct_consultant_model_02_capability_admission.sql` is also
untracked but creates **no** base table — it is a catalogue/admission migration —
which is why 5 untracked migrations yield only 4 tables.

**[MEASURED] Row counts matter:** the delta is not an empty scaffold —
`consultant_mp_allocations` (13), `scope3_categories` (15),
`consultant_mode_change_requests` (2) and `manual_processing_processors` (1)
carry live Demo-Lab fixture data. Committing the migrations must therefore not
require a reseed. **[INSPECTED]** the migrations are additive DDL; `20261030`
contains its `DROP TABLE IF EXISTS public.manual_processing_processors` only
inside a **commented** manual-ROLLBACK block, so replay is non-destructive.

### 1.4 T1 outcome

| Statement | Verdict |
|---|---|
| 141 is wrong | **No** — correct for the 2026-09-26 snapshot generation |
| 154 is wrong | **No** — correct for the current Demo Lab; corroborated live this review (154 tables, 154/154 RLS-enabled, 355 policies) |
| B-16 root cause | Dated snapshots of a growing schema quoted side by side without database name or measurement date; the Lab has no ledger, so its count is a moving target |
| Real defect | Presentation/attribution — **not** missing data. Affected documents must name the database **and** the measurement date, or say "current" |
| Residual risk | Until the five untracked migrations are committed, no document's count is reproducible from Git alone (§2.3, §3.2) |

**Documentation actions (annotate measurements — do not rewrite them).**

1. `-01 BASELINE`, `-02 INVENTORY`, `-03 VERIFICATION`: annotate 154 as
   *"current Demo Lab, 2026-10-08 review; 141 = 2026-09-26 snapshot"*.
2. The 2026-09-27 / 10-01 / 10-03 census family: annotate 141 as
   *"`ct_iv_p17m_20260926` snapshot, 2026-09-26"*.
3. `-04 DOCS-INTENT-04` §3.1: replace the open "136 vs 141 vs 154" question with
   the 13-table reconciliation of §1.3 and cross-reference this document.
4. Do **not** promote 154 to an "expected" count. It is an observation of the
   current replay state and changes with the next migration (AGENTS.md §74 — a
   table count is not a business outcome).

**B-16 status after this review: RESOLVED (mechanism established, 13-table delta
enumerated, both figures upheld).** Residual action is documentation annotation
only.

---

## 2. TASK 2 — review of the modified / untracked change set

### 2.1 Inventory (what is actually in the worktree)

**[MEASURED]** `git status --porcelain --untracked-files=all` at HEAD
`3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`:

| Category | Count | Composition |
|---|---|---|
| Tracked **modified** (total) | **78** | 45 backend (incl. 18 test files) · 24 frontend · 6 `tools/demo_lab` · `.gitignore` · 2 docs |
| — of which code/test | 76 | as above, minus the 2 docs |
| — of which docs | 2 | `CARBONTALLY_PE_VALIDATION_WORKFLOW_DECISION.md`, `docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md` |
| **Untracked** (total) | **195** | 114 `docs/` · 31 `backend/` · 24 `frontend/` · 14 `tools/` · 5 `supabase/` · 7 other |
| — non-doc code/test/sql/tools | **73** | 30 backend · 24 frontend · 5 migrations · 14 tools |
| — new **test** files | **29** | 18 backend (`tests/unit/**`) · 11 frontend (`src/v3/__tests__`, `src/__tests__`) |
| — new **migrations** | **5** | `20261030`, `20261101`, `20261102`, `20261103`, `20261104` |
| — review artefacts / debris | 7 | `nohup.out` (0 B) · `=` (0 B) · `8` (0 B) · `.p18_audit_tmp/` · `.costrict/` · `costrict-p3-ov-01-independent-re-verification.txt` · `Research/` |

**Untracked, out of scope for commit-readiness:** the 114 untracked `docs/`
files (including the whole 2026-09/10 audit generation) and `Research/`. They
are review artefacts. They must be committed **separately** from code, if at
all, because they are not required by any runtime dependency (§2.3).

**Compile-time dependency reality [MEASURED]** — the reason this is not a
"pick and choose" change set:

* **17** tracked-modified backend modules import **12** untracked backend
  modules. The most-depended-on are `api/client_access_guard` (7 importers:
  `v3_organizations`, `v3_vehicles`, `v3_automatic_processing`,
  `v3_manual_extraction`, `v3_processing_workflow`, `upload_gate`, `v3_context`),
  `domain/relationship_access` (7), `services/manual_processing_routing` (6),
  `domain/consultant_entitlement` (5), `services/manual_processing_notifications`
  (4), plus `api/v3_client_portal`, `api/client_portal_auth`,
  `api/admin_consultant_commercial`, `domain/client_identity`,
  `domain/consultant_retention`, `services/client_invitations`,
  `api/v3_manual_processing_coverage`.
* **10** tracked-modified frontend modules import **12** untracked frontend
  modules: `App.js` → `AcceptInvitation`, `v3/consultant/ClientOrgShell`,
  `v3/portal/ClientPortal`; `v3/components/V3Layout.jsx`,
  `v3/customer/ProcessingItemWorkspace.jsx`, `v3/customer/ReviewDetailPage.jsx`
  → `v3/clientAccess`; `v3/consultant/ConsultantPage.jsx`,
  `v3/customer/DashboardPage.jsx`, `v3/customer/ManualProcessingPage.jsx`
  → `ConsultantClientContext`; `v3/admin/AdminPage.jsx`,
  `v3/admin/FacilitiesTab.jsx`, `v3/customer/DocumentsPage.jsx`,
  `v3/ops/OperationsPage.jsx` → the untracked tabs/panels.
* 3 tracked-modified backend modules import code that exists **only** in
  **untracked migrations** (`manual_processing_routing` →
  `manual_processing_processors`; consultant coverage → `consultant_mp_allocations`;
  consultant model-03 → `consultant_mode_change_requests` /
  `consultant_relationship_requests`).

**[REASONED]** Therefore *any* commit of the tracked-modified files **without**
their untracked counterparts produces a tree that fails at import time
(`ModuleNotFoundError`) or at first query (`relation does not exist`). Selective
committing is not available. See §3.2 and §4.

### 2.2 Per-workstream review

**[MEASURED/INSPECTED]** The change set resolves into eight workstreams. The
identifying evidence is the `CT-*` markers carried by the untracked test files
and the migrations, plus the binding sites of the new guards.

| # | Workstream (evidence markers) | Principal files | What it does | Verdict |
|---|---|---|---|---|
| **WS-1** | `CT-CONSULTANT-MODEL-02/03` (`test_ct_consultant_model_02/03`, migrations `20261102`/`20261103`) | U: `domain/consultant_entitlement.py`, `domain/consultant_retention.py`, `api/admin_consultant_commercial.py`, `services/client_invitations.py`, 2 migrations · M: `v3_consultants.py`, `consultant_auth.py`, `dependencies.py`, `data/consultants.py`, `data/invitations.py`, `domain/partners.py`, `domain/branding.py`, `router.py`, `auth.py` | Consultant product modes/entitlements/capability admission, commercial admin, retention policy, consultant relationship-change requests | **ACCEPT** (code+test present; §2.5) |
| **WS-2** | `CT-CONSULTANT-CLIENT-IDENTITY-04` (`test_ct_consultant_client_identity_04`, migration `20261104`) | U: `domain/client_identity.py`, migration `20261104` · M: `v3_organizations.py`, `v3_consultants.py`, `data/organizations.py`, `services/client_invitations.py` (shared with WS-1) · FE U: `AcceptInvitation.jsx`, `AcceptInvitation.css`, `accept-invitation.test.jsx` | Client identity / invitation lifecycle, resolved server-side, with a real invitation-acceptance route replacing the placeholder | **ACCEPT** |
| **WS-3** | `CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05` / `CLOSURE-05A` (`client_access_guard.py`, `test_ct_client_plane_auth_05`, `…_closure_05a`) | U: `api/client_access_guard.py`, `domain/relationship_access.py`, `api/client_portal_auth.py`, `api/v3_client_portal.py`, FE `clientAccess.jsx`, `portal/ClientPortal.jsx`, `portal.css` · M (**binding sites**): `v3_organizations.py` ×6, `v3_vehicles.py` ×3, `upload_gate.py`, `v3_manual_extraction.py`, `v3_processing_workflow.py` ×2, `v3_automatic_processing.py` ×2, `v3_context.py` | The client-access **ceiling** (`RELATIONSHIP ∩ PROFILE ∩ ROLE ∩ ENTITLEMENT`) applied server-side on the **organisation** plane, so a consultant-managed client's users cannot inherit direct-customer assumptions | **ACCEPT** — highest-value workstream; see §2.4 for its known incompleteness |
| **WS-4** | `UX-01A` / `ORG-PARITY-01` / `NAV-01A` / team capabilities | U FE: `consultant/ClientAccessTab.jsx`, `ClientOrgShell.jsx`, `ConsultantClientContext.jsx`, `consultant/ManualProcessingCoverageTab.jsx`, `ClientMessagingTab.jsx` · M FE: `ConsultantPage.jsx`, `ConsultantTeamTab.jsx`, `ConsultantItemPage.jsx`, `DashboardPage.jsx`, `V3Layout.jsx`, `admin/AdminPage.jsx`, `admin/MembersTab.jsx`, `admin/FacilitiesTab.jsx`, `admin.css`, `consultant.css`, `App.js` · M BE: `v3_reporting.py` (F-NAV-1 reporting scope) · U tools: `verify_consultant_*_browser.py` | Client-context navigation and consultant/client surface parity, so an operating consultant sees *which client* they are inside | **ACCEPT** (UI claims are test-level only, §0 limit 2) |
| **WS-5** | `CT-MP-SUB-003` / `004` + `FIN-06` (`20261030`, `20261101`) | U: `services/manual_processing_routing.py`, `services/manual_processing_notifications.py`, `api/v3_manual_processing_coverage.py`, 2 migrations, FE `ManualProcessingPage.jsx`, `ops/ManualProcessingTab.jsx`, `ops/ManualProcessingCoverageTab.jsx` · M: `manual_processing_admin.py`, `manual_processing_auth.py`, `v3_operations.py`, `v3_documents.py`, `workers/automatic_processing.py`, `data/manual_processing.py`, `domain/manual_processing.py`, `services/work_items.py`, `ops/OperationsPage.jsx` | Manual-processing **routing** (which processor gets a blocked job), consultant coverage/allocation, notifications, governance enforcement (FIN-06) | **ACCEPT** — the largest single workstream |
| **WS-6** | `CT-PO-UPLOAD-UNIFY-001` | U: FE `UploadDocumentsPanel.jsx`, `uploadsCopy.js`, `upload-documents-panel.test.jsx` · M: `v3_document_uploads.py`, `v3_documents.py`, `DocumentsPage.jsx`, `direct-upload.test.js`, storage-management tests | One upload surface + one copy source, replacing divergent upload paths | **ACCEPT** |
| **WS-7** | demo-lab / staff-role provisioning | M: `provision.py`, `verify.py`, `manifest.json`, `README.md`, `run_demo_lab.sh`, `stack.py` · U: `supervise_demo_lab.py`, `systemd/carbontally-demo-lab.service`, `fixture_*/verify_*` · U test: `tests/unit/tools/test_demo_lab_staff_role_provisioning.py` · M doc: `CARBONTALLY_PE_VALIDATION_WORKFLOW_DECISION.md` | Make the Demo Lab reproducible/supervised and provision staff roles coherently | **ACCEPT** (tooling; not runtime code) — `stack.py`/`manifest.json` are also the T1 replay path |
| **WS-8** | release hygiene | M: `.gitignore` (adds `.aider*` etc.), `frontend/package.json`, `frontend/src/setupTests.js` (TextEncoder/TextDecoder shim), `frontend/src/OnboardingPage.jsx` (removes the `V3` nav badge), `frontend/src/App.test.js`, `frontend/App_.js` | Housekeeping needed for the release tree | **ACCEPT with one hygiene finding** — `frontend/App_.js` (F-06) and the root debris (F-07) |

**Cross-workstream files [INSPECTED]** — deliberately shared, not duplicated:
`api/router.py` (mounts `v3_client_portal`), `api/v3_organizations.py` (WS-2
identity + WS-3 ceiling, 6 binding sites), `api/v3_consultants.py` (WS-1/2/4),
`services/client_invitations.py` (WS-1/2), `services/manual_processing_routing.py`
(WS-3 gating + WS-5 routing), `frontend/src/App.js` (routes for WS-2/4/3),
`frontend/src/v3/api.js` (WS-3/4/5/6 clients). No workstream re-implements
another's module; the one risk is *ordering of commits*, answered in §4.

### 2.3 Dependency on uncommitted work — the release rule

**The governing rule [INSPECTED].** `CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md`
§3 step 1 (lines 118–122) makes the release freeze conditional on the tree
containing *"the P2 file set and nothing unreviewed"* and states the stop
condition verbatim:

> **STOP: any untracked file that the release depends on.**

The same document's step 5 (lines 146–159) requires the unapplied migration set
to be **in-place and additive**: no `DELETE`/`TRUNCATE public.*`, no
unconditional `DROP TABLE`/`COLUMN`.

**F-01 — the change set violates the first rule if committed partially
[MEASURED].**

| Dependency class | Count | Consequence of a partial commit |
|---|---|---|
| Tracked-modified backend modules importing **untracked** backend modules | **17 files → 12 untracked modules** | `ModuleNotFoundError` at API import; the app fails to start |
| Tracked-modified frontend modules importing **untracked** frontend modules | **10 files → 12 untracked modules** | build failure |
| Tracked-modified backend code depending on tables created **only** by untracked migrations | 3 files (`manual_processing_routing`, consultant coverage, consultant model-03) | `relation does not exist` at first query |
| Untracked modules that are merely *extra* (tools/verifiers/fixtures) | 26 of 73 | safe to defer, but see §4 |

**Therefore:** a commit of the tracked-modified set alone is **not a valid
release state**; the untracked counterparts are not optional add-ons, they are
the other half of the same change. This is a commit-mechanics finding, not a
code defect — the correct resolution is to commit the dependent untracked files
**with** the modified files (§4.2), never to weaken the rule.

**Additive-migration check on the five untracked migrations [MEASURED]**
(`/tmp/cr_migscan.txt` — statement scan of each file):

| Migration | Destructive statements | Base tables created | RLS on new table |
|---|---|---|---|
| `20261030…_manual_processing_routing.sql` | **0** | `manual_processing_processors` (`IF NOT EXISTS`) | yes (l.117) |
| `20261101…_ct_mp_sub_003_consultant_coverage.sql` | **0** | `consultant_mp_allocations` | yes (l.126) |
| `20261102…_ct_consultant_model_02_capability_admission.sql` | **0** | none (catalogue/admission data) | n/a |
| `20261103…_ct_consultant_model_03_client_access_and_mode.sql` | **0** | `consultant_relationship_requests`, `consultant_mode_change_requests` | yes (l.156, l.197) |
| `20261104…_ct_consultant_client_identity_04.sql` | **0** | none | n/a |

**[MEASURED]** zero destructive statements across all five; every newly created
table enables RLS. The set satisfies the CT-FINAL-03 step-5 additive criterion.
The tracked/untracked boundary is confirmed by `git ls-files`: `20261028` and
`20261029` are **tracked**; `20261030`–`20261104` are **untracked**; no
migration in the reviewed range reuses or edits a historical timestamp.

### 2.4 Security assessment of the new ceiling (**B-17**) — and its limits

**What `WS-3` establishes [INSPECTED].** `api/client_access_guard.py` (untracked)
resolves a *ceiling* from authoritative rows and reuses the same pure policy
module Plane C uses (`domain/relationship_access.py`):

```
profile_allows(operation, profile, state)
  OFF           → reads: no;  writes: none
  READ_ONLY     → reads: yes; writes: {comment}
  COLLABORATIVE → reads: yes; writes: {comment, upload_document,
                                         edit_master_data,
                                         correct_submitted_data, approve_final}
  MANAGED       → reads: yes; writes: {comment}
  state = RETAINED_READ_ONLY → READS ONLY ("no WRITE of any kind, and no
                                messaging-send", PA-2/PA-3)
  CLIENT_FORBIDDEN_OPERATIONS = {map_factors, edit_mappings, recalculate} → always denied
  unknown operation → denied (fail closed)
```

It is a **ceiling, never a grant**: direct customers, consultants and
staff/PE users are unaffected, and the decision cannot weaken tenant isolation.

**Measured binding sites [MEASURED]** — `require_client_operation(...)` is used
in exactly two routers; `enforce_client_operation(...)` in four:

| Router | Operation bound | Sites |
|---|---|---|
| `v3_organizations.py` (org profile; **facilities** `add_facility` l.963 …) | `edit_master_data` | 969, 990, 1018, 1056, 1083, 1112 |
| `v3_vehicles.py` (create/update/remove) | `edit_master_data` | 85, 108, 137 |
| `upload_gate.py` | `upload_document` | 267–270 |
| `v3_manual_extraction.py` | `correct_submitted_data` | 166 |
| `v3_processing_workflow.py` | correct / approve | 484, 1021 |
| `v3_automatic_processing.py` | trigger / recalculate | 327, 503 |
| `v3_context.py` | read-op map for the UI (not a write gate) | 58–70 |

**F-03 (P2, candidate) — `edit_master_data` is bound on vehicles and facilities
but not on suppliers.** `api/v3_suppliers.py` guards create/update/delete with
`require_org_admin()` alone (l.70, l.128, l.146) and has **no** ceiling call,
while its sibling master-data writes `add_facility` (bound, `v3_organizations.py`
l.963/969) and `v3_vehicles` (bound) enforce `edit_master_data`. Because a
consultant-managed client's own users reach this same organisation plane, a
client-org user holding `admin` **inside their own organisation** whose profile
is `MANAGED` or `READ_ONLY` — profiles whose ceiling is `{comment}` only — can
still create, update and delete suppliers. **The same operation class is
enforced inconsistently within one workstream.**

**F-04 (P2, candidate) — messaging-send is unbound; the RETAINED rule is
unenforced.** `domain.relationship_access.profile_allows` denies `OP_COMMENT`
when the relationship state is `STATE_RETAINED_READ_ONLY` (the documented
PA-2/PA-3 *"no messaging-send"* rule). `api/v3_messaging.py` never consults the
ceiling: `_authorize_org_actor` (l.67) returns `org_member` for **any** member of
the organisation, and `create_conversation` (l.131) / `send_message` (l.252) are
gated on nothing stronger. A retained (post-termination, read-only) client
organisation's member can therefore still create conversations and post
messages on the org plane.

**F-05 (P2, candidate) — customer-factor writes are unbound and member-level.**
`api/customer_factors.py`: create (l.158/161) and update (l.270/274) are gated
by `require_org_member()` **only** — no role check, no ceiling — while
approve/deactivate use `require_org_admin()` (l.308/311, l.350/353). Under
AGENTS.md §15 an approved customer factor *takes precedence* over generic
CarbonTally factors, and under §16 approval is a PO-governed act; yet the
*creation/update* path is reachable by a `MANAGED`/`READ_ONLY` profile client
member and while the relationship is `RETAINED`.

**F-06 (design gap — PO DECISION REQUIRED).** `api/v3_reports.py` (13 writes:
report shares, schedules), `api/v3_billing.py` (5 writes: orders/approvals) and
`api/v3_disclosure.py` are writable organisation-plane surfaces for which the OP
vocabulary defines **no** operation. They cannot be bound to the ceiling without
inventing a product rule (§62). Options for the owner: (a) add explicit OPs
(e.g. `share_report`, `manage_schedule`, `purchase`), (b) classify them under
`edit_master_data`, or (c) rule that only owner/admin roles on an active profile
may use them. **No option is selected in this review.**

**Status of B-17.** Every item above sits in files that are **unmodified by this
change set** (`v3_suppliers.py`, `v3_messaging.py`, `customer_factors.py`,
`v3_reports.py`, `v3_billing.py`, `v3_disclosure.py` are all clean versus HEAD)
and the CLOSURE-05A test suite makes no all-router coverage claim. They are
therefore **pre-existing incompleteness, not a regression introduced by the
diff** — this change set strictly *reduces* the attack surface. They are
**[REASONED]**: no live ALLOW/DENY pair was executed (§0 limit 3). Recorded as
**B-17**, severity **P2**, to be scheduled as a follow-up with a per-operation
router census — explicitly **not** a reason to withhold this commit.

### 2.5 Test evidence — what was actually run

**Scope of evidence [MEASURED].** The unit of verification for this review is the
**34 backend test files that exercise the changed code paths** (consultant
model/plane/identity, manual-processing routing and FIN-06 governance, storage/
upload, org-scope authorization, demo-lab tooling) plus the **19 frontend suites**
touching the changed components. This is a targeted selection, not the whole
suite.

| Run | Selection | Result | Evidence |
|---|---|---|---|
| Backend (authoritative) | 34 files | **883 tests, 0 failures, 0 errors, 0 skipped** in 243.0 s | JUnit XML `/tmp/cr_junit3.xml` (`tests=883 failures=0 errors=0 skipped=0`) |
| Backend (independent repeat 1) | same 34 files | completed 100%, zero `F`/`E` characters in progress output, `EXIT=0` | `/tmp/cr_cssum2.txt`, `/tmp/cr_csrun2.txt` |
| Backend (independent repeat 2) | same 34 files | completed 100%, zero `FAILED`/`ERROR` lines; 883 dots (12 × 72 + 19) | `/tmp/cr_cstests2.txt` |
| Frontend (`jest`) | 19 suites | **196 tests passed, 19/19 suites, 0 failures**, 7.2 s, `EXIT=0` | `/tmp/cr_fe_new_tests.txt` |

**New test coverage in the change set [MEASURED]** — 29 new backend test files
(`tests/unit/api/`, `tests/unit/domain/`, `tests/unit/tools/`) and 8 new frontend
suites, including: `test_ct_client_plane_auth_05`, `…_closure_05a`,
`test_ct_consultant_model_02/03`, `…_client_identity_04`, `_closure_01`,
`_ux_01a_team_identity`, `_org_parity`, `test_ct_mp_sub_003_consultant_coverage`,
`test_ct_mp_sub_004_*` (coverage surfaces, notifications, prod-readiness),
`test_p6_2a/2b_1–4/2c/2d/2e`, `test_manual_processing_routing` (api + domain),
`test_upload_document_classification`, `test_demo_lab_staff_role_provisioning`;
frontend `client-access-guard`, `client-access-closure-05a`,
`consultant-client-access`, `consultant-client-org-shell`, `consultant-nav-plane`,
`consultant-team-capabilities`, `consultant-ux-navigation`,
`manual-processing-coverage`, `upload-documents-panel`, `accept-invitation`,
`client-portal`.

**Two disclosures about this evidence.**

1. **Known-red tests are excluded from the selection, deliberately and
   visibly.** The four `tests/unit/data/` migration pins and three
   `tests/unit/engines/test_extraction_suggestions.py` tests (§2.6) are **not** in
   the 34 files. They are pre-existing red; including them would make the run
   report `7 failed` and say nothing about this change set. The selection is
   therefore "the tests that cover the change", and the red set is reported
   separately rather than omitted.
2. **Frontend `console.error` output is harness noise, not failure.** The jest
   log shows `[CarbonTally] GET /api/v3/me/context → 500` and simulated network
   errors (`abandon endpoint unreachable`); these are produced *by* tests that
   deliberately exercise the error paths, and all 196 tests pass. Recorded here so
   the noise is not later mistaken for a defect (AGENTS.md §78).

**Also verified in this pass [MEASURED]:** no secret-bearing file is untracked or
modified (`git status --porcelain | grep -iE '\.env|credential|secret|token|\.pem|\.key'`
→ none); `tools/seed_investor_demo/DEMO_IDENTITIES.md`, `demo_manifest.json` and
`.demo_state.json` remain ignored by `.gitignore` in both revisions.

### 2.6 Red tests at the worktree — attributed, not waved away

A commit must not be judged against `main`'s CI if the worktree is currently
red. Seven tests fail in the working tree today. They split cleanly into two
groups, and **neither group is caused by the code being reviewed**.

**Group A — migration-order pins (4 failures, all `backend/tests/unit/data/`)**

| Test | Assertion (measured) | What broke it |
|---|---|---|
| `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | `assert 103 == 71` — migration count is a **hard-coded 71** | Count grows with *every* migration; `100+` files exist at HEAD |
| `test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | latest migration must equal the I1 file | `20261028`/`20261029` are later and are **at HEAD** |
| `test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | latest must equal `20261007…_p8_insight_data_quality_reproducibility.sql`; actual `20261104…_client_identity_04.sql` | latest-value pin |
| `test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | fails on `20261029…_ct_final_03_staff_workload_rls.sql` not being in the P16 expected set | a **tracked migration already at HEAD** |

**[MEASURED]** `git cat-file -e HEAD:…` proves `20261028` and `20261029` exist at
HEAD; `git status --porcelain supabase/migrations/` shows the directory contains
**only** five `??` files and **no modified** tracked migration. Each pin asserts a
literal baseline (count `71`, "latest = I1/I2/P16 set") that tracked migrations
at HEAD already violate. **[REASONED] on those measured values:** all four were
already failing before this change set; the diff changes the *failure value*
(`20261104…` instead of `20261007…`), not the failing status. No `git stash` or
other tree mutation was performed to demonstrate this — read-only discipline was
preferred (§0).

**Group B — extraction engine (3 failures, `test_extraction_suggestions.py`)** —
`test_suggest_parses_clean_invoice`, `…_missing_fields_leave_unresolved`,
`…_no_fabrication_on_garbage`. These are the **already-recorded B-01**
(P1) engine-vs-test drift (`CT-CARBONTALLY-FOUNDATION-BASELINE-01.md` §"any 'all
tests pass' statement about this repository is unverifiable"). The failure values
are date-format (`'2026-01-15'` vs `'15/01/2026'`) and `extraction_evidence`
assertions — the extraction layer is **not touched** by this change set
(`backend/engines/**` is clean versus HEAD).

**F-02 (P2 — release-hygiene, tracked as B-18).** Four migration-baseline pins
are stale and will stay red through this commit. They must be **updated in the
same commit** (the change set is exactly the kind of "later migration" the pins
detect), or explicitly deferred with a recorded owner decision. Leaving them red
while claiming a green suite would breach AGENTS.md §73/§74. Group B is
**out of scope** and remains **B-01**.

**What this means for judging the change set:** the correct red-test question is
*"does the change set introduce any new failure?"* — not *"is the suite green?"*
On the measured evidence, the change set introduces **no new failing test** and
**no previously-passing test is now failing** across the 34 backend test files
and 19 frontend suites selected for it (§2.5).

---

## 3. Task 3 — commit readiness (**PD-E1**)

### 3.1 The question

**PD-E1** asks: *is this change set ready to be committed, and if so, as what?*
Three answers are possible and they are not interchangeable:

* **READY** — committable as one coherent release increment;
* **READY WITH ORDERING CONSTRAINTS** — committable, but only in a stated order
  and only as one bundle;
* **NOT READY** — a blocker must be cleared first.

### 3.2 Per-workstream readiness

| Workstream | Code complete | Test coverage in set | Blocking dependency | Verdict |
|---|---|---|---|---|
| WS-1 consultant model 02/03 | yes | yes (`test_ct_consultant_model_02/03`, `_closure_01`, `_full_implementation_03`, p6_2d/2e) | migrations `20261102`/`20261103` + `domain/consultant_entitlement.py`, `_retention.py` (untracked) | **READY** (bundle) |
| WS-2 client identity 04 | yes | yes (`test_ct_consultant_client_identity_04`, `accept-invitation.test.jsx`) | migration `20261104` + `domain/client_identity.py` | **READY** (bundle) |
| WS-3 plane auth 05/05A | yes | yes (`test_ct_client_plane_auth_05`, `_closure_05a`, 2 FE suites) | `client_access_guard.py`, `relationship_access.py`, `client_portal_auth.py`, `v3_client_portal.py` (all untracked) | **READY** — **B-17** scheduled separately (P2, pre-existing) |
| WS-4 consultant/client UX + parity | yes | yes (5 FE suites, `test_consultant_org_parity`, `_ux_01a`) | FE components (untracked) + `v3_reporting.py` (modified) | **READY** |
| WS-5 MP routing / coverage / FIN-06 | yes | yes (8 backend files + 1 FE suite) | migrations `20261030`/`20261101` + 2 untracked services | **READY** (bundle) |
| WS-6 upload unify | yes | yes (`test_upload_document_classification`, `upload-documents-panel.test.jsx`) | `UploadDocumentsPanel.jsx`, `uploadsCopy.js` (untracked) | **READY** |
| WS-7 demo-lab / staff roles | yes | yes (`test_demo_lab_staff_role_provisioning.py`) | none (tooling only) | **READY** |
| WS-8 release hygiene | yes | n/a (config/docs) | none | **READY** — with the `.gitignore` caveat (§3.4) |

### 3.3 Verdict

> **PD-E1: READY WITH ORDERING CONSTRAINTS.**
>
> The change set is **commit-ready as one bundled increment, and is NOT
> commit-ready in any partial form** (F-01). Committing the tracked-modified
> files without their untracked counterparts is explicitly forbidden by
> `CT-FINAL-03` step 1 — *"STOP: any untracked file that the release depends
> on."* — and would break the application at import time.

### 3.4 Commit ordering, and four caveats to handle *in* the commit

**Required order (one bundle, ordered internally).** `CT-FINAL-03` wants *"one
clean commit SHA"*, so the ordering below is about **what must be true together**,
not about producing five commits:

1. **Migrations first (5 files)** — `20261030`, `20261101`, `20261102`,
   `20261103`, `20261104`. Additive, RLS-enabled on every new table (§2.3), so
   the database may be migrated before the new code runs.
2. **Backend domain/services/API modules** — the untracked modules, *together
   with* the tracked-modified modules that import them and the tables they
   query (F-01). Applying the migrations without this code leaves new tables
   unused; committing this code without the migrations breaks the queries.
3. **Backend tests** — in the same increment as the code they cover.
4. **Frontend components + suites** — `App.js`/`api.js` (modified) with the
   untracked components they import.
5. **Tools, verifiers, demo-lab, docs.**

**[MEASURED] Caveat 1 — `.gitignore` looks far bigger than it is.** The raw
diff is `108 added / 107 deleted`, which reads like a rewrite. It is not: the
semantic delta is **exactly one added pattern, `.aider*`**. HEAD's file uses
**CRLF** (107 CR lines); the worktree file uses **LF** (0 CR lines), so the EOL
normalisation makes every line appear changed. With `tr -d '\r'`, blank lines
removed and the sets sorted, the two files differ **only** by `1a2 > .aider*` —
**no ignore pattern was lost**. (Relevant because a silently dropped
`__pycache__`/`.env*`/`node_modules` rule would be a security-relevant hygiene
regression; it did not happen.)

**Caveat 2 — `frontend/App_.js` is dead-legacy (F-07 → B-19).** The entry point
is `frontend/src/App.js`; `frontend/App_.js` (repo root of the frontend package)
is dead legacy that two prior scoping passes flagged as ambiguous. It must be
either deliberately included with a recorded rationale or **dropped from the
commit** — it must not ride along unnoticed.

**Caveat 3 — do not sweep the repository root with `git add -A` (F-08 → B-20).**
The untracked surface still contains debris that is **not** part of any
workstream: 0-byte files `8` and `=` (dated 2026-09-23), `nohup.out`,
`.p18_audit_tmp/`, `.costrict/`, `costrict-p*.txt`, and `Research/`. The 114
untracked `docs/` files are a separate publication decision.

**Caveat 4 — the four migration pins (F-02 → B-18).** `test_d17_…_ordering_is_unchanged`,
`test_i1_…_is_the_latest_migration`, `test_i2_…_is_the_latest_and_scoped_to_one_policy`
and `test_p17_…does_not_reuse_or_edit_a_historical_timestamp` are stale and red
(§2.6). Update them in the same commit, or record an owner decision to defer —
do not commit while implying the suite is green.

**Verified absent [MEASURED]:** no `.env*`, credential, key or token file is
untracked or modified; `tools/seed_investor_demo/DEMO_IDENTITIES.md` and
`demo_manifest.json` remain ignored.

---

## 4. Cross-cutting checks

### 4.1 Does every workstream have code *and* a test?

**PASS.** All eight workstreams carry at least one test in the change set (§3.2).
The only workstream without tests is **WS-8 (release hygiene)**, and it is
configuration/docs only (`.gitignore`, `package.json`, `setupTests.js`, dead-code
removal) — no behavioural surface to test. No workstream was found with code
changes and no accompanying test.

### 4.2 Is the change set free of dependency on uncommitted work *as committed*?

**CONDITIONAL PASS.** Depends entirely on committing the bundle. Measured
dependencies (F-01): 17 tracked-modified backend modules import 12 untracked
backend modules; 10 tracked-modified frontend modules import 12 untracked
frontend modules; 3 modules query tables created only by untracked migrations.
Commit the bundle → **PASS**. Commit the tracked-modified subset alone →
**FAIL, hard** (application cannot import). There is no middle option: the
dependency graph makes selective commit impossible, which is why §3.3 reads
"one bundle, ordered".

### 4.3 Do the new code paths have tests?

**PASS.** 29 new backend test files + 8 new frontend suites, covering the new
modules and the new guard binding sites: `883` backend tests pass with `0`
failures/errors/skips, and `196` frontend tests pass across `19/19` suites
(§2.5). Coverage is claimed only for the surfaces the tests exercise — no
blanket "the platform is tested" claim is made, and the ceiling gaps in §2.4
are precisely the places where no test exists.

### 4.4 Does the change set conflict with any red test?

**PASS, with one maintenance obligation.** Seven tests are red in the worktree;
all seven were red *before* this change set (§2.6 — four stale migration pins
broken by migrations already at HEAD, three B-01 extraction-engine tests in an
untouched layer). No test that passes at HEAD fails because of this change set.
The obligation (F-02/B-18): the four pins detect exactly this kind of change and
must be updated in the same commit, or deferred by explicit decision.

### 4.5 Secrets and credentials

**PASS [MEASURED].** No `.env*`, credential, key, token or PEM file is untracked
or modified. `.gitignore`'s ignore set is unchanged except for one added pattern
(`.aider*`) — verified after stripping the CRLF/LF difference (§3.4 caveat 1).
The demo credential surfaces (`DEMO_IDENTITIES.md`, `demo_manifest.json`,
`.demo_state.json`) remain ignored in both revisions.

| Check | Verdict |
|---|---|
| 4.1 workstream code+test coverage | **PASS** |
| 4.2 no dependency on uncommitted work | **CONDITIONAL PASS** (bundle required) |
| 4.3 test presence on new paths | **PASS** |
| 4.4 no conflict with red tests | **PASS** + pin-update obligation |
| 4.5 secrets | **PASS** |

---

## 5. Findings register and close-out

### 5.1 Findings

| ID | Finding | Severity | Status | Evidence level |
|---|---|---|---|---|
| **F-01** | **Partial commit is impossible and forbidden.** Tracked-modified code depends on untracked modules and on tables created only by untracked migrations (17 backend modules → 12 untracked modules; 10 FE modules → 12 untracked modules; 3 modules → tables from `20261030`/`20261101`/`20261103`). The `CT-FINAL-03` step-1 stop condition applies. | **P1 (release process)** | **Confirmed** — resolved by bundling (§3.4) | MEASURED |
| **F-02** | **Four migration-order pins are stale and red** (`test_d17_…_ordering_is_unchanged`, `test_i1_…_is_the_latest_migration`, `test_i2_…_is_the_latest_and_scoped_to_one_policy`, `test_p17_…_does_not_reuse_or_edit_a_historical_timestamp`). Red before this change set; still red after it. | **P2** | Confirmed → **B-18** | MEASURED (+REASONED attribution) |
| **F-03** | **`edit_master_data` ceiling bound on facilities and vehicles but not on suppliers** — `v3_suppliers.py` create/update/delete use `require_org_admin()` only, so a `MANAGED`/`READ_ONLY`-profile admin inside a consultant-managed client org can still write suppliers. | **P2** | Candidate, pre-existing file → **B-17** | REASONED |
| **F-04** | **Messaging-send has no ceiling:** the documented PA-2/PA-3 *"no messaging-send"* rule for `RETAINED` relationships is unenforced — `v3_messaging.py` never calls the guard and `_authorize_org_actor` admits any org member. | **P2** | Candidate, pre-existing file → **B-17** | REASONED |
| **F-05** | **Customer-factor create/update is member-level and unbound** (`customer_factors.py` l.161/274 via `require_org_member()`) while approve/deactivate are admin-gated — under §15 factor precedence and §16 approval policy this is the wrong boundary. | **P2** | Candidate, pre-existing file → **B-17** | REASONED |
| **F-06** | **OP-vocabulary gap:** report sharing/scheduling, billing/orders and disclosure have no classified operation, so they cannot be placed under the ceiling without a product decision. | **P2 (design)** | **PO DECISION REQUIRED** | REASONED |
| **F-07** | **`frontend/App_.js`**: tracked, modified, 41,982 bytes, **no importer anywhere in `frontend/src`** — dead legacy. Must be included deliberately or dropped. | **P3 (hygiene)** | Confirmed → **B-19** | MEASURED |
| **F-08** | **Repository-root debris** must not be swept in by `git add -A`: `8`, `=`, `nohup.out`, `.p18_audit_tmp/`, `.costrict/`, `costrict-p3-ov-01-….txt`, `Research/` (all untracked, none owned by a workstream). | **P3 (hygiene)** | Confirmed → **B-20** | MEASURED |

**Register changes:** **B-16** — *closed* by T1 (§1). **B-17, B-18, B-19, B-20** —
newly raised. **B-01** — unchanged, out of scope.

### 5.2 Corrections to existing documentation

* The **154-table** figure is **not** a contradiction and **not** documentation
  drift: it is the current `carbontally_demo_local` state, exactly **13** tables
  ahead of the 141-table snapshot earlier reviews captured (§1).
* `CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md` **Q5** (table-count
  expectations) and `CT-CARBONTALLY-FOUNDATION-DOCS-INTENT-04.md` **Q7**
  (migration ledger) are correct as written — both are content-clean versus HEAD
  in this review. Q5 should be appended with the **154 / +13** delta, and any
  future count should name the database *and* the date.
* `frontend/App_.js` was flagged **ambiguous** in an earlier scoping pass; this
  review confirms it is **dead** (no importer), upgrading it from "ambiguous" to
  "drop or justify".

### 5.3 Read-only attestation

Gathered, not mutated. Counts before the review: **78 tracked-modified / 195
untracked**; after: **78 / 196** — the single added untracked file is **this
report**. The only other writes are `backend/.pytest_cache/**` (gitignored,
produced by the test runs for §2.5). No commit, stage, reset, stash, checkout,
database write, migration application or service start was performed. The
`nohup.out` at the repository root is **pre-existing** (mtime 2026-10-06), not
created here.

### 5.4 What this review does **not** claim

* **No acceptance verdict.** "READY WITH ORDERING CONSTRAINTS" is a commit
  assessment, not product acceptance (AGENTS.md §73). Nothing here states that an
  investor or the Product Owner has accepted these workstreams.
* **No live security reproduction.** B-17's four items are reasoned from source
  and policy, not from executed ALLOW/DENY request pairs (§0 limit 3). A
  follow-up should reproduce each as a negative test.
* **No UI/UX verification.** WS-4's navigation and parity claims are verified only
  at component-test level; no browser pass was run.
* **No whole-suite green.** The authoritative run covers the 34 files that
  exercise the change; 7 tests elsewhere are red and documented (§2.6).

### 5.5 Answer to the three tasks

| Task | Answer |
|---|---|
| **T1 — 154 vs 141** | Not a contradiction. **141** = 2026-09-26 snapshot DB (`ct_iv_p17m_20260926`); **154** = current `carbontally_demo_local`; delta = **exactly 13 tables**, all created by migrations dated 2026-10-11…2026-11-03. **B-16 closed.** |
| **T2 — per-workstream judgement** | Eight workstreams (WS-1…WS-8), **all ACCEPT** on code + test evidence; one security incompleteness **B-17** (P2, pre-existing) and one design gap needing a PO decision (**F-06**). |
| **T3 — commit readiness (PD-E1)** | **READY WITH ORDERING CONSTRAINTS** — one bundle, migrations first, tracked files never without their untracked counterparts; four in-commit caveats (§3.4). |

**END OF REPORT — CT-CARBONTALLY-FOUNDATION-CODE-REVIEW-05**
