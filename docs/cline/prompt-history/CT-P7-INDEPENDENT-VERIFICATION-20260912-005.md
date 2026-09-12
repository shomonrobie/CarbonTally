# CT-P7-INDEPENDENT-VERIFICATION-20260912-005

**Prompt Ref:** `CT-P7-INDEPENDENT-VERIFICATION-20260912-005`
**Date:** 2026-09-12
**Authority:** Product Owner
**Type:** **INDEPENDENT VERIFICATION** (not implementation). This task did not modify application code, schema, migrations, RLS, APIs, frontend, or tests; it produced this report only.
**Implementation reviewed:** `CT-P7-AUDITABILITY-IMPLEMENTATION-20260912-004`

**VERDICT: `PHASE 7 INDEPENDENTLY VERIFIED WITH ACCEPTED RESIDUALS — READY FOR CLOSURE`**
(Closure is **not** self-authorised; see §27/§28. Several environment-limited checks are marked **NOT VERIFIED**, not PASS.)

---

## 1. Verification Scope

Independently determine whether the Phase 7 implementation satisfies the approved objective and the Phase 7 acceptance criteria, using **actual** source code, database behaviour, tests, and authorization behaviour — not the implementation report's claims.

Out of scope: fixing defects, implementing residuals, applying production migrations, or self-authorising closure.

## 2. Repository State

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `3c8158604ae538bd7ac6656afac9b1acf7476ce1` |
| `origin/main` | `9e13236149b8132d737258abc0aa7d69a974a85b` |
| Ahead / behind | `0 / +2` (2 commits ahead of origin, **not pushed**) |
| Implementation commit | `436815721aa2ec4b1d8ccd4f23d80c196fdbb109` (present) |
| Docs commit | `3c8158604ae538bd7ac6656afac9b1acf7476ce1` (present) |
| Worktree | dirty (pre-existing): **208 modified**, **52 untracked**, staged **0** |
| Pre-existing changes preserved | **Yes** — not reset/cleaned/modified |
| Commits since implementation | 1 (the docs commit only) |
| Phase 7 commits pushed | **No** |

## 3. Source Documents Reviewed

Blueprint V1.3 (§5 Actor Model, §13 Authorization, §14 RLS) · Master Roadmap V1.0 · Production Authentication & Access Spec 20260911 · Phase-6 closure/release boundary · `CT-P7P8-HISTORICAL-DECISION-ARCHAEOLOGY-20260911-001.md` · `CT-P7P8-ROLE-REPORT-CATALOGUE-20260912-002.md` · `CT-P7-AUDITABILITY-IMPLEMENTATION-20260912-004.md` · `CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md` · `CARBONTALLY_TERMS_OF_SERVICE_DRAFT.md` §11.1.

**Actual implementation inspected** (at HEAD = implementation commit content): `backend/domain/audit.py` · `backend/data/audit.py` · `backend/data/reporting.py` · `backend/api/dependencies.py` · `backend/api/v3_reporting.py` · `backend/api/v3_exports.py` · `backend/api/router.py` · `backend/main.py` · `frontend/src/v3/ops/AuditConsoleTab.jsx` · `frontend/src/v3/admin/{AdminPage,AuditTab}.jsx` · `frontend/src/v3/api.js` · migration `20260912000000_p7_audit_immutability_and_indexes.sql`.

## 4. Implementation Commit Reviewed

`436815721aa2ec4b1d8ccd4f23d80c196fdbb109` — 15 files, +2068 / −24 (verified via `git diff --name-only 9e13236..HEAD`). **No `.env`/secret files; no existing migration modified** (only the new one added). Bounded to Phase 7.

## 5. Verification Methodology

| Method | Executed |
|---|---|
| Static code review of the actual implementation | Yes |
| **Live PostgreSQL** (disposable e2e DB `127.0.0.1:55326`, PG 17.6) — schema, RLS, trigger behaviour | Yes |
| Migration applied **inside a transaction then ROLLBACK** (no persistent change) | Yes |
| **Independent execution of the real package-hash code path** (stubbed fetch) | Yes |
| Backend unit suite re-run | Yes |
| Frontend Jest (CRA) + production build | Yes |
| Route enumeration from the app router | Yes |

Environment note: the disposable e2e DB contains **no representative business dataset**, so live multi-document/multi-actor end-to-end scenarios could not be executed without creating data (out of scope). Those items are marked **NOT VERIFIED**.

---

## 6. Complete Auditability Matrix

Legend: **YES** verified in code/DB · **PARTIAL** partially supported · **NO** absent · **N/V** not verified (environment) · **P7** Phase 7 addition.

| Stage | Event | Actor | Actor type | Scope | Human/System | Outcome | Immutable | Queryable | Visible to authorised | Exportable | Production-populated |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Authentication | login/logout/session | **NO** | NO | – | – | – | – | – | – | – | – |
| Authorization | denied access | **NO** | NO | – | – | – | – | – | – | – | – |
| Authorization | role/membership change | YES | YES (P7) | YES | YES | **PARTIAL** (endpoint-dependent) | YES | YES | staff | – | N/V |
| Organisation/entity | scope changes | PARTIAL | YES (P7) | YES | YES | PARTIAL | YES | YES | staff | – | N/V |
| Document | upload | YES | YES (P7) | org | YES | YES | YES | YES (P7 activity) | owner/admin, consultant, staff | YES (P7 package) | N/V |
| Extraction | AI/system | YES | YES (P7 `origin=system`) | batch/entity | YES | YES | YES | YES | scoped | – | N/V |
| Extraction | human/PE | YES | YES (P7) | item | YES | YES | YES | YES | scoped | – | N/V |
| Mapping | applied/changed | YES | YES (P7) | item | YES | YES | YES | YES | scoped | – | N/V |
| Validation | validated/blocked | YES | YES (P7) | item | YES | YES | YES | YES | scoped | – | N/V |
| Calculation | completed | YES | YES (P7) | org (snapshot) | YES | YES | **YES (append-only + hash)** | YES | owner/admin, consultant, staff | YES (P7 package) | N/V |
| Evidence | inspected/created | YES | YES (P7) | org | YES | YES | YES | YES | scoped | – | N/V |
| Review | submitted/approved/rejected | YES | YES (P7) | item | YES | YES | YES | YES | scoped | – | N/V |
| QC | approved/rejected (CT + PE) | YES | YES (P7) | item | YES | YES | YES | YES | scoped | – | N/V |
| Customer Approval | approved (owner/admin) | YES | YES (P7) | item | YES | YES | YES | YES | staff/consultant | – | N/V |
| Report | generated/versioned/failed | YES | YES (P7 activity) | org | YES | YES (failure text) | YES (report_versions) | YES (P7 activity) | owner/admin | YES (P7 package) | N/V |
| Export | download | **PARTIAL** | PARTIAL | org | YES | – | YES | – | – | – | N/V |

**Actor / timestamp / resource-id / workflow-context / provenance / before-after** are carried by the canonical `audit_trail` (metadata + `changes`), verified in code (`data/audit.py`) and confirmed live (`audit_trail` schema on 55326). **before/after payloads are deliberately excluded from the customer/ops audit API responses** (`v3_reporting.py` returns only changed-field *names*; org activity `detail` = `metadata`).

**Decisive gap:** **Authentication and access-denied events are NOT captured** (see §7, §8) — consistent with the implementation report's residuals; **not** fabricated.

---

## 7. Authentication / Session Findings

* **No centralised all-actor session/authentication auditing.** Grep of `backend/api/**` and `backend/services/**` for `action="session|login|logout` → **NONE**. `public.login_history` exists but references `staff_profiles(id)` (`staff_id NOT NULL`) — a staff-only legacy table, not an all-actor session ledger.
* Supabase Auth performs authentication; the backend `get_current_user` resolves identity per request but does not write session events.
* **Classification:** Residual / **P2**. Not required by the approved Phase 7 objective (auditability of *system, data, calculation and workflow* activity); the implementation report documented it, and Phase 7 did not invent a session table or a forced timeout.
* Session duration **cannot** be reconstructed from CarbonTally records today — it is **absent**, not verified-as-present.

## 8. Security Findings

* **Access-denied events are not audited.** Authorization failures raise HTTP responses; no `audit_trail` write occurs. Cross-tenant, PE-foreign-entity, unauthorised-consultant and member-denied requests leave **no audit event**.
* **Sensitive audit access is NOT itself audited.** `grep 'audit.record'` in `v3_reporting.py` / `v3_exports.py` → **NONE**. Reading the audit trail / activity / readiness or downloading a package does **not** create an audit event. **Finding P2** (material for "who looked at the evidence" questions).
* **Audit-failure semantics are inconsistent:** most callers `await repos.audit.record(...)` **un-wrapped** (`admin_aliases.py:170`, `v3_operations.py:387/421/1361/1980`) → a write failure fails the request (fail-closed; no silent gap, but tight coupling). By contrast `audit_helpers.record_item_extraction_edit` deliberately swallows-and-logs the failure ("audit must never break the human edit") → a **potential silent audit gap** for that path (logged server-side only). **Finding P2.**
* No P0 security defect found: no RLS weakening, no authorization bypass in the reviewed code, no secret leakage.

## 9. RLS Findings (live, PostgreSQL 55326)

| Check | Result |
|---|---|
| `public.audit_trail` exists; RLS enabled | **Confirmed** (`relrowsecurity = true`) |
| Authenticated policies on `audit_trail` | **0** (deny-by-default) |
| `SET ROLE authenticated; SELECT` | **Denied** — `permission denied for table audit_trail` (no table grant) |
| Role attributes | `anon`/`authenticated`: `bypassrls=false`, `super=false`; `service_role`: `bypassrls=true`, `super=false`; `postgres`: table owner |
| Table owner | `postgres` |

**Interpretation:** the ledger is deny-by-default for `authenticated`/`anon`. The backend uses the **service role** and enforces authorization at the application layer (verified in §16). This matches the documented architecture.

## 10. GDPR / UK GDPR / Irish — Technical-Control Findings

**Technical support (implemented)**: material action/change/admin activity logging **YES** (canonical `audit_trail` + taxonomy); processing provenance **YES** (`calculation_snapshots`, evidence chain, factor provenance, package); data minimisation for credentials **YES** (grep of `data/audit.py`/`domain/audit.py` for `token|password|secret|api_key` → none); tenant isolation/least privilege **YES** (SQL `$1`-scoped unions + server guards).

**Technical gaps**: no session/auth audit; no access-denied audit; no audit-of-audit (§7, §8). Erasure/rectification of audit records is intentionally restricted by append-only semantics — a **retention policy** question, not a defect (pre-existing D-P2-04 deferred destructive retention).

**Organisation/legal dependencies**: this is a **technical control** review only. It does **not** establish GDPR/UK GDPR/Irish legal compliance, lawful basis, transfer mechanisms or retention periods. Those require legal review. **No compliance claim is made.**

## 11. Manual Extraction Findings

From schema + code (pre-existing substrate; Phase 7 surfaces it): source document → `organization_files`/`manual_extraction_items` (`extracted_by`, per item) → correction via `audit_helpers.record_item_extraction_edit` (`corrected_machine_output`, `previous_extracted_by`, `status_from/to`) → validation/review (`pe_reviewed_by`) → QC (`pe_qc_by`, `qc_by`) → calculation (`calculation_snapshots.source_item_id`) → report. The **original vs human-correction distinction is preserved explicitly**. Per-item (document-level) attribution is schema-supported and surfaced in the entity activity stream. **Live reconstruction on real data: NOT VERIFIED.**

## 12. Automatic Extraction Findings

Machine vs human provenance recorded: `MACHINE_EXTRACTOR` zero-UUID marker, `_record_human_gate`, and Phase 7 `origin`/`actor_type` (`classify_origin` treats `system`/`automatic_pipeline`/zero-UUID as system; unit tests pass). `document_processing_queue` carries per-stage timestamps, `reprocess_count`, `pipeline_version`, `error_log`, `calculation_snapshot_id`; `algorithm_version` on snapshots. Per-run model metadata is **PARTIAL** (documented). **Live: NOT VERIFIED.**

## 13. Batch Traceability Findings

The schema supports **document/item-level** attribution distinct from batch (`manual_extraction_items.extracted_by` per item + `calculation_snapshots.source_item_id`), and the Phase 7 entity stream emits item-level events scoped to the entity — so batch-level provenance does **not** structurally replace document-level provenance. Finer-grained item audit events come from `audit_helpers`. **The mandatory live multi-document/multi-operator scenario was NOT executed** (no representative dataset; constructing it is out of scope). **NOT VERIFIED (live)** — verification-coverage residual, not a defect.

## 14. Report → Source Evidence Findings

* Chain available: `report_generation_queue.generated_content` / `report_versions.content` → `emissions_logs.snapshot_id` → `calculation_snapshots` (`factor_id`, `factor_source`, `factor_set`, `import_batch_id`, `reporting_year`, `methodology`, `algorithm_version`, `content_hash`, `source_item_id`, `source_file`, `source_page`) → extraction item → source document. Verified by code (`data/exports.py` lineage join; `v3_emissions.py` `/{log_id}/evidence`; Phase 7 package includes snapshots + factor join).
* `report_versions` has **no direct snapshot/lineage column** — lineage runs via report content → emissions logs → snapshots. **PARTIAL / pre-existing.**
* **Live end-to-end on a real reported value: NOT VERIFIED** (no representative dataset).

## 15. Source → Report Reverse Lookup Findings

* Direction supported: source item → `calculation_snapshots.source_item_id` → `emissions_logs` → report content. The evidence endpoint resolves an emission back to source; the package includes `source_item_id`/`source_file`/`source_page` per snapshot.
* There is **no dedicated "which reports contain this source item" endpoint**; derivable but not surfaced. **PARTIAL.** **Live: NOT VERIFIED.**

## 16. Source Location (PDF/Page) Findings

* `calculation_snapshots.source_page` is persisted and surfaced in the package and evidence; `source_file` (name) too.
* **Bounding box / row coordinates / raw source text are NOT persisted** → navigation to an exact visual row is **not supported**; `source_page` gives page-level precision only. Scanned-PDF OCR is page-level. **PARTIAL** — honest limitation, not overclaimed.

## 17. Historical Calculation Integrity Findings

* `public.calculation_snapshots` is append-only by design with `content_hash` (SHA-256) and `factor_id ON DELETE RESTRICT`; recalculation creates a **new** snapshot — it does not rewrite the old. Verified by code + schema (table present live on 55326).
* `emissions_logs.snapshot_id` links each emission to its snapshot → original vs corrected results separable.
* **Live modify/recalculate scenario NOT executed** (would create data). **PARTIAL / NOT VERIFIED (live)** — structurally sound, behaviourally unexercised here.

## 18. API Findings

All Phase 7 endpoints **mounted** in `backend/api/router.py` (`v3_exports_router` line 203, `v3_reporting_router` line 221); enumerated live from the app router:

| Endpoint | Auth | Scope | Filters | Pagination |
|---|---|---|---|---|
| `GET /api/v3/ops/reporting/audit` | `require_staff` + `can_manage_staff` + `require_internal_staff` | internal | action/entity_type/entity_id/actor/category/origin/outcome/organization_id/since/until/q/sort/order | limit≤500/offset + honest `total` |
| `GET /api/v3/reporting/audit-activity` | `get_current_user` + `ensure_org_audit_access` | org (owner/admin, consultant grant, staff) | category/origin/outcome/start/end | limit/offset |
| `GET /api/v3/reporting/audit-readiness` | same | org | – | – |
| `GET /api/v3/reporting/consultant-client/{id}/audit-activity` | `ensure_consultant_org_access` | active grant | category/origin/outcome | limit/offset |
| `GET /api/v3/ops/entities/{id}/audit-activity` | `require_staff` + `require_entity_scope` + active entity | own entity | – | limit/offset |
| `GET /api/v3/exports/audit-package.json` | `ensure_org_audit_access` | org | reporting_year/limit | limit |

* Invalid taxonomy/timestamp → **422**; cross-tenant/role violations → **403**; anonymous → **401** (passing unit tests, suite EXIT=0). Response excludes before/after payloads. Empty states handled.

## 19. Frontend Findings

* **Jest (CRA `react-scripts test`)** — `audit-console-tab`: **PASS 5/5** (EXIT=0). (An earlier `npx jest` run failed to parse JSX — an **invocation** error, not a code defect.)
* **Production build** (`CI=false DISABLE_ESLINT_PLUGIN=true react-scripts build`): **Compiled successfully** (EXIT=0).
* The default `CI=true` build **fails at pre-existing eslint warnings in `src/App.js`** (legacy `no-unused-vars`/`react-hooks`) — **pre-existing, not Phase 7**.
* Phase 7 file lint: `AuditConsoleTab.jsx` reports `ErrorState` unused + `setRetryCount` unused — **pre-existing** (same pattern in `IssuesTriageTab.jsx`); the Phase 7 diff did not add them.
* The customer "Audit & evidence" tab renders only when `isAdmin` (`AdminPage.jsx`); the backend independently enforces owner/admin. **Owner/admin restriction verified in code; live UI walkthrough NOT VERIFIED.**

## 20. Evidence-Package Hash Verification (independent)

Executed the **real** `ReportingRepository.audit_package` code path with stubbed fetches, then independently recomputed SHA-256 over the exact canonical payload (content minus `counts`, `package_hash=null`, `json.dumps(..., sort_keys=True, default=str)`):

```
package_hash        = 3a1e28713de9a9f9bd284d55515d5f4b32f971dca2ff10b9f88a5b9b91818516
recomputed_hash     = 3a1e28713de9a9f9bd284d55515d5f4b32f971dca2ff10b9f88a5b9b91818516
HASH_MATCH          = True
not_assurance       = True
document_type       = carbontally_audit_evidence_package
has_notice          = True
TAMPER_CHANGES_HASH = True
```

**Result: PASS** — reproducible and tamper-evident. Note: `counts` is attached **after** hashing and is **not** covered (documented in `integrity.covered`); `generated_at` **is** covered → per-package hash. **Not a defect.**

## 21. Dashboard / RBAC Findings

* Customer audit capability: **owner/admin only** (`ensure_org_audit_access`), via the org admin "Audit & evidence" tab. Verified in code + tests.
* Consultant: client-scoped activity only via **active** grant. Verified in code + existing consultant tests.
* PE: entity-scoped activity only (`require_entity_scope` + active entity); PE staff **denied** org audit (403; test passes).
* Internal staff: ops audit console (staff-admin) + oversight access to org audit — intended/documented.
* **External Auditor: NO unrestricted role created** — grep found no auditor role/table/policy (comments only). Residual confirmed intentional.

## 22. Regression Tests

| Run | Command | Result |
|---|---|---|
| Phase 7 + reporting + audit-logger | `pytest tests/unit/domain/test_audit_p7.py tests/unit/api/test_p7_auditability.py tests/unit/api/test_reporting.py tests/unit/infra/test_audit_logger.py -q` | **EXIT=0** (111 tests) |
| Broad unit suite | `pytest tests/unit/{api,domain,infra,engines,services} -q` | **EXIT=0 at 100%** (~1,674 tests, 0 failures) |
| Frontend Jest | `react-scripts test audit-console-tab` | **PASS 5/5** |
| Frontend build | `react-scripts build` (eslint off) | **Compiled successfully** |

No test was weakened; no failures attributable to Phase 7. The `CI=true` build failure is **pre-existing** App.js lint.

## 23. Deployment Findings

* `backend/main.py` (legacy monolith, the deployed surface) imports the V3 router and, at **line 260–261**, `if V3_API_AVAILABLE: app.include_router(api_router)` → the Phase 7 reporting + export routes **are reachable** in the legacy deployment. `main_v2.py` serves the pure V3 app.
* **Caveat:** reachability is conditional on the V3 import succeeding (a defensive `except` sets `api_router=None`); if the V3 layer fails to import at runtime, the routes are absent. Deployment-time import success **NOT VERIFIED** in a running production process.
* The migration is **additive** and **NOT applied** to any DB (each environment verified: trigger/fn/indexes absent).

## 24. Audit Immutability Findings (live)

Migration applied **inside a transaction, then ROLLBACK** on the disposable e2e DB (55326) — no persistent change (post-rollback: trigger absent, function absent, 0 P7 indexes).

| Check | Live result |
|---|---|
| `p7_audit_trail_immutable` trigger created | **Yes** |
| Function `p7_audit_trail_immutable()` created | **Yes** |
| `INSERT` into `audit_trail` | **Allowed** (`insert_rows` 3 → 4) |
| `UPDATE audit_trail` | **BLOCKED** (`raise_exception`) |
| `DELETE FROM audit_trail` | **BLOCKED** (`raise_exception`) |
| 5 investigation indexes created | **Yes** (`idx_audit_trail_{performed_at,action_type,table_record,metadata_gin,org}`) |
| Rollback left no trace | **Yes (NO_TRIGGER / NO_FN / 0 indexes)** |

**Immutability limitation (real, documented):** the trigger is a normal (non-`ENABLE ALWAYS`) trigger. A **privileged path can bypass it** — demonstrated live: `SET session_replication_role = replica; UPDATE public.audit_trail …` → `UPDATE 3` succeeded. The **table owner** (`postgres`) could also `ALTER TABLE … DISABLE TRIGGER`. `service_role` has `bypassrls=true` but `super=false`, so the **application** path **cannot** bypass triggers (bypassrls affects RLS only). **Verdict: append-only holds for all non-privileged roles; a DB superuser/owner retains a bypass. Hardening option (not implemented): `ALTER TABLE public.audit_trail ENABLE ALWAYS TRIGGER p7_audit_trail_immutable;`** — recommendation only (P3).

## 25. Residual / PO-Decision Findings

| Residual | In approved P7 objective? | Required for acceptance? | Necessary for auditability? | Separate product/legal decision? | Needs new architecture? | Classification |
|---|---|---|---|---|---|---|
| External auditor identity/firm/engagement | No | No | No | **Yes** | Yes (new trust model) | **Residual / PO decision** |
| All-actor session logging | No | No | No (workflow audit exists) | Yes (retention/privacy) | Yes (session table or Auth hook) | **Residual / PO decision** |
| Access-denied audit events | Partially | No | Enhances security auditability | Yes | No (could write to ledger) | **P2 residual** |
| Sensitive-audit-access self-audit | Partially | No | Yes (for "who saw the evidence") | Yes | No | **P2 residual** |
| Evidence lock / e-signature | No | No | No (`content_hash` + package hash give integrity) | **Yes (legal)** | Yes | **Residual / PO decision** |
| Numeric audit-readiness "score" | No (readiness indicator delivered) | No | No | **Yes** | No | **Residual / PO decision** |
| Report-version freeze | No | No | No | Yes | No | **Residual / PO decision** |
| Legacy `AUDITOR_EXCEL` revival | No — correctly not revived | No | No | No | No | **Correctly absent** |

Per the interpretation rule (§36), absence of these does **not** fail Phase 7.

## 26. Severity-Ranked Defects

**P0 — Critical:** none found.

**P1 — High:** none found within the approved Phase 7 scope.

**P2 — Medium**
* **F2-1 — Sensitive audit access is not itself audited.** No audit event is written when an authorised user reads the audit trail/activity/readiness or downloads an evidence package → cannot answer "who accessed / who exported the evidence". (`v3_reporting.py`, `v3_exports.py`.)
* **F2-2 — No access-denied / security-failure audit events.** Cross-tenant, PE-foreign, unauthorised-consultant and member-denied attempts leave no durable event.
* **F2-3 — No all-actor session/authentication audit.** Login/logout/expiry/revocation not recorded centrally; session duration not reconstructable.
* **F2-4 — Inconsistent audit-failure semantics.** The best-effort path (`audit_helpers`) can leave a server-logged-only gap where a business action succeeds without an audit record; other callers fail-closed.

**P3 — Low / hardening**
* **F3-1 — Immutability trigger bypassable by a DB superuser/owner** (`session_replication_role=replica` demonstrated; not `ENABLE ALWAYS`). The application role cannot bypass.
* **F3-2 — Category/origin SQL filters exclude pre-Phase-7 rows** (no stored taxonomy; categorised on read only).
* **F3-3 — `counts` added after hashing** is not covered by the package hash (documented; not a defect).
* **F3-4 — Report-version lineage has no dedicated snapshot column** (derived via report content → emissions → snapshots). *Pre-existing.*
* **F3-5 — Production route reachability depends on V3 import success** in `main.py` (defensive fallback).
* **Pre-existing (not Phase 7):** `src/App.js` lint failures under `CI=true`; unused `ErrorState`/`setRetryCount` in `AuditConsoleTab.jsx`.

## 27. Remediation Recommendations (queue — NOT performed)

| Finding | Severity | Required remediation | Suggested implementation prompt |
|---|---|---|---|
| F2-1 | P2 | Write an `audit_trail` event on sensitive audit reads/exports (actor, org, resource, outcome) | "Phase 7 remediation: self-audit sensitive audit/evidence access" |
| F2-2 | P2 | Emit a security audit event on authorization denial (bounded categories) | "Phase 7 remediation: access-denied audit events" |
| F2-3 | P2 / PO | Decide + implement all-actor session logging (Auth hook or session table) | "PO decision + Phase 7.x: session/authentication audit" |
| F2-4 | P2 | Standardise audit-failure semantics (fail-closed vs outbox queue) and surface gaps | "Phase 7 remediation: audit-write failure semantics" |
| F3-1 | P3 | `ALTER TABLE public.audit_trail ENABLE ALWAYS TRIGGER p7_audit_trail_immutable;` | "Phase 7 hardening: ALWAYS trigger + least-privilege DB roles" |
| F3-2 | P3 | Derive/backfill legacy-row categories at read time, or accept the limitation | "Phase 7 hardening: legacy-row categorisation" |
| F3-5 | P3 | Verify V3 import + Phase 7 route presence in the deployed process | "Deployment verification: V3 route reachability" |

## 28. Final Acceptance Matrix

| # | Criterion | PASS / PARTIAL / FAIL / NOT VERIFIED | Evidence | Finding |
|---|---|---|---|---|
| 1 | Complete auditability | **PARTIAL** | canonical ledger + taxonomy + scoped timelines (code/tests/live schema) | F2-2, F2-3 |
| 2 | Accountability (human/system actor) | **PASS** | `actor`/`actor_type`/`origin`; `classify_origin` tests; `_record_human_gate` | – |
| 3 | Provenance | **PASS** | `calculation_snapshots` + factor provenance + package | – |
| 4 | Evidence-to-result traceability | **PASS (structural)** | evidence endpoint; package snapshots+factor join | live N/V |
| 5 | Source-to-report reverse traceability | **PARTIAL** | `source_item_id` lineage; no dedicated report lookup | live N/V |
| 6 | Batch/document attribution | **PARTIAL** | item-level `extracted_by` + `source_item_id` | live scenario N/V |
| 7 | Historical calculation integrity | **PASS (structural)** | append-only snapshots + `content_hash` + FK RESTRICT | live scenario N/V |
| 8 | Audit integrity (immutability) | **PASS (non-privileged)** | live trigger: UPDATE/DELETE blocked, INSERT ok | F3-1 |
| 9 | Authorization | **PASS** | `ensure_org_audit_access` + role tests (allow/deny) | – |
| 10 | RLS isolation | **PASS** | live: RLS enabled, 0 auth policies, authenticated denied | – |
| 11 | Investigation | **PASS** | 6 endpoints; taxonomy + filters; honest totals | – |
| 12 | Evidence package | **PASS** | independent hash match + tamper detection + notice | F3-3 (minor) |
| 13 | Audit readiness | **PASS** | "AUDIT EVIDENCE READINESS", `not_assurance:true`, tests | – |
| 14 | Dashboard/workspace integration | **PASS (code)** | owner/admin tab; scoped endpoints; no universal dashboard | live UI N/V |
| 15 | Security auditability | **PARTIAL** | access-denied + audit-access not logged | F2-1, F2-2 |
| 16 | Privacy / GDPR technical controls | **PASS (technical)** | no secrets in audit; tenant isolation; minimisation | legal review required |
| 17 | Separation of duties | **PASS** | distinct `pe_review:*`/`pe_qc:*`/`ct_qc:*`/`customer_review`/`qc_*` | – |
| 18 | Public positioning | **PASS** | `not_assurance:true` + notice; no auditor role; ToS §11.1 preserved | – |
| 19 | Regression safety | **PASS** | backend EXIT=0 (~1674); jest 5/5; build OK | pre-existing lint only |
| 20 | Deployment readiness | **PARTIAL** | routes mounted in `main.py`; migration add-only, unapplied | F3-5 N/V |

## 29. Final Verdict

> **PHASE 7 INDEPENDENTLY VERIFIED WITH ACCEPTED RESIDUALS — READY FOR CLOSURE**

Rationale: the approved Phase 7 objective and the mandatory acceptance criteria are **independently evidenced** (source code, live PostgreSQL, real-code hash execution, re-run test suites, route enumeration) — auditability, accountability, provenance, audit integrity (non-privileged roles), authorization, RLS isolation, investigation, evidence package and positioning all hold. **No P0/P1 defect** was found. Remaining items are **P2 residuals** (security-audit completeness), **P3 hardening**, and **environment-limited NOT-VERIFIED checks** (live batch/document end-to-end, report↔source live lineage, historical-recalc live, deployed-process import).

**Boundaries (per §38):** this is **technical auditability** verification. It does **not** establish **legal/regulatory compliance** and is **not** independent GHG assurance. Closure and remediation remain **Product Owner** decisions — this task does not self-authorise closure.

**Not performed:** implementation changes, migration application to any persistent DB, production mutation. The only repository addition is this report.

*End of verification report.*
