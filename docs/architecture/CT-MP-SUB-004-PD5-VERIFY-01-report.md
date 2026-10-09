# CT-MP-SUB-004 — PD-5 Fixture Independent Verification Report

**Document ID:** `CT-MP-SUB-004-PD5-VERIFY-01`
**Task ID:** `CT-MP-SUB-004-PD5-VERIFY-01`
**Type:** Independent verification (read-only apart from authorised Demo Lab fixture operations and the permitted allocation/release actions).
**Status:** COMPLETE
**Date:** 2026-10-04
**Verifier:** CoStrict (independent verifier — not the fixture implementer)

---

## 1. Task identity

| Field | Value |
| --- | --- |
| Task ID | `CT-MP-SUB-004-PD5-VERIFY-01` |
| Subject | Independently verify the Demo Lab QA fixture implemented under **PD-5** for **CT-MP-SUB-004**, and rule on the previously open gaps **F-5 / NV-1 / NV-2 / NV-3 / NV-4 / NV-8** |
| Repository | `ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD (verified) | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (`FINAL-03: freeze production cutover release`) — **unchanged** |
| Verifier role | Independent verification. No implementation, refactor, fix or acceptance performed. |

---

## 2. Verification authority

Read and applied, in order of precedence:

1. `docs/architecture/CT-MP-SUB-004-PO-decision-record.md` — authoritative for **PD-1 … PD-6**.
   In particular:
   * **PD-5 = A** — authorises a deterministic, resettable Demo Lab QA fixture **only**;
   * PD-5 §7.1 — the fixture may **not** change application code, product behaviour,
     schema/migration/RLS, the investor demo database, production, or deploy;
   * **PD-6 = B** — architectural ratification with a **per-migration review gate**;
     PD-6 does **not** authorise production deployment or migration application.
2. `CT-UX-MP-SUB-003` (`docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md`) —
   the now-authoritative UI/UX specification (per PD-1). §10 acceptance criteria.
3. `docs/architecture/CT-MP-SUB-004-PD5-FIXTURE-01-report.md` — the implementer's report
   (treated as **claims to verify**, not facts).
4. `docs/architecture/CT-MP-SUB-004-independent-verification-report.md` — the **historical**
   independent verification report. **Not modified by this task.**

Integrity of the governing artefacts at verification time (unchanged from their recorded baselines):

| Artefact | sha256 |
| --- | --- |
| `CT-MP-SUB-004-independent-verification-report.md` | `128c47cfc94fafc9931a0fb38dd964e359e9becd53d3ae0a35109587870748f9` (**matches the recorded baseline**) |
| `CarbonTally_Manual_Processing_Subscription_Options.md` | `d55644f00ad04014e286597770c57dfff7582bad3fb9523f8729e53e5b29ea5d` |
| `CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | `a27ad96428808cc44fe632da41dec77c171ed6909cdbbf7bf8e74d676079f3da` |

The historical verdict (**B — VERIFIED WITH FINDINGS / NOT READY FOR PO ACCEPTANCE**) is left
historically intact. This report states **what changed after PD-5** and what is established **now**.

---

## 3. Scope

**In scope:** independent inspection and execution of the PD-5 fixture; determinism/reset/round-trip;
real-browser verification of the positive coverage states at `http://localhost:3000`; API/back-end
cross-checks; authorization/security boundaries; baseline Demo Lab regression; production-safety.

**Out of scope (unchanged from the historical report):** NV-5 (responsive viewports), NV-6 (automated
accessibility audit), NV-7 (pixel-level D2 comparison), NV-9 (performance), NV-10 (notification
side-effects); and any acceptance/deployment/migration decision.

---

## 4. Environment used

| Component | Value |
| --- | --- |
| Lab gateway | `127.0.0.1:54430` (container `carbontally_demo_lab_gateway`, `Up`) |
| Backend | `127.0.0.1:8070` (`uvicorn`, PID 312590) |
| Frontend | `http://localhost:3000` — a CRA dev server **started by this verification** (PID 871992, `Compiled successfully`) |
| Pre-existing frontend | `localhost:3100` (PID 315566, `frontend/.env.local` sets `PORT=3100`) — **left untouched** (not used) |
| Database | container `supabase_db_carbon_ledger`, database `carbontally_demo_local` |
| Browser | headless `google-chrome` via Playwright (Chromium) |

Command used to raise the frontend on :3000 (do **not** use :3100):

```bash
cd frontend && PORT=3000 BROWSER=none nohup node node_modules/react-scripts/scripts/start.js \
  > /tmp/ct_frontend_3000.log 2>&1 &
```

Credentials were read at runtime from the existing Demo Lab state outside the repository
(`~/ct_local_env/demo_lab/credentials.local.json`, mode 0600). **No password, JWT, anon/service key
or signed URL is reproduced anywhere in this report.**

---

## 5. Files inspected

| File | Note |
| --- | --- |
| `docs/architecture/CT-MP-SUB-004-PO-decision-record.md` | PD-1…PD-6, §7/§7.1 (PD-5), §8 (PD-6) |
| `docs/architecture/CT-MP-SUB-004-PD5-FIXTURE-01-report.md` | implementer claims |
| `docs/architecture/CT-MP-SUB-004-independent-verification-report.md` | historical F-5, §19 NV list, §20 PD list, §21 verdict |
| `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | authoritative UI/UX (§10 AC) |
| `tools/demo_lab/README.md` | §8 documents the fixture |
| `tools/demo_lab/verify.py` | base Demo Lab verification |
| `tools/demo_lab/lab.py`, `tools/demo_lab/provision.py` | local config, deterministic UUIDs, GoTrue user helpers |
| `tools/demo_lab/fixture_mp_coverage.py` | fixture (953 lines) |
| `tools/demo_lab/fixture_mp_coverage_browser.py` | browser verification (330 lines) |
| `backend/api/v3_manual_processing_coverage.py` | route + auth model (customer/consultant) |
| `backend/api/manual_processing_admin.py` | admin coverage/client routes |

Fixture file hashes at verification time:

```
71ab28218f6aea9e33aeea915c4f18753b20d4739165b59908214cddf29c1cba  tools/demo_lab/fixture_mp_coverage.py
2a7ee71853e8918908ad443c32e97c485679693d58b9e638c3e0a3dd7288f9f0  tools/demo_lab/fixture_mp_coverage_browser.py
```

---

## 6. Fixture implementation inspected

Independently read (not just re-run):

* **States** are declared once (`PLANS`/`ORGS`/`ACTORS`/`FIRMS`/`SUBSCRIPTIONS`,
  [`fixture_mp_coverage.py:113`](tools/demo_lab/fixture_mp_coverage.py:113)).
* **Deterministic ids** — every fixture row is addressed by `fid(key)` →
  `lab.deterministic_uuid("mpfix:…")` ([`fixture_mp_coverage.py:86`](tools/demo_lab/fixture_mp_coverage.py:86)), written with
  `INSERT … ON CONFLICT (id) DO UPDATE`.
* **Labelling** — `metadata.fixture = "ct-mp-sub-004-pd5"`, names `MP-FX`, plan codes `MP-FX-`,
  e-mails `mp.*` ([`fixture_mp_coverage.py:68`](tools/demo_lab/fixture_mp_coverage.py:68)).
* **Reset scoping** — `RESET_TARGETS` deletes only by fixture ids / `MP-FX-*` plan codes / `mp.*`
  users ([`fixture_mp_coverage.py:478`](tools/demo_lab/fixture_mp_coverage.py:478)); GoTrue users removed via the lab admin API
  ([`fixture_mp_coverage.py:509`](tools/demo_lab/fixture_mp_coverage.py:509)).
* **Convergence** — `normalise_allocations()` prunes undeclared allocations owned by the fixture firms
  ([`fixture_mp_coverage.py:395`](tools/demo_lab/fixture_mp_coverage.py:395)).
* **Fail-closed precondition (PD-6 gate)** — `precondition()` is read-only (`to_regclass` + gateway
  `/auth/v1/health`) and, if a table is missing, stops and names the migration; it never applies one
  ([`fixture_mp_coverage.py:572`](tools/demo_lab/fixture_mp_coverage.py:572), [`fixture_mp_coverage.py:834`](tools/demo_lab/fixture_mp_coverage.py:834)).
* **Auth users** are GoTrue-assigned; the fixture mirrors the returned ids
  ([`fixture_mp_coverage.py:279`](tools/demo_lab/fixture_mp_coverage.py:279)).

Security posture of the read/write model (inspected): customer read uses `require_org_member()`
([`v3_manual_processing_coverage.py:123`](backend/api/v3_manual_processing_coverage.py:123)); consultant writes call
`ensure_consultant_permission(context, "manage_clients")` on **both** allocate and release
([`v3_manual_processing_coverage.py:268`](backend/api/v3_manual_processing_coverage.py:268), [`v3_manual_processing_coverage.py:362`](backend/api/v3_manual_processing_coverage.py:362)).

---

## 7. Fixture verification results

Independent checks were written by the verifier (own scripts, own assertions, ids resolved directly
from the database — **not** the fixture's expectations):
`/tmp/ct_pd5_verify/{api_probe.py,browser_probe.py,roundtrip.py,convergence.py}`.

| Channel | Result |
| --- | --- |
| Fixture `--verify` reproduction (implementer's script, re-executed) | **11/11** |
| **Independent API probe** (19 checks) | **19/19** |
| Fixture browser script reproduction | **10/10** |
| **Independent browser probe** (8 checks) | **8/8** |
| Baseline `verify.py` (before/after) | contexts **14/14**, routing **14/14**, probes **30/30**, isolation **18/18** |

### 7.1 Scope (A)
Fixture-owned rows are unambiguously identifiable: organisations carry
`metadata->>'fixture' = 'ct-mp-sub-004-pd5'`; plans are `MP-FX-*`; lab users are `mp.*`. Observed
baseline: **6 fixture organisations / 3 `MP-FX` plans / 4 fixture subscriptions / 5 `mp.*` auth
users**, alongside **5 non-fixture organisations / 20 non-fixture plans / 14 non-fixture auth users**.

### 7.2 Determinism (B)
`apply` → `apply` produced **identical counts and identical fixture organisation ids**; auth ids were
**stable across plain re-apply** (verified separately: `mp.consultant.selected` id unchanged across
three consecutive applies).

### 7.3 Reset (C)
See §8. `--reset` zeroed **every** fixture table (including the 5 GoTrue users and their mirrors) and
left **all** non-fixture counts unchanged.

### 7.4 Round-trip (D)
See §8.

### 7.5 Convergence
An out-of-band allocation created through the **real API** (allocated `1 → 2`) was pruned by the next
`apply` back to the declared baseline (`2 → 1`) — independently reproduced:

```json
{ "before": 1, "allocate_http": 200, "after_out_of_band_allocate": 2,
  "db_after_out_of_band_allocate": 2, "after_fixture_apply": 1,
  "db_after_fixture_apply": 1 }
```

### 7.6 Existing Demo Lab verification (E)
`python3 tools/demo_lab/verify.py` run **after** the fixture operations:
`actor contexts 14/14`, `authorization / isolation probes 30/30`, `isolation rules enforced 18/18`
(evidence `verify_20261004T180310Z.json`). No baseline authorization/isolation regression.

---

## 8. Reset/determinism evidence

Sequence driven by the verifier with its **own** SQL counts (not the fixture's `counts()`):
`apply → apply → reset → apply → verify`.

| Measure | apply #1 | apply #2 | **after reset** | apply #3 |
| --- | --- | --- | --- | --- |
| fixture organisations | 6 | 6 | **0** | 6 |
| non-fixture organisations | 5 | 5 | **5** | 5 |
| `MP-FX` plans | 3 | 3 | **0** | 3 |
| non-fixture plans | 20 | 20 | **20** | 20 |
| fixture subscriptions | 4 | 4 | **0** | 4 |
| fixture profiles | 2 | 2 | **0** | 2 |
| fixture firm members | 2 | 2 | **0** | 2 |
| fixture client grants | 3 | 3 | **0** | 3 |
| fixture allocations | 1 | 1 | **0** | 1 |
| fixture grants / processors | 1 / 1 | 1 / 1 | **0 / 0** | 1 / 1 |
| fixture `mp.*` auth users | 5 | 5 | **0** | 5 |
| non-fixture auth users | 14 | 14 | **14** | 14 |
| non-fixture profiles / firm-members / clients | 1 / 2 / 2 | — | **1 / 2 / 2** | 1 / 2 / 2 |

`reset` removed (exit 0, `failures: []`): allocations 1, processors 1, grants 1, subscriptions 4,
client grants 3, firm members 2, organisation members 3, profiles 2, organisations 6, plans 3,
GoTrue users 5, mirror rows 5.

Outcomes:

* `determinism apply#1 == apply#2` → **true**
* fixture org ids identical across apply#1/#2/#3 → **true**
* `reset` zeroes every fixture table → **true**
* non-fixture counts unchanged across the whole cycle → **true**
* re-apply restores the exact baseline → **true**
* fixture `--verify` passes **after** the round-trip (fresh GoTrue ids) → **rc 0**

Evidence (outside the repository): `~/ct_local_env/demo_lab/evidence/mp_fixture_{apply,reset,verify}_*.json`
(verifier-generated: `...verify_20261004T173128Z.json`, `...verify_20261004T175810Z.json`).

---

## 9. Customer browser verification

Real frontend at `http://localhost:3000`, real password login, verifier's own assertions
(`/tmp/ct_pd5_verify/browser_probe.py`, screenshots in `/tmp/ct_pd5_verify/shots/`).

| # | State | Expected (CT-UX-MP-SUB-003 §10) | Observed | Result |
| --- | --- | --- | --- | --- |
| 1 | direct | included / available | `AVAILABLE`, *Included in your subscription*, *Commercially entitled, not yet configured*; no `NOT INCLUDED` | **PASS** |
| 2 | dual | direct **and** sponsored | `AVAILABLE`, *Your coverage includes:*, *Direct subscription*, *Consultant-sponsored coverage*, `EFFECTIVE ENTITLEMENT`, `GOVERNANCE STATUS`; no `NOT INCLUDED` | **PASS** |
| 3 | sponsored | provided by consultant | `AVAILABLE`, *Provided through your consultant*; no `NOT INCLUDED` | **PASS** |
| 4 | negative | not entitled | `NOT INCLUDED`; **no** `AVAILABLE` | **PASS** |

The UI was cross-checked against the API (§12): the rendered states match the server's
`direct_entitled` / `sponsored_entitled` / `governance.enabled` / `operational_status`.

---

## 10. Consultant browser verification

| # | State | Expected | Observed | Result |
| --- | --- | --- | --- | --- |
| 5 | SELECTED_CLIENTS coverage | capacity meter + covered list populated | tab renders `SELECTED CLIENTS`; meter `aria-valuenow=1 / aria-valuemax=3`; covered client **MP-FX Client — Direct + Sponsored** shown; **Add Client** present | **PASS** |
| 6 | Allocate | count increases | **independently performed**: allocate eligible client → meter `1 → 2` | **PASS** |
| 7 | Release | count returns, no unrelated allocation affected | **independently performed**: release → meter `2 → 1`; DB allocation count returns to baseline (convergence §7.5) | **PASS** |
| 8 | ALL_ELIGIBLE_CLIENTS coverage | all-eligible populated; **no** allocation control | tab renders `ALL ELIGIBLE CLIENTS`; eligible client rendered; **no** `Add Client` control | **PASS** |

The allocate/release (NV-8) executed a **real database write path**; the verifier re-runs the fixture
`apply` afterwards and confirmed convergence back to the declared baseline.

---

## 11. Admin browser verification

Logged in as `platform.admin`; `/ops` → **Commercial Coverage** tab.

| # | State | Observed | Result |
| --- | --- | --- | --- |
| 9a | Firm on `SELECTED_CLIENTS` ("Load coverage") | meter `1/3`; *Purchased capacity* **3 clients**; *Allocated* **1 / 3**; covered client org id listed | **PASS** |
| 9b | Firm on `ALL_ELIGIBLE_CLIENTS` | `ALL ELIGIBLE CLIENTS`; *Automatically covered*; eligibility source *Active consultant-client relationship*; **no** allocation control | **PASS** |
| 9c | Client effective state ("Load client state") | source **direct+sponsored**; governance `ENABLED`; PE `CONFIGURED` | **PASS** |
| 10 | Negative | eligible-but-unallocated client → `entitled=false`, `sponsored.reason=not_allocated` (§12) | **PASS** |

---

## 12. API / backend cross-checks

Independent API probe (own HTTP calls, real password logins, ids read from the DB) — **19/19**:

| Area | Check | Observed |
| --- | --- | --- |
| Customer | direct / dual / sponsored | `available`; sources `['direct']` / `['direct','sponsored']` / `['sponsored']`; `operational_status` `not_yet_configured` / `configured` / `not_yet_configured` |
| Customer | negative (`owner.b`) | `not_included`, `effective_entitled=false` |
| Consultant | selected | `enabled=true`, `SELECTED_CLIENTS`, `capacity=3`, `allocated=1`, `available=2`, `eligible=2`, `covered=1` |
| Consultant | all-eligible | `ALL_ELIGIBLE_CLIENTS`, `capacity=null`, `eligible=1` |
| Consultant | allocate in ALL mode refused | **409** "…apply only to SELECTED_CLIENTS coverage…" |
| Admin | selected coverage | `enabled=true`, `SELECTED_CLIENTS`, `allocated=1/3` |
| Admin | all-eligible coverage | `ALL_ELIGIBLE_CLIENTS`, `capacity=null`, `eligible=1` |
| Admin | client dual | `effective_entitlement.source = direct+sponsored`, governance enabled, configured |
| Admin | client unallocated (negative) | `entitled=false`, `sponsored.reason=not_allocated` |

Backend log for the verification window: **0** HTTP 5xx / tracebacks.

---

## 13. Authorization / security verification

All boundaries held — **no unexpected ALLOW**, and **nothing was weakened** to make a check pass.

| Boundary | Expectation | Observed |
| --- | --- | --- |
| customer reads another customer's coverage (both directions) | deny | **403** "You don't have access to this organization" |
| customer reaches the admin control plane | deny | **403** "Staff access required (active staff profile)" |
| unentitled customer reaches admin plane | deny | **403** |
| consultant firm **member** (no `manage_clients`) **reads** firm coverage (PD-3) | allow | **200** |
| consultant firm **member allocates** | deny | **403** "consultant lacks permission: manage_clients" |
| consultant firm **member releases** | deny | **403** "consultant lacks permission: manage_clients" |
| consultant with `manage_clients` allocates/releases own clients | allow | **200** (browser §10, API §12) |
| unauthenticated consultant coverage read | deny | **401** |
| release of a foreign/non-owned allocation | deny | **404** |
| negative customer cannot use Manual Processing just because fixture data exists | deny | `not_included` (customer §9, API §12) |

---

## 14. Demo Lab regression / isolation results

`python3 tools/demo_lab/verify.py` (after all fixture operations):

```
── actor contexts: 14/14 correct  (auth: password_grant)
── authorization / isolation probes: 30/30 as expected
── isolation rules enforced: 18/18
```

All DEMO-T1 identities still authenticate with correct contexts/routing; every isolation probe
(Org A↔B, Client A↔B, consultant↔unrelated org, customer↔admin, customer/internal↔PE,
viewer/member↔owner/admin) still behaves as before. Evidence `verify_20261004T180310Z.json`.

---

## 15. Production-safety verification

| Requirement | Evidence | Result |
| --- | --- | --- |
| No production endpoint accessed | fixture files reference only `127.0.0.1` / `localhost`; grep found no non-local `http(s)` endpoint | **OK** |
| No production/cloud reference | only doc-string mentions of "production/Render"; no `render.com` / `*.supabase.co` / `vercel` usage | **OK** |
| No production DB changed | all SQL ran via `docker exec … carbontally_demo_local`; no cloud DSN | **OK** |
| No production migration applied | no migration file added/modified by this task (`git status supabase/migrations/` shows only the 2 pre-existing untracked files) | **OK** |
| No Supabase production project linked | no `supabase link`/`db push` executed; the fixture's precondition is read-only | **OK** |
| No production credentials used | credentials read from local `credentials.local.json`; nothing secret printed | **OK** |
| No commit | HEAD unchanged `375a48dc…` | **OK** |
| No push | branch position unchanged | **OK** |
| No deployment | none performed | **OK** |

No STOP condition was encountered.

---

## 16. Worktree / commit / push status

| Item | Before | After |
| --- | --- | --- |
| `git status --porcelain` entries | 140 | **140** (unchanged) |
| Repository files modified by this verification | — | **none** (this report is the only new file) |
| `git commit` / `git push` | — | **none** |
| HEAD | `375a48dc…` | `375a48dc…` |

Observations on the fixture's worktree footprint:

```
 M tools/demo_lab/README.md          (documented by the PD-5 report)
 M tools/demo_lab/stack.py           (NOT documented — see N-2; belongs to CT-PO-UPLOAD-BATCH-REMEDIATION-001)
?? tools/demo_lab/fixture_mp_coverage.py
?? tools/demo_lab/fixture_mp_coverage_browser.py
```

Artifacts **created by this verification** are outside the repository: the probes and screenshots in
`/tmp/ct_pd5_verify/`, the frontend log `/tmp/ct_frontend_3000.log`, and new evidence JSON files under
`~/ct_local_env/demo_lab/evidence/`. No other-party work was reverted or cleaned. The local
environment was **left running** (backend `8070`, gateway `54430`, frontend `3000`).

---

## 17. Finding-by-finding disposition

| Finding / Gap | Description | Disposition | Evidence |
| --- | --- | --- | --- |
| **F-5** | Positive coverage states (capacity, covered clients, allocate/release, ALL_ELIGIBLE populated, customer available/direct/sponsored/direct+sponsored) **not browser-verified** | **CLOSED** | §9, §10, §11 browser (independent 8/8 + fixture 10/10 reproduced); §12 API 19/19 |
| **NV-1** | Browser rendering of SELECTED_CLIENTS capacity/allocation, covered-clients, allocate/release | **CLOSED** | §10 #5–7 (meter `1/3`, allocate `1→2`, release `2→1`, covered client shown); §11 #9a |
| **NV-2** | Browser rendering of ALL_ELIGIBLE_CLIENTS populated state | **CLOSED** | §10 #8 (populated, no allocation control); §11 #9b |
| **NV-3** | Browser rendering of customer available / direct / sponsored / direct+sponsored | **CLOSED** | §9 #1–3 |
| **NV-4** | Admin Commercial Coverage tab **after** loading a firm/organisation | **CLOSED** | §11 #9a–9c (selected, all-eligible, client effective state) |
| **NV-8** | Consultant allocate/release **against the real database** | **CLOSED** | §10 #6–7 (real write path `1→2→1`) + convergence §7.5 |

Reasoning for closure: each item now has genuine **real-browser** evidence (not merely unit/API), the
browser state is corroborated by the **actual API**, and the write path was exercised against the
**real database**. This is exactly the material evidence the historical report (§19) recorded as
missing.

---

## 18. Newly discovered findings (this verification)

Neither finding affects the targeted gaps; both are recorded for completeness.

**N-1 (LOW / operational) — a session token acquired *before* `fixture apply` is rejected after it.**
`ensure_user()` performs a GoTrue admin `PUT /admin/users/{id}` with the lab password on every
`apply` ([`provision.py:78`](tools/demo_lab/provision.py:78)); the observed effect is that a bearer token obtained
before `apply` returns **401 "Invalid authentication token"** afterwards. Re-login restores access.
Impact: none on the fixture's purpose (its own scripts log in *after* apply) and none on data
integrity. Recorded as an operational caveat for anyone holding a token across an `apply`.

**N-2 (LOW / documentation accuracy) — the PD-5 implementation report's file attribution is imprecise.**
`CT-MP-SUB-004-PD5-FIXTURE-01-report.md` §3/§10 states that only the two new fixture files plus
`tools/demo_lab/README.md` were touched. The worktree also contains a modification to
`tools/demo_lab/stack.py` (adds `x-upsert` to the lab CORS `Access-Control-Allow-Headers`). The change
is unambiguously attributable to a **different** task (**CT-PO-UPLOAD-BATCH-REMEDIATION-001**, per its
own in-file comment), so it is **not a PD-5 scope breach**; the report's statement is simply
imprecise. No action taken.

---

## 19. Explicit limitations

1. This verification covers **only** the targeted gaps F-5 / NV-1…NV-4 / NV-8. NV-5, NV-6, NV-7,
   NV-9 and NV-10 remain **not verified** (out of scope).
2. The fail-closed **migration gate** path was **inspected**, not dynamically triggered (all
   prerequisite tables were already present in the lab). Its behaviour is inferred from
   `precondition()` + the `SystemExit` guard.
3. Reset scoping was proven by **id/plan-code/user predicates and count deltas**; per-row FK cascade
   behaviour was not exhaustively enumerated for every dependent table.
4. Browser assertions are **structural/textual** (including the ARIA capacity meter), not pixel-level.
5. The frontend dev server on `localhost:3000` was **started by this verification**; the pre-existing
   `localhost:3100` process was left untouched and was not used.
6. The fixture targets the local Demo Lab by port only; it is not intended for any other environment.
7. This verification establishes **technical closure of the targeted gaps only**. It does **not**
   grant production deployment, migration application, or CT-MP-SUB-004 acceptance — those remain
   PO/ops gates (PD-6; PO decision record §9).

---

## 20. Final verdict

All six targeted gaps — **F-5, NV-1, NV-2, NV-3, NV-4, NV-8** — were independently reproduced and
closed with real-browser + real-API + real-database evidence, and the base Demo Lab
authorization/isolation baseline remains intact. The two incidental findings above (N-1, N-2) are low
severity, do not bear on the targeted gaps, and required no code change.

> ## VERIFIED — TARGETED GAPS CLOSED

Per the task rule, this verdict addresses the **verification** of the PD-5 fixture and the targeted
gaps. It does **not** itself constitute CT-MP-SUB-004 acceptance and does **not** authorise production
deployment or migration application.

---

### Reproduction quick-start

```bash
# 1. base demo lab verification
python3 tools/demo_lab/verify.py

# 2. fixture server-side verification
python3 tools/demo_lab/fixture_mp_coverage.py --verify

# 3. real-browser verification (frontend must be up on :3000)
python3 tools/demo_lab/fixture_mp_coverage_browser.py

# 4. verifier's independent probes (this report)
python3 /tmp/ct_pd5_verify/api_probe.py
python3 /tmp/ct_pd5_verify/browser_probe.py
python3 /tmp/ct_pd5_verify/roundtrip.py
python3 /tmp/ct_pd5_verify/convergence.py
```

*Report path: `docs/architecture/CT-MP-SUB-004-PD5-VERIFY-01-report.md`*
