# CarbonTally V3 — D33.1 Evidence Precision & Evidence Record (Final Amendment)

**Date:** 2026-08-23 · **Mode:** additive presentation/audit refinement on D33
**Author:** Cline

---

## 1. Executive summary

D33 established the authoritative lineage chain (emission → calculation snapshot →
extraction item → source document). D33.1 turns that persisted provenance into a
customer-facing, authorized **Evidence Record** that answers *"why is this emission
this number?"* without exposing the database:

```
SOURCE DOCUMENT → ORIGINAL EXTRACTED DATA → CARBONTALLY MAPPING →
EMISSION FACTOR → CALCULATION → EMISSION RESULT
```

The UI clearly separates **ORIGINAL source data** (from the document) from
**CarbonTally-derived** data (mapping, factor, calculation, result), reports
evidence completeness honestly (COMPLETE / PARTIAL / UNAVAILABLE — never
fabricated), states source-location precision truthfully, exposes stable record
identifiers in a scoped "Technical details" expansion, and records append-only
evidence-access audit events (ids only — never URLs/secrets).

## 2. Before/after findings

| Capability | Before (D33) | After (D33.1) |
|---|---|---|
| Customer evidence presentation | Flat meta list (doc name, activity, factor, calculation) | Structured Evidence Record with origin-marked sections (original vs derived), formula, completeness badge, source-location statement, technical-details expansion |
| Original vs derived distinction | Not made | Explicit section labels + `origin` field per section |
| Evidence completeness | Not classified | COMPLETE / PARTIAL / UNAVAILABLE derived from persisted provenance |
| Source-location honesty | Page shown only if persisted | `source_location` block + human-readable statement ("Source line available; page/location not available.") |
| Evidence access audit | Not recorded | Append-only `audit_trail` rows on evidence view + reverse lookup (ids only) |
| Export provenance | snapshot_id, source_item_id, source_file, source_page | + `evidence_status` (COMPLETE/PARTIAL/UNAVAILABLE) |
| Pipeline page precision | Not accepted by the item calculate endpoint | `CalculatePayload.source_page` accepted + persisted on the snapshot |

## 3. Schema changes

**None.** D33.1 is purely additive presentation/audit on the existing D33 schema.
(The optional `source_location` JSONB referenced by the record builder is read from
the snapshot when present but is not introduced by D33.1.)

## 4. API changes

- `GET /api/v3/emissions/{log_id}/evidence` response now includes
  `evidence_record`: `completeness` + `completeness_reason`,
  `source_location` (page/sheet/row/column/json_path + honest `display`),
  `sections` (source_document, extraction, mapping, emission_factor, calculation,
  result — each with `origin: original|derived` + fields), and
  `technical_details` (stable ids + calculation metadata). Writes an
  `evidence.access` audit row (org, snapshot, source file ids).
- `GET /api/v3/documents/{file_id}/emissions` (reverse) writes an
  `evidence.reverse_lookup` audit row.
- `POST /api/v3/processing/items/{id}/calculate` accepts optional
  `source_page` (persisted on the snapshot when the pipeline reliably knows it).
- `GET /api/v3/exports/emissions.{csv,json}` add `evidence_status`.

## 5. Frontend changes

- New `src/v3/components/EvidenceRecordPanel.jsx` — the evidence record UI:
  completeness badge, source-location statement, Emission result / Calculation
## 6. Evidence-record design

Each section carries `origin`:
- **original** — source document + original extracted data (customer's document).
- **derived** — CarbonTally mapping, emission factor, calculation, result.

The `calculation.fields.formula` renders e.g.
`500 kWh × 0.00028 = 0.140 kg CO₂e`. `technical_details` exposes only stable
identifiers (`emission_log_id`, `calculation_snapshot_id`,
`manual_extraction_item_id`, `organization_file_id`, `emission_factor_id`,
`source_file`, `source_page`) plus scoped calculation metadata (methodology,
algorithm version, content hash, timestamps) — no SQL, no credentials, no raw
storage URLs.

## 7. Source-location precision by input type

| Input | Persisted precision | D33.1 statement |
|---|---|---|
| PDF | file + item (line) + page (when pipeline passes it) | "Source document + line with location: document, page N, extracted line." or "Source line available; page/location not available." |
| Image/scanned | file + item | line-level; page not captured |
| CSV | file + item (row = item) | file + row-level (item) |
| Excel | file + item | file + row-level; sheet/cell not captured (documented) |
| JSON | file + item | file + line-level; JSONPath not captured |
| Manual extraction | file + item + page when recorded | same rules |
## 11. Live verification

Real stack (Supabase Docker on :54425/:54426 + backend :8001 + frontend :3000):
upload → 2 extracted lines → map → validate → calculate (source_page=1) → 2
emissions with `evidence_status=COMPLETE`; evidence 200 with completeness
COMPLETE, formula, invoice reference, source page, signed URL, technical ids;
audit rows written (`evidence.access` 2, `evidence.reverse_lookup` 1); reverse
200 + 2; denials 403. **All fixtures removed afterwards** (before: emissions 2 /
snapshots 2 / items 6 / files 5 / factors 1 / evidence audits 8 / storage objects
2 → after: 0 / 0 / 4 / 4 / 0 / 0 / 0).

## 12. Screenshots

`screenshots/d33_evidence/` — 6 new captures (emissions list, evidence record
panel, technical details expansion, source document viewer, documents list,
document → emissions reverse) + updated `UI_SCREENSHOT_MANIFEST.md`.

## 13. Remaining limitations

- Excel sheet/cell references and CSV/JSON row/cell/JSONPath precision are not
  captured by the extraction pipeline (documented; the record honestly reports
  what exists).
- `source_page` must be passed by the pipeline; it is not auto-extracted.
- Audit rows are written per evidence view/reverse lookup (ids only); there is no
  retention policy surface for them (the `audit_trail` table already has the
  D31 admin read-side surface).

## 14. Final release recommendation

**READY** — the evidence-record presentation, completeness honesty,
original-vs-derived separation, technical details, evidence-access audit and
export provenance are implemented, tested and live-verified. D33 lineage and
security are unchanged and intact.


No precision is fabricated — when only document-level provenance exists, the UI
shows "Source document available; exact source location not available."

## 8. Evidence completeness logic

`domain/evidence.py::classify_evidence_completeness`:
- **COMPLETE** — document + extracted line + calculation + factor AND an exact
  source location (page).
- **PARTIAL** — a valid chain without an exact page/location, or an incomplete
  chain.
- **UNAVAILABLE** — no reliable source provenance.
The export's `evidence_status` mirrors this from the persisted columns.

## 9. Security verification

- Authorization unchanged: `require_org_member` + `ensure_org_access` (own org
  only); consultant = ACTIVE grant; entity staff have no customer-evidence path.
- Live: consultant evidence → 403; entity-staff reverse → 403; public storage URL
  blocked; signed URL fetch → 200.
- Audit rows contain ids only (verified: no signed URLs/tokens in audit payloads).
- Private Supabase Storage + D32 signed URLs remain authoritative.

## 10. Tests

| Suite | Result |
|---|---|
| Backend unit (incl. `test_evidence_record.py`) | **1018 passed** (0 failures) |
| RLS integration (`carbontally_test`) | **11 passed** |
| Frontend V3 API Jest | **18/18 passed** |
| Frontend production build | **succeeded** |

  formula / Emission factor / Mapping (CarbonTally-derived) sections, Original
  source data section (document, invoice/reference, supplier, date, extracted
  line), "Open source document" (signed URL), and a **Technical details /
  Evidence record** `<details>` expansion with stable record identifiers.
- `EmissionsPage.jsx` renders the panel from the evidence endpoint.
- `v3.css` — badge/panel/formula/technical-details styles.
