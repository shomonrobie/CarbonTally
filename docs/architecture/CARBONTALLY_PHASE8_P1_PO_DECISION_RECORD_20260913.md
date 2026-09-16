# CarbonTally — Phase 8 · Separate Workstream P1
## PO DECISION RECORD — `P1-D1`…`P1-D8` RATIFIED (2026-09-13)

**Authority:** PO ruling on the P1 Authorisation & Decision Package (`docs/architecture/CARBONTALLY_PHASE8_P1_AUTHORISATION_DECISION_PACKAGE_20260913.md`, task `…037`)
**Task that requested it:** `CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037`
**Ruling:** **Option A approved — P1 implementation is authorised.**
**Derives from / must not contradict:** `…020` P1 remediation contract (unmodified), B2-D3 (amended-never-deleted tests), `DM-7`, B1/B2/B3/B4 provenance semantics

---

## 1. Ratified decisions (verbatim rulings)

| ID | PO ruling |
|---|---|
| **`P1-D1`** | Authorise the P1 extraction shape change **for NEW DOCUMENTS ONLY**. Multi-line PDF/IMAGE documents may emit multiple per-source-line `line_items[]`. Implementation **MUST be shadow-first**: the coverage/classifier block is first computed and logged **without changing or blocking customer-visible behaviour**; customer-visible behaviour may change **only after** the required shadow evidence demonstrates the classifier is sufficiently selective per the P1 verification plan. Put the change behind a **`PIPELINE_VERSION` bump**. The `-020` §16.3 single-line tests **may be amended where the ratified behaviour changes, but MUST be amended, never deleted or weakened**. |
| **`P1-D2`** | When a document is classified **multi-line-suspect and AI is unavailable**, **block with a bounded, truthful reason**. Do **not** silently collapse the document into a misleading single-line result. |
| **`P1-D3`** | Per-page AI extraction is permitted **ONLY** when (1) the document is multi-line-suspect **AND** (2) the relevant text exceeds the existing clip boundary. **Enforce the P1 page cap.** Do not introduce unbounded AI extraction/cost. |
| **`P1-D4`** | **NO historical reprocessing or backfill in P1.** Existing documents remain untouched. |
| **`P1-D5`** | P1 supplies per-line `page` information for **NEW** extraction output. **Historical reclassification is a separate future workstream.** |
| **`P1-D6`** | Legacy `/api/upload*` and `pdf_engine` consolidation is **OUTSIDE P1**. Do not silently fold legacy-surface consolidation into this implementation. |
| **`P1-D7`** | Marker-derived `page` is **permitted with the OCR method stamp**, treated as **lower-trust provenance**, not equivalent to stronger page evidence. |
| **`P1-D8`** | AI-derived lines may be treated as evidence lines **ONLY** when explicitly stamped with an `ai:*` extraction method. Do **not** silently represent AI-derived evidence as deterministic source-line evidence. |

## 2. Implementation constraints (ratified, binding)

* Preserve the existing **deterministic + AI blending** architecture unless the authorised P1 shape change requires a **bounded** modification.
* Preserve existing **B1/B2/B3/B4 provenance and evidence semantics**.
* Do not invent regulatory claims or alter ratified disclosure semantics.
* Do not change **emission calculation logic** merely to solve extraction shape.
* Do not create a new emission-factor engine or factor catalogue as part of P1.
* No production changes; no historical re-extraction/backfill.
* Preserve unrelated worktree changes; no commit/push unless separately authorised.
* **There is NO Phase 9; Phase 8-X remains inside the Phase 8 programme.**

## 3. What this authorises, precisely

1. the multi-line `line_items[]` shape for **new** PDF/IMAGE extraction; 2. the deterministic multi-line-suspect classifier and the coverage block, **shadow-first (default off)**; 3. the `P1-D2` blocking behaviour, the `P1-D3` per-page AI policy with a cap, and `P1-D7`/`P1-D8` provenance stamping; 4. the `PIPELINE_VERSION` bump; 5. amending (never deleting) the `-020` §16.3 tests and adding line-aware tests.

**Not authorised:** any database migration; any historical backfill/re-extraction; any B2/B3/B4 object or semantics change; any `source_page` semantics change; legacy-surface removal (`P1-D6`); any calculation/factor change; production rollout, deployment or storage write; commit/push.
