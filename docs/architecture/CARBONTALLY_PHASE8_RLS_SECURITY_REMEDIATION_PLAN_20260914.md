# CarbonTally — Phase 8 · Separate Workstream RLS
## RLS SECURITY REMEDIATION PLAN — `…039`

**Amendment 1 — PO RULINGS (Option B, 2026-09-14): `D-1`, `D-2`, `D-11`, `D-13` APPROVED and recorded; `D-4`…`D-10`, `D-12` remain explicit gates.**

| Decision | Ruling | Effect here |
|---|---|---|
| **D-1** | **APPROVED** — authorise anonymous-grant containment (`RLS-4A-1`) as an independent least-privilege hardening step; it does **not** by itself change the intended product access model | **EXECUTED + VERIFIED** (§A) |
| **D-2** | **APPROVED** — accept the register's recorded status regarding the 12 missing production tables; **no** production remediation; treat the condition exactly within the existing RLS plan | **RECORDED ONLY** — no production action; the 5 QA policy-less tables stay as recorded gaps |
| **D-11** | **APPROVED** — re-affirm `FORCE ROW LEVEL SECURITY` **remains DEFERRED**; do not enable it in this remediation | **CONFIRMED** — census shows `force_rls = 0` after the step |
| **D-13** | **APPROVED** — resolve the sequence discrepancy per the register so the F-5/F-6 hardening is not silently omitted or reordered | **RESOLVED** (§B) |
| **D-4…D-10, D-12** | **NOT authorised yet** — preserved as explicit decision gates; return to the PO when each step is reached | **UNCHANGED** |

### A. `RLS-4A-1` — anonymous-grant containment — EXECUTED (QA / non-production only)

Migration: `supabase/migrations/20260920000000_p8_rls_anon_grant_containment.sql` — **`REVOKE`-only** (the register's authorised operation type): no `ENABLE`, **no policy change**, no grant to any other role, no data touched.

| Metric | Before | **After** | Note |
|---|---|---|---|
| `anon` grants in `public` | **458** | **4** | the 4 are all on **`emission_factors`** |
| `anon` grants on org-scoped tables | **182** | **0** | tenant surface fully contained |
| `anon` privilege on all other `public` tables | present | **none** | proven by `has_table_privilege('anon', …) = false` |
| `anon`-admitted policies | 0 | **0** | no policy change was made |
| `authenticated` grants | 810 | **810** | **parity** |
| policies total | 197 | **197** | **parity** |
| tables RLS-enabled | 133 | **133** | **parity** |
| `FORCE RLS` | 0 | **0** | **D-11 honoured** |

* Idempotency: applying the migration a second time returns `rc=0` with zero tables left to revoke.
* **`emission_factors` was deliberately NOT touched** — public/anonymous access to it is the **unratified** decision **D-4**; revoking it would silently answer a product question. Its 4 grants are unchanged and carried to the D-4 gate.
* **False-positive cleared:** `information_schema.role_table_grants` reported `messages` as `anon`-granted; the table's actual ACL is `postgres, authenticated, service_role` and `has_table_privilege('anon','public.messages',…) = false` — **no real `anon` grant existed there**, so containment is complete (`PUBLIC`-derived rows = 0).

### B. `D-13` — sequence discrepancy RESOLVED (governed sequence retained)

**RLS-4 is retained in the sequence** (not dropped), and the register's condition is satisfied explicitly:

```text
RLS-4A (RLS-4A-1 ✅ executed → RLS-4A-2 pending) → RLS-5 → RLS-3 → RLS-2 → RLS-1 → verification
```

* **F-5 / F-6 are explicitly assigned to `RLS-4A-1` / `RLS-4A-2`** so the function/`EXECUTE` hardening **cannot be silently omitted** — the exact risk `D-13` addresses.
* Executing F-5/F-6 remains gated on **D-5** (which functions are intentional public RPCs) and **D-12** (`anonymise_user` `EXECUTE`), neither of which is authorised yet.
* No reordering contrary to the governed sequence has occurred.


**Task identity:** `CT-P8-RLS-SECURITY-REMEDIATION-PLAN-20260913-039` (type **F** — RLS planning; gate **reopened** by the PO ruling on G0-H / `A-RLS` = **Option A**)
**Date:** 2026-09-14
**Authorities:** master execution authorisation · **G0-H/A-RLS ruling (Option A: RLS confirmed as a separate authorised Phase 8 workstream)** · parent register `docs/architecture/CARBONTALLY_PRODUCTION_RLS_SECURITY_HOLD_AND_REMEDIATION_REGISTER_20260912.md` and spec `…RLS_PRODUCTION_BASELINE_AND_REMEDIATION_SPEC_20260912.md` (both unmodified)
**Environment:** local repository + **non-production** `carbontally_qa_phase8` (read-only census) · HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400` · staged 0 · no commits
**Scope discipline:** planning + posture verification. **No production access** (prohibition preserved), no historical backfill, no test weakening, no product redesign, no commercial/subscription decisions, no Phase 9.

---

## 1. Verified non-production RLS posture census (read-only — the new evidence this plan adds)

Metric | Value | Interpretation
---|---|---
tables with RLS **enabled** | **133 / 133** | `rls_disabled = 0` — every public table is RLS-protected
`FORCE ROW LEVEL SECURITY` | **0** | owners/superusers still bypass RLS → consistent with **D-11** ("FORCE RLS remains deferred")
org-scoped tables (`organization_id`) | **54** | the tenancy surface
org-scoped tables **with ≥1 policy** | **49** | —
org-scoped tables **with RLS but NO policy** | **5** | **fail-closed coverage gaps** (§2)
policies granted to **`anon`/`public`** | **0** | no anonymous read path exists via policy
`anon` table **grants** on org-scoped tables | **182** | least-privilege concern, **not** an exposure (no admitting policy)

**The decisive distinction:** `anon` holds 182 table-level grants but **zero policies admit it**, so RLS denies every row — **fail-closed**: a **least-privilege/defence-in-depth** matter, **not** a live exposure in this environment. It nonetheless corroborates the register's **D-1** finding (97 anonymously *accessible* tables in production) from an independent direction, and containment is the cheapest item.

## 2. Coverage gaps found (fail-closed, functionally inaccessible)

RLS enabled, **no policy at all** — unreachable by any RLS-bound client role:

## 3. The blocking decision register (13 items — authoritative, unchanged)

Reproduced from the RLS hold register §8 (**Q1…Q13 / D-1…D-13**). None may be inferred; each gates a specific remediation step.

| # | Decision | Why it blocks |
|---|---|---|
| **D-1** | Authorise **anonymous-grant containment** (RLS-4A-1) as an independent step? | 97 anonymously accessible tables in production; **the fix needs no RLS change** → cheapest first step |
| **D-2** | Accept the status of the **12 production-missing tables** (7 billing, 2 consultant, `vehicles`, `work_item_assignments`, `data_discovery_requests`)? | determines whether Phase 8 / billing features are deployable; **corroborated by §2** |
| **D-3** | Adjudicate the **migration backlog** — apply in dependency order, or freeze the difference? | drift grows with every migration (**now 63 in-repo per `…042`**) |
| **D-4** | Is public/anonymous access to **`emission_factors`** a product requirement? | decides defect vs documented exception |
| **D-5** | Which of the 7 functions are **intentional public RPCs** vs policy-internal? | `EXECUTE` revocation cannot be applied blindly |
| **D-6** | **Who may change an organization member's role**, and by what path? | required before RLS-5 |
| **D-7** | **`users_update_self` — which columns** may a user update? | required before RLS-5 |
| **D-8** | Replace direct **Realtime** access on tenant tables with backend mediation? | determines `notifications` / `staff_workload` policies |
| **D-9** | Is a **tenant `organization_id` nullability** remediation acceptable? | the tenancy hole persists otherwise |
| **D-10** | Authorise a **dedicated read-only production DB role** for verification? | removes the transient-login discovery mechanism |
| **D-11** | Confirm **`FORCE RLS`** remains deferred? | re-affirm after activation — census: `force_rls = 0` (**consistent**) |
| **D-12** | Review **`anonymise_user` `EXECUTE` to `anon`** | potential unauthenticated data-mutation surface |
| **D-13** | Confirm whether **RLS-4 remains in the sequence** (§6.1) or reassign F-5/F-6 | prevents silent loss of function/`EXECUTE` hardening — **the sequence discrepancy** |

## 4. Planned remediation sequence (proposed; each step pending its decision)

1. **RLS-4A-1 — anonymous-grant containment** (needs **D-1** only; no RLS/policy change): census `anon` privileges per org-scoped table → revoke → re-run the §1 census to prove **182 → 0**, and prove no `anon` policy exists before *and* after.
2. **Policy coverage for the 5 fail-closed tables** (**D-2**) using a policy model consistent with the B-chain's `p8_disclosure_is_org_member/_admin` posture — **no new tenancy model invented**.
3. **Function/`EXECUTE` hardening** (**D-5**, **D-12**; **D-13** settles the sequence).
4. **Tenancy integrity** (**D-6**, **D-7**, **D-9**).
5. **Realtime mediation** (**D-8**) · **verification role** (**D-10**) · **`FORCE RLS` re-affirmation** (**D-11**).

All steps: QA-only, additive, one migration per step, `rc=0` ×2 re-apply, parity checks (pre-existing grants/policies/RLS flags unchanged), then the §5 verification. **Production remains prohibited (G0-D).**

## 5. Verification plan

Every step must demonstrate: (a) the target metric **before → after**; (b) **parity** — no pre-existing policy, grant or RLS flag altered; (c) for any added policy, cross-tenant **DENY** and same-tenant **ALLOW** tests; (d) no test weakened or deleted; (e) an **independent** re-run of the §1 census queries.

## 6. Carried-forward obligations

1. **D-1…D-13 PO rulings** — **D-1 is the natural first** (no RLS change required).
2. The **sequence discrepancy** (D-13 / register §6.1) must be resolved before step 3.
3. **G0-D** production prohibition stands; **D-10** concerns a *verification* role, not production remediation.
4. `…046` proceeds once this workstream's prerequisites are satisfied.

## 7. Verdict

### `…039 RLS REMEDIATION PLAN COMPLETE — POSTURE VERIFIED (133/133 RLS-ENABLED · FORCE RLS DEFERRED · ZERO ANON POLICIES · 182 ANON GRANTS = FAIL-CLOSED LEAST-PRIVILEGE, NOT EXPOSURE · 5 FAIL-CLOSED COVERAGE GAPS CORROBORATING D-2); HOLDING AT THE 13 RLS DECISIONS (D-1…D-13)`


`billing_credit_ledger` · `billing_orders` · `billing_payment_records` · `billing_storage_usage` · `data_discovery_requests`

**Material reconciliation:** this set is exactly the **billing + `data_discovery_requests`** group the register lists under **D-2** as *production-missing* tables (7 billing / 2 consultant / `vehicles` / `work_item_assignments` / `data_discovery_requests`). The census therefore **independently corroborates D-2** and shows the pattern is not merely production drift: without a policy these tables are **unusable**, making remediation a **functional** necessity as well as a security one.
