# CarbonTally — Phase 8 · DEMO-T2-C (Demo Lab factor dataset loading)
## PO DECISION RECORD — DEMO-T2-C CLOSED (2026-09-20)

**Task:** `CT-DEMO-T2-C-PO-CLOSURE`
**Date:** 2026-09-20
**Authority:** PO review and acceptance of the independent verification `OHD Task 078-C` (verdict **PASS — READY FOR PO CLOSURE**)
**Type:** DECISION RECORD — **no implementation, no code change, no test change, no factor-data change, no schema change, no migration, no deployment, no production access**

**Evidence base:**
* implementation — `05de2f3` `feat(DEMO-T2-C): add guarded Demo Lab factor seeding (DEFRA 2025 + SEAI 2025)` on `p8-release-reconciled`
* independent verification — **OHD Task 078-C**, verdict **PASS**
* seeder evidence (outside the repository, by design) — `~/ct_local_env/demo_lab/evidence/t2c_{dryrun,seed,reset}_*.json` (+ `_latest.json`)
* readiness audit of record — DEMO-T2-C readiness report (read-only, no writes)

---

## 1. PO RULING

**DEMO-T2-C is CLOSED.** DEMO-T2-C is recorded as:

| Attribute | Status |
|---|---|
| Implementation | **IMPLEMENTED** (`05de2f3`) |
| Independent verification | **INDEPENDENTLY VERIFIED** (OHD Task 078-C, verdict **PASS**) |
| Governance | **PO-CLOSED** |

Closure statement: **DEMO-T2-C PO CLOSED.**

## 2. ACCEPTED ARTEFACTS (all on `p8-release-reconciled`)

| SHA | Content |
|---|---|
| `05de2f3e26fe788f7d1e49460c010efcdc0399e3` | DEMO-T2-C implementation — new `tools/demo_lab/seed_factors.py`; `tools/demo_lab/run_demo_lab.sh` (bounded `--factors`); `tools/demo_lab/README.md` (§6 factor datasets) |
| `b4e02f4664d25b3776151a964c683cb0432bf040` | parent — DEMO-T2-B DEFRA import provenance (CLOSED; OHD Task 078 verified) |
| `fe36cdc` | predecessor — DEMO-T1 Demo Lab infrastructure + role-bearing identities |
| this document | DEMO-T2-C PO closure decision record |

Authoritative branch **`p8-release-reconciled`**; authoritative GitHub tip at closure **`05de2f3`**
(verified by direct `git ls-remote`); local HEAD == GitHub; push was **fast-forward only** (no force,
no amend, no rebase); working tree **CLEAN** at closure.

## 3. VERIFIED EVIDENCE BASIS (established by independent verification — not restated as new work)

| # | Verified item |
|---|---|
| 1 | **7,029** DEFRA-2025 / `GB` factors |
| 2 | **20** SEAI-2025 / `IE` factors |
| 3 | **7,049** total `emission_factors` |
| 4 | **0** NULL `import_batch_id` |
| 5 | Correct provenance (provider identity, version, reporting year, source file, status) |
| 6 | Correct source checksums (computed from the workbook bytes, not hard-coded) |
| 7 | Exactly **one active completed batch per provider** in the final restored state |
| 8 | Idempotency verified (repeat `sync` inserts 0, updates all rows, keeps one active batch) |
| 9 | Target guard verified (writes refused unless the database is exactly `carbontally_demo_local`) |
| 10 | Reset / reseed verified (factor-scoped only; identities preserved) |
| 11 | Demo Lab identities preserved (4 organisations / 8 memberships / 13 `auth.users`) |
| 12 | Reference, QA and other databases unchanged |
| 13 | Live factor-selection path verified |
| 14 | Source workbook semantics verified |
| 15 | Authoritative GitHub commit verified |
| 16 | Working tree clean |
| 17 | **No DEMO-T2-C blocking findings** |

## 4. FINAL DEMO LAB STATE (accepted at closure)

| Domain | State |
|---|---|
| `factor_set='DEFRA-2025'` / `country='GB'` | **7,029** |
| `factor_set='SEAI-2025'` / `country='IE'` | **20** |
| Total `emission_factors` | **7,049** |
| Rows without `import_batch_id` | **0** |
| Active DEFRA batch (`2025 (V1)`, `completed`) | **1** |
| Active SEAI batch (`2025 (V1.7)`, `completed`) | **1** |
| `organizations` | **4** |
| `organization_members` | **8** |
| `auth.users` (lab) | **13** |
| `customer_factors` | **0** |

The Demo Lab factor load is confined to `carbontally_demo_local`; the investor/reference dataset
(`postgres`), `carbontally_test`, `carbontally_qa_phase8` and all `ct_*` clones were not written.
`emission_factors` remains client-inaccessible by design (RLS on, 0 policies) — factors are consumed
through the backend only.

## 5. SOURCE CHECKSUMS (verification targets; computed by the importers from the workbooks)

| Dataset | SHA-256 |
|---|---|
| DEFRA 2025 (DESNZ) — `tools/carbon_data_factory/factors/ghg-conversion-factors-2025-flat-format.xlsx` | `8bfdb45b81ec4a88e3bdf4584637330f62e6bd09ce1940e654c5d7b7f736de94` |
| SEAI 2025 (V1.7) — `tools/carbon_data_factory/factors/SEAI-conversion-and-emission-factors.xlsx` | `e64f4f91cf5546767d80fc2fe6be252946bcafedbd957d6b2981c9cf3f640e6d` |

## 6. DEFERRED OBSERVATIONS — RECORDED, NOT IMPLEMENTED (must NOT reopen DEMO-T2-C)

The following are **explicit deferred observations**, classified by the PO as **not DEMO-T2-C closure
blockers**. None of them was remediated by this decision, and none may be remediated without a new,
separately PO-gated task.

| ID | Observation | Classification |
|---|---|---|
| **`O-1`** | Concurrent provider imports can create **multiple active batches** because there is no database-level uniqueness/locking constraint. The seeder's serial execution is **process-local only**. | deferred — future DB invariant / advisory-lock item |
| **`O-2`** | `import_batches.rows_imported` carries **insert-count semantics** and can be `0` on a repeat `sync` while all factors remain linked to the new active batch. | deferred — provenance-metadata semantics |
| **`O-3`** | Existing **`load_to_db` positional-parameter** issue remains untouched. | deferred — importer interface item |
| **`R-1`** | `run_demo_lab.sh --backend --factors` has a **pre-existing backend readiness race**; the factor step itself independently passed. | deferred — demo-tooling robustness |
| **`R-2`** | `--dry-run` reports a guard failure but currently **exits 0**; the real seed hard guard still **fails closed**. | deferred — demo-tooling ergonomics |
| **`R-3`** | **No dedicated automated seeder test file** exists. | deferred — test coverage item |
| **`R-4`** | Existing **factor-selection ambiguity / semantic behaviour** remains unchanged. | deferred — factor-selection policy item (cf. `F-DA-1`…`F-DA-4`) |

**Consequences of the deferral (binding):**

1. `O-1`…`O-3` and `R-1`…`R-4` are **observations, not DEMO-T2-C defects**, and **must not be used to
   reopen DEMO-T2-C**.
2. No behaviour, code, test, schema or factor data was altered to address them.
3. Serialised provider imports remain an **operational requirement** for the Demo Lab seeder, and the
   `O-2` interpretation rule remains binding: linked-factor counts are read from `emission_factors`,
   never from `rows_imported`.
4. The target guard remains mandatory: Demo Lab writes only, never `postgres`, `carbontally_test`,
   `carbontally_qa_phase8`, `ct_*` clones, unnamed DSNs, or any production surface.

## 7. WHAT THIS DECISION DOES NOT AUTHORISE

* No application, backend, frontend, `src/`, migration, schema or RLS change.
* No change to `tools/demo_lab/seed_factors.py`, `run_demo_lab.sh`, `README.md` or any importer.
* No test additions or modifications (including **no seeder test file** — see `R-3`).
* No remediation of `O-1`, `O-2`, `O-3`, `R-1`, `R-2` or `R-4`.
* No change to factor-selection or unit semantics.
* **No customer factors, no scenarios, no activities, no documents, no calculations, no calculation
  snapshots, no reports, no review/clarification workflows.**
* No production or Render access, no deployment, no hosted-Supabase operation.
* **No automatic start of the next work item — DEMO-T3 and later are not authorised by this record.**

## 8. IMPACT STATEMENT

| Domain | Impact |
|---|---|
| Production | **NONE** — no production access, write, job, queue operation or deployment |
| Code / tests / config / schema / migrations | **UNCHANGED** by this task (documentation-only commit) |
| Factor data | **UNCHANGED** by this task — the Demo Lab datasets were loaded by the T2-C implementation and independently verified; this record adds, edits and deletes nothing |
| Database | **NO WRITES** — closure is a governance record only; no disposable records were created, so no cleanup was required |
| Git | This record is committed and pushed to `p8-release-reconciled` (fast-forward only); the working tree finishes **CLEAN** |

## 9. STATUS LINE

**DEMO-T2-C CLOSED** — IMPLEMENTED (`05de2f3`) · INDEPENDENTLY VERIFIED (OHD Task 078-C, **PASS**) ·
PO-CLOSED (2026-09-20). Deferred observations `O-1`…`O-3` and `R-1`…`R-4` recorded, **not implemented**.
DEMO-T3 **not started**.
