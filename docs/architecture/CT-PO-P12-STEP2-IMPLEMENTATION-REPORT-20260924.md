# CT-PO-P12-STEP2-IMPLEMENTATION-REPORT-20260924

**Reference:** `CT-PO-P12-STEP2-IMPLEMENTATION-REPORT-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924` — **STEP 2 — Canonical Demo Environment**
**Repository:** `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`
**Production deployment:** **NOT AUTHORIZED**

---

## 1. Executive summary

Step 2 created **one controlled, reproducible canonical investor-demo environment**
and populated it with **real records produced through the real CarbonTally
pipelines**.

The single most important outcome: **the Step-1 EV-01 gap is closed through the real
pipeline, with no fabrication.** A genuinely tabular CSV was processed by the real
worker; the existing producers emitted `extracted_data.line_items[]`; the existing
forward hook materialised **2 `evidence_line_items`**; the calculation step populated
`calculation_snapshots.source_line_item_id`; and the **Source Evidence Viewer
resolves the chain over the real API (HTTP 200, FULL drill-down)**.

**Step 2 is nevertheless `INCOMPLETE`**, because two mandatory exit criteria are not
evidenced: the **disposable-clone integration verification was not executed**, and
**reset/reprovision repeatability was demonstrated only once**. One data target also
failed (**processing entities 1 of 2**).

## 2. Authorization compliance

| Rule | Compliance |
| --- | --- |
| No production mutation | **complied** — nothing outside `127.0.0.1` was touched |
| `postgres` flagship not mutated | **complied** — 975 orgs before and after |
| `carbontally_qa_phase8` / `carbontally_test` not reset | **complied** — 25 orgs / 717 users before and after |
| RLS not weakened | **complied** — 141/141 tables RLS-enabled, 298 policies, D-4 containment intact |
| Authorization not bypassed | **complied** — every seed used a real actor token via the real API |
| No fabricated evidence | **complied** — evidence lines came from the forward hook on a real CSV |
| No direct `evidence_line_items` insert | **complied** |
| `derive_line_candidates` not modified | **complied** — not touched |
| P1 rollout not enabled | **complied** — `CARBONTALLY_P1_EXTRACTION_SHAPE` untouched (still `shadow`) |
| No fabricated report states / Insight answers / calculations | **complied** — all states came from real API transitions |
| Generator not modified | **complied** — HEAD still `8ade2bf…`, no changes staged |
| Destructive integration tests not aimed at the Demo Lab | **complied** — none were run at all |
| Frozen scope not silently changed | **complied** — deviations are recorded in §7 |
| Documentation conflicts not silently resolved | **complied** — dispositions recorded in §6 |
| Step 3 not started | **complied** — no UI/presentation work |

## 3. What was built

1. **Environment**: `carbontally_demo_local` re-provisioned from the current release
   migration set — **81 migrations, 0 errors**, 141 public tables, **6 Insight
   tables**, B2 evidence schema, storage substrate (4 D32 policies, 2 private
   buckets), auth bootstrap.
2. **Generator**: pinned checkout verified (`HEAD == 8ade2bf…`).
3. **Identities**: 4 organisations (2 direct, 2 client), 1 consultant firm, 1
   processing entity, 13 users (8 members, 3 staff profiles).
4. **Factor data**: 7,049 active factors (DEFRA-2025, SEAI-2025).
5. **Document corpus**: 10 PDFs (real T3 corpus, pinned provenance) + **1 tabular
   CSV** uploaded through the real API.
6. **Story A**: **2 matched calculations** from the current HEAD, including the exact
   Step-1 value `2469.169780 kg CO₂e`.
7. **Story C**: 2 evidence lines, populated line links, Viewer resolution 200.
8. **Story D**: **10 blocked documents** with real persisted reasons across 5 classes
   (ambiguous, no-match, clarification, completeness, validation-missing-field).
9. **Story B**: **7 assignment rows** (4 open / 3 closed) with assign → claim →
   release → reassign exercised; 4 conversations (3 org + 1 PE) with 2 messages.
10. **Reporting**: 2 report versions in **different lifecycle states** (`APPROVED`,
    `DRAFT`) produced by real API transitions.
11. **Master data**: 1 facility, 1 asset (linked), 1 supplier via real CRUD.
12. **Insight**: 6 tables live; **10-tool closed catalogue** confirmed; 3 executions
    (`success`, **`no_data`**, `success`); 1 conversation + 2 persisted messages.
13. **Security**: `verify.py` **13/13 contexts, 30/30 probes, 18/18 isolation rules,
    0 failures**; `F-T1-001` no longer reproduces.

## 4. Five harness defects found and fixed (demo-lab tooling only)

| ID | Defect (evidence) | Fix | Product impact |
| --- | --- | --- | --- |
| **D-2-02** | `stack.py` ordering: storage substrate before migrations (`RuntimeError: storage schema clone errors: ['ERROR: relation "public.organization_members" does not exist']`, then `expected 4 D32 policies, found 0`); `auth` bootstrap after migrations (cascade `schema "auth" does not exist`, `function public.is_org_member(uuid) does not exist`) | re-sequenced the harness's own functions: auth → migrations → storage → grants → containers | none |
| **D-2-06** | `auth.users` never created on a fresh DB → 13 × `FAILURE auth_user_mirror: relation "auth.users" does not exist`, every membership/profile failing on FK | added `_clone_auth_schema_structure()` (structure-only `pg_dump`, the same mechanism `storage.py` uses) | none |
| **D-2-05** | JWKS fallback URL missing the GoTrue prefix → `HTTP Error 404: Not Found`, blocking a cold start of the storage container | corrected to `/auth/v1/.well-known/jwks.json` | none |
| **D-2-03** | `run_demo_lab.sh --backend --factors` starts the backend before factors load; the worker builds its `FactorSearchIndex` at `start()` → **all 10 documents mapped `no_match`, 0 calculations** on the first seed | operational: restart the backend **after** the factor load — the re-run produced realistic mapping outcomes | none |
| **D-2-04** | `t3_scenarios._multipart` hardcodes `Content-Type: application/pdf` → the CSV was stored `file_type=PDF`, `mime=application/pdf`, routed to the PDF extractor (`extraction no_text`) | the tabular seeder sends `text/csv` | none |

All five were **harness/operational**, not product defects. No application file was
modified.

## 5. Exit-criteria checklist

```text
[x] canonical Demo Lab identity proven
[x] current authorized release migrations applied            (81 files, 0 errors)
[x] Insight schema present                                   (6 tables)
[x] B2 evidence schema present                               (evidence_line_items + source_line_item_id)
[x] pinned generator restored and verified                   (HEAD == 8ade2bf…)
[x] frozen seed manifest recorded
[x] identity topology populated                              (4 orgs, 13 users, 8 members, 3 staff)
[x] organisation relationships populated                     (2 consultant↔client grants)
[ ] PE topology populated                                    FAIL — 1 of 2 entities
[x] >=2 successful matched calculations                      (2, current HEAD)
[x] >=2 genuine blocked documents                            (10, real persisted reasons)
[x] >=1 genuine CSV/XLSX processed                           (1 SPREADSHEET)
[x] >=2 evidence_line_items through the real pipeline        (2, FORWARD/csv)
[x] calculation snapshot links to evidence line              (2 of 2 resolvable)
[x] Source Evidence Viewer resolves real evidence            (HTTP 200, FULL)
[x] >=4 assignments                                          (7)
[~] >=1 reassignment                                         exercised (200); reassignment_history empty
[~] >=1 partial release                                      release exercised (200, row closed)
[x] meaningful workflow states populated
[x] both messaging planes populated                          (3 org + 1 entity; 2 messages)
[x] report lifecycle variation populated                     (APPROVED + DRAFT)
[x] master data populated                                    (1 facility, 1 asset, 1 supplier)
[x] Insight operational against seeded data                  (10-tool registry; 3 executions)
[x] >=2 meaningful Insight interactions                      (aggregation success + snapshot lookup)
[x] >=1 honest no-data Insight case                          (status=no_data)
[~] security DENY scenarios prepared/verified               30 probes + 18 isolation rules; S-4 blocked
[x] honest failure scenarios present                         (5 classes, 10 documents)
[x] Demo Lab verification harness executed                   (13/13, 30/30, 18/18)
[ ] disposable integration verification executed             FAIL — not executed
[ ] reset/reprovision repeatability demonstrated              PARTIAL — one cycle
[x] environment provenance recorded
[x] documentation conflict dispositions recorded             (section 6)
[x] no unauthorized product changes                          (tools/demo_lab + docs only)
[x] no production mutation
```

## 6. Documentation-conflict dispositions (D-2-9)

| ID | Conflict | Authoritative source | Decision | Action | Remaining limitation |
| --- | --- | --- | --- | --- | --- |
| **D-09** | `v3_messaging.py` docstring says PE staff "never get messaging access" while the same module implements the PE operational plane | the **running code** (verified live: 201 created by `pe_manager`) | record the docstring as wrong; do **not** change product code in Step 2 | documented only | docstring remains misleading until a separately authorized docs fix |
| **D-10** | X2/X7 contracts say "IMPLEMENTATION BLOCKED / PO DECISION REQUIRED" while implementation + wiring + tests exist | release **source** | **PO decision required** | none | contract text stays stale |
| **D-11** | `AGENTS.md` §54 documents a 1,185-identity dataset that does not exist (real manifest: 13 actors) | repository + live counts | **PO decision required** | none | `AGENTS.md` §54 remains inconsistent |
| **D-12** | No single authoritative T3 status record; OHD-079 FAIL with no re-verification record | tooling + live evidence | recorded; Step-2 re-ran the harness | `verify.py` re-run recorded; the first seed was re-run after the D-2-03 fix | T3 REM-001 status text not rewritten |
| **D-14** | Release-identity ambiguity (working tree vs stale local `origin`) | `github` remote | frozen release = `35eb7ba` (Step-1 final, GitHub-aligned) | recorded in every Step-2 artifact | the local-path `origin` stays stale |
| **D-27** | Governing PO artifacts untracked | repository | **PO decision required** (§7) | **no untracked PO artifact was committed** | durability risk persists |

## 7. PO artifact durability (D-2-10)

Reviewed and **left untracked, unmodified**:
`CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924.md`, `carbontally_handoff.md`, the Insight
architecture references, the Question Library, the INS-01 reconciliation, the PO
Insight Capability Decision Matrix, `.costrict/`, `costrict-*.txt`, stray `8` and `=`.

Classification: governing project record (workplan, handoff, INS-01 reconciliation,
PO matrices, Insight references, Question Library) vs working artifact
(`.costrict/`, stray files). Committing them is a **PO decision Step 2 does not
hold**; they remain uncommitted.

## 8. Defects

| Class | Findings |
| --- | --- |
| **Pre-existing (unchanged)** | 4 stale unit-test expectations (Step-1 baseline); X2/X7 contract staleness (D-10); `AGENTS.md` §54 dataset absence (D-11); untracked PO artifacts (D-27); stale local `origin` (D-14) |
| **Newly discovered** | 5 demo-lab harness defects, all **fixed** (D-2-02…D-2-06); `emission_factors` D-4 containment means an RLS-bound role sees zero factors (fail-closed by design, verified not to affect the app role); the corpus `uk-water` scenario maps `no_match` although the contract expects `EXPECTED_MATCHED` |
| **Environment-only** | Only 1 processing entity; no staff role granting `can_manage_staff` (support counterparty 409); `reassignment_history` unpopulated; `carbontally_insight_interactions` unpopulated by the tool-invoke route |
| **Documentation** | D-09, D-10, D-11, D-12, D-14, D-27 — dispositions recorded in §6; none silently resolved |
| **Product/code** | **None identified.** No Step-2 result required a product change; `F-T1-001` no longer reproduces |

## 9. Tests executed

| Suite | Result |
| --- | --- |
| `tools/demo_lab/verify.py` (canonical environment) | **13/13** contexts, **30/30** probes, **18/18** isolation rules, `known_product_defects: []` |
| Seed verification (`seed_factors.py`) | `ALL CHECKS OK` — 7,029 + 20 = 7,049 factors, all linked, 2 active batches, serial order preserved |
| `t3_scenarios.py seed` | exit 0; 11 real uploads, 10 honest blocks, no false successes |
| Tabular seeder | 2 calculations + 2 evidence lines + 2 link resolutions |
| Story-B / messaging / reports / master data / Insight API seeders | all HTTP 200/201 (see the Frozen Seed Manifest) |
| Unit suite | **not re-run** — no product code changed; the Step-1 baseline (3,220 tests, 4 pre-existing failures, 8 skipped) is unchanged by Step 2 |
| Integration suite | **NOT RUN** — see `CT-PO-P12-STEP2-DISPOSABLE-INTEGRATION-VERIFICATION-20260924.md` |
| No test was modified | **confirmed** |

## 10. Artifacts produced

New Step-2 documents (all in `docs/architecture/`):

```text
CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md
CT-PO-P12-STEP2-FROZEN-SEED-MANIFEST-20260924.md
CT-PO-P12-STEP2-RESET-REPROVISION-PROCEDURE-20260924.md
CT-PO-P12-STEP2-EXPECTED-COUNT-VERIFICATION-20260924.md
CT-PO-P12-STEP2-ENVIRONMENT-PROVENANCE-20260924.md
CT-PO-P12-STEP2-IMPLEMENTATION-REPORT-20260924.md      (this file)
CT-PO-P12-STEP2-DISPOSABLE-INTEGRATION-VERIFICATION-20260924.md
```

Step-2 tooling changes (demo-lab only):

```text
tools/demo_lab/stack.py     (ordering fix D-2-02 + auth-structure clone D-2-06)
tools/demo_lab/storage.py   (JWKS path fix D-2-05)
```

Runtime evidence (outside the repository, never committed):
`<state>/evidence/{verify_20260924T085608Z,t2c_seed_20260924T085615Z,t3_scenarios_latest}.json`,
`p12_step2_{tabular_seed,story_b,retries,completion,closeout,final}.json`,
`<state>/corpus/p12-step2-tabular/{csv,corpus_provenance.json}`, `/tmp/s2_pre_reset_manifest.json`.

## 11. Remaining work (before Step 3)

1. **Disposable-clone integration verification** (mandatory, outstanding).
2. **A second full reset → reprovision cycle** to evidence repeatability.
3. Provision a **second processing entity** (S-4) and an internal staff role granting
   `can_manage_staff` (support-messaging beat).
4. Fold the **backend-restart ordering** (D-2-03) and the **`text/csv` content type**
   (D-2-04) into the harness itself rather than the operational procedure.
5. Decide the PO items in §6 (D-10, D-11, D-27) and the `reassignment_history` /
   Insight-interaction delivery questions.

## 12. Final status

```text
STEP 2 INCOMPLETE
```

Rationale: the canonical environment, schema, pinned generator, frozen seed,
Stories A–D (including the end-to-end evidence chain through the real pipeline),
Story B, messaging, reporting, master data, Insight and the security verification
are **all evidenced**. However two mandatory exit criteria are unmet —
**disposable-clone integration verification (not executed)** and
**reset/reprovision repeatability (one cycle only)** — and one data target failed
(**processing entities 1 of 2**).

**Not claimed:** `INVESTOR DEMO READY` (that is the Step-4 gate). **Step 3 has not
been started.**



