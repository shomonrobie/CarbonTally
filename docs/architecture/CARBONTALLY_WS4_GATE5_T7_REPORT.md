# CarbonTally WS4 — Gate 5 — T7 Implementation Report
**Task T7: full regression suite (unit provenance/write-once/audit + API positive/negative)**

- **Date:** 4 September 2026
- **Git HEAD (verified):** `1639121` — nothing committed or pushed.
- **Accepted design:** `docs/architecture/CARBONTALLY_WS4_GATE5_DESIGN_READINESS_REPORT.md`
- **Predecessors:** T1–T6 COMPLETE/ACCEPTED. **Gate 5 has NOT passed.**

---

## 1. Exact T7 task executed

T7 from the accepted design report's implementation work breakdown (item 7):

> **T7 — Regression suite.** Unit (extraction provenance, write-once, audit) +
> API positive/negative tests; run the full backend unit suite; confirm the
> pre-existing unrelated integration-suite failures are unaffected (documented,
> out of scope).

Executed:

1. **Unit regression coverage verified in place** (from T3/T4): extraction
   provenance + write-once + audit tests exist in
   `tests/unit/services/test_automatic_processing.py` (`TestPhase2AIDurableExtraction`,
   `TestT4ExtractionAudit`, incl. contributing-AI merge persistence, failed-AI
   truthfulness, deterministic-only NULL, per-column write-once, machine-audit
   event shape, audit-failure resilience) and all pass.
2. **New API positive/negative tests** added in
   `tests/unit/api/test_v3_automatic_processing_jobs.py` (8 tests) against the
   in-memory FastAPI harness (`tests/unit/api/conftest.py`) with an in-memory
   `DocumentProcessingRepository` fake — covering the design §11 API row (job
   list/detail automation block for the owning org; cross-org detail/list denied;
   PE staff denied; unauthenticated denied; confirm keeps the automation block
   and stays org/PE-bound; review still requires org-admin authority).
3. **Full backend unit suite executed**: `pytest tests/unit` — all **1366
   tests passed** (exit 0).
4. **Pre-existing unrelated integration-suite failures confirmed unaffected**:
   no integration-suite file or dependency was modified in T7 (or in T1–T6); the
   known stale test-DB schema/signature drift failures remain documented and out
   of scope. Nothing in T7 touches that suite's environment.

No acceptance run, no migration, no production-code change.

---

## 2. Files changed

| File | Change |
|---|---|
| `backend/tests/unit/api/test_v3_automatic_processing_jobs.py` | **New** — 8 API positive/negative tests (in-memory DPQ repo fake, reuses existing harness fixtures). |
| `docs/architecture/CARBONTALLY_WS4_GATE5_T7_REPORT.md` | **New** — this report. |

No production code, migration, or RLS file changed; nothing committed or staged.

---

## 3. Migrations

**None.** T7 is a test/regression task; no migration was created or applied.

---

## 4. Tests executed

1. **New API module** `tests/unit/api/test_v3_automatic_processing_jobs.py`
   (8 tests) — positive/negative for `/api/v3/processing/jobs`:
   - detail returns the typed `automation` block for the owning org (200);
   - list returns org-scoped jobs with `automation` blocks + `total` + `by_stage`;
   - cross-org detail denied (403);
   - cross-org list denied (403);
   - PE-staff detail denied (403);
   - unauthenticated detail denied (401);
   - confirm: owning-org member 200 with automation block preserved through the
     human gate; cross-org and PE-staff confirm denied (403) — authorization
     unchanged;
   - review: plain org member denied (403), org owner (admin authority) 200 with
     automation block intact.
2. **Full backend unit suite** `pytest tests/unit` (1366 tests, exit 0).
3. Focused per-task suites already green from earlier tasks are included in the
   full-suite pass (service provenance/write-once/audit, API payload tests,
   domain, data-layer compile, infra, engine).

---

## 5. Results

| Test run | Result |
|---|---|
| `tests/unit/api/test_v3_automatic_processing_jobs.py` (new, 8 tests) | **8 passed** (exit 0) |
| Full backend unit suite `pytest tests/unit` | **1366 tests — all passed** (exit 0; 100% progress, no failures) |

New API assertions green:
- Detail/list for the owning org return the typed `automation` block
  (provider/model/model_version) next to `ai_extraction`.
- Cross-org job detail and list are denied with genuine 403s (org-bound
  `ensure_processing_org_access`).
- PE staff are denied on detail and on the confirm gate (403) — no machine/PE
  leakage into customer-org processing surfaces.
- Unauthenticated requests are denied (401).
- The write-once automation block survives the human confirm gate and the
  owner review at the API boundary (values unchanged in responses).
- `require_org_admin` review authorization is unchanged (member 403 / owner
  200).

Unit regression (already present from T3/T4, now re-run inside the full suite):
extraction provenance persistence, deterministic-only NULL truthfulness,
failed-AI attempted-model truthfulness, per-column write-once, and the
`automatic_processing:extracted` machine-audit event (incl. best-effort failure
behaviour).

---

## 6. Data-integrity impact

**None.** T7 adds in-memory tests only; no database, schema, or persistent data
was touched (no fixtures against real DBs, no migrations). No demo/investor data
was read or mutated. Unit/API tests run entirely against fakes.

---

## 7. Security impact

- New negative tests assert that the machine-provenance `automation` block
  introduces **no authorization path**: it is served only to the owning org's
  authorised users; cross-org and PE-staff requests are denied 403, and the
  machine actor (`automatic_pipeline`) appears nowhere as a user/PE/role/D38
  assignee/authorization principal.
- The block remains read-only evidence on the org-scoped endpoints; no new
  role, policy, or RLS change; Gate-4 human-provenance mechanism untouched.

---

## 8. Confirmation: T8 was not executed

Confirmed. This session performed **T7 only**. The Gate-5 verification fixture /
acceptance run (T8) was not executed. No production code or migration was
changed; nothing was committed or pushed.

---

## 9. Remaining Gate 5 work

Per the accepted design report (§12), after T7 the following remains:

- **T8** — Verification-only Gate-5 fixture run + acceptance evidence
  (machine-provenance matrix on the real stack with disposable fixtures and
  exact baseline restoration).

**Gate 5 is NOT passed** and no acceptance claim is made by this report.

---

## 10. Blockers discovered

**None.** No architecture decision beyond the accepted design was required; T7
introduces no conflict with Gate 4 or the frozen architecture. The pre-existing
unrelated integration-suite failures (stale test-DB schema/signature drift) are
documented and out of scope, and were not modified.

---

## FINAL VERDICT

**T7 COMPLETE**

Gate 5 has **not** been executed or passed. Nothing was committed or pushed.

