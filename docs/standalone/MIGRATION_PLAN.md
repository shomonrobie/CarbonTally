# Migration Plan — CarbonTally QA Harness V1.2 → Standalone Generic SaaS QA Framework

**Status:** PROPOSAL — staged plan for PO approval. No code changed yet.
**Invariant across every phase:** CarbonTally QA capability must not degrade;
the engine keeps all V1.2 trust guarantees; no application change ever.

Each phase lists: goal, files affected, risk, compatibility concerns, tests
required, rollback strategy.

---

## PHASE 0 — V1.2 freeze (baseline)

- **Goal:** record the exact pre-migration behavior to diff against.
- **Files affected:** none (create `qa_harness/docs/` or `docs/standalone/`
  baseline notes only).
- **Actions:**
  1. Tag the current tree (`v1.2-freeze` or record HEAD
     `16391217103b…`).
  2. Run the full CarbonTally QA (`run_all.py --no-ai`) at the current
     checkpoint and archive the finding set as the **baseline**.
  3. Record: `253` pytest self-tests, DB evidence (115 tables, 183 RLS
     policies, 94 FK orphan checks), browser sweep behavior.
- **Risk:** LOW (no change).
- **Compatibility:** n/a.
- **Tests:** full self-test suite + full CarbonTally profile run.
- **Rollback:** n/a.

## PHASE 1 — Extract configuration/profile boundary

- **Goal:** introduce the profile concept WITHOUT moving code yet. Copy
  `config/*.yaml` + identity/role/route data into a `profiles/carbontally/`
  skeleton; the engine still reads the old locations (dual-read or a thin
  redirect).
- **Files affected:** new `qa_harness/profiles/carbontally/` (data only);
  `config/loader.py` (optional profile-path resolution).
- **Risk:** LOW-MED — risk of config divergence between old and new
  locations.
- **Compatibility:** engine behavior unchanged; CT QA identical.
- **Tests:** config-parity test (old vs new config produce identical
  loaded objects); existing suite green.
- **Rollback:** delete the profile dir; loader falls back to old paths.

## PHASE 2 — Generalize identity & credentials

- **Goal:** replace hard-coded CT identity/credential logic with the generic
  abstraction (spec §5). Introduce `identities/model.py`,
  `credentials/provider.py` (env + file). CT population moves to the
  profile manifest; `core/credentials.py` CT file format becomes a
  profile-owned parser.
- **Files affected:** `identities/{loader,selectors,context}.py`,
  `core/credentials.py`, `core/secrets.py` (env-name generic),
  `config/qa_config.yaml` (credential env), new `profiles/carbontally/
  identities.yaml`.
- **Risk:** HIGH — identity/credential refactor can regress auth guarantees.
- **Compatibility:** env var `CARBON_TALLY_DEMO_PASSWORD` remains honored
  via profile (`credential.env_var`); browser auth logic untouched.
- **Tests:** new identity-provider tests; credentials redaction tests;
  auth-confirmation regression tests; full CT profile run vs baseline.
- **Rollback:** profile `credential` section points back to the old env
  name/format; old modules kept behind a flag during the phase.

## PHASE 3 — Decouple DB expectations

- **Goal:** DB collectors consume expectations from the profile. Move
  `EXPECTED_TABLES`, integrity rules, index/constraint/RLS/migration
  expectations into `profiles/carbontally/db_expectations.yaml` +
  `integrity_rules.yaml`.
- **Files affected:** `db/{schema_inventory,integrity,indexes,constraints,
  rls,migrations}.py` (expectation injection), profile data files.
- **Risk:** MED — expectation schema must match exactly.
- **Compatibility:** same rule semantics; same severity mapping.
- **Tests:** existing `test_db.py`, `test_run_db_runner.py`; new
  "expectations from profile" test; DB evidence diff vs baseline.
- **Rollback:** profile expectation loader falls back to legacy in-code
  lists.

## PHASE 4 — Decouple API probes

- **Goal:** probe specs load from `profiles/carbontally/api_probes.yaml`.
  `api/probe.py` stays the executor; `api/security.py`/`api/workflows.py`
  bindings become data.
- **Files affected:** `api/{probe,security,workflows}.py` (spec injection),
  profile data.
- **Risk:** MED.
- **Compatibility:** AUTHZ-1..N ids and semantics preserved.
- **Tests:** `test_api.py`, `test_api_probe.py`; probe parity test; CT API
  run vs baseline.
- **Rollback:** spec loader falls back to legacy specs.

## PHASE 5 — Decouple browser/routes/workflows

- **Goal:** sweeps, routes, landings, and workflow definitions read from the
  profile. Move `config/routes.yaml`, `roles.yaml`, `workflows.yaml`,
  `workflows/*.py` definitions, `browser/sweep.py` persona/landing data.
- **Files affected:** `browser/sweep.py` (data-driven), `workflows/executor`
  (binding lookup), profile files, `rules/business.py` → profile
  business rules.
- **Risk:** MED — sweep behavior must stay identical for CT.
- **Compatibility:** V1.2 auth logic frozen (only data source changes).
- **Tests:** `test_browser_auth.py`, `test_browser_sweep.py`,
  `test_workflows.py`; CT browser sweep diff vs baseline.
- **Rollback:** profile-driven data loader with legacy fallback.

## PHASE 6 — Reports & backlog generalization

- **Goal:** report filenames/backlog template from profile
  (`reports.prefix`), keeping CT's current filenames via its profile.
- **Files affected:** `reports/generator.py`, `reports/backlog.py`,
  profile `report_templates/`.
- **Risk:** LOW-MED — naming change could break downstream consumers if the
  profile is misconfigured (CT profile preserves current names).
- **Tests:** `test_reports.py`; report-name test per profile.
- **Rollback:** profile keeps `prefix: CARBONTALLY_QA_`.

## PHASE 7 — AI gateway (provider-neutral)

- **Goal:** `agents/base.py`/`swarm.py` behind `ai/gateway.py` protocol;
  OpenRouter becomes one provider; env var generic with profile override.
- **Files affected:** `agents/*`, new `saas_qa/ai/gateway.py`,
  `requirements-ai.txt`.
- **Risk:** MED — do not regress "AI never authoritative", redaction,
  cost tracking.
- **Compatibility:** `run_agents.py` continues to work with the same key.
- **Tests:** gateway unit tests (fake provider), swarm tests with a stub,
  redaction-before-call test.
- **Rollback:** keep OpenRouter provider as default; disable gateway flag.

## PHASE 8 — Generic example profile

- **Goal:** `profiles/generic/` example (fictional SaaS) to prove
  engine-only usability and feed the tutorial.
- **Files affected:** new profile + docs.
- **Risk:** LOW.
- **Tests:** run the engine against the example profile with mocked
  fixtures; no real app.
- **Rollback:** n/a (additive).

## PHASE 9 — Standalone repo preparation

- **Goal:** new repo `saas-qa-harness/` with `src/` layout, CLI
  (`qa-harness init/preflight/run`), packaging, `.gitignore`, LICENSE,
  CI (self-test + secret scan).
- **Files affected:** new repo; `qa_harness/` kept in place as V1.2
  reference until the new repo proves parity.
- **Risk:** HIGH (repo surgery) — mitigated by the parity gate (Phase 11).
- **Compatibility:** `qa-harness run --profile carbontally` produces the
  same finding set as `run_all.py` at Phase 0.
- **Tests:** full engine suite + full CT profile through the new CLI; diff
  vs baseline.
- **Rollback:** the old `qa_harness/` tree remains untouched and fully
  usable; new repo is additive.

## PHASE 10 — Documentation & security review

- **Goal:** finalize README_DRAFT, tutorial, profile docs; run the
  pre-publication secret scan (§ OPEN_SOURCE_SECURITY_CHECKLIST.md); CI
  secret-scan wired.
- **Files affected:** docs, CI, `.gitignore`.
- **Risk:** LOW-MED.
- **Tests:** doc examples executable; scan clean.
- **Rollback:** n/a (additive).

## PHASE 11 — Public release (PO approval gate)

- **Goal:** publish (rename to `saas-qa-harness`), with CarbonTally as the
  first reference profile. **PO decision required** on: package name,
  license, whether the CarbonTally profile ships inside the repo or as a
  separate private profile package.
- **Files affected:** repository metadata.
- **Risk:** HIGH (public exposure) — checklist gate required.
- **Tests:** post-publish smoke (fresh install from PyPI, run example
  profile, run CT profile).
- **Rollback:** yank release; private profile stays private.

---

## Compatibility gate (applies to every phase)

```
Before phase:  baseline = full CT QA run (findings + evidence hashes)
After phase:   current  = full CT QA run
Gate:          current == baseline  (modulo intentional harness fixes,
                                      each individually documented)
```

## Sequencing notes

- Phases 1–2 are the critical path; everything else is data relocation.
- The V1.2 auth/trust guarantees are frozen code from Phase 2 onward.
- No phase requires a CarbonTally application change.

---

# Dual-tool alignment (QA Harness V1.2 + Independent Audit Swarm V1)

The phases above were written for the QA Harness alone. The Product Owner's
dual-tool objective requires the same sequence to cover **both** systems and
to introduce the **shared contracts** first. The mapping below is the
canonical phase list (PHASE 0–11); the QA-Harness-only phases above map into
it as noted. The Audit Swarm starts ~95 % generic, so its column is mostly
"move data to profile" + wording cleanup.

| Phase | Name | QA Harness work (from prior plan) | Audit Swarm work |
|---|---|---|---|
| 0 | **Freeze current implementations** | baseline run + tag (prior PHASE 0) | freeze `default_config.json` + checkpoint; archive a `--no-ai` collect baseline (evidence hashes) |
| 1 | **Audit coupling** | this document set (`PORTABILITY_MATRIX.md`, `DUAL_TOOL_PORTABILITY_AUDIT.md`) | same documents, Part 2 |
| 2 | **Define shared contracts** | none (read-only) — produce `saas-assurance-contracts` spec: EvidencePacket, Finding, Severity, Classification (with compatibility table), ApplicationProfile, RunContext, EvidenceReference, Report | same contracts; both sides implement `to_unified()`/adapters |
| 3 | **Extract generic core** | prior PHASES 1–5 (profile boundary, identity/credentials, DB/API/browser/workflow decoupling) | rename package (`saas_audit_swarm`); move `default_config.json` → profile; genericize prompts/report wording; default checkpoint/blocklist → profile |
| 4 | **Create CarbonTally profile** | `profiles/carbontally/` holds all V1.2 config/rules/identities data | same profile consumed by collectors (personas, routes, API probes, db expectations) |
| 5 | **Create fictional reference SaaS profile** | `profiles/acme-notes/` (see TUTORIAL.md) | same profile |
| 6 | **Run CarbonTally regression tests** | parity gate: `current == baseline` | `--no-ai` collect + full AI run vs frozen baseline; evidence hashes identical |
| 7 | **Run reference SaaS tests** | harness against acme-notes (mocked/local fixture) | swarm against acme-notes evidence |
| 8 | **Security/privacy audit** | `OPEN_SOURCE_SECURITY_CHECKLIST.md` (incl. new `qa_harness/.gitignore`) | already-good `.gitignore` re-verified; key/creds env handling re-verified |
| 9 | **Documentation** | README_DRAFT, TUTORIAL, ARCHITECTURE, PROFILE, CONTRIBUTING, TROUBLESHOOTING | same docs + contracts doc |
| 10 | **Standalone repository creation** | `saas-assurance` monorepo (REPOSITORY_STRATEGY.md Option B) | package `saas-audit-swarm` + `saas-assurance-contracts` |
| 11 | **Open-source release** | PO gate: license (Apache-2.0 recommended), package names, whether `profiles/carbontally/` ships publicly or as a private profile package | same gate |

## Phase-specific risks (dual tool)

- **PHASE 2** — contract freeze is the linchpin; a bad schema locks both
  tools. Mitigate: schema versioning + compatibility table unit tests.
- **PHASE 3 (Audit Swarm)** — LOW risk; the only behavioral change is where
  profile data comes from. Keep the default profile as a fallback during the
  phase.
- **PHASE 6** — the parity gate must compare **evidence hashes**, not just
  finding titles, so silent evidence degradation is caught.
- **PHASE 11** — publishing `profiles/carbontally/` publicly is a PO
  decision: it contains CarbonTally role/route/business knowledge (valuable
  reference material, but company IP). A private profile package is the
  conservative option.

## Compatibility gate (unchanged)

```
Before phase:  baseline = CarbonTally profile run (findings + evidence hashes)
After phase:   current  = CarbonTally profile run
Gate:          current == baseline  (each intentional difference documented)
```
