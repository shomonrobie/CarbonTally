# Application Profile Contract — Specification

**Status:** PROPOSAL v1 — for Product Owner review.
**Purpose:** Define the formal contract between the generic QA engine and an
application profile, so the engine can test arbitrary SaaS applications and
CarbonTally becomes one (reference) profile.

---

## 1. Format decision: YAML + optional Python adapter (hybrid)

| Option | Pros | Cons |
|---|---|---|
| YAML only | declarative, safe to ship, easy diff/review, no code execution | cannot express bespoke logic (custom auth flows, exotic selectors) |
| JSON only | tool-universal, strict | verbose, no comments, worse for humans |
| Python only | maximum expressiveness | executes arbitrary code at load (security surface), harder for non-programmers |
| **Hybrid (recommended)** | YAML for all data; **optional** Python adapter file for behavior | requires a documented "when to use Python" rule |

**Decision: hybrid.** All declarative data (roles, routes, workflows, DB
expectations, API probes, identities, table rules) is YAML. A profile MAY
include a `adapter.py` with functions the engine calls by name (e.g.
`auth_login(page, credentials)`, `resolve_org_context(identity)`); if
absent, the engine uses built-in default behavior. The engine loads YAML
with a schema validator; `adapter.py` is only executed when the profile is
selected and is documented as "runs local code — review before use".

Security note: profiles are code+data that the operator chooses to run
against their own target. The standalone repo ships only example profiles;
the engine prints a warning when an adapter module is loaded.

## 2. Profile directory layout

```
profiles/<name>/
├── profile.yaml            # REQUIRED — identity of the application
├── adapter.py              # OPTIONAL — bespoke behavior hooks
├── environments.yaml       # target environments (local/staging/prod)
├── roles.yaml              # role vocabulary, capabilities, boundaries
├── identities.yaml         # population manifest (counts/patterns/aliases)
├── routes.yaml             # route catalog + landings
├── workflows.yaml          # declarative workflows (or workflows/*.yaml)
├── api_probes.yaml         # endpoint/status/negative-authz specs
├── security_expectations.yaml
├── db_expectations.yaml    # tables/columns/indexes/constraints/rls/migrations
├── integrity_rules.yaml    # orphan/duplicate/business-integrity rules
├── table_rules.yaml        # table/grid expectations
├── ux_rules.yaml           # UX rule overrides (optional)
├── exclusions.yaml         # exclusions/waivers
├── report_templates/       # report filenames + backlog template
├── tests/                  # profile regression tests
└── README.md
```

Every file is optional except `profile.yaml`. Unspecified sections use
engine defaults (generic rules apply).

## 3. `profile.yaml` — core identity

```yaml
application:
  name: CarbonTally                # display name
  slug: carbontally                # profile id, used in report paths
  type: carbon-accounting-saas     # free-form; for humans
  version: "3"                     # app version under test (for reference)

target:
  frontend_url: https://app.example.com
  api_url: https://api.example.com
  api_prefix: /api/v3
  auth_url: https://auth.example.com     # optional, for external IdP
  database:                             # optional; usually via env
    mode: dsn_env                        # dsn_env | env | none
    dsn_env: DATABASE_URL

authentication:
  mode: gotrue                          # built-in: gotrue | form | token
  login_url: /login
  selectors:                            # only for mode: form
    email: 'input[type=email]'
    password: 'input[type=password]'
    submit: 'button[type=submit]'
  session_signal:                       # how the engine confirms a session
    type: localStorage_prefix
    prefix: sb-                         # generic default; override per app
  independent_check: gotrue_password    # api_login | form_only | none
  app_gate_detection:                   # optional app-level gate text
    match_text: ["beta", "invite"]
```

## 4. Roles

```yaml
roles:
  owner:
    label: Owner
    workspace: customer
    landing_route: /home
    capabilities: [view, edit_org_profile, manage_members]
    boundaries: [must_not_access_other_tenants, must_not_access_staff_surfaces]
  member:
    label: Member
    workspace: customer
    landing_route: /home
    capabilities: [view]
    boundaries: [must_not_edit, must_not_manage_members]
  # custom roles are free-form: pe_manager, consultant, staff_admin, ...
```

The engine understands only two things about roles: the **workspace**
(customer/consultant/pe/ops/admin/public — a generic vocabulary, profile-
mapped) and the **capability/boundary** tokens (opaque strings that API
probes and rules reference). CarbonTally's full role vocabulary moves here
unchanged from `config/roles.yaml`.

## 5. Identities (no passwords)

```yaml
identities:
  manifest: identities.yaml        # or inline
  population:
    owner: { tenants: 2, count: 50, pattern: "owner.demo{index:04d}@{domain}" }
    member: { tenants: 2, count: 50, pattern: "member.demo{index:04d}@{domain}" }
    consultant: { tenants: 1, count: 50, pattern: "consultant.demo{index:04d}@{domain}" }
    pe_manager: { tenants: 1, count: 3, pattern: "pe-manager-{index}.demo@{domain}" }
  domain: demo.example.com
  credential:
    provider: env                 # env | file | secret_manager
    env_var: MY_APP_DEMO_PASSWORD
  representatives:                # deterministic sweep personas
    owner: "owner.demo0001@demo.example.com"
```

Passwords are NEVER in the profile. The profile declares *how to obtain*
credentials (provider + env var / file key). The engine resolves them at
run time through `credentials/`.

## 6. Routes

```yaml
routes:
  - { path: /login,  workspace: public,     auth: public }
  - { path: /home,   workspace: customer,   auth: authenticated }
  - { path: /ops,    workspace: ops,        auth: authenticated, roles: [pe_manager] }
landings:
  owner: /home
  consultant: /consultant
```

Generic route schema: `path`, `workspace`, `auth` (public|authenticated),
`roles` (optional allow-list), `label`.

## 7. Workflows

```yaml
workflows:
  document_to_emissions:
    label: Document → emissions
    personas: [owner, member]
    steps:
      - { action: login, expected_status: "200" }
      - { action: upload_document, expected_status: "201", verify_persisted: true }
      - { action: extraction, expected_status: "200", actor: internal_operator }
      - { action: calculation, expected_status: "200" }
      - { action: review, expected_status: "200" }
```

Generic `WorkflowStep` fields (kept from V1.2): `action`, `expected_status`
(`200/201/403/deny/no_path`), `actor`, `verify_persisted`, `description`,
plus additions: `resource` (template), `preconditions`, `cleanup`
(read-only aware), `evidence` (bool), `authorization_expectation`
(allow|deny). The action→endpoint binding lives in `api_probes.yaml`.

## 8. API probes (negative authorization, boundaries)

```yaml
api_probes:
  - { id: AUTHZ-1, kind: authz, method: GET,
      path: "/api/v3/documents?organization_id={org_b}",
      actor: customer_owner, expect: deny,
      description: "Customer A cannot read Customer B documents" }
  - { id: SMOKE-1, kind: smoke, method: GET,
      path: "/api/v3/health", actor: anonymous, expect: 200 }
  - { id: SEC-1, kind: security, method: GET,
      path: "/api/v3/admin/audit", actor: staff_admin, expect: 403 }
```

`{org_a}`, `{org_b}`, `{file_id}` placeholders are resolved by the engine
from the identity/tenant context (the V1.2 resource-discovery mechanism).
`expect`: `200/201/4xx/deny/allow/no_path` (same semantics as today).

## 9. DB expectations

```yaml
db_expectations:
  tables:
    organizations: { required: true, columns: [id, name] }
    organization_files: { required: true, columns: [...] }
  indexes:
    - { table: upload_batches, column: organization_id, severity: P2 }
  constraints:
    - { table: organization_members,
        unique: [organization_id, user_id], severity: P1 }
  rls:
    - { table: conversations, enabled: true, policies: 1 }
  migrations:
    count_min: 0
```

`integrity_rules.yaml` holds orphan/duplicate/impossible-status rules:

```yaml
orphan_rules:
  - { id: INT-ORPHAN-1, child: organization_files,
      child_key: organization_id, parent: organizations, severity: P1 }
duplicate_rules:
  - { id: INT-DUP-2, table: conversation_participants,
      on: [conversation_id, user_id], severity: P1 }
```

The engine collects live facts (schema inventory, RLS state, etc.) and
evaluates them against these expectations — exactly the V1.2 comparison,
with the data relocated.

## 10. Table / UX / security expectations

```yaml
table_rules:
  - { route: /documents, min_rows_for_pagination: 50,
      require_pagination: true, require_sort: true, ... }
ux_rules:
  long_queue_workspace_position:
    enabled: true
    max_workspace_offset_px: 0      # 0 = workspace must be its own route/page
security_expectations:
  - { id: SEC-1, area: public_vs_auth,
      check: anonymous_reaches_protected_route, severity: P1 }
```

## 11. Report identity

```yaml
reports:
  prefix: CARBONTALLY_QA_            # CarbonTally keeps its current names
  filenames:
    master: CARBONTALLY_QA_MASTER_REPORT.md
    executive: CARBONTALLY_QA_EXECUTIVE_SUMMARY.md
    findings: CARBONTALLY_QA_FINDINGS.md
    backlog: CLINE_IMPLEMENTATION_BACKLOG.md
  backlog_style: cline                # generic | cline | github
```

## 12. Environment

```yaml
environments:
  local:
    frontend_url: http://localhost:3000
    api_url: http://localhost:8050
    auth_url: http://127.0.0.1:54425
    database: { dsn_env: DATABASE_URL }
  prod:
    frontend_url: https://app.example.com
```

Environment files never contain secrets; DSNs come from environment or
credential provider at run time.

## 13. Validation

- The engine validates every profile file against a JSON Schema on load;
  invalid profiles fail preflight with a precise message (no silent
  defaults).
- `qa-harness init <name>` scaffolds a valid profile from
  `profiles/generic/`.
- `qa-harness validate --profile <name>` is part of preflight.

## 14. Adapter hooks (optional `adapter.py`)

| Hook | Signature | When |
|---|---|---|
| `auth_login(page, credentials, auth_cfg)` | page → AuthOutcome | custom login flows (SSO, MFA) |
| `resolve_org_context(identity, api)` | identity → {org_a, org_b, entity, ...} | non-standard tenant resolution |
| `landing_check(role, path, page)` | → verdict | custom landing rules |
| `workflow_action(action, step, ctx)` | → probe spec | bespoke workflow actions |
| `row_renderers(route)` | → table expectations | app-specific grids |

Defaults exist for every hook; adapter only overrides what it must.

## 15. Compatibility with V1.2

The CarbonTally profile is a **mechanical transplant**: every V1.2 module
classified `B` in `PORTABILITY_MATRIX.md` maps 1:1 onto a profile file. No
semantic change. The engine keeps every V1.2 trust guarantee (auth
confirmation, honest DB failure, defect classification, read-only).
