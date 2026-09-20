# OHD Task 079 — DEMO-T3 Independent Verification

**Task ID:** OHD-079
**Verification date:** 2026-09-20
**Verified commit:** `ad46599eac1e46fc725f0fba9f12debb2dfbf5e0` (`feat: implement DEMO-T3 audit-grade demo lab`)
**Parent / previously authoritative release:** `8c54f8eddc0d653a9cfa7babdc41c973a5e0a627`
**Repository:** `https://github.com/shomonrobie/CarbonTally.git`, branch `p8-release-reconciled`
**Verified by:** independent verifier (OpenHands / OHD) — read-only against the release; no implementation file was modified
**Overall verdict:** **FAIL** (see §20)

Every claim below is labelled:

* **VERIFIED** — reproduced/observed directly by OHD in this session.
* **CODE-TRACED** — established by source inspection, not runtime-tested.
* **CLAIMED** — asserted only by the implementation report itself.
* **NOT VERIFIED** — could not be independently established.

---

## 1. Scope

This verification covers the DEMO-T3 authorization only:

> "Yes, build a deterministic, audit-grade Demo Lab using real CarbonTally APIs, with synthetic
> documents generated externally and kept outside the runtime, while keeping IE and OCR as later
> bounded work."

The fifteen numbered authorization points, the storage substrate, the corpus, the real-API ingestion
path, ground-truth verification, factor mapping, calculation/provenance, the report layer, consultant
parity/isolation, manual-processing governance, idempotency/reset, production safety, out-of-scope
confirmation and negative paths were each tested as described below. IE/SEAI and OCR were **not**
exercised beyond confirming they remain deferred.

---

## 2. Repository / commit verification

| Check | Observed | Status |
|---|---|---|
| Branch | `p8-release-reconciled` | VERIFIED |
| Pre-T3 release | `8c54f8eddc0d653a9cfa7babdc41c973a5e0a627` exists and is the T3 commit's parent | VERIFIED |
| DEMO-T3 commit(s) | exactly one: `ad46599eac1e46fc725f0fba9f12debb2dfbf5e0` | VERIFIED |
| Commit metadata | `feat: implement DEMO-T3 audit-grade demo lab`, author `shomonrobie <shomonrobie@gmail.com>`, Sun Sep 20 19:31:54 2026 +0600 | VERIFIED |
| GitHub authoritative tip | `git ls-remote github refs/heads/p8-release-reconciled` ⇒ `ad46599…` | VERIFIED |
| local == GitHub | **yes** (identical object) | VERIFIED |
| Working tree | `git status --porcelain --untracked-files=all` ⇒ 0 lines | VERIFIED |
| Committed *and* pushed | yes — not a verification blocker | VERIFIED |
| Files changed | 6, all in `tools/demo_lab/` + one doc; **no** `src/`, `backend/`, `supabase/`, migration, RLS or frontend file | VERIFIED |

`git diff --name-status 8c54f8e ad46599`:

| Status | File | +/- |
|---|---|---|
| A | `docs/architecture/CARBONTALLY_DEMO_T3_IMPLEMENTATION_20260920.md` | +260 |
| M | `tools/demo_lab/lab.py` | +5 / −1 |
| M | `tools/demo_lab/stack.py` | +14 / −0 |
| A | `tools/demo_lab/storage.py` | +312 |
| A | `tools/demo_lab/t3_manifest.json` | +174 |
| A | `tools/demo_lab/t3_scenarios.py` | +580 |

`git diff --stat 8c54f8e ad46599 -- src/ backend/ supabase/` ⇒ **empty**.
`git diff --stat … -- '*requirements*.txt' pyproject.toml backend/pyproject.toml` ⇒ **empty**.

---

## 3. Environment

| Component | State | Status |
|---|---|---|
| Lab database | `carbontally_demo_local` on the stack Postgres `supabase_db_carbon_ledger:5432` (host `127.0.0.1:54426`) | VERIFIED |
| Lab backend | `uvicorn main:app` on `127.0.0.1:8070`, `/health` ⇒ 200 (`supabase_connected`, `pool_connected` true) | VERIFIED |
| Lab gateway | `127.0.0.1:54430` (`/auth/v1`, `/rest/v1`, `/storage/v1`) | VERIFIED |
| Lab storage container | `carbontally_demo_lab_storage` (storage-api v1.69.0, `STORAGE_BACKEND=file`, `DATABASE_URL=…/carbontally_demo_local`) up | VERIFIED |
| `GET /storage/v1/version` | 200 → `1.69.0` | VERIFIED |
| Storage schema | `storage` schema present in the lab DB | VERIFIED |
| Buckets | `documents`, `report-artifacts`, both `public = f` (private, 50 MiB limit) | VERIFIED |
| D32 policies | exactly 4, all `{authenticated}`: `d32_documents_{select,insert,update,delete}_org_member`; **0** anon/public policies | VERIFIED |
| Migrations | lab DB carries `schema_migrations`; report claims all 75 apply cleanly with `migrations_with_errors: []` | CLAIMED |
| Lab identities | 13 `auth.users`, 4 organisations, 8 memberships, 2 consultant clients | VERIFIED |
| External generator checkout | `/tmp/extgen` = clone of `shomonrobie/carbon_tally_synthetic_documents_generator`, HEAD `8ade2bf778d518d59924905849ab114ab2d0820a`, branch `main`, clean | VERIFIED (**pinned commit matches exactly**) |
| Factor slice | 7,049 DEFRA-2025/SEAI-2025 factors, one active batch per provider (from T2-C) | VERIFIED |

No production or hosted environment was contacted; every endpoint used is `127.0.0.1`.

---

## 4. External-generator separation (§4 of the task) — **VERIFIED**

| Check | Evidence | Status |
|---|---|---|
| Pinned commit | `git -C /tmp/extgen rev-parse HEAD` ⇒ `8ade2bf778d518d59924905849ab114ab2d0820a` | VERIFIED |
| No runtime import | `grep -rn "import generator\|from generator\|run_generation\|bulk_carbontally_generator\|prepare_samples" backend src tools` ⇒ no match | VERIFIED |
| No vendored copy | no generator directory under `tools/`; the release's only `*synthetic*` path is its own pre-existing `tools/generate_synthetic_documents.py` | VERIFIED |
| No dependency acquisition | requirements/pyproject diff empty | VERIFIED |
| No production module executes it | only references are documentation plus the pinned constants `GENERATOR_REPO`/`GENERATOR_COMMIT` in `tools/demo_lab/t3_scenarios.py` and `t3_manifest.json` | VERIFIED |
| Corpus produced externally, supplied as files | `sync-corpus --source /tmp/extgen` reads the checkout and copies PDF + truth sidecar into `<state>/corpus/t3-uk-curated-v1/` (outside the repo) | VERIFIED |
| Provenance recorded | `corpus_provenance.json` records repo, commit, seed, `source_pdf`, per-document `generation_seed`, `quality`, and PDF `sha256` | VERIFIED |
| Offline helper is not a runtime dependency | the helper only *reads* the pinned checkout and copies *documents* | VERIFIED |

This is a correct and clean separation; it is **not** classified as a runtime dependency.

---

## 5. Demo-Lab storage (§5) — **VERIFIED with one non-blocking gap**

Exercised the real storage path with real lab tokens (GoTrue password grant) and the app's own
endpoints.

| Test | Result | Status |
|---|---|---|
| App upload path stores objects | 11 T3 documents uploaded, each with a `storage.objects` row in `documents` under `uploads/<org-uuid>/<date>/<hash>_<filename>` | VERIFIED |
| Buckets private | `public = f` for both buckets | VERIFIED |
| Policies org-scoped, authenticated-only | 4 D32 policies, roles `{authenticated}`; no anon policy | VERIFIED |
| Authenticated retrieval (app path) | `GET /api/v3/documents/{id}/signed-url` ⇒ **200** with a `/storage/v1/object/sign/documents/…?token=…` URL; fetching it **without any auth header** ⇒ **200**, 5,164 bytes, `%PDF-` magic, `Content-Type: application/pdf` | VERIFIED |
| Object ownership/scoping | objects keyed by uploading org UUID (`3fd0f325…` Org A, `f03fb375…` Org B, `02b38744…` Client A, `b4bb08f1…` Client B) | VERIFIED |
| Cross-tenant retrieval | Org B token → Org A object and vice versa ⇒ denied (403) | VERIFIED |
| Unauthorised access | no token ⇒ 401/404 (anon cannot see the private bucket) | VERIFIED |
| Direct user-JWT storage calls | `GET /storage/v1/bucket` and `POST /storage/v1/object/...` with a lab user token ⇒ `400 {"statusCode":"403","error":"Unauthorized","message":"\"alg\" (Algorithm) Header Parameter value not allowed"}` | VERIFIED — **gap O-A** |
| Persistence | objects still present after the pipeline ran; referenced by `organization_files` | VERIFIED |
| Report-artefact bucket | `report-artifacts` exists and is private but contains **0 objects**; `POST /api/v2/generate-report` returns `"storage_url": ""` | VERIFIED — **observation O-E** |

**Gap O-A (root cause identified):** the lab-owned storage container is started with only
`PGRST_JWT_SECRET` (HS256) and **no `JWT_JWKS`**, while the developer's stack storage container carries
`JWT_JWKS` including the GoTrue **ES256** public key (`kid b81269f1-21d8-4f2e-b719-c2240a840d90`). The
lab GoTrue issues `alg: ES256` tokens, so the lab storage API rejects *user* JWTs. The application's own
document flow is unaffected (backend uses its service-key client plus signed URLs), so this is recorded
as a non-blocking substrate gap: the lab container config does not match the stack's, so the
"representative of the CarbonTally storage contract" claim holds only for the service-key path.

---

## 6. Real document ingestion path (§6) — **VERIFIED (API-only), journey incomplete**

| Check | Evidence | Status |
|---|---|---|
| Seeder uses real APIs | `t3_scenarios.py` calls `POST /api/v3/uploads` (direct) and `POST /api/v3/consultants/clients/{client_id}/documents` (consultant), then `POST /api/v3/processing/documents/{file_id}/enqueue`; no SQL INSERT/UPDATE for documents, evidence, extraction, calculations or reports | VERIFIED (code) + VERIFIED (run) |
| Tooling DB access read-only | `_scalar`/`lab.psql` SELECT probes only; the sole destructive statement is the corpus-scoped `reset` | VERIFIED |
| Direct-customer document creation | `org_a_owner` ⇒ **201**, real `organization_files` row, real `storage.objects` object, real D23 batch/item, real `document_processing_queue` job | VERIFIED |
| Consultant-client document creation | `consultant_owner` ⇒ **201** for Client A and Client B, rows scoped to the client org UUIDs | VERIFIED |
| Organization/client scope | verified per row against `organizations` ids | VERIFIED |
| Processing job creation | 11 jobs, one per scenario, `attempt_count` 0–1, `source_item_id` populated (evidence linkage present) | VERIFIED |
| Processing/extraction | **FAILED in practice** — every job ends `manual_review`/`blocked` | VERIFIED (failure) |
| Evidence creation | `organization_files` + `storage.objects` + `document_processing_queue` + `manual_extraction_items` rows exist per scenario | VERIFIED |
| Calculation path | **never reached** — 0 `calculation_snapshots` for all T3 jobs | VERIFIED (failure) |
| Provenance | job rows carry `source_item_id`; `factor_id`/`factor_set`/`country`/`scope`/`content_hash` exist only on snapshots, of which there are none | VERIFIED |
| Support metadata vs bypass | the seeder writes **no** rows of its own; every document row came from the API/pipeline | VERIFIED |

Explicit enqueue returns **422** for an already-auto-enqueued document — consistent with observation O-G.

---

## 7. Deterministic corpus (§7) — **FAIL**

Corpus: `t3-uk-curated-v1`, 11 scenarios, UK-only, all documents text-native (`is_scanned`
absent/false in every sidecar), provenance recorded with repo + commit + seed + `source_pdf` +
per-document `generation_seed` + PDF SHA-256.

Reproducibility tests:

| Test | Result | Status |
|---|---|---|
| Re-sync from the pinned checkout (scoring enabled, backend venv python) | selection reproduced for **10 of 11** scenarios (identical source documents to the shipped corpus/DB uploads) | VERIFIED |
| `uk-water` | selects `ORG_021_thames_water_202607.pdf` while the shipped corpus and the DB upload use `…_202605.pdf` | VERIFIED — **observation O-C** |
| Run-to-run stability | two consecutive identical invocations produced identical selections | VERIFIED |
| Dry-run vs real selection | identical (11/11) | VERIFIED |
| Re-sync with the ambient `python3` (documented usage) | every candidate scored **0** with `"error": "pdfplumber unavailable: No module named 'pdfplumber'"`, so the selector silently took the alphabetically first candidate for **all 11** scenarios, exit 0, no warning | VERIFIED — **observation O-B** |
| Seed provenance | manifest records `"seed": 42`, but the selected documents record per-document `generation_seed` values (2699260036, 1528123073, 1754253840, …) — 42 is not the seed that produced them | VERIFIED — **observation O-F** |

**Blocking defect B-1 (corpus).** CarbonTally's own deterministic extractor
(`backend/services/automatic_extraction.py::extract_document`) was executed directly against the 11
shipped corpus documents and compared with their ground-truth sidecars:

| Scenario | Ground truth (first line) | CarbonTally extraction | completeness |
|---|---|---|---|
| uk-electricity | 26940.5 kWh | Electricity / **None** / **None** | 0.33 |
| uk-gas | 8398.67 kWh | Natural gas / **39.0** / **L** (wrong qty + unit) | 1.00 |
| uk-diesel | 6953.75 L | Diesel / **22645.0** / **T** (wrong qty + unit) | 1.00 |
| uk-waste | 2.1 tonnes | Waste / None / None | 0.33 |
| uk-water | 152.7 m³ | Water / None / None | 0.33 |
| uk-spend | 63.47 km | **None / None / None** | 0.00 |
| uk-ambiguity | 11205.87 kWh | **Natural gas** / None / None | 0.33 |
| uk-missing-evidence | 211.1 miles | Travel / None / None | 0.33 |
| consultant-client-a | 51000.7 kWh | Electricity / None / None | 0.33 |
| consultant-client-b | 39.89 tonnes | Waste / None / None | 0.33 |
| direct-org-b-isolation | 39494.0 kWh | Electricity / None / None | 0.33 |

**11 of 11 documents are mis-extracted.** Root cause (VERIFIED): the watermarked generator layouts
interleave the quantity/unit columns in the PDF text layer. The "clean", score-3 uk-electricity
document contains:

```
Description Qty Unit Rate Net Total
Electricity supply - Off-Peak (ID:2 M6,T94R0-.752097k)Wh £0.29 £7,758.86
```

The selector's `_text_quality()` docstring claims to score "a separable quantity+unit pair", but the
code only tests (a) unit-token presence, (b) a `\d(kwh|litre|…)` "glued" regex, (c) text length — it
never verifies that a quantity/unit pair is actually parseable. Documents the extractor cannot read
therefore score 3/3 and win the selection.

**A workable corpus existed.** Running the same extractor over the full candidate pool for each
scenario glob (44–168 candidates each, all with truth sidecars) shows correctly-parseable
alternatives for **every** scenario:

| Scenario | candidates in glob | scanned until first correct | first correct candidate |
|---|---|---|---|
| uk-electricity | 120 | 35 | `ORG_027_octopus_energy_202510.pdf` |
| uk-gas | 132 | 7 | `ORG_018_british_gas_202511.pdf` |
| uk-diesel | 96 | 28 | `ORG_029_certas_energy_202606.pdf` |
| uk-waste | 96 | 18 | `ORG_018_biffa_waste_202602.pdf` |
| uk-water | 44 | 16 | `ORG_030_thames_water_202606.pdf` |
| uk-spend | 168 | 105 | `ORG_023_royal_mail_202509.pdf` |
| uk-ambiguity | 84 | 58 | `ORG_021_scottish_power_202605.pdf` |
| uk-missing-evidence | 60 | 17 | `ORG_018_national_rail_202608.pdf` |
| consultant-client-a | 48 | 48 | `ORG_030_edf_energy_202605.pdf` |
| consultant-client-b | 48 | 27 | `ORG_019_veolia_uk_202603.pdf` |
| direct-org-b-isolation | 132 | 15 | `ORG_019_e.on_energy_202602.pdf` |

The shipped selector examines only `corpus.candidates` candidates per glob — the manifest pins
`"candidates": 3` for all 11 scenarios (the code default is 4) — then keeps the highest score and breaks
ties by filename, so it never reaches the candidates the extractor can read. Example: for
`uk-electricity` the shipped choice is candidate #1, while candidate #2 extracts `26030.7 kWh`
correctly.

---

## 8. Document coverage (§8) — **declared only; no scenario reaches its workflow**

11 UK scenarios are declared (`uk-electricity`, `uk-gas`, `uk-diesel`, `uk-waste`, `uk-water`,
`uk-spend`, `uk-ambiguity`, `uk-missing-evidence`, `consultant-client-a`, `consultant-client-b`,
`direct-org-b-isolation`). Coverage of the required list is complete on paper, logistics is correctly
excluded, IE/SEAI and OCR are correctly absent.

However, per §8's rule ("Do not count a scenario merely because a fixture exists"), **no scenario
reaches a workflow outcome**: all 11 upload (201) then stop at the extraction gate. Verified job
outcomes after a full seed:

| Scenario | upload | job status | stage | reason (verbatim) |
|---|---|---|---|---|
| uk-electricity | 201 | manual_review | blocked | extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit |
| uk-gas | 201 | manual_review | blocked | mapping could not auto-resolve: line 1: no confident factor for 'Natural gas' litres (status=no_match, confidence=0.00) |
| uk-diesel | 201 | manual_review | blocked | mapping could not auto-resolve: line 1: no confident factor for 'Diesel' tonnes (status=no_match, confidence=0.00) |
| uk-waste | 201 | manual_review | blocked | extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit |
| uk-water | 201 | manual_review | blocked | extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit |
| uk-spend | 201 | manual_review | blocked | extraction completeness 0.00 below 0.50 threshold — unresolved: activity, quantity, unit |
| uk-ambiguity | 201 | manual_review | blocked | extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit |
| uk-missing-evidence | 201 | manual_review | blocked | extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit |
| consultant-client-a | 201 | manual_review | blocked | extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit |
| consultant-client-b | 201 | manual_review | blocked | extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit |
| direct-org-b-isolation | 201 | manual_review | blocked | extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit |

---

## 9. Ground-truth verification (§9) — mechanism **VERIFIED**, result **0/11**

`t3_scenarios.py verify` (executed by OHD) produced `t3_ground_truth_latest.json`:

```json
{"compared": 11, "activity_match": 2, "quantity_match": 0, "unit_match": 0,
 "snapshot_present": 0, "skipped": 0}
```

| Scenario | activity | quantity | unit | snapshot | evidence link | CarbonTally's first line |
|---|---|---|---|---|---|---|
| uk-electricity | ✗ | ✗ | ✗ | ✗ | ✓ | all null |
| uk-gas | ✓ (wrongly) | ✗ | ✗ | ✗ | ✓ | `Natural gas` (39.0 L vs 8398.67 kWh) |
| uk-diesel | ✓ (wrongly) | ✗ | ✗ | ✗ | ✓ | `Diesel` (22645.0 T vs 6953.75 L) |
| uk-waste | ✗ | ✗ | ✗ | ✗ | ✓ | all null |
| uk-water | ✗ | ✗ | ✗ | ✗ | ✓ | all null |
| uk-spend | ✗ | ✗ | ✗ | ✗ | ✓ | all null |
| uk-ambiguity | ✗ | ✗ | ✗ | ✗ | ✓ | all null |
| uk-missing-evidence | ✗ | ✗ | ✗ | ✗ | ✓ | all null |
| consultant-client-a | ✗ | ✗ | ✗ | ✗ | ✓ | all null |
| consultant-client-b | ✗ | ✗ | ✗ | ✗ | ✓ | all null |
| direct-org-b-isolation | ✗ | ✗ | ✗ | ✗ | ✓ | all null |

The comparison mechanism is real (it reads CarbonTally's own `document_processing_queue.extracted_data`
and `calculation_snapshots` provenance and reports per-field matches plus evidence linkage) —
**VERIFIED**. But with 0 quantity matches, 0 unit matches and 0 snapshots there is **nothing to
assert**, so the authorized "audit-grade E2E assertions" capability cannot be exercised — **FAIL**
(§20 requirement 8). The two activity "matches" are coincidental: they are the two confident-but-wrong
extractions (`uk-gas`, `uk-diesel`) whose activity label happens to match the expected one.

Independent per-field comparison by OHD (not via the tool) is in §7 — same conclusion.

---

## 10. Factor-matching verification (§10) — **NOT VERIFIED end-to-end; declared families partly unachievable**

No scenario reaches the mapping stage with a correct pair, so no factor can be verified end-to-end
through the T3 journey. To test the *declared* expectations, OHD probed the live matching path
(`POST /api/v2/factor-match`, real token) with each scenario's expected activity/unit:

| Scenario expectation | Probe (activity / unit) | Observed | Intended? |
|---|---|---|---|
| electricity family | `Electricity` / `kWh` | **ambiguous** (no factor) | **NO** — expectation not met |
| natural gas unqualified kWh ⇒ Net CV | `Natural gas` / `kWh` | **matched** `Fuels > Gaseous fuels > Natural gas (kg CO2e) [kWh (Net CV)]` = `0.2027`, id `b9d1ed06-…`, `DEFRA-2025`, `DEFRA-DESNZ`, GB, 2025, batch `f6c6e841` | YES (D-A Net-CV default preserved) |
| diesel family, not biodiesel | `Diesel` / `litres` | **ambiguous** (no biodiesel mis-selection, but no match either) | partly — no wrong family, no match |
| waste-disposal family, **not** waste oils | `Waste` / `tonnes` | **matched** `Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes]` = `3.5504`, id `9d499c4b-…` | **NO** — the family the manifest forbids |
| water unit compatibility | `Water` / `cubic metres` | **matched** `Water supply > Water supply > Water supply (kg CO2e) [cubic metres]` = `0.1913` | YES |
| spend/currency path | `Spend` / `GBP` and `General charges` / `GBP` | **no_match** (both) | **NO** — not demonstrable |

Every returned factor carried factor ID, factor set (`DEFRA-2025`), provider (`DEFRA-DESNZ`), country
(`GB`), unit, reporting year (2025) and import batch (`f6c6e841`) — the provenance surface is intact
**VERIFIED**.

**Blocking defect B-3:** at least four of the six approved core mappings (`electricity`, `waste`,
`diesel`, `spend`) do **not** produce the factor family the manifest declares — and where they do
resolve, `uk-waste` resolves to exactly the family the manifest says must not be chosen. The declared
expectations were evidently not validated against the real matching path. (These are probes with the
manifest's generic labels; the extraction never produced a real pair, so an end-to-end determination is
impossible until B-1 is fixed.)

---

## 11. Calculation / provenance (§11) — **FAIL (unreachable)**

| Requirement | Observed | Status |
|---|---|---|
| Calculation snapshot | **0 rows** in `calculation_snapshots` for every `t3imp…` job | VERIFIED (absent) |
| activity / quantity / quantity unit / factor id / factor set / import batch | not produced | NOT VERIFIED |
| source item / source page / source line item | `source_item_id` present on jobs (evidence linkage); no page/line provenance because no extraction completed | NOT VERIFIED |
| request id / content hash / CO2e | exist only on snapshots; none produced | NOT VERIFIED |
| derived from matched factor × extracted quantity | not demonstrable | NOT VERIFIED |
| no hard-coded demo results | no results at all; the seeder hard-codes nothing (checked) | VERIFIED |

---

## 12. Report lifecycle (§12) — API reachable, **T3 journey never reaches it**

| Check | Observed | Status |
|---|---|---|
| Persisted report creation | `POST /api/v3/reports` with `report_type=annual` ⇒ **201**, report `906ce1fc-…`, `status: completed`, persisted and listed by `GET /api/v3/reports` | VERIFIED |
| Legacy structured report | `POST /api/v2/generate-report` ⇒ **200**, 12-page structured payload (1,945 bytes) | VERIFIED |
| Provenance to calculations/evidence | the report was generated for Org A while **zero** calculations exist; it cannot trace to the T3 journey | VERIFIED (no provenance) |
| Artifact storage | `report-artifacts` bucket contains **0 objects**; `generate-report` returns `"storage_url": ""` | VERIFIED — **observation O-E** |
| Report retrieval / lifecycle state | the created report is retrievable and `completed`; the normal T3 demo flow never reaches this layer | VERIFIED |
| Scope discipline | no general Phase 9 audit performed (per instruction) | — |

---

## 13. Consultant-client parity / isolation (§13) — **VERIFIED**

| Check | Observed | Status |
|---|---|---|
| Consultant uploads for Client A and Client B | `201` for both, rows scoped to the client org | VERIFIED |
| Consultant lists Client A / Client B documents | `GET /api/v3/consultants/clients/{id}/documents` ⇒ 200 / 200, exactly 1 document each, correct file names | VERIFIED |
| Consultant cannot use the direct org surface | `GET /api/v3/documents?organization_id=<Client A>` ⇒ **403** | VERIFIED |
| Client A vs Client B isolation | `client_a_owner`: own org 200 (1 doc), Client B **403**; `client_b_owner`: own org 200, Client A **403**; cross-document fetches and signed URLs ⇒ **403** both directions | VERIFIED |
| Direct customer vs client isolation | `org_a_owner` → Client A document ⇒ **403**; `consultant_owner` → Client A document via org surface ⇒ **403** | VERIFIED |
| Direct-customer org isolation | Org A sees 8 own docs / Org B list ⇒ 403; Org B sees 2 own docs / Org A list ⇒ 403; cross-document fetch ⇒ 403 | VERIFIED |
| Stored objects scoped | object paths keyed by org UUID (4 distinct, correct per scenario) | VERIFIED |
| Consultant path uses the same capabilities | both journeys call the same `create_document_and_enqueue()` pipeline and produce identical job/evidence structures; **processing parity is moot because both stop at extraction** | VERIFIED (structure) / NOT VERIFIED (processing) |

---

## 14. Manual-processing governance (§14) — **deferred; governance intact**

| Check | Observed | Status |
|---|---|---|
| Grant rows in the lab | `manual_processing_grants` ⇒ **0 rows** (no grant created) | VERIFIED |
| Grant surface server-side and staff-only | router `/api/v3/admin/manual-processing`, guarded by `require_staff` + `require_internal_staff` + `ensure_staff_permission(can_manage_organizations)` | CODE-TRACED |
| Ordinary users cannot read or self-enable | `org_a_owner` and `client_a_owner` `GET`/`PUT` `/api/v3/admin/manual-processing/grants` ⇒ **403 `"Staff access required (active staff profile…)"`** | VERIFIED |
| Seeder cannot bypass the grant | the seeder never touches grants or the manual-processing admin plane | VERIFIED |
| Governance boundary respected | manual processing is **not** in the implemented critical path; documents that need it stay `manual_review`/`blocked` | VERIFIED |

Per the task instruction, absence of a manual-processing scenario is recorded as **deferred, not a
defect**. (Observation O-J: because the automatic path blocks every document, manual processing would be
the only way to complete a T3 document journey in this build — and it is deliberately not implemented.)

---

## 15. Idempotency / reset (§15) — idempotent **VERIFIED**, reset **FAIL**

| Test | Result | Status |
|---|---|---|
| First seed | 11/11 scenarios uploaded (201) and processed to a terminal state | VERIFIED |
| Second identical seed | **11/11 skipped** as `already seeded (idempotent)`, 0 new uploads, no duplicate scenario state | VERIFIED |
| Reset scope (dry-run) | exactly `organization_files: 11, manual_extraction_items: 11, document_processing_queue: 11, storage.objects: 11`; invariants `organizations 4 / members 8 / emission_factors 7049 / import_batches 2` preserved | VERIFIED |
| **Reset execution** | **FAILS**: `reset failed: ERROR: Direct deletion from storage tables is not allowed. Use the Storage API instead.` (trigger `storage.protect_objects_delete` → `storage.protect_delete()`), exit code **1**, and because the deletes are one `BEGIN…COMMIT` block **nothing is deleted** | VERIFIED (defect B-2) |
| Reset leaves identities/lab data intact | no damage: `auth_users 13`, `organizations 4`, `members 8`, `emission_factors 7049`, `import_batches 2`, `consultant_clients 2`; full 136-table census before/after showed **no differences** | VERIFIED |
| Reset does not touch unrelated/production data | statements scoped to `name/file_name LIKE 't3imp_%'` and `bucket_id='documents'`; fail-closed (no partial deletion) | VERIFIED |
| Repeat seed produces stable intended state | not re-testable through `reset` (B-2); repeat-seed skip behaviour verified instead | PARTIAL |
| Fail-closed behaviour | yes — the failure aborts the whole transaction, nothing partially removed | VERIFIED |

**Blocking defect B-2:** the shipped `reset` capability does not work at all. The trigger exists in both
the lab's cloned `storage` schema and the developer stack's `storage` schema, so this is structural, not
lab-specific. It fails safely (no identity or factor loss), but the required lab-scoped reset is
non-functional.

---

## 16. Production safety (§16) — **VERIFIED (safety comes from hard-coding, not from a guard)**

| Check | Observed | Status |
|---|---|---|
| Exact Demo-Lab database/environment guard | `assert_lab_database()` compares `SELECT current_database()` to `carbontally_demo_local` and raises `GuardError` (CLI exit 3) | CODE-TRACED |
| Can the tooling be pointed elsewhere? | **No configurable target exists**: `lab.psql()` always connects `-d LAB_DB` (`carbontally_demo_local`); `t3_scenarios.py`/`storage.py` read **no** `--db-url`/`DATABASE_URL`/env for the target | VERIFIED |
| Refusal of an incorrect environment | **not demonstrable** — the guard reads through the same hard-coded helper, so it can only ever observe the lab name (**observation O-H**: self-fulfilling guard) | NOT VERIFIED |
| Hostile-environment resistance | with `DATABASE_URL`, `SUPABASE_DB_URL`, `PGDATABASE`, `DEMO_LAB_DATABASE_URL` all aimed at the reference database, the tool still reported `carbontally_demo_local` and the reference DB stayed unchanged (`7049 factors / 0 batches`) | VERIFIED |
| No production DSN embedded | no remote URLs anywhere in the T3 tooling except the internal container health probe `http://carbontally_demo_lab_storage:5000/version` | VERIFIED |
| No destructive production fallback | the only destructive statements are scoped by the `t3imp_` prefix in the lab DB | VERIFIED |
| No automatic production-schema migration | `stack.py` provisions only the lab DB; `storage.py` reads the stack schema with `pg_dump --schema-only` (read-only source) and pipes definitions into the lab DB (`psql_stdin(..., db=LAB_DB)`) | VERIFIED |
| Explicit environment configuration | lab Docker network/DB name/ports are constants in `lab.py`; lab `.env` generated into the state dir | VERIFIED |

---

## 17. Out-of-scope confirmation (§17) — **VERIFIED (no silent expansion)**

| Prohibited expansion | Evidence | Status |
|---|---|---|
| IE/SEAI synthetic documents | 0 IE/SEAI matches in `t3_manifest.json`; all 11 scenarios UK; no SEAI corpus documents | VERIFIED |
| External-generator modification | `/tmp/extgen` clean at the pinned commit; no generator file in the diff | VERIFIED |
| Runtime dependency on the generator | see §4 | VERIFIED |
| OCR / Render redesign | no `backend/`, OCR or worker change in the diff; corpus is text-native only; OCR remains deferred | VERIFIED |
| Production deployment | no deployment artefact, no remote endpoint; everything on `127.0.0.1` | VERIFIED |
| Real customer data | all data generator-produced synthetic; no production dataset read or copied | VERIFIED |
| Broad Phase 9 work | the diff adds only demo-lab tooling; no report-engine or disclosure changes | VERIFIED |
| Unrelated RLS/security remediation | no policy/migration change; the D32 policies created are the four approved ones, in the lab DB only | VERIFIED |
| New calculation / factor-matching engine | none; matching and calculation are the existing engines (verified by probing the unchanged API) | VERIFIED |

---

## 18. Negative / failure-path testing (§18) — **VERIFIED (honest failures, no fabrication)**

| Test | Observed | Status |
|---|---|---|
| Invalid environment for the seeder | no configurable target; hostile env cannot redirect it (§16) | VERIFIED |
| Unauthorised organization access (upload) | `org_a_owner` uploading to Org B ⇒ **403 `"Organization access denied"`** | VERIFIED |
| Read-only role | `org_a_viewer` upload ⇒ **403 `"Viewers are read-only and cannot upload documents"`** (denied before any write) | VERIFIED |
| Unauthorised document read | cross-tenant document + signed URL ⇒ **403** in all tested directions | VERIFIED |
| Missing/invalid document | upload of a plain-text file mislabelled `application/pdf` ⇒ 201 then job `manual_review`/`blocked`, `extracted_data` **null**, reason **`extraction no_text: no usable text extracted (blank page, or image too low quality)`** — **no fabricated activity/quantity/unit** | VERIFIED |
| Missing document at enqueue | `POST /api/v3/processing/documents/<unknown>/enqueue` ⇒ **404 `"document not found"`** | VERIFIED |
| Non-existent consultant client | consultant upload to an unknown client ⇒ **404 `"client not found"`** | VERIFIED |
| Deliberate ambiguity case | `uk-ambiguity` blocks with an extraction reason (no invented values); the matching layer returns `ambiguous` rather than inventing a factor for `Electricity`/`kWh` and `Diesel`/`litres` | VERIFIED (preserved) |
| Unsupported/invalid factor mapping | `uk-gas` (`Natural gas` + `litres`) ⇒ `no_match`; `uk-diesel` (`Diesel` + `tonnes`) ⇒ `no_match`; both blocked with truthful reasons — **no factor fabricated** | VERIFIED |
| Incomplete-evidence case | `uk-missing-evidence` blocks at the completeness gate; no fabricated quantity/unit | VERIFIED |

Failure handling is a genuine strength of this build: the pipeline degrades to an honest
`manual_review`/`blocked` state and never invents activity, quantity, unit, factor or evidence.

---

## 19. Findings and observations

### Blocking defects

| ID | Defect | Impact | Evidence |
|---|---|---|---|
| **B-1** | **Corpus selection is not parseable.** `_text_quality()` does not test for a separable quantity+unit pair (despite its docstring); the shipped corpus contains 11/11 documents that CarbonTally's deterministic extractor mis-extracts (9 block at completeness 0.33/0.00, 2 produce confidently wrong quantity+unit). Parseable alternatives existed for all 11 scenarios within the same globs. | **No scenario reaches mapping → calculation → report**, so the authorized "real document/evidence/report flows" and "audit-grade E2E assertions" cannot be demonstrated. Directly causes §6/§8/§9/§10/§11/§12 to fail or be unverifiable. | §7 tables; `extract_document` run over the corpus and over all candidates |
| **B-2** | **`reset` is non-functional.** Direct `DELETE FROM storage.objects` is blocked by trigger `protect_objects_delete` (`storage.protect_delete()`); the transaction aborts, exit 1, **nothing is deleted**. | The shipped lab-scoped reset cannot clean T3 artefacts; re-seed-after-reset cannot be exercised. Fail-closed (no data loss). | `t3_scenarios.py reset` ⇒ `reset failed: ERROR: Direct deletion from storage tables is not allowed…`; 136-table census diff empty |
| **B-3** | **Declared factor mappings are not achievable.** With the manifest's expected pairs: `Electricity`/`kWh` ⇒ ambiguous, `Diesel`/`litres` ⇒ ambiguous, `Spend`/`GBP` ⇒ no_match, `Waste`/`tonnes` ⇒ the **forbidden** `Waste oils` family. | Even with extraction fixed, at least 4 of 6 core workflows would not produce the declared factor family; the manifest's "expected" contract is not validated against the real engine. | §10 probe table |

### Non-blocking observations

| ID | Observation | Detail |
|---|---|---|
| O-A | Lab storage API rejects user JWTs (ES256) | Lab container has `PGRST_JWT_SECRET` only; the stack container also has `JWT_JWKS` with the GoTrue ES256 public key. User-token `/storage/v1` calls fail (`"alg" … not allowed`); the app's service-key + signed-URL path works (verified: 200, real PDF bytes). |
| O-B | Silent scoring degradation | Without `pdfplumber` in the interpreter (the README documents `python3 …`, which lacks it) every candidate scores 0 with `quality.error` recorded, all 11 selections change to the first candidate, and `sync-corpus` still exits 0 with no warning. |
| O-C | `uk-water` selection not reproducible | With scoring enabled the selector now chooses `ORG_021_thames_water_202607.pdf` while the shipped corpus/DB uses `…_202605.pdf`; 10/11 scenarios reproduce exactly. |
| O-D | Corpus provenance overwritten by verification (disclosed side-effect) | OHD's re-syncs rewrote `<state>/corpus/t3-uk-curated-v1/corpus_provenance.json` (the shipped file is not in git). OHD removed the 8 corpus files its degraded run created and left the corpus self-consistent (provenance references exist for all 11 scenarios); the shipped `source`/`candidates_considered` record is no longer available, which slightly limits attribution of O-C. Pre-existing unreferenced files (e.g. `…certas_energy_202602.*`) were left untouched. |
| O-E | `report-artifacts` bucket unused | Bucket provisioned and private but contains 0 objects; `POST /api/v2/generate-report` returns `"storage_url": ""`. No T3 flow verified to write report artefacts. |
| O-F | Misleading seed provenance | Manifest/`GENERATOR_SEED = 42` vs per-document `generation_seed` values (2699260036, …). The corpus is pinned by *files at a commit*, not by a reproducible seed. |
| O-G | Enqueue API friction | `POST /api/v3/processing/documents/{id}/enqueue` requires a body and returns 422 for an already-auto-enqueued document; recorded by the implementation and reproduced by OHD. |
| O-H | Guard is self-fulfilling | `assert_lab_database()` reads `current_database()` through the same helper that hard-codes `carbontally_demo_local`, so it can never detect a wrong environment. Real safety comes from the hard-coded name (verified resistant to hostile env vars); the guard adds no detection capability. |
| O-I | Verification artefacts left in the lab | `ohd079-invalid-probe.txt` (1 `organization_files` + 1 item + 1 job + 1 `storage.objects` row), 1 persisted report (`906ce1fc-…`), 1 generated report payload. The `documents` bucket now holds 12 objects (11 T3 + 1 probe). OHD could not remove them via `reset` because of B-2. |
| O-J | Blocked documents make manual processing the only completion path | Every document needs manual review, while manual processing is deliberately deferred — so no end-to-end document journey exists in this build even in principle. |

### CLAIMED-only items (not independently reproducible)

* "all 75 release migrations now apply cleanly (`migrations_with_errors: []`)": OHD verified the storage
  schema/policies/buckets exist and the app works, but did not re-run `stack.py`.
* "10 tables / 17 functions" in the cloned `storage` schema (count not re-derived).
* The implementation report's self-declaration that guard/idempotency/reset were "code-traced" is
  accurate; OHD executed all three and found reset broken (B-2).

---

## 20. Final verdict

# FAIL

**Rule applied** (§20): "FAIL — One or more authorized requirements are not working or cannot be
independently established." The verdict is **not** "PASS WITH NON-BLOCKING OBSERVATIONS" because the
failure is inside the authorized scope, not beside it, and it is a runtime failure rather than something
merely code-traced.

**What works (independently reproduced):**

* The Demo-Lab **storage substrate** serves real, private, org-scoped document storage: uploads produce
  real `storage.objects` rows, the app's signed-URL download returns real PDF bytes (200), tenant
  isolation is enforced (403s in every tested direction).
* The **ingestion driver is genuinely API-based** — 11 documents uploaded through
  `POST /api/v3/uploads` and `POST /api/v3/consultants/clients/{id}/documents`, with real
  `organization_files`, D23 batch/item, `storage.objects` and `document_processing_queue` rows, and
  **no direct DB insertion of documents/evidence/calculations/reports**.
* **Consultant-client and direct-customer paths and isolation** are correct and demonstrated.
* **External-generator separation** is clean and correctly pinned.
* **Failure handling is honest**: blocked/manual-review states with truthful reasons and **no fabricated
  activity, quantity, unit, factor, calculation or evidence** — including for an invalid document.
* **Idempotent re-seed**, no production targeting, no scope expansion, IE/OCR still deferred,
  manual-processing governance intact (0 grants; ordinary users 403).

**Why the authorized scope nevertheless fails:**

1. **No document journey completes.** All 11 scenarios stop at extraction; there are **0 calculation
   snapshots**, so no evidence→factor→calculation→report chain exists and no audit-grade E2E assertion
   can be made (B-1).
2. **The corpus is the cause, and a usable corpus existed.** The selector picked 11/11 documents the
   extractor cannot read, while every scenario had correct alternatives within its own candidate glob
   (B-1).
3. **The declared expected mappings are partly wrong** against the real engine: electricity and diesel
   are ambiguous, spend does not resolve, and waste resolves to the family the manifest forbids (B-3).
4. **The shipped `reset` does not work at all** (B-2).

**Minimum remediation for a future bounded task** (reporting only — not performed by OHD):
(a) make the corpus scorer *prove* parseability by running the deterministic extractor (or an equivalent
quantity+unit pair test) across the candidate pool rather than the first 3, and pin the selected
document SHAs; (b) fail loudly when the scoring dependency is missing (O-B); (c) replace the corpus
delete in `reset` with the storage API path or an equivalent non-blocked mechanism and verify reset
end-to-end; (d) re-validate every declared `expected.factor_family` against
`POST /api/v2/factor-match` and record corrected expectations, or accept ambiguity/clarification as the
documented outcome.

No implementation defect was fixed, no implementation code was modified, and no PO closure is claimed.
PO closure remains the Product Owner's decision after reviewing this verification.

---

## 21. Reproduction commands (abridged)

```bash
# identity / scope
cd /home/shomonrobie/ct_93d5cdd
git rev-parse HEAD; git rev-parse 8c54f8e; git status --porcelain --untracked-files=all
git ls-remote github refs/heads/p8-release-reconciled
git diff --name-status 8c54f8e ad46599 ; git diff --stat 8c54f8e ad46599 -- src/ backend/ supabase/

# storage
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:54430/storage/v1/version
psql … -c "SELECT id,name,public FROM storage.buckets"            # both private
psql … -c "SELECT policyname,cmd,roles FROM pg_policies WHERE schemaname='storage'"
# app path: GET /api/v3/documents/{id}/signed-url -> 200, then fetch the URL -> 200 %PDF-

# corpus / tooling
python3 tools/demo_lab/t3_scenarios.py status
python3 tools/demo_lab/t3_scenarios.py sync-corpus --source /tmp/extgen --dry-run
./backend/.venv/bin/python tools/demo_lab/t3_scenarios.py sync-corpus --source /tmp/extgen
python3 tools/demo_lab/t3_scenarios.py seed --wait 90
python3 tools/demo_lab/t3_scenarios.py verify
python3 tools/demo_lab/t3_scenarios.py reset            # exits 1 (B-2)

# extractor proof (11/11 mis-extracted; alternatives exist in the same globs)
cd backend && ../backend/.venv/bin/python -c \
 "from services.automatic_extraction import extract_document, completeness_score; ..."

# factor families
POST /api/v2/factor-match {"activity":"Electricity","country":"GB","reporting_year":2025,"unit":"kWh",…}
```

Verification environment: lab state at `~/ct_local_env/demo_lab`, corpus at
`…/corpus/t3-uk-curated-v1`, pinned generator checkout at `/tmp/extgen`.
