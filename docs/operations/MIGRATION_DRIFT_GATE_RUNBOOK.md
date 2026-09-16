# Migration drift gate — runbook (WP-8)

## Why

Production once carried **21 of 68** migrations while application code that needed
the missing objects was deployable. Nothing enforced the relationship between the
repository migration set and the deployed ledger. This gate makes that state
impossible to reach silently.

## Comparator

`backend/tools/migration_drift.py` (read-only). Run from `backend/`:

```bash
# repository-side only (naming/order/duplicates; no ledger, no credentials)
python -m tools.migration_drift --repo-only --out-dir artifacts/migration_drift

# against a ledger snapshot file (CI-friendly, no credentials)
python -m tools.migration_drift --ledger-file ledger.txt

# against a NON-PRODUCTION database (read-only SELECT)
MIGRATION_DRIFT_DATABASE_URL=postgresql://... python -m tools.migration_drift
```

Detections: pending migrations, unexpected ledger entries, ordering anomalies,
duplicate migration versions, naming anomalies, and duplicate ledger rows.

## Release gate

* exit **0** = consistent (or an override was recorded);
* exit **1** = **DRIFT → release blocked**;
* exit **2** = usage/environment error.

CI: `.github/workflows/migration-drift.yml` runs the repository-side check on every
push/PR and, when `MIGRATION_DRIFT_DATABASE_URL` (a **non-production** staging
ledger) is configured as a secret, the full comparison. Evidence is uploaded as an
artefact (90-day retention).

## Emergency override

```bash
CARBONTALLY_MIGRATION_DRIFT_OVERRIDE=<ticket-id> python -m tools.migration_drift
```

The override **never** hides the drift: the report still says `drift: YES`, the
ticket id is written into the JSON+Markdown evidence, and the CLI prints a
warning. Use it only to unblock an unrelated emergency release; the follow-up
migration work remains mandatory.

## Safety

The comparator refuses a DSN containing `prod`, `live`, `qa`, `demo` or `investor`
unless `CARBONTALLY_MIGRATION_DRIFT_ALLOW=non-production` is set. Production
comparison is part of the PO-authorised production gate (D-15/D-17), never a CI
side effect.

## Evidence

`artifacts/migration_drift/migration_drift_<utc>.json|.md` — repository count,
ledger count, latest repository migration, latest applied migration, pending list
(in order), unexpected list, anomalies, override id, ledger source, timestamp.
Attach the artefact to every release.

## Operator workflow

1. Before deploying: run the gate against the target environment's ledger.
2. `drift: YES` → either apply the pending migrations under the authorised window,
   or **block the deployment**.
3. Attach the evidence artefact to the release record.
4. After deployment: re-run to prove parity (`drift: NO`).
