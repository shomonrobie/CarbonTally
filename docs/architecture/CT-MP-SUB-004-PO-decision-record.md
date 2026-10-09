# CT-MP-SUB-004 — Product Owner Decision Record

| Field | Value |
| --- | --- |
| **Document ID** | `CT-MP-SUB-004-PODR-01` |
| **Task ID** | `CT-MP-SUB-004-PO-DECISIONS-01` |
| **Decision date** | **2026-10-04** |
| **Subject** | CT-MP-SUB-004 — Manual Processing coverage (customer / consultant / admin) |
| **Decision authority** | Product Owner, CarbonTally |
| **Recorded by** | Cline (implementation agent) — recording, not authoring |
| **Status** | **RATIFIED — PO DECISIONS RECORDED** (PD-1 … PD-6) |
| **Type** | Documentation only. No application code, schema, migration, RLS, database, credential, Demo Lab, or production change. No commit, no push, no deploy. |

---

## 1. Purpose and authority

This document is the **authoritative written record of the Product Owner's
decisions PD-1 … PD-6** for CT-MP-SUB-004, issued on **2026-10-04**.

The decisions were issued **explicitly by the Product Owner**. This record does
not create, extend, reinterpret or narrow them; it records them, together with
their rationale, their consequences, and their relationship to the independent
verification findings.

Where this record and any other document appear to conflict, **this record and
the PO decisions it contains are authoritative**, and the conflicting document
is to be treated as stale (AGENTS.md §2 source-of-truth hierarchy: ratified PO
decisions outrank historical audit reports).

### 1.1 Relationship to the historical independent verification report

The independent verification report

`docs/architecture/CT-MP-SUB-004-independent-verification-report.md`

is a **historical artefact**. It is **NOT amended, rewritten, or superseded in
its findings** by this record, and its verdict has **not** been altered.

* Baseline sha256 of that report at the time of this record:
  `128c47cfc94fafc9931a0fb38dd964e359e9becd53d3ae0a35109587870748f9`
* Its verdict as at 2026-10-04 stands as the historical record:
  **"VERIFIED WITH FINDINGS — NOT READY FOR PO ACCEPTANCE"** (verdict **B**).
* This record documents the PO decisions that were **outstanding** at the time
  of that verification (its §20 table). Several of those decisions are now made;
  one open verification gap (F-5) is unaffected by the decisions and remains a
  QA gap, not a PO decision.

### 1.2 Baseline of the authoritative specifications

Both authoritative specifications were **unchanged** at the time of this record
(hashes match those recorded by the independent verification, i.e. no silent
edit of the specification was made to accommodate the decisions):

| Document | sha256 |
| --- | --- |
| `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` (CT-PO-MP-SUB-003) | `d55644f00ad04014e286597770c57dfff7582bad3fb9523f8729e53e5b29ea5d` |
| `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` (CT-UX-MP-SUB-003) | `a27ad96428808cc44fe632da41dec77c171ed6909cdbbf7bf8e74d676079f3da` |

> **Note (governance, not a decision):** CT-UX-MP-SUB-003 still carries the
> on-face marker `**Status:** PROPOSED FOR PO APPROVAL`, and its §11 governance
> table still reads `UI implementation — NOT YET AUTHORIZED`. PD-1 resolves the
> authorization, so those markers are now **stale**. Updating them is *not* part
> of this task and is listed under "Remaining work" in the companion report.

---

## 2. Decision summary

| # | Decision | Topic | Options offered | **PO chose** | Primary finding relationship |
| --- | --- | --- | --- | --- | --- |
| **PD-1** | Approval of the UI/UX specification and retrospective authorization of the CT-MP-SUB-004 UI | A / B | **A** | **F-1** (HIGH) — governance / authorization gap |
| **PD-2** | Internal CarbonTally staff access to the **customer** Manual Processing route | A / B | **A** | **F-2** (LOW) — behaviour confirmed stricter than claimed |
| **PD-3** | Who may **read** consultant-firm Manual Processing coverage | A / B | **A** | **F-8** (INFO) — outside F-1…F-6; closes §20 PD-3 |
| **PD-4** | Admin operational tab label | A / B | **A** | **F-6** (MEDIUM / PARTIAL) |
| **PD-5** | Demo Lab QA fixture for positive coverage states | A / B | **A** | **F-5** (MEDIUM) — plus NV-1 … NV-4 |
| **PD-6** | Ratification of the CT-MP-SUB-003 migrations **for application** | A / B | **B** | Governance gate (§20 PD-6); no direct F-1…F-6 finding |

---

## 3. PD-1 — Approve CT-UX-MP-SUB-003 and retrospectively authorize the CT-MP-SUB-004 UI

### Option offered
**A** / B

### **Exact decision: A**

* **APPROVE `CT-UX-MP-SUB-003` as the authoritative UI/UX specification** for
  the Manual Processing commercial/entitlement surfaces.
* **Retrospectively authorize** the already-delivered **CT-MP-SUB-004 UI
  implementation** against that specification.

### Rationale
F-1 established that the delivered customer, consultant and admin UI had been
implemented against `CT-UX-MP-SUB-003` while that document declared itself
`PROPOSED FOR PO APPROVAL` and its own §11 governance table recorded
`UI implementation — NOT YET AUTHORIZED`; `CT-PO-MP-SUB-003` §27 authorized
implementation only through the backend task `CT-MP-SUB-003`. Acceptance
authority was therefore absent even though the implementation, security and
runtime behaviour independently verified as sound.

The Product Owner has now supplied that authority: the specification is approved
as the UI/UX authority for these surfaces, and the UI already built against it is
authorized as having been built against the approved design.

### Consequence
* The **acceptance gate** created by F-1 is **cleared**.
* `CT-UX-MP-SUB-003` becomes the **authoritative UI/UX specification**; any
  further UI change to these surfaces is measured against it.
* This is a **retrospective authorization**. It does **not**:
  * ratify any deviation from the specification (F-6, F-10, F-11 continue to be
    measured against the now-authoritative document);
  * convert the independent verification verdict into acceptance (F-3 and F-5
    remain open — see §9);
  * authorize any migration, deployment or production change (see PD-6).
* No code change is required to give effect to PD-1.

### Relationship to verification findings
* **F-1 (HIGH — governance / authorization gap)**: **directly resolved** by PD-1.
  This was the single most material finding and was the stated reason the
  verification verdict was not A.
* Related: §20 **PD-1** of the verification report ("This is the gate on
  acceptance") — now decided.

---

## 4. PD-2 — Internal staff do NOT receive the customer Manual Processing route

### Option offered
A / B

### **Exact decision: A**

* **Internal CarbonTally staff do NOT receive access to the customer Manual
  Processing route.**
* **Keep the current denied / `403` behaviour.**

### Rationale
The implementation report's §2.1 claim — that internal staff *"keep their
existing operational exemption inside that guard"* — was independently proven
**false** (F-2): `require_org_member()` demands `current_user.is_org_member`,
internal and Processing Entity staff are not organisation members, and the route
returns **403**. The behaviour was verified to be **stricter** than claimed and
therefore safe.

The Product Owner confirms the observed behaviour is the intended behaviour:
internal staff operate Manual Processing through the **Admin control plane**
(the admin coverage surface), not through the *customer* workspace. The two
surfaces are distinct and must not be conflated.

### Consequence
* The `403` on the customer route for internal staff is **confirmed as correct
  product behaviour** — it is a **security property, not a defect**.
* There is **no requirement to change the authorization guard**, and no
  requirement to grant internal staff an org-member-like exemption.
* The **implementation report §2.1 remains factually inaccurate**; the report is
  not amended by this record, but this decision removes any product ambiguity
  about the intended behaviour.

### Relationship to verification findings
* **F-2 (LOW — inaccurate claim)**: the *decision* now aligns with the verified
  behaviour; the *documentation inaccuracy* in the implementation report is noted,
  not fixed here.
* Related: §20 **PD-2** ("the customer-route denial may well be correct, but it
  should be confirmed") — now confirmed.

---

## 5. PD-3 — Coverage **read** for all active firm members; `manage_clients` governs allocate/release

### Option offered
A / B

### **Exact decision: A**

* **ALL ACTIVE CONSULTANT FIRM MEMBERS** may **READ** their firm's Manual
  Processing coverage.
* **`manage_clients` remains required** for **allocate / release** operations.

### Rationale
Independent verification recorded (F-8, INFO) that **any** active firm member
can read the firm's full coverage payload (`200`), while
`consultant_allocate_client` and the release path require the `can_manage_clients`
capability. The verifier assessed this as *"a defensible member-read /
capability-write split"* and consistent with specification §6 ("only their firm's
coverage"), but noted that the specification does **not** state the
read-capability rule explicitly and asked for PO confirmation.

The Product Owner confirms the split as ratified product policy: **visibility is
firm-wide; mutability is capability-gated.**

### Consequence
* The read path's authorization model is **ratified as-is** — no code change.
* `manage_clients` (equivalently `can_manage_clients`) is **confirmed as the
  necessary capability for allocate/release**, and shall not be relaxed for
  ordinary firm members.
* F-8 moves from "noted for PO confirmation" to **decided**.
* The **write** paths remain subject to their own verification gap (F-5 / NV-8),
  which PD-5 is intended to close.

### Relationship to verification findings
* **F-8 (INFO)** — this decision is the PO confirmation F-8 requested. F-8 sits
  **outside** the F-1…F-6 severity set and corresponds to the verification
  report's §20 **PD-3**.
* **F-5 (MEDIUM)** — PD-3 ratifies the *rule*; it does not close the *browser
  verification gap* for the read/allocate/release states. PD-5 addresses that gap.

---

## 6. PD-4 — Keep the Admin operational tab label "Manual Processing"

### Option offered
A / B

### **Exact decision: A**

* **KEEP** the existing Admin operational tab label **`Manual Processing`**.
* **Do NOT rename it to `Operational Routing`.**

### Rationale
F-6 observed that `CT-UX-MP-SUB-003` §2/§8 depict the tab set as
`[ Commercial Coverage ] [ Operational Routing ] [ Assignments ]`, whereas the
implementation labels the operational tab **`Manual Processing`** (the
pre-existing surface). The verification classified this as **PARTIAL, not a
defect**, because the specification's §8 explicitly permits placement to follow
*"the existing CarbonTally navigation architecture"*.

The Product Owner confirms the implementation label is correct: the tab keeps its
established CarbonTally name, and no relabelling is required.

### Consequence
* **No code change.** The Admin tab bar keeps `Commercial Coverage` +
  `Manual Processing`.
* F-6 is **closed as decided** (the specification's prose naming is superseded by
  this decision, not by a UI change).
* Any future re-reading of §2/§8 shall treat the implemented label as the
  ratified presentation.

### Relationship to verification findings
* **F-6 (MEDIUM / PARTIAL — spec deviation)**: **resolved by decision** in favour
  of the implemented label.
* Related: §20 **PD-4** — now decided.

---

## 7. PD-5 — Create a deterministic / resettable Demo Lab QA fixture for positive coverage states

### Option offered
A / B

### **Exact decision: A**

* **CREATE** a deterministic, resettable **Demo Lab QA fixture** that can produce
  the **positive Manual Processing coverage states**, so the states that the
  independent verification could not reach can be browser-verified.
* **The fixture itself is NOT part of this task.** PD-5 authorizes the work; it
  does not perform it.

### Rationale
F-5 recorded that in the Demo Lab environment no consultant firm reports
`enabled:true`, no plan carries `features.consultant_manual_processing`, and
`capacity` is `null`, so the following could **not** be exercised in a real
browser and were verified only at unit/API level:

* the SELECTED_CLIENTS **capacity meter** and covered-clients list;
* the **allocate** and **release** flows;
* the populated **ALL_ELIGIBLE_CLIENTS** view;
* the customer **available / direct / sponsored / direct+sponsored** states —
  i.e. `CT-UX-MP-SUB-003` §10 acceptance criteria **3, 4, 5 (populated), 6, 8,
  9 (available)** and the presentational half of **10** (NV-1 … NV-4, NV-8).

The verifier was correctly unable to seed this, because mutating the Demo Lab is
an unauthorized data mutation (AGENTS.md §55). The Product Owner therefore
authorizes a **purpose-built, deterministic and resettable QA fixture** as QA
infrastructure — not a product rule and not a change to the application.

### Consequence
* PD-5 authorizes **QA-fixture work only** (see §7.1 for the explicit limit).
* The fixture must be **deterministic** (same input → same states) and
  **resettable** (leaves no residue), consistent with AGENTS.md §55 (isolated,
  labelled, tracked, cleaned-up QA records).
* On completion, the outstanding verification gap F-5 / NV-1 … NV-4 / NV-8
  becomes **closable by re-verification**, which is the precondition for any
  statement of CT-MP-SUB-004 acceptance.
* **No product behaviour, migration, or authorization changes** are implied by
  PD-5.

### Relationship to verification findings
* **F-5 (MEDIUM — verification gap)**: PD-5 is the authorized remedy. F-5 remains
  **OPEN** until the fixture exists **and** the states are browser-verified.
* **NV-1, NV-2, NV-3, NV-4, NV-8** ("BLOCKED BY ENVIRONMENT"): remain open for the
  same reason.
* Related: §20 **PD-5** — now decided.

---

### 7.1 Explicit scope limit of PD-5

> ### ⚠ PD-5 authorizes **QA-fixture work ONLY**
>
> **PD-5 authorizes the creation of a deterministic, resettable Demo Lab QA
> fixture for positive Manual Processing coverage states, and nothing else.**
>
> **PD-5 does NOT authorize:**
>
> * any change to **application code** (frontend or backend);
> * any change to **product behaviour**, authorization, capability rules or
>   workflow transitions;
> * any **schema**, **migration** or **RLS** change;
> * any change to the **investor demo database** (AGENTS.md §55);
> * any **production** access or modification;
> * any **deployment**.
>
> The fixture is **QA infrastructure**. Its purpose is to make the
> already-implemented positive coverage states **reachable for browser
> verification**; it is not a mechanism for changing what the product does.
>
> PD-5 is **not implemented in this task**. This task records the decision only.

---

## 8. PD-6 — Migration ratification with a per-migration review gate

### Option offered
A / B

### **Exact decision: B**

* The **CT-MP-SUB-003 migrations are architecturally ratified *in principle***.
* **BUT each migration requires separate migration review** before being applied
  **to any environment where it is not already applied**.
* This decision **does NOT authorize production migration or deployment.**

The three migrations in scope:

| Migration | Purpose |
| --- | --- |
| `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | P17A — `consultant_profiles.organization_id` plus factor-governance / accounting-dimension changes |
| `20261030000000_manual_processing_routing.sql` | Manual Processing routing |
| `20261101000000_ct_mp_sub_003_consultant_coverage.sql` | `consultant_mp_allocations` (consultant coverage) |

### Rationale
The Demo Lab database already supports the coverage read and write paths, so the
migrations' **architectural intent** is ratified. However, applying a migration is
a **state-changing, potentially irreversible operation** with RLS, foreign-key and
data-migration consequences. Ratifying the *architecture* is therefore distinct
from authorizing the *application* of each migration (AGENTS.md §66 database
change policy; §67 RLS policy).

The Product Owner therefore takes the cautious option: **architectural
ratification, per-migration review gate.**

### Consequence
* Each migration must receive its **own migration review** (schema delta,
  foreign keys, indexes, RLS impact, rollback path, environment target) before it
  is applied anywhere it is not already applied.
* Nothing in PD-6 authorizes applying a migration to production, to the investor
  demo database, or to any other environment.
* Nothing in PD-6 authorizes a **deployment** of any kind.

> ### ⛔ PD-6 does **NOT** authorize production deployment
>
> **PD-6 is an architectural-ratification decision with a per-migration review
> gate. It explicitly does NOT authorize:**
>
> * applying any migration to **production**;
> * applying any migration to any environment **other than** where it is already
>   applied, until that individual migration has passed its own review;
> * any **deployment**, release, cutover, or production configuration change;
> * any **RLS** change;
> * any change to the investor demo database.
>
> Production migration/deployment remains **separately gate-operated** and
> requires its own explicit authorization.

### Relationship to verification findings
* There is **no direct F-1 … F-6 finding** for PD-6. It corresponds to the
  verification report's §20 **PD-6**, which recorded that *"migration-application
  approval remains a PO/ops gate for other environments"*.
* It shares the **governance/authorization** category of **F-1**, but is a
  separate gate: F-1 was about *UI implementation authority*; PD-6 is about
  *migration application authority*.

---

## 9. Current CT-MP-SUB-004 acceptance status

**Status at the date of this record: `VERIFIED WITH FINDINGS — NOT YET ACCEPTED`**

| Gate | Status before PD-1…PD-6 | Status after PD-1…PD-6 |
| --- | --- | --- |
| **F-1** — UI implemented without PO authorization (HIGH) | **OPEN** — blocked acceptance | **CLOSED by PD-1** |
| **PD-2** — internal staff on customer route (behaviour) | OPEN | **CLOSED by PD-2** (keep `403`) |
| **PD-3** — firm-member coverage read capability (F-8) | OPEN | **CLOSED by PD-3** (read firm-wide; write gated by `manage_clients`) |
| **PD-4** — admin tab label (F-6) | OPEN | **CLOSED by PD-4** (keep `Manual Processing`) |
| **F-5 / NV-1…NV-4, NV-8** — positive coverage states not browser-verified (MEDIUM) | **OPEN** | **STILL OPEN** — remediation authorized by PD-5, not yet performed |
| **F-3** — `ConsultantPage.jsx` scope attribution not verifiable (MEDIUM) | OPEN | **STILL OPEN** — not covered by any PD |
| **F-2, F-4** — inaccurate claims in the implementation report (LOW) | OPEN | **STILL OPEN** — documentation inaccuracy; not covered by any PD |
| **F-7, F-9, F-10, F-11** — robustness / INFO notes | OPEN | **STILL OPEN** — not covered by any PD |
| **PD-6** — migrations ratified; per-migration review gate | OPEN | **DECIDED** (architecture ratified; application still gated) |
| **PD-7** — final public pricing / payment provider | OPEN | **STILL OPEN** (carried forward from D1 §29; not part of PD-1…PD-6) |

**Determination:**

* **PD-1 removes the acceptance blocker** identified by F-1. The delivered UI is
  now authorized against an approved UI/UX specification.
* CT-MP-SUB-004 is therefore **no longer blocked on a governance/authorization
  decision**.
* CT-MP-SUB-004 is **NOT yet accepted**, because the independent verification's
  **F-5 verification gap remains open**: the positive coverage, capacity,
  allocation and sponsored/direct customer states have not been browser-verified.
  PD-5 authorizes the QA fixture that makes re-verification possible.
* Acceptance therefore remains a **verification** step, not a **decision** step.
  No agent may declare CT-MP-SUB-004 accepted until F-5 (and the related NV items)
  are closed with current browser evidence, and the residual F-3 documentation
  gap is addressed or explicitly waived by the Product Owner.
* The historical independent verification verdict
  (**"VERIFIED WITH FINDINGS — NOT READY FOR PO ACCEPTANCE", B**) is **not
  rewritten** by this record.

---

## 10. Record control

| Item | Value |
| --- | --- |
| Repository HEAD at time of record | `375a48dc1b9e9cfd74090bbf747554ae997acb59` |
| Branch | `p8-release-reconciled` |
| Files created by this task | `docs/architecture/CT-MP-SUB-004-PO-decision-record.md`, `docs/architecture/CT-MP-SUB-004-PO-DECISIONS-01-report.md` |
| Files modified by this task | **NONE** (the independent verification report and both authoritative specifications are unmodified) |
| Application code changes | **NONE** |
| Database / schema / migration / RLS changes | **NONE** |
| Credential / Demo Lab changes | **NONE** |
| Production access | **NONE** |
| Commit / push / deploy | **NONE** |

### 10.1 Decisions NOT taken (explicitly out of scope of PD-1…PD-6)

* PD-7 (final public pricing, payment provider) remains **OPEN**.
* No decision was taken to change the authorization guard for internal staff
  (PD-2 keeps the current `403`).
* No decision was taken to apply any migration (PD-6 gates each one separately).
* No decision was taken to alter the capability model beyond confirming the
  existing read/write split (PD-3).
* No decision was taken on F-3 (scope attribution), F-4 (root-cause wording) or
  F-2 (implementation-report wording).

---

## 11. Sign-off

| Role | Statement |
| --- | --- |
| **Product Owner** (decision authority) | PD-1 … PD-6 issued 2026-10-04 as recorded above. |
| **Recorder** (Cline, implementation agent) | Decisions recorded faithfully; no code, schema, data, credential or production change made; no commit, push or deploy performed. |

*Companion report:* `docs/architecture/CT-MP-SUB-004-PO-DECISIONS-01-report.md`
