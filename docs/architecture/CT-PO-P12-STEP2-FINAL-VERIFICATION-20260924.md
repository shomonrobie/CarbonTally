# CT-PO-P12-STEP2-FINAL-VERIFICATION-20260924

**Reference:** `CT-PO-P12-STEP2-FINAL-VERIFICATION-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924` — **Step-2 final remediation + verification pass**
**Status:** STEP-2 DELIVERABLE — final verification
**Production deployment:** **NOT AUTHORIZED**

---

## 0. Repository

| Item | Value |
| --- | --- |
| Starting SHA | `54ee52cc819949e7694623fd51ae6513f0fe044a` |
| Ending SHA | recorded in §9 (the commit created by this pass) |
| Branch | `p8-release-reconciled` |
| Remote | `github` → `https://github.com/shomonrobie/CarbonTally.git` |
| Remote alignment | `github/p8-release-reconciled == HEAD` |
| Working tree | this pass changed **`tools/demo_lab/stack.py`** + `docs/architecture/` only; the pre-existing `.gitignore` modification and 13 pre-existing untracked artifacts remain untouched |
| Product code | **UNCHANGED** (`git diff 35eb7ba..HEAD -- ':!docs' ':!tools/demo_lab'` is empty) |

## 1. Protected environments

| Environment | Before | After | Mutation status |
| --- | --- | --- | --- |
| `postgres` (flagship) | 116 tables / 975 orgs / 1,343 users / 1,125 members | 116 tables / **975** orgs / **1,344** users / **1,125** members | **NO business-data mutation** — see §1.1 |
| `carbontally_test` | 117 tables / 15 orgs / 717 users | identical | **NO** |
| `carbontally_qa_phase8` | 133 tables / 25 orgs / 498 users | identical | **NO** |
| production | not accessed | not accessed | **NO** |

Evidence for the `postgres` row: `created_at::date = CURRENT_DATE` → `users = 1`,
`organizations = 0`, `organization_members = 0`, `processing_entities = 0`,
`staff_profiles = 0`, `audit_trail = 0`.

### 1.1 Resolution of the `1343 → 1344` contradiction (mandatory finding)

**Classification: A (the earlier "unchanged" wording was imprecise) + B (lab-identity
rows in the stack IdP by design). NOT an unauthorized protected-environment mutation.**

```text
postgres.public.users @demo-lab.carbontally.local = 14
  · 13 rows created 2026-09-19 16:39  (original DEMO-T1 provisioning — BEFORE Step 2)
  ·  1 row  created 2026-09-24 09:45  pe.beta.manager@demo-lab.carbontally.local
postgres.auth.users  @demo-lab.carbontally.local = 14   (same set)
carbontally_demo_local.public.users              = 14   (all lab)
carbontally_test / carbontally_qa_phase8 @demo-lab.* = 0
mechanism: trg_sync_auth_user_to_public_users AFTER INSERT ON auth.users
           EXECUTE FUNCTION sync_auth_user_to_public_users()
```

The pre-Step-2 baseline of **1,343 already contained the 13 lab identities**, so the
Demo Lab's auth delegation has always written lab rows into the stack IdP database —
the documented design (`tools/demo_lab/README.md` §7 limitation 2). Adding the
authorized `pe.beta.manager` actor produced exactly **one** new row there. No
organisation, membership, processing-entity, staff-profile or audit row was added; no
flagship data was deleted, migrated or reseeded; `public.organizations` is unchanged at
975. **No STOP condition was triggered.**

## 2. Repeatability — FAILED, with a proven root cause

### 2.1 Measurement (full, untruncated capture this time)

| Measurement | tables | RLS | **public policies** | zero-policy tables | insight | D32 | constraints | migration errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clean single pass **A** | 141 | 141 | **218** | 61 | 6 | 4 | 551 | **0** |
| Clean single pass **B** | 141 | 141 | **218** | 61 | 6 | 4 | 551 | **0** |
| Full `run_demo_lab.sh` cycle | 141 | 141 | **210** | 61 | 6 | 4 | — | 0 |
| **Second stack pass** on that state | 141 | 141 | **298** | **56** | 6 | 4 | — | 1 (`20260801000000_rc2_constraints.sql`, phase1) |

A vs B: **0 policies only-in-A, 0 only-in-B** — a clean single pass is byte-identical
and therefore deterministic.

### 2.2 Proven root cause

**The migration application is NOT idempotent: each additional pass ADDS policies**
(210 → 298 on a second pass; zero-policy tables 61 → 56; a phase-1 migration error
appears on re-run). This explains the historical figures:

```text
Cycle 1 = 298 policies  ← the database had received TWO migration passes
                          (a failed pre-fix attempt, then the successful pass)
Cycle 2 = 210 policies  ← one pass
```

It also falsifies the harness README's claim that *"Every step is idempotent:
re-running creates nothing twice"* **for the schema build**.

**Residual unexplained variance (recorded, not hidden):** one full-path cycle produced
**210** where the stack-only path produced **218** for the same release and code. The
8-policy delta is **not explained** by the available evidence.

### 2.3 Classification

```text
schema deterministic   : YES for a single stack pass (A == B, 0 differences)
policy deterministic   : YES within one path; NO across repeated passes
seed deterministic     : not established (blocked by the schema question)
runtime deterministic  : not established
FINAL                  : REPEATABILITY NOT ESTABLISHED
CAUSE CLASS            : demo-lab harness (non-idempotent migration application) and/or
                         one non-idempotent release migration
```

**Exact remediation:** make the migration application idempotent (or build the schema
exactly once per reset and assert a frozen policy manifest: count **and** name set),
then re-run two clean cycles and diff. Do **not** re-run until the counts happen to
match.

## 3. RLS zero-policy tables

| Measurement | count |
| --- | --- |
| Single clean pass | **61** |
| After a second stack pass | **56** |

All are **intentional fail-closed / service-role-only** state: RLS enabled with no
policy denies every RLS-bound role (the conservative posture). `verify.py` reports
18/18 isolation rules and the app role (`postgres`, `bypassrls = true`) performs all
server-side work. **No table was found where zero policies is an unintended hole**; the
count's *variation* is a symptom of §2.2, not a separate defect.

## 4. Disposable integration verification

| Item | Value |
| --- | --- |
| Clone | `ct_p12_final_integration` (protected-marker check passed; `CREATE DATABASE` + `pg_dump` schema+data+privileges from `carbontally_demo_local`) |
| Safety | canonical lab, `postgres`, `carbontally_test`, `carbontally_qa_phase8` never targeted |
| Start / end | 2026-09-24T10:15:36Z → 10:15:40Z |
| Command | `INTEGRATION_DATABASE_URL=…/ct_p12_final_integration pytest <9 suites> -q --tb=no -rf` |
| Result | **exit 1 — 12 failures** (was **21** before this pass's D-2-07 fix; **9 privilege-posture failures resolved**) |
| Cleanup | clone **DROPPED**, verified |

### 4.1 Per-test classification (all 12 residual failures)

| # | Test | Failure | Root cause | Classification | Blocking? |
| --- | --- | --- | --- | --- | --- |
| 1 | `test_consultants.py::test_profile_and_firm_member_roundtrip` | `assert None is not None` — `get_profile_by_user()` returned None after `create_profile()` | not established | **UNRESOLVED — possible product/query issue; needs independent follow-up** (not dismissed as stale) | open (not on the demo path) |
| 2 | `test_consultants.py::test_update_client_status` | `TypeError: add_client() missing 3 required positional arguments` | test calls `add_client(profile.id, org_id, "ACME LTD")`; the repository now requires `client_industry`, `client_contact_email`, `client_contact_name` | **stale test (pre-existing)** — the same file's other test passes all 6 args | no |
| 3 | `test_consultants.py::test_list_clients_firm_scoped` | same signature drift (3-arg call, line 57) | same | **stale test (pre-existing)** | no |
| 4 | `test_v3m1_v3m2_processing_entities.py::test_factor_baseline_unchanged` | `expected 7049 total factors, got 1` | the shared session fixture TRUNCATEs `emission_factors` (`conftest._TRUNCATE_TABLES`), so a global-population invariant cannot hold | **environment/fixture coupling (pre-existing)** | no |
| 5 | `test_v3_rls_behavior.py::TestBillingSecurityLockdown::test_authenticated_cannot_grant_credit_entitlement` | `DID NOT RAISE` | residual `authenticated` INSERT on `billing_credit_ledger`, `billing_idempotency_keys`, `billing_commercial_config` | **demo-lab over-grant — residual (D-2-07 partial fix)** | no (RLS still enforced) |
| 6 | `test_v3_rls_behavior.py::TestBillingDenyByDefault::test_authenticated_cannot_write_d37_tables` | same | same | as above | no |
| 7–12 | `test_calculation.py` — `test_calculate_produces_correct_co2e_and_persists_snapshot`, `test_content_hash_is_verifiable`, `test_calculate_updates_existing_log`, `test_calculate_publishes_and_persists_events`, `test_calculate_records_audit_entry`, `test_unit_mismatch_is_rejected_without_persistence` | `ForeignKeyViolationError: update or delete on table "emission_factors" violates foreign key constraint "calculation_snapshots_factor_id_fkey"` | the tests replace a factor while a snapshot references it (the clone carries seed data) | **fixture/data-precondition (environment)** | no |

## 5. Objective resolutions (§9–§16)

| § | Question | Resolution |
| --- | --- | --- |
| **§9** | Privilege posture: over-grant, obsolete test, or release defect? | **Option A — the Demo Lab was over-granted.** The release migrations **explicitly REVOKE** from `authenticated` (`REVOKE INSERT, UPDATE, DELETE ON public.usage_tracking`, `… public.customer_subscriptions`, `REVOKE UPDATE ON public.organizations / public.users`, plus RLS-4A2's dynamic revoke). The harness then ran a **blanket post-migration GRANT** that restored them. **Fixed in `tools/demo_lab/stack.py`** — the Supabase baseline now comes from `ALTER DEFAULT PRIVILEGES` *before* the migrations, and the blanket grant + anon SELECT baseline were removed. Effect: **9 failures resolved**; `usage_tracking` / `customer_subscriptions` `authenticated` INSERT now **0**. Residual: 3 billing tables still carry INSERT (2 remaining failures). |
| **§11** | Six FK failures | Fixture/data precondition in the clone (factor replacement while a snapshot references it). No fake factor ids, no FK disabling, no schema change. |
| **§12** | Drift failures | `B2 policy count 3 != 2` — **now PASSES**; the earlier failure was caused by the over-grant interfering (so it was environmental). `add_client()` 3-arg call sites — **stale tests** (the same file's other test passes 6 args). `factor baseline 7049 != 1` — **fixture coupling** (the fixture truncates the population it asserts). One **unresolved** round-trip failure (#1) is flagged for follow-up rather than dismissed as stale. |
| **§13** | `audit-activity` for `internal_operator` → 200 | **RESOLVED — correctly scoped, NOT a defect.** `internal_operator` → Org A **200**, Org B **200** (internal ops staff may read the ops audit plane); `org_a_owner` → Org A **200**, **Org B 403 "Organization access denied"**; `org_a_viewer` → Org A **403 "Audit records require organisation owner/admin access"**. Tenant isolation and the owner/admin gate are enforced; **no cross-tenant leak by a customer actor**. |
| **§14** | `enqueue` → 422 | **Contract observation, non-blocking.** The endpoint requires a request body; the **upload path enqueues automatically**, which is why processing succeeded regardless. No product change (no authoritative contract contradicted). |
| **§15** | `uk-water` `no_match` vs `EXPECTED_MATCHED` | **Not re-investigated this pass — remains OPEN.** The contract still declares `EXPECTED_MATCHED`; no match was fabricated. |
| **§16** | reassignment_history / partial release / Insight interactions | **Classifications unchanged** (no new evidence): assignment-row model records the reassignment; release closes the whole lease (no partial-quantity release exists); the `tools/invoke` `ToolResult` is the authoritative Insight execution record. |

## 6. Final security verification

```text
actor contexts        : 14/14 correct   (manifest now includes pe_beta_manager)
authorization probes  : 30/30 as expected
isolation rules       : 18/18 enforced
verify.py exit code   : 0
unexpected ALLOW      : 0
unexpected DENY       : 0
PE Alpha -> PE Beta   : 403 (batch items / item workspace / work claim)
PE Beta  -> PE Alpha  : 403
support role positive : 201 (platform_admin, can_manage_staff = true)
support role negative : 403 (internal_operator, can_manage_staff = false)
audit-activity scope  : customer cross-tenant 403; viewer 403; internal staff 200 (intended)
```

**No unexplained authorization result remains.**

## 7. Final demo evidence (restored canonical environment)

```text
orgs 4 · users 14 · PEs 2 (Alpha + Beta) · batches 4 · work items 11
calculation snapshots 2 · emissions logs 2 · evidence lines 2 · snapshot->line links 2
blocked documents 10 · tabular documents 1
work_item_assignments 7 · conversations 7 · messages 5 · report versions 3
facilities 1 · assets 1 · suppliers 1 · factors 7,049 · insight tables 6
EV-01: evidence lines FORWARD/csv -> line 1 = 2469.169780, line 2 = 1706.734000,
       both linked; Source Evidence Viewer 200, drill_down_depth FULL, document_available True
P1 shape mode: shadow (unchanged) · no direct evidence inserts · no backfill
```

## 8. Remaining issues (complete list)

| # | Issue | Class | Blocking? |
| --- | --- | --- | --- |
| 1 | **Migration application is not idempotent** — a second stack pass raises public policies 210 → 298 and errors on `20260801000000_rc2_constraints.sql` | demo-lab harness / migration chain | **BLOCKING (repeatability)** |
| 2 | **Single-pass variance across paths** — full-path cycle 210 vs stack-only 218, unexplained | demo-lab harness | **BLOCKING (repeatability)** |
| 3 | **Instrumentation gap** — the *earlier* cycles' policy manifests were not captured, so the historical 298 cannot be fully reconciled | process | non-blocking (remediation = manifest assertion) |
| 4 | Disposable integration suites **not green** (12/92 failing) | environment + pre-existing test drift | **BLOCKING (not proven green)** |
| 5 | Residual `authenticated` INSERT on `billing_credit_ledger`, `billing_idempotency_keys`, `billing_commercial_config` | demo-lab over-grant (D-2-07 residual) | non-blocking (RLS enforced) |
| 6 | `test_consultants.py::test_profile_and_firm_member_roundtrip` — `get_profile_by_user()` returned None | **UNRESOLVED — possible product/query issue** | open; must be investigated before production |
| 7 | Two stale `add_client()` call sites; one fixture-coupled factor-baseline test | pre-existing test drift | non-blocking |
| 8 | `uk-water` maps `no_match` although the contract declares `EXPECTED_MATCHED` | data/contract | non-blocking; open |
| 9 | `enqueue` requires a body (422) while the upload path auto-enqueues | API contract observation | non-blocking |
| 10 | `reassignment_history` unwritten; no partial-quantity release; `carbontally_insight_interactions` unwritten by `tools/invoke` | product contract questions | non-blocking (documented) |
| 11 | Documentation conflicts D-09/D-10/D-11/D-12/D-14/D-27 unchanged | documentation | PO decisions |
| 12 | `postgres.public.users` +1 (lab identity row) — now fully explained, but it means the flagship DB doubles as the lab IdP | design consequence | non-blocking (monitor) |

## 9. Git and final gate

```text
starting SHA : 54ee52cc819949e7694623fd51ae6513f0fe044a
ending SHA   : (this pass's commit; see the implementation-report addendum)
branch       : p8-release-reconciled
push target  : github/p8-release-reconciled
changes      : tools/demo_lab/stack.py (phased migration ordering, D-2-07 grant fix)
               + docs/architecture/CT-PO-P12-STEP2-FINAL-VERIFICATION-20260924.md
no product code, no UI, no Step-3 work, no secrets
```

### Gate decision

```text
STEP 2 INCOMPLETE
```

**Blockers (exactly two, both now root-caused):**

1. **Repeatability** — the schema build is **not idempotent** (proven: 210 → 298 policies on a second pass, plus a migration error on re-run), and single-pass results differ across the two harness paths (210 vs 218, unexplained). The environment cannot yet be shown to be reproducibly rebuildable.
2. **Disposable integration acceptance** — the required suites **executed but are not green** (12/92 failing). All 12 are classified (2 residual over-grant, 6 fixture precondition, 3 stale/coupled tests, 1 unresolved product-suspect), and the pass improved the result from 21 → 12, but no acceptance rule in the governing contract permits treating a non-green integration run as passing, so the criterion is not met.

**Resolved this pass:** protected-environment integrity (the `+1` is explained and is not an unauthorized mutation); the 9 privilege-posture failures (D-2-07 fixed in the harness); the `audit-activity` authorization question (correctly scoped, not a defect); the D32 migration error (phased ordering, 0 migration errors).

```text
STEP 3 NOT STARTED
```
