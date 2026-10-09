# CT-CONSULTANT-PO-CONSOLIDATION-01

**Consultant Model — Product Owner Decision Consolidation & Implementation Contract**

```text
Task ID                     CT-CONSULTANT-PO-CONSOLIDATION-01
Document type               PRODUCT OWNER DECISION CONSOLIDATION (read-only deliverable)
Mode                        READ-ONLY / DECISION CONSOLIDATION ONLY
Implementation authorization FALSE
Status                      BINDING CONSOLIDATION — supersedes conflicting material
Authoring agent             Cline
Date                        2026-10-06
Repository branch           p8-release-reconciled
STARTING HEAD               3fec874ca1f170ecb03e7daf69992dbf9e9cd18e
ENDING HEAD                 3fec874ca1f170ecb03e7daf69992dbf9e9cd18e (unchanged)
Working tree at start       dirty (177 entries — pre-existing, NOT modified by this task
                            beyond the creation of this file)
```

```text
DESIGN          = DESIGN          (design material is a proposal, not a fact)
PO DECISION     = PO DECISION     (binding; this document is its consolidated record)
IMPLEMENTATION  = NOT PERFORMED
VERIFICATION    = NOT PERFORMED
ACCEPTANCE      = NOT PERFORMED
```

> **Reading rule.** Nothing in this document is a claim that any behaviour is
> implemented, verified or accepted. Every "current state" statement is sourced
> from a named document or a named verification finding; every "must" is a
> decision or a derived requirement. `DESIGNED != IMPLEMENTED != VERIFIED != ACCEPTED`.

---

## Contents

```text
 1. Metadata / provenance
 2. Purpose and scope
 3. Source hierarchy
 4. Consolidated binding PO decisions
 5. Final consultant business model
 6. Commercial / admin configuration model
 7. Consultant RBAC / capability model
 8. Client access-profile model
 9. UI/UX acceptance matrix
10. UI/UX changes required from the PO decisions
11. Plane C contract
12. Branding contract
13. Approval contract
14. Relationship termination contract
15. Post-relationship access contract
16. Direct customer vs consultant-managed distinction
17. Known implementation findings the next task must address
18. Explicit implementation boundaries
19. Remaining open PO questions
20. Implementation acceptance criteria
21. Traceability matrix
22. Final readiness verdict
```

---

## 1. Metadata / provenance

```text
DOCUMENT          docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md
TASK              CT-CONSULTANT-PO-CONSOLIDATION-01
PURPOSE           Consolidate the binding Consultant Model decision document,
                  the completed Consultant Model UI/UX design report, and ten
                  newly issued Product Owner decisions into ONE implementation
                  contract usable by the next (implementation) task.
MODE              READ-ONLY. No code, schema, migration, RLS, storage, API,
                  route, test, seed, configuration, deployment or environment
                  change was made.
AUTHORITY         Product Owner decisions restated in §4.
STATUS            COMPLETE — §§1–22 written; no append sentinel remains.
DATE              2026-10-06 (session date)
VERDICT           READY_FOR_IMPLEMENTATION, scoped (§22); four sub-scopes
                  remain BLOCKED — PO DECISION REQUIRED (§19.3).
CONSUMER          The follow-on implementation task. §17 findings, §18
                  boundaries, §19 blockers, §20 acceptance criteria.
```

### 1.1 Inputs inspected in this session

| Ref | Document | Role | Session provenance |
|---|---|---|---|
| S1 | `docs/architecture/CT-CONSULTANT-MODEL-DECISION-AND-IMPLEMENTATION-01.md` | **PRIMARY / BINDING** | Read (headings + §§1–7, 12, 18) |
| S2 | `Research/CT-CONSULTANT-MODEL-UIUX-DESIGN-01/CT-CONSULTANT-MODEL-UIUX-DESIGN-01.md` | UI/UX DESIGN (proposal) | Read (§§6–9, 13–15, 17, 19–31) |
| S3 | `docs/architecture/CT-CONSULTANT-DASHBOARD-SUBSCRIPTION-BILLING-UIUX-01.md` | Secondary draft design | Read (§§14–17, 19) |
| S4 | `docs/architecture/CT-ORGANISATION-WORKSPACE-REFACTORED-UIUX-01.md` | Organisation workspace UX | Read (§§4–6, 10, 15–18, 24–25) |
| S5 | `Research/CT-CONSULTANT-UX-REMEDIATION-01/CT-CONSULTANT-UX-REMEDIATION-01.md` | Audit / research | Read (§§10–11, 16) |
| S6 | `Research/CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01/*` | Implementation report | Read |
| S7 | `Research/CT-CONSULTANT-ORGANISATION-PARITY-VERIFICATION-01/*` (CoStrict, independent) | Independent verification | Read |
| S8 | `docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md` | Admin control-plane decision (CL-66) | Headings inspected |
| S9 | `AGENTS.md` (project constitution) | Standing project rules | Read |
| S10 | **Product Owner decisions PO-1 … PO-10** (issued with this task) | **BINDING, NEW** | Verbatim from task brief |

```text
NOT inspected this session (do not treat as verified here)
 * live production OpenAPI contract (carbontally-api.onrender.com)
 * a full database/schema audit of the access-profile, client-user and
   entitlement surfaces (S2 V-10/V-11/V-12 = NOT VERIFIED)
 * browser/runtime behaviour (no application was run for this task)
```

```text
PROVENANCE DISCIPLINE
 * S2 is a DESIGN proposal. Its "PROPOSED" screens and DELTA register are not
   implemented by virtue of being designed.
 * S6 is a self-reported implementation report; S7 is the independent
   verification of it. Where they conflict, S7 governs.
 * S5 is an audit; its findings are historical until re-verified (AGENTS.md §80).
```

---

## 2. Purpose and scope

### 2.1 Purpose

To produce **one authoritative document** that an implementer can follow without
having to re-derive product policy from three partially-overlapping design
documents and two audit reports, and without having to guess any Product Owner
decision.

The document exists because, before this task, the consultant model was blocked
on ten explicit Product Owner questions (`S2 §30.2 PO-1…PO-10`). Those ten
questions are now **answered** (§4). This document records the answers, resolves
the design conflicts they create, and states the resulting contract.

### 2.2 In scope

```text
 * The consultant commercial/operating model (three modes; firm as customer)
 * Consultant RBAC/capability, client access profiles, entitlement boundary
 * Plane C (client-facing) contract and path family
 * Branding, approval, relationship-termination and post-relationship contracts
 * The UI/UX acceptance verdict per design area, and the exact required deltas
 * The known implementation findings the next task must address
 * Open questions that remain genuinely unanswered by the PO
 * Implementation acceptance criteria and the readiness verdict
```

### 2.3 Out of scope

```text
 * Implementation of any kind (no code, schema, migration, RLS, API, route,
   test, seed, config, deployment or environment change)
 * Pricing, plan names, seat counts, usage limits or any commercial value
 * Redesign of the D17/D19/D21/N1/N3 frozen UX decisions
 * Rewriting the primary decision document S1 or the design report S2
 * Any change to production, the investor demo data, or the Admin Panel
 * An implementation prompt (explicitly excluded by the task brief)
```

### 2.4 How the next task must use this document

```text
 1. §4 is the decision set. Do not re-litigate it.
 2. §5–§8 define the model that the implementation must express.
 3. §9–§10 define what UI exists, what changes, and what is rejected.
 4. §11–§16 are contracts. Each states MUST / MUST NOT behaviour.
 5. §17 lists defects carried forward — none are claimed fixed.
 6. §18 bounds the implementation.
 7. §19 lists the only questions still open; each has a safe default.
 8. §20 is the acceptance test surface.
 If a required behaviour is absent from this document, STOP and raise it —
 do not infer it from a design sketch.
```

---

## 3. Source hierarchy

### 3.1 Authority order for consultant-model decisions

```text
1. PRODUCT OWNER DECISIONS PO-1 … PO-10 (§4 of THIS document)
   Highest authority. Binding. Not reinterpretable.
2. THIS CONSOLIDATION DOCUMENT (§§5–§22)
   Where a PO decision requires a design consequence, this document states it.
3. PRIMARY DECISION DOCUMENT (S1) — CT-CONSULTANT-MODEL-DECISION-AND-
   IMPLEMENTATION-01, including binding decisions 1–24 (S1 §12)
   Binding except where a PO decision or this document supersedes it.
4. FROZEN UX / STANDING PROJECT LAW (S9 AGENTS.md; D17/D19/D21/N1/N3)
   Binding on implementation; not reopened here.
5. UI/UX DESIGN REPORT (S2)
   A DESIGN PROPOSAL. Adopted where consistent with 1–4; amended or rejected
   where not. Never evidence of implementation.
6. SECONDARY DRAFT DESIGN (S3)
   Reference only. Contains two items explicitly overruled (§9, DIV-1/§17).
7. ORGANISATION WORKSPACE UX (S4)
   Reference for the reused Organisation surface; its "do not implement yet"
   list (§24) is now largely answered by PO-1…PO-10.
8. AUDIT / RESEARCH (S5) and IMPLEMENTATION-VERIFICATION REPORTS (S6/S7)
   Historical evidence and regression targets. Never current state without
   re-verification.
```

### 3.2 Runtime-truth rule (unchanged from AGENTS.md §2)

For statements about **what the system currently does**, the order is: running
application → database state → API/OpenAPI contract → Git source → migrations →
automated tests. This document makes **no** current-behaviour claim of its own;
it cites S2/S6/S7 findings by ID and leaves them marked unverified where S2 left
them unverified.

### 3.3 Conflicts this document resolves

| # | Conflict | Resolution | Basis |
|---|---|---|---|
| C-1 | Per-client branding selector (S3 §17) vs firm-scoped branding (S1 §10, S2 §26.1 DIV-1) | **Firm-level branding only. Per-client branding is rejected.** | PO-3A (A) |
| C-2 | White-label as purchasable add-on vs mode-capped (S2 §30.2 PO-3b, OBS-1) | **White-Label presentation exists only in White-Label mode, entitlement-gated.** | PO-3B (A) |
| C-3 | Whether MANAGED profile / custom domain sit in Co-Branded (S2 §6 ladder, §27) | **MANAGED: Co-Branded ✓ and White-Label ✓. Custom domain: White-Label ONLY.** | PO-4 (C) |
| C-4 | Self-service plan chooser (S3 §14–15) vs forbidden unrestricted mode switching | **Mode change is a firm-initiated REQUEST; effect at the billing/renewal boundary, or immediate only with explicit CarbonTally approval.** | PO-1 (B+D) |
| C-5 | Client-side "change consultant" action (S2 §17.12 NOT-BUILT-2) vs either party may end the relationship (PO-7 D) | **Either-party initiation is binding; the client-side initiation *entry point* is open (§19 OQ-1). The non-destructive, audited state machine is NOT open.** | PO-7 + §19 |
| C-6 | Client factor-mapping / recalculation (S2 §24 △ rows) | **Not permitted for client users in any profile; consultant/operator-side only.** | PO-9 (A) |
| C-7 | Client-user approval authority (S1 §4, S2 §30.2 PO-6) | **Consultant-managed final approval IS allowed for an authorized consultant role. The blanket "customer-owner-only" rule does NOT apply to consultant-managed Organisations.** | PO-6 (B+C) |
| C-8 | Client-user invitation authority (S2 §30.2 PO-2) | **Consultant-side action only.** | PO-2 (A) |
| C-9 | Plane C path (S2 §30.2 PO-8, ID-4) | **`/portal/:clientId/*`.** | PO-8 (A) |
| C-10 | Client billing surface (S3 §17 vs S2 §17.10) | **Managed clients are never billed by CarbonTally; Plane C billing is a locked, explained state.** | S1 §7, PO-5, S2 §17.10 |

> **Inherited decision set.** This document does not re-open binding decisions
> 1–24 of S1 §12. Where PO-1…PO-10 restate or refine one of them, §4 records the
> refinement; the S1 decision otherwise stands.

### 3.4 Design-report questions now closed

S2 §30.2 raised PO-1…PO-10. All ten are answered; **none may be reopened**:

```text
S2 PO-1  Mode switching              → PO-1   ANSWERED (B+D)
S2 PO-2  Invite authority            → PO-2   ANSWERED (A, consultant only)
S2 PO-3a Brand granularity           → PO-3A  ANSWERED (A, firm-level only)
S2 PO-3b White-label cap             → PO-3B  ANSWERED (A, White-Label mode only)
S2 PO-4  Managed / custom domain     → PO-4   ANSWERED (C)
S2 PO-5  Plan names / pricing        → PO-5   ANSWERED (C: separate task, Admin-configured)
S2 PO-6  Client approval authority   → PO-6   ANSWERED (B+C)
S2 PO-7  Who may end a relationship  → PO-7   ANSWERED (D: either party, audited)
S2 PO-8  Plane C path                → PO-8   ANSWERED (A: /portal/:clientId/*)
S2 PO-9  Client factor mapping       → PO-9   ANSWERED (A: NO)
S2 PO-10 Post-relationship access    → PO-10  ANSWERED (B+E) — retention period flagged §19
```

---

## 4. Consolidated binding PO decisions

These ten decisions are the **authoritative** consultant-model policy. The
option labels (A/B/C/D/E) are the ones the Product Owner used. Each entry below
gives: the decision, its binding sub-clauses, the design consequences, and the
things it explicitly forbids.

### 4.1 Decision table

| ID | Topic | PO choice | One-line binding effect |
|---|---|---|---|
| **PO-1** | Mode switching | **B + D** | Firm **requests** a mode change; effect at billing/renewal boundary unless CarbonTally approves immediate; never an unrestricted self-service switch; existing client users/relationships must not be silently broken |
| **PO-2** | Client-user invitations | **A** | Inviting/managing/removing client users is **consultant-side only**; client users get no invitation authority |
| **PO-3A** | Branding granularity | **A** | **Firm-level branding only**; no per-client brand overrides |
| **PO-3B** | White-Label availability | **A** | White-Label presentation exists **only in White-Label mode**; entitlement-gated, not a free-standing add-on |
| **PO-4** | Managed profile + custom domain | **C** | MANAGED allowed in **Co-Branded and White-Label**; custom domain **White-Label only**; STANDARD = no client login/portal/managed plane |
| **PO-5** | Commercial configuration | **C** | Three product modes are architecture; **pricing/packaging is a separate commercial task**; CarbonTally **Admin Panel** is the authoritative configuration surface; consultants cannot change their own entitlements; **no invented prices/seats/limits** |
| **PO-6** | Final approval | **B + C** | A consultant role **may** perform final approval for a consultant-managed Organisation; approval follows consultant RBAC; **no** blanket "managed-owner-only" rule |
| **PO-7** | Ending the relationship | **D** | **Either party** may initiate; authorization + confirmation + audit (who/when) required; resulting access state defined; **never** deletes or migrates the Organisation |
| **PO-8** | Plane C path | **A** | **`/portal/:clientId/*`**; Organisation identity + authorization boundary stay explicit; branding/domain is never the security identity |
| **PO-9** | Client factor mapping / recalculation | **A** | **No** — client users never map factors, modify mappings or trigger recalculation (any profile) |
| **PO-10** | Post-relationship client access | **B + E** | History retained; **controlled read-only** client access permitted subject to platform retention/access policy; termination must never look like deletion/migration; **retention period is NOT invented here** (§19 OQ-2) |

```text
STATUS OF THE TEN  =  RESOLVED / BINDING
EFFECT             =  the ten blockers raised by S2 §30.2 are cleared
RESIDUAL           =  §19 lists five genuinely-open secondary questions, each
                      with a safe default; none re-opens PO-1…PO-10.
```

---

### 4.2 PO-1 — Mode switching (B + D)

**Binding.**

1. A **consultant firm** initiates a **mode-change request**. The request is a
   commercial transaction, not a settings toggle.
2. The commercial transition takes effect at the appropriate **billing /
   renewal boundary**, unless CarbonTally **explicitly approves** an immediate
   transition.
3. There MUST be **no unrestricted mode-switch control** that bypasses
   CarbonTally's commercial/entitlement authority.
4. **Already-invited client users and existing relationships MUST NOT be
   silently broken** by a mode transition.
5. The implementation MUST define the transition behaviour **explicitly** and
   MUST preserve existing data and history.

**Design consequences.**

```text
 * S2's "no mode switcher" position is RETAINED (A1/A7/A11 report the mode as a
   statement of fact — they never switch it).
 * A11 MUST gain a REQUEST affordance: "Request a mode/plan change" →
   submitted to CarbonTally; states: requested | approved-effective-at-boundary
   | approved-immediate | declined.
 * A transition-impact statement is MANDATORY before submission and MUST name
   the effect on client logins (e.g. moving to Standard disables client logins
   while retaining all data — mirrors S3 §15's downgrade warning, minus the
   self-service confirmation).
 * The transition is NON-DESTRUCTIVE: client access profiles, client-user
   records, branding configuration and history are RETAINED, not deleted.
   A mode that does not permit client access renders the client plane as C11
   "paused" and MUST NOT delete client-user records.
```

**Forbidden.**

```text
 * A UI control that changes the firm's mode or entitlement directly.
 * Any transition that deletes client users, profiles, branding config or data.
 * Any transition effective immediately without an explicit CarbonTally
   approval record.
 * Any transition that leaves an invited client user in an undefined state.
```

---

### 4.3 PO-2 — Client-user invitations (A)

**Binding.**

1. Inviting client users is a **consultant-side action**.
2. Only **appropriately authorized consultant users** may invite client users,
   manage client-user access, and remove or suspend client-user access.
3. Client users do **not** automatically receive invitation authority.
4. This is NOT Organisation RBAC: the consultant firm remains the **operator**
   of consultant-managed clients.

**Design consequences.**

```text
 * A5's "[ + Invite client user ]" is a CONSULTANT action in every profile,
   including MANAGED (S2 §24 INVITE NOTE is now CONFIRMED, not assumed).
 * The invite/manage/remove capability MUST resolve through consultant
   RBAC/capability (§7) — never through "is a member of the consultant firm".
 * A client user who holds Owner/Admin in the client Organisation still gets
   NO invitation authority (client-org role does not confer it).
```

**Forbidden.**

```text
 * Any client-facing invite, user-management, or suspend/remove control.
 * Deriving invite authority from client-Organisation role or profile alone.
```

---

### 4.4 PO-3A — Branding granularity (A)

**Binding.**

1. **Firm-level branding only.** A consultant firm has **one** applicable
   branding configuration, subject to its commercial entitlement.
2. **No per-client brand overrides.**
3. Client-facing surfaces inherit the firm brand; they are never individually
   re-branded.

**Design consequences.**

```text
 * Resolves S2 §26.1 DIV-1 in favour of FIRM-scoped branding and against S3 §17
   per-client branding. S3 §17's per-client brand selector is OVERRULED.
 * A7 (firm branding configuration) is a FIRM record — one per firm, no
   Client column, no "applies to client X" control.
 * A3 (client roster) MAY show the inherited firm brand as read-only context;
   it MUST NOT offer an edit control.
 * Plane C always renders the firm brand derived from the firm — never a
   per-client brand lookup.
```

**Forbidden.**

```text
 * Any branding control keyed to a client Organisation.
 * Any client-level brand record, brand override table, or per-client logo.
```

---

### 4.5 PO-3B — White-Label availability (A)

**Binding.**

1. **White-Label presentation exists only in White-Label mode.**
2. It is **entitlement-gated** by the CarbonTally-controlled commercial
   configuration — it is not a free-standing add-on that any mode may enable.
3. A firm in Standard or Co-Branded mode MUST NOT be presented a white-label
   client experience even if a stored flag suggests otherwise.

**Design consequences.**

```text
 * S2's PO-3b request is answered: presentation is CAPPED BY MODE, not sold
   independently.
 * The brand-kind ladder (S2 §6) is now hard-gated: Standard → carbon_tally;
   Co-Branded → co_branded; White-Label → white_label. An out-of-mode brand
   kind MUST NOT render.
 * OBS-1 (stored white_label_enabled) MUST be capped at presentation/enforcement
   time by the firm's mode. Stored configuration MUST NOT be destroyed as part
   of the cap (see §18 IMPL-3).
```

**Forbidden.**

```text
 * Rendering a white-label client surface in Standard or Co-Branded mode.
 * Delivering white-label as an add-on independent of the mode.
 * Deriving entitlement to white-label from stored client/plan configuration
   without the mode check.
```

---

### 4.6 PO-4 — Managed profile and custom domain (C)

**Binding.**

| Mode | CarbonTally brand | Firm brand | Client login / portal | MANAGED profile | Custom domain |
|---|---|---|---|---|---|
| **STANDARD** | required | visible (firm's own surfaces) | not permitted | not permitted | not permitted |
| **CO-BRANDED** | retained | applied to client surfaces | permitted | **permitted** | not permitted |
| **WHITE-LABEL** | absent from client surfaces | applied | permitted | **permitted** | **permitted** (subject to entitlement/configuration) |

**Binding clauses.**

1. **MANAGED** is permitted in **Co-Branded** and **White-Label**; it is not
   excluded by the co-branded branding model.
2. **Custom domain** is a **White-Label-only** capability.
3. STANDARD has **no client login, no client portal, no managed plane**.
4. Legal/brand-attribution obligations for the platform remain subject to
   CarbonTally's own legal policy and MUST NOT be hard-coded by the
   implementation.

**Design consequences.**

```text
 * S2 §6 ladder and §27 "PO-gated" markers are RESOLVED: MANAGED ✓✓ (CB, WL),
   custom domain ✓ (WL only), and ✗ (Standard, Co-Branded).
 * S2 §30.2 PO-4 ("is white-label custom domain available at all?" — now yes,
   White-Label only) is closed.
 * Plane C MUST therefore exist only where the mode permits it; in STANDARD the
   client plane is not routable for that firm and MUST fail closed (§11).
 * Custom domain resolution MUST be entitlement-checked server-side, never from
   the hostname alone (see §12 and §17 F-9).
```

**Forbidden.**

```text
 * A managed/portal experience in Standard mode.
 * A custom domain for a Co-Branded or Standard firm.
 * Treating the resolved hostname as proof of entitlement.
```

---

### 4.7 PO-5 — Commercial configuration (C)

**Binding.**

1. The **three product modes are the architecture**. Pricing, plan names,
   seat counts, usage limits and packaging are a **separate commercial task**.
2. The **CarbonTally Admin Panel is the authoritative configuration surface**
   for commercial/entitlement configuration.
3. **Consultants cannot change their own entitlements.**
4. The UI MUST NOT contain hard-coded prices, seat counts, or invented limits.
5. Client branding/plan/usage surfaces MUST NOT imply that the **consultant**
   bills CarbonTally, or that CarbonTally bills the **managed client**.

**Design consequences.**

```text
 * The mode/entitlement boundary is enforced from server-side configuration
   (§6). The UI reports; it never becomes the source of truth.
 * S3 §14–15 (self-service plan chooser, prices, seat counts) is OVERRULED as
   an integration design: the chooser becomes a REQUEST flow with no invented
   values (PO-1 B+D).
 * A11's commercial block reads Admin-configured values; where nothing is
   configured it must show an honest "not configured"/"configured by
   CarbonTally" state — never a placeholder price.
 * Blocked operations that require entitlement render the locked/not-entitled
   pattern (S2 ID-8 / S3 §16) with an explanation of WHO can enable it
   (CarbonTally), never a self-service upgrade button.
```

**Forbidden.**

```text
 * Any price, currency, seat count, usage cap or plan name invented by an
   engineer, a designer, a seed script, a fixture, or a test.
 * Any consultant-facing control that alters the firm's own entitlement.
 * Any UI that implies a managed client holds a CarbonTally subscription.
 * Any frontend-only entitlement check treated as the security boundary.
```

---

### 4.8 PO-6 — Final approval authority (B + C)

**Binding.**

1. For a **consultant-managed** Organisation, a **consultant role MAY perform
   the final approval**.
2. Final approval MUST follow **consultant RBAC/capability** — it is a named
   capability, not an implicit consequence of having the relationship.
3. The blanket rule that only a customer **Owner** may give final approval
   **does NOT apply** to consultant-managed Organisations.
4. Approval authority remains **separated** from processing ability: the person
   who calculated is not automatically the person who may approve.

**Design consequences.**

```text
 * S1 §4 + S2 §30.2 PO-6 are now unblocked. The approval step MUST record and
   display WHICH capacity approved:
       "Approved by <actor> (Consultant — Firm Name)"   [managed]
       "Approved by <actor> (Client Owner — Client Ltd)" [direct]
 * A4 / C2 render the same approve control, with the actor's capacity named.
 * Where a client profile ALSO permits approval (COLLABORATIVE / MANAGED
   per the client role), the client approval remains valid within its profile.
 * The capability must be grantable/revocable per consultant role through
   consultant RBAC.
```

**Forbidden.**

```text
 * Enforcing "customer Owner only" for final approval on a managed client.
 * Allowing approval with no capability check ("anyone with the relationship
   may approve").
 * Recording an approval without actor identity AND capacity.
 * Letting a client user approve where their access profile does not permit it.
```

---

### 4.9 PO-7 — Ending the relationship (D)

**Binding.**

1. **Either party may initiate** ending a consultant–client relationship.
2. The action requires **appropriate authorization** and **explicit
   confirmation**.
3. It MUST be **audited**: who initiated, when, and the reason.
4. The **resulting access state must be defined** (see §14, §15).
5. Termination **must never delete or migrate** the client Organisation or its
   data, and must never be presented as doing so.
6. It MUST NOT break auditability, evidence or history.

**Design consequences.**

```text
 * NEW UI required in Plane A/B: a relationship-termination workflow with
   authorization, confirmation, reason capture and audit trail. S2 had ONLY
   C11 "access paused" — that is now insufficient.
 * S2 NOT-BUILT-2 (no client-side "change consultant" control) is PARTIALLY
   AFFECTED: a client-side initiation path must exist in some form; the exact
   entry point and confirmation semantics are §19 OQ-1.
 * The termination state machine is NOT open: initiate → authorize → confirm →
   record → transition access (non-destructive).
 * Termination MUST NOT be reachable by URL manipulation, and MUST NOT be
   executable without confirmation.
```

**Forbidden.**

```text
 * Deleting, truncating, archiving-away or migrating the Organisation on
   termination.
 * Silently revoking access with no audit record.
 * Presenting termination with wording such as "your data has been deleted".
 * Terminating on a single click with no confirmation and no authorization.
```

---

### 4.10 PO-8 — Plane C path (A)

**Binding.**

1. The client-facing plane path is **`/portal/:clientId/*`**.
2. `:clientId` continues to identify the **Organisation**, and the
   organisation/authorization boundary stays **explicit** in the route.
3. Branding or a custom domain is **never** the security identity — it is
   presentation only.

**Design consequences.**

```text
 * S2 §30.2 PO-8 and S2 ID-4 are closed: /portal/:clientId/* is confirmed.
 * Routes MUST NOT be flattened to /portal/* for "cleaner" URLs.
 * A branded or custom-domain entry MUST resolve to the same organisation-scoped
   authorization checks. Hostname does not grant access.
 * Client-side navigation MUST NOT expose a client switcher; a client user is
   bound to their organisation(s) by authorization, not by a URL segment alone.
```

**Forbidden.**

```text
 * Any path change that removes the organisation identifier from the client
   plane route family.
 * Any authorization decision derived from a brand, hostname or subdomain.
```

---

### 4.11 PO-9 — Client factor mapping / recalculation (A)

**Binding.**

1. **Client users MUST NOT** map factors.
2. **Client users MUST NOT** modify mappings.
3. **Client users MUST NOT** trigger recalculation.
4. This applies to **all** client access profiles, including MANAGED and
   COLLABORATIVE, and including a client user holding the client-Organisation
   **Owner** role.

**Design consequences.**

```text
 * S2 §24 capability matrix △ rows are resolved to ✗ (not permitted):
       "Map factors / edit mappings"     → ✗ for every client profile
       "Trigger recalculation"           → ✗ for every client profile
 * Plane C MUST NOT contain a mapping editor, factor search, factor assignment
   control, or a recalculation trigger in any profile.
 * These capabilities remain on the **consultant/operator** side (Plane A/B).
 * If a client "change" would previously have triggered recalculation, the
   client action must become a REQUEST/review signal, not a recalculation.
```

**Forbidden.**

```text
 * Accepting a mapping or recalculation write from a client-plane session at the
   API layer (server-side denial is mandatory, not merely UI absence).
 * Treating the client-Organisation Owner role as sufficient for mapping.
```

---

### 4.12 PO-10 — Post-relationship client access (B + E)

**Binding.**

1. History is **retained**.
2. **Controlled read-only** client access is permitted, **subject to platform
   retention/access policy**.
3. Termination **must never look like deletion or migration** — the client must
   still be able to see their historical data.
4. The **retention period** is NOT decided by this document and MUST NOT be
   invented (§19 OQ-2). It is governed by the existing configurable retention
   controls (N3 / S1 retention domain).

**Design consequences.**

```text
 * A NEW post-relationship access state is required, distinct from OFF and from
   C11 "suspended": a RETAINED / READ-ONLY historical state.
 * C11 copy MUST be revised: "no longer your consultant — your data has not been
   deleted; access is now read-only under platform retention policy."
 * Post-relationship read-only access MUST be enforced server-side and MUST
   NOT be a client-side flag.
 * Retention enforcement MUST NOT weaken auditability, evidence or required
   history (AGENTS.md §42).
```

**Forbidden.**

```text
 * Any post-termination experience that implies the data was deleted, exported
   away, or moved to another organisation.
 * Deletion of history at termination.
 * Hard-coding a retention duration into the product.
 * Post-relationship WRITE access.
```

---

## 5. Final consultant business model

### 5.1 The five statements that define the model

```text
 B1. THE CONSULTANT FIRM IS A CARBONTALLY CUSTOMER.
     The firm buys CarbonTally. It has a subscription, a plan, seats, a
     commercial mode and an entitlement set — all set by CarbonTally (PO-5).

 B2. THE CLIENT IS A NORMAL ORGANISATION.
     A consultant-managed client is an ordinary organisation in the V3
     Organisation model: same tables, same relationships, same facility/asset
     master data, same workflow, same provenance. It is NOT a special type and
     NOT a sub-tenant structure invented for consultants.

 B3. THE CONSULTANT IS AN OPERATOR, NOT A VIEWER.
     A consultant with an authorized relationship operates the client's
     workspace: upload, process, map, validate, calculate, review, report, and
     (per PO-6) perform final approval. The consultant is NOT read-only.

 B4. ACCESS IS BY RELATIONSHIP + CAPABILITY, NEVER BY MEMBERSHIP INJECTION.
     A consultant is not made a member of the client organisation. Identity and
     authorization flow from the consultant-side relationship plus the
     consultant's capability in the firm (PO-2, PO-6). Two different firms'
     consultants must never resolve to each other's clients.

 B5. THE RELATIONSHIP IS COMMERCIAL AND REVOCABLE — NEVER DATA-BEARING.
     The relationship determines ACCESS. It never owns, holds, migrates or
     deletes client data. Ending it (PO-7) is an access transition; the data
     stays exactly where it is (PO-10).
```

### 5.2 Three product modes (commercial model)

| | STANDARD | CO-BRANDED | WHITE-LABEL |
|---|---|---|---|
| CarbonTally brand | required | retained | absent from client surfaces |
| Firm brand on its own surfaces | yes | yes | yes |
| Client login / portal | ✗ | ✓ | ✓ |
| MANAGED client profile | ✗ | ✓ | ✓ |
| Custom domain | ✗ | ✗ | ✓ (entitlement) |
| Client-facing branding | n/a (no client plane) | firm brand + CarbonTally | firm brand only |
| Typical use | consultant operates clients in its own workspace | consultant gives clients a branded portal | consultant presents CarbonTally as invisible |

> These three modes are **architecture** (PO-5). Prices, plan names, seat counts
> and limits are **not** architecture and are **not** in this document.

### 5.3 What a "consultant-managed client" is, concretely

```text
 * An ordinary organisation row, owned by the client (or by the consultant firm
   as the operating party, subject to the existing ownership model in S1).
 * Linked to the consultant firm by an explicit CONSULTANT–CLIENT RELATIONSHIP.
 * Carries (or resolves to) exactly ONE consultant ACCESS PROFILE for the
   client-side users: OFF / READ_ONLY / COLLABORATIVE / MANAGED.
 * May have CLIENT USER records issued by the consultant (PO-2) — these are
   client-side identities, NOT organisation members injected by the consultant.
 * Is billed to the CONSULTANT (or not at all), never directly to CarbonTally
   while managed (S1 §7).
```

### 5.4 Billing separation (binding)

```text
 * The consultant firm is the CarbonTally commercial counterparty.
 * A managed client is NOT a CarbonTally subscriber.
 * Plane C MUST NOT show the client a CarbonTally subscription, invoice, plan
   or upgrade control.
 * The consultant's billing state and the client's data state are SEPARATE
   concerns: an unpaid consultant subscription must never present to the client
   as a client data problem, and client data must never be held hostage to a
   consultant billing dispute without an explicit CarbonTally decision.
```

### 5.5 Tenancy invariants (non-negotiable)

```text
 INV-A  Consultant A can never reach Consultant B's clients.
 INV-B  Client A can never reach Client B's organisation.
 INV-C  A client user can never reach another client's organisation.
 INV-D  A consultant can never reach an unlinked organisation.
 INV-E  The client plane is never usable for an organisation link that is not
        ACTIVE or RETAINED-READ-ONLY.
 INV-F  No decision is ever taken from a hostname, subdomain, brand, hidden
        button, disabled control or route guard alone.
 INV-G  Subscription/entitlement is never a substitute for capability, and
        capability is never a substitute for relationship.
```

> INV-A…INV-F are the security spine of this model. Each has a corresponding
> negative test in §20.4.

---

## 6. Commercial / admin configuration model

### 6.1 The five boundaries — do not collapse them

```text
 +-----------------------------------------------------------------------+
 | A. PRODUCT MODE            STANDARD | CO-BRANDED | WHITE-LABEL        |
 |    What the firm *is*, commercially. Architecture (PO-5).             |
 +-----------------------------------------------------------------------+
 | B. COMMERCIAL ENTITLEMENT  what the firm has *bought*: plan, seats,   |
 |    enabled capabilities (e.g. custom domain), limits, renewal date.   |
 |    THE AUTHORITATIVE SOURCE IS THE CARBONTALLY ADMIN PANEL (PO-5).    |
 |    The consultant CANNOT change it. The frontend only REPORTS it.     |
 +-----------------------------------------------------------------------+
 | C. CONSULTANT RBAC         what a *person in the firm* may do:        |
 |    capabilities granted to the firm's roles. Firm-internal authority. |
 +-----------------------------------------------------------------------+
 | D. CLIENT ACCESS PROFILE   what the *client's users* may do, per       |
 |    relationship: OFF | READ_ONLY | COLLABORATIVE | MANAGED.            |
 +-----------------------------------------------------------------------+
 | E. CARBONTALLY AUTHORITY   what internal CarbonTally staff may do:     |
 |    Operator | Reviewer | QC | Staff Admin | System Admin.              |
 +-----------------------------------------------------------------------+
```

**The single most important rule in this section:**

```text
 PROFILE = CEILING.   ROLE/CAPABILITY = AUTHORITY.
 EFFECTIVE_PERMISSION(actor, org)
     = CAPABILITY(actor, firm)  ∩  PROFILE(client, org)  ∩  ENTITLEMENT(firm)
 A relationship existing grants NOTHING on its own.
 "Has relationship → full access" is FORBIDDEN.
```

### 6.2 Resolution order (mandatory, server-side)

```text
 1. Identify the AUTHENTICATED identity (customer user | consultant user |
    client user | PE user | CarbonTally staff).
 2. Resolve the ORGANISATION CONTEXT (which organisation, how the actor is
    connected to it: direct customer | consultant relationship | assignment).
 3. Resolve the FIRM ENTITLEMENT (mode + configured capabilities) from the
    ADMIN-CONTROLLED source. If nothing is configured → fail closed/explicit,
    never "assume enabled".
 4. Resolve the CONSULTANT CAPABILITY for this actor in this firm.
 5. Resolve the CLIENT ACCESS PROFILE for this relationship (client side only).
 6. Compute the effective permission as the INTERSECTION (see 6.1).
 7. Enforce, then record where the action is audit-relevant.
 Steps 3–6 MUST be server-side. A UI that hides a control is NOT enforcement.
```

### 6.3 What the CarbonTally Admin Panel owns (PO-5)

| Concern | Owner | Consultant may change? |
|---|---|---|
| Product mode of a firm | CarbonTally Admin | **No** (may *request*, PO-1) |
| Plan / subscription state | CarbonTally Admin | No |
| Seat counts and usage limits | CarbonTally Admin | No |
| Custom-domain entitlement | CarbonTally Admin | No (may request) |
| White-label entitlement | CarbonTally Admin (mode-capped, PO-3B) | No |
| Retention configuration | CarbonTally Admin (N3) | No |
| Firm branding *content* (logo/colours) | Consultant firm (within entitlement) | **Yes** |
| Consultant roles/capabilities | Consultant firm (within its entitlement) | Yes |
| Client access profile per client | Consultant firm | Yes |
| Client user accounts | Consultant firm (PO-2) | Yes |
| Pricing figures / plan names | **Outside this document** (separate commercial task, PO-5) | n/a |

> **Anti-duplication rule.** There must be exactly ONE authoritative source for
> entitlement. A second, consultant-writable copy of "what the firm has bought"
> is forbidden, because it is precisely the mechanism by which a consultant
> could silently grant themselves an unpaid capability.

### 6.4 Relationship to the Admin Control Plane (S8, CL-66)

```text
 * The CarbonTally Admin Control Plane is a SEPARATE privileged surface. It is
   NOT the customer/consultant application and MUST NOT be reachable from it.
 * Commercial/entitlement/retention configuration belongs to the Admin Plane.
 * The consultant application CONSUMES the results; it never writes them.
 * Files, routes and navigation of the two surfaces must remain separated
   (AGENTS.md §31).
 * Admin-side changes MUST be persistence-backed and auditable; they must not be
   frontend state.
```

### 6.5 Failure modes that are mandatory

```text
 FM-1  Nothing configured for the firm
       → explicit "not configured / contact CarbonTally" state.
       → NEVER "assume the highest tier" and NEVER "assume enabled".
 FM-2  Storage conflict between a stored flag and the mode (e.g. OBS-1
       white_label_enabled=true on a Standard firm)
       → the MODE wins at presentation/enforcement. The stored value is not
         trusted and is not destroyed (IMPL-3).
 FM-3  Entitlement service unavailable
       → fail closed for privileged/presentation-gated features, with a clear
         error; do not silently degrade to permissive.
 FM-4  Consultant asks for a capability they do not have
       → locked/not-entitled UI naming the owner of the decision
         (CarbonTally), never a self-service upgrade control.
 FM-5  Client plane requested for a link that is not ACTIVE
       → the defined non-active state (§11.4, §15.2). Never a data-less error
         that looks like deletion.
```

### 6.6 Implementation decisions delegated to the next task (PO input NOT required)

These are engineering choices. They carry a **safe default** so the implementer
never has to guess a product/commercial/security rule. None of them may be used
to widen access.

| ID | Matter | Safe default the implementer must take |
|---|---|---|
| **IMPL-1** | Persisted name of the "no client access" profile — S1 says `NONE`, S2 says `OFF` | Reuse **exactly one** existing persisted value; if the model already stores a "no access" state, reuse it and treat `NONE`/`OFF` as one concept. Do **not** add a second synonymous profile. |
| **IMPL-2** | Where the client access profile is stored (column on the relationship vs separate table) | Extend the **existing** relationship model if it already supports a status/profile column; add a table only if it does not. Migration required either way. |
| **IMPL-3** | Existing stored white-label flag on non-White-Label firms (S2 OBS-1) | Cap at presentation/enforcement by mode. **Do not delete or mutate** stored configuration; surface it for Admin reconciliation. |
| **IMPL-4** | `client_portal_url` exposed with nothing behind it (S2 OBS-2) | Either implement the Plane C route family as specified (§11) or render the value as unavailable. **Never** show a URL that 404s or dead-ends. Decide, and record the decision. |
| **IMPL-5** | Whether the consultant approval capability is a new capability or reuses an existing one | Inspect the existing capability model first. If no clean approval capability exists, introduce the **minimum coherent** one (S1 §4 fallback) and grant it only to roles that already hold approval-equivalent authority. Do not grant it to all firm users. |
| **IMPL-6** | Mode-transition behaviour for already-invited client users (PO-1) | Non-destructive: retain client-user records and profiles; render the client plane in the defined "paused" state; notify. Never delete, never orphan. |
| **IMPL-7** | Enforcement rollout for existing firms | Enforcement must be **built and correct**; rollout to existing demo/investor data must be non-destructive and must not silently break legitimate demo relationships (AGENTS.md §55). |
| **IMPL-8** | Client "change request" signalling after PO-9 removal of mapping/recalc | Client submits a **request/review signal** routed to the consultant; no recalculation, no mapping write, no direct data mutation. |

```text
 RULE: an IMPL item may NEVER be resolved in the direction of "grant more
 access", "delete data", "hard-code a commercial value", or "trust the client".
```

---

## 7. Consultant RBAC / capability model

### 7.1 Identity types (must remain distinct)

```text
 I1  CONSULTANT USER      a person belonging to a consultant FIRM.
 I2  CLIENT USER          a client-side identity issued by the consultant (PO-2),
                          bound to a client Organisation in Plane C.
 I3  DIRECT CUSTOMER USER a normal organisation user of a non-consultant org.
 I4  PE USER              processing-entity staff (assignment-scoped).
 I5  CARBONTALLY STAFF    Operator | Reviewer | QC | Staff Admin | System Admin.
 A person is ONE of these in a given session context. The implementation must
 not resolve one type's authority from another type's data.
```

### 7.2 The resolution chain for a consultant action

```text
 ACTOR
   → FIRM MEMBERSHIP                (is this person in the firm, and active?)
   → CONSULTANT–CLIENT RELATIONSHIP (does the firm link to this organisation,
                                     and is the link ACTIVE / RETAINED?)
   → FIRM ENTITLEMENT               (mode + configured capabilities; §6)
   → FIRM ROLE                      (what role does this person hold?)
   → CAPABILITY                     (does that role hold the required capability?)
   → ACTION                         (the specific operation requested)
   → ORGANISATION SCOPE             (is the target the organisation resolved?)
 ALL of these must be satisfied. Any one failing = DENY.
```

### 7.3 Capability set (aligned to S1 §3 / S2 §13.2 — not invented)

```text
 CAP-VIEW-CLIENT        see a client in the roster / open its workspace
 CAP-UPLOAD             upload documents into a client's workspace
 CAP-PROCESS            run automatic and/or manual processing
 CAP-MAP                map factors / edit mappings
 CAP-VALIDATE           resolve validation issues
 CAP-CALCULATE          run calc / recalculate
 CAP-REVIEW             act in the review workflow
 CAP-APPROVE            perform FINAL approval (PO-6; see IMPL-5)
 CAP-REPORT             generate/access reports
 CAP-INVITE-CLIENT-USER invite/manage/remove CLIENT USERS (PO-2)
 CAP-MANAGE-CLIENTS     create/manage client relationships & access profiles
 CAP-MANAGE-FIRM-USERS  manage consultant team members
 CAP-CONFIGURE-BRAND    edit the FIRM's branding content (PO-3A)
 CAP-REQUEST-COMMERCIAL submit a mode/entitlement REQUEST (PO-1) — request only
```

```text
 MANDATORY CAPABILITY PROPERTIES
  * Grantable/revocable per firm role by the firm.
  * NEVER inferred from "has the relationship".
  * NEVER inferred from the client-side profile (that is the CEILING, §6.1).
  * Approval (CAP-APPROVE) MUST be separable from processing/mapping, so one
    person need not both produce and approve.
```

### 7.4 Prohibitions

```text
 * Any authorization path that grants a capability because a relationship row
   exists (this is S6/S7 finding F-1 — still open, §17).
 * Any capability check performed only in the frontend.
 * Any "consultant = read-only viewer" assumption (S1 explicitly rejects it).
 * Any capability granted from the CLIENT organisation's role data.
 * Any capability granted because the actor is staff, unless the staff role
   genuinely holds it (Staff Admin != System Admin; AGENTS.md §14).
```

---

## 8. Client access-profile model

### 8.1 The profiles

| Profile | Meaning | Client may log in? |
|---|---|---|
| **OFF** *(== NONE in S1)* | No client access. Consultant works the data alone. | No |
| **READ_ONLY** | Client sees permitted data and reports. No writes. | Yes |
| **COLLABORATIVE** | Client sees data **and may contribute** within permitted limits. | Yes |
| **MANAGED** | Client sees a curated/managed view; consultant operates the lifecycle. | Yes |
| **POST-RELATIONSHIP (READ-ONLY RETAINED)** | Relationship ended (PO-7); history visible read-only under platform retention policy (PO-10). | Yes, read-only |

```text
 OFF and POST-RELATIONSHIP are DIFFERENT STATES with different messaging.
 OFF      = "the consultant has not given you access."
 RETAINED = "the relationship has ended; your data was NOT deleted."
```

### 8.2 Capability matrix — client-side, post-PO amendments

Legend: ✓ permitted · ✗ not permitted · — not applicable (no login).

| Client capability | OFF | READ_ONLY | COLLABORATIVE | MANAGED | RETAINED |
|---|---|---|---|---|---|
| Log in to Plane C | — | ✓ | ✓ | ✓ | ✓ (read-only) |
| View own organisation data | — | ✓ | ✓ | ✓ | ✓ |
| View reports / outputs | — | ✓ | ✓ | ✓ | ✓ |
| View evidence & provenance | — | ✓ | ✓ | ✓ | ✓ |
| **Invite/remove users (PO-2)** | — | ✗ | ✗ | ✗ | ✗ |
| Edit master data (facilities/assets/…) | — | ✗ | ✓ *(within limits)* | ✗ | ✗ |
| Upload documents | — | ✗ | ✓ *(within limits)* | ✗ | ✗ |
| Correct/annotate own submitted data | — | ✗ | ✓ | ✗ | ✗ |
| Comment / respond to a query | — | ✓ | ✓ | ✓ | ✗ |
| Approve (final) (PO-6) | — | ✗\* | ✓\* | ✓\* | ✗ |
| **Map factors / edit mappings (PO-9)** | — | ✗ | ✗ | ✗ | ✗ |
| **Trigger recalculation (PO-9)** | — | ✗ | ✗ | ✗ | ✗ |
| Change branding (PO-3A) | — | ✗ | ✗ | ✗ | ✗ |
| See/buy a CarbonTally plan (S1 §7) | — | ✗ | ✗ | ✗ | ✗ |
| Change consultant / own access profile | — | ✗ | ✗ | ✗ | ✗ |

```text
 * = Client-side approval is ADDITIONALLY gated by the CLIENT role the user
     holds and by the consultant's configuration. It is never inferred. Where
     the PO-6 consultant path is used, the CONSULTANT capability is the
     authority. If a client approval step exists, it is an explicit
     role+profile decision, never a consequence of "can see the page".
```

### 8.3 Profile rules

```text
 P-1  The profile is a CEILING, not a grant. It can only REDUCE what the
      consultant role could do on the client's behalf; it never confers
      consultant capability onto a client user.
 P-2  PO-9 rows are ✗ in EVERY profile, unconditionally.
 P-3  PO-2: no client user, in any profile, may invite/manage/remove users.
 P-4  The profile is set by the CONSULTANT firm (CAP-MANAGE-CLIENTS), per client.
 P-5  The profile can never be changed from Plane C, by URL, or by the client.
 P-6  Profile enforcement is SERVER-SIDE (§20.4 negative tests).
 P-7  A profile change MUST be audited (who, when, from → to).
 P-8  A profile change MUST NOT delete client data or client-user records.
 P-9  OFF and RETAINED must never share copy or iconography.
```

### 8.4 Profile × mode interaction

| | STANDARD | CO-BRANDED | WHITE-LABEL |
|---|---|---|---|
| OFF | consultant-only work | permitted | permitted |
| READ_ONLY | n/a (no client plane) | permitted | permitted |
| COLLABORATIVE | n/a | permitted | permitted |
| MANAGED | n/a (PO-4) | **permitted (PO-4)** | **permitted (PO-4)** |
| RETAINED | n/a | permitted | permitted |

```text
 In STANDARD the client plane does not exist for the firm, so any client-facing
 profile resolves to "no client plane". This is ENFORCED, not merely hidden.
```

---

## 9. UI/UX acceptance matrix

Verdict vocabulary:

```text
 ACCEPT AS DESIGNED            the design is adopted unchanged; implement it.
 ACCEPT WITH PO AMENDMENT      adopted, but PO-1…PO-10 change a detail; the
                               amendment is stated in §10.
 REQUIRES DESIGN CHANGE        the design is insufficient or now wrong; the
                               required change is stated in §10.
 OPEN (PO-DEPENDENT)           cannot be finalised; see §19.
 REJECTED                      explicitly overruled; do not implement.
```

| # | Design area | Design ref | Verdict | Reason / required amendment |
|---|---|---|---|---|
| **1** | Consultant shell & navigation (two-plane model) | S2 §9, §13, DELTA-13…15 | ACCEPT AS DESIGNED | Two-plane top navigation with explicit "where am I" context is sound and matches AGENTS.md §38/§76. Add the Plane C entry point only where the mode permits it (PO-4). |
| **2** | Consultant Hub / dashboard (A1) | S2 §9, §13.1 | ACCEPT AS DESIGNED | Roster-first hub with the commercial mode stated as **fact**. No switcher (PO-1). |
| **3** | Client roster (A3) | S2 §9, §13.3, DELTA-1/2 | ACCEPT WITH PO AMENDMENT | Adopted with richer operational context (AGENTS.md §37). Firm brand may appear **read-only**; **no** per-client brand control (PO-3A). |
| **4** | Org workspace reuse (Plane B) | S2 §12 DELTA-6…12, S4 | ACCEPT AS DESIGNED | D-20 reuse of the Organisation workspace is correct; the client's data is worked in the same surface (B2). |
| **5** | Client detail / "manage client" (A5) | S2 §13.4, §24 INVITE NOTE | ACCEPT WITH PO AMENDMENT | Invite is consultant-only (**confirmed**, PO-2). Access-profile selector present. **No** brand selector (PO-3A). |
| **6** | Firm branding configuration (A7) | S2 §11, §26.1 DIV-1 | ACCEPT WITH PO AMENDMENT | Firm-scoped, one config per firm (**PO-3A**). White-label controls appear **only** in White-Label mode (PO-3B), entitlement-gated. |
| **7** | Commercial / subscription block (A11) | S2 §13.6, §17.10, S3 §14–15 | ACCEPT WITH PO AMENDMENT | Reports Admin-configured facts; **no** invented prices/limits (PO-5). Adds "Request a mode/plan change" with boundary timing and transition impact (PO-1). Self-service chooser **REJECTED**. |
| **8** | Locked / not-entitled pattern (ID-8) | S2 §14, S3 §16 | ACCEPT AS DESIGNED | Correct pattern; must name CarbonTally as the enabling party and must never be the *only* enforcement (AGENTS.md §44). |
| **9** | Client portal shell / navigation (Plane C) | S2 §16, §17.1 | ACCEPT WITH PO AMENDMENT | Path family confirmed `/portal/:clientId/*` (PO-8). No client switcher, no plan, no branding control, no mapping, no recalculation (PO-9). Branding is the firm's, from the firm (PO-3A). |

| **10** | Client portal dashboards C1…C5 | S2 §17.2–17.6 | ACCEPT WITH PO AMENDMENT | Adopted. C2/C4 must render the **capacity** of approvals (PO-6). All views respect the access profile ceiling (PO-9/PO-2). |
| **11** | Client messaging (C6) | S2 §17.7, N1 | ACCEPT AS DESIGNED | N1 boundaries retained; no unrestricted Customer↔PE channel; server-side enforcement. Post-termination messaging policy = §19 OQ-4. |
| **12** | Client plans / billing (C10) | S2 §17.10, S1 §7 | ACCEPT AS DESIGNED | Locked/explained state is correct and now mandated by PO-4/PO-5: the client is never billed by CarbonTally. |
| **13** | Client "access paused" (C11) | S2 §17.11 | **REQUIRES DESIGN CHANGE** | Must be split into **two** states: *suspended/OFF* (relationship exists, access withdrawn) and *post-relationship retained read-only* (PO-10). Copy must never imply deletion. |
| **14** | Access-profile screen / selector | S2 §24, §13.4 | ACCEPT WITH PO AMENDMENT | Matrix adopted with the PO-9 rows forced to ✗ and invite forced to ✗ for clients (PO-2). INVITE NOTE becomes a confirmed rule, not a note. |
| **15** | Support / messages entry points (Plane C) | S2 §17.7, §17.12 | ACCEPT AS DESIGNED | Retained. |
| **16** | Security guards, deep-link & cross-tenant failure UX | S2 §25 | ACCEPT AS DESIGNED | Generic not-found, no existence disclosure, no UUID leakage; must correspond to real server-side denial (INV-A…INV-F). |
| **17** | Consultant/operator provenance display (DELTA-16/18) | S2 §22, §30.1 | ACCEPT AS DESIGNED | Recording and showing who acted, in what capacity, is required for PO-6 and PO-7 audit. |
| **18** | Client/organisation separation (GAP-7, D-3) | S2 §8.3, §28 GAP-7 | ACCEPT AS DESIGNED | Client-user record distinct from organisation membership; no consultant injection into `organization_members`. Confirmed by PO-2. |

### 9.1 Verdict roll-up

```text
 ACCEPT AS DESIGNED ............ 10  (rows 1,2,4,8,11,12,15,16,17,18)
 ACCEPT WITH PO AMENDMENT ......  7  (rows 3,5,6,7,9,10,14)
 REQUIRES DESIGN CHANGE ........  1  (row 13 — client "access paused" must split)
 REJECTED (elsewhere in design) .  2  (per-client branding; self-service plan chooser)
 OPEN (PO-DEPENDENT) ...........  0  (the design's own PO blockers are all answered)
```

### 9.2 Design elements explicitly rejected

| Element | Source | Rejected because |
|---|---|---|
| Per-client brand selector / per-client logo | S3 §17 | PO-3A (A): firm-level branding only |
| Self-service plan/mode chooser with prices and seats | S3 §14–15 | PO-1 (B+D) + PO-5 (C): request flow; no invented values |
| Client-side "edit mapping" / "recalculate" affordance | S2 §24 △ rows | PO-9 (A): never permitted for clients |
| Client-side invite/manage-user control | implied by symmetry | PO-2 (A): consultant-side only |
| Any client-facing plan/upgrade/subscription control | S3 §17 | S1 §7 + PO-5: client is not billed by CarbonTally |
| "Change consultant" client-side switcher **as designed (NOT-BUILT-2)** | S2 §17.12 | PO-7 D requires a client-initiated path in *some* form; the *mechanism* is §19 OQ-1. The prohibition on a flipping/toggling control stands. |

---

## 10. UI/UX changes required from the PO decisions

Each delta is a **required change** to the design material before/while
implementing. `MUST` items are contract; `MAY` items are permitted refinements.

### 10.1 Blocking / structural deltas

```text
 DELTA-9   Re-scope the client portal to PO-8 + PO-9.
           Path family = /portal/:clientId/*.
           REMOVE any client-side mapping editor, factor search, factor
           assignment or recalculation trigger, in EVERY profile.
           These are now consultant/operator-only capabilities.

 DELTA-11  Commercial reporting gains a REQUEST affordance (PO-1).
           A11 must present the mode as FACT and offer "Request a mode/plan
           change". Before submission it MUST show the transition impact,
           including the effect on existing client logins. The request is
           submitted to CarbonTally; the consultant cannot self-approve it.
           States: requested | approved-effective-at-boundary |
                   approved-immediate | declined.
           The self-service plan chooser (S3 §14–15) is REMOVED.

 DELTA-13  Access-profile matrix is PO-corrected (PO-2 + PO-9).
           Invite/manage users ................ ✗ for clients (consultant-only)
           Map factors / edit mappings ........ ✗ for clients (all profiles)
           Trigger recalculation .............. ✗ for clients (all profiles)
           Everything else unchanged from S2 §24.

 DELTA-14  C11 splits into TWO distinct states.
           (a) ACCESS SUSPENDED / OFF — relationship exists, access withdrawn.
           (b) POST-RELATIONSHIP RETAINED — relationship ended, history visible
               read-only under platform retention policy (PO-10).
           Copy MUST state that data was NOT deleted and NOT migrated.

 DELTA-15  NEW: relationship termination UI (PO-7).
           Plane A/B surface: initiate → authorize → confirm → reason →
           record → access transition. Auditable. Non-destructive.
           The client-side initiation entry point is §19 OQ-1.

 DELTA-16  Approval UI names the approving actor's CAPACITY (PO-6).
           "Approved by <actor> (Consultant — <Firm>)"  or
           "Approved by <actor> (Client Owner — <Client>)".

 DELTA-17  White-label controls are mode-gated in the UI (PO-3B).
           The white-label presentation options appear ONLY in White-Label
           mode; in Standard/Co-Branded they are absent or render the
           locked/not-entitled pattern naming CarbonTally as the enabler.

 DELTA-18  Branding screen is FIRM-scoped only (PO-3A).
           No Client column, no "applies to client" control, no per-client logo.
```

### 10.2 Adopted from the design without change (already PO-correct)

```text
 DELTA-1..8, DELTA-10, DELTA-12  (adopted; see S2 §30.1)
 * Two-plane navigation & context    (DELTA-13..15 naming aside)
 * Roster-first hub
 * Workspace reuse (D-20)
 * Locked/not-entitled pattern (ID-8)
 * Generic cross-tenant failure UX (S2 §25)
 * Provenance/actor display
 * No mode switcher as a *control*
 * No client switcher in Plane C
 * No billing/plan surface in Plane C for the client
```

### 10.3 Design elements that MUST NOT be built

```text
 NB-1  per-client brand override / per-client logo
 NB-2  self-service plan or mode switcher with prices/seats
 NB-3  client-side mapping edit / recalculation trigger
 NB-4  client-side user invitation / user management
 NB-5  a client-side "flip consultant" toggle (an audited initiation path is
       still required — §19 OQ-1)
 NB-6  any UI showing a CarbonTally subscription, invoice or plan to a managed
       client
 NB-7  any control granting a consultant their own entitlement
 NB-8  any placeholder/hard-coded price, seat count or usage limit
 NB-9  any experience that presents relationship termination as data deletion
```

---

## 11. Plane C contract

### 11.1 Path and identity

```text
 ROUTE FAMILY   /portal/:clientId/*                     (PO-8 A — binding)
 :clientId      identifies the CLIENT ORGANISATION.
 IDENTITY       the authenticated CLIENT USER (I2), issued by the consultant.
 AUTHORITY      the CONSULTANT–CLIENT RELATIONSHIP + the ACCESS PROFILE.
 PRESENTATION   the FIRM's brand (firm-scoped, PO-3A), where the mode permits.
```

### 11.2 Plane C MUST

```text
 MUST-1  Resolve the organisation from :clientId AND the authenticated client
         user's authorization. Both must agree.
 MUST-2  Enforce the ACCESS PROFILE server-side on every read and write.
 MUST-3  Deny factor mapping, mapping edits and recalculation, always (PO-9).
 MUST-4  Deny user invitation/user management, always (PO-2).
 MUST-5  Hide and deny any CarbonTally plan/billing/subscription surface
         (S1 §7, PO-5).
 MUST-6  Render the firm's brand from the firm record; never from a per-client
         brand record (PO-3A).
 MUST-7  Show organisation-scoped data only; never leak other clients.
 MUST-8  Provide a clear non-active state for links that are not ACTIVE
         (§11.4).
 MUST-9  Survive a deep link to a foreign :clientId with a generic,
         non-disclosing failure (no existence oracle).
 MUST-10 Render the "no further consultant" / end-of-relationship state per
         PO-10 without implying deletion (§15).
```

### 11.3 Plane C MUST NOT

```text
 MUSTNOT-1  Provide a client switcher or any cross-client navigation.
 MUSTNOT-2  Provide a consultant-level workspace, processing, mapping,
            validation or calculation capability.
 MUSTNOT-3  Provide an access-profile selector, branding control, or any
            control that changes the consultant relationship.
 MUSTNOT-4  Render a CarbonTally-branded client experience in WHITE-LABEL mode,
            or a white-label experience outside WHITE-LABEL mode (PO-3B).
 MUSTNOT-5  Exist at all for a STANDARD-mode firm (PO-4).
 MUSTNOT-6  Treat the hostname/subdomain/brand as authorization.
 MUSTNOT-7  Show raw UUIDs where a human-readable relationship is available
            (AGENTS.md §34/§75).
```

### 11.4 Non-active states on Plane C (explicit, non-disclosing vs explicit)

```text
 LINK ACTIVE                    → full profile experience.
 LINK SUSPENDED (OFF)           → "Access to this workspace is currently
                                   paused. Contact <Firm>." (no data loss claim)
 LINK TERMINATED (RETAINED)     → "Your engagement with <Firm> has ended. Your
                                   historical data has NOT been deleted and
                                   remains available read-only under our
                                   retention policy." + read-only history view
                                   (PO-10). Retention duration = §19 OQ-2.
 FIRM NOT ENTITLED / STANDARD   → Plane C is not routable for this firm.
                                 Fail closed with a clear, generic message.
 CLIENT USER REVOKED            → sign-in denied; nothing about the org disclosed.
 EXISTENCE / CROSS-TENANT PROBE → generic not-found. No confirmation that the
                                 organisation exists.
```

---

## 12. Branding contract

### 12.1 Granularity (PO-3A)

```text
 ONE BRAND PER FIRM. There is no per-client branding.
 The firm's brand configuration is a SINGLE record belonging to the firm.
 Every client surface of that firm renders the SAME brand.
```

### 12.2 Brand availability by mode (PO-3B + PO-4)

| Brand kind | STANDARD | CO-BRANDED | WHITE-LABEL |
|---|---|---|---|
| CarbonTally brand | required | retained | **absent from client surfaces** |
| Firm brand on firm's own surfaces | yes | yes | yes |
| Firm brand on client surfaces | n/a (no client plane) | yes | yes |
| Custom domain | ✗ | ✗ | ✓ (entitlement) |

### 12.3 Brand derivation (binding)

```text
 BR-1  Presentation is derived from the FIRM's mode + the FIRM's brand record.
 BR-2  NEVER derived from a per-client record.
 BR-3  NEVER derived from the hostname as an authorization input.
 BR-4  Custom domain is available ONLY in White-Label mode, and ONLY when
       entitlement is configured. The hostname must be VERIFIED against the
       stored, entitlement-checked mapping (see §17 F-9) — not trusted blindly.
 BR-5  A stored white-label flag that contradicts the mode is CAPPED by the
       mode and MUST NOT be destroyed as a side effect (IMPL-3).
 BR-6  Wherever CarbonTally attribution is legally required, it is retained
       according to CarbonTally's policy — not invented by the implementer.
 BR-7  Brand resolution failing MUST degrade to the safe default
       (CarbonTally brand), never to an unbranded/broken shell.
```

### 12.4 What is NOT in the branding contract

```text
 * No colours/fonts/asset specifications — D21 design system governs presentation.
 * No pricing or "branding as an add-on" packaging (PO-5).
 * No client-level brand inheritance rules beyond "the firm's brand applies".
 * No DNS/email administration (AGENTS.md §64 — the customer/consultant owns it).
```

---

## 13. Approval contract

### 13.1 Who may approve

| Context | Who may give FINAL approval | Authority source |
|---|---|---|
| Direct (non-consultant) organisation | the organisation's own authorized role(s) per existing policy (e.g. Owner) | Organisation RBAC |
| **Consultant-managed** organisation | a consultant holding **CAP-APPROVE** (PO-6 B+C) | Consultant RBAC |
| Consultant-managed, client also has COLLABORATIVE/MANAGED | the client user, **within their profile + client role**; and/or the consultant per above | Profile ∩ client role; consultant capability |

```text
 THE BLANKET "OWNER ONLY" RULE DOES NOT APPLY TO MANAGED ORGANISATIONS (PO-6 C).
```

### 13.2 Approval MUST

```text
 A-1  Record the actor's identity AND capacity (consultant vs client owner vs
      client role) — PO-6, PO-7 audit.
 A-2  Be authorized by an actual capability, never by relationship existence.
 A-3  Respect the client access profile where the approving party is a client.
 A-4  Preserve provenance: the approval attaches to the calculation/evidence
      chain (AGENTS.md §17/§26) without overwriting calculation history.
 A-5  Be idempotent/duplicate-safe: re-running must not create duplicate
      approvals or duplicate calculation snapshots (AGENTS.md §19).
 A-6  Be visible in the audit trail with a timestamp.
 A-7  Not be executable by a client user whose profile forbids it.
```

### 13.3 Approval MUST NOT

```text
 * Be granted because the actor "has the relationship".
 * Be granted because the actor uploaded the document or ran the calculation.
 * Be rendered without naming the capacity (no anonymous "Approved").
 * Overwrite or delete a prior approval record.
 * Be a frontend-only gate.
 * Require a client approval where the PO has permitted the consultant to
   complete final approval (i.e. do not re-impose "client owner only").
```

### 13.4 Review vs approval separation (unchanged)

```text
 REVIEW and APPROVAL remain distinct stages (AGENTS.md §26).
 A workflow MUST NOT present as complete while approval is outstanding.
 "Calculated" != "Reviewed" != "Approved". The UI must say which.
```

---

## 14. Relationship termination contract

### 14.1 Initiation (PO-7 D)

```text
 EITHER PARTY may initiate:
   - the CONSULTANT firm (its authorized role / capability), or
   - the CLIENT (via a client-initiated path — entry point = §19 OQ-1).
 The initiating party MUST be authenticated and authorized for that action.
```

### 14.2 The state machine (binding — not open)

```text
   [ACTIVE]
      |  initiate (either party, authorized)
      v
   [TERMINATION REQUESTED]   record: initiated_by, initiated_at, reason
      |  explicit confirmation by the initiating party
      |  (+ counterparty / CarbonTally confirmation per §19 OQ-1 semantics)
      v
   [TERMINATION CONFIRMED]   record: confirmed_by, confirmed_at
      |  access transition applied (non-destructive)
      v
   [TERMINATED / RETAINED]   consultant access revoked
                             client access = READ-ONLY RETAINED (PO-10)
                             all data + history preserved
      |  optional later re-link (new relationship, SAME organisation.id)
      v
   [ACTIVE] (new relationship; NOT a new organisation)
```

### 14.3 Termination MUST

```text
 T-1  Require explicit CONFIRMATION (no single-click termination).
 T-2  Require AUTHORIZATION (consultant capability / valid client session).
 T-3  Record WHO initiated, WHEN, and the REASON (PO-7 D).
 T-4  Record who confirmed and when.
 T-5  Revoke CONSULTANT access to the client organisation.
 T-6  Define the client's resulting state as READ-ONLY RETAINED (PO-10).
 T-7  Preserve organisation.id, all data, all history, all provenance.
 T-8  Preserve audit and evidence.
 T-9  Be idempotent (repeat submission must not duplicate the transition).
 T-10 Surface the state change clearly in BOTH the consultant and client UI.
```

### 14.4 Termination MUST NOT

```text
 X-1  Delete, truncate, archive-away or migrate the client Organisation.
 X-2  Delete or reassign client history, documents, extractions, calculations,
      evidence, reports or messages.
 X-3  Reassign organisation.id or change ownership of the data (S1 / AGENTS.md §11).
 X-4  Leave consultant access intact.
 X-5  Leave the client with an undefined state (must be a defined state, §15).
 X-6  Be presented as "your data has been deleted".
 X-7  Be executable without confirmation or without authorization.
 X-8  Break existing evidence, audit trail or reporting.
```

### 14.5 Post-termination re-link

```text
 Re-linking the same client to a consultant (or to CarbonTally directly) MUST
 reuse the SAME organisation.id — never a clone (AGENTS.md §11).
 The terminated relationship remains in history; the new relationship is a new
 record. Consultant access is scoped to the new relationship only.
```

---

## 15. Post-relationship access contract

### 15.1 States

```text
 S-RETAINED   client may see historical data read-only, subject to retention
              policy (PO-10 B+E).
 S-EXPIRED    retention period elapsed; access ends per platform retention
              policy (N3). The data lifecycle is governed by retention
              configuration — NOT invented here (§19 OQ-2).
 S-RELINKED   a new relationship exists; the new profile applies.
```

### 15.2 Client access after termination

```text
 PA-1  READ-ONLY historical access, subject to the platform retention/access
       policy (PO-10).
 PA-2  No WRITE access of any kind.
 PA-3  No messaging-send capability unless the PO confirms otherwise (§19 OQ-4);
       historical message history remains visible.
 PA-4  No user management, no branding control, no plan/billing surface.
 PA-5  The state must be clearly labelled and must state that data was NOT
       deleted and NOT migrated.
 PA-6  Enforcement is server-side; the client-side state is presentation only.
 PA-7  Retention MUST NOT weaken auditability, evidence or required history
       (AGENTS.md §42).
```

### 15.3 Consultant access after termination

```text
 CA-1  Consultant access to the client organisation is REVOKED (PO-7; AGENTS.md §11).
 CA-2  No residual read access via the terminated relationship. Continued
       involvement requires a NEW relationship record.
 CA-3  The consultant retains only what is theirs: the firm's own aggregate/
       commercial records — never the client's data.
```

### 15.4 Anti-patterns (forbidden)

```text
 * "Your consultant left, so your data is gone."
 * A blank portal, a 500 error, or an endless spinner after termination.
 * Silently re-homing the client under another consultant.
 * Deleting history to "clean up" an ended relationship.
 * Leaving the client's users with no explanation and no path to their data.
```

---

## 16. Direct customer vs consultant-managed distinction

| Dimension | DIRECT CUSTOMER | CONSULTANT-MANAGED CLIENT |
|---|---|---|
| Commercial counterparty to CarbonTally | the customer organisation | the **consultant firm** (the client is not a CarbonTally subscriber) |
| Who operates the workspace | the customer's own users | the **consultant firm's users** (operators, not viewers) |
| Who holds organisation membership | the customer's users | the client's own users; **consultants are NOT injected as members** (B4) |
| Client-facing plane | not applicable (they are the workspace) | Plane C `/portal/:clientId/*`, profile-scoped |
| Who sets the client's access profile | n/a | the consultant firm |
| Who invites client users | the customer's own authorized role | the **consultant** (PO-2) |
| Factor mapping / recalculation | customer roles per existing policy | **consultant only**; never the client (PO-9) |
| Final approval | the customer's authorized role (e.g. Owner) | **a consultant holding CAP-APPROVE may approve** (PO-6 B+C) |
| Branding | the organisation's own settings | firm-level brand only (PO-3A) |
| Mode / entitlement control | CarbonTally Admin | CarbonTally Admin (via the consultant's firm) |
| Billing surface visible to the end user | own subscription | **none** — locked/explained (PO-5, S1 §7) |
| Relationship termination | n/a | **explicit, audited, non-destructive** (PO-7) |
| Post-termination data state | n/a | **retained + read-only** (PO-10) |
| Consultant-to-consultant boundaries | n/a | hard isolation (INV-A, INV-D) |

```text
 The distinction is ENFORCED SERVER-SIDE. The most common failure mode to
 avoid is letting a consultant-managed client inherit direct-customer
 assumptions (or vice versa) inside the authorization layer.
```
## 17. Known implementation findings the next task must address

These findings are **current-code observations verified in this session** (§1.1).
They are recorded here as *inputs to the follow-on implementation task*.

```text
 NONE OF THESE WERE FIXED BY THIS TASK.
 This document makes NO implementation, migration, schema, API, RLS, RPC,
 route or UI change of any kind (see §18).
 A finding is a TARGET for the next task — not a claim that the target is
 already satisfied, and not an acceptance verdict.
```

| ID | Finding | Required by | Status |
|---|---|---|---|
| **F-1** | Consultant authorization admits on *relationship existence* with no capability term ("capability-blind admission") | PO-1…PO-10 via §7.2, §7.4, §6.2, §8.3 | **OPEN — NOT FIXED** |
| **F-2** | Consultant **final-approval** capability is not representable on a consultant firm member (CAP-APPROVE has no home) | PO-6 (B+C) via §13.1, §7.3 | **OPEN — NOT FIXED** |
| **F-3** | No persisted **client access-profile** (Plane C ceiling) exists anywhere: OFF / READ_ONLY / COLLABORATIVE / MANAGED / POST-RELATIONSHIP | PO-4, PO-10 via §8.1, §8.4 | **OPEN — NOT FIXED** |
| **F-4** | **Terminated relationship = total denial**: there is no grant state that can express "RETAINED read-only" | PO-10 (B+E) via §15.1, PA-1…PA-3 | **OPEN — NOT FIXED** |
| **F-5** | Custom-domain / white-label machinery exists but is **not mode-entitlement gated**; the three modes are two independent booleans, not a mode | PO-4 via §6.2, §12.2 | **OPEN — NOT FIXED** |
| **F-6** | No **mode-change REQUEST** workflow: mode appears directly editable, i.e. immediate rather than request-at-boundary | PO-1 (B+D) via §4.2, §6.5 | **OPEN — NOT FIXED** |
| **F-7** | Plane C is mounted at `/consultant/clients/:clientId/*`, **not** the PO-8 path `/portal/:clientId/*` | PO-8 (A) via §11.1 | **OPEN — NOT FIXED** |
| **F-8** | No **client-side** relationship entry point (invite / change / end) — consultant-side lifecycle only | PO-2, PO-7 (D) via §4.9, §10.1 | **OPEN — NOT FIXED** |
| **F-9** | A **hostname→brand** resolution path that is entitlement-checked does not exist; branding derivation never authorizes | §12.3, PO-3B, INV-F | **OPEN — NOT FIXED** |
| **F-10** | Firm-member capability write semantics must not regress to **wholesale replacement** of the capability map | §7.3 (grantable/revocable), §20.4 | **OPEN — NOT FIXED** |

### 17.1 Finding detail — admission and capability (F-1 … F-5)

```text
 F-1  CAPABILITY-BLIND CONSULTANT ADMISSION        [BLOCKS §7.2, §7.4]
      Evidence (current code):
        backend/api/consultant_auth.py
          * ensure_consultant_org_access()     admits when the relationship
            row is ACTIVE — the relationship ALONE is the decision.
          * resolve_managed_org_ids()          derives the consultant's WHOLE
            organisation scope from active grants; no capability term.
        backend/api/dependencies.py
          * ensure_org_access()                admits whenever
            `org_id in managed_org_ids` — again no capability term.
        Contrast:
          * the Consultant PROCESSING path DOES gate on six explicit flags
            (can_extract / can_map / can_validate / can_calculate /
             can_confirm_automation / can_submit) via
             ensure_consultant_processing_authorized().
        Consequence:  every NON-processing consultant route that reuses
          ensure_org_access() is effectively "has relationship = full access",
          which §7.4 forbids outright and §6.1 (PROFILE = CEILING,
          ROLE/CAPABILITY = AUTHORITY) contradicts.
        Required fix direction (implementation task): admission must evaluate
          CAPABILITY ∩ PROFILE ∩ ENTITLEMENT per §6.2, not relationship
          existence. Do NOT fix by widening the six processing flags.

 F-2  NO HOME FOR CONSULTANT FINAL APPROVAL        [BLOCKS PO-6, §13.1]
      Evidence (current code):
        * consultant firm-member permission maps enumerate ten capabilities;
          NONE of them is an approval capability.
        * the only `can_approve` flags in the system live in the
          CarbonTally STAFF surface (backend/domain/staff.py,
          backend/routes/admin/permissions.py) — a different identity plane.
        Consequence: PO-6 (B+C) cannot be satisfied today because the
          capability does not exist to be checked. §13.1's CAP-APPROVE must be
          materialised for CONSULTANT FIRM MEMBERS (schema + check + test),
          separable from processing/mapping per §7.3.

 F-3  NO CLIENT ACCESS-PROFILE STATE               [BLOCKS PO-4, §8]
      Evidence (current code):
        * no column, table or enum carries OFF / READ_ONLY / COLLABORATIVE /
          MANAGED / POST-RELATIONSHIP.
        * client access is effectively a binary active grant plus a per-member
          shortcut flag.
        Consequence: §8.1's five profiles and §8.4's profile × mode matrix
          have nowhere to live, so MUST-2 (§11.2) cannot be enforced.
        Note: MANAGED being unavailable in STANDARD mode (PO-4) is therefore
          also unenforceable until this is represented.

 F-4  TERMINATED = TOTAL DENIAL, NOT RETAINED       [BLOCKS PO-10, §15]
      Evidence (current code):
        * ensure_consultant_org_access()  denies any relationship status that
          is not ACTIVE.
        * resolve_managed_org_ids()       filters to status ACTIVE.
        * the client-status vocabulary already contains an ENDED-style value
          documented as granting NOTHING.
        Consequence: §15.1 / PA-1…PA-3 (post-relationship read-only retained
          access) has no grant state it could attach to, and MUST-10 (§11.2)
          cannot render the correct end-of-relationship state without
          implying deletion — which NB-9 forbids.
        Constraint: the retention DURATION is a PO question (§19 OQ-2) and
          must NOT be invented by the implementer.

 F-5  MODES ARE BOOLEANS; DOMAIN IS UNGATED          [BLOCKS PO-4, §12.2]
      Evidence (current code):
        * consultant branding is two INDEPENDENT booleans
          (white_label_enabled, co_branding_enabled) resolved by
          backend/domain/branding.py with "white-label wins".
        * custom domains are real: consultant_custom_domains table
          (PENDING / VERIFIED / ACTIVE / REMOVED_SUSPENDED) plus create /
          verify / activate / remove endpoints in backend/api/v3_whitelabel.py.
        * no server-side check ties a custom domain to WHITE-LABEL mode, and
          no mode entity exists to check it against.
        Consequence: PO-4's "custom domain = White-Label only" and
          "MANAGED available in Co-Branded + White-Label only" are
          UNENFORCEABLE as the code stands, and STANDARD firms can reach
          domain machinery.
```

### 17.2 Finding detail — workflow, path, entry points (F-6 … F-10)

```text
 F-6  NO MODE-CHANGE REQUEST WORKFLOW              [BLOCKS PO-1 (B+D)]
      Evidence (current code):
        * no request entity, no request endpoint, no `effective_at` /
          billing-boundary concept.
        * the consultant self-service branding surface writes the mode
          booleans directly (frontend/src/v3/consultant/ConsultantPage.jsx),
          which presents the change as IMMEDIATE.
        Consequence: PO-1's ratified semantics — a change is a REQUEST that
          becomes effective at the billing/renewal boundary, decided by
          CarbonTally — are absent. Implementing PO-1 therefore means
          REPLACING direct mode mutation with a request flow, not merely
          adding a button.

 F-7  PLANE C PATH DIVERGES FROM PO-8 (A)          [BLOCKS PO-8, §11.1]
      Evidence (current code):
        * frontend/src/App.js mounts the client-organisation shell at
          /consultant/clients/:clientId/* (home, documents, processing,
          review, manual-processing, emissions, reports, issues, messaging,
          insight, existing-data, capabilities, organization, evidence…).
        * NO /portal/ route family exists anywhere in the frontend.
        * the shell is a CONSULTANT-context workspace today; a
          client-LOGIN plane with profile-scoped navigation is not evidenced.
      Consequence: PO-8 (A) is binding (§11.1, §4.10) and §3.3 C-9 records it
        as closed. The implementation task must resolve this as an explicit,
        PO-visible route migration — NOT by silently changing live routes and
        NOT by declaring the existing path "close enough". Preserve-or-alias
        behaviour is an implementation decision, but the PO-8 path is the
        contract the acceptance criteria in §20.3 test.

 F-8  NO CLIENT-SIDE RELATIONSHIP ENTRY POINT      [BLOCKS PO-2, PO-7]
      Evidence (current code):
        * consultant-side client lifecycle exists
          (backend/api/v3_consultants.py), and an invited member record is
          exposed there with its invitation timestamp.
        * no client-side invite, "change consultant" or "end relationship"
          endpoint exists on any client plane.
        * the design's NOT-BUILT-2 toggle is explicitly rejected (§9.2, NB-5).
      Consequence: PO-2 (consultant-side invitations ONLY) is not yet enforced
        because there is no client-side counterpart to forbid; PO-7's
        either-party initiation has no client-side mechanism.
        PARTIALLY BLOCKED: the client-side MECHANISM is §19 OQ-1 and must be
        marked BLOCKED — PO DECISION REQUIRED, not guessed.

 F-9  HOSTNAME→BRAND IS NOT ENTITLEMENT-CHECKED    [BLOCKS §12.3, INV-F]
      Evidence (current code):
        * the domain lifecycle exists (see F-5) but nothing resolves an
          incoming request hostname to a firm brand.
        * backend/domain/branding.py is a pure derivation helper: it never
          authorizes anything and cannot, by itself, satisfy §12.3 or INV-F.
      Consequence: presenting a white-label experience requires a
        server-side, entitlement-checked hostname→brand mapping that respects
        REMOVED_SUSPENDED and mode. Until it exists, white-label presentation
        (PO-3B) is not safely deliverable and MUST NOT be simulated in the
        frontend (INV-F: no decision from a hostname/brand alone).

 F-10 CAPABILITY WRITE SEMANTICS                    [BLOCKS §7.3, §20.4]
      Evidence (current code):
        * tooling has previously written firm-member capability maps
          WHOLESALE, silently erasing migration-granted flags; the corrected
          behaviour merges per-key defaults (tools/demo_lab/provision.py).
        * firm-member capability columns are separate from any permissions
          JSONB map, so a wholesale write can drop the other representation.
      Consequence: once F-1/F-2 introduce capability checks, a wholesale
        capability write becomes a PRIVILEGE bug, not a cosmetic one. §20.4
        must carry a regression test asserting merge-not-replace and that no
        capability is granted by omission.
```

## 18. Explicit implementation boundaries

This section constrains the FOLLOW-ON implementation task. It is written as a
hard boundary list because the preceding sixteen sections are decision
material, not a to-do list of everything that could be built.

### 18.1 This task's own boundary (what was and was not done here)

```text
 THIS TASK IS DOCUMENTATION-ONLY. It produced this file and nothing else.
 NOT CHANGED BY THIS TASK:
   * no backend Python change        (api / domain / services / data / routes)
   * no frontend change              (routes, pages, components, styles)
   * no database change              (no migration, no table, no column, no RLS)
   * no API contract change          (no route added, altered or removed)
   * no RPC / job / worker change
   * no seed / demo-data change      (investor demo data untouched, AGENTS.md §55)
   * no test added, changed or removed
   * no AGENTS.md change, no frozen-UX change (D17/D19/D21/N1/N3)
 Do not read this document as an authorisation to apply schema changes; a
 migration requires its own inspected, reviewed change with its own tests
 (AGENTS.md §66, §67).
```

### 18.2 What the implementation task MUST NOT do

```text
 B-1  MUST NOT weaken, disable or bypass RLS. No service-role shortcut may
      replace server-side authorization (AGENTS.md §67, §68).
 B-2  MUST NOT encode "has an ACTIVE relationship ⇒ full access" anywhere
      (kills F-1). Every admitted action must satisfy
      CAPABILITY ∩ PROFILE ∩ ENTITLEMENT (this document §6.2).
 B-3  MUST NOT implement §19 OQ-1 / OQ-2 / OQ-3 / OQ-4 by assumption. Those
      sub-scopes are BLOCKED — PO DECISION REQUIRED. Partial implementations
      that "pick a sensible default" are prohibited (AGENTS.md §62).
 B-4  MUST NOT invent prices, seat counts, retention durations, usage limits
      or plan names (NB-8; §6.3; §19 OQ-2).
 B-5  MUST NOT build any §9.2 / §10.3 rejected element — in particular
      per-client branding (NB-1), a self-service plan/mode switcher (NB-2),
      client-side mapping/recalculation (NB-3), client-side user management
      (NB-4), a "flip consultant" toggle (NB-5), client-visible subscription
      surfaces (NB-6), consultant self-granted entitlement (NB-7), or a
      termination experience that reads as deletion (NB-9).
 B-6  MUST NOT rely on a hidden button, disabled control, route guard,
      hostname, subdomain or brand as the authorization decision (INV-F;
      AGENTS.md §7, §44).
 B-7  MUST NOT silently reshape the live Plane C routes. The PO-8 path is
      `/portal/:clientId/*`; the existing `/consultant/clients/:clientId/*`
      family is live. Any change must be an explicit, recorded migration
      decision with redirect/alias behaviour stated (F-7).
 B-8  MUST NOT repurpose the CarbonTally STAFF permission plane for
      consultant capabilities, nor the consultant capability plane for staff
      (F-2; §7.1 identity separation).
 B-9  MUST NOT modify, reset, truncate or reseed the investor demo dataset
      (AGENTS.md §54, §55). If a mutation test is unavoidable, create isolated
      labelled records, track them, and clean up only those (AGENTS.md §55).
 B-10 MUST NOT treat a frontend capability set as the authority for a backend
      decision, and MUST NOT assume a client-side profile grants authority
      (§6.1: the profile is the CEILING, never the grant).
 B-11 MUST NOT present relationship termination as deletion, migration or
      loss of data anywhere in copy, state naming or API shape (PO-10, NB-9).
 B-12 MUST NOT extend the capability vocabulary beyond §7.3, and MUST NOT
      satisfy PO-6 by overloading an existing processing flag (F-2).
 B-13 MUST NOT change frozen UX (D17, D19, D21, N1, N3). Where this document
      conflicts with a frozen decision, the conflict must be raised, not
      silently resolved (AGENTS.md §39, §40, §63).
 B-14 MUST NOT broaden permissions "to make the flow work" — the correct
      response to a denial is a capability grant made through the approved
      mechanism, or a PO decision (AGENTS.md §14, §44).
```

### 18.3 What the implementation task MUST do

```text
 M-1  Enforce every MUST / MUST-NOT in §11.2 and §11.3 server-side.
 M-2  Materialise the capability model of §7.3 (including CAP-APPROVE) and
      check it on admission (F-1, F-2).
 M-3  Represent the access profiles of §8.1 and enforce §8.4 (F-3).
 M-4  Represent RETAINED read-only post-termination state per §14.2 / §15
      WITHOUT inventing a retention duration (F-4, OQ-2).
 M-5  Implement the termination state machine of §14.2 as an audited,
      non-destructive transition (PO-7 D).
 M-6  Implement the mode/entitlement resolution order of §6.2 and the
      request-at-boundary mode change of PO-1 (F-5, F-6).
 M-7  Add the §20 acceptance criteria — including the §20.4 negative tests —
      as regression coverage BEFORE claiming completion.
 M-8  Preserve provenance and auditability on every approval, termination and
      post-relationship transition (AGENTS.md §17, §18).
```

## 19. Remaining open PO questions

These are the ONLY matters this document leaves undecided. Everything else in
§4–§16 is binding.

```text
 RULE FOR THE IMPLEMENTATION TASK
   * An OQ sub-scope is BLOCKED — PO DECISION REQUIRED.
   * Do NOT choose a default, do NOT infer one from the design report, and do
     NOT ship a partial version "to be adjusted later".
   * If an OQ blocks only PART of a feature, implement the unblocked part and
     stop at the boundary, leaving the blocked part unimplemented and visibly
     recorded (AGENTS.md §62, §73, §74).
```

### 19.1 Open questions

| ID | Matter | Why the PO must decide | Blocks | Referenced from |
|---|---|---|---|---|
| **OQ-1** | The CONSULTANT-SIDE vs CLIENT-SIDE mechanism by which a client *changes* or *ends* its consultant relationship: what the entry point is, who confirms, what the counterparty and CarbonTally see | PO-7 (D) ratifies *that* either party may initiate and that the transition is audited and non-destructive, but not the client-facing mechanism. The design's toggle is rejected (§9.2) | The client-side initiation path; §14.1 second bullet; NB-5; F-8 | §3.3 C-5, §4.9, §4.10, §9.2, §10.1, §10.3, §14.1 |
| **OQ-2** | The RETENTION PERIOD (and its scope) governing post-relationship retained data and read-only access | PO-10 (B+E) ratifies *that* history is retained and read-only access is permitted "subject to platform retention/access policy" — the period itself is a PO value and must not be invented | §15.1 / PA-1…PA-3 messaging, F-4 implementation, any retention copy | §4.12, §15.1, §11.4, §16 |
| **OQ-3** | How a relationship is TERMINATED when the client organisation has NO client-side access at all (profile OFF / no client login) — i.e. when PO-7's "either party" cannot include a client actor | PO-7's either-party rule is written for a client that can act. For an OFF-profile, no-login client the initiating party must be the consultant, CarbonTally, or an explicit client-side notice/confirmation route — a policy choice | The OFF-profile termination flow; §14.1 applicability; F-8 scope | *(introduced here; no earlier section refers to OQ-3)* |
| **OQ-4** | POST-TERMINATION MESSAGING: whether the retired relationship retains a messaging channel, a notice-only channel, or no channel | §15 / PA-3 currently states "no messaging-send capability unless the PO confirms otherwise". Whether an end-of-relationship channel is required is a communications-boundary policy decision (N1) | §15 PA-3, §9 matrix row 11, §11.4 | §9.1, §15, §11.4 |

```text
 OQ-3 is NEWLY ASSIGNED BY THIS SECTION. Earlier sections reference OQ-1, OQ-2
 and OQ-4 only; no existing cross-reference is altered by adding OQ-3.
```

### 19.2 What is NOT open (recorded to prevent re-litigation)

```text
 CLOSED — do not re-open as "open questions":
   * Mode semantics and the request-at-boundary rule ................. PO-1
   * Invitations are consultant-side only ............................ PO-2
   * Branding granularity = firm level ............................... PO-3A
   * White-label availability ....................................... PO-3B
   * MANAGED profile + custom-domain mode gating ..................... PO-4
   * Commercial configuration ownership .............................. PO-5
   * Consultant final-approval authority (CAP-APPROVE) ............... PO-6
   * Either party may terminate; audited; never deletes data ......... PO-7
   * Plane C path family /portal/:clientId/* ......................... PO-8
   * Client never maps factors or recalculates ....................... PO-9
   * Post-relationship data retained; read-only access permitted ..... PO-10
   * The tenancy invariants INV-A…INV-G .............................. §5.5
   * Five client profiles and their ceiling semantics ................ §8.1, §8.2
   * The termination state machine ................................... §14.2
   * Termination does NOT create a new organisation.id ............... §14.5 (PO-10 E)
```

### 19.3 Blocking register (what cannot be declared complete)

| Blocked sub-scope | OQ | Status if the task proceeds |
|---|---|---|
| Client-initiated relationship change/termination | OQ-1 | **BLOCKED — PO DECISION REQUIRED** |
| Post-relationship retention period & copy | OQ-2 | **BLOCKED — PO DECISION REQUIRED** |
| Termination for an OFF-profile / no-login client | OQ-3 | **BLOCKED — PO DECISION REQUIRED** |
| Post-termination messaging channel | OQ-4 | **BLOCKED — PO DECISION REQUIRED** |

> Any acceptance report produced by the implementation task MUST list these
> four sub-scopes as UNIMPLEMENTED / BLOCKED rather than folded into a
> pass/fail total (AGENTS.md §52, §73).

## 20. Implementation acceptance criteria

These criteria define what "done" means for the follow-on task. They are
written to be testable **without** trusting the frontend. A criterion is met
only when BOTH the UI behaviour AND the server-side denial are evidenced
(AGENTS.md §73, §74).

```text
 VERIFICATION DISCIPLINE
   * Every criterion below needs a NEGATIVE companion (§20.4) — an unexpected
     ALLOW is a security finding, not a pass.
   * "Implemented" ≠ "Verified". The implementation report must state which.
   * No criterion may be reported as met on the strength of a page loading,
     a button existing or a spinner moving.
```

### 20.1 Functional acceptance criteria

| AC | Requirement | Source | Verification method |
|---|---|---|---|
| **AC-F-1** | Consultant admission requires `CAPABILITY ∩ PROFILE ∩ ENTITLEMENT`; relationship existence alone never admits | F-1, §6.2, §7.2 | API test: ACTIVE relationship + missing capability ⇒ DENY |
| **AC-F-2** | `CAP-APPROVE` exists for consultant firm members, grantable/revocable, separable from processing and mapping | F-2, PO-6, §7.3, §13.1 | Grant/deny pair on the approval endpoint |
| **AC-F-3** | The client access profile is persisted and enforced on every Plane C read AND write | F-3, §8.1, MUST-2 | Matrix test per profile × operation |
| **AC-F-4** | `OFF` and `POST-RELATIONSHIP` are distinct states with distinct, non-alarming copy | §8.1, PO-10 | UI + state assertion; copy review |
| **AC-F-5** | Post-termination RETAINED read-only access resolves (no deletion-flavoured 404); duration NOT invented | §15, PA-1…PA-3, OQ-2 | API test + explicit UNBLOCKED/BLOCKED record |
| **AC-F-6** | `MANAGED` unavailable in STANDARD; custom domain unavailable outside WHITE-LABEL | F-5, PO-4, §6.2, §12.2 | Deny tests at the entitlement boundary |
| **AC-F-7** | A mode change is a REQUEST becoming effective at the billing/renewal boundary, decided by CarbonTally; direct mode mutation is rejected | F-6, PO-1 (B+D), §6.5 | Request lifecycle test + direct-write denial |
| **AC-F-8** | Plane C is served on the `/portal/:clientId/*` family | F-7, PO-8 (A), §11.1 | Route assertion + deep-link test |
| **AC-F-9** | Client-user invitation/management exists ONLY consultant-side; the client plane has no such control or endpoint | PO-2, §9.2, NB-4, MUST-4 | Endpoint absence + deny test |
| **AC-F-10** | Factor mapping and recalculation are denied to clients in the API and absent from the UI | PO-9, MUST-3, NB-3 | Deny test + UI absence |
| **AC-F-11** | No client-visible plan, invoice, subscription, upgrade, price, seat or usage limit | PO-5, §5.4, NB-6, NB-8 | API/UI assertion + string scan |
| **AC-F-12** | Plane C branding derives from the FIRM record only; no per-client brand path exists | PO-3A, §12.1, §12.3, NB-1 | Deny test on any per-client brand write |
| **AC-F-13** | Hostname→brand resolution uses a stored, entitlement-checked mapping; unverified/suspended domains present no firm brand | F-9, §12.3, INV-F | Table-driven test per domain status |
| **AC-F-14** | Termination preserves `organisation.id`, deletes no data and creates no clone | PO-7 (D), PO-10 (E), §14.2, §14.5 | Pre/post id + row-count comparison |
| **AC-F-15** | Every approval, termination, profile change and mode request is audited with actor, organisation, entity and timestamp | §13.2, §14.3, AGENTS.md §17/§18 | Audit-row assertions |
| **AC-F-16** | A STANDARD-mode firm exposes no client login or portal plane at all | PO-4, MUSTNOT-5 | Plane absence test |
| **AC-F-17** | A deep link to a foreign `:clientId` fails with a generic, non-disclosing error (no existence oracle) | MUST-9, INV-B, INV-C | Cross-tenant deep-link test |
| **AC-F-18** | Capability grant/revoke is per-capability and merges; no wholesale replacement; nothing is granted by omission | F-10, §7.3 | Merge regression test + default-deny assertion |

### 20.2 Security acceptance criteria

Aligned to AGENTS.md §44/§45, expressed for the consultant model. Each needs a
DENY test (never only an ALLOW test).

| AC | Requirement | Source |
|---|---|---|
| **AC-S-1** | Consultant A cannot reach Consultant B's client organisation through ANY route (read or write, incl. reports, evidence, messaging, exports) | INV-A, §5.5 |
| **AC-S-2** | A client user cannot reach another client organisation, nor its own organisation outside the consultant relationship's scope | INV-B, INV-C |
| **AC-S-3** | A consultant cannot reach an organisation it is not linked to — including by guessing an id, an entity id or a source-document path | INV-D |
| **AC-S-4** | The client plane is unusable for any link state other than ACTIVE or RETAINED-READ-ONLY | INV-E, MUST-8 |
| **AC-S-5** | No authorization decision derives from hostname, subdomain, brand, hidden button, disabled control or route guard | INV-F |
| **AC-S-6** | Entitlement never substitutes for capability and capability never substitutes for relationship — all three are checked | INV-G, §6.2 |
| **AC-S-7** | RLS is not disabled, weakened or bypassed; any service-role path retains explicit server-side authorization and is documented | AGENTS.md §67, §68, B-1 |
| **AC-S-8** | Storage access (signed URLs, document paths) respects the same model; authorization precedes any URL issuance; no signed URL in logs/reports | AGENTS.md §68, §78 |
| **AC-S-9** | Staff permissions are not a shortcut into consultant/client planes, and consultant capabilities do not reach internal operations | AGENTS.md §14, §45 |
| **AC-S-10** | No identifier, error message or timing difference discloses the existence of a foreign organisation, client, entity or document | MUST-9, AGENTS.md §46 |

### 20.3 UI/UX acceptance criteria

Every rejected element is an acceptance criterion in its own right: its
**absence must be verified**, not assumed.

| AC | Requirement | Source |
|---|---|---|
| **AC-U-1** | Plane C shows the firm's brand and no client-side brand or logo control | PO-3A, NB-1 |
| **AC-U-2** | No self-service plan, mode or seat chooser with any value; mode change is a request | PO-1, PO-5, NB-2, NB-8 |
| **AC-U-3** | No client-side mapping edit, mapping affordance or recalculation trigger | PO-9, NB-3 |
| **AC-U-4** | No client-side invitation or user management surface | PO-2, NB-4 |
| **AC-U-5** | No "flip consultant" toggle or switcher; the observed initiation path matches the OQ-1 decision or is absent while blocked | §9.2, NB-5, OQ-1 |
| **AC-U-6** | No CarbonTally subscription/invoice/plan/upgrade surface for a managed client | PO-5, §5.4, NB-6 |
| **AC-U-7** | No control allowing a consultant to grant itself entitlement | §6.3, NB-7 |
| **AC-U-8** | Termination is presented as an end of relationship with data retained — never as deletion or migration | PO-10, NB-9, §14.3 |
| **AC-U-9** | Every operational screen answers §76 (where am I, which client, what needs attention, what can I do, what happened, what next, how do I go back) with human-readable context, not raw UUIDs | AGENTS.md §36–§38, §75, §76, MUST-7 |
| **AC-U-10** | Meaningful loading, empty and non-active states exist; a spinner is never presented as proof of processing; §11.4 non-active states are implemented | AGENTS.md §47–§48, §11.4 |
| **AC-U-11** | The §9 acceptance matrix rows that changed (rows 3, 5, 6, 7, 9, 10, 13, 14) are re-verified against this document, and row 13's "access paused" split is implemented | §9, §10.1 |
| **AC-U-12** | Layouts hold at the §49 viewports without horizontal overflow, clipped tables or unusable dialogs; keyboard/ARIA baseline per §50 met | AGENTS.md §49, §50 |

### 20.4 Negative tests (mandatory)

One test per invariant is REQUIRED by §5.5. Additional rows cover the PO
prohibitions. Expected outcome is always DENY / ABSENT unless stated.

| ID | Actor | Attempted | Expected | Guards |
|---|---|---|---|---|
| **NT-01** | Consultant A | Read Consultant B's client organisation and its reports | DENY, generic error, no existence disclosure | INV-A |
| **NT-02** | Consultant A | Process/upload into Consultant B's client organisation | DENY | INV-A |
| **NT-03** | Consultant A | Reach an organisation it is not linked to (guessed id) | DENY | INV-D |
| **NT-04** | Client A user | Open Client B's organisation by editing `:clientId` | DENY, generic | INV-B |
| **NT-05** | Client user | Use a foreign `:clientId` with a valid session | DENY, generic | INV-C |
| **NT-06** | Client user | Reach a **different client of the same consultant firm** | DENY | INV-A/INV-C |
| **NT-07** | Client user | Use Plane C on a link that is OFF / SUSPENDED / ENDED | DENY (except RETAINED read-only) | INV-E |
| **NT-08** | Unauthenticated visitor | Reach Plane C via a white-label hostname/subdomain | DENY | INV-F |
| **NT-09** | Client user | Call a consultant capability endpoint directly, bypassing the UI | DENY | INV-F, INV-G |
| **NT-10** | Entitled firm, member without the capability | Perform the capability's action | DENY | INV-G, F-1 |
| **NT-11** | Capable member, relationship not ACTIVE | Perform the action | DENY | INV-G |
| **NT-12** | Relationship ACTIVE, capability absent | Perform the action | DENY | INV-G, F-1 |
| **NT-13** | Client user | Edit a factor mapping or trigger recalculation | DENY always (API + UI absent) | PO-9 |
| **NT-14** | Client user | Invite or manage a client user | DENY | PO-2 |
| **NT-15** | Client user | Read a plan, invoice, subscription or upgrade surface | DENY / absent | PO-5 |
| **NT-16** | STANDARD-mode firm | Reach a client login or portal plane at all | ABSENT (no plane) | PO-4 |
| **NT-17** | CO-BRANDED firm | Create or activate a custom domain | DENY | PO-4 |
| **NT-18** | Consultant member | Write the mode flags directly | DENY (request flow only) | PO-1 |
| **NT-19** | Consultant member | Grant the firm entitlement it does not hold | DENY | NB-7, §6.3 |
| **NT-20** | Consultant member | Write a per-client brand/logo | DENY | PO-3A |
| **NT-21** | Client user | Reach an internal CarbonTally operation | DENY | AGENTS.md §45 |
| **NT-22** | Non-admin staff user | Manage a consultant firm or its capabilities | DENY | AGENTS.md §14 |
| **NT-23** | Consultant Admin | Suspend a relationship, then reuse a live client session | Immediate revocation; no cached granted access | INV-E |
| **NT-24** | Capability write | Write a capability map omitting a key, or wholesale | Missing keys stay DENY; other keys preserved | F-10, §7.3 |
| **NT-25** | Any test | Mutate the investor demo dataset | No mutation (counts/relations asserted unchanged) | AGENTS.md §55 |

```text
 REPORTING RULE
   Every NT row must be reported with: role, organisation, entity context,
   route/endpoint, request, response status, and the evidence location.
   An unexpected ALLOW is a SECURITY FINDING of the highest severity and must
   stop the task from being reported as complete (AGENTS.md §45, §53).
```

## 21. Traceability matrix

Every binding decision must be traceable to: its source, the sections that
implement it as contract, the findings it creates or closes, the design deltas
it requires, the acceptance criteria that test it, and any open question.

| Decision | Contract sections | Findings | Deltas / prohibitions | Acceptance criteria | Open |
|---|---|---|---|---|---|
| **PO-1** Mode + request-at-boundary | §4.2, §5.2, §6.2, §6.5 | F-6 | DELTA-11; NB-2, NB-8 | AC-F-7, AC-U-2, NT-18 | — |
| **PO-2** Consultant-side invitations | §4.3, §8.2, §9.2, §11.2 | F-8 | DELTA-13; NB-4 | AC-F-9, AC-U-4, NT-14 | — |
| **PO-3A** Firm-level branding | §4.4, §12.1, §12.3 | F-9 | DELTA-18; NB-1 | AC-F-12, AC-U-1, NT-20 | — |
| **PO-3B** White-label availability | §4.5, §12.2 | F-5, F-9 | DELTA-17; MUSTNOT-4 | AC-F-6, AC-F-13, NT-08 | — |
| **PO-4** MANAGED + custom domain gating | §4.6, §5.2, §8.4, §12.2 | F-3, F-5 | DELTA-17 | AC-F-3, AC-F-6, AC-F-16, NT-16, NT-17 | — |
| **PO-5** Commercial configuration | §4.7, §5.4, §6.3 | — | NB-6, NB-7, NB-8 | AC-F-11, AC-U-6, AC-U-7, NT-15, NT-19 | — |
| **PO-6** Consultant final approval | §4.8, §7.3, §13 | F-2 | DELTA-16 | AC-F-2, AC-F-15 | — |
| **PO-7** Ending the relationship | §4.9, §14 | F-4 | DELTA-15; NB-9 | AC-F-14, AC-U-8, NT-23 | OQ-1, OQ-3 |
| **PO-8** Plane C path | §4.10, §11.1 | F-7 | DELTA-9 | AC-F-8, NT-04, NT-05 | — |
| **PO-9** Client cannot map/recalculate | §4.11, §8.2, §11.3 | — | DELTA-9, DELTA-13; NB-3 | AC-F-10, AC-U-3, NT-13 | — |
| **PO-10** Post-relationship access | §4.12, §15 | F-4 | DELTA-14, PA-1…PA-7, CA-1…CA-3 | AC-F-4, AC-F-5, AC-U-8, NT-07 | OQ-2, OQ-4 |
| **INV-A…INV-G** Tenancy invariants | §5.5, §7.4 | F-1 | §11.3 MUSTNOT-6 | AC-S-1…AC-S-10, NT-01…NT-12 | — |
| **Capability model** | §7.2, §7.3 | F-1, F-2, F-10 | §6.1 (ceiling vs authority) | AC-F-1, AC-F-18, NT-10…NT-12, NT-24 | — |
| **Profile model** | §8.1, §8.2, §8.3, §8.4 | F-3 | DELTA-13, DELTA-14 | AC-F-3, AC-F-4, AC-S-4 | — |
| **Frozen UX: N1 messaging** | §9, §11.4, §15 PA-3 | — | — | AC-U-10 | OQ-4 |
| **Frozen UX: N3 retention** | §15.1, §15.2 PA-7 | F-4 | — | AC-F-5 | OQ-2 |
| **Two-plane / workspace model** | §5.3, §11, §16 | F-7 | DELTA-1..10, DELTA-12 (adopted) | AC-U-9, AC-U-11 | — |

### 21.1 Source → section map (provenance of this document)

```text
 S1  Binding Consultant Model decision doc
       → §4 (PO decisions), §5 (business model), §7 (RBAC), §8 (profiles),
         §6 (config), §12 (§7 billing separation), §16 (distinction)
 S2  UI/UX design report
       → §9 (acceptance matrix), §10 (deltas), §11 (Plane C), §12 (branding),
         §13 (approval), §14 (termination), §15 (post-relationship)
 S3  Secondary design draft
       → §9.2 / §10.3 (REJECTED elements only — never adopted as contract)
 S4  Organisation-workspace material
       → §16, §8 (customer-side comparison)
 S5–S7  Audit / verification material
       → §17 (findings F-1 … F-10), §3.3 (conflicts)
 PO-1…PO-10  Product Owner decisions
       → §4 (binding), and they OVERRIDE S1–S7 wherever they disagree (§3.1)
 AGENTS.md (frozen UX D17/D19/D21/N1/N3 + constitution)
       → §18 (boundaries), §20 (acceptance + negative tests)
```

```text
 A section with NO row above would be untraceable. §1, §2, §3, §19, §21, §22
 are document-level (metadata, scope, hierarchy, open questions, traceability
 and verdict) and need no decision row.
```

## 22. Final readiness verdict

### 22.1 Verdict

```text
 VERDICT  =  READY_FOR_IMPLEMENTATION
```

The consultant model is **decidable**. Every matter that required a Product
Owner choice and was put to the PO is answered in §4 and treated as binding
throughout. The source conflicts are resolved and recorded (§3.3). The
capability, profile, entitlement, branding, approval, termination and
post-relationship contracts are written as enforceable rules (§7–§15), and the
direct-customer vs consultant-managed distinction is explicit (§16). The
implementation task therefore receives one contract, not several competing
narratives.

This verdict is **scoped**, and the scope is the whole of the verdict's honesty:

```text
 READY FOR IMPLEMENTATION  .......  PO-1 … PO-10 as consolidated (§4–§16),
                                    the tenancy invariants (§5.5), and the
                                    Plane C / branding / approval /
                                    termination / post-relationship contracts.

 BLOCKED — PO DECISION REQUIRED  ..  the four sub-scopes in §19.3
                                    (OQ-1, OQ-2, OQ-3, OQ-4).
                                    These are NOT ready and MUST NOT be
                                    guessed. Their absence does not make the
                                    rest undecidable, but their absence MUST
                                    be reported as UNIMPLEMENTED.
```

### 22.2 What this verdict explicitly does NOT claim

```text
 * It is NOT a claim that the required behaviour already exists.
   §17 records ten OPEN findings (F-1 … F-10) verified against current code.
 * It is NOT an acceptance verdict. No implementation, no verification and no
   acceptance testing was performed by this task (see the reporting block).
 * It is NOT a claim that the existing implementation is compliant.
   F-1 in particular means the current code is, in places, the OPPOSITE of the
   ratified model (relationship existence admitting access).
 * It does NOT authorise a schema change by itself. Migrations require their
   own inspected, reviewed change (B-1, §18.1, AGENTS.md §66/§67).
 * It does NOT close the design report. It re-scopes it: the rejected elements
   (§9.2, §10.3) must never be built, and the §9 acceptance matrix rows that
   changed require re-verification (AC-U-11).
```

### 22.3 Conditions attached to this readiness

```text
 C-1  The implementer must treat §19.3 as STOP lines, not as to-dos.
 C-2  No implementation may be reported complete while an unexpected ALLOW is
      outstanding in any §20.4 negative test (AGENTS.md §45).
 C-3  The implementation report must state IMPLEMENTED / TESTED / VERIFIED /
      ACCEPTED separately and must not merge the BLOCKED sub-scopes into a
      pass total (AGENTS.md §52, §73).
 C-4  Frozen UX (D17, D19, D21, N1, N3) remains frozen; any conflict between
      this document and a frozen decision must be raised as a finding rather
      than resolved silently (§18.2 B-13).
 C-5  Any capability, mode or profile representation introduced must be
      default-DENY: absence of an explicit grant is a denial (§7.4, F-10).
```

### 22.4 Residual risks carried into implementation

| Risk | Why it matters | Mitigation |
|---|---|---|
| **R-1** F-1 is a live over-permission path, not a gap | Every consultant route reusing relationship-based admission is a potential cross-client ALLOW | Fix admission first (AC-F-1) and prove it with NT-10…NT-12 before building on top |
| **R-2** The capability model and the profile model can drift apart | Two ceiling/authority concepts are easy to conflate; that confusion is the exact source of F-1 | Enforce one resolution chain (§6.2) in one place; test both directions (INV-G) |
| **R-3** Route migration to `/portal/:clientId/*` (F-7) touches live navigation | Silent route change breaks consultant workflows | Explicit, recorded migration with stated alias/redirect behaviour (B-7) |
| **R-4** Termination/persistence work touches data lifecycle | A wrong implementation reads as deletion and violates PO-10/NB-9 | Non-destructive transition tests (AC-F-14) plus explicit copy assertions (AC-U-8) |
| **R-5** Four PO blockers can stall delivery if treated as one big item | Over-scoping the blocked work delays the unblocked value | Implement to the §19.3 boundary; report the blocked sub-scopes explicitly |

### 22.5 What would change this verdict

```text
 The verdict becomes NOT_READY_FOR_IMPLEMENTATION if ANY of the following is
 established:
   1. A PO-1…PO-10 decision is found to contradict itself or §5.5.
   2. A frozen UX decision (D17/D19/D21/N1/N3) is found to actually conflict
      with a ratified PO decision rather than being compatible with it.
   3. The §19.3 blocked sub-scopes are found to be PREREQUISITES of the
      unblocked work rather than separable from it.
   4. An additional current-code finding is discovered that invalidates a
      contract section (e.g. an admission path that cannot be made
      capability-aware without re-architecting tenancy).
```

### 22.6 Closing statement

```text
 This document is a DECISION CONSOLIDATION. It resolves what the consultant
 model IS, records what the current code does, states the boundaries, and
 defines how the follow-on implementation will be judged.
 It performs no implementation, no verification and no acceptance.
 Anything it appears to assert about the running system is either evidenced in
 §1.1 / §17 or explicitly marked as a target rather than a fact.
```

**END OF DOCUMENT — CT-CONSULTANT-PO-CONSOLIDATION-01.**




















