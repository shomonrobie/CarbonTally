# CarbonTally WS4 — Gate 6 — Workstream W3 Implementation Report
**G6-C: Human-After-Automation Attribution Exposure (job API/domain contract)**

- **Date:** 4 September 2026
- **Authority:** G6-A and G6-B PASSED/ACCEPTED. This workstream addresses
  **G6-C only**: the minimum necessary exposure, through the existing job
  API/domain contract, of the original automated output/provenance and the
  authoritative human-after-automation attribution.
- **Git HEAD:** `1639121`. **No commit. No push.** G6-D was **not**
  implemented. No migration was required.

---

## 1. Current API/domain gap discovered (after G6-A / G6-B)

After G6-A and G6-B the persistence side already carried everything needed:

- machine provenance (`automation` block) and the G6-A preserved original
  output (`automation_extracted_data`) existed on the DPQ row;
- the human gates (confirm/retry/review) already persisted authoritative actor
  fields on the DPQ row (`created_by`, `updated_by`, `customer_reviewed_by/at`,
  `customer_approved`, `customer_notes`, `customer_rejection_reason`) and G6-B
  audit events.

What was **missing** was representation: the domain model
(`AutomaticProcessingJob`) did not map the human actor columns, the DPQ
repository `_JOB_COLUMNS`/mapper did not read them, and `_job_payload` exposed
neither the preserved original output (`automation_extracted_data`) nor any
human attribution. An authorized consumer of the job surface therefore could
not, from the API alone, (a) distinguish original machine output from current
human-edited output, or (b) see which human acted after automation and what the
review decision was. The G6-B audit events were persisted but not represented
on the job contract, and G6-C explicitly forbids exposing the raw audit trail.

## 2. Files changed

| File | Change |
|---|---|
| `backend/domain/automatic_processing.py` | `AutomaticProcessingJob` gains authoritative read-only human fields: `created_by`, `updated_by`, `customer_reviewed_by`, `customer_reviewed_at`, `customer_approved`, `customer_notes`, `customer_rejection_reason` (semantics documented). |
| `backend/data/document_processing.py` | `_JOB_COLUMNS` + row mapper now read those existing DB columns (verified round-trip against the live main DB). No schema change. |
| `backend/api/v3_automatic_processing.py` | `_job_payload` now returns `automation_extracted_data` (original machine output) and a distinct `human` block. All existing keys untouched. |
| `backend/tests/unit/api/test_v3_automatic_processing_jobs.py` | API test fakes mirror the repo human-field persistence; 4 focused G6-C tests added (module total 19). |
| `docs/architecture/CARBONTALLY_WS4_GATE6_W3_REPORT.md` | This report. |

## 3. Exact fields / contract exposed

Additive, read-only additions to the existing job list/detail/confirm/retry/
review payload (`_job_payload`):

- `automation_extracted_data` — the original machine-produced extraction output
  preserved by G6-A (write-once). Always separate from the existing
  `extracted_data` (the current, human-editable output). `null` when no
  automated output was ever durably produced (legacy/blocked/failed) — never
  fabricated.
- `human` — a clearly distinct structure (never mixed into the machine
  `automation` block):
  - `created_by` — authenticated user who uploaded/enqueued the job;
  - `updated_by` — authenticated user of the last confirm/retry re-enqueue
    (the authoritative actor field those gates persist);
  - `customer_reviewed_by`, `customer_reviewed_at` — owner/admin reviewer and
    timestamp of the review decision;
  - `customer_approved` — `true`/`false` outcome;
  - `customer_rejection_reason`, `customer_notes` — decision context.

The `automation` block (`provider`/`model`/`model_version`) and every existing
field are unchanged. No raw audit rows, no audit endpoint, and no actor field is
accepted from client input.

## 4. Authorization boundary

Reused the existing org-scoped job surface unchanged: `_checked_job` +
`ensure_processing_org_access` (owning org members, internal CarbonTally
staff/operations, and consultants with an ACTIVE client grant) for
list/detail/confirm/retry, and `require_org_admin` for the customer review
decision. PE staff remain denied on the job surface; customer users see only
their own organisation’s jobs. No new endpoint, role, or capability was added.

## 5. Security verification

- The exposed fields are read from the authoritative DPQ row only; actor
  identity is never taken from the request body (verified by test: a
  client-supplied `"actor"`/`"created_by"` is ignored and the returned
  `human.updated_by` is the authenticated user).
- Cross-organisation detail/confirm remains denied (403), PE detail denied
  (403), unauthenticated denied (401) — existing tests unchanged and passing;
  the new representation cannot be used to discover unrelated jobs.
- `automatic_pipeline` is a machine actor and can never appear in the `human`
  block; the machine `automation` block and G6-A `automation_extracted_data`
  are not writable via any human path.
- No RLS change; no new authorization path; no secrets or audit internals
  exposed.

## 6. Tests and results

- Focused run from `backend/`:
  `pytest tests/unit/api/test_v3_automatic_processing_jobs.py
  tests/unit/api/test_v3_automatic_processing_payload.py
  tests/unit/domain/test_automatic_processing.py
  tests/unit/services/test_automatic_processing.py
  tests/unit/api/test_gate4_remediation_actor_provenance.py -q`
  → **57 passed** (19 in the jobs API module: 8 original Gate-5 + 7 G6-B + 4
  G6-C; plus payload, domain, G6-A service and Gate-4 regression tests).
- `py_compile` of the four changed modules → OK.
- Read-only live-DB probe: the extended `_JOB_COLUMNS` SELECT + row mapper
  round-trip against the main DB succeeds; existing rows unchanged.

New G6-C tests prove: (1) an authorized caller receives the machine provenance
and the original `automation_extracted_data`; (2) original vs current output is
distinguishable (`automation_extracted_data` ≠ human-corrected
`extracted_data`); (3) a separate `human` block exists and is never merged into
machine attribution; (4) the human actor (`human.updated_by`,
`human.customer_reviewed_by`) is the authenticated actor; (5) client-supplied
actor/identity fields are ignored; (6) review outcome/timestamp are exposed;
(7) a legacy job with no automation and no human action stays truthful (all
nulls, nothing inferred). Existing tests already cover the remaining security
rows (cross-org 403, PE 403, unauthenticated 401, G6-A immutability, G6-B audit
semantics) and are unchanged/passing.

## 7. Compatibility impact

Purely additive: two new top-level keys (`automation_extracted_data`,
`human`) and no removal, rename or type change of any existing field. The
existing `automation` block and all prior payload fields are preserved exactly,
so existing API consumers are unaffected (verified by the unchanged payload
contract tests). No versioning introduced.

## 8. G6-D not implemented

Confirmed: no resume-marker/correction integrity work (G6-D), no item-level
human extraction-edit auditing, no workflow/audit/authorization redesign, and
no analytics/reporting changes were introduced by this workstream.

## 9. Architectural concerns

None. The exposure reuses the existing org-scoped job contract and the
authoritative DPQ actor columns (the second source explicitly allowed by the
G6-C data-truthfulness rule); no audit-trail query, no new table, no migration
and no new authorization surface was required. One noted semantic: `updated_by`
is the last confirm/retry re-enqueue actor (both gates share the same
authoritative field); the precise action distinction (confirm vs retry) remains
in the G6-B audit events, which are intentionally not surfaced through this job
payload to honour the “do not expose more audit data than necessary” rule.

**Status: G6-C IMPLEMENTED & TESTED — awaiting PO review/acceptance.**

