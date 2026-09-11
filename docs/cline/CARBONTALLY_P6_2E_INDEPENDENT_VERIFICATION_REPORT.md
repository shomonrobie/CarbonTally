# CarbonTally — P6-2E Independent Verification Report (CP2 / IV)

**Prompt Ref:** `CT-P6-2E-IV-20260910-001`
**Response Ref:** `CT-P6-2E-IV-20260910-001-R1`
**Verification date/time:** 2026-09-10, window 23:00 → 23:45 (+0600); repository clock captured `2026-09-10 23:39:50 +0600`
**Verifier role:** Independent verifier — fresh session, **not** the implementation agent; read-only / no remediation apart from the two mandated verification documents.
**Verification scope:** independently re-derive the repository, source, execution, schema, notification/event, authorization, idempotency, isolation, test, working-tree and scope state for the completed **P6-2E — Consultant Vocabulary (D8) & Lifecycle Events (D11)** against the ratified PO decisions, the Phase-6 Remainder Implementation Contract V1.0 and the P6-2E preflight.

**Final verdict:** `P6-2E INDEPENDENTLY VERIFIED — PASS WITH NON-BLOCKING FINDINGS`

> This verification does **not** trust the implementation report as proof. Every conclusion below
> was re-derived from primary sources (repository code, migrations, tests, execution). The
> implementation report is treated as *evidence to challenge*, not authority.

---

## 1. Prompt Ref

`CT-P6-2E-IV-20260910-001` — TASK "CarbonTally — P6-2E Independent Verification" (42 sections;
ABSOLUTE READ-ONLY RULE; one verdict; create the verification report + durable history; STOP).

## 2. Response Ref

`CT-P6-2E-IV-20260910-001-R1`.

## 3. Verification date/time

2026-09-10, approximately 23:00 → 23:45 (+0600). Repository clock captured at the end of evidence
collection: `2026-09-10 23:39:50 +0600`. The implementation session ended 20:47; no change
attributable to P6-2E occurred between the implementation window and this verification (confirmed
by `find -newermt`).

## 4. Verifier role

Independent verifier. Read-only. No production code, tests, migration, schema, RLS, frontend or
configuration was modified, and no defect was fixed. The only files this session created are the
two mandated verification documents (§31, §37).

## 5. Authority documents inspected

| # | Document | Used for |
|---|---|---|
| 1 | `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | architectural basis |
| 2 | `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | §9 gate order `P6-2C → P6-2D → P6-2E → P6-2F`; P6-2E = D39(D8) + D40(D11) |
| 3 | `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` | D8 (B — reuse), D11 (A — five events), L580–582 delegation, frozen P6-2C invariants |
| 4 | `docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md` | §7.1 (D8 Preserve+Verify), §7.2 (D11 events, emit/recipient table, non-decision, "no migration"), §8 billing, §10 frozen invariants |
| 5 | `docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` | consultant workflow context |
| 6 | `docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md` | review/QC context |
| 7 | `docs/cline/CARBONTALLY_P6_2E_PREFLIGHT_REPORT.md` | readiness input (§12–§15) |
| 8 | `docs/cline/CARBONTALLY_P6_2E_IMPLEMENTATION_REPORT.md` | **evidence challenged**, not authority |
| 9 | `docs/cline/CARBONTALLY_CP1_CLOSURE_REPORT.md` | CP1 closed; P6-2D frozen; F1 decision |
| 10 | `docs/cline/prompt-history/CT-P6-2E-IMPL-20260910-001.md` | implementation prompt/response record |
| 11 | `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md` | PO decision text |
| 12 | `docs/cline/CARBONTALLY_P6_2D_IMPLEMENTATION_REPORT.md`, `..._P6_2D_INDEPENDENT_VERIFICATION_REPORT.md` | P6-2D frozen baseline (context only) |

Primary sources re-read directly: `backend/services/consultant_lifecycle.py`, `backend/data/notifications.py`,
`backend/data/consultants.py`, `backend/domain/processing_origin.py`, `backend/api/v3_organizations.py`,
`backend/api/v3_processing_workflow.py`, `backend/api/v3_operations.py`, `backend/api/v3_automatic_processing.py`,
`backend/api/v3_messaging.py`, `backend/api/consultant_auth.py`, `backend/api/v3_consultants.py`,
`backend/infra/event_bus.py`, `supabase/migrations/20260902050000_phase5_notification_event_key.sql`,
`supabase/migrations/20260902040000_phase5_pe_operational_messaging.sql`,
`backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py`, `backend/tests/unit/api/fakes.py`.

## 6. Repository baseline (independently measured)

| Item | Value (independently observed) |
|---|---|
| Branch | `main` |
| HEAD | `1639121` (`16391217103b98dcea520070c5a22c68f12fe607`) — unchanged |
| Porcelain entries | **675** = 284 ` M` (tracked modified) + 152 ` D` (tracked deleted) + 239 `??` (untracked) |
| Commit / push / stage | **none** performed by this session |
| Tests collected | **1654** |
| Tests executed | **1654 passed, 1 warning, exit 0** |

**P6-2E attributable change set (independently established):**

* **Created (`??` untracked):** `backend/services/consultant_lifecycle.py`;
  `backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py`;
  `docs/cline/CARBONTALLY_P6_2E_IMPLEMENTATION_REPORT.md`;
  `docs/cline/prompt-history/CT-P6-2E-IMPL-20260910-001.md`.
* **Modified in place (6 `P6-2E` markers):** `backend/api/v3_organizations.py` (1),
  `backend/api/v3_operations.py` (1), `backend/api/v3_processing_workflow.py` (3),
  `backend/tests/unit/api/fakes.py` (1). `grep -rn 'P6-2E' backend --include=*.py` returns exactly
  these 6 markers (the `fakes.py` marker reads `# P6-2E — stateful notifications surface (D11 …)`,
  which is why a literal `P6-2E (D11)` search under-counts it).
* **Method:** `find backend frontend supabase tests -newermt '2026-09-10 20:20' -type f` returns
  exactly those 6 files — no other file in those trees changed.
* **Untouched (mtime pre-window):** `data/notifications.py` (09-02), `data/consultants.py` (09-06),
  `domain/processing_origin.py` (09-02), `services/billing.py` (09-06), `domain/billing.py` (09-05),
  `infra/event_bus.py` (08-07), `api/consultant_auth.py` (09-10 19:22); all of `supabase/**`
  (newest migration `20260910120000_p6_2d_consultant_provenance.sql`, 19:21 — pre-window).

> **Limitation.** The working tree is deeply dirty (284 pre-existing tracked modifications). Because
> the pre-P6-2E content of the four modified files was never committed, the exact *delta* attributable
> to P6-2E cannot be proved by `git diff` alone. It was established by (a) the 6 in-code `P6-2E`
> markers, (b) the `-newermt` window, and (c) functional tracing of every emit site.

## 7. D8 verification — consultant vocabulary

**Result: PRESERVED — zero production change; no consultant conversation kind; no consultant table; no new role/capability/permission. VERIFIED.**

| Check | Method (primary source) | Result |
|---|---|---|
| Consultants participate through the existing conversation mechanism | `api/v3_messaging.py::_authorize_org_actor` admits a caller via `ensure_consultant_org_access(...)` and returns participant role `"consultant"` | VERIFIED |
| Active grant determines participation | `api/consultant_auth.py::ensure_consultant_org_access` → `consultants.get_client_by_org(profile_id, org)` requires `client.status == "active"` (D15) | VERIFIED |
| `conversation_kind` vocabulary unchanged | migration `CHECK` vocabulary ⊆ {`org`,`entity`}; only `org`/`entity` appear in `supabase/migrations/*.sql` | VERIFIED |
| No consultant-specific conversation kind | repo scans — no `conversation_kind = 'consultant'` | VERIFIED |
| No consultant-specific conversation table | no `consultant_conversations` anywhere outside the new test's negative assertion | VERIFIED |
| No new role / capability / permission | `consultant_lifecycle.py` introduces none; the six consultant capability flags are untouched; `consultant_auth.py` mtime pre-window | VERIFIED |
| Organisation isolation intact | no-grant consultant → `POST /api/v3/messaging/conversations` = 403 (focused test, re-run) | VERIFIED |
| Participation does not bypass authorization | participant role resolved through the same `_resolve_context`/grant chain as every other consultant route | VERIFIED |

**Are the three reported D8 tests meaningful?** Yes, with one caveat.
`test_consultant_participates_through_existing_conversation_model` asserts the conversation's org
**and** the persisted participant role `consultant` through the real repository surface — meaningful.
`test_consultant_without_grant_cannot_message_client_org` asserts a real `403` — meaningful negative test.
`test_no_consultant_conversation_kind_was_introduced` is a repository scan over
`supabase/migrations/*.sql`; it is a legitimate guard for the *ratified migration-level* vocabulary but
it constrains **migrations, not Python** (recorded as IV-N7).

## 8. D11 five-event verification

The ratified D11 vocabulary is exactly `accepted`, `submitted_to_qc`, `qc_outcome`,
`customer_decision`, `rework` (`services/consultant_lifecycle.py::CONSULTANT_LIFECYCLE_EVENTS`).
All five are implemented, each at an existing trigger point; no new workflow, route or state was
introduced. `notification_type` = `consultant.lifecycle.<event>`.

**Event 1 — `accepted`** · `POST /api/v3/organizations/{org_id}/consultant-engagements/{engagement_id}/accept`
(`api/v3_organizations.py:706-743`). Authorization: `require_org_admin()` + `ensure_org_access(current_user, org_id)`
+ `can_transition_consultant_engagement(status, "active", actor_side="customer", origin=…)`; a non-pending
engagement raises `409` before any mutation. Mutation: `transition_client_lifecycle(engagement_id, "active")`
followed by `_audit_customer_engagement(...)`; only then `notify_engagement_accepted(repos, client=updated)`.
Key: `consultant.lifecycle.accepted:engagement:<engagement_id>`. Recipients: active members of
`client.consultant_id` (the engaged firm). Actor domain: `organisation_member`.
Meaning matches the ratified intent (the client organisation accepted the consultant engagement). **PASS.**

**Event 2 — `submitted_to_qc`** · `POST /api/v3/processing/items/{item_id}/consultant-submit`
(`api/v3_processing_workflow.py:714-793`). Authorization: `require_auth()` +
`ensure_consultant_submission_authorized` (active membership → active grant → `can_submit` → server-derived
scope → D38) + status must be `consultant_reviewed` (`409` otherwise) + `_require_transition` + the D6
non-charging entitlement preflight (fails closed). Mutation: `_record_consultant_provenance` →
`set_item_status("reviewed")` → `_audit_consultant_submit`; only then `notify_submitted_to_qc(repos, item, batch)`.
Key: `consultant.lifecycle.submitted_to_qc:item:<item_id>`. Recipients: active members of every firm holding an
**active** grant for the item's batch organisation, **plus** the existing internal ops resolver. Actor domain: `consultant`.
**PASS** (recipient-scope caveats at IV-N1/IV-N2).

**Event 3 — `qc_outcome`** · `POST /api/v3/ops/qc/items/{item_id}/decision` (`api/v3_operations.py:2038-2119`).
Authorization: `require_staff()` + `require_internal_staff(context)` + `ensure_staff_permission(context, "can_qc")`
+ `quality_score` range + status ∈ {`reviewed`,`pe_qc_approved`,`ct_qc`} (`409` otherwise). Mutation:
`manual_extraction.ct_qc_decision(...)` — the repository only mutates items still in CT-QC intake, so a concurrent
decision returns `None` → `409` with **no** audit and **no** event; a real decision records the append-only audit;
only then `notify_qc_outcome(...)`. Key: `consultant.lifecycle.qc_outcome:item:<item_id>:approved|rejected`.
Recipients: active members of active-grant firms for the item's org. Actor domain: `internal_staff`.
Both `approved` and `rejected` are handled. **PASS.**

**Event 4 — `customer_decision`** · `POST /api/v3/processing/items/{item_id}/customer-review`
(`api/v3_processing_workflow.py:910-1019`). Authorization: `require_org_admin()` (D5) + `_get_checked_item`
org scope + PE/CT-QC prerequisite + P6-2C automatic-only `calculated→approved` gate + P6-2B-4 manual CT-QC
prerequisite + `_require_transition` + rejection-reason `422`. Mutation: (approval) D37 `charge_processing`
with idempotency key `charge:item:<item_id>` → `customer_review(...)` → issue closure; only then
`notify_customer_decision(...)`. Key: `consultant.lifecycle.customer_decision:item:<item_id>:approved|rejected`.
Recipients: active members of active-grant firms for the item's org. Actor domain: `organisation_member`.
**Customer rejection emits `customer_decision:rejected` and NOT `rework`** — see §12/IV-N5. **PASS.**

**Event 5 — `rework`** · two sources, both after a *successful* transition:
(a) CT-QC rejection inside the same `/ops/qc/items/{id}/decision` handler (after `ct_qc_decision` + audit),
and (b) consultant review with `passed=false` — `POST /api/v3/processing/items/{item_id}/consultant-review`
(`api/v3_processing_workflow.py:587-663`), which requires status `calculated`, `_require_transition`,
a non-empty `rejection_reason`, then `set_item_status("mapping")` + audit; only then `notify_rework(..., source=REWORK_SOURCE_CONSULTANT_REVIEW_REJECTED)`.
Key: `consultant.lifecycle.rework:item:<item_id>:ct_qc_rejected` **|** `:consultant_review_rejected`.
A `passed=true` review emits nothing. Recipients: active members of active-grant firms for the item's org.
Actor domain: `internal_staff` (CT-QC) / `consultant` (review). **PASS** (cycle limitation at IV-N5).

## 9. Trigger matrix (independently reconstructed)

| Event | Trigger (route / state) | Authorization prerequisite | Event key | Recipients (server-derived) | Durable persistence | Idempotency | Denied path | Result |
| ----- | ----------------------- | -------------------------- | --------- | --------------------------- | ------------------- | ----------- | ----------- | ------ |
| `accepted` | `POST /organizations/{org}/consultant-engagements/{id}/accept`; after `transition_client_lifecycle(pending→active)` + audit | `require_org_admin` + `ensure_org_access` + `can_transition_consultant_engagement(..., actor_side="customer")`; 409 if not pending | `consultant.lifecycle.accepted:engagement:<id>` | active members of `engagement.consultant_id` (firm) | `notifications.create_idempotent` → `public.notifications` | DB `uq_notifications_event_key` + HTTP replay → 409 | member 403 · other-org admin 403 · unauth 401 → **0 rows** | PASS |
| `submitted_to_qc` | `POST /processing/items/{id}/consultant-submit`; after provenance + `set_item_status(→reviewed)` + audit | `require_auth` + `ensure_consultant_submission_authorized` (member → active grant → `can_submit` → scope → D38) + status `consultant_reviewed` + D6 entitlement | `consultant.lifecycle.submitted_to_qc:item:<id>` | active members of every active-grant firm for the batch org **+** `support_staff_user_ids()` | same | same | wrong state 409 · no `can_submit` 403 · suspended grant 403 · unauth 401 → 0 rows; replay 409 | PASS |
| `qc_outcome` | `POST /ops/qc/items/{id}/decision`; after guarded `ct_qc_decision` + audit | `require_staff` + `require_internal_staff` + `ensure_staff_permission("can_qc")` + status ∈ {reviewed, pe_qc_approved, ct_qc} + score 0..100 | `consultant.lifecycle.qc_outcome:item:<id>:approved\|rejected` | active members of active-grant firms for the item's org | same | same | no `can_qc` 403 · unauth 401 · consultant 403 · wrong state 409 · concurrent (None→409) → 0 rows | PASS |
| `customer_decision` | `POST /processing/items/{id}/customer-review`; after D37 charge + `customer_review` + issue closure | `require_org_admin` + `_get_checked_item` scope + PE/CT-QC prerequisite + P6-2C automatic-only gate + `_require_transition` + rejection-reason 422 | `consultant.lifecycle.customer_decision:item:<id>:approved\|rejected` | active members of active-grant firms for the item's org | same | same | member 403 · cross-org 403/404 · consultant 403 · unauth 401 → 0 rows | PASS |
| `rework` | (a) `/ops/qc/items/{id}/decision` **rejected**; (b) `/processing/items/{id}/consultant-review` `passed=false` (after `set_item_status(→mapping)` + audit) | as event 3 / as event 5(b) — status `calculated`, reason required (422) | `consultant.lifecycle.rework:item:<id>:ct_qc_rejected` / `:consultant_review_rejected` | active members of active-grant firms for the item's org | same | same | passed review → 0 rows · denied review → 0 rows · unknown-source key → `ValueError` | PASS |

Chronology for a rejected CT-QC item is preserved: `submitted_to_qc:item:<id>`, then
`qc_outcome:item:<id>:rejected`, then `rework:item:<id>:ct_qc_rejected` (see test
`test_qc_rejection_emits_outcome_and_rework`).

## 10. Event-key analysis

`lifecycle_event_key(event, *, identity, discriminator=None)` returns
`consultant.lifecycle.<event>:<identity>[:<discriminator>]`
(`services/consultant_lifecycle.py:82-99`). Properties independently established:

* **Deterministic** — pure string interpolation; no `uuid`, no randomness, no timestamp. Unknown
  events raise `ValueError`, so a typo cannot mint an unkeyed producer.
* **Stable business identity** — `engagement:<id>` for event 1; `item:<id>` for events 2–5. Identity
  is derived from server-loaded objects, never from the request.
* **No client control** — the key is built inside the module from `item`/`client` objects the route
  already loaded from the repository.
* **Outcome included where required** — `qc_outcome` and `customer_decision` carry
  `approved|rejected`; `rework` carries its stable source. `test_lifecycle_event_key_is_deterministic_and_server_generated`
  asserts approved ≠ rejected and two identity values produce distinct keys.
* **No unintentional collisions** — event type is namespaced; identity and discriminator separate
  distinct lifecycle events. (Deliberate *suppression* of repeats is IV-N5.)
* **Replay → same key.** `test_service_replay_persists_exactly_one_row_per_recipient` calls
  `notify_submitted_to_qc` twice and observes exactly one row.
* **Database uniqueness is the final boundary** —
  `supabase/migrations/20260902050000_phase5_notification_event_key.sql`:
  `CREATE UNIQUE INDEX uq_notifications_event_key ON public.notifications (recipient_id, event_key) WHERE event_key IS NOT NULL`,
  consumed by `NotificationsRepository.create_idempotent` via
  `ON CONFLICT (recipient_id, event_key) WHERE event_key IS NOT NULL DO NOTHING`.

**Duplicate/replay boundary — independently reasoned for one item:** the key is
`(recipient_id, event_key)`, so uniqueness is per recipient; the same business event emits at most one
row per recipient. Route-level replay (a second identical HTTP call) is additionally blocked by the
underlying state machine returning `409`, so it cannot re-emit even for a *different* recipient.
Tested: 1st emission (rows created), identical replay (409, row count unchanged), service-layer
replay (1 row), different outcome (distinct key — both may exist), different item/engagement
(distinct key). **One durable notification per intended lifecycle event per recipient: VERIFIED.**

## 11. Recipient matrix (independently reconstructed)

| Event | Consultant-firm recipients | Client-org recipients | CarbonTally / QC-Ops recipients | Actor domain |
| ----- | -------------------------- | --------------------- | ------------------------------- | ------------ |
| `accepted` | active members of the accepting engagement's firm | **none** | none | `organisation_member` |
| `submitted_to_qc` | active members of every active-grant firm for the org | none | internal staff resolved by `support_staff_user_ids()` (`can_manage_staff`) | `consultant` |
| `qc_outcome` | active members of active-grant firms for the org | **none** | none | `internal_staff` |
| `customer_decision` | active members of active-grant firms for the org | **none** | none | `organisation_member` |
| `rework` | active members of active-grant firms for the org | **none** | none | `internal_staff` / `consultant` |

Derivation mechanics: `_engaged_firm_ids` → `consultants.list_active_client_grants(org)` (SQL filter
`status = 'active'`) → `_firm_recipient_user_ids` → `consultants.list_firm_members(firm_id)` filtered in
Python by `is_active` and a truthy `user_id`. Internal recipients: `notifications.support_staff_user_ids()`
(`staff_profiles.entity_id IS NULL` AND role permissions `can_manage_staff = true`). Recipients are
de-duplicated with a set and sorted.

**Divergence from the ratified recipient table (see IV-C1).** The Implementation Contract §7.2 lists
**"client org owner/admin"** as a recipient for events **1, 3 and 4**, and the P6-2E preflight
(§12/§14/§83/§106/§113) repeats "client-org owner/admin for client-relevant events". The implementation
notifies **no client-org member for any event** — firm members only (plus internal ops for event 2), on
the stated rationale that the client is the actor for events 1/4 and events 3/5 are internal quality
gates. The same contract §7.2 and the register L580–582 declare the recipient matrix an **explicit
non-decision to be derived at implementation**, and the ratified PO policy does not enumerate
recipients. The authoritative documents therefore conflict; the implementation is self-consistent, it
under-notifies rather than over-notifies, and no privilege is granted. Classified **PO CLARIFICATION**
(IV-C1), non-blocking.

## 12. Recipient injection tests

* Routes carrying lifecycle emission accept **no** recipient/identity-bearing fields:
  `accept_consultant_engagement(org_id, engagement_id)` and `consultant_submit_item(item_id)` take **no body**;
  `customer_review_item` takes `{approved, rejection_reason, customer_notes}`;
  `ct_qc_decision_endpoint` takes `{quality_score, approved, qc_notes}`. None exposes `recipients`,
  `event_key`, `actor_domain`, org or firm.
* `test_recipients_are_server_derived_and_body_injection_is_ignored` posts
  `{"recipients": ["u-attacker"], "event_key": "attacker.chosen.key", "actor_domain": "internal_staff"}`
  to `consultant-submit` and asserts the only key is the server-derived one and the only recipient is
  `u-c1`. Because that route declares no body model, the injected JSON is simply ignored — which is
  exactly the guarantee, but the assertion is *weak* as a test (IV-N7a); the property is nonetheless
  structurally true for the routes that do accept bodies (their payload models have no recipient field).
* **Conclusion: recipients and event identity are server-derived and not client-controllable. VERIFIED.**

## 13. Cross-organisation isolation

Recipients are derived exclusively from the **item's/engagement's own organisation**, resolved
server-side (`_organization_id_for_item` loads the item's batch; event 1 uses the engagement's own
`org_id`). There is no request-supplied organisation or recipient. Test
`test_cross_firm_and_cross_org_recipients_are_excluded` seeds an item on `org-a` (firm-c1) and a second
grant `org-b`/firm-c2, then asserts only `u-c1` receives the `org-a` event. **Cross-org notification
leakage: NOT POSSIBLE — VERIFIED.** No path lets organisation A's event reach organisation B's users.

## 14. Cross-firm isolation

For a firm **without** an active grant for the organisation, isolation holds: `_engaged_firm_ids` only
returns firms whose `consultant_clients` row for that org is `status = 'active'`, so an unrelated firm
is never a recipient (same test). **Cross-firm leakage to an unrelated firm: NOT POSSIBLE — VERIFIED.**

**Nuance (IV-N2).** When **two firms both** hold active grants for the *same* organisation, both firms'
members receive an item event, because derivation is **organisation-grant-scoped**, not item-firm-scoped
(`_firm_and_ops` unions all `_engaged_firm_ids(org)`), even though P6-2D now records the item's actual
firm in `manual_extraction_items.consultant_firm_id`. This is **not** cross-tenant/cross-firm leakage:
both firms are already authorised for that organisation's resources under the ratified org-grant model.
It is over-breadth relative to "the actual workflow relationship" the register could be read to intend.
Recorded NON-BLOCKING for PO visibility; **not remediated**.

## 15. Denied-path verification

Every denied class was traced to a raise that precedes the emit call, and the focused tests assert both
the HTTP status and `_rows(world) == []`:

| Denied class | Evidence | Emitted? |
| ------------ | -------- | -------- |
| Unauthenticated | 401 on accept / submit / qc decision / customer-review | **0** |
| Unauthorised user (member, other-org admin, consultant on QC, etc.) | 403 | **0** |
| Missing capability (`can_submit` / `can_qc`) | 403 | **0** |
| Inactive / suspended grant | 403 (submit); zero firm recipients | **0** |
| Invalid state transition | 409 (wrong status, replay, concurrent QC) | **0** |
| Entitlement preflight failure (D6, fail-closed) | 4xx (`BillingError.status_code`) before mutation | **0** |
| Missing rejection reason | 422 | **0** |

These are demonstrated, not merely inferred: `test_engagement_accept_denied_paths_emit_nothing`,
`test_submission_without_capability_emits_nothing`, `test_submission_state_grant_and_auth_denials_emit_nothing`,
`test_qc_decision_denied_paths_emit_nothing`, `test_customer_decision_denied_paths_emit_nothing`,
`test_consultant_review_pass_and_denial_emit_nothing`, `test_no_active_grant_means_no_firm_recipients`.
**A denied operation emits zero lifecycle events. VERIFIED.**

## 16. Replay / idempotency

* **DB boundary:** `uq_notifications_event_key` (partial unique on `(recipient_id, event_key)`) +
  `create_idempotent` `ON CONFLICT … DO NOTHING` returning the existing row.
* **Service boundary:** deterministic key ⇒ identical replay is a no-op
  (`test_service_replay_persists_exactly_one_row_per_recipient` → 1 row).
* **HTTP boundary:** identical replay is refused by the workflow state machine (`409`) with the row count
  unchanged (`test_submission_replay_emits_one_durable_event`, `test_qc_decision_replay_emits_no_duplicate`,
  `test_engagement_accept_replay_emits_no_additional_event`).
* **Different outcome:** produces a distinct key (both `approved` and `rejected` rows may coexist).

**Replay cannot create duplicates. VERIFIED** (with the deliberate cycle-collapse behaviour of IV-N5).

## 17. Alternate-route analysis

Every route that can perform a relevant transition was enumerated:

| Route | Transition | Emits a D11 event? | Assessment |
| ----- | ---------- | ------------------ | ---------- |
| `POST /orgs/{org}/consultant-engagements/{id}/accept` | engagement → `active` | **yes** (`accepted`) | the ratified trigger |
| `POST /processing/items/{id}/consultant-submit` | `consultant_reviewed` → `reviewed` | **yes** (`submitted_to_qc`) | the ratified trigger |
| `POST /ops/qc/items/{id}/decision` | → `ct_qc_approved`/`ct_qc_rejected` | **yes** (`qc_outcome` + `rework`) | the ratified trigger |
| `POST /processing/items/{id}/customer-review` | → `approved`/`rejected` | **yes** (`customer_decision`) | the ratified trigger |
| `POST /processing/items/{id}/consultant-review` | → `consultant_reviewed`/`mapping` | **yes** on rejection (`rework`) | the ratified trigger (5b) |
| `POST /ops/items/{id}/submit-review` | `calculated` → `reviewed` (internal review) | **no** | **not** a D11 trigger: internal-origin review, not a consultant submission; explicitly asserted by `test_internal_submit_review_is_not_a_consultant_lifecycle_event` |
| `POST /automatic-processing/jobs/{job_id}/review` | writes the source item via `manual_extraction.customer_review(...)`, `→ approved`/`rejected` | **no** | **IV-N4** — a customer decision on the underlying item with no `customer_decision` event |
| `POST /consultants/clients/{client_id}/reactivate` | grant → `active` | **no** | **IV-N4** — an engagement can become active again without an `accepted` event |
| `POST /consultants/me/team/{member_id}/reactivate` | membership `is_active` → true | n/a | affects recipient derivation, not a lifecycle event |

**Expected property:** no *material* alternate-route bypass of the D11 contract. The two gaps
(automatic-processing job review; consultant `reactivate`) are **outside the contract's declared D11
trigger set** (contract §7.2 names the five routes explicitly) and neither crosses an authorization
boundary — both routes carry their own authenticated authorization, and automatic processing is
CarbonTally-staff-only (frozen invariant 4) so a consultant-provenance item should not normally reach
it. Recorded NON-BLOCKING (IV-N4). **No material bypass within the declared trigger set: VERIFIED.**

## 18. Authorization analysis

D11 introduces **no parallel authorization system**. Every emit site sits behind the pre-existing,
canonical gates and emits only after they pass:

* Event 1 — `require_org_admin()` + `ensure_org_access` + engagement transition rule (P6-1C).
* Event 2 — `require_auth()` + `ensure_consultant_submission_authorized` (the canonical P6-2A/2B-2 gate) + D6.
* Events 3/5a — `require_staff()` + `require_internal_staff` + `ensure_staff_permission("can_qc")`.
* Event 4 — `require_org_admin()` (D5) + `_require_transition` + PE/CT-QC prerequisites + D37 charge.
* Event 5b — `ensure_consultant_review_authorized` (P6-2B-1).

No new role, capability or permission appears anywhere in `consultant_lifecycle.py`; it is a pure
consumer of existing relationships (`consultants.*`, `notifications.support_staff_user_ids`). **VERIFIED.**

## 19. Emission ordering

Each handler performs, in order: authentication → authorization → validation/preflights → **data
mutation** → audit → **lifecycle emit** (last statement before returning). There is **no** code path
where an event is emitted and the subsequent business mutation fails: the emit is the final action and
its result is not used, so it cannot undo or precede the mutation. Traced for all five events
(`v3_organizations.py:730-743`, `v3_processing_workflow.py:778-793` & `1000-1019` & `637-663`,
`v3_operations.py:2065-2119`).

**Caveat (§20):** the emit is *after* success but *not in the same transaction*, so a crash between a
committed mutation and the emit loses the notification (over-emission cannot occur). **Emitted-before-
failed-mutation path: NONE — VERIFIED.**

## 20. Durability / best-effort analysis

`_emit` loops over recipients and wraps each `create_idempotent` in `try/except`, logging a warning on
failure and continuing (`consultant_lifecycle.py:177-198`). Consequences:

* Event failure **cannot** fail the business mutation (the mutation already committed).
* A persistence outage **loses the notice, not the action** — intended and mirrored from the existing
  `services/work_items.py` emitter convention.
* Partial failure within a loop (some recipients persisted, some not) is possible.
* The emit is **not** part of the same DB transaction as the mutation, and there is no outbox.

**Classification.** The ratified D11 policy requires deterministic/idempotent keys, the existing
idempotent infrastructure, server-derived recipients and no leakage. It does **not** explicitly mandate
transactional/at-least-once delivery, and the contract classifies the emitter as the *existing* pattern
to preserve. Best-effort is therefore **consistent with the authoritative contract and the pre-existing
architecture**, but it means "workflow succeeded" does not strictly imply "notification persisted".
Recorded as an acceptable non-blocking limitation with PO visibility (part of IV-N5's family; see
§32). No redesign performed.

## 21. In-process EventBus analysis

`backend/infra/event_bus.py` (mtimes 2026-08-07, pre-window) is an in-process, non-durable bus. The D11
module does **not** import or use it: `grep -n event_bus backend/services/consultant_lifecycle.py` = none;
the only `event_bus` references remain the pre-existing engine/worker paths (calculation, validation,
workflow, extraction, automatic-processing workers). **The authoritative D11 mechanism is durable
`public.notifications` persistence via `create_idempotent`, not the EventBus — VERIFIED.** Because the
EventBus is untouched by D11, it introduces no duplicate or ordering interaction.

## 22. Database / idempotency analysis

Inspected schema artefacts (existing, pre-P6-2E):

* `public.notifications` — `recipient_type`, `recipient_id`, `notification_type` (free-form text, no CHECK),
  `title`, `message`, `priority`, `link`, `event_key text`, `actor_domain text`, `is_read`, `created_at`.
* `event_key` and `actor_domain` added by `supabase/migrations/20260902050000_phase5_notification_event_key.sql`
  (`ADD COLUMN IF NOT EXISTS`).
* Uniqueness: `uq_notifications_event_key` = `UNIQUE (recipient_id, event_key) WHERE event_key IS NOT NULL`.
* Consumer: `NotificationsRepository.create_idempotent` (`data/notifications.py:116-167`) with
  `ON CONFLICT (recipient_id, event_key) WHERE event_key IS NOT NULL DO NOTHING`, re-reading the existing
  row when the insert is suppressed.

D11 uses the existing mechanism correctly and needs no schema change. **No migration was created by
P6-2E** (`ls -t supabase/migrations` → newest is `20260910120000_p6_2d_consultant_provenance.sql`, P6-2D),
consistent with contract §7.2 ("no migration … if a migration appears necessary, STOP and report").
`actor_domain` is populated per event; `notification_type` = `consultant.lifecycle.<event>`. **VERIFIED.**
*Limitation:* no live PostgreSQL was driven; the unique-index path was verified by SQL inspection and by
the in-memory fake that mirrors it (§33, IV-E2).

## 23. RLS analysis

**No RLS change was introduced.** `git status --porcelain -- supabase` shows no modified/new policy
migration attributable to P6-2E; the newest migration is the P6-2D one (pre-window); `find supabase`
after 20:20 returns nothing. D11 itself performs no direct SQL — it calls the repository, which uses the
same connection/session as all other backend data access, so there is no new RLS surface to police and no
RLS bypass added. **P6-2E introduced no RLS change — VERIFIED by repository inspection.**
*Limitation:* no live Supabase instance was driven, so RLS *enforcement* was not exercised (IV-E2). The
absence of live RLS testing is **not** taken as evidence that RLS is correct; the claim here is narrower
— P6-2E did not alter it.

## 24. Billing preservation

No billing file changed (`services/billing.py` mtime 2026-09-06, `domain/billing.py` 2026-09-05, both
pre-window). The only billing interaction touched by a D11 emit site is the *pre-existing* D37 charge at
customer approval (`charge:item:<item_id>`, unchanged) and the D6 non-charging entitlement preflight in
`consultant-submit` (unchanged read-only check). No new charge, no removed charge, no new billing state,
no subscription/credit change. D6/P6-2D billing behaviour is unchanged. **VERIFIED.**

## 25. P6-2D preservation (provenance / origin)

* `backend/domain/processing_origin.py` still contains exactly two origins
  (`CARBONTALLY_INTERNAL`, `PROCESSING_ENTITY`); **`CONSULTANT` is still not an origin** (grep = none).
* The P6-2D migration `20260910120000_p6_2d_consultant_provenance.sql` (firm/mode/write-once provenance)
  is untouched (pre-window).
* P6-2E adds **no** provenance to consultant automation `confirm`/`retry` (F1 remains out of scope /
  decided); `api/v3_automatic_processing.py` was **not** modified by P6-2E (not in the window).
* No P6-2D artefact was modified; P6-2D is **not** reopened. **VERIFIED.**

## 26. Focused tests

Command: `cd backend && python -m pytest tests/unit/api/test_p6_2e_consultant_lifecycle.py -p no:cacheprovider --tb=short`

Observed (independently):

```
...........................                                              [100%]
27 passed in 7.57s
EXIT=0
```

27 collected, 27 passed, 0 failed/error/skipped. `--collect-only` attributes 27 tests to this file.
The suite covers: all five positive events; the two rework sources; replay; cross-org and cross-firm
exclusion; body-injection ignorance; suspended-grant zero-recipients; internal submit-review not a
lifecycle event; denied paths (member/other-org admin/unauth/no-capability/wrong-state/concurrent);
key determinism and vocabulary; the three D8 tests. **VERIFIED — genuine and passing.**

## 27. Regression tests

No isolated regression command was run beyond the full suite (which subsumes `tests/unit/api`,
`tests/unit/services`, `tests/unit/infra`, `tests/unit/engines`, `tests/unit/domain` and `tests/unit`).
Relevant neighbouring suites are all contained in the full run and pass: `test_v3_messaging.py` (8),
`test_v3_notifications.py` (4), `test_p6_1c_engagement_confirmation.py` (27),
`test_p6_2a_*` (32), `test_p6_2b_1/2/3/4` (83), `test_p6_2c_approval_boundary.py` (30),
`test_p6_2d_entitlement.py` (2) + `test_p6_2d_provenance.py` (19), `test_v3_processing_workflow.py` (11),
`test_v3_operations.py` (41). **PASS** (see §28). No regression was observed.

## 28. Full unit suite results (independently observed)

Commands:
* `python -m pytest tests/unit --collect-only -q -p no:cacheprovider` → **1654** collected.
* `python -m pytest tests/unit -p no:cacheprovider --tb=line` → `1654 passed, 1 warning in 264.39s (0:04:24)`, **EXITCODE=0**.

| Metric | Value |
| ------ | ----- |
| Collected | **1654** |
| Passed | **1654** |
| Failed | **0** |
| Errors | **0** |
| Skipped | **0** |
| Exit code | **0** |
| Warnings | 1 (`requests`/`urllib3` dependency warning — environmental) |

**Baseline.** The implementation session reported 1627 before → 1654 after (+27). Independently: the
*focused* delta is verifiably 27 (`test_p6_2e_consultant_lifecycle.py: 27`), and the current count is
**1654** (observed). The "1627 before" figure is **historical** (recorded by the implementation session
and consistent with the P6-2D closure report, which recorded 1,627) and is **not independently
re-derivable** in this session (it would require reverting the new file). Distinction: 1654 = *observed*;
1627 = *historical evidence*; 1627+27 = 1654 = *inferred-and-consistent*.

## 29. Test-defect analysis

The implementation report states three focused-test iterations were required and that all failed
iterations were **test defects**, not production defects. I cannot independently re-derive the
intermediate states (the test file is untracked and there are no commits), so this is a
**LIMITATION**, not a VERIFIED claim. What can be established:

* The **final** test file is internally consistent and passes 27/27 against the production code as-is —
  therefore the production behaviour and the current expectations agree.
* No test was weakened to pass: the negative assertions are *strong* (they assert exact HTTP codes
  **and** `_rows(world) == []`), and the positive assertions check exact event keys **and** exact
  recipient lists.
* Two minor test-quality weaknesses exist and are **not** weakening of correctness (IV-N7):
  (a) the body-injection test targets a route with no body model, making the assertion vacuous;
  (b) two tests accept `status_code in (403, 404)`, slightly looser than a single exact code.
* Nothing is skipped or xfailed. `--collect-only` counts 27; the run reports 27 passed.

**No improperly weakened or skipped test was found.**

## 30. Scope-creep analysis

Confirmed by repository inspection that P6-2E did **not** introduce: new roles; new capabilities; new
permissions; RLS changes; migrations; a consultant `conversation_kind`; a consultant conversation table;
P6-2F UI; browser E2E; Auditor/Assurance; Analytics; Phase 7; Phase 8; billing redesign; P6-2D
remediation; or `confirm`/`retry` provenance. The attributable change set is exactly the 6 files in §6
(2 new source/test files + 4 files carrying 6 marked hunks + 2 docs). **No scope creep. VERIFIED.**

## 31. Documentation / history verification

Required by the prompt:

* `docs/cline/CARBONTALLY_P6_2E_IMPLEMENTATION_REPORT.md` — present.
* `docs/cline/prompt-history/CT-P6-2E-IMPL-20260910-001.md` — present, containing the exact Prompt Ref,
  the complete prompt (Part A, verbatim chunks), the Response Ref (`…-R1`) with datetime, the response
  (Part B), commands/files/findings (Part C), integrity confirmation (Part D), verdict and stop
  condition. **Required implementation-history content present — VERIFIED.**

**Integrity anomaly (see §37).** At the start of this session, the two *outputs this prompt requires —
the IV report and this IV history* — **already existed** as untracked files dated 2026-09-10 21:20 with
mode `0600`, carrying a verdict of `PASS WITH NON-BLOCKING FINDINGS`. That is inconsistent with the
prompt's premise of a fresh, not-yet-performed verification. This session re-derived the verification
independently from primary sources and **overwrote** both paths with its own output. The pre-existing
artefacts were untracked (never committed), so no git history was altered. Their existence and verdict
are recorded here for transparency; the conclusions in *this* report are the verifier's own.

`docs/cline/CARBONTALLY_P6_2E_IMPLEMENTATION_REPORT.md` and the implementation history record were
**read only** — not modified.

## 32. Findings

### BLOCKING
**None.** No violation of a ratified security, tenancy, authorization, lifecycle, idempotency or
architecture invariant was found.

### PO CLARIFICATION
* **IV-C1 — Recipient-matrix divergence (client-org recipients).** The Implementation Contract §7.2
  lists **"client org owner/admin"** for events **1, 3, 4** and **"the responsible processor"** for event 5;
  the P6-2E preflight (§12/§14/§83/§106/§113) repeats the client-org owner/admin requirement. The
  implementation notifies **no** client-org member for any event (firm members only, + internal ops for
  event 2). However the same contract §7.2 and the PO register L580–582 declare the recipient matrix an
  **explicit non-decision to be derived at implementation**, and `PO-PHASE6-D11-20260910` does not
  enumerate recipients. The authoritative documents therefore **conflict** and the implementation is
  self-consistent and disclosed. No leakage; no privilege granted. **Requires PO adjudication** of the
  intended audience. *Do not remediate without a PO decision.*

### NON-BLOCKING
* **IV-N1 — Event 2 internal recipients are staff-admins, not QC operators.**
  `notifications.support_staff_user_ids()` selects internal staff whose role grants `can_manage_staff`. A
  CT-QC operator holding `can_qc` but not `can_manage_staff` receives no QC-intake notice, although the
  contract/preflight describe the recipient as "CarbonTally QC/Ops intake". Authorised-recipient
  *coverage* gap only; no security effect.
* **IV-N2 — Recipient derivation is organisation-grant-scoped, not item-firm-scoped.** Where two firms
  both hold active grants for the same organisation, both are notified about an item one firm worked on
  (`_firm_and_ops` unions all `_engaged_firm_ids(org)`). Not cross-tenant/cross-firm leakage under the
  ratified org-grant authorization model (both firms are already authorised for that org), but broader
  than the "actual workflow relationship" now recorded by P6-2D `consultant_firm_id`.
* **IV-N3 — Recipient hygiene for a deactivated firm profile.** A firm with
  `consultant_profiles.is_active = False` but a retained `active` grant still yields recipients;
  `_engaged_firm_ids` does not re-check the firm profile (only `consultant_clients.status`). The users
  cannot obtain a consultant context, so the rows are inert, but they are persisted.
* **IV-N4 — Alternate-route gaps.** (a) `POST /api/v3/automatic-processing/jobs/{job_id}/review` performs
  a customer decision on the underlying item via `manual_extraction.customer_review(...)` without emitting
  event 4. (b) `POST /consultants/clients/{client_id}/reactivate` sets a grant `active` without emitting
  event 1. Both are **outside the contract's declared D11 trigger set**, both carry their own
  authorization, and automatic processing is staff-only — defensive/informational only.
* **IV-N5 — Per-cycle idempotency limitation.** Keys carry no cycle discriminator, so a second identical
  lifecycle occurrence for the same item is suppressed: a second rework from the same source, a
  resubmission, a second QC round with the same outcome, or a second customer decision with the same
  outcome all produce no new notification. This is the **ratified** deterministic-key idempotency design;
  per-cycle attribution would require durable per-item cycle state, i.e. a schema change the contract
  forbids. Accepted limitation; PO visibility only.
* **IV-N6 — Notification deep-link shape.** Events 2–5 use `link = "/consultant/items/{item_id}"`, whereas
  the frontend consultant item route is `/consultant/items/:clientId/:itemId`
  (`frontend/src/App.js:2169`). The link is therefore not a valid deep link. Presentation-only; the
  P6-2F UI gate owns the consultant surface.
* **IV-N7 — Test-quality weaknesses.** (a) `test_recipients_are_server_derived_and_body_injection_is_ignored`
  posts a JSON body to `consultant-submit`, which declares no body parameter, so the assertion is vacuous
  (the property is nonetheless structurally guaranteed); (b) `test_customer_decision_denied_paths_emit_nothing`
  and `test_no_active_grant_means_no_firm_recipients` accept `in (403, 404)`; (c) the focused suite does not
  cover two active firms on one organisation, the automatic-processing alternate route, or a `can_qc`-only
  internal recipient; (d) there is no database-level (integration) test of the real
  `uq_notifications_event_key` path.
* **IV-N8 — Implementation-report bookkeeping.** The report's "1627 before" baseline and its
  tracked-hunk accounting cannot be re-derived this session (untracked, no commits); the reported
  "porcelain 671 → 673" has since advanced (675 now, because the verification docs themselves are
  untracked). No behavioural impact.

### ENVIRONMENTAL (limitations of this verification)
* **IV-E1 — pytest summary suppression.** `pyproject.toml` sets `addopts = "-q"`; adding a second `-q`
  makes it `-qq`, which suppresses the final "N passed" line. All reported totals here were obtained with
  a single `-q`. Not a defect in P6-2E.
* **IV-E2 — no live database.** No Supabase/PostgreSQL instance was driven. Database-level idempotency,
  uniqueness and RLS were verified by schema/migration/SQL inspection + the in-memory fake, not by an
  integration run.
* **IV-E3 — no live browser/E2E run** (correctly out of P6-2E scope; P6-2F owns E2E acceptance).

## 33. Limitations

1. All API-level evidence is produced on the established in-memory fake harness; the true DB constraint
   path is verified by inspection of the migration and repository SQL, not by an integration run.
2. No live Supabase/RLS enforcement test (IV-E2, §23).
3. No pre-existing committed baseline → the exact P6-2E `git diff` delta and the "1627 before" count
   cannot be independently re-derived (§6, §28).
4. The pre-iteration focused-test history cannot be re-derived (untracked; no commits) — §29.

## 34. Final verdict

> **P6-2E INDEPENDENTLY VERIFIED — PASS WITH NON-BLOCKING FINDINGS**

Rationale: all five ratified D11 lifecycle events are implemented at the correct triggers with
deterministic, server-generated, collision-safe keys; durable idempotent persistence through the existing
`create_idempotent`/`uq_notifications_event_key` mechanism; server-derived, injection-proof recipients;
post-success emission ordering; silent denied paths; replay safety; and no cross-organisation or
cross-firm-tenant leakage. D8 is preserved with zero production change. P6-2D, billing, processing
origins, RLS, schema, roles and permissions are all preserved. The focused suite (27/27) and the full
unit suite (**1654 executed, 0 failed/errored/skipped, exit 0**) pass in the project virtualenv. The
residual issues are one PO clarification (client-org recipient audience, IV-C1) and eight non-blocking
findings; **no blocking defect was found**.

**CP2 status:** P6-2E is **eligible for CP2 closure**. Remediation: **not required** for acceptance;
IV-C1 requires a PO decision (not a code fix) before any recipient change.

## 35. Explicit stop-condition confirmation

Verification **STOPPED at the P6-2E boundary**. No stop condition was triggered:

| Stop condition | Status |
| -------------- | ------ |
| Client-controlled recipients possible | **NOT triggered** — no route accepts recipient/identity input; injection ignored |
| Cross-org notification leakage possible | **NOT triggered** — recipients derived from the item/engagement's own org |
| Cross-firm notification leakage possible | **NOT triggered as leakage** — over-breadth (IV-N2) only among firms already holding active grants for the same org |
| Unauthorized event emission possible | **NOT triggered** — every emit follows a canonical authorization pass |
| Duplicate lifecycle events can materially occur | **NOT triggered** — DB unique index + deterministic keys + state-machine 409 |
| Alternate-route bypass exists | **Observed, non-blocking** — IV-N4; neither is a declared D11 trigger nor crosses an authorization boundary |
| Event identity not deterministic | **NOT triggered** — pure deterministic key builder |
| Event emitted before failed mutation | **NOT triggered** — emit is the final post-success step |
| Migration / RLS / new permission required | **NOT required** — existing schema/index/permissions suffice |
| P6-2E conflicts with Blueprint / PO register | **NOT triggered** — the only divergence is a contract-vs-register recipient nuance (IV-C1), delegated to implementation |
| P6-2D must be reopened | **NOT triggered** — P6-2D artefacts untouched |
| Implementation scope materially expanded | **NOT triggered** — exact 6-file change set |

No remediation was performed. No P6-2F / Phase 7 / Phase 8 work was started.

## 36. Answers to the mandated questions

1. **All five D11 events correctly implemented?** Yes — §8/§9.
2. **Trigger points correct?** Yes — the five contract-declared routes/transitions.
3. **Event keys deterministic and collision-safe?** Yes — §10.
4. **Recipients fully server-derived?** Yes — §11/§12/§13.
5. **Can client input manipulate recipients or event identity?** No — §12.
6. **Cross-org and cross-firm notifications prevented?** Cross-org: yes. Cross-firm (unrelated firm): yes. Two firms *both* holding active grants for the same org are both notified (IV-N2) — not leakage, but broader than item-firm provenance.
7. **Do denied operations emit zero events?** Yes — §15.
8. **Can replay create duplicates?** No — §16.
9. **Can alternate routes bypass lifecycle emission?** Not within the declared trigger set; two out-of-set gaps (IV-N4).
10. **Is emission ordering safe?** Yes — mutate → audit → emit; no emit-before-failure path (§19), though not transactional (§20).
11. **Is best-effort persistence acceptable?** Acceptable under the authoritative contract, which mandates idempotent keys/recipients/no-leakage and preserves the existing best-effort emitter; recorded with PO visibility (§20).
12. **Is the rework-cycle limitation acceptable?** Acceptable as designed; per-cycle state would need a forbidden migration (IV-N5). PO visibility only.
13. **Is customer rejection correctly modelled without a rework event?** See §36 discussion below.
14. **Did P6-2E preserve D8?** Yes — §7.
15. **Did P6-2E preserve P6-2D?** Yes — §25.
16. **Any roles/capabilities/permissions/RLS/schema changes?** None — §7, §22, §23, §30.
17. **Are the tests sufficient and genuinely passing?** Genuine and passing (27/27, full suite 1654/0); sufficient for acceptance with the coverage gaps in IV-N7.
18. **Any blocking defects?** None.

### Customer rejection vs rework (prompt §12)
The ratified workflow routes a customer **rejection** back to `mapping` (a rework transition), but the
ratified **event vocabulary** names `rework` for the quality-gate returns (CT-QC rejection; consultant
review rejection) and `customer_decision` for the client's approve/reject. The implementation emits
`customer_decision:approved|rejected` and **no** client-rejection `rework` event. This is internally
consistent and matches the contract's emit-point table (§7.2 maps event 5 to "QC-reject / rework
transition", and the preflight lists event-5 triggers as `ct_qc_rejected` + the consultant-review rework
path). It is therefore **not** classified as a defect; the modelling is reasonable, though the PO may
wish to confirm whether a client-driven rework should *also* raise a `rework` notification (grouped with
IV-C1 for PO visibility). No behaviour was invented; no remediation performed.

## 37. Repository integrity & verdict confirmation

* Branch `main`; HEAD `1639121` (unchanged); **no commit, no push, no stage, no reset, no clean**.
* Pre-existing dirty tree: 284 ` M`, 152 ` D`, 239 `??` (675 porcelain entries) — dominated by earlier
  gates, not attributable to P6-2E or this session.
* Files created by **this** verification session (only these two): this report and
  `docs/cline/prompt-history/CT-P6-2E-IV-20260910-001.md`.
* **Integrity anomaly:** the two outputs this prompt requires pre-existed (untracked, dated 21:20, mode
  `0600`, verdict `PASS WITH NON-BLOCKING FINDINGS`). This session re-derived the verification
  independently and replaced both. No tracked file or git history was altered.
* No production code, test, migration, schema, RLS, frontend or configuration was modified; no defect
  was fixed; no remediation performed.

**Declaration:** verification is complete. The final verdict is
`P6-2E INDEPENDENTLY VERIFIED — PASS WITH NON-BLOCKING FINDINGS`. Verification stopped at the P6-2E
boundary; P6-2E is eligible for CP2 closure and the next authorised gate. No roadmap advancement was
performed.

