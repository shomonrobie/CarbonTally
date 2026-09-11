# CarbonTally Phase 5 — WS2 / D39 Implementation Report

- **Status:** WS2 — D39 IMPLEMENTATION COMPLETE AND VERIFIED.
- **Scope:** PE ↔ CarbonTally Operations operational messaging (PE-MSG-001)
  only. No D40, WS4 UI, or Phase-6 work performed.
- **Date:** 2 September 2026
- **Baseline (pre-migration):** factors 7,049; migrations 43; orgs 975;
  items 260; batches 56; conversations 34; messages 52; participants 62;
  notifications 0.

## 1. WS2 status
IMPLEMENTED and VERIFIED: positive/negative/context/IDOR/RLS-matrix/audit/
D38-regression gates all green; fixtures torn down; data integrity confirmed.

## 2. D39 objective
Controlled, entity-scoped, server-authorized operational messaging between
Processing Entity staff and authorised CarbonTally Operations actors — without
customer/consultant/other-PE exposure and without expanding data permissions.

## 3. Existing messaging architecture (CURRENT FACT)
- Org-scoped `conversations` (organization_id NOT NULL) + `messages` +
  `conversation_participants`; API in `v3_messaging.py` (`_authorize_org_actor`:
  org members, consultants with ACTIVE client grant, internal support staff
  with `can_manage_staff`). PE structurally denied (403).
- RLS: org-scoped SELECT policies via `is_org_member` / `is_org_consultant`
  (NULL org can never match); UPDATE/DELETE org policies; participants via
  `can_view_conversation_participants`/`is_conversation_participant`.
- Backend persists through the asyncpg pool (RLS = defence-in-depth +
  Realtime isolation); UI reads via API.

## 4. Final conversation scope model
Approved **Option B**: the existing conversation family is extended. Every
conversation now has an explicit discriminator:
- `conversation_kind = 'org'` → organisation-scoped (unchanged, default;
  existing 34 rows migrated to `org`, organisation NOT NULL).
- `conversation_kind = 'entity'` → PE operational conversation with
  `processing_entity_id` (NOT NULL) and `organization_id = NULL`, plus
  optional `context` jsonb (`{type:'batch'|'item', id}`) for work context.
A table CHECK guarantees exactly one scope per conversation.

## 5. Database changes
Additive columns: `conversations.conversation_kind`, `.processing_entity_id`,
`.context`; `conversations.organization_id` and `messages.organization_id`
dropped to nullable (org NOT NULL enforced by the CHECK for `org` kind);
indexes on entity scope and kind. No existing row changed (kind backfilled
`org`); no conversation/message deleted.

## 6. Migration details
`supabase/migrations/20260902040000_phase5_pe_operational_messaging.sql` —
idempotent, additive, RLS-aware. Migration count 43 → **44**. Applied and
verified (existing conversations 34 / messages 52 / participants 62 intact).

## 7. RLS architecture
New SECURITY DEFINER helpers: `is_active_pe_member(entity)` (active staff of
an ACTIVE entity via `auth.uid()`), `is_ops_messaging_staff()` (internal staff
`entity_id IS NULL` whose role grants `can_manage_staff`),
`can_view_entity_conversation(id)` (kind=entity AND owner-entity PE staff OR
ops support). New SELECT policies on conversations/messages/participants for
entity rows. Organisation policies untouched and structurally incapable of
matching NULL-org rows (both helper predicates require an organisation id).

## 8. API architecture
Extended the canonical V3 messaging API (`/api/v3/messaging`):
- `GET /entity-conversations` (PE = own entity; Ops = optional entity filter)
- `POST /entity-conversations` (PE = own ACTIVE entity; Ops = validated entity)
- `GET/POST /entity-conversations/{id}/messages`
- `POST /entity-conversations/{id}/read`
Same repository/service as org messaging; no parallel messaging stack.

## 9. Participant authorization
Server-derived only: PE members of the owning entity; internal CarbonTally
support (entity NULL + `can_manage_staff`). Client-supplied entity/participant
ids are never trusted for PE callers. Participant rows are recorded for
read-state; participants do not define authorization.

## 10. PE isolation
Verified: PE A cannot list/read/send to PE B conversations (403); PE-B list
excludes PE-A threads; PE cannot read customer org conversations (403).

## 11. Operations authorization
Only internal staff with `can_manage_staff` (role catalog, not client claim)
may act as Ops in entity conversations. Internal operator/reviewer without
that permission are denied (403).

## 12. Work/batch/issue context
Optional `context` on entity conversations. Context of type `batch`/`item` is
validated server-side against the entity assignment
(`manual_extraction_batches.entity_id`). Verified: an internal-origin item
referenced as context on an Alpha conversation is denied (403). Context can
never expand the caller's underlying work permissions.

## 13. Realtime security
Realtime uses RLS SELECT policies on the conversation family. The new
entity-scope policies provide isolation at the database layer (verified via
authenticated-role simulation, §20); org policies unchanged. No frontend
filtering is used as authorization.

## 14. Audit implementation
Entity conversation creation and message sends write immutable `audit_trail`
events (`table_name='conversation'`, `action_type='pe_msg:conversation_created'`
/ `pe_msg:message_sent`, actor + processing entity in metadata). Verified 5
events for the fixture run.

## 15. Performance / index analysis
Entity list bounded (LIMIT 200), message list bounded (200), participant
lookups per listed conversation (same as existing org listing). New indexes:
`ix_conversations_entity(processing_entity_id, kind)`,
`ix_conversations_kind(kind, created_at DESC)`. No unbounded queries added.

## 16. Existing messaging compatibility
Org-scoped customer ↔ consultant ↔ support messaging regression verified:
customer created an org conversation and read it (200); PE denied on the org
conversation (403); all pre-existing conversations/messages/participants
preserved (counts unchanged after fixture teardown).

## 17. D38 regression
PE claim + complete on an own-entity item still works (200/200) after WS2;
ledger/attribution logic untouched; WS2 fixtures removed (ledger 0).

## 18. Positive tests
P1–P10 all PASS (PE create with work context; PE send; Ops list + reply; PE
reads thread; PE mark-read; PE-B own-entity create; PE-A list excludes PE-B;
customer org conversation still functions).

## 19. Negative security matrix
All PASS: PE-A→PE-B read; PE-B→PE-A read; customer list/read; consultant list;
operator list (no support perm); reviewer list; forged conversation id (404);
PE→customer org conversation (403); forged entity on Ops create (422);
internal-origin item as Alpha work context (403).

## 20. NULL-organization RLS security tests (mandatory gate)
Authenticated-role simulation (real `auth.uid()` claims): PE-A entity
conversation visible to owner-entity PE staff (1) and Ops support (1);
invisible to PE-B (0), internal operator (0), internal reviewer (0), customer
owner (0), consultant (0). Org conversation visible only to the customer
owner (1); PE staff (0) and Ops support (0). Organisation policies do not
match NULL-org entity rows.

## 21. IDOR tests
All PASS: known conversation id of another PE → 403; forged conversation id →
404; customer/consultant direct API attempts → 403.

## 22. Fixture lifecycle
Isolated fixtures only (fixture org + items + entity/org conversations on demo
PEs/customer). All fixture conversations/messages/participants and WS2 audit
rows deleted; fixture org/items/batches torn down; final counts verified.

## 23. Data-integrity verification (post-teardown)
factors=7,049; migrations=44; orgs=975; items=260; batches=56;
conversations=34; messages=52; participants=62; notifications=0; ledger=0.

## 24. Files created
- supabase/migrations/20260902040000_phase5_pe_operational_messaging.sql
- docs/architecture/CARBONTALLY_PHASE5_WS2_D39_IMPLEMENTATION_REPORT.md

## 25. Files modified
- backend/data/messaging.py (entity conversation repository methods, optional
  message organisation scope)
- backend/api/v3_messaging.py (entity messaging endpoints + auth)

## 26. Files deleted
None.

## 27. Known limitations
- Issue-type work context is not yet offered (only batch/item), so an issue
  reference cannot be attached to a conversation thread yet.
- Realtime was verified at the RLS/authorization layer (deterministic DB
  matrix); a live end-to-end browser push test is deferred to WS4 UI
  integration.
- Work context is validated against `batches.entity_id`; conversations do not
  carry a mutable work pointer beyond the stored context.

## 28. Deferred UI work
PEShell/Ops messaging UI (WS4) — not part of WS2.

## 29. WS2 acceptance checklist
All items checked: Option B used; entity scope + kind implemented safely;
nullable-org cannot bypass RLS (verified); PE participant authorization;
Operations authorization; PE A↔PE B denied; PE↔customer denied; PE↔consultant
denied; unauthorized internal denied; forged IDs and IDOR denied; work-context
authorization verified; customer + consultant messaging works; existing
conversations/messages preserved; Realtime isolation verified (RLS); audit
verified; D38 regression passed; V1.2 regression passed (23 tests); isolated
fixtures removed; 7,049 factors preserved; migration integrity verified
(43→44); no investor/demo data mutated; no personal workspace; no billing
changes; no V1.2 changes.

IMPLEMENTED / VERIFIED — see §1. DEFERRED — WS4 UI + Realtime end-to-end push
test. No commits/pushes; working tree left for Product Owner review.
