# Beginner Tutorial — First Audit of a SaaS Application

This tutorial uses a **fictional** application so you can follow along
without any knowledge of CarbonTally.

**Fictional app:** *AcmeNotes* — a SaaS note-taking and team-workspace
product.

- Web app: `https://app.acmenotes.example`
- API: `https://api.acmenotes.example` (OpenAPI at `/openapi.json`)
- Auth: email + password at `/login`
- Database: PostgreSQL (Supabase-style), DSN supplied by environment
- Demo users (local test environment only):
  - `owner` — org owner (Acme Demo Ltd), can manage org and members
  - `member` — org member, read/write own notes
  - `viewer` — read-only
- Shared demo password (test env only): supplied via environment variable —
  never written in a profile.

> Every name, URL and email in this tutorial is invented. Do not reuse real
> credentials anywhere.

---

## 0. What you will do

```
Install → create profile → configure target → configure identities →
configure credentials → preflight → run deterministic QA → read findings →
inspect evidence → optional AI analysis → fix the app → run regression QA
```

---

## 1. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install saas-qa-harness
pip install "saas-qa-harness[browser]"
playwright install chromium
```

Check the install:

```bash
qa-harness --version
```

## 2. Create an application profile

```bash
qa-harness init acmenotes
```

This creates `profiles/acmenotes/` with a valid skeleton:

```
profiles/acmenotes/
├── profile.yaml
├── environments.yaml
├── roles.yaml
├── routes.yaml
├── identities.yaml
├── workflows.yaml
├── api_probes.yaml
└── db_expectations.yaml
```

## 3. Configure the target

Edit `profiles/acmenotes/profile.yaml`:

```yaml
application:
  name: AcmeNotes
  slug: acmenotes

target:
  frontend_url: https://app.acmenotes.example
  api_url: https://api.acmenotes.example
  api_prefix: /api/v1

authentication:
  mode: form
  login_url: /login
  selectors:
    email: 'input[name="email"]'
    password: 'input[name="password"]'
    submit: 'button[type="submit"]'
  session_signal:
    type: localStorage_prefix
    prefix: acmenotes_session
  independent_check: none          # no separate API login available
```

Add your environments in `environments.yaml`:

```yaml
environments:
  test:
    frontend_url: http://localhost:3001
    api_url: http://localhost:8001
    database: { dsn_env: ACMENOTES_TEST_DATABASE_URL }
  staging:
    frontend_url: https://staging.app.acmenotes.example
    api_url: https://staging.api.acmenotes.example
```

## 4. Configure identities

Edit `profiles/acmenotes/identities.yaml` — **roles and patterns, never
passwords**:

```yaml
identities:
  domain: demo.acmenotes.example
  population:
    owner:  { tenants: 2, count: 5,  pattern: "owner.demo{index:02d}@{domain}" }
    member: { tenants: 2, count: 20, pattern: "member.demo{index:02d}@{domain}" }
    viewer: { tenants: 2, count: 5,  pattern: "viewer.demo{index:02d}@{domain}" }
  representatives:
    owner:  "owner.demo01@demo.acmenotes.example"
    member: "member.demo01@demo.acmenotes.example"
    viewer: "viewer.demo01@demo.acmenotes.example"
  credential:
    provider: env
    env_var: ACMENOTES_DEMO_PASSWORD
```

Edit `roles.yaml` with AcmeNotes' vocabulary:

```yaml
roles:
  owner:
    workspace: customer
    landing_route: /dashboard
    capabilities: [manage_members, edit_org_profile, view_all]
    boundaries: [must_not_access_other_tenants]
  member:
    workspace: customer
    landing_route: /dashboard
    capabilities: [view, create_note]
    boundaries: [must_not_manage_members]
  viewer:
    workspace: customer
    landing_route: /dashboard
    capabilities: [view]
    boundaries: [must_not_create_note, must_not_edit]
```

Edit `routes.yaml`:

```yaml
routes:
  - { path: /login,     workspace: public,   auth: public }
  - { path: /dashboard, workspace: customer, auth: authenticated }
  - { path: /notes,     workspace: customer, auth: authenticated }
  - { path: /org,       workspace: customer, auth: authenticated, roles: [owner, member] }
  - { path: /admin,     workspace: admin,    auth: authenticated, roles: [staff_admin] }
```

## 5. Configure credentials

```bash
export ACMENOTES_DEMO_PASSWORD='correct-horse-battery-staple-2026'
```

That is all. The password is in your shell, not in the profile, not in the
repo. (For a team, use a gitignored credentials file — see
`docs/credentials.md` — or a secret manager when supported.)

## 6. Run preflight

```bash
qa-harness preflight --env test
```

Preflight checks (without touching the app):

- profile files are valid against the schema,
- identity patterns generate the declared population,
- credential provider resolves,
- optional tools are present (Playwright, etc.),
- target URLs are syntactically valid.

Expected output ends with:

```
preflight: OK
```

If a tool is missing you'll see `SKIPPED — TOOL UNAVAILABLE`; the run can
still proceed for the layers that are available.

## 7. Run deterministic QA

```bash
qa-harness run --env test --no-ai
```

The engine now:

1. connects read-only to the test database and inventories schema, RLS,
   indexes, constraints, orphan/duplicate integrity;
2. fetches the OpenAPI contract and inventories endpoints;
3. logs each representative identity in through the real login form and
   independently confirms the session;
4. sweeps anonymous + authenticated routes, checks route protection,
   console/network errors, responsive viewports, axe accessibility;
5. executes the declared workflows with persisted-state verification;
6. normalizes, deduplicates, classifies, and writes reports.

## 8. Read findings

```bash
less reports/latest/MASTER_REPORT.md
less reports/latest/FINDINGS.md
less reports/latest/EXECUTIVE_SUMMARY.md
```

Example finding (AcmeNotes):

```
QA-SEC-001 P1 anonymous  /admin
  Anonymous visitor reached protected route /admin
  Evidence: evidence/<run>/network/anon_admin.json
```

Classification cheat-sheet: `REAL` = confirmed; `RE-VERIFY` = candidate;
`INCONCLUSIVE` = probe couldn't exercise the gate; `HARNESS_*` = the harness
(or profile) is wrong, not the app; `SKIPPED`/`BLOCKED` = not run.

## 9. Inspect evidence

```bash
ls evidence/<run-id>/
```

- `api/` — redacted request/response payloads per finding
- `console/` — browser console logs
- `network/` — network summaries
- `screenshots/` — only meaningful captures (never blank/loading pages)

Every finding links its evidence. If evidence is missing, the finding was
not trusted enough to report as `REAL`.

## 10. Optional AI analysis

```bash
export SAAS_QA_AI_API_KEY='...'
qa-harness run --env test          # deterministic + AI analysis
# or, analyze the last deterministic run only:
qa-harness run_agents --env test
```

The AI layer summarizes, correlates, and prioritizes the deterministic
findings. It never invents findings: anything the AI suggests is labeled
`AI OBSERVATION` and must be confirmed deterministically before it counts.

## 11. Fix the application

For `QA-SEC-001` (anonymous visitor reaches `/admin`), the AcmeNotes team
adds a route guard on `/admin`. Nothing in the harness changes.

## 12. Run regression QA

```bash
qa-harness run --env test --no-ai
```

The run now shows:

- `QA-SEC-001` no longer appears (or appears as `RE-VERIFY` → then
  `REAL`-absent on the following run),
- nothing else regressed.

Compare with the previous run:

```bash
qa-harness report --diff reports/archive/<previous-run-id>
```

---

## Next steps

- Read `docs/APPLICATION_PROFILE_SPEC.md` for the full profile contract.
- Add workflows (`workflows.yaml`) for your critical user journeys.
- Add negative-authorization probes (`api_probes.yaml`) for cross-tenant
  cases.
- Add DB expectations (`db_expectations.yaml`) once you know your schema
  facts.
- Wire it into CI with `qa-harness run --no-ai && qa-harness report
  --fail-on P0,P1`.

---

# Part 2 — Audit Swarm: independent analysis of the same evidence

The QA Harness run above produced `evidence/` (canonical EvidencePackets)
and `findings.json`. The **Audit Swarm** is a second tool that interprets
that evidence with an optional AI layer.

## 13. Analyze the deterministic evidence

```bash
audit-swarm analyze ./evidence --no-ai
```

With `--no-ai` the swarm runs its deterministic stages only:

1. **cross-check** — deduplicates, finds contradictions, downgrades
   unsupported claims;
2. **final judge** — assigns severities and a summary.

Output: `findings.json`, `reports/INDEPENDENT_AUDIT_MASTER.md`,
`INDEPENDENT_AUDIT_EXECUTIVE.md`, `INDEPENDENT_AUDIT_SECURITY.md`,
`INDEPENDENT_AUDIT_UX.md`, `INDEPENDENT_AUDIT_ARCHITECTURE.md`.

## 14. Optional AI analysis (provider-neutral)

```bash
export SAAS_ASSURANCE_API_KEY='...'       # any supported provider
audit-swarm analyze ./evidence --provider openrouter
```

The swarm's DB/API/Frontend/UX/Security/Architecture agents each receive
only the evidence packets scoped to their role, plus the application
profile. Every AI finding carries `ai_generated: true` and a confidence;
the cross-check stage can only *downgrade*, never auto-*confirm*, an AI
claim. A finding becomes `CONFIRMED` only with deterministic evidence or
human/PO confirmation.

## 15. Collect fresh evidence with the swarm's own collectors

If you did not run the harness:

```bash
audit-swarm collect --profile acme-notes --no-ai
```

This runs the swarm's own DB catalog, API contract, frontend-map and
browser collectors (all read-only) and produces evidence packets directly.

## 16. End-to-end pattern for a release gate

```bash
qa-harness run --env test --no-ai          # deterministic QA + verdict
audit-swarm analyze ./evidence              # independent analysis
# release gate: no P0/P1 REAL defects, no security-boundary findings
```

---

## Recap — what you now have

| Artifact | Producer | Purpose |
|---|---|---|
| `evidence/` | `qa-harness` (or `audit-swarm collect`) | canonical, redacted, checksummed evidence |
| `findings.json` | both | machine-readable findings (shared schema) |
| QA reports | `qa-harness` | deterministic verdict + defect list |
| Audit reports | `audit-swarm` | independent analysis + prioritization |
| `profiles/acme-notes/` | you | reusable regression profile for AcmeNotes |
