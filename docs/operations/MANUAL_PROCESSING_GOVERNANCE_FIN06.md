# Manual Processing Governance — FIN-06 (CarbonTally Admin control plane)

**Status:** implemented (P8-FINALIZATION-IMPLEMENT-001). Server-enforced.
**Owner of the policy:** CarbonTally Admin (internal staff).
**Default:** **DISABLED** — absence of a governance row means manual processing is
denied for that scope (fail closed).

## 1. What "Manual Processing" means here

Manual processing is the human-performed path:

* manual-extraction **batches** and **items** (`/api/v3/manual-extraction/*`);
* the manual **stage actions** on the processing workflow (`extract`, `map`,
  `validate`, `calculate`, `consultant-submit`) for work that is not
  machine-produced (the fail-closed `item_is_automatic` predicate decides).

Automatic processing (the durable worker queue) is **not** governed by FIN-06.

## 2. Control plane

| Surface | Purpose |
|---|---|
| `GET /api/v3/admin/manual-processing/grants` | list explicit governance rows + precedence + default |
| `PUT /api/v3/admin/manual-processing/grants` | enable/disable exactly one scope |
| `DELETE /api/v3/admin/manual-processing/grants/{scope_type}/{scope_id}` | remove a row (falls back to inheritance/default deny) |
| `GET /api/v3/admin/manual-processing/effective/{organization_id}` | diagnostic: effective value + the scope level that decided it |

**Authorization:** internal CarbonTally staff (`staff_profiles.entity_id IS NULL`)
holding the existing admin-grade permission `can_manage_organizations`. Nothing in
the customer/consultant surface can call these endpoints, and the underlying table
has RLS enabled with **zero policies** and both client roles revoked.

## 3. Scope vocabulary and precedence

| scope_type | scope_id is |
|---|---|
| `organization` | `organizations.id` |
| `consultant_firm` | `consultant_profiles.id` (the firm) |
| `consultant_client` | `consultant_clients.id` (the firm↔organisation grant) |

Precedence — **most specific wins**:

```text
consultant_client  >  consultant_firm  >  organization  >  platform default
```

The first matching scope with an explicit row decides; an explicit `enabled=false`
on a specific scope beats a broader `enabled=true`. Selected clients are expressed
as one row per `consultant_client`; "all clients of a firm" is a single
`consultant_firm` row.

## 4. Job lifecycle behaviour

| Situation | Behaviour |
|---|---|
| New batch/item (any governed actor) | blocked with 403 when the effective value is false |
| QUEUED manual batches (`status='open'`) when a scope is disabled | **cancelled/invalidated** (the existing batch `cancelled` existence/state is reused) |
| Actively running batches (`status='in_progress'`) | **left to finish** — never terminated destructively |
| Re-enabling | new work is permitted; previously cancelled/failed/completed work is **never resurrected** |
| Queued work on re-enable | remains cancelled; the operator creates new work deliberately |

## 5. Actors

| Actor | Governed? |
|---|---|
| Organisation Owner/Admin/Member | **Yes** — needs an effective allow |
| Consultant user / consultant admin | **Yes** — needs an effective allow (client or firm scope) |
| Consultant-client user | **Yes** — same resolution |
| CarbonTally internal staff (platform operator) | **No** — keeps its existing staff-permission gating (`can_process`/`can_extract`); blocking the platform's own processing would break operations |
| Processing-entity staff | **No access to this pipeline at all** (pre-existing D18/entity boundary) |

> The platform-operator rule is an interpretation of the PO decision recorded for
> confirmation in the FIN-06 section of the implementation report.

## 6. Auditability

Every governance mutation is written through the **existing** append-only audit
infrastructure (`repos.audit.record` → `public.audit_logs`), entity type
`manual_processing_grant`, recording: actor, timestamp, scope type/id, previous
value + its level, new value, reason, cancelled batch ids, and the request
identifier (`x-request-id`/`x-correlation-id` when supplied).

Actions: `manual_processing:grant_set`, `manual_processing:grant_removed`,
`manual_processing:queued_batches_cancelled`.

## 7. Migration

`supabase/migrations/20260927000000_p8_fin06_manual_processing_governance.sql`
creates exactly one table (`public.manual_processing_grants`) with a uniqueness
constraint, the scope vocabulary CHECK, RLS enabled + zero policies, and both
client roles revoked. Applied twice in the disposable rehearsal clone (`rc=0`
both passes).

## 8. Open PO confirmations

See the implementation report §G: the definition boundary of "Manual Processing",
enablement authority (permission vs dedicated role), whether a narrow scope may
deny a broader grant (implemented: yes), re-enable semantics for queued work, and
the platform-operator exemption.
