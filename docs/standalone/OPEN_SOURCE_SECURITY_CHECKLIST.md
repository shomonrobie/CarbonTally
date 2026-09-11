# Open-Source Pre-Publication Security Checklist

**Status:** PROPOSAL — checklist for the eventual public release of the
standalone framework. Nothing here was deleted or modified during this audit.

The standalone repository will be public. Anything below that could identify,
authenticate, or embarrass a real deployment must NEVER enter it. This
checklist is organized as: what must never be published, where it currently
lives, and what `.gitignore`/CI policy is required.

---

## 1. What must NEVER enter the public repository

| Category | Examples | Currently where? |
|---|---|---|
| Passwords | demo password `<shared-demo-password>` | `.local-demo-credentials.md` (repo root, gitignored) — do NOT copy into standalone |
| API keys | `OPENROUTER_AGEN_SWARM_V1_API_KEY` value | env only |
| Supabase keys | anon/service_role keys from `supabase status` | env / CLI output (never stored) |
| JWTs / access/refresh tokens | `sb-*-auth-token` contents | `qa_harness/evidence/` (runtime) |
| DSNs / DB URLs | `postgresql://…` | env / `.env` (repo root, gitignored) |
| Signed URLs | document signed URLs | `qa_harness/evidence/api/*.json` (runtime) |
| Browser sessions/cookies | Playwright storage state | `qa_harness/evidence/traces/`, `videos/` (runtime) |
| Screenshots with secrets | full-page captures | `qa_harness/evidence/screenshots/` (runtime) |
| Traces with secrets | network traces | `qa_harness/evidence/traces/` (runtime) |
| Customer/demo data | identity population dumps, org data | `qa_harness/findings/*.jsonl` (runtime), `local_backups/*.sql` (repo root, gitignored?) |
| Private Hindsight memory | bank content, recall notes | outside repo (local Hindsight server) — never import |
| Generated reports | findings with real evidence paths | `qa_harness/reports/latest|archive/` (runtime) |
| Build artifacts | `*.egg-info/` | `qa_harness/carbontally_qa_harness.egg-info/` |
| Environment files | `.env`, `.env.*` | repo root |

## 2. Current runtime dirs that must be gitignored

The current harness writes runtime data into:

- `qa_harness/evidence/` — `api/`, `db/`, `console/`, `network/`,
  `screenshots/`, `traces/`, `videos/` + `registry.py`
- `qa_harness/findings/` — `raw/`, `normalized/`, `deduplicated/`
- `qa_harness/reports/` — `latest/`, `archive/`

None of these may be committed. The repo root `.gitignore` currently covers
only `/.local-demo-credentials.md`; the standalone repo needs its own
complete `.gitignore` (below).

## 3. Proposed `.gitignore` for the standalone repo

```gitignore
# --- secrets / credentials ---
*.env
.env*
!config/example/**.example
credentials*
keys.json
*.pem
*.key
*_credentials*.md
.local-demo-credentials.md

# --- runtime QA output (never publish) ---
evidence/
findings/
reports/
screenshots/
traces/
videos/

# --- tooling caches / artifacts ---
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
*.egg-info/
build/
dist/
node_modules/

# --- local state ---
.qa-harness/
supabase/
.coverage
htmlcov/
```

For the *current* CarbonTally repo, the same rules should be applied to
`qa_harness/` subpaths (recommendation only — the current repo already keeps
`qa_harness/` untracked).

## 4. Pre-publication secret scan (required)

Before the standalone repo is created:

1. `git clone` a fresh copy to a temp dir.
2. Run a secret scanner over the entire tree (e.g. `trufflehog
   filesystem`, `gitleaks`, or GitHub secret scanning on push):
   - patterns: AWS/GCP/Azure keys, private keys, JWT (`eyJ…`), Supabase
     `sb-`/`eyJhbGciOi` tokens, DSNs, generic high-entropy strings.
3. Scan **binary** content too (screenshots PNG, traces ZIP): OCR screenshots
   for visible credentials/PII before deciding to keep any fixture.
4. Confirm the runtime dirs are absent from the fresh clone.
5. Confirm no `carbon`, `carbontally.co.uk`, `localhost:3000/8050`,
   `127.0.0.1:54425/54426`, or demo-email strings appear in engine source
   (they may appear ONLY in `profiles/carbontally/`, and even there the
   email *population* should be a pointer to a private manifest, not inline).

## 5. CI policy (once published)

- **CI job 1 — self-tests:** `pip install -e .[test] && pytest` (engine
  tests only; no app contact).
- **CI job 2 — secret scan:** `gitleaks`/`trufflehog` on every PR; fail on
  findings.
- **CI job 3 — import/redaction smoke:** build the package, import all
  modules, run a tiny fake-profile run in a temp dir; assert no secret
  strings appear in captured stdout/stderr/report files.
- **CI job 4 — dependency audit:** `pip-audit` / `osv-scanner`.

## 6. Evidence hygiene rules (engine-level, already present — keep)

- Redactor registered with every credential the run obtains; all evidence
  writers redact before persist (`core/secrets.py` + `core/run_context.py`).
- Screenshots only captured when the page has content (V1.2 §26) — also
  minimizes accidental secret screenshots.
- Findings/reports are written under run-scoped dirs with a run id; the
  standalone repo keeps them gitignored.
- DSN policy never prints or stores the resolved DSN (V1.2 §DB).

## 7. Repository hygiene for the current CarbonTally repo (no deletion now)

For the migration, the following should be EXCLUDED from the standalone
repo (do not delete them here):

- `local_backups/` (live data dumps) — repo root
- `.local-demo-credentials.md` — repo root
- `qa_harness/evidence/`, `qa_harness/findings/`, `qa_harness/reports/`
- `qa_harness/.pytest_cache/`, `*.egg-info/`
- `tools/seed_investor_demo/` manifests referencing real demo identities
  (profile should reference them, not embed)

## 8. Reporting-sensitive-data policy

- Generated reports in the standalone repo are templates; the profile's
  report section may redact evidence paths or keep them relative.
- The README and reports must state: "Reports may contain application data.
  Do not publish raw reports."

## 9. Action items (future, after PO authorization)

1. Write `.gitignore` per §3 into the standalone repo.
2. Run the §4 scan on the prepared tree.
3. Add §5 CI jobs.
4. Sanitize `profiles/carbontally/` so it references (not embeds) the
   private identity manifest.
5. Add `NOTICE` documenting that CarbonTally is the first reference profile.

---

# Independent Audit Swarm additions (dual-tool release)

The checklist above covers the QA Harness. These items are specific to
`independent_audit/` and to releasing the two tools together.

## Current state (verified 2026-08-31)

| Item | Status |
|---|---|
| `independent_audit/.gitignore` | Present and correct: `config/keys.json`, `*.cred.json`, `reports/evidence|agents|screenshots|pages|*.md|findings.json|cost.json|run_meta.json`, `__pycache__`, `.pytest_cache`, `browser_driver/node_modules` |
| `config/keys.example.json` | Placeholder only (`sk-or-v1-REPLACE_ME`) — safe, but keep as an `.example` template and ensure it is never used as a real key path |
| `browser_driver/driver.mjs` | Credentials via `IA_CREDENTIALS_JSON` env only; never written to disk or evidence — keep this invariant |
| `ia_core/redact.py` | Covers JWTs, `sb_secret_*`, `sb_publishable_*`, OpenRouter keys, signed-URL tokens, DSNs, generic secrets — keep; add any new provider keys as patterns |
| `qa_harness/.gitignore` | **MISSING** — `qa_harness/` currently has no `.gitignore`; its `evidence/`, `findings/`, `reports/`, `.venv/`, `.pytest_cache/`, `*.egg-info/` must never be committed. **Release blocker.** |
| Both trees | Currently **untracked** in the CarbonTally repo (`?? qa_harness/`, `?? independent_audit/`) — nothing is at risk of a stray commit today, but this changes the moment either tree is staged |
| `.local-demo-credentials.md` | Gitignored (`/.local-demo-credentials.md`) — never copy into the standalone repo |
| Hardcoded secrets in source | None found (scan above; only regex patterns and fake test tokens) |
| Test tokens | `tests/*` contain intentionally fake JWTs/Supabase keys — fine, but the CI secret scanner must whitelist them explicitly (path-based) so it does not flag every PR |

## Additional release-blocker checklist (dual tool)

- [ ] Add `qa_harness/.gitignore` (rules from §3) before any commit of `qa_harness/`.
- [ ] Rename/neutralize: package name `carbontally-qa-harness` → `saas-qa-harness`; `run_audit.py` description; `ia_core/prompts.py`, `ia_core/report.py`, `orchestrator.py` CarbonTally wording; `reports/generator.py` "# CarbonTally QA —" titles.
- [ ] Move all profile data (incl. `independent_audit/config/default_config.json`) into `profiles/<app>/`; engine defaults must not name CarbonTally.
- [ ] Confirm the `ia_core/isolation.py` default blocklist no longer names CarbonTally repo paths (move to profile or generic patterns).
- [ ] Secret scan fresh clone (both packages) with the test-token path whitelist.
- [ ] Confirm no runtime evidence dirs exist in the fresh clone.
- [ ] OCR-scan a representative screenshot before deciding whether any sample screenshot ships in docs.
- [ ] PO decision: does `profiles/carbontally/` ship publicly (reference implementation) or as a private profile package?

## Evidence hygiene reminders that already hold in both tools

- DSN resolution prints nothing and stores nothing (verified for
  `db_collector`; `-w` psql, DSN+password become redaction phrases).
- Browser sessions are never serialized with tokens (`to_safe_dict` in the
  harness; env-injected credentials in the driver).
- Reports/findings carry run ids and are gitignored in both tools.
