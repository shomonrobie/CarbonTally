# CT-VERIFY-06 — Independent Final Verification of `CT-FINAL-01-PO-SCOPE-IMPLEMENTED`

**Date:** 2026-09-28
**Verifier:** independent verification agent (CT-VERIFY-06) — separate from the CT-FINAL-01 implementer
**Repository (target):** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**HEAD verified:** `dc3d78dc8021bd65978754cf131c38045ff8013d` (unchanged by this run)
**Mode:** verification only — **no fix was implemented**, no refactor, no production/demo mutation, no migration edited, no migration applied to any persistent environment.

> **Mandate honoured.** No product code, schema, RLS policy, migration, test or frozen report was
> edited. No commit, push, rebase, reset, stash or deploy was performed. Every destructive action
> was confined to the disposable `ct_verify06_*` stack. All verifier artefacts live under
> `/tmp/ctv06/`. The investor/demo environment, production and every pre-existing `ct_*` clone were
> never contacted.

---

## 1. Verification objective

Determine whether the implemented **CT-FINAL-01 PO scope** is *independently verifiable as working in
a disposable real runtime*, and produce a permanent PASS/FAIL evidence record. Acceptance is
**not** decided here — the PO / authorised release process decides.

---

## 2. Repository / commit actually tested

| Item | Value |
|---|---|
| Path | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD | `dc3d78dc8021bd65978754cf131c38045ff8013d` (matches the handoff) |
| Tested surface | the **uncommitted working tree** at that HEAD (the CT-FINAL-01 state), served by a live `uvicorn` |
| Migrations at HEAD | **92** |
| Migrations in the working tree | **93** (+ `20261024000000_ct_final_01_documents_bucket_size_limit.sql`) |

The handoff claim that the latest implementation is *uncommitted* was **re-verified, not assumed**:
`git rev-parse HEAD` is the reported SHA and `git status` shows the change-set as working-tree state
only.

---

## 3. Working-tree state (re-measured, as the handoff required)

| Measure | Session start | Session end | Delta |
|---|---|---|---|
| Tracked changes (` M` + ` D`) | 34 modified + 1 deleted = **35** | 34 modified + 1 deleted = **35** | **0** |
| Untracked files | **880** | **881** | +1 (see below) |
| `git status --porcelain` lines | 111 | 112 | +1 |

The single untracked-file delta is `docs/ChatGPT/carbontally_handoff_2026_09_28.md`
(`CT-HANDOFF-20260928-02`, mtime `2026-09-28 21:00`). It is **not** produced by any CT-VERIFY-06
tooling (`grep -rl` over `/tmp/ctv06` and `/tmp/ctv05` → no references); it is an externally
authored handoff document. **CT-VERIFY-06 modified zero tracked files.** The only file this task adds
to the repository is this report.

---

## 4. Disposable environment (reproducible fingerprints)

Built with the **in-repo** canonical rebuild driver (`e2e/environment/scripts/canonical_schema_rebuild.sh`),
never against a persistent environment.

| Element | Value |
|---|---|
| Postgres | `ct_verify06_pg` — image `public.ecr.aws/supabase/postgres:17.6.1.159`, `127.0.0.1:55540`, DB `postgres`, server 17.6 |
| Storage platform | `ct_verify06_storage` — image `public.ecr.aws/supabase/storage-api:v1.69.0` (host net, `:5000`) |
| PostgREST | `ct_verify06_rest` — image `public.ecr.aws/supabase/postgrest:v16.1` (host net, `:3199`) |
| API gateway | `/tmp/ctv06/gateway2.py` on `:54541`, mounts `/rest/v1`, `/auth/v1`, `/storage/v1` |
| Backend | `uvicorn main:app` on `127.0.0.1:8081` (working tree, `ENVIRONMENT=local_verify`) |
| Schema build | PHASE A–D + the new migration #93; 92 canonical migrations applied by `apply_migrations.sh` (`ALL_APPLIED applied=92`), then #93 applied separately |
| Extra disposable DB | `ctv06_bare` (no `storage` schema) — portability branch test only |
| F-046-1 discipline | the integration harness (`TRUNCATE … RESTART CASCADE`) was **never** run; only `CREATE`/read-only SQL, HTTP and the guarded migration runner |

### 4.1 Environment limitations (recorded, not hidden)

1. **Real GoTrue (Auth) service could not run** against the pinned Postgres image's pre-provisioned
   `auth` schema: GoTrue v2.195.0 fails with `column users.aud does not exist (SQLSTATE 42703)` →
   HTTP 500 on every auth operation. This is an **image version mismatch** (GoTrue vs
   `supabase/postgres:17.6.1.159` auth schema), **not a CarbonTally defect**. Auth enforcement was
   therefore exercised through the product's own documented JWT-decode path
   ([`backend/auth.py`](../backend/auth.py:200)).

2. **Storage JWT secret mismatch.** The Storage service signs against its own `AUTH_JWT_SECRET`
   (a different random value from the app/PostgREST secret), so user-JWT *direct-to-storage* uploads
   were rejected with `signature verification failed`. This blocked the *direct-to-storage* probe,
   not the application-layer limit tests.

---

## 5. Exact commands used (representative)

```bash
# 1. repo state
git -C /home/shomonrobie/ct_93d5cdd rev-parse HEAD ; git status --porcelain ; git ls-files --others --exclude-standard | wc -l

# 2. build the disposable canonical schema (+ real Storage platform layer)
bash e2e/environment/scripts/canonical_schema_rebuild.sh --prefix ct_verify06 --port 55540 \
     --profile ct-implement-02 --evidence /tmp/ctv06/evidence

# 3. exercise the NEW migration (item 8) and its branches
bash e2e/environment/scripts/apply_migrations.sh \
     --from 20261024000000_ct_final_01_documents_bucket_size_limit.sql \
     --to   20261024000000_ct_final_01_documents_bucket_size_limit.sql \
     --expect-count 1 --require-storage --host 127.0.0.1 --port 55540 --db postgres

# 4. seed two tenants + identities, mint platform-signed tokens
psql -h 127.0.0.1 -p 55540 -U supabase_admin -d postgres -f /tmp/ctv06/seed6.sql
/usr/bin/python3 /tmp/ctv06/mktok6.py

# 5. run the backend against the disposable stack
bash /tmp/ctv06/run_backend.sh                      # uvicorn 127.0.0.1:8081

# 6. verification matrices
/usr/bin/python3 /tmp/ctv06/probe1.py               # items 1,3,4,5,6,10
bash /tmp/ctv06/upload_tests.sh                     # item 7
# item 9 (direct PostgREST RLS) — inline probe recorded in §13

# 7. pre-existing failures (item 12)
/usr/bin/python3 -m pytest backend/tests/unit/api/test_review_sla_surfaces.py -q -p no:cacheprovider
/usr/bin/python3 -m pytest backend/tests/unit/api/test_f05_r1_org_scope_authorization.py \
  backend/tests/unit/api/test_f05_r2_r4_runtime_defects.py \
  backend/tests/unit/api/test_f04_factor_write_path_blocking.py \
  backend/tests/unit/api/test_ct_final_01_notification_sender.py \
  backend/tests/unit/api/test_ct_final_01_upload_limits.py \
  backend/tests/unit/api/test_pd4_legacy_audit_retirement.py -q -p no:cacheprovider
```

---

## 6. Runtime / browser evidence

* **Runtime:** live HTTP against `uvicorn` + real PostgREST + real Storage + a real 93-file schema. All
  matrices below are HTTP results, not unit mocks.
* **Browser:** **no Playwright / Cypress / Puppeteer is present** in the environment
  (`frontend/node_modules/.bin` → none); `/usr/bin/google-chrome` exists but there is no automation
  harness, and building the SPA would write into the frozen tree. **No browser/E2E claim is made**
  (see item 11).

---

## 7. Tenant-isolation evidence (item 1 — highest priority)

Two genuinely separate tenants and nine real identities exist in the disposable DB; tokens are
HS256 JWTs signed with the platform secret and carry the identity `sub`.

Identities: `ownerA` (Org A owner), `ownerB` (Org B owner), `outsider` (no membership),
`viewerA`/`memberA` (Org A viewer/member), `inactiveA` (**inactive** Org A membership), `admin`
(CarbonTally internal staff admin), `staffNonAdmin` (internal reviewer), `entityAdmin`
(Processing-Entity staff, role name `admin`), `ownerC` (owner of an **inactive** org C).

| # | Case | Expected | Observed |
|---|---|---|---|
| 1 | `ownerA → OrgA POST …/exports/exports/emissions` | 200 | **200** |
| 2 | `ownerB → OrgB` same | 200 | **200** |
| 3 | **`ownerB → OrgA` same** | 403, no data | **403**, zero victim-org needles |
| 4 | `outsider → OrgA` same | 403 | **403** |
| 5 | `ownerA → OrgA GET …/exports` | 200 | **200** |
| 6 | `ownerB → OrgA GET …/exports` | 403 | **403** |
| 7 | `ownerA → OrgA …/organization-activity` | 200 | **200** |
| 8 | `ownerB → OrgA …/organization-activity` | 403 | **403** |
| 9 | `ownerA → OrgA data/{org}/emissions-data` | 200 | **200** |
| 10 | `ownerB → OrgA data/{org}/emissions-data` | 403 | **403** |
| 11 | `ownerB → OrgB data/{org}/emissions-data` | 200 | **200** |
| 12 | `ownerB → OrgA …/dashboard-summary` | 403 | **403** |
| 13 | `ownerA → OrgA …/dashboard-summary` | 200 | **200** |
| 14 | `ownerB → OrgA data/{org}/defra-factors` | 403 | **403** |
| 15 | `ownerB → OrgA GET /api/{org}/emissions` | 403 | **403** |
| 16 | `viewerA → OrgA read` | 200 | **200** |
| 17 | `viewerA → OrgB read` | 403 | **403** |
| 18 | `memberA → OrgB read` | 403 | **403** |
| 19 | **`inactiveA → OrgA` (inactive membership)** | 403 | **403** |
| 20 | `entityAdmin → OrgA` (D20 scope-first) | 403 | **403** |
| 21 | **forged organisation id** (`ownerA → random uuid`) | 403 | **403** |
| 22 | no credentials | 401 | **401** |
| 23 | invalid bearer token | 401 | **401** |
| 24 | `ownerC → own INACTIVE org C` | (assess) | **200** — recorded, see D-7 |

**Item 1 verdict: PASS.** The release-blocking F-05-R1 cross-tenant disclosure is closed at runtime:
every cross-tenant attempt returns a clean **403** (never 500, never data), including
path-parameter substitution, forged identifiers and inactive memberships. This is the strongest
evidence in this report and it is runtime, not mock-level.

**Permanent regression coverage:** the in-repo matrix
[`test_f05_r1_org_scope_authorization.py`](../backend/tests/unit/api/test_f05_r1_org_scope_authorization.py)
(35 tests, ALLOW + DENY) passes (see §14). The independent runtime probe that produced the table above
is preserved verbatim in **Appendix A** of this report so the cross-tenant check survives as a
permanent artefact.

---

## 8. F-04 evidence (item 2 — unresolved factor blocking)

Target: `POST /api/admin/extraction/approve` (`require_role(["admin","data_approver"])`) — a real
write path that resolves the factor before writing.

| Case | Observed |
|---|---|
| **Unresolved factor** (`fuel_utility_type = "Unobtainium-X"`, 2025) | **HTTP 409** `FACTOR_UNRESOLVED_BLOCKED: no governed emission factor matches 'Unobtainium-X' for 2025. No emissions record was written…` |
| `emissions_logs` row count for Org A before/after the blocked call | **3 → 3** (nothing written) |
| Resolved factor (`"Electricity (kWh, UK grid)"`, 2025) | **HTTP 500** `PGRST204 … Could not find the 'approved_at' column of 'manual_review_queue'` — **but** the emissions row *was* written |
| Row written by the resolved call | `raw_quantity=100.0`, `calculated_kg_co2e=20.707`, `emission_factor_id=eeee0006-…f2` — i.e. `100 × 0.20707`, **correct provenance, no fabricated value** |
| Fabricated `2.68` default present in the write path? | **No** — the only `2.68` in live backend code is an unrelated sample row in the PD-3 admin module and a PDF-engine literal; the removed write-path default survives only as explanatory comments |
| `ownerA → approve` | **403** `Required roles: admin, data_approver. User has role: org_owner` |
| `staffNonAdmin → approve` | **403** `… User has role: reviewer` |
| `entityAdmin → approve` (role name `admin`, entity scope) | **403** `Processing Entity staff cannot hold role-name authority` (D20) |
| anonymous | **401** |

**Item 2 verdict: PASS (blocking) / FAIL (resolved path completion).**
The ratified F-04 guarantee — *an unresolved factor is a blocking validation state and nothing is
written, with no fabricated multiplier* — is independently verified. The companion requirement
*"valid resolved factor path still works"* is **not** met: the endpoint writes the emissions row and
then fails (`manual_review_queue` has no `approved_at` column), returning **500 after a successful
write** (non-atomic, wrong status). See **D-3**.

---

## 9. PD-3 evidence (item 3 — admin factor management)

| Case | Observed |
|---|---|
| `admin → GET /api/admin/defra/factors` | **200** |
| `staffNonAdmin / ownerA / entityAdmin →` same | **403 / 403 / 403** |
| anonymous | **401** |
| `admin → POST /api/admin/defra/factors` (create) | **200** with new `id` |
| `admin → GET …/{id}` | **200** |
| `admin → PUT …/{id}` (update) | **200**; follow-up GET returns the **updated** values (persistence verified) |
| `admin → DELETE …/{id}` | **200** |
| invalid body (`reporting_year:"not-a-year"`) | **422** with a field-level message |
| `ownerA → GET …/{id}` | **403** |

**Item 3 verdict: PASS**, with one defect: `GET …/factors/{id}` for a **deleted** id returns
**500** instead of 404 (**D-6**, LOW). Authorisation boundaries are correct in both directions.

---

## 10. PD-4 evidence (item 4 — canonical audit path)

| Check | Observed |
|---|---|
| Legacy console `backend/routes/admin/audit_logs.py` | **absent** (retired; deletion staged in the working tree only) |
| `admin → GET /api/admin/audit/activity` | **200** |
| `ownerA / staffNonAdmin →` same | **403 / 403** |
| `admin → GET /api/v2/admin/audit` | **200**, returns real `audit_trail` entries |
| `admin → GET /api/v3/ops/reporting/audit` (with `can_manage_staff`) | **200** — and the payload contains the audit entry created by an earlier PD-3 factor mutation (`entity_type: emission_factor`), i.e. the canonical ledger is genuinely written and read |
| `ownerA → GET /api/v3/ops/reporting/audit` | **403** `Staff access required (active staff profile)` |
| Migrations dropped/altered to retire records? | **None** — the immutability migrations remain in the chain |

**Item 4 verdict: PASS.** The canonical audit path works at runtime and is correctly authorised;
no legacy implementation was recreated and no audit data was deleted.

---

## 11. PD-5 evidence (item 5 — manual factor lookup)

| Case | Observed |
|---|---|
| `ownerA → GET /api/reports/defra-factors/2025` | **200**, `{"status":"success","factors":[…]}` including full provenance (`id`, `activity_type`, `co2e_multiplier`, `unit`, `scope`, `country`, `factor_source`, `factor_set`) |
| **No-result year** (`ownerA → …/1999`) | **200** `{"status":"success","factors":[],"count":0}` — neutral, no error, no dead end |
| anonymous | **401** |
| `admin` (internal staff, no org membership) → same | **403** `Organization member access required` |

**Item 5 verdict: PASS**, with a recorded asymmetry (**D-5**, informational): the route is
**organisation-member**-gated, so an internal CarbonTally admin cannot use the manual lookup; factors
are platform-global, so there is no cross-tenant leakage on this surface.

---

## 12. Notification-sender evidence (item 6)

The PUT request model field is `email_sender` (confirmed from the OpenAPI `NotificationSenderUpdate`
schema and [`api/v3_settings.py`](../backend/api/v3_settings.py:207)); the handler rejects invalid
values with **422**.

| Case | Observed |
|---|---|
| `admin → GET /api/v3/settings/notification-sender` | **200** — `email_sender = "CarbonTally <notifications@carbontally.co.uk>"`, `is_default: true`, `configured: false` |
| `admin → PUT {"email_sender":"CarbonTally Alerts <alerts@carbontally.co.uk>"}` | **200** — `configured: true`, `is_default: false` |
| `admin → GET` after the PUT (persistence) | **200** — the configured sender is returned |
| `PUT` customer/consultant domain (`evil@customer.example.co.uk`) | **422** `email_sender domain is not a CarbonTally platform domain…` — never stored |
| `PUT` header injection (`…\r\nBcc: …`) | **422** `must be a single address with no separators or control characters` |
| `PUT` multi-address (`a@…, b@…`) | **422** (same) |
| `PUT {"email_sender": null}` (clear) | **200** — the platform default is restored |
| `ownerA / staffNonAdmin → GET or PUT` | **403 / 403** |
| anonymous | **401** |

**Item 6 verdict: PASS.** Admin-only in both directions; the value persists and reads back; invalid,
injecting and multi-address values are refused with 422 and never used; the documented default
`notifications@carbontally.co.uk` is the effective sender when unconfigured. **Configuration was
verified; actual email delivery was NOT verified** (no mail sink in the disposable stack) — no
delivery claim is made.

---

## 13. Upload / storage evidence (items 7 and 8)

### 13.1 Item 7 — ratified limits (10 MB/file · 50 files/batch · 500 MB/batch)

| Ingress | Case | Observed |
|---|---|---|
| `POST /api/organizations/files/api/organizations/{org}/files/upload` | 10 MB + 1 byte | **413** `UPLOAD_FILE_TOO_LARGE: 'p3.bin' is 10.0MB; the platform limit is 10MB per file.` |
| same | 20 MB | **413** (same code) |
| same | 10 MB exactly | **not** rejected by the limit (the handler proceeds to storage) |
| `POST /api/v3/uploads` (canonical choke point) | 10 MB + 1 byte | **413** `UPLOAD_FILE_TOO_LARGE` |
| `POST /api/organizations/files/bulk-upload` | **51** files | **400** `UPLOAD_TOO_MANY_FILES: 51 files submitted; the platform limit is 50 files per batch.` |
| same | 50 files | count limit satisfied (**200**) |
| **`POST /api/upload` (legacy ingress)** | 10 MB + 1 byte | **HTTP 500** `cannot access local variable 'status' where it is not associated with a value` — **not 413** |
| direct-to-storage (`/storage/v1/object/documents/…`) | any | **NOT VERIFIED** — Storage rejected the user JWT (`signature verification failed`; env mismatch, §4.1) |

Findings from the code (read, not guessed):

* [`routes/upload.py:608`](../backend/routes/upload.py:608) — the legacy `/upload` endpoint checks a
  **hard-coded `50 * 1024 * 1024`**, not the ratified 10 MB ceiling; the ratified
  `effective_file_limit_bytes()` is only used by `validate_file_upload()`
  ([`routes/upload.py:94`](../backend/routes/upload.py:94)) which the `/upload` handler does not call.
  **A 10–50 MB file passes the legacy route's limit check.**
* [`routes/upload.py:689`](../backend/routes/upload.py:689) assigns a local variable `status`, which
  shadows the imported `fastapi.status` module for the whole function — so the 413 raise at
  [`routes/upload.py:610`](../backend/routes/upload.py:610), the storage-failure handler at
  [`routes/upload.py:648`](../backend/routes/upload.py:648) and every other `status.…` use *before*
  line 689 raise `UnboundLocalError` → **500**.
* The batch-total ceiling is arithmetically unreachable as a distinct trigger: `50 × 10 MB` is exactly
  `500 MB`, so the file-count guard fires first. `UPLOAD_BATCH_TOO_LARGE` is therefore
  defence-in-depth only (recorded, informational).

**Item 7 verdict: PASS** for per-file (10 MB → 413) and per-batch count (50 → 400) enforcement on the
modern ingresses, **FAIL** for the stated requirement *"enforcement cannot be bypassed simply by using
another upload route"* — `POST /api/upload` neither enforces the ratified ceiling nor returns a 4xx
(**D-2**). Storage-layer policy read-back is **PASS** (§13.3) but the direct-to-storage probe is
**NOT VERIFIED**.

### 13.2 Item 8 — the storage migration, exercised

`supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql` applied through the
in-repo canonical runner on a real Storage-provisioned target:

| Step | Observed |
|---|---|
| Pre-state | `documents` bucket: `public=f`, `file_size_limit` **unset** |
| Apply #93 | **rc 0**; `NOTICE: CT-FINAL-01: documents bucket aligned — file_size_limit = 10485760, public = f` |
| Post-state | `file_size_limit = 10485760`, `public = f` |
| Idempotent re-run | rc 0, unchanged (10 MiB) |
| **Tighten-only** semantics (`set 5 MiB`, re-run) | stays **5242880** — a smaller configured limit is never raised |
| Restore | back to `10485760` |
| **Portability** branch (bare DB `ctv06_bare`, no `storage.buckets`) | rc 0 with `NOTICE: storage layer not provisioned … not applicable` — a deliberate no-op, not a failure |
| Application tables touched | none |

**Item 8 verdict: PASS.** The migration applies cleanly, is idempotent, tightens-only, and is a safe
no-op where the Storage layer is absent — exactly as documented. It was **not** applied to any
persistent environment.

### 13.3 Storage-layer policy read-back

`storage.buckets` for `documents` = `file_size_limit 10485760`, `public = FALSE`, and the four D32
`storage.objects` policies are present and their behavioural semantics proof passed during the build
(`D32_SEMANTICS_RESULT pass=11 fail=0`).

---

## 14. RLS / PostgREST evidence (item 9)

Direct PostgREST over the disposable gateway with **real user JWTs** (role `authenticated`) — no
application layer involved:

| Request | Result |
|---|---|
| `ownerA → /rest/v1/emissions_logs` | **200**, **4 rows — Org A only** |
| `ownerB → /rest/v1/emissions_logs` | **200**, **1 row — Org B only** |
| `outsider → /rest/v1/emissions_logs` | **200**, **0 rows** |
| **`ownerB → ?organization_id=eq.<OrgA>`** | **200**, **0 rows** (RLS beats an explicit cross-tenant filter) |
| `ownerA → ?organization_id=eq.<OrgA>` | **200**, 4 rows |
| `ownerA → /rest/v1/organizations` | **200**, **1 row — Org A only** |
| `ownerA → ?id=eq.<OrgB>` | **200**, 0 rows |
| `ownerA → /rest/v1/organization_members` | **200**, Org A memberships only |
| `ownerA → /rest/v1/emission_factors` | **403 `42501`** — no `authenticated` grant; factors are not exposed through PostgREST |
| `service_role → /rest/v1/emissions_logs` | **200**, all 6 rows |

**Item 9 verdict: PASS.** Tenant isolation is enforced at the database/API layer independently of the
application; there is no accidental PostgREST exposure and no cross-tenant read.

---

## 15. Previously-affected 500-surface evidence (item 10)

| Surface | CT-VERIFY-05 state | CT-VERIFY-06 observed | Verdict |
|---|---|---|---|
| `POST …/exports/exports/emissions` | 500 (PGRST200) | **200** with correct rows | **PASS** |
| `GET …/organization-activity` | 500 (42703) | **200** | **PASS** |
| `GET …/data/{org}/emissions-data` | 500 (response-model) | **200** | **PASS** |
| `GET …/data/{org}/emissions/export-csv` | 500 | **200** | **PASS** |
| `GET /api/{OrgA}/emissions` | 500 | **200** | **PASS** |
| **`GET /api/{OrgB}/emissions`** (row with NULL `asset_id` — the F-05-R4 case) | 500 | **500** `Failed to get emissions: 'NoneType' object has no attribute 'get'` (traceback at `emissions.py:197`) | **FAIL — D-1** |
| **`POST /api/reports/generate-enhanced-report`** + `/api/generate-enhanced-report` (SECR) | 500 `FPDF.set_fill_color()` | **500** `Report generation failed: 'bytearray' object has no attribute 'encode'` (`report_generator.py:887`) | **FAIL — D-4** |
| `POST /api/documents/{org}/{file}/review` | (n/a) | **500** PGRST200 — no FK between `organization_files` and `customer_documents` (its own embed is unresolvable) | **FAIL — D-5b** |

**Item 10 verdict: FAIL.** Three of the previously-broken surfaces are genuinely fixed, but **PDF
report generation still returns 500** (the CT-FINAL-01 `set_fill_color` fix removed one FPDF
incompatibility and exposed the next one) and the **F-05-R4 NULL-relation 500 still occurs** on
`GET /api/{org_id}/emissions`. Cross-tenant review on the documents route correctly returns 403
before the handler runs.

---

## 16. Three pre-existing SLA failures (item 12)

`backend/tests/unit/api/test_review_sla_surfaces.py` reproduces **exactly three** failures, matching
the documented pre-existing baseline node ids:

| Failing test | Assertion |
|---|---|
| `test_canonical_ops_sla_surface_registered` | `'/api/v3/ops/sla/settings' in {'/api/v2/health'}` |
| `test_canonical_ops_review_assign_registered` | `'/api/v3/ops/review/{review_id}/assign' in {'/api/v2/health'}` |
| `test_admin_legacy_compat_surface_retained` | `'/api/v3/admin/sla/settings' in {'/api/v2/health'}` |

**Verdict: PASS (matches baseline).** All three inspect the **module-level** router
(`api.router.router`), which at import time exposes only `/api/v2/health`; the v3 families are attached
during application composition — the registered routes **do** exist in the composed app
(`/api/v3/ops/sla/settings` and `/api/v3/admin/sla/settings` are both present in the served OpenAPI
document). The tests inspect the wrong object. They are a **test defect**, pre-existing, **not caused
by CT-FINAL-01** and not fixed here (as instructed). No regression was introduced.

The CT-FINAL-01 regression suites pass cleanly:
`test_f05_r1_org_scope_authorization.py`, `test_f05_r2_r4_runtime_defects.py`,
`test_f04_factor_write_path_blocking.py`, `test_ct_final_01_notification_sender.py`,
`test_ct_final_01_upload_limits.py`, `test_pd4_legacy_audit_retirement.py`
→ **111 tests, exit 0, 0 failures**.

---

## 17. Production / demo non-mutation evidence (item 13)

| Requirement | Evidence |
|---|---|
| No production data mutation | Only `ct_verify06_pg` (disposable) was written; no hosted/production endpoint was contacted |
| No production migration | Migration #93 applied **only** to `ct_verify06_pg`; nothing else received it |
| No production deployment | `git log`/`git status` unchanged at HEAD `dc3d78dc…`; no push, no deploy |
| No investor/demo reset | The investor/demo project was never opened; pre-existing `ct_*` clones left running and untouched |
| No production secret modification | No secret file read/written; no credentials printed; the only credential-adjacent action was generating a *disposable* JWT secret into `/tmp` |
| No repository mutation | Tracked changes identical at start and end (34 M + 1 D); the sole new untracked file is an externally authored handoff doc (§3) |

**Item 13 verdict: PASS.**

---

## 18. Every PASS / FAIL / NOT VERIFIED / BLOCKED item

| # | Item | Verdict |
|---|---|---|
| 1 | Tenant isolation (ALLOW / DENY, forged ids, substitution, inactive, D20) | **PASS** |
| 2a | F-04 unresolved factor blocked, nothing written, no `2.68` | **PASS** |
| 2b | F-04 valid resolved factor path completes | **FAIL** (writes then 500s) |
| 3 | PD-3 admin factor management + boundaries | **PASS** (one LOW defect: deleted-id 500) |
| 4 | PD-4 canonical audit path | **PASS** |
| 5 | PD-5 manual factor lookup | **PASS** (recorded admin asymmetry) |
| 6 | Notification sender configuration (config, not delivery) | **PASS** |
| 6b | Notification **delivery** | **NOT VERIFIED** (no mail sink) |
| 7a | 10 MB/file enforced (files.py, /api/v3/uploads) | **PASS** |
| 7b | 50 files/batch enforced | **PASS** |
| 7c | 500 MB aggregate as a distinct trigger | **NOT VERIFIED** (arithmetically unreachable) |
| 7d | Cannot be bypassed via another upload route | **FAIL** (`POST /api/upload`, 50 MB + 500) |
| 7e | Direct-to-storage ceiling enforcement | **NOT VERIFIED / BLOCKED** (Storage rejected the user JWT — env mismatch) |
| 8 | Storage migration applies / idempotent / tighten-only / portable | **PASS** |
| 9 | RLS + PostgREST isolation | **PASS** |
| 10 | Previously-affected 500 surfaces | **FAIL** (PDF gen; NULL-relation emissions; documents-review embed) |
| 11 | PD-3 browser journey | **NOT VERIFIED / BLOCKED** (no automation harness) |
| 12 | Three pre-existing SLA failures | **PASS (baseline reproduced)** |
| 13 | No production/demo mutation | **PASS** |
| 14 | Canonical rebuild VERIFY (release tooling) | **FAIL** (migration-set accounting expects 92, tree has 93) — see D-0 |
| — | Auth service (GoTrue) runtime | **BLOCKED** (GoTrue/Postgres image mismatch — not a product defect) |

---

## 19. Defects discovered (documented, not fixed)

### D-0 — Canonical rebuild VERIFY fails on migration-set accounting — MEDIUM (release tooling)
`canonical_schema_rebuild.sh --profile ct-implement-02` applied all 92 canonical migrations and the
Storage platform layer cleanly, but its VERIFY step then reported **89 pass / 5 fail**, all
migration-set accounting:

```
FAIL migration_count: found 93 .sql files (expected 92)
FAIL migration_endpoints: last=20261024000000_ct_final_01_documents_bucket_size_limit.sql
FAIL migration_set_fingerprint_matches_recorded (actual a18a3d4f… vs expected 36d5d85b…)
FAIL baseline_migration_set_unchanged (actual aaab5eb4… vs expected 40b168b3…)
FAIL migration_set_only_authorised_revision: files differing from HEAD: [20261024000000_ct_final_01_…]
```

The schema-inventory checks passed; the failure is the pinned migration-set fingerprint/count, which
CT-FINAL-01's 93rd migration invalidates. **Consequence:** the "clean-checkout canonical rebuild
verifies green" property asserted by CT-RELEASE-04 no longer holds for this working tree. No
migration was edited and nothing was "normalised away" to hide it.

### D-1 — F-05-R4 NULL-relation 500 on `GET /api/{org_id}/emissions` — MEDIUM
Own-tenant read of a row whose `asset_id` is NULL still returns **500**
`'NoneType' object has no attribute 'get'` (`backend/routes/emissions.py:197`). The CT-FINAL-01
NULL-hardening covered the activity feed, the emissions-data transform, the CSV export and the shared
summary helper, but **not** this route. Reproduce: seed an `emissions_logs` row with `asset_id = NULL`
in the caller's own org, then `GET /api/{org}/emissions`.

### D-2 — Ratified per-file ceiling not enforced on the legacy `/api/upload`; route 500s — MEDIUM/HIGH
[`backend/routes/upload.py:608`](../backend/routes/upload.py:608) uses a hard-coded **50 MB** check, so
a 10–50 MB file passes the initial limit check — the ratified 10 MB ceiling is **not** enforced on this
ingress (contradicting the CT-FINAL-01 report §11.6). The route additionally returns **500** for every
error path because a local variable `status` (line 689) shadows `fastapi.status`
(`cannot access local variable 'status' …`). Reproduce: `POST /api/upload` with an 11 MB file.

### D-3 — Admin extraction approval writes then 500s (non-atomic, wrong status) — MEDIUM
`POST /api/admin/extraction/approve` with a resolvable factor writes the `emissions_logs` row and then
fails with `PGRST204 … Could not find the 'approved_at' column of 'manual_review_queue'`. Verified:
`manual_review_queue` columns contain no `approved_at`. The write is therefore **partial** and the
caller receives **500** after data has been committed. Reproduce with the F-04 probe body in §8.

### D-4 — PDF report generation still returns 500 — MEDIUM/HIGH
`POST /api/reports/generate-enhanced-report` and `/api/generate-enhanced-report` (report type `SECR`)
return **500** `'bytearray' object has no attribute 'encode'` at
[`backend/report_generator.py:887`](../backend/report_generator.py:887)
(`pdf_output = pdf.output(dest='S').encode('latin-1')`). The CT-FINAL-01 `set_fill_color` arity fix
removed the *first* FPDF incompatibility and exposed a *second* one. **The surface the release claims
to have repaired is still broken.** Pre-existing defect now reachable, not a regression introduced by
CT-FINAL-01 — but the "no `set_fill_color` traceback" goal is met while the feature remains 500.

### D-5 — Customer document review route is unreachable (missing FK) — MEDIUM
`POST /api/documents/{org_id}/{file_id}/review` embeds `customer_documents` from `organization_files`,
but **no foreign key exists** between those tables, so PostgREST answers `PGRST200 … Could not find a
relationship …` and the handler converts it to **500**. Consequence: this F-04 write path cannot be
exercised at runtime at all. (Its cross-tenant guard is nevertheless correct: `ownerB → OrgA` → 403.)

### D-6 — `GET /api/admin/defra/factors/{deleted_id}` returns 500 instead of 404 — LOW
After a successful `DELETE`, a subsequent `GET` of the same id returns **500**, not 404.

### D-7 — Access to an *inactive* organisation is allowed for its own member — informational / PO decision
`ownerC → GET /api/organizations/data/{orgC}/emissions-data` returns **200** where `organizations.is_active = false`.
This is not a cross-tenant issue (it is the caller's own org) and the org-scope guard does not consult
`is_active`. Recorded so the intended suspended-organisation behaviour can be ratified:
**PO DECISION REQUIRED.**

### D-8 — Environment-only blockers (not product defects)
* GoTrue v2.195 cannot operate against `supabase/postgres:17.6.1.159` (`auth.users.aud` missing).
* The Storage service signs against a different `AUTH_JWT_SECRET`, blocking user-JWT direct-to-storage probes.

---

## 20. Pre-existing failures, separately identified

| Failure class | Status | Attribution |
|---|---|---|
| `test_review_sla_surfaces.py` (3 tests) | reproduced identically | pre-existing **test** defect (inspects the module-level router) — proven unrelated by the CT-FINAL-01 baseline A/B |
| `report_generator.py:887` FPDF `.encode()` on `bytearray` | reproduced | pre-existing product defect, **masked** before CT-FINAL-01 by the earlier `set_fill_color` failure |
| `emissions.py:197` NULL relation | reproduced | pre-existing product defect (F-05-R4 did not cover this route) |
| `manual_review_queue.approved_at` missing (D-3) | reproduced | pre-existing schema/code mismatch |
| `organization_files ↔ customer_documents` FK absent (D-5) | reproduced | pre-existing schema/embed mismatch |
| `routes/upload.py` 50 MB + shadowed `status` (D-2) | reproduced | pre-existing, **and** inconsistent with the ratified 10 MB ceiling |
| Migration-pinned unit tests (71 vs 92/93) | not re-run in full here | pre-existing drift, recorded by CT-FINAL-01 |

None of these was fixed, as instructed.

---

## 21. Final CT-VERIFY-06 conclusion

### `CT-VERIFY-06 FAIL — REMEDIATION REQUIRED`

**Why it cannot be a PASS.** The release's headline remediation (F-05-R1 cross-tenant disclosure) is
**independently verified as fixed** — the tenant-isolation matrix and the RLS/PostgREST probes are
clean in all three directions and under forged/substituted/inactive identifiers. PD-3, PD-4, PD-5,
the notification sender and the storage migration also verify. **However**, the release cannot be
accepted because:

1. **PDF report generation still returns 500** (D-4) — a surface CT-FINAL-01 claims to have repaired.
2. **The F-05-R4 NULL-relation 500 persists** on `GET /api/{org_id}/emissions` (D-1) — the
   remediation did not cover that route.
3. **The ratified upload ceiling is bypassable** through `POST /api/upload` (50 MB check), which also
   returns 500 on every error path (D-2) — directly contradicting the requirement that enforcement
   "cannot be bypassed simply by using another upload route".
4. **The F-04 resolved-factor write path is not atomic** and returns 500 after committing an
   emissions row (D-3).
5. The canonical rebuild's VERIFY step no longer passes with the 93rd migration present (D-0).

**What is explicitly NOT claimed:** no acceptance; no production readiness; no browser/E2E
verification; no email-delivery verification; no direct-to-storage enforcement verification; the
500 MB aggregate trigger was not exercised as a distinct case.

**Recommended remediation order (separate authorised tasks):** D-4 and D-1 (the two lingering 500s) →
D-2 (upload bypass + 500) → D-3 (atomic write / correct status) → D-0 (reconcile the canonical
verifier/profile with the 93-migration tree) → D-5/D-6/D-7 (embed FK, 404, PO decision on inactive
orgs). None of these was implemented here.

---

## 22. Boundary statement

This task ended at **CT-VERIFY-06 independently verified and documented**. It does **not** authorise
CT-FINAL-02, CT-FINAL-03, production deployment, production migration or production acceptance. No
fix was applied; every defect above is recorded with reproduction evidence and left for an
authorised, separately scoped remediation task.

---

## Appendix A — the cross-tenant runtime probe (preserved)

Preserved so the independent cross-tenant check remains reproducible after this task. Run with a
disposable stack whose two tenants are `ORGA`/`ORGB` and identities `ownerA`/`ownerB`/`outsider`.

```python
#!/usr/bin/env python3
"""CT-VERIFY-06 cross-tenant runtime probe (disposable stack only)."""
import json, urllib.request, urllib.error
BASE = "http://127.0.0.1:8081"
T = json.load(open("/tmp/ctv06/tokens.json"))          # {"name": {"token": "..."}}
ORGA = "aaaa0006-0000-4000-8000-00000000000a"
ORGB = "aaaa0006-0000-4000-8000-00000000000b"

def call(method, path, who=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if who: req.add_header("Authorization", "Bearer " + T[who]["token"])
    if data is not None: req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return r.status, r.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()

CASES = [
    # (label, method, path, who, expect)
    ("OrgA user -> OrgA exports (ALLOW)", "POST", f"/api/organizations/{ORGA}/exports/exports/emissions", "ownerA", 200),
    ("OrgB user -> OrgB exports (ALLOW)", "POST", f"/api/organizations/{ORGB}/exports/exports/emissions", "ownerB", 200),
    ("OrgB user -> OrgA exports (DENY)",  "POST", f"/api/organizations/{ORGA}/exports/exports/emissions", "ownerB", 403),
    ("outsider -> OrgA exports (DENY)",   "POST", f"/api/organizations/{ORGA}/exports/exports/emissions", "outsider", 403),
    ("OrgB user -> OrgA activity (DENY)", "GET",  f"/api/organizations/{ORGA}/organization-activity", "ownerB", 403),
    ("OrgB user -> OrgA emissions-data (DENY)", "GET", f"/api/organizations/data/{ORGA}/emissions-data", "ownerB", 403),
    ("OrgB user -> OrgB emissions-data (ALLOW)", "GET", f"/api/organizations/data/{ORGB}/emissions-data", "ownerB", 200),
    ("OrgB user -> OrgA defra-factors (DENY)", "GET", f"/api/organizations/data/{ORGA}/defra-factors", "ownerB", 403),
]
fails = 0
for label, method, path, who, expect in CASES:
    status, text = call(method, path, who, {"format": "json"} if method == "POST" else None)
    leaks = [n for n in (ORGA, ORGB) if n in text and who != ("ownerA" if n == ORGA else "ownerB")]
    ok = status == expect and not leaks
    fails += 0 if ok else 1
    print("%-46s -> %s (expect %s) leaks=%s %s" % (label, status, expect, leaks or "none", "PASS" if ok else "FAIL"))
print("cross_tenant_probe_failures=%d" % fails)
```

## Appendix B — evidence index (all disposable, under `/tmp/ctv06/`)

| Artefact | Content |
|---|---|
| `rebuild.out`, `evidence/verify.txt` | canonical rebuild + VERIFY result (D-0) |
| `evidence/ledger_phase_b.tsv`, `ledger_phase_d.tsv`, `ledger_phase_e.tsv` | independent per-migration apply ledgers (92 + 1) |
| `evidence/logs_phase_e/001_*.log` | migration #93 NOTICE output |
| `seed6.sql`, `tokens.json`, `users.json` | fixtures + minted identity tokens |
| `probe1.py` / console matrices | items 1, 3, 4, 5, 6, 10 |
| `upload_tests.sh`, `f10m.bin`, `f10m1.bin`, `f20m.bin` | item 7 boundary files + results |
| `uvicorn.log` | 502 auth fallback lines and the D-1/D-4 tracebacks |
| `gateway2.py`, `start_gw.sh`, `stack.sh`, `auth.sh`, `run_backend.sh` | disposable-stack apparatus |

---

*End of CT-VERIFY-06. Target `dc3d78dc8021bd65978754cf131c38045ff8013d` on `p8-release-reconciled`;
no product code, schema, RLS, migration, test or frozen report was modified; nothing was committed,
pushed or deployed; every destructive action was confined to the disposable `ct_verify06_*` stack.*
