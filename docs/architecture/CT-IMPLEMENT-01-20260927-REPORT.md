# CT-IMPLEMENT-01 — CarbonTally Canonical Remediation, Local Schema Rebuild, Verification and Live-Migration Gate

**Task ID:** `CT-IMPLEMENT-01-20260927`
**Title:** CarbonTally Canonical Remediation, Local Schema Rebuild, Full Verification, and Data-Preserving Live Supabase Schema Migration
**Repository:** `/home/shomonrobie/ct_93d5cdd` (canonical implementation source)
**Branch:** `p8-release-reconciled`
**Starting SHA:** `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`
**Ending SHA (implementation tree):** `689bdc95750f3b7d088b2a5ea7a7ba195026b9a3`
**Date:** 2026-09-27
**Type:** implementation + schema verification + live-migration gate (read-only against every durable environment)

---

## 0. Verdict

```
CT_IMPLEMENT_01_PARTIAL_WITH_BLOCKERS
```

| Verdict component | State | Evidence |
|---|---|---|
| Local canonical schema rebuild + fingerprint | **COMPLETE, VERIFIED** | §5 — 57/57 checks, fingerprint `c89c50bd…` |
| Canonical remediation implemented (bounded scope) | **PARTIAL** | §6 — 4 of the agreed remediation areas implemented and tested; remainder enumerated in §12 |
| Live Supabase target identified | **NO — BLOCKED** | §4 — no production credential/target exists in this environment |
| Live data-preserving migration | **NOT ATTEMPTED (correctly)** | §4, §9 — mandatory stop condition §33.3/§33.4 |
| Application deployment | **NOT PERFORMED** | §9 — outside this task's authority (§27) |
| Production configuration change | **NONE** | §9 |
| Independent verification | **NOT PERFORMED** (Cline verified only) | §13 |

This verdict is deliberately weaker than `CT_IMPLEMENT_01_COMPLETE_LOCAL_AND_LIVE_SCHEMA_VERIFIED`
because the live environment is unreachable **and** significant implementation remains
incomplete. It is deliberately weaker than `CT_IMPLEMENT_01_COMPLETE_LOCAL_ONLY_LIVE_BLOCKED`
because the implementation scope of this task is not complete (§12). The
**local canonical schema itself is complete and verified**, and is not in doubt.

---

## 1. Scope executed in this session

| §  | Task requirement | Status |
|---|---|---|
| 1 | Record HEAD/branch/status/uncommitted/commits | **Done** (§0, §9) |
| 3 | Read the named upstream reports | **Done** (§3) |
| 7 | Local clean rebuild: platform → 1–26 → D32 → 27–89 → verify | **Done** (§5) |
| 8.1–8.3 | `defra_conversion_factors` legacy factor path | **Partially done** — canonical resolver + 4 call sites fixed (§6.5); remainder enumerated |
| 9 | Report sharing (`report_history`) | **BLOCKED — PO decision required** (§6.6) |
| 10 | Scheduled reporting (`report_schedules`) | **BLOCKED — PO decision required** (§6.6) |
| 11.1 A–E | Audit remediation | **Done** (§6.1–§6.4) |
| 11.2 | Audit coverage gaps | **Not implemented** — PO/privacy decision required (§12) |
| 12 | Legacy audit module disposition | **Retained, not revived, not deleted** (§6.8) |
| 13 | `notification_delivery_log` | **Not recreated** (§6.7) |
| 4 | PO-Q01…Q07 implementation | **Verification complete; no unauthorised implementation** (§7) |
| 14 | POD-P feature catalogue remediation | **NOT DONE — remaining work** (§12) |
| 16–20 | Retention / commercial / currency / notification / storage | **Verified only** (§7) |
| 21–23 | Local rebuild, data, testing | **Done to the degree stated** (§5, §11) |
| 25–26 | Live migration + local↔live reconciliation | **BLOCKED, not attempted** (§4) |

No PO decision was invented, changed or reinterpreted. No legacy table was created.
No production system was contacted.

## 2. Governance distinctions preserved (§2)

Every claim below is stated at exactly one level of the required ladder, and no level
is collapsed into another:

```
DOCUMENTED  ≠ PO-APPROVED ≠ IMPLEMENTATION-AUTHORIZED ≠ CODE EXISTS ≠ ROUTE WIRED
≠ AVAILABLE ≠ PERSISTED ≠ E2E VERIFIED ≠ INDEPENDENTLY VERIFIED ≠ PRODUCTION READY
≠ PRODUCTION AUTHORIZED
```

Concretely, in this report:

* a PO decision (`PO-Q01`…`PO-Q07`) is never treated as proof of technical feasibility;
* *code exists* is never reported as *available* or *persisted*;
* *the local canonical rebuild passed* is never reported as *production ready*;
* Cline's own test execution is never reported as *independent verification*.

---

## 3. Source material consulted, and absences

### 3.1 Read in this session

| Artefact | Use |
|---|---|
| `docs/architecture/CT-PO-CARBONTALLY-CT-SCHEMA-03-REPORT-20260927.md` (696 lines) | SCM-004…SCM-007 classification, live-broken route inventory, replacement mapping, PD-1…PD-6 |
| `docs/architecture/CT-PO-CARBONTALLY-CT-SCHEMA-01-REPORT-20260927.md` | canonical inventory + fingerprint baseline |
| `docs/architecture/CT-PO-CARBONTALLY-CT-AUDIT-01-CANONICAL-AUDIT-SYSTEM-RECONCILIATION-20260927.md` | canonical audit architecture, F-1…F-8, §11.1 A–E remediation items |
| `docs/architecture/CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md` (FIEW, 57 rows) | POD-P input |
| `docs/architecture/CT-PO-CARBONTALLY-FEATURE-VERIFICATION-MATRIX-20260927.md` | POD-P input (313 → 256 durable-wired) |
| `docs/architecture/CT-PO-CARBONTALLY-CT-SCHEMA-02-REPORT-20260927.md`, `e2e/environment/README.md` | canonical two-layer rebuild sequence + D32 operator contract |
| `e2e/environment/scripts/canonical_schema_rebuild.sh`, `canonical_schema_verify.py`, `d32_storage_operator.sql`, `verify_d32_policy_semantics.sql` | executed rebuild + verification harness |
| source: `backend/utils/audit_logger.py`, `backend/routes/admin/audit.py`, `backend/utils/emissions.py`, `backend/data/{emission_factors,customer_factors,factor_aliases}.py`, `backend/routes/{reference,documents_main,drafts,emissions}.py`, `backend/routes/admin/extraction.py` | remediation targets |

### 3.2 Absent from the repository (recorded, not invented)

| Named artefact in the task | Status |
|---|---|
| `CT-PO-CARBONTALLY-PO-DECISION-EVIDENCE-PACK-20260927.md` | **present** (965 lines) — the PO-Q01…Q07 decision text used in §7 |
| `CT-PO-CARBONTALLY-FEATURE-VERIFICATION-MATRIX-20260927.md` | present |
| `CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md` | present |
| `CT-PO-CARBONTALLY-FEATURE-CATALOGUE-INDEPENDENT-VERIFICATION-20260927.md` | present (333 lines) |
| `CT-PO-CARBONTALLY-CT-SCHEMA-0{1,2,3}-REPORT-20260927.md` | present |
| `CT-PO-CARBONTALLY-CT-AUDIT-01-…-RECONCILIATION-20260927.md` | present |
| `CT-RECON-01/02/03`, `CT-DB-RECON-01`, `CT-READINESS-01` evidence | **CT-READINESS-01 present**; `CT-RECON-03C` decision pack present; the CT-RECON/CT-DB-RECON results are carried in `CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927{,.md,-REPORT.md,-LEDGER.md}` rather than as separately named files |
| an explicit PO decision on **report sharing** (PD-1) and **report scheduling** (PD-2) | **ABSENT** — no repository governance text selects retire-vs-implement (§6.6) |

No absent artefact was reconstructed, and no verification that the task names is claimed
where the artefact is missing.

## 4. Live target determination — the gate that stopped live migration

### 4.1 Method (read-only; no connection attempted to any unknown host)

1. Enumerated every environment file in the canonical repository and recorded **variable
   names only** (values were never printed).
2. Extracted the **host** portion of the configured database/API targets (never the credentials).
3. Searched the repository for any hosted Supabase project reference.
4. Cross-checked the repository's own production documentation.

### 4.2 Evidence

| Probe | Result |
|---|---|
| `.env` files present | `backend/.env`, `frontend/.env.local`, `admin/.env.development.local` — nothing else |
| `backend/.env` variable names | `DATABASE_URL`, `PORT`, `REACT_APP_API_URL`, `BROWSER`, `ENVIRONMENT`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `RESEND_API_KEY`, `FOUNDER_EMAIL` |
| `DATABASE_URL` host | `127.0.0.1:54426` → the **local** `carbon_ledger` development stack, not a hosted project |
| `SUPABASE_URL` host | `http://127.0.0.1:19999` → local |
| Hosted project refs in env files | **0** (`grep -c 'supabase.co' backend/.env` = `0`) |
| `supabase/config.toml` | `project_id = "carbon_ledger"` — the **local CLI** project file |
| Repository production documentation | `CARBONTALLY_PRODUCTION_BACKUP_PHASE1_1_INDEPENDENT_VERIFICATION_20260911.md:146` — “Production endpoints or credentials: **None** (`onrender.com`, `supabase.co`, `https://`, `service_role` absent)”; `CT-PO-CARBONTALLY-RECON-03C-…:580` — no production URL, project ref or secret is involved |

### 4.3 Conclusion — mandatory stop

```
BLOCKED — LIVE TARGET NOT IDENTIFIABLE
Trigger: task §33.3 (live Supabase target cannot be conclusively identified)
         task §33.4 (live backup/recovery cannot be established)
```

There is **no hosted Supabase project** and **no production credential** available in this
environment. Per §25.1 a connection string must not be assumed to be production; per §25.4
no migration may be executed without a verified recovery point. Therefore:

* no production connection was opened;
* no live schema inventory was taken (task §25.2) and no live data inventory (§25.3);
* no migration was planned, applied or reverted;
* no backup/snapshot exists or could be verified.

**Impact:** the live half of this task (§25, §26) is unachievable from this environment. It
is *not* an implementation failure and must not be reported as one.

**Exact next action required (PO/operator):** supply the production Supabase project
reference *and* a verified recovery point, or run the pre-live gate (§24) and the canonical
migration from an operator-controlled host that holds those credentials. Nothing else in
this task blocks that step.

## 5. Local canonical schema rebuild — executed and verified

### 5.1 What was run

The repository already carries the CT-SCHEMA-02 deterministic, fail-closed rebuild harness
(`e2e/environment/scripts/canonical_schema_rebuild.sh`, 347 lines). It was executed against a
**brand-new disposable target**, not against any durable environment:

```bash
bash e2e/environment/scripts/canonical_schema_rebuild.sh \
     --prefix ct_impl01 --port 55470 --evidence /tmp/ct_impl01_evidence
```

Containers/volume: `ct_impl01_pg` (image `public.ecr.aws/supabase/postgres:17.6.1.159`),
`ct_impl01_storage` (`public.ecr.aws/supabase/storage-api:v1.69.0`), volume `ct_impl01_pgdata`.
Evidence: `/tmp/ct_impl01_evidence/` (inventory A–M, phase logs, ledger, `verify.txt`, `verify.json`).
Run log: `/tmp/impl01_rebuild.log`.

### 5.2 Canonical sequence actually exercised

```
PHASE A  platform provisioning  → storage.buckets / storage.objects / storage.foldername /
                                  auth.uid() / RLS on storage.objects  (proved present)
PHASE B  migrations 1–26        → creates public.organization_members
PHASE C  D32 operator step      → private `documents` bucket + the four approved
                                  provider-context policies on storage.objects
                                  + behavioural policy-semantics proof
PHASE D  migrations 27–89       → migration 27 validates what PHASE C created
VERIFY   canonical inventory / fingerprint / migration-set / D32 / P16R / P17
```

Freshness is proved, not assumed: the log records `fresh target public tables: 0` before the
platform layer, and every phase is fail-closed (the script aborts on any missing platform
object, wrong migration count, failed migration, unverifiable policy, unexpected fingerprint
or anon/public policy).

### 5.3 Result — PASS

```
=== RESULT: ALL CHECKS PASSED (57 pass, 0 fail) ===
REBUILD VERIFIED — canonical schema reproduced
```

| Canonical measure | Expected | Observed | Result |
|---|---:|---:|---|
| public tables | 145 | 145 | **PASS** |
| tables with RLS | 145 | 145 | **PASS** |
| tables **without** RLS | 0 | 0 | **PASS** |
| policies | 227 | 227 | **PASS** |
| policies granting `anon`/`public` | 0 | 0 | **PASS** |
| foreign keys | 172 | 172 | **PASS** |
| indexes | 551 | 551 | **PASS** |
| public functions | 31 | 31 | **PASS** |
| triggers | 88 | 88 | **PASS** |
| columns (all schemas) | 4592 | 4592 | **PASS** |
| **inventory fingerprint** | `c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f` | identical | **PASS** |
| migration-set fingerprint | recorded `40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30` | identical | **PASS** |
| provenance of the migration set | CT-SCHEMA-01 set `d73e1e2b…` reproduced from this HEAD | identical | **PASS** |

### 5.4 D32 operator step — idempotent and behaviourally correct

| Check | Result |
|---|---|
| `d32_storage_objects_rls_enabled` | PASS |
| four policies `d32_documents_{select,insert,update,delete}_org_member` (role `authenticated`) | PASS (4/4) |
| no extra / no `anon`/`public` storage policy | PASS |
| re-run idempotency | PASS — `phase_c_operator_rerun.txt` empty, log line “operator step idempotent (4 policies, 1 bucket, unchanged on re-run)” |
| behavioural semantics (`verify_d32_policy_semantics.sql`) | **11 pass / 0 fail** — member can read/update own-org object; member **cannot** insert another org's path; member **cannot** update another org's object; outsider sees no documents and cannot insert; non-uploads path not visible |

### 5.5 P16R / P17 canonical objects

All named P17-A/C/D/H/K objects and P16-R5/R7 indexes/columns verified present
(scope-3 taxonomy, contractual instruments + allocations, estimation records,
`disclosure_requirement_versions`, over-allocation guard, DC-04/05/07 and
unsubstantiated-estimate rules, calculation-request idempotency index,
reportability indexes, accounting-dimension columns).

### 5.6 Safety statement (§55.1, §22)

* The harness only ever created and modified its own labelled disposable container/volume.
* **No durable environment was contacted**: not the investor demo (`carbon_ledger`),
  not the demo lab, not the CT-SCHEMA-01/02 containers, not production.
* The truncating integration fixture (`backend/tests/integration/conftest.py`, F-046-1) was
  **never pointed at any target** in this task.
* Demo/fixture data was not used as evidence of production correctness.
* After the rebuild the disposable database was used only for **read-only** schema probes
  (buckets, columns, triggers, grants). No application data was inserted into it.

## 6. Remediations implemented

### 6.1 CT-AUDIT-01 §11.1 A — audit write failures are no longer swallowed

**Finding:** CT-AUDIT-01 F-3 — `backend/utils/audit_logger.py` caught every persistence error,
printed a warning and returned `None`, so an audit write could be lost on an authentication,
approval or permission-change path with no observable trace.

**Root cause:** a bare `except Exception` that only printed and returned `None`; there was no
failure counter, no structured log, no escalation mechanism and no way for a caller on a
security-critical path to demand a hard failure.

**Implementation (`backend/utils/audit_logger.py`, +132 lines):**

* explicit failure policy with two modes — `AUDIT_LOG_FAILURE_MODE=log` (default) and `=raise`;
  an unrecognised value falls back to `log` **with a warning**;
* an optional `strict: Optional[bool] = None` parameter on `log_audit()`, so a caller on a
  security/compliance-critical path can demand fail-closed behaviour regardless of the
  process-wide default (helper functions pass it through their existing `**kwargs`);
* a new `AuditWriteError(RuntimeError)`, raised only in strict mode, chained from the original
  exception (`.from e`);
* observability without secrets: `audit_failure_count()`, `last_audit_failure()`
  (action/resource/organization identity + error type — never payloads, tokens or signed URLs)
  and `reset_audit_failure_state()`;
* the `print(…)`-only path replaced by a structured `logging.getLogger("carbontally.audit").error(…)`.

**Behavioural compatibility:** in the default (`log`) mode the function still returns `None` on
failure, so no existing caller changes behaviour; only the *silence* is removed.

**Tests:** 5 unit tests (`test_audit_failure_is_observable_and_not_silent`,
`test_audit_strict_mode_fails_closed`, `test_audit_failure_mode_env_raises`,
`test_audit_success_records_no_failure`, `test_audit_unknown_failure_mode_falls_back_to_log`).

**Remaining limitation:** the *call sites* are not yet classified into strict/non-strict.
Choosing which approval/permission paths must fail closed is an operational decision; the
mechanism now exists for it (see §12 item R-6).

### 6.2 CT-AUDIT-01 §11.1 B — the shadowed activity-export route

**Finding:** CT-AUDIT-01 F-4 — within `backend/routes/admin/audit.py` (prefix `/api/admin/audit`)
the parameterised `GET /activity/{log_id}` was declared **before** the literal
`GET /activity/export` and `GET /activity/search`, so Starlette matched
`/api/admin/audit/activity/export` to the detail handler (which treats `"export"` as a log id).

**Implementation:** the detail handler was moved after all literal `/activity/*` routes; the
declaration order is now `…/activity`, `…/activity/export`, `…/activity/search`,
`…/activity/{log_id}`. Verified by importing the router:

```
['/api/admin/audit/activity', '/api/admin/audit/activity/export',
 '/api/admin/audit/activity/search', '/api/admin/audit/activity/{log_id}']
```

**Tests:** `test_activity_literal_routes_precede_parameterised_route` asserts declaration order
(the property Starlette's first-match resolution depends on).

**Remaining limitation:** the handlers still read the retained legacy `activity_logs` table
(§6.3); only the shadowing defect is fixed.

### 6.3 CT-AUDIT-01 §11.1 C/D — audit mutation boundary and immutability (verified, not changed)

**C — no new client-side mutation capability: unchanged.** No RLS policy, grant or write path
was added or widened by this task. The only writer touched (`utils/audit_logger.py`) continued
to write to the same table with the same columns.

**D — immutability verified on the canonical rebuild (read-only probes):**

| Object | RLS | Policies | Immutability | Grants |
|---|---|---|---|---|
| `public.audit_trail` (canonical ledger) | enabled | **0 — deny by default** | `CREATE TRIGGER p7_audit_trail_immutable BEFORE DELETE OR UPDATE ON public.audit_trail FOR EACH ROW EXECUTE FUNCTION p7_audit_trail_immutable()` — the function raises unconditionally (`audit_trail is append-only (Phase 7): % is not permitted`) for **every** role including `service_role` | `authenticated`, `postgres`, `service_role` (RLS governs effective access; 0 policies ⇒ no policy-based access) |
| `public.audit_logs` (legacy, retained) | enabled | 2 (`audit_logs_tenant_select`, `audit_logs_tenant_insert`, role `authenticated`) | **none** | full DML for `authenticated`, `postgres`, `service_role` (incl. `DELETE`/`UPDATE`/`TRUNCATE`) |
| `public.activity_logs` (legacy, retained) | enabled | 2 (`activity_logs_tenant_select`, `activity_logs_tenant_insert`) | **none** | full DML for `authenticated`, `postgres`, `service_role` |

**Conclusion:** canonical `audit_trail` immutability is **preserved and verified**; the legacy
`audit_logs`/`activity_logs` remain mutable by `service_role` exactly as CT-AUDIT-01 F-5
recorded (they are retained/superseded, zero rows in all probed environments).

**Deliberately not changed:** the row-level trigger cannot intercept `TRUNCATE` (a statement-level
operation), so `service_role`/`postgres` `TRUNCATE` grants on `audit_trail` remain a residual
hardening item (R-4, §12). Any change here would alter the canonical schema, and this task's own
pre-live gate (§21) requires the migration set to remain reproducible at the verified
fingerprint; a schema change therefore belongs to the next canonical release, not to this one.

### 6.4 CT-AUDIT-01 §11.1 E — stale audit documentation corrected

**Finding:** `docs/architecture/README.md` listed `GET /api/admin/audit/activity` as “Audit logs”
under “Admin Endpoints” with no indication that the legacy admin monitoring routes are not the
canonical audit surface, and `docs/architecture/API_ENDPOINTS.md` reproduces the legacy module
inventory.

**Implementation:** a correction block was added to `docs/architecture/README.md` immediately
after that endpoint list, stating:

* the listed routes are a historical inventory of `backend/routes/admin/audit.py`;
* they read the retained legacy `activity_logs` tables and are **not** the canonical audit system;
* the canonical ledger is `public.audit_trail` (append-only, deny-by-default RLS) written through
  `backend/domain/audit.py`, `backend/data/audit.py` and `backend/infra/audit_logger.py`;
* the orphaned `backend/routes/admin/audit_logs.py` is retained but superseded;
* the literal `/activity/export` and `/activity/search` paths are now registered before
  `/activity/{log_id}`.

**Remaining limitation:** only the primary index document was corrected. The wider
`docs/architecture/API_ENDPOINTS.md` inventory (a generated-style endpoint list) still lists the
legacy admin audit endpoints without a canonical-audit caveat — tracked as R-5 (§12).

### 6.5 CT-SCHEMA-03 SCM-004 (F-03/F-04) — canonical factor resolution and provenance

**Finding (CT-SCHEMA-03 F-03, F-04):** the retired table `defra_conversion_factors` was read by 12
registered backend modules (41 read sites). The core helper `utils/emissions.get_emission_factor()`
could therefore resolve **no** factor on the upload/extraction/manual-entry paths, and three
review/approval paths failed *inside* `try` blocks, recording emissions with a null factor link.
Recreating the legacy table is structurally forbidden by the canonical chain (R1 guard, CT-SCHEMA-03 F-01).

**Root cause:** an incomplete rename. The canonical chain renamed the legacy table to
`emission_factors` (same `activity_type` / `co2e_multiplier` / `reporting_year` columns) and added
`unit`, `scope`, `country`, `factor_source`, `factor_set`; the legacy call sites were never repointed.

**Canonical schema facts verified on the disposable canonical rebuild (read-only):**

| Object | Observed columns (abridged) |
|---|---|
| `public.emission_factors` | `id`, `reporting_year`, `activity_type`, `co2e_multiplier`, `unit`, `scope`, `factor_source`, `factor_set`, `country`, `region_deprecated`, `import_batch_id`, `scope2_method`, `scope3_category_hint`, `factor_type`, `gas_coverage`, timestamps |
| `public.customer_factors` | `id`, `organization_id`, `activity_type`, `co2e_multiplier`, `unit`, `scope`, `country`, `reporting_year`, `factor_source`, `status`, `version`, `effective_from`, `effective_to`, … |
| `public.factor_aliases` | `id`, `organization_id` (NULL = global), `alias_text`, `target_activity_type`, `target_provider_key`, … |
| `public.emissions_logs` | factor FK column is **`emission_factor_id`** — there is **no** `defra_factor_id` column |

**Implementation (`backend/utils/emissions.py`, +253/−56):** `get_emission_factor()` now resolves
through the **canonical governed chain**:

```
1. APPROVED CUSTOMER FACTOR   customer_factors   (organization_id + status = 'active')
2. CARBONTALLY FACTOR MATCHING emission_factors  (via factor_aliases; org-scoped then global)
3. UNRESOLVED                 → FactorUnresolved (controlled manual review)
```

* precedence mirrors the canonical repository (`CustomerFactorsRepository.get_active_for_org`,
  D-cf-5: only approved `status = 'active'` factors outrank CarbonTally factors) and
  `FactorAliasesRepository.find_by_alias` (org-scoped alias first, then global);
* the return value is a **superset** of the historical contract — `multiplier`, `reporting_year`,
  `factor_id`, `is_fallback` still work, and the factor decision is now traceable via
  `factor_kind`, `factor_source`, `factor_set`, `unit`, `scope`, `country`,
  `customer_factor_id`, `alias_used`, `resolution`;
* the latest-year fallback is retained but is **explicit** (`is_fallback=True`,
  `resolution='latest_year_fallback'`) — never silent;
* unresolved factors raise `FactorUnresolved(ValueError)` with a manual-review instruction, so a
  missing factor can no longer be an unrecorded `None` (legacy `except ValueError` handlers keep working);
* `organization_id` is an optional parameter (backward compatible); when supplied, customer-factor
  precedence applies;
* the legacy `ACTIVITY_TYPE_MAPPING` is preserved and applied before alias resolution.

**Provenance-column defect found and fixed (new finding, extension of F-04):** the canonical
`emissions_logs` table has **no** `defra_factor_id` column (verified above), yet four write paths
inserted `'defra_factor_id'` — so those inserts could not succeed against the canonical schema.
All four now write `'emission_factor_id'`.

**Call sites repointed in this session (5 files; 4 of the 41 read sites + 1 write column):**

| File | Change |
|---|---|
| `backend/utils/emissions.py` | canonical resolver (F-03 core) |
| `backend/routes/documents_main.py` | review/approval factor lookup → canonical, org-scoped; insert uses `emission_factor_id` |
| `backend/routes/drafts.py` | manual-entry approval factor lookup → canonical, org-scoped; insert uses `emission_factor_id` |
| `backend/routes/admin/extraction.py` | manual-extraction factor lookup → canonical, org-scoped; insert uses `emission_factor_id` |
| `backend/routes/emissions.py` | `emissions_logs` insert uses `emission_factor_id` |

**Tests:** 7 unit tests (canonical-only querying, customer-factor precedence, unapproved customer
factor not outranking, governed alias resolution, explicit latest-year fallback, controlled
unresolved state, activity-type mapping) plus 8 parametrised source guards (no legacy table token
in the repointed files; the canonical column present in each writer).

**Remaining limitation (material):** **37 of the 41 SCM-004 read sites are not yet repointed** —
enumerated in §12 (R-1) with their exact locations, taken from CT-SCHEMA-03 §8/§13. Until then the
admin factor API/UI, the customer SPA factor join, `report_generator.py`,
`organizations/{data,dashboard,exports}.py` and the `routes/reports.py` factor endpoints remain
live-broken. This is the largest residual item of this task and is **not** claimed as fixed.

### 6.6 SCM-005 / SCM-006 — report sharing and scheduled reporting: BLOCKED, no code change

| Item | Canonical replacement | Status |
|---|---|---|
| `report_history` (report **sharing**: `POST /api/reports/{report_id}/share`, `GET /api/reports/shared`) | report *versions* exist (`report_versions`), but **no** share register exists in any migration | **BLOCKED — PO decision required (PD-1)** |
| `report_schedules` (`POST/GET/DELETE /api/reports/schedule`) | **no** canonical object at all; `report_generation_queue` is a pipeline queue, not a schedule store | **BLOCKED — PO decision required (PD-2)** |

The task permits only the *unambiguously authorized* engineering portion here. Both items reduce to
a product choice — **retire the endpoints** or **implement a canonical model (+ durable scheduler)** —
which no repository governance document settles (§3.2). Per §9/§10 no product decision was invented,
no legacy table was recreated, and **no code was changed**:

* the endpoints keep returning a server error today, and that defect is *recorded*, not hidden;
* the engineering candidate change (fail explicitly with `501` and stop leaking raw PostgREST text,
  per AGENTS.md §46) is specified as R-2 in §12 and deliberately **not** applied, because changing
  the response contract of a documented endpoint before the retire/implement decision could conflict
  with the selected direction;
* `notification_delivery_log` (§6.7) is likewise not recreated.

### 6.7 SCM-007 — `notification_delivery_log` not recreated

Verified as CT-SCHEMA-03 classified it: the **only** code consumer is
`backend/routes/admin/audit_logs.py:404`, and that module is never imported, never registered in
`backend/main.py`, absent from `routes/admin/__init__.py` and absent from `verify_startup.py`, with
no dynamic import anywhere. It is an unreachable orphan (latent trap), not a live break.

Action taken: **none** — no table was created, no module was revived. The canonical notification
architecture (`notifications` + `notification_delivery`, both present in the canonical rebuild) is
untouched. The module's disposition is decided in §6.8.

### 6.8 Legacy audit module disposition (task §12) — retained, explicitly classified

`backend/routes/admin/audit_logs.py` was **not** deleted. Checked against the task's own removal
preconditions:

| Precondition for safe removal | Finding |
|---|---|
| D-P2-02 conditions | the module is classified orphaned/superseded, but no governance text authorises deletion of a 1,431-line legacy surface |
| Current route registration | not registered anywhere (verified) |
| Remaining legitimate consumer | none found |
| Canonical replacement | `audit_trail` + V2/V3 audit surfaces exist, but they do **not** cover the module's 12 endpoints one-for-one |
| New competing audit surface created | **no** |

Because removal is not *clearly* authorised and no PO decision retires the module's endpoint set,
it is **retained and explicitly classified as deprecated/orphaned** (documented in §6.4's
correction block). This is the conservative outcome the task prescribes when removal is not
clearly authorised.

## 7. PO decisions — implementation status and evidence

PO decisions were **not changed**. Each is reported at the level actually reached; where the
canonical schema already supports the decision, that is *verification*, **not** new implementation.
Evidence in this table was measured on the disposable canonical rebuild (read-only queries) or by
source inspection, as noted.

| Decision | PO direction | Canonical support (measured) | Implementation in this task |
|---|---|---|---|
| **PO-Q01** retention | domain-specific retention; 7 years = *CarbonTally product policy*, not a legal universal; 90-day telemetry | `system_settings` carries `document_retention_days`, `data_retention_days`, `audit_log_retention_days`, `backup_retention_days`, `operational_telemetry_retention_days` | **None (correct).** No destructive retention was implemented; §16 forbids it before data-class/backup/immutability review. Enumerated as R-7 |
| **PO-Q02** commercial terms | core limits now; overage mechanics deferred; quota exhaustion must never destroy data | `billing_plans`, `customer_subscriptions`, `usage_tracking`, `billing_storage_usage` all present | **None.** No numeric commercial value was invented; no overage billing built |
| **PO-Q03** currency | GBP now, EUR next, multi-currency-ready, currency explicit (never hard-coded) | 8 explicit currency columns incl. `organizations.currency`, `system_settings.default_currency`, `billing_plans.currency`, `customer_subscriptions.currency` | **Verified only.** No hard-coded GBP introduced |
| **PO-Q04** ingestion/storage/mapping/traceability | limits must follow infra → bucket → app; formats PDF/CSV/XLSX/JPG/PNG; mapping first-class; manual review a controlled success path | canonical `documents` bucket exists with `file_size_limit = NULL` (infrastructure limit governs); app limit is **configurable** (`backend/routes/upload.py`: `settings.get('max_file_size_mb', 50)`) — 100 MB is *not* hard-coded | **Verified only** here; the mapping/factor side is handled under §6.5 |
| **PO-Q05** notification identity | platform service sender `notifications@carbontally.co.uk`; sender ≠ actor ≠ tenant | already the default in `backend/services/v3_email.py` (`DEFAULT_FROM_EMAIL`), `backend/services/email_service.py`, `backend/utils/email.py`, `backend/routes/notifications.py`; `v3_email` documents that only the CarbonTally default or an allowed override may be used | **Verified only.** No credential touched, no secret read or written |
| **PO-Q06** SEO/PWA | public/marketing site only; PWA migration deferred | `frontend/public/` ships `robots.txt`, `sitemap.xml`, `manifest.json`, `index.html` | **Verified only.** No PWA migration attempted |
| **PO-Q07** source-to-report provenance | preserve enough lineage to reproduce calculations without mutable UI state | `calculation_snapshots` carries `source_item_id`, `source_page`, `facility_id`, `scope`; `emissions_logs` carries `facility_id`, `scope`; `evidence_line_items` carries `source_item_id`, `source_page` | **Partially served** by §6.5 (factor provenance now recorded); the full chain work is R-1/R-3 |
| **POD-P** feature catalogue | correct FIEW first, then regenerate CAP→FTR + FTR matrix, then independent verification | FIEW register contains exactly **57** machine-readable rows (FIEW-001…057) | **NOT DONE.** Not applied in this task — R-8. No catalogue count was hand-edited |

**Explicit non-claims:** no retention enforcement, no quota/billing mechanics, no PWA, no
notification sending change, and no feature-catalogue correction is claimed to exist.

---

## 8. Database

### 8.1 Local canonical database

| Field | Value |
|---|---|
| Target | `ct_impl01_pg` (`public.ecr.aws/supabase/postgres:17.6.1.159`) + `ct_impl01_storage` (`storage-api:v1.69.0`), volume `ct_impl01_pgdata`, host port `127.0.0.1:55470` — **disposable** |
| Migration count applied | **89 / 89** canonical files (unchanged; none added, none edited, none removed in this task) |
| `supabase/migrations/*.sql` on disk | **89** before and after |
| Local schema fingerprint | `c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f` — **matches canonical** |
| Migration-set fingerprint | `40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30` — matches the recorded value |
| Verification result | 57 checks PASS / 0 FAIL |
| Application rows | 0 (no seed loaded; reference rows only, as designed) |
| Retention | container/volume intentionally left in place for evidence (`--destroy` not used) |

### 8.2 Live database

| Field | Value |
|---|---|
| Live target identified | **NO** (§4) |
| Live migration state / schema fingerprint | **not measured — no connection attempted** |
| Pre-live data counts / post-live data counts | **not measured** |
| Unexplained differences | none (nothing was compared; nothing was migrated) |

### 8.3 Data preservation

No durable database was written to in this task — by any code path, migration or script.

---

## 9. Production

| Question (task §31) | Answer |
|---|---|
| Schema migration performed? | **NO** |
| Application deployment performed? | **NO** |
| Production configuration changed? | **NO** |
| Local↔live reconciliation performed? | **NO** (impossible without a live target) |
| Would application deployment have been required by the change set? | **No** — the implemented changes are backend-internal (factor resolution, audit observability, route ordering) and backward compatible; no frontend/admin build artefact depends on them |
| Secrets committed or exposed? | **No** — no credential, key, JWT, signed URL or `.env` value was printed, written or committed |

## 10. Security verification

| Area | Verification performed | Result |
|---|---|---|
| RLS coverage | canonical rebuild inventory | **145/145** public tables RLS-enabled; **0** without RLS |
| Policy posture | canonical rebuild inventory | **227** policies; **0** granting `anon`/`public` |
| Storage tenant isolation | `verify_d32_policy_semantics.sql` behavioural proof (member vs outsider vs other-org path) | **11 pass / 0 fail** — member *cannot* insert another org's path; member *cannot* update another org's object; outsider sees no documents and cannot insert |
| Canonical audit immutability | trigger/definition/behaviour probe | `p7_audit_trail_immutable` **BEFORE DELETE OR UPDATE … FOR EACH ROW**, raises unconditionally for every role; `audit_trail` has **0** policies (deny-by-default) |
| Legacy audit tables | grants/policies probe | `audit_logs`/`activity_logs` are tenant `SELECT`/`INSERT` policy-scoped for `authenticated`, and remain **mutable by `service_role`** (no immutability trigger) — residual R-4 |
| Audit writer change cannot weaken a boundary | source review | `utils/audit_logger.py` writes to the same table with the same columns; no policy/grant touched; default mode preserves the historical return contract |
| Factor precedence denial | unit test | an **unapproved** customer factor does **not** outrank the CarbonTally factor (`test_unapproved_customer_factor_does_not_outrank_canonical`) |
| Storage configuration | canonical rebuild probe | bucket `documents`: `public = false`, `file_size_limit = NULL` (infrastructure limit governs); exactly the four approved policies exist; no extra or anon/public policy |
| Secrets | session discipline | no secret value printed, written into the report, or committed; only variable **names** and host portions were recorded |
| Storage objects / demo data | session discipline | no durable environment contacted; no storage object created or read in a durable environment |

**Not verified in this task (no over-claim):** a full cross-tenant *database/API* negative suite
(table-level tenant isolation beyond the D32 storage predicates), full role-matrix denials
(Consultant A→B, PE A→B, Viewer→write, Member→admin, Staff→Staff-Admin), and any production
security verification. These require a seeded disposable database plus JWTs and are listed as R-9/§12.

---

## 11. Testing performed (and not performed)

### 11.1 Migration and schema tests

| Test | Method | Result |
|---|---|---|
| All 89 canonical migrations on a clean database | `canonical_schema_rebuild.sh` PHASE A→D | **PASS** (89/89; no migration added, edited or removed) |
| Migration-set integrity / duplicate & drift detection | harness `migration_set_fingerprint_matches_recorded` + `migration_set_provenance_ct_schema_01` | **PASS** |
| D32 operator step idempotency | PHASE C executed twice; second-run evidence file empty | **PASS** |
| Canonical inventory (tables/RLS/policies/FK/index/function/trigger/column) | harness verification | **PASS** (all values equal the canonical expected set) |
| Canonical schema fingerprint | harness verification | **PASS** — `c89c50bd…` |
| P16R/P17 named objects | harness verification | **PASS** |

### 11.2 Backend tests

| Test | Command | Result |
|---|---|---|
| New remediation suite | `python -m pytest tests/unit/test_ct_implement_01_remediation.py -q` | **21 passed, 0 failed** |
| Full backend unit suite | `python -m pytest tests/unit -q` | 4,075 test outcomes; **6 failed** |
| Are those 6 failures caused by this change set? | same 6 tests executed in a **detached worktree at the starting SHA `cb70fd6`** | **Identical 6 failures without this task's changes ⇒ PRE-EXISTING** (`tests/unit/data/test_d17_…`, `test_i1_insight_migration.py`, `test_i2_insight_authorization_contracts.py`, `tests/unit/engines/test_extraction_suggestions.py` ×3) |

The changed modules are not imported by any of the 6 failing test files.

### 11.3 API / frontend / E2E / negative-path tests

| Suite | Status |
|---|---|
| API route tests (live FastAPI app) | **NOT RUN** — no application server was started in this task. The changed route behaviour is covered structurally (router declaration order) and the factor/audit logic by unit tests |
| Frontend / admin (Jest/CRA) suites | **NOT RUN** — no frontend or admin file was changed by this task |
| E2E workflow tests (upload → … → report) | **NOT RUN** — requires a seeded stack; out of scope for the changed surface |
| Negative-path tests | **PARTIAL** — factor-unresolved controlled state, unapproved-customer-factor denial, D32 storage denials (11/11). Full role-matrix negative suite: R-9 |
| SCM-004 "trap" endpoint assertions | **still present and unchanged**: `backend/tests/test_all_endpoints.py` asserts `200` for `GET /api/reports/defra-factors/2024` and the defra-mapping path, whose backing legacy table no longer exists. They were **not** rewritten because the endpoints themselves are not yet repointed (R-1); rewriting the expectation now would encode a half-finished state |

## 12. Remaining work and blockers

Each item states its blocker type, because they are **not** equivalent:
`PO DECISION` (a product choice is missing) vs `SCOPE/TIME` (authorised but not completed) vs
`EXTERNAL` (needs credentials/infrastructure) vs `HARDENING` (requires a schema change).

### R-1 — SCM-004: 37 of 41 legacy factor read sites remain (SCOPE/TIME)

Repointed in this session: `utils/emissions.get_emission_factor` (core), `documents_main.py:517`,
`drafts.py:406`, `admin/extraction.py:190`, plus the `emissions_logs` write column. Still reading
the retired table (locations per CT-SCHEMA-03 §8/§13):

| File | Sites |
|---|---|
| `backend/report_generator.py` | `:595`, `:621`, `:764` |
| `backend/routes/emissions.py` | `:153`, `:199` (read), response key `:213` |
| `backend/routes/reports.py` | `:280` (`GET /api/reports/defra-factors/{year}`), `:1265` (`POST /api/reports/admin/import-defra-factors`) |
| `backend/routes/organizations/data.py` | `:142`, `:168`, `:229`, `:247`, `:252`, `:253`, `:391` (+ route `:363`) |
| `backend/routes/organizations/dashboard.py` | `:109`, `:124`, `:203`, `:236` |
| `backend/routes/organizations/exports.py` | `:56` |
| `backend/routes/admin/defra.py` | 16 reads across 9 routes, incl. the `:482` `defra_factor_id` filter |
| `frontend/src/App.js` | `:731` (customer SPA factor join — F-09) |
| `frontend/src/components/ManualEntryStandalone.jsx` | `:226` (wrong path `/api/defra-factors/{year}` — F-08), `:276` |
| `admin/src/pages/admin/DefraFactors.js`, `components/admin/DefraFactorModal.js`, `ImportDefraModal.js` | `:39`, `:81`, `:95`, `:52`, `:69` (admin Control Plane — F-07) |
| `prisma/schema.prisma`, `seed.ts`, legacy frontend copies | STALE artefacts (not built, not deployed) — F-13 |

**Next action:** repoint each site through the canonical resolver (§6.5) or the V3 factor-matching
service, preserving precedence and provenance; then update the SCM-004 trap assertions in
`backend/tests/test_all_endpoints.py`. Do **not** solve this by renaming the table in code, and never
by recreating the legacy table (forbidden by the canonical R1 guard).

**STATUS UPDATE 2026-09-28 (CT-IMPLEMENT-04 — R-1 partial remediation).** Every
non-decision-gated site in the table above is now repointed onto the canonical
`emission_factors` table, and both legacy frontend factor embeds are removed —
20 occurrences across 7 files (`report_generator.py`, `routes/emissions.py`,
`routes/organizations/{data,dashboard,exports}.py`, `frontend/src/App.js`,
`frontend/App_.js`). **19 occurrences remain in 3 backend files** (18 of them
executable reads in 2 files), plus 9 occurrences in 3 `admin/src` files:

| Residual file | Count | Class / why it was left |
|---|---|---|
| `backend/routes/admin/defra.py` | 16 | PD-3 / F-06 — the whole API is one PO decision |
| `backend/routes/reports.py` | 2 | PD-3 factor import (`:1290`) + PD-5 factor catalogue read (`:279`) — F-05 residual |
| `backend/routes/reference.py` | 1 | documentation comment only (no query) |
| `admin/src/**` (3 files) | 9 | PD-3 / F-07 — Control-Plane factor administration |
| `prisma/schema.prisma` (7), `seed.ts` (1), `frontend_backup_pre_v3_public_20260827/` (4), `e2e/environment/scripts/canonical_schema_verify.py` (1) | 13 | stale artefacts / deliberate absence assertions — F-13 |

(The guard file itself names the retired table 5 times — 2 docstring mentions and 3 assertions that
it is *absent*; `docs/**` mentions it 82 times. Both are intentional and are *not* residuals.)

The SCM-004 trap assertions in `backend/tests/test_all_endpoints.py` are
**unchanged**, because the two endpoints they assert
(`GET /api/reports/defra-factors/{year}` and
`POST /api/reports/admin/import-defra-factors`) are exactly the PD-3/PD-5-coupled
residual. **PD-3, PD-4 and PD-5 remain unratified** in `docs/`. Evidence:
`CT-IMPLEMENT-04-20260928-REPORT-FACTOR-READ-REPOINT.md`.

### R-2 — Report sharing / scheduling (PO DECISION)

`report_history`-sharing (`POST /api/reports/{id}/share`, `GET /api/reports/shared`) and the three
`/api/reports/schedule` endpoints are live-broken with **no** canonical object. The PO must choose
**retire** or **implement canonically** (scheduling additionally needs a durable server-side
scheduler). Until then: no code change, no new table. Optional, decision-neutral hardening once the
direction is known: return an explicit `501` with a plain-language reason instead of leaking raw
database error text (AGENTS.md §46).

### R-3 — Full source-to-report provenance chain (SCOPE/TIME)

PO-Q07 requires source artifact → extraction → normalization → mapping → factor → conversion →
calculation → review/approval → report/version, with manual correction preserving original,
corrected, actor, timestamp, reason, evidence and downstream effect. The canonical columns exist
(`calculation_snapshots.source_item_id/source_page/facility_id/scope`,
`evidence_line_items.source_item_id/source_page`), and the factor step is now provenance-bearing,
but the end-to-end chain is **not** implemented or E2E-verified by this task.

### R-4 — Audit hardening requiring a schema change (HARDENING)

* `audit_trail` `TRUNCATE` is not intercepted by the row-level append-only trigger (a
  statement-level operation) while `service_role`/`postgres` hold `TRUNCATE` grants.
* Legacy `audit_logs`/`activity_logs` remain mutable by `service_role` (CT-AUDIT-01 F-5).
* Both require a migration, which would change the canonical migration set and fingerprint.
  Recommended as an explicit next-release migration (statement-level trigger and/or grant review)
  with a deliberate fingerprint re-baseline — **not** smuggled into this task.

### R-5 — Documentation completeness (SCOPE/TIME)

`docs/architecture/API_ENDPOINTS.md` still lists the legacy admin audit endpoints without the
canonical-audit caveat that was applied to `docs/architecture/README.md`.

### R-6 — Classify audit call sites (PO/OPERATIONS DECISION)

The strict-failure mechanism now exists (§6.1) but the 35 canonical audit call sites are not yet
classified into fail-closed vs log-and-continue. Choosing which approval/permission/authentication
paths must fail closed is a product/operations decision.

### R-7 — Retention enforcement (PO DECISION + HARDENING)

PO-Q01 is selected but enforcement must not be destructive. Before any deletion job: data-class
inventory, purpose/legal boundaries, audit-immutability interaction, backup behaviour, tenant
isolation and reversibility. The five `system_settings` retention columns exist; nothing enforces them.

### R-8 — POD-P feature catalogue remediation (SCOPE/TIME)

Apply the 57 FIEW corrections (FIEW-001…057) to
`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` (Truth token →
`IMPLEMENTED_IN_CODE_BUT_BLOCKED_BY_SCHEMA` / `DISPOSABLE_ENVIRONMENT_ONLY` / `DOCUMENTED_ONLY`
per the FIEW §10 corrective action), recompute the headline (313 → **256** durable-wired), then
mechanically regenerate the CAP→FTR mapping and the FTR matrix, then obtain **independent**
verification. Not started; no count was hand-edited.

### R-9 — Tenant-isolation negative suite (SCOPE/TIME)

A seeded disposable database plus JWTs is required to exercise Customer A→B, Client A→B, Consultant
A→B (and A→B's client), PE A→B, Viewer→write, Member→admin, Staff→Staff-Admin, Customer→internal and
PE→internal denials at the API/RLS layer (D32 storage denials are already proved, 11/11).

### R-10 — Audit coverage gaps (PO DECISION)

Authentication events (login/logout/failure), security-setting changes, data-access/read auditing,
notification acknowledgement, verification activity and aggregate audit statistics are **absent**.
Each needs either new implementation under an existing policy or a new privacy/product decision.
Nothing was invented, and no "who accessed what" capability is claimed.

### R-11 — Live migration (EXTERNAL BLOCKER)

Blocked on a production Supabase target **and** a verified recovery point (§4). Then: pre-live gate
(§24) → live inventory (§25.2/§25.3) → data-preserving plan (§25.5) → apply (§25.7) → verify
(§25.8) → local↔live reconciliation (§26).

### R-12 — Non-blocking hygiene (SCOPE/TIME)

Seven dormant history tables and the retained legacy audit surfaces remain (CT-AUDIT-01 §20); the
`prisma/schema.prisma` model set is a pre-RC2 snapshot; the 6 pre-existing unit-test failures
(migration-ordering / extraction-suggestion assertions) are unrelated to this task but should be
triaged by their owning workstream.

---

## 13. Independent verification

**No independent verification occurred.** Everything in §5, §6 and §11 was executed and assessed by
Cline. That is *implementation verification*, and it is explicitly **not** the same as independent
verification (task §31, AGENTS.md §73).

Recommended independent checks, in priority order:

1. Re-run the canonical rebuild harness from a clean clone and compare the fingerprint independently.
2. Re-derive the SCM-004 remaining-site list from `git grep` and confirm the 37/41 accounting.
3. Re-run the new test suite and the parametrised source guards.
4. Attempt to falsify the audit-failure claims (force an insert failure; confirm the counter/log/
   `AuditWriteError` behave as stated, including `AUDIT_LOG_FAILURE_MODE=raise`).
5. Re-probe `audit_trail` immutability and the legacy `audit_logs` grants on an independent rebuild.
6. Re-check that the live blocker (§4) is a genuine environment limitation, not a mis-read.

---

## 14. Acceptance checklist (task §34, answered honestly)

| Item | State |
|---|---|
| PO-Q01…Q07, POD-P preserved (unchanged) | **YES** — none altered; POD-P not yet executed |
| CT-SCHEMA-03 legacy factor paths addressed | **PARTIAL** — core + 4 sites; 37 sites remain (R-1) |
| `defra_conversion_factors` NOT recreated | **YES** |
| Canonical factor matching used | **YES** — `emission_factors` + `customer_factors` + `factor_aliases` |
| Factor provenance preserved | **YES** — provenance keys returned; `emission_factor_id` written |
| Factor precedence preserved | **YES** — approved customer factor → CarbonTally → unresolved |
| Unresolved factors → controlled review | **YES** — `FactorUnresolved`, documented manual-review path |
| `report_history` handled per authorised direction | **NO — PO DECISION BLOCKED** (no direction exists) |
| `report_schedules` handled per authorised direction | **NO — PO DECISION BLOCKED** |
| `notification_delivery_log` NOT recreated | **YES** |
| Canonical notification architecture used | **YES** (untouched; `notifications` + `notification_delivery` present) |
| `audit_trail` remains authoritative | **YES** — verified |
| `audit_trail` remains immutable | **YES** — trigger verified (TRUNCATE caveat = R-4) |
| Legacy `audit_logs.py` not incorrectly revived | **YES** — still unregistered |
| Audit exception handling reviewed | **YES** — fixed and tested |
| Audit route shadowing fixed or retired | **YES** — fixed and tested |
| Audit permission risks reviewed | **YES** — documented (F-5 confirmed; R-4) |
| Stale audit documentation corrected | **PARTIAL** — README corrected; `API_ENDPOINTS.md` = R-5 |
| Feature catalogue corrected | **NO** — R-8 |
| CAP→FTR regenerated | **NO** — R-8 |
| FTR matrix regenerated | **NO** — R-8 |
| No unsupported feature claims introduced | **YES** — this report states residuals explicitly |
| Provenance chain implemented/verified | **PARTIAL** — factor step only (R-3) |
| Mapping is first-class | **PARTIAL** — factor/alias resolution canonicalised; mapping UI/lineage unchanged |
| Raw/corrected mapping distinguishable | **NOT ADDRESSED** (R-3) |
| Manual review is a controlled success path | **YES for factors** — unresolved → `FactorUnresolved` + manual-review instruction |
| Local clean rebuild passes | **YES** |
| 89 canonical migrations accounted for | **YES** — 89/89, unchanged |
| D32 sequence verified | **YES** — idempotent + 11/11 semantics |
| Canonical schema fingerprint matches | **YES** — `c89c50bd…` |
| Live target identity verified | **NO — BLOCKED (§4)** |
| Live backup/recovery verified | **NO — BLOCKED** |
| Live schema inventoried | **NO — BLOCKED** |
| Live data inventoried | **NO — BLOCKED** |
| Migration plan reviewed | **NO — BLOCKED** |
| Data-preserving migration executed | **NO — BLOCKED** |
| Live schema fingerprint verified | **NO — BLOCKED** |
| Live data preservation verified | **NO — BLOCKED** |
| No unexplained production data loss | **YES** (no production write occurred) |
| Local↔live structural reconciliation | **NO — BLOCKED** |
| No unauthorised application deployment | **YES** |
| No unauthorised production configuration change | **YES** |
| No secrets committed/exposed | **YES** |
| Final implementation report created | **YES** — this document |
| Final verdict supported by evidence | **YES** |

---

## 15. Final verdict

```
CT_IMPLEMENT_01_PARTIAL_WITH_BLOCKERS
```

* **Local canonical schema: COMPLETE and verified** — 89/89 migrations, 145 tables, 145 RLS-enabled,
  227 policies, 172 FKs, 551 indexes, 31 functions, 88 triggers, 4592 columns, fingerprint
  `c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f`, D32 operator step verified
  idempotent and behaviourally correct (11/11), P16R/P17 objects present.
* **Implementation: PARTIAL** — the audit defects (A/B/E), the canonical factor-resolution core and
  four legacy factor call sites plus the `emissions_logs` factor column are implemented, tested and
  committed. 37 legacy factor sites, report sharing/scheduling, the full provenance chain, audit
  coverage gaps, retention enforcement and the feature-catalogue regeneration remain.
* **Live migration: BLOCKED** — no production target or recovery point is available in this
  environment; nothing was attempted against any durable system.
* **No independent verification** — Cline's verification only.

Strengthening this verdict requires: (a) the PO decisions for report sharing/scheduling and the
remaining PO-Q implementation scope; (b) completion of R-1/R-3/R-8; (c) a production Supabase
target with a verified recovery point for R-11.

---

## 16. Changes, commits and evidence

### 16.1 Working tree

| Field | Value |
|---|---|
| Branch | `p8-release-reconciled` |
| Starting SHA | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Ending SHA (implementation) | `689bdc95750f3b7d088b2a5ea7a7ba195026b9a3` |
| Uncommitted entries before this task | **124** (pre-existing, untouched) |
| Uncommitted entries after the implementation commit | **124** — i.e. this task absorbed nothing unrelated |
| Concurrent agents | none observed modifying this repository during the session (HEAD advanced only by this task's own commit) |

### 16.2 Files changed by this task

| File | Change |
|---|---|
| `backend/utils/audit_logger.py` | audit failure visibility, `strict`, `AuditWriteError`, counters |
| `backend/routes/admin/audit.py` | literal `/activity/export` + `/activity/search` registered before `/activity/{log_id}` |
| `backend/utils/emissions.py` | canonical governed factor resolution with precedence + provenance + `FactorUnresolved` |
| `backend/routes/documents_main.py` | review/approval factor lookup → canonical; `emission_factor_id` |
| `backend/routes/drafts.py` | manual-entry factor lookup → canonical; `emission_factor_id` |
| `backend/routes/admin/extraction.py` | manual-extraction factor lookup → canonical; `emission_factor_id` |
| `backend/routes/emissions.py` | `emissions_logs` insert uses `emission_factor_id` |
| `backend/tests/unit/test_ct_implement_01_remediation.py` | **new** — 21 regression tests |
| `docs/architecture/README.md` | canonical-audit documentation correction |
| `docs/architecture/CT-IMPLEMENT-01-20260927-REPORT.md` | **new** — this report |

No migration, seed, configuration, `.env`, `frontend/**`, `admin/**` or `e2e/**` file was changed.

### 16.3 Commits created

| SHA | Subject |
|---|---|
| `689bdc95750f3b7d088b2a5ea7a7ba195026b9a3` | `fix(ct-implement-01): canonical factor resolution, audit failure visibility, admin audit route ordering` |
| `922b3236bb582fb6001dba6b7d4e4d02465a194b` | `docs(ct-implement-01): implementation report (partial, live migration blocked)` — the commit that first contained this report |
| `28f82ed` (full SHA in the session summary) | `docs(ct-implement-01): record the report commit SHA` — records `922b3236…` in §16.3. This convention terminates there: the SHA-recording commit's own SHA is reported in the session summary rather than self-referentially. |

Nothing was pushed.

### 16.4 Evidence index (session-local, outside the repository)

| Evidence | Contents |
|---|---|
| `/tmp/impl01_rebuild.log` | full rebuild log; `fresh target public tables: 0`; `RESULT: ALL CHECKS PASSED (57 pass, 0 fail)`; `REBUILD VERIFIED` |
| `/tmp/ct_impl01_evidence/` | `verify.txt`, `verify.json`, `ledger_{phase_b,phase_d,canonical}.tsv`, `phase_{a_identity,b,c_operator,c_operator_rerun,c_semantics,d}.txt`, `inventory/{A…M}` |
| `/tmp/impl01_probe_summary.txt` | canonical tables present; `emission_factors` / `factor_aliases` / `customer_factors` column sets |
| `/tmp/impl01_tail.txt`, `/tmp/impl01_auditsec.txt`, `/tmp/impl01_auditsec2.txt`, `/tmp/impl01_trigdef.txt` | `emissions_logs` factor column; audit table RLS/policies/grants; `audit_trail` trigger definition + function body |
| `/tmp/impl01_poq.txt`, `/tmp/impl01_q5q6.txt` | PO-Q01…Q07 support evidence (currency, retention, bucket limits, commercial tables, provenance columns, sender identity, SEO files, upload limit) |
| `/tmp/impl01_pytest_new3.txt`, `/tmp/impl01_pytest_unit.log`, `/tmp/impl01_*testcount*.txt` | 21/21 new tests; full unit suite; pre-existing failure analysis |
| `/tmp/impl01_rebuild_head.txt`, `/tmp/impl01_route*`, `/tmp/impl01_git.txt` | harness usage; router path order; git state and diffstat |
| `/tmp/ct_impl01.env` | **disposable** locally generated database password for the evidence target (not a durable credential; never printed) |

### 16.5 Final statement

The canonical repository now reproduces the canonical schema from zero at the canonical fingerprint,
and the audit/factor defects that could be fixed without inventing product policy are fixed, tested
and committed. The live database was not touched — it could not be identified, and per this task's
own mandatory stop conditions that is the correct outcome rather than a workaround. Everything this
task did **not** do is enumerated in §12 and repeated in the verdict; nothing is claimed that was not
measured.

<!--CTEOF-->
