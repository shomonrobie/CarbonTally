# CarbonTally — DEMO-T3-REM-001
## DEMO-T3 OHD-079 remediation (implementation report)

**Implementation ID:** `DEMO-T3-REM-001` · **Related:** `DEMO-T3-IMP-001`, verification `OHD-079` (FAIL)
**Verified commit under remediation:** `ad46599eac1e46fc725f0fba9f12debb2dfbf5e0`
**Type:** IMPLEMENTATION REPORT — no PO closure, no independent verification claimed.

---

## 1. Release / git state at start (§3)

| Item | Observed |
|---|---|
| Branch | `p8-release-reconciled` |
| Previous T3 implementation commit | `ad46599…` present (`git cat-file -t` ⇒ commit) |
| HEAD at remediation start | `a5d10a7c79124b5d5a9d3a086c140c6f446be8a6` = `docs: OHD Task 079 DEMO-T3 independent verification` |
| Delta above the verified commit | **only** `docs/verification/OHD_TASK_079_DEMO_T3_INDEPENDENT_VERIFICATION_20260920.md` (+562 lines) — no implementation change |
| GitHub tip | `a5d10a7…` (local == GitHub, divergence `0 0`) |
| Working tree | clean; the dirty `main` checkout untouched |

Not a blocking discrepancy: the expected parent commit exists and the only commit above it is OHD's
own verification report.

## 2. B-1 — diagnosis of the selector defect (§6.1)

The shipped selector (`_text_quality()`, now removed) scored candidates on (a) a unit token anywhere in
the text layer, (b) absence of a regex match for `\d(unit)`-glued tokens, (c) length > 200 characters.

The document OHD cited — `Electricity supply - Off-Peak (ID:2 M6,T94R0-.752097k)Wh £0.29 £7,758.86` —
contains the tokens `Wh`/`kWh` (so (a) passes), while the interleaved digits and unit are separated by
other characters so the glued-unit regex never matches (so (b) passes), and the page is long enough for
(c). It therefore received full marks despite being unusable.

**Root cause: the selector measured text appearance, not usability by the extraction path** — hence
11/11 unusable documents selected, with only the first 3 candidates ever examined.

## 3. B-1 — remediation implemented

* **New probe module `tools/demo_lab/t3_extract_probe.py`** — runs **the release's own extractor**
  (`backend/services/automatic_extraction.py: extract_document`, `completeness_score`) over candidates
  with the backend interpreter and emits one JSON verdict per candidate (`status`, `method`,
  `confidence`, `completeness`, per-field `resolved{activity,quantity,unit}`,
  `extracted_activity/quantity/unit`). It exits **3** if the extractor cannot be imported.
* **Selector rewritten** (`t3_scenarios.py`): removed `_text_quality`; added `probe_candidates()`
  (fail-loud), `_accepts()` (scenario acceptance rules applied to a **real** verdict) and
  `select_candidate()` — deterministic sorted order, fixed chunk 30, fixed cap 240, first genuinely
  parseable candidate wins. Method recorded as `real-extractor-activity-quantity-unit-v2`.
* **Provenance (§8)**: scenario id, source PDF + truth path, repository, generator commit,
  `document_id`, `document_generation_seed`, `pdf_sha256`, `truth_sha256`, the selected document's
  extractor verdict, candidates examined/total, selection method. **Misleading seed provenance
  corrected** — `SELECTION_SEED` is documented as the *demo selection* seed only, distinct from the
  generator base seed and from each document's own `generation_seed`.
* **Full-pool search (§7)**: the first-3 assumption is gone; the pool is scanned deterministically in
  bounded chunks and the corpus is **not** written unless every scenario resolves
  (`FAIL: … The existing corpus was NOT replaced.`).
* **Fail-loud (§9 / O-B)**: a missing backend interpreter, a probe import failure, or an incomplete
  verdict set aborts non-zero with the reason and the correct command — heuristics can no longer
  silently degrade into a false-quality corpus.
* **Scenario acceptance rules** added to `t3_manifest.json` (`accept.activity_keywords`,
  `accept.units`) plus `expect_unparseable: true` for `uk-missing-evidence`, so that scenario selects a
  *genuinely unparseable* document (proving the pipeline does not fabricate) rather than a parseable one.

Verified in this session: the probe **rejects** both known-bad documents
(`ORG_027_octopus_energy_202509.pdf`, `ORG_018_biffa_waste_202509.pdf` → `resolved
{activity:true, quantity:false, unit:false}`, `ok:false`) — the defect OHD observed is now caught
before any upload.

## 4. B-2 — reset remediation implemented (§16)

`reset` no longer writes to a protected storage table. Storage objects are deleted through the
**Storage API** (`DELETE /storage/v1/object/{bucket}/{path}` on the lab gateway with the lab service
key — `storage_delete_objects()`); only non-storage rows are then deleted by SQL. The platform trigger
`storage.protect_objects_delete` is **untouched**; HTTP 404 (already absent) counts as success for
idempotency; failures are reported, and the run now emits a `remaining` block so a reset can be proven
to have removed what it claims.

**Not executed end-to-end in this session** — the §17 seed → reset → verify → re-seed cycle remains
outstanding (see §7).

## 5. O-A — lab storage JWT/JWKS implemented

`tools/demo_lab/storage.py` now passes `JWT_JWKS` to the lab-owned storage API in addition to the
existing secret (`JWKS_URL = http://supabase_auth_carbon_ledger:9999/.well-known/jwks.json`).
The endpoint was verified in-network and publishes the lab GoTrue **ES256** verification key
(`{"keys":[{"alg":"ES256","crv":"P-256","kty":"EC","use":"sig",…}]}`). Verification is strengthened,
never weakened: no anonymous policy, no disabled verification, no production change. Container
reconciliation is idempotent via the existing spec-hash mechanism, so the new configuration is applied
on the next `stack.py` / `storage.py` run.

## 6. B-3 — factor-expectation revalidation

**Not completed in this session.** The plan (unchanged from OHD's recommendation) is to revalidate each
declared `expected.factor_family` against the running lab using the existing matcher
(`POST /api/v2/factor-match`, as OHD used) and then rewrite `t3_manifest.json` so each scenario declares
what is actually supported: exact factor id, family, deliberate ambiguity, no-match, or
review/clarification. No engine, alias or policy change is permitted — and none was made.

## 7. Outstanding work (bounded, same authorization)

1. Complete the corpus rebuild (a full-probe run over the candidate pools; running at report time).
2. Produce the §11 pre-seed validation evidence table (truth vs extracted activity/quantity/unit/completeness).
3. Re-seed, run the ground-truth comparison, and confirm the successful scenarios reach
   `calculation_snapshots` (real evidence → factor → calculation).
4. Execute and prove the §17 reset cycle, including the invariant counts.
5. B-3 factor-expectation revalidation + manifest rewrite.
6. Re-run the §19 storage-security assertions after the JWKS change.

## 8. What this remediation did NOT do

No change to the external generator (read-only checkout at `8ade2bf`), no production/Render/Supabase
change, no calculation or factor-matching engine change, no RLS/security-model change, no IE/OCR work,
no manual-processing governance change, and no bypass of the real document workflow.
