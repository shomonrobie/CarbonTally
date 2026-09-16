# CT-P8-B2-INDEPENDENT-VERIFICATION-20260913-025

**Phase 8 — B2 Evidence / Line-Item Addressability — INDEPENDENT VERIFICATION**

---

## 1. Task identity

| Item | Value |
|---|---|
| Task ID | `CT-P8-B2-INDEPENDENT-VERIFICATION-20260913-025` |
| Subject of verification | `CT-P8-B2-IMPLEMENTATION-20260913-024` (implementation only) |
| Date / time | 2026-09-13, start `08:09:11Z`, finish `~08:40Z` (run logs carry UTC) |
| Verification type | **Independent verification** — no implementation, no fixes, no commits, no deployment |
| Repository | `/home/shomonrobie/carbon_tally` (shared worktree; a parallel OHD/GA4 session was active) |

## 2. Verification authority and boundary

Authoritative for B2 (read and reconciled in full):

1. `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md`
2. `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md` (B2-D1…B2-D12 CLOSED)
3. `docs/cline/reports/CT-P8-B2-PO-IMPLEMENTATION-AUTHORISATION-20260913-019.md` (`MAY PROCEED`)
4. `docs/cline/reports/CT-P8-B2-AUTHORISATION-CONTRACT-CORRECTION-20260913-021.md` (corrected §20.3)
5. `docs/cline/reports/CT-P8-B2-IMPLEMENTATION-20260913-024.md` (implementation report, treated as a *claim*)
6. `docs/cline/reports/CT-P8-CURRENT-STATE-RECOVERY-20260913-023.md`
7. B1 contract + B1 PO ratification (B1→B2 dependency boundary)

Authority limits observed: **nothing was implemented, fixed, amended, committed, pushed or
deployed.** The only writes were (a) this report, (b) one **disposable verification clone**
(`ct_b2_iv_20260913`, created from a `pg_dump --schema-only` of the production-shaped local
database and dropped/recreated as needed). No production, investor-demo, dev or persistent
test database was modified; the implementation's own clone was **not** relied upon.

## 3. Start-state worktree evidence

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `37b19d13723b0b1eabceeade86ce1615a98ab400` — `feat(admin): admin-configurable Google Analytics 4 (Analytics & Integrations)` |
| Staged | **0 files** |
| Tracked modifications | 218 |
| Untracked entries | 88 (821 with `--untracked-files=all`) |
| B2 artefacts committed? | **No** — `git show --stat HEAD \| grep -icE 'b2\|evidence_line_items'` → `0`; the B2 files appear as ` M`/`??` only |
| GA4/OHD commit unrelated to B2? | **Yes** — its 14 changed files are `frontend/src/…` (GA4/consent/SettingsTab) and contain no B2 path |

**Movement since the implementation report:** HEAD advanced `19e4f01c…` → `37b19d13…`
because the **parallel OHD session committed its own GA4 work**; the implementation report
already records and correctly attributes this (its §B.1), and confirmed no B2 artefact was
captured. Independent re-confirmation here: the B2 artefacts are still uncommitted/unstaged,
and the parallel session's newer untracked files (`.openhands/`, `admin/src/analytics.js`,
`posthog-self-driving-report.md`) are unrelated to B2. **No unexpected change to B2 work was
found**, so verification proceeded.

Verification end state: HEAD unchanged (`37b19d13…`), `staged=0`, tracked modifications 218;
untracked 89 (the extra entry belongs to the parallel session, not to this task).

## 4. Contract / ratification reconciliation

| Source | Status | Note |
|---|---|---|
| B2 contract §7.1 DDL | **matched** by the migration, byte-for-byte on every column/constraint | see §6 |
| B2 contract §8.1/§9.1 (two additive columns + guarded FKs + indexes) | **matched** | `ON DELETE SET NULL`, both FKs named exactly as specified |
| B2-D1 (`source_item_id` NOT NULL + `ON DELETE RESTRICT`, CASCADE prohibited) | **matched** | `confdeltype='r'`; the only CASCADE is `organization_id` (§7.1) |
| B2-D2 (detect + report + never rewrite) | **matched** | `ON CONFLICT DO NOTHING`; divergence detected/reported; no `DO UPDATE` |
| B2-D3 (PE read mirrors the item policy) | **matched exactly** | policy `qual` is the item policy's expression with `id`→`source_item_id` (see §10) |
| B2-D4 / F-B2-7 (`source_page` never from `page_count`) | **matched** | `source_page` NULL in all runtime probes; `page_count` never read |
| B2-D5 (audit granularity) | **matched** | 1 forward event/document, 1 summary event/run, 1 divergence event/item/run |
| B2-D6 (single data-layer choke point) | **matched** | hook in `ManualExtractionRepository` only |
| B2-D7 (open `extraction_method`) | **matched** | no CHECK on the column; values `iv-forward-csv`, `iv_queue_stamp`, `unknown` observed |
| B2-D8 (`row_reference` NULL for Class-1) | **matched** | NULL in every materialised row |
| B2-D9 (no endpoint/UI) | **matched** | no new route, no frontend change |
| B2-D11 (no retention/deletion mechanism) | **matched** | 0 triggers, no soft-delete column, no purge path, `delete()` raises |
| B2-D12 (no retro-linking) | **matched** | historical snapshot byte-identical and link NULL after a backfill |
| §18.1 (two migrations, additive, `BEGIN…COMMIT`, idempotent) | **matched** | apply ×2 `rc=0`, zero drift |
| §20.6 (amend-never-delete for exactly two B1 tests) | **matched** | B3/B4 guards intact; no third B1 test weakened (see §9) |
| §20.2 (20 runtime acceptance tests) | **matched** | 21/21 pass on the verification clone |
| §22.2 (out-of-scope list) | **matched** | see §11 |

No ambiguity required reinterpretation, and no silent resolution of an unresolved decision was
found.


## 5. Implementation inspection (actual code, not the report)

| Claim to verify | Independent finding |
|---|---|
| `evidence_line_items` created exactly per §7.1 | **confirmed** — 14 columns; types/nullability/defaults exactly as specified (incl. `extraction_method varchar NOT NULL DEFAULT 'unknown'`) |
| 4 inline constraints | **confirmed** — `identity_unique UNIQUE (source_item_id, line_number)`, `line_number >= 1`, `source_page IS NULL OR >= 1`, `materialisation_kind IN ('FORWARD','BACKFILL')`; **no** CHECK on `extraction_method` (B2-D7) |
| `source_item_id NOT NULL` + RESTRICT | **confirmed** — `uuid NOT NULL`, `FOREIGN KEY … ON DELETE RESTRICT` |
| org / source-file relationships | **confirmed** — `organization_id → organizations ON DELETE CASCADE`; `source_file_id → organization_files ON DELETE SET NULL` |
| two explicit indexes + constraint-backed unique | **confirmed** — `idx_eli_org`, `idx_eli_source_file`, plus `evidence_line_items_identity_unique` (counted separately) |
| RLS + exactly two SELECT-only policies | **confirmed** — `relrowsecurity=t`, `relforcerowsecurity=f`, 2 policies, both `SELECT`/`{authenticated}` |
| privilege posture | **confirmed** — ACL `{postgres=arwdDxtm, authenticated=r, service_role=arwdDxtm}`; `anon` absent; no MAINTAIN anywhere |
| no triggers | **confirmed** — `pg_trigger` count for the table (non-internal) = 0 |
| no retention/deletion mechanism | **confirmed** — no `deleted_at`/`is_active`/`updated_at`; no purge function; repository `delete()` raises `NotImplementedError` |
| eligibility only from `extracted_data.line_items[]` | **confirmed** — `derive_line_candidates` reads only `extracted_data`; ineligible when the key is absent/not a list |
| flat records never fabricated | **confirmed** — flat payload ⇒ `eligible=False`, 0 rows |
| empty array ⇒ 0 rows, no fallback | **confirmed** — `skipped_no_lines=1`, 0 rows |
| recognised-key vocabulary | **confirmed** — exactly the 10 keys of §11.2; non-recognised keys excluded from the hash |
| 1-based ordinal identity, gaps preserved | **confirmed** — ordinals from `index+1`; malformed/empty elements skipped without renumbering |
| duplicates stay separate | **confirmed** — same hash, distinct ordinals |
| canonical hash determinism / `100`≡`100.0`≡`100.00` | **confirmed** (§7 probes 9; see also F-025-1 in §15) |
| `mapped_data` never an identity source | **confirmed** — an item whose `mapped_data.line_items` exists but `extracted_data.line_items` does not yields 0 rows |
| B2 never rewrites extraction JSONB | **confirmed** — `md5(extracted_data::text)` identical before/after materialise + backfill |
| idempotency: insert-if-absent, no `DO UPDATE` | **confirmed** — the only write statement is `INSERT … ON CONFLICT (source_item_id, line_number) DO NOTHING`; no `UPDATE`/`DELETE` SQL for the table exists in the data layer (only inside negative privilege *tests*) |
| divergence never rewrites stored provenance | **confirmed** — stored hash/ordinals unchanged after a corrected payload |
| forward hook is the single choke point | **confirmed** — `_materialise_evidence_lines` is called after the successful UPDATE in both `save_extracted_data` and `update_item(extracted_data=…)`, nowhere else |
| hook is best-effort (cannot break the save) | **confirmed** — `try/except Exception` ⇒ log; **injected-failure probe**: the extraction save still succeeded and the item persisted (§7 probe 24) |
| `extraction_method` additive keyword | **confirmed** — defaulted keyword on both methods (no existing caller changes); priority = per-line override → write-site stamp → queue stamp → `unknown` |
| `CalculationRequest.source_line_item_id` + snapshot propagation | **confirmed** — request field → `_build_snapshot` → `calculation_snapshots.source_line_item_id`; the ordinal resolve is a guarded lookup in both calculation paths |
| request-ID derivation unchanged | **confirmed** — `uuid5(NAMESPACE_DNS, f"{job.id}::calc::{idx}::c1::{calc_digest}")` with `_calc_payload_digest(extracted, mapped_data)`: **no** line id, **no** line row read |
| `_canonical()` conditional line inclusion | **confirmed** — appended only when set; a no-line snapshot hashes **identically** to the pre-B2 formula (recomputed independently) |
| no historical retro-linking | **confirmed** — pre-existing snapshot byte-identical with `source_line_item_id` still NULL |
| disclosure `link_value_evidence` additive kwarg | **confirmed** — kwarg added; snapshot-derived fill when omitted; written in the upsert, the NULL-snapshot UPDATE and the NULL-snapshot INSERT; **`$2..$7` positions of the NULL-snapshot branch preserved** (`source_line_item_id` appended as `$8`), so no existing B1 expectation changes |
| audit reuses the existing mechanism | **confirmed** — `data.audit.AuditRepository` over `audit_trail`; neither migration mentions `audit_trail`; no parallel audit system |
| no B3/B4 leakage into the B1 repository | **confirmed** — `source_line_item_id` appears only in the sanctioned `disclosure_value_evidence` statements plus the snapshot-derived read; `evidence_line_items` never appears in B1 SQL |


## 6. Database verification

Verified from the **provisioned verification clone** (`ct_b2_iv_20260913`) — not from the
implementation's clone and not from a report.

### 6.1 `evidence_line_items` columns (information_schema)

```
id                  uuid       NOT NULL  default uuid_generate_v4()
organization_id     uuid       NOT NULL
source_item_id      uuid       NOT NULL
source_file_id      uuid       NULL
line_number         integer    NOT NULL
source_page         integer    NULL
row_reference       text       NULL
raw_description     text       NULL
raw_quantity        numeric    NULL
raw_unit            text       NULL
payload_hash        text       NOT NULL
extraction_method   varchar    NOT NULL  default 'unknown'
materialisation_kind varchar   NOT NULL
created_at          timestamptz NOT NULL default now()
```

### 6.2 Constraints (as PostgreSQL reports them)

| Constraint | Definition |
|---|---|
| `evidence_line_items_identity_unique` | `UNIQUE (source_item_id, line_number)` |
| `evidence_line_items_kind_check` | `CHECK (materialisation_kind IN ('FORWARD','BACKFILL'))` |
| `evidence_line_items_line_number_check` | `CHECK (line_number >= 1)` |
| `evidence_line_items_source_page_check` | `CHECK (source_page IS NULL OR source_page >= 1)` |
| `evidence_line_items_source_item_id_fkey` | `FOREIGN KEY (source_item_id) REFERENCES manual_extraction_items(id) ON DELETE RESTRICT` |
| `evidence_line_items_source_file_id_fkey` | `… organization_files(id) ON DELETE SET NULL` |
| `evidence_line_items_organization_id_fkey` | `… organizations(id) ON DELETE CASCADE` |
| `evidence_line_items_pkey` | `PRIMARY KEY (id)` |

### 6.3 Downstream links

| Object | Type | Nullable | FK delete rule |
|---|---|---|---|
| `calculation_snapshots.source_line_item_id` | uuid | **YES** | `f / n` → `evidence_line_items(id) ON DELETE SET NULL` |
| `disclosure_value_evidence.source_line_item_id` | uuid | **YES** | `f / n` → `evidence_line_items(id) ON DELETE SET NULL` |

### 6.4 Indexes / triggers / B3-B4 objects

* Indexes: `evidence_line_items_identity_unique` (unique), `evidence_line_items_pkey`,
  `idx_eli_org (organization_id)`, `idx_eli_source_file (source_file_id)` — exactly the
  declared set (the identity index is constraint-backed and counted separately).
* Non-internal triggers on `evidence_line_items`: **0**.
* Public tables matching `%intensity%`, `%narrative%`, `%commentary%`, `%insight%`: **0**.


---

## 7. Independent runtime verification

Method: a purpose-written probe suite (`/tmp/iv_runtime.py`, verification-only, **not** a repo
artefact) using **its own fixtures** — fresh organisations, batches, items, a `csv` queue row,
a DEFRA factor, `organization_members`, and a `processing_entities` + `staff_profiles` +
`work_item_assignments` PE context — driving the real modules
(`ManualExtractionRepository`, `EvidenceLineItemsRepository`, `CalculationEngine`,
`DisclosureRepository`) against the disposable verification clone.

### 7.1 Runtime acceptance matrix (required vs observed)

| Case | Required | Observed | Verdict |
|---|---|---|---|
| structured 4-line extraction (via the forward hook) | 4 persisted lines, ordinals 1–4 | `[1,2,3,4]`, `kind=FORWARD`, org resolved server-side, stamp `iv-forward-csv` | **PASS** |
| duplicate identical lines | separate ordinals | 2 rows, same hash, distinct ids | **PASS** |
| malformed middle line | ordinal gap preserved | ordinals `[1,3]`, `skipped_malformed=1` | **PASS** |
| no `line_items` | zero lines | 0 rows, `eligible=False` | **PASS** |
| empty `line_items` | zero lines, no flat fallback | 0 rows, `skipped_no_lines=1` | **PASS** |
| rerun | zero duplicate inserts | settled rerun: 0 inserts, all rows/hashes identical | **PASS** |
| changed source payload | divergence only; stored row unchanged | `divergent_ordinals=(1,)`, 0 inserts, stored rows byte-identical | **PASS** |
| multiple calculations for the same line | same line provenance | 2 distinct snapshots → same `source_line_item_id`; line row unchanged | **PASS** |
| flat document calculation | line linkage NULL | snapshot `source_line_item_id IS NULL` | **PASS** |
| historical snapshot | not retro-linked | row `md5` unchanged; link still NULL after a backfill | **PASS** |
| evidence linkage | correct source line | `dve.source_line_item_id` = the line; re-link idempotent (1 row); omitted kwarg derived from the snapshot; consistency invariant 0 violations; NULL-snapshot branch also persists it | **PASS** |
| org isolation | cross-tenant denied | member A sees exactly its line; member B sees **0** of org A; no other-batch leakage | **PASS** |
| PE isolation | cross-entity denied | PE-X sees its assigned item's line; sees **0** of an item assigned elsewhere | **PASS** |
| authenticated INSERT / UPDATE / DELETE | denied | all three → `InsufficientPrivilegeError` | **PASS** |
| `anon` | no access | denied at the privilege layer (stronger than 0 rows) | **PASS** |
| service-role materialisation | permitted | the pool (service role) inserted every line above | **PASS** |
| source extraction-item delete | RESTRICT failure | `ForeignKeyViolationError`; lines intact | **PASS** |
| no retention trigger | confirmed | 0 triggers; no soft-delete/purge column; `delete()` raises | **PASS** |
| backfill dry-run | zero writes | rows `10→10`, `audit_trail 12→12`, `audit_written=False` | **PASS** |
| forward hook failure | extraction save still succeeds | injected `RuntimeError` → save returned the item, row persisted `status='extracted'`, 0 lines | **PASS** |
| audit granularity | 1 forward event/doc, 1 summary event/run, per-item divergence | observed exactly that (§7.2) | **PASS** |
| audit payload discipline | no source content/URLs/secrets | 0 audit rows containing line values, references or URLs | **PASS** |
| line identity under a shorter corrected array | never renumber/delete | ordinals stayed `[1,2,3,4]`, 0 inserts, divergence reported | **PASS** |

**Result: 45 checks, 43 PASS on the first run**; the two initial FAILs were probe-design
artefacts (shared global state), re-probed and PASS (§7.3).

### 7.2 Audit evidence (from `audit_trail`, verification clone)

* `report:evidence_line_items_materialised` — one row per document, e.g.
  `{"materialised": 4, "skipped_empty": 0, "payload_digests": {…}}`.
* `report:evidence_line_items_backfilled` — one row per run, e.g.
  `{"dry_run": false, "scanned_items": …, "materialised_rows": …, "divergences": …}`.
* `report:evidence_line_items_divergence_detected` — per affected item per run, payload
  `{"divergent_ordinals": [1], "line_item_ids": ["…"]}` — ordinals and ids only.
* No payload contained `Electricity`, `Natural gas`, `Diesel`, an invoice reference or a URL.

### 7.3 The two initial FAILs — investigated and resolved as probe artefacts

| Probe | Initial result | Root cause found | Corrected re-probe |
|---|---|---|---|
| "rerun inserts zero duplicates" | `materialised=1` | The `1` was the clone-seeded **pre-B2 item** (`33333333-…`: `line_items[]` present, never materialised) — exactly what a Class-1 backfill must do. That item now holds exactly 1 line, ordinal 1, `BACKFILL`, `unknown` | `/tmp/iv_recheck.py` **A1/A2 PASS**: settled rerun inserts nothing and rewrites nothing |
| "divergence audited per affected item" | count ≠ 1 | After a payload is corrected, **every subsequent run re-reports** the still-divergent ordinal (per-run reporting). `audit_trail` shows repeated identical divergence events for that item | `/tmp/iv_recheck.py` **B1/B2 PASS**: exactly +1 event per run; payload minimal |


---

## 8. Migration idempotency evidence (independent)

Independently built clone from `pg_dump --schema-only` of the production-shaped local database
(116 public tables; ACLs/policies/RLS included; 115 expected `SET ROLE` notices from role-owned
objects during restore). My own inventory tool captured four stages:

| Stage | State | Tables | Grant rows | Policies |
|---|---|---|---|---|
| A | pre-migration (with my probe rows) | 116 | 2840 | 174 |
| B | after B1 (both files, `rc=0`) | 127 | 3011 | 187 |
| C | after B2 (both files, `rc=0`) | 128 | 3026 | 189 |
| D | after **re-applying all four** (`rc=0`) | 128 | 3026 | 189 |

**A → B (B1):** adds exactly the 11 `disclosure_*` tables; **zero** columns/constraints/indexes
added to pre-existing tables; grants, policies and RLS flags on pre-existing tables
**unchanged**; probe rows unchanged.

**B → C (the declared B2 delta, contract §20.3):**

```
tables added                       : ['evidence_line_items']                     (exactly 1)
columns added on pre-existing      : [calculation_snapshots.source_line_item_id,
                                      disclosure_value_evidence.source_line_item_id]  (exactly 2)
columns removed / changed          : [] / []
constraints added on pre-existing  : [calculation_snapshots_source_line_item_id_fkey,
                                      disclosure_value_evidence_source_line_item_id_fkey]  (2)
constraints removed / changed      : [] / []
indexes added on pre-existing      : [(calculation_snapshots, idx_calculation_snapshots_source_line_item),
                                      (disclosure_value_evidence, idx_dve_source_line_item)]  (2)
indexes removed                    : []
grants on pre-existing tables      : unchanged ✔
policies on pre-existing tables    : unchanged ✔
RLS flags on pre-existing tables   : unchanged ✔
pre-existing probe rows            : unchanged ✔ (the only difference is the new table appearing)
```

**C vs D (re-application):** `tables`, `grants`, `policies`, `rls`, `columns`, `constraints`,
`indexes`, `probes` — **all eight sections identical**. No duplicate objects, no schema drift,
no privilege/policy drift, no existing-table modification.

## 9. B1 regression evidence (B1 → B2 boundary)

| Check | Evidence | Verdict |
|---|---|---|
| B1 migration files unchanged | `md5` at verification start **and** end: `20260914… = fd3a18a038bfe11b7fb098a3f52f09ed`, `20260915… = 0cdb37a8583c2b21799c68f00484012b`; byte sizes 32710 / 9823 — identical to the pre-implementation sizes recorded before the B2 work began. B2's migrations never touch them | **PASS** |
| B1 migration-text guards intact | The guards read the B1 file text; those files contain neither `evidence_line_items` nor `source_line_item_id` in statement position | **PASS** |
| Only the two §20.6-named B1 tests amended | `test_b2_b3_b4_boundary_untouched` and `test_no_b2_b3_b4_objects_in_the_repository` are the only amended tests (before/after inspected); `test_no_b2_b3_b4_tables` and `test_no_source_line_item_id_column` are **unchanged and passing** | **PASS** |
| Amendments do not weaken B3/B4 protection | The three B3/B4 guards (`intensity`, `narrative`, `commentary`) are retained verbatim in both tests; the B1 namespace assertion (exactly the 11 `disclosure_*` tables) is retained; B2-absence assertions were replaced by a B1-namespace check and the B2 presence assertions **moved** into the B2 suite | **PASS** |
| No third B1 expectation broken | The NULL-snapshot branch's `$5/$6/$7` positions were preserved (`source_line_item_id` appended as `$8`), so the B1 F3 typing assertions are untouched; the full B1 runtime suite (15 tests) passes on the B1+B2 clone | **PASS** |
| B2 does not alter B1 semantics beyond the ratified boundary | B1's repository receives exactly one additive optional keyword plus the snapshot-derived read; no B1 policy/grant/table changed (proven by the A→B and B→C inventories) | **PASS** |
| No B3/B4 schema or implementation as a consequence of B2 | 0 public tables matching `%intensity%`/`%narrative%`/`%commentary%`/`%insight%`; B2 adds one table and two columns only | **PASS** |


---

## 10. Security / RLS / privilege evidence

| Check | Evidence | Verdict |
|---|---|---|
| ACL on `evidence_line_items` | `{postgres=arwdDxtm/postgres, authenticated=r/postgres, service_role=arwdDxtm/postgres}` — `authenticated` holds **SELECT only**; `service_role` holds table DML/DDL but **not** MAINTAIN; `anon` holds **nothing** | **PASS** |
| `has_table_privilege` probes | `anon SELECT = false`; `authenticated INSERT/UPDATE/DELETE = false`, `SELECT = true`; `service_role INSERT = true` | **PASS** |
| RLS state | `relrowsecurity = true`, `relforcerowsecurity = false` (B1's declared posture; the production RLS hold is untouched) | **PASS** |
| Exactly two SELECT policies | `evidence_line_items_org_select` → `p8_disclosure_is_org_member(organization_id)`; `evidence_line_items_entity_select` → `((work_item_effective_entity(source_item_id) IS NOT NULL) AND is_entity_member(work_item_effective_entity(source_item_id)))` | **PASS** |
| PE policy mirrors the ratified item boundary (B2-D3) | `manual_extraction_items_entity_select` carries the identical expression with `id` in place of `source_item_id` — no widening, no new authorization model | **PASS** |
| No authenticated write path to lines | Only the org/PE SELECT policies exist; there is no `FOR INSERT/UPDATE/DELETE` policy, and the privileges deny those verbs (runtime-proven) | **PASS** |
| Cross-tenant denial | org-B member reads **0** org-A rows; a non-member authenticated session reads 0 | **PASS** |
| Cross-entity (PE) denial | PE-X sees its assigned item's line only; PE-Y's item returns 0; PE-Y sees 0 of PE-X | **PASS** |
| `anon` denial | denied at the privilege layer (stronger than an RLS 0-row result) | **PASS** |
| Sensitive data in audit payloads | 0 audit rows for the three B2 actions contain line values, references or URLs; payloads carry counts, ordinals, ids and hashes only | **PASS** |
| Secrets introduced | Pattern scan (api-key/secret/password/token/jwt/bearer/private-key) over every added/removed diff line of the touched tracked files **and** the new files/migrations: **no matches** | **PASS** |
| Production / persistent databases | Only `127.0.0.1:54426` was used: the source database was read **only** by `pg_dump --schema-only`; all schema/data changes occurred solely in the disposable clones `ct_b2_iv_20260913` (this task) and `carbontally_b2_clone_20260913` (the implementation's). No production connection, no dev/test migration, no investor-demo access | **PASS** |
| Dev/test databases still unprovisioned | The B2 runtime suite against `carbontally_test` yields **21 SKIPPED** (“B2 evidence-line schema is not provisioned”), confirming B2's migrations were **not** applied there | **PASS (data-safety property)** |

## 11. Scope-boundary evidence

| Boundary | Independent evidence | Verdict |
|---|---|---|
| P1 extraction untouched | `git status` shows `api/v3_processing_workflow.py`, `services/automatic_extraction.py`, `services/extraction_suggestions.py`, `services/ai_document_extraction.py` **unmodified**; each contains **0** B2 references | **PASS** |
| PDF/IMAGE remediation, OCR, AI row extraction, historical re-extraction | No OCR/AI/parser call in any B2 module (static scan); no extraction re-run anywhere; the backfill reads only persisted JSONB | **PASS** |
| P2 / EF-E, calculation formulas, factor matching | No factor/matching/formula/conversion/rounding code changed; the touched calculation files add one optional field, one snapshot column and a guarded lookup | **PASS** |
| Report lifecycle, A-RLS, RLS remediation, retention | No report-table RLS, lifecycle or retention artefact; no `FORCE ROW LEVEL SECURITY`; only two new SELECT policies on the new table | **PASS** |
| B3 / B4 | 0 intensity/narrative/commentary tables; no projections, mappings, templates or narrative code | **PASS** |
| Phase 8-X / Phase 9 / Insight / billing / frontend / new API | 0 occurrences in the B2 artefacts; no new route; no frontend file touched by B2 | **PASS** |
| Diff-level scope check | Across the 8 tracked files B2 touched: **+174 / −25** lines, and **none** of the added/removed lines mentions `intensity`, `narrative`, `commentary`, `insight`, `ocr`, `tesseract`, `billing`, `subscription`, `phase 8-x/9`, `retention` or `force row` | **PASS** |
| Unrelated work untouched | The parallel GA4 commit and its later untracked files are unrelated to B2; this verification changed no repository file other than adding its own report | **PASS** |


---

## 12. Finding-by-finding disposition

| Finding | Independent verification | Disposition |
|---|---|---|
| **F-024-1** — §11.2's backfill attribution rung 2 (`manual_extraction_batches.ai_extraction_method`) does not exist, so attribution is queue → `unknown` | `information_schema.columns` for `manual_extraction_batches.ai_extraction_method` = **0 rows** (confirmed on the clone). Behaviour: an item whose queue row carries `ai_extraction_method='iv_queue_stamp'` records `iv_queue_stamp`; an item with no queue row records `unknown`. **No column was invented**, no schema or semantics fabricated; `unknown` is the contract's declared honest default | **CONFIRMED — non-blocking; consistent with the contract and with the contract's own F-B2-15** |
| **F-024-2** — `api/v3_processing_workflow.py` not modified, so that site cannot pass `"manual"` | File **unmodified** (`git status` clean) and contains **0** B2 references. Resulting provenance is contract-compliant: §11.2 allows `unknown` where a site cannot supply a stamp, and the queue-derived stamp is used when available. The two other human sites (`v3_operations.py`) pass `"manual"`; the automatic pipeline passes its real `method_stamp` | **CONFIRMED — bounded, documented deviation with no functional impact** |
| **F-024-3** — line provenance enters `_canonical()` only when set; request-ID derivation untouched | Recomputed the pre-B2 canonical string for a no-line snapshot: the implementation's hash **equals** it. With a line set, the hash changes (the line is appended) while the no-line hash stays identical. `uuid5(NAMESPACE_DNS, f"{job.id}::calc::{idx}::c1::{calc_digest}")` contains no line id, and `_calc_payload_digest(extracted, mapped_data)` reads no line row. Runtime: a line-aware snapshot persists correctly; a historical snapshot stays byte-identical and NULL | **CONFIRMED — §8.4 satisfied** |
| **F-024-4** — no delete path exists | No `UPDATE`/`DELETE` SQL for `evidence_line_items` anywhere in the data layer (grep; the only occurrences are negative assertions inside the B2 test file); `delete()` raises `NotImplementedError` (runtime-proven). Consistent with amend-never-delete (B2-D2) and B2-D11 | **CONFIRMED — intended and correct** |
| **F-024-5** — dry run performs zero writes | Runtime: `evidence_line_items` rows `10 → 10`, `audit_trail` rows `12 → 12`, `report.audit_written = False` across a full dry-run backfill — **no writes of any kind** | **CONFIRMED** |
| **F-024-6** — pre-existing integration failures, none attributable to B2 | Ran the whole integration suite twice: on the B2-provisioned verification clone → **15 failures**; on the standard test database → **24 failures**. Byte-collation set difference: **unique to the B2 clone = 0**; shared = 15; unique to the baseline = 9 (incl. the entire `test_calculation.py` suite, which *passes* on the B2 clone) | **CONFIRMED — pre-existing/environmental; not fixed (out of scope)** |
| **F-024-7** — the dev/test skip is real and is not a PASS | Against `carbontally_test`: `21 skipped`, reason “B2 evidence-line schema is not provisioned in this integration database …”. Recorded as **SKIPPED — NOT PASS**; all B2 acceptance evidence therefore comes from the disposable B1+B2 clone | **CONFIRMED — SKIPPED, NOT PASS** |


---

## 13. Exact tests / commands / results

Run from `/home/shomonrobie/carbon_tally/backend` unless stated. `IVDB` =
`postgresql://postgres:postgres@127.0.0.1:54426/ct_b2_iv_20260913` (this task's disposable clone).

| # | Command | Result |
|---|---|---|
| 1 | `dropdb/createdb ct_b2_iv_20260913`; `pg_dump --schema-only …/postgres \| psql ct_b2_iv_20260913` | clone: 116 public tables, B1/B2 absent, ACLs restored (115 expected `SET ROLE` notices) |
| 2 | `python /tmp/iv_inv.py …/ct_b2_iv_20260913 /tmp/iv_A.json null --pin=/tmp/iv_pins.json` | stage A captured (116 tables / 2840 grants / 174 policies) |
| 3 | `psql … -f 20260914000000_p8_b1_…sql`, `…20260915000000_p8_b1_…sql` | `rc=0`, `rc=0`; stage B captured (127 / 3011 / 187) |
| 4 | `psql … -f 20260916000000_p8_b2_…sql`, `…20260916010000_p8_b2_…sql` | `rc=0`, `rc=0`; stage C captured (128 / 3026 / 189) |
| 5 | re-apply all four files | `rc=0` ×4; stage D captured — **C ≡ D on all eight inventory sections** |
| 6 | `python /tmp/iv_cmp.py A B C D` | declared B2 delta exact and exclusive; grants/policies/RLS/probe rows unchanged on pre-existing tables |
| 7 | `python /tmp/iv_runtime.py "$IVDB"` | **45 checks: 43 PASS**; 2 probe-design artefacts (re-probed at #8) |
| 8 | `python /tmp/iv_recheck.py "$IVDB"` | **RESULT: PASS** — A1/A2/B1/B2 all PASS |
| 9 | `python -m pytest tests/unit/data/test_b2_migration.py tests/unit/domain/test_evidence_line_items.py -q` | **`rc=0`** (14 static + 18 pure) |
| 10 | `INTEGRATION_DATABASE_URL="$IVDB" python -m pytest tests/integration/test_evidence_line_items_b2_runtime.py tests/integration/test_disclosure_b1_runtime.py -q` | **36 passed, `rc=0`** (21 B2 runtime + 15 B1 regression) |
| 11 | `python -m pytest tests/integration/test_evidence_line_items_b2_runtime.py -q -rs` (default `carbontally_test`) | **21 skipped, `rc=0`** → SKIPPED — NOT PASS |
| 12 | `INTEGRATION_DATABASE_URL="$IVDB" python -m pytest tests/integration -q` | 15 FAILED |
| 13 | `python -m pytest tests/integration -q` (default `carbontally_test`) | 24 FAILED |
| 14 | `LC_ALL=C comm -23 <clone FAILED> <baseline FAILED>` | **empty → 0 failures unique to the B2 clone** (shared = 15) |
| 15 | psql introspection (columns, constraints, FKs, indexes, triggers, ACL, policies, `has_table_privilege`, B3/B4 scan) | all match the contract (§6, §10) |
| 16 | `git status`, `git show --stat HEAD`, `git diff --stat` (8 tracked files), `git diff -U0` + keyword scan | B2 uncommitted; HEAD carries 0 B2 files; diff is B2-only (+174/−25) with no scope-creep keywords |
| 17 | `md5sum` of both B1 migration files (start and end) | identical: `fd3a18a0…`, `0cdb37a8…` |

### 13.1 Skipped tests — clearly labelled

* **SKIPPED — NOT PASS:** `tests/integration/test_evidence_line_items_b2_runtime.py` — 21 tests
  skipped on `carbontally_test` (and on the dev/demo database) because neither holds the B1/B2
  schema. Not counted as a pass anywhere in this report.
* No other suite was skipped: the B1 runtime suite, the B2 static/pure suites and the whole
  integration suite all **executed** (on the disposable clone or the standard test database).

---

## 14. Remaining non-blocking observations

| ID | Observation | Impact / recommendation |
|---|---|---|
| **F-025-1** | **Canonicalisation normalises numeric-looking *text* values.** `canonical_value()` applies `format(Decimal(str(v)).normalize(), "f")` to every scalar value of the ten recognised keys — not only to JSON numbers. Demonstrated: `invoice_number "00123"` and `"123"` produce the **same** `payload_hash`, and `decide_ordinals` consequently returns `SKIP_EXISTS` (divergence invisible) for that pair. Contract §11.2 says “numbers normalised”, so this is a literal-but-broad reading of the formula; it *reduces* false divergences (its stated purpose) and breaks no acceptance test, schema or security boundary. | **Non-blocking.** If the PO judges text keys out of scope for numeric normalisation, a bounded follow-up could restrict normalisation to JSON numbers only — noting that doing so would turn pre-existing rows with numeric-looking text keys into *divergence reports* (detect-only; stored rows stay immutable). Recommend recording the decision rather than silently changing it. |
| **F-025-2** | **Unreachable dead code:** `backend/domain/line_items.py` line 350 holds `return None` immediately after `return tuple(decisions)` inside `decide_ordinals` (and `first_text()` ends without an explicit `return None`). The module compiles (`py_compile` OK); behaviour is unaffected. | **Non-blocking (cosmetic).** A one-line cleanup for a future batch; recorded here rather than fixed, per the verification boundary. |

Neither observation is a material contract, security, integrity, scope, migration or runtime
defect, and neither affects any B2-D1…B2-D12 decision.


---

## 15. Final verdict

### `B2 INDEPENDENT VERIFICATION PASS — READY FOR PO CLOSURE`

Justification (every material check independently executed; none relying on the implementation
report or the implementation's clone):

| Dimension | Verdict |
|---|---|
| Contract conformance (schema, constraints, FKs, indexes, RLS, policies, privileges, delete semantics, §11 derivation, §12 boundary, §13 linkage, §9 evidence link, §17 audit) | **PASS** |
| Migration safety (two additive migrations, `rc=0` twice, exact declared delta, zero drift on pre-existing objects, zero row rewrites) | **PASS** |
| Runtime acceptance (§20.2 matrix, incl. security, RESTRICT, dry-run, best-effort hook) | **PASS** — 21/21 suite tests + 45/45 independent probes (after re-probing two probe artefacts) |
| B1 → B2 boundary (§20.6 amendments bounded; B1 files byte-identical; B1 suite green; no third expectation broken; no B3/B4 leakage) | **PASS** |
| Security / RLS / privilege posture; audit payload discipline; no secrets | **PASS** |
| Scope discipline (P1/P2/S-series/B3/B4/8-X/9/Insight/billing/frontend untouched; diff-level proof) | **PASS** |
| Data safety (production, dev, investor demo and persistent test DB untouched; disposable clones only) | **PASS** |
| Blocking findings | **None** |
| Non-blocking observations | **F-025-1** (canonicalisation breadth — needs a PO note if it matters), **F-025-2** (unreachable dead line). Neither material |

**Explicitly not claimed:** PO closure of B2, production readiness, deployment, or acceptance of
any later batch (B3/B4/8-X/9) — none of which exists. Independent verification does **not** close
B2; that remains a PO action, and the two observations above are offered for it.

**No fixes were performed.** Implementation files, migrations, tests, B1 artefacts, RLS and
databases were left exactly as found (apart from the disposable clones, retained so the PO or a
further verifier can re-run the suites).

**Verification boundary respected:** no commit, no push, no deployment, no schema change outside
the disposable clones, no modification of any B2/B1 implementation or test file.
