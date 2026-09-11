# CarbonTally Phase 5 — D38 / D39 / D40 Pre-Implementation Audit & Implementation Plan

- **Phase:** 5 — D38 / D39 / D40
- **Nature:** PRE-IMPLEMENTATION AUDIT AND DESIGN/PLANNING GATE — no
  implementation performed, no migration, no code change.
- **Date:** 2 September 2026
- **Governing architecture:** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.2.md`
  (frozen, complete). Phase 4 approved **OPTION A — no personal workspace**.
- **Status:** `PHASE 5 PRE-IMPLEMENTATION DESIGN COMPLETE — AWAITING PRODUCT
  OWNER APPROVAL`

Every section is labelled **CURRENT FACT**, **PROPOSED DESIGN**, or
**PRODUCT OWNER DECISION REQUIRED**.

---

## 1. Executive Summary

Phase 5 targets three decision-registered capabilities whose definitions are
established with high confidence from the consolidated Product Decision
Register, the V3 Architectural Decisions Register (ADR-V3-005), and the frozen
N1 / PE-MSG-001 decisions:

- **D38 — Assignment / reassignment attribution (ADR-V3-005).** Reuse
  `review_assignment_history` as the single attribution mechanism, reconcile
  dormant `reassignment_history` / `processing_assignments` before retirement,
  and record D22 (batch assignment) through the V3 `audit_trail`. Status:
  **PARTIAL** (D22 batch-assignment audit implemented; canonical per-item
  claim/assign/reassign/complete WorkItem layer and entity-scoped reassignment
  attribution are missing).
- **D39 — Messaging boundaries (N1; V1.2 PE-MSG-001).** Org-scoped customer /
  consultant / CarbonTally-support messaging is implemented with strict
  server-side actor authorization. **Entity-scoped PE ↔ CarbonTally
  operational messaging is NOT implemented** (no `entity_id` on
  `conversations`, no PE participant authorization, no RLS, no PE surface; PE
  is correctly denied 403 today). V1.2 froze PE-MSG-001 ("PE may communicate
  with CarbonTally Operations through controlled, auditable,
  work-item/issue-scoped messaging"), so the capability is decided at policy
  level while the concrete data/authorization/UX model is open.
- **D40 — Notifications.** Recipient-scoped notifications with mark-read /
  read-all and Realtime delivery exist (generic `recipient_type` /
  `recipient_id`). Status: **PARTIAL** — the notification surface is not yet
  wired for Processing Entity members (PEShell has no notification entry
  point), and event-driven creation is limited (document-processing events
  today; assignment / messaging events not yet integrated).

Recommended implementation order (foundations first): **WS1 attribution audit
→ WS2 entity operational messaging (D39) → WS3 notification completion (D40)
→ WS4 PE-surface & UI integration → WS5 tests/reporting**, each gated on the
PO decisions in §20. No personal workspace, no user-owned data, no billing
change is required by any D38/D39/D40 capability.

## 2. Source Authority Matrix

| Source | Authority | Relevant D38/D39/D40 content |
|---|---|---|
| `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` | **AUTHORITATIVE** (L3/L4 consolidated decision register) | D38 = Assignment/reassignment attribution (ADR-V3-005); D39 = Messaging boundaries (N1, APPROVED/FROZEN; entity-scoped PE messaging implementation open); D40 = Notifications (recipient-scoped; mark-read/read-all; Realtime). |
| `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` | **AUTHORITATIVE** (L3) | ADR-V3-005 Assignment & Reassignment — PROVISIONALLY DECIDED: reuse `review_assignment_history`; reconcile dormant `reassignment_history`/`processing_assignments`; DB none; Backend/API EXTEND. |
| `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.2.md` | **AUTHORITATIVE** (L1) | No D38/D39/D40 numbering; freezes N1 messaging boundaries and **PE-MSG-001** (PE ↔ CarbonTally operational, work/issue-scoped, auditable messaging). Governs all Phase-5 architecture. |
| `AGENTS.md` §28 (N1 messaging) / §42 retention / §45 security testing | **AUTHORITATIVE** (L1) | Messaging boundaries (Customer internal/support; Consultant internal/support/active-client; PE operational CarbonTally; no Customer↔PE); server-enforced; UI never the boundary. |
| `docs/cline/CARBONTALLY_PE_MESSAGING_PO_DECISION.md` | **SUPPORTING** (decision-history; superseded in part by V1.2 PE-MSG-001 freeze) | Documents current org-scoped messaging, PE-denied 403, absence of `entity_id` conversations, and the minimum compliant entity-scoped PE messaging design (if approved). |
| `docs/audit/cline/CARBONTALLY_V3_D20_D37_RELEASE_*`, `CARBONTALLY_V3_PUBLIC_WEBSITE_AND_ARCHITECTURE_AUDIT.md`, `CARBONTALLY_V3_MASTER_COMPLETION_SECURITY_HARDENING_REPORT.md` | **HISTORICAL / SUPERSEDED for numbering** | These use "D38" loosely as the *post-D37 phase* (public website & commercial readiness). That usage is not the decision-register D38 (assignment attribution). Its concrete items (public site, legal/pricing coherence, invitation acceptance, payment-provider adapter, legacy-surface retirement, workspace switching) are outside the Phase-5 D38/D39/D40 scope and must not be silently imported. |
| `docs/cline/CarbonTally_Backend_V3_Migration_Plan_v1.0.md` | **SUPPORTING** (historical migration plan) | ADR-V3-005 attribution reused via `review_assignment_history`; dormant `processing_assignments` retirement deferred; canonical WorkItem service (ADR-V3-003/011) listed MISSING — queue views + assign/reassign/complete/return writing `entity_id` + append-only history. |
| Implementation (backend `api/*`, `data/*`, `domain/*`; `frontend/src/v3/*`; Supabase migrations; live DB) | **AUTHORITATIVE** (current runtime truth) | Inventories in §4 and the gap tables. |
| `qa_harness/reports/latest/*` | **SUPPORTING** | No D38/D39/D40 redefinition found; used only as backlog context. |
EOF
## 3. D38 / D39 / D40 Definition (CURRENT FACT + PROPOSED DESIGN)

**D38 — Assignment / reassignment attribution (PROVISIONALLY DECIDED — ADR-V3-005).**

- Reuse `review_assignment_history` as the single attribution record
  (`assigned_by`, `assigned_to`, `previous_assigned_to`, `action`, `note`).
- Reconcile dormant `reassignment_history` / `processing_assignments` before
  retirement (do not delete history; formalise read-only/retirement state).
- D22 batch assignment records attribution through V3 `audit_trail`
  (append-only, immutable).
- Intended Phase-5 outcome: per-item assignment/claim/reassign/complete with
  **never-erased attribution** across CarbonTally-internal and PE processing,
  including partial-work recovery attribution (worker/entity failure).

**D39 — Messaging boundaries (APPROVED/FROZEN at policy level; implementation
partial).**

- N1 boundaries: Customer = internal/support messaging; Consultant =
  internal/support/authorised active-client messaging; CarbonTally =
  authorised support/admin messaging; **PE = operational CarbonTally
  messaging**. No unrestricted Customer ↔ PE; UI is never the boundary;
  server-enforced. PE-MSG-001 (V1.2): controlled, auditable,
  work-item/issue-scoped PE ↔ CarbonTally Operations messaging.
- Intended Phase-5 outcome: entity-scoped PE operational messaging model
  (own entity only), internal CarbonTally support participation, other PEs /
  customers / consultants denied, work-item/issue context optional, Realtime
  delivery, audit trail.

**D40 — Notifications (CURRENT implementation, partial coverage).**

- Recipient-scoped notifications (`recipient_type`/`recipient_id`);
  mark-read / read-all; Realtime delivery; pagination.
- Intended Phase-5 outcome: complete recipient coverage across all approved
  actor domains (customer, consultant, PE, internal), event-driven creation
  for assignment/messaging events, and a PE-appropriate notification entry
  inside the PEShell.

**Numbering ambiguity note (CURRENT FACT):** several pre-V1.2 Cline reports use
"D38" to mean the generic *post-D37 release-readiness phase* (public website &
commercial readiness). That usage is **SUPERSEDED for Phase-5 numbering**; the
decision register + ADR-V3-005 definitions above are authoritative. This
ambiguity does not block Phase 5 because both the definitions and the
implementation targets are established from authoritative registers.

## 4. Current Implementation Inventory (CURRENT FACT)

### D38 — Assignment / reassignment attribution

| Element | Status | Evidence |
|---|---|---|
| D22 batch assignment to PE/operator + V3 audit_trail record | **Implemented** | `POST /api/v3/ops/batches/{batch_id}/assign` (v3_operations.py:1794); `_record_batch_assignment_audit` writes append-only audit_trail with before/after assignment. |
| `review_assignment_history` table + legacy admin routes (`routes/admin/assignments.py`, `/api/v3/ops/review/{review_id}/assign`) | **Implemented (legacy, staff-centric)** | Table carries review_id/assigned_by/assigned_to/previous_assigned_to/action/note; legacy routes use it. |
| Canonical V3 WorkItem service (ADR-V3-003/011) — claim/assign/reassign/complete/return per item with `entity_id` + append-only history | **Missing** | Migration-plan inventory lists `services/work_items.py` as absent; ops operates on batches/items directly without a unified WorkItem queue layer. |
| Entity-scoped item reassignment with attribution + partial-work recovery | **Missing** | No entity-scoped item-level reassign endpoint; no `entity_id` on `review_assignment_history`. |
| Dormant `processing_assignments` / `reassignment_history` / `staff_workload` | **Present (dormant/legacy)** | Tables exist; retirement deferred per ADR-V3-016; not used by V3 ops. |

### D39 — Messaging boundaries

| Element | Status | Evidence |
|---|---|---|
| Org-scoped conversations (`organization_id`) + participants + messages + Realtime | **Implemented** | `conversations`, `conversation_participants`, `messages` tables; `v3_messaging.py` endpoints (create/list/messages/send/read); `_authorize_org_actor`; `useConversationRealtime`. |
| Customer workspace messaging (/messaging) + consultant Client messages tab + ops support tab | **Implemented** | `MessagingPage.jsx`, `ClientMessagingTab.jsx`, `OpsMessagingTab.jsx`. |
| PE denied on org messaging (403) | **Implemented (correct)** | `_authorize_org_actor` has no PE participant path; PE staff/managers receive 403. |
| Entity-scoped conversations (`entity_id` / processing_entity scope) | **Missing** | `conversations` has no entity/processing_entity column; no participant model for PE. |
| PE ↔ CarbonTally operational messaging UI in PE workspace | **Missing** | PEShell (/pe) has no messaging entry point. |
| Work-item/issue-scoped thread context (PE-MSG-001) | **Missing** | No thread ↔ batch/item/issue linkage model. |

### D40 — Notifications

| Element | Status | Evidence |
|---|---|---|
| `notifications` table + recipient model | **Implemented** | `recipient_type`, `recipient_id`, read/dismiss state, metadata, link. |
| List / mark-read / read-all API + pagination | **Implemented** | `v3_notifications.py` (GET "", POST /{id}/read, POST /read-all); `data/notifications.py` (create/list/count). |
| Realtime delivery & frontend bell (customer/consultant/staff shells) | **Implemented (partial surfaces)** | NotificationsPage + useNotifications hook in V3Layout surfaces. |
| Event-driven creation | **Partial** | Creation callers exist (document_processing events); assignment/messaging event notifications not wired. |
| PE recipient surface (PEShell entry point) | **Missing** | PE staff routed to /pe (PEShell) which has no notifications bell/entry. |

## 5. Actor Mapping (per capability — CURRENT FACT / PROPOSED DESIGN)

| Capability | Customer | Consultant | Processing Entity | CarbonTally Operations | CarbonTally Admin |
|---|---|---|---|---|---|
| D38 assignment attribution | Owner/admin approve; members view status | Views client processing status (permitted reports/queues) | PE manager/staff see own-entity assignments; operators claim/process own items | Internal operators/reviewers assign/reassign; attribution always preserved | System/admin audit visibility only |
| D39 messaging | Internal/support messaging per org; never direct-to-PE | Internal/support + authorised active-client messaging | **PE ↔ CarbonTally operational only (own entity)** — proposed | Support/admin participation in org + (proposed) PE operational threads | Support/admin participation |
| D40 notifications | Recipients: org members for events on their org | Firm members for client/firm events | **PE members for own-entity events** — proposed | Internal staff for queue/assignment events | Internal staff + admin events |

## 6. Workspace Mapping (CURRENT FACT / PROPOSED DESIGN)

| Capability | /app·/home | /consultant | /pe (PEShell) | /ops | /admin |
|---|---|---|---|---|---|
| D38 | Status visibility on processing/review pages (read) | Client status (read) | **Assignment/queue visibility + reassign attribution (read)** | Assign/claim/reassign actions + audit | Audit console |
| D39 | Org messaging | Client messages | **PE operational messaging entry (proposed)** | OpsMessagingTab (support) + PE-thread participation | N/A (support via ops) |
| D40 | Bell + list | Bell + list | **PE notifications entry (proposed)** | Bell + list | Bell (internal) |

No new shell is required: D39/D40 PE surfaces must be added **inside the
dedicated PEShell**; no personal shell is introduced.

## 7. Ownership Mapping (CURRENT FACT / PROPOSED DESIGN)

| Capability | Owning entity | org_id | PE assignment | user-owned | Audit |
|---|---|---|---|---|---|
| D38 attribution | Organisation work (batches/items) + PE assignment | Yes (batch→org; audit_trail org context) | `batch.entity_id` + immutable item `processing_entity_id` | No | review_assignment_history + audit_trail (append-only) |
| D39 org messaging | Organisation conversations | Yes | No | No (participants are members; conversation org-owned) | Read/audit log, timestamps |
| D39 PE operational messaging (proposed) | Entity-scoped threads | Not required (entity-scope) | `entity_id` carrier (proposed) | No | Append-only audit + participant join/leave history |
| D40 notifications | Recipient rows | Where event is org-scoped, metadata carries org | PE events carry entity | No (recipient scoping, not ownership of business data) | Notification lifecycle + originating event |

**Constraint (CURRENT FACT):** none of D38/D39/D40 requires user-owned
business data. All fit the organisation / entity-assignment / firm ownership
model. Notifications and messaging are *conversation/recipient scoping*, not
new ownership of emissions data.

## 8. Security Analysis (PROPOSED DESIGN — must hold for any implementation)

Security chain must be preserved for every capability:

```text
Frontend → API → Authentication → Actor resolution → Workspace resolution →
Authorization → Scoped data / RLS
```

| Attack vector | D38 | D39 | D40 |
|---|---|---|---|
| Cross-org access | Deny: attribution rows resolved via batch→org + staff/org guards | Deny: `_authorize_org_actor` | Deny: recipient = resolved actor |
| Cross-consultant-client | Deny: client grant checks | Deny (unchanged N1) | Deny: recipient scoping |
| Cross-PE (PE A ↔ PE B) | Deny: entity-scope guards | **Deny: proposed entity conversations are own-entity-only** | Deny: entity-scoped recipient |
| PE → customer | Deny (unchanged) | **Deny: PE operational threads exclude customers** | n/a |
| Customer → PE controls | Deny (unchanged) | Deny | n/a |
| Consultant → customer ownership | Deny (consultant never owner; D38 adds status only) | Deny (client messaging ≠ ownership) | Deny |
| Staff → customer boundaries | Deny except authorised ops review | Support threads only | Deny except authorised events |
| Admin privilege boundary | System-admin audit read only | Support/admin only | Admin events only |
| IDOR via URL/params / forged org or entity id | Guard on resolved actor + resource org/entity (never trust URL) | Guard on conversation scope + participant | Guard on recipient id |
| Frontend-only authorization | Rejected (server guards remain) | Rejected (server guards remain) | Rejected |
| user metadata manipulation | No effect (never read) | No effect | No effect |

Negative test matrix required at implementation time: Customer A↔B; Client A↔B;
Consultant A↔B; PE A↔PE B; PE→customer thread; customer→PE thread; staff→org
beyond support; admin boundary; forged conversation/notification/assignment IDs.

## 9. Individual-User Impact Analysis (CURRENT FACT / PROPOSED DESIGN)

Phase 4 approved **OPTION A — no personal workspace**. Audit of D38/D39/D40:

- **D38** creates *attribution on organisation-owned work* — no user-owned
  data. PE assignment is entity assignment of customer-org work, already
  modelled.
- **D39** creates *entity-scoped operational conversations* — a conversation
  container with PE↔CarbonTally participants, not a user-owned data store.
  This is consistent with N1/PE-MSG-001 and does **not** create a personal
  workspace, personal documents/emissions/reports, or user-owned credits.
- **D40** notification rows are recipient-scoped lifecycle records, not
  business data ownership.
- **`users.user_type` remains untouched** and is not reused as an
  authorization signal in any D38/D39/D40 proposal.

No D38/D39/D40 requirement is blocked by the Phase 4 decision, and none
requires a new actor domain.

## 10. Database Impact (PROPOSED DESIGN — no migrations yet)

| Capability | Schema classification | Notes |
|---|---|---|
| D38 (batch assignment audit + history attribution) | **A — no schema change** for batch assignment (audit_trail exists). Item-level entity reassignment may need **B** (additive `entity_id` on `review_assignment_history` or a scoped view) — B only. | Dormant tables reconciled/retired without deletion; history preserved. |
| D39 entity operational messaging | **B/C depending on model.** Either (B) additive nullable `processing_entity_id` (+ participant/scope columns, indexes, RLS) on the existing conversation family, or (C) a separate entity-conversation table family. **C requires PO decision + security review.** | Org-scoped messaging RLS untouched. No nullable-owner ambiguity: entity scope is NOT a user-owner. |
| D40 notifications | **B (additive, low)** — possible `entity_id` context/metadata or recipient-type additions + indexes. Existing generic recipient model may already suffice. | No new ownership model. |
| Global redesign / ownership model change | **E — not proposed.** | No D/E classification items without PO approval. |

Nullable-ownership risk: any additive scope column must be part of a
NOT-NULL-safe policy family (scoped rows have exactly one scope), never a
loose nullable `owner_user_id`. Retention (N3) stays configurable and
server-side; notifications/conversations retention must not weaken audit.

## 11. API Impact (PROPOSED DESIGN)

| Capability | Existing | Required (if approved) |
|---|---|---|
| D38 | `POST /api/v3/ops/batches/{id}/assign`; legacy `review/{id}/assign`; audit_trail | V3 item claim/assign/reassign/complete endpoints (ops + PE scope) preserving attribution; entity-scoped reassign guard; history read surface |
| D39 | `v3_messaging.py` org endpoints; `_authorize_org_actor` | Entity-scoped conversation endpoints (create/list/read/send/read-state) with PE own-entity guard; internal support participant guard; optional work-item/issue linkage |
| D40 | `v3_notifications.py` list/read/read-all | Event producers (assignment, messaging, QC); PE recipient resolution; pagination (exists) |

Extend canonical V3 API only; no parallel legacy API; idempotency where
writes are retryable (conversation create, read-state); audit events on every
state-changing action.

## 12. Frontend Impact (PROPOSED DESIGN)

| Capability | Surface | Required (if approved) |
|---|---|---|
| D38 | /ops queues + /pe (PEShell) | Assignment/reassign controls + attribution history UI within existing DataTable components; status/evidence readability |
| D39 | /pe (PEShell) | Entity operational messaging entry inside PEShell (reuse D21 primitives + realtime hook); ops support participation view |
| D40 | /pe (PEShell) + existing shells | PE notification entry (bell) inside PEShell; event-driven list refresh |

No new shell; PEShell remains dedicated; D21 components reused; loading /
error / empty states required per existing standard; responsive (six widths).

## 13. Billing Impact (PROPOSED DESIGN — no billing changes)

None of D38/D39/D40 touches subscriptions, credits, orders or payment records.
No user-level billing is proposed anywhere. No billing change in Phase 5.

## 14. Audit / Provenance Impact (PROPOSED DESIGN)

| Action | Business data change | Audit required | Actor/time/before-after | Org/workspace | Reason |
|---|---|---|---|---|---|
| Assign / reassign / claim item | Yes (assignment state) | Yes — review_assignment_history + audit_trail | Yes | Org + entity | assignment note |
| PE conversation create/join/message | Yes (thread state) | Yes — append-only participant + message audit | Yes | Entity | operational |
| Notification read/dismiss | Lifecycle only | Light (lifecycle events where material) | Yes | Recipient scope | n/a |

## 15. AI Impact (PROPOSED DESIGN)

None of D38/D39/D40 requires AI. Messaging thread assistance, notification
summaries or auto-assignment suggestions would be OPTIONAL AI-assist only and
must never: become an authorization mechanism, select factors, determine
accounting truth, bypass validation/approval, or create customer-facing claims
without review. If any such assist is ever proposed it requires explicit PO
approval and a controlled human-review boundary.

## 16. Existing vs Missing Capability Matrix

| # | Capability element | Existing | Missing | Notes |
|---|---|---|---|---|
| D38.1 | D22 batch assignment + audit_trail | ✅ | — | ops `/batches/{id}/assign` |
| D38.2 | Legacy staff review assignment history | ✅ (legacy) | — | `routes/admin/assignments.py` |
| D38.3 | Canonical V3 per-item claim/assign/reassign/complete (WorkItem) | — | ❌ | ADR-V3-003/011 |
| D38.4 | Entity-scoped reassignment attribution + partial-work recovery | — | ❌ | entity_id on history (B) |
| D38.5 | Dormant tables reconciled | — | ❌ | retirement deferred (ADR-V3-016) |
| D39.1 | Org-scoped messaging (customer/consultant/support) | ✅ | — | N1 compliant |
| D39.2 | PE denied 403 on org messaging | ✅ | — | Correct per N1 |
| D39.3 | Entity-scoped PE↔CT operational messaging | — | ❌ | PE-MSG-001; B/C schema |
| D39.4 | Work-item/issue-scoped thread context | — | ❌ | PE-MSG-001 |
| D40.1 | Notifications table + recipient model | ✅ | — | generic recipient |
| D40.2 | list/read/read-all + pagination + realtime | ✅ | — | v3_notifications |
| D40.3 | Event-driven creation across assignment/messaging | — | ❌ | partial (document events only) |
| D40.4 | PE notification surface in PEShell | — | ❌ | no bell in /pe |

## 17. Implementation Workstreams (PROPOSED DESIGN — ordered)

### WS0 — Phase-5 foundations (attribution baseline + inventory lock)
Objective: baseline assertions and dormant-table reconciliation record.
Dependencies: none. Files: backend data/domain tests + docs. DB impact: none
(reconciliation = formalise, no deletion). API: none. Frontend: none.
Security: none. Tests: read-only audit + regression baseline. Acceptance:
inventory tables verified; dormant tables documented. Rollback: n/a (no change).

### WS1 — D38 assignment/reassignment attribution (backend-first)
Objective: canonical V3 item-level claim/assign/reassign/complete preserving
attribution (ops + PE scope); history read surface; partial-work recovery.
Dependencies: WS0. Files: new `services/work_items.py` (or equivalent),
`data/*`, `api/v3_operations.py` / `api/v3_pe.py`, `domain/partners.py`
state machine, tests. DB: B (entity scope on history) if needed. API: new
endpoints (ops + pe, capability-gated). Frontend: later (WS4). Security:
own-entity + org guards, negative tests. Tests: unit state machine; integration
ALLOW/DENY; attribution preserved on reassign. Acceptance: every assignment/
reassignment writes append-only attribution; audit immutable. Rollback:
feature-flag off; endpoints additive.

### WS2 — D39 entity operational messaging (backend + schema, gated)
Objective: PE↔CarbonTally operational messaging model per N1/PE-MSG-001.
Dependencies: WS0; **PO decision (entity conversation model, B or C)**.
Files: migration (only after PO), `v3_messaging.py` entity scope + guards,
RLS policies, data layer, audit. DB: B or C. API: entity conversation
endpoints. Frontend: later (WS4). Security: own-entity-only participants;
internal support; deny customers/consultants/other PEs; negative tests.
Acceptance: PE staff of entity E can thread only with CarbonTally; PE A↔PE B
and Customer↔PE denied. Rollback: additive model behind approval; no legacy
path change.

### WS3 — D40 notifications completion
Objective: event-driven notifications for assignment/messaging/QC events;
PE recipient resolution; PEShell notification entry (WS4). Dependencies: WS1/WS2
event sources. Files: `data/notifications.py` producers, `v3_notifications.py`
recipient resolution, tests. DB: B if entity context added. API: minor.
Frontend: bell entry (WS4). Security: recipient = resolved actor only.
Tests: recipient scoping + cross-actor denial. Rollback: producers additive.

### WS4 — Frontend integration (D38 status/history + D39 PE messaging + D40 PE bell)
Objective: PE-appropriate UI inside the dedicated PEShell; ops attribution
history views; D21 primitives; responsive. Dependencies: WS1–WS3.
Files: `frontend/src/v3/pe/*`, `frontend/src/v3/ops/*`, api.js. Frontend only.
Security: visibility mirrors server. Tests: component + browser E2E (isolated
fixtures). Rollback: UI behind routes/capabilities.

### WS5 — Regression, security negative suite, docs & acceptance report
Dependencies: WS1–WS4. Files: tests + docs/audit + plan update.

## 18. Dependency Graph (PROPOSED DESIGN)

```text
WS0 (baseline)
  ├─ WS1 D38 attribution ──────────────┐
  └─ WS2 D39 entity messaging (PO gate) ┤
                                        ├─ WS4 UI integration → WS5 close-out
WS3 D40 notifications (needs WS1/WS2 events) ┘
```

## 19. Testing Strategy (PROPOSED DESIGN — no tests modified in this gate)

- **Unit:** attribution state machine; entity conversation authorization; PE
  recipient resolution; notification producer idempotency.
- **API integration (ALLOW/DENY):** org A↔org B; consultant client grant
  boundaries; PE A↔PE B; PE↔customer thread denial; staff support boundary;
  admin boundary; forged IDs; frontend-only attempts (403).
- **Frontend:** component tests for new PE/ops UI; browser E2E on isolated
  fixtures (no demo-data mutation), six-width responsive, D21 consistency.
- **Regression:** existing V1.2 suites remain green; no test modified to pass.

## 20. Product Owner Decision Register (PRODUCT OWNER DECISION REQUIRED)

| # | Question | Options | Cline recommendation | Architecture consequence | Security consequence | Commercial consequence | Blocks implementation? |
|---|---|---|---|---|---|---|---|
| P5-1 | Approve Phase-5 scope = D38 (attribution), D39 (N1/PE-MSG-001 entity operational messaging), D40 (notifications completion)? | (a) All three; (b) subset | All three, ordered WS0→WS5 | Defines phase | None beyond reviewed model | None (no billing) | Yes |
| P5-2 | D38: build canonical V3 item-level claim/assign/reassign/complete service (WorkItem) with entity scope? | (a) Yes full; (b) batch-level only; (c) defer | (a) — completes ADR-V3-003/005 gap | Extends ops+PE queues | Attribution never erased; guards required | None | Yes (WS1) |
| P5-3 | D38: retire/formalise dormant `processing_assignments`/`reassignment_history` (no deletion)? | (a) formalise read-only; (b) keep untouched | (a) | Cleaner inventory | History preserved | None | Yes (WS0/WS1) |
| P5-4 | D39: entity conversation model — (B) additive `processing_entity_id` on conversations vs (C) separate entity-conversation table family? | B / C | **B** (additive, reuses participant/message/RLS family; smaller) | B avoids parallel messaging stack | Own-entity guard + RLS additive | None | Yes (WS2) |
| P5-5 | D39: PE operational messaging participants = own-entity staff + authorised internal CarbonTally support/admin (work/issue-scoped, no customers, no other PEs)? | (a) as stated; (b) narrower | (a) — matches N1 + PE-MSG-001 | Thread scope | Deny Customer↔PE, PE↔PE | None | Yes (WS2) |
| P5-6 | D40: PE notifications entry inside PEShell and event producers for assignment/messaging/QC events? | (a) yes; (b) limited to existing | (a) | PE surface addition | Recipient scoping | None | Yes (WS3/WS4) |
| P5-7 | Confirm no D38/D39/D40 feature creates user-owned data / individual billing / personal workspace? | Confirm / dispute | Confirm | Locks Phase-4 Option A | n/a | n/a | Gates all WS |

## 21. Security Review Register (PROPOSED DESIGN)

Before implementation of WS2 (and WS1 entity scope), a security review is
required for: additive entity-scope RLS family; conversation participant
authorization (own-entity only); notification recipient resolution; nullable
scope columns; and the negative test matrix in §8. WS3/WS4 require a lighter
review pass. No D38/D39/D40 item bypasses the Frontend → API → Auth → Actor →
Workspace → Authorization → RLS chain.

## 22. Migration Plan — PROPOSED ONLY (no migration created)

- Migration count stays **42** during this gate.
- WS1 (if approved): one additive migration **B** (entity scope on
  `review_assignment_history` + indexes) — reversible, no data backfill beyond
  current assignments already captured in audit_trail.
- WS2 (if approved): one additive migration **B** (`processing_entity_id` +
  participant columns + RLS policies on the conversation family) or a new
  table family **C** if the PO chooses C. Org-scoped messaging RLS untouched.
- WS3 (if approved): optional additive columns/indexes **B**.
- No ownership-model change (**D**) and no architectural redesign (**E**).
- 7,049 emission factors untouched by every proposal.

## 23. Rollback Strategy (PROPOSED DESIGN)

- Additive endpoints/columns only; every workstream independently reversible
  by removing additive routes/columns without touching existing data.
- Attribution rows are append-only — rollback never deletes history.
- Feature gates (capability flags) before UI exposure; DB rollbacks use
  forward additive migrations only (no destructive migration).

## 24. Phase 5 Acceptance Criteria (proposed, post-approval)

1. D38: every assignment/reassignment persists append-only attribution;
   entity scope enforced; negative tests green.
2. D39: entity operational messaging live for own-entity PE staff and internal
   support; Customer↔PE and PE A↔PE B denied (403) in API and browser.
3. D40: notifications delivered to correct recipients across domains incl.
   PE; mark-read/read-all; event producers tested.
4. PEShell remains dedicated; no personal workspace; no user-owned data;
   users.user_type untouched.
5. Full V1.2 regression + browser responsive suite green; factors 7,049;
   migrations increment only through approved additive migrations.

## 25. Explicit Non-Goals

No personal workspace; no individual/user-owned emissions/reports/documents;
no individual billing/credits; no `users.user_type` repurposing; no new actor
domain; no global database redesign; no RLS rewrite; no auth replacement; no
V1.3; no billing redesign; no Phase-6 work; no migration created in this gate.
