# CarbonTally — WS4 Gate 4 Remediation — F1/F2 — Bounded Implementation + Regression

- **Workstream:** WS4 Gate 4 remediation (bounded implementation + regression)
- **Report date:** 4 September 2026
- **Repository Git SHA (HEAD):** `1639121` (no commit/push performed)
- **Verdict:** **REMEDIATION COMPLETE**
- **Scope note:** This is a remediation task only. The full Gate 4 matrix was **not**
  re-run; Gate 4 will be re-executed separately after PO review of this report.

---

## 1. Findings addressed

| Finding | Status | Remediation summary |
|---|---|---|
| **F1 — Human/entity actor attribution gap** (calculation; internal-origin validation; mapping internal + PE) | **ADDRESSED** | Successful map/validate/calculate actions now write canonical append-only audit events carrying the authenticated actor (CarbonTally internal staff user or PE staff user + entity context); successful calculations additionally persist the actual actor on the immutable calculation snapshot (`calculation_snapshots.performed_by`) — the organisation id is no longer the only actor identity on calculation evidence. |
| **F2 — PE-origin snapshot traceability gap** (`source_item_id = NULL` on the PE/entity-calculate path) | **ADDRESSED** | The entity-calculate handler now passes `source_item_id = item.id` (and the acting user) into the calculation request for both single-line and multi-line paths; the `/api/v3/pe` calculate delegate was also corrected to resolve the shared calculation engine through FastAPI DI so the canonical PE route actually executes. |

F3 (D38 batch-default semantics) and F4 (qc_specialist `can_process`) were **not**
modified — see §12.

---

## 2. Existing implementation analysis

Inspected before any change (per the required inspect-first protocol):

- `backend/api/v3_operations.py` — internal-origin map/validate/calculate
  (`/api/v3/ops/items/{id}/map|validate|calculate`) and entity/PE-origin handlers
  (`/api/v3/ops/entities/{id}/extraction/items/{id}/map|calculate`); batch/assignment
  audit helper `_record_batch_assignment_audit`; the `review:submitted` pattern
  (`submit_internal_review`).
- `backend/api/v3_pe.py` — PE validate/review/QC already record canonical audit
  events with `actor = pe.user_id` and `entity_id`/`pe_role` in `changed_fields`
  (`pe_validate:*`, `pe_review:*`, `pe_qc:*`). PE map/calculate delegated to the
  shared ops handlers without any audit, and `/pe/.../calculate` invoked the shared
  handler without resolving its `Depends(get_calculation_engine)` parameter.
- `backend/engines/calculation.py` — `CalculationRequest`/`CalculationEngine`;
  `calculate()` hard-coded `calculated_by = request.organization_id` when persisting
  the snapshot (root cause of the calculation-actor part of F1).
- `backend/data/emissions_logs.py` — `save_snapshot()` (immutable snapshot insert,
  ADR-5 append-only) with no actor parameter beyond the org-valued `calculated_by`.
- `backend/data/audit.py`, `domain/audit.py`, `infra/audit_logger.py` — the existing
  append-only audit model (`performed_by`/`metadata.actor` on `audit_trail`) already
  carries human actor attribution and is the established mechanism for
  assign/validate/review/QC events.
- `manual_extraction_items` actor columns (`extracted_by`, `qc_by`,
  `pe_reviewed_by`, `pe_qc_by`, `customer_reviewed_by`) — the item-level actor model
  used for the stages that have dedicated columns.
- Schema/migrations: `20260807020000_add_calculation_snapshots.sql`,
  `20260823010000_d33_evidence_traceability.sql` (adds `source_item_id` FK),
  `20260902020000_v1_2_dual_origin_workflow.sql`, `20260902030000_phase5_work_item_assignments.sql`.
- Gate 4 acceptance report (§14 F1/F2 evidence) and the current database
  (`calculation_snapshots.calculated_by` holds the organisation id; PE-origin
  snapshot had `source_item_id = NULL`).

**Canonical mechanism chosen (no new provenance system):** extend the existing
append-only audit contract (the pattern used by `work_item:*`, `pe_validate:*`,
`review:submitted`, `ct_qc:approved`) for map/validate/calculate, and extend the
immutable snapshot row with one additive actor column for the calculation evidence
itself.

---

## 3. Root cause of F1

1. **Calculation:** `CalculationEngine.calculate()` persisted every snapshot with
   `calculated_by = request.organization_id` — the request contract had no actor
   field and the API layer passed none, so the only actor-ish value ever stored was
   the organisation id. No calculate audit event existed in the API layer.
2. **Internal-origin validation:** the ops `/validate` endpoint transitioned the
   item and resolved issues but recorded no actor evidence (contrast: the PE
   `/validate` route records `pe_validate:*` with the PE actor).
3. **Mapping (internal + PE):** the ops `/map` and entity `/map` handlers persisted
   the mapping output but no actor evidence.

---

## 4. Root cause of F2

`entity_extraction_calculate()` (used by both the ops-entity route and the PE
application) built its `CalculationRequest` without `source_item_id`, unlike the
internal `calculate_item()` path which already set `source_item_id = item.id`. The
engine persisted exactly what the request carried, so PE-origin snapshots were
written with `source_item_id = NULL`, terminating the item → snapshot chain. A
secondary defect kept the canonical `/api/v3/pe/items/{id}/calculate` route from
running at all: it delegated to the shared ops handler without supplying its
`Depends(get_calculation_engine)` dependency, so the handler received the raw
`Depends` marker (the known “PE calculate 500”).

---

## 5. Exact files changed

| File | Change |
|---|---|
| `backend/engines/calculation.py` | `CalculationRequest` gains `performed_by: Optional[str]`; `calculate()` passes `performed_by` to `save_snapshot`; engine audit actor prefers `request.performed_by`, falling back to `calculation_engine` for automatic runs; `from_match_result` threads `performed_by` through. |
| `backend/data/emissions_logs.py` | `save_snapshot()` accepts `performed_by` and persists it to `calculation_snapshots.performed_by`; `_SNAPSHOT_COLUMNS` includes the column. |
| `backend/api/v3_operations.py` | New shared `_record_item_action_audit()` helper (item entity, actor, origin context). Internal `/map` records `ops_map:applied`; internal `/validate` records `ops_validate:validated`/`ops_validate:blocked`; internal `/calculate` records `ops_calculate:applied` (incl. `snapshot_id`) and threads `performed_by` (single + multi-line). Entity `/map` records `pe_map:applied`; entity `/calculate` records `pe_calculate:applied` (incl. `snapshot_id`, `entity_id`), threads `performed_by`, and **sets `source_item_id = item.id` (F2)** on single-line and multi-line requests. |
| `backend/api/v3_pe.py` | `/pe/items/{id}/map` and `/pe/items/{id}/calculate` pass the request `AuditContext` through to the shared handlers; `/pe/items/{id}/calculate` now also injects and passes the shared `CalculationEngine` (fixes the unresolved-`Depends` 500 so the canonical PE calculate path executes — required to exercise F2 on the PE surface). |
| `supabase/migrations/20260905000000_gate4_actor_provenance.sql` | **New additive migration** — adds nullable `calculation_snapshots.performed_by uuid` (+ index, comment; FK to `auth.users` `ON DELETE SET NULL` guarded on `auth` schema existence so the dedicated integration-test database, a schema-only mirror, still applies). |
| `backend/tests/unit/api/fakes.py` | `MemoryLogs.save_snapshot()` accepts and records `performed_by` (`_snapshot_actors`) so API tests can assert snapshot actor semantics. |
| `backend/tests/unit/engines/test_calculation.py` | `_MemorySink` accepts/records `performed_by`. |
| `backend/tests/unit/api/test_gate4_remediation_actor_provenance.py` | **New** — API-level F1/F2 regression tests (2 tests). |
| `backend/tests/integration/test_gate4_remediation_actor_provenance.py` | **New** — real-PostgreSQL engine/repository persistence test (1 test). |

No other repository files were changed by this remediation.

---

## 6. Exact migrations added

- `supabase/migrations/20260905000000_gate4_actor_provenance.sql` (migration #47 by
  filename ordering). Additive + idempotent (`ADD COLUMN IF NOT EXISTS`); no data
  rewrite, no column semantic change, no RLS change. Applied to the local main
  database and to the dedicated `carbontally_test` database for this run.

---

## 7. Provenance model used

- **Audit events (actor-attribution carrier):** each successful map / internal
  validate / calculate now writes one append-only `audit_trail` row exactly as the
  established review/QC/assign events do — `table_name = manual_extraction_item`,
  `record_id = item id`, `performed_by`/`metadata.actor = authenticated user id`,
  `changes` carries `status_from/status_to`, immutable `processing_origin` /
  `processing_entity_id`, and (where relevant) `entity_id`, `pe_role`-style context
  and `snapshot_id`.
- **Snapshot actor (calculation evidence):** the immutable snapshot row carries
  `performed_by` = the authenticated human/PE actor that requested the calculation;
  `calculated_by` retains its historical organisation-context semantic. `NULL`
  `performed_by` = historical rows or automatic-pipeline runs (machine provenance
  out of scope, §13).
- **Distinguishability:** a CarbonTally internal actor is a staff user whose
  profile has no entity; a PE actor is the PE staff user, additionally identified by
  `entity_id` in the audit event and the item’s immutable `processing_origin` /
  `processing_entity_id` captured on the same event. Item columns remain the actor
  carrier where they already exist (`extracted_by`, `qc_by`, …); they were not
  duplicated.
- PE map/calculate events are recorded once per successful action regardless of
  whether the request arrived via the ops-entity route or the canonical `/pe` route,
  because both routes share the same handler/audit point.

---

## 8. Tests added / changed

New tests:
- `backend/tests/unit/api/test_gate4_remediation_actor_provenance.py`
  - `test_internal_map_validate_calculate_persist_actor` — internal-origin flow:
    asserts exactly one `ops_map:applied` (actor `u-op`), one
    `ops_validate:validated` (actor `u-rev`), one `ops_calculate:applied` (actor
    `u-op`, with `snapshot_id`); snapshot actor = `u-op` (never `org-a`); snapshot
    `source_item_id` = item id (internal link intact).
  - `test_pe_map_calculate_persist_actor_and_link_snapshot` — PE-origin flow via
    the ops-entity (PE) surface: exactly one `pe_map:applied` (actor `u-ent`,
    `entity_id = entity-1`), one `pe_calculate:applied` (actor `u-ent`, `entity_id`,
    `snapshot_id`); snapshot actor = `u-ent` (never `org-a`); snapshot
    `source_item_id` = item id (F2).
- `backend/tests/integration/test_gate4_remediation_actor_provenance.py`
  - `test_engine_persists_actor_and_source_item_link` (real PostgreSQL, dedicated
    `carbontally_test` DB): engine-created snapshot row has `performed_by` = actor
    uuid, `performed_by != organisation id`, `source_item_id` = item id, result
    deterministic (18.4 kg CO₂e for 100 kWh × 0.184); automatic run without an
    actor keeps `performed_by = NULL`. The additive migration file is applied
    idempotently at module scope so the suite is self-contained.

Changed (compatibility only):
- `backend/tests/unit/api/fakes.py` (`MemoryLogs.save_snapshot`) and
  `backend/tests/unit/engines/test_calculation.py` (`_MemorySink.save_snapshot`)
  accept the new `performed_by` keyword and record it for assertions. No existing
  assertion was weakened.

---

## 9. Test results

| Suite / command | Result |
|---|---|
| New API regression file (`tests/unit/api/test_gate4_remediation_actor_provenance.py`) | **2 passed** |
| New integration file (`tests/integration/test_gate4_remediation_actor_provenance.py`, real PostgreSQL) | **1 passed** |
| Focused regression set — engines + automatic-processing service + ops/entity API suites incl. the new file | **321 passed, 0 failed** |
| Entire backend unit suite (`tests/unit`) | **All passed (0 failed)** |
| Application boot / route registration (create_app import + relevant route list incl. `/api/v3/pe/items/{id}/calculate`) | **OK** |
| Full `tests/integration` directory run | New remediation test passed; the suite reports 15 failures in **pre-existing unrelated modules** (`test_consultants`, `test_customer_admin`, `test_infra`, `test_reports`, `test_report_versions`, `test_v3m1_v3m2_processing_entities` baseline, `test_v3m3_customer_factors` RLS) caused by stale dedicated-test-DB schema/signature drift that predates this remediation — none touch calculation, audit, snapshots, ops/PE provenance, D38 or the files changed here. |

---

## 10. Database baseline before / after

| Metric | Task baseline | After remediation (main app DB) |
|---|---|---|
| emission_factors | 7,049 | 7,049 (unchanged) |
| organizations | 975 | 975 (unchanged) |
| manual_extraction_items | 260 | 260 (unchanged) |
| manual_extraction_batches | 56 | 56 (unchanged) |
| work_item_assignments | 0 | 0 (unchanged) |
| conversations | 34 | 34 (unchanged) |
| messages | 52 | 52 (unchanged) |
| conversation_participants | 62 | 62 (unchanged) |
| notifications | 0 | 0 (unchanged; removed one orphaned notification residue left by the earlier Gate-4 fixture that referenced the since-deleted Gate-4 item) |
| migrations | 46 | 47 files (new additive migration applied; schema column verified present in main + test DB) |

No demo/investor rows were created, mutated, or deleted by the remediation. All
integration/unit fixtures were cleaned; the only schema change is the additive
nullable `performed_by` column.

---

## 11. Security / invariant regression results

- Full backend **unit** suite green, including the existing authorization and
  provenance suites: `test_v3_operations.py`, `test_v3_entity_extraction.py`
  (PE isolation, internal/entity separation), `test_processing_origin_qc.py`,
  `test_v3_work_item_effective_assignment.py`, engine determinism tests and the
  audit-logger tests.
- New tests re-exercise the real guards: internal staff only for ops map/validate/
  calculate; PE staff only for entity-scoped work (ops-entity guard + actor
  recorded with `entity_id`); reviewer-only internal validation.
- Processing-origin immutability, effective assignment, D38 ledger, D39/D40 and RLS
  behaviour are untouched by the changes (no DDL on those objects; audit writes are
  append-only through the existing repository).
- Negative/authorization checks (PE↔internal separation, CT-QC separation,
  customer boundary) all remain covered by the unchanged existing unit suites that
  passed.
- No RLS policy was added/removed/changed. The only security-relevant schema
  addition is a nullable actor reference on append-only snapshots.

---

## 12. Confirmation — F3/F4 were NOT modified

- **F3 (D38 batch-default semantics):** no change. `work_item_assignments`, the
  single-open invariant, batch default, and batch-vs-item assignment architecture
  are untouched.
- **F4 (qc_specialist permissions):** no change. `qc_specialist` retains
  `can_process`; no staff-role row or permission was modified.

---

## 13. Confirmation — machine/provider/model provenance remains OUT OF SCOPE

This remediation records **human/PE actor attribution only**. Automatic-pipeline
calculations (no authenticated human caller) persist `performed_by = NULL` and the
engine audit falls back to the `calculation_engine` label, exactly as before. No
machine/provider/model/version provenance columns, fields or events were added.

---

## 14. Confirmation — no unrelated architecture was changed

- No new table, no duplicate provenance mechanism, no processing-origin change, no
  D38/D39/D40 change, no RLS change, no workflow-stage reordering, no UI change.
- The two narrow behavioural corrections beyond pure audit addition are both
  required by F1/F2: (1) `entity_extraction_calculate` now links `source_item_id`
  (F2) and threads the actor (F1); (2) the canonical `/pe` calculate delegate now
  resolves and passes the shared `CalculationEngine` through FastAPI DI — without
  this, the PE-origin calculate path F2 targets cannot execute at all (pre-existing
  unresolved-`Depends` defect documented in the Gate-4 report §16.3).
- Engine/domain changes are additive optional request fields with `None` defaults,
  preserving existing callers and automatic-pipeline behaviour.

---

## 15. Remaining limitations

1. Historical snapshots (created before this migration) keep `performed_by = NULL`;
   they are immutable by design and their org-valued `calculated_by` provenance is
   preserved. Only new calculations capture the human actor on the snapshot.
2. Item-level actor columns for map/validate/calculate were not added; attribution
   for those stages is carried by the canonical audit events (the same mechanism
   used for review/QC/assign), keeping the change minimal and consistent.
3. The dedicated integration-test database (`carbontally_test`) is a schema-only
   mirror without the `auth` schema, so the migration’s `auth.users` FK is guarded
   (created only where `auth.users` exists). Production/authoritative databases
   receive the FK.
4. The full `tests/integration` directory contains pre-existing failures in
   unrelated modules caused by stale test-DB schema drift; those were not part of
   this remediation and are recorded for a separate test-infrastructure item.
5. This remediation was verified through unit/API (real authorization + real
   engines over fakes), real-PostgreSQL engine/repository integration, and app-boot
   checks. The complete Gate 4 human-provenance matrix will be re-executed
   separately after PO review, per the task instructions.

---

## FINAL VERDICT

**REMEDIATION COMPLETE**

F1 (calculation / internal-validation / internal+PE mapping actor attribution) and
F2 (PE-origin snapshot `source_item_id` linkage) are implemented with the smallest
architecture-consistent change: additive snapshot actor column + canonical
append-only audit events reusing the established actor model. Focused regression
tests (unit/API + real-DB integration) pass, the baseline is restored exactly, and
F3/F4 plus all unrelated architecture remain untouched. Gate 4 has **not** been
re-passed and will be re-executed separately after PO review.
