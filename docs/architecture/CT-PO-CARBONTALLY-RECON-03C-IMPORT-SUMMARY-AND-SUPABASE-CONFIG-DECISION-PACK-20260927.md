# CT-PO — CARBONTALLY RECON-03C — `import_summary.md` + `supabase/config.toml` DECISION PACK

- **Task ID:** `CT-RECON-03C-20260927-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK`
- **Type:** READ-ONLY FORENSIC / DECISION SUPPORT (no product or configuration decision taken)
- **Date:** 2026-09-27
- **Predecessor:** `CT-PO-CARBONTALLY-HISTORICAL-32-FILE-TECHNICAL-RECONCILIATION-20260926.md`
  (CT-RECON-03B) — which left exactly two items open: **HIST-30** (`output/reports/import_summary.md`)
  and **HIST-32** (`supabase/config.toml`).
- **Companion:** `CT-PO-CARBONTALLY-RECON-03C-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK-20260927-REPORT.md`

## Control baseline (locked before any measurement)

| Repository | Path | Branch | HEAD |
|---|---|---|---|
| Historical | `/home/shomonrobie/carbon_tally` | `main` | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` (2026-09-16, `fix(frontend): retire legacy onboarding…`) |
| Canonical | `/home/shomonrobie/ct_93d5cdd` | `p8-release-reconciled` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (2026-09-26, `fix(public-truth): build provenance…`) |

Porcelain counts at baseline: historical **305** entries; canonical **32** entries (30 pre-existing + 2
untracked 03B documents). **Both baseline commits `2d23fb8` and `eed55d6` are ancestors of BOTH HEADs**
(`merge-base --is-ancestor` = YES ×4) — the two repositories share history, so their `HEAD` blobs for both
files under investigation are byte-identical. This matters: the differences found below are
**working-tree** differences, not divergent commits.

## Truth-standard legend (used throughout)

`DOCUMENTED` (a document asserts it) · `CODE EXISTS` (source present) · `CONFIGURED` (declared in a config
file) · `TEST EXPECTED` (asserted by a test) · `MIGRATION PRESENT` · `DATABASE NOT ACCESSED` (no DB
connection was made in this task) · `RUNTIME-OBSERVED` (read-only Docker/socket inspection of what is
actually running now) · `GIT-OBSERVED` (object-level Git measurement).

Nothing below conflates these. In particular: **TEST HARNESS EXPECTATION ≠ SUPABASE CONFIGURATION ≠
ACTUAL RUNNING SERVICE**, and no claim is made that a database contains 7,029 factors.

---

## 1. Executive summary

1. **The generator of the historical `import_summary.md` EXISTS in canonical.** The CT-RECON-03B item
   ("no generator for this path exists anywhere in canonical") is **incorrect for the current canonical
   tree**. The generator is `src/commands/import_defra.py` (288 lines) →
   `src/providers/defra/exporter.py:250 write_summary()`, whose docstring is literally
   *"Write `output/reports/import_summary.md` (the final report)"*, and the path is asserted by the
   canonical regression test `src/providers/defra/tests/test_import_provenance.py:389`. The earlier search
   failed because it looked for the *filename literal* `import_summary` in code, whereas the filename is
   constructed inside `write_summary` (`report_dir / "import_summary.md"`).
2. **The report is reproducible, not mysterious.** The historical report records a workbook SHA-256
   `8bfdb45b81ec4a88e3bdf4584637330f62e6bd09ce1940e654c5d7b7f736de94`; that exact byte-identical workbook
   is **tracked in canonical** at `tools/carbon_data_factory/docs/ghg-conversion-factors-2025-flat-format.xlsx`
   (plus a second copy under `tools/carbon_data_factory/factors/`). The same hash is hard-coded in the
   canonical Demo-Lab seeder `tools/demo_lab/seed_factors.py` together with `imported: 7029`,
   `skipped: 1711`, `factor_set: DEFRA-2025`, `factor_source: DEFRA-DESNZ`, `country: GB`.
3. **The committed report is the odd one out.** The version committed in *both* repositories
   (blob `4d2b2b38`, added by `2d23fb8`) uses an **older export format** (`# Import Summary` +
   `Configuration` table, `no_db = True`, log `…20260806_051222.log`) that the current canonical exporter
   no longer produces. The historical **working-tree** version (blob `f0193b5c`, 2026-08-15) matches the
   **current** canonical exporter format exactly and is the only copy carrying the `## Database load`
   section (`psycopg2`, inserted 7029, updated 0).
4. **The 2026-08-15 report is not lost if the file is deleted.** Its blob is reachable from a durable ref
   in the historical repository (`refs/cline/checkpoints/1790426195384_kpifz/5` → commit `f30b51b`):
   `git show f30b51b:output/reports/import_summary.md | sha256sum` = `81916d76…` = the worktree hash.
   Content loss risk is therefore LOW; the real exposure is *discoverability* (it lives in agent
   checkpoint refs, not in branch history).

5. **The 5442x port family is not a test artefact.** It is (a) the port family declared by the
   **historical working-tree** `supabase/config.toml` (an uncommitted local edit), (b) the family expected
   by canonical tests/harness/`.env` (43 lines across 20 executable files), and (c) **the family of the
   stack actually running now** — `docker ps` shows `supabase_kong_carbon_ledger` publishing
   `0.0.0.0:54425->8000`, `supabase_db_carbon_ledger` `0.0.0.0:54426->5432`,
   `supabase_studio_carbon_ledger` `54423->3000`, and both carry the label
   `com.supabase.cli.workdir:/home/shomonrobie/carbon_tally`.
6. **Canonical `supabase/config.toml` (54325/54326/…, `[db.migrations] enabled = true`) therefore describes
   neither the running stack nor the harness expectation.** The exact canonical↔historical-worktree diff is
   **7 hunks** (six ports + the migrations flag). Two references were **left un-remapped** in the historical
   edit (`[studio] api_url = http://localhost:54325`, `[analytics] port = 54327`) — an incompleteness the
   parallel e2e remap (553xx, project `carbontally_e2e`) did **not** have.
7. **Neither file can affect production.** `supabase/config.toml` is the local Supabase CLI project file;
   no deployment artefact references it (`vercel.json` holds only frontend rewrites/security headers and
   points at `https://*.supabase.co` / `https://carbontally-api.onrender.com`; there is no `render.yaml`;
   canonical CI `.github/workflows/migration-drift.yml` uses neither the CLI nor the flag).
8. **One engineering risk worth the PO's attention (not fixed here):** the canonical and historical
   directories declare the **same Supabase `project_id = "carbon_ledger"`** while declaring **different**
   host ports. Because the CLI derives its Docker Compose project from `project_id`, `supabase start` in
   *either* directory targets the *same* container set — a `supabase start`/`stop` in the canonical clone
   can silently rebind ports out from under tests that hard-code 54425/54426.
9. **Classification, Part A:** `MIXED` — predominantly `HISTORICAL_GENERATED_ARTIFACT`, containing genuine
   `AUDIT_EVIDENCE` (the only record of the 2026-08-15 *database load*) with key facts
   `DUPLICATED_INFORMATION` elsewhere in canonical.
10. **Part B classification:** local-environment configuration, **not** product configuration
    (`DOCUMENTED` as such by canonical's own release docs). `NEEDS_REVIEW` remains the accurate state for
    the *working-tree vs canonical* discrepancy; **PO decision required**.
11. No product, source, configuration, migration, database or deployment change was made by this task.

---

## 2. Historical `output/reports/import_summary.md` analysis (A1, A3, A4)

### A1 — exact contents and metadata (historical working tree)

| Property | Value | Provenance |
|---|---|---|
| Path | `/home/shomonrobie/carbon_tally/output/reports/import_summary.md` | OBSERVED |
| Size / lines | 1,164 bytes / 55 lines | OBSERVED |
| Mode | `-rwxr-xr-x` (0755) | OBSERVED |
| mtime | `2026-08-15 13:13:20 +0600` | OBSERVED |
| ctime / birth | `2026-08-20 12:50:56 +0600` | OBSERVED |
| SHA-256 | `81916d76be7b746372c35a6f68a181e6f80a5c307899e97682db507a03f35a52` | OBSERVED |
| Git blob | `f0193b5cffaf80724fe753ddd3134671839751f5` | GIT-OBSERVED |
| Git state | **tracked**, modified vs `HEAD` (` M`) | GIT-OBSERVED |
| Diff vs `HEAD` | 1 file changed, **55 insertions(+), 35 deletions(-)** | GIT-OBSERVED |

Content (structure, verbatim headings and figures):

```
# CarbonTally — DEFRA Import Summary
- Generated: 2026-08-15T00:13:20
- Execution time: 6m 50.0s
- Workbook: `D:\carbon_ledger\tools\carbon_data_factory\docs\ghg-conversion-factors-2025-flat-format.xlsx`
- SHA-256: `8bfdb45b81ec4a88e3bdf4584637330f62e6bd09ce1940e654c5d7b7f736de94`
- Reporting year: 2025
- Factor set: `DEFRA-2025`
## Sheets  processed 2 | data 1 | documentation 1 | unsupported 0
## Rows    scanned 8742 | parsed 8740 | blank 1 | end markers 1 | with DEFRA ID 8740 | factor value 7029
## Outcome **Rows imported 7029** | skipped 1711 | duplicates 0 | warnings 0 | errors 0
## Skipped rows by reason   `no_factor_value` 1711
## Database load  backend `psycopg2` | mode `sync` | inserted `7029` | updated `0` |
                 deleted_before_insert `0` | total_processed `7029`
```

**Note the `## Database load` block.** In the canonical exporter that section is emitted **only when
`result.db` is set** (`src/providers/defra/exporter.py:72`), i.e. only for a run performed **without**
`--no-db`. This file is therefore the record of a **real database load**, not a dry run.

### A3/A4 — Git history of this path (both repositories)

| Measurement | Historical | Canonical |
|---|---|---|
| `git log --follow -- <path>` (branch) | **2 commits**: `eed55d6`, `2d23fb8` | **2 commits**: `eed55d6`, `2d23fb8` |
| Adding commit (`--diff-filter=A`) | `2d23fb8` — 2026-08-06, `CarbonTally RC2 Final database baseline` | `2d23fb8` — same |
| Deleting commits | none | none |
| Commit metadata | `2d23fb8` = `2d23fb892921cbc41d6c0c20b7660e86fc968178`, **2026-08-06 06:42:42 -0700**, author `shomonrobie`, parent `a054991` | `eed55d6` = `eed55d62ee9f103279d0d2a94006952a517d3bde`, **same timestamp/message**, parent `00cff1d` |
| Commits touching the path with `--all` | **554** (552 are Cline-session **checkpoint merge commits**, i.e. agent stash-style snapshots) | 2 |

`2d23fb8` is **not** an ancestor of `eed55d6` (`merge-base --is-ancestor` = NO): they are two parallel
"RC2 Final database baseline" commits with identical content for this path, both of which are ancestors of
**both** current HEADs. This is why the `HEAD` blob is identical on both sides.

### Distinct content versions of this path (GIT-OBSERVED)

All distinct blobs of `output/reports/import_summary.md` reachable from any ref in the historical repo
(`rev-list --all --objects` matched each exactly once → **all five are reachable, none is dangling**):

| Blob | Content SHA-256 | What it is | Where it lives |
|---|---|---|---|
| `4d2b2b38` | `8babb331…` | 2026-08-06 05:12:27 run (`no_db=True`, old format) | commit trees `2d23fb8`, `eed55d6`, `5f4c361`; **canonical HEAD + worktree** |
| `f0193b5c` | `81916d76…` | **2026-08-15 run with real DB load** (new format) | **not** in `2d23fb8`/`eed55d6`; present in Cline checkpoint commit trees, e.g. `f30b51b`, and in the historical **worktree** |
| `0a23a543` | `dde3d584…` | further historical variant(s) of the same path | reachable from checkpoint lineage |
| `9c28f5fc` | `06efa1a7…` | further historical variant(s) of the same path | reachable from checkpoint lineage |
| `d42f28a6` | `a267940a…` | further historical variant(s) of the same path | reachable from checkpoint lineage |

Method notes: `git log --all --find-object=<blob>` returned no rows for the four non-baseline blobs because
their holders are **merge (checkpoint) commits**, which `git log` simplifies away by default — even with
`--full-history`. The blob→commit mapping above was therefore established by resolving `<commit>:<path>`
for every one of the 554 commits in which the path appears; that is the reliable method here.
`git cat-file -e f0193b5c…` = **EXISTS**, and
`git show f30b51b:output/reports/import_summary.md | sha256sum` = `81916d76…` (byte-identical copy).

**Recovery ref:** `f30b51b` is contained in exactly one ref —
`refs/cline/checkpoints/1790426195384_kpifz/5` (an agent-session checkpoint ref, **not** a branch) — and is
**not** an ancestor of `main`. Consequence: the 2026-08-15 run record is recoverable *today*, but it is not
part of published branch history and will not travel with a normal clone/fetch of `main`.

---

## 3. Canonical `output/reports/import_summary.md` analysis (A2)

| Property | Value | Provenance |
|---|---|---|
| Path | `/home/shomonrobie/ct_93d5cdd/output/reports/import_summary.md` | OBSERVED |
| Size / lines | 835 bytes / 34 lines | OBSERVED |
| Mode | `-rw-rw-r--` (0664) | OBSERVED |
| mtime | `2026-09-19 18:44:21 +0600` (= clone timestamp of the whole canonical tree) | OBSERVED |
| SHA-256 | `8babb3310cf40963fa518ff851c96b4a3f7c7cce13dcc2709c1a49a8307afc34` | OBSERVED |
| Git blob | `4d2b2b38561a43555cc581023dd8f517e80df0ae` | GIT-OBSERVED |
| Git state | **tracked, clean** — identical to `HEAD` (`git status --porcelain` empty) | GIT-OBSERVED |
| History | added `2d23fb8`, touched again by `eed55d6` (both ancestors of canonical HEAD) | GIT-OBSERVED |

Content summary: `# Import Summary`; `Generated: 2026-08-06T05:12:27`; a `## Configuration` table
(`workbook`, `reporting_year 2025`, `mode sync`, **`no_db True`**, `factor_source DEFRA-DESNZ`,
`factor_set DEFRA-2025`, `country GB`, `output_dir D:\carbon_ledger\output`,
`log_file D:\carbon_ledger\output\logs\import_defra_20260806_051222.log`); a `## Statistics` table
(`rows_scanned 8742`, `rows_parsed 8740`, `empty_rows 1`, `end_marker_rows 1`, `rows_with_id 8740`,
`factors_with_value 7029`, `skipped_no_factor 1711`, `duplicates 0`, `imported 7029`). **There is no
`## Database load` section** and the configuration explicitly records `no_db = True` → this is a
**validation/dry run**, produced ~15 hours before the historical working-tree run.

The committed format (`# Import Summary` + `Configuration`) is **not** the format produced by the current
canonical exporter (see §5), so the committed file is a **stale-format artefact of an older exporter
revision** that has been retained in the tree.

---

## 4. Import-summary lineage

Single path, two parallel baselines, five content versions, one *newer* version uncommitted:

```
2026-08-06 05:12:27  run with no_db=True (old format)            -> blob 4d2b2b38
2026-08-06 06:42:42  2d23fb8 (parent a054991) ADD <path>          [ = 4d2b2b38 ]
2026-08-06 06:42:42  eed55d6 (parent 00cff1d) ADD same path/message/blob [ = 4d2b2b38 ]
2026-08-15 00:06:30→00:13:20  real run, --no-db absent (DB load)  -> blob f0193b5c
                     log: output/logs/import_defra_20260815_000630.log (untracked)
                     report mtime 2026-08-15 13:13:20 (+0600)
2026-09-25..09-27    Cline checkpoint commits capture the worktree -> f0193b5c reachable
                     (e.g. f30b51b, refs/cline/checkpoints/…), never merged into main
2026-09-26  cb70fd6  canonical HEAD: worktree digest == HEAD digest for this path (clean)
```

Interpretation: `import_summary.md` is a **per-run output artefact** that was force-included in the
"RC2 Final database baseline" commits. Later runs overwrote it locally without committing; the agent
checkpoint mechanism incidentally preserved the newer content. The canonical clone carries the committed
(older) version because that is what `HEAD` contains. **This is a duplicated-information situation, not a
fork**: there is no competing lineage — only a committed snapshot plus a newer local run record.

### Untracked companions of the historical run (historical tree only)

`git ls-files output` in the historical repo returns **exactly one file** — `output/reports/import_summary.md`.
Everything else under `output/` is untracked local output (`output/` is **not** gitignored; only `*.log` is
ignored, via `.gitignore:25`):

| Artefact | Size | Notes |
|---|---|---|
| `output/sql/emission_factors.sql` | 5,707,634 B | header: `CarbonTally — DEFRA 2025 emission factors import (idempotent)`, target `public.emission_factors`, factor set `DEFRA-2025`, source `DEFRA-DESNZ`; **7,029 INSERT statements** (counted with `grep -c 'INSERT INTO'`) |
| `output/json/emission_factors.json` | 7,825,684 B | JSON export of the same run |
| `output/reports/import_statistics.json` | 658,729 B | machine-readable statistics (same generator) |
| `output/logs/import_defra_*.log` | 9 files, 1,854–1,944 B | run logs, 2026-08-06 … 2026-08-15 |
| `output/seai_2025/{sql,json,reports}` | 14,431 B / 37,502 B / 1,431 B + 667 B | SEAI 2025 artefacts incl. `import_summary_seai_2025.md` |

Canonical contains **none** of these (canonical `output/` holds only `reports/import_summary.md`).

---

## 5. Import-summary generator investigation (A6, A7)

### 5.1 The generator exists in canonical (CODE EXISTS) — 03B's "no generator" statement is superseded

| Element | Evidence |
|---|---|
| CLI | `src/commands/import_defra.py` (288 lines, tracked; last touched by `b4e02f4 feat(DEMO-T2): add DEFRA import provenance`) |
| Usage (module docstring) | `python -m src.commands.import_defra --no-db` (artefacts only) or without the flag (artefacts + DB sync) |
| Report writer | `src/providers/defra/exporter.py:250 write_summary()` — docstring *"Write `output/reports/import_summary.md` (the final report)"*; `path = report_dir / "import_summary.md"` |
| Statistics writer | `src/providers/defra/exporter.py:324 write_statistics()` → `output/reports/import_statistics.json` |
| Other writers | `write_sql()`, `write_json()` → `output/sql/…`, `output/json/…` |
| Header produced | `"# CarbonTally — DEFRA Import Summary"` — **identical to the historical 2026-08-15 file's first line** |
| DB-load section | emitted only `if result.db:` → present in the historical file, absent in the committed one |
| Default workbook | `DEFAULT_WORKBOOK = tools/carbon_data_factory/docs/ghg-conversion-factors-2025-flat-format.xlsx` |
| Default output root | `DEFAULT_OUTPUT = <repo>/output` |
| DB URL env names | `DATABASE_URL`, `SUPABASE_DB_URL`, `POSTGRES_URL` |
| Regression test | `src/providers/defra/tests/test_import_provenance.py:389` → `assert (tmp_path / "reports" / "import_summary.md").exists()`; `EXPECTED_DEFRA_2025_FACTORS = 7029`; imports `workbook_sha256` |
| Seeder/orchestrator | `tools/demo_lab/seed_factors.py` — explicitly *not* a second importer: it invokes `src.commands.import_defra` then `import_seai` in `sync` mode; expected DEFRA metadata contains `factor_source DEFRA-DESNZ`, `factor_set DEFRA-2025`, `country GB`, `imported 7029`, `skipped 1711`, `duplicates 0`, **`sha256 8bfdb45b…`** |
| Workbook present | canonical `tools/carbon_data_factory/docs/ghg-conversion-factors-2025-flat-format.xlsx` (tracked) and `tools/carbon_data_factory/factors/…` — **both SHA-256 `8bfdb45b…`, byte-identical to the hash the historical report records** |
| Historical repo | also contains `src/commands/import_defra.py` + `src/providers/defra/` (Aug-06 revisions) |

The historical run log names the producing modules and the original Windows build path: logger
`defra_importer`, module `src.providers.defra.exporter`, workbook
`D:\carbon_ledger\tools\carbon_data_factory\docs\ghg-conversion-factors-2025-flat-format.xlsx`; it ends with
`DONE — sheets=2 imported=7029 skipped=1711 duplicates=0 warnings=0 errors=0 elapsed=409951ms`, preceded by
`Database load complete (psycopg2): 7029 inserted, 0 updated`.

**Reproducibility conclusion:** the historical report is reproducible *content-wise* from canonical
artefacts — the generator (`src/commands/import_defra.py` + `src/providers/defra/exporter.py`), the exact
workbook (hash-verified and tracked) and the expected statistics (7029 / 1711 / 0 / 0) are all present in
canonical. What is **not** reproducible is the *DB-load result of that specific run* without running the
importer against a database.

### 5.2 A6 — repository-wide references (canonical)

| Reference | Type | Reads the file? |
|---|---|---|
| `docs/audit/cline/CARBONTALLY_V3_PLATFORM_FINALIZATION_REPORT.md:213,248` | documentation citing it as the 2026-08-15 run record and naming the two idempotent SQL seeds | No (cites) |
| 03A/03B reconciliation docs (`docs/architecture/CT-PO-…-20260926*.md`) | reconciliation records | No (cite) |
| `docs/cline/CarbonTally-SEAI-Provider-Implementation-v1.0.md:85` | cites the **SEAI sibling** path `output/seai_2025/reports/import_summary_seai_2025.md` | No |
| `docs/cline/prompt-history/CT-PROD-PUBLICATION-STAGING-PREP-20260911-001.md:413` | cites `output/json/import_summary.json` | No |
| `src/providers/defra/tests/test_import_provenance.py:389` | asserts the file is *generated* into a tmp dir | Generates only |
| Any code that **reads** the repo's `output/reports/import_summary.md` | **none found** | — |
| `qa_harness/**`, `backend/**`, `.github/workflows/**` referencing it | **none found** | — |

Concept-level searches confirm the same picture: `carbon_data_factory`, `no_factor_value`,
`workbook_analysis`, `rows_with_id`, `rows_scanned` appear in canonical **only** in the importer/exporter
code, its tests, and its docs — never as a reader of the historical artefact.

---

## 6. Import-summary information uniqueness analysis (A8, A9, A10)

### A8 — is the described factor dataset represented in canonical schema/migrations/database?

| Question | Finding | Provenance |
|---|---|---|
| Do canonical migrations contain emission-factor **rows**? | **No.** 89 migrations exist; those mentioning `emission_factors` are schema/RLS/verification only (`00000000000000_init_schema.sql`, `20260800000000_rc2_schema.sql` adds `factor_set`, `20260807010000_add_emission_factors_import_batch.sql`, `20260807020000_add_calculation_snapshots.sql`, RLS migrations, `20260926000000_p8_d4_emission_factors_internal_containment.sql`, …). No data seed of 7,029 rows. | MIGRATION PRESENT (schema only) / negative finding |
| Is there a seed mechanism? | **No.** `supabase/seeds/` does not exist; `[db.seed] enabled = false`, `sql_paths = []`. | CONFIGURED |
| Is the factor set represented elsewhere? | The historical tree holds the load artefact `output/sql/emission_factors.sql` (7,029 idempotent INSERTs; **untracked**, **absent from canonical**). Canonical references the factor set only via the importer CLI, the Demo-Lab seeder, expected-metadata constants and tests. | OBSERVED |
| Is the live dataset verified? | **DATABASE NOT ACCESSED** in this task (the mandate forbids DB connections). Recorded elsewhere: canonical `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md` §6 states the current dataset is **7,049 rows** (DEFRA-2025 = 7,029 + SEAI-2025 = 20) — `DOCUMENTED`, **not re-verified here**. Canonical `src/providers/defra/tests/test_import_provenance.py` asserts `EXPECTED_DEFRA_2025_FACTORS = 7029` against a database — `TEST EXPECTED`. | DOCUMENTED / TEST EXPECTED |

This reproduces the earlier `CARBONTALLY_PRODUCTION_DEPLOYMENT_READINESS_20260911.md` DR-02 finding
(factor reference data not reachable from a clean Release-1 deployment path): the *dataset* is still not
represented by any repository migration/seed — a fact **independent of** the fate of the report file.

### A9 — what is unique to the historical artefact, and what is duplicated?

| Fact in the historical report | Duplicated elsewhere? | Where |
|---|---|---|
| Workbook path + **SHA-256 `8bfdb45b…`** | **Yes** | canonical tracked workbook(s), byte-identical hash; `tools/demo_lab/seed_factors.py` hard-codes it |
| Factor set `DEFRA-2025`, source `DEFRA-DESNZ`, country `GB`, year 2025 | **Yes** | canonical schema/tests/docs, seeder, `factor_set` column semantics |
| imported **7029**, skipped **1711**, duplicates 0, warnings 0, errors 0 | **Yes** | committed canonical copy of the report; `seed_factors.py` expected metadata; `EXPECTED_DEFRA_2025_FACTORS` test |
| Sheet/row statistics (2 sheets; 8742 scanned; 8740 parsed; 1 blank; 1 end marker; 8740 with ID; 1,711 `no_factor_value`) | **Partly** | committed canonical copy carries the same figures in the older format |
| **`## Database load` block: psycopg2 / sync / inserted 7029 / updated 0 / deleted_before_insert 0 / total_processed 7029** | **No** | **unique to the historical working-tree file** |
| Execution time (6 m 50.0 s ≈ 409,951 ms) and timestamp (`2026-08-15T00:13:20`) | **No** | unique (the run log also records it, but that log is untracked and historical-only) |
| Local run environment (`D:\carbon_ledger\output`, log filename) | **No** | unique (same caveat) |

### A10 — what would be lost by deleting the historical file?

- **Product functionality: nothing.** No code reads it; no test asserts its repo-root presence; the report
  path is produced at *runtime* by `write_summary()`, so its absence cannot break any workflow.
- **Audit/provenance evidence: a specific, un-duplicated record** — that on 2026-08-15 the DEFRA-2025 factor
  set was loaded into a database by the importer (`psycopg2`, 7,029 inserted, 0 updated), with the workbook
  hash. That is the closest thing to a *provenance receipt* for the factor population the platform relies
  on, and it is **not** reproduced by the committed (dry-run) copy.
- **Reproducibility evidence: largely preserved** — generator + workbook + expected statistics all exist in
  canonical, so the run can be re-performed; the *historical execution* is attested by this file (and by
  the untracked log and recoverable blob `f0193b5c`).
- **Discoverability: partially at risk** — outside the worktree copy the content survives only in an agent
  checkpoint ref in the *historical* repository; canonical holds no blob, no commit and no documentation of
  the DB-load block.

### Classification (Part A — final)

**`MIXED`**, composed of:

1. `HISTORICAL_GENERATED_ARTIFACT` — machine-generated by `src/commands/import_defra.py` →
   `write_summary()`; overwritten on every run; path asserted by a test; not hand-authored;
2. `AUDIT_EVIDENCE` — the `## Database load` block and execution record are unique provenance evidence for
   the 2026-08-15 factor load;
3. `DUPLICATED_INFORMATION` — workbook hash, factor-set identity and all counter values are duplicated in
   canonical tooling, the committed report, and canonical tests.

It is **not** `DURABLE_PRODUCT_DOCUMENT` (a run output, not a maintained document) and not `OBSOLETE` (its
unique evidence has no replacement). The 03B verdict `NEEDS_REVIEW` is hereby **resolved** into `MIXED`;
the *disposition* remains the PO's call.

---

## 7. Supabase `config.toml` — exact diff (Part B)

Both files are **410 lines**, both are **tracked**, and both were last committed by `2d23fb8`
(2026-08-06) with the **same HEAD blob** `938b920b746dc03c2dda794fc2a2cc2df290e50e`
(SHA-256 `f9b1207b5f86a42f9b00e9354678e929749eea927cb8427fc4623c1a0351e9b2`).

The two repositories differ **only in the working tree**:

| Repository | `git status --porcelain -- supabase/config.toml` | Worktree blob | Worktree SHA-256 |
|---|---|---|---|
| Historical | ` M` (modified, **uncommitted**) | `bca4ef4bce3629d27d9ce461ab304c90574763b3` | `a8bc925634d3067f47cb27987282f9d0812a29685b21c7809c022e827b5643a9` |
| Canonical | *(empty — clean)* | `938b920b746dc03c2dda794fc2a2cc2df290e50e` | `f9b1207b…` (= HEAD) |

`diff -u <historical> <canonical>` yields **exactly 7 hunks**:

| # | Section | Line | Historical worktree | Canonical (= both HEADs) |
|---|---|---|---|---|
| 1 | `[api] port` | 9 | **54425** | 54325 |
| 2 | `[db] port` | 24 | **54426** | 54326 |
| 3 | `[db] shadow_port` | 26 | **54420** | 54320 |
| 4 | `[db.pooler] port` | 41 | **54429** | 54329 |
| 5 | `[db.migrations] enabled` | 55 | **false** | true |
| 6 | `[studio] port` | 123 | **54423** | 54323 |
| 7 | `[local_smtp] port` | 135 | **54424** | 54324 |

**Deliberately unchanged — and therefore *internally inconsistent* in the historical 5442x variant:**

| Section | Line | Value in BOTH files | Consequence in the historical variant |
|---|---|---|---|
| `[studio] api_url` | 126 | `http://localhost:54325` | Studio would target the canonical API port while the API listens on **54425** |
| `[analytics] port` | 386 | `54327` | analytics left in the 5432x family |
| `[edge_runtime] inspector_port` | 377 | `8083` | inspector left un-remapped |
| `[db.seed]` | 60-66 | `enabled = false`, `sql_paths = []` | identical in both |
| `[api.tls]`, `[db.pooler].enabled`, `[auth]*`, `[storage]*`, `[realtime]`, `[experimental.pgdelta]` | various | identical text | identical behaviour |

(`project_id = "carbon_ledger"` is identical in both files — see the risk note in §9.4 and §11.)

**Comparison with the third, *complete* remap already in canonical.**
`e2e/environment/supabase/config.toml` (`project_id = "carbontally_e2e"`) remaps the family to 553xx **and**
performs the two jobs the historical edit missed: `[studio] api_url = http://localhost:55325`,
`[analytics] port = 55327`, plus `inspector_port = 8183`. Its `[db.migrations] enabled = true` (it does
**not** carry the historical `false`). Canonical
`docs/cline/prompt-history/CT-P6-2F-ENV-IMPL-20260911-001.md:123` records how that copy was made:
`cp supabase/config.toml e2e/environment/supabase/config.toml  # then remap ports 544xx → 553xx` — direct
in-repo evidence that the **544xx family was the operative local configuration at that time**, and that
the e2e variant was derived *from it*.

### Other canonical documents that speak to this exact diff (DOCUMENTED)

| Document / line | Statement |
|---|---|
| `docs/cline/prompt-history/CT-PROD-PUBLICATION-RECON-20260911-001.md:154,352` | the diff is "local development port remap only (54325→54425, 54326→54426, 54320→54420) — environment-specific, not product config"; disposition **EXCLUDE** |
| `docs/audit/cline/CARBONTALLY_V3_D20_D37_GIT_RELEASE_PREPARATION_REPORT.md:200` | "`supabase/config.toml` diff is a local port renumber (…54320→54420, 54329→54429) — **local environment change, NOT part of the application release** (PO decision: exclude or separate config commit)" |
| `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md:63` | "`git log -- supabase/config.toml`: only `2d23fb8` — the current config (ports 54425/54426, `[db.migrations] enabled = false`) is an **uncommitted local change** from that baseline" |
| `docs/audit/cline/CARBONTALLY_LOCAL_SUPABASE_SETUP_AUDIT.md:57,82` | describes the config as api **54325**, db **54326**, shadow 54320, major_version 17, `[db.migrations] enabled` → "migrations WILL replay on `supabase db reset`" (i.e. it documents the canonical/committed values, not the worktree edit) |
| `docs/cline/CARBONTALLY_V3_PHASE3_RUNTIME_STABILITY_REPORT.md:117` | asserts `REACT_APP_SUPABASE_URL=http://127.0.0.1:54425` **is** the API gateway "(`supabase/config.toml [api].port = 54425`)" — a doc/config contradiction against canonical config today |
| `docs/cline/CARBONTALLY_INDEPENDENT_AUDIT_SWARM_V1_PRE_AUDIT_READINESS_REPORT.md:262` | "The DB port differs from the historical `54426` (per prior sessions); the current `.env`/config resolves to `54326`" |

---

## 8. Canonical port-contract analysis (Part C)

The requirement was: *do not assume the answer from `config.toml`*. Every hard-coded localhost port below
was located by exhaustive search of the canonical tree (excluding `.git`, `node_modules`, `.venv`, caches).

| Component | Canonical config port (CONFIGURED) | Test-harness expected port (TEST HARNESS EXPECTATION) | Other canonical references | Consistent? |
|---|---|---|---|---|
| Kong / API (`[api].port`) | **54325** | **54425** — `backend/tests/integration/conftest.py:59` (`os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54425")`); `backend/tests/unit/api/test_supabase_client_lifecycle.py:41,43`; `backend/tests/unit/api/test_v3_health_realtime.py:47,74`; `qa_harness/config/qa_config.yaml:39-40`; `qa_harness/config/environments.yaml:11-12`; `qa_harness/tests/harness/test_browser_auth.py:33`; `qa_harness/tests/harness/test_api_probe.py:30` | `backend/.env:9` `SUPABASE_URL=http://127.0.0.1:19999` (a different local gateway); 126 canonical docs mention 5442x | **NO** |
| Postgres (`[db].port`) | **54326** | **54426** — `conftest.py:40` default DSN `…@127.0.0.1:54426/carbontally_test`; **`conftest.py:19` docstring says `-p 54326`** (self-contradiction); `verify_activity_clarifications_rls.py:10`; `verify_p17_08_scope3_persistence_schema.py:17`; `test_i4_live_migration_and_persistence.py:17`; `test_p17l_capability_truth_surface_runtime.py:32,654`; `test_p17m2_governed_catalogue_selection_runtime.py:49`; `test_f039_1_adjudication_{concurrency,lifecycle}_runtime.py:12,17`; `test_p17k_governed_capability_catalogue_runtime.py:47`; `backup/test_exporter_local.py:37`; `qa_harness/scripts/run_db.py:55,74,85` (default `54426`); `qa_harness/config/*.yaml:43/15`; `qa_harness/tests/harness/test_db.py:172,204` | `backend/.env:3` `DATABASE_URL=…@127.0.0.1:54426/ct_local_93d5cdd`; outliers `backend/tests/unit/data/test_i2_insight_rls_live.py:21` (`:5432`) and `backend/tests/unit/infra/test_config.py:99,108` (`:54326`, parser fixture only) | **NO** (config vs code) and **internally split** (conftest code vs its own docstring) |
| Shadow DB (`[db].shadow_port`) | 54320 | none found | — | n/a (no consumer) |
| Pooler (`[db.pooler].port`) | 54329 | none found (`enabled = false`) | — | n/a |
| Studio (`[studio].port`) | 54323 | none found | `[studio].api_url` = `http://localhost:54325` (config-internal) | config-internal only |
| Inbucket / local SMTP (`[local_smtp].port`) | 54324 | none found | — | n/a |
| Analytics (`[analytics].port`) | 54327 | none found (`enabled = false`) | — | n/a |
| Edge inspector (`[edge_runtime].inspector_port`) | 8083 | none found | — | n/a |
| Backend API (`REACT_APP_API_URL`) | not in this config | — | `backend/.env:5` `http://localhost:8060`; code default `:8000`; audit docs observed the backend live on `:8050`/`:8070` | **NO** (unrelated to Supabase config, same class of drift) |

Quantification (canonical): `5442[0-9]` occurs on **275 lines in 153 files**; restricted to executable
directories (`backend/`, `qa_harness/`, `src/`, `tools/`) it is **43 lines in 20 files**; **126 docs**
mention it.

**Interpretation:** the canonical *executable* expectation (harness defaults, `.env`, verification scripts,
QA-harness config) is the **5442x family**, while the canonical *configuration file* declares the
**5432x family**. The mismatch is widest exactly where it matters most: the integration harness default DSN
and the QA-harness environment definitions.

---

## 9. The 5442x port family (Part D)

### 9.1 Service mapping

| Port | Service | Declared where |
|---|---|---|
| 54420 | Postgres shadow database (`supabase db diff`) | historical worktree `[db].shadow_port` |
| 54423 | Supabase Studio | historical worktree `[studio].port` |
| 54424 | Inbucket/Mailpit (local SMTP web UI) | historical worktree `[local_smtp].port` |
| 54425 | Kong / API gateway (REST, Auth, Storage, Realtime at `/…/v1`) | historical worktree `[api].port`; **RUNTIME-OBSERVED** `supabase_kong_carbon_ledger 0.0.0.0:54425->8000` |
| 54426 | Postgres | historical worktree `[db].port`; **RUNTIME-OBSERVED** `supabase_db_carbon_ledger 0.0.0.0:54426->5432` |
| 54429 | Connection pooler (currently disabled) | historical worktree `[db.pooler].port` |
| 54430 | **Not part of this family** — the separate Demo-Lab nginx gateway (`carbontally_demo_lab_gateway`, `nginx:alpine`, `127.0.0.1:54430->80`) fronting its own PostgREST/Storage containers | runtime only; no `config.toml` declaration |
| 19999 | Additional local gateway referenced by `backend/.env` `SUPABASE_URL` | code/env only; not part of this config |

### 9.2 Which tests depend on the family

All integration/verification suites and QA-harness entries that hard-code 54426/54425 (see §8, column 3).
Every such DSN targets either the dedicated `carbontally_test` database or a `ct_*` disposable clone —
consonant with the F-046-1 destructive-setup invariant.

### 9.3 Intentional, stale, or neither?

| Layer | Status | Evidence |
|---|---|---|
| Historical-worktree config 5442x | **Intentional machine-local remap**, uncommitted, and **incomplete** (2 references left at 5432x) | canonical release docs describe it as a local port renumber explicitly excluded from release |
| Canonical config 5432x | **Committed baseline** in *both* repositories (the "published default") | `git log -- supabase/config.toml` = only `2d23fb8`; canonical worktree clean |
| Test-harness expectation 5442x | **Not stale** — it matches the running stack and is current HEAD code | `conftest.py:40,58`; `qa_harness/config/*.yaml` |
| Actual running service 5442x | **Currently true** | `docker ps` + `ss -ltn` (54423/54425/54426 listening) + `com.supabase.cli.workdir:/home/shomonrobie/carbon_tally` |

### 9.4 Why the running stack is on 5442x (RUNTIME-OBSERVED, not inferred)

`docker inspect supabase_db_carbon_ledger|supabase_kong_carbon_ledger` →
`com.supabase.cli.project=carbon_ledger`, `com.supabase.cli.workdir=/home/shomonrobie/carbon_tally`.
The running `carbon_ledger` stack was therefore started **from the historical directory**, whose worktree
`config.toml` carries the 5442x remap. That is why canonical tests — which talk to the *running* stack —
expect 5442x while canonical's own `config.toml` declares 5432x.

**Could the running stack be rebuilt from canonical?** This cannot be established without starting a
Supabase stack, which this task does not do. What *can* be stated:

- `project_id` is **identical** (`carbon_ledger`) in the canonical and historical configs, so the CLI
  derives the **same** Compose project and the **same** container names from either directory;
- therefore `supabase stop`/`start` executed in *either* directory acts on the *same* container set, and a
  start from the canonical directory would attempt to bind **54323/54325/54326** instead of the ports that
  every current test expects. **This is a latent environment hazard, independent of which file the PO
  keeps.**

Precise framing: the **5442x family is not stale** (running + expected + code-referenced); the
**canonical `config.toml` is the artefact that is out of step with the environment it would define** if it
were used to start the stack.

### 9.5 Third family for completeness — e2e (`carbontally_e2e`, 553xx)

`e2e/environment/supabase/config.toml` is a **complete** remap of the same family (api 55325, db 55326,
shadow 55320, pooler 55329, studio 55323, `studio.api_url` 55325, smtp 55324, analytics 55327, inspector
8183), `[db.migrations] enabled = true`, `project_id = "carbontally_e2e"`. It is referenced by e2e
documentation as an isolated environment (`:55325`/`:55326`, backend `:8051`). It is **not** used by the
integration harness or the QA harness.

---

## 10. `[db.migrations]` analysis (Part E)

### 10.1 What the setting is

`[db.migrations] enabled` is a **Supabase CLI workflow flag**: when `false`, the CLI *skips migrations*
during `supabase db push` and `supabase db reset`. It is not read by the application, not read by FastAPI,
and not read by any test (no canonical reference to `db.migrations` exists outside documentation).

### 10.2 Why it was `false` historically (intent **established** — not inferred from absence)

| Evidence | Content |
|---|---|
| `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md:12,18,63,106,144` | the config (ports 54425/54426, `enabled = false`) is an **uncommitted local change from `2d23fb8`**; `supabase_migrations.schema_migrations` is absent because the DB was built by **restore + seed + direct migration application**, never by a CLI replay; with `enabled = false` "the CLI would skip migrations anyway"; applying remediation migrations via `db push` "will require an approved decision about the config" |
| `docs/audit/cline/CARBONTALLY_MIGRATION_APPLICATION_REPORT.md:21,85,99,111` | the flag was **temporarily enabled** to apply migrations, then **"restored to its previous value" (`enabled = false`)**, verified by `sed -n '53,58p'`; explicit operator instruction: *"Do NOT run `db push`/`db reset` merely to test the disabled config"*; and "Future migration application requires the same temporary-enable (Option A) or an equivalent approved mechanism" |
| `docs/audit/cline/CARBONTALLY_LOCAL_SUPABASE_SETUP_AUDIT.md:57,82,168,313` | documents the intended fresh-clone workflow with **`enabled = true`**: `supabase start` → `supabase db reset` replays the chain (local api :54325, db :54326, PG 17) |

**E1 answer:** the setting existed as a **deliberate local safety setting**. The developer database was not
built by the migration chain (restore/seed/direct application), so the CLI migration workflow was disabled
to prevent a `db reset`/`db push` from replaying migrations over a data-bearing database; it was returned to
`true` temporarily only when three remediation migrations had to be applied through the CLI.

### 10.3 Does canonical omit it?

**No — canonical contains the section with `enabled = true`** (line 55), i.e. the *committed baseline*
value. The historical worktree changed it to `false`. The "difference" is therefore a **local change in the
historical tree**, not an omission in canonical.

### 10.4 Does any current tooling assume migrations are enabled or disabled?

| Tooling | Reads `[db.migrations]`? | Behaviour |
|---|---|---|
| `.github/workflows/migration-drift.yml` (WP-8 release gate) | **No** | runs `python -m tools.migration_drift --repo-only` (no DB, no CLI); optional ledger comparison via the `MIGRATION_DRIFT_DATABASE_URL` secret; DSN guard refuses production-looking targets |
| `backend/tools/migration_drift.py` | **No** | single read-only `SELECT version FROM supabase_migrations.schema_migrations` |
| `qa_harness/db/migrations.py` | **No** (no `config.toml` reference anywhere in `qa_harness/`) | discovers/applies migrations directly over a DSN |
| Integration `conftest.py` | **No** | connects with `asyncpg` to an already-provisioned schema and SKIPs if absent |
| Backend application (`backend/**`) | **No** | never reads the Supabase CLI config |
| Supabase CLI | **Yes** (this is the flag's only consumer) | skips migrations on `db push`/`db reset` when `false` |

**Therefore:** nothing in canonical *assumes* `false`; nothing in canonical *assumes* `true` either —
except operator runbooks that expect a fresh clone to replay migrations
(`CARBONTALLY_LOCAL_SUPABASE_SETUP_AUDIT`).

### 10.5 Blast radius (E5)

| Surface | Affected by `[db.migrations] enabled = false`? |
|---|---|
| Local development | **Yes** — `supabase db reset`/`db push` on the local stack skip migrations |
| Test harnesses | **No** — harnesses bypass the CLI entirely (direct DSN) |
| Migration drift checks | **No** — the gate reads the ledger table, not the flag |
| CI | **No** — CI never starts Supabase and never runs the CLI |
| Production | **No** — a local CLI project file; production schema change is governed by the separate production migration policy (`docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md`, which records `supabase migration list --linked` as **PROHIBITED**) |
| Supabase CLI behaviour | **Yes** — the flag's only purpose |

### 10.6 Is the setting necessary?

- **`false`** is not necessary for the correctness of any current tool; it was a **local operator safety
  measure** specific to a database built outside the migration chain.
- **`true`** (canonical/committed) is what a fresh clone needs for the documented workflow — with the
  caveat canonical itself records: replaying migrations is **not** how the current development database was
  built, so `true` must not be applied to a data-bearing local database without a decision.

**`INTENT UNKNOWN` does not apply** to this setting: repository documentation establishes the intent. What
remains undecided is **which value the PO wants as canonical policy going forward**.

---

## 11. Production-impact analysis (Part F)

| Surface | Does either change touch it? | Evidence |
|---|---|---|
| Vercel (public frontend) | **No** | canonical `vercel.json` contains only rewrites for `/admin/*`, `/static/*`, an SPA fallback, and security headers; **zero** port literals, **zero** `config.toml` references; its CSP references `https://*.supabase.co` and `https://carbontally-api.onrender.com` |
| Render (FastAPI backend) | **No** | no `render.yaml`/`render.yml`/`Procfile`/`Dockerfile` at the repository root; Render configuration is documented separately (`docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`) and does not consume `supabase/config.toml`; `backend/config.py` `ALLOWED_ORIGINS` are `localhost:3000/3001/3002` (local dev only) |
| Production Supabase (hosted) | **No** | `supabase/config.toml` is the **local** CLI project file; a hosted project is addressed by project ref/URL, not by these `port` values; the file is untouched since `2d23fb8` and no migration/deploy artefact references it |
| Production API | **No** | no deployment artefact references either file |
| Production frontend | **No** | same |
| CI | **No** | `migration-drift.yml` uses no Supabase CLI, no ports, no CLI config |
| **Local development (the only affected surface)** | **Yes** | `supabase start` / `db reset` / `db push` port bindings and migration-replay behaviour |

**Statement:** a local `supabase/config.toml` port remap **cannot** change production infrastructure. No
production URL, project ref or secret is involved, and no production connection was made or attempted by
this task.

---

## 12. Evidence table

All rows are reproducible with read-only commands. `PROV` = provenance class.

| # | Fact | Measurement | PROV |
|---|---|---|---|
| E1 | Historical HEAD / branch / porcelain | `20b7a928…` / `main` / 305 | GIT-OBSERVED |
| E2 | Canonical HEAD / branch / porcelain | `cb70fd6…` / `p8-release-reconciled` / 32 | GIT-OBSERVED |
| E3 | Both `2d23fb8` and `eed55d6` are ancestors of both HEADs | `merge-base --is-ancestor` = YES ×4 | GIT-OBSERVED |
| E4 | Only 2 non-checkpoint commits touch `output/reports/import_summary.md` | `log --follow` → `eed55d6`, `2d23fb8`; 554 with `--all` (552 checkpoint merges) | GIT-OBSERVED |
| E5 | Historical worktree report digest | sha256 `81916d76…`, blob `f0193b5c`, 1,164 B / 55 lines, ` M` | OBSERVED |
| E6 | Canonical report digest | sha256 `8babb331…`, blob `4d2b2b38`, 835 B / 34 lines, clean | OBSERVED |
| E7 | 2026-08-15 report is reachable in Git | `git show f30b51b:output/reports/import_summary.md` → `81916d76…`; ref `refs/cline/checkpoints/1790426195384_kpifz/5` | GIT-OBSERVED |
| E8 | Five distinct blobs exist for this path; all five reachable from refs | `rev-list --all --objects` + per-commit blob resolution | GIT-OBSERVED |
| E9 | Generator CLI | `src/commands/import_defra.py` (288 lines; `--no-db`, `--mode`, `--db-url`, `--workbook`, `--output-dir`) | CODE EXISTS |
| E10 | Report writer + exact filename | `src/providers/defra/exporter.py:250` → `output/reports/import_summary.md` | CODE EXISTS |
| E11 | Header produced by the current exporter = the historical file's header | `"# CarbonTally — DEFRA Import Summary"` | CODE EXISTS |
| E12 | DB-load section emitted only when `result.db` is set | `exporter.py` `if result.db:` | CODE EXISTS |
| E13 | Report path asserted by a canonical test | `src/providers/defra/tests/test_import_provenance.py:389` | TEST EXPECTED |
| E14 | 7029 expected by a canonical test | `EXPECTED_DEFRA_2025_FACTORS = 7029` | TEST EXPECTED |
| E15 | Workbook hash duplicated in canonical tooling | `tools/demo_lab/seed_factors.py` expected metadata: `sha256 8bfdb45b…`, `imported 7029`, `skipped 1711` | CODE EXISTS |
| E16 | Workbook present, tracked, hash-identical | `tools/carbon_data_factory/{docs,factors}/ghg-conversion-factors-2025-flat-format.xlsx` → `8bfdb45b…` (both copies) | OBSERVED |
| E17 | Run log (historical, untracked) | `output/logs/import_defra_20260815_000630.log`; `DONE … imported=7029 … elapsed=409951ms`; `Database load complete (psycopg2): 7029 inserted, 0 updated` | OBSERVED |
| E18 | Load-SQL artefact (historical, untracked) | `output/sql/emission_factors.sql`, 5,707,634 B, 7,029 `INSERT INTO` | OBSERVED |
| E19 | Canonical migrations contain no factor rows / no seed dir | 89 migrations; `supabase/seeds` absent; `[db.seed] enabled=false`, `sql_paths=[]` | MIGRATION PRESENT (schema) / CONFIGURED |
| E20 | Canonical readers of the report | none found (code search; docs cite only) | negative finding |
| E21 | `output/` is not gitignored; only `*.log` is | `git check-ignore -v`; `.gitignore:25`; `git ls-files output` = 1 file | OBSERVED |
| E22 | Config HEAD blobs identical in both repos | `938b920b…` / sha256 `f9b1207b…`, 410 lines | GIT-OBSERVED |
| E23 | Historical config is an uncommitted edit; canonical is clean | ` M` vs (empty); worktree blobs `bca4ef4b` vs `938b920b` | GIT-OBSERVED |
| E24 | Exact config diff = 7 hunks | api 54425/54325 · db 54426/54326 · shadow 54420/54320 · pooler 54429/54329 · migrations false/true · studio 54423/54323 · smtp 54424/54324 | OBSERVED |
| E25 | Two references un-remapped in the historical edit | `[studio] api_url = http://localhost:54325` (line 126); `[analytics] port = 54327` (line 386) | CONFIGURED |
| E26 | e2e config is a complete 553xx remap | 55325/55326/55320/55329/55323/`api_url` 55325/55324/55327, inspector 8183, `carbontally_e2e`, migrations `true` | CONFIGURED |
| E27 | e2e copy derived from the 544xx config | `docs/cline/prompt-history/CT-P6-2F-ENV-IMPL-20260911-001.md:123` — `cp … # then remap ports 544xx → 553xx` | DOCUMENTED |
| E28 | Harness default DB DSN | `backend/tests/integration/conftest.py:40` → `127.0.0.1:54426/carbontally_test` | TEST HARNESS EXPECTATION |
| E29 | Harness default Supabase URL | `conftest.py:59` → `http://127.0.0.1:54425` | TEST HARNESS EXPECTATION |
| E30 | conftest docstring contradicts its own code | `conftest.py:19` `createdb … -p 54326` vs `:40` `54426` | TEST HARNESS EXPECTATION (internally split) |
| E31 | QA-harness environment expectation | `qa_harness/config/{qa_config,environments}.yaml` 54425/54426; `scripts/run_db.py:74` default `54426` | TEST HARNESS EXPECTATION |
| E32 | Canonical `.env` port + gateway | `backend/.env:3` DB `54426` (`ct_local_93d5cdd`); `:9` `SUPABASE_URL=…:19999` | CONFIGURED |
| E33 | 5442x spread in canonical | 275 lines / 153 files; 43 lines / 20 executable files; 126 docs | OBSERVED |
| E34 | Actual running stack ports | kong `54425->8000`, db `54426->5432`, studio `54423->3000` | RUNTIME-OBSERVED |
| E35 | Running stack's CLI workdir | container label `com.supabase.cli.workdir:/home/shomonrobie/carbon_tally` | RUNTIME-OBSERVED |
| E36 | Separate demo-lab gateway on 54430 | `carbontally_demo_lab_gateway nginx:alpine 127.0.0.1:54430->80` | RUNTIME-OBSERVED |
| E37 | `[db.migrations] false` intent documented | migration-history reconciliation + migration-application report (§10.2) | DOCUMENTED |
| E38 | No tooling reads `[db.migrations]` | greps across CI, `qa_harness/`, `backend/`, `tools/` | negative finding |
| E39 | CI migration gate is CLI-free | `.github/workflows/migration-drift.yml` (`--repo-only` + optional ledger DSN) | CONFIGURED |
| E40 | Production surfaces do not consume the config | `vercel.json` (no ports), no `render.yaml`, Render docs separate, CSP → hosted Supabase/onrender | OBSERVED |
| E41 | Live factor count | **not measured here** (`DATABASE NOT ACCESSED`); documented elsewhere as 7,049 (7,029 + 20) | DOCUMENTED |

---

## 13. Remaining uncertainty

| # | Uncertainty | Why it remains | Could it change a decision? |
|---|---|---|---|
| U1 | **Which config the running stack *should* use** — only *which it currently uses* is established | Determining the intended value requires a PO/engineering policy call, not more forensics | Yes (this is the decision itself) |
| U2 | **Whether a canonical `supabase start` would succeed/rebind** (the project-id collision hazard of §9.4) | Establishing it requires starting/stopping a Supabase stack — prohibited here (and unsafe: the stack is data-bearing) | Yes, as a caveat to the "port-align" option |
| U3 | **Current live factor count (7,029 / 7,049)** | `DATABASE NOT ACCESSED` per the mandate; prior hash-verified measurements exist in project records but were not re-derived | Confirms/denies whether the 2026-08-15 load is still the live dataset — matters for RETAIN/ARCHIVE weighting |
| U4 | **The three further historical blob variants** (`0a23a543`, `9c28f5fc`, `d42f28a6`) | Their containing commits are merge/checkpoint commits; `--find-object` cannot surface them, and enumerating their chronology adds no decision value | No (they are earlier iterations of the same generated file) |
| U5 | **Whether the *committed* canonical report was ever the "current" one** in the canonical clone | Cannot be observed (clone mtimes are uniform); only the format/staleness relationship is provable | No |
| U6 | **Exact intent behind the two un-remapped references** (studio `api_url`, analytics port) | No document explains why the 5442x remap was partial; only the *fact* of incompleteness is provable | Yes, if the PO chooses "port-align": alignment should be complete |
| U7 | **Whether any CI run has ever executed `migration-drift.yml`** | No run history inspected (out of scope; no network access to the CI service) | No |
| U8 | **Status of the historical repo's `output/**` companions** (log, SQL, JSON, statistics) | They are untracked local files; no maintainer decision exists about them | Yes for the "archive" option (they are the surrounding evidence) |

### Explicit non-claims

- It is **not** claimed that any database currently contains 7,029 DEFRA factors (`DOCUMENTED`/`TEST
  EXPECTED` only; no DB was opened).
- It is **not** claimed that the 5442x mapping is "correct" because tests reference it — it is claimed that
  it is (i) the family canonical tests expect, (ii) the family the running stack publishes, and (iii) the
  family the historical worktree declares. Correctness is a PO/engineering decision.
- It is **not** claimed that production is or was affected in any way by either file.

---

## 14. PO decision matrix

| Item | Technical finding | Product functionality at risk | Audit/provenance risk | Configuration risk | Evidence confidence | PO decision required |
|---|---|---|---|---|---|---|
| `output/reports/import_summary.md` | Machine-generated per-run report (`write_summary()` → exactly this path, asserted by a canonical test). The historical **worktree** copy = 2026-08-15 run **with a real DB load** (`psycopg2`, 7029 inserted / 0 updated) and is the only copy carrying that `## Database load` evidence; the copy committed in *both* repositories = an **older dry run** (`no_db=True`, 2026-08-06, superseded format). No code reads it; no test depends on the repo copy. Workbook hash `8bfdb45b…` and counters 7029/1711/0/0 are duplicated in canonical tooling (`seed_factors.py`, `test_import_provenance.py`). Content recoverable from checkpoint ref `f30b51b`; reproducible from the canonical generator + tracked workbook. Classification: `MIXED` (generated artefact + audit evidence + duplicated information). | **None** (nothing reads it; no workflow depends on its presence) | **Low–Medium** — deleting the worktree copy would leave no *committed or canonical* record of the 2026-08-15 DB load (only a checkpoint-ref blob in another repo, plus an untracked log) | **None** | **High** for file facts, lineage and generator; **Medium** on whether today's live dataset still matches that load (no DB access) | **YES** |
| `supabase/config.toml` | Both repositories' committed `HEAD` blob is identical, and canonical's worktree is clean (api 54325, db 54326, shadow 54320, pooler 54329, studio 54323, smtp 54324, `[db.migrations] enabled = true`). The historical **worktree** carries an uncommitted, **incomplete** remap to 5442x plus `enabled = false`. Canonical *executables* (integration conftest, QA harness, `.env`, ~10 verification scripts) expect **5442x/54425**, and the **running** `carbon_ledger` stack (started from the historical directory) publishes **54425/54426/54423**. `project_id` is identical in both clones → shared Compose project and container names. Nothing reads `[db.migrations]`; no CI or deploy artefact reads the file; production unaffected. Documented as "local port renumber — not product config" and excluded from release. | **None directly**; **latent operational risk** if `supabase start`/`stop` is run from the canonical clone (ports would move to 5432x, breaking every 5442x-referencing test/harness) | **None** (environment config, not evidence) | **Medium** — an unreconciled local edit exists in a working tree the live stack is currently running from; a fresh canonical clone would produce a differently-addressed local stack | **High** (config text, diff, harness references and running ports all directly measured); **Medium** on intended policy | **YES** |

**Neutrality statement:** the options below are presented with their evidence-based consequences. **None is
selected or recommended.** Both rows are marked `PO decision required`.

### 14.1 IMPORT SUMMARY — options (evidence for each, no selection)

| Option | What it would mean | Evidence the PO should weigh |
|---|---|---|
| **RETAIN** | Keep the historical working-tree version as-is (uncommitted) where it is | Preserves the only copy of the 2026-08-15 DB-load record in a live tree; leaves a modified tracked file inside a 305-entry dirty working tree (03B-class noise); the content is machine-regenerable |
| **ARCHIVE** | Preserve the run record (with its companions — log, `import_statistics.json`, `emission_factors.sql`) in an evidence location outside the source tree, then let a governed disposition of the original proceed | Keeps unique provenance evidence while removing a generated artefact from the release tree; consistent with the project's existing practice of preserving factor provenance outside the repo (prior EF preservation archive); requires a decision on *where* evidence lives |
| **DELETE** | Remove `output/reports/import_summary.md` from the historical working tree | Zero functional impact (no reader); content still recoverable via checkpoint ref `f30b51b` in the *historical* repo only; the committed canonical copy would remain; **would lose in-tree discoverability** of the DB-load facts |
| **RECONSTRUCT/REGENERATE** | Re-run `python -m src.commands.import_defra` (without `--no-db`, `--output-dir` at an approved location) using the tracked, hash-verified workbook; or restore the 2026-08-15 file into the canonical tree as a documented evidence artefact | Generator (`src/commands/import_defra.py`), workbook (SHA-256 matches) and expected statistics all exist in canonical → reproducible; **caveats:** a re-run against a live database is a *write* operation requiring its own authorisation, and its output would be a *new* run record (different timestamp/execution time), **not** the 2026-08-15 record |
| **NEEDS MORE EVIDENCE** | Defer | The only material open question is U3 (does the live dataset still equal the 2026-08-15 load?) — answerable only by an authorised read-only DB query, which this task was not permitted to run |

### 14.2 SUPABASE CONFIG — options (evidence for each, no selection)

| Option | What it would mean | Evidence the PO should weigh |
|---|---|---|
| **KEEP CANONICAL AS-IS** | Leave `supabase/config.toml` at 5432x / `migrations = true` (and leave the historical working-tree edit untouched) | Canonical is clean and equals both HEADs; docs describe 5432x as the fresh-clone default; **but** the harness/tests/`.env` expect 5442x and the running stack is on 5442x — the mismatch persists |
| **PORT-ALIGN CANONICAL CONFIG** | Bring the canonical worktree config into line with the environment the tests and the running stack actually use (5442x) | Removes the harness↔config contradiction and matches reality; **requires an explicit sub-decision** on also aligning the two references the historical edit left behind (`[studio] api_url`, `[analytics] port`), and must contend with the shared-`project_id` hazard (§9.4) — a `supabase start` from canonical would still target the same containers |
| **RESTORE `db.migrations` SETTING** | Re-introduce `enabled = false` into canonical (as the historical worktree had it) | Protects a restored/provisioned local database from an accidental `db reset`/`db push` replay; **but** it disables the documented fresh-clone workflow (`supabase db reset` replaying 89 migrations), and nothing in the toolchain needs it |
| **REMOVE HISTORICAL SETTING** | Adopt the canonical value (`enabled = true`) as the single policy and discard the historical `false` from consideration | Matches both HEADs and the setup audit; the historical `false` was a local safety measure for a database built outside the chain; removing it from the policy set is safe for CI/harness/production (none read the flag) but changes `db reset`/`db push` behaviour on a data-bearing local DB |
| **NEEDS MORE EVIDENCE** | Defer | Open: U1 (intended port policy) and U2 (whether the canonical clone's `supabase start` may be run at all, given the shared project id and the data-bearing stack) |

### 14.3 Decision-pack scope note

This pack deliberately stops at evidence. Implementing any option above would require a separate,
explicitly authorised change task with its own safety plan, because `supabase/config.toml` is coupled to a
live, data-bearing local stack.

---

## 15. Safety / end-state check and verdict

### 15.1 Re-measured state at the end of the task

| Check | Required | Measured | Result |
|---|---|---|---|
| Historical branch | unchanged | `main` | ✅ |
| Historical HEAD | unchanged | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | ✅ |
| Historical porcelain | unchanged | **305** entries (= 227 ` M` + 78 `??`, identical split to baseline) | ✅ |
| Historical `output/reports/import_summary.md` | not modified | 1,164 B, sha256 `81916d76…`, mtime `2026-08-15 13:13:20 +0600`, still ` M` (pre-existing) | ✅ |
| Historical `supabase/config.toml` | not modified | 14,823 B, sha256 `a8bc9256…`, mtime `2026-09-01 13:55:26 +0600`, still ` M` (pre-existing) | ✅ |
| Canonical branch | unchanged | `p8-release-reconciled` | ✅ |
| Canonical HEAD | unchanged | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | ✅ |
| Canonical porcelain | +1 only (this document) | **33** = 32 baseline + the new 03C decision pack; still exactly one tracked modification (` M .gitignore`, pre-existing) | ✅ |
| Canonical `output/reports/import_summary.md` | not modified | 835 B, sha256 `8babb331…`, mtime `2026-09-19 18:44:21`, clean | ✅ |
| Canonical `supabase/config.toml` | not modified | 14,822 B, sha256 `f9b1207b…`, clean | ✅ |
| Source / SQL / migrations / config modified | none **by this task** | canonical: `git status --porcelain -- supabase backend/.env` = **empty**, and the only non-untracked entry in the whole worktree is the pre-existing ` M .gitignore`. historical: unchanged 305/227/78 split with the same pre-existing entries (` M supabase/config.toml`, 3 `supabase/snippets/*.sql`, 227 tracked modifications overall) — no digest or mtime moved. **No file was created or edited anywhere except the two mandated Markdown reports.** | ✅ |
| Database access or mutation | none | no connection made to any database; no integration or harness suite executed | ✅ |
| Production access | none | no production URL, project ref or credential used | ✅ |
| Deletion / copy / move / rename / checkout / reset / stash / cherry-pick / merge / commit / push / deploy | none performed | — | ✅ |
| Harness destructive-setup invariant (F-046-1) respected | yes | the integration `conftest.py` fixture performs `TRUNCATE … RESTART IDENTITY CASCADE`; it was **not executed**, and no target database was named or contacted | ✅ |

Size cross-check supporting the diff: the historical `config.toml` is **14,823 B** and the canonical one
**14,822 B** — exactly 1 byte more, consistent with `enabled = false` (5) replacing `enabled = true` (4)
with all other replacements equal in length.

### 15.2 Files created by this task

| File | Purpose |
|---|---|
| `docs/architecture/CT-PO-CARBONTALLY-RECON-03C-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK-20260927.md` | this decision pack |
| `docs/architecture/CT-PO-CARBONTALLY-RECON-03C-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK-20260927-REPORT.md` | concise companion report |

Nothing else was created, modified or removed in either repository.

### 15.3 Answers to the two open questions, stated plainly

1. **Historical `output/reports/import_summary.md`** — a machine-generated per-run report whose generator
   (`src/commands/import_defra.py` → `src/providers/defra/exporter.py:250 write_summary`) **exists in
   canonical**, whose workbook is present and hash-verified, and whose worktree copy is the **only** record
   of a 2026-08-15 **database load** (7,029 inserted / 0 updated) — evidence that is *(a)* unique,
   *(b)* recoverable from a checkpoint ref, *(c)* reproducible from canonical artefacts, and
   *(d)* not needed by any code path. Classification: **`MIXED`**. **PO decision required.**
2. **`supabase/config.toml`** — the two repositories' committed configs are identical (5432x,
   `migrations = true`); the historical **worktree** holds an uncommitted, **incomplete** 5442x remap plus
   `migrations = false`. The canonical **tests/harness/.env expect 5442x**, the **running stack publishes
   5442x** (started from the historical directory), and **production is unaffected**. The
   `migrations = false` intent is **documented** (local safety for a database built outside the migration
   chain); no tool reads the flag. **PO decision required.**

### 15.4 Explicit statements

> **No product/source/configuration decision was implemented during this task.**

> No product decision was made, recommended, or implied. Both decision rows are marked `PO decision
> required`, and every option set in §14 is presented with evidence only.

### 15.5 Verdict

```
CT_RECON_03C_COMPLETE_DECISION_PACK
```

The two questions that CT-RECON-03B left open are **answered with evidence**. Every Part A–G question is
answered or explicitly declared unanswerable within the mandate (A8 database evidence: `DATABASE NOT
ACCESSED`; Part D "would the canonical stack use 5442x": not establishable without starting a Supabase
stack). Nothing is `BLOCKED`. The remaining items are **decisions** (PO) and **open uncertainties** (U1–U8,
§13), not missing forensics.

### 15.6 Follow-ups for the PO / next task (not implemented)

1. Decide the disposition of `output/reports/import_summary.md` (§14.1) — noting the unique 2026-08-15
   DB-load evidence and that its content survives in `refs/cline/checkpoints/…` only.
2. Decide the config policy (§14.2) — and, if "port-align" is chosen, decide the completeness question
   (`[studio] api_url`, `[analytics] port`) and how to handle the shared `project_id = "carbon_ledger"`
   collision between the two clones (§9.4).
3. If the PO needs U3 resolved (does the live dataset still equal the 2026-08-15 load?), authorise a
   **read-only** verification (the existing `src/providers/defra/tests/test_import_provenance.py` and the
   EF-preservation records are the natural starting points) against an explicitly permitted target — the
   harness's destructive `conftest.py` fixture (F-046-1) must never be pointed at a persistent database.
4. Consider recording the two 03C documents in Git (they are currently untracked), per the project's normal
   document-handling discipline.

