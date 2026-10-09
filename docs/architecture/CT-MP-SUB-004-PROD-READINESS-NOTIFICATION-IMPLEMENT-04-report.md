# CT-MP-SUB-004 — PROD-READINESS NOTIFICATION IMPLEMENT 04
## Manual Processing lifecycle notifications (N1–N4) — implementation + self-verification

| Field | Value |
| --- | --- |
| **Document ID** | `CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-IMPLEMENT-04` |
| **Task ID** | `CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-IMPLEMENT-04` |
| **Date** | **2026-10-05** |
| **Decision authority** | **Product Owner**, CarbonTally (authorization stated in the task directive; N1–N4 AUTHORIZED, client notification NOT AUTHORIZED) |
| **Implemented by** | Cline (implementation agent) |
| **Governing documents read in full** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md`; `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-POLICY-FACTFIND-03-report.md`; `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` (P-1/P-2) |
| **Repository HEAD at start and end** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (branch `p8-release-reconciled`) |
| **Status** | **IMPLEMENTED AND SELF-VERIFIED — READY FOR INDEPENDENT VERIFICATION** |
| **Type** | Application implementation (backend) + tests + this report. **No commit, no push, no deploy, no production access, no migration.** |

---

## §1 Task identity and authorization

This task implements the PO-authorised **Manual Processing lifecycle
notification set N1–N4** on top of the existing CarbonTally notification
architecture.

**Authorized (implemented here):**

| # | Event | Recipient | Channel |
| --- | --- | --- | --- |
| **N1** | MP work assigned/routed to a Processing Entity | the assigned PE's **active staff** | in-app (mandatory) |
| **N2** | MP item/batch assigned to a specific CarbonTally internal validator | **that validator** | in-app (mandatory) |
| **N3** | a document/batch **enters** Manual Processing | the **responsible consultant** for the affected client | in-app (mandatory) |
| **N4** | MP reaches its **terminal validated state** | the **original uploader** | in-app (mandatory) |

**Explicitly NOT authorized (and not implemented):**

* any notification to a **client organisation** user for the MP lifecycle;
* reuse of the automatic-processing `processing.completed` notification;
* **email** for N1–N4 (and no change to X2 email alerting);
* any **notification preference** system — no `notification_preferences`,
  `user_notification_preferences`, `organization_notification_settings`,
  notification feature flag, event-level toggle or Admin off-switch;
* any change to **coverage allocation/release** behaviour (audit-only).

**Method.** Existing-first: read the governing reports, inspected the current
source, then reused the established producer convention
(`services/consultant_lifecycle.py`, `services/work_items.py`) rather than
inventing a subsystem. No schema, RLS, migration, API-contract or frontend
change was required or made.

---

## §2 PO decisions implemented

| PO rule | Where it is enforced | Status |
| --- | --- | --- |
| N1 authoritative; PE staff notified; no email; no opt-out; no off-switch | `services/manual_processing_routing.py`, `services/work_items.py`, `api/v3_operations.py` → `services/manual_processing_notifications.py::notify_pe_item_assignment` / `notify_pe_batch_assignment` | IMPLEMENTED + TESTED |
| N2 authoritative; reuse `work_item.assigned` at item level; no duplicates | pre-existing producer in `services/work_items.py` reused unchanged; batch level added via `notify_validator_batch_assignment` | IMPLEMENTED + TESTED (item level pre-existing) |
| N3 authoritative; ONE responsible consultant resolved server-side; **never** a broadcast; fail-safe + escalation when not determinable | `notify_manual_processing_entry` + `resolve_responsible_consultant` | IMPLEMENTED + TESTED |
| N4 authoritative; only the true terminal validated state; durable uploader provenance; no false "finished" | `api/v3_operations.py::ct_qc_decision_endpoint` → `notify_manual_processing_completion` + `resolve_uploader` | IMPLEMENTED + TESTED |
| Client notification NOT authorised | no producer targets `organization_members` for MP; asserted by tests | IMPLEMENTED + TESTED |
| Coverage allocation/release unchanged (audit-only) | producer module contains no coverage/allocation vocabulary; `TestNV10NotificationBehaviour` stays green | PRESERVED + TESTED |
| No preference/opt-out/flag mechanism | none created; the producer reads no configuration | IMPLEMENTED + TESTED |
| In-app only; `notification_delivery.channel` unchanged | `_emit` calls `notifications.create_idempotent` only | IMPLEMENTED + TESTED |
| Server-derived recipients only; caller cannot choose recipient or event key | producers take no recipient/key inputs; negative tests | IMPLEMENTED + TESTED |
| Idempotency via `(recipient_id, event_key)` | deterministic keys; database unique index unchanged | IMPLEMENTED + TESTED |
| Assignment remains authoritative; notification failure must not roll back | producers are best-effort; failure-injection test | IMPLEMENTED + TESTED |

---

## §3 Existing architecture reused

| Layer | Reused artefact | Change |
| --- | --- | --- |
| Durable store | `public.notifications` via `NotificationsRepository.create_idempotent` (`backend/data/notifications.py:116`) | none |
| Idempotency | `uq_notifications_event_key` — `UNIQUE (recipient_id, event_key) WHERE event_key IS NOT NULL` | none |
| Retrieval | `GET /api/v3/notifications` (`backend/api/v3_notifications.py`) — recipient-scoped | none |
| Inbox UI | `frontend/src/v3/NotificationsPage.jsx`, `frontend/src/v3/pe/PeNotificationsBell.jsx` | none |
| PE recipient roster | `staff.list_entity_staff(entity_id)` (`backend/data/staff.py:91`) | read-only reuse |
| Consultant relationship model | `consultants.list_active_client_grants` / `list_firm_members` / `get_profile_by_id` | read-only reuse |
| Uploader provenance | `organization_files.uploaded_by` reached from `manual_extraction_items.file_id` | read-only reuse |
| Audit | existing append-only `audit_trail` via `repos.audit.record` | none |
| Producer convention | best-effort / logged / never fatal (`work_items.py`, `consultant_lifecycle.py`) | followed |

**Not used / not created:** no new table, no new column, no new RLS policy, no
new API route, no new provider, no Realtime dependency, no event bus, no email
provider call.

---

## §4 N1 implementation

**New producer** — `backend/services/manual_processing_notifications.py`:

```
notify_pe_item_assignment(repos, *, item_id, entity_id, assignment_id=None,
                          actor_domain="internal_staff")
notify_pe_batch_assignment(repos, *, batch_id, entity_id,
                           actor_domain="internal_staff")
```

Recipients: `pe_staff_recipients(repos, entity_id)` →
`staff.list_entity_staff(entity_id)`, keeping only active profiles with a
`user_id`; sorted and de-duplicated. Only the ASSIGNED entity is queried, so
other entities and all internal staff are excluded by construction.

**Call sites (traced from the automatic-fallback routing path and the D38
ledger):**

| Path | File | Behaviour |
| --- | --- | --- |
| Automatic fallback routing → configured PE | `backend/services/manual_processing_routing.py` (`route_failed_job`) | after `work_item_open(...)` + the `manual_processing:auto_routed` audit row (already committed), N1 fires with the new assignment-row id. On the router's idempotent branch N1 is re-attempted with the OPEN row's id, so a worker retry **heals** a failed delivery but can never duplicate it. |
| Item-level D38 assignment to a PE (ops assign / reassign / recover) | `backend/services/work_items.py` (`ops_assign_item`, PE branch) | previously notified **nobody** (the ledger shape constraint forces `assigned_to IS NULL` for a PE assignment, so the pre-existing internal-staff guard was false for every PE assignment). |
| Batch-level D22 assignment to a PE | `backend/api/v3_operations.py` (`assign_batch`) | previously notified nobody. |

**Not the source of truth.** The D38 `work_item_assignments` ledger is
unchanged and authoritative; `_emit` swallows and logs every failure, so a
notification outage cannot reverse or invalidate an assignment
(`test_assignment_survives_a_notification_failure`).

**Duplicate routing.** The event key carries the assignment-row identity, so a
re-route that creates no new ledger row (the router is idempotent by
construction, and `ops_assign_item` returns early without writing when the
target is already current) produces **no** second notification, while a genuine
reassignment to a different entity does.

---

## §5 N2 implementation

**Traced validation-assignment paths** (`work_item.assigned` distinction
verified against the actual workflow semantics):

| Event | Code path | Notification |
| --- | --- | --- |
| Internal validator assignment (item level, D38) | `work_items.ops_assign_item(target_user_id=…)` → `_notify_assignee` | **pre-existing** `work_item.assigned`, reused unchanged (`assigned_to is not None and assigned_to != actor_user_id`) |
| Internal validator assignment (batch level, D22) | `api/v3_operations.py::assign_batch` (`assigned_to`) | **NEW** `manual_processing.validator_assigned` via `notify_validator_batch_assignment` — previously notified nobody |
| PE assignment | `ops_assign_item(target_entity_id=…)`, `manual_processing_routing` | N1 (`manual_processing.pe_assigned`); **never** `work_item.assigned` |
| Self-claim | `ops_claim_item` → `ops_assign_item(action="claim")` | **no notification** (claimant == actor). Preserved. |
| Release | `ops_release_item`, `pe_release_item` | **no notification**. Preserved. |
| Completion (work item) | `ops_complete_item`, `pe_complete_item` | **no notification**. Preserved. |

No duplicate is produced: the item-level event keeps the single existing
producer and key (`work_item:{action}:{item_id}:{assignment_row_id}`), and the
batch-level event is a different event class with its own key
(`manual_processing.validator_assigned:batch:{batch_id}:{user_id}`).

---

## §6 N3 implementation

**MP entry boundaries implemented** (the two server-side paths by which a
document/batch actually *enters* Manual Processing):

1. **Automatic fallback routing** — `manual_processing_routing.route_failed_job`
   (the item that failed the automatic pipeline is routed into Manual
   Processing). Key: `manual_processing.entered:item:{item_id}`.
2. **Explicit governed MP batch creation** —
   `api/v3_manual_extraction.create_batch` (`POST
   /api/v3/manual-extraction/batches`, `require_org_admin()` + FIN-06
   `ensure_manual_processing_allowed`). Key:
   `manual_processing.entered:batch:{batch_id}`.

**Deliberately NOT an entry event** (documented boundary): uploading a document
(the shared-ingestion carrier is explicitly *not* MP work), and later
assignment/reassignment of already-entered work (N1/N2 territory). This keeps
the consultant from being notified repeatedly for one entry event.

**Recipient rule (server-derived, single, never a broadcast):**
`resolve_responsible_consultant(repos, organization_id=…, item=…)`:

1. the item's durable D7 consultant-firm provenance (`consultant_firm_id`) —
   used only when that firm still holds an ACTIVE client grant;
2. otherwise the **sole** ACTIVE `consultant_clients` relationship for the
   organisation;
3. inside that firm, exactly **one** consultant:
   a. the active firm member recorded as the creator of the client
      relationship (`consultant_clients.created_by`);
   b. otherwise the firm's principal consultant (`consultant_profiles.user_id`);
   c. only accepted when the candidate is an ACTIVE member of that firm.

**Fail-safe (PO rule).** Anything else returns `None`:

| Situation | Outcome |
| --- | --- |
| no consultant relationship (direct customer) | no notification, **no** escalation (normal state) |
| multiple ACTIVE relationships and no item provenance | no notification + audit `manual_processing:consultant_notification_unresolved` (`reason=multiple_consultant_relationships`) |
| provenance firm whose relationship ended / unrecordable firm / no resolvable active member | no notification + the same audit action with the precise reason |

The ambiguity is recorded in the **existing append-only audit trail** (the
"safest existing workflow/audit path"), never guessed and never broadcast. It is
flagged in §19 for PO review.

**Explicitly not notified:** other firm members, `can_manage_clients` members,
the client organisation, unrelated CarbonTally staff, and the uploader *unless*
the uploader is the resolved responsible consultant.

---

## §7 N4 implementation

**Terminal state identification (traced, not invented).** The current MP state
machine converges on exactly one terminal *validated* state:

```
automatic→manual entry → … → calculated
   internal path : calculated → reviewed            → (CT-QC) → ct_qc_approved | ct_qc_rejected
   PE path       : calculated → pe_review → pe_reviewed → pe_qc_approved → (CT-QC) → ct_qc_approved | ct_qc_rejected
   downstream    : ct_qc_approved → customer_review → approved | rejected
```

* The **late CarbonTally CT-QC gate is mandatory for manually processed work**
  (`api/processing_mode.py` P1 containment: manual work must pass CT-QC before
  customer review/approval; `pe_qc_approved` explicitly "NEVER grants
  CarbonTally QC authority" — `api/v3_pe.py`).
* `ct_qc_approved` is written in **exactly one place**:
  `ManualExtractionRepository.ct_qc_decision` (`data/manual_extraction.py`),
  called only from `POST /api/v3/ops/qc/items/{item_id}/decision`
  (`api/v3_operations.py::ct_qc_decision_endpoint`).

**Therefore N4 is emitted only there, and only when `approved is True`**, i.e.
only when the required validation/review is genuinely complete. PE review, PE
QC approval, PE release, intermediate stage transitions and closed work-item
assignments emit nothing.

**Recipient** — `resolve_uploader(repos, item)`:
`manual_extraction_items.file_id` → `organization_files.uploaded_by` (the
authoritative equivalent for the actual ingestion path
`api/v3_documents.create_document_and_enqueue`, which writes
`file_id=document_id` and `uploaded_by=<authenticated actor>`, including the
consultant upload path). Never derived from the current assignee, PE, validator,
organisation owner or firm owner; never rewritten by reassignment.

**Link safety (per recipient, server-resolved):** the recipient is linked to a
route they already have access to —
`/consultant` when the uploader is an active consultant firm member, otherwise
`/processing/{item_id}` (organisation processing-item page). No recipient is
given access they otherwise lack.

---

## §8 Recipient-resolution rules

| Event | Resolver | Recipient set | Explicit exclusions |
| --- | --- | --- | --- |
| N1 | `pe_staff_recipients` | active `staff_profiles.entity_id = <assigned entity>` | other entities; internal staff; inactive staff; staff without a user id |
| N2 | the D22/D38 assignee column (`assigned_to`) | that one internal staff user | self-assignment; PE targets; everyone else |
| N3 | `resolve_responsible_consultant` | ONE consultant (relationship owner → firm principal), verified active firm member | other firm members; `can_manage_clients` members; the client organisation; internal staff; unrelated firms; the uploader as such |
| N4 | `resolve_uploader` | ONE user: `organization_files.uploaded_by` | client org users; current PE/validator/assignee; org owner; firm owner |

No resolver has a request-derived input. No resolver returns a group.

---

## §9 Event keys and idempotency

All keys are built server-side from stable business identity (no randomness, no
timestamps, no caller input):

| Event | Key |
| --- | --- |
| N1 item | `manual_processing.pe_assigned:item:{item_id}:{assignment_row_id}` (falls back to `:entity:{entity_id}` if no row id is available) |
| N1 batch | `manual_processing.pe_assigned:batch:{batch_id}:{entity_id}` |
| N2 batch | `manual_processing.validator_assigned:batch:{batch_id}:{user_id}` |
| N2 item | pre-existing `work_item:{action}:{item_id}:{assignment_row_id}` (unchanged) |
| N3 item | `manual_processing.entered:item:{item_id}` |
| N3 batch | `manual_processing.entered:batch:{batch_id}` |
| N4 | `manual_processing.completed:item:{item_id}` |

The final idempotency boundary is the existing database constraint
`uq_notifications_event_key` on `(recipient_id, event_key)` — unchanged. The
producer functions accept **no** `recipient_id`, `event_key` or
`notification_target` parameter, and the API surfaces do not expose one
(`test_the_producer_entry_points_accept_no_recipient_or_event_key`,
`test_a_forged_recipient_in_an_api_body_is_never_used`).

Per-recipient semantics: same event + same recipient → one row; same event +
several authorised recipients → one row each.

---

## §10 Security / authorization verification

| Threat | Control | Test |
| --- | --- | --- |
| caller chooses a recipient | producers take no recipient input; the API body cannot nominate one | `test_the_producer_entry_points_accept_no_recipient_or_event_key`, `test_a_forged_recipient_in_an_api_body_is_never_used` |
| caller forges an event key | key generated server-side only; the unique index is the boundary | `test_the_event_key_unique_constraint_semantics_are_mirrored` |
| cross-tenant consultant notified | N3 uses the client organisation's own grants | `test_a_cross_tenant_consultant_is_not_notified_for_another_client` |
| unrelated consultant notified | N1/N3 resolvers never touch other firms | `test_an_unrelated_consultant_is_not_notified_by_a_pe_assignment` |
| unrelated Processing Entity notified | N1 queries only the assigned entity | `test_an_unrelated_processing_entity_is_not_notified` |
| client organisation notified (N3/N4) | no producer targets `organization_members` | `test_a_client_organisation_user_is_never_the_completion_recipient` |
| unrelated internal staff notified | N1 excludes internal staff; N2 targets one assignee | `test_internal_staff_are_never_n1_recipients`, `test_an_unrelated_internal_staff_member_is_not_notified` |
| wrong validator notified | N2 targets exactly the assignee | `test_the_wrong_validator_does_not_receive_it` |
| wrong uploader notified | N4 reads durable uploader provenance only | `test_a_wrong_uploader_is_not_treated_as_the_uploader` |
| a user reading another user's inbox | API is server-scoped to `current_user.user_id` | `test_another_user_cannot_see_the_uploaders_notification` |
| notification becomes an access-control mechanism | links are role-resolved and only bind to existing routes | §7, §11 |

Every case above is a **DENY** assertion in the suite; the corresponding ALLOW
case is asserted for each event class. Extra fields in a request body are never
used to derive a recipient.

---

## §11 Realtime / API delivery behaviour

* **Durable row = source of truth.** Delivery is the existing
  `public.notifications` row created by `NotificationsRepository.create_idempotent`.
* **`GET /api/v3/notifications` is the authoritative retrieval path** (bounded
  `limit` 1..500, newest-first, server-scoped to the caller). Verified by
  `test_a_recipient_can_retrieve_the_notification_through_the_api`.
* **Realtime stays best-effort.** No RLS policy was created or weakened, no
  publication change was made, and no assignment depends on Realtime.
  `public.notifications` remains RLS fail-closed with zero policies (CT-FINAL-03
  posture preserved).
* **No transactional dependency.** Producers run after the business mutation is
  committed; failures are logged, never raised.
* **Pre-existing Realtime defect — reported, NOT fixed** (see §19): the V3 shell
  and legacy admin subscriptions filter `notifications` on a non-existent
  `user_id` column instead of `recipient_id`. The inbox is nevertheless correct
  because it reads the API (including the window-focus refetch). Fixing it is a
  separate, unrelated Realtime/RLS task and was deliberately not expanded into
  this one.
* **No frontend change was required.** `frontend/src/v3/NotificationsPage.jsx`
  renders `notification.title` (set by every new event) and does **not** filter
  by type; `PeNotificationsBell.jsx` pulls the same endpoint. Both therefore
  display N1–N4 without a UI change (`TYPE_LABELS` only affects an optional
  caption).

---

## §12 Email exclusion

* `_emit` calls **only** `notifications.create_idempotent`: it never calls
  `record_delivery`, `email_for_user`, a mailer, or the X2 operational-alerting
  service. Asserted by source inspection
  (`test_the_producer_module_has_no_email_or_delivery_path`).
* `notification_delivery.channel` and the schema are **unchanged**.
* No email setting, consent or preference work was added.
* X2 operational alerting (`services/operational_alerting.py`) is untouched —
  still the only two-channel path.

---

## §13 Coverage allocation/release separation

The PO decision "allocation/release remain audit-only" is unchanged and provably
separate:

* the new producer module contains **no** allocation/release/coverage vocabulary
  (`test_the_producer_module_contains_no_allocation_or_release_vocabulary`);
* routing — which reads coverage/allocation state — emits only
  `manual_processing.*` events, never an allocation event
  (`test_routing_never_produces_a_coverage_notification`);
* `TestNV10NotificationBehaviour` (the live regression rail asserting that
  allocate/release write an audit row and **no** notification) remains green
  (§15).

---

## §14 Tests

New suite: `backend/tests/unit/api/test_ct_mp_sub_004_notification_implement_04.py`
(60 tests, in-memory fakes only — no database touched).

| Class | Tests | Covers |
| --- | --- | --- |
| `TestN1PeAssignment` | 9 | routing → PE staff; inactive excluded; unrelated PE denied; internal staff denied; duplicate routing not duplicated; ops item assignment; repeat assignment; notification-failure resilience; batch assignment |
| `TestN2ValidatorAssignment` | 8 | `work_item.assigned` to the assignee; wrong validator denied; self-claim silent; duplicate silent; PE assignment never `work_item.assigned`; batch validator assignment; self batch assignment silent; PE never notified of an internal assignment |
| `TestN3ConsultantEntry` | 8 | relationship owner; firm principal fallback; other members denied; item provenance wins; multiple relationships fail-safe + audited; no relationship → silent; explicit batch creation; idempotent |
| `TestN4Completion` | 10 | CT-QC approval → uploader; consultant link; org link; rejection silent; reassignment does not change uploader; PE completion silent; PE QC approval silent; no file link silent; duplicate decision no duplicate; client never recipient |
| `TestEventKeysAndResolvers` | 10 | key determinism/namespacing; per-assignment key movement; PE roster scoping; missing entity; consultant resolver fail-safes; uploader resolver; API retrieval; inbox isolation |
| `TestSecurityNegatives` | 6 | cross-tenant consultant; unrelated consultant; unrelated internal staff; wrong uploader; forged producer fields; forged API body fields |
| `TestIdempotency` | 4 | same event+recipient → 1; same event+N recipients → N; unique-constraint semantics; per-recipient rows |
| `TestChannelAndCoverageSeparation` | 5 | no email/delivery code path; every row in-app + actor-domained + keyed; no allocation vocabulary; routing emits no coverage event; blocked route emits nothing |

**Exact counts (this file):**

```
N1 tests:        9/9
N2 tests:        8/8
N3 tests:        8/8
N4 tests:        10/10
Idempotency:     4/4
Security:        6/6
Keys/resolvers:  10/10
Channel/coverage: 5/5
File total:      60/60 PASS
```

**Fake extensions made by this task** (test infrastructure only, 5 lines):
`MemoryManualExtraction.seed_item(..., file_id=...)` and
`MemoryConsultants.seed_client(..., created_by=...)` so the D33 item→document
link and the relationship-creator rule can be seeded exactly as production
stores them.

---

## §15 Regression results

| Suite | Result |
| --- | --- |
| `test_ct_mp_sub_004_prod_readiness.py` (incl. `TestNV10NotificationBehaviour`) | PASS — allocation/release still write an audit row and **no** notification |
| `test_manual_processing_routing.py` | PASS — routing/entitlement/governance semantics unchanged |
| `test_v3_operations.py`, `test_v3_entity_extraction.py`, `test_operations_auth.py`, `test_v3_work_item_effective_assignment.py` | PASS — D38/D22 assignment behaviour preserved |
| `test_p6_2b_3_ct_qc_decision.py`, `test_p6_2e_consultant_lifecycle.py`, `test_v3_qc.py` | PASS — CT-QC boundary and D11 lifecycle untouched |
| `test_v3_notifications.py` | PASS — notification API contract unchanged |
| Consolidated notification/assignment rail (15 files incl. this task's suite, `pytest -q`) | PASS — **364 tests, 0 failed** |
| Full backend suite (`pytest`, `tests/unit` + `tests/integration`) | 5279 passed, 124 failed, 174 skipped — **0 failures attributable to this task** (see §15.1 / §15.2) |

### §15.1 Full-suite result

Run (repo root; backend virtualenv; no services required):

```
cd backend && python -m pytest -q        # tests/unit + tests/integration
```

Result (one complete run, 588.32 s):

```
124 failed, 5279 passed, 174 skipped, 17 warnings in 588.32s (0:09:48)
FAILED lines naming a notification test: 0
```

Notification / assignment rail re-run in isolation — 15 files (this task's
60-test suite plus every adjacent notification, routing, assignment, CT-QC and
consultant-coverage file):

```
0 failed, 0 errors      (364 tests: progress line = 364 symbols, all '.')
```

`backend/pyproject.toml` suppresses pytest's final count line, so the pass
figure is read from the progress line (5 × 72 + 4 = 364) together with zero
`F`/`E` markers and zero `FAILED` lines.

### §15.2 Failure classification

See the table below. Every one of the 124 failures was classified against a
**pristine `git worktree` of HEAD `375a48d`** (a clean checkout of the committed
tree, no working-tree modifications, no `backend/.env`), which separates
failures caused by this session's working tree from failures that already exist
at HEAD.

| Class | Count | Caused by this task? | Evidence |
| --- | --- | --- | --- |
| Notification / this task's code | **0** | — | `grep -i notif` over all `FAILED` lines → no match; zero failures reference `manual_processing_notifications`, `notify_pe_item_assignment`, `notify_validator_batch_assignment`, `notify_manual_processing_entry`, `notify_manual_processing_completion` or `notifications.create_idempotent`; the 60 new tests and the whole 364-test rail pass |
| Pre-existing unit tests — migration-baseline expectations | **4** | no | `test_p17_migrations::test_p17_does_not_reuse_or_edit_a_historical_timestamp`, `test_i1_insight_migration::test_i1_migration_is_the_latest_migration`, `test_i2_insight_authorization_contracts::test_i2_migration_is_the_latest_and_scoped_to_one_policy`, `test_d17_provider_ownership_migration_revision::TestRevisionScope::test_migration_ordering_is_unchanged` — the **same four test ids fail in the pristine-HEAD worktree**. They assert "latest migration" invariants that later migration files violate (`20261029000000_ct_final_03_staff_workload_rls.sql` — mtime 2026-10-02; `20261030000000_manual_processing_routing.sql` — 2026-10-04; `20261101000000_ct_mp_sub_003_consultant_coverage.sql` — 2026-10-04), none of which this task authored — it created **no migration file at all** (§17) |
| Pre-existing unit tests — extraction suggestions | **3** | no | `tests/unit/engines/test_extraction_suggestions.py` (date normalisation, missing-field/garbage evidence) — **same three test ids fail in the pristine-HEAD worktree**; the test file and the engine (`backend/services/extraction_suggestions.py`, mtime 2026-09-24) are unmodified, and no module this task touched is on their path |
| Environment-dependent unit test — mail credential in `.env` | **1** | no | `test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` **passes in the pristine-HEAD worktree** and fails only in this working environment: `backend/.env` supplies `RESEND_API_KEY` / `SMTP_*`, `backend/config.py` calls `load_dotenv()` at import, so the platform default provider counts as *configured* and `send_transactional_email` returns `delivered=True`, whereas the test asserts an environment where email is not configured. Unrelated to N1–N4, which never invoke the mailer (§12) |
| Live-database integration tests | **116** | no | all under `tests/integration/`; the local PostgreSQL is reachable but its schema/data predate the committed migrations: `asyncpg.UndefinedColumnError: column "actor_organization_id" of relation "audit_trail" does not exist`; missing indexes/constraints (`report_versions_one_current_per_report`, `disclosure_requirement_versions_capability_check`, `activity_clarifications_context_unique`); missing reference data (`expected 7049 total factors, got 30`); and one environment guard failing because the suite is pointed at `carbontally_test` (`assert 'carbontally_test' not in ('carbontally_test', …)`). No notification surface is involved in any of them |
| **Total** | **124** | **0 attributable to this task** | |

Conclusion: **this task introduced no regression.** The 124 failures are
pre-existing unit expectations (7), one environment/credential condition (1) and
116 live-DB schema/data-drift integration failures; each was reproduced or
explained independently of this task's diff, which is confined to one new
service, three hook sites, one new test file and additive test-fake parameters
(§16).

---

## §16 Files changed

| File | Change | Lines |
| --- | --- | --- |
| `backend/services/manual_processing_notifications.py` | **NEW** — the single producer for N1–N4: vocabulary, deterministic event keys, recipient resolvers, best-effort `_emit`, ambiguity audit | 668 (new) |
| `backend/services/manual_processing_routing.py` *(untracked at HEAD)* | N1 on both the create and idempotent route paths (`:329`, `:405`); N3 on the create path (`:415`); import `:53–56` | +~30 |
| `backend/services/work_items.py` | N1 in the PE branch of `ops_assign_item` (`:222–232`); import `:24` | +12 |
| `backend/api/v3_operations.py` | N4 at the CT-QC approval (`:2203–2212`); N1/N2 in `assign_batch` (`:2321–2341`); import `:86–90` | +35 |
| `backend/api/v3_manual_extraction.py` | N3 at explicit MP batch creation (`:67–75`); import `:19` | +12/−2 |
| `backend/tests/unit/api/test_ct_mp_sub_004_notification_implement_04.py` | **NEW** — 60 tests | 949 (new) |
| `backend/tests/unit/api/fakes.py` | 5 lines of test-fake seeding support (`seed_item(file_id=…)`, `seed_client(created_by=…)`) | +5 (mine) |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-IMPLEMENT-04-report.md` | **NEW** — this report | new |

> **Working-tree disclosure.** `backend/tests/unit/api/fakes.py` was **already
> modified** in the working tree before this task started (450 insertions /
> 7 deletions at HEAD-relative diff, of which only **5 insertion lines** are
> mine). The other pre-existing uncommitted modifications present at session
> start (`backend/api/router.py`, `backend/data/manual_processing.py`,
> `backend/domain/manual_processing.py`, `backend/workers/automatic_processing.py`,
> several test files, frontend files, `tools/demo_lab/*`) were **not touched** by
> this task. Nothing was reverted, staged or committed.

**No production, migration, schema, RLS, API-contract, seed, fixture, credential
or frontend file was modified.**

---

## §17 Migration / schema impact

**None.** The fact-find's conclusion is confirmed by implementation:

* `public.notifications`, `notification_delivery`, `event_key`, `actor_domain`
  and `uq_notifications_event_key` are used exactly as they exist.
* No new table, column, index, constraint, trigger, policy or publication
  change; **no migration file was created**.
* `notification_type` is an existing free-form `VARCHAR`; the new values
  (`manual_processing.pe_assigned`, `manual_processing.validator_assigned`,
  `manual_processing.entered`, `manual_processing.completed`) require no DDL.
* `notification_delivery.channel` is unchanged (no delivery row is written).

---

## §18 Production safety

| Requirement | Status |
| --- | --- |
| No production deployment | honoured |
| No production migration / DB mutation / Supabase change | honoured |
| No commit / push / release | honoured (HEAD still `375a48dc…`; 0 staged) |
| No credential change | honoured |
| Investor/demo dataset untouched | honoured (no reseed, no mutation) |
| Demo Lab not required | verification is in-memory/unit; no local stack was started, stopped or restarted |
| Secrets in code/logs | none introduced; no signed URLs, tokens or credentials logged or stored |

Runtime: the default local stack was **not** disturbed. The new tests need no
running services (`:3000` not required; `:3100` never introduced).

---

## §19 Known limitations / deferred issues

1. **N3 attribution ambiguity (PO review requested).** The schema records the
   consultant **firm** durably on the item (`consultant_firm_id`) and the
   *person* who created each client relationship (`consultant_clients.created_by`),
   but there is no first-class "responsible consultant" column, and the firm
   principal (`consultant_profiles.user_id`) is the only other deterministic
   person. This implementation resolves, in order: relationship creator → firm
   principal, always requiring an ACTIVE firm member. Where the model genuinely
   cannot name one person (multiple ACTIVE firms for the same client with no
   item-level provenance), the event is **withheld** and recorded as
   `manual_processing:consultant_notification_unresolved`. If the PO wants a
   different responsible party (e.g. an explicit "account consultant" field, or
   the item uploader), that is a **product-model decision** requiring its own
   authorization — it is not an implementation choice.
2. **N4 depends on the D33 item→document link.** Items created through
   `POST /api/v3/manual-extraction/batches/{id}/items` currently carry no
   `file_id`, so no uploader can be resolved for them (the event is withheld, not
   guessed). All upload-path items (`api/v3_documents.create_document_and_enqueue`,
   used by both org-member and consultant uploads) do carry it. Recorded, not
   fixed.
3. **Pre-existing Realtime filter defect (NOT fixed here).** The V3 shell and the
   legacy admin subscribe to `notifications` with `filter: user_id=eq…` while the
   table's recipient column is `recipient_id`; and `public.notifications` is RLS
   fail-closed with zero policies. The API refetch is the deterministic path, so
   recipients still see N1–N4 (§11). Fixing Realtime is a separate RLS/Realtime
   task and was explicitly out of scope.
4. **No preference / opt-out UI or API** — intentional (PO decision). If an
   off-switch is ever authorised it belongs in the Admin control plane and needs
   its own task.
5. **Not tested (disclosed, out of scope):** live-DB integration of the new
   producers against a real PostgreSQL/Supabase instance; Supabase Realtime
   delivery; the Demo Lab end-to-end journey; email delivery for N1–N4 (there is
   none by design).
6. **`backend/services/manual_processing_routing.py` is untracked at HEAD**, so it
   does not appear in `git diff`; its contents (including the N1/N3 hooks) are
   part of the working tree reviewed here.

---

## §20 Final status

| Aspect | Status |
| --- | --- |
| N1 | **IMPLEMENTED + SELF-VERIFIED** (9/9) |
| N2 | **IMPLEMENTED + SELF-VERIFIED** (8/8; item-level producer pre-existing, reused) |
| N3 | **IMPLEMENTED + SELF-VERIFIED** (8/8) |
| N4 | **IMPLEMENTED + SELF-VERIFIED** (10/10) |
| Client notification | **NOT IMPLEMENTED** (per PO decision) |
| Email | **NOT IMPLEMENTED** (per PO decision; X2 untouched) |
| Preference/opt-out/off-switch | **NOT IMPLEMENTED** (per PO decision) |
| Coverage allocation/release | **UNCHANGED — audit-only** (`TestNV10NotificationBehaviour` green) |
| Migration / schema / RLS | **NONE REQUIRED, NONE MADE** |
| Full-suite regression | **NO REGRESSION ATTRIBUTABLE TO THIS TASK** — 5279 passed / 124 failed / 174 skipped, all 124 classified as pre-existing or environment (§15.2); notification rail 364/364 |
| Commit / push / deploy / production | **NONE** |

This task provides **implementation and self-verification only**. Independent
verification (CoStrict/OHD) has **not** been performed, and no acceptance,
production-readiness or production-SLO claim is made.

> ## **IMPLEMENTED AND SELF-VERIFIED — READY FOR INDEPENDENT VERIFICATION**
