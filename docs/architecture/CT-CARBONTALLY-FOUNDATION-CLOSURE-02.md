# CT-CARBONTALLY-FOUNDATION-CLOSURE-02

**Task:** reconcile the historical CarbonTally foundation reports (`CT-CARBONTALLY-FOUNDATION-BASELINE-01`,
`-INVENTORY-02`, `-VERIFICATION-03`, `-DOCS-INTENT-04`, `-CODE-REVIEW-05`) against the **current**
repository, runtime, database and test state; implement the findings that survive re-verification;
run focused and full suites; and record what is implemented, tested, verified and still open.

**Date:** 2026-10-09 (all times +06 unless stated)
**Branch:** `p8-release-reconciled`
**Agent:** Cline (implementation + reconciliation)
**Classification:** `COMPLETE_WITH_OBSERVATIONS` — no acceptance is claimed (AGENTS §73/§74)

---

## 0. Provenance rule

The Phase-2 rule is retained verbatim, because it is the reason this pass exists:

> `SOURCE STATE` (this git checkout) ≠ `RUNTIME STATE` (running processes) ≠
> `DATABASE STATE` (local databases) ≠ `TEST STATE` ≠ `DOCUMENTED STATE` (repo docs).
> Where they disagree, the disagreement is reported and **not** reconciled by choosing one.

Every claim below is tagged with the state it was measured in. Historical reports are used as
**regression targets and investigation hints**, never as current evidence (AGENTS §80).

---

## 1. Current verified state (measured this pass)

### 1.1 Source / Git

| Item | Value | Evidence |
|---|---|---|
| Branch | `p8-release-reconciled` | `git branch --show-current` |
| HEAD | `8ac778ed5ac29c9b565770824fbbef60e0418558` — `fix(db): revoke client-role privileges on CT03 request tables (F-1 closure)` | `git rev-parse HEAD`, `git log -1` |
| GitHub branch tip | `f3df392933a17b4d690de91a12f5f92195db2a7d` (`refs/heads/p8-release-reconciled`) | `git ls-remote github p8-release-reconciled` (exit 0) |
| Divergence vs **GitHub** | **local is 1 commit ahead** (the F-1 closure commit only) | comparison of the two SHAs above |
| Divergence vs **local-path remote** `origin` = `/tmp/ct_step2` | local is 232 ahead | artefact of a local-path remote; *not* a GitHub figure |
| Tracked-modified files | 8 = 6 task files + `.gitignore`, `frontend/App_.js` (both pre-existing, unrelated) | `git status --porcelain` |
| `.env` tracking | `.gitignore:83` → `.env*`; only tracked env file is `tools/demo_lab/backend.env.example` | `git check-ignore -v backend/.env` |

### 1.2 Runtime

| Item | Value | Evidence |
|---|---|---|
| API process | `uvicorn main:app --host 127.0.0.1 --port 8070`, cwd `<repo>/backend`, Python 3.14 venv | `/proc/<pid>/cmdline`, `/proc/<pid>/cwd` |
| API env (non-secret) | `SUPABASE_URL=http://127.0.0.1:54430` | `/proc/<pid>/environ` (filtered; no secret values copied) |
| API endpoints | `/openapi.json` 200, `/docs` 200, `/health` 200, `/api/health` **404** | `curl -o /dev/null -w '%{http_code}'` |
| OpenAPI contract | title `CarbonTally API`, version `3.0.0`, **654 paths** | live `/openapi.json` |
| Frontend dev server | `:3000` → 200 | `curl` |
| Local Supabase stacks | `supabase_kong_carbon_ledger :54425`, `supabase_db_carbon_ledger :54426`/`5432`, `carbontally_demo_lab_gateway :54430` | `docker ps` |

### 1.3 Database — three local generations (B-05, B-09)

All three databases live in the **same** Postgres cluster
(`supabase_db_carbon_ledger`, `postgres:17.6.1.147`); they are *not* interchangeable.

| Measure | `carbontally_demo_local` | `postgres` | `ct_local_93d5cdd` |
|---|---:|---:|---:|
| public tables | **154** | 116 | 135 |
| RLS policies | **355** | 174 | 218 |
| RLS-enabled tables | 154 | 116 | — |
| organisations | 14 | **975** | 25 |
| `public.users` | 23 | 1,352 | 658 |
| `auth.users` | 22 | **1,214** | *no `auth` schema* |
| `emission_factors` rows | 7,049 | 7,049 | **0** |
| CT-03 request tables present | **4/4** | 0/4 | 0/4 |
| migration ledger | **none** | 46 rows, tip `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | **none** |
| storage buckets | `report-artifacts`, `documents` | *(none listed)* | — |
| served to the running API | **YES** | no | no |

**Which database the running application actually uses (PD-4 evidence).**
The API's `SUPABASE_URL=http://127.0.0.1:54430` resolves to `carbontally_demo_lab_gateway`
(nginx) → `carbontally_demo_lab_postgrest`, whose `PGRST_DB_URI` names database
**`carbontally_demo_local`** (value masked; host `supabase_db_carbon_ledger:5432`). Therefore:

* the **live local runtime DB is `carbontally_demo_local`** (154 tables, 14 orgs, 22 auth users);
* the **1,185-identity investor demo population lives in `postgres`** (975 orgs / 1,214 auth users),
  which the running local application **does not** serve; and
* `ct_local_93d5cdd` (repo-named, 135 tables, no `auth` schema, 0 factors) is a third, scratch
  generation that must not be quoted as "the database".

This corrects B-12 and the AGENTS §§54–56 expectation: population-scale isolation testing is
*possible locally*, but only against `postgres`, and only by re-pointing the demo-lab topology —
a PO/topology decision (PD-4 / PD-B).

### 1.4 Applied-state divergence: F-1 is live but **not** local (new, B-21)

Effective ACLs on the CT-03 consultant request tables:

| Environment | `anon` | `authenticated` |
|---|---|---|
| live Supabase project (demo) | `NONE` | `NONE` ✅ F-1 applied |
| local runtime `carbontally_demo_local` | `r` (SELECT) | `a,r,w,d` (INSERT/SELECT/UPDATE/DELETE) ❌ F-1 **not** applied |

The F-1 migration
(`supabase/migrations/20261105000000_ct_consultant_model_03_request_tables_revoke_client_roles.sql`)
is committed and the live project carries its effect, but the **local runtime database still grants
client-role privileges** on `consultant_mode_change_requests` and
`consultant_relationship_requests`. In line with the read-only discipline of this task **no
migration was applied to any local database to make the environments agree.** Recorded as **B-21**
(P2, local environment) with a PD-4 dependency.


**B-07 closed by measurement:** the "232 ahead" figure quoted in an earlier scoped note was measured
against the *local-path* remote, not GitHub. Against GitHub the branch is **one** commit ahead, and

### 1.5 Test state (exact)

| Suite | Result | Evidence |
|---|---|---|
| Backend focused — 5 files: F-1 migration pin, I-02 supplier ceiling, p17 supplier write path, extraction-suggestions, invoice-extraction | **RC=0 — 127 tests, 0 failures** | `/tmp/c2_focused2.txt` |
| Backend full unit suite | **5,360 passed, 1 failed, 8 skipped**, 14 warnings, 640.54 s | `/tmp/c2_unit_full.txt` |
| Backend single failure | `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` — pre-existing, environment-coupled (§1.6) | `/tmp/c2_disc.txt`, `/tmp/c2_disc_iso.txt` |
| Frontend full Jest suite | **629 passed, 1 failed** (630 total), 58/59 suites passed, 19.8 s | `/tmp/c2_suites.txt` |
| Frontend single failure | `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` — pre-existing, unrelated (§1.7) | `/tmp/c2_fe_focus2.txt` |
| Frontend focused (new I-03 test + dr007) | `processing-upload-capability.test.jsx` **PASS**; dr007 **FAIL**; 1 failed / 4 passed of 5 | `/tmp/c2_fe_focus2.txt` |
| Live demo read-only probe | ledger 104 rows, tip `20261105000000`; 154 tables / 424 indexes / 231 policies / 151 RLS-enabled; CT-03 client grants `NONE`; `documents` bucket 59 objects | `/tmp/c2_live_state.txt` |

### 1.6 Classification of the one backend failure (pre-existing, not mine)

`test_create_request_as_admin` asserts `body["verification_delivered"] is False` (test comment:
*"Email delivery is NOT configured in unit tests — reported honestly"*, test file line 112 —
**unmodified at HEAD**). The route (`backend/api/v3_discovery.py:369`) calls
`send_transactional_email(..., settings_repo=repos.settings)` (`backend/services/v3_email.py:79`),
which resolves the **delivery provider from persisted platform settings**. In this developer
environment those settings resolve to a Resend-configured provider because `backend/.env` carries
`RESEND_API_KEY`; hence `delivered=True`.

Non-attribution evidence: the failure reproduces **in isolation**
(`pytest tests/unit/api/test_v3_discovery.py -k test_create_request_as_admin` → same assertion), and
neither changed backend file (`api/v3_suppliers.py`, `engines/invoice_extraction.py`) appears in the
route's import path. **Not introduced by this task; not fixed here** (a fix is a test-design
decision: guard the assertion on configured-provider state, or inject a provider double).

### 1.7 Classification of the one frontend failure (pre-existing, not mine)

`dr007-investor-display-fixes.test.jsx` → *"Issue 3 — customer review detail shows Mapped activity
from mapped_data.activity"* fails at line 107 (`row.textContent).toContain('Natural gas')`).
Non-attribution evidence:

* the test renders `src/v3/customer/ReviewDetailPage.jsx` and `ProcessingItemWorkspace.jsx`;
* the I-03 change is confined to `src/v3/customer/ProcessingPage.jsx`;
* neither component imports `ProcessingPage` (`grep` → no match), and the test file plus both
  components are **unmodified at HEAD** (`git status --porcelain` empty for all three).

⇒ the module graphs are disjoint; this is a genuine pre-existing `ReviewDetailPage` display defect
(mapped-activity fallback), **out of scope** for this closure, recorded as **B-22** (P3).

that commit is the intended F-1 closure.

---

## 2. Finding-by-finding reconciliation (B register)

Status vocabulary: **RESOLVED** (implemented + tested this pass), **SUPERSEDED** (the finding no
longer describes current state, with the measurement that supersedes it), **CONFIRMED-CURRENT**
(re-verified as still true), **OPEN** (still true, no decision or work authorised), **INFO**
(registered, not judged).

| ID | Historical claim | Status 2026-10-09 | Current evidence |
|---|---|---|---|
| **B-01** | Unit baseline RED: 7 failures / 2,537 collected (4 migration-order pins + 3 extraction-suggestion drifts) | **RESOLVED (superseded by measurement)** | Full suite now **5,360 passed / 1 failed / 8 skipped**; the 4 migration pins + 3 extraction-suggestion tests pass. The single remaining failure is a *different*, environment-coupled test (§1.6). Frontend 629/630. |
| **B-02** | Invoice table parser rejects real invoice forms: header anchored on literal `description`; rows accept only `[£$€]`, not ISO codes | **RESOLVED** | `backend/engines/invoice_extraction.py`: header now accepts `Item` / `Item Description` / `Description` / `Details`; `_CURRENCY_PREFIX` accepts ISO codes + symbols. Parity fixture 0 → **3** rows; corpus `output_all_variations` 51 → **217** files extracting (**166 gained, 0 lost**). Regression tests added. |
| **B-03** | Units vocabulary gap: `canonical_unit("units")` is `None` | **PINNED (deliberately not changed)** | New test `test_count_token_units_is_not_a_physical_unit` asserts `canonical_unit("units"/"unit"/"each"/"GBP") is None`. `"GBP" → None` is correct and must not be "fixed" (AGENTS §23); any widening requires the PD-C decision. |
| **B-04** | Runtime config drift: repo `backend/.env` (`PORT=8060`, `SUPABASE_URL=http://127.0.0.1:19999`) does not describe the running stack | **CONFIRMED-CURRENT (re-measured)** | `.env` still carries `PORT=8060` and `SUPABASE_URL=http://127.0.0.1:19999`, plus **duplicate** `REACT_APP_API_URL` keys (8060 then 8000). Neither 8060 nor 19999 is listening (`curl` → 000). Runtime serves `:8070` with `SUPABASE_URL=:54430` → `carbontally_demo_local`. `.env` is untracked/ignored ⇒ local-environment issue, not a repo defect; remediation belongs to PD-4. |
| **B-05** | Two divergent local schema generations (154/355 vs 135/218), no ledger anywhere | **CONFIRMED-CURRENT (extended to three)** | §1.3: `carbontally_demo_local` 154/355; `ct_local_93d5cdd` 135/218 **no auth schema, 0 factors**; plus investor-demo generation `postgres` 116/174 with a 46-row ledger. Every statement about "the database" must name it (AGENTS §84). |
| **B-06** | Five migrations exist only as uncommitted files yet the runtime DB was provisioned from them | **SUPERSEDED (measurement) + inverse confirmed** | Those migrations are now **committed** (F-1 last; HEAD `8ac778e`). The inverse gap is confirmed instead: the **local runtime DB has not had the F-1 revocation applied** (§1.4, **B-21**) while the live project has. |
| **B-07** | Handover frozen SHA ≠ HEAD | **RESOLVED (superseded)** | §1.1: HEAD `8ac778e`; GitHub tip `f3df392` ⇒ 1 commit ahead; the older "232 ahead" figure was measured against the local-path remote. |
| **B-08** | Readiness-audit F-05 ("database business-empty") holds only for one DB | **CONFIRMED-CURRENT** | `ct_local_93d5cdd` is business-empty (0 factors); `carbontally_demo_local` is data-bearing (14 orgs); `postgres` is heavily data-bearing (975 orgs). Re-scope historical "empty DB" claims by database name. |
| **B-09** | Review/approval + QC lifecycle have no live data anywhere | **CONFIRMED-CURRENT (local) / UNVERIFIED (live)** | Not re-measured on the live project this pass; locally those tables remain empty in the runtime DB. Live-side counts are remaining work (§7). |
| **B-10** | API-unit (2,788), Jest (58 files), integration and e2e suites unmeasured | **RESOLVED for the two large suites** | Backend unit: 5,361 collected, 640 s. Frontend Jest: 630 tests / 59 suites, 19.8 s. **Integration and e2e suites remain unmeasured** (§7). |
| **B-11** | `AGENTS.md` §54 points at a non-existent `tools/seed_investor_demo/DEMO_IDENTITIES.md` | **CONFIRMED-CURRENT** | Path still absent; the manifest present is `tools/demo_lab/manifest.json`. AGENTS.md is the PO's constitution — reconciliation is a documentation (PO) action, not an agent edit. |
| **B-12** | Demo-identity model divergence (1,185 identities vs 4 orgs / 14 actors) | **CONFIRMED-CURRENT + CORRECTED** | §1.3: the 1,214-auth-user investor population demonstrably exists — in **`postgres`**, not in the runtime DB (`carbontally_demo_local`, 22 auth users). The §56 expectation is *achievable* but needs a topology decision (PD-4). |

| **B-13** | `customer_factors` empty in the runtime DB (also `roles`, `units`) | **CONFIRMED-CURRENT (local)** | Not contradicted by anything measured this pass; customer-factor precedence (AGENTS §15/§16) still has no local live data to demonstrate. |
| **B-14** | Two `mapping_options` implementations coexist | **INFO (unchanged)** | Not re-assessed this pass; no work authorised. |
| **B-15** | Live OpenAPI still exposes legacy `v2`/unprefixed routes | **INFO (narrowed)** | Live contract 654 paths vs 781 source operations (INVENTORY-02); legacy coexistence unchanged, reachability still unassessed. |
| **B-16** | 154 vs 141 Demo-Lab table-count discrepancy | **RESOLVED (already, CODE-REVIEW-05)** | Mechanism = dated snapshots of a growing schema; current count is **154**, measured, dated and database-named (§1.3). |
| **B-17** | `edit_master_data` ceiling on facilities/assets/vehicles but not suppliers (F-03); messaging-send and customer-factor write ceilings (F-04/F-05) | **PARTIALLY RESOLVED** | **Suppliers RESOLVED** (I-02, §3). Messaging-send (F-04) and customer-factor create/update (F-05) remain **OPEN** — new-ceiling product decisions (F-06 ⇒ PO DECISION REQUIRED). |
| **B-18** | Four migration-order pins stale/red (F-02) | **RESOLVED (superseded)** | All four now pass in the full suite (§1.5); a future red would be a genuine ordering break — exactly what the pins exist to detect. |
| **B-19** | `frontend/App_.js` tracked-modified, 41,982 bytes, no importer → dead legacy | **CONFIRMED-CURRENT** | Still tracked-modified and unimported; deliberately **excluded** from this commit set. Removal/justification remains open (hygiene). |
| **B-20** | Repository-root debris must not be swept in by `git add -A` (`8`, `=`, `nohup.out`, `.p18_audit_tmp/`, `.costrict/`, `Research/`, `costrict-p3-ov-01-…txt`) | **CONFIRMED-CURRENT** | All still present. `8` and `=` are **pre-existing** (mtime 2026-09-23), i.e. not session debris, and were deliberately left untouched. This commit set staged **only** explicit paths (§6). |
| **B-21** | *(new)* F-1 revocation applied live but **not** in the local runtime DB | **CONFIRMED-CURRENT (new, P2)** | §1.4. Local environment; requires PD-4/PD-D authorisation before any local migration is applied. |
| **B-22** | *(new)* `dr007` Issue 3 — `ReviewDetailPage` does not surface `mapped_data.activity` | **CONFIRMED-CURRENT (new, P3)** | §1.7. Pre-existing; module graphs disjoint from this task's change. |

### 2.1 Inventory (I) register — spot reconciliation

| ID | Claim | Status | Note |
|---|---|---|---|
| **I-01** | `app.routes` under-reports the surface (50 vs 781) | CONFIRMED-CURRENT | Runtime contract now reports **654 paths**; source-operation enumeration unchanged in kind. |
| **I-02** | Suppliers write routes lack the `require_client_operation("edit_master_data")` ceiling | **RESOLVED** | Implemented this pass (§3); regression test added; p17 harness updated. |
| **I-03** | `ProcessingPage.jsx` upload control has no `useClientAccess()` gate | **RESOLVED** | Implemented this pass (§3); Jest test added. |
| **I-04** | Customer `/organization` renders `admin/AdminPage.jsx`; naming ≠ administrative plane | CONFIRMED-CURRENT | Registered routing observation, unchanged. |
| **I-05** | No `/admin` in the main app; separate `carbontally-admin` app (:3001) + `/ops` console | CONFIRMED-CURRENT | Two internal consoles + one legacy app still coexist; a PO architecture decision, not an implementation fix. |
| **I-06** | 17 operations declare no authentication dependency (incl. 3 mutations) | **CONFIRMED-CURRENT — security-relevant, OPEN** | Not re-enumerated this pass; remains the highest-value unaddressed security item. Recommending it as the next independent-QA target (not silently changed here). |
| **I-07** | Guard distribution (`require_org_member` 235 etc.) | INFO/UNCHANGED | Historical inventory statistic. |
| **I-08** | Audit-dependency presence sparse (35/781); end-to-end audit coverage UNKNOWN | **CONFIRMED-CURRENT** | Still UNKNOWN; needs a dedicated pass. |
| **I-09** | No migration ledger in either local DB; runtime DB ahead of the repo `.env` DB | **CONFIRMED + REFINED** | §1.3: still no ledger in `carbontally_demo_local` or `ct_local_93d5cdd`; the `.env` DB (`19999`) *does not exist as a service at all*, so the earlier "ahead/behind" framing was itself based on a stale `.env` (B-04). |
| **I-10** | Commercial/billing is provider-neutral (no checkout/SDK) | INFO/UNCHANGED | No change measured. |
| **I-11** | Master/reference data not consistently controlled (free-text types vs tables) | CONFIRMED-CURRENT | Unchanged; data-modelling decision. |
| **I-12** | Phase-1 `PO DECISION REQUIRED` items remain open | **CONFIRMED-CURRENT** | Unchanged; this pass opens no new product policy and takes none (AGENTS §62). |


---

## 3. Implemented in this pass

| Item | Files | Nature of change | Regression coverage |
|---|---|---|---|
| **B-02** invoice parser parity | `backend/engines/invoice_extraction.py` | Header accepts `Item` / `Item Description` / `Description` / `Details`; `_CURRENCY_PREFIX` accepts ISO codes (`GBP`, `USD`, `EUR`, …) as well as `£ $ €`. Smallest correct change; no re-architecture. | `backend/tests/unit/services/test_p12_impl_01_invoice_extraction.py` (+163 lines) |
| **B-01** stale expectations | `backend/tests/unit/engines/test_extraction_suggestions.py` | `_suggested_fields()` helper added; expectations reconciled to ISO date `2026-01-15` + `date_raw`; `unresolved == ["billing_period"]`. Tests, not product code. | same file |
| **B-03** pin | `backend/tests/unit/engines/test_extraction_suggestions.py` | New pin `test_count_token_units_is_not_a_physical_unit` (behaviour deliberately unchanged). | same file |
| **I-02** supplier ceiling | `backend/api/v3_suppliers.py`, `backend/tests/unit/api/test_foundation02_supplier_client_ceiling.py`, `backend/tests/unit/api/test_p17_03_supplier_write_path.py` | `require_client_operation("edit_master_data")` added to create/update/delete so suppliers match facilities/assets/vehicles. Server-side only — the UI is never the boundary (AGENTS §44). | 2 test files (new ceiling test + p17 harness fix) |
| **I-03** upload gate | `frontend/src/v3/customer/ProcessingPage.jsx`, `frontend/src/v3/__tests__/processing-upload-capability.test.jsx` | Upload card gated on `useClientAccess().can('upload_document')`; when absent, a `upload-unavailable-notice` explains *why* and what happens next (AGENTS §22/§48). Backend ceiling (`api/upload_gate.py`) unchanged and still authoritative. | new Jest file (PASS) |
| **Closure record** | `docs/architecture/CT-CARBONTALLY-FOUNDATION-CLOSURE-02.md` | This document. | n/a |

**Deliberately NOT changed** (recorded rather than "fixed"):

* `canonical_unit("units")` / `"GBP"` → `None` (B-03): correct per AGENTS §23; widening needs PD-C.
* `.env` values (B-04): untracked local configuration; changing it is PD-4, and the running
  topology lives outside the repo (`/home/shomonrobie/ct_local_env/demo_lab`).
* Local database applied state (B-21): applying a migration to a local DB to make environments
  agree was **not** done.
* `frontend/App_.js` (B-19), root debris (B-20), the discovery test (B-17/F-04/F-05): excluded.

---

## 4. Why B-02 is a real business fix (not a test-only change)

The parser is the **first stage of the platform's core pipeline** (AGENTS §18
`UPLOAD → INGEST → EXTRACT → …`). Before the change, a structurally valid invoice whose table
header used the almost-universal `Item` wording, or whose amounts carried an ISO currency code,
extracted **zero** line items — the pipeline then had nothing to map, validate or calculate. After
the change the same documents yield rows, measured over a 576-file synthetic corpus:

| Corpus metric | Before | After |
|---|---|---|
| Files extracting ≥1 row (of the varied forms tested) | 51 | **217** |
| Files that previously extracted and now fail | — | **0** (no regression) |
| Parity fixture rows (`Item`-header + `GBP` amounts) | 0 | **3** |

This is why the finding was carried as P1 rather than as a parsing nicety.


---

## 5. Recovery point produced this pass

| Property | Value |
|---|---|
| Directory | `/tmp/ct02_postchange_20261009/` |
| Archive | `live_post_f1.dump` — 1,741,182 bytes, custom format (`-Fc --no-owner`) |
| Integrity | `sha256sum -c SHA256SUMS.txt` → **OK**; `pg_restore -l` succeeds (archive readable) → `TOC.txt`, 2,689 lines |
| Archive metadata | created 2026-10-09 22:51:44 +06; dbname `postgres` (Supabase demo project); **2,681 TOC entries**; dumped from server 17.6 by `pg_dump` 18.6; compression gzip |
| Object coverage | `TABLE` 777 (154 `public` + 27 `auth` + storage/realtime and others), `TABLE DATA` 200, `INDEX` 322, `POLICY` 236, `TRIGGER` 110, `FUNCTION` 266, `SEQUENCE` 15, `CONSTRAINT` 498, `ACL` 6, `DEFAULT ACL` 24, `SEQUENCE SET` 2 |
| Database size at capture | 28 MB |
| Live state at capture | ledger 104 rows, tip `20261105000000`; CT-03 client grants `NONE` (F-1 effect present) |

**Honest caveat (AGENTS §73/§84).** This is a **single-database logical archive of the live demo
project**, taken after the F-1 change. It is not a cluster-wide restore point, and the
**restore of this archive was not re-executed this pass** — an earlier cluster-global restore drill
in this task's Step 1 produced observations about Supabase-managed object ownership that make a
blind restore unsafe; repeating that drill was not authorised. Therefore:

* *"a recovery point exists and is integrity-verified"* — **VERIFIED**;
* *"this recovery point has been restored successfully end-to-end"* — **NOT VERIFIED**.

Any future restore must be done into an isolated target with an explicit authorisation, and the
restore outcome recorded, before any destructive live operation is considered.

---

## 6. Git / publication

### 6.1 Preflight (measured)

```
git branch --show-current      → p8-release-reconciled
git rev-parse HEAD             → 8ac778ed5ac29c9b565770824fbbef60e0418558
git ls-remote github p8-release-reconciled → f3df392933a17b4d690de91a12f5f92195db2a7d (exit 0)
```

### 6.2 Content gate applied to the commit set

* Only **explicit paths** were staged — `git add -A` is forbidden by AGENTS §70 and the root
  debris register (B-19/B-20) is still present.
* Secret scan over every staged file (`sk-…`, `eyJ…`, `api_key|password|secret|token = "…"`,
  `postgres://…:…@`, the local demo password string) → **no hits**.
* No file was deleted, renamed or reverted; the worktree was preserved; no force-push, no rebase,
  no `reset --hard`, no `clean -fd`.
* Unrelated pre-existing modifications (`.gitignore`, `frontend/App_.js`) are **excluded**.
* Sensitivity note: the local demo database credential exists in untracked files
  (`backend/.env`, and the demo-lab env outside the repo, mode 600). During inspection it also
  appeared in the local **process table** (`ps`). It was not copied into the repository, this
  report, any commit, or any log. Local credential handling is part of PD-4.

### 6.3 Publication decision

Against **GitHub**, the branch is one commit ahead: `f3df392` (published tip, confirmed by
`ls-remote`) → `8ac778e` (local, intended F-1 closure). Every ahead commit is intended work, the
remote tip is known, and a non-fast-forward situation does not exist, so a **non-force push** of
this branch publishes only intended commits. The result of that push is recorded in §6.4.

> The "232 ahead" number seen in earlier notes refers to the *local-path* remote `origin`
> (`/tmp/ct_step2`), not GitHub, and must not be used for a publication decision (B-07).


### 6.4 Push result (executed)

```
$ git push github p8-release-reconciled
To https://github.com/shomonrobie/CarbonTally.git
   f3df392..8ac778e  p8-release-reconciled -> p8-release-reconciled
PUSH_EXIT=0
$ git ls-remote github p8-release-reconciled
8ac778ed5ac29c9b565770824fbbef60e0418558	refs/heads/p8-release-reconciled
```

Fast-forward only; no `--force`, no history rewrite, no worktree change (dirty-entry count before
and after the push is identical: 43). The published range `f3df392..8ac778e` contains exactly the
F-1 closure commit (2 files, +389 lines, no secrets).

---

## 7. Remaining work, and what is still not verified

| # | Item | Why it remains open | Owner |
|---|---|---|---|
| R-1 | **I-06** — 17 operations with no authentication dependency (incl. `POST /api/waitlist/`, `POST /api/test-upload`, `POST /api/users/password-reset*`) | Security-relevant; must be re-enumerated against the current source and each case judged (liveness vs business route). Not silently changed. | Implementation + independent QA |
| R-2 | **F-04** messaging-send ceiling and **F-05** customer-factor write boundary (F-06 ⇒ PO decision) | New ceilings on messaging and customer factors change *who may act* ⇒ PO DECISION REQUIRED (AGENTS §62). | PO |
| R-3 | **B-09** review/approval + QC live data; **B-13** customer-factor precedence live data | Needs an authorised evidence environment (PD-D) and a live-side count. | PO + QA |
| R-4 | **B-21** local runtime DB not at the live applied state | Requires a decision on whether the local stack is to be migrated/re-pointed (PD-4) before any local migration is applied. | PO |
| R-5 | **B-22 / dr007** `ReviewDetailPage` mapped-activity display | Pre-existing frontend defect; small, isolated, verified unrelated to this change set. | Implementation |
| R-6 | **B-11 / B-12** AGENTS §§54–56 vs the demo tooling that actually exists | Documentation/PO constitution change, including which identity model is authoritative. | PO |
| R-7 | Integration + e2e suites; behavioural RLS negatives against an authorised environment | Not runnable/authorised here; the largest remaining coverage gap (B-10 remainder). | Independent QA |
| R-8 | Discovery-test environment coupling (§1.6) and **I-08** audit-coverage measurement | Test-design + instrumentation work; neither is a product-behaviour change. | Implementation |
| R-9 | **B-19/B-20** dead `App_.js` and root debris | Release hygiene; must be handled deliberately (never by `git add -A`). | Implementation (with PO sign-off for the deletion) |

### 7.1 Product-owner decisions (unchanged in status; listed for closure completeness)

PD-A (ratify/withdraw the MP UI/UX spec) · PD-B (authoritative demo identity model) ·
PD-C (real-world invoice forms + spend-based factors — **partially answered in practice by B-02**,
but the product scope question remains) · PD-D (authorised evidence environment/credentials) ·
PD-E (commit or hold the consultant-parity change set — largely discharged: the change set is now
committed and published) · PD-F (retention durations) · **PD-4** (local topology: which database and
which `.env` are authoritative for local QA — now with hard evidence in §1.3/§1.4).

---

## 8. Verdict and attestation

**Classification: `COMPLETE_WITH_OBSERVATIONS`.**

| Statement | State |
|---|---|
| The foundation register has been reconciled against current source, runtime, database, test and git state | **VERIFIED** |
| B-02 (invoice parser parity) implemented, unit-tested, corpus-measured | **IMPLEMENTED + TESTED** (self-verified; not independently verified) |
| B-01 / B-03 / B-18 (unit-baseline items) reconciled and pinned | **TESTED** (full suite green apart from one pre-existing, unrelated test) |
| I-02 (supplier client ceiling) implemented server-side with ALLOW/DENY coverage | **IMPLEMENTED + TESTED** |
| I-03 (customer upload gate) implemented with a user-facing explanation, backend gate unchanged | **IMPLEMENTED + TESTED** (frontend) |
| Full backend unit suite recorded (5,360/1/8 in 640 s) and frontend Jest recorded (629/1 in 19.8 s) | **MEASURED** |
| Pre-existing failures independently attributed (not mine) | **VERIFIED** (§1.6, §1.7) |
| Recovery point produced and integrity-verified; restore not re-executed | **VERIFIED (existence + integrity)** / **NOT VERIFIED (restore)** |
| Intended commit set published to GitHub by fast-forward | **VERIFIED** (§6.4) |
| Product acceptance of any workflow end-to-end | **NOT CLAIMED** (AGENTS §73/§74) |

### 8.1 Publication of this closure commit

```
$ git commit  → 8675fcb  fix(foundation-02): reconcile foundation findings — invoice parser parity,
                          supplier client ceiling, customer upload gate
                 9 files changed, 1058 insertions(+), 26 deletions(-)
$ git push github p8-release-reconciled
   8ac778e..8675fcb  p8-release-reconciled -> p8-release-reconciled      PUSH_EXIT=0
$ git ls-remote github p8-release-reconciled
   8675fcb8891d1578a0704aab78ebacc9b806f241	refs/heads/p8-release-reconciled
```

Remote tip = local HEAD = `8675fcb`. Both pushes were fast-forward and non-forcing. Staged paths
were explicit (9 files); `.gitignore` and `frontend/App_.js` remained uncommitted and untouched, and
no root debris was swept in.

**Read-only / safety attestation.** No production system was mutated. No live database row,
policy, ACL, migration or storage object was modified. No local database was migrated, re-seeded or
restored. The investor-demo dataset was inspected only, and the local runtime DB was left exactly
as found (including the un-applied F-1 revocation recorded as B-21). No secrets were read into,
printed from, or committed by this work beyond the local process-table exposure noted in §6.2.

