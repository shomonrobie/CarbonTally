# CT-CONSULTANT-CLIENT-PLANE-PARITY-REMEDIATION-01

**F-NAV-1 — the consultant-operated client plane reaches the three
`/api/v3/reporting/*` organisation-plane endpoints**

Status: **IMPLEMENTED_AND_LAB_VERIFIED** (self, local Demo Lab).
This is NOT independently verified, NOT PO-accepted and NOT production-ready.

---

## 1. Task ID

`CT-CONSULTANT-CLIENT-PLANE-PARITY-REMEDIATION-01`

This is the single remaining authorization/parity item left OPEN by
`CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A` §19 (**F-NAV-1**), which that task
deliberately did **not** fix because it changes backend authorization.

It is **not** a navigation redesign, **not** a change to the consultant business
model, and **not** a widening of any tenant boundary. It removes a defect: the
organisation-plane reporting guard was *narrower* than the guard used by the
emissions/reports surfaces for the same, already-ratified consultant operating
plane (PD-3/PD-7 in `CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01`).

---

## 2. Starting SHA

```
branch : p8-release-reconciled
HEAD   : 3fec874ca1f170ecb03e7daf69992dbf9e9cd18e
```

The worktree was already dirty from preceding work (left intentionally
uncommitted). Those pre-existing modifications were preserved untouched.

---

## 3. Ending SHA

```
branch : p8-release-reconciled
HEAD   : 3fec874ca1f170ecb03e7daf69992dbf9e9cd18e   (unchanged — no commit)
```

No commit was made (not instructed). All work is worktree-only.

---

## 4. Worktree status

- HEAD unchanged; no `git reset --hard`, no `git clean -fd`, no rebase, no
  force-push, no checkout of unrelated work.
- No secret, token, signed URL or credential was written to any file.
- Files touched by THIS task are listed in §5. No unrelated change was absorbed.

---

## 5. Files changed

### Edited (tracked, pre-existing file)

| File | Change | sha256 after edit |
| --- | --- | --- |
| `backend/api/v3_reporting.py` | three routes moved onto the shared organisation-plane guard family; module docstring updated | `65624b50e3bc1f96575bbf8150b5857e898308b0fcdf6b0cc7affc937b426a4b` |

### New (untracked — deliberately not committed)

| File | Purpose |
| --- | --- |
| `backend/tests/unit/api/test_consultant_org_parity.py` (class `TestConsultantReachesManagedClientReporting`, file lines 503–621) | F-NAV-1 regression coverage: ALLOW **and** DENY cases for the reporting plane |
| `tools/demo_lab/verify_fnav1_reporting_scope_browser.py` | real-browser verification of the business outcome + the unchanged security boundary |

Both new files are already part of the uncommitted F-NAV-1 work; the file
`test_consultant_org_parity.py` carries the parity suite, to which this task
appended one class rather than creating a parallel file.

---

## 6. Root cause (verified, not inferred)

The three organisation-plane reporting endpoints declare **no organisation PATH
parameter** — the organisation is supplied as an `organization_id` **query**
parameter. Therefore `enforce_org_path_scope` (which the other organisation-plane
routes rely on for path-derived scope) is a no-op here, and the *entire* guard
chain was:

```python
current_user: AuthUser = Depends(get_current_user)   # authentication only
...
ensure_org_access(current_user, organization_id)     # tenant decision
```

`ensure_org_access` resolves membership from the caller's
`organization_members` rows. A consultant operating a managed client is
**not** an `organization_members` row of that client (PD-12 — the consultant is
admitted by the *authorization* layer, never by inventing a membership row), so
the consultant was refused **before** the consultant-aware admission step
(`require_org_member()` → `resolve_managed_org_ids` → `ensure_org_access`) could
ever run.

Observed user-visible effect (recorded verbatim in
`CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A` §19): inside the client workspace
the consultant saw `403` on `customer-dashboard`, `emissions-trend` and
`member-activity` — the D30 "Reporting overview" card was replaced by an error
message and the "Monthly emissions trend" panel stayed on "Loading trend…"
forever (the page swallows the failed trend request).

The route `GET /api/v3/reporting/consultant-portfolio` is a **different** plane
(consultant firm portfolio, `require_consultant`) and was already correct; it was
not touched.

---

## 7. The fix

The three routes now use the **same shared guard family** as the emissions
(`api/v3_emissions.py`) and reports (`api/v3_reports.py`) surfaces:

```python
# F-NAV-1 — the organisation plane guard, not a bare "any member" check
current_user: AuthUser = Depends(require_org_member()),
...
ensure_org_access(current_user, organization_id)
```

- `customer-dashboard` — `Depends(get_current_user)` → `Depends(require_org_member())`
- `emissions-trend` — same swap
- `member-activity` — same swap

`ensure_org_access` is **retained unchanged** on all three routes: it remains the
single tenant decision, so `require_org_member()` only contributes the
consultant-aware *admission*, never a second, parallel consultant authorization
rule. No new guard, no consultant-specific branch, no RLS change, no service-role
bypass, and no change to the response contract were introduced.

---

## 8. Frontend / API surface (unchanged by design)

The customer Home inside the client plane calls exactly these routes and nothing
new (`frontend/src/v3/api.js` → consumed by
`frontend/src/v3/customer/DashboardPage.jsx`, which the client plane reuses):

```
GET /api/v3/reporting/customer-dashboard?organization_id=…     api.js:1803
GET /api/v3/reporting/emissions-trend?organization_id=…&months=… api.js:1818
GET /api/v3/reporting/member-activity?organization_id=…          api.js:1821
```

The fix is server-side only: **no frontend file was changed**, and no UI
control was added, hidden, enabled or disabled as a substitute for the
authorization decision.

---

## 9. Tests

### 9.1 New regression class (unit, real routers over the in-memory world)

`backend/tests/unit/api/test_consultant_org_parity.py` →
`TestConsultantReachesManagedClientReporting` (8 tests). The shared surface under
test is `REPORTING_ROUTES` (all three F-NAV-1 URLs, `{org}`-formatted).

| Test | Property asserted |
| --- | --- |
| `test_consultant_with_active_grant_gets_the_same_reporting_payloads` | parity is proven *against the customer's own read*: the consultant's JSON is byte-equal to the customer owner's, each `200` carries `organization_id == org-a` (a `200` is only evidence when the payload is the **authorised** tenant's) |
| `test_consultant_is_denied_reporting_for_a_non_granted_organisation` | cross-tenant read is `403`, the other org id never appears in the response text, and the message stays the uniform `Organization access denied` (no consultant-specific oracle) |
| `test_reporting_denies_a_consultant_without_the_admission_capability` | F-1/§7.4 — the relationship row alone is not admission; `CAP-VIEW-CLIENT` is required → `403` |
| `test_revoking_the_grant_closes_the_reporting_plane` | AC-05 — scope is re-resolved per request; after the grant is `ended` all three routes are `403` and leak nothing |
| `test_suspended_client_tenant_closes_the_reporting_plane` | D-7 Decision B — a suspended client tenant serves its consultant nothing (`403`, `ORGANIZATION_SUSPENDED_DETAIL`) |
| `test_processing_entity_staff_cannot_reach_client_reporting` | D20 scope-first — the reporting plane never becomes a PE surface |
| `test_reporting_still_requires_authentication` | the guard swap must not open an anonymous path → `401` |
| `test_direct_customer_reporting_decision_is_unchanged` | AC-18 — a plain org **member** still gets `200` on its own org and `403` on another org |

Note (test-authoring detail, recorded because it is easy to get wrong): this
repository renders API denials in the standard envelope
`{"error": {"code", "message", "details"}}` (`api/router.py`) — **not**
`{"detail": …}` — so the denial assertions read `resp.json()["error"]["message"]`.

### 9.2 Runs performed in this session

| # | Command (cwd `backend/`) | Result |
| --- | --- | --- |
| 1 | `pytest tests/unit/api` | 2,631 collected; **exactly one** failure in the short-test summary — `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` (`assert True is False` on `verification_delivered`). No other failure/error. |
| 2 | `pytest tests/unit/api/test_consultant_org_parity.py tests/unit/api/test_f05_r1_org_scope_authorization.py tests/unit/api/test_reporting.py` | `114 passed, 4 warnings` in 77.56s — exit `0` |
| 3 | F-NAV-1 regression selection (parity + emissions/reports guard suites) | `446 passed, 4 warnings` — 0 failed |

Run 3 is the previously recorded F-NAV-1 regression selection
(`/tmp/fnav_regress2.txt`); runs 1–2 were re-executed against the final file sha
in §5, and run 2 is the selection that carries the 8 new F-NAV-1 tests.

### 9.3 Baseline — the one api-suite failure is pre-existing and unrelated

A pre-fix baseline probe was run with `backend/api/v3_reporting.py` **reverted**
to HEAD and then the fixed file restored (recorded restored sha
`65624b50…`, i.e. the sha in §5). That probe produced **8 failures without the
fix**:

```
FAILED tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin
FAILED tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
FAILED tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration
FAILED tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy
FAILED tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage
```

They fail **before** the change, so they are not caused by it. Their causes are
outside the touched surface: migration-count/ordering drift in
`supabase/migrations` (102 files present vs 71 pinned), the extraction-suggestion
date format (`2026-01-15` vs `15/01/2026`) and evidence-key expectations, and an
environment-dependent email-delivery flag in the discovery test. Only the first
of the eight lives in `tests/unit/api`, which is why run 1 shows a single
failure. **No test asserts the old (broken) reporting behaviour**, and the
reporting guard was not narrowed anywhere to make a test pass.

---

## 10. Lab / runtime verification (browser, Demo Lab)

Environment used (all local; nothing production-facing was touched):

| Component | Detail |
| --- | --- |
| Frontend | `http://localhost:3000` (running CRA, `react-scripts start`, pid 2781425/2781453) |
| Backend | `http://localhost:8070` — `uvicorn main:app`, fresh process **pid 3954292**, started after the §7 edit so the running code is the §5 sha |
| Supervisor | `tools/demo_lab/supervise_demo_lab.py run` (pid 2781366) — it auto-respawns children, so a child pid is not by itself evidence of which file is loaded |
| Driver | `~/ct_local_env/pwvenv/bin/python`, real headless Chrome with a **real password login** against the lab GoTrue (no token injection) |

Command:

```
~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_fnav1_reporting_scope_browser.py
```

Result (re-run against the final file sha for this report, not an earlier run):

```
status : PASS
checks : 20 passed, 0 failed
api    : http://localhost:8070   (DISCOVERED from the app's own traffic, not assumed)
```

Screenshots (meaningful authenticated workspace state, not landing pages):

```
~/ct_local_env/demo_lab/evidence/browser/fnav1_reporting_consultant_client_a_home.png
~/ct_local_env/demo_lab/evidence/browser/fnav1_reporting_consultant_member_client_a_home.png
~/ct_local_env/demo_lab/evidence/browser/fnav1_reporting_direct_customer_home.png
```

What the 20 checks establish:

1. **Business outcome (the point of the task).** As `consultant.owner` operating
   its managed client (client_a), the client-plane Home page renders the D30
   **"Reporting overview"** card, the **"Monthly emissions trend"** panel is *not*
   stuck on `Loading trend…`, and **no denial message** is present. All three
   reporting routes were observed returning **200** for the **client**
   organisation (`routes seen: customer-dashboard, emissions-trend,
   member-activity`).
2. **Boundaries not widened (`consultant_scope`).** The same session's own bearer
   token (never printed) reaches both of the firm's ACTIVE grants
   (client_a **and** client_b → 200/200/200) and is still refused the
   direct-customer organisations the firm does not manage
   (org_a → 403/403/403, org_b → 403/403/403). Knowing an organisation id grants
   nothing.
3. **Capability, not relationship (`restricted_consultant_member`,
   `consultant.member` with CAP-VIEW-CLIENT only).** Admitted to the client plane
   and reporting renders (trend resolves, no denial text).
4. **Customer regression (`owner.clienta`).** The member path is unchanged: own
   organisation 200/200/200 and reporting renders; another tenant refused
   (org_a → 403/403/403).

Expected noise in the console log: 2× `404` and 3× `403` — the latter are the
verifier's **intentional** cross-tenant denial probes, i.e. negative controls
behaving as designed, not application failures.

Browser results are the *business*-level check: corroboration of the API
decision, not a substitute for the unit boundary tests in §9 and not an
independent audit.

---

## 11. Security verification

| Boundary | Expected | Where proven |
| --- | --- | --- |
| Consultant → its own managed client (ACTIVE grant) | ALLOW 200, *same payload* as the customer's own read | unit §9.1 #1; browser §10.1 |
| Consultant → org the firm does not manage | DENY 403, no tenant id in the body, uniform message | unit §9.1 #2; browser §10.2 |
| Consultant without the admission capability | DENY 403 | unit §9.1 #3; browser §10.3 |
| Grant revoked (`ended`) | DENY 403 on the very next request | unit §9.1 #4 |
| Suspended client tenant (D-7 Decision B) | DENY 403 | unit §9.1 #5 |
| Processing Entity staff → customer reporting | DENY 403 | unit §9.1 #6 |
| Unauthenticated | DENY 401 | unit §9.1 #7 |
| Ordinary member → own org / other org | ALLOW 200 / DENY 403 (unchanged) | unit §9.1 #8; browser §10.4 |

The change removes a **false denial**; it adds no ALLOW that was previously a
DENY for any other principal, and it does not touch RLS, storage, or the
service-role path.

---

## 12. Scope discipline — what was deliberately NOT done

- No frontend change (no button hidden/shown, no route guard added).
- No RLS change, no migration, no schema change, no new table or index.
- No new API route, request schema or response field.
- No change to `ensure_org_access`, to `require_org_member()`, or to the
  consultant capability model; the parity mechanism ratified by
  `CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01` was **reused as-is**.
- No change to the `consultant-portfolio` route (a different plane).
- No investor-demo data, credential, or relationship was created, mutated or
  deleted; the verifier is read-only apart from its own screenshots.
- No commit.

---

## 13. Product decisions required

None. This task closes a defect against already-ratified decisions
(PD-3/PD-7 parity; PD-12 — consultants are not `organization_members` rows;
D-7 tenant liveness; D20 scope-first). It introduces no new policy.

Still open from `CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A` §19–§20 and
**unchanged** by this task: **PD-NAV-1** (no dedicated consultant "Firm &
Billing" surface) and **R-NAV-1** (legacy consultant item route).

---

## 14. Remaining limitations (honest)

- **Self-verified only.** All verification is self-performed on the local Demo
  Lab. No independent audit has re-tested F-NAV-1, so the status is
  `IMPLEMENTED_AND_LAB_VERIFIED`, **not** `ACCEPTED`.
- **One pre-existing failure remains** in `tests/unit/api`
  (`test_v3_discovery…`), plus the seven non-api pre-existing failures listed in
  §9.3. They are unrelated to this change and were **not** fixed here (out of
  scope).
- The full `tests/unit` tree (5,168 collected) was **not** re-run end-to-end in
  this session; the api suite (2,631) plus the parity/F-05 regression selection
  (§9.2) and the pre-fix baseline (§9.3) were.
- Local `:8070` backend + `:3000` frontend were used, per `frontend/.env.local`.
  Production deployment topology and OCR/email environment capabilities are
  unaffected by this change and out of scope.
- The two new files (§5) are **untracked**; nothing has been committed, so the
  work exists only in the worktree.

---

## 15. Acceptance status

```
IMPLEMENTED            yes  — backend/api/v3_reporting.py §7 (sha 65624b50…)
TESTED                 yes  — 8 new unit tests (§9.1), suite runs (§9.2)
LAB-VERIFIED           yes  — 20/20 browser checks, PASS (§10)
INDEPENDENTLY VERIFIED no   — no third-party re-test
PO-ACCEPTED            no
PRODUCTION-READY       no
```

**F-NAV-1: CLOSED (implemented, tested, locally browser-verified) — pending
independent verification.**

---

## 16. Evidence index

| Artefact | Location |
| --- | --- |
| Diff of the fix vs HEAD | `/tmp/b35.txt` |
| New test class (source) | `backend/tests/unit/api/test_consultant_org_parity.py:503–621` |
| api-suite run | `/tmp/b23.txt` (2,631 collected; 1 pre-existing failure) |
| Targeted run (parity + F-05 + reporting) | `/tmp/b47.txt` (`114 passed, 4 warnings`, exit `0`) |
| Targeted run (parity + F-05) | `/tmp/b37.txt` (`PARITY_EXIT=0`) |
| F-NAV-1 regression selection | `/tmp/fnav_regress2.txt` (446 passed) |
| Pre-fix baseline probe | `/tmp/fnav_baseline.txt` |
| Browser verification (JSON) | `/tmp/b21.txt`, `/tmp/b48.txt` — `PASS`, `api: http://localhost:8070` |
| Screenshots | `~/ct_local_env/demo_lab/evidence/browser/fnav1_reporting_*.png` |
| Verifier source | `tools/demo_lab/verify_fnav1_reporting_scope_browser.py` |
| Prior task that opened F-NAV-1 | `docs/architecture/CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A.md` §19 |


