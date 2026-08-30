# CarbonTally — Legacy Admin Dependency & Deprecation Inventory (D-P2-02)

**Status:** Ratified PO decision **D-P2-02 — DEPRECATE** (2026-08-30).
The V3 internal operations surface (`/ops`) is the canonical CarbonTally
internal administration system. Legacy admin functionality is **deprecated,
not deleted** — it remains mounted until the retirement conditions below are
met (AGENTS.md §79 legacy-code rule; the control-plane decision at
`CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`).

## 1. Scope

Legacy admin = the `routes/admin/*` package, mounted under `/api/admin/*`
(and `/api/v2/admin/audit`). It was the Phase-1-era administrative CRA's API.
No new feature is built on it; the V3 `/ops` application is the only supported
staff surface.

## 2. Feature coverage inventory (legacy → V3 replacement)

| # | Legacy surface (prefix) | Representative routes | V3 replacement | Coverage | Depends on legacy? | Notes |
|---|---|---|---|---|---|---|
| 1 | `/api/admin/staff` | list/create/update/delete, role change, reset-password, performance | `/api/v3/ops/staff` + `/api/v3/ops/staff-roles` (`StaffRoster.jsx`, `StaffRolesTab.jsx`) | ✅ FULL | No | Staff profile + role permission model is V3-canonical (`staff_roles.permissions`). |
| 2 | `/api/admin/permissions` | roles CRUD, permissions list, setup-defaults | `/api/v3/ops/staff-roles` (catalog read); role write via ops staff role surface | 🟡 PARTIAL | No | V3 reads the real catalog; role-edit write surface is minimal — treat legacy role-edit as superseded-by-read-only until an ops role-editor is built. |
| 3 | `/api/admin/reviews` + `review_history` | queue, assign, complete, reject, reorder, escalate, SLA monitor, history | `/api/v3/ops/queues/review` + `/api/v3/ops/review/*` + `GET /api/v3/ops/review-reporting` | ✅ FULL | No | V3 review queue resolves real items (UH-7 phantom rows dropped). |
| 4 | `/api/admin/assignments` | batch/review assignment, assignment-stats | `/api/v3/ops/batches/{id}/assign`, `/api/v3/ops/review/{id}/assign` | ✅ FULL | No | V3 assignment model = real `manual_extraction_batches.assigned_to` / `entity_id`. |
| 5 | `/api/admin/extraction` | approve, manual-review-note, batch/approve, reviews/pending | `/api/v3/processing/*`, `/api/v3/ops/items/{id}/*` (extract/map/validate/qc) | ✅ FULL | No | V3 pipeline is the D23 engine (server-authoritative). |
| 6 | `/api/admin/defra` | factor list/get/create/update | `/api/v3/emissions/factors` (read) + factor imports (`admin_imports.py` / `admin_providers.py`) | 🟡 PARTIAL | No | V3 reads factors; factor WRITE/import is via the V3 provider/import surface — verify `admin_imports` coverage before retiring `defra` writes. |
| 7 | `/api/admin/audit` + `audit-logs` | activity, export, stats, users | `/api/v2/admin/audit` (`admin_audit.py`, `AuditConsoleTab.jsx`) | ✅ FULL | No | V3 admin audit console is the canonical audit UI. |
| 8 | `/api/admin/workload` + `/api/admin` (workload) | staff workload, queue settings/stats/reassign | `/api/v3/ops/queues/*` + `/api/v3/ops/reporting/qc` + review reporting | 🟡 PARTIAL | No | V3 reporting covers queues/QC/review; the full workload-forecast read remains legacy-only. |
| 9 | `/api/admin/dashboard` + `analytics` | stats, documents, staff, orgs, SLA, system, queue, alerts, health/performance/usage | `/api/v3/ops/dashboard` + `/api/v3/ops/reporting/*` + `GET /api/v3/ops/reporting/qc` | 🟡 PARTIAL | No | Core dashboards are V3; legacy analytics extras (alerts, health detail) have no V3 twin yet. |
| 10 | `/api/admin/bulk` | org/documents status bulk ops + bulk delete | — | ❌ NONE | Yes (for those ops) | Bulk operational tooling — no V3 replacement. Keep until a V3 bulk surface is built or the need is formally dropped. |
| 11 | `/api/admin/beta` | beta access codes + beta users | — | ❌ NONE | Yes | Beta management is internal-only and has no V3 surface. Keep (internal ops tool). |
| 12 | `/api/admin/email/templates` + `/api/admin/logs` | template CRUD/preview, email/processing logs | — | ❌ NONE | Yes | Email templates + email/processing logs are legacy-only. Keep until the V3 admin console adds template/log management. |
| 13 | `/api/admin/document-types` | document types + extraction templates + mapping | `/api/v3/documents` (read) + `document_type_categories` | 🟡 PARTIAL | No | V3 documents surface covers customer-facing types; admin document-type CRUD is legacy-only. |
| 14 | `/api/admin/settings` | settings history, validate, reset | `/api/v3/settings/retention` (GET/PUT) | 🟡 PARTIAL | No | Retention is V3-canonical (D-P2-04). Other legacy settings (history/reset) have no V3 twin. |

## 3. Who still depends on legacy admin

- The **quarantined legacy admin CRA** (served by the deployment rewrite in
  `vercel.json` at `/admin/*`). No V3 code imports `routes/admin`.
- Internal ops tools without a V3 twin (bulk ops, beta codes, email templates,
  email/processing logs, document-type admin) — these have **no active V3
  consumer** and are used directly by operators today.
- Existing automated tests that pin legacy admin endpoints
  (e.g. `require_admin` regression, `/api/v2/admin/audit`).

## 4. Retirement conditions (must ALL hold before removal)

1. V3 replacements exist for every covered row above with ✅ or 🟡 (i.e. the
   🟡/❌ rows each have a shipped V3 twin or a written PO decision to drop the
   capability).
2. The legacy admin CRA rewrite (`vercel.json`) is removed from deployment.
3. No test, tool or runbook references `/api/admin/*` or `/api/v2/admin/audit`.
4. The permission drift guardrail holds: a single staff-role catalog
   (`staff_roles.permissions`) with no split-brain legacy catalog.

## 5. Deprecation status

All `/api/admin/*` and `/api/v2/admin/audit` surfaces are **DEPRECATED**
(documented here). They remain functional and mounted — **do not delete** —
until §4 is satisfied. No new features may be built on them.
