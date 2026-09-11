# CarbonTally V1.2 — Dual-Origin Workflow & CarbonTally QC Gate
# Design Report (Pre-Migration Design Package)

**Status:** PROPOSED DESIGN — awaiting Product Owner review
**Date:** 2 September 2026
**Authoritative architecture:** `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.2.md`
**Frozen decisions:** CT-QC-001 … CT-QC-005, PE-ROLE-001, PE-MSG-001

**Scope:** Design only. No database migration has been applied, no business data
modified, no Phase 4 work started. Baseline verified: **7,049 emission
factors**; **41 migrations**; git HEAD `16391217103b98dcea520070c5a22c68f12fe607`.

---

## 1. Current workflow diagram (verified behaviour)

### 1a. Manual-extraction item pipeline (`manual_extraction_items.status`,
`domain/partners.py ITEM_STATUS_FLOW`)

```
pending → extracting → extracted
                          │  (CarbonTally QC today = EARLY extraction gate:
                          │   ops `qc_item` can_review + `/api/v3/qc/*` admin,
                          │   list_qc_pending() = status='extracted' AND quality_score IS NULL;
                          │   writes qc_by/qc_at/quality_score → qc_approved | qc_rejected)
              ┌───────────┴───────────┐
              ▼                       ▼
      mapping/mapped            qc_approved / qc_rejected
              │                       │ (qc_rejected → extracting/mapping rework)
              ▼                       ▼
      validating/validated      mapping / mapped   (qc_approved → mapping)
              │
              ▼
      calculating/calculated ──→ customer_review ──→ approved | rejected
                    (rejected → mapping/extracting rework; approved → customer_review)
```

- **Origin today:** inferred from the *mutable* carrier
  `manual_extraction_batches.entity_id` (NULL = internal, populated = PE), plus
  `staff_profiles.entity_id` for actor attribution. No immutable per-item
  origin column exists.
- **Review stage (internal):** `manual_review_queue` rows (`entity_id`,
  `assigned_to`, `batch_id`, `customer_document_id`) with
  `review_assignment_history` + `review_audit_trail` actor provenance; completed
  by internal reviewers (`can_review`).
- **Customer approval:** item-level `customer_review(...)` → `customer_approved`,
  `customer_reviewed_by/at`, status `approved`/`rejected`; logged in
  `customer_review_log`. Authorized to organisation owner/admin (D5) or internal
  staff via `/api/v3/processing/*`.
- **PE processing today:** `/api/v3/operations/entities/{entity_id}/extraction/*`
  and the thin `/api/v3/pe/*` contract allow PE staff to run start/extract/map/
  calculate/status/clarify on entity-assigned batches. PE staff are blocked
  (`403`) from all CarbonTally-gated statuses (`validating/validated/
  customer_review/approved/rejected/qc_approved/qc_rejected`). PE-completed work
  therefore has **no current route** to CarbonTally QC / customer approval.
- **Durable automatic jobs:** separate job store
  `document_processing_queue` (stage machine
  enqueued→ingesting→extracting→mapping→validating→calculating→review→completed)
  mirrors results into `manual_extraction_items` (`source_item_id`); customer
  approval is the `review→completed` transition.

### 1b. CarbonTally QC today

- `/api/v3/qc/*` — CarbonTally-internal; `require_admin()` (explicitly rejects
  Processing Entity staff). Queue is **origin-agnostic** (verified: 28 pending =
  25 internal + 3 PE) and acts on `status='extracted'` items (**early**
  extraction-quality gate), writing `qc_by/qc_at/qc_notes/quality_score` and
  setting `qc_approved`/`qc_rejected`.

### 1c. Current state/status inventory

---

## 2. Target workflow diagram (V1.2 §9 canonical)

### PATH A — CARBONTALLY_INTERNAL (CarbonTally staff process; no PE stages)

```
Extraction → Mapping → Validation → Calculation* → Review
        → CarbonTally QC → Customer Approval
```
\* Calculation is shown explicitly because the platform performs authoritative
calculation between validation and review in both the manual and durable
pipelines (V1.2 §10/§11 evidence chain). Review = CarbonTally internal review.

### PATH B — PROCESSING_ENTITY (PE processes; PE stages present)

```
Extraction → Mapping → Validation → Calculation*
        → PE Review → PE QC → CarbonTally QC → Customer Approval
```

**Invariants**
- Internal work never acquires PE Review / PE QC stages.
- PE-originated work never bypasses CarbonTally QC.
- CarbonTally QC is origin-independent (CT-QC-002) and separate from Customer
  Approval.
- Customer Approval is the final, customer-side authority (CT-QC-005 / D5).

---

## 3. Proposed canonical stage/state model

Keep the existing single canonical work-item (`manual_extraction_items.status`)
as the **current-stage marker** and extend its vocabulary with explicit,
non-redundant stage states. Stage *completion events* are recorded in the
existing **audit trail** (see §5) — no parallel state machine, no new table.

Proposed canonical statuses (additive to `ITEM_STATUS_FLOW`):

| Stage | Statuses (current marker) |
|---|---|
| Source | `pending` |
| Extraction | `extracting`, `extracted` |
| Mapping | `mapping`, `mapped` |
| Validation | `validating`, `validated` |
| Calculation | `calculating`, `calculated` |
| Internal Review (PATH A) | `review` (awaiting), `reviewed` |
| PE Review (PATH B) | `pe_review` (awaiting), `pe_reviewed`, `pe_review_rejected` (rework) |
| PE QC (PATH B) | `pe_qc` (awaiting), `pe_qc_approved`, `pe_qc_rejected` (rework) |
| CarbonTally QC (both paths) | `ct_qc` (awaiting), `ct_qc_approved`, `ct_qc_rejected` (rework) |
| Customer | `customer_review`, `approved`, `rejected` |

Transition rules (canonical)
- `calculated` → `review` **if** origin = CARBONTALLY_INTERNAL (skip PE stages)
- `calculated` → `pe_review` **if** origin = PROCESSING_ENTITY
- `pe_reviewed` → `pe_qc`; `pe_qc_approved` → `ct_qc`
- `reviewed` → `ct_qc` (internal path)
- `ct_qc_approved` → `customer_review`
- Rejection/rework: `pe_review_rejected`/`pe_qc_rejected`/`ct_qc_rejected` →
  `mapping` (or `extracting`) as today; customer `rejected` → `mapping`/`extracting`.
- Corrections/reassignment always re-enter through an existing rework loop and
  re-require the appropriate downstream gates (CarbonTally QC where required).

Historical mapping of current statuses (compat — see §11)

| Existing | Under V1.2 model |
|---|---|
| `extracted` + QC not run | awaiting extraction-stage completeness; late CT QC now applies downstream |
| `qc_approved` / `qc_rejected` (early gate) | retained as **historical** early extraction-quality markers; backfilled as such; do not reinterpret as CT QC late gate |
| `mapping/mapped/validating/validated/calculating/calculated` | unchanged canonical markers |
| `customer_review/approved/rejected` | unchanged |

---

## 4. Processing-origin model

Three distinct concepts (must not be conflated):

1. **Processing origin** (immutable, historical):
   `manual_extraction_items.processing_origin VARCHAR`
   `CHECK (processing_origin IN ('CARBONTALLY_INTERNAL','PROCESSING_ENTITY'))`,
   set **once** when extraction begins (first claim/extract) from the
   then-current `manual_extraction_batches.entity_id`, and **never auto-updated**
   afterwards.
2. **Current assignment** (mutable): `manual_extraction_batches.entity_id`
   (NULL = internal). Drives routing, permission scope and the ops/PE queues.
   Reassignment changes only this carrier.
3. **Historical processing actor / PE identity**:
   `manual_extraction_items.processing_entity_id UUID` (nullable FK to
   `processing_entities`, `ON DELETE RESTRICT`) set once when
   `processing_origin='PROCESSING_ENTITY'`; plus existing actor columns
   (`extracted_by/extracted_at`, and new per-stage actor columns below) and the
   append-only audit events.

Reassignment example (must hold): PE-A extracts → PE-A Review → PE-A QC → work
reassigned to CarbonTally internal → CarbonTally QC. Because
`processing_origin` + `processing_entity_id` are immutable on the item and the
stage events are append-only, historical provenance still identifies PE-A as
the processing entity/origin even though the batch's `entity_id` now points to
internal.

PE identity where applicable is therefore never derived solely from the mutable
current batch assignment.

**Scope of the origin concept (clarification, 10 September 2026).**
`processing_origin` identifies the **manual-processing capacity / control path**:
CarbonTally internal processing vs Processing Entity processing. It does **not**
identify actor identity — the human actor is recorded separately (see the §5
provenance table: *"Who extracted?"* → `extracted_by/extracted_at`) — and it does
**not** identify processing mode: automatic vs manual processing is an independent,
actor-agnostic dimension (see the Final Architecture Blueprint §9, *"Processing model
— dimensional clarification"*).

Participation by any other actor — for example a Consultant processing on behalf of
an engaged client organisation, or the client organisation itself — does **not**
change this vocabulary. The two values remain exactly `CARBONTALLY_INTERNAL` and
`PROCESSING_ENTITY`, the CHECK constraint and the origin→stage routing are unchanged,
and no actor-domain value (such as the previously proposed `CONSULTANT`) is added to
`processing_origin`. The Product Owner withdrew that proposal on 10 September 2026 —
see `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`, decision
`PO-P6-2D-D7b-R-20260910`.


Working: `pending`, `extracting`, `extracted`, `mapping`, `mapped`,
`validating`, `validated`, `calculating`, `calculated`.
Quality/review: `qc_approved`, `qc_rejected` (early extraction QC).
Customer: `customer_review`, `approved`, `rejected`.
No PE Review / PE QC statuses exist. No late CarbonTally QC stage exists.

---

## 5. Provenance model

Answers required by V1.2 §6/§9 with the following sources:

| Question | Source |
|---|---|
| Who extracted? | `manual_extraction_items.extracted_by/extracted_at` |
| Internal or PE? | `processing_origin` (new, immutable) |
| Which PE? | `processing_entity_id` (new, immutable FK) |
| Who performed PE Review? | audit event `pe_review:*` actor (+ proposed `pe_reviewed_by/at` convenience columns) |
| Who performed PE QC? | audit event `pe_qc:*` actor (+ proposed `pe_qc_by/at`) |
| Who performed CarbonTally QC? | existing `qc_by/qc_at` repurposed for the late CT QC gate on new items; audit event `ct_qc:*` |
| Who approved as customer? | `customer_reviewed_by/at`, `customer_review_log` |
| Reassigned? | existing batch-assignment audit events (audit trail + `review_assignment_history`) |
| Corrected/reprocessed? | rework transitions recorded as audit events + `reprocess_count` on durable jobs |
| Stage history with timestamps | **append-only audit events** (`audit_trail` rows: `entity_type='manual_extraction_item'`, `entity_id=item.id`, `action=<stage>:<outcome>`, `actor`, `occurred_at`) — reuses existing audit immutability; no new provenance table |

New convenience columns on `manual_extraction_items` (current-state marker +
fast reporting): `pe_reviewed_by/at`, `pe_qc_by/at` (mirroring the existing
`qc_by/at` pattern). Historical audit events remain authoritative and immutable.

---

## 6. Reassignment behavior

- Reassignment (internal ↔ PE) updates only `manual_extraction_batches.entity_id`
  (and the durable job carrier where applicable) via the existing
  `assign_batch` path, preserving the current audit events.
- Origin/`processing_entity_id` and all completed stage events remain untouched.
- Work resuming after reassignment re-enters through the canonical rework loop
  from the appropriate stage and re-requires downstream gates (CarbonTally QC is
  never skipped because of reassignment).
- PE staff see work only while (and only where) the batch is assigned to their
  entity; after reassignment their /pe queue no longer lists it (assignment
  scope), while internal provenance still shows PE-A.

---

## 7. Authorization model

Identity + membership + resource scope + capability + workflow state (never
URL/route).

- **PE Review:** PE **Reviewer** (frozen role) on PE-assigned work only,
  through `/api/v3/pe/*` (capability `review`). Never on internal work.
- **PE QC:** PE **QC Specialist** on PE-assigned work only through `/api/v3/pe/*`
  (capability `qc`). PE QC is PE-domain only.
- **CarbonTally QC:** CarbonTally internal staff only. Enforcement layers:
  - `require_internal_staff` (entity staff always denied) on ops surfaces;
  - `require_admin()` on `/api/v3/qc/*` (already explicitly denies PE staff);
  - proposed dedicated internal permission `can_qc` granted to internal
    `qc_specialist` and `admin` role rows (staff-role permission JSONB only —
    no new column). Because every CT QC endpoint also enforces the
    internal-staff/admin trust domain, granting `can_qc` on the shared role row
    **cannot** grant a PE QC Specialist CarbonTally QC authority (PE roles are
    gated by PE capabilities and blocked by `require_internal_staff`/
    `require_admin`).
- **CarbonTally internal processing:** internal staff roles (operator/reviewer)
  via `/ops`; PE stages never required.
- **Customer Approval:** organisation owner/admin (D5) or internal staff via the
  existing customer-review surface. Separate from CarbonTally QC.
- Existing capability-name separation is preserved and tested (PE caps never
  intersect `can_review`/`can_process`/`can_manage_staff`/admin role names).



---

## 8. API impact

| Surface | Change |
|---|---|
| PE access contract `/api/v3/pe/*` | add capability-gated `review` (POST `.../pe-review`) and `qc` (POST `.../pe-qc`) actions for PE-assigned items; unchanged authorization model; never exposes CT QC |
| Operations `/api/v3/operations/*` | internal `review` sets `reviewed`; internal items proceed to CT QC; assignment endpoints unchanged; entity-batch isolation unchanged |
| CarbonTally QC `/api/v3/qc/*` | queue filters become stage- and origin-aware (`ct_qc` + `processing_origin`), retaining current origin fields; review action writes the late-gate decision; PE denied (unchanged) |
| Customer Approval `/api/v3/processing/*` | unchanged semantics; only `ct_qc_approved` items reach `customer_review` |
| Shared domain | extend `ITEM_STATUS_FLOW` + transition helpers (domain/partners.py); reuse canonical workflow engine — no duplicate logic |

All endpoints continue to delegate to shared repositories/engines.

---

## 9. UI impact (design only — not implemented)

- **/pe**: shows Extract → Map → Validate → (Calculate) → **PE Review** →
  **PE QC** for PE-assigned work; Data Entry Operator sees extract/map;
  Reviewer sees PE Review; QC Specialist sees PE QC; Admin sees team/entity
  admin. No CarbonTally QC controls, no customer approval controls.
- **/ops**: internal path shows … → Review → **CarbonTally QC** → submit for
  customer approval; processing-origin badge on queue/workbench rows; PE
  (entity-assigned) work visible only to authorized internal QC queues.
- **CarbonTally QC**: dedicated queue/workspace showing `processing_origin`
  (internal vs PE, PE identity where applicable), stage history, and CT QC
  approve/return actions.
- **Customer Approval**: unchanged; provenance/origin summaries visible for
  transparency; remains separate from QC.

---

## 10. Database migration proposal (NOT applied — for approval)

Affected tables:
- `manual_extraction_items` — add:
  - `processing_origin VARCHAR CHECK (...)` NOT NULL DEFAULT 'CARBONTALLY_INTERNAL'
  - `processing_entity_id UUID NULL` FK → `processing_entities(id)` ON DELETE RESTRICT
  - `pe_reviewed_by UUID NULL`, `pe_reviewed_at TIMESTAMPTZ NULL`
  - `pe_qc_by UUID NULL`, `pe_qc_at TIMESTAMPTZ NULL`
  - index `idx_items_processing_origin (processing_origin)`; partial index
    `(processing_entity_id) WHERE NOT NULL`; CHECK guard
    `(processing_origin <> 'PROCESSING_ENTITY' OR processing_entity_id IS NOT NULL)`
    for new PE rows.
- `staff_roles` — data-only permission addition `permissions = permissions || '{"can_qc": true}'`
  for rows `name IN ('qc_specialist','admin')` (internal role rows; PE authority
  still denied by trust-domain checks).
- No change to `processing_entities`, `emission_factors`, batch assignment,
  review/customer tables.

Constraints: additive `ADD COLUMN IF NOT EXISTS` / `ALTER TABLE ... ADD CONSTRAINT
IF NOT EXISTS`-style (idempotent), `CHECK` only on the new column, FK `RESTRICT`.

Backfill strategy: set `processing_origin` for existing rows from the current
batch carrier — `CARBONTALLY_INTERNAL` when `manual_extraction_batches.entity_id
IS NULL`, else `PROCESSING_ENTITY` + `processing_entity_id = batch.entity_id`.
Existing `qc_approved`/`qc_rejected` rows keep their historical meaning
(early extraction QC) and are **not** reinterpreted as late CT QC.

Compatibility strategy: legacy statuses remain valid in
`ITEM_STATUS_FLOW`; new statuses are additive; old consumers continue to see
the same columns they read today.

Rollback strategy: rollback = drop only the new columns/constraints/indexes
(additive, no destructive rewrite); role-permission JSONB change reverted by
`permissions - 'can_qc'`. No historical row is deleted or rewritten beyond the
origin backfill described above.

Data preservation: all existing items, actors, review history, QC history,
customer decisions, audit events, factors, PE relationships preserved.

---

## 11. Compatibility strategy (historical records)

- Historical rows are never silently reinterpreted.
- Existing `qc_approved`/`qc_rejected` (early gate) are labelled historical
  early extraction-QC markers; new work uses the late CT QC gate.
- Legacy internal review (`manual_review_queue`) maps to the canonical internal
  Review stage.
- Durable automatic-job stage history and `document_processing_queue`
  `reprocess_count` remain the authoritative job-side record; items receive the
  origin backfill only.

---

## 12. Test strategy

- Workflow unit tests (transition table): internal path never enters PE stages;
  PE path always includes PE Review → PE QC → CT QC; CT QC never skipped for PE;
  rejections rework correctly.
- Origin tests: origin set once at extraction; reassignment does not change
  origin/`processing_entity_id`; PE-A provenance survives reassignment to
  internal.
- QC queue tests: internal and PE items both reach CT QC; origin field correct.
- API tests: internal staff perform CT QC on both origins; PE staff 403 on CT QC.
- Customer approval tests: only `ct_qc_approved` reaches `customer_review`;
  approval separate from QC.

## 13. Security-negative test strategy

PE Reviewer/QC Specialist cannot perform CT QC; PE cannot reach /ops or /admin
QC surfaces; PE QC Specialist cannot access CT QC via capability name overlap;
cross-PE item access 403; reassigned work respects new assignment scope while
history retains PE-A; direct API calls enforce the same rules as UI.

## 14. Risks

- **Shared staff-role rows**: `qc_specialist` is used by both internal and PE
  staff — mitigated because every CT QC endpoint enforces the internal
  trust domain (`require_internal_staff`/`require_admin`) in addition to
  permissions.
- **Status vocabulary growth**: new statuses are additive but increase the
  state space; mitigated by keeping `ITEM_STATUS_FLOW` single-source and
  reusing rework loops instead of new statuses.
- **Origin backfill** on live rows reflects the *current* carrier for legacy
  rows (best available evidence; historical assignment audit events remain the
  authoritative record where the carrier changed).
- **Durable automatic pipeline** has a parallel job stage machine that must be
  extended consistently (add `ct_qc` insertable stage before `review`); scope
  must be sequenced to avoid drift.

## 15. Explicit items requiring PO approval

1. Approve the canonical status vocabulary (esp. `review`/`reviewed`,
   `pe_review*`, `pe_qc*`, `ct_qc*`) and the late CarbonTally QC gate replacing
   (for new work) the early `extracted`-stage QC semantics.
2. Approve the two new immutable columns on `manual_extraction_items`
   (`processing_origin`, `processing_entity_id`) and the per-stage PE actor
   convenience columns.
3. Approve granting internal `can_qc` permission to `qc_specialist`/`admin`
   staff-role rows (internal QC role separation), with PE authority excluded by
   trust-domain checks.
4. Approve the origin backfill policy for existing rows (from current batch
   carrier; audit remains authoritative for changed carriers).
5. Approve mapping of historical early `qc_approved`/`qc_rejected` rows as
   historical early-QC markers (not late CT QC).
6. Approve sequencing: single idempotent additive migration + domain
   transition-table extension + PE review/QC API actions + CT QC late-gate API
   + UI (PE/ops/CT QC) + regression/negative test suite.

---

## 16. Appendix — trace summary (Extraction → Customer Approval)

Internal (today): item `extracted` → (optional early CT QC) → `mapped` →
`validated` → `calculated` → review queue → `customer_review` → `approved`.
PE (today): item `extracted` → `mapped`/`calculated` via entity endpoints;
CarbonTally-gated statuses blocked → **no onward path** (gap).
Target adds: internal `reviewed → ct_qc → customer_review`; PE
`pe_review → pe_qc → ct_qc → customer_review`.

