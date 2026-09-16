# CarbonTally — System Blindspots: Consultant / WhiteLabel Audit

**Report ID:** `CT-SYSTEM-BLINDSPOTS-CONSULTANT-WHITELABEL-20260914-001`
**Task:** CT-OHD-SYSTEM-BLINDSPOTS-CONSULTANT-WHITELABEL-20260914-001
**Auditor:** OpenHands / OHD (independent)
**Date:** 2026-09-14 (environment operational date; see A.4 clock note)
**Type:** AUDIT / FORENSIC DISCOVERY ONLY — **nothing implemented, nothing fixed**
**Programme context:** Phase 8 + Phase 8-X. No Phase 9. Cline's Phase 8/8-X work was **not** redirected.

---

## A. AUDIT BASELINE

### A.1 Repository / worktree state

| Item | Value |
|---|---|
| Repo | `/home/shomonrobie/carbon_tally` |
| Branch | `main` |
| HEAD | `37b19d1` — `feat(admin): admin-configurable Google Analytics 4 (Analytics & Integrations)` |
| Working tree | **DIRTY — 344 changed/untracked paths** |
| Running API | `uvicorn main:app --host 0.0.0.0 --port 8050`, cwd `backend/`, PID 3392405 |
| API DB target | `DATABASE_URL=postgresql://postgres:***@127.0.0.1:54426/postgres` |
| Frontend | CRA dev server on `:3000`; frontend `.env.local` → `REACT_APP_API_URL=http://localhost:8050` |
| Production API | `https://carbontally-api.onrender.com` (538 routes) |

**This audit measured the WORKING TREE, not HEAD.** That distinction is not cosmetic — it is
the substance of finding **SB-02**. Uncommitted in-flight Phase 8 work relevant here:

```
M backend/data/emissions_logs.py          (2026-09-13 12:56)
M backend/services/automatic_processing.py (2026-09-13 12:57)
?? backend/data/evidence_line_items.py     (2026-09-13 12:53)
?? backend/services/extraction_fidelity.py (2026-09-14 13:02)
?? backend/api/v3_disclosure.py            (2026-09-14 12:20)
?? backend/data/disclosure*.py, domain/disclosure*.py, services/disclosure*.py
?? backend/data/report_artefacts.py
```

### A.2 Methodology

Read-only only. Production of evidence via: repository inspection; live authenticated API
probes against the local backend; live browser-equivalent probes (explicit `Origin` header, so
the response is evaluated exactly as a browser's CORS enforcement would evaluate it);
read-only SQL against `postgres`; direct comparison of migration files against applied
migrations; and comparison of local route surface against the production OpenAPI document.

**No application code, schema, migration, RLS policy, test, or configuration was modified. No
write was performed against application data.** One temporary diagnostic script was created
at `/tmp/consult_probe.sh` (outside the repository) — see A.5.

### A.3 Evidence standard used

Every material finding below is tagged **CONFIRMED** / **LIKELY** / **POSSIBLE — NEEDS
FURTHER EVIDENCE**. Nothing marked CONFIRMED rests on inference alone.

### A.4 Clock note

The agent's system clock reports `2026-08-24`; the repository, database, task ID and all
operational artifacts report **2026-09-14**. Findings use the 2026-09-14 operational date and
the timestamps actually recorded by the system. This discrepancy is noted, not resolved.

### A.5 Temporary diagnostics (declared, non-product)

`/tmp/consult_probe.sh` — signs in a named local demo identity via GoTrue and issues
**GET-only** probes. It is outside the repo, touches no product state, and is not a product
change. Local demo identities come from the existing gitignored
`tools/seed_investor_demo/DEMO_IDENTITIES.md`.

### A.6 Reproduction limitation (declared)

Browser-tool automation was unavailable this session (`No connection to browser extension`).
UI-level reproduction therefore rests on (i) code reading of the exact component that renders
the message, and (ii) **browser-equivalent HTTP reproduction** — requests carry an `Origin`
header, and the presence/absence of `Access-Control-Allow-Origin` (ACAO) is measured
directly. Because a browser rejects a cross-origin response that lacks ACAO with a
`TypeError` — indistinguishable in `fetch` from a transport failure — this is a faithful
reproduction of what the browser does. **Finding SB-01 is confirmed by this method.**

---

## B. CONSULTANT CLIENT WORKSPACE — "NETWORK ERROR"

### B.0 Executive answer

The message **"Network error — please check your connection and try again."** is a literal,
hardcoded string in `frontend/src/v3/api.js:56`. It is emitted **only** from the `catch` block
that wraps `fetch()` — i.e. when the promise *rejects*. **It is not a health check of the
user's connection.** It is thrown when the browser refuses a response (most commonly a CORS
failure), or when the transport genuinely failed.

**The user's internet was not the problem.** Two distinct, evidenced causes exist; one is
CONFIRMED and reproducible now, the other is LIKELY and measured against production.

### SB-01 — Every unhandled server 500 loses its CORS headers, so the browser reports it as "Network error"

| Field | Value |
|---|---|
| **Severity** | **P0** (diagnosability + product-wide; primary cause of the PO's confusion) |
| **Classification** | BUG (systemic: error-handling / API-contract) — **NEW FINDING, not in the previous audit** |
| **Status** | **CONFIRMED — reproducible** |
| **Affected roles** | ALL (customer Owner/Admin/Member/Viewer, Consultant, PE, internal staff) |
| **Affected org types** | ALL (ordinary org, consultant client org) |
| **Affected workflows** | Every workflow that can raise an unhandled exception |

**User-visible symptom.** A workspace shows *"Network error — please check your connection and
try again."* while the user's connection is fine and the API is up.

**Expected behaviour.** A server-side failure should surface as a server-side failure (e.g.
"Something went wrong on our side"), with the browser able to read the response.

**Actual behaviour.** The response reaches the browser but is rejected at the CORS layer, so
`fetch` rejects with a `TypeError`. `v3Fetch`'s `catch` then produces the network-error message
and sets `err.raw = 'network'`, discarding the real cause.

**Exact technical root cause.** Measured ACAO presence by status class (identical request
pattern, `Origin: http://localhost:3000`):

| Endpoint response | Status | ACAO present |
|---|---|---|
| `GET /api/v3/consultants/me/clients` | 200 | ✅ yes |
| `GET .../clients/{id}/issues` (foreign client) | 403 | ✅ yes |
| `GET /api/v3/consultants/me/profile` | 404 | ✅ yes |
| `GET .../clients/{id}/dashboard` (bad params) | 422 | ✅ yes |
| **`GET .../clients/{id}/evidence` (DB error)** | **500** | ❌ **NO** |

Only the **500** is missing `Access-Control-Allow-Origin`. Mechanism: 4xx responses are
produced by the `HTTPException` handler, which runs **inside** the middleware stack and so
passes back out through `CORSMiddleware`. Unhandled exceptions are produced by the generic
handler (`backend/main.py:358 @app.exception_handler(Exception)`), which in Starlette is
served by `ServerErrorMiddleware` — the **outermost** layer, sitting **outside**
`CORSMiddleware` (`backend/main.py:173`). Its response therefore never receives CORS headers.

**Frontend files/routes.** `frontend/src/v3/api.js:21-33` (`friendlyError`),
`:35-83` (`v3Fetch`), `:47-59` (the catch that fabricates the message).
**Backend files.** `backend/main.py:173` (CORS), `:336-355` (HTTPException handler),
`:358-375` (generic Exception handler).
**Database involved.** None directly.
**Reusable existing functionality.** `friendlyError()` already distinguishes 401/403/5xx
correctly — the defect is purely that 500s never reach it in the browser.
**Partially implemented?** No — the error taxonomy exists and works; this is a transport-layer
gap.
**Recommended fix direction (NOT implemented).** Ensure error responses leaving the outermost
handler carry CORS headers (add ACAO in the generic handler, or convert to a handled
exception class so it flows through the middleware), so `friendlyError` can classify it.
**Dependencies.** None.
**PO decision required?** No — pure defect.
**Evidence/tests used.** The status/ACAO matrix above (5 status classes); the `500` was
obtained from a genuine DB failure (SB-02), so it is a real-world 500, not synthetic.
**Regression risk.** Low, but the fix touches the global error path — verify 401 challenge
headers (`WWW-Authenticate`, added by RV-1) are not disturbed.

---

### SB-02 — Consultant client workspace fails because in-flight Phase 8 B1/B2 code queries a schema the running database does not have

| Field | Value |
|---|---|
| **Severity** | **P0** (blocks the consultant client workspace and customer calculation surfaces) |
| **Classification** | BUG (schema/code skew regression) |
| **Status** | **CONFIRMED — reproduced end-to-end** |
| **Affected roles** | Consultant (entire client workspace), Customer Owner (calculation history), internal/PE paths reading snapshots |
| **Affected org types** | Consultant client orgs **and** ordinary orgs |
| **Affected workflow** | Client workspace load; calculation history; evidence/provenance read |
| **Reproducible?** | Yes — deterministic |

**User-visible symptom.** PO report: client workspace shows *"Network error — please check your
connection and try again."* Cause of the visible text is SB-01; the underlying failure is this
finding.

**Expected behaviour.** The workspace loads, or fails with an accurate permission/data error.

**Actual behaviour — measured.**

```
GET /api/v3/consultants/clients/29a92a84-.../evidence?limit=50&offset=0
  → HTTP 500   {"success":false,"error":{"code":500,
                 "message":"column \"source_line_item_id\" does not exist", ...}}
  → ACAO: ABSENT  → browser reports "Network error — please check your connection and try again."
```

**Why it kills the WHOLE workspace.** `ConsultantPage.jsx:207-226` loads the client workspace
with a single `Promise.all` of **seven** independent requests (reports, dashboard, processing
status, issues, documents, processing items, evidence). One rejection rejects the whole
`Promise.all`; the `catch` at `:227-229` sets that one error as the page error, and `:302`
replaces the entire workspace with an error block.

**Exact technical root cause.** `_SNAPSHOT_COLUMNS` (`backend/data/emissions_logs.py:52-59`)
is an explicit snapshot column list now containing **`source_line_item_id`**. That column does
not exist in the `postgres` database:

```
$ SELECT column_name FROM information_schema.columns WHERE column_name LIKE '%line_item%';
(0 rows)

$ SELECT id, ..., source_line_item_id, ... FROM public.calculation_snapshots LIMIT 1;
ERROR:  column "source_line_item_id" does not exist
```

It is a **working-tree-only** modification — `git show HEAD:backend/data/emissions_logs.py`
does **not** contain it. The migrations that create it exist as files but were **never applied
to `postgres`**:

| Migration file | Applied to `postgres`? |
|---|---|
| `20260914000000_p8_b1_disclosure_model_foundation.sql` | ❌ no |
| `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` | ❌ no |
| `20260916000000_p8_b2_evidence_line_items.sql` | ❌ no |
| `20260916010000_p8_b2_provenance_line_links.sql` | ❌ no |

Newest applied migration: **`20260903010000_ws4_gate3_4a_item_assignment_foundation.sql`**.
There are **no** `202609*` entries at all.

**Where the migrations DID go — artifact evidence.** The apply logs were applied against
databases that already had the objects, and dedicated clone databases exist:

```
/tmp/apply_20260916010000_...line_links.sql.log:
  NOTICE: column "source_line_item_id" of relation "calculation_snapshots" already exists, skipping
/tmp/b2_clone_restore.log                                     (30 KB)
backend/tools/b2_clone_schema_harness.py                      (references both B2 objects)

Databases on 127.0.0.1:54426:
  postgres                              ← the API's target  ❌ UNMIGRATED
  carbontally_b2_clone_20260913         ← B2 clone          ✅ migrated
  ct_b2_iv_20260913                     ← B2 clone          ✅ migrated
  ct_b3_v3_20260913                     ← B3 clone          ✅ migrated
  carbontally_qa_phase8, carbontally_test
```

Missing objects in `postgres`: `evidence_line_items`, `disclosure_value_evidence`,
`disclosure_sections`, `disclosure_narrative`, `report_artefacts` — **all five MISSING**, and
the column absent.

**Blast radius (endpoints reading the broken column list).**

| Call site | Surface | Live result |
|---|---|---|
| `v3_consultants.py:1379` | Consultant client **evidence** | **500** (measured) |
| `v3_emissions.py:324` → `GET /api/v3/emissions/calculations` | **Customer** calculation history | **500** (measured) |
| `v3_emissions.py:338/520` → `GET /api/v3/emissions/calculations/{id}` | Customer calculation detail | 500 (same column) |
| `v3_emissions.py:397` | Customer evidence for a log | 500 (same column) |
| `automatic_processing.py:981` | **Automatic processing calculation stage** | latent failure — see SB-03 |

**Proven with an ordinary customer, not a consultant:** owner of *Quayside Energy* calling
`GET /api/v3/emissions/calculations?organization_id=bc197ccf-...` returns **500**
`column "source_line_item_id" does not exist` **with no ACAO header**. This is therefore **not
a consultant-specific defect**.

**Timeline — matches "worked as recently as yesterday".** `emissions_logs.py` modified
**2026-09-13 12:56**; B2 migration files written **2026-09-13 13:03** and applied only to
clones. The breakage therefore begins **2026-09-13**.

**Frontend files/routes.** `frontend/src/v3/consultant/ConsultantPage.jsx:207-229`, `:302`;
`frontend/src/v3/api.js:425,445,448,452,456,474,481`.
**Backend files/routes.** `backend/data/emissions_logs.py:52-59,304,338,354`;
`backend/api/v3_consultants.py:1352,1379`; `backend/api/v3_emissions.py:307,331,372,513`.
**Database tables.** `calculation_snapshots` (+ absent `evidence_line_items`, `disclosure_*`,
`report_artefacts`).
**Existing functionality reusable.** The repository already contains a **deliberate degraded
mode** pattern for exactly this situation — `backend/data/disclosure.py:21` documents
"*No B2/B3/B4 — no `evidence_line_items`, no `source_line_item_id`*" and guards optional use.
`_SNAPSHOT_COLUMNS` lacks any such capability probe.
**Partially implemented?** Yes — the B2 feature is implemented and verified against a clone.
**Recommended fix direction (NOT implemented).** Two independent steps, in this order:
(a) environment/release hygiene — apply the pending migrations to the target database, or
revert the working-tree code to a state matching the deployed schema;
(b) design — make the snapshot read surface capability-aware (mirroring `disclosure.py`'s
existing degraded pattern) so a schema/serving mismatch degrades instead of 500-ing.
**Dependencies.** SB-01 (amplifies impact), SB-03 (same root cause), Cline's in-flight B2 work.
**PO decision required?** No.
**Regression risk.** Medium — migration application on a live database; must be sequenced with
Cline, not by OHD.

---

### SB-03 — Automatic processing calculation stage is latently broken by the same missing column

| Field | Value |
|---|---|
| **Severity** | **P0** |
| **Classification** | BUG (latent; same root cause as SB-02) |
| **Status** | **CONFIRMED as a code/data condition — NOT yet observed as a runtime job failure** (stated honestly below) |
| **Affected workflow** | Automatic processing: `CALCULATE` stage |

**Actual behaviour.** `backend/services/automatic_processing.py:981` calls
`self._repos.logs.find_snapshot_by_request_id(request_ids[0])` on the main calculation path.
That method (`emissions_logs.py:344-358`) issues `SELECT {_SNAPSHOT_COLUMNS} ...` — which now
fails. **The call is not inside a `try`/`except`** (verified by reading the enclosing flow at
`:965-992`). The duplicate-prevention guard has therefore become a hard failure point.

**Why no job has failed yet (honest scope).** The newest queue row is **2026-09-14 05:24**
and is blocked upstream at *extraction* (my earlier audit's extraction-gate finding), so no
job has reached `calculating` since the code changed. Queue state now:

| status | stage | count | newest |
|---|---|---|---|
| approved | completed | 20 | 2026-08-29 12:38 |
| manual_review | blocked | 17 | 2026-09-14 05:24 |
| customer_review | review | 3 | 2026-08-29 13:24 |
| failed | — | **0** | — |

`SELECT count(*) FROM document_processing_queue WHERE last_error LIKE '%source_line_item_id%'`
→ **0**. **The failure is latent, not yet triggered.** It will fire on the next job that
reaches `calculating`.

**Classification.** Latent P0 — the next successful extraction triggers it.
**Recommended fix direction.** Subsumed by SB-02. Separately, a guard used on the critical
path should not be able to fail the job outright.
**PO decision required?** No.

---

### SB-04 — Workspaces load with all-or-nothing `Promise.all`, so one failing call destroys the page

| Field | Value |
|---|---|
| **Severity** | P2 |
| **Classification** | UX / robustness (architectural pattern) — **NEW** |
| **Status** | **CONFIRMED** |

**Actual behaviour.** `Promise.all` is used to load composite workspaces in **18 places**
under `frontend/src/v3`, including `ConsultantPage` (7 calls), `customer/ProcessingPage`,
`customer/DashboardPage`, `customer/DocumentsPage`, `reports/ReportsPage`,
`admin/MembersTab`, `admin/FacilitiesTab`, `ops/CommercialTab`. Any single rejection blanks the
entire workspace, and the user cannot see which panel failed or continue with the others.

**Why this matters here.** It converts SB-02 (one optional read failing) into total workspace
loss, and it is the direct reason the PO's symptom is *"the client workspace"* rather than
*"the evidence panel"*.

**Recommended fix direction (NOT implemented).** Per-call isolation
(`Promise.allSettled`) with per-panel error/empty states, keeping hard failures hard.
**PO decision required?** No (implementation pattern), though a product stance on partial
workspaces may be desirable.

---

### SB-12 — Production: cold-start latency against a 25-second client timeout

| Field | Value |
|---|---|
| **Severity** | P1 (production availability) |
| **Classification** | INTEGRATION / operational — **NEW** |
| **Status** | **LIKELY — measured, mechanism not fully reproduced** |

**Measured against `https://carbontally-api.onrender.com`:**
- First request of the session to `/` → **no response within 30 s** (curl `--max-time 30`;
  DNS 0.148 s, TCP connect 0.208 s — so the host resolved and connected, then hung).
- `/openapi.json` → **no response within 30 s**.
- `/api/v3/me/context` during warm-up → **401 in 8.44 s**.
- Immediately afterwards, once warm: `/` → **200 in 0.47–0.80 s**; `/api/v3/me/context` and
  `/api/v3/consultants/me/clients` → 401 in ~0.5–0.6 s.

**Interpretation.** The instance was asleep; the first requests were consumed by cold start.
The frontend aborts at `REQUEST_TIMEOUT_MS = 25000` (`api.js:17`). A cold start exceeding 25 s,
or a platform edge response during boot that lacks CORS headers, produces **the same**
user-facing outcome: an aborted request ("took too long") or a rejected fetch
("Network error"). **I could not force a cold start on demand**, so I cannot state which
message a given cold start produces. Classified LIKELY, not CONFIRMED.

**Also measured — CORS allowlist defects (`backend/config.py:23-36`):**
- `"https://*.onrender.com"` is a **dead entry**: Starlette matches `allow_origins` by exact
  string. Preflight from `https://foo.onrender.com` → **400, no ACAO**.
- Vercel **preview** origins are **not** allowed: preflight from
  `https://carbontally-frontend-abc123.vercel.app` → **400, no ACAO**. Any preview deployment
  therefore fails every API call with "Network error".

**Recommended fix direction (NOT implemented).** Keep-alive/health ping or a paid always-on
instance; raise or make explicit the client timeout for the first request;
remove/replace the dead wildcard; decide an explicit policy for preview origins (e.g.
`allow_origin_regex`). **PO decision required?** Yes — for the preview-origin policy and any
cost-bearing keep-alive.

---

## C. ORGANIZATION MODEL — WHAT ACTUALLY EXISTS

**CONFIRMED: the consultant's client IS a normal `organizations` row.** There is one
organization table, one membership table, one capability surface. The consultant relationship
is an **additional access path**, not a reduced organization type.

| Aspect | Reality in the repository |
|---|---|
| Client org record | `organizations` row (identical table) |
| Membership | `organization_members` — **914 of 916** client orgs have members |
| Client-staff login | Works; `client.owner.demo0001.1@…` → `actor_type: "customer"`, `workspaces: ["customer"]`, `destination: "/home"`, `role: owner` |
| Consultant link | `consultant_clients` (consultant_id, organization_id, status, lifecycle timestamps) |
| Consultant tables | `consultant_profiles`, `consultant_firm_members`, `consultant_clients`, `consultant_tasks`, `consultant_custom_domains`, `consultant_senders`, `consultant_billing` |

**`organizations` columns (68)** — note what is **absent**: there is **no `slug`, no
`organization_type`, no `status`**. Present and relevant: `is_active`, `archived_at`,
`customer_type`, `billing_mode`, **`subscription_status`, `subscription_tier`,
`subscription_id`**, `default_factor_year`, `reporting_standard`, `country`.

**Answers to the Section-6 questions:**

| Q | Finding |
|---|---|
| A. Shared correctly | Yes — org record, membership, documents, processing, reports, admin surface, client staff capabilities |
| B. Missing from consultant clients | Nothing structural found at the org level; gaps are in consultant-side management/read paths (SB-02) |
| C. Intentionally different | Only the consultant access path (`consultant_clients`) + branding |
| D. Differs by delegation only | Yes — consultant access is delegation layered over the same org |
| E. Differs accidentally | The **entitlement layer** (SB-07) treats every org identically and unconditionally denies |
| F. Two parallel org concepts? | **No** — single concept. Two parallel *subscription* concepts exist (SB-08) |
| G. Code assuming self-managed org? | `BillingService.get_entitlement` resolves entitlement purely from `organization_id` and ignores `consultant_clients` entirely (SB-07) |
| H. Code assuming consultant-managed org? | Not found |
| I. Consultant access conflicts with membership? | No conflict found; they are additive |
| J. Does RLS model the relationship? | Application-layer checks confirmed working (H.1); RLS itself not independently exercised |
| K. Does consultant access bypass tenant isolation? | **No** — cross-consultant access correctly denied (H.1) |
| L. Do client staff get the same capabilities? | **Yes** — measured: normal customer workspace |
| M. Settings/data silently unavailable? | Not proven; `docs`/`items`/`evidence` for non-active clients are 403 by design (SB-05 is the *listing* defect, not a silent-hiding defect) |

---

## D. WHITELABEL / SUBSCRIPTION MODEL

### SB-06 — WhiteLabel is not gated by any entitlement, and its UI is shown to every consultant

| Field | Value |
|---|---|
| **Severity** | **P1** (commercial/entitlement integrity) |
| **Classification** | MISSING CAPABILITY + **PRODUCT DECISION REQUIRED** — **NEW** |
| **Status** | **CONFIRMED (code + data)** |
| **Affected roles** | Consultant (all), Consultant team member with `manage_team` |
| **Affected workflow** | WhiteLabel domains/senders; consultant branding |

**Actual behaviour.**
- Every endpoint in `backend/api/v3_whitelabel.py` is gated **only** by
  `require_consultant` + `ensure_consultant_permission(context, "manage_team")`. **All ~13
  endpoints** (`custom-domains` list/create/verify/activate/remove, senders, etc.).
- There is **no** check of `white_label_enabled`, no subscription check, no plan/feature check.
- `white_label_enabled` exists and is **read only for presentation**, never for authorization:
  `data/consultants.py:28,45,86`; `api/v3_consultants.py:69,305`; `domain/branding.py:71,122,130`
  (*"consultant-only presentation"*).
- The frontend renders `<WhiteLabelTab />` **unconditionally**
  (`frontend/src/v3/consultant/ConsultantPage.jsx:1079`, inside the
  `view === 'whitelabel'` branch which any consultant can reach).
- **Data:** `consultant_profiles.white_label_enabled` → **false = 54, true = 1** (only
  `Quayside Food & Drink Advisory`). So the capability is **exposed to 55 firms, of which 54
  have the flag off**, and the backend will still accept their domain/sender operations.
- `consultant_custom_domains` = 0 rows (nobody has used it yet — nothing has leaked).

**Expected behaviour.** Per the PO's stated concept, WhiteLabel is a purchased capability.
Repository evidence does **not** establish what the entitlement source should be, so this is
flagged rather than decided.

**Root cause.** The WhiteLabel feature was built as a **consultant permission feature**, not
as an **entitlement-gated commercial feature**. `white_label_enabled` was introduced as a
presentation flag; no authorization path consumes it.

**Frontend.** `ConsultantPage.jsx:1079`, `WhiteLabelTab.jsx`.
**Backend.** `backend/api/v3_whitelabel.py` (all routes), `backend/api/consultant_auth.py:46`.
**Database.** `consultant_profiles.white_label_enabled`, `consultant_custom_domains`,
`consultant_senders`.
**Reusable functionality.** The permission layer (`ensure_consultant_permission`) and the
entitlement service (`services/billing.py`) already exist — an entitlement check would be
additive.
**Partially implemented?** Yes — feature complete, **gate absent**.
**Recommended fix direction (NOT implemented).** Add an entitlement/flag gate to the mutating
WhiteLabel endpoints and hide the tab when not entitled. **Do not** decide the commercial rule
without the PO (K.3).
**PO decision required?** **Yes.**

### SB-08 — Two parallel subscription representations; the authoritative one is empty

| Field | Value |
|---|---|
| **Severity** | **P1** (architectural; feeds SB-07) |
| **Classification** | ARCHITECTURAL GAP — **NEW** |
| **Status** | **CONFIRMED (live data)** |

**Actual behaviour — the two representations disagree:**

| Representation | State |
|---|---|
| `organizations.subscription_status` / `subscription_tier` / `subscription_id` | **POPULATED** — 940 orgs `active`/`pro`, 12 `active`/`enterprise`, 5 `trial`/`enterprise`, 4 `trial`/`pro`, 13 with only `billing_mode=CREDIT` |
| `customer_subscriptions` (plan_code, plan_version, features, limits, lifecycle_status) | **0 rows** |
| `consultant_billing` | **0 rows** |
| `billing_plans` (catalogue) | 6 rows — starter/professional/business(v1,v2)/enterprise, all `is_active` |

`services/billing.py:get_entitlement()` resolves the plan from
`billing_subscriptions.get_active_for_org()` → `customer_subscriptions` (empty) → therefore
`plan = None` and `subscription = None` for **every** organization, while a populated
`organizations.subscription_status='active'` sits **unread by the entitlement engine**.

Live confirmation for a real org (owner of *Quayside Energy*), `GET /api/v3/billing/me`:

```json
{"organization_name":"Quayside Energy","billing_mode":"CREDIT",
 "subscription":null,"plan":null,"credits":{"balance":0,"included_monthly":0}}
```

**Dead schema attached to the old model:** `customer_subscriptions.batch_upload_limit`,
`batch_upload_per_day`, `ai_extraction_limit`, `manual_extraction_pages_included`,
`stripe_*` columns — none reachable (see SB-09).

**Interpretation.** The prior subscription functionality was **disconnected, not deleted**:
its tables and one legacy column set survive. `billing_plans.features` contains only
`{"reports": true}` (and `{"custom": true}` for enterprise) — there is **no `whitelabel` and no
`batch_upload` feature key anywhere in the plan catalogue**, so no existing plan can express
either entitlement.

**Recommended fix direction (NOT implemented).** Establish a single authoritative entitlement
source and retire/align the other; this is a design decision (K.1/K.2), not a patch.
**PO decision required?** **Yes.**

---

## E. ORDINARY ORG vs CONSULTANT CLIENT — CAPABILITY COMPARISON

Measured on live data and live endpoints.

| Capability | Ordinary org (Quayside Energy) | Consultant client org (Quayside Distribution) | Verdict |
|---|---|---|---|
| `organizations` row | ✅ | ✅ | shared |
| Members (roles) | 4 (owner, admin, member, viewer) | present (914/916 orgs) | shared |
| Client-staff login → workspace | ✅ `actor_type: customer` | ✅ `actor_type: customer` | **shared** |
| `GET /api/v3/billing/me` | 200, `subscription: null` | 200, `subscription: null` | shared (equally broken, SB-07) |
| Calculation history | **500** | **500** | shared failure (SB-02) |
| Consultant access path | n/a | `consultant_clients` + consultant endpoints | intentional difference |
| WhiteLabel branding | n/a | consultant-level | intentional difference |
| Orgs with no members | 4 of 59 | 2 of 916 | minor data hygiene |

**Conclusion (CONFIRMED).** At the organization level there is **no second-class org**. The
differences are (i) the consultant access path and (ii) branding — both intentional. What
differs **accidentally** is entitlement: the commercial layer ignores the consultant
relationship completely and denies unconditionally (SB-07).

---

## F. CROSS-ROLE MATRIX (measured, not assumed)

| Role | Org context | Workflow | Result |
|---|---|---|---|
| Consultant | own firm | `/me/context` | 200, `actor_type=consultant`, dest `/consultant` |
| Consultant | own firm | `/consultants/me/clients` | 200, 15 clients |
| Consultant | own firm | `/consultants/me/dashboard` | 200 (15 clients, 13 active, 2 onboarding) |
| Consultant | own firm | `/consultants/me/branding/context` | 200 (`kind: carbon_tally`) |
| Consultant | **own active client** | reports | **500→"Network error"** (SB-02) |
| Consultant | **own ACTIVE client** | processing/status, issues, documents, items, reports | 200 ✅ |
| Consultant | **own ONBOARDING client** (listed!) | **all six workspace endpoints** | **403** (SB-05) |
| Consultant | **foreign consultant's client** (by client row id) | documents / detail | **403 "client belongs to another consultant firm"** ✅ |
| Consultant | **foreign org by raw org id** | documents / items | **404 "client not found"** ✅ |
| Customer Owner | ordinary org | `/me/context`, `/billing/me` | 200 ✅ |
| Customer Owner | ordinary org | calculations | **500** (SB-02) |
| Client-org Owner | consultant client org | `/me/context`, `/billing/me` | 200 ✅ |
| Anonymous | any protected route | — | 401 ✅ (prod + local) |

**Positive security results:** cross-consultant isolation holds at the application layer;
unknown org ids do not resolve; anonymous access is rejected. **No cross-tenant leak found.**

---

## G. UNKNOWN-UNKNOWNS FINDINGS

These are the systemic classes the PO asked to be hunted deliberately.

### SB-05 — 245 clients are listed to consultants but every one of them is unauthorized

| Field | Value |
|---|---|
| **Severity** | **P1** |
| **Classification** | BUG (UI permits / API rejects) + UX — **NEW** |
| **Status** | **CONFIRMED** |
| **Roles** | Consultant, consultant team member |

**Symptom.** The consultant's client list includes clients that open straight into an error.

**Measured.** `consultant_clients` status distribution: **active 672, onboarding 244,
inactive 1** → **245 of 917 (26.7%)** are non-active. `GET /api/v3/consultants/me/clients`
returns them (verified: *Dover Logistics*, status `onboarding`, appears in the list). Every
workspace endpoint then returns:

```
403 {"message":"Consultant is not authorized for this client organization
     (active consultant-client relationship required)"}
```

Reproduced with `13fce3fa-78d3-5424-883e-cc8432c5a83e`: reports, processing/status, issues,
documents, processing/items, evidence → **all 403**. Only `dashboard` differed (422), and that
was **my probe's fault, not a defect**: the frontend sends `start_date`/`end_date`
(`api.js:450`) whereas my probe sent `from`/`to`. Re-run with the correct parameters,
`dashboard` returns 200 — so all seven workspace calls fail on this client for the *same*
reason: no active consultant-client relationship.

**Root cause.** The list endpoint does not filter by lifecycle status while the authorization
guard requires `status = 'active'`. Two components disagree on the same field.
**Note.** The lifecycle gate itself appears deliberate (D27 lifecycle). The **defect is the
list/gate disagreement**, and the absence of any non-active state in the UI.
**Recommended fix direction (NOT implemented).** Filter or visibly mark non-active clients;
prevent selecting them; surface the lifecycle state and its meaning.
**PO decision required?** Partially — whether onboarding clients should be *openable* (K.6).

### SB-07 — Consultant submission AND customer approval are denied for every organization

| Field | Value |
|---|---|
| **Severity** | **P0 — blocks core business operation** |
| **Classification** | BUG (implemented-but-unreachable) + ARCHITECTURAL GAP |
| **Status** | **CONFIRMED (code + live data)** |
| **Roles** | Consultant, PE, internal QC, **Customer (approval)** |
| **Affected orgs** | **ALL** |

**Actual behaviour.** Two gates fail closed on an empty table:
- `services/billing.py:167-190` `ensure_processing_entitlement()` — called by the consultant
  submission path (`api/v3_processing_workflow.py:772`) — raises
  `EntitlementUnavailableError` (403) whenever
  `get_active_for_org(org)` is `None`.
- `services/billing.py:693-725` `charge_processing()` — called on **Customer Approval**
  (`api/v3_processing_workflow.py:987`, `idempotency_key=f"charge:item:{item.id}"`) — raises
  the same error, citing **(PO-D7, ratified Phase 6)**.

`get_active_for_org` (`data/billing.py:414-422`) reads:

```sql
SELECT ... FROM public.customer_subscriptions
WHERE organization_id = $1
  AND lifecycle_status IN ('trial','active','past_due','suspended')
```

Measured: `SELECT count(*) FROM customer_subscriptions` → **0**; matching rows for a real org
→ **0**. Therefore the lookup is **always** `None`, and **both gates always deny**.

**Consequence.** The ratified end-to-end chain
`… → REVIEW → CUSTOMER APPROVAL → COMPLETED → REPORTING` **cannot complete for any
organisation**, and consultant→QC submission is permanently 403. The denial messages are:

> "No active processing entitlement for this organization — consultant submission is denied.
> An organization must have an active subscription/plan before its work can be submitted to
> CarbonTally QC."

> "No active processing entitlement for this organization — chargeable processing is denied."

**Not yet observed as a runtime denial.** I did not POST the mutating endpoints (hard
boundary). The conclusion rests on: the gate code, the measured empty table, the measured
`subscription: null`, and the measured query returning 0 rows. Classified **CONFIRMED** for the
condition; the *runtime* denial follows deterministically.

**Related evidence.** 3 items have sat in `customer_review` since **2026-08-29** — consistent
with (not proof of) approval being unreachable.
**Deployment note.** The gate is **committed at HEAD** (`git show HEAD:...v3_processing_workflow.py`
contains `charge_processing`; `HEAD:services/billing.py` contains the PO-D7 comment), so it is
a deployed-code condition. Whether production's database also lacks subscriptions is
**UNVERIFIED** (no production DB access) — flagged.
**Recommended fix direction (NOT implemented).** Decide how entitlement is established when no
subscription-management system is live (K.1). Do **not** simply remove the gate — PO-D7 is
ratified.
**PO decision required?** **Yes — this is the single highest-priority PO decision in this
report.**

### SB-09 — Batch upload is hard-disabled and unconnected to the entitlement columns that exist

| Field | Value |
|---|---|
| **Severity** | **P1** (core product capability) |
| **Classification** | MISSING CAPABILITY + PRODUCT DECISION REQUIRED |
| **Status** | **CONFIRMED (reconfirms previous audit, unchanged)** |

`backend/routes/upload.py:288` returns a **hardcoded** `"status": "premium_feature"` — no
entitlement lookup at all. Meanwhile `customer_subscriptions.batch_upload_limit` and
`batch_upload_per_day` exist but are unreachable (table empty, and no code reads them).
**So the batch entitlement columns are dead schema, and batch upload is unconditionally
unavailable.** Consistent with my previous audit (legacy multi-file endpoint hard-returns
`limit: 1`; V3 accepts one file; `document_processing_queue.batch_id` NULL for 40/40).

### SB-10 — No organization/consultant/client → Processing Entity assignment persistence

| Field | Value |
|---|---|
| **Severity** | **P1** |
| **Classification** | ARCHITECTURAL GAP — reconfirms previous audit |
| **Status** | **CONFIRMED** |

| Question | Evidence |
|---|---|
| Assignment-rule model? | **No** — no `%rule%`/`%routing%`/`%auto_assign%` table |
| org → PE? | **No** — `organizations` has **no** `%entit%`/`%process%`/`%assign%`/`%consult%` column |
| consultant → PE? | **No** — `consultant_clients` has **no** PE column |
| client → PE? | **No** |
| batch-level assignment? | `processing_assignments`, `work_item_assignments`, `review_assignment_history`, `reassignment_history`, `processing_entities` exist (work-item level) |
| Upload-time auto-assignment? | Not found |
| Notification infra? | **Exists**: `notifications`, `notification_templates`, `notification_delivery` |
| No-rule behaviour / multiple matches / override / who configures / auditing | **Not established by the repository** — nothing to read |

**PO decision required?** Yes (routing policy).

### SB-11 — Auditor test artifact left in the shared investor demo dataset

| Field | Value |
|---|---|
| **Severity** | P2 |
| **Classification** | DATA/PROVENANCE (demo hygiene) — **NEW** |
| **Status** | **CONFIRMED** |

`consultant_clients` contains **`AUDIT-TEMP Consulting Client Ltd`**, status `active`,
created **2026-08-28**, owned by *Falcon Technologies Advisory*. It is the **first** client
returned for `consultant.demo0001`, so it is also what the workspace auto-selects.

Two issues: (i) §55 demo-safety requires labelled mutation-test records to be **cleaned up and
the cleanup verified** — this one was not; (ii) its single owner membership
(`organization_members`, role `owner`) has **no matching `auth.users` row** → an **orphaned
membership**, so no client user can ever sign into it.

**Recommended fix direction (NOT implemented).** Remove/relabel with the PO's approval; add a
referential-integrity check.

### SB-13 — CORS allowlist contains a non-functional wildcard

Covered in SB-12. `"https://*.onrender.com"` (`backend/config.py:34`) never matches; preflight
from `https://foo.onrender.com` → **400, no ACAO**. Severity **P3** (config hygiene), but it
signals a false assumption about wildcard support.

### SB-14 — `organizations` lacks `slug`, `organization_type`, and `status`

`organizations` (68 columns) has **no `slug`, no `organization_type`, no `status`**; lifecycle
is `is_active` + `archived_at`, and classification lives in `customer_type`/`billing_mode`.
Any spec or UI assuming an org "slug"/"type"/"status" does not match the schema. Recorded as an
**informational structural fact** (P3), because three different audits have now asked for
"organization slug".

---

## H. SECURITY FINDINGS

### H.1 Positive verification (no leak found)

| Test | Result |
|---|---|
| Consultant A → consultant B's client (client row id) | **403** "client belongs to another consultant firm" ✅ |
| Consultant A → consultant B's client (raw org id) | **404** "client not found" ✅ |
| Consultant A → own active client | 200 ✅ |
| Anonymous → `/api/v3/consultants/me/clients` (local + production) | **401** ✅ |
| Client-org owner → own org | 200 ✅ (scoped to own org) |

Cross-tenant isolation holds at the **application** layer for the consultant surface. I found
**no** consultant→client privilege escalation and **no** cross-consultant data exposure.

### H.2 SECURITY / ACCESS-CONTROL ISSUE — WhiteLabel operations available without entitlement (SB-06)

Not a tenant-isolation break, but a **commercial-authorization** gap: an entitlement-bearing
capability (custom domains, verified senders — which touch **email/DNS sender identity**) is
obtainable by any consultant firm member holding `manage_team`, with no purchase and no
`white_label_enabled`. Classified **SECURITY / ACCESS-CONTROL ISSUE (commercial authorization)**,
severity **P1**. Mitigating fact: `consultant_custom_domains` is currently empty, so nothing
has been mis-claimed yet. **Not exploited beyond what was necessary to establish it** (code +
data inspection only; no domain was created).

### H.3 Information-disclosure consequence of SB-01

The generic 500 handler writes the **raw exception string** into the response body
(`main.py:358-375`, message = `str(exc)`). Users cannot read it (blocked by CORS) but any
non-browser client can, and it is echoed to the console. Examples captured:
`column "source_line_item_id" does not exist`. Not a secret leak, but it is **internal
schema detail exposed on a public endpoint** and it becomes the user-facing message for any
non-browser consumer. Severity **P2**.

---

## I. RECONCILIATION WITH THE PREVIOUS OHD AUDIT

| Previous finding | Status now | Evidence |
|---|---|---|
| Extraction result discarded by completeness gate | **STILL PRESENT** | Newest job 2026-09-14 05:24 `manual_review/blocked`, `reason` = completeness below threshold; 0 jobs completed since 2026-09-11 |
| P0 factor-matching correctness (wrong row at confidence 1.00) | **STILL PRESENT — unchanged** | `backend/infra/search_index.py:132-177` docstring still: *"score is the fraction of query tokens present in the factor's activity_type tokens (1.0 = every token matched). Results are ordered deterministically: score descending, then activity type and id ascending"* — no component/total discriminator, no fix |
| PDF viewer re-navigation / re-signing | **STILL PRESENT** | `viewer_url` still derived from a per-request signed URL; 10 s poll unchanged (`ProcessingItemWorkspace.jsx`) |
| Blocked jobs with no practical recovery | **STILL PRESENT** | 17 blocked, `reenqueue(stage="extracting")` no-op unchanged |
| Batch upload missing / hard-disabled | **STILL PRESENT** | `routes/upload.py:288` hardcoded `premium_feature` |
| PE auto-assignment gaps | **STILL PRESENT** | No org/consultant→PE persistence (SB-10) |
| Missing PE notifications | **NOT RE-TESTED** | Notification tables exist; no PE notification written in the examined paths. Not re-verified this session — **remains open** |
| Multiple/parallel batch concepts | **STILL PRESENT** | `batch_id` NULL 40/40; batch row `total_documents=1` holding 47 items |
| Customer/org factor-source governance | **STILL OPEN as PO decision** | Not re-audited this session |
| Raw-table pagination | **STILL PRESENT** | `DataTable` ships `defaultPageSize = 10`; 22 V3 files still hand-roll `<table>` |
| CSS cascade leak (`.v3-meta-list`) | **NOT RE-TESTED** | Out of scope this session |
| Evidence/provenance, contradictory snapshots, missing calculation linkage | **SUPERSEDED IN PART by SB-02** | The B2 line-link work *is* the fix for calculation linkage — currently unrunnable because its schema is unapplied |

**New this session (not in the previous audit): SB-01, SB-02, SB-03, SB-04, SB-05, SB-06,
SB-07, SB-08, SB-11, SB-12, SB-13, SB-14.**

**Correction of my own earlier framing.** My previous audit's context summary treated PDF
MIME (`application/octet-stream`) as the viewer defect. That remains contradicted by
measurement (stored PDFs and signed URLs serve `application/pdf`); the viewer defect is the
per-request re-signing. No change to that conclusion.

---

## J. RECONCILIATION WITH PHASE 8 / PHASE 8-X / P1

Classification per the eight allowed categories.

| Finding | Classification |
|---|---|
| SB-01 (500 loses CORS) | **4. SEPARATE PRE-EXISTING PRODUCT DEFECT** — independent of Phase 8 |
| SB-02 (B2 column vs unmigrated DB) | **3. AUTHORIZED PHASE 8 / 8-X WORK (in-flight, B2)** — *environment/sequencing* issue, not a new workstream. Must go to Cline; OHD must not "fix" it. |
| SB-03 (calculation stage latent) | **3. AUTHORIZED PHASE 8 / 8-X WORK** (same root cause as SB-02) |
| SB-04 (`Promise.all` workspaces) | **4. SEPARATE PRE-EXISTING PRODUCT DEFECT** |
| SB-05 (245 listed-but-403 clients) | **4. SEPARATE PRE-EXISTING PRODUCT DEFECT** |
| SB-06 (WhiteLabel ungated) | **5. NEW PO PRODUCT DECISION REQUIRED** (+ 6. commercial-access issue) |
| SB-07 (entitlement empty → approval denied) | **4. SEPARATE PRE-EXISTING PRODUCT DEFECT** + **5. NEW PO PRODUCT DECISION REQUIRED** |
| SB-08 (dual subscriptions) | **4. SEPARATE PRE-EXISTING PRODUCT DEFECT** (architectural) |
| SB-09 (batch upload) | **4. SEPARATE PRE-EXISTING** (reconfirmed) + **5. PO DECISION** |
| SB-10 (PE routing) | **4. SEPARATE PRE-EXISTING** + **5. PO DECISION** |
| SB-11 (`AUDIT-TEMP`) | **4. SEPARATE PRE-EXISTING** (demo hygiene) |
| SB-12 (cold start / timeout) | **4. SEPARATE PRE-EXISTING** (operational) + **5. PO DECISION** (cost/origin policy) |
| SB-13, SB-14 | **4. SEPARATE PRE-EXISTING** (config/structure) |
| Previous audit's factor-matching P0 | **8. NEEDS FURTHER EVIDENCE** for Phase-8/P1 mapping — its remediation is **not** in B1–B4 and **is not** covered by the in-flight extraction work. Do **not** assume P1 covers it. |

**Boundary explicitly respected.** I have **not** expanded P1, **not** reopened B1/B2/B3/B4,
**not** reinterpreted any ratified decision, and **not** created a Phase 9. SB-02/SB-03 sit
inside Cline's authorized lane and are reported *to* that lane; the standalone defect in the
same area is **SB-01**, which is not Phase 8 work at all.

---

## K. PRODUCT DECISIONS REQUIRED

**K.1 — Where does processing entitlement come from, now that no subscription system is live?**
*Why evidence cannot answer it:* PO-D7's fail-closed rule is ratified, but the repository
contains **two** populated/empty subscription representations and no live provisioning path.
*Smallest reasonable options:* (a) provision `customer_subscriptions` rows for all orgs;
(b) make the entitlement gate read the populated `organizations.subscription_status/tier`;
(c) temporarily suspend the gate in non-production environments only; (d) leave as-is.
*Recommended:* (b) with explicit PO sign-off, or (a) — **never** silently drop the gate.
*Downstream:* consultant submission, customer approval, charging, credits, reports, batch.
**This is the highest-priority decision in the report.**

**K.2 — Which subscription representation is authoritative?** One must be retired or formally
aligned. *Downstream:* billing, entitlement, admin UI, legacy org management routes.

**K.3 — Is WhiteLabel gated by purchase, and by what?** Must the entitlement be a plan feature
(`billing_plans.features`), the `white_label_enabled` flag, or a new entitlement? May firms with
the flag off keep using it? *Downstream:* whitelabel API, consultant branding, commercial.

**K.4 — Do consultant client organisations own subscriptions, or does the consultant's
WhiteLabel subscription govern?** Section 5 asks this directly; the repository establishes
neither. Note the current code resolves entitlement from **`organization_id` only** and ignores
`consultant_clients` entirely. *Downstream:* SB-07, SB-08, consultant billing
(`consultant_billing` exists, empty, keyed by consultant+client).

**K.5 — Client limits per WhiteLabel consultant, and consultant entitlement expiry/suspension
behaviour.** Nothing in the repository defines either.

**K.6 — Should non-active (onboarding/inactive) consultant clients be openable?** 245 clients
are listed and unauthorized. If they must not be openable, the list must say so.

**K.7 — Batch upload policy** — still outstanding (reconfirmed dead schema).

**K.8 — Emission-factor source policy** (UK default, per-org choice) — still outstanding from
the previous audit; not re-audited this session.

**K.9 — PE routing policy** (rule source, no-match behaviour, multi-match, override,
configuration authority, audit) — nothing established (SB-10).

**K.10 — Production availability policy** — always-on instance versus accepting cold starts,
and the client timeout / preview-origin policy (SB-12).

---

## L. RECOMMENDED NEXT WORK ORDER

**Do not implement any of this from this report.** Sequence:

1. **PO: K.1** — entitlement source. Nothing downstream is trustworthy until this is answered.
2. **Cline (in-lane, not OHD): SB-02 / SB-03** — reconcile the running code with the target
   database schema (apply the pending B1/B2 migrations, or revert the advanced column list).
   This restores the consultant client workspace and customer calculations. Confirm with the
   PO before mutating any database.
3. **SB-01 (independent of Phase 8, high leverage)** — stop 500s from masquerading as network
   errors. Nearly every other finding in this report was invisible to the PO because of it.
4. **SB-07** — unblock consultant submission and customer approval once K.1 is decided.
5. **SB-05** — stop listing clients that cannot be opened (cheap, high UX value).
6. **SB-06** — gate WhiteLabel (or explicitly decide it is ungated).
7. **SB-04** — per-panel error isolation in composite workspaces.
8. **SB-08 / SB-09 / SB-10 / K.7–K.9** — architectural backlog, after PO decisions.
9. **SB-11 / SB-14 / SB-13** — housekeeping.
10. **Re-verify the previous audit's remaining items** — especially the factor-matching P0 and
    PE notifications, neither of which is covered by the in-flight Phase 8 work.

---

## M. DEPENDENCIES

- SB-02/SB-03 ↔ Cline's in-flight B2 work and the migration state of `postgres`.
- SB-01 independent; amplifies every other failure's user-visible impact.
- SB-07 depends on K.1; SB-06 on K.3; SB-08 on K.2.
- SB-09 depends on K.7 and on SB-08 (entitlement source).
- SB-04 interacts with every composite workspace.
- SB-12 depends on K.10 (cost).
- Production verification was **not possible** for: production DB schema, production
  subscription rows, production customer approval.

---

## N. REGRESSION / SECURITY CONCERNS

1. **Applying pending migrations is a production-risk operation** if performed without the PO's
   explicit approval — four Phase 8 migrations are pending, not one.
2. **Do not "fix" SB-07 by deleting the entitlement gate** — it is a ratified PO-D7 control.
3. **Do not "fix" SB-01 by suppressing errors** — the goal is to let genuine errors surface.
4. **SB-06 is a commercial-authorization gap, not a tenant-isolation gap** — do not overstate it
   as a data breach, and do not understate it either (it governs customer-facing sender
   identity).
5. **The 500 handler echoes raw exception text** (H.3) — any fix must not widen that exposure.
6. **Orphaned membership (SB-11)** suggests referential integrity between
   `organization_members.user_id` and `auth.users` is not enforced — worth a dedicated check.
7. RLS itself was **not** exercised directly this session (no RLS-level test); application-layer
   authorization was. A separate RLS verification should not be assumed complete.
8. `"https://*.onrender.com"` shows a false belief in wildcard support; other placeholders may
   share it.

---

## O. EXACT FILES / ROUTES / SCHEMA INSPECTED

**Frontend.** `src/v3/api.js` (21-33, 35-83, 373-389, 387, 425-487, 1098-1108, 1456-1465);
`src/v3/consultant/ConsultantPage.jsx` (195-265, 302, 820-900, 1070-1085);
`src/v3/consultant/WhiteLabelTab.jsx`; `src/v3/customer/ProcessingPage.jsx`;
`app/…` routes `/consultant`, `/consultant/items/:clientId/:itemId`.

**Backend.** `main.py` (173-190, 262, 336-375); `config.py` (23-42);
`api/router.py`, `api/dependencies.py`, `api/consultant_auth.py` (19, 46);
`api/v3_consultants.py` (69, 219-250, 305, 457-500, 947, 1352-1379);
`api/v3_emissions.py` (307, 324, 331, 338, 372, 397, 513, 520);
`api/v3_processing_workflow.py` (68, 728-800, 975-1000, 987);
`api/v3_billing.py` (26, 95-115); `api/v3_commercial.py` (41, 581, 671);
`api/v3_whitelabel.py` (10, 80-330); `services/billing.py` (87-190, 693-730);
`services/automatic_processing.py` (965-992, 981); `data/emissions_logs.py` (40-60, 295-360);
`data/consultants.py` (28, 45, 50, 86, 117); `data/billing.py` (414-431);
`data/disclosure.py` (21, 577-684); `data/evidence_line_items.py`;
`domain/branding.py` (11, 71, 122, 130); `routes/upload.py` (288);
`routes/organizations/management.py` (81-82, 232-233); `infra/search_index.py` (132-177);
`tools/b2_clone_schema_harness.py`.

**Routes exercised.** `/api/v3/me/context`, `/api/v3/consultants/me`,
`/api/v3/consultants/me/clients`, `/api/v3/consultants/me/dashboard`,
`/api/v3/consultants/me/branding/context`,
`/api/v3/consultants/clients/{id}/{reports,dashboard,processing/status,issues,documents,processing/items,evidence}`,
`/api/v3/emissions/calculations`, `/api/v3/billing/me`, `/api/v3/documents`,
`/api/v3/emissions/summary` (nonexistent — probe artifact, not a defect), plus CORS preflights.

**Schema.** `organizations` (68 cols), `organization_members`, `consultant_profiles`,
`consultant_firm_members`, `consultant_clients`, `consultant_custom_domains`,
`consultant_senders`, `consultant_billing`, `consultant_tasks`, `customer_subscriptions`,
`billing_plans`, `billing_*`, `document_processing_queue`, `manual_extraction_items`,
`calculation_snapshots`, `notifications`, `notification_templates`, `notification_delivery`,
`processing_entities`, `processing_assignments`, `work_item_assignments`,
`review_assignment_history`, `reassignment_history`, `supabase_migrations.schema_migrations`,
`information_schema.columns`/`tables`.

**Artifacts.** `/tmp/apply_2026091{4,5,6,7}*.sql.log`, `/tmp/b2_clone_restore.log`,
`/tmp/b3apply_*`, `/tmp/b3re_*`; databases `carbontally_b2_clone_20260913`,
`ct_b2_iv_20260913`, `ct_b3_v3_20260913`, `carbontally_qa_phase8`, `carbontally_test`.

---

## P. EVIDENCE AND REPRODUCTION RESULTS

**P.1 CORS / status matrix** (identical request pattern with `Origin: http://localhost:3000`):

```
200 /api/v3/consultants/me/clients                        ACAO=1
403 /api/v3/consultants/clients/{foreign}/issues          ACAO=1
404 /api/v3/consultants/me/profile                        ACAO=1
422 /api/v3/consultants/clients/{id}/dashboard?from=…     ACAO=1
500 /api/v3/consultants/clients/{id}/evidence             ACAO=0   ← SB-01
```

**P.2 Consultant client workspace, 7-call reproduction** (`consultant.demo0001`):

```
reports                200      processing/items       200
dashboard             (200 with the frontend's params)  evidence   500 ← kills Promise.all
processing/status      200      issues                 200
documents              200
```

**P.3 Customer (ordinary org) — same failure class:**

```
GET /api/v3/emissions/calculations?organization_id=bc197ccf-…
→ 500 {"error":{"code":500,"message":"column \"source_line_item_id\" does not exist"}}
→ ACAO absent
```

**P.4 Schema proof:**

```
SELECT ... WHERE column_name LIKE '%line_item%'                       → 0 rows
SELECT id,...,source_line_item_id,... FROM calculation_snapshots      → ERROR: does not exist
evidence_line_items / disclosure_value_evidence / disclosure_sections
  / disclosure_narrative / report_artefacts                           → all MISSING
newest applied migration                                              → 20260903010000
applied 202609* migrations                                            → none
```

**P.5 Entitlement proof:**

```
SELECT count(*) FROM customer_subscriptions                           → 0
active-subscription query for a real org                              → 0
GET /api/v3/billing/me (owner, Quayside Energy)                       → subscription:null, plan:null
```

**P.6 Client lifecycle:** `active 672 / onboarding 244 / inactive 1`; *Dover Logistics*
(onboarding) appears in `/me/clients` and 403s on all six workspace endpoints.

**P.7 WhiteLabel:** `white_label_enabled` false 54 / true 1; `consultant_custom_domains` 0;
all `v3_whitelabel.py` routes gated only by `require_consultant` + `manage_team`;
`ConsultantPage.jsx:1079` renders the tab unconditionally.

**P.8 Production:** 538 routes, **0** B1/B2-era routes (⇒ production runs pre-B2 code, so SB-02
is **not** live there); cold start measured (≥30 s hang, then 0.47-0.80 s warm);
`https://*.onrender.com` and Vercel preview origins → preflight **400, no ACAO**.

**P.9 Negative security tests** — foreign client 403, foreign org 404, anonymous 401 (local and
production).

**P.10 Not reproduced / not verified.** UI-level browser walkthrough (tooling unavailable);
production DB schema and subscription rows; production approval path; RLS-level tests; the
previous audit's PE-notification and CSS findings; the factor-matching P0's runtime behaviour
(code-level reconfirmation only).

---

## Q. FINAL RULE ACKNOWLEDGEMENT

This report makes no completion claim. Nothing was implemented, fixed, migrated, or altered.
The purpose — exposing the classes of defect not yet thought to look for — produced one
finding that explains the PO's own misdiagnosis (**SB-01**), one that blocks the entire
commercial workflow (**SB-07**), and one that explains the reported consultant failure and its
true (non-consultant-specific) scope (**SB-02/SB-03**). Findings that require implementation
are handed to Cline through the PO; OHD has not redirected or expanded any authorized Phase 8
or Phase 8-X work.
