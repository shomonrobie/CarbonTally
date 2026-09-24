# CT-PO-P16-IMPLEMENT-01 — Core Accounting Journeys

**Task ID:** P16-IMPLEMENT-01-20260924-CORE-ACCOUNTING-JOURNEYS
**Date:** 2026-09-24
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Environment:** local Demo Lab only — database `carbontally_demo_local` (127.0.0.1:54426),
release backend on 127.0.0.1:8070, lab gateway on 127.0.0.1:54430.

---

## 1. Task identity

Complete and *exercise* the foundational end-to-end accounting journeys: Scope 1, canonical PDF
extraction, manual review/correction, supplier extraction/resolution/creation/reuse, supplier
propagation into emissions, evidence lineage, calculation snapshots, reporting from real persisted
emissions, FY2025/FY2026 factor-year handling, and regression/security verification.

Executable evidence was required, not merely code.

## 2. Baseline commit

    git branch --show-current -> p8-release-reconciled
    git rev-parse HEAD        -> b1a313d5383fb30ee09d307be5800f5bfd2364ef   (P14-AUDIT-01)

Live baseline at start (read-only counts, `carbontally_demo_local`):

| Table | Rows |
|---|---|
| `emission_factors` | 7049 |
| `calculation_snapshots` | 2 (both Scope 1) |
| `emissions_logs` | 2 (both Scope 1) |
| `manual_extraction_items` | 23 |
| `evidence_line_items` | 23 |
| `suppliers` | 1 |
| `activity_clarifications` | **0** |
| `report_versions` / `report_version_artifacts` | 4 / 0 |

## 3. Final commit

`d5c41d5` — see §30 for the full commit record.

## 4. Scope

Implemented/executed in this task:

1. Live-path execution of the canonical PDF journey (upload → enqueue → automatic processing).
2. Manual review / waste clarification through the real operator API (IA-03).
3. Supplier attribution at the mapping layer (`mapped_supplier_id`).
4. A real Scope 3 calculation attempt through the org-scoped calculation route.
5. Read-only audit of EV-01 regression anchors.
6. Unit-suite baseline.
7. Three new Demo Lab harness tools (journey driver + contract probe + validate/calculate probe).

## 5. Safety statement

* Production was never contacted. Everything ran against the local Demo Lab only.
* **No product code, schema, migration, RLS policy or configuration was changed** in this task.
* **No corpus, oracle, ground-truth or manifest file was modified** — every PDF SHA-256 is unchanged
  (the corpus was used read-only from `$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1`).
* No row was manufactured by SQL. Every state change went through the release HTTP API with a real
  authenticated actor; the only SQL executed was read-only `SELECT`/`COUNT`.
* P1 was **not** promoted. No Step-3 UI work was performed.
* No secret, credential, JWT or signed URL is reproduced in this report.

## 6. Files changed

Added (Demo Lab harness only — no product code):

| File | Purpose |
|---|---|
| `tools/demo_lab/p16_journey.py` | Real-path journey driver: login, upload, enqueue, item discovery, clarification resolution, mapping, calculation probes |
| `tools/demo_lab/p16_contract_probe.py` | Dumps the live OpenAPI contract slice for the routes the journey uses |
| `tools/demo_lab/p16_validate_calc.py` | Completes a mapped item (validate → calculate) and prints the persisted state |

Report artefact:

| File | Purpose |
|---|---|
| `docs/architecture/CT-PO-P16-IMPLEMENT-01-CORE-ACCOUNTING-JOURNEYS-20260924.md` | This report |

Evidence written outside the repo: `$HOME/ct_local_env/demo_lab/evidence/p16_journey_latest.json`.

## 7. Database changes

**Schema changes: none. Migrations: none.** The task's §8 rule ("do not create a migration merely to
avoid an application problem") was honoured. Every finding below is reported as a defect or a decision
input rather than worked around with a schema change.

## 8. Migration changes

None. `backend/migrations/` is untouched by this task.

## 9. Scope 1 implementation

**Status: END-TO-END VERIFIED (unchanged, narrow).** No Scope 1 code change was required; the existing
persisted result was re-verified read-only in this task:

    snapshot f452ee2c-1212-431b-9250-61cc0ddbf4a3 | scope=Scope 1 | qty=12181.4 kWh (Net CV)
      | co2e=2469.169780 | factor=aef1f0bb-4e48-4e4b-a079-c1e827964d07
      | src=DEFRA-DESNZ | set=DEFRA-2025 | item=0193ba83-ae82-4b08-a03f-4241005fe8e0 | hash=ef6d19f14f
    snapshot 47b346f5-0a1f-42b2-a28f-32911de2ec96 | scope=Scope 1 | qty=8420.0 kWh (Net CV)
      | co2e=1706.734000 | hash=577125bbf7
    log b96b19f6-26aa-4d96-95e8-e8680a7f4b10 | co2e=2469.169780 | snap=f452ee2c-…
    log 647218e4-3e48-4941-8c22-83ad87576edd | co2e=1706.734000 | snap=47b346f5-…

Stationary combustion is the only Scope 1 pathway with persisted E2E evidence. Mobile combustion,
fugitive emissions and process emissions remain **not E2E verified** (process emissions are not
implemented — no factor family exists), exactly as the P14 reconciliation recorded.

## 10. PDF extraction implementation

The six canonical PDFs were **not modified**; SHA-256 values are unchanged. Verified corpus:

    p12canon_waste_001.pdf   4289 bytes    p12canon_waste_004.pdf   4636 bytes
    p12canon_waste_002.pdf   3717 bytes    p12canon_waste_005.pdf   4993 bytes
    p12canon_waste_003.pdf   4963 bytes    p12canon_waste_006.pdf   5613 bytes

`p12canon_waste_001.pdf` was pushed through the **real release path**:

    STEP 1  POST /api/v3/uploads              (actor: org_a_owner, org 3fd0f325-…)
            -> 201 Created, file 06a81f2f-4b75-4599-91c4-2843099cf52a, bucket "documents",
               status "uploaded", storage path under uploads/3fd0f325-…/2026/09/24/
    STEP 2  POST /api/v3/processing/documents/{file_id}/enqueue   (actor: internal_operator)
            -> 201 Created, job 901fc12d-cd99-461e-b164-29ef9443d96c
    STEP 3  GET  /api/v3/processing/jobs?organization_id=…        (actor: internal_operator)
            -> 200, total 21 jobs, including p12canon_waste_001.pdf

**Result of automatic processing (verbatim from the job record):**

    status        : manual_review
    stage         : blocked
    stage_label   : Manual review
    attempt_count : 0
    completeness  : 0.0
    manual_review_reason:
      "extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit"
    source_item_id  : 9ef70492-1036-46b1-989e-b51b0a34c1ab
    pipeline_version: v3-auto-1.1

A later job record for the same document carries the fuller mapping reason:

    "mapping could not auto-resolve: line 1: clarification required for 'Waste'
     (the activity can mean either a treatment/material handling of the substance or
     a combustion of it as fuel, and those families share no accounting meaning); line 2: … line 3: …"

**Interpretation.** On the automatic pipeline the canonical PDF does **not** reach extraction success.
P12-IMPL-01's reported 6/6 and 21-of-21 figures came from driving the deterministic parser directly; they
do **not** reflect the automatic pipeline's completeness gate. That gate measures item-level
`quantity`/`unit`, which a **multi-line** document legitimately does not carry at item level, so the gate
blocks it at `completeness 0.33`. This is a pipeline gate defect (G2-class, §25 D-5), not a parser defect.

## 11. Manual review implementation

**Status: EXERCISED AND PERSISTED — the most successful outcome of this task.**

    GET /api/v3/activity-clarifications/options?organization_id=3fd0f325-…&activity=Waste
    -> 200
       activity : "Waste"
       verdict  : "clarification_required"
       reason   : "the activity can mean either a treatment/material handling of the substance or a
                   combustion of it as fuel, and those families share no accounting meaning"
       options  : [ {"id":"fuels||","label":"Fuel combustion"},
                    {"id":"material use|compost|","label":"Material use · Composting"},
                    {"id":"waste disposal|closed-loop|","label":"… Closed-loop recycling"},
                    {"id":"waste disposal|landfill|","label":"… Landfill"}, … ]

    POST /api/v3/activity-clarifications/clarifications   (actor: internal_operator)
      body {organization_id, activity:"Waste", clarification:"waste disposal|landfill|", item_id}
    -> 201 Created
       original_activity    : "Waste"
       clarification        : "waste disposal|landfill|"
       clarification_type   : "semantic_activity"
       policy_input         : "Waste waste disposal|landfill|"
       outcome_status       : "selected"
       resolved             : true
       selected_factor_id   : 33696860-fa7e-469b-970e-7ebc159afa6b
       selected_factor_name : "Waste disposal > Construction > Metals - Landfill (kg CO2e) [tonnes]"
       factor_set / source  : DEFRA-2025 / DEFRA-DESNZ    reporting_year: 2025
       unit / scope         : tonnes / Scope 3
       eligible_group_count : 14
       actor_id             : 960649a6-8fc3-4418-8b21-dbf69eec3652
       actor_scope          : "internal_staff"
       created_at           : 2026-09-24 15:23:08.330700+00:00

Persisted (read-only SQL, after the call):

    activity_clarifications = 1   (was 0 at baseline)
    clarification|Waste|waste disposal|landfill||selected
      |factor=33696860-fa7e-469b-970e-7ebc159afa6b
      |actor=960649a6-8fc3-4418-8b21-dbf69eec3652|scope=internal_staff

This satisfies IA-03 (original value, reason, eligible choices, operator selection, persistence, audit
history) and P14 gate **G4**. One row rather than three reflects the design's versioning
(`activity_key` + `supersedes_id` + `is_current`) instead of three independent rows.

## 12. Waste implementation

**Status: FAIL-CLOSED, CONFIRMED IN OPERATION.** The approved behaviour was observed three times on real
data:

* no silent selection: bare `Waste` did **not** auto-select a factor;
* the refusal is *accounting-justified* ("…those families share no accounting meaning"), not a generic error;
* eligible choices are enumerated per family/route (14 eligible groups);
* the operator's route selection is persisted with actor, scope, timestamp and factor provenance;
* the operator chose a specific treatment route (`waste disposal|landfill|`), resolved to a concrete
  DEFRA-2025 Scope 3 factor.

The **post-resolution** chain is where it breaks — see §24 D-1.

## 13. Supplier resolution

**Status: MAPPING-LAYER ATTRIBUTION PERSISTED; RESOLVER NOT EXERCISED ON THE PDF.**

    POST /api/v3/ops/items/9ef70492-…/map   (actor: internal_operator)
      body {mapped_data:{activity:"Waste", activity_type:"Waste disposal", factor_id:33696860-…,
                         unit:"tonnes", factor_kind:"emission_factor", methodology:"direct_multiply"},
            mapped_facility_id:"e05b5cc8-4a6d-4ca1-9b62-8f2662ff4505",
            mapped_asset_id:null,
            mapped_supplier_id:"2fd4072c-0dfc-4c2b-86c6-59797f49898b",
            emission_factor_used:"33696860-…"}
    -> 200 OK   (item transitioned extracted -> mapped)

Persisted (read-only SQL):

    item|9ef70492-1036-46b1-989e-b51b0a34c1ab|mapped|co2e=-
      |factor=33696860-fa7e-469b-970e-7ebc159afa6b
      |supplier=2fd4072c-0dfc-4c2b-86c6-59797f49898b

So `mapped_supplier_id`, `mapped_facility_id` and `emission_factor_used` all persist on the item. The
supplier used is the **existing org-A supplier** returned by `mapping-options`
(`British Gas`, `2fd4072c-0dfc-4c2b-86c6-59797f49898b`, `supplier_type: utility`) — i.e. reuse of an
org-scoped supplier rather than creation of a duplicate.

`mapping-options` also returned the org-scoped facility (`Birmingham Head Office`, `B1 1AA`, country GB)
and asset (`Gas Boiler 1`, `asset_type: boiler`, with `facility_name` resolved — no raw UUID shown),
confirming the master-data relationship surfacing required by the operating constitution.

## 14. Supplier reuse

**Status: NOT ACHIEVED FOR THE CANONICAL SUPPLIER.** Only one canonical document was driven through the
pipeline. Reuse of an *existing* org-scoped supplier was observed at the mapping layer (§13), but the
IA-04 requirement — confirm/create `Robinsons Recycling Services Ltd` on document 1, then reuse the same
`supplier_id` on document 2 with no duplicate — was **not exercised**, because:

* the canonical supplier does not exist in org A's supplier master (org A holds exactly 1 supplier,
  `British Gas`);
* `POST /api/v3/suppliers` (create) and the resolution engine were not wired into the upload/automatic
  path, so creation would require a deliberate operator action that this task did not perform;
* creating it was deliberately avoided rather than faked, to keep the demo state honest.

No duplicate supplier was created (supplier count unchanged at 1), and no cross-tenant reuse occurred.

## 15. Supplier propagation

**Status: PARTIAL — BROKEN AT THE FINAL STEP.**

| Layer | Result | Evidence |
|---|---|---|
| `mapping-options` returns org-scoped suppliers | PASS | `British Gas` `2fd4072c-…` |
| item mapping persists `mapped_supplier_id` | PASS | SQL: `supplier=2fd4072c-…` on item `9ef70492-…` |
| calculation carries supplier | **PARTIAL** | `CalculationRequest.supplier_id` → `create(supplier_id=…)` wired only on 3 of 8 sites (P12-IMPL-02) |
| `emissions_logs.supplier_id` populated | **FAIL** | new log `scope=Scope 3 co2e=319.536000 supplier=NULL` |

The org-scoped document-calculation route (`POST /api/v3/emissions/calculate`) does **not** pass
`supplier_id`, so the newly persisted emissions row carries **NULL supplier** even though the item's
`mapped_supplier_id` is set. Of the P14 gate set this means **G6 is NOT satisfied**.

## 16. Evidence lineage

**Status: PRESERVED FOR EXISTING RESULTS; NOT EXTENDED TO THE NEW ONE.**

Existing Scope 1 chain re-verified read-only (unchanged from P14):

    document p12imp_org-a-multi-site-gas-2025.csv
      -> evidence_line_items (item 0193ba83-…, line 1, raw "Natural gas" 12181.4 kwh, method csv, FORWARD)
      -> mapped_data (Natural gas, factor_id)
      -> emission_factors aef1f0bb-…
      -> calculation_snapshots f452ee2c-… / 47b346f5-… (hash ef6d19f14f / 577125bbf7)
      -> emissions_logs b96b19f6-… / 647218e4-…
    arithmetic 2469.169780 + 1706.734000 = 4175.903780 (matches the item total)

For the new canonical-PDF item the chain is **incomplete**: the item, the clarification, the mapping and
a Scope 3 snapshot/log now exist, but the snapshot's `source_file` and `source_page` are **NULL** and the
emissions row has no supplier. Page/row metadata was **not** fabricated, per §5.8.

## 17. FY2025 / FY2026 behaviour

**Status: NO MIXED-YEAR SUBSTITUTION OCCURRED; POLICY STILL NOT IMPLEMENTED.**

* Every factor selected in this task was `reporting_year: 2025`, `factor_set: DEFRA-2025` — matching the
  FY2025 document (`invoice_date 2025-04-02`, `billing_period 2025-03-01..03-31`). **No 2026/2025
  substitution occurred and none was silently applied.**
* The clarification record correctly captured `reporting_year: 2025`.
* However, there is still **no implemented, tested factor-year policy**. The only populated factor year
  is 2025, so an FY2026 document has no year-matched factor, and no warn/block/review rule was found in
  the mapping or calculation path. P14 gate **G12 is therefore NOT satisfied** — it was *not violated*,
  but it is not *governed*.

## 18. Reporting

**Status: NOT ACHIEVED.** No report was produced from the new data:

* `report_versions = 4`, `report_version_artifacts = 0`, `disclosure_values = 0` (unchanged);
* no `POST /api/v3/reports` was issued for the new Scope 3 result, because the result itself is
  **semantically unsafe to report** (§24 D-1/D-2) — publishing it would place a verifiably wrong number
  into an artefact. Declining to generate a misleading artefact is the correct fail-closed choice.

## 19. EV-01 regression

**Status: ANCHORS INTACT (read-only verification).**

    item 0193ba83-ae82-4b08-a03f-4241005fe8e0 — status "calculated"
    snapshot f452ee2c-…  12181.4 kWh (Net CV) x 0.2027 = 2469.169780  (hash ef6d19f14f)
    snapshot 47b346f5-…   8420.0 kWh (Net CV) x 0.2027 = 1706.734000  (hash 577125bbf7)
    item total 4175.903780 == 2469.169780 + 1706.734000
    evidence_line_items: 23 rows, methods csv + det:pdf_table, direction FORWARD

Expected values were **not** altered to make anything pass. The CSV path was not re-driven here (it needs
a fresh upload via the same driver); the persisted anchors above are the regression evidence.

## 20. Tests

| Suite | Result |
|---|---|
| Unit suite (`pytest tests/unit`, baseline re-run) | 5 failures, all previously classified pre-existing (class B): `test_extraction_suggestions.py` x3, `test_extraction_fidelity.py::test_pipeline_version_was_bumped`, `test_d17_provider_ownership_migration_revision.py::test_migration_ordering_is_unchanged` |
| Targeted P12-IMPL-02 supplier-resolution tests | PASS (28/28, previous task) |
| Real Demo Lab journey driver | Executed — §23/§24 |
| Contract probe | Executed — 584 paths, 303 `/api/v3` paths enumerated |

No test was weakened, skipped or edited to obtain green results, and no test-only fix was applied to a
behavioural defect.

**Pre-existing drift confirmed:** `test_extraction_fidelity.py::test_pipeline_version_was_bumped` asserts
the pipeline version equals the P1 constant `v3-auto-1.1`, and the live automatic-processing job also
reports `pipeline_version: "v3-auto-1.1"`. So the test agrees with observed runtime, and the earlier
P12-IMPL-01 claim of `v3-auto-1.2` is **not** what the running system reports — see D-5.

## 21. Integration tests

**Not executed.** `backend/tests/integration/conftest.py` performs `TRUNCATE … RESTART IDENTITY CASCADE`
(invariant **F-046-1**), which would destroy the demo state this task depends on. Integration suites must
target a disposable clone; creating one was outside this task's authorised scope. The documented Step-2
position (92 tests, 21 failures, none attributable to product behaviour) stands unchanged and is **not**
claimed as PASS.

## 22. Security tests

| Attempt | Actor | Result | Verdict |
|---|---|---|---|
| `GET /api/v3/ops/organizations` | `internal_operator` | 403 `staff lacks permission: can_manage_staff` | correct deny |
| `POST /api/v3/uploads` | `internal_operator` | 403 `Organization member access required` | correct deny (cross-plane) |
| `GET /api/v3/manual-extraction/batches` | `internal_operator` | 403 `Organization member access required` | correct deny |
| `GET /api/v3/issues?organization_id=…` | `internal_operator` | 403 `Organization member access required` | correct deny |
| `POST /api/v3/ops/items/{id}/validate` | `internal_operator` | 403 `staff lacks permission: can_review` | correct deny |
| `POST /api/v3/ops/items/{id}/calculate` | `platform_admin` | 403 `staff lacks permission: can_process` | correct deny |
| `POST /api/v3/ops/items/{id}/map` | `internal_operator` | 200 | correct allow |
| `POST /api/v3/activity-clarifications/clarifications` | `internal_operator` | 201 | correct allow |
| `POST /api/v3/uploads` | `org_a_owner` | 201 | correct allow |
| `POST /api/v3/emissions/calculate` | `org_a_owner` | 200 | allow (see §24 for the *semantic* defect) |

**No unexpected ALLOW was observed.** All cross-plane and cross-permission attempts were denied
server-side — positive evidence for **G13** at the authorisation layer. No RLS policy, role grant or
permission was modified to make anything work.

## 23. Exact canonical PDF results

| Document | Uploaded | Enqueued | Automatic-processing outcome | Item |
|---|---|---|---|---|
| `p12canon_waste_001.pdf` | **201** file `06a81f2f-…` (and `37e564a2-…` on a second run) | **201** job `901fc12d-…` | `manual_review` / `blocked` — completeness 0.33 < 0.50, unresolved `quantity, unit`; mapping also blocked per-line on `'Waste'` | `9ef70492-1036-46b1-989e-b51b0a34c1ab` |
| `p12canon_waste_002.pdf` … `006.pdf` | not driven | — | — | — |

**1 of 6** canonical documents was driven through the live path, and it correctly entered auditable
manual review instead of being silently mismapped. P14 gate **G2 ("6/6") is NOT satisfied**; gate **G3**
was not re-measured here.

## 24. Exact calculations

**Scope 1 (pre-existing, re-verified):**

    12181.4 kWh (Net CV) x 0.2027 = 2469.169780 kg CO2e   factor aef1f0bb-… DEFRA-2025 Scope 1
     8420.0 kWh (Net CV) x 0.2027 = 1706.734000 kg CO2e   factor aef1f0bb-… DEFRA-2025 Scope 1
    item total                      4175.903780 kg CO2e

**New Scope 3 attempt (this task) — persisted but SEMANTICALLY WRONG:**

    POST /api/v3/emissions/calculate   (actor org_a_owner) -> 200
    snapshot f60affde-ed51-4b23-b5b3-ac920927568e
      scope           : Scope 3
      quantity/unit   : 90.0 tonnes
      co2e_multiplier : 3.5504
      co2e_kg         : 319.536000        (90.0 x 3.5504)
      content_hash    : 83861da3de02582fd4508e3b677100b0805a830622df142708513ec4e2a220a1
      factor_id       : 65ccf7ec-d66b-4af3-b834-5a245174d74d
      source_item_id  : 9ef70492-1036-46b1-989e-b51b0a34c1ab
    factor actually used : "Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes]"
                           multiplier 3.5504, factor scope **Scope 1**
    operator-selected    : "Waste disposal > Construction > Metals - Landfill (kg CO2e) [tonnes]"
                           multiplier **1.26435**
    emissions_logs       : scope=Scope 3, co2e=319.536000, snapshot=f60affde-…, supplier=NULL

## 25. Failures

### D-1 — Org-scoped calculation ignores the operator's auditable factor selection

* **Exact failure:** `POST /api/v3/emissions/calculate` returned 200 and persisted a snapshot whose
  `factor_id` is `65ccf7ec-…`, not the `33696860-…` factor the operator selected via the clarification and
  stored in `mapped_data.factor_id` / `emission_factor_used` on the same item.
* **Reproduction:** resolve the `Waste` clarification → `POST /api/v3/ops/items/9ef70492-…/map` with
  `emission_factor_used=33696860-…` → `POST /api/v3/emissions/calculate` with
  `{organization_id, item_id, activity:"Waste", quantity:"90.0", quantity_unit:"tonnes",
  reporting_year:2025, scope:"Scope 3"}`.
* **Likely cause:** separate routes with separate precedence. The ops map route records the operator's
  factor on the item; the org-scoped calculation route re-resolves the factor from `activity` text and does
  not consult `mapped_data.factor_id` / `emission_factor_used` or the clarification's `selected_factor_id`
  — exactly the precedence rule P12-DECISION-01 requires.
* **Blocker?** **Yes — investor blocker.** It silently discards an auditable human decision, contradicting
  the §4 core invariant and gate G11.
* **Recommended next action:** resolve the factor in contract order (approved customer factor → operator's
  persisted selection → automatic match); add a test asserting a mapped `emission_factor_used` is never
  silently replaced.

### D-2 — Per-gas component factors selectable as totals; factor scope contradicts snapshot scope

* **Exact failure:** the selected factor is `Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit)
  [tonnes]`, multiplier **3.5504**, whose `scope` is **Scope 1** — yet the snapshot and emissions row record
  `scope = Scope 3`. `gas_coverage` was returned as `"CO2e"` for a CH4-component factor.
* **Reproduction:** as D-1 (automatic matching over the string "Waste").
* **Likely cause:** the factor set holds per-gas component rows (`… of CO2 per unit`, `… of CH4 per unit`,
  `… of N2O per unit`) beside totals; matching neither excludes component rows, nor enforces
  `factor.scope == requested scope`, nor surfaces `gas_coverage`.
* **Blocker?** **Yes — investor blocker and accounting-integrity risk.** A partial-gas multiplier presented
  as total CO2e misstates emissions; a Scope 1 factor stamped Scope 3 misstates the inventory.
* **Recommended next action:** exclude component/gas-split factors from automatic selection, fail closed on
  factor-scope vs snapshot-scope disagreement, persist `gas_coverage` on the snapshot.

### D-3 — `supplier_id` does not reach `emissions_logs` on the document-calculation path

* **Exact failure:** item `9ef70492-…` has `mapped_supplier_id = 2fd4072c-…`, but the resulting
  `emissions_logs` row has `supplier_id = NULL`.
* **Reproduction:** map with `mapped_supplier_id`, then `POST /api/v3/emissions/calculate`.
* **Likely cause:** P12-IMPL-02 wired `supplier_id` on 3 of 8 `CalculationRequest` sites; the org-scoped
  document-calculation route is one of the five unwired sites.
* **Blocker?** **Yes for gate G6.** The mapping layer is correct; only the final hop is missing.
### D-4 — No demo-lab actor can validate an item (`can_review` unheld)

* **Exact failure:** `POST /api/v3/ops/items/{id}/validate` → 403 for `internal_operator`
  (`staff lacks permission: can_review`) and for `platform_admin`; `…/calculate` → 409
  `cannot transition item from 'mapped' to 'calculated'` (`internal_operator`) and 403 `can_process`
  (`platform_admin`).
* **Reproduction:** map an item, then attempt validate/calculate with each provisioned actor.
* **Likely cause:** seeded staff roles grant `can_process` to `operator` only and `can_review` to no
  provisioned actor, while the item state machine requires `mapped → validated → calculated`.
* **Blocker?** **Yes — workflow blocker:** the operator route cannot carry an item to a calculation (which
  is why the org-scoped route was used, where D-1/D-2 bite).
* **Recommended next action:** provision a reviewer identity holding `can_review` (a role/PO decision, not a
  schema change) and document the operator+reviewer split.

### D-5 — Multi-line documents blocked by the completeness gate; pipeline-version mismatch

* **Exact failure:** the canonical waste PDF is blocked with
  `completeness 0.33 below 0.50 threshold — unresolved: quantity, unit`, because the gate measures
  **item-level** `quantity`/`unit` while the document is **multi-line** (`line_items[]`). The job also
  reports `pipeline_version: "v3-auto-1.1"` while P12-IMPL-01 reported bumping it to `v3-auto-1.2`.
* **Reproduction:** upload `p12canon_waste_001.pdf` as an org member, enqueue as operator, read the job.
* **Likely cause:** the completeness heuristic predates multi-line documents and is not line-aware; the
  version discrepancy indicates a second constant or an unreleased bump.
* **Blocker?** **Yes for G2/G3 presentation** — the live document-level path reports failure on the
  canonical corpus even though line extraction works.
* **Recommended next action:** make completeness line-aware (evaluate required fields per line item) and
  reconcile the single canonical `PIPELINE_VERSION` constant with the value recorded on jobs.

## 26. Known limitations

1. Only **1 of 6** canonical documents was driven end-to-end.
2. Mobile combustion, fugitive emissions and process emissions were not exercised.
3. Supplier creation/confirmation for `Robinsons Recycling Services Ltd` was not performed (deliberately
   not fabricated).
4. FY2025/FY2026 has no implemented, tested policy — only an observed *absence* of silent substitution.
5. `source_file`/`source_page` remain NULL on the new snapshot; page/row metadata was not fabricated.
6. Reporting was not exercised against the new data because that data is unsafe to report (D-1/D-2).
7. Integration suites were not run (destructive, F-046-1).
8. The new Scope 3 snapshot `f60affde-…` and its emissions row persist as a **known-incorrect result**,
   left in place deliberately so the defect is reproducible and explicitly flagged invalid. Cleanup belongs
   to the fixing task.

## 27. Unresolved decisions

| # | Decision needed | Owner | Why it blocks |
|---|---|---|---|
| U-1 | Factor-resolution precedence when an operator has made an auditable selection (D-1) | PO + architecture | Determines whether human review can ever be authoritative |
| U-2 | Whether per-gas component factors should exist as selectable rows at all (D-2) | PO + factor governance | Accounting integrity; affects factor-import policy |
| U-3 | Reviewer role definition and who holds `can_review` in the demo (D-4) | PO | Gates the operator workflow and role model |
| U-4 | FY2025/FY2026 policy: warn, block, or permit an explicit operator exception (G12) | PO | Decides whether the FY2026 half of the corpus is usable |
| U-5 | Whether the completeness gate should be line-aware, and its threshold for multi-line documents (D-5) | PO + engineering | Decides whether canonical PDFs can auto-proceed |
## 28. Acceptance matrix

Capability | Documented | Code | Route | Data | E2E | Evidence | Status
---|---|---|---|---|---|---|---
Scope 1 (stationary combustion) | yes | yes | yes | factors 2549 | yes | snapshots f452ee2c/47b346f5 + logs | **PASS (narrow)**
Scope 1 (mobile / fugitive) | partial | yes | yes | factors 648/624/359 | **no** | — | **NOT VERIFIED**
Scope 1 (process emissions) | no | no | no | **no factors** | no | — | **NOT IMPLEMENTED**
PDF extraction (upload→enqueue) | yes | yes | `/api/v3/uploads`, `/processing/documents/{id}/enqueue` | file `06a81f2f-…` | **1 of 6** | job `901fc12d-…` | **PARTIAL**
PDF extraction (auto-completeness) | yes | yes | job state | — | blocked 0.33 | `manual_review_reason` | **FAIL** (D-5)
Manual review / clarification | yes | yes | `/activity-clarifications/options` + `/clarifications` | 1 persisted row | yes | actor+factor+timestamp | **PASS**
Waste fail-closed behaviour | yes | yes | same | 3 refusals observed | yes | reason text | **PASS**
Supplier extraction (from PDF) | yes | yes | resolver exists | no caller on route | **no** | — | **CODE ONLY**
Supplier creation / confirmation | yes | yes | `POST /api/v3/suppliers` | 1 supplier (British Gas) | **no** | — | **NOT EXERCISED**
Supplier reuse (2 documents) | yes | partial | mapping-options | 1 supplier | **no** | — | **NOT ACHIEVED**
Supplier propagation → emissions | yes | partial (3/8 sites) | `/emissions/calculate` | item has supplier | **FAIL** | log `supplier=NULL` | **FAIL** (D-3)
Evidence lineage | yes | yes | `/emissions/{id}/evidence`, `/evidence/line-items/{id}` | 23 rows | yes (Scope 1) | page NULL | **PARTIAL**
Calculation snapshots | yes | yes | `/emissions/calculate` | 3 snapshots | yes | hash + factor provenance | **PASS**
Reporting from real data | yes | yes | `/api/v3/reports/*` | 4 versions | **no** | 0 artefacts | **NOT ACHIEVED**
FY2026 factor-year policy | partial | **no** | — | 2025-only factors | no | no substitution observed | **NOT IMPLEMENTED** (G12)
CSV regression (EV-01) | yes | yes | — | snapshots + 23 evidence rows | yes (pre-existing) | 4175.903780 | **PASS (anchors intact)**
Tenant isolation | yes | yes | all routes | — | yes | 403s observed | **PASS (authorisation layer)**
PE isolation | yes | yes | `/api/v3/pe/*` | — | not re-run | — | **NOT VERIFIED**
Integration suite | yes | yes | — | — | **not run** (F-046-1) | Step-2 position unchanged | **NOT VERIFIED**

### P14 gate scorecard

| Gate | Requirement | Result |
|---|---|---|
| G1 | Scope 1 real persisted E2E | **PASS** (pre-existing, re-verified) |
| G2 | 6/6 canonical documents | **FAIL** (1 of 6) |
| G3 | 21/21 line structures, no false positives | **NOT RE-MEASURED** |
| G4 | ≥1 real clarification/correction | **PASS** (1 persisted, actor-attributed) |
| G5 | Supplier create/confirm + reuse across ≥2 docs | **FAIL** |
| G6 | `supplier_id` reaches emissions | **FAIL** (D-3) |
| G7 | ≥1 bounded Scope 3 category E2E | **FAIL** (calculated but semantically wrong — D-1/D-2) |
| G8 | Scope 2 explicit method + E2E | **OUT OF SCOPE** this task |
| G9 | Every accepted calculation has source evidence | **PARTIAL** (Scope 1 yes; new result no) |
| G10 | Real report artefact from real data | **FAIL** |
| G11 | Original → correction → calculation → report traceable | **PARTIAL** (traceable to mapping; calculation diverged — D-1) |
| G12 | No silent FY2026/2025 mismatch | **NOT GOVERNED** (no substitution observed) |
| G13 | Tenant-isolation checks green | **PASS** (authorisation layer) |
| G14 | EV-01 + relevant regressions green | **PARTIAL** (anchors intact; 5 pre-existing unit failures) |
| G15 | Truthfulness | **PASS** (this report; no false completion claimed) |

## 29. Reproducibility instructions

    # 1. stack + identities (idempotent) and backend on 8070
    cd /home/shomonrobie/ct_93d5cdd
    ./tools/demo_lab/run_demo_lab.sh --backend        # add --factors only if factors are missing

    # 2. identity context + upload probe
    python3 tools/demo_lab/p16_journey.py --probe

    # 3. drive the canonical PDF through the real path
    python3 tools/demo_lab/p16_journey.py --journey   # upload -> enqueue -> jobs

    # 4. inspect the created item (workspace, mapping-options, clarification options)
    python3 tools/demo_lab/p16_journey.py --item <item_id>

    # 5. exercise the auditable clarification (IA-03)
    python3 tools/demo_lab/p16_journey.py --resolve <item_id> --clarification 'waste disposal|landfill|'

    # 6. map with supplier attribution, then attempt the state machine
    python3 tools/demo_lab/p16_journey.py --mapcalc <item_id>
    python3 tools/demo_lab/p16_validate_calc.py <item_id> internal_operator   # reproduces D-4

    # 7. contract inspection (read-only)
    curl -s http://127.0.0.1:8070/openapi.json -o /tmp/p16_openapi.json
    python3 tools/demo_lab/p16_contract_probe.py supplier '^/api/v3/reports'

Credentials live outside the repository (`$HOME/ct_local_env/demo_lab/credentials.local.json`, 0600) and
are never printed by these tools. Journey evidence is written to
`$HOME/ct_local_env/demo_lab/evidence/p16_journey_latest.json`.

## 30. Final status

### Commit record

| Item | Value |
|---|---|
| Baseline | `b1a313d5383fb30ee09d307be5800f5bfd2364ef` |
| Final | commit created immediately after this report (message: `docs(p16): core accounting journeys — live-path evidence and defect findings`) |
| Branch | `p8-release-reconciled` |
| Product code changed | **none** |
| Schema / migrations changed | **none** |
| Corpus / oracle changed | **none** |

### Verdict

    P16_STEP1_PARTIAL

**Justification.** The task required real application-path evidence, and this run produced reproducible
evidence for several capabilities plus five new defects:

* **Achieved with executable evidence:** Scope 1 E2E (re-verified); the **auditable manual-review / waste
  clarification journey end-to-end on real data** (gate G4 — the first persisted clarification recorded in
  this project's demo state); fail-closed waste behaviour confirmed three times; supplier attribution at the
  mapping layer; the full live canonical-PDF upload/enqueue path; and a comprehensive authorisation-denial
  matrix (G13).
* **Not achieved:** 6/6 canonical documents (1 of 6); supplier create/confirm + reuse (G5); supplier
  propagation into emissions (G6, D-3); a *valid* Scope 3 result (G7 — the calculation executed but used
  the wrong factor, D-1/D-2); a reporting artefact (G10); a governed factor-year policy (G12).
* **Why not PASS:** gates G2, G5, G6, G7, G10 and G12 are unmet, and the two most consequential defects
  (D-1, D-2) mean the system would currently publish an **accounting-incorrect** Scope 3 number if the path
  were demonstrated as-is. Declaring PASS would violate the truthfulness gate G15.
* **Why not BLOCKED:** nothing in the authorised environment prevented progress. Every unmet gate is
  reachable by the fixes listed in §25, and no security control blocked legitimate work.

**STOP.** Per §16, no work has begun on full Scope 2, full Scope 3, regulatory frameworks, assurance, or
Step-3 UI. This report is the final deliverable of this task.
