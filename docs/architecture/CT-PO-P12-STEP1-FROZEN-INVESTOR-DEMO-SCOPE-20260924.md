# CT-PO-P12-STEP1-FROZEN-INVESTOR-DEMO-SCOPE-20260924

**Reference:** `CT-PO-P12-STEP1-FROZEN-INVESTOR-DEMO-SCOPE-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924` — **STEP 1**, workstream **1.4**
**Status:** PROPOSED FROZEN SCOPE — for PO ratification
**Basis:** *actually verified* capability only (see the Workflow Independent Verification and EV-01 reports)
**Production deployment:** **NOT AUTHORIZED**

---

## 0. What "frozen" means here

This document freezes **which four stories the investor demonstration will tell, on
which real records, and with which limits disclosed**. It does **not** authorize
implementation, seeding or mutation. Anything marked **[STEP-2 REQUIRED]** does not
exist yet and must be created under a PO-authorized Step 2.

Two rules govern every story:

1. **No fabricated chain.** Every displayed link must resolve to a real record.
   Where a link is unavailable, the *script must say so*.
2. **No invented capability.** Only implemented and code-verified surfaces are used.

**Counting rule (per workplan §2.3):** all counts below are **planning targets, not
fixed counts**; final counts must be frozen during Step 1's *output* review and then
implemented in Step 2.

---

## 1. Story A — "CarbonTally calculates." (Normal calculation)

**Target chain:** `upload → extraction → mapping → validation → calculation → emissions result`

### A.1 Frozen artifact (exists today — `DATABASE-OBSERVED`, `VERIFIED`)

| Item | Value |
| --- | --- |
| Document | `t3imp_uk-gas__ORG_022_british_gas_202511.pdf` (3 pages, `application/pdf`, extraction method `onnx_ocr`) |
| Extracted data | `activity = "Natural gas"`, `quantity = 12181.4`, `unit = "kWh (Net CV)"`, supplier/date/invoice present |
| Status | `document_processing_queue.status = customer_review` (fully processed through the pipeline) |
| Mapping | factor `b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5`, `factor_source = DEFRA-DESNZ`, `factor_set = DEFRA-2025` |
| **Expected calculation** | `12181.4 kWh × 0.2027 kg CO₂e/kWh = 2469.169780 kg CO₂e` |
| Calculation record | `calculation_snapshots.id = af640887-5818-47ad-b351-1505ac049c32`; `methodology = direct_multiply`; `algorithm_version = v1.0`; `content_hash` present; `request_id = 2255f582-0329-5c7a-a929-9619b6467877` |
| Emissions result | `emissions_logs.id = eb88e764-b93a-4bd6-8b66-a24fd6e45ca9`; `calculated_kg_co2e = 2469.169780`; `scope = Scope 1`; `snapshot_id` FK present |
| Organisation | `3fd0f325-16a1-5b53-8fb8-27929cf218fa` |
| Provenance available | **document-level**: `source_item_id = 2b41b332-…`, `source_file`, `factor_id`, `factor_source`, `factor_kind`, `content_hash` |

The corpus contract independently expects this scenario to match
(`t3_manifest.json` → `uk-gas` → `EXPECTED_MATCHED`, factor `b9d1ed06…`) — i.e. the
frozen record is the *intended* outcome, not luck.

### A.2 UI states the script may show

| Screen | Must show |
| --- | --- |
| Document/upload list | the real file, its **organisation**, batch and status (`customer_review`) |
| Processing state | persisted pipeline stage/timestamps (`ingested_at`, `extracted_at`, `mapped_at`, `validated_at`, `calculated_at`, `review_ready_at`) — not a spinner |
| Calculation detail | quantity, unit, multiplier, methodology, algorithm version, content hash, snapshot id |
| Emissions result | `2469.169780 kg CO₂e`, Scope 1, date `2025-05-05` |

### A.3 Required records (all exist)

`organization_files` → `document_processing_queue` → `manual_extraction_items` →
`calculation_snapshots` → `emissions_logs`.

### A.4 **[STEP-2 REQUIRED]** for a *repeatable* Story A

| Requirement | Why |
| --- | --- |
| Re-process a document **with the current HEAD** so the calculation record is produced by current code | The frozen snapshot was written 2026-09-20, **before** the `F-B2-7` correction (`999e4fb`, 2026-09-22) |
| Have **≥ 2** successful matched calculations (not 1) | A single record is a thin demo; `uk-water` (`EXPECTED_MATCHED`, factor `fb9d28bf-…`) is the natural second |
| Do **not** present the legacy snapshot's `source_page = 3` as an exact page | It equals the document page *count*; `domain/evidence.py` correctly marks it `unverified` |

---

## 2. Story B — "CarbonTally operates." (Operational workflow)

**Target chain:** `work item → processing entity → assignment/reassignment → review/approval`

### B.1 Exact states that can actually be demonstrated

| State | Demonstrable today? | Evidence |
| --- | --- | --- |
| Work item in `pending` / `extracted` / `calculated` | **YES** | Demo Lab: `pending 2`, `extracted 11`, `calculated 1` |
| Work item **blocked for manual review with a real reason** | **YES** | 13 `manual_review` queue rows with persisted `manual_review_reason` |
| Work item in `customer_review` | **YES** | 1 row (`uk-gas`) |
| Entity **assignment** (`work_item_assignments`) | **NO** | `work_item_assignments = 0` |
| **Reassignment** | **NO** | `reassignment_history = 0` |
| **Partial release / completion (lease)** | **NO** | no lease rows |
| PE workspace showing assigned work | **NO** | no assigned items |
| Review / QC decision states | **NO** | no review/QC state populated |

### B.2 The workflow as implemented (`CODE-TRACED`)

```text
batch assignment      POST /api/v3/ops/batches/{batch_id}/assign
item lease lifecycle  POST /api/v3/ops/items/{id}/work/claim | assign | reassign
                           | recover | release | complete
PE-side lifecycle     POST /api/v3/pe/items/{id}/work/claim | release | complete
review assignment     POST /api/v3/ops/review/{review_id}/assign | complete
QC                    POST /api/v3/ops/items/{id}/qc ; /api/v3/ops/qc/ct-queue
                           ; /api/v3/ops/qc/items/{id}/decision
PE review/QC          POST /api/v3/pe/items/{id}/pe-review | pe-qc
persistence           public.work_item_assignments (+ processing_assignments,
                      reassignment_history, review_assignment_history)
```

### B.3 Boundary the script **must** state honestly

Assignment and reassignment are **internal Operations ↔ Processing Entity** work
distribution. **Customer users do not assign work**, and there is **no
customer↔PE messaging plane** (D18 is absolute). The script must not imply that a
customer assigns work to a supplier/processor.

### B.4 **[STEP-2 REQUIRED]** for Story B

| Requirement | Count target |
| --- | --- |
| Work items assigned to a processing entity | ≥ 4 |
| Distinct assignment states to show | assigned, in-progress (claimed), released, completed |
| At least one **reassignment** with a real `reassignment_history` row | ≥ 1 |
| At least one **partial release** | ≥ 1 |
| Two processing entities (so PE A ≠ PE B is visible) | 2 |
| PE manager + PE staff identities | 1 + 1 |
| Review/QC state on at least one item | ≥ 1 |

**Current Demo Lab topology supports this**: `processing_entities = 1` and the
harness manifest already declares `pe.manager` (entity-scoped `pe_manager`) — so
Step 2 must add a **second** entity for the isolation story.

---

## 3. Story C — "CarbonTally explains." (Explainability)

**Target chain:** `emissions number → calculation snapshot → factor → source document → evidence → Insight explanation`

### 3.1 Link-by-link freeze (what is real **today**)

| Link | Real today? | Record |
| --- | --- | --- |
| **Emissions number** | **YES** | `2469.169780 kg CO₂e` (`emissions_logs.eb88e764…`) |
| **→ Calculation snapshot** | **YES** | `snapshot_id → af640887…` |
| **→ Factor** | **YES** | `factor_id = b9d1ed06…`, `factor_source = DEFRA-DESNZ`, `factor_set = DEFRA-2025`, `factor_kind = emission_factor` |
| **→ Methodology / version / hash** | **YES** | `direct_multiply`, `v1.0`, `content_hash`, `request_id` |
| **→ Source document** | **YES (document-level)** | `source_item_id = 2b41b332-…` → extraction item → `organization_files` record; the Viewer issues a signed URL at FULL depth only |
| **→ Exact source page/row** | **NO** | `source_line_item_id = NULL`; stored `source_page = 3` is a page **count** and is correctly classified `unverified` |
| **→ Evidence line item** | **NO** | `evidence_line_items = 0` (EV-01) |
| **→ Source Evidence Viewer** | **NO** | the route resolves by `line_item_id` and there is no line id to resolve |
| **→ Insight explanation** | **NO — BLOCKED** | **no Insight tables exist** in the Demo Lab (or any candidate environment) |

### 3.2 Frozen wording for the demonstration

> *"CarbonTally can trace this number back to its calculation snapshot, the exact
> emissions factor and factor set used, the algorithm version and content hash, and
> the source document it came from. The per-line evidence viewer and the Insight
> explanation are the next layer; they are enabled once the environment carries the
> line-level evidence records and the Insight schema."*

**Under no circumstances** may the demo imply that a line-level evidence chain is
currently populated.

### 3.3 **[STEP-2 REQUIRED]** for the full Story C

| Requirement | Authorization needed |
| --- | --- |
| At least one **genuinely tabular** source document (CSV/XLSX) processed through the real pipeline, so `extracted_data.line_items[]` exists and the forward hook materialises `evidence_line_items` rows | PO decision (EV-01 Option A) — see EV-01 §E |
| Alternatively: P1 controlled rollout (`CARBONTALLY_P1_EXTRACTION_SHAPE=enabled` + allowlist) scoped to the demo org for PDFs | PO decision (EV-01 Option B) |
| Insight schema present (all six `2026100*` migrations applied to the demo environment) | Step-2 environment authorization |
| ≥ 2 evidence line items with a resolvable `calculation_snapshots.source_line_item_id` | follows from the above |
| Insight data-quality/reproducibility answer states operable | P3 has **no UI renderer** — presenter-side API/tool demonstration must be agreed, or P3 excluded from the visual narrative |

**Note:** P2 (temporal comparison) and P3 (data quality/reproducibility) also require
their migrations to be applied before they can be shown at all.

---

## 4. Story D — "CarbonTally is honest about uncertainty." (Honest failure)

**Target:** `unsupported/ambiguous document → explicit reason → appropriate human action`

### 4.1 Real, persisted failure scenarios (all exist **today** — `DATABASE-OBSERVED`, `VERIFIED`)

The Demo Lab's 13 blocked documents already carry **specific, honest, human-readable
reasons** in `document_processing_queue.manual_review_reason`. Four distinct failure
*classes* are available, which is more than the story needs:

| # | Class | Real document | Persisted reason (verbatim) | Appropriate human action |
| --- | --- | --- | --- | --- |
| **D-1** | **Unsupported / no usable text** | `ohd079-invalid-probe.txt` (and `scope2_water_plus_commercial_invoice.pdf`) | `extraction no_text: no usable text extracted (blank page, or image too low quality)` | Operator supplies a readable source or marks the document unsupported; the system does **not** invent values |
| **D-2** | **Ambiguous mapping** | `t3imp_uk-electricity__ORG_027_octopus_energy_202510.pdf` | `mapping could not auto-resolve: line 1: no confident factor for 'Electricity' kWh (status=ambiguous…)` | Human selects/confirms the factor; no silent choice is made |
| **D-3** | **No matching factor / clarification required** | `t3imp_uk-waste__ORG_018_biffa_waste_202601.pdf` | `mapping could not auto-resolve: line 1: clarification required for 'Waste' (the activity …)` | Resolution via the clarification route (`/api/v3/ops/items/{id}/clarify`, `/api/v3/pe/items/{id}/clarify`) |
| **D-4** | **Insufficient data (completeness gate)** | `t3imp_uk-missing-evidence__ORG_018_national_rail_202509.pdf` | `extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit` | Operator completes the missing fields in the workspace, then re-runs validation/calculation |

Additional corroboration from the corpus contract (`t3_manifest.json`):
`uk-waste` is declared `EXPECTED_NO_MATCH`, `uk-spend` is declared `UNSUPPORTED_PDF`,
and six scenarios are declared `EXPECTED_AMBIGUOUS` — i.e. these are **intended**
honest-failure cases, not incidental breakage.

### 4.2 Frozen Story-D choice

**Recommended primary: D-2 (ambiguous mapping) with D-4 (insufficient data) as the
second beat.**

Rationale: D-2 shows the platform *refusing to choose* an emission factor — the
strongest honesty signal for an investor audience — and D-4 shows a **quantified**
completeness gate (`0.33 below 0.50`) rather than a vague error. D-1 is the fallback
if the audience is non-technical.

### 4.3 What the script must claim — and must not

| May claim | Must not claim |
| --- | --- |
| The document was processed and **blocked with a specific reason** | that processing "succeeded" |
| The reason names the exact unresolved field(s) or the ambiguity status | that a human already resolved it |
| A human action route exists (clarify / complete / reassign) | that the system guessed a factor |
| Nothing was written to emissions | that a partial emissions figure exists |

### 4.4 Honest-failure scenario that is **NOT** available today

| Scenario | Status |
| --- | --- |
| **Insight "no-data" answer** (e.g. asking for a period with no records → `no_data` / `zero` / `insufficient_data`) | **BLOCKED** — no Insight tables exist in any candidate environment. This is the workplan's expressly desired failure case and **requires Step 2** before it can be used |

---

## 5. Record-level requirements per story (consolidated)

| Story | Records that must exist | Exists today? |
| --- | --- | --- |
| **A** | ≥ 2 matched calculations with snapshot + emissions log + factor provenance | **PARTIAL** (1 of 2) |
| **B** | ≥ 4 work items, ≥ 2 entities, assignment + reassignment + partial release + review/QC states | **NO** |
| **C** | 1 traceable calculation chain; ≥ 2 `evidence_line_items` linked to snapshots; Insight schema + operable tools | **NO** for the last mile |
| **D** | ≥ 2 blocked documents with real reasons (already present) + **1 Insight no-data case** | **PARTIAL** (D-1…D-4 yes; Insight no-data no) |

---

## 6. Security / DENY requirements frozen for the demonstration

These must be **demonstrated**, not merely asserted (workplan requirement 12 and
AGENTS.md §45). Each is `DENY` unless stated otherwise.

| # | Case | Expected |
| --- | --- | --- |
| S-1 | Org A owner → Org B organisation data | **DENY** |
| S-2 | Client A owner → Client B data | **DENY** |
| S-3 | Consultant → an organisation it holds **no** active grant for | **DENY** |
| S-4 | Consultant → its own client organisation | **ALLOW** (positive control) |
| S-5 | PE Alpha → PE Beta work item | **DENY** |
| S-6 | PE staff → customer document/source evidence | **DENY** |
| S-7 | Customer org member → `/api/v3/pe/*` | **DENY** |
| S-8 | Customer org member → `/api/v3/ops/*` (internal operations) | **DENY** |
| S-9 | `viewer` → write (approve/assign/upload) | **DENY** |
| S-10 | `member` → owner/admin-only surface (e.g. audit) | **DENY** |
| S-11 | Customer → internal admin control plane | **DENY** |
| S-12 | Any tenant → the Insight tools of another tenant | **DENY** |
| S-13 | Evidence-line read below FULL DM-6 depth → exact source location | **RESTRICTED** (withheld, not nulled; honest message) |

The Demo Lab harness already encodes 30 authorization probes and 18 isolation rules;
the last recorded run reported **0 failures** (§9.2 of the IWV report). Step 2 must
**re-run** them against the frozen environment and add the S-1…S-13 cases that the
harness does not already cover.

---

## 7. Frozen planning targets for the Step-2 demo topology

**Planning targets only — not fixed counts** (workplan §2.3). They must be confirmed
at Step-2 authorization.

### 7.1 Environment

| Item | Frozen requirement |
| --- | --- |
| Canonical demo environment | **The Demo Lab** (`carbontally_demo_local`) — *not* the `postgres` flagship dataset (which cannot host the evidence chain at all, D-03) |
| Database identity | `carbontally_demo_local` only; hard name guard already implemented in the tooling |
| Repository/release identity | `p8-release-reconciled` @ the commit frozen at Step-2 authorization; **the release-identity ambiguity D-14 must be resolved first** |
| Migration state | **All** `supabase/migrations/*.sql` applied, explicitly including `20261001000000`, `20261002000000`, `20261003000000`, `20261005000000`, `20261006000000`, `20261007000000` |
| Safety checks | prove-not-production; record target identity; record pre-state; establish reset scope; establish rollback/recovery |
| Schema-revision record | a persisted record of the applied migration set (fixes D-08) |

### 7.2 Identities (planning targets)

| Persona | Target count | Notes |
| --- | --- | --- |
| Direct customer organisations | 2 | Org A, Org B (exist) |
| Roles per direct organisation | owner, admin, member, viewer | exist for Org A; Org B has owner + viewer |
| Consultant firm | 1 | exists (2 firm members) |
| Client organisations | 2 | Client A, Client B (exist) |
| Processing entities | **2** | only 1 exists today — a second is required for the PE-isolation story |
| PE manager / PE staff | 1 + 1 | `pe.manager` exists in the manifest |
| Internal roles | operator, reviewer, QC, staff admin | manifest declares platform admin + operator |
| Legacy/audit identities | as required by the harness | — |

### 7.3 Data (planning targets)

| Entity | Target |
| --- | --- |
| Batches | ~3 |
| Work items | ~12–15 across meaningful states |
| Matched calculations (snapshot + emissions log) | **≥ 2** |
| Blocked documents with real reasons (Story D) | **≥ 2** |
| **Tabular document producing `line_items[]`** | **≥ 1** (the EV-01 unlock) |
| `evidence_line_items` | **≥ 2** |
| Assignments | ≥ 4 (assigned / in-progress / released / completed) |
| Reassignments | ≥ 1 real `reassignment_history` row |
| Report versions | 2 with **different lifecycle states** (today all are `DRAFT`) |
| Conversations | covering the organisation plane **and** the PE-operational plane |
| Insight interactions | 2 real + **1 honest no-data case** |
| Master data | ≥ 1 facility, ≥ 1 asset, ≥ 1 supplier (so CRUD and relationships are visible) |
| Scope-1 data across two periods | required only if P2 temporal comparison is shown |

---

## 8. Explicitly out of scope

Unchanged from the workplan: production readiness/deployment; audit/certification;
Scope 3 Categories 1–15 completeness; market-based Scope 2; Scope 1 decomposition;
supplier intelligence; reduction/decision intelligence; general natural-language
querying; RAG; billing completion; **L7**; **L8**; unrestricted product/UI expansion.

Additionally out of scope for the demonstration's *claims*:

- a customer ↔ PE messaging plane (does not exist and must not be implied);
- any per-line evidence claim until Step 2 materialises real lines;
- any Insight answer until the Insight schema is applied;
- presenting the legacy snapshot's `source_page` as an exact location.

---

## 9. Verdict

**Frozen demo scope: COMPLETE (proposed), with three explicit [STEP-2 REQUIRED]
unlocks.**

| Story | Frozen? | Demonstrable today? |
| --- | --- | --- |
| **A — Normal calculation** | **FROZEN** | **Mostly** (1 real end-to-end record; ≥ 2 recommended) |
| **B — Operational workflow** | **FROZEN** | **No** — needs Step-2 assignment seeding; the boundary wording is frozen |
| **C — Explainability** | **FROZEN — with mandatory disclosure** | **Document-level only**; the evidence/Insight last mile requires Step 2 |
| **D — Honest failure** | **FROZEN** | **Yes** for document failures (D-1…D-4, with real persisted reasons); the Insight no-data case needs Step 2 |

The frozen scope is deliberately **smaller than the implemented capability** and
**exactly equal to the verifiable capability plus the three named unlocks**. No
capability is claimed for the demonstration that was not verified in Step 1.
