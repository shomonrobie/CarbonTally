# CarbonTally — Gap Analysis (Deliverable 4 of 5)

**Document:** `docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md`
**Audience:** Product Owner · engineering · independent QA/audit
**Date:** 2026-09-27
**Posture:** read-only forensic analysis — **no** DDL, DML, migration, seed, configuration change, deployment or endpoint execution was performed.

---

## 0. Purpose, method and inputs

### 0.1 Purpose

Deliverables 1–3 establish *what the platform contains, how it is configured, and
how functionality traces from capability to persistence to role to boundary.* This
deliverable answers the next question:

> **Where does the platform, as it exists today, fall short of its own ratified
> requirements — and what must happen to close each shortfall?**

It consolidates every gap already raised in the earlier deliverables into **one
authoritative register with one numbering scheme (`GA-nn`)**, adds severity, impact,
ownership (implementation vs Product Owner) and a closing action, and sequences the
remediation.

### 0.2 Method

1. Consolidate the gap-bearing registers from deliverables 1–3: `FTR-GAP-1…6`
   (traceability), `CFG-1…10` (configuration), `R1…R7` (derived requirements),
   `T1…T6` (terminology), persistence classes `A…E`, and truth-state distribution.
2. Re-test each against **live read-only evidence** (schema inventory, migration
   ledger, row counts across two databases).
3. Classify each by severity, ownership and closing action.
4. **Discard** any item that the live evidence does not support, and record it as
   *not asserted* (§5).

### 0.3 Inputs

| Input | Role in this document |
|---|---|
| `CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` | 54 domains, 354 `FTR` rows, truth states, classes `A–E`, `T1–T6`, `R1–R7`, `POD-A…POD-J` |
| `CT-PO-CARBONTALLY-CONFIGURATION-CATALOGUE-20260927.md` | configuration surfaces `C1–C8`, `CFG-1…CFG-10`, `POD-K…POD-O` |
| `CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md` | `W1–W8`, 16 boundary traces, §5.0 live population baseline, `FTR-GAP-1…6` |
| Live read-only probes (2026-09-27) | flagship `postgres` (116 public tables) and disposable clone `ct_p17k_20260926` (145 public tables) |
| `AGENTS.md` (workspace constitution) | the requirement each gap is measured against |

### 0.4 Evidence vocabulary used below

`VERIFIED(schema)` · `VERIFIED(code)` · `VERIFIED(live)` · `VERIFIED(schema)/
PREDICTED(runtime)` · `UNKNOWN` — identical to the convention used in
deliverables 1–3. No gap below is asserted on assumption alone.

---

## 1. Executive summary

### 1.1 The shape of the gap

The platform is **far more complete than a "demo"** and **far less proven than its
feature inventory suggests**. Concretely:

- **354 catalogued feature rows; 313 `IMPLEMENTED_AND_WIRED`.** The functional
  surface exists in code and is reachable from wired routes.
- **But the platform's own core pipeline is only half-evidenced.** Upload (52
  batches), manual extraction (264 items), calculation (100 snapshots), reporting
  (17 versions), messaging and the audit ledger are **durably populated**; the
  *durable automatic state machine*, *evidence materialisation*, *QC* and *approval*
  are **empty or absent everywhere** (§2.1 of this document, and §5.0 of deliverable 3).
- **Durability is not uniform across environments.** 89 migrations exist; the
  flagship ledger holds 46, so **43 are unapplied** — and four of six local
  environments have an unreadable ledger. Several catalogued capabilities
  (P17 disclosure/scope-3/estimation, P8 Insight, P8 adjudication) exist **only** in
  disposable clones or the demo database.
- **Configuration is broader than it is real.** 63 `system_settings` columns exist;
  two HIGH findings show the retention API and the upload-limit path are wired to
  columns that **do not exist** in any durable database, so effective policy is a
  hard-coded fallback.

None of that is a claim that the product does not work. It is a claim that **the
product has not been *proven* to work end-to-end in a durable environment**, and
that AGENTS §74 explicitly forbids presenting code presence as business outcome.

### 1.2 Registered gaps by severity

| Severity | Count | IDs |
|---|---:|---|
| **HIGH** | **6** | GA-01, GA-02, GA-03, GA-04, GA-05, GA-06 |
| **MEDIUM** | **13** | GA-07, GA-08, GA-09, GA-10, GA-11, GA-12, GA-13, GA-14, GA-15, GA-16, GA-17, GA-27, GA-29 |
| **LOW-MEDIUM** | **7** | GA-18, GA-19, GA-20, GA-21, GA-25, GA-26, GA-28 |
| **LOW** | **3** | GA-22, GA-23, GA-24 |
| **Total** | **29** | — |

### 1.3 The five gaps that actually block acceptance

| Rank | Gap | Why it blocks |
|---|---|---|
| 1 | **GA-01** 43 unapplied migrations / divergent environments | Nothing downstream of the applied set can be called durable or verified |
| 2 | **GA-04** automatic pipeline never exercised | The platform's core value chain is unproven at runtime |
| 3 | **GA-05** evidence stage has no durable store | AGENTS §17's provenance chain cannot be demonstrated |
| 4 | **GA-02 / GA-03** configuration wired to non-existent columns | Two ratified configurable surfaces silently behave as hard-coded policy |
| 5 | **GA-06** approval/QC stages empty | Workflow completion claims (AGENTS §26, §74) are unsupported |

### 1.4 Severity model

| Band | Meaning |
|---|---|
| **HIGH** | Blocks an AGENTS-ratified outcome (durability, provenance, workflow completion, configurable policy) or makes a current behaviour misleading |
| **MEDIUM** | Real defect or divergence with contained blast radius; must be closed before the affected surface is trusted |
| **LOW-MEDIUM** | Correctness/hygiene issue with policy or security implications |
| **LOW** | Documentation, naming or legacy-hygiene issue |

---

## 2. Consolidated gap register

Legend — **Owner:** `IMPL` (implementation/engineering can close it) · `PO`
(requires a Product Owner decision first) · `PO+IMPL` (decision, then engineering).
Every row cites the register that raised it so nothing is orphaned.

### 2.1 Durability and environment gaps

| ID | Sev | Gap | Evidence | Impact | Owner | Closing action |
|---|---|---|---|---|---|---|
| **GA-01** | **HIGH** | **43 migrations unapplied; environments divergent.** Release tree = 89 migration files; flagship ledger = 46 rows (newest `20260903010000`), delta = the ordered set `20260905000000_gate4_actor_provenance.sql` → `20261020000000_p17k_governed_capability_catalogue.sql`. Ledgers are **unreadable** in 4 of 6 local environments. | flag live ledger · R1 · FTR-GAP-5 · CFG-10 · POD-A | Features can be `IMPLEMENTED_AND_WIRED` in Git yet absent from **every durable database**. No environment currently represents the release tree. | PO+IMPL | Apply the 43 migrations, in filename order, to one **backed-up durable** database after prerequisite check (AGENTS §55.1 forbids destructive harnesses against durable data), then re-run the ledger arithmetic |
| **GA-05** | **HIGH** | **Evidence stage has no durable store.** `evidence_line_items` **does not exist** in the flagship and holds **0 rows** in the clone. | §5.0 baseline · D-domain 31/evidence tables · AGENTS §17 | The provenance chain *document → extraction → factor → calculation → snapshot → emissions → evidence → approval* (AGENTS §17) cannot be demonstrated; "evidence" today is a code claim, not a persisted artefact. | PO+IMPL | Decide the evidence persistence target (table family + bucket), apply its migration, and materialise one real evidence set from a real calculation |
| **GA-07** | MEDIUM | **No single authoritative environment.** Public-table counts: flagship 116 · `carbontally_demo_local` 141 · `carbontally_test` 117 · `carbontally_qa_phase8` 133 · `ct_local_93d5cdd` 135 · `ct_p17k_20260926` 145. P17 (`scope3_categories` 15, `estimation_records`), disclosure and Insight objects appear **only** in clones/demo. | flag §5.3 · Class **C** · CFG-10 | Capability evidence is scattered across disposable environments and will be lost with them; "it exists somewhere" is not durability. | PO+IMPL | Name one authoritative durable environment, apply GA-01, and re-verify the class-C objects there |
| **GA-16** | MEDIUM | **Production state `UNKNOWN`.** Production was never contacted; its schema/migration state is unverified. | R7 · POD-I · all `PROD:` truth states = `UNKNOWN` | No claim can be made about production parity, drift or readiness. | PO | Authorise a read-only production schema/ledger inspection and record the result |

### 2.2 Runtime-evidence gaps (nothing executed end-to-end)

| ID | Sev | Gap | Evidence | Impact | Owner | Closing action |
|---|---|---|---|---|---|---|
| **GA-04** | **HIGH** | **The durable automatic pipeline has never run.** `processing_queue`, `processing_steps`, `processing_logs`, `processing_assignments`, `processing_audit_trail` = **0 rows** in *both* environments; `work_item_assignments` = 2 (flagship) / 0 (clone). The populated queue is `document_processing_queue` = 40 — a *different*, non-state-machine object. | §5.0 baseline · D31 · FTR-GAP-2 · W3 · AGENTS §18/§19/§74 | The automatic path — the platform's core commercial value — has no observed execution and no resumability/retry/idempotency evidence. | IMPL | Execute one document through the full automatic pipeline in a disposable environment, capture per-stage rows, retries and `attempt_count` |
| **GA-06** | **HIGH** | **Approval and QC are unexercised.** `approval_requests`, `approval_decisions`, `qc_checks`, `qc_checklists`, `qc_errors`, `review_audit_trail` = **0 rows** everywhere. | §5.0 baseline · D32 · W5/W7 · AGENTS §26 | Any "workflow complete" or "reviewed" status is unsupported by durable records; AGENTS §26 forbids appearing complete while approval is outstanding. | PO+IMPL | Decide who approves what (already partly ratified), then run one approval and one QC cycle and capture the records |
| **GA-27** | MEDIUM | **Audit target ambiguity.** `audit_trail` = 563 (flagship) / 16 (clone) while the tables that carry the *configured* retention key — `audit_logs` and `activity_logs` — hold **0 rows** in both. | §5.0 baseline · D33 · CFG-1/CFG-5 | Retention policy is expressed against one audit store while audit writes land in another; audit completeness and retention enforcement are therefore ambiguous. | PO+IMPL | Ratify which store is the authoritative audit ledger and align retention config with it |
| **GA-28** | LOW-MED | **Commercial, SLA and white-label flows unexercised.** Every `billing_*` transactional table, `customer_subscriptions`, `consultant_billing`, `sla_definitions`, `sla_compliance`, `consultant_custom_domains`, `consultant_senders` = **0 rows** everywhere. | §5.0 baseline · CFG-8 · AGENTS §43/§64 | Billing, SLA and white-label capabilities are traceable but have never produced an outcome; their configured catalogue (`billing_plans` 6, `billing_commercial_config` 7) is policy without a transaction. | PO+IMPL | After POD-K/POD-L/POD-O, execute one end-to-end commercial and one white-label flow in a disposable environment |

### 2.3 Configuration gaps (`CFG-1…CFG-10`, from deliverable 2)

| ID | Sev | Gap | Evidence | Impact | Owner | Closing action |
|---|---|---|---|---|---|---|
| **GA-02** | **HIGH** | **Retention API wired to a column that exists in no durable database.** `SettingsRepository.get_retention()/update_retention()` read/write `system_settings.operational_telemetry_retention_days`; live `information_schema` count = 0 because `20260924000000_p8x_x2_operational_telemetry_retention.sql` is unapplied. | `backend/data/settings.py:26-29,64-93` · live column + ledger · CFG-1 | `GET/PUT /api/v3/settings/retention` and the ops retention tab are **predicted to fail with `UndefinedColumn`** against the durable flagship — i.e. a ratified configurable surface (N3) that cannot be administered. | PO+IMPL | Fold into GA-01 (apply the migration), then **execute** the endpoint to convert PREDICTED into VERIFIED |
| **GA-03** | **HIGH** | **Upload limits are not configurable in practice.** `routes/upload.py` reads `settings_json`, `max_file_size_mb`, `allowed_file_types`, `enable_auto_repair`, `max_batch_files`, `max_total_batch_size_mb` — **none of the first six are columns** — and uses `.maybe_single()`, so it falls back to hard-coded 50 MB / 20 files / 200 MB / 365 days. Conversely `max_upload_size_mb`, `max_batch_size_mb`, `max_file_upload_daily`, `max_documents_per_batch`, `max_pages_per_document` are read by **nothing**. | `backend/routes/upload.py:39-80` · live column list · CFG-3 | Effective upload policy is a code literal, not an administered value: the PO cannot change it through the control plane, and the schema implies a control that does not work. | PO+IMPL | POD-M: ratify the authoritative object (typed columns vs key/value payload) and the approved limits; then wire one path and remove the other |
| **GA-09** | MEDIUM | **37 more `system_settings` columns are inert** (no read path in either tree): localisation (`default_language`, `default_timezone`, `date_format`, …), tax (`carbon_tax_*`, `default_tax_*`, `default_vat_rate`), password/session/2FA policy, webhook retry, API rate limits, legacy SLA/backup columns. | per-name grep across `backend/`, `frontend/src`, `admin/src` · CFG-4 | The control plane *appears* far more configurable than it is; operators can "save" policy that changes nothing (AGENTS §43/§47 tension). | IMPL | For each column: wire it to a read path or mark it non-configurable in the UI; do not leave silent no-ops |
| **GA-10** | MEDIUM | **Commercial configuration is partially unset** and has no transactions: `storage.additional_rate_per_gb`, `standard_allowance.monthly_processing_units`, `.additional_rate`, `credit_policy.rollover.expiry_months`, `max_carryover_pct` all `null`; all billing transactional tables 0 rows. | live `billing_commercial_config` · CFG-8 | Storage overage, allowance overage and credit expiry have **no approved basis**; the engine cannot price an overage. | PO | POD-K: ratify the commercial terms, then persist them and test one overage calculation |
| **GA-08** | MEDIUM | **Retention is stored twice in the same row** — typed columns (audit 1 / data 365 / document 365 / backup 365) *and* `setting_value` JSONB with the same four numbers. Only the typed path is written. | live row dump · `data/settings.py` update path · CFG-2 | An unmaintained second source of truth that will silently diverge; a future reader may trust the wrong copy. | IMPL | Choose one representation (POD-N with POD-M) and remove or generate the other |
| **GA-17** | MEDIUM | **`platform_retention.audit_log_retention_days = 1`** against 365 for data, documents and backups. | live `system_settings` · CFG-5 · R5 | A one-day audit horizon is in direct tension with AGENTS §42 (audit/evidence traceability must not be weakened) and is almost certainly not the intended policy. | PO | POD-E / POD-N: ratify the audit retention value before any enforcement is switched on |
| **GA-24** | LOW | **CORS is hard-coded** (10 origins, not environment-overridable) and the `https://*.onrender.com` entry is **inert** because Starlette matches `allow_origins` exactly and no `allow_origin_regex` is set. | `backend/config.py:23-36` · `backend/main.py:175-183` · CFG-7 | The intended deploy convenience does not work; no credentialed wildcard exists (correct), but the misconfiguration is misleading. | IMPL | Move origins to configuration and either implement the wildcard via regex or delete the dead entry |
| **GA-25** | LOW-MED | **The plan catalogue mixes currencies** — GBP (v1) rows and USD (v2) rows live simultaneously while `system_settings.default_currency = 'GBP'`. | live `billing_plans` · CFG-9 | Ambiguous pricing basis for any quote or invoice. | PO | POD-L: single currency per catalogue, or explicitly dual-currency plans |
| **GA-26** | LOW-MED | **`FOUNDER_EMAIL` defaults to a personal address compiled into the release tree** and is the default notification recipient when unset. | `backend/config.py:20` · CFG-6 | A personal address can function as platform policy and leaks a personal identifier into the release artefact. | PO | POD-O: ratify per-environment sender/recipient identities; set them by environment variable |

`CFG-10` (settings introduced by the unapplied migrations are unverifiable durably)
is the configuration face of **GA-01** and is deliberately **not** duplicated as its
own row.

### 2.4 Functional and implementation gaps (from the truth-state distribution)

Deliverable 1 records **354 feature rows**: `IMPLEMENTED_AND_WIRED` 313 ·
`PARTIALLY_IMPLEMENTED` 17 · `DOCUMENTED_ONLY` 9 · `HISTORICAL_ONLY` 5 ·
`IMPLEMENTED_BACKEND_ONLY` 4 · `SCHEMA_ONLY` 4 · `SUPERSEDED` 1 · `DEPRECATED` 1 ·
`CODE_ONLY` 1 · `PRESENT` 1.

| ID | Sev | Gap | Evidence | Impact | Owner | Closing action |
|---|---|---|---|---|---|---|
| **GA-11** | MEDIUM | **17 `PARTIALLY_IMPLEMENTED` rows are untriaged.** Each is held back by a PO decision, an unapplied migration, or a missing surface. | flag §6.2 · per-row `Truth` column | A long tail of half-finished capability is exactly what makes an inventory look complete while workflows stall mid-journey. | PO+IMPL | Triage all 17: each becomes either a `GA` row, a `POD` decision, or a closed item with evidence |
| **GA-12** | MEDIUM | **4 `IMPLEMENTED_BACKEND_ONLY` + 1 `CODE_ONLY` capability have no verified wired surface.** The engine/service exists; no UI or route is confirmed to reach it. | flag §6.2 · CAP-120-style classification | Capability that cannot be exercised is indistinguishable from absent capability to a customer (AGENTS §74). | IMPL | For each: wire a surface and test it, or reclassify as internal/out of scope |
| **GA-13** | MEDIUM | **4 `SCHEMA_ONLY` objects are unused/empty — including the `roles` catalogue (0 rows in both environments).** RBAC behaviour is live, but enforced from membership rows and `staff_roles.permissions` (jsonb), not from `roles`. | flag FTR-057/FTR-301 · §5.0 baseline · T6 · R3 | Two role sources, one empty: a reader can conclude RBAC is unimplemented, and role→permission mapping has no populated single source (AGENTS §9/§14). | PO | POD-C: populate the catalogue as the authoritative source, or formally retire it |
| **GA-14** | MEDIUM | **`accounting_dimensions` naming drift:** documented as a table, implemented as **10 added columns** on `calculation_snapshots` / `emissions_logs` (P17-A is an `ALTER TABLE`); a table of that name holds **0 rows in all 78 databases**. | flag §5.3 · T2 · R2 | Any artefact written against an "`accounting_dimensions` table" will not work; docs-vs-schema divergence is a real traceability defect. | PO+IMPL | POD-B: declare the columns authoritative (and fix the docs) or create the table |
| **GA-15** | MEDIUM | **"Locations" vs Facilities information-architecture drift.** AGENTS §34/§35 and D17 speak of Locations; the flagship has `facilities` and **no** `locations` table. | flag T4 · R4 · live flagship inventory | Master-data IA and the data model disagree, and §35 requires optional fields to yield 4xx validation rather than raw database errors — a guarantee that must be demonstrated on the real entity. | PO | POD-D: decide separate entity vs facility facet, then align docs, schema and validation behaviour |
| **GA-18** | LOW-MED | **PE terminology conflict:** *Processing Entity* (AGENTS §8/§12, `processing_entities`, PE workspace, PE roles) vs *Principal / Reporting Entity* (census CAP-065/CAP-066 and part of the domain language). | flag T1 | A PE is an **operational actor**; a reporting/principal entity is an **accounting boundary**. Conflating them corrupts both the role model and the reporting model. | PO | POD-F: ratify one term and one concept per meaning; correct catalogue and docs |
| **GA-19** | LOW-MED | **The deprecated legacy admin control plane is still served.** PO `D-P2-02` deprecates the 19-screen legacy admin CRA, yet the `vercel.json` `/admin` rewrite still routes to it and it remains catalogued as live features (D45). | flag T5 · `vercel.json` · D45 · AGENTS §31 | Deprecation is a *decision*, not a deployment fact: a privileged legacy surface remains reachable while the ratified control plane is elsewhere. | PO+IMPL | POD-G: confirm the retirement path and the `/admin` rewrite end state; then remove or redirect it |
| **GA-20** | LOW-MED | **Legacy artefact disposition undecided** — Prisma lineage (`prisma/`, `schema.sql`, `CarbonTally_DB_Schema_V3M2.sql`), backups, `carbon-tally-ui-demo`, scratch outputs. | flag §5.4 · `PRESENT` row · POD-H | Superseded schema artefacts can be mistaken for authority; untouched artefacts complicate retention and audit (AGENTS §42/§79). | PO | POD-H: record a disposition (delete / archive / mark non-authoritative) per artefact class |
| **GA-21** | LOW-MED | **No exhaustive role→permission matrix.** Role surfaces in deliverable 3 are *representative* `FTR` ranges, not a per-permission specification. | FTR-GAP-6 · trace §4 | Security verification (AGENTS §45) needs an authoritative permission matrix to test ALLOW/DENY per role; without it negative testing is guesswork. | IMPL | Produce a per-capability × per-role matrix from the authoritative source and use it as the negative-test oracle |
| **GA-29** | MEDIUM | **No boundary refusal has been executed.** All 16 forbidden-path rows are `TRACED — NOT EXECUTED`: each has a designed refusal and a named enforcement layer, but no ALLOW/DENY outcome was observed. | trace §6 · AGENTS §45/§73 | Security posture is currently a *design* claim. AGENTS §45 treats every unexpected ALLOW as a serious finding — discoverable only by executing the refusals. | IMPL | Execute all 16 rows as negative tests (disposable environment or isolated QA records) and record ALLOW/DENY with evidence |

### 2.5 Traceability gaps (`FTR-GAP-1…6`) and their disposition

| Source gap | Statement | Disposition in this document |
|---|---|---|
| `FTR-GAP-1` | 3 capabilities (CAP-010 SEO/PWA, CAP-122 X7 runtime metrics, CAP-148 shared table/pagination standard) have no individual feature row | Carried as **GA-23** (LOW) — PO decision POD-J |
| `FTR-GAP-2` | The pipeline is traceable and **partially** populated, while the automatic state machine, evidence, QC and approval are empty or absent | Split into **GA-04** (HIGH) and **GA-05**/**GA-06** (HIGH) |
| `FTR-GAP-3` | The commercial flow is traceable but unexercised, and its policy inputs are `null` | Carried as **GA-10** (MEDIUM) + **GA-28** (LOW-MED) |
| `FTR-GAP-4` | The `CAP → FTR` join is analyst-derived, not machine-generated | Carried as **GA-22** (LOW) |
| `FTR-GAP-5` | Settings/features living only in the 43 unapplied migrations cannot be traceability-confirmed durably | Carried as **GA-01** (HIGH) |
| `FTR-GAP-6` | Role surfaces are representative ranges, not per-permission matrices | Carried as **GA-21** (LOW-MED) |

### 2.6 Naming and terminology gaps (`T1–T6`)

| Source | Conflict | Disposition |
|---|---|---|
| `T1` | PE = Processing Entity vs Principal/Reporting Entity | **GA-18** (needs POD-F) |
| `T2` | `accounting_dimensions` documented as a table, implemented as columns | **GA-14** (needs POD-B) |
| `T3` | Legacy `product_categories` vs P17-10 product/contract reporting dimensions | Absorbed into **GA-01/GA-07** (the P17 dimensions are class **C**) plus the explicit warning already carried in deliverable 1 §5.3 — *do not conflate them* |
| `T4` | "Locations" as a distinct master-data entity | **GA-15** (needs POD-D) |
| `T5` | Two admin surfaces; legacy CRA deprecated but still served | **GA-19** (needs POD-G) |
| `T6` | `roles` empty while role behaviour is live | **GA-13** (needs POD-C) |

### 2.7 Remaining LOW gaps

| ID | Sev | Gap | Evidence | Impact | Owner | Closing action |
|---|---|---|---|---|---|---|
| **GA-22** | LOW | **The `CAP → FTR` join is analyst-derived, not machine-generated.** | FTR-GAP-4 · trace §0.2 | The mapping is auditable but not self-validating; it must never be quoted as an authoritative index. | IMPL | Optionally generate the join from the FTR table and the census, so the mapping is reproducible |
| **GA-23** | LOW | **3 residual capabilities remain uncatalogued** — CAP-010 (SEO/PWA), CAP-122 (X7 runtime metrics), CAP-148 (shared table/pagination standard). | FTR-GAP-1 · POD-J · AGENTS §36 | A reader could assume they are catalogued commercial capabilities; the table/pagination standard is the one with real operational UX weight. | PO | POD-J: catalogue them as features or declare them out of scope |

---

## 3. Prioritised remediation sequence

Ordering follows dependency and evidence value, not effort. **No step may point a
destructive harness at durable data** (AGENTS §55.1); every execution step below is
to be run against a disposable clone or isolated, labelled, cleaned-up QA records.

| Wave | Purpose | Items | Exit criterion (evidence required) |
|---|---|---|---|
| **W0 — Decide** | Unblock everything that needs a product/business answer | POD-A, POD-B, POD-C, POD-D, POD-E, POD-K, POD-L, POD-M, POD-N, POD-O (see §4) | Written PO decisions recorded; each `GA` row moves to `IMPL` with a ratified target |
| **W1 — Durability** | Make one environment represent the release tree | **GA-01** (apply 43 migrations, filename order, backed up), then **GA-07** (declare it authoritative), **GA-02** (endpoint now executable), **GA-16** (production inspection) | Ledger arithmetic closes (89 = 89) on the declared durable environment; `information_schema` contains `operational_telemetry_retention_days`; environment table in deliverable 1 §5.3 re-run |
| **W2 — Configuration truth** | One authoritative source per policy value | **GA-03** (upload limits), **GA-08** (retention duplication), **GA-09** (37 inert columns), **GA-17** (audit retention) | Administered value demonstrably changes behaviour (test: change limit → observe enforcement); no inert "save" controls remain |
| **W3 — Prove the pipeline** | Convert the core claim from traced to observed | **GA-04** (automatic run with retry/resume evidence), **GA-05** (evidence materialised), **GA-06** (approval + QC cycle), **GA-27** (audit target) | Per-stage row counts before/after, `attempt_count`/retry evidence, a persisted evidence set, approval and QC records — captured in a disposable environment and reported with Git SHA |
| **W4 — Prove the boundaries** | Convert security posture from design to tested | **GA-29** (all 16 forbidden paths executed), **GA-21** (permission matrix as oracle), **GA-13** (role source) | ALLOW/DENY recorded per row; **every unexpected ALLOW raised as a serious finding** (AGENTS §45) |
| **W5 — Commercial & integration** | Exercise the remaining flows | **GA-10**, **GA-28** (billing/SLA/white-label), **GA-25** (currency) | One pricing/overage outcome and one white-label flow produce persisted records |
| **W6 — Hygiene & clarity** | Remove misleading surfaces and drift | **GA-11**, **GA-12**, **GA-14**, **GA-15**, **GA-18**, **GA-19**, **GA-20**, **GA-22**, **GA-23**, **GA-24**, **GA-26** | Each closed, or reclassified with a dated decision; no deprecated surface reachable without a stated reason |

---

## 4. Consolidated Product Owner decision register

Fifteen decisions are open across the three catalogues (`POD-A…POD-O`). **None of
them was answered by this analysis** — AGENTS §62 forbids inventing business policy.
The final column is an *engineering recommendation*, offered as input, not as a
decision.

| ID | Decision | Blocks | Recommendation (input only) |
|---|---|---|---|
| **POD-A** | Which durable environment carries the 43 unapplied migrations, in what order and under what authorisation | GA-01, GA-02, GA-07, GA-16 | Designate **one** durable environment, back it up first, apply in filename order, re-run the ledger arithmetic; keep clones disposable |
| **POD-B** | `accounting_dimensions`: ratify the 10 columns as authoritative, or require a table | GA-14 | Ratify the columns (they are already how the applied schema works) and correct the documentation instead of adding a duplicate object |
| **POD-C** | `roles` catalogue: populate it as the RBAC source, or formally retire it | GA-13 | Retire the empty table and document membership + `staff_roles.permissions` as authoritative — the least-change, least-duplication option |
| **POD-D** | Locations: separate entity or a facet of Facilities | GA-15 | Decide against D17 wording; then align schema, UI labels and validation so §35's 4xx guarantee is demonstrable |
| **POD-E** | Audit retention: does `audit_log_retention_days = 1` stand | GA-17 | Almost certainly raise it; a one-day audit horizon conflicts with §42's auditability requirement |
| **POD-F** | PE terminology: Processing Entity vs Principal/Reporting Entity | GA-18 | Keep *Processing Entity* for the operational actor (it matches schema and code); use a separate term for the accounting boundary |
| **POD-G** | Legacy admin control plane: retirement path and the `/admin` rewrite end state | GA-19 | Confirm `D-P2-02`; then remove the rewrite so the ratified control plane is the only privileged surface |
| **POD-H** | Legacy artefact disposition (Prisma lineage, backups, demo app, scratch outputs) | GA-20 | Mark superseded schema artefacts explicitly non-authoritative; archive rather than delete where history matters |
| **POD-I** | Production schema/migration expectations, and who verifies them | GA-16 | Authorise a read-only inspection and record the delta against the release tree |
| **POD-J** | Residual capabilities (SEO/PWA, X7 runtime metrics, shared table/pagination standard): catalogue or out of scope | GA-23 | Catalogue the table/pagination standard (§36 has operational weight); treat the other two as declared scope items |
| **POD-K** | Commercial terms: storage overage rate, allowance size and overage rate, credit expiry, carry-over cap | GA-10, GA-28 | Required before the billing engine can price an overage; set values, then test one overage |
| **POD-L** | Plan catalogue currency: single currency, or explicit dual-currency plans | GA-25 | Prefer one currency per catalogue version; if dual is intended, state it in the plan model |
| **POD-M** | Authoritative object and values for upload limits | GA-03 | Ratify the typed `system_settings` columns as authoritative and delete the key/value read path (or the reverse) — one path only |
| **POD-N** | Retention values for audit, operational telemetry, data, documents, backups (including the PX-7 initial 90 days) | GA-02, GA-08, GA-17 | Ratify one set; store it once; initialise operational telemetry to the PX-7 90-day value in schema |
| **POD-O** | Platform notification sender/recipient identity per environment | GA-26 | Set by environment variable per environment; remove the compiled personal-address default |

**Ratified decisions this analysis must not reopen.** `N3` (retention is
configurable and enforced server-side); `PX-7 Option (a), 2026-09-14`
(operational telemetry retention configurable, initial 90 days — expressed as a
schema default, not a code literal); PO `D-P2-02` (legacy admin CRA deprecated);
the same P8X-X2 migration records **"Production is PROHIBITED (G0-D open)"** for
that workstream — a constraint preserved here, not reversed.

---

## 5. Claims deliberately NOT made

Over-claiming in a gap analysis is itself a defect (AGENTS §73/§74). The following
are therefore recorded as **not asserted**, so no reader infers them:

| Not asserted | Why not |
|---|---|
| That any workflow **runs correctly end-to-end** | No workflow was executed (GA-04, GA-06, GA-29) |
| That any **boundary refusal works** | 16 boundaries are traced, none executed (GA-29) |
| That the platform is **insecure** | No penetration test was performed; the configured CORS surface contains no credentialed wildcard, and 174 RLS policies are present — that is *design* evidence, not a security verdict |
| That production **matches** the release tree — or does not | Production was never contacted (GA-16) |
| That the catalogued features are **absent** from production | Their production state is `UNKNOWN`, not `ABSENT` |
| That data was **lost or corrupted** anywhere | No destructive operation was performed or observed |
| That the demo/investor dataset is **invalid** | It was inspected read-only; no defect in it was established |
| That the empty tables are **bugs** | `0 rows` proves *unexercised*, not *broken*; the distinction is made explicitly in §5.0 of deliverable 3 |
| That any **secrets** were exposed | No secret, key, JWT or signed URL appears in any deliverable |

## 6. Verification limits and how each gap class is closed

| Class of gap | Current evidence | What closes it |
|---|---|---|
| Durability (GA-01, GA-07, GA-16) | Ledger arithmetic, live table inventories | Applying migrations to a declared durable environment, then re-running the same read-only probes |
| Configuration (GA-02, GA-03, GA-08…GA-10, GA-17, GA-24…GA-26) | Code-vs-schema comparison (`VERIFIED(schema)/PREDICTED(runtime)`) | Executing the affected endpoints and observing enforcement |
| Runtime behaviour (GA-04…GA-06, GA-27, GA-28, GA-29) | Live row counts proving non-execution | Executing the workflows and boundaries, capturing rows, retries and ALLOW/DENY |
| Functional residue (GA-11…GA-15, GA-18…GA-23) | Catalogue truth states and live schema | Triage plus PO decisions; then re-catalogue each row with dated disposition |
| Documentation/naming (GA-14, GA-18, GA-22, GA-23) | Document-vs-schema comparison | Correcting the artefacts against the ratified model |

## 7. Hand-back

| Item | Value |
|---|---|
| Document | `docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md` |
| Gaps registered | **29** — HIGH **6** · MEDIUM **13** · LOW-MEDIUM **7** · LOW **3** |
| Sources consolidated | `FTR-GAP-1…6` · `CFG-1…10` · `R1…R7` · `T1…T6` · persistence classes `A…E` · truth-state distribution |
| PO decisions consolidated | **15** (`POD-A…POD-O`), none answered here |
| Remediation waves defined | **7** (W0 decide → W6 hygiene) |
| Live evidence re-used | Flagship `postgres` (116 public tables) and clone `ct_p17k_20260926` (145 public tables), counts taken read-only |
| Secrets reproduced | **None** |
| Writes performed | **None** |
| Verification posture | Consolidation of three prior deliverables + live read-only verification; no workflow, endpoint or boundary executed |
| Verdict for this deliverable | `GAP_ANALYSIS_COMPLETE_WITH_29_REGISTERED_GAPS` |

**The single most important sentence in this document.** CarbonTally's feature
inventory is real and substantial — but its *core* claim to commercial value, the
automatic processing pipeline with evidence and approval, is **currently traced in
source and empty in data**. Until W1–W4 of §3 are executed and evidenced, no
completion or acceptance claim about the pipeline is supported.

<!--CTEOF-->


