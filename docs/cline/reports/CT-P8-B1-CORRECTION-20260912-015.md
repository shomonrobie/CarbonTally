# CT-P8-B1-CORRECTION-20260912-015

**Task ID:** `CT-P8-B1-CORRECTION-20260912-015`
**Title:** Phase 8 Batch B1 — Bounded Correction of V1-Confirmed Defects
**Role:** implementation engineer (bounded correction only)
**Date:** 2026-09-12 · **HEAD:** `19e4f01c176eee5870f3c15038b6e7c68b23281c` · **Branch:** `main`
**Runtime used:** disposable clone `b1v1_correction` in the local dev PostgreSQL 17.6 cluster — **not production**
**Final verdict:** `B1 CORRECTION COMPLETE — READY FOR V1 RE-VERIFICATION WITH NONBLOCKING FINDINGS`

> Correction basis: gate **V1** confirmed F1/F2 (P1) and F3/F4/F5 (P2). All four
> corrections are implemented, and **executed against a real PostgreSQL
> database**: F1, F2, F3 and F5 reproduce before the fix and pass after it; F4 is
> verified by privilege/RLS probes. F6 is addressed with a new runtime
> integration suite (15 tests) plus static guards. F7 was investigated and left
> unchanged (out-of-scope: the contract does not unambiguously require it).
> Nothing was committed, pushed or deployed; production was never touched.

---

## 1. Task ID
`CT-P8-B1-CORRECTION-20260912-015`.

## 2. V1 report reviewed
`docs/cline/reports/CT-P8-B1-V1-INDEPENDENT-VERIFICATION-20260912-014.md` — read in full. Its findings were
treated as *claims to be reproduced*, not as instructions: **all four addressable findings were reproduced
before any edit** (§5, §7, §9, §11, §12).

## 3. Governing documents
- Contract: `docs/architecture/CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md` (§9–§11, §22–§27).
- PO ratification: `docs/architecture/CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md` (PQ-1…PQ-8).
- B1 implementation report: `docs/cline/reports/CT-P8-B1-IMPLEMENTATION-20260912-013.md`.
- Authorisation: `docs/cline/reports/CT-P8-B1-PO-IMPLEMENTATION-AUTHORISATION-20260912-012.md`.
- Established repository patterns inspected: `20260807070000_add_new_table_rls.sql` (new-table privilege
  pattern), `20260810050000_v3m6_entity_rls.sql` (helper-function grant pattern), `backend/data/audit.py`,
  `backend/domain/audit.py`, `backend/infra/audit_logger.py`, `backend/api/audit_helpers.py`,
  `backend/tests/integration/conftest.py`, `backend/tests/integration/test_v3_rls_behavior.py`.

## 4. Pre-correction repository baseline

| Item | Value |
|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (unchanged through the task) |
| Branch | `main` |
| Staged | 0 |
| Modified (tracked) | 208 (all pre-existing; **none** is a B1 file) |
| Untracked (porcelain entries) | 71 |
| Migrations | 56 (highest: `20260914000000_p8_b1_disclosure_model_foundation.sql`) |
| Dev DB disclosure tables | 0 (B1 never applied to the dev/demo database) |

B1 files inspected byte-for-byte before editing: `supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql`
(583 lines, **never modified**), `backend/domain/disclosure.py` (332 lines), `backend/data/disclosure.py`
(462 lines), `backend/tests/unit/domain/test_disclosure.py`, `backend/tests/unit/data/test_disclosure_migration.py`.

---

## 5. F1 reproduction — `create_applicability_assessment` (P1)
Harness: `/tmp/c_repro.py` (outside the repo) against the clone with the **unmodified** code:

```
F1a determined_by=NULL :: REPRODUCED AmbiguousParameterError: could not determine data type of parameter $9
F1b determined_by=UUID :: REPRODUCED AmbiguousParameterError: could not determine data type of parameter $9
```
Both cases from the V1 report were reproduced (system write and actor write). Root cause confirmed by reading
the statement: `$9` is used as `determined_by` (uuid), inside `CASE WHEN $9 IS NULL` (untyped) and again as
`created_by` (uuid).

## 6. F1 correction
`backend/data/disclosure.py` → `create_applicability_assessment`. The **smallest safe** change: explicit
`::uuid` casts on the reused parameter (the existing repository pattern — `data/audit.py` casts
`$3::uuid`, `$4::uuid`, `$7::jsonb` the same way), plus an explicit `::jsonb` on the JSONB parameter:

```sql
VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6::jsonb, $7, $8, $9::uuid,
        CASE WHEN $9::uuid IS NULL THEN NULL ELSE now() END, $10, $9::uuid)
```
Column type, nullability, validation, `determined_by`/`determined_at` semantics and the table design are
**unchanged**. An inline comment records why the casts must not be "simplified" away.

## 7. F2 reproduction — `upsert_disclosure_value` (P1)
```
F2 materialisation :: REPRODUCED AmbiguousParameterError: inconsistent types deduced for parameter $6
DETAIL:  text versus character varying
```
Root cause confirmed: `$6` (`value_status`) is compared to the text literal `'RESOLVED'` while also being
assigned to the `varchar` column `value_status`.

## 8. F2 correction
Explicit `::varchar` on the reused parameter (and `$1::uuid, $2::uuid, $3::uuid, $4::uuid` for the uuid
parameters) so both uses deduce one type:

```sql
VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6::varchar, $7, $8, $9, $10, $11, $12, $13,
        CASE WHEN $6::varchar = 'RESOLVED' THEN now() ELSE NULL END)
```
Preserved exactly: `UNIQUE (report_version_id, requirement_version_id)` upsert, `value_status` semantics
(PENDING/RESOLVED/UNRESOLVED only), `effective_class` as the authoritative derived outcome, `source_kind`,
`computed_at`-on-RESOLVED, tenant enforcement and APPROVED/FINAL immutability (all runtime-tested, §22/§25).

## 9. F3 reproduction — NULL-snapshot evidence links duplicate (P2)
```
F3 repeated identical link rows :: 2 (1 = idempotent, >1 = REPRODUCED duplicate)
```
The same value linked twice with `calculation_snapshot_id = NULL` produced **two** rows: PostgreSQL treats
NULLs as distinct under `UNIQUE (disclosure_value_id, calculation_snapshot_id)`, so the `ON CONFLICT` upsert
never matched.

## 10. F3 correction
Two contract-consistent halves (both inside B1; no model redesign, no B2):

1. **Application layer** (`link_value_evidence`): the NULL-snapshot case now performs an explicit
   *re-link-as-update* keyed on the evidence **reference** — `UPDATE … WHERE disclosure_value_id = $1 AND
   calculation_snapshot_id IS NULL AND emissions_log_id IS NOT DISTINCT FROM $5::uuid AND source_item_id IS
   NOT DISTINCT FROM $6::uuid AND source_file_id IS NOT DISTINCT FROM $7::uuid`, falling back to
   `INSERT … VALUES (…, NULL, …)`. `source_page`/`evidence_completeness`/`contribution_share` stay the
   reference's mutable payload; the four evidence columns are its identity.
2. **Database backstop** (correction migration): `uq_dve_reference_nullsafe`, a NULL-safe expression unique
   index over `(disclosure_value_id, COALESCE(calculation_snapshot_id|emissions_log_id|source_item_id|
   source_file_id, '00000000-0000-0000-0000-000000000000'::uuid))`. The zero UUID is the codebase's
   established machine/"no value" marker (`data/audit.py::_SYSTEM_UUID`, `data/documents.py`,
   `tests/integration/conftest.py`) and can never be a real referenced id.

The pre-existing non-NULL path is untouched: `UNIQUE (disclosure_value_id, calculation_snapshot_id)` still
exists and its upsert semantics are preserved (runtime-tested). `evidence_line_items` / `source_line_item_id`
(B2) are **not** introduced.

**Observed deployment precondition (documented in the migration, not auto-remediated):** on a database where
the *pre-correction* code already produced duplicates, `CREATE UNIQUE INDEX` fails **loudly** (this happened
in the clone during verification and is reproduced in §17). The migration never deletes evidence rows; the
exact authorised dedupe statement is recorded as a comment in the migration for an operator to run
deliberately. Every real environment holds 0 `disclosure_value_evidence` rows (B1 is undeployed), so the index
creates cleanly there.

---

## 11. F4 assessment and correction — B1-table privileges (P2)
**Assessment (runtime, before correction):** with the B1 migration alone, `service_role` held only the
environment default (`REFERENCES, TRIGGER, TRUNCATE`) — it **could not SELECT or INSERT** any B1 table
("permission denied", reproduced twice) — and `authenticated` kept `TRUNCATE / TRIGGER / REFERENCES /
MAINTAIN`, which the local Supabase `public` default ACL grants to new tables and which the repository's
established pattern explicitly revokes (TRUNCATE is **not** gated by RLS —
`20260807070000_add_new_table_rls.sql` states this rationale).

**Correction (scoped strictly to the 11 new B1 tables, in the new migration):**
```sql
GRANT ALL ON TABLE public.disclosure_<t> TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_<t> FROM authenticated;
```
× 11 tables. This mirrors the ratified repository pattern exactly. Not changed: any existing table's grants or
policies; the wider RLS baseline; `anon` (B1 already revoked ALL from `anon`); the authenticated DML posture
B1 chose (SELECT-only on the 7 catalogue tables + `disclosure_values` + `disclosure_value_evidence`;
SELECT/INSERT/UPDATE/DELETE on `disclosure_applicability_assessments` + `disclosure_report_instance_binding`);
the RLS policies themselves (no policy was dropped, disabled or weakened, and no `USING (true)` write policy
was introduced).

**Verified after correction (all 11 tables):** `anon` holds no privilege; `authenticated` holds no
TRUNCATE/TRIGGER/REFERENCES/MAINTAIN; `service_role` holds SELECT/INSERT/UPDATE/DELETE (counter probes:
`anon_any_priv=0`, `auth_trunc_or_trig_or_ref_or_maint=0`, `service_role_missing_dml=0`,
`auth_write_on_readonly_tables=0`). `service_role` has `BYPASSRLS=true` in this cluster, so the grant is
genuinely usable (§23).

## 12. F5 assessment and correction — audit emission (P2)
**Assessment (runtime, before correction):** `before=0 after=0` B1 audit rows for five B1 writes; the data
layer contained no audit call. Confirmed: the contract expects B1 write paths to emit existing audit actions
(§22/§24/§26) while introducing **no** new audit table or taxonomy.

**Correction:** the six B1 write paths that exist today emit one entry each through the **existing**
mechanism — `data.audit.AuditRepository` over `public.audit_trail` — via a single best-effort module helper
`_record_audit(...)` in `backend/data/disclosure.py` (mirroring the established
`backend/api/audit_helpers.py` precedent: never raise into the caller). Action names are declared as a pure
vocabulary in `backend/domain/disclosure.py`:

| Write path | Action | Entity type |
|---|---|---|
| framework identity seed | `report:disclosure_framework_seeded` | `disclosure_frameworks` |
| purpose identity seed | `report:disclosure_purpose_seeded` | `disclosure_report_purposes` |
| applicability assessment | `report:disclosure_applicability_assessed` | `disclosure_applicability_assessments` |
| report instance binding | `report:disclosure_report_bound` | `disclosure_report_instance_binding` |
| value materialisation/update | `report:disclosure_value_materialised` | `disclosure_values` |
| value→evidence link | `report:disclosure_evidence_linked` | `disclosure_value_evidence` |

The `report` head classifies all six as `CAT_REPORT` under the existing taxonomy (asserted in the test
suite). The seed emits entries only for rows it actually inserted, so an idempotent re-run audits nothing.
No write path was invented: B1 exposes no requirement/mapping/purpose-version writers, so none were audited.
The catalogue **read** methods and `delete_disclosure_value` were left un-audited — the contract's event table
lists catalogue/reporting **writes** and value materialisation; deletion is not an audited event in §26 (see
§33).

**Verified (runtime):** 5 write calls → 5 `audit_trail` rows (delta 5); each carries the expected
`action_type`, `record_id`, `metadata.category = report`, `actor = system`, `origin = system`,
`organization_id`; no secrets/signed URLs/payload dumps (asserted).

## 13. F6 correction — runtime test coverage
See §18/§19/§20. A new runtime integration module executes the B1 repositories, guards and privileges
against real PostgreSQL (**15 tests, all passing**), and a new static guard module (9 tests) fails fast in
the unit suite if a required cast, the NULL-snapshot branch or the audit wiring is removed. The existing
pure/unit tests were **not** deleted or weakened.

## 14. F7 assessment — helper-function `PUBLIC EXECUTE` (P3) — **not changed**
The helpers `p8_disclosure_is_org_member` / `p8_disclosure_is_org_admin` **are** created by B1 (case B of the
task's decision rule), so per instruction the change was withheld unless the B1 contract requires it
*explicitly and unambiguously*. It does not: contract §23.A governs table-level read/write policy intent, and
§23.B limits the grant behaviour B1 introduces to "its own new tables (no `anon` grants)". The comparable
repo helper (`is_entity_member`, `20260810050000_v3m6_entity_rls.sql`) does `REVOKE ALL … FROM PUBLIC`, but
that is a convention, not a B1 contract requirement, and this task must not launch general privilege
hardening. **Recorded as an existing, out-of-scope observation** (P3); the correction migration deliberately
leaves the functions and their ACL untouched.

---

## 15. Database migration changes
**One new additive migration** (the B1 migration and all historical migrations are byte-identical):

`supabase/migrations/20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` (156 lines)

* Timestamp-ordered after `20260914000000` (repo ordering convention); migration count 56 → 57.
* **F4**: 11 × `GRANT ALL … TO service_role` + 11 × `REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN … FROM authenticated`.
* **F3**: `CREATE UNIQUE INDEX IF NOT EXISTS uq_dve_reference_nullsafe …` + `COMMENT ON INDEX`.
* Additive, deterministic, idempotent; **no** `DROP`, `ALTER TABLE`, `DELETE`, `TRUNCATE` or policy statement
  (asserted by a unit guard); no `USING (true)` anywhere; no existing table touched; no new table.
* Header documents the F3/F4 rationale, the B1 scope discipline, the deployment precondition and the
  explicitly-authorised dedupe recipe (commented, never executed).

**Runtime state:**
| Step | Result |
|---|---|
| B1 migration applied to clone (run 1) | `rc=0`; 116 → 127 public base tables; 11 `disclosure_*` |
| Correction migration applied (run 1, clean data) | `rc=0`, 0 errors; index created exactly as specified |
| Correction migration applied (run 2, idempotency) | `rc=0`, 0 errors; grants snapshot **identical** across runs |
| Correction migration on data with pre-fix duplicates | **fails loudly** by design (documented; index never silently skips) |

## 16. Runtime database used
`b1v1_correction` — a **disposable** database created inside the local dev Supabase PostgreSQL 17.6 cluster
(`supabase_db_carbon_ledger`, `127.0.0.1:54426`): `CREATE DATABASE` + schema-only `pg_dump` restore of the dev
schema (116 base tables, all dependency tables, `auth.uid()`, `anon`/`authenticated`/`service_role`), with the
dev database's `public` default ACL mirrored (`{postgres=arwdDxtm, anon=Dxtm, authenticated=Dxtm,
service_role=Dxtm}`) so the privilege assertions are meaningful. B1 + the correction were then applied.

**Production was never contacted; the dev/demo database was never modified** (re-verified at the end: 0
disclosure tables, 116 base tables, and the B1 migration was *not* applied there). The clone was dropped at
the end of the task (§34).

## 17. Runtime verification performed
| # | Requirement (task §20) | Method | Result |
|---|---|---|---|
| 1 | B1 migration state | apply + catalogue interrogation | PASS (11 tables, 127 base tables) |
| 2 | correction migration state | apply twice + grant diff | PASS (rc=0 ×2, stable grants, index present) |
| 3 | F1 corrected execution | repository call: `determined_by=NULL` and actor UUID | PASS — both insert; `determined_at` NULL for system, set for actor; `created_by` set for actor |
| 4 | F2 corrected execution | repository call: materialise + repeat upsert (RESOLVED, numeric) | PASS — one row, updated in place, `computed_at` set on RESOLVED |
| 5 | F3 corrected idempotency | repeated identical link; distinct references; raw duplicate; non-NULL path | PASS — 1 row on re-link (was 2); distinct references keep 2 rows; raw duplicate rejected (23505); non-NULL upsert unchanged |
| 6 | F4 corrected privilege posture | `has_table_privilege` matrix (13 probes × 11 tables) + counter probes | PASS — all four counters 0 |
| 7 | F5 audit emission | 5 write calls → `audit_trail` rows inspected | PASS — delta 5, expected action/entity/actor/category, no sensitive content |
| 8 | tenant isolation | repository rejections + RLS session probes | PASS (§22) |
| 9 | immutability | APPROVED/FINAL upsert + delete rejection; DRAFT delete allowed | PASS (§25) |
| 10 | regression | full unit suite, targeted lifecycle/report suites | PASS (§21) |

Pre-fix/post-fix deltas for the same harness (`/tmp/c_repro.py`):
```
BEFORE (unmodified code)                      AFTER (corrected code)
F1a determined_by=NULL → AmbiguousParameterError $9      → UNEXPECTED SUCCESS <uuid>
F1b determined_by=UUID → AmbiguousParameterError $9      → UNEXPECTED SUCCESS <uuid>
F2 materialisation     → AmbiguousParameterError $6      → UNEXPECTED SUCCESS <uuid>
F3 repeated link rows  = 2 (duplicate)                   → 1 (idempotent)
F5 audit rows (delta)  = 0                               → 5
```
(The harness's "UNEXPECTED SUCCESS" wording is the pre-fix expectation inverted; the run values are the
successful ids.)

---

## 18. Tests added / changed
**Added (3 files; none existing was weakened):**
1. `backend/tests/integration/test_disclosure_b1_runtime.py` — **15 runtime tests** against real PostgreSQL
   (skips — never fails — when the B1 schema is not provisioned, matching the suite's fail-safe convention):
   F1 ×2 (system / actor `determined_by`), F2 ×2 (materialisation / repeat upsert), F3 ×4 (re-link
   idempotency / DB backstop rejects a raw duplicate / distinct references representable / non-NULL
   uniqueness unchanged), tenant + PQ-2 agreement ×1, APPROVED/FINAL immutability ×1, F5 audit ×2,
   F4 privilege posture ×1, RLS actor boundary ×1, B2/B3/B4 boundary ×1.
2. `backend/tests/unit/data/test_disclosure_sql_typing.py` — **9 static guards** (no DB): the F1/F2 casts are
   present and the bare forms absent; the NULL-snapshot branch exists; six audit actions declared and wired;
   audit reuses `AuditRepository` (no hand-rolled ledger SQL); all six actions classify as `CAT_REPORT`; no
   B2/B3/B4 identifier in the executed SQL; the correction migration is additive/idempotent and covers all 11
   tables with no `USING (true)`.
3. `docs/cline/reports/CT-P8-B1-CORRECTION-20260912-015.md` (this report).

**Changed:** `backend/data/disclosure.py` (F1, F2, F3, F5 + docstring/imports), `backend/domain/disclosure.py`
(audit-action vocabulary). **Unchanged:** every existing test file, the B1 migration, all historical migrations.

## 19. Tests executed
| Target | Command (backend venv) | Result |
|---|---|---|
| New runtime suite (clone) | `INTEGRATION_DATABASE_URL=<clone> pytest tests/integration/test_disclosure_b1_runtime.py -q` | **15 passed, rc=0** |
| New static guards | `pytest tests/unit/data/test_disclosure_sql_typing.py -q` | 9 passed |
| B1 unit tests (existing) | `pytest tests/unit/domain/test_disclosure.py tests/unit/data/test_disclosure_migration.py -q` | 34 passed (unchanged) |
| Targeted regressions | `pytest tests/unit/data tests/unit/domain tests/unit/api/test_v3_report_lifecycle.py tests/unit/api/test_v3_reports.py -q` | **rc=0, all passed** |
| Broader unit suite | `timeout 300 pytest tests/unit -q` | **rc=0, all passed** (completed inside the cap this run) |
| Runtime constraint/privilege probes (ad hoc) | clone `psql` probes (grant matrix, counter probes, index) | all as expected (§11) |

Test counts: B1 unit files = 17 (`test_disclosure.py`) + 17 (`test_disclosure_migration.py`) + 9 (new guards)
= **43**; runtime integration = **15**. Exact aggregate counts are not printed by this pytest configuration
(`addopts = -q`); success is asserted by exit status (rc=0) and the dot output.

## 20. Test results
All executed suites passed (`rc=0`); no failures, no errors, no skips in the targets above. The runtime suite
executes the real repositories against PostgreSQL — the exact class of defect V1 found now fails there
(`test_f1_assessment_system_determined_executes`, `test_f2_value_materialisation_executes`,
`test_f3_null_snapshot_relink_is_idempotent`, `test_f3_null_snapshot_db_backstop_rejects_raw_duplicate`,
`test_b1_writes_emit_audit_entries`, `test_f4_corrected_privilege_posture`).

## 21. Regression results
- Report lifecycle / reports (`tests/unit/api/test_v3_report_lifecycle.py`, `tests/unit/api/test_v3_reports.py`,
  `tests/unit/domain/`): all pass.
- Full `tests/unit/`: rc=0.
- No unrelated/pre-existing failure was observed, so none needed separate documentation.
- No existing test was modified; `report_versions`, `report_generation_queue`, `calculation_snapshots`,
  `emissions_logs`, `manual_extraction_items`, `organization_files`, factor matching, extraction, legacy
  reporting and billing were not touched by this task.

---

## 22. Tenant verification
Runtime-verified after correction (both layers):
- Repository: cross-tenant `upsert_disclosure_value` → `DisclosureViolation`; cross-tenant
  `create_instance_binding` → `DisclosureViolation`; cross-tenant `link_value_evidence` →
  `DisclosureViolation`; unknown report → `DisclosureViolation`; PQ-2 period mismatch → `DisclosureViolation`.
- RLS (real `SET ROLE authenticated` sessions): an owner reads its own organisation (1 row) and sees **0** rows
  for another organisation; a member cannot INSERT an assessment for its own org; an owner cannot INSERT an
  assessment for another organisation.
- No tenant check was weakened to make SQL execute — the F1/F2 fixes add parameter typing only.

## 23. RLS / privilege verification
- Privilege matrix (13 `has_table_privilege` probes × 11 tables) all correct; counter probes:
  `anon_any_priv=0`, `auth_trunc_or_trig_or_ref_or_maint=0`, `service_role_missing_dml=0`,
  `auth_write_on_readonly_tables=0`.
- `service_role` usability proven end-to-end in a `SET ROLE service_role` session: it can now SELECT B1 rows
  and UPDATE a B1 row (previously "permission denied"); it also has `BYPASSRLS=true`.
- RLS itself is **unchanged**: still enabled on all 11 tables (verified in V1 and untouched here — this task
  contains no policy statement); `anon` still denied; owner/member/viewer boundaries still enforced; no
  `USING (true)` write policy introduced; the wider RLS baseline and every existing table's grants/policies
  left untouched.

## 24. Audit verification
Runtime: five B1 writes produced five `audit_trail` rows with the intended `action_type` values, the B1
entity id in `record_id`, `metadata.category='report'`, `metadata.actor='system'`,
`metadata.origin='system'`, `metadata.organization_id` = the tenant, and no `reason`. A sensitive-marker scan
(`signed`, `token`, `secret`, `password`, `jwt`, `http`, `bearer`) over `old_data`/`new_data`/`changes`/
`metadata` found none. An idempotent re-seed produced **no** additional audit row (no write happened). No new
audit table or subsystem was created (`INSERT INTO public.audit…` never appears in the data layer).

## 25. Immutability verification
Runtime-verified (behaviour unchanged): an `APPROVED` report version rejects a value write; a `FINAL` version
rejects a value write; a `FINAL`-attached value cannot be deleted; a `DRAFT` value can be deleted; no B1 DB
trigger was added (PQ-4 remains app-layer). The correction introduces no lifecycle bypass — the immutability
guards run before the (now working) SQL in both corrected methods.

---

## 26. B2 boundary verification — **PASS**
Runtime (clone): `evidence_line_items` does **not** exist; `calculation_snapshots.source_line_item_id` does
**not** exist; the data layer's executed SQL contains no `evidence_line_items`/`source_line_item_id`
identifier (static guard). No line-item addressability or backfill was added.

## 27. B3 boundary verification — **PASS**
No intensity table, denominator catalogue, intensity value or intensity calculation exists; the executed SQL
contains no intensity identifier. No E1 requirement/mapping content was seeded or invented.

## 28. B4 boundary verification — **PASS**
No narrative/commentary table, narrative overlay, frozen artefact or enhanced finalisation exists; the
executed SQL contains no narrative/commentary identifier. The correction changed no finalisation semantics.

## 29. Files created
1. `supabase/migrations/20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` (156 lines)
2. `backend/tests/integration/test_disclosure_b1_runtime.py` (15 runtime tests)
3. `backend/tests/unit/data/test_disclosure_sql_typing.py` (9 static guards)
4. `docs/cline/reports/CT-P8-B1-CORRECTION-20260912-015.md` (this report)

## 30. Files modified
1. `backend/data/disclosure.py` — F1 casts, F2 casts, F3 NULL-snapshot idempotency, F5 audit helper + six
   call sites, docstring/imports (an uncommitted B1 file: still untracked, so no *tracked* file was modified).
2. `backend/domain/disclosure.py` — the B1 audit-action vocabulary block (pure constants only).

**No other file was modified.** The 208 pre-existing tracked modifications are untouched.

## 31. Files intentionally untouched
`supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql` (byte-identical, 583 lines); all
historical migrations; `backend/tests/unit/domain/test_disclosure.py`;
`backend/tests/unit/data/test_disclosure_migration.py`; `backend/api/**` (no endpoint, no DI wiring — B1 API
exposure remains deferred); `backend/data/audit.py`, `backend/domain/audit.py`,
`backend/infra/audit_logger.py`, `backend/api/audit_helpers.py` (consumed, never modified);
`backend/tests/integration/conftest.py`; `report_versions`; `report_generation_queue`;
`calculation_snapshots`; `emissions_logs`; `manual_extraction_items`; `organization_files`; the
`p8_disclosure_*` helper functions and their ACLs (F7); all existing tables' grants/policies; the wider RLS
remediation; production and the dev/demo database.

## 32. Deviations
1. **F7 left unchanged** although B1 created the helpers — justified in §14 (the contract does not
   unambiguously require the revoke; general privilege hardening is out of scope).
2. **One extra cast beyond the literal F1 wording:** the F1 fix also added `::jsonb` to the
   characteristic-snapshot parameter, matching the established `data/audit.py` cast convention. Behaviour
   neutral; included so the previously never-executable statement cannot fail on a type/encoder mismatch.
3. **Both app-layer and DB-index corrections used for F3** (explicitly permitted by the task), documented in
   §10 with the reason (contract §25 states a *unique*-based guarantee that NULLs alone cannot provide).
4. **Clone-local dedupe during verification only:** the pre-fix reproduction left one duplicate row in the
   *disposable clone*, which made `CREATE UNIQUE INDEX` fail loudly. That single test-artefact row was deleted
   and the migration re-applied; the migration itself performs **no** deletion (documented precondition +
   commented recipe). No repository file or real database was affected.
5. The new runtime suite **skips** when B1 is not provisioned (environment-dependent schema), matching the
   suite's fail-safe convention; it therefore only executes where B1 (+ the correction) is applied.

---

## 33. Remaining findings (nonblocking)
| # | Finding | Severity | Status |
|---|---|---|---|
| R1 | F7 — `p8_disclosure_is_org_member` / `_admin` keep default `PUBLIC EXECUTE` (B1 created them; no unambiguous contract requirement to revoke) | P3 | Open, out of scope (documented) |
| R2 | `delete_disclosure_value` is not audited — the contract's §26 event table lists catalogue/reporting writes and value materialisation, not deletion. Auditing deletion would be a small new authorised item if the PO wants it | P3 | Observation |
| R3 | The original implementation tests could not have caught F1/F2/F3; the new runtime suite closes that gap, but nothing forces CI to provision a B1-bearing database, so that suite will *skip* in environments without B1 | P3 | Mitigated (skip-by-design; the privilege test fails loudly if the correction migration is missing) |
| R4 | Deployment precondition: applying `uq_dve_reference_nullsafe` to a database that already contains pre-fix duplicates fails loudly and requires the documented, explicitly-authorised dedupe first | P3 | Documented in the migration |

No P0/P1/P2 finding from V1 (F1–F5) remains open.

## 34. Git / worktree impact

| Item | Baseline | After correction |
|---|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` | **unchanged** |
| Branch | `main` | `main` |
| Staged | 0 | **0** |
| Modified (tracked) | 208 | **208 (unchanged; none is a B1 file)** |
| Untracked (porcelain) | 71 | **73** (+2 = correction migration, runtime integration test; the unit guard and this report sit inside already-collapsed untracked directories) |
| Migrations | 56 | **57** (+1) |

No reset/checkout/clean/stash/restore/rebase/amend. Pre-existing work preserved. The disposable clone
`b1v1_correction` was created for this task and **dropped** at the end; the `/tmp` harnesses, logs and dumps
created by this task were removed (unrelated pre-existing `/tmp/v1*.txt` files were left alone).

## 35. Production boundary confirmation
**Confirmed.** No production migration, schema change, RLS change, privilege change or deployment occurred.
No production/remote endpoint was contacted. The 34 outstanding production migrations remain a separate gate
and were not reconciled. The dev/demo database is unchanged (0 disclosure tables, 116 base tables).

## 36. Commit / push confirmation
**Confirmed: nothing was committed and nothing was pushed.** HEAD is unchanged and the git index is empty.

## 37. Final verdict

### `B1 CORRECTION COMPLETE — READY FOR V1 RE-VERIFICATION WITH NONBLOCKING FINDINGS`

| Dimension | Status |
|---|---|
| **IMPLEMENTED** | F1, F2, F3 (application + database halves), F4 and F5 corrected; F6 added; F7 investigated and intentionally not changed. |
| **TESTED** | B1 unit tests (34 existing + 9 new guards) and 15 new runtime integration tests pass; targeted regressions and the full `tests/unit/` suite pass (rc=0). |
| **RUNTIME VERIFIED** | Yes — in a disposable PostgreSQL 17.6 clone for F1 (both cases), F2, F3 (all four required cases), F4 (privilege matrix + RLS probes), F5 (audit rows), plus tenant isolation, immutability and the B2/B3/B4 boundary. |
| **INDEPENDENTLY VERIFIED** | **No** — that is the separate V1 re-verification gate; this report is the implementer's own evidence. |
| **PRODUCTION DEPLOYED** | **No.** |

**Why not a failure verdict:** every V1 P1/P2 finding this task was authorised to correct was reproduced,
corrected and re-verified at runtime, and no stop condition was met (no B1 redesign, no B2/B3/B4, no existing
table, no RLS remediation, no new audit architecture, no PQ change, no invented regulatory content, no
production access). The remaining items (R1–R4) are P3 observations.

*STOP — correction complete. V1 re-verification, B2, B3, B4 and Phase 8-X were **not** started; nothing was
committed or pushed; no production action was taken. The next decision belongs to the Product Owner.*
