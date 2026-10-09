# CT-CARBONTALLY-FOUNDATION-DOCS-INTENT-04 — Documented intent: the two local databases and the emission-factor seed

**Reference:** `CT-CARBONTALLY-FOUNDATION-DOCS-INTENT-04`
**Type:** Read-only documentation-intent search (Phase 4 of the foundation series)
**Branch:** `p8-release-reconciled`
**HEAD at execution:** `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` (unchanged by this task)
**Repository change produced by this task:** this report only (one new untracked file)
**Production contact:** none. No migration, seed, DDL/DML, RLS, configuration or database write of any kind.
**Question answered:** "what was supposed to happen" — never "what happened" except where a document
itself says it happened.

---

## 0. Method, scope and source classification

### 0.1 Search corpus

| Corpus | Coverage |
| --- | --- |
| `docs/**/*.md` | 930 markdown files (all subfolders), including `docs/architecture/`, `docs/operations/`, `docs/audit/`, `docs/audits/`, `docs/verification/`, `docs/deepseek/`, `docs/cline/`, `docs/ohd/`, `docs/implementation/`, `docs/demo-investor/` |
| `AGENTS.md` | searched for database references |
| `tools/**` | repository tooling and tool documentation (`tools/demo_lab/*` etc.) |
| `scripts/`, `qa_harness/` | searched (no hits for either database name) |
| `supabase/migrations/*.sql` | read for migration-header statements of purpose and target |
| Supplementary (flagged, outside `docs/`) | `Research/CT-PO-DEMO-LAB-PERSISTENCE-01/` (untracked working-tree research) and `~/ct_local_env/README.md` (outside the repository; cited *by* repository documents and read for the quoted text only) |

### 0.2 Method

Literal and case-insensitive `grep -rn` for: `carbontally_demo_local`, `ct_local_93d5cdd`, `7,049`,
`7049`, `emission_factors`, `demo lab`, `demo_lab`, `migration ledger`, `schema_migrations`,
`150+`, `150 tables`, `154 tables`, and each of the five migration timestamps `20261030`–`20261104`
(and each migration's file name). Only the passages that answer the seven questions were read.
No document was modified except the creation of this report. No seed, migration or database command
was run.

### 0.3 Evidence labels used below (applied per *passage*, not per document)

* **[INTENDED]** — the document states a goal, requirement, PO decision or ratified design.
* **[PLANNED]** — the document states a target that is explicitly not yet met.
* **[DONE]** — the document states that an action was executed (and, where stated, verified).
* **[MEASURED]** — an audit/census/verification record states an observed value of the current system.
  This is evidence of the *state*, not of intent, and is labelled as such throughout.
* **[PO DECISION]** — a ratified Product Owner decision (the strongest intent evidence available).

Where a document is ambiguous the passage is quoted and the ambiguity is left unresolved (§3).

---

## 1. Executive summary — one line per question

| # | Question | Status |
| --- | --- | --- |
| Q1 | Demo lab creation (`carbontally_demo_local`) | **PARTIAL** — creation and intended data shape are documented as intended and as done; the *comparative* claim ("less data than the original") is **NOT FOUND IN DOCS** as a stated goal |
| Q2 | Emission-factor seeding (which database, what count) | **FOUND** — the Demo Lab is the documented factor target at **7,049** (DEFRA-2025 7,029 + SEAI-2025 20, [PO DECISION] DEMO-T2-C CLOSED); `ct_local_93d5cdd` is documented at **0 factors** and is explicitly refused by the seeder's target guard |
| Q3 | Database lineage between the two databases | **PARTIAL** — the relationship is documented (same physical cluster, two different logical databases, different creation dates and different provisioning mechanisms); no document states that either was derived from the other; `ct_local_93d5cdd` is given several **conflicting role labels**, and neither "schema-only" nor "audit-only" is stated as its intended role |
| Q4 | RLS migration work and its application targets | **FOUND** — per-DB RLS policy counts, the QA-only PO prohibition on the P8 RLS group, and the FINAL-03 RLS pair (43-table artefact + `staff_workload` residual) with its source/template database (`ct_local_93d5cdd`) are all documented |
| Q5 | Table-count expectations | **PARTIAL** — documented counts exist for both databases (Demo Lab **141**, `ct_local_93d5cdd` **135**, production **150**, canonical rebuild **145**); no document states an expectation of **154** for the Demo Lab; **"150+ tables" does not appear anywhere in `docs/`** |
| Q6 | The five uncommitted migrations (`20261030`–`20261104`) | **FOUND** — each migration's purpose is documented (migration header + workstream reports); the documented application target is the **Demo Lab** `carbontally_demo_local` (documented as done: full-chain replay by `tools/demo_lab/stack.py`, plus two targeted manual applications); a **[PO DECISION]** records that the CT-MP-SUB-003 migrations require separate review before application to any environment where they are not already applied, and that this "does NOT authorize production migration or deployment" |
| Q7 | Applied-migration ledger (`supabase_migrations.schema_migrations`) | **FOUND** — the absence is explained for the development database, for `ct_local_93d5cdd` and for `carbontally_demo_local`; a one-time bootstrap is documented as *recommended and not executed*, and the environment is classified as a known, recorded gap rather than a defect |

---

## 2. Findings by question

### Q1 — Demo lab creation (`carbontally_demo_local`)

**Status: PARTIAL.** Creation and intended data shape: **FOUND**. "Less data than the original" as a
stated goal: **NOT FOUND IN DOCS**.

#### Q1.1 Which documents describe *creating* `carbontally_demo_local`

**`tools/demo_lab/README.md`** (DEMO-T1 tooling documentation) is the canonical description. It
states the purpose and the intended contents of the database:

> "**Scope:** make the authoritative release reproducibly runnable on a developer machine with
> **real, role-bearing synthetic identities**, so the application resolves each actor's
> entity/role and enforces the correct boundaries. This provisions **identity and access
> foundations only** — no factors, documents, calculations, reports, OCR policy, billing or
> manual-processing governance changes." — `tools/demo_lab/README.md:2-8` **[INTENDED]**

> "│   ├── DATABASE_URL ─────────► PostgreSQL: carbontally_demo_local  (127.0.0.1:54426)
>  │                              · release schema built from supabase/migrations/*
>  │                              · lab identities + relationships only" — `tools/demo_lab/README.md:16-18` **[INTENDED]**

It also states the boundary against the pre-existing databases:

> "The developer's local Supabase stack (`carbon_ledger`) is **read** for schema/keys and
> provides authentication; its databases — including the investor demo dataset — are never
> reseeded, truncated or altered." — `tools/demo_lab/README.md:24-26` **[INTENDED]**

**`docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md`** records the database
as the *canonical* local environment and names what it is not:

> "| Canonical database | **`carbontally_demo_local`** |" — line 21 **[INTENDED]**

> "| Explicitly NOT canonical | `postgres` (flagship), `carbontally_qa_phase8`, `carbontally_test`,
> production — **none mutated** |" — line 28 **[INTENDED]**

**`docs/architecture/CT-PO-P12-STEP2-ENVIRONMENT-PROVENANCE-20260924.md`** records the creation
act itself, in a mutation ledger:

> "| `reset_demo_lab.sh` | dropped `carbontally_demo_local`; removed the 3 lab containers; deleted the
> 13 lab auth users (`@demo-lab.carbontally.local`) from the local stack GoTrue |" — line 76 **[DONE]**

> "| `run_demo_lab.sh --backend --factors` | created the lab DB from `supabase/migrations/*`;
> provisioned 13 lab actors; wrote `<state>/backend.env`; started the backend; loaded 7,049 factors |" — line 77 **[DONE]**

**`docs/audit/costrict/CSTR-CARBONTALLY-ENVIRONMENT-RECON-001-20261003.md`** records the
three-environment intent and identifies the Demo Lab as the local one:

> "The **canonical local environment is the Demo Lab** (`carbontally_demo_local` on the developer's
> local Supabase stack + a release backend on `:8070`), intended to let the owner run **real,
> role-bearing** actors through the full pipeline." — line 38 **[INTENDED]**

> "**Intent** (`CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY` §H): a **freshly provisioned Demo
> Lab on the current release schema**, reproducible, with the historical `postgres` dataset retained
> **read-only** as reference." — line 50 **[INTENDED]**

#### Q1.2 What was its intended data shape?

The intended shape is stated in **absolute** terms, first as a frozen target list, then as a frozen
as-seeded manifest.

> "| Direct customer orgs | 2 | 2 | **PASS** | / | Consultant firm | 1 | 1 | **PASS** | /
> | Client orgs | 2 | 2 | **PASS** | / | Processing entities | 2 | **1** | **FAIL (target unmet)** | /
> | Users | 13 (frozen) | 13 | **PASS** | …" — `docs/architecture/CT-PO-P12-STEP2-EXPECTED-COUNT-VERIFICATION-20260924.md:16-20` **[PLANNED** (the table's own columns are *Expected* vs *Actual*)**]**

> "**Counts: PASS WITH FAILURES.** All investor-demo data targets are met except **processing
> entities (1 of 2)**, with three recorded observations." — same file, line 76 **[PLANNED]**

> "| Direct customer organisations | 2 | `Demo Lab Organisation A` … | Consultant firm | 1 | … /
> | Client organisations | 2 | … / | Users (auth mirror) | 13 | … / | Organisation members | 8 | …" — `docs/architecture/CT-PO-P12-STEP2-FROZEN-SEED-MANIFEST-20260924.md:30-38` **[DONE]**

The tooling documentation states what the lab deliberately does **not** contain by default:

> "Identities and infrastructure only **by default**: no documents, calculations, reports, MPG
> grants, clarification cases or reconciliation data are created — those belong to later demo
> workstreams. Factor datasets are loaded **only** when explicitly requested
> (`run_demo_lab.sh --factors` or `seed_factors.py`); customer factors remain out of scope." — `tools/demo_lab/README.md:164-167` **[INTENDED]**

> "Every step is idempotent: re-running creates nothing twice and destroys no lab data.
> Factor loading is **off by default** and happens only when `--factors` is passed." — `tools/demo_lab/README.md:57-58` **[INTENDED]**

#### Q1.3 Was "less data than the original" documented as a goal?

**NOT FOUND IN DOCS as a goal.** No document located by this search states that the Demo Lab was
intended to hold *less data than the original database*. The documentation instead expresses the
separation as **independence and non-interference**, and specifies the lab's own contents
absolutely (2 direct orgs, 2 client orgs, 1 consultant firm, 13 users).

The nearest comparative statements are descriptive labels and guard rules rather than goals:

> "`postgres` (the investor/reference dataset), `carbontally_test`, `carbontally_qa_phase8`, `ct_*`
> clones and a DSN with no database name are all refused" — `tools/demo_lab/README.md:113-115` **[INTENDED** (as a guard rule)**]**

> "The configured dev database (`ct_local_93d5cdd`) is not a demo environment at all: 25
> organisations, no documents, **no factors**, no snapshots, and a **2-table storage substrate** — it
> cannot process a document." — `docs/architecture/CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924.md:483` **[MEASURED]**

The measured size difference between the databases is recorded as observation, not as a target:

> "| organisations | **975** | 4 | **25** | **25** | **2** |" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:139` **[MEASURED]**
> (column order: `postgres` · `carbontally_demo_local` · `ct_local_93d5cdd` · `carbontally_qa_phase8` · Production)

### Q2 — Emission-factor seeding

**Status: FOUND.**

#### Q2.1 Which database(s) should hold `emission_factors`, and with what count

**`carbontally_demo_local` is the documented target**, with the count stated explicitly as
**7,049** (DEFRA-2025 7,029 + SEAI-2025 20):

> "| DEFRA 2025 (DESNZ) | `tools/carbon_data_factory/factors/ghg-conversion-factors-2025-flat-format.xlsx` | `DEFRA-2025` / `GB` | **7,029** (1,711 skipped, 0 duplicates) |
> | SEAI 2025 (V1.7) | `tools/carbon_data_factory/factors/SEAI-conversion-and-emission-factors.xlsx` | `SEAI-2025` / `IE` | **20** (8 skipped) |
> | | | total | **7,049** `emission_factors`, 2 active `import_batches` |" — `tools/demo_lab/README.md:100-104` **[INTENDED]**

The seeder is documented as **refusing every other database by name**, including `ct_*` databases:

> "**Target guard.** The seeder refuses to write unless the database name is exactly
> `carbontally_demo_local` (exit 3, before any write). `postgres` (the investor/reference dataset),
> `carbontally_test`, `carbontally_qa_phase8`, `ct_*` clones and a DSN with no database name are all
> refused; a local hostname is never treated as evidence of safety." — `tools/demo_lab/README.md:112-115` **[INTENDED]**

This is confirmed as a ratified closure condition, not merely tool behaviour:

> "| 9 | Target guard verified (writes refused unless the database is exactly `carbontally_demo_local`) |" — `docs/architecture/CARBONTALLY_PHASE8_DEMO_T2C_FACTOR_DATASET_LOADING_PO_CLOSURE_DECISION_20260920.md:55` **[DONE / PO DECISION** (the document is a PO closure record for DEMO-T2-C, "CLOSED")**]**

> "| Domain | State | … | `factor_set='DEFRA-2025'` / `country='GB'` | **7,029** | / `factor_set='SEAI-2025'` / `country='IE'` | **20** | / Total `emission_factors` | **7,049** |" — same file, lines 69-71 **[DONE]**

> "4. The target guard remains mandatory: Demo Lab writes only, never `postgres`, `carbontally_test`,
> `carbontally_qa_phase8`, `ct_*` clones, unnamed DSNs, or any production surface." — same file, lines 116-117 **[PO DECISION** (binding consequence)**]**

#### Q2.2 Was `ct_local_93d5cdd` ever intended to hold factors?

**NOT FOUND IN DOCS.** Every document located that states a factor population for
`ct_local_93d5cdd` states **zero**, and the seeder's documented guard explicitly refuses `ct_*`
databases:

> "| `ct_local_93d5cdd` | **135** | none | 67 migrations applied (documented) | P16, P16R, B2, manual grants |
> The canonical repo's target; **no factors, no `auth`** |" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:117` **[MEASURED]**

> "the canonical local DB (`ct_local_93d5cdd`) contains **no pipeline data** — `emission_factors=0`,
> `suppliers=0`, `customer_documents=0`, `calculation_snapshots=0`, `emissions_logs=0`,
> `evidence_line_items=0`, `report_versions=0`, `disclosure_requirement_versions=0`" — `docs/architecture/CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927.md:37` **[MEASURED]**

> "`ct_local_93d5cdd` has the schema the canonical repository targets but **no factors and** …" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md:356` **[MEASURED]**

The reconciliation ledger records the two factor populations as a duplication to be resolved, and
records the (unelected) PO decision:

> "| RECON STATUS | **DUPLICATE (content) with `carbontally_demo_local`** — identical content hash, different row ids |" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md:178` (DAT-01, `postgres`) **[MEASURED]**

> "| PO DECISION? | YES — reconcile first (only one factor library should survive into the canonical environment) |" — same file, line 192 (DAT-02, `carbontally_demo_local`) **[PLANNED** (a decision is recorded as *required*, not as taken)**]**

#### Q2.3 Is 7,049 a documented number anywhere?

**Yes — extensively, and as a preserved invariant across at least four distinct contexts.** It is
documented for the legacy/development database, for the Demo Lab, for production, and as a *test
assertion*.

| Context | Documented value | Citation |
| --- | --- | --- |
| `postgres` (development/investor dataset) | 7,049 (DEFRA 7,029 + SEAI 20) | `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:141, 152-157` **[MEASURED]** |
| `carbontally_demo_local` (Demo Lab) | 7,049, `import_batch_id` set, 2 `import_batches` | `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:141, 156`; `tools/demo_lab/README.md:104` **[MEASURED / INTENDED]** |
| `ct_local_93d5cdd` | **0** | `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:141` **[MEASURED]** |
| `carbontally_qa_phase8` | **0** | same row; also `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:294` **[MEASURED]** |
| Production | 7,049 (owner evidence); cutover expects "exactly **7,049** rows" | `docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md:52`; `.../DATABASE-RECONCILIATION-20260927-REPORT.md:141, 158` **[INTENDED** (cutover gate) **/ MEASURED]** |
| v2.1 factor baseline | 7,049 / 7,029 / 20 recorded and cross-referenced | `docs/cline/CarbonTally-v2.1-Traceability-Matrix-v1.0.md:89, 259, 612, 688`; `docs/cline/CarbonTally-SEAI-Development-DB-Import-v1.0.md:18, 42` **[DONE]** |
| Reference index | "`7049` rows in `emission_factors`"; "Do not alter factor data: the production `emission_factors` table is …" | `docs/CARBONTALLY_V3_REFERENCE_INDEX.md:184, 254` **[INTENDED** (instruction) **/ MEASURED]** |
| Test invariant | "`test_factor_baseline_unchanged` expects 7049 factors: QA currently holds **0**" | `docs/cline/reports/CT-P8-RLS-4A-2-HARDENING-20260914-059.md:59` **[MEASURED]** |

Two additional documented properties of the number:

> "**Emission-factor provenance established:** the 7,049 factors (DEFRA-2025 7,029 + SEAI-2025 20, all
> reporting_year 2025) were imported via **generated idempotent SQL insert scripts** … **not** via
> migrations … and **not** via the investor-demo seed" — `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md:17` **[DONE]**

> "| Local vs local identity | **Content-identical, row-id-different**: content hash `eefbcf6e3d26ea6d908bac182fe4a309`
> in **both**; id hashes differ … | Local vs live identity | **UNKNOWN — not verifiable here.**" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:157-158` **[MEASURED]**

---

### Q3 — Database lineage

**Status: PARTIAL.** The *relationship* is documented; a *derivation* of one database from the other
is **NOT FOUND IN DOCS**; the intended role of `ct_local_93d5cdd` carries **conflicting labels**
(§3.3) and neither "schema-only" nor "audit-only" is stated as its role.

#### Q3.1 What the documents say about the relationship

> "The two repositories are not attached to different clusters; they are attached to
> **different logical databases of the same cluster** (`postgres` vs `ct_local_93d5cdd`)." — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:234-235` **[MEASURED]**

> "| PRINCIPAL | 6 | `postgres`, `carbontally_demo_local`, `ct_local_93d5cdd`, `carbontally_qa_phase8`, `carbontally_test`, `carbontally_b2_clone_20260913` |" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:189` **[MEASURED]**
> (i.e. both are classified **PRINCIPAL**, not ephemeral clones — the 70 ephemeral `ct_*` databases are the ones documented as template-clones, same file, lines 191, 195-200)

> "The **storage did not move**. Both repositories declare the same Supabase project
> (`project_id = carbon_ledger`) and therefore address the **same Postgres volume** … and repository
> B's `backend/.env` was pointed at a **newly created, disposable logical database**
> (`ct_local_93d5cdd`, 2026-09-19) with an unroutable Supabase URL (`:19999`), while repository A's
> backend kept pointing at the …" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:374-380` **[MEASURED]**

> "| Creation of `ct_local_93d5cdd` + 67-migration apply | Yes (`ct_local_env/README.md`) | Yes (`psql` commands; `start_latest.sh`) | **Yes** (DB exists; 25 orgs dated 2026-09-19) | **Yes** | **Yes** (135 tables / 218 policies read today) |" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:215` **[DONE]**

#### Q3.2 Was one derived from the other?

**NOT FOUND IN DOCS.** No document states that `carbontally_demo_local` was created from
`ct_local_93d5cdd`, or vice versa. Each has its own separately documented provisioning mechanism and
date:

* **`ct_local_93d5cdd` — 2026-09-19, by applying migration files directly.** The repository
  reconciliation report cites `~/ct_local_env/README.md` (a file outside the repository) as the
  record; that README states the environment's identity:

  > "database  `ct_local_93d5cdd` (disposable)" — `~/ct_local_env/README.md:34` **[DONE]** (outside the repository; cited by `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:215, 360`)

  > "the schema was built by applying migration files directly (`psql`), not by the Supabase CLI, which
  > is why no ledger exists." — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:284-286` **[DONE]**

* **`carbontally_demo_local` — 2026-09-24, by the Demo Lab provisioner.** The census describes it as
  the most modern durable schema and records its builder:

  > "No migration ledger at all; its schema was provisioned by `tools/demo_lab`
  > (`stack.py`/`provision.py`) rather than by Supabase CLI migration history." — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:270-271` **[DONE]**

  > "Factor library present with `import_batch_id` set on all rows and 2 `import_batches` rows →
  > imported through the Demo Lab's own factor-import path, **not** the legacy generated-SQL path used
  > by `postgres`." — same file, lines 272-274 **[DONE]**

  This is corroborated by the Step-2 canonical record (81 migration files, 0 errors, 141 tables) and
  by the run provenance ("created the lab DB from `supabase/migrations/*`").
  Citations: `docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md:34-38`;
  `docs/architecture/CT-PO-P12-STEP2-ENVIRONMENT-PROVENANCE-20260924.md:77`.

The two are therefore documented as **siblings built independently from the same migration directory
at different times**, not as parent/child. The only `derive`-type lineage documented in this cluster
concerns other databases: the 70 ephemeral `ct_*` databases are recorded as
`CREATE DATABASE <name> TEMPLATE <source>` clones (`docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:195-200`),
and `ct_b7_schema_1790937075` is recorded as "a schema-only clone of `ct_local_93d5cdd` with both
BACKUP migrations applied" (`docs/cline/evidence/FINAL-03-P1-B7-20261002/01-b7-gate/README.md:34`).

#### Q3.3 Is `ct_local_93d5cdd` intended as a schema-only or audit-only environment?

**NOT FOUND IN DOCS.** Neither "schema-only" nor "audit-only" is stated as its intended role. It is
also demonstrably not schema-only by the documents' own measurements (it holds 25 organisations,
658 `public.users`, 5 staff profiles, 3 consultant profiles, 5 customer factors —
`docs/architecture/CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927.md:118`).

Instead, the documents label it inconsistently (see §3.3 for the full conflict list): "the canonical
repo's target", "READINESS-02 / latest-repo local run", "disposable", "Source/disposable baseline
(schema reference)", "the local QA database", "baseline clone", and "not a demo environment at all".

---

### Q4 — RLS migration work

**Status: FOUND.**

#### Q4.1 Which documents record RLS policy updates across tables

| Document | What it records |
| --- | --- |
| `docs/architecture/CARBONTALLY_PHASE8_RLS_SECURITY_REMEDIATION_PLAN_20260914.md` | The RLS workstream plan and its read-only **census**: "tables with RLS **enabled** \| **133 / 133** \| `rls_disabled = 0`" (line 58); "org-scoped tables **with RLS but NO policy** \| **5** \| **fail-closed coverage gaps**" (line 62); decision rows including "**D-1** \| **APPROVED** — authorise anonymous-grant containment (`RLS-4A-1`) … \| **EXECUTED + VERIFIED** (§A)" (line 8, §A line 14 "QA / non-production only") |
| `docs/architecture/CARBONTALLY_PHASE8_RLS_SECURITY_REMEDIATION_PLAN_20260914.md:100` | The standing rule for the whole workstream: "All steps: QA-only, additive, one migration per step, `rc=0` ×2 re-apply, parity checks (pre-existing grants/policies/RLS flags unchanged), then the §5 verification. **Production remains prohibited (G0-D).**" **[INTENDED]** |
| `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md:251` and `10-final-03-rls-remediation-implementation-and-verification-20261002.md:28, 44-45` | The **implementation record** for the two FINAL-03 RLS migrations: "`20261028000000_ct_final_03_rls_security_remediation.sql` (43 tables enabled — 41 fail-closed with zero policies, 2 enable-only with their 4 policies kept …) **plus the residual-closure follow-up `20261029000000_ct_final_03_staff_workload_rls.sql`**"; policy count "`218 → 218`"; "**No production contact; nothing deployed; nothing committed**" **[DONE]** |
| `docs/cline/reports/CT-P8-RLS-4A-1-DURABILITY-20260914-060.md:61` | "Verified on QA + clones only; **production remains unapplied and unauthorised** (G0-D open)." **[DONE]** |
| `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:284` (FTR-030) | Per-database policy coverage as measured: "`pg_policies`: 178 in `postgres`, 222 in `ct_local_93d5cdd`, 201 in `carbontally_qa_phase8` (all read live); MIG:`20260803000000_rc2_rls.sql`,`20260925000000_p8_rls_4b_group1_enablement.sql`" **[MEASURED]** |
| `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:226-227` | Per-database RLS-enabled tables and policy counts for all six principal databases (116/141/135/133/117/128 tables; 174/298/218/197/198/189 policies) **[MEASURED]** |
| `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md:324` | "Only RLS group 1 is enabled; report-table policy coverage incomplete (deny-all where no `organization_id`)" — with the three P8 RLS migration files named **[MEASURED]** |
| `docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md:852` (B-05) | Foundation-series measurement of the same split: "`carbontally_demo_local` 154 tables / 355 policies … vs `ct_local_93d5cdd` 135 tables / 218 policies (no auth, pipeline-empty). No ledger in either." **[MEASURED]** |

#### Q4.2 Which migrations were expected to apply, and to which database

Three distinct documented populations with three distinct documented targets:

**(a) The P8 RLS group — QA / non-production only; production prohibited.** The cutover package
withdraws a former production RLS expectation and states why:

> "> **Why the former `149 / 149 / 271` figure is withdrawn:** the repository's migration set contains
> **no `ALTER TABLE … ENABLE ROW LEVEL SECURITY` for 47 production tables** (`staff_roles`,
> `system_settings`, `notifications`, `email_logs`, `login_history`, `password_reset_tokens`,
> `audit_trail`, `emission_factors`, …), because the P8 RLS group (`20260920000000`, `20260922000000`,
> `20260923000000`, `20260925000000`) is **QA-only by ratified PO decision** — that migration states
> *"Production is prohibited (G0-D): QA / non-production application only."* Raising production to
> 149/149 is therefore neither achievable from this set nor permitted, and the 47-table RLS gap must
> be an **explicit recorded owner risk decision** (see evidence pack §6.3). Do **not** improvise it." — `docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md:183-186` **[PO DECISION]**

> "⇒ The step-7 expectation **`149 tables · 149 RLS-enabled · 271 policies` cannot be satisfied**, and
> part of it — enabling RLS on the 47 — is **prohibited in production** by a ratified PO decision
> carried by `20260920000000_p8_rls_anon_grant_containment.sql` (*"Production is prohibited (G0-D): QA /
> non-production application only"*)." — `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/08-final-03-p2-p5-p6-rls-decision-package-20261002.md:770` **[PO DECISION]**

The production RLS expectation that *does* apply is stated as a production-specific calculation:

> "Current measured baseline (2026-10-02, read-only): **134 tables · 87 RLS-enabled · 47 RLS-disabled ·
> 198 policies**; the 25 unapplied migrations add **16 tables · 11 RLS-enabled tables · 25 policies**
> → expected after step 5: **150 tables · 98 RLS-enabled · 223 policies**" — `docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md:175-177` **[INTENDED** (cutover gate, with a STOP condition on deviation)**]**

**(b) The FINAL-03 RLS remediation pair — verified against `ct_local_93d5cdd` (as a template source)
and disposable clones; no production contact.**

> "| `postgresql://…/ct_local_93d5cdd` | Source/disposable baseline (schema reference) | Yes (local) |" — `docs/audit/costrict/CSTR-FINAL03-RLS-VERIFY-001-20261002.md:38` **[MEASURED]**

> "clone — `CREATE DATABASE ct_f03_sw_verify TEMPLATE ct_local_93d5cdd` — into which File (1) and then
> File (2)" — `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/10-final-03-rls-remediation-implementation-and-verification-20261002.md:151` **[DONE]**

> "| Local/demo data untouched | **met** — verification ran against `TEMPLATE` clones; the source
> database (`ct_local_93d5cdd`) and the demo lab were never written to, and the source was re-checked
> unchanged after the residual-closure pass (`135/135` RLS, `218` policies, `staff_workload` 0 rows) |" — same file, line 441 **[DONE]**

**(c) The Demo Lab's own RLS expectation — every table enabled, recorded as a canonical property.**

> "| RLS enabled | 141 / 141 | / | RLS policies | **298** |" — `docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md:37-38` **[INTENDED / DONE]**

Finally, the production RLS posture as independently observed later is recorded as
"production Supabase migrated (150 tables / 147 RLS-on / 235 policies / 98 migrations)"
(`docs/audit/costrict/CSTR-CARBONTALLY-ENVIRONMENT-RECON-001-20261003.md:46`) **[MEASURED]** —
consistent with the documented 47-table RLS gap remaining open.

> Note: the only per-*table* policy artefacts in the repository that record a **target database for the
> RLS workstream** are the two FINAL-03 files (verified against `ct_local_93d5cdd` clones) and the P8
> RLS group (QA-only). The FINAL-03 record also states plainly that "the accepted 43-table artefact is
> byte-for-byte unchanged" and that nothing was committed
> (`docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md:251`).

---

### Q5 — Table count expectations

**Status: PARTIAL.** Documented counts exist for both databases and for every other principal
database; **no document states an expected count of 154** for the Demo Lab. **"150+ tables" is
NOT FOUND IN DOCS** — neither the literal string `150+` nor `160+` occurs anywhere under `docs/`
(or in `AGENTS.md`, `tools/`, `backend/`).

#### Q5.1 Documented table counts

| Database | Documented count | Citation | Class |
| --- | --- | --- | --- |
| `carbontally_demo_local` | 136 (pre-reset) → **141** (post-provision; 6 Insight tables, "the Step-1 schema gap is closed") | `docs/architecture/CT-PO-P12-STEP2-ENVIRONMENT-PROVENANCE-20260924.md:31, 55-56`; `.../CANONICAL-DEMO-ENVIRONMENT-20260924.md:36, 45-46` | **[DONE]** |
| `carbontally_demo_local` | **141** (baseline and current, unchanged) | `docs/architecture/CT-PO-CARBONTALLY-FEATURE-DELTA-CHANGELOG-20261003.md:142-148`; `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:224` | **[MEASURED]** |
| `ct_local_93d5cdd` | **135** | `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:224`; `docs/architecture/CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927.md:118`; `docs/architecture/CT-PO-CARBONTALLY-FEATURE-DELTA-CHANGELOG-20261003.md:142-148` | **[MEASURED / DONE]** (the 135 is also recorded as the outcome of the 67-migration build) |
| `postgres` (flagship) | 116 | `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:224` | **[MEASURED]** |
| `carbontally_qa_phase8` / `carbontally_test` / `carbontally_b2_clone_20260913` | 133 / 117 / 128 | `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:224` | **[MEASURED]** |
| "canonical rebuild" (from zero) | **145** tables (0 organisations / 0 factors) | `docs/architecture/CT-PO-CARBONTALLY-SCHEMA-COMPARISON-MATRIX-20260927.md:34, 64` | **[INTENDED / DONE]** |
| Production | 134 before the cutover set; **150** expected after cutover step 5 | `docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md:175-177`; `docs/audit/costrict/CSTR-CARBONTALLY-ENVIRONMENT-RECON-001-20261003.md:46` | **[INTENDED / MEASURED]** |
| `carbontally_demo_local` | **154** | `docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md:385, 522, 852`; `docs/architecture/CT-CARBONTALLY-FOUNDATION-INVENTORY-02.md:54, 69, 1164`; `docs/architecture/CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md:84` | **[MEASURED]** — **only the Phase-1/2/3 foundation series records 154**; no design, PO or Step-2 document states it |

Two nuances recorded in the documents themselves:

* The Demo Lab's table count is documented as an **outcome of schema completeness**, not as a target:
  the Step-2 record's expected/actual table is a list of *entity* counts
  (`EXPECTED-COUNT-VERIFICATION-20260924.md:16-37`), while the table/policy figures appear only under
  "§2 Supporting detail" (same file, lines 43-45). The frozen seed manifest does not state a table
  count at all (`FROZEN-SEED-MANIFEST-20260924.md`, in full).
* The environment drift across five principal databases was explicitly flagged as a **gap**, not an
  expectation:

  > "| **GA-07** | MEDIUM | **No single authoritative environment.** Public-table counts: flagship 116 ·
  > `carbontally_demo_local` 141 · `carbontally_test` 117 · `carbontally_qa_phase8` 133 ·
  > `ct_local_93d5cdd` 135 · `ct_p17k_20260926` 145." — `docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md:126` **[MEASURED]**

  > "The drift risk in this environment is therefore not repository drift but **database-generation
  > divergence**: six principal databases carry four different schema generations, and **no database
  > carries the canonical 89-file generation**." — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:323-327` **[MEASURED]**

---

### Q6 — The five uncommitted migrations (`20261030`–`20261104`)

**Status: FOUND.** Each file's purpose is documented in its own header and in workstream reports; the
documented application target is the **Demo Lab** `carbontally_demo_local` (documented as done, by two
mechanisms); the CT-MP-SUB-004 PO decision record documents that two of them require separate review
before application anywhere they are not already applied and that the decision "does NOT authorize
production migration or deployment".

#### Q6.1 Purpose of each migration

| Migration | Documented purpose (source: migration header + workstream reports) |
| --- | --- |
| `20261030000000_manual_processing_routing.sql` | "PO DECISION (ratified business rule): Manual Processing is a SUBSCRIPTION-PLAN capability, and the routing destination is an explicitly configured Processing Entity. This migration adds the ONE persistent configuration this workflow was missing … `public.manual_processing_processors` `scope_type \| scope_id -> processing_entity_id (active/inactive)`" — migration header, `supabase/migrations/20261030000000_manual_processing_routing.sql` (header comment, lines 2-15). Report form: "creates **exactly one table** — `public.manual_processing_processors` … RLS enabled + zero policies; `anon`/`authenticated` revoked, `service_role` granted). It is additive, idempotent and reversible" — `docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md:175-181` **[DONE]** |
| `20261101000000_ct_mp_sub_003_consultant_coverage.sql` | "CarbonTally CT-MP-SUB-003 — CONSULTANT-SPONSORED MANUAL PROCESSING COVERAGE … PO SPEC: docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md (CT-PO-MP-SUB-003, PO APPROVED — AUTHORITATIVE). Adds the ONE persistent record the consultant-sponsored entitlement model was missing: the per-client SELECTED-CLIENTS allocation ledger. `public.consultant_mp_allocations`" — migration header, `supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql` (header comment, lines 2-11) **[PO DECISION** (spec marked PO APPROVED) **]** |
| `20261102000000_ct_consultant_model_02_capability_admission.sql` | "CT-CONSULTANT-MODEL-IMPLEMENTATION-02 (Phase 1) — consultant capability model. … WHY F-1: consultant ADMISSION was capability-blind … `F-2`: PO-6 (B+C) / §13.1 require FINAL approval on a consultant-MANAGED organisation to be authorised by a consultant capability (CAP-APPROVE)" — migration header, `supabase/migrations/20261102000000_ct_consultant_model_02_capability_admission.sql` (header comment, lines 1-22) **[INTENDED]** |
| `20261103000000_ct_consultant_model_03_client_access_and_mode.sql` | "CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — client access profile, product mode, relationship requests and retention policy. … SAFETY * Additive + idempotent. No RLS policy is weakened, dropped or disabled. * The two new request tables are RLS-enabled with NO policies" — migration header, `supabase/migrations/20261103000000_ct_consultant_model_03_client_access_and_mode.sql` (header comment, lines 2-19) **[INTENDED]** |
| `20261104000000_ct_consultant_client_identity_04.sql` | "CT-CONSULTANT-CLIENT-IDENTITY-04 — client-user invitation lifecycle (PD-1A) and client-user role administration (PD-2A). … PD-1A (A) — CarbonTally-controlled secure single-use invitation; consultant/client must not bypass it. PD-2A (C) — dual authority with explicit boundaries … SAFETY * Additive + idempotent. No column is dropped, renamed or retyped" — migration header, `supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql` (header comment, lines 2-20) **[PO DECISION** (derived from a decision register) **]** |

Corroborating report-level statements:

> "| Migration | Purpose | … | `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | P17A … |
> `20261030000000_manual_processing_routing.sql` | Manual Processing routing |
> `20261101000000_ct_mp_sub_003_consultant_coverage.sql` | `consultant_mp_allocations` (consultant coverage) |" — `docs/architecture/CT-MP-SUB-004-PO-decision-record.md:328-340` **[PO DECISION]**

> "| Migrations | `20260927000000_p8_fin06_manual_processing_governance.sql`, `20261030000000_manual_processing_routing.sql` |" — `docs/architecture/CT-MP-SUB-003-implementation-report.md:30` **[DONE]**

> "`supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql` | additive schema" — `docs/architecture/CT-CONSULTANT-CLIENT-IDENTITY-04.md:183-184` **[DONE]**

The complete object set created by the five files is recorded as exactly four tables:

> "Grepping the five files for object-creating DDL yields exactly **four** tables and no views" — `docs/architecture/CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md:62-71` **[MEASURED]**
> `manual_processing_processors`, `consultant_mp_allocations`, `consultant_relationship_requests`, `consultant_mode_change_requests`; the other two files only `ALTER TABLE`.

#### Q6.2 Intended application target — the Demo Lab (documented as done)

Two mechanisms are documented, and both target `carbontally_demo_local`:

**(i) Full-chain replay by the Demo Lab provisioner** (which applies the working-tree migration
directory, including untracked files):

> "| **1** | **B-06** — the runtime DB contains objects created by migrations that exist in the working
> tree only as uncommitted files | **CONFIRMED** | **`ORIGIN = MANUAL_APPLICATION`**, established from
> the Postgres DDL log: at **2026-10-04 13:13:19 UTC** the *entire* `supabase/migrations/*.sql` chain
> was replayed against `carbontally_demo_local` by the repository's own Demo Lab provisioner
> (`tools/demo_lab/stack.py`, one `docker exec … psql` per file), which globs the working-tree
> migration directory and therefore applies untracked files. `manual_processing_processors` and
> `consultant_mp_allocations` were created in that pass; `consultant_mode_change_requests`/
> `consultant_relationship_requests` were created later (2026-10-06) by targeted manual application. |" — `docs/architecture/CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md:30` **[DONE]**

> "| Local demo lab (`carbontally_demo_local`) | **Yes** — via ordinary bring-up (`stack.py`
> re-applies all migrations) | §7.3 column + row evidence |" — `docs/architecture/CT-CONSULTANT-MODEL-IMPLEMENTATION-02.md:628` **[DONE]**

**(ii) Targeted manual application of a single file** where the lab predates the migration:

> "(`carbontally_demo_local`) was provisioned *before* the CT-04 migration existed," … "`docker exec -i
> supabase_db_carbon_ledger psql -U postgres -d carbontally_demo_local -v ON_ERROR_STOP=1 <
> supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql`." — `docs/architecture/CT-CONSULTANT-CLIENT-ACCESS-UX-01.md:197, 204` **[DONE]**

Same command recorded at `docs/architecture/CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md:166`.

#### Q6.3 What the documents say about *committing* / applying them elsewhere

The most explicit governance statement is the CT-MP-SUB-004 PO decision record, which covers three
migrations including two of the five:

> "* The **CT-MP-SUB-003 migrations are architecturally ratified *in principle***.
> * **BUT each migration requires separate migration review** before being applied **to any environment
> where it is not already applied**.
> * This decision **does NOT authorize production migration or deployment.**" — `docs/architecture/CT-MP-SUB-004-PO-decision-record.md:328-330` **[PO DECISION]**

> "The Demo Lab database already supports the coverage read and write paths, so the migrations'
> **architectural intent** is ratified. However, applying a migration is a **state-changing, potentially
> irreversible operation** … Ratifying the *architecture* is therefore distinct from authorizing the
> *application* of each migration" — same file, lines 341-346 **[PO DECISION]**

Their untracked status is documented as fact in several audit records:

> "`git status` shows exactly two untracked `supabase/migrations/*.sql` files —
> `20261030000000_manual_processing_routing.sql` and `20261101000000_ct_mp_sub_003_consultant_coverage.sql`
> — both **pre-existing** (CT-MP-SUB-003/004 workstream, dated 2026-10-04) and **not** created or
> modified by this task" — `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md:657` **[DONE]**

> "- **New migrations (untracked, 5):** `20261030000000_manual_processing_routing.sql`,
> `20261101000000_ct_mp_sub_003_consultant_coverage.sql`,
> `20261102000000_ct_consultant_model_02_capability_admission.sql`,
> `20261103000000_ct_consultant_model_03_client_access_and_mode.sql`,
> `20261104000000_ct_consultant_client_identity_04.sql`." — `docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md:212-216` **[MEASURED** (Phase-1 foundation record) **]**

> "| Pre-existing unit tests — migration-baseline expectations | **4** | … They assert "latest migration"
> invariants that later migration files violate (`20261029000000_ct_final_03_staff_workload_rls.sql` —
> mtime 2026-10-02; `20261030000000_manual_processing_routing.sql` — 2026-10-04;
> `20261101000000_ct_mp_sub_003_consultant_coverage.sql` — 2026-10-04), none of which this task
> authored" — `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-IMPLEMENT-04-report.md:446` **[DONE]**

**No document was found that authorises, plans or schedules the production application of any of the
five.** The FINAL-03 production cutover package (2026-10-02) defines its production set as
"`supabase/migrations/**` applied in order — the exact shipped set (**96 files** at 2026-10-02)"
(`docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md:43-44`) with the production
database's applied maximum recorded as `20260927000000`, so its 25-file unapplied set ends at
`20261029000000` (`docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md:105-107`).
The five files in question all sort **above** `20261029000000` and are therefore outside every
production set that documents a target; the only documented production authorisation found in this
search concerns the migration set frozen on 2026-10-02, which excludes them.

*(Working-tree observation for orientation only — the migration directory currently holds 103 `.sql`
files, of which the five named files are the highest-versioned.)*

---

### Q7 — Applied-migration ledger (`supabase_migrations.schema_migrations`)

**Status: FOUND.** The absence is explained separately for each database, is classified in the census
as a per-database property, and is accompanied by a recommended one-time bootstrap that is explicitly
recorded as **not implemented**.

#### Q7.1 Why the development database (`postgres`) has no ledger

> "**Missing `supabase_migrations.schema_migrations` explanation:** the current DB was assembled by
> **restore + seed + direct migration application** (not by a single `supabase db reset`/`db push`
> replay), so the Supabase CLI never created the history table. The project config also has
> `[db.migrations] enabled = false` and was modified locally after its only commit (`2d23fb8`)." — `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md:18` **[DONE]**

> "This is the current development database actively used for CarbonTally development (investor-demo
> data present; no `supabase_migrations` history — it was restored from a schema dump, which is why a
> full backup is essential)." — `docs/audit/cline/CARBONTALLY_DEVELOPMENT_DATABASE_BACKUP_REPORT.md:35` **[DONE]**

The same document records the remedy as a *recommended next step that was not performed*:

> "3. Obtain approval for the baseline mechanism: create `supabase_migrations.schema_migrations` and
> record the chain through `20260831010000` as applied (a one-time, explicitly approved bootstrap) — or
> an operator-approved alternative." — `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md:151`, under the heading "§14. Recommended safe procedure for the next step (**NOT implemented**)" **[PLANNED / NOT DONE]**

A later task *did* extend that database's ledger by the normal CLI path, under a temporary config
change: "Post-apply history: `supabase_migrations.schema_migrations` = **41 rows** … (baseline
intact, three appended)" — `docs/audit/cline/CARBONTALLY_MIGRATION_APPLICATION_REPORT.md:37`, with
config "Before: `enabled = false` … Temporarily set to `enabled = true` … **After: restored to
`enabled = false`**" (same file, lines 22-25) **[DONE]**.

#### Q7.2 Why `ct_local_93d5cdd` and `carbontally_demo_local` have no ledger

> "No migration ledger. `ct_local_env/README.md` (2026-09-19) records "135 public tables, **67 migrations
> applied** from `supabase/migrations`; the F-039-1-J uniqueness index and 218 RLS policies are present"
> — i.e. the schema was built by applying migration files directly (`psql`), not by the Supabase CLI,
> which is why no ledger exists." — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:282-286` **[DONE]**

> "No migration ledger at all; its schema was provisioned by `tools/demo_lab`
> (`stack.py`/`provision.py`) rather than by Supabase CLI migration history." — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:270-271` **[DONE]**

> "| `ct_local_93d5cdd` | 0 (no ledger) | — | 135 tables; `ct_local_env/README.md` states 67 migrations
> applied on 2026-09-19 … | **CONFIRMED_APPLIED (67; documented + object-corroborated)**; later
> migrations **CONFIRMED_NOT_APPLIED** |" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:317` **[DONE** (classification) **]**

> "| `carbontally_demo_local` | 0 (no ledger) | — | 141 tables incl. P16/P16R/B2/Insight; provisioned by
> `tools/demo_lab`, not by migration replay | **OBJECTS_PRESENT_APPLICATION_TIME_UNKNOWN** for those
> generations; **CONFIRMED_NOT_APPLIED** for P17 |" — same file, line 316 **[MEASURED]**

#### Q7.3 Is this expected, deprecated, or a known gap?

The documents treat it as an **explained consequence of how each database was built**, classified
per database, and as a **known gap with an unexecuted remedy**.

* Census, per-database ledger column for all six principal databases
  (`docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:229`): `postgres` "**46 rows**"
  (max `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql`); `carbontally_demo_local` and
  `ct_local_93d5cdd` "**ledger table absent**"; `carbontally_qa_phase8` and
  `carbontally_b2_clone_20260913` "ledger table present, **0 rows**"; `carbontally_test` "ledger table
  absent". Absence/presence is thus recorded as a normal per-environment property, not as a defect.
* Reconciliation ledger rows — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md:296-297`:
  "| MIG-04 | Applied migrations of `ct_local_93d5cdd` | … | none | 135 tables, 218 policies; README
  records 67 applied | **CONFIRMED_APPLIED 67 (documented + object-corroborated)** | NO | STRONGLY
  SUPPORTED |" and "| MIG-05 | Applied migrations of `carbontally_demo_local` | … |
  **OBJECTS_PRESENT_APPLICATION_TIME_UNKNOWN** | YES — reconcile first | …" **[MEASURED / PLANNED]**
* The reconciliation report answers both together:
  "`carbontally_demo_local`: no ledger; P16/P16R/B2/Insight/manual-grant objects present →
  `OBJECTS_PRESENT_APPLICATION_TIME_UNKNOWN`" and "`ct_local_93d5cdd`: **67** migrations applied
  (documented in `ct_local_env/README.md`, corroborated by 135 tables / 218 policies); no ledger …" —
  `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:355-364` **[MEASURED]**
* The drift gate that would compare against a ledger is documented as unable to run:
  "| Ledger mode against a provisioned ledger | **not executed** — no ledger source provisioned
  (`MIGRATION_DRIFT_DATABASE_URL` absent from `backend/.env`) |" —
  `docs/architecture/CT-PO-CT-READINESS-01-MIGRATION-DRIFT-AND-CANONICAL-DB-BASELINE-AUDIT-20260927-REPORT.md:111` **[MEASURED]**
* By contrast **production's** history *is* CLI-managed: "Migration history was managed by the CLI
  against `supabase_migrations.schema_migrations`; the CLI records a version only after that migration's
  transaction commits … No `db reset`, no manual history insert, no bypass of migration tracking." —
  `docs/audit/cline/CT-FINAL03-P3-SUPABASE-001-20261003.md:209` **[DONE]**

**Summary of the documented position:** the absence of `supabase_migrations.schema_migrations` in the
two local databases is (a) *explained* as the consequence of building each database by direct
application / provisioner replay rather than by the Supabase CLI, (b) *not* described anywhere as
deprecated, and (c) *never* described as satisfying any stated requirement — for `postgres` the
documents explicitly record an approved-bootstrap recommendation that was not implemented.

---

## 3. Conflicts between documents

Reported, not resolved. Each item names both sides with its citation.

### 3.1 The Demo Lab's table count: 136 vs 141 vs 154

* `docs/architecture/CT-PO-P12-STEP2-ENVIRONMENT-PROVENANCE-20260924.md:31, 55` — "Public tables | 136"
  (pre-reset manifest) → "Public tables | **141**" (post-provision, same day) **[DONE]**.
* `docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md:36` — "Public tables | **141**" **[DONE]**.
* `docs/architecture/CT-PO-CARBONTALLY-FEATURE-DELTA-CHANGELOG-20261003.md:142-148` — "`carbontally_demo_local` | 141 | 141 | 0" **[MEASURED]**.
* `docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md:522` — "`carbontally_demo_local`'s applied
  position: its schema (154 tables / 355 policies) …" **[MEASURED]**, with
  `docs/architecture/CT-CARBONTALLY-FOUNDATION-INVENTORY-02.md:54` "**2** (135 and 154 public tables)".

**Nature of the conflict:** the earlier values (136/141) are Step-2 records dated 2026-09-24; the later
value (154) exists only in the 2026-10/11 foundation series. No document reconciles the two, and no
document states 154 as an expectation.

### 3.2 The Demo Lab's RLS policy count: 274 vs 298 vs 355

* 274 — `docs/architecture/CT-PO-P12-STEP2-ENVIRONMENT-PROVENANCE-20260924.md:35` (pre-reset) **[DONE]**
* 298 — `docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md:38` (post-provision,
  "canonical") and `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:227` **[DONE / MEASURED]**
* 355 — `docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md:522` **[MEASURED]**

### 3.3 The role label of `ct_local_93d5cdd` — mutually inconsistent descriptors

| Label | Citation |
| --- | --- |
| "The canonical repo's target" | `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:117` |
| "READINESS-02 / latest-repo local run" | `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:277` |
| "(disposable)" | `~/ct_local_env/README.md:34` (outside the repository; cited by the reconciliation report) |
| "Source/disposable baseline (schema reference)" | `docs/audit/costrict/CSTR-FINAL03-RLS-VERIFY-001-20261002.md:38` |
| "the local QA database (`ct_local_93d5cdd`)" | `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md:149` |
| "`ct_local_93d5cdd` (baseline clone)" | `docs/architecture/CT-PO-P17-L-CAPABILITY-TRUTH-SURFACE-20260926.md:804` |
| "not a demo environment at all" | `docs/architecture/CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924.md:483` |

The same census that labels the Demo Lab "the most modern **durable** schema"
(`CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md:268`) is contradicted six days later by an independent
reconciliation that calls the lab schema stale:

> "| 5 | RLS / schema | **Different revision** — lab schema is stale / assembled by `stack.py`
> (136–141 tables); prod = 150 tables, 98 migrations | `[documented]` |" — `docs/audit/costrict/CSTR-FINAL03-BLK2-DEMO-INVESTOR-RECON-001-20261003.md:233`

> "| N-2 | Demo Lab schema is a **stale revision** (no/partial Insight tables) vs production (150 tables,
> 98 migrations). | limits equivalence `[documented]` |" — same file, line 309

A related tension: the Step-2 canonical record claims schema completeness —

> "**The Step-1 schema gap is closed**: the environment carries the complete current release schema
> including all six `2026100*` Insight migrations." — `docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md:45-46` **[DONE]**

— whereas later reports state the lab had to receive newer migrations by hand because it predated them:

> "(`carbontally_demo_local`) was provisioned *before* the CT-04 migration existed" — `docs/architecture/CT-CONSULTANT-CLIENT-ACCESS-UX-01.md:197` **[DONE]**

Both statements may be true at their respective dates; the documents do not reconcile them.

### 3.4 "Nothing committed" vs the current Git state (20261028 / 20261029)

* The FINAL-03 implementation record states: "**No production contact; nothing deployed; nothing
  committed**; the accepted 43-table artefact is byte-for-byte unchanged." —
  `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md:251` **[DONE]**
* The current working tree shows those two files as **tracked** (`git ls-files` returns
  `supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql` and
  `supabase/migrations/20261029000000_ct_final_03_staff_workload_rls.sql`), while exactly five migration
  files are untracked — the `20261030`–`20261104` set.
* `docs/audit/cline/CT-FINAL03-P3-SUPABASE-001-20261003.md:209, 214-224` records production application
  of 27 migrations ending `20261029000000_ct_final_03_staff_workload_rls.sql` **[DONE]**.

**Nature of the conflict:** a 2026-10-02 statement of "nothing committed" versus a working tree in which
the two FINAL-03 RLS artefacts are tracked, and versus a record of production application of that set.
No document states when the commit occurred.

### 3.5 The 7,049 factor library — one survivor, or two?

* "| PO DECISION? | YES — reconcile first (only one factor library should survive into the canonical
  environment) |" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md:192` **[PLANNED]**
* Production is nevertheless instructed to **preserve** its own 7,049 and to refuse local import:
  "the **7,049 emission factors** (authoritative reference dataset) — verified row-for-row"
  (`docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md:47`) and "**no local demo data
  imported** … a local import shows 975 organisations and/or the `@demo.carbontally.local` domain, which
  must be **0**" (same file, lines 71-72) **[INTENDED]**
* Local-vs-live byte-identity is documented as **UNKNOWN**: "| Local vs live identity | **UNKNOWN — not
  verifiable here.** |" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:158` **[MEASURED]**

**Nature of the conflict:** the ledger states that a reconciliation decision is *required* between the
duplicate local libraries, while the cutover package treats production's copy as authoritative and
requires it to be preserved byte-for-byte. Which copy is to survive is not stated.

---

## 4. Silent areas

Questions the documents do **not** address (all stated as absences, not as negatives):

1. **No comparative size goal.** No document states that the Demo Lab should hold less data than any
   other database; the relationship is expressed as independence and non-interference (§Q1.3).
2. **No intended table count for the Demo Lab.** The documents record 141 (and later 154) as outcomes
   of schema completeness; no document states a target table count for it, and the frozen seed manifest
   contains no table count at all.
3. **No statement of which local database is authoritative over the other.** This is recorded as an
   *open question*, not an answer: "2. Which of the two 25-organisation datasets is the intended base
   for future work, and how do they relate to each other?" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:248`.
4. **No lifecycle intent for `ct_local_93d5cdd`.** No document states whether it is to be retained,
   promoted, or retired; it is not described as "schema-only" or "audit-only".
5. **No statement about committing the five migrations.** The documents state (i) that they exist
   untracked, and (ii) that each requires separate review before *application*; no document states
   whether they should be committed to Git, and none states a commit plan for them.
6. **No target factor count for `ct_local_93d5cdd`.** Every statement is a measured zero; no document
   states that it should hold 0, or that it should hold 7,049.
7. **No combined account of the missing ledger.** The absence is explained per database (and for
   `postgres` as a specific historical mechanism); no document states whether a ledger should exist for
   either local database, nor whether the absence is accepted as permanent.
8. **No documented expectation for the 154-table / 355-policy state.** It appears only as measurement in
   the Phase-1/2/3 foundation series.
9. **No documented intent for `emission_factors` version parity between environments.** Local-vs-local
   content identity is recorded; local-vs-live is explicitly UNKNOWN
   (`CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md:158`).
10. **No document states which database the demo-lab factor import should *not* have touched**, beyond
    the seeder guard's own refusal list (which names `ct_*` databases, including `ct_local_93d5cdd`).

---

## 5. Consequences for PD-E — what the documents do and do not imply

**Scope note:** this section reports *only* what the documentation implies. It takes no position on
whether any action should be taken; where the documents are silent, that is stated as silence.

### 5.1 The five migrations (`20261030`–`20261104`) and committing

**What the documents DO provide:**

1. **A recorded governance rule that separates ratification from application** — and that does not
   authorise production:

   > "* The **CT-MP-SUB-003 migrations are architecturally ratified *in principle***.
   > * **BUT each migration requires separate migration review** before being applied **to any environment
   > where it is not already applied**.
   > * This decision **does NOT authorize production migration or deployment.**" — `docs/architecture/CT-MP-SUB-004-PO-decision-record.md:328-330` **[PO DECISION]**

2. **A recorded release-discipline condition that a release must not depend on untracked files:**

   > "| **P2** | **The BACKUP-01/02 file set is committed** (FINAL-02 §16.7 / DR-20 handoff H6), so the
   > deployed commit *is* the reviewed artifact. | `git status --porcelain` shows none of those paths as
   > untracked/modified; the commit SHA is recorded | **STOP** — deploying an uncommitted tree is not a
   > frozen artifact |" — `docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md:68` **[INTENDED]**

   > "**1. Freeze the release and record the SHA.** … Expected: one clean commit SHA; tag created; the
   > BACKUP set no longer untracked. Evidence: SHA, tag, porcelain output. **STOP: any untracked file that
   > the release depends on.**" — same file, lines 129-133 **[INTENDED]**

3. **The only application target documented for these five files is the Demo Lab**
   (`carbontally_demo_local`), and it is documented as already applied there by two mechanisms (§Q6.2).

**What the documents do NOT provide:**

* No document states that the five **should** be committed, nor that they should **not** be.
* No document records an intent to ship them, a target release containing them, or a production review
  for them. The FINAL-03 production set (frozen 2026-10-02) contains their predecessors only, up to
  `20261029000000` (§Q6.3).
* No document places them in any environment other than the Demo Lab.

**Documented implication, stated as narrowly as the text allows:** the repository's own release
discipline requires that a release not depend on untracked files (P2/step 1 above), and its migration
governance requires separate review before application to any environment where a migration is not
already applied. The five files are documented as untracked, pre-existing, and applied only in the Demo
Lab. Whether to commit them is **not addressed by any document located in this search**.

*(Related negative observation: `AGENTS.md` §70 lists what must never be committed — "`.env` files,
credentials, API keys, passwords, JWTs, local demo credentials, signed URLs, generated secrets" — and
does not include migration files; no document in this search was found that addresses committing
migrations as a category.)*

### 5.2 Was `ct_local_93d5cdd` supposed to be seeded?

**What the documents DO provide:**

1. **A ratifying PO closure that makes the Demo Lab the only factor target and makes the guard
   binding:**

   > "4. The target guard remains mandatory: Demo Lab writes only, never `postgres`, `carbontally_test`,
   > `carbontally_qa_phase8`, `ct_*` clones, unnamed DSNs, or any production surface." — `docs/architecture/CARBONTALLY_PHASE8_DEMO_T2C_FACTOR_DATASET_LOADING_PO_CLOSURE_DECISION_20260920.md:116-117` **[PO DECISION]**

   with the guard itself documented as refusing `ct_*` databases
   (`tools/demo_lab/README.md:112-115`) and verified as such ("Target guard verified (writes refused
   unless the database is exactly `carbontally_demo_local`)", same file, line 55).

2. **A baseline that relies on `ct_local_93d5cdd` being pipeline-empty:**

   > "the canonical local DB (`ct_local_93d5cdd`) contains **no pipeline data** — `emission_factors=0`,
   > `suppliers=0`, `customer_documents=0`, `calculation_snapshots=0`, `emissions_logs=0`,
   > `evidence_line_items=0`, `report_versions=0`, `disclosure_requirement_versions=0`" — `docs/architecture/CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927.md:37` **[MEASURED]**

3. **An open, recorded reconciliation item about which factor library survives:**

   > "| PO DECISION? | YES — reconcile first (only one factor library should survive into the canonical
   > environment) |" — `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md:192` **[PLANNED]**

**What the documents do NOT provide:**

* No sentence was found stating "`ct_local_93d5cdd` must never be seeded" or "`ct_local_93d5cdd` should
  be seeded". The refusal of `ct_*` databases is documented as a **guard on the Demo Lab seeder**, and
  the zero-factor state of `ct_local_93d5cdd` is documented as a **measurement** and as the premise of a
  READINESS-02 baseline.
* No document states whether the Demo Lab's factor dataset should become the canonical library, or
  whether the pre-existing `postgres` library should feed any other database (the ledger records this as
  a decision still *required*).

---

## 6. Verdict

**DOCS SEARCH COMPLETE** — every one of the seven questions produced a documented answer with a file
path and line citation, or an explicit **NOT FOUND IN DOCS** statement supported by the search that was
performed. No question was left unaddressed, and no document was found ambiguous enough to prevent an
answer from being recorded; the ambiguities that do exist are recorded verbatim as conflicts (§3) rather
than resolved.

### 6.1 Register of NOT FOUND items

| Question | Item not found | Search evidence |
| --- | --- | --- |
| Q1 | A statement that the Demo Lab was intended to hold **less data than the original database** | no such statement; the relationship is documented only as independence/non-interference |
| Q1 | An intended **table count** for the Demo Lab | the Step-2 expected/actual table covers entities only; the frozen seed manifest has no table count |
| Q2 | Any intent for `ct_local_93d5cdd` to hold factors | every statement is 0; the seeder guard refuses `ct_*` |
| Q3 | A statement that either database was **derived from** the other | both are documented as independently built from the migration directory at different dates |
| Q3 | `ct_local_93d5cdd` intended as **schema-only** or **audit-only** | neither phrase is used; it is labelled six different ways (§3.3) |
| Q5 | The literal string **"150+ tables"** (or "160+") | absent from `docs/**` (930 md files), `tools/`, `backend/`, `scripts/`, `qa_harness/`, `AGENTS.md` |
| Q5 | An **expected** table count of 154 | 154 appears only as a Phase-1/2/3 measurement, never as an expectation |
| Q6 | Authorisation, plan or schedule for **production** application of the five | the frozen production set ends at `20261029000000`; the PO decision record states it "does NOT authorize production" |
| Q6 / §5.1 | A statement that the five migrations **should be committed** | not addressed in any located document |
| Q7 | Whether a **ledger should exist** for either local database | the absence is explained per database; no requirement is stated either way |

### 6.2 What the documentation *does* establish (one line each)

1. `carbontally_demo_local` was created as the canonical local Demo Lab, on the current release schema,
   with a deliberately narrow, frozen, role-bearing identity/relationship dataset, and the pre-existing
   databases were not to be altered.
2. `emission_factors` = **7,049** (7,029 DEFRA-2025 GB + 20 SEAI-2025 IE) is the documented factor
   population for the Demo Lab and for production; `ct_local_93d5cdd` and QA are documented at **0**; the
   Demo Lab seeder is documented and PO-ratified as refusing every other database, including `ct_*`.
3. The two local databases are documented as **siblings in one physical cluster**, built independently
   (2026-09-19 direct `psql` migration application → `ct_local_93d5cdd`; 2026-09-24 provisioner replay →
   `carbontally_demo_local`), not as parent/child.
4. RLS work is documented with three distinct targets: the P8 RLS group is **QA-only (production
   prohibited, G0-D)**; the FINAL-03 RLS pair was verified against `ct_local_93d5cdd` template clones;
   the Demo Lab was expected at **141/141 RLS-enabled**.
5. Documented table counts are 141 (Demo Lab, 2026-09/10), 135 (`ct_local_93d5cdd`), 116 (`postgres`),
   150 (production, expected), 145 (canonical rebuild); **154 appears only in the foundation series**;
   **"150+" appears nowhere**.
6. The five migrations' purposes are documented per file, their only documented application target is the
   Demo Lab, they are documented as untracked, and their application elsewhere requires separate review
   (PO decision) with no production authorisation.
7. The missing migration ledger is documented as a consequence of how each database was built (restore +
   direct application + provisioner replay), with an approved-bootstrap recommendation for `postgres`
   recorded as **not implemented**, and a per-database ledger column classifying it as a normal
   per-environment property rather than a defect.

---

## 7. Sources, method limits and safety

### 7.1 Principal sources read (beyond grep hit lines)

* `tools/demo_lab/README.md` (321 lines; §§1-8 read)
* `docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md` (96 lines)
* `docs/architecture/CT-PO-P12-STEP2-ENVIRONMENT-PROVENANCE-20260924.md` (96 lines)
* `docs/architecture/CT-PO-P12-STEP2-EXPECTED-COUNT-VERIFICATION-20260924.md` (78 lines)
* `docs/architecture/CT-PO-P12-STEP2-FROZEN-SEED-MANIFEST-20260924.md` (104 lines)
* `docs/architecture/CARBONTALLY_PHASE8_DEMO_T2C_FACTOR_DATASET_LOADING_PO_CLOSURE_DECISION_20260920.md` (full)
* `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md` (§§4-7 and the per-database sections)
* `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md` (§§5-15, incl. §6 provenance and §15 mandatory answers)
* `docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md` (§§2-5)
* `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md` (full); `CARBONTALLY_DEVELOPMENT_DATABASE_BACKUP_REPORT.md` (§1); `CARBONTALLY_MIGRATION_APPLICATION_REPORT.md` (§§1-4)
* `docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md` (§§1-2 and steps 4-12)
* `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/README.md` (§§6, 10 and the index)
* `docs/audit/costrict/CSTR-CARBONTALLY-ENVIRONMENT-RECON-001-20261003.md` (§§1-3); `CSTR-FINAL03-RLS-VERIFY-001-20261002.md`; `CSTR-FINAL03-BLK2-DEMO-INVESTOR-RECON-001-20261003.md`
* `docs/architecture/CT-MP-SUB-004-PO-decision-record.md` (§ "the three migrations in scope")
* `docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md` (§§7-8)
* `docs/architecture/CT-CONSULTANT-CLIENT-IDENTITY-04.md`; `CT-CONSULTANT-CLIENT-ACCESS-UX-01.md`; `CT-CONSULTANT-MODEL-IMPLEMENTATION-02.md` (relevant sections)
* `docs/architecture/CT-PO-P12-INVESTOR-DEMO-READINESS-PREFLIGHT-20260923.md`; `CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924.md`; `CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY-20260924.md`; `CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md`; `CT-PO-CARBONTALLY-SCHEMA-COMPARISON-MATRIX-20260927.md`; `CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927.md`; `CT-PO-CARBONTALLY-FEATURE-DELTA-CHANGELOG-20261003.md`
* The five migration headers in `supabase/migrations/` (the first 18-32 lines of each)

### 7.2 Supplementary sources, explicitly flagged

* `Research/CT-PO-DEMO-LAB-PERSISTENCE-01/CT-PO-DEMO-LAB-PERSISTENCE-01.md` — **untracked working-tree
  material outside `docs/`**, consulted only for the Demo Lab's runtime topology and restart policy
  (lines 44-68). It contains no statement about database intent beyond confirming the same topology as
  `tools/demo_lab/README.md`.
* `~/ct_local_env/README.md` — **outside the repository**; read only for the `ct_local_93d5cdd`
  identity text that repository documents cite by name and line.

### 7.3 Method limits

* This was a **grep-directed** search over a 930-file documentation corpus; only passages answering the
  seven questions were read. A document that never names either database, `emission_factors`,
  `schema_migrations` or a migration timestamp could not have been reached by this method.
* Every database-state figure quoted in this report is a **document's own measurement**, restated with
  its citation. **This task made no database query**, read no database, and ran no migration or seed.
* Where documents conflict, this report quotes both sides and has **not** adjudicated (§3).
* Statements are labelled by what the *document* asserts, not by whether the assertion is operationally
  true in the current runtime (that comparison belongs to the separate verification pass).

### 7.4 Safety statement

* Repository changes produced by this task: **one new file** — this report
  (`docs/architecture/CT-CARBONTALLY-FOUNDATION-DOCS-INTENT-04.md`).
* No migration, seed, DDL/DML, RLS, configuration, `.env` or application-code change.
* No Git history operation; HEAD unchanged at `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`.
* No credentials, tokens, signed URLs or secrets were read, printed or stored; no production system was
  contacted.

---

End of CT-CARBONTALLY-FOUNDATION-DOCS-INTENT-04.
