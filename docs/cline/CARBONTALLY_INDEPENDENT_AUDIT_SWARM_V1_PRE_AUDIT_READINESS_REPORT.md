# CarbonTally — Independent Audit Swarm V1: Pre-Audit Readiness Report

- Date: 2026-08-31
- Checkpoint: `16391217103b98dcea520070c5a22c68f12fe607`
- Scope: **forensic validation of the Independent Audit Swarm itself** (READ-ONLY)
- CarbonTally application, DB, migrations, RLS, seed data, frontend, backend
  and `qa_harness/`: **NOT modified** (verified via `git status`; zero tracked
  application changes).
- This report documents why the collectors-only run must **not** be treated as
  an application audit, what defects were proven in the swarm, and what was
  fixed so the real audit can be gated safely.

---

## 1. Current run reconstruction

Command executed by the operator (collectors-only / AI-disabled):

```
cd /home/shomonrobie/carbon_tally/independent_audit
python3 run_audit.py --credentials-file /path/to/IA_CREDENTIALS.json --verbose
```

Reconstructed from `reports/run_meta.json` (the authoritative artifact):

| field | value |
|---|---|
| started_at / finished_at | 2026-08-31T12:34:39Z / 12:34:54Z |
| checkpoint / actual HEAD | `16391217…` / `16391217…` (match) |
| stages_completed | freshstart, collect, crosscheck, judge, reports |
| agents | **skipped — no model API key configured** |
| collectors | db = unavailable (psql, `127.0.0.1:54326` connection refused); api = ok (4 packets); frontend = ok (4 packets); browser = unavailable (credentials file was the literal placeholder `/path/to/IA_CREDENTIALS.json` → `FileNotFoundError`) |
| findings.json | `{"meta": {...}, "findings": []}` |
| cost.json | `call_count: 0`, `total_tokens: 0`, `total_estimated_cost_usd: 0` |
| warnings | 3 (db unavailable, browser FileNotFoundError, agents skipped) + **secret hygiene violations** (5 truncated entries, all `sha256:hex_secret`) |

**Verdict: the run produced zero findings because zero agents ran and two of
four collectors were unavailable. It is NOT a successful application audit.**

## 2. Evidence availability matrix (18:34 run)

| collector | status | evidence produced | evidence file |
|---|---|---|---|
| freshstart | ok | repo map, fresh-start exclusions | `evidence/repo_map.json` |
| db | unavailable | honest `available:false` + reason | `evidence/db_unavailable.json` |
| api | ok | openapi, routes, contract diff, probes | `evidence/api_*.json` (4) |
| frontend | ok | routes, components, api map, dead UI | `evidence/frontend_*.json` (4) |
| browser | **no packet** (raised) | stale `browser_pages.json` from 13:53 remained on disk | — |
| agents (AI) | skipped | none | none |
| crosscheck/judge | deterministic only (no AI) | empty finding set | findings.json |

Browser is the critical gap: the collector *raised* instead of writing an
`available:false` packet, so the run had **no in-memory browser evidence at
all**, while a stale `browser_pages.json` (from 13:53, a different run)
remained on disk where a reader could mistake it for current coverage.

## 3. Report validity

- The six reports under `reports/` **are** current-run artifacts: generated
  timestamps `2026-08-31T12:34:53Z` fall inside the run window
  (12:34:39–12:34:54Z), and their content matches `findings.json` (0 findings)
  and `cost.json` (0 calls).
- `reports/findings.json`, `reports/cost.json`, `reports/run_meta.json` are
  also current-run (same window).
- `reports/latest/` is **NOT pipeline output**: it contains three
  manually-authored session reports (NO_AI_FIX, DB_CONNECTION_FIX,
  AGENT_RUNTIME_FIX). The pipeline writes to the out-dir root
  (`reports/`). The `latest/` name is misleading but nothing was moved;
  this is documented rather than reorganized.
- **Defect:** the reports did not state run status. `MASTER` printed
  "total findings: 0" with no mention of the missing DB, missing browser
  evidence, or skipped AI. A reader could interpret the report as a clean
  audit. → fixed (see §10).

## 4. Zero-finding semantics

`"total findings: 0"` can **never** be read as an application-quality
conclusion when agents were skipped and DB/browser were unavailable.

- **Before:** reports showed `0 findings`, `0 defect findings`, "Top risks:
  none recorded" — indistinguishable from a complete audit that genuinely
  found nothing.
- **After:** every report now carries a `## Run status` block
  (`status: INCOMPLETE`, collector coverage, AI availability, reasons,
  warnings) and an explicit banner:

  > **STATUS: AUDIT INCOMPLETE — UNVERIFIED.** … "0 findings" means "0
  > findings under incomplete evidence" — it does NOT mean "0 defects".

  The Master/Executive reports additionally add a zero-finding caveat when
  the run is incomplete and produced 0 findings.

## 5. DB / browser / AI skip semantics

| component | before | after |
|---|---|---|
| DB unavailable | honest `db_unavailable` packet + warning (good) | unchanged, plus `collectors.db=unavailable` in run_meta and run-status reasons |
| Browser credentials missing | **raised** `FileNotFoundError` → warning only, no packet, stale file on disk | writes `browser_pages` packet `available:false` with the reason, records a run warning, `collectors.browser=unavailable` |
| Browser coverage claimed | a stale `available:false` packet could be mistaken for current | stale packets are removed at run start; the current packet is always this run's |
| AI unavailable | agents skipped, silently absent | `ai.agents_ran=false`, `ai.skip_reason` recorded, reports state "AI agent analysis: unavailable", no "AI analyzed" language |
| DB/browser/AI skip → status | indistinguishable from complete | `run_status.status = INCOMPLETE` with explicit reasons |

`db_unavailable`/`browser_pages` packets carry `available:false` — unavailable
is represented as unavailable evidence, never as an empty dataset.

## 6. Secret-hygiene investigation

`run_meta.json` warning:

```
"secret hygiene violations in report tree": ['sha256:hex_secret', ...]  (x5)
```

**Reproduction:** scanning every JSON file in the report tree with
`ia_core.redact.assert_no_secrets` flags **11 files** (the warning truncates
to `violations[:5]`). Every violating file is an evidence packet, and the
violation path is exactly `sha256:hex_secret`.

**Root cause:** `assert_no_secrets` uses the generic 64-hex pattern
`(\b[0-9a-f]{64}\b)` labelled `hex_secret`. Every `EvidencePacket` stores its
own **integrity checksum** in a `sha256` field (64 hex chars). The hygiene
check therefore flagged the swarm's own integrity metadata.

**Classification: E — false positives caused by the generic secret detector.**
The 64-hex values are the packets' `sha256` checksums, not secrets; no
credential material was present in the report tree.

**Fix (evidence-based, detector NOT weakened):** `assert_no_secrets` is
path-aware; it now suppresses the `hex_secret` kind only when the value sits
under a known integrity-metadata field name (`sha256`, `sha512`, `checksum`,
`digest`, `hash`, `etag`, `git_sha`, `commit_sha`, `revision`, …).
`redact_text` remains fully conservative (a bare 64-hex string anywhere in
text is still redacted), and a 64-hex value under any other field — or a JWT
sitting in a field named `sha256` — is still flagged (regression-tested).

After the fix, a full fresh-tree hygiene scan reports **NONE — CLEAN**.

## 7. Stale-artifact analysis

Stale artifacts found in `reports/` before the fix:

- `reports/agents/db_agent.findings.json` (15:46 — from an earlier partial
  agent attempt; the 18:34 run's agents were skipped, so this file did **not**
  belong to the current run).
- `reports/evidence/browser_pages.json` (13:53 — an earlier run's packet;
  the 18:34 run produced no browser packet at all).

The pipeline overwrote top-level artifacts (six reports, findings.json,
run_meta.json, cost.json) but never cleaned sub-directories, so stale
evidence and agent outputs persisted and were included in hygiene scans and
could be misread as current.

**Fix:** `Orchestrator.run()` now calls `_clean_pipeline_artifacts()` at the
start of every run, deleting exactly the pipeline-owned paths
(`evidence/`, `agents/`, `pages/`, `screenshots/`, the six reports,
`findings.json`, `run_meta.json`, `cost.json`). `reports/latest/` and any
other user content are preserved. After any run, every artifact present was
produced by that run; a zero-finding run is distinguishable from an old
zero-finding run by `run_meta.run_id`/timestamps. Verified live: a second
run into the same dir logged `cleaned 3 stale artifact(s)`.

## 8. Exit-status analysis

Three concepts are now explicitly separated:

1. **TOOL EXECUTION SUCCESS** — `run_audit.py` exits 0 for a valid
   collectors-only execution (unchanged, and correct: the run itself worked).
2. **AUDIT COMPLETENESS** — `run_meta.json.run_status.status` is
   `COMPLETE` only when all collectors are `ok`, the AI agent stage ran, and
   the reports stage ran; otherwise `INCOMPLETE` with reasons.
3. **APPLICATION ACCEPTANCE** — never asserted by the tool; the reports
   disclaim acceptance, and the readiness gate (§13) never implies it.

Exit 0 from `run_audit.py` therefore means "the tool ran", not "CarbonTally
passed". The readiness gate `readycheck.py` returns exit 1 (NOT READY) for
any environment/run that cannot support a real audit.

## 9. Root causes (summary)

| # | issue | root cause | proof |
|---|---|---|---|
| RC-1 | zero-finding reports misleading | reports render findings only; no run-status/coverage in `meta` | MASTER said "0 findings" with no incomplete banner |
| RC-2 | browser failure left no evidence | `resolve_credentials` raised `FileNotFoundError` out of `collect_browser_evidence`; no `browser_pages` packet written | run warning `browser collector: FileNotFoundError: …IA_CREDENTIALS.json` |
| RC-3 | stale artifacts persisted | no run-start cleanup of pipeline-owned dirs | `reports/agents/db_agent.findings.json` (15:46) present in the 18:34 run tree |
| RC-4 | hygiene gate failed every run | 64-hex regex flagged packets' own `sha256` checksums | 11 files, path `sha256:hex_secret` |
| RC-5 | agents/AI absence invisible in reports | no `ai` facts in meta; reports didn't render them | reports omit agents skip; `judge_ai_verdict: null` |
| RC-6 | browser status mis-recorded | packet *presence* used as "ok" | `browser=ok` even though packet says `available:false` (fixed during testing) |
| RC-7 | "report stage not run" leaked | run_status computed before the stage marked itself complete | MASTER reason list showed "report stage not run" on a reports-complete run (fixed) |

## 10. Tool-only fixes (all confined to `independent_audit/`)

| file | change |
|---|---|
| `ia_core/report.py` | `REPORT_NAMES`, `run_status()`, `_status_block()`; every report renders `## Run status` (status, coverage, AI availability, reasons, warnings, INCOMPLETE banner); Master/Executive zero-finding caveats; UX report shows honest "browser evidence: unavailable" |
| `ia_core/redact.py` | `assert_no_secrets` suppresses `hex_secret` only under integrity-metadata field names (path-aware); text redaction unchanged |
| `collectors/browser_collector.py` | missing/unreadable credentials → writes `browser_pages` `available:false` packet with reason (never raises) |
| `orchestrator.py` | `_clean_pipeline_artifacts()` at run start; `run_id`; structured `collectors` + `ai` facts; `run_status` computed before reports and finalized in run_meta; browser status from packet `available`; browser unavailable warning; reports stage marks itself complete before status computation |
| `readycheck.py` (new) | deterministic readiness gate: pre-run prerequisite checks + `--verify OUT_DIR` post-run verification |

No CarbonTally application file, database, migration, RLS, seed data,
frontend or backend code was modified. `qa_harness/` untouched.

## 11. Tests added

`tests/test_pre_ai_validation.py` — 22 deterministic tests:

| area | tests |
|---|---|
| run_status semantics | complete / incomplete (db+browser+AI missing) / collectors-only-no-reports |
| report validity | six reports produced; run id in header; incomplete banner + zero-finding caveat; complete run has no banner; executive never claims AI when unavailable; UX shows browser unavailable |
| browser credentials unavailable | packet `available:false` + reason; no coverage claim; no-credentials case |
| secret-hygiene false positives | packet `sha256` clean; 64-hex under other fields flagged; 64-hex in lists flagged; JWT under `sha256` field still flagged |
| stale-artifact prevention | cleanup removes pipeline artifacts, preserves `latest/` and user files |
| DB/AI/browser availability + exit status | end-to-end `--no-ai` run → exit 0, run_meta INCOMPLETE, honest collectors/warnings, db+browser unavailable packets; full pipeline with no key → agents skipped, INCOMPLETE banner in MASTER |
| readiness gate | ready→exit 0; db fail→exit 1; `verify_run` passes a complete synthetic run; flags incomplete run; flags stale artifacts |

## 12. Full test results

```
177 passed in 32.02s   (155 pre-existing + 22 new)
```

Plus live smoke verification (temporary output dirs, deleted afterwards):

- collectors-only run: `status=INCOMPLETE`, collectors
  `{db: unavailable, api: ok, frontend: ok, browser: unavailable}`, warnings
  record db + browser reasons, `run_id` present, tree contains **only**
  current-run artifacts, hygiene scan **CLEAN**.
- full report pipeline without a key: MASTER renders the INCOMPLETE banner,
  coverage and AI-unavailable lines; "report stage not run" no longer leaks.
- `readycheck.py`: pre-run **NOT READY** (db down at `127.0.0.1:54326`,
  no browser credentials, no OpenRouter key); `--verify` on the incomplete
  run → **NOT READY**, exit 1.

## 13. Readiness gate

`python3 readycheck.py` — pre-run prerequisites (all deterministic,
read-only, no AI):

| check | purpose |
|---|---|
| checkpoint | `git HEAD` == configured checkpoint |
| read-only guards | `assert_sql` rejects write SQL, accepts read SQL |
| db | psql `-w` `SELECT 1` via resolved connection (read-only) |
| api | HTTP GET `base_url` + `openapi_url` == 200 |
| frontend | HTTP GET frontend root < 400 |
| browser credentials | real credentials resolve (file/env), driver + node present |
| OpenRouter key | `resolve_api_key()` non-empty |

`python3 readycheck.py --verify OUT_DIR` — post-run verification: checkpoint
match, all six stages completed, `run_status COMPLETE`, AI agents ran,
collectors all `ok`, secret hygiene clean, **no stale artifacts** (nothing
predating `started_at`, excluding user dirs), six reports + findings/cost
present, ≥4 evidence packets, 6 agent outputs, `call_count > 0`.

Verdict: **READY FOR FULL INDEPENDENT AUDIT** (exit 0) or **NOT READY FOR
FULL INDEPENDENT AUDIT** (exit 1). Optional tooling (Schemathesis, ZAP) is
not made mandatory.

**Current state: NOT READY** — the gate honestly reports the environment's
DB is down at `127.0.0.1:54326`, no browser credentials file, no OpenRouter
key. The DB port differs from the historical `54426` (per prior sessions);
the current `.env`/config resolves to `54326`.

## 14. Exact command for the first REAL AI audit

Prerequisites (per the readiness gate, all must PASS):

1. DB reachable (start/point the local Supabase/Postgres; verify with the
   gate's `db` check).
2. Provide a real browser credentials file (e.g. the investor-demo
   identities) — never commit it.
3. Provide the OpenRouter key — never pass it on a command line visible to
   `ps` if avoidable; the gate and gateway read
   `OPENROUTER_AGEN_SWARM_V1_API_KEY` from the environment or the git-ignored
   keys file.

Then:

```
cd /home/shomonrobie/carbon_tally/independent_audit

# 1. gate (must print READY FOR FULL INDEPENDENT AUDIT, exit 0)
python3 readycheck.py --credentials-file /path/to/real/IA_CREDENTIALS.json

# 2. run the full audit (freshstart -> collect -> agents -> crosscheck -> judge -> reports)
python3 run_audit.py \
  --credentials-file /path/to/real/IA_CREDENTIALS.json \
  --verbose
# (the key is read from OPENROUTER_AGEN_SWARM_V1_API_KEY or the keys file;
#  --api-key is supported as a last resort)

# 3. verify the run
python3 readycheck.py --verify reports
```

Expected honest outcomes: six reports with `status: COMPLETE` (or an
explicit `INCOMPLETE` banner listing exactly what was missing), findings with
evidence references, `cost.json` with `call_count > 0`, hygiene clean, no
stale artifacts, and — regardless of findings count — no acceptance claim.

---

## Confirmation statements

- **Read-only:** no CarbonTally app code, DB, migrations, RLS, seed data,
  frontend, backend or `qa_harness/` file was modified; `git status` shows
  zero tracked application changes from this task.
- **No AI / no spend:** no OpenRouter call was made; `cost.json` remains
  `call_count: 0`; no model was invoked during this validation.
- **Nothing committed or pushed.**
- **The full AI audit has NOT been run** and remains gated on the readiness
  check.
