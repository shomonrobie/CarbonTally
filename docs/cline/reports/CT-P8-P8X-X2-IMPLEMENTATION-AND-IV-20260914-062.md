# CT-P8-P8X-X2 — OPERATIONAL ALERTING + TELEMETRY RETENTION — IMPLEMENTATION + VERIFICATION (IN PROGRESS)

**Task:** Phase 8-X `X2` (`…045`) — threshold evaluation + alert dispatch (8-X §13 **S1**)
**Authority:** PO decisions of 2026-09-14 — **`PX-6` Option (a)** internal-operations-only alerting (conditions, thresholds, recipients, hourly cooldown, in-product + email, 3 attempts/~15 min, failure recording) · **`PX-7` Option (a)/(d)** configurable server-side `operational_telemetry_retention_days` with initial value **90 days**, detail-only, aggregates indefinite, queue/logs/report/evidence excluded
**Contract:** `CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md`
**Status:** **IMPLEMENTATION COMPLETE — VERIFICATION PARTIALLY EXECUTED — NOT READY FOR CLOSURE**
**Environment:** QA/non-production for the authorised migration + settings; destructive work on disposable clones only (F-046-1) · production untouched

---

## 1. Files changed / added

| File | Change |
|---|---|
| `backend/domain/operational_alerts.py` | **new** — conditions, PO thresholds, hourly `event_key`, SLA not-configured handling |
| `backend/services/operational_alerting.py` | **new** — recipient resolution, in-product dispatch, email + 3-attempt retry, failure recording, audit |
| `backend/data/notifications.py` | +`internal_ops_user_ids` (`can_view_all`), +`email_for_user`, +`record_delivery`, +`prune_operational_alerts_before` |
| `backend/data/document_processing.py` | +`count_sla_breached`, +`prune_operational_metrics_before` |
| `backend/data/queue_settings.py` | +`is_configured` (distinguishes configured from defaulted SLA) |
| `backend/data/settings.py` | `operational_telemetry_retention_days` added to the retention read/write projection |
| `backend/services/retention.py` | telemetry domain + `_TELEMETRY_EXCLUDED_TABLES` + enforcement |
| `backend/workers/automatic_processing.py` | alert evaluation per tick, dispatch in a **background task** + outcome callback |
| `supabase/migrations/20260924000000_p8x_x2_operational_telemetry_retention.sql` | **new** — additive/idempotent column (DEFAULT 90) + guarded `platform_retention` row |
| `backend/tests/unit/domain/test_operational_alerts.py` | **new** — approved values, thresholds, cooldown, honest absence |

## 2. Implementation summary (all seven decisions)

1. **Conditions** — `QUEUE_BACKLOG`, `WORKER_STALE`, `RETRY_EXHAUSTED` live; **provider outage excluded** (`PX-4`).
2. **Thresholds** — `>100` waiting; `>15 min` heartbeat; SLA **only** from the configured setting; retry-exhausted = any job. Values are named PO constants; making them runtime-configurable needs a settings column (flagged, not done).
3. **Recipients** — internal staff (`entity_id IS NULL`, active) whose role permissions grant **`can_view_all`**; no mailbox/list created.
4. **Cooldown/dedup** — deterministic hourly `event_key` (`ops-alert::<CONDITION>::<YYYYMMDDTHH>`), enforced by the **existing** `notifications` unique index through `create_idempotent`.
5. **Delivery** — in-product row + email via the platform's `send_transactional_email`; a `(False, reason)` result is raised as an honest failure, never a fake success.
6. **Delivery failure** — up to **3 attempts** with a configurable delay (default ≈300 s ⇒ ~15 min), then `status='failed'` + `error_message` + attempt count recorded and the loop stops.
7. **`PX-7` retention** — `operational_telemetry_retention_days` (schema DEFAULT 90, row value 90, configurable via the settings service); enforced server-side in `services/retention.py` for telemetry detail only (`dashboard_metrics` metric rows + `ops_alert_%` notifications and deliveries); **aggregates indefinite**; **8-table never-purge list** exposed via `telemetry_excluded_tables()`.

## 3. Verification executed and PASSING

| # | Check | Evidence | Result |
|---|---|---|---|
| V1 | Approved values locked | `test_operational_alerts.py` asserts 100 / 900 s / 3 attempts / hourly key / provider-outage absent | **PASS** |
| V2 | Backlog alerts **only above** 100 (100 ⇒ no alert, 101 ⇒ alert) | unit test | **PASS** |
| V3 | Worker stale only **past** 15 min (900 ⇒ no, 901 ⇒ yes); never-ticked worker alerts and is never "healthy" | unit test | **PASS** |
| V4 | Retry-exhausted fires on any exhausted job; zero ⇒ no alert | unit test | **PASS** |
| V5 | **SLA not configured ⇒ no alert, `evaluable:false`** (no fabricated breach) | unit test + service `_sla_input` requires `is_configured()` | **PASS** |
| V6 | Every condition reported even when not evaluable; healthy inputs raise nothing | unit test | **PASS** |
| V7 | Migration additive + idempotent | clone `ct_x2_20260914`: apply ×2 `rc=0`, **0 errors**, row created with `telemetry=90` | **PASS** |
| V8 | Migration applied to QA, idempotent | QA: apply ×2 `rc=0`, **0 errors**; other retention domains **NULL/untouched**; queue/logs rows preserved | **PASS** |
| V9 | **Configurable without code change** | QA SQL round-trip 90→45→90; repository round-trip **90→120→90** with `document_retention_days` unchanged (`None`) | **PASS** |
| V10 | Repository read path after the change | live QA read: `operational_telemetry_retention_days=90`, all other domains `None` | **PASS** |
| V11 | Module integrity | AST + import of all 6 changed modules and the service/worker | **PASS** |
| V12 | Regression | alert-domain 4/4 · X1 domain 19/19 · ops-auth 18/18 (41 tests) | **PASS** |

## 4. Verification still OUTSTANDING (not yet executed — X2 is not closeable)

| # | Check | Why it is outstanding |
|---|---|---|
| **O1** | End-to-end dispatch on a disposable clone: alert actually created, recipient reached, in-product row + `notification_delivery` rows written | integration test not yet written/run |
| **O2** | **Hourly dedup proven in the database** (two dispatches in one hour ⇒ exactly one notification per recipient; next hour ⇒ a new one) | integration test |
| **O3** | **Recipient limitation proven** (a consultant, a customer and a processing-entity staffer receive nothing; only `can_view_all` internal staff do) | integration test |
| **O4** | **Email retry/failure behaviour proven** (3 attempts, then `status='failed'` with `error_message`; no endless retry) | service unit/integration test with an injected failing sender |
| **O5** | **Audit entry proven** (one `audit_trail` row per dispatch, attributable, no secrets/customer payload) | integration test |
| **O6** | **Retention enforcement proven end-to-end** (telemetry detail past the configured window pruned; aggregates untouched; the 8 excluded tables provably unchanged; dry-run default respected; value change ⇒ different cutoff) | integration test on a clone |
| **O7** | Worker wiring exercised (heartbeat + alert evaluation in one tick; dispatch in a background task; a failing dispatch does not stop processing) | worker-level test |
| **O8** | F-046-1 negative control re-confirmed for the X2 suites | integration harness |

## 5. Findings

| # | Finding | Disposition |
|---|---|---|
| `F-X2-1` | Self-found during implementation: my worker wiring first **awaited** the dispatch, which can sleep ~15 minutes and would have **stalled the claim loop**. The comment said "background task" while the code awaited it. | **Fixed in scope** (dispatch is now an `asyncio.create_task` with a logged done-callback). A verification item (O7) covers it. |
| `F-X2-2` | Self-found: `send_transactional_email` takes `to_email`/`html` and returns `(delivered, reason)`; my first call used the wrong keywords and ignored the failure flag. | **Fixed in scope** — the corrected call raises on `delivered=False`, so an unconfigured provider becomes a **recorded failure**, never a silent fake success. |
| `F-X2-3` | First retention migration attempt failed on the `setting_key` NOT NULL constraint (transaction rolled back correctly); my harness masked the exit code by piping through `grep` (restating `F-4A2-1`). | **Fixed in scope** (insert now mirrors the app's own `platform_retention` key; raw logs inspected). |
| — | No pre-existing or unrelated defect was touched. `F-X1-2`, `F-4A1B-1` and all other bounded items remain untouched as instructed. | — |

## 6. Scoped limitations (declared, not hidden)

* The **SLA signal** for this first release is the existing `processing_queue.sla_breached` flag; other SLA-bearing tables are not yet aggregated into the alert. Documented; extending it is a bounded follow-up, not a silent omission.
* **Thresholds remain code constants** because making them configurable requires a settings column (schema change → separate authorisation). The PO's values are honoured exactly as given.
* **Aggregates**: no aggregate telemetry store exists, so "aggregates retained indefinitely" is satisfied by *not pruning any aggregate*; no aggregate store was invented.
* Email delivery in the **QA** environment may legitimately fail (provider unconfigured) — which is exactly the failure path the PO approved: retry 3×, record, stop.

## 7. Status and next step

**X2 implementation is complete; independent verification is partially executed (V1–V12 PASS) with O1–O8 outstanding.**
**X2 is NOT ready for PO closure and has NOT been self-closed.** No new PO decision is required — the outstanding items are verification work under the existing authorisation.

## 8. Repository state

| Item | Value |
|---|---|
| Branch / HEAD | `main` / `37b19d13723b0b1eabceeade86ce1615a98ab400` |
| Migrations added | `20260924000000_p8x_x2_operational_telemetry_retention.sql` (applied to QA; additive/idempotent) |
| Commits | **none** |
| Clones | `ct_x2_20260914` (disposable) |
| Production / demo | untouched · F-046-1 enforced |


---

## 9. O1–O8 verification — COMPLETED (all PASS)

Suite: `tests/integration/test_operational_alerting_x2_runtime.py` (3 tests) on disposable clone
`ct_x2int_20260914` (fresh `pg_dump --schema-only` of QA + the three migrations), plus
`tests/unit/workers/test_x2_alert_wiring.py` (2 tests) for the worker.

| # | Check | Evidence | Result |
|---|---|---|---|
| **O1** | End-to-end dispatch | real evaluation of a clone with no heartbeat ⇒ `WORKER_STALE` alerted ⇒ notification row created for the approved recipient; `notification_delivery`: `in_product=delivered` **and** `email=sent` (sender invoked) | **PASS** |
| **O2** | **Hourly dedup** | second dispatch in the same hour ⇒ **1** alert notification; dispatch at **+1 h** ⇒ **2** (new `event_key`); enforced by the existing `event_key` unique index | **PASS** |
| **O3** | Recipient limitation | recipient set == internal staff with `can_view_all`; an internal staffer **without** it and an **entity (PE) staffer with** it both received **0** notifications | **PASS** |
| **O4** | Email retry/failure | failing sender ⇒ **exactly 3 attempts**, then `notification_delivery.status='failed'` with the provider error recorded; **no 4th attempt** | **PASS** |
| **O5** | Auditability | `audit_trail` row per dispatch (`action_type='operational_alert_dispatched'`, `performed_by` = acting principal) — **this check found `F-X2-4`** | **PASS** |
| **O6** | Retention | configured value used (`1` day, not hard-coded); **dry-run default leaves rows intact**; real run prunes the expired **ops alert** and expired **metric**, while an ordinary **product notification** and **fresh** telemetry survive; `document_processing_queue` and `processing_logs` counts **unchanged**; excluded-table list asserted; the setting was restored to the approved **90** | **PASS** |
| **O7** | Worker wiring | heartbeat written on every tick; alert dispatch scheduled as a **background task** and completed; a **failing dispatch does not stop processing** (verified with a raising stub) | **PASS** |
| **O8** | F-046-1 negative control | the same suite pointed at `carbontally_qa_phase8` ⇒ `RuntimeError` at `conftest.py:120` (protected-marker refusal); all 3 tests ERRORed **before touching data** | **PASS** |
| — | Regression | X2 domain 4/4 · X1 domain 19/19 · ops-auth 18/18 · X2 integration 3/3 · worker wiring 2/2 | **PASS** |

## 10. Defects found BY this verification (all fixed in scope, then re-verified)

| # | Defect | Why the earlier checks missed it | Fix |
|---|---|---|---|
| **`F-X2-4`** | The audit write called `audit.record(action=…)` but the real contract is `record(AuditEntry)` → `TypeError`, **silently swallowed** by my broad `except` ⇒ **no audit entry at all** | module imports and unit tests passed; only the DB-level O5 assertion could see it | builds a real `AuditEntry`; and the catch now records `audit_error` in the dispatch result instead of hiding the failure |
| **`F-X2-5`** | `data/notifications.py` never imported `dumps_jsonb` ⇒ `NameError` on the first real `record_delivery` call | call-time-only failure (imports were fine) | import added |
| **`F-X2-6`** | `record_delivery` reused `$3` in a value position and inside `CASE WHEN` ⇒ `AmbiguousParameterError (text vs character varying)` | again call-time-only; the project already documents this class of issue | explicit `$3::text` / `$2::text` / `$4::text` casts |
| — | Harness defects (mine, test-only): `audit_trail` has `performed_by`/`action_type` (not `actor`/`action`); `staff_profiles.entity_id` is an FK so a real `processing_entities` row is needed; cleanup must be FK-ordered | — | fixed; a clean clone re-run was used |

These three application defects were **real** and would have shipped a silently un-audited,
silently-failing dispatch path had verification stopped at "imports and unit tests pass".

## 11. Status

**X2 IMPLEMENTATION + INDEPENDENT VERIFICATION COMPLETE — READY FOR PO CLOSURE** (not self-closed).
All seven PO values are implemented and verified; all eight outstanding verification items now
**PASS**. No new PO decision was required at any point.


---

## 12. PO CLOSURE (2026-09-14) — transcription of the PO decision

> **X2 — PO CLOSED / ACCEPTED.** *"I accept the X2 implementation and independent verification
> reported in `CT-P8-P8X-X2-IMPLEMENTATION-AND-IV-20260914-062.md`."*

The PO's decision explicitly accepts: **V1–V12 PASS** · **O1–O8 PASS** · **`F-X2-4`, `F-X2-5`,
`F-X2-6`** as X2-scope defects that were fixed and re-verified · the approved **internal-only
alerting model** · the **approved thresholds and hourly deduplication** · **three-attempt email
failure handling** · **auditability** · **configurable server-side operational telemetry
retention** · the **approved 90-day initial configuration** · the **exclusion of processing
records/logs** from the telemetry retention policy.

* **Status: CLOSED — PO ACCEPTED.**
* This section is a **transcription only**: no closure was self-declared, and nothing beyond the
  PO's decision is inferred.
* Phase 8-X state after this closure: **X1 CLOSED · X2 CLOSED**; stages X4, X5, X7 and the X8
  verification stage remain (see the register reconciliation in
  `CT-P8-FINAL-PROGRAMME-REPORT-20260914-057.md` §14).

