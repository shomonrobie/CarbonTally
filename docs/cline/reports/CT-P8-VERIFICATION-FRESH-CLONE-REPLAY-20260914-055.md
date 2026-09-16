# CT-P8-VERIFICATION-FRESH-CLONE-REPLAY-20260914-055

**Task:** independent verification — **fresh-clone zero-delta replay** (discharges the B4 gate-V4 `A1` residual and extends the proof to the two newest migrations)
**Date:** 2026-09-14 · **Authority:** master execution authorisation `…050` (verification is part of the programme; no new PO gate needed)
**Environment:** **disposable clones only** — no production, no persistent QA writes. Git HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400` · staged 0 · no commits.
**F-046-1 (restated — programme invariant):** the integration harness performs destructive setup (`TRUNCATE … RESTART IDENTITY CASCADE`) and must never target a persistent/authoritative database. This task used **`CREATE DATABASE … TEMPLATE`** clones (`ct_b4v4_20260914`), verified by name before use; `carbontally_qa_phase8` was used for **read-only** checks only.

---

## 1. Why this task

* **B4 closure `…052` §2 recorded an explicit residual:** *"the fresh-clone zero-delta replay was last executed for the B3/V3 gate; for B4 it is proven by idempotent re-application plus the additive-only measurement, and is carried as a residual for the next verification pass."* This is that pass.
* The RLS-4A-1 and S2 `is_current` migrations had likewise only been proven on the **persistent QA** environment; the same replay closes that gap.
* Verification is authorised programme work, so this proceeds without a new PO decision.

## 2. Method (reproducible)

1. Locate a genuine **pre-B4 base**: `ct_b3_v3_20260913` — verified to contain B1 + B3 but **no** `disclosure_narrative_entries`, **no** `report_version_artifacts`, **no** S2 index.
2. `CREATE DATABASE ct_b4v4_20260914 TEMPLATE ct_b3_v3_20260913` → a disposable clone.
3. Capture a **fingerprint** of pre-existing objects: every `TABLE` (+ RLS/force flags), `POLICY` (+ roles/cmd), `GRANT` (per table/role/privilege) and `INDEX` in `public` — **3696 lines**.
4. Apply **`20260918000000_p8_b4_narrative_overlay.sql`** and **`20260919000000_p8_b4_frozen_artefact.sql`** — each **twice** (idempotency).
5. Capture the post-state fingerprint (**3740 lines**) and compute the set difference with an **order-independent, locale-safe** method (`grep -Fxv -f`) rather than `comm` (which warns when collation order differs — a trap worth recording).
6. Replay the two newest migrations (`20260920000000_p8_rls_anon_grant_containment.sql`, `20260921000000_p8_s2_is_current_single_valued.sql`) on the same fresh base, each twice.
7. Assert the ratified posture on the clone: S2 index present, RLS enabled table count, and the authoritative `anon` privilege check.

## 3. Results

| # | Check | Result |
|---|---|---|
| V1 | clone created from the pre-B4 base | `createdb_rc=0` |
| V2 | **B4-1 applies and re-applies** | **`rc=0`, `rc=0`** |
| V3 | **B4-2 applies and re-applies** | **`rc=0`, `rc=0`** |
| V4 | RLS-4A-1 applies and re-applies | `rc=0`, `rc=0` |
| V5 | S2 `is_current` applies and re-applies | `rc=0`, `rc=0` |
| V6 | **total schema delta** | **added 44 lines, removed 0** |
| V7 | **unattributable additions** (anything not about the two new B4 tables) | **0** |
| V8 | **removed/changed pre-existing objects** | **0** — *zero-delta proven* |
| V9 | added objects, categorised | **2 TABLE + 4 POLICY + 9 INDEX + 29 GRANT = 44** |
| V10 | new tables' RLS posture | both `rls=true force=false` (B4 posture honoured; `FORCE RLS` still deferred — D-11) |
| V11 | new policies | `disclosure_narrative_entries_read/_write`, `report_version_artifacts_read/_insert` — exactly the ratified B4 posture, `roles={authenticated}` only |
| V12 | S2 index on the fresh base | present (`report_versions_one_current_per_report`) |
| V13 | RLS-enabled tables on the clone | **133** (matches the QA posture) |
| V14 | authoritative `anon` privilege check on the clone after RLS-4A-1 | **1 relation only — `emission_factors`** (the D-4-governed table, deliberately excluded) |

**Conclusion:** the B4 migrations are **idempotent and strictly additive on a fresh clone**, with **zero modification of any pre-existing object**; the RLS-4A-1 and S2 migrations are likewise idempotent on a fresh base and reproduce the ratified posture. **The B4 gate-V4 `A1` residual is discharged and PASS.**

## 4. Verifier trap recorded (for future sessions)

`information_schema.role_table_grants` **over-reports** `anon` grants: it reports rows for `messages` even though that table's ACL contains **no `anon`** and `has_table_privilege('anon','public.messages', …) = false` (a `PUBLIC`/inheritance reporting artefact). A naive "is RLS-4A-1 done?" check built on that view returns a **false negative**.

**Rule: privilege conclusions must come from `has_table_privilege` (or `pg_class.relacl`) — never from the information-schema view alone.** This is why the D-1 verification and this report both use the authoritative function, and why re-checking the persistent QA environment after the session break confirmed **no regression** (still exactly 1 relation: `emission_factors`).

## 5. Carried-forward obligations

1. RLS-4A-2 + RLS steps 3–5 — gated on `D-4`…`D-10`, `D-12` (unauthorised).
2. S6 backlog item — comments + `A7` visibility.
3. P1 customer-visible enablement — external real-document shadow evidence.
4. EF-A / EF-D magnitude — requires the real catalogue (production boundary).
5. **F-046-1** remains restated in every report.

## 6. Verdict

### `FRESH-CLONE ZERO-DELTA REPLAY COMPLETE — B4 GATE-V4 A1 RESIDUAL DISCHARGED (PASS); RLS-4A-1 AND S2 ALSO PROVEN IDEMPOTENT ON A FRESH BASE; ZERO PRE-EXISTING OBJECTS CHANGED; DISPOSABLE CLONES ONLY`
