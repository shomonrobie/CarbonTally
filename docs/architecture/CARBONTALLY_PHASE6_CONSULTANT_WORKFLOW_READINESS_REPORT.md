# CarbonTally Phase 6 — Consultant Workflow — Architecture & Pre-Implementation Readiness Report

- **Date:** 4 September 2026
- **Status of task:** Architecture/readiness review **only**. No code, schema,
  migration, RLS, API, UI, workflow, D38/D39/D40 or authorization was modified.
  No fixtures were created and no data was mutated (database inspection was
  read-only). Nothing was committed or pushed.
- **Authoritative architecture:** `CarbonTally Final Architecture Blueprint
  v1.2` (APPROVED — ARCHITECTURE FREEZE). Where implementation reports differ,
  the architecture wins.
- **Closed gates (not reopened):** Gate 3 (item-level effective assignment),
  Gate 4 (human provenance), Gate 5 (automated-extraction machine provenance),
  Gate 6 (human-after-automation attribution) — all PASSED/ACCEPTED.

---

## 1. Executive summary

CarbonTally already contains a substantial, ratified consultant foundation:
consultant profiles/firms, firm members with real permission flags, the
`consultant_clients` **active-grant** relationship (D15) with the D19 lifecycle
(active/suspended/ended), RLS helper `is_org_consultant`, a server-side
consultant authorization chain
(identity → firm → active client grant → resource → action), consultant
dashboard/client/report/evidence/document-upload surfaces under `/consultant`,
branding (D21), and a consultant messaging domain that already admits
consultants only through an active grant while PE participation stays denied.

Phase 6 therefore is **not** "invent a consultant system". Phase 6 is the
completion of the remaining consultant *workflow*: deciding the final
provisioning model, defining the consultant processing/action capability
surface on client-organisation work, clarifying the review/approval boundary,
and wiring conversations/notifications — all inside the existing authorization
and provenance model.

The architecture can be designed without weakening any frozen trust boundary,
but several product/business decisions must be ratified first
(§25). Verdict: **PHASE 6 DESIGN READY — PO RATIFICATION REQUIRED**.

## 2. Current consultant architecture

Per Blueprint v1.2 (§5.2, §13, §15, §23, §24) and the ratified AGENTS.md §10
consultant operating model:

- A **consultant is a professional organisation managing client organisations**
  (not an ordinary customer staff member; not a Processing Entity; not
  CarbonTally Operations).
- Consultant access is based on **active client relationships/grants**
  (`consultant_clients.status = 'active'`); relationship lifecycle is
  ACTIVE / SUSPENDED / ENDED (+ legacy `inactive`). Ending a relationship
  revokes access **without deleting** the organisation, customer data,
  provenance, history or processing records.
- Consultant authorization chain (server-side, mirrored in RLS):
  identity → consultant firm → active client grant → resource → action.
- Consultants access the `/consultant` surface; calculation snapshots and
  evidence are exposed **through the API** under the grant (never a direct
  Supabase path).
- Consultant ↔ customer communication follows the consultant-client access
  model; there is **no** PE↔consultant unrestricted or PE↔customer channel.
- One identity system, one database, one V3 domain, one authorization model,
  one D21 UI foundation — consultants do not get a parallel application.

## 3. Existing consultant implementation inventory

Implemented today (HEAD `1639121`, verified against code and the live schema):

| Component | Current state |
|---|---|
| `consultant_profiles` | Profile per user (company, D21 branding/white-label columns, partner fields, `api_key`/`webhook_url` columns present). RLS on. |
| `consultant_firm_members` | `role`, real permission flags `can_manage_clients` / `can_upload_documents` / `can_generate_reports` / `can_manage_team`, `client_access` shortcut, `is_active`, `role_id` + `permissions` JSON, invite/join stamps. RLS on. |
| `consultant_clients` | Firm↔organisation grant: `organization_id`, `status`, `billing_plan`, lifecycle provenance (`suspended_at`, `ended_at`, `ended_by`, `lifecycle_updated_at`), `created_by`. RLS on (8 policies). Live rows: 917 grants (demo); statuses `onboarding`/`active`/`inactive`. |
| `consultant_tasks` | Lightweight consultant task list (not the work-item pipeline). |
| `consultant_billing`, `consultant_custom_domains`, `consultant_senders` | White-label/partner supporting tables. |
| `user_invitations` | Org/role invitation table (`email`, `role_id`, `organization_id`, `token`, `status`, `expires_at`) — invitation infra Phase 6 provisioning can build on. |
| `api/consultant_auth.py` | `require_consultant`, `ensure_consultant_permission`, `ensure_consultant_revocation_authority` (WS6/SEC-0003: Owner/Admin/Manager), `ensure_consultant_org_access` (D15 active grant). |
| `api/v3_consultants.py` (1181 lines) | `/me` profile + branding, client CRUD + lifecycle (add/suspend/end/reactivate), `create_customer` (PO Decision 3 / CON-1: consultant creates a customer org with owner), team roster + add/deactivate/reactivate, tasks, dashboard, client context/dashboard/reports/documents (upload → **same** durable auto pipeline), processing items, evidence, processing status, issues. |
| Messaging (D39) | `conversations`/`messages`/`conversation_participants` with `conversation_kind`, org id, `processing_entity_id` (PE ops messaging), RLS consultant participation via active grant (documented in `domain/messaging.py`). |
| Notifications (D40) | `notifications` with `recipient_type`/`recipient_id`, `event_key` dedupe (`create_idempotent`), `actor_domain`; D38 assignment notifications use `work_item.assigned`. |
| RLS | `is_org_consultant(org)` helper exists; RLS on consultant/org tables; `consultant_clients` has 8 policies. |
| Work/assignment (D38) | `work_item_assignments` ledger (`assignee_kind`: internal_staff \| processing_entity) with effective assignment (item → batch default → unassigned); origins CARBONTALLY_INTERNAL \| PROCESSING_ENTITY. Consultants are not part of D38 today. |

**Not yet implemented:** consultant extraction/mapping/validation/calculation
processing actions, consultant review/QC participation, customer-approval
workflow interactions, a finalised invitation-based provisioning flow, and
consultant notification event producers. `POST /consultant/me` currently lets
any authenticated user create a consultant profile and `POST /me/team` can add
an arbitrary existing `user_id` — i.e., self-service provisioning remains
**not finalised** (Phase-4 decision: invitation/provisioning-based "for now").

## 4. Identity model

- One Supabase Auth identity set. `AuthUser` is the authenticated request
  principal; contexts are derived server-side: customer = `organization_members`
  (roles owner/admin/member/viewer); consultant = `consultant_profiles` +
  active `consultant_firm_members` row; PE = staff profile bound to a
  processing entity; Operations = internal staff profile with permissions.
- A user can hold multiple identities (e.g. an org member who is also a
  consultant firm member); each API family enforces its own context dependency
  (`require_org_*`, `require_consultant`, `require_staff`, `require_pe_member`),
  so role families never cross-grant.
- `user_invitations` is the existing email/token/role invitation mechanism.


## 5. Consultant ↔ organisation relationship

**Q1/Q2 findings.** The architecture already answers the core question: a
consultant is an external professional organisation (firm) that works for
customer organisations **without becoming a customer staff member**. The
durable relationship is the **`consultant_clients` grant row** between the firm
(`consultant_profiles.id`) and the customer organisation
(`organization_id`), whose **only access-bearing state is `active`** (D15/D19).
This is the smallest durable relationship that exists and should be reused —
not a new "engagement" abstraction. `consultant_firm_members` define which
individual identities of the firm may act and with which `can_*` permission
flags; `consultant_clients.created_by` + lifecycle columns give relationship
provenance. Ending (`ended`) revokes access but preserves the org, data and
history (Blueprint §5.2).

**PO decision required (provisioning finalisation):** today any authenticated
user can self-create a profile and a `manage_team` member can add arbitrary
user ids without an invitation token. The ratified intent is
invitation/provisioning-based. Decide the exact flow (see §25, D-1).

## 6. Multi-organization behaviour

**Q3.** Yes — one consultant firm identity can work Organisation A, B, C
without leakage: the firm holds one `consultant_clients` row per organisation,
and every consultant action re-authorizes against **that** organisation via
`ensure_consultant_org_access` (or `_authorized_client_org` on the client
workspace) which requires an **active** grant for the specific org id supplied
by the client. RLS (`is_org_consultant(org)`) mirrors the same chain. Context
selection is per-request (`client_id`/`organization_id`), never a global
"active workspace" stored client-side as an authorization signal.

## 7. Consultant capability matrix (current implementation vs decision)

`Y`=implemented/available, `R`=proposed-to-ratify, `—`=not applicable,
`DECISION REQUIRED` where the architecture is silent.

| Capability | Customer User | Consultant | Ops | PE |
|---|---:|---:|---:|---:|
| View own/authorized organisation data | owner/admin | Y (active grant, API) | Y | assigned work |
| Upload documents | owner/admin/member | Y (`can_upload_documents`) | Y | Y (entity workspaces) |
| Enqueue automatic processing | via upload | Y (via upload, same pipeline) | Y | — |
| Extract / Map / Validate / Calculate (manual) | — | DECISION REQUIRED (D-3) | Y | Y (assigned) |
| Review (internal) | — | DECISION REQUIRED (D-3) | Y | PE review gate only |
| QC | — | R: no | Y | no (PE QC internal to PE) |
| Customer approval | owner/admin only | R: no (prepare/submit only, D-4) | no (org owner/admin only) | no |
| Assign PE / manage assignments | — | R: no | Y | no |
| Manage users/roles | owner/admin (org staff) | R: no (team only) | Staff Admin | no |
| View billing/subscription | owner/admin | DECISION REQUIRED (D-7) | Y | config |
| Conversations | org-scoped | active-grant org conversations (D39) | ops | ops-only (PE↔Ops) |
| Reports / evidence / exports | owner/admin (+viewer read) | Y (`can_generate_reports`; evidence API) | Y | scoped |

Do not treat the `R`/`DECISION REQUIRED` cells as implemented permissions; they
are the Phase-6 ratification surface (§25).

## 8. Consultant ↔ work / assignment model (D38)

D38 stays authoritative for **internal_staff | processing_entity** assignment.
Consultants are not currently an `assignee_kind` and the effective-assignment
rule (item → batch default → unassigned) is PE/Operations-centric.

Analysed options:

- **Model A (org-scoped full work access):** simplest, but risks consultant
  access equating to broad org operations access — rejected as too broad.
- **Model B (D38 item/batch assignments for consultants):** highest control but
  requires extending `assignee_kind`, the assignment ledger, queues and the
  effective-assignment view; heavier and partially redundant with the
  org-level grant.
- **Model C (org engagement scope + action/resource restrictions):**
  **proposed.** Active client grant = the org-scoped engagement; per-action
  `can_*` flags + item status/stage rules = the restrictions. Consultants act
  on client-organisation work (org-owned items/batches) through consultant
  workspaces that reuse the manual-extraction item surface, while D38/PE
  assignment continues to govern PE work.
- **Model D:** other — none more architecture-consistent found.

**PO decision required (D-2):** ratify Model C (or B) — including whether a
consultant may operate an item currently assigned to a Processing Entity
(proposal: no — the item stays PE-owned until the assignment closes/expires;
recommended conflict rule, D-2b).


## 9. Consultant ↔ PE boundary

The distinction is absolute and enforced today: consultant identity lives in
`consultant_profiles`/`consultant_firm_members`; PE identity lives in staff
profiles bound to `processing_entities`. There is **no** shared permission
column and **no** shared endpoint dependency between the two contexts.
Verified invariants for Phase 6: consultant permissions cannot satisfy
`require_pe_member`; PE users cannot obtain consultant grants without a
consultant profile/firm membership; consultant endpoints never expose
PE-only resources; consultants never appear as PE actors; consultant actions
cannot bypass PE assignment controls (see §8 conflict rule).

## 10. Consultant ↔ CarbonTally Operations boundary

Consultants must not inherit Operations privileges. Existing separation:
Operations staff resolve through `require_staff`/`operations_auth` and the ops
routers; consultants resolve through `require_consultant` and the consultant
routers. For Phase 6, consultant processing actions must NOT flow through the
ops routers/permission model; they need a consultant-scoped surface that shares
the underlying engines/repositories but enforces the consultant grant chain.
Explicitly out of consultant scope (proposal): internal assignment/reassignment,
PE assignment/management, CT QC, staff/role administration, customer org
administration, and Org-level user management.

## 11. Customer approval boundary

Current implementation: customer review/approval on automatic jobs is
`require_org_admin` (org owner/admin) — a consultant holding only a client
grant is not an org admin and therefore cannot approve today (correct).
Proposal to ratify (D-4): consultants may **prepare / review / recommend /
submit** work for customer review but may **never** perform the customer's final
approval; approval remains exclusively org owner/admin (with CarbonTally
internal staff operational override unchanged).


## 12. Consultant processing capabilities

Consultants today upload client documents that enter the **same** durable
automatic pipeline as customer uploads (extraction → mapping → validation →
calculation → review). Manual processing action endpoints (extract/map/
validate/calculate) do **not** exist for consultants yet.

Proposal (D-3): when ratified, consultants use the **existing processing
engines/repositories** behind a consultant-scoped surface (active grant + new
per-action `can_*` flags). The deterministic calculation engine stays
authoritative; AI stays non-authoritative; **no** consultant-specific
calculation logic is created. Stages a consultant may drive (extract → map →
validate → calculate → submit-for-review) and stages that remain
CarbonTally/org-controlled (final approval; CT QC) are part of the decision.

## 13. Consultant provenance model

Consultant actions are **human actions** in the existing provenance chain:

**Source Document → Work Item → Automated Execution → Automated Output →
Human Consultant Action → Validation → Calculation → Snapshot → Review/QC →
Customer Approval**

Reuse, do not replace: Gate-4 item actor columns + item audit events
(`ops_*/pe_*` analogues become `consultant_extract/map/validate/calculate` with
the consultant **user id** as actor and the firm/grant context in the event),
Gate-5 write-once `automation_*`/`automation_extracted_data` (never touched by
consultant edits), Gate-6 human-gate audit events and the G6-D correction
safeguards. Consultant provenance must record: actual consultant identity,
organisation/engagement context (client grant + org), resource/work item,
action, timestamp — no new provenance subsystem.

## 14. Consultant and automation

Verification requirement (same guarantees as Gate 6 for any human): consultant
corrections cannot overwrite `automation_extracted_data`; Gate-5
provider/model/version remain immutable (write-once trigger); consultant edits
are human provenance (never `automatic_pipeline`); stale resume markers cannot
bypass required recalculation (G6-D invalidation + data-digest snapshot ids);
consultant corrections flow through the same confirm/resume gates. No new work
is needed beyond giving consultant actions the same repository paths.

## 15. Consultant and PE workflow

Allowed/forbidden matrix (proposal to ratify where marked):

| Scenario | Rule |
|---|---|
| Consultant prepares → PE processes | Allow only if the item is NOT already PE-assigned; PE takes over from a clean/unassigned state. |
| PE processes → Consultant reviews | **PO decision (D-5):** recommend NO while the item is PE-assigned; the consultant reviews only after PE closes the assignment / CT release. |
| Consultant reviews → CarbonTally QC | Allow (CT QC stays the internal gate). |
| Consultant prepares → internal CarbonTally processing | Allow via shared engines under the consultant grant. |
| Consultant works on a PE-assigned item | **Forbidden** (proposed conflict rule §8/D-2b) — consultants cannot override D38 assignment ownership. |

## 16. Consultant conversations — D39

D39 infrastructure is reusable and already knows the consultant rule
(`domain/messaging.py`): org members participate; consultants participate only
through an ACTIVE `consultant_clients` grant for that org; PE staff never
participate in org/customer conversations (PE↔Ops only). Minimum Phase 6 model
(proposal): org/work-item/issue conversations between the consultant firm
(active grant) and the customer org members / CarbonTally support — no
consultant↔PE channel, no cross-org conversations, no customer-bypass channel.
Authorisation = participation + active grant + org RLS (existing storey).
Confirm whether a separate `conversation_kind` (e.g. `consultant_org`) is
desired or the org conversation kind suffices (D-6).

## 17. Consultant notifications — D40

D40 infrastructure is reusable as-is: `notifications` are per-recipient
(`recipient_type='user'`, `recipient_id` = user id) with `event_key`
idempotency and `actor_domain`. Phase 6 should produce consultant events only
through this repository. Candidate event set (authorisation design only, no
implementation): work/engagement assigned or requested, document/work status
change, review/submission request, customer feedback, completion, and
consultant-scoped issue/message notifications. Targets are the consultant
member user ids within an active grant context. Exact event vocabulary requires
ratification (D-6b) but no schema work is expected (event keys are free-form).

## 18. Billing / subscription / credits

Current state: `consultant_clients.billing_plan`/`billing_cycle` (display) and a
`consultant_billing` table exist; organisations carry `billing_mode`/
`subscription_*`/credit semantics. The architecture does **not** define whether
consultant processing consumes the client organisation's subscription/credits,
the firm's own plan (`consultant_billing`), or CarbonTally credits. This is a
business decision (**D-7**) — do not invent a billing model. Recommendation for
ratification: Phase 6 processing rides the client organisation's engagement
(credits/billing owned by the customer organisation, with the consultant firm
relationship recorded on the grant), while firm-level commercial terms remain a
CarbonTally↔firm matter managed internally via `consultant_billing`.


## 19. Security threat model (consultant-specific)

| Risk | Existing control | Missing / proposed control | Action |
|---|---|---|---|
| Cross-org data access | Active-grant org check (`ensure_consultant_org_access`) + `is_org_consultant` RLS | None | Implementation (keep) |
| Consultant-to-consultant isolation | Per-firm `consultant_profiles.id` scoping; firm-owned rows | Verify every new endpoint scopes by context.profile.id | Implementation |
| Consultant↔PE boundary | No shared role/permission; distinct dependencies | Conflict rule (§8/D-2b); never route consultant through PE paths | Implementation |
| Consultant↔Ops boundary | `require_consultant` vs `require_staff` separation | Consultant surface must not reuse ops routers | Implementation |
| Customer approval bypass | `require_org_admin` on approval; consultant is not an org admin | Ratify D-4 (never approve); test negatives | PO + tests |
| Assignment bypass | D38 ledger internal/PE only | PE-assigned items forbidden to consultants (D-2b) | PO + implementation |
| Document access | Grant-scoped storage path + API re-auth on upload/read | Consultant read of client documents must use same authorized read path (verify) | Implementation |
| API IDOR | `_checked_client`/`_authorized_client_org` (404 cross-firm) | Keep for every new client-scoped route | Implementation |
| Direct DB/RLS access | RLS on consultant tables; `is_org_consultant` | Blueprint: snapshot access via API only — keep | Implementation (audit) |
| Actor impersonation | Actor from `current_user`/`context` only | No client-supplied actor anywhere | Implementation |
| Stale authorization | `status='active'` enforced at request time; `is_active` member check | Lifecycle transitions must not leave cached sessions | Implementation |
| Conversation leakage | Participation + org/consultant RLS storey | No consultant↔PE conversation; kind rules (D-6) | PO + implementation |
| Notification leakage | Per-recipient notifications; event_key dedupe | Producer must target only members inside the grant | Implementation |
| Report/evidence/export leakage | Grant-scoped report/evidence endpoints | New export paths grant-scoped | Implementation |

## 20. Data / RLS implications

- The consultant trust surface is already RLS-backed
  (`consultant_profiles` RLS=1, `consultant_firm_members` RLS=2,
  `consultant_clients` RLS=8, `is_org_consultant` function present).
- Phase 6 should **reuse** these storeys. New RLS is only justified if the new
  capability requires item/batch-level consultant visibility — under Model C
  the existing org+grant RLS already covers org-scoped reads; processing writes
  go through server-authorised endpoints.
- No RLS weakening is required or proposed.

## 21. API implications

- New consultant-scoped routes under `/api/v3/consultants/...` (processing
  actions, submit-for-review, notifications) guarded by
  `require_consultant` + `ensure_consultant_permission` +
  `ensure_consultant_org_access`.
- Reuse existing repos/engines; no new authorization vocabulary. Provenance
  actor = consultant user id (+ firm/client context in audit `changed_fields`).

## 22. UI implications

- `/consultant` client workspace gains processing views consistent with D19/D21
  (queue → focused work area), using the same item/evidence contracts.
- No new application; the customer `/app` and ops surfaces remain unchanged.
- Route/hostname is not a security boundary (server-side checks remain).

## 23. Required database changes, if any

Likely **additive and minimal** after ratification:
- Optional new `can_*` permission columns on `consultant_firm_members` for
  processing actions if D-3 ratifies capability flags (or reuse `permissions`
  JSON) — schema decision at implementation time.
- Optional `conversation_kind` extension if D-6 requires a consultant kind.
- No new trust tables: `consultant_clients` remains the relationship.

## 24. Required migrations, if any

None required for design readiness. If ratifications add columns/kinds, each is
a small additive migration following the established convention (main +
`carbontally_test`, idempotent, RLS unchanged unless justified, no backfill,
baseline verification).

## 25. Open architecture / business decisions

**D-1 Provisioning:** final invitation/provisioning flow for consultant
profiles & firm members (replace/guard current open `POST /me` and

## 26. Proposed minimal implementation plan

1. Ratify decisions D-1…D-7 (PO package, no code).
2. Implement the consultant authorization contract additions (D-3 flags /
   Model C guards + PE-conflict rule) with negative tests.
3. Implement consultant processing actions reusing the shared engines with
   full Gate-4/5/6 provenance guarantees.
4. Implement submit-for-review and the approval-boundary guards (D-4).
5. Wire D39 conversations and D40 notifications for consultants.
6. Add the `/consultant` UI processing views (D19/D21), then run the Phase 6
   E2E/security acceptance matrix (including the negative cross-boundary
   cases from §19).

## 27. Proposed Phase 6 workstreams

Each workstream has objective/scope/dependencies/security invariants/tests/
acceptance/stop:

- **P6-0 Decision ratification package** — collate D-1…D-7 into a PO
  ratification brief. Stop: all decisions ratified (or scoped out).
- **P6-1 Consultant provisioning/invitation** (D-1) — invite-based profile/
  member creation, `can_*` flag administration, expiry/revocation; additive
  schema only if required. Depends: P6-0. Security: no arbitrary
  self-provisioning grants; no cross-firm. Tests: invitation accept/deny,
  revocation immediate. Stop: provisioning matrix green.
- **P6-2 Consultant authorization contract** (D-2, D-3, D-2b) — Model C scope
  resolution, permission flags, PE-assigned-item conflict rule, provenance
  actor model. Depends: P6-1. Security: cross-org/PE/Ops negatives. Stop:
  negative matrix green.
- **P6-3 Consultant processing actions** — extract/map/validate/calculate
  (per ratified set) via shared engines; confirm/resume; G6-A/B/C/D safeguards.
  Depends: P6-2. Stop: processing + provenance acceptance per scenario.
- **P6-4 Submit/review boundary** (D-4) — prepare/recommend/submit; final
  approval remains org owner/admin. Depends: P6-3. Stop: approval-boundary
  negatives green.
- **P6-5 Consultant conversations + notifications** (D-6/D-6b) — D39/D40 reuse.
  Depends: P6-2. Stop: conversation/notification authorization green.
- **P6-6 Consultant UI + E2E security acceptance** — `/consultant` processing
  views (D19/D21) + full persona matrix incl. §19 threats. Depends: P6-3…P6-5.
  Stop: acceptance report; no Phase 6 work continues beyond defined scope.

## 28. Test strategy

- Unit/API: authorization positives/negatives for every new consultant route
  (active grant, suspended/ended grant, cross-firm, PE user, internal staff,
  unauth), permission-flag gating, PE-assigned-item conflict, provenance event
  shape (consultant user actor), G6 invariants on consultant edits.
- Workflow: real-stack fixture scenarios (consultant upload → auto pipeline →
  consultant correct → recalc → customer approval denied to consultant) with
  baseline restore.
- Security: full §19 negative matrix incl. IDOR, actor injection, conversation/
  notification leakage.
- Regression: automatic processing, manual extraction, D38, D39, D40,
  Gate-4/5/6 suites on the affected code paths.

## 29. Rollback / data-safety considerations

- Every P6 workstream ships behind additive schema (if any) and additive API
  routes; no destructive migration; no data backfill or fabrication; no
  weakening of existing RLS/guards.
- All consultant actions reuse the append-only audit trail and write-once
  machine-provenance columns, so no Phase-6 feature can alter historical
  provenance. Fixture-based acceptance cleans up only what it created and
  verifies exact baselines.

## 30. Final readiness verdict

**PHASE 6 DESIGN READY — PO RATIFICATION REQUIRED**

The consultant architecture is largely present and ratified (identity, firm,
active client grant, D19 lifecycle, RLS, authorization chain, workspace,
messaging domain). The remaining Phase-6 workflow can be designed and built
inside that architecture without weakening any frozen trust boundary. Safe
design and implementation require ratification of the explicit decisions in
§25 (D-1…D-7), none of which is an implementation guess.

**Recommended first bounded workstream:** P6-0 (decision ratification package),
followed by P6-2 (consultant authorization contract) once D-1…D-3 are
ratified — because the authorization contract is the dependency for every
processing/provenance/conversation/notification workstream.

---

*End of report. Read-only task — no code, schema, RLS, API, UI or data was
changed; no fixtures created; nothing committed or pushed.*

`POST /me/team`), who sets `can_*` flags, and how invitations expire.
**D-2 Work-access model:** ratify Model C (org engagement + action/resource
restrictions) vs Model B (D38 assignments); D-2b PE-assigned-item conflict rule.
**D-3 Processing capability set:** which consultant actions (extract/map/
validate/calculate/review/submit) exist and their permission flags.
**D-4 Approval boundary:** consultants never perform final customer approval.
**D-5 PE→Consultant review ordering** and the PE/consultant hand-off rules.
**D-6 Conversation kind + D-6b notification event vocabulary for consultants.**
**D-7 Billing/credit ownership** for consultant-performed processing.

