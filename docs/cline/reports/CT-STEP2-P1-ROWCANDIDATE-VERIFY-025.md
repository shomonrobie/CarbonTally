# CT-STEP2-P1-ROWCANDIDATE-VERIFY-025 — P1 Row-Candidate Detection: Production Verification

Verification-only task. No application code, test, schema, rollout or configuration was
modified, and no defect was fixed.

---

## 1. Task ID

`CT-STEP2-P1-ROWCANDIDATE-VERIFY-025` — independent verification of the deployed P1
row-candidate detection remediation (`CT-STEP2-P1-ROWCANDIDATE-FIX-023`) against a **fresh**
production execution.

## 2. Baseline

| Item | Value |
| --- | --- |
| Implementation task | `CT-STEP2-P1-ROWCANDIDATE-FIX-023` |
| Banked release under verification | `e1f5c9dbd6af04957e464bc006b6634832fc8304` |
| Branch | `p8-release-reconciled` |
| Verification worktree | `/tmp/ct_step2` — `HEAD = e1f5c9d…8304`, `origin/p8-release-reconciled = e1f5c9d…8304`, working tree **clean** |
| Task-start state | unchanged from the 023 hand-off; this task created no code/test change |
| Expected deployment | Vercel `e1f5c9d`, Render `e1f5c9d` |

## 3. Production deployment evidence

Reachability and runtime facts (all read-only, no credentials involved):

```text
GET  https://carbontally-api.onrender.com/health        -> 200 in 7.7 s
     {"status":"healthy","service":"CarbonTally API","version":"3.0.0",
      "timestamp":"2026-09-18T07:53:54.636659Z",
      "supabase_connected":true,"pool_connected":true,
      "components":{"database":{"status":"connected"},
                    "pool":{"status":"connected"},
                    "api":{"status":"running","version":"3.0.0","routes":49}}}
GET  https://carbontally-api.onrender.com/openapi.json  -> 200 in 12.9 s
     title "CarbonTally API", version 3.0.0, 570 paths, securitySchemes ["HTTPBearer"]
response headers: server: cloudflare · x-render-origin-server: uvicorn
                  rndr-id: <instance id>            (NOT a Git commit identity)
```

Build/version identity probes (all unauthenticated): `/version`, `/api/version`, `/build`,
`/health/version`, `/api/v1/health`, `/api/config`, `/config` → **404** each. A search of the
production OpenAPI contract for `rollout`, `shape`, `fidelity` and `coverage` paths returned
**0 paths** — there is no deployment-identity or rollout-state endpoint to read.

**Runtime commit identity: NOT ESTABLISHED.** The application surface exposes no build/commit
identifier (`/health` reports only the semantic version `3.0.0`); `rndr-id` is an instance
identifier and is explicitly *not* treated as a commit identity. A repository check shows why
the application surface cannot settle this question either: the entire 023 change touched only

```text
backend/services/extraction_fidelity.py            (logic)
backend/tests/unit/services/...multiline.py        (tests)
docs/cline/reports/CT-STEP2-P1-ROWCANDIDATE-FIX-023.md
```

i.e. **no route, schema, or contract change** — `e88b394` and `e1f5c9d` produce an identical
OpenAPI surface, so route-level equality cannot discriminate between them. Deployment identity
therefore remains **unverified**, and this limitation is recorded rather than guessed.

## 4. Synthetic tenant / test-document identity

**No production session was available, so no test document and no test tenant were used.**

Credential availability, verified in this environment (values never read into any artifact):

| Source | Finding | Usable for production? |
| --- | --- | --- |
| `CT_ACC_EMAIL` / `CT_ACC_PASSWORD` (the runtime session used for the `019`/`020`/`022` production reads) | **unset** in this environment | **No** |
| local demo credential store (`tools/seed_investor_demo`, `independent_audit/ia_core/credentials.py`) | local demo-stack identities (`…@demo.carbontally.local`) with the shared *local* demo password | **No** — local stack only |
| `tests/e2e/.env.personas` | `E2E_BASE_URL=http://127.0.0.1:3001`, `E2E_SUPABASE_URL=http://127.0.0.1:55325` | **No** — points at the local stack, not the production Supabase project |
| production `SUPABASE_SERVICE_KEY` present in local `~/carbon_tally/.env.production` / `backend/.env` | service-role key | **Refused** — would bypass RLS/server-side authorization (AGENTS.md §44/§67 and this task's safety rules) |
| `POST /api/test-upload` (declares **no** security requirement in the production OpenAPI) | unauthenticated upload route present in the production contract | **Refused** — would be an *unauthorized production write*; recorded as an observation only and not exercised |

No stored session/token artifact from the earlier tasks exists (`/tmp` contains only helper
scripts that read credentials from the environment; `/tmp/aa2.js` is the public Vercel bundle).

A "safe copy/equivalent of the multi_fuel five-row table structure" therefore **could not be
submitted**: every production upload route in the contract requires `HTTPBearer`
(`POST /api/v3/uploads`, `/api/upload`, `/api/upload-pdf`, `/api/upload-csv`,
`/api/organizations/files/upload`, `/bulk-upload`, `/api/upload-batch`).

## 5. Test execution timestamp

Verification attempts executed `2026-09-18`, between `07:53Z` and `07:56Z`
(server-reported `/health` timestamp `2026-09-18T07:53:54.636659`).
**No production test execution was performed** — the bounded end-to-end test could not start.

## 6. Exact extraction / candidate evidence

**Production: none obtainable.** No fresh extraction was created, so no `candidate_lines`,
`line_items`, coverage block or `metadata.partial_extraction` evidence exists for this task.

For completeness — and explicitly **not** as production verification — the implementation
contract was re-read at the deployed SHA in the clean worktree (read-only, local file only):

```text
worktree /tmp/ct_step2 @ e1f5c9d (clean)
multi_fuel.pdf text layer -> classify(): candidate_lines = 5, multi_line_suspect = True
find_source_lines(): exactly 5 HITs (Gas usage / Diesel supply / Waste disposal /
                     Water supply / Power consumption); all 20 other lines rejected
build_line_items(): 5 items, order 1..5, quantities 5362.2 / 4434.4 / 60.0 / 163.2 / 24620.5,
                    units kwh / l / t / m3 / kwh
```

This is **implementation-level evidence only** and is not converted into a production result.

## 7. Five-row expected-vs-observed comparison

| # | Expected (oracle) | Observed in production |
| --- | --- | --- |
| 1 | Gas usage — 5362.2 kWh | **NOT OBSERVED** (no execution) |
| 2 | Diesel supply — 4434.4 L | **NOT OBSERVED** |
| 3 | Waste disposal — 60 t | **NOT OBSERVED** |
| 4 | Water supply — 163.2 m3 | **NOT OBSERVED** |
| 5 | Power consumption — 24620.5 kWh | **NOT OBSERVED** |
| A | five source rows detected | NOT ESTABLISHED |
| B | source order 1→2→3→4→5 preserved | NOT ESTABLISHED |
| C | quantities preserved | NOT ESTABLISHED |
| D | units preserved (`kwh`,`l`,`t`,`m3`,`kwh`) | NOT ESTABLISHED |
| E | no positional blending | NOT ESTABLISHED |
| F | no silent drop for short/symbolic units | NOT ESTABLISHED |
| G | P1 remains in shadow | NOT ESTABLISHED (unreadable without a session) |
| H | no unrelated production state modified | **CONFIRMED** (no writes performed — §10) |

## 8. Negative / furniture checks

Not executed in production (no execution was possible). At the deployed SHA the
implementation-level check rejects every furniture/prose line of the oracle document —
`Description Qty Unit Rate Subtotal`, `Subtotal: €…`, `Sales Tax: €…`, `Net Payable: €…`,
`Ref No.: PWR/2026/8130`, `Date: …`, `Period: …`, `Buyer: …`, `967 Renewable Road`,
`IV47 7UK`, `Pure Energy PLC`, `FUEL INVOICE`, `Terms: …`, `For testing purposes only` — plus
`Net Payable: £…` (currency-independent). This is **implementation evidence, not production
verification**, and is reported as such.

## 9. P1 rollout-state evidence

* Production: **not readable** — the rollout/shape mode is exposed only through governed
  extraction evidence (the coverage block in queue metadata) or an authenticated admin path;
  the production contract contains **0** `rollout`/`shape`/`fidelity`/`coverage` paths.
* Nothing in this task changed rollout state: no environment variable, feature flag,
  `shape_mode`, allowlist or activation setting was touched. The code that resolves the mode
  was not modified (023 changed unit/row detection only; `shape_mode`/`rollout_status` are
  identical between `3e7e25d` and `e1f5c9d`).
* Effective production mode therefore **remains `shadow` by default**, but this is asserted
  from unchanged configuration + unchanged code, **not** from a production read. It is
  recorded as an expected state, not as verified production evidence.

## 10. Tenant / data-safety evidence

```text
production uploads: 0         jobs created: 0        jobs requeued: 0      jobs retried: 0
jobs cancelled: 0             jobs unlocked: 0       rows updated: 0       rows deleted: 0
database access: none         schema changes: 0      migrations: 0
P1 rollout changes: 0         factor changes: 0      Render config changes: 0
deployments: 0                source-code changes: 0 test changes: 0
existing job 9ef61662-1c0a-497a-b5e9-c179e2134784: untouched (not read, not requeued)
cleanup required: none (no test data was created)
```

All HTTP traffic issued by this task was unauthenticated and read-only (`GET /health`,
`GET /openapi.json`, seven `GET` path probes). No credential was used, transmitted or recorded.
The verification worktree `/tmp/ct_step2` remained at `e1f5c9d` with a clean tree; the dirty
`~/carbon_tally` main worktree was not modified.

## 11. Infrastructure interference

Production behaved normally throughout this task: `/health` 200 (7.7 s) with database and pool
connected, `/openapi.json` 200 (12.9 s). **No 502/503, no timeout, no Cloudflare challenge and
no restart were observed** during the verification window. The blocker is **authorization**
(absence of an authorized synthetic production session), not infrastructure. No causality is
inferred, and no claim is made, about the separate Render memory incident.

## 12. Final verdict

### `BLOCKED`

Per the task's verdict rule — *"BLOCKED if production cannot be safely exercised or the
necessary evidence cannot be obtained"* — a fresh bounded production execution could not be
created, because no authorized production session exists in this environment and every
alternative route was either unsafe (RLS-bypassing service-role key, unauthenticated
`/api/test-upload`) or unauthorized (creating production accounts). Production reachability is
**not** the problem (the service is healthy); the missing element is **authorized access**.

Per the rule *"Do NOT convert PARTIAL/BLOCKED into PASS by inference"*, the implementation-level
re-read at `e1f5c9d` (§6, §8) is **not** treated as production verification.

## 13. Limitations

1. No authorized production session (`CT_ACC_EMAIL`/`CT_ACC_PASSWORD` unset) → no fresh
   extraction, therefore no production candidate evidence (task elements A–D).
2. Exact production commit identity is not establishable from the application/runtime surface
   (`/health` carries only `3.0.0`; no build endpoint; `rndr-id` is not a commit id) and the
   023 change altered no route, so the OpenAPI contract cannot discriminate `e88b394` from
   `e1f5c9d`.
3. Production P1 rollout state could not be read (no session; no rollout endpoint in the
   contract). Unchanged configuration + unchanged `shape_mode` code make `shadow` the expected
   state, but it is not verified production evidence.
4. No production negative/furniture check could be executed for the same reason.
5. Observation for the security backlog: `POST /api/test-upload` declares **no** security
   requirement in the production OpenAPI document (the authenticated upload routes all declare
   `HTTPBearer`). It was deliberately **not** probed, because probing it would be an
   unauthenticated production write. Whether it is protected in code (e.g. by a manual check
   that FastAPI does not express as a security requirement) is therefore **unknown** and
   requires a separate, authorized review.

## 14. Recommendation for the next PO gate

**Unblock and re-run — do not infer.** The single dependency for `025` is an authorized
synthetic production session:

1. Supply the synthetic acceptance session for the target tenant exactly as in tasks
   `014`–`022` (runtime-only `CT_ACC_EMAIL` / `CT_ACC_PASSWORD` for the synthetic Owner, never
   written to a file, report or commit), **or** explicitly authorize a specific sanctioned
   verification path (e.g. a disposable production-equivalent environment, or an approved
   QA-harness path) if the PO prefers not to hand out a production user session.
2. Re-run `025` unchanged. The bounded test is already fully specified by the task: upload one
   new synthetic five-row document (safe equivalent of `multi_fuel.pdf`), let the worker
   process it, then read the queue row's coverage evidence — expecting `candidate_lines: 5`,
   `mode: shadow`, 5 ordered line items with quantities
   `5362.2 / 4434.4 / 60.0 / 163.2 / 24620.5` and units `kwh / l / t / m3 / kwh`, then clean up
   the created document per the normal safe lifecycle.
3. Until that evidence exists, the deployed 023 fix must be treated as **implemented and
   locally verified but production-unverified**, and P1 must remain in `shadow`; a successful
   verification would **not** authorize activation.
4. Separately (not part of `025`): the unauthenticated `POST /api/test-upload` route observed
   in the production contract warrants its own authorized review.


