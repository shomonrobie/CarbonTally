# CT-CARBONTALLY-FOUNDATION-BASELINE-01 — CarbonTally Foundation Baseline

**Document ID:** `CT-CARBONTALLY-FOUNDATION-BASELINE-01`
**Task ID:** `CT-CARBONTALLY-FOUNDATION-BASELINE-01`
**Date of evidence capture:** 2026-10-08 (local, Asia/Dhaka +0600)
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**HEAD at capture:** `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`
**Type:** READ-ONLY BASELINE — evidence capture and reconciliation
**Status:** `COMPLETE_WITH_OBSERVATIONS` (read-only, document-only)
**Author:** Cline (implementation/audit agent)

**Truth vocabulary used in this document** (distinct states, AGENTS.md §73):
`VERIFIED` · `TESTED` · `IMPLEMENTED` · `DOCUMENT-ASSERTED` · `UNVERIFIED` · `BLOCKED` · `NOT RUN`.
Nothing in this document is reported as `ACCEPTED`. No Product Owner acceptance is claimed.

---

## 1. Task, scope and what this report is (and is not)

### 1.1 Purpose

Produce a single, current, evidence-based **foundation baseline** for CarbonTally as it
actually exists in this checkout, on this machine, in these databases, at the moment of
capture — so that subsequent implementation, verification and QA work starts from measured
reality rather than from historical reports.

### 1.2 Scope of this pass

| In scope | Out of scope |
| --- | --- |
| Repository identity, branch, HEAD, working-tree accounting | Any code change, refactor, fix or migration |
| Local runtime topology and liveness | Production (`pvwiojoyaqywtydzcpbg`) — not contacted |
| Local database structure, RLS surface, business-data volume | Database writes of any kind |
| Migration inventory and applied-state boundary | Applying migrations, seeding, truncation |
| Backend / frontend structural inventory | Starting or stopping services |
| API surface measurement (live OpenAPI) | Acceptance of any workflow |
| Test-suite baseline (exact runs performed this session) | Running the integration/e2e/API suites |
| Extraction-pipeline behaviour probes (read-only, in-process) | Corpus sweeps, OCR runs |

### 1.3 What this report is NOT

1. It is **not** an acceptance report. No workflow is declared working, complete or accepted
   (AGENTS.md §§73–74).
2. It is **not** a re-derivation of every historical audit. Historical findings are carried
   forward **with their original IDs and their original verification status**, and are marked
   as re-verified **only** where this session produced fresh evidence.
3. It is **not** a gap-closure plan. Actions in §15 are proposed, not authorised.
4. It is **not** a production statement. Production state is `UNKNOWN` (unchanged from
   `CT-PO-CT-READINESS-01` finding F-06).

### 1.4 Read-only attestation

- **No** database write, migration, seed, truncate, drop, `ALTER` or configuration change was
  performed. Every database statement executed was a read-only `count(*)`, `to_regclass()`,
  catalog or `information_schema` probe inside the local Postgres container.
- **No** repository mutation other than the creation of this one document under
  `docs/architecture/`.
- **No** service was started, stopped or restarted; **no** worker, harness or browser was run.
- **No** production host was contacted.
- **No** secret, credential, JWT, signed URL or demo password appears in this document. Only
  environment **key names** and non-secret endpoint values are quoted.
- The pre-existing dirty working tree (78 modified tracked files, 191 untracked paths) was
  **not** touched, and is treated in this report as immutable evidence (§4).

---

## 2. Method, evidence sources and classification scheme

### 2.1 Evidence tokens

| Token | Meaning |
| --- | --- |
| `GIT:` | `git` object/ref, branch, log, status, diff-stat inspected this session |
| `RUNTIME:` | live HTTP probe / listening socket / process env / supervisor state, this session |
| `DB:` | live read-only database probe, this session |
| `CODE:` | source file read this session |
| `TEST:` | test suite executed this session |
| `DOC:` | repository document read this session (assertion only) |
| `HANDOVER:` | `docs/architecture/carbontally_master_handover_2026-10-05.md` (2026-10-05) |

### 2.2 Placement classification `A–G`

Classes **A–E are inherited verbatim** from the repository's own controlled vocabulary
(`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` §5.2) so this
baseline stays comparable with the existing catalogue. Classes **F and G are introduced by
this baseline** to capture the two states that catalogue did not need (drift, and
environment-blocked).

| Class | Meaning | Where the durable object lives |
| --- | --- | --- |
| **A — SATISFIED** | Object/behaviour exists in a database **and** is reachable by a running code path | live database + code path |
| **B — MIGRATED_BUT_UNAPPLIED** | Exists as a migration in Git; not applied to the database under discussion | migration file only |
| **C — CLONE_ONLY** | Exists only in a disposable `ct_*`/demo database; no durable database holds it | disposable clone / demo DB |
| **D — NOT_IN_ANY_DATABASE** | Implied object exists in no database at all (naming drift, empty catalogue, unimplemented persistence) | nowhere |
| **E — CONFIGURATION_ONLY** | Requirement is satisfied by a settings key/value rather than a table | `system_settings` etc. |
| **F — DRIFT / CONFLICT** | Two current sources disagree: docs vs code, code vs test, code vs database, or config vs runtime | contradictory sources |
| **G — BLOCKED / NOT VERIFIABLE** | Cannot be confirmed or denied from this pass (missing credential, absent environment, pending PO decision) | unverifiable here |

> **Note for the Product Owner.** Classes A–E are quoted from the existing catalogue; F/G are
> new. If a different A–G taxonomy was intended for this baseline, only the letter mapping in
> §14 changes — the underlying evidence does not.

### 2.3 Finding severity

`P1` = release-integrity / security / test-baseline failure · `P2` = material baseline defect
or drift · `P3` = documentation or currency · `INFO` = recorded for completeness.

### 2.4 Method limitations (stated, not hidden)

1. The suites run were **unit-scope only**; API/unit (2,788 tests), integration, e2e and
   frontend suites were **not** run — all coverage below is therefore partial.
2. Runtime verification was **liveness and contract-shape only** (HTTP status, OpenAPI size and
   operation count). No authenticated browser journey was performed.
3. Database verification was **structural and volumetric** (tables, RLS flags, policy counts,
   row counts, object probes). RLS was **not** behaviourally evaluated: `carbontally_demo_local`
   has an `auth` data model but no credentials were used, and `ct_local_93d5cdd` has **no**
   `auth` data model at all.
4. In this environment the installed `pytest 9.1.1` does **not** emit its final
   `N failed, M passed` line into captured output. Totals in §13 are therefore derived from
   **collection counts + the enumerated failure list**; the passed count is deliberately not
   asserted where it is not machine-readable.
5. Extraction probes were executed against the **current parser source in-process** with
   strings taken from the real invoice forms documented in
   `docs/deepseek/what_was_wrong_extraction.md`. They demonstrate parser behaviour; they do not
   re-run the 144-file corpus.

---

## 3. Repository identity and Git baseline

| Item | Value | Evidence |
| --- | --- | --- |
| Workspace | `/home/shomonrobie/ct_93d5cdd` | `GIT:` |
| Branch | `p8-release-reconciled` | `GIT:` |
| HEAD | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` | `GIT:` |
| HEAD subject | `docs(CT-HANDOVER-2026-10-05-CHECKPOINT-01): add 2026-10-05 master handover checkpoint` | `GIT:` |
| HEAD commit date | 2026-10-05 15:22:58 +0600 | `GIT:` |
| Remote `github` | `https://github.com/shomonrobie/CarbonTally.git` | `GIT:` |
| Remote `origin` | `/tmp/ct_step2` (local path remote, not a network remote) | `GIT:` |
| Staged changes | **0** (`git diff --cached` empty) | `GIT:` |

Recent history (subject level): `3fec874` (2026-10-05 handover checkpoint) → `375a48d`
(2026-10-03 `FINAL-03: freeze production cutover release`) → `cabdca8` (2026-09-29
`docs(CT-FINAL-01): final security-fix and verification report`) → `5216c71` (2026-09-29
`CT-FINAL-01: close the CT-VERIFY-06 blockers (D-0, D-2, D-3, D-5, D-6)`).

**Baseline consequence.** The 2026-10-05 master handover names
`375a48dc1b9e9cfd74090bbf747554ae997acb59` as the frozen release SHA. HEAD has since advanced
by exactly **one documentation commit** (`3fec874`), so the *code* content of the frozen
release is HEAD's parent, but HEAD is **not** the SHA quoted in the handover
(`HANDOVER:` + `GIT:`) — recorded as B-07 in §14.3.

### 3.1 Structural inventory (`CODE:`)

| Metric | Count |
| --- | --- |
| Backend Python files (excluding `.venv`) | **717** |
| Backend test files (`backend/tests/**/test_*.py`) | **340** |
| Backend API route modules (`backend/api/*.py`) | **68** |
| — of which V3 route modules (`backend/api/v3_*.py`) | **41** |
| Engines (`backend/engines/*.py`) | **16** |
| Services (`backend/services/*.py`) | **39** |
| Frontend source files (`frontend/src/**/*.js` or `*.jsx`) | **280** |
| Frontend test files (`frontend/src/**/*.test.*`) | **58** |
| Frontend V3 planes (directories under `frontend/src/v3/`) | **13** (`admin, capabilities, components, consultant, customer, evidence, insight, messaging, ops, pe, portal, reports, __tests__`) |
| Supabase migration files (`supabase/migrations/*.sql`) | **103** |
| — of which version ≥ `20261001` | **28** |
| Repository Markdown documents (`docs/**/*.md`) | **927** |

> `AGENTS.md` §54 references the demo-identity manifest at
> `tools/seed_investor_demo/DEMO_IDENTITIES.md`. **That path does not exist in this checkout**
> (`CODE:` — `ls tools/seed_investor_demo` → *No such file or directory*). The manifest actually
> present is `tools/demo_lab/manifest.json` (with `tools/demo_lab/provision.py`). Recorded as
> B-11 in §14.3.

---

## 4. Working-tree state — the pre-existing change set (immutable evidence)

The working tree is **dirty by design** and was already dirty before this session. It is
recorded here so that later work cannot mistake it for its own output.

| Item | Value | Evidence |
| --- | --- | --- |
| `git status --porcelain` entries | **269** | `GIT:` |
| Tracked **modified** (`M`) | **78** | `GIT:` |
| Untracked (`??`) | **191** | `GIT:` |
| Staged | **0** | `GIT:` |
| `git diff --stat` (unstaged) | **78 files changed, 7,440 insertions(+), 928 deletions(-)** | `GIT:` |
| Created by this session | **only** `docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md` | `GIT:` |

### 4.1 Composition of the change set

- **Backend (modified):** 19 API modules (`consultant_auth`, `dependencies`,
  `manual_processing_admin`, `manual_processing_auth`, `router`, `upload_gate`,
  `v3_automatic_processing`, `v3_consultants`, `v3_context`, `v3_document_uploads`,
  `v3_documents`, `v3_manual_extraction`, `v3_operations`, `v3_organizations`,
  `v3_processing_workflow`, `v3_reporting`, `v3_vehicles`, …), `backend/auth.py`,
  `backend/data/{consultants,invitations,manual_processing,organizations}.py`,
  `backend/domain/{branding,manual_processing,partners}.py`, `backend/services/work_items.py`,
  `backend/workers/automatic_processing.py`, 18 API unit-test modules, plus
  `docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md` and
  `docs/architecture/CARBONTALLY_PE_VALIDATION_WORKFLOW_DECISION.md`.
- **Frontend (modified):** `src/App.js`, `src/OnboardingPage.jsx`, `src/v3/api.js`,
  `v3/components/V3Layout.jsx`, `v3/admin/{AdminPage,FacilitiesTab,MembersTab}.jsx` +
  `admin.css`, `v3/consultant/*` (4 files), `v3/customer/{DashboardPage,DocumentsPage,
  ProcessingItemWorkspace,ReviewDetailPage}.jsx`, `v3/ops/OperationsPage.jsx`, plus 7 test
  files.
- **Tooling (modified):** `tools/demo_lab/{README.md,manifest.json,provision.py,
  run_demo_lab.sh,stack.py,verify.py}`, `.gitignore`.
- **New migrations (untracked, 5):** `20261030000000_manual_processing_routing.sql`,
  `20261101000000_ct_mp_sub_003_consultant_coverage.sql`,
  `20261102000000_ct_consultant_model_02_capability_admission.sql`,
  `20261103000000_ct_consultant_model_03_client_access_and_mode.sql`,
  `20261104000000_ct_consultant_client_identity_04.sql`.
- **New frontend surfaces (untracked, examples):** `v3/clientAccess.jsx`,
  `v3/consultant/{ClientAccessTab,ClientOrgShell,ConsultantClientContext,ManualProcessingCoverageTab}.jsx`,
  `v3/customer/{ManualProcessingPage,UploadDocumentsPanel}.jsx`,
  `v3/ops/{ManualProcessingCoverageTab,ManualProcessingTab}.jsx`, `v3/portal/`,
  `src/AcceptInvitation.jsx`, `src/v3/uploadsCopy.jsx`, + 10 new test files.
- **New backend modules (untracked, examples):** `backend/api/admin_consultant_commercial.py`,
  `backend/api/client_access_guard.py`, `backend/api/client_portal/`.
- **Untracked research/report material:** `Research/` (7 task folders:
  `CT-CONSULTANT-MODEL-UIUX-DESIGN-01`, `CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01`,
  `CT-CONSULTANT-ORGANISATION-PARITY-VERIFY-01`, `CT-CONSULTANT-UX-REMEDIATION-01`,
  `CT-PO-DEMO-LAB-PERSISTENCE-01`, `CT-PO-PRODUCT-MODEL-IMPLEMENTATION-01`,
  `CT-PO-PRODUCT-MODEL-RECONCILIATION-01`), `docs/deepseek/`, `.costrict/`,
  `.p18_audit_tmp/`, and many `docs/architecture/*` / `docs/audit/*` reports.

### 4.2 Interpretation

The repository is in a **post-release, actively-extended** state. The uncommitted change set
carries the consultant-organisation-parity and Manual Processing commercial/UI work that
post-dates the frozen release, including **five unapplied migrations**. Source code alone
therefore does not describe what the running system can do — §5–§8 (runtime, databases,
migrations) are the authoritative sections.

### 4.3 Environment files and secret hygiene

| File | Tracked? | Notes |
| --- | --- | --- |
| `backend/.env` | **No** — ignored by `.gitignore:83` (`.env*`) | key **names** inspected only |
| `frontend/.env.local` | **No** — ignored by `frontend/.gitignore:16` | key names + two non-secret URLs quoted |
| `admin/.env.development.local` | **No** — ignored by `.gitignore:83` | not read |
| `~/ct_local_env/demo_lab/backend.env` (outside repo) | n/a | key names only; DSN redacted when quoted |

`git ls-files | grep '\.env'` returns **nothing**: no environment file is tracked, so no
credential is committed by that path (`GIT:`).

---

## 5. Local runtime baseline

### 5.1 Liveness and contract probes (`RUNTIME:`)

| Probe | Result |
| --- | --- |
| `GET http://127.0.0.1:8070/health` | **HTTP 200** — `{"status":"healthy","service":"CarbonTally API","version":"3.0.0","supabase_connected":true,"pool_connected":true}` |
| `GET http://127.0.0.1:8070/openapi.json` | **HTTP 200** — 868,614 bytes, **654 paths**, **777 operations** |
| `GET http://127.0.0.1:54430/` (demo-lab gateway) | **HTTP 200** |
| `GET http://localhost:3000/` (frontend) | **HTTP 200** |
| Supervisor state (`~/ct_local_env/demo_lab/supervisor.status.json`) | `state: running`; backend pid 1014820 (restarts 0); frontend pid 1014827 (restarts 0); `updated_at 2026-10-08T15:27:10+0600` |

### 5.2 Listening sockets relevant to the stack (`RUNTIME:`)

| Address | Service |
| --- | --- |
| `127.0.0.1:8070` | CarbonTally FastAPI (uvicorn, pid 1014820) — the **runtime** API port |
| `0.0.0.0:3000` | React frontend dev server |
| `127.0.0.1:54430` | demo-lab Supabase gateway (nginx) — the runtime `SUPABASE_URL` |
| `0.0.0.0:54426` | Postgres (container `supabase_db_carbon_ledger`, PostgreSQL 17.6.1.147) |
| `0.0.0.0:54425` | Supabase Kong (auth `/auth/v1`, rest `/rest/v1`) |
| `0.0.0.0:9999` | Hindsight memory service (published). Supabase Auth/GoTrue also listens on 9999 **inside its container**, but is not published on that host port |
| `0.0.0.0:5678` | n8n |
| `127.0.0.1:11434` | Ollama |
| internal only | `postgrest` (3000 in-container), `realtime` (4000), `storage-api` (5000), `pg-meta` (8080), `mailpit` |

Running containers (14): `supabase_db_carbon_ledger`, `supabase_kong_carbon_ledger`,
`supabase_auth_carbon_ledger`, `supabase_rest_carbon_ledger`, `supabase_realtime_carbon_ledger`,
`supabase_storage_carbon_ledger`, `supabase_pg_meta_carbon_ledger`,
`supabase_inbucket_carbon_ledger` (Mailpit), plus the demo-lab trio
`carbontally_demo_lab_gateway`, `carbontally_demo_lab_postgrest`,
`carbontally_demo_lab_storage`, plus `hindsight-carbontally` and `n8n-n8n-1`.
Uptime at capture: **1 day 40 min**, load average 3.39.

### 5.3 Configuration drift — `backend/.env` is **not** the runtime configuration (`RUNTIME:` + `DOC:`)

| Source | API port | Supabase URL | Database |
| --- | --- | --- | --- |
| Running process (`uvicorn` env) | **8070** | `http://127.0.0.1:54430` | `postgresql://postgres:***@127.0.0.1:54426/carbontally_demo_local` |
| `backend/.env` (in repo, git-ignored) | `PORT=8060` | `SUPABASE_URL=http://127.0.0.1:19999` | `DATABASE_URL` present (not quoted) |
| `frontend/.env.local` | `REACT_APP_API_URL=http://localhost:8070` | `REACT_APP_SUPABASE_URL=http://127.0.0.1:54430` | — |
| `~/ct_local_env/demo_lab/backend.env` (outside repo) | — | `SUPABASE_URL=http://127.0.0.1:54430` | `…54426/carbontally_demo_local` |

`127.0.0.1:19999` appears **nowhere** in the listening-socket inventory. Consequence: anything
executed with the *repository* environment (unit tests, CLI tools, scripts) resolves a
different port and a dead Supabase URL than the actually-running stack. Recorded as **B-04**.
`~/ct_local_env/demo_lab/backend.env` also declares `TESSERACT_CMD` (OCR dependency), which the
repository `.env` does not — i.e. OCR availability is an environment property of the demo lab,
consistent with AGENTS.md §20.

### 5.4 API surface composition (measured from live OpenAPI, `RUNTIME:`)

| Prefix | Paths | Tag families present |
| --- | --- | --- |
| `/api/v3` | 371 | Admin (Analytics, Audit, Beta, Bulk, DEFRA Factors, Email Templates, Extraction, Logs, Permissions, Review History, Reviews & Assignments, Settings, Staff Management, Staff Performance, Workload) |
| `/api/admin` | 91 | |
| `/api/organizations` | 61 | |
| `/api/reports` | 20 | |
| `/api/v2` | 17 | |
| `/api/customer-documents` | 14 | |
| `/api/documents` | 11 | |
| `/api/drafts` | 9 | |
| `/api/reference` | 7 | |
| `/api/emissions` | 6 | |
| `/api/glossary`, `/api/logs` | 5 each | |
| `/api/batches`, `/api/users`, `/api/notifications`, `/api/feedback` | 4 each | |

Non-V3 tag families present: Customer Documents, Customer Reviews, Documents, Drafts, Emissions,
Feedback, Glossary, Health, Logs, Notifications, Organization Analytics/Assets/Bulk/Dashboard/
Data/Exports/Files/Management/Members/Metadata/Team, Reference Data, Reports, System, Upload,
User Management, Waitlist.

Single-path prefixes: `/api/waitlist`, `/api/test-upload`, `/api/upload-csv`, `/api/upload-pdf`,
`/api/upload-batch`, `/api/repair-pdf`, `/api/upload`, `/api/generate-enhanced-report`,
`/api/generate-sustainability-report`, `/api/by-document-type`, `/api/by-asset`,
`/api/verification-pending`, `/api/stats`, `/`, `/health`.

The contract also exposes **legacy `v2` and unprefixed upload/generation routes** alongside the
V3 surface. This baseline records the coexistence; it makes **no** claim about which legacy
routes are still reachable or authorised (AGENTS.md §79).

---

## 6. Database baseline A — `carbontally_demo_local` (the running stack's database)

This is the database the **running** backend resolves (`RUNTIME:` process env;
`~/ct_local_env/demo_lab/backend.env`). It is the environment in which any browser/PO review of
the current stack actually operates.

### 6.1 Structure and security surface (`DB:`)

| Metric | Value |
| --- | --- |
| Server | PostgreSQL **17.6** (`x86_64-pc-linux-gnu`, gcc 15.2.0) |
| Public tables | **154** |
| Tables with RLS enabled | **154 / 154** (100 %) |
| Policies (`pg_policies`, public) | **355** |
| `supabase_migrations.schema_migrations` | **ABSENT** (no ledger relation) |
| `auth.users` | **22** (Supabase Auth data model present) |

### 6.2 Business-data volume (`DB:` — counts, not contents)

| Domain | Table | Rows |
| --- | --- | --- |
| Factors | `emission_factors` | **7,049** |
| | `customer_factors` | **0** |
| Tenancy | `organizations` | **14** |
| | `organization_members` | **15** |
| | `users` | **23** |
| | `auth.users` | **22** |
| Consultant model | `consultant_clients` | **8** |
| | `consultant_firm_members` | **4** |
| Processing entities | `processing_entities` | **2** |
| Documents | `organization_files` | **63** |
| | `document_processing_queue` | **48** |
| | `manual_extraction_batches` | **5** |
| | `manual_extraction_items` | **48** |
| | `upload_batches` | **2** |
| Calculation | `calculation_snapshots` | **34** |
| | `emissions_logs` | **34** |
| Evidence | `evidence_line_items` | **67** |
| Reporting | `report_versions` | **4** |
| Messaging | `conversations` | **9** |
| Notifications | `notifications` | **18** |
| Commercial | `billing_plans` | **27** |
| Disclosure (P8) | `disclosure_requirement_versions` | **18** |
| Audit | `audit_trail` | **502** |
| Issues | `issues` | **10** |

Highest-volume tables (measured independently): `emission_factors` 7,049; `audit_trail` 502;
`evidence_line_items` 67; `organization_files` 63; `document_processing_queue` 48;
`manual_extraction_items` 48; `calculation_snapshots` 34; `emissions_logs` 34; `billing_plans` 27;
`users` 23. Many of the 154 tables are empty (e.g. `customer_factors` 0, `approval_requests` 0,
`approval_decisions` 0, `processing_queue` 0, `qc_*` 0, `sla_*` 0, `roles` 0, `units` 0).

### 6.3 What this database demonstrates — and what it does not

**Demonstrable (`DB:`):** a populated document→extraction→calculation→evidence chain exists in
volume (63 files, 48 queue rows, 48 extracted items, 34 calculation snapshots, 34 emissions rows,
67 evidence lines, 502 audit-trail rows). This is the only local database in which the pipeline
has *output*.

**Not demonstrable / absent (`DB:`):** customer factors (0) — so **customer-factor precedence
(AGENTS.md §15/§16) has no live data to exercise**; approvals (`approval_requests` 0,
`approval_decisions` 0) — so the review/approval workflow has no live rows; `processing_queue` 0
and `qc_*` 0 — so QC/validation lifecycle tables are empty; `roles` 0 and `units` 0 — catalogue
tables are empty.

### 6.4 Demo-identity model divergence (`CODE:` + `DB:` + `DOC:`)

| Source | Declared demo population |
| --- | --- |
| `AGENTS.md` §54 (project instruction file) | ~50 direct customer organisations, 4 customer roles each, 911 consultant-client owner identities, 50 consultants, 3 PE managers, 3 PE staff, 5 internal staff, legacy/audit identities — **total 1,185 identities**; manifest at `tools/seed_investor_demo/DEMO_IDENTITIES.md` |
| `tools/demo_lab/manifest.json` (the manifest that actually exists) | `organizations` 4, `processing_entities` 2, `actors` 14 (`lab`, `namespace`, `email_domain`, `comment`, `consultant_firm` are the other top-level keys) |
| `carbontally_demo_local` (`DB:`) | 14 organisations, 23 users, 22 auth users, 8 consultant-client relations, 2 processing entities |

The three descriptions disagree by two orders of magnitude. Recorded as **B-12** (class F).
Consequence: the §56 test-coverage expectation ("do not test only one representative user";
cross-consultant / cross-client isolation at population scale) **cannot be satisfied from the
environment as documented**; either the investor-demo dataset described by `AGENTS.md` is not
present in this checkout, or the project instructions are stale. This requires a PO/tooling
decision, not an agent guess.

---

## 7. Database baseline B — `ct_local_93d5cdd` (the developer/audit database)

This is the database named after the checkout and used by the 2026-09-27 readiness audit. It is
**not** the running stack's database.

### 7.1 Structure, security surface and data (`DB:`)

| Metric | Value |
| --- | --- |
| Server | PostgreSQL **17.6** |
| Public tables | **135** |
| Tables with RLS enabled | **135 / 135** (100 %) |
| Policies (`pg_policies`, public) | **218** |
| `supabase_migrations.schema_migrations` | **ABSENT** |
| `auth.users` | **ABSENT** — `auth` data model not provisioned (matches readiness-audit finding F-04) |
| `organizations` | 25 |
| `organization_members` | 16 |
| `users` | 658 |
| `emission_factors` | **0** |
| `customer_factors` | 5 |
| `consultant_clients` | 3 |
| `processing_entities` | 7 |
| `organization_files` | **0** |
| `document_processing_queue` | **0** |
| `upload_batches` | **0** |
| `manual_extraction_batches` | 1 |
| `manual_extraction_items` | 1 |
| `calculation_snapshots` | **0** |
| `emissions_logs` | **0** |
| `evidence_line_items` | **0** |
| `report_versions` | **0** |
| `notifications` | **0** |
| `conversations` | 10 |
| `issues` | 3 |
| `billing_plans` | 8 |
| `audit_trail` | **0** |

**Interpretation.** This database is a **schema/business-data-empty** environment for the
processing pipeline: no factors, no documents, no queue, no snapshots, no emissions, no
evidence, no audit rows. It can host structural and authorisation *unit* work; it cannot
demonstrate a workflow outcome (AGENTS.md §74). This **re-confirms** readiness-audit F-05 *for
this database* — and shows that F-05 must **not** be applied to `carbontally_demo_local`, which
is data-bearing (§6).

### 7.2 Environment divergence summary

| Dimension | `carbontally_demo_local` | `ct_local_93d5cdd` |
| --- | --- | --- |
| Public tables | 154 | 135 |
| RLS coverage | 154 / 154 | 135 / 135 |
| Policies | 355 | 218 |
| Auth data model | **present** (`auth.users` = 22) | **absent** |
| Migration ledger | absent | absent |
| Processing-pipeline data | populated | empty |
| Role in the stack | **runtime DB for the demo lab** | developer/audit DB |

Two local databases therefore describe **two different schema generations of the same product**.
Any statement of the form "the database has X" is meaningless without naming the database —
recorded as B-05 in §14.3. The cluster as a whole contains **87 databases** (`DB:` — `psql -l`
listing), of which ~71 are disposable `ct_*` clones carrying historical phase evidence; they were
**not** inspected or touched in this pass.

---

## 8. Migration baseline and drift position

### 8.1 Inventory (`CODE:`)

- Migration files: **103** (`supabase/migrations/*.sql`).
- Files with version ≥ `20261001`: **28**.
- Newest: `20261104000000_ct_consultant_client_identity_04.sql`.
- Five newest files are **untracked** in Git (never committed): `20261030000000_manual_processing_routing.sql`,
  `20261101000000_ct_mp_sub_003_consultant_coverage.sql`,
  `20261102000000_ct_consultant_model_02_capability_admission.sql`,
  `20261103000000_ct_consultant_model_03_client_access_and_mode.sql`,
  `20261104000000_ct_consultant_client_identity_04.sql`.
- The 2026-09-27 readiness audit recorded **89** files and 14 outstanding (≥ `20261001`). The chain
  has since grown by 14 files; the *applied* position has not been shown to have moved (§8.3).

### 8.2 Applied-state is **not machine-verifiable** in either local database (`DB:`)

Neither database has `supabase_migrations.schema_migrations`, so "what is applied" is knowable
only by **object probing** — the same structural limitation recorded as readiness-audit F-03
(comparator emits no artefact without a ledger) and F-06 (production state unknown).

### 8.3 Object probes in `ct_local_93d5cdd` (`DB:`)

| Probed object | Result | Introducing migration (by filename) |
| --- | --- | --- |
| `accounting_dimensions` | **ABSENT** | P17-A (≥ `20261010`) |
| `contractual_instruments` | **ABSENT** | P17-C |
| `estimation_records` | **ABSENT** | P17-D |
| `scope3_categories` | **ABSENT** | P17 (≥ `20261010`) |
| `report_schedule_definitions` | **ABSENT** | `20261023000000_ct02_scheduled_reporting.sql` |
| `backup_jobs` | **ABSENT** | `20261026000000_ct_backup_01_backup_jobs.sql` |
| `consultant_mp_allocations` | **ABSENT** | `20261101000000_ct_mp_sub_003_consultant_coverage.sql` (untracked) |
| `consultant_client_access` | **ABSENT** | `20261103000000_ct_consultant_model_03_client_access_and_mode.sql` (untracked) |
| `manual_processing_grants` | **PRESENT** | earlier Manual Processing migration |
| `staff_workload` | **PRESENT** | table pre-exists; RLS migration is `20261029000000_ct_final_03_staff_workload_rls.sql` (≥ `20261029`) |

**Reading.** Every probed object whose *only* introducing migration is ≥ `20261001` is **absent**,
which is consistent with the readiness-audit conclusion that the ≥ `20261001` chain is not applied
to `ct_local_93d5cdd`. Table **presence** for `manual_processing_grants` / `staff_workload` does
**not** demonstrate that the later RLS migrations ran against them. No claim is made about
`carbontally_demo_local`'s applied position: its schema (154 tables / 355 policies) is neither
explainable nor non-explainable from the object probes performed, and the ledger that would answer
the question does not exist.

### 8.4 Migration-position drift is the direct cause of the red test baseline

Four unit tests assert that a *specific* migration is the newest in the chain
(`test_i1_migration_is_the_latest_migration` pins `…20261007…p8_insight_data_quality_reproducibility.sql`;
`test_i2_…` and `test_p17_migrations` pin the P16 baseline; `test_d17_…` pins **71** migration
files). The working tree now contains **103**, and the newest is
`20261104000000_ct_consultant_client_identity_04.sql`. Their failures are therefore
**order-pin drift**, not product regressions (see §13.2). Recorded as **B-06**.

---

## 9. Backend baseline

| Layer | Inventory (`CODE:`) |
| --- | --- |
| API routes | 68 modules in `backend/api/`, of which **41** are `v3_*.py` |
| Domain logic | `backend/domain/` (branding, manual_processing, partners, disclosure, insight_*, report_schedule, …) |
| Data access | `backend/data/` (consultants, invitations, manual_processing, organizations, …) |
| Services | 39 modules in `backend/services/`, including `work_items.py`, `report_schedule_runner.py`, `extraction_fidelity.py` |
| Engines (16 modules) | `activity_clarification`, `ai_extraction`, `benchmarking`, `calculation`, `extraction`, `factor_matching`, `factor_selection_policy`, `invoice_extraction`, `matching_stages`, `pdf_render`, `processing_workflow`, `report_generation`, `supplier_resolution`, `validation`, `workflow` (+ `__init__`) |
| Workers | `automatic_processing.py`, `report_schedules.py` |
| Auth | `backend/auth.py` (`require_auth`, `require_org_member` → `enforce_org_path_scope`), `backend/api/dependencies.py` |

Notable structural observations:

1. **The P1 extraction shaper is a fail-safe service, not an engine.**
   `backend/services/extraction_fidelity.py` exports `PIPELINE_VERSION_P1 = "v3-auto-1.1"`,
   `SHAPE_MODE_ENV = "CARBONTALLY_P1_EXTRACTION_SHAPE"`,
   `ROLLOUT_ALLOWLIST_ENV = "CARBONTALLY_P1_ORGANIZATION_ALLOWLIST"`, and `shape_mode()`, whose
   documented behaviour is that `enabled` **without** an allowlist silently downgrades to
   `shadow`. This fail-safe design is asserted by
   `backend/tests/unit/services/test_extraction_fidelity.py`. Consequence for the baseline:
   *whether the shaper is active in the running stack is an environment property
   (`CARBONTALLY_P1_EXTRACTION_SHAPE` / allowlist), not a code property* — and neither variable
   appears in `backend/.env` (key names listed in §4.3/§5.3). `UNVERIFIED`.
2. **Two `mapping_options` implementations exist**: `backend/api/v3_processing_workflow.py:1219`
   and `backend/api/v3_operations.py:1638`. Both resolve factor candidates with the
   qualifier-tolerant selector and both layer approved **customer factors** over system factors
   (`customer_factor_mapping_options`). Recorded as `INFO` (T3/Step-2 multiline workstream);
   this baseline does **not** assert that they are equivalent or that both are reachable.
3. The v3 manual-extraction/processing surface deliberately distinguishes `automatic` vs
   `manual` from the server-side predicate `item_is_automatic`
   (`backend/api/v3_processing_workflow.py:233`), consistent with AGENTS.md §19/§26.

---

## 10. Frontend baseline

| Item | Inventory (`CODE:`) |
| --- | --- |
| Source files | 280 (`frontend/src/**/*.js` or `*.jsx`) |
| Test files | 58 (`*.test.*`) |
| V3 planes | `admin`, `capabilities`, `components`, `consultant`, `customer`, `evidence`, `insight`, `messaging`, `ops`, `pe`, `portal`, `reports` (+ `__tests__`) |
| Legacy layers retained | `frontend/App_.js`, `frontend/src/App.js` (both modified in the worktree), plus a frozen copy tree `frontend_backup_pre_v3_public_20260827/` |

New (uncommitted) surfaces present in the V3 planes: client-access guard + client portal shell
(`v3/clientAccess.jsx`, `v3/consultant/{ClientAccessTab,ClientOrgShell,ConsultantClientContext}.jsx`,
`v3/portal/`), Manual Processing customer/consultant/admin surfaces
(`v3/customer/ManualProcessingPage.jsx`, `v3/consultant/ManualProcessingCoverageTab.jsx`,
`v3/ops/{ManualProcessingTab,ManualProcessingCoverageTab}.jsx`), and multi-document upload
(`v3/customer/UploadDocumentsPanel.jsx`).

**Verification status of the frontend: `NOT RUN`.** No Jest suite, no browser journey and no
responsive/accessibility check was executed in this pass. The frontend is therefore covered in
§14 only as *code present*, never as *working*.

---

## 11. Processing-pipeline (extraction → calculation) baseline

The pipeline is the product's core value (AGENTS.md §18). This section records what the **current
parser source actually does**, measured in-process this session.

### 11.1 Live parser probe — `backend/engines/invoice_extraction.py` (`CODE:` + direct execution)

| Probe | Result |
| --- | --- |
| `_TABLE_HEADER_RE.match("Item Quantity Unit Price Amount")` | **False** (item-table header form **rejected**) |
| `_TABLE_HEADER_RE.match("Description Qty Unit Rate Subtotal")` | **True** (description-form header accepted) |
| `_ROW_RE.match("Diesel supply - Premium 2,200 litres GBP1.40 GBP3,071.20")` | **False** (ISO currency code **not accepted**) |
| `_ROW_RE.match("Diesel supply - Premium 2,200 litres £1.40 £3,071.20")` | **True** (symbol form accepted) |
| `canonical_unit("GBP")` | `None` (**correct** — currency is never a unit) |
| `canonical_unit("litres")` / `("L")` / `("m3")` / `("tonnes")` | `litres` / `l` / `m3` / `tonnes` |
| `canonical_unit("units")` | `None` — **`"units"` is not in `_KNOWN_UNITS_PARSER`** |
| `extract_invoice_lines(<Item-header invoice with GBP amounts>)` | **0 lines** |

Regex evidence (`CODE:`):

```
_TABLE_HEADER_RE = re.compile(r"(?i)^\s*description\s+(?:qty|quantity)\s+unit\s+"
                              r"(?:rate|unit\s*price|price)\s+"
                              r"(?:subtotal|net\s*amount|net\s*total|amount|total)\s*$")
_ROW_RE          = … r"[£$€]?\s*(?P<rate>…)\s+[£$€]?\s*(?P<amount>…)$"
```

### 11.2 What this means

The two defects documented in `docs/deepseek/what_was_wrong_extraction.md` (dated 2026-10-08
14:51, i.e. **the same day as this baseline**) are **still present in the current source**:

- **RC-1** — the header anchor requires the literal word `description`, so real invoices printed
  as `Item Quantity Unit Price Amount` are rejected before any row is examined.
- **RC-2** — the row pattern accepts only currency **symbols** (`[£$€]`), so amounts printed as
  `GBP1.40` never match.
- **Units vocabulary gap** — `units` is not a recognised unit, so the services-invoice form
  (`… 600 units 29.24 17545.80`) cannot be resolved as a physical quantity.

Consequence: for these real-world invoice forms the pipeline's **first stage yields zero rows**,
and everything downstream (mapping → validation → calculation → evidence → reporting) has nothing
to consume. The same document reports the measured corpus impact (12 of 144 invoices producing any
line item) — that corpus measurement is **not** re-executed here and is therefore
`DOCUMENT-ASSERTED`, while the **parser behaviour itself is `VERIFIED` this session**.

### 11.3 Related pipeline facts (`UNVERIFIED` unless stated)

| Aspect | Baseline position |
| --- | --- |
| OCR | `TESSERACT_CMD` is declared only in the demo-lab env (outside the repo) → OCR capability is an environment dependency, not a code guarantee (`RUNTIME:`) |
| P1 shaper | Fail-safe shadow mode unless an allowlist is supplied; activity in the running stack **`UNVERIFIED`** (§9.1) |
| Mapping UI explainability | `mapping_options` returns facilities/assets/suppliers + factors + customer factors and computes `has_factors`, i.e. the "why is this dropdown empty" path exists in code (`CODE:`) — no UI verification performed |
| Server-authoritative calculation | Calculation and snapshot persistence are server-side (`engines/calculation.py`, `calculation_snapshots`) (`CODE:`); idempotency/deterministic-key behaviour at runtime **`UNVERIFIED`** in this pass |
| Provenance chain | `evidence_line_items` (67 rows) and `calculation_snapshots` (34 rows) exist in the runtime DB, so a provenance chain has been **produced** at some point (`DB:`); the chain was **not** traversed end-to-end in this pass |

---

## 12. Security and tenant-isolation baseline

### 12.1 Structural controls measured this session

| Control | `carbontally_demo_local` | `ct_local_93d5cdd` | Evidence |
| --- | --- | --- | --- |
| RLS enabled on every public table | **154 / 154** | **135 / 135** | `DB:` |
| Policies defined | **355** | **218** | `DB:` |
| `FORCE ROW LEVEL SECURITY` | not probed this pass | not probed this pass | — |
| Auth data model present | yes (22 users) | **no** | `DB:` |
| Behavioural RLS evaluation (positive/negative) | **`NOT RUN`** | **`NOT RUN`** (impossible without `auth`) | — |

### 12.2 Server-side authorisation surface (`CODE:`)

- `backend/auth.py` provides `require_auth()` and org-scoped guards
  (`require_org_member()` → `enforce_org_path_scope(request, current_user)`): the F-05-R1
  org-scope enforcement registered in the CT-MP-SUB-004 IV report is present in source.
- New (uncommitted) guards exist for the consultant/client plane:
  `backend/api/client_access_guard.py`, `backend/api/client_portal/`,
  `backend/api/consultant_auth.py`, `backend/api/manual_processing_auth.py`.
- A research artefact from the same workstream
  (`Research/CT-CONSULTANT-ORGANISATION-PARITY-VERIFY-01/qa/route_guard_audit.out`) reports
  `SOURCE_ORG_PATH_DECORATORS=107` org-path guards, audited from the real `Dependant` graph. That
  artefact is `DOCUMENT-ASSERTED`; it was **not** re-executed.

### 12.3 Negative-test coverage: `NOT RUN` (explicit)

None of the mandatory negative cases in AGENTS.md §45 was executed this pass — Customer A→B,
Client A→B, Consultant A→B, Consultant A→another consultant's client, PE A→B, PE→prohibited
customer document, Viewer→write, Member→admin, Staff→Staff-Admin, Staff-Admin→System-Admin,
Customer→internal ops, PE→internal ops. Consequently **no security claim and no security denial is
made in this document**; every unexpected ALLOW remains an uninvestigated risk until an authorised
verification pass runs.

### 12.4 Carried-forward security control that must not be lost — **F-046-1**

> The integration harness's `pool` fixture executes `TRUNCATE … RESTART IDENTITY CASCADE` against
> whatever `INTEGRATION_DATABASE_URL` names. The harness must **NEVER** be pointed at a persistent
> environment whose data matters — not persistent QA, not the investor demo, **never** production.
> Integration suites must target a disposable clone (`ct_*`) or `carbontally_test`; the fixture
> itself refuses targets matching `qa`/`demo`/`investor`/`prod`/`live` with an explicit `F-046-1`
> error. (Source: `CT-PO-CT-READINESS-01-…-REPORT.md` §8.1; `DOCUMENT-ASSERTED` — not re-executed.)

This constraint directly governs any future attempt to run the integration suite against the
**data-bearing** `carbontally_demo_local` database described in §6.

### 12.5 Secret hygiene

No credential, JWT, signed URL or demo password was read, printed or recorded. Database DSNs are
quoted with the password redacted. No tracked file contains an `.env` (§4.3).

---

## 13. Test baseline — exact runs performed this session

### 13.1 Runs

| # | Command (scope) | Collected | Result | Suite verdict |
| --- | --- | --- | --- | --- |
| 1 | `pytest backend/tests/unit --ignore=backend/tests/unit/api` | **2,537** | **7 FAILED**; process exit code **1** | **RED** |
| 2 | `pytest backend/tests/unit/engines` | **389** | **3 FAILED** (all in `test_extraction_suggestions.py`) | **RED** |
| 3 | `pytest backend/tests/unit/data/test_{d17_provider_ownership_migration_revision,i1_insight_migration,i2_insight_authorization_contracts,p17_migrations}.py` | — | **4 FAILED** | **RED** |
| 4 | `pytest backend/tests/unit/api --collect-only` | **2,788** | **`NOT RUN`** (suite not executed this pass) | — |
| 5 | Frontend Jest suite (58 test files) | — | **`NOT RUN`** | — |
| 6 | `backend/tests/integration`, `backend/tests/e2e` | — | **`NOT RUN`** (must not target data-bearing DBs — F-046-1, §12.4) | — |

> **Passed-count note.** As recorded in §2.4, this environment's `pytest 9.1.1` does not emit the
> final `N failed, M passed` line into captured output, so the number of *passing* tests is **not**
> asserted here. The failure set is exact and fully enumerated below.

### 13.2 The 7 failures, with cause

**Group A — migration-ordering pins invalidated by newer migrations (4 tests; §8.4):**

| Test | Assertion observed |
| --- | --- |
| `…/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | `assert 103 == 71` (test pins 71 migration files; the tree now has **103**) |
| `…/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | pinned newest `20261007000000_p8_insight_data_quality_reproducibility.sql`; the actual set contains later files |
| `…/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | actual newest is `20261104000000_ct_consultant_client_identity_04.sql` |
| `…/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | `unexpected migration after the P16 baseline: 20261029000000_ct_final_03_staff_workload_rls.sql` |

**Group B — extraction-suggestion expectation drift (3 tests):**

| Test | Assertion observed | Reading |
| --- | --- | --- |
| `…/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | `assert '2026-01-15' == '15/01/2026'` | the engine returns the **ISO-normalised** date; the test pins the printed day-first form. `docs/deepseek/what_was_wrong_extraction.md` §9 lists "day-first date normalisation to ISO" under *What Works (Do Not Break)*, so the **test expectation** is the stale side — but resolving it is an implementation decision, not PO policy |
| `…::test_suggest_missing_fields_leave_unresolved` | `assert {'extraction_evidence': {'supplier_header': {'candidates': [], 'reason': 'no candidate line', 'strategy': 'header_block'}}} == {}` | the engine now returns a provenance/evidence object where the test expects `{}` |
| `…::test_suggest_no_fabrication_on_garbage` | same assertion shape as above | same cause |

### 13.3 Test-baseline conclusion

**The unit test baseline is RED (7 failures), and no suite may currently be quoted as green.**
Group A is a direct consequence of uncommitted migration additions (§4/§8). Group B is an
engine-vs-test expectation drift in the extraction-suggestion layer. Until both are resolved, any
"all tests pass" statement about this repository is unverifiable. Recorded as **B-01** (P1).

---

## 14. Coverage matrix and Known Findings Register

### 14.1 Coverage matrix (`A–G` placement × evidence status)

| # | Capability domain | Code location (spot-checked) | Live object | Class | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Repository / release identity | whole tree | — | A | **VERIFIED** (`GIT:`) |
| 2 | Local API runtime | `backend/main` app, `uvicorn` pid 1014820 | — | A | **VERIFIED** (health 200, v3.0.0) |
| 3 | Local frontend runtime | `frontend/src/App.js`, `src/v3/*` | — | A | **VERIFIED** (HTTP 200 only); UI behaviour `NOT RUN` |
| 4 | Supabase substrate (gateway, kong, auth, rest, realtime, storage, mailpit) | `tools/demo_lab/stack.py` | 14 containers | A | **VERIFIED** (up, gateway 200) |
| 5 | Auth data model | `auth.users` | demo: 22 rows; dev: **absent** | **A / D** | **VERIFIED** |
| 6 | RLS policies | 89+ RLS migrations | demo: 355; dev: 218 (all tables RLS-on) | A | **VERIFIED** structurally; behavioural evaluation `NOT RUN` |
| 7 | Migration chain (files) | `supabase/migrations/` | 103 files (28 ≥ `20261001`) | A | **VERIFIED** inventory; applied state `G` |
| 8 | Migration ledger | `supabase_migrations.schema_migrations` | **absent in both DBs** | **D** | **VERIFIED** |
| 9 | API contract | 68 route modules | 654 paths / 777 operations live | A | **VERIFIED** |
| 10 | Factor catalogue | `backend/data/factors*`, `emission_factors` | demo: **7,049**; dev: **0** | **A / D** | **VERIFIED** |
| 11 | Customer factors (precedence) | `customer_factor_mapping_options` | demo: **0 rows** | **D** (no live data) + A (code) | **VERIFIED** absent → precedence untestable live |
| 12 | Documents / queue | `v3_document_uploads`, `automatic_processing` | demo: 63 files, 48 queue; dev: 0 | **A / D** | **VERIFIED** |
| 13 | Invoice table parser | `engines/invoice_extraction.py` | — | **F** | **VERIFIED** defective for real forms (§11) |
| 14 | Extraction suggestions | `engines/ai_extraction`, suggestion layer | — | **F** | **VERIFIED** engine-vs-test drift (§13.2) |
| 15 | Mapping / factor selection | `api/v3_processing_workflow.py:1219`, `api/v3_operations.py:1638` | factors reachable | A (code) | behaviour `G` (`NOT RUN`) |
| 16 | Calculation + snapshots | `engines/calculation.py`, `calculation_snapshots` | demo: **34** snapshots / 34 emissions | A | **VERIFIED** rows exist; end-to-end chain `G` |
| 17 | Evidence / provenance | `evidence_line_items`, disclosure evidence tables | demo: **67** rows | A | **VERIFIED** rows exist; chain not traversed |
| 18 | Review / approval | `approval_requests`, `approval_decisions` | demo: **0 / 0** rows | **D** (no live data) | **VERIFIED** absent |
| 19 | QC / validation lifecycle | `qc_checks`, `qc_errors`, `manual_review_queue` | demo: 0 rows | **D** | **VERIFIED** absent |
| 20 | Reporting (versions / schedules) | `report_versions`, `report_schedule_definitions` | demo: 4 versions, schedule table exists (0 rows); dev: table **absent** | A(empty) / **B** | **VERIFIED** |
| 21 | Manual Processing commercial | `api/manual_processing_admin.py`, `domain/manual_processing.py`, untracked migrations | demo: allocations **13**, grants **1**, processors **1**, subscriptions **4**, billing config **7**; dev: tables absent/0 | **A (demo) / B (dev)** | **VERIFIED** applied in the runtime DB **from uncommitted migrations** |
| 22 | Consultant model v2/v3 | `api/v3_consultants.py`, `api/admin_consultant_commercial.py`, untracked migrations | demo: `consultant_mode_change_requests` 2, `consultant_relationship_requests` 0; dev: **absent** | **A (demo) / B (dev)** | **VERIFIED** |
| 23 | Client-access guard (consultant→client) | `api/client_access_guard.py`, `v3/clientAccess.jsx`, `v3/portal/` | — | A (code) | behaviour `G` (`NOT RUN`) |
| 24 | Messaging | `conversations`, `messages`, `v3/messaging` | demo: 9 conversations / 10 messages; dev: 10 | A | objects **VERIFIED**; N1 boundary behaviour `G` |
| 25 | Notifications | `notifications`, notification services | demo: **18** rows; dev: 0 | A | objects **VERIFIED**; N1–N4 `IMPLEMENTED, NOT INDEPENDENTLY VERIFIED` |
| 26 | Insight (P8 I1–I6) | `api/v3_*insight*`, `carbontally_insight_*` | demo: conversations 4, messages 7, interactions 3, tool calls 1 | A (partial) | **VERIFIED** (demo); dev `NOT PROBED` |
| 27 | Disclosure / Scope-3 (P17) | `domain/disclosure.py`, `disclosure_*` | demo: `disclosure_requirement_versions` 18; dev: 0 and P17 objects **absent** | **A / B** | **VERIFIED** (divergent) |
| 28 | Billing / commercial config | `billing_*` | demo: `billing_plans` 27; dev: 8; `billing_commercial_config` 7 in both | A | **VERIFIED** |
| 29 | Processing-entity model | `processing_entities`, `api/v3_operations.py` | demo: **2**; dev: **7** | A | **VERIFIED** |
| 30 | Backup / restore subsystem | `backend/backup/`, `ct_backup_0*` migrations | dev: `backup_jobs` **absent**; demo: not probed | **B / G** | **UNVERIFIED** |
| 31 | Public website + assistant | `frontend/src/public/`, `src/public/assistant/` | — | A (code) | behaviour `G` (`NOT RUN`) |
| 32 | Admin control plane (`/ops` canonical, `/admin` deprecated) | `frontend/src/App.js`, `CSTR-FINAL03-BLK1-…` investigation | — | A (code) | documented `DOC:`; runtime `G` |
| 33 | QA harness | `qa_harness/` (16 entries) | — | A (code) | **`NOT RUN`** |
| 34 | e2e environment | `e2e/environment/scripts/canonical_schema_rebuild.sh` | stale migration subset (F-08) | **F** | **UNVERIFIED** this pass |

### 14.2 Carried-forward findings register (original IDs preserved; not silently re-labelled)

**Source `S1` — `CT-PO-CT-READINESS-01-MIGRATION-DRIFT-AND-CANONICAL-DB-BASELINE-AUDIT-20260927-REPORT.md` (2026-09-27).**

| ID | Sev | Headline (as originally recorded) | Original class | Position in this baseline |
| --- | --- | --- | --- | --- |
| F-01 | P1 | CI migration-drift gate cannot run (`secrets` context in a step `if:` → 0 jobs → gate inert) | VERIFIED | **`UNVERIFIED` today** — CI not inspected this pass |
| F-02 | P1 | `MIGRATION_DRIFT_DATABASE_URL` unset → ledger comparison inert by default | VERIFIED (design) | `UNVERIFIED` today |
| F-03 | P2 | Ledger mode without a ledger exits 1 with a raw traceback and writes no artefact | VERIFIED (reproduced) | **Still structurally true**: neither local DB has a ledger (§8.2) |
| F-04 | P2 | Local DB has no Supabase Auth data model → authenticated/RLS E2E cannot be validated locally | VERIFIED | **Re-confirmed for `ct_local_93d5cdd`**; **not true of `carbontally_demo_local`** (22 auth users) — statements must now name the DB |
| F-05 | P2 | Local DB business-data-empty (0 factors / documents / snapshots / emissions) | VERIFIED | **Re-confirmed for `ct_local_93d5cdd`**; **superseded for `carbontally_demo_local`** (7,049 factors; 34 snapshots; 67 evidence rows) |
| F-06 | P2 | Production migration state `UNKNOWN`; no safe evidence path | UNVERIFIED (BLOCKED) | Unchanged — production not contacted |
| F-07 | P3 | No historical gate evidence (0 artefacts ever) | VERIFIED | `UNVERIFIED` today |
| F-08 | P3 | e2e stack carries a stale migration subset (53 of 89 files) | VERIFIED | `UNVERIFIED` today; the divergence is now larger (103 files in the chain) |
| F-09 | INFO | Repository-side migration hygiene PASS (89 files, no anomalies) | VERIFIED | `UNVERIFIED` today (103 files, not re-linted) |
| F-046-1 | — | Integration harness `TRUNCATE` guard — must never target data-bearing DBs | Mandatory carry-forward | **Restated in §12.4; still binding** |

**Source `S2` — commit history (`CT-FINAL-01`, 2026-09-29).** CT-VERIFY-06 blockers **D-0, D-2, D-3,
D-5, D-6** are recorded as *closed* by commit `5216c71`. Position here: **closed per Git history, not
re-verified** (no re-test performed).

**Source `S3` — `docs/architecture/CT-MP-SUB-004-independent-verification-report.md` (2026-10-04; independent verification).**

| ID | Sev | Headline | Original class | Position now |
| --- | --- | --- | --- | --- |
| F-1 | **HIGH** | UI delivered against a UI/UX spec that is **not PO-approved** (`CT-UX-MP-SUB-003` self-declares *NOT YET AUTHORIZED*) — an acceptance-authority gap, not a code defect | PO DECISION REQUIRED | **Open** — §15.2 item PD-A |
| F-2 | LOW | Implementation report overstated internal-staff access; actual behaviour is stricter (403) | doc inaccuracy; behaviour accepted | Closed (handover) |
| F-3 | MEDIUM | `ConsultantPage.jsx` diff contained out-of-scope copy changes; attribution unresolvable from the worktree | NOT VERIFIABLE | Closed/accepted — root cause is the **same dirty-worktree condition** present today (§4) |
| F-5 | MEDIUM | Positive MP coverage states not browser-verifiable (no purchased coverage seeded) | BLOCKED BY ENVIRONMENT | Closed by PD-5 fixture work (independently verified) |
| F-6 | PARTIAL | Admin operational tab still labelled **Manual Processing** | PARTIAL | PO accepted |
| F-7 | LOW | `consultant_allocate_client` maps **any** exception to a 409 "already has an allocation" — error-fidelity risk (AGENTS §46) | robustness | **Required before production** — still open |
| F-8 | INFO | Any active firm member may read coverage; `manage_clients` required for allocate/release | INFO | PO-ratified split |
| F-9 | INFO | No client-supplied idempotency key on allocation writes | INFO | **Required before production** — still open |
| F-10 | INFO | Customer not-entitled copy merges two spec sections | INFO | Accepted |
| F-11 | INFO | Admin coverage tab takes raw ids (no picker) | INFO | **Required before production** — still open |
| NV-1…NV-4, NV-8 | — | Browser/DB coverage states; allocate/release against the real DB; admin tab with data | BLOCKED BY ENVIRONMENT | Closed by PD-5 fixture verification |
| NV-5 | — | Responsive behaviour at AGENTS §49 viewports | NOT VERIFIED | **Still open** (`NOT RUN` here too) |
| NV-6 | — | Accessibility audit | NOT VERIFIED | **Still open** (`NOT RUN` here too) |
| NV-7 | — | Pixel-level D2 comparison | NOT VERIFIED | Closed by PO decision |
| NV-9, NV-10 | — | Long-running/performance; email side-effects | Out of scope | Unchanged |

**Source `S4` — `docs/architecture/carbontally_master_handover_2026-10-05.md` (2026-10-05).**

| ID | Decision / finding | Position in this baseline |
| --- | --- | --- |
| PD-1 … PD-6 | Manual Processing product/commercial decisions | Ratified. PD-6 (allocation-table migration review gate) is **satisfied locally** — the runtime DB carries `consultant_mp_allocations` — but that migration remains **uncommitted** (§14.3 B-06) |
| N-1 | Fixture reset invalidates existing lab auth tokens until re-login | Accepted QA caveat |
| N-2 | Documentation attribution issue for a pre-existing `stack.py` change | Accepted documentation issue |
| P-1 | No dedicated production SLO for MP coverage operations in this release | PO decided |
| P-2 | Coverage allocation/release is audit-only (creates no notifications) | PO decided |
| N1–N4 | Manual Processing in-app notification decisions (email **not** authorised; DB is the source of truth; no opt-out system) | **IMPLEMENTED, self-verified — NOT independently verified** |
| Required before production | F-4 (tooling/test reliability), F-7, F-9, F-11, NV-5, NV-6 | Still outstanding — and **F-4 is materially worse today: the unit baseline is RED** (§13.3) |
| Not authorised | Production migration/deployment; provider-specific billing; platform SLO policy; email delivery for N1–N4; notification preferences; Realtime delivery fix; I3 tool-catalogue expansion | Unchanged |

### 14.3 New baseline findings produced by this pass

| ID | Sev | Finding | Class | Evidence |
| --- | --- | --- | --- | --- |
| **B-01** | **P1** | **Unit test baseline is RED: 7 failures / 2,537 collected** (4 migration-order pins + 3 extraction-suggestion drifts). No suite may be quoted as green. | F | `TEST:` §13 |
| **B-02** | **P1** | **Invoice table parser still rejects the real invoice forms**: header anchored on the literal `description` (`Item Quantity Unit Price Amount` → no match) and rows accept only `[£$€]` symbols, not ISO codes (`GBP1.40` → no match). A two-row `Item`-header/GBP invoice extracts **0 lines**. | F | executed probe §11.1; corroborates `docs/deepseek/what_was_wrong_extraction.md` (same day) |
| **B-03** | **P2** | Units vocabulary gap: `"units"` is not canonical (`canonical_unit("units") is None`), so the services-invoice quantity form cannot resolve. (`"GBP"` → `None` is **correct** and must not be "fixed".) | F | executed probe §11.1 |
| **B-04** | **P2** | **Runtime configuration drift**: the repository `backend/.env` (`PORT=8060`, `SUPABASE_URL=http://127.0.0.1:19999`) does **not** describe the running stack (`:8070`, `http://127.0.0.1:54430`); `19999` is not a listening socket. Tools/tests run with repo env would target a dead endpoint. | F | `RUNTIME:` §5.3 |
| **B-05** | **P2** | **Two divergent local schema generations**: `carbontally_demo_local` 154 tables / 355 policies (data-bearing, auth present) vs `ct_local_93d5cdd` 135 tables / 218 policies (no auth, pipeline-empty). No ledger in either. Statements about "the database" are ambiguous unless the DB is named. | F | `DB:` §6.1/§7.1 |
| **B-06** | **P2** | **Five migrations exist only as uncommitted files** (`20261030`–`20261104`), yet the **runtime DB has been provisioned from them** (`manual_processing_processors` 1 row, `consultant_mp_allocations` 13 rows, `consultant_mode_change_requests` 2) while the **dev DB has none of those objects**. The red migration-order tests are a direct consequence. | F | `CODE:`+`DB:` §4.1/§8.3/§8.4 |

| **B-07** | **P3** | The 2026-10-05 handover's frozen release SHA (`375a48d…`) is **not** HEAD (`3fec874…`, +1 documentation commit). | F | `GIT:` §3 |
| **B-08** | **P3** | Readiness-audit **F-05** (database business-empty) is true only of `ct_local_93d5cdd`; `carbontally_demo_local` is data-bearing. Historical findings must be re-scoped by database. | F | `DB:` §6.2/§7.1 |
| **B-09** | **P2** | **Review/approval and QC lifecycle have no live data anywhere**: `approval_requests` 0, `approval_decisions` 0, `processing_queue` 0, `qc_checks` 0, `customer_review_log` 0, `ai_content_history` 0 — in *both* databases. | D | `DB:` §14.1 rows 18–19 |
| **B-10** | **P2** | The API-unit suite (**2,788 tests**), the frontend Jest suite (58 files), integration and e2e suites were **not executed** in this pass → the largest automated coverage surface is unmeasured. | G | §13.1 |
| **B-11** | **P3** | `AGENTS.md` §54 points at `tools/seed_investor_demo/DEMO_IDENTITIES.md`, which **does not exist**; the manifest actually present is `tools/demo_lab/manifest.json`. | F | `CODE:` §3.1 |
| **B-12** | **P2** | **Demo-identity model divergence**: `AGENTS.md` §54 asserts **1,185** demo identities; `tools/demo_lab/manifest.json` declares **4 organisations / 2 processing entities / 14 actors**; the demo DB holds **14 organisations / 23 users / 22 auth users**. The §56 population-scale isolation expectation cannot be met from the environment as documented. | F | `CODE:`+`DB:` §6.4 |
| **B-13** | **P3** | `customer_factors` is empty (**0 rows**) in the runtime DB, so **customer-factor precedence (AGENTS §15/§16) has no live data** to demonstrate; likewise the `roles` and `units` catalogue tables (0 rows). | D | `DB:` §6.2/§6.3 |
| **B-14** | INFO | Two `mapping_options` implementations coexist (`v3_processing_workflow.py:1219`, `v3_operations.py:1638`); equivalence/reachability not assessed. | F | `CODE:` §9 |
| **B-15** | INFO | The live OpenAPI contract still exposes legacy `v2` and unprefixed upload/report-generation routes alongside 371 `/api/v3` paths; reachability/authorisation not assessed. | F | `RUNTIME:` §5.4 |

### 14.4 Implementation vs independent verification ledger

| State | Capabilities (as at this baseline) |
| --- | --- |
| **VERIFIED this session** | Repo identity/HEAD; working-tree accounting; runtime liveness (API/frontend/gateway); API contract size; both local DB structures, RLS counts and volumes; migration inventory and object probes; parser behaviour; the 7 unit failures |
| **IMPLEMENTED, self-verified only** (not independently verified) | Manual Processing N1–N4 notifications (`S4`); the whole uncommitted consultant-organisation-parity / client-access / MP-coverage change set (§4) |
| **IMPLEMENTED, unverified in this environment** | Mapping factor selection (incl. customer-factor precedence), calculation idempotency, evidence-chain traversal, report generation, messaging boundaries (N1 model), `/ops` vs `/admin` topology, public website/assistant |
| **INDEPENDENTLY VERIFIED (historically, by another agent)** | PD-5 MP coverage fixture; P8 I1–I5 insight persistence/authorization/tools (`docs/verification/*`); CT-MP-SUB-004 security negatives (19/19 held, per `S3`) — all **as of their own dates**, not re-run here |
| **BLOCKED / NOT VERIFIABLE here** | Production state (F-06); behavioural RLS (no credentials used); responsive (NV-5) and accessibility (NV-6) verification; long-running/performance behaviour |
| **ACCEPTED** | **Nothing.** No PO acceptance is claimed or implied anywhere in this document (AGENTS §73). |

---

## 15. Remaining limitations, PO decisions required, next actions and verdict

### 15.1 Limitations of this baseline

1. **Coverage is partial by construction.** Unit scope only; 2,788 API-unit tests, 58 frontend
   test files, integration and e2e were not executed (§13.1). No workflow outcome is declared.
2. **No behavioural security evidence.** RLS was inspected structurally, not exercised; no
   authenticated session, no negative boundary test (§12.3).
3. **Applied-migration state cannot be proven** for either local database (no ledger); conclusions
   rest on object probes (§8.3).
4. **The runtime DB's full applied position is unknown.** `carbontally_demo_local` demonstrably
   contains objects created by *uncommitted* migrations, so its schema cannot be mapped 1:1 to any
   committed migration set.
5. **Production is `UNKNOWN`** and was deliberately not contacted (F-06 unchanged).
6. **Passed counts are not asserted** because the toolchain in this environment does not emit them
   (§2.4).
7. **No claim is made about the correctness of any factor, any emissions number, or any report** —
   only about existence, volume and structure of the rows that hold them.

### 15.2 PO decisions required (`PO DECISION REQUIRED`)

| Ref | Decision needed | Why it blocks |
| --- | --- | --- |
| **PD-A** | Ratify or withdraw `CT-UX-MP-SUB-003` (the Manual Processing UI/UX spec that `S3` F-1 records as implemented-but-not-authorised), or direct re-scoping of the delivered UI | Acceptance authority for the delivered MP UI does not exist (S3 F-1, HIGH, still open) |
| **PD-B** | Which demo/identity model is authoritative: the §54 "1,185 identities / investor demo" model or the `tools/demo_lab/manifest.json` model (B-11/B-12) | Determines what population-scale isolation testing is even possible locally |
| **PD-C** | Whether extraction must support the **real-world invoice forms** now failing (B-02/B-03), and whether spend-based (`£`/`unit`-based) factors are in scope | Decides whether the pipeline's first stage is a P0 fix or an accepted limitation |
| **PD-D** | Authorised evidence environment for workflow/RLS/end-to-end verification (recurring action A4 of `S1`), and whether credentials may be issued for it | Without it every workflow claim remains `UNVERIFIED` |
| **PD-E** | Whether the uncommitted consultant-organisation-parity change set (B-06) is to be committed as the next release baseline, or held | The red migration-order tests cannot be resolved while the intent is unresolved |
| **PD-F** | Retention (N3) durations and enforcement scope remain configuration-only and unratified numerically (AGENTS §42) | Blocks any retention claim |

### 15.3 Proposed next actions (not authorised; for PO/backlog assignment)

| # | Action | Owner | Class |
| --- | --- | --- | --- |
| A-1 | Restore a green unit baseline: re-pin or generalise the four migration-order tests **and** resolve the three extraction-suggestion expectations (B-01) | Implementation | P1 |
| A-2 | Fix the invoice table parser header + ISO-currency forms and extend the units vocabulary (B-02/B-03), with regression tests over the real forms | Implementation | P1 |
| A-3 | Run the API-unit suite (2,788) and the frontend Jest suite once, and record exact results | Implementation | P2 |
| A-4 | Issue/refresh the repository `backend/.env` (or document explicitly that the demo-lab env outside the repo is the only supported runtime env) (B-04) | Implementation / PO | P2 |
| A-5 | Record an explicit statement of which database is authoritative for which QA purpose, and name the database in every future finding (B-05/B-08) | Documentation | P2 |
| A-6 | Characterise the two local schemas against the migration chain by object-level fingerprint (the readiness-audit method), now that 103 files exist | Implementation | P2 |
| A-7 | Provide behavioural RLS / negative-boundary verification against an authorised environment (PD-D) | Independent verification | P1 when unblocked |
| A-8 | Reconcile `AGENTS.md` §§54–56 with the demo tooling that actually exists (B-11/B-12) | PO + Documentation | P2 |
| A-9 | Re-run the CT-PO-CT-READINESS-01 CI-gate findings F-01/F-02/F-07/F-09, which are stale rather than disproven | Implementation | P2 |
| A-10 | Keep F-046-1 in force for every future integration run (§12.4) | All agents | Standing |

### 15.4 Verdict

**This task is `COMPLETE_WITH_OBSERVATIONS`.** A full read-only foundation baseline was captured
and verified against current runtime, database, Git and test evidence; nothing was changed except
the addition of this document.

- **Implemented:** this document only.
- **Tested:** two unit-scope pytest scopes (2,537 collected; 7 failures enumerated) plus
  in-process parser probes.
- **Verified:** repository identity and working-tree accounting; runtime liveness and API contract
  size; both local databases' structure, RLS counts and volumes; migration inventory and applied
  boundary by object probe; the parser defects; the exact unit failure set.
- **Not verified:** every workflow outcome, every authorisation boundary, the API/frontend/
  integration test suites, responsive and accessibility behaviour, production state, and the
  applied-migration position of the runtime database.
- **Accepted:** nothing.

**Headline position.** The release/repository state is *stable but dirty and drifted*: a frozen
release plus a large uncommitted extension set; a **red** unit test baseline; a **runtime database
that is ahead of the committed code**; two divergent local schemas with **no migration ledger**;
and an extraction parser that still **cannot read the real invoice forms the product exists to
process**. None of this is a security finding — it is a *foundation* finding, and it should be
resolved before any further acceptance claim is made.

---

## Appendix A — exact evidence acquisition (reproducible)

```bash
# --- repository identity / working tree -------------------------------------
git -C /home/shomonrobie/ct_93d5cdd rev-parse HEAD
git -C /home/shomonrobie/ct_93d5cdd status --porcelain | awk '{print $1}' | sort | uniq -c
git -C /home/shomonrobie/ct_93d5cdd diff --stat | tail -1
git -C /home/shomonrobie/ct_93d5cdd check-ignore -v backend/.env frontend/.env.local
git -C /home/shomonrobie/ct_93d5cdd ls-files | grep -E '(^|/)\.env'        # → empty

# --- structural counts ------------------------------------------------------
find backend -name '*.py' -not -path '*/.venv/*' | wc -l                    # 717
find backend/tests -name 'test_*.py' | wc -l                               # 340
find frontend/src -type f \( -name '*.jsx' -o -name '*.js' \) | wc -l      # 280
find frontend/src -type f -name '*.test.*' | wc -l                         # 58
ls supabase/migrations/*.sql | wc -l                                       # 103
ls supabase/migrations/*.sql | xargs -n1 basename | awk -F_ '$1 >= "20261001000000"' | wc -l   # 28
find docs -name '*.md' | wc -l                                             # 927

# --- runtime ----------------------------------------------------------------
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8070/health
curl -s http://127.0.0.1:8070/openapi.json | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(len(d['paths']), sum(len(v) for v in d['paths'].values()))"
ss -ltnp | head -30
docker ps --format '{{.Names}} {{.Ports}}'

# --- database (READ-ONLY) ---------------------------------------------------
for DB in carbontally_demo_local ct_local_93d5cdd; do
  docker exec supabase_db_carbon_ledger psql -U postgres -d "$DB" -A -t -c \
    "select count(*) from information_schema.tables where table_schema='public';"
  docker exec supabase_db_carbon_ledger psql -U postgres -d "$DB" -A -t -c \
    "select count(*) from pg_policies where schemaname='public';"
  docker exec supabase_db_carbon_ledger psql -U postgres -d "$DB" -A -t -c \
    "select coalesce(to_regclass('public.estimation_records')::text,'ABSENT');"
done

# --- tests ------------------------------------------------------------------
backend/.venv/bin/python -m pytest backend/tests/unit --ignore=backend/tests/unit/api -q --tb=no
backend/.venv/bin/python -m pytest backend/tests/unit/engines -q --tb=no
backend/.venv/bin/python -m pytest backend/tests/unit/api --collect-only -q

# --- parser probe (in-process, read-only) -----------------------------------
backend/.venv/bin/python - <<'PY'
import sys; sys.path.insert(0, 'backend')
from engines.invoice_extraction import _TABLE_HEADER_RE, _ROW_RE, canonical_unit, extract_invoice_lines
print(bool(_TABLE_HEADER_RE.match('Item Quantity Unit Price Amount')))          # False
print(bool(_ROW_RE.match('Diesel supply - Premium 2,200 litres GBP1.40 GBP3,071.20')))  # False
print(canonical_unit('GBP'), canonical_unit('units'))                           # None None
print(len(extract_invoice_lines('Item Quantity Unit Price Amount\nDiesel 2,200 litres GBP1.40 GBP3,071.20')))  # 0
PY
```

## Appendix B — evidence file index (this session, `/tmp`)

| File | Contents |
| --- | --- |
| `ct_base_git.txt`, `ct_base_meta.txt`, `ct_base_status.txt`, `ct_status_counts.txt`, `ct_ev_git2.txt` | Git identity, log, remotes, status/diff accounting, ignore rules |
| `ct_ports.txt`, `ct_procs.txt`, `ct_ev_db2.txt` (process env), `ct_runtime_http.txt`, `ct_api.txt` | Runtime topology, listening sockets, containers, liveness, OpenAPI surface |
| `ct_ev_db2.txt`, `ct_ev_mp_demo.txt`, `ct_ev_mp_dev.txt`, `ct_ev_cons.txt`, `db_verify_both.txt`, `db_tables.txt`, `db_rls.txt`, `db_policy_counts.txt`, `db_rowcounts_exact.txt`, `db_databases.txt` | Database structure, RLS, policies, row counts, object probes |
| `ct_ev_mig.txt`, `ct_ev_untracked_mig.txt`, `ct_stack_migrations.txt`, `ct_mig_tail.txt` | Migration inventory, untracked migrations and the objects they create |
| `ct_ev_counts.txt`, `ct_ev_paths.txt`, `ct_ev_final.txt`, `ct_tree_counts.txt`, `ct_frontend_tree.txt` | Structural counts, module lists, engine/worker inventory, V3 planes |
| `ct_pytest_nonapi2.txt`, `ct_pytest_nonapi2_summary.txt`, `ct_ev_fail7.txt`, `ct_collect_nonapi.txt` | Unit test runs, collection counts, exact failure reasons |
| `ct_ev_parser.txt`, `ct_verify_rc.txt`, `ct_verify_rc2.txt` | Parser source and in-process behaviour probes |
| `ct_extra10..ct_extra21.txt`, `ct_ids2.txt`, `ct_ids3.txt`, `ct_iv_findings.txt`, `ct_handover_*.txt`, `ct_docs_*.txt` | Document headings, finding-ID scans, handover extracts, baseline documents |
| `ct_outofrepo_env.txt`, `ct_env_backend.txt`, `ct_env_frontend.txt`, `ct_ls_tmp.txt` | Environment key names (no secret values) and evidence index |

## Appendix C — safety confirmation

| Control | Confirmation |
| --- | --- |
| Database writes | **None.** Read-only queries only (`count(*)`, `to_regclass`, catalog views) |
| Migrations applied | **None** |
| Seeds / truncates / drops | **None** |
| Services started/stopped/restarted | **None** |
| Production contacted | **No** |
| Investor-demo / runtime data mutated | **No** — `carbontally_demo_local` was read only |
| Repository changes | **One new untracked document** (this file); no tracked file modified, nothing staged, no commit, no push |
| Git history operations | **None** (no reset/clean/rebase/amend/force-push) |
| Secrets printed or stored | **None** (DSNs redacted; key names only) |

*End of `CT-CARBONTALLY-FOUNDATION-BASELINE-01`.*
