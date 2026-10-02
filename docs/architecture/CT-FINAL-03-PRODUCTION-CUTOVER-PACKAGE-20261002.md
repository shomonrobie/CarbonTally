# CT-FINAL-03 — Clean Production Cutover Package (22-step gated sequence)

**Date prepared:** 2026-10-02 · **Prepared by:** Cline (implementation / rehearsal operator)
**Acceptance authority:** CoStrict / OHD — **this package decides and executes nothing.**
**STATUS: PREPARED — NOT EXECUTED. No step below has been run.** Nothing here has touched production.

**Related documents**

| Document | Role |
| --- | --- |
| `CT-FINAL-02-CLOSURE-AND-LIVE-READINESS-20261001.md` | FINAL-02 evidence, §15 current status matrix, §16 2026-10-02 re-run, §17 verdict, §16.9 local artefacts/cleanup |
| `CT-FINAL-02-B2-READONLY-VERIFICATION-20261001.md` | the read-only managed-backup/PITR verifier and its result |
| `CARBONTALLY_PRODUCTION_BACKUP_RESTORE_COMPLETE_IMPLEMENTATION_20261002.md` | BACKUP-01/02 implementation, artifact/restore/DR-20 evidence |
| `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md` | **owner data-preservation decision (2026-10-02)** — retained-entity baseline, per-table counts, factor fingerprint, migration-conflict analysis, preservation plan, P2/P5/P6 inputs |
| `CT-FINAL-02-CLOSURE-AND-LIVE-READINESS-20261001.md` §11 | the earlier 17-step intent checklist — superseded in operational detail by this package |

---

## 0. Scope, and what this package is NOT

**FINAL-03 is a DATA-PRESERVING PRODUCTION MIGRATION, not a customer-data migration and no longer a
"clean initialization".** (Owner decision, 2026-10-02 — see the amendment immediately below, which
**supersedes** this paragraph's original clean-initialization wording.) CarbonTally holds **no external
customer data**. The **7,049 emission factors** are the authoritative non-demo dataset and are
preserved row-for-row.

> ### AMENDMENT — owner data decision, 2026-10-02 (authoritative; supersedes "clean initialization")
>
> The production project `pvwiojoyaqywtydzcpbg` already contains **two owner-created TEST organisations
> and two owner-created TEST accounts**, which are **not external customer data** and **must be
> preserved**:
>
> | Retained entity | Identifier | Name / account |
> | --- | --- | --- |
> | Organisation 1 | `0c0aa358-eaed-492c-9a8b-f7fabe6531ac` | Babui Technologies UK Limited |
> | Organisation 2 | `8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` | Faria Green Company UK LTD |
> | Account 1 | `40b9f3f6-040d-4cc5-9bb1-82ae10115421` | `sho***@gmail.com` |
> | Account 2 | `ab7a9f50-8f16-4eb4-a229-40fa3a87c3e4` | `far***@gmail.com` |
>
> **Production initialization is therefore:** PRESERVE the retained organisations/accounts and their
> `organization_members` relationships **+** APPLY the canonical migrations (including BACKUP-01/02)
> **+** PRESERVE the 7,049 emission factors **+** DO NOT import any local demo/test business data
> **+** NEVER touch the local demo environment.
>
> **Prohibited:** re-initializing to an empty database; deleting/truncating/resetting/exporting-over
> the retained rows; importing local demo organisations, users, consultants, clients, reports,
> calculations, documents or evidence; editing immutable historical migrations to make replay
> convenient; deploying Render or Vercel; any destructive production operation.
>
> Full assessment, per-table counts, fingerprints and the preservation plan:
> `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md`

**This package is not authorization.** It is the runbook the *next* authorized pass would execute
step-by-step, each step gated by an explicit expected result and a stop condition. Issuing it grants
nothing, decides nothing and changes nothing.

**Nothing in this package may be executed while any precondition in §1 is unmet.**

---

## 1. Preconditions — every one must be TRUE before step 1

| # | Gate | How it is shown to be true | If unmet |
| --- | --- | --- | --- |
| **P1** | **B7 is fixed and verified.** The backup worker no longer leases a pooled connection without releasing it (`backend/backup/jobs.py`, and the same idiom in `backend/backup/service.py`); a missing backup table is a terminal, backed-off condition, not a per-tick error. | the fix is present in the frozen commit; the backup unit + integration suites are green; the canonical drill completes; a ≥10-minute soak against a schema-complete database shows **no** connection growth (no `/health` timeout) | **STOP — and, as of the 2026-10-02 second pass, the *only* clause not met is the frozen commit. All other clauses are locally verified (§1.1).** See FINAL-02 §15.2/§15.2.1/§17. Do not deploy: any commit that predates the fix would lose DB-backed API within minutes |
| **P2** | **The BACKUP-01/02 file set is committed** (FINAL-02 §16.7 / DR-20 handoff H6), so the deployed commit *is* the reviewed artifact. | `git status --porcelain` shows none of those paths as untracked/modified; the commit SHA is recorded | **STOP** — deploying an uncommitted tree is not a frozen artifact |
| **P3** | **Both BACKUP migrations exist in the migration set**, and are applied **before** the backend process starts anywhere the worker runs. | `supabase/migrations/20261026000000_ct_backup_01_backup_jobs.sql` and `..._ct_backup_02_backup_sets_and_verification.sql` present; after step 5, `public.backup_jobs` exists with the step-6 column/index set | **STOP** — the worker errors every tick on a database that lacks them |
| **P4** | **The B2′ recovery-posture decision is recorded** by the owner for project `pvwiojoyaqywtydzcpbg` (managed backups with non-zero retention and/or the PITR add-on), and the read-only verifier then reports the capability present. | a fresh GET-only run of the B2′ verifier (FINAL-02 §15.1) shows backups non-zero / PITR enabled as decided | **STOP for the cutover** — a production launch with no managed recovery capability is a decision, not an accident; it must be an *explicit, recorded* owner decision |
| **P5** | **The secret store is populated** for the backend and the frontend (list in step 13), including the backup key material. | the variables are present in the platform secret mechanism and absent from the repository | **STOP** |
| **P6** | **Environment ownership is confirmed**: the production Supabase project, the Render service (`carbontally-api.onrender.com`) and the Vercel project are the intended targets; `qa_harness/` is untouched by this pass. | project refs, service names and the frozen SHA are written into the evidence pack | **STOP** |

### 1.1 P1 status as of 2026-10-02 (second pass) — **clauses verified; gate still OPEN**

The implementer's post-fix pass applied the §15.2 minimal fix in the **working tree** and produced the
live evidence for P1's *verifiable* clauses. Evidence pack:
`docs/cline/evidence/FINAL-03-P1-B7-20261002/01-b7-gate/` (index and method: that folder's `README.md`;
narrative: FINAL-02 §15.2.1).

| P1 clause | Result | Artifact |
| --- | --- | --- |
| the fix is present in the **frozen commit** | **NOT MET — no frozen commit exists** (nothing was committed; that is gate **P2**) | `00-freeze/` is deliberately absent |
| backup unit + integration suites are green | **MET** — 275 tests · 0 failures · 0 errors · 0 skipped · EXIT=0 | `junit-backup-suites.xml` |
| the canonical drill completes | **MET** — completes, EXIT=0; against `ct_final02_src` it reproduces FINAL-02 §16.5 (94 applied / 1 already present / 1 failed = `20260801000000_rc2_constraints.sql`; phase 2 `secrets`-only; phase 4 the known harness truncate refusal) | `drill-post-fix-source-ct_final02_src.txt` |
| a ≥10-min soak on a schema-complete database shows no connection growth and no `/health` timeout | **MET** — 600 s, 5/5 clauses true, pool `size == idle` throughout, 2,862 `/health` probes, **0 timeouts**; the pre-fix control still fires, so the verdict is not vacuous | `soak-b7-schema-complete.json`, `soak-b7-control-prefix.json` |

**Therefore P1 is not satisfied — do not treat this as authorization.** One clause is structurally
unmeetable until P2 is done, and FINAL-02 §17's ordered action 1 also still owes a B4/D-7 re-run. What
changed is the *reason* to hold: **P1 is no longer open on evidence, it is open on commitment.**


---

## 2. Preserve / do not carry

**Preserve and initialize**

- `supabase/migrations/**` applied in order — the exact shipped set (**96 files** at 2026-10-02,
  including the two BACKUP migrations of P3);
- platform configuration: auth providers + redirect allow-list, JWT secret/keys, `storage` bucket
  definitions (private `documents`, 10,485,760-byte ceiling), PostgREST roles/grants, RLS enablement;
- the **7,049 emission factors** (authoritative reference dataset) — verified row-for-row;
- required system/bootstrap configuration (platform admin/staff rows, `system_settings`);
- production secrets delivered through the proper secret mechanism (never committed).

**Do NOT carry into production as customer data** — every demo organisation, demo user, demo
consultant, demo client, demo report, demo document, demo calculation, demo evidence and demo
activity/audit/business record, and the demo credential file. If a demo row is found in production after
step 9, **STOP and re-initialize**; do not "clean up in place".

---

## 3. The 22-step sequence

Each step states its **action**, the **command** (or console action), the **expected result**, the
**evidence to capture** and the **STOP condition**. `$RELEASE` = the frozen commit SHA from step 1;
`DB` = the production database; the drill tool is `/home/shomonrobie/ct_93d5cdd/tools/backup_recovery_drill.py`.

**1. Freeze the release and record the SHA.**
Action: confirm the tree contains the P2 file set and nothing unreviewed. Command:
`git rev-parse HEAD`, `git status --porcelain`, `git tag -a ct-final-03 -m "FINAL-03 cutover"`.
Expected: one clean commit SHA; tag created; the BACKUP set no longer untracked.
Evidence: SHA, tag, porcelain output. STOP: any untracked file that the release depends on.

**2. Verify the B7 fix (gate P1).**
Action: inspect the lease site and re-run the suites.
Command: `grep -n "release\|async with" backend/backup/jobs.py backend/backup/service.py`;
`backend/.venv/bin/python -m pytest -q tests/unit/backup tests/integration/backup`.
Expected: a release path exists at every lease; **275 tests, 0 failures** — the two-path run
(`tests/unit/backup` **253** + `tests/integration/backup` **22**); FINAL-02's *four-path* composite is
**287** post-fix, and its pre-fix value was **275** by coincidence of a different decomposition
(FINAL-02 §15.2.1); the ≥10-minute soak shows no connection growth. Evidence: grep output, JUnit XML,
soak timeline. STOP: any growth.

**3. Record the owner's B2′ decision (gate P4).**
Action: capture the decision in writing and re-run the read-only verifier.
Command: GET-only verifier of FINAL-02 §15.1 (no POST/PATCH/PUT/DELETE).
Expected: statement of posture + verifier output consistent with it. Evidence: decision note + JSON.
STOP: an unrecorded or unimplemented decision.

**4. Take the production backup of the current state and record the restore point.**
Action: create/verify the managed backup and note the restore point (this is also the B2′ evidence
capture). Command: platform backup + `GET /v1/projects/{ref}/database/backups`.
Expected: a completed backup with a restore point time. Evidence: backup list JSON.
STOP: no completed backup — do not proceed to destructive steps.

**5. Apply the frozen migration set to the production database.**
Action: apply `supabase/migrations/**` in filename order to `DB`.
Command: `supabase db push` (or the reviewed SQL application path) against the production project.
**Preservation guard (2026-10-02):** this is an **in-place, additive** application against a live
database that holds two owner TEST organisations and two owner TEST accounts. Do **not** run any
"reset / clean / truncate / drop schema" procedure, and pass the **production** DSN
(`SUPABASE_LIVE_POSTGRES_DATABASE_URL`) — never the local `DATABASE_URL`, which points at
`127.0.0.1:54426`. The unapplied set was verified to contain no `DELETE`/`TRUNCATE public.*`, no
unconditional `DROP TABLE`/`COLUMN` and no data `UPDATE` other than the two benign statements listed in
`docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md` §6.1.
Expected: every migration applied; no failure. Evidence: apply log + `python backend/tools/migration_drift.py`
report showing no drift. STOP: any failed migration — investigate; **do not** skip and continue
(the known immutable `20260801000000_rc2_constraints.sql` data-dependence must have no trigger in a
clean database).

**6. Pre-start schema gate: the backup tables exist.**
Action: confirm before any backend process starts. Command:
`psql "$DB" -tAc "select table_name from information_schema.tables where table_schema='public' and table_name like 'backup%'"`.
Expected: `backup_jobs` present (created by `20261026000000_ct_backup_01_backup_jobs.sql`) **and**
extended by `20261027000000_ct_backup_02_backup_sets_and_verification.sql` — its backup-set and
verification columns plus `backup_jobs_single_flight_idx` / `backup_jobs_backup_set_idx` /
`backup_jobs_verification_idx` all present. Evidence: table + column + index list. STOP: absent or
only half-applied — starting the backend now reproduces B7.

**7. Schema verification (production-specific expectation — AMENDED 2026-10-02).**
Action: count the objects and compare against the **production-specific expected state**, computed as
*current production objects + the additive objects created by the unapplied migration set*.
Current measured baseline (2026-10-02, read-only): **134 tables · 87 RLS-enabled · 47 RLS-disabled ·
198 policies**; the 25 unapplied migrations add **16 tables · 11 RLS-enabled tables · 25 policies**
→ expected after step 5: **150 tables · 98 RLS-enabled · 223 policies**, with `backup_jobs`,
`backup_sets`-class objects and their indexes present.
Evidence: raw output before/after + the table/index list.
STOP: any deviation from **those** counts, or any table/row lost.
> **Why the former `149 / 149 / 271` figure is withdrawn:** the repository's migration set contains **no
> `ALTER TABLE … ENABLE ROW LEVEL SECURITY` for 47 production tables** (`staff_roles`, `system_settings`,
> `notifications`, `email_logs`, `login_history`, `password_reset_tokens`, `audit_trail`,
> `emission_factors`, …), because the P8 RLS group (`20260920000000`, `20260922000000`,
> `20260923000000`, `20260925000000`) is **QA-only by ratified PO decision** — that migration states
> *"Production is prohibited (G0-D): QA / non-production application only."* Raising production to
> 149/149 is therefore neither achievable from this set nor permitted, and the 47-table RLS gap must be
> an **explicit recorded owner risk decision** (see evidence pack §6.3). Do **not** improvise it.

**8. Emission-factor verification.**
Action: verify the authoritative dataset. Command:
`psql "$DB" -tAc "select count(*) from public.emission_factors"` + checksum spot-check.
Expected: exactly **7,049** rows; checksums match the reference; no factor row altered.
Evidence: count + checksum output. STOP: any mismatch.

**9. Preservation verification of the retained production entities (REPLACES "clean initialization").**
Action: **preserve, do not initialize.** After step 5, re-read and compare against the recorded
baseline. Nothing may be deleted, truncated, reset or exported-over.
Expected (must all hold):
* `public.organizations` still contains **exactly 2 rows** — `0c0aa358-eaed-492c-9a8b-f7fabe6531ac`
  (Babui Technologies UK Limited) and `8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` (Faria Green Company UK
  LTD), both `is_active = true`;
* `auth.users` still contains **exactly 2 rows** — `40b9f3f6-040d-4cc5-9bb1-82ae10115421` and
  `ab7a9f50-8f16-4eb4-a229-40fa3a87c3e4`, both confirmed and not banned;
* `public.organization_members` still contains the **2 membership rows** linking each account to its
  own organisation (§3 of the evidence pack);
* the org-linked rows are unchanged: `evidence_line_items` **74**, `document_processing_queue` **11**,
  `organization_files` **11**, `manual_extraction_batches` **2**, `conversations` **1**, `messages` **1**;
* `storage.objects` in the private `documents` bucket = **58**;
* `public.emission_factors` = **7,049** with the recorded row fingerprint unchanged;
* **no local demo data imported** — `organizations` = 2 and `auth.users` = 2 (a local import shows 975
  organisations and/or the `@demo.carbontally.local` domain, which must be **0**).
Evidence: before/after row dumps for the four retained entities, the per-table counts, the factor
count + fingerprint, and a live sign-in + "load my organisation" transcript per retained account.
STOP: any retained row changed or missing, any count deviation, or any demo row present.
> The former instruction — *bootstrap platform-only rows; expected zero organisations/users;
> `where …demo…` → 0; re-initialize if non-zero* — is **withdrawn** as a data-destruction risk, and its
> query was also schema-wrong (it selected an `organizations.slug` column that does not exist in
> production). See `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md` §6–§7.

**10. Platform authentication configuration.**
Action: configure auth providers and the redirect allow-list, and set the JWT secret/keys in the
production project. Expected: sign-in works for a real account; redirects land only on allowed origins.
Evidence: settings capture + a real sign-in/sign-out. STOP: wildcard redirects or a default JWT secret.

**11. Storage configuration.**
Action: define the `documents` bucket as **private** with the **10,485,760-byte** ceiling and the
canonical RLS policies; do not reuse demo objects. Expected: bucket private, limit exact, policies
present. Evidence: `storage.buckets` row + policy list + one real upload/download/sign test.
STOP: a public bucket or a changed ceiling.

**12. PostgREST roles and grants.**
Action: verify the `anon` / `authenticated` / `service_role` grants match the frozen canonical set.
Expected: anonymous cannot read tenant data; role separation intact. Evidence: grant listing +
anonymous read attempt refused. STOP: any over-grant.

**13. Provision the backend's production secrets.**
Action: populate the platform secret store (never the repository) with at minimum:
`SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (and `SUPABASE_SERVICE_ROLE_KEY` where the code path expects it),
`SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL` (or `SUPABASE_DB_URL`),
the email/SMTP provider credentials (`RESEND_API_KEY`, `FOUNDER_EMAIL`, or the SMTP set),
analytics keys, and the backup set — `CT_BACKUP_OBJECT_STORE` (`s3` in production),
`CT_BACKUP_S3_ENDPOINT`, `CT_BACKUP_S3_REGION`, `CT_BACKUP_S3_BUCKET`, `CT_BACKUP_S3_ACCESS_KEY`,
`CT_BACKUP_S3_SECRET_KEY`, `CT_BACKUP_S3_PREFIX` (if used), `CT_BACKUP_ENCRYPTION_KEY` (base64, 32
bytes), `CT_BACKUP_KEY_ID`, `CT_BACKUP_RETENTION_DAYS` (where retention is enforced), plus
`CT_BACKUP_PRUNE_ARTIFACTS=1` if artifact pruning is wanted.
Expected: every variable present in the store; `git grep` finds none of the values. Evidence: variable
name list (values redacted) + the grep. STOP: any secret in the repository, or a missing backup key
(the backup code fails closed, and the worker will not run without it).

**14. Deploy the backend at the frozen commit.**
Action: deploy `$RELEASE` to the Render service with the step-13 environment. Expected: deploy
succeeds; `/health` returns **200**; `/` reports `CarbonTally API` `3.0.0`; the log contains
`🗄️ Backup worker started` and **no** `backup worker tick failed`. Evidence: deploy log + endpoint
outputs + the startup log lines. STOP: a failed worker start, or any tick failure.

**15. Post-deploy stability soak (the B7 regression test in production).**
Action: poll for at least **10 minutes** and watch connections. Command:
`while :; do curl -s -o /dev/null -w '%{http_code} %{time_total}\n' https://carbontally-api.onrender.com/health; sleep 15; done`
(plus a `pg_stat_activity` count against the production database). Expected: every poll **200** with
latency stable; connection count flat over time. Evidence: the poll timeline + connection counts.
STOP: a single timeout, or monotonically growing connections — **roll back step 14** and re-open B7.

**16. Deploy the frontend.**
Action: deploy the frozen build to Vercel with the production `REACT_APP_*` wiring. Expected: the app
loads against the production API; `vercel.json` headers (nosniff, SAMEORIGIN, CSP) are served.
Evidence: deploy log + header capture + a load in a clean browser profile. STOP: the app still pointing
at a local/preview API, or a CSP that blocks the production API origin.

**17. Live authentication journeys.**
Action: with a **real** account created through the product's own mechanisms (no shared demo
password): sign-up, sign-in, session persistence, logout, password reset. Expected: all succeed;
refusals are non-disclosing. Evidence: transcript + screenshots. STOP: any bypass of the real path.

**18. Live storage journeys.**
Action: upload, download and sign a document through the production bucket with RLS in force.
Expected: own-org access works; cross-tenant and anonymous access are refused. Evidence: transcripts
showing both the permitted and the refused paths. STOP: any cross-tenant success.

**19. Live email (B1 re-proved in production).**
Action: trigger the canonical transactional email path and confirm **external** receipt by a real
mailbox. Expected: message received; provider reports delivered; the sender/domain are the production
ones. Evidence: the received message (headers) + provider log. STOP: no external receipt — B1's
criterion is not met in production until it is.

**20. Live actor journeys and the isolation/lifecycle matrices against production.**
Action: run the owner / admin / member / viewer journeys, the consultant portfolio + client-switch
(cross-tenant refusal), the CarbonTally admin `/ops` surfaces, then the **B5** matrix and the **B4/D-7**
matrix against the production project with real grants. Expected: **29/29** and **35/35**, EXIT=0.
Evidence: matrix JSON/logs + the screenshots. STOP: any failure — the matrices are the contract.

**21. First production backup, and the first restore rehearsal on a disposable copy.**
Action: (a) run the deployed backup path once end-to-end **against production** and verify the artifact
envelope/checksums by reading it back (the product's own `BackupService`/D1 path — the drill's Phase 1);
(b) restore that artifact into a **disposable** scratch database and run the drill against *that* as the
source. The drill refuses any non-disposable name by design (`tools/backup_recovery_drill.py`,
`assert_disposable`: `ct_*` or `carbontally_test` only, and never a name containing
`qa`/`demo`/`investor`/`prod`/`live`), so **production is never a drill source or target**:
`backend/.venv/bin/python tools/backup_recovery_drill.py --source <scratch_db> --skip-app-check`
(no `--keep-target`, so the scratch target is dropped and only the scratch source remains).
Expected: a completed production backup job; an artifact whose SHA-256 re-verifies; a restore that
reproduces the schema and factor counts; the drill exits **0**. Evidence: job row, artifact manifest,
restore report, drill output. STOP: any verification failure — a production backup path that has never
restored is not a recovery capability.

**22. Assemble the evidence pack and hand the decision over.**
Action: collect step 1–21 evidence (SHAs, logs, JSON, screenshots, matrices, drill report) into one
indexed pack and hand it to the acceptance authority. Expected: the pack is complete and every claim in
it is traceable to an artifact. Evidence: the pack index itself. STOP: the operator does **not** record
acceptance — that is CoStrict / OHD's act alone (FINAL-02 §17).

---

## 4. Abort and rollback criteria

Stop the sequence and revert to the last good state on **any** of the following; record which one fired.

| Trigger | Where | Response |
| --- | --- | --- |
| Any test/suite/matrix is not green | steps 2, 20 | abort; fix; re-run from the failed step |
| A migration fails or drift appears | step 5 | abort; do **not** skip the migration and continue |
| Backup tables absent/half-applied | step 6 | abort before starting the API (prevents a B7-class failure) |
| Any demo row present in production | step 9 | re-initialize the database; do not clean in place |
| Any secret found in the repository | step 13 | abort; rotate the secret; re-provision |
| Worker start failure or a single `/health` timeout / rising connection count | steps 14–15 | **roll back the backend deployment**, redeploy the previous commit, re-open B7 |
| Cross-tenant access succeeds anywhere | steps 18, 20 | abort immediately; treat as a security regression |
| Backup does not verify or restore | step 21 | abort; the recovery capability is not established |
| No external email receipt | step 19 | do not record B1 as met in production |

**Rollback of the application is a redeploy of the previous frozen commit** (Render + Vercel). Because
FINAL-03 is a **clean initialization with no customer data**, a database rollback means
**re-initializing from the migration set** (step 5 onwards) — not a data restore. The step-4 managed
backup exists precisely so that this is a choice, not a loss.

---

## 5. Evidence pack (index structure)

| Folder | Contents |
| --- | --- |
| `00-freeze/` | step 1 SHA, tag, `git status --porcelain` |
| `01-b7-gate/` | step 2 grep, JUnit XML (275 tests — two-path run; FINAL-02 four-path composite **287** post-fix, §15.2.1), soak timeline |
| `02-b2prime/` | step 3–4 decision note, read-only verifier JSON, restore point |
| `03-database/` | step 5–9 migration log, drift report, production-specific object counts (134/87/198 → 150/98/223), 7,049-factor check + fingerprint, retained-entity before/after preservation dumps |
| `04-platform/` | steps 10–12 auth settings, bucket row + policies, grants, refusals |
| `05-deploy/` | steps 13–16 secret-name list (values redacted), deploy logs, headers, soak |
| `06-journeys/` | steps 17–20 transcripts, screenshots, B5 29/29, B4/D-7 35/35 |
| `07-recovery/` | step 21 job row, artifact manifest, restore report, drill output |
| `08-pack/` | this index + the acceptance authority's recorded decision (step 22) |

---

## 6. Authorization and status statement

**PREPARED, NOT EXECUTED.** At the time of writing, **no step in §3 has been run**: no production
deploy, no production database connection, no migration applied, no backup created or restored, no
configuration or secret changed, no production email, no real customer account. Nothing in this package
has been committed or staged; it exists as a single document in the repository working tree.

**It cannot be run yet.** Gate **P1 (the B7 fix)** and gate **P2 (the BACKUP file set committed)** are
open, and gate **P4 (the B2′ recovery posture)** is the owner's decision — all three are recorded in
FINAL-02 §15.2 / §16.7 / §17. **Executing this sequence before P1–P6 are true would deploy a known,
measured connection-exhaustion defect to production.**

> **Update, 2026-10-02 second pass (§1.1).** P1's *verifiable* clauses are now **locally verified** — the
> suite run, the drill and two 600 s soaks are in `docs/cline/evidence/FINAL-03-P1-B7-20261002/01-b7-gate/`.
> P1 nevertheless remains **false**, because the clause that requires the fix to exist in the **frozen
> commit** cannot be met before P2 is done, and because the B4/D-7 re-run is still outstanding. Nothing in
> this package was executed, staged or committed in that pass; **`00-freeze/` and `02-b2prime/`–`08-pack/`
> do not exist yet, deliberately.**

> **Update, 2026-10-02 — data-preservation pass (Phase 0 + owner decision).** A **read-only** Phase 0
> assessment of the production project was executed (every psql session forced
> `default_transaction_read_only = on`) and the owner's **data decision of 2026-10-02** is now recorded
> as the §0 amendment above. Measured production baseline: **134 public tables · 87 RLS-enabled · 47
> RLS-disabled · 198 policies · 7,049 emission factors · applied migrations to `20260927000000` (25
> unapplied)**; the retained entities are two owner TEST organisations and two owner TEST accounts with
> **2 `organization_members` rows, 101 org-linked rows and 58 storage objects**. The unapplied migration
> set was verified **additive and non-destructive** for those rows. Evidence and the preservation plan:
> `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/`.
>
> This pass **executed no step of §3**: no commit, no deploy, no migration, no production write, no
> deletion, and no change to the local demo environment. **Gates P2 (freeze scope), P5 (backup secret
> material) and P6 (Render/Vercel/SMTP identity) remain OPEN**, and one **new decision item** is raised
> — step 7's `149/149/271` expectation is unachievable and partly production-prohibited (§7 note;
> evidence pack §6.3). Status line:
> `FINAL-03 DATA PRESERVATION PLAN READY — AWAITING P2/P5/P6`.

**Acceptance is not this package's, nor the operator's, to give.** Step 22 hands the evidence to
CoStrict / OHD; their recorded verdict is the only acceptance event.

**Owner sign-off to authorize execution (to be completed by the owner, not by Cline):**

| Field | Value |
| --- | --- |
| Authorized by | _pending_ |
| Date | _pending_ |
| Release SHA / tag | _pending_ |
| P1–P6 confirmed true | _pending_ |
| B2′ posture decision recorded | _pending_ |

