# SaaS QA Harness — README (Draft)

> **Draft for review.** This is the proposed README for the standalone
> open-source project. It does not replace the current CarbonTally QA
> Harness README.

---

## 1. What the project is

**SaaS QA Harness** is a free, open-source, read-only QA / Application
Assurance framework for SaaS applications. It inspects an application across
many layers — database, RLS, API contract, authentication, authorization,
browser UI/UX, responsiveness, accessibility, workflows, evidence, and
reporting — and produces deterministic, evidence-backed findings.

It was born from the CarbonTally QA Harness V1.2 and is built to be generic:
CarbonTally is one *application profile*, not the identity of the framework.

## 2. What problem it solves

SaaS teams often audit their application ad hoc: spreadsheets of
checklists, screenshots pasted into tickets, "it worked on my machine".
This framework gives you:

- a repeatable, read-only audit of the whole stack,
- honest results (no fake PASS, no silent SKIP),
- evidence (API responses, console, network, screenshots) attached to every
  finding,
- deterministic output that does not depend on an AI model,
- application knowledge isolated in a profile you can version and share.

## 3. What it tests

| Layer | Checks |
|---|---|
| Database | schema inventory, tables, columns, types, nullability, PK/FK, indexes, unique/check constraints, RLS state + policies, migrations, orphan records, duplicate keys, impossible statuses |
| API | OpenAPI contract, route inventory, status codes, request validation, authentication, authorization matrix, tenant isolation, safe negative probes, security boundaries |
| Browser | anonymous + authenticated route sweeps, persona sweeps, login verification, route protection, console/network errors, responsive viewports, axe accessibility, screenshots |
| Workflows | declarative end-to-end flows (upload → processing → emissions → report) with persisted-state verification |
| Reporting | normalized findings, deduplication, severity, executive/master/findings reports, optional issue backlog |

## 4. What it does NOT guarantee

- It does **not** prove an application is secure or bug-free. It reports
  what it observes and marks what it cannot test.
- It does **not** replace penetration testing or a human review.
- It does **not** write to your application by default; mutation tests are
  an explicit opt-in with isolated, tagged, cleaned-up records.
- AI analysis is optional and **never** authoritative by itself.

## 5. Architecture

```
GENERIC ENGINE  +  APPLICATION PROFILE  +  TARGET ENVIRONMENT
                  +  CREDENTIAL PROVIDER  +  OPTIONAL AI PROVIDER
```

The engine contains no application business logic. Everything specific —
roles, routes, workflows, DB expectations, API probes, identities — lives in
a profile. See `docs/` and the profile spec.

## 6. Safety model

- **Read-only by default.** The engine never mutates the application unless
  you explicitly opt into a mutation test, and mutation tests create only
  tagged records they later clean up.
- **No accidental mutation.** Mutation requires a separate flag and a
  profile-declared mutation scope; if safe mutation cannot be guaranteed
  the run reports `BLOCKED — SAFE MUTATION NOT AVAILABLE`.
- **No destructive actions.** The framework never resets, truncates, or
  drops anything, and never deletes data.

## 7. Read-only behavior

Every collector uses read-only queries/requests. DB collectors are
SELECT-only (enforced in code). API probes use safe bodies for deny-gated
POSTs so a correct application returns 403 before any write. Writes with an
"allow" expectation are SKIPPED with an explicit reason.

## 8. Supported technologies

- Python 3.10+ (engine)
- PostgreSQL / Supabase (database QA)
- OpenAPI 3.x (contract QA)
- Any browser automation via Playwright (Chromium)
- axe-core (accessibility)
- Any OpenAI-compatible chat API (optional AI analysis)

## 9. Installation

```bash
pip install saas-qa-harness          # core (recommended: pipx)
# optional extras
pip install "saas-qa-harness[browser]"   # Playwright browser QA
pip install "saas-qa-harness[ai]"        # optional AI analysis
playwright install chromium
```

## 10. Configuration

```bash
qa-harness init my-app
```

This scaffolds `profiles/my-app/`. Edit `profile.yaml`, `roles.yaml`,
`routes.yaml`, `workflows.yaml`, `api_probes.yaml`, `db_expectations.yaml`,
`table_rules.yaml`. Every file is optional except `profile.yaml`; the
engine applies generic defaults for the rest.

```bash
qa-harness preflight                 # validates profile, env, tools
```

## 11. Credentials setup

Passwords and tokens are **never** in profiles or source code. The profile
declares a credential provider:

```yaml
identities:
  credential:
    provider: env             # env | file | secret_manager (future)
    env_var: MY_APP_DEMO_PASSWORD
```

- **env:** export `MY_APP_DEMO_PASSWORD=...` before running.
- **file:** a gitignored credentials file (JSON/YAML) whose format is
  documented in `docs/credentials.md`.

The engine registers every credential it obtains with its redactor; secrets
cannot appear in reports, evidence, logs, or console output.

## 12. Running a first audit

```bash
qa-harness run --no-ai          # deterministic QA (no model calls)
qa-harness run                  # deterministic QA + optional AI analysis
qa-harness report               # regenerate reports from the last run
```

Exit codes: `0` all checks ran and no defect found; `1` defects found;
`2` usage error; `3` tool unavailable; `4` read-only violation would be
needed. See `docs/exit-codes.md`.

## 13. Understanding results

- `reports/latest/MASTER_REPORT.md` — run metadata, coverage, verdict.
- `reports/latest/FINDINGS.md` — every finding with evidence and
  reproduction.
- `reports/latest/EXECUTIVE_SUMMARY.md` — counts by severity/area.
- Verdict vocabulary: `ACCEPTED`, `ACCEPTED WITH CONDITIONS`,
  `NOT ACCEPTED`, `UNVERIFIED`. The harness never claims acceptance merely
  because tests were incomplete.

Findings are classified:

| Classification | Meaning |
|---|---|
| `REAL` / `APPLICATION_DEFECT` | confirmed defect with deterministic evidence |
| `RE-VERIFY` | candidate; needs one confirming run |
| `INCONCLUSIVE` | probe could not exercise the intended behavior |
| `HARNESS_CONTRACT_DEFECT` | the harness itself sent a bad request (not an app defect) |
| `HARNESS_RUNTIME_ERROR` | harness failed; evidence is not trusted |
| `SKIPPED` / `BLOCKED` | not run (tool unavailable / safety boundary) |
| `PO_DECISION_REQUIRED` | ambiguous requirement |

## 14. Evidence structure

```
evidence/<run-id>/
  api/          redacted API request/response payloads
  db/           schema, RLS, integrity, index, constraint payloads
  console/      browser console logs
  network/      network request summaries
  screenshots/  page captures (only when the page has content)
  traces/       Playwright traces
  videos/       Playwright videos
evidence/registry.json   run → evidence index
```

Screenshots are captured only when a page is ready; the harness refuses
blank/loading captures.

## 15. AI optionality

- `qa-harness run --no-ai` needs no API key and produces the full report.
- With a key, the optional AI layer analyzes deterministic findings
  (prioritization, correlation, discovery). AI findings are never
  automatically confirmed defects.
- Provider-neutral: configure any OpenAI-compatible endpoint
  (`SAAS_QA_AI_BASE_URL`, `SAAS_QA_AI_API_KEY`, `SAAS_QA_AI_MODEL`).

## 16. Application profiles

A profile is a directory of YAML (+ optional `adapter.py`) describing one
application: targets, roles, routes, workflows, DB expectations, API
probes, table rules, report identity. The engine consumes profiles through
a validated contract (`docs/APPLICATION_PROFILE_SPEC.md`).

The repository ships `profiles/generic/` (example) and, if authorized, the
CarbonTally profile as the first real reference implementation.

## 17. Creating a new application profile

1. `qa-harness init my-app`
2. Fill `profile.yaml`: name, frontend/API URLs, auth mode.
3. Add roles + routes (copy from the generic example, adjust).
4. Add workflows for your main user journeys.
5. Add API probes for authorization boundaries you care about.
6. Add DB expectations if you run database QA.
7. Add identities (role/tenant/count; no passwords) + configure the
   credential provider.
8. `qa-harness preflight && qa-harness run --no-ai`.

## 18. Database configuration

- Set the DSN via environment (`DATABASE_URL` or `SUPABASE_DB_URL`) or an
  explicit `--db-dsn`; the engine never guesses and never prints the DSN.
- If no DSN is available the database stage reports
  `DB UNAVAILABLE` and the rest of the run continues.

## 19. API configuration

- Point `api_url` at your API; the engine discovers OpenAPI (`/openapi.json`
  or configured path).
- Declare important endpoints + negative-authz cases in `api_probes.yaml`.

## 20. Browser configuration

- `frontend_url` + auth mode + selectors in `profile.yaml`.
- Viewports and thresholds in `config/example/ux_rules.yaml`.

## 21. Workflow configuration

- Declarative steps in `workflows.yaml`; action→endpoint bindings in
  `api_probes.yaml`; persisted-state verification happens automatically for
  `verify_persisted: true` steps.

## 22. Security testing

- The framework is an assurance tool, not an exploit tool. It checks
  authorization boundaries, tenant isolation, route protection, RLS, and
  contract validity with safe, read-only probes.
- For active security testing, use dedicated tools (e.g. OWASP ZAP); the
  harness reports `SKIPPED — TOOL UNAVAILABLE` for optional tools it cannot
  use.

## 23. CI/CD usage

```bash
# in CI (read-only against a preview/staging environment):
qa-harness preflight
qa-harness run --no-ai
# fail the build on P0/P1 REAL findings:
qa-harness report --fail-on P0,P1
```

## 24. Troubleshooting

- `auth=AUTHENTICATION_FAILURE` → check credentials provider + app gate.
- `auth=INCONCLUSIVE` → the browser left /login but no session was
  confirmed; check selectors and session signal.
- `DB UNAVAILABLE` → DSN not resolvable; set `DATABASE_URL`.
- `SKIPPED — TOOL UNAVAILABLE` → install the optional extra.
- `HARNESS_CONTRACT_DEFECT` → the profile sends a bad request; fix the
  profile, not the app.

## 25. Limitations

- Read-only by default; mutation scenarios are limited by the safety model.
- Browser QA depends on stable selectors and the app's SPA behavior.
- DB QA currently targets PostgreSQL/Supabase-family databases.
- Deterministic coverage is as good as the profile's rules.
- Historical memory (Hindsight) is optional and never authoritative.

## 26. Contributing

See `CONTRIBUTING.md` (to be written): report issues, add providers, add
generic rules, improve docs. No CarbonTally-specific changes belong in the
engine.

## 27. License

[License TBD — see the portability audit §Licensing. Recommendation:
Apache-2.0. CarbonTally is the first reference application profile; its
profile data ships under the same license or as a separate artifact per PO
decision.]

---

# Appendix — the second tool: Audit Swarm (AI-optional analysis)

This README draft describes the QA Harness. The open-source project ships a
**second, independent tool**: the **Audit Swarm**. They share the
`saas-assurance-contracts` package and the same application-profile format.

## What the Audit Swarm adds

The QA Harness produces deterministic evidence and findings. The Audit Swarm
**interprets** that evidence with an optional AI layer — correlation,
contradiction detection, architecture/UX/security analysis, prioritization
and a final judgment. It can also collect its own evidence (DB catalog, API
contract, frontend map, browser pages).

```
qa-harness run --no-ai          # deterministic evidence + findings
        │
        ▼
   evidence/  (canonical EvidencePacket)
        │
audit-swarm analyze ./evidence [--no-ai | --provider openrouter]
        │
        ▼
   findings.json + FINAL report  (AI findings are labeled, never auto-confirmed)
```

## Key properties

- **AI-optional.** `audit-swarm analyze --no-ai` runs the deterministic
  cross-check and judge stages only.
- **Provider-neutral.** OpenRouter today; OpenAI/Anthropic/local adapters
  via the same `Provider` interface. No provider is a hard dependency.
- **Honest evidence.** Every finding cites an `EvidenceReference`
  (evidence_id + sha256). AI findings carry `ai_generated: true` and
  `confidence`; they are never promoted to `CONFIRMED` automatically.
- **Read-only** and **fresh-start**: it never mutates the target and never
  reads historical audit reports as truth.

## Install & run

```bash
pip install saas-qa-harness saas-audit-swarm
qa-harness init my-app
qa-harness preflight my-app
qa-harness run --no-ai                 # → evidence/ + findings.json
audit-swarm analyze ./evidence          # → findings.json + reports
```

Or one entry point: `saas-assurance run-qa <app>` / `saas-assurance analyze <evidence-dir>`.

## Boundaries (what each tool is for)

| You want | Use |
|---|---|
| Repeatable deterministic regression QA, verdicts | `qa-harness` |
| Independent AI-assisted defect discovery & prioritization | `audit-swarm` |
| Both, with shared evidence | run `qa-harness` then `audit-swarm analyze ./evidence` |

The QA Harness must work with **zero AI**; the Audit Swarm treats AI as an
optional enhancement. Neither tool depends on the other to function.
