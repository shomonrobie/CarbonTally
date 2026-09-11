# Migration Baseline Report — CarbonTally QA Harness V1.2 + Independent Audit Swarm V1

Captured at the start of the standalone extraction project. The existing
CarbonTally implementation is the frozen regression/reference target.

## Git state

| Field | Value |
|---|---|
| Branch | `main` |
| HEAD | `16391217103b98dcea520070c5a22c68f12fe607` |
| Working tree | contains pre-existing uncommitted changes (untouched) |

## QA Harness V1.2 (qa_harness/)

- **Self-tests:** 253 passed (`qa_harness/tests/`, 26 test files).
- **Trustworthiness guarantees (must not regress):**
  - read-only by default; mutation requires explicit opt-in
  - secret redaction in all outputs (core/secrets.py wired into run context)
  - independent authentication confirmation (browser `_authenticate`):
    URL-path extraction, independent credential check, localStorage/session
    key confirmation, persistence re-check, app-gate detection, typed
    AuthOutcome, downstream audits gated on success, one auth finding per
    persona
  - honest DB-unavailable state (DSN precedence; never prints; never guesses)
  - harness-vs-application defect separation
    (HARNESS_CONTRACT_DEFECT / HARNESS_RUNTIME_ERROR / APPLICATION_DEFECT /
    INCONCLUSIVE / RE-VERIFY / SKIPPED / BLOCKED / PO_DECISION_REQUIRED)
  - SELECT-only DB enforcement
  - evidence provenance (run id + registry)
  - optional AI analysis; deterministic QA without AI
- **Major capabilities:** DB schema/RLS/integrity/index/constraint/migration
  QA, OpenAPI contract + binding audit, API authorization probes (AUTHZ-*),
  browser persona/route sweeps, responsive, axe accessibility, table rules,
  workflow execution (read-only), evidence collection, finding
  normalization/dedup, reports (CARBONTALLY_QA_MASTER/EXECUTIVE_SUMMARY/
  FINDINGS, CLINE_IMPLEMENTATION_BACKLOG), calibration reclassification
  tool (reclassify.py), preflight.
- **CLI:** `scripts/{preflight,run_db,run_api,run_browser,run_workflows,
  run_agents,run_all,audit_openapi_bindings,reclassify}.py` with flags
  `--read-only --role --route --workflow --no-ai --no-visual --no-security`.
- **Known current observations (live-verified at this checkpoint):**
  anonymous visitor reaches `/home`; all personas land on `/onboarding`;
  console errors incl. realtime WebSocket failure; 36 repo migrations vs 0
  applied; missing `organization_members` unique constraint; `beta_users`
  RLS 0 policies/0 rows. These are app findings, not harness defects.

## Independent Audit Swarm V1 (independent_audit/)

- **Self-tests:** 146 passed (previous session); orchestrator + collectors +
  agents + ia_core (config/cost/dedupe/evidence/isolation/model_gateway/
  normalize/prompts/readonly/redact/report/schema).
- **Characteristics:** AI optional (`--no-ai` = collectors only), evidence
  driven, provenance aware, read-only collectors, DSN precedence with repo
  `.env` discovery, redaction, psql `-w`/`-F "\t"`, DbCollectorError →
  explicit `db_unavailable` note (run continues).
- **Collectors:** freshstart, api, frontend, browser, db. Agents:
  crosscheck, final_judge, roles, runner.

## Evidence/finding compatibility notes

- Finding model fields: id, category, severity, title, role, route,
  workflow, expected, actual, description, evidence[], reproduction[],
  business_impact, security_impact, root_cause, suggested_fix, status,
  related_cline_task, classification, source, timestamp, git_sha,
  normalized_key, dedup_group_size.
- Categories: DB, RLS, API, AUTH, WF, UI, UX, SEC, A11Y.
- Severity: P0–P3. Classifications: REAL / APPLICATION_DEFECT / RE-VERIFY /
  HARNESS_CONTRACT_DEFECT / HARNESS_RUNTIME_ERROR / AUTHENTICATION_FAILURE /
  INCONCLUSIVE / SKIPPED / BLOCKED / PO_DECISION_REQUIRED.
- Evidence dirs: api/, db/, console/, network/, screenshots/, traces/,
  videos/ + registry.
- The shared contracts package must map these V1.2 vocabularies onto the
  new canonical model with compatibility mappings.

## Scope of extraction (from portability audit)

- Generic engine (core, db collectors, api engine, browser engine,
  workflow model/executor, rules, findings pipeline, reports engine,
  redaction, safety) → `saas-assurance/packages/qa-harness`.
- CarbonTally data (config YAMLs, identities, DB/API/security expectations,
  workflows, report naming, env defs) → `profiles/carbontally`.
- Independent audit → `saas-assurance/packages/audit-swarm`.
- Shared contracts → `saas-assurance/packages/contracts`.
- Fictional proof profile → `profiles/acme-notes`.
