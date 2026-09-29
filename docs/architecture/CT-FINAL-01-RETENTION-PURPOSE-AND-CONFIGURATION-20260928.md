# CT-FINAL-01 — Retention: purpose, configuration and the never-purge set

* **Task:** CT-FINAL-01 (ratified production PO scope), item **retention**
* **Date:** 2026-09-28
* **Repository:** `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`,
  baseline HEAD `dc3d78dc8021bd65978754cf131c38045ff8013d`
* **Nature of this change:** **documentation only.** No retention duration is
  invented here, no deletion logic is changed, no table is aged, no policy is
  re-pointed, and no migration is added.
* **Related frozen decision:** **N3 — retention is configurable and enforced
  server-side** (frozen UX/architecture decision; AGENTS.md #42/#63).

---

## 1. The principle: retention follows PURPOSE, not a headline number

Retention is decided by *why* a record exists, not by a single platform-wide
duration. Two rules follow from that and are enforced by the existing code:

1. **Configurable, server-side, never invented.** The policy values live in
   `system_settings` and are read/written only through the admin surface
   (`/api/v3/settings/retention`, `require_admin()`); enforcement is
   `backend/services/retention.py`. An unset value means **not configured** and
   nothing is purged — the platform never fabricates a duration (AGENTS.md #42).
2. **Never weaken auditability, evidence or regulatory traceability.** Some
   records are outside retention by design; deleting them would destroy the
   product's core capability (provenance, verification, reporting).

### 1.1 What is NOT a justification

* **UK GDPR does not prescribe a number of years.** Article 5(1)(e) (the storage
  limitation principle) requires personal data to be kept *no longer than is
  necessary for the purposes for which it is processed* — it mandates a
  purpose-based justification, not "seven years". Any statement of the form
  *"GDPR requires N years"* is inaccurate and must not be used to justify a
  retention period in CarbonTally.
* **Retention is not the same as deletion capability.** Configuring a duration
  never authorises a blanket delete: every enforcement path is scoped by domain
  and defaults to dry-run (`retention.py` requires an explicit `dry_run=False`).

---

## 2. Purpose-based retention matrix

Legend for **status**: `CONFIGURABLE` — a value can be set by an admin and is
enforced server-side; `INDEFINITE` — outside retention by explicit design;
`PO DECISION REQUIRED` — a number cannot be chosen by an engineer.

| # | Domain (records) | Why it exists (purpose) | Status | Where the value lives / is enforced |
|---|---|---|---|---|
| 1 | `document_processing_queue`, `processing_logs` | Operational state of the processing pipeline — needed while work is in flight | **INDEFINITE** (business records) | explicitly excluded from telemetry retention (`retention.py::_TELEMETRY_EXCLUDED_TABLES`) |
| 2 | Uploaded source documents (`organization_files` + `storage.objects`) | The evidence base: every reported number must trace back to a source document | `CONFIGURABLE` (`document_retention_days`) | `system_settings.document_retention_days`; enforced by `retention.py` for the document domain only |
| 3 | `calculation_snapshots` | Immutable forensic record of how a number was produced (factor, unit, actor, hash) | **INDEFINITE** | excluded from every retention rule |
| 4 | `evidence_line_items` | Source→number evidence chain used in review and assurance | **INDEFINITE** | excluded from every retention rule |
| 5 | `emissions_logs` | The reported emissions facts themselves | **INDEFINITE** (while the reporting obligation applies) | excluded from every retention rule |
| 6 | `audit_trail` (canonical ledger) | Who did what, when — the accountability record | **INDEFINITE** | excluded from every retention rule; append-only at the database (Phase-7 trigger) |
| 7 | Legacy per-domain activity logs (`audit_logs`, `activity_logs`, `document_activity_log`) | Historical activity records, retained-but-immutable (PD-4 retired only the orphan *console*) | **INDEFINITE** (retained) | DB-0001 immutability migration; no table dropped, no writer removed by CT-FINAL-01 |
| 8 | Reports and report versions/artefacts (`report_versions`, `report_version_artifacts`, `report-artifacts` bucket) | The delivered commercial output; must remain reproducible | **INDEFINITE** | `report_*` excluded from every retention rule (`B4-D8`) |
| 9 | Operational telemetry (heartbeats; operational alert notifications + deliveries) | Runtime observability only — no business or evidential value | `CONFIGURABLE` (`operational_telemetry_retention_days`, initial value **90 days**) | `system_settings.operational_telemetry_retention_days` (migration `20260924000000_p8x_x2_…`); enforced by `retention.py` |
| 10 | Backups | Disaster recovery | `CONFIGURABLE` (`backup_retention_days`) | `system_settings.backup_retention_days` (infrastructure cycles) |
| 11 | Platform authentication/security logs (`auth.*`, provider logs) | Security investigation | `PO DECISION REQUIRED` | Supabase/provider-managed; not enforced by CarbonTally code |
| 12 | Messages and message activity | User communication | `PO DECISION REQUIRED` (N1 boundary — not an engineering choice) | — |
| 13 | Onboarding/adoption data (`discovery` requests, verification codes) | Short-lived verification only | `CONFIGURABLE` — a short life is defensible, but the duration is a product choice | — |

---

## 3. Where "≈7 years" is justified — and how

A long retention term (commonly **six to seven years**) is a **commercial and
accounting** position, not a GDPR requirement. Where it is used, the
justification must be stated in these terms:

* **Accounting/bookkeeping records.** UK company law requires accounting records
  to be kept for a minimum period (**three years** for a private company, **six
  years** for a public company — Companies Act 2006 s.388), and **HMRC** expects
  business records to be kept for around **six years** (VAT records: six years).
  Seven years is a *prudent superset* of those minimums, chosen to cover a full
  enquiry window plus the current year — a business choice, not a statutory
  obligation.
* **Assurance / verification cycles.** Where emissions data is independently
  assured, the practical requirement is the assurance period plus a further
  cycle, so the evidence behind a prior year's figures is still available. This
  also yields "≈7 years" as a *practice*, determined by the client's scheme and
  verifier.
* **Regulated scheme rules vary.** Sector schemes (for example UK ETS and
  comparable regimes) set their own participant record-keeping obligations. A
  CarbonTally value must therefore remain **configurable per domain** rather than
  hard-coded, and the applicable scheme rules must be confirmed with the
  regulator and the client's verifier before a value is set.

These are the *justification patterns* to use. They do not select a number: the
number for each domain remains configurable, and any new default requires the
documented purpose above.

---

## 4. What CT-FINAL-01 changed (and did not change)

**Changed:** nothing in retention behaviour. This document exists because the
ratified scope requires the retention position to be *written down* in
purpose-based terms rather than implied by whatever number happens to sit in the
settings row.

**Explicitly unchanged:** the retention columns and their migration history; the
`/api/v3/settings/retention` admin surface; the enforcement module and its
dry-run default; the never-purge exclusion list; and every frozen decision
retention depends on (N3, the evidence/audit invariants).

## 5. Safety guarantees that must survive any future retention work

1. **No blanket deletion.** Enforcement is per-domain and opt-in; "not
   configured" purges nothing.
2. **No retention rule may touch the excluded set** — `document_processing_queue`,
   `processing_logs`, `report_versions`, `report_version_artifacts`,
   `evidence_line_items`, `calculation_snapshots`, `emissions_logs`,
   `audit_trail` (`retention.py::_TELEMETRY_EXCLUDED_TABLES`; assertable via
   `telemetry_excluded_tables()`).
3. **Soft delete only** (`deleted_at`) — retention never hard-deletes.
4. **Dry-run by default**; applying requires an explicit, deliberate caller.
5. **Configuration is admin-only and server-side**; the UI is not a retention
   control.
6. **A duration is never invented** — an unset value is displayed as
   "Not configured", never as a fabricated default.
