# CT-MP-SUB-004-PD5-FIXTURE-01 — Implementation Report

**Manual Processing coverage QA fixture (deterministic + resettable)**

| | |
| --- | --- |
| **Task** | Implement the Demo Lab QA fixture authorized by **PD-5** so the positive Manual Processing coverage states become browser-verifiable |
| **Authority** | `docs/architecture/CT-MP-SUB-004-PO-decision-record.md` §7 **PD-5** (decision: **A**), §7.1 (explicit scope limit), §8 **PD-6** (migration/RLS gate) |
| **Repository** | `ct_93d5cdd` · branch `p8-release-reconciled` · HEAD `375a48dc1b9e9cfd74090bbf747554ae997acb59` |
| **Environment** | local Demo Lab only (lab Postgres + lab GoTrue gateway `127.0.0.1:54430`, release backend `127.0.0.1:8070`) |
| **Date** | 2026-10-04 |
| **Agent role** | Implementation (Cline) — **not** independent verification, **not** acceptance |
| **Final status** | **FIXTURE IMPLEMENTED, TESTED AND SELF-VERIFIED — READY FOR TARGETED INDEPENDENT VERIFICATION** (see §12) |

---

## 1. Authority and scope

PD-5 decided (**exact decision: A**): *create a deterministic, resettable Demo Lab
QA fixture that can produce the positive Manual Processing coverage states, so
the states the independent verification could not reach can be browser-verified.*

PD-5 §7.1 limits this strictly to **QA-fixture work only**. It does **NOT**
authorize:

> * any change to **application code** (frontend or backend);
> * any change to **product behaviour**, authorization, capability rules or workflow transitions;
> * any **schema**, **migration** or **RLS** change;
> * any change to the **investor demo database** (AGENTS.md §55);
> * any **production** access or modification;
> * any **deployment**.

This task is therefore bounded to **Demo Lab QA infrastructure**. It creates no
product rule, changes no application behaviour, and applies no migration.

PD-6 is respected: because no required table was missing in the lab, the fixture
applied nothing and triggered no migration-review gate (§5.5).

---

## 2. The verified gap this addresses (F-5 / NV-1…NV-4, NV-8)

From `docs/architecture/CT-MP-SUB-004-independent-verification-report.md`:

> **F-5 — Positive coverage states are NOT browser-verified (verification gap).**
> In the demo-lab environment the consultant firm reports `enabled:false`, `mode:null`,
> `capacity:null` and no plan carries `features.consultant_manual_processing`, so the
> following could not be exercised in a real browser: SELECTED_CLIENTS capacity meter and
> covered-clients list, the allocate/release flows, the ALL_ELIGIBLE_CLIENTS populated view,
> and the customer `available` / direct / sponsored / direct+sponsored states.
> *Impact:* D2 §10 acceptance criteria 3, 4, 5 (populated), 6, 8, 9 (available) and 10
> (presentational half) are verified only at unit/API level, not visually.

| Code | State that was unreachable | Addressed by this fixture |
| --- | --- | --- |
| NV-1 | SELECTED_CLIENTS capacity meter / covered-clients table / allocate / release | §6.2 checks 5, 6, 8 |
| NV-2 | ALL_ELIGIBLE_CLIENTS populated state | §6.2 checks 7, 9 |
| NV-3 | customer `available` / direct / sponsored / direct+sponsored | §6.2 checks 1, 2, 3 |
| NV-4 | Admin Commercial Coverage tab **after** loading a firm/organisation | §6.2 checks 8, 9, 10 |
| NV-8 | Consultant allocate/release **against the real database** | §6.2 check 6 |

**This task does not close F-5 / NV-1…NV-4 / NV-8.** It removes the *environmental*
blocker (AGENTS.md §55 forbade the verifier from seeding the lab). Only an
**independent re-verification** performed by QA/OHD can close them, and only the
Product Owner can accept CT-MP-SUB-004.

---

## 3. Deliverables

| File | Lines | Kind |
| --- | --- | --- |
| `tools/demo_lab/fixture_mp_coverage.py` | 952 | new (untracked) |
| `tools/demo_lab/fixture_mp_coverage_browser.py` | 330 | new (untracked) |
| `tools/demo_lab/README.md` | 228 | modified — new §8 documents the fixture (+65 lines) |
| `docs/architecture/CT-MP-SUB-004-PD5-FIXTURE-01-report.md` | — | this report |

No application code, migration, RLS policy or provisioned lab data was modified
(§10).

The fixture **extends the existing DEMO-T1 mechanism** (`tools/demo_lab/lab.py`,
`tools/demo_lab/provision.py`, the DEMO-T1 identity pattern) rather than
introducing a parallel seeding path, and reuses the existing Demo Lab evidence
directory.

---

## 4. Fixture design

### 4.1 Coverage is expressed with the **existing** model only

No new coverage, subscription, consultant or PE concept was invented. Each state
is produced by writing to tables that already exist in the release schema:

| Concern | Existing mechanism used |
| --- | --- |
| customer direct entitlement | `customer_subscriptions` → `billing_plans.features.manual_processing.enabled` |
| firm (consultant) coverage | the firm's **own** organisation subscription; `features.consultant_manual_processing` is read from `consultant_profiles.organization_id` |
| eligibility | the existing `consultant_clients` relationship |
| SELECTED_CLIENTS allocation | `consultant_mp_allocations` (migration `20261101000000_ct_mp_sub_003_consultant_coverage.sql`) |
| FIN-06 governance | `manual_processing_grants` (migration `20261030000000_manual_processing_routing.sql`) |
| operational "configured" state | `manual_processing_processors` (same migration) |

### 4.2 States produced

| # | State | Representation | Fixture identity |
| --- | --- | --- | --- |
| 1 | customer **direct** | plan `MP-FX-DIRECT` with `features.manual_processing.enabled` | `mp.owner.direct@demo-lab.carbontally.local` |
| 2 | customer **direct + sponsored** | direct plan **and** an active `consultant_mp_allocations` row under the SELECTED firm | `mp.owner.dual@demo-lab.carbontally.local` |
| 3 | customer **sponsored** | ALL_ELIGIBLE_CLIENTS coverage of the ALL firm | `mp.owner.sponsored@demo-lab.carbontally.local` |
| 4 | customer **negative** | provisioned customer, no subscription, no relationship | `owner.b@demo-lab.carbontally.local` |
| 5 | consultant **SELECTED_CLIENTS** | firm plan `MP-FX-FIRM-SELECTED`, capacity 3, one client pre-allocated | `mp.consultant.selected@demo-lab.carbontally.local` |
| 6 | consultant **ALL_ELIGIBLE_CLIENTS** | firm plan `MP-FX-FIRM-ALL`, populated eligible view | `mp.consultant.allel@demo-lab.carbontally.local` |
| 7 | **eligible-but-unallocated** (negative) | active `consultant_clients` row, no allocation → `not_allocated` | (no login required) |

Entities created: 6 organisations (2 firms + 4 clients), 2 `consultant_profiles`
firms, 2 `consultant_firm_members`, 3 `consultant_clients`, 4
`customer_subscriptions`, 3 `billing_plans`, 1 `consultant_mp_allocations`, 1
`manual_processing_grants`, 1 `manual_processing_processors`, 5 lab auth users.

### 4.3 Labelling (AGENTS.md §55 — isolated, labelled, tracked)

* organisation `metadata.fixture = "ct-mp-sub-004-pd5"`;
* organisation/company names prefixed `MP-FX`;
* `billing_plans.plan_code` prefixed `MP-FX-`;
* auth-user e-mail local-parts prefixed `mp.` in the lab domain.

Nothing is ambiguous about which rows belong to the fixture, so cleanup can be
exact (§8).


---

## 5. Fixture mechanism

### 5.1 CLI

```bash
python3 tools/demo_lab/fixture_mp_coverage.py            # apply (idempotent, converging)
python3 tools/demo_lab/fixture_mp_coverage.py --verify   # server-side verification (live API)
python3 tools/demo_lab/fixture_mp_coverage.py --reset    # remove ONLY the fixture rows + users
python3 tools/demo_lab/fixture_mp_coverage.py --json     # machine-readable output
python3 tools/demo_lab/fixture_mp_coverage_browser.py    # real headless-Chrome browser verification
```

`--json` is combinable with the other modes; every mode writes evidence (§9).

### 5.2 Determinism

Every fixture row is addressed by a deterministic UUID
(`lab.deterministic_uuid("mpfix:…")` / `fid(key)`) and written with
`INSERT … ON CONFLICT (id) DO UPDATE`. Re-running `apply` produces the **same ids
and the same row counts** — proven in §7.

Auth **user ids are the one exception**: `provision.ensure_user` lets GoTrue
assign the id on creation, so a full `--reset` followed by `apply` issues fresh
auth ids. The fixture mirrors whatever GoTrue returns into `auth.users` /
`public.users` and links memberships to it, and **no check depends on the
auth-id values** — proven in §8.4 (11/11 still pass after a full round-trip).

### 5.3 Convergence

`apply` runs `normalise_allocations()` after `apply_allocations()`: it deletes
*fixture-owned* allocation rows that the fixture does not declare. If a QA run
allocates a client through the UI, the next `apply` returns the firm to the
declared baseline instead of accumulating residue. (The model retains
`released`/inactive rows as history; `normalise_allocations` only prunes rows
belonging to this fixture's firms and ids.)

### 5.4 Idempotence

Memberships, subscriptions, client grants, firm membership, plans and grants are
all upserts, so repeating `apply` is a no-op in effect (§7).

### 5.5 Fail-closed preconditions (PD-6 gate)

`precondition()` is read-only and checks, before anything is written, that every
prerequisite table exists (`to_regclass`) and that the lab gateway answers
`/auth/v1/health`. If a table is missing it **stops and names the exact migration**
that would create it —

```
"manual_processing_grants":  "supabase/migrations/20261030000000_manual_processing_routing.sql"
"consultant_mp_allocations": "supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql"
```

— and applies nothing. The fixture never applies a migration and therefore cannot
silently cross the PD-6 migration-review gate.


### 5.6 Reset scoping

`--reset` deletes by fixture identity only:

| Target | Predicate |
| --- | --- |
| `consultant_mp_allocations` | `consultant_id IN <fixture firm ids>` |
| `manual_processing_processors` / `manual_processing_grants` | `scope_id IN <fixture org ids>` |
| `customer_subscriptions` | `organization_id IN <fixture org ids>` |
| `consultant_clients` | `consultant_id IN <fixture firm ids>` |
| `consultant_firm_members` / `consultant_profiles` | fixture firm ids |
| `organization_members` / `organizations` | fixture org ids |
| `billing_plans` | `plan_code IN ('MP-FX-DIRECT','MP-FX-FIRM-SELECTED','MP-FX-FIRM-ALL')` |
| lab auth users | e-mail ∈ fixture `mp.*` addresses (GoTrue delete + `auth.users`/`public.users` mirrors) |

It never touches provisioned DEMO-T1 identities, the investor demo dataset, other
lab data, production or Render. Note that negative state 4 uses the
**pre-existing** provisioned `org_b` / `owner.b` identity — the fixture only
*reads* it as the negative case; it neither creates nor deletes it.

Roughly 55 lines of the fixture are the declarative `PLANS` / `ORGS` / `ACTORS` /
`FIRMS` / `SUBSCRIPTIONS` data; the rest is orchestration.

---

## 6. Verification performed

Self-verification only (AGENTS.md §73: *implemented ≠ tested ≠ verified ≠
accepted*). Two independent surfaces were exercised: the **live HTTP API** and a
**real headless Chrome browser** using real password logins.

### 6.1 Server-side verification — 11/11 PASS

`python3 tools/demo_lab/fixture_mp_coverage.py --verify`
(evidence `mp_fixture_verify_20261004T165127Z.json`):

| # | Check | Observed |
| --- | --- | --- |
| 1 | `customer:org_client_direct` | `http=200 status=available sources=['direct'] direct=True sponsored=False operational=not_yet_configured` |
| 2 | `customer:org_client_dual` | `http=200 status=available sources=['direct','sponsored'] direct=True sponsored=True operational=configured` |
| 3 | `customer:org_client_sponsored` | `http=200 status=available sources=['sponsored'] direct=False sponsored=True operational=not_yet_configured` |
| 4 | `customer:org_client_dual:governance_active` | `governance={'enabled': True}` |
| 5 | `negative:org_b:not_included` | `http=200 status=not_included` |
| 6 | `consultant:firm_selected` | `enabled=True mode=SELECTED_CLIENTS capacity=3 allocated=1 available=2 eligible=2 covered=1 unallocated=1` |
| 7 | `consultant:firm_all` | `enabled=True mode=ALL_ELIGIBLE_CLIENTS capacity=None allocated=0 eligible=1 covered=0 unallocated=1` |
| 8 | `admin:firm_selected_coverage` | `enabled=True mode=SELECTED_CLIENTS allocated=1/3 available=2` |
| 9 | `admin:firm_all_coverage` | `mode=ALL_ELIGIBLE_CLIENTS capacity=None eligible=1` |
| 10 | `admin:client_dual_state` | `source=direct+sponsored gov=True configured=True` |
| 11 | `negative:org_client_unallocated:not_allocated` | `entitled=False sponsored_reason=not_allocated` |

Checks 5 and 11 are **negative** states (correctly not-entitled), so the fixture
also demonstrates that coverage is not being granted accidentally.

### 6.2 Browser verification — 10/10 PASS

`python3 tools/demo_lab/fixture_mp_coverage_browser.py` — real headless Chrome,
real password logins via `/login`, per-state screenshots
(evidence `mp_fixture_browser_20261004T154741Z.json`):

| # | Check (`browser:`) | Observed |
| --- | --- | --- |
| 1 | `customer_direct` | `AVAILABLE`, *Included in your subscription*, *Commercially entitled, not yet configured*; no `NOT INCLUDED` |
| 2 | `customer_dual` | `AVAILABLE`, *Your coverage includes:*, *Direct subscription*, *Consultant-sponsored coverage*, `EFFECTIVE ENTITLEMENT`, `GOVERNANCE STATUS`, *Active*, *Configured*, *Both commercial paths support one operational Manual Processing service*; no `NOT INCLUDED` |
| 3 | `customer_sponsored` | `AVAILABLE`, *Provided through your consultant*, *MP-FX Consultancy — All-Eligible Coverage*; no `NOT INCLUDED` |
| 4 | `customer_negative_org_b` | `NOT INCLUDED` rendered; no `AVAILABLE` badge |
| 5 | `consultant_selected` | capacity meter `aria-valuenow=1 / aria-valuemax=3`; **Add Client** control present |
| 6 | `consultant_selected_allocate_release` | Allocate → meter **2**, Release → meter **1** (real DB write path, NV-8) |
| 7 | `consultant_all_eligible` | eligible client rendered; **no** allocation control (correct for ALL_ELIGIBLE_CLIENTS) |
| 8 | `admin_coverage_selected` | meter `1/3`; *Purchased capacity* = **3 clients**; *Allocated* = **1 / 3**; covered client id listed |
| 9 | `admin_coverage_all_eligible` | *Automatically covered*; eligibility source *Active consultant-client relationship* |
| 10 | `admin_client_effective_state` | source rendered; governance shown; PE configured shown |

Screenshots: `<state dir>/evidence/browser/mp_fixture_*.png` (10 files, one per
state), e.g. `mp_fixture_customer_dual.png`,
`mp_fixture_consultant_selected_allocate_release.png`,
`mp_fixture_admin_coverage_selected.png`.

Assertions were written against the text the components actually render. Two
initial admin assertions were corrected after inspection: the Commercial
Coverage **covered-clients table renders organisation ids, not names**
(`ManualProcessingCoverageTab.jsx`), so the check asserts the fixture org id plus
the *Purchased capacity*/*Allocated* rows and the meter.


### 6.3 No collateral impact on provisioned Demo Lab data — 100% PASS

`python3 tools/demo_lab/verify.py` (the pre-existing base Demo Lab verification)
was run **after** the fixture and after a full reset→re-apply round-trip:

```
── actor contexts: 14/14 correct  (auth: password_grant)
── authorization / isolation probes: 30/30 as expected
── isolation rules enforced: 18/18
```

All DEMO-T1 identities still authenticate with correct contexts and routing, and
every isolation probe (org A↔B, consultant↔client, PE, staff administration)
still behaves as before. Evidence: `verify_20261004T165132Z.json`.

---

## 7. Determinism evidence

* **Repeat `apply`** — a second consecutive `apply` produced identical row counts
  and identical fixture ids, with no accumulation (compared from two apply
  JSON reports).
* **Repeat `apply` after out-of-band UI writes** — `apply` immediately after the
  browser allocate/release run still reported
  `"consultant_mp_allocations": 1` (the declared baseline), i.e. UI residue does
  not accumulate.

Declared baseline counts returned by every `apply`:

```json
{ "organizations": 6, "billing_plans": 3, "customer_subscriptions": 4,
  "consultant_profiles": 2, "consultant_firm_members": 2, "consultant_clients": 3,
  "consultant_mp_allocations": 1, "manual_processing_grants": 1,
  "manual_processing_processors": 1 }
```

---

## 8. Reset evidence (round-trip proof)

Full cycle: `apply` → `reset` → `apply`, with row counts captured at each step.
Evidence `mp_fixture_apply_20261004T165031Z.json`,
`mp_fixture_reset_20261004T165026Z.json`.

### 8.1 What `reset` removed (exit 0, `failures: []`)

```json
{ "consultant_mp_allocations": 2, "manual_processing_processors": 1,
  "manual_processing_grants": 1, "customer_subscriptions": 4,
  "consultant_clients": 3, "consultant_firm_members": 2,
  "organization_members": 3, "consultant_profiles": 2, "organizations": 6,
  "billing_plans": 3, "gotrue_removed": 5, "mirror_rows_removed": 5 }
```

### 8.2 Counts before → after reset → after re-apply

| Measure | Before | After reset | After re-apply |
| --- | --- | --- | --- |
| `organizations` (total) | 11 | 5 | 11 |
| `organizations` (**non-fixture**) | **5** | **5** | **5** |
| `organizations` (fixture) | 6 | 0 | 6 |
| `auth.users` (total) | 19 | 14 | 19 |
| `auth.users` (fixture `mp.*`) | 5 | 0 | 5 |
| `public.users` (total) | 20 | 15 | 20 |
| `billing_plans` (total / fixture) | 23 / 3 | 20 / 0 | 23 / 3 |
| `customer_subscriptions` | 4 | 0 | 4 |
| `consultant_profiles` (total / fixture) | 3 / 2 | 1 / 0 | 3 / 2 |
| `consultant_clients` (total / fixture) | 5 / 3 | 2 / 0 | 5 / 3 |
| `consultant_mp_allocations` | 2 | 0 | 1 |
| `manual_processing_grants` | 1 | 0 | 1 |
| `manual_processing_processors` | 1 | 0 | 1 |

**Non-fixture rows are unchanged (5 → 5 → 5)** and every delta equals exactly the
fixture's own rows — i.e. `reset` removed only fixture data.

### 8.3 Determinism across the round-trip

All fixture **data-row** ids after the reset+re-apply are identical to the ids
from the earlier apply, including organisations, firms, client grants and the
allocation:

```
org_firm_selected        bf6f05c4-62c7-5910-8ffb-19e1575c4139
org_firm_all             caf31aaa-5192-5b34-a773-1a58c65a5d7c
org_client_direct        2412c8d3-f267-5f5c-968f-02d6dc27a7d4
org_client_dual          aa6cde4e-e2ab-54c2-a3a8-fd2094046d59
org_client_sponsored     c0d22fe2-51fc-5854-aea6-2ec91daa4656
org_client_unallocated   97d4b3c7-58ba-5ff4-8732-cad9c3eeddb5
firm_selected            1ee24d1d-3883-518a-9c82-ba6bd4d1911f
firm_all                 caab859a-5ff7-5942-8528-939940d5f3a7
alloc firm_selected:org_client_dual  bdad5ffd-8171-5cd0-b0fa-dcab4d4ce116
```

(Auth user ids differ, as expected and documented in §5.2.)

### 8.4 Verification still passes after the round-trip

`--verify` run after the round-trip: **11/11 as expected** (evidence
`mp_fixture_verify_20261004T165127Z.json`) — i.e. regenerated auth ids do not
affect any coverage state.


---

## 9. Evidence and artefacts

Evidence is written **outside the repository**, under the Demo Lab state
directory (`/home/shomonrobie/ct_local_env/demo_lab/evidence/`), consistent with
the existing Demo Lab convention:

| File | Content |
| --- | --- |
| `mp_fixture_apply_<ts>.json` (+ `_latest`) | precondition result, counts, ids, logins, failures |
| `mp_fixture_verify_<ts>.json` (+ `_latest`) | the 11 server-side checks |
| `mp_fixture_browser_<ts>.json` (+ `_latest`) | the 10 browser checks + detail |
| `mp_fixture_reset_<ts>.json` (+ `_latest`) | per-table removal counts |
| `evidence/browser/mp_fixture_*.png` | 10 per-state screenshots |

No secret is written to evidence: the apply report contains **fixture logins
(e-mail addresses only) and ids**, never passwords, tokens, JWTs or signed URLs.

---

## 10. Production safety and blast radius

| Requirement | How it is met |
| --- | --- |
| No application-code change | only `tools/demo_lab/*` (new files) + `tools/demo_lab/README.md` were touched; no `backend/**`, no `frontend/**` |
| No product-behaviour / authorization / capability change | none; the fixture writes data the release schema already models |
| No schema / migration / RLS change | none; `precondition()` is read-only and fails closed instead of migrating |
| No investor-demo mutation | the fixture never touches DEMO-T1 records (proven §8.2: non-fixture counts unchanged) nor the investor demo dataset |
| No production access | all targets are `127.0.0.1` lab ports (`lab.GATEWAY_PORT`, `lab.BACKEND_PORT`); no Render/Supabase cloud endpoint is referenced |
| No deployment | none performed |
| No secrets committed | credentials come from the existing Demo Lab credential mechanism at runtime; nothing new is stored |
| Reversible | `--reset` restores the environment to the pre-fixture state (§8) |

### Git state

`git status` shows the two new untracked files plus the README modification made
by this task:

```
?? tools/demo_lab/fixture_mp_coverage.py
?? tools/demo_lab/fixture_mp_coverage_browser.py
 M tools/demo_lab/README.md
```

Everything else in the working tree (the many ` M ` / `?? ` entries) is
**pre-existing state from earlier CT-MP-SUB-003/004 work, not created by this
task**. In particular the `.gitignore` modification (`+.aider*`, plus line-ending
churn) was **not** made by this task, and no fixture/evidence path needed to be
added to `.gitignore` because evidence lives outside the repository.


---

## 11. Limitations and things this report does NOT claim

1. **F-5 / NV-1…NV-4 / NV-8 remain OPEN.** This work removes the environmental
   blocker; closure requires **independent** re-verification, and CT-MP-SUB-004
   acceptance remains a Product Owner decision. Status
   `VERIFIED WITH FINDINGS — NOT YET ACCEPTED` is unchanged by this report.
2. **Self-verified, not independently verified.** The fixture, its server-side
   checks and its browser checks were written by the same agent. Its *existence*
   and *behaviour* have not yet been audited by OHD/QA.
3. **Auth ids are not deterministic** after `--reset` (§5.2). Fixture *data-row*
   ids are.
4. **The browser run is timing-sensitive.** A cold Chrome context can delay the
   `/login` paint, so the browser script retries the real login. One earlier run
   produced a transient login timeout (8/9) that did not reproduce; the final run
   is 10/10.
5. **Not covered by this fixture** (unchanged from the verification report):
   NV-5 responsive viewports, NV-6 automated accessibility, NV-7 pixel-level D2
   comparison, NV-9 performance, NV-10 notification side-effects.
6. **Realtime console noise.** The lab gateway does not proxy Supabase Realtime,
   so the browser console logs `WebSocket … /realtime/v1/websocket` errors. These
   are environmental and unrelated to Manual Processing coverage.
7. **No test-framework tests added.** The fixture is a Demo Lab tool verified by
   its own live API/browser checks; no `backend/tests/**` or
   `frontend/src/v3/__tests__/**` file was added, because PD-5 authorizes
   QA-fixture work and the gap is a *browser-reachability* gap rather than a
   unit-coverage gap.
8. **Lab-only.** The fixture targets the local Demo Lab database/gateway by port.
   It is not intended for, and was not run against, any other environment.

**Nothing was committed or pushed.** No independent acceptance was performed.


---

## 12. Final status

> ## ✅ FIXTURE IMPLEMENTED, TESTED AND SELF-VERIFIED — READY FOR TARGETED INDEPENDENT VERIFICATION

| Dimension | Verdict |
| --- | --- |
| Implemented | **YES** — `fixture_mp_coverage.py` (952 lines), `fixture_mp_coverage_browser.py` (330 lines), README §8 |
| Tested | **YES** — `apply` / `--verify` / `--reset` / `--json` all executed successfully (exit 0, `failures: []`) |
| Self-verified (API) | **YES** — 11/11 checks as expected, including 2 negative states |
| Self-verified (browser) | **YES** — 10/10 checks, real headless Chrome + real password logins, per-state screenshots |
| No collateral impact | **YES** — base Demo Lab `verify.py` 14/14 contexts, 30/30 authorization probes, 18/18 isolation rules |
| Deterministic | **YES** — repeat `apply` yields identical ids and counts |
| Converging | **YES** — UI allocate/release converges back to the declared baseline on the next `apply` |
| Resettable | **YES** — `reset` removes exactly the fixture rows/users; non-fixture counts unchanged (5 → 5 → 5); environment fully restorable |
| Production-safe | **YES** — no app code, no schema/migration/RLS, no investor-demo change, no production access, no deployment, no secrets |
| Committed / pushed | **NO** — deliberately left in the working tree |
| Independent acceptance | **NOT PERFORMED** — out of scope for this task (AGENTS.md §58/§73) |

**Recommended next step (targeted independent verification).** Ask QA/OHD to,
independently of this implementation:

1. run `python3 tools/demo_lab/fixture_mp_coverage.py` then
   `python3 tools/demo_lab/fixture_mp_coverage_browser.py` in the Demo Lab, or
   inspect the existing evidence under
   `evidence/mp_fixture_{apply,browser,verify}_*.json` and
   `evidence/browser/mp_fixture_*.png`;
2. confirm the D2 §10 acceptance criteria **3, 4, 5 (populated), 6, 8, 9
   (available)** and the presentational half of **10** are now genuinely
   browser-reachable (NV-1…NV-4, NV-8);
3. confirm the reset scoping (§8) leaves the provisioned Demo Lab and investor
   demo data untouched;
4. then rule on **F-5 / NV-1…NV-4 / NV-8** and, if satisfied, escalate the
   CT-MP-SUB-004 acceptance decision to the Product Owner.

No action on F-3, F-2, F-4, F-7, F-9, F-10, F-11 or the PD-6
migration-application gate was taken or implied by this task.

