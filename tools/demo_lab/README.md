# DEMO-T1 — Local Demo Lab (identities + infrastructure)

**Scope:** make the authoritative release reproducibly runnable on a developer machine with
**real, role-bearing synthetic identities**, so the application resolves each actor's
entity/role and enforces the correct boundaries. This provisions **identity and access
foundations only** — no factors, documents, calculations, reports, OCR policy, billing or
manual-processing governance changes.

---

## 1. Topology (local only)

```
release backend (127.0.0.1:8070)
   ├── DATABASE_URL ─────────► PostgreSQL: carbontally_demo_local  (127.0.0.1:54426)
   │                              · release schema built from supabase/migrations/*
   │                              · lab identities + relationships only
   └── SUPABASE_URL ─────────► lab gateway (127.0.0.1:54430)
                                  ├── /rest/v1 → lab PostgREST  → carbontally_demo_local
                                  └── /auth/v1 → local stack GoTrue (supabase_auth_carbon_ledger)
```

The developer's local Supabase stack (`carbon_ledger`) is **read** for schema/keys and
provides authentication; its databases — including the investor demo dataset — are never
reseeded, truncated or altered.

Containers created by this tooling (all disposable, prefixed `carbontally_demo_lab_`):

| container | role |
|---|---|
| `carbontally_demo_lab_postgrest` | REST (PostgREST) over the lab database |
| `carbontally_demo_lab_gateway` | nginx: the single localhost-published port (auth + rest) |

Ports: gateway `54430` (localhost only), lab backend `8070` (with `--backend`).

## 2. Commands

```bash
./tools/demo_lab/run_demo_lab.sh              # stack + provision + verify
./tools/demo_lab/run_demo_lab.sh --backend    # ... and start the release backend
./tools/demo_lab/run_demo_lab.sh --factors    # ... and load the DEMO-T2-C factor datasets
python3 tools/demo_lab/verify.py              # re-verify (server-side)
python3 tools/demo_lab/seed_factors.py --dry-run   # factor plan + checksums (no DB access)
python3 tools/demo_lab/seed_factors.py             # load DEFRA 2025 + SEAI 2025 (serial)
python3 tools/demo_lab/seed_factors.py --reset      # remove ONLY the T2-C factors + batches
./tools/demo_lab/reset_demo_lab.sh            # remove lab DB + containers (+ lab auth users)
./tools/demo_lab/reset_demo_lab.sh --purge-state   # also delete local credentials/evidence
```

Every step is idempotent: re-running creates nothing twice and destroys no lab data.
Factor loading is **off by default** and happens only when `--factors` is passed.

## 3. Actors (authoritative list: `manifest.json`)

| actor | entity | role | workspace |
|---|---|---|---|
| `platform.admin` | CarbonTally internal (platform) | staff role `admin` (`can_manage_organizations`) | `/ops` + admin control plane |
| `operator` | CarbonTally internal staff | staff role `operator` | `/ops` |
| `pe.manager` | Processing Entity Alpha | staff role `pe_manager` (entity-scoped) | `/pe` |
| `owner.a` / `admin.a` / `member.a` / `viewer.a` | Demo Lab Organisation A | owner / admin / member / viewer | `/home` |
| `owner.b` / `viewer.b` | Demo Lab Organisation B | owner / viewer | `/home` |
| `consultant.owner` / `consultant.member` | Demo Lab Carbon Consultants (firm) | owner / consultant (member capability flags all false) | `/consultant` |
| `owner.clienta` / `owner.clientb` | Client A / Client B (consultant-managed organisations) | owner | `/home` |

E-mail domain: `@demo-lab.carbontally.local` (distinct from the investor demo dataset's
`@demo.carbontally.local`).

## 4. Credentials

* **Never in the repository.** Tooling reads/writes `<state dir>` (default
  `~/ct_local_env/demo_lab/`); `credentials.local.json` is created mode `0600`.
* The lab generates its own **synthetic password** and a **JWT secret** locally; service/anon
  keys come from the *local* stack. No production credential, URL or dataset is used.
* Rotate: `./tools/demo_lab/reset_demo_lab.sh --purge-state` then `run_demo_lab.sh`.

## 5. What `verify.py` proves

* authentication per actor (password grant against the local GoTrue);
* `GET /api/v3/me/context` returns the expected **actor type, destination, organisation and
  role** for every actor;
* a probe matrix over real release gates — organisation reads, the owner/admin-only audit
  surface, the consultant plane, the PE plane, the admin control plane — each with an
  expected ALLOW or DENY;
* isolation rules: Org A ↮ Org B, Client A ↮ Client B, consultant ↮ unrelated organisation,
  customer ↮ admin plane, customer/internal staff ↮ PE plane, viewer/member ↮ owner/admin.

Evidence JSON is written to `<state dir>/evidence/` (no tokens or passwords stored).

## 6. Factor datasets (DEMO-T2-C)

The lab can be loaded with the **verified** DEFRA and SEAI factor datasets so real factor
matching/selection can be exercised (server-side; `emission_factors` stays client-inaccessible).

| dataset | workbook (in the release) | factor_set / country | rows |
|---|---|---|---|
| DEFRA 2025 (DESNZ) | `tools/carbon_data_factory/factors/ghg-conversion-factors-2025-flat-format.xlsx` | `DEFRA-2025` / `GB` | **7,029** (1,711 skipped, 0 duplicates) |
| SEAI 2025 (V1.7) | `tools/carbon_data_factory/factors/SEAI-conversion-and-emission-factors.xlsx` | `SEAI-2025` / `IE` | **20** (8 skipped) |
| | | total | **7,049** `emission_factors`, 2 active `import_batches` |

Mechanism: `tools/demo_lab/seed_factors.py` orchestrates the **existing verified importers**
(`python -m src.commands.import_defra`, then `... import_seai`) in `sync` mode. No parsing,
mapping, checksum or provenance logic is duplicated, no raw SQL factor rows are written and
nothing is copied from the reference database — the importer computes each batch's
`source_checksum` from the workbook bytes.

**Target guard.** The seeder refuses to write unless the database name is exactly
`carbontally_demo_local` (exit 3, before any write). `postgres` (the investor/reference dataset),
`carbontally_test`, `carbontally_qa_phase8`, `ct_*` clones and a DSN with no database name are all
refused; a local hostname is never treated as evidence of safety.

```bash
python3 tools/demo_lab/seed_factors.py --dry-run    # plan, workbooks, SHA-256s — no DB access
python3 tools/demo_lab/seed_factors.py              # DEFRA sync, then SEAI sync (serial)
python3 tools/demo_lab/seed_factors.py --reset      # remove ONLY the T2-C factors + batches
python3 tools/demo_lab/seed_factors.py --db-url postgresql://…/carbontally_demo_local
```

* **Idempotent.** A repeat run re-points the same factor rows to a new provenance batch
  (0 inserted / 7,029 updated for DEFRA; 0 / 20 for SEAI), deactivates the previous batch and
  keeps **exactly one active batch** per provider/year. Factor counts stay 7,029 / 20 / 7,049.
* **O-2 caveat.** `import_batches.rows_imported` is the **insert** count, so a repeat `sync`
  shows `rows_imported = 0` while every factor is linked to the new batch. Read linked-factor
  counts from `emission_factors`, never from `rows_imported`.
* **Reset scope.** `--reset` deletes only `factor_set IN ('DEFRA-2025','SEAI-2025')` and their
  `import_batches` rows. Organisations, memberships, users, audit rows, customer factors,
  other providers' rows and all lab infrastructure are untouched (asserted by the run).
* **Serialised imports (required).** OHD finding **O-1** is unresolved: concurrent imports can
  leave more than one active batch for a provider/year. The seeder runs DEFRA then SEAI strictly
  one after the other — never start a second provider import concurrently.
* **Prerequisites.** The backend venv (`backend/.venv/bin/python`) with `psycopg2`/`openpyxl`
  installed (override with `DEMO_LAB_PYTHON`), Docker access to the local Supabase cluster, and
  the two workbooks present at the paths above. The seeder verifies each workbook's SHA-256
  against the reference value before/after loading.
* **Evidence.** Written outside the repository:
  `<state dir>/evidence/t2c_{dryrun,seed,reset}_*.json` (plus `t2c_seed_latest.json`).
* **Not included:** customer factors, documents, scenarios, calculations, snapshots and reports
  (later workstreams).

## 7. Known limitations (recorded honestly)

1. **Authentication is delegated to the local stack GoTrue.** The lab does not run its own:
   the supabase GoTrue image migrates an existing `auth` schema but cannot bootstrap one, and
   its migrations expect objects from Supabase's platform bootstrap (e.g.
   `auth.code_challenge_method`), so a fresh isolated auth schema crash-loops. Using the
   stack's healthy GoTrue (same image) gives real password logins while adding only
   clearly-namespaced lab users to the stack's auth data.
2. **Auth vs data split.** Auth lives in the stack database, lab data in the lab database, so
   `provision.py` mirrors the 13 lab user ids into the lab database's `auth.users` to satisfy
   the release's foreign keys (ids and e-mails only — no hashes, no sessions).
3. **One release migration is tolerated, not applied:**
   `20260823000000_d32_private_documents_storage.sql` needs `storage.buckets`; the lab
   deliberately omits the storage schema (documents are a later workstream). Recorded in the
   stack summary output.
4. **F-T1-001 (product defect, outside this task):**
   `GET /api/v3/reporting/audit-activity` returns **HTTP 500** for a correctly-authorized
   organisation owner (`asyncpg: operator does not exist: uuid = text`). T1 does not fix it;
   it is reported for a separate bounded task.
5. Identities and infrastructure only **by default**: no documents, calculations, reports, MPG
   grants, clarification cases or reconciliation data are created — those belong to later demo
   workstreams. Factor datasets are loaded **only** when explicitly requested
   (`run_demo_lab.sh --factors` or `seed_factors.py`); customer factors remain out of scope.
