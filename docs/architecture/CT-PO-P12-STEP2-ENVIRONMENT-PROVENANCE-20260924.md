# CT-PO-P12-STEP2-ENVIRONMENT-PROVENANCE-20260924

**Reference:** `CT-PO-P12-STEP2-ENVIRONMENT-PROVENANCE-20260924`
**Date:** 2026-09-24
**Governing workplan:** STEP 2 — environment provenance record
**Status:** STEP-2 DELIVERABLE
**Production deployment:** **NOT AUTHORIZED**

---

## 1. Release and identity

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD at Step-2 provisioning | `35eb7bab9ee87839d07b50a2fd70a662d1ce1675` (**identical to the Step-1 final release state**) |
| Step-1 pre-Step-2 HEAD | `3c38cbc59c95c04ea434ae128f86c94fd4b69190` |
| GitHub alignment | `github/p8-release-reconciled == HEAD` |
| Database | `carbontally_demo_local` |
| Host / port | `127.0.0.1:54426` |
| Container | `supabase_db_carbon_ledger` (PostgreSQL 17.6) |
| Gateway | `127.0.0.1:54430` |
| Backend | `127.0.0.1:8070` |

## 2. Pre-reset manifest (captured before any mutation)

Recorded at `/tmp/s2_pre_reset_manifest.json` and summarised here:

| Item | Pre-reset value |
| --- | --- |
| Public tables | 136 |
| Insight tables | **0** (the Step-1 gap) |
| `evidence_line_items` | present, **0 rows** |
| RLS-enabled tables | 136 / 136 |
| Policies | 274 |
| `storage` schema | present |
| Organizations | 4 |
| Users | 13 |
| Organisation members | 8 |
| Processing entities | 1 |
| Batches / work items | 4 / 14 |
| Snapshots / emissions | 1 / 1 |
| Conversations / messages | 0 / 0 |
| Report versions | 2 (both `DRAFT`) |
| Facilities / assets / suppliers | 0 / 0 / 0 |
| Assignments / reassignments | 0 / 0 |
| `audit_trail` | 113 |
| Generator HEAD | `8ade2bf…` (**== pin**) |
| `/tmp/extgen` | absent |

## 3. Post-provision state (this session)

| Item | Post-provision value |
| --- | --- |
| Public tables | **141** |
| Insight tables | **6** |
| Migration files / errors | **81 / 0** |
| RLS-enabled tables | 141 / 141 |
| Policies | **298** |
| Storage: tables / functions / D32 policies / buckets | 10 / 17 / 4 / 2 (both private) |
| Auth: enums / helper functions | 9 / 4 |
| Factors | 7,049 (DEFRA-2025 7,029 + SEAI-2025 20), 2 active batches |
| Documents | 11 (10 PDF + 1 CSV); 10 blocked, 1 processed |
| Snapshots / emissions / evidence lines | 2 / 2 / 2 |
| Assignments (open/closed) | 7 (4 / 3) |
| Conversations (org/entity) / messages | 4 (3 / 1) / 2 |
| Report versions | 2 (`APPROVED`, `DRAFT`) |
| Facilities / assets / suppliers | 1 / 1 / 1 |
| Insight | 6 tables; 10-tool registry; 3 executions incl. 1 `no_data`; 1 conversation + 2 messages |
| Security verification | 13/13 contexts, 30/30 probes, 18/18 isolation rules, 0 failures |

## 4. Mutation ledger (what was changed, and only this)

| Action | Scope |
| --- | --- |
| `reset_demo_lab.sh` | dropped `carbontally_demo_local`; removed the 3 lab containers; deleted the 13 lab auth users (`@demo-lab.carbontally.local`) from the local stack GoTrue |
| `run_demo_lab.sh --backend --factors` | created the lab DB from `supabase/migrations/*`; provisioned 13 lab actors; wrote `<state>/backend.env`; started the backend; loaded 7,049 factors |
| `t3_scenarios.py seed` | uploaded 11 PDF corpus documents via the real API and enqueued the real pipeline (10 blocked, 0 false successes) |
| `t3_scenarios.py reset` | removed the T3 corpus artefacts once (identities/factors preserved — asserted by the tool) |
| Tabular seeder | uploaded 1 CSV with `text/csv`; removed the artefacts of one earlier mis-typed upload created in this same session |
| Story-B/report/Insight seeders | created 1 facility, 1 asset, 1 supplier, 2 reports, 4 conversations, 2 messages, 7 assignment rows, 1 Insight conversation + 2 messages — all through the real API |
| **Not touched** | `postgres`, `carbontally_qa_phase8`, `carbontally_test`, production; RLS policies; migrations; any application/test/seed code |

## 5. Secrets

No credential, service key, JWT, refresh token or signed URL was read into a
document, printed in a report or committed. The lab credentials remain in
`<state>/credentials.local.json` (mode 600, outside the repository) and were never
opened.

## 6. Reproducibility

The environment is reproducible through
`CT-PO-P12-STEP2-RESET-REPROVISION-PROCEDURE-20260924.md`. One full
`reset → reprovision → seed → verify` cycle was executed and recorded here; a second
cycle was **not** run, so strict repeatability remains an open Step-2 criterion.
