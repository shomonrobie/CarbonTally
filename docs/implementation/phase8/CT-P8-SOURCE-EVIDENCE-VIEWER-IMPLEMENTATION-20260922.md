# CT-P8-SOURCE-EVIDENCE-VIEWER-IMPLEMENTATION-20260922

**Task / authorization ID:** PO Authorization — *Shared Source Evidence Viewer + Insight Evidence Navigation* (2026-09-22).
Forensic basis: `CT-P8-SOURCE-EVIDENCE-FORENSIC-20260922`
(`docs/implementation/phase8/CT-P8-SOURCE-EVIDENCE-FORENSIC-20260922.md`).

**Repository / release authority**

| Item | Value |
| --- | --- |
| Authoritative checkout | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| Remote | `github` |
| Starting HEAD (verified before changes) | `a368c6e642333077729d9f6a73d7767f2764956f` |
| Ending HEAD | see §13 (filled at commit time) |

The starting HEAD was re-verified at the beginning of the task (not assumed):
`git rev-parse HEAD` returned `a368c6e…`, the working tree was clean, and
`git rev-list --left-right --count HEAD...github/p8-release-reconciled` returned
`0 0`.

---

## 1. Scope delivered

The PO decision implemented here:

> CarbonTally implements a **shared Source Evidence Viewer**. Insight explains; the
> evidence system proves.

Delivered:

1. **One shared viewer capability** (not an Insight-specific viewer) reachable from
   the existing customer evidence flow and from CarbonTally Insight.
2. **A bounded, re-authorized evidence-line resolution read**
   (`GET /api/v3/evidence/line-items/{evidence_line_item_id}`) exposing an
   allowlist only.
3. **The `source_page` provenance correction** (page *count* is never a source
   location) plus honest handling of historical records.
4. **The DM-6 inconsistency correction** on the D33 customer evidence path: the
   signed source-document URL (a storage pointer) is now issued at FULL depth
   only.
5. **Insight evidence handoff** (`View source evidence`) with no new I3 tool and
   **no I3 contract change**.

Explicitly **not** delivered (per authorization §11/§12/§13/§16): no I7
retention/erasure policy, no I8 billing/plan gating/metering, no AI/RAG/vector
search, no new I3 tool, no I2 semantic change beyond the DM-6 correction, no
schema/migration change, no historical data rewrite, no production deployment.

---

## 2. Files changed

### Backend (implementation)

| File | Change |
| --- | --- |
| `backend/domain/evidence.py` | Added `PAGE_STATE_*`, `resolve_source_page()`, `derive_line_location()`; `source_location_precision()` now reports `page_state`/`reported_page` and only lists a page when verified; `build_evidence_record()` accepts the resolved evidence `line` and derives the verified page + line identifiers. |
| `backend/services/automatic_processing.py` | `_calculate_line()` no longer writes `job.metadata["page_count"]` into `calculation_snapshots.source_page`; it writes the authoritative per-line page from `evidence_line_items` (or `NULL`). |
| `backend/api/v3_emissions.py` | `GET /api/v3/emissions/{log_id}/evidence` now applies DM-6 (denied roles 403), resolves the evidence line, reports the verified page/state, issues the signed URL/`path`/`metadata` at FULL depth only, and exposes the line handoff (`evidence.source_line_item_id`). |
| `backend/api/v3_evidence.py` | **New** — the shared viewer's resolution route (DM-6 + organisation isolation + allowlist + access audit). |
| `backend/api/router.py` | Registered the new router (`v3_evidence_router`). |
| `backend/data/emissions_logs.py` | Added `list_for_line(line_item_id, organization_id, limit)` — bounded, org-scoped, allowlisted calculation context for one evidence line. |

### Frontend (implementation)

| File | Change |
| --- | --- |
| `frontend/src/v3/evidence/evidenceLocation.js` | **New** — pure location presentation (`locationView`, `locationRows`, `hasExactLocation`) and the single evidence handoff (`evidenceViewerPath`, `evidenceViewerPathForReference`). |
| `frontend/src/v3/evidence/SourceEvidenceViewer.jsx` | **New** — the shared viewer page (document ↔ extracted/mapped evidence, authority-linked, read-only, non-disclosing failure state). |
| `frontend/src/v3/evidence/evidence-viewer.css` | **New** — D21-token styling for the viewer. |
| `frontend/src/v3/api.js` | Added `getEvidenceLine(lineItemId)`. |
| `frontend/src/App.js` | Added the authenticated route `/evidence/line-items/:lineItemId`. |
| `frontend/src/v3/components/EvidenceRecordPanel.jsx` | Shows the *verified* page only (otherwise unverified/unavailable), gates the document link on the server-issued URL, and adds the `View source evidence` handoff. |
| `frontend/src/v3/insight/references.js` | Added the evidence handoff (`evidenceHandoffPath`, `EVIDENCE_HANDOFF_LABEL`); the four-kind catalogue and the I3 identifier mapping are unchanged. |
| `frontend/src/v3/insight/InsightReferences.jsx` | Renders the handoff for `evidence_line_item` locators and for resolved snapshots carrying `source_line_item_id`. |

### Tests

| File | Change |
| --- | --- |
| `backend/tests/unit/api/test_source_evidence_viewer.py` | **New** — 22 tests: DM-6 posture, signed-URL boundary, resolution/allowlist, location semantics, historical `source_page`. |
| `backend/tests/unit/services/test_multiline_provenance_mapping.py` | Extended the line-item fake with by-id read + per-line pages; **new** tests proving `page_count` never becomes `source_page`. |
| `backend/tests/unit/api/test_evidence_record.py` | COMPLETE now requires a verified page (line supplied); **new** `test_evidence_record_page_is_unverified_without_a_line`; the endpoint test asserts verified page + line handoff + CONTROLLED posture. |
| `backend/tests/unit/api/test_evidence_traceability.py` | The former "member gets a signed URL" assertion is replaced by the corrected posture; **new** owner-receives-signed-document test. |
| `backend/tests/unit/api/fakes.py` | `_EvidenceLinesStub` is now stateful (`seed`, `get`, ordinal resolve) and `MemoryLogs` gained `list_for_line` + `seed_line_snapshots` (test support only). |
| `frontend/src/v3/__tests__/source-evidence-viewer.test.jsx` | **New** — 7 tests (document, withheld document, linked location, unavailable, restricted, read-only, retry re-authorization). |
| `frontend/src/v3/__tests__/evidence-location.test.js` | **New** — 12 tests (location states, ordinal≠row, handoff paths). |
| `frontend/src/v3/__tests__/insight-references.test.jsx` | The `evidence_line_item` expectations now assert the shared-viewer handoff (and that no I3 tool is invoked); added a resolved-snapshot handoff test. |

---

## 3. Architecture

```
customer evidence tracing ─┐
report/disclosure evidence ─┼─► Shared Source Evidence Viewer
CarbonTally Insight ────────┘        │
                                     ├── LEFT : original source document
                                     │         (SecureDocumentViewer + signed URL, FULL only)
                                     └── RIGHT: extracted/mapped evidence, derived location,
                                                calculation context, access rationale
                                                │
                                                └── GET /api/v3/evidence/line-items/{id}
                                                        → evidence_line_items (B2, authoritative)
                                                        → manual_extraction_items → organization_files
                                                        → calculation_snapshots (referencing refs)
Inbound:  GET /api/v3/emissions/{log_id}/evidence  (D33, preserved and corrected)
```

Design rules kept:

* **No second evidence model.** The viewer reads `evidence_line_items` and the
  existing provenance relationships; no new table, no new materialisation.
* **Locators, not grants.** The route carries an id only; the backend re-applies
  authorisation on every read.
* **No mutation.** Nothing in the viewer is editable; the line projection is
  read-only.
* **Bounded rendering.** The right pane shows the single evidence line, its
  derived location and the calculations that reference it — never a dump of the
  whole extraction and never an unrestricted spreadsheet renderer.

---

## 4. Authorization behaviour (DM-6 preserved, never broadened)

`exposure_for_role()` (the single ratified matrix) is applied on both evidence
reads. Nothing was widened: the one behavioural change is a correction in the
restrictive direction.

| Caller | Depth | Evidence route | Signed document URL |
| --- | --- | --- | --- |
| Owner (`org_owner`) | FULL | 200 | issued |
| Admin (`org_admin` / `admin`) | FULL | 200 | issued |
| Member (`user`) | CONTROLLED | 200 | **withheld** (issued before this change) |
| Viewer (`org_viewer`) | CONTROLLED | 200 | **withheld** |
| Consultant | BOUNDED (policy level) | 403 at the org-member dependency (unchanged, see §9) | never |
| Processing Entity staff | DENIED | 403 | never |
| CarbonTally internal staff | DENIED | 403 | never |
| Unrecognised organisation role | DENIED (DM-6) | 403 | never |
| Foreign organisation | — | 403 (organisation isolation) | never |

* Re-authorization happens **per request** (tested: the same locator yields the
  Member projection for a Member and the FULL projection for an Owner).
* Evidence reads are audited (`evidence.access`, `evidence.line_access`) with ids
  only — never URLs, tokens or storage paths (tested).
* The signed URL is ephemeral and is only produced *after* the depth check.

**DM-6 interpretation (explicit, for review).** The forensic finding named the
signed source-document URL as the inconsistency. This implementation therefore
withholds the **storage pointers** below FULL — the signed URL, the storage
`path`, the document `metadata`, and any page/sheet/row locator (a page is a
document reference) — while the document's *identity* (name, type, size) and the
caller's own extracted evidence/amounts continue to be visible at the depths the
matrix already allows. No new role, policy or allowlist was introduced.

---

## 5. Evidence resolution

`GET /api/v3/evidence/line-items/{evidence_line_item_id}` — new, **bounded** and
read-only. Order of operations:

1. `require_org_member()` (authentication + organisation membership);
2. DM-6 resolution and denial (`403` with the DM-6 rationale for denied roles);
3. `evidence_line_items.get(id)` → `404` when absent;
4. `ensure_org_access(caller, line.organization_id)` → `403` for a foreign line;
5. resolve the parent extraction item and the source document (line link → item
   link → canonical path fallback);
6. project the line through the **existing** DM-6 allowlist
   (`domain.disclosure_exposure.project_lines`) — one policy, no second one;
7. derive the location (only with document references allowed);
8. load the bounded calculation references for the line;
9. append an `evidence.line_access` audit entry (ids only).

Response allowlist (no arbitrary columns, no raw row dump):

```
evidence_line_item_id · source_item_id · materialisation_kind
line      { …DM-6 allowlist… }               (id, line_number, amounts at
                                              CONTROLLED+, redacted_fields)
location  { kind, page, page_state, sheet, row, column, row_reference,
            line_number, ordinal_note, precision, display }
          | { state: "restricted", display }
document  { id, name, file_type, size_bytes, uploaded_at, signed_url }
          (+ path, metadata at FULL only)
document_available · calculations[] (bounded reference + result context)
access    { drill_down_depth, drill_down_rationale, document_references_available }
```

The existing D33 customer route `GET /api/v3/emissions/{log_id}/evidence` is
**preserved** and now additionally carries `evidence.source_line_item_id` (the
viewer handoff), `evidence.source_page` (verified only), `source_page_state` and
`drill_down_depth`.

## 6. Location semantics

`domain/evidence.derive_line_location()` derives a location from **authoritative
data only**:

| Evidence | Location produced |
| --- | --- |
| line with its own `source_page` (producer-supplied page) | `kind: "page"`, `page_state: "verified"` |
| CSV/XLSX line whose extraction element carries `source_row` | `kind: "sheet_row"` (sheet from `extracted_data.source_sheet`) or `kind: "row"` |
| a genuine printed reference in `row_reference` | `kind: "reference"` |
| nothing authoritative | `kind: "unavailable"` + an explicit explanation |

* An evidence **ordinal is never a physical row or page**: `line_number` is
  reported separately with the note *"That ordinal is not a physical file row or
  page on its own."*
* OCR bounding boxes are **not** invented — no persisted OCR coordinates exist,
  so the viewer states that the exact visual location is unavailable.
* Below FULL depth the location block is `{ state: "restricted", display }`
  (withheld and explained, not silently nulled).
* The UI distinguishes the three states explicitly
  (`data-location-state="exact|unavailable|restricted"`).

## 7. Historical `source_page` handling

* **Write path fixed:** `automatic_processing._calculate_line()` now writes
  `source_page` from the authoritative per-line `evidence_line_items.source_page`
  only, and leaves it `NULL` otherwise. `job.metadata["page_count"]` no longer
  reaches the column (F-B2-7 alignment).
* **Read path made honest:** `resolve_source_page()` treats a page as *verified*
  only when the resolved evidence line supplies it. A page stored on the snapshot
  alone is reported as `unverified` — `technical_details.source_page = None`,
  `source_page_reported = <historical value>` retained for audit, and the record
  is `PARTIAL`, not `COMPLETE`.
* **No destructive migration.** Historical rows are untouched. They are simply not
  presented as exact locations until an independent authoritative source supports
  the page. Historical limitation documented in §10.

## 8. CarbonTally Insight handoff

* Insight **explains**; the evidence system **proves**. `InsightReferences` now
  renders `View source evidence` when, and only when, an authoritative evidence
  LINE is known:
  * reference kind `evidence_line_item` → `/evidence/line-items/{id}` (the shared
    viewer resolves and re-authorizes; released as a link, not as an access
    decision);
  * a **resolved** `calculation_snapshot` whose ratified projection already
    carries `source_line_item_id` → `/evidence/line-items/{that id}`.
* **No fifth I3 tool.** The four-tool catalogue, its registry payload and its
  projections are unchanged; `_SNAPSHOT_FIELDS` already contained
  `source_line_item_id`, so **no I3 contract change was necessary** (the additive
  projection allowed by §6 turned out to be unnecessary — the smaller change).
* **No guessing.** A `report`/`report_version` reference, an unresolved reference,
  or a snapshot without a line id produces no handoff — the existing truthful
  answer states stand.
* **No string searching** for the customer question ("Why did I have 20K CO₂ on
  Feb 2 2024?"). That date/amount discovery capability does not exist in the
  deterministic backend today and is **not** invented here (see §10).

## 9. Tests

Backend (**all run in memory; the development database was never opened**):

| Command | Result |
| --- | --- |
| `pytest tests/unit/api/test_source_evidence_viewer.py -q` | **22 passed** |
| `pytest tests/unit/api/test_evidence_record.py tests/unit/api/test_evidence_traceability.py tests/unit/api/test_v3_emissions.py tests/unit/services/test_multiline_provenance_mapping.py tests/unit/api/test_source_evidence_viewer.py -q` | **74 passed** |
| `pytest tests/unit -q` (full unit suite) | 4 failed, remainder passed — all 4 are **pre-existing and unrelated** (below) |

Frontend:

| Command | Result |
| --- | --- |
| `react-scripts test --watchAll=false --testPathPattern='(source-evidence-viewer|evidence-location|insight-references)'` | **3 suites, 40 tests passed** |

**Pre-existing failures (not regressions).** The same four tests fail identically
at the starting HEAD, verified in a pristine worktree
(`git worktree add /tmp/ct_pristine a368c6e`):

* `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered`
* `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered`
* `tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained`
  (their `_paths()` helper returns only `{'/api/v2/health'}` — a defect in the
  helper, unrelated to this task)
* `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`
  (a hard-coded migration count of 71 while the repository holds 78 — no migration
  was added or changed by this task)

New coverage by requirement:

* **Authorization** — Owner/Admin FULL; Member/Viewer CONTROLLED with no signed
  URL; DM-6 denial for an unrecognised organisation role; PE staff and internal
  staff denied; cross-organisation denied; re-authorization on every read; the
  signed URL never bypasses authorization.
* **Evidence resolution** — a valid line resolves with allowlisted provenance; the
  exact top-level key set is pinned; nonexistent id → 404; foreign org → 403; the
  CONTROLLED line projection is exactly the DM-6 allowlist with `redacted_fields`;
  the read is audited without URLs.
* **Location** — PDF verified page; CSV row taken from the producer (5) while the
  ordinal is 3; XLSX sheet+row; unavailable; ordinal never a page/row.
* **Historical `source_page`** — a page count (8) is never presented as a page;
  unverified state with the reported value retained; an authoritative line page
  (2) is used and verified; the emissions route exposes `unverified` and the
  record is `PARTIAL`.
* **Viewer (frontend)** — document beside evidence; withheld document below FULL;
  linked location; restricted location; unreliable-location caveat; read-only;
  non-disclosing failure state; retry re-requests the locator.
* **Insight** — handoff for an `evidence_line_item` locator with **no** I3 tool
  invocation; handoff from a resolved snapshot; no handoff invented elsewhere.

## 10. Known limitations

1. **Historical page provenance cannot be repaired.** Existing
   `calculation_snapshots.source_page` values that came from the page-count path
   are now displayed as *unverified*. No independent authoritative record exists to
   reconstruct the true page for those rows, and the PO prohibited a blind rewrite,
   so they remain unverified until re-processed or otherwise supported.
2. **A bare evidence ordinal has no physical location.** Where the producer did not
   persist a page/`source_row`, the viewer says the exact location is unavailable
   rather than presenting the ordinal as one.
3. **No OCR coordinate provenance exists**, so visual page targeting is limited to
   the page level; the viewer states this honestly instead of drawing bounding
   boxes.
4. **The viewer does not render the whole extraction.** The right pane shows the
   single evidence line and its calculation context (bounded by design and by the
   DM-6 allowlist); neighbouring spreadsheet rows are deliberately not exposed.
5. **Member/Viewer experience is intentionally narrower.** CONTROLLED has no
   document reference and therefore no page/sheet/row and no in-viewer document, so
   a Member sees the extracted evidence plus an explanation. That is the ratified
   DM-6 posture, not a defect; letting members see source locations would be a
   **new PO decision**.
6. **Consultant reachability is unchanged.** Consultants are not organisation
   members, so the customer evidence surfaces refuse them (403) exactly as before;
   the BOUNDED projection is asserted at the policy level. Extending consultant
   access to these routes would change I2 authorization semantics and is therefore
   out of scope (authorization §16).
7. **The customer documents route (`GET /api/v3/documents/{id}/signed-url`) was left
   unchanged.** It is the document-management surface (the customer's own uploads),
   not the evidence path the forensic finding named; changing it would alter access
   for the whole documents workspace. The evidence surfaces now enforce the
   corrected posture.
8. **Date/amount discovery ("why did I have 20K CO₂e on 2024-02-02?") is not
   implemented.** No deterministic backend capability resolves an emission by
   date/amount to an evidence line, and the authorization forbade inventing one.
   Recorded here as the missing capability rather than faked.
9. **Frontend component tests mock `react-router-dom`** (the repository's existing
   convention — the installed module cannot be resolved in this environment), so
   routing itself is not exercised by these unit tests.

## 11. Explicitly unimplemented / deferred (per authorization)

* **I7** retention/erasure/export policy and any redaction regime — not started.
  The permission invariant is preserved explicitly: no new retention regime, no
  automatic deletion, `evidence_line_items` remains append-only, signed URLs remain
  ephemeral, and viewing and export remain subject to the same authorization.
* **I8** billing, subscription checks, credits, per-view metering, quotas and
  payment integration — not implemented; the viewer is **not plan-gated**.
* **AI**: no RAG, LangChain, vector search, AI summarisation, AI-generated
  locations/provenance or invoice matching. Evidence stays deterministic.
* **No schema/migration change** and **no historical data migration**.
* **No production deployment.**

## 12. Scope stop-condition review

No stop condition was encountered. Specifically: I2 semantics were not changed
beyond the DM-6 correction; the four-tool I3 catalogue is untouched; I4 canonical
audit semantics are untouched (a new D33.1-style `evidence.line_access` audit action
was added, mirroring the existing `evidence.access`); retention/erasure policy,
billing, `ai_content_history`, the synthetic document generator and production
deployment were not touched; and no destructive historical migration was performed.

## 13. Git

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| Remote | `github` (`https://github.com/shomonrobie/CarbonTally.git`) |
| Implementation + documentation commit | recorded in the checkpoint commit message and reported in the task response |
| Push status | pushed to `github/p8-release-reconciled` (see task response for the verified alignment) |

`origin` remains the dead local path `/tmp/ct_step2`; it was **not** modified. No
other clone or branch was touched.

## 14. Status statement

**IMPLEMENTED and TESTED** (backend unit suite + frontend suite run in this
session, with the four pre-existing unrelated failures reported separately).

**Not independently VERIFIED and not ACCEPTED** — this report makes no acceptance
claim. Independent OHD verification and the subsequent PO closure are required, and
per the authorization's final stop condition no I7/I8 work, no deployment and no PO
closure were performed.
