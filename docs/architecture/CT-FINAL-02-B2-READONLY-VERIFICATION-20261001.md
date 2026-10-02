# CT-FINAL-02 — B2′ Read-Only Managed Backup / PITR Verification

**Date:** 2026-10-01 · **Operator:** Cline (implementation / rehearsal operator)
**Acceptance authority:** CoStrict / OHD — **this report accepts nothing and changes no decision.**
**Scope:** a single bounded task — use the newly supplied Supabase management credential
(`SUPABASE_ACCESS_TOKEN`, gitignored `backend/.env`) to obtain the **B2′ managed backup/PITR
evidence** over the Management API, **read-only**, without mutating production.

**Headline:** the credential **authenticates** and the B2′ evidence that was previously unobtainable
has now been obtained — and **it is negative**. The live production project has **zero managed
backups**, **PITR is disabled**, **no PITR add-on is purchased**, and the owning organization
(`CarbonLedger`) is on the **`free`** plan. B2′ therefore moves from *"evidence unavailable
(credential absent)"* to *"evidence obtained — the capability is not in place"*. **B2′ is NOT
closed** and FINAL-02 remains OPEN.

| Item | Result |
| --- | --- |
| Credential authenticated (Management API) | **YES** — `GET /v1/projects` → 200 |
| B2′ evidence obtainable read-only | **YES** — 10 documented GET endpoints, all reached |
| Managed backups present on live project | **NO** — `backups: []` (count 0) |
| PITR enabled on live project | **NO** — `pitr_enabled: false`, no add-on, entitlement `set: []` |
| **B2′ status** | **REMAINS OPEN** — evidence obtained; capability absent (§4) |
| Production mutated | **NO** — GET only; no POST/PATCH/PUT/DELETE issued |
| FINAL-02 acceptance | **NOT granted, not claimed** |

---

## 0. B2′ as it stood immediately before this task

`CT-FINAL-02-20261001-LIVE-EVIDENCE-CLOSURE-PASS-REPORT.md` Part H.3 retired **B2** ("live/shared
Supabase credentials unavailable") because the live factor count (7,049) and live schema were
already evidenced read-only, leaving only the managed backup/PITR third, restated as:

> **B2′ — managed backup/PITR evidence unavailable (needs a management API token, not a DB DSN).**
> Closure vehicle (matrix L564): **Management-API backup/PITR evidence**.

That document's summary row records the *reason* as "credentials unavailable". This task supplies the
token and replaces the assumption with measurement.

---

## 1. Credential handling

| Property | Value |
| --- | --- |
| Source | `/home/shomonrobie/ct_93d5cdd/backend/.env` (gitignored — `git status` shows no `.env`) |
| Variable | `SUPABASE_ACCESS_TOKEN` |
| Prefix test | `startswith("sbp_")` → **True** |
| Length | **47** |
| Fingerprint | `sha256[:12]` = **`6c2b00cea2bf`** |
| Token value | **never printed, never logged, never written to any output file** |

**Project ref pinned from the environment, not from task text:** `SUPABASE_LIVE_URL` in the same
`.env` resolves to ref **`pvwiojoyaqywtydzcpbg`** (20 chars). The task text rendered the same ref with
one fewer `y`; the **environment/live-URL value is treated as authoritative** and is the only ref
called. (The service-role key is a data-plane credential and is **not** accepted by the Management
API — 401 — which is why B2′ required a `sbp_` PAT.)

---

## 2. Method — read-only by construction

Verifier: `/home/shomonrobie/ct_local_env/final02_rehearsal/b2/b2_verify.py` (outside the repository).
Every request is `urllib.request.Request(..., method="GET")`; the script contains **no** POST, PATCH,
PUT or DELETE call and records `http_methods: ["GET"]` in its summary. The PATCH sibling of the backup
schedule endpoint was deliberately **not** called. Only endpoints documented in the Supabase
Management API OpenAPI spec were used.

Raw responses: `.../b2/raw/*.json`; summary:
`.../b2/b2_verification_20261001T110110Z.json`.

| # | Endpoint (GET) | Status |
| --- | --- | --- |
| 01 | `/v1/projects` | 200 |
| 02 | `/v1/projects/{ref}` | 200 |
| 03 | `/v1/projects/{ref}/database/backups` | 200 |
| 04 | `/v1/projects/{ref}/database/backups/restore-point` | 400 |
| 05 | `/v1/projects/{ref}/database/backups/schedule` | 402 |
| 06 | `/v1/projects/{ref}/billing/addons` | 200 |
| 07 | `/v1/projects/{ref}/config/database/postgres` | 200 |
| 08 | `/v1/organizations` | 200 |
| 09 | `/v1/organizations/{slug}` | 200 |
| 10 | `/v1/organizations/{slug}/entitlements` | 200 |

---

## 3. Evidence

### 3.1 Authentication and project identity

- `GET /v1/projects` → **200**; **3** projects visible to this PAT; target `pvwiojoyaqywtydzcpbg`
  **present**.
- `GET /v1/projects/pvwiojoyaqywtydzcpbg` → **200**:
  `name` **CarbonTally**, `status` **ACTIVE_HEALTHY**, `region` **eu-west-2**,
  `database.version` **17.6.1.147**, `created_at` **2026-07-17T01:56:53Z**,
  `organization_id` **pfurlzwxdtvyljnahlnx**.

### 3.2 The B2′ core read — managed backups

`GET /v1/projects/pvwiojoyaqywtydzcpbg/database/backups` → **200**:

```json
{ "backups": [], "physical_backup_data": {}, "pitr_enabled": false,
  "region": "eu-west-2", "walg_enabled": true }
```

- **`backups` is empty — there are zero managed backups**, so there is no restore point and no
  retention window. `physical_backup_data` is likewise `{}`.
- **`pitr_enabled` is `false`.**
- `walg_enabled: true` records only that the platform's physical-backup (WAL-G) subsystem flag is on
  for this project. It is **not** evidence of a retained backup: the backup list is empty and the
  org's retention entitlement is 0 days (§3.5). No restorable artefact exists.

Corroborating reads:

- `GET /database/backups/restore-point` → **400** `{"message": "This endpoint is unavailable at the
  moment"}`.
- `GET /database/backups/schedule` → **402** `entitlement_required`, feature `backup.schedule`:
  *"This feature requires the Enterprise organization plan."*
- `GET /projects/{ref}/config/database/postgres` → **200**; **no** WAL/archive/backup/recovery/PITR
  keys are returned by the API.

### 3.3 PITR commercial state

`GET /v1/projects/{ref}/billing/addons` → **200**:

- **`selected_addons`: `[]`** — **no add-on of any kind is purchased**, PITR included.
- `available_addons` lists `pitr` as a **purchasable** product (`pitr_7` $100/mo, `pitr_14` $200/mo,
  `pitr_28` $400/mo) alongside `custom_domain`, `compute_instance`, `ipv4`, `log_drain`,
  `etl_pipeline`, `auth_mfa_phone`, `auth_mfa_web_authn`. Availability in this list means *offered for
  purchase*, not *entitled*.

### 3.4 Organization

- `GET /v1/organizations` → **200**; two organizations visible: `gcslnwazrprrcnhajjfn` (**TenderAI**)
  and `pfurlzwxdtvyljnahlnx` (**CarbonLedger**).
- `GET /v1/organizations/pfurlzwxdtvyljnahlnx` → **200**: **`plan`: `free`**, `name`: CarbonLedger.

### 3.5 Authoritative entitlements — the decisive read

`GET /v1/organizations/pfurlzwxdtvyljnahlnx/entitlements` → **200** (64 entitlements returned). The
four backup/PITR grants:

| Entitlement key | `enabled` | Config |
| --- | --- | --- |
| `backup.retention_days` | **false** | `value: 0`, `unlimited: false`, `unit: days` |
| `backup.restore_to_new_project` | **false** | — |
| `backup.schedule` | **false** | — |
| `pitr.available_variants` | **false** | `set: []` |

Every backup/PITR entitlement in the organization is **disabled**, backup retention is **0 days**, and
the PITR variant set is **empty**. This is the authoritative, server-side statement of what the
platform will and will not do for this project, and it is consistent with the `free` plan and with the
empty `backups` array.

---

## 4. Verdict on B2′

**B2′ REMAINS OPEN.** The two possible readings must not be conflated:

- *Evidence availability* — **resolved.** A management-API token now exists, authenticates, and
  yields the backup/PITR configuration. The previous "credentials unavailable" reason is withdrawn
  permanently and must not be re-used.
- *Managed backup/PITR verified* — **not satisfied.** The criterion is a positive assurance that
  managed backup and/or PITR protection exists for the live project. The measurement shows the
  opposite: **0 backups, retention 0 days, `pitr_enabled: false`, no PITR add-on, all backup/PITR
  entitlements disabled, org plan `free`.**

Reporting "B2′ CLOSED — MANAGED BACKUP/PITR VERIFIED" on this evidence would be a **false assurance**,
so it is not made.

**Exact missing evidence that keeps B2′ open** — any one of:

1. a **non-empty** `GET /v1/projects/{ref}/database/backups` response containing a completed backup
   (`inserted_at` within the retention window); or
2. **`pitr_enabled: true`** on the project *and* a selected `pitr` add-on in `/billing/addons` *and*
   `pitr.available_variants.config.set` non-empty in the org entitlements; or
3. a **`backup.retention_days` entitlement with `value > 0`** (and, if used, `backup.schedule`
   entitled).

All three are currently false. None can be produced by a read-only call: they require a **commercial
and/or configuration change on the CarbonLedger organization** (moving off `free`, and/or purchasing
the PITR add-on), performed by the account owner — not by this task.

---

## 5. What was deliberately NOT done

- **No mutation of any kind**: no POST/PATCH/PUT/DELETE was issued against the Management API; the
  backup *schedule* PATCH (which exists as a sibling of the read used) was intentionally not called.
- **No production deploy, no production DB write, no production email, no real customer account.**
- **No payment plan change, no add-on purchase, no organization setting change.**
- **No application code, migration, configuration or verifier-under-review was modified.**
- **No commit and no push.** No FINAL-03 work was started. **FINAL-02 acceptance is not claimed.**

---

## 6. Repository preservation

| Check | Value |
| --- | --- |
| `git rev-parse HEAD` | `cabdca8380415e73a25cf23eb393d0b15c0af391` (unchanged) |
| Branch | `p8-release-reconciled` (unchanged) |
| Working-tree entries before this task | **132** |
| Added by this task | **this file only** |
| Working-tree entries after this task | **133** |
| `qa_harness/` | untouched |
| `backend/.env` | not modified; remains gitignored |
| Verifier artefacts | written **outside** the repository (`~/ct_local_env/final02_rehearsal/b2/`) |

---

## 7. Recommended next action (owner decision, not a technical step)

The B2′ blocker is no longer an evidence problem — it is a **product/operational exposure**: the
production database currently has **no managed backup and no PITR**, so there is no platform-level
restore path for the live project.

1. **Decide the recovery posture for production.** Either (a) move the `CarbonLedger` organization off
   the `free` plan so daily managed backups with non-zero retention exist, and/or (b) purchase the
   `pitr` add-on (`pitr_7`/`14`/`28`) so PITR is enabled. This is a commercial action the owner must
   take.
2. **Re-run the same read-only verifier** afterwards; B2′ closes **only** when §4's missing evidence
   appears (non-empty `backups` and/or `pitr_enabled: true` with a selected add-on).
3. Until then, **do not** transcribe B2′ as closed, and **do not** treat FINAL-02 as ready for an
   acceptance statement on the strength of this task.

**End of report. B2′ = REMAINS OPEN (evidence obtained; capability absent). No acceptance claimed.**
