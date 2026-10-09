# CT-CARBONTALLY-FOUNDATION-REMEDIATION-03

**Task:** resolve the specific discrepancies left open by `CT-CARBONTALLY-FOUNDATION-CLOSURE-02`
(B-03 canonical-unit contract, B-21 local/live F-1 drift, the two remaining test failures, the
unverified recovery restore, I-06 authentication review, and the F-04/F-05/B-09/B-13/B-19/B-20/PD
register), then state foundation acceptance readiness honestly.

**Date:** 2026-10-09/10 (times +06)
**Branch:** `p8-release-reconciled`
**Agent:** Cline (implementation + verification)
**Classification:** `COMPLETE_WITH_OBSERVATIONS` — **no product acceptance is claimed** (AGENTS §73/§74)

---

## 0. Authority, safety and provenance

* **Worktree preservation.** Nothing was reset, cleaned, stashed, checked out destructively,
  rebased or force-pushed. `.gitignore` and `frontend/App_.js` (both tracked-modified *before* this
  task and unrelated to it) are **still modified and were deliberately not staged**; every untracked
  root artefact (`8`, `=`, `nohup.out`, `.costrict/`, `.p18_audit_tmp/`, `Research/`,
  `costrict-p3-ov-01-…txt`, the `.docx#` lock file) is untouched. Only explicit task-owned paths
  were staged (§10).
* **Secrets.** No credential, token, service-role key, JWT or DSN value appears in this report or in
  any captured log. Database output carries host/port/dbname only; passwords were read into scratch
  environment files (`chmod 600`) and never printed. The one live-side credential used
  (`backend/.env` → `SUPABASE_LIVE_POSTGRES_DATABASE_URL`) is untracked and ignored (`.gitignore:83`
  → `.env*`).
* **Environment classification.** The Supabase project reached for read-only comparison is the
  **live demo** environment. It is **not** production and is not described as such.
* **Provenance rule retained** (CLOSURE-02 §0): `SOURCE ≠ RUNTIME ≠ DATABASE ≠ TEST ≠ DOCUMENTED`.
  Every claim below names the state it was measured in; historical reports were used only as
  regression targets.

---

## 1. Refreshed baseline (measured before any edit)

| Item | Value | Evidence |
|---|---|---|
| Repository | `/home/shomonrobie/ct_93d5cdd` | `pwd` |
| Branch | `p8-release-reconciled` | `git branch --show-current` |
| HEAD at task start | **`fb88cde839bcb55f3f77dd465ec5f6ec3b8a0ac3`** | `git rev-parse HEAD` |
| GitHub tip at task start | **`fb88cde…`** (`refs/heads/p8-release-reconciled`) | `git ls-remote github p8-release-reconciled` |
| Divergence vs GitHub | **0 ahead / 0 behind** | `git rev-list --left-right --count github/…...HEAD` |
| Divergence vs local-path remote `origin` = `/tmp/ct_step2` | 0 ahead / **234 behind** | same, vs `origin` |
| Tracked-modified at task start | 2 (` .gitignore`, `frontend/App_.js`) — both pre-existing/unrelated | `git status --porcelain` |

---

## 2. B-03 — canonical-unit contract (Phase 1)

### 2.1 What `canonical_unit` actually is (evidence)

`canonical_unit()` (`backend/engines/invoice_extraction.py:268`) is the **deterministic invoice
item-table parser's physical-unit gate**. `None` means *the row is dropped*
(`extract_invoice_lines` lines 320-322: `unit = canonical_unit(...)` / `if not unit: continue`).
A **second**, platform-wide vocabulary exists in `backend/core/units.py` (`UNIT_ALIASES` +
`normalize_unit`) — the D23/§23 single normaliser, used by the factor/mapping/disclosure paths
(`data/emission_factors.py:149`, `services/automatic_processing.py:1360-1366`,
`services/ai_document_extraction.py:76`, `domain/disclosure_projection.py:174`).

| Token | `canonical_unit` (parser gate) | `normalize_unit` (central) | Contract verdict | Authority |
|---|---|---|---|---|
| `"units"` | `None` → row dropped | `"units"` passthrough | **Count token, not a physical unit** — correctly not canonical (the factor set is physical-unit based). Whether such rows must still be *surfaced* is a PO decision (PD-C). | P12-IMPL-01 §13 ("unknown units rejected unless in the unit vocabulary"); AGENTS §23/§25 |
| `"unit"` / `"each"` | `None` | passthrough | Same class as `units`. | as above |
| `"GBP"` | `None` → row dropped | `"GBP"` passthrough; `is_currency_unit("GBP") is True` | **Currency, never a physical unit.** Dropping a currency-in-unit-column row is the *ratified* P1 false-positive protection. Currency activity is supported as **spend-based** activity (customer factor + `mapping_no_factors_reason` / `spend_mapping_suggestion`), not by a physical factor. | P12-IMPL-01 §13 ("currency-as-unit (`GBP`) … a row whose unit is a currency is dropped"); `core/units.py::CURRENCY_UNITS`; CL-47 |
| `"mi"` | **`None` → row dropped (defect)** | `"mi"` (alias gap) | **Standard miles abbreviation — a *physical* unit.** `miles` was already accepted in *both* vocabularies, so `mi` was a missing spelling, not new vocabulary. | AGENTS §23; CL-3/CL-14; corpus ground truth |

### 2.2 Measured consequence of the unit gate over the local corpus

Read-only sweep of `…/carbon_tally_synthetic_documents/output_all_variations` (536 PDFs; 321 with a
text layer and a recognised item-table header), grouping every row that `_ROW_RE` matched but the
unit gate dropped:

| Measure | Before | After B-03a fix |
|---|---|---|
| Rows dropped by the unit gate | **147** | **111** |
| Files with ≥1 dropped row | 50 | 38 |
| Files whose *only* rows were dropped | 49 | 37 |
| Dropped tokens | `units` 111, **`mi` 36** | `units` 111 |

Verbatim printed rows behind the `mi` drops (`border_double_trav.pdf`):
`Mileage claims - Client Meeting 700 mi GBP0.38 GBP266.70` — ground truth
`line_item_count: 3`, `document_type: travel_document`. The parser returned **0 rows** for the whole
document: the mileage activity disappeared before mapping (silent under-reporting — AGENTS
§21/§22/§74). Corpus-wide, **12 travel documents recovered**; 72 travel PDFs were reviewed and 39 now
yield rows.

### 2.3 Decision taken (B-03a: FIXED) and decisions **not** taken

* **B-03a — FIXED (justified, no policy change).** `mi` → `miles` added to the single central alias
  table (`backend/core/units.py::UNIT_ALIASES`) **and** to the parser's alias table
  (`invoice_extraction._UNIT_ALIASES`). `miles` was already an accepted physical unit in both
  vocabularies, the corpus ground truth expects those lines, and no new unit was invented. Focused
  regression tests added (§9). Measured: 36 rows / 12 files recovered, **0 lost**, `units` drops
  unchanged.
* **B-03b — PO DECISION REQUIRED (`PD-C`), NOT implemented.** Whether a printed *count/spend* unit
  (`units`, `each`, `GBP`) should (A) keep being dropped fail-closed — current ratified behaviour,
  pinned by `test_count_token_units_is_not_a_physical_unit` — (B) be surfaced as an unresolved line
  item preserving `unit_raw`/quantity with the honest "no physical factor / spend path" reason
  (AGENTS §21/§22), or (C) gain a spend/count factor path. **Size of the decision: 111 rows in 38
  documents** (37 of them ground-truth at 3 lines) currently vanish. Changing `canonical_unit`
  semantics or the parser's emission contract is product policy (AGENTS §62) and was **not** made.
* **B-03c — REGISTERED (hygiene, no behaviour change).** The parser vocabulary carries `"grosscv"`,
  which `_ROW_RE`'s unit group (`[A-Za-z][A-Za-z³]{0,5}` → max **6** characters) can never match:
  dead vocabulary. The parser's duplication of `core/units.py` (§23) remains but is **benign for
  matching** — both runtime call paths normalise the row's unit centrally before the factor lookup
  (call sites verified above). No change; folded into the normaliser-consolidation backlog.

---

## 3. The two remaining test failures (Phase 3) — reproduced, classified, fixed

### 3.1 Backend — `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`

**Reproduced on the current tree** (`PYTEST_RC=1`, same assertion):
`assert body["verification_delivered"] is False` → `assert True is False`.

**Causal proof (not attribution by assertion)** — the test **passes** when the delivery credential is
neutralised in the process environment:

```
$ cd backend && RESEND_API_KEY= ./.venv/bin/python -m pytest \
      tests/unit/api/test_v3_discovery.py -k test_create_request_as_admin -q
1 passed  →  RC=0
```

**Mechanism (source-verified):** the route calls
`send_transactional_email(..., settings_repo=repos.settings)` (`api/v3_discovery.py`), which resolves
the *provider* from persisted platform settings (default `resend`) and the *credential* from the
environment — `services/email_provider.py::deliver_email_sync` → `_resend_client(env_name)`, where
`env_name = RESEND_API_KEY`. This developer environment exports `RESEND_API_KEY`, so the documented
"not configured (local/dev)" path returns `delivered=True` and attempts a real send **inside a unit
test**.

**Classification: environment-dependent test assumption + missing test isolation** (the assertion
comment "Email delivery is NOT configured in unit tests" was an assumption about the developer
environment, not a hermetic property). No product defect — delivering honestly through the configured
provider is the documented behaviour.

**Fix (minimal, hermetic, assertion unchanged):** the test now pins the three credential environment
variables to *unset* via the `monkeypatch` fixture, exercising the same code path deterministically
and removing the unintended outbound send. The `is False` assertion is untouched.

**Result:** `tests/unit/api/test_v3_discovery.py` → **16 passed, `PYTEST_RC=0`** (whole file).

### 3.2 Frontend — `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` (Issue 3)

**Reproduced** (`JEST_RC=1`): `Expected substring: "Natural gas"` / `Received string: "Mapped activity"`.

**Root cause (DOM-verified, not inferred):** `ReviewDetailPage` renders each key fact as

```jsx
<div className="v3-meta-item">
  <div className="k">Mapped activity</div>
  <div className="v">Natural gas</div>
</div>
```

`screen.getByText('Mapped activity')` returns the **label cell**, so `.closest('div')` returned that
cell itself and the assertion could never observe the value — a **test-scope defect**, not the
mapped-activity display defect recorded as B-22 in CLOSURE-02 §1.7. The component logic
(`data.mapped_data?.activity_type || data.mapped_data?.activity || '—'`) is correct and does render
`Natural gas`.

**Fix (minimal, scope corrected, assertions neither weakened nor skipped):** the query now selects
the meta row (`.closest('.v3-meta-item')`); `toContain('Natural gas')` and `not.toContain('—')` are
unchanged, so the test still fails if the value regresses to an em dash.

**Result:** **2 passed, `JEST_RC=0`.**

---

## 4. B-21 — local/live F-1 drift (Phase 2)

### 4.1 Which database each component actually uses (measured; credentials never printed)

| Component | Points at | Evidence |
|---|---|---|
| API `:8070` | `SUPABASE_URL=http://127.0.0.1:54430` → `carbontally_demo_lab_gateway` (nginx) | `/proc/<pid>/environ` |
| `carbontally_demo_lab_postgrest` | `PGRST_DB_URI` → **`carbontally_demo_local`**; `PGRST_DB_ANON_ROLE=anon`, schemas `public` | `docker inspect` (URI reported as host/port/user/dbname only) |
| `carbontally_demo_lab_storage` | `DATABASE_URL` → **`carbontally_demo_local`** | `docker inspect` |
| `supabase_auth_carbon_ledger` (GoTrue) | `GOTRUE_DB_DATABASE_URL` → **`postgres`** | `docker inspect` |

⇒ **The local stack is itself split**: business data in `carbontally_demo_local`, auth (GoTrue) in
`postgres`. The *runtime application database* is unambiguously **`carbontally_demo_local`**; the
investor-demo generation is `postgres` (legacy 46-row ledger, 975 organisations — untouched here).
`ct_local_93d5cdd` (135 tables, no `auth` schema, 0 factors) is a third, older generation that does
not even contain the two CT-03 tables.

### 4.2 The drift, and why "grants" ≠ "RLS behaviour"

| Environment | CT-03 tables ACL | RLS | policies | effective client access |
|---|---|---|---|---|
| live Supabase project (demo) | `{postgres=arwdDxtm, service_role=arwdDxtm}` | enabled | 0 | denied — no privilege |
| local runtime `carbontally_demo_local` (before) | `{postgres=…, **anon=r**, **authenticated=arwd**, service_role=…}` | enabled | 0 | denied by **RLS only** |
| `ct_local_93d5cdd` / `postgres` | tables absent | — | — | n/a |

Neither local generation has a `supabase_migrations` schema at all (**no ledger**) — the precise,
evidenced root cause of the drift: the runtime DB was provisioned outside the migration ledger, so it
carries no applied-state record and cannot be reconciled in the ledger sense.

**Effective-privilege probes before remediation** (transaction + `SET LOCAL ROLE`, rolled back —
deliberately behavioural, not privilege inspection):

```
anon          SELECT consultant_mode_change_requests → 0 rows (RLS default-deny, no error)
authenticated SELECT consultant_mode_change_requests → 0 rows
authenticated INSERT ...                             → ERROR: new row violates row-level security policy
```

⇒ the historical B-21 framing is confirmed but its **risk** was over-stated: client roles were denied
by RLS evaluation alone — exactly the posture the F-1 migration's own root-cause note describes. The
gap was **defence-in-depth / state parity**, not an exploitable hole; but any future permissive policy
would have exposed it immediately.

### 4.3 Remediation applied (authorised, non-destructive, reversible)

The committed migration
`supabase/migrations/20261105000000_ct_consultant_model_03_request_tables_revoke_client_roles.sql`
(ACL-only `REVOKE`/`GRANT`, one transaction, **fail-closed post-condition**, self-documented as
"hardening only, additive and idempotent … cannot widen access") was applied **verbatim** to the
established runtime database:

```
docker exec -i supabase_db_carbon_ledger psql -X -q -v ON_ERROR_STOP=1 -U postgres \
  -d carbontally_demo_local < …/20261105000000_…revoke_client_roles.sql
NOTICE:  CT03 F-1 closure: public.consultant_relationship_requests is service-role only, RLS enabled
NOTICE:  CT03 F-1 closure: public.consultant_mode_change_requests   is service-role only, RLS enabled
APPLY_RC=0
```

Pre-requisites established **before** applying (the conditions the task sets for a local migration):
**target** = the DB the running app serves (§4.1); **ordering** = the final migration of the CT-03
delta and order-independent (absolute REVOKE/GRANT, idempotent by construction); **existing schema
state** = both tables present with the expected owner/RLS posture, ACL-only change; **procedure** =
committed file applied in one transaction with `ON_ERROR_STOP=1`, no ledger write (that DB has no
ledger and none was created). Non-destructive (no DDL/data/policy change) and reversible
(`GRANT SELECT, INSERT, UPDATE, DELETE … TO anon, authenticated;` — the migration documents the
rollback).

**Verified post-conditions:**

| Check | Before | After |
|---|---|---|
| `consultant_mode_change_requests` ACL | `{postgres=arwdDxtm, anon=r, authenticated=arwd, service_role=arwdDxtm}` | `{postgres=arwdDxtm, service_role=arwdDxtm}` ✅ **identical to live** |
| `consultant_relationship_requests` ACL | idem | idem ✅ |
| anon / authenticated effective access | 0 rows (RLS) | **`permission denied for table …`** (privilege **and** RLS) |
| `service_role` SELECT/INSERT/UPDATE/DELETE | true | **true / true / true / true** (consuming path intact) |
| data | `mode_change_rows=2`, `rel_request_rows=0`, `organizations=14`, `public.users=23` | **unchanged** |
| structure | 154 public tables / 355 policies / no ledger | **unchanged** |
| idempotency | — | second apply `RERUN_RC=0`, identical ACL |

**B-21 status: RESOLVED (local runtime).** The two *other* local generations were **not** touched:
`postgres` (investor-demo + auth backend) was deliberately left alone under AGENTS §55, and
`ct_local_93d5cdd` is not the runtime database. Their role remains the open `PD-4` question.

---

## 5. Recovery restore drill (Phase 4) — restoration now **tested**, not merely checksummed

**Artifact.** `/tmp/ct02_postchange_20261009/live_post_f1.dump` — 1,741,182 bytes, mtime
2026-10-09 22:53:32 +06, `sha256sum` = `d2860a77ed65c3d00952c4cb089356fcbd7802e9d0671798a8e9ab4ae3246724`
**matches `SHA256SUMS.txt`**; `TOC.txt` records **Archive created at 2026-10-09 22:51:44 +06**, i.e.
*after* the live F-1 revocation.

**Isolation (safety).** Restores were performed into **brand-new, uniquely named disposable
databases** in the local cluster (`ct_r3_postf1_restore_<epoch>`, `ct_r3_postf1_v2_<epoch>`),
pre-provisioned with the Supabase-equivalent `extensions` schema/extension environment (the same
procedure the earlier drill established). **No existing database — the live demo, `carbontally_demo_local`,
`postgres`, `ct_local_93d5cdd`, or any developer database — was written, restored over, renamed or
dropped.** Both disposable databases were dropped after verification (`dropdb_rc=0`;
`still_exists=0`).

**Result:**

| Step | Outcome |
|---|---|
| `createdb` / `dropdb` | rc=0 / rc=0 |
| `pg_restore` exit | **rc=1, errors=144, warnings=1** — *all* privileged-role/ownership classes (41× `must be able to SET ROLE "supabase_auth_admin"`, 28× storage_admin, 28× realtime_admin, 16× supabase_admin, 18× default-privilege, 5× grant-option, plus vault/`pg_stat_statements`/`log_min_messages`/pre-created `extensions` schema). **No application-object or data error.** The restoring login (`postgres`, non-superuser locally) cannot assume the Supabase platform roles; the `public` application schema restored completely. |
| schemas restored | `auth, extensions, graphql, graphql_public, public, realtime, storage, supabase_migrations, vault` |
| structure vs live | **154 public tables / 231 policies / 151 RLS-enabled / 424 indexes** — **exactly equal to live** |
| migration ledger | **104 rows, tip `20261105000000`**, F-1 row present (`f1_ledger_row=1`) — equal to live |
| **post-F-1 state inside the dump** | restored CT-03 ACL = `{postgres=arwdDxtm, service_role=arwdDxtm}` (client roles NONE), `rls=true`, `policies=0` ⇒ **the snapshot does carry the post-change ACL state** |
| data vs live | `organizations 2/2`, `public.users 2/2`, `auth.users 2/2`, `emission_factors 7049/7049`, `customer_factors 0/0`, `organization_files 12/12`, `organization_members 2/2`, `customer_documents 0/0` — **identical** (restored vs live) |
| usability | real business queries succeed on the restored snapshot (org↔member join = 2; `emission_factors` where `unit='litres'` = 152); RLS behaviour is coherent (`anon` → `permission denied`; `service_role` → sees 2 organisations) |
| unrelated local DBs after drill | `carbontally_demo_local, ct_local_93d5cdd, postgres` — all present |

**Phase 4 verdict: RESTORE VERIFIED.** The post-change recovery point is a faithful, usable,
post-F-1 snapshot of the live demo. Caveat stated plainly: the 144 restore errors are
platform-role/ownership gaps of a *non-superuser local login* against Supabase-managed schemas; a
full recovery onto Supabase's own platform roles would need those roles (or `--no-owner`), and the
`auth`/`storage`/`realtime` *data* semantics (e.g. Vault secrets, cron jobs) are not independently
validated beyond their object presence. The **application** schema, its data and its security
posture are verified equal to live.

---

## 6. I-06 — authentication review (Phase 5), re-enumerated with proof of coverage

**Method (deterministic, not grepped):** the real app was imported and every route object walked,
including FastAPI's newer `_IncludedRouter` nodes **and their include-time dependencies**; for each
operation the full `dependant` tree was flattened against auth markers (`current_user`, `require_*`,
`authorize`, `identity`, `bearer`, `jwt`, `api_key`, `admin`, `staff`, `role`, `permission`,
`checker`, `guard`, …). The discovered `(method, path)` set was cross-checked against the generated
OpenAPI contract:

```
spec_operations        = 777 (654 paths)
discovered_operations  = 798
spec_not_covered       = 0      ← every contract operation was inspected
no_auth_operations     = 17     ← reproduces INVENTORY-02's count exactly
no_auth_expected_public= 6
no_auth_unexpected     = 11
```

**Runtime confirmation** (anonymous `curl` against the local API `:8070`): the six public GETs answer
200; only the one non-persisting POST was invoked. Control set — `GET /api/v3/settings/retention`,
`/api/v3/suppliers`, `/api/admin/staff`, `/api/v3/processing/jobs` — all return **401**, so broad
authentication *is* enforced and these 17 are exceptions, not a systemic failure.

| # | Method & path | Handler / router | Intent | Auth dependency | Reads / writes | Risk & evidence | Action |
|---|---|---|---|---|---|---|---|
| 1 | `GET /` | `main.root` | framework | none | none | none | **INTENTIONAL** |
| 2 | `GET /docs` | FastAPI Swagger | framework | none | none | none | **INTENTIONAL** |
| 3 | `GET /docs/oauth2-redirect` | FastAPI | framework | none | none | none | **INTENTIONAL** |
| 4 | `GET /redoc` | FastAPI | framework | none | none | none | **INTENTIONAL** |
| 5 | `GET /openapi.json` | FastAPI | contract | none | none (already public on the deployed API) | informational | **INTENTIONAL** |
| 6 | `GET /health` | `main.health_check` | liveness | none | none | none | **INTENTIONAL** |
| 7-9 | `GET /api/glossary/`, `/categories`, `/{term_id}` | `routes.glossary` | public content | none (handler docstring: "Public endpoint") | reads `glossary` where `is_active = true` | global content, no tenant data; runtime 200 `{data:[]}` | **INTENTIONAL-PUBLIC** |
| 10 | `GET /api/reports/report_status` | `routes.reports.report_service_status` | service metadata | none | **no DB access** — static capability list | leaks only report names/version; inconsistent with the file's own "PROPER AUTH" heading | **LOW** → register `I-06a` |
| 11 | `GET /api/v2/health` | `api.router.health` | liveness | none | none | none | **INTENTIONAL** |
| 12 | `GET /api/v3/health/realtime` | `api.v3_health.realtime_health` | readiness probe | none | outbound Realtime probe | documented semantics; runtime `degraded` (known local provisioning mismatch) | **INTENTIONAL** |
| 13 | `GET /api/v3/settings/analytics` | `api.v3_settings.get_analytics_settings` | public bootstrap | none — **deliberate and documented in the handler** | reads settings, returns **only `enabled` + `ga4_measurement_id`** | runtime `{"enabled":false,"ga4_measurement_id":null}`; no retention/actors/tenant data; values are public in the browser anyway | **INTENTIONAL-PUBLIC (justified)** |
| 14 | `POST /api/waitlist/` | `routes.waitlist.add_to_waitlist` | public signup | none (by design) | **writes `waitlist`** (upsert by email) | abuse/DoS surface; no rate limiting observed; no tenant data read | **INTENTIONAL-PUBLIC** → register `I-06b` |
| 15 | `POST /api/users/password-reset` | `request_password_reset` | self-service reset | none (by design) | writes `password_reset_tokens`, sends email | **enumeration-resistant**: identical response in found / not-found / exception branches. Residual: no rate limiting (mail-flood abuse) | **INTENTIONAL-PUBLIC** → register `I-06b` |
| 16 | `POST /api/users/password-reset/confirm` | `confirm_password_reset` | token-authorized reset | **authorization = the reset token** (`secrets.token_urlsafe(32)`, 1 h expiry, single-use flag) | updates the password via the admin API; marks the token used | the token *is* the credential | **INTENTIONAL-PUBLIC (token-gated)** |
| 17 | `POST /api/test-upload` | `routes.upload.test_upload` | **diagnostic** | none | **does NOT persist** — reads the body, enforces the canonical upload limit, echoes metadata (source-verified; runtime 200 with a 1-byte file) | unauthenticated body-reading ingress ⇒ resource-abuse surface, **no data mutation** (the historical "mutation" label is inaccurate) | register `I-06c` |

**I-06 outcome.** The 17-operation count is **reproduced exactly** with full contract coverage, and
the classification is refined: 6 framework/liveness, 4 intentionally-public business routes
(glossary ×3, waitlist), 3 deliberately-public with a trimmed payload or token authorization
(analytics bootstrap, password-reset ×2), 2 liveness/readiness, 1 static service-metadata route, 1
non-persisting diagnostic. **No confirmed authentication defect was found, therefore no authentication
was added** — task Phase 5 expressly forbids doing so indiscriminately. Three residual *policy/ops*
items are registered instead: `I-06a` (authenticate or annotate `report_status`),
`I-06b` (rate-limit the three unauthenticated write/email endpoints), `I-06c` (decide the production
exposure of `POST /api/test-upload`). Corrections to the historical filing: it named 3 mutations —
`password-reset/confirm` is token-gated by design, and `test-upload` does not persist.

---

## 7. Updated foundation register (Phase 6)

Status vocabulary: **RESOLVED** · **CONFIRMED-CURRENT** · **OPEN** · **BLOCKED** · **PO DECISION
REQUIRED**. Every row was re-measured in this pass; historical wording is quoted only to show what was
being tested.

### 7.1 Previously open findings

| ID | Historical claim | Status now (evidence) | Consequence if unresolved | Safe next action / decision needed |
|---|---|---|---|---|
| **B-03** | `canonical_unit("units") is None` = "units vocabulary gap" | **SPLIT & RESOLVED** — B-03a `mi` alias gap **FIXED** (36 rows / 12 files recovered, 0 lost); B-03b count/spend drop **PO DECISION REQUIRED** (111 rows / 38 docs); B-03c dead `grosscv` token registered. Contract table §2.1 | B-03b: count/spend invoice lines stay invisible to review/mapping (silent under-coverage) | `PD-C` (options A/B/C in §2.3) |
| **B-09** | Review/approval + QC lifecycle have no live data | **CONFIRMED-CURRENT — now measured on the live demo too**: `approval_requests`, `approval_decisions`, `processing_queue`, `qc_checks`, `customer_review_log`, `ai_content_history` = **0** in *both* `carbontally_demo_local` and live | The review/approval/QC lifecycle is unexercised end-to-end anywhere ⇒ cannot be accepted as working | Authorised evidence environment (`PD-D`) + a seeded lifecycle run |
| **B-13** | `customer_factors` empty ⇒ customer-factor precedence has no live data | **CONFIRMED-CURRENT (both environments)**: `customer_factors = 0` locally **and** live (live `emission_factors = 7049`) | AGENTS §15/§16 precedence (approved customer factor wins) is unproven with real data | Seed an approved customer factor in the authorised environment (`PD-D`) |
| **B-19** | `frontend/App_.js` tracked-modified, no importer | **CONFIRMED-CURRENT**: still `M`, 41,982 bytes, no importer found | Dead legacy noise in every status/diff | PO sign-off to delete (or an explicit "kept deliberately" note); **not swept here** |
| **B-20** | Root debris must never be swept in by `git add -A` | **CONFIRMED-CURRENT**: `8` (0 B), `=` (0 B), `nohup.out`, `backend/nohup.out`, `.costrict/`, `.p18_audit_tmp/`, `Research/`, `costrict-p3-ov-01-…txt`, `.docx#` lock all present, untouched. This task staged explicit paths only (§10) | Accidental commits / confusing releases | Owner decision on deletion; never `git add -A` |
| **F-04** | Messaging-send has no ceiling for `RETAINED` relationships | **CONFIRMED-CURRENT**: `api/v3_messaging.py::_authorize_org_actor` admits (a) any member of the same org, (b) consultants with an active grant, (c) internal staff with `can_manage_staff`; grep for `RETAINED` / `require_client_operation` in that module → **no match** | A `RETAINED`/`READ_ONLY` client can still *send* messages although PA-2/PA-3 says the relationship retains no messaging-send | **PO DECISION REQUIRED** (`PD-G`). The mechanism exists (`api/client_access_guard.py::require_client_operation`, already applied to suppliers/organizations/vehicles) — only the policy is missing |
| **F-05** | Customer-factor create/update is member-level while approve/deactivate are admin-gated | **CONFIRMED-CURRENT**: `create`/`update` = `require_org_member()`; `approve`/`deactivate` = `require_org_admin()` (`api/customer_factors.py:158/270/308/350`). AGENTS §16 ratifies Owner self-approval and bars *Member approval*; it does not decide whether a Member may **propose** a factor | Under- or over-scoped authoring depending on intent | **PO DECISION REQUIRED** (`PD-H`) |
| **B-11/B-12** | AGENTS §§54-56 vs the demo tooling that exists | **CONFIRMED-CURRENT**: the referenced manifest describes ~1,185 demo identities, while the live demo project holds **2 organisations / 2 auth users** and the large population lives in the local `postgres` generation | Two coexisting definitions of "demo" ⇒ ambiguous QA/acceptance semantics | **PO DECISION REQUIRED** (`PD-B`) |
| **I-06** | 17 operations with no authentication dependency (3 mutations) | **RE-ENUMERATED (777/777 contract operations inspected, 0 uncovered) and CLASSIFIED** — 17 confirmed, **no defect found**, 3 residual policy items opened (`I-06a/b/c`); mutation count corrected | Unbounded abuse surface on 3 unauthenticated write/email endpoints | `I-06b` rate limiting (PO/ops); `I-06a`, `I-06c` decisions |
| **I-08** | Audit-coverage measurement | **OPEN / UNCHANGED** (not attempted; no evidence gathered) | Cannot claim audit completeness | Instrumentation work item |
| **B-17** (discovery test) | Environment-coupled unit test | **RESOLVED** — hermetic credential pin (§3.1); file 16/16 green | — | — |
| **B-22** (dr007 Issue 3) | `ReviewDetailPage` mapped-activity display defect | **RESOLVED as a test-scope defect** (§3.2 — the component renders the value; the assertion selected the label cell) | — | — |
| **B-21** | Live F-1 applied but local grants still present | **RESOLVED** (§4.3) — F-1 applied to the established runtime DB; ACL identical to live; idempotent; data/structure unchanged | Remaining topology question is `PD-4` only | — |

### 7.2 Verification claims that remain unproven

| Claim | Status | Why |
|---|---|---|
| Integration suite | **NOT RUN (UNVERIFIED)** | Outside this task's scope; no integration environment/authorisation established here |
| E2E / browser suite | **NOT RUN (UNVERIFIED)** | Same |
| Behavioural RLS negatives (tenant↔tenant, consultant↔client, PE↔PE, viewer↔write, member↔admin) against an authorised environment | **NOT RUN (UNVERIFIED)** — historical claims stay unproven | Needs the authorised evidence environment (`PD-D`) and role identities; unit/contract layers do not cover it |
| Live end-to-end workflow (upload → … → report) with real data | **NOT RUN (UNVERIFIED)** | B-09/B-13 show 0 lifecycle rows and 0 customer factors in the live demo ⇒ nothing to exercise. **Product acceptance is explicitly not claimed** (AGENTS §73/§74) |
| Storage/document processing at corpus scale | **PARTIAL** — the invoice-table parser was measured over 536 PDFs (§2.2); the full pipeline was not re-run end-to-end | Scope |
| Restore onto Supabase platform roles (owner-perfect) | **PARTIAL** — application schema/data/ACL verified equal to live; 144 platform-role/ownership errors remain (documented in §5) | Local login is not a member of the Supabase platform roles |

### 7.3 PO / environment decisions (register)

| ID | Decision needed | Current evidence | Who must decide |
|---|---|---|---|
| **PD-4** | Which local database and which `.env` are authoritative for local development/QA; should the other generations be retired or re-pointed? | Runtime DB is `carbontally_demo_local` (postgrest + storage); auth lives in `postgres`; a third generation `ct_local_93d5cdd` exists; **neither local generation has a migration ledger**; `backend/.env` describes a stack that is not running (`PORT=8060`, `SUPABASE_URL=:19999`) | PO / environment owner |
| **PD-C** | Count/spend invoice lines: drop (current), surface as unresolved, or add a spend/count factor path | 111 rows / 38 corpus documents dropped; `canonical_unit("GBP"/"units") is None` is otherwise correct | PO |
| **PD-D** | Authorised evidence environment + identities for lifecycle, factor-precedence and RLS-negative verification | B-09/B-13 both 0 in live; no authorised fixture environment established | PO |
| **PD-G** (new) | Messaging-send ceiling for `RETAINED`/`READ_ONLY` client profiles | F-04 confirmed current; the `require_client_operation` ceiling exists and is already applied elsewhere | PO |
| **PD-H** (new) | Who may create/update a customer factor (Member propose-then-Owner-approve, or Owner/Admin only) | F-05 confirmed current; `approve`/`deactivate` already admin-gated | PO |
| **PD-I** (new) | Rate limiting for the unauthenticated write/email endpoints (`waitlist`, `password-reset` ×2); production exposure of `POST /api/test-upload`; authenticate-or-annotate `GET /api/reports/report_status` | I-06 evidence (§6): no rate limiting observed; `test-upload` non-persisting; `report_status` static metadata | PO / ops |
| **PD-A, PD-B, PD-E, PD-F** | Unchanged from CLOSURE-02 §7.1 (MP UI/UX spec; authoritative demo identity model; consultant-parity change set — now published; retention durations) | CLOSURE-02 §7.1 | PO |

---

## 8. Tests — exact commands and results (Phase 7)

| # | Command (cwd) | Result |
|---|---|---|
| 1 | `backend$ ./.venv/bin/python -m pytest tests/unit/api/test_v3_discovery.py -k test_create_request_as_admin -q` (before fix) | **1 failed** — `assert True is False` (reproduced) |
| 2 | `backend$ RESEND_API_KEY= ./.venv/bin/python -m pytest tests/unit/api/test_v3_discovery.py -k test_create_request_as_admin -q` | **1 passed, RC=0** — causal proof of the env coupling |
| 3 | `backend$ ./.venv/bin/python -m pytest tests/unit/api/test_v3_discovery.py -q` (after fix) | **16 passed, `PYTEST_RC=0`** |
| 4 | `frontend$ CI=true npx react-scripts test --watchAll=false --testPathPattern="dr007-investor-display-fixes"` (before fix) | **1 failed / 2** — `Received string: "Mapped activity"` |
| 5 | same, after fix | **2 passed, `JEST_RC=0`** |
| 6 | `backend$ ./.venv/bin/python -m pytest tests/unit/test_units.py tests/unit/services/test_p12_impl_01_invoice_extraction.py -q` | **102 passed, `PYTEST_RC=0`** (includes the new B-03a tests) |
| 7 | `backend$ ./.venv/bin/python -m pytest tests/unit/test_units_family_compat.py tests/unit/test_units_qualifier.py tests/unit/test_d_a_natural_gas_basis.py -q` | **88 passed, `PYTEST_RC=0`** (dependants of the shared normaliser) |
| 8 | `frontend$ CI=true npx react-scripts test --watchAll=false` (full Jest) | **59/59 suites, 630/630 tests passed, `JEST_RC=0`** (was 629/1 before this task) |
| 9 | `backend$ ./.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider` (full unit suite — run because a **shared core module** changed) | **5,365 passed / 0 failed / 8 skipped, `PYTEST_RC=0`** — see §8.1 |

Additionally measured (not pytest): the read-only corpus sweeps (§2.2), the disposable-database
restore drill (§5), the live/local DB censuses (§4), the effective-privilege probes (§4.2/§4.3), and
the anonymous runtime route probes (§6). None of those write to a shared database.

### 8.1 Full backend unit suite

```
$ cd backend && ./.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider
………………………………………………………………………… [100%]
PYTEST_RC=0
```

**Result (2026-10-10 00:15:57 → 00:26:53, ≈656 s): 5,365 passed · 0 failed · 8 skipped.**

The skipped set is the same 8 as before. *Counting method, stated transparently because pytest's
terminal summary line was not written to the redirected log in this environment (verified absent from
the raw capture):* the same log contains 5,373 progress markers, exactly **8** of which are `s`
(skipped) and the rest `.` (passed), and the run exited `RC=0` after reaching `[100%]`.
Independent arithmetic cross-check against CLOSURE-02: its run was **5,360 passed + 1 failed + 8
skipped**; this task adds **4** focused tests (2 new + 2 new parametrisations) and converts the one
failure to a pass ⇒ 5,360 + 4 + 1 = **5,365** passed, with the same 8 skips. ✅

*Reason for running it:* `backend/core/units.py` is a **shared** normaliser (calculation, mapping,
disclosure, AI extraction), so the alias addition was verified against the whole unit suite rather
than only its direct tests. **No failure remains in this suite** — the report claims a green suite only
because none does.

---

## 9. Changes made (files, migrations, databases)

### 9.1 Code / test changes (7 files)

| File | Change | Why |
|---|---|---|
| `backend/core/units.py` | `+1`: `UNIT_ALIASES["mi"] = "miles"` | B-03a — missing physical-unit alias on the single central normaliser |
| `backend/engines/invoice_extraction.py` | `+11/-…`: `_UNIT_ALIASES` gains `mi`/`mile`/`miles` (+ explanatory comment) | B-03a — the parser gate that was dropping whole mileage rows |
| `backend/tests/unit/test_units.py` | `+13`: `test_normalize_distance_miles_abbreviation` | focused regression for the alias |
| `backend/tests/unit/services/test_p12_impl_01_invoice_extraction.py` | `+23/-…`: `mi`/`mile` parametrisation + `test_mileage_abbreviation_rows_are_extracted` | focused regression for row retention + canonical emission |
| `backend/tests/unit/api/test_v3_discovery.py` | `+17/-…`: hermetic credential pin (assertion untouched) | B-17 — environment-coupled test |
| `frontend/src/v3/__tests__/dr007-investor-display-fixes.test.jsx` | `+7/-…`: assertion scope corrected to the meta row | B-22 — test-scope defect |
| `docs/architecture/CT-CARBONTALLY-FOUNDATION-CLOSURE-02.md` | `+11/-…`: two garbled seams repaired (§1.4 dangling sentence; §1.7 stray fragment) and B-22/§1.4 cross-referenced to this report | The committed closure report is an input to this task; its two split-edit artefacts were corrected, no finding or status was altered |

New document: **`docs/architecture/CT-CARBONTALLY-FOUNDATION-REMEDIATION-03.md`** (this report).

### 9.2 Database actions

| Environment | Action | Detail |
|---|---|---|
| **`carbontally_demo_local`** (local runtime DB — established in §4.1) | **One migration applied**: `20261105000000_ct_consultant_model_03_request_tables_revoke_client_roles.sql`, verbatim, single transaction, `ON_ERROR_STOP=1` | ACL-only hardening; no DDL, no data, no policy change; **no ledger row written** (that DB has no `supabase_migrations` schema and none was created); idempotent (verified by re-run); rollback documented in the migration file |
| **`postgres`** (local: investor-demo + GoTrue auth) | **No writes** | Deliberately untouched (AGENTS §55) |
| **`ct_local_93d5cdd`** (third generation) | **No writes** | Not the runtime DB; role is part of `PD-4` |
| **Disposable drill DBs** (`ct_r3_postf1_restore_*`, `ct_r3_postf1_v2_*`) | **Created, restored into, verified, dropped** | Isolated restore targets only (§5) |
| **Live Supabase demo project** | **Read-only only** (SELECTs, ledger/ACL/policy/row-count queries) | No live writes in this task |

### 9.3 Files deliberately **not** staged / not touched

`.gitignore`, `frontend/App_.js` (both tracked-modified before this task, unrelated), and every
untracked root artefact (§0). No `git reset`, `git clean`, `git stash`, destructive checkout, rebase
or force-push was used at any point.

---

## 10. Git, commit and publication

* **Branch:** `p8-release-reconciled`. **HEAD before this task:**
  `fb88cde839bcb55f3f77dd465ec5f6ec3b8a0ac3` = **the GitHub tip** (0 ahead / 0 behind, verified with
  `git ls-remote github p8-release-reconciled`).
* **Staging discipline:** explicit task-owned paths only — the 7 modified files of §9.1 plus this new
  report. `.gitignore` and `frontend/App_.js` were **not** staged; `git add -A` was never used.
* **Staged-diff / secret review:** performed before committing (file list, `--stat`, and a scan of the
  staged diff for credential-shaped content). No secret, DSN, token, key or signed URL is present in
  the staged changes.
* **Commit/push:** a normal (non-forced) commit, pushed fast-forward to `github`
  (`https://github.com/shomonrobie/CarbonTally.git`) only after confirming the branch relationship and
  the exact commits being pushed. Result recorded verbatim:

```
$ git commit -F <msg>                       # normal commit, no force, no rebase
[p8-release-reconciled 926bdbc] fix(foundation-03): mileage-unit alias, hermetic/scope test fixes, local F-1 apply
 8 files changed, 664 insertions(+), 9 deletions(-)
 create mode 100644 docs/architecture/CT-CARBONTALLY-FOUNDATION-REMEDIATION-03.md

$ git push github p8-release-reconciled      # fast-forward, non-forced
To https://github.com/shomonrobie/CarbonTally.git
   fb88cde..926bdbc  p8-release-reconciled -> p8-release-reconciled
PUSH_RC=0

$ git ls-remote github p8-release-reconciled
926bdbcd096c5224ca665ea765173b1c226c4670	refs/heads/p8-release-reconciled

$ git rev-list --left-right --count github/p8-release-reconciled...HEAD
0       0        # local HEAD == GitHub tip
```

* `fb88cde` → `926bdbc` is a **fast-forward**; exactly one commit was published and every file in it
  belongs to this task (§9.1).
* The published range (`fb88cde..926bdbcd096c5224ca665ea765173b1c226c4670`) contains **only** this
  task's change set — no unrelated work, and `.gitignore`/`frontend/App_.js` are absent from it.
* A follow-up docs-only commit records this publication block (below), exactly as CLOSURE-02 did, so
  the report carries its own verified SHAs.

* **Post-push verification:** local `HEAD` and the GitHub remote tip were compared with
  `git ls-remote`; they must be equal for the push to count as verified (recorded above).
* **Never a push target for this work:** the unrelated local-path remote `origin` (`/tmp/ct_step2`).

---

## 11. Remaining risks

| # | Risk | Severity | Why it remains | Owner |
|---|---|---|---|---|
| R-1 | **Count/spend invoice lines dropped (B-03b)** — 111 rows / 38 corpus documents vanish before mapping | P2 | Product-policy decision (`PD-C`); fail-closed is the current ratified contract | PO → Implementation |
| R-2 | **No messaging-send ceiling for `RETAINED`/`READ_ONLY` clients (F-04)** | P2 | Needs `PD-G`; the guard mechanism already exists | PO → Implementation |
| R-3 | **Customer-factor authoring boundary undecided (F-05)** | P2 | Needs `PD-H`; `approve`/`deactivate` already admin-gated | PO → Implementation |
| R-4 | **No rate limiting on 3 unauthenticated write/email endpoints; `POST /api/test-upload` exposed** | P2 | `PD-I` (ops/policy); `test-upload` is non-persisting but body-reading | PO / ops |
| R-5 | **Lifecycle, factor-precedence and RLS-negative verification unproven (B-09/B-13, integration/E2E)** | **P1 for acceptance** | Live demo has 0 lifecycle rows / 0 customer factors; no authorised evidence environment (`PD-D`) | PO (environment) + QA |
| R-6 | **Local topology ambiguity (PD-4)** — three local generations, two `.env` targets, no ledger in either modern generation | P2 | Needs a PO/environment decision; this task aligned only the runtime DB's ACLs | PO / environment owner |
| R-7 | **Live demo is data-thin** (2 organisations / 2 auth users / 0 customer factors / 0 lifecycle rows) while AGENTS §§54-56 describe a ~1,185-identity demo | P2 | Which identity model is authoritative is `PD-B`/`PD-D` | PO |
| R-8 | **Dead vocabulary / duplicated unit logic (B-03c)** — `grosscv` unreachable; parser vocabulary duplicates `core/units.py` | P4 (hygiene) | Benign for factor matching (central normalisation verified); a §23 consistency debt | Implementation backlog |
| R-9 | **Dead `frontend/App_.js` + root debris (B-19/B-20)** | P4 (hygiene) | Needs an owner decision; never swept automatically | PO sign-off → Implementation |
| R-10 | **I-08 audit-coverage measurement** | P3 | Not attempted; no evidence gathered either way | Implementation |

---

## 12. Acceptance-readiness recommendation

### 12.1 Acceptance matrix (states kept distinct — AGENTS §73)

| Dimension | State | Evidence |
|---|---|---|
| Implementation of the itemised findings | **IMPLEMENTED** — B-03a, B-17, B-22, B-21 fixed; B-03b/F-04/F-05/I-06a-c deliberately **not** implemented (policy-dependent) | §2, §3, §4, §6 |
| Focused tests for every change | **TESTED** — 16/16, 2/2, 102, 88, plus 2 causal-proof runs | §8 |
| Full backend unit suite | **MEASURED — 5,365 passed / 0 failed / 8 skipped (RC=0)** | §8.1 |
| Full frontend Jest suite | **MEASURED — fully green: 59/59 suites, 630/630 tests** | §8 |
| Database state verified | **VERIFIED** (local runtime + live, read-only; before/after ACL + effective-privilege probes) | §4 |
| Migration applied | **ONE — authorised, non-destructive, idempotent, ledger-free (that DB has no ledger)** | §4.3, §9.2 |
| Recovery restore verified | **VERIFIED** — isolated disposable restore; structure/data/ledger/ACL equal to live; drill DBs dropped | §5 |
| Security review (authentication surface) | **COMPLETE for the 17-operation scope** — 777/777 contract operations inspected; no defect found; 3 residual policy items registered | §6 |
| Behavioural RLS-negative verification | **NOT DONE (UNVERIFIED)** — needs the authorised environment | §7.2 |
| Integration / E2E suites | **NOT RUN (UNVERIFIED)** | §7.2 |
| PO decisions complete | **NO** — `PD-4`, `PD-C`, `PD-D`, `PD-G`, `PD-H`, `PD-I` (+ PD-A/B/E/F) remain open | §7.3 |
| Product acceptance (business outcome end-to-end) | **NOT CLAIMED** | AGENTS §73/§74; §7.2 |
| Release status | **NOT RELEASED** — the branch is published for review, not released | §10 |

### 12.2 Recommendation

**The foundation is materially closer to acceptance but is NOT ready for foundation acceptance.**

Closed with evidence in this task: the B-03 canonical-unit contract is now explicit and one real
defect inside it (`mi` → `miles`, verified to recover 36 printed mileage rows across 12 documents with
zero loss) is fixed; the live/local F-1 drift is resolved on the established runtime database via a
non-destructive, idempotent, verified apply; both previously failing tests are fixed at their true
root cause (environment coupling; assertion scope) with the assertions left intact; the post-change
recovery point is now **restore-verified** into an isolated database and matches live on structure,
data, migration ledger and post-F-1 ACLs; the 17 unauthenticated operations are re-enumerated with
**proof of full contract coverage** and classified, with no confirmed authentication defect; and the
finding/decision register is current.

What still blocks acceptance:

1. **No behavioural RLS-negative verification and no integration/E2E run** (R-5) — the security and
   workflow claims that matter most remain unproven.
2. **No end-to-end business outcome exercised on real data** — the live demo holds 0 lifecycle rows
   and 0 customer factors, so review/approval/QC (B-09) and customer-factor precedence (B-13) cannot be
   demonstrated (R-5/R-7).
3. **Six PO/environment decisions remain open** (`PD-4`, `PD-C`, `PD-D`, `PD-G`, `PD-H`, `PD-I`);
   three of them (`PD-C`, `PD-G`, `PD-H`) decide *who may act* and what activity data survives.
4. **Local topology is still ambiguous** (R-6): three local database generations, two conflicting
   `.env` targets, and no migration ledger in either modern generation — "the local environment" is not
   yet reproducible from source.

Recommended order of next steps: answer **`PD-D`** (authorised evidence environment) → run behavioural
RLS negatives + the integration suite + one full lifecycle with a seeded customer factor → decide
**`PD-C`/`PD-G`/`PD-H`** (the three ceilings) → resolve **`PD-4`** (authoritative local DB + ledger) →
independent QA re-verification of B-03a, B-21 and the two test fixes. Only then can an
ACCEPTED / RELEASED verdict be considered.

### 12.3 Attestation

* No credential, token, key, DSN or signed URL was written into this report, a commit, or a log.
* No unrelated worktree change was absorbed; no destructive Git operation was used.
* The live demo is described as a demo environment, never as production.
* Migrations/restores were performed only against explicitly established targets; disposable restore
  databases were removed.
* Everything not measured in this pass is stated as **UNVERIFIED** rather than assumed.

| Untracked at task start | 32 entries (root debris + older reports, none owned by this task) | `git status --porcelain` |
| CLOSURE-02 report vs reality | committed at `fb88cde`; its §1.1/§1.4/§1.6/§1.7 findings reproduce; **two documentation seams were garbled by its final split edit and are corrected here** (§10) | `git show --stat fb88cde`; current file |
| API runtime | `uvicorn main:app --host 127.0.0.1 --port 8070`, cwd `<repo>/backend`, venv `backend/.venv` | `/proc/<pid>/cmdline` |
| API env (non-secret) | `SUPABASE_URL=http://127.0.0.1:54430` | `/proc/<pid>/environ` (filtered) |
| Local cluster | `supabase_db_carbon_ledger` (`postgres:17.6.1.147`), **90 databases** | `docker ps`, `pg_database` |

The prior report's HEAD, DB state and test outcomes were **re-measured, not assumed**. Nothing was
found ahead of GitHub; the "232 ahead" figure is an artefact of the local-path remote (B-07 remains
closed — the CLOSURE-02 §1.4 seam is corrected here).
