# CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017

**Task identity:** `CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017`
**Task type:** ARCHITECTURE + IMPLEMENTATION CONTRACT ONLY — **implementation not authorised**
**Date:** 2026-09-13
**Batch:** Phase 8 Reporting / Disclosure — **B2 Evidence / Line-Item Addressability**
**Primary deliverable:** `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md`
**Verdict:** `B2 IMPLEMENTATION CONTRACT COMPLETE — READY FOR PO REVIEW`

---

## 1. Task identity and scope

Produce the complete, bounded implementation contract for Phase 8 batch **B2 — Evidence / Line-Item
Addressability**, determining the data model, snapshot/evidence linkage, provenance chain, backfill boundary,
API/service impact, calculation integration, immutability, RLS, audit, migration strategy, test contract,
implementation boundary and decision questions — **on the basis of the repository and the existing Phase 8
governance records only**.

**Respected constraints (verified §3):** no implementation; no migration created; no backend/frontend/test
change; no RLS change; no data mutation; no production action; no commit; no push; no worktree disturbance.
Exactly two files were written (the contract and this report).

## 2. Scope

**In scope for this task:** read-only inspection of governance records, code, migrations and live schema;
produce the contract and this report.

**Out of scope (explicitly not performed):** implementing B2; creating migrations; modifying
`backend/`, `frontend/`, `supabase/migrations/`, tests or RLS; running the backfill; provisioning databases;
reopening B1; resolving any PO decision.

## 3. Baseline / worktree state recorded before analysis

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (`feat: implement Phase 8 report lifecycle foundation`) |
| Staged changes | 0 |
| Tracked modifications (pre-existing, unrelated) | 208 |
| Untracked paths (pre-existing) | 73 |
| Migrations on disk | 57 (newest: `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql`) |
| Worktree operations | **none** (no reset/clean/stash/checkout/stage/commit/push) |
| Files written by this task | `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md`; this report |

**Live database (read-only introspection, local development DB)** [V]: `evidence_line_items` and
`calculation_snapshots.source_line_item_id` **do not exist**; B1's `disclosure_*` relations are also absent
(B1 has never been applied to this environment, consistent with report 016). `manual_extraction_items` has 36
columns and **no `organization_id`** (tenant via `batch_id`). `calculation_snapshots` has `source_item_id`
(FK→items, `SET NULL`), `source_file`, `source_page` only. `manual_extraction_items` has exactly one RLS
policy (PE SELECT via `work_item_effective_entity` + `is_entity_member`); `calculation_snapshots` has exactly
one (`is_org_member(organization_id)`); neither has an authenticated write policy.

## 4. Sources inspected

Governance/design [D]: Disclosure Model Design (§13, §14, §17, §18.2, §22) · Disclosure Model Decision Record
(§6 `DM-7` + Gate-0 refinement, §10) · P8X comprehensive implementation-readiness (§15, §16, §20–§22, §29) ·
B1 implementation contract (§6, §25, line 413) · `CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912` ·
`CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912`.

Code/migrations [R]: `backend/engines/calculation.py` · `backend/domain/calculation.py` ·
`backend/services/automatic_processing.py` · `automatic_extraction.py` · `ai_document_extraction.py` ·
`extraction_suggestions.py` · `backend/api/v3_operations.py` · `v3_processing_workflow.py` ·
`v3_manual_extraction.py` · `backend/data/manual_extraction.py` · `document_processing.py` · `disclosure.py` ·
`backend/domain/evidence.py` · migrations `20260823010000_d33…`, `20260912000000_p7…`, `20260914000000_p8_b1…`,
`20260915000000_p8_b1_correction…`, `20260903010000_ws4_gate3_4a…`, `20260810050000_v3m6_entity_rls…` ·
`backend/tests/integration/{conftest.py,test_disclosure_b1_runtime.py}` ·
`backend/tests/unit/data/test_disclosure_{migration,sql_typing}.py`.

Live schema/policy introspection (read-only) [V].

---

## 5. Current-state findings (summary; full evidence in contract §4)

| # | Finding | Tag |
|---|---|---|
| F-B2-1 | No durable line identity exists; snapshot provenance stops at document level | [R]/[V] |
| F-B2-2 | The **ordinal** is already the implicit join key (`mapped_lines[idx]`) and is guaranteed aligned on success (a dropped line blocks the job) | [R] |
| F-B2-3 | Deterministic request ids are **already line-scoped** (`…::calc::{idx}::c1::{digest}`) — must not change | [R] |
| F-B2-4 | `mapped_data.line_items` is **rewritten/lossy** after calculation — never a B2 identity source | [R] |
| F-B2-5 | The original source row number is **not recoverable**; `invoice_number` is a document id, not a line ref | [R] |
| F-B2-6 | Persisted arrays are already normalised (empty rows/records dropped) and ordered | [R] |
| F-B2-7 | **`calculation_snapshots.source_page` is a page COUNT** (`job.metadata["page_count"]`), yet `domain/evidence.py` treats a non-NULL page as an exact location → false `COMPLETE` | [R] |
| F-B2-8 | Tenant is reachable only via the parent batch; the item has no `organization_id` | [R]/[V] |
| F-B2-9 | One pipeline choke point (`save_extracted_data`, 4 call sites) + one extra writer (`PUT /manual-extraction/items/{id}`) | [R] |
| F-B2-10 | **No application path deletes an extraction item** (`delete()` is a no-op stub) | [R] |
| F-B2-11 | D33 is the additive template (guarded column/FK/index, idempotent exact-match backfill, one transaction) | [R] |
| F-B2-12 | B1's corrected privilege/RLS/helper posture is the template for a new table | [R] |
| F-B2-13 | **Two B1 test-scope artefacts B2 necessarily invalidates** (runtime `test_b2_b3_b4_boundary_untouched`; unit `test_no_b2_b3_b4_objects_in_the_repository`); the two migration-text guards stay valid | [R] |
| F-B2-14 | Runtime verification precedent: forced dedicated test DB (D31), skip-when-unprovisioned, privileges-inclusive clone harness (V1R) | [R]/[V] |
| F-B2-15 | Extraction-method vocabulary is open and only persisted on the **queue**, never on the item | [R] |
| F-B2-16 | No environment holds B1/B2 → runtime V2 needs a provisioned disposable clone | [V] |

**Two genuinely new defects/risks discovered by this task (not previously recorded in the Phase 8 records):**

1. **F-B2-7 — `source_page` is a page count used as a page.** `_calculate_line` sets
   `source_page=job.metadata.get("page_count")` (`automatic_processing.py:1134`); the metadata value is the
   item's page count (`v3_processing_workflow.py:991`); `domain/evidence.py` maps non-NULL page → `has_page`
   → `COMPLETE`. Consequence: auto-processed evidence can claim an **exact source location that is false**.
   Surfaced as decision **B2-D4**; B2 must never copy the value and must not silently "fix" it as part of a
   provenance batch.
2. **F-B2-13 — B1's boundary tests contradict B2's existence by design.** These assertions were correct for
   B1's scope, but a naive B2 implementation would either fail them or (worse) delete them, removing the
   guard against B3/B4 leakage. The contract mandates specific, minimal **amendments** (§20.6 of the contract).

## 6. Proposed B2 architecture (summary)

> One new immutable, org-scoped, addressable line table materialised deterministically from the *persisted*
> `extracted_data.line_items[]` by ordinal; two additive nullable FK columns closing the line hop in the
> ratified chain; an idempotent, dry-runnable Class-1 backfill for historical structured data; a best-effort
> forward hook so new extractions materialise automatically; runtime-verified RLS/privilege/audit posture that
> leaves every pre-existing object and row untouched.

**Canonicality decision (deliverable F):** *hybrid, and deliberately so.* `extracted_data.line_items[]` stays
the **extraction output** and the sole eligibility source (never written by B2); `evidence_line_items` is the
**immutable provenance/evidence authority** (the thing that can be pointed at). A JSONB-pointer design was
rejected because it breaks D15 the moment a correction rewrites the array; a normalized-extraction redesign was
rejected as P1 territory.

## 7. Exact schema (summary; normative SQL in contract §7–§9)

**New table `public.evidence_line_items`** — `id`, `organization_id` (NOT NULL), `source_item_id` (NOT NULL),
`source_file_id`, `line_number` (1-based ordinal, NOT NULL), `source_page`, `row_reference`,
`raw_description`, `raw_quantity`, `raw_unit`, `payload_hash` (NOT NULL), `extraction_method` (NOT NULL
DEFAULT `'unknown'`), `materialisation_kind` (`FORWARD`|`BACKFILL`), `created_at`;
`UNIQUE (source_item_id, line_number)`; CHECKs on `line_number >= 1`, `source_page >= 1`,
`materialisation_kind` vocabulary; indexes on `(organization_id)`, `(source_file_id)`.

**Additive columns:** `calculation_snapshots.source_line_item_id uuid` (nullable, FK → `evidence_line_items`
`ON DELETE SET NULL`, indexed) and `disclosure_value_evidence.source_line_item_id uuid` (same shape; already
sanctioned by the ratified B1 contract line 413).

**Deliberate reductions from design §14.3** (documented, for PO confirmation): dropped
`document_type_code`, `confidence_score`, `extracted_at`, `extracted_by` (document-level or **no producer**)
and `processing_origin` (**mutable parent attribute** — `mark_pe_origin_if_unset` can change it after
materialisation, so a copy can become wrong). **Additions:** `materialisation_kind` (the `DM-7` honesty signal)
and `created_at`. Rejected: whole-payload JSONB copy, marker columns on `manual_extraction_items`, `updated_at`,
soft-delete flag.

---

## 8. Exact migration strategy

**Two new migrations, additive only; the backfill is not a migration** (contract §18):

| File | Contents |
|---|---|
| `supabase/migrations/20260916000000_p8_b2_evidence_line_items.sql` | B2-1 — create `evidence_line_items` + constraints + indexes; RLS enable; privilege posture (anon revoked; `authenticated` SELECT only; TRUNCATE/TRIGGER/REFERENCES/MAINTAIN revoked; `service_role` ALL); org-member SELECT policy; **[REC]** PE SELECT policy mirroring the item policy; explicit precondition check that the B1 helper `p8_disclosure_is_org_member` exists (fails loudly if not) |
| `supabase/migrations/20260916010000_p8_b2_provenance_line_links.sql` | B2-2 — `calculation_snapshots.source_line_item_id` + guarded FK (`SET NULL`) + index; `disclosure_value_evidence.source_line_item_id` + guarded FK + index |

* **Ordering:** B2-1 after B1's `20260914000000_…`; B2-2 after B2-1 and after B1's foundation (its FK targets).
  Timestamps `20260916…` sort strictly after B1's `20260914`/`20260915`.
* **Idempotency:** both re-appliable with `rc=0` and zero diff; guarded `DO $$ … IF NOT EXISTS (conname) …`
  blocks (D33 pattern); `ADD COLUMN IF NOT EXISTS`; `CREATE INDEX IF NOT EXISTS`.
* **No data dependency:** neither migration reads or writes table data.
* **B1 migrations untouched** (byte-identical) — which is what keeps B1's two migration-text guards valid.
* **Deployment:** not authorised. The **34 previously-outstanding migrations remain a production blocker**
  (G0-D); B2 adds 2 more. Production application is out of scope.
* **Backfill:** a separately-invoked, offline, idempotent operation (dry-run + run report + divergence
  detection) with a thin CLI entry point alongside `backend/tools/enforce_retention.py`; **execution on any
  environment is separately authorised**.

## 9. Exact provenance model

**Forward:** `report_generation_queue → report_versions → disclosure_values → disclosure_value_evidence →
calculation_snapshots → { source_item_id → manual_extraction_items → organization_files | **source_line_item_id
→ evidence_line_items** }`.

**Reverse:** `organization_files → manual_extraction_items → evidence_line_items → calculation_snapshots →
emissions_logs / disclosure_value_evidence → disclosure_values → report_versions`.

**Already authoritative (untouched):** D33's `file_id`/`source_item_id`/`snapshot_id` chain; B1's
value→evidence links; `domain/evidence.py` classification.
**New in B2:** line identity; snapshot→line; evidence→line.
**Honesty rule:** where no line exists the chain stops at document level, the link stays NULL and the
classification stays PARTIAL/UNAVAILABLE; no synthetic line, placeholder or sentinel UUID is ever created.

## 10. Structured historical backfill boundary (Class-1 only)

* **Eligibility:** `extracted_data.line_items` is a non-empty JSON array; per element (in array order,
  ordinal = index+1): object with ≥ 1 recognised key carrying a value → materialise; empty object →
  `skipped_empty`; non-object → `skipped_malformed`; **ordinals are never renumbered** (gaps preserved).
* **Deterministic identity:** `(source_item_id, line_number)`; `payload_hash` = sha256 over the canonical
  recognised-key payload (sorted keys, compact separators, numeric normalisation so `100`/`100.0`/`100.00`
  hash identically). Pure function of the persisted row — no clock, no randomness, no external calls.
* **Idempotency:** `INSERT … ON CONFLICT (source_item_id, line_number) DO NOTHING` — rerun inserts nothing,
  mutates nothing, deletes nothing. Deliberately **not** B1's `DO UPDATE` (a line is immutable evidence).
* **Divergence:** a stored row whose hash no longer matches the derivable payload is **reported**, never
  rewritten (decision B2-D2).
* **Not backfillable:** flat PDF/IMAGE records, OCR-text-only records, records without sufficient source
  representation — **no** rows, **no** inference, **no** re-extraction, **no** derivation from aggregate
  fields; the separately-authorised P1 re-parsing capability is out of scope.
* **Coverage safety net:** the forward hook covers new writes; the backfill (safe to re-run) covers anything
  missed — hence no marker column is needed or added.

## 11. API / service impact

* **Write:** materialisation hooks the **single data-layer choke point** `ManualExtractionRepository`
  (`save_extracted_data`, and `update_item` when `extracted_data` is supplied), best-effort and non-blocking;
  `save_extracted_data` gains an **additive optional** `extraction_method` keyword (the pipeline passes its
  real `method_stamp`; human paths pass `"manual"`). This covers all four API/pipeline call sites (verified
  in contract §12.1).
* **Read:** new insert-only materialisation + `list_for_item` / `get` / `get_by_ordinals` / `count_for_item`
  in `backend/data/evidence_line_items.py`, all org-scoped.
* **No new HTTP endpoint and no frontend work** (B2-D9): B2 delivers addressability; the drill-down surface is
  B3/B4 (`DM-6`). Existing response shapes are unchanged.
* **Semantics:** create = materialisation only (a line is derived, never authored); **update and delete are not
  supported** in B2.

---

## 12. Calculation integration

* `CalculationRequest` gains one optional field `source_line_item_id`; the snapshot persists it.
* **Population:** both calculation paths resolve `(source_item_id, idx+1)` → line id via one indexed lookup
  (`evidence_line_items_identity_unique`) and pass it through:
  `automatic_processing._calculate_line` and `v3_operations._run_line_calculation`.
* **NULL semantics:** flat documents (`targets=[dict(extracted)]`), manual computations, unmaterialised lines
  and historical snapshots keep NULL.
* **Never touched:** the deterministic request-id derivations, resume markers, the duplicate-prevention guard,
  factor matching/precedence, unit resolution, methodology, rounding and the `content_hash` algorithm.
* **Explicit prohibition:** `source_line_item_id` must **not** enter the request-id derivation; otherwise a
  snapshot requested before and after materialisation would hash differently and duplicate the calculation
  (violating `DM-7` and the `V2` acceptance).
* **No historical retro-linking:** existing snapshots are never inferred onto a line (B2-D12).
* **No new calculation engine** is created; the calculation layer is consumed unchanged.

## 13. Evidence integration

* B2 adds **one** additive nullable column on B1's `disclosure_value_evidence` (`source_line_item_id`), already
  sanctioned by the ratified B1 contract, keeping B3's value→line enumeration a **one-hop join** and covering
  snapshot-less evidence rows.
* `link_value_evidence` gains exactly one optional keyword argument; B1's unique constraint and NULL-safe index
  are **unchanged**, and a snapshot can never legitimately appear twice for one value (one snapshot = one line).
* Multi-line cardinality already works: one value → n evidence rows → n snapshots → n lines.
* **Rejected:** a new value↔line bridge table (duplicate model); modifying `emissions_logs` (derivable via
  `snapshot_id`); changing `domain/evidence.py` classification (a B3/B4 presentation question). The `dve`
  column is written only from the snapshot/line, enforced by a consistency test.

## 14. Authorization / RLS intent

* **New table posture** (mirrors B1's corrected pattern): `anon` revoked; `authenticated` **SELECT only**
  (`INSERT/UPDATE/DELETE/TRUNCATE/TRIGGER/REFERENCES/MAINTAIN` revoked); `service_role` ALL;
  `ENABLE ROW LEVEL SECURITY`; org-member SELECT policy reusing the **existing** B1 helper (never recreated;
  B2-1 fails loudly if B1 is absent); **[REC]** PE SELECT policy mirroring the existing
  `manual_extraction_items_entity_select` boundary via
  `is_entity_member(work_item_effective_entity(source_item_id))` (B2-D3 — widens nothing: the line payload is a
  subset of the JSONB PE can already read).
* **Existing tables (B2-2):** the two additive columns change **no** grant, policy or RLS flag — proven by the
  clone harness.
* **Application layer remains the enforced boundary** (B1's declared posture); B2 adds **no** new authorization
  mechanism, remediates **no** unrelated RLS and grants **no** consultant/staff capability.
* **Viewer/member/consultant:** no write path exists at all in B2 (so viewer restrictions hold by
  construction); consultant access stays bounded by the existing `ensure_org_access`/`require_org_member`
  guards.
* **Negative tests are mandatory:** cross-tenant read → 0 rows; PE-X → PE-Y → 0 rows; `anon` → 0 rows;
  authenticated writes → permission denied.

## 15. Audit requirements

Three new actions on the **existing** `audit_trail` (no parallel audit system):

| Action | Scope |
|---|---|
| `report:evidence_line_items_materialised` | Forward materialisation — **one row per document** (counts, ids, hashes only) |
| `report:evidence_line_items_backfilled` | **One summary row per backfill run** (dry-run flag, counters, divergence count) |
| `report:evidence_line_items_divergence_detected` | Per item, only when an ordinal’s hash diverges |

Audit payloads never contain line values, document contents or signed URLs. Audit is best-effort and must never
break materialisation; the run report records the audit outcome. Volume rationale recorded as B2-D5.

---

## 16. Test / verification plan (V2)

* **Static/migration:** additive-only assertions (one new table; `ADD COLUMN IF NOT EXISTS` on the two expected
  tables; `SET NULL` consumer FKs; no `DROP`/`ALTER TYPE`/`RENAME`/`UPDATE`/`DELETE`; B1 migration files
  unchanged).
* **Pure unit:** eligibility, recognised-key derivation, `raw_*` mapping, canonical `payload_hash`
  (numeric-representation and key-order invariance), ordinal gaps, `DO NOTHING` decisions, divergence
  classification.
* **Runtime (database-backed, mandatory — a green static suite is *not* verification: the V1 lesson):** the **20**
  runtime acceptance tests in the contract §20.2, covering materialisation order/count, idempotent rerun,
  identical-duplicate distinctness, gaps, no-`line_items`, empty array, snapshot linkage, flat-document NULL,
  multiple calculations per line, divergence, forward-then-backfill, RLS ALLOW/DENY, privilege denial,
  historical immutability, evidence linkage, audit emission, no-re-extraction and migration idempotency.
* **Clone harness (V1R method, adapted):** privileges-inclusive clone — table-level grants/policies/RLS
  identical for the 116 pre-existing tables, rows byte-identical, and only the declared delta present
  (1 new table; 2 new columns on pre-existing tables; 5 new FK constraints — 3 declared inside the new table
  + 2 on pre-existing tables; 4 explicit new indexes plus 1 constraint-backed unique index; 2 policies;
  no trigger); re-apply → `rc=0`, zero diff. *(Figures aligned to the ratified contract §20.3 —
  `CT-P8-B2-AUTHORISATION-CONTRACT-CORRECTION-20260913-021`.)*
* **Regression:** the whole existing suite green, and the B1 runtime suite green including F1–F5, tenant
  isolation, immutability, privilege posture and audit emission.
* **Mandatory B1 test amendments (contract §20.6):** amend — **never delete** — the two B1-scope negative
  assertions (`test_b2_b3_b4_boundary_untouched`, `test_no_b2_b3_b4_objects_in_the_repository`) so that the
  B3/B4 guards survive and the B2 assertions move into the B2 suite; the two migration-text guards stay valid.
* **Environment:** V2 requires a provisioned B1+B2 disposable clone (`INTEGRATION_DATABASE_URL`; the suite skips
  otherwise). **A skip is not a PASS** and must be reported as such.

## 17. Implementation boundary

**In scope for B2:** the two migrations; the new table's DDL/constraints/indexes/RLS/privilege posture;
materialisation logic (eligibility, derivation, canonical hash, ordinal rules); the insert-only repository plus
its read functions; the forward hook and the additive `extraction_method` keyword; the Class-1 backfill
operation (dry-run, batched, idempotent, run report, divergence detection) with its CLI entry point (execution
separately authorised); `CalculationRequest.source_line_item_id` + snapshot persistence + the ordinal resolve
in both calculation paths; `link_value_evidence(..., source_line_item_id=None)`; the three audit actions; the B2
tests, the §20.6 amendments and the clone harness; the B2 implementation and V2 reports.

**Out of scope (must not be absorbed):** P1 extraction fidelity / OCR / AI-gate changes; historical re-parsing;
P2 EF-E; B3 (framework/requirement projections, applicability, intensity, per-gas, base year, drill-down
endpoints/UI); B4 (narrative, finalisation, frozen artefact); Phase 8-X; broad production RLS remediation;
legacy report route (D16); subscription/allowance; end-to-end customer evidence; full ESRS/CSRD content;
fixing F-B2-7 or F-B2-4; retention execution (N3); any frontend change; production migration/deployment.

## 18. Decisions (12) — CLOSED / PO-RATIFIED

All twelve were **CLOSED by the Product Owner** in `CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018`
(B2-D1…B2-D12); **none blocks implementation**. The authoritative wording is the ratification record §3 and the
contract §23 — the table below records the ratified outcome for each.

| # | Decision | Ratified outcome | Blocks B2? |
|---|---|---|---|
| B2-D1 | `source_item_id` delete rule | **`ON DELETE RESTRICT` — preservation-first; `CASCADE` prohibited** | No |
| B2-D2 | Divergence/supersession policy | **detect + report + never rewrite** | No |
| B2-D3 | PE read access | **mirror the existing source-item boundary** (no new consultant model) | No |
| B2-D4 | F-B2-7 (`source_page` = page count) | **deferred to a separate bounded remediation workstream** — B2 does not fix, reinterpret, copy or propagate it | No |
| B2-D5 | Audit granularity | **per-document (forward) + per-run (backfill) + per-item divergence** | No |
| B2-D6 | Forward hook placement | **data-layer choke point** | No |
| B2-D7 | `extraction_method` vocabulary | **open — no restrictive CHECK** | No |
| B2-D8 | `row_reference` rule | **NULL for Class-1** (never `invoice_number`) | No |
| B2-D9 | New endpoint/UI in B2 | **none** | No |
| B2-D10 | Field deviation from design §14.3 | **accepted** — removed `document_type_code`, `confidence_score`, `extracted_at`, `extracted_by`, `processing_origin`; added/retained `materialisation_kind`, `created_at` | No |
| B2-D11 | Retention/deletion of evidence lines | **B2 introduces no retention/deletion mechanism** — N3 / the retention+privacy workstream remains separate | No |
| B2-D12 | Historical snapshot retro-linking | **none — no retro-linking** | No |

## 19. Risks (top)

R1 “B2 misread as the extraction fix / false traceability assurance” (High) · R2 materialisation drifting into a
second extraction engine · R3 ordinal identity drift under corrections (mitigated by divergence detection) ·
R4 historical NULL links read as a defect · R5 backfill audit volume · R6 hot-table column addition to
`calculation_snapshots` · R7 B1 guard tests deleted rather than amended · R8 verified only statically ·
R9 runtime suite skips and is reported as success · R10 scope creep into B3 · R11 wrong delete semantics ·
R12 denormalised `dve` divergence · R13 backfill reading `mapped_data` · R14 future retention blocked.
Mitigations are specified in contract §24.

## 20. Dependency / blocker matrix (summary)

**Prerequisites present/closed:** B1 foundation + correction; the D33 schema (`manual_extraction_items`,
`document_processing_queue`, `organization_files`); `work_item_effective_entity`/`is_entity_member`; the
calculation engine; `audit_trail` + P7; the application authorization guards.

**Not blockers:** P1 (parallel; B2 works without it — line population stays thin for flat PDFs), P2, B3/B4
(successors), G0-A (affects B3 seed rows only).

**Open / declared:**
1. **A provisioned B1+B2 database for runtime V2** — without it the runtime suite skips and V2 acceptance
   cannot be claimed (contract §18.5 recipe).
2. **G0-D — production migration strategy** — the 34 previously-outstanding migrations remain a production
   deployment blocker; B2 adds 2; **production is not authorised**.
3. The twelve B2-D* decisions (none blocking).

## 21. Verification of this task (what was actually checked)

| Check | Result |
|---|---|
| No source/schema/test/RLS file modified | Confirmed — only the two mandated documents were written |
| No migration created or applied | Confirmed — `supabase/migrations` untouched (57 files, same newest file) |
| No database mutation | Confirmed — read-only introspection only (SELECT against `information_schema`/`pg_policy`/`pg_constraint`) |
| Worktree undisturbed | Confirmed — no stage/commit/push/reset/clean/stash/checkout; 208 tracked mods and 73 untracked paths unchanged |
| Secrets | None introduced; no credentials, tokens or signed URLs appear in either document |
| Evidence tags | Every material claim in the contract carries **[R]/[V]/[D]/[I]/[REC]/[U]** |
| Deliverables | Architecture contract + this report, both complete |

## 22. Explicit verdict

**`B2 IMPLEMENTATION CONTRACT COMPLETE — READY FOR PO REVIEW`**

* All mandated deliverables (A–S of the task) are addressed with exact, testable specifications.
* Two environment/deployment items are declared openly (runtime provisioning; G0-D) rather than hidden.
* Twelve decision questions are surfaced with options, recommendations and consequences; **none blocks
  implementation**; five (B2-D1, B2-D2, B2-D3, B2-D4, B2-D11) are recommended for explicit PO resolution
  together with this review.
* No architectural contradiction with B1 was found. B1 remains CLOSED; its migration files are untouched; the
  two B1 test-scope consequences of B2 are bounded, named and prescribed (contract §20.6).
* Two previously unrecorded findings (F-B2-7 `source_page` = page count; F-B2-13 B1 boundary-test scope) were
  discovered by this analysis and are carried into the decision list rather than silently fixed.

**Stop condition respected:** nothing was implemented; no migration was created; no code was modified; no
production action was taken; no commit; no push.
