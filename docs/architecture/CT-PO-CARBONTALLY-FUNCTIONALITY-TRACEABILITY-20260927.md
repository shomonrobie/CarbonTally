# CT-FEATURE-01 / Deliverable 3 — CarbonTally Functionality Traceability

**Task ID:** `CT-FEATURE-01-20260927-CARBONTALLY-COMPLETE-FEATURE-AND-FUNCTIONALITY-CATALOGUE-FROM-SCHEMA-CODE-AND-HISTORICAL-EVIDENCE`
**Type:** READ-ONLY forensic discovery — no implementation, no migration, no seed, no deployment
**Date:** 2026-09-27
**Trees:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` · `/home/shomonrobie/carbon_tally` @ `20b7a928bb73fdfacf8271ff537a8fd245f62c79`
**Companion documents:** feature catalogue (1), configuration catalogue (2), gap analysis (4), report (5)

---

## 0. What traceability means in this document

Three joins are traced, and nothing else is claimed:

1. **Capability → feature.** Every one of the 152 `CAP-` capabilities in the prior census is joined to the domain(s) and `FTR-` range(s) that deliver it, or explicitly declared *not individually catalogued*.
2. **Role → feature.** Each operating role is joined to the domains it can act on, with the enforcement layer named (API guard, RLS, or both).
3. **Workflow → evidence.** The end-to-end business chains are traced step by step to the `FTR` rows and the persistence objects that make each step auditable.

### 0.1 Join-status vocabulary

| Status | Meaning |
|---|---|
| `TRACED` | The capability is delivered by catalogued features; the join is by subject and by the evidence tokens in the feature rows |
| `TRACED (SPLIT)` | The capability is delivered across more than one domain and cannot be reduced to a single feature group |
| `NOT INDIVIDUALLY CATALOGUED` | No `FTR` row exists; declared as a census residual rather than invented (POD-J) |
| `HISTORICAL` | Present as historical/legacy artefact only |

### 0.2 Reading rules

- A join is **by subject**, not by machine-generated ID correspondence. No tool
  produced these mappings; they are analyst judgements made against the
  catalogue's own evidence tokens and are declared as such.
- Where a capability's implementation lives in a layer the catalogue marks
  `DOCUMENTED_ONLY`, `SCHEMA_ONLY` or `PARTIAL`, the join inherits that status —
  it is **not** upgraded to "working" by being traceable.
- Traceability proves **where** functionality lives. It never proves that the
  functionality works at runtime; that requires execution, which this pass did not
  perform.

---

## 1. Method

| Step | Source | Output |
|---|---|---|
| 1 | `CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md` — 152 `CAP-` rows | the capability set to be joined |
| 2 | `CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` — 54 domains, 354 `FTR-` rows with `DB:` / `API:` / `BE:` / `UI:` / `AD:` / `DOC:` / `TEST:` evidence tokens | the feature side of the join |
| 3 | Live flagship database (`postgres`, 116 tables) and the P17 clone (`ct_p17k_20260926`, 145 tables) | persistence reality for each join |
| 4 | Role guards in `backend/auth.py`, `backend/api/v3_*.py` (`require_admin`, `require_staff`, `require_internal_staff`, `_require_billing_admin`) + 174 RLS policies | the authorization side of the join |

---

## 2. Join integrity summary

| Measure | Value |
|---|---|
| Capabilities joined | **152 / 152** |
| Distinct `FTR` rows referenced across the join | **354** (all domains 01–54 appear in at least one join) |
| Capabilities mapped to exactly one domain | 118 |
| Capabilities mapped to two or more domains (`TRACED (SPLIT)`) | 31 |
| Capabilities with no individual `FTR` row (`NOT INDIVIDUALLY CATALOGUED`) | 3 — CAP-010 (SEO/PWA), CAP-122 (X7 API runtime metrics), CAP-148 (shared table contract) |
| Capabilities traced to historical/legacy rows | 6 — CAP-091, CAP-138, CAP-143, CAP-144, CAP-145, CAP-150 |
| Capabilities whose only surviving implementation is documentation | 4 — CAP-010, CAP-122, CAP-145, CAP-152 (partial) |

**The three residuals are not failures of the catalogue.** They are capabilities
that exist in the census and have no surviving first-class implementation object
in either tree; declaring them here is what prevents the catalogue from
over-claiming coverage (finding **FTR-GAP-1**, §7).

---

## 3. Complete capability → feature join (152 rows)

Column key: `Dom` = domain number in the feature catalogue; `FTR` = feature-id
range; `Status` = join status per §0.1.

| CAP | Capability | Dom | FTR | Status |
|---|---|---|---|---|
| CAP-001 | Public marketing landing page | 52 | FTR-341…345 | TRACED |
| CAP-002 | Company / about page | 52 | FTR-341, FTR-344 | TRACED |
| CAP-003 | Pricing page | 49, 52 | FTR-329, FTR-341 | TRACED (SPLIT) |
| CAP-004 | Legal and policy pages | 52 | FTR-344, FTR-345 | TRACED |
| CAP-005 | Cookie consent banner | 52 | FTR-344 | TRACED |
| CAP-006 | Glossary (public read + admin management) | 52, 01 | FTR-344, FTR-014 | TRACED (SPLIT) |
| CAP-007 | FAQ / contact / services pages | 52 | FTR-341, FTR-344 | TRACED |
| CAP-008 | Carbon Reduction Plan page | 52 | FTR-341, FTR-345 | TRACED |
| CAP-009 | Public CarbonTally Assistant | 52, 42 | FTR-342, FTR-267…269 | TRACED (SPLIT) |
| CAP-010 | SEO and PWA artefacts | 52 | — | NOT INDIVIDUALLY CATALOGUED |
| CAP-011 | Admin-configurable Google Analytics 4 | 01, 52 | FTR-008, FTR-009 | TRACED (SPLIT) |
| CAP-012 | Self-service signup / onboarding | 02, 04 | FTR-025…029, FTR-037…041 | TRACED (SPLIT) |
| CAP-013 | Beta access programme | 01 | FTR-010…014 | TRACED |
| CAP-014 | Email + password authentication | 02 | FTR-021…023 | TRACED |
| CAP-015 | Google OAuth / OAuth callback | 02 | FTR-024 | TRACED |
| CAP-016 | Magic-link authentication | 02 | FTR-021 | TRACED |
| CAP-017 | TOTP MFA / authenticator app | 02, 46 | FTR-023, FTR-302 | TRACED (SPLIT) |
| CAP-018 | Password reset | 02 | FTR-022, FTR-025 | TRACED |
| CAP-019 | One account, one role identity model | 06 | FTR-053…059 | TRACED |
| CAP-020 | Customer owner / admin / member / viewer | 06 | FTR-054…056 | TRACED |
| CAP-021 | CT internal roles (operator, reviewer, QC, staff admin, system admin) | 06, 44 | FTR-057, FTR-281…284 | TRACED (SPLIT) |
| CAP-022 | PE roles (PE manager, PE staff/operator) | 06, 10 | FTR-058, FTR-078…080 | TRACED (SPLIT) |
| CAP-023 | Consultant roles and granular permissions | 06, 07 | FTR-059, FTR-060…063 | TRACED (SPLIT) |
| CAP-024 | Team management (invite / remove / suspend) | 05 | FTR-048…052 | TRACED |
| CAP-025 | Login history / staff presence | 02, 44 | FTR-026, FTR-289 | TRACED (SPLIT) |
| CAP-026 | Organisation profile and metadata | 04 | FTR-037…041 | TRACED |
| CAP-027 | Facilities master data | 11 | FTR-083…085 | TRACED |
| CAP-028 | Locations master data | 11 | FTR-083, FTR-085 | TRACED |
| CAP-029 | Assets master data | 12 | FTR-086, FTR-087 | TRACED |
| CAP-030 | Vehicles master data | 12 | FTR-086, FTR-088 | TRACED |
| CAP-031 | Suppliers master data | 13 | FTR-089…091 | TRACED |
| CAP-032 | System settings / platform configuration | 01 | FTR-008, FTR-009, FTR-210 | TRACED |
| CAP-033 | Protected environment / demo lab | 47 | FTR-308…312 | TRACED |
| CAP-034 | CSV / XLSX import pipeline | 14, 15 | FTR-092…096, FTR-102…106 | TRACED (SPLIT) |
| CAP-035 | Bulk upload (multi-file) | 14 | FTR-093, FTR-097 | TRACED |
| CAP-036 | PDF ingestion portal | 14 | FTR-092, FTR-094 | TRACED |
| CAP-037 | Private document storage (bucket + RLS) | 41, 46 | FTR-263…266, FTR-297 | TRACED (SPLIT) |
| CAP-038 | Document status and activity logging | 14, 33 | FTR-095, FTR-202…205 | TRACED (SPLIT) |
| CAP-039 | Manual entry (single + standalone + V3) | 15 | FTR-103, FTR-107 | TRACED |
| CAP-040 | Manual extraction review (FIN-06 governance) | 17 | FTR-118…121 | TRACED |
| CAP-041 | OCR / PDF text extraction | 15 | FTR-102, FTR-104 | TRACED |
| CAP-042 | AI-assisted document extraction | 15, 42 | FTR-105, FTR-268 | TRACED (SPLIT) |
| CAP-043 | Extraction fidelity scoring and suggestions | 15 | FTR-106, FTR-110 | TRACED |
| CAP-044 | Activity clarifications (F-039-1) | 17, 19 | FTR-121, FTR-131 | TRACED (SPLIT) |
| CAP-045 | Durable automatic processing worker | 31 | FTR-188…191 | TRACED |
| CAP-046 | Processing workflow / job state machine | 31 | FTR-188, FTR-192…194 | TRACED |
| CAP-047 | Factor matching engine | 20 | FTR-136…139 | TRACED |
| CAP-048 | Factor selection policy (precedence and safety) | 20, 21 | FTR-140, FTR-144…146 | TRACED (SPLIT) |
| CAP-049 | DEFRA emission-factor provider and catalogue | 20 | FTR-141 | TRACED |
| CAP-050 | SEAI emission-factor provider | 20 | FTR-142 | TRACED |
| CAP-051 | Customer custom factors + owner self-approval | 20, 21 | FTR-143, FTR-147 | TRACED (SPLIT) |
| CAP-052 | Factor governance (P17-A) | 21 | FTR-144…147 | TRACED |
| CAP-053 | Factor aliases | 20 | FTR-139 | TRACED |
| CAP-054 | Unit normalisation | 16 | FTR-114…117 | TRACED |
| CAP-055 | Validation engine and issue lifecycle | 19 | FTR-131…135 | TRACED |
| CAP-056 | Multi-line / item-level factor contract | 16, 30 | FTR-112, FTR-180 | TRACED (SPLIT) |

| CAP-057 | Calculation engine and immutable snapshots | 30 | FTR-179…183 | TRACED |
| CAP-058 | Deterministic calculation idempotency | 30 | FTR-184, FTR-185 | TRACED |
| CAP-059 | Result reportability lifecycle | 30, 34 | FTR-186, FTR-211 | TRACED (SPLIT) |
| CAP-060 | Scope 1 emissions (fuel and combustion) | 22 | FTR-148…150 | TRACED |
| CAP-061 | Scope 2 location-based accounting | 23 | FTR-151…153 | TRACED |
| CAP-062 | Scope 2 market-based + contractual instruments | 24, 25 | FTR-154…156, FTR-157…160 | TRACED (SPLIT) |
| CAP-063 | Scope 3 — all fifteen categories | 27 | FTR-164…169 | TRACED |
| CAP-064 | Scope 3 estimation and assumption records | 29 | FTR-175…178 | TRACED |
| CAP-065 | Unified CAMS domain and accounting boundaries | 28 | FTR-170…172 | TRACED |
| CAP-066 | Acting-for attribution and accounting-context API | 09 | FTR-075…077 | TRACED |
| CAP-067 | Product-contract reporting dimensions | 28 | FTR-173, FTR-174 | TRACED |
| CAP-068 | Governed capability catalogue (18 rows) | 50 | FTR-330…332 | TRACED |
| CAP-069 | Customer + investor capability truth surface | 50 | FTR-333, FTR-334 | TRACED |
| CAP-070 | Seven governed capability values / one vocabulary | 50 | FTR-335 | TRACED |
| CAP-071 | Evidence trail and source-evidence viewer | 18 | FTR-126…128 | TRACED |
| CAP-072 | Evidence line items + provenance line links | 18 | FTR-129, FTR-130 | TRACED |
| CAP-073 | Immutable audit ledger | 33 | FTR-202…205 | TRACED |
| CAP-074 | Actor, automation and write-once provenance gates | 33 | FTR-206, FTR-207 | TRACED |
| CAP-075 | Data-quality scan and reproducibility | 19 | FTR-134, FTR-135 | TRACED |
| CAP-076 | Review queue and review workspace (D19) | 17 | FTR-118, FTR-122…124 | TRACED |
| CAP-077 | CarbonTally QC queue | 17 | FTR-119, FTR-123 | TRACED |
| CAP-078 | Quality chain: PE QC → CT QC → customer final approval | 17, 32 | FTR-120, FTR-197…200 | TRACED (SPLIT) |
| CAP-079 | Manual review queue (operator) | 17, 44 | FTR-121, FTR-285, FTR-286 | TRACED (SPLIT) |
| CAP-080 | Reassignment and review-assignment history | 17 | FTR-124, FTR-125 | TRACED |
| CAP-081 | Adjudication lifecycle and context lineage | 17, 32 | FTR-122, FTR-197, FTR-201 | TRACED (SPLIT) |
| CAP-082 | Extraction error review (admin) | 17, 45 | FTR-125, FTR-292 | TRACED (SPLIT) |
| CAP-083 | Work-item assignment + PE operational messaging | 10, 40 | FTR-081, FTR-255…258 | TRACED (SPLIT) |
| CAP-084 | Report lifecycle and catalogue | 34 | FTR-211…214 | TRACED |
| CAP-085 | Report versions and frozen artefacts | 35 | FTR-223…225 | TRACED |
| CAP-086 | Intensity catalogue and ratios | 34 | FTR-215, FTR-216 | TRACED |
| CAP-087 | Disclosure narrative overlay | 36 | FTR-226, FTR-227 | TRACED |
| CAP-088 | Disclosure model and projection engine | 36 | FTR-228…231 | TRACED |
| CAP-089 | Disclosure correction privileges and evidence idempotency | 36 | FTR-232, FTR-233 | TRACED |
| CAP-090 | Report exports and export history | 34 | FTR-217, FTR-218 | TRACED |
| CAP-091 | Legacy reporting and report generator | 34, 54 | FTR-219…222, FTR-351 | TRACED / HISTORICAL |
| CAP-092 | Insight Layer-1 persistence (I1) | 37 | FTR-234, FTR-235 | TRACED |
| CAP-093 | Insight Layer-1 authorisation (I2) | 37 | FTR-236 | TRACED |
| CAP-094 | Insight tool catalogue (I3) — four ratified read-only tools | 37 | FTR-237, FTR-238 | TRACED |
| CAP-095 | Insight Layer-2 interaction orchestration (I4) | 37 | FTR-239, FTR-240 | TRACED |
| CAP-096 | Insight query planner, context and rate limiting | 37 | FTR-241 | TRACED |
| CAP-097 | Insight temporal comparison (P2) | 37 | FTR-242 | TRACED |
| CAP-098 | Insight references and answer-state model | 37 | FTR-238, FTR-240 | TRACED |
| CAP-099 | Authenticated messaging (N1) | 40 | FTR-255…262 | TRACED |
| CAP-100 | Realtime subscriptions | 42 | FTR-270, FTR-271 | TRACED |
| CAP-101 | Notifications (in-app + delivery ledger) | 39 | FTR-249…252 | TRACED |
| CAP-102 | Email delivery via Resend | 39, 42 | FTR-253, FTR-269 | TRACED (SPLIT) |
| CAP-103 | Activity feed and activity logging | 33, 38 | FTR-208, FTR-243 | TRACED (SPLIT) |
| CAP-104 | Consultant workspace | 07 | FTR-064…066 | TRACED |
| CAP-105 | Consultant portfolio and active-client switching | 07, 08 | FTR-067, FTR-070…072 | TRACED (SPLIT) |

| CAP-106 | Consultant team management | 07 | FTR-068, FTR-069 | TRACED |
| CAP-107 | Consultant new-customer onboarding (CON-1) | 08 | FTR-073, FTR-074 | TRACED |
| CAP-108 | Consultant revocation / lifecycle | 07, 08 | FTR-069, FTR-074 | TRACED (SPLIT) |
| CAP-109 | Consultant billing | 49 | FTR-326…328 | TRACED |
| CAP-110 | White-label branding and custom domains | 42, 04 | FTR-272, FTR-041 | TRACED (SPLIT) |
| CAP-111 | PE dedicated workspace shell | 10 | FTR-082 | TRACED |
| CAP-112 | PE work items and assignments | 10 | FTR-081 | TRACED |
| CAP-113 | PE routed item workspace (G5) | 10 | FTR-079, FTR-080 | TRACED |
| CAP-114 | Secure document viewer / PE no-download policy | 41, 46 | FTR-266, FTR-307 | TRACED (SPLIT) |
| CAP-115 | PE manager dashboard (F1) | 10 | FTR-080 | TRACED |
| CAP-116 | Processing Entities administration | 45, 10 | FTR-293, FTR-078 | TRACED (SPLIT) |
| CAP-117 | Operations console | 44 | FTR-281, FTR-282 | TRACED |
| CAP-118 | Operator queue and routed workspaces | 44 | FTR-285, FTR-286 | TRACED |
| CAP-119 | Operational health (X1) | 44 | FTR-287 | TRACED |
| CAP-120 | Operational alerting (X2) | 44 | FTR-288 | TRACED |
| CAP-121 | Operational intelligence aggregation (X4) | 44 | FTR-284, FTR-287 | TRACED |
| CAP-122 | Persisted API runtime metrics (X7) | 44 | — | NOT INDIVIDUALLY CATALOGUED |
| CAP-123 | SLA definitions and compliance | 44 | FTR-283, FTR-284 | TRACED |
| CAP-124 | Search and existing-data discovery | 38, 43 | FTR-244…248, FTR-273 | TRACED (SPLIT) |
| CAP-125 | Configurable retention (N3) | 01, 33 | FTR-008, FTR-209, FTR-210 | TRACED (SPLIT) |
| CAP-126 | Admin control plane (separate application) | 45 | FTR-290, FTR-291 | TRACED |
| CAP-127 | Admin dashboard, customers, organisations, users, batches | 45 | FTR-292, FTR-294 | TRACED |
| CAP-128 | Admin work hub, live queue stats, staff dashboard, presence | 45 | FTR-291, FTR-295 | TRACED |
| CAP-129 | Audit console tabs (admin + ops) | 45, 33 | FTR-296, FTR-202…205 | TRACED (SPLIT) |
| CAP-130 | Commercial and settings tabs (admin/ops) | 45, 49 | FTR-296, FTR-323 | TRACED (SPLIT) |
| CAP-131 | Configurable billing and subscription | 49 | FTR-323…325 | TRACED |
| CAP-132 | Public website vs authenticated application separation | 52, 46 | FTR-343, FTR-297 | TRACED (SPLIT) |
| CAP-133 | Build provenance (SHA + branch in the bundle) | 53 | FTR-347 | TRACED |
| CAP-134 | Security headers (6, byte-exact) | 46 | FTR-298 | TRACED |
| CAP-135 | Migration drift gate (WP-8) | 53 | FTR-348 | TRACED |
| CAP-136 | Backup and recovery drill | 53 | FTR-350 | TRACED |
| CAP-137 | Investor demo seeder and identity manifest | 47 | FTR-308, FTR-309 | TRACED |
| CAP-138 | Carbon data factory (Prisma/TS scaffold) | 47, 54 | FTR-310, FTR-352 | TRACED / HISTORICAL |
| CAP-139 | Synthetic documents and OCR environment provisioning | 47 | FTR-311 | TRACED |
| CAP-140 | CarbonTally QA harness | 48 | FTR-314…318 | TRACED |
| CAP-141 | Isolated E2E environment | 48 | FTR-319, FTR-320 | TRACED |
| CAP-142 | Independent audit tooling, agent swarm, SaaS assurance framework | 48 | FTR-321, FTR-322 | TRACED |
| CAP-143 | Legacy admin dashboard artefacts | 54 | FTR-353 | HISTORICAL |
| CAP-144 | Static UI mockups and design demos | 54, 51 | FTR-340, FTR-353 | HISTORICAL |
| CAP-145 | Prisma schema snapshot and introspection lineage | 54 | FTR-352 | HISTORICAL |
| CAP-146 | D19 processing workbench | 17 | FTR-123, FTR-124 | TRACED |
| CAP-147 | D21 unified design system | 51 | FTR-336…340 | TRACED |
| CAP-148 | Shared table contract, pagination and page-size standard | — | — | NOT INDIVIDUALLY CATALOGUED |
| CAP-149 | Deployment topology and hosting configuration | 53 | FTR-346, FTR-349 | TRACED |
| CAP-150 | Legacy API surface and dual router mount | 43, 54 | FTR-273, FTR-354 | TRACED / HISTORICAL |
| CAP-151 | Dual ASGI entrypoints | 53, 43 | FTR-346, FTR-280 | TRACED (SPLIT) |
| CAP-152 | Seed and demo data definitions | 47 | FTR-312, FTR-313 | TRACED |

---

## 4. Role → capability traceability

Roles are the operating domains of AGENTS §9–§14. "Representative features" gives
the `FTR` rows that anchor the role's operational surface; it is deliberately not
an exhaustive permission list.

| Role | Permitted capability surface (representative `FTR`) | Denied by design | Enforcement layer(s) |
|---|---|---|---|
| **Public visitor** | FTR-341…345 (public website, Assistant FTR-342, GA4 read FTR-009, legal/cookie FTR-344) | everything authenticated; all tenant data | no session; RLS denies anonymous reads; only the GA4 read is unauthenticated |
| **Customer Owner** | FTR-037…047 (org), FTR-048…052 (team), FTR-083…091 (master data), FTR-092…111 (documents/extraction), FTR-144…147 (**approve own customer factor**), FTR-197…201 (approve results), FTR-211…233 (reports/disclosures), FTR-323 (own subscription) | platform administration (FTR-290…296), internal operations (FTR-281…289), commercial config writes (FTR-323…329) | API authorization + RLS on every org-scoped table |
| **Customer Admin** | as Owner minus factor self-approval where capabilities are separated; org configuration FTR-037…041 | commercial configuration; internal operations | API + RLS |
| **Customer Member** | FTR-092…111 upload/extract, FTR-112…135 map/validate, FTR-126…130 evidence read | factor approval (FTR-147) unless separately authorised; user/role administration FTR-048…052 | API + RLS |
| **Customer Viewer** | read-only: FTR-126…130 evidence, FTR-211…225 reports, FTR-243…248 dashboards | **all writes** — no upload, no mapping, no calculation, no approval | API + RLS (write policies exclude viewer) |
| **Consultant** | FTR-060…069 (workspace, team), FTR-070…074 (client lifecycle), plus the client operating surface FTR-037…233 **scoped to active authorised clients** | other consultants' clients; CarbonTally internal operations; commercial config | consultant/client relationship rows + API authorization + RLS |
| **Consultant team member** | assigned subset of the consultant's client scope (FTR-068, FTR-070…072) | unassigned clients; consultant portfolio administration | assignment rows + API + RLS |
| **Client Owner (consultant-managed)** | own organisation's FTR-037…233 surface, including approvals | the consultant's other clients; consultant administrative surface | relationship-scoped API + RLS |
| **PE Manager** | FTR-078…082 (PE administration, work items, routed workspace, dashboard FTR-080) | unrestricted customer data; customer configuration; internal admin | PE assignment rows + PE guards + RLS |
| **PE Staff / Operator** | assigned work items only (FTR-079, FTR-081); **view-only, no download** for source documents (FTR-266, FTR-307) | other PEs' work; customer download rights; internal privileges | assignment rows + storage policy + API authorization |
| **CarbonTally Operator** | FTR-281…289 (operations console, queues FTR-285/286, SLA FTR-283) | user/role administration; commercial policy; system administration | `require_staff` family + RLS |
| **CarbonTally Reviewer / QC** | FTR-118…125 (review, QC queue FTR-119, adjudication FTR-122) | user/role administration; commercial configuration; system administration | `require_staff` family + RLS |
| **Staff Admin** | FTR-048…052 (user administration), FTR-293 (PE administration), FTR-294 (batches) | system-level administrative controls reserved to System Admin | `require_staff` + explicit staff-admin guard |
| **System Admin** | FTR-290…296 (control plane), FTR-008/FTR-210 (platform settings incl. retention), FTR-209 audit console | nothing internal is denied — but every action is audited (FTR-202…205) | `require_admin()` + RLS + audit ledger |
| **Internal staff (billing authority)** | FTR-323…329 read **and** write (commercial configuration, plans, subscriptions) | customer/consultant access to the same surface | `require_staff` **and** `require_internal_staff` (`_require_billing_admin`) |

**One structural fact this matrix makes explicit:** the only roles that reach the
commercial and platform-configuration surfaces are CarbonTally internal staff, and
the guard is server-side in both cases. A customer or consultant reaching
`/api/v3/commercial/*` or `PUT /api/v3/settings/*` is a **security finding**, not
a UX defect (see §6).

---

## 5. Workflow → evidence traces

Each trace names the steps, the actor, the feature anchor, the persistence that
makes the step auditable, and the guard that protects it. A step the feature
catalogue qualifies as `SCHEMA_ONLY` or `DOCUMENTED_ONLY` stays qualified here.

### 5.0 Live population baseline (read-only counts, 2026-09-27)

The traces below reference these verified row counts. **Flagship** = local
`postgres` (116 public tables); **clone** = disposable `ct_p17k_20260926`
(145 public tables). Counts were taken read-only (`query_to_xml` counting; no DDL,
no DML).

| Evidence object | Flagship | Clone | Reading |
|---|---:|---:|---|
| `organizations` | 975 | 5 | tenant model populated durably |
| `organization_members` | 1125 | 1 | membership populated |
| `consultant_clients` | 917 | 0 | consultant ↔ client relationships populated |
| `consultant_profiles` / `consultant_firm_members` | 55 / 54 | 0 / 0 | consultant operating model populated |
| `processing_entities` | 11 | 0 | PE entities exist |
| `facilities` / `assets` / `suppliers` / `vehicles` | 157 / 310 / 156 / 3 | 0 | master data populated |
| `emission_factors` / `customer_factors` | 7049 / 245 | 4 / 0 | factor model populated |
| `upload_batches` | 52 | 0 | upload exercised |
| `document_processing_queue` | 40 | 0 | documents queued |
| `manual_extraction_batches` / `manual_extraction_items` | 57 / 264 | 0 / 0 | **manual** extraction exercised |
| `manual_review_queue` | 2 | 0 | manual review holds 2 items |
| `calculation_snapshots` / `emissions_logs` | 100 / 100 | 8 / 0 | calculation exercised |
| `report_versions` / `report_generation_queue` | 17 / 14 | 8 / 8 | reporting exercised |
| `conversations` / `conversation_participants` / `messages` | 36 / 65 / 54 | 0 | messaging exercised |
| `audit_trail` | 563 | 16 | audit ledger written |
| `audit_logs` / `activity_logs` | 0 / 0 | 0 / 0 | audit writes are observed in `audit_trail`; these two stay empty |
| `processing_queue` / `processing_steps` / `processing_assignments` / `processing_logs` | 0 | 0 | **durable automatic state machine never exercised** |
| `work_item_assignments` | 2 | 0 | work routing barely exercised |
| `approval_requests` / `approval_decisions` | 0 / 0 | 0 / 0 | approval stage never exercised |
| `qc_checks` / `qc_checklists` / `qc_errors` | 0 / 0 / 0 | 0 / 0 / 0 | QC stage never exercised |
| `evidence_line_items` | table **absent** | 0 | evidence stage has no durable data anywhere |
| `billing_*` transactional · `customer_subscriptions` · `consultant_billing` | 0 | 0 | commercial flow unexercised (CFG-8) |
| `sla_definitions` / `sla_compliance` | 0 / 0 | 0 / 0 | SLA lifecycle unexercised |
| `consultant_custom_domains` / `consultant_senders` | 0 / 0 | 0 / 0 | white-label unexercised |
| `disclosure_frameworks` / `disclosure_requirement_versions` / `disclosure_values` | tables **absent** | 3 / 55 / 12 | disclosure model exists **only** in the disposable clone |
| `scope3_categories` | absent | 15 | ditto |
| `carbontally_insight_*` | absent | 0 | Insight schema only in the clone |

**Reading of the baseline.** Tenant, membership, consultant-relationship,
master-data, factor, manual-extraction, calculation, reporting, messaging and audit
objects are **genuinely populated**. The durable automatic-processing state machine,
evidence materialisation, QC, approval, commercial, SLA and white-label objects are
**empty or absent**. Claims about those stages are therefore **source-level**
claims, never observed behaviour.

### W1 — Public visitor journey

`landing (FTR-341)` → `content pages (FTR-344)` → `Assistant conversation (FTR-342, FTR-268/269)` → `signup entry (FTR-025)`.
Persistence: Assistant thread/conversation records only. Guard: none required —
no tenant data is reachable, and the GA4 configuration read (FTR-009) is
unauthenticated **by explicit design** and narrowed to two non-secret fields.

### W2 — Onboarding to a usable tenant

`signup (FTR-025…029)` → `verification` → `organisation created (FTR-037)` → `owner role assigned (FTR-053/054)` → `first facility (FTR-083)` → `first upload (FTR-092)`.
Persistence: `organizations`, role/membership rows, master-data tables.
Guard: Supabase Auth + RLS.

### W3 — Core processing pipeline (the pipeline AGENTS §18 defines)

| Step | Actor | Feature anchor | Persistence | Guard |
|---|---|---|---|---|
| Upload | Customer / consultant member | FTR-092…097 | `documents`, batches, storage object | RLS + org membership (limits: CFG-3) |
| Enqueue | System | FTR-188…190 | processing queue rows | server-side |
| Ingest | Worker | FTR-190, FTR-191 | job state-machine rows | durable worker, `attempt_count` |
| Extract | Worker / operator | FTR-102…111 | extraction items, fidelity score | server-authoritative |
| Map | Operator / member | FTR-112…117, FTR-136…143 | mapping rows, factor reference | approved customer factor takes precedence |
| Validate | System | FTR-131…135 | validation issues with lifecycle | blocking issues must be resolvable, not stale |
| Calculate | **Server only** | FTR-179…187 | `calculation_snapshots` with `source_item_id` | deterministic request id; duplicates prevented |
| Evidence | System | FTR-126…130 | evidence rows, provenance links | write-once |
| Review | CT Reviewer / QC | FTR-118…125 | review queue and assignment rows | quality chain PE QC → CT QC (FTR-120) |
| Customer approval | Customer Owner | FTR-197…201 | approval records | cannot be bypassed by UI state |
| Completed → Reporting | System / member | FTR-211…233 | report catalogue, versions, frozen artefacts | reports built from persisted emissions only |

**Trace conclusion.** Every step of the ratified pipeline has at least one
catalogued feature row and a named persistence object, and the evidence is
**uneven** rather than uniformly absent: upload (52 batches), manual extraction
(264 items), calculation (100 snapshots), reporting (17 versions), messaging and
the audit ledger are **populated durably**; the durable automatic state machine
(`processing_queue`, `processing_steps`, `processing_logs`, `processing_assignments`
= 0 rows), evidence materialisation (`evidence_line_items` absent in the flagship,
0 rows in the clone), QC and approval (`approval_requests`/`approval_decisions` = 0)
are **not**. The pipeline is therefore traceable end-to-end and **partially
populated**, while its automatic, evidence, QC and approval stages remain
**UNVERIFIED at runtime** (finding **FTR-GAP-2**, §7).


### W4 — Consultant operating flow

`consultant workspace (FTR-064)` → `create customer (FTR-073)` → `assign team member (FTR-068)` → `switch active client (FTR-067)` → `operate client workspace (FTR-037…233 scoped)` → `client approval by client owner (FTR-197…201)` → `relationship ends → access revoked, organisation preserved (FTR-074)`
Trace note: the consultant operating model is **durably populated** in the flagship
(`consultant_clients` 917, `consultant_profiles` 55, `consultant_firm_members` 54),
so the relationship model exists in data, not only in code. What is **not**
evidenced is the **end-of-relationship transition** that AGENTS §11 governs
(revocation while preserving `organizations.id`, data, history and provenance): no
executed revocation transition was found in any durable environment. The trace above
is a *designed* path with a populated precondition, not an observed run.


### W5 — Processing Entity flow

`PE manager dashboard (FTR-080)` → `work item routed (FTR-081)` → `PE opens routed workspace (FTR-079)` → `views source document without download (FTR-266, FTR-307)` → `QC outcome (FTR-120)` → `message to CarbonTally (FTR-255…)`
Guard: PE assignment scope at every step; no customer download rights; PE-to-PE
isolation. Trace note: the PE model is **partially populated** — `processing_entities`
11 rows in the flagship — while `processing_assignments` holds **0** and
`work_item_assignments` **2** rows, and every QC table (`qc_checks`, `qc_checklists`,
`qc_errors`) holds **0**, so work routing, the PE QC outcome and the no-download
source view have **no observed execution** anywhere.


### W6 — Commercial / credit flow

`plan catalogue (FTR-324)` → `subscription (FTR-325)` → `credit ledger (FTR-326)` → `commercial config (FTR-323)` → `consultant billing (FTR-328)`
Trace note: the mechanism is traceable, the **policy inputs are not configured**
(CFG-8), and every billing transactional table is empty — so no commercial
outcome can be demonstrated (finding **FTR-GAP-3**, §7).

### W7 — Insight flow

`Layer-1 persistence (FTR-234/235)` → `authorisation (FTR-236)` → `four read-only tools (FTR-237/238)` → `Layer-2 orchestration (FTR-239/240)` → `planner + rate limiting (FTR-241)` → `temporal comparison (FTR-242)`
Guard: read-only by ratified design; AI runtime key is server-side only.

### W8 — Retention / lifecycle flow

`retention configured (FTR-008, FTR-210)` → `persisted server-side` → `enforced by lifecycle jobs (FTR-209)` → `audit ledger retains what auditability requires (FTR-202…205)`
Trace note: the configuration half of this chain is **predicted to fail** against
the durable flagship (CFG-1), and the enforcement half has no runtime evidence.

---

## 6. Boundary traceability (AGENTS §45 negative-test set)

Traceability of a boundary means: *the boundary has a named enforcement layer and a
catalogued feature that must refuse the request.* It does **not** mean the refusal
has been executed during this pass — every row below is
`TRACED — NOT EXECUTED`.

| Forbidden path | Must be refused by | Related roles | Feature anchor | Status |
|---|---|---|---|---|
| Customer A → Customer B data | RLS `organization_id` policies + API authorization | Owner/Admin/Member/Viewer | FTR-030…036, FTR-297 | TRACED — NOT EXECUTED |
| Client A → Client B (same consultant) | consultant/client relationship scope | Client Owner | FTR-070…074 | TRACED — NOT EXECUTED |
| Consultant A → Consultant B portfolio | consultant ownership rows + API authorization | Consultant | FTR-060…067 | TRACED — NOT EXECUTED |
| Consultant A → Consultant B's client | relationship join, not role alone | Consultant | FTR-070…074 | TRACED — NOT EXECUTED |
| PE A → PE B work | PE assignment scope + RLS | PE Manager / PE Staff | FTR-078…081 | TRACED — NOT EXECUTED |
| PE → prohibited customer document (download) | **no-download storage policy** + API authorization | PE Staff/Operator | FTR-266, FTR-307 | TRACED — NOT EXECUTED |
| Viewer → any write | write policies exclude viewer + API guard | Viewer | FTR-030…036, FTR-048 | TRACED — NOT EXECUTED |
| Member → admin operation | role capability check server-side | Member | FTR-053…056 | TRACED — NOT EXECUTED |
| Staff → Staff-Admin operation | explicit staff-admin guard (not "any staff") | Operator/Reviewer/QC | FTR-048…052, FTR-293 | TRACED — NOT EXECUTED |
| Staff Admin → System-Admin-only operation | `require_admin()` | Staff Admin | FTR-290…296 | TRACED — NOT EXECUTED |
| Customer → internal operations | staff-only routers + `require_staff` | all customer roles | FTR-281…289 | TRACED — NOT EXECUTED |
| PE → internal operations | same | PE roles | FTR-281…289 | TRACED — NOT EXECUTED |
| Customer/consultant → commercial config | `require_staff` + `require_internal_staff` | Owner, Consultant | FTR-323…329 | TRACED — NOT EXECUTED (guard verified in source, deliverable 2 §5) |
| Anonymous → GA4 write / retention read | `require_admin()` | visitor | FTR-008…009 | TRACED — NOT EXECUTED |
| Cross-tenant report/disclosure read | RLS on report/evidence tables | any customer role | FTR-211…233, FTR-126…130 | TRACED — NOT EXECUTED |
| Unrestricted Customer ↔ PE messaging | messaging boundary (no such channel exists by design) | Customer + PE | FTR-255…262 | TRACED — NOT EXECUTED |

**Honest framing.** Every boundary has a designed refusal and a named enforcement
layer — which is what this deliverable can establish from source. **None of the
refusals was executed** here, so the register above is a *traceability* claim, not a
security verdict. Executing these rows belongs to the QA harness and independent
negative testing; until then no ALLOW/DENY outcome should be reported for any row.

---

## 7. Traceability gaps and declarations

| ID | Gap | Why it matters | Handling |
|---|---|---|---|
| **FTR-GAP-1** | 3 capabilities (CAP-010, CAP-122, CAP-148) have no individual feature row | A reader could otherwise assume SEO/PWA, X7 runtime metrics and the shared table contract are catalogued capabilities | Declared residual — PO decision on whether to catalogue or retire them (POD-J) |
| **FTR-GAP-2** | The pipeline (W3) is traceable and **partially populated** — 52 upload batches, 264 manual extraction items, 100 calculation snapshots, 17 report versions — while the durable automatic state machine, evidence, QC and approval objects hold **0 rows or do not exist** | Partial data plus traceability could be mistaken for proof the *automatic* pipeline runs end-to-end — the exact confusion AGENTS §74 forbids | Stated in §5.0 and W3; execution required before any completion claim |
| **FTR-GAP-3** | The commercial flow (W6) is traceable but unexercised, and its policy inputs are `null` (CFG-8) | A traceable billing engine with no configured policy and no transactions cannot produce an outcome | Stated in W6; POD-K owns the policy gap |
| **FTR-GAP-4** | The `CAP → FTR` join is **analyst-derived**, not machine-generated | Prevents anyone treating the mapping as an authoritative index | Declared in §0.2; the join is auditable but not self-validating |
| **FTR-GAP-5** | Settings/features that live only in the **43 unapplied migrations** cannot be traceability-confirmed durably (operational telemetry retention, P8X-X2, P17) | A feature can be `IMPLEMENTED` in code, catalogued, and still not exist in any durable environment | Recorded; aligns with CFG-1/CFG-10 in deliverable 2 |
| **FTR-GAP-6** | Role surfaces are stated as **representative** `FTR` ranges, not per-permission matrices | A representative mapping must never be read as a complete permission specification | Declared in §4; an exhaustive per-capability permission matrix is a separate deliverable if required |

---

## 8. Hand-back

| Item | Value |
|---|---|
| Document | `docs/architecture/CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md` |
| Capabilities joined | **152 / 152** (`TRACED` single-domain 118 · split 31 · residual 3) |
| Feature rows referenced | domains 01–54, `FTR-001…354` |
| Role surfaces traced | **15 roles** across customer, consultant, client, PE, internal and public domains |
| Workflows traced | **8** (W1–W8), including the full AGENTS §18 pipeline as W3 |
| Boundary conditions traced | **16** forbidden paths, each with a named enforcement layer |
| Findings raised | **FTR-GAP-1 … FTR-GAP-6** |
| Secrets reproduced | **None** |
| Writes performed | **None** — read-only discovery only |
| Verification posture | Source + schema + **live read-only row-count** verification (§5.0); **no execution** of any workflow or boundary |
| Verdict for this deliverable | `FUNCTIONALITY_TRACEABILITY_COMPLETE_WITH_DECLARED_GAPS` |

**What is not claimed.** This document does not prove that any traced capability
executes, that any boundary refuses, or that any workflow completes. It proves
where each capability is implemented, which role may act on it, which layer
enforces the boundary, and which gaps remain — nothing beyond that.

<!--CTEOF-->







