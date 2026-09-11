# Portability Matrix — QA Harness V1.2 AND Independent Audit Swarm V1

File/module-by-module classification of `qa_harness/` (Part 1) and
`independent_audit/` (Part 2) for conversion into standalone generic SaaS
QA/assurance tools.

## Classification legend

| Class | Meaning |
|---|---|
| **A — GENERIC** | Already reusable by arbitrary SaaS applications (no CarbonTally knowledge). |
| **B — PROFILE** | CarbonTally-specific product knowledge that should move into an application profile. |
| **C — COUPLED** | Generic engine containing embedded CarbonTally assumptions (needs de-coupling). |
| **D — SECURITY/SENSITIVE** | Credentials, credential handling, secrets, runtime data, sensitive evidence. |
| **E — TEST INFRA** | Generic test infrastructure. |
| **F — DOCUMENTATION** | Documentation requiring separation/rewrite. |
| **G — DEAD/REDUNDANT** | Apparently unnecessary, duplicated, obsolete, or legacy. |

A file may carry a primary class and secondary flags (e.g. `A/D` = generic
engine + sensitive data handling). `Refactor` = whether code change is
required to make it generic (YES / MINOR / NO). `Risk` = LOW / MED / HIGH
(the risk of breaking current CarbonTally capability during refactor).

Counts (source files, excluding `.venv`, caches, `egg-info`, runtime dirs):

- Python modules (non-test): **96**
- Config/docs/non-Python: **19**
- Test files: **26** + 2 fixtures
- Totals below cover the non-test modules + configs; tests are classified as one group.

---

## 1. `core/` — engine core

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `core/findings.py` | **A** | Finding model, classifications, normalization, deduplication — app-agnostic | none | none | `saas_qa/core/findings.py` | NO | LOW |
| `core/evidence.py` | **A** | Evidence path/store + registry | none | none | `saas_qa/core/evidence.py` | NO | LOW |
| `core/secrets.py` | **A/D** | Redactor; lists env var name `CARBON_TALLY_DEMO_PASSWORD` | one env name in a redaction list | env name should come from profile, not core | `saas_qa/core/redaction.py` | MINOR | LOW |
| `core/safety.py` | **A** | Read-only enforcement, mutation guards | none | none | `saas_qa/core/safety.py` | NO | LOW |
| `core/status.py` | **A** | `ToolUnavailable`, exit codes, skip states | none | none | `saas_qa/core/status.py` | NO | LOW |
| `core/config.py` | **A** | `TargetEnv`, config loading | default local URLs (localhost:3000/8050) | defaults belong in profile/example | `saas_qa/core/config.py` (profile-driven) | MINOR | LOW |
| `core/credentials.py` | **D** | Demo-credential file parsing; hard-codes `demo.carbontally.local` regex + `CARBON_TALLY_DEMO_PASSWORD` | domain + env name + email pattern | must become a generic credential-provider contract; CT parsing moves to profile | `saas_qa/core/credentials.py` (interface) + `saas_qa/providers/credential_file.py` | YES | MED |
| `core/run_context.py` | **C** | Orchestrates run; loads demo credentials; environment model | env defaults, credential loading, report naming | should take profile + environment + credential provider as inputs | `saas_qa/core/run_context.py` | YES | MED |
| `core/__init__.py` | A | package init | none | none | — | NO | LOW |

## 2. `identities/` — identity model

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `identities/loader.py` | **B** | Hard-coded `DEMO_DOMAIN=demo.carbontally.local`, `TEST_DOMAIN`, counts (1183), `REPRESENTATIVE_EMAILS` map | everything | the entire identity population is CT demo data | `profiles/carbontally/identities.py` + `saas_qa/identities/loader.py` (generic) | YES | MED |
| `identities/context.py` | **B/C** | Persona→workspace/landing model | persona/workspace vocabulary is CT | generic role vocabulary + profile-supplied mappings | `saas_qa/identities/context.py` (generic) + profile data | YES | MED |
| `identities/resolver.py` | **A** | by-email lookup over a manifest | works on whatever manifest it is given | none | `saas_qa/identities/resolver.py` | NO | LOW |
| `identities/selectors.py` | **B** | Generates emails like `owner.demo{index:04d}@demo.carbontally.local` | email pattern is CT | pattern belongs in profile (generic "selector policy") | `saas_qa/identities/selectors.py` (policy-driven) | YES | MED |

## 3. `db/` — database QA

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `db/schema_inventory.py` | **C** | Generic enumerator BUT `EXPECTED_TABLES` + per-table column expectations are CarbonTally | 20+ CT table names + columns | expectation list must come from profile | `saas_qa/db/schema_inventory.py` (expectations injected) + `profiles/carbontally/db_expectations.py` | YES | MED |
| `db/integrity.py` | **C** | Generic integrity engine but `INT-ORPHAN-*` / `INT-DUP-*` rules hard-code CT tables/columns | CT table names | rules must come from profile | `saas_qa/db/integrity.py` (rule-driven) + profile rules | YES | MED |
| `db/indexes.py` | **C** | Expected-index list is CT | CT table/column names | from profile | `saas_qa/db/indexes.py` | YES | MED |
| `db/constraints.py` | **C** | Expected constraints are CT | CT table names | from profile | `saas_qa/db/constraints.py` | YES | MED |
| `db/rls.py` | **C** | RLS expectation table is CT | CT tables/policies | from profile | `saas_qa/db/rls.py` | YES | MED |
| `db/migrations.py` | **C** | Migration-count expectations are CT (36 migrations) | CT migration catalog | from profile | `saas_qa/db/migrations.py` | YES | MED |
| `db/discovery.py` | **A** | Generic SELECT-only resource discovery | none (returns None on missing tables) | none | `saas_qa/db/discovery.py` | NO | LOW |

## 4. `api/` — API QA

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `api/probe.py` | **C** | Probe engine is generic BUT `AUTHZ-1..N` specs hard-code `/api/v3/...` paths, `org_a/org_b` identities, demo emails | endpoints + identities | specs must come from profile | `saas_qa/api/probe.py` (spec-driven) + `profiles/carbontally/api_probes.py` | YES | MED |
| `api/session.py` | **A** | API session pool, token handling | none | none | `saas_qa/api/session.py` | NO | LOW |
| `api/contract.py` | **A** | OpenAPI contract inspection | none | none | `saas_qa/api/contract.py` | NO | LOW |
| `api/inventory.py` | **A** | API route inventory | none | none | `saas_qa/api/inventory.py` | NO | LOW |
| `api/authorization.py` | **A** | Generic allow/deny matrix runner | none (matrix data external) | none | `saas_qa/api/authorization.py` | NO | LOW |
| `api/security.py` | **C** | Security-boundary probes reference CT endpoints | endpoint list | from profile | `saas_qa/api/security.py` (profile-driven) | YES | MED |
| `api/workflows.py` | **C** | Workflow-probe bindings reference the CT action catalog | action→endpoint map | from profile | `saas_qa/api/workflows.py` (profile-driven) | YES | MED |

## 5. `browser/` — browser/UI QA

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `browser/playwright/controller.py` | **A** | Generic Playwright controller | none | none | `saas_qa/browser/controller.py` | NO | LOW |
| `browser/auth/session.py` | **C/D** | `demo_login` = GoTrue password grant; comments reference `@demo.carbontally.local` | auth provider + domain | auth mode must be profile-declared (GoTrue is one provider) | `saas_qa/browser/auth/` (provider registry) + profile | YES | MED |
| `browser/sweep.py` | **C** | Persona sweep engine; pulls `REPRESENTATIVE_EMAILS`, landing expectations | identities + landings | from profile | `saas_qa/browser/sweep.py` (profile-driven) | YES | MED |
| `browser/routes/navigator.py` | **A** | Route navigation + readiness | none | none | `saas_qa/browser/navigator.py` | NO | LOW |
| `browser/tables/auditor.py` | **A** | Generic table/grid auditor | none (rules external) | none | `saas_qa/browser/tables.py` | NO | LOW |
| `browser/responsive/auditor.py` | **A** | Responsive auditor; default base_url `http://localhost:3000` | default URL | default from profile | `saas_qa/browser/responsive.py` | MINOR | LOW |
| `browser/accessibility/axe.py` | **A** | axe-core runner | none | none | `saas_qa/browser/accessibility.py` | NO | LOW |
| `browser/workflows/driver.py` | **A** | Browser workflow driver | none (steps external) | none | `saas_qa/browser/workflow_driver.py` | NO | LOW |
| `browser/fixtures/generate.py` | **B** | Generates demo-identity fixture JSON (CT emails) | emails | from profile | `profiles/carbontally/fixtures.py` | YES | LOW |

## 6. `workflows/` — workflow engine

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `workflows/base.py` | **A** | `WorkflowStep`/`Workflow` dataclasses — declarative, app-agnostic | none | none | `saas_qa/workflows/model.py` | NO | LOW |
| `workflows/executor.py` | **A/C** | Executor is largely generic; imports probe engine + action vocabulary | action names (`upload_document`, `calculate`, …) | action→endpoint binding from profile | `saas_qa/workflows/executor.py` | YES | MED |
| `workflows/customer.py` | **B** | CT customer pipeline steps | CT workflow | profile | `profiles/carbontally/workflows/customer.py` | YES (move) | LOW |
| `workflows/consultant.py` | **B** | CT consultant workflow | CT | profile | `profiles/carbontally/workflows/consultant.py` | YES (move) | LOW |
| `workflows/client.py` | **B** | CT client workflow | CT | profile | `profiles/carbontally/workflows/client.py` | YES (move) | LOW |
| `workflows/pe.py` | **B** | CT processing-entity workflow | CT | profile | `profiles/carbontally/workflows/pe.py` | YES (move) | LOW |
| `workflows/operations.py` | **B** | CT internal-ops workflow | CT | profile | `profiles/carbontally/workflows/operations.py` | YES (move) | LOW |
| `workflows/admin.py` | **B** | CT admin workflow | CT | profile | `profiles/carbontally/workflows/admin.py` | YES (move) | LOW |
| `workflows/messaging.py` | **B** | CT messaging workflow | CT | profile | `profiles/carbontally/workflows/messaging.py` | YES (move) | LOW |

## 7. `rules/` — business/UX rules

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `rules/business.py` | **B** | "primary CarbonTally business expectations" | CT business rules | profile | `profiles/carbontally/business_rules.py` | YES (move) | LOW |
| `rules/security.py` | **B/C** | Security expectations; some CT-specific | CT boundaries | split generic/CT | `saas_qa/rules/security.py` + profile | YES | MED |
| `rules/ux.py` | **A** | Generic UX rules (workspace-position, loading/error/empty states) | none | none | `saas_qa/rules/ux.py` | NO | LOW |
| `rules/tables.py` | **A** | Generic table rules | none | none | `saas_qa/rules/tables.py` | NO | LOW |
| `rules/navigation.py` | **A** | Generic navigation rules | none | none | `saas_qa/rules/navigation.py` | NO | LOW |

## 8. `agents/` — AI layer

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `agents/base.py` | **C/D** | Agent base; `openrouter_available()` hard-codes `OPENROUTER_AGEN_SWARM_V1_API_KEY` | OpenRouter key name | provider-neutral gateway | `saas_qa/agents/base.py` + `saas_qa/ai/gateway.py` | YES | MED |
| `agents/swarm.py` | **C** | Hard-codes OpenRouter base URL + model | OpenRouter | provider config from env/profile | `saas_qa/agents/swarm.py` (provider configurable) | YES | MED |
| `agents/ux_agent.py` | A/B | Agent prompt references CT routes/personas | prompt content | generic prompt + profile context | `saas_qa/agents/ux_agent.py` | MINOR | LOW |
| `agents/workflow_agent.py` | A/B | same | prompt content | same | `saas_qa/agents/workflow_agent.py` | MINOR | LOW |
| `agents/security_agent.py` | A/B | same | prompt content | same | `saas_qa/agents/security_agent.py` | MINOR | LOW |
| `agents/api_agent.py` | A/B | same | prompt content | same | `saas_qa/agents/api_agent.py` | MINOR | LOW |
| `agents/judge_agent.py` | **A** | Final judge over deterministic findings | none | none | `saas_qa/agents/judge_agent.py` | NO | LOW |

## 9. `reports/` — reporting

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `reports/generator.py` | **C** | Generic report engine BUT filenames hard-coded `CARBONTALLY_QA_*` | report names | profile/template-driven names | `saas_qa/reports/generator.py` (names configurable) | YES | MED |
| `reports/backlog.py` | **C** | Cline backlog generator (project-specific convention) | "Cline" convention | generic issue-tracker output + adapter | `saas_qa/reports/backlog.py` (template per project) | YES | MED |

## 10. `scripts/` — CLI entry points

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `scripts/common.py` | **A** | Shared arg parsing (read-only flags) | none | none | `saas_qa/cli/common.py` | NO | LOW |
| `scripts/preflight.py` | **C** | Validates CT config + identity generation | CT identity checks | generic preflight + profile validators | `saas_qa/cli/preflight.py` | YES | MED |
| `scripts/run_db.py` | **C** | DB runner; DSN discovery; CT config defaults | env names | DSN policy generic + profile | `saas_qa/cli/run_db.py` | YES | MED |
| `scripts/run_api.py` | **C** | API runner; loads CT probe specs | probe specs | from profile | `saas_qa/cli/run_api.py` | YES | MED |
| `scripts/run_browser.py` | **C** | Browser runner; personas/landings | CT personas | from profile | `saas_qa/cli/run_browser.py` | YES | MED |
| `scripts/run_workflows.py` | **C** | Workflow runner; CT workflows | CT workflows | from profile | `saas_qa/cli/run_workflows.py` | YES | MED |
| `scripts/run_agents.py` | **A** | AI analysis entry | none (uses key env) | provider env generic | `saas_qa/cli/run_agents.py` | MINOR | LOW |
| `scripts/run_all.py` | **A/C** | Orchestrator; stage names generic; report bundle CT-named | report names | from profile | `saas_qa/cli/run_all.py` | MINOR | MED |
| `scripts/audit_openapi_bindings.py` | **A** | Static binding audit vs OpenAPI | none | none | `saas_qa/scripts/audit_openapi_bindings.py` | NO | LOW |
| `scripts/reclassify.py` | **A** | Calibration reclassification tool | none | none | `saas_qa/scripts/reclassify.py` | NO | LOW |

## 11. `config/` — configuration

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `config/qa_config.yaml` | **B/D** | CT master config (name, local env URLs, credential env names, domain) | CT | profile (may reference env names) | `profiles/carbontally/` + `config/example/` | move | LOW |
| `config/environments.yaml` | **B** | CT env definitions (localhost URLs, carbontally.co.uk) | CT URLs | profile (targets) | `profiles/carbontally/environments.yaml` | move | LOW |
| `config/roles.yaml` | **B** | CT role model + boundaries | CT | profile | `profiles/carbontally/roles.yaml` | move | LOW |
| `config/routes.yaml` | **B** | CT route catalog | CT | profile | `profiles/carbontally/routes.yaml` | move | LOW |
| `config/workflows.yaml` | **B** | CT workflow action lists | CT | profile | `profiles/carbontally/workflows.yaml` | move | LOW |
| `config/table_rules.yaml` | **B** | CT table expectations | CT | profile | `profiles/carbontally/table_rules.yaml` | move | LOW |
| `config/ux_rules.yaml` | **A** | Generic UX rules (viewports, thresholds) | none | none | `saas_qa/config/ux_rules.yaml` (defaults) | NO | LOW |
| `config/severity.yaml` | **A** | Generic severity vocabulary | none | none | `saas_qa/config/severity.yaml` | NO | LOW |
| `config/exclusions.yaml` | **B** | CT exclusion catalog | CT | profile | `profiles/carbontally/exclusions.yaml` | move | LOW |
| `config/loader.py` | **A** | YAML config loading | none | none | `saas_qa/config/loader.py` | NO | LOW |

## 12. Other

| File | Class | Why | CarbonTally dependency | Portability problem | Future location | Refactor | Risk |
|---|---|---|---|---|---|---|---|
| `findings/store.py` | **A** | raw/normalized/dedup persistence | none | none | `saas_qa/findings/store.py` | NO | LOW |
| `visual/axe/runner.py` | **G** | Thin wrapper duplicating `browser/accessibility/axe.py` (37 vs 104 lines) | none | duplicate a11y path | merge into browser a11y | YES (consolidate) | LOW |
| `pyproject.toml` | **C** | name `carbontally-qa-harness`, description, keywords | package identity | rename + CLI entry | `saas_qa/pyproject.toml` (recommended name) | YES | LOW |
| `requirements.txt` | **C** | CT-named header; deps are generic | naming only | rename + optional extras | `saas_qa/requirements*.txt` | MINOR | LOW |
| `Makefile` | **C** | CT-named help text; targets generic | naming only | rename | `saas_qa/Makefile` | MINOR | LOW |
| `README.md` | **F** | CT-specific usage docs | all | rewrite generic + profile docs | `saas_qa/README.md` + `profiles/carbontally/README.md` | YES | LOW |
| `carbontally_qa_harness.egg-info/` | **G** | Build artifact | — | exclude from repo | n/a (gitignore) | NO | LOW |
| `tests/` (26 files + fixtures) | **E** | Harness self-tests; fixtures contain CT emails (test_identities, test_browser_auth, sample_manifest) | fixtures | fixtures→profile or generic examples | `saas_qa/tests/` + profile tests | MINOR | LOW |
| `.pytest_cache/` | G | cache | — | exclude | n/a | NO | LOW |

## 13. Runtime data dirs (never committed)

| Path | Class | Notes |
|---|---|---|
| `evidence/` (api/db/console/network/screenshots/traces/videos) | **D** | May contain tokens, screenshots, PII. Must be gitignored. |
| `reports/latest/`, `reports/archive/` | **D** | Generated findings can contain sensitive details. Gitignore; only publish sanitized reports. |
| `findings/raw|normalized|deduplicated/` | **D** | Same. |
| `.local-demo-credentials.md` (repo root) | **D** | Already gitignored at repo root; must NEVER enter the standalone repo. |

---

## Summary counts (non-test source modules + configs)

| Class | Count (approx.) |
|---|---|
| A — GENERIC (no refactor) | ~26 modules |
| A with MINOR de-coupling | ~8 |
| B — PROFILE (move, not rewrite) | ~24 files |
| C — COUPLED (needs de-coupling) | ~30 modules |
| D — SECURITY/SENSITIVE (dedicated) | ~6 modules + runtime dirs |
| E — TEST INFRA | 26 test files + 2 fixtures |
| F — DOCUMENTATION | 1 (README) |
| G — DEAD/REDUNDANT | 2 (`visual/axe/runner.py`, egg-info) |

The majority of the **engine** (core, findings, evidence, safety, status,
navigator, auditors, session, contract, discovery, executor model) is
already generic. The CarbonTally coupling is concentrated in: (1) identity
population, (2) config YAMLs, (3) DB expectation rules, (4) API probe
specs, (5) workflow definitions, (6) report/bundle naming, (7) credential
file format, (8) AI provider env names.

---

# Part 2 — independent_audit/ matrix (Independent Audit Swarm V1)

Classification legend is the same (A–H). Source files only (tests are one
group; `reports/latest/` is runtime).

| Module | Class | Refactor | Notes |
|---|---|---|---|
| `ia_core/evidence.py` | A | NO | EvidencePacket with schema_version, sha256, redaction, prompt rendering. |
| `ia_core/schema.py` | A | NO | Strict finding schema + enums; generic. |
| `ia_core/normalize.py` | A | NO | Deterministic model-output enforcement. |
| `ia_core/dedupe.py` | A | NO | Deduplication. |
| `ia_core/redact.py` | D/A | NO | JWT/DSN/signed-URL/API-key patterns; generic. |
| `ia_core/cost.py` | A | NO | Model cost accounting; generic. |
| `ia_core/model_gateway.py` | A/D | MINOR | OpenRouter/OpenAI-compatible; provider-neutral transport; needs a formal `Provider` interface + extra providers (OpenAI/Anthropic/local). |
| `ia_core/report.py` | C | MINOR | Report writer; a few "CarbonTally" strings in prose. |
| `ia_core/readonly.py` | D/A | NO | Read-only SQL/HTTP guard; prose mentions CarbonTally; mechanism generic. |
| `ia_core/config.py` | C | MINOR | Config + `.env` discovery; default `checkpoint` is a CarbonTally commit SHA. |
| `ia_core/isolation.py` | C | MINOR | Fresh-start blocklist; defaults name CarbonTally repo dirs — move defaults to profile. |
| `ia_core/prompts.py` | C | MINOR | Role prompts; ground rules generic; "CarbonTally" wording genericizes to "target application". |
| `agents/roles.py` | A | NO | Evidence-kind-scoped role registry; fully generic. |
| `agents/runner.py` | A | NO | Deterministic runner. |
| `agents/crosscheck.py` | A | NO | Cross-check normalization. |
| `agents/final_judge.py` | A | NO | Final judge. |
| `collectors/db_collector.py` | A/D | NO | Generic catalog/RLS/integrity collector; generic DSN resolution. |
| `collectors/api_collector.py` | A | NO | OpenAPI/routes/probe collector; probes from config. |
| `collectors/frontend_collector.py` | A | NO | Route/component/API-map collector. |
| `collectors/browser_collector.py` | A | NO | Browser jobs builder. |
| `collectors/fresh_start.py` | A | NO | Repo map + blocklist enforcement. |
| `browser_driver/driver.mjs` | A/D | NO | Playwright evidence driver; credentials via env; read-only. |
| `orchestrator.py` | C | MINOR | Pipeline; report note references CarbonTally; otherwise generic. |
| `run_audit.py` | C | MINOR | CLI; description string + default checkpoint. |
| `config/default_config.json` | **B** | MOVE | The entire CarbonTally profile: checkpoint, repo dirs, URLs, personas, routes, viewports. |
| `config/keys.example.json` | A/D | NO | Placeholder template. |
| `.gitignore` | A | NO | Correct (keys, cred files, reports outputs). |
| `tests/*` | F | MINOR | 146 deterministic tests; some filenames/strings mention carbontally. |
| `README.md` | G | REWRITE | CarbonTally-specific. |
| `requirements.txt` | A | NO | Generic. |

## independent_audit summary counts

| Class | Count |
|---|---|
| A — GENERIC (no refactor) | ~24 files |
| C — COUPLED (MINOR de-coupling) | ~8 files |
| B — PROFILE (move to profile) | 1 file (`config/default_config.json`) |
| D — SECURITY/SENSITIVE | 4 (redact, readonly, model_gateway, driver) |
| E — TEST INFRA / runtime | 13 test files + `reports/latest/` |
| G — DOCUMENTATION | README |

**Portability estimate:** ~95 % generic now; the extraction effort is LOW —
move `default_config.json` data into a profile, genericize prompt/report
wording and default checkpoint/blocklist, and rename CLI/README strings.
