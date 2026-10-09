# CT-CONSULTANT-DECISION-STATE-ARTEFACT-AUDIT-01

**Consultant Platform — Decision-State Artefact Audit (read-only)**

```text
Task ID                 CT-CONSULTANT-DECISION-STATE-ARTEFACT-AUDIT-01
Document type           READ-ONLY DECISION-STATE AUDIT
Mode                    READ-ONLY / NO CODE / NO SCHEMA / NO MIGRATION / NO TEST CHANGE
Status                  COMPLETE
Authoring agent         Cline
Date                    2026-10-07
Repository branch       p8-release-reconciled
HEAD                    3fec874ca1f170ecb03e7daf69992dbf9e9cd18e
Worktree at start       dirty (221 entries — pre-existing; NOT modified by this task
                        beyond the creation of this file)
```

```text
DECIDED          = a Product Owner / binding decision exists (quoted source)
IMPLEMENTED      = code/schema for it exists in the CURRENT working tree
TESTED           = automated tests exist and were run
LAB-VERIFIED     = verified against the running local Demo Lab (by the implementer)
INDEPENDENTLY VERIFIED = re-tested by a different agent/report
ACCEPTED         = the Product Owner has accepted it
OPEN             = no ratified answer exists; a PO DECISION is still required
```

> **Reading rule.** This document asserts no acceptance. Every "Implemented"
> statement is backed either by a file in the current worktree (cited by path and
> line) or by a named change-map document. Every "Open" statement names the
> decision that is missing. `DECIDED != IMPLEMENTED != TESTED != VERIFIED != ACCEPTED`.

---

## 1. Purpose and scope

This audit answers one question for the whole consultant platform:

> **Which consultant-platform decisions are (a) decided, (b) implemented,
> (c) verified, and (d) genuinely still open — and where is each one written
> down?**

It is deliberately an **artefact map**, not a re-implementation and not a
re-verification. It does not fix anything, does not re-run the full QA harness,
and does not change any decision. Where an implementation claim could be checked
cheaply against the current tree, it was (cited inline).

### 1.1 In scope

- The consultant operating model (firm as customer, client as organisation).
- Consultant RBAC / capabilities.
- Client access profiles and Plane C (the client portal).
- Product modes (standard / co-branded / white-label) and entitlement gating.
- Retention and post-relationship access.
- The consultant UX / navigation remediation stream.
- The F-NAV-1 client-plane reporting-parity defect.

### 1.2 Out of scope

- Manual-processing subscription streams (CT-MP-SUB-003/004) except where they
  intersect a consultant decision (noted, not audited).
- Billing/pricing numbers (PO-5 routes these to a separate commercial task).
- Production deployment, OCR/email environment capability.
- Any code, schema, migration, RLS, API, test or seed change.

---

## 2. Method and authority order

Sources were read and reconciled in the authority order the task specifies:

```text
1. PO Decision Register / ratified PO decisions   (CT-CONSULTANT-PO-CONSOLIDATION-01 §4)
2. Consultant PO Consolidation                    (CT-CONSULTANT-PO-CONSOLIDATION-01)
3. Binding architecture decisions                 (PD-3/PD-7/PD-12; D15/D20/D21)
4. Architecture / change-map docs                 (CT01, CT02, CT03, UX-*, CLI-Remediation)
5. Current code                                   (backend/, frontend/, supabase/)
6. Schema / migrations / RLS                       (supabase/migrations/*.sql)
7. Tests                                           (backend/tests, frontend/src/__tests__)
8. Research / secondary design                     (DASHBOARD-SUBSCRIPTION-BILLING-UIUX-01)
9. Historical / audit docs                          (docs/ohd, docs/audit)
```

Where a lower source disagreed with a higher one, the higher source governs and
the disagreement is recorded in §7 (Drift observations).

### 2.1 Artefacts inspected

| Artefact | Path |
|---|---|
| PO consolidation (authority) | `docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md` |
| Model decision baseline | `docs/architecture/CT-CONSULTANT-MODEL-DECISION-AND-IMPLEMENTATION-01.md` |
| Change map — capabilities | `docs/architecture/CT-CONSULTANT-MODEL-IMPLEMENTATION-02.md` |
| Change map — profiles/modes/Plane C | `docs/architecture/CT-CONSULTANT-MODEL-IMPLEMENTATION-03.md` |
| UX navigation remediation | `docs/architecture/CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01.md` / `…-01A.md` |
| Independent consultant verify | `docs/architecture/CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01.md` |
| F-NAV-1 remediation | `docs/architecture/CT-CONSULTANT-CLIENT-PLANE-PARITY-REMEDIATION-01.md` |
| Billing/UX design draft | `docs/architecture/CT-CONSULTANT-DASHBOARD-SUBSCRIPTION-BILLING-UIUX-01.md` |
| CT02 migration | `supabase/migrations/20261102000000_ct_consultant_model_02_capability_admission.sql` |
| CT03 migration | `supabase/migrations/20261103000000_ct_consultant_model_03_client_access_and_mode.sql` |
| Admission gate (code) | `backend/api/consultant_auth.py` |
| Profile matrix (code) | `backend/domain/relationship_access.py` |
| Mode/entitlement (code) | `backend/domain/consultant_entitlement.py` |
| Retention policy (code) | `backend/domain/consultant_retention.py` |
| Plane C API (code) | `backend/api/v3_client_portal.py`, `backend/api/client_portal_auth.py` |
| Plane C route (code) | `frontend/src/App.js:2242` |

---

## 3. Decision inventory

There are **seven artefact layers** of consultant decisions/obligations. Each has
a different authority weight.

| Layer | Artefact | What it is | Authority |
|---|---|---|---|
| **D1** | `CT-CONSULTANT-PO-CONSOLIDATION-01.md` §4 | **PO-1 … PO-10** — ten ratified binding decisions | **BINDING** |
| **D2** | `…-PO-CONSOLIDATION-01.md` §17 | **F-1 … F-10** — current-code findings to fix | Targets (not defects claimed as current) |
| **D3** | `…-PO-CONSOLIDATION-01.md` §19 | **OQ-1 … OQ-4** — four secondary questions | Open questions (safe defaults) |
| **D4** | `CT-CONSULTANT-MODEL-DECISION-AND-IMPLEMENTATION-01.md` | Model baseline + implementation mandate | Binding design baseline |
| **D5** | `CT-CONSULTANT-MODEL-IMPLEMENTATION-02/03.md` | Change maps — what was built for F-1/F-2/F-10 (CT02) and F-3..F-9 (CT03) | Implementation records |
| **D6** | `…-IMPLEMENTATION-03.md` §37/§38 | **G-1 … G-9** gaps and **PD-1 … PD-6** PO decisions | Open items |
| **D7** | `CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01.md` §31 | **PD-NAV-1, PD-3A, PD-1A, PD-2A, R-NAV-1** + F-IND-1..5 | Independent-verify backlog |

### 3.1 Binding decisions (D1 — the ten)

Repeated verbatim-by-reference from `CT-CONSULTANT-PO-CONSOLIDATION-01.md` §4.1:

| ID | Topic | PO choice | Binding effect |
|---|---|---|---|
| **PO-1** | Mode switching | B + D | Firm **requests**; effect at billing/renewal boundary; never self-service; existing relationships not silently broken |
| **PO-2** | Client-user invitations | A | Inviting/managing/removing client users is **consultant-side only** |
| **PO-3A** | Branding granularity | A | **Firm-level branding only**; no per-client overrides |
| **PO-3B** | White-label availability | A | White-label presentation exists **only in White-Label mode** |
| **PO-4** | Managed profile + custom domain | C | MANAGED in Co-Branded + White-Label only; custom domain **White-Label only**; STANDARD = no client plane |
| **PO-5** | Commercial configuration | C | Modes are architecture; **pricing/packaging is a separate commercial task**; Admin Panel authoritative; no invented prices |
| **PO-6** | Final approval | B + C | A consultant role **may** perform final approval for a managed org; follows consultant RBAC |
| **PO-7** | Ending the relationship | D | **Either party** may initiate; auth + confirmation + audit; never deletes/migrates the org |
| **PO-8** | Plane C path | A | **`/portal/:clientId/*`**; branding is never the security identity |
| **PO-9** | Client factor mapping | A | **No** — client users never map/remap/recalculate (any profile) |
| **PO-10** | Post-relationship access | B + E | History retained; **controlled read-only** access; retention period NOT invented here |

### 3.2 Additional ratified consultant decisions referenced

| Decision | Source | Effect |
|---|---|---|
| **PD-3 / PD-7** | `CT-CONSULTANT-CLIENT-PLANE-PARITY-REMEDIATION-01.md` (refers to `CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01`) | Consultant-operated client plane reaches the same organisation-plane endpoints (emissions/reports); reused as-is |
| **PD-12** | same | Consultants are **not** `organization_members` rows |
| **D-7** | same | Tenant liveness |
| **D20 / D15** | `20260821000000_d20_d15_active_consultant_grant.sql` | Only `status=active` grants consultant access |
| **D21** | `20260821010000_d21_white_label_branding.sql` | White-label branding (legacy booleans, now mode-capped) |
| **D11-C1** | Hindsight / P6-2 governance | Firm-centric lifecycle notification recipients; client orgs not recipients |
| **P6-2C D1/D2/D3** | `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` | Ratified processing-capability decisions |
| **P6-2D D7b** | same | **Withdrawn** — `CONSULTANT` `processing_origin` value rejected |

---

## 4. Decision-state matrix (the core finding)

Legend — `●` = yes/complete · `◐` = partial · `○` = no/absent · `—` = n/a.
"Sub-state" records the *residual* that is still open even where the top-level
decision is done.

### 4.1 PO-1 … PO-10

| Decision | Decided | Implemented | Tested | Lab-verified | Indep. verified | Accepted | Residual open (sub-state) |
|---|:--:|:--:|:--:|:--:|:--:|:--:|---|
| **PO-1** Mode switching (request-at-boundary) | ● | ● | ● | ● | ○ | ○ | Request has **no decision consumer** — G-5 / PD-5 |
| **PO-2** Invitations consultant-side only | ● | ● | ● | ● | ○ | ○ | None (enforced by route absence) |
| **PO-3A** Firm-level branding only | ● | ● | ◐ | ● | ○ | ○ | Surfaced via brand derivation; no per-client override path |
| **PO-3B** White-label availability mode-gated | ● | ● | ● | ● | ○ | ○ | None (entitlement matrix) |
| **PO-4** MANAGED + custom-domain gating | ● | ● | ● | ● | ○ | ○ | Custom-*domain* provisioning UI is separate (D21/whitelabel) |
| **PO-5** Commercial configuration | ● | ◐ | ◐ | ◐ | ○ | ○ | **Pricing/packaging deliberately OUT** (separate commercial task) |
| **PO-6** Final approval | ● | ◐ | ● | ● | ○ | ○ | Consultant CAP-APPROVE done (CT02); **client-side `approve_final` role gate NOT built** → G-3 / PD-1 |
| **PO-7** Ending the relationship | ● | ◐ | ● | ● | ○ | ○ | Mechanism done (request); **execution/confirmation workflow** open → G-5 / PD-5 |
| **PO-8** Plane C path `/portal/:clientId/*` | ● | ● | ● | ● | ○ | ○ | None |
| **PO-9** Client never maps/recalculates | ● | ● | ● | ● | ○ | ○ | None |
| **PO-10** Post-relationship retained read-only | ● | ◐ | ● | ● | ○ | ○ | Retained **read** done; **deletion execution** open → G-2/G-9 / PD-3; **post-termination messaging** open → PD-2 |

> **Bottom line for D1:** all ten decisions are **DECIDED**. All ten have a
> shipped-in-worktree implementation; **two are only partially implemented**
> (PO-5 commercial numbers are explicitly out of scope; PO-6 client approval
> gate and PO-10 execution/messaging are open). **None** is independently
> verified or PO-accepted.

### 4.2 Findings F-1 … F-10

| Finding | Requirement | State | Evidence in current tree |
|---|---|---|---|
| **F-1** | Capability-gated consultant admission | **CLOSED (impl+test+lab)** | `backend/api/consultant_auth.py:185` (`if not context.firm_member.can_view_client: return ()`) |
| **F-2** | Consultant final-approval capability | **CLOSED (impl+test+lab)** | `consultant_auth.py:33,315,320` + `can_approve` (migration CT02) |
| **F-3** | Persisted client access profile | **CLOSED** | `relationship_access.py`; migration CT03 column `client_access_profile` |
| **F-4** | RETAINED read-only state | **CLOSED (read half)** | `relationship_access.resolve_relationship_state` + `retained_read_only` |
| **F-5** | Mode entitlement gating | **◐ ENTITLEMENT HALF CLOSED** | `consultant_entitlement.py`; hostname resolver open (see F-9) |
| **F-6** | Mode-change REQUEST | **CLOSED** | `consultant_mode_change_requests` (CT03 migration); `v3_consultants.py:528` `POST /me/mode-change-requests` |
| **F-7** | Plane C at `/portal/:clientId/*` | **CLOSED** | `frontend/src/App.js:2242`; `backend/api/v3_client_portal.py` |
| **F-8** | Client-side relationship entry point | **CLOSED (mechanism=request)** | `v3_client_portal.py` `relationship-requests`; requires `confirmed` |
| **F-9** | Hostname→brand resolution | **◐ PARTIAL / OPEN** | entitlement gate exists; **resolution path absent** (G-4 / PD-6) |
| **F-10** | Capability write MERGE not REPLACE | **CLOSED** | `v3_consultants.py` `PATCH /me/team/{member_id}/capabilities` (CT02) |

### 4.3 Open questions OQ-1 … OQ-4 (PO-Consolidation §19)

| OQ | Question | State after CT03 |
|---|---|---|
| **OQ-1** | Mechanism to change/end a relationship | **RESOLVED as mechanism** (confirmed request persists, changes nothing). Operational workflow open → **PD-5** |
| **OQ-2** | Retention period & scope | **RESOLVED: 7 years** (Admin-configurable). Execution open → **PD-3**; API surface open → **PD-4** |
| **OQ-3** | Termination for an OFF / no-login client | **RESOLVED as mechanism** (CarbonTally support path) |
| **OQ-4** | Post-termination messaging channel | **OPEN** → **PD-2** (CT03 implements "none") |

> §19.3 of the PO consolidation listed four BLOCKED sub-scopes (OQ-1..OQ-4). CT03
> resolved OQ-1/OQ-2/OQ-3 as *mechanisms* and re-raised the residual parts as
> **PD-1 … PD-6** (see 4.4). OQ-4 survives as PD-2.

### 4.4 PO DECISION REQUIRED register (D6 + D7 consolidated)

These are the **genuinely open** consultant decisions across every artefact.
None of them re-opens PO-1 … PO-10; each is a residual the implementation
deliberately left to the Product Owner.

| ID | Open decision | Source | Consequence if unresolved (current behaviour) |
|---|---|---|---|
| **PD-1** | Which **client role(s)** may exercise `approve_final`, under what firm config? | CT03 §38 | MANAGED ceiling **denies** `approve_final` (fail closed) — a managed client cannot approve |
| **PD-2** | Post-termination messaging: channel / notice-only / none? | CT03 §38 (OQ-4) | CT03 implements **"none"** |
| **PD-3** | Retention **execution**: indefinite, or run deletion at 7y; who is notified? | CT03 §38 | `auto_delete_enabled=false`; nothing deletes |
| **PD-4** | Who may edit the consultant-retention setting (System Admin vs Staff Admin) + Admin UI? | CT03 §38 | Setting stored but **no API surface** (G-1) |
| **PD-5** | Who confirms a client-initiated relationship request, SLA, what the client sees? | CT03 §38 | Requests persist as `requested`; **nothing advances them** (G-5) |
| **PD-6** | Hostname→brand resolution policy (verified/suspended domain behaviour) | CT03 §38 | No resolver; INV-F satisfied only by having no hostname input |
| **PD-NAV-1** | Dedicated consultant "Firm & Billing" surface | Independent Verify §31 | No dedicated surface; billing reachable but not consolidated |
| **PD-3A** | Server-side hardening of firm-task `client_id` | Independent Verify §31 (F-IND-1) | `201` for unauthorised / foreign client id (no access conferred) |
| **PD-1A** | Team invitation / signup-email lifecycle vs resolve-by-email | Independent Verify §31 | Team adds resolve an existing identity by email |
| **PD-2A** | May a firm admin assign the `owner` role from the Team surface? | Independent Verify §31 | Undecided |
| **R-NAV-1** | Consolidate legacy `/consultant/items/…` route | Independent Verify §31 | Legacy route remains |
| **G2 / Q-1** | May an active-grant consultant create manual-extraction batches for an engaged client? | Recall (CT-MP-SUB-004 fact-finding) | Guard asymmetry between `/manual-extraction` and `/processing`; **BLOCKED — PO_DECISION_REQUIRED** |

> **Non-decision, informational findings** (Independent Verify): F-IND-2
> (client-context endpoint existence oracle, recommend uniform 404),
> F-IND-3 (`is_org_consultant()` omits `can_view_client` — defence-in-depth
> dilution), F-IND-4/F-IND-5 (informational). These are **hardening** items, not
> blocked policy, but F-IND-2 remediation is recommended.

---

## 5. Implementation evidence (what is actually in the tree)

### 5.1 Migrations (schema truth)

| Migration | Purpose |
|---|---|
| `20261102000000_ct_consultant_model_02_capability_admission.sql` | Adds `consultant_firm_members.can_view_client` + `can_approve` (NOT NULL DEFAULT false). Backfills `can_view_client=true` on pre-existing active members (IMPL-1). **No RLS change.** |
| `20261103000000_ct_consultant_model_03_client_access_and_mode.sql` | Adds `consultant_clients.client_access_profile` (CHECK off/read_only/collaborative/managed, DEFAULT off) + `retained_read_only`; `consultant_profiles.commercial_mode` (CHECK standard/co_branded/white_label); tables `consultant_relationship_requests` and `consultant_mode_change_requests` (RLS enabled, **no policies** = deny-by-default); `system_settings.consultant_relationship_retention` = 7y, `auto_delete_enabled=false`. **No RLS weakened.** |

Both migrations are **additive and idempotent**; CT03 is recorded as **applied to
the local Demo Lab DB** (`carbontally_demo_local`). Neither is applied to
production.

### 5.2 Code (behaviour truth)

| Concern | File | Confirmed |
|---|---|---|
| Capability-gated admission (F-1) | `backend/api/consultant_auth.py:185` | ✅ `can_view_client` gate present; relationship alone no longer admits |
| Consultant approval authority (F-2) | `backend/api/consultant_auth.py:33,315,320` | ✅ `can_approve` authority resolver |
| Profile ceiling + PO-9 (F-3/PO-9) | `backend/domain/relationship_access.py` | ✅ `CLIENT_FORBIDDEN_OPERATIONS = {map_factors, edit_mappings, recalculate}`; `profile_allows` fails closed |
| Modes + entitlement (F-5/PO-4) | `backend/domain/consultant_entitlement.py` | ✅ STANDARD/CO_BRANDED/WHITE_LABEL matrix; mode wins over legacy flags |
| Retention policy (OQ-2) | `backend/domain/consultant_retention.py` | ✅ 7y default; fail-safe; **deletes nothing** |
| Plane C API (F-7/F-8) | `backend/api/v3_client_portal.py` + `client_portal_auth.py` | ✅ `/api/v3/portal/{client_id}/...`; server-authoritative context; absence of map/recalc/user/plan routes |
| Plane C route (F-7) | `frontend/src/App.js:2242` | ✅ `/portal/:clientId/*` |
| Firm-side mode/profile endpoints (F-3/F-4/F-6) | `backend/api/v3_consultants.py:528,576,629` | ✅ mode-change request, access-profile write, audit |

### 5.3 Change markers (delta re-derivation)

Both increments are marked so the delta is mechanically separable inside a shared
dirty worktree:

```bash
grep -rl 'CT-CONSULTANT-MODEL-IMPLEMENTATION-02' backend frontend supabase tools 2>/dev/null | sort
grep -rl 'CT-CONSULTANT-MODEL-IMPLEMENTATION-03' backend frontend supabase tools 2>/dev/null | sort
```

Both were run in this audit: the CT02 marker hits `consultant_auth.py`,
`v3_consultants.py`, `v3_processing_workflow.py`, `data/consultants.py`,
`domain/partners.py`, the CT02 migration and lab tools; the CT03 marker hits the
four new domain/api modules, `v3_client_portal.py`, `client_portal_auth.py`,
`router.py`, `App.js`, the portal frontend, the CT03 migration and lab verifiers.
**This confirms CT02 and CT03 are present in the current worktree, not merely
described in a document.**

---

## 6. What is genuinely open (the answer to the question)

Grouped by *kind* of openness, so the PO can dispose of them efficiently.

### 6.1 Open because no PO decision exists (policy)

```text
PD-1   client role(s) that may approve_final
PD-2   post-termination messaging channel (OQ-4)
PD-3   retention execution + legal hold + notification
PD-4   who may edit the retention setting
PD-5   who confirms a client relationship request (and SLA)
PD-6   hostname -> brand resolution policy
PD-3A  firm-task client_id server-side hardening
PD-1A  team-invitation / signup-email lifecycle
PD-2A  firm-admin assigning the owner role
PD-NAV-1  dedicated Firm & Billing surface
G2/Q-1 consultant creation of manual-extraction batches (guard asymmetry)
```

### 6.2 Open because implementation is deliberately deferred (engineering)

```text
G-1  consultant-retention setting has no API surface (needs PD-4)
G-2  retention deletion not executed (needs PD-3)
G-3  no client-side approve_final role gate (needs PD-1)
G-4  hostname->brand resolver unimplemented (needs PD-6)
G-5  relationship/mode requests have no decision consumer (needs PD-5)
G-6  Plane C renders no report/evidence page yet (ceiling permits it)
G-7  four migration-contract tests stay red (pre-existing inventory allow-lists)
G-8  Demo Lab gateway does not proxy Supabase Realtime WebSocket (environment)
G-9  retention expiry computed but never enforced (is_retained has no caller)
R-NAV-1  legacy /consultant/items route not consolidated
```

### 6.3 Open because nothing manages the requests yet

A **notable structural gap**: CT03 created two request tables
(`consultant_relationship_requests`, `consultant_mode_change_requests`) and the
APIs that *create* requests, but **no consumer** advances a request to
`approved`/`rejected`/`completed`. In the current tree a request is a durable,
audited **record with no decision workflow** (G-5). This is a real gap that
spans PD-1/PD-5.

### 6.4 Explicitly NOT open (do not re-litigate)

From `CT-CONSULTANT-PO-CONSOLIDATION-01.md` §19.2 — recorded closed: mode
semantics (PO-1), invitations consultant-side (PO-2), branding granularity
(PO-3A), white-label availability (PO-3B), MANAGED + custom-domain gating (PO-4),
commercial configuration ownership (PO-5), consultant final-approval authority
(PO-6), either-party termination (PO-7), Plane C path (PO-8), client never
maps/recalculates (PO-9), retained data + read-only access (PO-10), the tenancy
invariants INV-A…INV-G, the five client profiles, the termination state machine,
and "termination does not create a new organisation.id".

---

## 7. Drift observations (source disagreements / supersessions)

| # | Observation | Disposition |
|---|---|---|
| DR-1 | An earlier "Final Approval" finding treated consultant approval as **customer-only**; `CT-CONSULTANT-MODEL-DECISION-AND-IMPLEMENTATION-01.md` §18 states this is **superseded** by PO-6 (consultant **may** approve) | Superseded by PO-6 — do not resurrect |
| DR-2 | `DASHBOARD-SUBSCRIPTION-BILLING-UIUX-01.md` is **DESIGN REVIEW ONLY**; its §19 lists 11 items "requiring PO confirmation". Several are now **closed by PO-1..PO-10** (e.g. MANAGED in co-branded/white-label = PO-4; client invite authority = PO-2; post-handover read-only = PO-10) | Design doc is subordinate; PO decisions govern. Its unresolved items (plan names, pricing, seat/limit numbers) = **PO-5 separate commercial task** |
| DR-3 | `CT02`'s unknown-capability test asserted `can_manage_team` was unaddressable; `CT03` exposes the full operational capability set, so CT03 **superseded** that expectation with `can_grant_seat_entitlement` remaining unaddressable | Declared supersession in CT03 §33 — correct, not a weakened assertion |
| DR-4 | `CT-CONSULTANT-MODEL-IMPLEMENTATION-02/03` statuses are self-declared **LAB-VERIFIED (self) — NOT INDEPENDENTLY VERIFIED**; the independent report (`…UX-PARITY-INDEPENDENT-VERIFY-01`) covers the **UX/navigation** increment, **not** the CT03 client-plane increment | CT03 client-plane remains **without independent verification** |
| DR-5 | AGENTS.md §54 records ~177 pre-existing worktree entries; this session measured **221** | Worktree grew (more uncommitted streams); no reset was performed |
| DR-6 | `requires_consultant` (`/consultant-portfolio`) is a **separate plane** and was deliberately untouched by the F-NAV-1 fix | Not a defect; different authorization plane |

---

## 8. Verification and acceptance state

This is the layer most often conflated. The honest roll-up:

| Increment | IMPLEMENTED | TESTED | LAB-VERIFIED | INDEP. VERIFIED | PO-ACCEPTED |
|---|:--:|:--:|:--:|:--:|:--:|
| **CT02** capability admission & approval | ✅ | ✅ unit | ✅ | ❌ | ❌ |
| **CT03** profiles / modes / Plane C / retention | ✅ | ✅ unit (73 + 7 FE) | ✅ (API 32/32, security 46/46, browser 31/31) | ❌ | ❌ |
| **UX-NAV-01 / 01A** navigation remediation | ✅ | ✅ (19 + full FE) | ✅ (24/24, 49/50) | ✅ (`VERIFIED_WITH_FINDINGS`) | ❌ |
| **F-NAV-1** client-plane reporting parity | ✅ | ✅ (8 unit) | ✅ (browser 20/20) | ❌ | ❌ |

Key facts:

- The **only** independent verification in this whole stream is
  `CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01.md`, verdict
  `VERIFIED_WITH_FINDINGS` with **no blocking findings** and recommendation
  **"PO ACCEPTANCE"** — but that report explicitly says it is **not** a
  production-readiness recommendation.
- **CT03** (the client-plane increment) is self-verified only; its own report
  says "Awaiting independent QA and the PO decisions PD-1 … PD-6".
- **F-NAV-1** is `IMPLEMENTED_AND_LAB_VERIFIED`, "pending independent
  verification".
- Full backend suite carries **8 pre-existing failures** (unchanged CT02→CT03
  baseline; 4 are migration-inventory allow-lists — G-7).
- **No increment is PO-accepted.** No increment is production-ready.

---

## 9. Traceability and residual risks

### 9.1 Decision → implementation → open mapping (compact)

```text
PO-1  mode request     -> consultant_mode_change_requests / POST me/mode-change-requests  -> G-5/PD-5
PO-2  invitations      -> absent on Plane C (route-absence test)                           -> closed
PO-3A firm branding    -> portal renders firm brand (no per-client override path)          -> closed
PO-3B white-label gate -> consultant_entitlement.white_label_presentation                  -> closed
PO-4  managed/domain   -> consultant_entitlement matrix (403 in standard)                  -> closed
PO-5  commercial cfg   -> no consultant write path                                         -> OUT (separate commercial task)
PO-6  final approval   -> can_approve (consult) ; client approve_final NOT built           -> G-3/PD-1
PO-7  end relationship -> relationship-requests (confirmed, audited, non-destructive)      -> G-5/PD-5
PO-8  Plane C path     -> App.js /portal/:clientId/* + /api/v3/portal/*                     -> closed
PO-9  no client mapping-> relationship_access CLIENT_FORBIDDEN_OPERATIONS (fail closed)    -> closed
PO-10 post-relationship-> retained_read_only + 7y policy (no execution, no messaging)      -> G-2/PD-3, PD-2
```

### 9.2 Residual risks carried forward

| Risk | Description |
|---|---|
| R-1 | **Client-plane increment unverified independently** — CT03 self-verification only; the security matrix (46/46) was authored by the implementer |
| R-2 | **No decision consumer** for relationship/mode requests — records accumulate with no workflow (G-5) |
| R-3 | **Retention is a policy with no teeth** — `is_retained` has no production caller and nothing deletes (G-2/G-9) |
| R-4 | **Client approval is fail-closed** — managed clients cannot approve until PD-1 is decided (safe, but a functional gap) |
| R-5 | **Behaviour is worktree-only** — CT02/CT03/F-NAV-1 are uncommitted; the CT03 schema migration is applied to the **lab** DB only; a fresh checkout has neither the code nor the migration |
| R-6 | **Migration-inventory contract tests red** (G-7) — CI noise that can hide real migration regressions |
| R-7 | **F-IND-2 existence oracle** — the client-context endpoint distinguishes "not yours" (403) from "absent" (404); low severity, recommend uniform 404 |

---

## 10. Final verdict

```text
DECISION-STATE AUDIT  =  COMPLETE
SCOPE                 =  READ-ONLY (no code/schema/migration/test change)
```

- **Decided:** the consultant business model is **fully decided** at the policy
  layer — PO-1 … PO-10 are ratified and binding, and the ten blockers they were
  meant to clear are cleared.
- **Implemented:** the decided model is **substantially implemented in the
  current worktree** (CT02 + CT03), evidenced by files, migrations and change
  markers — not merely by documents.
- **Verified:** implementation is **self-lab-verified**; only the
  **UX/navigation** increment has been **independently verified**. The **CT03
  client plane** has **not** been independently verified.
- **Accepted:** **nothing** is PO-accepted.
- **Genuinely open:** twelve policy decisions and ten engineering gaps remain,
  dominated by three themes — **(i) the request/decision workflow does not exist
  yet** (PD-5/G-5), **(ii) retention has no teeth** (PD-3/G-2/G-9), and
  **(iii) unverified client-plane security** (R-1). All are residuals of a
  decided model, not re-openings of it.

### 10.1 Recommended disposition

1. **Independent verification of CT03** (client plane) — the single highest-value
   next step; it is the only security-sensitive increment without a second pair
   of eyes.
2. **Decide PD-5 + PD-1 together** — both concern who disposes of a request;
   building the decision consumer unblocks PO-1 and PO-7 end-to-end.
3. **Decide PD-3/PD-4** — turns the retention policy into enforceable behaviour
   and gives the `system_settings` key an owner and a surface.
4. **Commit strategy** — decide how CT02/CT03/F-NAV-1 leave the worktree and how
   the lab-only migration (R-5) reaches the environment of record.

---

## 11. Metadata / change hygiene (this task)

```text
DOCUMENT          docs/architecture/CT-CONSULTANT-DECISION-STATE-ARTEFACT-AUDIT-01.md
TASK              CT-CONSULTANT-DECISION-STATE-ARTEFACT-AUDIT-01
MODE              READ-ONLY. No code, schema, migration, RLS, API, route, test,
                  seed, configuration, deployment or environment change was made.
FILES CREATED     this document only
GIT               branch p8-release-reconciled; HEAD 3fec874ca1f170ecb03e7daf69992dbf9e9cd18e
                  unchanged; no reset/clean/rebase/force-push; worktree preserved
                  (221 pre-existing entries at start)
SECRETS           none introduced (no keys, tokens, JWTs or signed URLs written)
AUTHORITY         Product Owner decisions (CT-CONSULTANT-PO-CONSOLIDATION-01 §4)
                  override every lower source in this document.
```

**END OF DOCUMENT — CT-CONSULTANT-DECISION-STATE-ARTEFACT-AUDIT-01.**
