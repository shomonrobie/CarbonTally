# CarbonTally — Consultant / Client / Workspace / Lifecycle Decision Recovery

**Document ID:** CT-CLINE-CONSULTANT-CLIENT-DECISION-RECOVERY-20260930
**Date:** 2026-09-30
**Author:** Cline (evidence recovery only)
**Mode:** READ-ONLY RECONCILIATION — no code, schema, migration, test or
documentation change beyond this one report
**Subject:** Recover the Product Owner's **already-ratified** decisions for the
consultant / client / workspace / lifecycle model (C1–C12) from authoritative
repository evidence, separate them from what is merely implemented, merely
proposed, or genuinely undecided, and state what — if anything — actually
requires a new Product Owner decision.

> **STATUS UPDATE — 2026-09-30 (later than this report; product questions only).**
> The Product Owner has since answered **all seven** questions in §6 (U-1…U-7), the storage gate
> questions in §7.2, and the entitlement/capacity question. They are now recorded as Product Owner
> decisions in `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` **§41**
> (U-1…U-7 in §41.1, capacity in §41.2, storage governance S-1…S-3 in §41.3, status reconciliation
> in §41.5). This report's question text and evidence are left exactly as authored — this note only
> records the later status. No decision below was reopened, and this report remains evidence, not
> authority. **Scope of these annotations:** the header block, §6, the §7.2 gate, the §8.2 table and
> §10 only; no question text, evidence or classification was altered.

---

## 0. Scope, method and authority

### 0.1 What this report is

1. A recovery and reconciliation of **existing** Product Owner authority.
2. A separation of five things that are routinely conflated:
   - a **product decision** (what CarbonTally must be),
   - a **frozen/approved architecture** (how it must be shaped),
   - **implementation** (what the repository actually does),
   - a **proposal** (something written down but never ratified),
   - an **undecided question** (no authority answers it).
3. A statement of **implementation gaps** where a ratified decision is not yet
   satisfied by the code.

### 0.2 What this report is NOT

- It does **not** make, infer, or "helpfully" decide any product question.
- It does **not** propose a storage namespace, schema change, migration, index,
  constraint, API, UI, or test.
- It does **not** reopen anything already ratified.
- It does **not** treat implementation, tests, or historical audits as a
  substitute for a Product Owner decision where the PO decision is the
  authority that is being recovered.

### 0.3 Authority hierarchy applied

The repository's own hierarchy (`AGENTS.md`, "Source Of Truth Order") was
applied, with the Product-Owner-relevant precedence being:

```
1. Explicit ratified Product Owner decision (dated, named register/document)
2. Later Product Owner clarification (dated, supersedes earlier PO text)
3. Frozen UX/design architecture (Product Owner Decision Register — APPROVED / FROZEN)
4. Established architecture (accepted architecture documents)
5. Cline-produced reports and registers
6. OpenHands-produced reports and registers
7. Implementation (code, migrations, tests) — evidence of behaviour, never of intent
8. Historical audits — evidence of the moment they were written, never of current state
```

Rule applied throughout: **a later explicit Product Owner decision beats an
earlier audit, an earlier architecture document, and the implementation.** Where
the implementation contradicts a ratified decision, that is reported as an
**implementation gap**, not as evidence that the decision changed.

### 0.4 Provenance

- Inspected read-only at commit `cabdca8380415e73a25cf23eb393d0b15c0af391`
  (short `cabdca8`), branch `p8-release-reconciled`, last commit
  `2026-09-29T11:04:53+06:00`.
- Baseline working tree before authoring: **105** entries in
  `git status --porcelain` (pre-existing modifications from earlier work, plus
  the pre-existing untracked
  `docs/architecture/CARBONTALLY_STORAGE_PO_EVIDENCE_REVIEW_20260930.md`).
  Those changes were **not** made by this task.
- This task created exactly one file: this report.

---

## 1. ALREADY DECIDED — DO NOT REOPEN

This is the core output. Every row below is a **Product Owner decision or a
frozen/approved architecture decision that already exists**. None of it is open
for re-litigation, and none of it was invented by this report.

| # | Already decided | Authority (document → section) | Date | Implemented? | Gap? | May be reopened? |
|---|---|---|---|---|---|---|
| A-1 | A consultant firm **can have its own customers** (client organisations). This is a fundamental CarbonTally requirement; consultants are first-class operators, **not** read-only advisers or portfolio viewers. | `AGENTS.md` → §10 "CONSULTANT OPERATING MODEL — RATIFIED" | Ratified (repo constitution) | YES — `consultant_clients`, `/v3/consultant/*` | No | **NO** |
| A-2 | A consultant may operate a **portfolio of many clients**: create/manage customers, manage the portfolio, create/manage team members, assign team members, switch active clients, operate client workspaces, upload/process client documents, map/validate data, calculate emissions, participate in review, **generate/access permitted reports**, communicate with authorised clients. | `AGENTS.md` → §10 (the explicit list) | Ratified | Mostly YES; reporting blocked → gap G-1 | YES (reporting) | **NO** |
| A-3 | Consultant access is limited to organisations they are **authorised** to operate; **cross-consultant client access must be denied**. | `AGENTS.md` → §10 (final two rules); negative-test mandate `AGENTS.md` → §45 | Ratified | YES — RLS `is_org_consultant` + API `ensure_consultant_org_access` | No | **NO** |
| A-4 | A consultant–client relationship is an **explicit relationship**; a client initially belongs to a consultant under the established consultant operating model. | `AGENTS.md` → §11; Actor Model §37.2 (`consultant_clients`, "never the data owner") | Ratified | YES — `consultant_clients` with lifecycle | No | **NO** |
| A-5 | A client may later: **remain**, **leave the consultant**, **become a direct CarbonTally customer**, or **use another consultant**. | `AGENTS.md` → §11 | Ratified | Partial — (a)/(b) implemented (D19/D35), (c) handover not implemented → gap G-2 | YES (handover) | **NO** (the four options are decided) |
| A-6 | When a consultant relationship ends: the **same `organisation.id` is preserved**, data is preserved, history is preserved, provenance is preserved, and consultant access is revoked. | `AGENTS.md` → §11 | Ratified | YES — soft lifecycle + audit | No | **NO** |
| A-7 | **Do NOT clone the organisation merely to change consultant ownership.** | `AGENTS.md` → §11 (final line) | Ratified | YES — no cloning path exists | No | **NO** |
| A-8 | An organisation is the **tenancy / data-ownership anchor**; consultant relationships sit **beside** the organisation tenancy spine and never inside it. | Actor Model §37.2, §37.5; `AGENTS.md` §7 isolation axes; Spec §"Customer/Organization — tenant that owns data" | Established architecture (accepted) | YES | No | **NO** |
| A-9 | A CAMS client **must remain an independent organisation** (its own `organization_id`), because in-place independence is what preserves tenant isolation, data ownership, reporting boundaries and a future direct CarbonTally relationship. Stated as a **HARD PRODUCT DECISION**. | PO decision `CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` (D2) → §13 "Hard product decisions", §21 | 2026-09-25 | YES | No | **NO** |
| A-10 | Organization **identity** must be distinguished from organization **relationships** (`organization_type` vs relationship records); a client's relationship change must never rewrite its accounting data. | PO decision D2 → §21; `CT-PO-P17-DECISION-01` capability/applicability contract | 2026-09-25 | Partial — `organization_type` exists; a generic relationship table is **not** implemented (see U-4) | YES (reconciliation) | **NO** (the separation itself is decided) |
| A-11 | In a consultant-managed arrangement the **client owns its data, its reports and its evidence**; the consultant does **not** become the data owner and holds **delegated, auditable** access only. | PO decision D2 → §8, §14, §24 (reporting belongs to the client org), §25 (evidence belongs to the org whose accounting it supports); Actor Model §37.5 (`consultant_clients` "never the data owner"); `CT-PO-P17-ARCH-01` item 14; `CT-PO-P17-DECISION-01` items 9–10 ("data ownership remains with the client organization; operator identity distinct from ownership") | 2026-09-25 | YES (ownership + acting-for provenance) | No | **NO** |
| A-12 | **ACTING FOR is operational CONTEXT, not an authorization boundary.** It never grants access; the actor must already be entitled (membership or an `active` consultant grant); ownership stays `organization_id`; it is persisted so provenance survives membership/consultancy changes. | PO decision D2 → §22, §23; `CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` §35; UIUX-01 §6, §44; executed in `backend/domain/acting_for.py`, `backend/api/accounting_context_auth.py` | 2026-09-25 | YES — `acting_for`/`actor_organization_id` columns, `domain/acting_for.py`, `api/accounting_context_auth.py`, tests | No | **NO** |
| A-13 | There is **ONE accounting engine** and **no parallel consultant engine** — no second Scope 2 path, no duplicated factor-selection rule, no duplicate evidence model. Consultants get a portfolio/delegation layer **on top of** the same engine. | PO decision D2 → §15, §37, §38; `backend/domain/cams.py` docstring (persona differs only in *what it may ask for*) | 2026-09-25 | YES — single `resolve_accounting_dimensions` path | No | **NO** |
| A-14 | The **relationship end is enforced**: only `consultant_clients.status = 'active'` grants access (D15), in **both** RLS and API. `suspended`/`ended` grant access to nothing. | PO decision D15 (with D20); migration `20260821000000_d20_d15_active_consultant_grant.sql`; `20260822010000_d27_d19_customer_lifecycle.sql` §2 comments | PO decision + accepted architecture | YES | No | **NO** |
| A-15 | Consultants **must never perform Customer Approval**; QC and final approval are not consultant capabilities. Review participation is delegated; approval is the client's. | P6-2 PO Decision Register D5/D9; P6-0 clarification `C-SEC-005`; Actor Model §37.1; UIUX D2 (review/approval are distinct operations with distinct permissions) | Approved / frozen | YES (capability model grants no approval) | No | **NO** |
| A-16 | The **consultant capability model is the existing six-flag model** (`can_manage_clients`, `can_upload_documents`, `can_generate_reports`, `can_manage_team`, + processing flags); **no new flag** is introduced. | `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` → "P6-2C invariants remain frozen (do not reopen)" and the line-394 note ("no new flag; the existing six-flag model") | PO decision (frozen) | YES — `consultant_firm_members` flags | No | **NO** |
| A-17 | **Self-service onboarding (D35)**: a new organisation may look up an existing consultant, verify it and **choose** the relationship; the customer becomes an **OWNER** of its organisation; **`USE ALL` adopts existing data in place** (same `organization_id`, no copy, no export/re-import); `customer_type = 'direct'`; **all ACTIVE consultant grants end**; **`DISCARD` deletes nothing**. | Actor Model → §43.1 (D19/D35), §48 (D35); migration `20260822010000_d27_d19_customer_lifecycle.sql`; `backend/api/v3_discovery.py` (`set_customer_type`); `tests/unit/api/test_v3_discovery.py`, `test_self_service_onboarding.py`, `tests/unit/domain/test_d19_domain.py` | Approved + implemented | YES | Billing/entitlement act after conversion → gap G-3 | **NO** |
| A-18 | **Revocation removes consultant access only.** It is explicitly **not** data deletion, not data movement, not archival, and not ownership transfer. The client organisation survives its consultant relationship. | `AGENTS.md` §11; PO decision D30 (`CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md`: revocation removes active access but **never** deletes client data; soft `status='ended'` + audit); Actor Model §37.7 (five distinct concepts); D19 `DISCARD` deletes nothing | PO decision (ratified) | YES — soft end + audit + no delete | No | **NO** |
| A-19 | Active-client model: a consultant works across approved client organisations **one active client at a time**, the active client is always explicit, organisation isolation and one-account-one-role are preserved; the server re-authorises the client id on every request. | UIUX Product Owner Decision Register v1 → **D3 "Consultant Operating Model"**, status **APPROVED / FROZEN** (lines 117–134) | Approved / frozen | YES — frontend-local active client (`localStorage('v3_consultant_active_client')`) + `_checked_client` + `ensure_consultant_org_access` per request | Client-switch list **display** filtering is UX backlog only | **NO** — **read carefully:** this is the *consultant's UI context*, **not** a per-client exclusivity constraint (see C2 / U-1) |
| A-20 | **Entitlement/commercial ownership during consultant-managed operation** belongs to the client organisation — the client organisation owns the processing entitlement consumed on its behalf. | P6-0 / P6-BILL-1 clarification | Ratified PO clarification | Partial (billing activation deferred) | YES (SB-07 / SB-08) | **NO** (the ownership rule is decided) |
| A-21 | **Data ownership and accounting governance are different things**: customer-provided operational data does not automatically become reportable, and the governed accounting system is CarbonTally's, not the client's or the consultant's to redefine. | PO decision D2 → §7, §8, §9, §10 | 2026-09-25 | Partial (governance implemented in the domain layer) | No | **NO** |
| A-22 | **No duplicate data models / no parallel tenant abstraction** may be introduced for consultants or clients. | PO decision D2 → §21, §22; `AGENTS.md` §64 (no duplicate tenant abstractions); Actor Model §37.13-K18 | 2026-09-25 | YES as of writing | No | **NO** |
| A-23 | **The consultant firm is itself a real CarbonTally organisation** with its own Scope 1/2/3 accounting data, **additively** — a consultant profile without a firm organisation keeps working exactly as before. | `ARCH-06 HIGH-01` as implemented: `organizations.organization_type` CHECK `('CUSTOMER','CONSULTANT','PROCESSING_ENTITY','CARBONTALLY_INTERNAL')` + `consultant_profiles.organization_id` FK `ON DELETE SET NULL` (`supabase/migrations/20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` lines 245–292) | Accepted architecture decision (P17-A) | YES (columns exist; NULL-tolerant) | See U-4 (vocabulary reconciliation) | **NO** as a decision; **reconciliation** of the vocabularies is open |
| A-24 | Consultant-side **client metadata** (`client_name`, contacts, billing plan/cycle, tags, notes) is a **consultant relationship record**, while the accounting tenancy stays `organizations`. | `consultant_clients` DDL `supabase/migrations/00000000000000_init_schema.sql` lines 1554–1574; Actor Model §37.2 | Established architecture (accepted) | YES | No | **NO** |

### 1.1 The recovered model in one paragraph (no new information)

A **client is an independent organisation** (`organization_id` is the only
tenancy and data-ownership anchor). A **consultant firm is also an organisation**
(`organization_type = 'CONSULTANT'`) and is **never** the owner of its clients'
data. The two are connected by an **explicit, revocable, enforced relationship**
(`consultant_clients`, access only while `status = 'active'`), which grants the
consultant **delegated operational access** to that client's workspace — never
ownership. Ending the relationship **revokes access and preserves everything
else** (identity, data, history, provenance); it is **not** deletion, **not**
movement, **not** archival, **not** ownership transfer, and **not** grounds to
clone the organisation. The client may stay, leave, **become a direct CarbonTally
customer in place** (`USE ALL`, no copy; customer becomes OWNER; `customer_type`
becomes `'direct'`; consultant grants end), or use another consultant. When a
consultant or team member operates a client workspace, the operation is
**attributed** to the acting-for organisation (provenance) while **authorization**
still comes only from membership or an active grant.

---

## 2. DECISION-AUTHORITY TABLE (C1–C12)

Classification vocabulary (exactly one per row):
`RATIFIED` · `RATIFIED—IMPLEMENTED` · `RATIFIED—IMPLEMENTATION GAP` ·
`ARCHITECTURALLY ESTABLISHED` · `IMPLEMENTED BUT NOT PO-RATIFIED` ·
`PROPOSAL` · `SUPERSEDED` · `CONFLICTED` · `NOT ESTABLISHED`.

| ID | Question | Classification | Decision authority | Date | PO-ratified? | Arch. established? | Implemented? | Implementation evidence | Gap / conflict | PO decision required? |
|---|---|---|---|---|---|---|---|---|---|---|
| **C1** | Consultant → many clients (portfolio) | **RATIFIED—IMPLEMENTED** | `AGENTS.md` §10 ("manage their customer portfolio", RATIFIED); UIUX D3 (APPROVED/FROZEN); PO D2 §12 (portfolio tree Client A/B/C), §17; Actor Model §7–§8 ("Multiple clients: YES") | Ratified; PO restated 2026-09-25 | **YES** | YES | YES | `consultant_clients` (N rows per `consultant_id`); `ConsultantsRepository.list_clients`; firm-1 with client-a + client-b in `tests/unit/api/` consultant suites | None | **NO** |
| **C2** | Client → **one active consultant** (per-client exclusivity) | **NOT ESTABLISHED** as an exclusivity rule; implementation is deliberately non-exclusive | **No authority states per-client exclusivity.** The nearest text is UIUX D3 "one active client at a time", which is the *consultant's UI context*, not a constraint on the client. Actor Model §37.3 states the opposite of enforcement: multiple grants to one org "**are schema-representable**", and there is "no **exclusivity** … enforcement" | — | **NO** | **NO** — the **non-exclusive** model is what is established | Non-exclusive by construction | `UNIQUE(consultant_id, organization_id)` only (`init_schema.sql` lines 1571, 2143–2144) = one row **per pair**, **not** one per organisation; no partial unique index; each firm resolves only its **own** grant (`get_client_by_org(firm_id, organization_id)`) with no cross-firm exclusivity check anywhere; a firm's `list_clients` lists all of its clients; adoption ends **all** active grants (implying several can exist) | Reading D3 as exclusivity would be a misread — flagged as K-2 | **YES — see U-1** |
| **C3** | Client = a **normal CarbonTally organisation** (not a second tenant kind) | **RATIFIED—IMPLEMENTED** | PO D2 §13 ("**HARD PRODUCT DECISION**: the client must remain an independent organization"), §21 (identity vs relationship); `AGENTS.md` §7 (org = data tenant) + §64 (no duplicate tenant abstractions); Actor Model §37.2 ("org-scoped tenancy spine"); `CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` D35 §48 (real owner role model reused; no second role system, no tenancy abstraction) | 2026-09-25 (PO); earlier architecture | **YES** | YES | YES | `organizations` + `organization_members` are the only client tenancy; client orgs appear in `/v3/organizations`, reports, dashboards, exports like any other tenant; no client-specific tenant table exists | `organizations.customer_type` ('direct' / 'consultant_managed') and `organization_type` coexist — both informational (see K-3) | **NO** (decision); **U-4** covers vocabulary reconciliation only |
| **C4** | **Workspace capability parity** — the consultant can do in a client workspace what the client can | **RATIFIED—IMPLEMENTATION GAP** | RATIFIED scope: `AGENTS.md` §10 (documents, processing, mapping, validation, calculation, review participation, **"generate/access permitted reports"**, messaging); PO D2 §15 (same capabilities subject to delegated permissions), §37–§38 (no parallel engine); Actor Model §37.12 managed-service mode | Ratified; PO restated 2026-09-25 | **YES** | YES | **PARTIAL** | Present: processing, mapping, validation, calculation, evidence, messaging, accounting-context acting-for (`api/accounting_context_auth.py`); D21 branding resolves for a consultant with an active grant in `api/v3_reports.py` | **G-1** Reporting/disclosure parity **missing**: `v3_reports` endpoints are gated by `require_org_member()`; a consultant may not open/generate/download a client report even though PO text says "permitted reports". `CT-FEATURE-AUDIT-P1-P8X-001` §1.2/§6 recorded this and asked for a PO decision; the 2026-09-25 CAMS decision answers the *direction*, not the *implementation* (see K-5) | **NO** for direction (already ratified); implementation only |
| **C5** | **Client owns its data**; consultant is a delegated operator | **RATIFIED—IMPLEMENTATION GAP** | PO D2 §8 (ownership vs governance), §14 (consultant does not become owner), §24, §25; Actor Model §37.5 (`consultant_clients` "never the data owner"); `CT-PO-P17-ARCH-01` item 14; `CT-PO-P17-DECISION-01` items 9–10; PO D30 | 2026-09-25 | **YES** | YES | Ownership YES; **per-client delegation config NO** | `organization_id` is the owner on every path (`domain/acting_for.py`); `acting_for`/`actor_organization_id` on accounting objects (migration `20261010000000` §7); consultant read/write only via an `active` grant | **G-4** Per-client delegated **capability** configuration (PO D2 §18 shows Client A/B/C with *different* consultant capabilities) is not implemented: capability today is **firm-level** (`consultant_firm_members.can_*`) + `client_access uuid[]` + engagement — not a per-client capability set. Mechanism open → **U-3** | **YES — see U-3** (mechanism only; ownership is decided) |
| **C6** | Consultant relationship is **separate from** organisation identity | **RATIFIED—IMPLEMENTED** | PO D2 §21 (distinguish organization identity from relationships), §13 (separate relationship record `consultant_org_id`/`client_org_id`/`status`); `AGENTS.md` §7 (relationship is its own isolation axis); Actor Model §37.2; FPD register D22 (four access axes never interchangeable) | 2026-09-25 | **YES** | YES | YES | `consultant_clients` is its own table with its own lifecycle/RLS; `consultant_profiles.organization_id` gives the firm its own tenant **without** touching relationship rows (migration comment: does "**NOT** touch `consultant_clients` (the ratified relationship table, reused unchanged)"); `api/accounting_context_auth.py` resolves `OWN` / `CONSULTANT_CLIENT` / `CARBONTALLY_INTERNAL` from authoritative state | No generic `organization_relationship` table exists — not required: PO D2 §21 says inspect and **reuse** the existing organization/relationship architecture, which `consultant_clients` satisfies | **NO** |
| **C7** | **Revocation preserves the client's data** (access ends; data does not) | **RATIFIED—IMPLEMENTED** | `AGENTS.md` §11 (same `organisation.id`, data/history/provenance preserved, access revoked, no cloning); PO D30 (FPD register: revocation removes **active access only**, **never** deletes client data; soft `status='ended'` + audit); PO D15 (only `active` grants access); migration comments in `20260822010000_d27_d19_customer_lifecycle.sql` (`status` = active/suspended/ended/inactive; `ended_by` is provenance, "not authorization") | Ratified | **YES** | YES | YES | Soft lifecycle (`ended_at`, `ended_by`, `lifecycle_updated_at`) + audit; revocation API never deletes accounting rows; `tests/unit/api/test_consultant_revocation.py`, `test_p6_2e_consultant_lifecycle.py` assert access removed and org/data intact; `organization_id` FK from `consultant_clients` is `ON DELETE CASCADE` **on organisation deletion only** (a different action, not revocation) | Residual (implementation, **not** a product conflict) — **R-1**: RLS policy `cc_delete_own_firm` grants a firm DELETE on its own `consultant_clients` rows, so a **hard** relationship-row delete is possible at the DB layer while the API uses soft-end. Row deletion destroys relationship provenance (it does not touch client data) | **NO** for the product decision; **R-1** is an implementation hardening item |
| **C8** | A client organisation **can exist without any consultant** | **RATIFIED—IMPLEMENTED** | `AGENTS.md` §11 (the client "may leave the consultant"; organisation survives); PO D2 §13 (client independence; future direct relationship preserved); Actor Model §37.4 (relationship ends → client leaves/transitions/switches); FPD D35 §48 (an organisation can be created with **no** consultant at all) | Ratified | **YES** | YES | YES | No constraint anywhere requires a client to have a consultant: `organizations` has no `consultant_id`; no NOT NULL/FK from clients to grants; `organization_members` owners operate freely; `v3_discovery` onboarding path creates/attaches with no grant; `consultant_clients.status` values `ended`/`inactive` are legitimate terminal states | Note the distinction the evidence requires: "an organisation may **exist** and be fully usable by its own members with no consultant" is implemented; "such an organisation may hold its own CarbonTally **subscription/entitlement**" is a billing gap (G-3) | **NO** |
| **C9** | A consultant-managed client can **later become a direct CarbonTally customer** | **RATIFIED—IMPLEMENTED** | `AGENTS.md` §11 ("become a direct CarbonTally customer"); Actor Model §37.1(1) and §37.4(b) **in-place transition (preferred)**; PO D2 §13/§21 (preserve the future direct relationship without restructuring accounting data); PO D35/D19 (§43.1, §48) | Ratified | **YES** | YES | YES (in-place), with commercial gap | Implemented in place: `organizations` row and all org-scoped data unchanged; client users added as `organization_members` **OWNER**; **all ACTIVE consultant grants ended**; `customer_type = 'direct'`; `USE ALL` = adopt in place, **no copy/export/re-import**; `DISCARD` **deletes nothing**; `backend/api/v3_discovery.py` (`set_customer_type`); covered by `test_v3_discovery.py`, `test_self_service_onboarding.py`, `test_d19_domain.py` | **G-3** Commercial activation after conversion (subscription/entitlement) is **not** implemented — the org becomes `direct` but no entitlement is provisioned (SB-07/SB-08; entitlement source-of-truth open). **G-2b** no customer-facing engagement list UI for the accept/reject flow (client-side) | **NO** for the conversion decision; **G-3** needs a PO decision on entitlement source of truth → **U-7** |
| **C10** | **Ownership during conversion** — same organisation becomes the direct customer; the client's users become **OWNER**s | **RATIFIED—IMPLEMENTED** | Actor Model §43.1 (D19: "customer becomes an org owner"; `customer_type = 'direct'`) and §48 (D35: "**USE ALL** adopts in place (existing org id preserved, customer becomes owner, ACTIVE consultant grants end, `customer_type=direct`)"); PO D2 §24/§25 (ownership of reports/evidence) + §21 (no restructuring) | Ratified | **YES** | YES | YES | Asserted by tests: owner membership created; consultant grants ended; `customer_type` set to `direct`; `tests/unit/domain/test_d19_domain.py`, `tests/unit/api/test_self_service_onboarding.py` | Two governance boundaries are **deliberately** unchanged and must not be read as gaps: (1) `customer_type` is **informational, never authorization** (migration comment: "NEVER used as an authorization source — access is always derived from memberships/grants/RLS"); (2) becoming a direct customer does **not** by itself grant accounting powers — governance stays with CarbonTally (A-21). Post-conversion **entitlement provisioning** remains G-3 | **NO** |
| **C11** | **Revocation ≠ data deletion / movement / archival / ownership transfer** | **RATIFIED—IMPLEMENTED** | `AGENTS.md` §11; PO D30 ("never deletes client data"); Actor Model §37.7 — **five distinct concepts** (relationship, authorization, direct-customer status, leaving CarbonTally, platform suspension) are never collapsed; Actor Model §37.4/§37.5 (data preserved by identity of `organization_id`; **no copy, no export/re-import**); PO D19 §7 (`DISCARD` deletes nothing) | Ratified | **YES** | YES | YES | No delete/move/archive/transfer path exists on revocation; lifecycle is `active → suspended → ended` with provenance columns; destructive deletion of organisational data is **deferred** policy (destructive-deletion question is explicitly deferred, not decided) | **NOT ESTABLISHED (and must NOT be invented here):** what happens to **consultant-generated artefacts** (documents the consultant uploaded, consultant-side notes/tags, branding artefacts) after the relationship ends. No authority defines archive, transfer, or ownership-transfer semantics for them. See **U-5** | **YES — see U-5** |
| **C12** | **Consultant handover** (Client A → Consultant B) | **ARCHITECTURALLY ESTABLISHED** (direction) — **mechanism NOT ESTABLISHED** | `AGENTS.md` §11 ("use another consultant"); Actor Model §37.4(c): consultant switch "is representable **today at the data level** (multiple firms may hold grants to one org); **requires an explicit handover workflow and end-of-access enforcement for the outgoing firm (D15)**"; Actor Model §37.3: "no API/frontend flow and no exclusivity or handover enforcement"; Actor Model §37.1/§37.4 lifecycle diagram branch (c) "(new grant; handover)"; UIUX D3/D8 (active-client model); P6-1C controlled engagement implements the **incoming** firm's route | Ratified direction; sequence undecided (no authority fixes the mechanism) | **DIRECTION ONLY** — the mechanism is not ratified | YES (direction) | **PARTIAL** | Enforced today: end-of-access for the outgoing firm (D15: only `active` grants access) — so a handover *can* be executed as **end A, then engage B** using existing primitives (P6-1C controlled engagement for B). **Not** implemented: any handover workflow/API/UI, any who-initiated record on the consultant surface, and any rule that orders the two operations | **U-2**: is a **sequential** handover (outgoing grant ends *before* the incoming grant becomes active) the required model, or is **concurrent multi-consultant** access permitted (which the current schema allows)? Also whether handover must be atomic/transactional. Separately, Actor Model §37.3's "no who-initiated-the-end record / no lifecycle-change audit on the consultant surface" is a **stale** statement (see K-7) | **YES — see U-2** |

### 2.1 Scoreboard

| Classification | Count | Items |
|---|---|---|
| RATIFIED—IMPLEMENTED | 9 | C1, C3, C6, C7, C8, C9, C10, C11 (+ the A-rows) |
| RATIFIED—IMPLEMENTATION GAP | 2 | C4, C5 |
| ARCHITECTURALLY ESTABLISHED (mechanism open) | 1 | C12 |
| NOT ESTABLISHED | 1 | **C2** (per-client exclusivity) |
| CONFLICTED (unresolved) | 0 | — |

**Answer to the central question of this recovery: of C1–C12, only C2 is a
genuine gap in Product Owner authority.** C12's *direction* is ratified but its
*mechanism* is undefined (U-2). Everything else in C1–C12 is already decided.

---

## 3. CONFLICTS, STALE STATEMENTS AND MISREADING HAZARDS

These are **documentation** conflicts, not product-policy conflicts. Each is
resolved by the authority hierarchy in §0.3 — none reopens a decision.

### K-1 — Stale audit finding: "consultant → arbitrary organisation is incompatible / D-D CONFLICT"

- **Claim:** `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md` (2026-09-21), row C7,
  states that "consultant linking to an arbitrary pre-existing organisation" is
  **NOT compatible as-is** and that the authorised-engagement mechanism is
  "unresolved decision **D-D — CONFLICT — PO DECISION REQUIRED**".
- **Current authority and runtime truth:** the **P6-1C controlled engagement**
  boundary was implemented on 2026-09-06
  (`supabase/migrations/20260906090000_p6_1c_consultant_engagement.sql`,
  `docs/cline/CARBONTALLY_P6_1C_ENGAGEMENT_CONFIRMATION_REPORT.md`): attaching an
  **existing** organisation to a firm is a *pending engagement* the client must
  accept; only acceptance makes the grant `active`. The same audit's own feature
  matrix lists P6-1C as implemented/current.
- **Resolution:** the audit's C7 row is **internally inconsistent and stale**.
  The mechanism is established **and** implemented. What remains is (a) a PO
  **ratification record** for whichever D-D option was selected, and (b) the
  client-facing UI for the accept/reject flow (G-2b). Recorded as a
  documentation defect — **not** a conflict to resolve by re-deciding behaviour.

### K-2 — Misreading hazard: "one active client at a time" ≠ per-client exclusivity

- **Source:** UIUX Product Owner Decision Register v1 → **D3** (APPROVED/FROZEN):
  "A consultant works across approved client organisations **one active client at
  a time**".
- **Correct reading:** D3 constrains the **consultant's UI/context** (which
  client is being operated *now*, always explicit, frontend-local, re-authorised
  server-side). It says **nothing** about how many consultants may hold an
  `active` grant on the same client organisation.
- **Authority for the client side:** Actor Model §37.3 — multiple grants to one
  org "**are schema-representable**… no exclusivity or handover enforcement".
- **Resolution:** do not cite D3 as evidence for C2. C2 remains **undecided**
  (U-1).

### K-3 — Two overlapping organisation vocabularies (`customer_type` vs `organization_type`)

- `organizations.customer_type` — `'direct' | 'consultant_managed' | NULL`,
  explicitly **informational, NEVER authorization** (migration
  `20260822010000_d27_d19_customer_lifecycle.sql` §1 comment).
- `organizations.organization_type` — CHECK
  `('CUSTOMER','CONSULTANT','PROCESSING_ENTITY','CARBONTALLY_INTERNAL')`,
  **NULL treated as CUSTOMER** for backward compatibility (migration
  `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql`
  lines 245–269).
- PO D2 §20/§21 requires the consultant-organization concept to be
  **reconciled** with the existing organization/capability architecture, and §21
  requires organization *identity* to be distinguished from organization
  *relationships*.
- **Resolution:** the *decisions* (identity vs relationship; additivity; no
  second tenancy model) are ratified. The **reconciliation of the two
  vocabularies is not done** and is a **PO decision about the target data
  model** → **U-4**. Neither column may be treated as an authorization source
  meanwhile.

### K-4 — Consultant reporting parity: ratified text vs running gate

- **Ratified:** `AGENTS.md` §10 ("generate/access permitted reports"); PO D2 §15
  (a consultant may operate the same functionality for authorised clients,
  subject to delegated permissions) and §24 (reporting belongs to the client
  org).
- **Running code:** `backend/api/v3_reports.py` gates report list / generate /
  open / download with `require_org_member()`; a consultant is resolved there
  only for **branding** (`resolve_report_branding`, which explicitly handles "a
  consultant with an ACTIVE grant (D15)").
- **Resolution:** direction ratified, **implementation lags** → **G-1**. Not a
  conflict, and not an open PO question about direction.

### K-5 — `CT-P8 … P-1` "PO decision required" is SUPERSEDED

- `docs/ohd/reports/CT-P8-CURRENT-STATE-GAP-RECONCILIATION-AND-CONSULTANT-CLIENT-PARITY-20260915.md`
  raises **P-1** (consultant client reporting/disclosure parity) as *requiring a
  PO decision*.
- The later **2026-09-25 PO decision** (D2 §15, §24;
  `CT-PO-P17-POST-ARCH-DECISIONS-20260925.md`) decides the direction. Per §0.3
  the later explicit PO decision wins.
- **Resolution:** **SUPERSEDED.** P-1 must not be put to the Product Owner again
  as an open question; the residue is implementation (G-1).

### K-6 — D-number collisions across registers (documentation hazard)

- `D19` means **consultant transition / customer lifecycle** in the Actor Model
  (§43.1) **and** something else in the UIUX register; `D35` means **self-service
  onboarding** in the Actor Model (§48) **and** durable automatic processing in
  the FPD register; `D27` is customer lifecycle here.
- **Consequence:** a citation by number alone is not safe. Every authority claim
  in this report therefore cites **document + section/line**, not a bare
  `Dnn`. No decision is affected; only citation hygiene.

### K-7 — Stale Actor Model gap statements (superseded by later decisions + code)

`docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §37.3/§37.5
is a **snapshot of 2026-09-15 gaps**. The following statements in it are **no
longer true** and must not be quoted as current:

| Actor Model statement | Status now |
|---|---|
| "No formal **direct-CarbonTally-customer** state on `organizations`." | **SUPERSEDED** — `organizations.customer_type` exists (`'direct'`, `'consultant_managed'`). |
| "No **relationship-end enforcement** — `consultant_clients.status` is a display/soft flag only; both `is_org_consultant` (RLS) and `ensure_consultant_org_access` (API) ignore it." | **SUPERSEDED** — D15/D20 (migration `20260821000000`) + D27 lifecycle (`20260822010000`) make `status = 'active'` the sole access predicate in **both** RLS and API. |
| "No transition/handover workflow, **no who-initiated-the-end record**, no lifecycle-change audit on the consultant surface." | **PARTIALLY SUPERSEDED** — `ended_at` / `ended_by` / `lifecycle_updated_at` + audit exist (provenance of who ended). The **handover workflow** part is still accurate → U-2. |
| "Multiple consultant grants to one org … no exclusivity or handover enforcement." | **STILL ACCURATE** → U-1 / U-2. |
| §37.5 "Data preservation requirements (ARCHITECTURAL GAP / NOT SUPPORTED)" | **PARTIALLY SUPERSEDED** — revocation preserves data by design and in code (C7/C11). The **destructive-deletion / retention** question is still **deferred, not decided** (U-5). |

---

## 4. RATIFIED DECISIONS WITH IMPLEMENTATION GAPS (implementation work, not decisions)

| ID | Ratified by | What is missing in the code | Evidence of the gap | Is a new PO decision needed? |
|---|---|---|---|---|
| **G-1** | `AGENTS.md` §10; PO D2 §15, §24 | Consultant access to client **reports/disclosure** ("permitted reports") | `backend/api/v3_reports.py` uses `require_org_member()` on list/generate/open/download; only `resolve_report_branding` handles a consultant grant | **NO** — direction decided (K-5) |
| **G-2** | Actor Model §37.4(c); `AGENTS.md` §11 | Consultant **handover workflow** (any API/UI/ordering rule) | No handover endpoint/UI; ordering rule undefined (`37.3` "no … handover enforcement") | Direction decided; **mechanism → U-2** |
| **G-2b** | P6-1C engagement decision | Customer-side **accept/reject engagement UI** (backend boundary exists) | P6-1C confirmation report notes the customer-side surface is not built | **NO** — UX backlog |
| **G-3** | PO D35 for conversion; P6-0/P6-BILL-1 for entitlement ownership | **Entitlement/subscription provisioning** after (a) conversion to direct and (b) consultant-managed operation; single source of truth for entitlement | 245 inaccessible-but-listed clients; SB-07/SB-08 outstanding | **YES** for the entitlement source of truth → **U-7** |
| **G-4** | PO D2 §18 (per-client capability example: Client A/B/C differ) | **Per-client delegated capability configuration** | Capability is firm-level `consultant_firm_members.can_*` (+ `client_access uuid[]`); no per-client capability set | **YES** for the mechanism → **U-3** |

Per §0.2, this report names gaps **without proposing** how to close them.

---

## 5. RESIDUAL RISK (implementation hardening; no product decision affected)

| ID | Observation | Why it matters | Does it change any decision? |
|---|---|---|---|
| **R-1** | RLS policy `cc_delete_own_firm` grants a consultant firm **DELETE** on its own `consultant_clients` rows (`20260803000000_rc2_rls.sql` lines 369–374; re-issued in `20260822000000_p9_rls_recursion_fix.sql` lines 103–107), while the API uses **soft** end (`status='ended'`, `ended_at`, `ended_by`). | A hard row delete erases the **relationship provenance** record; it does **not** touch client data, so A-6/A-18 are not violated in substance — but "provenance is preserved" is weaker at the DB layer than at the API layer. | **NO** — hardening item only |

---

## 6. GENUINELY UNRESOLVED — PO DECISION REQUIRED

Every item below is a question for which **no Product Owner decision, no frozen
architecture and no accepted architecture** provides an answer. They are the
**only** questions in the consultant/client/workspace/lifecycle space that may be
brought to the Product Owner. This report deliberately **does not recommend** an
answer to any of them.

> **RESOLUTION STATUS (2026-09-30): U-1 … U-7 are all RESOLVED** by explicit Product Owner decisions,
> recorded in `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41.1:
> U-1 only one active consultant at a time; U-2 sequential handover (no simultaneous active
> consultants); U-3 the same consultant permission configuration for every client; U-4 Customer
> includes both Organizations and Consultants, with organisation identity and commercial customer
> status kept distinct; U-5 consultant-generated artefacts stay with the client organisation and
> retain consultant provenance (no deletion/movement/ownership transfer); U-6 normal
> consultant-managed client users have no normal workspace access, white-label workspace access is
> permitted and transfers nothing; U-7 the consultant is the direct commercial customer and the
> client's own entitlement applies on conversion.
> The question text below is unchanged: it is the historical record of what was open.

### U-1 — Is there per-client consultant exclusivity? (from C2)

- **Question to the Product Owner:** may **more than one** consultant firm hold
  an `active` consultant–client grant on the **same** client organisation at the
  same time, or must a client organisation have **at most one** active
  consultant (with a second acceptance either prevented, or requiring the first
  relationship to end first)?
- **What exists:** a non-exclusive data model (`UNIQUE(consultant_id, organization_id)`
  = one row per *pair*); Actor Model §37.3 states multi-grant is
  schema-representable and unenforced; UIUX D3's "one active client at a time"
  governs the consultant's UI context only.
- **What does NOT exist:** any statement of intended exclusivity, and any
  enforcement mechanism (constraint, trigger, or service check).
- **Why it matters:** it changes whether a second consultant can be onboarded
  alongside an incumbent, what "the client's consultant" means to an auditor, how
  handover is staged (U-2), and what a future exclusivity rule must do with
  grants that are already concurrent.

### U-2 — Handover workflow and ordering (from C12)

- **Question to the Product Owner:** when a client moves from Consultant A to
  Consultant B, must A's access **end before** B's engagement becomes active
  (sequential, no overlap), or is **concurrent** access by A and B permitted
  during a transition window? Must the handover be a single atomic act, and who
  is entitled to initiate it (the client, the incoming firm, the outgoing firm,
  or CarbonTally)?
- **What exists:** end-of-access enforcement for the outgoing firm (D15) and the
  P6-1C controlled engagement for the incoming firm — so the *outcome* is
  reachable today, in two independent steps.
- **What does NOT exist:** any handover workflow, ordering rule, transition
  window definition, or initiating-actor rule.
- **Why it matters:** overlapping access during a handover is either a product
  feature (warm transition) or a governance defect (two firms operating one
  tenant's disclosure), depending entirely on the answer.

### U-3 — Mechanism for per-client delegated capabilities (from C5 / G-4)

- **Question to the Product Owner:** is the consultant's capability in a client
  workspace (a) the **firm/member-level** `can_*` set already frozen (A-16),
  (b) a **per-client** delegated capability set (which PO D2 §18 illustrates), or
  (c) a per-client **scope/variant** of the same set?
- **What exists:** PO D2 §18 shows each client with its own capability context;
  A-16 freezes the six-flag model and forbids inventing a new flag.
- **What does NOT exist:** a decided mechanism reconciling §18 with the frozen
  flag model — i.e. whether the per-client difference is expressed by
  *configuration of the same set* (engagement / `client_access`) or requires a
  new per-client capability structure.
- **Why it matters:** it is the difference between two materially different
  authorization data models, and A-22 / PO D2 §22 forbid introducing a duplicate
  model without a decision.

### U-4 — Reconciliation of `customer_type` and `organization_type` (from K-3)

- **Question to the Product Owner:** what is the single authoritative
  organisation-kind vocabulary — `customer_type` (`direct` / `consultant_managed`),
  `organization_type` (`CUSTOMER` / `CONSULTANT` / `PROCESSING_ENTITY` /
  `CARBONTALLY_INTERNAL`), both with explicitly defined non-authorization roles,
  or a replacement — given that PO D2 §20/§21 require reconciliation and forbid
  duplicate data models?
- **What exists:** both columns, both additive, both explicitly informational.
- **What does NOT exist:** a decision on which one is authoritative for what, or
  how the two are kept consistent (e.g. can a `CONSULTANT` org also be
  `consultant_managed`? is a `CONSULTANT` org a CarbonTally *customer*?).
- **Why it matters:** reporting/disclosure segmentation, entitlement and any
  future tenancy rule keyed on organisation kind depend on it — and §0.2 forbids
  this report from choosing one.

### U-5 — Post-revocation lifecycle of consultant-generated artefacts and retention

- **Question to the Product Owner:** after a relationship ends, what is the
  required lifecycle of **artefacts associated with the relationship or produced
  by the consultant** (documents the consultant uploaded, consultant-side notes /
  tags / engagement records, consultant branding artefacts), and is there a
  **retention or destruction** rule for any of it?
- **What exists:** the client's accounting data, history and provenance are
  preserved (C7/C11); `DISCARD` deletes nothing; `consultant_clients` carries
  consultant-side metadata (A-24).
- **What does NOT exist:** any archive / transfer / ownership-transfer /
  retention / deletion rule for consultant-side artefacts. Destructive deletion
  is explicitly **deferred** policy, not a decided one.
- **Why it matters:** this is precisely the boundary the Product Owner drew
  between "revocation" and "deletion / movement / archival / ownership transfer";
  it is also the question any storage or retention design must be answered
  against.

### U-6 — Client-side access to the workspace during a consultant relationship

- **Question to the Product Owner:** during an active consultant relationship, do
  the client's own users get CarbonTally logins/workspace access — and under which
  brand (CarbonTally co-branded, or consultant white-label) — or is
  consultant-managed mode assumed to have no client-side login at all?
- **What exists:** Actor Model §37.1 — client access is **not** automatic;
  co-branded/white-label client-facing modes are FUTURE / PARTIAL; D21 branding
  rules exist; engagement acceptance is required (P6-1C).
- **What does NOT exist:** a decision on whether and when client-side users log
  in during consultant-managed mode, and the customer-side engagement UI (G-2b).
- **Why it matters:** it determines whether a consultant-managed client is a
  first-class workspace user (with its own review/approval duties) or a party
  reachable only through its consultant.

### U-7 — Entitlement source of truth after conversion and during managed operation

- **Question to the Product Owner:** after a client becomes a direct customer (in
  place, `USE ALL`), and during consultant-managed operation, **who or what
  provisions and owns the processing entitlement**, and what is the single
  authoritative source of truth for it (SB-07 / SB-08; the
  inaccessible-but-listed clients of SB-05 belong here too)?
- **What exists:** the PO clarification that the **client organisation owns the
  entitlement consumed on its behalf** (A-20); conversion mechanics are
  implemented (A-17).
- **What does NOT exist:** the provisioning mechanism and owner, and the
  source-of-truth decision; the semantics of the `onboarding` status for
  inaccessible-but-listed clients.
- **Why it matters:** without it, going direct changes a data label but not a
  commercial reality, and quota semantics remain undefined.

---

## 7. STORAGE DECISION GATE

A storage decision (object-storage namespace layout, bucket/prefix keys, object
lifecycle/retention, or any consultant/client storage segregation) is a
**derived** decision: its key must come from the organisation/relationship model,
which is governed by the decisions recovered in §1. This gate states which
storage constraints are **already fixed by ratified decisions** and which
**must be answered by the Product Owner** before any namespace can be ratified.

### 7.1 Already fixed by ratified decisions (NOT open)

| # | Storage constraint already implied by a ratified decision | Source |
|---|---|---|
| SG-1 | The storage **tenancy key is the client organisation** (`organizations.id`). Storage may not be keyed on a consultant, because the client owns its data and a consultant "never the data owner". | A-8, A-11, C5 |
| SG-2 | Storage must **not** be reorganised, copied, re-exported or re-imported when a consultant relationship begins, ends, is suspended, or is handed over. Identity of `organization_id` is the preservation mechanism. | A-6, A-9, C7, C9, Actor Model §37.4(b) |
| SG-3 | A revocation **must not** move or delete client bytes. Whatever a retention rule says, "ended relationship" is not a data-lifecycle event for client-owned artefacts. | A-18, C11 |
| SG-4 | Creating a **second** storage/tenancy structure for consultants or clients (a "consultant namespace" duplicating the organisation namespace) is prohibited absent a PO decision, because it would be a duplicate data model. | A-22, PO D2 §21/§22 |
| SG-5 | Any storage design must distinguish **metadata from bytes** consistently in both layers; a consultant-facing relationship record (`consultant_clients` metadata) is **not** the same as the bytes it references. | A-24 |
| SG-6 | Provenance must survive membership and consultancy changes: storage records must retain **who acted** (`acting_for` / `actor_organization_id`) even if the actor's relationship later ends. | A-12, C7 |

### 7.2 Open questions that block a storage decision (PO input required)

| # | Storage question that cannot be answered from existing authority | Blocked by |
|---|---|---|
| SG-7 | **Whose space does a consultant-generated artefact occupy after the relationship ends?** (consultant-uploaded documents, consultant notes/tags/branding artefacts — archive, keep in the client space, transfer, or delete?) | **U-5** (no rule exists) |
| SG-8 | **Which organisation-kind vocabulary keys storage segmentation** — `customer_type` or `organization_type` — given both exist and their reconciliation is undecided? | **U-4** (K-3) |
| SG-9 | **Does a handover require a storage overlap/deduplication rule**, i.e. may two firms' artefacts coexist in one client's storage if concurrent access (U-1/U-2) is permitted? | **U-1, U-2** |
| SG-10 | **What is the retention/destruction rule**, if any, for any of the above — including whether destructive deletion is ever permitted (currently deferred policy, not decided)? | **U-5** |
| SG-11 | **Is storage capacity/entitlement metered per client organisation**, and if so against which entitlement (which is itself undecided)? | **U-7** |

> **CLOSURE STATUS (2026-09-30): the storage gate in §7.2 above is CLOSED in substance.** The Product Owner's
> storage governance decisions **S-1** (client organisation is the storage tenancy anchor; no physical
> consultant tenancy; provenance in metadata/audit), **S-2** (backend authorization before signing;
> short-lived signed URLs; no service-role exposure) and **S-3** (audit significant document access
> events), together with U-1/U-2/U-4/U-5/U-7, answer SG-7, SG-8, SG-9, SG-10 and SG-11 — recorded in
> `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41. No namespace, migration or
> destruction rule is implied by that closure, and no destructive rule is authorised. Storage
> Management Steps 1 + 2 are **CLOSED** (register §41.4).

### 7.3 Explicit non-action

Per the task constraint and §0.2, **this report does not propose a namespace,
bucket, prefix, key format, retention period, or migration.** It states only
which storage constraints are already entailed by ratified decisions (7.1) and
which PO answers must exist first (7.2). The pre-existing document
`docs/architecture/CARBONTALLY_STORAGE_PO_EVIDENCE_REVIEW_20260930.md` (present
in the working tree before this task, authored outside it, **not** modified by
this report) is the separately-owned storage evidence artefact; nothing here
supersedes, restates or extends it.

---

## 8. PRODUCT OWNER DECISION RECOVERY RESULT

### 8.1 What is recovered

The Product Owner's position on the consultant / client / workspace / lifecycle
model is **already substantially and coherently ratified**. Recovered:

- **Portfolio model (C1)** — a consultant firm serves many client organisations;
  consultants are first-class operators, not read-only advisers.
- **Client identity (C3, C6)** — a client **is** a normal CarbonTally
  organisation; the consultant relationship is a **separate** record, never a
  second tenancy, never a rewrite of organisation identity.
- **Ownership (C5, C10, C11)** — the client owns its organisation, data,
  reports and evidence; the consultant holds **delegated, auditable** access and
  never becomes the data owner; becoming a direct customer happens **in place**
  with the client's users as OWNERs.
- **Lifecycle (C7, C8)** — revocation **removes access only**; it is not
  deletion, not movement, not archival, not ownership transfer, and not grounds
  to clone the organisation. The client organisation survives its consultant.
- **Conversion (C9)** — a consultant-managed client may become a direct
  CarbonTally customer with **no copy, no export/re-import** (`USE ALL` adopts in
  place; `DISCARD` deletes nothing; all ACTIVE grants end;
  `customer_type = 'direct'`).
- **Direction for capability parity (C4)** and for **handover (C12)** — the
  direction is ratified even though the implementation (reporting parity) and the
  mechanism (handover) are not complete.

### 8.2 What is NOT recovered — and must be asked

Only the following are genuinely unanswered. Nothing else in this space should
be put to the Product Owner:

| # | The question | From |
|---|---|---|
| U-1 | May a client organisation have **more than one active consultant** at once, or is exclusivity intended (and then enforced)? | C2 |
| U-2 | Handover: **sequential vs concurrent**, atomic vs staged, and who may initiate? | C12 |
| U-3 | Per-client consultant capability: **same frozen flag set configured per client**, or a per-client capability structure? | C5 / G-4 |
| U-4 | Which organisation-kind vocabulary is authoritative — `customer_type`, `organization_type`, both with defined roles, or a replacement? | K-3 |
| U-5 | Post-revocation lifecycle of **consultant-generated artefacts** and any retention/destruction rule. | C11 |
| U-6 | Do **client-side users** log in during consultant-managed mode, and under which brand? | Actor Model §37.1 |
| U-7 | **Entitlement** source of truth and provisioning after conversion and during managed operation. | G-3 |

> **RESOLVED (2026-09-30):** every row above is answered by Product Owner decisions recorded in
> `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41.1 (U-1…U-7). See also the
> resolution note at the head of §6.

### 8.3 Correct handling of everything else

1. **Do not re-ask** anything in §1 — it is decided and ratified.
2. **Do not present** `CT-P8 P-1` (consultant reporting/disclosure parity) as an
   open PO question; it is **SUPERSEDED** (K-5). It is implementation work (G-1).
3. **Do not read** UIUX D3 "one active client at a time" as per-client
   exclusivity (K-2).
4. **Do not treat** the Actor Model §37.3/§37.5 gap list as current (K-7);
   relationship-end enforcement, `customer_type`, and ended-by provenance now
   exist.
5. **Do not propose** a storage namespace, schema change, or migration as part of
   this recovery; the storage gate (§7) shows why the key cannot be chosen before
   U-4/U-5 are answered.
6. **Do not infer** a decision from implementation, tests, or historical audits
   (they are evidence of behaviour only).

### 8.4 Statement of constraint compliance

- No implementation was performed or proposed.
- No storage namespace, schema, migration, constraint, API, UI or test was
  designed, suggested or scaffolded.
- No product decision was made, inferred or "recommended" by this report.
- No already-ratified decision was reopened; the only questions raised are those
  for which no authority exists.

---

## 9. FILES EXAMINED

All evidence was read **read-only**. Nothing in this list was modified. Extract
files under `/tmp/rc*.txt` are scratch greps taken from the repository paths
below; the repository paths are the authoritative sources.

### 9.1 Authority — Product Owner decisions, registers, constitution

| Path | Used for |
|---|---|
| `AGENTS.md` | §10 consultant operating model (RATIFIED, lines 376–407); §11 consultant/client relationship (lines 411–433); §45 negative tests (lines 1216–1240); §7 isolation axes; §64 no duplicate tenant abstractions; source-of-truth order |
| `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` | D2: §7–§10 ownership vs governance; §13 hard product decisions; §14 consultant not owner; §15 capability parity; §18 per-client capability; §20–§22 identity vs relationship + acting-for; §23; §24–§25 reports/evidence ownership; §37–§38 one engine |
| `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` | post-architecture PO decision set; §35 acting-for |
| `docs/architecture/CT-PO-P17-DECISION-01-CAMS-CAPABILITY-APPLICABILITY-CONTRACT-20260925.md` | capability/applicability contract; items 9–10 (ownership + operator identity) |
| `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md` | item 14 (client data ownership) |
| `docs/audit/openhands/ui-ux/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` | **D3 consultant operating model (APPROVED/FROZEN, lines 117–134)**; D2 review/approval; D8; D21 |
| `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` | D5/D9 approval separation; "P6-2C invariants remain frozen (do not reopen)"; six-flag model (line 394) |
| `docs/architecture/CARBONTALLY_PHASE6_P0_1_COMMERCIAL_CONSULTANT_CLARIFICATION.md` | `C-SEC-005`; entitlement ownership during managed operation |
| `docs/architecture/CARBONTALLY_PHASE6_P0_PO_RATIFICATION_REPORT.md` | P6-0 ratification |
| `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` | D30 revocation semantics; D35 §48; D22 four access axes; D20/D21 |
| `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` | §7–§8; §34; **§37.1–§37.7** (incl. line 1366 §37.4 lifecycles, lines 1390–1392 enforcement limits); **§43.1 (D19)**; **§48 (D35)**; K-invariants; §37.3 stale-gap list |
| `docs/audit/openhands/ui-ux/CARBONTALLY_V3_CUSTOMER_FAQ.md` and `docs/audit/openhands/CARBONTALLY_V3_CUSTOMER_FAQ.md` | customer-facing statement "consultants see one active client at a time" (line 705 in both) — used only to confirm the UI-context reading and the FAQ's non-authoritative status |

### 9.2 Reports and audits (evidence of a moment, not authority)

| Path | Used for |
|---|---|
| `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md` | C7 row / D-D "CONFLICT" claim (found stale); §1.2, §6 reporting-parity finding; P6-1C status |
| `docs/cline/CARBONTALLY_P6_1C_ENGAGEMENT_CONFIRMATION_REPORT.md` | controlled engagement boundary as implemented |
| `docs/ohd/reports/CT-P8-CURRENT-STATE-GAP-RECONCILIATION-AND-CONSULTANT-CLIENT-PARITY-20260915.md` | P-1 (superseded); P-9/SB-05 listed-but-inaccessible clients; SB-07/SB-08 |
| `docs/architecture/CARBONTALLY_STORAGE_PO_EVIDENCE_REVIEW_20260930.md` | **not examined for content; recorded as pre-existing and untouched** (see §7.3) |

### 9.3 Database schema

| Path | Lines / sections used |
|---|---|
| `supabase/migrations/00000000000000_init_schema.sql` | `consultant_clients` DDL lines 1554–1574; **`consultant_clients_consultant_org_uniq` on `(consultant_id, organization_id)` lines 2143–2144**; `consultant_firm_members` |
| `supabase/migrations/20260803000000_rc2_rls.sql` | `cc_*_own_firm` policies lines 331–374; consultant read path on relationships |
| `supabase/migrations/20260806000000_rc2_verification.sql` | constraint inventory incl. `consultant_clients_consultant_org_uniq` |
| `supabase/migrations/20260821000000_d20_d15_active_consultant_grant.sql` | D15 active-grant enforcement in RLS |
| `supabase/migrations/20260822000000_p9_rls_recursion_fix.sql` | re-issued `cc_*` policies (lines 91–110) |
| `supabase/migrations/20260822010000_d27_d19_customer_lifecycle.sql` | `customer_type` (informational, never authorization); lifecycle columns/comments lines 38–59; deny-all RLS for new tables; verification checklist |
| `supabase/migrations/20260906090000_p6_1c_consultant_engagement.sql` | controlled engagement |
| `supabase/migrations/20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | `organizations.organization_type` CHECK + comment (lines 245–269); `consultant_profiles.organization_id` (lines 271–292); accounting dims + acting-for columns; factor governance |

### 9.4 Backend code

| Path | Evidence taken |
|---|---|
| `backend/api/v3_discovery.py` | self-service onboarding / D19 adoption (`set_customer_type`, in-place ownership, grant termination) |
| `backend/api/v3_consultants.py` | `_checked_client` (line 188) and every consultant client-scoped route; firm capability exposure incl. `client_access` (lines 228, 947–951); line 502 grant lookup on create |
| `backend/api/v3_reports.py` | `require_org_member()` on all report endpoints (e.g. lines 233, 252, 294, 479–1326); consultant handled only for branding (lines 283–286, 803, 901–903, 939) → **G-1** evidence |
| `backend/api/consultant_auth.py` | firm-member capability flags (line 46 mapping; line 223 note that `client_access` does not independently grant access); grant resolution lines 231, 330 |
| `backend/api/consultant_branding.py` | `resolve_report_branding` grant lookup (line 67) |
| `backend/api/accounting_context_auth.py` | relationship kinds `OWN` / `CONSULTANT_CLIENT` / `CARBONTALLY_INTERNAL`; acting-for resolution over `get_client_by_org` / `list_clients` (lines 19, 51) |
| `backend/api/manual_processing_auth.py` | active-grant check via `get_client_by_org` (line 51) |
| `backend/domain/acting_for.py` | acting-for as provenance, never authorization |
| `backend/domain/cams.py` | "**There is ONE accounting engine**… Consultants get a portfolio/delegation layer *on top of* this engine … A persona may differ in *what it may ask for*; it cannot differ in *what makes a defensible number*" → A-13 |
| `backend/domain/partners.py` | firm-member capability model: `can_manage_clients` (line 164), `client_access` (line 176) → **G-4** evidence |
| `backend/data/consultants.py` | `get_client_by_org(firm_id, organization_id)` (line 370) — the pair-scoped grant lookup that is the only relationship check on the client side → C2 evidence |

### 9.5 Tests (behavioural evidence only)

| Path | Evidence taken |
|---|---|
| `backend/tests/unit/api/test_consultant_revocation.py` | revocation removes consultant access; capability flag required for the action; non-owner roles denied |
| `backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py` | lifecycle states; only `active` grants access |
| `backend/tests/unit/api/test_self_service_onboarding.py` | D35 onboarding incl. use/discard adoption semantics |
| `backend/tests/unit/api/test_v3_discovery.py` | `set_customer_type` behaviour |
| `backend/tests/unit/domain/test_d19_domain.py` | D19 lifecycle/transition domain rules |
| `backend/tests/integration/test_consultants.py` | `get_client_by_org` pair semantics (lines 64–68) |
| `backend/tests/unit/api/test_p17_02_organization_context.py`, `test_v3_activity_clarifications_api.py`, `test_scope_aware_authorization.py`, `test_consultant_branding.py`, `test_v3_whitelabel.py`, `test_p6_2a_r1_b1_automation_confirm_retry.py`, `test_p6_1b_membership_workspace_authorization.py` | consultant capability/branding/scope fixtures and assertions |
| `backend/tests/e2e/fixtures.py` | firm-member flag fixtures (line 47) |

---

## 10. VERIFICATION STATUS

```
VERIFICATION STATUS: COMPLETE — EXISTING DECISIONS RECOVERED; IMPLEMENTATION GAPS IDENTIFIED
```

Supporting statement of this status:

- **COMPLETE** — every item in C1–C12 was traced to either an explicit Product
  Owner decision, a frozen/approved architecture, an accepted architecture
  decision, or an evidenced absence of any of these.
- **EXISTING DECISIONS RECOVERED** — §1 records 24 already-ratified decisions
  (A-1…A-24) with their authorities; §2 classifies C1–C12; §3 resolves every
  documentation conflict found (K-1…K-7), including one stale audit "CONFLICT"
  row and one already-**SUPERSEDED** open PO question.
- **IMPLEMENTATION GAPS IDENTIFIED** — §4 records five gaps (G-1, G-2, G-2b,
  G-3, G-4) where a ratified decision is not yet satisfied by the code, and §5
  records one residual hardening risk (R-1).
- **NO NEW PO DECISIONS MADE** — §6 lists the only questions that are genuinely
  unanswered (U-1…U-7); none of them was answered, recommended, or presupposed
  here, and no storage namespace, schema change, migration, API, UI or test was
  proposed.
- **Only open C-item:** C2 (per-client exclusivity) → **U-1**. The only open
  C-item *mechanism* is C12 handover → **U-2**.

> **Addendum (2026-09-30):** as of this report's authorship the items above were open. They were
> subsequently answered by the Product Owner — see the status update in the header block, §6 and
> §7.2, and `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41. The verification
> statement of §10 remains the status of **this report**, not of the questions.

**END OF REPORT**
