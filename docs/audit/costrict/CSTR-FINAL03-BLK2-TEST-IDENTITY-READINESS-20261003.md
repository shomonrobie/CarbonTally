# CSTR-FINAL03-BLK2 — Production Test-Identity Readiness Investigation

**Report ID:** CSTR-FINAL03-BLK2-TEST-IDENTITY-READINESS-20261003
**Date:** 2026-10-03
**Investigator:** CoStrict (independent verification authority)
**Type:** READ-ONLY forensic investigation. No production mutation. No remediation.
**Frozen release:** `375a48dc1b9e9cfd74090bbf747554ae997acb59` (branch `p8-release-reconciled`)
**Predecessors:** `CSTR-FINAL03-LIVE-ACCEPTANCE-001` (raised BLK-2) · `CSTR-FINAL03-BLK1-…-TOPOLOGY-INVESTIGATION` · `CSTR-FINAL03-BLK1-POST-REMEDIATION-VERIFY-20261003` (BLK-1 cleared)

**Evidence labels:** **DC** direct code evidence · **DD** documented decision · **DS** read-only data-store observation · **LO** live public observation · **IN** inference · **NT** not testable.

---

## A. Executive conclusion

> **PARTIALLY READY — SPECIFIC ADDITIONAL IDENTITY/DATA REQUIREMENT**

Production already contains **two owner-created, PO-preserved test organisations with two active `owner`
identities** (Babu / Faria) whose provenance is ratified in the FINAL-03 data-preservation evidence
([`README.md:12`](docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md:12), **DD**). These can
legitimately support the **customer / tenant-isolation / storage** half of the acceptance matrix
(auth C1/C2/C5/C6, routing → `/home`, D1–D5, G1/G2/G5).

They **cannot** support the **staff / consultant / Processing Entity** half, because production contains
**zero** staff profiles, **zero** consultant profiles/firm memberships, and **zero** processing entities
(**DS**). Those actor types are structurally distinct in the authorization model
([`operations_auth.py:79`](backend/api/operations_auth.py:79),
[`consultant_auth.py:76`](backend/api/consultant_auth.py:76),
[`pe_auth.py:102`](backend/api/pe_auth.py:102), **DC**) and therefore cannot be collapsed into an existing
customer identity.

**BLK-2 is a test-identity / test-data readiness gap, not a product defect** (§G). No executed check failed;
the criteria are **NOT TESTED**, not **TESTED AND FAILED**.

---

## B. Existing identity inventory (minimum necessary detail)

Read-only observation of the production data store (`default_transaction_read_only = on`), plus ratified
evidence. **No credential, token, key or full account identifier is reproduced.**

| # | Actor | Provider | Org / relationship | Role | Status | Provenance |
|---|---|---|---|---|---|---|
| 1 | Owner (`sho***@gmail.com`) | **Google OAuth** | Babui Technologies UK Limited | `owner` (active) | email confirmed, not banned | owner-created test identity (**DD**) |
| 2 | Owner (`far***@gmail.com`) | **Email + password** | Faria Green Company UK LTD | `owner` (active) | email confirmed, not banned | owner-created test identity (**DD**) |

| Aggregate | Value | Source |
|---|---|---|
| `organizations` | **2** (Babui, Faria — both `is_active=t`) | **DS** |
| `auth.users` | **2** (1 `email`, 1 `google`; both confirmed, neither banned) | **DS** |
| `organization_members` | **2** (both `owner`, both `is_active=t`) | **DS** |
| `consultant_profiles` | **0** | **DS** |
| `consultant_firm_members` | **0** | **DS** |
| `consultant_clients` | **0** | **DS** |
| `processing_entities` | **0** | **DS** |
| `staff_profiles` (total / active) | **0 / 0** | **DS** |
| `staff_roles` | **1** (`pe_manager`; permissions `{can_process, can_review, can_view_all}`) | **DS** |
| `roles` (customer-org reference table) | 0 | **DS** |
| `documents` storage objects | 58 | **DS** |
| `emission_factors` | 7,049 | **DS** |

**Per-organisation data (usable for isolation/storage acceptance without creating anything):**

| Organisation | files | evidence items | manual-extraction batches | processing-queue rows |
|---|---|---|---|---|
| Babui Technologies UK Limited | 3 | 0 | 1 | 3 |
| Faria Green Company UK LTD | 8 | 74 | 1 | 8 |

**Suitability assessment (not assumed — derived):**

1. **Suitable for FINAL-03 acceptance (customer/tenant subset).** Both owners are active `owner` members of
   distinct active organisations with existing documents/queue rows → they can exercise C1/C2/C5/C6, routing
   → `/home`, D1–D5 (two distinct tenants), and G1/G2/G5.
2. **Unsuitable for staff/consultant/PE criteria.** An `owner` membership resolves to `actor_type: "customer"`
   ([`v3_context.py:99`](backend/api/v3_context.py:99), **DC**); it grants no `staff_profile`, no consultant
   membership, and no entity scope.
3. **Unavailable in-workspace.** No owner credential exists in the workspace; per the established mechanism the
   owner supplies it **at runtime only** ([`CT-STEP2-P1-ROWCANDIDATE-VERIFY-025:63`](docs/cline/reports/CT-STEP2-P1-ROWCANDIDATE-VERIFY-025.md:63), **DD**).
4. **Suitable only for specific cases.** The `owner` role is the only customer role present; **Admin / Member /
   Viewer** customer roles do not exist in production, so intra-tenant role distinctions are not covered.

---

## C. Acceptance matrix

Status vocabulary: `READY WITH EXISTING IDENTITY` · `REQUIRES ADDITIONAL AUTHORIZED IDENTITY` ·
`REQUIRES ADDITIONAL CONTROLLED PRODUCTION DATA` · `NOT TESTABLE WITHOUT MUTATION` · `NOT APPLICABLE` · `UNKNOWN`.

| Acceptance area | Criterion | Identity required | Existing identity available? | Data required? | Status | Evidence |
|---|---|---|---|---|---|---|
| Authentication | C1 successful login | 1 active owner | **Yes** (owner #2, email/password) | none | `READY WITH EXISTING IDENTITY` | **DS**/**DD** |
| Authentication | C2 authenticated request | same | **Yes** | none | `READY WITH EXISTING IDENTITY` | **DS** |
| Authentication | C5 logout | same session | **Yes** | none | `READY WITH EXISTING IDENTITY` | **DS** |
| Authentication | C6 re-login | same | **Yes** | none | `READY WITH EXISTING IDENTITY` | **DS** |
| Authentication | Google OAuth | owner #1 (Google provider) | **Account exists**; requires owner-driven Google session | none | `READY WITH EXISTING IDENTITY` (owner-driven) — else `NOT TESTABLE — AUTHORIZED GOOGLE IDENTITY UNAVAILABLE` | **DS** (§12) |
| Authentication | email/password | owner #2 | **Yes** | none | `READY WITH EXISTING IDENTITY` | **DS** |
| Authentication | `/auth/callback` | authenticated browser | **Yes** | none | `READY WITH EXISTING IDENTITY` | **DC**/**LO** |
| Authentication | `GET /api/v3/me/context` | any authenticated actor | **Yes** (customer) | none | `READY WITH EXISTING IDENTITY` | **DC** |
| Routing | staff → `/ops` | internal staff profile | **No** (`staff_profiles`=0) | `staff_profiles` + `staff_roles.permissions` | `REQUIRES ADDITIONAL AUTHORIZED IDENTITY` | [`v3_context.py:51`](backend/api/v3_context.py:51) |
| Routing | entity_staff → `/pe` | PE staff profile + active entity | **No** (`staff_profiles`=0, `processing_entities`=0) | staff profile w/ `entity_id` + entity + PE role | `REQUIRES ADDITIONAL AUTHORIZED IDENTITY` + DATA | [`pe_auth.py:102`](backend/api/pe_auth.py:102) |
| Routing | consultant → `/consultant` | consultant firm member | **No** (`consultant_profiles`=0) | profile + firm membership | `REQUIRES ADDITIONAL AUTHORIZED IDENTITY` + DATA | [`consultant_auth.py:76`](backend/api/consultant_auth.py:76) |
| Routing | customer → `/home` | org member | **Yes** (2 owners) | none | `READY WITH EXISTING IDENTITY` | [`v3_context.py:99`](backend/api/v3_context.py:99) |
| Routing | new/unresolved → `/onboarding` | account with no relationship | **No** (creating one = mutation) | none | `NOT TESTABLE WITHOUT MUTATION` | [`v3_context.py:122`](backend/api/v3_context.py:122) |
| Tenant isolation | D1, D2 (each org sees only its own data) | **both** owners | **Yes** | existing org data (both orgs) | `READY WITH EXISTING IDENTITY` | **DS** |
| Tenant isolation | D3 (cross-org object access denied) | both owners | **Yes** | existing data | `READY WITH EXISTING IDENTITY` | **DS** |
| Tenant isolation | D4 (id / path / query substitution) | one owner + the other org id | **Yes** | existing data | `READY WITH EXISTING IDENTITY` | **DS** |
| Tenant isolation | D5 (cross-tenant storage access) | both owners + existing objects | **Yes** | 11 `organization_files` / 58 objects | `READY WITH EXISTING IDENTITY` | **DS** |
| Staff/permission | E1 internal staff behaviour | staff profile (`entity_id` NULL) | **No** | `staff_profiles` + staff role | `REQUIRES ADDITIONAL AUTHORIZED IDENTITY` | [`operations_auth.py:79`](backend/api/operations_auth.py:79) |
| Staff/permission | E2 consultant/client model | consultant | **No** | consultant + client grant | `REQUIRES ADDITIONAL AUTHORIZED IDENTITY` + DATA | [`consultant_auth.py:136`](backend/api/consultant_auth.py:136) |
| Staff/permission | E3 consultant isolation | **two** consultants/firms | **No** | 2 consultant profiles + isolation | `REQUIRES ADDITIONAL AUTHORIZED IDENTITY` + DATA | **DC** |
| Staff/permission | E4 owner isolation | 2 owners | **Yes** | existing data | `READY WITH EXISTING IDENTITY` | **DS** |
| Staff/permission | E6 suspended access | identity w/ suspendable state | **No** (no non-owner actor) | membership/entity state to toggle | `REQUIRES ADDITIONAL CONTROLLED PRODUCTION DATA` (mutating) | **DC** |
| Staff/permission | E-cust. Admin/Member/Viewer distinction | non-owner customer roles | **No** | additional memberships | `REQUIRES ADDITIONAL CONTROLLED PRODUCTION DATA` (mutating) | **DS** |
| Storage | G1 authorised document access | 1 owner + existing object | **Yes** | Faria 8 / Babui 3 files | `READY WITH EXISTING IDENTITY` | **DS** |
| Storage | G2 cross-organisation denial | both owners | **Yes** | existing objects | `READY WITH EXISTING IDENTITY` | **DS** |
| Storage | G5 signed-URL behaviour | 1 owner + existing object | **Yes** | existing object | `READY WITH EXISTING IDENTITY` | **DC** |
| Calculation/report | I end-to-end pipeline | authenticated customer | **Yes** (owner) | **requires new calculations/reports** | `NOT TESTABLE WITHOUT MUTATION` (or `REQUIRES ADDITIONAL CONTROLLED PRODUCTION DATA`) | live-acceptance §15 (**DD**) |
| Email | J transactional send | authenticated customer + recipient | **Yes** (owner) | controlled non-customer recipient | `NOT TESTABLE WITHOUT MUTATION` | live-acceptance §16 (**DD**) |

---

## D. Minimum identity set

**Customer / tenant / storage half — 2 identities, both already existing (no creation):**

| # | Identity | Context | Permissions / relationship | Why required | Criteria served |
|---|---|---|---|---|---|
| 1 | Owner `sho***@gmail.com` | Babui (Google OAuth) | `organization_members.role = owner`, active | OAuth login; tenant A; cross-tenant actor | C1–C6 (OAuth), routing → `/home`, D1–D5, G1/G2/G5, E4 |
| 2 | Owner `far***@gmail.com` | Faria (email/password) | `organization_members.role = owner`, active | password login; tenant B; richer data (74 evidence items) | C1–C6 (password), D1–D5, G1/G2/G5, E4 |

Two are required **only** because cross-tenant isolation (D3/D4/D5, E4) needs **two distinct tenants** with
distinct owners. **One** owner would suffice for the single-tenant subset (C, routing `/home`, G1/G5).

**Staff / consultant / PE half — 3 additional controlled identities (creation required):**

| # | Identity type | Minimum supporting rows | Permissions needed | Why required | Criteria served |
|---|---|---|---|---|---|
| 3 | Internal staff | `staff_profiles` (active, `entity_id` NULL) + `staff_roles` with `can_review`/`can_process`/`can_view_all` | staff permission set per [`operations_auth.py:95`](backend/api/operations_auth.py:95) | Prove `staff → /ops`; E1; staff-vs-customer denial | routing → `/ops`, E1, E5/E6 |
| 4 | Consultant | `consultant_profiles` (active) + `consultant_firm_members` (active, `can_*`) + `consultant_clients` (status `active`) for one org | consultant capability flags per [`consultant_auth.py:45`](backend/api/consultant_auth.py:45) | Prove `consultant → /consultant`; client-grant boundary | routing → `/consultant`, E2 |
| 5 | Processing Entity staff | `staff_profiles` (active, `entity_id` set) + `processing_entities` (active) + PE staff role (`operator`/`reviewer`/`qc_specialist`/`pe_manager`) | PE capability set per [`pe_auth.py:63`](backend/api/pe_auth.py:63) | Prove `entity_staff → /pe`; PE isolation | routing → `/pe`, E3/E6 |

**They cannot be merged.** Staff, consultant and PE are three mutually exclusive resolution branches
([`v3_context.py:51`](backend/api/v3_context.py:51), [:68](backend/api/v3_context.py:68),
[:82](backend/api/v3_context.py:82), [:99](backend/api/v3_context.py:99), **DC**): a consultant identity is
denied `/ops`; internal staff are denied `/pe` ([`pe_auth.py:115`](backend/api/pe_auth.py:115)); PE staff are
denied ops-wide surfaces ([`operations_auth.py:104`](backend/api/operations_auth.py:104)).

**Minimum total for the FULL authenticated FINAL-03 matrix: 5 identities** (2 existing + 3 new).
`/onboarding` and non-owner customer roles would add further identities/data and are **not** part of the
minimum.

---

## E. Minimum data set

### E.1 Existing preserved data that can be reused (no creation)

| Data | Available | Supports |
|---|---|---|
| 2 active organisations with 2 active `owner` memberships | **DS** | routing → `/home`, D1–D5, E4 |
| 11 `organization_files` (Babui 3 / Faria 8) + 58 storage objects | **DS** | G1/G2/G5, D5 |
| 2 `manual_extraction_batches`, 11 `document_processing_queue` rows | **DS** | G, partial I prerequisites |
| 74 `evidence_line_items` (Faria) | **DS** | evidence/provenance context |
| 7,049 emission factors | **DS** | H (already accepted) |
| Documented **runtime-supplied** owner credential mechanism | **DD** | enables the above without storing secrets |

### E.2 Data that would have to be created (only if the new identities are authorised)

1. One `staff_profiles` row (+ linking a `staff_roles` permission row) for the internal-staff identity.
2. One `consultant_profiles` + one `consultant_firm_members` row, plus one `consultant_clients` row
   (`status = active`) linking the consultant to an existing organisation — reuse Babui or Faria as the client
   so **no new organisation** is required.
3. One `processing_entities` row + one `staff_profiles` row with `entity_id` set (PE staff) — the PE work items
   (`manual_review_queue` / `issues`) would need at least one assigned row to exercise the PE work surface.
4. For E6 (suspended access): a state toggled on a created membership/entity (mutating; isolated to the
   acceptance records).
5. For I: a disposable document → calculation → report chain **inside an existing organisation** (mutating);
   or defer I.
6. For J: a **controlled, non-customer recipient** address owned by the PO (mutating).

**Zero-unnecessary-mutation principle:** items 1–3 can all be anchored to the **existing** organisations
(no new tenant), and the runtime-credential mechanism (`§F`) avoids persisting any secret. Items 5–6 are the
only ones that would create commercial/audit artefacts and should be explicitly PO-authorised or deferred.

---

## F. Credential governance

**Existing project-approved mechanism (reuse it — do not invent a new one).**
`CT-STEP2-P1-ROWCANDIDATE-VERIFY-025` documents the authoritative pattern: a **"synthetic acceptance
identity; credentials supplied at runtime only, never written to any file, report or commit"**
([`…:63`](docs/cline/reports/CT-STEP2-P1-ROWCANDIDATE-VERIFY-025.md:63), **DD**). The FINAL-03 preservation
record likewise requires the retained identities to be described as **"controlled owner/test identities"**,
never as real customers ([`README.md:24`](docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md:24), **DD**).

**Answers to §9 of the brief:**

1. **Can an existing owner account be used?** **Yes, for the customer/tenant/storage subset** (owners #1/#2),
   with the credential supplied at runtime.
2. **If not, is a dedicated acceptance account required?** **Yes, for the staff/consultant/PE subset** — three
   dedicated controlled identities (§D).
3. **Who should own it?** The **CarbonTally Product Owner** (the same authority that owns the retained
   production identities); created only under explicit PO authorisation.
4. **What minimum permissions?** The least privilege that still exercises the boundary: staff →
   `{can_review, can_process, can_view_all}` (no `can_manage_staff`, no `can_manage_billing`); consultant →
   active firm membership + `can_*` flags for the tested actions + one active client grant; PE →
   `operator`/`reviewer` scope on a single entity.
5. **Which role?** Internal **staff** (`/ops`), **consultant** (`/consultant`), **PE staff** (`/pe`); the two
   customer identities remain `owner`.
6. **Does any acceptance require multiple identities?** **Yes** — D3/D4/D5 and E4 require **two** customer
   tenants; E2/E3 require a consultant **and** a client organisation; E3 ideally two consultants/firms.
7. **How to handle credentials?** Runtime-only, as the established mechanism; never in Git, `.env` committed to
   source, Vercel source, or CoStrict reports. Google OAuth for owner #1 is exercised by the owner in their own
   browser session (no credential is extracted).
8. **Existing approved mechanism?** **Yes** — the runtime-supplied synthetic-acceptance-identity pattern above;
   no new mechanism is needed.

---

## G. BLK-2 classification

| Category | Applies? | Basis |
|---|---|---|
| **NOT TESTED** | **Yes** | C1/C2/C5/C6, D1–D5 (authenticated), E1–E4/E6, G1/G2/G5, I, J were not executed in the live acceptance (live-acceptance §6, **DD**) |
| **UNAVAILABLE TEST IDENTITY** | **Yes — dominant cause** | No in-workspace owner credential; **zero** staff/consultant/PE identities in production (**DS**) |
| **MISSING TEST DATA** | **Yes (secondary)** | No consultant-client grant, no processing entity, no non-owner customer roles, no disposable calculation/email fixture (**DS**/**DC**) |
| **ACTUAL PRODUCT DEFECT** | **No evidence** | Every executed check passed: unauthenticated denial (401), invalid-credential rejection (400 `invalid_credentials`), client-path RLS denial (`42501`), CORS exact-origin allow-list, private-bucket denial (live-acceptance §6–§19, **DD**). **Nothing was TESTED AND FAILED.** |

**Distinction stated explicitly:** BLK-2 = `NO AUTHORIZED TEST IDENTITY` (+ `MISSING TEST DATA`), i.e.
**NOT TESTED** — **not** an authentication, role-resolution, routing, authorization, tenant-isolation, storage,
calculation/reporting or email **defect**. No defect is inferred from the absence of testing (brief §8).

---

## H. Recommended next action

**Exactly one:**

> **PO DECISION + authorisation: authorise a bounded, controlled FINAL-03 authenticated acceptance identity set,
> then schedule the authenticated acceptance run.**

Precise specification the PO must authorise (**do not implement now**):

* **Identity type(s):** 2 **existing** owner identities (reuse, no creation) **plus** 3 **new** minimal
  controlled identities — 1 internal **staff**, 1 **consultant**, 1 **Processing Entity** staff.
* **Minimum permissions:** staff → `can_review, can_process, can_view_all` only; consultant → active firm
  membership + `can_*` flags for tested actions + one active client grant; PE → `operator`/`reviewer` scope on
  one entity.
* **Required organisation/context:** all three new identities anchored to the **existing** organisations
  (no new tenant): consultant granted access to one existing org; PE entity assigned to one existing org's work.
* **One or multiple identities:** **multiple** — the copy above (5 total); cross-tenant and cross-actor
  criteria cannot be met with fewer.
* **Minimum data required:** the rows in §E.2 items 1–3 (no new organisation); items 5–6 (disposable
  calculation/email)
  are optional and must be separately authorised or deferred.
* **Who must authorise creation:** the **CarbonTally Product Owner**; credentials supplied **at runtime only**
  via the established mechanism (§F), never stored.

If the PO authorises only the **customer half** (no new identities), the customer/tenant/storage criteria
(C, routing → `/home`, D, G, E4) can proceed immediately with the two existing owners; the staff/consultant/PE
criteria will remain `REQUIRES ADDITIONAL AUTHORIZED IDENTITY`.

---

## I. Mutation statement

> **NO PRODUCTION IDENTITIES, DATA, DATABASE RECORDS, STORAGE OBJECTS, CREDENTIALS, AUTHENTICATION SETTINGS, OR APPLICATION CODE WERE CREATED OR MODIFIED.**

No user, organisation, membership, consultant, staff, PE, session, document, storage object, audit record or
billing record was created. No password was set, reset or changed; no role or membership was changed; no
migration, RLS policy, grant, schema or configuration was altered; no email was sent; nothing was deployed,
committed, pushed or restarted. The only production-data access was **read-only** (`SET
default_transaction_read_only = on`); the only network access was unauthenticated HTTP GET of public resources.
The only file written was this report.

---

### Exact evidence inspected

**Documents (DD):** `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md`,
`…/02-preservation-assessment-entities.txt`, `…/06-environment-identity-redacted.txt`,
`…/08-final-03-p2-p5-p6-rls-decision-package-20261002.md`,
`docs/audit/costrict/CSTR-FINAL03-LIVE-ACCEPTANCE-001-20261003.md`,
`docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md`,
`docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`,
`docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`,
`docs/cline/reports/CT-STEP2-P1-ROWCANDIDATE-VERIFY-025.md`,
`docs/architecture/CT-FINAL-02-20261001-LIVE-EVIDENCE-CLOSURE-PASS-REPORT.md`.

**Code (DC):** `backend/api/v3_context.py`, `backend/api/operations_auth.py`, `backend/api/consultant_auth.py`,
`backend/api/pe_auth.py`, `frontend/src/v3/components/RoleRoute.jsx`, `frontend/src/App.js`.

**Data store (DS, read-only):** `organizations`, `organization_members`, `auth.users`, `auth.identities`,
`consultant_profiles`, `consultant_firm_members`, `consultant_clients`, `processing_entities`, `staff_profiles`,
`staff_roles`, `roles`, `organization_files`, `evidence_line_items`, `manual_extraction_batches`,
`document_processing_queue`, `storage.objects`.

**Live public (LO):** `https://carbontally.co.uk`, `/login`, `/ops`, `/admin`, `/auth/callback`.

---

**READY FOR PO REVIEW — BLK-2 TEST IDENTITY READINESS INVESTIGATION COMPLETE — NO PRODUCTION MUTATION PERFORMED**
