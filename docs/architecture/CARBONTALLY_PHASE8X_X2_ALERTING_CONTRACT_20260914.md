# CarbonTally Phase 8-X X2 — BOUNDED ALERTING IMPLEMENTATION CONTRACT (from `PX-6` + `PX-7`)

**Task:** Phase 8-X `X2` (`…045`) — threshold evaluation + alert dispatch (8-X §13 **S1**; discovery doc §"Stage X6 — Thresholds & alerting")
**Authority:** PO decisions of 2026-09-14 — **`PX-6` Option (a)** (internal CarbonTally operations alerting **only**; *"no invented thresholds; no invented recipient lists"*) and **`PX-7` Option (d)** (detailed operational telemetry **90 days**, aggregates **indefinitely**; server-side; must not weaken report/evidence retention). X2 is authorised **only after** this contract.
**Date:** 2026-09-14 · **Type:** CONTRACT (no implementation — see §7 STOP)
**Status:** **CONTRACT PRODUCED — OPEN PO CHOICES — IMPLEMENTATION BLOCKED AT THE `PX-6` GATE**
**Environment:** QA/non-production only · production unauthorised (G0-D) · no provider access (`PX-4` deferred)

---

## 1. Scope

| In scope | Out of scope (per the PO's X2 boundary) |
|---|---|
| Evaluating **approved** pipeline failure conditions | customer/consultant-facing alerts |
| Dispatching alerts to **internal CarbonTally operations/admin personnel** | runtime/deployment introspection |
| Reusing the **existing** notification + settings infrastructure | provider-console access |
| **`PX-7`** retention for operational telemetry/alerting data | production access/modification · S6 · X4–X7 · S8 · RLS 3–5 · `F-X1-2` · **OHD** |

**Stop conditions carried from 8-X (binding):** *"if alerting requires a new messaging framework → stop"*, and the project rule that a **schema change requires separate authorisation**.

## 2. Reuse map (verified present — no invented infrastructure)

| Need | Existing object | Verified state |
|---|---|---|
| Enablement + recipients configuration | `system_settings.sla_breach_alert_enabled`, `system_settings.sla_breach_alert_recipients` | **columns exist — the table has 0 rows (nothing configured)** |
| SLA thresholds | `system_settings.sla_default_hours`, `system_settings.sla_escalation_hours`, `sla_definitions.sla_hours` | columns/table exist — **`sla_definitions` has 0 rows** |
| Alert record + **deduplication** | `notifications` (`event_key`, `recipient_type`, `recipient_id`, `notification_type`, `priority`, `metadata`, `actor_domain`) | exists — **0 rows**; `event_key` is the prescribed idempotency key |
| Delivery + failure record | `notification_delivery` (`channel`, `status`, `sent_at`, `delivered_at`, `error_message`) | exists — **0 rows** |
| Dispatch pattern to copy | `backend/services/consultant_lifecycle.py` — the only existing `notification_delivery` writer | present |
| Audit | canonical append-only `audit_trail` | in use across Phase 8 |
| Pipeline signals to evaluate | X1's `domain/operational_health.py` + `document_processing_queue` | **X1 CLOSED** — available now |

**No new messaging framework is required** → the 8-X stop condition does **not** fire.

## 3. The seven elements `PX-6` requires — determination

| # | Element | Determination | Status |
|---|---|---|---|
| 1 | **Alert conditions** (which failures alert) | 8-X §13 **S1** names the categories: **queue backlog**, **SLA breach**, **repeated failures**, (provider outage). **Provider outage is excluded** — it needs provider access, which `PX-4` declined. Which of the remaining three are live, and in what combination, is **stated nowhere**. | **OPEN → `X2-D1`** |
| 2 | **Thresholds** (the numbers) | Every candidate source is **empty**: `system_settings` 0 rows, `sla_definitions` 0 rows. `PX-6` says *"no invented thresholds"* — no number may be chosen by me. | **OPEN → `X2-D2`** |
| 3 | **Recipients** | The **mechanism** is `system_settings.sla_breach_alert_recipients` (a configured list) — but it is **empty**, and `PX-6` says *"no invented recipient lists"*. Whether it is a stored address list, a role/mailbox, or "internal staff holding a given permission" is a business choice. | **OPEN → `X2-D3`** |
| 4 | **Deduplication / cooldown** | **Mechanism determined**: `notifications.event_key` idempotency (no duplicate alert) plus *"rate-limited dispatch"* / *"no alert storms"* (8-X Stage X6 verification). The **cooldown window** — how long before the same condition may alert again — is a number and is **configured nowhere**. | **SPLIT: mechanism ✔ DETERMINED · window OPEN → `X2-D4`** |
| 5 | **Delivery mechanism** | **Determined**: reuse `notifications` + `notification_delivery` (8-X: *"reuse `notifications`/`notification_delivery`"*, *"reuse `system_settings` keys"*). No new framework. The **channel(s)** — in-app only, email, or both — is part of `PX-6`'s *"channels"* and is **not stated**. | **SPLIT: transport ✔ DETERMINED · channels OPEN → `X2-D5`** |
| 6 | **Failure handling** | **Partly determined**: `notification_delivery.status` + `error_message` record failures (existing pattern). Whether a failed delivery is **retried** — and how often/for how long — is **not determined**. | **SPLIT: recording ✔ DETERMINED · retry policy OPEN → `X2-D6`** |
| 7 | **Audit record** | **Determined by existing convention**: mutation-class entries through the canonical append-only `audit_trail`, recording alert identity, condition, threshold, resolved recipients and delivery outcome. No new audit mechanism. | **DETERMINED ✔** |

**Net position: five of the seven required elements contain a value that exists in no authoritative artefact.** Under `PX-6`'s own instruction — *"If any of those require a new business/PO choice not already determined by PX-6, STOP and return that decision to me rather than inventing it"* — **X2 implementation is stopped at this gate** (§7).


## 4. `PX-7` retention — design (determined; implementation-gated)

| Rule (`PX-7` Option d) | Design consequence |
|---|---|
| Detailed operational telemetry retained **90 days** | Applies to **telemetry/alerting detail**: heartbeat/metric rows, alert `notifications` and their `notification_delivery` rows, and any future operational telemetry added by X2 |
| Aggregates retained **indefinitely** | Applies to derived aggregate telemetry only. **No aggregate store exists today** — creating one would be a **new table = schema change = separate authorisation** (§5) |
| **Server-side enforcement, never a UI convention** | Enforced by the server/retention mechanism (the existing retention-configuration path), never by presentation logic |
| **Must not weaken report/evidence retention** | `B4-D8` (reports retained **indefinitely**, no deletion path) is untouched. **Excluded from `PX-7`:** `report_versions`, `report_version_artifacts`, `disclosure_*`, `evidence_line_items`, `calculation_snapshots`, `emissions_logs`, `audit_trail` |
| **Data-safety boundary (flagged, not decided by me)** | The processing **job record** (`document_processing_queue`) and `processing_logs` are operational **work** records, not telemetry — deleting them at 90 days would destroy the processing history the product depends on. I have **excluded them** and flag the exclusion for confirmation → **`X2-D7`** (scope confirmation, not a new business rule) |

## 5. Implementation gates carried forward

1. **`PX-6` open choices** (§3) — **blocking**.
2. **Any schema change** (e.g. a config column for a backlog threshold, or an aggregates table) requires **separate PO authorisation**, exactly as `PX-5` required for the X1 heartbeat.
3. **Provider access** remains declined (`PX-4`) — no provider-outage alerting.
4. **No new messaging framework** — the 8-X stop condition is not triggered.

## 6. Verification expectations (for when the gate clears)

* Threshold fixtures per approved condition: each condition fires exactly at its approved value and **not before**.
* **Duplicate suppression** via `event_key`: a second identical evaluation creates **no** second alert.
* **No alert storms** — rate-limited dispatch proven by test.
* **Recipients exactly as approved** — nobody outside the approved set receives an alert.
* **Failure path** — a failed delivery is recorded with `error_message` and never corrupts the alert record.
* **Audit** — every dispatch is attributable (condition, threshold, recipients, outcome); no secret or customer payload in an alert body.
* **Retention** — 90-day detail expiry enforced **server-side**; aggregates unaffected; report/evidence retention provably unchanged.
* **Authorization** — internal-staff scope only; no consultant or customer can receive or read operational alerts.
* **F-046-1** — any destructive test on a disposable clone only.

## 7. STOP — what blocks X2, and what does not

**Blocking (new PO choices required under `PX-6`):** `X2-D1` conditions · `X2-D2` thresholds · `X2-D3` recipients · `X2-D4` cooldown window · `X2-D5` channels · `X2-D6` retry policy.

**Not blocking:** infrastructure reuse (§2), the dedup mechanism (`event_key`), the audit path, the transport, and the whole `PX-7` retention design (§4).

**Consequence:** X2 **cannot be implemented** until those values are supplied. I have **not** invented a threshold, recipient list, channel, cooldown or retry policy, and **no implementation has begun**.

