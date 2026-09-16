# CT-P8-RLS-4A-2 — AUTHENTICATED GRANT HARDENING — IMPLEMENTATION + INDEPENDENT VERIFICATION

**Task:** `CT-P8-RLS-4A-2-AUTHENTICATED-GRANT-HARDENING` (Phase 8 separate security workstream)
**Authority:** PO decision of 2026-09-14, item 6 — *"Authorise the bounded security remediation to revoke unnecessary blanket TRUNCATE-class privileges from signed-in application users, subject to the existing RLS/security contract and independent verification. Do not expand this into the unresolved RLS steps 3–5."*
**Register scope:** RLS remediation register §6.1 — RLS-4A-2: *"reduce `authenticated` from `ALL` to `SELECT,INSERT,UPDATE,DELETE` (dropping `TRUNCATE` / `REFERENCES` / `TRIGGER`) … Operation types: REVOKE only."*
**Date:** 2026-09-14 · **Type:** IMPLEMENTATION + INDEPENDENT VERIFICATION (non-production)
**Verdict:** **EXECUTED — VERIFIED — READY FOR PO REVIEW/CLOSURE**

---

## 1. What changed

| Item | Value |
|---|---|
| New migration | `supabase/migrations/20260922000000_p8_rls_4a2_authenticated_grant_hardening.sql` |
| Operation type | **REVOKE only** (no ENABLE, no policy change, no grant to any role) |
| Role affected | **`authenticated` only** (signed-in application users) |
| Privileges revoked | `TRUNCATE`, `REFERENCES`, `TRIGGER`, and — see §3 — `MAINTAIN` |
| Durability | matching `ALTER DEFAULT PRIVILEGES … REVOKE` for `public` tables created by `postgres` |
| Environment | **`carbontally_qa_phase8`** (PO-named Phase 8 QA environment, 2026-09-14) + disposable clones |
| Production | **not touched** (G0-D open; production remains unauthorised) |
| RLS flags / policies / data / columns / constraints / indexes | **unchanged** |

## 2. Measured effect (live, `carbontally_qa_phase8`)

| Measurement | Before | After |
|---|---|---|
| Relations where `authenticated` holds **TRUNCATE** | **119** | **0** |
| … holds **REFERENCES** | **119** | **0** |
| … holds **TRIGGER** | **119** | **0** |
| … holds **MAINTAIN** | **119** | **0** |
| … holds **SELECT** (must be preserved) | 125 | **125** |
| … holds **INSERT** | 109 | **109** |
| … holds **UPDATE** | 108 | **108** |
| … holds **DELETE** | 108 | **108** |
| Public RLS **policies** | 197 | **197** |
| RLS-**enabled** tables | 133 | **133** |
| `anon`-exposed relations | 1 (`emission_factors`, D-4 gate) | **1** |

Migration NOTICE on QA: `RLS-4A-2: tables processed=119, authenticated non-DML relations before=119, after=0 (privs=TRUNCATE, REFERENCES, TRIGGER, MAINTAIN)`.

## 3. Two implementation facts that shaped the change (declared, evidence-based)

1. **`MAINTAIN` included (PostgreSQL 17.6).** The register's target is *"exactly SELECT,INSERT,UPDATE,DELETE"*, but PG 17 added `MAINTAIN` (VACUUM/ANALYZE/REINDEX/CLUSTER/REFRESH), which `authenticated` held on the same 119 relations. The stated target posture is unreachable without revoking it; `MAINTAIN` is the same non-DML blanket class, so revoking it **completes** the ratified target. **Called out here so the PO can veto it** (regranting is one statement).
2. **Default privileges made the hardening durable.** `public` carries a default ACL registered by `postgres` granting `Dxtm` (TRUNCATE, REFERENCES, TRIGGER, MAINTAIN) to `authenticated` on **future** tables, so a table-level `REVOKE` alone would have been undone by the next `CREATE TABLE`. The matching default-privilege `REVOKE` was therefore included (same role, same privilege class, still REVOKE-only).

## 4. Independent verification

| # | Check | Evidence | Result |
|---|---|---|---|
| V1 | Additive/structural discipline | full public-schema fingerprint before/after on a disposable clone (`ct_rls4a2_20260914`); delta = **exactly one line** — the `public` table default-ACL entry for `authenticated`. **No `rls`, `pol`, `col` or `con` line changed.** | **PASS** |
| V2 | Idempotency | apply #1 `rc=0`, apply #2 `rc=0` (both with `ON_ERROR_STOP=1`); posture identical after both | **PASS** |
| V3 | Privilege outcome (clone + QA) | TRUNCATE/REFERENCES/TRIGGER/MAINTAIN 119 → **0**; SELECT/INSERT/UPDATE/DELETE preserved | **PASS** |
| V4 | Behavioural NEGATIVE (grant level) | `SET ROLE authenticated; TRUNCATE TABLE public.issues;` → **`ERROR: permission denied for table issues`** on the clone **and** on QA | **PASS** |
| V5 | Behavioural POSITIVE | `SET ROLE authenticated; SELECT count(*) FROM public.issues;` → executes (0 rows via RLS, no privilege error) | **PASS** |
| V6 | RLS unchanged | policies 197 before/after; RLS-enabled tables 133 before/after; no policy text changed (V1) | **PASS** |
| V7 | `anon` not touched | `anon`-exposed relations still **1**; migration does not touch `anon` (RLS-4A-1 / D-4 scope) | **PASS** |
| V8 | **Causality (A/B)** — the one suite that errored | `test_disclosure_b3_v3_security.py` (9 setup errors) run **with** the hardening (`auth_truncate=0`) and with it **temporarily reverted** (`auth_truncate=133`): **identical 9 errors in both** → **not caused by this change**. Root cause: a **data-dependent fixture** (`TypeError: 'NoneType' object is not subscriptable`) on a schema-only clone | **PASS (not a regression)** |
| V9 | Data-dependence of the remaining failure | `test_disclosure_b3_projection_runtime.py::test_intensity_catalogue_and_ratio_selection` needs the 4 B3 intensity seeds: clone (schema-only) = **0**, QA = **4**. `test_factor_baseline_unchanged` expects 7049 factors: QA currently holds **0**. Both are **environment/clone-fidelity** artefacts, not privilege regressions | **PASS (attributed)** |
| V10 | Phase 8 suites on the hardened posture | targeted run (`report_versions`, `report_lifecycle`, `s1s3_iv_invariants`, `s2_is_current_invariant`, `disclosure_b1_runtime`, `v3_rls_behavior`, `disclosure_b3_projection_runtime`, `disclosure_b4_finalisation_runtime`, `evidence_line_items_b2_runtime`): **no failure or error attributable to this change** | **PASS** |

**F-046-1 restated:** every exclusive/destructive operation ran on disposable `ct_*` clones
(`ct_rls4a2_20260914`, `ct_rls4a2_reg_20260914`) restored `--schema-only` from QA, with
`current_database()` verified first. QA received only the authorised migration.
**No production access of any kind.**

## 5. Findings raised by this work

### 5.1 `F-4A2-1` — verification-harness trap: **`psql -f` returns `rc=0` on SQL error**

The first application reported `rc1=0` while the migration had **failed**
(`ERROR: malformed array literal: "MAINTAIN"` — the `privs := privs || 'MAINTAIN'`
array-concatenation ambiguity in PL/pgSQL) and its transaction correctly rolled back.
**`psql -f` does not fail the exit code unless `-v ON_ERROR_STOP=1` is set.** Corrected:
the migration now uses `array_append`, and every later application used `ON_ERROR_STOP=1`.
**Any earlier "rc=0" evidence that did not set `ON_ERROR_STOP` is weaker than it looks** —
recorded as a methodology finding for all future migration verification.

### 5.2 `F-4A2-2` — the **`anon` default-privilege gap is deliberately NOT fixed** (out of scope)

The same `public` default ACL that granted `authenticated` `Dxtm` also grants **`anon`** that
class on every future table. RLS-4A-1 revoked `anon` privileges **at table level**, so new
tables re-acquire them. The PO's decision 6 covers **signed-in users only**, so this is
**reported, not fixed** — fixing it touches the `anon` surface (RLS-4A-1 scope and the
unratified `D-4` question about `emission_factors`). **Separate authorisation required.**

### 5.3 Residual least-privilege observations (not actioned)

* `service_role` retains full privileges (by design — backend role).
* `anon` default ACL also grants sequence `w` (UPDATE) — same class of gap as §5.2.
* `emission_factors` remains the single `anon`-exposed relation, pending `D-4`.

## 6. Limitations (honest)

* A schema-only clone cannot exercise data-seeded suites (no factor catalogue, no B3 seeds);
  those failures were **attributed by direct row-count comparison and an A/B test**, not assumed away (§4 V8/V9).
* No browser/E2E pass; this is a database-privilege verification.
* Verified on **QA + disposable clones** only; production remains unapplied and unauthorised.

## 7. Verdict and status

**RLS-4A-2 — IMPLEMENTED, APPLIED TO QA, INDEPENDENTLY VERIFIED — READY FOR PO REVIEW/CLOSURE.**
(Not self-closed: closure is a PO act.)

*Not authorised by this work:* RLS steps 3–5 (`D-4`…`D-10`, `D-12` remain undecided), the
`anon` default-privilege fix (§5.2), and any production application.

## 9. PO closure (2026-09-14)

> **PO DECISION: "F-4A2-2 / RLS-4A-2 — PO CLOSED."** The `authenticated` grant hardening
> (this record, §1–§8) is **accepted as implemented and independently verified.**

* **Status: CLOSED — PO ACCEPTED.**
* Bundled with it: `F-4A2-2` (RLS-4A-1 durability, `…060`) is likewise **PO CLOSED**.
* **Not** authorised and **not** performed: RLS steps 3–5 (`D-4`…`D-10`, `D-12`) and the `anon` sequence-default observation.
* Recorded by transcription of the PO's decision only; no self-closure.

## 8. Repository / worktree state

| Item | Value |
|---|---|
| New file | `supabase/migrations/20260922000000_p8_rls_4a2_authenticated_grant_hardening.sql` |
| Code / tests changed | **none** |
| Branch / HEAD | `main` / `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged) |
| Commits | **none** |
| Clones created | `ct_rls4a2_20260914`, `ct_rls4a2_reg_20260914` (disposable) |
| Production | untouched |

