# CT-IMPLEMENT-03 — Report Schedule and Share Canonicalization (implementation report)

**Date:** 2026-09-28
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Task ID:** CT-IMPLEMENT-03-20260928-REPORT-SCHEDULE-AND-SHARE-CANONICALIZATION
**Starting SHA:** `21310afae69cace6b67985eda7e817b0aee1c33b`
**Ending SHA:** see §23 (recorded after the report commit)
**Status:** APPLICATION LAYER **IMPLEMENTED · UNIT-TESTED · E2E-VERIFIED ON A DISPOSABLE
CANONICAL DATABASE**; **NOT INDEPENDENTLY VERIFIED**; **NOT PRODUCTION READY**

> **INDEPENDENT VERIFICATION NOT PERFORMED.** Every result below comes from the
> implementing agent's own harness on disposable infrastructure. `TESTED` and
> `VERIFIED` here mean "the named command reproduces the stated result", not
> "independently accepted" (AGENTS.md §73).

---

## 1. Task and scope

Reconcile the report-scheduling and report-sharing application layer with the
canonical schema (CT-SCHEMA-01/02, extended by CT-IMPLEMENT-02), closing the two
findings CT-IMPLEMENT-02 left open:

* **F-1** — the schedule and share routes read/wrote the **retired**
  `report_schedules` / `report_history` tables and were live-broken against any
  canonical database.
* **F-2** — `GET /api/reports/schedule/frequencies` advertised `daily`, which the
  canonical frequency CHECK rejects.

| Layer | In scope | Out of scope (remaining) |
|---|---|---|
| Schema | **none** — no migration was added, changed or applied | live/production migration (R-11, external blocker) |
| Data | canonical schedule/share repositories | R-1 remaining factor sites (~37) |
| Services | canonical schedule/share services + the runner's producer | R-3 provenance suite, R-7 retention |
| API | canonical `/api/v3/reports` schedule/share routes; legacy router delegation | R-6 audit classification, R-10 audit coverage |
| Worker | durable due-schedule trigger bound to the canonical runner | none |
| Docs | this report | R-5 `API_ENDPOINTS.md` truth pass, R-8 feature catalogue |

No business policy was invented. Where a product decision would have been needed,
the work was left unimplemented and recorded (§20).

---

## 2. CT-IMPLEMENT-02 evidence consumed (treated as established, then re-checked)

| Evidence | Value | How it was used here |
|---|---|---|
| From-zero extended rebuild | 94 pass / 0 fail | the canonical schema was assumed present; re-verified structurally (§18.1) |
| DB suite | 68 assertions, 0 FAIL | not re-run (out of scope); the E2E adds app-layer assertions instead |
| Baseline 89-migration fingerprint | `40b168b3…` unchanged | this change-set adds **no** migration, so the fingerprints cannot have moved |
| Extended chain | 92 migrations | ditto |
| `backend/domain/report_schedule.py` | exists, 27 tests | extended additively (`SCHEDULE_REPORT_TYPES`) and reused unchanged otherwise |
| `backend/services/report_schedule_runner.py` | exists, 11 tests | wired to real persistence + a real producer; **not modified** |
| Canonical tables | `report_schedule_definitions`, `report_schedule_runs`, `report_shares`, `report_share_access_events` | the only tables this change-set writes |
| Route/data-layer rewrite | incomplete | completed here (§12–§15) |
| Independent verification | not performed | unchanged (§22) |

---

## 3. Legacy schedule/share reference inventory (Phase 0)

Every reference to the two retired tables, classified. `report_schedules` had the
four table accesses CT-SCHEMA-03 recorded; `report_history` had three.

| # | Location | Class | Evidence | Disposition |
|---|---|---|---|---|
| 1 | `backend/routes/reports.py:1372` `POST /api/reports/schedule` → `from_('report_schedules').insert` | **ACTIVE_RUNTIME (live-broken)** | 500 on any canonical database (table absent) | replaced by canonical create (§12) |
| 2 | `backend/routes/reports.py:1435` `GET /api/reports/schedule` → `from_('report_schedules').select` | **ACTIVE_RUNTIME (live-broken)** | 500 | replaced by canonical list (§12) |
| 3 | `backend/routes/reports.py:1498` `DELETE /api/reports/schedule/{id}` → existence `select` | **ACTIVE_RUNTIME (live-broken)** | 500 | replaced by canonical delete (§12) |
| 4 | `backend/routes/reports.py:1510` `DELETE /api/reports/schedule/{id}` → `.delete()` | **ACTIVE_RUNTIME (live-broken)** | 500 | replaced by canonical delete (§12) |
| 5 | `backend/routes/reports.py:1852` `POST /api/reports/{id}/share` → `from_('report_history').select` | **ACTIVE_RUNTIME (live-broken)** | 500 | replaced by canonical share (§15) |
| 6 | `backend/routes/reports.py:1929` share → `from_('report_history').update` (shares in `metadata`) | **ACTIVE_RUNTIME (live-broken)** | 500 | replaced by canonical share (§15) |
| 7 | `backend/routes/reports.py:1969` `GET /api/reports/shared` → whole-table `select` | **ACTIVE_RUNTIME (live-broken + over-broad)** | 500; also enumerated every report-history row before filtering in Python | replaced by the canonical recipient-scoped read (§15) |
| 8 | `backend/routes/reports.py:2034` `calculate_next_run()` | **DEAD_LEGACY after the rewrite** | only callers were accesses 1–4 | removed; superseded by `domain.report_schedule.next_occurrence` |
| 9 | `backend/routes/reports.py:110/123/176/182` legacy schedule/share models | **DEAD_LEGACY after the rewrite** | described retired fields (`day_of_week`, `format`, `filters`, `metadata.shares`) | removed; replaced by canonical request models + `services.*.shape_*` |
| 10 | `…20261023000000_ct02_scheduled_reporting.sql:85` `to_regclass('public.report_schedules')` | **DOCUMENTATION_ONLY (DDL guard)** | refuses to apply if the retired table exists (PD-2) | unchanged — a guard, not an access |
| 11 | `…20261022000000_ct02_report_sharing.sql` `to_regclass('public.report_history')` | **DOCUMENTATION_ONLY (DDL guard)** | ditto (PD-1) | unchanged |
| 12 | `e2e/environment/scripts/canonical_schema_verify.py:154` legacy-absent list | **TEST_ONLY** | asserts absence from the canonical inventory | unchanged |
| 13 | `API_ENDPOINTS.md`, docs/architecture, `docs/cline/…Module_Inventory_V3.md` prose | **DOCUMENTATION_ONLY** | historical/inventory text | not touched (R-5 scope) |
| 14 | `frontend/**` | **none** | zero callers (§16) | nothing to change |
| 15 | docstrings in `domain/report_schedule.py`, `services/report_schedule_runner.py`, `data/report_schedules.py` naming the retired table | **DOCUMENTATION_ONLY (prose)** | explain what was retired and why it must not return | kept deliberately; §19 asserts *access*, not mentions |

**No reference was classified DEAD merely because it is old.** Items 8 and 9 are
dead because their only callers were accesses 1–7; those are proven live by
`main.py:214` (the legacy router is registered) and by CT-SCHEMA-03's route
register.

---

## 4. Canonical schedule architecture (Phase 0–1 contract)

Trace, route → service → repository → table:

```
api/v3_reports.py          services/report_schedules.py     data/report_schedules.py        schema
POST /schedules         →  ReportScheduleService.create →  INSERT report_schedule_definitions
GET  /schedules         →  …list_schedules              →  SELECT … WHERE organization_id = $1
GET  /schedules/{id}    →  …get / …runs                 →  report_schedule_definitions / _runs
POST /schedules/{id}/pause|resume → …pause/…resume       →  UPDATE is_active,next_run_at,paused_at
DELETE /schedules/{id}  →  …delete                      →  DELETE report_schedule_definitions
(worker)                ←  ScheduleStore protocol        ←  due_schedules/open_run/finish_run/record_outcome
```

| Property | Canonical behaviour | Where enforced |
|---|---|---|
| Frequency vocabulary | `weekly`, `monthly`, `quarterly`, `annual` | schema CHECK + `domain.report_schedule.FREQUENCIES` |
| Report-type vocabulary | `annual` only | schema CHECK + `SCHEDULE_REPORT_TYPES`, drift-guarded against the engine's supported set |
| Run/result vocabulary | runs `running/succeeded/failed/skipped`; schedule `last_result` `succeeded/failed/skipped` | schema CHECKs + domain constants |
| Due selection | persisted `next_run_at <= now`, `is_active`, ordered by due time, bounded by limit | repository SQL |
| Idempotency | `UNIQUE (schedule_id, scheduled_for)`; `open_run` uses `ON CONFLICT DO NOTHING` | schema + repository |
| Run immutability | one transition `running → terminal`, no DELETE | schema guard `ct02_report_schedule_run_guard` |
| Retry/backoff | `failure_count` + `retry_policy{max_attempts,backoff_minutes}`, paused when exhausted | domain arithmetic + runner + repository state write |
| Report/version linkage | `report_generation_queue.id` + `report_versions.id`, produced by the normal engine | producer + schema FKs |
| Audit | `correlation_id = schedule id`, `entity_id = schedule id`, category `report`, actor = the person (lifecycle) or `system` (run) | services + the runner's audit sink |
| Persistence interfaces | `ScheduleStore`, `ReportProducer`, `AuditSink` injected; the runner still holds no client | CT-IMPLEMENT-02 architecture, preserved |

### 4.1 Legacy → canonical mapping

| Legacy component | Replaced by | Implemented? | Persisted? | Route-wired? | Frontend caller? | E2E verified? |
|---|---|---|---|---|---|---|
| `report_schedules` table | `report_schedule_definitions` + `report_schedule_runs` (CT-IMPLEMENT-02 migration) | yes | yes | yes | **no** | **yes** (§18) |
| `POST/GET/DELETE /api/reports/schedule` | same URLs, delegating to the canonical service; canonical surface `/api/v3/reports/schedules*` | yes | yes | yes | no | **yes** |
| `daily` frequency advertisement | canonical vocabulary generated from `FREQUENCIES` | yes | n/a | yes | no | **yes** |
| `ReportScheduleCreate` (`day_of_week`/`format`/`filters`) | `ScheduleCreateIn` / `LegacyScheduleCreate` (canonical fields, `extra="forbid"`) | yes | n/a | yes | no | **yes** |
| `report_history` share register (`metadata.shares`) | `report_shares` + `report_share_access_events` | yes | yes | yes | no | **yes** |
| `POST /api/reports/{id}/share`, `GET /api/reports/shared` | same URLs, delegating; canonical surface `/api/v3/reports/{id}/shares*`, `/shares/received` | yes | yes | yes | no | **yes** |
| `calculate_next_run()` | `domain.report_schedule.next_occurrence` | yes | n/a | used by the service | n/a | **yes** (via create) |

---

## 5. `report_schedules` disposition

**Retired. Not recreated. No compatibility table was added, and no migration was
written to satisfy a stale reference.**

* The canonical model uses different names (`report_schedule_definitions`,
  `report_schedule_runs`) precisely so a future reader cannot mistake it for the
  retired table (the CT-IMPLEMENT-02 migration says so itself).
* Every application reference is gone (§3). The only remaining mentions are
  documentation prose and the migrations' own fail-closed guards.
* The E2E target proves absence structurally: `to_regclass('public.report_schedules')
  IS NULL` and `IS NULL` for `report_history`, asserted at the start of the suite
  (§18.1). Because the table does not exist, **any** surviving code path that
  queried it would fail loudly rather than silently pass.

---

## 6. F-1 root cause

`backend/routes/reports.py` was written against a legacy schema in which
`report_schedules` and `report_history` existed. No canonical migration ever
created them (CT-SCHEMA-03 SCM-005/006), so once the canonical chain was applied:

* the four `report_schedules` accesses raised a PostgREST "relation does not
  exist" error, which the handlers converted into a `500` — the create, list and
  delete paths of `/api/reports/schedule*` could not work at all;
* the three `report_history` accesses did the same for `POST /{id}/share` and
  `GET /shared`, and additionally read the *whole* table before filtering in
  Python.

There was also no canonical replacement at the time (no share register, no
schedule model), which is why CT-IMPLEMENT-01/02 escalated PD-1/PD-2. After
CT-IMPLEMENT-02 those canonical objects exist; this change-set points the
application at them. **Root cause: application code targeting a retired schema
that the canonical chain deliberately does not contain** — not a missing table.

---

## 7. F-2 root cause

`GET /api/reports/schedule/frequencies` returned a **hard-coded literal list**
(`daily`, `weekly`, `monthly`, `quarterly`) that was never derived from the
persistence model. The canonical table's CHECK accepts
`weekly|monthly|quarterly|annual`, so the endpoint advertised a value that could
not be stored and omitted one that could (`annual`). CT-SCHEMA-03/CT-IMPLEMENT-02
therefore recorded it as a mismatch and left it in place while the surface was
non-functional. **Root cause: a hand-written vocabulary with no link to the schema
CHECK.**

---

## 8. Canonical frequency contract

| Question | Answer |
|---|---|
| Persistable values | `weekly`, `monthly`, `quarterly`, `annual` (exactly `report_schedule_definitions_frequency_check`) |
| Values the API advertises | the same four, generated from `domain.report_schedule.FREQUENCIES` via `services.report_schedules.canonical_frequencies()` |
| `daily` | **not canonical.** It is not advertised, it is refused at the request boundary with a message that names the retired advertisement, and the database refuses it too (`LEGACY_UNSUPPORTED_FREQUENCIES` records the history in code) |
| Backwards-compatible alias | **none added.** An alias would have to invent a persisted meaning for `daily` (which the schema rejects); the endpoint was corrected instead, on both surfaces |
| Both surfaces | `GET /api/v3/reports/schedules/frequencies` (canonical) and `GET /api/reports/schedule/frequencies` (legacy, delegating, `Deprecation` header) return the same list |
| Tests | `test_frequency_api_matches_the_canonical_vocabulary` (E2E), `test_frequencies_endpoint_advertises_the_canonical_vocabulary` (unit), `test_canonical_frequencies_advertise_only_persistable_values` (unit), plus the invalid-value tests (`daily` → 422) |

---

## 9. Schedule route changes

| Route | Before | After |
|---|---|---|
| `POST /api/v3/reports/schedules` | — | new: canonical create (org owner/admin), 201 |
| `GET /api/v3/reports/schedules` | — | new: org-scoped page (`limit`, `offset`, `is_active`) + total + frequencies |
| `GET /api/v3/reports/schedules/frequencies` | — | new: canonical vocabulary |
| `GET /api/v3/reports/schedules/{id}` | — | new: schedule + its 20 most recent runs |
| `GET /api/v3/reports/schedules/{id}/runs` | — | new: bounded execution history |
| `POST /api/v3/reports/schedules/{id}/pause` \| `/resume` | — | new: audited state changes |
| `DELETE /api/v3/reports/schedules/{id}` | — | new: audited; **409** when the schedule has run |
| `GET /api/reports/schedule/frequencies` | hard-coded list with `daily` | canonical vocabulary + `Deprecation`/`Link` |
| `POST /api/reports/schedule` | `report_schedules` insert (500) | canonical create via the service |
| `GET /api/reports/schedule` | `report_schedules` select (500) | canonical list via the service |
| `DELETE /api/reports/schedule/{id}` | `report_schedules` delete (500) | canonical delete via the service (409 when it has run) |

**Route declaration order matters and was corrected:** Starlette matches routes in
declaration order, so the literal `GET /api/v3/reports/schedules` had to be
declared **before** the pre-existing parameterised `GET /api/v3/reports/{report_id}`
— otherwise the parameterised route swallowed it and passed
`report_id='schedules'` to the detail handler (observed as
`DataError: invalid input for query argument $1: 'schedules'` during E2E). The
whole CT-IMPLEMENT-03 block now precedes the parameterised report routes; route
count is unchanged (27) and the module is the same length, so nothing else moved.

**Authority (enforced server-side, on both surfaces):** reads require organisation
membership; writes require organisation owner/admin — mirroring the RLS policies
the schema declares (`p8_disclosure_is_org_member` / `_is_org_admin`). Processing
Entity staff and CarbonTally internal staff are refused as customer-organisation
authorities, consistent with the existing report-lifecycle boundary.

**Documented contract change on the legacy URLs:** the request body is now the
canonical one (`reporting_year`, `run_time`, `timezone`, `recipients`, optional
`period_start`/`period_end`; `extra="forbid"`), and responses describe the
**canonical persisted row** (`shape_schedule`), not the retired
`ReportScheduleResponse`. A stale payload is refused with a described 422 rather
than silently half-applied. No frontend caller exists (§16), so no shipped client
breaks.

---

## 10. Schedule persistence changes

`backend/data/report_schedules.py` (new) is the canonical persistence and also the
runner's `ScheduleStore`:

| Method | Guarantee it relies on |
|---|---|
| `create` | the schema trigger requires a due time on an active schedule; `retry_policy` defaults to the migration's own JSONB default |
| `get_for_org` / `list_for_org` / `count_for_org` | tenant isolation is part of the read (another org's id resolves to `None`) |
| `set_active` | pause stamps `paused_at` and **preserves** `next_run_at`; resume clears `paused_at` — the `is_active OR paused_at IS NOT NULL` CHECK holds both ways |
| `delete` | returns whether a row was removed; `has_runs` lets the service refuse before the cascade trips the run guard |
| `due_schedules` | persisted due selection, oldest first, bounded |
| `open_run` | `ON CONFLICT (schedule_id, scheduled_for) DO NOTHING` → idempotency decided by the UNIQUE key, not by Python |
| `finish_run` | `WHERE status = 'running'` → at most one transition; terminal statuses only |
| `record_outcome` | writes `next_run_at`, `last_result`, `failure_count`, `is_active`, `last_error`, `paused_at` verbatim |
| `list_runs` / `get_run` | real execution history |

**Persistence-architecture constraint preserved:** the repository is injected into
the runner; the domain/runner still hold no client, so they cannot bypass RLS or
the report workflow.

### 10.1 Finding N-1 (recorded, app-layer handled) — a schedule that ran cannot be deleted

The canonical schema makes `report_schedule_runs` append-only for **every** role
(`ct02_report_schedule_run_guard` refuses DELETE), while
`report_schedule_definitions` deletes its runs by `ON DELETE CASCADE`. Deleting a
schedule that has executed therefore breaches the guard and fails at the database
level — and the same cascade means **deleting the owning organisation** fails too
(§20.3). Handling implemented now: `has_runs` + a described **409** ("this schedule
has execution history, which is immutable; pause it instead of deleting it"), so
the caller sees a business answer rather than a 500. The organisation-deletion
implication is an architecture decision, not an application one (§20.3).

---

## 11. Schedule runner integration

`backend/services/report_schedule_runner.py` (CT-IMPLEMENT-02) is **unmodified**;
what was missing was (a) real persistence, (b) a real producer, and (c) something
that actually ticks.

| Piece | Implementation |
|---|---|
| Persistence | `ReportSchedulesRepository` structurally satisfies the runner's `ScheduleStore` |
| Producer | `backend/services/report_schedule_producer.py` — `CanonicalReportProducer` creates the `report_generation_queue` row (QUEUED), marks it GENERATING, runs the authoritative `ReportGenerationEngine` against that row, records the `report_versions` snapshot, and returns `ProducedReport(report_id, report_version_id, result_summary)`. A failure is persisted to the queue row and re-raised, so the run is recorded as `failed` with a real code and the retry policy applies |
| Audit sink | `services.report_schedules.build_audit_sink(repos)` writes one canonical `audit_trail` entry per outcome with `correlation_id = schedule id` |
| Trigger | `backend/workers/report_schedules.py` — a lifespan-managed loop (mirroring `workers.automatic_processing`), started/stopped from `main.py`, with `tick()` and `run_once()`; disabled by `CT_REPORT_SCHEDULES_ENABLED=0` |
| Same engine as the API | `api.dependencies.build_report_engine()` was factored out of `get_report_engine()` so the worker composes **the same** engine the reporting API uses (no second, drifting copy) |

No skip policy was invented: `CanonicalReportProducer` never returns `None` (the
runner would record that as a failure). A product decision on "when is a scheduled
report not worth producing" would be needed before adding one — recorded as a
non-gate observation, not implemented.

---

## 12. Share-route analysis and implementation

Legacy shape: `POST /api/reports/{report_id}/share` read `report_history`,
appended `{id, shared_with, permission, shared_by, created_at, expires_at}` into
that row's `metadata.shares` JSONB and wrote it back; `GET /api/reports/shared`
read the **entire** `report_history` table and filtered in Python; `GET /shared`
also resolved `auth.users` per share. Report identity was `report_history.id` and
nothing was version-aware.

Canonical model (CT-IMPLEMENT-02 / PD-1), which the schema itself enforces:

| Property | Contract |
|---|---|
| Identity | version-bound: `report_version_id NOT NULL`, never re-pointed |
| Eligibility | a version's lifecycle state must be `APPROVED` (or `FINAL`) — enforced by trigger |
| Tenant | `organization_id NOT NULL`, must equal the version's owning organisation — enforced by trigger |
| Recipient | at least one of `recipient_user_id` / `recipient_email` (lower-cased) |
| Permission | `view` or `download` |
| Expiry | validated at creation, evaluated server-side |
| Revocation | one-way update, self-describing (`revoked_by` + `revocation_reason`); the register keeps the history |
| Duplicates | `report_shares_active_recipient_key` allows one live share per (version, recipient) → re-share = revoke + share |
| History | `report_share_access_events` append-only, vocabulary `created/access/download/revoked/denied` |
| No public URL | no public token column; a hashed link token must still be redeemed by an authenticated recipient |

**Is sharing fully specified?** The identity/eligibility/recipient/permission/
expiry/revocation/history contract is fully specified **by the schema**, so the
share *register* was implemented: create (201), list, revoke (200), access history,
and the recipient's own `GET /shares/received`. `POST`/`GET /api/reports/{id}/share`
and `GET /api/reports/shared` now delegate to it.

**What was deliberately not implemented:** *consuming* a share — returning the
report content to a recipient and recording `access`/`download`/`denied` events.
That needs a delivery/download policy (who may read version content — including a
recipient outside the organisation — and what a signed URL may be issued for;
AGENTS.md §68) that no ratified decision covers. The event vocabulary for it
already exists, and nothing was invented in its place. Recorded as **G-2** (§20).

**Version binding for the report-scoped legacy URL (implementation decision, not
policy):** PD-1 sharing is version-bound, so `POST /{report_id}/share` without an
explicit `version_number` binds to the report's **current** version, and refuses
with **409** when that version is not immutable. The alternative — choosing some
other version, or sharing a draft — would be inventing policy.

| Legacy route | Now |
|---|---|
| `POST /api/reports/{id}/share` | delegates (canonical body + optional `version_number`); response describes the persisted share row; `Deprecation`/`Link` |
| `GET /api/reports/shared` | delegates to the canonical recipient-scoped read |
| `POST /api/v3/reports/{report_id}/shares` | new canonical create (org owner/admin) |
| `GET /api/v3/reports/{report_id}/shares` | new canonical register (revoked history included) |
| `POST /api/v3/reports/shares/{id}/revoke` | new canonical revocation (reason required) |
| `GET /api/v3/reports/shares/{id}/access-history` | new append-only history |
| `GET /api/v3/reports/shares/received` | new recipient view (own identity only) |

---

## 13. Frontend reconciliation (Phase 5)

Searched `frontend/src/**` (the V3 application and the public site) and `admin/`:

| Search | Result |
|---|---|
| `reports/schedule`, `schedule/frequencies`, `report_schedules`, `report_history` | **zero hits** in `frontend/src/**` |
| `daily` as a schedule frequency | **zero hits** |
| share calls (`/share`, `shared_with`, `/shared`) | zero report-share hits; the only `share` matches are unrelated prose/helpers ("shared contract", "shared style guide") |
| the V3 reports surface | calls `/api/v3/reports/...` only (`getReport`, `versions`, lifecycle actions, `pdf`, `download`) — a different router from the legacy `/api/reports/*` |

**Conclusion: no active frontend caller exists for the legacy schedule/share
contract, and none needed updating.** The task's instruction "do not silently
remove existing functionality" is therefore satisfied by *preserving the legacy
URLs* as delegating compat routes rather than deleting them, and no UI work was
invented for features the frontend does not have (schedule management, sharing).

Not done (and not invented): building schedule/share UI. That is product scope,
not reconciliation.

---

## 14. Tests

### 14.1 Unit (DB-free) — 66 new tests, all passing

| File | Tests | What it holds to account |
|---|---|---|
| `tests/unit/services/test_report_schedules_service.py` | 24 | canonical persistence values; due-time arithmetic at the configured local time; recipient normalisation; **`daily` and every non-canonical frequency refused with nothing persisted**; name/type/year/timezone/run-time/period/recipient validation; audit content and `correlation_id`; tenant-scoped reads; pause preserves the due time; resume keeps a future due time and recomputes a past one; delete scoping; **delete refused for a schedule that has run**; canonical frequency list; the runner's audit sink |
| `tests/unit/services/test_report_schedule_producer.py` | 6 | the QUEUED→GENERATING→engine sequence against one queue row; request carries the schedule configuration and period; version snapshot recorded; engine failure persisted and re-raised; a `mark_failed` failure never masks the original error; the producer never returns `None` |
| `tests/unit/services/test_report_shares_service.py` | 16 | version binding (current and explicit); mutable versions refused with nothing written; unknown version/report; permission/expiry/recipient validation; duplicate live grant → conflict; `created` event + audit; revocation requires a reason and is one-way; cross-tenant revocation denied; received-shares filtering (revoked, expired); history; JSON shaping |
| `tests/unit/routes/test_ct03_legacy_canonical_delegation.py` | 20 | **no module under `backend/` outside `tests/` accesses a retired table** (PostgREST `from_(...)` and SQL access patterns, runtime-wide); the legacy router names no retired table; legacy delegation records the canonical call; frequencies are canonical; stale payloads refused; authority enforced (owner/admin/member/viewer/PE/internal/other-org); canonical routes registered; `SCHEDULE_REPORT_TYPES ⊆ SUPPORTED_REPORT_TYPES` drift guard |

Existing CT-IMPLEMENT-02 suites still pass unchanged: `test_report_schedule.py`
(27) and `test_report_schedule_runner.py` (11) — 104 tests in the six files run
together, `EXIT=0`.

### 14.2 Full unit suite

`python -m pytest tests/unit -q`: **7 failures, all pre-existing and proven so by
running the same files at the starting SHA in a `git worktree`** (§14.3). No new
failure was introduced.

| Pre-existing failure | Why it fails | Caused by |
|---|---|---|
| `test_d17_provider_ownership_migration_revision.py::…migration_ordering_is_unchanged` | asserts the newest migration is the D17 revision | CT-IMPLEMENT-02 added 20261021/22/23 |
| `test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | pins I1 as the latest migration | ditto |
| `test_i2_insight_authorization_contracts.py::…is_the_latest_and_scoped_to_one_policy` | ditto | ditto |
| `test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | ditto | ditto |
| `test_extraction_suggestions.py` (3 tests) | engine suggestion expectations | unrelated/pre-existing |

### 14.3 Attribution evidence

```
$ git worktree add /tmp/ct03_base 21310af      # the starting SHA, no CT-IMPLEMENT-03 changes
$ (cd /tmp/ct03_base/backend && pytest tests/unit/data/test_d17_provider_ownership_migration_revision.py \
   tests/unit/data/test_i1_insight_migration.py tests/unit/data/test_i2_insight_authorization_contracts.py \
   tests/unit/data/test_p17_migrations.py tests/unit/engines/test_extraction_suggestions.py -q)
→ FAILED … (the same 7)   EXIT=1
```
The worktree was removed afterwards; no repository state was reset.

---

## 15. Disposable-database E2E results (Phase 7)

### 15.1 Target and its provenance

| Property | Value |
|---|---|
| Host/port | `127.0.0.1:55481` — disposable container `ct_impl02b_pg` |
| Database | `ct_impl03_e2e`, a **clone of the canonical database** created with `CREATE DATABASE ct_impl03_e2e TEMPLATE postgres` |
| Schema provenance | the CT-IMPLEMENT-02 from-zero rebuild (92 canonical migrations, storage platform layer, D32 operator step), already verified `94 pass / 0 fail` |
| Tables | 149 public tables; the four canonical schedule/share tables present; `report_schedules` and `report_history` **ABSENT** |
| F-046-1 posture | the fixture refuses the main databases and any name matching `qa`/`demo`/`investor`/`prod`/`live`, and requires a `ct_*` clone; the clone contains no data whose preservation matters |
| Destructiveness | **none** — one organisation + two users per test, deleted afterwards (§15.3) |

### 15.2 Command and result

```bash
cd backend
INTEGRATION_DATABASE_URL="postgresql://supabase_admin:***@127.0.0.1:55481/ct_impl03_e2e" \
  python -m pytest tests/integration/test_ct03_report_schedule_share_canonical.py -q -p no:cacheprovider
# ..........  EXIT=0      (10 tests, all passing; run twice with the same result)
```

| # | Test | What it proves with real HTTP + real PostgreSQL |
|---|---|---|
| 1 | `test_the_target_is_a_disposable_clone_with_the_canonical_schema` | the target is a `ct_*` clone; the four canonical tables exist; **both retired tables are absent** |
| 2 | `test_frequency_api_matches_the_canonical_vocabulary` | the API advertises exactly the four persistable frequencies |
| 3 | `test_schedule_create_read_pause_resume_delete_persist_canonically` | create (201) → row in `report_schedule_definitions` with the canonical values (recipients JSONB, `run_time`, `next_run_at`, `created_by`); audit row keyed by schedule id; list; detail; pause (`is_active=false`, `paused_at` set); resume; delete → row gone; second delete → 404 |
| 4 | `test_schedule_validation_and_authority_are_enforced_over_http` | `daily`/unknown timezone/empty recipients/unsupported report type → 422 **and nothing persisted**; member may read but not write (403); another organisation's member refused (403) |
| 5 | `test_the_runner_executes_a_due_schedule_and_records_real_artefacts` | persisted `next_run_at` in the past → `run_due()` selects it, the **real engine** produces a real `report_generation_queue` row with content plus a `report_versions` snapshot; the run records `succeeded` with both ids; schedule state advances; one audit entry with `correlation_id = schedule id` |
| 6 | `test_a_repeated_tick_cannot_create_a_second_run_or_report` | the same due slot re-claimed (`duplicate_slots == 1`) with still exactly **one** run row and **one** report; and deleting a schedule that has run → **409**, row surviving |
| 7 | `test_sharing_and_revoking_persist_the_canonical_share_register` | share (201) → `report_shares` row bound to the version, with a `created` access event and an audit entry; register; access history; revoke → one-way with the reason preserved and a `revoked` event; a second revoke does not rewrite the first |
| 8 | `test_sharing_a_mutable_version_is_refused_and_persists_nothing` | sharing a `DRAFT` version → 409, no share row |
| 9 | `test_legacy_schedule_surface_delegates_and_persists_canonically` | the legacy `/api/reports/schedule*` surface returns the canonical vocabulary with a `Deprecation` header, persists to the canonical table, lists and deletes canonically |
| 10 | `test_legacy_share_surface_is_version_bound_and_canonical` | the legacy share route writes a canonical, version-bound share; `/api/reports/shared` returns it to its recipient; a plain member cannot share (403) |

### 15.3 Post-run database state (disposable clone)

| Table | Rows | Note |
|---|---|---|
| `report_schedule_definitions` | 3 | the schedules that executed (undeletable by design — §10.1) |
| `report_schedule_runs` | 2 | real executions |
| `report_shares` | 8 | retained because their append-only access events block the cascade |
| `report_share_access_events` | 11 | append-only |
| retired `report_schedules` | table absent | `to_regclass(…) → NULL` |
| `audit_trail` entries | not deletable | append-only by design |

Teardown records exactly which rows the canonical guards retain instead of
disguising them; the clone is discarded after the run, and nothing outside the
rows this module created was touched.

### 15.4 Finding N-2 — the canonical audit guard breaks the shared integration fixture

While setting this up, the **existing** suite fixture failed immediately:

```
tests/integration/conftest.py:139: in pool
    await conn.execute(f"TRUNCATE {tables} RESTART IDENTITY CASCADE")
E   asyncpg.exceptions.RaiseError: append-only ledger (CT-IMPLEMENT-02):
    TRUNCATE of public.audit_trail is not permitted
    (set ct.audit_purge_authorised=on only from an authorised purge run)
```

`tests/integration/conftest.py` truncates `audit_trail` (with
`report_versions`, `report_generation_queue`, …) as destructive session setup.
CT-IMPLEMENT-02's append-only hardening now refuses that **on any canonical
database**, so *every* integration suite using that fixture cannot start against a
canonical schema. It is a cross-unit integration gap between the CT-IMPLEMENT-02
hardening and the CT-era harness, not specific to this task — and it was not
worked around by weakening the guard:

* this module defines its own **non-destructive** pool fixture, which is why the
  E2E above runs at all;
* the guard was **not** disabled and no `ct.audit_purge_authorised` exception was
  granted anywhere;
* the general fix (an explicit authorised-purge path for disposable targets, or a
  non-destructive default fixture) is recorded in §20.

---

## 16. Evidence that the canonical runtime no longer depends on `report_schedules`

Four independent lines of evidence:

1. **Static (runtime-wide).** `tests/unit/routes/test_ct03_legacy_canonical_delegation.py
   ::test_no_runtime_module_accesses_a_retired_report_table` walks every `*.py`
   under `backend/` except `tests/` and fails if any module matches a retired-table
   **access**: `from_('report_schedules')`, `from_('report_history')`,
   `FROM public.report_schedules`, `FROM public.report_history`,
   `INTO public.report_schedules`, `UPDATE public.report_history`,
   `DELETE FROM public.report_history`. Result: **zero offenders**. (A module,
   handler or docstring that merely contains the words is not an access, and the
   assertion says so.)
2. **Static (the legacy module).** The same file asserts that
   `backend/routes/reports.py` contains **no** mention of `report_history` at all
   and no retired-table access; the patch that produced it asserted this before
   writing the file (`AssertionError` if any access survived).
3. **Structural (the database).** The E2E target has no `report_schedules` and no
   `report_history` (`to_regclass(…) IS NULL`, asserted by the suite). Any code
   path that still queried them would raise, so the passing E2E is itself
   evidence that the exercised paths do not.
4. **Behavioural.** Both surfaces' create/list/pause/resume/delete and share/revoke
   paths persisted to and read from the canonical tables **in the same run**
   (§15.2), with assertions on the rows themselves rather than on status codes.

No `report_schedules` compatibility table was created; no migration was added by
this change-set at all.

---

## 17. PO-gated and out-of-scope items (deliberately left unresolved)

| ID | Item | Class | Why it is not done here |
|---|---|---|---|
| **G-1** | **R-6 — audit call-site classification** (which audits are fail-closed vs log-and-continue) | `IMPLEMENTABLE_AFTER_PO_DECISION` | unchanged from CT-IMPLEMENT-02. The audits added here follow the **established best-effort pattern** of the surrounding reporting module (lifecycle + share + schedule events all log-and-continue); no classification was invented |
| **G-2** | **Consuming a share** — returning report content to a recipient and recording `access`/`download`/`denied` | `IMPLEMENTABLE_AFTER_PO_DECISION` | needs a delivery/download policy: may a recipient outside the organisation read version content, and under what signed-URL terms (AGENTS.md §68)? The schema's event vocabulary exists; no policy does |
| **G-3** | **Organisation deletion vs immutable history** — an organisation with a run-bearing schedule (or with shares) cannot be deleted, because the cascades trip the append-only run/access guards | `IMPLEMENTABLE_AFTER_PO_DECISION` | an architecture decision (soft-delete/anonymise an organisation, purge-and-record, or accept "cannot delete"). Detected here by E2E evidence, not guessed at |
| **G-4** | **Harness fix for N-2** — the shared integration `pool` fixture cannot start against a canonical database | `IMPLEMENTABLE_AFTER_PO_DECISION` | choosing between an explicitly authorised purge GUC for disposable targets and a non-destructive default fixture is a test-infrastructure policy decision; this task avoided both by using its own fixture |
| **R-1** | ~37 remaining legacy factor read sites | unchanged | out of scope (CT-IMPLEMENT-01/02 scope) |
| **R-3** | source-to-report provenance suite | unchanged | out of scope |
| **R-5** | documentation truth (`API_ENDPOINTS.md` still describes `get_report_schedules()`) | `DOCUMENTATION_ONLY` | a docs pass; safe to do, but a separate unit |
| **R-7** | retention enforcement | unchanged | PO-gated (needs a data-class inventory) |
| **R-8** | feature catalogue regeneration | unchanged | out of scope |
| **R-9** | seeded tenant-isolation negative suite | partially served here: org-scoped reads, cross-org refusals and cross-tenant share refusal are asserted per-operation (unit + E2E); the seeded bulk suite remains open |
| **R-10/R-11** | audit coverage gaps; live migration | unchanged | R-11 remains an **EXTERNAL BLOCKER** (no production target, no verified recovery point) |

---

## 18. Known limitations (stated, not hidden)

1. **Delivery is not implemented.** A schedule executes, produces a canonical
   report + version, records real outcomes and audits them; recipients are stored
   and validated as configuration, but **no email/notification is sent**. Sending
   is part of G-2's policy area (and inherits the existing email provider rules).
2. **Share consumption is not implemented** (G-2). The `access`, `download` and
   `denied` event types exist in the schema and are unused by this change-set.
3. **Failure/retry paths are unit-tested, not E2E-tested.** The E2E covers
   success, idempotency and the undeletable-schedule refusal against the real
   engine; forcing a real engine failure would need fault injection. The runner's
   backoff, retry-exhaustion pause and skip semantics remain covered by
   CT-IMPLEMENT-02's 11 unit tests plus this unit suite.
4. **PostgreSQL returns `UUID`/`datetime` objects** where the JSON round-trip held
   strings; several E2E assertions compare explicitly (`str(...)`). Recorded
   because it is a real E2E-writing hazard.
5. **The engine's `page_count` is absent for an organisation with no emissions
   data**, so the produced run summary records `page_count: 0`. Nothing is
   invented: the field is absent in the persisted content, and 0 is its only
   faithful reading.
6. **Multi-instance execution.** The worker runs inside the API process; if the
   deployment ever runs several instances, each will tick. Idempotency is enforced
   by the per-slot UNIQUE key (verified), so duplicates cannot occur, but the
   excess ticks are work. A single-scheduler deployment is a deployment decision.
7. **No UI** for schedule management or sharing was added (none is requested by
   PD-1/PD-2, and no frontend caller exists).
8. **Legacy response shapes changed** on the surviving legacy URLs (§9). Documented
   rather than silent, and no shipped caller exists.
9. **Rows that the canonical guards make immutable are not removable** (run rows,
   audit rows, share access events, and therefore the parents of those rows). Any
   future "reset demo data" procedure must account for this (see G-3).
10. **`API_ENDPOINTS.md` was not updated** (R-5); it still lists
    `get_report_schedules()` among the legacy handlers and does not yet describe
    the canonical schedule/share routes.

---

## 19. Production boundary

**Production was untouched.** Nothing was deployed, pushed, migrated, or
reconfigured:

| Surface | Action |
|---|---|
| GitHub | **no push** — the four commits are local to `p8-release-reconciled` |
| Render | not contacted |
| Vercel | not contacted |
| Production Supabase (database, Auth, Storage) | not contacted; no production credentials were used |
| Production Storage | not contacted; no signed URL was generated or logged |
| Investor demo database / identities | **not touched** (the E2E ran only against the disposable clone `ct_impl03_e2e` on `127.0.0.1:55481`) |
| Local Supabase main database (`:54326`/`:54426`) | not touched |
| Migrations | **none added or applied**; the two CT-IMPLEMENT-02 migrations were already committed |
| Environment files (`e2e/environment/**`, `supabase/config.toml`, `.gitignore`, `.env`) | not modified (they remain the pre-existing uncommitted CT-SCHEMA-02 unit) |

The only infrastructure used was a **disposable container the project already
labelled `ct_impl02b`** and a database cloned inside it. No durable environment
was read or written.

---

## 20. Independent-verification status

**INDEPENDENT VERIFICATION NOT PERFORMED.**

* Every result in this report comes from the implementing agent's own harness.
* `IMPLEMENTED` ≠ `TESTED` ≠ `VERIFIED` ≠ `ACCEPTED` (AGENTS.md §73). The statements
  supported here are "implemented", "unit-tested" and "E2E-verified on a
  disposable canonical database **by the implementer**".
* No OHD/independent pass has re-tested the affected workflows, and no PO
  acceptance has been sought.
* The legacy contract changes (§9) and the new canonical routes have **not** been
  reviewed by anyone other than the implementer.
* The two findings raised here (N-2 harness/guard incompatibility; the G-3
  organisation-deletion conflict) have **not** been independently reproduced.

---

## 21. Mandatory final verification — explicit answers

| # | Question | Answer |
|---|---|---|
| 1 | Does any ACTIVE_RUNTIME code still query `report_schedules`? | **No.** |
| 2 | If yes, where and why? | n/a. The seven legacy accesses were replaced (§3); the runtime-wide static assertion reports zero offenders (§16.1). |
| 3 | Does the canonical schedule route persist to the canonical schedule structure? | **Yes** — `report_schedule_definitions` (+ `report_schedule_runs` when it executes), asserted row-by-row in E2E tests 3, 5, 6 and 9. |
| 4 | Does the schedule runner actually execute through the route/data-layer integration? | **Yes** — a schedule created over HTTP is selected from its persisted `next_run_at` and executed by the real runner with the real repository, producer and report engine; the run row, report row, version row and audit row are then asserted (E2E test 5, §15.2). |
| 5 | What exact frequency values can be persisted? | `weekly`, `monthly`, `quarterly`, `annual`. |
| 6 | What exact frequency values does the API advertise? | The same four, on both surfaces. |
| 7 | Can the API advertise `daily` while persistence rejects it? | **No.** `daily` is neither advertised nor accepted; it is refused with a described 422 before any write. |
| 8 | Does report sharing use the canonical report/version architecture? | **Yes** — a share is bound to a `report_versions` row of a `report_generation_queue` report, validated by the schema trigger, and refused (409) for mutable versions. |
| 9 | Is report sharing blocked by R-6 or another PO decision? | **The register is not.** R-6 (audit classification) does not gate it; the audits follow the module's existing best-effort pattern. **Consuming** a share is PO-gated (G-2) and was left unimplemented. |
| 10 | Are any frontend callers still using legacy schedule/share contracts? | **No** — zero callers (§13). |
| 11 | What was verified with real disposable PostgreSQL? | Target identity and schema; canonical create/read/pause/resume/delete persistence; due selection; real execution through the engine; per-slot idempotency; report+version linkage; audit correlation; the undeletable-schedule refusal; share create/list/revoke/access-history; mutable-version refusal; both legacy surfaces' delegation and persistence (§15). |
| 12 | What remains only unit-tested? | Runner failure/retry/backoff/pause semantics; producer failure persistence; the runner's audit-failure resilience; the `SCHEDULE_REPORT_TYPES ⊆ engine` drift guard. |
| 13 | What remains unverified? | Independent verification of anything above; delivery/notification (not implemented); share consumption (not implemented); multi-instance ticking; production behaviour; R-1/R-3/R-5/R-7/R-8/R-9/R-10/R-11; the general harness fix for N-2. |
| 14 | Was production untouched? | **Yes** — see §19. |
| 15 | Was GitHub untouched? | **Yes** — no push, no history rewrite, no reset. |

---

## 22. Git state

| Property | Value |
|---|---|
| Branch | `p8-release-reconciled` |
| Starting SHA | `21310afae69cace6b67985eda7e817b0aee1c33b` (CT-IMPLEMENT-02's last commit) |
| Ending SHA | **`eff1c56`** — the CT-IMPLEMENT-03 report commit, i.e. the branch tip once the implementation, tests and this report were in place. The only commit after it is the one that adds this sentence (a bookkeeping note carrying no code) |
| Pushed | **no** |
| History rewritten / reset / amended | **no** (`git reset`, `git clean`, force-push and amend were not used) |

| Commit | SHA | Subject |
|---|---|---|
| 1 | `a74359e` | `CT-IMPLEMENT-03: canonical schedule/share data layer, services and producer` |
| 2 | `a599b24` | `CT-IMPLEMENT-03: canonical schedule/share routes, legacy delegation, runner worker` |
| 3 | `429df43` | `CT-IMPLEMENT-03: unit and disposable-DB E2E coverage for schedule/share canonicalization` |
| 4 | `eff1c56` | `CT-IMPLEMENT-03: implementation report` (**ending SHA**) |

Files changed by this change-set:

```
new  backend/data/report_schedules.py
new  backend/data/report_shares.py
new  backend/services/report_schedules.py
new  backend/services/report_shares.py
new  backend/services/report_schedule_producer.py
new  backend/workers/report_schedules.py
mod  backend/data/__init__.py                 (exports)
mod  backend/domain/report_schedule.py        (SCHEDULE_REPORT_TYPES — additive)
mod  backend/api/dependencies.py              (bundle wiring + build_report_engine factored out)
mod  backend/api/v3_reports.py                (canonical schedule/share routes; block reordered)
mod  backend/routes/reports.py                (retired-table access removed; canonical delegation)
mod  backend/main.py                          (worker lifespan start/stop)
new  backend/tests/unit/services/test_report_schedules_service.py
new  backend/tests/unit/services/test_report_schedule_producer.py
new  backend/tests/unit/services/test_report_shares_service.py
new  backend/tests/unit/routes/test_ct03_legacy_canonical_delegation.py
new  backend/tests/integration/test_ct03_report_schedule_share_canonical.py
new  docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-03-REPORT-20260928.md
```

**Pre-existing changes left exactly as they were** (not absorbed, not reverted,
not committed by this unit): the CT-SCHEMA-02 environment-layer files
(`e2e/environment/scripts/apply_migrations.sh`, `bootstrap.sh`, `reset.sh`,
`d32_storage_operator.sql`, `d32_search_path_regression.sh`,
`verify_d32_policy_semantics.sql`, `e2e/environment/README.md`,
`e2e/environment/supabase/config.toml`, `e2e/environment/supabase/migrations`
(symlink), `.gitignore`), the uncommitted D32 migration revision
(`supabase/migrations/20260823000000_d32_private_documents_storage.sql`), and the
large body of untracked audit/architecture documents.

---

## 23. Required-section index

| Required item | Where |
|---|---|
| 1 Task ID | header |
| 2 Objective | §1 |
| 3 Starting SHA | header, §22 |
| 4 Ending SHA | §22 |
| 5 CT-IMPLEMENT-02 evidence consumed | §2 |
| 6 Legacy schedule/share reference inventory | §3 |
| 7 Canonical schedule architecture | §4, §4.1 |
| 8 `report_schedules` disposition | §5 |
| 9 F-1 root cause | §6 |
| 10 F-2 root cause | §7 |
| 11 Canonical frequency contract | §8 |
| 12 Schedule route changes | §9 |
| 13 Schedule persistence changes | §10 (+ §10.1 finding N-1) |
| 14 Schedule runner integration | §11 |
| 15 Share-route analysis | §12 |
| 16 Frontend reconciliation | §13 |
| 17 Tests | §14 |
| 18 Disposable DB E2E results | §15 (+ §15.4 finding N-2) |
| 19 Evidence the canonical runtime no longer depends on `report_schedules` | §16 |
| 20 PO-gated items left unresolved | §17 |
| 21 Known limitations | §18 |
| 22 Production boundary | §19 |
| 23 Independent-verification status | §20 |
| 24 Final verdict | §24 |
| Mandatory final verification (15 questions) | §21 |

---

## 24. Final verdict

**`CT_IMPLEMENT_03_COMPLETE_WITH_PO_GATES`**

*The reconciliation itself is complete:* no active runtime path touches
`report_schedules`/`report_history`; the schedule and share application layers
persist to and read from the canonical tables; the frequency contract is the
canonical vocabulary on both surfaces; the runner executes real scheduled reports
through the canonical data layer; and all of it is verified against real
PostgreSQL on a disposable canonical clone, with 66 new unit tests and 10 E2E tests
passing.

*The PO gates are:* **G-2** (consuming a share — delivery/download policy), **G-3**
(organisation deletion vs immutable run/share history, found by evidence), **G-4**
(the integration-harness fix for the canonical audit guard) and **G-1** (R-6 audit
classification, unchanged), plus the previously open R-1/R-3/R-5/R-7/R-8/R-9/R-10
and the external R-11 migration blocker.

*Not claimed:* production readiness, independent verification, delivery/notification,
share consumption, or any tenant-isolation proof beyond the per-operation
assertions in this change-set.

**No `report_schedules` table was created; no canonical CHECK or guard was
weakened; no migration was added; nothing was pushed and nothing in production was
touched.**
