# CarbonTally P6-2F — Browser E2E Security Acceptance

This directory holds the CarbonTally browser/E2E layer for the **P6-2F final
Phase-6 UI/UX + E2E security acceptance gate** (`PO-PHASE6-F-ACC-20260910`,
`PO-PHASE6-F-ENV-20260910`).

It replaces the previous placeholder (`tests/example.spec.ts`, which pointed at
`playwright.dev`) with real CarbonTally specs wired through the root
`playwright.config.ts` (`testDir: './tests/e2e'`).

## Layers

| Layer | Location | Runs without an isolated stack? |
|---|---|---|
| Application/API acceptance (personas + fixtures + ALLOW/DENY) | `backend/tests/e2e/` | ✅ yes (isolated in-memory world) |
| Browser specs | `tests/e2e/*.spec.ts` | partially — unauthenticated route protection only |
| Browser personas/helpers | `tests/e2e/personas.ts` | — |

## Running the application acceptance suite (no browser needed)

```bash
cd backend
python -m pytest tests/e2e -p no:cacheprovider
```

## Running the browser specs against the isolated environment

1. Provision the **dedicated isolated environment** (synthetic data only — never
   the investor-demo dataset, never production; see
   `PO-PHASE6-F-ENV-20260910`).
2. Start the frontend and backend under test, then export the environment:

```bash
export E2E_BASE_URL="http://localhost:3000"

# synthetic personas created by the isolated environment seeding step
export E2E_ORG_OWNER_EMAIL=...       E2E_ORG_OWNER_PASSWORD=...
export E2E_ORG_MEMBER_EMAIL=...      E2E_ORG_MEMBER_PASSWORD=...
export E2E_CONSULTANT_A_EMAIL=...    E2E_CONSULTANT_A_PASSWORD=...
export E2E_CONSULTANT_B_EMAIL=...    E2E_CONSULTANT_B_PASSWORD=...
export E2E_INTERNAL_QC_EMAIL=...     E2E_INTERNAL_QC_PASSWORD=...

# synthetic ids referenced by the specs
export E2E_CLIENT_A_ID=...  E2E_CLIENT_B_ID=...  E2E_ITEM_A_ID=...

npx playwright test
```

Authenticated specs **skip** (they never silently pass) when the environment is
absent, so the harness can never claim acceptance for an untested area.

### Route-protection specs only (no credentials required)

`tests/e2e/carbontally/route-protection.spec.ts` runs against any served
CarbonTally frontend:

```bash
export E2E_BASE_URL="http://localhost:3000"
npx playwright test tests/e2e/carbontally/route-protection.spec.ts
```

A ready-made SPA server for a locally built frontend is provided:

```bash
node tests/e2e/static-server.mjs ./frontend/build 3000
```

## Principles

* The **UI is never the security boundary** — every DENY test targets the real
  server authorization (direct API invocation and direct navigation).
* No credentials are hard-coded; no production data or credentials are used.
* Specs must distinguish pass / skip / fail honestly.
