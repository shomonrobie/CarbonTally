# CT-MP-SUB-004 — PROD-READINESS NOTIFICATION **VERIFY-05**
## Independent verification of Manual Processing lifecycle notifications (N1–N4)

| Field | Value |
| --- | --- |
| **Document ID** | `CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-VERIFY-05` |
| **Task ID** | `CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-VERIFY-05` |
| **Date of verification** | **2026-10-05** |
| **Verifier** | Independent verification agent (CoStrict) — **not** the implementing agent |
| **Subject of verification** | `CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-IMPLEMENT-04` |
| **Implementation report audited** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-IMPLEMENT-04-report.md` |
| **Verdict** | **VERIFIED WITH FINDINGS — NOT READY FOR PO ACCEPTANCE** (see §22) |
| **Recommendation** | PO manual acceptance testing **may proceed** — the N1–N4 behaviours are independently reproduced; the findings are coverage/limitation findings, not demonstrated functional defects |
| **Production boundary** | No production access, no migration, no deployment, no credential change, **no commit, no push** by this task (§21) |

> This report is **independent verification evidence**. It is **not** acceptance.
> Only the Product Owner can accept. The implementation agent's self-verification
> was treated as an **audited claim**, never as authority.

---

## §1 Task identity

Independently verify the IMPLEMENT-04 Manual Processing lifecycle notifications
N1–N4, plus the mandated regression that **MP coverage allocation/release remain
audit-only**.

Independence measures taken:

* the producer module, every call site, the repository layer and the API layer were
  read directly (no reliance on test names or on the implementation report);
* **every** claimed recipient-resolution repository method was confirmed to exist
  on the **real** data layer (fakes could otherwise mask a silent no-op);
* runtime verification was executed against the **live Demo Lab database** and the
  **running backend**, using **real credentials** through the **real gateway** —
  no test fake was imported or executed;
* browser verification drove the **real frontend on `:3000`** with real logins;
* the full-suite failure claim was **independently reproduced and independently
  classified**, including a **pristine `git worktree` control run**;
* the implementation's own reports were treated as evidence to falsify, not to
  confirm.

---

## §2 Governing authority

| Document | Role in this verification |
| --- | --- |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-IMPLEMENT-04-report.md` | The implementation under verification (audited claim source) |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md` | Governing fact-finding that established the notification architecture and the absence of an MP producer |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-POLICY-FACTFIND-03-report.md` | Governing policy fact-finding (channel/email/preference/Realtime posture) |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` (**P-1 / P-2**) | The ratified PO decision record: **P-2 — allocation/release remain audit-only**; **no** new notification/preference/provider/outbox authorised by that record |
| `AGENTS.md` | CarbonTally operating constitution (§2 source-of-truth hierarchy, §44–45 security testing, §70 Git safety, §73 acceptance language, §74 no false completion) |

**Note on P-2 vs N1–N4.** P-2 (recording the closure of NV-10) decided that
*allocation/release* stay audit-only. The N1–N4 authorisation is a **separate,
later** PO authorisation carried in the IMPLEMENT-04 task directive (2026-10-05).
This verification treated N1–N4 as authorised **and** P-2 as still binding; both
were tested, and they are consistent (allocation/release emit audit rows and no
notification — §15).

---

## §3 Implementation baseline

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD **at verification start** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` ("FINAL-03: freeze production cutover release") — matches the implementation report |
| HEAD **at verification close** | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` — **one additional, documentation-only commit** landed during the verification window (see §20 L-6) |
| Files changed by this task | **none** (verification only; report added) |
| Working tree | 161 entries; the IMPLEMENT-04 artefacts are present and unmodified by this task: `backend/services/manual_processing_notifications.py` (untracked/new), `backend/services/manual_processing_routing.py` (untracked), the hook sites in `backend/services/work_items.py`, `backend/api/v3_operations.py`, `backend/api/v3_manual_extraction.py`, and `backend/tests/unit/api/test_ct_mp_sub_004_notification_implement_04.py` |

The code actually verified is therefore **“HEAD 375a48d plus the IMPLEMENT-04
working-tree changes”**. The intervening commit changed **only**
`docs/carbontally_master_handover_2026-10-05.md` (1 file, +1023 lines, no
`.py/.js/.jsx/.ts/.tsx/.sql`), so the verified code baseline is unaffected.

---

## §4 Environment

| Component | Detail |
| --- | --- |
| Database | `carbontally_demo_local` on `127.0.0.1:54426` (local Demo Lab; **not** the investor `postgres` dataset, **not** production) |
| Gateway / auth | `http://127.0.0.1:54430` (local GoTrue + PostgREST), `/auth/v1/health` = 200 |
| Backend | `http://127.0.0.1:8070` (release backend, started by this task from `backend.env`) — `/health` 200, `/openapi.json` 200 |
| Frontend | `http://localhost:3000` (pre-existing repo dev server, `PORT=3000`, cwd `…/ct_93d5cdd/frontend`, `static/js/bundle.js` 200) — **`:3100` was not used** |
| Fixture | PD-5 MP coverage fixture already applied (1 `manual_processing_grants` row for org `aa6cde4e…`); fixture implementation **not** altered |
| Baseline DB state | `notifications` = 8 rows (**zero** `manual_processing.*`), `notification_delivery` = **0** rows, open `work_item_assignments` = 4 |
| Verification artefacts (outside the repo) | `~/ct_local_env/verify05/verify_mp_notif.py` (43 runtime checks), `browser_verify.py` (11 browser checks), `reset_verify05.sql`, `runtime_evidence.json`, `browser/browser_evidence.json`, `browser/*.png`, `fullsuite.log` |

---

## §5 Source / code audit

### 5.1 Producer module

`backend/services/manual_processing_notifications.py` (668 lines, new) — read in
full. It defines the four notification types, five deterministic key builders,
four recipient resolvers, a best-effort `_emit`, and one audit helper. Structural
properties confirmed by reading, not by test names:

| Property | Evidence |
| --- | --- |
| In-app only | `_emit` calls `repos.notifications.create_idempotent` and nothing else; the module contains **no** `record_delivery` / `email_for_user` / mailer / `operational_alerting` call (`grep` → only docstring mentions) |
| No caller-supplied recipient or key | `inspect.signature` of all four producer entry points exposes **no** `recipient_id` / `event_key` / `notification_target` parameter (`SEC-SIG-1`, runtime) |
| Server-derived recipients | `pe_staff_recipients`, `resolve_responsible_consultant`, `resolve_uploader` — no request input anywhere |
| Best-effort, never fatal | `_emit` wraps each `create_idempotent` in `try/except` and logs; `pe_staff_recipients` and every resolver also swallow lookup errors |
| Idempotency boundary | the existing partial unique index `uq_notifications_event_key` on `(recipient_id, event_key)`; **no new index** |

### 5.2 Recipient-resolution methods exist on the REAL repositories

This was the highest-value static check, because every resolver degrades **silently**
to “no notification” when a method is missing:

| Resolver call | Real repository method | Found |
| --- | --- | --- |
| `repos.staff.list_entity_staff` | `backend/data/staff.py:91` | ✅ |
| `repos.consultants.list_active_client_grants` | `backend/data/consultants.py:440` | ✅ |
| `repos.consultants.list_firm_members` | `backend/data/consultants.py:255` | ✅ |
| `repos.consultants.get_profile_by_id` | `backend/data/consultants.py:194` | ✅ |
| `repos.consultants.get_active_memberships_by_user` | `backend/data/consultants.py:298` | ✅ |
| `repos.manual_extraction.get_item_consultant_provenance` | `backend/data/manual_extraction.py:729` | ✅ |
| `repos.files.get` (`OrganizationFilesRepository`) | `backend/data/organization_files.py:87` | ✅ |

The domain carriers carry the fields the resolvers read:
`ConsultantClient.created_by` (`backend/domain/partners.py:277`),
`ConsultantFirmMember.user_id/is_active` (`backend/domain/partners.py:152`),
`StaffProfile.entity_id/is_active/user_id` (`backend/domain/staff.py:51`).
**No silent no-op path was found.**

### 5.3 Call sites traced (business event → recipient → key → `create_idempotent` → row → API)

| Event | Call site (verified in source) | Recipient resolution | Key |
| --- | --- | --- | --- |
| **N1** item PE assignment | `backend/services/work_items.py:222–232` (`ops_assign_item`, `elif pe_id is not None`) | `pe_staff_recipients(entity)` → `staff.list_entity_staff` | `manual_processing.pe_assigned:item:{item}:{assignment_row_id}` |
| **N1** item (router) | `backend/services/manual_processing_routing.py:329` and `:405` | same | same (create + idempotent branch) |
| **N1** batch | `backend/api/v3_operations.py:2335–2341` (`assign_batch`, `if updated.entity_id`) | same | `manual_processing.pe_assigned:batch:{batch}:{entity}` |
| **N2** item | pre-existing `work_items._notify_assignee` (`backend/services/work_items.py:52–70`, invoked at `:216–221`) | `assigned_to`, `!= actor` | `work_item:{action}:{item}:{assignment_row_id}` |
| **N2** batch | `backend/api/v3_operations.py:2342–2350` (`elif updated.assigned_to and != actor`) | that user | `manual_processing.validator_assigned:batch:{batch}:{user}` |
| **N3** item entry | `backend/services/manual_processing_routing.py:415–419` | `resolve_responsible_consultant(org, item)` | `manual_processing.entered:item:{item}` |
| **N3** batch entry | `backend/api/v3_manual_extraction.py:73–75` (`create_batch`) | `resolve_responsible_consultant(org, None)` | `manual_processing.entered:batch:{batch}` |
| **N4** terminal | `backend/api/v3_operations.py:2211–2212` (`ct_qc_decision_endpoint`, `if payload.approved`) | `resolve_uploader(item)` → `organization_files.uploaded_by` | `manual_processing.completed:item:{item}` |

`git diff` confirms `services/work_items.py` was changed **only** by the import
plus the `elif pe_id is not None` branch; `_notify_assignee` and all of
`ops_claim_item` / `ops_release_item` / `ops_complete_item` / `pe_*` are unchanged.

### 5.4 “Exactly one writer of `ct_qc_approved`” — checked

The N4 claim depends on `ct_qc_approved` being written in exactly one place. The
repository writer `ManualExtractionRepository.ct_qc_decision`
(`backend/data/manual_extraction.py:800–823`) updates only rows whose status is in
`('reviewed','pe_qc_approved','ct_qc')`, and it is reached from the single route
`POST /api/v3/ops/qc/items/{item_id}/decision`. No other writer of
`ct_qc_approved` was found. `notify_manual_processing_completion` is referenced
by exactly one call site.

### 5.5 N1 previously notified nobody — corroborated

`work_item_assignee_shape` (live DB) forces `assigned_to IS NULL` for a
`processing_entity` assignment, so the pre-existing
`if assigned_to is not None and assigned_to != actor_user_id` guard was **false
for every PE assignment**. The live database at baseline contained 3 open
PE assignments (`3248eaf8`, `62ee2200`, `69d6369a`) with **0** PE notifications —
independent corroboration that N1 is genuinely new behaviour.

---

## §6 N1 — MP work assigned to a Processing Entity

**Runtime method.** Real HTTP `POST /api/v3/ops/items/{id}/work/assign` with a real
`platform.admin` bearer token, against the live lab DB. Item
`35f31e6d-1118-4262-920e-822bfdf4d88f` (Org A, verified unassigned).

| Check | Result | Evidence |
| --- | --- | --- |
| Assignment accepted | PASS | HTTP 200; D38 row `ac8db643-bb53-4327-83ac-72db6a89ebb3` (`assign`, `processing_entity`, PE Alpha `f8c4f11e…`) |
| Correct active PE staff recipient | PASS | exactly **one** row → `b986d83c-b8ab-42e4-837a-2c2d486448e8` (`pe.manager`) |
| Durable in-app row | PASS | `id=70286f9b-95f0-4537-8e8f-f683350a6f6f`, type `manual_processing.pe_assigned`, title “Manual processing work assigned”, `actor_domain=internal_staff` |
| Deterministic event key | PASS | `manual_processing.pe_assigned:item:35f31e6d-1118-4262-920e-822bfdf4d88f:ac8db643-bb53-4327-83ac-72db6a89ebb3` (equals the open D38 row id) |
| Unrelated PE **denied** | PASS | PE Beta staff `ac2ed5ac…` had **no** row for this item at this step |
| Internal staff **denied** | PASS | no rows for `1fe17efb…` / `960649a6…` |
| **No email** | PASS | `notification_delivery` unchanged at **0** rows; module has no mailer path (§5.1) |
| Assignment remains authoritative | PASS | `audit_trail` `work_item:assign` row present for the item; producer failures are swallowed (§5.1) |
| Idempotency (HTTP repeat + 3 direct producer replays) | PASS | still exactly **1** row |
| Genuine reassignment | PASS | reassign to PE Beta → new row `b5e3dac4…` keyed to the **new** row `5e34477d-ec2e-49ef-a17a-92b94b45931d`; PE Beta notified, Alpha’s original row retained |
| Batch-level N1 | PASS (service layer — see F-1) | `manual_processing.pe_assigned:batch:a2ffd5bf-…:f8c4f11e-…` → exactly 1 row (`a6bb6174…`) for PE Alpha staff, idempotent across 2 calls |

**Conclusion N1:** independently verified — durable, correct recipient, no email,
no client notification, idempotent, deterministic server-side key, assignment
authoritative. **No finding against N1 semantics.** The only gap is that the
*batch* trigger could not be driven over HTTP with the shipped Demo Lab
identities (F-1).

---

## §7 N2 — assignment to a specific CarbonTally validator

**Runtime method.** Real HTTP `POST /api/v3/ops/items/{id}/work/assign` with
`{"assigned_to": <operator>}`; item `c9175c9f-2e37-482f-be64-11e577b8d11c`.

| Check | Result | Evidence |
| --- | --- | --- |
| Exact validator notified | PASS | row `ac27604a-fdc4-4c78-9e2e-f07690dff78c` → `960649a6…` (operator **only**) |
| Notification created | PASS | type `work_item.assigned`, key `work_item:assign:c9175c9f-…:27b691ab-542e-4477-b4ca-7efd1c5e2377` |
| No duplicate on repeat assignment | PASS | still exactly 1 row |
| A PE assignment never emits `work_item.assigned` | PASS | PE Alpha staff have **no** `work_item.assigned` rows |
| Self-claim / release / completion silent | PASS (source) | `ops_claim_item` → `assigned_to == actor` ⇒ the `if` is false and the `elif` requires a PE id ⇒ no producer call; `_ops_close`/`ops_complete_item` contain no producer call |
| Batch-level N2 | PASS (service layer — see F-1) | `manual_processing.validator_assigned:batch:d8b87866-…:960649a6-…` → exactly 1 row (`ce36be31…`), idempotent |

**Reuse of `work_item.assigned` — semantic check the task demanded.**
The existing producer is genuinely reused, and it *does* correspond to
validator-assignment semantics **for internal-staff assignments**:

* it fires only when `assigned_to` is set (internal staff) — never for a PE
  assignment (shape-constrained `assigned_to IS NULL`);
* it targets exactly the assignee;
* it is silent for self-claim (claimant == actor).

It is, however, a **generic** type: the row's title/message (“Work item
assigned / assigned to you (assign)”) does not distinguish *CarbonTally validator
assignment* from any other internal work-item assignment, and the recipient is
whatever **active internal staff** user the caller nominated — the item-level
surface does not itself assert a *validator* capability. The assignment ledger and
the route's `can_process`/`can_review` gate remain the authoritative controls, so
this is **not** a security or correctness defect — it is an information-semantics
limitation (**F-3**, LOW).

---

## §8 N3 — a document/batch enters Manual Processing

**Recipient rule verified in source** (`resolve_responsible_consultant`):
(1) the item's durable D7 `consultant_firm_id` **when that firm still holds an
ACTIVE grant** → else (2) the **sole** ACTIVE `consultant_clients` relationship →
within that firm, (a) the active member recorded as `consultant_clients.created_by`
→ else (b) the firm principal `consultant_profiles.user_id`; anything else ⇒
`None` (event withheld; audited unless the client is a direct customer).

### 8.1 HTTP entry path (strongest evidence)

Because only the PD-5 fixture organisation `aa6cde4e-e2ab-54c2-a3a8-fd2094046d59`
has FIN-06 Manual Processing enabled, the HTTP entry event was driven there as its
real owner (`mp.owner.dual`):

* `POST /api/v3/manual-extraction/batches?organization_id=aa6cde4e…` → **HTTP 201**, batch `ab8757c3-7379-4ab8-bc99-ab75c87ea1a0`;
* exactly **one** notification: recipient `270b49a4-e32e-403f-a513-abdb4463f969`, type
  `manual_processing.entered`, key `manual_processing.entered:batch:ab8757c3-…`;
* that user **is** `consultant_clients.created_by` for that org (and the firm’s only
  active member) → the **relationship-creator rule fires**;
* the *other* fixture firm principal (`991d19fb…`) received **nothing**;
* **cleaned up** (notification + batch deleted; `manual_extraction_batches` back to 4).

This independently verifies the **creator rule** and the HTTP wiring.

### 8.2 Firm-principal fallback + non-broadcast (service layer, live DB)

Using `CLIENT_A` (single ACTIVE grant → firm `5d37e668…`, `created_by` **NULL**, and
**two** active firm members):

| Check | Result | Evidence |
| --- | --- | --- |
| Exactly one responsible consultant | PASS | `304ff83c-dd57-40d2-8032-b5de3f6eb86a` (`consultant.owner`), key `manual_processing.entered:item:9cf03b18-…` (row `3a922568…`) — principal fallback |
| **No broadcast** to other firm members | PASS | `7c200ce8…` (`consultant.member`, active, `client_access` includes Client A) received **nothing** |
| **No client notification** | PASS | `a896b98d…` (Client A owner) received nothing |
| Idempotent | PASS | 3 calls ⇒ still exactly 1 row |
| Fail-safe, no relationship | PASS | Org A (direct customer, no grant) ⇒ **0** rows, and **no** escalation audit (normal state) |
| Batch variant | PASS | `manual_processing.entered:batch:8dec0827-…` → 1 row (`0678f0fd…`) to the same consultant |
| Caller cannot redirect the recipient | PASS | producer signatures take no recipient (§5.1); the HTTP body exposes no recipient field on `BatchCreate` |

### 8.3 Determinism assessment (the task asked for a finding if not deterministic)

Given fixed data the resolution **is** deterministic and single-valued, and it
**never** guesses or broadcasts. **But** the “responsible consultant” is a
**derived heuristic**, not a first-class product concept: the schema has no
responsible-consultant column, so the recipient is “whoever created the client
relationship, else the firm principal”. If a firm’s creator leaves, or the PO’s
intended responsible party is a specific team member, the notification goes to the
principal instead. This is **F-2** (MEDIUM, product-model), already flagged for PO
review by the implementation report §19.1 — this verification **confirms** the
finding and its determinism boundary, and adds that the *creator* rule is now
independently proven to work.

**Not independently reproduced:** the `multiple_consultant_relationships` audit
escalation (no lab organisation currently has two ACTIVE grants; constructing one
would have required a second cross-firm relationship grant). It is covered only by
the unit suite. Recorded in §19/§20.

**Conclusion N3:** independently verified for the single-grant and provenance
cases, including non-broadcast, client exclusion and the HTTP entry path.
Determinism is confirmed for fixed data, with the product-model caveat above.

---

## §9 N4 — terminal validated state → original uploader

**Runtime method.** Item `1a27d672-13ec-4bfc-a2d9-dec825705841` (Org A; `file_id` →
`organization_files.uploaded_by` = `52a55937…`, the Org A owner).

| Step | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | MP work assigned to PE Alpha | PASS | D38 row `315716b6…`; N1 row `3f6f4f00…` |
| 2 | **PE completes its portion before validation** | PASS | `POST /api/v3/pe/items/{id}/complete` … **zero** `manual_processing.completed` rows — **no false “finished”** |
| 3 | Terminal CT-QC approval (`ct_qc_decision(approved=True)`) + producer | PASS | exactly 1 completion row `f2c00ccb-24ae-4a1c-a5a8-2a9868d34f4` → **`52a55937…` (original uploader)**, key `manual_processing.completed:item:1a27d672-…`, title “Manual processing complete” |
| 4 | Wrong actors | PASS | **no** completion row for PE Alpha/Beta staff, the validator (`1fe17efb…`), the operator, the client or the consultant |
| 5 | Duplicate terminal transition | PASS | second `ct_qc_decision` returned `None` (already terminal ⇒ HTTP 409 path) and a direct producer replay added **no** row |
| 6 | **Reassignment does not change the uploader** | PASS | after reassigning the item to PE Beta (row `c994e591…`, which emitted a *new* N1 to PE Beta) the completion row is unchanged: same recipient, same key, count still 1 |
| 7 | Item status | PASS | `manual_extraction_items.status = ct_qc_approved`, `qc_by = 1fe17efb…` |
| 8 | Link safety | PASS (browser) | the uploader’s “Open” link resolved to `/processing/1a27d672-…` and rendered without any authorization error; the PE/consultant/client tokens were **denied** on the ops workspace route (§10) |
| 9 | **No email / no client notification** | PASS | `notification_delivery` unchanged; zero completion rows for any client user |

**Conclusion N4:** independently verified — including the two behaviours the task
singled out (**PE completion must not trigger N4**; **terminal validation must**),
uploader provenance stability under reassignment, and wrong-actor exclusion.

**Disclosure:** step 3 invoked the `ct_qc_decision` repository writer followed by
the exact producer call the endpoint makes, because the endpoint’s `can_qc` gate is
not satisfiable by any shipped Demo Lab identity (F-1). The endpoint wiring itself
was confirmed by source inspection (§5.3) and by the endpoint’s 403 evidence.

---

## §10 Idempotency (independently tested per event)

| Event | Test | Result |
| --- | --- | --- |
| N1 | HTTP repeat + 3 direct producer replays | **1** row |
| N1 (new entity) | genuine reassignment | **1 new** row with a **new** key (correct) |
| N1 batch | 2 calls | **1** row |
| N2 item | HTTP repeat | **1** row |
| N2 batch | 2 calls | **1** row |
| N3 item | 3 calls | **1** row |
| N3 batch (HTTP) | 1 call + cleanup | **1** row |
| N4 | duplicate terminal transition + producer replay | **1** row |
| Global | `(recipient_id, event_key)` uniqueness across the **entire** table | **0 duplicates** |

All assertions were made against **persisted rows** (`SELECT` on
`public.notifications`), not mocked repository calls. The 43-check harness may be
re-run at any time via `~/ct_local_env/verify05/verify_mp_notif.py` after
`reset_verify05.sql`.

---

## §11 Event-key audit

| Event | Observed key | Deterministic | Server-generated | Stable | Retry-safe | Caller-controlled |
| --- | --- | --- | --- | --- | --- | --- |
| N1 item | `manual_processing.pe_assigned:item:{item}:{assignment_row_id}` | ✅ business identity | ✅ | ✅ | ✅ | ❌ |
| N1 batch | `manual_processing.pe_assigned:batch:{batch}:{entity}` | ✅ | ✅ | ✅ | ✅ | ❌ |
| N2 item | `work_item:{action}:{item}:{assignment_row_id}` | ✅ (pre-existing) | ✅ | ✅ | ✅ | ❌ |
| N2 batch | `manual_processing.validator_assigned:batch:{batch}:{user}` | ✅ | ✅ | ✅ | ✅ | ❌ |
| N3 item | `manual_processing.entered:item:{item}` | ✅ | ✅ | ✅ | ✅ | ❌ |
| N3 batch | `manual_processing.entered:batch:{batch}` | ✅ | ✅ | ✅ | ✅ | ❌ |
| N4 | `manual_processing.completed:item:{item}` | ✅ | ✅ | ✅ | ✅ | ❌ |

* **No** key contains a timestamp, a random value, or a caller-supplied token
  (`KEY-1`: 0 degenerate keys over every MP row).
* All keys are compatible with the **existing** partial unique index
  `uq_notifications_event_key` — no DDL was required and none exists in the diff.
* **Known (correct) consequence:** keying N1 on the assignment row means a
  repeated *identical* re-route emits nothing, while a genuine reassignment emits a
  new event. Verified both ways.

---

## §12 Security / tenant isolation

Executed with **real tokens** against the **real API**.

| Probe | Expected | Observed |
| --- | --- | --- |
| Correct recipient (PE Alpha) | visible | ✅ 200, own N1 row(s) present |
| Unrelated PE (Beta) | not visible | ✅ Alpha’s rows absent from Beta’s inbox |
| Consultant firm member (not the resolved recipient) | not visible | ✅ N3 rows absent |
| Client organisation (Client A) | not visible | ✅ **0** MP rows in the inbox (`total = 0`) |
| Cross-tenant organisation (Org B) | not visible | ✅ MP rows absent |
| Unauthenticated `GET /api/v3/notifications` | denied | ✅ 401 |
| **Award scope:** any actor served another user’s row | none | ✅ none (whole-matrix sweep) |
| **Notification is not an access-control mechanism** | denied | ✅ consultant / client / PE tokens all **denied** on `GET /api/v3/ops/items/{id}/workspace` (401/403) |
| Underlying-work access remains separately authorized | — | ✅ confirmed: the notification row grants nothing |

**No unexpected ALLOW was observed.**

---

## §13 API retrieval

`GET /api/v3/notifications` (unchanged contract):

* N1 row retrieved by PE Alpha’s authenticated context; **not** retrievable by PE Beta;
* N3 row retrieved by the responsible consultant; **not** retrievable by the other
  firm member;
* N4 row retrieved by the original uploader;
* the retrieved N4 payload carries `notification_type = manual_processing.completed`,
  a non-empty `title` and `created_at`;
* `total`/`limit`/`offset` pagination fields behave as before;
* **no** unauthorized rows in any response;
* unauthenticated access denied (401).

Supabase Realtime was **not** required for acceptance, and was **not** used as
evidence of delivery.

---

## §14 Realtime limitation (recorded, deliberately **not** fixed)

| Observation | Evidence |
| --- | --- |
| Frontend subscribes to `notifications` with `filter: user_id=eq.${user.id}` while the table’s recipient column is **`recipient_id`** | `frontend/src/context/RealtimeContext.jsx:313`, `frontend/src/lib/realtime/manager.js:258` |
| Those files are **unmodified versus HEAD** ⇒ the defect is **pre-existing**, not introduced by IMPLEMENT-04 | `git status --short` on both files → empty |
| `public.notifications` is **RLS fail-closed with zero policies** (CT-FINAL-03 posture preserved) | live DB: `relrowsecurity = t`, `pg_policies` → **0 rows** |
| Implementation did **not** weaken notification RLS | no policy/DDL change in the diff; posture identical to baseline |
| Implementation did **not** make Realtime a transactional dependency | producers run after the business mutation; failures are logged, never raised; the 43-check run passed with Realtime unreachable |
| MP workflow does not fail when Realtime is unavailable | runtime run completed with the lab gateway (which does not proxy `/realtime/v1`) in place |
| Durable API remains authoritative | `GET /api/v3/notifications` returned every row; `backend.log` contains **0** producer-failure warnings |

**Authoritative conclusion:** Realtime delivery of notifications is **not working**
in this environment for two independent, pre-existing reasons (wrong filter column;
RLS with no policies). It does **not** affect N1–N4 acceptance because the inbox is
served by the API. Realtime was **not** fixed and must remain a separate task.

---

## §15 Email exclusion

| Check | Result |
| --- | --- |
| `notification_delivery` row count before vs after the whole N1–N4 run | **0 → 0** |
| `_emit` call graph | `create_idempotent` only (no `record_delivery`, `email_for_user`, mailer, Resend/SMTP) |
| `notification_delivery.channel` / schema | unchanged; no DDL in the diff |
| X2 operational alerting (`services/operational_alerting.py`) | untouched (not referenced by the new module) |
| Preference / opt-out / feature-flag mechanism | **none created**; the producer reads no configuration |
| Backend log during the run | 0 producer-failure warnings |

**N1–N4 are in-app only. No email is sent. No opt-out exists.** Confirmed.

---

## §16 Allocation / release regression (must remain audit-only)

| Check | Result | Evidence |
| --- | --- | --- |
| Target modules contain no notification vocabulary | PASS | `grep -rn 'notifications\|create_idempotent\|Notification' backend/api/manual_processing_admin.py backend/api/manual_processing_auth.py backend/data/manual_processing.py backend/domain/manual_processing.py` → **no matches** |
| The new producer module contains no allocation/release behaviour | PASS | only two textual mentions, both docstrings explicitly stating allocation/release stay audit-only |
| Allocation/release write **audit only** | PASS | `backend/api/v3_manual_processing_coverage.py:348–350` writes `manual_processing:allocation_created`; `:406–408` writes `manual_processing:allocation_released`; neither references notifications |
| NV-10 regression rail | PASS | `test_ct_mp_sub_004_prod_readiness.py -k NV10` → **3 passed** (allocate / release / admin-allocate each write an audit row and leave the notification count unchanged) |
| **Live-DB confirmation** | PASS | the lab `audit_trail` contains `manual_processing:allocation_created` **and** `manual_processing:allocation_released` rows (2026-10-05 02:00–02:05, actor `270b49a4…`) with **zero** corresponding notification rows |

**Allocation/release remain audit-only. No implementation turn turned them into
notifications. Regression preserved.**

---

## §17 Browser verification

Real headless Chromium, **one fresh browser context per actor** (an earlier draft
shared one context; that leaked sessions and produced false positives — corrected
before recording results), real credential logins at `/login`. Frontend
`http://localhost:3000`; **`:3100` was not used**.

| # | Actor | Check | Result |
| --- | --- | --- | --- |
| 1 | `pe.manager` (PE Alpha) | lands in `/pe`; N1 “Manual processing work assigned” visible in the PE bell | PASS |
| 2 | `pe.manager` | opening the notification target stays inside the authorized PE workspace; no denial markers | PASS |
| 3 | `pe.beta.manager` | authenticates; sees **neither** the consultant N3 **nor** the uploader N4 | PASS |
| 4 | `consultant.owner` | N3 “Work entered manual processing” visible in `/notifications` | PASS |
| 5 | `consultant.owner` | opening the target keeps them inside their workspace | PASS |
| 6 | `consultant.member` | same firm, **does not** see N3 | PASS |
| 7 | `owner.a` (uploader) | N4 “Manual processing complete” visible | PASS |
| 8 | `owner.a` | opening the target reaches `/processing/{item}` with no authorization error | PASS |
| 9 | `owner.clienta` | client org sees **no** MP lifecycle notification | PASS |

**11/11 browser checks PASS.** Screenshots:
`~/ct_local_env/verify05/browser/01…09*.png`.
Console output per actor contains **only** the known Demo Lab gateway WebSocket
errors (`ws://127.0.0.1:54430/realtime/v1/…`) — an environmental gateway
limitation documented in `tools/demo_lab/README.md` §Known limitations, **not** a
page exception and unrelated to notifications.

---

## §18 PO MANUAL QA ACTOR MATRIX

No passwords appear here. Read credentials from
`~/ct_local_env/demo_lab/credentials.local.json`
(`demo_password`, mode 0600, outside the repository).
E-mail domain: `demo-lab.carbontally.local`.

| Login identifier | Role | Org / firm | Intended test state | Expected notification | Expected **non**-notification | Browser route | Fixture / reset command | Expected result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `platform.admin@…` | CarbonTally internal `admin` | CarbonTally | assigned MP work to PE Alpha | — (actor is the assigner) | N1 to self | `http://localhost:3000/ops` | `python3 tools/demo_lab/run_demo_lab.sh --backend` then `… verify_mp_notif.py` | assignment accepted; PE notified |
| `pe.manager@…` | PE staff `pe_manager` | Demo Lab PE Alpha (`f8c4f11e…`) | item `35f31e6d…` assigned to PE Alpha | **N1** “Manual processing work assigned” in the bell (`/pe`) | N3, N4 | `http://localhost:3000/pe` | as above (or use the rows already left in place) | bell badge ≥ 1; row opens inside `/pe` |
| `pe.beta.manager@…` | PE staff `pe_manager` | Demo Lab PE Beta (`8ab93340…`) | unrelated entity | — | **N3**, **N4** | `http://localhost:3000/pe` | none (read-only) | bell shows PE Beta’s own rows only |
| `consultant.owner@…` | Consultant firm **owner** / principal | Demo Lab Carbon Consultants (`5d37e668…`) | item `9cf03b18…` (Client A) entered MP | **N3** “Work entered manual processing” | N1, N4 | `http://localhost:3000/notifications` | none (read-only) | exactly one N3 row, opens in the consultant workspace |
| `consultant.member@…` | Consultant firm **member** | same firm | same event | — | **N3** | `http://localhost:3000/notifications` | none (read-only) | inbox does **not** contain the N3 row |
| `owner.a@…` | Customer **owner** (original uploader) | Demo Lab Organisation A | item `1a27d672…` reached `ct_qc_approved` | **N4** “Manual processing complete” | N3 | `http://localhost:3000/notifications` | none (read-only) | row present; “Open” → `/processing/1a27d672…` renders |
| `owner.clienta@…` | Client **owner** | Demo Lab Client A (`02b38744…`) | the client of the N3 event | — | **N1, N2, N3, N4** | `http://localhost:3000/notifications` | none (read-only) | inbox empty of MP rows (`total = 0`) |
| `operator@…` | CarbonTally internal `operator` | CarbonTally | item `c9175c9f…` assigned to this validator | **N2** “Work item assigned” | N1 | `http://localhost:3000/notifications` | none (read-only) | one N2 row to this user only |
| `mp.owner.dual@…` | Fixture customer owner | MP-FX org `aa6cde4e…` (MP **enabled**) | create an MP batch | **N3** to the firm’s relationship creator | N3 to the other firm principal | `http://localhost:3000/manual-processing` | none (write) — then delete the batch | 201; one N3 row |
| `owner.b@…` | Unrelated org owner | Demo Lab Organisation B | cross-tenant probe | — | all MP rows | `http://localhost:3000/notifications` | none (read-only) | no MP rows |

**State currently left in the Demo Lab for the PO (from this verification run):**

* 9 `manual_processing.*` rows + 1 `work_item.assigned` row (created by the
  runtime harness; see §16/§19 of this report for the exact ids);
* item `35f31e6d…` open → PE Beta; item `c9175c9f…` open → operator;
  item `1a27d672…` = `ct_qc_approved`; item `9cf03b18…` unchanged.

**Reset command (QA-only, removes only what this verification created):**

```bash
docker exec -i supabase_db_carbon_ledger psql -U postgres \
  -d carbontally_demo_local -v ON_ERROR_STOP=1 -f - \
  < ~/ct_local_env/verify05/reset_verify05.sql
# expected afterwards: notifications = 8, open work-item assignments = 4
```

The script contains **no** write to the PD-5 fixture, the DEMO-T1 identities, the
investor dataset or any production system.

---

## §19 Reproducible PO procedure

**Classification:** (R) = read-only, (W) = mutates Demo Lab, (X) = reset.

1. **(R)** Confirm the stack: `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8070/health` → `200`; `curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/` → `200`.
2. **(X)** Optional clean start: run the `reset_verify05.sql` command in §18, then
   re-seed the state with the verification server-side harness:
   `~/ct_93d5cdd/backend/.venv/bin/python ~/ct_local_env/verify05/verify_mp_notif.py`
   (43 checks; writes only the rows listed in §18).
3. **(R)** Log in as **actor A** = `pe.manager@…` at
   `http://localhost:3000/login`, open `http://localhost:3000/pe`, click the bell →
   observe **N1**.
4. **(R)** Open the N1 row → confirm the target stays inside `/pe`.
5. **(R)** Log in as **actor B** = `pe.beta.manager@…` (use a **fresh
   private/incognito window**, or log out first) → bell must **not** show N3/N4.
6. **(R)** Repeat for `consultant.owner@…` (**N3 visible**) and
   `consultant.member@…` (**N3 absent**) at `/notifications`.
7. **(R)** Repeat for `owner.a@…` (**N4 visible**; open it) and
   `owner.clienta@…` (**no** MP rows).
8. **(W, optional)** For the HTTP N3 write path: log in as `mp.owner.dual@…`, create
   a batch at `/manual-processing`, observe a single N3 to the firm creator, then
   delete the batch.
9. **(X)** Finish with the reset command in §18 if the mutated state is not wanted.
   If the PO wants to keep the notifications for inspection, do nothing — the
   frontend is read-only for them.

> **Important for step 5/6/7:** always use a **fresh browser context**
> (private window or explicit log-out). A shared tab keeps the previous actor’s
> session and will show the previous actor’s inbox — this was observed and
> corrected during verification.

---

## §20 Full-suite failure classification (independent)

**Independently reproduced** (`cd backend && .venv/bin/python -m pytest -q -o addopts=""`):

```
124 failed, 5279 passed, 174 skipped, 17 warnings in 759.55s (0:12:39)
```

This **exactly matches** the implementation report's claim (5279 / 124 / 174), and
the per-failure breakdown was **derived independently** from the raw log, not
copied:

| Class | Independently observed | Reproduced how |
| --- | --- | --- |
| Migration-baseline unit expectations | **4** — `tests/unit/data/test_p17_migrations…`, `test_i1_insight_migration…`, `test_i2_insight_authorization_contracts…`, `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | **Reproduced on a pristine `git worktree` of HEAD** (clean, 0 modified files) → the same 4 ids fail there |
| Extraction-suggestion unit tests | **3** — `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice`, `::test_suggest_missing_fields_leave_unresolved`, `::test_suggest_no_fabrication_on_garbage` | Same pristine-worktree control run → the same 3 ids fail there |
| Environment-dependent discovery test | **1** — `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | **Passes** in the pristine worktree and fails only in the working environment (a `.env`-supplied mail credential makes the platform default provider count as configured) |
| Live-DB integration / environment | **116** — all under `tests/integration/` | Schema/data drift of the local DB: `column "actor_organization_id" of relation "audit_trail" does not exist` ×63, `UndefinedTableError` ×61, `calculation_snapshots.source_line_item_id` ×9, `document_processing_queue.stage` ×3, `expected 7049 total factors` ×2, plus unique/FK/ambiguous-parameter and one `carbontally_test` environment guard |
| **Notification-task failures** | **0** | `grep -Ei 'notif\|manual_processing\|work_item\|pe_assigned\|validator_assigned\|entered\|completed'` over all 124 `FAILED` ids → **no match** |
| **Total** | **124** | 4 + 3 + 1 + 116 = 124 ✅ |

**Conclusion:** the implementation report's “0 failures attributable to
IMPLEMENT-04” claim is **independently confirmed** for the whole 124-failure set,
with the 7 non-integration failures additionally reproduced against a pristine
checkout and the 1 environment-dependent failure shown to pass there.

**Notification regression rail** (16 files, run independently):
`386 passed, 0 failed` — including this task's 60-test suite (`60 passed`) and the
NV-10 audit-only rail (`3 passed`).

---

## §21 Findings

| ID | Severity | Finding | Affected actor / workflow | Expected | Actual | Evidence | Likely root cause | Impact on acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **F-1** | **MEDIUM (verification coverage / Demo Lab readiness — not an app defect)** | Three N1–N4 **HTTP trigger paths cannot be exercised with the shipped Demo Lab identities**, so those events were verified at service/route-function level against the live DB rather than end-to-end over HTTP: (a) `POST /api/v3/ops/batches/{id}/assign` requires `can_manage_staff` **and** `can_process` — no staff role has both (`admin` has `can_manage_staff` only, `operator` has `can_process` only) ⇒ 403 for both; (b) `POST /api/v3/ops/qc/items/{id}/decision` requires `can_qc` — **no** Demo Lab staff role defines `can_qc` (`admin` = `can_review/is_superuser/is_staff_admin/can_manage_staff/can_manage_organizations`) ⇒ 403, so N4 has **no HTTP trigger**; (c) `POST /api/v3/manual-extraction/batches` requires FIN-06 MP enabled — only the PD-5 fixture org qualifies, so Org A / Client A / Client B cannot reach the N3 entry path (403 “Manual processing is not enabled for this organisation”) | Internal CarbonTally ops, validators, MP customers | a Demo Lab identity able to trigger each authorised event over HTTP | 403 “staff lacks permission: can_process” / “…: can_manage_staff” / “…: can_qc”; 403 FIN-06 | Live probes (§4, §6–§9); role permission JSON in `staff_roles` | Not an IMPLEMENT-04 defect — the gates are correct and fail-closed. But it **reduces independent assurance** for the batch-level N1/N2 and for N4’s HTTP wiring | **Limits, does not block.** N3 HTTP *was* proven via the fixture org; N1/N2 item level *were* proven over HTTP |
| **F-2** | **MEDIUM (product model — PO review already requested)** | N3’s “responsible consultant” is a **derived heuristic** (`consultant_clients.created_by` → firm principal), not a first-class product field. Deterministic for fixed data and never broadcast/guessed, but if the relationship creator leaves or the intended recipient is a different team member, the notification goes to the firm principal — or is withheld + audited | Responsible consultant, client organisations | a PO-defined, schema-backed responsible consultant | derived recipient; withheld + `manual_processing:consultant_notification_unresolved` audit where undeterminable | §8; `manual_processing_notifications.py:254–303`; proven for both rules | no responsible-consultant column exists in the schema | **Does not block** (fail-safe), but the PO must ratify the rule before relying on N3 attribution |
| **F-3** | **LOW (information semantics)** | N2 item-level reuses the generic `work_item.assigned` type: the row does not distinguish a *CarbonTally validator assignment* from any other internal work-item assignment, and the item-level surface does not itself assert a validator capability (route gate + ledger remain authoritative) | Internal validators | an unambiguous validator-assignment signal | generic “Work item assigned” title/type | §7; `work_items.py:52–70` | reuse of the pre-existing producer, as authorised by the task | Cosmetic/semantic; does not affect the recipient, idempotency or authorization |
| **F-4** | **PASS-as-finding (recorded)** | The **implemented** producer is genuinely in-app-only, deterministic, idempotent, server-derived and fail-safe on every path tested. **No N1–N4 functional defect was found** | all | — | — | §6–§16 | — | none |
| **F-5** | **INFORMATIONAL (pre-existing, NOT introduced, NOT fixed)** | Notification Realtime is non-functional: the frontend filters `notifications` on `user_id=eq.` while the column is `recipient_id`, and `public.notifications` is RLS fail-closed with **zero** policies. The API inbox is authoritative and correct | all notification recipients | — | Realtime delivers nothing; inbox still correct | §14 | pre-existing baseline (files unmodified vs HEAD) | **None** for N1–N4 acceptance; separate task required if live delivery is wanted |

**No defect was found in the authorised N1–N4 behaviour, and no implementation was
changed to make verification pass.**

---

## §22 Limitations (what was *not* independently established)

| # | Limitation | Reason |
| --- | --- | --- |
| L-1 | N1-batch and N2-batch were verified by calling the **exact producer functions the endpoints call**, not over HTTP | F-1(a) permission matrix |
| L-2 | N4’s **HTTP endpoint wiring** (FastAPI dependency/authorization chain) was verified by source inspection + the endpoint’s 403 response, not by a successful end-to-end HTTP approval | F-1(b) no `can_qc` identity |
| L-3 | The `multiple_consultant_relationships` / `provenance_firm_relationship_ended` / `firm_member_unresolved` **audit escalations** were not reproduced live | no lab organisation has two ACTIVE grants; constructing one would require an extra cross-firm relationship grant (deliberately avoided) |
| L-4 | N3 via the **automatic-fallback routing** path (`route_failed_job`) was not triggered live | requires an automatic-processing job to fail into routing; the routing hooks were read in source and the N3 producer was exercised directly + via the MP batch HTTP path |
| L-5 | Only 116 integration failures were classified **by error signature**, not individually re-executed against a provisioned schema | no provisioned schema matching the committed migrations is available locally (the drift is the cause) |
| L-6 | **HEAD advanced during the verification window** (375a48d → 3fec874c). | The intervening commit is **documentation-only** (1 file, `docs/carbontally_master_handover_2026-10-05.md`, no code) and was **not made by this task**. The pristine control worktree therefore also sits at 3fec874c; for the 7 reproduced unit failures this is immaterial because the commit touches no code or migration |
| L-7 | Frontend unit tests (`react-scripts test`) were not run | the task's required verification surface is the notification inbox/bell behaviour, which was exercised against the running app; the app's own suite is unaffected by IMPLEMENT-04 (no frontend file changed) |
| L-8 | Realtime delivery was not tested as a positive case | it is non-functional for pre-existing reasons (F-5) and the task explicitly required *not* fixing it and *not* requiring it for acceptance |

---

## §23 Production safety

| Requirement | Status | Evidence |
| --- | --- | --- |
| No production DB access | ✅ honoured | every DB operation targeted `carbontally_demo_local` on `127.0.0.1:54426`; the production/investor `postgres` dataset was never contacted |
| No production migration | ✅ honoured | no migration file created, edited or applied; no DDL executed |
| No production deployment | ✅ honoured | no deploy command was issued |
| No production credentials | ✅ honoured | only `~/ct_local_env/demo_lab/backend.env` + `credentials.local.json` (local, mode 0600) were read; the generated backend env is unmodified |
| No production Supabase project modification | ✅ honoured | only the local stack/gateway |
| No commit by this task | ✅ honoured | no `git commit` was issued by this task; the working tree is unchanged apart from this report |
| No push | ✅ honoured | no `git push` was issued |
| No implementation change | ✅ honoured | the only file created is this report; `verify_*.py` / `reset_verify05.sql` live **outside** the repo (`~/ct_local_env/verify05/`) |
| Investor/demo dataset untouched | ✅ honoured | no reseed/truncate; the PD-5 fixture was not altered; ALL lab mutations are enumerated in §18 and fully reversible via `reset_verify05.sql` |
| Secrets in this report/code | ✅ none | no passwords, tokens, JWTs, signed URLs or keys are recorded |

**Disclosure.** During the verification window the repository HEAD advanced from
`375a48d` to `3fec874c` by a **documentation-only** commit
(`docs/carbontally_master_handover_2026-10-05.md`, author `shomonrobie`,
2026-10-05 15:22:58 +0600) created **outside this task**. A second, pre-existing
`prunable` worktree `/tmp/ct_head` (detached at `375a48d`) was already registered
before this task began and was left untouched; the temporary control worktree this
task created (`/tmp/ct_head_375a48d`) was removed.

---

## §24 Final independent-verification verdict

> # **VERIFIED WITH FINDINGS — NOT READY FOR PO ACCEPTANCE**

**All four authorised behaviours (N1, N2, N3, N4) were independently reproduced**
against the live Demo Lab — real actors, real HTTP endpoints, real repositories,
real persistence — together with idempotency, event-key determinism, tenant
isolation, API retrieval, email exclusion, the allocation/release audit-only
regression, and 11/11 browser checks across five actor classes.

**Findings remain,** which is why this is not “VERIFIED — NO FINDINGS”:

* **F-1 (MEDIUM)** — three trigger paths (batch-level N1, batch-level N2, N4’s HTTP
  endpoint) are **not reachable over HTTP with the shipped Demo Lab identities**;
  they were verified one layer below. This is a *verification-coverage* and
  *Demo-Lab-readiness* gap, not a demonstrated application defect — but it means
  independent assurance for those three paths is **weaker than for the others**.
* **F-2 (MEDIUM)** — N3 attribution is a deterministic **heuristic** rather than a
  PO-ratified responsible-consultant model. It is fail-safe (never guessed, never
  broadcast) but requires PO ratification before N3 can be relied on commercially.
* **F-3 (LOW)** — N2 item-level reuses a generic notification type.
* **F-5 (INFORMATIONAL)** — notification Realtime is broken for pre-existing
  reasons; the durable API is authoritative and correct.

**Nothing was fixed, patched or reverted.** The implementation is **substantially
correct and safe**; the remaining items are a PO governance decision (F-2), a
Demo Lab coverage gap (F-1) and two low/informational notes (F-3, F-5).

**Only the Product Owner can accept this work.** This report does **not** claim
acceptance, production-readiness or production SLO compliance, and it makes no
production-scale claim.

The local Demo Lab is left running (`database 54426`, `gateway 54430`, `backend
8070`, `frontend 3000`) with the N1–N4 evidence rows in place for the PO’s manual
testing, per §18/§19.

---

### Evidence index (outside the repository)

| Artefact | Path |
| --- | --- |
| 43-check live runtime harness + JSON evidence | `~/ct_local_env/verify05/verify_mp_notif.py`, `runtime_evidence.json` |
| 11-check browser harness + JSON + screenshots | `~/ct_local_env/verify05/browser_verify.py`, `browser/browser_evidence.json`, `browser/*.png` |
| QA-only reset | `~/ct_local_env/verify05/reset_verify05.sql` |
| Full-suite log + extracted FAILED ids | `~/ct_local_env/verify05/fullsuite.log`, `failed_ids.txt` |
