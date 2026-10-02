# FINAL-03 — Data Preservation Assessment and Decision Record

**Date:** 2026-10-02 · **Prepared by:** Cline (implementation / rehearsal operator)
**Status:** ASSESSMENT COMPLETE — READ-ONLY. **No production record was created, modified or deleted.**
No deploy (Render/Vercel). No migration applied. No commit created.
Report line: `FINAL-03 DATA PRESERVATION PLAN READY — AWAITING P2/P5/P6`

---

## 1. Owner decision (recorded 2026-10-02) — supersedes the "clean initialization" assumption

The two organisations and two accounts **already in the production project are owner-created test
identities, not external customer data**, and **must be preserved**. The FINAL-03 §0 premise
("clean initialization = no organisations/users in production") is **superseded**.

Resulting production initialization strategy:

> **PRESERVE the existing owner-created test organisations/accounts**
> **+ APPLY the production schema/migrations/configuration**
> **+ PRESERVE the 7,049 emission factors**
> **+ DO NOT import any local demo/test business data**
> **+ NEVER touch the local demo environment.**

A destructive "reset production to empty" procedure is **prohibited**. The retained identities may
remain after launch, but they must always be described as **controlled owner/test identities**, never
as real customers.

---

## 2. Production project identity (unchanged from Phase 0)

| Field | Value |
| --- | --- |
| Project ref | `pvwiojoyaqywtydzcpbg` ("CarbonTally") |
| Organisation ref | `pfurlzwxdtvyljnahlnx` |
| Region / engine | eu-west-2 · PostgreSQL 17.6 · pooler `aws-1-eu-west-2.pooler.supabase.com` |
| Credential used | `SUPABASE_LIVE_POSTGRES_DATABASE_URL` from `backend/.env` (**session forced read-only**) |
| Owner confirmation (gate P6) | **still required** — recorded here as documentary evidence, not owner sign-off |

⚠️ `DATABASE_URL` and `SUPABASE_URL` in `backend/.env` are **LOCAL** values (`127.0.0.1`). Only
`SUPABASE_LIVE_*` addresses production. Never pass `DATABASE_URL` as `$DB` in a production step.

---

## 3. The four retained entities (all confirmed present, all active)

| # | Kind | Identifier | Detail |
| --- | --- | --- | --- |
| 1 | Organisation | `0c0aa358-eaed-492c-9a8b-f7fabe6531ac` | **Babui Technologies UK Limited** — active=true, created 2026-09-17 07:24:56Z |
| 2 | Organisation | `8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` | **Faria Green Company UK LTD** — active=true, created 2026-09-17 15:24:27Z |
| 3 | Auth account | `40b9f3f6-040d-4cc5-9bb1-82ae10115421` | `sho***@gmail.com` — e-mail confirmed 2026-08-18, last sign-in **2026-09-26 13:45Z**, not banned |
| 4 | Auth account | `ab7a9f50-8f16-4eb4-a229-40fa3a87c3e4` | `far***@gmail.com` — e-mail confirmed 2026-09-17, last sign-in **2026-09-24 05:15Z**, not banned |

**Relationship that must survive** — `public.organization_members` (columns: `id, organization_id,
user_id, role, created_at, is_active, updated_at`), exactly 2 rows:

| user | organisation |
| --- | --- |
| `40b9f3f6-…5421` | `0c0aa358-…31ac` (Babui Technologies UK Limited) |
| `ab7a9f50-…c3e4` | `8ae45e55-…98cd` (Faria Green Company UK LTD) |

Supporting auth state observed: `auth.sessions` = 26, `auth.refresh_tokens` = 48 (sessions that a
migration must not disturb; no `auth.*` object is touched by the unapplied migration set).

---

## 4. Associated records belonging to the retained organisations

Only **seven** public tables hold rows linked to the two retained orgs — a very light footprint,
consistent with "created to test signup / login / organisation behaviour":

| Table | Rows | Note |
| --- | --- | --- |
| `evidence_line_items` | 74 | largest association |
| `document_processing_queue` | 11 | |
| `organization_files` | 11 | |
| `organization_members` | 2 | **the membership relationship (§3)** |
| `manual_extraction_batches` | 2 | |
| `conversations` | 1 | |
| `messages` | 1 | |

Storage: the private `documents` bucket holds **58 objects**; bucket is `public=false` with a
**2,097,152-byte (2 MiB)** ceiling (canonical is 10,485,760 B — see §6.3).

All other public tables hold **zero** rows for these orgs. Business tables named in the runbook
(`reports`, `documents`, `calculations`, `evidence`, `consultants`, `clients`) **do not exist** in
production under those names, so no such rows can be lost.

---

## 5. Authoritative dataset — the 7,049 emission factors survive

| Check | Value |
| --- | --- |
| `public.emission_factors` rows (production) | **7,049** — matches the authoritative count exactly |
| Row-level fingerprint | `md5(string_agg(md5(row::text), '' order by md5(row::text)))` recorded in the evidence |
| Migration impact on factor **rows** | **none** — no `DELETE`/`TRUNCATE`/`UPDATE` against `emission_factors` in the 25 unapplied migrations |
| Migration impact on factor **structure** | additive only — `ALTER TABLE public.emission_factors ADD COLUMN IF NOT EXISTS …` (factor-governance columns) + comments; two new FKs *reference* the table (`ON DELETE SET NULL` / `ON DELETE RESTRICT`) and neither writes to it |

**Conclusion:** step 5 preserves all 7,049 factor rows; the count **and** the fingerprint must be
re-measured and compared afterwards (package step 8).

---

## 6. Migration and schema conflict analysis (25 unapplied files, `version > 20260927000000`)

Production's applied maximum is **`20260927000000`**; **25 of 96** migration files are unapplied,
including both BACKUP migrations.

### 6.1 Preservation safety of the unapplied set — PASS, no data-destroying statement found
* **No** `DELETE FROM public.*` and **no** `TRUNCATE public.*` anywhere in the set.
* **No** unconditional `DROP TABLE` / `DROP COLUMN`; drops are `IF EXISTS` and target policies,
  triggers or constraints being replaced.
* **No** `ADD COLUMN` or `CREATE TABLE` without `IF NOT EXISTS`.
* The 16 tables the set creates (`activity_clarifications`, `backup_jobs`,
  `carbontally_insight_conversations|interactions|messages|tool_calls`, `contractual_instruments`,
  `estimation_records`, `insight_concurrency_leases`, `insight_rate_limit_buckets`,
  `instrument_allocations`, `report_schedule_definitions`, `report_schedule_runs`,
  `report_share_access_events`, `report_shares`, `scope3_categories`) are **all absent from
  production today** → purely additive.
* Only **two DML statements**, both benign:
  1. `20260930000000_p8_fs_adjudication_lifecycle.sql` — backfills `adjudication_id` /
     `effective_context_key` on `activity_clarifications`, **created earlier in the same batch**
     (no pre-existing rows at risk).
  2. `20261026000000_ct_backup_01_backup_jobs.sql` — merges `{"can_manage_backups": true}` into
     `staff_roles.permissions` for the **`admin` / `system_admin` names only**; documented as a
     capability grant that widens no RLS policy and touches no other permission.

### 6.2 Idempotency risk to watch at step 5 (not a preservation threat)
Three files create policies with no preceding `DROP POLICY IF EXISTS` (`20261001000000` 4/0,
`20261002000000` 1/0, `20261003000000` 4/0). Their target tables do not exist in production, so no
collision is expected; if one fails, the package's rule applies — **abort and investigate, never skip**.

> **Re-measured in the FINAL-03 decision pass:** the unguarded files are **two** —
> `20261001000000` (4 creates / 0 drops) and `20261003000000` (4 creates / 0 drops);
> `20261002000000` is guarded (1 create / 1 drop). See
> `08-final-03-p2-p5-p6-rls-decision-package-20261002.md` §F.4.

### 6.3 ⚠️ DECISION REQUIRED — the step-7 gate (149 / 149 / 271) cannot be satisfied, and part of it is *prohibited* in production by an existing PO decision
* Production today: **134 tables · 87 RLS-enabled · 47 RLS-DISABLED · 198 policies**.
* The 47 RLS-disabled tables include `staff_roles`, `system_settings`, `notifications`, `email_logs`,
  `login_history`, `password_reset_tokens`, `audit_trail`, `emission_factors`, `user_activity_log`, …
* **The repository's migration set contains no `ALTER TABLE … ENABLE ROW LEVEL SECURITY` for any of
  those 47 tables** (verified individually) → applying the canonical set can **never** raise
  production to 149/149.
* The reason is a **ratified PO decision**: `20260920000000_p8_rls_anon_grant_containment.sql` states
  *"Production is prohibited (G0-D): QA / non-production application only"*, and the P8 RLS group
  (`20260920000000`, `20260922000000`, `20260923000000`, `20260925000000`) is that QA-only hardening
  lineage. The local QA database (`ct_local_93d5cdd`) shows 135/135 RLS-enabled precisely because
  those migrations ran there.
* **Therefore step 7's expected `149 tables · 149 RLS-enabled · 271 policies` must be replaced by a
  production-specific expected state** computed as *current production objects + additive objects
  from the 25 unapplied migrations* — arithmetic today: 134 + 16 = **150** tables, 87 + 11 = **98**
  RLS-enabled, 198 + 25 = **223** policies. The 47-table RLS gap must become an **explicit, recorded
  owner risk decision**; it must not be silently "fixed" by applying a production-prohibited
  migration, and I will not improvise it.

> **Corrected in the FINAL-03 decision pass** (see
> `08-final-03-p2-p5-p6-rls-decision-package-20261002.md` §F.3): table count **134 + 16 = 150** ✓;
> RLS-enabled is **87 + 16 = 103**, not 98 — the 25 files contain **16**
> `ALTER TABLE … ENABLE ROW LEVEL SECURITY` statements, one for each new table they create, spread
> over 10 files; the policy count is **not** derivable from file contents (35 `CREATE POLICY` /
> 27 guarded `DROP POLICY` statements appear, so the naive figures are 206–233) and must be
> re-measured from `pg_policies` at step 7. **RLS-disabled stays at 47 after the batch** — the
> canonical set does not close the gap by a single table.
* Related open items already on record: RLS hold register D-4 (`emission_factors` anonymous access
  unratified) and D-11 (`FORCE ROW LEVEL SECURITY` deferred).

### 6.4 Other pre-cutover deltas to close at steps 5/11 (not preservation threats)
`documents` bucket ceiling **2,097,152 B** vs canonical **10,485,760 B** — corrected by the unapplied
`20261024000000_ct_final_01_documents_bucket_size_limit.sql` /
`20261025000000_ct_step2_documents_bucket_size_alignment.sql`. `backup*` tables **absent** → BACKUP-01/02
land in this same batch and must be applied **before** any backend/worker start (P3 / step 6).

---

## 7. Preservation plan — what must survive, and how it is verified

| # | Must survive | Verification (evidence captured at the step) |
| --- | --- | --- |
| 1 | Org `0c0aa358-…31ac` (Babui Technologies UK Limited), `is_active=true` | row re-read after step 5, field by field |
| 2 | Org `8ae45e55-…98cd` (Faria Green Company UK LTD), `is_active=true` | row re-read after step 5, field by field |
| 3 | User `40b9f3f6-…5421` (`sho***@gmail.com`), confirmed, not banned | `auth.users` re-read + **live sign-in** |
| 4 | User `ab7a9f50-…c3e4` (`far***@gmail.com`), confirmed, not banned | `auth.users` re-read + **live sign-in** |
| 5 | Both `organization_members` rows (user↔org, `role`, `is_active`) | re-read; each account must load **its own** organisation in the UI |
| 6 | The 101 org-linked rows (§4: 74+11+11+2+2+1+1) | per-table counts re-measured against §4 |
| 7 | 58 objects in the private `documents` bucket | count re-measured; one download/sign test per retained org |
| 8 | 7,049 emission factors, rows unchanged | count **and** fingerprint compared to §5 |
| 9 | Sessions / refresh tokens (26 / 48) as far as practical | no `auth.*` object is modified by the batch; sign-in re-tested |
| 10 | No local demo data imported | `organizations` / `auth.users` must remain **2 / 2** (a local import would show 975 organisations or `@demo.carbontally.local`); local stacks untouched |

**Mandatory order:** managed backup of the current production state (step 4) → apply the 25 migrations
**including BACKUP-01/02** (step 5) → pre-start schema gate (step 6) → **only then** start the
backend/worker (step 14) → re-verify 1–10 immediately after step 5 and again at step 11.

**Prohibited by this decision:** re-initializing to an empty database; cleaning the retained rows
"in place"; editing immutable historical migrations to make replay convenient; any export/restore that
overwrites the two organisations or the two accounts.

---

## 8. Remaining owner inputs — P2 / P5 / P6

| Gate | Status | Exact input required |
| --- | --- | --- |
| **P2** | OPEN | **Ratify the freeze manifest** (§8.1). No release commit will be created until then. |
| **P5** | OPEN — **blocking** | Production backup secret material: `CT_BACKUP_OBJECT_STORE=s3`, `CT_BACKUP_S3_ENDPOINT`, `CT_BACKUP_S3_REGION`, `CT_BACKUP_S3_BUCKET`, `CT_BACKUP_S3_ACCESS_KEY`, `CT_BACKUP_S3_SECRET_KEY`, `CT_BACKUP_S3_PREFIX` (if used), `CT_BACKUP_ENCRYPTION_KEY` (base64, 32 bytes), `CT_BACKUP_KEY_ID`, `CT_BACKUP_RETENTION_DAYS` (+`CT_BACKUP_PRUNE_ARTIFACTS` if wanted). **Zero `CT_BACKUP_*` variables exist in this environment** and the code fails closed. |
| **P6** | OPEN — **blocking** | Recorded **Render** service identity (docs name `carbontally-api.onrender.com`, but `/health` is unreachable from here and there is no `render.yaml`) and the **Vercel** project identity (no project name/ID recorded; `vercel` CLI absent; no token). Plus a production **SMTP** identity — only local dev SMTP/Resend values exist. |
| P4 | Satisfied on commitment only | Owner's recorded B2′ posture (managed PITR unavailable on the current plan), as stated in the owner brief. |
| — | NEW decision item | §6.3 — the step-7 schema/RLS expectation must be replaced, and the 47-table RLS gap recorded as an explicit owner risk decision. Full detail, the 47-table classification and the recommended remediation sequence: `08-final-03-p2-p5-p6-rls-decision-package-20261002.md` §C (classification), §F.3 (measured deltas: +16 tables, +16 RLS-enabled, RLS-disabled stays 47), §H (decision register). |
| — | NEW decision item (2026-10-02, second pass) | **Authorise the R-1/R-2/R-3 remediation change-set**: RLS enablement on the 15 hard-blocking C tables (system_settings, staff_roles, password_reset_tokens, beta_access_codes, beta_users, conversation_participants, email_logs, notifications, review_audit_trail, waitlist, audit_trail, manual_extraction_items, consultant_billing, consultant_tasks, login_history) + keeping the existing `manual_extraction_items` policy + moving/deleting the affected browser call sites — **plus two rulings**: (a) `staff_workload` downgraded from blocking to owner-decision (its only code paths reference non-existent columns), (b) the 9 class-D tables (**D-6**) accepted-as-inert *or* enabled in the same migration (recommended: enable now — free). Exact paths, the 10-field assessment of the nine tables and the full decision table: `09-final-03-r1-r2-r3-remediation-decision-20261002.md` (§1 R-1, §2 R-2, §3 R-3, §4 nine tables, §5 A/B/C/D, §6 gate table, §7 P2/P5/P6, §8 evidence index). |

### 8.1 Freeze manifest (P2) — reconciled, awaiting ratification
165 dirty entries (115 `??` / 50 ` M`): **83** runtime-code, **14** tests, **61** CT evidence/audit
docs, **75** other docs (14 of them non-CT: unrelated PO/insight/ChatGPT/deepseek/business material),
**6** scratch/junk, **2** repo config (`backend/requirements.txt`, `.gitignore`).

**Proposed:** freeze runtime code **+** tests **+** CT evidence docs **+** `backend/requirements.txt`
**+** `.gitignore`, on a **new branch** (leaving `p8-release-reconciled` untouched); exclude the 75
other docs and preserve the 6 scratch paths untracked (`.costrict/`, `.p18_audit_tmp/`, `8`, `=`,
`backend/nohup.out`, `costrict-p3-ov-01-independent-re-verification.txt`).

The release **depends on 23 currently-untracked paths** — every new `backend/backup/*` module
(`jobs`, `worker`, `objects`, `policy`, `restore`, `retention`, `s3store`, `sigv4`, `verification`),
`backend/api/v3_backups.py`, `backend/api/upload_gate.py`, `backend/api/v3_document_uploads.py`,
`backend/services/{document_cleanup,document_security,email_provider,storage_keys,storage_metering}.py`,
`frontend/src/v3/ops/BackupsTab.jsx`, `admin/src/services/factorAdminService.js`, both BACKUP
migrations and `tools/b7_pool_soak.py` — so HEAD
`cabdca8380415e73a25cf23eb393d0b15c0af391` (2026-09-29) is **not deployable as-is**.

---

## 9. Evidence index (this folder)

| File | Contents |
| --- | --- |
| `00-freeze-branch-head.txt` | branch, HEAD SHA, remotes, dirty-entry counts |
| `00-freeze-git-status-porcelain.txt` | the full 165-entry `git status --porcelain` |
| `00-freeze-workspace-reconciliation.txt` | bucket classification + untracked-but-required paths |
| `01-production-pre-cutover-state.txt` | production identity, counts, migration state, buckets, extensions |
| `02-preservation-assessment-entities.txt` | retained entities and the membership relationship |
| `02-preservation-org-linked-counts.txt` | single-round-trip non-zero linkage scan |
| `02-local-environment-inventory.txt` | local containers — all local demo/rehearsal stacks, untouched |
| `03-schema-drift-and-rls.txt` | the 47 RLS-disabled tables, existence check for created tables, the 2 DML statements |
| `04-migration-conflict-analysis.txt` | destructive-statement scan, policy idempotency, RLS enablement list |
| `05-rls-prohibition-and-storage.txt` | storage inventory + migration-set RLS absence evidence |
| `06-environment-identity-redacted.txt` | local vs live credential identity (hosts only; values redacted) |
| `07-production-public-tables.txt` | the 134 production table names |
| `08-final-03-p2-p5-p6-rls-decision-package-20261002.md` | **the decision companion**: P2 freeze manifest detail (A), data-preservation proof + verdict (B), **classification of all 47 RLS-disabled tables** with the 12-field evidence and the recommended remediation sequence (C), P5 backup inputs (D), P6 Render/Vercel/email inputs (E), migration/schema conflict + measured state delta (F), residual risks (G), decision register and status (H) |
| `09-final-03-r1-r2-r3-remediation-decision-20261002.md` | **the R-1/R-2/R-3 remediation decision (assessment only)**: full path traces for `system_settings` (R-1), `staff_roles.permissions` (R-2) and token material (R-3) with the five R-1 determinations; the **10-field assessment of each of the nine browser-accessed tables**; the remaining **38 tables classified A/B/C/D exactly once** (mapped 1:1 to package `08` C1/C2/C3/C4 — no numbers bent to the old 149/149/271 baseline); the **production-gate decision table** (R-1…R-6 + every C and D table) with the four categories separated; P2/P5/P6 readiness restated; and the exact file/line evidence for every production-impacting conclusion. **No SQL, no migration, no RLS change, no deploy.** |
| `10-final-03-rls-remediation-implementation-and-verification-20261002.md` | **the RLS remediation IMPLEMENTATION record** (owner-authorised 2026-10-02, **two additive migrations**): `20261028000000_ct_final_03_rls_security_remediation.sql` (43 tables enabled — 41 fail-closed with zero policies, 2 enable-only with their 4 policies kept; no policy, grant, FORCE RLS, schema or data change) **plus the residual-closure follow-up `20261029000000_ct_final_03_staff_workload_rls.sql`** (`staff_workload` RLS-enabled, zero policies, §1.5/§2.5/§2.6); the database-level **before/after enforcement evidence** (pre-state exposure of `system_settings`/`staff_roles` and of `staff_workload` confirmed by real row counts — the residual proven against a *seeded row*, so "0 rows" cannot be confused with an empty table; post-state deny-all; `service_role` backend intact; idempotent re-runs; policy count `218 → 218`), **all 23 browser call-site resolutions** (8 removed, 12 re-pointed, 3 unchanged) and the 4 backend endpoints they moved to, the focused static+live suite result (**30 passed / 1 skipped**; 21/1 before the residual closure), the §10 security-invariant and §12 production-data-preservation statuses, the now-**closed** `staff_workload` residual, and the exact file manifest. **No production contact; nothing deployed; nothing committed; the accepted 43-table artefact is byte-for-byte unchanged.** |


---

## 10. Compliance statement for this pass

**Performed:** read-only assessment, repo-only migration analysis, evidence capture, documentation update.
**Not performed (deliberately):** any production mutation, Render deploy, Vercel deploy, destructive
production operation, deletion of any production record, any change to the local demo environment, and
any Git commit. Every production psql session ran with `default_transaction_read_only = on`.

**Report line:** `FINAL-03 DATA PRESERVATION PLAN READY — AWAITING P2/P5/P6`

### 10.1 Implementation pass — 2026-10-02 (RLS security remediation)

**Performed (owner-authorised implementation):** one new, additive, security-only migration
(`20261028000000_ct_final_03_rls_security_remediation.sql`) enabling RLS on 43 tables with **zero new
policies**; the 23 browser/PostgREST call sites resolved (8 removed, 12 re-pointed, 3 unchanged);
four backend endpoints completed/added to receive the moved calls; a focused static + live RLS test
suite added and passing (21 passed / 1 skipped). Full detail, evidence and the exact file manifest:
`10-final-03-rls-remediation-implementation-and-verification-20261002.md`.

**Not performed (hard stop respected):** no production mutation of any kind (the migration was applied
only to a disposable local `TEMPLATE` clone), no production Supabase change, no Render deploy, no Vercel
deploy, no production secret configured, no P5/P6 execution, no Git commit or push, no historical
migration modified, and no other FINAL-03 phase started. No existing table, policy, grant or row was
changed: the migration's own post-conditions prove the `public` policy count is unchanged (delta 0).

**Report line:** `FINAL-03 RLS SECURITY REMEDIATION IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

**Standing owner decisions untouched:** D-1 (P2 freeze ratification), D-3 (step-7 gate), D-4/P5 (backup
credentials + encryption-key escrow), D-5/P6 (Render/Vercel/email identities).

### 10.2 Residual-closure pass — 2026-10-02 (`staff_workload`)

**Performed (owner-authorised, security-first objective):** the single recorded residual was closed by
**adding** one more additive, security-only migration —
`20261029000000_ct_final_03_staff_workload_rls.sql` — which enables RLS on `public.staff_workload` with
**ZERO policies**, no grant, no FORCE RLS, no schema/function/storage change and no data change. The
already-accepted 43-table artefact `20261028000000_…` was **not** modified (byte-for-byte unchanged):
`AGENTS.md` §66 states no rule permitting an already-created migration to be edited, and editing an
artefact already accepted "in principle" would invalidate that acceptance. The two files are disjoint and
neither creates, drops or alters a policy. The phase-1 deletion of the dead `staff_workload` browser read
is preserved (only its comment was corrected); the inert realtime registration was left untouched rather
than given a policy, as the authorisation required. Verified on a **fresh disposable clone**
(`ct_f03_sw_verify`, production pre-state reproduced by disabling RLS on the 44 tables): `authenticated`
went from reading **1 row** (and `UPDATE 1` / `DELETE 1` / `INSERT` accepted) to **0 rows**
(`UPDATE 0` / `DELETE 0` / RLS-violation on INSERT) against a seeded row; `anon` denied throughout;
`service_role` preserved; policy count `218 → 218` (delta 0); 44/44 target tables RLS-enabled; idempotent
re-run exit 0; focus suite **30 passed / 1 skipped**; route suite **25 passed**. Full detail: `10-…`
§1.5, §2.5, §2.6. There is **no remaining RLS residual** in this change-set's scope.

**Not performed (hard stop respected):** no production contact of any kind (local cluster only), no
production Supabase change, no Render deploy, no Vercel deploy, no production secret configured, no P5/P6
execution, no commit or push, no historical migration modified, no policy created to preserve legacy
behaviour, and no scope beyond `staff_workload`.

**Full unit suite — reported honestly.** `pytest tests/unit` was run twice with a 25-minute cap; run 1
executed every test and printed the complete short summary with **9 failures**, then was stopped by the cap
before the totals line (no pass count is claimed). All 9 were triaged and **none is caused by this pass**:
five are "the newest migration in the chain" guard snapshots from earlier phases (STEP2 / BACKUP-01/02 /
phase-1 FINAL-03), which were **already failing** — proven by recomputing each assertion with this pass's
file excluded (`names[-1]` was already `20261028000000_…`; `len(names)` was already 97 ≠ 71; the later-set
and post-P16 allow-lists already contained non-family migrations) — and four are unrelated pre-existing
engine/route behaviours (`test_extraction_suggestions` ×3, `test_v3_discovery::test_create_request_as_admin`).
They are flagged for the owner (`10-…` §7.1) and deliberately not touched. Claimed for this pass instead:
the focused static+live RLS suite (**30 passed / 1 skipped**), `tests/unit/routes` (**25 passed**), the Babel
parse of the one changed front-end file, and the live before/after database evidence.

**Report line:** `FINAL-03 RLS SECURITY REMEDIATION — SINGLE RESIDUAL CLOSED — READY FOR INDEPENDENT VERIFICATION`
