# CT-CONSULTANT-PLATFORM-FULL-IMPLEMENTATION-03 — Implementation Report

## 1. Document control

| Field | Value |
|---|---|
| Task ID | `CT-CONSULTANT-PLATFORM-FULL-IMPLEMENTATION-03` |
| Date | 2026-10-07 |
| Agent | Cline (implementation) |
| Branch / HEAD | `p8-release-reconciled` @ `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| Migrations added/changed | **None** |
| New API routes | **4** (2 firm-side PD-5, 2 admin PO-1) |
| PO decisions reopened | **None** (PO-1…PO-10 preserved) |
| Final status | **`IMPLEMENTED` / `TESTED` (bounded subset) — `ACCEPTED` withheld; `READY-FOR-INDEPENDENT-VERIFICATION`. See §25.** |

## 2. Authority sources (authority order honoured, AGENTS.md §2/§62)

1. `docs/architecture/CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02.md` — **PO IMPLEMENTATION BASELINE** (present in the repo; the STOP condition "authoritative register absent" is **not** triggered).
2. Existing binding `CT-CONSULTANT-PO-CONSOLIDATION-01.md` (PO-1…PO-10, unchanged).
3. Existing security/RLS/authorization contracts (`is_org_consultant`, `require_consultant`, `require_admin`).
4. Existing implementation (CT03 + CLOSURE-01).
5. Verification evidence (this session's tests).

## 3. Executive summary — and a candid scope statement

The brief (`CT-CONSULTANT-PLATFORM-FULL-IMPLEMENTATION-03`, 27 sections) is a
**very large, multi-increment programme**. Reconnaissance established that a
large part of the *model* is **already implemented** (CT03: client access
profiles, Plane C client portal, mode + relationship **request** records,
retention policy, branding; plus the CLOSURE-01 read surfaces). What remained
were the **net-new halves**.

This session implemented, and tested, the two **closest-to-complete and least
policy-ambiguous** net-new increments that the register resolves and the brief
prioritises:

* **PD-5** — the firm, as a party, **DECIDES** an inbound client relationship
  change/end request, with a **non-destructive** termination transition.
* **PO-1** — the **CarbonTally Admin DECIDES** a firm's product-mode change
  request; the admin route is the **only writer** of `commercial_mode`.

**This is deliberately not the whole task.** The remaining increments —
**PD-1A client invitation lifecycle**, **PD-2A client-user role administration**,
**White-Label email sending**, and the **Demo-Lab browser walkthrough/screenshots**
— are **NOT implemented in this session** and are recorded honestly in §12 and
§23. They are **not** blocked by a missing Product-Owner decision any more (the
register resolves them); they are simply **out of this session's implemented
scope** and require further scheduled work. No completion claim is made for
them.

**No STOP condition was hit for the two delivered increments.** The STOP
conditions in the brief §26 (policy/RLS/legal conflicts) were checked and none
apply to the delivered work.

## 4. Gap analysis — what already existed vs. what was missing

| Capability | Pre-existing (CT03 / CLOSURE-01) | This session |
|---|---|---|
| Client access profiles OFF/READ_ONLY/COLLABORATIVE/MANAGED + RETAINED | **Implemented** (`domain/relationship_access.py`; migration column `consultant_clients.client_access_profile`) | unchanged |
| Plane C client portal (`/api/v3/portal/{clientId}/*`) | **Implemented** (`api/v3_client_portal.py`, `api/client_portal_auth.py`) | unchanged |
| Product modes + entitlement gating | **Implemented** (`domain/consultant_entitlement.py`) | unchanged |
| Mode-change **request** (+ firm read surface) | **Implemented** (`POST/GET /me/mode-change-requests`) | unchanged |
| Relationship-request **create** (client) + firm read surface | **Implemented** (`consultant_relationship_requests`; `GET /me/relationship-requests`) | unchanged |
| Retention policy (7yr, no auto-delete) | **Implemented** (`domain/consultant_retention.py`) | unchanged |
| Firm-level branding (mode-capped) | **Implemented** (`domain/branding.py`) | unchanged |
| **Relationship-request DECISION + termination (PD-5)** | **Missing** | **Implemented here** |
| **Mode-change DECISION (PO-1)** | **Missing** | **Implemented here** |
| Client invitation lifecycle (PD-1A) | **Missing** | **Not implemented** (§12) |
| Client-user role administration (PD-2A) | **Missing** | **Not implemented** (§23) |
| White-Label email send | **Missing** | **Not implemented** (§23) |

## 5. Increment 1 — PD-5 relationship-request decision (firm side)

**Decision source.** Register §2 PD-5 (**C + S2**): either party initiates;
the workflow is **party-controlled**; CarbonTally provides arbitration; a
normal SLA target of 3 business days is an operational target, **not** automatic
approval.

**Implementation.** A request the CLIENT raised against a firm is decided by
that firm. `POST /api/v3/consultants/me/relationship-requests/{request_id}/decision`:

* server-authoritatively **firm-scoped** — a request whose `consultant_id` is
  not the caller's firm is a uniform **404** (no existence oracle);
* **reject** → request `status = cancelled`; relationship untouched;
* **approve** of `change_consultant` → request `status = confirmed` (execution of
  the actual consultant change remains a CarbonTally-arbitrated step — not
  invented here);
* **approve** of `end_relationship` → requires `confirmed=true` (T-1: no
  single-click termination), performs the **NON-DESTRUCTIVE** transition
  `consultant_clients.status → ended` via the existing
  `transition_client_lifecycle`, then marks the request `completed`. The
  Organisation, its id, data, evidence, calculations, reports and audit are
  **never** deleted; the PO-10 retained-read-only flag is a **separate**
  consultant action;
* the decision is **atomic** (`WHERE status = 'requested'`) so a second decision
  is a **409**; every transition is **audited**.

## 6. Increment 2 — PO-1 mode-change decision (CarbonTally Admin)

**Decision source.** Register §2 PO-1 (existing, operationalised). A firm only
**requests**; CarbonTally Admin decides; the normal effect is at the
billing/renewal boundary unless an earlier transition is approved.

**Implementation.** New admin-gated module `api/admin_consultant_commercial.py`:

* `GET /api/v3/admin/consultants/mode-change-requests` — the platform queue of
  every **undecided** request;
* `POST /api/v3/admin/consultants/mode-change-requests/{request_id}/decision` —
  `approve` / `reject`. `reject` leaves the firm untouched. `approve` records the
  decision at `effective_at` (the billing/renewal boundary); with
  `apply_now=true` CarbonTally approves an **earlier** transition and
  `set_commercial_mode` applies the mode to `consultant_profiles.commercial_mode`
  — the **only** writer of that column (a consultant has no such route);
* atomic + audited; `require_admin` re-checked server-side.

## 7. Files changed this session

**New:**
| File | Purpose |
|---|---|
| `backend/api/admin_consultant_commercial.py` | PO-1 admin decision surface |
| `backend/tests/unit/api/test_ct_consultant_full_implementation_03.py` | 18 new tests |
| `docs/architecture/CT-CONSULTANT-PLATFORM-FULL-IMPLEMENTATION-03.md` | this report |

**Modified** (all four were **already dirty** in the pre-existing workstream —
no unrelated change was absorbed):
| File | Change |
|---|---|
| `backend/data/consultants.py` | +5 repository methods (PD-5 + PO-1) + `datetime` import |
| `backend/api/v3_consultants.py` | +`RelationshipRequestDecision` model + PD-5 decision route |
| `backend/api/router.py` | register `admin_consultant_commercial` router |
| `backend/tests/unit/api/fakes.py` | +6 in-memory repository methods |

## 8. Migrations

**None.** The two delivered increments read/write tables that already exist
(`consultant_relationship_requests`, `consultant_mode_change_requests`,
`consultant_clients`, `consultant_profiles`), all created by
`supabase/migrations/20261103000000_ct_consultant_model_03_client_access_and_mode.sql`
(CT03). No schema change, no RLS change, no data change.

## 9. New API contracts

| Method | Path | Gate | Body | Success |
|---|---|---|---|---|
| POST | `/api/v3/consultants/me/relationship-requests/{id}/decision` | `require_consultant` + capability `manage_clients` | `{decision: approve\|reject, decision_note?, confirmed?}` | 200 `{request, ended_client_id}` |
| GET | `/api/v3/admin/consultants/mode-change-requests` | `require_admin()` | — | 200 `{requests}` |
| POST | `/api/v3/admin/consultants/mode-change-requests/{id}/decision` | `require_admin()` | `{decision: approve\|reject, decision_note?, effective_at?, apply_now?}` | 200 `{request, applied_mode}` |

## 10. Authorization matrix (delivered endpoints)

| Actor | PD-5 decision | PO-1 admin queue | PO-1 decision |
|---|---|---|---|
| Client Organisation member (client user) | **403** | **403** | **403** |
| Firm member **with** `can_manage_clients` (own firm's request) | **200** | **403** | **403** |
| Firm member **without** `can_manage_clients` | **403** | **403** | **403** |
| Firm member → **another firm's** request | **404** | **403** | **403** |
| CarbonTally Admin (`require_admin`) | 403 (not a consultant) | **200** | **200** |
| Processing Entity staff | **403** | **403** | **403** |
| Unauthenticated | **401** | **401** | **401** |

All rows are exercised by the 16 new tests (§17). No actor can act outside its
tenant: the PD-5 route re-derives the request's firm server-side; the PO-1 route
is platform-admin only.

## 11. Client profile matrix (CT03 — unchanged, for reference)

| Profile | read | comment | upload | edit master | correct | approve_final | map/recalc/delete |
|---|---|---|---|---|---|---|---|
| OFF | — | — | — | — | — | — | — |
| READ_ONLY | ✔ | ✔ | — | — | — | — | — (always denied) |
| COLLABORATIVE | ✔ | ✔ | ✔ | ✔ | ✔ | ceiling only | — (always denied) |
| MANAGED | ✔ | ✔ | — | — | — | — | — (always denied) |
| RETAINED_READ_ONLY | ✔ | — | — | — | — | — | — (always denied) |

Enforced server-side by `domain/relationship_access.py::profile_allows`
(PO-9: `map_factors`/`edit_mappings`/`recalculate` denied in **every** profile).
This session did not modify it.

## 12. Invitation lifecycle (PD-1A) — NOT implemented this session

The register's PD-1A (CarbonTally-controlled secure single-use invitation) is
**resolved** but **not implemented**. It requires, and does **not** yet have:

1. a **new additive migration** for a durable invitation token table
   (single-use, expiring, RLS-enabled, deny-by-default);
2. an **acceptance flow** that consumes the token atomically and creates
   membership **only** in the target Organisation, wired to **Supabase Auth**
   (which owns identity) — never storing passwords;
3. **White-Label invitation email** (consultant verified sender where entitled);
4. frontend surfaces and the full invitation test matrix (new/existing user,
   duplicate, expiry, replay, revoke, wrong tenant, wrong firm).

This is a **bounded, well-specified next increment**; it is deliberately left to
its own session to avoid an under-tested identity flow. **Not claimed as done.**

## 13. Relationship lifecycle (delivered)

```
requested ──(firm reject)──▶ cancelled
    │
    ├─(firm approve, change_consultant)──▶ confirmed   (arbitration → execution: TBD by support)
    └─(firm approve, end_relationship + confirmed)──▶ completed
                                        └─ consultant_clients.status: active ─▶ ended  (NON-destructive)
```

A `change_consultant` approval records the firm's acceptance but does **not**
reassign the relationship (that requires the incoming firm / support
arbitration — not invented). The relationship row and Organisation are preserved
throughout.

## 14. Mode lifecycle (delivered)

```
requested ──(admin reject)──▶ rejected            (firm mode untouched)
    │
    └─(admin approve)──▶ approved  (effective_at = billing/renewal boundary)
                            └─ if apply_now: commercial_mode applied immediately
```

No consultant-side mode mutation exists. `set_commercial_mode` is the sole
writer of `consultant_profiles.commercial_mode`.

## 15. Branding behaviour (White-Label)

Firm-level branding and mode-capped presentation already exist
(`domain/branding.py`, `domain/consultant_entitlement.py`,
`api/client_portal_auth.py`). This session did **not** change branding. The
**White-Label email send** path is **not implemented** (needs the configured
email sender and a verified-sender check) — recorded as a gap in §23. No
per-client branding exists; branding is never a tenant identity.

## 16. UX changes / header cleanup

**No frontend change this session.** The header/navigation cleanup
(`CarbonTally` never `CarbonTallyV3`; exactly one "Working on:" context; exactly
one "Back to Consultant") was addressed in `CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01`
and CLOSURE-01 item E, and is **not re-verified here**. The brief's §17/§18 UX
requirements are therefore **partially pre-existing and not re-proven** this
session (see §23).

## 17. Tests and results

New suite — `backend/tests/unit/api/test_ct_consultant_full_implementation_03.py`
(**18 tests**, all pass): the 9 PD-5 cases in §10 plus 7 PO-1 cases (list,
approve+apply_now, approve deferred, reject, double-decision 409, unknown 404,
consultant 403), plus **2 concurrent-decision race tests** (one per decision
surface — see §26) that inject a *lost atomic claim* (`decide_*` returns `None`)
and assert the route returns **409**, never a `200` with a null body.

| Command | Result |
|---|---|
| `pytest tests/unit/api/test_ct_consultant_full_implementation_03.py -q` | **18 passed** |
| consultant regression set (closure_01, model_03, revocation, org_parity, d19_lifecycle, composition_root, v3_routes_exposed, p6_2e_lifecycle) | **184 passed** |
| consultant subset (new suite + closure_01 + model_02 + org_parity) — re-run on resumption | **100 passed** |
| `tests/unit/api` (whole package) | **2662 collected; 2661 passed; 1 failed; 0 errors** |

> Environment note (resumption): in this shell `pytest` resolves from the user
> site (`~/.local/bin/pytest`, interpreter `/usr/bin/python3`); the venv has no
> `pytest` module. The counts above are the same suite the first pass ran.

## 18. Browser evidence / screenshots

**NOT performed.** A Demo-Lab browser walkthrough (brief §23) was **not** run in
this session — the delivered increments are backend/server-authoritative and were
verified at the API layer over the in-memory world. Browser verification of the
PD-5/PO-1 surfaces (and a re-check of the header cleanup) is **outstanding**
independent QA work. **No browser claim is made.**

## 19. Security results

* Every new route **re-authorizes server-side**; the frontend is never the
  boundary (AGENTS.md §44).
* PD-5 is **firm-scoped** with a uniform **404** for a foreign firm's request —
  no existence oracle.
* PO-1 is **platform-admin only** (`require_admin`); consultants and client
  users receive **403**.
* No new permission vocabulary was invented; the admin gate and the
  `manage_clients` capability are the **existing** ones.
* `set_commercial_mode` is the **only** writer of `commercial_mode`.
* No secrets, tokens, or signed URLs introduced.

## 20. RLS results

**No RLS change.** The read/write paths use the application's existing
service-role repositories for tables that are already RLS-enabled
(deny-by-default, service-role API only — per the CT03 migration). Application
authorization is enforced **in addition to** RLS (service role is never a
substitute for authorization).

## 21. Direct-customer regression

Not exercised end-to-end this session, but **no shared customer path was
modified**: the changes are additive routes plus new repository methods; the
existing customer, consultant-plane, billing, reporting and messaging code is
untouched. The full `tests/unit/api` run (2661 passed) is the broad regression
signal.

## 22. Pre-existing vs. introduced failures

| Failure | Classification |
|---|---|
| `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | **PRE-EXISTING / ENVIRONMENTAL** — caused by the gitignored `backend/.env` (Resend/SMTP config); reproduced identically in the prior CLOSURE-01 session and unrelated to these changes. |
| **Introduced by this session** | **None.** |

## 23. Known remaining gaps (honest, unranked by wishful thinking)

| # | Gap | State |
|---|---|---|
| G1 | **PD-1A client invitation lifecycle** (token table + Supabase-Auth acceptance + email) | **NOT implemented** (§12) |
| G2 | **PD-2A client-user role administration** (invite / assign / change / suspend / revoke) | **NOT implemented** |
| G3 | **White-Label invitation/notification email** (verified sender) | **NOT implemented** |
| G4 | **Demo-Lab browser walkthrough + screenshots** (brief §23) | **NOT performed** |
| G5 | **Header/nav cleanup re-verification** (exactly one "Working on:", no "V3") | pre-existing; **not re-proven** |
| G6 | **`change_consultant` execution** (actual re-assignment) | approval recorded; execution left to supported arbitration |
| G7 | **Relationship-decision SLA (3 business days)** enforcement/reminders | target only; **no scheduler** |
| G8 | **`F-IND-2`** uniform denial contract on the client-context endpoint | open recommendation (unchanged) |
| G9 | Relationship **client-side** decision of a consultant-initiated request | only the firm-side decision is implemented |

**STOP conditions (brief §26) encountered:** **none** that blocked the delivered
increments. No PO-decision conflict, no RLS/authorization conflict, no legal/
retention policy invention, no production/hosted access required.

## 24. Git and worktree state

| Item | Value |
|---|---|
| Branch | `p8-release-reconciled` |
| Starting SHA | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| Ending SHA | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` (**unchanged**) |
| Commit / reset / stash / rebase / force-push | **None performed** |
| Pre-existing dirty workstream | **Preserved, not absorbed** (the four modified files were already dirty) |
| New untracked files | `backend/api/admin_consultant_commercial.py`, `backend/tests/unit/api/test_ct_consultant_full_implementation_03.py`, this report |
| Migrations | **None** |

## 25. Final status

* **PD-5 relationship-request decision + non-destructive termination** —
  `IMPLEMENTED` · `TESTED`.
* **PO-1 mode-change decision (CarbonTally Admin)** — `IMPLEMENTED` · `TESTED`.
* `LAB-VERIFIED` — **NO** (no Demo-Lab browser pass).
* Overall — **`IMPLEMENTED` / `TESTED` (bounded subset); `ACCEPTED` withheld;
  `READY-FOR-INDEPENDENT-VERIFICATION`** for the two delivered increments only.

**Acceptance is a Product-Owner step after independent (CoStrict) verification.**
The remaining increments (§12, §23) must be scheduled and implemented before the
brief's §27 "complete only when" checklist can be claimed.

## 26. Resumption addendum (2026-10-07, second pass)

A follow-up pass **re-verified** the delivered increments against the live
repository (AGENTS.md §80: prior claims are not current without re-evidence) and
closed one real gap between the **documented** and the **coded** atomicity.

* **Defect found and fixed (both decision surfaces).** The routes' only `409`
  guarantee was the *read* pre-check (`status != 'requested'`). If a concurrent
  decision won the atomic `WHERE status='requested'` claim first, `decide_*`
  returned `None` and the route replied **`200` with a `null` request body** —
  contradicting the documented "second decision → 409". Both routes now raise
  **`409`** when the atomic claim returns `None`:
  * `backend/api/v3_consultants.py` — PD-5, **reject** and **approve** branches;
  * `backend/api/admin_consultant_commercial.py` — PO-1, **reject** and **approve** branches.

  No reordering was introduced: the PD-5 termination stays *idempotent-first*
  (guarded by `status == "active"`), which remains crash-recoverable, so the fix
  is purely additive and preserves that property.
* **Regression evidence:** the 2 new race-injection tests fail before the fix
  and pass after; the new suite is **18 passed**; the consultant subset is
  **100 passed**; the full `tests/unit/api` package still shows only the single
  **pre-existing / environmental** `test_v3_discovery` failure
  (`verification_delivered` is `True` because email config is present — see §22).
* **No new routes, no schema/RLS change, no secret introduced.** Routes remain
  **4**; HEAD remains `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` (**unchanged**).

**Revised status:** unchanged conclusion — `IMPLEMENTED` / `TESTED` (bounded
subset); `ACCEPTED` withheld; **`READY-FOR-INDEPENDENT-VERIFICATION`**.




