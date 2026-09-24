# CT-PO-P12-STEP2-RESET-REPROVISION-PROCEDURE-20260924

**Reference:** `CT-PO-P12-STEP2-RESET-REPROVISION-PROCEDURE-20260924`
**Date:** 2026-09-24
**Governing workplan:** STEP 2 — repeatable `reset → migrations → seed → verify → reproduce`
**Status:** STEP-2 DELIVERABLE — operational procedure (verified once end-to-end in this session)
**Production deployment:** **NOT AUTHORIZED**

---

## 1. Target guard (non-negotiable)

```text
TARGET DATABASE : carbontally_demo_local
TARGET CONTAINER: supabase_db_carbon_ledger + carbontally_demo_lab_{postgrest,storage,gateway}
TARGET ENV      : local developer machine (127.0.0.1) only
FORBIDDEN       : postgres, carbontally_qa_phase8, carbontally_test, production, Render, hosted Supabase
```

Guards already enforced by the tooling (reuse — do not bypass):

- `lab.LAB_DB == "carbontally_demo_local"`; `reset_demo_lab.sh` drops **only** that database;
- `t3_scenarios.assert_lab_database()` hard-fails unless `current_database()` is the lab;
- `seed_factors.py` refuses any target whose name is not exactly `carbontally_demo_local`;
- the integration harness refuses `qa`/`demo`/`investor`/`prod`/`live` targets (F-046-1).

## 2. Procedure

```bash
cd /home/shomonrobie/ct_93d5cdd
# lab-local psql credentials only — the documented default in
# tools/demo_lab/backend.env.example (never a production credential)
export PGPASSWORD="$(grep -oP '(?<=:)[^:@]+(?=@)' <<< "$(grep '^DATABASE_URL' \
  $HOME/ct_local_env/demo_lab/backend.env | cut -d= -f2-)")"

# 0. capture a pre-reset manifest (counts, schema, identity, release, generator)
python3 <pre-reset manifest script>          # see the Environment Provenance Record

# 1. RESET (lab DB + lab containers + lab auth users only)
./tools/demo_lab/reset_demo_lab.sh
#    → keeps <state>/credentials.local.json and the corpus; use --purge-state to rotate

# 2. REPROVISION — schema + identities + env file + backend + verify + factors
PYTHON=$PWD/backend/.venv/bin/python ./tools/demo_lab/run_demo_lab.sh --backend --factors

# 2b. ORDERING FIX (harness defect D-2-03 — REQUIRED, else every document maps no_match):
#     the worker builds its factor index at startup, so restart the backend AFTER the factors load
pkill -f "uvicorn main:app --host 127.0.0.1 --port 8070"
cd backend && set -a && . $HOME/ct_local_env/demo_lab/backend.env && set +a
nohup .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8070 > $HOME/ct_local_env/demo_lab/backend.log 2>&1 &
cd .. && curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8070/health   # expect 200

# 3. PDF corpus seed (real upload → real pipeline)
./backend/.venv/bin/python tools/demo_lab/t3_scenarios.py seed --wait 180

# 4. Tabular seed (EV-01 unlock; MUST send Content-Type: text/csv — defect D-2-04)
./backend/.venv/bin/python <tabular seeder>            # posts to /api/v3/uploads + …/enqueue

# 5. Operational/messaging/report/master-data/Insight seeding via the real API
./backend/.venv/bin/python <story-b seeder>

# 6. VERIFY
./backend/.venv/bin/python tools/demo_lab/verify.py     # 13/13 contexts, 30/30 probes, 18/18 isolation
python3 <counts script>                                 # expected-vs-actual counts

# 7. REPRODUCE-ABILITY CHECK (repeat steps 1–6 and compare counts)
```

## 3. Observed timings and results (this session)

| Step | Result |
| --- | --- |
| Reset | lab auth users removed (13), 3 lab containers removed, lab DB dropped; **protected DBs unchanged** (`postgres` 975 orgs, `carbontally_test` 717 users, `qa_phase8` 25 orgs) |
| Schema build | 81 migrations, **0 errors**, 141 public tables, 6 Insight tables, 4 D32 policies, 2 private buckets |
| Provision | 13 actors, 4 orgs, 8 members, 3 staff profiles, 1 consultant firm, 2 client grants, 1 PE |
| Backend | `/health` 200; worker started |
| Verify | 13/13, 30/30, 18/18, `known_product_defects: []` |
| Factors | 7,029 + 20 = **7,049**, all linked, 2 active batches |
| PDF seed | 11 uploads → 10 blocked with real reasons, 0 erroneous successes |
| Tabular seed | 2 calculations + 2 evidence lines + populated line links |
| Story B / messaging / reports / master data / Insight | all HTTP 200/201 as recorded in the Frozen Seed Manifest |

## 4. Required harness fixes (already applied to `tools/demo_lab/`)

| ID | Issue | Fix |
| --- | --- | --- |
| D-2-02 | storage substrate before migrations; `auth` bootstrap after them | re-sequenced within `stack.py` (`auth` → migrations → storage → grants → containers) |
| D-2-06 | `auth.users` not created on a fresh DB | `_clone_auth_schema_structure()` (`pg_dump --schema-only --schema=auth`, structure only) |
| D-2-05 | JWKS fallback path 404 | corrected to `/auth/v1/.well-known/jwks.json` |
| D-2-03 | backend started before factors → empty worker factor index | restart the backend after the factor load (step 2b) |
| D-2-04 | multipart hardcodes `application/pdf` | tabular seeder sends `text/csv` |

## 5. Known limitations of this procedure

1. **Repeatability is demonstrated once**, not twice, in this session: the counts in
   step 7 were captured after a single `reset → reprovision → seed → verify` cycle.
   A second full cycle is required to claim repeatability (Step-2 exit criterion
   remains open).
2. The step-2b backend restart is currently **manual**; it should be folded into
   `run_demo_lab.sh` (tooling change, not yet made).
3. `sync-corpus --source` must point at the pinned checkout
   (`/home/shomonrobie/carbon_tally_synthetic_documents`); `/tmp/extgen` does not exist.
4. Provisioning a **second processing entity** and an internal staff role granting
   `can_manage_staff` is required for the S-4 and support-messaging beats.
