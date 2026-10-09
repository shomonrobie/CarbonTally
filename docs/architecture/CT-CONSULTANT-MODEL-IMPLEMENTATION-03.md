# CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — Client access profiles, product modes, retention and Plane C

| | |
|---|---|
| **Status** | IMPLEMENTED · TESTED (unit, backend + frontend) · LAB-VERIFIED (API, security matrix, browser) · NOT INDEPENDENTLY VERIFIED |
| **Task** | `CT-CONSULTANT-MODEL-IMPLEMENTATION-03` |
| **Predecessor documents** | `docs/architecture/CT-CONSULTANT-MODEL-DECISION-AND-IMPLEMENTATION-01.md` (CT01), `…-02.md` (CT02) |
| **Decision source** | `docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md` — §5.2, §6.1–§6.5, §8.1–§8.4, §11–§12, §13.1, §14–§15, §17.1 (F-3…F-9), §19 (OQ-1/OQ-2/OQ-3), §20 (AC-F-3…AC-F-17, AC-S-4, AC-S-10), §24 |
| **Findings closed** | **F-3, F-4, F-6, F-7, F-8** in full; **F-5**, **F-9** entitlement half only (see §26) |
| **Repository** | `/home/shomonrobie/ct_93d5cdd` |
| **Git at time of writing** | branch `p8-release-reconciled`, HEAD `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` (working tree carries several neighbouring uncommitted workstreams — §40) |
| **Agent** | Cline (implementation) |
| **Date** | 2026-10-06 |
| **Migration** | `supabase/migrations/20261103000000_ct_consultant_model_03_client_access_and_mode.sql` — **APPLIED to the local Demo Lab database** |

> **Change markers.** Every CT03 hunk carries the literal string
> `CT-CONSULTANT-MODEL-IMPLEMENTATION-03`, so the CT03 delta is mechanically
> separable from the neighbouring uncommitted workstreams that share this
> working tree (§7). Re-derive the file list with
> `grep -rl 'CT-CONSULTANT-MODEL-IMPLEMENTATION-03'`.

---

## 1. What this document is

This is the **change map / implementation report** for Phase 3 of the ratified
consultant model. It is not a decision record: the business decisions were
already ratified in `CT-CONSULTANT-PO-CONSOLIDATION-01.md`, which this increment
*implements*. The document records what was actually built, why each hunk
exists, how it was verified against the running system, and what remains open.

It is deliberately organised so the **status of every claim is explicit**: a
component is `IMPLEMENTED`, `TESTED`, `LAB-VERIFIED`, `VERIFIED` (by an
independent agent) or `ACCEPTED` (by the Product Owner). These are not synonyms
(AGENTS.md §73), and no acceptance verdict is asserted here.

## 2. Status and the language of acceptance

| Layer | State | Evidence |
|---|---|---|
| Database migration | **IMPLEMENTED · APPLIED (lab)** | §8–§10; columns, tables, constraints and the retention setting queried live |
| Domain rules (pure) | **IMPLEMENTED · TESTED** | §11–§13 |
| Repository / persistence | **IMPLEMENTED · TESTED** | §14 |
| Firm-side API (F-3, F-4, F-6) | **IMPLEMENTED · TESTED · LAB-VERIFIED** | §15, §31 |
| Client-plane API (Plane C) | **IMPLEMENTED · TESTED · LAB-VERIFIED** | §16–§19, §31 |
| Frontend (Plane C + firm editor) | **IMPLEMENTED · TESTED (unit) · BROWSER-VERIFIED** | §21–§23, §32 |
| Security boundaries | **IMPLEMENTED · LAB-VERIFIED (46/46)** | §20, §37 |
| Retention **execution** (deletion) | **NOT IMPLEMENTED — deliberate** | §13, §37 |
| Consultant-retention **API surface** | **NOT IMPLEMENTED — gap recorded** | §37, §38 |
| Independent verification (OHD/QA) | **NOT PERFORMED** | §38 |
| Product-Owner acceptance | **NOT GIVEN** | — |

## 3. Task, authority and source-of-truth hierarchy

The task brief authorises a **client-plane increment**: persist the client access
profile (F-3), express post-relationship retained read-only (F-4), make the three
product modes real and entitlement-gated (F-5), make a mode change a REQUEST
(F-6), serve Plane C at the PO-8 path (F-7), give the client a relationship entry
point (F-8), and keep branding mode-capped (F-9).

Authority was resolved in the order AGENTS.md §2 prescribes: the **running
system** first (the Demo Lab backend, its OpenAPI contract and the lab
database), then current Git source, then the ratified PO document. Where a
ratified rule could not be expressed without inventing policy, the
implementation **fails closed** and the divergence is recorded in §37/§38 rather
than resolved by invention.


---

## 4. Scope — what CT03 delivers

1. **Client access profile (F-3)** — a persisted, server-enforced ceiling on the
   client plane: `off` / `read_only` / `collaborative` / `managed`, plus the
   derived post-relationship state.
2. **Post-relationship retained read-only (F-4, PO-10)** — an ended relationship
   can carry a retained flag that grants READ-only history access, grants no
   write and no messaging-send, and never deletes or clones the Organisation.
3. **Product mode + entitlement (F-5, PO-4/PO-5)** — `standard` / `co_branded` /
   `white_label` persisted once, authoritative over the legacy booleans, and used
   to gate the client plane, the `managed` profile and the custom domain.
4. **Mode-change REQUEST (F-6, PO-1)** — the firm can only *request*; there is no
   consultant write path for the mode at all.
5. **Plane C at `/portal/:clientId/*` (F-7, PO-8 A)** — the client portal route
   family, with its own API namespace and its own authorization gate.
6. **Client-side relationship entry point (F-8, OQ-1/OQ-3)** — authenticated,
   confirmed, auditable, strictly non-destructive change/end requests.
7. **Mode-capped brand (F-9 partial, BR-5)** — a stored white-label flag that
   contradicts the mode is capped at presentation and never destroyed.
8. **Retention policy (OQ-2, now binding)** — one authoritative, Admin-owned
   7-year default in `system_settings`, resolved by a pure module.

## 5. Out of scope (explicitly)

| Not done | Why |
|---|---|
| A **hostname → brand resolution path** (second half of F-9) | Requires a routing decision the brief does not ratify; inventing it would violate INV-F. The entitlement gate it must call exists and is tested. |
| **Retention deletion execution** (auto-delete, legal hold) | The policy model is implemented; deletion is destructive and the migration deliberately disables it (`auto_delete_enabled: false`). Remaining work, not invented. |
| **Client-side `approve_final` role gate** (§13.1 — the `*` in §8.2) | No ratified mechanism decides "which client role may approve for this firm". The profile ceiling therefore denies it (fail closed). |
| **Admin UI to edit the consultant-retention setting** | The Admin settings plane already exposes the platform N3 retention columns; the consultant key is not yet wired to any endpoint (§37). |
| **Client-user invitation/onboarding** (PO-2) | Ratified as consultant-side; deliberately absent from Plane C. |
| **Execution workflow for relationship requests** | Requests are persisted and audited; approval/execution belongs to the out-of-scope CarbonTally support workflow. |

## 6. Change map — the CT03 file set

Derived mechanically from the change marker (§7).

**Backend — new**

| File | Purpose |
|---|---|
| `backend/domain/relationship_access.py` | F-3/F-4/PO-9 — profiles, states, the operation matrix (pure) |
| `backend/domain/consultant_entitlement.py` | F-5/F-6/F-9 — modes, entitlements, BR-5 capping (pure) |
| `backend/domain/consultant_retention.py` | OQ-2/PO-10 — the retention policy resolver (pure) |
| `backend/api/client_portal_auth.py` | Plane C authorization gate + context resolution |
| `backend/api/v3_client_portal.py` | Plane C routes (`/api/v3/portal/...`) |
| `backend/tests/unit/api/test_ct_consultant_model_03.py` | 73 CT03 unit tests |
| `frontend/src/v3/portal/ClientPortal.jsx` | Plane C shell + relationship page |
| `frontend/src/v3/portal/portal.css` | Plane C styling |
| `frontend/src/v3/__tests__/client-portal.test.jsx` | Plane C unit tests |
| `supabase/migrations/20261103000000_ct_consultant_model_03_client_access_and_mode.sql` | The CT03 migration |

**Backend — modified:** `api/v3_consultants.py` (F-3/F-4/F-6 endpoints, audit,
firm-mode resolution), `api/router.py` (Plane C router registration),
`data/consultants.py` (repository methods + projections), `domain/partners.py`
(relationship model fields), `domain/branding.py` (mode-capped brand),
`tests/unit/api/fakes.py` (CT03 fixtures),
`tests/unit/api/test_ct_consultant_model_02.py` (capability-set supersession — §33).

**Frontend — modified:** `src/App.js` (`/portal/:clientId/*`), `src/v3/api.js`
(8 CT03 methods), `src/v3/consultant/ConsultantTeamTab.jsx` (full capability
editor), `src/v3/__tests__/consultant-team-capabilities.test.jsx`.

**Demo Lab — new evidence tooling:** `tools/demo_lab/fixture_ct03_client_plane.py`,
`tools/demo_lab/verify_ct03_client_plane_browser.py`,
`tools/demo_lab/verify_ct03_security_matrix.py`.

## 7. Change markers and delta re-derivation

Every CT03 hunk is marked with the literal
`CT-CONSULTANT-MODEL-IMPLEMENTATION-03`. Re-derive the complete delta:

```bash
grep -rl 'CT-CONSULTANT-MODEL-IMPLEMENTATION-03' \
  --include='*.py' --include='*.js' --include='*.jsx' --include='*.css' \
  --include='*.sql' --include='*.md' . | grep -v '\.venv\|node_modules\|\.git/'
```

That command is the authoritative file list; §6 is its human-readable summary.
**Why the marker matters:** this working tree simultaneously carries CT02,
CT-MP-SUB-003/004, FIN-06 and the storage-management workstream, so `git diff`

---

## 8. Database change — the CT03 migration

`supabase/migrations/20261103000000_ct_consultant_model_03_client_access_and_mode.sql`
— **additive, idempotent, applied cleanly to the local Demo Lab database**
(`carbontally_demo_local`) and verified there.

| # | Change | Detail |
|---|---|---|
| 1 | `consultant_clients.client_access_profile` | `TEXT NOT NULL DEFAULT 'off'` + `CHECK (… IN ('off','read_only','collaborative','managed'))` |
| 2 | `consultant_clients.retained_read_only` | `BOOLEAN NOT NULL DEFAULT false` (PO-10) |
| 3 | `consultant_profiles.commercial_mode` | `TEXT NOT NULL DEFAULT 'standard'` + `CHECK (… IN ('standard','co_branded','white_label'))` |
| 4 | `consultant_relationship_requests` | NEW table (OQ-1/OQ-3): `request_type ∈ {change_consultant, end_relationship}`, `initiated_capacity ∈ {client, consultant, support}`, `status ∈ {requested, confirmed, cancelled, completed}` |
| 5 | `consultant_mode_change_requests` | NEW table (PO-1): `current_mode`/`requested_mode` restricted to the three modes, `status ∈ {requested, approved, rejected, cancelled}`, `effective_at` = the billing/renewal boundary |
| 6 | `system_settings.consultant_relationship_retention` | `{"years": 7, "retained_read_only": true, "legal_hold_blocks_deletion": true, "auto_delete_enabled": false}` |
| 7 | Indexes | `(organization_id, status)` and `(firm_id, status)` for the request queues |
| 8 | Comments | Every new column/table carries the ratified rule in a `COMMENT ON`, so the schema documents the policy |

**Deliberate deny-by-default decisions.** The access profile defaults to `off`
and the mode backfill *preserves an already de-facto mode only* (a firm that was
white-label stays white-label; everything else stays `standard`). No existing
relationship is silently granted a profile — no client plane existed before this
increment, so `off` is not a regression of any shipped capability, and FM-1
("never assume enabled") is the ratified stance.

**Nothing destructive.** No `DROP`, no `TRUNCATE`, no `DELETE`, no data rewrite;
no Organisation is deleted or cloned (§11/§15 — the same `organizations.id` is
preserved through every relationship transition). Verified live after applying:

```
consultant_clients.client_access_profile   text    NOT NULL   default 'off'
consultant_clients.retained_read_only      boolean NOT NULL   default false
consultant_profiles.commercial_mode        text    NOT NULL   default 'standard'
consultant_relationship_requests           4 CHECK constraints + FK organisation_id
consultant_mode_change_requests            2 CHECK constraints + FK firm_id
system_settings.consultant_relationship_retention  = {"years": 7, …}
```

## 9. Database change — RLS and security posture

The two new tables are created with **RLS ENABLED and no policies at all** —
deny-by-default, reachable only by the service-role API behind its own
authorization — the same pattern the repository already uses for
`public.data_discovery_requests` (migration header, §3.3). This is *not* a
weakening of any existing policy:

* no existing policy is altered, dropped or disabled anywhere in the migration;
* the new tables carry no read path for `anon` or `authenticated`;
* the client plane never queries PostgREST directly with the client's token: the
  backend resolves the context and applies its own gate (§18), then reads with
  the service role — so the *API* authorization is the boundary that matters for
  these rows, and the RLS posture (no policies) is the correct fail-closed one.

The two new request tables are append-only in practice: the API only ever
INSERTs a request; no CT03 code path updates or deletes one.

## 10. Database change — the retention policy setting

OQ-2 is now **binding**: the default retention period is **7 years**, owned by
CarbonTally Admin, stored once in `public.system_settings` under

---

## 11. Domain — `relationship_access` (F-3, F-4, PO-9)

`backend/domain/relationship_access.py` is **pure**: it holds no I/O and grants
nothing. It answers exactly two questions.

**States (derived, never a duplicated column).**
`resolve_relationship_state(status, retained_read_only)`:

| `status` | `retained_read_only` | state |
|---|---|---|
| `active` | — | `active` |
| `ended` / `terminated` | `true` | `retained_read_only` |
| `ended` / `terminated` | `false` | `off` |
| `pending` / `rejected` / `suspended` / `inactive` / `onboarding` | *any* | `off` |

The retained flag **cannot lift a non-ended relationship** — only
`ended`/`terminated` qualify (verified by test and by the API's 409, §31).

**Profiles and the ceiling.** `normalise_profile` **fails closed to `off`** for
any unknown/absent value. The write matrix (post-PO amendments) is:

| Operation | off | read_only | collaborative | managed | retained |
|---|---|---|---|---|---|
| `read_data` / `read_reports` / `read_evidence` | ✗ | ✓ | ✓ | ✓ | ✓ |
| `comment` | ✗ | ✓ | ✓ | ✓ | ✗ |
| `upload_document` | ✗ | ✗ | ✓ | ✗ | ✗ |
| `edit_master_data` | ✗ | ✗ | ✓ | ✗ | ✗ |
| `correct_submitted_data` | ✗ | ✗ | ✓ | ✗ | ✗ |
| `approve_final` | ✗ | ✗ | ✓ | ✗ ¹ | ✗ |
| `map_factors` / `edit_mappings` / `recalculate` | ✗ | ✗ | ✗ | ✗ | ✗ |

¹ **Deliberate divergence from the §8.2 matrix text.** §8.2 marks MANAGED
approve-final `✓*`; the `*` is a *conditional* — additionally gated by the client
role and firm configuration (§13.1) — and no such gate exists. Granting it from
the profile alone would confer approval authority that no ratified component
confers, so the ceiling **denies** it and a test
(`test_managed_denies_approve_final_fail_closed`) pins that decision together
with its rationale. Recorded as remaining work in §37/§38.

`profile_allows` evaluates **PO-9 first**, unconditionally, so no
profile/state combination can ever permit mapping or recalculation; an operation
outside `KNOWN_OPERATIONS` is denied by omission (fail closed).

## 12. Domain — `consultant_entitlement` (F-5, F-6, F-9, BR-5)

Three modes, one authority:

| Mode | client plane | managed profile | custom domain | white-label presentation |
|---|---|---|---|---|
| `standard` | ✗ | ✗ | ✗ | ✗ |
| `co_branded` | ✓ | ✓ | ✗ | ✗ (co-branded) |
| `white_label` | ✓ | ✓ | ✓ | ✓ |

* `normalise_mode` **fails closed to `standard`** (FM-1).
* `resolve_mode(mode, wl_flag, co_flag)` — **the stored mode WINS**; the legacy
  D21 booleans are only used when no mode is stored
  (`derive_mode_from_flags`), which reproduces the historical "white-label wins"
  precedence exactly (IMPL-3/FM-2/BR-5). The legacy flags are never destroyed —
  they are capped at presentation.
* Entitlement and capability are kept on **separate axes** (INV-G): a mode grants
  no capability, and no capability can imply a mode.

`domain/branding.py` consumes this to cap the *presentation*: with mode
`standard`, a contradicting stored `white_label_enabled` produces no
CarbonTally-invisible brand (verified by `test_brand_is_capped_by_the_mode`).
This is the **entitlement half of F-9**; the hostname → brand *resolver* is the
unimplemented half (§5, §26).

## 13. Domain — `consultant_retention` (OQ-2, PO-10)

`RetentionPolicy` (frozen dataclass): `years=7`, `retained_read_only=True`,
`legal_hold_blocks_deletion=True`, `auto_delete_enabled=False`. It derives an
expiry (`ended_at + 365 × years`) and answers `is_retained(...)` — nothing else.
`resolve_retention_policy(setting_value)` is **fail-safe**: an absent, malformed,
zero or negative value resolves to the ratified 7-year default, never to
"no retention" and never to "delete now".

The module performs **no I/O and deletes nothing**; the caller owns the legal-hold
state. This is the honest boundary of the increment: the *policy and state model*
are implemented, the *execution* of deletion is not (§37).

## 14. Repository and persistence layer

`backend/data/consultants.py` gained the CT03 persistence methods used by both
planes — `get_relationship_for_org`, `set_relationship_access(profile=…,
retained_read_only=…)`, `create_relationship_request`, `create_mode_change_request`
— plus the projections that carry `client_access_profile`, `retained_read_only`
and `commercial_mode` onto the relationship/branding models. `domain/partners.py`
(`ConsultantClient`) gained the two new fields.

The repository is deliberately thin: **no business rule lives here** (that is
`domain/`'s job) and **no authorization decision lives here** (that is `api/`'s
job). `set_relationship_access` writes only the columns it was given, so a
profile change can never silently reset the retained flag or vice versa. The
firm-side routes re-check ownership of the relationship before calling it (§15),
and the client plane can never reach it at all (§17).

`consultant_relationship_retention` (reusing the existing Admin configuration
architecture that already carries `data_retention_days`,
`document_retention_days` and `audit_log_retention_days`). The duration is
therefore **not** hard-coded into business logic (§24); it is resolved by
`domain/consultant_retention.resolve_retention_policy`.

---

## 15. API surface — firm side (F-3, F-4, F-6)

All three routes were read from the **running** `/openapi.json` (645 paths) — they
are not documented from memory:

| Method | Path | Purpose | Gate |
|---|---|---|---|
| `POST` | `/api/v3/consultants/clients/{client_id}/access-profile` | Set the client profile (F-3) | consultant firm + `CAP-MANAGE-CLIENTS` |
| `POST` | `/api/v3/consultants/clients/{client_id}/retention` | Apply/lift retained read-only (F-4, PO-10) | consultant firm + `CAP-MANAGE-CLIENTS` |
| `POST` | `/api/v3/consultants/me/mode-change-requests` | REQUEST a mode change (F-6, PO-1) | consultant firm + `CAP-MANAGE-TEAM` |

Behaviour enforced in the handlers (each verified live, §31):

* **ownership first** — a client id belonging to another firm is a **404**, never
  a 403 and never an oracle: the firm must not learn that the row exists;
* **validation** — an unknown profile is `422` (`extra="forbid"` on the model, so
  a forged field such as `is_active` is a validation error rather than a silent
  no-op); an unknown mode is `422`; requesting the *current* mode is `422`;
* **entitlement** — setting `managed` while the firm's mode is `standard` is
  `403` (PO-4);
* **retention** — applying retained read-only to an **active** relationship is
  `409`; only `ended`/`terminated` may be retained;
* **audit** — each action appends an `AuditEntry` with
  `changed_fields={before, after}` (`consultant.client_access_profile_updated`,
  `consultant.relationship_retained_read_only` / `…_retention_lifted`,
  `consultant.mode_change_requested`). The audit helper can never break the firm
  action (a failure is swallowed) — deliberately, because an audit outage must
  not become a security bypass *and* must not block a legitimate operation.

**There is no consultant write path for `commercial_mode` anywhere.** The mode is
CarbonTally-Admin-owned (PO-5); the firm can only request. Verified live: after an
accepted request the stored mode is unchanged (§31).

## 16. API surface — client plane (Plane C, F-7, F-8)

Router: `backend/api/v3_client_portal.py`, prefix `/api/v3/portal`, mirroring the
PO-8 binding route family `/portal/:clientId/*`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v3/portal/{client_id}/context` | Context + the profile ceiling matrix (MUST-2) |
| `GET` | `/api/v3/portal/{client_id}/organization` | Organisation-scoped data only (MUST-7) |
| `POST` | `/api/v3/portal/{client_id}/annotations` | Client comment / respond to a query |
| `POST` | `/api/v3/portal/{client_id}/relationship-requests` | OQ-1/OQ-3 change/end REQUEST |

`GET /context` returns the server-authoritative `organization`, `consultant`,
`brand`, `mode`, `profile`, `state`, `retained_read_only` and a `capabilities`
map. **The capabilities map is a UI hint only** — every route independently calls
`ensure_client_operation(context, …)`, so removing the UI hint would change
nothing about what is permitted (the UI is not the security boundary).

The relationship-request route is strictly non-destructive (T-1): it requires
`confirmed: true` (`428` otherwise), rejects an unknown `request_type` (`422`),
and returns `409` on an already-ended relationship ("contact CarbonTally support
to reconnect"). It creates an audit row and a `consultant_relationship_requests`
record — never a status change. This is OQ-1/OQ-3 answered **by mechanism**: the
client initiates and confirms; CarbonTally decides and records; nothing is
destroyed, and the OFF-client case resolves through the documented support path.

## 17. Deliberate route absence (PO-9 / PO-2 / PO-5)

The client plane has **no** route for: factor mapping, mapping edits,
recalculation, user invitation/management, branding, plan/billing/subscription,
or changing one's own access profile. This is not merely "the UI hides it":

* a unit test asserts route **absence** via `app.openapi()["paths"]`;
* the live matrix asserts `/portal/{id}/factors`, `/portal/{id}/mappings` and
  `/portal/{id}/recalculate` return `404`/`405` for a legitimate client token;
* PO-9 is additionally enforced *positively* inside `profile_allows`, so even if a
  route were later added the operation would still be denied.

Absence of a route is a stronger guarantee than a deny branch — there is no code
path to forget to guard.

## 18. Authorization model — the resolution order

`backend/api/client_portal_auth.py` is the single server-side gate for Plane C. It
enforces the §6.2 order and **fails closed at every step**:

1. **authenticated?** — no user → `401`.
2. **identity separation** — internal staff or processing-entity identities are
   refused (`403`): they have their own planes (§7.1, AGENTS §45).
3. **organisation binding** — the actor must be an *active organisation member*
   **and** their organisation must equal `:clientId`. A foreign `:clientId` is
   refused **generically**.
4. **relationship exists** — an organisation with no consultant relationship is a
   direct customer: Plane C does not apply → refuse.
5. **state** — only `active` or `retained_read_only` may use the plane
   (INV-E / AC-S-4).
6. **entitlement** — the firm's mode must entitle a client plane; a `standard`
   firm exposes none (MUSTNOT-5 / AC-F-16).
7. **profile ceiling** — every read and write is then judged by
   `profile_allows(operation, profile, state)`.

**One denial, always.** Every failure raises the identical
`PORTAL_DENIED_DETAIL = "Client portal access is not available for this
workspace"` — the same status and the same body whether the organisation does not
exist, belongs to another tenant, has no consultant, is suspended, or is paused
(§11.4 / AC-F-17 / AC-S-10: no existence oracle, no identifier leak). The UI
renders that single generic message; the client cannot vary `clientId`,
organisation or tenant through the URL.



---

## 19. Authorization matrix — client plane (verified live)

State × profile × operation, as the running backend actually answers (lab
evidence, §31). "gate" = the resolution step that decides.

| Actor profile / state | `GET /context` | `POST /annotations` | `/factors`, `/recalculate` |
|---|---|---|---|
| `managed` (active, mode `white_label`) | **200** | **201** | **404** |
| `read_only` (active) | **200** | **201** | **404** |
| `collaborative` (active) | **200** | **201** | **404** |
| `off` (active) | **403** | **403** | **403/404** |
| `read_only` + `ended` + retained | **200** | **403** (PA-3) | **403/404** |
| `read_only` + `ended`, retained lifted | **403** | **403** | — |
| same firm, mode `standard` | **403** | **403** | — |
| direct customer (no relationship) | **403** | **403** | — |
| foreign `:clientId` (any actor) | **403** | **403** | — |
| unauthenticated | **401** | **401** | — |

Two rows deserve emphasis:

* **entitlement beats profile** — with the firm in `standard` mode the very same
  client whose profile is `managed` is refused: the *mode* gate is evaluated
  before the profile can matter (F-5/MUSTNOT-5).
* **retained is read-only** — the retained client still reads its own history
  (`200`) but cannot write (`403`), which is exactly PA-1…PA-3; the state is
  re-derived from `status` + flag on every request, so lifting the flag closes
  the plane on the next call.

## 20. Identity separation and cross-tenant denial

Verified live with real password-grant tokens (46-check matrix, §31):

| Attempt | Result |
|---|---|
| consultant owner → client plane | **403** |
| consultant member → client plane | **403** |
| internal operator → client plane | **403** |
| platform admin → client plane | **403** |
| PE manager → client plane | **403** |
| client → consultant plane (`/consultants/me`) | **403** |
| client → firm access-profile write | **403** |
| client → mode-change request | **403** |
| firm → another firm's client id | **404** (no oracle) |
| managed client → another client's organisation (deep link) | **403**, generic copy, and the browser shows no trace of the other organisation |

This is the §45 negative-test set for the consultant model: Customer↔Customer,
Consultant↔Client, PE→client, staff→internal, client→internal. **No unexpected
ALLOW was observed.** The one nuance worth recording: a *consultant* identity is
refused on Plane C *by design* — consultants operate Plane B (the firm
workspace), and admitting them to the client plane would collapse two boundaries.

## 21. Frontend — Plane C client shell

`frontend/src/v3/portal/ClientPortal.jsx` (+ `portal.css`) implements the PO-8
route family. It is a **shell that grants nothing**: every call it makes is
re-authorised server-side, and a deep link to a foreign `:clientId` renders a
generic notice rather than data.

| Route | Renders |
|---|---|
| `/portal/:clientId` | Overview: organisation (name, country, status), the profile in words, and the comment box **only when `capabilities.comment` is true** |
| `/portal/:clientId/relationship` | Firm, relationship status, profile, workspace; for an active link, the non-destructive change/end **request** actions (each behind `window.confirm`); for a retained link, an explanatory card instead |
| `/portal/:clientId/*` | The generic denial notice |

Meaningful business copy, not status codes (AGENTS §75/§76):

* profile labels: `Read only`, `Collaborative`, `Managed by your consultant`,
  `No portal access`;
* `OFF` and `RETAINED` never share copy (P-9): the retained banner says the
  engagement **has ended** and that data **was not deleted**; the OFF notice says
  the workspace is not available and points to the consultant/support;
* a retained client sees "Commenting is not available for this workspace after
  the engagement has ended" instead of a live comment box, and a card explaining
  that clients never map factors or trigger recalculation and why.

## 22. Frontend — firm-side capability editor

`frontend/src/v3/consultant/ConsultantTeamTab.jsx` now exposes the **full
operational capability set** the backend actually stores (P1/P5), not the two
flags CT02 introduced: `can_view_client`, `can_approve`, `can_manage_clients`,
`can_upload_documents`, `can_generate_reports`, `can_manage_team`, plus the
P6-2A processing set (`can_extract`, `can_map`, `can_validate`, `can_calculate`,
`can_confirm_automation`, `can_submit`).

The corresponding API model is **partial by design** with `extra="forbid"`, so
granting one capability never silently resets the others (F-10: a capability
write must MERGE, never REPLACE) and **no commercial entitlement is
addressable** — plan, seats, mode, white-label or custom-domain entitlement have
no field, and an attempted forged field is a `422`, not a silent no-op (§6.3/P5).

## 23. Frontend — routing and API client

`src/App.js` mounts `<Route path="/portal/:clientId/*" element={<ClientPortal />} />`
(the parameter is the **client organisation**, per PO-8 A). `src/v3/api.js` gained
eight methods: `getPortalContext`, `getPortalOrganization`, `postPortalAnnotation`,
`requestPortalRelationshipChange`, `setConsultantClientAccessProfile`,
`setConsultantClientRetention`, and the mode-change request — all routed through
the shared `v3Fetch` helper, so the error envelope
(`{"error": {"code", "message"}}`) is handled consistently and the UI can show a
human message rather than a raw technical error (AGENTS §46).

The migration also records `auto_delete_enabled: false` so that the *policy
model* is unambiguous: nothing in CT03 deletes anything. Deletion execution
remains unimplemented by design (§37).

alone cannot attribute a hunk to CT03.



---

## 24. Invariant register and verification

| Invariant | Meaning (PO doc §5.5) | CT03 position | Evidence |
|---|---|---|---|
| **INV-A** | Consultant A can never reach Consultant B's clients | **LAB-VERIFIED at the firm-administration boundary** | targeting another firm's relationship id → `404` (§31); CT03 adds no cross-firm query path |
| **INV-B** | Client A can never reach Client B's organisation | **LAB-VERIFIED** | deep link → `403` with generic copy; browser shows no trace of the other organisation (§32) |
| **INV-C** | A client user can never reach another client's organisation | **LAB-VERIFIED** | as INV-B, driven by the actor's *own* membership (§18 step 3) |
| **INV-D** | A consultant can never reach an unlinked organisation | **LAB-VERIFIED (client plane + firm admin)**; org-data posture otherwise unchanged | the plane refuses a relationship-less organisation; firm admin refuses a foreign client id. CT03 does not alter RLS |
| **INV-E** | The client plane is never usable for a link that is not ACTIVE | **LAB-VERIFIED** | `off` and lifted-retention → `403`; non-active statuses denied by unit test |
| **INV-F** | No decision is taken from a hostname, subdomain or brand | **PARTIAL — not violated, not complete** | the brand is now *derived from the mode* and capped (BR-5) and nothing in CT03 consumes a hostname; the ratified hostname→brand resolver is unimplemented (§26 F-9) |
| **INV-G** | Entitlement is never a substitute for capability, nor capability for entitlement | **LAB-VERIFIED** | `managed` profile refused in `standard` mode (`403`); a forged entitlement field on the capability model is `422`; capability writes cannot change the mode |

## 25. Acceptance-criteria traceability

| AC | Requirement | Where verified |
|---|---|---|
| **AC-F-3** | Profile persisted and enforced on every Plane C read **and** write | `TestClientAccessProfileMatrix`; live matrix (`/context` 200/403 per profile; `annotations` 201/403) |
| **AC-F-4** | `OFF` and `POST-RELATIONSHIP` are distinct states with non-alarming copy | separate banner vs generic notice in `ClientPortal.jsx`; browser evidence §32 |
| **AC-F-5** | Retained read-only resolves; duration NOT invented | live: retained → `200`; lifted → `403`; policy default 7 y, `auto_delete_enabled=False` |
| **AC-F-6** | `MANAGED` unavailable in STANDARD; custom domain only in WHITE-LABEL | live: profile write → `403` in standard mode; `custom_domain_available` per mode in unit tests |
| **AC-F-7** | A mode change is a REQUEST decided by CarbonTally; direct mutation rejected | live: `201` request recorded, stored mode unchanged; no consultant write path exists |
| **AC-F-8** | Plane C served on `/portal/:clientId/*` | `App.js` route + OpenAPI `/api/v3/portal/*` + deep-link browser test |
| **AC-F-9** | Client-user invitation/management exists only consultant-side | route-absence test; live `/portal/{id}/factors|mappings|recalculate` → `404` |
| **AC-F-16** | A STANDARD-mode firm exposes no client plane at all | live: `403` while mode `standard`, `200` after restore |
| **AC-F-17** | A deep link to a foreign `:clientId` fails generically (no oracle) | live `403` with an identical body; browser-confirmed |
| **AC-S-4** | The plane is unusable for any state other than ACTIVE / RETAINED | `state_has_client_plane` + live `off`/lifted `403` |
| **AC-S-10** | No identifier/timing disclosure on denial | one `PORTAL_DENIED_DETAIL` for every denial class |

## 26. Requirement traceability (F-3 … F-9)

| Finding | Ratified requirement | CT03 status |
|---|---|---|
| **F-3** | Persist and enforce the client access profile (§8.1/§8.3/§8.4) | **CLOSED** — column, CHECK, matrix, UI label, live enforcement |
| **F-4** | A state that expresses RETAINED read-only after termination (PO-10) | **CLOSED** — flag + derived state + read-only enforcement; deletion deliberately not implemented |
| **F-5** | Three modes, entitlement-gated; branding not ungated | **ENTITLEMENT HALF CLOSED** — mode column, entitlement matrix, plane/profile/domain gating, mode-capped brand. The hostname→brand resolver remains open (see F-9) |
| **F-6** | Mode change is a REQUEST at the billing boundary (PO-1) | **CLOSED** — request table, request-only API, consultant write path absent, Admin decides |
| **F-7** | Plane C served at `/portal/:clientId/*` (PO-8 A) | **CLOSED** — route + API namespace + gate; browser-verified |
| **F-8** | A client-side relationship entry point (change/end) | **CLOSED (mechanism = request)** — confirmed, audited, non-destructive; OFF clients use the support path (OQ-3) |
| **F-9** | Entitlement-checked hostname→brand resolution (§12.3, INV-F) | **PARTIAL** — the entitlement gate and mode capping exist and are tested; the *resolution path* is not implemented and nothing takes a decision from a hostname (INV-F is not violated). Remaining work §37 |


## 27. PO decision traceability

| PO | Decision | CT03 implementation |
|---|---|---|
| **PO-1** | Mode change = request, effective at the billing/renewal boundary | `consultant_mode_change_requests` + `effective_at`; request-only API |
| **PO-2** | Client-user invitation is consultant-side only | absent from Plane C (route-absence test) |
| **PO-3A** | Firm-level branding only | the portal renders the **firm** brand resolved from the firm record; no per-client or client-editable branding |
| **PO-3B** | White-label availability is mode-dependent | `white_label_presentation` entitlement; capped brand |
| **PO-4** | `MANAGED` and the custom domain are gated | `managed_profile_available` / `custom_domain_available`; live `403` in standard mode |
| **PO-5** | The mode is CarbonTally-Admin-owned | no consultant write path; the stored mode is unchanged after a request (verified) |
| **PO-6** | Client-side approval is role+config gated | **not implemented** — the ceiling denies `approve_final` for `managed` (fail closed, §11) |
| **PO-7** | Either party may end; audited; non-destructive | relationship requests persist + audit; nothing is deleted; a retained end keeps the organisation |
| **PO-8** | Plane C at `/portal/:clientId/*` | implemented + browser-verified |
| **PO-9** | Clients never map factors / edit mappings / recalculate | enforced first in `profile_allows`, asserted for every profile × state, absent from the API *and* the UI |
| **PO-10** | Post-relationship retained read-only, subject to policy | retained state + read-only enforcement + 7-year policy (deletion not executed) |

## 28. Open-question resolution (OQ-1 … OQ-3)

| OQ | Question | CT03 resolution |
|---|---|---|
| **OQ-1** | The mechanism by which a client changes or ends its consultant relationship | **Resolved as a mechanism:** an authenticated, *confirmed* REQUEST (`relationship-requests`) that creates an auditable record and changes nothing; the consultant/support path decides. A one-click destructive toggle is explicitly not implemented (T-1) |
| **OQ-2** | The retention period and its scope | **Resolved by the PO: 7 years**, Admin-configurable, one authoritative setting resolved by a pure module with a fail-safe default; scope = the relationship's organisation data with retained read-only access while the policy allows and a legal hold overriding deletion |
| **OQ-3** | How a relationship ends when the client has no plane at all (`off`) | **Resolved by path, not by invention:** for an OFF client the plane does not exist, so initiation is the consultant / CarbonTally support route; the portal copy points there and the request endpoint is unreachable for that client **by construction** |


---

## 29. Manual test identities (10 roles)

All identities are **local Demo Lab only** (`@demo-lab.carbontally.local`, shared
lab password from the lab credential store — never committed). Three are created
by the CT03 fixture (§30); the rest already exist in the lab. The authoritative
strings are in `tools/demo_lab/fixture_ct03_client_plane.py` (`NEW_CLIENTS`) and
`~/ct_local_env/demo_lab/credentials.local.json`.

| # | Role | Identity | What the CT03 manual pass should show |
|---|---|---|---|
| 1 | Consultant **firm owner** | `consultant.owner@demo-lab.carbontally.local` | Firm workspace; can set a client profile; can *request* a mode change; **cannot** write the mode |
| 2 | Consultant **firm member** | `consultant.member@demo-lab.carbontally.local` | Sees only the clients its `client_access`/`can_view_client` allows; **denied** the mode-change request (no `CAP-MANAGE-TEAM`) |
| 3 | Client owner, **read_only** | `owner.clienta@demo-lab.carbontally.local` | `/portal/02b38744-27fe-5062-8f36-9af7a726eb4c` → "Read only": reads, may comment, cannot upload/edit |
| 4 | Client owner, **collaborative** | `owner.clientb@demo-lab.carbontally.local` | `/portal/b4bb08f1-52d5-5155-9572-99026760814c` → "Collaborative" contribution ceiling |
| 5 | **Managed** client owner | `ct03.owner.managed@demo-lab.carbontally.local` | `/portal/5aaf36d2-3d9b-579f-b230-9e434dd89772` → "Managed by your consultant"; comment enabled; no upload/edit/approve |
| 6 | **Retained** client owner | `ct03.owner.retained@demo-lab.carbontally.local` | `/portal/f633fd92-a059-5716-a634-9a07d9c9af85` → ended banner, "Ended (retained read-only)", reads history, **no** comment box, **no** request buttons |
| 7 | **OFF** client owner | `ct03.owner.off@demo-lab.carbontally.local` | `/portal/6d53a26b-0d05-53d1-8daf-eef7c7ac761c` → the generic unavailable notice only |
| 8 | **Internal operator** | `operator@demo-lab.carbontally.local` | Denied the client plane entirely (has its own plane) |
| 9 | **Platform admin** | `platform.admin@demo-lab.carbontally.local` | Denied the client plane; owns the mode decision (PO-5) — the fixture performs it on their behalf |
| 10 | **PE manager** | `pe.manager@demo-lab.carbontally.local` | Denied the client plane (PE isolation, AGENTS §32) |

## 30. Demo Lab QA fixture — design and isolation

`tools/demo_lab/fixture_ct03_client_plane.py` (`FIXTURE_ID =
ct-consultant-03-client-plane`) makes every CT03 state reachable in the lab. It
follows the existing `fixture_mp_coverage.py` pattern: deterministic UUIDs,
idempotent `INSERT … ON CONFLICT`, explicit labels, and a `--reset` that removes
**exactly** what it created and restores the two rows it touched.

```bash
python3 tools/demo_lab/fixture_ct03_client_plane.py           # apply (idempotent)
python3 tools/demo_lab/fixture_ct03_client_plane.py --verify  # live checks
python3 tools/demo_lab/fixture_ct03_client_plane.py --reset   # remove + restore
```

| Item | Value (all ids new; the two pre-existing rows are restored on reset) |
|---|---|
| Firm mode (Admin-owned) | `Demo Lab Carbon Consultants` → `commercial_mode = 'white_label'` (reset → `standard`) |
| `client_a` relationship profile | `read_only` (reset → `off`) |
| `client_b` relationship profile | `collaborative` (reset → `off`) |
| `CT03-QA Managed Client` | org `5aaf36d2-3d9b-579f-b230-9e434dd89772`, relationship `9d084191-81ae-538c-9dff-0cbc0f370809`, active, `managed` |
| `CT03-QA Retained Client` | org `f633fd92-a059-5716-a634-9a07d9c9af85`, relationship `742c9401-c4de-5623-9bcd-27dd0a1ce849`, **ended**, `read_only`, retained |
| `CT03-QA Off Client` | org `6d53a26b-0d05-53d1-8daf-eef7c7ac761c`, relationship `2ea78568-4d64-5a55-9e9a-116b14448de9`, active, `off` |

**Two deliberate isolation decisions** (both learned from the running system, not
assumed):

1. the fixture **adds no second organisation membership to any existing demo
   identity**. `auth.py` resolves a user's organisation with `maybe_single()`, so
   a second active membership would break that identity's organisation resolution
   *and every other fixture that uses it*. Instead three NEW client identities are
   provisioned, each with exactly one membership — an invariant `--verify` asserts
   (`identity[x].active_memberships == 1`);
2. the fixture **creates no consultant write path for `commercial_mode`**. PO-5
   forbids one, so the mode is set the way CarbonTally Admin would — directly on
   `consultant_profiles.commercial_mode` — while the consultant surface only ever
   *requests* (F-6).

The fixture writes only to the local Demo Lab database and the local lab gateway.
The investor-demo dataset and the MP-FX (CT-MP-SUB) fixture orgs/firms are never
touched.

---

## 31. Lab evidence — live API and security matrix

Two independent verifiers run against the **running** backend
(`http://127.0.0.1:8070`), using the same password-grant login path as the
browser.

**A. `tools/demo_lab/fixture_ct03_client_plane.py --verify` → 32/32 PASS**

Firm mode; the two pre-existing profiles; and for each fixture client: the stored
`status`/`profile`/`retained` tuple, exactly one active membership, a successful
real login, and the portal verdict —

* `managed` → `200`, `profile=managed`, `state=active`, `read_data=true`,
  `comment=true`, `upload_document=false` (PO-4), `map_factors=false`,
  `recalculate=false` (PO-9);
* `retained` → `200`, `state=retained_read_only`, `read_data=true`,
  `comment=false`, `upload_document=false` (PA-3);
* `off` → `403`.

**B. `tools/demo_lab/verify_ct03_security_matrix.py` → 46/46 PASS**

Highlights:

* **identity separation** — consultant owner, consultant member, internal
  operator, platform admin and PE manager are all **denied** the client plane; a
  client is denied the consultant plane and the firm access-profile write;
* **entitlement gate** — with the firm flipped to `standard` the *same* `managed`
  client is refused (`403`) and a `managed` profile write is refused (`403`);
  restored to `white_label` → `200`;
* **profile ceiling** — unknown profile → `422`; another firm's client id → `404`;
* **PO-9** — `/portal/{id}/factors|mappings|recalculate` → `404`; no client write
  route beyond comment;
* **retained lifecycle** — apply-on-active → `409`; apply-on-ended → `200`;
  lift → the plane closes (`403`); re-apply → it re-opens (`200`); the
  organisation row still exists (nothing deleted);
* **mode change** — firm owner → `201` with an auditable `requested` row; request
  for the current mode → `422`; unknown mode → `422`; firm member without
  `CAP-MANAGE-TEAM` → `403`; client → `403`; and the stored `commercial_mode` is
  **unchanged** (PO-5);
* **retention policy** — the setting is present, resolves to **7 years**, has
  `auto_delete_enabled=False`, and fails safe on absent/malformed input.

## 32. Lab evidence — browser verification

`tools/demo_lab/verify_ct03_client_plane_browser.py` (real headless Chrome at
`/usr/bin/google-chrome`, real logins, no token injection) → **31/31 PASS**, one
full-page screenshot per state:

```
~/ct_local_env/demo_lab/evidence/browser/ct03_plane_managed.png
~/ct_local_env/demo_lab/evidence/browser/ct03_plane_retained.png
~/ct_local_env/demo_lab/evidence/browser/ct03_plane_off.png
~/ct_local_env/demo_lab/evidence/browser/ct03_plane_cross_tenant.png
~/ct_local_env/demo_lab/evidence/browser/ct03_plane_client_a_read_only.png
~/ct_local_env/demo_lab/evidence/browser/ct03_plane_retained_relationship.png
```

Asserted against **rendered text**, not internals: the managed client sees its
organisation name, "Managed by your consultant" and the comment box; the retained
client sees the organisation name, the ended banner and "Commenting is not
available for this workspace after the engagement has ended" and **not** the
comment box; the OFF client sees only "This workspace is not available /
Client portal access is not available for this workspace"; the managed client
deep-linking to another client's organisation gets that same generic notice with
**no trace of the other organisation**; the read-only client sees "Read only" plus
its comment affordance; the retained relationship page says "Ended (retained
read-only)" and offers **no** end/change request buttons.

**Two recorded environment notes — not CT03 defects.** Every page logs three
`ws://127.0.0.1:54430/realtime/v1/websocket` handshake errors because the lab
gateway does not complete the Supabase Realtime upgrade (pre-existing, present on
the denied page too); and each *expected* denial logs the 403 it should log. The
verifier classifies both explicitly and fails only on **unexpected** application
console errors (AGENTS §78).


---

## 33. Test evidence — backend unit

`backend/tests/unit/api/test_ct_consultant_model_03.py` — **73 tests, exit 0,
0 failures** (`./.venv/bin/python -m pytest
tests/unit/api/test_ct_consultant_model_03.py -q`). Coverage by class:

| Class | Tests | What it pins |
|---|---|---|
| `TestClientAccessProfileMatrix` | 9 | state derivation; PO-9 denied in **every** profile × state; OFF permits nothing; read-only reads+comments only; collaborative contributes; managed is curated; the fail-closed `approve_final` decision (§11); retained is read-only with no send; unknown operation fails closed |
| `TestProductModeEntitlement` | 8 | unknown mode → standard; the mode wins over a contradicting legacy flag; legacy derivation preserved when no mode is stored; plane/managed/domain gating per mode; brand capping (BR-5) |
| `TestRetentionPolicy` | 3 | default 7 years; configurable and validated; expiry derived, not hard-coded |
| `TestPlaneCGate` | 9 | active client reaches its own workspace; foreign client id denied generically; direct customer has no plane; OFF has no plane; non-active links denied; standard-mode firm has no plane; retained resolves read-only; unauthenticated rejected; consultant identity not admitted |
| `TestPlaneCWriteCeiling` | 4 | active profiles may comment; retained may not; organisation read is organisation-scoped; **no mapping/recalculation route exists** (asserted via `app.openapi()["paths"]`) |
| `TestClientRelationshipRequests` | 4 | client can request an end; confirmation required; invalid type rejected; a retained client cannot re-request on the plane |
| `TestCapabilityAdministration` | 5 | the full operational set is grantable; a consultant cannot elevate itself; cross-firm target denied; commercial entitlement is not addressable; administration denied without `CAP-MANAGE-TEAM` |
| `TestFirmSideRelationshipAdministration` | 7+ | profile is entitlement-checked; set when entitled; unknown value rejected; foreign target denied; retention only on an ended relationship; retention applicable; mode change is a request not a write; unknown/no-op mode rejected |

**Deliberate supersession (CT02 → CT03).** CT02's unknown-capability test asserted
`can_manage_team` was not an addressable field; CT03 exposes the full operational
capability set (P1/P5), so that expectation was replaced by the correct one
(`can_grant_seat_entitlement` — a *commercial entitlement* — is the thing that
must remain unaddressable). This is a change to an existing test with a stated
reason, not a silently weakened assertion; the commercial-entitlement boundary is
still asserted (`test_commercial_entitlement_is_not_addressable`).

## 34. Test evidence — frontend unit

`CI=true npx react-scripts test --watchAll=false --testPathPattern='(client-portal|consultant-team-capabilities)'`:

```
PASS src/v3/__tests__/consultant-team-capabilities.test.jsx
PASS src/v3/__tests__/client-portal.test.jsx
Test Suites: 2 passed, 2 total
Tests:       7 passed, 7 total
```

These cover the Plane C render paths (denied / retained / comment capability) and
the firm-side capability editor's merge semantics. They are **unit tests with a
mocked API client**; end-to-end behaviour is established by §31–§32.


## 35. Full-suite regression position vs the CT02 baseline

A complete backend unit run collects **5,081 tests**. The failure set is
**identical to the CT02 baseline** — 8 failures, the same 8 ids — so CT03
introduces **no new failure**:

```
FAILED tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin
FAILED tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
FAILED tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration
FAILED tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy
FAILED tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage
```

The CT03 test file passes in full inside that same run (its 73 tests are part of
the collected total), and the CT03-specific suites (§31–§34) pass independently.

## 36. Failure attribution and baseline honesty

The 8 failures are **pre-existing and out of CT03 scope**; they were the recorded
CT02 baseline. They are not "known-red by design" — they are stale maintenance
items, and saying so plainly is more useful than a green claim:

| Group | Count | Diagnosis (read from the test source, not guessed) |
|---|---|---|
| `test_extraction_suggestions.py` | 3 | Extraction-suggestion engine expectations drift from the current engine (unrelated subsystem; no CT03 file touched) |
| Migration-contract tests (`i1`, `i2`, `p17`, `d17_revision`) | 4 | **Migration-inventory allow-lists.** `test_i1_migration_is_the_latest_migration` enumerates the *exact* migrations allowed to follow I1, and its list ends at `20261007…`; the repository has since appended P17, the MP-SUB migrations and CT02 — so these were already red before CT03 and remain red for the same reason |
| `test_v3_discovery.py::…::test_create_request_as_admin` | 1 | Discovery-request authorization expectation (unrelated subsystem) |

**Consequence for CT03:** adding
`20261103000000_ct_consultant_model_03_…` does **not** create a new failure — the
same four tests were already failing for the same reason — but a future
migration-contract chore should extend those allow-lists (or convert them to a
"declared order" assertion) so the inventory test stops taxing every migration
append. That is deliberately **not** done here: it would edit another
workstream's contract tests inside a client-plane increment.


---

## 37. Known gaps and remaining work

Ordered by what a reviewer should look at first.

| # | Gap | Evidence | Severity | Suggested next step |
|---|---|---|---|---|
| G-1 | **The consultant-retention setting has no API surface.** `GET /api/v3/settings/retention` exposes the platform N3 columns only (`audit_log_retention_days`, `data_retention_days`, `document_retention_days`, `backup_retention_days`, `operational_telemetry_retention_days`); `consultant_relationship_retention` is stored and resolvable in code but not readable/writable through any endpoint | live payload captured in §31; `RETENTION_SETTING_KEY` has no caller outside its module and tests | MEDIUM | Wire the key into the existing N3 settings endpoint/UI, after the PO decides who may edit it |
| G-2 | **Retention deletion is not executed.** The policy model exists; nothing deletes, and `auto_delete_enabled` is deliberately `false` | migration setting; §13 | MEDIUM | Implement only once the PO confirms the execution policy and legal-hold semantics |
| G-3 | **No client-side `approve_final` role gate** (§13.1), so `MANAGED` denies approval at the ceiling | §11 note ¹; pinned by `test_managed_denies_approve_final_fail_closed` | MEDIUM | PO decision on which client role may approve, then a role+config gate; only then may the MANAGED ceiling admit it |
| G-4 | **F-9 hostname→brand resolver unimplemented** — the entitlement gate exists, the resolution path does not | §26; the only domain code is *management* (`api/v3_whitelabel.py`) | MEDIUM | Design + ratify the resolution path; INV-F is currently satisfied by having no hostname input at all |
| G-5 | **Relationship/mode REQUESTs have no decision consumer.** They persist as `requested`; nothing advances them | no updater for either request table in CT03 | LOW–MEDIUM | A CarbonTally-admin decision surface (approve/reject + `effective_at`) |
| G-6 | **The capability matrix advertises `read_reports` / `read_evidence`, but Plane C renders no report or evidence page yet** (overview + relationship only) | `ClientPortal.jsx` routes; `portal_capabilities()` output | LOW | Add the read-only report/evidence views (the ceiling already permits them) |
| G-7 | **The four migration-contract tests stay red** (pre-existing inventory allow-lists) | §36 | LOW | Extend the allow-lists / restate the contract |
| G-8 | **The Demo Lab gateway does not proxy the Supabase Realtime WebSocket** | §32 note; pre-existing | LOW (environment) | Fix the lab gateway upstream if realtime UI is to be browser-verified |
| G-9 | Planned retention expiry is computed but never enforced (`is_retained` has no production caller) | `domain/consultant_retention.py` | LOW | Call it where retained access is resolved, once G-2 is decided |

**Explicitly not a gap:** there is no consultant path to write `commercial_mode`,
no client path to manage users, and no client path to map factors — those
absences *are* the requirement (§17).

## 38. PO DECISION REQUIRED register

| # | Decision needed | Why it cannot be inferred |
|---|---|---|
| **PD-1** | Which **client role(s)** may exercise `approve_final`, under what firm configuration (§13.1 — the `*` in §8.2)? | The matrix marks the cell conditional but never names the condition; granting it unconditionally would invent approval authority (G-3) |
| **PD-2** | **Post-termination messaging (OQ-4):** does a retained relationship keep a messaging channel, a notice-only channel, or none? | PA-3 currently forbids sends; CT03 implements "none" and must not extend that without a decision |
| **PD-3** | **Retention execution:** is indefinite retention (no auto-delete) the intended end state, or must deletion run at the 7-year expiry, and who is notified? | The period is ratified; the execution and legal-hold operation are not (G-2, G-9) |
| **PD-4** | **Who may edit the consultant-retention setting** (System Admin only, or Staff Admin too), and should it appear in the Admin UI? | N3 says "the approved Settings/Admin control plane"; role granularity is a PO choice (G-1) |
| **PD-5** | **Who confirms a client-initiated relationship request**, within what SLA, and what the client sees meanwhile? | OQ-1 ratified *that* either party may initiate and that it is audited — not the operational workflow (G-5) |
| **PD-6** | **Hostname→brand resolution:** which hostnames may resolve, and what happens for an unverified or suspended domain? | §12.3 requires an entitlement-checked mapping; the routing policy is not ratified (G-4) |


## 39. Reproduction procedure

Run from the repository root unless stated otherwise. The Demo Lab must be
running; the exact live state is recorded in §40.

```bash
# 1. Backend unit tests for the CT03 surface
cd backend && ./.venv/bin/python -m pytest tests/unit/api/test_ct_consultant_model_03.py -q
#    -> 73 passed (exit 0)

# 2. Full backend unit suite (regression position, §35)
cd backend && ./.venv/bin/python -m pytest tests/unit -q --tb=no -rf
#    -> 5,081 collected; the same 8 pre-existing failures as the CT02 baseline

# 3. Frontend unit tests
cd frontend && CI=true npx react-scripts test --watchAll=false \
  --testPathPattern='(client-portal|consultant-team-capabilities)'
#    -> Test Suites: 2 passed, 2 total; Tests: 7 passed

# 4. Demo Lab fixture — apply, verify, reset
./backend/.venv/bin/python tools/demo_lab/fixture_ct03_client_plane.py
./backend/.venv/bin/python tools/demo_lab/fixture_ct03_client_plane.py --verify
#    -> 32/32 checks pass (live backend + lab database)

# 5. Live security / authorization matrix
./backend/.venv/bin/python tools/demo_lab/verify_ct03_security_matrix.py
#    -> 46/46 checks pass

# 6. Browser verification (needs the lab frontend on :3000)
~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_ct03_client_plane_browser.py
#    -> 31/31 checks pass; screenshots in ~/ct_local_env/demo_lab/evidence/browser/

# 7. Manual pass — open http://localhost:3000/login and use the identities in §29
```

The migration was applied to the lab database with a small idempotent runner
(`psql -f supabase/migrations/20261103000000_ct_consultant_model_03_client_access_and_mode.sql`
against `carbontally_demo_local` on `127.0.0.1:54426`); it is additive and
re-runnable, so re-applying it is safe.

## 40. Change-set hygiene, Git state and residual limitations

* **Git state at the time of writing:** branch `p8-release-reconciled`, HEAD
  `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`. **Nothing was committed or pushed by
  this task** — the CT03 delta remains in the working tree alongside the CT02,
  CT-MP-SUB-003/004, FIN-06 and storage-management workstreams, which is why every
  CT03 hunk carries a change marker (§7).
* **No secret was introduced.** The new tooling reads the lab password, JWT
  secret, anon/service keys and any signed URLs from the existing lab state store
  **outside the repository** and never prints them; the browser verifier
  explicitly strips query strings from recorded URLs, because a console message
  can contain an `apikey` (AGENTS §78). No `.env`, credential, token or signed URL
  was written into the repository or into this report.
* **No unrelated change was absorbed.** Files outside the CT03 marker set were not
  edited, with two declared exceptions: the supersession in
  `tests/unit/api/test_ct_consultant_model_02.py` (§33), and one added test in
  `test_ct_consultant_model_03.py` (the fail-closed `approve_final` pin, §11).
* **No frozen UX was redesigned.** Plane C is a **new** surface on the ratified
  PO-8 path; D19 (workbench) and D21 (design system) were untouched, and the
  portal reuses the established semantic classes (`v3-btn`, `portal-*`).
* **No PO decision was silently changed.** Where a ratified rule could not be
  honoured without inventing policy, the implementation fails closed and the
  divergence is registered (§11 note ¹, §37, §38).
* **Residual limitations of this report.** (i) It is a *self*-verification: the
  evidence in §31–§34 was produced by the implementing agent, so the honest status
  is **LAB-VERIFIED (self) — NOT INDEPENDENTLY VERIFIED**; (ii) the browser pass
  exercises the three fixture client states plus the two pre-existing clients, not
  every profile × role × firm-configuration combination; (iii) the Plane C
  report/evidence pages do not exist yet (G-6), so those operations are proven at
  the API ceiling only; (iv) the Demo Lab Realtime WebSocket is unavailable, so
  realtime UI was not verified (G-8).

---

*End of report — 40 sections. Status: **IMPLEMENTED · TESTED · LAB-VERIFIED
(self) · NOT INDEPENDENTLY VERIFIED**. Awaiting independent QA and the PO
decisions PD-1 … PD-6.*

