# CarbonTally — Independent Functional / Product / UX Audit

**Report ID:** CT-PRODUCT-UX-FUNCTIONAL-AUDIT-20260824-001
**Type:** AUDIT / GAP ASSESSMENT — no application code, schema, migration, data or configuration was changed
**Auditor:** OpenHands (OHD), independent
**Environment:** local repo `/home/shomonrobie/carbon_tally`, branch `main`, committed HEAD `37b19d1` —
**but the audit was performed against the WORKING TREE**, which carries uncommitted changes on top of HEAD.
This matters and is stated explicitly in Section P.1.
**Backend runtime:** uvicorn on `localhost:8050` (live OpenAPI inspected) — serving the working tree
**Database:** local Supabase Postgres (service-role queries, read-only)
**Storage:** Supabase Storage, private bucket `documents`
**Latest DB evidence timestamp:** 2026-09-14 05:24 UTC (job `b6e15354`)
**Sandbox clock:** 2026-08-24 (clock skew vs. repository/DB activity — dates below are taken from the DB/git, not the sandbox clock)
**Phase context:** Phase 8 closed work is left untouched. Phase 8-X is treated as part of Phase 8. No Phase 9. B1/B2/B3/B4/D19/D21/N1/N3 were **not** reopened.

---

## A. Executive summary

Nine audit areas were traced through the real frontend, the live API contract, the live database, the processing worker and the existing documentation. Every finding below is anchored to a file/line, a live HTTP header, or a live row — not to inference.

The single most important conclusions:

1. **Automatic processing runs, and it works — but it is currently rejecting nearly everything.** The worker is real and started in the app lifespan. Of 40 durable jobs, 20 completed and were approved, 3 are waiting on customer review, 17 are blocked at a human gate, and **0 failed**. It is not "broken". However, **every one of the 4 jobs created after the 2026-09-11 release commit is blocked**, i.e. a 0 % completion rate on the most recent real documents.

2. **The exact failure point for "no emissions have been calculated from this document yet" is now pinned.** It is **not** a viewer/API/display bug. On the newest post-release document (`color_02_water.pdf`, 2026-09-14) the pipeline ran *ingest → extract*, computed an extraction completeness of **0.33** (threshold 0.50, "unresolved: quantity, unit"), and then **discarded the partial extraction** (`extracted_data` NULL, `mapped_data` NULL, `last_error` NULL). Mapping, validation and calculation never ran. Nothing existed to display, so the UI message was *correct*. The failure class is **"extraction result was thrown away"**, not "extraction was never invoked" and not "the UI does not expose it".

3. **A newly-discovered P0 emissions-correctness defect sits behind the completed jobs.** The factor matcher scores candidates on *query-token coverage only* and breaks ties *alphabetically*, so it confidently picks DEFRA's per-gas **component** rows and alphabetically-early junk rows. Proven by executing the real pipeline entry point and by a persisted snapshot: 12,500 kWh of UK electricity was mapped to `… Electricity: UK > kWh (kg CO2e of CH4 per unit)` = **0.0009**, recorded as **Scope 3**, calculated as **11.25 kg CO2e** (correct order of magnitude ≈ 2,588 kg), **passed validation with zero findings**, and was **approved**. This is worse than a missing feature — it is a silent, traceable, wrong number.

4. **The PDF viewer defect has two independent causes, and only one is the content-type.** (a) The stored content type: sampled live, 12/12 PDF objects and all 228 `organization_files` PDF rows now serve `application/pdf` with no `Content-Disposition` — the octet-stream leg is remediated for this dataset, but the helper explicitly never touches existing objects and the viewer still decides renderability from the *file name*, not the served MIME. (b) **The repeated open/download is a URL-instability bug**: a 10-second poll replaces `source.viewer_url` with a *freshly signed URL every time* (proven — two sign calls 2 s apart produce different `iat`/`exp` claims), so the iframe `src` changes every 10 s and re-navigates, re-triggering the download each cycle.

5. **Batch upload is not a UI defect.** The multi-file UI exists but is orphaned in the legacy shell; the legacy multi-file endpoint is **deliberately hard-disabled** behind a hard-coded "premium feature" refusal; the V3 API accepts exactly one file; and the batch data model — which does exist, with a working repository and API — is **not wired to the live upload path** (all 40 processing jobs have `batch_id` NULL; one auto-created batch named "Uploads" declares `total_documents = 1` while holding **47** items).

6. **Automatic PE assignment has no rule engine and no persistence.** Batch/work-item assignment is well built (single-party, active-entity validated, audited) but is entirely manual and per-item/per-batch. There is no `organisation → PE`, `consultant → PE` or `client → PE` record anywhere in the schema. The only "auto assign" artefact is a single global boolean inside one `queue_settings` row. No notification is created when work is assigned to a PE.

7. **"Load Factor" is a button, not a factor.** It is `Load factor options` in the processing workspace, and it is empty precisely because extraction produced no `activity` — i.e. it is a **symptom of finding #2**, not an emission-factor gap. The UI already explains the genuinely-empty cases honestly.

8. **The vertical-text CSS defect is a cross-stylesheet cascade leak, proven in the built bundle.** A page-scoped `reports.css` rule globally overrides the shared `.v3-meta-list` layout into a ≥200 px grid; combined with a hard `width:190px` label and `min-width:0` on the value, the value element computes to ~0 px and breaks character-by-character. It is a **shared-component defect affecting 14 call sites**, not one screen.

9. **The admin table issue is systemic, and "10 rows per page" is already the codebase convention.** `DataTable` has shipped with `defaultPageSize = 10` and page sizes `[10, 25, 50, 100]`; 18 pages adopt it, **22 hand-roll `<table>`**, including the observed `CommercialTab`.

**Nothing in this report was implemented. No repository file other than this report was created or modified.**

---

## B. Critical blockers

| ID | Severity | Blocker |
|----|----------|---------|
| **A4-1** | **P0** | Automatic pipeline discards partial extraction and blocks; 100 % of post-release documents blocked. No document reaches emissions. |
| **A4-2** | **P0** | Factor matcher auto-matches wrong DEFRA **component** rows at `confidence 1.00`, passes validation, and is approved → silently wrong CO₂e and wrong Scope. |
| **A2-2** | **P1** | Processing-workspace viewer re-navigates every 10 s because the signed URL changes on every poll → repeated external opens/downloads. |
| **A4-3** | **P1** | 17/40 jobs parked at `blocked` with `attempt_count = 0` and no operator-facing recovery path in evidence. |
| **A1-2** | **P1** | Batch upload hard-disabled in code (`premium_feature`) and absent from the V3 API and the V3 UI. |

No P0 security/authorization blocker was found in the areas audited. RLS, signed-URL-only document access, and the Viewer read-only gate are intact in the paths inspected.

---

## C. Confirmed bugs

**BUG-01 — Extraction product discarded by the completeness gate (Area 4)** `P0 · BUG · DATA/PROVENANCE`
- **User-visible symptom:** "No emissions have been calculated from this document yet." plus `{"extracted_data": {}, "mapped_data": {}, …all null}`.
- **Expected:** a document that was read successfully enough to identify `activity` should persist what was found and ask a human only for the missing fields.
- **Actual:** the pipeline runs ingest + extract, computes `completeness = 0.33`, and persists **nothing** (`extracted_data` NULL, `mapped_data` NULL, `last_error` NULL, `attempt_count` 0) before blocking.
- **Root cause:** the extraction gate treats a sub-threshold `_completeness` as a hard human gate and does not persist the partial extraction payload; the job row is the only evidence of what was found, and it is written as an empty object.
- **Evidence:** job `b6e15354-b064-46d4-a549-457b8f489f07` (`color_02_water.pdf`, created 2026-09-14 05:23:49) and `e7db7f32-090c-41d4-b015-3e6b41d3f83d` (`border_double_fuel.pdf`, 2026-09-12): `stage='blocked'`, `status='manual_review'`, `manual_review_reason='extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit'`, extracted/mapped NULL.
- **Frontend:** `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` (data pane), `frontend/src/v3/components/EvidenceRecordPanel.jsx`.
- **Backend:** `backend/services/automatic_processing.py` (`_extract`, blocked-gate re-entry), `backend/services/automatic_extraction.py` (`_completeness`), `backend/domain/automatic_processing.py:98-110`.
- **DB:** `document_processing_queue` (stage/status/manual_review_reason/extracted_data), `manual_extraction_items`.
- **Reusable:** the frontend line-item editor (`ExtractionPanel.jsx`, `ProcessingItemWorkspace.jsx`) and `POST /api/v3/ops/items/…/extract` already accept free-form `extracted_data` — the human contract for partial data exists.
- **Partial implementation:** yes — the pipeline and the gate exist and work; only the persistence-on-block behaviour is wrong.
- **Recommended direction:** persist the partial extraction on the item/job before blocking (and show it pre-filled in the workspace) so a human completes rather than retypes. Do **not** lower the threshold without a PO decision.
- **Dependencies:** `_completeness` scoring; manual-review UX; A4-3.
- **PO decision required:** yes for the threshold value and for whether partial auto-acceptance is ever allowed.
- **Regression risk:** medium (extraction gate is shared by PDF/IMAGE/CSV/XLSX).

**BUG-02 — Wrong factor matched at full confidence (Area 4/5)** `P0 · BUG · DATA/PROVENANCE`
- **User-visible symptom:** plausible-looking emissions figures and Scope labels that are wrong by 1–2 orders of magnitude, with no warning.
- **Expected:** the total (`kg CO2e`) factor for the activity/unit/scope, or `no_match`.
- **Actual:** `Managed assets- electricity > Electricity generated > Electricity: UK > kWh (kg CO2e of CH4 per unit)` = **0.0009**, Scope 3, chosen for UK grid electricity; and `Bioenergy > Biofuel > Development diesel` = **0.03705** chosen for GB diesel (correct total rows present: 0.177 / 2.66155).
- **Root cause:** `FactorSearchIndex.keyword_search` scores `overlap / len(query_tokens)` — for `"Diesel"` the token set is `{"diesel"}`, so *every* factor containing "diesel" scores a perfect **1.00**; ties break on `activity_type.casefold()` ascending, so alphabetically-early rows (`Bioenergy…`, `Managed assets…`) beat the canonical `Fuels…` / `UK electricity…` rows. `KeywordSearchStage` requests `limit=1` and accepts at `>= 0.80`. The DEFRA import stores per-gas breakdown rows (`kg CO2e of CH4 / CO2 / N2O per unit`) alongside totals with no discriminator column.
- **Evidence (live, executed through the real entry point `engines.factor_matching.build_matching_pipeline`):** GB/2025/`Electricity`/`kWh` → `status=matched conf=1.00` `mult=0.0009`; GB/2025/`Diesel`/`litres` → `status=matched conf=1.00` `mult=0.03705`. Persisted: job `e49b46b3-…`, snapshot `6297840f-…` → `quantity 12500 kWh`, `co2e_multiplier 0.0009`, `co2e_kg 11.25`, `scope Scope 3`, `methodology direct_multiply`, `validation_result {"status":"passed","findings":[]}`, job `status='approved'`.
- **Frontend:** mapping pickers (`ProcessingItemWorkspace.jsx`, `ExtractionPanel.jsx`) surface the same factors, so a human can also pick a wrong one.
- **Backend:** `backend/infra/search_index.py:132-177`, `backend/engines/matching_stages.py` (`ExactMatchStage`, `KeywordSearchStage`), `backend/engines/factor_matching.py:292`.
- **DB:** `emission_factors` (no component/total discriminator), `calculation_snapshots`, `emissions_logs`, `document_processing_queue`, `manual_extraction_items`.
- **Reusable:** `factor_aliases`, `customer_factors`, `MatchingPipelineConfig` (already has a confidence floor).
- **Partial:** yes — `confidence` and `stages_executed` are already recorded, so the review gate *could* have caught it; `AUTO_MAPPING_CONFIDENCE_MIN = 0.6` is simply defeated by the 1.00 score.
- **Recommended direction:** make the score penalise unmatched factor tokens and prefer total rows (e.g. penalise `of CH4/CO2/N2O per unit` qualifiers, require scope agreement, prefer `provider`/`factor_set` defaults); consider requesting more than `limit=1` and adjudicating.
- **Dependencies:** the DEFRA import's row semantics; A6/Area-5 factor-source governance.
- **PO decision required:** yes — what "the right factor" means (total vs. per-gas, Scope 1 vs 3 electricity, DEFRA vs SEAI default).
- **Regression risk:** high — the scoring function is the single entry to every calculation.

**BUG-03 — Viewer re-navigates every 10 s because the signed URL is regenerated (Area 2)** `P1 · BUG · UX/INTEGRATION`
- **Symptom:** while the workspace stays open, the same PDF is repeatedly downloaded/opened in additional browser windows.
- **Expected:** one render, stable until the user acts or the signature nears expiry.
- **Actual:** a new signed URL is issued on every workspace fetch and pushed straight into the iframe.
- **Root cause:** `ProcessingItemWorkspace.jsx:194-201` polls `getProcessingItemWorkspace` every 10 000 ms and `setWorkspace(w)` replaces the object; `sourceUrl={source.viewer_url}` (line ~891) where `viewer_url = signed.file_url` (`backend/api/v3_processing_workflow.py:1062`, `backend/api/v3_operations.py:1528`) is re-signed per request. Supabase signed tokens embed `iat`/`exp`, so the string changes every second.
- **Evidence:** two `POST /storage/v1/object/sign/…` calls 2 s apart → **tokens differ**; decoded claims `iat 1789369287/exp 1789372887` vs `iat 1789369289/exp 1789372889`. Aggravated because 162 of 240 items are `pending` (i.e. "in flight", so the poll runs continuously).
- **Frontend:** `frontend/src/v3/customer/ProcessingItemWorkspace.jsx`, `frontend/src/v3/components/workbench/WorkbenchShell.jsx:43`, `frontend/src/v3/components/workbench/SecureDocumentViewer.jsx:75-84`.
- **Backend:** the two `viewer_url` producers above; `backend/services/storage.py:57-71`.
- **Reusable:** `DataTable`-style memo patterns exist; no new component is needed.
- **Recommended direction (smallest correct):** keep a stable identity for the frame (key the iframe on the document id/path) and only replace the signed URL on explicit refresh or near expiry; alternatively memoise the signature per item for the poll window.
- **PO decision required:** no.
- **Regression risk:** low.

**BUG-04 — Viewer guesses renderability from the file name, not the served MIME (Area 2)** `P1 · BUG · INTEGRATION`
- **Symptom:** a `.pdf` opens/downloads externally instead of rendering in the left pane.
- **Root cause:** `detectKind(title, src)` (`SecureDocumentViewer.jsx:31-38`) classifies on the **name**; the browser classifies on the **response `Content-Type`**. `application/octet-stream` cannot be rendered inline, so the frame is built and then downloads. The P0-1 helper `_renderable_content_type` (`backend/api/v3_documents.py:188-205`) only repairs *new* uploads whose supplied type is generic and explicitly leaves existing objects untouched.
- **Evidence:** sampled 12 stored PDF objects → all `Content-Type: application/pdf`, no `Content-Disposition`; `organization_files.mime_type` = `application/pdf` for 228/228 PDFs. The signed-URL leg also returns `application/pdf`. So the octet-stream leg is currently **remediated for this dataset**, but the design mismatch remains for any object stored before/outside the fix.
- **Frontend:** `SecureDocumentViewer.jsx`; **Backend:** `v3_documents.py`; **Storage:** object metadata in bucket `documents`.
- **Recommended direction:** drive the viewer decision from the server-reported MIME (or a server-computed `renderable` boolean) rather than the file name; treat unrenderable content with the existing explicit placeholder instead of an iframe. Repairing historical object metadata is a separate, PO-approved data operation.
- **Dependencies:** BUG-03 (same component).
- **PO decision required:** yes for backfilling stored object content types.
- **Regression risk:** low-medium (viewer is shared by customer, ops, PE and review surfaces).

**BUG-05 — The processing job row never records its own calculation (Area 4)** `P1 · BUG · DATA/PROVENANCE`
- **Symptom:** surfaces that read the job/queue record show "no emissions" for jobs that did calculate.
- **Evidence:** of 20 `stage='completed'` jobs, **20/20 have `calculation_snapshot_id`**, but **0/20 have `calculated_emissions_kg_co2e`** and only **1/20 has `emission_factor_used`**. The paired `manual_extraction_items` row *is* denormalised (item `a1610bbb-…`: `calculated_emissions_kg_co2e = 11.25`, `emission_factor_used` set).
- **Root cause:** the automatic pipeline persists the immutable snapshot and the item denormalisation but never writes back to the job row's denormalised columns.
- **Backend:** `backend/services/automatic_processing.py` (calculate stage), `backend/data/processing.py`.
- **Recommended direction:** write the same denormalised values (or stop exposing the columns), so two records of the same job cannot disagree.
- **PO decision required:** no. **Regression risk:** low.

**BUG-06 — Two contradictory snapshots returned for one document (Area 4/5)** `P1 · BUG · DATA/PROVENANCE`
- **Symptom:** "Emissions derived from <doc>" lists multiple, conflicting CO₂e figures for the same source document.
- **Evidence:** D33 reverse lookup for `electricity_invoice.jpg` returns **two** rows — snapshot `62ff4299` (2 212.5 kg, 0.177, Scope 2, 2026-08-26) and snapshot `6297840f` (11.25 kg, 0.0009, Scope 3, 2026-08-29). 100 snapshots exist for 46 distinct `source_item_id`s (up to 4 per item); one pair shares both `source_item_id` **and** `content_hash` (true duplicate).
- **Expected (AGENTS.md §19/§17):** repeated processing must not create duplicate snapshots; history is preserved but the *current* result must be unambiguous.
- **Root cause:** re-calculation writes a new snapshot without superseding/deprecating the previous one, and the reverse lookup returns all of them with no "current" marker.
- **DB:** `calculation_snapshots` (`request_id`, `content_hash`, `calculated_at`), `emissions_logs.snapshot_id`.
- **Recommended direction:** mark superseded snapshots (or expose a canonical/current pointer) and have the reverse lookup return the current result plus history.
- **PO decision required:** yes — how superseded emissions results should be presented. **Regression risk:** medium.

**BUG-07 — "Uploads" batch instance declares fabricated counts (Area 1)** `P2 · BUG · DATA/PROVENANCE`
- **Evidence:** `manual_extraction_batches` id `c743b982-…` `batch_name = 'Uploads'`, `total_documents = 1`, `total_pages = 1`, **actual items = 47**. Other "Uploads" rows declare 4 while holding 4–8.
- **Root cause:** `create_document_and_enqueue` creates the batch once with hard-coded `total_documents=1, total_pages=1` and never increments on subsequent item creation.
- **Backend:** `backend/api/v3_documents.py` (`create_document_and_enqueue`).
- **Recommended direction:** derive batch counts by aggregation, or maintain them on insert.
- **PO decision required:** no. **Regression risk:** low.

**OBS-01 — Automatic path records a page *count* as `source_page`** `P2 · OBSERVATION · DATA/PROVENANCE`
- Directly observed in the working tree: `backend/services/automatic_processing.py` builds the calculation request with `source_page=job.metadata.get("page_count")` — i.e. a **document page count** (e.g. `1`, `3`) is written into the snapshot's `source_page`, which every consumer treats as a **page number**. For a multi-page document this asserts a page that does not exist, and it is not a true provenance coordinate.
- Corroborated on real data: the electricity snapshot records `source_page = 1` for a document whose `page_count` is 1 (correct by coincidence); the defect only becomes visible on multi-page PDFs.
- This is noted for completeness only. It belongs to the pre-existing B2-D4 provenance/evidence workstream (**explicitly not reopened here**) and is **not** included in the recommended priority order. It is recorded so the evidence is not lost.


---

## D. Missing capabilities

**MISS-01 — Multi-file (batch) upload (Area 1)** `P1 · MISSING CAPABILITY`
- **UI:** the only V3 file input is `frontend/src/v3/customer/DocumentsPage.jsx:177` — `<input type="file" onChange={(e)=>setFile(e.target.files[0] || null)} />`, **no `multiple` attribute**; `ProcessingPage.jsx:293` is also single-file (`accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx"`).
- **The multi-file UI exists but is orphaned:** `frontend/src/BulkUpload.jsx` has `multiple` (lines 393-394) and `files.forEach` (line 116), but it is mounted only inside the legacy `Dashboard` component (`App.js:502`, rendered at `App.js:1829`), and no route in the live route table (`App.js:2000-2250`) reaches `Dashboard`. The legacy multi-file backend is deliberately disabled — see MISS-02.
- **API:** V3 has no multi-file endpoint. `POST /api/v3/documents/uploads` (`v3_documents.py:208-214`) takes a single `file: UploadFile = File(...)`. Batch *metadata* endpoints exist (`POST/GET /api/v3/documents/batches`) but nothing accepts `N` files, and no upload path calls them.
- **Maximum batch size:** none documented and none enforced in V3. The only enforced limit is the legacy hard-coded `"limit": 1`. **No size or SLA should be assumed.**
- **Partial failures:** not implemented on the live path (the only multi-file endpoint returns before doing work).
- **Per-document status and lineage:** **already correct** — each upload creates its own `organization_files` row, its own `manual_extraction_items` row (`file_id` link, D33) and its own `document_processing_queue` job. 264 items, 0 without a batch id.
- **Exact reason for absence (verified):** `backend/routes/upload.py:273-296` — `POST /upload-batch` declares `files: List[UploadFile] = File(...)` and then immediately returns a hard-coded, customer-level refusal:
  ```python
  return {"status": "premium_feature",
          "message": "Bulk upload is a premium feature. Please upgrade to access this functionality.",
          "feature": "bulk_upload", "limit": 1, "action": "upgrade_required"}
  ```
  Nothing is stored; the surrounding `try/except` is unreachable.
- **Verdict:** **NOT merely a UI defect.** It is a deliberate product gate plus a V3 intake gap, layered on top of a batch data model that already exists and holds real data.
- **Reusable:** `upload_batches` (+ `UploadBatchesRepository`, `total_files/processed_files/status/error_count/entity_id`), `manual_extraction_batches`, `document_processing_queue.batch_id`, `POST /api/v3/ops/batches/{id}/assign`, `GET /api/v3/pe/batches/{batch_id}/items`.
- **PO decision required:** yes — is bulk upload a paid tier, what is the maximum batch size, and what is the processing SLA?

**MISS-02 — Automatic PE assignment rules (Area 6)** `P1 · MISSING CAPABILITY · ARCHITECTURAL GAP`
- **No rule model exists.** Searches for `auto_assign`, `assignment_rule`, `routing_rule` across `backend/`, `frontend/src/` and `supabase/migrations/` return only `queue_settings.auto_assign_enabled` — a **single global boolean** inside the single `review_sla_defaults` row, used for review workload balancing, not PE routing.
- **No organisation → PE persistence.** `organizations` has **no** column matching `%entity%`, `%route%`, `%assign%`, `%processing%` or `%consultant%` (68 columns checked). `processing_entities` has no organisation link. There is no `organization_processing_entity`-style table. Therefore "Organisation XYZ → PE 123" has **nowhere to be stored today**.
- **What does exist:** `work_item_assignments` (per-item, `assignee_kind` = `internal_staff` XOR `processing_entity`, CHECK-enforced, actions `assign/reassign/claim/recover`, `previous_assigned_to`/`previous_processing_entity_id`/`reason`/`actor_domain`, unique open assignment per item — 2 rows); and `POST /api/v3/ops/batches/{batch_id}/assign` (`v3_operations.py:2160`), which assigns a *manual-extraction batch* to exactly one operator XOR PE, rejects non-`active` entities, sets the batch `in_progress`, clears the other side and writes before→after audit.
- **At upload time:** nothing is assigned. Uploads never set `processing_entity_id`/`entity_id`, and `document_processing_queue.batch_id` is NULL for **all 40** jobs.
- **No rule matched / multiple rules matched:** undefined — no engine exists. Flagged as a PO decision.
- **Manual override:** yes (item-level assign/reassign/claim; batch-level assign), audited.
- **Who can configure:** internal staff only — `require_staff` + `can_manage_staff` + `can_process`. An Organisation Owner, consultant or client cannot route work to a PE; consistent with AGENTS.md §12.
- **Audited:** yes for assignments (`work_item_assignments` history + V3 audit trail with previous→new).
- **Notification:** infrastructure exists (`notifications.recipient_type`, `actor_domain`, `event_key` with a uniqueness index, `notification_delivery`, Realtime, `frontend/src/v3/NotificationsPage.jsx`) but **no notification is created by `assign_batch`**, and the automatic pipeline's `_notify` (`automatic_processing.py:1164-1188`) notifies only the organisation's `owner`/`admin` members — **never a PE**. So "PE receives an immediate notification" is missing, not merely broken.
- **Conflicting permissions:** none found; PE staff are explicitly barred from being assigned a manual-extraction batch as a person (`v3_operations.py:2220-2224`).
- **PO decision required:** yes — rule source (org/consultant/client), precedence when multiple rules match, fallback when none match, and who may edit rules.

**MISS-03 — Customer/organisation choice of emission-factor source (Area 5B)** `P2 · MISSING CAPABILITY`
- No per-org factor-source/provider selector exists in schema or API. `organizations.default_factor_year` (2025 for 962 orgs, blank for 13) is the only factor-related organisation setting found. Country (`GB` 818 / `IE` 157) is stored and *is* used to filter factors, so cross-country selection works implicitly; explicit source selection does not exist.
- **Do not decide this for the PO** — see Section F.

**MISS-04 — Automatic assignment notifications (Area 6)** `P2 · MISSING CAPABILITY` — see MISS-02.

**MISS-05 — Pagination/sorting/filtering on 22 V3 tables (Area 7)** `P2 · MISSING CAPABILITY` — see Section L.

---

## E. Architectural gaps

**ARCH-01 — Batch model exists in three parallel places and the live path touches one (Area 1)** `P1 · ARCHITECTURAL GAP`
Three batch concepts coexist: `upload_batches` (RC2, with `UploadBatchesRepository`, the V3 `/batches` API and `entity_id`), `manual_extraction_batches` (D23 manual/PE batches, 57 rows), and `document_processing_queue.batch_id`.
- The V3 upload path creates **only** the reusable "Uploads" `manual_extraction_batches` row, with fabricated counts (BUG-07).
- `upload_batches` holds 52 rows — 50 `pending` with `total_files=4, processed_files=0, batch_type NULL` — never advanced, and is not created by the upload path.
- `document_processing_queue.batch_id` is NULL for all 40 jobs → **no batch-level progress or partial-failure accounting for automatic processing is possible today.**
- Consequence: "batch upload" cannot be delivered as a UI-only change; the intake, the batch record and the job linkage must agree first.

**ARCH-02 — Automatic processing worker runs in-process in the API application (Area 3)** `P2 · ARCHITECTURAL GAP`
`backend/main.py:282-285` starts `workers.automatic_processing.get_automatic_processing_worker()` inside the FastAPI lifespan, polling every 1 s (`workers/automatic_processing.py:40-91`). The job state is durable and resumable (good), but there is no separate worker process/queue: throughput and availability are coupled to the web instance, and horizontal scaling would have every replica poll the same table (the lock/claim design mitigates, but this is an architectural choice worth a PO/architecture decision before load testing).

**ARCH-03 — Two incompatible factor-retrieval paths (Area 5D)** `P2 · ARCHITECTURAL GAP`
The automatic pipeline resolves factors through `MatchingPipeline` (`engines/factor_matching.py`), while the human mapping picker uses `repos.factors.find_by_activity` → `activity_type ILIKE '%activity%'` with `limit=20` (`data/emission_factors.py:114+`, called from `v3_processing_workflow.py:1099-1142`). Different scoring, different ordering, different candidate sets — the operator can be shown a different (and differently-ordered) world from the one the pipeline used. `ExtractionPanel.jsx` uses a third path (`/mapping-options` variants). This is why a match can be "confident" in the pipeline while the picker looks empty, and vice versa.

**ARCH-04 — Blocked jobs are terminal in practice (Area 3/4)** `P1 · ARCHITECTURAL GAP`
`blocked` is a `HUMAN_GATE_STAGE` and the worker correctly releases the lock, but all 17 blocked jobs have `attempt_count = 0` and the newest are unactioned. There is no retry/backoff, no escalation, and no observable "who must act" path in the evidence — a document can sit forever. `manual_review_queue` holds only 2 rows for 17 blocked jobs, so blocked jobs are not all surfaced into the human queue.

**ARCH-05 — DEFRA component rows are indistinguishable from totals in the data model (Area 5)** `P0-adjacent · ARCHITECTURAL GAP / DATA`
`emission_factors` stores totals (`… (kg CO2e)`) and per-gas components (`… (kg CO2e of CH4 per unit)`, `… of CO2 per unit`, `… of N2O per unit`) as ordinary sibling rows with no column marking them as components, no `is_total` flag and no parent/child relation. This makes BUG-02 possible and will make any future factor-set migration risky. Scopes are present and populated (Scope 1 = 2 549, Scope 2 = 354, Scope 3 = 4 090, Outside of Scopes = 56) but are not used to disambiguate electricity.

---

## F. Product decisions required

| # | Decision needed | Why it cannot be inferred |
|---|-----------------|---------------------------|
| F-01 | Should batch/multi-file upload be free, a paid tier, or unrestricted — and what is the maximum batch size and SLA? | Legacy code asserts "premium feature … limit 1"; nothing else in the repository or a ratified decision states a policy. |
| F-02 | For UK organisations, is DEFRA the *mandated* default source, and may a customer select a different source (SEAI, own factors, per-geography/per-period)? | The pipeline is country-filtered and DEFRA-DESNZ dominates (7 029 of 7 049 rows), so DEFRA is the *de facto* default, but no ratified decision or setting establishes it as policy or permits alternatives. |
| F-03 | Which factors are legitimate for a given activity — the total row only, or per-gas rows too? Should Scope be taken from the factor or derived? | The dataset contains both and the current matcher conflates them (BUG-02). This is a methodology decision. |
| F-04 | What is the correct extraction-completeness threshold, and may a partial extraction be persisted/auto-accepted? | 0.50 is hard-coded; whether a partial result should be shown pre-filled to an operator is a product choice. |
| F-05 | PE assignment rules: source of truth, precedence when multiple rules match, fallback when none match, and who may edit them. | No rule model exists; the required example (org/consultant/client → PE) is a product requirement, not an implementation detail. |
| F-06 | Should assigning work to a PE notify the PE (and in-app only, or by email via the existing Resend integration)? | No notification is created today; the recipient model supports it, the policy does not exist. |
| F-07 | Is "10 rows per page" the ratified global table default for admin/ops tables? | `defaultPageSize = 10` is already the shipped `DataTable` default, so this is an in-codebase convention — but confirming it as a *global* rule (and whether every table must adopt `DataTable`) is a PO/UI decision. |
| F-08 | How should superseded emissions results be presented (current + history, or history only)? | Two conflicting snapshots are returned for one document (BUG-06); presentation policy is a product choice. |
| F-09 | May stored object content types be backfilled for historical documents? | The P0-1 helper deliberately never alters existing objects; repairing them is a data operation requiring approval. |

---

## G. UX/CSS findings

**CSS-01 — Vertical text in `.v3-meta-item` (Area 8)** `P1 · UX/CSS` (cosmetic-severe: it makes a primary organisation identifier unreadable)
- **Reproduced by:** DOM + CSS + built-artefact analysis (not by browser interaction; see Section Q for the limits of this).
- **Observed DOM:** `frontend/src/v3/admin/ProfileTab.jsx:12-19` `Field` renders
  `<div class="v3-meta-item"><div class="k">{label}</div><div class="v">{value}</div></div>`,
  inside `<div className="v3-meta-list">` (line 129). `<Field label="Name" value={profile?.name} />` (line 130) is the reported "Quayside Energy" element.
- **The two rules quoted in the issue are both real, and there is a third, decisive one:**
  - `frontend/src/v3/v3.css:301` → `.v3-meta-list{display:flex;flex-direction:column;gap:8px;min-width:0}`
  - `frontend/src/v3/reports/reports.css:263-267` → `.v3-meta-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px 20px}`
  - `frontend/src/v3/v3.css:303-304` → `.v3-meta-item .k{width:190px;flex:none}` and `.v3-meta-item .v{min-width:0;overflow-wrap:anywhere}`
- **Why normal names render vertically (arithmetic, not speculation):** the `reports.css` rule turns each `.v3-meta-item` into a **grid item in a column that is at least 200 px wide**, while its own flex layout consumes `190 px (label) + 12 px (gap) = 202 px`. The value element has `min-width:0`, so it is squeezed to ~0 px; `overflow-wrap:anywhere` then permits a break between every character → one character per line.
- **Cascade proof (built bundle `frontend/build/static/css/main.2356c9d3.css`):** both `.v3-meta-list` rules are present — the flex rule at byte offset 205 421 and the **grid rule at 267 896**, i.e. the grid rule wins by source order. Extracted verbatim:
  ```
  .v3-meta-list{display:flex;flex-direction:column;gap:8px;min-width:0}
  …
  .v3-meta-list{grid-gap:10px 20px;display:grid;gap:10px 20px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
  ```
  There are also **two** `.v3-meta-item .v` rules (both `v3.css` and `reports.css`), matching the duplication quoted in the issue.
- **Why it varies by screen/viewport:** `auto-fit` + `1fr` makes column width track the card width, so the available width for `.v` fluctuates around 0–20 px depending on layout and viewport — hence an apparently intermittent, size-dependent defect.
- **Single screen or shared component?** **Shared component defect.** `.v3-meta-list` has 14 call sites: `admin/ProfileTab.jsx:129`, `admin/SecurityTab.jsx:81,99`, `admin/MembersTab.jsx:120`, `customer/ReviewDetailPage.jsx:126`, `customer/EmissionsPage.jsx:191`, `customer/IssuesPage.jsx:194`, `components/EvidenceRecordPanel.jsx:30,39,46,56,63,81`, `reports/ReportDetailPage.jsx:215`. `reports.css` is imported by `reports/ReportsPage.jsx:18` and `reports/ReportDetailPage.jsx:17`; once bundled, CRA emits it **globally**, so the override applies on every route, not just reports.
- **`writing-mode`/`orientation`:** not used anywhere in these rules — the vertical appearance is purely width collapse, not a `writing-mode` defect.
- **Recommended direction (smallest correct):** stop the global leak — scope the `reports.css` overrides to the report detail surface (e.g. `.v3-detail-section .v3-meta-list`) or delete them and let the D21 shared stylesheet own the class; and make `.v3-meta-item` non-collapsing (`flex-wrap:wrap`, label `flex:0 0 auto` with a max-width rather than a hard 190 px, value `flex:1 1 auto` with `min-width:12ch`). Verify the reports detail page is unchanged, since it was presumably designed against the grid.
- **PO decision required:** no. **Regression risk:** medium (14 call sites; do not regress reports).

---

## H. Emission-factor findings

**What CarbonTally actually has today (verified):**

| Aspect | Status | Evidence |
|---|---|---|
| Factor data | **Present** | `emission_factors` = 7 049 rows: DEFRA-DESNZ 7 029, SEAI 20; year 2025 |
| Scopes | **Present and populated** | Scope 1 = 2 549, Scope 2 = 354, Scope 3 = 4 090, Outside of Scopes = 56 |
| Aliases / customer factors | **Present** | `factor_aliases`, `customer_factors` tables; CL-44 picker precedence path exists |
| Country filtering | **Implemented** | Pipeline filtered by `country`; GB vs IE return different providers (IE → SEAI `Fuels > …`) |
| Year selection | **Partially implemented** | `organizations.default_factor_year` (2025 for 962 orgs, blank for 13); pipeline accepts `reporting_year` |
| Versioning / import lineage | **Implemented** | `import_batches` table, `import_batch_id` on snapshots, `factor_set` (e.g. `DEFRA-2025`) |
| Provenance on results | **Strong** | `calculation_snapshots` carries `factor_id`, `factor_kind`, `customer_factor_id`, `factor_source`, `factor_set`, `import_batch_id`, `content_hash`, `algorithm_version`, `request_id`, `source_item_id`, `source_page`, `calculated_at` |
| Matching correctness | **Defective** | BUG-02 (component rows matched at confidence 1.00) |
| Component vs total discriminator | **Absent** | ARCH-05 |
| Admin UI for system factors | **Exists, but in a separate app** | `admin/src/pages/admin/DefraFactors.js` + `admin/src/components/admin/DefraFactorModal.js` + `ImportDefraModal.js`; served under `/admin/*` by root `vercel.json` rewrites; backed by `routes/admin/defra.py`, `api/admin_imports.py`, `api/admin_providers.py`, `routes/reports.py:1238 /admin/import-defra-factors` |
| Admin UI in the V3 app | **Missing for system factors** | `frontend/src/v3/admin/` contains only `CustomFactorsTab.jsx` (customer factors) |
| Factor activation/deactivation | **UNVERIFIED** | Not confirmed in code within this audit's budget; do not assume either way |
| Per-org factor source selection | **Missing** | No schema column, no API, no UI (MISS-03) |

**Answers to A–D as posed:**

- **A. UK companies / DEFRA as the default.** Yes, **de facto** — 7 029 of 7 049 rows are `DEFRA-DESNZ`, the matcher filters by `country`, and UK tests resolve DEFRA rows (`factor_source = 'DEFRA-DESNZ'`, `factor_set = 'DEFRA-2025'` is what the persisted snapshot recorded). There is **no explicit "default factor source" setting**: the default is emergent from which rows exist for a country. If a ratified default is required, it would have to be established as an explicit, persisted, server-side setting (organisation-level, with a system-level fallback) — it does not exist today.
- **B. Customer choice.** **Not supported.** Nothing in `organizations` (68 columns checked), no settings key, no API, and no UI exposes a factor-source choice. The architecture does not *prevent* it — factors are already partitioned by `country`/`year`/`provider_key`/`factor_set`, and `MatchingPipelineConfig` has provider plumbing — but there is no configuration surface. **PO decision F-02 applies; do not assume customers may choose arbitrary factors.**
- **C. Admin management.** A DEFRA factor management UI **does exist** (`admin/` app: list, modal, import) with import/version lineage, but it sits outside the V3 application shell (`/admin/*`), and the V3 app cannot manage system factors at all. Provenance is recorded on every calculation. Whether factors can be **activated/deactivated**, whether versions can be **selected**, and whether factors can be **associated with geography/entity/reporting period** as first-class configuration is **UNVERIFIED** — geography and period are already implicit in the data (`country`, year, `factor_set`), entity association is not evidenced.
- **D. "Load Factor".** **This is not an emission factor concept in the codebase.** It is the button label `Load factor options` at `frontend/src/v3/customer/ProcessingItemWorkspace.jsx:576`, which calls `loadMappingOptions` → `GET /api/v3/…/items/{item_id}/mapping-options` (`backend/api/v3_processing_workflow.py:1099-1142`). That endpoint derives candidates from `item.extracted_data.activity` + `unit` via `repos.factors.find_by_activity` (`limit=20`, `ILIKE` substring). Therefore: **when extraction produced no `activity`, `activity = ''` → `factors = []` → the panel shows "No factor options loaded yet."** The root cause is **missing extraction (BUG-01)**, not a missing factor, not a category-mapping error, and not an unsupported activity type. The UI is already honest: it renders `no_factors_reason` and, for spend-based activities (`GBP`/`EUR`, which the physical-unit DEFRA/SEAI sets cannot cover), a `spend_suggestion` with a deep link to `/organization?tab=factors`. Secondary contributor: ARCH-03 (the picker and the pipeline use different retrieval paths).

---

## I. Automatic-processing pipeline trace

Stage machine (`backend/domain/automatic_processing.py:98-110`):
`RUNNABLE_STAGES = (enqueued, ingesting, extracting, mapping, validating, calculating)`;
`HUMAN_GATE_STAGES = (blocked, review)`; `TERMINAL_STAGES = (completed, failed)`.
Worker: `backend/workers/automatic_processing.py`, started at `backend/main.py:282-285` (in-process, 1 s poll), durable claims/locks, resume on restart, deterministic `request_id`, no-duplicate guard via `find_snapshot_by_request_id`.

| Stage | Implemented? | API | DB | UI | Runtime verdict |
|---|---|---|---|---|---|
| UPLOAD | **Yes** | `POST /api/v3/documents/uploads` (single file) | `organization_files`, `manual_extraction_batches/items` | `DocumentsPage.jsx`, `ProcessingPage.jsx` | **Works.** Storage → record → item → job + OCR prefill. Single-file only. |
| QUEUE | **Yes** | `POST /api/v3/documents/uploads` (enqueue is part of it) | `document_processing_queue` (40 rows) | `ProcessingPage.jsx` list | **Works**, durable. Not linked to `batch_id` (all NULL). |
| EXTRACTION | **Yes, but destructive on failure** | internal worker stage | `extracted_data` | `ExtractionPanel.jsx`, workspace | **Runs**; **discards partial results** and blocks (BUG-01). 8/17 blocked jobs persisted nothing; 4 post-release jobs all blocked. |
| CATEGORISATION (Scope 1/2/3) | **Implemented, but inherits the factor** | — | `calculation_snapshots.scope` | workspace, emissions views | **Works mechanically**; produced **Scope 3** for electricity because the wrong factor row was chosen (BUG-02). Do not treat the stored scope as verified. |
| FACTOR MATCHING | **Implemented, defective** | `GET /api/v3/emissions/factors*`, `/lookup` | `emission_factors`, `factor_aliases`, `customer_factors` | mapping pickers | **Blocks 5/17** with `no_match` (`Natural gas` kWh/m3, `Waste` cubic metres, spend-based GBP activities); **and matches wrong factors at confidence 1.00** for others (BUG-02). Fixed-width window: `mapped_data` records `stages_executed`, `mapping_confidence`, `methodology`. |
| VALIDATION | **Yes** | worker stage | `validation_result` on job | workspace findings, `IssuesPage.jsx` | **Ran and passed** the wrong electricity factor with `{"status":"passed","findings":[]}` — validation does not catch component-row factors or scope mismatch. |
| CALCULATION | **Yes** | worker stage; `POST /api/v3/…/calculate` | `calculation_snapshots` (100 rows), `emissions_logs` | workspace, `EmissionsPage.jsx` | **Works and is server-authoritative.** Exercised end-to-end: 20/20 completed jobs have a snapshot. 4/17 blocks dated 2026-08-29 are **historical** (pre-`daad396` P0-3 methodology/unit normalisation in `engines/calculation.py:230-266`) and must not be reported as current without re-verification. |
| EVIDENCE / PROVENANCE | **Yes** | `GET /api/v3/documents/{id}/emissions` (D33) | `calculation_snapshots` ← `emissions_logs` ← `manual_extraction_items.file_id` | `EvidenceRecordPanel.jsx`, `EvidenceTrail.jsx` | **Chain is intact** — proven for `electricity_invoice.jpg`: item `a1610bbb` → snapshots `62ff4299`, `6297840f` → logs `047b02f8`, `850c3d4e`. Audit entry written per lookup. Caveat: returns **multiple contradictory results** (BUG-06) and `source_location` has no persistence. |
| REVIEW | **Yes** | worker gate `review`; `POST /api/v3/ops/review/{id}/assign\|complete` | `document_processing_queue.stage='review'` (3 rows), `manual_review_queue` (2) | `ReviewPage.jsx`, `ReviewDetailPage.jsx` | **Reached and populated** (3 jobs at `customer_review`). |
| APPROVAL | **Yes** | customer approve/reject in workspace | item `customer_approved`, job `status='approved'` | `ProcessingItemWorkspace.jsx` | **Works** — 20 jobs `approved`/`completed`. |

**Runtime distribution of `document_processing_queue` (40 rows):**

| status | stage | count |
|---|---|---|
| approved | completed | 20 |
| manual_review | blocked | 17 |
| customer_review | review | 3 |
| **failed** | — | **0** |

Blocked reasons (17): extraction completeness 0.00 → 4; extraction completeness 0.33 → 6; mapping `no_match` → 5; calculation blocked → 4 (all dated 2026-08-29, historical). Of the 17 blocked, **8 have `extracted_data` NULL/empty** and 13 have no `mapped_data`.

**Post-release behaviour (created after the 2026-09-11 release `daad396`) — 4 jobs, all blocked, 0 completed:**
`color_02_water.pdf` (2026-09-14, completeness 0.33), `border_double_fuel.pdf` (2026-09-12, completeness 0.33), `ultimate_logi.pdf` (2026-09-12, mapping `no_match` for `'Waste' cubic metres`), `mock_scope3.csv` (2026-09-13, mapping `no_match` for spend activities).

**Precisely where the execution path breaks:** at the **extraction gate** first (partial result discarded), and at the **mapping gate** second (no confident factor). It does **not** break at: ingestion, document registration, job creation, the worker, snapshot persistence, the D33 reverse lookup, or the API response — all of those were exercised and are sound.

---

## J. Manual-processing pipeline trace

The manual/PE side is **substantially built** — considerably more than the reported symptoms suggest.

| Capability | Status | Evidence |
|---|---|---|
| Manual batches | **Implemented** | `manual_extraction_batches` (57 rows): `batch_name`, `total_documents`, `total_pages`, `total_cost`, `price_per_page`, `currency`, `status`, `sla_deadline`, `sla_breached`, `assigned_to`, `assigned_by`, `entity_id`, `qc_*`, `customer_notes` |
| Work items | **Implemented** | `manual_extraction_items` (264 rows): 35 columns incl. `processing_origin`, `processing_entity_id`, `pe_reviewed_by/at`, `pe_qc_by/at`, `qc_*`, `customer_reviewed_*`, `customer_approved` |
| Batch → PE / operator assignment | **Implemented** | `POST /api/v3/ops/batches/{batch_id}/assign` — exactly one of `assigned_to` XOR `entity_id`, entity must be `active`, batch → `in_progress`, audit before→after + reason |
| Item-level assignment | **Implemented** | `POST /api/v3/ops/items/{item_id}/work/assign` and `/work/reassign`; `work_item_assignments` with CHECK-enforced assignee shape and full previous→new history |
| Staff queue / operator queue | **Implemented** | `GET /api/v3/ops/…`, `frontend/src/v3/ops/OperatorQueue.jsx`, `ReviewQueue.jsx`, `QcQueue.jsx`, `StaffRoster.jsx`, `PEManagerDashboard.jsx` |
| PE workspace | **Implemented** | API: `/api/v3/pe/items/{item_id}/{extract,map,calculate,clarify}`, `/api/v3/pe/batches/{batch_id}/items`, `/api/v3/pe/issues*`; UI routes `/pe`, `/pe/assignments`, `/pe/items/:entityId/:itemId` (`App.js:2214-2249`) |
| PE extraction workspace (entity-scoped) | **Implemented** | `/api/v3/ops/entities/{entity_id}/extraction/{batches,items,next-item}`, `…/items/{item_id}/{extract,map,calculate,clarify,start,status}`, `…/dashboard`, `…/performance`, `…/audit-activity`; UI `frontend/src/v3/ops/EntityExtractionWorkspace.jsx` |
| Task/work-item model | **Implemented** | `work_item_assignments`, `manual_review_queue`, `staff_workload`, `staff_profiles`, `processing_assignments` (legacy, 0 rows) |
| Status/state model | **Implemented** | item `status`, batch `status`, `processing_origin`; workbench lock derived from server status (`ExtractionPanel.jsx` `LOCKED_STATUSES`) |
| Notifications | **Infrastructure only** | `notifications` supports `recipient_type`/`actor_domain`/`event_key`; **no PE notification is emitted on assignment** (MISS-04) |
| Automatic vs manual conflation | **Shared intake, distinguishable** | **One** upload path feeds both: `create_document_and_enqueue` creates the storage object + `organization_files` + a `manual_extraction_items` row + an automatic `document_processing_queue` job + OCR prefill, and the **consultant** client-upload endpoint reuses the identical function. `manual_extraction_items.processing_origin` distinguishes origin. They share one batch ("Uploads"), which is the main conflation risk. |
| Legacy parallel path | **Present, not adopted** | `/api/upload*` → `pdf_engine.py`(legacy) with hard-coded multipliers/aggregation; still reachable but not part of the V3 pipeline |

**Verdict:** the architecture **already** supports the intended manual/PE model; the gaps are *automatic* assignment, notification, and inventory/triage UX — not the work-item, assignment, status or PE-workspace layers.

---

## K. PE assignment / notification assessment

Traced against the required capability (`Organisation XYZ → PE 123`, `Consultant ABC → PE 123`, `Client 123 → PE 789`, auto-assign on upload, immediate PE notification, auditable, tied to the right org/client/batch/work item).

| Requirement | Status today | Evidence |
|---|---|---|
| Assignment-rule model | **DOES NOT EXIST** | No `assignment_rules`/routing table; only `queue_settings.auto_assign_enabled` (global bool in the single `review_sla_defaults` row) |
| `organisation → PE` | **DOES NOT EXIST** | `organizations` has no entity/route/assignment column (68 columns scanned) |
| `consultant → PE` | **DOES NOT EXIST** | No consultant↔PE table |
| `client → PE` | **DOES NOT EXIST** | No client↔PE table |
| Batch-level assignment | **EXISTS (manual)** | `POST /api/v3/ops/batches/{batch_id}/assign`; `manual_extraction_batches.entity_id` |
| Automatic assignment at upload | **DOES NOT EXIST** | No entity written at upload; `document_processing_queue.batch_id` NULL for all 40 jobs |
| No rule matched | **UNDEFINED** | No engine → PO decision |
| Multiple rules matched | **UNDEFINED** | No engine → PO decision |
| Manual override | **EXISTS** | batch assign/reassign; item assign/reassign/claim; clears the other party; audited |
| Who can configure | Internal staff only | `require_staff` + `can_manage_staff` + `can_process`; PE-staff-as-person assignment explicitly blocked |
| Assignment changes audited | **YES** | `work_item_assignments.previous_*` + `reason` + `action`; batch audit with previous→new party |
| Notification infrastructure | **EXISTS** | `notifications` (`recipient_type`, `actor_domain`, `event_key` + unique index), `notification_delivery`, Realtime, `NotificationsPage.jsx` |
| Immediate vs polling | **Event-written, pushed by Realtime** | `notifications` row insert + Supabase Realtime; the pipeline's own `_notify` targets org owner/admin only |
| PE notified on assignment | **NO** | `assign_batch` writes batch + audit only; no notification row |
| Conflicting permissions | **None found** | PE staff barred from person-assignment of batches; PE cannot self-assign orgs |
| Correct org/client/batch linkage | **Partial** | Item→batch→org is intact; **batch↔job** linkage is missing (ARCH-01) |

**Bottom line:** CarbonTally today has a *manual* assignment capability with good audit history, and **no** automatic PE routing, **no** rule persistence and **no** PE notification. The required feature is an addition, not a repair.

---

## L. Admin-table assessment

**The observed screen:** `frontend/src/v3/ops/CommercialTab.jsx` (Internal Operations → Commercial tab; customers / billing mode / credit ledger).
- It renders a **hand-rolled** table: `<table className="v3-table" style={{marginTop:8}}>` + `<thead>` + `(orgs||[]).map(...)` (**lines ~457-478**), and a second raw table for the credit ledger. Columns: Organisation, Mode, Country, Status, Ledger.
- Present: a `Filter by billing mode` `<select>` (All / CREDIT / STANDARD).
- **Missing:** pagination, column sorting, page-size selection, accessible `scope`'d headers, record count, empty state.
- **Component used:** none — `DataTable` is **not imported by this file**.

**The infrastructure already exists.** `frontend/src/v3/components/ui/DataTable.jsx` (D21.7) ships with:
- `PAGE_SIZES = [10, 25, 50, 100]` and **`defaultPageSize = 10`**;
- client pagination (`clientPaginate`) that always reports the real row count;
- client sorting via `sortValue` and server-side sorting via `onSortChange`/`sortKey`/`sortDir`;
- server pagination contract (`total`, `limit`, `offset`, `onPage`);
- caption, empty label, compact mode, row keys.

**Therefore "10 rows per page" is already an established codebase convention** — it is `DataTable`'s default, not a novel requirement. It has simply not been adopted everywhere. (Confirming it as a *global mandate* remains a PO/UI decision — F-07.)

**Is this isolated or systemic?** **Systemic.** 18 files use `DataTable`; **22 V3 files render raw `<table>`**:

| File | raw `<table>` | File | raw `<table>` |
|---|---|---|---|
| `consultant/ConsultantPage.jsx` | 8 | `ops/StaffRoster.jsx` | 1 |
| `ops/CommercialTab.jsx` | 6 | `ops/StaffRolesTab.jsx` | 1 |
| `customer/BillingPage.jsx` | 3 | `ops/SlaTab.jsx` | 1 |
| `ops/ReviewQueue.jsx` | 2 | `ops/ProcessingEntitiesTab.jsx` | 1 |
| `ops/QcQueue.jsx` | 2 | `ops/ExtractionPanel.jsx` | 1 |
| `ops/PEManagerDashboard.jsx` | 2 | `ops/EntityExtractionWorkspace.jsx` | 1 |
| `ops/OpsDashboard.jsx` | 2 | `customer/IssuesPage.jsx` | 1 |
| `ops/OperatorQueue.jsx` | 2 | `customer/DocumentsPage.jsx` | 1 |
| `customer/ExistingDataDiscoveryPage.jsx` | 2 | `admin/SecurityTab.jsx` | 1 |
| `customer/DashboardPage.jsx` | 2 | `admin/MembersTab.jsx` | 2 |
| `consultant/WhiteLabelTab.jsx` | 2 | `consultant/ConsultantTeamTab.jsx` | 2 |

Notably `DocumentsPage.jsx` uses `DataTable` for its document list **and** a raw table elsewhere, and `admin/SecurityTab.jsx` / `admin/MembersTab.jsx` also carry the `v3-meta-list` CSS defect (Section G) — i.e. the same pages lose both table and layout conventions.

**Recommended direction:** adopt `DataTable` on the ops/admin screens (the observed screen is one instance), starting with the highest-row-count operational tables; add a guard (test or lint) so new raw tables are flagged. Do **not** retrofit controls onto genuinely tiny static tables (AGENTS.md §36).

---

## M. Recommended priority order

| Order | ID | Severity | Why first |
|---|---|---|---|
| 1 | **A4-2** (wrong factor at 1.00) | P0 | Silently wrong, validated, approved emissions numbers — the platform's core value is a wrong answer. |
| 2 | **A4-1** (partial extraction discarded → 100 % block) | P0 | No document currently reaches emissions; blocks all downstream value. |
| 3 | **A4-3** (blocked jobs unrecoverable) | P1 | 17 jobs parked; without recovery, #2 stays invisible to operators. |
| 4 | **A2-2** (10 s re-sign → repeated downloads) | P1 | Cheap fix, blocks human review of every document. |
| 5 | **BUG-05 / BUG-06** (job row unrecorded; duplicate snapshots) | P1 | Trust in the evidence chain; two answers for one document. |
| 6 | **A2-1** (viewer name-vs-MIME) | P1 | Correctness of the viewer boundary for non-remediated objects. |
| 7 | **ARCH-05 + F-03** (component vs total rows) | P0-adjacent | Enables a durable fix for #1 rather than a patch. |
| 8 | **A1-1/A1-2/ARCH-01** (batch upload) | P1 | Core capability, but currently a PO decision (F-01) blocks design. |
| 9 | **CSS-01** (vertical text) | P1 (cosmetic-severe) | One-line cascade fix, 14 screens, high perceived-quality value. |
| 10 | **L** (22 tables) | P2 | Mechanical adoption of an existing component. |
| 11 | **A6/F-05/F-06** (PE auto-assign + notify) | P1/P2 | New capability requiring PO decisions before design. |
| 12 | **MISS-03/F-02** (factor-source choice) | P2 | PO decision, no implementation until ratified. |

---

## N. Dependencies

- **A4-2 and ARCH-05 are coupled.** Fixing the scoring without a component/total discriminator will keep producing confident wrong matches. Factor data semantics must be settled with A4-2.
- **A4-2 also depends on F-03** (may per-gas rows be used?) and on F-02 (source defaults), because "the right factor" changes with both.
- **A4-1 → A5-D.** The "Load Factor" complaint cannot be resolved independently of extraction; it will resolve itself for documents where extraction succeeds.
- **A4-1 and A4-3 are paired.** Persisting partial extraction without a recovery/escalation path merely moves the dead end.
- **A1-2 → ARCH-01.** Enabling multi-file intake without fixing the batch model will manufacture the fabricated-count problem at scale. `document_processing_queue.batch_id` must be populated first, otherwise batch progress and partial-failure accounting remain impossible.
- **BUG-03 and BUG-04 are the same component** and should be fixed together to avoid two rounds of viewer regression testing.
- **CSS-01 fix must be verified against `ReportDetailPage`**, which was designed against the grid override.
- **A6 depends on F-05/F-06**; the assignment *mechanics* (audit, override, entity validation) can be reused unchanged.

---

## O. Regression / security concerns

- **No P0 authorization defect found** in the areas audited. `POST /api/v3/documents/uploads` denies `org_viewer` before any storage object or row is created; documents live in a private bucket and only short-lived signed URLs are produced (D32); the D33 reverse-lookup endpoint enforces `require_org_member()` + `ensure_org_access` and writes an evidence-access audit entry. PE boundaries are enforced server-side in the PE/ops endpoints inspected.
- **Signed URLs must never be logged.** The `viewer_url` is a signed URL with a live token; any change to BUG-03 must not add logging of the URL (AGENTS.md §68/§78).
- **Changing the matching score is high-blast-radius:** it feeds `emission_factors` → `calculation_snapshots` → `emissions_logs` → reports. Any fix must re-verify all four plus report output, and must be tested with both ALLOW and DENY-style cases (right factor accepted, component/junk rows rejected).
- **Do not "fix" the wrong-factor problem by lowering `AUTO_MAPPING_CONFIDENCE_MIN`** — the matched score is already 1.00, so the floor is not the defect. Raising it would block everything else.
- **Duplicate-snapshot handling must not delete history** (immutability, AGENTS.md §17/§19).
- **Investor demo data must not be touched.** No demo rows were mutated in this audit; all queries were reads.
- **Existing blocked rows are historical evidence.** The four `calculation blocked` rows dated 2026-08-29 predate the `daad396` (2026-09-11) P0-3 methodology/unit normalisation and must not be reported as current defects without re-running.

---

## P. Exact files / routes / schema inspected

**Frontend**
`frontend/src/App.js` (routes 2000-2250; legacy `Dashboard` 502, `BulkUpload` mount 1829, `UploadManager` 1818) · `frontend/src/index.js` · `frontend/src/BulkUpload.jsx` (116, 393-394) · `frontend/src/components/UploadSection.js` · `frontend/src/UploadManager.js` · `frontend/src/v3/customer/DocumentsPage.jsx:177` · `frontend/src/v3/customer/ProcessingPage.jsx:293` · `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` (poll 194-201; WorkbenchShell ~891; mapping pane 576-615) · `frontend/src/v3/customer/ReviewDetailPage.jsx:126` · `frontend/src/v3/customer/EmissionsPage.jsx:191` · `frontend/src/v3/customer/IssuesPage.jsx:194` · `frontend/src/v3/components/workbench/SecureDocumentViewer.jsx` (whole file) · `frontend/src/v3/components/workbench/WorkbenchShell.jsx:43` · `frontend/src/v3/components/EvidenceRecordPanel.jsx:30-81` · `frontend/src/v3/components/ui/DataTable.jsx` · `frontend/src/v3/ops/CommercialTab.jsx` · `frontend/src/v3/ops/ExtractionPanel.jsx:85-140,436` · `frontend/src/v3/ops/WorkItemWorkspace.jsx:108` · `frontend/src/v3/admin/ProfileTab.jsx:12-19,129-148` · `frontend/src/v3/admin/SecurityTab.jsx:81,99` · `frontend/src/v3/admin/MembersTab.jsx:120` · `frontend/src/v3/reports/ReportDetailPage.jsx:17,215` · `frontend/src/v3/reports/ReportsPage.jsx:18` · `frontend/src/v3/v3.css:301-304` · `frontend/src/v3/reports/reports.css:263-281` · `frontend/build/static/css/main.2356c9d3.css` · `frontend/vercel.json` · `vercel.json` · `admin/src/pages/admin/DefraFactors.js` · `admin/src/components/admin/DefraFactorModal.js` · `admin/src/components/admin/ImportDefraModal.js` · `admin/src/App.js`

**Backend**
`backend/main.py:270-285,389-392` · `backend/workers/automatic_processing.py:1-91,169` · `backend/services/automatic_processing.py:240-300,1164-1188` · `backend/services/automatic_extraction.py` · `backend/services/storage.py:26,57-80` · `backend/api/v3_documents.py:160-205,208-380,451-505` · `backend/api/v3_processing_workflow.py:1062,1099-1142` · `backend/api/v3_operations.py:1528,2160-2245,2248-2290` · `backend/api/v3_consultants.py:1275` · `backend/routes/upload.py:124,185,265-296,553` · `backend/engines/calculation.py:230-266` · `backend/engines/factor_matching.py:292` · `backend/engines/matching_stages.py:60-200` · `backend/infra/search_index.py:132-177` · `backend/domain/matching.py` · `backend/domain/automatic_processing.py:98-110,218-228` · `backend/domain/processing.py`/`domain/operations.py:152` · `backend/data/emission_factors.py:114+` · `backend/data/emissions_logs.py:316-333` · `backend/data/upload_batches.py` · `backend/data/processing_entities.py` · `backend/data/queue_settings.py` · `backend/api/dependencies.py:63,300,355,491` · `backend/data/__init__.py:19,29`

**Live API surface (inspected via `http://localhost:8050/openapi.json`)**
`POST /api/v3/documents/uploads` · `GET /api/v3/documents` · `GET /api/v3/documents/{file_id}/url` · `GET /api/v3/documents/{file_id}/emissions` · `POST /api/v3/documents/uploads/{file_id}/ocr` · `POST/GET /api/v3/documents/batches` · `POST /api/v3/ops/batches/{batch_id}/assign` · `POST /api/v3/ops/items/{item_id}/work/assign|reassign` · `POST /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/{extract,map,calculate,clarify,start,status}` · `GET /api/v3/ops/entities/{entity_id}/extraction/{batches,next-item}` · `POST /api/v3/pe/items/{item_id}/{extract,map,calculate,clarify}` · `GET /api/v3/pe/batches/{batch_id}/items` · `POST /api/v3/pe/issues*` · `POST /api/v3/ops/review/{review_id}/assign|complete` · `POST /api/v3/admin/review-queue/{review_id}/assign` · `POST/GET /api/admin/assignments/*` · `GET/PUT /api/v3/admin/entities/{entity_id}` · `POST /api/v3/settings/analytics` (context) · `POST /upload-batch` (legacy, disabled) · `POST /api/admin/import-defra-factors`

**Database / storage**
`document_processing_queue` · `manual_extraction_batches` · `manual_extraction_items` · `upload_batches` · `manual_review_queue` · `processing_queue` · `processing_assignments` · `processing_entities` · `work_item_assignments` · `review_assignment_history` · `reassignment_history` · `queue_settings` · `notifications` · `notification_templates` · `notification_delivery` · `calculation_snapshots` · `emissions_logs` · `emission_factors` · `factor_aliases` · `customer_factors` · `organizations` · `organization_files` · `import_batches` · Supabase Storage bucket `documents` (+ `uploads` referenced in legacy paths)

**Documentation / policy**
`AGENTS.md` (§17, §19, §23, §36, §42, §57, §63, §66-70, §80) · `tools/seed_investor_demo/DEMO_IDENTITIES.md` (referenced, not exercised)

### P.1 Working-tree state — a material qualification

The repository working tree carries **uncommitted** changes on top of HEAD `37b19d1`, and the running API on `:8050` serves that working tree. Everything read and executed in this audit reflects the **working tree**, not the committed release. Explicitly:

- **Unmodified vs HEAD (so the findings are stable and committed):** `backend/api/v3_documents.py` (incl. the P0-1 `_renderable_content_type` helper), `frontend/src/v3/components/workbench/SecureDocumentViewer.jsx`, `backend/services/storage.py`. Verified via `git diff HEAD -- <paths>` → empty. The P0-3 methodology/unit normalisation (`derive_methodology`, `resolve_unit_for_factor`) is also in HEAD (`daad396`).
- **Modified vs HEAD (in-flight work) and relevant to this audit:** `backend/services/automatic_processing.py` (+20/−1), `backend/services/automatic_extraction.py` (+53), `backend/engines/calculation.py` (+8), `backend/domain/automatic_processing.py` (+2/−1), `backend/data/emissions_logs.py` (+9/−? ), `backend/api/v3_operations.py`, `backend/api/dependencies.py`, `backend/api/router.py`; plus untracked Phase 8 files (`backend/api/v3_disclosure.py`, `backend/data/{disclosure,disclosure_narrative,disclosure_projection,evidence_line_items,report_artefacts}.py`, `backend/domain/disclosure.py`, …).
- **What the in-flight work does (read from the diff):**
  - `automatic_extraction.py` already contains a **shadow-first Phase 8 P1 extraction-fidelity block** (`services/extraction_fidelity`): it computes a `coverage` block, and in `MODE_ENABLED` emits `line_items[]` for multi-line-suspect documents, or returns `status = "multi_line_unresolved"` with a `block_reason` instead of silently collapsing. **This is directly adjacent to finding A4-1** — the P1 remediation for extraction fidelity is *partially implemented in shadow mode*, not absent. It has evidently not been enabled in this environment (the observed post-release jobs still carry the collapsed single-record behaviour and the 0.33 completeness gate), so **A4-1 remains reproducible as described**, but the recommended direction overlaps existing Phase 8 P1 work and must be coordinated rather than duplicated.
  - `automatic_processing.py` resolves a `source_line_item_id` via `evidence_line_items.get_by_ordinals` (B2 §13.2, best-effort, NULL when unresolvable).
  - `engines/calculation.py` adds `source_line_item_id` and deliberately **excludes it from the content-hash and `request_id` derivation** (B2 §8.4/§13.3) — relevant context for the duplicate-snapshot finding (BUG-06): the dedupe key is unchanged by that field.
- **Because of this, every finding in this report should be re-confirmed against a frozen commit before implementation**, and `automatic_extraction.py` / `automatic_processing.py` must be treated as actively changing. This is exactly the AGENTS.md §80 discipline applied to my own audit.

---

## Q. Evidence and reproduction results

All commands were read-only. Service-role credentials were used only for read queries and the storage sign/HEAD checks; no secret value was printed.

1. **Matching pipeline, executed through the real entry point** (`engines.factor_matching.build_matching_pipeline`, 7 049 factors indexed):
   ```
   country=GB year=2025 activity='Electricity' unit='kWh'  -> matched conf=1.00 factor='Managed assets- electricity > … > kWh (kg CO2e of CH4 per unit) [kWh]' mult=0.0009
   country=GB year=2025 activity='Diesel'      unit='litres' -> matched conf=1.00 factor='Bioenergy > Biofuel > Development diesel (kg CO2e) [litres]'        mult=0.03705
   country=IE year=2025 activity='Electricity' unit='kWh'  -> matched conf=1.00 factor='Fuels > Electricity > Electricity consumption (kg CO2) [kWh]'       mult=0.197803384
   country=IE year=2025 activity='Diesel'      unit='litres' -> matched conf=1.00 factor='Fuels > Liquid fuels > Diesel / gasoil (100% petroleum) (kg CO2) [litres]' mult=2.682327
   ```
   DB confirms the correct rows exist and were not chosen, e.g. `Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e) [litres] = 2.66155`; `UK electricity > … > kWh (kg CO2e) [kWh] = 0.177`; `Managed assets- … (kg CO2e of CH4 per unit) = 0.0009`.

2. **Persisted wrong result** — job `e49b46b3-6006-4e7e-98a4-ac57c4eb0047` (`electricity_invoice.jpg`): `status=approved`, `stage=completed`, `extracted_data` complete, `mapped_data.methodology="keyword_search"`, `mapping_confidence=1.0`, factor `34dac8fd-…`; `validation_result={"status":"passed","findings":[]}`; snapshot `6297840f-936f-479c-b55f-af2752812268`: `quantity 12500`, `co2e_multiplier 0.0009`, `co2e_kg 11.25`, `scope Scope 3`, `calculated_at 2026-08-29 12:02:08`.

3. **Current failure point** — job `b6e15354-b064-46d4-a549-457b8f489f07` (`color_02_water.pdf`, 2026-09-14): `stage=blocked`, `status=manual_review`, `extracted_data` NULL, `mapped_data` NULL, `last_error` NULL, `attempt_count=0`, reason `extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit`. Identical shape for `e7db7f32-…`. **All 4 jobs created after 2026-09-11 are blocked; none completed.**

4. **Queue distribution** — 40 rows: 20 `approved`/`completed`, 17 `manual_review`/`blocked`, 3 `customer_review`/`review`, 0 failed. Blocked: 8 with empty `extracted_data`, 13 with no `mapped_data`. Reasons: 10 completeness, 5 mapping `no_match`, 4 calculation (all dated 2026-08-29, historical).

5. **Denormalisation gap** — `stage='completed'`: `count(*)=20`, `count(calculation_snapshot_id)=20`, `count(calculated_emissions_kg_co2e)=0`, `count(emission_factor_used)=1`.

6. **Reverse-lookup chain works** — `manual_extraction_items.file_id` → `calculation_snapshots.source_item_id` → `emissions_logs.snapshot_id` returns 2 rows for `electricity_invoice.jpg` (2 212.5 kg and 11.25 kg) → confirms both that the D33 path is functional and that it returns conflicting results. 100 snapshots / 46 source items / up to 4 each; 1 true duplicate sharing `source_item_id` + `content_hash`.

7. **Signed-URL instability** — two `POST /storage/v1/object/sign/documents/<path>` calls 2 s apart: tokens differ; decoded claims `{scope: download, iat: 1789369287, exp: 1789372887}` vs `{iat: 1789369289, exp: 1789372889}`. The signed URL itself returns `HTTP 200`, `Content-Type: application/pdf`, **no `Content-Disposition`**.

8. **Stored content types** — 12/12 sampled PDF objects return `Content-Type: application/pdf`; `organization_files.mime_type` = `application/pdf` for 228/228 PDFs (plus xlsx 20, csv 13, jpeg 1, plain 1). The octet-stream leg is **not currently reproducible in this dataset**.

9. **Batch model not wired** — `document_processing_queue.batch_id` NULL for **40/40**; `upload_batches` 52 rows (50 `pending`, `total_files=4`, `processed_files=0`, `batch_type` NULL); `manual_extraction_batches` "Uploads" declaring `total_documents=1` with **47** actual items; 0/264 items without a batch.

10. **Legacy batch endpoint disabled** — `backend/routes/upload.py:273-296` returns `{"status":"premium_feature", …, "limit":1, "action":"upgrade_required"}` unconditionally, before any work.

11. **CSS cascade, from the built bundle** — `frontend/build/static/css/main.2356c9d3.css`: `.v3-meta-list{display:flex;flex-direction:column;gap:8px;min-width:0}` at 205 421 and `.v3-meta-list{grid-gap:10px 20px;display:grid;gap:10px 20px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}` at 267 896 (grid wins); `.v3-meta-item .k{flex:none;font-size:13px;width:190px}`; `.v3-meta-item .v{min-width:0;overflow-wrap:anywhere}`; 2 `.v3-meta-list` rules and 2 `.v3-meta-item .v` rules.

12. **Emission-factor inventory** — `emission_factors` 7 049 rows (DEFRA-DESNZ 7 029 / SEAI 20, year 2025); scopes 2 549 / 354 / 4 090 / 56; `organizations` country GB 818 / IE 157, `default_factor_year` 2025 = 962, blank = 13; `processing_entities` 11 rows (Entity Alpha/Beta, PE Alpha/Beta/Gamma Ltd, Test PEs); `work_item_assignments` 2 rows; `queue_settings` 1 row.

13. **Schema checks** — `organizations` has **no** `%entity%`/`%route%`/`%assign%`/`%processing%`/`%consultant%` column (68 columns); `notifications` has `recipient_type`, `actor_domain`, `event_key` (+ `uq_notifications_event_key`); `manual_extraction_items` has 35 columns incl. `processing_origin`, `processing_entity_id`, `pe_*`.

14. **Table convention** — `DataTable.jsx`: `PAGE_SIZES = [10,25,50,100]`, `defaultPageSize = 10`; 18 adopters, 22 raw-`<table>` V3 files.

**Limits of this evidence (stated so the audit is not overstated):**
- The CSS defect was proven by DOM + cascade + arithmetic and the **built** stylesheet, **not** by visual browser confirmation. A screenshot at a real viewport would close this gap.
- The empty `Load factor options` result was established from code + endpoint logic, not from a logged-in click-through.
- Factor **activation/deactivation** semantics were not traced (marked UNVERIFIED).
- The four `calculation blocked` rows are historical; post-`daad396` calculation-stage behaviour for unit/methodology cases was **not** re-executed (re-running jobs would mutate queue state, which this audit was instructed not to do).
- Whether a PE can *currently* see assigned work end-to-end was verified at the API/schema/route level, not by logging in as a PE.
- No `attempt_count`/retry behaviour was exercised; `attempt_count=0` on blocked jobs is an observation, not a tested retry path.

---

## R. Recommended implementation sequence

**Step 0 — PO decisions (blocking, no code).** F-01 (batch policy/size/SLA), F-02 (factor-source policy), F-03 (component vs total rows), F-04 (completeness threshold + partial persistence), F-05/F-06 (PE rules + notification), F-07 (global 10-row rule), F-08 (superseded results), F-09 (content-type backfill).

**Step 1 — Stop emitting wrong numbers (A4-2 + ARCH-05).** Make the matcher reject per-gas component rows and penalise unmatched factor tokens; make validation fail on a component-row factor and on a scope mismatch. Regression-test the scoring function with right-factor/allowed and component-row/denied cases, then re-run representative documents through the real pipeline entry point and compare against the DEFRA totals by hand. **Do not ship anything else in the same change** — this is the highest-risk, highest-value fix.

**Step 2 — Make extraction lossless on block (A4-1).** Persist the partial extraction payload before entering the human gate, surface it pre-filled in the processing workspace, and record precisely which fields are unresolved. Re-verify that post-release documents at least reach manual review *with data*.

**Step 3 — Make the human gate actionable (A4-3).** Ensure every blocked job is represented in an operator queue with an owner, a reason and a resume path; define retry/escalation. Confirm the count of blocked-with-no-data goes to zero.

**Step 4 — Fix the secure viewer (A2-2 + A2-1, one change, one regression pass).** Stabilise the iframe source (key on the document, re-sign only on demand/expiry) and drive renderability from the server-reported MIME or a server-computed flag. Verify Owner/Admin/Member/Consultant/PE/Viewer paths and the PE no-download boundary.

**Step 5 — Repair evidence trust (BUG-05 + BUG-06).** Write back the job's denormalised emissions/factor, and mark or expose a canonical snapshot so one document yields one current answer plus history. Verify reports still aggregate correctly.

**Step 6 — Batch upload (ARCH-01 → A1-1/A1-2).** Only after F-01: populate `document_processing_queue.batch_id`, decide the single batch of record, fix the fabricated counts, then add a multi-file intake (reusing the existing `create_document_and_enqueue` per file so per-document lineage and partial-failure isolation come for free) and re-enable/replace the disabled legacy endpoint. Add a multi-file picker to `DocumentsPage.jsx`/`ProcessingPage.jsx` (or revoke the orphaned `BulkUpload` into the V3 shell).

**Step 7 — CSS cascade fix (CSS-01).** Remove/scope the `reports.css` `.v3-meta-list`/`.v3-meta-item` overrides, make `.v3-meta-item` wrap without collapsing, then screenshot all 14 call sites plus the reports detail page at the standard viewports (1920/1440/1280/1024/768/430/390/375).

**Step 8 — Table convention (L, F-07).** Migrate the ops/admin raw tables to `DataTable` (10-row default), highest row counts first; add a guard test.

**Step 9 — PE auto-assignment + notification (A6, after F-05/F-06).** Add the rule model and persistence, resolve precedence/fallback, hook assignment into upload, and emit a PE notification through the existing `notifications`/Realtime path. Reuse the existing assignment mechanics, audit trail and active-entity validation unchanged.

**Step 10 — Factor-source governance (MISS-03, after F-02).** Add explicit, persisted, server-side source/default configuration with a system fallback, and expose it in the appropriate administrative surface. Reuse the existing `country`/`year`/`provider_key`/`factor_set` partitioning and `MatchingPipelineConfig` plumbing.

**Independent QA after each step.** Steps 1, 2 and 5 change persisted emissions behaviour and must be re-verified against the live pipeline and the D33 evidence chain, not only by unit tests.

---

*No application code, database schema, migration, production data or configuration was modified in producing this audit. No fix was implemented.*
