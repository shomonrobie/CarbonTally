# Standalone SaaS QA Framework — Proposed Architecture

**Status:** PROPOSAL — for Product Owner review. No code changed.

This document specifies the target architecture for turning the CarbonTally
QA Harness V1.2 into a free, open-source, standalone, generic SaaS QA /
Application Assurance Framework. It covers: top-level separation, module
responsibilities, the profile contract, identity/credentials, DB/API/
browser/workflow adapters, findings/evidence, AI neutrality, Hindsight
optionality, CLI/packaging, and the compatibility requirement.

---

## 1. Core separation principle

```
        GENERIC ENGINE                APPLICATION PROFILE (data)
   ┌────────────────────────┐   ┌──────────────────────────────┐
   │ core / db / api /      │   │ name, targets, roles, routes, │
   │ browser / workflows /  │◄──┤ workflows, DB expectations,   │
   │ rules / evidence /     │   │ API probes, security bounds,  │
   │ findings / reports /   │   │ identities, credentials map   │
   │ agents (optional)      │   └──────────────────────────────┘
   └────────────────────────┘                │
        │        │        │                  │
   TARGET ENVIRONMENT   CREDENTIAL PROVIDER  OPTIONAL AI PROVIDER
   (URLs, DSNs, env)    (file / env / future (OpenRouter today,
                         secret manager)      OpenAI/Anthropic/… later)
```

Rules of the separation:

1. The engine contains **zero** application-specific business logic.
2. All application knowledge lives in a **profile** (data + thin code).
3. The engine never reads secrets; it asks a **credential provider**.
4. AI is an **optional provider** behind a gateway; deterministic QA never
   depends on it.
5. Historical memory (Hindsight) is an **optional plugin**; it can seed
   profile expectations but never fabricates current findings.

## 2. Proposed repository structure

```
saas-qa-harness/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt              # core (always installed)
├── requirements-browser.txt      # playwright (+ optional axe)
├── requirements-ai.txt           # openai-compatible client (optional)
├── Makefile
├── .gitignore                    # runtime dirs, credentials, secrets
├── .github/workflows/ci.yml      # self-tests, secret-scan
│
├── src/saas_qa/                  # THE GENERIC ENGINE
│   ├── __init__.py
│   ├── core/                     # finding model, evidence, safety, status,
│   │   │                         # redaction, run context, config
│   │   ├── findings.py
│   │   ├── evidence.py
│   │   ├── redaction.py
│   │   ├── safety.py
│   │   ├── status.py
│   │   ├── config.py
│   │   └── run_context.py
│   │
│   ├── identities/               # generic identity abstraction
│   │   ├── model.py              # Identity, Role, Tenant, Relationship
│   │   ├── loader.py             # manifest-driven loading
│   │   ├── resolver.py           # by-email / by-role lookup
│   │   └── selectors.py          # deterministic pair/cross-boundary select
│   │
│   ├── credentials/              # provider interface + impls
│   │   ├── provider.py           # CredentialProvider protocol
│   │   ├── env.py                # environment provider
│   │   ├── file.py               # generic credentials file (JSON/YAML)
│   │   └── secret_manager.py     # FUTURE: Vault/AWS/GCP/Azure
│   │
│   ├── db/                       # generic database QA (PostgreSQL/Supabase)
│   │   ├── connection.py         # DSN policy (never prints)
│   │   ├── schema_inventory.py   # information_schema enumeration
│   │   ├── integrity.py          # rule-driven orphan/dup/integrity checks
│   │   ├── indexes.py
│   │   ├── constraints.py
│   │   ├── rls.py
│   │   ├── migrations.py
│   │   └── discovery.py          # SELECT-only resource discovery
│   │
│   ├── api/                      # generic API QA
│   │   ├── session.py            # session/token pool
│   │   ├── contract.py           # OpenAPI inspection
│   │   ├── inventory.py          # route discovery
│   │   ├── authorization.py      # allow/deny matrix engine
│   │   ├── security.py           # boundary probes (profile-driven)
│   │   └── probe.py              # spec-driven probe executor
│   │
│   ├── browser/                  # generic browser QA (Playwright)
│   │   ├── controller.py
│   │   ├── auth/
│   │   │   ├── base.py           # AuthProvider protocol
│   │   │   ├── session.py        # session verification (V1.2 logic)
│   │   │   └── providers/        # gotrue.py, oauth.py (future)
│   │   ├── navigator.py          # route navigation + readiness
│   │   ├── sweep.py              # persona/route sweeps (profile-driven)
│   │   ├── tables.py             # table/grid auditor
│   │   ├── responsive.py
│   │   ├── accessibility.py      # axe
│   │   └── workflow_driver.py
│   │
│   ├── workflows/                # declarative workflow engine
│   │   ├── model.py              # WorkflowStep/Workflow (from V1.2)
│   │   └── executor.py           # read-only execution + persisted-state
│   │
│   ├── rules/                    # generic rule engine + default rules
│   │   ├── base.py
│   │   ├── ux.py
│   │   ├── tables.py
│   │   ├── navigation.py
│   │   └── security.py
│   │
│   ├── evidence/                 # evidence store + registry + redaction
│   ├── findings/                 # store (raw/normalized/dedup)
│   ├── reports/
│   │   ├── generator.py          # template-driven report names
│   │   └── backlog.py            # generic issue-backlog template
│   │
│   ├── agents/                   # OPTIONAL AI layer (provider-neutral)
│   │   ├── gateway.py            # AIProvider protocol + routing
│   │   ├── base.py               # observation schema
│   │   ├── swarm.py
│   │   ├── ux_agent.py
│   │   ├── workflow_agent.py
│   │   ├── security_agent.py
│   │   ├── api_agent.py
│   │   └── judge_agent.py
│   │
│   ├── cli/                      # entry points (console_scripts)
│   │   ├── __main__.py           # qa-harness
│   │   ├── init.py               # qa-harness init <name>
│   │   ├── preflight.py
│   │   ├── run_db.py
│   │   ├── run_api.py
│   │   ├── run_browser.py
│   │   ├── run_workflows.py
│   │   ├── run_agents.py
│   │   └── run_all.py
│   │
│   └── tests/                    # engine self-tests (NO app knowledge)
│
├── profiles/                     # APPLICATION PROFILES
│   ├── generic/                  # minimal example (docs + example data)
│   │   ├── profile.yaml
│   │   ├── roles.yaml
│   │   ├── routes.yaml
│   │   ├── workflows.yaml
│   │   ├── db_expectations.yaml
│   │   └── README.md
│   ├── carbontally/              # first real reference profile
│   │   ├── profile.yaml          # name, targets, auth mode, credential env
│   │   ├── identities.yaml       # population manifest (or pointer to it)
│   │   ├── roles.yaml            # ← config/roles.yaml today
│   │   ├── routes.yaml           # ← config/routes.yaml today
│   │   ├── workflows/            # ← workflows/{customer,...}.py today
│   │   ├── db_expectations/      # ← db/{schema,indexes,constraints,rls,…}
│   │   ├── api_probes/           # ← api/probe.py AUTHZ specs
│   │   ├── business_rules.py     # ← rules/business.py today
│   │   ├── report_templates/     # ← CARBONTALLY_QA_* naming
│   │   ├── tests/                # profile-level regression tests
│   │   └── README.md
│   └── my-other-saas/            # user-created profiles (gitignored examples)
│
├── config/
│   └── example/                  # engine defaults (severity, ux rules,
│                                 # viewports, thresholds) + environment
│                                 # templates (NEVER real targets)
│
└── docs/
    ├── standalone/               # this audit + specs
    ├── guide/                    # README_DRAFT content
    └── security/                 # security checklist, threat notes
```

## 3. Responsibility of each major directory

| Directory | Responsibility |
|---|---|
| `src/saas_qa/core/` | Engine primitives: finding model/classification/dedup, evidence store, redaction, safety (read-only), status/skip states, run context, generic config. |
| `src/saas_qa/identities/` | Generic identity abstraction: roles/tenants/relationships loaded from a profile manifest; deterministic selection incl. cross-boundary pairs. |
| `src/saas_qa/credentials/` | `CredentialProvider` protocol + implementations (env, file). Never logs; never serializes secrets. |
| `src/saas_qa/db/` | Read-only PostgreSQL/Supabase QA. Collectors enumerate schema/constraints/indexes/RLS/migrations; integrity runs profile-supplied rules; discovery finds real resource ids. |
| `src/saas_qa/api/` | OpenAPI/contract QA, route inventory, session pool, allow/deny matrix, profile-driven security/probe specs. |
| `src/saas_qa/browser/` | Playwright controller, auth providers + V1.2 session verification, navigator, persona/route sweeps, table/responsive/a11y auditors. |
| `src/saas_qa/workflows/` | Declarative workflow model + read-only executor (persisted-state verification, no spinners). |
| `src/saas_qa/rules/` | Generic rule engine + default UX/table/navigation/security rules. |
| `src/saas_qa/evidence/` | Evidence store/registry (screenshots, traces, videos, api, db, console, network) with readiness discipline. |
| `src/saas_qa/findings/` | Persistence of raw/normalized/deduplicated findings. |
| `src/saas_qa/reports/` | Report generator (template-driven names) + generic backlog output. |
| `src/saas_qa/agents/` | Optional AI layer: provider-neutral gateway, role agents, judge. Deterministic findings only; AI never auto-confirms. |
| `src/saas_qa/cli/` | Console entry points (`qa-harness …`). |
| `profiles/` | Application profiles. Everything app-specific lives here. |
| `config/example/` | Engine default config + environment templates. |
| `docs/` | Public docs (guide, security, standalone blueprint). |

## 4. Application profile contract

Defined in full in `APPLICATION_PROFILE_SPEC.md`. Summary:

- A profile is a directory with a `profile.yaml` (or `.json`) plus optional
  YAML/JSON data files and optional Python modules for bespoke logic.
- The engine reads the profile through a `Profile` loader; the profile never
  imports engine internals (one-directional dependency).
- Hybrid decision: **YAML for data, Python adapter for behavior** (see spec
  §Decision).

## 5. Identity / credential architecture

- `identities/model.py` defines generic `Identity(role, tenant,
  relationships, email-alias, …)`; a profile maps its vocabulary onto it
  (CarbonTally: `customer_owner`→owner with tenant `org_a`; `pe_manager`→
  processing-entity operator; etc.).
- A profile declares which identities it needs by **role + tenant + count**
  (`owner: {tenants: 2, count: 50}`), never passwords.
- `credentials/provider.py` returns `(username, password/token)` only to
  authenticated call sites; `CredentialProvider` implementations: env
  vars (`SAAS_QA_<PROFILE>_PASSWORD`), a gitignored credentials file
  (generic JSON/YAML, schema documented), and a future secret-manager
  provider.
- Redaction: the run context registers every credential it obtains with the
  redactor; no output path can contain a secret (V1.2 guarantee kept).
- Browser/API sessions obtain credentials through the same provider; the
  independent-auth-confirmation logic from V1.2 is preserved verbatim.

## 6. Database adapter

- `db/connection.py` owns DSN policy: explicit DSN → env vars →
  repo-local `.env` → `DB UNAVAILABLE` (never guesses, never prompts,
  never prints).
- Collectors are generic (information_schema/pg_catalog). All expectations
  (`expected_tables`, `expected_columns`, `expected_indexes`,
  `expected_constraints`, `expected_rls`, `expected_migrations`,
  `integrity_rules`, `orphan_rules`, `duplicate_rules`) come from the
  profile as declarative data — the exact schema the V1.2 modules use
  today, relocated.
- `db/discovery.py` stays generic (SELECT-only resource discovery; missing
  tables degrade to `None`).

## 7. API adapter

- Engine: OpenAPI discovery, route inventory, contract comparison,
  status-code checks, request validation, session/token pool, allow/deny
  matrix engine, safe negative probes, tenant-isolation probes.
- Profile supplies: important endpoints, expected roles per endpoint,
  expected statuses, negative-authorization cases (actor→action→resource→
  expect), required parameters, and workflow action→endpoint bindings.
- Probe specs stay declarative (`ProbeSpec`), exactly as `api/probe.py`
  already models them — only the data moves.

## 8. Browser / UI adapter

- Engine: anonymous/authenticated sweeps, persona sweeps, route protection,
  responsive, a11y, console/network capture, screenshot evidence, stable
  rendering detection, navigation verification.
- Auth: `AuthProvider` protocol (GoTrue is one provider; a profile
  declares `mode`, `login_url`, `selectors`). The V1.2 trust architecture
  is preserved **unchanged**:
  - path-aware authentication detection (`urlparse`, never full-URL
    comparison),
  - independent credential verification (provider-backed login),
  - localStorage/session-key verification where applicable,
  - authentication persistence re-check,
  - app-gate (beta) detection,
  - downstream audits gated on confirmed authentication,
  - exactly one authentication finding per persona.
- Routes/personas/landings come from the profile.

## 9. Workflow engine

- `workflows/model.py` = the V1.2 `WorkflowStep`/`Workflow` dataclasses
  (already generic: `actor/action/resource/expected/preconditions/cleanup/
  evidence/authorization-expectation`).
- `workflows/executor.py` stays the read-only executor (GET executes;
  deny-gated writes probe with safe bodies; allow-writes SKIP with
  `READ-ONLY MUTATION BLOCKED`; persisted state verified via DB-backed API).
- All CarbonTally workflow *definitions* move to the profile
  (`profiles/carbontally/workflows/`), which is pure data today — the
  executor already consumes declarative step lists.

## 10. Findings / evidence model

- The V1.2 finding model is kept: ID/category/severity/role/route/workflow/
  expected/actual/description/evidence/reproduction/impact/root cause/fix/
  status/classification/source/timestamp/git SHA.
- Classification vocabulary is split into:
  - **Framework-level** (engine-agnostic): `CONFIRMED`, `LIKELY`,
    `POSSIBLE`, `FALSE_POSITIVE`, `DUPLICATE`, `INSUFFICIENT_EVIDENCE`,
    `RE-VERIFY`, `HARNESS_CONTRACT_DEFECT`, `HARNESS_RUNTIME_ERROR`,
    `INCONCLUSIVE`, `SKIPPED`, `BLOCKED`.
  - **Verdict-level** (counted by the verdict model): `APPLICATION_DEFECT`
    (confirmed), `RE-VERIFY` (candidate), with `PO_DECISION_REQUIRED`
    (product question) excluded from acceptance but reported.
- Normalization + dedup (phrase convergence, evidence preservation) stay
  exactly as calibrated.

## 11. AI architecture (optional)

```
AI provider (OpenRouter / OpenAI / Anthropic / Ollama / local)
        ↓
model gateway (protocol: list models, complete, cost)
        ↓
structured finding schema (AI observations, never raw verdicts)
        ↓
deterministic validation layer (only REAL + evidence pass)
        ↓
reports (AI section separated from deterministic findings)
```

- Gateway interface is provider-neutral (`chat(messages) → Completion`).
  OpenRouter becomes one provider; the engine never imports it.
- Env var for the key is generic (`SAAS_QA_AI_API_KEY` with per-provider
  overrides); profile may pin `provider` and `model`.
- Rules preserved: AI analyzes deterministic findings only; evidence
  scoping; redaction before any model call; structured output; AI findings
  are never automatically confirmed defects; cost tracking per run.

## 12. Hindsight / memory (optional plugin)

- Memory is a plugin behind `memory.py` interface
  (`recall(topic) → notes`). Hindsight is one implementation; `none` is the
  default.
- Memory may seed **profile expectations** (regression targets, known
  boundaries) but never produces current findings. Current findings come
  from current evidence only (documented in README + reports).

## 13. CLI / quick start

Target experience (Part 16):

```
pip install saas-qa-harness          # or: pipx install
qa-harness init my-app                # scaffolds profiles/my-app
qa-harness preflight                  # validates profile + env + tools
qa-harness run --no-ai                # deterministic QA
qa-harness run                        # + optional AI analysis
qa-harness report                     # regenerate reports from last run
```

- Current harness has `scripts/run_*.py` and `--read-only/--role/--route/
  --workflow/--no-ai/--no-visual/--no-security` flags already; the CLI
  restructure is **mechanical** (console_scripts + `cli/` package + `init`
  scaffolding). No engine change required.
- The existing commands (`run_all.py`, `run_db.py`, …) map 1:1 to the new
  CLI subcommands; `run_all.py` remains available for backwards
  compatibility during migration.

## 14. Packaging

- Recommended package name (RECOMMENDATION — PO decision required):
  `saas-qa-harness` (PyPI: `saas-qa-harness`, import `saas_qa`).
  Alternatives: `qa-harness`, `app-assurance-framework`.
- `pyproject.toml` with `[project.scripts] qa-harness = "saas_qa.cli:main"`.
- Python `>=3.10` (current harness uses 3.14 in dev; keep 3.10 floor for
  reach).
- Optional extras: `[browser]` (playwright), `[ai]` (openai-compatible
  client), `[db]` (psycopg2-binary), `[test]` (pytest). Core stays
  dependency-light (`PyYAML`, `requests`).

## 15. Licensing (summary — full tradeoff in Part 18 of audit)

Recommendation: **Apache-2.0** (permissive, patent grant, clear NOTICE for
the CarbonTally-derived portions). MIT is simpler; GPL-3.0 maximizes
freedom but is incompatible with many commercial SaaS vendors' closed
consumers. PO decides.

## 16. Compatibility requirement (Part 21)

After refactor, CarbonTally QA must not lose capability. The CarbonTally
profile supplies: 1183 demo identities, personas, security boundaries,
workflows, DB checks, browser testing, API testing, evidence, and reports —
all through the profile. The engine keeps every V1.2 trust guarantee.
Acceptance gate for each migration phase: run the full CarbonTally profile
through the engine and diff the finding set against the pre-migration
baseline (same set modulo known harness fixes).

## 17. Deterministic-first (Part 22)

- `run --no-ai` produces the full report (findings, evidence, verdict).
- AI adds analysis/correlation/prioritization only; its section is clearly
  separated and never required for basic correctness.

## 18. What this architecture does NOT do

- No mutation by default; mutation stays an explicit, tagged, cleaned-up
  opt-in (V1.2 §33).
- No public-identity assumption: profiles own their identity populations.
- No Hindsight dependency: memory is optional.
- No OpenRouter dependency: AI is optional and provider-neutral.

---

# Dual-tool architecture (QA Harness + Audit Swarm)

This document's sections 1–11 describe the QA Harness engine. The open-source
project actually ships **two independent tools** sharing one contracts
package. This section adds the second tool and the shared surface.

## Two engines, one contract layer

```
                saas-assurance-contracts (schema only)
        EvidencePacket | Finding | Severity | Classification |
        ApplicationProfile | RunContext | EvidenceReference | Report
                          ▲                    ▲
        ┌─────────────────┴─────┐    ┌─────────┴──────────┐
        │  saas-qa-harness      │    │  saas-audit-swarm  │
        │  deterministic        │    │  AI-optional       │
        │  zero-AI runtime      │    │  analysis engine   │
        └───────────────────────┘    └────────────────────┘
                     │                        │
                     └─────────┬──────────────┘
                               ▼
                    evidence/ + findings.json
                               ▼
                          final reports
```

## Second engine — Audit Swarm

| Aspect | Design |
|---|---|
| Pipeline | `freshstart → collect → agents → crosscheck → judge → reports` (unchanged from V1) |
| Collectors | DB catalog/RLS/integrity, API OpenAPI/contract-diff/probes, frontend map, browser pages — all profile-driven, all read-only |
| Agents | db/api/frontend/ux/security/architecture investigators + crosscheck + final judge; evidence-kind-scoped isolation |
| AI | optional; provider-neutral `Provider` interface (OpenRouter today; OpenAI/Anthropic/local later); `--no-ai` runs deterministic stages |
| Evidence input | its own collectors AND qa_harness evidence via the `evidence/adapters/qa_harness.py` adapter |
| Output | `findings.json`, `INDEPENDENT_AUDIT_{MASTER,EXECUTIVE,FINDINGS,SECURITY,UX,ARCHITECTURE}.md` |
| Safety | read-only SQL guard, safe-HTTP guard, fresh-start isolation (profile-configurable blocklist), DSN/credential redaction |

## Shared-surface decisions

1. **ApplicationProfile is the single config contract** (see
   APPLICATION_PROFILE_SPEC.md) — both engines consume it; neither embeds
   profile data.
2. **EvidencePacket is the single evidence contract** (see
   SHARED_EVIDENCE_FINDING_CONTRACT.md) — qa_harness writes it (adapter),
   the swarm reads it.
3. **Finding + Classification are unified**; the compatibility table maps
   existing V1.2/V1 vocabularies.
4. **AI never auto-confirms** — enforced in the contracts and in both
   normalizers.
5. **Hindsight is optional context, never evidence** — a `MemoryStore`
   interface (local file / Hindsight API), profile-scoped, disabled by
   default-equivalent behavior.

## Responsibilities matrix (summary)

| Responsibility | Harness | Swarm |
|---|---|---|
| Deterministic checks + evidence + regression + verdict | ✅ | — |
| Own collectors (optional) | — | ✅ |
| AI interpretation, correlation, contradiction, judgment | optional garnish | ✅ |
| Machine-readable findings + reports | ✅ shared envelope | ✅ shared envelope |

Neither tool depends on the other to run; both depend on the contracts
package and a profile.
