# CT-PO-P12-STEP2-FROZEN-SEED-MANIFEST-20260924

**Reference:** `CT-PO-P12-STEP2-FROZEN-SEED-MANIFEST-20260924`
**Date:** 2026-09-24
**Governing workplan:** STEP 2 — **D-2-7 frozen counts**
**Status:** STEP-2 DELIVERABLE — frozen seed manifest (as actually seeded)
**Production deployment:** **NOT AUTHORIZED**

---

## 1. Provenance

| Item | Value |
| --- | --- |
| Release | `p8-release-reconciled` @ `35eb7bab9ee87839d07b50a2fd70a662d1ce1675` |
| Database | `carbontally_demo_local` (`127.0.0.1:54426`, container `supabase_db_carbon_ledger`) |
| Migration set | 81 files, 0 errors |
| Generator | `8ade2bf778d518d59924905849ab114ab2d082a0` (HEAD == pin) |
| Corpus (PDF) | `t3-uk-curated-v1` — 11 documents, real-extractor-selected |
| Corpus (tabular) | `p12-step2-tabular/p12imp_org-a-multi-site-gas-2025.csv` — SHA-256 recorded in `<state>/corpus/p12-step2-tabular/corpus_provenance.json` |
| Seed invocations | `tools/demo_lab/run_demo_lab.sh --backend --factors`; `tools/demo_lab/t3_scenarios.py seed --wait 180`; the tabular seeder (real `POST /api/v3/uploads` + `…/enqueue`); Story-B API seeder |
| Seed timestamps | 2026-09-24T08:56Z (stack/factors/verify) → 09:15Z (tabular) → 09:18–09:21Z (Story B / reports / Insight) |
| Evidence | `<state>/evidence/{verify_,t2c_seed_,t3_scenarios_}20260924*.json`, `p12_step2_tabular_seed.json`, `p12_step2_story_b.json`, `p12_step2_retries.json`, `p12_step2_completion.json`, `p12_step2_closeout.json`, `p12_step2_final.json` |

## 2. Identity topology (as seeded)

| Persona | Count | Detail |
| --- | --- | --- |
| Direct customer organisations | 2 | `Demo Lab Organisation A` (`3fd0f325…`), `Demo Lab Organisation B` |
| Consultant firm | 1 | `consultant_profiles = 1`, `consultant_firm_members = 2` |
| Client organisations | 2 | `Demo Lab Client A` (`02b38744…`), `Demo Lab Client B` |
| Consultant↔client grants | 2 | `consultant_clients = 2` |
| Processing entities | **1** | `Demo Lab Processing Entity Alpha` (active) — **target was 2** |
| Users (auth mirror) | 13 | `users = 13`, `auth.users` mirrored ids |
| Organisation members | 8 | `organization_members = 8` |
| Internal staff profiles | 3 | `platform_admin`, `internal_operator`, `pe_manager` |
| Staff roles | 3 | no role grants `can_manage_staff` (see limitation) |

## 3. Document corpus and pipeline outcomes

| Item | Count |
| --- | --- |
| Documents uploaded | **11** (10 PDF corpus + 1 CSV) |
| Fully processed (`customer_review`) | **1** (the CSV) |
| Blocked for manual review (`manual_review`, real persisted reason) | **10** |
| Tabular (`SPREADSHEET`) documents | **1** |
| `extracted_data.line_items[]` present | **1** (the CSV — `array`) |

### Blocked documents — genuine, persisted failure classes

| Class | Document(s) | Persisted reason (abbreviated) |
| --- | --- | --- |
| Ambiguous mapping | electricity, diesel, ambiguity, consultant-client-a, direct-org-b-isolation | `no confident factor for 'Electricity' kWh (status=ambiguous…)` |
| No matching factor / clarification | waste, consultant-client-b | `clarification required for 'Waste' …` |
| No match | water | `no confident factor for 'Water' litres (status=no_match…)` |
| Completeness below threshold | missing-evidence | `extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit` |
| Validation missing field | gas | `validation found blocking findings: EXTRACTION_MISSING_FIELD (supplier)` |

## 4. Calculation and evidence records (Story A / Story C)

| Item | Count | Detail |
| --- | --- | --- |
| `calculation_snapshots` | **2** | both from the tabular CSV, current HEAD |
| `emissions_logs` | **2** | snapshot + factor FKs present |
| `evidence_line_items` | **2** | `materialisation_kind = FORWARD`, `extraction_method = csv` |
| Snapshots with `source_line_item_id` | **2 / 2** | resolvable to the evidence line |
| Source Evidence Viewer | **HTTP 200** | full chain + `drill_down_depth = FULL` for the Owner |

Exact calculations:

```text
12181.4 kWh (Net CV) × 0.2027 = 2469.169780 kg CO2e   (Scope 1, DEFRA-DESNZ / DEFRA-2025,
                                                       direct_multiply, algorithm v1.0)
 8420.0 kWh (Net CV) × 0.2027 = 1706.734000 kg CO2e   (same factor and method)
```

`2469.169780` reproduces the Step-1 frozen value **exactly**, now produced by the
current release through the real pipeline.

## 5. Operational workflow, messaging, reporting, master data, Insight

| Item | Count | Detail |
| --- | --- | --- |
| `work_item_assignments` | **7** | 4 `open`, 3 `closed`; assign → claim → release → reassign → claim exercised (all HTTP 200) |
| `reassignment_history` | **0** | the ops path records reassignment as a new assignment row |
| `conversations` | **4** | `org` 3, `entity` 1 |
| `messages` | **2** | one org-plane, one PE-operational |
| `conversation_participants` | 4 | server-resolved only |
| `report_versions` | **2** | **`APPROVED` (2025)** and **`DRAFT` (2024)** — real lifecycle variation |
| `facilities` / `assets` / `suppliers` | 1 / 1 / 1 | asset linked to the facility; created via the real CRUD API (HTTP 201) |
| Insight tool registry | **10** tools | closed catalogue confirmed live |
| Insight executions | **3** | `insight_aggregation` → `success`; `insight_aggregation` (no rows) → **`no_data`**; `calculation_snapshot_lookup` → `success` |
| Insight persisted records | 1 conversation, 2 messages | `carbontally_insight_interactions = 0` |

## 6. Authorization / isolation result

```text
13/13 actor contexts · 30/30 authorization probes · 18/18 isolation rules · 0 failures
```

## 7. Frozen counts vs the Step-1 planning targets

See `CT-PO-P12-STEP2-EXPECTED-COUNT-VERIFICATION-20260924.md` for the expected-vs-actual
table and the status of each target.
