# OHD — INDEPENDENT VERIFICATION — CARBONTALLY PHASE 8 I3 (controlled read-only Insight tools)

**Verification ID:** `OHD-P8-I3-INSIGHT-TOOLS-INDEPENDENT-VERIFICATION-20260921`
**Date:** 2026-09-21
**Verifier:** OHD (independent verification agent) — read-only, no implementation changes
**Governing specification:** PO I3 Tool Catalogue Ratification Decision Record (2026-09-21), as recorded in `docs/implementation/phase8/CT-P8-I3-INSIGHT-TOOLS-20260921.md` §13
**Cline implementation verdict under review:** `I3 IMPLEMENTED — READY FOR INDEPENDENT OHD VERIFICATION`

---

## 1. Verification ID and scope

`OHD-P8-I3-INSIGHT-TOOLS-INDEPENDENT-VERIFICATION-20260921`.

**In scope:** the four-tool ratified catalogue; the six-point tool contract; I2 authorization preservation on every tool invocation; reference semantics; field allowlists; bounded output; the status vocabulary; deterministic intent classification; report lifecycle (§30.3); CalculationSnapshot provenance; API integration; I4 boundary; regression; repository hygiene.

**Out of scope / not performed:** no implementation, no fix, no refactor, no migration, no deployment, no PO decision, **no closure of I3**. No file inside the repository's application surface was modified; the only repository change is this report.

## 2. Exact repository/commit verified

| Item | Value |
|---|---|
| Branch | `p8-release-reconciled` |
| **HEAD (report commit)** | **`9245dc5b233dac560261f161fbd232186f81caad`** (`9245dc5`) |
| **Implementation commit** | **`674fe077d38ed3cfe6ef21685d9b16f515ea1ce7`** (`674fe07`, parent `bfcb04c`) |
| Remote | `github/p8-release-reconciled` = `9245dc5b233dac560261f161fbd232186f81caad` — **aligned** |
| Working tree | clean (`git status --porcelain --untracked-files=all` → 0); no stash |
| Stale remote | `origin` = `/tmp/ct_step2` @ `93d5cddd…` — **not** used as evidence |
| I2 verified state | `177dff5`; OHD I2 re-verification report `a11c7d5` is an ancestor of HEAD |

**Exact changed files (I3 line, `bfcb04c..9245dc5`)**

```
backend/api/router.py                                        (+4)
backend/api/v3_insight_tools.py                              (new, 70 lines)
backend/domain/insight_tool.py                               (new, 160 lines)
backend/services/insight_tools.py                            (new, 354 lines)
backend/tests/unit/api/test_v3_insight_i3_tools.py           (new, 490 lines)
docs/implementation/phase8/CT-P8-I3-INSIGHT-TOOLS-20260921.md (docs; +121 then +59)
```

No other file changed. `git diff --name-status bfcb04c 9245dc5 | grep -c supabase/` → **0** (no migration, no schema, no topology change).

**I1/I2 foundation byte-unchanged vs the verified I2 state `177dff5`** (independently confirmed, not taken from the report):

| File | Result |
|---|---|
| `backend/api/v3_insight.py` | UNCHANGED |
| `backend/api/insight_authz.py` | UNCHANGED |
| `backend/data/insight.py` | UNCHANGED |
| `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` | UNCHANGED |
| `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql` | UNCHANGED |

## 3. Methodology

Verification was performed against the running code, not against the implementation report:

1. **Code trace** of the three new modules and the router diff, comparing declarations with enforcement (declarations alone were never accepted as proof).
2. **Production-path execution.** The application was composed by the real `create_app()`, and repositories were obtained from the **real** `api.dependencies.get_repositories()` factory (driven by `DATABASE_URL` and `infra.supabase.get_service_pool()`). Only `get_current_user` was overridden (no real JWTs are available offline); principals were derived from the database using exactly the rules `auth.py` applies. This is the key methodological difference from the implementation-time tests, which substitute a duck-typed bundle.
3. **Real data.** Reads were executed against the **current database** (`carbontally_demo_local`, Demo Lab) strictly **read-only**, and against an auditor-owned disposable database for the writable fixtures.
4. **Adversarial/negative testing** per §15.
5. **Source-projection comparison** of every declared allowlist against the columns/keys the backing repositories actually return.
6. **Independent test execution**, including the full unit suite that the implementation report states was not completed.
7. All probe scripts live outside the repository (`/tmp`); nothing was committed except this report.

## 4. Code-trace findings — six-point contract

`backend/domain/insight_tool.py` is pure typing (no I/O, no authorization decision, no database, no provider) and defines: `TOOL_CONTRACT_VERSION = "i3-6point-v1"`, `MAX_IDENTIFIER_LENGTH = 128`, `MAX_RESULT_ITEMS = 200`, `ToolStatus`, `REFERENCE_KINDS` (4), `InsightReference` (constructor raises on an unratified kind), `ToolInputSpec`, `ToolDefinition`, `ToolResult`, `bounded()`.

| Point | Where enforced | Independently observed enforcement |
|---|---|---|
| 1 identity | `TOOL_DEFINITIONS` + closed `TOOL_REGISTRY` dict (4 entries) | `GET /tools` returns exactly 4; registry has no other member |
| 2 input | `ToolInputSpec` + `_validate_input()` | unknown parameter → `invalid_input/unknown_parameter`; missing required → `missing_required_parameter`; non-string/non-int → `invalid_parameter_type`; >128 chars → `parameter_too_long`; non-numeric `version_number` → `invalid_version_number` — all reproduced over HTTP |
| 3 authorization | every invocation calls `authorize_insight_scope(...)` then re-checks the **resolved object's** organisation | see §8 |
| 4 output | `_project(row, allowlist)` copies only allow-listed keys — never a row passthrough | payload keys ⊆ the declared allowlist in every success case (§9) |
| 5 reference | `InsightReference(kind, id)` restricted to `REFERENCE_KINDS` | references are `{kind,id}` only; kinds ⊆ the four ratified domains (§10) |
| 6 failure/status | `ToolResult` + `ToolStatus` | only ratified statuses emitted; `provider_unavailable` never produced (§11) |

`contract_version` is a module constant stamped on every result and on the registry payload — consistent and deterministic (identical across repeated calls, verified byte-identical).

## 5. Test commands and results

| Suite | Command | Result |
|---|---|---|
| I3 suite | `pytest tests/unit/api/test_v3_insight_i3_tools.py` | **30 passed / 0 failed / 0 skipped** — matches the reported 30 |
| Focused I1+I2+I3 regression | `pytest tests/unit/api/test_v3_insight_i3_tools.py tests/unit/api/test_v3_insight_endpoints.py tests/unit/api/test_v3_insight_i2_authorization.py tests/unit/data/test_i1_insight_migration.py tests/unit/data/test_i2_insight_authorization_contracts.py tests/unit/data/test_i2_insight_rls_live.py` (with `INSIGHT_RLS_TEST_DSN` set to a disposable database) | **93 passed / 0 failed / 0 skipped** (includes the 5 live-RLS tests) |
| **Full unit suite** (the run the implementation report states was not completed) | `pytest tests/unit -q --tb=no --junitxml=…` | **COMPLETED: 2,884 collected / 2,872 passed / 4 failed / 0 errors / 8 skipped** |

Cline's prediction of ≈2,884 collected was correct (2,854 + 30). The run completed; no timeout, no truncation.

## 6. Security/adversarial results (§15)

All checks were executed over HTTP against the real router and the real repository factory.

| Check | Result |
|---|---|
| cross-organisation report id | `not_authorized` |
| cross-organisation version id | `not_authorized` |
| cross-organisation calculation snapshot | `not_authorized` (on the current database) |
| cross-organisation evidence reference | blocked by defect **D-01** (tool returns `error`; no data returned) |
| forged/unratified reference kind | impossible: `InsightReference` raises at construction; reference kinds are restricted to the four |
| unratified tool name (`sql_query`, `arbitrary_query`, `get_rows`, `run_sql`, `report_search`, `list_reports`, `tool`, `REPORT_LOOKUP`, `"report_lookup "`, `""`) | all refused (`invalid_input/unratified_tool`; the empty name is rejected by the API with 422) |
| malformed IDs | fail closed: `error/internal_error`, **no** SQL text, stack, DSN or column name in the response |
| missing caller context (anonymous) | 401 on `/tools`, `/tools/invoke` |
| inactive organisation | `not_authorized` |
| unauthorized customer role (auditor persona via `role` and via `role_name`) | `not_authorized` |
| unauthorized consultant relationship | `not_authorized`; consultant **with** an active grant → `success` |
| staff without `can_view_all`/`is_superuser` | `not_authorized` |
| staff with `is_superuser` and the correct organisation scope | `success`; with a mismatched scope → `not_authorized` |
| PE (processing entity) | 403 at the gate |
| direct endpoint invocation (bypass attempt) | still fully authorized — no bypass |
| extra fields to retrieve hidden columns (`{"report_id":…, "include":"final_report_url"}`) | `invalid_input/unknown_parameter` |
| arbitrary query-like input / SQL metacharacters in ids | no SQL is composed by the tool layer; ids are bound parameters; a `SELECT`-shaped id simply resolves to `no_data`/`error` |
| ambiguous intent / unsupported intent | `invalid_input/ambiguous_intent` / `invalid_input/unsupported_intent` |
| object-existence disclosure through denial responses | **partially observable** — see observation O-02 |

## 7. I2 preservation findings (§5 of the brief)

| Requirement | Finding |
|---|---|
| current scope obtained through the existing I2 mechanism | ✅ every tool call routes through `authorize_insight_scope`; no re-implementation, no caching, no widening |
| requested object resolved, then authorized against the resolved object | ✅ `report_lookup` compares the report row's organisation; `report_version_lookup` resolves the version, then loads its **report** and compares that organisation; `report_evidence_lookup` uses the projection's `report_context` organisation; `snapshot_lookup` compares the snapshot row's organisation |
| stored identifier cannot grant access | ✅ references are locators only; after membership revocation the same ids are denied and return `data == {}`, `references == []`; after restoration they work again |
| cross-organisation denied | ✅ (all four tools) |
| inactive/suspended organisation denied | ✅ (`not_authorized`) |
| consultant uses the existing `consultant_clients` relationship | ✅ no parallel model added; ungranted consultant denied, granted consultant allowed |
| staff uses the existing I2 staff permissions | ✅ `can_view_all`/`is_superuser` via the unchanged I2 resolver; permission-less staff get no tool scope |
| auditor/PE/public not newly introduced | ✅ auditor persona denied; PE 403; anonymous 401 |
| no parallel authorization model | ✅ the only authorization input is `InsightAccess` from I2 |
| TOCTOU (id validated before resolution) | ✅ **not present**: authorization is performed **after** resolution, against the resolved object's organisation, on every resolution — including the object fetched through a second hop (`version → report`) |

## 8. Field-allowlist findings

Every declared allowlist was compared against the columns the backing repository actually selects, and against the payloads produced from **real rows containing secret markers**. Every allowlisted field exists in the source (no silently-empty fields), and every omission claimed in the implementation report is true:

| Tool | Allowlisted | Source fields omitted (verified) |
|---|---|---|
| `report_lookup` | `id, organization_id, report_type, reporting_year, report_name, status, created_at, completed_at` + `versions`, `current_version`, `is_approved_or_final` | `final_report_url`, `final_report_file_name`, `final_report_size_bytes`, `user_id`, `created_by`, `updated_by`, `generated_content`, `user_edits`, `metadata`, `error_log`, `template_id`, `data_sources`, `progress_percentage`, `current_step`, `started_at`, `updated_at` — all absent from the payload (probe seeded those columns with distinctive marker strings; none appeared) |
| `report_version_lookup` | `id, report_id, version_number, status, is_current, created_at` (+ `report_organization_id`) | `content`, `file_url`, `file_name`, `created_by`, `notes`, `change_summary` — all absent |
| `report_evidence_lookup` | line identity/provenance (`disclosure_value_id, requirement_version_id, calculation_snapshot_id, evidence_line_item_id, line_number, materialisation_kind`) + coverage counts | `raw_description`, `raw_quantity`, `raw_unit`, `source_page` — the repository selects them; the tool's allowlist drops them, so raw extracted evidence is **not** exposed merely because it exists (verified by source trace) |
| `calculation_snapshot_lookup` | the ratified PO §3.4 provenance set incl. `content_hash`, `factor_id`, `factor_kind`, `customer_factor_id`, `factor_source`, `source_item_id`, `source_line_item_id` | `calculated_by`, `performed_by`, `request_id`, `import_batch_id`, `factor_set`, `source_file`, `source_page`, `calculated_at` — none present in the payload; the ratified provenance **is** present against a real row |

`_project()` filters to the allowlist, so extra row keys cannot leak by construction. No row object is ever returned directly.

## 9. Reference findings

* Only the four ratified reference kinds can be constructed (`REFERENCE_KINDS`); an unratified kind raises `ValueError` at construction (so an unratified reference cannot even be represented, let alone resolved).
* References are locators: payload `references` contain only `{kind, id}`; they carry no authority. Demonstrated live: after the caller's membership was revoked, the same report id (previously returned by `report_lookup`) was denied with no data and no references; after restoration it succeeded again — re-resolution per call.
* Reference resolution is deterministic (ordered, de-duplicated by `(kind, id)`), and references are derived from the **bounded** result set (the 200-item traversal produced exactly 201 references: 1 report + 200 versions).
* No broader reference namespace exists: the tool layer returns no other kind, and `evidence_line_item`/`calculation_snapshot` references are only ever built from fields of already-authorized rows.
* Cross-scope references are denied at the authorization step before any object data is read (§8).
* **Limitation:** the evidence tool's reference construction could not be exercised end-to-end on live data because the tool is unreachable in production (see D-01); it is exercised at unit level by the passing suite, and its projection inputs exist and are correct in the current database.

## 10. Report lifecycle findings (§30.3)

| Requirement | Finding |
|---|---|
| report/version identified | ✅ version identity is always stated (`id`, `report_id`, `version_number`) |
| lifecycle state identified | ✅ `status` stated on the report, on `current_version`, on every item in `versions`, and on the evidence tool's `report_version` summary |
| historical/non-current versions not silently represented as current | ✅ `is_current` is stated per version and `current_version` is resolved separately via `get_current`; the two are independent fields |
| `is_approved_or_final` derived from the ratified immutable set | ✅ derived from `IMMUTABLE_REPORT_VERSION_STATUSES` (`APPROVED`, `FINAL`) imported from `domain/disclosure` — live: DRAFT → `false`, REVIEWED → `false`, APPROVED → `true` |
| drafts cannot be represented as approved/final | ✅ reproduced on a real DRAFT current version (`false`) and on a REVIEWED current version (`false`) |
| version interface fields not silently exposed | ✅ `content`, `file_url`, `file_name`, `created_by`, `notes`, `change_summary` omitted for both report tools, including on real rows that contain them |

## 11. CalculationSnapshot findings

* The tool reads the **existing authoritative** `CalculationSnapshot` through the pre-existing `EmissionsLogsRepository.get_snapshot` (`SELECT … FROM public.calculation_snapshots WHERE id = $1`). No calculation engine, no arithmetic, no recomputation exists in the I3 code — the value is returned as stored.
* No mutation: the I3 modules contain no `INSERT`/`UPDATE`/`DELETE`/`save`/status-transition statement (grep-verified), and the row is unchanged after invocations.
* Authorized provenance is preserved and verified against a **real** row on the current database: `content_hash`, `factor_id`, `factor_kind` (`emission_factor`), `factor_source`, `source_item_id` all returned.
* Omitted/internal provenance is not leaked: `calculated_by`, `performed_by`, `request_id`, `import_batch_id`, `factor_set`, `source_file`, `source_page`, `calculated_at` are absent from the payload.
* Authorization is through I2 plus the snapshot row's own organisation check (cross-organisation → `not_authorized`).
* Data path verified, not just the schema: the returned `content_hash`/`factor_id`/`source_item_id` values were compared with the stored row in the current database and match.

## 12. API findings

* `backend/api/v3_insight_tools.py`: `APIRouter(prefix="/api/v3/insight/tools", dependencies=[Depends(require_insight_user)])` with `GET ""` (registry), `POST /invoke`, `POST /intent`. `backend/api/router.py` gains only one import and one `include_router`; **no existing route was modified**.
* Composed application exposes **exactly six** Insight paths (independently enumerated via `app.openapi()`, because this FastAPI version composes included routers lazily as `_IncludedRouter` and `app.routes` no longer flattens):
  `GET,POST /api/v3/insight/conversations`, `GET /api/v3/insight/conversations/{conversation_id}`, `GET,POST /api/v3/insight/conversations/{conversation_id}/messages`, `GET /api/v3/insight/tools`, `POST /api/v3/insight/tools/intent`, `POST /api/v3/insight/tools/invoke`.
* Authorization cannot be bypassed by calling `/invoke` directly: every invocation performs the full I2 scope resolution (verified: direct invocation by an unauthorized principal is denied; PE 403; anonymous 401).
* Malformed requests fail safely (422 at the API for structurally invalid bodies; in-band ratified statuses otherwise).
* Unsupported tool names cannot dispatch (closed registry lookup, `unratified_tool`).
* No arbitrary query execution: no SQL is composed in the tool layer, no dynamic identifiers, `_project()` is an allowlist, and the parameters are bound values.
* No unintended public/persona access: the router-level gate plus the I2 scope resolution are both present.

## 13. I4-boundary findings

* No LLM/provider integration, prompts, natural-language answer generation, RAG, embeddings, vector search, LangChain/other orchestration, context/memory system, I4 canonical audit, UI, retention/export, billing or automatic/external action exists in the I3 code (source scan; the only matches are documentation words and the word "coverage").
* No provider/HTTP client is imported by the I3 modules; `provider_unavailable` is **declared only** and is never raised (verified in code and in runtime statuses observed).
* The structured `invocation` record (`tool`, `contract_version`, `status`, `authorization: "i2-boundary"`, `reference_kinds`) is returned in the response only — it is **not persisted**, no new table/column exists (`supabase/` unchanged), which is exactly the I3 contract/audit-compatibility boundary. It is **not** evidence of I4 having been implemented.
* **No scope leakage found.**

## 14. Pre-existing failures (independently characterised)

| Failing test | Independent finding |
|---|---|
| `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered` | its `_paths()` helper sees only `{'/api/v2/health'}` because the app composes included routers lazily (`_IncludedRouter`) in the installed FastAPI version. Failure is a framework-version/enumeration artifact, present before I3 |
| `…::test_canonical_ops_review_assign_registered` | same cause |
| `…::test_admin_legacy_compat_surface_retained` | same cause |
| `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | `assert len(names) == 71` vs 77 migration files on disk; pre-existing drift, and **I3 added no migration** (0 `supabase/` changes), so it cannot be I3-caused |

These four also failed at `177dff5` (I2 re-verification: 2,854/4F) and at `ad49f57`, `5bd5e29`, `e48ee55`. **No new failure was introduced by I3.**

## 15. Newly discovered failures

### D-01 — BLOCKER (HIGH) — `report_evidence_lookup` cannot execute in production

**Defect.** `backend/services/insight_tools.py` reaches the disclosure projection through the repository bundle:

```
315:  context    = await repos.disclosure_projection.report_context(version_id)
320:  raw_lines  = await repos.disclosure_projection.value_lines(report_version_id=version_id)
325:  counts     = await repos.disclosure_projection.evidence_coverage(disclosure_value_id=value_id)
```

The production bundle has **no** `disclosure_projection` attribute. `RepositoryBundle` (`backend/api/dependencies.py`) declares 46 fields and none is `disclosure_projection`; the whole file never mentions "disclosure"; the `get_repositories()` factory constructs 46 repositories and no disclosure projection. A case-insensitive grep for `disclosure` in `api/dependencies.py` returns nothing, and `repos.disclosure_projection` appears **only** in `services/insight_tools.py` — every other consumer of that repository constructs it directly (`DisclosureProjectionRepository(pool)`, e.g. `api/v3_disclosure.py`, `services/disclosure_projection.py`).

**Reproduction (independent, three independent methods):**

1. **Real factory introspection.** Setting `DATABASE_URL` to a disposable database and calling the real `api.dependencies.get_repositories()`: `hasattr(bundle, "disclosure_projection")` → **False** (while `reports`, `report_versions`, `logs`, `organizations`, `staff`, `consultants` are all present).
2. **Direct root-cause call.** With a real principal, `authorize_insight_scope(...)` succeeds (`persona=customer`) and then `_report_evidence_lookup(bundle, access, {...})` raises
   `AttributeError: 'RepositoryBundle' object has no attribute 'disclosure_projection'`
   **before any database read** — i.e. this is a wiring defect, not a data or environment issue.
3. **HTTP end-to-end.** `POST /api/v3/insight/tools/invoke` with `{"tool": "report_evidence_lookup", …}` returns `{"status": "error", "reason": "internal_error", "data": {}, "references": []}` — reproduced both on the auditor's disposable database **and on the current Demo Lab database read-only** (so it is environment-independent), while `report_lookup`, `report_version_lookup` and `calculation_snapshot_lookup` return `success` in the same run.

**Why the 30 tests pass anyway (masking).** `backend/tests/unit/api/test_v3_insight_i3_tools.py` overrides `get_repositories` with a duck-typed namespace that **injects** the missing attribute:

```
242:  async def _repositories():
243:      return type("Bundle", (), {"reports": world.reports, "report_versions": world.versions,
244:                                 "disclosure_projection": world.projection, "logs": world.logs, …})()
```

The tests therefore exercise the authored attribute, never the production bundle. No test asserts that the real `RepositoryBundle` satisfies what the tool layer requires — so the I3 suite cannot fail on this defect by construction.

**Amplifying factor.** `invoke_tool` wraps tool execution in a blanket `except Exception: return error/internal_error`, which converts the `AttributeError` into a generic status and hides the cause from operators and from the suite. Fail-closed (no data, no leak) but non-diagnosable.

**Impact.** One of the four PO-ratified tools is non-functional for every caller in every environment: the ratified catalogue cannot be operated as ratified. Any future consumer depending on evidence lookup receives `error`. No confidentiality or integrity breach — no data is returned.

**Severity:** HIGH — blocker for I3 closure. Reportable and reproducible; **not fixed** by the verifier.

### D-02 — LOW (latent import hygiene) — circular import between the service and API packages

Importing the service module first fails:

```
$ python -c "from services import insight_tools"
ImportError: cannot import name 'classify_intent' from partially initialized module
'services.insight_tools' (most likely due to a circular import)
```

Chain: `services.insight_tools` → `api.dependencies` → `api/__init__` → `api.router` → `api.v3_insight_tools` → `services.insight_tools` (partially initialised). The application's own order works (`import api.v3_insight_tools` then `from services import insight_tools` → OK), which is why the running app and the test suite are unaffected. Any script, worker or future consumer importing the service layer directly will fail, and the layering inversion (service → API package) is fragile. **Not fixed** by the verifier.

## 16. Observations (informational, no verdict impact)

* **O-01.** The blanket `except Exception` in `invoke_tool` (a) masked D-01 and (b) turns a malformed identifier into `error/internal_error` rather than `invalid_input`/`no_data` (observed: `report_id="not-a-uuid"` → `error`). It fails closed and leaks nothing (no SQL, stack, DSN or column name in the response — verified), but it degrades diagnosability and blurs the status vocabulary.
* **O-02.** Object-existence disclosure: a valid-but-foreign id returns `not_authorized`, while a valid-but-absent id returns `no_data`, so an authenticated caller who knows a UUID can distinguish "exists in another organisation" from "does not exist". No tenant data or content is exposed, both are HTTP-200 in-band denials with empty `data`/`references`, and the UUID space makes guessing impractical. Same class as the I2 observation O-03; a uniform denial policy would close it.
* **O-03.** Documentation inaccuracy (not a code defect): the implementation report states ">124 chars → `parameter_too_long`", but `MAX_IDENTIFIER_LENGTH` is **128** and validation rejects strings longer than 128.
* **O-04.** Intent routing is fail-safe but narrow: because `report`/`summary document` is a `report_lookup` keyword while `version`, `evidence`, `calculation`/`snapshot`/`co2e` are keywords of other tools, natural phrasings such as "show me the report evidence" or "co2e for the report version snapshot" are classified `ambiguous_intent` and refused. The PO ratified explicit refusal for ambiguity, so this is compliant; the practical effect (many realistic utterances refuse) is recorded for the PO.
* **O-05.** The route-enumeration failures (§14) indicate the repository's path-assertion helper is stale for the installed FastAPI version; enumerating `app.openapi()["paths"]` is the working method (used here).
* **O-06.** `report_evidence_lookup`'s tool logic and allowlist could not be exercised end-to-end on live data because the tool is unreachable in production (D-01). Its unit-level behaviour is covered by the passing suite (with an injected projection), its projections match the real disclosure tables present in the current database, and its allowlist was verified by source trace.

## 17. Environment, data and limitations

* **Databases.** Auditor-owned disposable `ct_i2_verify_20260921` (writable; report/version/snapshot fixtures) and `carbontally_demo_local` (Demo Lab) — **read-only** for real-data verification of the three working tools. `carbontally_test` and QA were not written to. No production access, no deployment, no migration.
* **Probe scripts** (outside the repository, not committed): `/tmp/i3_probe_a.py` (production-bundle wiring), `/tmp/i3_probe_c.py` (HTTP end-to-end + adversarial), `/tmp/i3_probe_d.py` (current-database read-only), `/tmp/i3_probe_e.py` (bound, references, personas), `/tmp/i3_schema_check.py` (schema/column availability).
* **Limitations.** (1) No real JWTs offline, so `get_current_user` was overridden while the repository factory, router, authorization layer, persistence and database were real; the principal construction mirrors `auth.py` rule-for-rule. (2) The disposable database is behind the Phase 8 B1/B2 migrations, which is why the snapshot tool needed the current database to be exercised (`source_line_item_id` exists in the current database and not in the clone) — this is an environment drift, not an I3 defect, and it is reported as such. (3) Cline's implementation report was read for claims only and was never used as evidence. (4) The verification target was not switched at any point.
* **Hygiene.** `git status --porcelain` → 0 after verification; no application file, test, migration, configuration or fixture was modified; no secret was read, printed or introduced (secret scan of the four new files → 0 matches); repository topology untouched; the only repository change produced by this verification is this report.

## 18. Final verdict

> # **FAIL — DEFECTS/BLOCKERS FOUND**

**Rationale.** The I3 implementation is largely sound, and most of the ratified requirements are independently verified: only the four ratified tools exist and only they can be dispatched; the six-point contract is genuinely enforced rather than merely declared; I2 authorization is preserved on every resolution with object-level re-checks and no TOCTOU; references behave as locators, not grants; the status vocabulary is respected and `provider_unavailable` is never manufactured; intent classification is deterministic and provider-free; report lifecycle §30.3 is satisfied, including the draft-never-approved rule; the CalculationSnapshot path reuses the authoritative stored value with correct provenance and no internal leakage; the output bound (200/`truncated`) and determinism hold on real data; exactly six Insight paths are composed and no existing route changed; the I1/I2 foundation is byte-unchanged; nothing beyond I3 was implemented; and the full unit suite completed with **no new failures**.

It nevertheless **fails** because one of the four PO-ratified tools is **non-functional in production**: `report_evidence_lookup` cannot execute, because the production repository bundle does not provide the `disclosure_projection` repository that the tool layer requires (D-01). This is not a hypothetical risk: it was reproduced against the real factory, in a direct root-cause call, and over HTTP on both a disposable and the current database, and the passing 30-test suite cannot detect it because the suite injects the missing attribute into a substitute bundle. A ratified deliverable that cannot be operated, with a test suite that structurally cannot fail on it, is a blocker for stage closure. D-02 (circular import between the service and API packages) is reported as a lower-severity latent defect, and O-01…O-06 are recorded for the PO.

**I3 is NOT closed and is NOT verified by this report.** The sequence remains: **Cline implementation → OHD independent verification → PO I3 closure decision.** I4 and later stages remain unauthorized. No defect reported here was fixed, and no implementation change was made.

**Required remediation input for the PO/Cline (not performed by OHD):** wire the disclosure projection into the tool path (e.g. expose it on `RepositoryBundle`/`get_repositories`, or construct it in the service from the pool as every other consumer does), and add a test that exercises the **real** production bundle so the suite can detect wiring gaps of this class; consider narrowing the blanket `except Exception` so internal defects are diagnosable (D-01/O-01); and remove the service→API import cycle (D-02).
