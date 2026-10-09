# CT-PO-CT-READINESS-01 — Migration Drift & Canonical DB Baseline — REPORT

* **Report type:** verification / implementation report (READ-ONLY audit deliverable)
* **Date:** 2026-09-27
* **Repository:** `/home/shomonrobie/ct_93d5cdd`
* **Branch:** `p8-release-reconciled`
* **Git SHA (HEAD, unchanged):** `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`
* **Companion audit:** `CT-PO-CT-READINESS-01-MIGRATION-DRIFT-AND-CANONICAL-DB-BASELINE-AUDIT-20260927.md`
* **Authority:** `AGENTS.md` §§2, 5, 44, 46, 52, 53, 55.1, 66, 70, 73, 74, 77, 80, 82–85

---

## 1. Task

Complete a **read-only** database / migration baseline audit for CarbonTally:

1. Determine the root cause of the failing CI "Migration drift gate".
2. Establish the canonical applied migration boundary and object state of every
   reachable environment.
3. Produce exactly two Markdown documents (audit + report) without changing code,
   database, migrations, or Git history.

---

## 2. Scope

**Performed**

* Static analysis of `.github/workflows/migration-drift.yml` (actionlint v1.7.12).
* Behavioural analysis of `backend/tools/migration_drift.py` (read-only code inspection
  plus two local executions).
* Repository migration inventory and hygiene check (`supabase/migrations`, 89 files).
* e2e environment migration-set comparison (`e2e/environment/supabase/migrations`).
* Read-only catalog inspection of the local PostgreSQL database reached through
  `backend/.env` `DATABASE_URL`.
* Boundary pinning by catalog fingerprinting against migration sources.
* Object-level verification of all 6 P17 migrations (tables, columns, functions, indexes,
  seed rows).

**Not performed (deliberately)**

* No file in `backend/`, `supabase/`, `.github/` or any application source was modified.
* No migration applied, no ledger created, no DDL/DML issued.
* No production or staging contact; no `CARBONTALLY_MIGRATION_DRIFT_ALLOW` flag set.
* No integration harness run (`INTEGRATION_DATABASE_URL` never set).
* No `git add` / `commit` / `push` / `reset` / `clean` / `checkout` / rebase.

---

## 3. Files changed

| File | Change | Lines |
| --- | --- | --- |
| `docs/architecture/CT-PO-CT-READINESS-01-MIGRATION-DRIFT-AND-CANONICAL-DB-BASELINE-AUDIT-20260927.md` | **new** (audit) | ~730 |
| `docs/architecture/CT-PO-CT-READINESS-01-MIGRATION-DRIFT-AND-CANONICAL-DB-BASELINE-AUDIT-20260927-REPORT.md` | **new** (this report) | — |

No other file was created, edited, renamed or deleted. No source, config, workflow,
migration, test or environment file was touched.

---

## 4. Database changes

**None.** No DDL, no DML, no truncate, no seed, no ledger write, no role/grant change.

Every database session opened by this audit was forced read-only and time-bounded:

```sql
SET default_transaction_read_only = on;
SET statement_timeout = '20s';
```

The only non-`psql` tool executed against the database was the project's own read-only
comparator (`python -m tools.migration_drift --dsn …`), which issues a single
`SELECT version FROM supabase_migrations.schema_migrations ORDER BY version`.
That call failed harmlessly (see §7) because the ledger relation does not exist.

---

## 5. Migrations

**None added, none applied, none modified.** The repository migration set is untouched
(89 files before and after; latest `20261020000000_p17k_governed_capability_catalogue.sql`).

---

## 6. API changes / frontend changes

**None.** No FastAPI route, schema, contract or dependency changed; no React route,
component, style or design token changed; no OpenAPI contract change was made. The live
OpenAPI contract was not modified and no route was invented (AGENTS.md §65).

---

## 7. Tests and runtime verification

### 7.1 Static workflow test (root cause of the CI failure)

| Check | Command | Result |
| --- | --- | --- |
| actionlint version | `actionlint -version` | `1.7.12` |
| Drift workflow lint | `actionlint .github/workflows/migration-drift.yml` | **exit 1** — `migration-drift.yml:47:17: context "secrets" is not allowed here` |
| Repo-wide workflow lint | `actionlint` | same **single** finding (no other workflow defect) |

### 7.2 Comparator reproduction (local, read-only)

| Check | Result |
| --- | --- |
| Repository-only mode (the workflow's "Repository-side check" step) | exit `0`; `anomalies = 0`; repository set internally consistent |
| Ledger mode against a database without the ledger relation | exit `1` with an **unhandled `asyncpg.exceptions.UndefinedTableError`** traceback and **no evidence artefact written** (reproduced) |
| Ledger mode against a provisioned ledger | **not executed** — no ledger source provisioned (`MIGRATION_DRIFT_DATABASE_URL` absent from `backend/.env`) |

### 7.3 Database baseline verification (local `ct_local_93d5cdd`, PostgreSQL 17.6)

| Check | Result |
| --- | --- |
| Applied/unapplied boundary | **pinned** between `20260931…` (objects present) and `20261001…` (objects absent) |
| Outstanding migrations | **14** (all versions ≥ `20261001`) |
| P17 objects present | **0** — verified by object-level probes for P17A/C/D/H/10/K |
| P17K seed rows | `disclosure_framework_versions = 0`, `disclosure_requirement_versions = 0` |
| Migration ledger schema | **ABSENT** (`supabase_migrations` does not exist) |
| Public schema size | 135 tables / 331 indexes / 55 functions / 89 triggers / 0 views |
| RLS | enabled on 135/135 public tables; `FORCE RLS` 0; 218 policies; 10 policies reference `auth.*` |
| Supabase Auth data model | **ABSENT** (`auth` schema has 0 relations; `auth.users` does not exist) although roles `anon`, `authenticated`, `service_role`, `supabase_admin`, `supabase_auth_admin` and `auth.uid()/jwt()/role()` do exist |
| Storage | `storage.buckets`, `storage.objects` present |
| Business data | organisations 25, members 16, consultant profiles 3, staff profiles 5, `roles` 0, emission factors **0**, documents **0**, batches **0**, snapshots **0**, emissions **0** |

### 7.4 Interpretation of the CI run history

The observed runs of the gate concluded **failure with zero jobs** — GitHub rejected the
workflow before creating any job — which is exactly what a statically invalid workflow
produces. Consequently the workflow's *always-run* repository-side check has never produced
CI output either, and **no drift evidence artefact has ever been produced** (the
`upload-artifact@v4` step reports 0 artefacts).

---

## 8. Security verification

| Control | Status |
| --- | --- |
| Read-only enforced on every DB session | PASS |
| Statement timeout applied | PASS (`20s`) |
| Credentials/tokens/JWTs/signed URLs printed | **none** (key **names** only were inspected) |
| Production contacted | **no** |
| Investor-demo dataset touched | **no** — the audited local DB is not the demo set; no demo row was read or written |
| DB writes | **none** |
| Git history mutated | **no** (no reset/clean/force-push/rebase/commit) |
| Integration harness pointed at a data-bearing DB | **no** (`INTEGRATION_DATABASE_URL` unset) |

### 8.1 F-046-1 restatement (mandatory carry-forward)

> The integration harness's `pool` fixture executes `TRUNCATE … RESTART IDENTITY CASCADE`
> against whatever `INTEGRATION_DATABASE_URL` names. The harness must **NEVER** be pointed
> at a persistent environment whose data matters — not persistent QA, not the investor
> demo, **never** production. Integration suites must target a disposable clone (`ct_*`)
> or `carbontally_test`; the fixture itself refuses targets matching
> `qa`/`demo`/`investor`/`prod`/`live` with an explicit `F-046-1` error. In this audit the
> harness was not run at all, and the database it *would* have targeted was left untouched.

### 8.2 Security findings from this audit

None. The audit itself introduced no new exposure and did not bypass RLS, authorization or
tenant isolation. The one security-relevant observation is negative-but-important: the CI
gate that would detect schema drift is **not executing**, which is a release-integrity
control failure rather than a data-exposure issue.

---

## 9. Findings delivered (summary)

| ID | Sev | Headline | Class |
| --- | --- | --- | --- |
| F-01 | **P1** | CI migration-drift gate cannot run: `secrets` context used in a step `if:` → actionlint error → 0 jobs → gate inert since introduction | VERIFIED |
| F-02 | **P1** | `MIGRATION_DRIFT_DATABASE_URL` is unset in the only configured environment, so the ledger comparison is inert by default; the gate would be a no-op even if it parsed | VERIFIED (design inspection) |
| F-03 | **P2** | Ledger mode against a ledger-less database exits 1 with a raw `asyncpg` traceback and writes **no** evidence artefact | VERIFIED (reproduced) |
| F-04 | **P2** | Local database has **no Supabase Auth data model** (`auth` schema has 0 relations) → authenticated/RLS E2E cannot be validated locally | VERIFIED |
| F-05 | **P2** | Local database is business-data-empty for the audited pipeline (0 factors, 0 documents, 0 snapshots, 0 emissions) → no workflow outcome is demonstrable | VERIFIED |
| F-06 | **P2** | Production migration state is **UNKNOWN**; no safe evidence path exists and no prod DSN is provisioned | UNVERIFIED (BLOCKED) |
| F-07 | **P3** | No historical gate evidence: 0 artefacts ever produced; the documented override-recording guarantee has never been exercised | VERIFIED |
| F-08 | **P3** | e2e stack carries a stale **subset** of migrations (53 of 89, ceiling `20260910120000`, 0 `202610*` files) — a third drifting baseline | VERIFIED |
| F-09 | INFO | Repository-side migration hygiene: **PASS** (89 files, no naming/duplicate/ordering anomalies, repo-only comparator exit 0) | VERIFIED |

Full reproduction, impact and remediation direction for each finding are in the companion
audit document (§6).

---

## 10. Git state

* Verified before and after the audit; **HEAD and branch unchanged**
  (`p8-release-reconciled` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`).
* **Tracked-file delta created by this session: none.** One tracked file shows as modified
  in `git status` (`.gitignore`, `108 insertions / 107 deletions`), but its on-disk mtime is
  **2026-09-23** — four days before this session — so it is a **pre-existing** working-tree
  state and was not touched by this audit. It was left exactly as found.
* Files created by this session: **only** the two mandated documents under
  `docs/architecture/`.
* The working tree also contains many pre-existing untracked artefacts from earlier
  sessions (e.g. `.p18_audit_tmp/`, previously produced `docs/architecture/*` reports and
  `docs/ChatGPT/*`). None of these were created, modified or deleted by this audit.
* No staged changes were created, no commit was made, nothing was pushed, and no history
  operation (`reset --hard`, `clean -fd`, rebase, amend, force-push) was performed.

---

## 11. Remaining limitations and next actions

**Limitations of this deliverable**

1. Production and staging baselines are **UNKNOWN** — the report states this rather than
   inferring parity (AGENTS.md §80).
2. Migration-object fingerprinting covered the objects *declared by* the candidate
   migrations; it is not an exhaustive schema diff of the local database.
3. Local RLS was inspected structurally (enabled flags, policy inventory) but **not**
   behaviourally evaluated, because the Auth data model is absent (F-04).
4. No acceptance claim is made for any workflow (AGENTS.md §§73–74).

**Next actions (owners)**

| # | Action | Owner |
| --- | --- | --- |
| A1 | Fix `.github/workflows/migration-drift.yml` line 47; add an actionlint CI job so an invalid workflow cannot merge again | Implementation |
| A2 | Give the comparator a distinct `BLOCKED` outcome + evidence artefact when the ledger is missing/unreachable (F-03) | Implementation |
| A3 | Provision a non-production ledger for CI comparison | **PO decision required** |
| A4 | Nominate the authorised evidence environment for P17/P16R/Insight verification | **PO decision required** |
| A5 | Apply the 14 outstanding migrations to a **disposable** database and verify ordered application (P17K depends on P17D's `scope3_categories`) | Implementation |
| A6 | Re-provision the local stack with Supabase Auth, or record local auth/RLS as permanently UNVERIFIED in QA scope | Implementation / environment |
| A7 | Document or regenerate the e2e migration set (F-08) | Implementation |

---

## 12. Verdict

**Implemented:** audit + report documents only. **Tested:** static workflow lint, comparator
reproduction, catalog/boundary verification, P17 object-level verification.
**Verified:** all findings above against current runtime evidence. **Accepted:** no — no
Product Owner acceptance is claimed.

**P17 readiness: NOT VERIFIED.** The release gate that should protect this position is
currently non-functional, and the P17 object baseline is absent from every reachable
environment.

*(End of report — CT-PO-CT-READINESS-01)*