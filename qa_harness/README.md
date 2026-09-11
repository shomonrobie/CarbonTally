# CarbonTally QA Harness v1

A reusable, professional, **read-only** QA harness for independently verifying
CarbonTally V3 — covering database, schema, RLS, API, authentication,
authorization, workflow, browser, UI/UX, table/grid, responsive, accessibility,
messaging, processing, calculation, evidence-chain, reporting, security
boundary, role/capability and public-vs-authenticated application separation.

> **Status: BUILD-ONLY.** The harness is built and self-tested. It must NOT be
> run against CarbonTally until the current application implementation work
> reaches a stable checkpoint and a run is explicitly authorized. See
> `docs/audit/openhands/` for the audit history used as requirements context.

## Quick start

```bash
# 1. Create the harness environment (isolated; never touches the app)
cd qa_harness
uv venv .venv
uv pip install --python .venv/bin/python -e ".[core,test]"

# 2. Verify the environment (no application contact)
.venv/bin/python scripts/preflight.py

# 3. Run the harness self-tests (isolated; mocked fixtures only)
.venv/bin/python -m pytest
```

## Command interface (spec §34)

| Command | Purpose |
| --- | --- |
| `python qa_harness/scripts/preflight.py` | Validate environment, imports, optional tools, Git SHA (offline) |
| `python qa_harness/scripts/run_db.py` | Read-only database QA (schema, integrity, indexes, constraints, RLS, migrations) |
| `python qa_harness/scripts/run_api.py` | OpenAPI discovery, contract, authorization matrix + **authenticated API probes** |
| `python qa_harness/scripts/run_workflows.py` | **Executes read-only workflow steps** (mutation steps SKIPPED) |
| `python qa_harness/scripts/run_browser.py` | **Role sweeps**: login, landing, routes, tables, responsive, axe, separation |
| `python qa_harness/scripts/run_agents.py` | Optional OpenRouter AI analysis over deduplicated findings |
| `python qa_harness/scripts/run_all.py` | Full QA run (future) — shared RunContext, stages, dedup, reports, verdict |

Common flags: `--read-only` (default on) · `--role` · `--route` · `--workflow` ·
`--no-ai` · `--no-visual` · `--no-security` · `--env`

## V1.1 execution engine

V1.1 upgrades the build from declarations to an executable, read-only engine.
Every stage shares one `RunContext` (findings store, evidence registry,
secret redaction, run id, git SHA) and emits findings into the raw →
normalized → deduplicated pipeline.

- **API probes** (`api/probe.py`): a `ProbeSpec` expresses ACTOR / ACTION /
  RESOURCE / EXPECTED RESULT. `_classify` maps DENY/ALLOW/NO_PATH/HTTP codes
  to PASS/FAIL/WARNING so 401/403/404/409/422 are contextualized, never
  blanket-flagged. Cross-boundary pairs (customer↔customer, consultant↔
  consultant, PE↔PE, staff↔staff-admin, …) resolve deterministically from the
  demo identity population.
- **Mutation gating** (`config/qa_config.yaml → api_probe`): DENY-gated
  POST probes run with an empty body against non-existent resources (a
  correct app refuses before writing). ALLOW-gated mutation probes
  (upload/extract/map/validate/calculate/approve/create/…) are `SKIPPED —
  READ-ONLY MUTATION BLOCKED`.
- **Workflow executor** (`workflows/executor.py`): binds each workflow step
  to a read-only endpoint, verifies persisted state via the DB-backed API
  (never UI animations), and marks un-boundable steps (Realtime/WebSocket,
  browser-only) as SKIPPED.
- **Browser sweep** (`browser/sweep.py`): per role group — anonymous
  application-separation check, real-form login, landing verification,
  route visits with console/network/blank/JS-exception capture, table
  audits, responsive sweep on the authenticated context, axe scans.
- **Read-only safeguards** (`core/run_context.py`, `scripts/common.py`):
  default read-only; secrets redacted at emission and in evidence files;
  `BLOCKED — SAFE MUTATION NOT AVAILABLE` when a mutation stage is requested.

Standalone stage runs (`run_db.py`, `run_api.py`, …) own their RunContext and
produce their own report set; `run_all.py` owns one context across all stages.

## Layout

```
qa_harness/
├── config/          # YAML: environments, roles, routes, workflows, table/ux rules, severity, exclusions
├── core/            # findings model + normalization + dedup, secrets redaction, status, safety, evidence
├── identities/      # loader (full demo population), resolver, deterministic selectors
├── db/              # schema inventory, integrity, indexes, constraints, RLS, migrations (read-only)
├── api/             # endpoint inventory, contract, authorization matrix, security boundaries, state machines
├── browser/         # Playwright controller, auth sessions, navigator, table auditor, responsive, axe, workflow driver, fixtures
├── visual/axe/      # axe integration for visual QA
├── workflows/       # executable workflows: customer, consultant, client, pe, operations, admin, messaging
├── rules/           # declarative business, security, UX, table, navigation rules
├── agents/          # optional AI layer: UX/workflow/security/API analysts + final judge + swarm
├── evidence/        # screenshots, traces, videos, api, db, console, network (registry)
├── findings/        # raw → normalized → deduplicated finding stores
├── reports/         # latest/ + archive/: master, executive summary, findings, Cline backlog
├── scripts/         # CLI entry points (above)
└── tests/           # harness self-tests + fixtures (isolated; never contact the app)
```

## Identity population (spec §7)

`config/roles.yaml` + `identities/` model the **complete** demo population from
`tools/seed_investor_demo/DEMO_IDENTITIES.md` — not just 13 representative
personas. The generated model mirrors the live `auth.users` population
(read-only verified): **1183 demo identities** at `@demo.carbontally.local`
(200 direct customer roles + 911 client owners + 50 consultants + 6 PE +
5 internal staff + 11 legacy demo fixtures) plus **9 non-demo** audit/system
accounts (6 OHD `@test` + 3 selftest/fixture) = **1192 total**.
DEMO_IDENTITIES.md documented 1185 demo identities (verified 2026-08-28);
the live count drifted by 2, so the model uses live-verified counts and
reports the documented total separately. The resolver loads the full manifest
(17 representative personas); selectors choose deterministic representatives
and cross-boundary pairs (Customer A vs B, Client A vs B, Consultant A vs B,
PE A vs B, internal vs PE, viewer vs member, member vs admin, staff vs staff
admin, staff admin vs system admin).

Demo identities (`is_demo`, i.e. `@demo.carbontally.local`) are the only
identities authenticated with the shared `CARBON_TALLY_DEMO_PASSWORD`.
Legacy `@demo` fixtures are part of that population; OHD audit
(`@test.carbontally.local`) and system/selftest accounts are modelled for
completeness but are never authenticated with demo credentials.

Secrets are never hard-coded or logged. At run time the harness reads:

- demo credential — from the local credentials file or `CARBON_TALLY_DEMO_PASSWORD` (below)
- `OPENROUTER_AGEN_SWARM_V1_API_KEY` — optional AI analysis
- `SUPABASE_DB_URL` / `DATABASE_URL` — read-only DB access (kept separate from demo credentials)
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET` — presence checked only

## Local demo credential file (spec V1.2)

The shared local demo password is read automatically from the **gitignored**
repository-root file `.local-demo-credentials.md` — you no longer need to
export it in every shell. The identity model remains authoritative for the
population; the file only supplies the authentication secret.

- Location: `<repo-root>/.local-demo-credentials.md` (gitignored — never commit)
- Format (current): `Local-only password (shared): **<password>**`
- Representative emails in the markdown table are parsed for information only;
  identity selection still comes from `tools/seed_investor_demo/` and the
  harness identity loader.

Precedence (highest first):

1. `CARBON_TALLY_DEMO_PASSWORD` (or `DEMO_PASSWORD`) environment variable
2. local credentials file
3. no credential → authenticated QA is `SKIPPED — TOOL UNAVAILABLE` (never guessed)

Security rules:

- Only `@demo.carbontally.local` identities may request the shared password;
  audit, system fixtures and arbitrary emails are structurally rejected.
- The password is never written to findings, evidence, screenshots, traces,
  reports, logs, AI prompts, or config files.
- Database credentials are a separate concern (`DATABASE_URL` /
  `SUPABASE_DB_URL`) and are never placed in the demo credential file.

Verify credential availability without displaying it:

```bash
python -m qa_harness.scripts.preflight
# Demo credentials (values are never printed):
#   source: local credentials file   | environment | NOT SET
#   password: SET                    | NOT SET
```

## Database connection handling (V1.2)

`run_db` resolves the read-only QA DSN **without ever printing it**, in this
order (see `scripts/run_db.py:_resolve_connection`):

1. `SUPABASE_DB_URL` (operator-provided)
2. `DATABASE_URL` (the configured `postgres_dsn_env`, default)
3. `POSTGRES_PASSWORD`-based structured build (host/port/db from config)
4. local `supabase status --output json` discovery — **local environment only**
   and gated by `database.allow_supabase_status_discovery` in
   `qa_config.yaml`. The raw CLI output contains keys; it is parsed
   in-process and never logged or stored.

DB QA is purely **read-only SELECT / catalog inspection**. If the database is
unreachable or the driver is missing the stage prints
`SKIPPED — DATABASE UNREACHABLE` / `SKIPPED — TOOL UNAVAILABLE` and the run
continues; DB QA failure never breaks API/workflow/browser stages.

**Resource discovery** (`qa_harness/db/discovery.py`, gated by
`database.resource_discovery`) performs parameterized SELECT-only lookups
(e.g. a real conversation id for a participant) so resource-bound workflow
probes either run against a real resource or SKIP with an explicit reason —
never a meaningless fake-id 404. Missing tables/columns degrade to `None`
(probe SKIPs), never an exception.

## Finding classification (V1.2 calibration)

Every finding carries a `classification`:

- `REAL` — verified app defect (counts toward the verdict).
- `RE-VERIFY` — candidate app finding needing one confirming run.
- `HARNESS_CONTRACT_DEFECT` — the harness itself sent a contract-violating
  request (missing required param, wrong resource binding). **Not an app
  defect**; reported in a separate calibration section and never counted.
- `INCONCLUSIVE` — the probe could not exercise the intended gate (e.g.
  422-on-deny because validation precedes authz). Never counted.
- `SKIPPED` / `BLOCKED` / `PO_DECISION_REQUIRED` — not run / read-only
  boundary / ambiguous requirement.

Only `REAL` + `RE-VERIFY` count toward the acceptance verdict and the Cline
backlog. Maintain the bindings with the static contract audit:

```bash
python qa_harness/scripts/audit_openapi_bindings.py [openapi_url]
```

**Reclassifying a previous run after a harness fix.** When a harness defect
is fixed, a prior run's findings that depended on the defective behavior
must be marked `RE-VERIFY` (never silently deleted, never trusted as-is).
`reclassify.py` preserves every finding and all evidence and only changes
the classification plus a `[calibration]` note:

```bash
python qa_harness/scripts/reclassify.py \
    --source run_browser.py \
    --classification RE-VERIFY \
    --reason "generated from an unauthenticated /login page (V1.2 full-URL login detection bug); re-verify after the fix"
```

Use `--dry-run` first; `--no-reports` skips report regeneration. After
reclassifying, `reports/latest/` is regenerated from the store with an
`UNVERIFIED` verdict (it is not a fresh application run). See
`reports/latest/CARBONTALLY_QA_HARNESS_V1.2_FIRST_RUN_CALIBRATION_REPORT.md`
for the first application of this tool.

## Finding model & severity (spec §28–§29)

Normalized findings carry: ID (`QA-DB-xxx`, `QA-RLS-xxx`, `QA-API-xxx`,
`QA-AUTH-xxx`, `QA-WF-xxx`, `QA-UI-xxx`, `QA-UX-xxx`, `QA-SEC-xxx`,
`QA-A11Y-xxx`), category, severity (P0–P3), role, route, workflow, expected,
actual, description, evidence, reproduction, business/security impact, root
cause, suggested fix, status, related Cline task, source, timestamp, Git SHA.

Severity: **P0** security breach/cross-tenant leak/auth bypass/destructive
corruption · **P1** core workflow blocked (calculation/approval/consultant
operability/critical admin/messaging) · **P2** major degradation/missing
operational controls/major UX · **P3** minor UX/copy/cosmetic/a11y.

Deduplication normalizes phrasing ("No pagination in document table" →
"Documents table lacks pagination") while preserving all evidence.

## Safety (spec §33)

Default mode is **READ ONLY**. Any future mutation test must explicitly
declare itself, use isolated QA-tagged records, clean up only its own records,
verify cleanup, never delete investor-demo data and never reset the database.
If safe mutation cannot be guaranteed the run reports:

```
BLOCKED — SAFE MUTATION NOT AVAILABLE
```

## Tool handling (spec §36)

Playwright/Chromium, axe, Schemathesis, pgTAP, OWASP ZAP and OpenRouter are
all **optional**. When unavailable the harness prints
`SKIPPED — TOOL UNAVAILABLE` and continues; it never crashes on a missing
tool.

## Reports (spec §31–§32)

`reports/latest/` contains the master report, executive summary, findings and
a generated `CLINE_IMPLEMENTATION_BACKLOG.md`; previous runs are archived to
`reports/archive/`. Acceptance verdicts are deterministic:

- `NOT ACCEPTED` — any P0/P1 finding
- `UNVERIFIED` — core areas not tested (never claims acceptance from incomplete tests)
- `ACCEPTED WITH CONDITIONS` — only P2s remain, all areas tested
- `ACCEPTED` — clean, all areas tested

## No secret leaks (spec §37)

Tokens, passwords, service keys and signed URLs are redacted from reports,
screenshots, logs, Git and console output by `core/secrets.py`.
