# CT-P8-SOURCE-EVIDENCE-FORENSIC-20260922

**Forensic analysis of CarbonTally document extraction, mapping, calculation evidence, audit/evidence tracing, and the proposed source-document evidence viewer.**

| Item | Value |
| --- | --- |
| **Forensic ID** | `CT-P8-SOURCE-EVIDENCE-FORENSIC-20260922` |
| **Date** | 2026-09-22 |
| **Repository** | `/home/shomonrobie/ct_93d5cdd` |
| **Branch** | `p8-release-reconciled` |
| **HEAD at analysis** | `67d399f478feabf643d32e66a00fcc408660eb3e` (I6 PO closure) |
| **Remote** | `github/p8-release-reconciled` — aligned `0/0` |
| **Working tree** | clean (`git status --porcelain --untracked-files=all` empty) |
| **Change footprint of this task** | **one new documentation file only** (this report) — no code, schema, migration, RLS, API, test or configuration change |
| **Authorization** | **Forensic/read-only only. NO implementation is authorized by this document.** |
| **Method** | independent repository inspection: schema/migrations, backend domain/data/service/API layers, frontend components and API client, tests, and the closed Phase 8 governance records |

## 1. Forensic identification

| Item | Value |
| --- | --- |
| Investigation subject | what CarbonTally can **actually** do today for source-evidence tracing, source-document viewing, and Insight-driven navigation to evidence |
| Target scenario | a customer asks Insight *why* a specific dated emission (e.g. `20,000 kg CO₂e`, 2024-02-02) occurred, and whether CarbonTally can locate the exact invoice and the exact line/row that supports it |
| Classification vocabulary | **VERIFIED** · **PARTIALLY VERIFIED** · **NOT FOUND** · **UNKNOWN** · **INFERENCE** |
| Verdict summary | evidence **tracing** exists and is substantial; source-document **viewing** exists only inside the internal processing workbench; Insight **navigation** to evidence does **not** exist; exact **line/row locators** are half-produced and half-unreachable (see §31) |

## 2. Repository / commit state

**[VERIFIED]** At the start of this analysis:

* branch `p8-release-reconciled`;
* `git rev-parse HEAD` = `67d399f478feabf643d32e66a00fcc408660eb3e` (the I6 PO-closure revision, as expected);
* `git rev-parse github/p8-release-reconciled` = the same SHA; `git rev-list --left-right --count HEAD...github/p8-release-reconciled` = `0 0`;
* working tree clean (no modified/untracked files).

No discrepancy with the expected state was found, so the investigation proceeded. Bounded commit context:

| Revision | Meaning |
| --- | --- |
| `4887c66` | I5 closure (I6 implementation baseline) |
| `09e2315` | I6 UI implementation |
| `ea7ccc2` | I6 report revision |
| `4acc249` | I6 OHD independent verification (`I6 VERIFIED PASS`) |
| `67d399f` | I6 PO closure (`I6 — UI: CLOSED — VERIFIED PASS`) |

## 3. Scope and authorization boundary

**This is a forensic investigation.** It establishes the current repository reality and identifies the smallest future implementation boundary. It performs and authorizes **no** implementation.

Explicitly, this analysis does **not** authorize:

* I7 (privacy / retention / export);
* I8 (billing / production hardening);
* an I3 tool extension (including any by-identifier `evidence_line_item` lookup);
* an evidence viewer (any new viewer, route, component or API);
* any change to the `evidence_line_item` contract, schema, RLS or migrations;
* any change to extraction, mapping, calculation, storage, audit or the I6 UI.

Nothing in this report is a PO decision. §32 lists what a PO would have to decide; §27 states the minimum future architecture **as an architectural finding only**.

## 4. Governing Phase 8 context

Read and applied as governing context:

| Document | Relevance |
| --- | --- |
| `docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` | global decisions (references are locators, never grants; no new tools without a PO decision; §14 non-authorizations) |
| `docs/architecture/CARBONTALLY_P8_I3_INSIGHT_CLOSURE_20260921.md` | the closed four-tool catalogue and `ToolStatus` |
| `docs/architecture/CARBONTALLY_P8_I4_INSIGHT_CLOSURE_20260921.md` | deterministic-first orchestration, Layer-2 evidence, canonical audit |
| `docs/architecture/CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` | bounded current-conversation context (unaffected by this analysis) |
| `docs/architecture/CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` | I6 `CLOSED — VERIFIED PASS`; the four accepted PO follow-ups (incl. `evidence_line_item` resolvability) |
| `docs/implementation/phase8/CT-P8-I6-OHD-VERIFICATION-20260922.md` | independent confirmation that the `evidence_line_item` reference kind has no ratified by-identifier tool |
| `docs/architecture/CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md` | §14 answer vocabulary, §15.4 tokens/cost, reference kinds, I6 stage status |

Supporting architecture contracts cited by the code itself (read for the boundaries they impose, not as proof of current behaviour): `CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` (evidence line-item addressability, §7/§11/§12/§13.2), `CARBONTALLY_PHASE8_B1_*` (disclosure foundation), `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` (DM-6 drill-down matrix), `CARBONTALLY_PHASE8_P1_PDF_IMAGE_EXTRACTION_REMEDIATION_CONTRACT_20260913.md` (P1 per-line provenance).

## 5. Customer scenario (the question to be answered by evidence)

> *"Why did I have 20K CO₂e emissions on February 2, 2024? Can CarbonTally Insight find the exact invoice (PDF, image, XLS, or CSV) and locate the exact line/row of that invoice that supports the emission?"*

Three separable questions are hidden in it, and the forensic answer differs for each (§22–§24):

1. can CarbonTally determine **which** extracted/mapped data supports the calculation? (evidence tracing)
2. can CarbonTally **show** the original document for that data? (source-document viewing)
3. can **Insight** identify that evidence and take the customer to it? (Insight navigation)

**[VERIFIED] The scenario as phrased cannot be answered end-to-end today.** The blocking links are in §26. Concretely, verified: (a) a customer **can** reach an evidence record and a signed source-document URL for an existing emission (§9, §11), (b) the evidence record's "exact location" is at best a document-level page value (§14), and (c) Insight cannot start from "an emission on a date" and cannot open a document at all (§20).

## 6. Existing document ingestion / extraction

**[VERIFIED] Ingestion and extraction exist and are multi-format.** Key paths and symbols:

| Concern | Evidence |
| --- | --- |
| Upload + OCR + document reads | `backend/api/v3_documents.py`: `POST /api/v3/documents/uploads` (L211), `POST /api/v3/documents/uploads/{file_id}/ocr` (L513), `GET /api/v3/documents/documents` (L545), `GET /api/v3/documents/documents/{file_id}` (L560), `GET …/{file_id}/signed-url` (L573), `GET …/{file_id}/emissions` (L597), batches (L650–673) |
| Deterministic extraction (PDF / image / CSV / XLSX) | `backend/services/automatic_extraction.py` — `_extract_csv` (L731), `_xlsx_sheet_result` (L771, bounded to 5 sheets by `_XLSX_SHEET_SCAN_LIMIT` L768), `_rows_to_line_items` (L667) |
| Per-row provenance (CSV/XLSX) | `_rows_to_line_items` stamps **`source_row` = 1-based data-row index** on every record (L673–683); CSV adds `extracted_data["source_headers"]` (L747); XLSX adds `source_headers` + **`source_sheet`** + `sheet_names` (L786–788) |
| PDF/IMAGE per-line provenance (P1) | `backend/services/extraction_fidelity.py` `build_line_items` (L415) stamps per line: **`page`**, `page_basis`, `page_trust`, `extraction_method`, `line_number`, `source_line`, `description`, and carries the document's `invoice_number` |
| P1 gating | `backend/services/automatic_extraction.py` `_apply_p1_fidelity` (L378): per-line `line_items[]` are emitted **only** in `MODE_ENABLED` **and** when the document is `multi_line_suspect` (L429–441); the default is `shadow` (`shape_mode`, L409) |
| AI/LLM extraction path | `backend/services/ai_document_extraction.py` (prompt L169; parsed `line_items` L248; `{"line_items": lines}` L262) |
| OCR | v3 documents OCR endpoint (L513) + `automatic_extraction` OCR method strings (`onnx_ocr`, L373) |
| **OCR coordinates / regions** | **NOT FOUND** — a search of `backend/services`, `backend/pdf_engine.py` and `backend/api/v3_documents.py` for `bbox`, `bounding_box`, `coordinate(s)`, `polygon`, `regions` returned **no matches**. Text/line/quantity/unit/page/row/sheet keys are the entire provenance vocabulary |

**[VERIFIED] Ingest → extraction identity.** `manual_extraction_items` is the extraction record (its `extracted_data` JSONB holds the flat record or `line_items[]`), `manual_extraction_batches` groups items per organisation, and `organization_files` is the source document. D33 linked them structurally: `manual_extraction_items.file_id → organization_files(id) ON DELETE SET NULL` (`supabase/migrations/20260823010000_d33_evidence_traceability.sql` L66–92).

## 7. Existing mapping

**[VERIFIED]** Mapping is deterministic and line-aware in the automatic pipeline, and it is persisted next to the extraction it came from:

| Concern | Evidence |
| --- | --- |
| Mapping stage | `backend/services/automatic_processing.py` — tabular documents map `line_items` positionally (`mapped_data = {"line_items": mapped_lines}`, L1498–1503; targets chosen by `line_items = extracted.get("line_items") or []`, L1342–1343, L1716–1717) |
| Line ↔ mapped line alignment | `_calculate_line` uses `mapped.get("line_items")[idx]` when tabular, else the flat mapping (L1839–1846) |
| Mapping source text | `_mapping_input_text(line)` (L1883) — the row's own literal source text is the mapping input (CL-57) |
| Factor resolution | `factor_id` from the mapped line, falling back to `customer_factors` when the factor is a customer factor (L1847–1857) |
| Mapping record | `manual_extraction_items.mapped_data`, and the processing job's `mapped_data` (`job.mapped_data`, L1819) |

**[PARTIALLY VERIFIED]** There is **no per-line mapping identifier**: a mapped line is addressed by its **ordinal position** in `mapped_data.line_items[]`, and by the extraction item it belongs to (`manual_extraction_items.id`, i.e. the snapshot's `source_item_id`). No `mapped_line_id` exists in the schema or the code.

## 8. Existing calculation evidence

**[VERIFIED] The calculation snapshot is the authoritative evidence record and it carries source provenance.**

| Concern | Evidence |
| --- | --- |
| Snapshot table | `public.calculation_snapshots` — `supabase/migrations/20260807020000_add_calculation_snapshots.sql` (L21) |
| D33 lineage columns | `20260823010000_d33_evidence_traceability.sql`: `ADD COLUMN IF NOT EXISTS source_item_id uuid, source_file text, source_page integer` on `calculation_snapshots` (L61–64), FK `source_item_id → manual_extraction_items(id)` (L77–81), index `idx_calculation_snapshots_source_item` (L95) |
| B2 line linkage | `20260916010000_p8_b2_provenance_line_links.sql`: `calculation_snapshots.source_line_item_id → evidence_line_items(id) ON DELETE SET NULL` (L42–61) + `idx_calculation_snapshots_source_line_item` |
| Factor provenance | `20260810020000_v3m3_customer_factors.sql` (L169–203) — `factor_id`, `factor_kind`, `customer_factor_id`, `factor_source` (AGENTS.md §15) |
| Actor provenance | `20260905000000_gate4_actor_provenance.sql` (L28–44) |
| Snapshot columns | `backend/data/emissions_logs.py` `_LOG_COLUMNS_L` (L57) includes `source_item_id, source_line_item_id, source_file, source_page, performed_by`; insert L464; joined read L324, L494–495 |
| Engine contract | `backend/engines/calculation.py` — `CalculationRequest.source_file/source_page` (L165–166, L279–280), forwarded (L335–336, L505–506) |
| Snapshot ↔ line resolution | `backend/services/automatic_processing.py` `_calculate_line` (L1809–1914): for tabular documents it resolves `evidence_line_items.get_by_ordinals(source_item_id, [idx + 1])` (L1827–1832) and passes `source_line_item_id` into the request (L1909) — a **lookup, never an insert**, best-effort (unresolvable ⇒ link NULL) |
| Workflow path | `backend/engines/workflow.py` (L631) sets `source_file=run.document.filename` |

**[VERIFIED — material accuracy defect, pre-existing, not remediated here] `source_page` is written from the *document page count*, not the line's page.** `backend/services/automatic_processing.py` L1907:

```python
source_page=job.metadata.get("page_count"),
```

`page_count` is the document-level page count (`automatic_extraction.py` L374). Verified consequences:

* a line from page 1 of a 20-page invoice is recorded as `source_page = 20`;
* `backend/domain/evidence.py` `classify_evidence_completeness` (L21–51) treats `has_page` as the COMPLETE-vs-PARTIAL discriminator, so a page *count* can raise a record to **COMPLETE**;
* `backend/data/exports.py` (L54–58) applies the same rule to exports;
* B2 explicitly forbids that pattern for its own column — `20260916000000_p8_b2_evidence_line_items.sql` L102–103 (*"a genuine per-line page only. Never page_count (F-B2-7 is a separate workstream; B2-D4)"*) and `backend/domain/line_items.py` L17–19 — so the rule is understood and enforced in `evidence_line_items`, but the D33 snapshot column was populated from `page_count` independently.

**[VERIFIED] There is no `source_sheet` / `source_row` / `source_cell` / `source_location` column on `calculation_snapshots`** (grep of `supabase/migrations/**` for `source_location` returns only `backend/domain/evidence.py` + its tests). The generic locator model that *reads* those fields —

```python
loc = (snapshot or {}).get("source_location") or {}   # backend/domain/evidence.py L150
```

— has **no writer**, so the spreadsheet precision the model already supports (`source_location_precision(..., sheet, row, column, json_path)`, L54–103) is unreachable today.

## 9. Existing audit / evidence tracing

**[VERIFIED] A customer-facing, authorization-gated evidence record already exists end to end.**

| Layer | Evidence |
| --- | --- |
| API | `GET /api/v3/emissions/{log_id}/evidence` — `backend/api/v3_emissions.py` L372–510, `require_org_member()` + `ensure_org_access(current_user, log.organization_id)` (L393) |
| Documented chain | L380–384: *"emissions_log → calculation_snapshot → extraction item → source document (organization_files) → private-storage signed URL"* |
| Returned shape | `emission`, `calculation` (`shape_snapshot`), `source_item` (incl. `extracted_data`, `mapped_data`), `source_document` (incl. **`signed_url`**), `factor`, `customer_factor`, `evidence` (`source_item_id`, `source_file`, **`source_page`**, `signed_url`, `authorized_org`), `evidence_record` |
| Evidence model | `backend/domain/evidence.py` — `build_evidence_record` (L123); sections `source_document` and `extraction` are marked **`origin: original`**, `mapping` / `emission_factor` / `calculation` / `result` are **`derived`**; `technical_details` carries the stable ids + `source_file` + `source_page` + methodology + `content_hash` |
| Honest completeness | `classify_evidence_completeness` (L21–51) → COMPLETE / PARTIAL / UNAVAILABLE + reason |
| Source location | `source_location_precision` (L54–103) → `display`, `precision`, and an explicit *"page/location not available"* string when no locator exists (never fabricated) |
| Access audit | D33.1 append-only `evidence.access` entry with **ids only** (v3_emissions.py L431–453) |
| Consultant read | `GET /api/v3/consultants/clients/{client_id}/evidence` — `backend/api/v3_consultants.py` L1352 |
| Evidence-line audit | `backend/domain/line_items.py` L77–87: `report:evidence_line_items_materialised` / `_backfilled` / `_divergence_detected`, written through the existing `data.audit.AuditRepository` into `public.audit_trail` |
| Canonical ledger | `public.audit_trail` + `backend/data/audit.py`, `backend/api/admin_audit.py`, frontend `frontend/src/v3/admin/AuditTab.jsx` |
| Customer UI trigger | `frontend/src/v3/customer/EmissionsPage.jsx` — per-row **"View evidence"** button (L216) → `getEmissionEvidence(row.id)` (L43–48; client `frontend/src/v3/api.js` L1282) → `<EvidenceRecordPanel evidence={…}/>` (L231) |
| Evidence presentation | `frontend/src/v3/components/EvidenceRecordPanel.jsx` — completeness badge + reason (L19–23), source-location line (L24–26), derived sections, **"Original source data — from the document"** (L62–69), **"Open source document"** link to the signed URL (L70–76), and a *Technical details / Evidence record* expansion including **Source page** (L87–89) |
| Evidence trail (D33) | `frontend/src/v3/components/EvidenceTrail.jsx` — timeline built from `evidence_record.sections`; never fabricates a step for absent data (L45) |
| Phase 7 assurance | `E7` consultant evidence view (`frontend/src/v3/api.js` L517–521) and the auditor/assurance surface (api.js L1325) |

**[VERIFIED] "Which extracted/mapped data supports a calculation?" is therefore already answerable today** for an emission/snapshot: `source_item_id` → `manual_extraction_items` → `file_id` → `organization_files` → signed URL, with the §8 caveats (`source_page` semantics) and the §10 caveat (line-level identity only where lines were materialised).

## 10. `evidence_line_item` trace

The I6 OHD verification recorded that `evidence_line_item` is a ratified reference kind with **no ratified by-identifier tool**. The deeper repository reality is:

### 10.1 Schema representation — [VERIFIED]

`public.evidence_line_items` (`supabase/migrations/20260916000000_p8_b2_evidence_line_items.sql` L61–88):

| Column | Type / constraint |
| --- | --- |
| `id` | `uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4()` |
| `organization_id` | `uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE` |
| `source_item_id` | `uuid NOT NULL REFERENCES manual_extraction_items(id) ON DELETE RESTRICT` (B2-D1) |
| `source_file_id` | `uuid REFERENCES organization_files(id) ON DELETE SET NULL` |
| `line_number` | `integer NOT NULL CHECK (>= 1)` — 1-based ordinal in the persisted `extracted_data.line_items[]`; never renumbered, gaps preserved |
| `source_page` | `integer` (CHECK `IS NULL OR >= 1`) — *"a genuine per-line page only. Never page_count"* (L102–103) |
| `row_reference` | `text` — *"a genuine printed source reference only; NULL for Class-1 materialisation"* (L104–105) |
| `raw_description` / `raw_quantity` / `raw_unit` | the source line's own values, as extracted (pre-normalisation) |
| `payload_hash` | `text NOT NULL` — sha256 of the canonical line payload (divergence detection) |
| `extraction_method` | `varchar NOT NULL DEFAULT 'unknown'` — open vocabulary |
| `materialisation_kind` | `varchar NOT NULL CHECK IN ('FORWARD','BACKFILL')` |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` |
| Identity | `evidence_line_items_identity_unique UNIQUE (source_item_id, line_number)` |
| Indexes | `idx_eli_org`, `idx_eli_source_file` |
| RLS / grants | RLS enabled; exactly two **SELECT-only** policies (`evidence_line_items_org_select` via `p8_disclosure_is_org_member`; `evidence_line_items_entity_select` mirroring the PE item boundary); `anon` none, `authenticated` SELECT only, `service_role` ALL; append-only (no UPDATE/DELETE/trigger — `backend/data/evidence_line_items.py` L15–18, L565–570) |

### 10.2 Backend / domain representation — [VERIFIED]

* `backend/domain/line_items.py` — pure derivation: `derive_line_candidates(extracted_data)` (L233), `LineCandidate` (L203), `compute_payload_hash` (L151), `decide_ordinals` (INSERT / SKIP_EXISTS / DIVERGENCE, L304).
* Per-line optional interface (L52–55): `page` → `source_page`; **`line_reference`** → `row_reference`; `extraction_method` → per-line override. The header states these are *"the complete B2↔P1 interface; **none has a producer today**"* (L51–55).
* `backend/data/evidence_line_items.py` — append-only repository: `materialise_for_item` (L333) + Class-1 `backfill` (L473); read surface `list_for_item` (L287), **`get(id)` (L300)**, `get_by_ordinals` (L307), `count_for_item` (L322).
* Forward hook: `backend/data/manual_extraction.py` `_materialise_evidence_lines` (L457–486), called after the extraction UPDATE succeeds; deliberately best-effort (never fails a save), with the idempotent backfill (`backend/tools/backfill_evidence_line_items.py`) as the safety net. Repository exposed on the bundle (`backend/api/dependencies.py` L337, L404).
* Eligibility: only items whose persisted `extracted_data.line_items` is an array (`domain/line_items.py` L242–248). **A flat/single-record extraction is ineligible and yields no lines** (§11.1).

### 10.3 I3 / I4 / frontend representation — [VERIFIED]

* I3 reference kind: `backend/domain/insight_tool.py` `REFERENCE_KINDS` (L55–60) includes `evidence_line_item`.
* I3 projections: `backend/services/insight_tools.py` — `_EVIDENCE_LINE_FIELDS` (L66–69) = `disclosure_value_id, requirement_version_id, calculation_snapshot_id, evidence_line_item_id, line_number, materialisation_kind`; `report_evidence_lookup` requires **`report_version_id`** (L102–110); `_SNAPSHOT_FIELDS` (L75–81) include `source_item_id` and `source_line_item_id` but **not** `source_file` / `source_page` (deliberate: L73–74 *"not named — omitted, not inferred"*).
* I4 records only allowlisted projections (`backend/domain/insight_interaction.py` `project_tool_arguments` / `project_result_metadata`); it never carries the line payload.
* Bridge: `backend/data/disclosure_projection.py` `value_lines` (L186–200) is the B2 join producing `evidence_line_item_id`, `line_number`, `source_page`, `raw_*` for a report version — this is what I3 consumes.
* Frontend: `frontend/src/v3/insight/references.js` renders the kind as a locator and deliberately declares it unresolvable (`IDENTIFIER_TOOL` has no `evidence_line_item` key).

### 10.4 The six required determinations

| Question | Determination |
| --- | --- |
| 1. merely a locator? | **NO — richer.** `evidence_line_items` is a persisted, immutable, append-only **entity** with its own id, organisation, payload hash and audit trail. It is *also* used as an Insight reference locator. |
| 2. linked to an actual persisted extracted row? | **YES — [VERIFIED].** `source_item_id` + `line_number` address the element inside `manual_extraction_items.extracted_data.line_items[]`; uniqueness enforced by `evidence_line_items_identity_unique`. |
| 3. linked to an original document? | **YES — [VERIFIED].** `source_file_id → organization_files(id)` (nullable, SET NULL), indexed `idx_eli_source_file`. |
| 4. already resolvable through an existing service/API? | **PARTIALLY — [VERIFIED].** Data layer: `get(id)`, `get_by_ordinals`, `list_for_item` exist. HTTP: the **only** line-level reads are (a) `GET /api/v3/reports/{report_id}/disclosure/{value_id}/lines` (DM-6 drill-down, `backend/api/v3_disclosure.py` L226–276) and (b) the I3 `report_evidence_lookup` tool, which needs a **report version id**. **No endpoint accepts an `evidence_line_item` id**, and no endpoint returns a line's `source_file_id`. |
| 5. already visually represented elsewhere? | **PARTIALLY — [VERIFIED].** Customers see the D33 evidence record (`EvidenceRecordPanel`) and the D33 trail (`EvidenceTrail`) — both **item/snapshot-level**, not line-level. The DM-6 line drill-down API has **no frontend consumer at all**: a grep of `frontend/src` for `disclosure` finds only public marketing copy plus the I6 label map (`frontend/src/v3/insight/references.js` L134). The D19 workbench shows the document beside structured data, but not keyed to an evidence line. |
| 6. currently impossible to resolve without new backend capability? | **YES for by-id resolution — [VERIFIED].** Resolving one `evidence_line_item` id (e.g. from an Insight reference) to its line/document needs either a new by-id read endpoint or an I3 tool — a PO decision. Resolution *by report version* (I3) and *by ordinal within an item* (calculation path) already work today. |

## 11. Existing source-document storage / access

**[VERIFIED]**

| Concern | Evidence |
| --- | --- |
| Bucket / privacy | `backend/services/storage.py` — `DOCUMENTS_BUCKET = "documents"` (L27), module doc: *"D32 makes the bucket PRIVATE and serves objects only through short-lived SIGNED URLs"* (L4–6) |
| Signed URL issuance | `storage_signed_url(path, expires_in=SIGNED_URL_TTL_SECONDS)` (L58–72); `SIGNED_URL_TTL_SECONDS = 3600` (L30) |
| Path handling | `path_from_url` (L36–55) normalises legacy public URLs, signed URLs and bare paths |
| Work-item signing | `signed_item(item)` (L75–82) — fresh signed `file_url` for ops/customer workspace responses |
| Customer document read | `GET /api/v3/documents/documents/{file_id}` (v3_documents.py L560) and `GET …/{file_id}/signed-url` (L573–594) — both `require_org_member()` + `ensure_org_access(current_user, doc.organization_id)`, returning `{url, expires_in_seconds: 3600}` |
| Evidence-path signing | `GET /api/v3/emissions/{log_id}/evidence` returns `source_document.signed_url` and `evidence.signed_url` (v3_emissions.py L495, L506) |
| PE / ops signing | `signed_item` used by ops surfaces; `backend/tests/unit/api/test_v3_operations.py` L799 asserts *"ops batch items returns signed urls not raw paths"* |
| Signed-URL hygiene | `test_disclosure_b4_finalisation_runtime.py` L470–489 asserts the signed URL is **audited without recording the URL**; `test_disclosure_b3_v3_security.py` L344 asserts `signed_url` never appears in a payload/log |
| Legacy path | `backend/routes/upload.py` L437, L639 still call `get_public_url` for the legacy upload route (`backend/routes/organizations/files.py` L581 likewise); `path_from_url` explicitly tolerates legacy public URLs (L38–50) |

**[VERIFIED] An authenticated customer organisation member can already fetch their own organisation's original source document** as a 1-hour signed URL — both directly (documents route) and through the evidence-record response. Signed URLs are issued only **after** an authorization check, and they are treated as secrets in tests and audit.

## 12. Existing document viewer

**[VERIFIED] A source-document viewer exists, but only inside the D19 processing workbench.**

`frontend/src/v3/components/workbench/SecureDocumentViewer.jsx` (122 lines):

| Behaviour | Evidence |
| --- | --- |
| Type classification | `detectKind(title, src)` (L33–40): `.pdf` → `pdf`; `.png/.jpg/.jpeg/.gif/.webp/.bmp/.tif/.tiff` → `image`; `.csv/.xlsx/.xls/.tsv` → `data`; else `other` |
| PDF | non-sandboxed `<iframe src={signedUrl}>` (L95–104) — Chromium's PDF viewer cannot run in a sandboxed frame (P0-1 comment L7–12) |
| Image | sandboxed `<iframe>` (`sandbox="allow-same-origin"`, L49) |
| CSV / TSV / XLSX | **not framed** — delegated to `StructuredDataPreview` (L61–77) |
| Unknown type | explicit placeholder *"Document preview is not available for this file type."* (L79–91) |
| No document | explicit empty state *"No source document available for this item."* (L51–59) |
| Controls | **zoom only** (L43, 106–112) plus the view-only/no-download affordance when `allowDownload` is false (L113–118) |
| **Page navigation** | **NOT FOUND** — no page control, page number, `#page=` fragment or `<Page>` selection exists in the component |
| **Highlight / scroll-to-location** | **NOT FOUND** — no prop, state or attribute for a page/line/row target |
| Callers | `frontend/src/v3/components/workbench/WorkbenchShell.jsx`, and through it `frontend/src/v3/ops/ExtractionPanel.jsx` (L436), `frontend/src/v3/ops/WorkItemWorkspace.jsx` (L108), `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` (L894), `frontend/src/v3/customer/ReviewDetailPage.jsx` |

**[VERIFIED] The customer evidence path differs:** `EmissionsPage` → `EvidenceRecordPanel` does **not** embed a viewer; it presents an **"Open source document" anchor to the signed URL** (`EvidenceRecordPanel.jsx` L70–76), opening the file in a new browser tab. A customer can therefore *open* the document today, but not *inside* an evidence view, and not at a located position.

## 13. Existing extracted-data viewer

**[VERIFIED] A read-only extracted/mapped representation exists — the workbench's right-hand pane.**

`frontend/src/v3/components/workbench/StructuredDataPreview.jsx` (154 lines):

* parses CSV/TSV text (bounded) and XLSX via SheetJS — first worksheet only (`sheet_to_json(..., { header: 1 })`, L80);
* caps the preview (`MAX_PREVIEW_ROWS`, `MAX_PREVIEW_COLUMNS`; `body.slice(0, MAX)`, L60) and states the total (L113, L132);
* renders a plain `<table>` — headers from the first row, then body rows (`<tr key={`r-${rIndex}`}>`, L142–147).

**[NOT FOUND]** in `StructuredDataPreview`: row numbers, worksheet-name display, cell references (`A1`), row highlighting, or any "scroll to row" input. **[VERIFIED]** extracted/mapped JSON is also displayed on the workspace pages (e.g. `ProcessingItemWorkspace`, `ReviewDetailPage`, and `evidence_record.sections.extraction`/`.mapping` inside `EvidenceRecordPanel`) — always as *values*, never keyed to a document position.

## 13.1 The required per-file-type matrix

| Source | Existing original-file viewer? | Existing extracted view? | Exact source locator? | Existing linkage? |
| --- | --- | --- | --- | --- |
| **PDF** | **PARTIALLY VERIFIED** — embedded `<iframe>` viewer inside the D19 workbench only; the customer evidence view offers a new-tab link, not an embedded viewer | **VERIFIED** — extracted/mapped values shown in the workbench and in the evidence record | **PARTIALLY VERIFIED** — a *page* exists in `extracted_data.line_items[].page` (P1, gated) and in `evidence_line_items.source_page`, but `calculation_snapshots.source_page` holds the **document page count** (§8) and no line-level page reaches the customer evidence record | **PARTIALLY VERIFIED** — snapshot → item → document links exist; page→viewer highlighting does not |
| **Image** | **PARTIALLY VERIFIED** — sandboxed iframe in the workbench only; no OCR-region rendering | **VERIFIED** (as PDF) | **PARTIALLY VERIFIED** — P1 assigns `page` (1 for a single-page image) when enabled; **no OCR coordinates/regions exist anywhere** (§6) | **PARTIALLY VERIFIED** (as PDF) |
| **XLS/XLSX** | **PARTIALLY VERIFIED** — not the original workbook; `StructuredDataPreview` renders the **parsed first sheet** (bounded) | **VERIFIED** — parsed rows/headers, plus `extracted_data.source_headers` / `source_sheet` / `sheet_names` | **PARTIALLY VERIFIED** — `source_row` (per line) and `source_sheet` exist in `extracted_data`; `evidence_line_items.row_reference` is **NULL** (its reader expects `line_reference`, which nothing emits); no sheet/row/cell column exists on snapshots | **NOT FOUND** — no sheet/row/cell reaches the snapshot, the evidence record or any viewer step |
| **CSV** | **PARTIALLY VERIFIED** — parsed preview, not the original bytes | **VERIFIED** — parsed rows/headers | **PARTIALLY VERIFIED** — `source_row` per line; `source_headers` preserved; `row_reference` NULL as above | **NOT FOUND** (as XLSX) |

**[PARTIALLY VERIFIED — precise reader/producer mismatch]** B2 reads `element["page"]` → `source_page` (`backend/domain/line_items.py` L178–183) and `element["line_reference"]` → `row_reference` (L186–189). The only per-line producers emit `page` (P1), `source_row` and `source_line` (CSV/XLSX). Therefore:

* `evidence_line_items.source_page` **can** be populated when P1 line items are persisted (key matches);
* `evidence_line_items.row_reference` is **always NULL** today, because **no code emits `line_reference`** — its only repository occurrences are the reader, its unit tests, and the contract/audit documents that record it as producer-less (`docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` L745, L1455; `backend/tests/unit/domain/test_evidence_line_items.py` L195, L215, L229).

## 14. PDF provenance

**[PARTIALLY VERIFIED]** Verified representation today:

1. **Per line, in the extraction** — `extracted_data.line_items[].page` (int ≥ 1) plus `page_basis` (`marker`/`text`), `page_trust` (`lower`/`standard`), `extraction_method`, `line_number`, `source_line`, `description`, and the carried `invoice_number` — produced by `backend/services/extraction_fidelity.py` `build_line_items` (L415–479) and applied by `_apply_p1_fidelity` (`automatic_extraction.py` L378–441) **only when P1 mode is `enabled` and the document is multi-line-suspect**.
2. **Per line, addressable** — `evidence_line_items.source_page`, materialised from the same `page` key by the B2 forward hook / backfill.
3. **On the calculation snapshot** — `source_file` (file **name**) and `source_page`, the latter set from `job.metadata["page_count"]` (§8), i.e. a document-level value.
4. **In the evidence record** — `technical_details.source_page` and `source_location.display` ("page N" when non-null).

Missing for the scenario: a **line-level** page that reaches the customer evidence record; any region/coordinate for a scanned page; and any viewer capability to open or scroll to that page (§12).

## 15. Image provenance

**[PARTIALLY VERIFIED]** Images share the PDF path: the P1 fidelity hook is explicitly applied to the image path as well as PDF (`automatic_extraction.py` `_apply_p1_fidelity` docstring, L396–399: *"this hook is applied to both the PDF path and the IMAGE path"*). Consequences: an image line can carry `page` (typically `1`) and the same per-line keys; otherwise identical to §14.

**[NOT FOUND]** — OCR **region/coordinate** provenance of any kind (`bbox`, `bounding_box`, `coordinates`, `regions`, `polygon`) across `backend/services`, `backend/pdf_engine.py`, `backend/api/v3_documents.py`. So "highlight the exact region of a scanned invoice" has **no data foundation today**.

## 16. XLS/XLSX provenance

**[PARTIALLY VERIFIED]** The extractor produces real workbook provenance, but it is **not addressable downstream**:

* `extracted_data.source_sheet` = the parsed worksheet title; `extracted_data.sheet_names` = the workbook's sheet names; `extracted_data.source_headers` = the verbatim header row (`automatic_extraction.py` L786–788);
* every line item carries `source_row` = 1-based **data-row** index (header excluded) — `_rows_to_line_items` L673–683; the docstring states the intent explicitly: *"a parsed line can always be traced back to its position in the original file"* (L673–675);
* the sheet scan is bounded (first 5 sheets) and the row order of `line_items` matches the file's row order (L675, L764–768).

**[NOT FOUND] / gaps (all verified):**

* `evidence_line_items` has **no sheet/row/cell column**, and its `row_reference` (the only text locator) is always NULL because its reader key (`line_reference`) has no producer (§13.1);
* `calculation_snapshots` has no sheet/row/cell column, and the `source_location` field its reader expects has **no writer** (§8), so `source_location_precision(sheet=…, row=…, column=…)` always receives `None` in the real chain;
* no frontend surface displays or accepts a worksheet/row/cell locator (§12, §13).

## 17. CSV provenance

**[PARTIALLY VERIFIED]** Same shape as XLSX minus sheets: `source_headers` preserved verbatim (`automatic_extraction.py` L745–747) and `source_row` per line (L673–683). **[NOT FOUND]** the same downstream gaps: no CSV row number reaches `evidence_line_items.row_reference` (NULL), no snapshot location column, and no viewer that could highlight a row.

**[VERIFIED] A partial substitute exists:** `evidence_line_items.line_number` — the 1-based ordinal of the element in `extracted_data.line_items[]` — is persisted and is the only line locator that survives to the database for CSV/XLSX. Because the extractor skips blank rows, that ordinal is *related to* but **not guaranteed to equal** the literal file row number.

## 18. Existing evidence APIs

| Route | File / symbol | Authorization | Returns |
| --- | --- | --- | --- |
| `GET /api/v3/emissions/{log_id}/evidence` | `backend/api/v3_emissions.py` L372 (`emission_evidence`) | `require_org_member()` + `ensure_org_access` | full D33 evidence record + signed URL (§9) |
| `POST /api/v3/emissions/calculations/{snapshot_id}/verify` | `backend/api/v3_emissions.py` L513 (`verify_calculation`) | org member | reproducibility check of a stored snapshot |
| `GET /api/v3/consultants/clients/{client_id}/evidence` | `backend/api/v3_consultants.py` L1352 | consultant grant | client evidence history |
| `GET /api/v3/reports/{report_id}/disclosure` | `backend/api/v3_disclosure.py` L195 | org member + `_authorize_read` | disclosure values for the current version |
| **`GET /api/v3/reports/{report_id}/disclosure/{value_id}/lines`** | `backend/api/v3_disclosure.py` L226 (`get_disclosure_value_lines`) | org member + `_authorize_read` + **DM-6** role depth | **evidence lines** (`evidence_line_item_id`, `line_number`, `source_page`, `raw_*`, `materialisation_kind`) projected to the caller's depth |
| `POST /api/v3/reports/{report_id}/disclosure/project` | L282 | org **write** (`_authorize_write`) | (re)project disclosure values |
| `GET /api/v3/reports/{report_id}/frozen-artefact` / `POST …/signed-url` | L635, L659 | org member | frozen report artefact + **audited** signed URL |
| `GET /api/v3/documents/documents/{file_id}/signed-url` | `backend/api/v3_documents.py` L573 | org member + org access | 1-hour signed URL for the original document |
| `GET /api/v3/documents/documents/{file_id}/emissions` | L597 | org member | emissions produced from one document |
| Ops / PE equivalent | `backend/api/v3_operations.py` (e.g. `GET /items/{item_id}/workspace` L1496, `POST /items/{item_id}/calculate` L1812) | staff / PE scope | work-item workspace incl. signed `file_url` |

**[NOT FOUND]** any route that (a) accepts an `evidence_line_item` id, (b) lists evidence lines for an **emission log** or **snapshot** (only per **report value**, and per I3 report version), or (c) exposes a line's `source_file_id`.

## 19. Existing I3 tools

**[VERIFIED]** The catalogue is closed at four tools (`backend/services/insight_tools.py` L83–120). Evidence-relevant characteristics:

| Tool | Required input | Evidence-relevant output | Reference kinds |
| --- | --- | --- | --- |
| `report_lookup` | `report_id` | report + version summary + lifecycle | `report`, `report_version` |
| `report_version_lookup` | `version_id` or `report_id` + `version_number` | version identity + lifecycle | `report_version`, `report` |
| `report_evidence_lookup` | **`report_version_id`** | `report_version`, `lines` (`disclosure_value_id`, `requirement_version_id`, `calculation_snapshot_id`, **`evidence_line_item_id`**, `line_number`, `materialisation_kind`), `coverage` (`reference_count`, `line_linked_count`, `snapshot_linked_count`) | `report_version`, `evidence_line_item`, `calculation_snapshot` |
| `calculation_snapshot_lookup` | `snapshot_id` | snapshot provenance incl. **`source_item_id`**, **`source_line_item_id`**, factor fields, `co2e_kg`, `methodology`, `content_hash` | `calculation_snapshot`, `evidence_line_item` |

**[VERIFIED] Deliberate omissions:** `_SNAPSHOT_FIELDS` excludes `source_file` / `source_page` and the module says why (`insight_tools.py` L73–74: *"internal ingest identifiers, source_file/source_page (not named — omitted, not inferred)"*); `_EVIDENCE_LINE_FIELDS` excludes `source_page`, `raw_*` and `source_file_id`. Both tools are read-only, I2-gated and re-check the resolved object's organisation (PO §3.3; AGENTS.md §44).

**[VERIFIED] Consequence:** `report_evidence_lookup` yields **`evidence_line_item_id` + `line_number`** for a report version, and `calculation_snapshot_lookup` yields `source_line_item_id` for a snapshot — but **neither returns a document identifier or a page**, so an Insight answer containing these locators cannot be turned into "open the invoice" with today's tool vocabulary.

## 20. Insight integration path

**[VERIFIED] What happens today when the scenario question is asked.**

| Step | Current behaviour (verified) |
| --- | --- |
| Question received | `POST /api/v3/insight/interactions` → `services/insight_interactions.run_interaction` persists the raw question as an I1 message, then classifies intent **deterministically** |
| Intent routing | `services/insight_tools.classify_intent` (L157–173) keyword-matches: `version/revision/superseded/which draft` → `report_version_lookup`; `evidence/source line/backing/supporting/audit trail` → `report_evidence_lookup`; `calculation/snapshot/emission factor/factor used/co2e/kg co2` → `calculation_snapshot_lookup`; `report/summary document` → `report_lookup`. Two matches ⇒ `invalid_input` (ambiguous), no match ⇒ `invalid_input` (unsupported) |
| Input scoping | `build_tool_input` (L179–190) takes the **first UUID found in the question** (`extract_identifiers`, `_UUID_RE`, L174–176). No id ⇒ `needs_clarification` (L366) — the tool is **not** called |
| Tools available for evidence | Only the four above. **There is no "emissions by date/amount/organisation" tool**, and no tool accepts a date, a CO₂e value or an emissions-log id |
| Result | Tool result + allowlisted projections + references → optional bounded narration → I4 answer state → canonical audit |
| I6 UI rendering | `frontend/src/v3/insight/InsightReferences.jsx` renders each reference as a locator; `report` / `report_version` / `calculation_snapshot` can be opened via `POST /api/v3/insight/tools/invoke` (through `invokeInsightTool`); `evidence_line_item` is declared **unresolvable** (no open control at all) |

**So, for the scenario question as phrased:** it contains no UUID ⇒ if it routes to `calculation_snapshot_lookup`, the answer state is `needs_clarification`; if it contains no routing keyword at all, the intent is `unsupported_intent` → `invalid_input`. Either way **Insight cannot start from "an emission on 2024-02-02"**. It can only start from an identifier the customer already has (a report id, version id, or snapshot id), and even then it returns **locators**, never a document.

**[VERIFIED] What the current four tools *could* contribute (if the customer supplies an id):**

* `calculation_snapshot_lookup(snapshot_id)` → `source_item_id`, `source_line_item_id`, factor provenance, `co2e_kg` — i.e. the **authoritative calculation** the customer is asking about;
* `report_evidence_lookup(report_version_id)` → the report version's lines with `evidence_line_item_id` + `line_number` + coverage counts.

**[VERIFIED] What is missing to finish the path:** the UI has no route from a locator to `/emissions/{log_id}/evidence` (that endpoint takes an **emission log id**, which no I3 tool returns), no route to the document signed-URL endpoint, and no viewer that highlights the located line/row (§12, §13). No I3 tool returns `source_file_id`, a page, or a row.

## 21. I2 authorization / security implications

**[VERIFIED] Existing authorization that already governs source-document evidence access:**

| Boundary | Enforcement |
| --- | --- |
| Organisation isolation | `ensure_org_access` / `_authorize_read` / `_authorize_write` on every evidence/document route; RLS on `evidence_line_items`, `calculation_snapshots`, `organization_files` |
| Creator-private Insight | I1/I4 `conversation_is_visible` (org **and** creator) — a reference can never be shared between users |
| Reference ≠ grant | PO §3.3: references are locators; I3 re-authorizes the resolved object's organisation on every call |
| Evidence-line exposure | **DM-6 matrix** (`backend/domain/disclosure_exposure.py`): Owner/Admin → `FULL` (lines + amounts + document refs + download); Member/Viewer (and generic `user`) → `CONTROLLED` (structural keys + amounts, **document references never exposed**); Consultant → `BOUNDED` (structural only); PE staff, internal staff, unrecognised roles → **`DENIED`** (403, never a partially redacted answer, L152–157) |
| Redaction shape | fail-closed allowlist; hidden keys are **removed** (not nulled) and reported in `redacted_fields` (`redact_line`, L178–197) |
| Source documents | private bucket; signed URLs issued only after an authorization check; 1-hour expiry; never logged or stored in audit (tests assert both) |
| PE boundary | `evidence_line_items_entity_select` mirrors the existing PE item boundary (B2-D3); PE has no Insight access at all (I2) |

**[VERIFIED] Answer to the question posed in this section:** the **existing** authorization model is *sufficient in kind* to govern a source-document evidence viewer — it already has (a) an organisation boundary, (b) a creator-private Insight boundary, (c) a role-depth evidence matrix with an explicit download flag, and (d) an audited signed-URL mechanism. Two consequences follow:

1. any viewer must consume these existing decisions rather than invent its own (e.g. a viewer must respect `allow_document_refs` / `allow_download` from DM-6, not just org membership);
2. the one decision the matrix does **not** settle is whether a **Controlled**-depth customer (Member/Viewer) should be able to open the *original document* at all — today DM-6 says **no** document references below `FULL`, while the D33 evidence endpoint's `source_document.signed_url` is exposed to **any** org member. That is a genuine, verified **inconsistency between two existing authorization postures** and needs a PO decision before a shared viewer is built (§32).

## 22. Capability 1 — evidence tracing

> Can CarbonTally determine which extracted/mapped data supports a calculation?

**VERDICT: VERIFIED — the capability exists and is substantial, with three bounded gaps.**

| Element | Status |
| --- | --- |
| Emission → snapshot | **VERIFIED** (`emissions_logs.snapshot_id`) |
| Snapshot → extraction item | **VERIFIED** (`calculation_snapshots.source_item_id`, D33 FK) |
| Extraction item → document | **VERIFIED** (`manual_extraction_items.file_id` → `organization_files`) |
| Snapshot → source **line** | **VERIFIED with conditions** — `source_line_item_id` resolved by ordinal for tabular documents (`automatic_processing._calculate_line`); NULL for flat records, pre-B2 history, or before materialisation |
| Document + evidence record + signed URL | **VERIFIED** (`GET /api/v3/emissions/{log_id}/evidence`) |
| Disclosure value → evidence lines | **VERIFIED** (`value_lines` join + DM-6 route + I3 `report_evidence_lookup`) |
| Exact page | **PARTIALLY VERIFIED** — `evidence_line_items.source_page` is genuine when P1 emitted `page`; `calculation_snapshots.source_page` is the **document page count** (§8) |
| Exact row / sheet / cell | **NOT FOUND** — producer data exists in `extracted_data` (`source_row`, `source_sheet`) but nothing carries it into evidence, snapshot or API |
| OCR region | **NOT FOUND** |
| Access audit of evidence reads | **VERIFIED** (`evidence.access`) |

## 23. Capability 2 — source-document viewing

> Can CarbonTally show the original PDF/image/XLS/CSV associated with that evidence?

**VERDICT: PARTIALLY VERIFIED — the ability to *open* a document exists; a *source-document evidence viewer* does not.**

* **[VERIFIED] Open, customer-facing:** `source_document.signed_url` in the D33 evidence response + the "Open source document" anchor (`EvidenceRecordPanel.jsx` L70–76) → the original file opens in a new browser tab. Also `GET /api/v3/documents/documents/{file_id}/signed-url`.
* **[VERIFIED] Embedded viewing exists but is workbench-only:** `SecureDocumentViewer` (PDF iframe / image iframe / CSV-XLSX parsed preview) is reachable only through `WorkbenchShell` (ops, PE, and the customer processing/review pages).
* **[NOT FOUND] The proposed design (document left, extracted/mapped evidence right, linked):** no component accepts a document + a locator and shows them together outside the workbench; the workbench shows document-beside-data but is **not** keyed to an evidence line, page or row.
* **[NOT FOUND] Location highlighting:** no page control, no scroll-to-line, no row/cell highlight, no OCR region — for PDF, image, XLSX or CSV.

## 24. Capability 3 — Insight navigation

> Can CarbonTally Insight securely identify that evidence and take the customer to the appropriate existing evidence/source view?

**VERDICT: NOT FOUND (as a navigation capability) — with a PARTIALLY VERIFIED foundation.**

* **[VERIFIED] The secure identification half exists in principle:** I3 tools return authoritative evidence locators (`evidence_line_item_id`, `line_number`, `calculation_snapshot_id`, `source_item_id`, `source_line_item_id`) and I6 renders them as locators with backend-authorized resolution for three of four kinds.
* **[NOT FOUND] The navigation half:** no link, route, deep-link or action goes from an Insight reference to `/emissions/{log_id}/evidence`, to the EmissionsPage evidence panel, to a document signed URL, or to any viewer. I6 has no emissions-log concept at all.
* **[VERIFIED] Blocked origins:** Insight cannot be entered from a date, an amount or an emissions record — only from an identifier present in the question (`build_tool_input`), because the closed catalogue has no emissions-lookup tool.
* **[VERIFIED] Blocked reference kind:** `evidence_line_item` — the kind that names the supporting line — is **not resolvable** from the UI and has no by-id backend route.

## 25. Shared evidence architecture assessment

**VERDICT: [INFERENCE] Yes — the repository already has the shared seams; an Insight-specific evidence implementation would duplicate four things that exist once today.**

Evidence that a shared design is the natural fit (all **[VERIFIED]**):

1. **One line model:** `evidence_line_items` is already the single addressable source-line entity, consumed by the calculation path (ordinal lookup), the disclosure projection (`value_lines`) and I3 (`report_evidence_lookup`). It is not Insight-specific.
2. **One provenance join:** `data/disclosure_projection.value_lines` materialises `disclosure value → snapshot → evidence line` once and is reused by both the DM-6 API and I3.
3. **One authorization policy:** DM-6 (`backend/domain/disclosure_exposure.py`) already expresses per-role evidence depth **including a download flag** — exactly the policy a viewer needs. A second policy would be a second source of truth.
4. **One storage-access mechanism:** `services.storage.storage_signed_url` (1-hour TTL) plus the audited-issue pattern (`frozen_artefact.signed_url_issued`) already define how a document is safely shown.
5. **One viewer primitive:** `SecureDocumentViewer` + `StructuredDataPreview` already classify and render PDF / image / CSV / XLSX safely, including the no-download boundary.

Duplication a second implementation would reintroduce (each verified as a **single** existing implementation): document-type classification and framing rules (`detectKind`), storage signing + TTL policy, structured-data parsing (SheetJS/CSV bounds), and the evidence-depth/redaction matrix.

**Architectural conclusion [INFERENCE]:** extend the existing evidence surface (one viewer component + one authorized locator contract) rather than building an Insight-only viewer; Insight should hand over a **locator** and let the shared viewer resolve it under DM-6. This is a finding only — §27 states what would be required, and none of it is authorized.

## 26. Missing capabilities

| # | Missing capability | Classification | Verified basis |
| --- | --- | --- | --- |
| M1 | A **line-level page** reaching the customer evidence record | PARTIALLY VERIFIED (producer exists; the wire is wrong) | `evidence_line_items.source_page` is genuine but `calculation_snapshots.source_page` = `page_count` (§8) |
| M2 | **Row / sheet / cell** locators in evidence or snapshot storage | NOT FOUND | `source_row`/`source_sheet` exist only inside `extracted_data`; no columns downstream (§16, §17) |
| M3 | **OCR region/coordinate** provenance | NOT FOUND | no bbox/region code anywhere (§15) |
| M4 | A **by-identifier read** of an `evidence_line_item` (with its document) | NOT FOUND | only `value_lines` (per report value) and I3 (per report version) read lines (§10.4, §18) |
| M5 | A customer-facing **embedded** source-document evidence viewer | NOT FOUND | the viewer is workbench-only; the customer path is a new-tab link (§12, §23) |
| M6 | **Location-aware** viewing (open at page / scroll to row / highlight cell) | NOT FOUND | no viewer prop or component supports a target location (§12, §13) |
| M7 | **Insight → evidence navigation** (locator → view) | NOT FOUND | no link/route; I6 has no emissions-log identity (§24) |
| M8 | An Insight entry point from a **date/amount/emissions record** | NOT FOUND | no emissions-lookup tool; input requires a question-borne UUID (§20) |
| M9 | A **producer for `line_reference`** (the only `row_reference` reader key) | NOT FOUND | no code emits it; `row_reference` is always NULL (§13.1) |
| M10 | A **settled authorization posture** for document viewing below DM-6 `FULL` | UNKNOWN → PO decision | DM-6 denies document refs below FULL, while the D33 evidence endpoint exposes `source_document.signed_url` to any org member (§21) |

## 27. Minimum future architecture (finding only — nothing authorized)

The smallest set of changes that would satisfy the scenario, derived **only** from repository evidence. Ordered by dependency, not preference.

### 27.1 Existing capability that can be reused unchanged

* `public.evidence_line_items` — schema, RLS, append-only repository, forward hook and backfill (no schema change needed for reuse);
* `public.calculation_snapshots.source_item_id` / `source_line_item_id` / `source_file` and their FKs;
* `GET /api/v3/emissions/{log_id}/evidence` (D33) including the evidence record and the signed-URL mechanism;
* `GET /api/v3/documents/documents/{file_id}/signed-url` and `services.storage.storage_signed_url`;
* the DM-6 exposure matrix (`exposure_for_role` / `project_lines`) as the authorization policy for any evidence disclosure;
* `SecureDocumentViewer` + `StructuredDataPreview` as the rendering primitives (extended, not replaced);
* `EvidenceRecordPanel` / `EvidenceTrail` as the customer-facing evidence presentation;
* the I4 interaction/audit contracts, the I5 context contract and the I6 workspace itself.

### 27.2 Missing capability (each item is a change; none is authorized here)

1. **Carry the line's own page** into the D33 evidence path instead of the document page count — i.e. take `evidence_line_items.source_page` for the resolved line (via `source_line_item_id`), and leave the value NULL when unknown. *Causes M1 and restores the honesty of the COMPLETE/PARTIAL classification.*
2. **Align or read the row locator that already exists conceptually:** either emit `line_reference` from the CSV/XLSX/P1 line builders (so B2's `row_reference` starts filling), or read the already-present `source_row` / `source_sheet`. *Causes M2/M9 — a key-alignment decision, not a new model.*
3. **Surface the workbook locator in the evidence record:** write the existing `source_sheet` / `source_row` into a snapshot location value (the reader — `source_location_precision(sheet, row, column)` — is already implemented and currently starved of data). *Causes M2; makes `EvidenceRecordPanel`'s precision line truthful for spreadsheets.*
4. **One authorized locator → evidence read** that accepts identifiers the system already mints (`evidence_line_item_id`, or `source_item_id` + `line_number`, or `snapshot_id`) and returns the line plus its document reference and locator, projected through DM-6. *Causes M4; the single most load-bearing new backend capability.*

### 27.3 Required new backend capability (in principle)

* **A locator-resolution read** (item 4). It could be realised as a **new/extended I3 tool** (a PO decision — the catalogue is closed at four) **or** as an existing-surface endpoint outside Insight (e.g. an evidence-line read under `/api/v3/emissions` or `/api/v3/reports`), reusing DM-6. The forensic finding is that **one** such read is required; which surface hosts it is a governance decision, not an architectural one.
* Optional, and only if the PO wants the locator *inside* an Insight answer: an additive allowlist extension to `_EVIDENCE_LINE_FIELDS` / `_SNAPSHOT_FIELDS` (still a tool change).

### 27.4 Required new frontend capability (in principle)

* A **shared evidence viewer surface**: either an embedded viewer region inside `EvidenceRecordPanel`, or one evidence-view route/component that combines `SecureDocumentViewer` (or `StructuredDataPreview`) with the evidence record, consuming the existing signed-URL and DM-6 decisions.
* **Location targeting** (page for PDF/image; row/sheet for CSV/XLSX) built from the locator the backend returns, with an honest "location not available" state where the locator is absent — the existing `source_location.display` string already models exactly that.
* **Insight hand-off:** a link/action from an Insight reference (starting with `calculation_snapshot` and `evidence_line_item`) to that surface, carrying the locator only.

### 27.5 Required I3 extension (if any)

* **Contingent, not automatic.** It is required **only** if the PO decides the customer must *open* evidence **from inside Insight**. The minimum would be a way to resolve `evidence_line_item` (today impossible) and, for the scenario question, a way to reach an evidence chain without pasting an ID — the latter would be a **new tool**, and therefore a PO decision.
* Not required if Insight is allowed to hand over a **locator** to a shared evidence surface that performs its own authorized resolution.

### 27.6 I7 implications

* **Retention/privacy:** `evidence_line_items` is deliberately append-only with **no retention, soft-delete or purge mechanism** (B2-D11; `backend/data/evidence_line_items.py` L15–18, L565–570) and stores `raw_description`, `raw_quantity`, `raw_unit` — i.e. **customer document content in the database**. A viewer increases the number of surfaces reading that content, so I7 must settle retention, redaction and erasure for evidence lines, snapshots and documents **together**.
* **Export:** the locator a viewer would show is also export-visible (`backend/data/exports.py` already classifies evidence completeness), so the export contract must be settled alongside the viewer.
* **Access auditing:** evidence viewing is already audited (`evidence.access`); a wider viewer needs the same treatment (I7/I8 observability).

### 27.7 I8 implications

* **No billing or entitlement change is implied** by evidence tracing itself; if evidence viewing became a plan feature, that would be an I8 commercial decision.
* **Performance / cost:** a viewer issues signed URLs (per view, 1-hour) and a structured preview downloads the file client-side (`StructuredDataPreview`) — bounded today by preview caps; at scale this is an I8 capacity/egress consideration.
* **Reliability / support:** a widened viewer needs the explicit failure states the platform already uses (document unavailable, expired signed URL, depth denied) and should be covered by the QA harness — an I8 operational decision.

## 28. I3 implications

**[VERIFIED] State today:** the catalogue is closed at four tools; `report_evidence_lookup` and `calculation_snapshot_lookup` already return authoritative evidence locators; no tool returns a document id, page or row; `report_evidence_lookup` requires a **report version id**, and every tool requires a question-borne UUID.

**[INFERENCE] What that implies:**

* For **evidence tracing inside Insight**, an I3 extension is **not strictly necessary**: the minimum viable path is "Insight returns locators (already true) → the customer opens a shared evidence surface that resolves them itself (M4)".
* An I3 extension **becomes necessary** if the PO requires any of: resolving an `evidence_line_item` id; naming a document/page/row inside an Insight answer; or starting from a date/amount rather than an identifier. Those are **new tool capabilities** and need an explicit PO decision — including whether they belong in I3 at all rather than in a non-Insight endpoint.
* Any such change must preserve: read-only, deterministic, bounded input/output, the I2 boundary, references-as-locators, and the closed `ToolStatus` vocabulary (PO §3.3–§3.5).

## 29. I7 implications

**[VERIFIED]** Evidence and document content is retained indefinitely by design today (`evidence_line_items` append-only with no purge; snapshots and documents have no retention mechanism of their own; `backend/services/retention.py` lists `evidence_line_items` among retention **domains**, while B2 deliberately implements no mechanism).

**[INFERENCE]** Before a shared evidence viewer exposes document content more widely, I7 must decide at least: retention for documents, snapshots and evidence lines; whether `raw_description` (document text) is personal data; erasure semantics for an append-only evidence ledger versus a document-deletion request; and whether viewing/exporting evidence needs additional access logging or disclosure controls. **This analysis does not authorize or pre-judge any of that** (PO §16).

## 30. I8 implications

**[VERIFIED]** No billing, plan, credit or entitlement code is involved in any evidence path; signed URLs are issued per request with a 1-hour TTL; the QA harness covers evidence/processing behaviour at unit and integration level.

**[INFERENCE]** I8-relevant questions if a viewer is built: is evidence viewing metered or plan-gated; what are the egress/cost bounds of document viewing at scale; what availability and failure-state guarantees apply; and how is a viewer covered by the QA harness? **No I8 implementation is authorized or implied** (PO §16).

## 31. Verified vs inferred findings

### 31.1 [VERIFIED] — directly established from repository evidence

1. The full D33 chain `emission → snapshot → extraction item → document` exists with FKs, indexes and an authorized API, and includes a signed source-document URL.
2. A customer-facing evidence record with original/derived sectioning, completeness classification and source-location precision exists (`backend/domain/evidence.py`, `frontend/src/v3/components/EvidenceRecordPanel.jsx`).
3. `public.evidence_line_items` exists as an immutable, append-only, addressable source-line entity (`line_number`, `source_page`, `row_reference`, `payload_hash`, org/PE RLS, `UNIQUE (source_item_id, line_number)`), populated by a forward hook plus an idempotent backfill.
4. `calculation_snapshots.source_line_item_id` is resolved **by ordinal** for tabular documents at calculation time (`automatic_processing._calculate_line`).
5. `evidence_line_items.row_reference` is **always NULL** today: its reader key `line_reference` has **no producer anywhere** in the repository.
6. `calculation_snapshots.source_page` is populated from the **document page count**, not a per-line page — and that value drives the COMPLETE/PARTIAL classification in `domain/evidence.py` and `data/exports.py`.
7. `calculation_snapshots` has **no** sheet/row/cell/location column, and the `source_location` field `domain/evidence.py` reads has **no writer**.
8. CSV/XLSX extraction stamps per-line `source_row` and document-level `source_sheet` / `source_headers` / `sheet_names`, none of which leave `extracted_data`.
9. PDF/IMAGE per-line `page` provenance exists but only under P1 `MODE_ENABLED` for multi-line-suspect documents (the default is `shadow`).
10. **No OCR coordinate/region provenance exists anywhere.**
11. A document viewer exists (PDF/image frames; CSV/XLSX parsed preview) but is reachable **only** through the D19 workbench, with **no page navigation and no location targeting**.
12. The DM-6 per-role evidence exposure matrix exists and is enforced on the disclosure drill-down route; PE staff and internal staff are denied.
13. **No route accepts an `evidence_line_item` id**; the only line-level reads are per report value (DM-6) and per report version (I3).
14. **No frontend consumes the disclosure drill-down endpoints at all.**
15. I3 returns evidence locators but **no document id, page or row**, and requires an identifier in the question.
16. Signed URLs are authorization-gated, short-lived, never logged, and audited without recording the URL.

### 31.2 [INFERENCE] — reasoned conclusions, clearly separated

* **I1** — a shared evidence viewer should extend today's single line-model / policy / viewer seams rather than duplicate them (§25).
* **I2** — one new authorized locator-resolution read is the load-bearing missing backend capability (§27.3).
* **I3** — an I3 extension is contingent on whether evidence must be openable *from inside Insight*; it is not automatically required (§28).
* **I4** — the fastest honest improvement to today's evidence record is to stop labelling a document page *count* as an exact source location (§27.2 item 1).
* **I5** — CSV/XLSX "exact row" is achievable **without** a new provenance model, because the producer data already exists; the gap is key alignment and downstream transport (§27.2 items 2–3).

### 31.3 [UNKNOWN] — repository evidence insufficient

* Whether any environment (dev, demo, production) currently holds `evidence_line_items` rows at all — this investigation was read-only and **did not query any database**; the answer depends on P1 rollout state and on whether items were persisted with `line_items[]`.
* Whether any deployed environment runs P1 in `enabled` mode for any organisation (configuration-dependent).
* Actual OCR-engine capability in the deployed environment (an explicit environment dependency per AGENTS.md §20).

## 32. Open PO decisions

None of these is decided here. Each is a product/governance choice that the forensic evidence now makes concrete.

| # | Decision required | Why it is needed (evidence) |
| --- | --- | --- |
| **P-1** | Should an evidence **viewer** exist at all, and for which roles? | DM-6 already fixes evidence depth per role and denies document references below `FULL`, while the D33 evidence endpoint exposes `source_document.signed_url` to any org member (§21, M10). The two postures must be reconciled before a viewer is built. |
| **P-2** | Is **line-level location** (page / row / sheet / cell) required, or is document-level evidence sufficient? | Only `line_number` survives reliably today; the page is mis-wired and row/sheet never leaves the extraction (§8, §14–§17, M1/M2/M9). |
| **P-3** | Is an **I3 extension** required (by-id `evidence_line_item` resolution, a document/page locator, and/or an entry point that does not need a pasted id)? | The catalogue is closed at four tools; references are locators; no tool returns a document or a page (§19, §24, §28). |
| **P-4** | Should the viewer be **shared** with regular audit/evidence tracing (one component, one policy) or Insight-specific? | The seams for sharing already exist: one line model, one provenance join, one DM-6 policy, one storage mechanism, one viewer primitive (§25). |
| **P-5** | What is the **retention / erasure / redaction** posture for evidence lines, snapshots and documents (I7)? | `evidence_line_items` is append-only with no purge and stores raw document text; a viewer widens exposure (§29). |
| **P-6** | Is evidence viewing **metered, plan-gated or free** (I8)? | No entitlement code touches evidence today; a viewer adds per-view signed URLs and client-side document fetches (§30). |
| **P-7** | Should the **`source_page` semantics defect** be corrected as a bounded data-integrity change, and should affected historical rows be left as-is or qualified? | A document page *count* currently masquerades as an exact location and can mark evidence COMPLETE (§8). Historical rows cannot be un-written without a decision — D33/B2 preserve history by design. |

## 33. Final forensic conclusion

**What exists today — [VERIFIED].**
CarbonTally already has a working, authorized evidence-tracing chain from an emission result back to the source document: `emissions_logs.snapshot_id → calculation_snapshots` (carrying `source_item_id`, `source_line_item_id`, factor provenance, `source_file`, `source_page`) `→ manual_extraction_items → organization_files`, surfaced by `GET /api/v3/emissions/{log_id}/evidence` and rendered by `EvidenceRecordPanel` / `EvidenceTrail`, with an append-only `evidence.access` audit entry. It also has a durable, immutable, line-addressable evidence model (`public.evidence_line_items`) already consumed by the calculation path, by the disclosure projection and by an I3 tool; a per-role evidence-exposure policy (DM-6); private document storage with short-lived signed URLs; and a working document / structured-data viewer — **inside the D19 processing workbench**.

**What does not exist today — [VERIFIED] / [NOT FOUND].**
A customer-facing **source-document evidence viewer** in the proposed left-document / right-evidence / linked form does **not** exist; the customer evidence surface ends at a new-tab link. **Exact source-location provenance is incomplete**: the per-line page is mis-wired (the snapshot stores a document page *count*), row/sheet locators never leave the extraction, `row_reference` is always NULL, and no OCR region exists. **Insight cannot navigate to evidence**: it has no emissions-by-date entry point, returns no document/page/row, and cannot resolve the `evidence_line_item` kind at all. Finally, **no by-identifier line read exists** for the identifiers the platform itself mints, and **no frontend consumes** the DM-6 line drill-down endpoints.

**Consequently, for the customer scenario as phrased, the answer today is partial.** The system can find the authoritative calculation and the source **document** (and can open it), but it cannot take the customer from "20K CO₂e on 2024-02-02" to **the exact line/row of that invoice without a supplied identifier**, and it cannot locate or highlight that line inside any viewer. The blocking links are M1–M4 (locator completeness) and M5–M8 (viewing and Insight navigation); the one genuinely new backend capability required is **a single authorized locator-resolution read**, and everything else can be built by extending what already exists.

**No implementation was performed.** This document is a read-only forensic analysis. It changes no code, schema, migration, RLS, API, tool, test or configuration, and it authorizes nothing: I7, I8, an I3 extension, an evidence viewer and any change to `evidence_line_item` each remain separate PO decisions, listed in §32.

















