# DR-004 — Deep Browser Verification of the Existing R-A Customer Calculation Journey

- **Prompt ID:** `DR-004`
- **Timestamp:** 2026-09-20, ~21:2x–22:0x UTC (local session)
- **Nature:** strictly read-only browser verification. No feature was implemented, no fix applied, no data changed.

Evidence labels: `BROWSER-VERIFIED` · `RUNTIME-OBSERVED` · `DATABASE-OBSERVED` · `CODE-TRACED` · `INFERENCE` · `LIMITATION`.

---

## 1. Git baseline

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD | `8f9af42e62366bf93b9e8aa79f875406602ef5ee` (== DR-003, as required) |
| Working tree | clean (`git status --porcelain` empty) |
| Remote divergence | `0 0` vs `github/p8-release-reconciled` |

`RUNTIME-OBSERVED`

## 2. Browser environment

| Item | Value |
| --- | --- |
| Frontend | `http://localhost:3000` → HTTP 200 |
| Demo Lab backend | `http://127.0.0.1:8070` → HTTP 200 (`/health`) |
| Demo Lab gateway | `http://127.0.0.1:54430` → `/rest/v1/` HTTP 200 |
| Browser | `/usr/bin/google-chrome` headless `--headless=new`, 1440×900 |
| Driver | none installed; unchanged DR-003 CDP harness (Node 22 global `WebSocket`) |
| Harness files | `/tmp/dr004_browser.js`, `/tmp/dr004b.js` (outside the repository; **no tooling added to the repo**) |
| Evidence | screenshots `/tmp/dr004_shots/{c1_home,d1_emissions,j1_evidence,k1_review,k2_review_detail,e1_documents,e2_doc_detail,l1_processing,l2_item_workspace}.png`, log `/tmp/dr004_out.txt` |
| Demo Lab configuration | **not altered** during DR-004 |

## 3. Authentication evidence

Real UI login (no session seeding): `/login` rendered, `org_a_owner` credentials typed into the rendered form and submitted →
`login -> http://localhost:3000/home`; `session: {"keys":["sb-127-auth-token"],"hasAccessToken":true,"user":true}`.
Observed API traffic includes `GET http://127.0.0.1:54430/auth/v1/user -> 200` and `GET /api/v3/me/context -> 200` (organisation `3fd0f325-16a1-5b53-8fb8-27929cf218fa`, "Demo Lab Organisation A"). No user or organisation was created. `BROWSER-VERIFIED`

## 4. R-A identification evidence (Part D)

Found **through the UI** (queue → row click), not by URL construction:

| Item | Finding |
| --- | --- |
| Route before click | `/processing` → row `t3imp_uk-gas__ORG_022_british_gas_202511.pdf \| Uploads \| CALCULATED \| pdf \| 2469.16978` |
| Route after click | `http://localhost:3000/processing/2b41b332-98ef-4f99-9ea0-5d40d1da0a6c` (ProcessingItemPage → ProcessingItemWorkspace) |
| Component | `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` (`CODE-TRACED`) |
| Displayed status | `CALCULATED`, pipeline `Extract › Map › Validate › 4 Calculate › 5 Review › 6 Approve › 7 Evidence`, sub-label `Automatic processing — Awaiting review · attempt 0/3 — CUSTOMER REVIEW` |
| Displayed result | `Calculated result 2469.16978 kg CO2e` |
| Snapshot id in UI | `af640887-5818-47ad-b351-1505ac049c32` (matches the known R-A snapshot exactly) |
| Emissions list row | `/emissions` → `2025-05-05 \| Natural gas \| Scope 1 \| 2469.16978` |
| Documents panel | "Emissions derived from t3imp_uk-gas__ORG_022_british_gas_202511.pdf" → `2025-05-05 \| … \| Scope 1 \| 2469.169780 \| af640887-5818-47ad-b351-1505ac049c32` |
| Review queue row | `/review` → `t3imp_uk-gas__ORG_022_british_gas_202511.pdf \| CALCULATED \| 2469.16978 \| Not yet` |

The displayed value matched `2469.169780 kg CO2e` in every surface; no unexpected value was observed (no stop condition triggered). `BROWSER-VERIFIED`

## 5. Organisation / context evidence

`/home`: `Demo Lab Organisation A · V3 customer workspace`, `READY REPORTS 2 · QUEUED REPORTS 0 · DOCUMENTS 9 · MEMBERS 4 · EMISSIONS ROWS 1 · TOTAL TCO₂E 2.47`, `Emissions 2.47 tCO₂e (1 rows) · Scope 1: 2.47 tCO₂e · Latest month: 2025-05`, `Documents Total 9 · Processed 0 · Pending 0`, `Processing 9 items · 0% complete · Mapped 0 · Unmapped 9`, `source: 1 · extraction: 1 · calculation: 1`. `BROWSER-VERIFIED`

## 6. Document-detail findings (Part E)

- `CODE-TRACED`: the router (`frontend/src/App.js`) has **no `/documents/:id` route**; `DocumentsPage` is the only documents surface.
- Clicking the R-A row (`t3imp_uk-gas__ORG_022_british_gas_202511.pdf | PDF | 199.6 KB | —`) did **not** navigate; it expanded an inline panel on the same page: **"Emissions derived from t3imp_uk-gas__ORG_022_british_gas_202511.pdf"** with `PERIOD | ACTIVITY | SCOPE | KG CO₂E | SNAPSHOT` = `2025-05-05 | …pdf | Scope 1 | 2469.169780 | af640887-5818-47ad-b351-1505ac049c32`. `BROWSER-VERIFIED`
- Visible metadata: filename, type `PDF`, size `199.6 KB`; page header "Upload and browse org documents (Supabase Storage via the V3 API)"; upload control with data-type selector (`Utility | Fuel | Scope 3 | Other`); "Upload batches (0) — No upload batches yet."
- Document status / processing status are **not** shown in this surface (no status column, no detail page).
- **Discrepancy:** the `Uploaded` column renders **"—" for all 9 documents**, including the R-A document — no upload timestamp is displayed anywhere on this surface. `BROWSER-VERIFIED`
- No customer document preview/view existed to open; the only source-document access is the evidence drawer's `Open source document` (not opened — it issues a signed URL). `NOT FOUND` (customer preview) + `INFERENCE`

## 7. Extraction findings (Part F)

Workspace `/processing/2b41b332-98ef-4f99-9ea0-5d40d1da0a6c` → "Extraction" panel:

- Note: *"Extraction is locked once the item leaves the extraction stage."* The panel renders the field labels `Supplier | Invoice number | Invoice date | Currency | Activity | Quantity | Unit | Amount`.
- The extracted values appear in the same workspace's **"Emissions & evidence"** panel as structured JSON (`extracted_data`):

```
"date": "05/05/2025", "unit": "kWh", "activity": "Natural gas",
"quantity": 12181.4, "supplier": "Clear Power PLC", "invoice_number": "GRN/2027/6987"
```

- Review detail (`/review/<id>`) shows `Extracted activity Natural gas`, `Quantity 12181.4 kWh`.

All five fields named in the prompt (activity `Natural gas`, quantity `12181.4`, unit `kWh`, date `05/05/2025`, supplier `Clear Power PLC`) are displayed and match the known backend state. `BROWSER-VERIFIED`

## 8. Manual-correction history findings (Part G)

- The supplier value **is** visible: evidence drawer → `ORIGINAL SOURCE DATA — FROM THE DOCUMENT` → `Supplier | Clear Power PLC`, with `Invoice / reference | GRN/2027/6987` and `Document date | 05/05/2025`.
- Workspace Validation panel: `No validation findings recorded yet.`
- **No explicit manual-correction/audit entry was observed** in any inspected surface (no "corrected by", actor or timestamp for the supplier field). The drawer's unopened control labelled `Technical details / Evidence record` (§12) is the only plausible location for such a trail.
- Classification: **PARTIALLY VERIFIED** — the corrected value and its document context are displayed; an explicit *human-confirmation* provenance statement was **NOT FOUND** in the rendered UI. `BROWSER-VERIFIED` + `LIMITATION`

## 9. Factor-match findings (Part H)

Evidence drawer → `EMISSION FACTOR — CARBONTALLY`:

| Field | Displayed value |
| --- | --- |
| Factor | `Fuels > Gaseous fuels > Natural gas (kg CO2e) [kWh (Net CV)]` |
| Source | `DEFRA-DESNZ` |
| Set | `DEFRA-2025` |
| Value | `0.2027 kWh (Net CV)` |
| Reporting year | `2025` |
| MAPPING section | Mapped activity `Natural gas`; Activity type `Natural gas` |

The workspace/review structured data exposes the factor record id and match mechanics: `"factor_id": "b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5"`, `"factor_kind": "emission_factor"`, `"methodology": "selection_policy"`, `"source_ordinal": 1`, `"mapping_confidence": 1`, `"stages_executed": ["exact_match","natural_key","alias_match","keyword_search","fuzzy_match","calorific_basis","selection_policy"]`; review detail shows `Emission factor b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5`. `BROWSER-VERIFIED`
The factor UUID matches the expected R-A factor and the multiplier `0.2027` / set `DEFRA-2025` match expectations. The Mapping panel's factor picker is empty in this item's state: *"Load factor options — No factor options loaded yet."* (with an explanatory hint); nothing was selected or submitted. `BROWSER-VERIFIED`
Observation (not an error): the drawer labels **Source** `DEFRA-DESNZ` and **Set** `DEFRA-2025`, whereas the prompt names source `DEFRA-2025` / provider key `defra`; the provider *key* is internal and is not surfaced to the customer, which shows the dataset label instead. `RUNTIME-OBSERVED`

## 10. Calculation findings (Part I)

Evidence drawer → `CALCULATION — CARBONTALLY`:

```
12181.4 kWh (Net CV) × 0.2027 = 2469.169780 kg CO₂e     Methodology: direct_multiply   Algorithm version: v1.0
```

and `EMISSION RESULT — CARBONTALLY`: `kg CO₂e 2469.16978 | Scope 1 | Period 2025-05-05`.
Workspace Calculation panel: `Calculated result 2469.16978 kg CO2e`, `Scope - · Methodology selection_policy`.
`/emissions` history row: `2025-05-05 | Natural gas | Scope 1 | 2469.16978 | Fuels > Gaseous fuels > Natural gas (kg CO2e) [kWh (Net CV)]`.
The customer can therefore read quantity, unit, multiplier, result, scope, methodology, reporting year and status. Nothing was recalculated. `BROWSER-VERIFIED`
**Discrepancy (minor):** the workspace Calculation panel renders `Scope -` for the same item whose scope is `Scope 1` in the drawer, the emissions list and the review/evidence JSON. `BROWSER-VERIFIED`

## 11. Provenance findings

Visible chain: *document → extracted line (page 3) → mapped activity → factor (set/value/year) → calculation → emissions result*, with calculation **snapshot `af640887-5818-47ad-b351-1505ac049c32`** rendered in the workspace and the documents panel, and evidence status `COMPLETE`. `BROWSER-VERIFIED`
Not surfaced anywhere inspected: the **emissions-log id `eb88e764-b93a-4bd6-8b66-a24fd6e45ca9`** and the **R-A job id `d868e0d7-…`** (internal identifiers are not exposed to the customer). `NOT FOUND` in the UI — an observation, not classified as missing functionality. `LIMITATION`

## 12. Evidence-drawer findings (Part J)

`/emissions` → `View evidence` opened an **inline drawer** (no navigation, no data change), headed
**"Evidence — t3imp_uk-gas__ORG_022_british_gas_202511.pdf `COMPLETE`"**, summarised as *"Document + extracted line + source page + calculation + factor."*

Observed contents, in order: `Source document + line with location: document, page 3, extracted line` · `EMISSION RESULT … 2469.16978 · Scope 1 · Period 2025-05-05` · `CALCULATION … 12181.4 kWh (Net CV) × 0.2027 = 2469.169780 kg CO₂e · direct_multiply · v1.0` · `EMISSION FACTOR … DEFRA-DESNZ / DEFRA-2025 / 0.2027 kWh (Net CV) / 2025` · `MAPPING … Natural gas` · `ORIGINAL SOURCE DATA — FROM THE DOCUMENT … …pdf · GRN/2027/6987 · Clear Power PLC · 05/05/2025 · Extracted line Natural gas — 12181.4 kWh`. Actions: `Open source document`, `Technical details / Evidence record`. `BROWSER-VERIFIED`
**Absent from the rendered drawer** (recorded precisely, not interpreted as a product defect): hashes/checksums, extraction/calculation timestamps, an evidence-record identifier, an actor/audit trail for the manual supplier correction, and the emissions-log id. The `Technical details / Evidence record` control **could not be opened** in this pass — it is not exposed as a `button`/`a` element (text-matched click returned `NOT FOUND`); its contents remain `IMPLEMENTED — NOT VERIFIED`. `BROWSER-VERIFIED` + `LIMITATION`
No evidence was created, modified or approved; console errors across both runs: **none**. `RUNTIME-OBSERVED`

## 13. Review findings (Part K)

- `/review` queue: *"Items awaiting customer verification. Review shows the full evidence chain; approval is the distinct final gate (D5)."* → row `t3imp_uk-gas__ORG_022_british_gas_202511.pdf | CALCULATED | 2469.16978 | Reviewed: Not yet`.
- Row click → `/review/<id>` "Review item": `Status CALCULATED`, `Extracted activity Natural gas`, `Quantity 12181.4 kWh`, `Mapped activity —`, `Emission factor b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5`, `Calculated (kg CO₂e) 2469.16978`, `Notes (optional)`, and controls **`Approve` / `Reject` / `Close`** — **none clicked**. `BROWSER-VERIFIED`
- Approval state **unchanged** (`Reviewed: Not yet`); no rejection or change request performed.
- **Discrepancy (minor):** `Mapped activity` renders as `—` on the review detail page while the drawer/workspace map the activity to `Natural gas`. `BROWSER-VERIFIED`

## 14. Exception-journey findings (Part L)

`/processing` → **"Waiting for review (8)"**: *"Automatic processing stopped on these documents because it could not resolve every required field. Nothing has been discarded - open the item to complete the missing details and the pipeline will continue."*, with per-document reasons:

| Item | Displayed reason |
| --- | --- |
| `t3imp_uk-ambiguity__ORG_027_octopus_energy_202608.pdf` | `ambiguous, confidence=0.00` (`Electricity` kWh) |
| `t3imp_uk-water__ORG_030_thames_water_202605.pdf` | `no_match, confidence=0.00` (`Water` litres) |
| `t3imp_uk-waste__ORG_018_biffa_waste_202601.pdf` | `clarification required for 'Waste'` (treatment/material-handling vs combustion; families share no accounting meaning) |
| `t3imp_uk-diesel__ORG_029_certas_energy_202509.pdf` | `ambiguous` (`Diesel` tonnes) |
| `t3imp_uk-gas__ORG_018_british_gas_202605.pdf` | `no_match` (`Natural gas` kWh) |
| `t3imp_uk-electricity__ORG_027_octopus_energy_202510.pdf` | `ambiguous` (`Electricity` kWh) |
| `ohd079-invalid-probe.txt` | `extraction no_text: no usable text extracted` |
| `scope2_water_plus_commercial_invoice.pdf` | `extraction no_text: no usable text extracted` |

The customer therefore sees **what stopped, why, and the stated next step** ("open the item to complete the missing details and the pipeline will continue"). The R-A `…022…` gas item *did* resolve, so both outcomes are demonstrable side by side. `BROWSER-VERIFIED`
`LIMITATION`: an exception item's own workspace was **not** opened in this pass (the single row click landed on the R-A item, which was the §4–§12 priority); the exception item's internal panels and "Open workspace" controls therefore remain `PARTIALLY VERIFIED` (list-level only). No retry, confirmation or correction was performed on any item.

## 15. UI → API traces (Part M)

Captured from the browser's own network traffic (`Network` domain), not from assumptions. Calls go to the Demo Lab backend `http://localhost:8070` except auth, which goes to the gateway `http://127.0.0.1:54430`:

| UI surface / component | Endpoint observed | Status | Rendered result |
| --- | --- | --- | --- |
| Shell on every V3 page (`V3Layout`, `RoleRoute`) | `GET /api/v3/me/context` | 200 | org context "Demo Lab Organisation A"; role gating |
| Shell notifications | `GET /api/v3/notifications` | 200 | notification control |
| Auth session | `GET http://127.0.0.1:54430/auth/v1/user` | 200 | persisted session |
| `DashboardPage` (`/home`) | `GET /api/v3/organizations/<org>/members`, `GET /api/v3/documents`, `GET /api/v3/reporting/emissions-trend`, `GET /api/v3/reporting/member-activity`, `GET /api/v3/exports/emissions.json` | all 200 | 9 documents / 4 members / 2.47 tCO₂e, trend + tiles |
| `EmissionsPage` (`/emissions`) | `GET /api/v3/exports/emissions.json` + `OPTIONS` preflight | 200 | R-A row `2469.16978` + factor label |
| Evidence drawer (`openEvidence` → `components/EvidenceTrail.jsx`) | no new XHR observed — rendered from already-fetched page data | n/a | full evidence chain (§12) |
| `ReviewPage` (`/review`) | `GET /api/v3/processing/customer-review` | 200 | `CALCULATED / 2469.16978 / Not yet` |
| `ReviewDetailPage` (`/review/<id>`) | no new XHR observed (client-side render of loaded item) | n/a | Status / Extracted activity / Quantity / Factor / Calculated + Approve/Reject |
| `DocumentsPage` (`/documents`) | `GET /api/v3/documents`, `GET /api/v3/batches` | 200 | 9 documents + batches empty state |
| Documents inline panel (row click) | none — client-side render | n/a | "Emissions derived from …" → Scope 1 / `2469.169780` / snapshot `af640887…` |
| `ProcessingPage` (`/processing`) | `GET /api/v3/processing/status`, `GET /api/v3/processing/jobs`, `GET /api/v3/manual-extraction/batches` | 200 | queue incl. "Waiting for review (8)" + reasons |
| `ProcessingItemWorkspace` (`/processing/<item>`) | rendered from the loaded item payload | n/a | pipeline + Extraction/Mapping/Validation/Calculation + `extracted_data`/`mapped_data` JSON + snapshot id |
| Exception reasons (§14) | produced by `GET /api/v3/processing/jobs` | 200 | `no_match` / `ambiguous` / `clarification required` / `extraction no_text` |

**Conclusion:** every inspected surface rendered data obtained from live CarbonTally backend endpoints (`/api/v3/...` on the Demo Lab FastAPI) carrying the R-A values; **no static/demo strings were observed**. `RUNTIME-OBSERVED`
Read-only server-side cross-check: `/api/v3/me/context` → 200 and `/api/v3/processing/customer-review` → 200 (the same endpoints the UI uses); two *guessed* endpoint names (`/api/v3/processing/items/<id>`, `/api/v3/emissions/records`) returned 404/422, which is evidence of a wrong guess, **not** of absence. `RUNTIME-OBSERVED` + `INFERENCE`

## 16. Verification matrix (Part O)

| Journey element | Browser result | Backend consistency | UI completeness | Evidence | Status |
| --- | --- | --- | --- | --- | --- |
| Document detail | Row click opens an inline "Emissions derived from …" panel; no detail route exists | `Scope 1`, `2469.169780`, snapshot `af640887…` match | Name/type/size + derived emissions; **no status, no preview, `Uploaded` = "—"** | §6; `e1_documents.png`, `e2_doc_detail.png` | **PARTIALLY VERIFIED** |
| Extraction | Extraction panel (locked) + full `extracted_data` JSON | activity/quantity/unit/date/supplier match backend | Complete for the 5 key fields; currency/amount render as labels only | §7; `l2_item_workspace.png` | **BROWSER VERIFIED** |
| Manual correction history | Supplier value + document context shown | `Clear Power PLC` matches | No "manually corrected/confirmed by" audit statement | §8 | **PARTIALLY VERIFIED** |
| Factor match | Factor, source, set, value, year in drawer; `factor_id`, methodology, 7 stages, confidence 1 in JSON | `b9d1ed06-…`, `0.2027`, `DEFRA-2025` match expectations | Strong; provider key not surfaced (dataset label shown) | §9 | **BROWSER VERIFIED** |
| Calculation | Drawer formula + result; workspace result; emissions row | `12181.4 × 0.2027 = 2469.169780` matches | Complete; workspace shows `Scope -` (minor inconsistency) | §10 | **BROWSER VERIFIED** |
| Provenance | Snapshot id + full chain visible | snapshot `af640887…` matches the known R-A snapshot | Job id / emissions-log id not surfaced | §11 | **PARTIALLY VERIFIED** |
| Evidence drawer | Opens read-only; rich chain; status `COMPLETE` | page 3, invoice `GRN/2027/6987`, supplier, factor all match | No hashes/timestamps; `Technical details / Evidence record` not openable by click | §12; `j1_evidence.png` | **PARTIALLY VERIFIED** |
| Review | Queue + review item page with Approve/Reject (untouched) | `CALCULATED`, `2469.16978`, `Not yet` match | Controls present; `Mapped activity —` blank | §13; `k2_review_detail.png` | **BROWSER VERIFIED** |
| Exception/manual review | 8 blocked items with reasons + next-step guidance | reasons consistent with prior server-side evidence | List-level only; item workspace not opened | §14; `l1_processing.png` | **PARTIALLY VERIFIED** |
| Customer document preview | — | — | No such surface found | §6 | **NOT FOUND** |
| `Technical details / Evidence record` | Not openable in this pass | — | — | §12 | **IMPLEMENTED — NOT VERIFIED** |
| Approval / rejection | Controls exist, deliberately untouched | State unchanged (`Not yet`) | — | §13 | **NOT YET AUTHORIZED** |

## 17. Investor-demo factual answers (Part P)

- **Q1 — Can an investor see a real uploaded document?** **Yes, indirectly.** `/documents` lists 9 real Demo Lab documents with name/type/size; the R-A document `t3imp_uk-gas__ORG_022_british_gas_202511.pdf` (199.6 KB) is listed and clickable, and clicking it renders its derived emissions. There is **no document-detail page and no in-app preview**; the raw file is only reachable via the evidence drawer's `Open source document` (not opened). `BROWSER-VERIFIED`
- **Q2 — Can an investor see the extracted information?** **Yes.** Workspace `extracted_data`: `date 05/05/2025, unit kWh, activity Natural gas, quantity 12181.4, supplier Clear Power PLC, invoice_number GRN/2027/6987`; the review detail repeats `Extracted activity Natural gas` / `Quantity 12181.4 kWh`. `BROWSER-VERIFIED`
- **Q3 — Can an investor see how the factor was selected?** **Yes.** Drawer: factor name, `Source DEFRA-DESNZ`, `Set DEFRA-2025`, `Value 0.2027`, `Reporting year 2025`; workspace/review JSON: `factor_id b9d1ed06-…`, `methodology selection_policy`, 7 `stages_executed`, `mapping_confidence 1`. The internal provider key is not shown. `BROWSER-VERIFIED`
- **Q4 — Can an investor see the actual calculation?** **Yes.** `12181.4 kWh (Net CV) × 0.2027 = 2469.169780 kg CO₂e`, methodology `direct_multiply`, algorithm `v1.0`; the same result appears in the emissions history, the workspace and the review item. `BROWSER-VERIFIED`
- **Q5 — Can an investor trace the result back to evidence/provenance?** **Yes, substantially.** The drawer self-labels `COMPLETE` and chains document (page 3) → extracted line → mapping → factor → calculation → emissions; the calculation snapshot `af640887-…` is displayed. Hashes, timestamps and the actor trail for the manual supplier correction are **not** visible. `BROWSER-VERIFIED` (partial)
- **Q6 — Can an investor see that the item awaits review?** **Yes.** `/review` shows `CALCULATED` / `Reviewed: Not yet`; the workspace shows `CUSTOMER REVIEW` / `Awaiting review · attempt 0/3`; the review item page offers `Approve` / `Reject` (untouched). `BROWSER-VERIFIED`
- **Q7 — Can an investor see how CarbonTally handles a blocked/ambiguous item?** **Yes.** `/processing` "Waiting for review (8)" lists each stopped document with its machine-generated reason (`no_match`, `ambiguous`, `clarification required for 'Waste'`, `extraction no_text`), states that nothing was discarded, and tells the customer how to continue; the R-A `…022…` gas item *did* resolve, so both outcomes are visible side by side. `BROWSER-VERIFIED`

## 18. Discrepancies

1. **Documents `Uploaded` column is empty ("—") for all 9 documents** — no upload timestamp displayed anywhere in that surface. `BROWSER-VERIFIED`
2. **Workspace Calculation panel shows `Scope -`** while every other surface shows `Scope 1` for the same item. `BROWSER-VERIFIED`
3. **Review detail `Mapped activity` shows `—`** while the drawer/workspace show `Natural gas`. `BROWSER-VERIFIED`
4. **Factor "Source" reads `DEFRA-DESNZ`** while the factor *set* is `DEFRA-2025` and the internal provider key is `defra` — a labelling difference in what the customer sees, not a data mismatch. `RUNTIME-OBSERVED`
5. **The evidence drawer exposes no hashes, timestamps or audit identifiers**, and `Technical details / Evidence record` could not be opened by a text-matched click because it is not a `button`/`a`; whether that panel holds them is unverified. `BROWSER-VERIFIED` + `LIMITATION`
6. **Extraction panel renders `Currency` / `Amount` labels without values**, and neither key exists in `extracted_data` — an empty-label presentation, recorded as an observation. `BROWSER-VERIFIED`

## 19. Limitations

- Strictly read-only pass: **no** Approve / Reject / Retry / Confirm / Save / Upload / Export / Calculate / Generate control was clicked, so those paths remain `NOT YET AUTHORIZED`.
- An exception item's own workspace was not opened (§14).
- `Open source document` (signed-URL preview path) was not clicked → `IMPLEMENTED — NOT VERIFIED`.
- The drawer's technical/audit sub-panel could not be opened (§12).
- Backend cross-checks were limited to endpoints the UI itself used; two guessed endpoint names returned 404/422 (wrong guesses, not evidence of absence).
- Realtime/messaging remains blocked by the missing lab `/realtime/v1/` route (DR-003 carry-over); not re-tested here.

## 20. Remaining blockers

1. No customer-facing **document detail / preview** surface (only an inline "Emissions derived from …" panel).
2. `Uploaded` metadata is not rendered anywhere.
3. No visible **correction/audit history** (actor + timestamp) for the human-confirmed supplier.
4. The evidence drawer's **technical/audit record** is not reachable via a customer-visible click target in this pass.
5. Realtime/messaging blocked at the lab gateway (DR-003 carry-over).

## 21. PO decisions required

1. Whether the **`Uploaded` column gap** and the **`Scope -` / `Mapped activity —`** display gaps should become triaged frontend defects (observed read-only here; no fix applied).
2. Whether a **customer document-detail / preview** surface is required (currently `NOT FOUND`) or the inline evidence panel is the intended design.
3. Whether **manual-correction provenance** (who confirmed the supplier, and when) must be customer-visible, and whether the evidence drawer should expose hashes/timestamps.
4. Whether the `Technical details / Evidence record` control should be reachable — it was not openable via a text-matched click in this pass and needs a code-level trace before any conclusion.
5. Whether to verify an **exception-item workspace** in a follow-up (one blocked item opened read-only).
6. Whether approval/rejection walkthroughs, export execution and report generation are now authorised (all were `NOT YET AUTHORIZED` here).

## 22. Data-mutation audit

| Action class | Occurred? |
| --- | --- |
| Upload / retry / confirm / correct / approve / reject / request changes / finalize | **No** |
| Recalculation / regenerate report / create export | **No** |
| Document, job or item deletion | **No** |
| Demo Lab reset / reseed / DB modification | **No** |
| Configuration change (Demo Lab, gateway, backend, frontend) | **No** |
| Observational writes | authentication session for an existing demo identity (inherent to real login; permitted by Part C) |
| Read-only interactions | 2 browser runs (9 route captures + 3 deeper captures), ~20 authenticated page views, 1 evidence drawer opened, 1 review detail opened, 0 signed URLs requested |
| Console errors | **none** in either run |

No supposedly read-only action mutated data; the Part N guarantee held throughout. `RUNTIME-OBSERVED` + `BROWSER-VERIFIED`

## 23. Final bounded verdict

The existing CarbonTally customer UI **does** expose the R-A calculation journey in depth, from live backend data. Through real browser authentication a customer reaches the R-A item (`…uk-gas__ORG_022…`, `CALCULATED`) and can read its extracted fields exactly as they exist in the backend (`Natural gas`, `12181.4 kWh`, `05/05/2025`, `Clear Power PLC`, `GRN/2027/6987`), see the matched factor (`b9d1ed06-…`, set `DEFRA-2025`, value `0.2027`), read the arithmetic (`12181.4 kWh (Net CV) × 0.2027 = 2469.169780 kg CO₂e`) with methodology and algorithm version, follow a `COMPLETE` evidence chain from the document (page 3, extracted line) to the emissions result, see the calculation snapshot `af640887-5818-47ad-b351-1505ac049c32`, and see the item awaiting customer review with untouched `Approve`/`Reject` controls. Blocked items are explained in the queue with machine-generated reasons and an explicit next step. Six concrete display discrepancies were recorded, and five areas (document preview, correction/audit history, evidence hashes/timestamps, the technical evidence record, and an exception-item workspace) are partially or not verified. Nothing was mutated; no application, tooling or configuration change was made. CarbonTally is **not** declared investor-ready and this report asserts nothing beyond the evidence above.
