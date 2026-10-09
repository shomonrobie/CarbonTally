# CarbonTally Project Handoff — Current Release / Investor Readiness State

**Handoff ID:** `CT-HANDOFF-20260928-02`  
**Prepared:** 2026-09-28  
**Canonical repository:** `/home/shomonrobie/ct_93d5cdd`  
**Canonical branch:** `p8-release-reconciled`  
**Current reported HEAD:** `dc3d78dc8021bd65978754cf131c38045ff8013d`  
**Production deployment:** NOT AUTHORIZED / NOT PERFORMED

> **Truth standard:** `DOCUMENTED ≠ CODE EXISTS ≠ ROUTE WIRED ≠ AVAILABLE ≠ PERSISTED ≠ E2E VERIFIED ≠ INDEPENDENTLY VERIFIED ≠ PRODUCTION READY`.

---

# 1. Goal

Bring CarbonTally through the final controlled release path:

1. Finish and independently verify `CT-FINAL-01`.
2. Run `CT-FINAL-02-20260928-LOCAL-PRODUCTION-REHEARSAL`.
3. Run `CT-FINAL-03-20260928-PRODUCTION-CUTOVER` only after FINAL-02 passes.

The immediate state is **`CT-FINAL-01-PO-SCOPE-IMPLEMENTED`**, not accepted.

The final acceptance must include:

```text
Org A user → Org A data = ALLOW
Org B user → Org A data = DENY / 403
Org B user → Org B data = ALLOW
```

This cross-tenant test must remain a permanent release regression test.

Explicitly not yet authorized: production deployment, production migration, destructive demo reset, unrelated reconciliation/research, or speculative product expansion.

---

# 2. Current State

## 2.1 Repository — FACT

- Repo: `/home/shomonrobie/ct_93d5cdd`
- Branch: `p8-release-reconciled`
- HEAD: `dc3d78dc8021bd65978754cf131c38045ff8013d`
- Latest CT-FINAL-01 PO-scope implementation left HEAD unchanged.
- Nothing committed, pushed, or deployed.
- `git stash list` was empty at handoff.
- Latest implementation handoff reported **34 modified + 1 deleted + 76 untracked**.
- Zero-byte pre-existing files `8` and `=` were left untouched.

These counts must be re-measured at the start of the next session before new implementation.

## 2.2 Canonical schema — FACT

Independently rebuilt/verified:

- 92 migrations
- 149 tables
- 149 RLS-enabled tables
- 235 policies
- 182 foreign keys
- 569 indexes
- 37 functions
- 100 triggers
- 4,652 columns
- migration fingerprint: `36d5d85b93e6a6d0caba68037445fc43df4a87203b5931513bf07494e2437944`
- inventory fingerprint: `5291cd9197bb7f0f84a99dec22c1b365633f4cd206cac5b787668cb4ee9c1407`

## 2.3 Factor library — FACT

- Protected factor library: **7,049 factors**.
- Canonical table: `emission_factors`.
- Retired table: `defra_conversion_factors`.
- The retired table must not be recreated merely to support stale code.
- CT-IMPLEMENT-04 established the authorized factor-read repointing and confinement guard.

## 2.4 CT-FINAL-01 security/runtime — FACT

Implemented and locally tested:

- F-05-R1 cross-tenant organization-path authorization;
- F-05-R2.1 PDF generation 500;
- F-05-R2.2 organization-activity 500;
- F-05-R2.3 emissions-data response-model 500;
- F-05-R3 cross-tenant 500 → 403;
- F-05-R4 NULL embedded relation;
- F-05-R7 guard scan-root widening.

The F-05-R1 fix is central and protects organization path parameters before service-role handler access.

## 2.5 Ratified PO scope — FACT

Implemented + locally tested:

- **F-04:** unresolved factor blocks writes with `FACTOR_UNRESOLVED_BLOCKED` / HTTP 409; fabricated `2.68` default removed.
- **PD-4:** legacy admin audit-log implementation retired/deleted; historical audit data not dropped; canonical audit remains.
- **Notifications:** centralized sender service; admin-only `GET/PUT /api/v3/settings/notification-sender`; initial/default sender `notifications@carbontally.co.uk`; application actor remains distinct from SMTP sender.
- **Uploads:** 10 MB/file, 50 files/batch, 500 MB aggregate; server-side enforcement.
- **Retention:** purpose-based; seven years may apply to justified carbon-accounting/business evidence; not claimed as a universal GDPR requirement.
- **Billing:** no live billing in investor/demo release.
- **Currency:** GBP + EUR; future USD extensibility retained.
- **SEO/PWA:** deferred.
- **Provenance:** required end-to-end.

## 2.6 Tests — FACT

Focused PO-scope tests:

- F-04: 20
- notification sender: 25
- upload limits: 16
- PD-4 retirement: 7
- settings: 5

**73 passed.**

Combined CT-FINAL-01 regression: **150 passed, 100%, exit 0**.

Earlier full unit suite: **3,840 run / 3,830 passed / 10 failed**; the 10 failures were A/B-proven pre-existing in that report.

The later PO-scope handoff reproduced three remaining SLA failures against baseline; they are documented as pre-existing and were not silently fixed.

## 2.7 Untested — FACT

CT-FINAL-01 has **not** been independently accepted.

Still requiring independent/runtime verification:

- real disposable PostgreSQL/Supabase runtime;
- real auth tokens;
- real PostgREST/RLS behavior;
- PD-3 browser/admin journey;
- notification configuration/runtime behavior;
- storage-bucket enforcement;
- complete investor workflow;
- backup/restore;
- rollback strategy;
- final frontend/backend compatibility;
- production cutover.

The new migration `supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql` has **not been applied to any real environment**. This does **not** mean the historical CarbonTally runtime/storage did not work; it is a new storage-policy tightening introduced by CT-FINAL-01 and should be exercised in a disposable environment.

## 2.8 Remaining — FACT

- `CT-VERIFY-06` not started.
- PD-3 UI not browser-tested.
- Three SLA test failures remain and are documented as pre-existing.
- Three retention domains are reported as `PO DECISION REQUIRED`; exact domains must be identified before assigning policy.
- Storage migration needs disposable-environment verification.
- Production has not been changed.

---

# 3. Active Files

## Current handoff

`carbontally_handoff.md`

Persistent project state and next-phase instructions.

## CT-FINAL-01

`CT-FINAL-01-20260928-REPORT.md`

Implementation evidence for F-05 remediation and original FINAL-01 state. Its earlier PO-gated wording is historical and superseded by the later ratified PO-scope implementation.

## CT-IMPLEMENT-04

`CT-IMPLEMENT-04-20260928-REPORT-FACTOR-READ-REPOINT.md`

Canonical `emission_factors` repoint and legacy-reference guard evidence.

`docs/architecture/CT-IMPLEMENT-04-20260928-INDEPENDENT-VERIFICATION-BRIEF.md`

Frozen independent-verification instructions; not itself a PASS claim.

## CT-RELEASE-04

`docs/architecture/CT-PO-CARBONTALLY-CT-RELEASE-04-REPORT-20260928.md`

Clean-checkout canonical rebuild evidence: 92 migrations, deterministic fingerprints, no production/demo mutation.

## CT-VERIFY-03

`docs/architecture/CT-PO-CARBONTALLY-CT-VERIFY-03-INDEPENDENT-REPORT-20260928.md`

Independent verification of the CT-IMPLEMENT-03/report scheduling-sharing work and canonical runtime/schema aspects.

## Schema evidence

`CT-PO-CARBONTALLY-CT-SCHEMA-01-REPORT-20260927.md`

Canonical schema inventory/reconciliation.

`CT-PO-CARBONTALLY-CT-SCHEMA-02-REPORT-20260927.md`

Schema extension and 92-migration implementation evidence.

`CT-PO-CARBONTALLY-CT-SCHEMA-03-REPORT-20260927.md`

Code/schema disposition and PO-decision evidence.

`CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION-20260927.md`

Clean canonical schema rebuild verification.

## CT-FINAL-01 implementation files

- `backend/utils/emissions.py` — F-04 blocking primitives.
- `backend/routes/drafts.py` — F-04 write blocking.
- `backend/routes/documents_main.py` — F-04 write blocking.
- `backend/routes/admin/extraction.py` — F-04 write blocking.
- `backend/routes/admin/audit_logs.py` — retired legacy audit implementation; deleted.
- `backend/services/email_sender.py` — centralized email sender.
- `backend/services/v3_email.py` — sender compatibility alias.
- `backend/data/settings.py` — sender configuration persistence.
- `backend/api/v3_settings.py` — admin notification sender API.
- `backend/utils/upload_limits.py` — upload policy.
- `backend/api/v3_documents.py` — upload enforcement.
- `backend/routes/organizations/files.py` — upload enforcement.
- `backend/routes/upload.py` — upload enforcement.
- `supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql` — storage limit migration; not yet applied.
- `backend/tests/unit/api/test_f04_factor_write_path_blocking.py` — 20 tests.
- `backend/tests/unit/api/test_ct_final_01_notification_sender.py` — 25 tests.
- `backend/tests/unit/api/test_ct_final_01_upload_limits.py` — 16 tests.
- `backend/tests/unit/api/test_pd4_legacy_audit_retirement.py` — 7 tests.
- `backend/tests/unit/api/test_v3_settings.py` — 5 tests.

---

# 4. Changes Made

## Canonical schema/rebuild

Completed and independently verified: 92-migration canonical tree, clean rebuilds, fingerprints, RLS/policy/FK/index/function/trigger inventory, and D32 provenance/operator semantics.

## Factor repoint

Completed and independently verified: authorized non-PO-gated retired factor reads repointed to canonical factor architecture; guard widened; no production writes.

## CT-FINAL-01 security

Completed and locally tested: central exact-tenant path enforcement, fail-closed authorization, cross-tenant 403, runtime 500 corrections, NULL relation handling, guard-scan widening.

## CT-FINAL-01 ratified PO scope

Completed and locally tested: F-04, PD-4, notifications, upload limits, retention documentation, associated tests and report addendum.

## Safety

No production deployment, migration, push, commit, investor/demo reset, production data mutation, or environment-secret modification occurred during this final sequence.

---

# 5. Facts vs Guesses

## Facts

- Canonical repo: `/home/shomonrobie/ct_93d5cdd`.
- Branch: `p8-release-reconciled`.
- Current reported HEAD: `dc3d78dc8021bd65978754cf131c38045ff8013d`.
- CT-FINAL-01 PO scope is implemented and locally tested.
- 73 focused PO-scope tests passed.
- 150 combined CT-FINAL-01 regression tests passed.
- Canonical schema is 92 migrations.
- Factor library is 7,049 factors.
- Canonical factor table is `emission_factors`.
- CT-VERIFY-06 has not started.
- Production has not been deployed.

## Not yet verified / must not be guessed

- exact Git state after this handoff is generated;
- every changed API against real PostgREST/Supabase;
- PD-3 browser workflow;
- storage migration behavior on provisioned Storage;
- whether an existing live bucket already satisfies the new 10 MB ceiling;
- final disposition of the three SLA failures;
- exact policy values for the three remaining retention domains;
- final investor/demo readiness;
- production readiness.

---

# 6. Next Step — Ordered

## 1. CT-VERIFY-06 — immediate next action

`CT-VERIFY-06-20260928-INDEPENDENT-FINAL-VERIFICATION`

Independent verification, not another implementation pass.

Use a disposable environment and verify:

1. two real tenants;
2. real authentication/tokens;
3. permanent F-05 cross-tenant regression;
4. F-04 factor blocking;
5. PD-3 admin factor management;
6. PD-4 canonical audit path;
7. PD-5 manual factor lookup;
8. notification sender authorization;
9. 10 MB / 50 file / 500 MB enforcement;
10. storage migration behavior;
11. RLS/PostgREST;
12. activity/emissions/PDF surfaces previously affected by 500s;
13. PD-3 browser journey;
14. pre-existing status of the three SLA failures;
15. no production/demo mutation.

## 2. CT-FINAL-02 — local + production-like rehearsal

Only after CT-FINAL-01 is independently accepted.

`CT-FINAL-02-20260928-LOCAL-PRODUCTION-REHEARSAL`

### Local PC

Establish and prove:

- Supabase
- PostgreSQL
- Auth
- Storage
- Realtime
- FastAPI
- Frontend
- 92+ migrations
- 7,049 factors
- controlled demo data
- customer/consultant/admin journeys
- ingestion/extraction/mapping/calculation
- reports/exports/sharing/schedules
- notifications
- admin factor management
- manual factor lookup
- upload limits
- retention behavior

### Production-like

Build from the exact same final release commit and verify:

- migrations/schema/RLS;
- tenant isolation/authentication;
- storage/factors;
- ingestion/extraction/mapping/calculation;
- reports/exports/sharing/schedules;
- notifications;
- admin/manual factor workflows;
- upload/retention behavior;
- investor demo journeys;
- backup/restore;
- rollback strategy;
- factor-library integrity;
- release fingerprint;
- frontend/backend compatibility.

**No production deployment yet.**

## 3. CT-FINAL-03 — actual live cutover

Only after FINAL-02 passes.

`CT-FINAL-03-20260928-PRODUCTION-CUTOVER`

```text
BACKUP
  ↓
FINAL DB MIGRATION
  ↓
VERIFY SCHEMA
  ↓
VERIFY FACTORS
  ↓
DEPLOY BACKEND
  ↓
DEPLOY FRONTEND
  ↓
LIVE SMOKE TEST
  ↓
INVESTOR JOURNEY
  ↓
FINAL ACCEPTANCE
```

Final live acceptance must include the permanent three-case cross-tenant test.

---

# 7. Required Documents for Next Phase

## Before / for CT-VERIFY-06

- `CT-VERIFY-06-20260928-INDEPENDENT-FINAL-VERIFICATION` report.
- Disposable-environment evidence.
- PD-3 browser evidence.
- Storage migration verification evidence.
- Final CT-FINAL-01 addendum/status update.

## For CT-FINAL-02

- `CT-FINAL-02-20260928-LOCAL-PRODUCTION-REHEARSAL` report.
- Local environment fingerprint.
- Production-like environment fingerprint.
- Migration/schema/RLS verification.
- Authentication/tenant-isolation verification.
- Factor-library integrity report.
- Ingestion/extraction/mapping/calculation verification.
- Reporting/export/sharing/scheduling verification.
- Notification verification.
- Admin/manual factor verification.
- Upload-limit verification.
- Retention-behavior verification.
- Backup/restore rehearsal.
- Rollback-strategy rehearsal.
- Frontend/backend compatibility evidence.
- Investor-demo journey rehearsal.
- Independent FINAL-02 acceptance report.

## For CT-FINAL-03

- Final release fingerprint.
- Production backup evidence.
- Final migration package/fingerprint.
- Production schema verification.
- Production factor integrity verification.
- Backend deployment evidence.
- Frontend deployment evidence.
- Live smoke-test report.
- Cross-tenant live authorization evidence.
- Investor journey live acceptance.
- Final production acceptance record.

---

# 8. Governance Rules

1. Do not start another broad reconciliation/research phase unless a concrete discrepancy requires it.
2. Do not modify production during CT-VERIFY-06.
3. Do not mutate the investor/demo environment during CT-VERIFY-06.
4. Use disposable databases for destructive integration tests.
5. Never edit an existing migration.
6. Never recreate `defra_conversion_factors` to hide stale references.
7. Preserve the 7,049-factor library.
8. Never fabricate unresolved extraction/factor data.
9. Manual review is a valid controlled outcome.
10. Separate application actor from SMTP sender identity.
11. Do not silently turn documentation into authorization.
12. Do not claim E2E or independent verification from unit tests.
13. Do not claim production readiness before FINAL-03.
14. Do not fix unrelated historical tests merely to obtain a green suite.
15. Keep the exact cross-tenant regression permanently.

---

# 9. Handoff Conclusion

**Current milestone:** `CT-FINAL-01-PO-SCOPE-IMPLEMENTED`  
**Acceptance:** NOT YET ACCEPTED  
**Immediate next action:** `CT-VERIFY-06-20260928-INDEPENDENT-FINAL-VERIFICATION`  
**Production:** NOT DEPLOYED / NOT AUTHORIZED AT THIS STAGE

```text
CT-VERIFY-06
    ↓
CT-FINAL-01 ACCEPTED
    ↓
CT-FINAL-02 LOCAL + PRODUCTION-LIKE REHEARSAL
    ↓
CT-FINAL-02 ACCEPTED
    ↓
CT-FINAL-03 ACTUAL LIVE CUTOVER
    ↓
LIVE ACCEPTANCE
```

The project has moved past the major canonical-schema and factor-repoint reconciliation problem. The remaining work is the controlled verification → rehearsal → cutover sequence.

**The next session should begin with CT-VERIFY-06.**
