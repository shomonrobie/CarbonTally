# CT-MP-SUB-004 — PROD-READINESS NOTIFICATION POLICY FACT-FINDING 03

## Should Manual Processing lifecycle notifications be mandatory or configurable — and if configurable, at what level?

| Field | Value |
| --- | --- |
| **Task ID** | `CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-POLICY-FACTFIND-03` |
| **Type** | Read-only architecture / product-policy fact-finding. **No implementation, no schema change, no migration, no RLS change, no notification change, no Realtime change, no test change, no commit, no push, no deploy.** |
| **Subject** | Decision preparation for the **notification policy / configuration model** of the (not-yet-authorised) Manual Processing *lifecycle* notification set (N1–N4). |
| **Repository HEAD at time of work** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (`375a48d`, *"FINAL-03: freeze production cutover release"*) |
| **Branch** | `p8-release-reconciled` |
| **Date of work** | 2026-10-05 |
| **Working tree at start** | Pre-existing uncommitted work only (the CT-MP-SUB-004 implementation + FINAL-03 remediation set). **Nothing was staged, committed, reset, cleaned or reverted by this task.** |
| **Status** | **NOTIFICATION POLICY FACT-FINDING COMPLETE — READY FOR PO DECISION** |

---

## §1 Task identification

### 1.1 Purpose

Produce **evidence and options only** for one question:

> Given the *actual* CarbonTally database schema, notification architecture,
> communication/Realtime architecture, authorization model and existing
> Admin/configuration patterns — **should Manual Processing lifecycle
> notifications (N1–N4) be mandatory or configurable, and if configurable, at
> what level?**

This report does **not** decide the policy. It exists so the PO can make one
precise decision that authorises (or refuses) a later implementation task.

### 1.2 Scope — what was investigated

* the **live** notification schema (`notifications`, `notification_delivery`,
  `notification_templates`) — every column, index, constraint, RLS state;
* every **notification producer** in the backend and the exact recipient
  resolution each one uses;
* every **configuration surface** that could carry a notification policy
  (platform Admin, organisation, user, event, channel);
* the **Manual Processing actor model** (PE staff, internal validator, uploader,
  consultant, client) and whether each actor is *deterministically resolvable*
  from existing data;
* the **Supabase Realtime** delivery path and its fallbacks;
* the **migration impact** of each candidate configuration model.

### 1.3 Scope — what this task explicitly did **not** do

| Not done | Status |
| --- | --- |
| Adding notification functionality, events or recipients | **NOT DONE** |
| Adding notification preferences / Admin settings / feature flags | **NOT DONE** |
| Adding database tables, columns, migrations, RLS policies or grants | **NOT DONE** |
| Modifying notification code, Realtime, frontend or backend | **NOT DONE** |
| Modifying tests, fixtures or demo data | **NOT DONE** |
| Changing any existing product behaviour | **NOT DONE** |
| Commit / push / deploy / migrate | **NOT DONE** |

### 1.4 Governing documents consulted (documented truth)

| Document | Role in this report |
| --- | --- |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01-report.md` | P-1/P-2 fact-find; **Governance status** cell records the NF-02 scope split |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` | **AUTHORITATIVE PO decision record** — P-2 CLOSED (§5). **Read only; not modified.** |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-01-report.md` | Prod-readiness report; §21 P-1/P-2 CLOSED; §22 P-2 scope clarification |
| `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md` | **Direct predecessor.** §7.3 question, §8.2 proposed wording, §9.2 verification extension |
| `docs/architecture/CT-MP-SUB-004-independent-verification-report.md` | NV-9/NV-10 verification targets (`:665–666`) |
| `docs/architecture/CT-MP-SUB-004-PD5-VERIFY-01-report.md` | PD-5 fixture verification (positive coverage states) |
| `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | Authoritative D2 UI/UX spec — **contains no notification requirement** (verified: zero `notif*` matches) |
| `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` | Authoritative MP-SUB-003 PO spec (§25 concept boundaries) — **contains no notification requirement** (verified: zero `notif*` matches) |
| `docs/architecture/CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md` | **The ratified precedent** for PO-decided notification recipients/channels (PX-6) |
| `tools/demo_lab/README.md` | Demo Lab topology; the Realtime-proxy limitation (`:225–227`) |

### 1.5 Evidence standard used in this report

Every substantive statement is tagged with exactly one label:

| Label | Meaning |
| --- | --- |
| **[CODE]** | Verified by reading the current repository source (file + line/symbol cited). |
| **[DDL]** | Verified in the current schema/migration SQL (file + line cited). |
| **[DOC]** | A written, ratified CarbonTally decision/spec (document cited). |
| **[INFER]** | **Architectural inference** by Cline. Not a decision, not verified behaviour. |
| **[REC]** | **Cline recommendation.** Explicitly **not** a PO decision. |
| **[PO DECISION REQUIRED]** | A business choice only the Product Owner may make. |

Where the repository is **silent**, this report says so explicitly rather than
substituting general SaaS assumptions.

### 1.6 Working-tree caveat (must be read with §2/§3)

The working tree is **dirty** with the pre-existing CT-MP-SUB-004 + FINAL-03
change-set (this task changed nothing). `git status --porcelain` reports
**153** entries at the time of this fact-find. Therefore:

* file content below reflects the **working tree**, which is the authoritative
  in-flight state, not `HEAD`;
* no migration, table, column, policy or notification behaviour in this report
  was authored by this task.

---

## §2 Existing DB notification architecture

### 2.1 `public.notifications` — the single in-app inbox table [DDL]

Defined in `supabase/migrations/00000000000000_init_schema.sql:1409–1427`:

```sql
CREATE TABLE public.notifications (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    recipient_type VARCHAR NOT NULL,
    recipient_id UUID NOT NULL,
    notification_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR,
    link TEXT,
    metadata JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    is_dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

Two columns were added later by
`supabase/migrations/20260902050000_phase5_notification_event_key.sql:10–14`:

```sql
ALTER TABLE public.notifications ADD COLUMN IF NOT EXISTS event_key text;
ALTER TABLE public.notifications ADD COLUMN IF NOT EXISTS actor_domain text;
```

**Structural facts that constrain every policy option:**

| Fact | Evidence |
| --- | --- |
| `recipient_type` / `recipient_id` are the **only** recipient model. | `:1411–1412` [DDL] |
| `recipient_id` is a **bare UUID with no foreign key** — no referential integrity to `users`, `staff_profiles` or `organizations`. | `:1412` [DDL] |
| The table has **no `organization_id` / tenant column** at all. A notification is therefore *not organisation-scoped at the row level*; scoping is implicit in the recipient. | `:1409–1425` [DDL] |
| `notification_type` is a **free-form `VARCHAR`** with **no enum, no CHECK, no lookup table**. New event types require **no migration**. | `:1413` [DDL]; `consultant_lifecycle.py:65–68` comments this explicitly [CODE] |
| `priority` is declared `VARCHAR` in the schema but is written/read as an **integer string** (`str(priority)`). | `:1416` [DDL] vs `notifications.py:93–94, 27` [CODE] |
| `event_key` and `actor_domain` are nullable and used only by idempotent producers. | `notifications.py:116–167` [CODE] |
| There is **no** `channel`, `preference`, `opt_out`, `enabled`, `muted` or `delivery_policy` column. | `:1409–1425` [DDL] |

The repository's canonical column list (`backend/data/notifications.py:12–15`):

```python
_NOTIF_COLUMNS = (
    "id, recipient_type, recipient_id, notification_type, title, message, "
    "priority, link, is_read, created_at"
)
```

### 2.2 `public.notification_delivery` — per-channel delivery tracking [DDL]

`supabase/migrations/00000000000000_init_schema.sql:1429–1443`:

```sql
CREATE TABLE public.notification_delivery (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    notification_id UUID NOT NULL REFERENCES public.notifications(id) ON DELETE CASCADE,
    channel VARCHAR NOT NULL,
    status VARCHAR,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**This is the single most important structural fact for §11 (event vs channel).**
The schema already separates *the event row* (`notifications`) from *how it was
delivered* (`notification_delivery.channel`). The channel is **per delivery row**,
so **one notification event can legitimately carry several channel rows** — the
event is modelled as durable and channel-independent **by construction**.

There is **no** unique constraint on `(notification_id, channel)`, so the table
is an append-only delivery *log*, not a per-channel state machine. [DDL]
Only one producer writes to it today (§3.5).

### 2.3 `public.notification_templates` — present but effectively unused [DDL]/[CODE]

`supabase/migrations/00000000000000_init_schema.sql:151–165` defines
`notification_templates` (`template_type VARCHAR UNIQUE NOT NULL`, `subject`,
`body`, `variables JSONB`, `is_active`).

* Live usage in the backend: **one legacy reference only** —
  `backend/routes/notifications.py:531` (`get_notification_templates`), a legacy
  route surface. [CODE]
* **No V3 producer reads it.** `NotificationsRepository.create` /
  `create_idempotent` insert literal `title`/`message` strings supplied by the
  producer; nothing resolves a template. [CODE]
* It was included in the **fail-closed RLS enablement lists**
  (`20260803000000_rc2_rls.sql:121`, `20260925000000_p8_rls_4b_group1_enablement.sql:75`). [DDL]

**Consequence for policy:** CarbonTally has *no template-driven notification
config*. Copy is code, not configuration. An "event-level configuration" option
(Option E) therefore cannot be implemented by toggling template rows.

### 2.4 Constraints and indexes (the idempotency + inbox contract) [DDL]

| Object | Definition | Where |
| --- | --- | --- |
| `uq_notifications_event_key` | `UNIQUE (recipient_id, event_key) WHERE event_key IS NOT NULL` | `20260902050000_phase5_notification_event_key.sql:16–18` |
| `ix_notifications_recipient_inbox` | `(recipient_type, recipient_id, is_read, created_at DESC)` | same file `:20–21` |
| `notifications_unread_recipient_idx` | `(recipient_id, created_at)` | `00000000000000_init_schema.sql:2200`, re-created in `20260802000000_rc2_indexes.sql:73–74` |
| `notification_delivery.notification_id` FK | `REFERENCES public.notifications(id) ON DELETE CASCADE` | `init_schema.sql:1431` |

**Key facts:**

* Idempotency is a **database guarantee** (`uq_notifications_event_key`), keyed
  on `(recipient_id, event_key)` — i.e. *per recipient*: the **same business
  event may (and must) create one row per recipient**. A "one notification per
  event" policy is therefore **not** what the schema enforces. [DDL]
* There is **no** index on `notification_type`. Any future "did we already send
  type X?" query or an event-level *configuration* keyed by type would need one. [DDL]
* There is **no** PII/payload PII concern at the schema level: title/message are
  free text.

### 2.5 RLS posture — fail-closed, zero policies, API-mediated [DDL]

`notifications` and `notification_delivery` were enabled under **CT-FINAL-03
RLS security remediation** (`supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql`):

* `notifications` is in **GROUP A (41) — fail-closed** (`:105`, listed under
  "§5 remaining production-sensitive Class-C… R-5", `:22–24`). [DDL]
* `notification_delivery` is in the **Class-B (19)** free-enablement set (`:128`). [DDL]
* **Neither table has any policy.** The migration's own header states the rule
  (`:15–19`): *"FAIL-CLOSED: `ALTER TABLE … ENABLE ROW LEVEL SECURITY` with ZERO
  policies. With RLS on and no policy, every `anon` / `authenticated`
  SELECT/INSERT/UPDATE/DELETE is denied while `service_role` (the FastAPI
  backend, which holds BYPASSRLS) is unaffected."* [DDL]/[DOC]
* The migration changes **no policy, grant, data or schema** beyond enablement
  (`:50–52`, `:64–67`). [DDL]
* `grep 'POLICY' supabase/migrations/00000000000000_init_schema.sql` returns
  **zero** matches — `notifications` never had an RLS policy. [DDL]

**Consequences (critical for §5 and §7):**

1. **No browser may read or write `public.notifications` directly.** The only
   path is the authenticated FastAPI API (`/api/v3/notifications`), which the
   backend reads through the `service_role`/BYPASSRLS pool. [DDL]/[CODE]
2. **Realtime `postgres_changes` on `notifications` cannot deliver to an
   `authenticated` client** — Supabase Realtime applies the subscriber's RLS.
   With RLS enabled and zero policies, the change never reaches the client.
   This is not a bug in the realtime client; it is the CT-FINAL-03 posture. [INFER, from DDL + the code's own comments]
3. Therefore **Realtime is best-effort decoration and the API is the delivery
   guarantee** — which the frontend code states in as many words
   (`frontend/src/context/RealtimeContext.jsx:299–305`): *"Best-effort live
   delivery… if RLS blocks it, the API refetch on window focus is the
   deterministic fallback (never a console error)"*. [CODE]
4. Tenant isolation for notifications is **not** an RLS property; it is an
   **application-authorization property** (`recipient_id = current_user.user_id`
   is enforced in the repository query, `notifications.py:50–56`). §5 of AGENTS.md
   ("the UI is never a security boundary") is satisfied because the *backend*
   filters. [CODE]

### 2.6 Existing configuration tables that touch notifications [DDL]

| Table | Has anything to do with *whether/how* a notification is sent? |
| --- | --- |
| `system_settings` | **Partially.** One key (`platform_notifications`) holds the **email sender address** only — see §4.1. No enablement/policy key exists. |
| `queue_settings` | **No.** Key/value queue configuration; unrelated to notifications. |
| `notification_templates` | **No live role** (§2.3). |
| `sla_definitions` | **No.** Empty in the environments documented by the X2 contract (`CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md:41`). |

### 2.7 Structures that are **absent** — stated explicitly [DDL]

A repository-wide search of the live schema (`CarbonTally_DB_Schema_V3M2.sql`
and `supabase/migrations/*.sql`) returns **zero** tables or columns for:

| Searched for | Result |
| --- | --- |
| `notification_preferences` / `notification_settings` | **ABSENT** |
| any `preferences` table or column | **ABSENT** (`grep 'preferences'` → 0 matches) |
| `user_preferences` | **ABSENT** |
| `organization_settings` | **ABSENT from the live schema** — it exists **only** as an unapplied historical design script: `docs/architecture/DB_Migration/migration_003_org_man.sql:38`. [DDL] |
| `feature_flags` | **ABSENT from the live schema** — **only** in the unapplied design script `docs/architecture/DB_Migration/MIGRATION_009_PLATFORM_ADMINISTRATION.sql:52`. [DDL] |
| any per-tenant/per-user notification opt-out, mute or channel preference | **ABSENT** |

> **This is the headline §2 finding.** CarbonTally has an authoritative,
> ratified, durable notification *capability* — and **no notification
> configuration/preference mechanism of any kind, at any level**.
> The absence is not an oversight to be filled by inference; it means **every
> option in §7 is a genuinely new product decision**, and the PO is deciding
> from a clean sheet on the *configuration* dimension only.

---

## §3 Existing notification code architecture

### 3.1 The repository — `backend/data/notifications.py` (`NotificationsRepository`) [CODE]

Registered in the DI bundle at `backend/api/dependencies.py:67, 354, 461`
(`repos.notifications`). Every method, in full:

| Method | Line | What it really does |
| --- | --- | --- |
| `list_for_user(user_id, unread_only, limit, offset)` | `:37–58` | `WHERE recipient_type='user' AND recipient_id=$1` — **the identity filter is the authorization** |
| `count_for_user(user_id, unread_only)` | `:60–69` | pagination total |
| `create(user_id, *, notification_type, title, message, priority, link)` | `:71–98` | plain insert; **no** `event_key` → **not** deduplicated |
| `mark_read(notification_id, user_id)` | `:100–107` | `WHERE id=$1 AND recipient_type='user' AND recipient_id=$2` (ownership enforced in SQL) |
| `mark_all_read(user_id)` | `:109–114` | bulk |
| `create_idempotent(user_id, event_key, *, …, actor_domain)` | `:116–167` | `ON CONFLICT (recipient_id, event_key) … DO NOTHING` then re-select — **the durable producer primitive** |
| `support_staff_user_ids()` | `:169–178` | resolver (see §3.2) |
| `entity_participant_user_ids(conversation_id, entity_id, exclude_user)` | `:180–194` | resolver (see §3.2) |
| `get / save / delete` | `:196–210` | `save`/`delete` are **no-ops** (read-mostly repository) |
| `internal_ops_user_ids()` | `:213–227` | resolver (see §3.2) |
| `email_for_user(user_id)` | `:229–235` | `SELECT email FROM public.users WHERE id=$1` — the email channel's only address source |
| `record_delivery(notification_id, *, channel, status, error_message, attempts)` | `:237–268` | inserts a `notification_delivery` row; sets `sent_at`/`delivered_at` from `status` |
| `prune_operational_alerts_before(cutoff, *, dry_run)` | `:270–312` | retention **scoped to `notification_type LIKE 'ops_alert_%'` only** |

**Note on `create` vs `create_idempotent`:** both exist and both are used
today. `automatic_processing.py:1953` and `v3_discovery.py:691` use the
**non-idempotent** `create`; every other producer uses `create_idempotent`.
This matters for Option E/F (a per-event toggle): the schema-level dedupe
guarantee only applies to the producers that opt in. [CODE]

### 3.2 Recipient resolvers — exactly three exist [CODE]

There are **only three** recipient-resolution helpers in the entire backend,
and each has a narrow, server-derived meaning:

| Resolver | Line | Recipient set | Explicitly excluded |
| --- | --- | --- | --- |
| `support_staff_user_ids()` | `:169–178` | active **internal** staff (`staff_profiles.entity_id IS NULL`) whose role permission `can_manage_staff = true` | PE staff (`entity_id IS NOT NULL`) excluded **by construction** |
| `internal_ops_user_ids()` | `:213–227` | active **internal** staff whose role permission `can_view_all = true` — the PO-approved X2 recipient set | PE staff excluded by construction |
| `entity_participant_user_ids(conversation_id, entity_id, exclude_user)` | `:180–194` | **members of one entity conversation** (`conversation_participants` joined to `staff_profiles.entity_id = $2`) | any user not already a conversation participant |

> **Critical gap for N1.** There is **no** resolver of the form
> *"all active staff of Processing Entity X"* used by any notification producer.
> The only such query in the codebase is
> `backend/data/staff.py:91` `list_entity_staff(entity_id)` — a **staff roster**
> method (returns `StaffProfile` rows, which carry `user_id`), used by the
> entity dashboard, **not** by any notification path. [CODE]
> So *"PE notified of assigned Manual Processing work"* is **technically
> resolvable from existing data** (`list_entity_staff`) but is **not an existing
> notification behaviour** — it would be a new producer plus a new resolution
> path. [INFER]

Similarly, there is **no** resolver for *"the uploader of this document/item"* and
**no** resolver for *"the responsible consultant for this client"* — although
both identities are persisted (§5.5, §5.3). [CODE]

### 3.3 The complete, verified producer inventory [CODE]

| # | Producer (file:line) | Event / `notification_type` | Recipients | Idempotent? | Channel |
| --- | --- | --- | --- | --- | --- |
| P1 | `backend/services/work_items.py:51–69`, called **only** at `:216` (`ops_assign_item`) | `work_item.assigned` | **internal staff assignee only** (when `assignee_kind='internal_staff'`) | yes (`event_key`) | in-app only |
| P2 | `backend/services/consultant_lifecycle.py:143–200` (`_emit`) | 5 ratified D11 events → `consultant.lifecycle.<event>`: `accepted`, `submitted_to_qc`, `qc_outcome`, `customer_decision`, `rework` | server-derived only: firm members (`list_firm_members`), internal ops (`support_staff_user_ids`) | yes (`lifecycle_event_key`) | in-app only |
| P3 | `backend/services/operational_alerting.py:113–215` | `ops_alert_%` types (X2) | `internal_ops_user_ids()` | yes (`alert["event_key"]`) | **in-app + email** |
| P4 | `backend/api/v3_backups.py:171–198`, `:612` | `backup` (`backup:<job>:verification_failed`) | internal backup operators | yes | in-app only |
| P5 | `backend/api/v3_messaging.py:519–535` | `pe_msg.message`, `pe_msg.ops_reply` | `support_staff_user_ids()` or `entity_participant_user_ids(...)` | yes (`pe_msg:<msg>:<recipient>`) | in-app only |
| P6 | `backend/api/v3_discovery.py:691–700` | `general` | request-derived user | **no** (`create`) | in-app only |
| P7 | `backend/services/automatic_processing.py:1939–1966` (`_notify`), called at `:1797` | `processing.completed` | **the customer organisation's `owner` + `admin` members** (`organizations.get_members`) | **no** (`create`) — guarded by `job.notified_at is None` | in-app only |
| P8 | `backend/main.py:331–345` | `backup` | internal backup operators | yes | in-app only |

Existing `notification_type` namespaces in the tree:
`work_item.assigned`, `consultant.lifecycle.*`, `pe_msg.*`, `ops_alert_*`,
`backup`, `general`, `processing.completed`.

**Three facts that shape §6/§7:**

1. **No producer emits any Manual Processing event.** A repository-wide search
   for notification creation inside the MP surfaces returns **zero matches**;
   MP transitions produce **audit rows only** (§6). [CODE]
2. **No producer checks any preference, flag or setting before emitting.**
   Grep for `notification_preference|opt_out|unsubscribe|notify_on_` across
   `backend/data`, `backend/api`, `backend/services`, `backend/domain`,
   `frontend/src`, `admin/src` returns **only unrelated matches**
   (`channel.unsubscribe()` calls and analytics-consent helpers). [CODE]
   **Notification generation is currently unconditional and mandatory everywhere
   it exists.** This is the single most decision-relevant fact in this report.
3. **P7 is an existing client-facing notification** (`processing.completed` to
   org owner/admin). It belongs to the **automatic-processing** workflow, not
   Manual Processing — see §6.5 and §12.

### 3.4 Idempotency — how duplicates are prevented today [CODE]/[DDL]

* Primitive: `create_idempotent` → `INSERT … ON CONFLICT (recipient_id, event_key)
  WHERE event_key IS NOT NULL DO NOTHING`, backed by `uq_notifications_event_key`.
* `event_key` is **always server-generated from a stable business identity** —
  never client input. Verified shapes:
  * `consultant_lifecycle.lifecycle_event_key()` → `consultant.lifecycle.<event>:<identity>[:<discriminator>]` (`consultant_lifecycle.py:83–100`);
  * `backup:<job.id>:verification_failed` (`v3_backups.py:612`);
  * `pe_msg:<message.id>:<recipient>` (`v3_messaging.py:527`).
* **A client can never choose a recipient or an event key.** Asserted negatively
  in tests: `tests/e2e/test_p6_2f_deny_matrix.py:126` injects
  `"event_key": "attacker.chosen.key"` and asserts it is **not** honoured. [CODE]

### 3.5 Delivery recording, retry and the two-channel precedent [CODE]

`operational_alerting.py` is the **only** producer that implements the full
event-plus-channel model:

| Aspect | Where | Behaviour |
| --- | --- | --- |
| Channel constants | `CHANNEL_IN_PRODUCT`, `CHANNEL_EMAIL` | two named channels |
| In-product delivery | `_dispatch_one` (`:158–162`) | `record_delivery(..., channel=CHANNEL_IN_PRODUCT, status="delivered")` |
| Email delivery | `_deliver_email` (`:170–215`) | up to `DELIVERY_MAX_ATTEMPTS` (3) attempts; **honest failure** — `status="failed"` + `error_message`; `"no email address on record"` when `email_for_user` returns `None` |
| Never fatal | docstring `:107–111` | "A failure at any point is recorded and never raised to the caller." |
| No-recipient case | `:125–128` | `skipped_reason = "no internal recipient holds can_view_all"` — **recorded honestly, never reported as sent** |

**This is the ratified architecture for "mandatory event, per-channel delivery
record" — and it is PO-approved precedent, not invention**
(`CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md:4` — *"PO decisions of
2026-09-14 — `PX-6` Option (a) … 'no invented thresholds; no invented recipient
lists'"*, and `:898` — *"PX-6: Confirm alert recipients, channels and
thresholds"*). [DOC]

**What it does *not* have:** the channels are **not configurable**. There is no
setting that says "in-product yes, email no" for a given alert. Both are
attempted for every alert, for every recipient. [CODE]

### 3.6 API surface [CODE]

`backend/api/v3_notifications.py` — `router = APIRouter(prefix="/api/v3/notifications")`:

| Method | Route | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/api/v3/notifications` | `require_auth()` | `limit` clamped 1..500; returns `{notifications, total, limit, offset}` |
| POST | `/api/v3/notifications/{id}/read` | `require_auth()` | 404 when not the caller's row |
| POST | `/api/v3/notifications/read-all` | `require_auth()` | bulk mark |

**There is no producer API and no configuration API.** Producers run
server-side and in-process; no HTTP route creates a notification on behalf of
a caller. Consequently a *notification policy* has **no existing API home** —
it would have to be introduced either under `/api/v3/settings/*` or under the
MP Admin control plane (§4).

### 3.7 Frontend surfaces [CODE]

| Surface | File | Reality |
| --- | --- | --- |
| V3 shell notification bell | `frontend/src/context/RealtimeContext.jsx:306–332` | Subscribes `channel('ct-v3-notifications')` `postgres_changes` on `notifications` with **`filter: user_id=eq.${user.id}`**. The recipient column is **`recipient_id`, not `user_id`** → the filter can never match; the code calls this out as best-effort and relies on the API refetch on window focus (`:340–344`). |
| PE notification bell | `frontend/src/v3/pe/PeNotificationsBell.jsx:31–46` | **Pull only**: `listNotifications()` on mount; no Realtime subscription. Header comment (`:9–13`): *"Notifications are never an access-control mechanism."* |
| Legacy hook | `frontend/src/hooks/useNotifications.js:33–58` | Subscribes `channel('notifications')` on the same table with **no filter** — for an `authenticated` client this is RLS-denied anyway (fail-closed). Also calls the **removed** legacy route `/api/notifications` in `NotificationService.checkNotifications` (`:183`) despite the hook's own ISC-6 comment. |
| Notification service | `frontend/src/services/NotificationService.js` | Browser `Notification` API + service worker + toasts. Its `markAsRead` posts to the **removed legacy** `/api/notifications/{id}/read` (`:129`) and references `getToken`/`API_URL` that are **not defined in the module** (`:128`, `:183`). |
| Notification settings UI | `frontend/src/components/NotificationSettings.jsx` | **DEAD CODE.** `grep -rn 'NotificationSettings' frontend/src admin/src` returns **only the file's own definition and export** — it is **imported and mounted nowhere**. Its "Notification Types" checkboxes are `defaultChecked` with **no handler and no persistence** (`:97–122`); its `toast.*` calls are on an unimported symbol. See §4.4. |

### 3.8 Existing tests that pin current behaviour [CODE]

| Test | Pin |
| --- | --- |
| `backend/tests/unit/api/test_v3_notifications.py` | API contract: bounded defaults, limit clamping (1..500), 401 without auth |
| `backend/tests/unit/api/test_ct_mp_sub_004_prod_readiness.py` — `class TestNV10NotificationBehaviour` (`:487–530`) | **Three assertions that MP allocation/release emit NO notification row** (`world.notifications.rows` unchanged) and that `"notification"` does not appear in the response body |
| `backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py` | Deterministic, server-generated event keys; recipient sets; attacker-chosen keys rejected (`:619`) |
| `backend/tests/e2e/test_p6_2f_allow_workflows.py:104`, `…_deny_matrix.py:126`, `…_invariants.py:133–176` | Event keys are server-generated and cannot be forged |
| `backend/tests/integration/test_operational_alerting_x2_runtime.py` | Hourly dedup via `event_key`; a new hour is a new key |

> **Regression implication (material for §10).** `TestNV10NotificationBehaviour`
> asserts *absence* of MP notifications for allocation/release. Those tests are
> scoped to the **coverage** surface, which is CLOSED audit-only. They do **not**
> constrain MP *lifecycle* notifications — but any future implementation keying
> on `notification_type LIKE 'manual_processing%'` must be checked against them
> so the two scopes stay provably disjoint.

### 3.9 The email path [CODE]

| Layer | File | Note |
| --- | --- | --- |
| Low-level send + templates | `backend/utils/email.py:20` `send_email`, `:69` `send_email_from_db_template`, `:117–617` invitation/welcome/password-reset/report/beta/bulk helpers | Also `:617 log_email` → writes `email_logs` |
| Sender identity resolution | `backend/services/email_sender.py` (`resolve_email_sender`, `describe_email_sender`, `normalise_email_sender`, `notification_identity`) | Used by `/api/v3/settings/notification-sender` |
| Provider config | `backend/services/email_provider.py` | Stores provider **and the name of the env var** holding the credential — never the credential |
| Provider | Resend (`requirements`: `resend`; `operational_alerting.py` sends via the platform sender) | External dependency |
| Audit | `email_logs` table + `backend/routes/admin/logs.py` | Legacy admin log reader; `email_logs` is in the CT-FINAL-03 fail-closed group (`:104`) |

**Fact:** email is used for invitations, password resets, reports and X2
operational alerts. It is **not** used by P1 (`work_item.assigned`), P2
(consultant lifecycle), P4/P8 (backups), P5 (PE messaging) or P6/P7. So today
**all Manual-Processing-adjacent notification traffic (there is none) and all
workflow notification traffic is in-app only**; email exists as an *operational
alerting* channel, not a general workflow channel. [CODE]

---

## §4 Existing configuration architecture

### 4.1 Platform Admin configuration — the established, working pattern [CODE]/[DDL]

CarbonTally **does** have a mature platform-level configuration mechanism.

**Storage:** `public.system_settings`
(`supabase/migrations/00000000000000_init_schema.sql:2022–2086`) — a
**key/value** table: `setting_key VARCHAR UNIQUE NOT NULL`,
`setting_value JSONB NOT NULL`, `setting_type`, `description`, `is_editable`,
`updated_by`, `updated_at`. It also carries *many legacy columns*
(`two_factor_required`, `password_expiry_days`, `sla_breach_alert_*`, …) which
are **not** used by the V3 settings surface.

**Access:** `backend/data/settings.py` (`SettingsRepository`) reads/writes
**fixed, named keys** and exposes only an **allow-list** of fields:

| `setting_key` | Repository constant | Fields surfaced | Admin route |
| --- | --- | --- | --- |
| `platform_retention` | `_SETTINGS_KEY` (`settings.py:24`) | the table's own retention *columns* (`audit_log_retention_days`, `data_retention_days`, `document_retention_days`, `backup_retention_days`, `operational_telemetry_retention_days`) | `GET/PUT /api/v3/settings/retention` (`v3_settings.py:214, 224`) |
| `analytics_ga4` | `_ANALYTICS_KEY` (`:32`) | `enabled`, `ga4_measurement_id` | `GET/PUT /api/v3/settings/analytics` (`:251, 273`) |
| `platform_notifications` | `_NOTIFICATION_KEY` (`:37`) | **`email_sender` only** (`_notification_from_row`, `:118–138`) | `GET/PUT /api/v3/settings/notification-sender` (`:308, 331`) |
| `upload_policy` | `_UPLOAD_POLICY_KEY` (`:42`) | `POLICY_FIELDS` from `utils.upload_limits` | `GET/PUT /api/v3/settings/upload-policy` (`:367, 387`) |
| `email_provider` | `_EMAIL_PROVIDER_KEY` (`:49`) | provider + **env-var name** (never the secret) | `GET/PUT /api/v3/settings/email-provider` + `/validate` (`:421, 445, 480`) |
| `backup_policy` | `_BACKUP_POLICY_KEY` (`:59`) | `backup.policy.POLICY_FIELDS` | backup policy surface |

**The pattern's rules — all directly reusable by a notification policy:**

1. **One row per configuration domain**, identified by a fixed `setting_key`. [CODE]
2. **Narrow allow-list**: unknown keys in a stored payload are ignored, so "an
   operator can never smuggle an unrelated limit in through this row"
   (`_upload_policy_from_row` docstring, `:99–101`). [CODE]
3. **Fail-closed to a documented default**: a missing row / malformed payload
   degrades to "not configured", never to an invented value
   (`_notification_from_row` docstring, `:121–124`; `_backup_policy_from_row`,
   `:66–70`). [CODE]
4. **Admin-gated**: every route uses `Depends(require_admin())`
   (`backend/auth.py:760`; re-exported at `backend/api/dependencies.py:34`). [CODE]
5. **Audited**: `updated_by` is stamped with `current_user.user_id` on every write. [CODE]
6. **RLS-consistent**: `system_settings` is **fail-closed** under CT-FINAL-03
   (`20261028000000_…:98`, listed as critical `R-1`) — reachable only through the
   admin API, never from a browser. The admin Settings page's own comment records
   this (`admin/src/pages/admin/Settings.js:63–70`). [DDL]/[CODE]

> **Conclusion for §7 Option B:** a *"Platform Admin → notification policy"*
> setting would be a **straightforward reuse** of an existing, proven, audited,
> RLS-safe pattern — **no new table, no new RLS, no new grant, no new
> authorization model.** That is a material architectural fact, not an opinion.

### 4.2 The existing Admin control plane for Manual Processing itself [DDL]/[CODE]

Manual Processing policy is **already** Admin-configured through three
purpose-built, audited admin surfaces. This is the closest existing *home* to an
MP notification policy:

| Control plane | Table | Written by | Audit action |
| --- | --- | --- | --- |
| MP governance on/off per scope | `public.manual_processing_grants` (FIN-06) | `backend/api/manual_processing_admin.py` | `manual_processing:grant_set`, `:grant_removed`, `:grant_rejected_not_entitled`, `:queued_batches_cancelled` |
| MP routing destination per scope | `public.manual_processing_processors` (`20261030000000_manual_processing_routing.sql:64–82`) | same module | `manual_processing:processor_set`, `:processor_removed`, `:processor_rejected_not_entitled` |
| Consultant-sponsored coverage | `public.consultant_mp_allocations` (`20261101000000_ct_mp_sub_003_consultant_coverage.sql:69–90`) | `backend/api/manual_processing_admin.py` + `backend/api/v3_manual_processing_coverage.py` | `manual_processing:allocation_created`, `:allocation_released` |

Shared design posture, quoted from the routing migration (`:33–36`):
*"RLS ENABLED with ZERO policies, and both client roles revoked. Only the
service role (the FastAPI backend, which performs the CarbonTally-Admin
authorization at the API boundary) can read or write these rows. Entitlement +
authorization are enforced server-side."*

**Consequence:** if the PO wants an *Admin-configurable* MP notification policy,
there is an **existing, ratified, audited admin control-plane idiom** for MP
policy to extend. What does **not** exist is any precedent for user- or
organisation-level configuration (§4.3, §4.4). [INFER]

### 4.3 Organisation-level configuration — **ABSENT** [DDL]/[CODE]

| Candidate | Reality |
| --- | --- |
| `organization_settings` | **Not in the live schema.** Present only in the unapplied design script `docs/architecture/DB_Migration/migration_003_org_man.sql:38`. [DDL] |
| Any per-organisation settings/preferences table | **None.** `grep 'CREATE TABLE' *.sql \| grep -i 'pref\|_settings\|flag\|config\|policy'` returns only `system_settings`, `queue_settings`, `billing_plans`, `billing_commercial_config`, `billing_credit_ledger` and the two unapplied design-doc tables. [DDL] |
| Per-organisation commercial configuration | Exists but is **commercial only**: `billing_commercial_config` is a **platform-wide, versioned** key/value rule set (not per-org), and `customer_subscriptions` / `billing_plans` express plan entitlements. Neither is a notification policy. [DDL] |
| Per-consultant-firm capability flags | Exist as **authorization** flags, not preferences: `consultant_firm_members.can_manage_clients`, `can_upload_documents`, `can_generate_reports`, … (`backend/data/consultants.py:50`, `backend/api/consultant_auth.py:19, 46`). [CODE] |

> **The organisation-level option (Option C) has no existing vehicle.** It would
> require a new table (or a new keyed column), new RLS, a new organisation-scoped
> admin surface, **and** a new "who in the org may change it" authorization
> decision. It is the **heaviest** option in §7. [INFER]

### 4.4 User-level configuration — **ABSENT**, and a legacy UI must not be mistaken for one [CODE]

This section exists because the repository contains a component that *looks* like
a notification-preference UI but is not one. Reporting it accurately matters so
the PO does not assume an existing mechanism.

| Surface | Verdict |
| --- | --- |
| `frontend/src/components/NotificationSettings.jsx` | **DEAD + non-persistent.** Not imported anywhere (grep returns only its own definition/export). Its toggles are either browser-permission driven (`Push Notifications` → `Notification.requestPermission()`) or **`defaultChecked` checkboxes with no `onChange`, no state binding and no API call** (`In-App Notifications`, `Notification Sound`, and all four "Notification Types" boxes, `:71–122`). It persists **nothing**. |
| `admin/src/pages/admin/Settings.js` — "⏱️ Session & Notifications" card (`:394–473`) | **Cosmetically present, functionally inert.** The card renders `Email Notifications`, `Email Alerts` and `Weekly Reports` checkboxes (`:437–463`) bound to local React state, but `handleSaveSettings` (`:120–155`) submits **only** `/api/v3/settings/upload-policy` and `/api/v3/settings/retention`. The file's own comment states the position (`:116–119`): *"Only limits the backend genuinely persists are submitted. Every other field on this legacy screen has no column anywhere in the schema (package 09 §1.1), so it stays local-only and is neither read from nor written to the platform settings store."* |
| Any user preferences table/API | **None** (§2.7). |

> **Consequence:** **there is no user-level notification configuration**, and the
> two legacy surfaces above are *not* a foundation — one is dead code, the other
> is a documented no-op. Any recommendation involving individual opt-out
> (Option D) must say plainly that it is a **new capability with no existing
> foundation**.

### 4.5 Event-level configuration — **ABSENT** [CODE]

No mechanism maps a `notification_type` to an enabled/disabled state. There is
no lookup table, no CHECK constraint, no settings key, and **no index on
`notification_type`** (§2.4). Event identity exists only as a free-form string on
each row. [DDL]/[CODE]

### 4.6 Channel-level configuration — **partially present, not configurable** [CODE]

The only channel-aware producer is `operational_alerting.py` (§3.5). It uses two
channels (`CHANNEL_IN_PRODUCT`, `CHANNEL_EMAIL`) and records each in
`notification_delivery`. But:

* which channels are attempted is **hard-coded in code**, not configuration;
* there is no per-recipient or per-event channel choice;
* no other producer writes `notification_delivery` at all.

So the *substrate* for channel-level policy exists (a delivery table with a
`channel` column) while the *configuration* does not. [CODE]/[INFER]

### 4.7 Feature flags — **ABSENT** [DDL]

`feature_flags` exists **only** in the unapplied design script
`docs/architecture/DB_Migration/MIGRATION_009_PLATFORM_ADMINISTRATION.sql:52`,
never in `supabase/migrations/`. There is no flag mechanism to reuse. [DDL]

### 4.8 The ratified precedent: the PO decides recipients and channels (PX-6) [DOC]

`docs/architecture/CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md` is the
existing, ratified answer to *exactly this class of question* for the X2
alerting workstream:

* `:4` — *"Authority: PO decisions of 2026-09-14 — `PX-6` Option (a) (internal
  CarbonTally operations alerting **only**; 'no invented thresholds; no invented
  recipient lists')…"*
* `:41–42` — the contract explicitly **refused** to choose thresholds and
  recipients: *"`PX-6` says 'no invented thresholds' — no number may be chosen by
  me"*; *"`PX-6` says 'no invented recipient lists'… Whether it is a stored
  address list, a role/mailbox, or 'internal staff holding a given permission' is
  a business choice."*
* `:898` — the PX-6 question in the PO's own terms: *"Confirm **alert recipients,
  channels and thresholds**"*.

> **This is the governance precedent this fact-find follows:** recipients,
> channels and enablement are **PO choices**, and a fact-finder must present
> options with evidence rather than choose. It also establishes that CarbonTally
> already separates *recipient decision* from *channel decision* at the PO level.

### 4.9 Summary: which configuration mechanism exists where? [CODE]/[DDL]

| Level | Mechanism exists? | Evidence |
| --- | --- | --- |
| **A. Platform Admin** | **YES** — `system_settings` + `/api/v3/settings/*` (admin-gated, audited) | §4.1 |
| **B. Admin control plane (MP-specific)** | **YES** — grants / processors / allocations, all audited | §4.2 |
| **C. Organisation** | **NO** | §4.3 |
| **D. Individual user** | **NO** (legacy UI is dead / non-persistent) | §4.4 |
| **E. Event-level** | **NO** | §4.5 |
| **F. Channel-level** | **PARTIAL substrate only** (`notification_delivery.channel`); no configuration | §4.6 |
| **G. Feature flag** | **NO** | §4.7 |

**Note the shape of this result:** CarbonTally is **Admin-config-heavy and
end-user-config-absent**. That is the opposite of a generic consumer SaaS
assumption, and it is the single most important input to §7 and §8. [INFER]

---

## §5 Manual Processing actor model

### 5.0 The actors the proposed N1–N4 events would target

| Proposed event | Actor to notify | Actor exists in the data model? | Deterministically resolvable today? |
| --- | --- | --- | --- |
| **N1** MP work assigned | Processing Entity (its staff) | **YES** | **Resolvable, but not by any existing resolver** — `staff.list_entity_staff(entity_id)` is the only query |
| **N2** validation assigned | assigned CarbonTally internal validator | **YES** | **Partially** — the assignment holder is in `work_item_assignments.assigned_to`; a producer already targets it on the ops-assign path (§6.2) |
| **N3** MP entry | submitting/responsible consultant | **YES** | **Resolvable, but not by any existing resolver** — `consultant_clients` + `consultant_firm_members` |
| **N4** MP completion | original uploader | **YES** | **Resolvable, but not by any existing resolver** — `customer_documents.uploaded_by` (+ `manual_extraction_items.file_id`) |
| — | **client / customer user** | exists | `organizations.get_members` (used by P7) — **but see §12: excluded by PO context** |

### 5.1 Internal CarbonTally staff (operators, reviewers, QC, admins) [DDL]/[CODE]

* `public.staff_profiles` (`init_schema.sql:1234`) — `user_id`, `role_id`,
  `entity_id` (**nullable**: `NULL` = internal CarbonTally; populated = PE staff;
  added by `20260810000000_v3m1_processing_entities.sql:65–66`).
* `public.staff_roles` with a **`permissions JSONB`** — capabilities are
  individual booleans, e.g. `can_manage_staff`, `can_view_all`
  (used by the two internal resolvers, `notifications.py:174–177, 217–221`). [CODE]
* Admin authority for the platform settings surface is `require_admin()`
  (`backend/auth.py:760`), backed by superuser/staff-role checks
  (`auth.py:803–824`). [CODE]
* Internal staff work queues exist and are **pull-based**:
  `manual_extraction.py` exposes `list_operator_batches`, `next_operator_item`,
  `list_qc_pending`, `count_qc_pending`, `list_ct_qc_pending`, `ops_dashboard_all`. [CODE]

### 5.2 Processing Entity staff [DDL]/[CODE]

* `public.processing_entities` (`20260810000000_v3m1_processing_entities.sql:45–48`) —
  `id`, `name`, `status` (`active|remediation|suspended|terminated`).
  The comment is explicit (`:50–54`): *"First-class Human Data Processing Entity
  (ADR-V3-001 — Option B, dedicated table). **Distinct from** Customer/Organization,
  User, Entity Staff, Consultant and CarbonTally internal staff."*
* PE staff = `staff_profiles` rows with `entity_id` set; roster query:
  `backend/data/staff.py:91` `list_entity_staff(entity_id)` returns `StaffProfile`
  objects carrying **`user_id`**. There is also `assign_staff_to_entity` (`:170`). [CODE]
* PE authentication/authorization: `backend/api/pe_auth.py` + `backend/api/v3_pe.py`
  (prefix `/api/v3/pe/*`), including `pe_work` (`v3_pe.py:150`) and
  `pe_work_item_read / claim / release / complete` (`:604–658`). [CODE]
* **Discoverability today = pull.** PE surfaces load on mount
  (`frontend/src/v3/pe/PEDedicatedHome.jsx:66–67`, `PeWorkItemsPage.jsx:89`)
  with a manual `refresh` counter; there is **no `setInterval` polling and no
  Realtime subscription** for PE work items (`grep setInterval` across
  `frontend/src/v3/pe/*.jsx` → **zero matches**). [CODE]
* **No existing producer notifies a PE** — see §6.1.

### 5.3 Consultants and consultant firms [DDL]/[CODE]

| Entity | Table | Key columns |
| --- | --- | --- |
| The **firm** | `public.consultant_profiles` | `organization_id` → the firm's own organisation, which carries its D37 subscription (used by `ct_mp_sub_003` for commercial coverage) |
| **Firm membership** | `public.consultant_firm_members` (`init_schema.sql:1582+`) | `firm_id`, `user_id`, `role`, `is_active`, `can_manage_clients`, `can_upload_documents`, `can_generate_reports`, … (`backend/data/consultants.py:50`) |
| **Client relationship (eligibility)** | `public.consultant_clients` (`init_schema.sql:1554–1580`) | `consultant_id` (firm), `organization_id` (client), `client_contact_email`, `client_contact_name`, `status`, **`UNIQUE (consultant_id, organization_id)`** |
| **Coverage allocation** | `public.consultant_mp_allocations` (`20261101000000_…:69–90`) | `consultant_id`, `consultant_client_id`, `organization_id`, `state ∈ (active, released)` |

Resolvers that exist: `consultants.list_firm_members(firm_id)`,
`consultants.list_active_client_grants(organization_id)`,
`consultants.get_user_summaries(user_ids)` (`consultants.py:263`). [CODE]

**Consequence for N3:** the *responsible consultant* for a client is derivable
from `consultant_clients` (and, for sponsored work, from
`consultant_mp_allocations`); firm members are derivable from
`consultant_firm_members`. Both are **server-derived and authoritative** — but no
notification producer does this today, and the PO must decide *which* consultant
(uploader, firm owner, all `can_manage_clients` members, or all firm members) is
"the relevant consultant". That is a **business choice, not a technical one**.
[PO DECISION REQUIRED]

### 5.4 Customer users [DDL]/[CODE]

`public.organization_members` with roles `owner | admin | member | viewer`
(unique index `organization_members_org_user_uniq`, `init_schema.sql:2140`).
`organizations.get_members(org_id)` returns members with a `role` attribute —
this is what P7 uses (`automatic_processing.py:1949–1954`). [CODE]

**Per the stated business context, clients are *not* proposed recipients for the
MP lifecycle set** — see §12.

### 5.5 Uploader provenance — where it lives and whether it is durable [DDL]/[CODE]

This is the evidence base for N4 and for the "Important uploader rule".

| Record | Column | Written where | Durable? |
| --- | --- | --- | --- |
| Customer/organisation document (canonical ingestion record) | `public.customer_documents.uploaded_by UUID` (`init_schema.sql:605`) | `backend/api/v3_document_uploads.py:315, 644` (`uploaded_by=actor.user_id`); `backend/api/v3_documents.py:279` (`uploaded_by=current_user.user_id`) | **YES** — written at upload from the authenticated actor |
| Consultant-uploaded document | same column | **`backend/api/v3_consultants.py:1318`** (`uploaded_by=current_user.user_id`) | **YES** — the uploading consultant's user id |
| Organisation file (storage record) | `public.organization_files.uploaded_by` (`init_schema.sql:550`) | `backend/data/organization_files.py:50–79` | YES |
| Upload batch | `public.upload_batches.created_by_user_id` **and** `created_by` (`init_schema.sql:1929, 1939`) | batch creation | YES |
| MP batch | `public.manual_extraction_batches.created_by` (`init_schema.sql:1130`) | batch creation | YES |
| MP work item | `public.manual_extraction_items.file_id` (used by `find_item_by_file_id`, `manual_extraction.py:419–443`) **and** `document_processing_queue_id` (`init_schema.sql:1142`) | enqueue | YES — links item → document |
| MP work item consultant provenance | `consultant_firm_id`, `processing_mode`, `consultant_provenance_at` (`20260910120000_p6_2d_consultant_provenance.sql:40–44`) | `manual_extraction.record_consultant_provenance` (`manual_extraction.py:697`) | YES — **the item records which firm submitted it** |

**Answers to the four questions the task asked about the uploader:**

1. **Where is uploader identity stored?** Primarily
   `customer_documents.uploaded_by`, with `organization_files.uploaded_by` and
   `upload_batches.created_by_user_id` as sibling records. [DDL]
2. **Is it durable?** **Yes** — written at upload time from the authenticated
   actor; never overwritten by assignment changes. [CODE]
3. **Does it survive reassignment?** **Yes.** Assignment is a *separate*,
   append-only concept; the D38 migration header states *"Immutable V1.2
   provenance (manual_extraction_items.processing_origin /
   processing_entity_id) is NEVER written by this migration or by the D38
   service; current assignment is a separate, changeable concept"*
   (`20260902030000_phase5_work_item_assignments.sql:20–22`). [DDL]
4. **Can the uploader differ from the responsible consultant?** **Yes,
   demonstrably.** A firm colleague with `can_upload_documents` may upload while a
   different member holds the client relationship; and an organisation's own
   member can upload (`v3_document_uploads.py:315`) with no consultant involved at
   all. Nothing in the data model enforces
   `uploader == responsible consultant`. **Do not assume `uploader == client`,
   `uploader == organisation owner`, or `uploader == every consultant in the
   firm`.** [CODE]/[INFER]

### 5.6 Work-item assignment and the "validator" concept [DDL]/[CODE]

* Canonical assignment ledger: `public.work_item_assignments`
  (`20260902030000_phase5_work_item_assignments.sql:25–61`) with
  **`assignee_kind CHECK (assignee_kind IN ('internal_staff','processing_entity'))`**,
  `assigned_to`, `processing_entity_id`, `assigned_by`, `actor_domain`, a
  **one-open-assignment-per-item** unique index (`:64–66`), and the shape
  constraint `work_item_assignee_shape` (`:55–60`).
  This table is the **only** work-item assignment record (routing migration
  header, `:27–28`). [DDL]
* RLS: **enabled with NO policies** (`:80–83`) — API-only access. [DDL]
* "Validator"/QC identity columns already exist:
  `manual_extraction_items.extracted_by / qc_by / qc_at` (`init_schema.sql:1155–1159`),
  `manual_extraction_batches.qc_by` (`:1123`),
  `document_processing_queue.manual_extracted_by / qc_by` (`:807, 811`). [DDL]
* **N2 is therefore resolvable** — an internal-staff assignment is stored in
  `work_item_assignments.assigned_to` when `assignee_kind='internal_staff'` —
  and P1 (`work_item.assigned`) already notifies **exactly that recipient** when
  the assignment is made through `ops_assign_item`. **N2 therefore partially
  exists today** — see §6.2. [CODE]

### 5.7 Actor-resolvability summary [CODE]/[INFER]

| Actor | Authoritative source | Existing notification resolver |
| --- | --- | --- |
| Internal ops (view-all) | `staff_profiles` + `staff_roles.permissions.can_view_all` | **`internal_ops_user_ids()`** |
| Internal ops (staff management) | `staff_profiles` + `can_manage_staff` | **`support_staff_user_ids()`** |
| Assigned internal validator | `work_item_assignments.assigned_to` | **`_notify_assignee` (P1)** — used only at `ops_assign_item:216` |
| **PE staff of an entity** | `staff_profiles.entity_id` | **NONE** (`staff.list_entity_staff` exists but is unused for notifications) |
| Firm members | `consultant_firm_members` | used by **P2** (lifecycle) only |
| Responsible consultant for a client | `consultant_clients` | **NONE** |
| **Uploader** | `customer_documents.uploaded_by` (+ `manual_extraction_items.file_id`) | **NONE** |
| Client org users | `organization_members` | used by **P7** only |

---

## §6 Manual Processing notification events (N1–N4) — actual current behaviour

### 6.0 How work actually enters Manual Processing

| Path | Trigger | Code | Result |
| --- | --- | --- | --- |
| **B (automatic fallback routing)** | an automatic-processing job fails a stage and the applicable FIN-06 grant + configured processor allow fallback | `backend/services/manual_processing_routing.py` → `work_item_open(action="assign", assignee_kind="processing_entity", processing_entity_id=…)` (`:356–366`) + audit `manual_processing:auto_routed` (`:368–387`) | one open D38 assignment + **one audit row** |
| **Human ops assignment** | operations assigns/claims an item | `backend/services/work_items.py` `ops_assign_item` (`:180–226`), `ops_claim_item` (`:229–234`) | assignment + audit; **P1 notification only when the target is a specific internal user** |
| **PE self-claim** | PE staff claims an eligible item | `pe_claim_item` (`work_items.py:358–392`) | assignment + audit; **no notification** |
| **PE release** | PE staff releases | `pe_release_item` (`work_items.py:395–422`) | close + audit; **no notification** |
| **PE completion** | PE staff completes | `pe_complete_item` (`work_items.py:425+`) | close + audit; **no notification** |

**Definitive evidence:** `grep -rn 'notif'` across
`backend/services/manual_processing_routing.py`,
`backend/domain/manual_processing.py`, `backend/data/manual_processing.py`,
`backend/data/manual_extraction.py`,
`backend/api/v3_manual_processing_coverage.py` and
`backend/api/manual_processing_admin.py` returns **zero matches**. [CODE]

### 6.1 N1 — PE work assignment [CODE]

| Question the task asked | Verified answer |
| --- | --- |
| Does a notification exist today? | **NO.** Routing creates the assignment and an audit row; it calls nothing on `repos.notifications`. |
| Can the PE discover the work anyway? | **YES, by pull** — `GET /api/v3/pe/work` (`v3_pe.py:150`), plus the entity batch/item lists (`manual_extraction.list_entity_batches / list_entity_items / next_entity_item_effective`) and the PE home/items pages that load on mount. |
| Is there polling? | **NO.** No `setInterval` anywhere in `frontend/src/v3/pe/*.jsx`; PE surfaces refresh only on mount or manual action. |
| What happens if a notification is disabled / absent? | **Identical to today**: the item appears in the queue on the next page load or manual refresh. No work is lost — the assignment row is durable. |
| Would optional notification risk unattended work? | **It is already the current state.** Work is not "attended" by notification today; it is attended by someone opening the PE workspace. `[INFER]` |
| Is a PE-resolving notification possible? | **Technically yes**, via `staff.list_entity_staff(entity_id)` → `user_id`; no producer does it. [CODE] |

> **Classification (consistent with NF-02 §7): the N1 notification requirement is
> NOT ESTABLISHED.** It is not required for the work to be actionable, because the
> assignment is durable and the queue is authoritative. Whether it is *desirable*
> (timeliness, SLA) is a business judgement — **[PO DECISION REQUIRED]**.

### 6.2 N2 — CarbonTally validator / internal assignment [CODE]

**This is the one place where something already exists.**

* `_notify_assignee` (`work_items.py:51–69`) → `notification_type="work_item.assigned"`,
  `priority=30`, `link=/ops/items/{item_id}`, idempotent.
* It fires **only** at `work_items.py:220–225`, guarded by
  `if assigned_to is not None and assigned_to != actor_user_id`. [CODE]
* Because `work_item_assignee_shape` forces `assigned_to IS NULL` for a
  `processing_entity` assignment, that guard is **false for every PE assignment**:
  **PE assignments are never notified**; only internal-staff assignments to a
  *different* user are. Self-assignment (`claim`) is deliberately not notified. [DDL]/[CODE]
* There is **no test** covering the PE claim/release/complete paths' notification
  behaviour (no assertions exist). [CODE]

> **Classification: for N2 the requirement is ALREADY IMPLEMENTED** for the
> ops-assign path, and the mechanism (durable, idempotent, per-assignee) is the
> established house convention. Extending the same treatment to PE-side
> assignment is a **scope question for the PO**, not a new architecture.

### 6.3 N3 — MP entry → submitting/responsible consultant [CODE]

| Question | Verified answer |
| --- | --- |
| Notification exists? | **NO.** No producer targets a consultant for MP entry. The only producer whose recipients are consultants is P2 (consultant *lifecycle*), and its five ratified events do not include MP entry (NF-02 §6.1). |
| Is it customer-facing communication? | By default it is **firm-internal operational** communication (the submitting consultant/firm). For a **direct** customer with no consultant it would become customer-facing if an org member were notified. |
| Existing status/work-item mechanism? | **Yes** — the client's batches/items/statuses are queryable (`manual_extraction.list_batches / list_items`, `workflow_dashboard`, `workflow_status`) and surfaced in the consultant workspace. *Pull* exists; *push* does not. |
| Is the recipient determinable? | **YES but underspecified**: the item records `consultant_firm_id` provenance and `consultant_clients` gives the firm↔org grant; the **specific human** ("the relevant consultant") is a PO choice (§5.3). |

> **Classification: N3 is a NEW requirement** — unsatisfiable by any existing
> producer. The **recipient rule is a PO decision, not an engineering one.**
> **[PO DECISION REQUIRED]**

### 6.4 N4 — MP completion → original uploader [CODE]

| Question | Verified answer |
| --- | --- |
| Notification exists? | **NO** for the MP path. `pe_complete_item`, `set_item_status`, `ct_qc_decision`, `customer_review` emit audit rows only. |
| Is the uploader deterministically identifiable? | **YES** — `customer_documents.uploaded_by`, reachable from the item via `manual_extraction_items.file_id` / `document_processing_queue_id` (§5.5). |
| What provenance exists? | `uploaded_by` (document), `created_by` (batch), `consultant_firm_id` / `processing_mode` (item). |
| Is the uploader always a consultant? | **NO.** It is whoever authenticated the upload — a consultant firm member, *or* an organisation member uploading directly. The PO's assumption "the uploader is a consultant" holds for the consultant-upload workflow but is **not enforced by the data model** (§5.5). |
| Is there an existing notification for a *client*? | **YES — but for a different workflow.** P7 (`automatic_processing._notify`, `:1939–1966`, called at `:1797`) notifies the organisation's `owner`/`admin` members with `processing.completed` after **automatic** extraction/mapping/validation/calculation. See §6.5. |

> **Classification: N4 is a NEW requirement.** The recipient is resolvable.
> Whether the *client* should ever be a recipient of an MP-lifecycle notification
> is explicitly out of scope per the stated business context — and note that an
> existing client notification already exists for the *automatic* path, which the
> PO should not be surprised to discover (§6.5). **[PO DECISION REQUIRED]**

### 6.5 The existing client-facing notification (must not be confused with N4) [CODE]

`automatic_processing.py:1939–1966`:

```python
async def _notify(self, job, notification_type, title, message) -> None:
    """Create an in-app notification for the org's owners/admins (best-effort)."""
    members = await self._repos.organizations.get_members(job.organization_id)
    for member in members:
        if getattr(member, "role", None) in ("owner", "admin"):
            await self._repos.notifications.create(
                member.user_id, notification_type=notification_type, …
                link=f"/processing/jobs/{job.id}")
    await self._repos.processing.mark_notified(job.id)
```

* Called once per job (`:1797`) under the guard `if job.notified_at is None`
  (`:1796`), with `notification_type="processing.completed"`.
* **Workflow attribution: automatic processing (AI/durable job pipeline), not
  Manual Processing.** It is not triggered from any MP code path (zero `notif`
  matches in the MP surfaces, §6.0).
* It is the **only** existing notification that targets a *customer
  organisation*, and it is a legitimate precedent that CarbonTally *already*
  notifies client-side users for a document-lifecycle milestone. [CODE]

**This task did not change it, and must not be read as recommending any change to
it.**

### 6.6 Event matrix — proposed vs actual

| Event | Proposed recipient | Exists today? | Emitted at | Recipient resolvable? | Classification |
| --- | --- | --- | --- | --- | --- |
| **N1** MP work assigned | PE (entity staff) | **NO** | `manual_processing_routing.py:356–387` (assignment + audit) | yes (`list_entity_staff`) | **REQUIREMENT NOT ESTABLISHED** (durable queue exists; pull works) |
| **N2** validation assigned | assigned internal validator | **PARTIALLY** | `work_items.py:216 → 220–225` (`work_item.assigned`) for internal targets only | yes (`assigned_to`) | **ALREADY IMPLEMENTED** for ops-assign; PE-side is new |
| **N3** MP entry | responsible/submitting consultant | **NO** | (nothing) | yes (`consultant_clients`, `consultant_firm_id`) — *which* consultant is a PO choice | **NEW REQUIREMENT** |
| **N4** MP completion | original uploader | **NO** | (nothing) | yes (`customer_documents.uploaded_by`) | **NEW REQUIREMENT** |
| — | client organisation | **EXISTS for the automatic path only** | `automatic_processing.py:1797` | yes (`organizations.get_members`) | **excluded from MP lifecycle by PO context** |

### 6.7 Governance cross-check: does P-2 already answer the N1–N4 question? [DOC]

Read strictly, **no**.

* `CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` §5 decides that
  **"Manual Processing allocation and release transitions remain audit-only"**
  (`:33–34`) and lists, among the twelve sub-items, *"No new notification event
  types are authorised"* (`:37`) and *"No new notification preference system is
  authorised"* (`:39`).
* NF-02 established (and the governance follow-up in
  `CT-MP-SUB-004-PROD-READINESS-01-report.md` §22 records) that
  **P-2's scope is the coverage allocation/release surface**, and that
  *"must any actor be notified when a document batch/item enters Manual
  Processing"* is **OPEN — PO DECISION REQUIRED** (`§22`, `:755`).
* Therefore the N1–N4 set is **outside** P-2's closed scope. [DOC]

**Caveat the PO must see.** P-2 sub-item 7 (*"No new notification preference
system is authorised"*) is **scoped** to the coverage surface by that
clarification. If the PO selects a *configurable* option in §9, the cleanest
governance move is to record the new decision explicitly **and** note the
relationship to P-2 item 7, rather than silently reading P-2 as permitting a
preference system for a different surface. **[INFER]** — flagged so the PO can
choose how to record it.

---

## §7 Configuration options — evaluated against CarbonTally's actual architecture

### 7.1 The comparison matrix

Every cell is grounded in §2–§6 evidence. "Existing fit" means *how closely the
option matches a mechanism that CarbonTally already has in the live tree*.

| Option | Existing architecture fit | DB support | RLS impact | Admin UX impact | Workflow risk | Complexity | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A. Mandatory** (all authorised MP lifecycle notifications always generated; no toggle) | **HIGH** — this is what *every* one of the 8 existing producers already does; **no producer anywhere checks a preference** (§3.3) | **NONE required** — `notification_type` is free-form and unconstrained (§2.1) | **NONE** — producers write via the service-role pool; `notifications` stays fail-closed (§2.5) | **NONE** | **LOWEST** — matches current N2 behaviour and the X2 alerting precedent | **LOWEST** — new producers only, reusing `create_idempotent` | **Strongest fit for the event layer** — but see §11: the *delivery* question must still be answered |
| **B. Platform Admin configurable** | **HIGH** — reuses the proven `system_settings` + `/api/v3/settings/*` pattern **and** the MP admin control-plane idiom (§4.1, §4.2) | **NONE** — one new `setting_key` row in an existing table | **NONE** — `system_settings` already fail-closed and admin-API-only | **LOW** — one new admin card/route following six existing precedents | **MEDIUM** — a mis-set policy silently stops operational notifications; needs fail-closed defaults + audit | **LOW–MEDIUM** — no new table, no new RLS; a repository method + route + tests | **RECOMMENDED *only* if the PO wants an off-switch** — the cheapest configurability that exists |
| **C. Organisation configurable** | **LOW** — no org-level settings store exists anywhere (§4.3) | **NEW TABLE or NEW COLUMN required** | **NEW RLS required** + a new "who may change it" authorization rule | **HIGH** — no org-settings surface exists to extend | **MEDIUM–HIGH** — a client org could disable signals the PE/ops side depends on | **HIGH** — table + RLS + repo + API + org UI + role decision | **NOT recommended for a first implementation** |
| **D. Individual user configurable** | **LOWEST** — no user-preference store exists; the only look-alike UI is **dead code** (§4.4) | **NEW TABLE required** | **NEW RLS required** (self-service yet tenant-safe) | **HIGH** — needs a real user-facing preferences surface (none exists) | **HIGH** — a PE user could mute work notifications and miss assigned work; needs a "cannot opt out of workflow-critical" rule | **HIGHEST** — table + RLS + API + UI + a new policy concept | **NOT recommended for a first implementation** |
| **E. Event-level configuration** | **MEDIUM** — fits the admin settings pattern, but event identity is an *unindexed free-form string* (§2.4) | **NONE** (a JSON allow-list in `system_settings`) — add an index if queried | **NONE** | **MEDIUM** — an event-toggle matrix is a denser admin UI | **MEDIUM–HIGH** — every toggle is a way to silently disable a workflow signal | **MEDIUM** | **Only as a *sub-set* of B** (a small fixed list of MP event toggles), if at all |
| **F. Channel-level configuration** | **HIGHEST schema alignment** — `notification_delivery.channel` already exists and X2 already writes two channels (§2.2, §3.5) | **NONE** — delivery rows already support multiple channels | **NONE** | **LOW** (platform) / **MEDIUM** (per-user) | **LOW** — the event still exists and still appears in-app | **LOW–MEDIUM** — replays X2's `record_delivery` pattern | **RECOMMENDED for the delivery layer** — the natural place to be configurable |
| **G. Reuse an existing mechanism wholesale** | **PARTIAL** — no existing mechanism covers *notification* configuration; the nearest whole mechanism is X2 alerting (hard-coded channels, PO-fixed recipients) | n/a | n/a | n/a | n/a | n/a | **Does not exist as a drop-in.** What *is* reusable: the **code pattern** (`create_idempotent` + `record_delivery` + event keys) and the **admin pattern** (`system_settings` key) — not a ready-made policy object |

### 7.2 Option A — Mandatory

**Evidence for:**
* Every existing producer is unconditional (§3.3). A mandatory MP lifecycle set
  is therefore the *consistent* choice, not a novelty.
* The X2 alerting contract is PO-ratified as "*internal only, no invented
  recipients*" and emits **always**, for **all** qualifying recipients. [DOC]
* Mandatory events avoid the failure mode where an operator disables a
  notification and an operational signal silently disappears. [INFER]

**Evidence against:**
* It removes the PO's future ability to tune noise without a code change.
* It cannot express the very reasonable policy *"in-app always, email optional"* —
  that requires F, not A.

**Verdict:** [REC] **A is the correct choice for the *event* layer.**

### 7.3 Option B — Platform Admin configurable

**Evidence for:**
* The mechanism exists, works, is audited, is RLS-safe, and already serves six
  configuration domains (§4.1) — including one literally named
  `platform_notifications`.
* MP policy is *already* admin-configured in three places (§4.2), so an admin
  switch is idiomatic for this domain.
* Fail-closed defaults are an established rule of the pattern (§4.1 rule 3).

**Risks:**
* An admin switch that disables operational notifications is a **silent
  operational hazard**: nothing fails; work simply stops being announced. Any such
  switch needs (a) a fail-closed default, (b) audit via `updated_by`, and (c) an
  explicit "workflow-critical events are not disableable" carve-out if the PO
  wants one.
* It overlaps what `notification_type` already expresses, so it must be a small,
  **closed** set rather than an open vocabulary.

**Verdict:** [REC] **Acceptable and cheap — but only as a bounded "notification
policy" key with a closed field allow-list**, never a generic per-event toggle bag.

### 7.4 Option C — Organisation configurable

**Evidence:**
* No organisation settings store exists (§4.3); `organization_settings` is an
  unapplied design-doc artefact only.
* CarbonTally's organisation-level commercial model (`customer_subscriptions`,
  `billing_plans`, `billing_commercial_config`) is explicitly *commercial*, and
  the newest migrations state a firm design boundary against duplicating it
  (`20261101000000_…:18–32`). [DDL]

**Risks:** a customer organisation could switch off notifications that the
Processing Entity or CarbonTally operations rely on — i.e. a tenant could degrade
another party's operational visibility. Resolving that needs a
"core events are not org-configurable" rule plus a new authorization decision for
*who* inside the org may change it (owner only? owner+admin?).

**Verdict:** [REC] **Do not introduce for a first implementation.** If the PO
ever wants tenant control, the sane boundary is *channel* configuration only
(Option F at org level), not event suppression.

### 7.5 Option D — Individual user configurable

**Evidence:**
* No user preference store exists (§4.4). The only apparent precedent,
  `NotificationSettings.jsx`, is **dead code with non-persisted toggles** — it
  cannot be "extended" without first being built.
* Every existing recipient set is **server-derived** and deliberately
  non-negotiable (`support_staff_user_ids`, `internal_ops_user_ids`,
  `entity_participant_user_ids`; §3.2). The architecture's whole posture is
  "the server decides the recipients". [CODE]

**Risks:** a PE operator or operator-internal user could mute the very signal that
tells them work exists. Any user-level option therefore has to be split into
"mutable (marketing/optional)" and "immutable (workflow-critical)" categories —
which is itself a new product concept with no existing basis.

**Verdict:** [REC] **Do not introduce for a first implementation.** If the PO wants
user control, restrict it to the **delivery channel** (F) for *non-critical*
events, and explicitly forbid opting out of workflow-critical events.

### 7.6 Option E — Event-level configuration

**Evidence:**
* Fits the admin settings pattern mechanically, but `notification_type` has **no
  index, no enum and no registry** (§2.4) — an event toggle list would be a
  hard-coded allow-list in a JSONB payload, which the settings pattern explicitly
  supports (`POLICY_FIELDS` allow-listing, §4.1 rule 2). [CODE]
* The existing event vocabulary is small and namespaced (`work_item.assigned`,
  `consultant.lifecycle.*`, `pe_msg.*`, `ops_alert_*`, `backup`, `general`,
  `processing.completed`; §3.3) — so a closed list is feasible. [CODE]

**Risks:** every toggle is a latent way to silence a workflow signal; the noise
argument for toggles is real but small at four events.

**Verdict:** [REC] **Only acceptable as a tightly bounded subset of B**, with the
workflow-critical events (N1, N2) declared non-disableable if the PO so chooses.

### 7.7 Option F — Channel-level configuration

**Evidence for (strongest schema alignment in this report):**
* The schema **already** models the event and the delivery separately
  (`notifications` vs `notification_delivery.channel`; §2.2). [DDL]
* The X2 producer **already** implements two channels with honest per-channel
  delivery records and bounded retry (§3.5). [CODE]
* Email infrastructure already exists end-to-end (Resend, `email_sender`,
  `email_provider`, `email_logs`) and is already admin-configured — the
  *provider* is a `system_settings` key (§4.1). [CODE]
* Adding a channel to an existing event is **additive**: no event semantics
  change, no RLS change, no new table. [INFER]

**Risks:** email to external addresses has consent/anti-spam and deliverability
implications. Those are exactly the implications P-2 cited when declining email
for the coverage surface
(`CT-MP-SUB-004-PROD-READINESS-01-report.md:493`: *"New user-facing behaviour with
email-provider, consent and anti-spam implications"*). [DOC] The PO must own that
decision for the MP lifecycle set too.

**Verdict:** [REC] **F is the natural place for configurability.** "Event
mandatory + channel optional" is not merely an option — it is the shape the
existing schema and the existing X2 producer already assume.

### 7.8 Option G — Reuse an existing mechanism wholesale

**Evidence:** There is no existing notification-*policy* mechanism to reuse
(§4.9). The nearest analogue, X2 alerting, does **not** offer configuration — it
offers a **fixed, PO-ratified recipient set** and **hard-coded channels**
(`CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md:4, 41–42`). [DOC]/[CODE]

What *is* reusable, and is recommended as the implementation substrate:

| Reusable asset | Source |
| --- | --- |
| Durable, idempotent event writing | `NotificationsRepository.create_idempotent` + `uq_notifications_event_key` |
| Server-generated, deterministic event keys | `lifecycle_event_key` pattern (`consultant_lifecycle.py:83–100`) |
| Per-channel delivery recording + bounded retry | `operational_alerting.py` `_dispatch_one` / `_deliver_email` / `record_delivery` |
| Platform-level, audited, fail-closed configuration | `system_settings` key + `SettingsRepository` + `require_admin()` route |
| Admin control-plane idiom for MP policy | `manual_processing_grants` / `manual_processing_processors` / `consultant_mp_allocations` |
| Email transport + sender configuration | `utils/email.py`, `email_sender`, `email_provider`, `/api/v3/settings/notification-sender` |
| Frontend inbox consumption | `listNotifications` API (works today, RLS-safe) |

**Verdict:** [REC] **There is no drop-in policy object — but there is a complete,
proven *kit* of parts.** Any option the PO selects should be assembled from the
assets above rather than invented.

### 7.9 What the options *do not* change

For the avoidance of doubt, **none** of A–G requires:

* any change to `public.notifications` or `public.notification_delivery` columns;
* any change to the fail-closed RLS posture (§2.5);
* any Realtime change (Realtime cannot deliver these rows to browsers today —
  §2.5 point 2 — so no option depends on it);
* any change to `public.notification_templates`, `email_logs`, or the sender
  configuration;
* any change to the existing P1–P8 producers.

---

## §8 Architectural recommendation

> ## **ARCHITECTURAL/PRODUCT RECOMMENDATION — NOT YET A PO DECISION**
>
> Everything in §8 is **Cline's recommendation** ([REC]), derived from the
> evidence in §2–§7. It is **not** a PO decision, **not** implemented, and
> **not** authorised. The PO may accept, reject or amend any part of it.

### 8.1 The recommendation in one paragraph

**Make the *event* mandatory and make the *delivery channel* the configurable
dimension.** Manual Processing lifecycle notifications N1–N4 should each be
generated unconditionally by the server (Option A at the event layer), because
that matches the behaviour of all eight existing producers and needs no schema,
RLS or preference machinery. Configurability, where the PO wants it, should be
expressed as **channel** policy (Option F) — and, if an operational off-switch is
required at all, as **one bounded Platform Admin setting** (Option B) rather than
organisation- or user-level preferences (Options C/D), for which CarbonTally has
**no existing foundation whatsoever**.

### 8.2 The specific answers the task requires

| # | Question | Recommendation | Basis |
| --- | --- | --- | --- |
| 1 | **Should workflow-critical notifications be mandatory?** | **YES.** N1 and N2 in particular: they announce work that a party must act on. | Every existing producer is unconditional (§3.3); a muted work signal has no compensating control in the PE workspace (no polling — §5.2) |
| 2 | **Should notification delivery be configurable?** | **YES — but only the delivery dimension**, not whether the business event produces a notification. | The schema already separates the two (§2.2); X2 already writes per-channel delivery rows (§3.5) |
| 3 | **If configurable, at what level?** | **Platform Admin** (the only level with an existing, audited, RLS-safe mechanism — §4.1) plus, at most, **channel** granularity. **Not** organisation-level, **not** user-level for a first implementation. | §4.3/§4.4 show C and D are greenfield; §4.1/§4.2 show A/B are established |
| 4 | **Should PE assignment notification (N1) be configurable?** | **No — not as an event.** If the PO authorises N1 at all, it should be mandatory in-app. | A PE has no polling and no Realtime for work items (§5.2); suppressing the only announcement would risk unattended work |
| 5 | **Should validator assignment notification (N2) be configurable?** | **No — not as an event.** It already exists and is mandatory (P1, `work_item.assigned`) for the ops-assign path. | §6.2 |
| 6 | **Should uploader completion notification (N4) be configurable?** | **Channel-level only.** The event is a legitimate operational completion signal; whether it also goes by email is a reasonable per-installation choice. | §6.4; email consent implications are a PO matter (§7.7) |
| 7 | **Should in-app delivery be mandatory?** | **YES.** In-app is the only channel that is guaranteed today: the row is durable and readable through `/api/v3/notifications` regardless of Realtime or RLS. | §2.5, §3.5 |
| 8 | **Should email be separately configurable?** | **YES — and it should be OFF by default unless the PO explicitly authorises it.** Email to external parties introduces consent/anti-spam/deliverability obligations that P-2 already identified as the reason to decline email for a different surface. | §7.7; `…PROD-READINESS-01-report.md:493` [DOC] |
| 9 | **Should Admin control this?** | **YES, if anything is configurable.** Platform Admin only, via a new `system_settings` key with a closed field allow-list, fail-closed defaults and `updated_by` audit. | §4.1 |
| 10 | **Should individual users control this?** | **NO for a first implementation.** There is no user-preference store and no working UI; and the architecture's posture is that the server decides recipients. | §3.2, §4.4 |

### 8.3 What "minimum schema/configuration change" would be required

Under the recommended model (**mandatory events + channel-level policy + at most
one Admin key**):

| Change | Required? |
| --- | --- |
| New table | **NO** |
| New column on `notifications` / `notification_delivery` | **NO** (`channel` already exists) |
| New migration for the notification tables | **NO** |
| New RLS policy | **NO** (`notifications` stays fail-closed; producers use the service-role pool) |
| New `notification_type` index | **Only if** a type-keyed configuration query is added — recommended if Option E is chosen |
| New `system_settings` row | **YES, if any policy is configured** — one new `setting_key` (e.g. a bounded `manual_processing_notification_policy`), applied through the existing upsert path (`settings.py:263–276` pattern) |
| New admin route | **YES, if configured** — one `GET`/`PUT` pair under `/api/v3/settings/*`, `Depends(require_admin())` |
| New producer code | **YES, for whatever events the PO authorises** — using `create_idempotent` + server-generated event keys + `record_delivery` for channels |
| New recipient resolvers | **YES, for N1/N3/N4** — see §10.3 |

**In short: the recommended model needs at most one settings row and one admin
route — no schema, no RLS, no new table.**

### 8.4 The event-vs-delivery distinction (explicitly evaluated)

The task requires this distinction to be evaluated explicitly, and it is the
pivot of the whole recommendation.

**Two possible policies:**

```
POLICY 1 — mandatory event, configurable delivery          POLICY 2 — optional event
───────────────────────────────────────────────           ─────────────────────────
   MP lifecycle EVENT  (always produced)                     MP lifecycle EVENT
        ├── in-app    (mandatory)                                 └── (on/off per event)
        └── email     (optional / configurable)                      └── in-app (+ whatever channel)
```

| Aspect | **Policy 1** (mandatory event / configurable channel) | **Policy 2** (optional event) |
| --- | --- | --- |
| Which architecture is CarbonTally's design already closest to? | **POLICY 1 — decisively.** `notifications` (the event) and `notification_delivery.channel` (the delivery) are **separate tables** (§2.2), and the only multi-channel producer already writes per-channel delivery rows while always producing the event itself (§3.5). | **Not represented anywhere.** No table, column, key or flag expresses a per-event on/off state (§4.5). |
| Schema change needed | **None** | `system_settings` JSON (no migration) *or* a new table if indexed |
| Failure mode if misconfigured | Email silently stops; the in-app signal survives — degraded, not lost | **The operational signal disappears entirely** |
| Precedent | X2 alerting (`PX-6`): PO fixes recipients; the implementation still always produces the event | None in this repository |
| Governance clarity | The PO decides a *channel* question — narrow, reversible, low-consequence | The PO decides a *"should this work signal exist at all"* question — broad, and touching AGENTS.md §47/§74 |

**Conclusion ([REC], not a PO decision):** CarbonTally's existing design is
**closest to Policy 1 by construction**, and Policy 1 is the safer default. Make
the event mandatory; let the channel be the configurable dimension.

### 8.5 What the recommendation deliberately does **not** do

* It does **not** decide whether N1–N4 should exist at all — that is the PO's
  §7.3/§9 question, and NF-02 already classified N1 as *requirement not
  established*.
* It does **not** choose recipients. Per §4.8 (PX-6 precedent), **recipients are
  a PO decision**, and for N3 in particular the PO must name *which* consultant.
* It does **not** authorise email. Email to external parties is a consent/anti-spam
  decision the PO must take explicitly.
* It does **not** authorise any implementation.

---

## §9 Minimum PO decision required

### 9.1 The smallest precise question

> **Should Manual Processing lifecycle notifications (N1 PE assignment, N2
> validator assignment, N3 MP-entry → responsible consultant, N4 MP-completion →
> original uploader) be generated as mandatory events, with only the delivery
> channel (in-app vs email) being configurable — or should the events themselves
> be individually enable/disable-able, and if so by Platform Admin only?**

Derived from the evidence, the PO is being asked to settle **two coupled
sub-questions**:

| Sub-question | Options | Evidence that forces the choice |
| --- | --- | --- |
| **Q1 — Which events exist at all?** | (a) none; (b) N1 only; (c) N1+N3; (d) N3+N4 (consultant-facing only); (e) all four | N1 = *requirement not established* (§6.1); N2 already implemented (§6.2); N3/N4 = new (§6.3, §6.4). NF-02 §7.3 already left the *"notify on MP entry"* question open. |
| **Q2 — Is the event mandatory or configurable, and at what level?** | (a) mandatory, channel-configurable only; (b) mandatory, no configuration; (c) Platform-Admin-configurable per event; (d) org- or user-configurable | Only Platform Admin (B) has an existing mechanism (§4.9). No org- or user-level foundation exists (§4.3, §4.4). |

### 9.2 Explicit PO choices the report cannot make

| # | Choice | Why it is a PO decision |
| --- | --- | --- |
| 1 | Do N1 (PE) and N3 (consultant) notifications *exist* at all? | A business judgement about timeliness vs interruption; NF-02 established the requirement is not technically necessary |
| 2 | For N3, **which** consultant is "the relevant consultant"? | Uploader? firm owner? every `can_manage_clients` member? every firm member? All are resolvable; the answer is policy (§5.3) |
| 3 | For N4, may the **original uploader** ever be a **client** org user (direct-customer upload)? | Creates client-facing communication that the stated business context excludes (§12) |
| 4 | Is **email** in scope at all for these events? | Consent/anti-spam/deliverability; the PO declined email for the coverage surface on exactly these grounds (§7.7) |
| 5 | Does an operational **off-switch** need to exist? | Determines whether Option B is needed at all, or whether Option A suffices |
| 6 | How is this recorded relative to **P-2 sub-item 7** ("no new notification preference system")? | Governance hygiene — the scopes are distinct but the PO should say so explicitly (§6.7) |

### 9.3 Recommended shape of the PO decision record

[REC] The PO decision should state, as a minimum:

1. **Which of N1–N4 are authorised** (by name).
2. **For each authorised event: the recipient rule** (the exact actor set).
3. **Whether the event is mandatory or Admin-configurable** (and if the latter,
   the closed list of configurable fields and the fail-closed default).
4. **Channel policy**: in-app mandatory; email *authorised / not authorised*
   (and if authorised, per-event or global).
5. **A statement of the relationship to P-2** (distinct scope; P-2 item 7 not
   disturbed).
6. **A statement that no organisation-level or user-level preference mechanism is
   authorised** (unless the PO decides otherwise, in which case a separate,
   larger scope follows).
7. **Explicit confirmation that implementation is a *separate* task** requiring
   its own authorisation, tests and independent verification.

---

## §10 Migration / implementation impact

**No migration was created, authored or applied by this task.** The following is
a *conceptual* impact assessment only.

### 10.1 Impact per option

| Option | Migration required? | Structure required | RLS required? | New Admin API? | Concretely, what would have to change |
| --- | --- | --- | --- | --- | --- |
| **A. Mandatory** | **NO** | reuse `notifications` (+ `notification_delivery` for channels) | **NO** | **NO** | new producer functions + recipient resolvers only |
| **B. Platform Admin** | **NO** (one `system_settings` row is data, not schema) | reuse `system_settings` (`setting_key`/`setting_value JSONB`) | **NO** (already fail-closed, admin-API-only) | **YES — one `GET`/`PUT` pair** under `/api/v3/settings/*` | repository read/write method with a closed `POLICY_FIELDS`-style allow-list; route under `require_admin()`; admin UI card |
| **C. Organisation** | **YES** | **new table** (e.g. `organization_notification_settings`) *or* a new keyed column | **YES — new policies** (org-scoped read for members; write for owner/admin) + a new authorization decision | **YES** (org-scoped API) | table + RLS + repo + API + organisation settings UI + "who may change it" rule |
| **D. Individual user** | **YES** | **new table** (e.g. `user_notification_preferences`) | **YES — new self-service RLS** that is also tenant-safe | **YES** (user-scoped API) | table + RLS + repo + API + user settings UI + a "workflow-critical cannot be muted" concept |
| **E. Event-level** | **NO** (JSON allow-list in `system_settings`) | reuse `system_settings`; **recommend a `notification_type` index** if queried | **NO** | **YES** (extend the B route) | closed event-key list; producer-side lookup on each emit; tests |
| **F. Channel-level** | **NO** | reuse `notification_delivery.channel` | **NO** | **ONLY IF** platform-configurable (then as B's route) | producers call `record_delivery` per channel, X2-style; channel-selection helper; tests |
| **G. Existing mechanism** | n/a | n/a | n/a | n/a | n/a — no drop-in exists (§7.8) |

### 10.2 If a migration *were* required (conceptual only — **NOT created**)

Only Options C and D would require schema. Conceptually:

* **C** would need one new table with an `organization_id` FK to
  `public.organizations`, a small closed column set (per-event booleans or a
  `policy JSONB`), `updated_by`/`updated_at`, **RLS enabled with tenant-scoped
  policies** (a departure from the fail-closed-zero-policy house pattern used for
  `manual_processing_*` tables), plus a new authorization rule for who may write.
* **D** would need one new table keyed to the authenticated user, RLS permitting
  self-read/self-write, plus a designed "not mutable" class for workflow-critical
  events. **Neither is proposed here.**

Both would also require a **new migration file**, application of which is a
production change and is **not authorised by this fact-find**.

### 10.3 Recipient resolvers that any authorised implementation would need

| Event | Resolver to add | Existing query to reuse |
| --- | --- | --- |
| **N1** | PE staff of the assigned entity | `backend/data/staff.py:91` `list_entity_staff(entity_id)` → `user_id` |
| **N2** | (none new) | `work_item_assignments.assigned_to`; P1 `_notify_assignee` already exists |
| **N3** | responsible/submitting consultant(s) for a client | `consultants.list_active_client_grants(organization_id)`, `list_firm_members(firm_id)`, `manual_extraction_items.consultant_firm_id` |
| **N4** | original uploader | `customer_documents.uploaded_by` reached via `manual_extraction_items.file_id` / `document_processing_queue_id` |

Each new resolver must be **server-derived** (never request-supplied), matching
the existing convention (`consultant_lifecycle.py:28–31`: *"Server-derived
recipients only… A request can never choose a recipient."*). [CODE]

### 10.4 Test impact

| Existing test | Impact of any MP notification work |
| --- | --- |
| `test_ct_mp_sub_004_prod_readiness.py::TestNV10NotificationBehaviour` (`:487–530`) | **Must stay green.** It asserts allocation/release emit **no** notification. Any new MP *lifecycle* notification must not be triggered by the coverage allocate/release paths, or these tests fail — a useful safety rail. |
| `test_v3_notifications.py` | Unaffected (API contract) |
| `test_p6_2e_consultant_lifecycle.py` | Unaffected unless a new lifecycle event type is added — which P-2 item 5 does not authorise for the coverage surface |
| `test_operational_alerting_x2_runtime.py` | Unaffected |
| New tests required | event-key determinism; recipient-set correctness (allow **and** deny); idempotency on retry; channel delivery rows; and — if Option B/E is chosen — a fail-closed-default test for a missing/malformed settings row |

### 10.5 Independent-verification impact

Per NF-02 §9.2/§9.3/§9.4, the verification target for the **coverage** surface is
unchanged. If the PO authorises any N1–N4 event, independent verification must be
**extended** to cover:

* the new event(s) exist, are idempotent, and carry server-generated keys;
* the recipient set is exactly the PO-authorised set (positive and negative);
* MP coverage allocate/release **still emit no notification**
  (`TestNV10NotificationBehaviour` semantics preserved);
* in-app delivery is durable and readable via `/api/v3/notifications` for the
  intended recipient and **not** readable by any other actor;
* if channels are enabled: per-channel `notification_delivery` rows exist and a
  failed email is recorded honestly, never as sent.

---

## §11 Production safety

| Safety property | Status | Evidence |
| --- | --- | --- |
| No production database accessed | **CONFIRMED — not accessed** | Only repository files, schema/migration SQL and source were read. No DB connection was made. |
| No production credentials used | **CONFIRMED — none used** | No credential, token, connection string or signed URL was read, printed or used. |
| No migration authored, edited or applied | **CONFIRMED — none** | `supabase/migrations/` is unchanged; no new `.sql` file exists. |
| No RLS change | **CONFIRMED — none** | No policy, grant or enable/disable statement was written. `notifications` remains fail-closed with zero policies. |
| No code change (backend or frontend) | **CONFIRMED — none** | The only file created is this report. |
| No notification behaviour change | **CONFIRMED — none** | No producer, recipient rule, event type or preference was added or altered. |
| No Realtime change | **CONFIRMED — none** | No channel, publication or subscription was added or modified. |
| No test / fixture change | **CONFIRMED — none** | No test file, fixture, seeder or demo-lab script was modified. |
| No demo data change | **CONFIRMED — none** | The investor demo dataset and Demo Lab were not touched. |
| No commit | **CONFIRMED — no commit** | `git log -1` is still `375a48dc… FINAL-03: freeze production cutover release`; `git diff --cached` is empty (0 staged). |
| No push | **CONFIRMED — no push** | No remote operation was performed. |
| No deploy / no production access | **CONFIRMED — none** | No deployment, Render/Vercel/Supabase write, or remote call was made. |
| No secrets introduced | **CONFIRMED — none** | This report contains no credential, token, JWT, signed URL, password or DB connection string. |
| Working tree otherwise preserved | **CONFIRMED** | Pre-existing modified/untracked files were neither reverted nor cleaned. |
| Files created by this task | **exactly one** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-POLICY-FACTFIND-03-report.md` (new, untracked) |
| Files modified by this task | **none** | — |

**Prohibited actions — explicit confirmation that none occurred:** adding
notification functionality, notification preferences, Admin settings, database
tables, migrations, RLS changes, notification code changes, Supabase Realtime
changes, frontend changes, backend changes, test changes, fixture changes, or any
change to existing product behaviour.

---

## §12 Final status

**Summary of the answer to the primary question:**

> Based on the actual CarbonTally architecture, the **event** layer should be
> **mandatory** — every existing producer is unconditional, `notification_type`
> is unconstrained (so no migration is needed), the assignment/queue state is
> durable, and the fail-closed RLS posture means Realtime is decoration rather
> than a dependency. The **configuration** dimension CarbonTally can genuinely
> support today is **delivery channel** (the schema already separates
> `notifications` from `notification_delivery.channel`) and, at most, **one
> bounded Platform Admin setting** (the `system_settings` key pattern, already
> used for six configuration domains and already admin-gated and audited).
> **Organisation-level and individual-user-level notification configuration do
> not exist in any form** — the only look-alike UIs are dead code and a
> documented no-op — so Options C and D would be new capabilities, not reuse.
> No schema change, no RLS change and no migration is required by the recommended
> model.

**Governance position:** this report **does not decide anything**. N1–N4 remain
unauthorised; the MP-entry notification question remains **OPEN — PO DECISION
REQUIRED** (P-2 CLOSED applies **only** to coverage allocation/release, per the
NF-02 governance follow-up recorded identically in
`CT-MP-SUB-004-PROD-READINESS-01-report.md` §22,
`…-PO-DECISIONS-01-report.md` §H and `…-PO-FACTFIND-01-report.md`). The
authoritative decision record
`docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` was **read
only and is unmodified**.

**Next step:** PO selects the notification policy/configuration model (from §9)
→ formal PO decision record → separate implementation task → independent
verification.

NOTIFICATION POLICY FACT-FINDING COMPLETE — READY FOR PO DECISION

---

## Appendix A — Findings summary (one line each)

| # | Finding | Evidence |
| --- | --- | --- |
| F-NP3-1 | `notifications` has **no** `organization_id`/tenant column and a bare, FK-less `recipient_id`; scoping is purely `recipient_type='user' AND recipient_id=$1` in the repository. | §2.1 |
| F-NP3-2 | `notification_delivery.channel` **already models delivery separately from the event** — the schema is channel-separable by construction. | §2.2 |
| F-NP3-3 | `notification_templates` exists but is **not used by any V3 producer**; copy is code, not configuration. | §2.3 |
| F-NP3-4 | `notification_type` is a **free-form VARCHAR with no enum, no CHECK and no index** — new event types need no migration, but type-keyed *configuration* would need an index. | §2.1, §2.4 |
| F-NP3-5 | `notifications` is **RLS fail-closed with ZERO policies** (CT-FINAL-03); the API is the only read path and Realtime cannot deliver these rows to a browser. | §2.5 |
| F-NP3-6 | **No notification preference/settings table, column, flag or key exists at any level.** `organization_settings` and `feature_flags` exist only as unapplied design docs. | §2.7 |
| F-NP3-7 | **Every** existing producer emits unconditionally — no producer anywhere checks a preference, flag or setting. | §3.3 |
| F-NP3-8 | Exactly **three** recipient resolvers exist; there is **no resolver** for PE staff, the responsible consultant, or the uploader. | §3.2, §5.7 |
| F-NP3-9 | `operational_alerting.py` is the **only** two-channel producer (in-product + email) with per-channel `record_delivery`, bounded retry and honest failure recording — the ratified "mandatory event, recorded delivery" precedent. | §3.5 |
| F-NP3-10 | Platform Admin configuration is an **established, audited, fail-closed, RLS-safe pattern** (`system_settings` + `/api/v3/settings/*`), already carrying a `platform_notifications` key (sender only). | §4.1 |
| F-NP3-11 | MP policy is **already** Admin-configured three times (grants, processors, allocations), all audited — an existing control-plane idiom for MP. | §4.2 |
| F-NP3-12 | **No organisation-level configuration exists**; `organization_settings` is an unapplied design artefact. | §4.3 |
| F-NP3-13 | **No user-level configuration exists.** `frontend/src/components/NotificationSettings.jsx` is **dead code** (never imported) with non-persisted `defaultChecked` toggles; the Admin Settings "Session & Notifications" card is a documented **no-op** for notification fields. | §4.4 |
| F-NP3-14 | The PO has **already** taken this class of decision once (PX-6): recipients and channels are **PO choices**, not implementer choices. | §4.8 |
| F-NP3-15 | **No MP surface contains any notification code** (`grep notif` → zero matches across six MP modules). MP transitions are audit-only. | §6.0 |
| F-NP3-16 | **N1 (PE assignment) requirement is NOT ESTABLISHED**: routing creates a durable D38 assignment + audit and no notification; the PE queue is pull-only with **no polling and no Realtime**. | §6.1 |
| F-NP3-17 | **N2 (validator assignment) already exists** — `work_item.assigned` fires for internal-staff assignments to another user; the guard (`assigned_to is not None`) means **PE assignments are never notified**. | §6.2 |
| F-NP3-18 | **N3 and N4 are new requirements**; both recipients are resolvable from existing data, but *which* consultant (N3) is a PO choice. | §6.3, §6.4 |
| F-NP3-19 | Uploader provenance (`customer_documents.uploaded_by`) is **durable and survives reassignment**, but the uploader is **not** guaranteed to be a consultant, the client, or the org owner. | §5.5 |
| F-NP3-20 | An **existing client-facing notification** (`processing.completed` → org owner/admin, `automatic_processing._notify`) belongs to the **automatic-processing** workflow, not MP. Not changed; must not be confused with N4. | §6.5 |
| F-NP3-21 | P-2 **does not** answer the N1–N4 question (its scope is coverage allocation/release); P-2 sub-item 7 ("no new notification preference system") should be addressed explicitly in any new decision. | §6.7 |
| F-NP3-22 | The recommended model requires **no migration, no RLS change and no new table** — at most one `system_settings` row and one admin route. | §8.3, §10.1 |
| F-NP3-23 | `TestNV10NotificationBehaviour` asserts MP allocate/release emit **no** notification and is a live regression rail for the separate coverage scope. | §3.8, §10.4 |
| F-NP3-24 | PE work-item discoverability today is **100% pull** (mount-load + manual refresh); there is no polling and no Realtime subscription for work items, batches or assignments. | §5.2 |

---

## Appendix B — Exact read-only commands run in this fact-find

All commands are non-mutating reads. Outputs were written to `/tmp/*.txt` and read
back (the shell integration in this environment does not reliably capture `cat`
output).

```bash
# --- governing documents / task context ---
grep -n '^#\|^##\|^###' docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md
sed -n '1,40p' docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01-report.md
grep -n '## §2[0-9]\|### 22\|\bP-2\b' docs/architecture/CT-MP-SUB-004-PROD-READINESS-01-report.md
sed -n '155,170p;228,240p;275,295p' docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md
sed -n '246,290p' docs/architecture/CT-MP-SUB-004-PO-decision-record.md          # PD-5
grep -n -i 'notif' docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md
grep -rn -i 'notif' docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md
grep -rn 'PX-6\|PX-7' docs/architecture/*.md
sed -n '1,10p' docs/architecture/CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md
grep -n -i 'notif\|NV-10\|NV-9\|realtime' docs/architecture/CT-MP-SUB-004-independent-verification-report.md
sed -n '1,230p' tools/demo_lab/README.md

# --- notification schema / DDL ---
grep -n 'CREATE TABLE.*notification' CarbonTally_DB_Schema_V3M2.sql supabase/migrations/*.sql
sed -n '151,165p;1409,1443p;2022,2099p' supabase/migrations/00000000000000_init_schema.sql
sed -n '1,40p' supabase/migrations/20260902050000_phase5_notification_event_key.sql
grep -rn 'notifications\|notification_delivery\|notification_templates' supabase/migrations/*.sql | grep -i 'policy\|grant\|enable row'
grep -n 'POLICY' supabase/migrations/00000000000000_init_schema.sql
sed -n '88,145p' supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql
grep -rn 'preferences' CarbonTally_DB_Schema_V3M2.sql supabase/migrations/*.sql
grep -rn 'organization_settings' CarbonTally_DB_Schema_V3M2.sql supabase/migrations/*.sql
grep -rn 'feature_flags' CarbonTally_DB_Schema_V3M2.sql supabase/migrations/*.sql
grep -rn 'CREATE TABLE' --include='*.sql' . | grep -i 'pref\|_settings\|flag\|config\|policy'

# --- notification code ---
sed -n '1,313p' backend/data/notifications.py
sed -n '1,73p' backend/api/v3_notifications.py
grep -rn 'create_idempotent\|event_key' backend/ --include='*.py' | grep -v '.venv'
grep -rn 'notification_type' backend/ --include='*.py' | grep -v '.venv'
grep -rn 'repos.notifications\|NotificationsRepository' backend/ --include='*.py' | grep -v '.venv'
grep -rni 'notification_preference\|opt_out\|unsubscribe\|notify_on_' backend/data backend/api backend/services backend/domain frontend/src admin/src
sed -n '35,230p' backend/services/work_items.py
sed -n '1,215p' backend/services/consultant_lifecycle.py
sed -n '100,215p' backend/services/operational_alerting.py
sed -n '1780,1966p' backend/services/automatic_processing.py
sed -n '500,545p' backend/api/v3_messaging.py
grep -rn 'send_email\|resend\|email' backend/services/consultant_lifecycle.py backend/api/v3_backups.py backend/services/work_items.py backend/api/v3_messaging.py
grep -n 'def ' backend/utils/email.py
grep -n 'def require_admin' backend/auth.py
```

```bash
# --- configuration architecture ---
sed -n '1,145p' backend/data/settings.py
sed -n '300,370p' backend/api/v3_settings.py
grep -n '@router\|def ' backend/api/v3_settings.py
sed -n '1,160p;390,495p' admin/src/pages/admin/Settings.js
grep -rn 'NotificationSettings' frontend/src admin/src
sed -n '1,130p' frontend/src/components/NotificationSettings.jsx

# --- Realtime / frontend delivery ---
grep -rn 'channel(\|postgres_changes\|removeChannel' frontend/src admin/src
sed -n '290,345p' frontend/src/context/RealtimeContext.jsx
sed -n '1,152p' frontend/src/hooks/useNotifications.js
sed -n '1,222p' frontend/src/services/NotificationService.js
sed -n '1,90p' frontend/src/v3/pe/PeNotificationsBell.jsx
grep -rn 'setInterval\|useEffect\|refresh\|fetch(' frontend/src/v3/pe/PeWorkItemsPage.jsx frontend/src/v3/pe/PEDedicatedHome.jsx

# --- actor model / MP schema ---
grep -n 'CREATE TABLE public.manual_extraction_batches' -A 30 supabase/migrations/00000000000000_init_schema.sql
grep -n 'CREATE TABLE public.manual_extraction_items' -A 30 supabase/migrations/00000000000000_init_schema.sql
sed -n '780,860p;1922,1941p;1554,1580p' supabase/migrations/00000000000000_init_schema.sql
grep -n 'ALTER TABLE\|ADD COLUMN' supabase/migrations/20260910120000_p6_2d_consultant_provenance.sql
grep -n 'ALTER TABLE\|ADD COLUMN' supabase/migrations/20260905000000_gate4_actor_provenance.sql
sed -n '1,83p' supabase/migrations/20260902030000_phase5_work_item_assignments.sql
sed -n '45,80p' supabase/migrations/20260810000000_v3m1_processing_entities.sql
sed -n '1,130p' supabase/migrations/20261030000000_manual_processing_routing.sql
sed -n '1,125p' supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql
grep -rn 'uploaded_by' backend/ --include='*.py' | grep -v '.venv'
sed -n '400,445p' backend/data/manual_extraction.py
grep -rn 'def .*user_ids\|def .*staff\|entity_id' backend/data/staff.py backend/data/consultants.py

# --- MP notification behaviour ---
grep -rn 'notif' backend/services/manual_processing_routing.py backend/domain/manual_processing.py \
  backend/data/manual_processing.py backend/data/manual_extraction.py \
  backend/api/v3_manual_processing_coverage.py backend/api/manual_processing_admin.py
sed -n '300,420p' backend/services/manual_processing_routing.py
grep -rn 'auto_routed\|auto_route' backend/ --include='*.py' | grep -v '.venv'
sed -n '470,535p' backend/tests/unit/api/test_ct_mp_sub_004_prod_readiness.py
sed -n '1,90p' backend/tests/unit/api/test_v3_notifications.py
grep -rn 'pe/work\|/pe/\|pe_work' backend/api/*.py

# --- production-safety / git state ---
git --no-pager rev-parse HEAD
git --no-pager branch --show-current
git --no-pager status --porcelain | wc -l
git --no-pager diff --cached --name-only | wc -l
git --no-pager status --porcelain docs/architecture
git --no-pager log -1 --format='%H %s'
```

**Note on environment friction (disclosed for reproducibility):** the VS Code
terminal's shell integration in this session did not reliably report command
completion or capture `cat` output, and one stale command was echoed repeatedly.
Every command above was therefore written to an explicit `/tmp/*.txt` file and
read back with the file reader. **No command performed a write to the repository,
the database, or any remote system.**

---

*End of report body.*

*This document is a read-only fact-find. It creates no policy, changes no code,
and authorises no implementation. The Product Owner's next decision is the one
described in §9.*

NOTIFICATION POLICY FACT-FINDING COMPLETE — READY FOR PO DECISION

