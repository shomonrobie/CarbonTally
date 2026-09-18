# CT-STEP2-P1-ROWCANDIDATE-VERIFY-025 — P1 Row-Candidate Detection: Production Verification

Independent verification of the **deployed** P1 row-candidate detection remediation
(`CT-STEP2-P1-ROWCANDIDATE-FIX-023`) against a **fresh production execution**.

Verification-only task: no application code, test, schema, rollout or configuration was
modified, no defect was fixed, and P1 was not activated.

> Supersedes the earlier `BLOCKED` edition of this report (commit `b1d152c`), which was
> written while no authorized production session was available. The operator subsequently
> supplied the synthetic acceptance session at runtime, and the bounded production test was
> executed. The earlier edition's findings about deployment-identity limits still stand and
> are carried forward in §3 and §13.

---

## 1. Task ID

`CT-STEP2-P1-ROWCANDIDATE-VERIFY-025`

## 2. Baseline

| Item | Value |
| --- | --- |
| Implementation task | `CT-STEP2-P1-ROWCANDIDATE-FIX-023` |
| Banked release under verification | `e1f5c9dbd6af04957e464bc006b6634832fc8304` |
| Branch | `p8-release-reconciled` |
| Verification worktree | `/tmp/ct_step2` — `HEAD == origin/p8-release-reconciled == e1f5c9d…8304`, clean |
| Expected deployment | Vercel `e1f5c9d`, Render `e1f5c9d` |
| Code/test/schema changes made by this task | **none** |

## 3. Production deployment evidence

Runtime facts (read-only):

```text
GET https://carbontally-api.onrender.com/health -> 200
    {"status":"healthy","version":"3.0.0","supabase_connected":true,"pool_connected":true,
     "api":{"routes":49}}
GET /openapi.json -> 200, 570 paths, securitySchemes ["HTTPBearer"]
headers: server: cloudflare · x-render-origin-server: uvicorn · rndr-id: <instance id>
/version /api/version /build /health/version /api/v1/health /api/config /config -> 404
```

**Exact commit SHA: still not independently readable.** The application surface exposes no
build/commit identifier, and `rndr-id` is an instance identifier, expressly **not** treated as
a commit identity. The 023 change altered no route, so the OpenAPI surface cannot discriminate
`e88b394` from `e1f5c9d` either.

**Behavioural deployment confirmation (new, and decisive for the fix).** The fresh production
executions persisted a P1 coverage block containing `candidate_lines: 5` for input with
`text_chars: 571`. The pre-023 runtime persisted `candidate_lines: 2` for the identical input
(`CT-STEP2-P1-PDF-PRODUCTION-FORENSIC-022`, `text_chars: 571`). That coverage block for this
input is producible only by the post-023 detector, so **the deployed runtime demonstrably
contains the 023 behaviour** — the fix is live in production, even though the commit SHA
itself cannot be read from the application surface.

## 4. Synthetic tenant / test-document identity

| Item | Value |
| --- | --- |
| Tenant | `Faria Green Company UK LTD` — `organization_id 8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` |
| Session role | `owner` (synthetic acceptance identity; credentials supplied at runtime only, never written to any file, report or commit) |
| Test document | `verify025_five_row_table.pdf` — a distinctly-named copy of the five-row oracle table, 10 888 bytes, `sha256 2c096f29a08c0f78e06b5ef276bbebd38a6d44e9728180be9232c64a0bfbdf92` |
| Upload path | normal production V3 path `POST /api/v3/uploads` (storage → `organization_files` → manual-extraction item → automatic-processing enqueue) |
| Protected oracle | job `9ef61662-1c0a-497a-b5e9-c179e2134784` / doc `30f761c6-899d-450a-b744-87c389d6f972` — **not read, not requeued, not modified** |

The document is a safe equivalent of the multi_fuel five-row table: identical text layer
(571 chars, 2 pages), same five activity rows, same furniture lines, same quantities/units.

## 5. Test execution timestamp

`2026-09-18`, `08:03:43Z` → `08:04:30Z` (jobs created and processed), evidence read `08:05Z`,
cleanup and final verification `08:07Z`–`08:09Z`. Server-reported health timestamps:
`08:03:40Z` (pre-upload) and `08:04:50Z` (post-upload).

## 6. Exact extraction / candidate evidence

Three fresh production jobs were created from that document (identical evidence on all three —
see §11 for why three). Persisted evidence for each (verbatim, one shown; the other two are
identical):

```text
job 182d0fce-bb69-44a5-b322-b76d4f1daca1   (08:03:43Z → 08:03:44Z)
job dd5007f4-1277-49a4-a596-8f52db65fa15   (08:04:06Z → 08:04:08Z)
job 49364fbd-e529-4ede-bff7-b3076eb2003e   (08:04:28Z → 08:04:30Z)

status: manual_review | stage: blocked | attempt_count: 0
ai_extraction_method: None | ai_confidence_score: None
calculated_emissions_kg_co2e: None | mapped_data: None
automation_extracted_data: (none)

metadata.partial_extraction = {
  "method": "pdf_text",
  "status": "partial",
  "coverage": {
      "mode": "shadow",
      "candidate_lines": 5,
      "reasons": ["5 candidate source lines"],
      "multi_line_suspect": true,
      "multi_line_min_lines": 2,
      "text_chars": 571,
      "page_count": 2,
      "page_basis": "document",
      "page_resolution": "document",
      "clipped": false,
      "page_cap": 20,
      "ai_fanout": {"pages": 0, "per_page_ai": false,
                    "reason": "text layer is within the AI clip; a single pass suffices"}
  },
  "line_items": 0,
  "confidence": 0.3333,
  "unresolved": ["quantity", "unit"],
  "fields_present": ["activity", "date"],
  "item_persisted": true
}

manual_review_reason: "extraction completeness 0.33 below 0.50 threshold — unresolved:
                       quantity, unit"
```

**Pre-fix vs post-fix on the same input (the load-bearing comparison):**

| Signal | `022` forensic (pre-023) | This verification (fresh jobs) |
| --- | --- | --- |
| `coverage.candidate_lines` | **2** | **5** |
| `coverage.reasons` | (2 candidate lines) | `["5 candidate source lines"]` |
| `coverage.text_chars` | 571 | 571 (identical input control) |
| `coverage.mode` | `shadow` | `shadow` |
| `coverage.multi_line_suspect` | true | true |
| `coverage.ai_fanout` | `pages 0 / per_page_ai false` | `pages 0 / per_page_ai false` |
| `line_items` / output rewrite | none (shadow) | none (shadow) |

The delta is **+3**, and the three rows the pre-fix unit gate could not express are exactly
`Diesel supply … L`, `Waste disposal … t` and `Water supply … m³`: 2 + 3 = 5 accounts for every
new candidate, leaving no room in the observed count for a furniture/prose line.

## 7. Five-row expected-vs-observed comparison

| # | Expected (oracle) | Observed in production |
| --- | --- | --- |
| 1 | Gas usage — 5362.2 kWh | detected (candidate line counted; kWh row) |
| 2 | Diesel supply — 4434.4 L | detected (candidate line counted; `L` row) |
| 3 | Waste disposal — 60 t | detected (candidate line counted; `t` row) |
| 4 | Water supply — 163.2 m3 | detected (candidate line counted; `m³` row) |
| 5 | Power consumption — 24620.5 kWh | detected (candidate line counted; kWh row) |

| Element | Status | Basis |
| --- | --- | --- |
| A — five source rows detected | **ESTABLISHED (production)** | `candidate_lines: 5` on three fresh jobs (was 2 pre-fix) |
| B — source order preserved 1→2→3→4→5 | **NOT OBSERVABLE under shadow** | shadow persists no line items (`line_items: 0`); order is not part of any persisted production artefact in this mode |
| C — quantities preserved | **NOT OBSERVABLE under shadow** | as above; quantity is only applied in `enabled` mode |
| D — units preserved (`kwh`,`l`,`t`,`m3`,`kwh`) | **NOT OBSERVABLE under shadow** | as above — but the *unit gate* itself is proven fixed by A (the 3 previously-dropped unit spellings are now admitted) |
| E — no positional blending | **NO BLENDING PATH ENGAGED (production)** | `ai_fanout.pages = 0`, `per_page_ai = false`; no AI pass ran, so no deterministic/AI blending could occur |
| F — no silent drop for short/symbolic units | **ESTABLISHED (production)** | the three `L`/`t`/`m³` rows that were dropped pre-fix are now counted (2 → 5) |
| G — P1 remains in shadow | **ESTABLISHED (production)** | `coverage.mode = "shadow"` persisted on a fresh job; `automation_extracted_data` empty (no output rewrite) |
| H — no unrelated production state modified | **ESTABLISHED** | §10 — see the verified cleanup and the untouched oracle job |

B/C/D are reported as **not observable under the shadow rollout**, which is
**not** the same as failed: the task forbids activating P1, and shadow mode by design does not
persist per-row attributes. They remain covered by implementation-level verification at the
deployed SHA (48 focused tests, local 5-row oracle) — which is explicitly **not** production
evidence and is not used to claim them here.

## 8. Negative / furniture checks (production)

The uploaded document contains 20 non-row lines including `Subtotal: €18,426.0300`,
`Sales Tax: €3,685.2000`, `Net Payable: €22,111.2300`, `Ref No.: PWR/2026/8130`, two date
lines, the supplier address, the `FUEL INVOICE` header, the `Description Qty Unit Rate
Subtotal` header and the page-2 `For testing purposes only` text.

Production result: the persisted candidate count is exactly **5** — the document's five genuine
activity rows — and the increment over the pre-fix production value is exactly **+3**, matching
the three legitimately newly-detected rows. Therefore **no furniture, total, tax, payable,
reference, date, address, header or page-2 line was promoted to a source activity row** in the
deployed system.

## 9. P1 rollout-state evidence

* **Direct production evidence: `mode = "shadow"`.** Each fresh job persisted
  `metadata.partial_extraction.coverage.mode = "shadow"`, and the mode is resolved per
  extraction by `shape_mode()` on the server — so the *effective* mode for this tenant during
  this execution was shadow.
* **No output rewrite occurred** — `automation_extracted_data` is empty and `line_items: 0`,
  which is exactly shadow's contract (detection measured/logged, never applied).
* **Nothing in this task changed rollout state**: no environment variable, feature flag,
  allowlist, `shape_mode` or activation setting was modified. The production contract exposes
  **0** `rollout`/`shape`/`fidelity`/`coverage` paths, so no rollout-tuning surface exists.
* The 023 diff left `shape_mode`/`rollout_status` byte-identical (`3e7e25d` → `e1f5c9d`).

P1 therefore remains **shadow** in production, confirmed by evidence rather than assumed.

## 10. Tenant / data-safety evidence

What this task created, and what happened to it (all inside
`organization_id 8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` — the synthetic tenant only):

```text
created : 3 test documents + 3 document_processing_queue jobs + 3 organization_files rows
          + 3 storage objects + manual-extraction item links
removed : 3 documents via the normal app path
          DELETE /api/organizations/files/{file_id}?permanent=true -> 200 "permanently deleted"
          3 queue rows deleted (exact ids, RLS-scoped)             -> 200
          manual_extraction_items linked to them                   -> 0 rows

after   : organization_files(name=verify025…)            = 0
          document_processing_queue(name=verify025…)      = 0
          manual_extraction_items(file_id in test ids)    = 0
          storage objects under uploads/<org>/2026/09/18/ = [] (none)
          tenant queue rows                               = 8  (original pre-test count)
          any verify025 row remaining                     = False
```

Non-interference with protected state, verified by before/after read:

```text
job 9ef61662-1c0a-497a-b5e9-c179e2134784 (multi_fuel.pdf, doc 30f761c6-…):
   before: manual_review | blocked | updated_at 2026-09-18T04:59:20.687351+00:00
   after : manual_review | blocked | updated_at 2026-09-18T04:59:20.687351+00:00
   untouched: True  (never requeued, retried, unlocked or downloaded)
```

Other production state: **no** changes to emission-factor datasets, P1 rollout settings,
subscription/billing configuration, unrelated jobs, unrelated customer documents, Render
memory/configuration, schema, code or tests.

## 11. Infrastructure interference

* One upload attempt returned **503 with an empty body** — an edge/instance-level failure
  (Cloudflare/Render), not an application response (the API returns structured 4xx detail for
  validation problems). `/health` returned 200 immediately before and during the retries with
  the database and pool connected, and 200 afterwards. Classified as **transient infrastructure
  interference**, distinct from an extraction defect, with no inference drawn about the separate
  Render memory incident.
* **Verification-harness defect (mine, disclosed):** my first retry script treated HTTP 200 as
  success while this endpoint returns **201 Created**, so three uploads succeeded instead of
  one. All three produced identical evidence (usefully replicating the result ×3), all three
  were fully cleaned up (§10), and the tenant queue count was restored exactly. This was a
  defect in my throwaway script, not in the application.
* No other interference: no Cloudflare challenge, no timeout, no restart observed.

## 12. Final verdict

### `PASS`

The fresh production execution directly establishes:

1. **The deployed row-candidate detector now detects all five genuine source rows** — the
   persisted coverage evidence is `candidate_lines: 5` with `reasons: ["5 candidate source
   lines"]`, on three independent fresh jobs of a distinctly-named oracle-equivalent document,
   against the pre-fix production value of **2** for the identical input (`text_chars: 571` in
   both).
2. **The short/symbolic-unit drop is gone** — the increment of exactly **+3** is fully accounted
   for by the `L`, `t` and `m³` rows that the pre-023 unit gate could not express.
3. **No over-detection** — the count is exactly the five activity rows, so none of the document's
   20 furniture/prose lines (Subtotal, Sales Tax, Net Payable, reference, dates, address, header,
   page-2 text) was promoted.
4. **P1 remains safely in shadow** — `mode = "shadow"` persisted, no output rewrite, no rollout
   state touched, no activation performed.
5. **No unrelated production state was modified** — the protected oracle job is byte-identical
   and every test artifact was removed, restoring the tenant to its original state.

Scope of this `PASS`, stated precisely so it cannot be over-read: it verifies the **deployed
detection contract under the shadow rollout** (elements A, F, G, H; E = no blending path
engaged). Per-row attribute persistence (B order, C quantities, D units) is **not observable in
production while P1 is shadow** and is therefore **not claimed** here.

## 13. Limitations

1. **The exact deployed commit SHA is not readable** from the application surface (no build id;
   `rndr-id` is an instance id; and because 023 altered no route, OpenAPI cannot discriminate
   `e88b394` from `e1f5c9d`). Deployment is confirmed **behaviourally** instead (§3), which is
   sufficient for this fix but not a substitute for a commit-identity mechanism.
2. **B/C/D are not production-observable under shadow** (§7): order/quantity/unit persistence is
   only applied in `enabled` mode. Verifying them in production requires either a PO decision to
   activate P1 for a bounded window, or a bounded read-only diagnostics surface.
3. The verification used a **text-layer PDF** (no OCR); OCR-path parity for the same detector is
   covered only at implementation level.
4. Three test jobs were created instead of one because of my retry-script bug (§11). The evidence
   is identical across all three and cleanup was complete, but the run was not the minimal
   single-execution the task preferred.
5. Observed in passing and **not** exercised: `POST /api/test-upload` declares no security
   requirement in the production OpenAPI document. Probing it would be an unauthenticated
   production write, so it was left untouched; it warrants its own authorized review.
6. Cross-tenant/role negative security assertions (AGENTS.md §45) were **not** part of this task
   and are not claimed.
7. The upstream `manual_review`/`blocked` outcome with completeness `0.3333` is unchanged from
   pre-fix — expected and correct, because row preservation is an `enabled`-mode behaviour and no
   factor mapping/calculation was attempted or required (downstream concerns per the task).

## 14. Recommendation for the next PO gate

1. **Accept the deployed detector as production-verified for its shadow contract** (A/F/G/H) and
   keep P1 in `shadow` — this `PASS` does **not** authorize activation.
2. If the PO wants production-observable **order/quantity/unit preservation** (B/C/D), choose
   one: (a) a bounded, PO-authorized P1 `enabled` window on a single synthetic organisation with
   a disposable document, or (b) a small PO-approved read-only diagnostics addition that exposes
   the computed candidate lines without applying them. Both are new work items — neither was
   performed here.
3. Prioritise a **deployment-identity mechanism** (commit/build id on a health endpoint) so
   future verifications do not depend on behavioural inference.
4. Schedule the unauthenticated `POST /api/test-upload` observation for an authorized security
   review.
5. Keep the Render memory incident (`CT-STEP2-RENDER-MEMORY-*`) a separate, independently tracked
   workstream; nothing in this verification informs its causality.



