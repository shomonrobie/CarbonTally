# CT-AUDIT-01 — CarbonTally Canonical Audit System: Archaeology & Reconciliation

**Task ID:** `CT-AUDIT-01-20260927-CARBONTALLY-CANONICAL-AUDIT-SYSTEM-ARCHAEOLOGY-AND-RECONCILIATION`
**Type:** READ-ONLY INVESTIGATION / ARCHITECTURE RECONCILIATION
**Authority:** PO discovery only — **no implementation authorised**
**Report date:** 2026-09-27
**Repository investigated:** `/home/shomonrobie/ct_93d5cdd` (HEAD `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`, branch `p8-release-reconciled`)
**Upstream:** CT-SCHEMA-03 `CT-PO-CARBONTALLY-CT-SCHEMA-03-REPORT-20260927.md` (SCM-004…SCM-007)
**Production:** NEVER TOUCHED · **Database writes:** NONE (SELECT / RAISE NOTICE only) · **Git mutations:** NONE

> Method: repository archaeology across **10 on-disk copies**, **all Git refs** of the working
> repository plus HEAD identity of 8 sibling checkouts, the **89-migration canonical chain**,
> the **live schema and row counts** of 4 probed databases, the code inventory of legal
> writers/readers, and the documentation record. Every claim below carries a path, line,
> SHA, or query result.

---

## 1. Executive finding

**The comprehensive audit capability was NOT lost, and it is NOT the orphaned module.**

CarbonTally currently runs a **two-tier audit architecture** that is registered, persisted,
immutability-protected, populated with real rows, unit/integration-tested and UI-consumed:

| Tier | Carrier | Status | Runtime evidence |
|---|---|---|---|
| **Tier 1 — canonical forensic audit ledger** | table `public.audit_trail` + `backend/domain/audit.py` + `backend/data/audit.py` + `backend/infra/audit_logger.py` | **IMPLEMENTED · WIRED · POPULATED** | `audit_trail` = **563 rows** (`supabase_db_carbon_ledger`, db `postgres`), **242 rows** (db `carbontally_demo_local` = investor demo) |
| **Tier 2 — legacy per-domain activity logs** | tables `audit_logs`, `activity_logs`, `document_activity_log` (+ `message_activity_log`, `verification_activity_log`, …) + `backend/utils/audit_logger.py` | **RETIRED-IN-PLACE (retained, immutable, no longer written)** | `audit_logs` = **0 rows in all four probed databases**; yet 12 legacy insert sites exist in the code |

The single genuinely orphaned object is the **12-endpoint legacy admin console module**
`backend/routes/admin/audit_logs.py`, which CT-SCHEMA-03 classified correctly. Its
supersession is *explicitly documented in the repository*:

* migration `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql:9-19` —
  *"``public.audit_trail`` (RC2) — the canonical append-only audit ledger used by
  ``backend/data/audit.py`` (AuditRepository) for material human/system actions across every
  surface"* … *"``audit_logs`` / ``activity_logs`` / ``document_activity_log`` — **legacy**
  per-domain activity records"*;
* `docs/audit/cline/CARBONTALLY_V3_ARCHITECTURE_CONFORMITY_GATE.md:649` —
  `routes/admin/audit_logs.py` (stale) → **"Yes — `api/admin_audit.py` + `data/audit.py`"**;
* `docs/architecture/CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md:65` — lists
  `routes/admin/audit_logs.py` among *"Stale route modules … not imported"*;
* `docs/architecture/ARCHITECTURE_DECISIONS.md` / ADR-V3-013 — *"no new history table"*
  (referenced from `backend/api/v3_operations.py:372`).

### 1.1 Refinement of the CT-SCHEMA-03 implication (required by the task brief)

| CT-SCHEMA-03 statement | CT-AUDIT-01 finding |
|---|---|
| `backend/routes/admin/audit_logs.py` is an unregistered orphan | **CONFIRMED AND EXTENDED** — never imported in *any* reachable Git commit; its 12 endpoints have **no consumer** anywhere in the repo (0 hits for `api/admin/audit-logs` in `frontend/src`, `admin/src`, `qa_harness/`, `backend/` outside the module itself) |
| `notification_delivery_log` reference at `:404` cannot execute (SCM-007 → S3) | **CONFIRMED** — `notification_delivery_log` is **ABSENT** in both canonical-schema databases; canonical `notification_delivery` (0 rows) + `notifications` exist |
| *Implicature:* audit capability may be orphaned/lost | **CORRECTED** — comprehensive audit is implemented in Tier 1 and wired; only the *legacy read console* is orphaned. The two tiers must be treated separately |

### 1.2 The "ten variants" premise

The PO brief anticipated ~10 **variants**. Verified result: there are **10 copies but only
ONE semantic version**.

* All 10 copies are byte-identical after line-ending normalisation
  (`tr -d '\r' | md5sum` = `1058bf33c3948df3affb91b198902f5f` for the representative pair).
* 6 copies are **CRLF** (55,504 bytes) and 4 are **LF** (54,073 bytes); 55,504 − 54,073 =
  1,431 = the file's line count ⇒ the delta is *exactly* CRLF conversion, nothing else.
* The three Git commits that ever touched the file (`eed55d6`, `2d23fb8` — both 2026-08-06 —
  and `077c866` — 2026-08-27) all contain the **same normalised content** ⇒ **no
  MINOR/MAJOR evolution lineage exists**, there is no "earlier" and no "later" semantic
  version, and no on-disk copy is a richer implementation than
  `backend/routes/admin/audit_logs.py`.

Consequently the archaeology question is not *"which of ten variants is canonical"* but
*"why does one frozen artefact exist in ten places while a different, live audit system
runs in the application"* — answered in §3/§16.

---

## 2. Ten-copy `audit_logs.py` census

Machine-wide search `find / -xdev -name 'audit_logs*.py'` (excluding `node_modules`,
`site-packages`, `/proc`, `/sys`) returned 153 paths: **144 are third-party** (litellm
`proxy/management_helpers/audit_logs.py` and `openai/resources/admin/organization/audit_logs.py`
inside `~/.cache/uv`) and **10 are CarbonTally copies** (V-06 is a scratch copy in `/tmp`).

| ID | Path | Repo / HEAD | Lines | Bytes | EOL | Routes | Content hash | Status |
|---|---|---|---|---|---|---|---|---|
| V-01 | `/home/shomonrobie/ct_93d5cdd/backend/routes/admin/audit_logs.py` | `ct_93d5cdd` @ `cb70fd6` (`p8-release-reconciled`) | 1431 | 55,504 | CRLF | 12 | `1058bf33c394` | **CURRENT checkout · UNREGISTERED (orphan)** |
| V-02 | `/home/shomonrobie/carbon_tally/backend/routes/admin/audit_logs.py` | `carbon_tally` @ `20b7a92` | 1431 | 55,504 | CRLF | 12 | `1058bf33c394` | duplicate checkout · unregistered |
| V-03 | `/home/shomonrobie/carbon_tally_p8_release/backend/routes/admin/audit_logs.py` | `carbon_tally_p8_release` @ `0be7438` | 1431 | 55,504 | CRLF | 12 | `1058bf33c394` | duplicate checkout |
| V-04 | `/home/shomonrobie/workspace/project/0000789dfc0f47f790dcfe312824eb99/backend/routes/admin/audit_logs.py` | `0be7438` | 1431 | 55,504 | CRLF | 12 | `1058bf33c394` | workspace duplicate |
| V-05 | `/home/shomonrobie/Documents/carbon_tally_backup_25_aug_2025/backend/routes/admin/audit_logs.py` | dated backup @ `878bd0f` | 1431 | 55,504 | CRLF | 12 | `1058bf33c394` | dated backup |
| V-06 | `/tmp/m3_base/backend/routes/admin/audit_logs.py` | scratch (M3 baseline copy) | 1431 | 55,504 | CRLF | 12 | `1058bf33c394` | generated scratch copy |
| V-07 | `/home/shomonrobie/workspace/project/0581ebdb72e141ce84f925c7c5bb7479/CarbonTally_audit/backend/routes/admin/audit_logs.py` | audit workspace @ `2fd4345` | 1431 | 54,073 | LF | 12 | `1058bf33c394` | duplicate (LF) |
| V-08 | `/home/shomonrobie/workspace/project/fd01b4949db94cebabd1216d255bf4a2/carbon_tally_audit/backend/routes/admin/audit_logs.py` | audit workspace @ `9458067` | 1431 | 54,073 | LF | 12 | `1058bf33c394` | duplicate (LF) |
| V-09 | `/home/shomonrobie/workspace/project/carbontally_uiux_audit/backend/routes/admin/audit_logs.py` | uiux workspace @ `d4dcca1` | 1431 | 54,073 | LF | 12 | `1058bf33c394` | duplicate (LF) |
| V-10 | `/home/shomonrobie/workspace/project/carbontally_docs_publish/backend/routes/admin/audit_logs.py` | docs workspace @ `9339a9b` | 1431 | 54,073 | LF | 12 | `1058bf33c394` | duplicate (LF) |

`wc -l` = 1431 because the file has no trailing newline; the module inventory
(`docs/cline/CarbonTally_Backend_Module_Inventory_V3.md:94`) counts **1432 lines / 55,504
bytes**, matching V-01 exactly. `sha256sum` short hashes also split the ten into exactly two
groups (`042e7dae…` CRLF ×6, `a6fdb0b1…` LF ×4).

### 2.1 Per-variant capability profile (identical for all ten)

| Attribute | Value | Evidence |
|---|---|---|
| Router prefix / tag | `/api/admin/audit-logs`, `["Admin Audit Logs"]` | `backend/routes/admin/audit_logs.py:12` |
| Endpoints | **12** | §2.2 |
| Pydantic models | **9** | module inventory `:3756-3775`; re-verified by parse |
| Authorization | `require_admin()` on every handler | `audit_logs.py` (`from auth import AuthUser, require_admin`) |
| Tables referenced | `audit_logs`, `message_activity_log`, `notification_delivery_log`, `verification_activity_log`, `customer_verifications`, `messages`, `notifications`, `organizations`, `auth.users` | `grep -oE "from_\('…'\)"` |
| Audit fields supported | `user_id`, `staff_id`, `organization_member_id`, `organization_id`, `action_type`, `resource_type`, `resource_id`, `action`, `description`, `ip_address`, `user_agent`, `old_data`, `new_data`, `changes`, `metadata`, `created_at` + resolved `user_email`, `user_name`, `organization_name` | `AuditLogResponse` (`:20-48`) |
| Registered? | **NO** | §11 |
| Superseded? | **YES** — by `api/admin_audit.py` + `data/audit.py` (documented) | conformity gate `:649` |

### 2.2 The 12 endpoints (all unreachable in the running app)

`GET /` (search) · `GET /messages` · `GET /notifications` · `GET /verifications` ·
`GET /export` · `GET /stats` · `GET /organizations` · `GET /actions` · `GET /users` ·
`GET /users/summary` · `GET /users/{user_id}/activities` · `GET /users/export`.

This set is precisely the "broader audit system" in the task brief (actor/staff/membership
identity, action + resource type, before/after, filtering, statistics, exports, user
activity history, message activity, notification activity, verification activity).

### 2.3 Semantic-diff classification

| Pair | Classification | Basis |
|---|---|---|
| V-01 … V-10, all pairs | **SAME / DUPLICATE** | normalised md5 identical; only EOL differs (`diff` empty after `tr -d '\r'`) |
| Any on-disk copy vs Git history | **SAME** | all 3 historical blobs normalise to `1058bf33c394` |
| `audit_logs.py` vs `api/admin_audit.py` + `data/audit.py` | **DIFFERENT SYSTEM** (superseding) | legacy PostgREST reads vs `AuditRepository` over `audit_trail` ("no second audit-log system is created", `admin_audit.py:1-7`) |
| Earliest vs latest meaningful version | **identical** (2026-08-06 → 2026-08-27) | `git log` blob hashes |

**No variant is a more complete implementation than the orphaned
`backend/routes/admin/audit_logs.py`** — all ten are that module.

---

## 3. Historical timeline (Git evidence)

| Date | Commit | Event | Evidence |
|---|---|---|---|
| 2026-08-06 | `eed55d6`, `2d23fb8` "CarbonTally RC2 Final database baseline" | `backend/routes/admin/audit_logs.py` **added**; `supabase/migrations/00000000000000_init_schema.sql` **added**, creating `audit_logs` (`:1647`), `audit_trail`, and the whole legacy activity family; `routes/admin/audit.py` added in the same baseline | `git log --all --diff-filter=A`; blob hash `1058bf33c394` |
| 2026-08-27 | `077c866` "feat: finalize v3 ux and promote public website" | last touch of `audit_logs.py` — **content unchanged** | same blob hash |
| 2026-08-30 | (documented decision, not a commit) | PO decision **D-P2-02 DEPRECATE** ratified: V3 `/ops` is the canonical internal administration surface; legacy `/api/admin/*` *and* `/api/v2/admin/audit` deprecated-but-mounted | `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:3-15,58-60` |
| 2026-09-11 | `daad396` "release: establish CarbonTally production release 1" | `20260831020000_audit_activity_immutability.sql` introduced (WS1/DB-0001): UPDATE/DELETE policies dropped on `audit_logs`, `activity_logs`, `document_activity_log`; `activity_feed` re-scoped to row owner | `git log --diff-filter=A -- <path>`; migration header `:1-12` |
| 2026-09-12 | `4368157` "feat(phase7): auditor/assurance auditability, taxonomy, evidence package" | `20260912000000_p7_audit_immutability_and_indexes.sql`: append-only **trigger** on `audit_trail`, 5 investigation indexes, Phase-7 taxonomy in `metadata`; ships `frontend/src/v3/ops/AuditConsoleTab.jsx`, `frontend/src/v3/admin/AuditTab.jsx`, `api/v3_reporting.py` audit endpoints | `git log --diff-filter=A`; migration text `:1-82` |
| 2026-09-25 | `5282660` "feat(p17): add CAMS accounting-dimension and boundary migrations" | `20261010000000_p17a_…sql` adds `actor_organization_id` + `acting_for_organization_id` to `audit_trail` (and `evidence_line_items`, `customer_documents`, `suppliers`, `review_audit_trail`) — the consultant "acting for" carrier | `git log --diff-filter=A`; migration `:295-320` |
| 2026-09-27 | (this audit chain) | CT-SCHEMA-03 reclassifies SCM-007 (`notification_delivery_log`) S2 → S3 orphan | `CT-PO-CARBONTALLY-CT-SCHEMA-03-REPORT-20260927.md:306-326` |

**Commits that removed, renamed or deregistered audit functionality: NONE FOUND.**
There is no "audit router stopped being registered" event: `backend/routes/admin/audit_logs.py`
was created unregistered on 2026-08-06 and never entered `main.py` or
`backend/routes/admin/__init__.py` in any commit on any ref
(`git log --all -S 'audit_logs' -- backend/main.py backend/routes/admin/__init__.py` → empty;
`git grep -n 'admin.audit_logs' <every-touching-commit>` → matches only the module's own header
comment). The canonical audit system was built *alongside* it, not by removing it.

---

## 4. Audit schema / migration history

### 4.1 The canonical chain creates the audit family (89 migrations, 147 `CREATE TABLE` statements)

`supabase/migrations/00000000000000_init_schema.sql` (added 2026-08-06, `eed55d6`/`2d23fb8`):

* `:1647` `CREATE TABLE public.audit_logs (...)` — 16 columns, `:1667` comment, indexes
  `:2232-2234` (`idx_audit_logs_tenant_id`, `idx_audit_logs_created_at`,
  `idx_audit_logs_table_record`);
* `:1669` `CREATE TABLE public.audit_trail (...)` — 13 columns at birth
  (`id`, `action_type`, `table_name`, `record_id`, `performed_by`, `performed_at`,
  `old_data`, `new_data`, `changes`, `ip_address`, `user_agent`, `metadata`, `created_at`),
  comment *"Generic audit trail"*;
* the rest of the audit/activity family in the same file: `activity_logs`,
  `activity_feed`, `document_activity_log`, `message_activity_log`,
  `verification_activity_log`, `user_activity_log`, `staff_activity_log`,
  `processing_audit_trail`, `review_audit_trail`, `reassignment_history`, `login_history`,
  `export_history`, `notification_delivery`, `notifications`, `domain_events`,
  `evidence_line_items`, `disclosure_value_evidence`, `customer_review_log`,
  `conversation_activity_log`, `email_logs`, `emissions_logs`, `processing_logs`,
  `processing_time_log`, `review_assignment_history`, `verification_logs`,
  `ai_content_history`, `activity_clarifications`, `activity_categories`.

* **No migration creates `notification_delivery_log`** (`git grep -F notification_delivery_log -- supabase/migrations` → 0), confirming CT-SCHEMA-03 and SCM-007.

### 4.2 Migrations that touch the audit family

| Migration | Effect on audit | Evidence |
|---|---|---|
| `00000000000000_init_schema.sql` | CREATE `audit_logs` (+3 indexes), CREATE `audit_trail`, CREATE 28 further audit/activity tables | `grep -n audit_logs` → `:1647,1667,2232-2234` |
| `20260805000000_rc2_triggers.sql` | RC2 triggers referencing `audit_trail` | `grep -rln audit_trail supabase/migrations` |
| `20260806000000_rc2_verification.sql` | RC2 verification assertions referencing `audit_trail` | idem |
| `20260807070000_add_new_table_rls.sql` | RLS for the newly added tables (audit-family batch) | idem |
| `20260810040000_v3m5_issues.sql`, `20260821020000_d22_processing_work_assignment.sql`, `20260824030000_d37_master_commercial_billing.sql` | consumers/writers of `audit_trail` (issues, D22 assignment, D37 billing) | idem |
| **`20260831020000_audit_activity_immutability.sql`** (DB-0001) | `DROP POLICY audit_logs_tenant_update/audit_logs_tenant_delete`, same for `activity_logs`, `document_activity_log`; re-scopes `activity_feed` update/delete to `user_id = auth.uid()`. Header: *"`audit_logs`, `activity_logs`, `document_activity_log` are **historical** audit/activity records"* and *"The V3 forensic `audit_trail` is already deny-by-default (no policies)"* | `:1-45` |
| **`20260912000000_p7_audit_immutability_and_indexes.sql`** (Phase 7) | `p7_audit_trail_immutable()` + `CREATE TRIGGER p7_audit_trail_immutable BEFORE UPDATE OR DELETE ON public.audit_trail`; 5 indexes (`performed_at`, `action_type`, `table_name+record_id`, `metadata` GIN, partial org index). Header names `audit_trail` the **"canonical append-only audit ledger used by `backend/data/audit.py`"** and calls `audit_logs`/`activity_logs`/`document_activity_log` **"legacy per-domain activity records"**; notes the trigger fires for **every role including the service role** | `:1-82` |
| `20260925000000_p8_rls_4b_group1_enablement.sql` | RLS enablement batch includes `audit_logs` in its approved append-only family (`:78`); `audit_trail` deliberately **not** in the list (already deny-by-default) | `:60-100` |
| `20260927000000_p8_fin06_manual_processing_governance.sql` | references `public.audit_logs` as the destination of governance-change recording (`:16`) | migration comment |
| `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | `ALTER TABLE public.audit_trail ADD COLUMN IF NOT EXISTS actor_organization_id uuid, acting_for_organization_id uuid` (+4 other carriers), §10.3 "CONTEXT, NOT AUTHORIZATION" | `:295-320` |
| `20261013000000_p17h_estimation_and_assumption_records.sql` | further `acting_for_organization_id` carriers | `grep -rln` |

**Counts:** migrations referencing `audit_trail` = **12**; migrations referencing `audit_logs`
= **6** (`00000000000000_init_schema`, `20260831020000`, `20260831030000`, `20260912000000`,
`20260925000000`, `20260927000000`).

### 4.3 CT-SCHEMA-03 R1 guard interaction (important negative result)

The canonical R1 guard in `20260800000000_rc2_schema.sql` (which raises an EXCEPTION if
`defra_conversion_factors` exists — CT-SCHEMA-03 F-01) contains **zero references to
`audit_logs` or `audit_trail`**: the audit tables are neither forbidden nor dropped by the
RC2 baseline. The audit family is therefore part of the *ratified* canonical surface, not a
legacy survivor that the chain tolerates.

---

## 5. Canonical schema comparison (measured, not assumed)

### 5.1 Read-only presence / row-count probe

Method: `docker exec … psql -U postgres -d <db> -c "DO $$ … to_regclass + EXECUTE count(*) … $$"`
(SELECT/RAISE NOTICE only). Scripts `/tmp/aud1_probe.sh`, `/tmp/aud1_probe2.sh`,
`/tmp/aud1_probe3.sh`; raw output `/tmp/aud1_dbprobe.txt`, `/tmp/aud1_dbprobe2.txt`,
`/tmp/aud1_dbprobe3.txt`.

| Table | CT-SCHEMA-01 rebuild (`ct_schema01_pg`) | CT-SCHEMA-02 (`ct_schema02_pg`) | `supabase_db_carbon_ledger` db `postgres` | db `carbontally_demo_local` (**investor demo**) |
|---|---|---|---|---|
| `audit_logs` | **PRESENT** (0 rows) | **PRESENT** (0) | PRESENT (0) | PRESENT (**0**) |
| `audit_trail` | PRESENT (0) | PRESENT (0) | PRESENT (**563**) | PRESENT (**242**) |
| `activity_logs` | PRESENT (0) | PRESENT (0) | PRESENT (0) | PRESENT (0) |
| `document_activity_log` | PRESENT (0) | PRESENT (0) | PRESENT (0) | PRESENT (0) |
| `message_activity_log` | PRESENT (0) | PRESENT (0) | PRESENT (0) | PRESENT (0) |
| `verification_activity_log` | PRESENT (0) | PRESENT (0) | PRESENT (0) | PRESENT (0) |
| `user_activity_log` / `staff_activity_log` | PRESENT (0) | PRESENT (0) | PRESENT (0) | PRESENT (0) |
| `notification_delivery` | PRESENT (0) | PRESENT (0) | PRESENT (0) | PRESENT (0) |
| **`notification_delivery_log`** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** |
| `calculation_snapshots` | PRESENT (0) | PRESENT (0) | PRESENT (100) | PRESENT (34) |
| `notifications` | PRESENT (0) | PRESENT (0) | PRESENT (3) | PRESENT (6) |
| `domain_events`, `review_audit_trail`, `login_history`, `export_history`, `reassignment_history` | PRESENT (0 each) | PRESENT (0 each) | PRESENT (0 each) | PRESENT (0 each) |

### 5.2 Answers to Q5 / Q6 / Q7 of the brief

* **Q5 — does `audit_logs` exist in the canonical CT-SCHEMA-01/02 schema?** **YES.** It is
  created by the canonical chain (`init_schema.sql:1647`) and present in both the CT-SCHEMA-01
  disposable rebuild and the CT-SCHEMA-02 fingerprint database. It is therefore **not** an
  SCM-004…007-class missing object, and **no canonical replacement is required for
  `audit_logs` itself**. (This does not alter CT-SCHEMA-03's four graded names —
  `defra_conversion_factors`, `report_history`, `report_schedules`, `notification_delivery_log`
  — which remain absent; `audit_logs` was never one of them.)
* **Q6 — exact canonical `audit_logs` schema:** 16 columns —
  `id uuid PK default extensions.uuid_generate_v4()`, `user_id uuid`, `staff_id uuid`,
  `organization_member_id uuid`, `organization_id uuid`, `action_type text NOT NULL`,
  `resource_type text`, `resource_id uuid`, `action text NOT NULL`, `description text`,
  `ip_address text`, `user_agent text`, `old_data jsonb`, `new_data jsonb`, `changes jsonb`,
  `metadata jsonb`, `created_at timestamptz DEFAULT now()`; 3 indexes; RLS **enabled**
  (not forced); policies **INSERT + SELECT only** (§10); **no triggers**; **no FK constraints**
  on `organization_id`/`user_id` (nullable and unconstrained — the same nullability the
  earlier audit chain flagged).
* **Q7 — status of `audit_logs`:** the evidence selects **(A) intentionally superseded**
  combined with **(C) replaced by another canonical audit table**, with **retention instead
  of removal**:
  * (A) `20260912000000:14-19` labels it a *legacy per-domain activity record* while naming
    `audit_trail` the canonical ledger; the conformity gate maps `routes/admin/audit_logs.py`
    → `api/admin_audit.py` + `data/audit.py`;
  * (C) every ledger capability the legacy console offered exists over `audit_trail`
    (search, filters, statistics, CSV export, correlation reconstruction, before/after);
  * **not (B) accidental omission** (it is in the chain and in both schema DBs),
    **not (D) split** (nothing was reassigned out of it), **not (E) never migrated**
    (created by `init_schema`), **not (F) unresolved**;
  * "superseded" here means *superseded as the canonical ledger*, **not scheduled for
    deletion** — PO decision D-P2-02 is explicitly "deprecated, not deleted".

### 5.3 Functional comparison — is anything the legacy console offered *lost*?

| Legacy capability (`audit_logs.py`) | Canonical replacement | Parity |
|---|---|---|
| `GET /` search with user/org/action/resource/date filters + paging | `AuditQuery` (`domain/audit.py:288`) · `GET /api/v2/admin/audit` (correlation / entity / action / actor / time bounds) · `GET /api/v3/ops/reporting/audit` (+ `category`/`origin`/`outcome`/`q`/`sort`/`order`, BL-4) | **FULL** (V3 adds taxonomy filters + server-side ordering) |
| `GET /stats` (totals; by action type / resource / org / user) | `AuditRepository.count()`; `GET /api/v3/reporting/audit-readiness`; ops reporting | **PARTIAL** (no single V3 endpoint returns the legacy aggregate shapes) |
| `GET /export`, `GET /users/export` (CSV) | `AuditRepository.export_csv()`; `GET /api/v2/admin/audit/export` (`AuditCsvOut`); `GET /api/v3/exports/audit-package.json` | **FULL** |
| `GET /organizations`, `GET /actions` (filter vocabularies) | canonical taxonomy (`CATEGORIES`, action-prefix map) exposed only through filters | **PARTIAL** |
| `GET /users`, `/users/summary`, `/users/{id}/activities` (user activity history) | `actor=` filter on canonical audit reads | **PARTIAL** (no per-user roll-up endpoint) |
| `GET /messages` (`message_activity_log`) | `message_activity_log` has **no writer**; canonical messaging audits via `repos.audit.record` (`api/v3_messaging.py:320`) | **REPLACED** (different carrier; legacy table 0 rows) |
| `GET /notifications` (`notification_delivery_log`) | `notification_delivery` + `notifications` via `backend/data/notifications.py:253` | **REPLACED** — and the legacy endpoint is **structurally broken** (absent table, SCM-007) |
| `GET /verifications` (`verification_activity_log`) | carrier still exists; only unregistered modules and `routes/emissions.py:900` read it; 0 rows | **WEAKER** (no live writer found) |

**Conclusion:** the *ledger* capability is preserved and improved. The measurable regressions
are (a) per-user activity roll-ups and aggregate statistics shapes, and (b) the
message/notification/verification activity sub-surfaces, which sit on carriers that either
receive no writes or do not exist.

---

## 6. Audit writer inventory (canonical vs legacy)

### 6.1 Tier 1 — canonical writers (`public.audit_trail`)

| Writer | Mechanism | Evidence |
|---|---|---|
| `backend/data/audit.py` — `AuditRepository.record()`, `save()`, `delete()` | `INSERT INTO public.audit_trail (action_type, table_name, record_id, performed_by, performed_at, old_data, new_data, changes, ip_address, metadata, created_at, actor_organization_id, acting_for_organization_id)` | `:29-33`, `:205-235` |
| `backend/domain/audit.py` | `AuditEntry` frozen dataclass: `correlation_id`, `entity_type`, `entity_id`, `action`, `actor`, `occurred_at`, `changed_fields`, `reason`, `ip_address`, `before`, `after` + Phase-7 `actor_type`/`origin`/`outcome`/`organization_id`/`category` + P17 `actor_organization_id`/`acting_for_organization_id`; `classify_action()`, `classify_origin()` | `:163-210`, `:206-260` |
| `backend/infra/audit_logger.py` | `AuditLogger`, `AuditSink` protocol, `@audit` decorator, `init_audit_logger()`, `get_audit_logger()`, `reset_audit_logger()` | `:43-254` |
| `backend/api/dependencies.py` | wires `AuditRepository` (`:41`, `:52`) and the process-wide `AuditLogger` (`:101`, `:508`) | imports |
| Call sites | **35** `repos.audit.record(` invocations in shipping (non-test) code; **39** files reference `AuditRepository`/`audit.record(` | `grep -rn 'repos.audit.record(' backend/ --include='*.py' \| grep -v tests \| wc -l` → 35 |
| Consumer modules (all registered) | `api/`: `v3_operations`, `v3_consultants`, `v3_pe`, `v3_messaging`, `v3_documents`, `v3_emissions`, `v3_evidence`, `v3_organizations`, `v3_reporting`, `v3_reports`, `v3_whitelabel`, `v3_commercial`, `v3_discovery`, `v3_automatic_processing`, `v3_processing_workflow`, `admin_aliases`, `admin_entities`, `admin_audit`, `audit_helpers`, `customer_factors`, `issues`, `manual_processing_admin`, `contracts`; `data/`: `disclosure`, `evidence_line_items`, `accounting_context`; `services/`: `billing`, `work_items`, `operational_alerting`, `disclosure_finalisation`, `disclosure_narrative`; `engines/`: `extraction`, `ai_extraction`, `calculation`, `validation`, `factor_matching`, `workflow`, `benchmarking`, `report_generation`; `workers/automatic_processing` | `grep -rln` |
| Classification | **actually executable** — every module is registered, or imported by one that is (§11) | — |

### 6.2 Tier 2 — legacy writers (`public.audit_logs`)

| Writer | Sites | Module registered? | Classification |
|---|---|---|---|
| `backend/utils/audit_logger.py::log_audit` (+ `log_document_action`, `log_verification_action`, `log_message_action`, `log_notification_action`) | `:56` | utility | **executable** — but swallows every exception (`:63-65`, `print("⚠️ Error logging audit: …")`) → **F-3** |
| `backend/routes/customer_documents.py` | `:828`, `:973`, `:1312`, `:1881` (insert) + `:1372` (read) | **YES** (`main.py:229`) | executable |
| `backend/routes/emissions.py` | `:1073`, `:1209` (insert) + `:886`, `:900` (read) | **YES** (`main.py:226`) | executable |
| `backend/routes/organizations/files.py` | `:1354` (insert) | **YES** (`main.py:255`) | executable |
| `backend/routes/customer_verifications.py` | `:534`, `:662`, `:793`, `:930` (insert) | **NO — unregistered** (imported by nothing) | **dead code** |
| `backend/routes/admin/dashboard.py` | 8 reads + `:1560` insert + `:1487`/`:1500` UPDATE | **NO — unregistered** | **dead code** |
| `backend/routes/customer_dashboard.py` | 4 reads (`:155`, `:597`, `:829`, `:968`) | **NO — unregistered** | **dead code** |
| `backend/routes/admin/audit_logs.py` | 10 reads | **NO — orphan** | **dead code** |
| **Total legacy `from_('audit_logs')` call sites** | **43 across 8 modules** (12 inserts, 31 reads) | — | **F-3 / §14** |

**Authoritative canonical writer:** `data/audit.py::AuditRepository.record` — the only writer
named by the migrations, ADR-V3-013 and the module docstrings. The legacy
`utils/audit_logger.py::log_audit` remains the de-facto writer of the legacy tier but is
referenced by **no** canonical module (`grep -rn 'utils.audit_logger' backend/` → only its own
header); the eight modules that call `from_('audit_logs')` are all legitimately legacy
admin/customer surfaces.

---

## 7. Audit reader / UI inventory

### 7.1 Wired readers (canonical, registered)

| Surface | Route(s) | Registration | Authorization | UI consumer |
|---|---|---|---|---|
| `backend/api/admin_audit.py` (196 lines, prefix `/api/v2/admin/audit`, tag `Admin Audit`) | `GET ""`, `GET /export`, `GET /correlation/{correlation_id}`, `GET /{entry_id}` | `api/router.py:28` import → `:202 router.include_router(audit_router)` → `main.py:265 app.include_router(api_router)` | `require_admin` (`api/dependencies.py`) | **none found** (0 hits for `admin/audit` in `frontend/src`/`admin/src`) |
| `backend/api/v3_reporting.py` | `GET /api/v3/ops/reporting/audit` (`:259`), `GET /api/v3/reporting/audit-readiness` (`:378`), `GET /api/v3/reporting/audit-activity` (`:394`), `GET /api/v3/reporting/consultant-client/{client_id}/audit-activity` (`:427`), `GET /api/v3/ops/entities/{entity_id}/audit-activity` (`:458`) | `api/router.py:67` → `:237` | org owner/admin for customer scope; staff `can_manage_staff` for ops console; consultant/PE scoped | `frontend/src/v3/ops/AuditConsoleTab.jsx` (via `getOpsAudit`), `frontend/src/v3/admin/AuditTab.jsx` (via `getAuditReadiness`, `getAuditActivity`) |
| `backend/api/v3_exports.py` | `GET /api/v3/exports/audit-package.json` (`:90`) | `api/router.py:38` → `:214` | org-scoped | `auditPackageUrl()` in `frontend/src/v3/api.js:1366` |
| `backend/routes/admin/audit.py` (196 lines, prefix `/api/admin/audit`, tag `Admin - Audit`) | `GET /activity`, `GET /activity/{log_id}`, `GET /activity/export`, `GET /activity/search` | `main.py:69` import → `:240 include_router(audit.router)` | `require_admin()` | none (Legacy admin CRA has no audit page) — **reads legacy `activity_logs`**, not `audit_trail` |
| `backend/routes/admin/review_history.py` | `GET /history/audit`, `GET /history/audit/export` (`:113`, `:145`) | `main.py:241` | `require_admin` | legacy admin CRA |
| `backend/routes/logs.py` (+ alias `admin/logs.py`) | `/api/logs/*` read/write over `activity_logs` | `main.py:225` and `:242` | `require_role(["admin","staff"])` / `require_org_member` | legacy |

### 7.2 Legacy readers whose modules are NOT registered

| Module | Reads | Consequence |
|---|---|---|
| `backend/routes/admin/dashboard.py` | 8 `audit_logs` reads (org activity, API request counts, error rate, security events, resolutions) + 1 insert + 2 UPDATEs | module never imported → those admin analytics are **not reachable** |
| `backend/routes/customer_dashboard.py` | 4 `audit_logs` reads (customer activity feed, alerts) | not reachable |
| `backend/routes/customer_verifications.py` | writes only | not reachable |
| `backend/routes/admin/audit_logs.py` | 10 reads (the 12-endpoint console) | not reachable — **the orphan** |

### 7.3 UI surface census

| UI | Path | Wiring | Endpoint |
|---|---|---|---|
| Ops audit console | `frontend/src/v3/ops/AuditConsoleTab.jsx` (filters action/entity/actor/category/origin/outcome/q, 50-row paging) | `OperationsPage.jsx:21,99` tab `audit`, gated by `canManage` | `/api/v3/ops/reporting/audit` |
| Customer audit & evidence tab | `frontend/src/v3/admin/AuditTab.jsx` (readiness + activity + audit package download) | `AdminPage.jsx:20,129` tab `audit`, gated `isAdmin` | `/api/v3/reporting/audit-readiness`, `/audit-activity`, `/api/v3/exports/audit-package.json` |
| Tests | `frontend/src/v3/__tests__/audit-console-tab.test.jsx`, `evidence-trail.test.jsx` | vitest | — |
| Legacy admin CRA | `admin/src/**` — **no audit page**; only `components/LogViewer.jsx`, `components/admin/LogViewer.jsx` | — | none |

### 7.4 Reader conclusion

The canonical audit **read** surface is more capable than the orphan it replaced (taxonomy
filters, server-side ordering, consultant-client and PE-entity scoped reads, JSON evidence
package, CSV export) and is UI-wired. The only *unconsumed* registered audit API is
`/api/v2/admin/audit` (4 endpoints) — registered, tested by the legacy-admin test set, but with
no frontend caller.

---

## 8. Audit coverage matrix

Legend: **Y** = verified present; **P** = partial / only some paths; **N** = verified absent;
**U** = unknown (no evidence found — not inferred). "E2E" = verified end-to-end with evidence
in this read-only audit.

### 8.1 Authentication · user/access · organisation · documents

| Capability | Documented | Code | Writer | Persistence | Reader | Route wired | Tests | E2E | Evidence / notes |
|---|---|---|---|---|---|---|---|---|---|
| Login / logout / failed authentication | P — taxonomy only (`domain/audit.py:93 "logout": CAT_AUTH`) | N | **N** | N (`login_history` exists, **0 writers**) | N | N | N | N | No writer emitting `login`/`logout` audit events found in `backend/`; `routes/users.py:304` calls `supabase.auth.sign_in_with_password` with no audit entry; `admin/dashboard.py:1262` reads `auth.users.last_sign_in_at` (module unregistered) ⇒ **gap / PD-7.4** |
| Password / security-setting change | P (`admin/settings.py:29 max_login_attempts`) | P | **U** | P | P | Y (legacy settings) | U | N | no canonical `security:`-family writer found; legacy settings deprecated (D-P2-02 row 14) |
| User creation / role change / membership change | Y (D-P2-02 rows 1-2; `staff_roles.permissions`) | Y (`v3_organizations`, `admin_aliases`, `admin_entities`) | Y (`repos.audit.record`) | Y (`audit_trail`, 563 rows) | Y (`/api/v2/admin/audit`, ops staff surfaces) | Y | Y (`test_p17_02_accounting_api.py` + ops tests) | P (not re-run here) | canonical path verified by code + populated rows |
| Permission / access grant-revocation | Y (staff-roles catalog) | Y | Y | Y | Y | Y | Y | U | per-operation coverage not enumerated |
| Organisation creation / change | Y | Y (`v3_organizations.py:23,651`) | Y | Y | Y | Y | Y | U | — |
| Tenant membership changes | Y | Y (`v3_organizations`, `admin_aliases`) | Y | Y | Y | Y | Y | U | — |
| Consultant acting-for context | Y (P17/ARCH-04 §10.3) | Y (`AuditEntry.actor_organization_id` / `acting_for_organization_id`; `api/audit_helpers.record_acting_for_attribution`; `api/v3_accounting_context.py:35`) | Y (action `acting_for_attributed`) | Y — **real columns** on `audit_trail` (`20261010000000_p17a:304-308`) | Y (`/api/v3/reporting/consultant-client/{id}/audit-activity`) | Y | Y (`test_p17_migrations.py`, `test_p17_02_accounting_api.py`) | U | per-write-path adoption is **unknown** — only paths that adopted the helper emit attribution |
| Document upload / download / access | Y | Y (`v3_documents`, `customer_documents`) | Y — canonical (`v3_documents.py:618`) **and** legacy (`customer_documents.py:828,973,1312,1881`) | Y | Y | Y | Y | U | **two writers for one domain**; legacy table 0 rows in probes |
| Document extraction / correction / replacement / deletion | Y | Y (`v3_operations.py:1151-1232`; `api/audit_helpers.record_item_extraction_edit`) | Y | Y | Y | Y | Y (`test_f_t1_001_audit_activity_sql_typing.py`) | U | "audit must never break the human edit" (`audit_helpers.py:90-95`) |

### 8.2 Mapping · supplier · emissions · review · reporting · admin · notifications

| Capability | Documented | Code | Writer | Persistence | Reader | Route wired | Tests | E2E | Evidence / notes |
|---|---|---|---|---|---|---|---|---|---|
| Mapping (factor / unit / supplier / facility) | Y | Y (`engines/factor_matching.py:56`; `api/v3_operations.py` item actions) | Y | Y | Y | Y | Y | U | `AuditLogger` injected into `engines/factor_matching.py` |
| Mapping correction | Y | Y (`api/audit_helpers.py:28 changed_extraction_keys`) | Y | Y | Y | Y | Y | U | before/after in `changes` / `old_data` / `new_data` |
| Supplier resolution / correction / reuse | Y (P17 additive columns on `suppliers`) | Y | Y | Y (`audit_trail` + `suppliers.actor_organization_id`) | Y | Y | Y (`test_p17_migrations.py`) | U | — |
| Activity creation / correction | Y | Y | Y | Y | Y | Y | Y | U | — |
| Factor selection / customer-factor governance | Y (customer-factor precedence) | Y (`api/customer_factors.py:39`) | Y | Y | Y | Y | Y | U | factor approvals audited through `repos.audit.record` |
| Unit conversion | Y (`engines/calculation.py`) | Y | P (engine-level) | Y | Y | Y | Y | U | not a first-class event type |
| Calculation / recalculation / estimation | Y | Y (`engines/calculation.py`; `v3_emissions.py:401`; `20261013000000_p17h`) | Y | Y (`audit_trail` + `calculation_snapshots` 100/34 rows) | Y | Y | Y | U | snapshots carry provenance; the audit records the act |
| Manual review opened / assignment / decision | Y (D22) | Y (`v3_operations.py:360-395`; `manual_processing_admin.py:30`; `v3_automatic_processing.py`) | Y | Y | Y (`/api/v3/ops/reporting/review`) | Y | Y | U | "recorded through the existing V3 `audit_trail` (ADR-V3-013)" |
| Review QC / clarification | Y | Y (`api/issues.py`, `v3_qc.py`, `v3_activity_clarifications.py`) | Y | Y | Y | Y | Y | U | — |
| Approval / rejection | Y | Y | Y | Y | Y | Y | Y | U | — |
| Report generation / versioning / modification | Y (D30 lifecycle) | Y (`engines/report_generation.py:53`; `v3_reports.py:61`) | Y | Y | Y | Y | Y | U | `report_versions` = canonical version history (CT-SCHEMA-03) |
| Report approval | Y | Y (`20260913000000_p8_report_lifecycle_status.sql` references `audit_trail`) | Y | Y | Y | Y | Y | U | — |
| Report download / export / sharing | Y (export history) | Y (`routes/organizations/exports.py` → `export_history`) | Y (legacy `export_history`) | Y (0 rows) | Y | Y | Y | N | **no canonical share model** (as CT-SCHEMA-03 PD-2); `audit-package.json` covers evidence export |
| Admin configuration changes | Y (D-P2-04) | Y (`v3_organizations`, `admin_*`) | Y | Y | Y | Y | Y | U | — |
| Factor administration | Y | Y (`admin_imports.py`, `admin_providers.py`, `api/customer_factors.py`) | Y | Y | Y | Y | Y | U | — |
| User administration | Y (D-P2-02 row 1) | Y | Y | Y | Y | Y | Y | U | — |
| Notification creation / delivery / failure / retry | Y | Y (`data/notifications.py`) | Y (`INSERT INTO public.notification_delivery` `:253`) | Y (0 rows at probe; pruned for `ops_alert_%`) | Y (`services/operational_alerting.py`) | Y | Y | U | retention **deletes** delivery rows for ops alerts only (`:265-295`) — deliberate and documented |
| Notification acknowledgement / open | N | N | N | N | N | N | N | N | no read/acknowledgement audit found |
| Message activity | Y (legacy carrier `message_activity_log`) | Y (`v3_messaging.py:320`, canonical) | P (legacy carrier has **no writer**) | P (0 rows) | P (only the orphan reads it) | P | U | N | canonical messaging audits to `audit_trail`; legacy carrier dormant |
| Verification activity | Y (legacy carrier) | Y (`routes/emissions.py:900` read; writes only in unregistered modules) | P | P (0 rows) | P | P | U | N | carrier retained but unreachable as a read surface |
| Data-access logging (who read what) | N (no policy found) | N | N | N | N | N | N | N | **no read-access audit exists** — explicitly a PD-7 scope item (B) |
| Immutable/append-only guarantee | Y (Phase 7 + DB-0001) | Y | n/a | Y | n/a | n/a | Y (`test_audit_immutability_migration.py`, `test_p7_auditability.py`) | **Y (DDL-level, verified live in §10)** | trigger + policy evidence from `ct_schema01_pg` |

### 8.3 Coverage verdict

* **Ledger coverage is broad**: ~26 domains have a canonical writer; the strongly-covered
  domains are processing operations, consultants/acting-for, PE, messaging, documents,
  reporting, disclosures, evidence, commercial/billing, issues, automatic processing.
* **Verified gaps**: authentication events (login/logout/failed), read/data-access logging,
  notification acknowledgement, per-user activity roll-ups, message/verification activity
  sub-surfaces.
* **Not verified in this audit**: that every one of the 35 canonical call sites actually fires
  in each environment (no E2E run performed — read-only mandate).

---

## 9. Multi-tenant / consultant actor-context analysis (P17)

**Question:** can an audit event distinguish *"Consultant user acting on behalf of Client A"*
from *"Client A user acting directly"*, and does it capture actor organisation, data-owner
organisation and downstream effect?

### 9.1 The canonical ledger represents it — measured

| Attribute required by the brief | Canonical carrier | Evidence |
|---|---|---|
| actor | `audit_trail.performed_by` (uuid; non-UUID labels → zero-UUID) | `data/audit.py:51-57`, `_AUDIT_COLUMNS :29-33` |
| actor type | `metadata.actor_type` (`ACTOR_TYPES` taxonomy) | `domain/audit.py:89-91` |
| actor class (`human`/`system`) | `metadata.origin` via `classify_origin(actor, actor_type)` | `domain/audit.py:190-204` |
| **actor organisation** (the org the actor BELONGS to) | **`audit_trail.actor_organization_id` (real column)** | live column verified in `ct_schema01_pg`; added `20261010000000_p17a:304-308` |
| **data-owner organisation** | `metadata.organization_id` (queryable: `metadata->>'organization_id'`, partial index `idx_audit_trail_org`) | `data/audit.py:196`; `20260912000000:73-76` |
| **"ACTING FOR" context / consultant organisation** | **`audit_trail.acting_for_organization_id` (real column)** | same ALTER; action `acting_for_attributed` |
| target resource | `table_name` (entity type) + `record_id` (entity id) | `_AUDIT_COLUMNS` |
| action | `action_type` (+ canonical `category` derived by `classify_action`) | `domain/audit.py:163-188` |
| timestamp | `performed_at` / `created_at` | DDL |
| source | `ip_address` (inet), `user_agent` | DDL |
| before/after state | `old_data`, `new_data`, `changes` jsonb | DDL + `record()` |
| reason | `metadata.reason` | `data/audit.py:60` (`_entry_metadata`) |
| downstream effect | `correlation_id` (all entries of one request/pipeline run) + `AuditRepository.get_by_correlation()` | `data/audit.py:296-306` |
| outcome | `metadata.outcome` (`success`/`failure`) | `domain/audit.py:94-95` |

### 9.2 Verdict on consultant-vs-client distinguishability

**REPRESENTABLE AND IMPLEMENTED (canonical tier); NOT REPRESENTABLE (legacy tier).**

* Canonical: yes. `record_acting_for_attribution` (`api/audit_helpers.py:95-146`) writes
  `action="acting_for_attributed"` with `changed_fields` carrying
  `{carrier, owner_organization_id, acting_for_organization_id, actor_organization_id}`, and
  its docstring states the values come *"from the SERVER-RESOLVED accounting context, never
  from the request payload, so the ledger records who the actor actually was entitled to act
  for rather than what the caller claimed"* — i.e. the distinction is tamper-resistant by
  construction. Read-side support exists: `GET /api/v3/reporting/consultant-client/{client_id}/
  audit-activity` (`api/v3_reporting.py:427`) and `/api/v3/ops/entities/{entity_id}/
  audit-activity` (`:458`).
* Legacy: no. `audit_logs` has `user_id`, `staff_id`, `organization_member_id`,
  `organization_id` only — no actor/owner/acting-for triple — so no legacy row can express
  "consultant acting for client" distinctly from "client user".
* **Gap (documented, not decided):** the *proportion of write paths* that adopt
  `record_acting_for_attribution` is **unknown** — no coverage map exists, and `AuditEntry`'s
  P17 fields default to `None` "so all existing behaviour is unchanged (the column simply
  stays NULL)" (`domain/audit.py:100-108`). Nullable columns plus opt-in calls mean an
  attribution-blind event is indistinguishable from an attribution-bearing one **only if**
  callers are audited per path — a verification task, listed in §20.

### 9.3 Tenant isolation of the audit read surfaces

* Scoped reads are server-side: customer audit activity requires org owner/admin
  (`frontend/src/v3/admin/AuditTab.jsx` header: *"Authorization is server-side (organisation
  owner/admin only); this tab is a UX convenience and is never the security boundary"*);
  ops console requires `can_manage_staff`; consultant-client and entity reads are
  relationship-scoped (`api/v3_reporting.py:427,458`).
* RLS on `audit_trail` is deny-by-default with **zero policies** (§10) ⇒ PostgREST clients
  cannot read the ledger at all, independent of UI.
* RLS on `audit_logs` grants SELECT to `is_org_member(organization_id) OR
  is_org_consultant(organization_id)` — i.e. **consultants are explicitly allowed to read
  their client's legacy audit rows**, consistent with the AGENTS.md consultant operating
  model.

---

## 10. Immutability / security analysis (live DDL evidence)

Probe: `/tmp/aud1_probe3.sh` against the canonical rebuild `ct_schema01_pg`
(raw output `/tmp/aud1_dbprobe3.txt`).

### 10.1 Measured state — Tier 1 (`audit_trail`)

| Property | Value |
|---|---|
| Columns (17) | `id`, `action_type`, `table_name`, `record_id`, `performed_by`, `performed_at`, `old_data`, `new_data`, `changes`, `ip_address` (inet), `user_agent`, `metadata`, `created_at`, **`actor_organization_id`**, **`acting_for_organization_id`** |
| RLS enabled / forced | `relrowsecurity = true`, `relforcerowsecurity = false` |
| Policies | **NONE** (zero rows in `pg_policies`) ⇒ deny-by-default for `anon`/`authenticated` |
| Trigger | `p7_audit_trail_immutable` (BEFORE UPDATE OR DELETE, FOR EACH ROW) |
| Function | `p7_audit_trail_immutable()` — `RAISE EXCEPTION 'audit_trail is append-only (Phase 7): % is not permitted'` |
| Grants | `authenticated` and `service_role`: DELETE, INSERT, SELECT, UPDATE (grants are overridden by RLS + trigger) |
| Intended model | **append-only, trigger-generated enforcement for every role** — migration comment: *"the trigger fires for every role, including the service role used by the backend — so the ledger is append-only at the database, not merely by convention. A future authorised retention/purge process must deliberately drop this trigger first (documented, controlled)."* (`20260912000000:24-27`) |

### 10.2 Measured state — Tier 2 (`audit_logs`)

| Property | Value |
|---|---|
| RLS enabled / forced | `true` / `false` |
| Policies (live) | `audit_logs_tenant_insert` (INSERT → `authenticated`, `is_org_member(organization_id)`), `audit_logs_tenant_select` (SELECT → `authenticated`, `is_org_member(organization_id) OR is_org_consultant(organization_id)`) |
| UPDATE / DELETE policies | **dropped** by `20260831020000` (DB-0001) ⇒ ordinary users cannot mutate history |
| Triggers | **none** |
| Grants | `authenticated`: DELETE, INSERT, SELECT, UPDATE; `service_role`: full DML incl. TRUNCATE |
| Residual exposure | (i) `authenticated` retains a **client-side INSERT path** into `audit_logs` for own-org rows; (ii) **`service_role` can UPDATE/DELETE audit_logs with no trigger guard** — unlike `audit_trail`. This asymmetry is a stated audit-completeness question for the PO, not a defect claim: the DB-0001 hardening explicitly targeted *"ordinary authenticated users"*. |

### 10.3 Related immutability surfaces

* `activity_feed` — UPDATE/DELETE **intentionally retained** and re-scoped to the row owner
  (`user_id = auth.uid()`), because it is a user-facing read/unread feed (`20260831020000:37-42`).
* `calculation_snapshots` — append-only by design + SHA-256 `content_hash`
  (`20260912000000:18-19`); 100 rows in the dev DB, 34 in the demo DB.
* `notification_delivery` — **prunable** for `notification_type LIKE 'ops_alert_%'` only
  (`backend/data/notifications.py:265-295`); ordinary notification delivery is never pruned.

### 10.4 Retention interplay (N3)

The only retention code that touches audit-adjacent telemetry is the operational-alert prune
above. There is **no** retention path for `audit_trail` — by design it is immutable, so any
N3 retention rule for the audit ledger would require dropping the trigger (documented as a
deliberate, controlled operation). This is a **PO decision interaction** (PD-7.F) rather than
an engineering bug: the current state is internally consistent (immutable ledger + no purge).

### 10.5 Security evidence for the audit subsystem

* `backend/tests/unit/api/test_audit_immutability_migration.py`,
  `backend/tests/unit/api/test_p7_auditability.py`,
  `backend/tests/unit/domain/test_audit.py`, `test_audit_p7.py`,
  `backend/tests/unit/infra/test_audit_logger.py`,
  `backend/tests/unit/data/test_f_t1_001_audit_activity_sql_typing.py`,
  `backend/tests/integration/test_audit.py`, `test_audit_logger.py` — **8 dedicated audit
  test modules**; 17 further test files reference `audit_trail`; 196 test files mention
  `audit` (whole-repo count).
* The audit read APIs are authorization-guarded server-side (`require_admin`,
  `can_manage_staff`, org owner/admin, consultant/entity scoping) — no reliance on UI gating.

### 10.6 Defect found while auditing (reported, not fixed)

**F-4 — `/api/admin/audit/activity/export` is shadowed by `/api/admin/audit/activity/{log_id}`.**
In `backend/routes/admin/audit.py` the parameterised route is registered at `:76`
(`async def get_activity_log_detail(log_id: str, …)`) *before* the literal route at `:106`
(`@router.get("/activity/export")`), and FastAPI matches in registration order ⇒ a request for
the CSV export is routed to the detail handler with `log_id="export"` and returns
`404 "Activity log not found"`. The export endpoint is therefore effectively unreachable.
Engineering-only fix (route ordering); **not applied** under this read-only mandate.

---

## 11. Current route registration status

### 11.1 Method

`grep -n 'include_router' backend/main.py` (38 mounts + 1 conditional V3 mount),
`grep -n 'include_router' backend/api/router.py` (53 mounts; V3 composition root mounted at
`main.py:265`), `backend/routes/admin/__init__.py`, and the import blocks at `main.py:40-100`.

### 11.2 Audit-relevant modules

| Module | Registered? | Registration point | Notes |
|---|---|---|---|
| `backend/api/admin_audit.py` | **YES** | `api/router.py:28` → `:202` → `main.py:265` | canonical admin audit trail API (`/api/v2/admin/audit`, 4 endpoints) |
| `backend/api/v3_reporting.py` | **YES** | `api/router.py:67` → `:237` | 5 audit read endpoints incl. consultant-client and entity scope |
| `backend/api/v3_exports.py` | **YES** | `api/router.py:38` → `:214` | `/api/v3/exports/audit-package.json` |
| `backend/api/v3_operations.py`, `v3_consolidated` writers (`v3_*`), `engines/*`, `workers/automatic_processing.py` | **YES** (imported by the V3 root) | `api/router.py` + engine wiring | canonical audit *writers* |
| `backend/routes/admin/audit.py` | **YES** | `main.py:69` → `:240` | legacy activity-log reader over `activity_logs` |
| `backend/routes/admin/review_history.py` | **YES** | `main.py:241` | review audit trail reader |
| `backend/routes/logs.py` / `admin/logs.py` | **YES** | `main.py:225`, `:242` | `activity_logs` read/write |
| `backend/routes/reports.py` | **YES** | `main.py:214` | legacy `audit_logs` reads (3 sites) |
| `backend/routes/emissions.py` | **YES** | `main.py:226` | legacy `audit_logs` read + 2 inserts |
| `backend/routes/customer_documents.py` | **YES** | `main.py:229` | legacy `audit_logs` inserts (4) |
| `backend/routes/organizations/files.py` | **YES** | `main.py:255` | legacy `audit_logs` insert (1) |
| **`backend/routes/admin/audit_logs.py`** | **NO — ORPHAN** | absent from `main.py`, `routes/admin/__init__.py`, any import anywhere, and *every* commit on every ref | **the CT-SCHEMA-03 orphan, confirmed** |
| `backend/routes/admin/dashboard.py` | **NO** | not imported (`routes/admin/__init__.py` exports staff, defra, extraction, reviews, assignments, permissions, workload, beta, audit, review_history, logs→admin_logs, bulk→admin_bulk, email_templates, analytics→admin_analytics, settings) | stale |
| `backend/routes/customer_dashboard.py` | **NO** | imported by nothing | stale |
| `backend/routes/customer_verifications.py` | **NO** | imported by nothing | stale |
| `backend/routes/admin/document-types.py`, `routes/communication.py` | **NO** | documented stale set (`CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md:65`) | stale |

### 11.3 The orphan's absence is provable three ways

1. **Static**: `grep -rn 'audit_logs' backend/main.py backend/routes/admin/__init__.py` → no
   import/registration line; `grep -n 'audit' backend/main.py` → only `audit` (the *other*
   module) at `:69`, `:131`, `:240`.
2. **Historical**: `git log --all -S 'audit_logs' -- backend/main.py backend/routes/admin/__init__.py`
   → **empty** (never registered in any commit on any ref).
3. **Consumer**: `grep -rn 'api/admin/audit-logs' frontend/src admin/src qa_harness` → **0 hits**;
   `git log --all -S 'admin/audit-logs' -- frontend admin` → **empty** (never consumed by any
   frontend in the repository's history).

### 11.4 Documentation contradicts the runtime (F-1)

| Document | Claim | Reality |
|---|---|---|
| `API_ENDPOINTS.md:90-105` | lists `routes\admin\audit_logs.py` endpoints with **✅** (live) status | none are routable |
| `docs/architecture/API_DOCUMENTATION.md:55-62,99` | documents `/api/admin/audit-logs/*` as current ("NEW FILE") | orphan |
| `docs/architecture/filestructure.md:6` | `audit_logs.py  # ✅ NEW` | orphan |
| `docs/architecture/changelog.md:12,111,550` | "Audit log endpoints (6 endpoints)" / "✅ NEW" | orphan |
| `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:611` (FTR-207) | "Audit console (admin + ops tabs) … IMPLEMENTED_AND_WIRED … API:`/api/v2/admin/audit`(4), legacy `/api/admin/audit-logs`(12)" | the 4 are wired; the 12 are **not** — the catalogue counts orphan endpoints as part of the wired console |
| `docs/cline/CarbonTally_Backend_Module_Inventory_V3.md:94` | 12 endpoints, "EXTEND / REVIEW" | accurate as an inventory, silent on reachability |
| `docs/audit/cline/CARBONTALLY_V3_ARCHITECTURE_CONFORMITY_GATE.md:174,257,649` | "`audit_logs.py` stale"; superseded by `api/admin_audit.py` + `data/audit.py` | **correct** |
| `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:27,58-60` | D-P2-02: legacy admin **and** `/api/v2/admin/audit` are DEPRECATED, not deleted; row 7 names `/api/v2/admin/audit` the V3 replacement for audit | internally inconsistent: row 7 promotes what §5 deprecates, and the *actual* wired console is `/api/v3/ops/reporting/audit` (PD-7.2) |

---

## 12. What is genuinely implemented (code + persistence + wiring + tests)

1. **The canonical audit ledger** — `public.audit_trail` (17 live columns), populated with
   **563** rows (dev DB) and **242** rows (investor demo DB).
2. **Canonical writer stack** — `domain/audit.py` (model + taxonomy) → `data/audit.py`
   (`AuditRepository.record/query/count/export_csv/get_by_correlation`) →
   `infra/audit_logger.py` (`AuditLogger`, `@audit` decorator) wired through
   `api/dependencies.py`; **35** shipping call sites across ~35 modules (engines, workers,
   V3 APIs, services).
3. **Append-only enforcement at the database** — trigger `p7_audit_trail_immutable`, fires for
   every role including `service_role`; verified live on `ct_schema01_pg`.
4. **Deny-by-default RLS on the ledger** — RLS enabled, **zero policies**; no PostgREST path
   can read or write it.
5. **Registered read APIs** — `/api/v2/admin/audit` (4 endpoints, `require_admin`) and five V3
   audit reads including consultant-client and PE-entity scoped activity.
6. **Registered UI** — ops audit console tab (`AuditConsoleTab.jsx`, taxonomy filters, paging)
   and customer audit & evidence tab (`AuditTab.jsx`, readiness + activity + JSON package).
7. **Consultant "acting-for" attribution** — dedicated ledger columns + server-resolved
   helper + read scoping (§9).
8. **Correlation-based reconstruction** — `correlation_id` + `get_by_correlation()` +
   `GET /api/v2/admin/audit/correlation/{correlation_id}`.
9. **CSV/spreadsheet + JSON package export** of audit data.
10. **Test coverage of the audit subsystem** — 8 dedicated audit test modules + 17 files
    asserting on `audit_trail` (including migration-level immutability assertions).
11. **Legacy tier retained and hardened** — `audit_logs`, `activity_logs`,
    `document_activity_log` now immutable for ordinary users (DB-0001), still present in the
    canonical schema (so no schema drift), and still readable by the registered legacy
    surfaces (`reports.py`, `emissions.py`).

## 13. What is merely documented (no runtime path)

| Item | Where documented | Reality |
|---|---|---|
| 12 legacy admin audit-console endpoints | `API_ENDPOINTS.md` (✅ flags), `API_DOCUMENTATION.md`, `filestructure.md`, `changelog.md`, FTR-207 | **no route registered; no consumer** |
| `/api/admin/audit-logs` as part of the "wired audit console" | `CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:611` | over-counted |
| `/api/v2/admin/audit` as the canonical V3 audit UI API | `CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:27` | registered but **no UI consumer**; the wired console uses `/api/v3/ops/reporting/audit` |
| User activity history / audit statistics aggregates | legacy console design | only `actor=` filtering exists canonically |
| Login/logout/failed-auth auditing | taxonomy entry `"logout": CAT_AUTH` (`domain/audit.py:93`); `login_history` table | **no writer**; `login_history` 0 rows, 0 code references |
| `message_activity_log`, `notification_delivery_log`, `verification_activity_log` as activity sub-surfaces | legacy console + docs | carriers exist (except `notification_delivery_log`), but **no live writer** and no live reader except the orphan |
| Dormant history tables | `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md:290` — *"Dormant duplicate history tables remain (`staff_activity_log`, `user_activity_log`, `processing_time_log`, `verification_logs` — no code references)"* | **independently re-measured**: `user_activity_log` 0 backend references, `processing_time_log` 0, `processing_audit_trail` 0, `login_history` 0, `staff_activity_log` only a handler *name* in unregistered `admin/staff.py`, `verification_logs` only a handler name in the orphan ⇒ confirmation supported |

## 14. What is broken (current defects, with evidence)

| ID | Severity | Defect | Evidence |
|---|---|---|---|
| **F-1** | High (documentation-truth) | 12 endpoints documented as live (✅) but unrouted; feature catalogue counts them as wired | `API_ENDPOINTS.md:90-105`; FTR-207 `:611`; runtime §11.3 |
| **F-2** | Medium (latent trap, = CT-SCHEMA-03 SCM-007) | orphan reads absent table `notification_delivery_log` → would 500 if ever wired | `audit_logs.py:404`; `notification_delivery_log` ABSENT in 4 databases |
| **F-3** | Medium (silent audit loss) | `utils/audit_logger.log_audit` swallows **all** exceptions and returns `None`; the 12 legacy insert sites therefore fail silently; consistent with `audit_logs` = 0 rows in every probed DB despite reachable call sites | `utils/audit_logger.py:63-65`; probe §5.1 |
| **F-4** | Medium | `/api/admin/audit/activity/export` shadowed by `/api/admin/audit/activity/{log_id}` (route order) → export unreachable | `routes/admin/audit.py:76` before `:106` |
| **F-5** | Low/Medium (asymmetry) | `service_role` can UPDATE/DELETE `audit_logs` (no trigger) while `audit_trail` is trigger-protected for every role | live probe §10.2 |
| **F-6** | Low (doc inconsistency) | D-P2-02 row 7 names `/api/v2/admin/audit` as the V3 replacement while §5 deprecates it | `CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:27` vs `:58` |
| **F-7** | Low | Legacy `audit_logs` still carries an `authenticated` INSERT policy + grant (client-side writes possible for own-org rows) | live probe §10.2 |
| **F-8** | Informational | Three stale modules (`admin/dashboard.py`, `customer_dashboard.py`, `customer_verifications.py`) are not registered yet still contain audit code, inflating every code↔schema census (CT-SCHEMA-03 counted only 5 `defra_conversion_factors` hits; the same pattern applies to `audit_logs`: 43 sites, of which 21 belong to unregistered modules) | §6.2, §7.2 |

**None of these is "the audit system is broken".** The canonical ledger works; the defects are
documentation truth, orphan hygiene, one route-ordering bug and legacy-tier asymmetry.

## 15. What is orphaned

| Object | Type | Evidence | Assessment |
|---|---|---|---|
| `backend/routes/admin/audit_logs.py` (V-01…V-10) | module · 12 endpoints · 9 models | never imported/registered/consumed (§11.3) | **ORPHAN — CT-SCHEMA-03 classification CONFIRMED** (never registered in any commit, not merely currently unregistered) |
| `backend/routes/admin/dashboard.py` | module (admin analytics incl. 11 `audit_logs` sites) | not imported | orphan |
| `backend/routes/customer_dashboard.py` | module (4 `audit_logs` reads) | not imported | orphan |
| `backend/routes/customer_verifications.py` | module (4 `audit_logs` inserts) | not imported | orphan |
| `backend/routes/admin/document-types.py`, `backend/routes/communication.py` | modules | documented stale set (`CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md:65`) | orphan (non-audit; listed for completeness of the same class) |
| Legacy carriers with **no writer**: `user_activity_log`, `staff_activity_log`, `processing_audit_trail`, `processing_time_log`, `login_history`, `message_activity_log`, `verification_logs` | tables | 0 code references each (or handler-name-only hits) | dormant schema |
| `/api/admin/audit/*` (4 endpoints, registered, `require_admin`, reads `activity_logs`) | registered API | registered but **no consumer**; deprecated by D-P2-02 while simultaneously named as the audit replacement | **"wired but unconsumed"** — distinct from orphan |

## 16. What was superseded (and by what)

| Superseded object | Superseded by | Evidence | Form of supersession |
|---|---|---|---|
| `routes/admin/audit_logs.py` (legacy audit console API, 12 endpoints) | `api/admin_audit.py` + `data/audit.py` (+ `api/v3_reporting.py` audit reads) | `CARBONTALLY_V3_ARCHITECTURE_CONFORMITY_GATE.md:649`; `CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md:65,161` | documented replacement, deletion deferred (D-P2-02 "deprecated, not deleted") |
| `audit_logs` as *the* audit ledger | `audit_trail` (canonical, ADR-V3-013 "no new history table") | `20260912000000:9-19` | **ledger superseded; table retained** (immutable, still canonical for the legacy tier) |
| `activity_logs` / `document_activity_log` as audit history | `audit_trail` | same migration header | retained, immutable, still used by registered legacy surfaces (`admin/audit.py`, `logs.py`) |
| Duplicate history surfaces (`staff_activity_log`, `user_activity_log`, `processing_time_log`, `verification_logs`, `processing_audit_trail`, `login_history`, `reassignment_history`) | `audit_trail` + `domain_events` + `review_assignment_history` + `calculation_snapshots` | `CT-FEATURE-AUDIT-P1-P8X-001.md:290` ("consolidate or retire the dormant history surfaces") | **identified for consolidation — not yet consolidated** |
| `notification_delivery_log` (legacy) | `notification_delivery` + `notifications` | SCM-007; `data/notifications.py:253` | replaced (legacy name never migrated) |
| `/api/v2/admin/audit` (per D-P2-02 §5) | `/api/v3/ops/reporting/audit` etc. | `CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:27` vs `:58` | **unresolved** — see PD-7.2 |

## 17. What remains unknown (explicitly not inferred)

| # | Unknown | Why unresolved | What would resolve it |
|---|---|---|---|
| U-1 | Whether the 35 canonical `repos.audit.record` call sites all pass `actor_organization_id`/`acting_for_organization_id` | opt-in nullable columns; no per-path coverage map; no E2E run authorised | static call-site audit + a targeted E2E write per path |
| U-2 | Whether legacy writers ever succeeded in production | legacy insert sites swallow exceptions; all probed DBs show 0 rows; production never touched | read-only production row count / application logs (PO-authorised) |
| U-3 | Why `audit_trail` and `calculation_snapshots` are populated while all legacy audit tables are empty | no runtime instrumentation available read-only | DB-level write history, logs, or a controlled E2E run |
| U-4 | Whether `/api/v2/admin/audit` is intended to survive the D-P2-02 deprecation | document contradicts itself (row 7 vs §5); tests depend on it | PO decision PD-7.2 |
| U-5 | Whether authentication events are audited anywhere outside the app (Supabase Auth internal logs) | out of repository scope; GoTrue log retention is environment-specific | environment inspection (not part of this mandate) |
| U-6 | Whether any consumer outside the repository (deployment tooling, external callers) uses `/api/admin/audit-logs` | only local scope searched (frontend, admin, qa_harness, docs) | API gateway logs / external contract review |
| U-7 | Exact per-table column counts and constraint counts of the 30-odd audit-family tables | this audit measured only presence/rows and the two principal tables' columns | schema-diff pass (CT-SCHEMA-01/02 style) per table |
| U-8 | Whether the p7 trigger has ever blocked a legitimate retention/purge attempt | no execution history available read-only | operational logs |

---

## 18. PO decisions required

**This audit decides none of these.** Options and evidence only.

### PD-7 — Canonical Audit & Access History (architecture level)

| Sub-scope | Question for the PO | Evidence available now |
|---|---|---|
| **A. Comprehensive audit event history** | Is `public.audit_trail` (ADR-V3-013) the single lasting audit ledger for all surfaces, with the legacy tier formally retired as a *capability*? | §5 parity table, §6, §12 |
| **B. Data-access logging** | Must read/access events (who viewed or downloaded which record) be audited? **No such capability exists today.** | §8.2 row "Data-access logging = N" |
| **C. Change history** | Is before/after change history required for every domain, or only for the domains already covered? | §8 coverage matrix (26 domains with writers, gaps listed) |
| **D. Provenance** | Is the existing chain (document → extraction → factor → validation → snapshot → emissions → evidence → audit) sufficient, or must it be extended? | `audit_trail` + `calculation_snapshots.content_hash` |
| **E. Security events** | Must authentication events (login/logout/failed/password change) and authorisation denials be audited? Today they are **not**. | §8.1 row 1; `domain/audit.py:93` (taxonomy only) |
| **F. Retention** | How does N3 retention apply to an immutable ledger? `audit_trail` is currently **unpurgeable without dropping the trigger**. | §10.4; `20260912000000:24-27` |
| **G. Immutable / append-only behaviour** | Confirm append-only for **every role including `service_role`**, and whether the lesser protection of legacy `audit_logs` (F-5) is acceptable or must be raised. | §10.1 vs §10.2 |
| **H. Consultant / client actor context** | Must `actor_organization_id` / `acting_for_organization_id` be **mandatory** on ledger writes (making U-1 a requirement rather than caller discipline), and do legacy carriers need equivalent columns? | §9; `domain/audit.py:100-108` (currently optional) |

### Additional decisions arising from this archaeology

| ID | Decision required | Options | Evidence |
|---|---|---|---|
| **PD-7.1** | Fate of the orphaned 12-endpoint legacy audit console (`audit_logs.py` × 10 copies) | (i) leave frozen unregistered (current); (ii) formally retire with a documented replacement note; (iii) re-point at canonical tables and register | §2, §5.3, §11.3 |
| **PD-7.2** | Status of `/api/v2/admin/audit` — canonical, retired, or retained-but-deprecated | registered + tested, but named "V3 replacement" in one place and "DEPRECATED" in another, with no UI consumer | `CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:27` vs `:58` (F-6) |
| **PD-7.3** | Whether the seven dormant audit/history tables should be consolidated or retired (ADR-V3-013 already recommends consolidation) | consolidate / retire / retain unmapped | §16; `CT-FEATURE-AUDIT-P1-P8X-001.md:290` |
| **PD-7.4** | Whether authentication and authorisation-denial events must be audited (currently absent) | add writers / accept gap / delegate to Supabase Auth logs | §8.1 |
| **PD-7.5** | Whether legacy `audit_logs` keeps its `authenticated` INSERT path and `service_role` UPDATE/DELETE ability (F-5, F-7) | tighten to append-only-for-all like `audit_trail` / leave as-is | live probe §10.2 |
| **PD-7.6** | Whether the legacy activity sub-surfaces (message / notification / verification activity history) must be re-provided on canonical carriers | re-provide / drop formally | §5.3 regressions |

## 19. Engineering-only remediation candidates (no policy decision needed)

| # | Candidate | Risk | Note |
|---|---|---|---|
| E-1 | Correct documentation truth: remove the ✅ flags for the orphan's endpoints in `API_ENDPOINTS.md`, mark `API_DOCUMENTATION.md` / `changelog.md` / `filestructure.md` entries as historical, and annotate FTR-207 so the 12 endpoints are not counted as wired | none (docs) | must not alter ratified decisions |
| E-2 | Fix the route-ordering shadowing of `/api/admin/audit/activity/export` (F-4) — register the literal route before `/activity/{log_id}`, or constrain the path parameter to a UUID | low | small and testable |
| E-3 | Add a **reachability guard** for the stale-module class (a repository check that flags unregistered route modules containing live-looking schema reads) so F-1/F-2/F-8 cannot recur silently | low | aligns with AGENTS.md §74 ("no false completion") |
| E-4 | Record the audit-family orphans (`audit_logs.py`, `admin/dashboard.py`, `customer_dashboard.py`, `customer_verifications.py`) in the existing legacy-retirement tracker rather than scattered docs (D-P2-02 §4 conditions) | low | no code change |
| E-5 | **Do not** "make it work" by recreating `notification_delivery_log`; the orphan's dependency must not drive schema | — | explicit non-action, recorded so a future agent cannot silently reverse it (AGENTS.md §15; CT-SCHEMA-03 F-01 spirit) |
| E-6 | **Do not** delete `audit_logs.py` (or any copy) while D-P2-02 §4 retirement conditions are unmet | — | explicit non-action |

**Out of scope for engineering:** any decision to retain/delete/recreate audit tables, any change
to the RLS/immutability model, and any new audit architecture.

## 20. Recommended next investigation / implementation sequence

1. **PO**: decide PD-7 (A–H) and PD-7.1…PD-7.6. No audit-model change should precede this.
2. **Investigation (read-only)**: U-1 — a static coverage map of the 35 canonical call sites
   showing which pass `actor_organization_id` / `acting_for_organization_id`. Cheap,
   deterministic, zero runtime risk.
3. **Investigation (read-only, PO-authorised)**: U-2/U-3 — establish why legacy writers
   persist 0 rows. Any E2E must run in a disposable clone; **never** the investor demo DB and
   never production (AGENTS.md §55.1; CT-SCHEMA-03 safety invariant).
4. **Engineering (docs + low-risk code)**: E-1, E-2, E-3, E-4 once step 1 authorises.
5. **Independent verification**: audit read paths (`/api/v2/admin/audit`,
   `/api/v3/ops/reporting/audit`, `/api/v3/reporting/audit-activity`,
   `/consultant-client/{id}/audit-activity`, `/ops/entities/{id}/audit-activity`,
   `/api/v3/exports/audit-package.json`) plus negative tests — non-admin denied, cross-tenant
   denied, consultant scope enforced, ledger UPDATE/DELETE rejected.
6. **Only then** consider consolidation/retirement of dormant surfaces (PD-7.3) as its own
   migration-backed change with its own report.

---

## 21. Evidence index (exact paths, SHAs, artefacts)

### 21.1 Repository state

| Item | Value |
|---|---|
| Working repository | `/home/shomonrobie/ct_93d5cdd` |
| HEAD / branch | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` / `p8-release-reconciled` |
| Git refs searched | all refs (`git log --all`) for `backend/routes/admin/audit_logs.py`, `backend/main.py`, `backend/routes/admin/__init__.py`, `frontend/`, `admin/`, and every audit migration |
| Sibling checkouts inspected | `carbon_tally` `20b7a92` · `carbon_tally_p8_release` `0be7438` · `workspace/project/0000789…` `0be7438` · `Documents/carbon_tally_backup_25_aug_2025` `878bd0f` · `workspace/project/0581…/CarbonTally_audit` `2fd4345` · `workspace/project/fd01b4…/carbon_tally_audit` `9458067` · `workspace/project/carbontally_uiux_audit` `d4dcca1` · `workspace/project/carbontally_docs_publish` `9339a9b` |
| Copy hashes | normalised `md5 = 1058bf33c3948df3affb91b198902f5f` (all 10); `sha256` short `042e7dae…` (CRLF ×6) / `a6fdb0b1…` (LF ×4) |

### 21.2 Commits cited

| SHA | Date | Message |
|---|---|---|
| `eed55d62ee9f103279d0d2a94006952a517d3bde` | 2026-08-06 | CarbonTally RC2 Final database baseline (adds `audit_logs.py`, `init_schema.sql`) |
| `2d23fb892921cbc41d6c0c20b7660e86fc968178` | 2026-08-06 | CarbonTally RC2 Final database baseline |
| `077c866fdd9c9cf0d6ca418685b357bea6ed5691` | 2026-08-27 | feat: finalize v3 ux and promote public website |
| `daad396523ac693352cc2f4ebb7fc58814a9e60b` | 2026-09-11 | release: establish CarbonTally production release 1 (adds `20260831020000_audit_activity_immutability.sql`) |
| `436815721aa2ec4b1d8ccd4f23d80c196fdbb109` | 2026-09-12 | feat(phase7): auditor/assurance auditability, taxonomy, evidence package (adds `20260912000000_p7_audit_immutability_and_indexes.sql`) |
| `52826607b88071db6b3e10cd7f98f08362c9a4bf` | 2026-09-25 | feat(p17): add CAMS accounting-dimension and boundary migrations (adds `20261010000000_p17a_…sql`) |

### 21.3 Code artefacts

| Path | Relevance |
|---|---|
| `backend/routes/admin/audit_logs.py` | the orphan (12 endpoints, 9 models, 1431 lines) |
| `backend/routes/admin/audit.py` | registered legacy activity-log reader (`/api/admin/audit`); contains F-4 |
| `backend/api/admin_audit.py` | canonical admin audit-trail API (`/api/v2/admin/audit`, 4 endpoints) |
| `backend/data/audit.py` | `AuditRepository` → `public.audit_trail` (INSERT / query / count / export_csv / correlation) |
| `backend/domain/audit.py` | `AuditEntry` / `AuditTrail` / `AuditQuery`; taxonomy incl. `CAT_AUTH` at `:93` |
| `backend/infra/audit_logger.py` | `AuditLogger` / `AuditSink` / `@audit` decorator (254 lines) |
| `backend/utils/audit_logger.py` | legacy writer to `audit_logs`; swallows exceptions (F-3) |
| `backend/api/audit_helpers.py` | `record_item_extraction_edit`, `record_acting_for_attribution` (P17) |
| `backend/api/v3_reporting.py` | 5 audit read endpoints (org / consultant-client / entity scoped) |
| `backend/api/v3_exports.py` | `/api/v3/exports/audit-package.json` |
| `backend/data/notifications.py` | `notification_delivery` writer + ops-alert retention prune |
| `backend/main.py` | legacy mount table (`:212-259`), V3 mount (`:265`), admin imports (`:60-78`) |
| `backend/api/router.py` | V3 composition root (`:202` audit, `:214` exports, `:237` reporting) |
| `backend/routes/admin/__init__.py` | package exports (proves `audit_logs` is absent) |
| `frontend/src/v3/ops/AuditConsoleTab.jsx` + `OperationsPage.jsx:21,99` | wired ops audit console |
| `frontend/src/v3/admin/AuditTab.jsx` + `AdminPage.jsx:20,129` | wired customer audit & evidence tab |
| `frontend/src/v3/api.js:1325-1371` | `getOpsAudit`, `getAuditReadiness`, `getAuditActivity`, `getConsultantClientAuditActivity`, `auditPackageUrl` |

### 21.4 Schema / migration artefacts

`supabase/migrations/00000000000000_init_schema.sql` (`:1647` `audit_logs`, `:1669` `audit_trail`,
`:2232-2234` indexes) · `20260805000000_rc2_triggers.sql` · `20260806000000_rc2_verification.sql` ·
`20260807070000_add_new_table_rls.sql` · `20260810040000_v3m5_issues.sql` ·
`20260821020000_d22_processing_work_assignment.sql` ·
`20260824030000_d37_master_commercial_billing.sql` ·
**`20260831020000_audit_activity_immutability.sql`** ·
**`20260912000000_p7_audit_immutability_and_indexes.sql`** ·
`20260913000000_p8_report_lifecycle_status.sql` · `20260925000000_p8_rls_4b_group1_enablement.sql` ·
`20260927000000_p8_fin06_manual_processing_governance.sql` ·
`20261003000000_p8_i4_insight_interactions.sql` ·
`20261008000000_p16r5_result_reportability_lifecycle.sql` ·
**`20261010000000_p17a_accounting_dimensions_and_factor_governance.sql`** ·
`20261013000000_p17h_estimation_and_assumption_records.sql`.

### 21.5 Documentation artefacts

`docs/audit/cline/CARBONTALLY_V3_ARCHITECTURE_CONFORMITY_GATE.md:174,257,649` ·
`docs/architecture/CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md:65,161` ·
`docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:3-15,27,46-60` ·
`docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md:290` (ADR-V3-013 row; dormant history tables) ·
`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:611` (FTR-207) ·
`docs/cline/CarbonTally_Backend_Module_Inventory_V3.md:94,3756-3775` ·
`API_ENDPOINTS.md:9-10,78-105` · `docs/architecture/API_DOCUMENTATION.md:55-62,99` ·
`docs/architecture/filestructure.md:6` · `docs/architecture/changelog.md:12,111,550` ·
`docs/architecture/CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md` ·
`docs/architecture/CT-PO-P17-IMPLEMENT-02-API-ACTING-FOR-WRITE-PATHS-20250925.md` ·
`docs/architecture/CT-PO-CARBONTALLY-CT-SCHEMA-03-REPORT-20260927.md:306-326`.

### 21.6 Databases probed (read-only)

`ct_schema01_pg` (db `postgres`) · `ct_schema02_pg` (db `postgres`) ·
`supabase_db_carbon_ledger` (dbs `postgres` and `carbontally_demo_local`, the latter being the
target named by `carbontally_demo_lab_postgrest`'s `PGRST_DB_URI`). 15 containers were running
(`ct_schema0{1,2}_{pg,storage}`, `carbontally_demo_lab_{gateway,storage,postgrest}`,
`supabase_*_carbon_ledger`, plus unrelated `hindsight-*` and `n8n-n8n-1`).

### 21.7 Scratch evidence (outside the repository; not part of the deliverable)

Probe scripts `/tmp/aud1_probe.sh`, `/tmp/aud1_probe2.sh`, `/tmp/aud1_probe3.sh`; raw probe
output `/tmp/aud1_dbprobe.txt`, `/tmp/aud1_dbprobe2.txt`, `/tmp/aud1_dbprobe3.txt`; and 74
`/tmp/aud1_*.txt` captures covering the copy census (`aud1_variants.txt`, `aud1_crlf.txt`,
`aud1_vdiff_sum.txt`), Git archaeology (`aud1_ghist.txt`, `aud1_git2.txt`, `aud1_git3.txt`,
`aud1_gitblob.txt`, `aud1_perfile.txt`), migrations (`aud1_ddl.txt`, `aud1_ddl2.txt`,
`aud1_mig_audit.txt`, `aud1_trail_ddl.txt`, `aud1_p7.txt`, `aud1_p17a.txt`), writers/readers
(`aud1_writers*.txt`, `aud1_usage.txt`, `aud1_readers.txt`, `aud1_importers.txt`,
`aud1_sites.txt`, `aud1_lowcounts.txt`), registration (`aud1_reg.txt`, `aud1_reg2.txt`,
`aud1_regmatrix.txt`, `aud1_apiinit*.txt`, `aud1_mainimports.txt`, `aud1_mainhead.txt`,
`aud1_unreg.txt`), UI (`aud1_ui.txt`, `aud1_ui_ep.txt`, `aud1_uiusage.txt`), docs
(`aud1_docs.txt`, `aud1_docsauditlogspy.txt`, `aud1_adr.txt`, `aud1_gate.txt`,
`aud1_legacyinv.txt`), tests (`aud1_tests.txt`), actor context (`aud1_domain_audit.txt`,
`aud1_helpers.txt`, `aud1_actingfor.txt`, `aud1_data_audit.txt`) and environment
(`aud1_env.txt`, `aud1_find.txt`, `aud1_containers.txt`).

---

## 22. Explicit limitations

1. **Read-only scope.** No code was executed, no endpoint called, no E2E workflow run and no
   write performed. *"Route wired"* therefore means *statically registered*, and *"writer
   exists"* means *code path present* — neither implies a successful runtime write (U-1…U-3).
2. **Production was not inspected.** Database evidence comes from local containers; the
   production schema is inferred only from migrations plus canonical-rebuild results.
3. **Row-count evidence is environment-specific.** `audit_trail` = 563/242 and `audit_logs` = 0
   describe the probed local databases, not production.
4. **"0 code references"** for dormant tables means no reference in `backend/**/*.py`; SQL,
   seed, script and external-tooling references were not exhaustively searched per table.
5. **Copy-census completeness.** The machine-wide `find -xdev` covers the root filesystem
   (excluding other mounts) and skipped `node_modules`, `site-packages`, `.venv`; archives
   (`*.zip`) were enumerated but **not opened**, so a copy inside an unopened archive cannot be
   excluded.
6. **Documentation counts are as of this HEAD**, and several documents are themselves stale
   (which is a finding, F-1).
7. **No business-acceptance verdict.** This report identifies architecture and defects; it does
   not accept, certify or declare anything production-ready, and deliberately avoids the
   "PRODUCTION READY" formulation.

---

## Verification counts (task-required)

| Metric | Count | Basis |
|---|---|---|
| `audit_logs.py` variants found | **10 copies on disk / 1 semantic version** (6 CRLF + 4 LF; 3 Git commits all identical) | §2 |
| Repositories / checkouts searched | **9** (working repo + 8 sibling HEADs) + machine-wide filesystem sweep + 1 scratch directory | §2, §21.1 |
| Git refs / history searched | **all refs** of the working repository (`git log --all`, `-S`, `--diff-filter=A/D/R`, per-blob hashing); siblings compared by HEAD identity | §3, §21 |
| Audit tables found (canonical chain) | **32** tables matched the audit/activity/event/history/log/evidence/notification/access family, out of 147 `CREATE TABLE` statements (canonical schema documented as 145 tables) | §4.1 |
| Audit writers found | **2 canonical entry points** (`AuditRepository.record`, `AuditLogger`) invoked from **35 shipping call sites**; **1 legacy writer helper** + **12 direct legacy insert sites** (43 `audit_logs` call sites across 8 modules in total) | §6 |
| Audit readers found | **6 registered surfaces** (4 `/api/v2/admin/audit` + 5 V3 audit reads, `/audit-package.json`, legacy `/api/admin/audit` 4, `review_history` 2, `logs`), **2 wired UIs**, **4 unregistered legacy reader modules**, **12 orphan endpoints** | §7 |
| Canonical audit objects found | table `audit_trail` (17 columns, 1 trigger, 1 function, 5 indexes, 0 policies), `domain/audit.py`, `data/audit.py`, `infra/audit_logger.py`, `api/admin_audit.py`, `api/audit_helpers.py`, `api/v3_reporting.py` audit routes, `api/v3_exports.py` audit package, 12 audit-touching migrations, 8 dedicated audit test modules | §4, §6, §7, §10 |
| Orphan audit objects found | **1 audit module** (`routes/admin/audit_logs.py` — 12 endpoints, 10 on-disk copies) + **3 further unregistered modules containing audit code** + **7 dormant audit/history tables** | §15 |
| Unresolved audit questions | **8** (U-1…U-8) | §17 |
| PO decisions required | **PD-7** (8 scopes A–H) + **PD-7.1 … PD-7.6** = **13 decision items covering 14 scopes** | §18 |
| Defects classified | **8** (F-1…F-8) | §14 |
| Engineering-only candidates | **6** (E-1…E-6, two of which are explicit non-actions) | §19 |

---

## FINAL VERDICT

# `CT_AUDIT_01_CANONICAL_AUDIT_IDENTIFIED`

**Rationale.** The canonical CarbonTally audit architecture was identified by convergent current
evidence and is neither lost nor dormant: `public.audit_trail` is created by the canonical
migration chain, protected by a database-level append-only trigger and deny-by-default RLS,
written by `AuditRepository` through `AuditLogger` from ~35 shipping modules, populated with real
rows (563 dev / 242 demo), read by registered admin and V3 APIs, surfaced in two wired UI tabs,
covered by 8 dedicated test modules, and governed by ADR-V3-013 and PO decision D-P2-02. The
orphaned `backend/routes/admin/audit_logs.py` (ten byte-equivalent copies, one semantic version,
never registered in any commit and never consumed by any UI) is confirmed exactly as CT-SCHEMA-03
classified it, and is documented in-repo as superseded by `api/admin_audit.py` + `data/audit.py`.
Remaining gaps (authentication-event auditing, data-access logging, per-path acting-for coverage,
dormant-table consolidation) are **open PO questions**, not unidentified architecture, and are
enumerated in §17–§20.

`CT_AUDIT_01_AUDIT_SYSTEM_PARTIALLY_RECONCILED` and `CT_AUDIT_01_AUDIT_SYSTEM_UNRESOLVED` are
**not** used: the tier structure, canonical carrier, writers, readers, persistence evidence and
supersession record are all established with current evidence.

**No implementation was performed. No "PRODUCTION READY" claim is made.**

<!--CTEOF-->
