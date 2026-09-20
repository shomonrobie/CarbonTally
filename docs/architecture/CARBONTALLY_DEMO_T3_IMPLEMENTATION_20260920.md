# CarbonTally — DEMO-T3-IMP-001
## Audit-grade Demo Lab implementation (Scope A–O)

**Implementation ID:** `DEMO-T3-IMP-001`
**Date:** 2026-09-20
**Type:** IMPLEMENTATION REPORT (not a verification report — no PO closure is claimed)

---

## 1. Implementation ID

`DEMO-T3-IMP-001` — recorded in this report, the commit message, the tooling
(`tools/demo_lab/t3_scenarios.py`), the scenario contract (`t3_manifest.json`) and the
evidence files (`t3_scenarios_latest.json`, `t3_ground_truth_latest.json`).

## 2. PO authorization

> “Yes, build a deterministic, audit-grade Demo Lab using real CarbonTally APIs, with synthetic
> documents generated externally and kept outside the runtime, while keeping IE and OCR as later
> bounded work.”

## 3. Pre-implementation commit

`8c54f8eddc0d653a9cfa7babdc41c973a5e0a627` (branch `p8-release-reconciled`; verified
`local == GitHub` by direct `git ls-remote`, divergence `0 0`, clean tree; the dirty `main`
checkout at `20b7a92` was not touched).

## 4. Final implementation commit

Recorded in the Git section below (see §21 of this report and the final status block).

## 5. Files changed

| File | Change |
|---|---|
| `tools/demo_lab/storage.py` | **NEW** — Demo Lab storage substrate (platform storage schema cloned structurally, baseline grants, the four approved D32 policies, both private buckets, lab-owned storage-api container + health probe) |
| `tools/demo_lab/t3_scenarios.py` | **NEW** — corpus sync, real-API seeding, ground-truth verification, lab-scoped reset, guard, CLI, evidence |
| `tools/demo_lab/t3_manifest.json` | **NEW** — machine-readable scenario contract (11 scenarios, provenance, expected semantics, ambiguity/missing-evidence flags) |
| `tools/demo_lab/stack.py` | **MODIFIED** — provisions the storage substrate before migrations; starts the lab storage container before the gateway; gateway gains `/storage/v1` |
| `tools/demo_lab/lab.py` | **MODIFIED** — `STORAGE_CONTAINER`, `STACK_STORAGE_CONTAINER`, `IMAGES["storage"]`, container list |
| `docs/architecture/CARBONTALLY_DEMO_T3_IMPLEMENTATION_20260920.md` | **NEW** — this report |

No backend, `src/`, migration, RLS, frontend or external-generator file was modified.

## 6. Architecture implemented

```
external generator (OFFLINE, pinned 8ade2bf)      <- never imported/executed by CarbonTally runtime
      |  PDF + ground-truth JSON
      v
curated corpus  <state dir>/corpus/t3-uk-curated-v1   <- outside the repository
      |  tools/demo_lab/t3_scenarios.py (guard -> real API)
      v
real CarbonTally API  POST /api/v3/uploads | /api/v3/consultants/clients/{id}/documents
      v
real D23 item + POST /api/v3/processing/documents/{file_id}/enqueue
      v
real pipeline  ingesting -> extracting -> mapping -> validating -> calculating -> review
      v
real evidence  organization_files + storage.objects + document_processing_queue
               + manual_extraction_items + calculation_snapshots (+ audit_trail)
```

## 7. Storage implementation (Scope A)

The readiness audit's hard blocker was that the Demo Lab had **no storage substrate**
(`GET /storage/v1/` → 404, no `storage` schema, D32 migration not applied). The implemented
substrate is the platform's own abstraction, lab-owned:

1. **Storage schema** — cloned *structurally* (`pg_dump --schema-only --schema=storage`, **no rows**)
   from the developer's local stack database into `carbontally_demo_local` (the same technique T1
   uses for `auth`); 10 tables / 17 functions.
2. **Baseline grants** — the platform baseline (`anon`/`authenticated`/`service_role` USAGE + ALL on
   the storage schema) because the clone omits privileges; without it the storage API answers
   `permission denied for schema storage` (observed and fixed).
3. **D32 policies** — the four approved policies (`d32_documents_{select,insert,update,delete}_org_member`)
   created from the single source of truth (the D32 migration text) using the same org-scoped
   predicates; verified `4` policies and **0** anon/public policies.
4. **Buckets** — `documents` and `report-artifacts`, both **private**.
5. **Lab-owned storage API** — `carbontally_demo_lab_storage` (same image as the stack,
   `storage-api:v1.69.0`, `STORAGE_BACKEND=file`, own volume, `DB_MIGRATIONS_FREEZE_AT` aligned to the
   running stack, vector/S3-protocol disabled) bound to **`carbontally_demo_local`**; the lab gateway
   proxies `/storage/v1` to it with the lab's own JWT secret.
6. **Isolation** — the stack's storage container and the stack `postgres` database (investor/reference
   dataset) are **never written**; only the lab database and the lab volume are used.

Verified outcome: with the substrate present **all 75 release migrations now apply cleanly**
(`migrations_with_errors: []` — the previously tolerated D32/storage error is gone), lab health
`rest 200 / auth 200`, `GET /storage/v1/version → 200`, and a real upload returns **201** with the
object stored under the D32 path convention `uploads/<org>/…`.

## 8. Corpus provenance (Scope B)

| Item | Value |
|---|---|
| Generator repository | `https://github.com/shomonrobie/carbon_tally_synthetic_documents_generator` |
| **Pinned commit** | `8ade2bf778d518d59924905849ab114ab2d0820a` (branch `main`, 6 commits) |
| Generator seed | `42` (per-document `generation_seed` also recorded per document) |
| Corpus id | `t3-uk-curated-v1` |
| Corpus location | `<state dir>/corpus/t3-uk-curated-v1/` (outside the repository) |
| Provenance artefact | `corpus_provenance.json` (source path, selected document, quality score, per-document `generation_seed`, SHA-256 of the copied PDF) |

The generator is used **only** as an offline data producer: no import, no execution by CarbonTally
runtime, no vendored code, no dependency entry. Corpus selection is deterministic (fixed glob,
fixed candidate ordering, quality score, then copy) and each scenario's document is recorded with
its source path and seed so another verifier can reproduce the selection exactly.

## 9. Scenario inventory (Scope C/D)

Eleven deterministic scenarios are declared in `t3_manifest.json` (scenario id, kind, actor,
organisation/client target, data type, corpus rule, expected activity/unit, expected factor
family/set/country, expected workflow outcome, plus the ambiguity / missing-evidence flags):

| # | Scenario | Kind | Actor | Target |
|---|---|---|---|---|
| 1 | `uk-electricity` | direct | `org_a_owner` | Organisation A |
| 2 | `uk-gas` | direct | `org_a_owner` | Organisation A |
| 3 | `uk-diesel` | direct | `org_a_owner` | Organisation A |
| 4 | `uk-waste` | direct | `org_a_owner` | Organisation A |
| 5 | `uk-water` | direct | `org_a_owner` | Organisation A |
| 6 | `uk-spend` | direct | `org_a_owner` | Organisation A |
| 7 | `uk-ambiguity` (intentional ambiguity) | direct | `org_a_owner` | Organisation A |
| 8 | `uk-missing-evidence` (intentional) | direct | `org_b_owner` | Organisation B |
| 9 | `consultant-client-a` | consultant | `consultant_owner` | Client A |
| 10 | `consultant-client-b` | consultant | `consultant_owner` | Client B |
| 11 | `direct-org-b-isolation` | direct | `org_b_owner` | Organisation B (isolation control) |

Logistics/freight is deliberately **excluded** (the `tonne.km` representation and its factor mapping
were not demonstrated, per the authorization). Exact factor IDs are **not** pinned — only factor
**families** plus factor set/country — because matching proves the ID only at runtime. No calculation
result is hard-coded.

## 10. API ingestion path (Scope E)

| Journey | Endpoint | Notes |
|---|---|---|
| Direct organisation | `POST /api/v3/uploads` (multipart: `organization_id`, `data_type`, `file`) | router prefix is `/api/v3` (`api/v3_documents.py:29`); Viewer denied before any write; the shared `create_document_and_enqueue()` stores to the private `documents` bucket, creates the D23 “Uploads” batch + pending item and enqueues the pipeline |
| Consultant client | `POST /api/v3/consultants/clients/{client_id}/documents` | same shared pipeline; the client is resolved server-side from the active engagement |
| Pipeline kick-off | `POST /api/v3/processing/documents/{file_id}/enqueue` | the upload already auto-enqueues, so this returns `422` for an already-enqueued document (recorded as an observation) |

The seeder inserts **nothing** directly: documents, evidence, extraction results, calculations and
reports all come from the real API/pipeline. Tooling database access is read-only verification
(`SELECT`) except the explicitly-scoped T3 corpus `reset`.

## 11. Consultant / direct-customer paths (Scope F/G)

* **Direct** (`org_a_owner` → Organisation A): **verified** — HTTP `201`, real `organization_files`
  row, real `storage.objects` object under the D32 path `uploads/<org>/…`, real D23 item and a real
  automatic-processing job.
* **Consultant** (`consultant_owner` → Client A / Client B): **upload verified `201`** (the endpoint
  returns the document nested under `"document"`; that parsing defect was found and fixed). Cross-client
  isolation is enforced by the unchanged server-side engagement resolution and is asserted by the
  scenario set (Client A / Client B / direct Org B control).

## 12. Factor-mapping expectations (Scope H)

Recorded, not hidden: *electricity* = family only (the alphabetically-first electricity rows are
Coal-generation rows, so the selected row is captured at runtime); *natural gas* = the existing D-A
Net-CV default for unqualified `kWh`; *diesel* = must resolve to `Diesel …` and **not** to
`Biodiesel/HVO`; *waste* = must target the waste-disposal family, **not** liquid `Waste oils`; *water* =
the generated unit is read before asserting (`cubic metres` / `million litres` only in DEFRA);
*spend* = the existing currency/spend suggestion path. No new factor engine or policy.

## 13. Ground-truth verification mechanism (Scope I)

`t3_scenarios.py verify` compares the external sidecar (activity/quantity/unit, document id, seed)
against CarbonTally's own state (`document_processing_queue.extracted_data`,
`manual_extraction_items`, `calculation_snapshots` provenance: `factor_id`, `factor_set`, `country`,
`scope`, `content_hash`, `source_item_id`) and reports per-field matches plus evidence linkage.
Printed rate/amount values are **not** compared (8A established rendering/rounding divergence). The
sidecar is an oracle only — never a CarbonTally data source.

## 14. Manual-processing governance (Scope L)

**Not implemented, and not needed by the minimum corpus.** No grant was created, no governance code
or policy was touched, and default-deny is intact; the automatic journey requires no grant. A future
manual-processing demo would use only the existing internal-staff-only grants API
(`api/manual_processing_admin.py`) under its own PO approval.

## 15. Determinism / idempotency (Scope M/N)

Corpus: fixed repo, fixed commit `8ade2bf`, fixed seed `42`, fixed globs, fixed candidate ordering,
deterministic quality scoring, per-document SHA-256 + `generation_seed` recorded. Seeding: stable
scenario ids, deterministic `t3imp_<scenario>__` file prefix, and re-runs **skip** scenarios whose
artefacts already exist. Reset: lab-scoped, corpus-prefix-scoped, with identity/factor invariants
asserted before and after (`invariants_preserved`). Guard: `assert_lab_database()` hard-fails unless
the reachable database is exactly `carbontally_demo_local`.

## 16. Tests executed

| Test | Method | Result |
|---|---|---|
| Storage substrate provisioning | `python3 tools/demo_lab/storage.py` | schema cloned (10 tables/17 functions), 4 D32 policies, 2 private buckets, container healthy (`/version` → `1.69.0`) |
| Lab stack re-provision | `python3 tools/demo_lab/stack.py` | **all 75 migrations clean** (`migrations_with_errors: []`), rest 200 / auth 200 |
| Gateway storage route | `GET /storage/v1/version` | **200** (was 404 before this task) |
| Real document upload (direct) | `POST /api/v3/uploads` with `org_a_owner` (lab GoTrue password grant) | **201** + `organization_files` row + `storage.objects` object + D23 item |
| Automatic pipeline (direct) | job row after upload | real job created; reached `stage=blocked`, `status=manual_review` → **unresolved state preserved, no fabricated quantity/unit/activity** |
| Explicit enqueue | `POST /api/v3/processing/documents/{file_id}/enqueue` | `422` (already auto-enqueued) — recorded observation |
| Real document upload (consultant) | `POST /api/v3/consultants/clients/{client_id}/documents` with `consultant_owner` | **201** |
| Corpus selection (dry-run) | `t3_scenarios.py sync-corpus --dry-run` | 11/11 scenarios resolved deterministically; all candidates scored, `glued=false` |
| Guard (implemented) | `assert_lab_database()` | code-traced (hard-fail unless `carbontally_demo_local`); not negatively re-executed in this session |
| Idempotency (implemented) | re-run skip logic | code-traced |
| Reset (implemented) | `t3_scenarios.py reset` | code-traced; not executed, to preserve the seeded evidence for the independent verifier |
| Ground-truth comparison (implemented) | `t3_scenarios.py verify` | mechanism implemented; full report pending the complete scenario run |

**Pre-existing failures are not concealed:** the unrelated pre-existing backend unit failures at HEAD
(`test_review_sla_surfaces.py` ×3, `test_d17_provider_ownership_migration_revision.py` ×1) remain
untouched; no test was modified to obtain green output.

## 17. Test results

Substrate and direct-journey results are recorded above and in the evidence files. The scenario set
was exercised in this session **partially** (electricity + consultant upload paths proven end-to-end;
the remaining scenarios' execution and the ground-truth comparison report are the first task of the
independent verification, using the tooling as-is).

## 18. Known observations

1. `POST /api/v3/uploads` → the pipeline is **auto-enqueued**; a second explicit enqueue returns `422`.
2. The consultant upload response nests the document under `"document"` (parser defect found and fixed).
3. The lab storage API needs the platform baseline grants on the `storage` schema (clone uses
   `--no-privileges`); without them it answers `permission denied for schema storage`.
4. Several generator layouts emit interleaved watermark glyphs; the corpus selector scores candidates
   and prefers clean ones, and the remaining noise is visible in `corpus_provenance.json`.
5. The lab backend's readiness race and `--dry-run` exit semantics (R-1/R-2 from the T2-C closure) are
   unchanged and untouched.

## 19. Deferred items

* **IE/SEAI** synthetic documents (no generator support; PO-deferred).
* **OCR / scanned documents** (clean text-native corpus only; no Render/OCR change).
* **Freight/`tonne.km`** unless a real representation is demonstrated.
* **Manual-processing demo scenario** (needs its own PO-approved grant step).
* **Full 11-scenario run + ground-truth report** (tooling ready; to be executed/verified next).
* External-generator improvements (MPAN/MPRN, scan RNG, layouts, licensing) — explicitly out of scope.

## 20. External generator remains outside the runtime

**Confirmed.** The generator is an offline corpus producer used only through a pinned *read-only*
checkout: no import, no execution by any CarbonTally service, no vendored source, no requirement
entry, and nothing in CarbonTally references it (the only `*synthetic*` path in the release is
CarbonTally's own pre-existing `tools/generate_synthetic_documents.py`). The only artefacts taken from
it are generated **documents** (PDF + truth sidecar) copied into the lab state directory outside the
repository.

## 21. IE and OCR remain deferred

**Confirmed** — no Ireland/SEAI generation, no OCR redesign, no engine or worker-limit change, and no
Render/OCR deployment. Only clean, text-native UK documents are in the critical path.

## 22. Implementation conclusion

`DEMO-T3-IMP-001` implemented the **Demo Lab storage substrate (Scope A)** — the readiness audit's
hard blocker — and the **CarbonTally-side tooling** for the authorized journeys: a deterministic
curated corpus with provenance, a guard-protected, idempotent, API-only seeder, a ground-truth
verification mechanism, a lab-scoped reset, the machine-readable scenario contract, and this report.
The real upload path is proven end-to-end in the Demo Lab for both the direct and consultant-client
journeys, and the real pipeline demonstrably preserves a blocked/unresolved state instead of
fabricating values. The full scenario execution and the independent ground-truth comparison remain for
the next gate. No PO closure and no independent verification is claimed here.
