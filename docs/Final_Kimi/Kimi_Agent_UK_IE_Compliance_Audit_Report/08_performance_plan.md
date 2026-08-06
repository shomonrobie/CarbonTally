# CarbonTally — Performance & Scale Plan (RC2-Frozen)

*Status: architecture specification only. Database frozen at RC2. Indexes are frozen (I1–I5 + K5 unique-backed, ~18 targeted) — this plan proposes **monitoring, query discipline, pooling and platform scaling only; never new indexes, never partitioning now** (frozen revisit trigger: >10–20M rows/table, vacuum pressure, or retention-window failure). Consistent with `CarbonTally_RC2_Architecture_Freeze.md` §6–§7. Cost classes: **free** (code/config discipline, no new spend), **config** (plan/setting change on existing platform), **infra** (new billable infrastructure).*

## 1. Per-Customer Data Assumptions

Stated assumptions, aligned with freeze §7; the quarterly review replaces them with observed values.

| Measure | Assumption per average org / year | Notes |
|---|---|---|
| Documents uploaded | ~600 (≈50/month) | ~2 MB average → ~1.2 GB storage/org/year in `documents` |
| Pipeline rows | ~600 `document_processing_queue` + ~2,000–5,000 `processing_logs` | Completed history trimmed by retention jobs |
| `emissions_logs` rows | ~1,000–2,000 | Core reporting read path (I1b) |
| Messages / notifications | ~500 / ~1,000 | Support chat + event fan-out |
| Storage (all buckets) | ~2 GB/org/year steady state | Documents + attachments + derived PDFs; `generated-reports`/`ai-temp`/`temp-uploads` are self-trimming (90 d / 72 h / 24 h) |
| Audit/activity rows | 10–50 per user-day | 9+ table append-only family |
| Concurrent active users | ~10% of seats at peak | Drives Realtime + connection counts |
| Consultant skew | One consultant org may aggregate ×10–×50 client tenants | Per-tenant statistics get lumpy at the top |

Aggregate read: 1,000 orgs ≈ 0.6M documents/yr (~1–2 TB storage, low-seven-figure pipeline rows, ~10⁶–10⁷ `emissions_logs`); 10,000 orgs ≈ 6M documents/yr (~10–20 TB, `emissions_logs` at 10⁷–10⁸ — inside the frozen partitioning-revisit band).

## 2. Tier Plans

### Tier 1 — 10 customers (private beta / design partners)

Platform estate: `emissions_logs` ~10⁴ rows; queues ~10³–10⁴; storage ~20 GB; a handful of concurrent users.

| Dimension | Holds | Starts to hurt | Action at this tier (cost class) |
|---|---|---|---|
| Caching | Next.js route/data cache for static shell and marketing; nothing else needed | Cold factor lookups are still sub-10 ms — caching would be theatre | Ship cache-invalidation *conventions* now (cache keys name the org and the entity version) so later tiers add caching without rework (**free**) |
| Worker Scaling | Single worker process per type (virus scan, OCR/extraction, report generation) on one small instance; fixed poll cadence against I2 partials | Nothing | Baseline throughput metrics captured per worker type (jobs/min, p95 job duration) — every later scaling decision is judged against these (**free**) |
| Storage | Single-tier standard; 5 private buckets; hourly temp/AI sweepers | Nothing | Verify sweepers and lifecycle jobs run green from day one — discipline is cheapest before data exists (**free**) |
| Database | Smallest Supabase compute; I1–I5 trivially serve everything; RLS predicate cost invisible | Nothing | Capture monitoring baselines (row counts, p95 per watchlist table, vacuum stats) per freeze §7.1 "now" column; EXPLAIN gate in CI live from the first query (**free**) |
| Realtime | Channel-per-org for messaging/notifications; a few dozen concurrent channels | Nothing | Channel naming and authz conventions fixed now (`org:{id}:messages`, `org:{id}:notify:{user_id}`); no per-user message channels — fan-out stays server-side (**free**) |
| Search | Trigram (I5a–c) autocomplete on suppliers/orgs — instant on tiny tables | Nothing | Tenant-scope every search query first (org equality prunes the trigram scan) — habit costs nothing now, saves the tier-3 rework (**free**) |
| Indexes | Frozen RC2 set; partials are tiny and hot | Nothing | Verify worker claim predicates match the I2 partials exactly (Gate 7) and keep CI checking — a mismatched predicate is silently unused, not an error (**free**) |
| Queue scaling | `document_processing_queue` + `processing_queue` + `report_generation_queue` polled by single workers; skip-locked claim pattern | Nothing | Claim batch sizes and poll cadence set as configuration, not constants — later tiers tune values, not code (**free**) |

### Tier 2 — 100 customers (~launch ×2)

Estate: `emissions_logs` ~10⁵–10⁶; queues ~10⁵; audit family ~10⁶; storage ~200 GB; tens of concurrent users. Freeze verdict: **nothing structural degrades** — I1–I5 plus retention jobs are sized for this.

| Dimension | Holds | Starts to hurt | Action at this tier (cost class) |
|---|---|---|---|
| Caching | Next.js cache carries read-heavy screens; factor lookups still fast uncached | Repeated `emission_factors` and org-settings reads on every page/action are pure waste at rising request rates | Introduce Upstash Redis for two justified classes only: **emission-factor lookups** (invalidate on factor-set publish — rare, admin-triggered) and **org settings** (invalidate on settings write, write-through). TTL 1 h backstop. Nothing else cached — evidence bar per freeze (**config** — Upstash plan) |
| Worker Scaling | Single workers still clear the load | OCR burstiness (month-end upload spikes) creates visible queue lag at fixed capacity | Move OCR/extraction workers to 2–3 replicas behind the skip-locked claim; autoscale on queue-depth metric, not CPU. Scan and report workers stay at 1–2 (**config/infra** — worker instances) |
| Storage | ~200 GB, single tier, sweepers green | Nothing | First real storage-cost baseline; confirm `generated-reports` 90-day job holds the byte curve flat (**free**) |
| Database | B-tree comfort everywhere; RLS cost still minor | Dashboard aggregation p95 becomes the first metric to watch (I1b-served) | **Query discipline only**: keyset pagination enforced on all lists (no OFFSET), no `SELECT *` on hot tables, batch writes on the pipeline path; Supabase pooler in transaction mode as the standard app connection (**free**); Supabase compute size-up if p95 demands (**config**) |
| Realtime | Channel-per-org; hundreds of concurrent connections | Nothing (Supabase Realtime handles this trivially) | Fan-out limit set as policy: notifications fan out to org members server-side only below 50 recipients; larger orgs get a single org-channel event + client-side relevance filter (**free**) |
| Search | Trigram fine on growing but small master-data tables | Autocomplete keystroke rate multiplies query count | Debounce + tenant-scoped queries (already convention); cache supplier-autocomplete result sets per org in Redis for 5 min (**free/config**) |
| Indexes | Frozen set | Churn on queue partials begins (dead tuples) | **Monitoring only**: track partial-index bloat ratio and dead-tuple counts between vacuums; tune autovacuum aggressiveness on queue tables if needed — a setting, not an index (**free/config**) |
| Queue scaling | Skip-locked claims on I2 partials | Poll traffic rises with worker count | Raise claim batch size; keep cadence; add per-queue depth/age dashboards with alert thresholds (depth > 5 min of throughput) (**free**) |

### Tier 3 — 1,000 customers

Estate: ~0.6M documents/yr, ~1–2 TB storage, `emissions_logs` ~10⁶–10⁷, queues ~10⁶ with retention holding. Freeze §7.1 named pressure points now bite: RLS predicate cost, queue polling contention, partial-index bloat, write amplification (~5–8 indexes maintained per pipeline write).

| Dimension | Holds | Starts to hurt | Action at this tier (cost class) |
|---|---|---|---|
| Caching | Factor + settings caches carrying well | Dashboard aggregates (period rollups) become the expensive repeated read; per-request computation multiplies DB load × concurrent viewers | Add **dashboard aggregate cache** in Redis: key = org + period + last-`emissions_logs`-write timestamp; invalidation on any org emissions write (write-through invalidation, not TTL-only). Justified: the product's headline numbers, read-heavy, cheap to invalidate (**config**) |
| Worker Scaling | Autoscaled OCR pool | Sustained month-end depth; report-generation queue contends with OCR for compute | Separate worker pools per queue with independent autoscaling (scan 2–4, OCR 5–15, reports 2–6 — scaled on per-queue depth/age); queue priorities honoured in claim order; per-tenant fair-share guard so one bulk-uploading org cannot starve others (**infra**) |
| Storage | ~1–2 TB; lifecycle jobs holding | Storage cost is now a line item that finance notices | First annual storage-cost review armed (freeze trigger for tiering, v1.1+); verify pinned-export counts stay exceptional; confirm sweeper metrics trend flat. **No tiering yet** — trigger is the cost trajectory, not the calendar (**free** now) |
| Database | Indexes still serve; no structural change permitted | RLS per-row predicate evaluation is the dominant per-query cost on `emissions_logs` and queue tables; write amplification on the pipeline path | **Strictly within the freeze**: (a) pooler sizing review at ~500 concurrent tenants (freeze §7.1) — session/transaction mode split per workload (**config**); (b) index **consolidation** only if bloat is measured — rebuild/dedupe, never add (freeze-sanctioned, v1.1/v1.2, bloat-triggered) (**free**); (c) Supabase compute size-up (**config**); (d) read offload of heavy reporting to a **read replica** only if reporting p95 shows contention — freeze lists replicas at v2.0 trigger, so escalate via change control if needed early (**infra**, change-controlled) |
| Realtime | Channel-per-org; thousands of connections | Connection count and notification fan-out at the largest orgs; consultant orgs aggregating ×10–×50 tenants through one surface | Org-channel fan-out with server-side aggregation (batch notifications into digest events at high velocity); per-org connection caps; Realtime plan sizing review (**config**); consultant portal moves to polling-with-Realtime-hints rather than N client-tenant channel subscriptions (**free**) |
| Search | Trigram on tenant-scoped queries | Similarity-scan cost on large supplier tables; keystroke volume at thousands of concurrent users | Redis-cache autocomplete per org; raise the **external search trigger** (freeze §7 class: trigram then external at scale) — evaluate a search service (e.g., a managed OpenSearch/Typesense class) when trigram p95 on supplier autocomplete breaches 300 ms sustained *or* search scope expands to document content. Until then: nothing — tenant scoping keeps trigram honest (**infra** when trigger fires, else **free**) |
| Indexes | Frozen set — monitoring posture absolute | Partial-index bloat on queue tables; membership/GIN surface bloat; write amplification | Bloat-ratio dashboard; scheduled `REINDEX CONCURRENTLY` of bloated partials in maintenance windows (maintenance of frozen indexes, not new indexes); autovacuum tuning per hot table (**free/config**). **No new index proposals** — anything needing one goes through the v1.1 evidence gate (typed-column promotion preferred, per freeze §6.3) |
| Queue scaling | Independent pools; skip-locked claims | Claim-poll latency approaching the 200 ms watchlist threshold; completed-row history pressure | Tighten completed-row retention on queue tables (freeze-sanctioned first response); verify retention DELETEs run inside windows; claim batch/cadence tuned per queue; dead-letter handling for poisoned jobs (**free**) |

### Tier 4 — 10,000 customers

Estate: ~6M documents/yr, ~10–20 TB storage, `emissions_logs` 10⁷–10⁸ (**frozen partitioning-revisit trigger likely fires**), audit family ~10⁸ aggregate, erasure jobs stretching toward the one-month DSAR clock (freeze §7.1).

| Dimension | Holds | Starts to hurt | Action at this tier (cost class) |
|---|---|---|---|
| Caching | All three cache classes mature | Cache fleet coordination; invalidation storms on bulk imports | Versioned cache keys (org + entity-version) become mandatory; aggregate cache sharded by org hash; stampede protection (single-flight recomputation) on dashboard aggregates (**free/config**) |
| Worker Scaling | Per-queue autoscaling pools | Sustained high throughput; tenant skew (one consultant org = thousands of tenants' work) | Worker autoscaling on composite signal (queue depth × age × job class); dedicated capacity lane for bulk/enterprise tenants; spot/interruptible capacity for reprocessing backlogs (**infra**) |
| Storage | 10–20 TB; lifecycle jobs essential, not optional | Storage cost is a top-3 platform cost; backup/restore windows lengthen | **Storage tiering activates** (freeze trigger: annual cost review — by now it has fired): lifecycle transition of cold `documents` prefixes to colder class; erasure/offboarding sweeps strictly enforced as cost control; storage-cost-per-org becomes a pricing input (**config/infra**) |
| Database | Frozen index set still the only index set; single primary still serves OLTP | `emissions_logs` enters the 10–20M+ revisit band; retention DELETEs strain windows; backup windows stretch RTO; reporting contends with OLTP | In frozen-trigger order: (a) **read replicas / reporting offload** — reporting p95 contention trigger (freeze: v2.0) (**infra**); (b) retention windows tightened + erasure-job parallelisation and rehearsed bulk erasure (freeze: v1.1, rehearsal-time trigger) (**free/config**); (c) **partitioning revisit of the audit family and `emissions_logs`** — only because the frozen trigger (>10–20M rows / vacuum pressure / retention-window failure) has fired; executed as a versioned change (v1.2/v2.0), never ad hoc (**infra/major change control**). Still **no new B-tree/GIN proposals** outside the evidence gate |
| Realtime | Channel-per-org at platform-plan ceilings | Connection counts at plan limits; fan-out at enterprise scale | Realtime dedicated/plan scale-up (**infra**); enterprise orgs on aggregated channels; strict per-org connection caps; degradation contract: under overload, notifications degrade to 30-second polling while messages stay live (**config**) |
| Search | Trigram for tenant-scoped autocomplete | Any cross-document/content search is beyond trigram's brief; autocomplete p95 on the largest supplier sets | **External search trigger fires** (if not already at tier 3): managed search service for document/message content, fed by outbox-style events from the pipeline; trigram retained for entry-time duplicate prompts (its frozen job); Postgres full-text on `messages.content` remains a v1.1 evidence-gated candidate, not a tier-4 improvisation (**infra**) |
| Indexes | Frozen set, plus whatever the partitioning revisit (if executed) carries per partition | Bloat and write amplification at 10⁷+ rows | Rebuild/REINDEX schedule per hot index; per-tenant statistics reviewed for skewed consultant orgs; the v1.1 evidence-gated items (targeted `extracted_data` GIN **only** with query-log evidence, typed-column promotion preferred) decided by then on data, not projection (**free/config**) |
| Queue scaling | Autoscaled pools with fairness lanes | Claim contention at very high worker counts; completed-history growth | Completed-row retention at its tightest sustainable window; queue throughput benchmarked quarterly against the 200 ms claim-p95 threshold; if claim latency cannot be held, that is input to the partitioning revisit for `document_processing_queue` (freeze candidate #3) (**free/config**) |

## 3. Caching Register (all tiers) — What, Where, Invalidation

| Cached item | Store | First tier active | Invalidation rule |
|---|---|---|---|
| Emission-factor lookups (`emission_factors` by year/activity/country) | Upstash Redis | 100 | On factor-set publish (admin action); 1 h TTL backstop |
| Organisation settings / subscription limits | Upstash Redis | 100 | Write-through on settings write; 1 h TTL backstop |
| Supplier autocomplete result sets (per org) | Upstash Redis | 100 | 5 min TTL (entry-time UX tolerates staleness); bust on supplier write |
| Dashboard aggregates (period rollups) | Upstash Redis | 1,000 | On any org `emissions_logs` write (key carries last-write version); 15 min TTL backstop |
| Next.js route/data cache (shell, reference data, signed-image responses) | Next.js cache | 10 | Path/tag revalidation on mutation; default route TTLs |

Cache discipline: every entry names its org and a version/timestamp in the key (so invalidation is surgical, never a flush); nothing is cached whose invalidation cannot be stated in one sentence; Upstash is introduced only where the table above justifies it — the freeze's "only where justified" bar.

## 4. Capacity-Planning Table

| Tier | Dimension | Action | Trigger metric (stated assumption, re-baselined quarterly) | Cost class |
|---|---|---|---|---|
| 10 | All | Baselines captured; conventions fixed; CI EXPLAIN gate live | Launch readiness gates (Gate 4/5/7 green) | free |
| 100 | Caching | Redis: factors + settings | Repeated identical reads > 20% of query volume | config |
| 100 | Workers | OCR 2–3 replicas, depth-autoscaled | Queue depth > 5 min of throughput sustained | config/infra |
| 100 | Database | Pooler transaction mode; compute size-up | Connection saturation > 70%; p95 drift vs baseline | config |
| 100 | Indexes | Bloat monitoring on queue partials | Dead-tuple ratio climbing between vacuums | free |
| 1,000 | Caching | Dashboard aggregate cache | Aggregation p95 > 500 ms or > 30% of DB read load | config |
| 1,000 | Workers | Per-queue pools (scan 2–4 / OCR 5–15 / reports 2–6) + fair-share | Per-queue age p95 > SLA; single-tenant depth dominance | infra |
| 1,000 | Storage | Annual cost review armed; sweeper metrics flat | Storage £/org/month trend (first annual review) | free |
| 1,000 | Database | Pooler sizing review (~500 concurrent tenants); consolidation **only if bloat measured**; replica via change control if reporting contends | Pooler saturation; bloat ratio threshold; reporting p95 contention | config / infra |
| 1,000 | Realtime | Server-side fan-out aggregation; per-org caps | Concurrent connections vs plan ceiling; fan-out latency | config |
| 1,000 | Search | External search **evaluation** armed | Supplier autocomplete p95 > 300 ms sustained, or scope expands to content | infra (if fires) |
| 1,000 | Queue | Retention tightening; claim tuning | Claim p95 approaching 200 ms (frozen watchlist) | free |
| 10,000 | Storage | Tiering/lifecycle transition of cold `documents` | Annual cost review trigger fired (freeze §7) | config/infra |
| 10,000 | Database | Read replicas (reporting offload); erasure parallelisation; **partitioning revisit** (audit family, `emissions_logs`, possibly queue tables) | Reporting p95 contention; erasure rehearsal → one week; **>10–20M rows/table, vacuum pressure, or retention-window failure** (frozen) | infra / major change control |
| 10,000 | Realtime | Plan scale-up; degradation contract live | Connection counts at plan ceiling | infra/config |
| 10,000 | Search | External search service live (outbox-fed); trigram retained for entry-time dedup | Trigger fired at tier 3/4 | infra |
| 10,000 | Workers | Composite autoscaling + enterprise lanes + spot capacity for backlogs | Depth × age × class composite; tenant-skew incidents | infra |
| 10,000 | Queue | Tightest retention; queue partitioning input to revisit | Claim p95 > 200 ms unsustainable by retention | free/config |

## 5. Explicit Non-Actions (frozen, restated so no tier improvises them)

1. **No new indexes at any tier** without the v1.1 evidence gate (query-log evidence; typed-column promotion preferred over jsonb GIN). Index work permitted: monitoring, REINDEX/consolidation of the frozen set on measured bloat.
2. **No partitioning** until the frozen trigger fires (>10–20M rows/table, sustained vacuum pressure, or retention DELETEs exceeding their window) — then executed as a versioned change (v1.2/v2.0), not an emergency improvisation.
3. **No audit-archive storage/table** before its v1.1 trigger (T2, deferred with trigger).
4. **No public buckets, no long-lived signed URLs, no per-tenant buckets** at any scale — the storage posture does not change with size.
5. **No blanket caching** — Upstash/Next.js caches exist only per the §3 register with stated invalidation.
6. **100,000-org horizon** (single-primary limits, sharding/second cluster, ~25,000-org trigger) is a v2.0+ planning item per freeze §7.1 — noted here for completeness, planned for nowhere.

---

*Consistency statement: every tier action is either free/config discipline, a freeze-named "now" item, or a freeze-named deferred item acting on its frozen trigger. No rejected item (I6 blanket FK indexes, blanket jsonb GIN, partitioning now) is resurrected at any tier.*
