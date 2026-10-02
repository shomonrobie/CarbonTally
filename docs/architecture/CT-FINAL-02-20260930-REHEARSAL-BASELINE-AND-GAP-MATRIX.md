# CT-FINAL-02 — Rehearsal Baseline, Gap Matrix & Backup/Restore Assessment

**Report ID:** `CT-FINAL-02-20260930-REHEARSAL-BASELINE-AND-GAP-MATRIX`
**Prepared:** 2026-09-30
**Reconciled:** 2026-10-01 — documentation-only status reconciliation against CoStrict's
FINAL-02 independent verification of 2026-09-30 (B4/D-7 and the §8 handoff); **no code change**.
**Authority:** FINAL-02 — Complete System Rehearsal & Acceptance — **IN PROGRESS**
**Scope of this slice:** read-only baseline, factual gap matrix, and the authorised
backup/restore + migration-compatibility rehearsal on **disposable** databases only.
**Commits / pushes / deployments / production or shared-data mutation by this task:** **none**.

> **Truth standard (unchanged):**
> `DOCUMENTED ≠ CODE EXISTS ≠ ROUTE WIRED ≠ AVAILABLE ≠ PERSISTED ≠ E2E VERIFIED ≠ INDEPENDENTLY VERIFIED ≠ PRODUCTION READY`.

This report does **not** close FINAL-02, does not claim production readiness, does not
authorise FINAL-03, does not reopen FINAL-01, does not start Storage Step 3, and does
not alter any settled product decision.

> **Evidence correction applied 2026-09-30 (post independent verification):** the B6
> missing-canonical-table count in §5.0 (and its echoes in §5.11, §6 and §8.1) is
> corrected from the originally reported **19 → 33** to the independently verified value.
> **B6 remains CONFIRMED** — it is strengthened, not weakened. No other figure, status or
> conclusion in this report was changed.

> **Status reconciliation applied 2026-10-01 (after CoStrict's FINAL-02 independent
> verification of 2026-09-30).** That verification (verdict *FINAL-02 INDEPENDENT VERIFICATION —
> DEFECTS FOUND*, §1 and §9) returned **D-7 Decision B — VERIFIED (application layer)** (94/94
> tests, exit 0; semantics, fail-closed lookup, owner/admin fast path and guard fan-out
> independently inspected) and recorded **D-7 live/RLS proof: `BLOCKED BY ENVIRONMENT`**.
> Blocker **B4 therefore no longer reads "independently unverified"**: its **implementation facet
> is closed / independently verified**, while its **live RLS/PostgREST-proof facet remains OPEN**
> (B2/B5). §1.3, §6 (B4), §7 item 10, §8 and §9 are reconciled to that verdict; **§8.1 items 1–5
> are recorded as completed and independently verified**, and only the credential / browser / live
> items in §8.2 remain open. The same verification **VERIFIED** the 41-tracked-file change set, the
> backup/restore drill, the 93/94 migration replay, the local = 116 / head = 149 baseline, the 7
> pre-existing failures (A/B) and Storage Steps 1+2; it found **exactly one material evidence
> defect — the 19 → 33 canonical-table count, already corrected above — and no application, code,
> data, RLS, migration or storage defect.** **FINAL-02 remains OPEN.** The IV report's
> `Gate state: OPEN` stands, and that report is **not edited** (CoStrict's artifact — §7 item 10).
> This reconciliation **cites** the verification; it does not file, restate or re-issue it.
> **No code, test, migration, configuration, `.env`, credential, bucket, RLS policy, database or
> environment was changed by this reconciliation.**

---

## 0. What this report is (and is not)

* It is a **factual baseline + gap matrix** for the remaining FINAL-02 rehearsal surface.
* It re-derives the state of the **current working tree**, which is **not** the state the
  independent verification report describes (see §1.3).
* It records **one genuinely new piece of evidence**: a re-run of the project's existing
  backup/recovery drill against a **disposable, production-like copy of the current release
  candidate** (§5), replacing drill evidence taken against a materially older schema revision.
* It makes **no code change**. No engineering gap in this slice required one; the single
  migration-chain failure found is data-state dependent and must **not** be "fixed" by
  editing an immutable historical migration (§5.4).
* It does **not** restate or re-issue the CoStrict verdict. The IV report's
  `Gate state: OPEN` stands and remains CoStrict's to change.

---

## 1. FINAL-02 baseline

### 1.1 Repository identity (FACT — measured this session)

| Field | Value |
| --- | --- |
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD | `cabdca8380415e73a25cf23eb393d0b15c0af391` (CT-FINAL-01 final security-fix report) |
| Commits made by this task | **none** |
| Pushes | **none** |
| Deployment / migration applied to any persistent environment | **none** |
| `git worktree list` | primary only |
| `git stash list` | empty |
| Pre-existing zero-byte files `8`, `=` | untouched |

The release candidate is a **dirty working tree on top of `cabdca8`** — not a commit.

### 1.2 Working-tree change set (FACT — measured this session)

| Measure | Value |
| --- | --- |
| Tracked modified files (`--untracked-files=no`) | **41** (0 deletions) |
| Untracked entries (`--porcelain`) / files (`--untracked-files=all`) | **89** / **934** |
| Total `--porcelain` lines | **130** |
| Decision register diff | `+284 / −0` (documentation only) |
| Staged changes | none |

Migrations in the repository: **94** files in `supabase/migrations/`, of which
`20261025000000_ct_step2_documents_bucket_size_alignment.sql` is **untracked (new)** and
`20261024000000_ct_final_01_documents_bucket_size_limit.sql` is the CT-FINAL-01 ceiling file.

### 1.3 The working tree has advanced materially beyond `CT-FINAL-02-INDEPENDENT-VERIFICATION-REPORT.md`

This is the most important baseline fact. It is a **state** correction, not a disagreement
with the verifier's reasoning.

| Evidence | mtime |
| --- | --- |
| `docs/architecture/CT-FINAL-02-20260929-EMAIL-AND-UPLOAD-CONFIGURATION-REPORT.md` | 2026-09-29 14:46 |
| `docs/architecture/CT-FINAL-02-INDEPENDENT-VERIFICATION-REPORT.md` (CoStrict, Gate OPEN) | 2026-09-29 17:12 |
| `backend/tests/unit/api/test_d7_org_lifecycle_decisions.py` (new, untracked) | 2026-09-29 23:25 |
| `backend/auth.py` (D-7 Decision B implementation; 336 insertions / 9 deletions) | 2026-09-30 12:54 |
| `backend/tests/unit/api/test_storage_management_step1.py` (new, untracked) | 2026-09-30 19:53 |
| `backend/services/storage.py` (Storage Step 2) | 2026-09-30 20:38 |
| Storage architecture, decision register, Step 1/2 closure records | 2026-09-30 21:58 – 22:03 |

The IV report recorded **24** tracked modified files; the tree now has **41**. The
**17 additional** tracked files are:

```text
backend/api/dependencies.py            backend/routes/document_activity.py
backend/api/router.py                  backend/routes/emissions.py
backend/api/v3_consultants.py          backend/routes/organizations/files.py
backend/api/v3_documents.py            backend/routes/organizations/management.py
backend/auth.py                        backend/routes/upload.py
backend/data/organization_files.py     backend/services/retention.py
backend/routes/admin/bulk.py           backend/services/storage.py
frontend/src/v3/consultant/ConsultantPage.jsx
frontend/src/v3/customer/DocumentsPage.jsx
docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md
```

Guarding suites that did not exist when the IV report was written (collected counts):

| Suite | Tests |
| --- | --- |
| `tests/unit/api/test_d7_org_lifecycle_decisions.py` | 70 |
| `tests/unit/api/test_d7_f1_f2_f3_enforcement.py` | 24 |
| `tests/unit/api/test_storage_management_step1.py` | 30 |
| `tests/unit/api/test_storage_management_step2.py` | 41 |
| `tests/unit/api/test_g1_g2_emissions_query_scope_and_staff_access.py` | 43 |
| `tests/unit/api/test_ct_final_02_email_provider.py` | 71 |

**Consequence for blocker B4.** The IV report's §11 / §19 B4 statement — *"`is_org_active`
… is referenced by no RLS policy … the back end … never checks `organizations.is_active`"* —
described the tree **as it stood at 2026-09-29 17:12**. The current tree contains an
uncommitted **D-7 Decision B** implementation in `backend/auth.py`
(`_caller_organization_inactive`, `_organization_inactive_for_path_org`,
`ORGANIZATION_SUSPENDED_DETAIL`, `organizations.is_active` read at the guard layer), with
**94 passing unit tests** across the two D-7 suites. B4 therefore moved from "not implemented"
to **"implemented in the working tree, independently unverified"** in this baseline.
**CoStrict's FINAL-02 independent verification of 2026-09-30 then returned `VERIFIED` on that
implementation at the application layer** (§1: uniform non-disclosing `ORGANIZATION_SUSPENDED_DETAIL`;
fail-closed `is_organization_active` on false / no-row / HTTP error / exception; a single
resolution point carried on `AuthUser.organization_is_active`; owner/admin authority stripped for
an inactive tenant; all six guards wired — `enforce_org_path_scope`, `enforce_org_query_scope`,
`require_org_member`, `require_org_member_or_internal_staff`, `require_org_admin`,
`require_org_access`; F2 `_ensure_audit_org_active` on the member **and** consultant paths;
body-scope routes enforced transitively; 94/94 tests, exit 0), and left **D-7 live/RLS proof
`BLOCKED BY ENVIRONMENT`**. **B4 is therefore split:** the *implementation* facet is
**closed / independently verified**; the *live proof* facet remains a **closure blocker** for an
environment reason, not an implementation reason (B2/B5). No CoStrict report was edited to record
this; it is recorded here and in §6 / §8.

### 1.4 Already IMPLEMENTED / VERIFIED / CLOSED in the release candidate

| Area | State | Evidence |
| --- | --- | --- |
| Storage Management Step 1 | **CLOSED** | `…STORAGE_MANAGEMENT_STEP1_IMPLEMENTATION_20260930.md`; 30 tests pass |
| Storage Management Step 2 | **CLOSED** | `…STEP2_IMPLEMENTATION_20260930.md` §20; 41 tests pass |
| Storage governance decisions S-1…S-3 | **CURRENT (L1, 2026-09-30)** | Decision register §41.3, §41.4 |
| Consultant/client + entitlement reconciliation U-1…U-7, E-4 | **RECONCILED (L1, 2026-09-30)** | Decision register §41.1, §41.2, §41.5 |
| Email provider abstraction, sender identity, secret handling | **PASS** | IV report §4–§7; 71 tests pass this session |
| Upload policy (3 values, ceilings, server-side enforcement) | **PASS** | IV report §8–§9; storage-layer ceiling re-verified on a disposable copy (§5.3) |
| Factor library (count/structure/retired table) | **PASS (local)** | IV report §14; 7,049 re-confirmed this session |
| CT-FINAL-01 regression (incl. F-05-R1 org-path scope) | **PASS** | IV report §15; 35 tests pass this session |
| Backup/restore (database, local disposable) | **VERIFIED (tool-proven)** | §5 of this report |

---

## 2. Gap matrix — remaining FINAL-02 rehearsal surface

Status vocabulary is restricted to: IMPLEMENTED · VERIFIED · PARTIALLY VERIFIED · BLOCKED ·
MISSING · NOT APPLICABLE · DEFERRED BY DECISION · OPERATIONAL / DEPLOYMENT DEPENDENCY.

### 2.1 Areas 1–15

| # | Area | Existing implementation | Existing tests/evidence | Status | Concrete gap | Required action | Verification method |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Local PC environment | Local Supabase stack (`project_id carbon_ledger`) + FastAPI + React/Vercel topology | Local Postgres 17.6 reachable; 116 public tables; 7,049 factors; `pg_dump`/`pg_restore`/`psql` present | **PARTIALLY VERIFIED** | No browser/authenticated session (B3); no from-zero clean rebuild performed this slice | none (evidence gathering only) | Disposable stack + authenticated session |
| 2 | Supabase configuration/integration | Local stack reproducible; `storage.buckets` provisioned; 4 `d32_documents_*` policies | IV §10, §12; this session: storage layer present, bucket private, `file_size_limit` column present | **PARTIALLY VERIFIED** | Live/shared project configuration is unreachable from this environment | **OPERATIONAL / DEPLOYMENT DEPENDENCY** (B2) | Provide read-only live connection |
| 3 | PostgreSQL schema & migrations | 94 migrations; `backend/tools/migration_drift.py` + runbook `.github/workflows/migration-drift.yml` | This session: restored reconstruction accepts **93/94**; 1 data-dependent failure (§5.4) | **PARTIALLY VERIFIED** | No clean *from-zero* rebuild rehearsal in this slice; `supabase_migrations.schema_migrations` on the local stack holds only 46 rows (stale ledger — observation) | Rehearsal on a disposable from-zero stack | Drift gate + from-zero rebuild |
| 4 | Authentication & JWT isolation | `backend/auth.py` `get_current_user`, `get_active_org_role`, `_org_admin_authority`, `enforce_org_path_scope`, D-7 Decision B inactive-org denial | 35 F-05-R1 + 94 D-7 tests pass this session | **PARTIALLY VERIFIED** | No authenticated JWT/organisation matrix on real PostgREST (B5) | Provision non-production users/orgs in a disposable stack | Live JWT matrix (ALLOW/DENY/403) |
| 5 | Storage integration | Storage Steps 1+2 (single ingress gate, signed URLs after authorization, no public URL) | 30 + 41 tests pass this session; Steps 1+2 CLOSED; bucket ceiling re-verified (§5.3) | **VERIFIED** (Steps 1+2) | Authenticated storage-object isolation matrix not derived (B5) | Disposable user JWTs | Live storage isolation matrix |
| 6 | Realtime | Supabase Realtime present in the local stack (`realtime` schema) | Not exercised; no realtime code in this change set | **PARTIALLY VERIFIED** | Not exercised in this slice | none added — out of this slice's scope | Local realtime subscription probe |
| 7 | FastAPI backend | Routers registered; `backend/api/router.py`; application imports cleanly | 314 unit tests pass this session (exit 0) | **VERIFIED** (unit) | No live HTTP drive of every route (IV §9 caveat) | Live smoke over ingress routes | Authenticated HTTP smoke test |
| 8 | Frontend/backend compatibility | `frontend/src/v3/api.js`, `ops/SettingsTab.jsx`, customer/consultant pages | IV §16: 36 Jest tests pass; browser QA not done | **PARTIALLY VERIFIED** | No authenticated browser session (B3) | Provision non-production admin login | Live browser QA |
| 9 | Factor library | Canonical `emission_factors`; retired `defra_conversion_factors` absent | 7,049 re-confirmed this session (local); IV §14 | **VERIFIED** (local) | Live/shared factor count unverifiable (B2) | Read-only live connection | Live count + key uniqueness |
| 10 | Customer workflows | Customer documents/drafts/emissions surfaces (`frontend/src/v3/customer/*`) | Unit suites pass; IV §16 component tests | **PARTIALLY VERIFIED** | Journey not driven end-to-end in a browser | Demo-journey rehearsal | Browser journey |
| 11 | Consultant workflows | Consultant pages + `api/v3_consultants.py`; firm/member capability model (register U-3) | Unit suites pass | **PARTIALLY VERIFIED** | Journey not driven end-to-end in a browser | Demo-journey rehearsal | Browser journey |
| 12 | Admin workflows | `/ops` control plane (`SettingsTab`, factor management) | IV §16 Jest; 71 email-provider tests | **PARTIALLY VERIFIED** | Live browser QA of admin panels not possible (B3) | Provision non-production admin login | Browser QA |
| 13 | Ingestion | Upload ingress paths (5 + test-upload) with `resolve_policy`/`enforce_*` | IV §9 call-site map + probes; upload suites pass | **PARTIALLY VERIFIED** | Not every route driven over live HTTP | Live HTTP ingress probes | Authenticated upload drive |
| 14 | Extraction | Extraction engines + suggestions | 3 `extraction_suggestions` tests **fail pre-existing** (IV §17 A/B proof) | **PARTIALLY VERIFIED** | Engine drift acknowledged, not caused by this change set | Disposition per IV §17 (not "fixed" to green the suite) | Full-suite run + A/B worktree |
| 15 | Mapping | Factor matching / clarification engines (`api/v3_activity_clarifications.py`) | Integration lifecycle suite exists (real schema) | **PARTIALLY VERIFIED** | Integration suite errors at setup on a reconstruction (§5.5) — harness truncates an append-only ledger | Sanctioned purge authorisation for the harness | Integration suite on disposable DB |

### 2.2 Areas 16–29

| # | Area | Existing implementation | Existing tests/evidence | Status | Concrete gap | Required action | Verification method |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | Emission calculations | Server-authoritative calculation; `routes/emissions.py` scope enforcement | `test_g1_g2_emissions_query_scope_and_staff_access.py` (43) passes; F-05-R1 export denial test passes | **PARTIALLY VERIFIED** | Not re-derived against live data | Live calculation rehearsal | Integration run |
| 17 | Reports | Report generation queue/versions; `routes/reports.py` ingress enforced | Unit suites pass | **PARTIALLY VERIFIED** | Not re-derived against live data | Live report rehearsal | Integration run |
| 18 | Exports | Export surfaces with org-path scope enforcement | F-05-R1 cross-tenant export denial covered (35 tests) | **PARTIALLY VERIFIED** | Not re-derived live | Live export rehearsal | Integration run |
| 19 | Sharing | Report sharing (`20261022000000_ct02_report_sharing.sql`) | Migration present; IV §15 regression pass | **PARTIALLY VERIFIED** | Not exercised live | Live sharing rehearsal | Integration run |
| 20 | Schedules | Scheduled reporting (`20261023000000_ct02_scheduled_reporting.sql`) | Migration present | **PARTIALLY VERIFIED** | Not exercised live | Live schedule rehearsal | Integration run |
| 21 | Notifications | Centralised email sender + provider abstraction + admin-only sender config | 71 provider tests pass this session; IV §4–§7 PASS | **VERIFIED** (application) · **BLOCKED** (external delivery) | No real SMTP credential (B1) | Provide credential in the deployment environment (never in chat) | Controlled external delivery |
| 22 | Admin factor management | Admin factor surfaces + `admin/` CRA quarantine | IV §16 Jest; PD-3 browser QA outstanding | **PARTIALLY VERIFIED** | Browser QA not possible (B3) | Non-production admin login | Browser QA |
| 23 | Manual factor lookup | Manual lookup surfaces (PD-5) | Covered by passing CT-VERIFY/REMEDIATE suites (IV §15) | **PARTIALLY VERIFIED** | Not exercised in a browser | Browser QA | Browser QA |
| 24 | Upload limits | `utils/upload_limits.py` + enforcement at every ingress; storage-layer ceiling migration | IV §8–§9 PASS; **this session**: both bucket migrations apply cleanly to a disposable copy → `file_size_limit = 10485760`, `public = false` | **VERIFIED** (application + storage layer on a disposable copy) | Live bucket ceiling depends on applying `20261024000000` / `20261025000000` at deployment | Apply via the authorised deployment process | Post-deployment bucket assertion |
| 25 | Retention behaviour | Purpose-based retention config; `services/retention.py`; destructive enforcement **not** implemented | Retention endpoints/tests unchanged and passing (IV §15) | **DEFERRED BY DECISION** | Destructive retention is deferred; no policy invented | none (deferred) | n/a |
| 26 | Backup/restore | `backend/backup/*` (encrypted logical exporter), `backend/tools/backup_export.py`, `tools/backup_recovery_drill.py` | **This session**: drill re-run against the current release candidate — §5 | **VERIFIED** (database, disposable) · **NOT COVERED** (storage object bytes) | Storage **object bytes** have no backup mechanism in this repository; Supabase-managed backup/PITR unverifiable here | Recorded as operational dependency (§5.6), not a new architecture phase | Provider-side backup/PITR evidence |
| 27 | Migration/rollback strategy | `tools/migration_drift.py` + `docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md`; idempotent migration chain | **This session**: 93/94 replay on a reconstruction; drift gate exists in CI | **PARTIALLY VERIFIED** | No *rollback* rehearsal (a rollback of an applied deployment is not implemented by design); one historical migration cannot replay over the copied dev data (§5.4) | Documented as an operational/data-hygiene dependency | Rollback runbook + dry run on a disposable target |
| 28 | Release fingerprint | HEAD `cabdca8…` + measured working-tree change set | This report §1.1–§1.2 | **PARTIALLY VERIFIED** | A *release* fingerprint cannot exist while the candidate is an uncommitted dirty tree | Commit (requires explicit authorisation) | Recomputed fingerprint after commit |
| 29 | Investor/demo journeys | Demo/investor data preserved; no destructive reset (D53) | Not driven in this slice | **PARTIALLY VERIFIED** | Journey not driven end-to-end in a browser | Browser journey rehearsal | Browser journey |

**No new requirement has been created by this matrix.** Every "required action" is either
(a) evidence that only an authenticated/browser or credentialed environment can produce,
(b) an operational/deployment dependency, or (c) already-deferred behaviour.
Nothing here promotes a non-blocking storage observation into a Storage Step 3.

---

## 3. Changes made

### 3.1 Repository changes

| File | Change | Reason |
| --- | --- | --- |
| `docs/architecture/CT-FINAL-02-20260930-REHEARSAL-BASELINE-AND-GAP-MATRIX.md` | **new** (this report) | Record the FINAL-02 baseline, gap matrix and the re-derived backup/restore evidence |

**No other repository file was created, modified or deleted by this task.** Specifically:
no application code, no migration, no test, no configuration, no `.env`, no bucket, no
RLS policy and no production or shared data was changed. No commit, no push, no deploy.

### 3.2 Disposable rehearsal environments (not repository state)

| Object | Created by | Final state |
| --- | --- | --- |
| `ct_final02_src` (disposable DB) | `pg_dump` of the local stack `postgres` DB, restored into a fresh `ct_` database, then brought to migration head | **retained** (deliberately) so CoStrict can re-run the drill; drop at will with `DROP DATABASE ct_final02_src WITH (FORCE)` |
| `ct_final02_p4` (disposable DB) | reproduction of the drill's Phase 4 error | dropped after evidence capture |
| `ct_final02_src_restored_*` (disposable DBs) | the drill's own targets | dropped by the drill |
| `/tmp/ct_*.dump`, `/tmp/ct_backup_drill_*/` | drill/evidence scratch | `/tmp` only; plaintext dumps deleted at the end of this task; the encrypted artifact is keyless-by-design (ephemeral drill key) |

The guard in `tools/backup_recovery_drill.py` (`assert_disposable`) refused nothing here
because every database used carries a `ct_` prefix; the local stack and every
`carbontally_*`/demo database were **read-only** throughout.

### 3.3 Why no code change was made

Every gap found in this slice resolves to one of:

1. evidence that requires an authenticated/browser session, a real credential, or a live
   environment (B1, B2, B3, B5);
2. an operational/deployment dependency (storage-object backup, Supabase-managed PITR,
   the two bucket migrations on a live project);
3. data-state/legacy-assumption behaviour of an **immutable historical migration** (§5.4),
   which must be documented rather than edited;
4. already-deferred behaviour (destructive retention, D-7 in the previous tree state).

None of these is authorised as a code change by the FINAL-02 brief, and STOP condition
"the correct solution is an operational/deployment dependency rather than a code change"
was reached instead of implementing.

---

## 4. Tests

### 4.1 Commands and exact results (this session)

```bash
cd /home/shomonrobie/ct_93d5cdd/backend
.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/unit/api/test_f05_r1_org_scope_authorization.py \
  tests/unit/api/test_d7_org_lifecycle_decisions.py \
  tests/unit/api/test_d7_f1_f2_f3_enforcement.py \
  tests/unit/api/test_storage_management_step1.py \
  tests/unit/api/test_storage_management_step2.py \
  tests/unit/api/test_g1_g2_emissions_query_scope_and_staff_access.py \
  tests/unit/api/test_ct_final_02_email_provider.py
```

| Result | Value |
| --- | --- |
| Collected | **314** tests (per-file: 35 + 70 + 24 + 30 + 41 + 43 + 71) |
| Progress | `[100%]` — **only pass markers**, no `F`, no `E`, no `s` |
| Exit code | **0** |
| Failures | **0** |

```bash
cd /home/shomonrobie/ct_93d5cdd/backend
.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/unit/tools/test_backup_export.py \
  tests/unit/tools/test_backup_recovery_drill_guard.py
```
→ **17 passed**, exit 0 (backup exporter + drill guard, including the disposable-name guard).

**Environment observation (affects how results must be read):** in this environment
`pytest 9.1.1` on Python 3.14 **does not emit the final summary line** into a redirected
file (verified with a deliberately small run: `[100%]`, `EXIT=0`, no `"N passed"` line).
Counts above therefore come from `--collect-only` (also exit 0) plus the progress/exit
evidence, not from a summary line. This is a reporting artefact, not a test outcome.

### 4.2 Tenant-isolation surface specifically (Phase D re-confirmation)

The permanent cross-tenant regression is carried by
`tests/unit/api/test_f05_r1_org_scope_authorization.py` (35 tests, all pass), which asserts
the *application* layer contract (Org A → Org A data ALLOW; Org B → Org A data DENY/403;
Org B → Org B ALLOW, including the export denial path). The two D-7 suites (94 tests) add
the inactive-organisation denial matrix. The **live JWT/organisation matrix against real
PostgREST** remains **NOT VERIFIED** (B5) and must not be inferred from these unit results.

### 4.3 Deliberately NOT run in this slice (so the record is unambiguous)

* the full backend suite (~4.4k tests) and its 7 known pre-existing failures — cited from
  IV report §17 (A/B-proven there against a pristine `cabdca8` worktree); **not re-derived
  here**;
* frontend Jest suites and any browser session (B3);
* anything against the live/shared Supabase project (B2) or a real SMTP server (B1);
* production anything.

---

## 5. Backup/restore assessment

All of §5 was executed on **disposable** databases only. The local Supabase stack and every
`carbontally_*`/demo database were read-only; no object, bucket, credential or shared row was
touched.

### 5.0 A material baseline finding that scoped this rehearsal

The local Supabase stack database (`postgres` @ `127.0.0.1:54426`) is **behind the shipped
migration chain**: it carries **116** public tables, while a database built by applying the
chain carries **149** (the number the project handover §2.2 records as canonical). A direct
table-set comparison shows **33 canonical tables absent** from the local stack and **none**
present that the canonical schema lacks (**116 + 33 = 149**; the local stack is
**33** canonical tables behind head):

> **Evidence correction (applied 2026-09-30, after independent verification).**
> This subsection **originally reported 19** absent canonical tables and listed only
> **18 names**, which was internally inconsistent (`116 + 19 ≠ 149`). CoStrict's
> independent verification established **33** and independently enumerated the 33
> table names, and identified the original enumeration as **defective**. The corrected
> count and the complete verified list are shown below. The **B6 conclusion is unchanged
> and CONFIRMED** — the original report *understated* the schema drift, so B6 is
> **strengthened**, not weakened. Re-measured read-only during this correction: local
> stack **116** public tables; disposable head-complete copy `ct_final02_src` **149**;
> absent **33**; present locally but not canonical **0**. Only the B6 count and its
> enumeration were corrected; no other figure, status or conclusion was changed.

```text
activity_clarifications
carbontally_insight_conversations
carbontally_insight_interactions
carbontally_insight_messages
carbontally_insight_tool_calls
contractual_instruments
disclosure_applicability_assessments
disclosure_framework_versions
disclosure_frameworks
disclosure_intensity_denominator_framework_links
disclosure_intensity_denominator_types
disclosure_intensity_ratios
disclosure_narrative_entries
disclosure_purpose_requirements
disclosure_report_instance_binding
disclosure_report_purpose_versions
disclosure_report_purposes
disclosure_requirement_mappings
disclosure_requirement_versions
disclosure_value_evidence
disclosure_values
estimation_records
evidence_line_items
insight_concurrency_leases
insight_rate_limit_buckets
instrument_allocations
manual_processing_grants
report_schedule_definitions
report_schedule_runs
report_share_access_events
report_shares
report_version_artifacts
scope3_categories
```

A rehearsal run *directly* against the local stack would therefore **not** exercise the
adjudication, disclosure, evidence-line-item, manual-processing-grant or report-artifact
surfaces at all. The rehearsal below was consequently performed on a disposable copy that was
**first brought to migration head** (149 tables / 149 RLS-tables / 271 policies / 7,049
factors). The local stack itself was **not** mutated (no unauthorised change to a persistent
environment).

### 5.1 What the existing backup mechanism is (inventory, not new work)

| Component | Role |
| --- | --- |
| `backend/backup/` (`service.py`, `exporter.py`, `artifact.py`, `catalog.py`, `crypto.py`, `storage.py`, `settings.py`, `errors.py`) | Phase-1 encrypted **logical** exporter (AES-256-GCM envelope, per-member checksums, `catalog.json` inventory). `__init__.py` states that **restore (D4) is not implemented**. |
| `backend/tools/backup_export.py` | Operator entrypoint: refuses a destination inside the repository, requires `CT_BACKUP_ENCRYPTION_KEY`, never prints the DSN, exits non-zero on failure. |
| `tools/backup_recovery_drill.py` | The **recovery** rehearsal tool: Phase 1 own-exporter verification, Phase 2 `pg_dump -Fc` → `pg_restore` into a fresh disposable DB with a fingerprint comparison, Phase 3 migration-chain compatibility, Phase 4 application-vs-reconstruction. Refuses non-disposable names. |
| `docs/operations/CARBONTALLY_BACKUP_RECOVERY_DRILL.md` | The drill record (2026-09-19) and its explicit list of what is **not** covered. |
| `backend/tests/unit/backup/*`, `tests/unit/tools/test_backup_export.py`, `…test_backup_recovery_drill_guard.py`, `tests/integration/backup/test_exporter_local.py` | Exporter/crypto/artifact/storage/settings contracts + the disposable-name guard (**17 tests pass this session**). |

### 5.2 Database backup — VERIFIED (disposable)

Phase 1 of `tools/backup_recovery_drill.py --source ct_final02_src`, head-complete source
(149 tables):

```text
artifact                  backups/<id>/carbontally-logical-backup-v1.tar.gz.enc
artifact size             966,907 bytes
ciphertext only           True   (no plaintext DDL/COPY material in the stored object)
envelope                  version 1 · AES-256-GCM · key_id key-v1
members                   154  (manifest + catalog + ddl + 149 per-table .copy)
content checksums         152 verified after decryption
manifest counts           149 tables · 14,245 rows · 271 policies · 103 triggers · 37 functions
manifest schemas          ['public']  (credential-bearing schemas refused by policy)
DDL member can rebuild    CREATE TABLE ✓ PK ✓ FK ✓ CREATE INDEX ✓ UNIQUE ✓ POLICY ✓
                          ENABLE ROW LEVEL SECURITY ✗   (known, documented)
```

**Conclusion:** the exporter produces a verifiable, encrypted, checksummed, reproducible
artefact for the **current** release-candidate schema. It is still **not a restore path by
itself** (D4 unimplemented; the DDL member is informational and does not enable RLS). That
limitation was already recorded in the drill documentation and is **unchanged** — no new
architecture was invented to close it.

### 5.3 Database restore — VERIFIED (disposable)

Phase 2 of the same run — platform-native recovery, head-complete source:

```text
dump size (pg_dump -Fc of ct_final02_src)   3,197,036 bytes
pg_restore return code                      1  (see caveat below)
missing tables                              0
row-count mismatches                        0
index delta 0 · constraint delta 0 · policy delta 0 · rls-table delta 0 · bucket delta 0
```

The single ignored `pg_restore` error is **not** an application error:

```text
pg_restore: error: could not execute query: ERROR: permission denied for table secrets
Command was: COPY vault.secrets (...) FROM stdin;
```

`vault.secrets` (and `realtime.list_changes` on the first copy attempt) are **Supabase-internal
objects owned by the Supabase management roles**; a plain `postgres`-role `pg_dump`/`pg_restore`
cannot recreate them. Every application-schema object restored exactly.

**Positive fidelity signal found in Phase 4 (§5.5):** the reconstruction still **enforces** the
append-only audit-ledger guard — a restored database refused `TRUNCATE public.audit_trail` with
`append-only ledger (CT-IMPLEMENT-02)`. Triggers/functions therefore survive the restore intact;
the guard is not "restored away".

### 5.4 Migration-chain compatibility of a reconstruction — 93/94, one data-dependent failure

Phase 3 applies the **shipped migration chain** to the reconstruction:

```text
{'migrations': 94, 'applied': 92, 'already_present': 1,
 'failed': [('20260801000000_rc2_constraints.sql',
             'column "organization_id" of relation "conversations" contains null values')]}
```

Root cause (verified, not inferred):

* `supabase/migrations/20260801000000_rc2_constraints.sql:101` executes
  `ALTER TABLE public.conversations ALTER COLUMN organization_id SET NOT NULL;`
* the file's own comment at line 97 records its assumption: *"Empty table → no backfill burden."*
* the copied data contains **36** rows in `conversations`, **1** with a NULL `organization_id`
  (measured: `36 conversations, 1 with null org`).

An **immutable historical migration** therefore cannot replay over data whose shape it did not
anticipate. Per governance (**never edit an existing migration**; do not invent a backfill
policy) this is recorded as a **data-hygiene / operational dependency for any restore that
replays the chain over such data** — not a code defect, and not something this change set
introduced.

### 5.5 Application-vs-reconstruction (Phase 4) — classification

Phase 4 sets `INTEGRATION_DATABASE_URL` to the reconstruction and runs
`tests/integration/test_f039_1_adjudication_lifecycle_runtime.py`. It errors at **setup**
(9/9 tests) with:

```text
asyncpg.exceptions.RaiseError: append-only ledger (CT-IMPLEMENT-02):
  TRUNCATE of public.audit_trail is not permitted
  (set ct.audit_purge_authorised=on only from an authorised purge run)
```

* **Classification: ENVIRONMENT / HARNESS limitation — not an application defect.** The suite's
  session fixture truncates the target database; the reconstruction correctly refuses to truncate
  an append-only ledger. The harness target must either be an authorised purge run or carry no
  ledger data.
* **It is simultaneously positive evidence of restore fidelity** (§5.3).
* No production code, ledger guard or test was weakened to "get past" this.

### 5.6 Storage object coverage — NOT COVERED (unchanged)

* Object **bytes** (uploaded documents) have **no** backup mechanism anywhere in this repository.
  Only bucket **configuration** is covered: this run re-confirmed `bucket delta 0`, the
  `documents` bucket private with the ratified `file_size_limit = 10485760`, and the four
  `d32_documents_*` policies present.
* The two bucket migrations (`20261024000000`, `20261025000000`) applied cleanly to the disposable
  copy and converged to the same state — the pending storage-layer alignment is provably
  applicable and idempotent **where `storage.buckets.file_size_limit` exists**. On a stack whose
  storage schema predates that column they raise a column error instead of the documented no-op
  (**observation only**; those files were already independently verified and are **not edited**
  here).
* Object-byte backup remains a provider-side question. **No strategy was invented.**

### 5.7 Supabase-managed recovery — NOT VERIFIABLE HERE

No live/shared credentials exist in this environment (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
`DATABASE_URL`, `SUPABASE_DB_URL` unset; `backend/.env` points only at `127.0.0.1`). No claim is
made about the managed backup tier, the PITR window or the last successful backup. The evidence
required to close it is already listed in `CARBONTALLY_BACKUP_RECOVERY_DRILL.md` §7 (a)–(e).

### 5.8 Scheduling — none

`.github/workflows/` contains exactly one workflow (`migration-drift.yml`); there is **no backup
workflow and no `cron` schedule anywhere** in the repository. Backups are **operator-invoked**
only (`backend/tools/backup_export.py`). This confirms the existing ops record ("no scheduled
backups") and is recorded as an operational dependency, not a new phase.

### 5.9 Retention — configuration only; no backup-artifact retention policy

* Application: purpose-based retention configuration exists; **destructive enforcement is
  deferred by decision** (register §24). Nothing invented here.
* Backup artefacts: **no retention policy is defined** (no schedule ⇒ nothing to expire). The
  exporter writes to an operator-supplied directory outside the working tree with mode `0700`.

### 5.10 RPO / RTO — NOT DEFINED

There is still **no agreed RPO/RTO and no schedule that delivers one** — unchanged from the drill
record. This is a PO/operational decision, not an engineering gap in this slice.

### 5.11 Operational dependencies (not new implementation)

1. Storage-object byte backup/versioning for the `documents` bucket (provider-side).
2. Supabase-managed backup/PITR evidence for the live project.
3. An agreed RPO/RTO + schedule (and therefore a backup-artefact retention policy).
4. Apply `20261024000000` / `20261025000000` at deployment (the live bucket ceiling is only pinned
   once they are applied through the authorised process).
5. Local-stack schema drift (§5.0): the local PC database is **33** canonical tables behind; a
   head-complete rehearsal environment must be built from the chain (as done here).
6. Restore-time data hygiene for `conversations.organization_id` (§5.4).

None of these is a code change, and none of them creates a new architecture phase.

---

## 6. Remaining blockers

Only genuine blockers are listed. B1–B3, B5 are carried forward unchanged from IV report §19;
**B4 changes meaning** in this slice; **B6 is new and is a prerequisite for a representative
local rehearsal** (not a claim of a code defect). After CoStrict's 2026-09-30 verification,
**B4 is a live-proof blocker only** — its implementation facet is independently verified (§1.3).

| # | Blocker | Current state (this slice) | Impact | Required to proceed |
| --- | --- | --- | --- | --- |
| B1 | A2Hosting SMTP credential/configuration unavailable | **Unchanged** (no SMTP variable/credential in the environment) | External email delivery cannot be independently verified | Provide the credential in the deployment environment (never in chat) |
| B2 | Live/shared Supabase credentials unavailable | **Unchanged** (all Supabase/DSN variables unset; `.env` localhost-only) | Live factor count, live schema and managed backup/PITR cannot be confirmed | Provide a read-only live connection |
| B3 | No admin test credentials / authenticated session | **Unchanged** | Live browser QA of `/ops` (upload policy, email delivery, factor management) not possible | Provision a non-production admin login |
| B4 | D-7 inactive-organisation denial — **live/RLS proof only** | Implemented in the working tree (`backend/auth.py`, 336 insertions; 94 passing unit tests) and **independently VERIFIED at the application layer** by CoStrict's FINAL-02 verification of 2026-09-30 (§1; 94/94 tests reproduced, exit 0). **Live/RLS/PostgREST proof: not performed — `BLOCKED BY ENVIRONMENT`** | The *implementation* gap is **closed and independently verified**; only the live proof is outstanding, and the IV report's §11/§19 B4 text (2026-09-29, pre-implementation) is stale | Provide a non-production environment with minted admin/user/consultant JWTs (the B2/B5 vehicle) so the live denial can be observed — **no implementation work remains** |
| B5 | Storage/JWT isolation matrix | **Unchanged** | Authenticated per-user/per-org object isolation is not derived | Provision non-production users/orgs in a disposable stack |
| B6 | **Local rehearsal database is not at schema head** (116 of 149 canonical public tables; **33** tables missing — §5.0; corrected 19 → 33 after independent verification) | **New, evidence-backed** | Any rehearsal run *directly* against the local stack silently omits adjudication, disclosure, evidence-line-item, manual-processing-grant and report-artifact surfaces | Build the rehearsal stack from the shipped chain (a disposable head-complete copy was built and used here); decide separately whether the local dev stack should be brought forward |

**Not blockers** (do not promote): the two bucket migrations not being applied to the live project
(deployment dependency), storage-object byte backup (provider dependency), RPO/RTO (PO decision),
the 7 pre-existing unit failures (documented), destructive retention (deferred by decision).

---

## 7. Deferred / operational items — not new implementation phases

1. **Storage-object byte backup/versioning** for the `documents` bucket — provider-side; no
   strategy exists or is invented (D44/D32 unchanged; S-1…S-3 unchanged).
2. **Supabase-managed backup/PITR** — unverifiable here; evidence list already written in the
   drill document §7.
3. **RPO/RTO + backup schedule + artefact retention** — a PO/operational decision.
4. **Pending storage-layer bucket migrations** — apply at deployment; only then is the live
   storage-layer ceiling pinned (application limits are already in force).
5. **Storage Step 2 §20.1 non-blocking observations (all 10)** — still NON-BLOCKING / DEFERRED /
   FOLLOW-UP. This report confirms none of them has been promoted to a requirement or to a
   Storage Step 3.
6. **Destructive retention** — deferred by decision (register §24).
7. **The 7 pre-existing unit failures** (4 migration-drift/"latest migration" + 3
   `extraction_suggestions`) — A/B-proven pre-existing at `cabdca8` in IV §17; deliberately not
   "fixed" to obtain a green suite (handoff governance rule 14).
8. **`services/email_service.py:202` unreachable `return True`** — dead-code cleanliness note
   carried from IV §4; no runtime effect; not fixed here.
9. **`supabase_migrations.schema_migrations` on the local stack holds only 46 rows** (latest
   `20260903010000`) while the database has 116 tables — the ledger is not a reliable statement
   of the local stack's applied state. Recorded as an observation; the authoritative rehearsal
   evidence is the applied-chain fingerprint (§5.0).
10. **Stale IV-report statements** (B4 §11/§19, the 24-file change-set enumeration, the
    "116 RLS tables" baseline) — the report is the verifier's; it is **not edited here**, and the
    correction is filed in §1.3 for CoStrict to reflect. CoStrict's 2026-09-30 verification
    independently confirmed the change set (41 tracked, identical set) and the 116/149 baseline,
    and returned **`VERIFIED`** for D-7 Decision B at the application layer; the IV report's own
    §11/§19 B4 text remains the 2026-09-29 pre-implementation state and is **CoStrict's to revise**.
    For the same reason the earlier FINAL-02 slice report
    `CT-FINAL-02-20260929-EMAIL-AND-UPLOAD-CONFIGURATION-REPORT.md` still carries a
    **"D-7 — PO DECISION REQUIRED (carried forward)"** line (`:543`, `:572`) describing the
    2026-09-29 state; it is a dated slice artifact and is **not edited** — its D-7 status is
    **superseded** by the recorded Decision B (IV §11) and by the 2026-09-30 verification above.
11. **CoStrict non-defect observation — register traceability for D-7 Decision B** (verification
    observation (b), 2026-09-30): the approved Decision B semantics live in the IV report §11,
    while the decision register's `+284` lines cover §41.1–§41.6 (consultant/storage) only. This
    reconciliation **does not** edit the register and **creates no new PO decision**; the
    observation is recorded only so it is not lost.

None of the above is promoted into a new architecture or research phase.

---

## 8. Independent verification handoff — what CoStrict should verify next

The IV report's gate remains **OPEN**. §8.1 lists, in priority order, the items this slice made
*verifiable now*; **CoStrict's FINAL-02 independent verification of 2026-09-30 has since completed
all five**, and the outcome is recorded inline against each item. §8.2 lists what still requires
credentials, a browser session or a live environment — **unchanged and still open**.

### 8.1 Newly verifiable (no credential or browser needed)

1. **D-7 Decision B (was B4).** Independently re-derive the implementation in `backend/auth.py`
   (`_caller_organization_inactive`, `_organization_inactive_for_path_org`,
   `ORGANIZATION_SUSPENDED_DETAIL`, `organizations.is_active` at the guard layer), the fail-closed
   lookup behaviour, the owner/admin fast path, and the 94 tests in
   `tests/unit/api/test_d7_org_lifecycle_decisions.py` + `test_d7_f1_f2_f3_enforcement.py`.
   Confirm the §1.3 supersession and state plainly whether the IV report's B4 must be revised.
   **Status (reconciled 2026-10-01): COMPLETE — independently VERIFIED (CoStrict, 2026-09-30,
   §1 / §9): 94/94 tests reproduced, exit 0; every element above confirmed; two non-defect
   observations recorded (foreign-org unknown-`is_active` handling; register traceability —
   §7 item 11). The IV report's B4 §11/§19 text **must be revised** (it is the pre-implementation
   state) — that revision is CoStrict's to make (§7 item 10). D-7 live/RLS proof remains blocked
   (§8.2 item 6).**
2. **The advanced change set.** Re-enumerate the working tree (41 tracked modified / 89 untracked
   entries) and verify the change set the IV report did *not* cover (D-7, G1/G2 emissions scope and
   staff access, Storage Steps 1+2 surfaces) as its own scope — not by cross-reference to the
   email/upload verification.
   **Status (reconciled 2026-10-01): COMPLETE — independently VERIFIED (verification §2): 41
   tracked modified (identical set), 94 migrations, register `+284/−0`; untracked entries measured
   **88–90 (volatile)** against the 89 reported — that single count is `PARTIALLY VERIFIED`; no
   material product change was omitted.**
3. **Backup/restore rehearsal (§5).** Re-run
   `backend/.venv/bin/python tools/backup_recovery_drill.py --source ct_final02_src` and
   independently confirm: 149 tables / 271 policies at source; `missing_tables 0`;
   `row_count_mismatches {}`; index/constraint/policy/RLS/bucket deltas all **0**; the single
   `vault.secrets` restore error is Supabase-internal; the reconstruction refuses
   `TRUNCATE public.audit_trail`; the migration replay is 93/94 with the one data-dependent failure
   attributed to `20260801000000_rc2_constraints.sql`.
   **Status (reconciled 2026-10-01): COMPLETE — reproduced exactly (verification §3–§4): 149
   tables / 149 RLS / 271 policies / 7,049 factors; artifact 966,907 B ciphertext-only; members
   154 / checksums 152; `missing_tables 0`; `row_count_mismatches {}`; index/constraint/policy/
   RLS/bucket deltas all 0; the `vault.secrets` error confirmed Supabase-internal
   (`owner=supabase_admin`); `TRUNCATE public.audit_trail` refused with the append-only-ledger
   error and 2 non-internal triggers survive; migration replay 93/94 with the rc2 data-state
   failure. One **observation**: Phase 3 re-application is not state-idempotent (271 → 351 policies
   via `20260803000000_rc2_rls.sql:141`) — a re-application artifact, not a policy gap.**
4. **Local-stack schema drift (§5.0).** Independently confirm the **33** missing canonical
   tables (corrected from the originally reported 19) and
   decide whether that is acceptable for a "local PC rehearsal" claim (B6).
   **Status (reconciled 2026-10-01): COMPLETE — independently VERIFIED (verification §5): local
   **116**, chain-head rehearsal **149**, local-minus-head **0**, missing canonical **33**. The
   original 19 / 18-name enumeration was the **single material defect found** and is already
   corrected in §5.0, §5.11, §6 and here (B6 conclusion unchanged and understated).**
5. **No-regression claim.** Re-derive the 7 pre-existing failures against a pristine `cabdca8`
   worktree (IV §17 method) so that "no new regression" rests on fresh A/B evidence, and confirm
   that nothing else in the repository changed besides this report (§3.1).
   **Status (reconciled 2026-10-01): COMPLETE — independently VERIFIED (verification §6): the same
   7 failures (`test_d17_provider_ownership_migration_revision.py`, `test_i1_insight_migration.py`,
   `test_i2_insight_authorization_contracts.py`, `test_p17_migrations.py`, 3 ×
   `test_extraction_suggestions.py`) fail identically in the current tree and in a pristine
   `cabdca8` tree; no test or migration was modified. `PARTIALLY VERIFIED` only in that
   `test_f05_r1_org_scope_authorization.py` (35 pass) is DB-free application-layer evidence —
   authenticated JWT/PostgREST and Storage isolation remain un-derived (B5, §8.2 item 6).**

### 8.2 Still requiring credentials / a browser / a live environment

6. **B3 + B5 (the FINAL-02 closure-evidence run):** a disposable stack with minted non-production
   admin/user/consultant JWTs, then (a) authenticated browser QA of `/ops` and (b) the authenticated
   storage/JWT isolation matrix, plus CT-VERIFY-06 items 11 and 7e, **and the D-7 live/RLS/PostgREST
   proof of the inactive-organisation denial (the same authenticated matrix is its vehicle;
   CoStrict recorded it `BLOCKED BY ENVIRONMENT` while verifying the application layer).**
7. **B1:** external A2Hosting delivery, once a credential exists in the environment.
8. **B2:** live factor count/schema, and Supabase-managed backup/PITR evidence (§5.7).

### 8.3 Explicit non-claims

This slice does **not** claim E2E or independent verification, does **not** claim production
readiness, does **not** authorise FINAL-03, does **not** reopen FINAL-01, does **not** start
Storage Step 3, and does **not** alter any settled product decision (register §41 and its
predecessors stand as written).

---

## 9. Final status

**FINAL-02 IMPLEMENTATION SLICE COMPLETE — READY FOR INDEPENDENT VERIFICATION**

The *slice* (read-only baseline + gap matrix + the authorised disposable backup/restore and
migration-compatibility rehearsal, with no code change) is complete and its evidence is
reproducible. **Independent verification of the slice has since been performed (CoStrict,
2026-09-30): verdict *FINAL-02 INDEPENDENT VERIFICATION — DEFECTS FOUND* — the single material
defect being the B6 enumeration (19 → 33), corrected in this report on 2026-09-30 23:12, with
D-7 Decision B verified at the application layer.** **FINAL-02 itself remains OPEN**: the closure
gate is unchanged, blockers B1–B3, B5 and B6 stand, **B4 stands only as the live/RLS proof**
(§1.3, §6), and acceptance is CoStrict's to grant.

### 9.1 Handoff status summary (reconciled 2026-10-01 — documentation only; no code change)

**Closed / independently verified**

| Item | Authority |
| --- | --- |
| FINAL-01 | CT-FINAL-01 closure records (untouched) |
| Storage Management Steps 1 + 2 | CLOSED and independently verified (verification §8; not reopened) |
| B6 **documentation correction** (19 → 33) | CoStrict 2026-09-30 verification §5; applied here 2026-09-30 23:12 |
| **D-7 Decision B application-layer implementation** | **independently VERIFIED — CoStrict 2026-09-30 verification §1 / §9 (94/94 tests, exit 0)** |
| Backup/restore drill · migration replay 93/94 · change set (41 tracked) · 7 pre-existing failures (A/B) · local 116 / head 149 | VERIFIED by the same verification (§2–§6) |

**Open / evidence still required** (all non-code, environment/credential/operational)

| # | Open item | Missing evidence |
| --- | --- | --- |
| FINAL-02 | closure itself | gate **OPEN**; acceptance is CoStrict's to grant |
| B1 | external email delivery | A2Hosting SMTP credential in the deployment environment |
| B2 | live/shared Supabase | read-only live connection (live schema/factors, provider-managed backup/PITR) |
| B3 | `/ops` browser QA | non-production admin login / authenticated browser session |
| B4 | **D-7 live/RLS/PostgREST proof only** | minted non-production JWTs on a disposable/live stack (B2/B5 vehicle) |
| B5 | JWT/PostgREST + Storage object isolation matrix | non-production users/orgs and authenticated storage objects |
| B6 | local rehearsal stack **33 canonical tables behind** | build rehearsals from the shipped chain (done here via `ct_final02_src`); decide separately whether to bring the local dev stack forward |

**Not authorized**

FINAL-03 · Storage Step 3 · production deployment or mutation · any new implementation outside the
existing authorization. This reconciliation makes **no new PO decision**, starts **no new
architecture phase**, and **does not claim FINAL-02 closed or production ready**.

---

## Appendix A — exact commands run (reproducible)

```bash
# repository identity / change set
git branch --show-current; git log -1 --format='%H %s'
git status --porcelain | wc -l                       # 130
git status --porcelain --untracked-files=no | wc -l  # 41
git diff --numstat                                   # per-file change set (§1.2)

# schema / migration facts
ls supabase/migrations | wc -l                       # 94
psql "$H/postgres" -tAc "select version()"           # PostgreSQL 17.6
psql "$H/postgres" -tAc "select count(*) from public.emission_factors"   # 7049
psql "$H/ct_final02_src" -tAc "select count(*) from pg_class c join pg_namespace n
  on n.oid=c.relnamespace where n.nspname='public' and c.relkind in ('r','p')"  # 149 at head

# head-complete disposable rehearsal source (local stack read-only)
pg_dump --format=custom --file /tmp/ct_final02_src.dump "$H/postgres"
psql "$H/postgres" -c 'CREATE DATABASE ct_final02_src'
pg_restore --no-owner --no-privileges --dbname "$H/ct_final02_src" /tmp/ct_final02_src.dump
#   then apply all 94 shipped migrations in-transaction, recording per-file failures

# the recovery drill (existing tool, unmodified)
backend/.venv/bin/python tools/backup_recovery_drill.py --source ct_final02_src --skip-app-check
backend/.venv/bin/python tools/backup_recovery_drill.py --source ct_final02_src   # incl. Phase 4
# Phase-4 error reproduction (kept target):
cd backend && INTEGRATION_DATABASE_URL=$H/ct_final02_p4 .venv/bin/python -m pytest -q \
    tests/integration/test_f039_1_adjudication_lifecycle_runtime.py

# test suites (§4)
cd backend && .venv/bin/python -m pytest -q -p no:cacheprovider <7 suites>   # 314 collected, exit 0
cd backend && .venv/bin/python -m pytest -q -p no:cacheprovider \
    tests/unit/tools/test_backup_export.py tests/unit/tools/test_backup_recovery_drill_guard.py
```

`$H` = `postgresql://postgres:postgres@127.0.0.1:54426`

## Appendix B — disposable environment hygiene

* Created: `ct_final02_src` (**retained** so the drill can be re-run), `ct_final02_p4` (dropped),
  drill-created `ct_final02_src_restored_*` (dropped by the drill itself).
* Remove the retained copy with:
  `psql "$H/postgres" -c 'DROP DATABASE ct_final02_src WITH (FORCE)'`.
* Plaintext dumps under `/tmp` were deleted at the end of this task; the encrypted drill artefact is
  unusable by design (ephemeral 32-byte drill key, never written to disk).
* Read-only throughout: the local Supabase stack, all `carbontally_*` databases, the demo/investor
  data, every bucket object, every credential and every shared row.

## Appendix C — safety confirmation

* Repository changes by this task: **one new documentation file** (this report). Nothing else —
  no application code, migration, test, configuration, `.env`, bucket, RLS policy or credential was
  modified; nothing was deleted, renamed or moved.
* `git worktree list`: primary only (no worktree created this session). `git stash list`: empty.
* No production or shared-environment access; no deployment; no migration applied to any persistent
  environment; no commit; no push.
* No non-blocking storage observation was promoted to a requirement, and no Storage Step 3 was
  started. No settled product decision was altered.
* **END OF REPORT.**





