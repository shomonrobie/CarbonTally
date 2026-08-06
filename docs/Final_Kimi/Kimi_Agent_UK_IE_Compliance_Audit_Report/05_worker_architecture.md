# CarbonTally v1.0 — Background Worker Architecture (RC2-Frozen Schema)

Architecture specification only. No SQL, no code, no migrations, no seed data. All names use the post-RC1/RC2 vocabulary (`emission_factors`, `emission_factor_used`, `default_factor_year`, `file_checksum`, `user_invitations`). Queue tables are frozen: `document_processing_queue`, `processing_queue`, `report_generation_queue`, `manual_review_queue`; supporting logs `processing_logs`, `processing_audit_trail`; reference `queue_settings`, `sla_definitions`, `system_settings`. Workers connect with the **service role only** (RLS bypass) and must filter `organization_id` in code for every tenant read/write. Claiming uses `FOR UPDATE SKIP LOCKED`-style claim semantics against the frozen claim partial indexes (`dpq_claim_idx`, `processing_queue_claim_idx`, `report_generation_queue_claim_idx`) — the claim status subsets must match those index predicates exactly.

## 1. Worker Roster

### 1.1 File Virus Scanner

| Aspect | Design |
|---|---|
| Purpose | Scan every uploaded object while it is still in `temp-uploads`, before the complete-move into `documents` and before any downstream processing touches it; infected or unscannable files are retained in the `quarantine/` prefix for investigation (never deleted on detect, never moved into `documents`) |
| Trigger / queue source | First claim on `document_processing_queue` where `status = 'pending'` and `processing_type = 'virus_scan'` (enqueue written by `/documents/uploads/{id}/complete`; the object remains in `temp-uploads` until a clean verdict); claim predicate matches `dpq_claim_idx` |
| Input | `customer_document_id`, `file_url` (short-lived signed URL minted server-side), `file_checksum`, `file_size_bytes`, `organization_id` |
| Output (tables written) | `document_processing_queue` (status → `processing` for OCR stage on clean; → `failed` with `metadata.scan_result` on infection); `customer_documents.status` (`uploaded→pending→processing` / `failed`); `processing_logs` row (step=`virus_scan`, `duration_ms`, `details`); `processing_audit_trail` row. On clean verdict the object is moved from `temp-uploads` into `documents`; on infection it is retained in the `quarantine/` prefix and a `notifications` row is sent to the uploader |
| Failure modes | Scanner engine unreachable; file unreadable/corrupt; signed URL expiry mid-scan; oversize archive bomb |
| Retry policy | Standard backoff (§2), max 5 attempts; corrupt/unreadable is non-retryable → `failed` + manual review notification |
| Idempotency key | `virus_scan:{customer_document_id}:{file_checksum}` — re-scan of identical bytes short-circuits to the recorded verdict |

### 1.2 OCR Worker

| Aspect | Design |
|---|---|
| Purpose | Extract raw text and layout from clean PDFs/images to feed AI extraction |
| Trigger / queue source | `document_processing_queue` claim, `status = 'processing'`, `processing_type = 'ocr'` (promoted by Virus Scanner on clean verdict) |
| Input | `file_url` (signed), `file_type`, `page_count`, `organization_id` |
| Output | `document_processing_queue.metadata.ocr_text_ref` (large text stored in Storage, not jsonb); `page_count` backfill; `processing_logs` (step=`ocr`); status unchanged (`processing`) — hands off to AI Extraction by writing `processing_type='ai_extraction'`; `processing_audit_trail` |
| Failure modes | OCR engine timeout; unsupported encoding; scanned-image quality too low (low text yield → route straight to `manual_review` with `manual_requested_at` set) |
| Retry policy | Standard backoff, max 4; low-yield is deterministic → no retry, escalate to manual path |
| Idempotency key | `ocr:{customer_document_id}:{file_checksum}` — completed OCR output reference wins on replay |

### 1.3 AI Extraction Worker

| Aspect | Design |
|---|---|
| Purpose | Structured extraction (supplier, dates, quantities, document type) and mapping hints (facility/asset/supplier/document-type) from OCR text |
| Trigger / queue source | `document_processing_queue` claim, `status = 'processing'`, `processing_type = 'ai_extraction'` |
| Input | OCR text reference, org context (facility/supplier candidate lists), `document_type_code`, `customer_subscriptions.ai_extraction_limit/used` (plan gate) |
| Output | `document_processing_queue`: `ai_extraction_result`, `ai_confidence_score` (0–100, K3c), `ai_extraction_method`, `ai_extracted_at`, `ai_processing_time_ms`, `ai_mapped_facility_id/asset_id/supplier_id`, `ai_mapping_confidence`, `ai_mapped_document_type_code`; status → `ai_extracted` (confidence ≥ threshold from `queue_settings`) or `manual_review`; `customer_documents.extracted_data`, `confidence_score`, status → `processed` / `manual_review`; `customer_subscriptions.ai_extraction_used` increment; `processing_logs`, `processing_audit_trail` |
| Failure modes | Model API timeout/5xx; token-limit truncation; confidence below threshold (business route, not error → `manual_review`); plan limit exhausted → `manual_review` with `customer_notified_at` |
| Retry policy | Standard backoff, max 5 for transport errors; truncation/confidence outcomes are terminal business routes, not retries |
| Idempotency key | `ai_extract:{queue_row_id}:{ocr_output_hash}` — replay returns recorded `ai_extraction_result` without a second model call or usage increment |

### 1.4 Image Processing Worker

| Aspect | Design |
|---|---|
| Purpose | Normalise raster uploads (rotation, deskew, resolution normalisation) and generate page thumbnails/previews for the review UI |
| Trigger / queue source | `document_processing_queue` claim, `status = 'processing'`, `processing_type = 'image_preprocess'` (set by Virus Scanner for image MIME types; runs before OCR) |
| Input | `file_url` (signed), `file_type`, `organization_id` |
| Output | Normalised object + thumbnails in Storage; `document_processing_queue.metadata.preview_urls`; `processing_logs` (step=`image_preprocess`); `processing_type` advanced to `ocr` |
| Failure modes | Corrupt image (non-retryable → `failed`); transformation library error (retryable) |
| Retry policy | Standard backoff, max 3 |
| Idempotency key | `img:{customer_document_id}:{file_checksum}` |

### 1.5 Carbon Calculation Worker

| Aspect | Design |
|---|---|
| Purpose | Convert confirmed extracted quantities into emissions using `emission_factors` matched on `(reporting_year, activity_type, country)` (K5 natural key); write the ledger row |
| Trigger / queue source | `document_processing_queue` claim when status reaches `customer_review`→approval event, or `processing_queue` claim (`queue_status='pending'`, predicate matches `processing_queue_claim_idx`) for batch/recalculation jobs; also invoked after manual-extraction QC approval |
| Input | `extracted_data`/`mapped_data` (AI or manual), org `country` and `default_factor_year`, facility/supplier mapping, billing period |
| Output | `emissions_logs` row (`organization_id, asset_id, emission_factor_id, start_date, end_date, raw_quantity, unit, scope, calculated_kg_co2e, customer_document_id, supplier_id, data_source, confidence_score, created_by_user_id`); `document_processing_queue.calculated_emissions_kg_co2e`, `emission_factor_used`, `emission_calculation_method`; `customer_documents.calculated_emissions_kg_co2e`; correction rows are positive quantities with a type/flag in `metadata` (K3: no negatives); `processing_logs` |
| Failure modes | No matching factor for (year, activity, country) — non-retryable → document to `manual_review` with `customer_notes` reason; ambiguous unit (free-text `unit`) → manual review; numeric overflow (retry-exempt, data fix required) |
| Retry policy | Standard backoff, max 3 for transient DB errors; factor-miss is terminal routing, not retry |
| Idempotency key | `calc:{customer_document_id}:{emission_factor_id}:{billing_period_start}` — duplicate suppression via existing `emissions_logs` lookup before insert; corrections create new rows deliberately |

### 1.6 Report Generation Worker

| Aspect | Design |
|---|---|
| Purpose | Assemble report content (incl. SECR) from `emissions_logs` aggregates + templates; drive `report_generation_queue` progress |
| Trigger / queue source | `report_generation_queue` claim, `status='pending'` (predicate matches `report_generation_queue_claim_idx`) |
| Input | Queue row: `report_type, reporting_year, template_id, data_sources, user_edits`; org row (`secr_enabled`, `reporting_standard`, `default_factor_year`); `organization_metadata` for intensity denominators |
| Output | `report_generation_queue`: `generated_content`, `progress_percentage`, `current_step`, `ai_model_used, ai_tokens_used, ai_cost, ai_processing_time_ms`, status → `generating`…`content_ready` (vocabulary per app constants; `error_log` on failure); `ai_content_history` provenance rows; then hands to PDF Generation Worker (§1.7); `processing_logs` |
| Failure modes | Empty data set for year → terminal with `error_log` + user notification; model timeout (retryable); template missing (terminal, `failed`) |
| Retry policy | Standard backoff, max 4 |
| Idempotency key | `report_gen:{queue_row_id}:{content_input_hash}` — re-run after edits uses new hash by design |

### 1.7 PDF Generation Worker

| Aspect | Design |
|---|---|
| Purpose | Render final report artefacts (and document previews where required) to PDF in Storage |
| Trigger / queue source | `report_generation_queue` row at `content_ready`; chained by Report Generation Worker (same queue table, `current_step='pdf_render'`) |
| Input | `generated_content`, `user_edits`, template, branding (consultant co-branding from `consultant_profiles` when client report) |
| Output | PDF object in private bucket; `report_generation_queue.final_report_url, final_report_file_name, final_report_size_bytes`, status → `completed`, `completed_at`, `progress_percentage=100`; `report_versions` snapshot (`is_current` flip); `export_history` row when user-requested export; `notifications` to requester |
| Failure modes | Renderer crash/OOM on very large reports (split-render retry); Storage write failure (retryable) |
| Retry policy | Standard backoff, max 3 |
| Idempotency key | `pdf:{queue_row_id}:{content_hash}` — same hash reuses existing artefact |

### 1.8 Notification Worker

| Aspect | Design |
|---|---|
| Purpose | Fan out domain events to in-app notifications and delivery channels; honour templates |
| Trigger / queue source | `processing_queue` rows with `document_type='notification'` written by API service layer and other workers (`queue_status='pending'`, claim predicate matches `processing_queue_claim_idx`); Supabase Realtime broadcast on `notifications` insert |
| Input | Event payload in `metadata`: `recipient_type, recipient_id, notification_type, title, message, priority, link` |
| Output | `notifications` rows; `notification_delivery` rows per channel (`channel, status, sent_at, delivered_at, error_message`); Realtime publish; escalations update `manual_review_queue.customer_notified_at` where applicable |
| Failure modes | Realtime publish failure (degrade silently — row is source of truth); template missing → fallback plain template, `error_message` recorded |
| Retry policy | Standard backoff, max 4 |
| Idempotency key | `notif:{event_type}:{resource_id}:{recipient_id}` — dedup against existing `notifications` row |

### 1.9 Email Worker

| Aspect | Design |
|---|---|
| Purpose | Transactional email: invitations (`user_invitations`), notifications with email channel, report-ready, support replies, staff alerts (SLA breach recipients from `system_settings.sla_breach_alert_recipients`) |
| Trigger / queue source | `processing_queue` rows `document_type='email'` (`queue_status='pending'`) written by API/workers |
| Input | Template reference (`email_templates` / `notification_templates`), recipient, variables, `organization_id` |
| Output | Provider send; `email_logs` row (`email, type, status, error_message`); `notification_delivery` update when email-channel |
| Failure modes | Provider 4xx (invalid address — terminal, record `email_logs.status='failed'`, no retry); provider 5xx/rate-limit (retryable with `Retry-After` honoured); template missing (terminal) |
| Retry policy | Standard backoff, max 5; provider-imposed delay overrides computed backoff |
| Idempotency key | `email:{type}:{recipient}:{template}:{resource_id}` |

### 1.10 Cleanup Worker

| Aspect | Design |
|---|---|
| Purpose | Scheduled hygiene: retention enforcement, expired artefacts, stuck-job reaper, erasure support |
| Trigger / queue source | Cron schedule (Supabase scheduled functions invoking the worker entrypoint); no queue table — tasks derive from `system_settings` retention keys (`audit_log_retention_days, data_retention_days, document_retention_days`) |
| Input | `system_settings` retention values; `export_history.expires_at`; signed-URL expiry horizon; stuck-queue thresholds (`queue_settings`) |
| Output | DELETEs of expired `export_history` files + Storage objects; retention DELETEs on append-only logs per policy (no audit-archive table — T2 deferred); reaper: queue rows past claim timeout returned to claimable status with attempt counter incremented, or moved to dead-letter handling (§3); `password_reset_tokens` / `user_invitations` expiry sweeps (status → expired); `processing_logs` summary rows |
| Failure modes | Partial delete failure (continue, log, next run completes); Storage/DB inconsistency (log for ops) |
| Retry policy | Run-level: next scheduled run is the retry; individual item failures logged, max 3 consecutive item failures before alerting staff |
| Idempotency key | `cleanup:{job_class}:{run_date}` — sweeps are naturally idempotent (predicates match only eligible rows) |

## 2. Retry Strategy (cross-cutting)

| Parameter | Value |
|---|---|
| Base schedule | Exponential: `delay_n = base × 2^n`, base 30 s → 30 s, 1 m, 2 m, 4 m, 8 m … |
| Jitter | Full jitter: actual delay uniform in `[0, computed]`; prevents thundering-herd against provider rate limits |
| Max attempts | Per worker table above (3–5); attempt counter carried in queue-row `metadata.attempts` (no new column) |
| Error classification | Transport/5xx/timeout → retryable; validation/data-shape/factor-miss/plan-limit → terminal business routing (manual review or `failed`), never retried |
| Provider hints | `Retry-After` and provider rate-limit responses override computed delay |
| Claim timeout | A claimed row not completed within its lease (per `queue_settings`) is reclaimed by the Cleanup Worker reaper and counts as an attempt |
| Backoff authority | Delays read from `queue_settings` (`setting_value` jsonb) so ops can tune without deploy; defaults above |

## 3. Dead Letter Queue (no new tables)

| Item | Design |
|---|---|
| Where failures land | The frozen status vocabulary is the DLQ: `document_processing_queue.status='failed'` for the document pipeline; `processing_queue.queue_status='on_hold'` (with `notes` recording terminal error) for notification/email/generic jobs; `report_generation_queue.status='failed'` + `error_log` for reports |
| Triage surface | Dead-lettered document rows surface in `manual_review_queue` (status pending, `priority` raised, `customer_notes`/`staff_notes` carrying the failure) — this is the staff workbench, not a new table |
| Re-drive | Staff action via Admin endpoints (§13 of 04_api_design) resets the row to its re-entry status (`pending`/`processing`); attempt counter resets only on manual re-drive |
| Alerting | On dead-letter, Notification Worker emits staff notification; `sla_breached` set where `sla_deadline` passed; `sla_compliance` reporting consumes these flags |
| Audit | Every dead-letter transition writes `processing_audit_trail` (`action='dead_letter'`, `previous_value`/`new_value`, `notes`) |

## 4. Priority Queue (within frozen schema)

| Queue table | Priority mechanism available today | Ordering strategy |
|---|---|---|
| `processing_queue` | `priority` (int), `priority_score` (int), `sla_deadline`, `sla_breached` — present in dump | Claim order: `sla_breached DESC, priority_score DESC, sla_deadline ASC NULLS LAST, created_at ASC` |
| `manual_review_queue` | `priority`, `priority_score`, `sla_deadline`, `escalation_level` — present | Same ordering; `escalation_level` increments per SLA breach per `sla_definitions.escalation_hours` |
| `document_processing_queue` | **No priority columns** — verified against dump | Ordering without schema change: `created_at ASC` within `batch_id`/`batch_sequence`; urgency expressed by routing (e.g. `processing_type` stage, `qc_required`) and by `queue_settings` weights applied at claim time in worker code; per-document SLA tracked on the linked `processing_queue`/`manual_review_queue` rows, which do carry priority |
| `report_generation_queue` | **No priority columns** | `created_at ASC`; concurrency cap per organisation prevents one tenant starving others (fair-share scheduling in worker claim loop) |
| SLA source | `sla_definitions(document_type, priority_level, sla_hours, escalation_hours)` + `system_settings.sla_default_hours`; business-hours aware via `business_hours` | `sla_deadline` stamped at enqueue by the API service layer |

## 5. Worker Scaling

| Item | Design |
|---|---|
| Topology | Horizontally scaled stateless worker processes (container per worker class), N replicas each; SKIP-LOCKED claiming makes replicas mutually safe — no leader election |
| Concurrency per class (launch defaults, tunable via `queue_settings`) | Virus Scanner 8; Image Processing 4; OCR 4; AI Extraction 6 (model-provider rate-limit bound); Carbon Calculation 8 (DB-bound, fast); Report Generation 2 (heavy); PDF Generation 2 (memory-heavy); Notification 8; Email 4 (provider rate-limit bound); Cleanup 1 (single-run lock) |
| DB connection discipline | Service-role connection per worker with small pool (≤5 connections/replica); no long transactions — claim, process, commit; aggregate pool ceiling kept well under Supabase connection limit; Realtime uses its own channel, never the worker pool |
| Throughput assumptions (year-one) | Peak 200 documents/hour platform-wide; AI extraction ~20–60 s/doc; reports ≤ 20 concurrent generations; email bursts (invites, report-ready) ≤ 500/hour — defaults above give ≥3× headroom |
| Backpressure | Workers stop claiming when provider rate-limits or pool saturation is detected; queue depth and `sla_breached` counts drive autoscaling signals and the `dashboard_metrics`/`staff_workload` ops views |
| Secrets | API keys (model, email, scanner) in environment/secret store only; never in `system_settings` rows or logs |

## 6. Pipeline Choreography: Upload → Confirmed

End-to-end state flow mapped **exactly** to the frozen status columns. `document_processing_queue.status ∈ {pending, processing, ai_extracted, manual_review, manual_extraction, qc, customer_review, approved, rejected, completed, failed}`; `customer_documents.status ∈ {uploaded, pending, processing, processed, manual_review, verified, approved, rejected, failed}`; `processing_queue.queue_status ∈ {pending, assigned, in_progress, on_hold, completed, cancelled}`.

| Stage | Actor | `customer_documents.status` | `document_processing_queue.status` | `processing_queue.queue_status` | Side effects |
|---|---|---|---|---|---|
| Upload init | API | `uploaded` | — (row created at complete) | — | `file_checksum` recorded; signed URL issued |
| Upload complete | API | `pending` | `pending` | `pending` | Queue rows enqueued; batch counters (`upload_batches.total_files`) |
| Virus scan | File Virus Scanner | `processing` (clean) / `failed` (infected) | `processing` / `failed` | `in_progress` | `processing_logs`; infected → notification |
| Image preprocess (images only) | Image Processing | `processing` | `processing` | `in_progress` | Previews in Storage |
| OCR | OCR Worker | `processing` | `processing` | `in_progress` | OCR text to Storage; low yield → manual route |
| AI extraction | AI Extraction Worker | `processed` (high conf.) / `manual_review` (low conf.) | `ai_extracted` / `manual_review` | `in_progress` | Usage counter increment; mapping hints written |
| Manual extraction (staff) | Staff via Admin API; Manual Review path | `manual_review` | `manual_extraction` | `assigned`→`in_progress` | `manual_review_queue` row worked; `manual_extraction_result`, SLA tracked |
| QC (when `qc_required`) | QC staff | `manual_review` | `qc` | `in_progress` | `qc_checks`/`qc_errors`; fail → back to `manual_extraction` |
| Customer review | API (customer) | `manual_review`/`processed` | `customer_review` | `in_progress` | Review payload via `/documents/{id}/review` |
| Confirm / approve | API (customer) | `approved` / `rejected` | `approved` / `rejected` | `in_progress` | `customer_verifications` + `verification_logs` written |
| Carbon calculation | Carbon Calculation Worker | `verified` | `completed` (factor miss → `manual_review`) | `completed` | `emissions_logs` row; `emission_factor_used` recorded; corrections as positive rows |
| Terminal failure | Any worker | `failed` | `failed` | `on_hold` | Dead-letter per §3; staff triage in `manual_review_queue` |

Realtime surfaces (`notifications`, `messages`, queue progress) are published at each transition by the writing worker; the client never polls for pipeline state.

---

**Worker count: 10** (File Virus Scanner, OCR, AI Extraction, Image Processing, Carbon Calculation, Report Generation, PDF Generation, Notification, Email, Cleanup) plus **4 cross-cutting sections** (Retry Strategy, Dead Letter Queue, Priority Queue, Worker Scaling) and the pipeline choreography state-flow table. All queue tables, status vocabularies, priority/SLA columns and supporting tables verified against the frozen schema dump and RC1 release notes; no tables or columns invented; no SQL/code/seed content.
