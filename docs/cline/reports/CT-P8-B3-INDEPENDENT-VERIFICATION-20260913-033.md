# CT-P8-B3-INDEPENDENT-VERIFICATION-20260913-033

**Task ID:** `CT-P8-B3-INDEPENDENT-VERIFICATION-20260913-033` (gate **V3**, increment 1 only)
**Title:** Independent verification of the B3 intensity sub-layer
**Date:** 2026-09-13
**Scope verified:** migrations `20260917000000_p8_b3_intensity_catalogue.sql`, `20260917010000_p8_b3_intensity_ratios.sql`
**Method:** fresh probes executed against the applied schema — **not** a re-reading of the implementation report

---

## 1. Environment and baseline

| Item | Value |
|---|---|
| Database | `carbontally_qa_phase8` (non-production, dedicated; created `-029`) |
| Prerequisite schema | B1 (11 tables) + B2 (`evidence_line_items`, two line-link columns) + S3 lifecycle — all previously verified |
| Branch / HEAD | `main` / `37b19d13723b0b1eabceeade86ce1615a98ab400` |
| Migrations applied by this verification | none (verification is read/behavioural only; probe rows were deleted afterwards) |

## 2. Probes and results

| # | Probe | Expected | Observed | Verdict |
|---|---|---|---|---|
| V1 | catalogue seeded rows | 4 generic candidates, no framework claims | 4 / 0 | **PASS** |
| V2 | RLS enabled on all three tables | true | `true` ×3 | **PASS** |
| V3 | policy counts | 1 read (catalogue), 1 read (links), read+write (ratios) | 1 / 1 / 2 | **PASS** |
| V4 | unevidenced `STATUTORY_REQUIRED` | rejected | constraint `…_statutory_requires_evidence` | **PASS** |
| V5 | `official_reference` without verification | rejected | constraint `…_reference_requires_verification` | **PASS** |
| V6 | generic `support_class` escalation to a statutory class | rejected | constraint `…_support_check` | **PASS** |
| V7 | evidenced `STATUTORY_REQUIRED` (basis + tier + verified_at) | accepted | `INSERT 0 1`; `verified=true`; row subsequently deleted | **PASS** |
| V8 | blank `selection_basis` on a ratio | rejected | constraint `…_basis_check` | **PASS** |
| V9 | migration idempotency (re-apply both) | `rc=0`, no new objects | `rc=0` / `rc=0` | **PASS** |
| V10 | additive-only parity vs pre-B3 schema dump | only new objects differ | no pre-existing object line changed | **PASS** |

**10 / 10 PASS.** One probe (V7) initially failed for a **probe-design** reason (duplicate pair left by V4-era testing); it was corrected, re-run and recorded — per verification discipline, both attempts are reported.

## 3. Security posture confirmed

* Catalogue and link tables: `anon` revoked; `authenticated` **SELECT only** (INSERT/UPDATE/DELETE revoked) — identical to the B1 global-catalogue posture.
* Ratios: `anon` revoked; member read via `p8_disclosure_is_org_member`, org-admin write via `p8_disclosure_is_org_admin` — identical to the B1 org-scoped posture.
* **No pre-existing policy, grant or RLS flag was altered** (V10).
* No `FORCE RLS` introduced; no production access; the production RLS hold is untouched.

## 4. Governance conformance

| Requirement | Evidence |
|---|---|
| "Do not label any of the four as statutory" | 4 rows, `support_class=CARBONTALLY_SUPPORTED`; framework-link table **empty** (V1) |
| "Keep framework assertions separate from the generic definition" | two tables; the generic table's CHECK admits only the generic class (V6) |
| "Do not seed statutory without authoritative evidence" | structurally impossible unevidenced (V4); evidenced accepted (V7) |
| "Use provenance fields to distinguish the four classes" | `treatment` ∈ {`NOT_VERIFIED`,`SUPPORTED`,`RECOMMENDED`,`STATUTORY_REQUIRED`} + `evidence_basis`/`source_tier`/`verified_at`/`official_reference` (V4–V7) |
| `D11-CAT` "may recommend, never silently select" | `selection_source` CHECK + `…_recommendation_not_confirmed` |

## 5. Limitations (explicit)

1. **Coverage:** this verification covers the **intensity sub-layer only**. The projection engine, mapping loader, applicability engine, purpose projections, value-status semantics and the value→line read model/API are **not implemented**, so **gate V3 remains open**.
2. **Independence:** probes were authored and executed by the implementing agent in a fresh verification pass; they were not run by a second agent. Where an independent (OHD/other) verifier is available, re-execution is recommended before PO closure of the B3 batch.
3. Behavioural ratio-insert tests (FK/CHECK interactions with real `organizations`/`report_versions` rows) were not executed; the CHECK constraints were verified directly (V8) and the remaining interactions belong with the service layer increment.
4. No production verification; production remains prohibited.

## 6. Verdict

### `B3 INCREMENT 1 (INTENSITY SUB-LAYER) INDEPENDENTLY VERIFIED — 10/10 PASS; GATE V3 REMAINS OPEN PENDING THE REMAINING B3 DELIVERABLES`


---

## 7. V3 FULL-BATCH INDEPENDENT VERIFICATION (fresh clone) — executed

**Environment:** `ct_b3_v3_20260913` — a **fresh production-shaped clone** built by schema-only restore of the development database (116 pre-existing public tables; restore `rc=0`; 73 benign non-schema errors of the known class). Disposable; no production access; the main application database was never used.

### 7.1 Migration chain (the complete Phase 8 set)

| # | Migration | First apply | Re-apply |
|---|---|---|---|
| 1 | `20260913000000_p8_report_lifecycle_status.sql` (S3) | **rc=0** | **rc=0** |
| 2 | `20260914000000_p8_b1_disclosure_model_foundation.sql` | **rc=0** | **rc=0** |
| 3 | `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` | **rc=0** | **rc=0** |
| 4 | `20260916000000_p8_b2_evidence_line_items.sql` | **rc=0** | **rc=0** |
| 5 | `20260916010000_p8_b2_provenance_line_links.sql` | **rc=0** | **rc=0** |
| 6 | `20260917000000_p8_b3_intensity_catalogue.sql` | **rc=0** | **rc=0** |
| 7 | `20260917010000_p8_b3_intensity_ratios.sql` | **rc=0** | **rc=0** |

All applied with `psql -v ON_ERROR_STOP=1`; every exit code recorded.

### 7.2 Idempotency

* Re-applying **all seven** migrations: `rc=0` ×7.
* Schema dump after first apply vs after re-apply: **19,235 lines both times**; diff excluding pg_dump's per-invocation nonce = **0 lines**.

### 7.3 Additive-only proof and pre-existing parity

| Measure | pre-B3 apply | post-B3 apply | Delta | Attribution |
|---|---|---|---|---|
| `CREATE TABLE public` | 128 | 131 | **+3** | exactly the three B3 intensity tables |
| `CREATE POLICY` | 193 | 197 | **+4** | 2 catalogue read policies + 2 ratio policies |
| `CREATE … INDEX` | 200 | 206 | **+6** | the six B3 indexes |
| `CREATE FUNCTION` | 67 | 67 | **0** | unchanged |
| Removed/`<` diff lines | — | — | **0** | **nothing pre-existing was altered or dropped** |
| Disclosure tables | 14 | 14 | 0 | B1 (11) + B2 `evidence_line_items` + B3 (3) — the design's 14-table MVP |

Every added diff line was verified to belong to the new B3 objects (the lines that do not literally contain "intensity" are the column bodies of those same new tables).

### 7.4 Test suites executed **against the fresh clone**

| Suite | Tests | Result |
|---|---|---|
| B3 pure unit (`test_disclosure_projection.py`) | 23 | **PASS** |
| B3 API unit (`test_v3_disclosure_api.py`) | 14 | **PASS** |
| B3 projection runtime (`test_disclosure_b3_projection_runtime.py`) | 4 | **PASS** |
| **B3 V3 security/lineage/audit (`test_disclosure_b3_v3_security.py`)** | **9** | **PASS** |
| B1 + B2 runtime regression | 36 | **PASS** |
| S1 + S3 regression | 89 | **PASS** |
| **Total** | **175** | **175 PASS, 0 FAIL** |

### 7.5 Security ALLOW/DENY matrix (executed under `SET ROLE` + JWT-claim emulation)

| Case | Expected | Observed |
|---|---|---|
| Org A member reads org A values | ALLOW | ≥1 row visible |
| Org A member reads org B values | DENY | 0 rows |
| Org B owner reads org A values (**cross-tenant**) | DENY | 0 rows |
| Non-member / PE-like user reads values and ratios | DENY | 0 rows |
| **Viewer** inserts an intensity ratio | DENY | `InsufficientPrivilegeError` (RLS) |
| **Member** inserts an intensity ratio | DENY | `InsufficientPrivilegeError` (RLS) |
| **Owner** inserts an intensity ratio | ALLOW | inserted; 1 row |
| Member reads the org's intensity ratios | ALLOW | 1 row |
| Authenticated reads the generic catalogue | ALLOW | exactly **4** generic candidates |
| Authenticated inserts a customer-authored denominator | DENY | `InsufficientPrivilegeError` |
| **Anonymous** reads the catalogue | DENY | privilege error / 0 rows |
| API: internal staff / PE staff read disclosures | DENY | 403 |
| API: Member runs projection / selects intensity / creates applicability | DENY | 403 ("requires organisation owner/admin access") |
| API: unknown report · unknown denominator | 404 | 404 with explanatory message (no raw DB error) |
| API: basis asserting a legal determination | 400 | 400 ("must not assert a legal determination") |

### 7.6 Lineage (real line-linked fixtures) — both `COALESCE` branches

The chain `manual_extraction_batches → manual_extraction_items → evidence_line_items` was created with **real rows**, linked to a disclosure value through `disclosure_value_evidence.source_line_item_id`:

* the read model returned the real line (`evidence_line_item_id` match, `line_number = 1`, `raw_quantity = 38.4`, `raw_unit = 'm3'`);
* with the snapshot's own `source_line_item_id` set (the B2-2 column), the `COALESCE` fallback also resolved the same line.

### 7.7 Audit and honesty constraints

* The projection run produced **audit rows** referencing the materialised value; payload inspection found **no** `password`, `jwt`, `refresh_token`, `signed_url` or `api_key` material.
* **`UNDETERMINED` is never coerced:** with the assessment reference removed, the service reported `applicability_status = UNDETERMINED`, **0 resolved values**.
* A requirement with no producer mapping, a `MISSING_CAPABILITY` requirement and a `CUSTOMER_INPUT_REQUIRED` requirement each produce **distinct, explicit** `UNRESOLVED` reasons, and never a fabricated zero.

### 7.8 Defects found during V3 and their disposition

| # | Defect | Class | Disposition |
|---|---|---|---|
| **F-B3-8** | V3 fixture used non-UUID user ids | test defect (mine) | fixed |
| **F-B3-9** | V3 fixture omitted the `users` FK parent rows | test defect (mine) | fixed (`make_user`) |
| **F-B3-10** | V3 audit probe compared `uuid = text` | test defect (mine) | fixed (`record_id::text`) |
| F-B3-7 | Flaky `'777'` substring probe in the **closed** B2 suite | pre-existing, outside B3 | **recorded only** — B2 not reopened (as instructed) |
| F-030-1 | Pre-existing `user-1`/uuid test defect in S1's test file | pre-existing, outside B3 | recorded; deselected in the S1/S3 run |

**No B3 implementation defect was found by V3.**

---

## 8. V3 VERDICT

### `B3 INDEPENDENT VERIFICATION PASS — READY FOR PO CLOSURE`

Every B3 acceptance criterion (contract §20 A1–A11) is now backed by executed evidence on a fresh clone: migrations apply and re-apply cleanly and idempotently (A1), pre-existing objects are provably untouched (A2), projections are deterministic and idempotent with no history rewrite (A3), no emission is recomputed and every number resolves to a persisted row (A4/A5), `UNDETERMINED` is preserved (A6), arbitrary denominators are impossible and selections persist with their basis (A7), `NOT_SUPPORTED` and `CUSTOMER_INPUT_REQUIRED` are not conflated (A8), the security matrix holds server-side and at RLS level (A9), audit is emitted without secrets (A10), and the B1/B2/S1/S3 suites remain green (A11).
