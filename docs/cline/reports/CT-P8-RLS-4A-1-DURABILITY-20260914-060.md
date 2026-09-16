# CT-P8-RLS-4A-1-DURABILITY (F-4A2-2) — ANONYMOUS DEFAULT-PRIVILEGE HARDENING — IMPLEMENTATION + INDEPENDENT VERIFICATION

**Task:** `F-4A2-2` — RLS-4A-1 durability gap (anonymous default privileges)
**Authority:** PO decision of 2026-09-14 — *"F-4A2-2: Option A approved. Proceed with the bounded anonymous-role default-privilege hardening and independent verification. **Do not expand the RLS scope.**"*
**Date:** 2026-09-14 · **Type:** IMPLEMENTATION + INDEPENDENT VERIFICATION (non-production)
**Verdict:** **EXECUTED — VERIFIED — READY FOR PO REVIEW/CLOSURE**

---

## 1. The gap (measured before the fix, not assumed)

RLS-4A-1 revoked `anon` table privileges **table by table**. The `public` default ACL
registered by role `postgres` still granted `Dxtm` (TRUNCATE, REFERENCES, TRIGGER, MAINTAIN)
to `anon` on every **future** table — so the containment would have silently regressed on the
next `CREATE TABLE`.

**Pre-fix durability probe** (disposable clone `ct_4a1b_20260914`): a newly created `public`
table inherited `anon` → `truncate=true refs=true trigger=true maintain=true` (**gap
demonstrated**). The same probe for `authenticated` returned `false` (RLS-4A-2 already durable).

## 2. The change (one statement, REVOKE-only)

`supabase/migrations/20260923000000_p8_rls_4a1b_anon_default_privilege_hardening.sql`:

```sql
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE TRUNCATE, REFERENCES, TRIGGER, MAINTAIN ON TABLES FROM anon;
```

**Deliberately minimal — scope NOT expanded:**

| Not touched | Why |
|---|---|
| **`emission_factors`** (table level) | it is the **unratified product decision D-4**; `anon` keeps its deliberate SELECT *and* its TRUNCATE there, exactly as found |
| sequence defaults (`anon=w`) | a different object type, not part of the approved Option A wording → **recorded as a residual observation** |
| `storage` schema defaults | Supabase-managed, out of scope |
| `service_role` defaults | backend role, required |
| RLS flags, policies, columns, constraints, indexes, data | untouched (proved below) |

## 3. Results

| Check | Evidence | Result |
|---|---|---|
| C1 | default ACL before → after | `{postgres=arwdDxtm, **anon=Dxtm**, service_role=Dxtm}` → `{postgres=arwdDxtm, service_role=Dxtm}` (QA + clone) | **PASS** |
| C2 | **post-fix durability probe** (new table on the clone) | `anon truncate=false refs=false trigger=false maintain=false` | **PASS** |
| C3 | **end-to-end proof** — fresh clone restored from hardened QA, then a new table created | `anon truncate=false maintain=false` · `authenticated truncate=false` (both containments durable) | **PASS** |
| C4 | idempotency | apply #1 `rc=0`, apply #2 `rc=0` (`ON_ERROR_STOP=1` — see `F-4A2-1` in `…059`) | **PASS** |
| C5 | no RLS change | policies **197** before and after; structural fingerprint delta = **exactly one line** (the anon default-ACL entry) | **PASS** |
| C6 | **D-4 boundary respected** | `emission_factors`: `anon` SELECT **true**, `anon` TRUNCATE **true** (unchanged); `anon` table-level non-DML tables on QA = **1** (that table only) | **PASS** |
| C7 | `authenticated` posture unchanged | non-DML privileges still **0** (RLS-4A-2 holds) | **PASS** |
| C8 | effective anonymous access unchanged today | only the pre-existing deliberate `emission_factors` read remains; nothing customer-facing changes | **PASS** |

## 4. Findings

* **`F-4A1B-1` (observation, not actioned)** — `public` **sequence** default privileges still grant `anon` `w` (UPDATE), and the `storage` schema defaults grant `anon` broadly. Both are outside the approved Option A wording. Recorded for a future bounded decision; **not** changed here.
* No other residual: `anon` holds no privileges on any `public` table other than `emission_factors`.

## 5. Limitations

* Durability was proved by **new-table probes on disposable clones** (`ct_4a1b_20260914`, `ct_4a1b_verify_20260914`); **no probe table was created in QA** (QA received only the authorised migration).
* Verified on QA + clones only; **production remains unapplied and unauthorised** (G0-D open).
* RLS steps 3–5 remain **not authorised** and were not touched.

## 6. Verdict

**F-4A2-2 — IMPLEMENTED, APPLIED TO QA, INDEPENDENTLY VERIFIED — READY FOR PO REVIEW/CLOSURE.**
(Not self-closed: closure is a PO act.)

## 9. PO closure (2026-09-14)

> **PO DECISION: "F-4A2-2 / RLS-4A-2 — PO CLOSED. The anonymous-role default-privilege
> hardening is accepted as implemented and independently verified."**

* **Status: CLOSED — PO ACCEPTED.**
* The remaining `anon` **sequence-default `UPDATE`** observation (§4 `F-4A1B-1`) is **not authorised for action now** and is recorded as a **future, separately bounded PO decision**; it was **not** modified as part of this work.
* No self-closure was performed: this record only transcribes the PO's decision.

---

## 7. State

| Item | Value |
|---|---|
| New file | `supabase/migrations/20260923000000_p8_rls_4a1b_anon_default_privilege_hardening.sql` |
| Application/RLS code changed | **none** |
| Branch / HEAD | `main` / `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged) |
| Commits | **none** |
| Clones | `ct_4a1b_20260914`, `ct_4a1b_verify_20260914` (disposable) |
| Production / investor demo | untouched |
| F-046-1 | enforced (clone-only destructive/exclusive work; identity verified first) |
