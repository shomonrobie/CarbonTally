## Section 6 — Performance Review

*Scope: Supabase/PostgreSQL 16, multi-tenant with row-level security. The index posture below restates the frozen Structural Change Review verdicts — five targeted index families (I1–I5, roughly 18 indexes once the UNIQUE-backed indexes of the constraint set are counted), the I6 blanket "index every FK" programme REJECTED, the blanket-jsonb GIN programme REJECTED, and partitioning REJECTED with a documented revisit trigger. Nothing in this section resurrects a rejected item. All builds are CONCURRENT, each in its own transaction, per the P3 phase of the hardening plan; every family carries the migration-file verification caveat (the schema dump showed no indexes, so each family may collapse from "build" to "verify"). All volume figures are stated assumptions, not measurements.*

### 6.1 Approved index register

The register admits only indexes serving actual v1.0 query paths: RLS tenant joins, queue claiming, dedup lookups, unread counts and search. Anything else failed the real-value bar and was rejected (I6) or deferred evidence-gated to v1.1.

| Index family | Target table / columns | Type | Query it serves | Why it earns its place |
|---|---|---|---|---|
| I1a | `customer_documents(organization_id, created_at DESC)` | Composite B-tree | Document list screen (tenant-scoped, most recent first) | Every document screen and every RLS policy joins on `organization_id`; the DESC ordering matches the dominant list query on the primary pipeline entity. Without it, the launch's busiest screen seq-scans a growing table. |
| I1b | `emissions_logs(organization_id, start_date)` | Composite B-tree | Emissions aggregations and period rollups (SECR/UK reporting flow) | The core reporting read path: tenant-scoped aggregation over a date range. Index-serves the product's headline numbers and the RLS join simultaneously. |
| I1c | `suppliers(organization_id)` | B-tree | Supplier pickers, supplier-scoped lists | Tenant picker queried on every upload and mapping screen. |
| I1d | `facilities(organization_id)` | B-tree | Facility pickers, site lists | Same tenant-picker shape as I1c; small table now, but the index is the discipline that keeps the join constant as facilities accrete. |
| I2a | `document_processing_queue(status, created_at)` WHERE status in the unclaimed/active set | Partial composite B-tree | Worker claim polling (claim oldest unclaimed item) | The single hottest read pattern in the system: workers poll continuously, and an unindexed claim query seq-scans the whole history of completed work on every poll. The partial keeps the index small and hot — completed rows never enter it. |
| I2b | `processing_queue(queue_status, …)` WHERE unclaimed/active | Partial composite B-tree | Ops-queue claim polling | Same claim shape on the ops/manual processing queue; decouples worker throughput from table age. |
| I2c | `report_generation_queue` status path | Partial B-tree | Report-generation worker polling | Lower volume than I2a/I2b but identical access shape; same justification at smaller scale. |
| I3a | `messages(conversation_id, created_at)` | Composite B-tree | Support-chat thread rendering | Per-page-load query on a committed v1.0 screen; timeline ordering is the natural index shape. |
| I3b | `conversation_participants(conversation_id, user_id)` | Composite B-tree | Participant resolution on every thread view and message insert | Stops the participant join seq-scanning; also the lookup path for unread-state derivation. |
| I3c | `notifications(recipient_id)` WHERE unread (`is_read = false`) | Partial B-tree | Notification badge / unread count | A badge count on every page load must not scan the full notification history; the partial indexes only what the badge can ever count. |
| I4 | `consultant_firm_members.client_access` | GIN (uuid array) | Consultant RLS evaluation (is this client org in the consultant's access array?) | The sole justified GIN in v1.0. The array is ADR-locked (junction-table replacement rejected), so the security predicate cannot B-tree; without the GIN every consultant RLS check seq-scans membership rows. Low-churn table, so GIN write amplification is acceptable. |
| I5a | `suppliers.name` | Trigram (`pg_trgm`) | Supplier autocomplete, "did you mean?" duplicate prompt | The soft control complementing the hard identifier uniqueness of the constraint set — prevents the "City Electrical 2" workaround pattern without outlawing legitimate same-name suppliers. |
| I5b | `suppliers.vat_number` | Trigram (`pg_trgm`) | Fuzzy identifier matching at supplier entry | Near-duplicate VAT detection at entry time. |
| I5c | `organizations.name` | Trigram (`pg_trgm`) | Org autocomplete (consultant/staff screens) | Same autocomplete justification; may land in the v1.0.x window rather than launch day, as it serves UX, not correctness. |

Register count: 16 targeted indexes in I1–I5, plus the UNIQUE-backed indexes below — the "~18 targeted indexes" headline once shared paths are collapsed. Deferred without prejudice (evidence-gated, v1.1, against query logs or committed screens): a targeted GIN on `customer_documents.extracted_data`, full-text search on `messages.content`, staff/ops composites, and non-entry-point FK indexes. The blanket jsonb GIN programme and the I6 blanket FK programme remain rejected, not deferred.

### 6.2 Index-bearing unique constraints

The uniqueness set (constraint item K5 of the structural review) is enforced by UNIQUE constraints whose backing indexes double as query-path indexes. They are counted here, not in §6.1, per the review's own accounting.

| Unique constraint | Table / columns | Lookup path it also serves |
|---|---|---|
| Membership uniqueness | `organization_members(organization_id, user_id)` | RLS membership evaluation — the most frequent security lookup in the system |
| Consultant-client link | `consultant_clients(consultant_id, organization_id)` | Consultant portal client lists |
| Billing month | `usage_tracking(organization_id, usage_month)` | Limit-check on every metered action (uploads, extractions) |
| Report version | `report_versions(report_id, version_number)` | Version resolution and `is_current` disambiguation |
| Supplier VAT (partial, WHERE NOT NULL) | `suppliers(organization_id, vat_number)` | Supplier dedup lookup at document mapping |
| Supplier company number (partial, WHERE NOT NULL) | `suppliers(organization_id, company_number)` | As above, on the second identifier |
| Factor uniqueness | `emission_factors(reporting_year, activity_type, country)` | Factor resolution in the calculation path |
| Reset token (retained per K6) | `password_reset_tokens(token)` | Token validation on the reset flow |

A name-unique on `suppliers` remains explicitly excluded (legitimate same-name suppliers exist; the trigram "did you mean?" of I5 is the soft control).

### 6.3 Expected bottlenecks at launch

Five pressure points are expected to dominate at launch volume (~50 customers; pipeline tables at low six figures; busiest log tables at low seven figures after year one — stated assumptions from the hardening plan's volume realism). None requires structural change now; each has a named mitigation already in the plan.

| Bottleneck | Where it bites | Why | Posture |
|---|---|---|---|
| RLS per-row policy evaluation | `emissions_logs`, `customer_documents`, the queue tables, `messages`, `notifications` | PostgreSQL evaluates the tenant predicate per row on every query; on large tables the predicate cost and the membership join dominate query time | I1 composites and the membership UNIQUE-backed index make the predicate index-served; K7's NOT NULL `organization_id` makes policies total functions. Watch p95 on the document list and emissions aggregation (Gate 7 load smoke). |
| Queue polling contention | `document_processing_queue`, `processing_queue` | Workers poll on a fixed cadence; concurrent claimers contend for the head of the queue, and the partial indexes only help if the claim predicate matches them exactly | I2 partials plus the skip-locked claim pattern (§6.6); Gate 7 verifies the plans use the partials — a predicate mismatch is silently unused, not an error. |
| jsonb metadata filtering without GIN | `customer_documents.extracted_data`/`mapped_data`, `emissions_logs.metadata`, `activity_logs.metadata`, audit `old_data`/`new_data` | Any filter on a jsonb key seq-scans; this is **deliberate** — the blanket GIN programme is rejected because GIN rewrites entries on every jsonb update, write-amplifying the hottest tables for zero observed key-filter queries | A targeted GIN on `extracted_data` is reconsidered only when query logs show a committed screen or worker filtering on jsonb keys (the C23 evidence gate), and even then the preferred remedy is promoting the hot key to a typed column (C11, v1.1), not indexing the jsonb. |
| Trigram search cost | `suppliers.name`/`.vat_number`, `organizations.name` | Trigram similarity scans are costlier than B-tree lookups and degrade on large tables; autocomplete keystrokes multiply the query rate | Acceptable at launch volume on small master-data tables; if supplier counts grow an order of magnitude, tenant-scope the search first (the org equality prunes the trigram scan). |
| Wide-row audit tables | `audit_logs`, `audit_trail`, `activity_logs`, `processing_audit_trail`, `review_audit_trail` and peers (9+ tables) | Rows carry multiple jsonb payloads (`old_data`, `new_data`, `changes`, `metadata`); table scans and vacuum traverse large TOAST-heavy rows, and retention DELETEs get slower as tables grow | Append-only posture (UPDATE/DELETE revoked per the audit-hardening B item) plus the retention schedule (§7); no index on the jsonb payloads — reads are time-ordered, served by the primary key and `created_at`. |

### 6.4 Large tables watchlist

Hot and growing tables identified from the schema dump, with the metric watched and the threshold that forces action. Thresholds are stated assumptions, tuned at the first quarterly review against real growth.

| Table | Why it grows | Monitoring metric | Intervention threshold |
|---|---|---|---|
| `emissions_logs` | One row per emission entry per tenant per period; grows with documents processed and manual entries | Row count per org; aggregation p95 on `(organization_id, start_date)` | >10–20M rows or aggregation p95 doubling quarter-on-quarter → partitioning revisit (§6.5) |
| `document_processing_queue` | One row per document through the AI/manual pipeline; accumulates completed history | Claim-poll latency; dead-tuple ratio between vacuums | Claim p95 > 200ms at the partial index, or vacuum pressure → retention tightening on completed rows; partitioning revisit |
| `processing_queue` | Ops/manual processing history | As above | As above |
| `processing_logs` | Step-level logging per document — highest write rate in the pipeline | Row count growth per week | 90-day retention job (already scheduled v1.0.1) missing its window or table > 10M rows |
| `messages` / `notifications` | Support chat and event notifications per user | Unread-partial size; thread-render p95 | Thread render p95 breach, or notification history degrading the badge partial → retention/archival review |
| `audit_logs` + `audit_trail` + the 9+ audit/activity family | Append-only history of every sensitive action; widest rows in the schema | Family row counts; vacuum duration; retention-job duration | Retention window cannot be met by the pg_cron jobs, or vacuum pressure → audit-archive table (T2, deferred to v1.1) activates |
| `file_attachments` | Chat/document attachments; metadata rows here, bytes in storage | Row count; storage bucket size | Storage growth per Section 7; table itself is not the pressure point |
| `login_history` / `email_logs` / `notification_delivery_log` | Per-event logging | Row counts | 12-month retention jobs (scheduled) failing to hold the line |

### 6.5 Partition candidates — frozen decision

**Decision: NO partitioning in v1.0 or v1.1 as currently scoped.** Monthly RANGE partitioning was evaluated and REJECTED (hardening plan D4; confirmed by the structural review): low-seven-figure row counts after year one are trivially served by B-trees plus retention DELETEs, and partitioning multiplies operational surface — per-partition indexes, partition-aware migration tooling, pruning edge cases — for zero measured benefit. Cheap-to-do is not worth-doing.

Future candidates, named now so the trigger is unambiguous:

1. The audit/activity log family (`audit_logs`, `audit_trail`, `activity_logs`, `processing_audit_trail`, peers) — append-only, time-ordered, the natural RANGE shape.
2. `emissions_logs` — the largest tenant data table; partitioning key would be period date.
3. `document_processing_queue` / `processing_logs` — only if completed-row retention cannot hold the partial-index posture.

**Revisit trigger (frozen):** any watchlist table exceeding ~10–20M rows, **or** sustained vacuum pressure (autovacuum unable to keep dead tuples bounded at the tuned settings), **or** retention DELETEs that can no longer run inside their maintenance window. The trigger is re-tested at each quarterly review against measured counts, not projected ones.

### 6.6 Query optimisation guidance — principles for the application team

- **Tenant-scope every query first.** Always filter on `organization_id` equality before anything else; it makes the RLS predicate and the I1 composites work together and prunes every other access path. Never rely on RLS alone for scoping in application SQL — belt and braces are cheap at read time.
- **No `SELECT *` on hot tables.** Name the columns. The pipeline and audit tables are wide and jsonb-heavy; projecting `extracted_data`, `metadata` or `old_data`/`new_data` when the screen needs three fields toasts and detoasts megabytes per page.
- **Paginate `messages`, `notifications` and document lists with keyset (cursor) pagination**, not `OFFSET`. Deep offsets re-scan and re-sort everything skipped; the I1/I3 composites are ordered exactly for keyset use.
- **Claim queue work with the skip-locked pattern**: select the head of the unclaimed set ordered FIFO, `FOR UPDATE SKIP LOCKED`, bounded batch. Never claim with an ad-hoc status filter — the I2 partials match one predicate exactly, and a mismatched predicate silently seq-scans (Gate 7 checks the plans; CI keeps checking).
- **Never filter on jsonb keys in application queries.** If a screen needs to filter by something inside `extracted_data` or `metadata`, that is the signal to raise the typed-column promotion discussion (v1.1 evidence gate), not to ship the jsonb filter.
- **Count unread via the partial's shape** (`recipient_id` + unread flag), and prefer existence checks over `COUNT(*)` where the UI only needs a badge-or-none.
- **EXPLAIN gate in CI**: every new or changed query against a watchlist table lands with an `EXPLAIN` (analyse, buffers) captured in the pull request on a seeded database; any seq scan on `emissions_logs`, `customer_documents`, the queue tables, `messages` or `notifications` fails the gate unless explicitly waived with a reason recorded.
- **Batch writes; avoid row-at-a-time upserts on the pipeline path.** Each row write touches I1/I2/K5 indexes; batching amortises index maintenance and keeps write amplification predictable.

## Section 7 — Future Scalability

*Assumptions, stated explicitly and deliberately rough: an average organisation uploads ~50 documents/month (~600/year), producing ~600 pipeline rows and ~2,000–5,000 step-log rows/year; accumulates ~1,000–2,000 `emissions_logs` rows/year; generates ~500 messages and ~1,000 notifications/year; and every sensitive action appends to one or more audit tables at roughly 10–50 audit rows per user-day. A consultant org aggregates its client base (×10–×50 tenants' activity through one membership surface). These are planning assumptions, not measurements; the quarterly review replaces them with observed values.*

### 7.1 Scale ladder

| Scale (orgs) | What degrades or breaks | Why | Now (inexpensive) | Defer — trigger and target version |
|---|---|---|---|---|
| **100** (~launch ×2) | Nothing structural. `emissions_logs` ~10⁵–10⁶ rows; queues ~10⁵; audit family ~10⁶. All within B-tree comfort. | I1–I5 plus retention jobs are sized for this | Monitoring baselines captured at launch (row counts, p95 per watchlist table, vacuum stats) so every later threshold is judged against evidence, not vibes | — |
| **1,000** | RLS policy evaluation becomes the dominant per-query cost on `emissions_logs` and queue tables; queue polling contention rises with worker count; index bloat appears on churn-heavy partials (queue tables) and on the membership/GIN surface; storage at ~0.6M documents/year (~low-TB in buckets, stated assumption) | Per-row predicate cost scales with rows scanned; more workers × same poll cadence multiplies claim traffic; every write maintains ~5–8 indexes on the pipeline path (write amplification) | Retention jobs verified to hold completed queue rows and `processing_logs` inside their windows (v1.0.x schedule); pg_cron retention already B-class | Connection pooling (PgBouncer/Supabase pooler sizing) reviewed at ~500 concurrent tenants; targeted index consolidation if bloat measured — v1.1/v1.2, triggered by bloat ratio, not calendar |
| **10,000** | `emissions_logs` ~10⁷–10⁸ rows — partitioning revisit trigger likely fires; audit family (9+ tables) at 10⁸ aggregate — retention DELETEs strain maintenance windows and the audit-archive question (T2, DEFERRED to v1.1) becomes live; backup/restore windows lengthen beyond comfortable RTO; queue throughput needs worker autoscaling; tenant data skew (one consultant org with thousands of client tenants) makes per-tenant statistics and any per-tenant operation lumpy; anonymisation/erasure jobs against ~40 FK references stretch toward the one-month DSAR clock | Rows and TOAST volume outgrow single-table vacuum/retention economics; PITR base-backup size scales linearly; erasure touches every tenant table per request | Archival posture on the biggest log table: retention windows and the erasure runbook's FK graph kept current (already plan artefacts); nothing else inexpensive is left | Partitioning of the audit family and `emissions_logs` — trigger: >10–20M rows/table or vacuum pressure (frozen) — v1.2/v2.0. Audit-archive table (T2) — trigger: retention/vacuum pressure — v1.1+. Read replicas / reporting offload — trigger: reporting p95 contention — v2.0. Erasure-job parallelisation and a rehearsed bulk-erasure variant — trigger: rehearsal time approaching one week — v1.1 |
| **100,000** | Single-primary PostgreSQL assumption itself: connection counts exceed Supabase plan ceilings even pooled; storage at tens of TB; backup windows require continuous-archiving economics review; per-tenant RLS evaluation and index maintenance are fine per query but aggregate write amplification on the pipeline path is the ceiling; consultant-skew orgs may individually exceed the 10–20M row trigger on their own | At this scale the constraint is platform economics and operational windows, not any single index | Nothing — nothing here is inexpensive | Sharding/tenant-grouping strategy, storage tiering, possibly a second cluster per region — trigger: ~25,000 orgs or platform-limit telemetry — v2.0+ planning horizon |

### 7.2 Stress points in prose

**RLS policy evaluation at scale.** The policy model is sound and frozen; the cost is per-row predicate evaluation plus the membership/`client_access` lookup on every query. At 100–1,000 orgs the I1 composites and the membership UNIQUE-backed index keep this index-served. The risk at 10,000+ is not correctness but the aggregate: policies that join `organization_members` on every query of a 10⁸-row table demand that the membership lookup never leaves cache. Recommendation NOW: capture the Gate 7 query plans as the launch baseline so any planner regression (e.g. after statistics drift) is detected against evidence. DEFER: policy simplification or cached-claims patterns — trigger: measured p95 regression attributable to the predicate — v1.2.

**Index bloat and write amplification.** Every pipeline write maintains the I1/I2 composites and partials plus the K5 UNIQUE-backed indexes; the queue partials churn as rows transition status (a row leaves the partial on completion — the partial self-heals by design). GIN write amplification exists only on the low-churn `client_access` column, which is why it was the sole GIN admitted. NOW: include index bloat ratio in the launch monitoring baseline. DEFER: reindex scheduling and any index consolidation — trigger: measured bloat or write-latency regression — v1.1/v1.2.

**Queue throughput.** The claim pattern is constant-time by construction (I2 partials + skip-locked); throughput scales with workers until claim contention on the queue head becomes visible. DEFER: worker autoscaling and poll-cadence jitter — trigger: sustained claim latency or backlog age breaching the SLA definitions already in `sla_definitions` — v1.1.

**Audit-log growth (9+ tables).** The per-domain taxonomy is ADR-frozen and consolidation is rejected. Growth is unbounded by design (append-only evidence); the bound is retention. NOW (inexpensive): land the v1.0.x retention schedule and confirm the audit privilege-hardening (no UPDATE/DELETE) so the retention DELETEs are the only writer of history. DEFER: the audit-archive table (T2) — **kept as DEFERRED to v1.1 with its trigger** (measured log growth or vacuum pressure, the same revisit trigger as partitioning); unified read-only view (C7) — v1.1.

**Storage growth (documents).** Metadata lives in the database; bytes live in Supabase Storage. At ~0.6M documents/year per 1,000 orgs (assumption), bucket size — not table size — is the cost driver, and `file_attachments`/`customer_documents` rows stay modest. NOW: `retention_until` on the document class (already B-class) so lifecycle policy exists before the data does. DEFER: storage tiering/lifecycle rules — trigger: storage cost trajectory at the first annual review — v1.1+.

**Connection pooling / Supabase limits.** Supabase plan ceilings on connections and compute bind before the schema does. NOW: nothing beyond using the platform pooler correctly (workers and API on pooled connections; no long-lived idle transactions — an app-team rule, free). DEFER: plan-tier and pooler sizing review — trigger: ~500 concurrent tenants or pooler saturation telemetry — v1.1/v1.2.

**Tenant data skew.** One consultant org aggregating thousands of client tenants concentrates membership checks, `client_access` array evaluations and list queries. The I4 GIN is exactly the mitigation for the security predicate; list-level skew is absorbed by the tenant composites. NOW: nothing. DEFER: per-tenant statistics review and possible pagination hard-limits on consultant portal surfaces — trigger: measured skew (top-tenant row share > 10× median) with latency impact — v1.1/v1.2.

**Backup/restore windows.** PITR base backups grow linearly with data; restore rehearsal time is the honest metric. NOW: residency verification already gates launch (P5); add a timed restore rehearsal to the first quarterly review — inexpensive and evidence-producing. DEFER: restore-window objectives and any archival-tier backup strategy — trigger: rehearsal time exceeding the recovery objective — v1.1+.

**Anonymisation/erasure duration at scale.** The anonymise-in-place runbook touches ~40 FK references per user; per-request duration grows with tenant history, and the statutory clock does not. NOW: the procedure is launch-gated and rehearsal-timed (P5) — already the plan. DEFER: parallelised/batched erasure variant and a per-tenant data-retention sweep that shrinks what erasure must touch — trigger: staging rehearsal time trending toward one week per request — v1.1.

### 7.3 Recommendation summary

**Inexpensive now-items (approved):** monitoring baselines at launch (row counts, p95 per watchlist table, index bloat ratio, vacuum stats); retention schedule and pg_cron jobs per the v1.0.x window (archival posture on the biggest log tables is retention, not new structure — the audit-archive table itself stays DEFERRED to v1.1 with its growth/vacuum trigger); Gate 7 query plans captured as the regression baseline; one timed restore rehearsal per quarter; pooler discipline as an app-team rule.

**Everything else is deferred with a named trigger and target version** — partitioning (>10–20M rows/table or vacuum pressure; v1.2/v2.0), audit-archive table (T2; measured growth or vacuum pressure; v1.1+), targeted GIN on `extracted_data` (query-log evidence of jsonb key filtering; v1.1, with typed-column promotion preferred), read replicas (reporting contention; v2.0), connection/plan scaling (pooler saturation; v1.1/v1.2), erasure parallelisation (rehearsal time → one week; v1.1), storage tiering (annual cost review; v1.1+), and sharding/second-cluster planning (~25,000 orgs or platform-limit telemetry; v2.0+). No rejected item — blanket GIN, the I6 index programme, partitioning now — is resurrected anywhere in this ladder; each appears only as a triggered revisit, exactly as the structural review froze it.

*End of Sections 6–7.*
