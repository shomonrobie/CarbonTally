# CarbonTally — P6-2E Implementation Report

**Prompt Ref:** `CT-P6-2E-IMPL-20260910-001`
**Response Ref:** `CT-P6-2E-IMPL-20260910-001-R1`
**Implementation date/time:** 2026-09-10 20:22 → 20:47 (+0600)
**Phase / Checkpoint / Gate:** Phase 6 / CP2 / P6-2E — Consultant Vocabulary & Lifecycle Events
**Mode:** IMPLEMENTATION (no independent verification performed)

---

## 1. Prompt Ref

`CT-P6-2E-IMPL-20260910-001` (TASK: "CarbonTally — P6-2E Implementation", 30 sections,
ABSOLUTE RULE: implement P6-2E only).

## 2. Response Ref

`CT-P6-2E-IMPL-20260910-001-R1` — implementation session, verdict
`P6-2E IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`.

## 3. Implementation date/time

Start 2026-09-10 20:22:27 +0600 (baseline capture), end 2026-09-10 20:47:09 +0600
(final Git snapshot).

## 4. Authority documents inspected

* `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`
* `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`
* `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` (D8, D11 + L580–582 delegation)
* `docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md` (§7)
* `docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md`
* `docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`
* `docs/architecture/CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md`
* `docs/cline/CARBONTALLY_P6_2E_PREFLIGHT_REPORT.md`
* `docs/cline/CARBONTALLY_CP1_CLOSURE_REPORT.md`
* `docs/cline/CARBONTALLY_P6_2D_IMPLEMENTATION_REPORT.md`,
  `docs/cline/CARBONTALLY_P6_2D_INDEPENDENT_VERIFICATION_REPORT.md`

Implementation inspected before change: `backend/data/notifications.py`,
`backend/data/consultants.py`, `backend/data/organizations.py`,
`backend/data/manual_extraction.py`, `backend/api/v3_messaging.py`,
`backend/api/consultant_auth.py`, `backend/api/v3_organizations.py`,
`backend/api/v3_processing_workflow.py`, `backend/api/v3_operations.py`,
`backend/api/v3_notifications.py`, `backend/services/work_items.py`,
`backend/infra/event_bus.py`, `supabase/migrations/20260902050000_phase5_notification_event_key.sql`,
`supabase/migrations/20260902040000_phase5_pe_operational_messaging.sql`,
`backend/tests/unit/api/fakes.py`, `backend/tests/unit/api/conftest.py` and the
P6-1C / P6-2B-1 / P6-2B-2 / P6-2B-3 / P6-2C test suites.

## 5. Baseline repository state (measured before implementation)

| Item | Value |
| --- | --- |
| Branch | `main` |
| HEAD | `1639121` |
| porcelain entries | 671 |
| tracked `M` files | 284 (all pre-existing) |
| Backend tests collected (`pytest tests/unit --collect-only`) | **1627** |
| Date/time of baseline capture | 2026-09-10 20:22:27 +0600 |

## 6. D8 assessment — reuse the existing conversation model

**Result: D8 required ZERO production change.** Verified in source before acting:

* `api/v3_messaging.py::_authorize_org_actor` returns participant role
  `consultant` for a caller with an ACTIVE consultant-client grant
  (`ensure_consultant_org_access` → `consultants.get_client_by_org`). Consultants
  therefore participate through the existing conversation model with no new kind.
* `conversation_kind` vocabulary in the migrations is exactly `org` / `entity`
  (constrained by the existing multi-line CHECK in
  `20260902040000_phase5_pe_operational_messaging.sql`).
* No consultant-specific conversation table, kind, role, capability or
  permission was added.

D8 delivery is therefore *verification coverage only* (3 new tests, §16).

## 7. D11 design

* New centralised module `backend/services/consultant_lifecycle.py` owns the five
  event definitions, the deterministic key builder, the server-side recipient
  derivation and the emit helper. No parallel event system was introduced.
* Persistence uses the **existing durable** path:
  `NotificationsRepository.create_idempotent` → `public.notifications`
  (`ON CONFLICT (recipient_id, event_key) WHERE event_key IS NOT NULL DO NOTHING`,
  unique index `uq_notifications_event_key`). `notification_type` and
  `actor_domain` are existing columns; no schema change.
* The in-process `infra/event_bus.py` is **deliberately NOT used** for D11
  (fire-and-forget, non-durable). It remains untouched.
* Emits are invoked **after** authorization + the state mutation + the success
  audit, so a denied/failed request emits nothing.
* Emission is best-effort and logged (mirrors `services/work_items.py`): a
  notification failure can never fail the business action.

## 8. Five event definitions

| # | Event (`event` / `notification_type`) | Business meaning | Actors notified |
| --- | --- | --- | --- |
| 1 | `accepted` / `consultant.lifecycle.accepted` | Client org accepted the consultant engagement | Engaged firm members |
| 2 | `submitted_to_qc` / `consultant.lifecycle.submitted_to_qc` | Consultant submitted reviewed work to CT-QC | Engaged firm members + internal ops |
| 3 | `qc_outcome` / `consultant.lifecycle.qc_outcome` | CarbonTally QC decision (approved/rejected) | Engaged firm members |
| 4 | `customer_decision` / `consultant.lifecycle.customer_decision` | Client approved/rejected the processed item | Engaged firm members |
| 5 | `rework` / `consultant.lifecycle.rework` | Work returned for rework | Engaged firm members |

Rework sources (stable discriminators, never client-supplied):
`ct_qc_rejected`, `consultant_review_rejected`.

## 9. Trigger locations

| Event | Trigger (existing route) | Emit site |
| --- | --- | --- |
| 1 `accepted` | `POST /api/v3/organizations/{org_id}/consultant-engagements/{engagement_id}/accept` (`api/v3_organizations.py`, after `transition_client_lifecycle` + audit) | `notify_engagement_accepted` |
| 2 `submitted_to_qc` | `POST /api/v3/processing/items/{item_id}/consultant-submit` (`api/v3_processing_workflow.py`, after `set_item_status` + audit) | `notify_submitted_to_qc` |
| 3 `qc_outcome` (+5 on rejection) | `POST /api/v3/ops/qc/items/{item_id}/decision` (`api/v3_operations.py`, after the decision + append-only audit) | `notify_qc_outcome` (+ `notify_rework`) |
| 4 `customer_decision` | `POST /api/v3/processing/items/{item_id}/customer-review` (`api/v3_processing_workflow.py`, after `customer_review` + issue closure) | `notify_customer_decision` |
| 5 `rework` | `POST /api/v3/processing/items/{item_id}/consultant-review` when `passed=false` (`api/v3_processing_workflow.py`, after the rejection transition + audit) | `notify_rework` |

Total emit sites: **6** (five events; `rework` fires from two governed sources).

## 10. Deterministic event-key design

```
consultant.lifecycle.<event>:<identity>[:<discriminator>]
```

| Event | Key |
| --- | --- |
| accepted | `consultant.lifecycle.accepted:engagement:<engagement_id>` |
| submitted_to_qc | `consultant.lifecycle.submitted_to_qc:item:<item_id>` |
| qc_outcome | `consultant.lifecycle.qc_outcome:item:<item_id>:approved\|rejected` |
| customer_decision | `consultant.lifecycle.customer_decision:item:<item_id>:approved\|rejected` |
| rework | `consultant.lifecycle.rework:item:<item_id>:<source>` |

* Derived only from stable server-side business identity (item/engagement id +
  outcome). No randomness, no request-supplied component, no clock.
* Namespace mirrors the `notification_type` value (`consultant.lifecycle.*`).
* Database uniqueness (`uq_notifications_event_key`, per recipient+key) is the
  final idempotency boundary: a retry/replay can never duplicate a notification.
* `lifecycle_event_key` raises `ValueError` for any event outside the five-event
  vocabulary (no accidental event minting).

## 11. Recipient matrix (derived, not decorative)

| Event | Engaged firm members | Internal CT ops | Client org | QC staff |
| --- | --- | --- | --- | --- |
| accepted | ✅ (`engagement.consultant_id` → active members) | — | — (client is the actor) | — |
| submitted_to_qc | ✅ (active grants for the item's org) | ✅ (`support_staff_user_ids`) | — | — |
| qc_outcome | ✅ | — | — | — (QC actor is staff; no self-notify) |
| customer_decision | ✅ | — | — (client is the actor) | — |
| rework | ✅ | — | — (internal rework, not customer-visible) | — |

Rationale: all five events concern the consultant firm's processing
participation (the party that must act or be informed). Events 1 and 4 are
triggered *by* the client, so notifying the client of its own action adds no
signal; events 3 and 5 are internal quality-gate transitions (the mediated
rework loop is not customer-visible). Client-facing visibility continues through
the existing customer-review surface, not through internal lifecycle notices.

Derivation sources (all existing, all server-side):
`consultants.list_firm_members` (active members only),
`consultants.list_active_client_grants` (status `active` only),
`notifications.support_staff_user_ids` (existing internal-ops resolver).

## 12. Authorization / security design

* No route's authorization was modified; emits are placed strictly after the
  existing authorization + mutation + audit, so denied paths cannot emit.
* Recipients are never read from the request. A client cannot supply a
  recipient, an event key or an actor domain (test:
  `test_recipients_are_server_derived_and_body_injection_is_ignored`).
* Cross-organisation and cross-firm isolation is preserved: recipients are
  limited to firms holding an ACTIVE grant for the item's organisation and the
  active members of those firms (tests:
  `test_cross_firm_and_cross_org_recipients_are_excluded`,
  `test_no_active_grant_means_no_firm_recipients`,
  `test_engagement_accepted_emits_lifecycle_event_for_firm_members`).
* No RLS change, no policy change, no service-role escalation was required.
* No new role, capability, permission or grant was introduced. The
  `can_manage_staff` predicate used by `support_staff_user_ids` already existed.

## 13. Files created

| File | Purpose |
| --- | --- |
| `backend/services/consultant_lifecycle.py` | Centralised D11 definitions, deterministic keys, server-derived recipients, five public `notify_*` emit helpers |
| `backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py` | 27 focused D11 + D8 tests |
| `docs/cline/CARBONTALLY_P6_2E_IMPLEMENTATION_REPORT.md` | This report |
| `docs/cline/prompt-history/CT-P6-2E-IMPL-20260910-001.md` | Durable prompt/response history |

## 14. Files modified

| File | Change (P6-2E only) |
| --- | --- |
| `backend/api/v3_organizations.py` | +7 lines: engagement-accept emit (event 1) |
| `backend/api/v3_processing_workflow.py` | +3 hunks: submit (event 2), consultant-review rework (event 5), customer decision (event 4) |
| `backend/api/v3_operations.py` | +1 hunk: CT-QC outcome (event 3) + rejection rework (event 5) |
| `backend/tests/unit/api/fakes.py` | +`MemoryNotifications` (idempotency-faithful fake with `rows`/assertion helpers) and bundle wiring — `notifications` was previously a no-op `_StubRepo` |

**Pre-existing working-tree modifications are preserved and were NOT cleaned.**
`git diff --stat` for those four files totals 1846 insertions / 29 deletions, the
overwhelming majority of which pre-date this session (the baseline snapshot
already recorded 284 tracked `M` files). Only 6 P6-2E marker hunks are mine
(`grep -c 'P6-2E (D11)'`: 1 + 1 + 3 across the three API files; 1 `P6-2E` marker
in `fakes.py`). `find … -newermt 20:20` over `backend frontend supabase tests`
returns exactly the six implementation/test files and nothing else.

## 15. Files intentionally unchanged

`backend/data/notifications.py`, `backend/data/consultants.py`,
`backend/data/organizations.py`, `backend/data/manual_extraction.py`,
`backend/api/v3_messaging.py`, `backend/api/consultant_auth.py`,
`backend/domain/messaging.py`, `backend/api/v3_notifications.py`,
`backend/infra/event_bus.py`, `supabase/migrations/**` (no migration),
any RLS policy, and all P6-2C / P6-2D provenance code.

## 16. Tests added (27, all in the new focused module)

| Group | Tests |
| --- | --- |
| Event 1 accepted | emit + recipient derivation; denied paths (member/other-org-admin/unauthenticated); replay emits no additional event |
| Event 2 submitted_to_qc | deterministic key + firm recipients; internal-ops recipients; capability denial; state/grant/unauthenticated denials; replay; alternate route (`ops/items/{id}/submit-review`) emits nothing |
| Event 3 qc_outcome | approval (firm only, no QC self-notify, no rework event); rejection (outcome + rework); denials (no `can_qc`, unauthenticated, consultant); replay 409 → no duplicate |
| Event 4 customer_decision | approval (firm only, client actor excluded); rejection (decision only, no rework); denials (member / cross-org owner / consultant / unauthenticated) |
| Event 5 rework | consultant-review rejection emits rework; passed review and denied review emit nothing |
| Recipients / isolation | body-injection ignored; cross-firm & cross-org exclusion; suspended grant → no firm recipients |
| Idempotency / key design | service replay → exactly one row per recipient; key determinism/namespace/outcome-distinctness/unknown-event `ValueError`; exact five-event vocabulary |
| D8 | consultant participates via the existing conversation model (participant role `consultant`); no-grant consultant denied; no consultant `conversation_kind`/table in migrations |

## 17. Tests executed

| Run | Command | Result |
| --- | --- | --- |
| Focused (iteration 1) | `pytest tests/unit/api/test_p6_2e_consultant_lifecycle.py -q` | 19 failed / 1 passed — 2 defects injected by the *tests* (wrong expected key literal, missing `_rows` helper) + 1 test that merely confirmed isolation (missing grant seed) |
| Focused (iteration 2) | same | 3 failed / 24 passed — remaining test-authoring issues corrected (submission denial ordering, rework `actor_domain` expectation, missing `_seed_grant`) |
| Focused (iteration 3) | same | **27 passed, 0 failed, 0 errors, 0 skipped, exit 0** |

No production behaviour was changed as a result of the failing iterations; all
three corrections were to test expectations/seeding (two of them because the
implementation was *more* correct than the test assumed).

## 18. Regression results

| Run | Command | Collected | Result | Exit |
| --- | --- | --- | --- | --- |
| Baseline (before) | `pytest tests/unit --collect-only -q` | **1627** | n/a | 0 |
| After (collect) | `pytest tests/unit --collect-only -q` | **1654** | 1627 + 27 new | 0 |
| Targeted regression | `pytest tests/unit/api tests/unit/services tests/unit/infra -q` | 1170 | **all passed** (0 failures/errors) | 0 |
| Full unit suite | `pytest tests/unit -q` | 1654 | **all passed** (0 failures/errors/skips) | 0 |

Note: this environment's pytest output omits the final "N passed" summary line,
so counts are derived from the collected-per-file listing and the progress output
(1654 executed marks, zero `F`/`E`). Exit code 0 in both runs.

P6-2C / P6-2D / messaging / notification suites that ran inside the full suite
include `test_v3_notifications.py`, `test_p6_2b_1..4`, `test_p6_2c_approval_boundary.py`,
`test_p6_2d_entitlement.py`, `test_p6_2d_provenance.py`, `test_p6_1c_engagement_confirmation.py`,
`test_v3_consultants.py`, `test_v3_qc.py`, `test_d19_lifecycle.py` — all passed.

## 19. Migration / schema assessment

**No migration was created and none is required.** The implementation reuses
existing columns (`notifications.event_key`, `notifications.actor_domain`,
`notifications.notification_type`) and the existing partial unique index
`uq_notifications_event_key` added by
`supabase/migrations/20260902050000_phase5_notification_event_key.sql`.
`supabase/migrations/` is unmodified.

## 20. RLS assessment

**No RLS change.** No policy, no `USING`/`WITH CHECK` clause and no helper
function was modified. Notification reads remain the caller-scoped existing
surfaces (`list_for_user` filters `recipient_type='user' AND recipient_id=$1`).

## 21. Roles / capabilities / permissions assessment

**None created or broadened.** The only capability reference is the *existing*
`can_manage_staff` predicate inside the *existing*
`notifications.support_staff_user_ids()` resolver (used unchanged). No new role,
capability, permission or grant row was added, and no authorization decision in
any route changed.

## 22. Security findings

| Test | Expected | Actual | Result |
| --- | --- | --- | --- |
| Recipient injection (body `recipients`/`event_key`/`actor_domain`) | ignored/rejected | ignored; only server-derived recipient + deterministic key persisted | PASS |
| Cross-org recipient | excluded | excluded (`test_cross_firm_and_cross_org_recipients_are_excluded`) | PASS |
| Cross-firm recipient | excluded | excluded (firm without an active grant for the item's org) | PASS |
| No active grant | zero firm recipients | zero rows; request itself denied 403 | PASS |
| Unauthenticated event trigger (all 5 routes) | denied, no event | 401 and zero notification rows | PASS |
| Denied transition / insufficient capability | no event | 403 and zero notification rows | PASS |
| Duplicate event (HTTP replay) | one durable event | second attempt 409; row count unchanged | PASS |
| Replay at the durable layer | no duplicate | second identical emit reuses the existing row (`create_idempotent`) | PASS |
| Event-key collision | safely suppressed | DB unique index + `ON CONFLICT DO NOTHING`; deterministic keys | PASS |
| Alternate route (`ops/items/{id}/submit-review`) | protected | emits no consultant lifecycle event | PASS |
| Inactive firm member | excluded | excluded from recipients | PASS |
| Suspended engagement grant | no recipient/no access | 403, zero rows | PASS |
| QC actor self-notification | none | QC staff never a recipient of their own decision | PASS |

No unexpected ALLOW was observed.

## 23. Limitations

1. **Recipient matrix is firm-centric by derivation** — no client-org recipient
   is notified for any of the five events (rationale in §11). Client-facing
   visibility remains the existing customer-review surface. If the Product Owner
   wants client-side lifecycle notices, that is a new recipient-policy decision.
2. **Per-cycle rework attribution** — the `rework` key is
   `item:<id>:<source>`. A *second* rework cycle from the same source state for
   the same item does not re-notify (deliberate idempotency). Distinguishing
   cycles would require durable per-item cycle state (a schema change ⇒ STOP
   condition), so it was not implemented.
3. **Customer rejection is not a rework source** — a customer rejection emits
   event 4 with outcome `rejected` (the firm is informed and must act) rather
   than a separate event 5. Only the two governed internal sources
   (`ct_qc_rejected`, `consultant_review_rejected`) produce `rework`.
4. **Notification delivery is in-app only** — no email/push channel was added;
   D11 defines the durable in-app event. Email remains a separate concern.
5. **Fake-based verification** — API tests run against in-memory repositories
   (the established convention). The `MemoryNotifications` fake mirrors the
   unique-index idempotency semantics but is not the database; the real DB
   constraint path (`ON CONFLICT … DO NOTHING`) is covered by inspection, not by
   an integration test in this session.
6. **No live-database execution** — no local Supabase instance was driven; all
   evidence is unit/API-level.
7. Pre-existing working-tree modifications in the four touched files remain
   (not mine, intentionally not cleaned); a reviewer must diff by hunk.

## 24. Risks

* **Low** — additive only: no schema, RLS, role, permission or route
  authorization change; emits are post-success and best-effort.
* **Low** — best-effort emit swallows (and logs) notification failures; a
  persistence outage therefore loses a notification rather than the workflow
  action. Acceptable and consistent with the existing `work_items.py` emitter,
  but it does mean "workflow succeeded" does not strictly imply "notification
  persisted".
* **Medium (operational)** — for events 3–5 the item's organisation is resolved
  by loading the item's batch when the route did not already have it
  (one extra read on the CT-QC decision path only).
* **Low** — the client-facing notice gap (§23.1) is a product expectation risk,
  not a security risk.

## 25. Scope compliance

Confirmed: no P6-2D reopening, no provenance expansion (no `confirm`/`retry`
provenance, no consultant-firm/processing-mode provenance change), no F1
implementation, no RLS modification, no migration, no new roles/capabilities/
permissions, no consultant `conversation_kind` or conversation table, no
`/consultant` UI redesign, no browser E2E, no Auditor/Assurance, no Analytics,
no Phase 7/8 work, no billing change.

## 26. Commands executed (verbatim intent)

```bash
git rev-parse --abbrev-ref HEAD ; git rev-parse --short HEAD ; git status --porcelain=v1
python -m pytest tests/unit --collect-only -q -p no:cacheprovider          # baseline 1627
python -m pytest tests/unit/api/test_p6_2e_consultant_lifecycle.py -q      # focused (x3)
python -m pytest tests/unit/api tests/unit/services tests/unit/infra -q    # targeted regression
python -m pytest tests/unit -q                                             # full suite
python -m pytest tests/unit --collect-only -q -p no:cacheprovider          # after 1654
git --no-pager diff --stat -- <four modified files>
find backend frontend supabase tests -newermt '2026-09-10 20:20' -type f
```

## 27. Git status

| Item | Before | After |
| --- | --- | --- |
| Branch | `main` | `main` (unchanged) |
| HEAD | `1639121` | `1639121` (unchanged) |
| porcelain entries | 671 | 673 (+2 untracked P6-2E source/test files) |
| tracked `M` files | 284 | 284 (unchanged — no tracked-file-count change) |

P6-2E changes: 2 new untracked files (`backend/services/consultant_lifecycle.py`,
`backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py`) + 6 in-place hunks in
4 already-modified tracked files + 2 new docs. **No `git add`, no commit, no
push, no reset, no clean.** Unrelated modifications were left untouched.

## 28. Final verdict

`P6-2E IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

> **Independent verification has NOT been performed in this session.**

## 29. Stop-condition confirmation

No stop condition was triggered: no new role/capability/permission was needed,
no RLS modification was needed, no schema migration was needed, recipient
semantics were established safely from existing relationships, no existing
authorization boundary conflicted with D11, cross-org/cross-firm isolation is
guaranteed by construction and tested, deterministic idempotency is guaranteed
by the deterministic key + existing DB unique index, no architecture conflict
with the Blueprint/PO register appeared, and no P6-2D / F1 / P6-2F / Phase 7–8
work was required.

Implementation stopped at the P6-2E boundary. The next action is a **separate
independent P6-2E verification session**.




