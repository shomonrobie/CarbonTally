# CT-P8-B4-CONTRACT-AND-PO-DECISIONS-20260913-034

**Task ID:** `CT-P8-B4-CONTRACT-AND-PO-DECISIONS-20260913-034`
**Title:** Phase 8 Batch B4 — Narrative, Finalisation and Frozen Artefact — contract + PO decision register
**Date:** 2026-09-13
**Type:** CONTRACT / DECISION PREPARATION ONLY (no implementation in this task)
**Authorization:** PO blanket authorization `…050`; PO ruling `…040` (**no Phase 9**)
**Contract produced:** `docs/architecture/CARBONTALLY_PHASE8_B4_IMPLEMENTATION_CONTRACT_20260913.md`

---

## 1. Sources inspected

| Source | Used for |
|---|---|
| `CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` (§10, §10.3, §15, §17–§20, §21–§26, §28, §33–§35, §37) | narrative rules, approval, frozen artefact, retention, the `P1`–`P8`/`A1`–`A15` decision set |
| `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` (`A1`, `A3`, `P3`, `DM-5`, `DM-6`, `DM-7`, `D15`) | the **ratified** narrative/finalisation/drill-down policy spine |
| `CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` (§§8.3.1, 9.1–9.3, 10) | the S4 blockade's source clauses |
| `CT-P8-REPORTING-S4-NARRATIVE-OVERLAY-20260912-001.md` | the hard-stop conditions and their reasons |
| B3 contract + `CT-P8-B3-CLOSURE-20260913-051.md` + B3 V3 report | the B3→B4 interface actually delivered |
| Live schema (`carbontally_qa_phase8`) | verified current state (no narrative store; dormant `report_comments`, `user_edits`, `final_report_url`) |
| `CT-P8-REST-PLAN-20260913-027.md` §8.3/§20 B4 row; §22 register; `D-13`/`D-14` | the plan's B4 expectations |

## 2. Key finding — the S4 hard stop is now resolved by later ratified decisions

S4 blocked because the narrative **allowlist** and the **authorization rules** were marked `PO DECISION REQUIRED` **in documents dated before 20:42 on 2026-09-12**. The Disclosure Model Decision Record (same day, later) **ratified**:

* **`A1`** — narrative is **bounded and requirement-specific**; **no report-wide narrative editing**; authoring by **Customer Owner/Admin**;
* **`A3`** — **no arbitrary character/field limits**; typed fields + normal technical validation; only evidence-backed limits;
* **`P3`** — customers may **not** edit calculated emissions, provenance, factor data or system-derived values (enforced at the API boundary);
* **`DM-5`** — finalisation gates on unresolved `REQUIRED`; `CUSTOMER_INPUT_REQUIRED` **blocks**, `NOT_SUPPORTED` is **surfaced**, never collapsed;
* **`DM-6`** — drill-down depth per role (Owner/Admin full; Viewer controlled; Consultant bounded; PE/cross-tenant denied).

Therefore the narrative/finalisation *policy spine* needs **no new PO decision**; only the approval workflow, frozen artefact, retention, comments and the S4/S5/S6/S7 allocation remain open (`B4-D1…B4-D12`).

## 3. Contract summary

The contract (§§1–22) establishes: definition and root boundary; verified current state; deliverables A–L with the **governing policy status of each**; explicit non-scope; the S4-resolution table; the narrative overlay schema (**requirement-bound**, unique per requirement+kind, DRAFT-only, plain text, no arbitrary limits, no trigger/retention artefact); the domain rules (binding required, Owner/Admin authoring, never authoritative, immutability); the `DM-5` finalisation gate with its explicit output shape; the `DM-6` drill-down matrix; the **[DECISION REQUIRED]** approval/frozen-artefact/retention sections; historical immutability; the RLS/audit posture; the API surface; the test contract and **gate V4**; the migration strategy (B4-1 implementable now, B4-2 gated on `B4-D5…D7`); the environment/deployment boundaries; the full **`B4-Dn` register (`B4-D1…B4-D19`)**; and gate-V4 acceptance criteria A1–A11.

## 4. Decision register outcome

| Class | IDs |
|---|---|
| **OPEN — PO DECISION REQUIRED** | `B4-D1` approver authority · `B4-D2` post-approval invalidation/revocation · `B4-D3` review gate · `B4-D4`/`B4-D9` comments · `B4-D5` frozen artefact mandatory · `B4-D6` storage model · `B4-D7` hashing · `B4-D8` retention · `B4-D10` S4/S5/S6/S7 allocation · `B4-D11` download audit/staleness/drill-down exposure · `B4-D12` entitlement gating |
| **RATIFIED** | `B4-D13` narrative binding + authoring + limits (`A1`/`A3`/`P3`) · `B4-D14` finalisation (`DM-5`) · `B4-D15` drill-down (`DM-6`) · `B4-D16` historical immutability (`D15`) |
| **DECIDED (contract)** | `B4-D17` deterministic-only narrative (AI = S8, outside B4) · `B4-D18` no triggers/retention artefact · `B4-D19` RLS posture |

**Deliverables A, B, C, D, H, I, K and the narrative part of J are implementable now** (their policy is ratified). Deliverables E, F, G require `B4-D1…B4-D8` (and `B4-D10` fixes the batch boundary).

## 5. Files created

1. `docs/architecture/CARBONTALLY_PHASE8_B4_IMPLEMENTATION_CONTRACT_20260913.md`
2. this report

No pre-existing file was modified. **No implementation, migration, schema change, test change or data change occurred in this task.**

## 6. Repository state

| Item | Value |
|---|---|
| Branch / HEAD | `main` / `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged) |
| Staged | 0 |
| Commits | none |

## 7. Verdict

### `B4 CONTRACT COMPLETE — 12 PO DECISIONS REQUIRED (B4-D1…B4-D12); NARRATIVE + FINALISATION SPINE RATIFIED AND IMPLEMENTABLE NOW`

**Next action (no PO decision needed):** implement the ratified B4 increment — the narrative overlay + the `DM-5` finalisation gate + the `DM-6` exposure rule — while raising `B4-D1` (approver authority) and the frozen-artefact/retention/allocation decisions in the compact format as they block.
