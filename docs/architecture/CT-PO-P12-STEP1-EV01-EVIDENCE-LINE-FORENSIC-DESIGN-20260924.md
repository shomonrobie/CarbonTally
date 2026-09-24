# CT-PO-P12-STEP1-EV01-EVIDENCE-LINE-FORENSIC-DESIGN-20260924

**Reference:** `CT-PO-P12-STEP1-EV01-EVIDENCE-LINE-FORENSIC-DESIGN-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924` — **STEP 1**, workstream **1.3** (EV-01)
**Known problem under investigation:** *"Current examined environments contained zero `evidence_line_items`."*
**Status:** FORENSIC / DESIGN STUDY — **read-only**
**Production deployment:** **NOT AUTHORIZED**

---

## 0. Authorization boundary

This study **identifies** a remediation. Identifying it **does not authorize**
implementing it. The workplan §1.3 states explicitly: *"No evidence implementation
is authorized by this workplan merely because the study identifies a gap."*
Evidence backfill is listed as **not authorized** by Step 1 (§7, §17.3).

No code, migration, RLS policy, seed row or database was modified. All database
access was read-only (`SELECT`/`count(*)`/catalog only).

---

## A. Observed state

### A.1 Demo Lab (`carbontally_demo_local`, `FACT`, `VERIFIED`)

| Object | Count |
| --- | --- |
| `public.evidence_line_items` | **0** |
| `public.disclosure_value_evidence` | 0 |
| `public.manual_extraction_batches` | 4 |
| `public.manual_extraction_items` | 14 |
| `public.document_processing_queue` | 14 (13 `manual_review`, 1 `customer_review`) |
| `public.calculation_snapshots` | 1 |
| `public.emissions_logs` | 1 |
| `public.emission_factors` | 7,049 |

Extraction-item status distribution: `pending 2`, `extracted 11`, `calculated 1`.

**The decisive observation.** Of the 14 items, 12 carry a non-null
`extracted_data`; **none** carries a `line_items` key:

```text
"items_with_line_items_array" = 0
"no_extracted_data"           = 2      -- the 2 'pending' items
jsonb_typeof(extracted_data->'line_items') = NULL   -- for every row
```

The complete key set actually present across all populated items:

```text
activity, date, gross_amount, invoice_number, net_amount, quantity, supplier, unit
```

— i.e. a **flat, single-activity payload**, not a line array.

The one processed document carries queue metadata proving the extraction saw a
multi-line document but emitted a flat payload:

```text
document_processing_queue d868e0d7…  (status customer_review, ai_extraction_method onnx_ocr)
metadata.p1_coverage = {
  "mode": "shadow",
  "multi_line_suspect": true,
  "candidate_lines": 2,
  "page_count": 3,
  "page_resolution": "document"
}
```

The single calculation snapshot (`af640887…`) therefore has:

```text
activity = Natural gas   quantity = 12181.4   unit = kWh (Net CV)
co2e_multiplier = 0.2027  co2e_kg = 2469.169780   methodology = direct_multiply
factor_source = DEFRA-DESNZ   request_id = 2255f582-…
source_item_id = 2b41b332-…        <-- present (document-level provenance)
source_line_item_id = NULL         <-- absent  (line-level provenance)
source_page = 3                    <-- equals the document page_count
```

### A.2 Flagship dataset (`postgres`, `FACT`, `VERIFIED`)

| Object | State |
| --- | --- |
| `public.evidence_line_items` | **table does not exist** |
| `public.calculation_snapshots` | 100 |
| `public.emissions_logs` | 100 |
| `public.manual_extraction_items` | 264 (rich state spread) |

### A.3 Insight schema (`FACT`, `VERIFIED`)

`evidence_line_items` cannot be reached from Insight in any candidate
environment because **no candidate environment has the Insight tables**:
`carbontally_demo_local` 0, `postgres` 0, `carbontally_qa_phase8` 0 (of 136/116/133
public tables respectively). Insight tables exist only in disposable `ct_*`
clones and `carbontally_test`.

---

## B. Expected state

The investor journey (workplan Story C) requires an addressable chain:

```text
Source document
   ↓ extracted activity/data
   ↓ mapped emission factor
   ↓ validation
   ↓ deterministic calculation
   ↓ calculation snapshot
   ↓ emissions result
   ↓ provenance
   ↓ evidence / Source Evidence Viewer
   ↓ Insight explanation
```

For the **Evidence / Source Evidence Viewer** link to be demonstrable, the platform
requires at least one `public.evidence_line_items` row for a calculated item,
because:

- `GET /api/v3/evidence/line-items/{line_item_id}` resolves **an evidence line item
  id** (`backend/api/v3_evidence.py:127` — `repos.evidence_line_items.get(line_item_id)`);
- the report-evidence Insight tool returns `reference_kinds` including
  `evidence_line_item` (`services/insight_tools.py`);
- the calculation integration writes `calculation_snapshots.source_line_item_id`
  **only** from a resolved evidence line (`automatic_processing.py::_calculate_line`
  → `evidence_line_items.get_by_ordinals`, a *lookup*, never an insert).

So the expected state for Story C is: **≥ 1 evidence line item**, linked by
`calculation_snapshots.source_line_item_id`, resolvable by the Viewer and by the
Insight evidence handoff.

---

## C. Root cause

**The absence of `evidence_line_items` is caused primarily by a payload-shape
gate that is working exactly as ratified — combined with a document corpus that
never produces the required payload shape.** It is **not** caused by a missing
online hook, a missing linkage, or a schema mismatch inside the Demo Lab.

### C.1 The single derivation rule

`evidence_line_items` rows are derivable **only** from
`manual_extraction_items.extracted_data.line_items[]`:

- `backend/domain/line_items.py::derive_line_candidates` returns
  `DerivationResult(eligible=False, INELIGIBLE_LINE_COUNT, (), 0, 0, 0)` when
  `line_items` is absent or an empty array.
- The module docstring is explicit: it *"never fabricates a line for a flat
  document and never splits an aggregate into synthetic rows (manufacturing
  granularity is prohibited; P1 owns extraction fidelity)"*.
- Both write paths consume the same rule:
  - **forward**: `data/manual_extraction.py::_materialise_evidence_lines`
    (called from `update_item` and `save_extracted_data`), best-effort;
  - **backfill**: `data/evidence_line_items.py::backfill`, whose Class-1 scan
    selects only items where
    `jsonb_typeof(extracted_data->'line_items') = 'array' AND jsonb_array_length(...) >= 1`.

**Consequence, mechanically:** with a flat payload the forward hook inserts 0 rows
by design, and the backfill's *safety net* also has 0 eligible items. Neither path
can produce a row.

### C.2 Who ever emits `line_items[]` (`CODE-TRACED`)

| Producer | Emits `line_items[]`? | Condition |
| --- | --- | --- |
| `automatic_extraction._extract_csv` | **Yes, always** | any CSV with data rows |
| `automatic_extraction._extract_xlsx` | **Yes, always** | any worksheet with data rows |
| `automatic_extraction._extract_pdf` | **Only conditionally** | requires effective P1 shape mode `enabled` **AND** `judgement.multi_line_suspect` |
| `services/ai_document_extraction` | Yes when the AI returns a tabular document | AI path only |

The PDF gate is controlled by:

```text
CARBONTALLY_P1_EXTRACTION_SHAPE          default: "shadow"
CARBONTALLY_P1_ORGANIZATION_ALLOWLIST    required for "enabled" to take effect
```

`services/extraction_fidelity.py::shape_mode` documents the fail-safe: an empty or
missing allowlist **downgrades `enabled` to `shadow`**, and the default **must**
stay `shadow` until shadow evidence is recorded (`P1-D1`).

In `shadow` mode the classifier *measures and logs* (the coverage block) but
**deliberately does not change customer-visible output** — so a multi-line-suspect
PDF is collapsed into the flat payload.

### C.3 The causal chain, as it actually occurred

```text
T3 corpus: 14 documents — ALL PDF/text (no CSV, no XLSX)
        ↓
PDF path → P1 effective mode = "shadow"   (default; allowlist not set)
        ↓
classifier: multi_line_suspect = true, candidate_lines = 2
        ↓
shadow ⇒ shaped output withheld ⇒ flat extracted_data
        ↓
extracted_data has NO line_items key
        ↓
forward hook: derive_line_candidates → eligible=False → 0 inserts
backfill    : 0 eligible items                          → 0 inserts
        ↓
evidence_line_items = 0
        ↓
calculation_snapshots.source_line_item_id = NULL
        ↓
Source Evidence Viewer has no line id to resolve
Insight evidence handoff has no evidence_line_item reference
```

### C.4 Causes explicitly excluded

| Candidate cause (from workplan §1.3) | Verdict | Evidence |
| --- | --- | --- |
| **offline-only materialisation** | **EXCLUDED** | a forward (online) hook exists and is reached from the data layer |
| **missing online materialisation** | **EXCLUDED** | `_materialise_evidence_lines` is invoked from both `update_item` and `save_extracted_data`; the mechanism is present, it simply derives 0 candidates |
| **missing linkage** | **EXCLUDED as primary** | the snapshot→line link is NULL *because* no line exists; the lookup code path is correct and is a lookup-only by design |
| **schema mismatch (Demo Lab)** | **EXCLUDED** | `public.evidence_line_items` **exists** in `carbontally_demo_local` with the B2 DDL; it is genuinely empty |
| **schema mismatch (flagship dataset)** | **CONFIRMED (secondary, different environment)** | `postgres` has **no** `evidence_line_items` table at all |
| **demo-seeding omission** | **CONFIRMED as a contributing cause** | the seeded corpus contains **no CSV/XLSX** document, so the unconditional tabular producers were never exercised |
| **another concrete implementation/data-path issue** | **CONFIRMED (primary)** | the payload-shape gate + default-off P1 rollout is the decisive mechanism |

### C.5 Root-cause statement

> **Primary:** evidence lines are derived exclusively from
> `extracted_data.line_items[]`; every document processed in the Demo Lab was a
> PDF processed under the default `shadow` extraction-shape mode, so the
> multi-line classifier's finding (`2 candidate lines`) was recorded but the shaped
> output was deliberately withheld. The persisted payload was therefore flat, the
> derivation rule correctly produced zero candidates, and both the forward hook and
> the Class-1 backfill inserted nothing. This is a **working-as-designed
> consequence of P1 `shadow` + a corpus that never contains a tabular source**, not
> a broken materialisation path.
>
> **Secondary (environmental):** the historical flagship dataset lacks the B2
> table entirely, so it can never demonstrate the chain.
>
> **Contributing:** no CSV/XLSX document was ever seeded into the Demo Lab, so the
> only unconditional `line_items[]` producers were never exercised.

**Classification: this is neither a product defect nor purely a demo-environment
problem — it is an *unexercised ratified capability* whose activation is a
configuration/corpus decision, not a code fix.**

---

## D. Data / path trace — where the chain succeeds and where it breaks

| # | Link | Status in the Demo Lab | Evidence |
| --- | --- | --- | --- |
| 1 | **Source document** | **WORKS** | `organization_files = 14`; Storage substrate provisioned by the lab; 14 `document_processing_queue` rows |
| 2 | **Extracted activity/data** | **WORKS (flat shape)** | 12 items with `extracted_data`; 11 `extracted`, 1 `calculated` |
| 3 | **`line_items[]` (addressability)** | **BREAKS HERE** | `jsonb_typeof(extracted_data->'line_items')` = NULL for all rows; P1 `shadow` withheld shaped output |
| 4 | **`evidence_line_items` materialisation** | **BREAKS (0 rows)** | derivation rule returns `eligible=False`; backfill selects 0 eligible items |
| 5 | **Mapped emission factor** | **WORKS** | `emission_factors = 7,049` (DEFRA-2025 + SEAI-2025) |
| 6 | **Validation** | **WORKS** | snapshot `methodology = direct_multiply`; the completed item passed validation |
| 7 | **Deterministic calculation** | **WORKS** | snapshot `af640887…` = `2469.169780` kg CO₂e; `algorithm_version = v1.0`; `content_hash` present |
| 8 | **Calculation snapshot** | **WORKS** | 1 immutable row, `request_id` present |
| 9 | **Emissions result** | **WORKS** | `emissions_logs` `eb88e764…`, `calculated_kg_co2e = 2469.169780`, `snapshot_id` FK present |
| 10 | **Document-level provenance** | **WORKS** | `source_item_id = 2b41b332-…`, `source_file`, `factor_id`, `factor_source`, `factor_kind` |
| 11 | **Line-level provenance** | **BREAKS** | `source_line_item_id = NULL` (no line exists to reference) |
| 12 | **`source_page` integrity** | **PRESENT BUT UNVERIFIED** | stored `3` = document `page_count`; `domain/evidence.py` classifies it `PAGE_STATE_UNVERIFIED` and refuses to present it as an exact location |
| 13 | **Evidence / Source Evidence Viewer** | **BREAKS** | the Viewer resolves by `line_item_id`; zero rows exist |
| 14 | **Insight explanation** | **BREAKS (different cause)** | no Insight tables in the environment; the Insight evidence handoff is therefore unreachable |

**Where the chain is real today:** links 1, 2, 5, 6, 7, 8, 9, 10.
**Where it breaks:** links 3 → 4 → 11 → 13 (one causal chain), plus link 14
(an independent schema blocker).

---

## E. Minimum safe remediation (RECOMMENDATION — not authorized)

**Guiding constraints**

- `domain/line_items.py` must **not** be changed to derive lines from a flat
  payload: that would *manufacture granularity* and is prohibited by the ratified
  B2 contract (§11.1, F-B2-4).
- The Class-1 backfill **cannot** help: it has 0 eligible items by definition.
- Evidence must be produced by the **real pipeline**, never by raw SQL inserts; an
  out-of-band insert would fabricate an evidence trail and violate
  "no fabricated evidence / no simulated audit trail".

### E.1 Option A — corpus-only (no code change, no configuration change)

**Action:** include **at least one genuinely tabular source document** (CSV or XLSX)
in the frozen Step-2 demo corpus and process it through the normal
upload → automatic-processing pipeline.

**Why it works:** `_extract_csv` / `_extract_xlsx` emit `line_items[]`
**unconditionally**; `derive_line_candidates` then yields real candidates and the
existing forward hook (`save_extracted_data` → `_materialise_evidence_lines`)
inserts the rows with `materialisation_kind = 'FORWARD'`, a real `payload_hash` and
a server-resolved `organization_id`.

**Cost:** small (one seeded document). **Code change:** none.
**Behaviour change to production:** none. **Risk:** low.

### E.2 Option B — configuration-only (P1 controlled rollout for the demo org)

**Action:** for the **Demo Lab only**, set
`CARBONTALLY_P1_EXTRACTION_SHAPE=enabled` together with
`CARBONTALLY_P1_ORGANIZATION_ALLOWLIST=<demo organisation id>` (the documented
controlled-rollout mechanism), then re-process the demo PDFs.

**Why it works:** in `enabled` mode a multi-line-suspect PDF emits per-source-line
`line_items[]`, which the existing hook materialises.

**Cost:** small. **Code change:** none (a documented P1 facility).
**Caveat:** it changes extraction output shape for that organisation, so the demo
narrative must state that the shaped output is an explicitly enabled, bounded
rollout. **Risk:** medium unless strictly scoped to the lab; the code documents that
the default must remain `shadow` until shadow evidence is recorded (P1-D1) and must
never be enabled globally by default.

### E.3 Recommendation

For Story C the strongest *and smallest* option is **A**: a tabular document also
gives the demo a naturally multi-line artefact with real per-line rows, without
changing any extraction-shape policy. Option B is a legitimate fallback if the
frozen corpus must remain PDF-only.

### E.4 Explicitly rejected remediation

| Rejected | Why |
| --- | --- |
| Change `derive_line_candidates` to synthesise a line from a flat payload | Prohibited: manufacturing granularity; would fabricate evidence |
| Direct `INSERT INTO evidence_line_items` for the demo | Fabricated provenance; violates "real processing over animations" |
| Run the Class-1 backfill CLI with `--apply` hoping to populate | Provably 0 eligible items; a no-op that would only add audit noise |
| Add B2/Insight tables to `postgres` by hand | Mutating the protected flagship dataset; not authorized |
| Manufacture a `source_page` value | Current code already refuses to present an unverified page (correct behaviour) |

### E.5 Additional Step-2 conditions for the *full* Story-C chain

1. **Insight schema** — the demo environment must be re-provisioned to the current
   release migration state (all six `2026100*` Insight migrations), otherwise
   Insight cannot run at all and Story C's last link is unreachable.
2. **`source_page` honesty** — historical rows keep `NULL` line links and an
   unverified page count. Only documents processed **after** the remediation carry
   a verified line-level page, so the demo must use a freshly processed document and
   must never present the legacy snapshot's `source_page` as exact.

---

## F. Risk

| Risk | Assessment |
| --- | --- |
| **Regression risk of Option A** | **Low** — no code path changes; a new document exercises existing, tested producers (`_extract_csv`/`_extract_xlsx`) and the existing forward hook |
| **Regression risk of Option B** | **Medium** — changes extraction output shape for the enabled organisation only; must be scoped by allowlist and must not become a global default |
| **Tenant/security risk** | **Low if the pipeline is used.** `organization_id` is resolved server-side from the parent batch (the item has no `organization_id`, F-B2-8); RLS is unchanged; the Viewer re-authorizes on every read and treats a stored line id as a locator, not a grant. Risk rises sharply if rows are inserted out-of-band (rejected) |
| **Data-integrity risk** | **Low** — the table is append-only (`ON CONFLICT DO NOTHING`; no UPDATE/DELETE statement exists); a hash difference is reported as DIVERGENCE, never reconciled in place |
| **Provenance/audit risk** | **Low** — materialisation emits the existing `report:evidence_line_items_materialised` audit action via the existing audit repository |
| **Demo-truthfulness risk** | **Present and manageable** — the demo must disclose that the evidence-line capability was activated for the demo corpus / scoped rollout, and must not imply broadly populated evidence for the PDF corpus |
| **Scope-expansion risk** | **High if unbounded** — "make evidence work" could drift into a general extraction-fidelity programme. Step-2 scope must be limited to the frozen Story-C documents |
| **Risk of *not* remediating** | Story C cannot be demonstrated at all; the Source Evidence Viewer and the Insight evidence handoff remain unshowable, and the target narrative loses its final link |

---

## G. Authorization boundary (explicit)

**Identifying this remediation does NOT authorize implementing it.**

Not authorized by Step 1, and not performed:

- evidence-line implementation or backfill;
- any change to `domain/line_items.py`, the extraction producers, P1 shape policy,
  the forward hook or the backfill CLI;
- enabling `CARBONTALLY_P1_EXTRACTION_SHAPE=enabled` for any organisation;
- adding tabular documents to any environment;
- applying the Insight migrations or otherwise mutating any database;
- beginning investor-demo UI work.

Every item in §E is a **RECOMMENDATION** requiring an explicit PO decision before
execution. Step 1 stops here.

---

## H. EV-01 verdict

**EV-01: COMPLETE — root cause established with converging code and data evidence;
remediation identified but NOT AUTHORIZED.**

- The known fact (zero `evidence_line_items`) is **confirmed** and now **explained**.
- The preflight's `UNKNOWN` ("whether the pipeline *should* have produced a row") is
  **resolved**: it should not, and cannot, under the currently configured extraction
  shape — and that behaviour is the ratified, contract-compliant behaviour.
- Two environment-level blockers are additionally identified: the flagship dataset
  has no B2 table, and no candidate environment has the Insight tables.
- No implementation was performed.
