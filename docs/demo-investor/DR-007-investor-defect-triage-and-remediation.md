# DR-007 — Investor-Facing Defect Triage + Bounded Remediation

- **Prompt ID:** `DR-007`
- **Nature:** read-only triage of nine issues, then **bounded** Phase-2 fixes only where a clear display defect was established.
- **R-A was not recalculated, remapped, re-extracted or approved.**

Evidence labels: `CODE-TRACED` · `RUNTIME-OBSERVED` · `BROWSER-VERIFIED` · `DATABASE-OBSERVED` · `ARTIFACT-VERIFIED` · `INFERENCE` · `LIMITATION`.

---

## 1. Git baseline (before changes)

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD | `51716c1101ef10898404133da8506dccae4594db` (== DR-006, as required) |
| Working tree | clean |
| Remote divergence | `0 0` vs `github/p8-release-reconciled` |

## 2. Issue investigations

### Issue 1 — Documents "Uploaded" column
- `CODE-TRACED`: `frontend/src/v3/customer/DocumentsPage.jsx` declared the column `accessor: 'created_at'` and rendered `{d.created_at || '—'}`.
- `CODE-TRACED` (backend): `backend/data/documents.py` builds the entity field **`uploaded_at = r.get("upload_date") or r.get("created_at")`**; `backend/api/v3_documents.py` `list_documents()` returns those entities under `"documents"`.
- `BROWSER-VERIFIED`: the payload carries the timestamp, yet the pre-fix UI showed `—` for all nine documents.
- **Root cause: frontend read the wrong field name.** Genuine frontend display defect (Category A).

### Issue 2 — Workspace `Scope -`
- `CODE-TRACED`: `ProcessingItemWorkspace.jsx` rendered `Scope {data.mapped_data?.scope || '-'}`, while `mapped_data` (observed in DR-004) contains `unit, status, activity, factor_id, factor_kind, methodology, source_ordinal, stages_executed, mapping_confidence` — **no `scope`**.
- `DATABASE-OBSERVED`: scope is authoritative elsewhere — the factor row has `"scope":"Scope 1"`, the emissions row has `scope`, and the export CSV carries `scope = Scope 1`.
- **Root cause: the panel read a non-existent payload path**; every other surface renders `Scope 1` correctly. Genuine display defect (Category A).

### Issue 3 — Review `Mapped activity —`
- `CODE-TRACED`: `ReviewDetailPage.jsx` used `data.mapped_data?.activity_type || '—'`, but the payload's `mapped_data` carries **`activity`** (`"activity":"Natural gas"`); `activity_type` is an emission-*factor* field.
- **Root cause: frontend read the wrong key.** Genuine display defect (Category A).

### Issue 4 — Factor source terminology (`DEFRA-DESNZ` vs `DEFRA-2025`)
- `DATABASE-OBSERVED` (read-only SQL, factor `b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5`): the row carries **two distinct fields** — `"factor_source":"DEFRA-DESNZ"` **and** `"factor_set":"DEFRA-2025"` (plus `reporting_year 2025`, `unit "kWh (Net CV)"`, `"scope":"Scope 1"`, `co2e_multiplier 0.2027`, `country GB`).
- The drawer renders `Source DEFRA-DESNZ` / `Set DEFRA-2025`; report content renders `factor_sources ["DEFRA-DESNZ"]` / `factor_sets ["DEFRA-2025"]`.
- **Conclusion: NOT a defect — intentional, data-faithful terminology** (source = publishing dataset family, set = annual factor set). No cosmetic change made.

### Issue 5 — Evidence `Technical details / Evidence record`
- `CODE-TRACED`: `frontend/src/v3/components/EvidenceRecordPanel.jsx:79-80` renders a **native HTML disclosure** — `<details class="v3-evidence-details"><summary>Technical details / Evidence record</summary>`, containing Emission log id, Calculation snapshot id, Extraction item id, Source file id, Factor id and (when present) Source page.
- DR-004's "not clickable" observation was a **harness limitation** (its helper matched only `button`/`a`; `<summary>` is neither).
- **Conclusion: NOT a defect** — the detail view exists and the backend supplies the ids. No change made. (`LIMITATION`: re-expansion was not re-clicked in DR-007's scripted run; the markup is traced and the drawer itself was opened and verified in DR-004.)

### Issue 6 — Extraction `Currency` / `Amount` labels
- `CODE-TRACED`: these are **editable inputs of the extraction-correction form** (`TextInput label="Currency" value={header.currency} disabled={!editableExtraction}`; likewise `Amount`), rendered so a human can correct the header, disabled once the item leaves the extraction stage.
- The R-A document genuinely has no currency/amount (`extracted_data` = date, unit, activity, quantity, supplier, invoice_number), so they render empty by design.
- **Conclusion: intentional product behaviour, not data loss.** A UX observation (hide empty locked fields) is recorded for PO; not changed because it touches extraction display.

### Issue 7 — Customer document detail / preview
- `CODE-TRACED`: the router registers `/documents` only (no `/documents/:id`); a document row opens an inline "Emissions derived from …" panel, and the processing workspace carries the per-document source, extraction, mapping, calculation and evidence panes.
- **Conclusion: the customer document view is represented through the processing workspace + inline emissions panel; a dedicated document-detail/preview page is a missing capability → `PO DECISION REQUIRED`.** No feature created (Part D).

### Issue 8 — Duplicate annual reports
- `CODE-TRACED`: generation is `POST /api/v3/reports` → `create_generation_request(...)` → a **new report row per call** (verified in DR-006); the list is data-driven, newest first; versioning is per row and DR-006 established that history is preserved rather than overwritten.
- **Conclusion: expected generation semantics + a stale pre-R-A Demo Lab artefact — not a code defect.** The investor-visible effect (two "Annual emissions report 2025" rows, one `insufficient_data`) is recorded. **No deletion performed (PO decision).**

### Issue 9 — Stale `ghg_inventory` report
- `CODE-TRACED`: grepping `ghg_inventory` across `frontend/` and `backend/` (excluding `.venv`) returns **zero references** → it is **not an advertised product feature** and the UI does not reference it; the row appears only because the reports list renders what exists for the organisation.
- `RUNTIME-OBSERVED`: `GET /api/v3/reports/types` → `[{"id":"annual", …}]`; `POST /api/v3/reports` with `ghg_inventory` → **422** `unsupported report type`.
- **Conclusion: legacy/stale Demo Lab data, not a product defect. `PO DECISION REQUIRED`** on keep/remove; generation was **not** implemented and the artefact was **not** deleted.

## 3. Classification matrix (Part B)

| Issue | Root cause | Investor impact | Genuine defect? | Fix authorized? | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Uploaded column | FE read `created_at`; API field is `uploaded_at` | Nine documents looked undated | **Yes — display** | **Yes (Cat A)** | **FIXED** |
| Scope | FE read `mapped_data.scope`; scope lives on the emissions row | Result looked under-specified vs evidence | **Yes — display** | **Yes (Cat A)** | **FIXED** |
| Mapped activity | FE read `mapped_data.activity_type`; payload has `activity` | Looked as though no mapping existed | **Yes — display** | **Yes (Cat A)** | **FIXED** |
| Factor terminology | Two real DB fields (`factor_source`, `factor_set`) | None (faithful) | **No** | n/a | Keep; documented |
| Evidence control | Native `<details>/<summary>`; DR-004 harness matched only button/a | None | **No** | n/a | Keep; harness corrected |
| Currency/Amount | Editable extraction-form inputs; absent on this document | Slight (empty disabled fields) | **No** (UX observation) | No (touches extraction display) | PO/UX decision |
| Document detail | No `/documents/:id` route | Investors cannot open a document page | **Missing capability** | No (Part D) | `PO DECISION REQUIRED` |
| Duplicate annual reports | New row per generation + stale pre-R-A row | Two same-titled reports, one empty | **Not a code defect** (stale demo data) | No (no deletion in scope) | `PO DECISION REQUIRED` |
| ghg_inventory | Legacy row; type unsupported by the API and unreferenced in code | An un-refreshable report is visible | **Not a product defect** (stale data) | No | `PO DECISION REQUIRED` |

## 4. Fixes actually applied (Phase 2 — Category A only)

| # | File | Change |
| --- | --- | --- |
| 1 | `frontend/src/v3/customer/DocumentsPage.jsx` | "Uploaded" column reads **`uploaded_at`** (with `created_at` fallback) for rendering and sorting; comment records the backend origin of the field |
| 2 | `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` | Calculation panel resolves scope as `mapped_data?.scope` → **`evidence?.emissions?.[0]?.scope`** → `'-'`, so it shows the same `Scope 1` as the evidence pane |
| 3 | `frontend/src/v3/customer/ReviewDetailPage.jsx` | "Mapped activity" falls back to **`mapped_data?.activity`** when `activity_type` is absent |

No backend, schema, RLS, storage, factor, extraction, calculation, matching, report-engine or evidence-schema change; no Demo Lab data added, altered or removed.

## 5. Files changed

| File | Status |
| --- | --- |
| `frontend/src/v3/customer/DocumentsPage.jsx` | modified (+comment, field mapping) |
| `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` | modified (+comment, scope fallback) |
| `frontend/src/v3/customer/ReviewDetailPage.jsx` | modified (mapped-activity fallback) |
| `frontend/src/v3/__tests__/dr007-investor-display-fixes.test.jsx` | **new** — narrow regressions for issues 2 and 3 |
| `docs/demo-investor/DR-007-investor-defect-triage-and-remediation.md` | **new** — this report |

## 6. Tests performed

1. **New regressions written**: (a) the workspace Calculation panel renders `Scope 1` from an emissions row shaped like the real R-A payload, `Scope - · Methodology` no longer appears, and `2469.16978 kg CO2e` still renders; (b) the review detail renders `Mapped activity … Natural gas` from `mapped_data.activity`.
2. **Targeted run attempted**: `CI=true npx react-scripts test --watchAll=false --testPathPattern=dr007-investor-display-fixes` → suite could not start: jest/jsdom fails loading the native `canvas` binding (`Cannot find module '../build/Release/canvas.node'`).
3. **Confirmed pre-existing**: the *existing* `evidence-trail.test.jsx` fails identically → the frontend runner is broken in this workspace independently of DR-007. `LIMITATION`: the new tests are ready for CI but were not executable here.
4. **Compile check**: the running CRA dev server recompiled the three edited modules → `webpack compiled with 1 warning` (the pre-existing `useEffect` exhaustive-deps warning in `ReviewDetailPage`); **no compile errors**.
5. **Browser verification** (§7) — the strongest available evidence in this environment.

## 7. Browser re-verification (Part G)

Real login (`org_a_owner`), post-fix, zero console errors:

| Surface | Observation | Issue |
| --- | --- | --- |
| Documents | `Uploaded` now shows real timestamps, e.g. R-A document `2026-09-20T17:32:20.713747+00:00`, others `15:37:45`, `15:37:42`, `15:37:39` (previously `—` for all) | 1 — **VERIFIED** |
| R-A workspace `/processing/2b41b332-…` | `Calculated result · 2469.16978 kg CO2e · **Scope Scope 1** · Methodology selection_policy`; `Scope -` absent; evidence pane still `2025-05-05 · Scope Scope 1 · Snapshot af640887-…`; evidence trail Source document / Extraction / Mapping / Validation / Calculation all `COMPLETE` | 2 — **VERIFIED** |
| Review detail `/review/<id>` | `Status CALCULATED · Extracted activity Natural gas · Quantity 12181.4 kWh · **Mapped activity Natural gas** · Emission factor b9d1ed06-… · Calculated 2469.16978`; Approve/Reject/Close untouched | 3 — **VERIFIED** |
| Reports | `READY 3`; regenerated annual report present (Sep 21, 2026, 03:59 AM) and superseded rows preserved — unchanged by DR-007 | 8 — behaviour unchanged |

Screenshots: `/tmp/dr007_shots/{a_documents,b_workspace,c_evidence,d_review,e_reports}.png`; log `/tmp/dr007_out.txt`.

## 8. R-A integrity check (Part E)

Unchanged and re-observed post-fix: result **2469.16978 kg CO2e** (workspace + review), scope **Scope 1**, snapshot **af640887-5818-47ad-b351-1505ac049c32**, factor **b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5**, activity **Natural gas**, quantity **12181.4 kWh**. The underlying payload JSON is identical pre- and post-fix — only rendering changed. Emissions log `eb88e764-…` unchanged (verified in DR-005/006 export reads). No recalculation, remapping, extraction change or approval occurred.

## 9. Unresolved issues

1. Duplicate "Annual emissions report 2025" rows (one `insufficient_data`) — retained deliberately; resolution requires deleting/annotating demo data or changing report-creation architecture (out of scope).
2. `ghg_inventory 2025` remains `insufficient_data` and un-refreshable through the API.
3. Extraction `Currency`/`Amount` empty disabled inputs remain (intentional form behaviour; UX change deferred).
4. No customer document-detail/preview page (missing capability).
5. Frontend jest runner cannot start in this workspace (`canvas.node`) — pre-existing environment limitation affecting all frontend tests.

## 10. PO decisions required

1. Whether to remove/annotate the stale pre-R-A annual report and the legacy `ghg_inventory` row in the Demo Lab (a demo-data change).
2. Whether a customer document-detail/preview capability is required.
3. Whether the extraction form should hide empty locked fields (`Currency`/`Amount`).
4. Whether the reports list should label superseded reports (e.g. a "superseded" badge) instead of showing two identical titles.
5. Whether to repair the frontend jest environment (`canvas`) so DR-007's regressions can run in CI.

## 11. Explicit out-of-scope items

Not implemented (Part D): new document-detail functionality; `ghg_inventory` generation; report-engine/version-architecture changes; calculation, extraction or matching changes; provenance/evidence-schema changes; approval execution; billing/payment integration; Realtime gateway changes; new Demo Lab data; schema/RLS/security changes.

## 12. Final bounded verdict

Nine issues were triaged using code, runtime, database and browser evidence. **Three** were genuine, investor-facing display defects (documents `Uploaded` mapped to the wrong field; workspace scope read from a path the backend does not populate; review "Mapped activity" read from the wrong key). All three were fixed with minimal frontend-only changes, compiled cleanly, and **browser-verified** — the Uploaded column now shows real timestamps, the workspace shows `Scope 1`, and the review detail shows `Mapped activity Natural gas`, with the R-A result, scope, snapshot and factor ids unchanged. Three issues were established as **not defects** (factor source/set are two real DB fields; the evidence "technical details" control is a working native disclosure; empty Currency/Amount are editable-form inputs). Three issues require **PO decisions** and were left untouched (missing document-detail capability; duplicate/stale annual report; legacy `ghg_inventory`). No backend, schema, security, calculation or data change was made, no report was regenerated or deleted, and nothing was approved. The regression tests written for the two rendering fixes could not be executed because the workspace's jest/jsdom environment cannot load `canvas` — a pre-existing limitation recorded above. CarbonTally is **not** declared investor-ready and this report asserts nothing beyond the evidence above.
