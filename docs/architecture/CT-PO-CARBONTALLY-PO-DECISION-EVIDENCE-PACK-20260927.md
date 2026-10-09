# CT-PO-CARBONTALLY-PO-DECISION-EVIDENCE-PACK-20260927

> Read-only product-governance analysis. **No Product Owner decision is made,
> selected, ranked or recommended in this document.** Where documentation contains
> an engineering opinion it is labelled `ENGINEERING INPUT — NOT A PO DECISION`.

## 1. Task identity

| Item | Value |
|---|---|
| Task ID | `CT-PO-DECISION-01-20260927-CARBONTALLY-PO-DECISION-EVIDENCE-PACK` |
| Purpose | Determine which registered `POD` items are genuine Product Owner decisions, which are not, and what the PO actually has to answer |
| Question answered | "Given everything currently known about CarbonTally, what decisions actually need to be made by the Product Owner, what decisions do NOT belong to the Product Owner, and what information should be presented before each genuine PO decision?" |
| Posture | **Read-only forensic / governance.** No code, schema, data, configuration, migration, deployment, Git or production mutation |
| Primary repository | `/home/shomonrobie/ct_93d5cdd` — branch `p8-release-reconciled`, HEAD `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Historical repository | `/home/shomonrobie/carbon_tally` — branch `main`, HEAD `20b7a928bb73fdfacf8271ff537a8fd245f62c79` |
| Working-tree state | `ct_93d5cdd`: **47** modified/untracked entries when this task began (1 modified `.gitignore`, 46 untracked), rising to **50** by hand-back: +1 this deliverable, +2 outputs written mid-task by the concurrent `CT-FEATURE-02` task (see §14 note). Neither tree was modified by this task |
| Deliverable | `docs/architecture/CT-PO-CARBONTALLY-PO-DECISION-EVIDENCE-PACK-20260927.md` |
| PODs reviewed | **15** (`POD-A` … `POD-O`) + a parallel **18**-item census register (`POD-001` … `POD-018`) mapped for completeness |
| Verdict | see §22 |

**What this document is not.** It is not a PO decision, not a business
recommendation, not a re-audit of D1–D5, and not the independent technical
verification that `CT-FEATURE-02` is performing concurrently.

---

## 2. Evidence sources

### 2.1 Primary source documents (5 — the immediate source set)

| # | Document | Extent |
|---|---|---|
| 1 | `CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` | 1,190 lines / 150,660 bytes · 354 `FTR` rows · `POD-A…POD-J` |
| 2 | `CT-PO-CARBONTALLY-CONFIGURATION-CATALOGUE-20260927.md` | 422 lines / 30,816 bytes · `CFG-1…CFG-10` · `POD-K…POD-O` |
| 3 | `CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md` | 478 lines / 37,435 bytes · §5.0 population baseline · 16 boundary rows |
| 4 | `CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md` | 309 lines / 35,223 bytes · 29 `GA` rows · §4 register (15 PODs) |
| 5 | `CT-PO-CARBONTALLY-FINAL-REPORT-20260927.md` | 217 lines / 15,437 bytes · §7 PO decision queue |

### 2.2 Prior/adjacent documents consulted (27)

Census and ledger family: `CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md`
(register §11.2, 18 items), `…-REPORT.md`,
`CT-PO-CARBONTALLY-CENSUS-INDEPENDENT-VERIFICATION-20260926.md`,
`CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926.md`,
`CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md`,
`CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md` / `…-LEDGER.md`,
`CT-PO-MASTER-WORKPLAN-20260925.md`.

Decision-register family: `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md`
(§32 unresolved items · D21 terminology · D22 · D43 · D47 · known decisions 13–22),
`docs/audit/openhands/ui-ux/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`
(§24 N1 · §25 N2), `docs/audit/openhands/ui-ux/README.md`,
`docs/audit/openhands/ui-ux/MASTER_UX_DECISION_RECONCILIATION_REPORT.md`.

Audit/verification family: `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md`,
`docs/audit/cline/CARBONTALLY_V3_PUBLIC_WEBSITE_AND_ARCHITECTURE_AUDIT.md`,
`docs/audit/cline/CARBONTALLY_V3_GIT_REPOSITORY_AUDIT_AND_RELEASE_READINESS_REPORT.md`,
`docs/audit/cline/CARBONTALLY_V3_POST_IMPLEMENTATION_MASTER_UX_AUDIT.md`,
`docs/audit/cline/CARBONTALLY_V3_FINAL_IMPLEMENTATION_REPORT.md`,
`docs/audit/cline/CARBONTALLY_V3_INVESTOR_DEMO_DATA_REPORT.md`,
`docs/audit/openhands/CARBONTALLY_V3_UI_VISUAL_ACCEPTANCE_AUDIT.md`,
`docs/audit/openhands/CARBONTALLY_V3_PE_SECURITY_AUDIT.md`,
`docs/cline/CARBONTALLY_V3_PHASE2_COMPLETION_MATRIX.md`,
`docs/cline/reports/CT-P8-FINAL-PROGRAMME-REPORT-20260914-057.md`,
`docs/cline/reports/CT-P8-G0-GATE-RECONCILIATION-20260914-042.md`,
`docs/cline/reports/CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017.md`,
`docs/cline/reports/P8-FINALIZATION-RECON-001.md`,
`docs/cline/prompt-history/CT-PROD-PUBLICATION-RECON-20260911-001.md`,
`docs/ohd/reports/CT-P8-CURRENT-STATE-GAP-RECONCILIATION-AND-CONSULTANT-CLIENT-PARITY-20260915.md`,
`docs/architecture/CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md`,
`docs/architecture/CARBONTALLY_PHASE8X_X7_API_RUNTIME_METRICS_CONTRACT_20260915.md`,
`docs/architecture/CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md`,
`docs/architecture/CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md`,
`docs/architecture/CT-PO-P12-STEP1-DOCUMENTATION-RECONCILIATION-20260924.md`,
and the workspace `AGENTS.md`.

### 2.3 Source / migration artefacts inspected (16)

`backend/config.py` · `backend/data/settings.py` · `backend/api/v3_settings.py` ·
`backend/routes/upload.py` · `backend/routes/admin/settings.py` ·
`backend/data/billing.py` · `backend/services/billing.py` · `backend/domain/billing.py` ·
`backend/data/notifications.py` · `backend/utils/email.py` · `backend/services/v3_email.py` ·
`backend/routes/notifications.py` · `backend/data/staff.py` · `backend/auth.py` ·
`supabase/migrations/00000000000000_init_schema.sql` ·
`supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql` ·
`frontend/src/v3/admin/LocationsTab.jsx`.

**Search posture:** the 5 primary documents were read in depth (targeted sections);
the 27 prior documents were consulted by targeted search/read rather than full read.
Every claim below cites the artefact it came from. No database was queried by this
task: all row counts, column inventories and ledger figures are quoted from D2/D3/D4,
which took them read-only on 2026-09-27.

---

## 3. Important truth-status limitations

These limitations bound every classification in this pack.

| # | Limitation | Consequence for PO decision-making |
|---|---|---|
| L1 | **The 354-feature catalogue is not independently verified.** Its truth states (`IMPLEMENTED_AND_WIRED` 313 · `PARTIALLY_IMPLEMENTED` 17 · etc.) were produced by Cline. `CT-FEATURE-02` is running concurrently to detect false `IMPLEMENTED_AND_WIRED` claims; its result does not exist yet | No PO question in this pack is answered *from* a catalogue truth state alone. Where a question would change if a wiring claim proved false, that is stated (§14) |
| L2 | **Production was never contacted.** Every `PROD:` truth state is `UNKNOWN`. Documentary production facts are limited to the public site and API host names quoted in D1 §1.3 | No claim of production parity, drift, readiness or absence is made or relied upon (§15, PO-AUTH-03) |
| L3 | **Documentary registers are design authority, not runtime proof.** N1, N2, N3, D-P2-02, D43, D47 etc. are recorded in decision registers; their *implementation* state is separately evidenced and sometimes stale (e.g. X2/X7 contract records still read "BLOCKED" while the services exist) | `ALREADY_RATIFIED` below means *the decision is closed*, **not** that its implementation is verified |
| L4 | **Two registers, colliding labels.** D1–D3's register is `POD-A…POD-O` (15). The 2026-09-26 capability census has its own `POD-001…POD-018` (18), and D1 §6.3 explicitly says its numbering is distinct — yet feature rows cite census `POD-0xx` labels beside `POD-A…J` | Every POD reference in this pack is prefixed by its register (`A–O` = deliverable register; `census` = capability census) |
| L5 | **Decision-label collisions in the audit registers.** `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` uses **D21 for "Canonical terminology"**, while the frozen UX baseline (AGENTS §63) uses **D21 for the unified design system**; the same register also cites "D21 primitives" for UI. D-numbers are therefore not globally unique | Ratification claims below cite the register *and* the section, never a bare `Dxx` |
| L6 | **D2/D3/D4 database figures are point-in-time** (read-only probes, 2026-09-27; flagship `postgres` 116 public tables; disposable clone `ct_p17k_20260926` 145). This pack re-executed no probe | Counts are quoted as evidence, not re-asserted as current |
| L7 | **No durable environment represents the release tree** (D4 GA-01/GA-07: 89 migration files in Git, flagship ledger 46 rows, ledgers unreadable in 4 of 6 local environments) | Several PODs have a *policy* answer available now and an *execution* step that is not (§20) |
| L8 | **Read-only posture.** Nothing was executed: no endpoint, workflow, boundary, migration, seed, DDL, DML, deploy, commit or configuration change | All behavioural statements remain source/schema claims, consistent with AGENTS §73/§74 |
| L9 | **Register completeness.** A–O is not the only open queue: the census register still lists 18 items, three of which have no A–O equivalent and materially affect execution (§4.3) | The PO should treat §4.3 as part of the same queue |

---

## 4. Current POD register

### 4.1 The deliverable register — `POD-A` … `POD-O` (15)

| ID | Subject as currently registered | Raised by | Register's own framing |
|---|---|---|---|
| `POD-A` | Which durable environment carries the 43 unapplied migrations, in what order/authorisation | D1 §6.3 · D2 CFG-10 · D4 GA-01 | "Changes durable data; AGENTS §55.1 forbids pointing destructive harnesses at durable data" |
| `POD-B` | `accounting_dimensions`: ratify the 10 columns as authoritative **or** require a table | D1 §1.2, T2, R2 · D4 GA-14 | "Product/architecture semantics (T2)" |
| `POD-C` | `roles` catalogue: populate it, or formally retire it | D1 T6, R3 · D4 GA-13 | "Authoritative RBAC source (T6)" |
| `POD-D` | Locations: separate entity vs facility facet | D1 T4, R4 · D4 GA-15 | "Information architecture (D17/T4)" |
| `POD-E` | Retention: `audit_log_retention_days = 1` vs 365 for data/documents/backups | D1 R5 · D2 CFG-5 · D4 GA-17 | "Conflicts with auditability expectations (AGENTS §42)" |
| `POD-F` | PE terminology: Processing Entity vs Principal/Reporting Entity | D1 T1 · D4 GA-18 | "Cross-cutting naming (T1)" |
| `POD-G` | Legacy admin control plane: confirm retirement path and the `/admin` rewrite's end state | D1 T5 · D4 GA-19 | "AGENTS §31 + PO D-P2-02" |
| `POD-H` | Legacy artefact disposition (Prisma lineage, backups, `carbon-tally-ui-demo`, scratch outputs) | D1 §5.4 · D4 GA-20 | "AGENTS §42, §79" |
| `POD-I` | Production schema/migration state: is production expected to match the release tree, and who verifies it | D1 §1.3, R7 · D4 GA-16 | "Currently `UNKNOWN`" |
| `POD-J` | Residual capabilities (SEO/PWA, X7 runtime metrics, shared table/pagination standard): catalogue or out of scope | D1 §7.3 · D3 FTR-GAP-1 · D4 GA-23 | "Scope of the commercial product (AGENTS §36)" |
| `POD-K` | Storage overage rate, standard-allowance size and overage rate, credit expiry, carry-over cap | D2 CFG-8 · D4 GA-10, GA-28 | "Commercial terms, not technical settings; the values are absent" |
| `POD-L` | Single currency per plan catalogue, or explicitly dual-currency plans | D2 CFG-9 · D4 GA-25 | "Pricing policy; the versioned plan model can express either" |
| `POD-M` | Which object is authoritative for upload limits, **and** the approved limit values | D2 CFG-3 · D4 GA-03 | "Hard-coded fallbacks (50 MB / 20 files / 200 MB) act as policy by accident" |
| `POD-N` | Retention values for audit, operational telemetry, data, documents, backups (incl. PX-7 90 days) | D2 CFG-1/CFG-5 · D4 GA-02, GA-08, GA-17 | "Retention is configurable by ratified decision (N3); the audit value is extreme" |
| `POD-O` | The platform notification sender/recipient identity for each environment | D2 CFG-6 · D4 GA-26 | "Prevents a personal address from functioning as platform policy" |

### 4.2 What the register mixes together

Every A–O row currently contains at least two of: (i) a product/business policy
value, (ii) an implementation/representation choice, (iii) an authorisation to act,
(iv) a documentation correction. That mixing is why 15 items *look* like 15 PO
decisions. §5–§12 separate the layers.

### 4.3 The parallel census register — `census POD-001` … `POD-018`

The 2026-09-26 capability census lists 18 items "requiring a PO decision"
(`CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md` §11.2). Their status was
**not** re-verified here (AGENTS §80 — historical until re-established). Mapping:

| Census item | Subject | Overlaps | Observation |
|---|---|---|---|
| `POD-001`, `POD-002` | P17 release authorisation; production migration gate | `POD-A`, `POD-I` | Same authorisation family |
| `POD-003`, `POD-016` | 32 uncommitted historical files; historical-tree reconciliation | `POD-H` | Repository governance |
| `POD-004` | Port `tools/seed_investor_demo/` + `DEMO_IDENTITIES.md` into the canonical tree | — | **No A–O equivalent**; touches AGENTS §54 manifest |
| `POD-005` | Legacy API retirement policy (401/407 endpoints) | — | **No A–O equivalent**; product/architecture scope |
| `POD-006` | QA-harness authorisation **and target** | — | **No A–O equivalent**; prerequisite for W3/W4 execution (§20) |
| `POD-007` | Merge `p8-release-reconciled` → `main` | — | Release governance; still unmerged (branch is current HEAD) |
| `POD-008` | Enforce CSP rather than report-only | — | Security-policy authorisation |
| `POD-009` | Retention durations configured | `POD-E`, `POD-N` | Same question, older label |
| `POD-010` | P17-K capability vocabulary as the single canonical vocabulary | — | **No A–O equivalent**; vocabulary governance (CHG-020, `F-1`/`F-2`) |
| `POD-011` | Make the admin console operational (Supabase build settings) | `POD-G` | Partly superseded by the `/ops` control plane (D-P2-02) |
| `POD-012` | Beta-programme fate (`beta_users`, `beta_access_codes`, `/beta-login`) | — | Product-scope question (retire or retain) |
| `POD-013` | Pilot/prototype artefacts retained (UI mockups, legacy admin, Prisma lineage, `carbon-tally-ui-demo`) | `POD-H` | Same question |
| `POD-014` | Nominate the independent verification regime | — | Governance |
| `POD-015` | Workspace-load regression vs P17 release priority | — | Prioritisation |
| `POD-017` | Which role-capability matrix is authoritative for internal staff | `POD-C` (partly) | Contents of the capability matrix — see §8 |
| `POD-018` | Sales-blueprint feature lists marked non-implemented | — | Documentation/roadmap governance |

**Observation (not a decision):** three census items — `POD-005` (legacy API
retirement), `POD-006` (QA-harness authorisation), `POD-010` (canonical capability
vocabulary) — have no representation in the A–O register yet would block or shape
execution. They are carried in §11 and §20 so the PO queue is complete, without
this pack inventing business policy.

---

## 5. POD classification matrix

Exactly one primary category per POD. Where a POD spans layers, the secondary
aspect is named in the final column.

| POD | Current decision | Classification | Genuine PO question | Blocks | Depends on | Prior ratification | Status |
|---|---|---|---|---|---|---|---|
| `POD-A` | Which durable environment carries the 43 migrations, in what order/authorisation | **PO_AUTHORIZATION_ONLY** *(secondary: ENGINEERING_DECISION — migration order/ledger mechanics; product requirement already evidenced)* | None. "May engineering designate one durable environment as authoritative, back it up, and apply the 43 migrations in filename order — including confirming that the regenerable demo data may be affected?" | GA-01, GA-02, GA-07, GA-16, W1, W3 | Authorisation; backup; AGENTS §55.1 | None needed — requirement evidenced by GA-01/GA-07; demo-data regeneration already indicated by the PO | Open — authorisation |
| `POD-B` | `accounting_dimensions`: columns or table | **ARCHITECTURE_DECISION** *(secondary: doc correction; PO scope only if a customer/BI-addressable dimension object is intended)* | None on current evidence | GA-14, R2, T2, and any artefact written against a "dimensions table" | `CT-SCHEMA-01`; `PENDING_COSTRICT_VERIFICATION` (flag only) | — | Open — engineering/architecture |
| `POD-C` | `roles` catalogue: populate or retire | **ENGINEERING_DECISION** *(secondary: the *content* of the capability matrix is product policy — census `POD-017`, GA-21)* | None for the object; capability policy content is a separate PO item (`census POD-017`) | GA-13, GA-21, T6, W4 | `PENDING_COSTRICT_VERIFICATION` (flag only) | Register D43 (ratified role model; `staff_roles.permissions` named as the implementation) | Open — engineering |
| `POD-D` | Locations: separate entity vs facility facet | **ALREADY_RATIFIED** | None | GA-15 (documentation/validation alignment only) | — | **N2** — "PO DIRECTION RESOLVED; ENGINEERING DECISION"; D17 frozen; implemented as facilities reuse and verified PASS in the UX audit | Closed |
| `POD-E` | Audit retention `= 1` | **DUPLICATE_OR_CONSOLIDATABLE** → fold into `POD-N` *(secondary: GENUINE_PO_DECISION — a retention value)* | Covered by `PO-Q01` | GA-17, GA-08 | `POD-N` | N3 (configurable, server-side); D-P2-04 (destructive enforcement deferred) | Closed as a separate item |
| `POD-F` | PE terminology | **ALREADY_RATIFIED** | None | GA-18 (documentation correction) | — | Register "D21 — Canonical terminology" (CURRENT, authority L1: *Customer Organisation, Processing Entity, PE Staff…*); AGENTS §8/§12; D22 | Closed |
| `POD-G` | Legacy admin control plane: retirement path | **ALREADY_RATIFIED** | None *(note the older register §32 entry "final admin surface `/admin` vs `/ops` — UNRESOLVED"; recorded in §19 as a superseded contradiction)* | GA-19 (engineering execution) | — | PO **D-P2-02** (legacy admin CRA deprecated; V3 `/ops` canonical; legacy stays mounted until its retirement conditions are met) | Closed |
| `POD-H` | Legacy artefact disposition | **PO_AUTHORIZATION_ONLY** *(secondary: ENGINEERING_DECISION for archive mechanics; deleting history-bearing artefacts needs explicit authorisation)* | None *(the only PO-relevant act is authorising destruction of history-bearing artefacts)* | GA-20 | Backup/retention context (`POD-N`) | AGENTS §42/§79 (do not delete legacy without reference checks) | Open — authorisation |

| `POD-I` | Production schema/migration state | **PO_AUTHORIZATION_ONLY** *(secondary: engineering/QA performs the inspection and owns the parity expectation)* | None *(the question is authorisation: "do you authorise a read-only production schema/ledger inspection?")* | GA-16 and every `PROD:` claim | Interpretation of the G0-D prohibition (§19) | P8X-X2 migration header: "Production is PROHIBITED (G0-D open)" | Open — authorisation |
| `POD-J` | Residual capabilities: catalogue or out of scope | **DUPLICATE_OR_CONSOLIDATABLE** — split into `J1` SEO/PWA · `J2` X7 runtime metrics · `J3` shared table/pagination standard *(secondary: `J1` is a GENUINE_PO_DECISION; `J2`/`J3` are ARCHITECTURE_DECISION)* | `PO-Q06` (SEO/PWA scope only) | GA-23, FTR-GAP-1 | `J2` relates to the open `PX-6` alerting decision | Register D47 + known decision 15 (DataTable/pagination standardisation is an engineering direction); AGENTS §36 supplies the operational requirement | Split |
| `POD-K` | Commercial terms: storage overage, allowance size/overage, credit expiry, carry-over cap | **GENUINE_PO_DECISION** | `PO-Q02` | GA-10, GA-28, W5 | None (values can be set now) | None announced for these values | Open — PO |
| `POD-L` | Plan catalogue currency model | **GENUINE_PO_DECISION** | `PO-Q03` | GA-25, GA-28, W5 | None | None announced; `billing_plans.currency` is per-plan | Open — PO |
| `POD-M` | Authoritative upload-limit object **and** approved values | **GENUINE_PO_DECISION** (values) *(secondary: ENGINEERING_DECISION — which object is authoritative)* | `PO-Q04` | GA-03, W2 | Engineering decides the object; enforcement currently unreachable | None; hard-coded fallbacks are not a ratification | Open — PO |
| `POD-N` | Retention values: audit / telemetry / data / documents / backups | **GENUINE_PO_DECISION** | `PO-Q01` | GA-02, GA-08, GA-17, W2 | Telemetry *enforcement* needs GA-01 (technical); the telemetry value itself is already ratified | **N3**; **PX-7 Option (a) 2026-09-14** (telemetry initial 90 days as a schema default); **D-P2-04** (destructive enforcement deferred) | Open — PO (remaining domains) |
| `POD-O` | Platform notification sender/recipient identity | **GENUINE_PO_DECISION** *(secondary: ENGINEERING_DECISION — environment-variable mechanism)* | `PO-Q05` | GA-26, GA-28 | Recipients overlap the open `PX-6` alerting policy (§11) | D11-C1 firm-centric recipient model (consultant lifecycle notifications only) | Open — PO |

### 5.1 Classification counts

| Classification | Count | PODs |
|---|---:|---|
| `GENUINE_PO_DECISION` | **5** | `POD-K`, `POD-L`, `POD-M`, `POD-N`, `POD-O` |
| `PO_AUTHORIZATION_ONLY` | **3** | `POD-A`, `POD-H`, `POD-I` |
| `ENGINEERING_DECISION` | **1** | `POD-C` |
| `ARCHITECTURE_DECISION` | **1** | `POD-B` |
| `ALREADY_RATIFIED` | **3** | `POD-D`, `POD-F`, `POD-G` |
| `BLOCKED_PENDING_TECHNICAL_VERIFICATION` | **0** | — (see §10) |
| `DUPLICATE_OR_CONSOLIDATABLE` | **2** | `POD-E` (→`POD-N`), `POD-J` (→`J1`/`J2`/`J3`) |
| `NO_LONGER_REQUIRED` | **0** | — (see §12) |
| **Total** | **15** | |

**Reading:** the register's 15 "PO decisions" reduce to **6 product questions**
(§16 `PO-Q01…PO-Q06`) plus **4 authorisations** (§7 `PO-AUTH-01…PO-AUTH-04`).
Eleven of the fifteen rows are not PO product decisions: five are already decided,
three need authorisation only, one is engineering, one is architecture, and two are
duplicates/splits.

---

## 6. Genuine Product Owner decisions

Five registered PODs remain genuine PO decisions. Each is presented with the same
fifteen fields. **No option is ranked and no business preference is expressed.**

### 6.1 `POD-K` — commercial terms (values absent)

| Field | Content |
|---|---|
| 1. Decision ID | `POD-K` → PO question `PO-Q02` |
| 2. Plain-English question | "What are CarbonTally's commercial terms for storage overage, standard-allowance size and overage, credit expiry and credit carry-over limits?" |
| 3. Why the decision exists | These are commercial policy values, not technical settings. The schema supports them and every one is currently `null`, so the billing engine has no approved basis to price an overage |
| 4. Current evidence | `billing_commercial_config` holds 7 versioned keys; `storage.additional_rate_per_gb` **null**, `standard_allowance.monthly_processing_units` **null**, `.additional_rate` **null**, `credit_policy.rollover.expiry_months` **null**, `max_carryover_pct` **null**; `assisted_pricing` seeded `simple 0.99 / standard 1.99 / complex 3.99` **USD**; every `billing_*` transactional table, `customer_subscriptions` and `consultant_billing` = **0 rows** everywhere. Sources: D2 §3.3, CFG-8; D4 GA-10/GA-28; table created by `20260824020000_d37_0_…`; read via `backend/data/billing.py`, API `/api/v3/commercial/*` |
| 5. What is already known | The mechanism exists and is versioned/effective-dated; the read path is implemented; two value sets *are* configured (credit classes 1/2/4, assisted prices); the default commercial mode is `CREDIT`; credit rollover is enabled with emergency allowance at 10 % |
| 6. What is unknown | The intended values; whether commercial billing is in scope for the near-term product; whether the USD assisted prices (beside GBP storage/allowance rows) are intentional |
| 7. What is **not** the PO's responsibility | Column names, JSONB shape, versioning mechanics, which object stores a value, how an overage is arithmetically computed, migration order, API shape |
| 8. What the decision blocks | GA-10 and GA-28 (W5): no overage can be priced; no commercial flow can be executed end-to-end; any quote or invoice lacks an approved basis |
| 9. Dependencies | None technical to take the decision. Execution depends on a usable environment (GA-01); if currency also changes, on `POD-L` |
| 10. Options supported by evidence | (a) set all values now; (b) set credit/allowance values and defer storage overage; (c) defer commercial configuration entirely and leave the engine unpriced for now |
| 11. Consequences of each option | (a) enables a testable commercial flow; adds values that must then be maintained. (b) narrows what can be tested. (c) nothing changes operationally today (0 transactions), but GA-10/GA-28 stay open |
| 12. Can it be deferred? | Yes — no transactional data exists, so no customer outcome is currently affected. Deferral keeps W5 blocked |
| 13. Must technical verification happen first? | **No.** The fields exist and are documented; the values can be chosen from business intent alone |
| 14. Prior ratifications | None announced for these values. `default_billing_mode = CREDIT` is configured, not ratified |
| 15. Exact source references | D2 §3.3, §6 (CFG-8), §7 (`POD-K`); D4 GA-10, GA-28, §4 register; `supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql`; `backend/data/billing.py`; `backend/services/billing.py` |

### 6.2 `POD-L` — plan catalogue currency model

| Field | Content |
|---|---|
| 1. Decision ID | `POD-L` → PO question `PO-Q03` |
| 2. Plain-English question | "Should each plan catalogue version be priced in one currency, or should CarbonTally deliberately offer plans in more than one currency?" |
| 3. Why the decision exists | The live catalogue mixes currencies while one system-wide default currency is set. Which model is intended is pricing policy, not a defect to be silently normalised |
| 4. Current evidence | Live `billing_plans` (6 rows): Starter v1 GBP 0 · Starter v2 USD 49 · Professional v1 GBP 149 · Business v1 GBP 299 · Business v2 USD 399 · Enterprise v1 GBP 0/custom. DDL: `currency TEXT NOT NULL DEFAULT 'GBP'`, `UNIQUE (plan_code, version)`, effective-dated. `system_settings.default_currency` defaults `'GBP'` with a CHECK constraint limited to `('GBP','EUR')`; `billing_commercial_config.assisted_pricing` is seeded in **USD**. Sources: D2 §3.3–§3.4, CFG-9; `20260824020000_d37_0_…`; `00000000000000_init_schema.sql` |
| 5. What is already known | The versioned model can express either choice (currency is per plan row); Starter v1 is superseded and v2 current, so versioning behaves as designed; `processing_limits` differ between versions |
| 6. What is unknown | Whether the USD rows are intentional (non-UK market), placeholders, or artefacts; whether any customer is quoted in USD today (0 subscriptions exist) |
| 7. What is **not** the PO's responsibility | How currency is stored, column vs reference table, FX mechanics, number formatting, plan-version mechanics |
| 8. What the decision blocks | GA-25 and GA-28 (W5): quotes/invoices have an ambiguous pricing basis; the USD assisted-pricing inconsistency also sits unresolved |
| 9. Dependencies | Coordinate with `POD-K` (storage/allowance currencies are already GBP) |
| 10. Options supported by evidence | (a) one currency per catalogue version; (b) explicit dual-currency support declared in the plan model; (c) single currency now, multi-currency deferred to a later version |
| 11. Consequences of each option | (a) simplest consistent basis; requires deciding which existing rows are authoritative. (b) matches what the live rows already show and requires an explicit product position on quoting/invoicing. (c) defers an unresolved question |
| 12. Can it be deferred? | Yes — no subscription or invoice exists yet |
| 13. Must technical verification happen first? | **No** |
| 14. Prior ratifications | None announced. `billing_plans.currency`'s `'GBP'` is a schema default, not a commercial decision |
| 15. Exact source references | D2 §3.3–§3.4, §6 (CFG-9), §7 (`POD-L`); D4 GA-25; `supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql` (plan DDL + seed); `00000000000000_init_schema.sql` (`system_settings.default_currency` + CHECK) |

### 6.3 `POD-M` — approved upload limits (values half only)

| Field | Content |
|---|---|
| 1. Decision ID | `POD-M` (values) → PO question `PO-Q04`. The *object* half of `POD-M` is engineering (§8) |
| 2. Plain-English question | "What upload limits should CarbonTally enforce for customers — maximum file size, files per batch, total batch size, permitted file types, and any per-day/per-document/per-page quotas?" |
| 3. Why the decision exists | Today the effective limits are code literals, so a code constant is acting as product policy. The PO decides the limits; nobody else can |
| 4. Current evidence | `backend/routes/upload.py` requests `settings_json`, `max_file_size_mb`, `allowed_file_types`, `enable_auto_repair`, `max_batch_files`, `max_total_batch_size_mb` — none of the first six exist as columns — and reads with `.maybe_single()` against a 2-row table, so it falls into its `except` branch: **effective policy is 50 MB per file, 20 files per batch, 200 MB per batch, PDF/CSV/XLSX/JPG/PNG, 365-day data retention**. Columns `max_upload_size_mb`, `max_batch_size_mb`, `max_file_upload_daily`, `max_documents_per_batch`, `max_pages_per_document` are read by **no code path**. `frontend/src/UploadManager.js` and `PDFRepairTool.js` separately enforce `50 * 1024 * 1024`. Sources: D2 §3.1, §6 (CFG-3); D4 GA-03; `backend/routes/upload.py:39–80` |
| 5. What is already known | Exactly what values are enforced today (verified code + schema comparison); the schema already contains candidate columns; 37 further settings columns are inert (GA-09) |
| 6. What is unknown | Whether the PO wants those values; whether any quota concept (daily, per-document, per-page) is wanted at all; whether the admin UI can currently persist an effective change (engineering question) |
| 7. What is **not** the PO's responsibility | Which object is authoritative (typed columns vs key/value payload), how the router reads it, which columns are dropped, how validation failures are surfaced (must be 4xx — an engineering guarantee, GA-03) |
| 8. What the decision blocks | GA-03 and W2: the control plane cannot demonstrate that changing a limit changes behaviour until the values and a single authoritative read path exist |
| 9. Dependencies | Engineering decision on the authoritative object (§8); a usable environment for enforcement testing (GA-01) |
| 10. Options supported by evidence | (a) ratify the currently enforced set (50 MB / 20 files / 200 MB); (b) choose different values; (c) choose values *and* declare some existing columns out of scope/non-configurable |
| 11. Consequences of each option | Any choice makes today's accidental policy explicit; option (c) also reduces the inert-control surface. No option changes enforcement until the read path is fixed |
| 12. Can it be deferred? | Yes, but the accidental-policy condition persists and the admin surface keeps implying control it does not have |
| 13. Must technical verification happen first? | **No for the values.** The values decision is *not* blocked — current effective values are established by direct code/schema comparison. Only the *object* and *enforcement* parts are technical |
| 14. Prior ratifications | None. Hard-coded fallbacks are not a ratification of any limit |
| 15. Exact source references | D2 §3.1, §6 (CFG-3), §7 (`POD-M`); D4 GA-03, GA-09; `backend/routes/upload.py`; `backend/routes/admin/settings.py`; `frontend/src/UploadManager.js`; `frontend/src/components/PDFRepairTool.js` |

### 6.4 `POD-N` — retention policy values (absorbing `POD-E`)

| Field | Content |
|---|---|
| 1. Decision ID | `POD-N` (absorbs `POD-E`) → PO question `PO-Q01` |
| 2. Plain-English question | "How long should CarbonTally retain audit records, operational telemetry, data, documents and backups?" |
| 3. Why the decision exists | Retention duration is business/regulatory policy. Two domains have no ratified value, and one live value (audit = **1 day**) sits in direct tension with AGENTS §42's auditability requirement |
| 4. Current evidence | `system_settings` row `platform_retention`: `audit_log_retention_days` **1**, `data_retention_days` **365**, `document_retention_days` **365**, `backup_retention_days` **365** — duplicated in typed columns **and** a `setting_value` JSONB copy that no verified write path maintains. `operational_telemetry_retention_days` **exists in no durable local database** because `20260924000000_p8x_x2_operational_telemetry_retention.sql` is unapplied, so `GET/PUT /api/v3/settings/retention` is *predicted* to fail with `UndefinedColumn`. Sources: D2 §3.1, §6 (CFG-1/2/5); D4 GA-02/GA-08/GA-17; `backend/data/settings.py`; `backend/api/v3_settings.py` |
| 5. What is already known | **N3** (retention configurable and enforced server-side; durations never invented by code); **PX-7 Option (a)** (telemetry retention configurable, **initial 90 days**, expressed as a schema **default** not a code literal, and `data_retention_days` must not be reused for it); **D-P2-04** (destructive retention enforcement **deferred** — no automatic destructive deletion is active) |
| 6. What is unknown | Intended values for audit, data, document and backup; whether the audit value of 1 was ever intentional; whether/when enforcement is ever enabled |
| 7. What is **not** the PO's responsibility | The telemetry column's existence, the duplicated JSONB copy, typed-columns-vs-key/value representation, the pruning implementation, and the migration that adds the column |
| 8. What the decision blocks | GA-17 (audit horizon), GA-08 (single representation), W2; and any claim that retention is administered — the endpoint cannot be exercised until GA-01 lands |
| 9. Dependencies | GA-01 before the telemetry domain can be *enforced*; engineering choice of one representation (GA-08) |
| 10. Options supported by evidence | (a) one policy set across the five domains; (b) domain-specific values; (c) a policy set plus an explicit statement that enforcement stays deferred |
| 11. Consequences of each option | Every option changes only *stored policy* — no destructive deletion occurs while D-P2-04 stands. Option (c) keeps the ratified non-destructive posture explicit |
| 12. Can it be deferred? | Partly. The audit value is the one the gap analysis flags as almost certainly unintended, so it is the highest-value element to settle; full deferral leaves GA-17 open |
| 13. Must technical verification happen first? | **No for the values** (N3/PX-7 constrain *how*, not *what*). Telemetry *enforcement* is technically blocked by GA-01 and is not part of this decision |
| 14. Prior ratifications | **N3**; **PX-7 Option (a) 2026-09-14**; **D-P2-04** |
| 15. Exact source references | D2 §3.1, §6 (CFG-1/2/5), §7 (`POD-N`, `POD-E`); D4 GA-02, GA-08, GA-17; `00000000000000_init_schema.sql`; `20260924000000_p8x_x2_operational_telemetry_retention.sql` header; `backend/data/settings.py`; `backend/api/v3_settings.py`; AGENTS §42; decision register known decision 20 (D16/N3/D-P2-04) |

### 6.5 `POD-O` — platform notification identity

| Field | Content |
|---|---|
| 1. Decision ID | `POD-O` → PO question `PO-Q05` |
| 2. Plain-English question | "Who should CarbonTally's automated emails and alerts come from, and who should receive platform-level notifications in each environment?" |
| 3. Why the decision exists | A personal address is compiled into the release tree as the default notification recipient, and there is no recorded product decision naming the platform's sender/recipient identity. This is customer-visible identity plus a privacy question |
| 4. Current evidence | `backend/config.py:20` — `FOUNDER_EMAIL = os.getenv("FOUNDER_EMAIL", "shomonrobie@gmail.com")` (a **personal** address, default recipient when unset). Three hard-coded senders: `backend/utils/email.py:23,71`, `backend/routes/notifications.py:75` and `backend/services/v3_email.py:21` all default to `"CarbonTally <notifications@carbontally.co.uk>"`; `v3_email.py` documents that the From address may only be the CarbonTally default **or** a verified sender. White-label sender records exist (`consultant_senders` = **0 rows**). Sources: D2 §4.1, §6 (CFG-6); D4 GA-26; AGENTS §64 (verified senders use existing provider infrastructure; customers own their domains) |
| 5. What is already known | The service mailbox `notifications@carbontally.co.uk` is the coded sender; delivery is via Resend (`RESEND_API_KEY`); consultant customers may in future have their own verified senders (AGENTS §64, D11-C1 recipient model for consultant lifecycle notifications) |
| 6. What is unknown | The intended platform sender identity (service address, role address, or branded address); who owns internal/alert mailboxes per environment; whether any consultant-branded sending is intended and when |
| 7. What is **not** the PO's responsibility | Environment-variable mechanics, secret storage, provider selection, DKIM/SPF/DMARC configuration, template implementation |
| 8. What the decision blocks | GA-26; GA-28's white-label/commercial flow; any claim that notification identity is administered rather than compiled in |
| 9. Dependencies | Related but distinct: the still-open `PX-6` alerting policy (recipients/channels/thresholds — "PO DECISION REQUIRED" per the insight coverage matrix and `D-28`). Recipient intent should be settled consistently with `PX-6` (§11) |
| 10. Options supported by evidence | (a) ratify a platform service address as sender and define a role mailbox (not a personal address) as default recipient; (b) brand senders per environment; (c) additionally permit verified consultant senders for white-label journeys — the schema already provides `consultant_senders` |
| 11. Consequences of each option | Any option removes a personal identifier from platform policy. Option (c) adds white-label capability that is currently unexercised (0 sender rows) |
| 12. Can it be deferred? | Yes for white-label; the personal-address default is the element with the clearest hygiene consequence and is cheap to settle |
| 13. Must technical verification happen first? | **No.** The mechanism (environment variable, verified senders) is documented and the current compiled default is verified in source |
| 14. Prior ratifications | D11-C1 (firm-centric recipients for consultant lifecycle notifications only — does **not** settle the platform identity); AGENTS §64 white-label model |
| 15. Exact source references | D2 §4.1, §6 (CFG-6), §7 (`POD-O`); D4 GA-26, GA-28; `backend/config.py`; `backend/utils/email.py`; `backend/routes/notifications.py`; `backend/services/v3_email.py`; `backend/data/notifications.py`; `docs/architecture/CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md` (`PX-6`, `D-28`) |

---

## 7. PO authorization decisions

These are not product-design questions. The requirement is already evidenced; what
is missing is permission to act. Each item states exactly what the authorisation
would cover and what it would **not** authorise.

| ID | From | Authorisation requested | Covers | Does **not** cover |
|---|---|---|---|---|
| `PO-AUTH-01` | `POD-A` (GA-01/GA-07) | "May engineering designate **one** durable environment as the authoritative environment, take a backup first, apply the 43 unapplied migrations in filename order, and re-run the ledger arithmetic — accepting that regenerable demo data in that environment may be affected?" | Designation of one durable target; backup; ordered application; evidence capture | Choosing *which* database; merging environments; migrating production (`PO-AUTH-03`); pointing a destructive harness at durable data (AGENTS §55.1) |
| `PO-AUTH-02` | `POD-H` (GA-20) | "May superseded repository artefacts be archived or removed, and which classes (Prisma lineage, backups, `carbon-tally-ui-demo`, scratch outputs) may be **destroyed** rather than archived?" | Disposition per artefact class; destruction of history-bearing artefacts | Any schema change; any demo/investor dataset change (AGENTS §54/§55); deleting a still-referenced surface without the reference check AGENTS §79 requires |
| `PO-AUTH-03` | `POD-I` (GA-16) | "Do you authorise a **read-only** production schema/migration inspection, and does that inspection fall inside or outside the `G0-D` prohibition?" | A read-only probe of production schema/ledger; recording the delta against the release tree | Any production migration, deployment, data change or configuration change; any interpretation that `G0-D` is closed |
| `PO-AUTH-04` | `census POD-006` (status not re-verified) | "May the QA/integration harness be executed, and against which **disposable** target?" | Execution of suites against a disposable clone or the dedicated test database | Execution against any data-bearing environment — AGENTS §55.1 makes the harness's `TRUNCATE … RESTART IDENTITY CASCADE` destructive by design |

**Sequencing note (not a business preference):** `PO-AUTH-03` is the cheapest of the
four (read-only, no mutation) and removes the largest block of `UNKNOWN` claims;
`PO-AUTH-01` gates every execution wave; `PO-AUTH-04` gates W3/W4. Authorising an
inspection is **not** a statement that production matches the release tree.

---

## 8. Engineering/architecture decisions

Decisions inside layers that already have a ratified product direction. The PO may
define the *desired outcome*; engineering chooses the mechanism.

### 8.1 `POD-B` — accounting-dimensions representation (**ARCHITECTURE_DECISION**)

- **What must be decided:** whether the ten P17 accounting dimensions stay as
  `ALTER TABLE` columns on `calculation_snapshots` / `emissions_logs` (plus four on
  `emission_factors`, two on `customer_factors`, two on `organizations`), or are
  restructured into a physical dimension object — and the documentation correction
  that follows.
- **Evidence:** P17-A adds ten columns and creates **no table**; a table of that name
  holds 0 rows in all 78 databases; the domain type is used in code
  (`backend/domain/accounting_dimensions.py`, `emissions_logs.py`, `v3_scope2.py`,
  `v3_scope3.py`, `v3_accounting_context.py`) with an `as_columns()` contract; D1 §1.2
  calls it "documentation-vs-schema naming drift, not a schema gap".
- **Why not a PO decision:** product semantics (which dimensions exist, and that every
  calculation preserves them) are already implemented and consumed; only the physical
  representation and the documents disagree.
- **PO-relevant boundary:** if the PO wants an *externally addressable* dimensions
  object (customer-visible or a BI/API contract), that introduces product scope and
  should be raised as a new PO question. Nothing in the evidence shows such a contract.
- **Reference:** D1 §1.2 / T2 / R2; D4 GA-14;
  `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql`;
  `backend/domain/accounting_dimensions.py`.
- `ENGINEERING INPUT — NOT A PO DECISION` (D4 §4 suggests ratifying the columns and
  correcting documentation; recorded as input only).

### 8.2 `POD-C` — RBAC authority object (**ENGINEERING_DECISION**)

- **What must be decided:** whether the empty `roles` table (defined in
  `00000000000000_init_schema.sql`, "Role definitions for RBAC", `permissions` JSONB,
  **no seed insert anywhere**, 0 rows) is populated as a catalogue or formally retired.
- **Evidence:** authorisation resolves from `organization_members` and
  `staff_profiles` → `staff_roles.permissions` (`backend/auth.py:245-254`,
  `backend/data/staff.py`, `backend/api/operations_auth.py`,
  `backend/api/insight_authz.py`, `backend/api/v3_messaging.py`); register D43
  (RATIFIED) names `staff_roles.permissions` as the implementation;
  `backend/api/v3_operations.py::list_staff_roles` already returns
  `{"staff_roles": …, "roles": role_matrix}`.
- **Why not a PO decision:** which object is the RBAC authority is a schema/implementation
  question. The *policy content* (which staff role may do what) is separate and is
  registered as `census POD-017` / GA-21.
- **PO-relevant boundary:** if the PO requires a governed, customer-visible capability
  matrix artefact (FTR-059 `DOCUMENTED_ONLY`), that is a product/documentation
  requirement — raise it explicitly rather than inferring it from the empty table.
- **Reference:** D1 T6/R3; D4 GA-13, GA-21; `00000000000000_init_schema.sql`;
  `backend/auth.py`.
- `ENGINEERING INPUT — NOT A PO DECISION` (D4 §4 suggests retiring the empty table;
  input only).

### 8.3 Other engineering/architecture items carried by PO-classified PODs

| Item | Nature | Why it is not a PO question |
|---|---|---|
| `POD-M` object choice | ENGINEERING_DECISION | Which `system_settings` object is authoritative (typed columns vs key/value payload), and removing the second read path, is implementation. The PO supplies values (§6.3) |
| `POD-N` retention storage & enforcement | ENGINEERING_DECISION | One representation per value (GA-08); enabling the telemetry column (GA-01); the pruning mechanism. Policy values come from the PO (§6.4) |
| `POD-O` delivery mechanism | ENGINEERING_DECISION | Environment variables, secret handling, provider configuration, template plumbing |
| `POD-A` migration mechanics | ENGINEERING_DECISION | Filename ordering, prerequisite check, ledger arithmetic, backup procedure, verification probe |
| `POD-H` archive mechanics | ENGINEERING_DECISION | Where archived artefacts live, `.gitignore` updates, reference checks |
| `J2` X7 runtime metrics | ARCHITECTURE_DECISION | `backend/services/api_metrics.py` exists and is wired through `api/router.py` middleware while its contract record still reads "IMPLEMENTATION BLOCKED: PO DECISION REQUIRED". The capability is a platform observability decision; the *alerting thresholds/recipients* are the PO-facing part and belong to `PX-6` |
| `J3` shared table/pagination standard | ARCHITECTURE_DECISION | Register D47 + known decision 15 already record standardisation as an engineering direction; AGENTS §36 supplies the operational requirement (pagination, page size, sorting, filtering, counts) |
| `GA-24` CORS hard-coding | ENGINEERING_DECISION | Origins, regex vs list, removing the inert wildcard entry — configuration mechanics (D4 GA-24 marks it `IMPL`) |
| `GA-09` 37 inert settings columns | ENGINEERING_DECISION | Wire each column or mark it non-configurable; "which columns exist" is not a PO decision |
| `GA-21` permission matrix | ENGINEERING_DECISION (content policy may need the PO) | Producing a per-permission × per-role matrix is analysis; AGENTS §45 needs it as the negative-test oracle |
| `census POD-010` P17-K vocabulary | ENGINEERING/ARCHITECTURE (governance vocabulary) | `F-1`/`F-2` already prohibit a second model; internal vocabulary ratification is not product policy. Listed because it is absent from the A–O register (§11) |

---

## 9. Already-ratified decisions

Three registered PODs are already decided. They must not be re-put to the PO as open
product questions; each retains an **engineering/documentation execution action**.

### 9.1 `POD-D` — Locations vs Facilities (**ALREADY_RATIFIED**)

| Field | Content |
|---|---|
| Was it a PO decision? | It *was*, and it **has been answered** |
| Ratified text | "CarbonTally does NOT require a separate physical `locations` database table at this stage. The physical implementation may use a dedicated Locations table/entity OR the existing Facilities model/structure, provided the resulting product satisfies the frozen D17 UX and functional requirements." — **Status: "PO DIRECTION RESOLVED; ENGINEERING DECISION"** |
| Authority | `docs/audit/openhands/ui-ux/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` §25 (N2); summarised in `docs/audit/openhands/ui-ux/README.md` (N-series table); recorded as resolved in `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §32 ("PO DIRECTION RESOLVED; ENGINEERING DECISION on representation") |
| Implementation evidence | `frontend/src/v3/admin/LocationsTab.jsx` header: "Engineering decision (N2): Locations reuse the existing `facilities` model … No separate `locations` table is created"; it presents facilities as the organisation's Locations hierarchy and defers CRUD to the "Facilities & Assets" tab. `facilities` exists in the flagship (157 rows); no `locations` table exists. UX audits record the Locations tab as **PASS** (facilities reuse) |
| Remaining work (engineering, not PO) | GA-15: align AGENTS/D17 wording, schema description, UI labels and validation so AGENTS §35's 4xx-on-optional-field guarantee is demonstrable on the real entity; correct catalogue R4/T4 framing from "OPEN — PO decision" to "closed by N2; representation = engineering" |
| Why it was re-opened in D1–D4 | The catalogue treated the *wording drift* (AGENTS §34/§35 + D17 say "Locations"; the schema has only `facilities`) as an open PO question. The registry shows the PO decision is already made and only representation/documentation remained |

### 9.2 `POD-F` — PE terminology (**ALREADY_RATIFIED**)

| Field | Content |
|---|---|
| Ratified text | Register "D21 — Canonical terminology": *"Use established terms: Customer Organisation, **Processing Entity**, PE Staff, Processing Work, Human Processing/Review, Validation, QC, Evidence, Emission Factor, Custom Emission Factor, Factor Matching, Calculation, CarbonTally Staff; do not casually replace with 'client/worker/outsourcing company'."* Status **CURRENT**, authority **L1**, source PO-REG §19 + the V3 glossary |
| Corroboration | AGENTS §8/§12; register D22 (four access axes, never interchangeable); PE surfaces are `processing_entities`, `/api/v3/pe`, `/api/v3/admin/entities`, the PE workspace and `pe_manager` / PE staff roles |
| Where the conflicting term comes from | "Principal Entity" / "Principal / Reporting Entities" appears in the capability census (CAP-065/CAP-066), in D1's Domain 10 heading, and in the task example list — **no implementation of that name exists** (D1 FTR-078 records exactly this) |
| Remaining work (engineering/documentation) | GA-18: correct the census/catalogue wording to the ratified term. If an *accounting-boundary* concept is ever exposed to customers, that introduces new customer-facing terminology and **would** be a PO question — today it is documentary only |
| Why it was re-opened | The catalogue recorded the drift as "PO terminology decision required"; the register shows the term was already ratified |

### 9.3 `POD-G` — legacy admin control plane (**ALREADY_RATIFIED**)

| Field | Content |
|---|---|
| Ratified text | PO **D-P2-02** (2026-08-30): legacy Admin CRA **DEPRECATE** — inventory recorded in `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`; **V3 `/ops` is canonical**; the legacy surface **stays mounted until its retirement conditions are met** (do not delete it early) |
| Current runtime fact | The 19-screen legacy CRA is still served by the `vercel.json` `/admin` rewrite and still appears as live features in D1 Domain 45 (T5); `admin/**` remains a second React app |
| Remaining work (engineering) | GA-19: execute the retirement path for the rewrite (remove or redirect) after confirming the inventory's retirement conditions; re-classify Domain 45 rows |
| Contradiction recorded (not silently resolved) | `docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §32 still lists *"Final admin control-plane surface: dedicated `/admin` V3 surface vs `/ops` — UNRESOLVED (PO DECISION REQUIRED)"*. It conflicts with the ratified `/ops`-canonical position. Recorded in §19 as **superseded**, not elevated into a new PO question. If the PO disagrees, one short ruling ("`/ops` remains canonical" / "move the privileged surface to `/admin`") closes it permanently |

### 9.4 Wider ratified context these three sit inside

| Ratification | Substance | Source |
|---|---|---|
| `N1` | Messaging access and communication boundaries (no direct Customer ↔ PE chat; RLS/API-enforced) | decision register §24; AGENTS §28 |
| `N2` | Location physical data-model representation (see §9.1) | decision register §25 |
| `N3` | Configurable data retention: configurable via Settings/Admin, no invented durations, server-side enforcement | decision register §26; AGENTS §42 |
| `PX-7 Option (a)`, 2026-09-14 | Operational telemetry retention configurable, **initial 90 days**, as a schema default, not a code literal | `20260924000000_p8x_x2_operational_telemetry_retention.sql` header; D2 §7 |
| `D-P2-02` | Legacy admin CRA deprecated (see §9.3) | PO decision record; legacy admin inventory |
| `D-P2-03` / `D43` | QC limited authority; staff/admin separation; `system_admin` superset; permission keys | register D43; AGENTS §10/§13/§14 |
| `D-P2-04` / known decision 20 | Destructive retention enforcement **deferred** | register ("destructive retention deletion DEFERRED"); D2 §7 |
| `D11-C1` | Firm-centric recipients for consultant lifecycle notifications | PO decision record (CP2 / P6-2E closure) |
| `G0-D` (open) | Production deployment/migration **prohibited** while open | P8X-X2 migration header; G0 gate reconciliation reports |
| `D22` | Four access axes never interchangeable | register D22; AGENTS §7–§9 |
| `D47` + known decision 15 | Existing D21 UI primitives are the UI foundation; DataTable/pagination standardisation is an engineering direction | register D47; AGENTS §40 |

**Conclusion for §9:** `POD-D`, `POD-F` and `POD-G` are **closed**; D1–D4 framing them
as open PO decisions is a **catalogue observation to correct**, not a product question
to re-answer. This is the pack's primary reclassification finding.

---

## 10. Decisions blocked pending technical verification

### 10.1 None by primary classification

No POD is classified `BLOCKED_PENDING_TECHNICAL_VERIFICATION`, and this is a positive
finding rather than a gap: every remaining product question (`PO-Q01…PO-Q06`) can be
answered from current evidence plus business intent, because each depends on *policy
values* that the schema already has a place to hold. Nothing forces the PO to choose
implementation to compensate for missing technical evidence.

### 10.2 Items carrying a verification flag or a technical dependency

| Item | Flag | Why | What the verification would change |
|---|---|---|---|
| `POD-B` | `PENDING_COSTRICT_VERIFICATION` | If `CT-FEATURE-02` showed that the accounting-dimension columns are declared but never actually written by the wired calculation path, the representation question would acquire a *functional* dimension | Would not make it a PO decision; would add a functional-defect finding |
| `POD-C` | `PENDING_COSTRICT_VERIFICATION` | If role wiring were shown to read `roles` somewhere unreviewed, "retire vs populate" changes materially | Would not make it a PO decision; would change the engineering conclusion |
| `POD-F` | `PENDING_COSTRICT_VERIFICATION` | If a "principal/reporting entity" concept were shown to exist in code/schema, the terminology question becomes bigger than documentation | Would not reopen the ratified *term*; could add a missing-concept question |
| `POD-G` | `PENDING_COSTRICT_VERIFICATION` | If the `/admin` rewrite were shown to be already severed or replaced, GA-19 collapses to documentation | Would only accelerate the engineering close-out |
| `POD-M` | `PENDING_COSTRICT_VERIFICATION` | The *values* decision is not blocked. The claim "no code path reads the typed columns" is the part most exposed to a false-negative grep | Values remain a PO decision either way; the object choice stays engineering |
| `POD-N` | Technical dependency (not a PO block) | Telemetry retention **enforcement** cannot run until `operational_telemetry_retention_days` exists (GA-01/GA-02) | Enforcement, not policy. PO-Q01 is answerable now |
| `POD-A`, `POD-I` | Authorisation dependency | Action needs permission, not technical discovery | Substantially completes GA-01/GA-16 once authorised |

### 10.3 What would force a genuine block

If the PO requires *proof of a runtime behaviour* before choosing a value — for example
"show me that changing the upload limit changes enforcement before I set the limit" —
then the values decision becomes `BLOCKED_PENDING_TECHNICAL_VERIFICATION` until GA-03's
single read path is fixed and executed. That condition is raised here explicitly so
the PO can see the trade-off; it is **not** assumed.

---

## 11. Duplicate/consolidatable decisions

### 11.1 Within the A–O register

| Consolidation | Items | Basis | Effect |
|---|---|---|---|
| Retention policy | `POD-E` → `POD-N` | `POD-N` already names the audit value explicitly ("including whether audit retention stays at 1 day") and covers telemetry/data/documents/backups. D4 §2.3 files the audit value under GA-17 with the closing action "POD-E / POD-N: ratify the audit retention value" | One question (`PO-Q01`) instead of two |
| Residual capabilities | `POD-J` → `J1` SEO/PWA · `J2` X7 runtime metrics · `J3` shared table/pagination standard | The three subjects have different natures (product scope / platform observability / engineering standard) and the register itself cites two different authorities (AGENTS §36 for the table standard; "scope of the commercial product" for the rest) | One PO question (`PO-Q06`, SEO/PWA only) + two engineering items |
| Upload limits | `POD-M` object half → engineering; values half stays PO | The register asks two questions in one row | `PO-Q04` (values) + engineering object choice |
| Legacy artefacts | `POD-H` + `census POD-013` | Same subject (Prisma lineage, legacy admin, demo app, scratch outputs) | One authorisation (`PO-AUTH-02`) |
| Legacy admin | `POD-G` + `census POD-011` | `census POD-011` (admin console build settings) is subsumed by the D-P2-02 `/ops`-canonical decision | Closed (§9.3) |
| Environment/durability | `POD-A` + `census POD-001`/`POD-002` + `POD-I` | Same authorisation family (durable environment; migration application; production gate). `census POD-002`'s "apply 6 / apply all 21" options are superseded by the current 43-migration delta (GA-01) | Two authorisations (`PO-AUTH-01`, `PO-AUTH-03`) |
| Role model | `POD-C` + `census POD-017` + GA-21 | The *object* is engineering; the *capability matrix content* is a PO/analysis item | Engineering item + a distinct content question if the PO wants a governed matrix |
| Notification identity | `POD-O` + `PX-6` | `POD-O` covers sender/recipient identity; `PX-6` (alert recipients/channels/thresholds) is still recorded as PO DECISION REQUIRED in the insight coverage matrix and `D-28`. They overlap on *recipients* | `PO-Q05` should be answered together with `PX-6`; the two are related but not identical |

### 11.2 Consolidation map — register to final queue

| Final queue item | Absorbs | Type |
|---|---|---|
| `PO-Q01` | `POD-N`, `POD-E`, `census POD-009` | PO product decision (retention values) |
| `PO-Q02` | `POD-K` | PO commercial decision |
| `PO-Q03` | `POD-L` | PO commercial decision |
| `PO-Q04` | `POD-M` (values) | PO product decision |
| `PO-Q05` | `POD-O` (+ coordinate with `PX-6`) | PO product/policy decision |
| `PO-Q06` | `POD-J1` (SEO/PWA) | PO scope decision |
| `PO-AUTH-01` | `POD-A`, `census POD-001`/`POD-002` | Authorisation |
| `PO-AUTH-02` | `POD-H`, `census POD-013` | Authorisation |
| `PO-AUTH-03` | `POD-I`, GA-16 | Authorisation |
| `PO-AUTH-04` | `census POD-006` | Authorisation (execution prerequisite) |
| Engineering set (§8, §17) | `POD-B`, `POD-C`, `POD-M` object, `POD-N` storage, `POD-O` mechanism, `POD-A` mechanics, `POD-H` mechanics, `J2`, `J3`, `GA-09`, `GA-21`, `GA-24`, `census POD-010` | Engineering/architecture |
| Closed | `POD-D`, `POD-F`, `POD-G`, `census POD-011` | Already ratified |

**Net effect:** 15 + 18 register entries reduce to **6 product questions**, **4
authorisations**, one bounded engineering/architecture set, and a group already closed.

---

## 12. Decisions no longer required

**Count classified `NO_LONGER_REQUIRED`: 0.** Nothing in the register is void — each
entry either remains open in another category, or is closed as already-decided.

However, **five register entries cease to be PO decisions** and should be removed from
any PO decision queue:

| Entry | Ceases to be a PO decision because | Where it goes instead |
|---|---|---|
| `POD-B` | Product semantics are implemented and consumed; only representation/documentation disagrees | Engineering/architecture (§8.1) |
| `POD-C` | Which object is the RBAC authority is implementation; register D43 already names the authoritative mechanism | Engineering (§8.2) |
| `POD-D` | N2: PO direction resolved; representation is engineering | Closed + documentation work (§9.1) |
| `POD-F` | Canonical terminology already ratified | Closed + documentation work (§9.2) |
| `POD-G` | D-P2-02 already ratified | Closed + engineering execution (§9.3) |

This distinction matters: these five are *not* "no longer required work" — the work
remains (documentation correction, representation choice, rewrite removal). They are
no longer **Product Owner** decisions.

---

## 13. Cross-POD dependency graph

### 13.1 Graph (text form)

```
                        ┌────────────────────────────┐
                        │  PO-AUTH-03  (production   │  cheapest, read-only,
                        │  read-only inspection)     │  removes UNKNOWNs
                        └──────────────┬─────────────┘
                                       │ respects G0-D prohibition
                                       ▼
  PO-Q01..PO-Q06  ──────────────────────────────────►  policy values available
  (product/commercial values, none                         │
   technically blocked)                                    │
                                                           ▼
  PO-AUTH-01 ──► one durable env, backup, 43 migrations ──► W1 durability
        │                     │                             │
        │                     ├── POD-N telemetry enforcement (GA-02)
        │                     ├── POD-M enforcement test (GA-03)
        │                     └── POD-B representation verified durably
        ▼
  PO-AUTH-04 ──► QA harness on a DISPOSABLE target ──► W3 pipeline proof
                                                       W4 boundary proof (16 paths)
  POD-D ─┐
  POD-F ─┼──► no PO action; documentation/engineering closes GA-15/GA-18/GA-19
  POD-G ─┘
  POD-B / POD-C ──► engineering/architecture, flagged PENDING_COSTRICT_VERIFICATION
  CT-SCHEMA-01 ───► scope not yet defined in the repository (§15, §19)
```

### 13.2 Dependency table

| Item | Depends on | Blocked by it | Gating event |
|---|---|---|---|
| `POD-A` (durability) ↔ schema durability | Authorisation; backup; AGENTS §55.1 | GA-01, GA-02, GA-07, W1, W2, W3, W5 | `PO-AUTH-01` |
| `POD-B` ↔ accounting model | `CT-SCHEMA-01` (unscoped) | GA-14 and any artefact assuming a dimensions table | `PENDING_COSTRICT_VERIFICATION`, then engineering choice |
| `POD-C` ↔ RBAC | Register D43 (already names the mechanism) | GA-13, GA-21, W4 oracle | `PENDING_COSTRICT_VERIFICATION`, then engineering choice |
| `POD-D` ↔ facilities/locations | Nothing (N2 closed) | GA-15 documentation/validation | Engineering execution |
| `POD-E` ↔ retention | Folded into `POD-N` | — | Closed as an item |
| `POD-F` ↔ entity model | Nothing (terminology ratified) | GA-18 documentation | Engineering execution |
| `POD-G` ↔ Admin | Nothing (D-P2-02 ratified) | GA-19 rewrite execution | Engineering execution |
| `POD-H` ↔ artefact disposition | Authorisation; retention context | GA-20 | `PO-AUTH-02` |
| `POD-I` ↔ production verification | Authorisation + G0-D interpretation | GA-16, every `PROD:` claim | `PO-AUTH-03` |
| `POD-J` ↔ product scope | Split | GA-23, FTR-GAP-1 | `PO-Q06` (`J1`); engineering (`J2`,`J3`) |
| `POD-K` ↔ billing | Nothing technical | GA-10, GA-28, W5 | `PO-Q02` |
| `POD-L` ↔ billing | Coordinate with `POD-K` | GA-25, GA-28, W5 | `PO-Q03` |
| `POD-M` ↔ configuration architecture | Values now; object choice engineering; enforcement after GA-01/GA-03 | GA-03, GA-09, W2 | `PO-Q04` + engineering |
| `POD-N` ↔ retention architecture | Values now; telemetry enforcement after GA-01; single representation engineering | GA-02, GA-08, GA-17, W2 | `PO-Q01` + GA-01 (enforcement) |
| `POD-O` ↔ notification configuration | Recipients overlap `PX-6` | GA-26, GA-28 | `PO-Q05` (+ `PX-6`) |

### 13.3 What each gating event unlocks

| Gating event | Unlocks |
|---|---|
| `PO-Q01…PO-Q06` (product values) | W0 exits; every value-dependent GA row moves to `IMPL` with a ratified target |
| `PO-AUTH-01` | GA-01/GA-07/GA-02 execution → W1; makes `POD-B`/`POD-N` enforcement verifiable durably |
| `PO-AUTH-02` | GA-20 disposition; repository hygiene |
| `PO-AUTH-03` | GA-16; removes the `PROD: UNKNOWN` blanket |
| `PO-AUTH-04` | W3 (pipeline/evidence/approval/QC) and W4 (16 boundary paths) execution on disposable targets |
| `CT-FEATURE-02` | Independent confirmation or refutation of wiring claims (§14) |
| `CT-SCHEMA-01` (scope first) | Canonical schema construction input (§15) |
| Runtime workflow verification | Converts `PREDICTED` configuration failures into `VERIFIED` outcomes (GA-02, GA-03) |

---

## 14. Decisions affected by CT-FEATURE-02

`CT-FEATURE-02`
(`CT-FEATURE-02-20260927-INDEPENDENT-VERIFICATION-OF-CARBONTALLY-FEATURE-CATALOGUE-AND-FALSE-IMPLEMENTED-AND-WIRED-DETECTION`)
is running concurrently. **Its result is not available and is not assumed here.**
Counting `POD-A…POD-O` only: **5 of 15** are flagged.

> **Note added during this task's own verification pass (metadata only, content not
> consumed).** Two untracked files written by the concurrent `CT-FEATURE-02` task
> appeared in the working tree while this pack was being finalised:
> `docs/architecture/CT-PO-CARBONTALLY-FEATURE-CATALOGUE-INDEPENDENT-VERIFICATION-20260927.md`
> (24,519 bytes, mtime 16:01:02) and
> `docs/architecture/CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md`
> (23,700 bytes, mtime 16:01:45). Their **contents were deliberately not read or used**:
> the task instruction is not to wait for, duplicate or pre-empt that verification, and
> they were in flight at the time. The flags below therefore stand as written and must be
> re-checked against that task's **final** report.

| POD | Nature of exposure | If `CT-FEATURE-02` confirms wiring | If it contradicts wiring |
|---|---|---|---|
| `POD-B` | `accounting_dimensions` writes | Representation remains engineering/documentation | Adds a functional defect (dimensions declared but not populated); representation question gains weight. Still not a PO decision |
| `POD-C` | `roles`-table reads | Retire/populate stays engineering | If `roles` is read by code elsewhere, the "authoritative RBAC source" question changes materially |
| `POD-F` | existence of a "principal/reporting entity" implementation | Terminology stays closed | Could reveal an unlisted concept needing its own decision |
| `POD-G` | `/admin` rewrite state | GA-19 is documentation + removal | If the rewrite is already severed, GA-19 closes faster |
| `POD-M` | "nothing reads the typed columns" | Object choice engineering; values PO | If a read path exists, the enforcement picture changes (still engineering) |

**No PO question in this pack is classified as depending on `CT-FEATURE-02`.** The five
flags affect *engineering conclusions and documentation*, not the six product questions.
Should `CT-FEATURE-02` disclose a capability that the catalogue marked
`IMPLEMENTED_AND_WIRED` but that turns out to be unwired **and customer-facing**, the
hosting POD classification would have to be revisited — that contingency is recorded in
§19 rather than pre-judged.

---

## 15. Decisions affected by CT-SCHEMA-01

**Status of `CT-SCHEMA-01`:** the identifier appears **exactly once** in the repository —
D1 §1 summary row: *"Schema requirements derived | yes — §4 (input to CT-SCHEMA-01)"*.
No task definition, scope statement or workplan entry for `CT-SCHEMA-01` exists in
either repository (searched `docs/`, and the master workplan, which refers to
"authorised release/schema" without naming the task). Its scope is therefore **an open
uncertainty** (§19): this pack cannot treat it as an authority for anything, and no PO
decision should be deferred to it until its scope exists.

On the assumption that `CT-SCHEMA-01` means "construct the canonical schema from the
release migration tree", **4 of 15** PODs are affected:

| POD | How `CT-SCHEMA-01` (as scoped) would affect it | Does that change its classification? |
|---|---|---|
| `POD-A` | It is the execution counterpart of `PO-AUTH-01`: applying 43 migrations is "schema construction". Adopting `CT-SCHEMA-01` does not change the *authorisation* question | No — still authorisation |
| `POD-B` | It could resolve the representation choice ("columns are canonical; correct the documents") | No — still architecture/engineering |
| `POD-C` | It could decide whether the empty `roles` table is dropped, populated or frozen | No — still engineering |
| `POD-N` | It would carry the `operational_telemetry_retention_days` column and the single-representation decision (GA-08) | No — the PO's value question is independent; enforcement is still gated by GA-01 |

**Not affected:** `POD-D`, `POD-F`, `POD-G` (closed), `POD-E` (folded), `POD-I`
(production-facing, not schema construction), `POD-H` (repository artefacts),
`POD-J` (`J1` product scope; `J2`/`J3` engineering standards), `POD-K`, `POD-L`,
`POD-M` (values), `POD-O` (environment identity).

**Scope advice (not a business choice):** define `CT-SCHEMA-01`'s scope — target
environment, relationship to `PO-AUTH-01`, and whether it may alter durable data —
**before** it is relied upon for any of the four rows above. Until then, treat D1 §4 as
the input and `PO-AUTH-01` as the gate.

---

## 16. Final Product Owner questionnaire

### 16.1 Questions actually requiring Product Owner input

Six questions. Each is understandable without reading the forensic documents, and each
is a **policy** question. No option is marked preferred.

#### `PO-Q01` — Retention

- **QUESTION:** For each domain — audit records, operational telemetry, activity/source data, documents, backups — how long should CarbonTally retain the records?
- **WHY_IT_MATTERS:** Retention is legal/commercial and auditability policy. Audit retention is **1 day** today while data/documents/backups are 365; a one-day audit horizon conflicts with the platform's own traceability requirement (AGENTS §42).
- **CURRENT_FACTS:** `system_settings.platform_retention` holds audit **1** · data **365** · document **365** · backup **365**, duplicated between typed columns and a JSONB copy. Operational telemetry retention is already ratified to start at **90 days**, but the column does not yet exist in any durable database. Destructive enforcement is deferred by prior decision, so no deletion is active.
- **OPTIONS_SUPPORTED_BY_EVIDENCE:** (a) one retention set across domains; (b) different values per domain; (c) values plus an explicit statement that enforcement stays off. The telemetry 90-day value is **already decided** and needs no re-answering.
- **DEPENDENCIES:** None for the values. Enforcing the telemetry domain waits for the environment migration (`PO-AUTH-01`).
- **WHAT_HAPPENS_AFTER_DECISION:** retention gains approved values; the duplicate-storage defect becomes a bounded engineering fix; the audit-horizon gap closes.

#### `PO-Q02` — Commercial terms

- **QUESTION:** What are the commercial values for storage overage, the standard allowance and its overage, credit expiry, and credit carry-over limits?
- **WHY_IT_MATTERS:** These are prices and allowances. Five values are unset, so the platform cannot price an overage and every quote/invoice is unbacked.
- **CURRENT_FACTS:** `billing_commercial_config` has 7 versioned keys; `storage.additional_rate_per_gb`, `standard_allowance.monthly_processing_units`, `standard_allowance.additional_rate`, `credit_policy.rollover.expiry_months`, `max_carryover_pct` are all **null**. Credit classes (1/2/4) and assisted prices (0.99/1.99/3.99 **USD**) are configured. No billing transaction has ever been recorded (all billing tables 0 rows).
- **OPTIONS_SUPPORTED_BY_EVIDENCE:** (a) set all values now; (b) set credit/allowance values and defer storage overage; (c) defer commercial configuration entirely for now.
- **DEPENDENCIES:** Currency handling (`PO-Q03`) affects how the values read.
- **WHAT_HAPPENS_AFTER_DECISION:** the billing engine has an approved basis; one end-to-end commercial flow becomes testable; the commercial gap row closes.

#### `PO-Q03` — Plan currency

- **QUESTION:** Should each plan version be priced in a single currency, or should CarbonTally deliberately offer plans in more than one currency?
- **WHY_IT_MATTERS:** The live catalogue contains both GBP and USD rows, and the configured assisted prices are USD while storage/allowance are GBP. Pricing intent is a commercial choice.
- **CURRENT_FACTS:** 6 live plan rows: Starter v1 GBP 0 · Starter v2 USD 49 · Professional v1 GBP 149 · Business v1 GBP 299 · Business v2 USD 399 · Enterprise v1 GBP 0/custom; plan currency is per row and versioned; the system-wide `default_currency` is `'GBP'` (CHECK limited to GBP/EUR).
- **OPTIONS_SUPPORTED_BY_EVIDENCE:** (a) one currency per catalogue version; (b) explicit multi-currency plans; (c) one currency now, multi-currency later.
- **DEPENDENCIES:** Coordinate with `PO-Q02`.
- **WHAT_HAPPENS_AFTER_DECISION:** the pricing basis becomes unambiguous; the mixed-currency finding is either corrected or ratified as intentional.

#### `PO-Q04` — Upload limits

- **QUESTION:** What upload limits should CarbonTally enforce — maximum file size, files per batch, total batch size, permitted file types, and whether daily/per-document/per-page quotas exist at all?
- **WHY_IT_MATTERS:** Today's enforced limits are code literals (50 MB / 20 files / 200 MB / PDF,CSV,XLSX,JPG,PNG), so a constant is acting as product policy and the control plane cannot change it.
- **CURRENT_FACTS:** The upload router asks for settings that do not exist as columns and falls back to those literals; several settings columns exist that no code reads; the frontend separately enforces the same 50 MB figure. *Which* object should hold the values is an engineering question and is excluded from this question.
- **OPTIONS_SUPPORTED_BY_EVIDENCE:** (a) ratify the values already enforced; (b) choose different values; (c) choose values and declare unused columns out of scope.
- **DEPENDENCIES:** Enforcement testing needs a working environment (`PO-AUTH-01`) and the single read path (engineering). The values decision itself is not blocked.
- **WHAT_HAPPENS_AFTER_DECISION:** controlled upload policy replaces accidental policy; the control plane can be shown to affect behaviour.

#### `PO-Q05` — Platform notification identity

- **QUESTION:** Who should the platform's automated emails come from, and who should receive platform-level notifications in each environment?
- **WHY_IT_MATTERS:** A personal email address is compiled into the release tree as the default recipient, and no decision records the intended platform sender/recipient identity — a customer-visible identity and privacy matter.
- **CURRENT_FACTS:** `FOUNDER_EMAIL` defaults to a personal address (`backend/config.py`); the coded sender is `CarbonTally <notifications@carbontally.co.uk>` in three modules; delivery uses the existing email provider; white-label sender records exist but are empty (0 rows). Related but separate: the still-open `PX-6` decision on alert recipients/channels/thresholds.
- **OPTIONS_SUPPORTED_BY_EVIDENCE:** (a) ratify a service sender and a role mailbox as default recipient; (b) per-environment branded senders; (c) also permit verified consultant/customer senders for white-label journeys.
- **DEPENDENCIES:** Recipient intent should be settled consistently with `PX-6`.
- **WHAT_HAPPENS_AFTER_DECISION:** no personal address functions as platform policy; notification identity becomes administered rather than compiled in.

#### `PO-Q06` — SEO/PWA scope (split from `POD-J`)

- **QUESTION:** Are the public-site SEO and installable-PWA artefacts in scope as product capabilities, or declared out of scope for now?
- **WHY_IT_MATTERS:** These are the only residual capabilities with no individual feature row, so a reader cannot tell whether they are intended product surface or incidental build output.
- **CURRENT_FACTS:** 3 residual capabilities were declared uncatalogued: SEO/PWA, X7 runtime metrics, shared table/pagination standard. Only the SEO/PWA item is product scope: the other two are platform engineering (the table/pagination standard already has a register entry as an engineering direction, and AGENTS §36 supplies its operational requirement).
- **OPTIONS_SUPPORTED_BY_EVIDENCE:** (a) catalogue them as product capabilities; (b) declare them out of scope; (c) catalogue the ones already live and declare the rest out of scope.
- **DEPENDENCIES:** None.
- **WHAT_HAPPENS_AFTER_DECISION:** the residual-capability gap closes and the catalogue's scope statement becomes complete.

### 16.2 Authorisations requested separately (not product decisions)

Presented here for the PO's convenience; these are **permissions to act**, not policy
choices. Detail and boundaries: §7.

| ID | One-line ask |
|---|---|
| `PO-AUTH-01` | Authorise designating one durable environment and applying the 43 migrations in filename order after backup (`POD-A`). |
| `PO-AUTH-02` | Authorise archive/removal — and where applicable destruction — of superseded repository artefacts (`POD-H`). |
| `PO-AUTH-03` | Authorise a **read-only** production schema/ledger inspection and state whether it falls inside the `G0-D` prohibition (`POD-I`). |
| `PO-AUTH-04` | Authorise QA/integration harness execution against a **disposable** target (`census POD-006`, status not re-verified). |

## 17. Engineering-only decision list

These should be decided by engineering (with the PO's desired outcome in mind) and
**not** put to the Product Owner as business questions. Each cites the evidence that
justifies the delegation.

| # | Decision | Owner | Evidence / constraint that settles the "who" |
|---|---|---|---|
| E1 | Migration filename ordering, prerequisite check, backup procedure, ledger arithmetic for the 43 unapplied migrations | Engineering | AGENTS §66; D4 GA-01 closing action; only the *authorisation* is PO (`PO-AUTH-01`) |
| E2 | Which physical database/environment is designated durable | Engineering/operations (under `PO-AUTH-01`) | D4 GA-07; task constraint that the PO must not select a database |
| E3 | Whether accounting dimensions stay as columns or become a physical object; correction of documents calling it a table | Architecture/engineering | P17-A is `ALTER TABLE`; code consumes the columns; D1 §1.2 |
| E4 | Whether the empty `roles` table is retired or populated; single RBAC authority | Engineering | Register D43 names `staff_roles.permissions`; `auth.py` resolves from it |
| E5 | Single storage representation for retention values (typed columns vs JSONB) | Engineering | D2 CFG-2; D4 GA-08 |
| E6 | Which object is authoritative for upload limits; removal of the second read path | Engineering | D2 CFG-3; D4 GA-03 closing action |
| E7 | Wiring or de-configuring the 37 inert `system_settings` columns | Engineering | D2 CFG-4; D4 GA-09 |
| E8 | Implementation of the operational-telemetry retention column (GA-01) | Engineering | `20260924000000_p8x_x2_…sql` unapplied; D4 GA-02 |
| E9 | Environment-variable mechanism, secret handling and provider plumbing for notification identity | Engineering | `backend/services/v3_email.py` docstring; `RESEND_API_KEY` usage |
| E10 | Removal/redirection of the `/admin` rewrite per the D-P2-02 retirement conditions | Engineering | Legacy admin inventory; D4 GA-19 |
| E11 | Archive mechanics and reference checks for superseded artefacts; `.gitignore` updates | Engineering | AGENTS §79; D4 GA-20 |
| E12 | CORS origins handling (list vs regex) and removal of the inert wildcard entry | Engineering | D2 CFG-7; D4 GA-24 |
| E13 | Per-permission × per-role capability matrix as the negative-test oracle | Engineering (content policy may need the PO) | AGENTS §45; D4 GA-21; FTR-GAP-6 |
| E14 | X7 runtime-metrics capability shape (what is persisted, metrics retention, wiring) | Architecture/engineering | `backend/services/api_metrics.py` + router middleware exist; contract record is stale |
| E15 | Shared DataTable/pagination standard implementation scope | Engineering (D21/§36 constrain the outcome) | Register D47 + known decision 15; AGENTS §36 |
| E16 | P17-K capability-vocabulary consolidation inside the platform | Engineering/architecture governance | `F-1`/`F-2` prohibit a second model |
| E17 | Verification probe design and evidence capture for GA-01/GA-02/GA-03 | Engineering/QA | D4 §6 — "how each gap class is closed" |
| E18 | Any schema change required by the above (migrations, RLS, grants) | Engineering, under AGENTS §66/§67 | AGENTS §66/§67; no ad-hoc production modifications |

**Do not ask the PO:** migration filenames, SQL implementation, table-vs-column where
product semantics are already clear, API or repository implementation, RLS
implementation, service architecture, index design, database normalisation, or
migration mechanics.

---

## 18. Prior ratifications that must remain closed

This pack does not reopen any of the following, and none should be re-put to the PO as
an open question. Sources are given so each can be verified independently.

| Ratification | Text / substance | Source | What reopening would damage |
|---|---|---|---|
| **N3** | Retention is configurable and enforced server-side; durations must never be invented by code | Decision register §26 (`CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`); AGENTS §42 | The configurable-retention control plane and AGENTS §42 |
| **PX-7 Option (a)**, 2026-09-14 | Operational telemetry retention = configurable server-side, **initial value 90 days**, expressed as a **schema default** not a code literal; `data_retention_days` must not be reused | `supabase/migrations/20260924000000_p8x_x2_operational_telemetry_retention.sql` header (quoted in D2 §7) | A settled value and the schema-default contract |
| **D-P2-02** | Legacy Admin CRA deprecated; V3 `/ops` canonical; legacy stays mounted until its retirement conditions are met | PO decision (2026-08-30); `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md` | The admin control-plane decision (§9.3) |
| **D-P2-03 / D43** | QC limited authority (never customer approval); staff/admin separation; `system_admin` superset; permission keys | Register D43 (RATIFIED), source D-P2-03 | The role model that RLS and APIs implement |
| **D-P2-04 / known decision 20** | Destructive retention deletion **deferred** (no automatic destructive deletion active) | Register; D2 §7 | Would silently switch on deletion |
| **`G0-D` (open) — production prohibition** | Production deployment/migration **prohibited** while `G0-D` is open; the P8X-X2 header records "Production is PROHIBITED (G0-D open)" | Migration header; `CT-P8-G0-GATE-RECONCILIATION-20260914-042.md`; `CT-P8-CURRENT-STATE-GAP-RECONCILIATION-…-20260915.md` | Any production action treated as "implied". `PO-AUTH-03` therefore asks the PO to **interpret** the prohibition, not to override it silently |
| **N1** | Messaging access and communication boundaries; no direct Customer ↔ PE chat; RLS/API-enforced | Decision register §24; AGENTS §28 | Messaging boundaries |
| **N2** | Location physical data-model representation (engineering decision inside frozen D17) | Decision register §25 | `POD-D` (§9.1) |
| **D11-C1** | Consultant lifecycle notifications use firm-centric recipients; client-organisation recipients are **not** part of that flow | PO decision record (CP2 / P6-2E closure) | Consultant notification behaviour |
| **D22** | Four access axes never interchangeable (customers, internal staff, PE staff, consultants) | Register D22; AGENTS §7–§9 | The role/entity model |
| **D47 + known decision 15 / D21 design system** | Existing UI primitives are the UI foundation; DataTable/pagination standardisation is an engineering direction | Register D47; AGENTS §40/§63 | The frozen design system that `POD-J3` was mistakenly treated as a PO question about |

**Not ratified, therefore not on this list:** the five commercial values (`POD-K`), the
currency model (`POD-L`), the upload limits (`POD-M`), the audit/data/document/backup
retention values (`POD-N`), the platform notification identity (`POD-O`), and the
SEO/PWA scope question (`PO-Q06`). Those remain genuinely open.

---

## 19. Open uncertainties

| # | Uncertainty | Why it matters here | How it would be closed |
|---|---|---|---|
| U1 | **`CT-FEATURE-02` result not consumed.** Two in-flight output files appeared in the working tree at 16:01:02/16:01:45 on this date (see the §14 note); their content was deliberately not read or used | Five PODs carry `PENDING_COSTRICT_VERIFICATION`; a refutation of wiring claims could add functional findings (not PO questions) | Consume its **final** report; re-check §14 flags |
| U2 | **`CT-SCHEMA-01` has no scope in the repository** — a single reference (D1 §1) | Four PODs are described as "affected by" an undefined task | Define its scope before relying on it (§15) |
| U3 | **`PX-6` status** (alert recipients/channels/thresholds) is still recorded as PO DECISION REQUIRED in the insight coverage matrix, while the alerting service exists and its contract record is stale | `PO-Q05` (notification identity) overlaps `PX-6` on recipients; answering one without the other risks inconsistency | Confirm `PX-6`'s live status; answer `PO-Q05` with it |
| U4 | **Whether a read-only production inspection falls inside the `G0-D` production prohibition** | Determines whether `PO-AUTH-03` needs an explicit carve-out | A PO interpretation, or replacing `G0-D` with a bounded read-only permission |
| U5 | **Was audit retention = 1 ever intentional?** | It is the single most anomalous live policy value | PO answer in `PO-Q01` |
| U6 | **Are the 43 unapplied migrations the complete delta?** Ledger tables are unreadable in 4 of 6 local environments, and no environment represents the release tree | Affects the *scale* of `PO-AUTH-01`, not whether it is needed | Re-run ledger arithmetic after `PO-AUTH-01` (D4 GA-01 exit criterion) |
| U7 | **Whether the USD plan rows / USD assisted prices are intentional** | Shapes `PO-Q03`'s options | PO answer; no technical blocker |
| U8 | **Older register §32 contradiction** ("`/admin` vs `/ops` — UNRESOLVED") versus ratified D-P2-02 | Could cause the admin question to be re-opened by mistake | One-line PO confirmation, or treat the older entry as superseded (§9.3) |
| U9 | **Register-label collisions** (`POD-A…O` vs `census POD-001…018`; `D21` = terminology vs design system) | Two registers and two meanings for one label invite mis-citation | Documentation hygiene: prefix every reference; correct colliding entries |
| U10 | **Repository working-tree state** — `ct_93d5cdd` has 47 dirty entries including untracked deliverables, `.costrict/`, `.p18_audit_tmp/` and two stray untracked files named `8` and `=`; `carbon_tally` has 305 | Affects any "release-ready tree" claim; these deliverables are not yet committed | Deliberate Git governance (AGENTS §70); not a PO decision |
| U11 | **Census-register items never re-verified** (`census POD-004`, `POD-005`, `POD-007`, `POD-008`, `POD-012`, `POD-014`, `POD-015`, `POD-018`) | Some may still be open and are absent from the A–O queue | A register reconciliation pass (§4.3 mapping) |
| U12 | **Whether the telemetry retention endpoint actually fails at runtime** — D2 marks it `PREDICTED (runtime)` | Converts a predicted failure into a verified one | Execute after `PO-AUTH-01` (needs the durable column) |
| U13 | **Assisted pricing is in USD while allowance/storage are GBP inside the same commercial config** (found in this pass; not previously registered as its own finding) | Compounds `PO-Q03`'s evidence | Fold into `PO-Q03`; register as a configuration observation |

---

## 20. Recommended decision sequence

**Sequencing advice only. No business option is recommended or ranked.**

| Step | Action | Why now | Depends on |
|---|---|---|---|
| 1 | Answer `PO-AUTH-03` (read-only production inspection) | Read-only, cheapest, removes the largest `UNKNOWN` blanket; does **not** touch `G0-D`'s prohibition on change | Nothing |
| 2 | Answer `PO-Q01` and `PO-Q04` (retention values; upload limits) | Both are single-source policy questions with the anomalies already identified; neither needs technical discovery | Nothing |
| 3 | Answer `PO-Q02` and `PO-Q03` (commercial values; currency), ideally in one sitting | They interact; both are currently unbacked | None (coordinate together) |
| 4 | Answer `PO-Q05` (notification identity) with `PX-6` | Prevents two partially-overlapping recipient decisions | Confirmation of `PX-6` status |
| 5 | Answer `PO-Q06` (SEO/PWA scope) | Closes the residual-capability gap | Nothing |
| 6 | Answer `PO-AUTH-01` (durable environment + 43 migrations) | Gates every execution wave | Backup plan; `PO-AUTH-01` wording |
| 7 | After 6: execute W1, re-run the ledger arithmetic, then re-verify `POD-B`/`POD-C`/`POD-N` enforcement | Converts `PREDICTED` into `VERIFIED` | `PO-AUTH-01` |
| 8 | Answer `PO-AUTH-02` (artefact disposition) at any convenient point | Independent of the others; hygiene | Nothing |
| 9 | Answer `PO-AUTH-04` (harness target) before any W3/W4 execution | Required by AGENTS §55.1 | A disposable target exists |
| 10 | Define `CT-SCHEMA-01` scope, then re-check §15 | Prevents reliance on an undefined task | Nothing |
| 11 | Consume `CT-FEATURE-02`, then re-check §14 | Independent verification of wiring claims | Its publication |

**Parallel-safe:** steps 1–5 and 8 need no technical prerequisite. **Serialised:**
step 7 follows step 6; step 9 precedes W3/W4.

---

## 21. Limitations

1. **No decision was made.** This pack classifies and exposes; it does not choose.
2. **No runtime verification.** Nothing was executed; classification rests on documents,
   source, schema definitions and prior read-only probes.
3. **No production contact.** Every production state remains `UNKNOWN`; `G0-D` stands.
4. **The feature catalogue is treated as Cline evidence, not independently verified
   truth** (L1). `CT-FEATURE-02` was neither duplicated nor pre-empted.
5. **Classification is judgement within the task's definitions.** "Genuine PO decision"
   was applied only where a choice depends on product intent, business/commercial policy,
   product scope, customer-facing semantics/terminology, retention policy or supported
   capability scope — and could not be derived from existing technical evidence.
6. **Documentary registers are treated as design authority.** Where they conflict with
   each other (`D21`, the `/ops` vs `/admin` entry) the conflict is recorded, not
   resolved.
7. **D2/D3/D4 figures are quoted, not re-measured.** They are point-in-time read-only
   counts; drift is possible.
8. **Coverage of prior documents is targeted, not exhaustive.** 272 `.md` files exist in
   `docs/architecture` alone; the five primary documents were read closely, 27 prior
   documents consulted by search, and 16 source/migration artefacts inspected.
9. **Register completeness.** The A–O register was reviewed in full as required, and the
   parallel census register mapped; census statuses were not re-established.
10. **Nothing in D1–D5 was corrected.** Observations about D1–D5 (reclassification,
   register collisions, undefined `CT-SCHEMA-01`, the `POD-0xx` label overlap) are
   recorded here as findings for their authors/owners to action.
11. **Read-only posture preserved.** No source file was modified; one new document (this
   deliverable) was created; no database, environment, configuration or Git object was
   changed; production was not contacted.

---

## 22. Hand-back

| Item | Value |
|---|---|
| Deliverable | `docs/architecture/CT-PO-CARBONTALLY-PO-DECISION-EVIDENCE-PACK-20260927.md` |
| Primary repository | `/home/shomonrobie/ct_93d5cdd` |
| Exact HEAD SHA | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Branch | `p8-release-reconciled` |
| Working-tree state | **47** dirty entries when the task began (1 modified `.gitignore`, 46 untracked incl. the five deliverables, `.costrict/`, `.p18_audit_tmp/`, stray files `8` and `=`); **50** at hand-back — the additions are this deliverable (untracked, +1) and two in-flight outputs of the concurrent `CT-FEATURE-02` task (untracked, +2; existence noted, content not read). Historical repository `carbon_tally` @ `20b7a928bb73fdfacf8271ff537a8fd245f62c79` (`main`), 305 dirty entries, untouched |
| Source documents reviewed | **32** = 5 primary deliverables + 27 prior/adjacent documents (plus 16 source/migration artefacts) |
| PODs reviewed | **15** (`POD-A…POD-O`), all classified; plus **18** census-register items mapped |
| `GENUINE_PO_DECISION` | **5** — `POD-K`, `POD-L`, `POD-M`, `POD-N`, `POD-O` |
| `PO_AUTHORIZATION_ONLY` | **3** — `POD-A`, `POD-H`, `POD-I` |
| `ENGINEERING_DECISION` | **1** — `POD-C` |
| `ARCHITECTURE_DECISION` | **1** — `POD-B` |
| `ALREADY_RATIFIED` | **3** — `POD-D`, `POD-F`, `POD-G` |
| `BLOCKED_PENDING_TECHNICAL_VERIFICATION` | **0** |
| `DUPLICATE_OR_CONSOLIDATABLE` | **2** — `POD-E` (→`POD-N`), `POD-J` (→`J1`/`J2`/`J3`) |
| `NO_LONGER_REQUIRED` | **0** |
| Final PO questions | **6** (`PO-Q01…PO-Q06`) + **4** authorisations (`PO-AUTH-01…PO-AUTH-04`) |
| Decisions affected by `CT-FEATURE-02` | **5** (`POD-B`, `POD-C`, `POD-F`, `POD-G`, `POD-M`) — flags only; no PO question depends on it |
| Decisions affected by `CT-SCHEMA-01` | **4** (`POD-A`, `POD-B`, `POD-C`, `POD-N`) — and `CT-SCHEMA-01` itself is unscoped (U2) |
| Source files modified | **None** (one new deliverable document created, as required) |
| Database modified | **No** |
| Production contacted | **No** |
| Git mutated | **No** (only read-only `git rev-parse`, `git branch --show-current`, `git status`) |
| Secrets reproduced | **None** (no tokens, keys, JWTs, signed URLs or credentials; the personal address noted in `POD-O` is quoted because it is a compiled-in default and the substance of the finding) |
| Writes performed | **None** |
| Verdict | **`CT_PO_DECISION_01_COMPLETE_WITH_OBSERVATIONS`** |

### 22.1 Why "with observations"

The classification task is complete, and the observations are substantive rather than
cosmetic:

1. **Three of the fifteen registered "PO decisions" are already decided** (`POD-D` by
   N2, `POD-F` by the canonical-terminology register entry, `POD-G` by D-P2-02). The
   catalogue/register framing them as open risks re-asking settled questions.
2. **Two entries are duplicates/splits** (`POD-E` folds into `POD-N`; `POD-J` splits
   into one scope question and two engineering items), so the queue shrinks without any
   policy being lost.
3. **Four entries are authorisations, not product questions** (`POD-A`, `POD-H`,
   `POD-I` + census `POD-006`), which changes the *kind* of answer required.
4. **Two entries are implementation layers inside ratified directions** (`POD-B`
   architecture, `POD-C` engineering).
5. **Two registers and two label meanings collide** (`POD-0xx` census vs `POD-A…O`;
   `D21` terminology vs `D21` design system), and the census register carries three items
   with no A–O equivalent that materially affect execution.
6. **`CT-SCHEMA-01` is unscoped** despite being cited as an authority for schema input.

**Bottom line for the Product Owner:** the platform poses **six genuine product
questions** and **four authorisation requests**. Everything else is either already
decided, an engineering/architecture choice, or documentation correction. No Product
Owner decision is made by this document.

`CT_PO_DECISION_01_COMPLETE_WITH_OBSERVATIONS`

<!--CTEOF-->

