# CarbonTally WS4 / Gate 3 — Architecture Reconciliation Report

**D22 / D38 / Processing-Assignment Model**
**Analysis only — no code changes, no migrations, no commit/push.**

- Date: 3 September 2026
- Authoritative architecture: `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.2.md` (frozen V1.2)
- Implementation inspected: D22 batch assignment, D38 `work_item_assignments` ledger + service + routes, PE/Ops APIs, entity/org RLS, V1.2 dual-origin workflow, WS1 (D38) acceptance evidence.
- Status: Gate 1 PASS (accepted), Gate 2 PASS (accepted), Gate 3 BLOCKED (architectural conflict). This report reconciles the Gate 3 model mismatch for PO decision.

---

## 1. Executive Finding

**ARCHITECTURE DECISION REQUIRED (leaning to Option B — item-level processing assignment required).**

Blueprint V1.2 requires that a *customer's work* may be processed by multiple processing entities and/or CarbonTally staff (§6.4), that CarbonTally may process work internally alongside external PEs (§9, CT-QC-001), and that processing-origin/stage provenance identify which PE or internal team/member performed each relevant stage (CT-QC-004, §11). The current D22/D38 implementation instead authorizes manual-extraction processing at the **batch** level: one processing party per batch (`manual_extraction_batches.entity_id` XOR `assigned_to`), enforced in RLS, in the service layer, and across the PE/Ops access contracts.

That is an **implementation/domain-model gap relative to the approved architecture** (not merely a Gate-3 test-design problem): the architecture speaks about assignment of *work* and *stages*, while the implementation implements assignment at the granularity of the *batch container*. The D38 `work_item_assignments` ledger already expresses **item-level** assignment intent; what is missing is item-level **processing authorization** and a CarbonTally-controlled item-to-PE assignment path.

**Recommendation:** **OPTION B** — introduce item-level processing assignment as the effective per-work-item boundary (item open assignment, else batch default, else unassigned), implemented as an additive extension of D38 plus RLS/service-layer checks; keep the batch as an optional operational default/container. Exact wording for PO approval is in §13.

---

## 2. V1.2 Requirements Relevant to Processing Assignment

Source: `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.2.md`.

| § | Requirement (quote/paraphrase) | Relevance |
| --- | --- | --- |
| §5.3 | PE is an independent third-party service provider performing **CarbonTally-assigned** work; PE access is entity-scoped and **assignment-based**. | Assignment is the authorization predicate — not batch membership per se. |
| §6.4 | "CarbonTally controls assignment." PEs cannot select arbitrary customer work, claim arbitrary documents, enumerate customers, browse other PEs' work, or access unassigned work. "**A customer may have work processed by multiple processing entities and/or CarbonTally staff.** There is no permanent customer-to-PE exclusivity requirement." | Direct authority for multi-party processing of one customer's work; no exclusivity requirement. The sentence is customer-scoped; the blueprint never states that a *batch* is the processing-party boundary. |
| §9 | Two canonical origins (internal and PE); CarbonTally internal staff may perform the same manual work as PEs; CarbonTally QC may verify "PE work that has already passed PE Review and PE QC" and "corrected, reassigned, or otherwise reprocessed work". | Workflow is per work item/stage; the term **reassigned** implies assignment can change for a piece of work. |
| §9 / CT-QC-004 | "Processing origin must be preserved as auditable provenance, including **which CarbonTally team/member or Processing Entity performed each relevant stage**." | Stage-level executor attribution is required — supports per-item granularity. |
| §10 | Durable automatic processing pipeline (upload → durable job → extraction → mapping → validation → calculation → immutable snapshot → review/QC) with AI assist and deterministic calculation. | Future executors (automation/OCR/LLM) must be representable without corrupting assignment semantics. |
| §11 | Evidence/provenance chain source document → extracted value → mapped activity → factor → calculation → snapshot → review/QC → approval. | Provenance is item-centric. |
| §13 | PE authorization = identity + processing entity + **assigned work** + resource + action. | "Assigned work" is naturally item/assignment-scoped. |
| §14 | RLS remains defense-in-depth: organization RLS, consultant relationship RLS, **PE entity RLS**, server-side helpers, explicit resource checks. | RLS must follow the effective assignment model, not contradict it. |
| §28 | Invariants: PE cannot access unassigned work (8); PE cannot access another PE's work (9); CarbonTally controls PE assignment (12); data minimization (25). | These constrain any item-level model; they do not require batch-level exclusivity. |
| §31.2 CT-QC-001..005 | Frozen V1.2 amendment: internal department + external PEs; CT QC independent of origin; PE QC distinct; origin/stage provenance; two canonical workflow paths without mandatory PE processing. | Confirms origin ≠ assignment and both origins can coexist in one customer context. |

Blueprint V1.2 does **not** state that a batch is a processing security/attribution boundary and does **not** require a single processing party per batch.


## 3. Current D22 Model (actual implementation)

- Table `manual_extraction_batches` carries the mutable party carrier: `entity_id` (PE) XOR `assigned_to` (internal staff), plus `assigned_by`, `status` (`in_progress` on assignment), audit on change.
- Assignment endpoint: `POST /api/v3/ops/batches/{batch_id}/assign` (`BatchAssign`: exactly one of `assigned_to` / `entity_id`; internal staff with `can_manage_staff` + `can_process`). Reassignment replaces the whole batch party and records `assigned`/`reassigned` batch-audit events.
- Batch access helpers (all batch-level):
  - `operations_auth.ensure_batch_operator_access` — internal staff only on `entity_id IS NULL` batches assigned to them or open; entity staff only on own-entity batches.
  - `operations_auth.ensure_entity_batch_access` — any entity workspace item/batch read requires `batch.entity_id == caller entity`.
  - `v3_pe._ensure_assigned_item` / `_pe_entity_item` — PE item/work access requires `batch.entity_id == caller entity`.
- RLS (live `pg_policies`):
  - `manual_extraction_batches_entity_select`: `entity_id IS NOT NULL AND is_entity_member(entity_id)`.
  - `manual_extraction_items_entity_select`: items visible to entity staff only when **their batch** has `entity_id IS NOT NULL AND is_entity_member(batch.entity_id)` — a subquery on the batch carrier.
- Net effect: **a batch has exactly one processing party; batch = processing security boundary for manual-extraction work.**

## 4. Current D38 Model (actual implementation)

- Table `work_item_assignments` (append-only ledger, additive migration `20260902030000_…`): `status open|closed`, `action assign|reassign|claim|recover`, `assignee_kind internal_staff|processing_entity`, `assigned_to` XOR `processing_entity_id`, `assigned_by`, `actor_domain`, `previous_*`, `reason`, `close_action released|completed|reassigned|recovered|superseded`, single-open partial unique index. RLS enabled, **no policies** — API-only.
- Service `backend/services/work_items.py`:
  - Internal domain: `ops_assign_item` (claim/assign/reassign/recover) targets an **internal staff user** only, and **refuses** items whose `batch.entity_id IS NOT NULL` ("PE work is entity-scoped").
  - PE domain: `pe_claim_item`/`pe_release_item`/`pe_complete_item` operate only on items whose `batch.entity_id == own entity`; no PE reassign; other-entity open claims are denied.
- Routes:
  - Ops: `GET/POST /api/v3/ops/items/{id}/work[/claim|assign|reassign|recover|release|complete]`; `WorkItemTarget = {assigned_to (internal staff), reason}` (OpenAPI-verified).
  - PE: `GET/POST /api/v3/pe/items/{id}/work[/claim|release|complete]` only.
- WS1 (D38) acceptance evidence records: "PE reassignment of individual items is NOT authorized (403 route absence + service denial for other-entity open claims); PE batch reassignment remains."
- D38 is therefore an **item-level attribution ledger over a batch-level authorization model**. Current open-ledger population = 0 (baseline).

## 5. Intended Domain Model

Consistent reading of V1.2 + approved decisions (WS1/WS4, D22, CT-QC amendments):

1. **Standalone file** — a work item may exist without a batch (V1.2 does not require batch membership for an item to be processed; item-centric provenance chain §11 supports this). Currently items are always created inside a batch; a standalone-file item is a forward model with no contradicting V1.2 decision.
2. **Batch** = grouping/container/context for work items; **not necessarily** the security/attribution boundary of each item.
3. **Batch-level assignment** = optional operational default (`Batch → PE Alpha`), applied when the item has no item-level assignment.
4. **Item-level assignment** = per-work-item processing party (`Item A → Alpha`, `Item B → Beta`, `Item C → Alpha`, `Item D → Internal`) — the granularity implied by §6.4/§9/CT-QC-004/§13 and expressed in intent by D38.
5. **Effective assignment** = item open `work_item_assignments` row **if present**, else batch default (`entity_id`/`assigned_to`), else unassigned (CarbonTally-controlled queue). Server-side derivation; never duplicated into a second mutable source of truth.
6. **Assignment changes** controlled by CarbonTally Operations: assign item → PE; reassign PE Alpha → PE Beta; move PE → Internal; move Internal → PE; release; recover — each closing the previous open row and appending history.
7. **Processing origin stays immutable** and is distinct from current assignment, history, actual execution, and audit evidence.


## 6. Gap Analysis (exact differences)

| Intended (V1.2) | Current implementation | Gap |
| --- | --- | --- |
| Per-work-item processing party | Per-batch party (`entity_id` XOR `assigned_to`) | Granularity mismatch |
| One batch may contain items assigned to Alpha, Beta, Alpha, Internal | One batch is Alpha **or** Beta **or** Internal | One-batch multi-party not representable |
| PE item access authorized by "assigned work" (§13/§28-8) | PE item access authorized by `batch.entity_id` (service + RLS) | Batch-level authorization block |
| CarbonTally may assign/reassign an item between PEs / to internal | No ops→entity item assign; no PE→PE item reassign route | Missing authorized assignment path |
| Internal staff may process an item in a PE-defaulted batch after reassignment | Ops service refuses items in any `entity_id`-assigned batch | Party-change only possible whole-batch |
| Origin immutable + stage provenance | Origin immutable (`processing_origin`/`processing_entity_id`; `mark_pe_origin_if_unset`) | No gap (correctly implemented) |
| Effective assignment derivation | No derivation; current party read = batch fields; D38 open row is attribution only for processing | Missing "current effective assignment" semantics on processing paths |
| D38 = item-level ledger | D38 ledger is item-level, but constrained by batch-scope in the service | Extension needed, not redesign |

The single most important mismatch: **RLS and PE/Ops processing helpers evaluate `batch.entity_id`, so the batch is the de facto authorization boundary**, while the approved architecture requires assignment of *work* to be the boundary.

## 7. Security Impact

Mandatory invariants (§28) and their status under the proposed correction:

| Invariant | Risk/threat under item-level model | Mitigation (analysis) |
| --- | --- | --- |
| PE cannot access unassigned work | If item has no effective assignment and falls back to batch, PE must still not see it when batch is unassigned | Effective-assignment resolution denies when neither item nor batch is assigned to the caller |
| PE cannot access another PE's work | Item reassigned Alpha→Beta: Alpha's old claims closed; RLS/item access must use the *new* effective assignment only | Item-level RLS qual resolves current open ledger row (or batch default) with `is_entity_member` |
| PE cannot enumerate customers / batches not its own | Batch-level RLS `entity_select` currently exposes all own-entity batches — with item-level model, batch SELECT may still show the batch to the default PE, but **item SELECT must be restricted to items effectively assigned to the caller** | New item-level select predicate; no customer/org enumeration path added |
| CarbonTally controls PE assignment | Ops gain ability to assign/reassign items to PEs — must remain internal-staff-only (`can_manage_staff` + process capability), never PE-initiated | Extend ops item-work contract; PE surface gains only read of effective assignment + claim/release/complete on own assigned items |
| QC independence | Unchanged: PE QC vs CT QC decision stages keyed off workflow state + origin, not off assignment | No change to QC endpoints/state machine |
| Processing origin immutable | Assignment changes must never write `processing_origin` | D38 service already never writes origin; keep that invariant and assert it in tests |
| Assignment history auditable | Item reassign adds ledger rows with `previous_*`, `close_action='reassigned'`, actor | Ledger is append-only; single-open index preserved |
| Frontend never security boundary; RLS defense in depth | Any new security-definer RLS function must not leak other-entity rows | `is_entity_member`-style helper returning boolean over item/batch grants only |
| No PE customer-wide access from one processed item | Item-level grant is per item; effective assignment gives no org-wide scope | Item grant never implies organization membership |

Main new risks: (a) RLS predicate correctness on the item select path; (b) race between reassignment and in-flight PE processing (mitigated by single-open unique index + transactional close/open); (c) over-broad batch SELECT for default-PE contexts — must be paired with item-level restriction so batch visibility cannot be used to enumerate another PE's items in the same batch.

## 8. Data Migration Impact (analysis only)

- Baseline: 7,049 factors · 975 orgs · 260 items · 56 batches · **0** open `work_item_assignments`.
- 56 existing batches carry a batch-level party (`entity_id` or `assigned_to`) → reinterpreted as **defaults** under the new model; no row rewrite required.
- 260 existing items: processing-origin columns stay as-is; origin immutability preserved.
- 0 open ledger rows today → no open-assignment reconciliation needed. (If open rows existed later, they would already be canonical item assignments.)
- No destructive migration; additive only (new nullable columns/indexes if any; new RLS policy expressions). Investor/demo data untouched.

This model is consistent with V1.2: nothing in the blueprint or ratified decisions requires batch-level exclusivity, and §6.4/§9/CT-QC-004 actively anticipate multiple parties for a customer's work with per-stage provenance.


## 9. API Impact (analysis only)

- **Ops item work** (`/api/v3/ops/items/{id}/work/*`): extend assign/reassign/recover target vocabulary to accept a processing entity (in addition to internal staff); release/complete unchanged; history read unchanged. Remove the hard service denial triggered merely by `batch.entity_id IS NOT NULL` when the operation is an authorized item-level assignment.
- **PE work** (`/api/v3/pe/*`): work listing and item access resolve the item's effective assignment (open ledger row else batch default). PE retains claim/release/complete on own effectively-assigned items only. No PE-initiated reassign.
- **Processing endpoints** (start/extract/map/validate/calculate under `/pe` and `/ops/entities/…`): authorization switches from `batch.entity_id == entity` to `effective_assignment(item) == entity` (batch default allowed).
- **Batch assign endpoint** retained as the default-assignment mechanism (unchanged semantics; becomes a default rather than the exclusive boundary).
- **Read surfaces**: PE `/work`, Ops queues, CT-QC queue, customer review unchanged in shape; PE items enumerated per effective assignment.

## 10. Workflow Impact (analysis only)

- The V1.2 status state machine is per **item** today (`pending…calculated → pe_review → pe_qc → ct_qc → approved`; internal path `…calculated → reviewed → ct_qc → approved`). Origin + status already select the correct path.
- Switching the processing *party* to item-level does **not** change statuses, transitions, QC semantics, or customer approval semantics. `processing_origin` continues to determine which upstream controls apply.
- One genuine nuance: a PE-origin item reassigned to CarbonTally internal staff mid-flight keeps `processing_origin = PROCESSING_ENTITY` and its PE Review/PE QC markers (origin is historical fact). Internal staff may then perform later stages or rework on that item; the canonical path for *that item* remains origin-driven. No state-machine redesign required.
- No contradiction found that requires redesigning the V1.2 workflow.

## 11. Gate Impact (analysis only)

- **Gate 1 (Internal terminal E2E)**: evidence exercised one internal-origin item/batch with a single party. Under the item-level model the same flow remains valid (item effectively internal). No invalidation.
- **Gate 2 (PE terminal E2E)**: evidence exercised one PE-origin item in an Alpha-assigned batch with PE Review/PE QC/CT QC/customer approval. Valid under the item-level model (item effectively Alpha). No invalidation.
- **D38 acceptance (WS1/WS4)**: internal claim/assign/reassign/release/complete/recover and PE own-entity claim evidence remain valid — those operations remain allowed. **Targeted re-verification needed** after implementation for: ops→entity item assignment, PE item list by effective assignment, reassign PE Alpha→Beta, item moved PE↔internal within one batch, and cross-PE denial when the batch default differs from an item's assignment.
- **D39 (PE/Ops messaging)**: unaffected (conversation/entity scoping independent of item assignment).
- **D40 (notifications)**: unaffected; optionally a D38 assignment notification for entity-target assignment can be emitted on the same idempotent-event-key mechanism.
- **Gate 3**: becomes executable after the correction (the one-batch Alpha/Beta/Alpha/Internal fixture then has a legitimate representation and authorization path).

## 12. Minimum Required Change (smallest technically sound change)

Prefer **extension of D38** (the ledger is already item-level and append-only); do not redesign or add a parallel table.

1. **DB (additive):**
   - Treat the open `work_item_assignments` row as the canonical item-level current assignment (already supported by schema and single-open index).
   - Keep `manual_extraction_batches.entity_id/assigned_to` as the **default**; add no redundant item-party column (avoid dual sources of truth), or — only if RLS cannot consult the ledger cleanly — add a nullable derived/current-party column maintained transactionally by the D38 service. (Preference: ledger-derived, no duplicate column.)
   - Add an item-level entity-grant RLS helper (security-definer, boolean) and replace the batch-subquery qual in `manual_extraction_items_entity_select` (and any equivalent batch item read) with an effective-assignment predicate.
2. **Service (`work_items.py`):** extend ops item assign/reassign/recover to accept `assignee_kind = processing_entity`; close the previous open row (`reassigned`) and open the new row in one transaction; keep single-open invariant; keep internal_staff behavior; keep PE domain semantics (claim/release/complete on own effectively-assigned items only).
3. **APIs:** ops item-work target payload gains an optional entity target; PE list/processing authorization reads effective assignment; batch-assign remains for defaults.
4. **Authorization/RLS:** item processing and PE reads resolve effective assignment server-side and in RLS; CarbonTally-only assignment control preserved; no new PE capability; separation of duties (ops assign vs PE process vs PE QC vs CT QC vs customer) untouched.
5. **Audit:** existing ledger + audit events continue; ensure each reassign records actor (`assigned_by`, `actor_domain`) and `previous_*`; no new audit table.
6. **Workflow:** no state-machine change.
7. **Tests/regression:** add ALLOW/DENY matrix for one-batch multi-party (Alpha/Beta/Alpha/Internal), reassign, origin immutability, cross-PE denial when item assignment differs from batch default; re-run affected WS4 subsets after implementation.


## 13. PO Decision Required

Approve or reject the following decision wording:

> "CarbonTally adopts **item-level processing assignment** for manual-extraction work items. The effective processing party for a work item is: (1) the item's open D38 `work_item_assignments` assignment if present, else (2) the batch-level default (`manual_extraction_batches.entity_id` / `assigned_to`), else (3) unassigned (CarbonTally-controlled queue). CarbonTally Operations may assign, reassign (including PE→PE and PE↔Internal), release and recover individual work items through the D38 contract; Processing Entities may only claim, release or complete items effectively assigned to their own entity; PE-initiated reassignment remains prohibited. `processing_origin` and stage provenance remain immutable and are not changed by assignment. D38 is extended (not redesigned); the V1.2 workflow state machine, CT QC independence, PE QC scope, customer approval authority, and all §28 security invariants are preserved. RLS gains item-level effective-assignment checks. This change is required for WS4 Gate 3 (one batch may contain items assigned to multiple processing parties)."

## 14. Recommended Next Workstream (smallest, only if PO approves)

1. Additive DB change (RLS helper/policy + any ledger service support) with a forward-only migration; no data rewrite.
2. `work_items.py` ops entity-target assignment/reassignment (transactional close/open), plus PE read-of-effective-assignment.
3. API payload/route extension (ops item assign to entity; PE item list semantics) — no new roles/capabilities.
4. Regression ALLOW/DENY matrix incl. the one-batch Alpha/Beta/Alpha/Internal fixture, cross-PE denial, origin immutability, single-open invariant.
5. Targeted re-verification of D38 evidence + affected WS4 subsets (Gate 1/Gate 2 paths remain logically unchanged).
6. Re-run WS4 Gate 3 only after implementation and PO sign-off.
7. Future automated processing: keep **assignment = accountable party** (CarbonTally internal department/PE) and represent automation/OCR/LLM as CarbonTally-controlled **executors with machine provenance** on the durable pipeline (existing extraction provenance + job records); do not add automation as an "assignee" to the D38 party vocabulary.

---

*This document is analysis only. No code, SQL, RLS, API, UI, tests, D38/D39/D40, or blueprint content was changed. No commit/push was made. The WS4 Gate 3 fixture, probe evidence and cleanup remain exactly as recorded in the Gate 3 entry of `CARBONTALLY_PHASE5_WS4_FINAL_ACCEPTANCE_REPORT.md`.*
