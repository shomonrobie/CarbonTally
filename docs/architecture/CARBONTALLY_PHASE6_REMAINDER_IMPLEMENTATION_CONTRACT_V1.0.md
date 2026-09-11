# CarbonTally — Phase 6 Remainder Implementation Contract

**Document ID:** `CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001`
**File:** `docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md`
**Version:** V1.0
**Date:** 10 September 2026
**Status:** **AUTHORITATIVE IMPLEMENTATION CONTRACT — READY FOR PO REVIEW / CP1 EXECUTION**
**Prompt Ref:** `CT-PHASE6-REMAINDER-IC-20260910-001`
**Task type:** contract definition only — **no implementation authorised by the task that produced this document**

---

## 1. Authority and relationships

| Item | Value |
|---|---|
| Policy authority | Product Owner (ratified decisions in `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`, sections `## P6-2C Ratified PO Decisions`, `## P6-2D Ratified PO Decision`, `## P6 Remainder Ratified PO Decisions — 2026-09-10`) |
| Architecture authority | `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (incl. §9 *Processing model — dimensional clarification*) |
| Roadmap authority | `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (§9 Phase 6; **unmodified by this contract**) |
| Origin model | `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4 (*Scope of the origin concept*) |
| Baseline evidence | `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md`; `…_UNIFIED_READINESS_ANALYSIS.md`; `…_PROCESSING_MODEL_RECONCILIATION_REPORT.md`; `…_PROCESSING_MODEL_DOCUMENTATION_AMENDMENT_REPORT.md`; `…_P6_2D_RESIDUAL_ORIGIN_WORDING_CLARIFICATION_REPORT.md`; the P6-2C independent verification report |
| Relationship to Blueprint V1.3 | This contract **implements** the ratified model; it does not amend the Blueprint. Additive, nullable provenance fields only; nothing may contradict Blueprint §9 or §11. |
| Relationship to Roadmap V1.0 | Executes Phase-6 gates **P6-2D → P6-2E → P6-2F** in the ratified order; no reordering, renaming or re-scoping; creates no Phase-7/8 work. |

**Conflict rule:** if this contract conflicts with the PO register or the Blueprint, the register/Blueprint wins and the implementer **STOPS and reports** rather than improvising.

## 2. CP0 status

| Checkpoint | Status |
|---|---|
| **CP0 — PO ratification** | **COMPLETE** (11 decisions ratified 10 Sep 2026) |
| CP1 — P6-2D | NOT STARTED — this contract authorises its *scope*; implementation requires a separate implementation prompt |
| CP2 — P6-2E | NOT STARTED — blocked until CP1 passes and is independently verified |
| CP3 — P6-2F | NOT STARTED — blocked until CP2 passes; must run in a fresh session |

**CP0 exit criteria met:** D6=A, D7=A, D7b=withdrawn, D7c=A, D8=B, D11=A, billing=deferred, D4=out of scope, P6-2F-ACC=A, P6-2F-ENV=A, campaign=A — recorded with policy and implementation status distinguished.

## 3. Processing-model invariants (must be preserved in behaviour)

Seven **separate** concepts:

| # | Concept | Definition for implementation purposes |
|---|---|---|
| 1 | **Actor** | Organisation · Consultant · CarbonTally Internal · Processing Entity · system/automation worker |
| 2 | **Processing mode** | **Automatic** or **Manual** |
| 3 | **Input type** | PDF · CSV · XLS/XLSX · images (where supported) |
| 4 | **Workflow state** | The item/job pipeline state |
| 5 | **Processing origin** | The **manual-processing capacity/control path**: CarbonTally Internal vs Processing Entity |
| 6 | **Provenance** | Evidence of who performed an action + source/factor/machine provenance |
| 7 | **Entitlement** | Owned by the **client Organisation** |

**Automatic vs manual processing is ACTOR-AGNOSTIC.** Therefore:

- Organisation **may** perform automatic processing; **may** perform manual correction/mapping/validation/calculation.
- Consultant **may** perform automatic processing where authorised; **may** perform manual processing/correction where authorised.
- CarbonTally Internal **may** perform automatic and/or manual processing where authorised.
- Processing Entity participates **according to its existing authorised processing capacity/workflow** (a *manual* capacity; no automatic channel).
- Automatic processing **may fall back to manual processing** (existing confidence/validation gates → human correction → continue).

**Prohibited reinterpretations:** `CONSULTANT = MANUAL`; `ORGANISATION = AUTOMATIC`; `CARBONTALLY INTERNAL = AUTOMATIC`; `PROCESSING ENTITY = MANUAL` as a universal equivalence over all manual work.

**Implementation consequence:** no authorisation or mode branch may key on actor-domain constants except where the existing architecture already does (e.g. PE surface confinement). Mode continues to be determined by the existing derived predicate, never by actor identity.

## 4. `processing_origin` — critical constraint

`processing_origin` **is not** an actor identity, **is not** a processing mode, **is not** a replacement for Consultant or Organisation, and **is not** a generic provenance field. It represents the existing **Internal-vs-Processing-Entity processing-origin / control-path** distinction, stored immutably and write-once, driving stage routing (`review` vs `pe_review`) and the applicable upstream controls.

**Hard prohibitions (binding on CP1–CP3):**

1. Do **not** introduce `CONSULTANT` (or any actor name) as a `processing_origin` value.
2. Do **not** change the `processing_origin` CHECK constraint or its two-value vocabulary (`CARBONTALLY_INTERNAL`, `PROCESSING_ENTITY`).
3. Do **not** create consultant-specific `review` / `pe_review` routing.
4. Do **not** create queue semantics based on "consultant-as-origin".
5. Do **not** reinterpret `processing_origin` as actor identity, mode or generic provenance.

**Status:** the Consultant-origin concept is **withdrawn / rejected** by PO decision (`PO-PHASE6-D7b-R-20260910`). There is no open question to implement.

## 5. Change classification rules

Every proposed change must be classified as exactly one of:

| # | Class | Meaning |
|---|---|---|
| 1 | **Preserve** | Existing behaviour that must not change; only regression protection added |
| 2 | **Verify** | Existing behaviour asserted against the contract with no code change (evidence required) |
| 3 | **Production code change required** | Behaviour must be added/altered |
| 4 | **Database migration required** | Additive, nullable schema change (never destructive) |
| 5 | **RLS change required** | Policy change — **must be avoided**; if it appears necessary, STOP and report |
| 6 | **Test-only change** | New/updated automated tests |
| 7 | **E2E infrastructure / fixture change** | Browser/E2E harness or fixtures |
| 8 | **Documentation-only** | Reports, evidence records, prompt-history |

**"Must exist" vs "must be changed":** a ratified decision does **not** imply a code change. For each decision this contract states (a) that the behaviour **must exist** and (b) whether anything must actually **be changed**. Where behaviour already exists, the obligation is *preserve + verify* (classes 1–2), not redesign.

**Baseline at contract date (re-measure, never assume):** `pytest -q tests/unit` → **1,606 tests, EXIT 0**; `supabase/migrations/` → **52** files (`YYYYMMDDHHMMSS_<slug>.sql`); the consultant capability model = the existing six-flag set; one billing charge site; the frozen P6-2C invariants (§10).

## 6. CP1 — P6-2D contract (D6 · D7 · D7b · D7c)

Held refs: `PO-PHASE6-D6-R-20260910`, `PO-PHASE6-D7-R-20260910`, `PO-PHASE6-D7b-R-20260910`, `PO-PHASE6-D7c-R-20260910`.

### 6.1 D6 — Entitlement timing

**Must exist (policy):** entitlement owned by the **client Organisation**; consultant submission performs a **non-charging** availability check; submission does not consume entitlement; the **canonical approval-time check** remains authoritative for enforcement/consumption; actor and mode never transfer ownership.

**Must be changed: NOTHING** — classification **1 Preserve** + **2 Verify**.

Evidence of existing implementation (verify, do not rebuild):

- `backend/services/billing.py` — `ensure_processing_entitlement(organization_id)` (read-only, fail-closed 403, no charge/consumption/mutation).
- `backend/api/v3_processing_workflow.py:714` — that call inside the **consultant submit** route, before mutation.
- `backend/api/v3_processing_workflow.py:920` — the single `charge_processing(...)` call site on the **customer approval** route, idempotency key `charge:item:{item_id}`.

**Required work:** contract-named regression coverage only (**class 6**): no active entitlement ⇒ consultant submission **403** with zero mutation/charge; submission never charges; approval charge single and idempotent; ownership resolved server-side from `batch.organization_id`.

**Prohibitions:** no entitlement redesign; no consultant/actor-owned entitlement; no charging at submission; no new billing semantics.

### 6.2 D7 — Firm provenance + processing-mode provenance

**Must exist (policy):** durable, **server-derived** provenance capturing the relevant **firm** at action time, plus **processing-mode** provenance preserved **separately** where the architecture requires it; actor / firm / mode / origin / state / entitlement remain distinct; historical provenance stable and not rewritten by later membership/grant changes.

**Current provenance storage (verified by inspection in this contract task):**

| Location | Fields | Covers |
|---|---|---|
| `manual_extraction_items` | `extracted_by`, `extracted_at`, `assigned_to`, `assigned_by`, `assigned_at`, `qc_by`, `qc_at`, `qc_notes`, `qc_approved`, `customer_reviewed_by`, `customer_reviewed_at`, `customer_approved`, `emission_factor_used`, `calculated_emissions_kg_co2e` | human actor identity per stage, factor, decision |
| `document_processing_queue` (job) | `automation_extracted_data`, `automation_provider`, `automation_model` (write-once) | machine/automatic actor |
| `emissions_logs` / calculation snapshots | `calculated_by`, `calculated_at`, `performed_by`, `request_id`, `factor_kind`, `customer_factor_id`, `source_item_id`, `source_file`, `source_page` | calculation provenance chain |
| `audit_trail` (+ `api/audit_helpers.py`) | `performed_by`, `action_type`, `record_id`, `metadata` (actor, state transitions) | append-only audit |
| `work_item_assignments` (D38 ledger) | `assignee_kind`, `assigned_to`, `processing_entity_id`, `assigned_by`, `actor_domain`, `previous_*` | assignment provenance |
| `manual_extraction_items` | `processing_origin`, `processing_entity_id` (immutable) | origin (capacity/control path) |

**Genuinely missing (the D7 gap):** the acting **consultant firm** is recorded **nowhere**; **processing mode** exists only as a *derived* predicate (`backend/api/processing_mode.py::item_is_automatic`) and is not stored as explicit provenance.

**Consultant actions requiring capture:** `start`, `extract`, `map`, `validate`, `calculate`, `consultant-review`, `consultant-submit` (`POST /api/v3/processing/items/{id}/…`).

**Classification:**

| Element | Class |
|---|---|
| Firm-at-action-time capture (server-derived from the authorised grant) | **3 Production code change** |
| Processing-mode provenance captured at the same point | **3 Production code change** |
| Additive, nullable storage for the above | **4 Migration (additive-only, nullable)** |
| Existing actor/factor/machine provenance | **1 Preserve** |
| Existing `item_is_automatic` predicate semantics | **1 Preserve** — must not change |
| Firm/mode never accepted from a request body | **3** (enforcement) |
| Regression + negative tests | **6** |
| RLS | **5 — NOT required.** An additive nullable column inherits the existing posture; **RLS must remain unchanged**. If a policy change appears necessary: **STOP and report**. |

**Migration rules:** additive + nullable only; no `NOT NULL`; no default-based fabrication; no UPDATE/backfill of historical rows; existing rows stay valid with NULL provenance; reversible by dropping the added column.

### 6.3 D7c — No historical backfill

**Must exist (policy):** **no historical provenance backfill.** Prohibited: fabricated historical firm provenance; inferred historical actor→firm mapping; synthetic historical provenance; retrospective reinterpretation of existing rows. Prospective capture only.

**Classification: 1 Preserve (prohibition)** + **6 tests**.

**Migration implications:** if the D7 change adds a nullable column, the migration must contain **no** `UPDATE … SET` backfill, **no** `DEFAULT` that fabricates provenance, and **no** derivation from membership/grant tables. Existing historical rows remain valid and unchanged (NULL provenance where never captured). Any enforcement must be prospective (write path), never retro-fit to history.

### 6.4 CP1 — deliverables, evidence and stop conditions

**Deliverables:** production change (class 3); one additive nullable migration (class 4); focused tests (class 6); regression additions (class 6); an evidence record (class 8).

**Required evidence:** focused-suite result; targeted regression result; full `pytest -q tests/unit` result with the collected count re-measured against the recorded baseline; migration file path + before/after schema evidence for the added column(s); proof of no backfill; RLS-unchanged evidence; the two-value `processing_origin` regression assertion; a per-item list of every file changed with its classification.

**STOP if:** a second migration appears necessary; an RLS change appears necessary; any origin/CHECK/routing change appears necessary; a new role/capability/permission appears necessary; the migration cannot be made additive and nullable; or any §10 frozen invariant would change.

### 6.5 D7b — explicitly closed (retained statement)

**Hard constraint:** D7b is withdrawn/rejected as a proposed model; there is **no** open question. Do **not**: add Consultant as `processing_origin`; create a Consultant-origin CHECK value; change origin routing; create new origin semantics; reinterpret origin as actor identity. **Classification: 1 Preserve** + **6 Verify** (a regression test asserting the two-value vocabulary and the absent consultant value is required evidence).

## 7. CP2 — P6-2E contract (D8 · D11)

Held refs: `PO-PHASE6-D8-20260910`, `PO-PHASE6-D11-20260910`.

### 7.1 D8 — Consultant conversation model

**Must exist (policy):** **reuse the existing conversation model.** No dedicated consultant conversation kind during Phase 6 unless a later concrete product/security requirement is demonstrated and separately PO-approved.

**Current state (verified):** `api/v3_messaging.py` admits consultants through the active grant (participant role `consultant`) within the existing org-scoped conversation family; `data/messaging.py` uses `conversation_kind`, whose only non-customer value in use is `entity` (PE messaging).

**Must be changed: NOTHING** — **1 Preserve** + **2 Verify**; consultant-participation and isolation tests are **6**.

**Prohibitions:** no new conversation kind; no schema expansion; no weakening of conversation authorisation; no change to the PE entity-kind guard.

### 7.2 D11 — Consultant lifecycle notifications (five events)

**Must exist (policy):** lifecycle notifications for **1 Accepted · 2 Submitted to QC · 3 QC outcome · 4 Customer decision · 5 Rework**, using deterministic idempotent event keys, the existing idempotent notification infrastructure, server-side recipient derivation from the actual workflow relationship, and no cross-organisation/firm/actor leakage.

**Existing infrastructure (preserve):** `backend/data/notifications.py::create_idempotent` (`event_key` dedupe, recipient type/id, `actor_domain`); the emitter pattern in `backend/services/work_items.py` (`notification_type="work_item.assigned"`, `event_key=f"work_item:{action}:{item_id}:{…}"`).

**Existing emit points to integrate with (no new workflow):**

| Event | Trigger (existing route/state) | Recipients (server-derived) |
|---|---|---|
| 1 Accepted | engagement acceptance (P6-1C engagement confirmation surface) | acting firm's authorised members; client org owner/admin |
| 2 Submitted to QC | `POST /api/v3/processing/items/{id}/consultant-submit` | firm members (authorised); CarbonTally QC/Ops intake |
| 3 QC outcome | CT-QC decision route (`api/v3_operations.py` → `ct_qc_approved` / `ct_qc_rejected`) | firm members; client org owner/admin |
| 4 Customer decision | `POST /api/v3/processing/items/{id}/customer-review` | firm members; client org owner/admin |
| 5 Rework | QC-reject / rework transition back to extraction/mapping | firm members; the responsible processor |

**Requirements per event:** deterministic, server-generated, idempotent, replay-safe `event_key`; payload limited to what the recipient may see; recipient list computed server-side from the workflow relationship (never from a request body); dedupe via `create_idempotent`; **no notification on a denied action**; no cross-org/cross-firm leakage.

**Classification:** event constants + emit sites + recipient derivation = **3**; reuse of `create_idempotent` = **1**; idempotency/dedupe/isolation/denial tests = **6**; **no migration** (the notifications store already carries `event_key`) — if a migration appears necessary, STOP and report.

**Explicit non-decision:** exact key strings and the recipient matrix must be **derived in the implementation session** from existing architecture/code; this contract does not invent them.

## 8. Billing constraint

**Ratified: automatic job-review billing remains deferred** (`PO-PHASE6-BILL-DEFER-20260910`; extends `PO-P6-2C-D3-20260910`). During P6-2D/E/F: **no** billing redesign; **no** new billing semantics; **no** new charging state; **no** subscription/credit architecture change; **no** added/removed charge; **no** resolution of the automatic job-review policy question.

**Preserve (1) and verify (2):** the single charge site at customer approval; idempotency key `charge:item:{item_id}`; no charge on any denied path; the non-charging entitlement preflight (D6); the job-review path continuing to stamp without charging.

**Classification:** **1 Preserve** + **2 Verify** + **6 tests**. `backend/services/billing.py` must not be modified except where D6 *verification* requires a test-only change.

## 9. D4 — out of scope (hard exclusion)

PE ↔ Consultant handoff is **OUT OF SCOPE** (`PO-PHASE6-D4-20260910`). Do not implement it; do not create workflow states, assignment semantics, authorisation flows, roles or capabilities for it. Any prompt/design assuming D4 work must be **rejected and reported**, not absorbed.

## 10. Frozen invariants — must survive CP1–CP3 unchanged

**P6-2C frozen invariants (re-confirmed in the PO register; class 1 Preserve, class 6 for regression coverage):**

1. Client-created (pre-existing-org) consultant engagements remain supported; no ownership cloning of the client organisation.
2. The Consultant capability model is the **existing six-flag set** — no new capability flags.
3. Consultant work is a **capacity/control-path** participation within the existing workflow — the state machine is unchanged.
4. Automatic processing remains **CarbonTally-staff-only** — consultants receive no automatic-processing channel.
5. Automatic-processing **provider selection remains internal** — never consultant-selectable.
6. Consultant data visibility is **grant-scoped** — without an active grant, no consultant access to client data.
7. `processing_origin` remains immutable and outside Consultant onboarding — one origin is set once per item.
8. Items processed pre-engagement remain visible but **un-entitled** for consultant rework — entitlements stay client-organisation-owned.
9. PE↔Consultant handoff remains out of scope (see §9).
10. The frozen workflow-state vocabulary (`extracted → mapped → validated → pending_review | pe_review → completed`, with `blocked`/rework paths) is unchanged; existing status transitions must not be amended.

**Frozen UX/system decisions in force (class 1):** D17 master-data IA; D19 processing workbench (workbench-first structure, source/validation/evidence panes, keyboard access); D21 design system (semantic tokens only); N1 authenticated messaging (no unrestricted Customer↔PE channel; consultants message only within authorised active-client relationships); N3 configurable retention (server-side). Any change to these requires PO review, not implementer discretion.

## 11. CP3 — P6-2F contract (final UI/UX + E2E security acceptance)

Held refs: `PO-PHASE6-F-ACC-20260910` (full acceptance + mandatory independent verification), `PO-PHASE6-F-ENV-20260910` (isolated synthetic E2E environment).

### 11.1 Scope of the final gate

P6-2F is the **final Phase-6 acceptance gate**: end-to-end, role-complete, security-focused, evidence-backed. It covers the complete end-user processing workflows:

- **Organisation** workflows (upload → … → customer approval).
- **Consultant** workflows (view; manual extraction/mapping/validation/calculation where granted; consultant review; consultant submit to CT-QC; rework participation; messaging within the active-client relationship; lifecycle notifications).
- **CarbonTally internal** workflows (operations queue; CT-QC decision; assignment; oversight).
- **Processing Entity** workflows (PE review queue; PE-origin item processing; PE source-document boundary).
- **Automatic** processing (CarbonTally-staff-triggered only) and **manual** processing.
- **Automatic → manual fallback** (confidence/validation gate → human correction → continue).
- Review/QC, approval, entitlement, provenance, notifications and billing invariants (unchanged/deferred — §8).

### 11.2 Mandatory security verification focus (ALLOW and DENY cases)

Authentication · organisation isolation · firm isolation · active-grant enforcement · canonical capability resolver · processing-entity authorisation · operations authorisation · organisation-admin approval authority · approval boundary · CT-QC boundary · processing-origin integrity · provenance integrity · entitlement integrity · billing invariants · IDOR · actor injection · alternate-route bypass · replay · idempotency · concurrency-sensitive paths · event-key duplication · UI-only authorisation bypass · unauthorised capability/role creation.

Every unexpected ALLOW is a **material finding** and blocks acceptance until resolved or explicitly PO-accepted.

### 11.3 Binding statement

> **UI visibility is never the security boundary.** Server-side authorisation remains authoritative for every operation; a hidden, disabled, unmounted or un-routed control is not authorisation.

### 11.4 Frontend deliverables (D19/D21 conformant)

Where the backend capability already exists but the UI does not surface it, P6-2F adds the consultant-facing surface: consultant review/submit controls in the processing workbench; consultant status/queue context; firm/actor provenance display (business language, not UUID-first); notification surfacing; entitlement/approval-state clarity; scoped messaging entry points. Classification **3** + **7**. No new design system; semantic tokens only; no routes/roles/capabilities beyond those already authorised.

### 11.5 Classification

Consultant workflow UI = **3**; E2E personas/fixtures/runner = **7**; acceptance report + evidence = **8**; existing D19/D21/N1 behaviour = **1 Preserve**; no schema/RLS/billing change (**4/5 excluded** unless a STOP condition is raised and PO-approved).

## 12. P6-2F E2E environment requirements

A **dedicated, isolated E2E environment** is mandatory (`PO-PHASE6-F-ENV-20260910`):

- Synthetic/test data only; **no production data**; **no destructive operations** against production or the investor-demo dataset.
- A clearly labelled, **isolated** synthetic dataset created for E2E. Never reseed, truncate or globally modify the investor demo (`tools/seed_investor_demo/DEMO_IDENTITIES.md`); all E2E records must be created, tracked and cleaned up by the test itself.
- Representative roles: organisation owner/admin/member/viewer; consultant (firm principal + member); CarbonTally operator/reviewer/QC; PE manager/staff — with at least **two organisations, two firms and two PEs** so isolation is provable.
- Realistic authentication (Supabase Auth) and realistic RLS/security boundaries — the **same policies as production**.
- Reproducible fixtures and **resettable** test state, with verified teardown.
- Safe test billing behaviour: entitlement/charge assertions must not create real charges; billing remains deferred and **asserted, not exercised**.
- Negative-security testing must be possible (cross-org, cross-firm, cross-PE, viewer-write, staff-admin escalation, replayed and injected-actor attempts).
- **No weakening of production security to make E2E pass** — never disable RLS, relax a policy or widen a capability for test convenience.

**Existing harness (reuse, extend):** `qa_harness/scripts/run_all.py` (with `--no-ai` deterministic mode), `run_api.py`, `run_db.py`, `run_workflows.py`, `run_browser.py`, `preflight.py`. The browser layer consumes Playwright specs (currently only `tests/example.spec.ts`); extending it is class 7. Harness outputs must distinguish **PASS / FAIL / SKIPPED / BLOCKED / UNVERIFIED** and must never report acceptance merely because the harness ran.

## 13. Mandatory checkpoint model

| Checkpoint | Content | Gate rule |
|---|---|---|
| **CP0** | PO ratification of all 11 remainder decisions | **COMPLETE** |
| **CP1** | P6-2D implementation → focused tests → regression → evidence → **independent verification** | P6-2E **cannot begin** until CP1 passes and is independently verified |
| **CP2** | P6-2E implementation → focused tests → regression → evidence → **independent verification** | P6-2F **cannot begin** until CP2 passes and is independently verified |
| **CP3** | P6-2F implementation (fresh session) → UI/E2E testing → full regression → **mandatory independent verification** | P6-2F is **not self-certified**; acceptance requires independent verification evidence |

**Rules:** each checkpoint ends with a written report containing files changed (with classification), tests run, evidence, residual risk, and an explicit verdict. No checkpoint may be declared passed on the basis of a single successful call, a rendering page, or a moving spinner. Skipped/blocked items must be reported as such — never silently converted to PASS.

## 14. Fresh-session requirement

> **P6-2F implementation must begin in a fresh Cline session.**

This is required to reduce implementation-session confirmation bias and to give the final UI/security gate an independent implementation context, distinct from the sessions that produced P6-2D/P6-2E. CP1 and CP2 may run in their own sessions (each starting from verified state); CP3 must not inherit CP2's session context.

## 15. Consolidated security invariants

**Identity and boundaries:** authenticated access only; organisation isolation; consultant-firm isolation; active-grant enforcement; canonical capability resolution (single resolver — no ad-hoc role checks); PE authorisation; operations authorisation; organisation-admin approval authority; approval boundary; CT-QC enforcement.

**Model integrity:** processing-origin immutability/integrity (two values only); durable server-derived provenance; entitlement ownership by the client organisation.

**Financial integrity:** append-only audit behaviour; billing single-charge behaviour; no-charge-on-denial; billing idempotency; deferred automatic job-review billing unchanged.

**Attack resistance:** RLS enforcement (never disabled/bypassed); IDOR resistance; actor-injection resistance; alternate-route resistance; concurrency safety; replay resistance; event idempotency (deterministic keys); no UI-only authorisation; no unauthorised new role/capability/permission.

**Verification duty:** each invariant above must have at least one DENY-side test proving the negative case, not only an ALLOW-side happy path.

## 16. Scope boundaries

### 16.1 IN SCOPE

Everything required for D6, D7, D7b closure, D7c, D8, D11, P6-2D, P6-2E, P6-2F, the E2E security acceptance, and their required tests, evidence and reports — plus the minimum frontend surface needed to make consultant work usable in P6-2F.

### 16.2 OUT OF SCOPE (explicit)

- Phase 7 Auditor / Assurance.
- Phase 8 Advanced Analytics.
- PE ↔ Consultant handoff (D4).
- Billing redesign, new billing semantics, or resolution of automatic job-review billing.
- Unrelated refactoring, unrelated schema changes, unrelated UI redesign.
- New roles, new capabilities, new permissions.
- `CONSULTANT` as a `processing_origin` value; any origin CHECK/routing/semantic change.
- Historical provenance backfill.
- Any change to the investor-demo dataset, RLS policies, or frozen D17/D19/D21/N1/N3 decisions.
- Automatic-processing availability or provider selection for consultants (frozen P6-2C invariant 4/5).

## 17. Implementation boundary — change classification summary

| Workstream item | Must exist | Must be changed | Class |
|---|---|---|---|
| D6 entitlement ownership + non-charging preflight | yes | no | 1 + 2 |
| D6 approval-time canonical charge | yes | no | 1 + 2 |
| D6 regression coverage | — | yes | 6 |
| D7 firm provenance captured at action time | yes | **yes** | 3 |
| D7 processing-mode provenance (separate from origin) | yes | **yes** | 3 |
| D7 additive nullable storage | yes | **yes** | 4 |
| D7 existing actor/factor/machine provenance | yes | no | 1 |
| D7 RLS | yes (unchanged) | **no** | 5 — not required |
| D7b closure (no consultant origin) | yes | no | 1 + 6 |
| D7c no backfill | yes (prohibition) | no | 1 + 6 |
| D8 conversation reuse | yes | no | 1 + 2 |
| D11 five lifecycle events | yes | **yes** (constants, emit sites, recipients) | 3 |
| D11 idempotent notification infrastructure | yes | no | 1 |
| D11 event/idempotency/isolation tests | — | yes | 6 |
| P6-2F consultant UI surface | yes | **yes** | 3 + 7 |
| P6-2F E2E environment + fixtures | yes | **yes** | 7 |
| Acceptance/verification reports | yes | yes | 8 |
| D17/D19/D21/N1/N3, P6-2C invariants | yes | no | 1 |

**Rule:** no item may be upgraded to "must be changed" during implementation without a recorded reason and, where it touches §4/§8/§9/§10, an explicit PO check.

## 18. Required evidence and independent verification

**Every checkpoint must produce (class 8 documentation):**

1. Scope executed, with the PO decision refs translated.
2. Files changed, each labelled with its classification 1–8.
3. Tests added/changed and the exact commands run, with raw results.
4. Regression result for the full unit suite, with the collected count compared against the **1,606 / EXIT 0** baseline (a reduced count must be explained).
5. Database/migration evidence: file path, before/after column evidence, proof of additivity/nullability, proof of no backfill.
6. Security evidence: ALLOW and DENY cases, with the actor (role/org/firm/PE), route, and expected vs actual status.
7. Explicit statement of what was **not** changed (RLS, billing, origin vocabulary, investor demo).
8. Residual risk, unknowns and any BLOCKED/UNVERIFIED item.
9. Git state (branch, HEAD, changed-file list) — no secrets, no credentials, no signed URLs.

**Independent verification (mandatory for every checkpoint):** a separate verification pass (independent reviewer/agent) must re-derive the claims from the runtime, database, tests and diffs — not from the implementation report's prose — and must return `VERIFIED` / `PARTIALLY VERIFIED` / `NOT VERIFIED` with its own evidence. P6-2F acceptance is **not** self-certified.

## 19. Stop conditions

An implementation session must **STOP and report** (verdict `BLOCKED — CLARIFICATION REQUIRED`) if any of the following occurs:

1. A decision requires a **PO decision** (business policy, who can approve, who can be a recipient, retention, communication boundaries, capability scope).
2. An **RLS change** appears necessary, or RLS would need to be bypassed.
3. A **second migration** (or any destructive/non-additive migration) appears necessary.
4. Any change to **`processing_origin`** values, CHECK constraint, routing or vocabulary appears necessary.
5. A **new role, capability or permission** appears necessary.
6. A **billing** semantic change appears necessary.
7. Any **§10 frozen invariant**, §4 constraint or §9 exclusion would be violated.
8. A requirement conflicts with the PO register or Blueprint V1.3.
9. Evidence cannot be produced for a claimed pass.
10. The investor-demo dataset would need mutation that cannot be safely isolated and cleaned up.

## 20. Handoff

**Next task (separate prompt):** CP1 / P6-2D implementation session, executed strictly against §6 of this contract, ending with the §18 evidence set and independent verification.

**Do not begin CP2 or CP3** until the preceding checkpoint has passed and been independently verified. **Do not modify this contract** during implementation: if it must change, produce a revision with a new version number, a change list, and PO notification.

**Related records:** register `…_P6_2_PO_DECISION_REGISTER.md`; ratification report `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md`; prompt-history `docs/cline/prompt-history/CT-PHASE6-PO-RAT-20260910-001.md` and `…/CT-PHASE6-REMAINDER-IC-20260910-001.md`.






