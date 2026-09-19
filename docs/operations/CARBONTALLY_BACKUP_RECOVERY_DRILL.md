# CarbonTally — Backup & Recovery Drill (workstream F, STEP2-070)

```text
STATUS            database recovery VERIFIED locally (disposable targets only)
                  the shipped D1 export artifact VERIFIED as an artifact, but NOT restorable
                  (restore D4 is not implemented; storage objects are not covered)
PRODUCTION        not contacted · not modified · no backup setting changed · nothing deployed
EVIDENCE          tools/backup_recovery_drill.py --source ct_step2_070   (exit 0)
DATE              2026-09-19
```

This document records a **performed** recovery drill, not a claim. It exists because the
project's own operations reference previously recorded `PROVEN RESTORE DRILL — NOT
PERFORMED`, which left recoverability unproven. Everything below was executed against
DISPOSABLE databases on the local PostgreSQL cluster; no persistent environment was involved.

## 1. What was actually run

```text
tools/backup_recovery_drill.py --source ct_step2_070
  source: ct_step2_070   — a DISPOSABLE database carrying the FULL shipped schema
                           (135 public tables built by applying the real migration set)
  target: ct_step2_070_restored_<n> — created by the drill, dropped by the drill
  guard:  the tool refuses any database whose name is not `ct_*`/`carbontally_test`
          or that contains qa/demo/investor/prod/live (see
          tests/unit/tools/test_backup_recovery_drill_guard.py, 9 assertions)
```

## 2. Phase 1 — the project's OWN export capability (`backend/backup`)

The production `BackupService` was run end to end (env-configured, drill-only encryption key,
local object store, `CT_BACKUP_SCHEMAS=public`, `CT_BACKUP_VERIFY_READBACK=1`):

```text
artifact                backups/<id>/carbontally-logical-backup-v1.tar.gz.enc
artifact size           155,456 bytes
ciphertext only         True (no plaintext DDL/COPY material in the stored object)
envelope                version 1 · AES-256-GCM · key_id key-v1
members                 140  (manifest + catalog + ddl + 135 per-table .copy members)
content checksums       138 verified (integrity verified after decryption)
manifest counts         135 tables · 752 rows · 218 policies · 89 triggers · 55 functions
manifest schemas        ['public']   (credential-bearing schemas are refused by policy)
```

What the artifact's `ddl.sql` member can and cannot rebuild (measured from the member text):

```text
CREATE TABLE ✓   PRIMARY KEY ✓   FOREIGN KEY ✓   CREATE INDEX ✓   UNIQUE ✓
POLICY ✓ … but ENABLE ROW LEVEL SECURITY ✗
```

**Conclusion for phase 1:** the export capability produces a genuinely verifiable,
encrypted, checksummed artifact that carries schema metadata and all table data. It is
**not** a recovery path on its own:

* restore (D4) is **not implemented** (`backend/backup/__init__.py` states this explicitly);
* the DDL member is documented in-code as *"best-effort, **informational** … not claimed to
  be a restorable dump"*, and it does not enable RLS, so replaying it would leave the
  database unprotected even if the data members were loaded;
* policies/triggers/functions are inventoried in `catalog.json` (metadata), not as
  executable restore steps.

## 3. Phase 2 — actual recovery with the platform's native tooling

The database was recovered from a physical-format dump (`pg_dump -Fc`) into a **fresh**
disposable database (`pg_restore --no-owner --no-privileges`):

```text
dump size               762,173 bytes
pg_restore return code  0            (no errors)
tables missing          0            (135 of 135 public tables present)
row-count mismatches    0            (every non-empty table, incl. activity_clarifications)
index delta             0            (331 indexes)
constraint delta        0            (507 constraints)
policy delta            0            (218 RLS policies)
RLS-enabled tables      135 → 135    (row-level security survived the restore)
storage.buckets         1  → 1       (bucket CONFIGURATION restored)
```

## 4. Phase 3 — migration / state compatibility

The shipped migration set was applied on top of the reconstruction:

```text
75 migrations · 74 applied · 1 already present · 0 failed
```

⇒ a restored database is at the current migration state and accepts the shipped migrations,
so recovery and schema evolution do not conflict.

## 5. Phase 4 — application compatibility

The real API/repository lifecycle suite was run **against the restored database**
(`INTEGRATION_DATABASE_URL=<restored>`, `tests/integration/test_f039_1_adjudication_lifecycle_runtime.py`):

```text
return code 0   (the application reads, writes and versions adjudications on the reconstruction)
```

## 6. What is still NOT covered (explicit gaps, not assumptions)

```text
1. Restore from the project's own artifact — NOT IMPLEMENTED (D4). The artifact is verified
   as an artifact; it cannot rebuild a database today. Recovery currently relies on the
   platform's native tooling (pg_dump/pg_restore), which the drill proves works.
2. RLS enforcement in the artifact's DDL member — NOT REPRESENTED (measured: no
   `ENABLE ROW LEVEL SECURITY`). A future restore implementation must enable RLS and install
   the policies/triggers/functions from catalog.json, or the restored database would be
   unprotected.
3. Storage OBJECTS (uploaded documents) — NOT COVERED by any mechanism found in this
   repository; only bucket CONFIGURATION is reproducible (verified above, and the bucket is
   created by migration `20260823000000_d32_private_documents_storage.sql`). Object bytes
   live in Supabase Storage and need a provider-side backup/versioning answer.
4. Production backup configuration (Supabase managed backups / point-in-time recovery) —
   NOT VERIFIABLE from this environment. See §7: BLOCKED — ENVIRONMENT/ACCESS REQUIRED,
   not a pass.
5. RPO/RTO and a scheduling mechanism — NOT DEFINED (the ops reference already records
   "no scheduled backups").
```

## 7. Evidence required to close the production half (BLOCKED — ENVIRONMENT/ACCESS)

Nothing here should be read as evidence about production:

```text
a. Supabase project backup/PITR configuration: enabled backup tier, retention window, PITR
   window, and the last successful backup timestamp (Supabase dashboard / Management API).
b. A restore rehearsal in a NON-production Supabase project (or a dedicated branch) from a
   real production backup, with row-count/schema verification equal to §3.
c. The storage-object backup/versioning policy for the documents bucket, plus one sampled
   object restored and byte-compared.
d. The agreed RPO/RTO and the schedule that delivers it (a written operational decision).
e. A named operator and a documented, rehearsed procedure covering (a)–(d).
```

Until (a)–(e) exist, no disaster-recovery readiness claim is made anywhere in this project.

## 8. Reproducing the drill

```bash
# a disposable database carrying the full shipped schema
backend/.venv/bin/python tools/backup_recovery_drill.py --source ct_step2_070

# keep the reconstruction for inspection
backend/.venv/bin/python tools/backup_recovery_drill.py --source ct_step2_070 --keep-target
```

The tool never contacts production, refuses persistent-looking targets, drops only the
database it created, and prints its evidence in four phases.

