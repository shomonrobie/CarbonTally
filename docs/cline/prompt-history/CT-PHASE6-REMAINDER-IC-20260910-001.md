# Cline Prompt History — `CT-PHASE6-REMAINDER-IC-20260910-001`

**Prompt Ref:** `CT-PHASE6-REMAINDER-IC-20260910-001`
**Prompt datetime:** 2026-09-10 (local session, Asia/Dhaka +0600); recorded 2026-09-10 18:32:53 +0600 (pre-edit state captured)
**Task type:** Documentation / Implementation Contract Definition ONLY
**Phase:** Phase 6 · Current gate **CP0 (complete)** · Next gate **P6-2D**
**Response Ref:** `CT-PHASE6-REMAINDER-IC-20260910-001-R1`
**Response datetime:** 2026-09-10 (same session)
**Verdict:** **IMPLEMENTATION CONTRACT COMPLETE — READY FOR PO REVIEW**

---

## 1. Exact prompt text

```text
# CLINE TASK — CREATE PHASE 6 REMAINDER IMPLEMENTATION CONTRACT

**Prompt Ref:** `CT-PHASE6-REMAINDER-IC-20260910-001`
**Task Type:** Documentation / Implementation Contract Definition ONLY
**Phase:** Phase 6
**Current Gate:** CP0 complete
**Next Gate:** P6-2D
**Implementation:** **NOT AUTHORIZED IN THIS TASK**

---

## 1. OBJECTIVE

Create the authoritative **Phase 6 Remainder Implementation Contract** that translates the already-ratified Product Owner decisions into exact, bounded implementation requirements for:

* **CP1 / P6-2D**
* **CP2 / P6-2E**
* **CP3 / P6-2F**

This task is strictly a **contract-definition task**.

Do NOT implement code.

Do NOT modify database schema.

Do NOT create migrations.

Do NOT modify RLS.

Do NOT modify UI.

Do NOT modify billing.

Do NOT refactor existing production components.

Do NOT start P6-2D.

The purpose of this task is to establish the exact implementation boundary that a subsequent Cline implementation session must follow.

---

# 2. AUTHORITATIVE SOURCES — READ FIRST

Before writing the contract, inspect and reconcile the following authoritative documents:

1. `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`

2. `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`

3. `docs/architecture/CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md`

4. `docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md`

5. `docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`

6. `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`

7. `docs/architecture/CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md`

8. `docs/cline/CARBONTALLY_PHASE6_REMAINDER_UNIFIED_READINESS_ANALYSIS.md`

9. `docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_RECONCILIATION_REPORT.md`

10. `docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_DOCUMENTATION_AMENDMENT_REPORT.md`

11. `docs/cline/CARBONTALLY_P6_2D_RESIDUAL_ORIGIN_WORDING_CLARIFICATION_REPORT.md`

12. `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md`

Also inspect the relevant prompt-history records, particularly:

`docs/cline/prompt-history/CT-PHASE6-PO-RAT-20260910-001.md`

and the P6-2D model/documentation prompt-history records.

---

# 3. FUNDAMENTAL PROCESSING MODEL — MUST BE PRESERVED

The implementation contract MUST explicitly preserve the foundational CarbonTally processing model.

These concepts are separate:

1. **Actor**

   * Organisation
   * Consultant
   * CarbonTally Internal
   * Processing Entity
   * system/automation where applicable

2. **Processing Mode**

   * Automatic
   * Manual

3. **Input Type**

   * PDF
   * CSV
   * XLS/XLSX
   * images where supported

4. **Workflow State**

5. **Processing Origin**

   * existing Internal / PE distinction
   * NOT an actor
   * NOT a processing mode

6. **Provenance**

7. **Entitlement**

The contract MUST explicitly state:

> Automatic vs Manual processing is actor-agnostic.

Therefore:

* Organisation may perform automatic processing.
* Organisation may perform manual correction/mapping.
* Consultant may perform automatic processing where authorized.
* Consultant may perform manual processing/correction where authorized.
* CarbonTally Internal may perform automatic and/or manual processing where authorized.
* Processing Entity participates according to its existing authorized processing capacity/workflow.
* Automatic processing may fall back to manual processing.

Do NOT reinterpret:

`CONSULTANT = MANUAL`

or:

`ORGANISATION = AUTOMATIC`

or:

`PROCESSING ENTITY = MANUAL`

as universal actor/mode equivalences.

---

# 4. PROCESSING ORIGIN — CRITICAL CONSTRAINT

The contract MUST preserve the existing meaning of `processing_origin`.

`processing_origin` is NOT:

* an actor identity
* a processing mode
* a replacement for Consultant
* a replacement for Organisation
* a generic provenance field

It represents the existing Internal-vs-Processing-Entity processing-origin/control-path distinction.

The contract MUST explicitly prohibit introducing:

`CONSULTANT`

as a new processing-origin value.

No CHECK constraint, routing vocabulary, state-machine vocabulary, or schema vocabulary should be changed to introduce Consultant as an origin.

The previously proposed Consultant-origin concept is **withdrawn/rejected** by PO decision.
```

*(prompt continues — see §1b)*

## 1b. Exact prompt text (continued)

```text
---

# 5. CP1 — P6-2D IMPLEMENTATION CONTRACT

Define the exact implementation boundary for P6-2D.

The contract MUST cover:

## D6 — Entitlement

Implement/verify the ratified D6 model:

* entitlement belongs to the client Organisation
* submission preflight must remain non-charging
* canonical approval-time enforcement/consumption must remain authoritative
* actor does not transfer ownership
* processing mode does not transfer ownership
* consultant participation does not transfer entitlement
* processing entity participation does not transfer entitlement

If existing implementation already satisfies the ratified contract, specify that it must be preserved rather than unnecessarily redesigned.

Identify precisely what must be changed versus what must merely be verified.

---

## D7 — Provenance

Implement/verify the ratified D7 model.

The system must support durable, server-derived provenance that captures the relevant actor/firm provenance at action time.

Requirements:

* provenance must be server-derived
* provenance must not be actor-supplied
* historical provenance must remain stable
* actor identity and firm identity must remain distinct concepts
* processing mode provenance must remain separate from actor/firm provenance
* processing origin must remain separate from provenance
* workflow state must remain separate from provenance
* entitlement must remain separate from provenance

The contract must identify:

* where provenance is currently stored
* which actions require provenance
* what fields already exist
* what fields, if any, are genuinely missing
* whether a migration is required
* whether any migration must be additive only

Do NOT infer or fabricate historical provenance.

---

# 6. D7b — EXPLICITLY CLOSED

Record the following as a hard implementation constraint:

**D7b is withdrawn/rejected as a proposed model.**

There is no open question requiring implementation.

Do NOT:

* add Consultant as `processing_origin`
* create a Consultant-origin CHECK value
* change origin routing
* create new origin semantics
* reinterpret processing origin as actor identity

---

# 7. D7c — HISTORICAL DATA

Implement the ratified D7c decision:

**No historical provenance backfill.**

Requirements:

* no fabricated historical firm provenance
* no inferred historical actor-to-firm mapping
* no synthetic historical provenance
* no retrospective reinterpretation of existing rows
* prospective capture only where required

If a migration is required for a new nullable/additive field, document the exact reason and ensure existing historical records remain valid without fabricated values.

---

# 8. P6-2E — CONSULTANT VOCABULARY / D8 / D11

Define the CP2 contract.

## D8 — Conversation Model

Use the existing conversation model.

Do NOT introduce a dedicated Consultant conversation type merely for Phase 6.

If an existing conversation mechanism already supports the required consultant workflow, reuse it.

Any future dedicated conversation kind must require a separate concrete requirement and PO decision.

---

## D11 — Consultant Lifecycle Events

Implement the ratified five-event model:

1. Accepted
2. Submitted to QC
3. QC outcome
4. Customer decision
5. Rework

The contract must define for each:

* event trigger
* event identity
* event payload requirements
* recipient determination
* authorization requirements
* idempotency behavior
* duplicate prevention
* leakage/isolation requirements

Event keys must be:

* deterministic
* server-generated
* idempotent
* safe under replay

Recipients must be determined server-side.

Do NOT trust client-supplied recipient identity.

Events must not leak information across organisations/firms that should be isolated.

---

# 9. BILLING CONSTRAINT

The existing billing model must NOT be redesigned during this campaign.

The ratified decision is:

**Automatic job-review billing remains deferred.**

Do NOT introduce:

* new billing semantics
* new charging states
* new subscription architecture
* new credit architecture
* billing redesign
* unrelated payment changes

Any existing billing invariant relevant to approval must remain protected.

---

# 10. D4 — OUT OF SCOPE

PE ↔ Consultant handoff is explicitly:

**OUT OF SCOPE FOR PHASE 6**

Do not implement it.

Do not create new workflow states for it.

Do not create new roles/capabilities solely for it.

It remains a future decision.
```

*(prompt continues — see §1c)*

## 1c. Exact prompt text (continued)

```text
---

# 11. CP3 — P6-2F FINAL ACCEPTANCE CONTRACT

Define P6-2F as the final Phase 6 UI/UX + E2E security acceptance gate.

The contract must cover the complete end-user processing workflows, including relevant:

* Organisation workflows
* Consultant workflows
* CarbonTally internal workflows
* Processing Entity workflows
* automatic processing
* manual processing
* automatic → manual fallback
* review/QC
* approval
* entitlement
* provenance
* notifications
* billing invariants

The final gate must include security verification for:

* authentication
* organisation isolation
* firm isolation
* active grants
* canonical capability resolver
* processing-entity authorization
* operations authorization
* organisation-admin authority
* approval boundary
* CT-QC boundary
* processing-origin integrity
* provenance integrity
* entitlement integrity
* billing invariants
* IDOR
* actor injection
* alternate-route bypass
* replay
* idempotency
* concurrency-sensitive paths
* event-key duplication
* UI-only authorization bypass
* unauthorized capability/role creation

The contract must explicitly state:

> UI visibility is never the security boundary.

Server-side authorization remains authoritative.

---

# 12. P6-2F E2E ENVIRONMENT

The contract must require a dedicated isolated E2E environment.

Requirements:

* synthetic/test data
* no production data
* no destructive production operations
* representative roles
* realistic authentication
* realistic RLS/security boundaries
* reproducible fixtures
* resettable test state
* safe test billing behavior
* no weakening of production security merely to make E2E tests pass

The E2E environment must allow negative-security testing.

---

# 13. MANDATORY CHECKPOINT MODEL

The implementation contract MUST preserve these hard checkpoints:

### CP0

PO ratification — COMPLETE.

### CP1

P6-2D implementation
→ focused tests
→ regression
→ evidence
→ independent verification

P6-2E cannot begin until CP1 passes.

### CP2

P6-2E implementation
→ focused tests
→ regression
→ evidence
→ independent verification

P6-2F cannot begin until CP2 passes.

### CP3

P6-2F implementation
→ fresh Cline session
→ UI/E2E testing
→ full regression
→ mandatory independent verification

P6-2F must NOT be treated as self-certified.

---

# 14. FRESH SESSION REQUIREMENT

The contract must explicitly require:

> P6-2F implementation must begin in a fresh Cline session.

This is required to reduce implementation-session confirmation bias and ensure the final UI/security gate receives an independent implementation context.

---

# 15. SECURITY INVARIANTS

Create a consolidated security-invariant section in the contract.

At minimum preserve:

* authenticated access
* organisation isolation
* consultant-firm isolation
* active-grant enforcement
* canonical capability resolution
* PE authorization
* Ops authorization
* organisation-admin approval authority
* approval boundary
* CT-QC enforcement
* processing-origin immutability/integrity
* durable provenance
* entitlement ownership
* append-only audit behavior
* billing single-charge behavior
* no-charge-on-denial behavior
* billing idempotency
* RLS enforcement
* IDOR resistance
* actor injection resistance
* alternate-route resistance
* concurrency safety
* replay resistance
* event idempotency
* no UI-only authorization
* no unauthorized new role/capability/permission
```

*(prompt continues — see §1d)*

## 1d. Exact prompt text (continued and completed)

```text
---

# 16. SCOPE CONTROL

The contract MUST contain explicit:

### IN SCOPE

Everything required for D6, D7, D8, D11, P6-2D, P6-2E, P6-2F, E2E security acceptance, and their required tests/evidence.

### OUT OF SCOPE

At minimum:

* Phase 7 Auditor / Assurance
* Phase 8 Advanced Analytics
* PE↔Consultant handoff
* billing redesign
* unrelated refactoring
* unrelated schema changes
* unrelated UI redesign
* new roles
* new capabilities
* new permissions
* Consultant processing-origin value
* historical provenance backfill

---

# 17. IMPLEMENTATION BOUNDARY

For every proposed change, classify it as one of:

1. Existing behavior — preserve
2. Existing behavior — verify
3. Production code change required
4. Database migration required
5. RLS change required
6. Test-only change
7. E2E infrastructure/test fixture change
8. Documentation-only

Do not assume a code/schema change is required merely because the decision exists.

The contract must distinguish:

**"must exist"**

from:

**"must be changed."**

---

# 18. REQUIRED OUTPUT DOCUMENT

Create:

`docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md`

The document must be suitable for direct use as the authoritative implementation contract for the subsequent Cline implementation sessions.

It must include:

* document status
* version
* date
* authority
* relationship to Blueprint V1.3
* relationship to Master Roadmap V1.0
* CP0 status
* CP1 contract
* CP2 contract
* CP3 contract
* D6
* D7
* D7b closure
* D7c
* D8
* D11
* billing constraint
* D4 exclusion
* processing-model invariants
* security invariants
* E2E environment requirements
* checkpoint rules
* fresh-session requirement
* scope boundaries
* implementation classification rules
* required evidence
* independent verification requirements
* stop conditions

---

# 19. DURABLE CLINE HISTORY RECORD

Create:

`docs/cline/prompt-history/CT-PHASE6-REMAINDER-IC-20260910-001.md`

The history record MUST contain:

* exact Prompt Ref
* exact prompt text
* prompt datetime
* Response Ref
* response datetime
* complete Cline response
* files inspected
* files created
* files changed
* files explicitly unchanged
* commands executed
* tests executed, if any
* findings
* decisions
* risks
* scope assessment
* final verdict
* stop-condition confirmation

---

# 20. NO IMPLEMENTATION

This is critical.

STOP after the implementation contract and durable history record are created.

Do NOT:

* implement P6-2D
* modify production Python
* modify frontend
* modify database
* create migration
* modify RLS
* modify billing
* run implementation tests
* commit
* push

Only documentation necessary to define the contract is authorized.

---

# 21. FINAL RESPONSE FORMAT

Return a concise implementation-contract report containing:

1. Contract created
2. Contract path
3. History record path
4. Documents inspected
5. Decisions translated
6. Scope boundaries
7. Any unresolved ambiguity
8. Files changed
9. Files unchanged
10. Confirmation that NO implementation was performed
11. Confirmation that NO commit/push was performed
12. Final verdict

The expected final verdict is one of:

**IMPLEMENTATION CONTRACT COMPLETE — READY FOR PO REVIEW**

or

**IMPLEMENTATION CONTRACT BLOCKED — CLARIFICATION REQUIRED**

Do not proceed beyond this task.
```

**End of exact prompt text.**

---

## 2. Session context at prompt time

- Branch `main`, HEAD `1639121` (unchanged before and after).
- Working tree (porcelain entries): **663** at capture (18:32:53 +0600) — untracked documentation only.
- CP0 (PO ratification of the 11 remainder decisions) recorded earlier in the same working day in the PO Decision Register.
- No code, schema, migration, RLS, billing, frontend or test file was touched by this task.
- **Pre-existing working-tree state (NOT from this task):** the repository carries uncommitted tracked modifications and untracked files from earlier Phase-6 sessions (284 tracked `M` entries, e.g. `.agents/skills/**` and `backend/api/v3_processing_workflow.py`, whose mtime is **15:43 +0600**, ~2h49m *before* this task's 18:32 start). `docs/cline/prompt-history/` is entirely untracked and is therefore reported by git as a single collapsed `?? docs/cline/prompt-history/` entry — which is why the porcelain count moved only 663 → 664 despite two new files. A `find backend frontend supabase qa_harness tests -newermt '2026-09-10 18:30'` returned **empty**, confirming this task touched documentation only. These pre-existing modifications are recorded here so a later auditor does not attribute them to `CT-PHASE6-REMAINDER-IC-20260910-001`.

## 3. Documents inspected (for this task)

Authoritative sources named in prompt §2, plus targeted code/schema inspection to ground the D6/D7/D8/D11 contract statements:

1. `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` — ratified decision text (P6-2C, P6-2D, `## P6 Remainder Ratified PO Decisions — 2026-09-10`).
2. `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` — §9 processing-model dimensional clarification.
3. `docs/architecture/CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` — §4 scope of the origin concept.
4. `docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` — §13 note, state machine.
5. `docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md` — §6/§21/§22 annotated QC-flow text.
6. `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` — Phase-6 gates (read-only; unmodified).
7. `docs/cline/CARBONTALLY_PHASE6_REMAINDER_UNIFIED_READINESS_ANALYSIS.md`.
8. `docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_RECONCILIATION_REPORT.md`.
9. `docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_DOCUMENTATION_AMENDMENT_REPORT.md`.
10. `docs/cline/CARBONTALLY_P6_2D_RESIDUAL_ORIGIN_WORDING_CLARIFICATION_REPORT.md`.
11. `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md` (§19 next-step instruction).
12. `docs/cline/prompt-history/CT-PHASE6-PO-RAT-20260910-001.md`.
13. `docs/architecture/CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md`.

**Targeted code/schema inspection (read-only, no edits):**

- `backend/services/billing.py` — `ensure_processing_entitlement` (line 167) semantics.
- `backend/api/v3_processing_workflow.py` — submit route entitlement preflight (line 714); approval-time `charge_processing` charge site (line 920); consultant routes (`/batches/{id}/start|complete|cancel`, `/items/{id}/start|extract|map|validate|consultant-review|consultant-submit|calculate|customer-review`).
- `backend/data/manual_extraction.py` — item column list (assigned/qc/extracted/calculated/customer-review provenance).
- `backend/data/emissions_logs.py` — calculation provenance columns and snapshot chain.
- `backend/api/processing_mode.py` — `CT_QC_SATISFIED_STATUSES`, `item_is_automatic` predicate.
- `backend/api/v3_operations.py` — CT-QC decision route setting `ct_qc_approved` / `ct_qc_rejected`.
- `backend/data/notifications.py` + `backend/services/work_items.py` — `create_idempotent` `event_key` dedupe and existing emitter pattern.
- `backend/api/v3_messaging.py` + `backend/data/messaging.py` — consultant conversation participation and `conversation_kind`.
- `supabase/migrations/` — 52 files; naming `YYYYMMDDHHMMSS_<slug>.sql`; latest `20260906100000_p6_2a_consultant_processing_permissions.sql`.
- `qa_harness/scripts/` — `run_all.py`, `run_api.py`, `run_db.py`, `run_workflows.py`, `run_browser.py`, `preflight.py`; browser specs (`tests/example.spec.ts`); frontend test runner `react-scripts test`.

## 4. Files created by this task

| Path | Purpose | Class |
|---|---|---|
| `docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md` | Authoritative Phase-6 Remainder Implementation Contract (20 sections) | 8 Documentation-only |
| `docs/cline/prompt-history/CT-PHASE6-REMAINDER-IC-20260910-001.md` | This durable prompt/response history record | 8 Documentation-only |

## 5. Files changed by this task

**None.** No existing file was modified. (The two files above are new.)

## 6. Files explicitly unchanged

- `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (untouched).
- `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` (untouched — no new decisions to record).
- `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`, `…V1.2_DUAL_ORIGIN…`, `…P6_2_…ARCHITECTURE`, `…P6_2B_…ARCHITECTURE` (untouched).
- All `backend/**` production Python, `frontend/**`, `supabase/migrations/**`, RLS policies, billing code and existing test files (untouched).
- Investor-demo dataset and identity manifest (untouched).

## 7. Commands executed

```bash
# pre-edit state capture
git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD && git status --porcelain=v1 | wc -l
# read-only inspection
grep -rn 'ensure_processing_entitlement' --include=*.py backend
grep -rn 'charge_processing(' --include=*.py backend/api
grep -n 'extracted_by\|qc_by\|customer_reviewed_by\|performed_by' backend/data/manual_extraction.py
grep -n 'performed_by\|calculated_by\|source_item_id\|factor_kind' backend/data/emissions_logs.py
grep -rn 'notification_type=\|event_key=' --include=*.py backend/api backend/services
grep -n '@router.post' backend/api/v3_processing_workflow.py
grep -rn 'ct_qc_rejected\|ct_qc_approved' --include=*.py backend/api
ls supabase/migrations | wc -l && ls supabase/migrations | tail -3
ls qa_harness/scripts && ls tests/ && grep -n '"test"' frontend/package.json
```

## 8. Tests executed

**None.** This task is documentation-only and the prompt explicitly forbids running implementation tests. The unit-suite baseline (**1,606 tests, EXIT 0**) is carried forward as a *contract requirement* to be re-measured by the CP1 implementation session, not re-run here.

---

## 9. Complete Cline response (final report)

**PHASE 6 REMAINDER IMPLEMENTATION CONTRACT — FINAL REPORT**

1. **Contract created** — YES.
2. **Contract path** — `docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md` (Document ID `CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001`, V1.0, 10 Sep 2026).
3. **History record path** — `docs/cline/prompt-history/CT-PHASE6-REMAINDER-IC-20260910-001.md` (this record).
4. **Documents inspected** — the 13 authoritative/record documents of prompt §2 plus the read-only code/schema/harness inspection listed in §3 above.
5. **Decisions translated** — all 11 ratified decisions: D6=A (entitlement ownership/timing), D7=A (durable server-derived firm + mode provenance), D7b=withdrawn (no Consultant origin), D7c=A (no historical backfill), D8=B (reuse conversation model), D11=A (five lifecycle events, deterministic idempotent keys, server-side recipients), BILL-DEFER=A (automatic job-review billing deferred), D4=A (PE↔Consultant handoff out of scope), F-ACC=A (full acceptance + mandatory independent verification), F-ENV=A (isolated synthetic E2E environment), CAMPAIGN=A (single campaign, hard checkpoints, fresh session for P6-2F).
6. **Scope boundaries** — IN: D6/D7/D7b/D7c/D8/D11 + P6-2D, P6-2E, P6-2F, E2E security acceptance and their tests/evidence. OUT: Phase 7, Phase 8, PE↔Consultant handoff, billing redesign, unrelated refactor/schema/UI, new roles/capabilities/permissions, Consultant origin value, historical provenance backfill, investor-demo mutation, frozen D17/D19/D21/N1/N3 changes.
7. **Unresolved ambiguity** — none blocking. Two items are deliberately left to the implementation session, as the ratifications intend: (a) the D7 provenance *representation* (exact additive nullable column(s)/naming) after code+schema inspection, with constraints fixed by §6.2; (b) the D11 event *key strings* and recipient matrix, derived from the existing code in §7.2. Neither requires a new PO decision.
8. **Files changed** — none.
9. **Files unchanged** — all pre-existing files (roadmap, register, blueprint, architecture docs, backend, frontend, migrations, RLS, billing, tests, demo data).
10. **No implementation performed** — CONFIRMED: no production Python, frontend, database, migration, RLS or billing change; no implementation tests run.
11. **No commit/push performed** — CONFIRMED: branch `main`, HEAD `1639121` unchanged; working tree gains untracked documentation only.
12. **Final verdict** — **IMPLEMENTATION CONTRACT COMPLETE — READY FOR PO REVIEW**.

## 10. Findings

1. D6 is **already implemented** exactly as ratified (non-charging `ensure_processing_entitlement` preflight at consultant submit; single approval-time charge site with `charge:item:{item_id}` idempotency). CP1 must *preserve + verify*, not redesign — preventing an unnecessary billing-touching change.
2. D7's genuine gap is narrow and precise: consultant **firm** is recorded nowhere, and processing **mode** exists only as a derived predicate (`item_is_automatic`), not as stored provenance. Everything else in the provenance chain already exists (item actor stamps, machine provenance, calculation snapshot chain, append-only audit, assignment ledger).
3. D8 needs **no** change: consultant conversation participation already flows through the existing org-scoped conversation family via the active grant; `conversation_kind` has no consultant value.
4. D11 needs **code but no migration**: the existing `create_idempotent`/`event_key` infrastructure already provides deterministic dedupe, so the work is event constants, emit sites and server-derived recipients.
5. Five distinct workflow routes already exist for the five ratified lifecycle moments (`consultant-submit`, CT-QC decision, `customer-review`, rework transition, engagement acceptance) — so D11 introduces no new workflow and no new state.
6. RLS is **not** required to change: `manual_extraction_items` already carries the correct posture, and a single additive nullable provenance column inherits it. This is recorded as a STOP condition if that ever stops being true.

## 11. Decisions made in this task

1. Contract versioning: **V1.0**, dated 10 Sep 2026, status *authoritative / ready for PO review*, at the prompt-mandated path under `docs/architecture/`.
2. Explicit **"must exist" vs "must be changed"** table (§17) so no implementation session infers a code change from the mere existence of a decision.
3. D7 changes classified **3 (code) + 4 (additive nullable migration)**, with **RLS explicitly classified "not required"** rather than permitted.
4. D6, D8, billing and the P6-2C / frozen-UX invariants classified **1 Preserve + 2 Verify**.
5. D11 key strings and the recipient matrix recorded as **implementation-session derivation**, not invented here.
6. Stop conditions enumerated (10) covering PO-policy gaps, RLS, extra migrations, origin changes, new roles/capabilities, billing semantics, frozen-invariant conflicts, evidence gaps and demo-data safety.

## 12. Risks and mitigations

| Risk | Mitigation recorded in the contract |
|---|---|
| Implementation session "redesigns" D6/billing while chasing D7 | §6.1 + §8 fix D6/billing as preserve+verify; billing changes require a STOP |
| Provenance column added NOT NULL or backfilled | §6.2/§6.4 migration rules: additive, nullable, no `UPDATE`, no fabricating `DEFAULT` |
| Origin vocabulary quietly extended to Consultant | §4 hard prohibitions + §6.3 regression assertion of the two-value vocabulary |
| D11 recipients taken from the request body | §7.2 server-side recipient derivation + §15 actor-injection resistance |
| Event replay creating duplicate notifications | §7.2 deterministic keys + `create_idempotent` dedupe + replay tests |
| E2E run mutating the investor demo | §12 isolation rules + §19 stop condition 10 |
| P6-2F self-certified | §13 CP3 + §14 fresh-session requirement + §18 independent verification |
| Scope creep into Phase 7/8 or PE↔Consultant handoff | §9 + §16.2 explicit exclusions |

## 13. Scope assessment

The task stayed strictly inside its authorised boundary: **documentation only**. Two files created, no file modified, no code/schema/RLS/billing/frontend/test change, no migration, no commit, no push, no implementation work, no demo-data interaction. The contract is complete against prompt §18's required-content list (every listed element is present across §1–§20), and prompt §19's required history fields are all present in this record.

## 14. Stop-condition confirmation

**CONFIRMED — stopped at the task boundary.** The implementation contract and this durable history record are created; **nothing further was executed**. Specifically not done: P6-2D implementation, production Python change, frontend change, database change, migration creation, RLS change, billing change, implementation-test execution, commit, push.

**Next authorised action (separate prompt):** CP1 / P6-2D implementation against contract §6 (D6 verify + D7 code/migration + D7b/D7c constraints), ending with the §18 evidence set and independent verification. CP2 and CP3 remain blocked until their preceding checkpoint passes and is independently verified; CP3 must start in a fresh session.

**Final verdict:** **IMPLEMENTATION CONTRACT COMPLETE — READY FOR PO REVIEW**






