# CT-P8-B1-IMPLEMENTATION-20260912-013

**Task ID:** `CT-P8-B1-IMPLEMENTATION-20260912-013`
**Title:** Phase 8 Batch B1 — Disclosure Model Foundation Implementation
**Date:** 2026-09-12 (start `2026-09-12T21:41:01+06:00`)
**Final verdict:** `B1 IMPLEMENTATION COMPLETE — READY FOR INDEPENDENT VERIFICATION`

> **Status discipline:** **IMPLEMENTED** and **TESTED** (implementation tests) here. **NOT independently
> verified** (gate V1 is separate). **NOT production deployed.** **Not** Phase-8-complete.

---

## 1. Task ID
`CT-P8-B1-IMPLEMENTATION-20260912-013`.

## 2. Authorisation basis
B1 implementation **authorised** by `docs/cline/reports/CT-P8-B1-PO-IMPLEMENTATION-AUTHORISATION-20260912-012.md`
(verdict: `B1 IMPLEMENTATION AUTHORISED — READY FOR B1 IMPLEMENTATION`), bounded by the B1 implementation
contract and ratified by `docs/architecture/CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`
(PQ-1…PQ-8 closed).

## 3. Governing documents
`CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md`; `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`;
`CT-P8-B1-PO-IMPLEMENTATION-AUTHORISATION-20260912-012.md`; the Disclosure Model decision record, design,
and G0 consolidation; existing migrations/backend patterns.

## 4. Pre-implementation repository baseline
HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c` · branch `main` (ahead 14) · staged 0 · modified 208
(all pre-existing, unrelated) · untracked 66 · migrations 55. No `disclosure_*` table existed anywhere.

## 5. Implementation scope
The **11-table B1 Disclosure Model Foundation** only, plus its pure domain model, data-layer boundary,
and implementation tests. Nothing else.

## 6. Exact 11 tables implemented
`disclosure_frameworks`, `disclosure_framework_versions`, `disclosure_requirement_versions`,
`disclosure_requirement_mappings`, `disclosure_report_purposes`, `disclosure_report_purpose_versions`,
`disclosure_purpose_requirements`, `disclosure_applicability_assessments`,
`disclosure_report_instance_binding`, `disclosure_values`, `disclosure_value_evidence`.
**Verified: exactly 11** (`CREATE TABLE IF NOT EXISTS public.disclosure_*` count = 11); **no 12th table**.

## 7. Migration created
`supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql` — **583 lines**, additive,
idempotent. Repository migration count moved **55 → 56**; **no existing migration was modified, renamed,
reordered or deleted**.

## 8. Schema implementation summary
- Global catalogue tables (7): no `organization_id`; `code`/version uniques; enumerated `CHECK`s.
- Organisation-scoped tables (4): `organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE`.
- PKs `uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4()`; `timestamptz … DEFAULT now()`.
- PK/FK/UNIQUE/CHECK implemented exactly per contract §9–§10; indexes per §11 (20 indexes incl.
  `uq_drm_current` partial unique and the FK indexes).
- `disclosure_values.value_status` `CHECK (value_status IN ('PENDING','RESOLVED','UNRESOLVED'))`;
  `effective_class` present + `CHECK` in the requirement-class set.
- `disclosure_requirement_versions` identifier-safety `CHECK (identifier_status = 'RESOLVED' OR official_identifier IS NULL)`.
- `disclosure_framework_versions` `CHECK (status <> 'ADOPTED_NOT_IN_FORCE' OR applicable_from IS NULL)`.
- Period tables: `reporting_period_start`/`_end` `date NOT NULL` + `CHECK (reporting_period_end >= reporting_period_start)`.

## 9. Reference seeds implemented
Idempotent (`ON CONFLICT (code) DO NOTHING`): **3 framework identities** (`GHG_PROTOCOL`, `UK_SECR`,
`ESRS_E1`) + **4 purpose identities** (`ANNUAL_CARBON`, `MANAGEMENT`, `UK_SECR`, `ESRS_E1_QUANT`).
**Not seeded (PQ-6):** framework-VERSION rows and all requirement/mapping content — deliberately left
empty with the reason documented in the migration header. **No invented versions, identifiers, thresholds,
deadlines, denominators or materiality values.**

---

## 10. Domain / data implementation
- **`backend/domain/disclosure.py`** (pure, no I/O): the B1 vocabularies, validators
  (`validate_*`), reference-seed identities, `DisclosureViolation`, and the ratified invariants
  `assert_value_status_is_materialisation_only`, `assert_value_status_independent`,
  `assert_identifier_safety`, `assert_not_in_force_has_no_applicable_from`, `assert_period_order`,
  `assert_periods_agree` (PQ-2), `is_immutable_report_version`/`assert_report_version_mutable` (PQ-4),
  `assert_same_organization` (cross-tenant).
- **`backend/data/disclosure.py`**: `DisclosureCatalogRepository` (catalogue read + idempotent seed) and
  `DisclosureRepository` (org-scoped applicability / instance-binding / values / value-evidence with the
  app-layer invariants). Reuses `AbstractRepository` (`data.base`), the service-role `asyncpg` pool and the
  existing row-mapper/paging idioms. **No new repository architecture, no new authorization framework, no
  new audit system, no calculation/report engine.**
- **API exposure deferred** as the contract requires (no endpoints added).

## 11. Authorization / tenant implementation
Organisation-scoped reads/writes are authorised **server-side** through the repository invariants:
`report_organization()` / `report_version_owner()` resolve the owner; `assert_same_organization` rejects a
mismatched `organization_id`; `create_instance_binding` verifies the report belongs to the org and enforces
the PQ-2 period agreement. The existing guard helpers (`require_org_member`/`require_org_admin`/
`ensure_org_access`) are reused unchanged for any future surface. **No weakening of the application-layer
boundary because production RLS is incomplete.**

## 12. RLS implementation limited to B1
Only the **new** tables are affected: RLS `ENABLE`d on all 11; `anon` revoked on all 11; global catalogues
→ authenticated `SELECT` only (no client write); `disclosure_applicability_assessments` → member read /
admin write; `disclosure_report_instance_binding` → member read/write; `disclosure_values` /
`disclosure_value_evidence` → member read only (system/service-role writes). A `SECURITY DEFINER` membership
helper avoids reintroducing the known `organization_members` recursion defect. **No existing policy, grant
or table was modified; the 97/104 RLS remediation was NOT attempted.** Policies use guarded
`DROP POLICY IF EXISTS` + `CREATE POLICY` (idempotent).

## 13. Audit implementation
The B1 tables are auditable through the **existing** append-only `audit_trail` + `AuditRepository`/taxonomy
(the repository layer is the write boundary; no new audit table, no secret/signed-URL content). Per contract
§26 the audited events are framework/version/requirement/mapping/purpose writes, applicability assessment,
instance binding, value materialisation and value→evidence creation. **No new audit mechanism introduced.**

## 14. Immutability implementation
`assert_report_version_mutable` is called in `upsert_disclosure_value` and `delete_disclosure_value` after
resolving the parent report-version `status`; `APPROVED`/`FINAL` raise `DisclosureViolation`. **Application/
service-layer enforcement (PQ-4); NO database trigger created.**

## 15. Idempotency implementation
`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, guarded `DROP POLICY IF EXISTS` + `CREATE POLICY`,
`ON CONFLICT DO NOTHING` seeds, and upsert-on-unique for mappings/values/evidence/bindings. Re-running the
migration or the seed creates no duplicates. **No destructive statement.**

## 16. Tests added
| File | Coverage |
|---|---|
| `backend/tests/unit/domain/test_disclosure.py` | Vocabularies; PQ-3 `value_status` (only PENDING/RESOLVED/UNRESOLVED; the 4 old values rejected; independence from `effective_class`); identifier safety; not-in-force; period order + PQ-2 agreement; PQ-4 immutability; cross-tenant rejection; identity-only seeds |
| `backend/tests/unit/data/test_disclosure_migration.py` | Exactly 11 tables; no B2/B3/B4 tables; no existing table ALTERed; no `source_line_item_id`; `value_status` CHECK; `effective_class`; value uniqueness; both period tables + order checks; `UNIQUE(report_id)`; consolidation vocabulary; identifier-safety CHECK; not-in-force CHECK; partial-unique current mapping; idempotency guards; RLS enabled + `anon` revoked for all 11; identity-only seeds |

## 17. Tests executed
`python -m pytest tests/unit/domain/test_disclosure.py tests/unit/data/test_disclosure_migration.py -q`
(run from `backend/` with the project venv).

## 18. Test results
**34 tests — all PASS (100%).** Zero failures, zero errors. Module imports verified
(`domain.disclosure`, `data.disclosure`).

## 19. Database migration execution result
**NOT executed.** No authorised dev/QA database session was available in this environment (and credentials
must not be read/printed), so the migration was **not** applied. The migration is verified **statically**
(structural tests) and is idempotent by construction. **No successful DB execution is claimed**, and no
fabricated execution result is reported. Applying it in dev/QA is a follow-up action (and remains the
prerequisite for the independent V1 gate).

---

## 20. Regression results
- **No existing file was modified** (`git diff` = the same 208 pre-existing entries; unchanged content).
- **Targeted regression:** `tests/unit/api/test_v3_report_lifecycle.py` + `tests/unit/api/test_v3_reports.py`
  → **all PASS** (report lifecycle S1/S3 intact).
- **`tests/unit/domain/`** → all PASS (includes the new disclosure tests).
- **Full `tests/unit/` run:** reached **~49% with 0 failures** before the 280 s cap; **no failures or errors
  observed** in the completed portion. The full suite was not exhausted within the cap (not a failure).
- No existing test was weakened.

## 21. Files created
1. `supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql` (B1 migration; 11 tables)
2. `backend/domain/disclosure.py` (pure domain model + invariants)
3. `backend/data/disclosure.py` (catalogue + org-scoped repositories)
4. `backend/tests/unit/domain/test_disclosure.py` (domain tests)
5. `backend/tests/unit/data/test_disclosure_migration.py` (migration structural tests)
6. `backend/tests/unit/data/__init__.py` (test package init)
7. `docs/cline/reports/CT-P8-B1-IMPLEMENTATION-20260912-013.md` (this report)

## 22. Files modified
**None.** Zero existing files were modified (no source, schema, migration, API, frontend, RLS or config file).
The 208 pre-existing working-tree modifications were **not** touched.

## 23. Files intentionally not modified
`docs/architecture/**` (contract, ratification, design, decision record, roadmap); the 55 pre-existing
migrations; `backend/api/dependencies.py`/`RepositoryBundle` (not wired in — B1 API exposure is deferred, so
no DI registration was needed); `calculation_snapshots`; `report_versions` schema; `report_generation_queue`;
legacy reporting; extraction; factor matching; billing; Phase 8-X; RLS on existing tables; all unrelated
working-tree changes.

## 24. B1/B2/B3/B4 boundary confirmation
- **B1 only** — 11 tables; no 12th.
- **B2 NOT implemented:** no `evidence_line_items`; no `source_line_item_id` column; no line-item backfill.
- **B3 NOT implemented:** no intensity tables/catalogue/values; no E1 requirement/mapping content.
- **B4 NOT implemented:** no narrative overlay, no management commentary, no finalisation/frozen artefacts.
Confirmed by the migration structural tests (`test_no_b2_b3_b4_tables`, `test_no_source_line_item_id_column`)
and by the absence of any such file in the change set.

## 25. Security / tenant verification performed
- Cross-tenant rejection tested (`assert_same_organization` equal/mismatch/None) and enforced in
  `upsert_disclosure_value`, `create_instance_binding`, `link_value_evidence`.
- App-layer immutability enforced and tested for `APPROVED`/`FINAL`.
- RLS enabled + `anon` revoked on all 11 new tables (statically verified).
- No secrets/signed URLs/storage objects stored in B1 tables; evidence **referenced, never copied**.

## 26. Known limitations / findings
- **Migration not DB-executed** here (no authorised DB session) — independent dev/QA application remains.
- **Framework-version rows are NOT seeded** (PQ-6 requires a PO-confirmed, authoritative-evidence list);
  the tables exist and are empty by design.
- **B1 tables are unpopulated** (disclosure values arrive only once the B3 projection layer exists).
- **RLS is defence-in-depth only**; the mandatory boundary is the application layer (the wider RLS baseline
  is a separate workstream and was untouched).
- The **`data/` test package** is new; no pre-existing `tests/unit/data/` existed.

## 27. Git / worktree impact

| Item | Before (`21:41:01`) | After |
|---|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (unchanged) |
| Branch | `main` (ahead 14) | `main` (ahead 14) |
| Staged | 0 | **0** |
| Modified (tracked, ` M`) | 208 | **208 (unchanged)** |
| Untracked (porcelain entries) | 66 | **71 (+5** = migration + 2 modules + 1 test + the new `tests/unit/data/` dir) |
| Migrations | 55 | **56 (+1)** |

**No tracked file was modified.** 208 pre-existing modifications preserved unchanged. No
reset/checkout/clean/stash/restore/rebase/amend. **No commit. No push.**

## 28. Confirmation no production deployment occurred
**Confirmed.** Nothing was deployed. No production migration was applied; no Supabase production state was
read or written; the 34 outstanding production migrations were **not** reconciled or touched.

## 29. Confirmation no commit / push occurred
**Confirmed.** HEAD is unchanged; nothing was staged, committed or pushed.

## 30. Final verdict

### `B1 IMPLEMENTATION COMPLETE — READY FOR INDEPENDENT VERIFICATION`

**Distinction:**
- **IMPLEMENTED** — the 11-table B1 foundation, domain model and data layer (additive; zero existing tables modified).
- **TESTED** — 34 implementation tests pass; targeted regression passes; full unit run showed 0 failures to ~49%.
- **INDEPENDENTLY VERIFIED** — **NOT** (gate V1 is a separate task).
- **PRODUCTION DEPLOYED** — **NOT** (dev/QA application and the migration-reconciliation gate remain).

*STOP — B1 implementation and implementation-level testing complete. B2/B3/B4/V1/Phase 8-X NOT begun; no
migration applied to production; nothing committed or pushed.*


