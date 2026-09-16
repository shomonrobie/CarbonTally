# CT-P8-B2-PO-IMPLEMENTATION-AUTHORISATION-20260913-019

**1. Task identity:** `CT-P8-B2-PO-IMPLEMENTATION-AUTHORISATION-20260913-019` — **re-run** (fresh gate) after the
bounded documentation correction `CT-P8-B2-AUTHORISATION-CONTRACT-CORRECTION-20260913-021`.

**2. Task type:** PO IMPLEMENTATION AUTHORISATION GATE ONLY — bounded readiness verification. **Nothing
implemented.** The only file written by this task is this report.

**Re-run context:** the first execution of this gate returned the **blocked** verdict (contract inconsistency) on
one material finding (**F-019-1**: contract §20.3's "New objects present" expectation under-counted the new
indexes and used ambiguous FK/policy counts). Task 021 corrected the contract and report 017. This report
re-verifies the whole gate against the **corrected** governance chain.

**Verdict:** `B2 IMPLEMENTATION AUTHORISATION COMPLETE — B2 IMPLEMENTATION MAY PROCEED` (§20)

**Date:** 2026-09-13 · **Batch:** Phase 8 Reporting / Disclosure — B2 Evidence / Line-Item Addressability

---

## 3. Authoritative documents inspected

| # | Document | Role | Inspected |
|---|---|---|---|
| A1 | `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` (1,686 lines, §1–§28; mtime 11:53, 130,989 bytes) | implementation contract under verification (post-correction) | in full via targeted reads of §1, §3, §4, §5, §6, §6.1, §7, §8, §9, §10, §11, §12, §13, §14, §15, §16, §17, §18, §19, §20, §21, §22, §23, §24, §25, §26, §27, §28 |
| A2 | `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md` (364 lines, §1–§11; mtime 10:58) | authoritative PO decision record | decisions + boundary sections |
| A3 | `docs/cline/reports/CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017.md` (392 lines; mtime 11:55) | contract task report (figures corrected by task 021) | §3, §8, §9, §10, §12, §13, §14, §16, §18 |
| A4 | `docs/cline/reports/CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018.md` (193 lines; mtime 10:59) | ratification task report | in full |
| A5 | `docs/cline/reports/CT-P8-B2-AUTHORISATION-CONTRACT-CORRECTION-20260913-021.md` (269 lines; mtime 11:58) | the correction of F-019-1 | in full |
| S1 | `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` | `DM-7`, §10 honesty invariant | §6, §10 |
| S2 | `docs/architecture/CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md` | batch plan, gates | §15, §16, §20–§22, §29 |
| S3 | `docs/architecture/CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md` | B1 boundary + forward note | §6, §25, line 413 |
| S4 | `docs/cline/reports/CT-P8-B1-{IMPLEMENTATION-013, V1-INDEPENDENT-VERIFICATION-014, CORRECTION-015, V1R-INDEPENDENT-RE-VERIFICATION-016}.md` | B1 closure chain (B1 CLOSED; 11 tables; privilege posture; V1R clone method) | cited statements |
| S5 | `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` | P1 forensics (8→1) | §1, §4, §11, §12, §15–§20 |
| S6 | `docs/cline/reports/CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md` | P2/EF-E forensics | header + findings |
| S7 | `docs/architecture/CARBONTALLY_PHASE8_P1_PDF_IMAGE_EXTRACTION_REMEDIATION_CONTRACT_20260913.md` (889 lines, 10:59, independent workstream) | separate P1 artefact (not B2) | §0, §1, §6, §8, §9, §11, §13 |
| C1 | `supabase/migrations/20260914000000_p8_b1_*.sql`, `…20260915000000_p8_b1_correction_*.sql` | B1 migrations (must remain untouched) | sha256 + mtime recorded (§4) |
| C2 | `backend/tests/integration/{conftest.py, test_disclosure_b1_runtime.py}`, `backend/tests/unit/data/test_disclosure_{migration,sql_typing}.py` | B1 test scope / F-B2-13 | cited assertions |
| C3 | Read-only live introspection (`information_schema`, `pg_constraint`, `pg_policies`, `pg_database`) | environment status | §17 |

No new forensic investigation was performed; code citations were re-verified only as the anchors the contract
already records.

## 4. Baseline Git / worktree state (recorded before analysis)

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (`feat: implement Phase 8 report lifecycle foundation`) |
| Staged changes | 0 |
| Tracked modifications | 208 (pre-existing, unrelated) |
| Untracked (normal / all listings) | 76 / 797 |
| Migrations on disk | 57 — newest `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` |
| B2 migration files present | **none** (`ls supabase/migrations \| grep 20260916` → 0) |
| Worktree operations this task | **none** (no reset / clean / stash / checkout / stage / commit / push); the gate report at the mandated path was rewritten as the sole output |
| Governance-chain mtimes | contract 11:53:46 · report 017 11:55:34 · correction report 021 11:58:17 · ratification record 10:58:19 · report 018 10:59:13 |

**B1 migration integrity baseline (they are untracked in git, so no VCS baseline exists — V1 F6/V1R precedent):**

```
7cf72bcdfb2f21b45a07cae80451e3863444d58258a53684cc5bc05711b545a8  …_20260914000000_p8_b1_disclosure_model_foundation.sql
702faf2224c9fd75ab48958ccbe0f20505ca5b22cd4af77f878889fe9d66bdf4  …_20260915000000_p8_b1_correction_…_.sql
```

These hashes are **identical** to those recorded by the previous gate run (before the task-021 documentation
corrections), which is direct evidence that the B2 governance tasks have not touched the B1 migrations.

**Concurrent work detected (not B2, no conflict):** the newest non-B2 additions to the worktree are the
independent P1 workstream artefacts created at 10:59:47 today (see §8). No new file has appeared since
11:58:17.

---

## 5. Contract completeness verification

| Required item | Where specified | Status |
|---|---|---|
| Exact B2 schema (new table) | §7.1 `CREATE TABLE IF NOT EXISTS public.evidence_line_items` (L295–L321) | **specified** |
| Exact table/column names | §7.1 — 14 columns: `id`, `organization_id`, `source_item_id`, `source_file_id`, `line_number`, `source_page`, `row_reference`, `raw_description`, `raw_quantity`, `raw_unit`, `payload_hash`, `extraction_method`, `materialisation_kind`, `created_at` | **specified** |
| Exact constraints | §7.1 L312–L317 — `line_number >= 1`; `source_page IS NULL OR >= 1`; `materialisation_kind IN ('FORWARD','BACKFILL')`; `UNIQUE (source_item_id, line_number)` | **specified** |
| Exact indexes | §7.1 L320 (`idx_eli_org`), L321 (`idx_eli_source_file`), §8.1 L448 (`idx_calculation_snapshots_source_line_item`), §9.1 L518 (`idx_dve_source_line_item`) = **4 explicit**; plus the constraint-backed `evidence_line_items_identity_unique` (L317) — now enumerated explicitly in §20.3 (L1169–L1201) | **specified** |
| FK targets and `ON DELETE` semantics | §7.1 (`organizations` CASCADE; `manual_extraction_items` **RESTRICT**; `organization_files` SET NULL), §8.1 (SET NULL), §9.1 (SET NULL); §20.3 now enumerates all **5** FK constraints with scope | **specified** |
| RLS intent | §16.1 (enable RLS; org-member `SELECT` policy `evidence_line_items_org_select`; PE mirror; no authenticated write policy) | **specified** |
| Privilege intent | §16.1 L955–L958 (`anon` REVOKE ALL; `authenticated` SELECT only with INSERT/UPDATE/DELETE/TRUNCATE/TRIGGER/REFERENCES/MAINTAIN revoked; `service_role` ALL) | **specified** |
| Materialisation semantics | §11.1 (eligibility), §11.2 (deterministic derivation) | **specified** |
| Line identity | §7.1 (`line_number` = 1-based persisted-array ordinal; UNIQUE with `source_item_id`); §11.1 (gaps preserved, never renumbered) | **specified** |
| Payload hashing | §11.2 (recognised keys; canonical JSON; numeric normalisation; exclusions) | **specified** |
| Idempotency | §11.3 (`ON CONFLICT … DO NOTHING`; rerun behaviour table) | **specified** |
| Divergence handling | §11.3 (detect / report / never rewrite) | **specified** |
| Forward hook | §12.1 (data-layer choke point; additive `extraction_method` kwarg; best-effort) | **specified** |
| Structured backfill | §11.4 (may/may not), §11.5 (not backfillable), §11.6 (coverage + safety net) | **specified** |
| Calculation snapshot integration | §8 (column, population/NULL rules, coexistence, immutability), §13 (both paths, resolve rule) | **specified** |
| Disclosure evidence integration | §9 (column, sanctioned by B1 contract line 413, non-destructive), §14 (B2/B3 separation + B3 join) | **specified** |
| Audit | §17 (three actions; existing `audit_trail`; payload exclusions) | **specified** |
| API / service boundaries | §12.1–§12.4 (write hook, read functions, create/update/delete semantics, **no new endpoint**) | **specified** |
| Immutability | §7.6, §15.1–§15.3 | **specified** |
| Historical-data handling | §11.5, §13.4, §15.2 | **specified** |
| Test requirements | §20.1 artefacts; §20.2 (**20** runtime tests, numbered 1–20); §20.3 clone harness + exact delta; §20.4 regression; §20.5 static-insufficient; §20.6 B1 amendments; §20.7 environment | **specified** |
| Migration ordering | §18.2 (hard dependency on B1 foundation; B2-1 before B2-2; `20260916…` sorts after B1) | **specified** |
| Implementation boundary | §22.1 (11 in-scope items) | **specified** |
| Out-of-scope items | §22.2 (expanded table), §6 (workstream table + five prohibitions), §6.1 | **specified** |
| Failure / edge cases | §21 (22 enumerated cases with required behaviour + "never" column) | **specified** |
| Rollback / data-safety | §19 (per-object coexistence table; hard rules; documented rollback shape; no destructive migration) | **specified** |

**Result:** every required item is specified with normative detail. **F-019-1 is resolved** (verified in §19.1):
the §20.3 expectation now matches the normative DDL exactly, with the constraint-backed unique index counted
separately from the four explicit indexes.

**Verification greps (this run):** §20.2 numbered items → `1…20`; §20.3 row present at L1166; enumeration
anchors present at L1169, L1172, L1173, L1175, L1190, L1195, L1198, L1201.

---

## 6. B2-D1 … B2-D12 verification

| # | Ratified decision | Ratification record | Contract reflection | Status |
|---|---|---|---|---|
| B2-D1 | `RESTRICT` preservation-first; no CASCADE | A2 §3, §3.1 | §7.1 DDL `ON DELETE RESTRICT` (L299); rationale (L328–333); §7.4 row; §7.6; §15.1; §15.3; §18.1; §20.2 test 19; §21 cases 9–10; §23 B2-D1; §24 R11; **§20.3 enumeration item 2** | **consistent** |
| B2-D2 | detect + report + never rewrite | A2 §3 | §11.3; §23 B2-D2 | **consistent** |
| B2-D3 | mirror PE item boundary; no new consultant model | A2 §3 | §16.1 PE row (L957); §16.3; §18.1; §23 B2-D3; §20.3 enumeration (PE-mirror policy) | **consistent** |
| B2-D4 | F-B2-7 deferred, not absorbed | A2 §3, §5 | §1.3; §4 F-B2-7 disposition; §6 table row; §6.1 Q7; §11.2; §22.2; §23 B2-D4; §27.1 | **consistent** |
| B2-D5 | bounded audit granularity | A2 §3 | §17 (three actions); §23 B2-D5 | **consistent** |
| B2-D6 | data-layer forward hook | A2 §3 | §12.1 (PO-RATIFIED — B2-D6); §23 B2-D6 | **consistent** |
| B2-D7 | open `extraction_method` vocabulary | A2 §3 | §7.1 (no CHECK); §11.2; §23 B2-D7 | **consistent** |
| B2-D8 | `row_reference` NULL for Class-1 | A2 §3 | §7.2; §11.2; §23 B2-D8 | **consistent** |
| B2-D9 | no new endpoint / no frontend | A2 §3 | §12.4; §22; §23 B2-D9 | **consistent** |
| B2-D10 | field deviation ratified | A2 §3 | §7.2–§7.4; §23 B2-D10 | **consistent** |
| B2-D11 | no retention/deletion mechanism | A2 §3 | §7.6 (L419–425); §15.3 (L925–942); §20.2 test 20; §20.3 ("Triggers (0)"); §23 B2-D11; §24 R14; §27.3 | **consistent** |
| B2-D12 | no retro-linking | A2 §3 | §8.4; §13.4; §15.2; §22.2; §23 B2-D12 | **consistent** |

Verified mechanically this run: contract §23 contains **12/12** `PO DECISION (B2-D…)` blocks plus the closure
summary (§23.13); the ratification record contains **12** `### B2-D…` entries each ending in
`Blockers: none` (13 occurrences incl. the §3.1 summary line).

**Focus items:**

* **A — D1 (`ON DELETE RESTRICT`, no CASCADE):** the DDL literal is present and unchanged (L299); the
  prohibition is stated (L328–333); no residual `CASCADE` recommendation exists in the contract or in report 017
  (sweep §19.2). ✔
* **B — D11 (no retention/deletion mechanism):** stated in §7.6, §15.3, §20.2 test 20, §20.3 ("Triggers (0)")
  and §23 B2-D11; the only retained "soft now" phrase is the corrective note recording its replacement. ✔
* **C — D4 (F-B2-7 deferred):** recorded as a separately tracked remediation finding (§4, §23 B2-D4, §27.1) with
  the express prohibition on fixing, reinterpreting, copying or propagating the value. ✔
* **D — D12 (no retro-linking):** §8.4, §13.4, §15.2, §22.2, §23 B2-D12; B2 writes `source_line_item_id` only on
  new snapshots. ✔

## 7. B1 compatibility verification

| Check | Evidence | Status |
|---|---|---|
| B1 remains CLOSED | A4/S4 chain; contract §1 (B1 CLOSED, not reopened) | **compliant** |
| B1's 11-table scope intact | contract §20.6 requires the disclosure-namespace check to remain "exactly the 11 B1 tables"; B2 creates **no** `disclosure_*` table | **compliant** |
| No hidden B1 table | B2's new table is `evidence_line_items` (no `disclosure_` prefix); §22.1 item 1 | **compliant** |
| `disclosure_value_evidence` extended only by the ratified nullable line FK | §9.1 (guarded `ADD COLUMN IF NOT EXISTS source_line_item_id uuid` + FK `ON DELETE SET NULL` + index); §9.3 (B1 unique constraint and `uq_dve_reference_nullsafe` unmodified) | **compliant** |
| B1 `value_status` semantics untouched | the contract never alters `value_status`; §9.3 enumerates what B2 does not change | **compliant** |
| B1 immutability / audit / RLS decisions intact | §9.3 (audit action reused; immutability rule inherited); §16.2 (no grant/policy/RLS change on B1 tables) | **compliant** |
| B1 migration files byte-identical | sha256 values recorded in §4 are **identical to the pre-correction gate run** (`7cf72bcd…`, `702faf22…`); contract §18.3 requires it; B2 declares two **new** filenames | **compliant** (untracked in git → hash baseline is the evidence) |
| B1's two invalidated scope assertions handled | §20.6 + §27.2: **amend, never delete**; B3/B4 guards preserved; migration-text guards untouched | **compliant** |

---

## 8. P1 boundary verification (PDF/IMAGE extraction)

| Check | Evidence | Status |
|---|---|---|
| No authorisation of PDF/IMAGE extraction remediation | §1.2; §6 table row (P1 = separate future **investigation** workstream); §22.2 row; §27.4 | **compliant** |
| No IMAGE remediation / OCR redesign | §6.1 ("no extraction code, prompt, gate, OCR setting or `source_page` behaviour may be changed"); §22.2 | **compliant** |
| No AI extraction-gate changes | §6.1; §22.2 | **compliant** |
| No historical PDF/IMAGE re-extraction | §11.5 (classes 2/3/4 → no rows, no re-parse); §11.4 ("may not re-run any extraction, OCR, LLM, parser or heuristic"); `DM-7` refinement 3 (quoted in §6 prohibitions) | **compliant** |
| No `source_page` repair | §6 row; §27.1 (B2 does not remediate, reinterpret, copy, transform or propagate); §11.2/§11.7 (`source_page` only from a genuine per-line value) | **compliant** |
| Only interface to P1 is the declared hook | §11.7 (optional element keys `page`, `line_reference`, `extraction_method`; no extractor modified by B2) | **compliant** |
| Separate investigation is a future bounded workstream | §6.1 (12 questions recorded) | **compliant** |

**Cross-workstream observation [O-1] (positive, unchanged):** the independent P1 workstream artefact
`docs/architecture/CARBONTALLY_PHASE8_P1_PDF_IMAGE_EXTRACTION_REMEDIATION_CONTRACT_20260913.md` (889 lines,
10:59:47 today) plus its forensic report 020 **align** with B2: they cite B2 §6.1/§7.1/§11/§27.1/§27.4 and the
ratification record (B2-D4/D8/D12) as their interfaces, adopt B2 §11.7's optional keys and §11.2's key
vocabulary with the array-ordinal position as B2's `line_number`, and keep B2 objects,
`evidence_line_items`, `calculation_snapshots.source_line_item_id` and the `source_page` remediation explicitly
**out of scope**. No B2 file was modified by that workstream, and the interface remains consistent.

## 9. P2 boundary verification (EF-E / factor matching)

| Check | Evidence | Status |
|---|---|---|
| EF-E not absorbed | §1.2; §6 row (P2 independent, no coupling); §22.2 row; §25 row 8 | **compliant** |
| No `FactorMatchingEngine` change | §6 prohibition 4 ("No change to the calculation engine, the factor-matching engine, or the report lifecycle spine"); §13.3 | **compliant** |
| No factor-precedence change | §13.3 (factor precedence untouched) | **compliant** |
| No unit-matching change | §11.2 (`raw_unit` stored pre-normalisation; unit aliasing remains `core.units`' job); §13.3 | **compliant** |

## 10. B3 / B4 boundary verification

| Check | Evidence | Status |
|---|---|---|
| B2 = evidence/line-item addressability only | §5.2 deliverables D1–D11 (no framework/intensity/narrative item); §14.1 separation table | **compliant** |
| B3 work not silently implemented | §14.1 (B3 owns requirements/mappings/applicability/purpose/intensity/per-gas/base-year, read model + UI); §22.2; §23 B2-D9 | **compliant** |
| B4 work not silently implemented | §14.1 (narrative/finalisation/frozen artefact = B4); §22.2 | **compliant** |
| B2 does not pre-empt B3's read model | §14.2 (design target only, "not implemented here"); §12.4 (no endpoint) | **compliant** |
| B1-test amendment preserves B3/B4 guards | §20.6 (split: B3/B4 negatives unchanged; only B2-absence assertions move to the B2 suite); §27.2 ("the B3/B4 negative assertions are preserved"); "amend, **never** delete" | **compliant** |

## 11. Phase 8-X boundary verification

| Check | Evidence | Status |
|---|---|---|
| Phase 8-X remains separate | §6 row ("separate namespace, separate gate"); §22.2 row | **compliant** |
| No X1–X8 work authorised | none of the 11 §22.1 in-scope items touches Phase 8-X; §22.2 excludes it | **compliant** |
| No runtime introspection / worker heartbeat / operational analytics change | §17 (audit only, existing `audit_trail`); §12 (no new endpoint); §22.2; §6 prohibition 4 | **compliant** |
| No Phase 8-X migration | §18.1 declares exactly two B2 migrations; no other file created | **compliant** |

---

## 12. Security / RLS boundary verification

| Check | Evidence | Status |
|---|---|---|
| Bounded to the new table + declared columns | §16.1 (new table), §16.2 ("adding a nullable column with a guarded FK and an index changes **no** grant, **no** policy and **no** RLS flag"), §22.2 | **compliant** |
| No broad production RLS remediation | §16 preamble ("B2 adds posture **only for its own objects** … does not remediate the broad production RLS baseline and modifies **no** unrelated policy (G0-H)") | **compliant** |
| `anon` denial | §16.1 L955 (`REVOKE ALL`, no policy) | **compliant** |
| Authenticated read boundary | §16.1 L956 (`GRANT SELECT` only; `evidence_line_items_org_select` using the **existing** B1 helper `p8_disclosure_is_org_member(organization_id)`; helper never recreated; B2-1 fails loudly if B1 is absent) | **compliant** |
| Authenticated write denial | §16.1 L956 (`INSERT/UPDATE/DELETE/TRUNCATE/TRIGGER/REFERENCES/MAINTAIN` revoked) | **compliant** |
| Service-role operational access | §16.1 L958 (`GRANT ALL`; backend is the writer) | **compliant** |
| Org/member isolation | §16.1 (cross-tenant read must return **zero** rows — primary negative test); §16.3 (customer/consultant scoping via existing guards) | **compliant** |
| PE boundary | §16.1 L957 + §16.3 + §23 B2-D3 (mirror `manual_extraction_items_entity_select` via `is_entity_member(work_item_effective_entity(source_item_id))`; no new consultant authorization model; no widening) | **compliant** |
| No new authorization mechanism | §6 prohibition 5; §16.3 | **compliant** |
| Negative tests required | §20.2 tests 12–13 (RLS ALLOW/DENY; privilege denial) | **compliant** |

**No RLS change is authorised or performed by this task** (read-only inspection only; §17).

## 13. Historical reproducibility verification (D15 / `DM-7`)

| Check | Evidence | Status |
|---|---|---|
| Deterministic / idempotent materialisation of structured `line_items[]` | §11.1 (eligibility), §11.2 (pure derivation + canonical `payload_hash`), §11.3 (`DO NOTHING`; no clock/randomness/external calls) | **compliant** |
| Flat PDF/IMAGE history not silently re-extracted | §11.4 ("may not re-run any extraction, OCR, LLM, parser or heuristic"), §11.5 (classes 2/3/4 → no rows) | **compliant** |
| No synthetic lines | §10.4 (no synthetic line, placeholder or sentinel UUID); §11.1 (empty array never falls back to the flat record); §8.2 | **compliant** |
| No historical snapshot retro-linking | §8.4, §13.4, §15.2, §22.2, §23 B2-D12 | **compliant** |
| Divergence reported, not rewritten | §11.3 (divergence table + `DO NOTHING` rationale), §23 B2-D2 | **compliant** |
| Existing provenance preserved | §19 (rows byte-identical expected), §9.3 (B1 document-level evidence remains valid), §10.4 | **compliant** |
| Materialised line survives later JSONB correction | §7.5 (immutable materialised record, not a live pointer), §15.2 (finalized report reproducible via `raw_*` + `payload_hash`) | **compliant** |

## 14. Calculation safety verification

| Check | Evidence | Status |
|---|---|---|
| No new calculation engine | §13.1 ("Consumed unchanged"), §13.3, §23 note ("No new calculation engine is created and none may be"), §6 prohibition 4 | **compliant** |
| No factor-matching alteration | §13.3; §6 row / §22.2 (P2); §1.2 | **compliant** |
| No methodology alteration | §13.3 | **compliant** |
| No rounding alteration | §13.3 ("no formula, factor selection, rounding, methodology, hash algorithm … is touched") | **compliant** |
| No request-ID derivation change | §8.4; §13.3 | **compliant** |
| `source_line_item_id` not in request-ID derivation | §8.4 (explicit prohibition + duplicate-snapshot rationale, L498); §13.3; §23 note | **compliant** |
| Only optional source-line provenance added | §13.1 (`CalculationRequest` gains one optional field); §8.1 (nullable column; existing snapshots untouched); §8.2 (NULL rules) | **compliant** |

---

## 15. Migration readiness verification

| Check | Evidence | Status |
|---|---|---|
| Exactly two migrations declared | §18.1 (L1023–1024): `20260916000000_p8_b2_evidence_line_items.sql`, `20260916010000_p8_b2_provenance_line_links.sql`; identical names in §18.2/§18.3 and report 018 | **compliant** |
| Additive-only intent | §18.1 (`CREATE TABLE IF NOT EXISTS`; `ADD COLUMN IF NOT EXISTS`; guarded FK via `DO $$ … conname …`; `CREATE INDEX IF NOT EXISTS`); §19 hard rules; §23 B2-D11 (no trigger) | **compliant** |
| B1 migration files remain untouched | §18.3 ("remain **byte-identical**"); sha256 values in §4 are unchanged from the pre-correction run | **compliant** |
| Migration ordering valid | §18.2 (B2-1 after B1 foundation; B2-2 after B2-1); `20260916…` sorts strictly after B1's `20260914`/`20260915`; on disk the newest migration is still the B1 correction | **compliant** |
| FK dependencies understood | §18.2 (B2-2 targets `evidence_line_items` from B2-1 and `disclosure_value_evidence` from B1); §16.1 (B2-1 precondition on the B1 helper, failing loudly) | **compliant** |
| No destructive operation required | §19 hard rules + documented rollback shape; §20.1 forbids `DROP`/`ALTER TYPE`/`RENAME`/`UPDATE`/`DELETE` | **compliant** |
| Backfill separate from the schema migration | §11.4 ("the backfill is **NOT a migration**"; separately invoked; dry-run; execution separately authorised); §18.1 | **compliant** |
| Production deployment not authorised | §18.4 item 7; §22.2; §25 row 11 | **compliant** |

**No migration file was created or applied by this task** (§17, §19.3).

## 16. Runtime verification readiness

| Requirement | Evidence | Status |
|---|---|---|
| Database-backed runtime suite required | §20.2 preamble ("mandatory"); §20.5 (static-only is insufficient — the V1 lesson) | **present** |
| Migration idempotency | §20.2 test 18; §20.3 last row | **present** |
| RLS / privilege verification | §20.2 tests 12–13; §20.3 table-level parity | **present** |
| Tenant isolation | §20.2 test 12; §19 | **present** |
| Materialisation | §20.2 tests 1, 4–6 | **present** |
| Idempotency | §20.2 tests 2, 11 | **present** |
| Divergence | §20.2 tests 10, 16 | **present** |
| Line identity | §20.2 tests 1, 4; §20.1 pure tests | **present** |
| Calculation linkage | §20.2 tests 7–9 | **present** |
| Evidence linkage | §20.2 test 15 (incl. snapshot↔`dve` consistency) | **present** |
| Historical behaviour | §20.2 tests 5–6, 8, 14 | **present** |
| Audit | §20.2 test 16 | **present** |
| Immutability | §20.2 tests 2, 14, 19 | **present** |
| Retention-artifact absence | §20.2 test 20; §20.3 ("Triggers (0)") | **present** |
| B1 regression | §20.4 (B1 suite green incl. F1–F5, tenant isolation, immutability, privilege posture, audit emission) | **present** |
| B3/B4 boundary protection | §20.6 (amend-not-delete; guards preserved); §27.2 | **present** |
| **A SKIPPED suite is NOT a PASS** | §20.7 ("a skip is **not** a PASS … must be stated in the B2 verification report rather than papered over"); §24 R9 | **present** |
| Provisioned B1+B2 disposable clone required for final runtime verification | §18.5 (clone recipe; never the main app DB or investor-demo DB — D31); §20.7; §25 row 10 | **present** (environment does not yet exist — §17) |

Contract §20.2 contains **20** numbered runtime acceptance tests (verified `1…20` this run).

## 17. Environment status

**No provisioned B1+B2 disposable verification database currently exists** [V, read-only introspection]:

| Database | Public tables | `disclosure_*` tables | `evidence_line_items` | `calculation_snapshots.source_line_item_id` |
|---|---|---|---|---|
| dev application DB (`DATABASE_URL`) | 116 | 0 | absent | absent |
| `carbontally_test` (integration DB used by `conftest.py`) | 114 | 0 | absent | absent |
| `postgres`, `_supabase`, `storage_vectors` | not B1/B2-bearing | — | absent | absent |

* `conftest.py` forces `DATABASE_URL = INTEGRATION_DATABASE_URL` (default
  `postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test`) and refuses the main application DB (D31).
* Consequently the B1 runtime suite **and** any future B2 runtime suite **SKIP** in this environment — the §20.7
  declared limitation, **not** a PASS.
* **Not a blocker to implementation authorisation** (the contract does not require the clone before
  implementation; §25 row 10 classifies it as a V2 verification blocker). But **runtime V2 can never be
  declared PASS without it**, and implementation and verification remain separate gates.
* **Actionable [O-2]:** `carbontally_test` has 114 public tables and no B1 schema, whereas §20.3's parity check
  targets **116 pre-existing** tables (the production-shaped clone V1R measured). The implementation task must
  build the §18.5 privileges-inclusive disposable clone rather than treating `carbontally_test` as the clone.

## 18. Production deployment boundary (preserved)

* **Production deployment is NOT authorised** — §18.4 item 7 ("Never run against production while the
  outstanding-migration decision (G0-D) is unresolved"), §22.2 ("Production migration / deployment — **not
  authorised**"), §26.3, A2 §9.
* **G0-D remains OPEN** — §25 row 11: "G0-D — production migration strategy for the 34-outstanding backlog …
  **Open**; B2 adds 2 migrations; production not authorised".
* The **34 previously-outstanding migrations remain a production deployment blocker**; B2 adds **two**.
* **No migration reconciliation was attempted** in this task.

---

## 19. Contradictions / findings

### 19.1 F-019-1 — RESOLVED (was the sole blocker in the first run)

**Original finding (first run of this gate):** contract §20.3's "New objects present" row stated *"3 new
indexes (org, source_file, dve line)"* and used ambiguous totals ("2 FKs", "2–3 policies"), contradicting the
normative DDL (four explicit indexes + one constraint-backed unique index) and its own adjacent row (two new
indexes on pre-existing tables).

**Resolution (task 021, verified this run):**

| Element | Now stated | Verified |
|---|---|---|
| New table | 1 — `public.evidence_line_items` | L1166 + enumeration L1172 |
| New columns on pre-existing tables | 2 — `calculation_snapshots.source_line_item_id`, `disclosure_value_evidence.source_line_item_id` | L1173 |
| FK constraints | **5** — 3 declared inside the new table (`organizations`; `manual_extraction_items` **`ON DELETE RESTRICT`**; `organization_files` `SET NULL`) + 2 on pre-existing tables (`calculation_snapshots_source_line_item_id_fkey`, `disclosure_value_evidence_source_line_item_id_fkey`) | L1175–L1189 |
| Explicit indexes | **4** — `idx_eli_org`, `idx_eli_source_file`, `idx_calculation_snapshots_source_line_item`, `idx_dve_source_line_item` | L1190–L1194 |
| Constraint-backed unique index | **1, counted separately** — `evidence_line_items_identity_unique` (`UNIQUE (source_item_id, line_number)`) | L1195–L1197 |
| Policies | **2** — org-member SELECT (`p8_disclosure_is_org_member(organization_id)`) + PE-mirror SELECT (`is_entity_member(work_item_effective_entity(source_item_id))`) | L1198–L1200 |
| Triggers | **0** (B2-D11) | L1201 |

**Sweep result:** `3 new indexes`, `3 indexes`, `2 FKs`, `2–3 policies`, `the 18`, `recommend CASCADE`,
`Unresolved decisions` → **0 occurrences in both the contract and report 017**; the corrected figures are
present and agree in both documents (4 explicit / 1 constraint-backed / 5 FK / 2 policies / 0 triggers;
**20** runtime tests). **No material contradiction remains.**

### 19.2 Non-material observations (recorded; not blocking)

* **O-1 — concurrent P1 workstream aligns with B2** (§8): P1's remediation contract adopts B2 §11.7's optional
  keys and §11.2's vocabulary, and keeps B2 objects and the `source_page` remediation out of scope. No B2 file
  was modified by it.
* **O-2 — environment shape** (§17): `carbontally_test` (114 tables, no B1 schema) cannot serve as the §20.3
  clone; the §18.5 disposable clone must be built. Not an authorisation blocker.
* **O-3 — B1 migrations are untracked in git**, so "byte-identical" is evidenced by the sha256 baseline in §4
  (identical across the pre-correction and post-correction gate runs) rather than by a VCS diff.
* **O-4 — two deliberate textual residuals** (both benign): the contract's B2-D11 rationale retains the phrase
  *"the earlier wording 'soft now'"* as the corrective note recording its replacement; and the previous
  (blocked) run of this gate is recorded in report 021 as finding F-019-1, whose verbatim defect quotations
  remain there by design.
* **O-5 — this report was rewritten.** The report path is the mandated output of this task; the first run's
  content (BLOCKED verdict, finding F-019-1) is superseded by this re-run and is preserved in report 021.

### 19.3 What is NOT disputed

No contradiction, ambiguity or gap was found in: contract completeness (26/26 required items); the twelve PO
decisions and their contract reflection; B1 compatibility; the P1, P2, B3/B4 and Phase 8-X boundaries; the
security/RLS posture; historical reproducibility (D15/`DM-7`); calculation safety; the two-migration additive
strategy; the runtime acceptance contract; the environment declaration; or the production-deployment boundary.

## 20. Explicit verdict

**`B2 IMPLEMENTATION AUTHORISATION COMPLETE — B2 IMPLEMENTATION MAY PROCEED`**

**Basis:** every authorisation condition is satisfied against the **corrected** governance chain. The single
material finding from the first run (**F-019-1**) is resolved and verified (§19.1); the contract specifies all
26 required completeness items; B2-D1…B2-D12 are closed and consistently reflected; B1 compatibility, all
workstream boundaries, the security posture, historical reproducibility, calculation safety, migration
readiness and the runtime verification contract are compliant; and no material contradiction remains.

**This verdict means ONLY that the next separate task may implement B2.** It does **not** mean that B2 is
implemented, that B2 is verified, that any migration is applied, or that production deployment is authorised.

**Carried forward as implementation preconditions (not blockers to authorisation):**

1. build the **§18.5 disposable B1+B2 clone** before runtime V2 — a **SKIPPED suite is not a PASS** (§20.7);
2. keep **implementation and verification as separate gates**;
3. respect **G0-D / the production deployment prohibition** (34 outstanding migrations + B2's 2);
4. apply the §20.6 **amend-never-delete** B1 test rule and the §27.1/§27.2/§27.3 dispositions.

**Explicitly NOT authorised or implied:** B2 implementation by this task; creation or application of any
migration; production deployment; any backend/frontend/test/RLS/extraction/OCR/AI/`source_page`/factor-matching
change; historical backfill; any commit or push.

**Task discipline:** the only file written was this report; the worktree was not reset, cleaned, stashed,
checked out, staged, committed or pushed; baseline `main` / `19e4f01c176eee5870f3c15038b6e7c68b23281c` /
staged 0 / 208 pre-existing tracked modifications / 57 migrations is unchanged; no B2 migration file exists; no
database object was created or modified.
