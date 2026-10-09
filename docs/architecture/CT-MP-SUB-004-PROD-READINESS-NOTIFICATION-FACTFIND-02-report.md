# CT-MP-SUB-004 — PROD-READINESS NOTIFICATION FACT-FINDING 02

## Does the P-2 decision unintentionally cover *"a document batch entering Manual Processing"*?

| Field | Value |
| --- | --- |
| **Task ID** | `CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02` |
| **Task type** | Targeted **read-only** fact-finding (document upload → work item → Manual Processing routing → actor notification/communication) |
| **Repository / branch** | `/home/shomonrobie/ct_93d5cdd` · `p8-release-reconciled` |
| **HEAD** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (unchanged by this task) |
| **Worktree state read** | **39 pre-existing tracked modifications, uncommitted, NOT touched by this task** (see §1.6) |
| **Authorised writes** | **Exactly one: this report file.** No application, test, fixture, migration, schema, RLS, config or docs-governance change |
| **Governing decision record** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` (**read only, unmodified**) |
| **Final status** | **NOTIFICATION FACT-FINDING COMPLETE — READY FOR PO CLARIFICATION** (§12) |

---

## §1 Task identification

### 1.1 Purpose

Determine whether the current PO decision recorded in
`CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` §5/§6 (**P-2**, NV-10) needs a
**narrow clarification/amendment** distinguishing:

* **Manual Processing coverage allocation/release**, which the PO has decided may
  remain **audit-only**; from
* **a document batch entering Manual Processing**, which may (or may not) require
  near-real-time **operational** notification to the relevant actors.

### 1.2 Scope — what was investigated

1. The complete real code path: consultant/customer **upload → storage/upload completion → document or batch record → work item → Manual Processing routing → processor/PE assignment → existing actor communication/notification**.
2. The **existing notification architecture** (system, communication, Supabase Realtime usage, persistence, recipients, delivery, retry/failure, authorization).
3. Who the **actual recipients** are under the *existing* authorization model (submitting consultant, responsible consultant/firm, assigned PE/processor, internal ops, client).
4. Three **must-be-distinguished** business events: **A** coverage allocation/release · **B** a document batch entering Manual Processing · **C** processing status changes.
5. What **"real-time"** means in the *existing* architecture (not a new definition).
6. A single classification of the document-batch notification requirement (A/B/C/D).
7. Whether the **P-2 wording** needs amendment, and if so the **minimum** wording change (proposed, **not applied**).

### 1.3 Scope — what this task explicitly did **not** do

* No implementation (backend or frontend). No notification added or removed.
* No change to the P-1/P-2 decision record, or to any other governing document.
* No Supabase Realtime configuration, no publication change, no notification config.
* No email behaviour, no recipient matrix, no preference, no outbox, no worker.
* No change to the Manual Processing workflow, routes, services or UI.
* No migration, no deployment, no schema/RLS/grant change, no test or fixture change.
* No commit, no push.
* **No new product decision was made.** Where a decision is needed it is stated as a question, not answered.

### 1.4 Governing documents consulted (documented truth)

| Document | Used for |
| --- | --- |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01-report.md` | The governing P-1/P-2 fact-finding (notification architecture, MP audit-only evidence, producer inventory) |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` | The **authoritative P-1/P-2 decision record** (§5 P-2, §6 NV-10 acceptance, §8.1 prohibitions) |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-01-report.md` | Production-readiness acceptance target (NV-1…NV-10) |
| `docs/architecture/CT-MP-SUB-004-independent-verification-report.md` | The NV-9/NV-10 verification-gap origin (§19 "NOT verified"; NV-10 row at `:666`) |
| `docs/architecture/CT-MP-SUB-004-PD5-VERIFY-01-report.md` | PD-5 verification context |
| `docs/architecture/CT-MP-SUB-004-PO-decision-record.md` | The PD-1…PD-6 MP decision record (FIN-06 governance / routing authority) |
| `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | **The authoritative D2 UI/UX specification** (644 lines) — checked for any notification requirement |
| `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` | **D40/D11 notification vocabulary** (`:279–294`, ratification table `:501`) — the ratified event vocabulary |
| `tools/demo_lab/README.md` | Demo Lab context (NV-9/NV-5 evidence baseline) |

### 1.5 Evidence standard used in this report

Findings are labelled:

* **[CODE]** — implemented behaviour read directly from the current working-tree source (file + symbol + line).
* **[DDL]** — database/schema/migration fact.
* **[DOC]** — a documented requirement or ratified decision.
* **[INFER]** — inference, clearly marked as such and **never** presented as product policy.
* **[UNVERIFIED]** — not established by this read-only fact-finding (usually an environment/runtime property).

**No runtime observation was performed.** No server was started, no browser was
opened, no database query was executed (§11). Every "implemented behaviour"
statement below is static source reading of the **working tree**.

### 1.6 Working-tree caveat (material — must be read with §2/§3)

HEAD is `375a48dc1b9e9cfd74090bbf747554ae997acb59`. The working tree contains
**39 uncommitted, pre-existing tracked modifications** (none created by this
task). Because several files central to this fact-find are among them, every
finding below describes the **working tree**, which is the state previously
audited by the P-1/P-2 fact-find:

| Working-tree-modified file relevant here | Relevance |
| --- | --- |
| `backend/api/manual_processing_admin.py`, `backend/api/manual_processing_auth.py` | MP governance / coverage admin surfaces |
| `backend/api/v3_documents.py`, `backend/api/v3_document_uploads.py` | **The upload + enqueue pipeline** |
| `backend/data/manual_processing.py`, `backend/domain/manual_processing.py` | MP entitlement/coverage domain + persistence |
| `backend/workers/automatic_processing.py` | **The worker that performs MP fallback routing** |
| `backend/api/router.py`, `backend/tests/unit/api/fakes.py` | Routing registration / test doubles |
| `frontend/src/v3/api.js`, `frontend/src/v3/consultant/ConsultantPage.jsx`, `frontend/src/App.js` | Notification inbox wrappers / consultant polling / app shell |

The two modules that carry the **most** weight for the P-2 question —
`backend/services/work_items.py` and `backend/services/manual_processing_routing.py`
— are **unmodified** (identical to HEAD).

---

## §2 Existing document workflow (traced end-to-end)

The workflow below is the **actual** implementation, traced by symbol — not by
UI label. Two upload ingresses share **one** durable pipeline.

### 2.1 Ingress A — customer/organisation direct upload (signed URL)

| Step | Route / symbol | File |
| --- | --- | --- |
| 1. Authorise upload | `POST /api/v3/documents/upload-url` → `start_organization_upload` | `backend/api/v3_document_uploads.py:792` (helper `_start_upload` `:255`) |
| 2. Browser uploads bytes directly to Supabase Storage | (no backend involvement) | — |
| 3. Verify + security gate | `POST /api/v3/documents/{document_id}/upload-complete` → `complete_organization_upload` `:816` → `_complete_upload` **`:405`** | `backend/api/v3_document_uploads.py` |
| 4. Enter the durable pipeline | `await enqueue_document_processing(...)` **`:635`** | `backend/api/v3_document_uploads.py` |
| Abandon path | `POST /api/v3/documents/{document_id}/upload-abandon` → `abandon_organization_upload` `:835` → `_abandon_pending_upload` `:686` | same file |

`_complete_upload` **[CODE]** checks the document's `organization_id` against the
actor, refuses non-canonical storage keys, probes the stored object, then sets
`STATUS_CLEAN`, writes `record_document_event(action=ACTION_ACCEPTED)` and calls
`enqueue_document_processing` **only** for a security-cleared document.

### 2.2 Ingress B — consultant uploads a document **for** an authorised client (CON-2/3)

| Step | Route / symbol | File |
| --- | --- | --- |
| 1. Upload | `POST /api/v3/consultants/clients/{client_id}/documents` → `upload_client_document` **`:1275`** | `backend/api/v3_consultants.py` |
| 2. Authorise | `api.upload_gate.authorize_consultant_upload` (`:1294`) — active `consultant_clients` grant (D15) + firm ownership (404 cross-firm / 403 inactive) + firm member `can_upload_documents` | `backend/api/upload_gate.py` |
| 3. Same canonical pipeline | `create_document_and_enqueue(...)` **`:1311`** (imported from `api.v3_documents`) | `backend/api/v3_consultants.py` |
| 4. Read-back surfaces | `GET /api/v3/consultants/clients/{client_id}/documents` `:1252`; `GET …/processing/items` `:1330+`; `GET …/processing/status` | `backend/api/v3_consultants.py` |

**Material point [CODE]:** the consultant uploads **into the client
organisation** (`org_id = actor.organization_id`, the client org), and
`create_document_and_enqueue` passes `provenance=actor.provenance()` so the
consultant origin is recorded — but **nothing in this path notifies anyone**.

### 2.3 Shared ingestion — `enqueue_document_processing`

`backend/api/v3_documents.py:506` **[CODE]**. Its own docstring states the shared
contract: *"so a directly-uploaded (signed-URL) document enters exactly the same
durable pipeline as a server-proxied upload: extraction batch/item →
`document_processing_queue` job → OCR prefill."*

| Sub-step | Symbol / line | Result |
| --- | --- | --- |
| Grouping batch | `repos.manual_extraction.list_batches(...)` `:76`; reuse `batch_name == "Uploads"` with status `open`/`in_progress` `:77–85`; else `create_batch(...)` `:87` | **One reusable "Uploads" `manual_extraction_batches` row per organisation** |
| Work item | `repos.manual_extraction.create_item(...)` | a `manual_extraction_items` row, **`pending`** |
| Automatic job | `document_processing_queue` insert (via `repos.processing…`) → `enqueue_state["automatic_processing"]="enqueued"` | durable automatic-processing job |
| MP posture (record only) | `from services.manual_processing_routing import ManualProcessingRouter` `:155`; `await ManualProcessingRouter(repos).resolve(organization_id)` `:157`; `enqueue_state["manual_processing"] = {entitled, enabled, effective, configured, outcome}` `:158–164` | the **posture is recorded**, nothing is routed |
| Persist | `repos.files.update_metadata(document_id, record_metadata)` `:172–179` | `organization_files.metadata` JSONB (no schema change) |
| OCR prefill | `:190+` (deferred for direct uploads, `content is None`) | item stays `pending` for human entry on OCR failure |

> **Decisive comment in the code itself [CODE]** — `backend/api/v3_documents.py:144–153`:
> *"The item created above is the SHARED-INGESTION carrier the automatic job
> references (`source_item_id`) and must therefore always exist for provenance;
> **it is NOT a manual-processing work item and is never placed in a Processing
> Entity queue here.** Whether a later automatic-extraction FAILURE may route to
> a Processing Entity is decided entirely server-side by the entitlement + FIN-06
> governance + configured-processor chain (`services.manual_processing_routing`)
> and is recorded below so the customer's routing posture is never silent."*

**Therefore: uploading a document (customer or consultant) does *not* itself
create Manual Processing work, and does *not* notify anyone.** [CODE]

### 2.4 The worker and the Manual Processing fallback routing (Event B's real trigger)

| Step | Symbol / line | File |
| --- | --- | --- |
| Durable loop | `AutomaticProcessingWorker._run_loop` → `_tick` **`:122`** | `backend/workers/automatic_processing.py` |
| Liveness | `repos.processing.record_worker_heartbeat(...)` `:134` | "X1 (M2)" — liveness on **every** tick |
| Operational alerting | `OperationalAlertingService(...).evaluate_and_dispatch(...)` `:147–155` (background task) | X2 — internal staff only |
| Claim + process | `repos.processing.claim_next(...)` `:158` → `_process_one(job, token)` → `AutomaticProcessingService.process_job` | — |
| **MP fallback boundary** | `await self._route_manual_processing_fallback(final)` **`:228`**; helper `:229`; `ManualProcessingRouter(self._repos).route_failed_job(job)` **`:239`** | the only automatic trigger into MP |
| Failure stages | `FAILURE_STAGES = ("blocked", "failed")` `:70` | `backend/services/manual_processing_routing.py` |
| Decision chain | subscription entitlement → FIN-06 governance (`most-specific-wins`) → `manual_processing_processors` configured PE; `effective = entitled AND enabled` | `ManualProcessingRouter` class `:73`; `resolve()` / `route_failed_job()` |
| **Writes on route** | `repos.manual_extraction.work_item_open(item_id=…, action="assign", assignee_kind="processing_entity", assigned_to=None, processing_entity_id=…, actor=SYSTEM_ACTOR, actor_domain="internal_staff", close_action="superseded")` **`:226`** | the **D38 `work_item_assignments` ledger** — *no parallel task system* |
| Audit on route | `repos.audit.record(AuditEntry(..., action="manual_processing:auto_routed", …))` **`:237–240`** with the full decision (`job_id`, `failure_stage`, `processing_entity_id`, `entitlement_source`, `plan_code`, `governance_source_level`, …) | the **existing append-only `audit_trail`** |
| Non-route outcomes (audit only) | `manual_processing:auto_route_denied` / `manual_processing:auto_route_blocked_no_processor` (`_audit_skip` `:395–436`); `processor_not_active`; `human_assignment_preserved` (`:204–219`) | same ledger |
| Idempotency | if the configured entity already holds the open assignment → `{"routed": True, "idempotent": True}` `:187–199` | retries/requeues/restarts cannot duplicate work |
| **Notifications** | **none** — the module docstring states it writes *only* through the existing D38 ledger and the existing audit infrastructure | verified: no `notifications` reference in the module |

**Consequence [CODE]:** when a consultant-uploaded document's automatic
extraction ends `blocked`/`failed` and MP is effective with a configured PE, the
item is **assigned to that Processing Entity and audited** — and **no actor is
notified**: not the PE, not the consultant, not internal ops.

### 2.5 The other (human-initiated) ways work enters Manual Processing

| Path | Route / symbol | Notification today |
| --- | --- | --- |
| Create a manual-extraction batch | `POST /api/v3/manual-extraction/batches` → `create_batch` `:46` (`require_org_admin()` + `ensure_manual_processing_allowed`) → `repos.manual_extraction.create_batch` | **None** [CODE] |
| Add an item to a batch | `POST /api/v3/manual-extraction/batches/{batch_id}/items` → `create_item` `:136` | **None** |
| **Batch-level** assignment to an internal operator **or** a PE (D22) | `POST /api/v3/ops/batches/{batch_id}/assign` → `assign_batch` **`backend/api/v3_operations.py:2226`** → `repos.manual_extraction.update_batch(status="in_progress", assigned_to=… \| entity_id=…)` + `_record_batch_assignment_audit(...)` | **None** [CODE] |
| **Item-level** assignment (D38) | `POST /api/v3/ops/items/{item_id}/work/{claim\|assign\|reassign\|recover}` → `backend/api/v3_operations.py:2777 / 2792 / 2809 / 2820` → `backend/services/work_items.py::ops_claim_item` `:130` / `ops_assign_item` `:158` / `ops_reassign_item` `:138` / `ops_recover_item` `:151` | **Internal-staff target only** → `work_item.assigned` (§3.4) |
| **PE-side** claim / release / complete (D38) | `POST /api/v3/pe/items/{item_id}/work/{claim\|release\|complete}` → `backend/api/v3_pe.py:617 / 634 / 649` → `pe_claim_item` `:354` / `pe_release_item` `:391` / `pe_complete_item` `:421` | **None** (no producer at all) |
| Read the assigned work (pull) | `GET /api/v3/pe/work` `backend/api/v3_pe.py:149`; `GET …/pe/batches/{batch_id}/items` `:188`; ops: `GET /api/v3/ops/batches/{batch_id}/items` `:2206`, `GET /api/v3/ops/next-item` `:2567` | pull-only |

**[CODE]** `ops_assign_item` is the **only** assignment function that notifies,
and only conditionally (`:121–126`):

```python
if assigned_to is not None and assigned_to != actor_user_id:   # INTERNAL STAFF target only
    await _notify_assignee(repos, user_id=assigned_to,
        event_key=f"work_item:{action}:{item_id}:{new_row['id']}",
        item_id=item_id, action=action, actor_domain=actor_domain)
```

A **Processing Entity** target (`target_entity_id`) never reaches `_notify_assignee`.

---

## §3 Existing notification and communication architecture

### 3.1 Persistence and contract [DDL]**[CODE]**

| Layer | Artefact | Evidence |
| --- | --- | --- |
| Table | `public.notifications` — **per-recipient** rows: `recipient_type`, `recipient_id`, `notification_type`, `title`, `message`, `priority`, `link`, `metadata`, `is_read`, `read_at`, `is_dismissed`, `dismissed_at`, `created_at`, `updated_at` | `CarbonTally_DB_Schema_V3M2.sql:1823–1841`; `supabase/migrations/00000000000000_init_schema.sql:1409` |
| Delivery table | `public.notification_delivery` (per-attempt: `channel`, `status`, `sent_at`, `delivered_at`, `error_message`, `metadata`) | same init schema `:1429`; written by `NotificationsRepository.record_delivery` |
| Idempotency | `notifications.event_key` + `notifications.actor_domain`; **`uq_notifications_event_key` = UNIQUE (recipient_id, event_key) WHERE event_key IS NOT NULL** | `supabase/migrations/20260902050000_phase5_notification_event_key.sql:6–16`; inbox index `ix_notifications_recipient_inbox` `:16` |
| Repository | `backend/data/notifications.py` — `create` `:71`, **`create_idempotent` `:116`**, `mark_read` `:100`, `mark_all_read` `:109`, `support_staff_user_ids` `:169`, `entity_participant_user_ids` `:180`, `internal_ops_user_ids` `:213`, `email_for_user` `:229`, `record_delivery` `:237` | read directly |
| Read API | `backend/api/v3_notifications.py` — `GET /api/v3/notifications` `:17` (clamped `limit 1..500`, newest-first), `POST /{id}/read` `:56`, `POST /read-all` `:68`, all `require_auth()` and **server-side scoped to `current_user.user_id`** | read directly |
| Frontend inbox | `frontend/src/v3/NotificationsPage.jsx` (`/notifications`, route `frontend/src/App.js:2129`); PE bell `frontend/src/v3/pe/PeNotificationsBell.jsx`; wrappers `frontend/src/v3/api.js:1320–1337` | read directly |
| Email | `notification_delivery` rows written through the canonical platform mailer; **only the X2 operational-alerting path performs email fan-out** | `backend/services/operational_alerting.py:168–235` |

### 3.2 Delivery semantics (ratified) [DOC]**[CODE]**

* Producers are **best-effort and post-commit**: the business action is already
  committed, a producer failure is logged and never fatal
  (`work_items.py:68–69`; `v3_messaging.py:527–528`; `consultant_lifecycle.py:160–165`).
* Notification delivery is **not transactional** with the business operation — by design.
* Duplicate prevention is **the database index** (`ON CONFLICT (recipient_id, event_key) DO NOTHING`).
* Retry exists **only** for X2 email delivery: **3 attempts over ≈15 min**, then `status='failed'` + `error_message` + attempt count, then stop.
* **Producers create the in-product row only**; the in-product **+ email** fan-out is what X2's alerting service adds [INFER from the producer inventory, consistent with the P-1/P-2 fact-find §3.5].

### 3.3 Existing notification **producers** (the complete, verified set) [CODE]

| Producer (file : line) | Recipient(s) derived server-side | `notification_type` |
| --- | --- | --- |
| `backend/services/work_items.py:58` (`_notify_assignee`, called only from `ops_assign_item`) | **the internal-staff assignee only** | `work_item.assigned` (priority 30, `link=/ops/items/{item_id}`) |
| `backend/services/consultant_lifecycle.py:187` (`_emit`) — five ratified events (`:287–421`) | firm members (`_firm_recipient_user_ids`), engaged firms (`_engaged_firm_ids`), internal ops (`_internal_ops_recipient_user_ids`), client owner/admin per emitter | `consultant.lifecycle.{accepted,submitted_to_qc,qc_outcome,customer_decision,rework}` |
| `backend/services/automatic_processing.py:1940/1953` (`_notify`), called once at **`:1797`** | the org's members whose role is `owner`/`admin` | `processing.completed` (`link=/processing/jobs/{job.id}`) |
| `backend/api/v3_messaging.py:519–526` | the **opposite side** of a PE↔CarbonTally conversation (`support_staff_user_ids()` / `entity_participant_user_ids(...)`) | `pe_msg.message` / `pe_msg.ops_reply` |
| `backend/services/operational_alerting.py:138` (=X2) | internal staff (`support_staff_user_ids`) | `ops_alert_queue_backlog` / `_worker_stale` / `_sla_breach` / `_retry_exhausted` |
| `backend/api/v3_backups.py:187`, `backend/main.py:337` | the configured backup recipient | `backup` |
| `backend/api/v3_discovery.py:691` | the acting user (adoption confirmation) | `general` |

**No producer exists in, or is called by:**
`backend/services/manual_processing_routing.py`, `backend/api/manual_processing_admin.py`,
`backend/api/manual_processing_auth.py`, `backend/api/v3_manual_processing_coverage.py`,
`backend/data/manual_processing.py`, `backend/domain/manual_processing.py`,
`backend/api/v3_manual_extraction.py`, `backend/api/v3_pe.py`. **[CODE]**

### 3.4 The one assignment notification, in full [CODE]

`backend/services/work_items.py:51–69`:

```python
async def _notify_assignee(repos, *, user_id, event_key, item_id, action, actor_domain):
    """Best-effort D40 notification for an internal assignment event. …"""
    try:
        await repos.notifications.create_idempotent(
            user_id, event_key,
            notification_type="work_item.assigned",
            title="Work item assigned",
            message=f"Work item assigned to you ({action})",
            priority=30, link=f"/ops/items/{item_id}", actor_domain=actor_domain)
    except Exception:
        _log.warning("notification producer failed for work_item %s", item_id)
```

* Recipient = **the internal CarbonTally staff user the item was assigned to**.
* It is **not** produced for a Processing-Entity target, **not** produced for the
  acting user themselves, and **not** produced by `pe_claim/release/complete`.
* The deep link `/ops/items/{item_id}` **does** resolve (`frontend/src/App.js:2211`).
* **No test asserts this producer** (`grep -rn 'work_item.assigned' backend/tests` → no matches). [CODE]

### 3.5 Supabase Realtime — what is actually configured and used [CODE]

| Consumer | Channel / table / filter | Actor scope | Used by |
| --- | --- | --- | --- |
| **V3 messaging (the live, current use)** | `supabase.channel(...)` + `postgres_changes` on **`messages`** | conversation-scoped | `frontend/src/v3/messaging/useConversationRealtime.js:17–45`, imported by `frontend/src/v3/customer/MessagingPage.jsx:12`, `frontend/src/v3/consultant/ClientMessagingTab.jsx:10`, `frontend/src/v3/ops/OpsMessagingTab.jsx:15` |
| App-wide legacy realtime provider | `.channel('ct-v3-notifications')` → `postgres_changes` INSERT on **`notifications`** with **`filter: user_id=eq.${user.id}`** `:300–320`; `.channel('documents_${org.id}')` → `documents` `:427+`; `messages` unread count `:101–150`; `presence` `:170+` | app-wide, mounted by `frontend/src/App.js:90/1959` (`RealtimeProviderWrapper`, defined `RealtimeContext.jsx:492`) | the customer/consultant/ops SPA shell |
| Legacy admin CRA | `notifications` (`user_id` filter), `manual_review_queue`, `customer_documents` | admin only | `admin/src/pages/admin/WorkHub.jsx:116–135`, `LiveQueueStats.jsx:136–147`, `admin/src/context/RealtimeContext.jsx:20–124` |
| Legacy/orphaned modules (no live importer found) | `frontend/src/lib/realtime/manager.js` (org/staff/conversation channels), `frontend/src/hooks/useNotifications.js` | — | `grep` for importers of `lib/realtime` / `hooks/useNotifications` → **none** in `frontend/src` [CODE] |

**[CODE] Material defects in the notification realtime path (not introduced here):**

1. The subscription filter is `user_id=eq.${user.id}`, but `public.notifications`
   has **no `user_id` column** — it has `recipient_id` / `recipient_type`
   (`CarbonTally_DB_Schema_V3M2.sql:1823–1841`). The same wrong filter is used in
   the admin app.
2. The code itself concedes the fallback (`RealtimeContext.jsx:302–304`):
   *"Best-effort live delivery: when Realtime can deliver rows this keeps the bell
   live; if RLS blocks it, the API refetch on window focus is the deterministic
   fallback (never a console error)"*, and the subscribe callback explicitly
   tolerates `CHANNEL_ERROR` / `TIMED_OUT`.
3. **Publication membership is not declared anywhere in the repository**
   (`grep 'CREATE PUBLICATION\|ALTER PUBLICATION … ADD TABLE'` → none; only
   `ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres"` in the V3M2 dump
   `:5310`). Membership of `messages`/`conversations` is recorded as a
   **deployment/dashboard** item in `docs/audit/cline/CARBONTALLY_V3_D27_D19_FINAL_REPORT.md:199–200`
   ("documented in D26 audit §42"), and the workspace-access audit notes
   *"`supabase_realtime` is not declared in the schema SQL and could not be
   confirmed against the live DB"* (`…ACTOR_WORKSPACE_ACCESS_MODEL.md:2570–2572`). **[UNVERIFIED]** in this read-only pass.

**There is no Realtime subscription for work items, batches, assignments,
Manual Processing routing, or the D38 ledger.** [CODE]

### 3.6 What "real-time" means in the existing architecture

**[CODE]** For the manual-processing/PE/ops surfaces the answer is **not**
Realtime: it is **pull + polling**:

| Surface | Freshness mechanism | Evidence |
| --- | --- | --- |
| Customer Processing page | `setInterval(..., 10000)` while work is in flight | `frontend/src/v3/customer/ProcessingPage.jsx:101` |
| Customer Processing item workspace | timer | `frontend/src/v3/customer/ProcessingItemWorkspace.jsx:195` |
| Consultant client-processing view | `setInterval(..., 10000)` while in flight, reading `getClientProcessingItems` / `getClientProcessingStatus` | `frontend/src/v3/consultant/ConsultantPage.jsx:279–291` |
| Ops operator queue | load on mount + explicit refresh (no timer) | `frontend/src/v3/ops/OperatorQueue.jsx:54,72` |
| PE work items | load on mount + `refresh` state (no timer) | `frontend/src/v3/pe/PeWorkItemsPage.jsx:66,89` |
| PE notification bell | fetch on mount and on open only (no Realtime, no polling) | `frontend/src/v3/pe/PeNotificationsBell.jsx:25–40` |
| Messaging (V3) | **Supabase Realtime** `postgres_changes` on `messages` | §3.5 row 1 |

**Durability [CODE]:** every producer writes a **durable `notifications` row**
first; Realtime is only an (optional, currently mis-filtered) *signal* on top of
it. Therefore the durable artefact survives an offline actor — an offline actor
recovers state by reading the inbox API / refreshing the queue, not from
Realtime. **Message-based realtime is not durable by itself** [INFER, consistent
with the `consultant_lifecycle.py` docstring: *"Durable, not ephemeral… The
in-process `EventBus` is deliberately NOT used (fire-and-forget, non-durable)"*].

### 3.7 Internal operational alerting (X2) — scope, recipients, thresholds [CODE]**[DOC]**

| Aspect | Finding |
| --- | --- |
| Where it runs | once per automatic-processing worker tick, as a background task (`backend/workers/automatic_processing.py:147–155`) |
| Conditions (PO `X2-D1`, all three) | `QUEUE_BACKLOG`, `WORKER_STALE`, `RETRY_EXHAUSTED` (+ `SLA_BREACH` only from the configured setting) — `backend/domain/operational_alerts.py:55–66` |
| Thresholds (PO-supplied, not invented) | backlog **> 100** waiting `:39`; worker stale **> 900 s** `:42`; cooldown **1/hour** `:45`; provider outage excluded (`PX-4`) |
| Recipients (`PX-6`) | **internal CarbonTally operations only** — no customer/consultant/PE recipients |
| Channels | in-product + email, 3 attempts ≈15 min then `status='failed'` (`backend/services/operational_alerting.py:135–235`) |
| Dedup | `event_key = ops-alert::<CONDITION>::<YYYYMMDDTHH>` → the existing `uq_notifications_event_key` index (`domain/operational_alerts.py:111–121`) |
| Scope | **queue-level and platform-level**, not per-batch/per-item, and **not** Manual-Processing-entry specific |

---

## §4 Manual Processing workflow — exactly what happens on a consultant upload

**Scenario:** a consultant uploads a document for Client A; the item's automatic
extraction fails; MP is effective for Client A with a configured PE.

| # | What happens | Evidence | Notification |
| --- | --- | --- | --- |
| 1 | Consultant uploads → `upload_client_document` route | `v3_consultants.py:1275` | none |
| 2 | Upload gate authorises (active D15 grant, same firm, `can_upload_documents`) | `api/upload_gate.py` | none |
| 3 | Document stored under the **client org**; `create_document_and_enqueue` runs the security gate + acceptance audit | `v3_documents.py` (`create_document_and_enqueue`) | none |
| 4 | `enqueue_document_processing` **reuses/creates the org's "Uploads" batch** and creates a `pending` `manual_extraction_items` row | `v3_documents.py:76–90` | none |
| 5 | A durable `document_processing_queue` job is enqueued; MP **posture only** is recorded on the document metadata | `v3_documents.py:155–179` | none |
| 6 | The **item is explicitly NOT a MP work item** at this point | code comment `v3_documents.py:144–153` | none |
| 7 | Worker claims and processes the job | `workers/automatic_processing.py:158` | `processing.completed` to **org owner/admin** if it *succeeds* (`:1797`) |
| 8 | Job ends `blocked`/`failed` → `_route_manual_processing_fallback` | `workers/automatic_processing.py:228,239` | none for the failure itself |
| 9 | `route_failed_job` resolves entitlement → FIN-06 enablement → configured PE; `effective = entitled AND enabled` | `services/manual_processing_routing.py:73+` | none |
| 10 | **Work is created**: `work_item_open(... assignee_kind="processing_entity", processing_entity_id=<PE> ...)` on the D38 ledger | `manual_processing_routing.py:226` | **none** |
| 11 | **Decision is audited**: `manual_processing:auto_routed` (+ `…auto_route_denied` / `…blocked_no_processor` when it cannot route) | `manual_processing_routing.py:237–240`, `:395–436` | none |
| 12 | The PE discovers the work by **pulling** `GET /api/v3/pe/work` (ops: `GET /api/v3/ops/batches/{batch_id}/items` / `…/next-item`); the PE work-items page loads on mount only | `v3_pe.py:149`; `v3_operations.py:2206,2567`; `frontend/src/v3/pe/PeWorkItemsPage.jsx:89` | **none** |
| 13 | The consultant discovers status by **polling** the client-processing endpoints every 10 s while work is in flight | `frontend/src/v3/consultant/ConsultantPage.jsx:279–291` | **none** |

**Also true (and important):** if the automatic pipeline *succeeds*, the **client
org's owners/admins** receive `processing.completed` (`automatic_processing.py:1797`).
That is an **automatic-processing completion** notification to the **customer** —
not a Manual-Processing-entry notification — and the **consultant who uploaded**
receives nothing from it.

**Therefore, Event B ("a document batch enters Manual Processing") currently has
exactly one outcome: work created + audit written + no actor notified.** [CODE]

---

## §5 Actor matrix

Recipients below are only those the **existing** authorization/workflow model can
already derive server-side; none were invented.

| Actor | Current notification/communication for a batch entering MP | Evidence |
| --- | --- | --- |
| **Submitting consultant** | **None.** The route returns the document; no producer exists on the upload path or the routing path. Status is discovered by 10 s polling of the client-processing endpoints. | `v3_consultants.py:1275–1330`; `manual_processing_routing.py` (no producers); `ConsultantPage.jsx:279` |
| **Responsible consultant / consultant firm** | **None for this event.** The firm *is* resolvable server-side (`consultants.list_firm_members(firm_id)`) and *is* used by the **D11 lifecycle** producers — but those fire on QC/review/customer-decision routes only, never on upload or MP routing. Not "all firm members get notified": recipients are resolved per event. | `consultant_lifecycle.py:69–108,187`; callers `v3_operations.py:2189–2197`, `v3_processing_workflow.py:682,823,1054`, `v3_organizations.py:747`, `v3_reports.py:1058+` |
| **Assigned PE / processor** | **None.** Automatic fallback routing writes the D38 assignment + audit and stops. PE-side claim/release/complete also produce no notification. The PE discovers work by pull (`GET /api/v3/pe/work`); its bell fetches only on mount/open. | `manual_processing_routing.py:226–240`; `work_items.py:354/391/421`; `v3_pe.py:149`; `PeNotificationsBell.jsx:25–40` |
| **Relevant internal operations staff** | **Indirect only.** (a) Item-level assignment **to an internal staff user** → `work_item.assigned` to that user (`work_items.py:121–126`). (b) X2 `ops_alert_*` for **queue-level** backlog / worker-stale / retry-exhausted / SLA. Neither is triggered by "a batch entered MP", and neither is per-batch or per-PE. | §3.3, §3.4, §3.7 |
| **Client** | **No MP notification path exists.** The client org's owners/admins can receive `processing.completed` for that org's own *automatic* completions. The PO context (consultants upload on behalf of clients; clients do not access CarbonTally for this workflow) is **not contradicted** by any implementation — and **no client notification is introduced or proposed here**. | `automatic_processing.py:1797`; no producer in `manual_processing_routing.py` / `v3_pe.py` / `v3_manual_extraction.py` |

**Explicitly *not* assumed:** that every firm member should be notified; that the
PE should be notified; that clients should be notified. None of these is
established by the repository. [UNVERIFIED as a requirement]

---

## §6 Event matrix

| Event | Current behaviour | Existing mechanism |
| --- | --- | --- |
| **A1 — Coverage allocation** (consultant allocates a client; admin allocates on the firm's behalf) | **Audit only.** No notification; no response field claims one. | `POST /api/v3/consultants/me/manual-processing/allocations` (`v3_manual_processing_coverage.py:266`) → audit `manual_processing:allocation_created` (`:350`); `POST /api/v3/admin/manual-processing/coverage/allocations` (`manual_processing_admin.py:676`) → audit `:761` |
| **A2 — Coverage release** | **Audit only.** | `DELETE /api/v3/consultants/me/manual-processing/allocations/{allocation_id}` (`v3_manual_processing_coverage.py:377`) → audit `manual_processing:allocation_released` (`:408`); admin `DELETE` (`manual_processing_admin.py:787`) → audit `:804` |
| **A3 — Governance / processor configuration changes** (FIN-06 grant set/removed, processor set/removed, queued batches cancelled) | **Audit only.** | `manual_processing_admin.py` actions `:335 grant_set`, `:385 grant_removed`, `:574 processor_set`, `:617 processor_removed`, `:321 queued_batches_cancelled`, `:278`/`:540` `*_rejected_not_entitled` |
| **B — Document batch enters Manual Processing** — automatic fallback routed | **Work created; audit written; no actor notified.** | `route_failed_job` → `work_item_open` (`manual_processing_routing.py:226`) + audit `manual_processing:auto_routed` (`:240`); **no producer** |
| **B′ — Batch/entity assignment by ops, or batch creation** | **Work created; audit written; no actor notified.** | `POST /api/v3/ops/batches/{batch_id}/assign` (`v3_operations.py:2226`) + `_record_batch_assignment_audit`; `POST /api/v3/manual-extraction/batches` (`v3_manual_extraction.py:46`) |
| **B″ — Item-level assignment** | **Internal-staff target → notified; PE target → not notified.** | `ops_assign_item` → `work_item.assigned` (`work_items.py:121–126`); `pe_claim/release/complete` → audit only (`work_items.py:354/391/421`) |
| **B‴ — Routing could not happen** (`no_processor_configured`, `auto_route_denied`, `processor_not_active`, `human_assignment_preserved`) | **Audit only** — i.e. exactly the "work is waiting and nobody was told" case. | `_audit_skip` (`manual_processing_routing.py:395–436`), `:170–184`, `:204–219` |
| **C1 — Automatic processing completed** | **Customer org owners/admins notified** (once per job). | `automatic_processing.py:1797` → `_notify` → `processing.completed` (`:1953`) |
| **C2 — Processing stage changes** (PE/ops: start, extract, map, validate, calculate, status, pe-review, pe-qc) | **No notification from any of these routes.** | `v3_pe.py:225–488`, `v3_operations.py:1108–1993` — no producer |
| **C3 — QC outcome / review submission / customer decision / rework** (the consultant lifecycle) | **Notified** (D11, five ratified events) to firm members / internal ops / client owner-admin per emitter. | `consultant_lifecycle.py:287–421`; callers `v3_operations.py:2189–2197`, `v3_processing_workflow.py:682,823,1054`, `v3_organizations.py:747`, `v3_reports.py:1058+` |
| **C4 — Queue-level health problems** (backlog, worker stale, retry exhausted, SLA) | **Internal ops alerted** (in-product + email, hourly cooldown). | X2 (§3.7) |
| **C5 — PE ↔ CarbonTally messaging** | **Counterparty notified.** | `v3_messaging.py:519–526` |

**No new events are proposed here.** Rows A1–A3 are the events the current **P-2**
decision governs. Rows B, B′, B″ and B‴ are the events the PO must now **separate**
from them.

### 6.1 The existing ratified event vocabulary contains no MP-entry event [DOC]

| Decision | Ratified content | Source |
| --- | --- | --- |
| **D11 / D40 notification vocabulary** | Exactly **five** consultant-processing lifecycle events: *engagement accepted · submitted to CarbonTally QC · QC outcome · customer decision · rework*. `PO-PHASE6-D11-20260910` = **A**, implemented in `consultant_lifecycle.py`. **No MP routing / assignment / batch-entry event is in the vocabulary.** | `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md:279–294`, ratification `:501`; `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md:135` |
| **D2 — authoritative MP UI/UX spec** | A **644-line** specification whose sections are coverage/commercial/entitlement screens only (§1–§11). `grep -i 'notif\|alert\|real-time\|realtime\|email'` over it returns **no** notification requirement; the only "Available" matches are coverage-capacity states (`:119,135,196,212,229,235,250,260,300,331,332,348,389,531,613`). | `CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` |
| **NV-10 (the origin of P-2)** | *"Email/notification side-effects — None expected from this surface."* — a statement about the **MP coverage/allocation surface**. | `CT-MP-SUB-004-independent-verification-report.md:666` |

**Conclusion:** no ratified CarbonTally decision requires, or forbids, a
notification for *"a document batch entering Manual Processing"*. That question
is **currently undecided**. [DOC]

---

## §7 Requirement classification

**Classification of the document-batch notification requirement:**

> ## **D. REQUIREMENT NOT ESTABLISHED**
>
> The repository does **not** establish that a notification is required when a
> document batch enters Manual Processing. The question requires a **new PO
> decision**.
>
> **Conditional finding (not the classification):** *if* the PO were to require
> such a notification, the current implementation would be **C. NOT SATISFIED** —
> the workflow creates the Manual Processing work (D38 assignment + audit) and
> **no relevant actor receives operational communication** for that event.
> There is no actor subset that is partially covered, so **B. PARTIALLY
> SATISFIED** would be wrong, and **A. ALREADY SATISFIED** is factually false.

### 7.1 Why D and not A/B/C (evidence-based, not industry-assumption)

| Question | Answer | Basis |
| --- | --- | --- |
| Does a ratified CarbonTally decision require a notification when a batch enters MP? | **No** — the D11/D40 vocabulary has five *consultant-lifecycle* events and no MP-entry event; D2 requires none; NV-10's "none expected" refers to the coverage/allocation surface. | §6.1 [DOC] |
| Does the MP implementation emit any notification for that event? | **No** — no producer exists on the routing path or the upload path. | §2.4, §3.3 [CODE] |
| Is the work nevertheless created and traceable? | **Yes** — D38 `work_item_assignments` row + append-only `manual_processing:auto_routed` audit entry with the full decision. | §2.4 [CODE] |
| Is any actor able to *discover* the work without a notification? | **Yes, by pull/poll** — PE `GET /api/v3/pe/work`; ops queue endpoints; consultant 10 s polling. | §3.6 [CODE] |
| Is there an existing *internal* safety net? | **Yes, but not for this event** — X2 alerts on **queue-level** conditions only, and item-level assignment notifies **only an internal-staff target**. | §3.7, §3.4 [CODE] |
| Would "no notification" be a security or authorization problem? | **No** — access is unaffected; the notification table is not an authorization mechanism (`PeNotificationsBell.jsx` header: *"notifications are never an access-control mechanism"*). | [CODE]/[DOC] |

### 7.2 What the repository *does* establish

1. The notification **subsystem** is complete, durable, idempotent, recipient-scoped and API-exposed (§3.1–3.3) **[CODE]**.
2. The MP/upload/routing path deliberately uses **audit + ledger**, not notifications (§2.3, §2.4) **[CODE]**.
3. The "batch enters MP" work is **created and observable by pull** — the current product simply does not *push* it (§3.6) **[CODE]**.
4. No platform mechanism exists that would deliver such a push today: the only notification Realtime subscription for V3 **filters on a non-existent column and is documented as best-effort with an API fallback** (§3.5) **[CODE]**.

### 7.3 Smallest possible decision question (not answered here)

> **Does the PO authorise near-real-time operational notification to the assigned
> Processing Entity — and, if so, the submitting/responsible consultant — when a
> document batch/item **enters Manual Processing** (i.e. when automatic-extraction
> fallback routing creates Manual Processing work, or an operator assigns a batch
> or item to a Processing Entity), as distinct from MP coverage allocation/release,
> which remains audit-only?**

Deliberately **not** answered, and deliberately **not** widened to a recipient
matrix, a channel choice, a preference system, or an email policy — those would be
follow-on decisions only if the answer above is "yes".

---

## §8 Impact on the P-2 decision record

### 8.1 Finding

> ## **Option 2 — the current P-2 wording is too broad and should be amended to distinguish coverage allocation/release from document-batch operational notifications.**

**Why.** P-2 is *intended* to cover the **MP coverage/allocation surface** (NV-10),
and its supporting evidence — the `grep` over `manual_processing_admin.py`,
`manual_processing_auth.py`, `data/manual_processing.py`, `domain/manual_processing.py`
— proves exactly that. But three of its sentences are drafted at the level of
**"Manual Processing" as a whole**, so a reader (or a verifier) can legitimately
read them as closing the separate question of a batch entering MP:

| Sentence in `…PO-DECISIONS-01.md` | Line | Over-broad reading risk |
| --- | --- | --- |
| *"Manual Processing proactive notifications are NOT required for this release."* | `:162` | reads as **all** MP notifications, not just allocation/release |
| *"No new MP notification event types are authorised by this decision."* | `:232` | could be read as forbidding an MP-entry event |
| *"Creating any new notification behaviour (event, recipient matrix, preference, provider, outbox, worker) — NOT CREATED"* / *"No new notification behaviour is created."* | `:279`, `:291` | could be read as an absolute bar on any future MP notification |

Ambiguity is a real governance defect here, because:

* the P-2 `grep` evidence set **does not include** `services/manual_processing_routing.py`,
  `backend/workers/automatic_processing.py`, `services/work_items.py`, or the upload
  pipeline — i.e. the files where "a batch enters MP" actually happens (§2.3–2.5);
* the routing path **does** create operational work with **no** notification (§2.4, §4);
* no ratified decision covers that event (§6.1), so nothing else closes it either.

### 8.2 Proposed **minimum** wording change — **PROPOSED, NOT APPLIED**

Append **one** scope paragraph to §5 of
`CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` (immediately after §5.1) and
**one** clarifying clause to §6 — nothing else. No P-1 text, no
acceptance-target rewrite, no prohibition removal.

**Proposed addition to §5 (new §5.1a):**

> **Scope limit (added by the Notification fact-finding 02).** P-2, including every
> prohibition in §6 and §8.1, applies **only** to **Manual Processing coverage
> allocation and release** transitions (NV-10) — i.e. the
> `manual_processing:allocation_created` / `manual_processing:allocation_released`
> family. P-2 does **not** determine whether any actor must be notified when a
> **document batch or item enters Manual Processing** (automatic-extraction
> fallback routing; a batch/entity or item assignment by operations). That separate
> question is **OPEN — PO DECISION REQUIRED**, and remains unclosed by this record.
> P-2 is not to be read, by a verifier or an agent, as either requiring or
> prohibiting such a notification.

**Proposed one-clause amendment to §6 item 5** (currently *"No new MP notification
event types are authorised by this decision."*):

> 5. **No new MP *coverage* notification event types** are authorised by this decision
>    (see the §5.1a scope limit: this does not address a document batch entering
>    Manual Processing).

**Not proposed:** any change to the **decision** itself (allocation/release stay
audit-only), to NV-10's status, to any P-1 text, or to the five explicit
prohibition statements in §8.1.

### 8.3 What the PO is not being asked to do

* Not to authorise a notification (that is the §7.3 question, if the PO chooses to answer it).
* Not to reopen FIN-06 governance, the D38 assignment model, or the D11 vocabulary.
* Not to change an audit-only behaviour that is already correct and deliberate.

---

## §9 Independent-verification impact (what CoStrict/OHD must verify **after** the PO finalises)

### 9.1 Verification that **stays exactly as it is** (NV-10 / P-2, unchanged)

From `…PO-DECISIONS-01.md` §10.2 (must still pass, unchanged by this report):

1. The MP coverage `grep` over `manual_processing_admin.py`, `manual_processing_auth.py`,
   `data/manual_processing.py`, `domain/manual_processing.py` → **no** notification matches.
2. Allocate / release / admin-allocate still write the audit events and the
   `notifications` row count is **unchanged**; no response body claims a notification.
3. No real `public.notifications` row is created by an allocation/release operation.
4. No new notification subsystem or provider was introduced.

### 9.2 Verification that must be **extended** because of this fact-find

| # | What to verify | Why | Suggested check |
| --- | --- | --- | --- |
| V1 | **P-2 is not read as covering the MP-entry event.** The verifier must record whether the amendment in §8.2 was applied, and must not treat "no MP notification" as verified for the *routing* event. | The wording risk in §8.1 | Read the amended §5.1a / §6.5; record "applied / not applied" |
| V2 | **The routing path still emits no notification** (current behaviour, unchanged by this fact-find). | Establishes the baseline for any later decision | Exercise `route_failed_job` (or read it): assert the D38 assignment row + `manual_processing:auto_routed` audit exist and that the `notifications` row count is unchanged |
| V3 | **The `no_processor_configured` case is audited and silent.** | It is the worst-case "work is waiting, nobody was told" state | Assert `manual_processing:auto_route_blocked_no_processor` in `audit_trail`; assert no notification row |
| V4 | **Item/batch/entity assignment notifications are exactly as stated** (§2.5, §3.4): an internal-staff target is notified; a PE target is not; PE claim/release/complete never notify. | Prevents an over-claim in either direction | Drive `POST /api/v3/ops/items/{id}/work/assign` with `assigned_to` vs `entity_id`; assert the `work_item.assigned` row exists in only the first case |
| V5 | **Discovery is pull-based**, i.e. the PE sees the work via `GET /api/v3/pe/work` (and the PE bell only refetches on mount/open). | The PO's decision must rest on the *actual* discovery mechanism | Browser/API check on the PE workspace |
| V6 | **Realtime does not currently deliver notifications**: the V3 notification subscription filters on `user_id`, which is **not a column** of `public.notifications`; the code documents an API fallback. | A PO "yes" decision cannot assume live push already works, and a PO "no" decision must not be justified by a broken live path | Inspect the channel filter; confirm the fallback behaviour; **publication membership is an environment check** (§3.5.3), not a repo check |
| V7 | **No client notification path for this workflow** (§5, last row). | The PO context says clients do not use CarbonTally for this workflow | Assert no producer targets client members for MP entry |

### 9.3 If the PO answers §7.3 with **"yes" — notify on MP entry**

Then, and only then, this becomes a **new, separately-scoped work item** (event
name, recipients, idempotent event key, durability, channel, tests), requiring its
own decision record and its own acceptance criteria. Nothing in this report
authorises it, and no part of CT-MP-SUB-004's current acceptance target may be
read as delivering it.

### 9.4 If the PO answers §7.3 with **"no" — pull remains sufficient**

Then the amendment in §8.2 (or an equivalent scoping statement) is still required,
because otherwise a verifier cannot tell whether "no MP notifications" was the
*decision* or an *oversight* — and §4 shows there is currently a genuine gap
between "work was created" and "somebody was told".

---

## §10 Evidence index (every substantive claim)

### 10.1 Upload / ingestion

| Claim | Exact artefact |
| --- | --- |
| Customer direct-upload routes | `backend/api/v3_document_uploads.py` — `start_organization_upload` `:792`, `complete_organization_upload` `:816`, `abandon_organization_upload` `:835`; helper `_complete_upload` `:405`, `_abandon_pending_upload` `:686` |
| Consultant upload (CON-2/3) route | `backend/api/v3_consultants.py:1275` `upload_client_document` → `authorize_consultant_upload` `:1294` → `create_document_and_enqueue` `:1311` |
| Upload authorisation | `backend/api/upload_gate.py` (`authorize_consultant_upload`); policy via `utils/upload_limits.py` `resolve_policy` |
| Shared enqueue + "Uploads" batch + posture | `backend/api/v3_documents.py` — `create_document_and_enqueue`, `enqueue_document_processing` `:506`, batch reuse `:76–90`, "NOT a MP work item" comment `:144–153`, `ManualProcessingRouter(...).resolve(...)` `:155–164`, metadata write `:172–179` |
| Manual-extraction entry routes | `backend/api/v3_manual_extraction.py` — `create_batch` `:46`, `create_item` `:136` |

### 10.2 Worker and Manual Processing routing

| Claim | Exact artefact |
| --- | --- |
| Worker loop / heartbeat / alerting / claim | `backend/workers/automatic_processing.py` — `_tick` `:122`, heartbeat `:134`, X2 dispatch `:147–155`, `claim_next` `:158` |
| MP fallback boundary | same file — call `:228`, `_route_manual_processing_fallback` `:229`, `route_failed_job(job)` `:239` |
| Failure stages / decision chain / ledger / audit | `backend/services/manual_processing_routing.py` — `FAILURE_STAGES` `:70`, `ManualProcessingRouter` `:73`, `SYSTEM_ACTOR` `:59`, `ROUTING_ACTOR_DOMAIN` `:66`, `work_item_open(...)` `:226`, audit `manual_processing:auto_routed` `:237–240`, `_audit_skip` `:395–436`, `human_assignment_preserved` `:204–219`, `processor_not_active` `:170–184` |
| D38 assignment / the one notification | `backend/services/work_items.py` — `_notify_assignee` `:51–69` (create `:58`), `work_item_open` `:101`, notify call `:121–126`; `ops_claim_item` `:130`, `ops_reassign_item` `:138`, `ops_recover_item` `:151`; `pe_claim_item` `:354`, `pe_release_item` `:391`, `pe_complete_item` `:421` |
| Batch-level assignment | `backend/api/v3_operations.py:2226` `assign_batch` (+ `_record_batch_assignment_audit`) |
| Ops / PE work routes | `backend/api/v3_operations.py:2777 / 2792 / 2809 / 2820`; `backend/api/v3_pe.py:617 / 634 / 649`; reads `v3_pe.py:149 / 188`, `v3_operations.py:2206 / 2567` |

### 10.3 Notifications

| Claim | Exact artefact |
| --- | --- |
| Tables + idempotency index | `CarbonTally_DB_Schema_V3M2.sql:1823–1841`; `supabase/migrations/00000000000000_init_schema.sql:1409,1429`; `supabase/migrations/20260902050000_phase5_notification_event_key.sql:6–16` |
| Repository | `backend/data/notifications.py` `:71,100,109,116,169,180,213,229,237,270` |
| Read API | `backend/api/v3_notifications.py:17,56,68`; frontend `frontend/src/v3/api.js:1320–1337`, `frontend/src/v3/NotificationsPage.jsx`, route `frontend/src/App.js:2129` |
| Producers | `work_items.py:58`; `consultant_lifecycle.py:127,187,287–421`; `automatic_processing.py:1797,1940,1953`; `v3_messaging.py:519–526`; `operational_alerting.py:102,138`; `v3_backups.py:187`; `main.py:337`; `v3_discovery.py:691` |
| X2 conditions / thresholds / recipients | `backend/domain/operational_alerts.py:39,42,45,55–66,70–75,78,111–121`; `backend/services/operational_alerting.py:46–235` |
| Realtime (live consumers) | `frontend/src/v3/messaging/useConversationRealtime.js:17–45`; `frontend/src/context/RealtimeContext.jsx:101–150,170,300–320,427+,492`; `frontend/src/App.js:90,1959`; admin `admin/src/pages/admin/WorkHub.jsx:116–135`, `LiveQueueStats.jsx:136–147`, `admin/src/context/RealtimeContext.jsx:20–124` |
| Realtime publication | `CarbonTally_DB_Schema_V3M2.sql:5310` (owner only; no `ADD TABLE` anywhere); `docs/audit/cline/CARBONTALLY_V3_D27_D19_FINAL_REPORT.md:199–200`; `docs/audit/openhands/ui-ux/supporting-evidence/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md:2570–2572` |
| Freshness by polling | `frontend/src/v3/customer/ProcessingPage.jsx:101`; `…/ProcessingItemWorkspace.jsx:195`; `…/consultant/ConsultantPage.jsx:279–291`; `…/ops/OperatorQueue.jsx:54,72`; `…/pe/PeWorkItemsPage.jsx:66,89`; `…/pe/PeNotificationsBell.jsx:25–40` |

### 10.4 Governing decisions

| Claim | Exact artefact |
| --- | --- |
| P-2 wording / prohibitions | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md:159–245,271–291` |
| NV-10 origin | `docs/architecture/CT-MP-SUB-004-independent-verification-report.md:666` |
| D11/D40 vocabulary + ratification | `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md:279–294,501`; `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md:25,135` |
| D2 spec (no notification requirement) | `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` (644 lines, §1–§11) |

### 10.5 Relevant tests (read for coverage, **not modified**)

| Test file | Relevance |
| --- | --- |
| `backend/tests/unit/api/test_manual_processing_routing.py` | Routing behaviour; no notification assertions |
| `backend/tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py` | Coverage allocation + routing; no notification assertions |
| `backend/tests/unit/api/test_v3_work_item_effective_assignment.py` | D38 effective assignment; no notification assertions |
| `backend/tests/unit/api/test_v3_notifications.py` | The notification **inbox API** only |
| `backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py` | The **only** producer-level notification suite (D11) |
| `backend/tests/unit/api/fakes.py:2976–3020` | `MemoryNotifications.create_idempotent` mirrors `uq_notifications_event_key` |
| `grep -rn 'work_item.assigned' backend/tests` | **no matches** → the one assignment producer is untested |

---

## §11 Production-safety verification (explicit)

| Requirement | Status | How it was ensured |
| --- | --- | --- |
| No production DB accessed | **CONFIRMED** | No database client, connection string, `psql`, Supabase CLI or SQL execution was used. No DB credentials were read or needed. All persistence claims come from `.sql` files and repository code |
| No production credentials used | **CONFIRMED** | No `.env`, key, token or session was read or used |
| No production Supabase project accessed | **CONFIRMED** | No network call to a Supabase/local API endpoint; no Realtime connection opened |
| No migration | **CONFIRMED** | No migration was authored or applied. `git status` shows exactly two untracked `supabase/migrations/*.sql` files — `20261030000000_manual_processing_routing.sql` and `20261101000000_ct_mp_sub_003_consultant_coverage.sql` — both **pre-existing** (CT-MP-SUB-003/004 workstream, dated 2026-10-04) and **not** created or modified by this task |
| No deployment | **CONFIRMED** | No build, container or hosting action performed |
| No schema / RLS modification | **CONFIRMED** | No DDL or policy touched |
| No application code modification | **CONFIRMED** | The only new file is this report; the 39 tracked modifications are pre-existing and were **not** touched |
| No tests modified | **CONFIRMED** | No file under `backend/tests/**`, `tests/**`, `frontend/src/**/__tests__/**` was written |
| No fixture modification | **CONFIRMED** | No `tools/demo_lab/**` or seed file was written |
| No commit | **CONFIRMED** | Nothing staged or committed; HEAD remains `375a48dc…` |
| No push | **CONFIRMED** | No remote operation performed |

**Note on `services/work_items.py` / `services/manual_processing_routing.py`:**
both are **unmodified** working-tree files, so the P-2 finding does not depend on
uncommitted work in either. The routing and notification behaviour claimed in §2.4
is therefore true of **both** HEAD and the working tree for those two modules.

---

## §12 Final status

> ## **NOTIFICATION FACT-FINDING COMPLETE — READY FOR PO CLARIFICATION**

**This status means exactly this, and no more:**

1. **Evidence is sufficient** to establish, from the actual CarbonTally working-tree
   source, exactly what happens from a consultant document upload through to
   Manual Processing routing and actor communication (§2, §4).
2. **Event B ("a document batch enters Manual Processing") is not satisfied today**:
   the work is created on the D38 ledger and audited (`manual_processing:auto_routed`)
   but **no relevant actor is notified** (§2.4, §4, §5).
3. **The requirement itself is not established** by any ratified CarbonTally
   decision (§6.1), so the classification is **D — REQUIREMENT NOT ESTABLISHED** (§7),
   and the **smallest PO decision question** is stated in §7.3.
4. **The P-2 wording is too broad** and should be amended with the minimum scoping
   change proposed in §8.2 — **proposed, not applied**.
5. `CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` remains the **authoritative
   record**, unmodified, until the PO decides whether to amend it.

**This report does NOT claim, and must not be read as claiming:**

* implementation complete — **no implementation was performed**;
* production readiness — **not assessed here**;
* independent verification — **this is a fact-find, not an IV**;
* final PO acceptance — **the PO has not been asked yet**;
* that notifications *should* be added — **no product decision was made**.

**Read-only boundary held:** no application code, tests, database, migrations, RLS,
notification configuration, Realtime configuration, UI or product behaviour was
changed; no notification was added or removed; the decision record was not
modified; nothing was committed or pushed (§11).

**Recommended next step:** present §7.3 (the question) and §8.2 (the minimum
wording change) to the PO. If the PO amends P-2, independent verification
(CoStrict/OHD) proceeds with §9.1 unchanged **plus** the §9.2 extension checks.

---

## Appendix A — Findings summary (one line each)

| # | Finding | Class |
| --- | --- | --- |
| F1 | A consultant upload enters the client org's reusable **"Uploads"** `manual_extraction_batches` batch and creates a `pending` `manual_extraction_items` row; the code states this item is **NOT** a MP work item | [CODE] |
| F2 | The upload path records the MP **posture** on the document metadata only (`entitled/enabled/effective/configured/outcome`); it routes nothing and notifies no one | [CODE] |
| F3 | Manual Processing work is created **only** later, by `ManualProcessingRouter.route_failed_job` after an automatic `blocked`/`failed` outcome, or by an operator batch/item assignment | [CODE] |
| F4 | The routing path writes the D38 `work_item_assignments` ledger + `manual_processing:auto_routed` audit and **emits no notification** | [CODE] |
| F5 | The **only** assignment notification in the system (`work_item.assigned`) fires **only** for an internal-staff target, is not produced for the acting user, and is **untested** | [CODE] |
| F6 | PE-side claim/release/complete notify **nobody**; PE discovery is pull-only (`GET /api/v3/pe/work`) | [CODE] |
| F7 | The consultant discovers status by **10 s polling**; ops/PE queues load on mount with manual refresh | [CODE] |
| F8 | The **only** live V3 Realtime consumer is messaging (`messages`); there is **no** Realtime subscription for work items, batches or assignments | [CODE] |
| F9 | The V3 notification Realtime subscription filters on `user_id`, a **non-existent column** (`public.notifications` has `recipient_id`); the code documents an API-refetch fallback | [CODE] |
| F10 | Realtime publication membership is **not declared in the repository** and is an environment/dashboard property — **[UNVERIFIED]** here | [UNVERIFIED] |
| F11 | The full notification subsystem (tables, idempotent repository, inbox API, X2 email+retry, D11 producers) **already exists** and needs no redesign | [CODE]/[DOC] |
| F12 | The ratified **D11/D40 vocabulary contains no MP-entry event**, and the D2 spec requires no notification | [DOC] |
| F13 | P-2 is evidenced only over the coverage/allocation files, yet three of its sentences are drafted as "Manual Processing" as a whole → **Option 2: amend with a scope limit** | [DOC] |
| F14 | No client notification path exists for this workflow (and none is proposed) | [CODE] |
| F15 | The automatic-processing **success** path notifies the customer org's owner/admin (`processing.completed`); the **failure** path notifies nobody before routing to MP | [CODE] |

## Appendix B — Exact commands run in this fact-find (all read-only)

`git status --porcelain`, `git branch --show-current`, `git rev-parse HEAD`,
`git diff --name-only`, `git diff --cached --name-only`, `git ls-files --others --exclude-standard`,
`grep -rn` / `find` / `sed -n` / `cat` / `wc -l` over repository source, migrations,
schema dumps, docs and tests (no `psql`, no `supabase` CLI, no HTTP, no test runner).

No test suite was executed, because no code was changed and this task is
evidence-gathering only; running the suite would not have added evidence about
notification *absence* that static tracing does not already establish.

---

**End of report** — `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md`
