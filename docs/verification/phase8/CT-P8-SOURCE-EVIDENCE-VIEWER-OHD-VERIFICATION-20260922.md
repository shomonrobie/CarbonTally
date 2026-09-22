# CT-P8-SOURCE-EVIDENCE-VIEWER-OHD-VERIFICATION-20260922

**Verification ID:** `OHD-P8-SEV-20260922`
**Verifier:** OHD, independent verifier (not the implementer)
**Mandate:** PO authorization, 2026-09-22 — *Shared Source Evidence Viewer + Insight Evidence Navigation*
**Architectural principle under test:** Insight explains; the evidence system proves.
**Method:** read-only inspection, independent test execution, and verifier-authored adversarial probes. No application code, test, migration, schema or configuration was modified; nothing was deployed; defects were reported, not fixed.

---

## 1. Verdict

**PASS WITH NON-BLOCKING OBSERVATIONS**

The implementation satisfies the PO authorization. One shared evidence capability exists and is genuinely shared (customer evidence panel + Insight handoff), the DM-6 boundary is enforced and re-evaluated on every read, no signed URL is produced below FULL, the `page_count` → `source_page` conflation is removed at the write path, historical values are preserved but presented as unverified, no precision is manufactured, and no unauthorized scope (I7, I8, billing, RAG, I3, schema, destructive migration) was introduced.

No unauthorized disclosure of protected evidence content was found. The residual items in §14 are pre-existing, non-disclosing, or expected-by-design; none is acceptance-blocking. **The implementation is not declared accepted and the PO stage is not closed — that remains the PO's decision.**

---

## 2. Repository state and integrity

| Item | Value |
| --- | --- |
| Authoritative checkout | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| **Current HEAD inspected** | `de021ab6e083329867a6e7fd71e721e3656e6f45` |
| Implementation commit inspected | `999e4fbf92f66079fa78cfb07b8e686097cda628` |
| Working tree | clean (`git status --porcelain` empty) |
| Stash | none |
| Remote alignment | remote `github` = `https://github.com/shomonrobie/CarbonTally.git`; `github/p8-release-reconciled` = `de021ab6` = HEAD ✅ |
| Head delta over the implementation | `999e4fb..de021ab` = **1 file, docs only** (`+8/-2` in the implementation report: recorded SHAs) |
| Baseline used for regression comparison | `67d399f` (pristine pre-implementation) |
| Code difference between that baseline and the implementation's true parent `a368c6e` | **0 code files** (one docs file only) — so the baseline comparison is exact |

Change footprint of the implementation (`67d399f..999e4fb`, 25 files): backend `domain/evidence.py`, `services/automatic_processing.py`, `api/v3_emissions.py`, `api/v3_evidence.py` (new), `api/router.py`, `data/emissions_logs.py`; frontend `v3/evidence/{SourceEvidenceViewer.jsx,evidenceLocation.js,.css}`, `v3/api.js`, `App.js`, `v3/components/EvidenceRecordPanel.jsx`, `v3/insight/{references.js,InsightReferences.jsx}`; tests as listed in §13; the forensic and implementation reports. **No migration, no `.sql`, no schema change; exactly one new route.**

The authoritative implementation report exists at `docs/implementation/phase8/CT-P8-SOURCE-EVIDENCE-VIEWER-IMPLEMENTATION-20260922.md` (393 lines) and its claims were checked, not trusted (§13, §14.6).

### 2.1 Discrepancy recorded during this verification

An earlier instruction named the verification target as `0be7438ddbd1f05c004246cbafc844cbdb1af319`. That commit is **not** this work: it is `feat(p8/fs): consultant+client HTTP authz…; 27 tests; report 053` (Fri 18 Sep 2026, author `shomonrobie`) and it is an **ancestor** of HEAD — a different, earlier workstream. HEAD could not equal it without discarding the 22 Sep source-evidence work. The corrected target (`999e4fb`, an ancestor of HEAD) is what this report verifies, as the PO subsequently confirmed.

Environment note for future gates: `origin` in this checkout is a **local-path remote** (`/tmp/ct_step2`) whose `p8-release-reconciled` ref is `93d5cddd` (19 Sep). Any gate phrased as `HEAD == origin/p8-release-reconciled` fails for environmental reasons; the canonical remote is `github`.

---

## 3. Evidence model and resolver

* **One evidence model.** The viewer reads the existing `evidence_line_items` table through `RepositoryBundle.evidence_line_items`; no second evidence model, table, projection table or duplicate resolver was introduced.
* **Route contract** — `GET /api/v3/evidence/line-items/{evidence_line_item_id}` (`backend/api/v3_evidence.py`, registered in `api/router.py`; the only new route in the commit):
  * *authenticated* — unauthenticated request → **401** (observed).
  * *organization-scoped* — the line is fetched by id and then `ensure_org_access(current_user, line.organization_id)`; a line belonging to another organization → **403** (observed), with a generic body (`{"code":"FORBIDDEN","message":"Organization access denied"}`) naming neither the organization nor the resource.
  * *DM-6 protected* — `require_org_member()` plus the `domain.disclosure` / `domain.disclosure_exposure` policy; roles outside the recognised set → **403**.
  * *re-authorized on every request* — authorization is recomputed per request from the caller identity; a verifier probe switched the same locator owner → member → owner and the posture changed to CONTROLLED and back to FULL, so no previously issued permission is trusted.
  * *bounded* — one line, exactly the allowlisted provenance keys, at most five related calculations, one location block.
  * *allowlisted* — top-level response key set is exactly `{evidence_line_item_id, source_item_id, materialisation_kind, line, location, document, document_available, calculations, access}` (pinned by the repository suite and re-derived independently).
  * *read-only* — GET only; no mutation, no post-processing.
  * *audited* — one `evidence.line_access` entry per read through the existing `AuditEntry` contract.
* **Invalid identifiers do not disclose content:** a well-formed but absent UUID → **404** `evidence line not found`; a malformed id → **404**; never a 5xx.

---

## 4. Authorization verification (DM-6)

Independently probed with the verifier's own fixtures (`/tmp/ct_sev_probe/backend/tests/unit/api/test_ohd_independent_probe.py`):

| Role | Required | Observed |
| --- | --- | --- |
| Owner | FULL | FULL — signed URL issued, `path`/`metadata` present, doc identity present |
| Admin | FULL | FULL |
| Member | CONTROLLED | CONTROLLED — `signed_url == ""`, `path`/`metadata` keys **absent**, `location` = restricted, document identity name/type only |
| Viewer | CONTROLLED | CONTROLLED |
| Consultant (they are not org members) | 403 on the customer evidence route | **403** (`Organization member access required`) |
| Consultant added as an organisation member | existing bounded policy, never FULL | **200 BOUNDED** — no signed URL, restricted location, no quantity |
| Processing Entity staff | DENIED | **403** |
| CarbonTally internal staff | DENIED | **403** |
| Unknown / unrecognised org role | DENIED | **403** |
| Foreign organization | DENIED | **403** |
| Unauthenticated | — | **401** |

Below FULL the implementation exposes **none** of: signed source-document URL; storage path; document metadata constituting a document reference; page/sheet/row location.

**Signed URLs are produced only after authorization succeeds.** The strongest form of this was probed with a signing call-counter rather than a blanked field: at CONTROLLED the storage signer was **never invoked** (`calls == []`), and it was invoked again only when the caller was restored to FULL — i.e. no URL is generated and then hidden.

The five pre-existing disclosure tests that asserted the superseded posture were replaced by tests asserting the corrected posture; the replacement is consistent with the ratified matrix, and the new posture is stronger, not weaker (an owner-only "receives a signed document" test was added alongside).

---

## 5. Audit behaviour

* Evidence reads are audited: the D33 route writes `evidence.access` (unchanged block, unchanged action), the new resolver writes `evidence.line_access`.
* Audit payloads contain **identifiers only** — verifier probes asserted the recorded entry contains the organization, the caller, the line/log identifiers and the resource type, and that **no** signed URL, storage path, bucket name or token appears in it.
* An audit failure does not break the read (observed: a raising audit sink still yields a 200 response).
* **Canonical I4 audit semantics untouched** — `backend/domain/audit.py`, the audit logger and the audit API are **not in the change footprint** (0 files). The new entry uses the existing contract; no new audit semantics were invented.

---

## 6. Source-page correction (critical area)

* **Write path.** `backend/services/automatic_processing.py` `_calculate_line()`: `source_page=job.metadata.get("page_count")` is **removed**. A new local `source_page` starts as `None` and is set **only** from `evidence_line_items.source_page` for the resolved authoritative line, accepted only when `isinstance(int) and not isinstance(bool) and >= 1`; otherwise it stays `NULL`. The resolver is wrapped so provenance failure can never block processing. Verified in the diff and by the repository's `page_count`-provenance tests.
* **No remaining conflation.** Repository-wide grep for `page_count` shows every other use is the document/item page **count** column or fidelity classification — never `calculation_snapshots.source_page`. The one formerly offending assignment is gone.
* **Historical values.** No migration, no `UPDATE`, no backfill (0 SQL files in the footprint). Historical page-count-derived values are retained physically, exposed as `source_page_reported`, and the **effective** page is `None` with `page_state = "unverified"`.
* **Not presented as verified.** Probe: a snapshot whose historical page is 8 and whose authoritative line page is 5 reports `source_page 5 / verified` and **never** presents 8 as a page; with no authoritative line page, the reported 8 is retained but the state is `unverified`, completeness is `PARTIAL`, and the display does not say "page 8". `source_location_precision()` lists a page only when verified.
* **The `page_count` vs `source_page` distinction is preserved.** These are treated as different facts end to end. **No conflation remains in the calculation path** — this was the forensic blocker (F-B2-7) and it is closed.

Test-level confirmation: `tests/unit/services/test_multiline_provenance_mapping.py` (14 tests) plus the new `unverified`/`PARTIAL` assertions exercise exactly this, and they pass.

---

## 7. Location semantics

| Case | Expected | Observed |
| --- | --- | --- |
| PDF, genuine producer page | verified page presented | `kind: page`, `page_state: verified`, "Source page 2." |
| CSV, producer `source_row` | the producer's row used | `kind: row`, row 14 (probe: producer row 14 with ordinal 3 is never conflated) |
| XLS/XLSX | sheet + row represented | `kind: sheet_row`, `sheet: Emissions`, `row: 14` |
| `row_reference` | used only when authoritative | used only when present and non-empty (`reference` kind); absent → `unavailable` |
| Missing location | explicitly unavailable | `kind: unavailable`, "Exact source location is not available for this line." + an ordinal caveat |
| Restricted (below FULL) | restricted, no precision | `state: restricted`, uniform copy, no page/sheet/row |
| Ordinals | never a row or a page | probe: ordinal 3 renders as "Line 3" and the view never says "page 3"/"row 3"; the ordinal note says so explicitly |
| OCR | no invented bounding boxes | no visual/OCR keys exist in the contract; no coordinates are produced |

`resolve_source_page` was independently probed over 8 inputs: a valid positive int page is verified; `None`, `0`, negative, boolean and string values are never treated as a page. No path manufactures precision.

---

## 8. Shared viewer verification (frontend)

One capability, not an Insight-only implementation: `v3/evidence/SourceEvidenceViewer` is a standalone route (`/evidence/line-items/:lineItemId`, authenticated) reused by the customer evidence panel and by the Insight handoff. `evidenceLocation.js` is the single location/URL kernel; Insight renders no viewer of its own.

* **Left pane** — the original source document, only when the backend issued a signed URL (probe: no signed URL ⇒ **no frame in the DOM at all**; the withheld notice is shown, and it distinguishes "not available at your access level" from "no stored source document"). The URL carries a location locator only.
* **Right pane** — read-only extracted evidence, mapped evidence, location/provenance and bounded calculation context.
* **Not an unrestricted viewer** — one line, at most five calculation references, one location block; no spreadsheet, mapping, factor or extraction editors. Probe: no `input/textarea/select/form` in the ready state, and the only buttons are the reused document primitive's zoom controls.
* **Non-disclosing failure states** — 403, 404, 500 and network failure render **byte-identical** copy in one state, with no document frame, no evidence and no textual hint of existence (probe asserts the absence of "403/404/500/not found/does not exist/organisation" and identical text across all four).
* **Retry reauthorizes** — the retry control re-calls the backend (`getEvidenceLine` invoked again; no cached permission).
* **Hostile-payload probe** — a `restricted` or `unavailable` location block containing embedded `page: 8`, `sheet`, `row: 42/99` values renders **none** of them: the UI trusts the state, not the numbers.

---

## 9. Insight handoff verification

* `evidence_line_item` reference → a handoff link to the shared viewer, rendered **without invoking any I3 tool** (probe: zero tool calls on render).
* Resolved `calculation_snapshot` → a handoff **only** when the resolved data carries an authoritative `source_line_item_id` (probe: present → linkage to that line; absent → no link).
* `report`, `report_version`, unresolved, unknown-kind and malformed references → **no fabricated link** (probed). The kernel `evidenceHandoffPath` is field-driven rather than kind-driven, but the I3 report/snapshot projections cannot supply the field unless it exists authoritatively, so no report reference fabricates a link in practice (observation 14.5).
* Unavailable/failed resolution renders one non-disclosing state, stated as "it is not available to you", never "it does not exist".
* **I3 boundary intact:** `backend/services/insight_tools.py` is **not in the change footprint**; the catalogue remains exactly four tools; the identifier→tool mapping and the contract are unchanged; no fifth tool was added.

---

## 10. Customer evidence flow

`GET /api/v3/emissions/{log_id}/evidence` still works (owner 200; the response shape is additive). It now returns the DM-6 `evidence` block (`drill_down_depth`, rationale, reference availability), the **verified** page where authoritative (`source_page 5 / verified`), `source_page_reported` for the historical value, the `PARTIAL` completeness where the page is not verified, and the `source_item_id`/`source_line_item_id` handoff. Below FULL it returns no signed URL, no `path` and no `metadata`, and no page/sheet/row. Existing evidence functionality was not broken; the route's audit action is unchanged.

---

## 11. Date/amount discovery boundary

Checked and **not implemented**, as the report states. No new code resolves an emission by date or amount, performs document text search, or fabricates an invoice, calculation or line (grep of the diff for text-search/amount/date-range/discovery constructs: none). The viewer resolves a *known* evidence-line identifier only; it does not pretend to answer "why did I have 20K CO₂e on 2024-02-02?".

Reported as a **known deferred capability**, not a failure: no deterministic, authorized backend capability exists to map date/amount → evidence line, and inventing one (semantic search, fuzzy matching, LLM inference) would violate the authorization.

---

## 12. Scope compliance and database

Confirmed **not** present in the implementation commit: I7; I8; billing/subscription/credits/metering; RAG; LangChain; vector search/embeddings; `ai_content_history`; the synthetic document generator; a fifth I3 tool; schema/migration changes; destructive historical migration; production deployment. (Content grep of the diff returns documentation prose only; the 25-file footprint contains no such code.)

**Database:** the implementation neither opened nor changed a database. The footprint contains **0** migration/SQL/schema files, the audit and repository contracts are unchanged, and the entire backend suite — including every new evidence test — runs against in-memory fakes with no credentials and no Supabase/Postgres connection. Verified by running it.

---

## 13. Test results (independent)

**Backend** (executed by the verifier at HEAD, in an isolated `/tmp` copy of the tree so the audited repository stayed read-only):

| Command | Result |
| --- | --- |
| `pytest tests/unit -q` (full unit suite) | 2978 collected; failure set **byte-identical** to the pristine baseline `67d399f` (same 4 failures, same 97 skipped, same 16 errors) |
| `pytest tests/unit/api/test_source_evidence_viewer.py -q` | **22 passed** |
| evidence/emissions/provenance/disclosure/insight focused set | **274 passed, 0 failed** |
| the report's own 5-file command | **74 passed** (reproduced exactly) |
| new tests attributable to the change | **+26 collected** vs baseline |

**Frontend:**

| Command | Result |
| --- | --- |
| `--testPathPattern='(source-evidence-viewer\|evidence-location\|insight-references)'` | **3 suites, 40 tests passed** (reproduced exactly) |
| new/modified suites incl. `insight-page` | **4 suites, 85 tests passed** |
| full `react-scripts test --watchAll=false` | 41 suites / 452 tests, 451 passed, 1 failed, 2 suites failing — **identical failure set** to the baseline (39 suites / 430 tests, 429 passed, same 2 suites) |
| production build (`react-scripts build`) | **exit 0**, "Compiled with warnings": exactly the **105 pre-existing** lint warnings, **none** from the new evidence files |

**Verifier-authored adversarial probes — 60 checks, all passing** (they live in `/tmp`, not in the repository): 32 backend API probes, 15 viewer probes, 8 Insight-handoff probes, 5 customer-panel probes.

### 13.1 Pre-existing failures — independently confirmed

The report's classification was not accepted on trust; each failure set was reproduced at the pristine baseline `67d399f` (which differs from the implementation's true parent by a docs file only):

* **Backend (4, pre-existing):** `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered`, `::test_canonical_ops_review_assign_registered`, `::test_admin_legacy_compat_surface_retained` (their `_paths()` helper returns only `{'/api/v2/health'}` — a helper defect), and `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` (hard-coded migration count 71 while the repository holds 78).
* **Frontend (2 suites / 1 test, pre-existing):** `src/App.test.js` and `src/v3/__tests__/dr007-investor-display-fixes.test.jsx`.

All are unrelated to this change and identical before and after. No regression was found in either suite.

---

## 14. Defects and observations

**No acceptance-blocking defect found.** Observed items, in decreasing significance:

1. **`source_item.file_url` is returned below FULL on the amended customer evidence route (pre-existing key; policy inconsistency — PO decision requested).** `GET /api/v3/emissions/{log_id}/evidence` returns the `source_item` block (`file_url`, `file_id`, `extracted_data`, `mapped_data`) without any DM-6 depth gate, while the same response correctly nulls `source_document.path`, `source_document.metadata` and the signed URL. `source_item.file_url` is the exact value `path_from_url()` converts into a signable storage path, i.e. the key family the ratified policy withholds below FULL. *Reproduction:* verifier probe `test_observation_source_item_file_url_is_returned_below_full` — as org Member: `source_document.path is None`, `metadata is None`, `signed_url == ""`, signer never called, **and** `source_item.file_url` non-empty. *Severity: medium.* *Blocks acceptance: no — but the PO should ratify or correct it.* The block is **identical in the pristine baseline** (not introduced by this change), it is **not consumed by any frontend code**, and the same locator is already obtainable by the same authenticated member through the authorized documents surface (`GET /api/v3/documents/{file_id}/signed-url` requires only `require_org_member()` + org match), so no content or credential is disclosed that the caller is not otherwise authorized to obtain. *Smallest remediation if the PO wants the boundary absolute:* omit or null `file_url`/`file_id` in the `source_item` block unless the exposure policy grants document references — a zero-consumer, zero-risk change.
2. **DM-6 is not enforced on the customer documents route** (`GET /api/v3/documents/{file_id}/signed-url`), which any organisation member can call for their own organisation's file. This is pre-existing, is disclosed as limitation 7 of the implementation report, and is arguably the customer's own document-management surface rather than the evidence path — but it is the larger policy question behind observation 1, and it is a **PO decision**, not something this change introduced or could silently fix.
3. **Export/reporting completeness still infers COMPLETE from the presence of a page.** `backend/data/exports.py::_evidence_status` and `backend/data/reporting.py::audit_readiness` treat `source_page IS NOT NULL` as evidence-complete. Historical page-count-derived values therefore still read as COMPLETE on those two surfaces, even though the same row is correctly `PARTIAL`/`unverified` on the corrected customer surfaces. Neither file is in the change footprint, so this is a pre-existing residual of the same forensic finding, not a regression — but the `page_count`/`source_page` distinction is not yet uniform platform-wide (supporting the PO's stated preference to keep exports out of scope).
4. **Foreign-organization identifiers produce 403 versus 404 for absent ones.** This distinguishes "no such line" from "a line exists in another organization" for a caller holding a valid UUID, with a generic body that names nothing. It matches the platform-wide `ensure_org_access` convention used by other by-id routes (including the pre-existing D33 route), the identifier is an unguessable UUID, and the UI collapses every failure into one state. *Severity: low; not blocking.* If the PO wants strict non-disclosure, the smallest remediation is to return 404 for foreign evidence resources on the evidence-reading routes.
5. **`raw_description` is withheld at CONTROLLED.** The prospectively-worded DM-6 allowlist recognises structural keys (`description`, `activity`, `amount`, …) but not `raw_description`, so a Member sees mapped field values and not the raw description. The unit tests pin the exact CONTROLLED key set, so this is intentional-looking; it is recorded because it is a *behavioural* consequence of a key-name choice rather than a stated policy decision, and the PO may wish to ratify it. *Severity: low; never over-exposes.*
6. **Implementation-report inaccuracies (documentation only).** The report's tests table says the new frontend viewer suite has "7 tests" — the suite executes **8**; and `frontend/src/v3/__tests__/insight-page.test.jsx` (a `react-router-dom` mock needed so the page suite can render the handoff link) is changed but absent from the report's file inventory. Both are minor. Every other numeric claim checked — 22 backend tests, 74-in-5-files, 3 suites/40 frontend tests, the 4 backend and 2 frontend pre-existing failures, no schema/migration, no new I3 tool, one new route, `source_page` correction — was reproduced exactly.
7. **The changed customer panel has no repository test coverage.** `frontend/src/v3/components/EvidenceRecordPanel.jsx` is modified (verified page only, server-issued URL gating, handoff) and no suite imports it. The verifier probed it directly (5 checks: a historical page count of 8 is never rendered as a page, an authoritative page 7 is, no signed URL ⇒ no link, a signed URL ⇒ link, handoff only with an authoritative line id) and it behaves correctly. A repository test would be desirable, but its absence is a coverage gap, not a defect.
8. **Path convention note.** Prior OHD reports live under `docs/implementation/phase8/`; this report is at the PO-specified `docs/verification/phase8/`. Harmless, but the PO may wish to unify the location.
9. **Routing and the failed-suite caveat.** Component tests mock `react-router-dom` because the installed module cannot be resolved in this environment (the repository's existing convention, disclosed as limitation 9), so route *wiring* is asserted structurally (`App.js` registers the authenticated route) rather than by rendering the router.

---

## 15. Known deferred capability

Date/amount discovery ("why did I have 20K CO₂e on 2024-02-02?") is **not implemented and is not faked**. This is the expected outcome and is recorded as a deferred capability, not a defect: the viewer proves a *known* emission back to its evidence, which is what was authorized.

---

## 16. Statement of independence and limits

* Every action was read-only with respect to the audited repository; probe and test-suite runs used isolated copies under `/tmp`, and the working tree, HEAD and stash were unchanged at the end of verification.
* No defect was patched, no test was altered to pass, no migration was created, nothing was deployed, and no I7/I8 work was started.
* This verification is based on code inspection, independent test execution and 60 adversarial probes at `de021ab6` (implementation `999e4fb`). It does not assert runtime behaviour in a production deployment, and it does not authorise acceptance.

**Final verdict: PASS WITH NON-BLOCKING OBSERVATIONS.**

The implementation is **not** declared accepted and the PO stage is **not** closed. That decision, and the disposition of observations 14.1–14.3, remains with the PO.

*This report was produced by an AI agent (OpenHands, acting as OHD) on behalf of the PO.*
