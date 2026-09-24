# CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924

**Reference:** `CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924` — **STEP 2**
**Status:** STEP-2 DELIVERABLE — canonical environment record
**Production deployment:** **NOT AUTHORIZED**

---

## 1. Canonical environment identity

| Item | Value |
| --- | --- |
| Canonical database | **`carbontally_demo_local`** |
| Host / port | `127.0.0.1:54426` |
| Container | `supabase_db_carbon_ledger` (PostgreSQL 17.6) + lab containers `carbontally_demo_lab_{postgrest,storage,gateway}` |
| Gateway (auth + REST) | `http://127.0.0.1:54430` (`/auth/v1`, `/rest/v1`) |
| Release backend | `http://127.0.0.1:8070` (`/health` → 200) |
| Release | branch `p8-release-reconciled`, HEAD **`35eb7bab9ee87839d07b50a2fd70a662d1ce1675`** — **identical to the Step-1 final release state** |
| GitHub alignment | `github/p8-release-reconciled == HEAD` |
| Explicitly NOT canonical | `postgres` (flagship), `carbontally_qa_phase8`, `carbontally_test`, production — **none mutated** |

## 2. Schema revision

| Item | Value |
| --- | --- |
| Migration files applied | **81** (`supabase/migrations/*.sql`, sorted) |
| Migration errors | **0** |
| Public tables | **141** |
| RLS enabled | 141 / 141 |
| RLS policies | **298** |
| Insight tables | **6** — `carbontally_insight_conversations`, `carbontally_insight_interactions`, `carbontally_insight_messages`, `carbontally_insight_tool_calls`, `insight_concurrency_leases`, `insight_rate_limit_buckets` |
| B2 evidence schema | `public.evidence_line_items` present; `calculation_snapshots.source_line_item_id` present |
| Storage substrate | `storage` schema (10 tables, 17 functions), **4** approved D32 policies, 2 private buckets (`documents`, `report-artifacts`) |
| Auth bootstrap | `auth` schema cloned (structure only) + 9 enums + 4 RLS helper functions |
| Grants | 3 roles with public grants (`anon`, `authenticated`, `service_role`) |

**The Step-1 schema gap is closed**: the environment carries the complete current
release schema including all six `2026100*` Insight migrations.

## 3. Pinned synthetic generator

| Item | Value |
| --- | --- |
| Checkout | `/home/shomonrobie/carbon_tally_synthetic_documents` |
| HEAD | **`8ade2bf778d518d59924905849ab114ab2d0820a`** — **equals the required pin** |
| Modification | **none** |
| Corpus | `t3-uk-curated-v1`, 11 documents selected by the real extractor; provenance records the pin |
| `/tmp/extgen` | absent — the pinned checkout above was used as the source |

## 4. Step-2 tooling changes (demo-lab tooling only — no product change)

Five harness defects blocked a cold start. All were fixed **inside
`tools/demo_lab/`**; no application, backend, frontend, migration, RLS or test file
was modified.

| ID | Defect | Fix |
| --- | --- | --- |
| **D-2-02** | `stack.py::ensure_database` applied the storage substrate **before** migrations and `ensure_auth_bootstrap` **after** them. On a fresh DB the D32 policies cannot exist before `public.organization_members` (`relation does not exist`, then `expected 4 D32 policies, found 0`), and without `auth` the first RLS migration aborts and the chain cascades. | Re-sequenced the **existing** functions: `auth` bootstrap → migrations → storage substrate → grants → containers |
| **D-2-06** | Nothing created `auth.users` on a fresh DB, although `provision.py` mirrors ids into it | Added `_clone_auth_schema_structure()` — the same `pg_dump --schema-only` mechanism `storage.py` already uses; structure only (no rows, hashes or sessions) |
| **D-2-05** | The JWKS fallback source used a bare path (always 404), so the storage container could not start before the gateway | Corrected the URL to the GoTrue prefix `/auth/v1/.well-known/jwks.json` |
| **D-2-03** | `run_demo_lab.sh --backend --factors` starts the backend **before** loading factors; the worker builds its in-memory `FactorSearchIndex` at `start()`, so every document mapped to `no_match` (0 calculations) | Operational fix: restart the backend **after** the factors are loaded (documented in the reset/reprovision procedure) |
| **D-2-04** | `t3_scenarios._multipart` hardcodes `Content-Type: application/pdf`, so a tabular upload is stored as `file_type=PDF` and routed to the PDF extractor (`no_text`) | The tabular seeder sends `text/csv` (harness helper untouched) |

## 5. Verification of the canonical environment

`tools/demo_lab/verify.py` (read-only probes) against the canonical environment:

```text
actor contexts        : 13/13 correct (auth: password_grant)
authorization probes  : 30/30 as expected
isolation rules       : 18/18 enforced
known_product_defects : []      (F-T1-001 no longer reproduces)
database              : carbontally_demo_local
evidence              : <state>/evidence/verify_20260924T085608Z.json
```

## 6. Service state

| Service | State |
| --- | --- |
| Release backend `:8070` | running, `/health` → 200, automatic-processing worker started **after** the factor load |
| Demo Lab gateway `:54430` | running (`/auth/v1/health` → 200) |
| PostgREST / storage containers | running |
| Factor dataset | **7,049** active factors (DEFRA-2025 7,029 + SEAI-2025 20), 2 active import batches |

## 7. Residual environment limitations

| Limitation | Impact |
| --- | --- |
| Only **1** processing entity (`Demo Lab Processing Entity Alpha`) | frozen-scope case S-4 (PE Alpha → PE Beta) cannot be demonstrated; a second entity must be provisioned |
| No internal staff role grants `can_manage_staff` in the lab topology | the N1 support counterparty path returns **409** ("No authorised CarbonTally support participant is available"); the customer↔support messaging beat is unavailable |
| `reassignment_history` is empty | the reassignment is recorded as a new `work_item_assignments` row (7 rows: 4 `open`, 3 `closed`); the dedicated history table is not written by the ops path |
| `carbontally_insight_interactions` = 0 | Insight execution is demonstrated via `POST /api/v3/insight/tools/invoke` and persisted as a conversation + 2 messages; that route does not write the interaction table |
| `uk-water` scenario maps to `no_match` | the corpus contract expects it `EXPECTED_MATCHED`; the factor vocabulary has no `Water`/`litres` match (honest, recorded) |

