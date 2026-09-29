# CT-FINAL-01 / PD-4 — retirement of the orphan legacy audit console

* **Task:** CT-FINAL-01 (ratified production PO scope), item **PD-4**
* **Date:** 2026-09-28
* **Repository:** `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`,
  baseline HEAD `dc3d78dc8021bd65978754cf131c38045ff8013d`
* **Decision type:** PO-RATIFIED (PD-4 was previously listed as "unratified /
  dead code accumulates" in CT-SCHEMA-03 §20 and CT-AUDIT-01 PD-7.1)
* **Deployment:** **none.** No push, no deploy, no database change, no migration.
* **Reversible:** yes — the artefact is in Git history (see §6).

---

## 1. What PD-4 decided

CT-SCHEMA-03 SCM-007 / CT-AUDIT-01 PD-7.1 recorded three options for the
orphaned legacy audit console:

1. leave it frozen and unregistered (the state at the time);
2. **formally retire it with a documented replacement note**;
3. revive and repoint it at the canonical tables.

The ratified production scope chooses **(2) — retire**. Rationale, unchanged from
the two audits that produced the finding:

* the module is **never imported, never registered and never startup-checked** in
  any reachable commit, and none of its 12 endpoints has any consumer in
  `backend/`, `frontend/src`, `admin/src` or `qa_harness/`;
* one of its handlers (`:404`) queries **`notification_delivery_log`**, a table
  that does **not exist** in the canonical schema (the canonical carrier is
  `notification_delivery`) — so a future re-wire would import a guaranteed
  runtime failure;
* the comprehensive audit capability is **not** lost: it lives in the canonical
  Tier-1 ledger (table `audit_trail` + `backend/domain/audit.py` +
  `backend/data/audit.py` + `backend/infra/audit_logger.py`) and the registered
  read surface, so the orphan console carries no unique capability.

## 2. What was retired

| Item | Detail |
|---|---|
| File removed | `backend/routes/admin/audit_logs.py` |
| Size / length at retirement | 55,504 bytes / 1,431 lines (CRLF) |
| sha256 at retirement | `042e7daefe853d647bca1830fb1a0af42776554243a8ff844554862292cc5e77` |
| Last commit touching it | `077c866fdd9c9cf0d6ca418685b357bea6ed5691` (2026-08-27) |
| Endpoints removed | 12 (all unregistered; zero consumers) |
| Canonical replacement for reads | `/api/v3/ops/reporting/audit` (registered; `backend/api/v3_reporting.py:259`) and `backend/api/admin_audit.py` (`/api/v2/admin/audit`) |
| Canonical replacement for writes | `AuditRepository` (`backend/data/audit.py`) → `public.audit_trail` |

CT-AUDIT-01 established that the module existed in 10 on-disk copies but in
**exactly one semantic version** (all copies byte-identical after EOL
normalisation, hash `1058bf33c3948df3affb91b198902f5f` over the LF form), and that
no copy is a richer implementation than the repository copy being retired here.

## 3. What was explicitly NOT changed (historical records preserved)

PD-4 is a **code** retirement. It is **not** a data-retention decision, and this
change-set deliberately does not touch:

* **no table was dropped, altered, truncated or emptied** — including the legacy
  per-domain activity tables `audit_logs`, `activity_logs`,
  `document_activity_log`, `message_activity_log`, `verification_activity_log`
  and the canonical `audit_trail`;
* **no migration was added, edited or removed** (the canonical chain is
  unchanged; the immutability migration
  `20260912000000_p7_audit_immutability_and_indexes.sql` and its DELETE/UPDATE
  policy drops are untouched);
* **no RLS policy, grant or privilege** was changed (the legacy tables keep
  their append-only posture and their existing SELECT access);
* **no other route, service or repository** was modified — the legacy
  `utils/audit_logger.py` writer used by reachable legacy routes is untouched
  (that surface is a separate item, PD-7.5 / PD-7.6, not PD-4);
* historical audit rows already written remain readable exactly as before.

## 4. Why deletion rather than "keep frozen"

Keeping the artefact in the importable route tree was the exact failure mode the
finding describes: `backend/routes/` is the package that route modules are added
to, so its presence is a standing invitation to register it — and registering it
would immediately produce `PGRST205`/`PGRST200` errors against
`notification_delivery_log` plus 12 endpoints with no authorization review. A
documented retirement with a recorded hash removes that hazard at the source
while keeping the artefact recoverable from Git.

## 5. Verification performed in this change-set

| Claim | How it is verified | Result |
|---|---|---|
| Nothing imports or registers the module | repository-wide grep for `audit_logs.py` / `admin.audit_logs` / `import audit_logs` before deletion | only the module's own header |
| No runtime reference survives the deletion | guard test `backend/tests/unit/api/test_pd4_legacy_audit_retirement.py` | **PASS** |
| The retired name `notification_delivery_log` is referenced nowhere in runtime code | same guard test (scans every non-test module under `backend/`) | **PASS** |
| The canonical audit surfaces still exist and target `audit_trail` | same guard test | **PASS** |
| Legacy audit tables are still defined by the migration chain (records preserved) | same guard test reads the immutability migration | **PASS** |
| The backend still imports and composes | `python -c "import main"` + the unit/API suite | **PASS** |

## 6. Recovery (if the artefact is ever needed for archaeology)

```
cd /home/shomonrobie/ct_93d5cdd
git show 077c866fdd9c9cf0d6ca418685b357bea6ed5691:backend/routes/admin/audit_logs.py > /tmp/audit_logs.py.retired
sha256sum /tmp/audit_logs.py.retired   # expect 042e7daefe853d647bca1830fb1a0af42776554243a8ff844554862292cc5e77
```

Recovery is for **reading**, not for re-registration: any revival must first be
repointed onto `notification_delivery` and reviewed under the authorization and
audit-model decisions (PD-7.2, PD-7.5).
