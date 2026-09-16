# CT-P8-B1-V1R-INDEPENDENT-RE-VERIFICATION-20260913-016

**Task ID:** `CT-P8-B1-V1R-INDEPENDENT-RE-VERIFICATION-20260913-016`
**Title:** Phase 8 Batch B1 — Independent Re-Verification After Bounded Correction
**Role:** independent verification engineer (verification-only: nothing was fixed, patched, committed or deployed)
**Environment:** local workstation · repo `/home/shomonrobie/carbon_tally` · HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c` · branch `main`
**Runtime:** **fresh** disposable clone `b1v1r_verify` (PostgreSQL 17.6, local dev cluster) + a second privileges-inclusive clone `b1v1r_priv` — **not production, not the dev/demo database**
**Final verdict:** `B1 V1 INDEPENDENT RE-VERIFICATION — PASS WITH NONBLOCKING FINDINGS`

> All material V1 findings (F1, F2, F3, F4, F5) are independently reproduced-as-closed at runtime; F6
> coverage exists, was inspected and was executed; F7 is correctly classified as a P3 out-of-scope
> observation and is not a material B1 security defect; PQ-1…PQ-8, tenant isolation, RLS, audit,
> immutability, migration/idempotency and regression all pass. Only P3 observations and verification
> limitations remain (§37/§38).

---

## 1. Task ID
`CT-P8-B1-V1R-INDEPENDENT-RE-VERIFICATION-20260913-016`.

## 2. Purpose
Determine independently whether the corrected B1 implementation now satisfies the authorised B1 contract and
PQ-1…PQ-8, and whether the material V1 findings are actually closed — **without** trusting the correction
report's claims.

## 3. Governing documents
Contract `CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md` (§9–§11, §22–§27); PO ratification
`CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md` (PQ-1…PQ-8); authorisation
`CT-P8-B1-PO-IMPLEMENTATION-AUTHORISATION-20260912-012.md`; implementation report
`CT-P8-B1-IMPLEMENTATION-20260912-013.md`; V1 report `CT-P8-B1-V1-INDEPENDENT-VERIFICATION-20260912-014.md`;
correction report `CT-P8-B1-CORRECTION-20260912-015.md`. Also inspected first-hand:
`backend/data/disclosure.py`, `backend/domain/disclosure.py`, both B1 migrations,
`backend/tests/integration/test_disclosure_b1_runtime.py`,
`backend/tests/unit/data/test_disclosure_sql_typing.py`, `backend/tests/integration/conftest.py`,
`backend/data/audit.py`, `backend/domain/audit.py`, `20260807070000_add_new_table_rls.sql`.

## 4. Previous V1 result
`B1 V1 INDEPENDENT VERIFICATION — FAIL` — F1/F2 (P1) non-executable write methods; F3/F4/F5 (P2); F6 (P3
static-only tests); F7 (P3 helper ACL). The schema/migration/seed/RLS/tenant/PQ surface already passed V1.

## 5. Correction report reviewed
`CT-P8-B1-CORRECTION-20260912-015.md` (`B1 CORRECTION COMPLETE — READY FOR V1 RE-VERIFICATION WITH
NONBLOCKING FINDINGS`) was read in full and treated as evidence, not authority. Its four material claims
(F1/F2 casts, F3 app-layer + DB index, F4 grants, F5 audit) were each re-derived from source and re-tested at
runtime in a *new* environment (§13–§17).

## 6. Repository baseline (captured before verification)

| Item | Value |
|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Branch | `main` |
| `git log -1 --oneline` | `19e4f01c feat: implement Phase 8 report lifecycle foundation` |
| Staged | 0 |
| Modified (tracked) | 208 (all pre-existing; **none** is a B1 file) |
| Untracked (porcelain entries) | 73 |
| Migrations | 57 (last three: `20260913000000_p8_report_lifecycle_status.sql`, `20260914000000_p8_b1_disclosure_model_foundation.sql`, `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql`) |
| Dev DB disclosure tables | 0 (B1 never applied there) |

Nothing was reset, checked out, cleaned, stashed, rebased, amended, restored, committed or pushed.

## 7. Verification environment
Local Supabase dev stack (`supabase_db_carbon_ledger`, PostgreSQL **17.6**, `127.0.0.1:54426`). Two
disposable databases were created for this task and both were **dropped** afterwards:
`b1v1r_verify` (faithful runtime) and `b1v1r_priv` (privileges-inclusive invariance baseline). Production and
the dev/demo database were never touched or contacted.

## 8. Fresh clone construction
`DROP DATABASE IF EXISTS … WITH (FORCE)` → `CREATE DATABASE b1v1r_verify` → schema-only
`pg_dump --schema-only --no-owner --no-privileges` of the dev database restored (1 error, the benign
`log_min_messages` SET) → **116 public base tables**, all dependency tables, `auth.uid()`, and the
`anon`/`authenticated`/`service_role` roles present → the dev database's `public` default ACL mirrored
(`anon/authenticated/service_role = Dxtm` for role `postgres`) so privilege assertions are meaningful.
A second clone `b1v1r_priv` was restored **with privileges** (`--schema-only --no-owner`; 464 existing-table
grant rows, 174 policies) to serve as an independent invariance baseline; its 73 restore errors are benign
environment noise (63 `permission denied to change default privileges`, 5 grant-option notices, 3
realtime/admin-function, 1 log-parameter) and `CLONE_MATCHES_DEV_EXISTING_GRANTS=yes` confirms the table
grants restored faithfully.

---

## 9. Migration execution (fresh clone, unmodified migrations)
| Step | Result |
|---|---|
| `20260914000000_p8_b1_disclosure_model_foundation.sql` | `rc=0`, 0 errors; base tables **116 → 127**; **11** `disclosure_*` tables |
| `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` | `rc=0`, 0 errors; `uq_dve_reference_nullsafe` created exactly as specified |
| Neither migration was modified during verification | confirmed (statement inventory + content inspection, §35) |

## 10. Migration idempotency
Both migrations were applied a **second** time to the same clone: `b1_rerun_rc=0`, `corr_rerun_rc=0`.
Fingerprints before/after: `tables=11 idx=45 fw=3 purp=4` → **identical**; a schema-only dump of
`public.disclosure_*` before/after is **identical after normalisation** (`diff_lines=0` across 1166 lines
when pg_dump's random `\restrict`/`\unrestrict` tokens are ignored — those two random token lines are the
only raw difference). No duplicate tables, indexes or seeds; no destructive statement (§36).

## 11. Schema verification (live catalogue of the fresh clone)
- **Exactly 11** `disclosure_*` tables, names identical to the contracted set; no 12th table.
- **RLS enabled on all 11** (`relrowsecurity = true`).
- **13 policies**, exactly as contracted: 7 catalogue `_read` SELECT policies (`USING (true)`,
  `TO authenticated` — read-only), member-read + **admin-write** on
  `disclosure_applicability_assessments`, member-read + member-write on
  `disclosure_report_instance_binding`, and read-only on `disclosure_values` / `disclosure_value_evidence`
  (**no authenticated write policy at all**). No permissive write policy anywhere.
- **45 indexes** over the 11 tables, including the contract's `uq_drm_current` (`… WHERE is_current`,
  partial unique) and the correction's `uq_dve_reference_nullsafe` (expression unique over
  `COALESCE(calculation_snapshot_id|emissions_log_id|source_item_id|source_file_id,
  '00000000-0000-0000-0000-000000000000'::uuid)`).
- Runtime re-checks confirmed the B1 constraints V1 had verified: `uq_drm_current` partial uniqueness,
  `disclosure_values_unique`, `disclosure_value_evidence_unique`
  (`UNIQUE (disclosure_value_id, calculation_snapshot_id)`), period-order CHECKs on both period tables, the
  identifier-safety CHECK, the not-in-force CHECK and the enum CHECKs (§22, §23).
- **Zero existing tables altered** — proved independently: in the privileges-inclusive clone, grants,
  policies and RLS flags for all 116 pre-existing tables are **identical before and after** applying both
  migrations (`NON_B1_GRANTS_UNCHANGED=yes`, `NON_B1_POLICIES_UNCHANGED=yes`, `NON_B1_RLS_UNCHANGED=yes`),
  and that clone's existing-table grants match the dev database exactly.

## 12. Seed verification
Measured on the **pristine** clone before the harness wrote anything:
`{'fw': 3, 'purp': 4, 'fwv': 0, 'reqv': 0, 'reqm': 0, 'purpv': 0, 'purpr': 0}` — exactly the three framework
identities (`ESRS_E1, GHG_PROTOCOL, UK_SECR`), the four purpose identities
(`ANNUAL_CARBON, ESRS_E1_QUANT, MANAGEMENT, UK_SECR`) and **no** framework-version, requirement, mapping,
purpose-version or purpose-requirement rows. Re-running the seed is a no-op
(`{'frameworks_inserted': 0, 'purposes_inserted': 0}`) and added no audit row.

---

## 13. F1 re-verification — `create_applicability_assessment` — **PASS**
Independently executed against the fresh clone through the real repository (not a static test):
- **(A) `determined_by = NULL`** → inserted successfully, **no `AmbiguousParameterError`**;
  `determined_by`, `created_by` and `determined_at` are all NULL; `assessed_status` (`UNDETERMINED`),
  `basis`, `reporting_year`, explicit period start/end and `version=1` persisted correctly; the JSONB
  `characteristic_snapshot` round-tripped (proving the `::jsonb` cast path).
- **(B) `determined_by = <valid UUID>`** → inserted successfully; `determined_by` **and** `created_by` equal
  the actor, and `determined_at` is set.
- **No regression of other fields**; validation unchanged (invalid status / blank basis / bad period order
  still raise `DisclosureViolation` — see PQ-2 in §21).
- **Tenant enforcement intact**: cross-tenant write attempts through the tenant-scoped paths are still
  rejected (§28).

## 14. F2 re-verification — `upsert_disclosure_value` — **PASS**
1. Initial materialisation succeeds — **no `AmbiguousParameterError`**.
2. The row persists with the expected values; `effective_class='CUSTOMER_INPUT_REQUIRED'` remains
   **independent** of `value_status='PENDING'`.
3. `value_status` stays within the allowed three-value vocabulary; the four forbidden values are rejected by
   the database (§22).
4. A repeat upsert (RESOLVED, numeric 12.5, unit `kg CO2e`, `source_kind=CALCULATION_AGGREGATE`) **updates the
   same row in place** (same id).
5. Exactly **one** value exists for the unique `(report_version_id, requirement_version_id)` pair
   (`rows=1`).
6. `computed_at` is NULL for PENDING and **set** for RESOLVED.
7. A fully-nullable combination (`requirement_mapping_id=None`, `numeric_value=None`, `value_unit=None`,
   `text_value=None`, `source_kind=None`, `reason` set, `effective_class='NOT_SUPPORTED'`,
   `value_status='UNRESOLVED'`) also executes — i.e. the previously ambiguous NULL-parameter paths are safe.

## 15. F3 re-verification — `link_value_evidence` — **PASS**
| Check | Result |
|---|---|
| First NULL-snapshot link | one row created |
| Second **identical** NULL-snapshot link | **still one row** (same id, payload updated — previously 2 rows) |
| Distinct references on the same value (two different `source_file_id`) | two independent rows (`rows=3` for the value) |
| Re-linking an existing distinct reference | updates that row, **no** 4th row |
| Raw duplicate NULL-snapshot insert (bypassing the repository) | **rejected**, SQLSTATE **23505** by `uq_dve_reference_nullsafe` |
| Index definition | expression unique index over the four COALESCEd reference columns with the zero-UUID sentinel |
| Non-NULL `calculation_snapshot_id` path | unchanged: repeated link upserts to one row, same id |
| B1's original `UNIQUE (disclosure_value_id, calculation_snapshot_id)` | still present |

## 16. F4 re-verification — privileges on the NEW B1 tables — **PASS**
Per-table matrix (14 probes × 11 tables, executed at runtime):
- **anon**: no SELECT/INSERT and no privilege at all on any of the 11 tables.
- **authenticated**: no `TRUNCATE`, `TRIGGER`, `REFERENCES` or `MAINTAIN` on any of the 11 tables; SELECT
  present everywhere; DML present **only** on `disclosure_applicability_assessments` and
  `disclosure_report_instance_binding` (the two policy-governed tables) and revoked on the nine read-only
  surfaces.
- **service_role**: SELECT/INSERT/UPDATE/DELETE on all 11 tables; runtime usability proved with a
  `SET ROLE service_role` session that **reads** B1 rows and **updates** a B1 row (`sqlstate=OK`) —
  the exact capability that was missing before the correction (`BYPASSRLS=true` in this cluster).
- **RLS remains enabled** on all 11 tables; **no existing-table grant or policy changed** (invariance proof,
  §11); no broad RLS remediation was attempted.
- Nothing was modified by this verification task.

## 17. F5 re-verification — audit emission — **PASS**
Executed the four existing B1 write paths and inspected `audit_trail`:
| Write path | Emitted action | Verified |
|---|---|---|
| applicability assessment | `report:disclosure_applicability_assessed` | ✔ action, `record_id` = the new row, `category=report`, `actor=system`, `origin=system`, `organization_id` = tenant, no `reason` |
| report-instance binding | `report:disclosure_report_bound` | ✔ (same assertions) |
| disclosure value materialisation | `report:disclosure_value_materialised` | ✔ (same assertions) |
| value→evidence link | `report:disclosure_evidence_linked` | ✔ (same assertions) |

Also verified: **no** sensitive markers (`signed`, `token`, `secret`, `password`, `jwt`, `http`, `bearer`) in
`old_data`/`new_data`/`changes`/`metadata`; an **idempotent re-seed emits no audit row** (no write occurred);
the mechanism is the **existing** `data.audit.AuditRepository` over the single existing `audit_trail` table
(no new audit table/subsystem — the data layer contains no hand-rolled audit SQL).
**Residual (limitation, not a defect):** the *seed-insert* branch (catalogue write → audit row) cannot be
exercised on a database that already contains the seed identities without deleting those rows, which this
task declined to do; it is covered instead by static inspection and by the static guard test, and the
no-op-audits-nothing behaviour was runtime-verified.

---

## 18. F6 re-verification — runtime coverage — **PASS**
The test code was **inspected**, not merely counted, and then **executed**.

`backend/tests/integration/test_disclosure_b1_runtime.py` — 15 real-PostgreSQL tests, named by defect:
`test_f1_assessment_system_determined_executes`, `test_f1_assessment_actor_determined_executes`,
`test_f2_value_materialisation_executes`, `test_f2_repeat_upsert_updates_one_row`,
`test_f3_null_snapshot_relink_is_idempotent`, `test_f3_null_snapshot_db_backstop_rejects_raw_duplicate`,
`test_f3_distinct_references_stay_representable`, `test_f3_non_null_snapshot_uniqueness_unchanged`,
`test_tenant_isolation_and_pq2_agreement_still_enforced`, `test_approved_and_final_versions_are_immutable`,
`test_b1_writes_emit_audit_entries`, `test_catalogue_seed_audits_only_actual_writes`,
`test_f4_corrected_privilege_posture`, `test_rls_actor_boundary_still_enforced`,
`test_b2_b3_b4_boundary_untouched`. They call the **real repository methods** and assert on **database state**
(rows, SQLSTATE, `has_table_privilege`, `audit_trail` contents, `SET ROLE` sessions). Detection capability
therefore follows directly: the pre-correction SQL raised `AmbiguousParameterError` on those very calls (V1
report; correction report §5/§7), so these tests would fail against the pre-correction code.

`backend/tests/unit/data/test_disclosure_sql_typing.py` — 9 no-database guards: the F1/F2 casts present and
the bare forms absent, the NULL-snapshot branch present, the six audit actions declared and wired, the audit
mechanism reused, `CAT_REPORT` classification, no B2/B3/B4 identifier in executed SQL, and the correction
migration additive/idempotent/complete.

**Executed against the fresh clone:** `INTEGRATION_DATABASE_URL=<clone> pytest
tests/integration/test_disclosure_b1_runtime.py` → **15 passed, rc=0**. The static guards pass in the unit
suite (§32). The suite is also self-guarding: it **skips** (never fails) when the B1 schema is not provisioned
— the environment condition being that B1 has not been applied to `carbontally_test`/the dev database
(0 disclosure tables), which is why `INTEGRATION_DATABASE_URL` was pointed at the clone for this
verification.

## 19. F7 re-verification — helper `PUBLIC EXECUTE` — **PASS (correctly classified P3, not a material defect)**
- **Created by B1?** Yes — `p8_disclosure_is_org_member` / `p8_disclosure_is_org_admin` are defined in
  `20260914000000_p8_b1_disclosure_model_foundation.sql` (lines 426/441) and are used by the B1 RLS policies.
- **Did B1 modify their privilege state?** They carry the PostgreSQL default (`proacl` NULL ⇒ PUBLIC may
  EXECUTE); the correction migration contains **0** references to them, so the correction changed nothing.
- **Does the contract explicitly require a revocation?** **No.** A contract-wide search for
  `PUBLIC EXECUTE`, `REVOKE`, function-privilege and `search_path` requirements returns **no** requirement;
  §23.A/§23.B scope the grant behaviour to table-level policy intent and to B1's own new tables.
- **Actual security-boundary failure?** **No.** Both helpers are `SECURITY DEFINER` with
  `search_path = public, pg_temp`, return only a membership/admin boolean for `auth.uid()`, and at runtime an
  `anon` session **cannot obtain a positive result** (it is false or denied). RLS is defence-in-depth per the
  contract, and B1's enforced boundary is the application layer.
- **Conclusion:** P3 out-of-scope observation, recorded in §37; **not** an unresolved material B1 security
  defect, and no acceptance criterion depends on it.

## 20. PQ-1 result — **PASS**
Exactly the 11 contracted `disclosure_*` tables exist; no 12th table; no intensity table/denominator
catalogue/calculation (runtime `LIKE '%intensity%'` → none).

## 21. PQ-2 result — **PASS**
Both period tables carry explicit `reporting_period_start`/`reporting_period_end` with the order CHECK
(constraint definitions verified live). Runtime: matching binding/assessment periods **accepted**;
mismatching periods **rejected** (`DisclosureViolation`); invalid period order **rejected** for both the
binding and the assessment; the stored period is verbatim (no calendar-year substitution from
`report_generation_queue.reporting_year`).

## 22. PQ-3 result — **PASS**
Live CHECK allows only `PENDING`/`RESOLVED`/`UNRESOLVED`; all four previously-overlapping values
(`CUSTOMER_INPUT_REQUIRED`, `NOT_SUPPORTED`, `NOT_APPLICABLE`, `UNDETERMINED`) are rejected by the database
(SQLSTATE 23514) in this independent run. `effective_class` exists, is CHECK-constrained to the
requirement-class set and remains authoritative; the two dimensions were proven independent in the live
database (`CUSTOMER_INPUT_REQUIRED`+`PENDING` and `NOT_SUPPORTED`+`UNRESOLVED` rows both persisted).

## 23. PQ-4 result — **PASS**
`APPROVED` and `FINAL` report versions reject value **mutation**; `FINAL` rejects value **deletion** (the
frozen row survived); a `DRAFT` version permits deletion (lifecycle-permitted operations still work); **zero**
non-internal triggers exist on the 11 tables (immutability remains app-layer).

## 24. PQ-5 result — **PASS**
No production migration, schema change, RLS change, privilege change or deployment occurred; no production
endpoint was contacted; the 34-migration reconciliation was not attempted. Evidence: the dev/demo database
is unchanged (**0** disclosure tables, 116 base tables, **0** disclosure audit rows), HEAD is unchanged, and
all runtime work was confined to disposable clones (§7). The 34 outstanding migrations remain a separate
production gate.

---

## 25. PQ-6 result — **PASS**
Seeds are exactly the three framework identities and four purpose identities, measured on the pristine clone
before any harness write (§12); **zero** framework-version/requirement/mapping/purpose-version/
purpose-requirement rows; no fabricated statutory content; seed re-run is a no-op.

## 26. PQ-7 result — **PASS**
E1 remains conditional: **no** requirement row carries an `official_identifier` (0 rows), no E1 requirement
mappings exist (0 mapping rows), and no full ESRS/CSRD support is claimed. The only E1 strings in the
codebase are the ratified identity codes `ESRS_E1` / `ESRS_E1_QUANT`.

## 27. PQ-8 result — **PASS**
The correction remains B1-only: 11 tables, one additive B1-scoped migration, two B1 source files, B1 test
files, nothing else; the B1 migration contains no correction content, and no historical migration was
modified.

## 28. Tenant isolation re-verification — **PASS**
Runtime (real roles, fresh clone):
- Repository layer: cross-tenant value write, value write against another organisation's report version,
  cross-tenant instance binding, binding referencing **another organisation's assessment**, cross-tenant
  evidence link and evidence link to a non-existent value are **all rejected** (`DisclosureViolation`).
- RLS layer (`SET ROLE authenticated` + `auth.uid()` claims): **owner** reads its own organisation's values
  and assessments and sees **zero** rows of another organisation; **member** reads but cannot write an
  assessment (admin-only); **viewer** reads and cannot write; **another tenant's owner** reads zero rows and
  cannot write org A; **anon** is denied outright; **service_role** can read and write (the corrected
  capability).

## 29. RLS re-verification — **PASS**
RLS enabled on all 11 B1 tables (§11); the 13 policies are exactly the contracted intent (7 read-only
catalogue policies + admin-write assessment policy + member-write binding policy + member-read policies +
read-only values/evidence); `USING (true)` appears **only** on catalogue SELECT policies (read-all, as
contracted) and never on a write policy; **no existing-table policy was modified** (invariance proof, §11);
nothing was remediated or weakened by this task.

## 30. Audit re-verification — **PASS**
See §17: four write paths emit the expected existing-taxonomy actions with correct entity, actor
(`system`/actor-supplied), `category=report`, tenant id, no `reason`, and no sensitive content; the existing
`audit_trail`/`AuditRepository` is reused and **no new audit system exists** (single audit table; no
hand-rolled audit SQL in the data layer).

## 31. Immutability re-verification — **PASS**
See §23 (PQ-4): APPROVED/FINAL mutation rejected, FINAL deletion rejected, DRAFT deletion allowed, zero B1
triggers, and the guards run before the (now executable) SQL — no bypass introduced by the correction.

## 32. Regression tests — **PASS**
| Target | Result |
|---|---|
| `tests/unit/domain/test_disclosure.py` | pass (17) |
| `tests/unit/data/test_disclosure_migration.py` | pass (17) |
| `tests/unit/data/test_disclosure_sql_typing.py` | pass (9) |
| `tests/integration/test_disclosure_b1_runtime.py` (clone) | **15 passed, rc=0** |
| `tests/unit/domain/` | pass |
| `tests/unit/api/test_v3_report_lifecycle.py` + `tests/unit/api/test_v3_reports.py` | pass (targeted regression, rc=0) |
| combined targeted run | **rc=0** |
| broader `tests/unit/` | **rc=0** (no failures) |

No test was modified or weakened. No unrelated pre-existing failure was observed.

## 33. B2/B3/B4 boundary — **PASS**
Runtime: no `evidence_line_items` table; no `calculation_snapshots.source_line_item_id` column; no
intensity tables; no narrative/commentary/frozen-artefact tables. The data layer's executed SQL contains no
such identifier (static guard). No line-item addressability, intensity, narrative or finalisation work was
introduced.

## 34. Phase 8-X boundary — **PASS**
No Phase 8-X object, file or reference was introduced; the only new migration is the B1 correction.

---

## 35. Git / worktree verification

| Item | Baseline | After this verification |
|---|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` | **unchanged** |
| Branch | `main` | `main` |
| Staged | 0 | **0** |
| Modified (tracked) | 208 | **208 (unchanged)** |
| Tracked files matching `disclosure|p8_b1` in the diff | 0 | **0** |
| Existing migrations modified | 0 | **0** |
| Untracked (porcelain) | 73 | **73** (this report lives inside an already-collapsed untracked `docs/cline/reports/` directory) |
| Migrations | 57 | **57** |

`git diff -- <B1 paths>` returns **0 lines for all four paths** — because the B1 files are **untracked**
(`git ls-files` → 0 for those paths), so git has no committed baseline to diff against. This is a
**verification limitation**, mitigated by independent evidence:
- the correction's *statements* exist only in the new migration — the non-comment statement inventory is
  exactly 22 `GRANT`/`REVOKE` statements + `CREATE UNIQUE INDEX IF NOT EXISTS` + `COMMENT ON INDEX`, with no
  destructive token (`DROP`, `DELETE FROM`, `TRUNCATE`, `ALTER TABLE`, `USING (true)`) anywhere;
- the B1 migration contains **none** of the correction's identifiers (`uq_dve_reference_nullsafe`,
  `service_role`, `REVOKE TRUNCATE`) and is still 583 lines with no destructive statement — i.e. the
  correction was not folded back into it;
- the two migrations apply **independently and in order** (B1 alone `rc=0`; correction after B1 `rc=0`, in two
  different clones), so the correction is additive rather than a rewrite;
- no *tracked* file matching B1 (or any migration) was modified, so the corrected source files are the same
  untracked artefacts the correction produced.

Untracked B1-related files (unchanged set): the B1 migration, the correction migration,
`backend/data/disclosure.py`, `backend/domain/disclosure.py`,
`backend/tests/unit/domain/test_disclosure.py`, `backend/tests/unit/data/test_disclosure_migration.py`,
`backend/tests/unit/data/test_disclosure_sql_typing.py`,
`backend/tests/integration/test_disclosure_b1_runtime.py`, plus the Phase-8 documents/reports.
Nothing was reverted, cleaned or restored; all unrelated work is preserved.

## 36. Deployment-precondition assessment
- **Clean database → migration success:** in **two** fresh clones the B1 migration and then the correction
  migration both applied with `rc=0` and 0 errors, on first attempt and again on re-application (idempotent,
  `diff_lines=0`). **Runtime-verified.**
- **Already-duplicated historical data:** the correction report observed that `CREATE UNIQUE INDEX` fails
  **loudly** when duplicates already exist. That condition was **not** reproduced here: per instruction no
  duplicate rows were manufactured, no deduplication recipe was executed and no data was deleted. The
  behaviour is deterministic from index semantics (a unique index cannot be created over violating rows).
- **Distinction:** (a) **clean-DB migration success — PASS, runtime-verified**; (b) **behaviour against
  already-duplicated historical data — not exercised** (by instruction); the migration is
  **non-destructive** (it never deletes or repairs rows — an operator would need the documented, explicitly
  authorised dedupe first).
- **Operational relevance today:** every environment holds **0** `disclosure_value_evidence` rows (B1 is
  undeployed; the dev/demo database still has 0 disclosure tables), so the precondition is theoretical for the
  current state. Recorded as P3 operational consideration R4.

## 37. Findings
| # | Finding | Severity | Status | Classification |
|---|---|---|---|---|
| R1 | F7 — B1-created helpers `p8_disclosure_is_org_member`/`_admin` retain the default PUBLIC EXECUTE; the contract requires no revocation; anon cannot obtain a positive result | P3 | CONFIRMED | Out-of-scope observation, nonblocking |
| R2 | `delete_disclosure_value` is not audited (contract §26 lists catalogue/reporting writes and value materialisation, not deletion) | P3 | CONFIRMED | Nonblocking observation |
| R3 | The runtime integration suite **skips** where the B1 schema is not provisioned (B1 is not applied to the dev/`carbontally_test` databases), so it only executes where B1 is present | P3 | CONFIRMED | Environment/verification condition |
| R4 | Deployment precondition: creating `uq_dve_reference_nullsafe` on already-duplicated historical data fails loudly and needs a documented, authorised dedupe first | P3 | CONFIRMED | Operational consideration (§36) |
| R5 | B1 files are untracked, so git cannot prove the B1 migration is byte-identical to its pre-correction state | P3 | CONFIRMED | Verification limitation (mitigated, §35) |
| R6 | The seed-**insert** audit branch was not runtime-exercised (it would require deleting seed identities) | P3 | CONFIRMED | Verification limitation (§17) |

**No P0, P1 or P2 finding remains.** All material V1 findings (F1–F5) are closed and runtime-verified; F6 is
closed by an executed runtime suite; F7 is correctly classified and is not a material B1 security defect.

---

## 38. Verification limitations
1. **Reconstructed environment:** clones were built by schema-only restore of the dev database with a
   manually mirrored `public` default ACL — faithful for the objects exercised, not byte-identical to the dev
   instance. The privileges clone restored with 73 benign errors (default-privilege/admin-function noise) yet
   its existing-table grants matched the dev database exactly.
2. **RLS actor emulation:** `SET ROLE` + `request.jwt.claims` exercises policies and privileges but not the
   full GoTrue/PostgREST request path; B1 has no consultant/PE-scoped policy to exercise (as contracted).
3. **Untracked-file diff gap** (§35) — mitigated by statement inventory, content inspection and independent
   application order.
4. **Seed-insert audit branch not runtime-exercised** (§17).
5. **Already-duplicated-data behaviour of the index migration not exercised**, by instruction (§36).
6. Only B1-related and unit/regression suites were run; the unrelated integration modules were not run.
7. Production remains untouched and unverified by design (PQ-5).

## 39. Verification matrix

| Area | Requirement | Method | Result | Evidence |
|---|---|---|---|---|
| Schema | exactly 11 B1 tables, no extra | live catalogue on fresh clone | PASS | 11 names match; 116→127 base tables |
| Schema | zero existing tables altered | privileges-inclusive clone before/after | PASS | grants/policies/RLS identical for all 116 tables |
| Migration | applies on current baseline | apply to fresh clone | PASS | `b1_rc=0`, `corr_rc=0`, 0 errors |
| Migration idempotency | re-run is a no-op | second application + dump diff | PASS | `rc=0`×2; `diff_lines=0` (1166 lines) |
| Seeds | identities only, no invented content | pristine-state counts | PASS | fw=3, purp=4, other catalogue tables 0 |
| F1 | assessment executes, system + actor | real repository calls | PASS | both insert; determined_at NULL/set correctly |
| F2 | materialisation + repeat upsert | real repository calls | PASS | 1 row per pair; in-place update; computed_at on RESOLVED |
| F3 | NULL-snapshot link idempotency | repository + raw SQL probe | PASS | re-link → 1 row; raw duplicate → 23505 |
| F4 | B1-table privilege posture | 14 probes × 11 tables + role sessions | PASS | all counters clean; service_role usable |
| F5 | audit emission via existing mechanism | 4 write paths → `audit_trail` | PASS | correct action/entity/actor/category; no secrets |
| F6 | runtime coverage exists and passes | code inspection + execution | PASS | 15/15 runtime tests; 9 static guards |
| F7 | correctly classified | source + live ACL + contract search | PASS | P3 out-of-scope; anon cannot get a positive result |
| PQ-1 | 11 tables / no intensity | live catalogue | PASS | 0 intensity objects |
| PQ-2 | explicit periods, order + agreement | repository + constraint definitions | PASS | matched accepted; mismatch/order rejected |
| PQ-3 | value_status vocabulary + separation | live CHECK + runtime inserts | PASS | 4 forbidden → 23514; both states persist |
| PQ-4 | APPROVED/FINAL immutability, no trigger | repository calls + trigger count | PASS | mutations/deletion rejected; DRAFT delete OK |
| PQ-5 | no production action | dev-DB re-check, HEAD, no remote access | PASS | dev DB 0 disclosure tables / 116 base tables |
| PQ-6 | identity seeds only | pristine counts | PASS | 3 frameworks, 4 purposes, 0 versions |
| PQ-7 | E1 conditional | live rows | PASS | 0 official identifiers, 0 mappings |
| PQ-8 | B1-only correction | statement inventory + git | PASS | one additive migration; no tracked B1 change |
| Tenant isolation | cross-tenant denial | repository + RLS sessions | PASS | all cross-tenant paths rejected; 0 foreign rows |
| RLS | enabled, intended policies, no permissive write | live `pg_policies` + runtime probes | PASS | 11/11 enabled; 13 intended policies |
| Audit | correct, safe, existing infra | runtime audit inspection | PASS | see §17/§30 |
| Immutability | APPROVED/FINAL frozen | runtime repository calls | PASS | see §23 |
| Regression | targeted + broader suites | pytest | PASS | rc=0 (see §32) |
| B2 exclusion | no evidence_line_items / source_line_item_id | live catalogue | PASS | 0 / 0 |
| B3 exclusion | no intensity objects | live catalogue | PASS | 0 |
| B4 exclusion | no narrative/commentary/frozen objects | live catalogue | PASS | 0 |
| Phase 8-X exclusion | untouched | live catalogue + git | PASS | 0 objects; no new non-B1 files |

---

## 40. Final verdict

### `B1 V1 INDEPENDENT RE-VERIFICATION — PASS WITH NONBLOCKING FINDINGS`

| Dimension | Status |
|---|---|
| **IMPLEMENTED** | The 11-table B1 foundation plus the bounded correction (F1, F2, F3 app+DB, F4, F5) are present and complete in B1 scope. |
| **TESTED** | 43 B1 unit tests (incl. 9 static guards) and 15 runtime integration tests pass; targeted regressions and the broader `tests/unit/` suite pass (`rc=0`). |
| **RUNTIME VERIFIED** | Independently, in a **fresh** PostgreSQL 17.6 clone: one 87-check harness ran **87 PASS / 0 FAIL**, covering migration execution, idempotency, seeds, F1–F5, PQ-1…PQ-8, tenant isolation, RLS allow/deny across real roles, immutability and the B2/B3/B4 boundary. |
| **INDEPENDENTLY VERIFIED** | **Yes** for this gate's scope: schema, migration, idempotency, seeds, F1–F7 classification, PQ-1…PQ-8, tenant isolation, RLS, audit, immutability, regression, boundaries and git scope. |
| **PRODUCTION DEPLOYED** | **No** — no production migration, schema, RLS or privilege change, no deployment, no production access. |

**Acceptance criteria (§38 of the task):** criteria 1–17 are all satisfied. No material B1 defect remains; the
only open items are P3 observations and verification limitations (R1–R6, §37/§38).

**Not claimed:** production readiness, Phase 8 completion, regulatory/ESRS/CSRD compliance, assurance, or
certification of any kind.

*STOP — re-verification complete. Nothing was fixed, patched, committed or pushed; no production action was
taken; B2/B3/B4 and Phase 8-X were not started; no broad RLS remediation was performed. The Product Owner
decides the next task.*
