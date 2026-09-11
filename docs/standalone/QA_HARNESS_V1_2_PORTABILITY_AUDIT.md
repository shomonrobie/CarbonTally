# CarbonTally QA Harness V1.2 — Forensic Portability Audit

**Prepared for:** Product Owner review
**Scope:** `qa_harness/` as it exists at CarbonTally HEAD
`16391217103b98dcea520070c5a22c68f12fe607`
**Purpose:** Determine how to transform the CarbonTally QA Harness V1.2 into a
free, open-source, standalone, generic SaaS QA / Application Assurance
Framework while preserving CarbonTally's existing QA capability.
**Constraint honored:** zero application changes; this is an audit/blueprint
only. Nothing under `qa_harness/` was modified.

---

## 1. Executive summary

The harness is architecturally healthier than its name suggests. The core
engine — finding model, evidence, safety, redaction, DB/API/browser
auditors, workflow *model*, report engine — is written application-agnostically.
CarbonTally enters through **data and declarative configuration**: identity
populations, YAML catalogs, DB expectation rules, API probe specs, workflow
definitions, and report naming.

This means the portability task is primarily **boundary extraction**
(move CarbonTally data behind a profile interface) rather than engine
rewriting. The single most invasive exception is **identity/credential
loading**, where CarbonTally's demo-domain assumptions are hard-coded in
`identities/loader.py`, `identities/selectors.py`, `core/credentials.py`,
and `config/qa_config.yaml`.

The existing V1.2 calibration work (independent auth confirmation, honest
DB failure, harness-vs-app defect separation, RE-VERIFY classification)
must be carried into the standalone framework **verbatim** — they are the
trustworthiness foundation and they are already generic.

---

## 2. Method

- Every source file under `qa_harness/` was inspected and classified
  (full matrix: `PORTABILITY_MATRIX.md`).
- Direct coupling: all occurrences of `carbon` (case-insensitive),
  `demo.carbontally.local`, `test.carbontally.local`, `carbontally.co.uk`,
  `localhost:3000/8050`, `54425/54426`, `/api/v3`, `CARBON_TALLY_*` env
  names, and `OPENROUTER_AGEN_SWARM_V1_API_KEY` were located.
- Indirect coupling: fixed role names, route paths, table names, workflow
  action names, report filenames, and identity counts were located.
- The audit does **not** modify any file.

---

## 3. Complete coupling inventory

### 3.1 Direct CarbonTally coupling (by file)

| File(s) | Coupling |
|---|---|
| `identities/loader.py` | `DEMO_DOMAIN = "demo.carbontally.local"`, `TEST_DOMAIN = "test.carbontally.local"`, documented counts (1183 demo + 7 test), hard-coded emails (13 representatives + 6 OHD + 1 Cline probe) |
| `identities/selectors.py` | email templates `owner.demo{index:04d}@demo.carbontally.local`, `consultant.demo{index:04d}@…`, `pe-manager-{index}.demo@…`, `{persona}.demo@…` |
| `core/credentials.py` | env `CARBON_TALLY_DEMO_PASSWORD` / `DEMO_PASSWORD`; regex for `@demo.carbontally.local` emails in the credentials file table |
| `core/secrets.py` | redaction list includes `CARBON_TALLY_DEMO_PASSWORD` |
| `config/qa_config.yaml` | project name "CarbonTally QA Harness", local target URLs, `password_env: CARBON_TALLY_DEMO_PASSWORD`, `domain: demo.carbontally.local`, identity counts |
| `config/environments.yaml` | `http://localhost:3000`, `http://localhost:8050`, `http://127.0.0.1:54425`, production `https://carbontally.co.uk`, `api_prefix: /api/v3` |
| `config/roles.yaml` | full CT role model (customer_owner/admin/member/viewer, client_owner, consultant, pe_manager, pe_staff, internal_*, staff_admin, system_admin) + CT capability/boundary vocabulary |
| `config/routes.yaml` | CT route catalog (/, /login, /platform, /services, /pricing, /faq…, /home, /emissions, /documents, /processing, /review, /messaging, /issues, /notifications, /reports, /billing, /organization, /onboarding, /consultant, /ops) |
| `config/workflows.yaml` | CT workflow action lists (upload_document, storage_object, file_record, processing_job, ingestion, extraction, mapping, validation, calculation, evidence, review, approval, completed, emissions, reporting; automatic/manual processing; consultant; PE; ops; admin; messaging) |
| `config/table_rules.yaml`, `config/exclusions.yaml` | CT table expectations and exclusions |
| `db/schema_inventory.py` | `EXPECTED_TABLES` (organizations, organization_members, consultant_profiles, consultant_clients, staff_profiles, processing_entities, organization_files, upload_batches, manual_extraction_batches/items, emission_factors, customer_factors, calculation_snapshots, emissions_logs, issues, report_versions, conversations, conversation_participants, messages, notifications, processing_queue, …) + per-table expected columns |
| `db/integrity.py` | `INT-ORPHAN-1..8`, `INT-DUP-1..2` rules naming CT tables/columns (organization_files, manual_extraction_items, conversation_participants, …) |
| `db/indexes.py` | expected indexes on CT tables (upload_batches.organization_id, emissions_logs.organization_id, processing_queue.stage/entity_id, …) |
| `db/constraints.py`, `db/rls.py`, `db/migrations.py` | CT expected constraints, RLS policy expectations, migration count (36) |
| `api/probe.py` | `AUTHZ-1..N` probe specs with `/api/v3/documents`, `/api/v3/organizations`, `/api/v3/uploads`, `/api/v3/search`, `/api/v3/consultants/clients`, `/api/v3/ops/…`, `/api/v3/messaging/…`, `/api/v3/processing/…`, `/api/v3/settings/retention`, `/api/v3/commercial/config` + `customer_owner_b`-style demo identities |
| `api/security.py`, `api/workflows.py` | CT security-boundary and workflow-probe bindings |
| `browser/auth/session.py` | GoTrue password grant against local Supabase; docs reference `@demo.carbontally.local` population |
| `browser/sweep.py` | `REPRESENTATIVE_EMAILS` import; per-persona landing expectations |
| `browser/responsive/auditor.py` | default `base_url="http://localhost:3000"` |
| `browser/fixtures/generate.py` | generates fixture identities with CT emails |
| `workflows/{customer,consultant,client,pe,operations,admin,messaging}.py` | CT workflow definitions (action vocabulary, personas) |
| `rules/business.py` | "primary CarbonTally business expectations as regression targets" |
| `agents/*.py` | prompts reference CT routes/personas; `swarm.py`/`base.py` hard-code OpenRouter (`openrouter/auto`, `https://openrouter.ai/api/v1`, `OPENROUTER_AGEN_SWARM_V1_API_KEY`) |
| `reports/generator.py` | hard-coded filenames `CARBONTALLY_QA_MASTER_REPORT.md`, `CARBONTALLY_QA_EXECUTIVE_SUMMARY.md`, `CARBONTALLY_QA_FINDINGS.md` |
| `reports/backlog.py` | "Cline implementation backlog" convention (project-internal workflow) |
| `scripts/*.py` | orchestrate the above; `run_db.py` DSN env names; `preflight.py` validates CT identity generation |
| `pyproject.toml` | name `carbontally-qa-harness`, description/keywords |
| `requirements.txt`, `Makefile`, `README.md` | CT naming and CT-only docs |

### 3.2 Indirect coupling (does not say "CarbonTally")

- **Fixed role vocabulary** (`customer_owner`, `client_owner`, `pe_manager`,
  `internal_operator`, `staff_admin`, …) baked into `roles.yaml`, identity
  selectors, workflow personas, and agent prompts.
- **Fixed route paths** (`/home`, `/ops`, `/consultant`, `/onboarding`,
  `/documents`, `/processing`, `/review`, `/messaging`, …) in `routes.yaml`
  and sweep landings.
- **Fixed DB table names** in `db/*` expectation rules.
- **Fixed API paths** (`/api/v3/…`) in probe specs.
- **Fixed action vocabulary** (`upload_document`, `calculate`, `approve`,
  `customer-review`, …) in workflow definitions and executor.
- **Fixed organization model** (organization→members→roles, consultant→
  client, processing-entity boundaries) in `roles.yaml` boundaries and
  `rules/business.py`.
- **Fixed authentication assumption** — GoTrue/email-password in
  `browser/auth/session.py` and `api/session.py`.
- **Fixed identity counts** (1183, 7) in `loader.py` and `qa_config.yaml`.
- **Fixed demo email pattern** (`{role}.demo{NNNN}@demo.carbontally.local`).
- **Fixed report naming** (`CARBONTALLY_QA_*`) and the "Cline backlog"
  convention.
- **Fixed env names** (`CARBON_TALLY_DEMO_PASSWORD`,
  `OPENROUTER_AGEN_SWARM_V1_API_KEY`).
- **Hindsight-derived assumptions** — historical findings are encoded as
  comment/regression expectations in `rules/business.py` (e.g. "Historical
  defect SEC-1: viewer upload must be denied") and `roles.yaml` boundaries.
  These are *requirements* today, which is legitimate, but they must be
  clearly attributed to the CarbonTally profile, not the generic engine.

### 3.3 Coupling by kind — where the work is

| Kind | Volume | Move to profile? | Engine change needed? |
|---|---|---|---|
| Identity population (emails/counts/domains) | high | yes | yes — identity abstraction |
| Config YAMLs (roles/routes/workflows/tables/exclusions) | high | yes | minimal — already data-driven |
| DB expectation rules | medium | yes | yes — inject expectations |
| API probe specs | medium | yes | yes — spec-driven engine |
| Workflow definitions | medium | yes | minimal — declarative model exists |
| Report/bundle naming + backlog | low | yes | yes — configurable names/templates |
| Credential file format + env names | medium | yes | yes — credential-provider contract |
| AI provider binding (OpenRouter) | low | yes | yes — provider-neutral gateway |
| Agent prompt content | low | yes | minimal — inject profile context |

---

## 4. What is already generic (reusable as-is)

- `core/findings.py` — finding model, classification, normalization, dedup
- `core/evidence.py`, `core/secrets.py` (redaction core), `core/safety.py`,
  `core/status.py`
- `findings/store.py` — persistence
- `db/discovery.py` — SELECT-only resource discovery
- `api/session.py`, `api/contract.py`, `api/inventory.py`,
  `api/authorization.py` (matrix engine)
- `browser/playwright/controller.py`, `browser/routes/navigator.py`,
  `browser/tables/auditor.py`, `browser/responsive/auditor.py` (minor
  default), `browser/accessibility/axe.py`, `browser/workflows/driver.py`
- `workflows/base.py` (declarative step model), `workflows/executor.py`
  (largely)
- `rules/ux.py`, `rules/tables.py`, `rules/navigation.py`
- `config/loader.py`, `config/severity.yaml`, `config/ux_rules.yaml`
- `scripts/common.py`, `scripts/audit_openapi_bindings.py`,
  `scripts/reclassify.py`, `scripts/run_agents.py` (structure)
- `agents/judge_agent.py` (role), agent base concepts
- All V1.2 calibration guarantees (independent auth confirmation,
  HARNESS_CONTRACT_DEFECT vs APPLICATION_DEFECT, RE-VERIFY, read-only
  enforcement, honest DB-unavailable) — already generic mechanisms.

## 5. What must move to the CarbonTally profile (with zero engine loss)

| Area | Files |
|---|---|
| Identities | `identities/loader.py` data, `identities/selectors.py` patterns, `identities/context.py` mappings |
| Roles & boundaries | `config/roles.yaml` |
| Routes & landing | `config/routes.yaml` + sweep landing map |
| Workflows | `workflows/{customer,consultant,client,pe,operations,admin,messaging}.py`, `config/workflows.yaml` |
| DB expectations | `db/schema_inventory.py` EXPECTED_TABLES/columns, `db/integrity.py` rules, `db/indexes.py`, `db/constraints.py`, `db/rls.py`, `db/migrations.py`, `config/table_rules.yaml`, `config/exclusions.yaml` |
| API probes | `api/probe.py` AUTHZ specs, `api/security.py`, `api/workflows.py` bindings |
| Business rules | `rules/business.py`, parts of `rules/security.py` |
| Targets/env | `config/environments.yaml`, `config/qa_config.yaml` target section |
| Credentials | credentials file format (profile-owned), `CARBON_TALLY_DEMO_PASSWORD` env name |
| Report identity | report filenames, backlog template |
| Docs | `README.md` → generic + profile README |

## 6. What must stay generic in the engine (non-negotiable)

- Read-only default + mutation guards (`core/safety.py`)
- Secret redaction in ALL outputs (`core/secrets.py`)
- Independent auth confirmation; auth failure ≠ app findings
  (`browser/sweep.py` `_authenticate`, `browser/auth/session.py`)
- Honest DB-unavailable (`run_db.py` DSN policy)
- Harness-defect vs application-defect separation (classification model)
- INCONCLUSIVE / RE-VERIFY / PO_DECISION distinctions
- Evidence-backed findings; no fake PASS, no silent SKIP
- Deterministic QA without AI; AI optional and never authoritative
- Finding model, normalization, dedup, severity

## 7. Quality-requirement gap analysis (Part 23)

| Requirement | Current state | Gap / action |
|---|---|---|
| Deterministic tests | 253 pytest self-tests | keep; move CT fixtures to profile tests |
| Reproducible runs | run-id + git SHA in evidence | keep |
| Evidence-backed findings | evidence registry + paths | keep |
| Safe defaults | read-only default | keep |
| Secret redaction | redactor wired into run context + evidence | keep; add provider-level redaction for AI gateway |
| Clear failure states | exit codes + SKIPPED/TOOL UNAVAILABLE | keep |
| Honest unavailable | DB UNAVAILABLE note | keep |
| No fake PASS | PASS only on real probes | keep |
| No silent SKIP | every skip has a reason | keep |
| No silent DB failure | single HARNESS_RUNTIME_ERROR + no partial evidence | keep |
| No auth false positives | V1.2 `_authenticate` | keep (explicitly) |
| No mutation by default | safety module | keep |
| Configurable profiles | **new** | build profile contract (see `APPLICATION_PROFILE_SPEC.md`) |
| Provider-neutral AI | **new** | build gateway interface (see `STANDALONE_ARCHITECTURE.md` §AI) |
| Documented limitations | README + reports | extend to generic docs |

Current architecture **violations/risks** found:

1. **Identity/credential hard-coding** — the single biggest portability
   blocker (see §3.2). Must become a provider contract.
2. **`visual/axe/runner.py` duplication** — two a11y paths
   (`visual/axe/runner.py` wraps `browser/accessibility/axe.py`); risk of
   divergence. Consolidate.
3. **Report filenames hard-coded** — `CARBONTALLY_QA_*` in
   `reports/generator.py`; blocks generic branding.
4. **"Cline backlog" convention** hard-coded in `reports/backlog.py` —
   project-internal; make template-driven.
5. **OpenRouter binding** hard-coded in `agents/base.py` +
   `agents/swarm.py`; blocks provider-neutrality.
6. **Credentials file format is CT-owned** (`core/credentials.py` parses a
   markdown table of CT demo actors); generic credential providers needed.
7. **No `.gitignore` inside `qa_harness/`** — the standalone repo needs one
   before publication (runtime dirs hold screenshots/traces/reports).
8. **DB expectations spread across 5 modules + 2 YAMLs** — profile
   aggregation needed to keep a single source of truth.

## 8. Portability risk register (top)

| Risk | Level | Mitigation |
|---|---|---|
| Breaking CarbonTally QA capability during de-coupling | HIGH | Phased migration (see `MIGRATION_PLAN.md`); CT profile kept in-repo; run CT QA after every phase |
| Identity abstraction regressing V1.2 auth guarantees | HIGH | Freeze `browser/sweep.py` auth logic; only change *where* identity data comes from |
| Credential handling leaking during provider refactor | HIGH | Credential-provider interface returns redacted-safe objects; D/P separation maintained; secret-scan CI |
| DB expectation injection changing semantics | MED | Keep rule schema identical; only relocate data |
| Report name/template change confusing existing consumers | MED | Configurable names with CT profile preserving current filenames |
| AI gateway rewrite losing cost control | MED | Gateway interface includes cost tracking + "never auto-confirm" rule |

---

## 9. Conclusion

The harness is **~75% portable by structure**; the exact figure must be read
from `PORTABILITY_MATRIX.md` (counts there). The engine core is generic;
CarbonTally is expressed almost entirely as data. The realistic path to a
standalone framework is: define the profile contract → move CarbonTally data
behind it → generalize identity/credentials + report naming + AI gateway →
ship with CarbonTally as the first reference profile. No application change
is required at any step.
