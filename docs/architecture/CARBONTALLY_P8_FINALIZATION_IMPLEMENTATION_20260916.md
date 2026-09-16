# CarbonTally — Phase 8 Finalization Implementation Record (P8-FINALIZATION-IMPLEMENT-001)

**Release tree:** `p8-release-reconciled` @ `2a34557` + this task's commits.
**Scope:** D-7 messaging, D-4 `emission_factors`, FIN-06 governance, FIN-05
retention, consultant-client parity audit, migration drift gate, D-11 storage
procedure, D-15/D-16/D-14 read-only readiness. **Production is untouched.**

---

## 1. D-7 / P8-FIN-02 — server-authoritative messaging

### Architecture (unchanged, extended)

The N1 server-side messaging API (`backend/api/v3_messaging.py`,
`/api/v3/messaging/*`) remains the single write path. This task adds the bounded
piece it was missing: **the caller can request a counterparty and the server
resolves it** — the browser never names or inserts a participant.

```
customer / consultant                server (service role)              database
  POST /api/v3/messaging/conversations
  {organization_id, subject,
   counterparty: "support"}  ─────►  _authorize_org_actor()
                                     create_conversation()  ─────────►  conversations INSERT
                                     add_participant(creator) ───────►  conversation_participants INSERT
                                     _resolve_support_participant() ─►  staff_profiles (internal + can_manage_staff)
                                     add_participant(support) ───────►  conversation_participants INSERT
                                     _audit_entity()  ───────────────►  audit_logs (append-only)
```

* `counterparty` accepts exactly `"support"` (pattern-validated; anything else is a
  422). Omitted ⇒ today's behaviour (creator only), so consultant↔client threads
  are unchanged.
* The support participant is resolved from the **existing authoritative source**
  (`repos.notifications.support_staff_user_ids()`: internal staff whose role grants
  `can_manage_staff`), deterministically (lowest user id). No staff directory is
  consulted and **no `users` peer read remains** in the chat components.
* Messages are written with the conversation's `organization_id`, satisfying the
  `messages_tenant_insert` policy; the retired group-flag column is never written.
* Audit: `msg:conversation_created` / `msg:message_sent` through the existing
  append-only audit repository (entity type `conversation`).

### Frontend

`ChatWidget` (start support conversation, conversation list) and `ChatWindow`
(send message) now call the API (`createMessagingConversation(..., 'support')`,
`sendMessagingMessage`). Direct browser INSERTs into `conversations`,
`conversation_participants` and `messages` are **removed**; the retired staff
picker is replaced by a "Contact support" action. RLS-permitted reads
(conversation/message/participant SELECT, read-marking UPDATE) are unchanged.

### Security / isolation

| Case | Result |
|---|---|
| Org member creates a support conversation | 201; participants = {caller, support} |
| Same caller, no authorised support staff configured | **409** (no fabricated participant) |
| Invalid/unknown counterparty value | **422** |
| Org B member creating/reading/sending to Org A | **403** (all three operations) |
| Consultant with an ENDED grant | **403** |
| Processing-entity staff | **403** (unchanged D18 boundary) |
| Browser-side participant INSERT | **not required and no longer present** |

---

## 2. D-4 — `emission_factors` is internal / server-side

**Migration:** `20260926000000_p8_d4_emission_factors_internal_containment.sql`
(REVOKE-only on one table; no policy, no RLS-flag, no data, no other table).

Measured in the disposable rehearsal clone (`ct_fin_impl_20260916`), with the
legacy grants deliberately injected first:

```
before:  anon 4 grants, authenticated 4 grants
apply D-4 (rc=0)
after:   anon 0, authenticated 0     ← migration NOTICE captured
```

Post-apply posture: `anon=false`, `authenticated=false` for the table;
`relrowsecurity=true` and policy count `0` unchanged; the backend's SQL path
connects as the table **owner**, so factor matching, import, calculation,
reporting and the admin factor surface are unaffected.

**Observation (pre-existing, not a regression):** in the rehearsal clone
`service_role` held **no** privilege on `emission_factors` before *and* after this
migration (the clone's default ACL never granted it). The migration contains no
statement naming `service_role`. Production's posture must be measured in D-15.

---

## 3. FIN-05 — beta / waitlist retained (non-destructive)

Verified posture (canonical local DB): `beta_users`, `beta_access_codes`,
`waitlist` — **RLS enabled, 0 policies** (fail-closed for client roles); 0 rows
locally. Routes remain registered (`/beta/signup`, `/beta-login`,
`/admin/beta-management`) and RLS-4B explicitly excludes these tables. **Nothing
was deleted, migrated or modified.** Retention/retirement policy remains future
product work (report §Q.3).

---

## 4. Consultant-client parity audit

### Audited surfaces

| Surface | Organisation workspace | Consultant-client workspace | Classification |
|---|---|---|---|
| Documents (list/upload) | `/api/v3/documents/*` | `/api/v3/consultants/clients/{id}/documents` | parity (different route family) |
| Processing items / queue | `/api/v3/processing/*` | `/api/v3/consultants/clients/{id}/processing/items` | parity |
| Evidence / audit package | `/api/v3/evidence`, exports | `/api/v3/consultants/clients/{id}/evidence` | parity |
| Dashboard / context | org-scoped | `/api/v3/consultants/clients/{id}/dashboard`, `/context` | parity |
| Messaging | `/api/v3/messaging/*` | same (active-grant consultant) | parity (extended by this task) |
| Manual processing | `/api/v3/manual-extraction/*` | governed by FIN-06 for both | parity (governed) |
| **Reports (Phase 8 lifecycle)** | `/api/v3/reports/*` | **no consultant path** (`require_org_member` + `ensure_org_access`, staff-only bypass) | **GAP** |
| **Disclosure / frozen artefact** | `/api/v3/disclosure/*` | **no consultant path** | **GAP** |
| Approval / finalisation | Owner/Admin only | excluded by **ratified B4-D1** | intentional |
| Master data, settings, billing | org surfaces | not exposed | intentional |

### Outcome (stop-and-report, per the task's stop conditions)

The genuine parity gaps are the **Phase 8 reporting and disclosure surfaces**.
They were **not** implemented, because closing them conflicts with a ratified PO
decision and changes the authorization model of the whole Phase 8 report surface:

* **B4-D1 (ratified):** "Owner **and** Admin may approve/finalise; consultants and
  internal staff may **never**" — approval/finalisation parity is excluded *by
  decision*;
* the disclosure/exposure semantics were ratified separately (D1–D17 reporting
  ratification);
* access would have to be granted through the shared org-boundary helper used by
  every report/disclosure endpoint — a security-relevant change that needs its own
  scoped PO decision, independent verification and a negative-test matrix.

**No parity change was implemented.** The gap register above is the deliverable; a
bounded follow-up (PO decision → implementation → independent verification) is
recommended (report §Q.5).

---

## 5. Production readiness (read-only; no production contact)

| Gate | State |
|---|---|
| **D-15** (production ACL/ledger census) | **NOT PERFORMED** — no authorised read-only production access exists in this environment; the only reachable credentials are local/dev and `.env.production` was deliberately **not** used. Production was never connected to. Exact query set + masking rules: reconnaissance report §12. |
| **D-16** (backup/PITR + restore rehearsal) | **NOT VERIFIED** — provider access is a PO/ops action. Application backup code remains independently verified (N1 PASS). A genuine provider-level restore rehearsal cannot be performed from this environment. |
| **D-14** (migration window plan) | Delta recalculated from the release tree: **71 repository migrations**; production baseline **21 (recorded, unverified)** ⇒ up to **50 pending** until D-15 measures the real ledger. Ordered list + risk markers: reconnaissance report §14. The disposable rehearsal (§6) validates the newest three files end-to-end. |
| **D-17** (production migration authorisation) | **NOT AUTHORISED, NOT EXECUTED.** Terminal PO gate. |

## 6. Disposable migration rehearsal (evidence)

Environment: `ct_fin_impl_20260916` (clone of `ct_p8_rehearsal_20260915`; never
production, never the investor demo, never persistent QA).

| Step | Result |
|---|---|
| `20260925000000_p8_rls_4b_group1_enablement` | rc=0 (50/50 approved tables; no policy/grant/storage change) |
| `20260926000000_p8_d4_…containment` | rc=0, then **rc=0 again (idempotent)**; anon 4→0, authenticated 4→0 (grants injected first to prove the revoke) |
| `20260927000000_p8_fin06_…governance` | rc=0, **rc=0 again (idempotent)**; `rls=true policies=0 anon=false auth=false`, `enabled_rows=0`, constraints = `pkey`, `scope_key`, `scope_type_check` |

**Rehearsal defect found and fixed:** the first FIN-06 draft failed to apply
(`COMMENT ON` cannot use adjacent string literals, and a truncated `CREATE TABLE`
left the statement unterminated). Only the rehearsal surfaced it; the migration was
corrected and re-verified (rc=0 ×2).

```
# drift gate against the rehearsed clone
migration-drift: repository=71 ledger=71 pending=0 unexpected=0 anomalies=0 drift=False

# drift gate against the local canonical DB (46 applied)
migration-drift: repository=71 ledger=46 pending=29 unexpected=4 anomalies=0 drift=True → RELEASE BLOCKED
```

The `unexpected=4` entries are ledger versions with no repository file in that
database — exactly the class of drift the gate exists to expose.

## 7. D-11 — `report-artifacts` (operational provisioning)

Procedure: `docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md`. The bucket is
**not** created by any migration (PO decision). Application preflight added:
`SupabaseReportArtefactStorage.bucket_exists()` (read-only; `False` on absence or
provider error). **The bucket was not created in any environment** — no provider
credentials were used; the remaining operator action is documented.

## 8. Migration drift gate (WP-8)

`backend/tools/migration_drift.py` + `.github/workflows/migration-drift.yml` +
`docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md`. Detects pending migrations,
unexpected ledger entries, ordering anomalies, duplicate versions, duplicate ledger
rows and naming anomalies; hard-fails the release (exit 1); supports a recorded,
time-boxed emergency override; refuses production-looking DSNs; writes JSON +
Markdown evidence.
