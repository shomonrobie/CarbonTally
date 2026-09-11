# CarbonTally Phase 6 Remainder — Unified P6-2D / P6-2E / P6-2F Readiness, Dependency & Consolidation Analysis

1. **Prompt Ref:** `CT-PHASE6-REMAINDER-RA-20260910-001`
2. **Date/time:** 10 September 2026, approx. 17:10–17:55 local (Asia/Dhaka +0600)
3. **Role:** CarbonTally architecture/readiness-analysis agent — **readiness and planning only**
4. **Repository:** `/home/shomonrobie/carbon_tally`, branch `main`,
   HEAD `16391217103b98dcea520070c5a22c68f12fe607` (`1639121`).

---

## 1. Executive verdict

### SAFE ONLY WITH HARD INTERNAL CHECKPOINTS

A single **PO-authorised implementation campaign** for the Phase 6 remainder is
technically feasible, because the remaining work is **bounded, additive and
partly already implemented**. It is **not** safe as one uninterrupted
implementation stream, for four evidence-based reasons:

1. **A PO decision gate is a hard precondition.** The P6-2 register's
   `D6 / D7 / D8 / D11` rows are **register recommendations only**, not ratified
   decisions (`CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`: *"No decision is
   presumed ratified by this table"*; only `PO-P6-2C-D1/D2/D3-20260910` are
   ratified). Implementing D7/D8/D11 without ratification would invent product
   policy (AGENTS.md §62; register "Final Recommendation").
2. **Workload/context risk.** The remainder spans ~15–23 source files, 1–2
   additive migrations, 3–6 new test suites, a frontend surface and an E2E
   persona matrix — while the working tree already carries **657 uncommitted
   entries** (large pre-Phase-6 change set). One uninterrupted agent context
   risks context loss and scope drift.
3. **P6-2F is the FINAL Phase-6 acceptance gate** (roadmap §9/§13; readiness
   §27 P6-6). An acceptance gate must not be self-implemented-and-self-accepted
   in the same context as the features it accepts.
4. **Each internal gate must remain independently verifiable.** Project history
   (P6-2A → R1; P6-2B-3 → P6-2B-4; P6-2C verification) shows self-reported PASS
   has repeatedly required independent re-verification.

**Model:** one campaign, one authorisation, **four checkpoints** — a
Checkpoint 0 PO-ratification gate plus three implementation checkpoints, each
with STOP-IF-FAILED, focused tests, regression, an evidence record and
independent verification. **P6-2F must run in a fresh agent session** even
though authorised by the same campaign.

---

## 2. Current Phase 6 status

| Gate | Name (as documented) | State (evidence-based) |
|---|---|---|
| P6-0 | Decision ratification package | COMPLETE — `PHASE 6 POLICY RATIFIED — IMPLEMENTATION READY` |
| P6-1B | Consultant membership/team/workspace authorisation | IMPLEMENTED — **no independent verification artifact on disk** (roadmap §9) |
| P6-1C | Consultant engagement confirmation | IMPLEMENTED — **no independent verification artifact on disk** (roadmap §9) |
| P6-2A (+R1) | Consultant processing authorisation contract | COMPLETE — VERIFIED (`P6-2A RE-VERIFICATION PASSED`) |
| P6-2B-1 | Consultant Review | COMPLETE — VERIFIED |
| P6-2B-2 | Consultant Submission | COMPLETE — VERIFIED |
| P6-2B-3 | CarbonTally QC decision | Blocker found; CLOSED THROUGH P6-2B-4 |
| P6-2B-4 | Mandatory CT-QC prerequisite (manual) | IMPLEMENTED + VERIFIED (in-session; no on-disk verification artifact) |
| **P6-2C** | Approval-boundary hardening + workflow-stage authorisation | **CLOSED — `P6-2C VERIFIED — PASS WITH NON-BLOCKING FINDINGS`** (`CT-P6-2C-IV-20260910-001`) |
| P6-2D | Entitlement availability at submit (D6) + consultant firm/origin provenance (D7) | **NEXT** — see §3 |
| P6-2E | D39 conversation kind (D8) + D40 notification vocabulary (D11) | REMAINING — see §4 |
| P6-2F | `/consultant` processing UI (D19/D21) + E2E security acceptance | REMAINING — **FINAL PHASE 6 GATE** — see §5 |

**P6-2C is not reopened.** No material dependency conflict between P6-2C and the
remainder was found; P6-2C's only forward obligation is that its invariants stay
frozen (§11) and are re-proven by P6-2F.

---

## 3. P6-2D analysis

1. **Official name:** "Entitlement & provenance finalisation (D6/D7)"
   (`P6_2_…ARCHITECTURE.md` §13); "Entitlement availability at submit (D6) +
   consultant firm/origin provenance (D7)" (roadmap §9).
2. **Authoritative definition:** D6 = processing-entitlement **timing** (client
   organisation owns entitlement; approval-time check canonical; optional
   **non-charging** availability check at consultant submission). D7 =
   **consultant firm provenance** — how "which consultant firm acted" is
   recorded (register `P6-2-D6`, `P6-2-D7`). The roadmap also places
   "origin-specific queue labelling (D7)" in the same deferral row.
3. **Requirements and status:**

| # | Requirement | Evidence inspected | Status |
|---|---|---|---|
| D6-1 | Client organisation (never the firm) owns entitlement | P6-0 D-7 (ratified); `services/billing.py` charge path | COMPLETE |
| D6-2 | Approval-time check canonical, single charge site | `v3_processing_workflow.py` l.920 (`charge:item:{id}`) | COMPLETE |
| D6-3 | Non-charging availability check at consultant submission, fail-closed | `services/billing.py::ensure_processing_entitlement` (D6-labelled, read-only, 403 `EntitlementUnavailableError`), called in the consultant submit route **before mutation** | **IMPLEMENTED / NOT INDEPENDENTLY VERIFIED as a standalone D6 gate** (exercised inside the verified P6-2B-2 suite) |
| D6-4 | Availability surfaced to the consultant/client workspace | `v3_consultants.py` `entitlement_scope` (l.246–250); `v3_commercial` `/entitlement/{org}` | PARTIAL (backend only; UI requirement unsettled) |
| D7-1 | Acting consultant **firm** recorded in provenance at action time | `grep -i firm` across `v3_processing_workflow.py`, `data/manual_extraction.py`, `engines/calculation.py`, `api/audit_helpers.py`, `services/billing.py` → **comments only**; no firm on item/snapshot/audit payloads | **NOT STARTED** |
| D7-2 | Consultant processing-origin value | `domain/processing_origin.py` defines only `CARBONTALLY_INTERNAL`, `PROCESSING_ENTITY` | **NOT STARTED** |
| D7-3 | Origin-specific queue labelling for consultant origin | `v3_operations.py` uses origin only for the PE guard/labels | **NOT STARTED** |
| D7-4 | Distinctions preserved (actor identity vs firm vs client org vs origin vs machine/human) | register D7 list | NOT STARTED (by design until D7-1 is ratified) |

4. **Existing implementation:** D6 complete; D7 none.
5. **Existing verification:** D6 only inside P6-2B-2's verification; D7 none.
6. **Remaining implementation:** D7-1..D7-3 (additive field + writes at action
   time + origin value + labels); D6 needs ratification and D6-named regression
   coverage (no code change expected).
7. **Remaining tests:** new focused `test_p6_2d_*` suite — firm attribution on
   consultant actions; origin write-once/immutability parity (internal vs PE vs
   consultant); queue/gate parity; D6 negatives (no entitlement ⇒ 403, zero
   mutation, zero charge); plus regression on P6-2A/2B/2C suites.
8. **Security requirements:** firm/origin must be **server-derived** (never from
   the request body); the existing PE-origin guard must not be weakened; no RLS
   change; additive column inherits the existing policy posture.
9. **Relevant D-items:** D6, D7 (blocking); D5 (origin vocabulary continuity);
   D9 (approval boundary — frozen).
10. **Relevant API routes:** `POST /api/v3/processing/items/{id}/consultant-review`;
    `POST …/consultant-submit` (D6 call site); `…/start|extract|map|validate|calculate`
    (firm-at-action-time writes); `GET /api/v3/consultants/clients/{id}/processing/items`;
    ops queue routes (`/api/v3/ops/*`).
11. **Backend files:** `domain/processing_origin.py`, `data/manual_extraction.py`,
    `api/v3_processing_workflow.py`, `api/audit_helpers.py`,
    `api/v3_consultants.py`, `api/v3_operations.py` (labels),
    possibly `data/consultants.py` (firm lookup).
12. **DB/schema/RLS dependencies:** one **additive** column (e.g.
    `consultant_firm_id`) and a new migration (`supabase/migrations/` currently
    holds 52 entries). RLS posture unchanged.
13. **Frontend dependencies:** display of firm/origin in the consultant item
    workspace and ops queues (delivered in P6-2F).
14. **Billing dependencies:** none beyond the existing D6 check; charge
    semantics frozen (PO-P6-2C-D3).
15. **Provenance/audit implications:** additive audit/provenance dimension;
    append-only audit and write-once machine provenance preserved; no backfill.
16. **Dependency on P6-2C:** invariant continuity only; no code dependency.
17. **Dependency on P6-2E:** none — **P6-2E depends on P6-2D**, not the reverse.
18. **Dependency on P6-2F:** P6-2F depends on P6-2D (labels/provenance display).
19. **PO decisions already ratified:** P6-0 D-7 (client org owns credits);
    `PO-P6-2C-D1/D2/D3` (approval boundary; billing frozen/deferred).
20. **New PO decisions required:** **PO-D6** ratification and **PO-D7**
    ratification + representation choice (§9). Neither is ratified today.

### P6-2D summary

P6-2D is **smaller than its name suggests**: half of it (D6) already exists and
is exercised by a verified suite; the substantive remaining work is **D7**
(additive firm provenance + consultant origin value + origin labels), which is
**blocked on PO ratification of D7** and needs one additive migration.

---

## 4. P6-2E analysis

1. **Official name:** "D39/D40 consultant vocabulary (D8/D11)"
   (`P6_2_…ARCHITECTURE.md` §13); "D39 conversation kind (D8) + D40 notification
   vocabulary (D11)" (roadmap §9).
2. **Authoritative definition:** D8 = decide whether consultants get a distinct
   conversation kind or reuse org conversations with active-grant participant
   derivation; D11 = enumerate the consultant processing notification events and
   their recipients (register `P6-2-D8`, `P6-2-D11`; readiness §26 step 5).
3. **Requirements and status:**

| # | Requirement | Evidence inspected | Status |
|---|---|---|---|
| D8-1 | Consultant participation in org conversations via an active grant | `api/v3_messaging.py` — consultants admitted with participant role `consultant` (`ensure_consultant_org_access`); consultants may create threads; UI `ClientMessagingTab.jsx` | **COMPLETE** (the register's recommended "reuse" model is already the implemented model) |
| D8-2 | Distinct consultant conversation kind (only if ratified) | `data/messaging.py` `conversation_kind`; only observed value in use is `entity` (PE messaging, PE-MSG-001); no consultant kind | **NOT STARTED** — **PO-D8 must first decide whether it is required at all** |
| D8-3 | Participant derivation follows the active-grant rule | `v3_messaging.py` l.56–88 | COMPLETE |
| D8-4 | Messaging boundaries (no Customer↔PE; PE via Ops) | `v3_messaging.py` entity-kind guard; N1 principles | COMPLETE (preserve; regression only) |
| D11-1 | Idempotent notification infrastructure | `data/notifications.py::create_idempotent` (l.116); `services/work_items.py` l.51–61 | COMPLETE (infrastructure) |
| D11-2 | Consultant lifecycle events: engagement accepted; submitted to CT-QC; QC outcome; customer decision; rework required | `grep 'notification_type=\|event_key='` finds only `work_item.assigned` and `general` | **NOT STARTED** |
| D11-3 | Recipient derivation (firm members / client owner-admin / Ops QC assignee) | none exists for consultant events | **NOT STARTED** |
| D11-4 | UI surfacing | `NotificationsPage.jsx`, `pe/PeNotificationsBell.jsx` exist | PARTIAL (generic surface; no consultant events) |

4. **Existing implementation:** D8 reuse model, messaging boundaries and the
   notification infrastructure; no consultant kind and no consultant events.
5. **Existing verification:** PE/ops/customer messaging paths are covered; no
   consultant-event verification exists.
6. **Remaining implementation:** D11 constants + emit sites at the consultant
   lifecycle points + recipient derivation; D8 only if a distinct kind is
   ratified (otherwise no code).
7. **Remaining tests:** per-event idempotency/dedupe; recipient scoping (firm
   member vs client owner/admin vs Ops); no cross-org/cross-firm leakage; **no
   notification emitted on any denial**; regression on messaging/notification
   suites.
8. **Security implications:** no cross-org/cross-firm leakage; server-side
   recipient derivation; denied actions must not emit success notifications; a
   new kind (if ratified) must not widen the frozen N1 boundaries.
9. **Relevant D-items:** D8, D11 (blocking); D5 (origin/firm context in
   payloads); D9 (frozen).
10. **API/backend dependencies:** `api/v3_processing_workflow.py`
    (consultant-review / consultant-submit), `api/v3_qc.py` /
    `api/v3_operations.py` (QC outcome), `api/v3_consultants.py` (engagement
    acceptance), `data/notifications.py`, `services/work_items.py` (pattern),
    `data/messaging.py` + `api/v3_messaging.py` (only if D8 adds a kind),
    `api/audit_helpers.py`.
11. **Frontend dependencies:** consultant/client notification surfacing in
    P6-2F; kind filter only if ratified.
12. **Notification dependencies:** reuse the idempotent `event_key` model and the
    existing recipient/authorisation pattern; do not duplicate.
13. **Audit/provenance implications:** notifications are derived events; the
    underlying workflow mutation keeps writing its own audit record; D11 must not
    create false success notifications on denied paths.
14. **Dependency on P6-2D:** **YES — 2E depends on 2D.** Notification payloads
    and recipient context name firm/origin, so implementing D11 before D7's
    representation is ratified would force rework. Order: 2D → 2E.
15. **Dependency on P6-2F:** P6-2F consumes the events for UI surfacing.
16. **PO decisions already ratified:** none of D8/D11 is ratified.
17. **New PO decisions required:** **PO-D8** (kind or no kind; exact string if
    any) and **PO-D11** (exact event keys + recipients). Both block
    implementation.

### P6-2E summary

P6-2E is **half-satisfied and half-unbuilt**: the consultant messaging model
(D8's recommended reuse option) already exists, while **D11 notification
vocabulary is entirely absent**. The bulk of the work is D11, which depends on
D7 being settled first.

---

## 5. P6-2F analysis

1. **Official name:** "`/consultant` processing UI (D19/D21) + E2E security
   acceptance" (roadmap §9; `P6_2_…ARCHITECTURE.md` §13). **FINAL PHASE 6 GATE**
   — readiness §27 P6-6: *"Stop: acceptance report; no Phase 6 work continues
   beyond defined scope."*
2. **Authoritative definition:** the consultant processing UI conforming to the
   frozen D19 workbench and D21 design system, followed by the Phase-6 E2E
   security acceptance matrix (readiness §28; P6-2 §14; P6-2B §23).
3. **UI/UX and E2E requirements and status:**

| # | Requirement | Evidence inspected | Status |
|---|---|---|---|
| F-1 | Routed consultant processing workspace (focused page, not inline) | `frontend/src/v3/consultant/ConsultantItemPage.jsx` — route `/consultant/items/:clientId/:itemId`, reuses shared `ExtractionPanel` (extract → map → validate → calculate → evidence) | PARTIAL (exists; D19 conformance unverified) |
| F-2 | Consultant review + submit-to-CT-QC controls | **Absent** — no `consultant-review` / `consultant-submit` / `consultant_reviewed` reference in `frontend/src` | **NOT STARTED** |
| F-3 | Consultant queue/list with business context (client, status, origin) | `ConsultantPage.jsx` (1,092 lines): dashboard / workspace / clients / branding / whitelabel / team / messaging tabs | PARTIAL (no firm/origin context — depends on D7) |
| F-4 | Firm/origin provenance display | depends on D7 | **NOT STARTED** |
| F-5 | Notification surfacing for consultant events | `NotificationsPage.jsx` exists; events do not (D11) | PARTIAL |
| F-6 | Client messaging tab | `ClientMessagingTab.jsx` (182 lines) | COMPLETE |
| F-7 | Team / new-customer / white-label tabs | `ConsultantTeamTab.jsx`, `NewCustomerView.jsx`, `WhiteLabelTab.jsx` | COMPLETE |
| F-8 | D21 design-system conformance | `consultant.css` + shared `components/ui` | IMPLEMENTED / NOT INDEPENDENTLY VERIFIED |
| F-9 | Frontend unit coverage of the consultant surface | `frontend/src/v3/__tests__/consultant-page.test.jsx` | PARTIAL (single page) |
| F-10 | E2E persona matrix (customer / consultant / PE / ops / internal) | `playwright.config.ts` (`testDir: './tests'`); `tests/` contains **only `example.spec.ts`** | **NOT STARTED** |
| F-11 | E2E negative security flows (IDOR, actor injection, alternate-route bypass, cross-org/cross-firm, approval boundary) | `qa_harness/browser/*` infrastructure exists (playwright controller, `workflows/driver.py`, `routes/navigator.py`, `auth/session.py`, `tables/auditor.py`, `responsive/auditor.py`, `accessibility/axe.py`, `sweep.py`); no Phase-6 suite | **NOT STARTED (infrastructure READY)** |
| F-12 | Responsive + accessibility acceptance (AGENTS.md §49/§50) | `qa_harness/browser/responsive`, `…/accessibility` modules exist | PARTIAL (infrastructure ready, no evidence) |
| F-13 | Acceptance report + evidence (meaningful screenshots, Git SHA, viewport, console/network) | no P6-2F artifact exists | **NOT STARTED** |

4. **Customer workflows to accept:** upload → pipeline → customer review →
   **customer approval** (owner/admin only, single charge, provenance intact).
5. **Consultant workflows:** onboard client → engage → upload → process
   (extract/map/validate/calculate) → consultant review → **submit to CT-QC** →
   rework loop; the consultant must never reach CT-QC decision or customer
   approval.
6. **PE workflows:** PE Review/PE QC → CarbonTally QC → customer review, with the
   PE-origin guard intact and PE denied on the customer-approval route.
7. **Operations workflows:** ops queues, ops stage claims (`can_review`),
   internal CT-QC decision, origin/label visibility.
8. **Organisation/role boundaries:** owner/admin vs member vs viewer vs
   consultant vs firm member vs PE user vs internal staff vs System Admin.
9. **Billing behaviour to verify:** single charge site at customer approval; no
   charge on denial; idempotent duplicate approval; consultant submission
   non-charging (D6); the **deferred** automatic job-review charging policy stays
   unchanged (PO-P6-2C-D3).
10. **Provenance/audit behaviour to verify:** human actor, write-once machine
    provenance, human-after-automation attribution, immutable `processing_origin`,
    snapshots with `performed_by`/`source_item_id`, firm dimension (post-D7),
    append-only audit, denied actions producing no success records.
11. **Cross-organisation isolation:** org A actor ⇒ org B resource denied; firm A
    consultant ⇒ firm B client denied; PE A ⇒ PE B denied.
12. **Negative security flows:** the AGENTS.md §45 matrix plus the P6-2C matrix
    (consultant/PE/ops/member/viewer/anonymous/cross-org ⇒ approval DENIED;
    capability-gated stage claims; `reviewed → customer_review` 409; actor
    injection; alternate routes).
13. **Relevant D-items:** D19 (frozen workbench), D21 (frozen design system),
    D9 (frozen approval boundary), plus whatever D8/D11 ratifies.
14. **Existing implementation:** consultant workspace + tabs + jest test;
    backend consultant action/submit routes already exist.
15. **Existing verification:** P6-2A/2B/2C verified; **no P6-1B/1C verification
    artifacts on disk**; no UI/E2E acceptance of the consultant surface.
16. **Remaining implementation:** F-2 (review/submit UI), F-3/F-4 (origin/firm
    context + labels), F-5 (notification surfacing — depends on D11), plus any
    D19/D21 gaps discovered.
17. **Remaining E2E tests:** F-10..F-12 plus the acceptance report (F-13).
18. **Dependency on P6-2D:** YES (firm/origin display + queue labels).
19. **Dependency on P6-2E:** YES (notification surfacing) — unless the PO
    explicitly defers/scopes out D11.
20. **Final Phase-6 acceptance requirements:** the acceptance report must cover
    the readiness §28 test strategy, the P6-2 §14 verification plan and the
    P6-2B §23 regression requirements, honouring the P6-2F stop condition (*"no
    Phase 6 work continues beyond defined scope"*).
21. **PO decisions already ratified:** D19/D21; the P6-2C invariants; billing
    frozen (D3).
22. **New PO decisions required:** the acceptance standard (personas, artifacts,
    whether the QA-harness run is mandatory), the E2E environment/demo-safety
    rule, and whether P6-2F requires an independent verification agent (§9).

### P6-2F summary

The consultant UI is **further along than "NOT STARTED"** — a routed processing
workspace and six components already exist — but the gate is **not closeable
today**: the review/submit UI is absent, firm/origin context awaits D7,
notifications await D11, and **there is no E2E acceptance suite at all** (only a
Playwright scaffold `tests/example.spec.ts`), despite mature harness
infrastructure. P6-2F is the largest and highest-risk remaining item and the one
that most clearly requires its own session and independent acceptance.

---

## 6. Consolidation feasibility

**Can P6-2D + P6-2E + P6-2F be implemented as one controlled campaign? — YES, but
only as one campaign with four hard checkpoints, and with each gate separately
verifiable.**

### A. Recommended consolidation model

```text
ONE AUTHORISED PHASE-6-REMAINDER CAMPAIGN
  |
  CHECKPOINT 0 — PO ratification gate (NO CODE)
  |   ratify D6 / D7 / D8 / D11; assign or close the deferred
  |   automatic-job-review charging question; confirm D4 scoped out;
  |   approve the unified contract
  |   STOP IF NOT RATIFIED (implementation cannot start)
  |
  CHECKPOINT 1 — P6-2D implementation (own session)
  |   D7 firm provenance + consultant origin + labels (+ D6 ratification coverage)
  |   → focused tests → targeted regression → evidence record
  |   STOP IF FAILED → independent verification → close P6-2D
  |
  CHECKPOINT 2 — P6-2E implementation (own session)
  |   D11 events + recipients (+ D8 only if ratified, else explicit no-op)
  |   → focused tests → targeted regression → evidence record
  |   STOP IF FAILED → independent verification → close P6-2E
  |
  CHECKPOINT 3 — P6-2F implementation + acceptance (FRESH session)
      review/submit UI + firm/origin display + notification surfacing
      → frontend tests → E2E persona/negative matrix → full Phase 6 regression
      → acceptance report + evidence
      → STOP  → MANDATORY independent verification (final gate)
```

This is the model the evidence supports: it preserves the PO-ratified
`P6-2C → P6-2D → P6-2E → P6-2F` order (roadmap §9 "not to be reordered"), keeps
each gate's evidence separable, and stops the implementing agent from declaring
Phase 6 complete on its own tests (AGENTS.md §74; readiness §27 P6-6).

### B. What must remain separately gated (hard checkpoints even if implementation
is consolidated)

1. **Checkpoint 0 — PO ratification.** D6/D7/D8/D11 are not ratified. No
   implementation may create policy (AGENTS.md §62).
2. **Migration checkpoint (P6-2D, and P6-2E if a kind is added).** Schema changes
   must be applied, inspected and verified as their own step, separately from API
   and frontend work, with before/after evidence — never bundled into a UI
   checkpoint.
3. **Billing/entitlement checkpoint.** Billing is frozen (PO-P6-2C-D3). Any
   billing-touching action requires an explicit PO decision first.
4. **P6-2F acceptance checkpoint — independent.** The final gate's verdict must
   come from an independent verification pass, not the implementer.
5. **Full-suite regression checkpoint after each gate** (`pytest tests/unit`,
   currently **1,606 tests, EXIT 0** as verified at P6-2C) plus the affected
   suites, with the baseline re-measured rather than assumed.
6. **Git/state checkpoint.** The working tree currently has **657 uncommitted
   entries**; each gate must record branch/HEAD/status and must not absorb
   unrelated changes.

### C. What must NOT be combined

1. **DDL/migration with UI/E2E work** in one checkpoint — a schema failure must
   be isolatable from a UI failure.
2. **Anything touching billing charge semantics** with D7/D8/D11 work. The
   deferred automatic-job-review charging policy (PO-P6-2C-D3) must **not** be
   resolved as a side effect of P6-2D/2E/2F implementation.
3. **P6-2F UI/acceptance with the implementation of the features it accepts**
   inside one agent context (context loss + self-acceptance risk).
4. **The automatic-processing path** (`v3_automatic_processing.py`, worker,
   `services/automatic_processing.py`) with any of the above; it is frozen except
   where a ratified decision requires otherwise.
5. **D4 (PE ↔ Consultant handoff)** with the remainder: it is register-flagged as
   possibly scoped out and must not be pulled in implicitly.
6. **Demo/investor data mutation** with E2E acceptance (AGENTS.md §54/§55);
   isolated, clearly-labelled QA records only.

---

## 7. Required internal checkpoints

| # | Checkpoint | Exit criteria | On failure |
|---|---|---|---|
| 0 | PO ratification (D6/D7/D8/D11; deferred charging question; D4 scope; contract approval) | written ratified decisions in the PO register + an authorised contract | **STOP** — no implementation |
| 1 | P6-2D implementation | D7 requirements implemented; D6 coverage named; focused suite green; targeted regression green; evidence record; no drift | STOP; report; do not proceed |
| 1v | P6-2D independent verification | independent artifact with a verdict | STOP if FAIL |
| 2 | P6-2E implementation | D11 events/recipients (D8 only if ratified); focused suite green; regression green; evidence record | STOP; report; do not proceed |
| 2v | P6-2E independent verification | independent artifact with a verdict | STOP if FAIL |
| 3 | P6-2F implementation + acceptance (fresh session) | review/submit UI + provenance/labels + notification surfacing; frontend tests; E2E persona + negative matrix; full Phase 6 regression; acceptance report + evidence | STOP; report; do not proceed |
| 3v | **P6-2F independent verification (mandatory)** | independent verdict on the final Phase-6 gate | STOP if FAIL — Phase 6 not closed |

---

## 8. Dependency graph

Actual dependencies **discovered from the repository and authoritative documents**
(not assumed from the roadmap order):

```text
P6-0 (ratified policy)
  └─ P6-1B / P6-1C (implemented; verification artifacts absent)
       └─ P6-2A(+R1) → P6-2B-1 → P6-2B-2 → P6-2B-3 → P6-2B-4  [all CLOSED/VERIFIED]
            └─ P6-2C  [CLOSED — VERIFIED]  ── invariants FROZEN ─────────────┐
                                                                            │
PO ratification gate (D6/D7/D8/D11)  ◄── HARD PRECONDITION                  │
        │                                                                   │
        ▼                                                                   │
P6-2D  D6 (already implemented)  +  D7 (firm provenance, CONSULTANT          │
        origin, origin labels, additive migration)                          │
        │                                                                   │
        ├──► P6-2E  D11 notification events/recipients  (payloads need       │
        │           firm/origin context ⇒ 2E depends on 2D)                 │
        │        D8 conversation kind (OPTIONAL: only if ratified — the      │
        │           reuse model already exists ⇒ may be a no-op)             │
        │                                                                   │
        └──────────────►  P6-2F  /consultant processing UI (D19/D21)        │
                          + E2E security acceptance  ◄───────────────────────┘
                          (consumes 2C + 2D + 2E; MUST run last)
```

**Sequential vs parallel:**

- **P6-2D → P6-2E must be sequential.** D11's payloads and recipients name the
  acting firm/origin; implementing events before D7's representation is ratified
  would force rework. The only safely parallel activity is *drafting* the D11
  event-key list (no code) alongside D7's design — and only after Checkpoint 0.
- **P6-2D and P6-2F are partly parallelisable in the sense that UI work for
  sections not depending on D7 could start early — but the campaign should not
  do this**, because it splits evidence and invites drift. Keep 2F last.
- **P6-2C is closed and upstream of all three** (invariant provider, no code
  dependency).
- The roadmap order `P6-2C → P6-2D → P6-2E → P6-2F` is **also technically
  necessary** on the evidence, so no PO sequencing change is required (or
  recommended) to enable consolidation.

---

## 9. Unified implementation contract proposal

**Is one unified contract appropriate? — YES, conditionally.**

A single contract named `CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001` is
appropriate **only if** it is written as a *gated* contract whose Checkpoint 0 is
the PO ratification of D6/D7/D8/D11 (plus the deferred-question assignment). It
must not be created as an unconditional authorisation, because implementing D7/D8
/D11 without ratification would invent product policy.

**Proposed contract structure (proposal only — NOT created, NOT authorised):**

| § | Section | Content |
|---|---|---|
| 1 | P6-2D scope | D6: ratify + name coverage (no code). D7: firm at action time (server-derived), `CONSULTANT` origin value, origin-specific queue labels; additive migration; no backfill |
| 2 | P6-2E scope | D11: fixed event-key vocabulary + recipients; reuse `create_idempotent`; no notification on denial. D8: only if ratified (else explicit no-op) |
| 3 | P6-2F scope | Consultant review/submit UI; firm/origin display; notification surfacing; E2E persona + negative matrix; acceptance report |
| 4 | Dependencies | This document §8 (2D→2E→2F) |
| 5 | Internal checkpoints | This document §7 (0, 1, 1v, 2, 2v, 3, 3v) |
| 6 | Security invariants | This document §11 |
| 7 | Workflow invariants | `ITEM_STATUS_FLOW` additions only by ratified decision; no new state without PO approval |
| 8 | Authorization invariants | resolver-only; `_STAGE_PERMISSION` as the single consultant gating site |
| 9 | Billing invariants | frozen (PO-P6-2C-D3); no new charge site; D6 check read-only |
| 10 | Provenance invariants | additive, write-once preserved, no backfill, append-only audit |
| 11 | Audit invariants | denied actions produce no success records |
| 12 | RLS invariants | no weakening; additive column inherits existing posture |
| 13 | Frontend/UI requirements | D19/D21 conformance; business-first labels; no UUIDs |
| 14 | E2E requirements | persona matrix + negative matrix + responsive/a11y evidence |
| 15 | Regression requirements | `pytest tests/unit` baseline (currently 1,606 EXIT 0) + messaging/notification/frontend suites |
| 16 | Rollback/stop conditions | STOP-IF-FAILED per checkpoint; additive-only migrations |
| 17 | Out of scope | D4 handoff; automatic job-review charging (unless assigned); billing redesign; RLS redesign; Phase 7/8; demo-data mutation |
| 18 | PO decision requirements | This document §10 |
| 19 | Acceptance criteria | P6-2F acceptance report + independent verification verdict |
| 20 | Independent verification requirements | Per gate (1v, 2v) and mandatory at 3v |

**Condition:** do not create the contract until Checkpoint 0 ratifications are
recorded; then create it once, as the single authorisation for the campaign.

---

## 10. PO decisions required

| Ref (proposed) | Exact question | Why it matters | Options | Recommended | Blocks? |
|---|---|---|---|---|---|
| `PO-P6-2D-D6-R-20260910` | Ratify the entitlement-timing policy: approval-time check canonical + non-charging availability check at consultant submission (already implemented as `ensure_processing_entitlement`)? | Determines whether existing D6 code is accepted as policy; today it is only a register recommendation | A ratify as-is · B move/remove the submit-time check · C charging check at start | **A** — matches the register's recommended option, the code and P6-0 D-7 ownership | YES (P6-2D closure) |
| `PO-P6-2D-D7-R-20260910` | Ratify **firm provenance**: additive `consultant_firm_id` recorded at action time (server-derived) on item/audit/snapshot? | The only substantive P6-2D implementation; adds a schema column | A additive field at action time · B derive at read time · C extend `processing_origin` vocabulary | **A** — no reinterpretation, audit-stable, survives firm changes | YES (P6-2D impl) |
| `PO-P6-2D-D7b-R-20260910` | Add the `CONSULTANT` `processing_origin` value + origin-specific queue labels in P6-2D (roadmap deferral row)? | Affects origin guard parity, queues, labels | A add origin + labels · B no new origin (reuse `CARBONTALLY_INTERNAL`) · C defer to Phase 7 | **A** — matches P6-2B §21 P3 and the roadmap row | YES (P6-2D scope) |
| `PO-P6-2D-D7c-R-20260910` | Backfill firm/origin onto **historical** items? | Data safety; audit immutability | A no backfill (new actions only) · B best-effort backfill | **A** — preserves write-once history (AGENTS.md §17) | No (defaults to A) |
| `PO-P6-2E-D8-20260910` | Consultant conversation kind: reuse org conversations with active-grant participants (already implemented) or add a distinct kind? | Decides whether P6-2E has any D8 code at all | A reuse (no new kind) · B add kind `<string>` | **A** — reuse already exists; no schema change | YES (P6-2E D8 scope) |
| `PO-P6-2E-D11-20260910` | Ratify the D40 event-key vocabulary and recipients for consultant processing events | Event constants are product policy; recipients define who is told what | A the register list (`engagement.request_accepted`, `consultant.submitted_to_qc`, `ct_qc.decision`, `customer.decision`, `consultant.rework_required`) with firm-member / client-admin / Ops recipients · B modify | **A** — matches register D11 and readiness §26 step 5 | YES (P6-2E impl) |
| `PO-PHASE6-DEFER-20260910` | Assign or close the **deferred automatic job-review charging** question (roadmap §18 finding 2; frozen by PO-P6-2C-D3) | Prevents an unowned policy gap being silently resolved | A leave deferred + explicitly out of scope · B assign to P6-2D · C new gate | **A** — keeps Phase 6 bounded | YES (contract completeness) |
| `PO-PHASE6-D4-20260910` | Confirm D4 (PE ↔ Consultant handoff) stays **scoped out** of Phase 6 | Register allows scoping out; pulling it in is new scope | A scoped out · B in scope | **A** — no authoritative requirement exists | YES (contract completeness) |
| `PO-P6-2F-ACC-20260910` | Phase-6 acceptance standard: personas, artifacts, and whether a QA-harness run is mandatory | Defines what "Phase 6 complete" means | A readiness §28 matrix + harness run + evidence + independent verification · B UI smoke only | **A** — AGENTS.md §51/§74; roadmap §9 | YES (P6-2F exit) |
| `PO-P6-2F-ENV-20260910` | E2E environment + demo-data safety rule (investor demo identities ≈ 1,185) | AGENTS.md §54/§55 forbid casual demo mutation | A local demo + isolated labelled QA records, cleaned and verified · B dedicated E2E dataset | **A** — preserves the ratified demo asset | YES (P6-2F exec) |
| `PO-PHASE6-CAMPAIGN-20260910` | Authorise the consolidated campaign and its contract `CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001` | Without it the remainder stays per-gate | A authorise with checkpoints (fresh session for 2F) · B four separate campaigns | **A** | YES (gates all implementation) |

**No decision above is made here** — recommendations are recommendations; the PO
remains the sole policy authority (AGENTS.md §2, §62).

**Numbering warning.** The code comment `PO-D7 (ratified, Phase 6)` in
`services/billing.py` refers to the **P6-0** decision *D-7 (billing/credit
ownership)*, **not** the P6-2 register's `D7` (firm provenance). The P6-2
register's `D1–D11` rows remain recommendations; implementation must not treat
one numbering system's ratification as the other's.

---

## 11. Code / file impact

### P6-2D

| Class | Files |
|---|---|
| MUST change | `backend/domain/processing_origin.py` (add `CONSULTANT` + label), `backend/data/manual_extraction.py` (write server-derived firm/origin at action time), `backend/api/v3_processing_workflow.py` (pass the acting firm into provenance/audit for consultant actions), `backend/api/audit_helpers.py`, `supabase/migrations/<new-additive>.sql`, **new** `backend/tests/unit/api/test_p6_2d_*.py` |
| MAY change | `backend/api/v3_consultants.py` (surface firm/origin), `backend/api/v3_operations.py` (queue labels), `backend/data/consultants.py` (firm lookup) |
| MUST NOT change | charge semantics in `backend/services/billing.py`; `backend/api/v3_automatic_processing.py` + worker; the P6-2C approval guard; existing RLS policies; existing tests; demo/seed data |
| Migrations | 1 additive (nullable column, no backfill, no destructive DDL) |
| RLS changes | none expected (additive column inherits the existing posture) |
| Frontend | none in this checkpoint (display deferred to P6-2F) |

### P6-2E

| Class | Files |
|---|---|
| MUST change | notification event constants, emit sites in `backend/api/v3_processing_workflow.py` (consultant-review/submit), `backend/api/v3_qc.py` / `backend/api/v3_operations.py` (QC outcome), `backend/api/v3_consultants.py` (engagement accepted), recipient derivation, **new** `backend/tests/unit/api/test_p6_2e_*.py` |
| MAY change | `backend/data/messaging.py` + `backend/api/v3_messaging.py` **only if** PO-D8 ratifies a kind (+1 additive migration); `frontend/src/v3/NotificationsPage.jsx` (surfacing may move to P6-2F) |
| MUST NOT change | the frozen N1 messaging boundaries; PE messaging routes; `create_idempotent` semantics; billing; RLS |
| Migrations | 0 if D8 = reuse (recommended); 1 additive if a kind is added |
| Frontend | minimal here; consultant-facing surfacing belongs to P6-2F |

### P6-2F

| Class | Files |
|---|---|
| MUST change | `frontend/src/v3/consultant/ConsultantItemPage.jsx` (review/submit surface, provenance/origin display), `frontend/src/v3/api.js` (consultant review/submit calls + new fields), `frontend/src/v3/consultant/ConsultantPage.jsx` (lists/labels), **new** E2E suite (Playwright spec(s) under `tests/` and/or `qa_harness/browser/workflows/*`), frontend tests, `docs/cline/CARBONTALLY_P6_2F_*ACCEPTANCE*.md` |
| MAY change | `frontend/src/v3/components/**` (shared primitives), `frontend/src/v3/ops/*` (label parity), `frontend/src/v3/consultant/consultant.css` |
| MUST NOT change | backend business logic (unless a defect is found — then a *separate* minimal fix + verification, never a silent drive-by), D19/D21 frozen structure, demo data, `supabase/**` |
| Migrations / RLS | none |
| E2E | new persona + negative matrix suites (none exist today) |

**Protecting the 657 pre-existing working-tree changes:** each checkpoint must
(a) record `git status`/HEAD before and after, (b) touch only the files declared
for that checkpoint, (c) never run repo-wide formatters or bulk writes, and
(d) report any file changed outside its declared set.

---

## 12. Security invariants (unified checklist for the remainder)

| # | Invariant | Applies to 2D/2E/2F | P6-2C frozen? |
|---|---|---|---|
| 1 | Authentication enforced before any logic (401 unauthenticated) | all | — |
| 2 | Organisation isolation (org A ⇒ org B denied) | all | — |
| 3 | Firm isolation (firm A ⇒ firm B client denied) | 2D, 2E, 2F | — |
| 4 | Consultant grant must be **active** (membership → engagement → resource) | all | — |
| 5 | Consultant capability gating via the canonical resolver only | 2D, 2F | **YES** (S2/S3) |
| 6 | PE authorisation confined to `/pe` surfaces; PE denied on customer approval | all | **YES** |
| 7 | Operations authorisation unchanged (`can_review`, ops queues) | all | — |
| 8 | Customer/org-admin authority for approval (`require_org_admin`) | all | **YES** (S1) |
| 9 | Approval boundary: `calculated → approved` is automatic-only | all | **YES** (S1) |
| 10 | CT-QC authority CarbonTally-only; manual work cannot bypass it | all | **YES** (P6-2B-4) |
| 11 | Processing origin immutable/write-once; PE-origin guard | 2D (extends), all | **YES** |
| 12 | Provenance: human actor + firm (post-D7), no reinterpretation, no backfill | 2D, 2F | — |
| 13 | Audit: append-only; **denials create no success records** | 2D, 2E, 2F | — |
| 14 | Billing: single charge site; denials never charge; idempotent | all | **YES** (D3) |
| 15 | RLS: no weakening; no authenticated write policy added casually | 2D, 2E | — |
| 16 | IDOR / cross-firm / cross-org rejection (403/404, zero mutation) | all | — |
| 17 | Actor/identity injection rejected (identity from session, never payload) | all | **YES** |
| 18 | Alternate-route bypass closed (ops/PE/job-review/QC routes) | all | **YES** |
| 19 | Concurrency: no duplicate charge/mutation on races | 2D, 2E, 2F | — |
| 20 | Replay/idempotency: notification `event_key` dedupe; charge key | 2E | — |
| 21 | No UI-only authorization assumption (server enforces everything) | 2F | — |
| 22 | No new capability/role/permission without an explicit PO decision | 2D, 2E | **YES** |

**P6-2C invariants that must remain frozen while implementing 2D/2E/2F**
(verified at `CT-P6-2C-IV-20260910-001`):

1. `calculated → approved` is automatic-processing-only (S1).
2. The consultant `review` stage claim requires the existing `can_submit` (S2).
3. The `source` stage claim requires the existing `can_extract` (S3).
4. `_STAGE_PERMISSION` remains the **single** consultant stage-gating site
   (no parallel authorization logic may be introduced).
5. The approval route stays `require_org_admin()` with the single charge site
   (`charge:item:{id}`) after all guards.
6. No new capability, role, permission or flag may be added without a PO
   decision (PO-P6-2C-D2's explicit non-decision).
7. The billing files remain unchanged (PO-P6-2C-D3).

---

## 13. Test / verification strategy (unified)

| Tier | Content | Runs after |
|---|---|---|
| A. Unit | domain/state-machine helpers, origin/provenance helpers, notification payload builders | CP1 (2D), CP2 (2E) |
| B. API authorisation | positive/negative per new route and per new field: active/inactive grant, cross-firm, cross-org, PE, ops, unauth, viewer/member/admin | CP1, CP2 |
| C. Workflow | consultant lifecycle end-to-end at API level (submit → CT-QC → customer review → approval + rework), with firm/origin assertions | CP1, CP2 |
| D. Billing regression | single charge site, no charge on denial, idempotent duplicate approval, non-charging D6 check, **automatic job-review behaviour unchanged** | CP1, CP2, CP3 |
| E. Provenance/audit regression | human actor, write-once machine provenance, human-after-automation, immutable origin, snapshots, **firm dimension (new)**, append-only audit, no false success records | CP1, CP2, CP3 |
| F. RLS/integration | additive-column visibility under the existing policies; no authenticated write policy added; before/after DB baseline counts | CP1 (+CP2 if a migration) |
| G. Frontend tests | consultant page/item/review-submit component tests (jest) | CP3 |
| H. E2E (browser) | persona matrix: customer / consultant / PE / ops / internal on the consultant processing workflow; responsive + a11y evidence via the QA harness | CP3 |
| I. Security-negative | AGENTS.md §45 matrix + P6-2C matrix re-run against the post-2D/2E system | CP3 (and targeted subsets at CP1/CP2) |
| J. Final Phase-6 acceptance | readiness §28 strategy + P6-2 §14 verification plan + P6-2B §23 regression; full `pytest tests/unit` baseline; acceptance report with evidence | CP3 + CP3v |

**Gate discipline:** A–F confirm each implementation checkpoint; G–J are only
meaningful once the features exist and therefore **must wait for P6-2F** (with
the exception of targeted security negatives at CP1/CP2). Nothing in this plan
requires modifying production code to run a test.

**Baseline discipline:** the current verified baseline is **1,606 unit tests,
EXIT 0** (P6-2C verification). Each checkpoint re-measures rather than assumes it;
new suites add to the count, and any *decrease* is a regression finding.

---

## 14. Implementation campaign design (recommended execution model)

```text
PHASE 6 REMAINDER — IMPLEMENTATION CAMPAIGN
  (authorised only after Checkpoint 0 ratification)

CHECKPOINT 1 — P6-2D                        [own session]
  D7 implementation (firm provenance + CONSULTANT origin + labels)
  → additive migration applied and verified
  → focused tests (test_p6_2d_*)
  → targeted regression (P6-2A/2B/2C + provenance/QC/origin suites)
  → internal evidence checkpoint
  → STOP IF FAILED → independent verification → P6-2D closed

CHECKPOINT 2 — P6-2E                        [own session]
  D11 notification events + recipients  (+ D8 only if ratified)
  → focused tests (test_p6_2e_*)
  → targeted regression (messaging/notification/workflow suites)
  → internal evidence checkpoint
  → STOP IF FAILED → independent verification → P6-2E closed

CHECKPOINT 3 — P6-2F                        [FRESH session]
  consultant review/submit UI + firm/origin display + notification surfacing
  → frontend tests
  → E2E persona matrix + security negatives + responsive/a11y
  → FULL Phase 6 regression (pytest tests/unit + frontend + E2E)
  → acceptance report + evidence
  → STOP → MANDATORY independent verification (final gate)

The implementing agent must NOT declare Phase 6 complete on its own tests.
```

This mirrors the requested model but is grounded in the discovered
dependencies: 2D → 2E → 2F, with the D8 branch potentially collapsing to a no-op
and the D6 branch requiring no code at all.

---

## 15. Cline workload assessment

| Dimension | Estimate (evidence-based) |
|---|---|
| Estimated files (implementation) | ~15–23 (2D ≈ 5–7; 2E ≈ 4–6; 2F ≈ 6–10) |
| Migrations | 1 additive (2D); +1 only if PO-D8 ratifies a kind |
| New tests | 3–6 suites (2D focused, 2E focused, frontend, E2E specs, plus acceptance evidence) |
| Documentation | 2D report, 2E report, 2F acceptance report, 3 verification reports, prompt-history records, PO decision records |
| Frontend complexity | Medium — a mature consultant surface exists; the missing review/submit panel and label work are additive |
| E2E complexity | **High** — a full persona + negative matrix does not exist; the harness exists but no Phase-6 suite, and the investor demo dataset must be handled safely |
| Context requirements | High for 2F (frontend + harness + evidence + demo identities); medium for 2D/2E |
| Security invariants to hold | 22 (§12), 7 of them P6-2C-frozen |
| Likelihood of context loss | High in a single uninterrupted stream (657 uncommitted entries already; large diffs) |
| Likelihood of scope drift | Medium-high (D4, billing/automatic-path, D8 "while we are here") |
| Durable-record burden | 4 reports + 4 prompt-history records + PO register entries |

**Recommendation: SAFE ONLY WITH HARD INTERNAL CHECKPOINTS.**

Rationale: 2D and 2E are individually small and additive, and could even share a
session; 2F is a different discipline (UI + browser E2E + evidence) with the
largest blast radius and the weakest existing verification. Bundling them without
checkpoints would (a) hide a migration or authorization failure behind UI work,
(b) let a single context loss invalidate the whole remainder, and (c) compromise
the independence of the final acceptance gate.

**Do not** attempt all three in one session. **Do** issue one authorised campaign
with four checkpoints and run Checkpoint 3 in a fresh session.

---

## 16. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Implementing D7/D8/D11 without PO ratification ⇒ invented policy | High if not gated | High (governance) | Checkpoint 0; do not create the contract until ratified |
| R2 | Firm/origin provenance altered in a way that breaks write-once history or the PE guard | Medium | High | Additive column only; guard-parity tests; no backfill (recommended) |
| R3 | Additive migration collides with RLS expectations or the 52 existing migrations | Low-medium | High | Migration as its own checkpoint; before/after DB baseline; no RLS change |
| R4 | D11 emits notifications on denied paths or leaks cross-org/cross-firm | Medium | High | Denial-path tests; recipient scoping tests; reuse `create_idempotent` |
| R5 | UI/E2E work silently changes backend behaviour ("drive-by fix") | Medium | High | MUST-NOT-CHANGE list; any backend defect ⇒ separate minimal fix + verification |
| R6 | P6-2F E2E mutates the investor demo dataset | Medium | High (AGENTS.md §54/§55) | PO-P6-2F-ENV; isolated labelled QA records; verified cleanup |
| R7 | P6-2F acceptance self-declared without independent verification | Medium | High | CP3v mandatory |
| R8 | Pre-existing 657-entry working tree causes accidental absorption/regression | Medium | Medium-high | Per-checkpoint `git status`; file-scoped edits; no repo-wide formatters |
| R9 | Scope creep from unowned items (D4 handoff, automatic job-review charging) | Medium | Medium-high | Explicit out-of-scope list in the contract; PO-PHASE6-DEFER/D4 decisions |
| R10 | D8 kind added "just in case", creating schema/vocabulary drift | Low-medium | Medium | PO-P6-2E-D8 decision; default is reuse (no code) |
| R11 | P6-1B/1C remain unverified yet underpin the UI that P6-2F accepts | Medium | Medium | P6-2F acceptance must exercise those surfaces; record the limitation |
| R12 | Test-count/baseline drift mistaken for progress | Low | Medium | Re-measure the baseline each checkpoint (currently 1,606 EXIT 0) |

---

## 17. Evidence limitations

1. **No runtime verification was performed in this task.** It is a read-only
   readiness analysis: no application was started, no test suite was re-run, no
   browser harness was executed. Statements about "implemented" are based on
   source inspection and existing reports, not on fresh runtime evidence.
2. **Frontend behaviour was assessed statically** (file inventory, route/tab
   structure, import analysis). Whether the consultant workspace is *fully*
   D19/D21 conformant and responsive was **not** verified in a browser.
3. **P6-1B / P6-1C remain unverified** (no verification artifacts on disk), which
   inherits into P6-2F's acceptance scope.
4. **D6 was not independently re-exercised in this task**; its "implemented"
   status rests on source inspection plus the P6-2B-2 verified suite.
5. **E2E feasibility is inferred** from the presence of `playwright.config.ts`,
   `tests/example.spec.ts` and `qa_harness/browser/*`; the harness was not run, so
   its readiness for a Phase-6 persona matrix is **UNVERIFIED**.
6. **No PO decision is asserted as ratified** except the P6-2C D1/D2/D3 entries
   and the P6-0 package; the D1–D11 register rows are quoted as recommendations.
7. **Effort estimates are engineering estimates**, not measured data.

---

## 18. Recommended next step

**Exact next action — a PO decision package, not an implementation prompt.**

1. Present §10 to the Product Owner and obtain written ratification/modification
   of `PO-P6-2D-D6-R`, `PO-P6-2D-D7-R`, `PO-P6-2D-D7b-R`, `PO-P6-2D-D7c-R`,
   `PO-P6-2E-D8`, `PO-P6-2E-D11`, `PO-PHASE6-DEFER`, `PO-PHASE6-D4`,
   `PO-P6-2F-ACC`, `PO-P6-2F-ENV` and `PO-PHASE6-CAMPAIGN`
   (record them in `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` alongside the
   ratified P6-2C entries).
2. **Only then** create the gated contract
   `CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001` per §9 (structure already
   proposed; not created here because Checkpoint 0 is unmet).
3. Issue **Checkpoint 1 (P6-2D)** as a bounded implementation prompt, then its
   independent verification, then Checkpoint 2 (P6-2E), then Checkpoint 3
   (P6-2F) in a fresh session, then the mandatory final independent verification.

If the PO prefers lower risk: keep P6-2D and P6-2E as one campaign and P6-2F as a
separate campaign. That is also safe and changes only the authorisation wrapper,
not the checkpoint structure.

---

## 19. Explicit no-implementation statement

**No implementation was performed.** This task changed **nothing** in:

- backend code · frontend code · tests · database · schema · migrations · RLS ·
  billing · configuration · seed/demo data · the Master Roadmap · the
  Architecture Blueprint · the PO decision register · the P6-2C artefacts.

The only files created are this readiness analysis and its mandatory
prompt-history record. No contract was created (the proposal in §9 is explicitly
labelled a proposal, not an authorisation). No commit, no push, no revert, no
cleanup of the pre-existing working tree.

---

## 20. Evidence index (documents and code inspected)

**Authority / architecture / roadmap:** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`;
`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (§9, §12, §13, §14, §18);
`CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md` (§26, §27, §28, §30);
`CARBONTALLY_PHASE6_P0_PO_RATIFICATION_REPORT.md`;
`CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` (§13, §14);
`CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md` (§21, §22, §23);
`CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` (D1–D11, cross-dependencies,
P6-2C ratified entries).

**P6-2C records:** `CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_CONTRACT.md`;
`docs/cline/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_REPORT.md`;
`docs/cline/CARBONTALLY_P6_2C_INDEPENDENT_VERIFICATION_REPORT.md`;
`docs/cline/prompt-history/CT-P6-2C-RA-20260910-001.md`.

**Earlier P6-2 evidence:** P6-2A verification + R1 re-verification reports;
P6-2B-1/2/3 implementation + verification reports; P6-2B-4 implementation report.

**Code inspected (read-only):** `backend/api/v3_processing_workflow.py`
(consultant submit route + D6 call site + approval guards);
`backend/services/billing.py` (`ensure_processing_entitlement`, `charge_processing`);
`backend/domain/processing_origin.py`; `backend/domain/partners.py`
(`WORKFLOW_STAGES`, `ITEM_STATUS_FLOW`, consultant capability flags);
`backend/data/manual_extraction.py`; `backend/api/v3_messaging.py`;
`backend/data/messaging.py`; `backend/data/notifications.py`;
`backend/services/work_items.py`; `backend/api/v3_consultants.py`;
`backend/api/v3_operations.py`; `backend/api/v3_qc.py`;
`frontend/src/v3/consultant/*` (`ConsultantPage.jsx`, `ConsultantItemPage.jsx`,
`ClientMessagingTab.jsx`, `ConsultantTeamTab.jsx`, `NewCustomerView.jsx`,
`WhiteLabelTab.jsx`); `frontend/src/v3/api.js`;
`frontend/src/v3/__tests__/consultant-page.test.jsx`;
`qa_harness/browser/**`; `playwright.config.ts`; `tests/example.spec.ts`;
`supabase/migrations/` (inventory only).

**Prompt-history records inspected:** `CT-P6-2C-RA-20260910-001.md`,
`CT-P6-2C-PO-20260910-001.md`, `CT-P6-2C-IMPL-20260910-001.md`,
`CT-P6-2C-IV-20260910-001.md`.











