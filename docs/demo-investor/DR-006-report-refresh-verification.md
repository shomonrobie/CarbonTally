# DR-006 — Report Refresh Verification

- **Prompt ID:** `DR-006`
- **Timestamp:** 2026-09-21, ~03:5x–04:2x local (≈2026-09-20 21:59 UTC generation)
- **Scope:** the **only** authorised mutation was regenerating the existing Demo Lab report(s) through CarbonTally's existing report-generation mechanism.
- **No** report-engine, frontend, schema, RLS, storage, factor, extraction or emissions change was made. R-A was **not** approved.

Evidence labels: `CODE-TRACED` · `RUNTIME-OBSERVED` · `BROWSER-VERIFIED` · `DATABASE-OBSERVED` · `ARTIFACT-VERIFIED` · `INFERENCE` · `LIMITATION`.

---

## 1. Git baseline

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD | `81074b2cd05be3ec9155c6e816c54d2940a777de` (== DR-005, as required) |
| Working tree | clean (`git status --porcelain` empty) |
| Remote divergence | `0 0` vs `github/p8-release-reconciled` |

## 2. Pre-generation report state

`DATABASE-OBSERVED` (read-only API reads before any mutation):

| Report | Type | Year | Status | Version | Generated | Totals in content |
| --- | --- | --- | --- | --- | --- | --- |
| `906ce1fc-066a-49c4-b651-8dc964a8c091` | `annual` | 2025 | `completed` / Ready (12 pages) | v1 `3524a75a-…`, status `DRAFT`, file `report-906ce1fc-….json` | `2026-09-20T13:47:27Z` | `{status: insufficient_data, total_co2e_kg: null, note: "no emissions data in reporting period"}`; lineage `emissions_logs.count 0` |
| `baf7e3f8-b255-47f5-99ff-ba16966dd067` | `ghg_inventory` | 2025 | `completed` / Ready (12 pages) | **no versions** (`[]`; `current_version {}`) | `2026-09-20T13:47:21Z` | same `insufficient_data` totals; no `2469` |

Both artefacts were 2,358 B / 2,372 B and contained no R-A data — consistent with DR-005's staleness finding (reports generated 13:47; R-A emissions row created 19:16).

## 3. Report-generation architecture (`CODE-TRACED`)

- **UI** `ReportsPage` (`+ Generate report`) → `api.js` → `generateReport(payload)` → **`POST /api/v3/reports`** with `{organization_id, report_type, reporting_year}` (`frontend/src/v3/reports/ReportsPage.jsx:50-53`; `frontend/src/v3/api.js`).
- **Backend** `backend/api/v3_reports.py` → `@router.post("", status_code=201) async def generate_report(payload: ReportGenerateIn, …)` with `require_org_member()`, `ensure_org_access(...)`, `validate_report_type(...)` and a DI-injected `ReportGenerationEngine`.
  - Docstring: *"Generate a report through the authoritative engine (**synchronous**). Lifecycle: QUEUED → GENERATING → READY (`completed`), or → FAILED with the real `error_log` persisted. On success a version snapshot is recorded on the existing `report_versions` table."*
  - `repos.reports.create_generation_request(...)` creates the queue row **first**, so every lifecycle state is persisted.
- **Type allow-list:** `validate_report_type` rejects unregistered types; `GET /api/v3/reports/types` returns exactly `[{"id":"annual","name":"Annual emissions report (structured 12-section V3 report)"}]`. `RUNTIME-OBSERVED`
- **Aggregation (evidenced by the generated content):** `"source": "emissions_logs + emission_factors (read-only aggregation)"`, `figures_from: emissions_logs_aggregation`, filtered by `organization_id` + `reporting_year` (`2025-01-01 → 2025-12-31`), factor ids resolved from `emission_factors`; methodology `direct_multiply`, engine `report_generation` v1.0.
- **Artifact:** produced by the engine, served by `GET /api/v3/reports/{report_id}/download` (attachment JSON).
- **Version/state:** a successful generation records a `report_versions` snapshot (`is_current=True`, `status=DRAFT`) on the **new** report row; pre-existing rows/versions are untouched.
- **Already designed to pick up new emissions?** **Yes** — each run re-aggregates `emissions_logs` read-only for the org/period; nothing caches the aggregate.
- **Not a regeneration path:** `POST /api/v3/reports/{report_id}/versions` only copies the source version's immutable engine content into a new `DRAFT` version (*"The new version carries the source version's system `content` (engine output is immutable)"*) — it would not see new emissions, so it was **not** used.

## 4. Regeneration mechanism used (Part D)

The existing product mechanism, unchanged: `POST /api/v3/reports` under the org's existing identity (`require_org_member`), exactly two calls — `{"organization_id":"3fd0f325-16a1-5b53-8fb8-27929cf218fa","report_type":"annual","reporting_year":2025}` and `{…,"report_type":"ghg_inventory","reporting_year":2025}`. No SQL, no manual artifact replacement, no storage manipulation, no code change; generation is synchronous (~0.16 s).

## 5. Generation results

| Report | Request | Result |
| --- | --- | --- |
| **Annual** | `POST /api/v3/reports` `{org, annual, 2025}` | **HTTP 201** in 0.159 s — success. Response `{report, content}`; new report `a7e76a38-4ef7-47d8-8f46-f5dce8f9e51d`, `status completed` / `Ready`, 12 pages, `created_at 2026-09-20T21:59:32Z` |
| **GHG inventory** | `POST /api/v3/reports` `{org, ghg_inventory, 2025}` | **HTTP 422 — BLOCKED BY DESIGN**, no state change. Verbatim: `{"success":false,"error":{"code":422,"message":"unsupported report type 'ghg_inventory'; supported: annual","timestamp":"2026-09-21T03:59:32.298580","path":"/api/v3/reports"}}` |

The 422 is a **type allow-list rejection**, not an engine failure: the API currently supports only `annual`. The pre-existing `ghg_inventory` row stems from an earlier/other path and **cannot be regenerated through the current API** — recorded as a concrete finding (§15) and **not fixed** (Part F/L boundary).

## 6. Resulting versions and artifacts

- **New annual report**: id `a7e76a38-4ef7-47d8-8f46-f5dce8f9e51d`; version **1** = `892db750-2c6e-4262-85ab-feb66549660e` (`is_current: true`, `status: DRAFT`, `change_summary: "Generated annual report for 2025 by 589dbadf-…"`, `file_name: report-a7e76a38-…json`).
- **Artifact**: `GET /api/v3/reports/a7e76a38-…/download` → **HTTP 200**, `application/json`, `content-disposition: attachment; filename="report-a7e76a38-…json"`, **4,735 bytes** (previous artefact 2,358 B).
- **Pre-existing artefacts intact**: `906ce1fc-…` still downloads (HTTP 200, 2,358 B); `baf7e3f8-…` unchanged.

## 7. Report content after regeneration (Part G)

`ARTIFACT-VERIFIED` + `BROWSER-VERIFIED` — the regenerated annual report now contains the R-A calculation:

| Field | Value |
| --- | --- |
| Reporting period | `2025-01-01 → 2025-12-31` (reporting_year 2025) |
| Organization | `Demo Lab Organisation A` (`3fd0f325-…`), country `GB`, `found`, active |
| **Emissions totals** | `{"status":"available","total_co2e_kg":"2469.169780","unit":"kg CO2e","source":"DEFRA-DESNZ","total_rows":1}` |
| **Scope 1** | `{"Scope 1":{"co2e_kg":"2469.169780","unit":"kg CO2e"}}`, scopes status `available`, unit `kg CO2e`, source `DEFRA-DESNZ` |
| **Activity (Natural gas)** | `{"activity_type":"Fuels > Gaseous fuels > Natural gas (kg CO2e) [kWh (Net CV)]","co2e_kg":"2469.169780","quantity":"12181.4","unit":"kWh (Net CV)","row_count":1}`, `total_activities: 1` |
| Factor provenance | `{"countries":["GB"],"factor_sets":["DEFRA-2025"],"gas_coverage":"CO2e","factor_sources":["DEFRA-DESNZ"]}` |
| Source lineage | `{"source":"emissions_logs + emission_factors (read-only aggregation)","aggregate":{"total_rows":1,"by_scope_count":1},"emissions_logs":{"count":1,"reporting_year":2025},"emission_factors":{"resolved":1,"factor_ids":["b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5"]}}` |
| Calculation information | `{"unit":"kg CO2e","status":"available","methodology":"direct_multiply","figures_from":"emissions_logs_aggregation","algorithm_version":"v1.0"}` |
| Benchmarking | `scope:Scope 1 → value 2469.169780, source DEFRA-DESNZ, status available`; activity intensity `0.202700 kg CO2e per kWh (Net CV)` (= 2469.169780 ÷ 12181.4); per-FTE/area/revenue correctly `not_available` (denominators absent from org metadata) |
| Validation | `{"ok":true,"status":"passed","counts":{"error":0,"warning":0,"suggestion":0},"issues":[]}` |
| Metadata | `report_type annual`, engine `report_generation` v1.0, `generated_at 2026-09-20T21:59:32Z` |

The previous condition — `"no emissions data in reporting period"` — is **no longer presented** for this report; the string `insufficient_data` occurs **zero times** in the new artefact.

## 8. UI verification (`BROWSER-VERIFIED`)

Real browser login (`org_a_owner`) → `/reports`:

- Counters changed from `READY 2` to **`READY 3`**; the new row is `Annual emissions report 2025 | annual | 2025 | Ready | Sep 21, 2026, 03:59 AM | 1 | 589dbadf | View Download`, alongside the preserved `Annual emissions report 2025 (Sep 20, 2026, 07:47 PM)` and `ghg_inventory 2025 (07:47 PM)`.
- Opening the new row → `/reports/a7e76a38-4ef7-47d8-8f46-f5dce8f9e51d`: **Emissions totals** `{"unit":"kg CO2e","source":"DEFRA-DESNZ","status":"available","total_rows":1,"total_co2e_kg":"2469.169780"}`; Source lineage `COMPLETE` with `emissions_logs.count 1` and `factor_ids ["b9d1ed06-…"]`; Factor provenance `COMPLETE` (`GB`, `DEFRA-2025`, `CO2e`); Calculation information `COMPLETE` (`kg CO2e`, `available`, `direct_multiply`, `v1.0`); Validation `COMPLETE` / passed; details `ORGANIZATION Demo Lab Organisation A`, `REPORT TYPE annual`, `REPORTING PERIOD 2025-01-01 → 2025-12-31`, `STATUS Ready`.
- APIs: `GET /api/v3/reports`, `/api/v3/reports/{id}`, `/content`, `/versions` → all **200**; **zero console errors**. Screenshots: `/tmp/dr006_shots/{a_reports_after,b_annual_detail}.png`.

## 9. Artifact verification (Part H)

| Check | Result |
| --- | --- |
| HTTP status | **200 OK** |
| MIME / disposition | `application/json`; `attachment; filename="report-a7e76a38-4ef7-47d8-8f46-f5dce8f9e51d.json"` |
| Size | **4,735 bytes** (superseded artefact 2,358 B) |
| Valid content | yes — JSON with `report_id`, `organization_id`, `report_type`, `reporting_year`, `status`, `generated_at`, `branding`, 12-section `content` |
| Report version | version 1 of the new report row (`892db750-…`, `is_current: true`) |
| Generated timestamp | `content.generation.generated_at = 2026-09-20T21:59:32.163338+00:00`; row `created_at/completed_at 21:59:32Z` |
| Organization / period | `3fd0f325-16a1-5b53-8fb8-27929cf218fa` / `2025-01-01 → 2025-12-31` |
| Emissions total | **`2469.169780 kg CO2e`** (source `DEFRA-DESNZ`) |
| R-A linkage | factor id `b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5` and quantity `12181.4 kWh (Net CV)` present via `emission_factors.factor_ids` + the activity row. The **emissions-log id (`eb88e764…`) and snapshot id (`af640887…`) are not stored in the report content** — the report aggregates at factor/activity level (limitation, not a defect: the snapshot is verified elsewhere). |

The **artifact itself** (not just the UI) contains the updated result: `/tmp/artifact_after.json` contains `2469` ×1 and **0** × `insufficient_data`; the preserved old artefact contains `0` × `2469` and `1` × `insufficient_data`.

## 10. R-A consistency check (Part I)

| Source | Value | Consistent? |
| --- | --- | --- |
| Dashboard `/home` | `TOTAL TCO₂E 2.47` · `EMISSIONS ROWS 1` (= 2,469.16978 kg) | ✓ |
| Emissions `/emissions` | `2469.16978 kg CO₂e`, factor `…Natural gas (kg CO2e) [kWh (Net CV)]`, `Scope 1` | ✓ |
| Snapshot (UI/workspace) | `af640887-5818-47ad-b351-1505ac049c32` | ✓ |
| Emissions log (export CSV) | `eb88e764-…`, `calculated_kg_co2e 2469.16978`, `snapshot_id af640887-…`, `source_item_id 2b41b332-…` | ✓ |
| **Reports (regenerated annual 2025)** | `total_co2e_kg 2469.169780`, Scope 1 `2469.169780`, activity `Natural gas` `12181.4 kWh (Net CV)`, factor set `DEFRA-2025`, factor id `b9d1ed06-…` | ✓ |

No discrepancy found between dashboard/emissions/snapshot/emissions-log and the regenerated report.

## 11. Historical versioning behaviour (Part J)

- Regeneration **created a new report row + a new version + a new artifact**; nothing was overwritten or deleted.
- Preserved: `906ce1fc-…` (annual 2025, v1 `3524a75a-…`, 2,358 B, `insufficient_data`) and `baf7e3f8-…` (ghg_inventory 2025, 2,372 B) — both still listed in the UI and still downloadable (HTTP 200).
- Refresh lineage: `906ce1fc-…` (v1, 13:47Z, pre-R-A) → **`a7e76a38-…` (v1, 21:59Z, includes R-A)**.
- `LIMITATION`: the refreshed report is a **separate report row of the same type/year**, not a new version of the original row, so the UI shows two "Annual emissions report 2025" rows (03:59 AM and 07:47 PM). Whether the product should support in-place regeneration is a PO decision — the existing `/{id}/versions` route cannot do it (it copies immutable engine output).

## 12. Data mutation audit

| Action | Authorised? | Occurred |
| --- | --- | --- |
| `POST /api/v3/reports` (`annual`, org A, 2025) | **Yes** (Part E) | **Yes** — 1 new report `a7e76a38-…` + 1 version + 1 artefact |
| `POST /api/v3/reports` (`ghg_inventory`) | Yes (attempted) | **Rejected 422**, no state change |
| R-A approval / rejection | No | No |
| Extraction, mapping, factors, emissions, snapshots | No | No |
| Documents, processing jobs, retries | No | No |
| Other report types / other organizations | No | No |
| Exports, subscriptions, payments, messages | No | No |
| Demo Lab reset / reseed / configuration change | No | No |

## 13. Files changed

| File | Change |
| --- | --- |
| `docs/demo-investor/DR-006-report-refresh-verification.md` | new (committed) |

**Runtime (non-repository) changes from the authorised regeneration** — deliberately **not** committed as files: one `reports` row, one `report_versions` row, one generation-request row and one JSON artefact for report `a7e76a38-…`. No product code, tooling, schema, RLS or configuration was modified.

## 14. Report-generation errors

1. **`ghg_inventory` regeneration refused** — `POST /api/v3/reports` → **422** `unsupported report type 'ghg_inventory'; supported: annual`. Root cause (`CODE-TRACED` + `RUNTIME-OBSERVED`): the generation API's report-type allow-list contains only `annual` (`GET /api/v3/reports/types` → `["annual"]`), while the Demo Lab contains a pre-existing `ghg_inventory` row created by an earlier/other path. **No fix applied** (Part F/L boundary).
2. Otherwise none: the annual generation completed synchronously in 0.159 s, `status completed`, no `error_log`, validation `passed`, and zero console errors during UI verification.

## 15. Remaining limitations

- The **ghg_inventory** report still reports `insufficient_data` for 2025 and cannot be refreshed through the current API (§14) — the only remaining investor-facing report inconsistency in the Demo Lab.
- The refreshed content exposes **factor-level provenance only** (`factor_ids`, factor set/source); the calculation **snapshot id** (`af640887…`) and the emissions-log id are not embedded in the artefact.
- The refreshed annual report is a **second report row** of the same type/year rather than a new version of the original (§11), so identical titles appear twice in the reports list.
- The new version's snapshot status is `DRAFT` while its report row reports `completed`/Ready (pre-existing behaviour, also true of the old row) — a minor state-labelling observation, not investigated further.
- The PDF variant (`GET /{report_id}/pdf`) and the report lifecycle actions (submit/approve/request-changes/reject/finalize) were not exercised.

## 16. PO decisions required

1. Whether the **ghg_inventory** report should be (a) made regenerable via the API (allow-list/engine scope — a code change, not authorised here), (b) removed from the Demo Lab as a stale artefact, or (c) accepted as a known limitation.
2. Whether the product should support **in-place regeneration as a new version** of an existing report (currently a new row is created, producing duplicate titles).
3. Whether the report artefact should embed the **calculation snapshot id** for stronger investor-facing provenance.
4. Whether the superseded pre-R-A annual report should remain visible in the demo (history is preserved by design).
5. Whether a documented **report-refresh step** should be run before any investor session.

## 17. Verification matrix (Part M)

| Report | Before | Generation | After UI | After artifact | R-A included? | Versioning | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Annual | Ready, `insufficient_data`, 2,358 B, 13:47Z | **HTTP 201** (0.159 s) | Ready, totals `2469.169780 kg CO2e`; lineage/provenance/validation COMPLETE | 200, `application/json`, 4,735 B, `2469`×1, `insufficient_data`×0 | **Yes** | new row `a7e76a38-…` + v1 `892db750-…`; old row/version/artefact preserved | **VERIFIED** |
| GHG inventory | Ready, `insufficient_data`, 2,372 B, 13:47Z | **HTTP 422** — type unsupported by the API | unchanged (`insufficient_data`) | unchanged (2,372 B; no `2469`) | No | none created | **BLOCKED** |

## 18. Final bounded verdict

The existing report-generation implementation **does** incorporate current emissions data when re-run: one authorised `POST /api/v3/reports` produced a new Ready annual report whose UI, API content and downloaded artefact all report **`2469.169780 kg CO2e`** for Scope 1 / Natural gas with `DEFRA-2025` factor provenance, `emissions_logs.count 1`, factor id `b9d1ed06-…`, quantity `12181.4 kWh (Net CV)`, passed validation, and **no** occurrence of `insufficient_data`. The "no emissions data in reporting period" condition is therefore resolved for the annual report, and the superseded artefact was preserved rather than overwritten. The `ghg_inventory` report could **not** be refreshed because the generation API supports only `annual` (HTTP 422) — documented verbatim and deliberately **not** fixed. No product code, schema, RLS, storage, factor, extraction, emissions or approval state was changed; the only runtime mutations were the authorised report generation and its version/artefact records. CarbonTally is **not** declared investor-ready and this report asserts nothing beyond the evidence above.
