# CarbonTally Phase 5 — WS3 / D40 Implementation Report

- **Status:** WS3 — D40 IMPLEMENTATION COMPLETE AND VERIFIED.
- **Scope:** D40 notification event producers + PE notification entry point.
  No WS4, WS5, or Phase-6 work performed.
- **Date:** 2 September 2026
- **Baseline (pre-migration):** factors 7,049; migrations 44; orgs 975;
  items 260; batches 56; conversations 34; messages 52; participants 62;
  notifications 0; ledger 0.

## 1. WS3 status
IMPLEMENTED and VERIFIED: positive/negative/idempotency/recipient-isolation/
audit/regression/UI gates all green; fixtures removed; data integrity
confirmed.

## 2. Existing notification architecture (CURRENT FACT)
- Recipient-scoped `notifications` (recipient_type='user', recipient_id uuid)
  with list/read/read-all API (`/api/v3/notifications`) — recipient identity
  is always the authenticated user (never client-supplied). Repository:
  `data/notifications.py` (NotificationsRepository in the RepositoryBundle).
- No existing event producers for work-item/messaging events; no idempotency
  key; no RLS policies (reads are API-scoped through the pool); frontend
  bell exists on shared shells only.

## 3. D40 implementation
Additive completion of the existing capability:
- Deterministic event-key idempotency for producers.
- D38 → D40 producers (internal assignment/reassign/recover target notify).
- D39 → D40 producers (PE message → authorised Operations; Operations reply →
  PE participants).
- PE notification entry point (bell) inside the dedicated PEShell.

## 4. Event producer architecture
Producers live inside the canonical action paths (services/work_items.py and
v3_messaging.py send_entity_message) and are best-effort side effects after
the business action + immutable audit have committed: a notification failure
is logged (detectable) and can never roll back or alter the business action.
Recipients are always resolved server-side from the event.

## 5. D38 integration
`work_item:assign`, `:reassign`, `:recover` on internal items notify the new
assignee (target ≠ actor) with `notification_type='work_item.assigned'`,
event_key `work_item:<action>:<item>:<ledger row id>`, link `/ops/items/{id}`.
Self-claims produce no notification. Duplicate assign-to-same-assignee
produces no second notification.

## 6. D39 integration
PE operational message → all authorised CarbonTally Operations support staff
(active internal staff whose role grants `can_manage_staff`; bounded fan-out).
Operations reply → PE staff participants of that conversation (own entity
only, sender excluded). Types `pe_msg.message` / `pe_msg.ops_reply`; event key
`pe_msg:<message id>:<recipient>`. No broadcast; no customer/consultant/
other-PE recipients.

## 7. Recipient resolution
100% server-side from the event and authorized relationships (ledger
assignee; support-role catalog; entity conversation participants). No client
can supply recipient_id/type, organization_id, processing_entity_id,
conversation_id or work_item_id for notification targeting; there is no
client notification-creation endpoint (verified 405).

## 8. Idempotency
Migration adds `notifications.event_key` + unique partial index
`(recipient_id, event_key) WHERE event_key IS NOT NULL`;
`create_idempotent(...)` uses `ON CONFLICT ... DO NOTHING` with existing-row
fallback. Retried producers can never create duplicate notifications
(verified: zero duplicate (recipient,event_key) rows after events).

## 9. Transactional consistency
No outbox exists in the platform; the smallest safe architecture is used:
notification creation is a post-commit best-effort side effect within the
same request lifecycle, logged on failure (no silent loss, no business
rollback coupling). Trade-off documented as a KNOWN LIMITATION (§29).

## 10. API changes
None to the notification contract (list/read/read-all unchanged and
recipient-scoped). Producers were added inside existing D38/D39 endpoints —
no new public notification surface.

## 11. Database changes
Migration 45: additive `notifications.event_key`, `notifications.actor_domain`
and inbox index. No existing rows changed (notifications were 0); no data
touched.

## 12. RLS
Notifications remain API-scoped to the authenticated recipient (no table
grant path introduced); producers run through the backend pool. No RLS
weakened, no service-role bypass added, no client recipient spoofing possible
(verified forged mark-read → 404).

## 13. Realtime
Notifications are read through the API; Realtime delivery is not used by the
frontend notification surface, so no Realtime channel was introduced. The
existing notification architecture is unchanged. Realtime isolation for D39
conversation events remains enforced by the WS2 RLS policies (unchanged).

## 14. PE notification surface
Minimal bell added to the dedicated PEShell (`PeNotificationsBell.jsx`):
unread badge, list (20 newest), mark-read, mark-all-read, target navigation.
Bell links point at surfaces whose APIs independently re-authorize; the bell
is not an access mechanism. No shared-shell/navigation changes.

## 15. Audit
Business events remain audited by the originating D38/D39 audit paths
(verified work_item + pe_msg audit events present). Notification rows carry
actor_domain/event_key metadata; no new audit spam introduced.

## 16. Performance
Unread count uses a bounded unread query; list limited to 20 with server-side
pagination API (limit 1..500); fan-out bounded to support staff / conversation
PE participants; inbox index `(recipient_type, recipient_id, is_read,
created_at DESC)` added. No unbounded queries.

## 17. Positive tests
T1 internal assign → assignee notification; T2 duplicate assign → no dup;
T3 self-claim → no self notification; T4 entity conversation; T5 PE message;
T6/T7 both Ops support staff notified of PE message; T8 ops reply; T9 PE
participant notified; T10 mark-read reduces unread; T11 read-all; T12 zero
duplicate (recipient,event_key); T13 work_item + pe_msg audits present.
ALL PASS.

## 18. Negative security matrix
N1 operator receives no pe_msg; N2 reviewer receives only work_item types;
N3 PE-B gets nothing; N4 customer nothing; N5 consultant nothing; N6 forged
mark-read of another user's notification → 404; N7 no client notification
creation endpoint → 405. ALL PASS.

## 19. Cross-domain tests
PE A events never reach PE B, customer, consultant, or unprivileged internal
users (N1–N5); D39/D38 authorization unchanged (regression R1/R2).

## 20. D38 regression
PE claim + complete (200/200); assignment/notification behavior verified
T1–T3; ledger and immutable provenance untouched.

## 21. D39 regression
PE list + conversation read (200/200); conversation authorization unchanged;
WS2 RLS intact.

## 22. V1.2 regression
Unit subset (23 tests) green; PE roles/QC/CT QC/customer approval unchanged;
immutable processing-origin model untouched.

## 23. Responsive verification
PEShell notification bell verified at 1920/1440/1280/1024/768/390 at 100%
zoom: bell + unread badge present, panel opens, zero horizontal overflow,
panel fully inside the viewport at every width (fixed-position panel). ALL
PASS. Screenshots: /tmp/ws3_bell_1440.png, /tmp/ws3_bell_390.png.

## 24. Data-integrity verification (post-teardown)
factors=7,049; migrations=45; orgs=975; items=260; batches=56;
conversations=34; messages=52; participants=62; notifications=0; ledger=0.

## 25. Fixture lifecycle
Isolated fixture org/items + entity conversation only; all notifications,
conversations, ledger rows and WS3 audit rows removed at teardown; demo data
untouched.

## 26. Files created
- supabase/migrations/20260902050000_phase5_notification_event_key.sql
- frontend/src/v3/pe/PeNotificationsBell.jsx
- docs/architecture/CARBONTALLY_PHASE5_WS3_D40_IMPLEMENTATION_REPORT.md

## 27. Files modified
- backend/data/notifications.py (idempotent create, recipient-resolution
  helpers)
- backend/services/work_items.py (D38 → D40 producer)
- backend/api/v3_messaging.py (D39 → D40 producers)
- frontend/src/v3/pe/PEShell.jsx (bell mount)
- frontend/src/v3/pe/pe.css (bell styles)

## 28. Files deleted
None.

## 29. Known limitations
- Producer delivery is best-effort post-commit (logged on failure); no outbox
  pattern exists in the platform and none was introduced.
- Notifications are API-read; Realtime notification push was not added (not
  previously present) — Realtime isolation for conversation events remains
  enforced by the WS2 RLS layer.
- Notification text is deliberately generic (no work/item identifiers beyond
  a safe link) to avoid exposing operational context in the list payload.

## 30. Deferred WS4 work
Full PEShell/Ops notification + messaging UI polish and end-to-end browser
workflow integration — not part of WS3.

## 31. WS3 acceptance checklist
All items checked: existing notification architecture preserved; D38 event
producers (assign/reassign/recover) implemented; D39 message producers
implemented; recipient resolution server-side; recipient spoofing denied
(no creation endpoint); reads recipient-scoped; PE A/B, PE/customer,
PE/consultant, unauthorized-internal isolation verified; notification targets
independently authorize (D38/D39 APIs unchanged); idempotency + retry verified
(event-key unique index); RLS/API scoping verified; Realtime isolation
unchanged-and-secure; D38/D39/V1.2 regressions passed; PE entry point
implemented in the dedicated PEShell; six-width responsive verification
passed; fixtures removed; 7,049 factors preserved; migration integrity
verified (44→45); no investor/demo data mutated; no personal workspace; no
billing changes; no V1.2 changes.

IMPLEMENTED / VERIFIED — see §1. DEFERRED — full WS4 integration and Realtime
notification push. No commits/pushes; working tree left for PO review.
