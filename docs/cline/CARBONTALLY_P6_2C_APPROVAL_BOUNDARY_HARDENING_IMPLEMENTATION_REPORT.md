# CarbonTally P6-2C — Approval-Boundary Hardening & Workflow-Stage Authorisation — Implementation Report

1. **Contract Ref:** `CARBONTALLY-P6-2C-IC-20260910-001`
2. **Prompt Ref:** `CT-P6-2C-IMPL-20260910-001` (Response Ref `CT-P6-2C-IMPL-20260910-001-R`)
3. **Implementation date/time:** 2026-09-10, approx. 16:30–17:10 local (Asia/Dhaka +0600)
4. **Objective:** implement exactly the P6-2C contract — make `calculated → approved`
   automatic-processing-only (PO-P6-2C-D1), gate the consultant `review`/`source`
   stage claims on existing capabilities (PO-P6-2C-D2), and preserve everything
   else including billing (PO-P6-2C-D3).
5. **PO decisions relied upon:** `PO-P6-2C-D1-20260910` = A;
   `PO-P6-2C-D2-20260910` = A; `PO-P6-2C-D3-20260910` = A
   (`docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`).

## 6. Files inspected

`docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`;
`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`;
`CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`;
`CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_CONTRACT.md`;
`CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md`;
`CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`;
`docs/cline/prompt-history/CT-P6-2C-RA-20260910-001.md`;
`docs/cline/prompt-history/CT-P6-2C-PO-20260910-001.md`;
P6-1C/P6-2A/P6-2A-R1/P6-2B-1..4 implementation + verification reports.
Code: `backend/api/v3_processing_workflow.py` (`_STAGE_PERMISSION`,
`_STAGE_WORKING_STATUS`, `start_item`, `customer_review_item`,
`consultant-review`, `consultant-submit`);
`backend/domain/partners.py` (`ITEM_STATUS_FLOW`, `WORKFLOW_STAGES`);
`backend/api/processing_mode.py`; `backend/api/consultant_auth.py`
(`ensure_consultant_processing_authorized`, `CONSULTANT_PERMISSIONS`);
`backend/api/v3_operations.py`; `backend/api/v3_pe.py`;
`backend/api/v3_automatic_processing.py` (`review_job`, `_job_payload`);
`backend/auth.py` (`require_org_admin`); `backend/api/operations_auth.py`;
`backend/tests/unit/api/test_p6_2b_4_ct_qc_prerequisite.py` (fixture patterns).

## 7. Files changed

| Path | Change |
|---|---|
| `backend/api/v3_processing_workflow.py` | S1 + S2 + S3 (2 bounded edits) |
| `backend/tests/unit/api/test_p6_2c_approval_boundary.py` | **new** focused suite (30 tests) |
| `docs/cline/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_REPORT.md` | **new** (this report) |
| `docs/cline/prompt-history/CT-P6-2C-IMPL-20260910-001.md` | **new** prompt-history record |

## 8. Files intentionally unchanged

`backend/domain/partners.py` (the `calculated → approved` entry is **kept** —
PO-D1); `backend/api/processing_mode.py` (predicate semantics frozen — reused,
not modified); `backend/api/consultant_auth.py` (no new keys/permissions);
`backend/api/v3_automatic_processing.py`; the automatic worker and services;
`backend/services/billing.py`; `backend/api/v3_pe.py`;
`backend/data/manual_extraction.py`; `backend/data/document_processing.py`;
`backend/api/dependencies.py`; all `supabase/**` (schema/migrations/RLS);
all pre-existing tests; frontend (no UI change); Master Roadmap; Blueprint.

## 9. Detailed implementation changes

**S1 — `calculated → approved` is automatic-processing-only**
(`customer_review_item`, `POST /api/v3/processing/items/{id}/customer-review`).
After the existing state-machine check and before the CT-QC prerequisite guard and
the D37 charge, a new guard runs for source status `calculated`:

```python
if item.status == "calculated":
    from api.processing_mode import item_is_automatic
    if not await item_is_automatic(repos, item):
        raise HTTPException(403, "... automatic-processing only ...")
```

Any `calculated` approval is therefore explicitly conditional on the item being
AUTOMATIC under the existing, unchanged P1 predicate (`item_is_automatic`). The
state-machine transition itself is untouched and grants no authority; manual work
keeps its CT-QC path; the pre-existing PE-origin, CT-QC-prerequisite, reason,
billing and concurrency behaviour is unchanged.

**S2 — consultant `review` stage claim requires `can_submit`** and
**S3 — `source` alias requires `can_extract`** (`_STAGE_PERMISSION`):

```python
_STAGE_PERMISSION = {
    "source": "extract", "extraction": "extract", "mapping": "map",
    "validation": "validate", "calculation": "calculate", "review": "submit",
}
```

`start_item` already passes `_STAGE_PERMISSION.get(payload.stage)` into the
canonical resolver `ensure_consultant_processing_authorized` via
`_get_checked_item`, so **no new authorization logic** was added: the existing
`identity → firm → active grant → resource → action → stage` resolver now also
covers these two stage claims. No new capability/role/permission. Organisation
members and internal staff are unaffected (the resolver is actor-class aware).
The `consultant-review` *action* endpoint is untouched (its ratified
permission-free review semantics are preserved).

## 10. Security behaviour

- `calculated → approved` for a manual item → **403** (explicit automatic-only).
- Consultant / PE / Operations / member / viewer / unauthenticated / cross-org
  actor → **403/401** on the approval route (unchanged, re-proven).
- Consultant with an active grant and **zero** capabilities → **403** on the
  `review` stage claim (previously 200).
- Consultant holding `can_submit` → legitimate `review` claim still **200**.
- `source` claim: `can_extract` required (**403** without, **200** with).
- `reviewed → customer_review` → **409** (P6-2B-4 protection intact).
- PE-origin guard intact; actor/ID injection rejected; IDOR denied.

## 11. Workflow behaviour

`ITEM_STATUS_FLOW` is **unmodified**; `reviewed` still has no `customer_review`
exit; the canonical manual path `… → ct_qc_approved → customer_review → approved`
still works (proven); invalid transitions still **409** with zero mutation.

## 12. Automatic-processing behaviour

Unchanged: the worker, `/jobs/*` routes and the automatic approval path are
untouched. An automatic item at `calculated` is still approved by the org
owner/admin (**200**, one charge) and the `/jobs/{id}/review` route still
completes the job and stamps the item.

## 13. Consultant capability behaviour

Only the *stage claim* is newly gated. The six-flag model is unchanged; no flag
was added, renamed or widened. `can_submit` retains its existing meaning
(consultant submission) and now also gates the generic `review` stage claim.

## 14. Billing preservation (PO-P6-2C-D3)

**No billing change.** `services/billing.py` untouched; no new/removed charge; no
idempotency/subscription/refund change. Tests assert: one charge at Customer
Approval (500 → 499); zero charge on every denied path; automatic
`/jobs/{id}/review` still charges nothing (existing behaviour, unchanged).

## 15. Provenance preservation

`processing_origin`, `processing_entity_id` and `source_item_id` are untouched by
both the allowed and the denied flows (asserted in the new suite).

## 16. Audit behaviour

Guards run before mutation/charge; denied requests write **no** success audit
record (asserted); successful consultant review still audits (asserted).
Append-only audit trail untouched.

## 17. Focused tests

`backend/tests/unit/api/test_p6_2c_approval_boundary.py` — **30 tests**:

| Area | Tests |
|---|---|
| D1 approval boundary | automatic owner approval (row 18); manual `calculated` approval + rejection denied (rows 10/11/19); consultant (1); PE (2); operations (3); member (4); viewer (5); unauthenticated (6); cross-org (7); invalid transition 409 (16); PE-origin guard (20); `ct_qc_approved` manual approval still works; double-approval idempotency (17); alternate endpoints (12/13); actor/identity injection (14); job-review stamp without charge (23) |
| D2 stage gating | 0-capability consultant `review` denied (8); `can_submit` allowed (9); wrong-flag denied; `source` requires `can_extract` (10); cross-firm IDOR denied (15); org-member unchanged (D10); internal staff unchanged; `reviewed → customer_review` 409 (11) |
| Parity/audit/provenance | ops/PE stage-claim parity (S4); denied ⇒ no success audit / success ⇒ audit (21); provenance unchanged on allowed + denied flows (22) |

Run: `pytest -q tests/unit/api/test_p6_2c_approval_boundary.py` → **30 passed**.

## 18. Regression tests

Targeted regression group (contract §14 list), run in one command:
`pytest -q <23 suites>` → **408 tests, 100% pass, EXIT 0**
(P6-2B-4/3/2/1, P6-2A, P6-2A-R1, P6-BILL-1, `v3_processing_workflow`,
`phase1_core_regressions`, `v3_operations`, `v3_qc`, `processing_origin_qc`,
`v1_2_dual_origin_workflow`, automatic jobs/payload/services, `operations_auth`,
`scope_aware_authorization`, `pe_auth`, `billing_core`, `v3_consultants`,
P6-1B, P6-1C).
**No existing test was modified.**

## 19. Full-unit test result

`pytest -q tests/unit` → **EXIT 0** (no failures/errors, 100% progress).

## 20. Test counts

| Measure | Value |
|---|---|
| Baseline (before this task) | 1,576 collected |
| New focused suite | +30 tests (`test_p6_2c_approval_boundary.py`) |
| **Collected now** | **1,606** |
| Focused suite result | 30 passed |
| Targeted regression group | 408 tests, 100% pass, EXIT 0 |
| Full unit suite result | **EXIT 0** |

The +30 increase is exactly the new P6-2C suite; no existing test was added,
removed or modified.

## 21. Failures

None in the final runs. (During development two of my *new* provenance tests
initially failed because they called the async in-memory `get_item_origin`
without awaiting; they were corrected in the new test file. No production defect
was involved.)

## 22. Warnings

One pre-existing environment warning only:
`RequestsDependencyWarning: urllib3 (2.7.0) / chardet / charset_normalizer`
(site-packages, unrelated to P6-2C).

## 23. Risks

| Risk | Assessment |
|---|---|
| Guard placement in the approval route | Placed after the state machine (409 preserved) and before the charge; verified by tests |
| Over-gating consultants | Only the `review`/`source` **stage claims** are gated, on existing capabilities; legitimate flows proven |
| `source` alias gating beyond the literal D2 wording | Contract S3; removable as a one-line change if the PO scopes D2 to `review` only |
| Billing drift | No billing file touched; each denied path asserts zero charge |
| P1 predicate dependence | Predicate reused unchanged; fail-closed (non-automatic ⇒ denied) |

## 24. Scope verification

Implemented exactly contract scope S1–S5:
S1 automatic-only `calculated → approved`; S2 `review` → `can_submit`;
S3 `source` → `can_extract`; S4 parity verified by tests; S5 focused suite.
No P6-2D/E/F, Phase 7/8, UI, billing, schema, migration, RLS, provenance,
automatic-processing architecture or new-capability work was performed.

## 25. Remaining deferred items

Automatic job-review billing policy (PO-P6-2C-D3 — **DEFERRED**); D4 PE↔Consultant
handoff; D6/D7 (P6-2D); D8/D11 (P6-2E); `/consultant` UI + E2E (P6-2F);
on-disk verification artifacts for P6-2B-4 / P6-1B / P6-1C.

## 26. Final verdict

**P6-2C IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION**

## 27. STOP-condition confirmation

No stop condition occurred: no authority/contract conflict, no new
role/capability/permission, no schema/migration/RLS need, no billing change, no
automatic-processing redesign, no predicate change, no existing test weakened or
deleted, no P6-2D/E/F scope, no unresolved ambiguity.

**"P6-2C implementation is complete for this task. STOP. Do not perform
independent verification, do not begin P6-2D, and do not commit or push."**

*(No commit. No push. Independent verification is a separate subsequent gate and
has NOT been performed by this task.)*


