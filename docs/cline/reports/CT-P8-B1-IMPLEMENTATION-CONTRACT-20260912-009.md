# CT-P8-B1-IMPLEMENTATION-CONTRACT-20260912-009

**Task ID:** `CT-P8-B1-IMPLEMENTATION-CONTRACT-20260912-009`
**Title:** Phase 8 Reporting — B1 Disclosure Model Foundation Implementation Contract
**Date:** 2026-09-12
**Type:** READ-ONLY architecture / implementation-contract — **no implementation**
**Verdict:** `B1 IMPLEMENTATION CONTRACT COMPLETE — READY FOR PO REVIEW`

---

## 1. Repository / branch
`carbon_tally` · branch **`main`** · working tree with substantial pre-existing modifications (preserved).

## 2. Starting HEAD
`19e4f01c176eee5870f3c15038b6e7c68b23281c` — `19e4f01 feat: implement Phase 8 report lifecycle foundation`.

## 3. Ending HEAD
`19e4f01c176eee5870f3c15038b6e7c68b23281c` — **unchanged** (no commit).

## 4. Initial Git status summary (before)
| Item | Value |
|---|---|
| Branch | `main` (ahead 14 of `origin/main`) |
| Staged | 0 |
| Modified (tracked) | 208 |
| Untracked (porcelain entries) | 64 |
| Recorded | `2026-09-12T20:54:49+06:00` |

## 5. Final Git status summary (after)
| Item | Value |
|---|---|
| Branch | `main` (ahead 14) |
| Staged | **0** |
| Modified (tracked) | **208 (unchanged)** |
| Untracked (porcelain entries) | **65 (+1** = the new `docs/architecture/…B1_IMPLEMENTATION_CONTRACT…md`; the report sits inside the already-untracked `docs/cline/reports/`) |
| Recorded | task end |

**208 pre-existing modifications preserved unchanged. No reset / checkout / clean / stash / restore /
rebase / amend. No unrelated file altered. No commit. No push.**

## 6. Files created / modified
**Created (2):**
1. `docs/architecture/CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md` (the B1 contract)
2. `docs/cline/reports/CT-P8-B1-IMPLEMENTATION-CONTRACT-20260912-009.md` (this report)

**Modified: none.** No other file was created, modified, moved or deleted.

## 7. Confirmation that no source/schema/migration/API/frontend/RLS/production change was made
**Confirmed.** No application source, database schema, migration, API route, frontend code, RLS policy,
grant, configuration or production state was created or modified. **No migration was created or run.**
Nothing was applied to Supabase. No `evidence_line_items` / `source_line_item_id` was created. No
extraction/factor/calculation/report/narrative change. The change set is **two Markdown documents**.

## 8. Documents inspected
The D1–D17 ratification; the Disclosure Model design (esp. §§6–9, 11, 13, 18, 19, 20, 22); the Decision
Record (20 decisions + G0-B + `DM-7` refinement); the comprehensive readiness assessment (§20 batch plan);
the line-item and emission-factor forensic reports; the G0 governance consolidation report; the RLS
production baseline; the Master Roadmap (Phase 8 wording).

## 9. Repository areas inspected
`supabase/migrations/**` (55 files: init schema, `20260807020000_add_calculation_snapshots.sql`,
`20260823010000_d33_evidence_traceability.sql`, `20260831030000_tenant_org_id_not_null.sql`,
`20260913000000_p8_report_lifecycle_status.sql`, RLS/GRANT statements across migrations);
`backend/api/v3_reports.py`, `backend/domain/report_lifecycle.py`, `backend/engines/report_generation.py`,
`backend/engines/calculation.py`, `backend/services/automatic_extraction.py`,
`backend/services/extraction_suggestions.py`, `backend/services/ai_document_extraction.py`,
`backend/domain/evidence.py`, `backend/data/emission_factors.py`, `backend/core/units.py`; key tables
(`organizations`, `report_generation_queue`, `report_versions`, `report_templates`, `calculation_snapshots`,
`manual_extraction_items`, `organization_files`, `audit_trail`, `activity_categories`).

## 10. Findings
1. **[CONFIRMED]** **No `disclosure_*` table exists anywhere** in the repository — the Disclosure Model is entirely unimplemented.
2. **[CONFIRMED]** `calculation_snapshots` is append-only/immutable with `content_hash`, `request_id`; D33 added `source_item_id`/`source_file`/`source_page` (FK `SET NULL`) — the exact pattern B2 will mirror.
3. **[CONFIRMED]** The report spine is `report_generation_queue` (instance) → `report_versions` (version, `UNIQUE(report_id, version_number)`); **`report_versions.report_id` has no FK** (pre-existing).
4. **[CONFIRMED]** `report_generation_queue.report_type` is `NOT NULL` with one supported value (`annual`) — `purpose_code` must therefore be a **separate** disclosure-layer concept (`DM-2`).
5. **[CONFIRMED]** `organizations` already carries the applicability characteristics (size, listing, structure, country, FYE, standards, `secr_enabled`, `esrs_enabled`, …) — no new columns needed for `characteristic_snapshot`.
6. **[CONFIRMED]** RLS is **not currently a reliable boundary** (97/104 production tables disabled; `anon` `GRANT ALL`); **21 applied / 34 outstanding** migrations, including the P8 lifecycle migration.
7. **[CONFIRMED]** Conventions: `id UUID PK DEFAULT extensions.uuid_generate_v4()`; `organization_id … ENUM REFERENCES organizations(id) ON DELETE CASCADE`; `TIMESTAMPTZ DEFAULT NOW()`; `created_by`/`updated_by`.
8. **[UNRESOLVED — recorded]** The design §22.1 MVP list (14 tables incl. `evidence_line_items` + intensity) conflicts with the roadmap §20 batch split (B2/B3). This is a **delivery-sequencing** conflict, not semantic.

---

## 11. Proposed B1 contract summary
**B1 = 11 new tables, zero modified objects.** Framework/version catalogue (`disclosure_frameworks`,
`disclosure_framework_versions`); requirement model (`disclosure_requirement_versions`,
`disclosure_requirement_mappings`); purpose model (`disclosure_report_purposes`,
`disclosure_report_purpose_versions`, `disclosure_purpose_requirements`); reporting context
(`disclosure_report_instance_binding`, `disclosure_applicability_assessments`); value layer
(`disclosure_values`, `disclosure_value_evidence`). Every column, type, nullability, default, key,
constraint, index and FK is specified exactly in the contract (§§9–12). Global catalogues carry no
`organization_id`; organisation-scoped tables carry `organization_id NOT NULL`. Enumerations are
`CHECK (col IN (…))`. Additive, idempotent, one migration.

## 12. B1/B2 boundary
**[PROPOSED] B1 needs no placeholder.** The existing chain (`calculation_snapshots` → D33 → items/files)
already carries document/page provenance; `disclosure_value_evidence` references it. **B2** later creates
`evidence_line_items`, adds `calculation_snapshots.source_line_item_id` (additive FK `SET NULL`) and may
add an additive `source_line_item_id` to `disclosure_value_evidence`. Line-item granularity is **never
manufactured**; flat PDF/IMAGE records are not backfilled into false line items.

## 13. Migration findings
- **[CONFIRMED]** 55 migrations in repo; **21 applied / 34 outstanding** in production.
- **[PROPOSED]** B1 = **one** fresh additive migration `20260914000000_p8_b1_disclosure_model_foundation.sql`,
  idempotent (`IF NOT EXISTS` + `pg_constraint` guards, D33 pattern).
- **[CONFIRMED]** B1 depends only on objects that exist at the 21-migration level → **applicable in dev/QA now**.
- **[UNRESOLVED]** Production application ahead of the backlog is a PO/deployment decision (**PQ-5**); the
  backlog is a **P0 deployment** concern, not a design blocker. **No existing migration is modified.**

## 14. RLS / security findings
- **[CONFIRMED]** RLS is not a reliable boundary today (97/104 disabled; `anon` `GRANT ALL`).
- **[PROPOSED]** B1 declares RLS **intent** (global catalogues: authenticated read, service-role write; org
  tables: org-scoped read/write with service-role bypass) and grants **no `anon`** access on its **new**
  tables. **App-layer authorization is the enforced boundary** (reuse `require_org_member`/`require_org_admin`/
  `ensure_org_access`). B1 does **not** perform broader RLS remediation and modifies **no** existing policy
  or grant. Cross-tenant integrity is an app-layer + verification invariant (the report FK chain carries no
  composite tenant key).

## 15. Historical / backfill findings
- **[CONFIRMED]** `DM-7` (with the Gate 0 refinement) governs: deterministic/idempotent backfill only where
  `line_items[]` already exists; flat historical PDF/IMAGE cannot be deterministically backfilled; re-parsing
  requires a separately authorised and verified task; no silent re-extraction; no manufactured line provenance.
- **[PROPOSED]** **B1 performs no historical backfill.** Class 2 work (`evidence_line_items` population,
  `source_line_item_id`) belongs to **B2**. Class 3 (re-parsing flat PDF/IMAGE, rewriting rows to manufacture
  provenance) is **prohibited**.

## 16. Open PO decisions
**PQ-1** intensity placement (B1 vs B3 — recommend **B3**); **PQ-2** explicit reporting-period placement
(recommend applicability assessment + instance binding); **PQ-3** confirm `value_status` vocabulary;
**PQ-4** immutability enforcement (app-layer vs trigger); **PQ-5** production migration strategy for the
34-outstanding backlog; **PQ-6** reference-seed scope (frameworks/versions/purposes only, in B1);
**PQ-7** re-affirm `E1-COV` CONDITIONAL (E1 seeding stays gated — **not** a B1 blocker);
**PQ-8** confirm the roadmap as the delivery schedule for the design-MVP set.

## 17. Blockers
**No B1 blocker.** The contract could be written without inventing a material architecture decision:
table ownership, tenant boundary, requirement identity, purpose semantics, applicability states and the
B1/B2 boundary are all resolvable from the authoritative documents + repository. The only blockers
identified are **deployment**-level (34-outstanding migration backlog; RLS baseline) and are recorded as
**PQ-5** / separate workstreams — they do **not** prevent B1's design or its dev/QA application.

## 18. Implementation-readiness verdict
The contract is **complete and implementation-ready for PO review**. B1 implementation remains **NOT
AUTHORISED** by this task.

---

## Final verdict

### `B1 IMPLEMENTATION CONTRACT COMPLETE — READY FOR PO REVIEW`

*STOP — read-only contract complete. No implementation begun; no B1/B2/P1/P2/Phase 8-X started; no
implementation prompt created; nothing committed or pushed.*

