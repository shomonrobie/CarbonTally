# CT-RECON-03C — REPORT (companion summary)

**Task:** `CT-RECON-03C-20260927-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK`
**Type:** READ-ONLY forensic / decision support
**Date:** 2026-09-27
**Full pack:** `docs/architecture/CT-PO-CARBONTALLY-RECON-03C-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK-20260927.md`

## Baselines used

| Repo | Branch | HEAD |
|---|---|---|
| Historical `/home/shomonrobie/carbon_tally` | `main` | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` |
| Canonical `/home/shomonrobie/ct_93d5cdd` | `p8-release-reconciled` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |

Both `2d23fb8` and `eed55d6` are ancestors of **both** HEADs → the two repositories share the history of
these two paths, and their `HEAD` blobs for both files are identical. All differences found are
**working-tree** differences.

## 1. What was asked

Resolve the two items CT-RECON-03B left open — historical `output/reports/import_summary.md` (HIST-30) and
`supabase/config.toml` (HIST-32) — with enough evidence for a PO decision, without making that decision and
without modifying or deleting anything.

## 2. Method

Read-only throughout: filesystem metadata and digests; Git object/history inspection (`log --follow`,
`merge-base --is-ancestor`, `rev-list --all --objects`, per-commit blob resolution, `cat-file`,
`check-ignore`); exhaustive content searches for the filename **and** for the report's concepts
(`carbon_data_factory`, `no_factor_value`, `rows_scanned`, `7029`, `DEFRA-2025`); source and test
inspection; CI/workflow inspection; **read-only** `docker ps` / `docker inspect` to establish what is
actually running. No database was opened; no test suite was run — the integration fixture `TRUNCATE`s its
target (F-046-1), so it was deliberately not executed. Limits are stated per finding.

## 3. Key findings — `output/reports/import_summary.md`

1. **The generator EXISTS in canonical** (this supersedes 03B's "no generator anywhere"):
   `src/commands/import_defra.py` (288 lines) → `src/providers/defra/exporter.py:250 write_summary()`, whose
   docstring is *"Write `output/reports/import_summary.md` (the final report)"*; the path is asserted by
   `src/providers/defra/tests/test_import_provenance.py:389`. The earlier search missed it because the
   filename is built inside `write_summary` (`report_dir / "import_summary.md"`).
2. **The historical worktree copy is the newer, meaningful one**: generated `2026-08-15T00:13:20`, workbook
   `ghg-conversion-factors-2025-flat-format.xlsx`, workbook SHA-256 `8bfdb45b…`, factor set `DEFRA-2025`,
   7,029 imported / 1,711 skipped / 0 duplicates / 0 warnings / 0 errors, **plus a `## Database load` block
   (`psycopg2`, inserted `7029`, updated `0`)** — that section is emitted only for runs *without* `--no-db`,
   so this is a real load record, not a dry run. (1,164 B, 55 lines, blob `f0193b5c`, sha256 `81916d76…`,
   tracked and ` M`.)
3. **The committed copy (identical in both repos) is the older dry run**: `# Import Summary`,
   `2026-08-06T05:12:27`, **`no_db = True`**, no DB-load section; 835 B / 34 lines, blob `4d2b2b38`,
   sha256 `8babb331…`.
4. **Lineage:** only 2 non-checkpoint commits ever touch the path (`2d23fb8` ADD; `eed55d6` same content);
   552 of the 554 commits referencing it are Cline checkpoint merges. Five distinct blobs exist for the
   path and **all five are reachable** from refs.
5. **Recoverable (not merely dangling):** `git show f30b51b:output/reports/import_summary.md` reproduces the
   2026-08-15 content byte-for-byte (`81916d76…`); that commit sits only in
   `refs/cline/checkpoints/1790426195384_kpifz/5` and is **not** an ancestor of `main`.
6. **Reproducible:** the workbook is tracked in canonical at
   `tools/carbon_data_factory/docs/ghg-conversion-factors-2025-flat-format.xlsx` (and under `factors/`) with
   SHA-256 `8bfdb45b…` — byte-identical to the hash the report records; `tools/demo_lab/seed_factors.py`
   hard-codes the same hash plus `imported 7029` / `skipped 1711`; `test_import_provenance.py` asserts
   `EXPECTED_DEFRA_2025_FACTORS = 7029`.
7. **No consumer:** no code reads the repo copy; no test depends on it; only documentation cites it. The
   historical run's companions (`output/logs/import_defra_20260815_000630.log`,
   `output/reports/import_statistics.json`, `output/sql/emission_factors.sql` with 7,029 `INSERT INTO`s,
   `output/json/…`) are **untracked** and exist only in the historical tree.
8. **Dataset representation:** no canonical migration or seed contains factor rows (`supabase/seeds` absent;
   `[db.seed] enabled = false`, `sql_paths = []`). The live count was **not** measured here
   (`DATABASE NOT ACCESSED`); it is documented elsewhere as 7,049 (7,029 + 20) — `DOCUMENTED`, not
   re-verified.
9. **Classification: `MIXED`** — historical generated artefact + unique audit evidence + partially
   duplicated information. Loss risk: product functionality **none**; audit/provenance **low–medium**
   (in-tree discoverability only).

## 4. Key findings — `supabase/config.toml`

1. Both repos' committed config is identical, and canonical's worktree is clean: api **54325**, db **54326**,
   shadow **54320**, pooler **54329**, studio **54323**, smtp **54324**, `[db.migrations] enabled = true`
   (blob `938b920b…`).
2. The historical **worktree** carries an uncommitted remap to **54425 / 54426 / 54420 / 54429 / 54423 /
   54424** plus `enabled = false` — **exactly 7 diff hunks**. File size 14,823 B vs canonical 14,822 B
   (+1 byte, consistent with `false` replacing `true`).
3. The historical edit is **incomplete**: `[studio] api_url = http://localhost:54325` (line 126) and
   `[analytics] port = 54327` (line 386) were left in the 5432x family. By contrast, the e2e copy
   (`e2e/environment/supabase/config.toml`, `project_id = carbontally_e2e`) is a **complete** 553xx remap
   (including `api_url` 55325, analytics 55327, inspector 8183), and canonical docs record it was produced by
   `cp supabase/config.toml … # then remap ports 544xx → 553xx` — evidence that the 544xx family was the
   operative local configuration at the time.
4. **What canonical actually expects:** integration `conftest.py:40` default DSN
   `postgresql://…@127.0.0.1:54426/carbontally_test` and `:59` `SUPABASE_URL=http://127.0.0.1:54425` — while
   its own docstring at `:19` still says `-p 54326`; `qa_harness/config/{qa_config,environments}.yaml`
   54425/54426; `qa_harness/scripts/run_db.py:74` default 54426; ~10 verification scripts; `backend/.env:3`
   54426. `5442x` appears on 275 lines in 153 files (43 lines / 20 files of executable code; 126 docs).
5. **What is actually running** (RUNTIME-OBSERVED): `supabase_kong_carbon_ledger 54425->8000`,
   `supabase_db_carbon_ledger 54426->5432`, `supabase_studio_carbon_ledger 54423->3000`, and the containers
   carry `com.supabase.cli.workdir:/home/shomonrobie/carbon_tally` — the live stack was started **from the
   historical directory**.
6. **Conclusion:** canonical's config describes neither the harness expectation nor the running stack. The
   5442x family is **not stale**; canonical's config is the artefact that is out of step with the environment
   it would define. **Latent hazard:** both clones declare the same `project_id = "carbon_ledger"`, hence the
   same Compose project and container names with **different** port bindings.
7. **`[db.migrations]`:** intent is **established**, not inferred — a local safety setting for a database
   built by restore/seed/direct application (not by CLI replay); canonical docs record the flag was
   temporarily enabled to apply three remediation migrations and then restored to `false`, together with the
   instruction not to run `db push`/`db reset` merely to test it. **Nothing reads the flag** (CI's
   `migration-drift.yml` is `--repo-only` + optional ledger DSN; `qa_harness/db/migrations.py` and the drift
   comparator work over DSNs). Blast radius: local CLI behaviour only. `INTENT UNKNOWN` does **not** apply.
8. **Production:** unaffected. No deploy artefact references the file (`vercel.json` = frontend rewrites and
   security headers only, CSP → `*.supabase.co` / `carbontally-api.onrender.com`; no `render.yaml`; Render
   configuration documented separately). A local config port remap cannot change Vercel, Render, the hosted
   Supabase project, the production API or the production frontend.

## 5. Disposition summary

| Item | Classification | Product functionality at risk | Audit/provenance risk | Configuration risk | Evidence confidence | PO decision |
|---|---|---|---|---|---|---|
| `output/reports/import_summary.md` | `MIXED` (generated artefact + audit evidence + duplicated information) | none | low–medium (only in-tree discoverability of the 2026-08-15 DB-load record) | none | high (file/lineage/generator); medium on live-dataset equivalence (no DB access) | **required** |
| `supabase/config.toml` | local environment configuration (documented as *not* product config) | none directly; latent operational risk via shared `project_id` | none | medium (unreconciled local edit; config vs harness/running-stack mismatch) | high (text/diff/harness/running ports); medium on intended policy | **required** |

**Options presented to the PO (none selected, none recommended):**

- IMPORT SUMMARY: **RETAIN** · **ARCHIVE** · **DELETE** · **RECONSTRUCT/REGENERATE** · **NEEDS MORE EVIDENCE**
- SUPABASE CONFIG: **KEEP CANONICAL AS-IS** · **PORT-ALIGN CANONICAL CONFIG** · **RESTORE `db.migrations`
  SETTING** · **REMOVE HISTORICAL SETTING** · **NEEDS MORE EVIDENCE**

Full option-by-option evidence is in §14 of the main pack.

## 6. Verification / end-state (re-measured after all work)

| Check | Measured | Result |
|---|---|---|
| Historical branch / HEAD | `main` / `20b7a928…` | unchanged ✅ |
| Historical porcelain | 305 (227 ` M` + 78 `??`) | unchanged ✅ |
| Historical `import_summary.md` | 1,164 B, `81916d76…`, mtime 2026-08-15 13:13:20, ` M` | unchanged ✅ |
| Historical `supabase/config.toml` | 14,823 B, `a8bc9256…`, mtime 2026-09-01 13:55:26, ` M` | unchanged ✅ |
| Canonical branch / HEAD | `p8-release-reconciled` / `cb70fd6…` | unchanged ✅ |
| Canonical porcelain | 33 = 32 baseline + this pack (+ the companion report) | only additions are the two 03C documents ✅ |
| Canonical `import_summary.md` | 835 B, `8babb331…`, clean | unchanged ✅ |
| Canonical `supabase/config.toml` | 14,822 B, `f9b1207b…`, clean | unchanged ✅ |
| Source / SQL / migrations / config modified | none (`git status --porcelain -- supabase backend/.env` empty) | ✅ |
| Database access / mutation | none (no connection; no suite executed) | ✅ |
| Production access | none | ✅ |
| Delete / copy / move / rename / checkout / reset / stash / merge / commit / push / deploy | none performed | ✅ |
| F-046-1 destructive-setup invariant | integration fixture never executed; no target named | respected ✅ |

Files created by this task (the only changes anywhere):
`docs/architecture/CT-PO-CARBONTALLY-RECON-03C-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK-20260927.md`
and `…-REPORT.md`.

## 7. Remaining uncertainty (nothing blocking)

- **U1** intended port policy (a decision, not missing forensics).
- **U2** whether a `supabase start` from the canonical clone may ever be run — the shared
  `project_id = "carbon_ledger"` means it targets the same **data-bearing** container set. Not testable here
  without starting/stopping Supabase (prohibited and unsafe).
- **U3** whether the live dataset still equals the 2026-08-15 load (7,029 / 7,049): requires an authorised
  **read-only** query; `DATABASE NOT ACCESSED` in this task.
- **U4–U8** (three further historical blob variants; whether the committed report was ever "current" in the
  canonical clone; why the 5442x remap was partial; whether CI has ever run the drift gate; the status of the
  historical tree's untracked `output/**` companions).

Explicit non-claims: no database was shown to contain 7,029 factors; the 5442x mapping is not asserted to be
"correct" merely because tests reference it; production is not claimed to be affected in any way.

## 8. Verdict

```
CT_RECON_03C_COMPLETE_DECISION_PACK
```

Both questions left open by CT-RECON-03B are answered with evidence; every Part A–G question is answered or
explicitly declared unanswerable within the mandate. Nothing is `BLOCKED`. The remaining items are **PO
decisions** and **open uncertainties**, not missing forensics.

> **No product/source/configuration decision was implemented during this task.**