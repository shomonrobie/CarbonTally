# OHD — I3 REMEDIATION INDEPENDENT RE-VERIFICATION — CarbonTally Phase 8 Insight controlled read-only tools

**Verification ID:** `OHD-P8-I3-INSIGHT-TOOLS-REVERIFICATION-20260921`
**Date:** 2026-09-21
**Verifier:** OHD (independent verification agent) — read-only with respect to application code
**Remediation under review:** `651f8c1aa60c635ec1e4da482cfcd651d6657fe8` (`651f8c1`)
**Predecessor:** `docs/verification/OHD-P8-I3-INSIGHT-TOOLS-INDEPENDENT-VERIFICATION-20260921.md` (verdict `FAIL — DEFECTS/BLOCKERS FOUND`, report commit `9c92742`)
**Governing specification:** PO I3 Tool Catalogue Ratification Decision Record (2026-09-21)

---

## 1. Revision, branch, remote and working-tree verification

| Item | Value | Result |
|---|---|---|
| Authoritative checkout | `/home/shomonrobie/ct_93d5cdd` (the Phase 8 release checkout) | ✅ |
| Branch | `p8-release-reconciled` | ✅ |
| **HEAD** | **`651f8c1aa60c635ec1e4da482cfcd651d6657fe8`** | ✅ exact match |
| Remote | `github/p8-release-reconciled` = `651f8c1aa60c635ec1e4da482cfcd651d6657fe8` | ✅ aligned |
| Ahead/behind | `git rev-list --left-right --count github/p8-release-reconciled...HEAD` → `0 0` | ✅ |
| Working tree | `git status --porcelain --untracked-files=all` → empty | ✅ clean |
| Stash | none | ✅ |
| Stale remote | `origin` = `/tmp/ct_step2` — **not used as evidence** | ✅ |

**Footprint of the remediation** (`9c92742` → `651f8c1`) matches the declared set exactly, with no extra file:

```
M  backend/api/dependencies.py                          (+7)
M  backend/services/insight_tools.py                    (+19 -5)
M  backend/tests/unit/api/fakes.py                      (+4)
A  backend/tests/unit/api/test_v3_insight_i3_wiring.py  (+185)
M  docs/implementation/phase8/CT-P8-I3-INSIGHT-TOOLS-20260921.md (+82)
```

No migration, no configuration, no unrelated application file. Every construction site of `RepositoryBundle` in the repository (production `api/dependencies.py:353` and `tests/unit/api/fakes.py:4458`) was updated, so the added dataclass field cannot break another construction path. No repository topology was altered (no branch switch, merge, rebase, reset, prune or remote change).

## 2. D-01 remediation — verified through the REAL production construction path

**Key question: can `report_evidence_lookup` now execute successfully using the real CarbonTally repository wiring rather than a test-only injected `disclosure_projection`? — YES.**

### 2.1 The production factory now provides the repository

Verified by calling the **real** `api.dependencies.get_repositories()` (only `DATABASE_URL` set; no monkeypatching of the factory, no dependency override):

| Check | Result |
|---|---|
| `RepositoryBundle` declares `disclosure_projection` | ✅ (47 fields, was 46) |
| `get_repositories()` constructs it | ✅ `disclosure_projection=DisclosureProjectionRepository(pool)` present in the factory source |
| Constructed object type | ✅ `isinstance(bundle.disclosure_projection, DisclosureProjectionRepository)` → True |
| Read methods the tool needs | ✅ `report_context`, `value_lines`, `evidence_coverage` all present |
| Bundle type | ✅ real `RepositoryBundle` instance |

### 2.2 The original failure path, reproduced end-to-end over the real HTTP path

Composed with the real `create_app()`; repositories from the real `get_repositories()`; real database rows in a disposable full-schema clone; only `get_current_user` overridden (no real JWTs offline) with the principal derived from the database using `auth.py`'s own rules.

```
POST /api/v3/insight/tools/invoke
{"organization_id": "86572570-…", "tool": "report_evidence_lookup",
 "input": {"report_version_id": "5cb34146-2372-477b-9254-71fdce6ab403"}}

-> status: "success"
   data.report_version : {"id": "5cb34146-…", "status": "DRAFT", "reporting_year": 2025}
   data.lines[0]       : {"disclosure_value_id": "1ca27192-…", "requirement_version_id": "2ea61234-…",
                          "calculation_snapshot_id": "f794340a-…", "evidence_line_item_id": "8109b9c3-…",
                          "line_number": 1, "materialisation_kind": "BACKFILL"}
   data.coverage[0]    : {"disclosure_value_id": "1ca27192-…", "reference_count": 1,
                          "line_linked_count": 1, "snapshot_linked_count": 1}
   references          : [report_version 5cb34146-…, evidence_line_item 8109b9c3-…, calculation_snapshot f794340a-…]
   truncated           : false
   invocation          : {"tool": "report_evidence_lookup", "contract_version": "i3-6point-v1",
                          "status": "success", "authorization": "i2-boundary", ...}
```

Before the remediation this exact call returned `{"status": "error", "reason": "internal_error"}` because `repos.disclosure_projection` raised `AttributeError`; the same call now returns real evidence from real rows through the real wiring. The three chained reads (`report_context` → `value_lines` → `evidence_coverage`) all executed against the live database.

### 2.3 Status semantics through the real path

| Case | Expected | Observed |
|---|---|---|
| authorized version with a linked evidence line (rich chain) | `success` | ✅ `success` |
| authorized version whose value has no linked line | `success` | ✅ `success` (1 line row, no linked provenance) |
| valid-but-unknown version id | `no_data` | ✅ `no_data` |
| version belonging to another organisation (caller scoped elsewhere) | `not_authorized` | ✅ `not_authorized`, with `data == {}` and `references == []` |
| suspended (`organizations.is_active = false`) organisation | `not_authorized` | ✅ `not_authorized` |
| malformed identifier | fail closed, no leakage | ✅ no SQL/stack/DSN in the response |

### 2.4 Allowlist and references (post-remediation)

* Returned payload keys are exactly `report_version`, `lines`, `coverage`.
* `lines[]` exposes identity/provenance only (`disclosure_value_id`, `requirement_version_id`, `calculation_snapshot_id`, `evidence_line_item_id`, `line_number`, `materialisation_kind`).
* The database rows used **do** carry raw extracted content (`raw_description = 'Electricity'`, `raw_quantity = 100`, `raw_unit = 'kWh'`) and the repository selects those columns — none of them appear in the payload. Also absent: `source_page`, `evidence_completeness`, `contribution_share`, `payload_hash`, `extraction_method`, `source_item_id`, `source_file_id`.
* References are `{kind, id}` locators only, restricted to the three ratified kinds this tool may emit, and are derived from authorized rows only.
* Reference re-resolution is enforced: after deactivating the caller's membership the same `report_version_id` and the previously returned references are denied (`not_authorized`, empty data/references); after restoration they succeed again. A stored reference is not a grant.

### 2.5 No write path introduced by the remediation

Database table counts (`disclosure_values`, `disclosure_value_evidence`, `evidence_line_items`, `calculation_snapshots`, `report_versions`, `report_generation_queue`, `organization_members`) were **identical before and after** the full invocation matrix. The I3 service contains no `INSERT`/`UPDATE`/`DELETE`/`save`/status-transition statement. The remediation adds no write capability — only an import, a dataclass field, a constructor argument and a log statement.

## 3. D-02 remediation — import cycle

Verified with fresh interpreters, by exit code (stderr was inspected separately, see §8 note):

| Import | Result |
|---|---|
| `import services.insight_tools` (standalone, first) | ✅ succeeds |
| `import api.router` | ✅ succeeds |
| `import api.v3_insight_tools` | ✅ succeeds |
| `import main` | ✅ succeeds (exit 0, `app` present) |

The pre-remediation module-load imports were:

```
pre  : from api.dependencies import RepositoryBundle
       from api.insight_authz import InsightAccess, authorize_insight_scope
       from auth import AuthUser
post : none
```

The remediated module imports the API packages under `if TYPE_CHECKING:` for annotations and imports `authorize_insight_scope` **inside** `_authorize()` at call time. Verified in the source (not merely in an assertion): the module-load section contains no `api.*`/`auth` import, and the call path still performs the real I2 authorization (proved by the full authorization matrix in §5). The layering inversion `services → api` at import time is therefore gone; the runtime dependency on the I2 boundary is retained by design.

## 4. I3 contract unchanged

| Requirement | Result |
|---|---|
| Exactly the four ratified tools registered | ✅ `report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup` (`GET /api/v3/insight/tools` returns precisely these) |
| Unratified tools unavailable | ✅ `sql_query`, `run_sql`, `report_search`, `REPORT_LOOKUP`, `""` all refused (in-band `invalid_input`/`unratified_tool`, or 422 for an empty name at the API) |
| Six-point contract intact | ✅ `backend/domain/insight_tool.py` is **unchanged** by the remediation (0 diff lines): identity, input spec, authorization delegation, output allowlist, reference semantics, status/failure |
| Status vocabulary unchanged | ✅ `ToolStatus` **unchanged** (0 diff lines); only `success`, `no_data`, `not_authorized`, `invalid_input`, `error` were emitted; no new public status category was introduced; `provider_unavailable` remains declared-but-never-raised and is **not** treated as an I3 requirement |
| `contract_version` | ✅ `i3-6point-v1`, stamped consistently on results and the registry |

## 5. I2 authorization boundary — real-path matrix

Every case below was executed over the real router with the real repositories and real database fixtures (verifier's own disposable database).

| Case | Expected | Observed |
|---|---|---|
| customer `org_owner` | allow | ✅ `success` |
| customer `org_admin` | allow | ✅ `success` |
| customer `org_member` | allow | ✅ `success` |
| customer `org_viewer` | allow | ✅ `success` |
| consultant **with** an ACTIVE `consultant_clients` grant | allow | ✅ `success` |
| consultant **without** a grant | deny | ✅ `not_authorized` |
| staff with `is_superuser` (existing staff permission) | allow | ✅ `success` |
| staff without the required permission | deny | ✅ `not_authorized` |
| staff whose role names the auditor persona | deny | ✅ `not_authorized` |
| non-member (outsider) | deny | ✅ `not_authorized` |
| non-member with a forged `org_root`/`root`/`superuser`/`org_superuser`/`authenticated` claim (5 variants) | deny | ✅ `not_authorized` (all five) |
| cross-organisation version | deny | ✅ `not_authorized` |
| processing entity | refuse at the gate | ✅ 403 |
| anonymous | refuse at the gate | ✅ 401 |
| membership revoked → next read | deny | ✅ `not_authorized` |
| consultant grant revoked → next read | deny | ✅ `not_authorized` |
| membership restored → next read | allow | ✅ `success` |

* Authorization is evaluated on **every** protected read: each of the three cases above flipped without any restart, session or cache.
* The decision is made on the **resolved object's** organisation (the evidence tool uses the projection's `report_context` organisation), so an identifier cannot act as a grant.
* References are locators, not grants (§2.4).
* **Creator-private visibility** (D2 §9.2, `conversation_is_visible` / `visibility_created_by`) applies to Insight **conversation** objects. The I3 tool layer reads none of those objects — its four targets are organisation-scoped report/version/disclosure/snapshot read models — so the tools neither bypass nor duplicate that rule; I2 remains the single visibility model and no second model was introduced. (Verified: the tool layer contains no conversation access; `api/insight_authz.py` is byte-unchanged.)
* The auditor persona is not an `organization_members.role` value (the DB check constraint permits `owner/admin/member/viewer`), so the auditor case was exercised through a staff role named `auditor` — the only reachable route for that persona.
* Informational, not a finding: a principal whose *claim* is swapped while its DB-granted staff permission remains is decided by the DB-derived principal and permissions; in production `AuthUser` is minted by `auth.py` from the database, so a forged claim is only reachable if a token could be forged. No new forgery capability was introduced by the remediation.

## 6. Field disclosure — ratified allowlists unchanged

Verified on real rows after deliberately writing marker values into sensitive columns of the target rows (verifier's own database):

* `report_lookup` returned exactly: `id, organization_id, report_type, reporting_year, report_name, status, created_at, completed_at`, `versions[]`, `current_version`, `is_approved_or_final`.
* `report_version_lookup` returned exactly: `id, report_id, version_number, status, is_current, created_at`, `report_organization_id`.
* `report_evidence_lookup` returned exactly: `report_version`, `lines`, `coverage` (as in §2.4).
* **Absent from every payload** (searched the concatenated JSON for both field names and marker values): `generated_content`, `user_edits`, `final_report_url`, `error_log`, `metadata`, `content`, `file_url`, `file_name`, `notes`, `change_summary`, `created_by`, `raw_description`, `raw_quantity`, `raw_unit`, `source_page` — and the marker strings written into them.
* No allowlist was expanded by the remediation: the projections in `services/insight_tools.py` are unchanged in this respect (the diff adds only the logging handler and import reorganisation), and `domain/insight_tool.py` is untouched.

## 7. Deterministic and read-only behaviour

| Check | Result |
|---|---|
| no arbitrary SQL/query interface | ✅ no SQL is composed in the tool layer; identifiers are bound parameters |
| no mutation capability | ✅ no write statement; table counts unchanged (§2.5) |
| no LLM/provider dependency | ✅ none imported by the I3 modules |
| no RAG / embeddings / vector search / LangChain | ✅ none |
| deterministic intent classification | ✅ all four ratified utterances routed to the ratified tool; ambiguous phrasing (`"show me the report evidence"`) refused as `invalid_input/ambiguous_intent` without choosing a tool |
| repeated equivalent authorized requests | ✅ byte-identical results for both `report_evidence_lookup` and `report_lookup` |
| no new runtime dependency | ✅ no change to `requirements*.txt`, `pyproject.toml` or `package.json` |

## 8. Error boundary

An internal failure was induced in the verifier's harness only (one real repository method replaced by a raising stub — no repository code was modified) and invoked through the real HTTP surface:

| Check | Result |
|---|---|
| public status | ✅ `error` / `internal_error` (unchanged vocabulary) |
| stack trace, SQL, DSN, secret or internal detail in the **public** response | ✅ none (searched for `Traceback`, `postgresql://`, the induced column name, `RuntimeError`, and credential-shaped text) |
| **server-side** diagnostics | ✅ a log record **is** produced on the service logger (`logger.exception("insight tool %s failed", …)`), so the failure class that previously produced an undiagnosable `error` is now diagnosable — this closes the verifier's earlier observation O-01 |
| new public error/status category | ✅ none introduced |

Informational: the server-side log line carries the exception text, which can include the offending parameter value (observed for a malformed identifier). That is intended server-side diagnosability and never reaches the public response. Unrelated stderr noise encountered while importing `main` was inspected and is **pre-existing** FastAPI `regex=` deprecation warnings in phase-6 route modules (`routes/emissions.py`, `routes/admin/staff.py`, `routes/admin/workload.py`), not errors.

## 9. Regression testing — independently executed

| Suite | Command (abridged) | Result |
|---|---|---|
| I3 original suite (30) + **new real-wiring suite (5)** | `pytest tests/unit/api/test_v3_insight_i3_tools.py tests/unit/api/test_v3_insight_i3_wiring.py` | **35 collected / 35 passed / 0 failed / 0 errors / 0 skipped** — matches the claimed 35 |
| Focused I1/I2 + Insight regression | `pytest tests/unit/api/test_v3_insight_endpoints.py tests/unit/api/test_v3_insight_i2_authorization.py tests/unit/data/test_i1_insight_migration.py tests/unit/data/test_i2_insight_authorization_contracts.py tests/unit/data/test_i2_insight_rls_live.py` (`INSIGHT_RLS_TEST_DSN` set) | **63 collected / 63 passed / 0 failed / 0 errors / 0 skipped** (= the claimed 58 plus the 5 live-RLS tests) |
| **Full unit suite** | `pytest tests/unit -q --tb=no --junitxml=…` | **COMPLETED: 2,889 collected / 2,877 passed / 4 failed / 0 errors / 8 skipped** — matches the claimed 2,877/4/8 |

### 9.1 Failure classification (inspected, not accepted)

| Failing test | Independent classification |
|---|---|
| `test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered` | **pre-existing, unrelated.** Its `_paths()` helper iterates `router.routes` filtering `isinstance(r, APIRoute)`; in the installed FastAPI version included routers are composed lazily (`<_IncludedRouter>`) so only `/api/v2/health` is visible. Framework-version artifact present before I3 |
| `…::test_canonical_ops_review_assign_registered` | same cause — pre-existing, unrelated |
| `…::test_admin_legacy_compat_surface_retained` | same cause — pre-existing, unrelated |
| `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | **pre-existing, unrelated.** `assert len(names) == 71` vs 77 migration files on disk; the entire I3 line adds **zero** migrations, and the remediation changes no `supabase/` file |

**Mechanical proof that the remediation caused none of them:** the junit failure sets are compared programmatically — pre-remediation (`9245dc5`, 2,884 collected) and post-remediation (`651f8c1`, 2,889 collected) have an **identical** failure set; new failures introduced: **none**; failures fixed: none; collected-count delta: **+5**, exactly the new wiring tests. None of the four is I3-related, I1/I2-related, or remediation-caused.

### 9.2 The new regression suite is sensitive to D-01 (not vacuous)

`test_v3_insight_i3_wiring.py` obtains its bundle from the **real** `get_repositories()` (only the pool provider is stubbed) and asserts the real `RepositoryBundle` satisfies every repository the tool layer resolves. Its assertions were evaluated against the pre-remediation source and the remediated source:

| Assertion | Pre-remediation (`9245dc5`) | Post-remediation |
|---|---|---|
| dataclass declares `disclosure_projection` | ❌ absent | ✅ present |
| factory constructs `disclosure_projection=` | ❌ absent | ✅ present |
| `data.disclosure_projection` imported | ❌ absent | ✅ present |

So the suite would have failed on the defect it now guards. Its `REQUIRED_REPOSITORIES` set (`reports`, `report_versions`, `disclosure_projection`, `logs`, `organizations`, `staff`, `consultants`) was independently checked against the modules: it is **complete and correct** — the tool layer resolves `reports`, `report_versions`, `disclosure_projection`, `logs`; `organizations` plus `staff` and `consultants` (via `resolve_staff_context` / `ensure_consultant_org_access`) are resolved by the I2 boundary.

## 10. I1/I2 integrity

Verified against the known verified I2 application revision `177dff51f59e9b904c021b4bbb7a6c7ee236adf1`:

| File | Result |
|---|---|
| `backend/api/v3_insight.py` | UNCHANGED |
| `backend/api/insight_authz.py` | UNCHANGED |
| `backend/data/insight.py` | UNCHANGED |
| `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` | UNCHANGED |
| `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql` | UNCHANGED |
| I1/I2 verification suites (5 files) | UNCHANGED (0 diff) |
| Any `supabase/` change across the whole I3 line (`177dff5` → HEAD) | **0** |

**Declared, authorised changes to shared application files** (reported explicitly because they are not I3-private):

* `backend/api/router.py` — mounts the I3 router (I3 implementation commit, unchanged by the remediation).
* `backend/api/dependencies.py` — **additive** change to the shared composition root: one import, one dataclass field, one constructor keyword argument. It changes no I2 authorization logic and no existing repository; it was necessary because the real bundle must expose the projection the ratified evidence tool reads. No other construction site exists.

Everything else in the I3 line is new I3 files plus tests and documentation.

## 11. I4–I8 boundary

| Prohibited item | Result |
|---|---|
| I4 AI interaction / canonical I4 audit | ✅ absent; the `invocation` record remains response-only and is not persisted anywhere (no new table/column; the grep for an insert/save/persist path for it returns 0) |
| AI provider integration | ✅ absent (no provider/HTTP client imported by the I3 modules) |
| RAG / embeddings / vector search / LangChain | ✅ absent |
| context/memory | ✅ absent |
| I6 UI / retention / export / billing | ✅ absent |
| production hardening / autonomous actions | ✅ absent |
| additional tools | ✅ registry remains exactly four; the four `TOOL_*` constants are unchanged |
| additional personas / permissions | ✅ none added; no permission vocabulary change; `api/insight_authz.py` unchanged |
| new public status category | ✅ none (`ToolStatus` unchanged) |
| new runtime dependency | ✅ none |
| master specification used as an implementation authorisation | ✅ no code or test references `CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION.md`, and the file is not in the repository; I4–I8 implementation was neither performed nor verified here |

The only non-I3-shaped addition is the operational `logging` call attached to the existing fail-closed exception handler. It is observability on the ratified `error`/`internal_error` path, not I4 audit and not a new capability; it adds no external behaviour beyond the log line.

## 12. Method, environment and limitations

* **Real production construction path.** The application was composed with the real `create_app()`; repositories came from the real `api.dependencies.get_repositories()` factory (driven by `DATABASE_URL` → `infra.supabase.get_service_pool()`). No dependency override of `get_repositories` was used for the wiring verification, and no repository object was fabricated.
* **Real data.** The decisive evidence-path verification ran against real rows: report version `5cb34146-2372-477b-9254-71fdce6ab403`, disclosure value `1ca27192-b841-4d6a-ad4f-b0c7cb0ccc6f`, evidence line `8109b9c3-2714-4692-843f-69cafbde1cdb`, calculation snapshot `f794340a-8beb-47d7-8b0f-b06110e232f7` in organisation `86572570-9de5-4367-ab3f-ee535af2d4b8`.
* **Databases.** The verifier created its own disposable database `ct_i3_reverify_20260921` (template copy of the rehearsal database `ct_p8_rehearsal_20260915`, 133 tables with the full Phase-8 B1/B2 disclosure schema). All fixture writes went there only. `carbontally_demo_local` was **not** written to (and holds no disclosure data, so it could not serve the evidence path). No production, QA, deployment or migration action was taken. `carbontally_test` was not used.
* **Limitations.** (1) No real JWTs offline, so `get_current_user` was overridden while the router, repository factory, I2 authorization layer and database were real; principals were derived from the database with `auth.py`'s rules (including the `org_` role normalisation and `.eq('is_active', True)` membership filter). (2) The `REQUIRED_REPOSITORIES` completeness check was done by tracing module code, not by exhaustive runtime interception. (3) Cline's claims were read for orientation only and were never used as evidence; every statement above is from code, database or API observation at `651f8c1`.
* **Probe artefacts** (outside the repository, not committed): `/tmp/i3rv_probe_f.py` (decisive wiring/evidence/status/error-boundary probe — 40 checks, 40 passed), `/tmp/i3rv_probe_g.py` (authorization matrix, field disclosure, determinism — 25 checks, 25 passed), `/tmp/i3rv_sensitivity.py` (test-sensitivity and D-02 comparison).
* **Hygiene.** `git status --porcelain` → 0 after verification; no application file, test, migration, configuration, fixture or data was modified by the verifier; no secret was read, printed or introduced; repository topology untouched; the only repository change produced by this verification is this report.

## 13. Final verdict

> # **PASS — I3 REMEDIATION VERIFIED**

**Basis.**

* **D-01 (was HIGH/blocker) — remediated and independently verified.** The real `RepositoryBundle`/`get_repositories()` path now provides `DisclosureProjectionRepository` as `disclosure_projection` (47 fields, correct type, required methods), and the exact call that previously returned `error/internal_error` now returns `success` with real evidence lines, real coverage counts and authorized locator references, through the real HTTP surface and the real repository wiring — including correct `no_data`, cross-scope `not_authorized`, suspended-organisation `not_authorized`, allowlist enforcement, reference re-resolution, and no write path. The new wiring regression suite exercises the real factory, would have failed before the fix, and pins a repository set that was independently confirmed complete.
* **D-02 (was LOW) — remediated and independently verified.** `services.insight_tools`, `api.router`, `api.v3_insight_tools` and `main` all import standalone; the module-load `services → api` cycle is gone while the runtime delegation to the I2 boundary remains.
* **No regression, no scope creep.** 35/35 I3 + wiring, 63/63 focused I1/I2+Insight (including live RLS), full suite 2,889 / 2,877 passed / 4 failed / 0 errors / 8 skipped with a failure set **identical** to pre-remediation and independently shown to be pre-existing and unrelated; I1/I2 application files and both Insight migrations byte-unchanged; zero migrations added; no provider/LLM/RAG/I4 audit/UI/retention/billing/autonomous capability; vocabulary, registry and six-point contract unchanged.

**Carried-over informational observations (not blockers, for the PO record).** (1) A valid-but-foreign identifier yields `not_authorized` while a valid-but-absent one yields `no_data`, so an authenticated caller who knows a UUID can distinguish "exists in another organisation" from "does not exist" — this is inherent to the PO-ratified status vocabulary; no tenant data is exposed. (2) The original I3 suite still builds a duck-typed bundle; the masking risk that produced D-01 is now bounded by the dedicated real-wiring suite, but the pattern remains in `test_v3_insight_i3_tools.py` and is worth retiring in a later housekeeping pass. (3) The server-side log line can contain the offending parameter value — intended diagnosability, server-side only. (4) `authorize_insight_scope` is imported per call inside `_authorize()`; a module-level deferred lookup would be marginally cleaner, with no behavioural difference.

**Stage status.** I3 is **not** PO-closed by this report — the sequence remains: Cline implementation/remediation → OHD independent verification → PO closure decision. **I4–I8 are not authorized**, and nothing in this re-verification authorizes them; the newly saved master specification is a specification/control reference only.
