# CarbonTally V3 — Phase B (CL-54): Customer Processing Workspace — Implementation Report

**Implementer:** Cline
**Date:** 2026-08-29
**Baseline:** `6148c86` (`main`) + Phase A (CL-56) automatic pipeline
**Authoritative contract:** OpenHands `CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md` CL-54,
per the Phase 2 implementation order.

---

## 1. What was built

A **genuine customer processing workspace** in the customer application:

* `GET /processing` — a real dashboard: upload, pipeline status, every processing item
  (with live status) that deep-links into the item workspace, and the durable
  automatic-processing jobs (Phase A) with retry/confirm actions.
* `GET /processing/:itemId` — a routed, deep-linkable, refresh-safe item workspace:
  split-screen source document + data/actions, covering the full customer journey:

  upload → see processing status → open document → inspect extraction → edit
  extraction → map factors → validate → calculate → see emissions → see evidence
  → send to review → approve/reject (owner/admin).

## 2. Security boundary (the explicit requirement)

**"Do not expose staff-only `/ops/items/...` endpoints to customers."**

The customer workspace uses ONLY the org-scoped `/api/v3/processing/*` surface:

| Customer action | Org-scoped endpoint | Staff surface it replaces |
|---|---|---|
| Open item workspace | `GET /api/v3/processing/items/{id}/workspace` | `GET /api/v3/ops/items/{id}/workspace` (require_staff) |
| Claim a stage | `POST /api/v3/processing/items/{id}/start` | `POST /api/v3/ops/items/{id}/start` |
| Save extraction | `POST /api/v3/processing/items/{id}/extract` | `POST /api/v3/ops/items/{id}/extract` |
| Save mapping | `POST /api/v3/processing/items/{id}/map` | `POST /api/v3/ops/items/{id}/map` |
| Validate | `POST /api/v3/processing/items/{id}/validate` | `POST /api/v3/ops/items/{id}/validate` |
| Calculate | `POST /api/v3/processing/items/{id}/calculate` | `POST /api/v3/ops/items/{id}/calculate` |
| Mapping options | `GET /api/v3/processing/items/{id}/mapping-options` | `GET /api/v3/ops/items/{id}/mapping-options` |
| Approve/Reject | `POST /api/v3/processing/items/{id}/customer-review` (owner/admin) | `POST /api/v3/ops/items/{id}/qc` (staff) |

**Bug fixed:** the customer `ReviewDetailPage` previously called the staff
`getItemWorkspace` (`/api/v3/ops/items/{id}/workspace`, `require_staff`) — it now uses the
org-scoped workspace endpoint. Live verification: the customer receives **403** on
`/api/v3/ops/items/{id}/workspace` and **200** on `/api/v3/processing/items/{id}/workspace`.

## 3. Files

| File | Change |
|---|---|
| `frontend/src/v3/api.js` | New org-scoped customer-processing client functions (`getProcessingItemWorkspace`, `startProcessingItem`, `saveProcessingExtraction`, `saveProcessingMapping`, `validateProcessingItem`, `calculateProcessingItem`, `getProcessingMappingOptions`, `getProcessingStatus`, `getProcessingQueue`, `getProcessingNextItem`, `getProcessingIssues`, `getProcessingJobs`, `getProcessingJob`, `enqueueDocumentForProcessing`, `confirmProcessingJob`, `retryProcessingJob`, `reviewProcessingJob`). |
| `frontend/src/v3/customer/ProcessingPage.jsx` | Rebuilt as the genuine processing dashboard (upload + pipeline status + items + automatic jobs). |
| `frontend/src/v3/customer/ProcessingItemPage.jsx` | New routed page at `/processing/:itemId`. |
| `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` | New org-scoped item workspace (source viewer + extraction/mapping/validation/calculation/evidence/review/approve). |
| `frontend/src/v3/customer/ReviewDetailPage.jsx` | Switched from staff `getItemWorkspace` to org-scoped `getProcessingItemWorkspace`. |
| `frontend/src/App.js` | Registered `/processing/:itemId` under the customer `RoleRoute requireOrg`. |
| `frontend/src/v3/__tests__/customer-processing-api.test.js` | New — asserts the customer surface uses only `/api/v3/processing/*` and never staff functions. |
| `frontend/src/v3/__tests__/customer-processing-workspace.test.jsx` | New — component test: panes render, calculated result shown, Approve/Reject only for owner/admin. |

Backend: no new endpoints were required — the org-scoped `/api/v3/processing/*` surface (v3_processing_workflow)
already provides the workspace contract (`source` + `data` + `status` + `issues` + `workflow`) and the
server-authoritative state machine (including the CL-2 `validated -> calculating -> calculated` gate).

## 4. Verification

### Live API boundary
* Customer owner `GET /api/v3/processing/items/{id}/workspace` → **200** (workspace payload).
* Customer owner `GET /api/v3/ops/items/{id}/workspace` → **403** (require_staff — never used by the app).
* Full flow exercised live as the customer owner: upload → automatic pipeline calculates →
  workspace shows the result → send to review (`customer_review`) → approve (`approved`,
  `customer_approved=True`).
* **Member** `POST .../customer-review` → **403** "Organization admin privileges required" (D5 gate).

### Frontend tests
* `src/v3` suite: **125 passed / 8 suites** (including the 7 new CL-54 tests).
* `npx react-scripts build` → **success**.
