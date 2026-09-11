# CT-P7-AUDITABILITY-IMPLEMENTATION-20260912-004

**Prompt Ref:** `CT-P7-AUDITABILITY-IMPLEMENTATION-20260912-004`
**Date:** 2026-09-12
**Authority:** Product Owner delegated implementation decision for Phase 7 (subject to independent verification + Phase 7 closure).
**Scope:** Phase 7 — Auditor / Assurance implemented as an **auditability + audit trail + evidence traceability + assurance-support** capability.
**Positioning preserved:** CarbonTally provides traceable calculations, evidence, provenance and audit-ready records that can support internal review and independent assurance. CarbonTally is **not** an independent auditor/verifier and provides **no** assurance opinion. Every Phase 7 payload carries `not_assurance: true`.

---

## 1. Implementation Summary

Phase 7 was implemented as a **reuse-first extension of the existing audit substrate** — no parallel audit architecture and no new audit table.

Delivered:

1. **Canonical audit taxonomy** (domain) — `category`, `origin` (human/system), `outcome`, `actor_type`, `organization_id`, derived deterministically from the existing `audit_trail` action/actor. Stored in the existing `metadata` JSONB (no schema change).
2. **Investigation filters** — the audit console endpoint gained `category` / `origin` / `outcome` / `entity_id` / `organization_id` / `since` / `until` filters over the same ledger.
3. **Customer auditability** — org-scoped `audit-activity` + `audit-readiness` endpoints (organisation **owner/admin** only; internal staff for oversight; PE staff denied; cross-tenant denied).
4. **Consultant auditability** — client-scoped `audit-activity` gated on an **active** client grant.
5. **PE auditability** — entity-scoped `audit-activity` (own entity only), framed as operational traceability, **not** employee surveillance.
6. **Audit/evidence package** — org-scoped `audit-package.json` with factor provenance, evidence references, workflow history, integrity hashes and a **package SHA-256**, carrying an explicit not-an-assurance-opinion notice.
7. **Audit Evidence Readiness** indicator — evidence-based, explicitly labelled, never "assured"/"verified"/"certified".
8. **Audit integrity** — append-only enforcement on `audit_trail` (DB trigger, all roles) + investigation indexes; the previous `ON CONFLICT ... DO UPDATE` upsert was removed.
9. **Frontend** — taxonomy filters + columns in the ops audit console; a customer "Audit & evidence" tab (owner/admin) with readiness, activity and package download.
10. **Tests + documentation.**

---

## 2. Repository State (before / after)

| Item | Before | After |
|---|---|---|
| Branch | `main` | `main` |
| HEAD | `9e13236149b8132d737258abc0aa7d69a974a85b` | **`436815721aa2ec4b1d8ccd4f23d80c196fdbb109`** (Phase 7 commit) |
| `origin/main` | `9e13236149b8132d737258abc0aa7d69a974a85b` | unchanged — **not pushed** |
| Worktree | dirty (pre-existing: 208 modified, 51 untracked) | pre-existing changes **preserved**; Phase 7 files committed (15 files, +2068/−24) |

**Commit:** `4368157` — `feat(phase7): auditor/assurance auditability, taxonomy, evidence package` (15 files changed, 2068 insertions, 24 deletions). **Not pushed** (push remains a separate, unauthorised step).

No destructive operation, no reset, no unrelated cleanup. Pre-existing modified/untracked work was not touched.

---

## 3. Files Changed

**Added**
- `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql`
- `backend/tests/unit/domain/test_audit_p7.py`
- `backend/tests/unit/api/test_p7_auditability.py`
- `frontend/src/v3/admin/AuditTab.jsx`
- `docs/cline/prompt-history/CT-P7-AUDITABILITY-IMPLEMENTATION-20260912-004.md` (this report)

**Modified**
- `backend/domain/audit.py` — taxonomy, `classify_action`, `classify_origin`, extended `AuditEntry` / `AuditQuery`.
- `backend/data/audit.py` — metadata taxonomy read/write, new filters, insert-only `save()`.
- `backend/data/reporting.py` — org/entity activity streams, readiness, evidence package (+ pure readiness helper).
- `backend/api/dependencies.py` — shared `ensure_org_audit_access` guard.
- `backend/api/v3_reporting.py` — audit filters + `audit-activity`, `audit-readiness`, consultant + entity activity endpoints.
- `backend/api/v3_exports.py` — `audit-package.json`.
- `backend/tests/unit/api/fakes.py` — `MemoryAudit` taxonomy filters; `MemoryReporting` Phase 7 fakes.
- `frontend/src/v3/ops/AuditConsoleTab.jsx` — filters + columns.
- `frontend/src/v3/api.js` — audit client functions.
- `frontend/src/v3/admin/AdminPage.jsx` — "Audit & evidence" tab.

---

## 4. Database Changes

**One additive migration:** `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql`

* **No new table.** No column added. No existing policy modified.
* `public.p7_audit_trail_immutable()` trigger function + `BEFORE UPDATE OR DELETE` trigger on `public.audit_trail` → the canonical audit ledger is **append-only for every role** (including the service role).
* Investigation indexes: `(performed_at DESC)`, `(action_type)`, `(table_name, record_id)`, GIN `(metadata jsonb_path_ops)`, and an org-scoped partial index on `(metadata->>'organization_id') WHERE metadata ? 'organization_id'`.
* Idempotent (`CREATE OR REPLACE FUNCTION`, `DROP TRIGGER IF EXISTS` + `CREATE`, `CREATE INDEX IF NOT EXISTS`).

**Canonical responsibility (documented, no fragmentation):**

| Structure | Responsibility |
|---|---|
| `public.audit_trail` | **Canonical append-only audit ledger** for material human/system actions (all surfaces). Phase 7 taxonomy lives in `metadata`. |
| `audit_logs` / `activity_logs` / `document_activity_log` | Legacy per-domain activity records; already immutable (DB-0001, `20260831020000`). Unchanged. |
| `calculation_snapshots` | Immutable forensic calculation records (+ `content_hash`). Unchanged. |
| `login_history` | Staff-only login record (`staff_id NOT NULL`). Not used for Phase 7 session events (see residuals). |

**Not done (correctly):** no production migration was applied (release controls govern that); no RLS changed or disabled.

---

## 5. API Changes

| Endpoint | Change |
|---|---|
| `GET /api/v3/ops/reporting/audit` | **Extended** with `category`, `origin`, `outcome`, `entity_id`, `organization_id`, `since`, `until`; response now includes `category`/`origin`/`outcome`/`actor_type`/`organization_id`. Guard unchanged (`can_manage_staff`, internal staff only). |
| `GET /api/v3/reporting/audit-activity` | **New** — org-scoped material-activity timeline. Guard: `ensure_org_audit_access`. |
| `GET /api/v3/reporting/audit-readiness` | **New** — AUDIT EVIDENCE READINESS (evidence-based; `not_assurance: true`). |
| `GET /api/v3/reporting/consultant-client/{client_id}/audit-activity` | **New** — consultant client-scoped activity (active grant required). |
| `GET /api/v3/ops/entities/{entity_id}/audit-activity` | **New** — entity-scoped activity (`require_entity_scope`, active entity). |
| `GET /api/v3/exports/audit-package.json` | **New** — scoped audit/evidence package (JSON) with package SHA-256 + notice. |

All new endpoints are server-authorised on every request; the URL/workspace is never the boundary.

---

## 6. Frontend Changes

* `frontend/src/v3/ops/AuditConsoleTab.jsx` — added **Category / Origin / Outcome** filters and **Category / Origin / Outcome** columns; the API client forwards the new filter params.
* `frontend/src/v3/admin/AuditTab.jsx` (**new**) — customer "Audit & evidence" tab: readiness indicator, recent activity (category-filterable), and evidence-package download. Carries the explicit "not an assurance opinion" notice.
* `frontend/src/v3/admin/AdminPage.jsx` — added the "Audit & evidence" tab, shown to **owner/admin** only (`adminOnly` + `isAdmin`). The backend independently enforces the same boundary.
* `frontend/src/v3/api.js` — `getAuditReadiness`, `getAuditActivity`, `getConsultantClientAuditActivity`, `auditPackageUrl`; `getOpsAudit` forwards the new filters.

No public-marketing wording was changed (see §16).

---

## 7. RLS / Security Changes

* **No RLS policy was changed, weakened or bypassed.**
* New reads reuse existing guards: `ensure_org_access`, `requester_org_admin`-equivalent role check, `ensure_consultant_org_access`, `require_entity_scope`, `require_internal_staff`.
* The shared guard `ensure_org_audit_access` (in `api/dependencies.py`) denies PE staff, requires org **owner/admin** for org members, allows authorised consultants, and allows internal staff for oversight.
* No secrets/tokens/passwords are written to audit records; the taxonomy stores identifiers/classification only.
* The `audit_trail` immutability trigger is defence-in-depth at the database for all roles.

---

## 8. Audit-Event Coverage Matrix

Legend: **Y** captured · **P** partial (some paths) · **N** not captured (residual) · **P7** added/strengthened by Phase 7.

| Lifecycle area | Event | Status | Where / notes |
|---|---|---|---|
| Authentication | login success / failure / logout / session events | **N (residual)** | Supabase Auth is client-side; `login_history` is staff-only and unused. Not centralised in `audit_trail` (see §13). |
| Authorization | access denied / security failure | **N (residual)** | Denials raise HTTP responses; no central denial audit event. |
| Authorization | role / membership / capability / scope changes | **P** | Captured where the creating endpoint records (staff, members, consultant, entity) — not exhaustive. |
| Documents | upload / ingestion | **Y** | `v3_documents` records audit on upload. |
| Documents | download / export | **P** | Export endpoints are audited in part; document download audit is not exhaustive. |
| Documents | human correction / status transition | **Y** | `v3_operations` / `v3_pe` / `audit_helpers.record_item_extraction_edit`. |
| Extraction / mapping / validation | AI + human actions | **Y** | `ops_*` / `pe_*` / `org_item_extraction` actions. |
| Calculation | requested / applied / verified | **Y** | `*_calculate:applied`, `verify`; `calculation_snapshots` immutable + `content_hash`. |
| Calculation | factor / version / provenance | **Y** | Snapshot carries `factor_id/source/set/import_batch_id/reporting_year/methodology/algorithm_version`. |
| Evidence | created / linked / inspected | **Y** | `evidence.access`, `evidence.reverse_lookup`; D33 chain endpoint. |
| Workflow | assignment / reassignment | **Y** | `batch:assigned`, work-assignment routes + audit. |
| Workflow | review / QC / approval / rejection / reopen | **Y** | `review:*`, `qc:*`, `pe_review:*`, `pe_qc:*`, customer-review actions. |
| Reporting | report generated / versioned / failed | **P** | `report_generation_queue` lifecycle is surfaced in the Phase 7 activity timeline; report-versions table records versions. |
| Administration | organisation / member / consultant / PE / staff / role changes | **P** | Captured where endpoints record (`organization.created`, `processing_entity:*`, roles). |
| Automated / system | worker / retry / automated transition | **Y** | `_record_human_gate` + automation provenance; **P7** now classifies `origin=system`. |
| Provenance | human-vs-machine ordering | **Y** | `MACHINE_EXTRACTOR`, `corrected_machine_output`; **P7** `origin`/`actor_type`. |

**P7 taxonomy** now classifies every recorded event with a canonical `category` + `origin` (+ `outcome`/`actor_type`/`organization_id` where supplied), so the ledger is investigable even where the *event itself* was already recorded.

---

## 9. Existing vs New Audit Capability

| Capability | Before Phase 7 | After Phase 7 |
|---|---|---|
| Canonical ledger | `audit_trail` (append-only by policy absence) | **+ DB-enforced append-only (trigger, all roles)** |
| Taxonomy | none (raw action/actor) | **category / origin / outcome / actor_type / organization_id** |
| Investigation | action / entity_type / actor / q / date | **+ category / origin / outcome / entity_id / organization_id / since / until** |
| Customer audit visibility | none | **org-scoped activity + readiness (owner/admin)** |
| Consultant audit visibility | per-client evidence only | **+ client-scoped activity (active grant)** |
| PE audit visibility | work surfaces only | **+ entity-scoped activity timeline** |
| Evidence package | CSV/JSON exports (per-row lineage) | **+ self-describing package with package hash + notice** |
| Readiness | per-result completeness only | **+ AUDIT EVIDENCE READINESS aggregate (evidence-based)** |
| Integrity indexes | none dedicated | **+ 5 investigation indexes** |
| Immutability of history | policy-based | **+ trigger-enforced** |

**Reuse (not duplicated):** `audit_trail`, `calculation_snapshots`, evidence chain, `ReportingRepository`, exports, report engine, `ensure_org_access` / `ensure_consultant_org_access` / `require_entity_scope`.

---

## 10. Tests Run

All backend tests run in memory over the shared fakes (`backend/tests/unit/api/conftest.py`); the database is never opened.

1. **New Phase 7 domain tests** — `tests/unit/domain/test_audit_p7.py` (taxonomy + `AuditQuery` validation + readiness helper).
2. **New Phase 7 API tests** — `tests/unit/api/test_p7_auditability.py` (authorization ALLOW/DENY + filters + shapes).
3. **Regression-focused** — `tests/unit/api/test_reporting.py`, `tests/unit/infra/test_audit_logger.py` (+ the two new files).
4. **Broad unit suite** — `tests/unit/api`, `tests/unit/domain`, `tests/unit/infra`, `tests/unit/engines`, `tests/unit/services`.

Commands:
```
python -m pytest tests/unit/domain/test_audit_p7.py tests/unit/api/test_p7_auditability.py -q
python -m pytest tests/unit/api/test_reporting.py tests/unit/infra/test_audit_logger.py \
                 tests/unit/domain/test_audit_p7.py tests/unit/api/test_p7_auditability.py -q
python -m pytest tests/unit/api tests/unit/domain tests/unit/infra tests/unit/engines tests/unit/services -q
```
Import smoke check: `python -c "import api.dependencies, api.v3_reporting, api.v3_exports, data.reporting, data.audit, domain.audit"` → **IMPORT-OK**.

## 11. Test Results

| Run | Result |
|---|---|
| New Phase 7 tests (domain + API) | **58 passed** |
| Targeted regression (reporting + audit logger + Phase 7) | **111 passed** (EXIT=0) |
| Broad unit suite (api/domain/infra/engines/services) | **EXIT=0** (~1,674 tests, 0 failures/errors) |
| Import smoke check | **IMPORT-OK** |

No existing test was weakened or modified to pass Phase 7 (only the in-memory fakes were *extended* with new, additive filters/methods).

> Frontend Jest tests were **not executed** in this environment (no npm/jest run performed). The existing `frontend/src/v3/__tests__/audit-console-tab.test.jsx` continues to exercise `getOpsAudit` with tolerant assertions and is expected to pass; this requires verification in a frontend-capable environment (§18).

## 12. Known Limitations

1. **Session/authentication events are not centralised** — Supabase Auth logs in client-side; `login_history` is staff-only and unused. Phase 7 did **not** invent a session-logging table or a forced session timeout (§13).
2. **Access-denied events are not audited** — denials are HTTP responses, not ledger events.
3. **Org scope for `audit_trail`** relies on `metadata.organization_id` being present. Events written **before** the taxonomy are categorised on read (derived) but are **excluded from a SQL category/origin filter** (honest: legacy rows have no stored taxonomy).
4. **Org activity timeline** is assembled from the org-tagged ledger plus authoritative org-scoped tables; it is a reconstruction, not a single event stream.
5. **`source_item_id` may be null** on historical snapshots — evidence completeness is then PARTIAL/UNAVAILABLE (reported honestly).
6. **Readiness is descriptive only** — it never asserts verification/assurance.
7. **Schema-dependent queries** — the activity streams and readiness read `calculation_snapshots.source_item_id/source_file/source_page` (added by a later migration); if those columns are absent in an environment, the Phase 7 read endpoints fail there. Production migration state remains governed by existing release controls.
8. Frontend tests not executed here (see note above).

## 13. Residual Gaps (explicitly NOT improvised)

These were assessed and **deliberately left as residuals** rather than inventing product decisions:

1. **External assurance / auditor identity + firm/engagement model + external access** — requires a new trust/RLS model and a Product Owner decision. **Not implemented.**
2. **Session logging** (login/logout/expiry/revocation, session duration) — needs either a new all-actor session table or a Supabase Auth hook; would alter the authentication model. **Not implemented** (documented).
3. **Access-denied audit events** — needs a decision on which denials are security-significant and where to write them. **Not implemented.**
4. **Evidence lock/freeze + legally meaningful e-signature/attestation** — a separate requirement; `content_hash` + the package hash provide integrity, not legal signature. **Not implemented.**
5. **Audit-readiness "score"** — a numeric score risks implying assurance; only an evidence-based readiness indicator was implemented. **PO decision required** for any score.
6. **Report-version freeze** — not added (report versions already exist; a freeze workflow is a product decision).
7. **`AUDITOR_EXCEL`** — legacy export **not revived** (left as-is in the legacy monolith).

---

## 14. Migration Requirements

* **One migration to apply:** `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql`.
* Additive + idempotent; safe to run once. Requires no data backfill and no column change.
* **Not applied by this task.** Production application remains governed by existing CarbonTally release controls and must not be applied silently.
* **Rollback:** `DROP TRIGGER p7_audit_trail_immutable ON public.audit_trail; DROP FUNCTION public.p7_audit_trail_immutable(); DROP INDEX ...` (all reversible; no data change).
* **Future retention/purge caveat:** any authorised destructive retention of audit records must deliberately disable the trigger first (documented in the migration header).

## 15. Production Deployment Requirements

1. **Apply the migration** through the approved release process (verify `audit_trail` exists and that INSERT/SELECT continue to work; confirm UPDATE/DELETE raise).
2. **Verify schema columns** used by the activity/readiness reads exist in the target environment (`calculation_snapshots.source_item_id/source_file/source_page`, `issues.*`, `organization_files.*`, `report_generation_queue.*`).
3. **Verify the deployed entry point** — the legacy `main.py` mounts the V3 router alongside; ensure the new `/api/v3/reporting/*` and `/api/v3/exports/*` routes are reachable in the deployed app.
4. **Frontend build** — ship the updated `api.js`, `AuditConsoleTab.jsx`, `AdminPage.jsx`, `AuditTab.jsx`.
5. **No new env vars, no billing/config change, no auth change.**
6. **Do not apply to production without authorisation** (release controls govern).

## 16. Public-Claim Review

* **No public/marketing wording was changed by this task.**
* Phase 7 UI wording is deliberately non-assurance: the customer tab states CarbonTally "provides traceable calculations, evidence, provenance and audit-ready records that can support internal review and independent assurance processes … This is not an assurance opinion, verification or certification."
* The readiness indicator is labelled **"AUDIT EVIDENCE READINESS"** and never "Verified"/"Assured"/"Certified".
* Existing approved positioning is preserved (`docs/legal/draft/CARBONTALLY_TERMS_OF_SERVICE_DRAFT.md` §11.1; archaeology; Blueprint). No claim of independent audit/verification is made anywhere in the Phase 7 code or UI.
* Any future public/legal wording change remains a PO/legal decision.

## 17. Phase 7 Acceptance Status

| Acceptance criterion | Status |
|---|---|
| Auditability — material workflow reconstructable from durable records | **Met** (org/entity activity timelines from authoritative tables + ledger) |
| Accountability — material actions identify the responsible actor | **Met** (`actor`, `actor_type`, `origin`; machine vs human) |
| Provenance — calculations traceable through evidence chain | **Met** (snapshots + factor provenance + package; existing D33 chain reused) |
| Integrity — history not casually modifiable | **Met** (append-only trigger for all roles + `content_hash`) |
| Authorization — audit data scoped to the actor/entity/capability model | **Met** (owner/admin, active consultant grant, entity scope, internal staff) |
| Security — no weakening of RLS/auth | **Met** (no RLS change; reuse of existing guards) |
| Investigation — authorised users can search/inspect | **Met** (taxonomy + filters in the console) |
| Evidence — a scoped evidence package can be produced | **Met** (`audit-package.json` with package hash + notice) |
| Separation of duties — approval / QC / assurance distinct | **Met** (no change; QC ≠ approval ≠ assurance) |
| Positioning — no independent-auditor claim | **Met** |
| Testing — relevant tests pass | **Met** (backend; frontend jest pending env) |

**Verdict: `PHASE 7 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`.** (This is an implementation statement, not an independent verification. Independent verification is not performed by this task.)

## 18. Items Requiring Independent Verification

1. **Authorization negative tests against a real database/RLS** — cross-tenant, consultant non-grant, PE foreign-entity, org-member denial, anonymous denial; confirm RLS + server guards both deny.
2. **Immutability at the database** — confirm `UPDATE`/`DELETE` on `audit_trail` raise for every role (including service role) after the migration; confirm `INSERT`/`SELECT` unaffected.
3. **Evidence-package integrity** — recompute the SHA-256 over the canonical payload and confirm it matches `integrity.package_hash`; confirm the notice/`not_assurance` fields are present.
4. **Readiness honesty** — confirm labels never read "assured"/"verified"/"certified" in any surface.
5. **Activity stream correctness** — confirm org A never sees org B events; consultant only active clients; PE only own entity.
6. **Frontend** — run `frontend/src/v3/__tests__/audit-console-tab.test.jsx` and build; manually verify the customer "Audit & evidence" tab is owner/admin-only.
7. **Route reachability in the deployed app** (legacy monolith vs `main_v2.py`).
8. **Residual gaps** (§13) confirmed as intentionally out of scope.

---

## Appendix — Git / Change Control

* No destructive reset; pre-existing worktree changes preserved.
* Changes bounded to Phase 7.
* Commit: recorded after tests + documentation (see final response). No push unless repository workflow permits and no unresolved safety issue remains.
* **Not applied to production.** No secrets added.

*End of report.*
