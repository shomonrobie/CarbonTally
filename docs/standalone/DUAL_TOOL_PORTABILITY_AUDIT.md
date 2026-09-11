# DUAL-TOOL PORTABILITY AUDIT
### CarbonTally QA Harness V1.2 + Independent Audit Swarm V1
### Zero-code portability/separation architecture audit

- Date: 2026-08-31
- Scope: READ-ONLY audit of `qa_harness/` and `independent_audit/`. No code
  was changed, nothing was committed or pushed, CarbonTally is untouched.
- Baseline: checkpoint `16391217103b98dcea520070c5a22c68f12fe607`

---

## 1. Objective

Determine how the two assurance tools can become **portable, generic, free
and open-source** tools for arbitrary SaaS applications, with CarbonTally
reduced to a single **application profile / reference implementation**.

```
    Generic SaaS Application
             │
             ▼
      Application Profile        (profiles/<app>/)
             │
       ┌─────┴─────┐
       ▼           ▼
 QA Harness     Audit Swarm      (two independent tools, shared contracts)
       │           │
       └─────┬─────┘
             ▼
       Evidence / Findings        (canonical EvidencePacket + Finding)
             │
             ▼
        Final Reports
```

---

## 2. Inventory summary

| System | Source modules | Runtime data | Self-tests | Docs |
|---|---|---|---|---|
| `qa_harness/` | ~105 Python files, 10 YAML configs, 1 pyproject, Makefile | 30 API JSON, 6 DB JSON, 63 screenshots, 3 findings JSONL, 54 archived reports | 33 test files | README |
| `independent_audit/` | 22 `ia_core`/collectors/agents files, 1 orchestrator, 1 CLI, 1 Playwright driver | evidence packets (gitignored), latest fix report | 13 test files (146 tests) | README, requirements.txt |

Both trees are currently **untracked** in git (`?? qa_harness/`,
`?? independent_audit/`). Nothing is committed, pushed, or published.

---

## 3. Module-level classification (A–H)

Legend:
- **A. GENERIC** — portable as-is; no CarbonTally assumption.
- **B. CARBONTALLY-SPECIFIC** — encodes CarbonTally knowledge.
- **C. MIXED / COUPLED** — mechanism is generic but defaults/embedded data
  are CarbonTally-specific.
- **D. SECURITY-SENSITIVE** — handles credentials/redaction/safety.
- **E. RUNTIME/EVIDENCE DATA** — generated output, never published.
- **F. TEST INFRASTRUCTURE** — deterministic self-tests.
- **G. DOCUMENTATION**.
- **H. REDUNDANT/LEGACY** — dead or superseded.

### 3.1 qa_harness/

| Module | Class | Notes |
|---|---|---|
| `core/config.py` | A/C | Generic YAML config loader; `api_prefix="/api/v3"` default is a mild CarbonTally default. |
| `core/evidence.py` | A | EvidenceStore (kind/run_id/role/route/name); fully generic. |
| `core/findings.py` | A/C | Finding model, normalization, dedup; `emissions` synonym entry is CarbonTally-flavored. |
| `core/status.py` | A | ToolUnavailable / SKIPPED / BLOCKED vocabulary; generic. |
| `core/secrets.py` | D/A | Secret redaction patterns; generic (Supabase patterns are generic SaaS shapes). |
| `core/safety.py` | D/A | Read-only guard + mutation policy; prose mentions investor-demo data; mechanism generic. |
| `core/run_context.py` | C | Run orchestration; loads **demo credentials** (CarbonTally). |
| `core/credentials.py` | B/D | `demo.carbontally.local` shared-password loader; deep CarbonTally coupling. |
| `identities/loader.py` | B | Demo identity email scheme (1183 identities), DEMO_IDENTITIES manifest. |
| `identities/context.py` | C | Identity/org/consultant/PE relationship resolution (CarbonTally semantics). |
| `identities/resolver.py` | C | Role→persona→email demo mapping. |
| `identities/selectors.py` | B | Generates `{role}.demoNNNN@demo.carbontally.local` emails. |
| `api/probe.py` | C | Probe runner generic; **hard-coded AUTHZ-1…23 CarbonTally probes + demo emails**. |
| `api/session.py` | C | Session cache; `demo_login` coupling. |
| `api/inventory.py` | A | OpenAPI route inventory; generic. |
| `api/contract.py` | A | Implementation↔OpenAPI contract diff; generic. |
| `api/authorization.py` | C | Generic framework + hard-coded `E("AUTHZ-17", ...)` CarbonTally expectations. |
| `api/workflows.py` | C | Generic executor; processing-stage list from CarbonTally backend. |
| `db/discovery.py` | C | SELECT-only resource discovery; contains CarbonTally queries (conversations, orgs). |
| `db/schema_inventory.py` | A | Catalog inspection (tables/columns/indexes); generic. |
| `db/constraints.py` | B | Expected constraints hard-coded: `facilities` postcode CHECK, `emissions_logs` PK. |
| `db/indexes.py` | A/C | Generic inspection + expected CarbonTally indexes. |
| `db/rls.py` | A/C | RlsAudit generic; RlsExpectation vocabulary generic (free-text actor/resource). |
| `db/migrations.py` | A | Migrations state diff; generic. |
| `db/integrity.py` | B | Orphan rules on `organizations`, `consultant_clients`, `emissions_logs`, `calculated_emissions_kg_co2e`. |
| `browser/auth/session.py` | C/D | Playwright + API auth; `demo_login` refuses non-demo identities (CarbonTally). |
| `browser/playwright/controller.py` | A | Generic controller. |
| `browser/routes/navigator.py` | A | Route-driven navigation; generic. |
| `browser/tables/auditor.py` | A | Table/grid auditor; generic (thresholds from config). |
| `browser/responsive/auditor.py` | A | Viewport sweep; generic. |
| `browser/accessibility/axe.py` | A | axe-core runner; generic. |
| `browser/workflows/driver.py` | A | Workflow driver; generic (workflow steps from config). |
| `browser/sweep.py` | A | Route sweep; generic. |
| `browser/fixtures/generate.py` | C | In-memory CSV/PDF fixture generation; CSV content is fuel/utility flavored. |
| `workflows/*.py` | B | customer, consultant, client, pe, operations, messaging, admin — CarbonTally workflows. |
| `workflows/executor.py` | A | Step executor; generic. |
| `rules/business.py` | B | BUS-1…N: document→emissions→report chain, factor/unit rules. |
| `rules/security.py` | B | SECR-1…N: viewer/member/PE/consultant authorization expectations. |
| `rules/navigation.py` | C | Workspace navigation expectations (public/customer/consultant/pe/ops/admin). |
| `rules/tables.py` | C | Table expectations keyed to CarbonTally screens (documents/emissions/queue). |
| `rules/ux.py` | A/C | Reusable UX rules; some CarbonTally prose (queue→workbench). |
| `agents/base.py` | A/D | Optional-AI base agent; OpenRouter env resolution; generic. |
| `agents/swarm.py` | A | Deterministic agent swarm; generic. |
| `agents/{api,judge,security,ux,workflow}_agent.py` | C | Prompts mention CarbonTally; framework generic. |
| `scripts/run_all.py` | C | Stage orchestrator; CarbonTally names in output strings. |
| `scripts/{run_db,run_api,run_browser,run_workflows,run_agents}.py` | C | Stage runners; CarbonTally names in output strings. |
| `scripts/preflight.py` | A | Preflight (git SHA, env check); generic. |
| `scripts/common.py` | A | Arg/env helpers; generic. |
| `scripts/reclassify.py` | C | Reclassification tool; finding vocabulary shared. |
| `scripts/audit_openapi_bindings.py` | C | OpenAPI→bindings audit; CarbonTally paths referenced. |
| `config/*.yaml` (roles, routes, workflows, qa_config, environments, table_rules, ux_rules, severity, exclusions) | **B** | The de-facto CarbonTally profile data. |
| `config/loader.py` | A | YAML loading; generic. |
| `visual/axe/runner.py` | A | axe wrapper; generic. |
| `reports/generator.py` | C | Report generation; "# CarbonTally QA —" titles. |
| `reports/backlog.py` | C | Cline backlog generator; CarbonTally naming. |
| `evidence/`, `findings/`, `reports/archive+latest/` | **E** | Runtime output (30 API, 6 DB, 63 screenshots, findings JSONL, 54 reports). |
| `tests/harness/*` | F | Deterministic self-tests (markers `harness`, `mutation`); fixtures use demo emails but tests are harness-only. |
| `tests/fixtures/{sample_manifest.json,tiny_openapi.json}` | F | Test fixtures; sample_manifest contains demo emails (test-only). |
| `pyproject.toml` | C | Package name `carbontally-qa-harness`; optional deps pattern already generic. |
| `README.md` | G | CarbonTally-specific. |
| `Makefile` | A | Common tasks. |
| `.venv/`, `.pytest_cache/`, `carbontally_qa_harness.egg-info/` | E/H | Vendored environment + build metadata. |

### 3.2 independent_audit/

| Module | Class | Notes |
|---|---|---|
| `ia_core/evidence.py` | A | EvidencePacket with schema_version, sha256, redaction; generic. |
| `ia_core/schema.py` | A | Strict Finding schema (Category/Severity/Confidence/Classification); generic. |
| `ia_core/normalize.py` | A | Deterministic model-output enforcement; generic. |
| `ia_core/dedupe.py` | A | Deduplication; generic. |
| `ia_core/redact.py` | D/A | Redaction patterns incl. DSN/JWT/signed URL; generic. |
| `ia_core/cost.py` | A | Cost accounting; generic. |
| `ia_core/model_gateway.py` | A/D | OpenRouter/OpenAI-compatible gateway + structured JSON; provider-neutral transport; injectable HTTP. |
| `ia_core/report.py` | C | Report writer; a few CarbonTally strings (prompts verbatim "CarbonTally"). |
| `ia_core/readonly.py` | D/A | Read-only SQL/HTTP guard; prose references CarbonTally; mechanism generic. |
| `ia_core/config.py` | C | Config resolution + repo `.env` discovery; default `checkpoint` is a CarbonTally commit. |
| `ia_core/isolation.py` | C | Fresh-start blocklist; defaults name CarbonTally repo dirs (`docs/audit`, `qa_harness`, `local_backups`) but are configurable. |
| `ia_core/prompts.py` | C | Role prompts; ground rules generic, some wording references CarbonTally; role names generic. |
| `agents/roles.py` | A | Evidence-kind-scoped role registry; fully generic. |
| `agents/runner.py` | A | Deterministic agent runner; generic. |
| `agents/crosscheck.py` | A | Cross-check normalization; generic. |
| `agents/final_judge.py` | A | Final judge; generic. |
| `collectors/db_collector.py` | A/D | Catalog + RLS + integrity collector; SQL is generic; DSN resolution generic (db.dsn > db.env > env > repo .env). |
| `collectors/api_collector.py` | A | OpenAPI/routes/probes collector; generic (probes come from config). |
| `collectors/frontend_collector.py` | A | Route/component/API-map collector; generic. |
| `collectors/browser_collector.py` | A | Browser jobs builder; generic. |
| `collectors/fresh_start.py` | A | Repo map + blocklist enforcement; generic. |
| `browser_driver/driver.mjs` | A/D | Playwright evidence driver; credentials via `IA_CREDENTIALS_JSON` env; read-only; generic. |
| `orchestrator.py` | C | Pipeline (freshstart→collect→agents→crosscheck→judge→reports); report note references CarbonTally; otherwise generic. |
| `run_audit.py` | C | CLI; `description="CarbonTally independent audit swarm"`. |
| `config/default_config.json` | **B** | CarbonTally profile data: checkpoint, repo dirs, localhost URLs, 13 CarbonTally personas, routes, viewports. |
| `config/keys.example.json` | A/D | Template with placeholder (`sk-or-v1-REPLACE_ME`). |
| `.gitignore` | A | Correctly ignores keys, credentials files, reports outputs. |
| `tests/*` | F | 146 deterministic tests (some filenames mention carbontally). |
| `README.md` | G | CarbonTally-specific. |
| `requirements.txt` | A | Generic. |
| `reports/latest/*.md` | E | Runtime reports (gitignored). |

---

## 4. CarbonTally coupling — complete list

### 4.1 Direct coupling (verbatim CarbonTally knowledge)

1. **`qa_harness/config/*.yaml`** — roles, routes, workflows, environments,
   table rules, UX rules: all CarbonTally profile data embedded in the
   harness.
2. **`qa_harness/core/credentials.py`** — `demo.carbontally.local` domain,
   shared-demo-password loading, `.local-demo-credentials.md`.
3. **`qa_harness/identities/`** — 1183-identity demo scheme,
   `{role}.demoNNNN@demo.carbontally.local`, `pe-manager-N.demo`,
   `client.owner.demoCCCC.K`.
4. **`qa_harness/api/probe.py`** — AUTHZ-1…23 endpoints
   (`/api/v3/documents`, `/api/v3/organizations`, `/api/v3/uploads`,
   `/api/v3/ops/queues/operator`, `/api/v3/processing/items/.../customer-review`,
   `/api/v3/settings/retention`, `/api/v3/commercial/config`, …) and demo
   cross-tenant email pairs.
5. **`qa_harness/db/integrity.py` / `constraints.py` / `indexes.py`** —
   `organizations`, `organization_members`, `consultant_clients`,
   `upload_batches`, `assets`, `facilities`, `emissions_logs`,
   `calculation_snapshots`, `calculated_emissions_kg_co2e`.
6. **`qa_harness/rules/business.py` / `security.py`** — document→emissions→
   report chain, unit aliases, factor approval, PE/consultant/client
   authorization matrix, retention/commercial gates.
7. **`qa_harness/workflows/*.py`** — customer/consultant/client/pe/
   operations/messaging/admin workflows.
8. **`qa_harness/api/authorization.py`** — hard-coded AUTHZ expectations.
9. **`qa_harness/browser/auth/session.py` + `core/run_context.py`** — demo
   login flow, demo password resolution.
10. **`qa_harness/reports/generator.py` / `backlog.py`** — "CarbonTally QA —"
    report titles, Cline backlog format.
11. **`independent_audit/config/default_config.json`** — the entire CarbonTally
    profile (personas, routes, URLs, repo layout, checkpoint).
12. **`independent_audit/ia_core/isolation.py`** — default blocklist names
    CarbonTally repo dirs (`docs/audit`, `qa_harness`, `local_backups`).
13. **`independent_audit/ia_core/config.py`** — default `checkpoint` = a
    CarbonTally commit SHA.
14. **Prompts/output strings** — `ia_core/prompts.py`,
    `ia_core/report.py`, `orchestrator.py`, `run_audit.py`, qa_harness
    `agents/*`, `scripts/*` mention CarbonTally.
15. **Package identity** — `carbontally-qa-harness` in `pyproject.toml`.

### 4.2 Indirect coupling (no "CarbonTally" word)

1. **Tech-stack assumptions**: Supabase (GoTrue, PostgREST, RLS, storage),
   FastAPI OpenAPI on `:8050`, React on `:3000`, `backend/api`,
   `frontend/src`, `supabase/migrations` layout. These are treated as
   *defaults*; the profile must override them.
2. **Role vocabulary**: customer_owner/admin/member/viewer, consultant,
   client_owner, pe_manager/pe_staff, operator/reviewer/qc,
   staff_admin/system_admin — appears in both tools as hard-coded names
   (must become profile data).
3. **Route set**: `/home, /emissions, /documents, /processing, /review,
   /reports, /admin, /ops, /data, /messaging, /consultant, /billing` —
   hard-coded in `default_config.json` and `routes.yaml`.
4. **Domain knowledge in finding normalization**: `core/findings.py`
   synonym `"emissions": {"emission","emissions","co2e","tco2e"}`.
5. **DB discovery queries** in `db/discovery.py` (conversations,
   organization_members) and workflow step semantics (upload→storage→
   file_record→processing_job→…).
6. **Security model expectations** — RLS everywhere, org/tenant isolation,
   consultant/client relationship — encoded as rules rather than profile
   data.

---

## 5. Portability estimate

| Tool | Generic now | CarbonTally-coupled | Extraction effort (relative) |
|---|---|---|---|
| **QA Harness V1.2** | ~35 % | ~40 % specific, ~25 % mixed | **High.** The generic kernel (core/status, core/evidence, db catalog, api inventory/contract, browser controllers/auditors, workflow executor, scripts/preflight/common, config loader, Makefile, self-tests) is portable with modest changes. The coupling is concentrated in ~25 modules + 10 YAML files that move to a profile. Largest work: identities/credentials → generic identity abstraction; rules/workflows → profile; AUTHZ probes → profile-driven. |
| **Independent Audit Swarm V1** | ~95 % | ~5 % (config + wording + defaults) | **Low.** Core, collectors, agents, orchestrator, driver are already CarbonTally-free. Only `default_config.json` (→ profile), isolation defaults, checkpoint default, prompt wording, CLI/README need moving/genericizing. |

Both tools were deliberately designed around read-only discipline, optional
AI, redaction and evidence provenance — those design choices are exactly
what open-source SaaS tooling needs, and they transfer directly.

---

## 6. Tool boundary (recommended)

- **QA Harness = deterministic evidence producer.** Owns: DB/RLS/API/browser
  inspection, authentication for probes, authorization negative tests,
  workflows, responsive/accessibility, table/UX rule checks, evidence
  collection, regression runs, deterministic findings, acceptance verdict.
- **Audit Swarm = independent analysis layer.** Owns: AI-optional
  interpretation of evidence, finding correlation, contradiction detection,
  architecture/UX/security analysis, prioritization, cross-check,
  final judgment, machine-readable findings + reports.
- **Shared (contracts package):** EvidencePacket, Finding, Severity,
  Classification (unified vocabulary), ApplicationProfile, RunContext,
  EvidenceReference, Report envelope.
- **Overlap to remove:** both define their own evidence/finding models
  today; both have agent layers (qa_harness `agents/`, audit swarm `agents/`);
  both generate reports. After extraction: qa_harness's agent layer becomes
  optional-analysis *inside* the harness, while the audit swarm is the
  primary cross-tool analysis consumer; reports share an envelope.

---

## 7. Repository strategy, package names, licenses — summary

Full analysis in `REPOSITORY_STRATEGY.md`. Recommendation:

- **Layout:** monorepo **Option B** `github.com/<org>/saas-assurance`
  with `packages/qa-harness`, `packages/audit-swarm`, and
  `packages/contracts`.
- **Package names:** `saas-qa-harness`, `saas-audit-swarm`,
  `saas-assurance-contracts` (imports: `saas_qa_harness.*`,
  `saas_audit_swarm.*`, `saas_assurance_contracts.*`).
- **License:** **Apache-2.0** (permissive + patent grant + safe for
  commercial consumers); MIT acceptable alternative; GPL-family rejected.
- **CLI:** unified `saas-assurance` CLI with `init | preflight | run-qa |
  analyze`, plus thin per-tool entry points (`qa-harness`, `audit-swarm`).

---

## 8. Migration phases — summary

Full plan in `MIGRATION_PLAN.md` (PHASE 0–11). CarbonTally compatibility is
a hard requirement: the CarbonTally **application profile** preserves every
current capability (V1.2 QA, 1183 demo identities, personas, security
boundaries, DB/API/browser checks, evidence, reports).

---

## 9. Key risks (top 5)

1. **Identity/credential generalization** is the riskiest extraction: the
   demo-identity + shared-password model must become a generic
   credential-source abstraction without weakening qa_harness's existing
   safety rule ("never hand the demo password to a non-demo identity").
2. **Classification vocabulary unification** — two mature finding
   classifications (qa_harness REAL/RE-VERIFY/HARNESS_*/INCONCLUSIVE vs
   audit-swarm CONFIRMED/LIKELY/POSSIBLE/…). A lossy mapping would corrupt
   verdicts; needs an explicit compatibility table (see
   `SHARED_EVIDENCE_FINDING_CONTRACT.md`).
3. **Report/CarbonTally-language removal** while preserving evidence
   provenance and the acceptance-verdict semantics.
4. **qa_harness has no `.gitignore`** — opening the repo without one would
   publish runtime evidence (screenshots, API responses, findings) and a
   vendored `.venv`.
5. **Schema drift** between the two evidence models during extraction —
   mitigated by freezing the EvidencePacket schema in the contracts package
   first (PHASE 2).

---

## 10. Conclusion

- Both tools **can realistically become open source**; the Audit Swarm is
  near-ready (low effort), the QA Harness needs a profile-extraction
  refactor (high but well-bounded effort).
- **CarbonTally should be the first reference application** — it has the
  deepest persona/role/tenant model and exercises every layer.
- The two tools should **remain independently usable** and **independent
  projects in one repo**: QA Harness must run with zero AI; the Audit Swarm
  is AI-optional and consumes harness evidence (or its own collectors).
- CarbonTally application code, database, migrations, RLS, seed data and
  configuration are **not modified** by this audit and will not be modified
  by the extraction (PHASE 3–5) beyond moving profile data out of the two
  tools' defaults.

---

*End of DUAL_TOOL_PORTABILITY_AUDIT.md. Companion docs:
STANDALONE_ARCHITECTURE.md, APPLICATION_PROFILE_SPEC.md,
SHARED_EVIDENCE_FINDING_CONTRACT.md, REPOSITORY_STRATEGY.md,
OPEN_SOURCE_SECURITY_CHECKLIST.md, README_DRAFT.md, TUTORIAL.md,
MIGRATION_PLAN.md, PORTABILITY_MATRIX.md.*
