# PE Operational Messaging — PO Decision Required (Phase B)

Status: **PO DECISION REQUIRED — no implementation made.**

Prepared by: Cline (implementation agent), Phase B close-out, 2026-08-31.
Source of truth verified: `backend/api/v3_messaging.py`, `frontend/src/v3/ops/OpsMessagingTab.jsx`,
`frontend/src/v3/consultant/ClientMessagingTab.jsx`, `supabase/migrations/00000000000000_init_schema.sql`
(`public.conversations`), live demo database.

## 1. What messaging currently supports

- Conversations are **organisation-scoped**: `public.conversations.organization_id` is the only
  participant-scope key (there are also legacy `staff_id`/`customer_id` columns; no entity column).
- Participants (server-authorised by `_authorize_org_actor` in `v3_messaging.py`):
  1. **Org members** of the conversation's organisation (customer workspace),
  2. **Consultants** holding an ACTIVE `consultant_clients` grant for the organisation,
  3. **Internal CarbonTally staff** with `entity_id IS NULL` **and** the `can_manage_staff`
     permission ("CarbonTally Support / Authorised Admin").
- Delivery: API persists through the service role; the frontend subscribes via Supabase Realtime
  (`useConversationRealtime`), with the API refetch as the deterministic fallback.

## 2. What PE staff / PE managers can access today

- **Nothing on the messaging surface.** PE staff and PE managers are denied `403` on every
  org-scoped messaging route. This is the **ratified D18/N1 boundary** (AGENTS.md §28): there is
  *no unrestricted Customer ↔ PE communication*, and general employees / entity staff never get
  messaging access.

## 3. What customer / consultant messaging supports

- Customer ↔ consultant (active grant) ↔ internal support-admin threads per organisation, in the
  customer workspace (`/messaging` area) and the consultant `Client messages` tab.

## 4. Whether conversations have an entity/processing-entity context

- **No.** There is no `entity_id` / `processing_entity_id` on `conversations`, no entity-scoped
  participant model, and no RLS story for entity conversations. PE staff cannot even see a
  conversation list.

## 5. Minimum product behaviour required for PE operational messaging (if approved)

N1 (AGENTS.md §28) defines PE messaging as **"operational CarbonTally messaging"** — i.e. PE users
communicate with CarbonTally, not with customers/consultants. A compliant minimal design would be:

1. **New conversation scope** — an entity-scoped thread model (e.g. an optional
   `processing_entity_id` on conversations, or a separate entity-messaging table) so PE work is
   not mixed into customer org threads.
2. **Authorisation** — PE staff/managers of **their own** entity may read/write entity threads;
   internal CarbonTally staff (internal, non-entity) may participate; customers, consultants and
   other PEs remain denied (no Customer ↔ PE, no PE A ↔ PE B).
3. **RLS** — new policies for entity-scoped conversations + participants; the existing org-scoped
   messaging RLS stays untouched.
4. **Frontend** — an entity-messaging surface in the PE workspace (`/ops` entity landing) alongside
   the existing ops/staff support tab.
5. **Realtime** — reuse the existing conversation realtime hook scoped to entity conversations.

## 6. Decision required (PO)

- **Do we authorise entity-scoped PE ↔ internal-CarbonTally operational messaging?**
  - If **approved**: implement the entity conversation model + RLS + PE workspace surface
    (a schema/RLS/product-model change — separate task after this decision).
  - If **not approved / deferred**: keep the current D18 boundary (PE denied 403 on messaging),
    which is correct and already enforced server-side.

No speculative implementation was made in Phase B.
