# CarbonTally — P6-2E Preflight Report (D8 / D11)

**Prompt Ref:** `CT-CP1-CLOSE-P6-2E-PREFLIGHT-20260910-001`
**Response Ref:** `CT-CP1-CLOSE-P6-2E-PREFLIGHT-20260910-001-R1`
**Date/time:** 2026-09-10, 20:14 → 20:35 (+0600)
**Phase 6 · Gate:** P6-2E (D39 consultant conversation kind / D40 notification vocabulary)
**Mode:** read-only preflight · **implementation NOT AUTHORIZED**
**Final preflight verdict:** **P6-2E PREFLIGHT PASS — READY FOR IMPLEMENTATION CONTRACT / IMPLEMENTATION**

---

## 1. Authority chain

`Blueprint V1.3` (§9 processing model; §11 evidence/provenance) → `Master Roadmap V1.0` (§9: gate order `P6-2C → P6-2D → P6-2E → P6-2F`; P6-2E = D39/D8 + D40/D11; P6-2F = final UI/UX + E2E acceptance) → `P6-2 PO Decision Register` (`PO-PHASE6-D8-20260910` = **B** reuse the conversation model; `PO-PHASE6-D11-20260910` = **A** five lifecycle events; `PO-PHASE6-CAMPAIGN-20260910` hard checkpoints; frozen P6-2C invariants) → `Phase 6 Remainder Implementation Contract V1.0` (§7.1 D8 = preserve + verify, no code change; §7.2 D11 = five events, **no migration**, keys/recipient matrix derived in the implementation session; §15 security invariants; §19 STOP conditions) → repository.

Governing register text (L559–584): **D8** — "no dedicated consultant conversation kind is introduced unless later evidence demonstrates a concrete product/security requirement the existing model cannot satisfy; consultant participation continues through the existing authorisation/grant model; no unnecessary schema expansion; conversation authorisation must not be weakened". **D11** — five events with "deterministic/idempotent event keys; use the existing idempotent notification infrastructure; server-side recipient derivation; recipients determined from the actual workflow relationship; notifications must not leak data across organisations, firms or unauthorised actors"; the exact event constants/keys and the recipient matrix are "**not** defined here — the future implementation contract must derive them".

## 2. CP1 closure status
**CP1 — CLOSED.** P6-2D was independently verified (`PASS WITH NON-BLOCKING FINDINGS`), F1 accepted as out of P6-2D scope, no remediation required, P6-2D remains closed (see `docs/cline/CARBONTALLY_CP1_CLOSURE_REPORT.md`). The CP1 exit criteria for starting P6-2E are satisfied.

## 3. F1 decision
**ACCEPT AS OUT OF P6-2D SCOPE.** The seven consultant item-workflow actions are the P6-2D provenance scope; consultant-triggered automation `confirm`/`retry` are not added; P6-2D is not reopened; any future requirement for that provenance is a separately authorized change. (Detail: CP1 closure report §6–§8.)

## 4. P6-2E scope
**IN SCOPE — exactly two ratified workstreams:**
- **D8** — verify/reuse the existing conversation model for consultant participation; no dedicated consultant conversation kind (contract classification `1 Preserve + 2 Verify`; "must be changed: **NOTHING**").
- **D11** — implement the five consultant lifecycle notifications (accepted · submitted to QC · QC outcome · customer decision · rework) with deterministic idempotent server-side event keys, the existing idempotent notification infrastructure, and server-derived recipients from the actual workflow relationship.

**OUT OF SCOPE:** P6-2F UI/UX and its E2E/security acceptance; browser E2E campaign; final Phase-6 acceptance; Phase 7 Auditor/Assurance; Phase 8 Analytics; PE↔Consultant handoff; billing redesign; processing-origin redesign; P6-2D remediation; provenance expansion to `confirm`/`retry`; documentation/repository cleanup; new roles/capabilities/permissions without separate PO approval; RLS redesign; new conversation kinds.

## 5. D8 — current state (independently established)

| Element | Current state |
|---|---|
| Conversation model | `public.conversations` + `public.conversation_participants` + `public.messages`; repository `MessagingRepository` (`data/messaging.py`): create/get/list/participants/send/list/mark-read/close |
| Conversation kind | `conversation_kind` CHECK limited to **`'org'`** (default) and **`'entity'`** (PE operational messaging, migration `20260902040000`) — **no consultant kind** |
| Consultant participation | `api/v3_messaging.py` `_authorize_org_actor(...)` resolves the caller's participant role **`org_member` / `consultant`** (plus a staff participant role for authorised CarbonTally organisations) using the **active consultant grant** → consultant participation is already supported by the existing model |
| Authorisation posture | participant-scoped reads/writes; entity rows additionally filtered by `conversations_entity_select` (PE members only); org conversations remain under the existing organisation policy |
| Consultant-specific kind | **absent — and not required by the ratified D8 decision** |
| D8 gap | **none functional.** P6-2E's D8 obligation is *verification* (consultant participation via the reused model; conversation authorisation not weakened) plus regression coverage. |

## 6. D11 — current state (independently established)

| Element | Current state |
|---|---|
| Notifications store | `public.notifications` — `recipient_type`, `recipient_id`, `notification_type` (free-form `VARCHAR NOT NULL`, **no CHECK**), `title`, `message`, `priority`, `link`, `metadata JSONB`, `is_read`, `read_at`, `is_dismissed`, `created_at`, `updated_at` |
| Idempotency | `create_idempotent(user_id, event_key, …)` (`data/notifications.py:116`): `INSERT … ON CONFLICT (recipient_id, event_key) WHERE event_key IS NOT NULL DO NOTHING` + unique partial index `uq_notifications_event_key` (migration `20260902050000`); returns the existing row on conflict → **replay-safe**; `actor_domain` column also available |
| Event vocabulary in use | `work_item.assigned` (`services/work_items.py:58`) — the only existing `event_key` emitter; other `create(...)` callers are non-keyed (messaging notification, automatic-processing notification, discovery) |
| Recipient resolvers already available | `support_staff_user_ids()` (internal staff with `can_manage_staff`); `entity_participant_user_ids(...)` (PE participants); `consultants.list_firm_members(firm_id)`; `consultants.list_active_client_grants(organization_id)`; `organizations.get_members(org_id)` / `list_members_with_email(org_id)`; `organizations.get_active_memberships_for_user(user_id)` |
| Five lifecycle events | **NOT IMPLEMENTED** — no `event_key` emitter exists for accepted / submitted-to-QC / QC outcome / customer decision / rework |
| Trigger points (all already exist — no new workflow needed) | 1 **accepted** → `POST /api/v3/organizations/{org_id}/consultant-engagements/{engagement_id}/accept` (P6-1C; `pending → active`, customer owner/admin) · 2 **submitted to QC** → `POST /api/v3/processing/items/{id}/consultant-submit` (audit `consultant.submit:submitted`) · 3 **QC outcome** → CT-QC decision endpoint (`api/v3_operations.py:2039`; `ct_qc_approved` / `ct_qc_rejected`, audit `ct_qc:approved\|rejected`) · 4 **customer decision** → `POST /api/v3/processing/items/{id}/customer-review` · 5 **rework** → `ct_qc_rejected` and the consultant-review rework path (`consultant.review:rework` → `mapping`) |
| D11 gaps | event constants + emit sites; deterministic key formats; server-derived recipient derivation for the firm↔client relationship; focused idempotency/isolation tests |

## 7. Existing event infrastructure
`infra/event_bus.py` is an **in-process, fire-and-forget** `DomainEvent` pub/sub (handlers scheduled as background tasks; `drain()` / `publish_and_wait()` for tests and orderly shutdown). It is **not durable** and therefore **not** the correct mechanism for D11. The durable, replay-safe mechanism already exists as the notifications table + `create_idempotent` + the unique `(recipient_id, event_key)` index — exactly as the existing `work_item.assigned` emitter uses. **D11 should emit notifications at the trigger points (the `services/work_items.py` pattern), not through the bus.** No event-bus change is required.

## 8. Existing conversation infrastructure
`data/messaging.py` (`MessagingRepository`), `api/v3_messaging.py` (org + entity surfaces), `domain/messaging.py` (`Conversation`, `ConversationParticipant`, `Message`), the `conversation_kind` CHECK (`org`/`entity`), and the `conversations_entity_select` policy. Consultant participation already flows through the grant-based `_authorize_org_actor`. **No conversation change is required by D8.**

## 9. Existing notification infrastructure
`data/notifications.py`: `create_idempotent`, `create`, `get`, `mark_read` (recipient-scoped), `mark_all_read`, `support_staff_user_ids`, `entity_participant_user_ids`; notification read/mark endpoints are recipient-scoped server-side; `notification_type` is an unconstrained vocabulary column (so new lifecycle types need **no schema change**); indexes support `(recipient_id, created_at)`, `(recipient_type, recipient_id, is_read, created_at DESC)` and the unique idempotency index.

## 10. Existing idempotency infrastructure
Database-enforced: `uq_notifications_event_key` UNIQUE partial index on `(recipient_id, event_key) WHERE event_key IS NOT NULL`, consumed by `create_idempotent` via `ON CONFLICT … DO NOTHING` — the same mechanism the shipped `work_item:…` emitter relies on. It satisfies "deterministic, server-generated, idempotent, replay-safe" keys with **no new infrastructure**.

## 11. Schema / migration assessment
**No migration is required for P6-2E.**
- D11 needs no new columns: `event_key` + `actor_domain` already exist (migration `20260902050000`) and `notification_type` is free-form.
- D8 needs no new column and no CHECK change: `conversation_kind` already supports `org`/`entity` and consultants participate through the existing tables.
- If an implementation session nonetheless concludes a migration is required, it must be additive/nullable (contract §17) and it must **STOP and report** rather than improvise (contract §19 stop condition 3).
- If a migration were ever added, **no RLS change** would be required for notifications (§12).

## 12. RLS / security assessment

| Invariant P6-2E must preserve | Current posture / P6-2E obligation |
|---|---|
| Authentication | every messaging/notification surface requires an authenticated user (`require_auth`) — preserve |
| Organisation isolation | conversation participation and notification reads are caller-scoped — preserve |
| Consultant **firm** isolation | consultant access derives from the active grant (`_resolve_context` → single firm); recipient lists must derive from the *same* authoritative relationship — preserve, never widen |
| Active grants | only `status='active'` `consultant_clients` grants confer access — preserve |
| Canonical capability resolution | reuse `api/consultant_auth.py`; no parallel checks |
| **Server-side event creation** | creators must call `create_idempotent` server-side only; no client-supplied notification payloads |
| **Server-side recipient determination** | recipients resolved from repository relationships (firm members · client-org owner/admin · CT-QC/Ops staff) — **never** from request body/parameter/header |
| No client-controlled recipient | the D11 security core; requires explicit DENY tests |
| No cross-organisation / cross-firm leakage | a notification may reach only actors authorised for the underlying item/engagement; requires isolation tests |
| Idempotent creation / replay resistance | reuse `uq_notifications_event_key`; requires duplicate-suppression tests |
| Alternate-route protection | no non-lifecycle route may insert lifecycle notifications; no lifecycle route may emit before authorization |
| RLS | **unchanged** — no policy statement may appear in the P6-2E change set. `notifications` has no RLS policy today (API-only, recipient-scoped reads; no `ENABLE ROW LEVEL SECURITY` found); conversations keep their existing policies. Any perceived need to change RLS is a **STOP** condition |
| No new role/capability/permission | none may be added without separate PO approval (contract §19 stop condition 5) |

## 13. Test coverage assessment

| Area | Existing | Required for P6-2E (written at implementation time) |
|---|---|---|
| Notifications API | `backend/tests/unit/api/test_v3_notifications.py`; fakes support notifications | lifecycle-specific positive tests |
| Idempotency | infrastructure used indirectly; **no dedicated test** of `create_idempotent` duplicate suppression | **new**: same event emitted twice ⇒ exactly one row per recipient (`event_key` uniqueness) |
| Recipient determination | `work_item.assigned` emitter tests only | **new**: server-derived recipients per event; client-supplied recipient fields ignored |
| Isolation | messaging/organisation isolation tests exist | **new**: cross-org and cross-firm DENY (no receipt or triggering of another firm's/client's lifecycle events) |
| Denied-path behaviour | P6-2A/2B denial suites exist | **new**: a denied action (403/409) emits **no** notification |
| D8 regression | consultant messaging participation covered by existing suites | **new/verify**: consultant participation via grant; no consultant conversation kind; entity-kind guard unchanged |
| Event bus | `tests/unit/infra/test_event_bus.py` | unchanged |
| Regression | full unit suite (currently **1,627 collected**, all green) | re-run and re-measure the baseline at implementation time |

## 14. Implementation gaps (the actual P6-2E work)
1. **D11 — event constants + emit sites** at the five existing trigger points (accepted · submitted-to-QC · QC outcome · customer decision · rework), using deterministic server-generated `event_key` values and the existing `create_idempotent`.
2. **D11 — recipient derivation** from the authoritative relationships (firm members for consultant-relevant events; client-org owner/admin for client-relevant events; CT-QC/Ops staff for QC intake), with small additive repository helpers if existing resolvers are insufficient (e.g. a role-filtered org-member lookup) — **no** new identity model, role, capability or permission.
3. **D11 — focused tests** (idempotency · recipient derivation · isolation · no-emit-on-denial).
4. **D8 — verification + regression coverage only** (no production change expected).
5. **Evidence** per contract §18, followed by independent verification (the CP2 gate).

## 15. Unresolved decisions
- **No PO decision is required.** The register explicitly delegates the exact event constants/keys and the recipient matrix to the implementation, to be derived from the existing architecture and code (register L580–582); contract §7.2 records the same instruction. The relationships those recipients must come from are identified in §12/§14.
- **Implementation-session derivations (documented, not blockers):** the precise `event_key` string formats and `notification_type` values; the role filter for client-org recipients (owner/admin, matching the approval-authority invariants); and the rule that an event with no authorised recipient emits to **zero** recipients rather than widening the audience.
- **Escalation rule:** if any derivation would require a new role/capability/permission, an RLS change, a migration, or a change to authorization ordering, the implementation must **STOP** per contract §19 and report `BLOCKED — CLARIFICATION REQUIRED`.

## 16. Scope boundaries
P6-2E is limited to **D8 (verify/reuse)** and **D11 (five lifecycle notifications)**. It must not touch: P6-2F UI/UX or E2E acceptance; Phase 7/8; PE↔Consultant handoff; billing; processing-origin vocabulary; P6-2D artefacts; provenance for automation `confirm`/`retry`; RLS; the roadmap; documentation cleanup; or add roles/capabilities/permissions.

## 17. Recommendation
Proceed to an **implementation contract / implementation authorization** for P6-2E limited to D8 + D11, carrying these pre-agreed constraints into that authorization: reuse `create_idempotent` and the unique `(recipient_id, event_key)` index; emit directly at the five existing trigger points (not via the event bus); derive recipients server-side only; expect **no migration** and **no RLS change**; keep the D8 production change at zero (verification + tests only); re-measure the regression baseline (currently 1,627 collected) at the start of the implementation session; and treat any need for a migration, an RLS change or a new permission as a **STOP**.

## 18. Final preflight verdict

> **P6-2E PREFLIGHT PASS — READY FOR IMPLEMENTATION CONTRACT / IMPLEMENTATION**

Grounds: the authority chain agrees; CP1 is closed and P6-2D is frozen; D8 requires no production change (the reuse model and consultant participation already exist); D11's infrastructure (idempotent keys, recipient resolvers, free-form `notification_type`, all five trigger points) already exists with **no migration and no RLS change** required; the security invariants and test obligations are identified; and no unresolved blocking ambiguity or PO decision remains. **P6-2E has not started** — implementation requires separate authorization by the project owner.



