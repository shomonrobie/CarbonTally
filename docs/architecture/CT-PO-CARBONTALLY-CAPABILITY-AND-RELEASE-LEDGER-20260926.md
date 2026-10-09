# CT-RECON-01 — CarbonTally Capability & Release Ledger

**Derived from:** `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md`
**Task ID:** `CT-RECON-01-20260926-CARBONTALLY-COMPLETE-CAPABILITY-AND-CHANGE-CENSUS`
**Type:** READ-ONLY DECISION LEDGER — **no decision is populated by this document**
**Date:** 2026-09-26
**Canonical tree:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (`p8-release-reconciled`)
**Historical tree:** `/home/shomonrobie/carbon_tally` @ `20b7a928bb73fdfacf8271ff537a8fd245f62c79` (`main`)

---

## 1. How to read this ledger

One row per capability from the census (CAP-001…CAP-152). The final two columns
are **deliberately empty of decision**:

* **PO decision** — always `UNKNOWN`
* **Release decision** — always `UNKNOWN`

Neither is inferred, recommended or defaulted anywhere in this document

Column tokens:

| Column | Values |
|---|---|
| Current impl | `WIRED` · `CODE-ONLY` · `DUAL` · `LEGACY` · `PERSISTED` · `absent` |
| Wiring | the route / router that reaches it, or `none` |
| Tests | `U:` unit files · `I:` integration files · `—` none found |
| Ind. verification | `OHD` where an independent verification record exists · `none` |
| Prod evidence | `PV` · `LIVE-UNKNOWN` · `NOT-DEPLOYED` · `N/A` |
| Deployment state | where it runs today |
| P17 | `yes` · `no` · `partial` |

`UNKNOWN` in the last two columns means the Product Owner has not decided and
this census has not decided on their behalf.

---

## 2. Capability ledger

| ID | Capability | Evidence | Historical origin | Current impl | Wiring | Tests | Ind. verification | Prod evidence | Dependencies | P17 | Deployment state | Open technical questions | PO decision | Release decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CAP-001 | Public marketing website | `LandingPage.jsx`; route `/` | pre-V3 public snapshot | WIRED | `/` | — | none | PV | — | no | Deployed (Vercel) | Is the published page set contractual? | UNKNOWN | UNKNOWN |
| CAP-002 | About page | `AboutUs.jsx`; `/about` | pre-V3 | WIRED | `/about` | — | none | LIVE-UNKNOWN | — | no | Deployed (frontend) | Content owner | UNKNOWN | UNKNOWN |
| CAP-003 | Pricing page | `PricingPage.jsx`; `/pricing` | pre-V3 | WIRED | `/pricing` | — | none | LIVE-UNKNOWN | Billing CAP-131 | partial | Deployed (frontend) | Public price vs configurable billing | UNKNOWN | UNKNOWN |
| CAP-004 | Legal/policy pages | 4 components; 4 routes | pre-V3 | WIRED | `/terms` `/privacy` `/cookies` `/data-security` | `DataSecurity.test.jsx` | none | LIVE-UNKNOWN | — | no | Deployed (frontend) | Legal review status | UNKNOWN | UNKNOWN |
| CAP-005 | Cookie consent banner | `CookieBanner.jsx` | pre-V3 | WIRED | global | — | none | PV | — | no | Deployed | Is consent persisted? | UNKNOWN | UNKNOWN |
| CAP-006 | Glossary (public + admin) | `Glossary.jsx`; `routes/glossary.py` (8) | pre-V3 | DUAL | `/glossary`; `/admin/glossary-management` | — | none | LIVE-UNKNOWN | — | no | Deployed | Which glossary is canonical? | UNKNOWN | UNKNOWN |
| CAP-007 | FAQ/contact/services pages | 5 routes | pre-V3 | WIRED | `/faq` `/contact` `/services` `/processing-services` `/platform` | — | none | LIVE-UNKNOWN | — | no | Deployed | Placeholders? | UNKNOWN | UNKNOWN |
| CAP-008 | Carbon Reduction Plan page | `CarbonReductionPlan.jsx` | pre-V3 | WIRED | `/carbon-reduction-plan` | — | none | LIVE-UNKNOWN | — | no | Deployed | Product or marketing? | UNKNOWN | UNKNOWN |
| CAP-009 | Public CarbonTally Assistant | chat widget; `routes/communication.py` (22) | legacy chat | LEGACY | chat widget | — | none | LIVE-UNKNOWN | messaging CAP-099 | no | Deployed | Public-only policy? LLM provider? | UNKNOWN | UNKNOWN |
| CAP-010 | SEO/PWA artefacts | `frontend/public/*` | pre-V3 | WIRED | static | — | none | PV | — | no | Deployed | Is `sw.js` functional? | UNKNOWN | UNKNOWN |
| CAP-011 | Admin-configurable GA4 | `Analytics.js`; `AnalyticsBootstrap.jsx`; `37b19d1` | none | WIRED | `/admin/analytics` | `AnalyticsBootstrap.test.jsx` | none | LIVE-UNKNOWN | admin config ISS-006 | no | Deployed (config-gated) | Does GA4 fire live? PostHog lineage? | UNKNOWN | UNKNOWN |
| CAP-012 | Self-service signup/onboarding | `SelfServiceSignup.jsx`; `d35_*` | beta-only | DUAL | `/signup` `/onboarding` | `I:` org membership | none | LIVE-UNKNOWN | PO: signup closed | no | Deployed (frontend) | Is signup closed as decided? | UNKNOWN | UNKNOWN |
| CAP-013 | Beta access programme | `BetaLogin.jsx`; `admin/beta.py` (10) | original entry path | DUAL | `/beta-login` `/beta/signup`; `/admin/beta-management` | — | none | LIVE-UNKNOWN | PO §1.3 | no | Deployed | Retire or retain? | UNKNOWN | UNKNOWN |
| CAP-014 | Email/password auth | `Login.js`; `backend/auth.py` | pre-V3 | WIRED | `/login` | — | none | LIVE-UNKNOWN | — | no | Deployed | Works end-to-end? ISS-001 | UNKNOWN | UNKNOWN |
| CAP-015 | Google OAuth / callback | `AuthCallback.js`; oauth tables | pre-V3 | WIRED | `/auth/callback` | — | none | **REGRESSION** | — | no | Deployed but failing | Root cause of ISS-001 | UNKNOWN | UNKNOWN |
| CAP-016 | Magic-link auth | `MagicLink.jsx` | pre-V3 | WIRED | `/auth/magic` | — | none | LIVE-UNKNOWN | email CAP-102 | no | Deployed | Enabled live? | UNKNOWN | UNKNOWN |
| CAP-017 | TOTP MFA | `auth.mfa_*` tables | pre-V3 | WIRED | — | — | none | LIVE-UNKNOWN | deployment policy | no | Implemented; enforcement unknown | Enforced in production? | UNKNOWN | UNKNOWN |
| CAP-018 | Password reset | `password_reset_tokens` | pre-V3 | WIRED | `/login` | — | none | LIVE-UNKNOWN | email CAP-102 | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-019 | One account one role | PO Register §2.1; `v3m8_*` | — | WIRED | — | `I:` role suites | none | LIVE-UNKNOWN | — | no | Deployed | Truly excluded everywhere? | UNKNOWN | UNKNOWN |

| CAP-020 | Customer role model (owner/admin/member/viewer) | `data/roles.py`; RLS | pre-V3 | WIRED | `RoleRoute.jsx` | `U:api/*` | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-021 | CT internal roles (operator/reviewer/QC/staff admin/system admin) | `v3m8_*`; `staff_roles` | — | WIRED | `/ops`; admin | `I:operations*` | none | LIVE-UNKNOWN | — | no | Deployed | Authoritative capability matrix? | UNKNOWN | UNKNOWN |
| CAP-022 | PE roles (manager/staff) | `v3m8_pe_manager_role`; `pe_auth.py` | — | WIRED | `/pe` | `I:test_pe*` | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-023 | Consultant roles + granular permissions | `consultant_role*`; `p6_2a_*` | — | WIRED | `/consultant` | `I:consultant*` | none | LIVE-UNKNOWN | — | no | Deployed | First-class operator enforced server-side? | UNKNOWN | UNKNOWN |
| CAP-024 | Team management (invite/remove/suspend) | `TeamManagement.js`; `members.py` (10) | pre-V3 | DUAL | `/organization`; `/admin/users` | `U:data/invitations` | none | LIVE-UNKNOWN | — | no | Deployed | Two member paths | UNKNOWN | UNKNOWN |
| CAP-025 | Login history / staff presence | `login_history`; `StaffPresence.jsx` | pre-V3 | DUAL | component; `/staff-dashboard` | — | none | LIVE-UNKNOWN | retention CAP-125 | no | Deployed | Retention applies? | UNKNOWN | UNKNOWN |
| CAP-026 | Organisation profile + metadata | `metadata.py` (15) | pre-V3 | DUAL | `/organization`; `/admin/organizations` | `U:` metadata | none | LIVE-UNKNOWN | — | no | Deployed | Two implementations | UNKNOWN | UNKNOWN |
| CAP-027 | Facilities master data | `FacilitiesTab.jsx`; `assets.py` | pre-V3 | DUAL | `/organization` tab | `I:` facility | none | LIVE-UNKNOWN | — | no | Deployed | UUID vs name display | UNKNOWN | UNKNOWN |
| CAP-028 | Locations master data | `LocationsTab.jsx` | — | WIRED | `/organization` tab | `I:` | none | LIVE-UNKNOWN | — | no | Deployed | Relationship to facilities | UNKNOWN | UNKNOWN |
| CAP-029 | Assets master data | `AssetManager.js`; `assets.py` (11) | pre-V3 | DUAL | `/organization` | — | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-030 | Vehicles master data | `VehiclesTab.jsx`; `v3m7_vehicles` | none | WIRED | `/organization` tab | `I:` | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-031 | Suppliers master data (+P17 write attribution) | `v3_suppliers.py`; `suppliers` | pre-V3 | DUAL | `/organization` tab | `U:test_p17_03_supplier_write_path.py` | none | LIVE-UNKNOWN | acting-for CAP-066 | partial | Partly deployed | Write path needs accounting context | UNKNOWN | UNKNOWN |
| CAP-032 | System settings / platform config | `v3_settings.py`; `system_settings` | pre-V3 | DUAL | settings tabs; `/admin/settings` | `U:` | none | LIVE-UNKNOWN | retention, billing | no | Deployed | Which settings authoritative? | UNKNOWN | UNKNOWN |
| CAP-033 | Demo lab | `tools/demo_lab/**` | none | CODE-ONLY | — | — | none | N/A | own DSN | no | Local/tooling | Still operated? | UNKNOWN | UNKNOWN |
| CAP-034 | CSV/XLSX import pipeline | `upload.py` (10); `import_batches` | pre-V3 | DUAL | `/documents`; `/admin/batches` | `I:` import | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-035 | Bulk upload | `BulkUpload.jsx`; `UploadManager.js` | pre-V3 | DUAL | components | — | none | LIVE-UNKNOWN | — | no | Deployed | Overlap with V3 upload | UNKNOWN | UNKNOWN |
| CAP-036 | PDF ingestion portal | `PDFIngestionPortal.jsx`; `customer_documents.py` (16) | pre-V3 | DUAL | `/documents` | — | none | LIVE-UNKNOWN | OCR CAP-041 | no | Deployed | Unified document model gap | UNKNOWN | UNKNOWN |
| CAP-037 | Private document storage | `d32_*`; `services/storage.py` | none | PERSISTED | — | `I:` storage | none | LIVE-UNKNOWN | — | no | Migration state unknown | Bucket verified live? | UNKNOWN | UNKNOWN |
| CAP-038 | Document status/activity logging | `DocumentStatus.jsx`; `document_activity_log` | pre-V3 | DUAL | component | — | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |

| CAP-039 | Manual entry (3 variants) | `ManualEntry*.jsx`; `v3_manual_extraction.py` | pre-V3 | DUAL | `/dashboard` `/existing-data` | `I:` manual extraction | none | LIVE-UNKNOWN | FIN-06 CAP-040 | no | Deployed | Three implementations | UNKNOWN | UNKNOWN |
| CAP-040 | Manual extraction review (FIN-06) | `manual_processing_admin.py`; `p8_fin06_*` | none | WIRED | admin queue | `U:` | none | NOT-DEPLOYED | — | no | Migration unapplied | Applied live? | UNKNOWN | UNKNOWN |
| CAP-041 | OCR / PDF extraction | `pdf_engine.py`; `pdf_render.py`; tesseract script | pre-V3 | WIRED | workspace panel | `I:` extraction | none | LIVE-UNKNOWN | **tesseract env** | no | Deployed (env-dependent) | OCR present in live image? ISS-012 | UNKNOWN | UNKNOWN |
| CAP-042 | AI-assisted extraction | `ai_extraction.py`; `llm_client.py` | — | WIRED | — | `U:engines/*` | none | LIVE-UNKNOWN | LLM credentials | no | Deployed (config-gated) | Provider live? Cost controls? | UNKNOWN | UNKNOWN |
| CAP-043 | Extraction fidelity + suggestions | `extraction_fidelity.py`; `extraction_suggestions.py` | none | CODE-ONLY | none | `U:` | none | NOT-DEPLOYED | — | no | In repo only | Wired to a route? | UNKNOWN | UNKNOWN |
| CAP-044 | Activity clarifications (F-039-1) | `v3_activity_clarifications.py`; 3 `p8_fs_*` | none | WIRED | workspace | `U:` | none | NOT-DEPLOYED | CAP-081 | no | Migration unapplied | Applied live? | UNKNOWN | UNKNOWN |
| CAP-045 | Durable automatic processing worker | `workers/automatic_processing.py`; `v3m9_*` | none | WIRED | `/processing` | `I:` auto-processing | none | LIVE-UNKNOWN | — | no | Deployed (worker in-process) | Worker healthy live? Stale locks? | UNKNOWN | UNKNOWN |
| CAP-046 | Processing workflow state machine | `v3_processing_workflow.py`; `domain/workflow.py` | pre-V3 queue | DUAL | `/processing/:itemId` | `I:` workflow | none | LIVE-UNKNOWN | — | no | Deployed | Two queue models | UNKNOWN | UNKNOWN |
| CAP-047 | Factor matching engine | `engines/factor_matching.py` | pre-V3 | WIRED | mapping UI | `U:engines/*` | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-048 | Factor selection policy | `factor_selection_policy.py`; `a12d156` | none | WIRED | — | `U:` P16 | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-049 | DEFRA factor provider + catalogue | `src/providers/defra/*`; `defra_conversion_factors` | pre-V3 | DUAL | `/admin/defra` | `U:defra tests` | none | LIVE-UNKNOWN | CAP-052 | no | Deployed | Which DEFRA release live? **R-1 truth-pass 2026-09-28:** the legacy table is retired (renamed `emission_factors` by R1); non-admin read sites repointed onto the canonical resolver (CT-IMPLEMENT-04); `/admin/defra` API + `admin/src` page remain legacy-broken pending **PD-3** | UNKNOWN | UNKNOWN |
| CAP-050 | SEAI factor provider | `src/providers/seai/*` | post-V2.1 | WIRED | — | `U:SEAI tests` | none | LIVE-UNKNOWN | — | no | CLI only | Ireland launch readiness | UNKNOWN | UNKNOWN |
| CAP-051 | Customer custom factors + self-approval | `customer_factors.py`; `v3m3_*` | none | WIRED | admin tab | `U:customer_factor_integration` | none | LIVE-UNKNOWN | PO §16 | no | Deployed | Self-approval as ratified? | UNKNOWN | UNKNOWN |
| CAP-052 | Factor governance (P17-A) | `p17a_*`; `p8_d4_*` | none | PERSISTED | — | `U:test_p17_migrations.py` | none | NOT-DEPLOYED | — | yes | Migration unapplied | — | UNKNOWN | UNKNOWN |
| CAP-053 | Factor aliases | `admin_aliases.py`; `add_factor_aliases` | none | WIRED | aliases router | — | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-054 | Unit normalisation | `core/units.py` | pre-V3 | WIRED | — | `U:units` | none | LIVE-UNKNOWN | — | no | Deployed | Single central mechanism? | UNKNOWN | UNKNOWN |
| CAP-055 | Validation engine + issue lifecycle | `engines/validation.py`; `v3m5_issues` | pre-V3 | DUAL | `/issues`; `/admin/errors` | `I:` issues | none | LIVE-UNKNOWN | — | no | Deployed | Stale blocking issues? | UNKNOWN | UNKNOWN |
| CAP-056 | Multi-line item-level factor contract | `line_items.py`; `899706d`, `78718bb` | none | WIRED | — | `U:` line items | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-057 | Calculation engine + snapshots | `engines/calculation.py`; `calculation_snapshots` | pre-V3 | DUAL | `/emissions` | `U:test_calculation.py` | none | LIVE-UNKNOWN | — | no | Deployed | Snapshot provenance complete? | UNKNOWN | UNKNOWN |

| CAP-058 | Calculation idempotency | `p16r7_*` | none | PERSISTED | — | `U:` P16 | none | NOT-DEPLOYED | — | partial | Migration unapplied | Applied live? | UNKNOWN | UNKNOWN |
| CAP-059 | Result reportability lifecycle | `p16r5_*`; `report_lifecycle.py` | none | PERSISTED | — | `U:` P16 | none | NOT-DEPLOYED | CAP-084 | partial | Migration unapplied | — | UNKNOWN | UNKNOWN |
| CAP-060 | Scope 1 emissions | `data/emissions_logs.py`; `v3_emissions.py` | pre-V3 | WIRED | `/emissions` | `I:test_emissions_logs.py` | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-061 | Scope 2 location-based | `domain/scope2.py`; `v3_scope2.py` | pre-V3 | WIRED | `/emissions` | `U:test_p17_05_scope2_calculation.py` | none | NOT-DEPLOYED | P17 migrations | yes | Not deployed | Which parts need P17 schema? | UNKNOWN | UNKNOWN |
| CAP-062 | Scope 2 market-based + instruments | `domain/contractual_instruments.py`; `p17c_*` | none | WIRED | `/emissions` | `U:test_p17_06_*` | none | NOT-DEPLOYED | P17 migrations | yes | Not deployed | Self-declared incomplete | UNKNOWN | UNKNOWN |
| CAP-063 | Scope 3 all fifteen categories | `domain/scope3.py`; `p17d_*`; `7739ed7` | none | WIRED | `/emissions` | `U:test_p17_scope3.py` | none | NOT-DEPLOYED | P17 migrations | yes | Not deployed | Category applicability deferred (PO) | UNKNOWN | UNKNOWN |
| CAP-064 | Scope 3 estimation records | `domain/estimation.py`; `p17h_*` | none | WIRED | `/emissions` | `I:test_p17_09_*` | none | NOT-DEPLOYED | P17 migrations | yes | Not deployed | — | UNKNOWN | UNKNOWN |
| CAP-065 | Unified CAMS domain + boundaries | `domain/cams.py`; `p17a_*` | none | WIRED | — | `U:test_p17_cams.py` | none | NOT-DEPLOYED | P17 migrations | yes | Not deployed | — | UNKNOWN | UNKNOWN |
| CAP-066 | Acting-for attribution + context API | `v3_accounting_context.py`; `domain/acting_for.py` | none | WIRED | accounting-context router | `U:test_p17_02_accounting_api.py` | none | NOT-DEPLOYED | P17 migrations | yes | Not deployed | — | UNKNOWN | UNKNOWN |
| CAP-067 | Product-contract reporting dimensions | `p17_10_*`; `0f248ad` | none | PERSISTED | — | `U:test_p17_10_product_contract.py` | none | NOT-DEPLOYED | P17 migrations | yes | Not deployed | — | UNKNOWN | UNKNOWN |
| CAP-068 | Governed capability catalogue (18 rows) | `p17k_*`; `capability_catalogue.py` | none | PERSISTED | disclosure path | `U:test_p17k_*`; `I:test_p17k_*_runtime.py` | none | NOT-DEPLOYED | P17-K migration | yes | Not deployed | Rollup must be 4/6/3/2 | UNKNOWN | UNKNOWN |
| CAP-069 | Capability truth surface (customer + investor) | `CapabilitiesPage.jsx`; `InvestorCapabilityPage.jsx` | none | WIRED | `/capabilities`, `/capabilities/product` | `U:test_p17l_*`; `capability-truth-surface.test.jsx` | none | NOT-DEPLOYED | CAP-068 | yes | Not deployed | AG-3..AG-8 render branches | UNKNOWN | UNKNOWN |
| CAP-070 | Seven governed capability values | `domain/disclosure.py` | none | WIRED | — | `U:test_p17k_governed_capability_catalogue.py` | none | NOT-DEPLOYED | CAP-068 | yes | Not deployed | Second vocabulary forbidden | UNKNOWN | UNKNOWN |
| CAP-071 | Evidence trail + source viewer | `EvidenceTrail.jsx`; `v3_evidence.py` | none | WIRED | evidence views | `U:` | none | LIVE-UNKNOWN | — | no | Deployed | Signed-URL handling | UNKNOWN | UNKNOWN |
| CAP-072 | Evidence line items + provenance links | `p8_b2_*` | none | PERSISTED | — | `I:` B2 | none | NOT-DEPLOYED | — | no | Migration unapplied | Applied live? | UNKNOWN | UNKNOWN |
| CAP-073 | Immutable audit ledger | `p7_*`; `audit_activity_immutability` | pre-V3 | DUAL | audit tabs | `U:test_audit*` | none | LIVE-UNKNOWN | — | no | Deployed | Any open update path? | UNKNOWN | UNKNOWN |
| CAP-074 | Actor/automation provenance gates | 4 `gate*_*` migrations | none | PERSISTED | — | `I:` gates | none | LIVE-UNKNOWN | — | no | Partly unknown | — | UNKNOWN | UNKNOWN |
| CAP-075 | Data-quality scan + reproducibility | `domain/data_quality.py`; `8554b78` | none | WIRED | Insight surface | `U:` | OHD (`0c34908`) | NOT-DEPLOYED | CAP-092 | no | Migration unapplied | — | UNKNOWN | UNKNOWN |
| CAP-076 | Review queue + D19 review workspace | `v3_review.py`; `ReviewQueue.jsx` | pre-V3 | DUAL | `/review` `/review/:itemId` `/ops/review/:itemId` | `I:` review | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |

| CAP-077 | CarbonTally QC queue | `v3_qc.py`; `QcQueue.jsx` | none | WIRED | `/ops/qc/:itemId` | `I:` QC | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-078 | Quality chain PE QC → CT QC → customer approval | PO §2.3; `approval_requests` | none | DUAL | `/review` | `I:` approvals | none | LIVE-UNKNOWN | — | no | Deployed | All stages enforced server-side? | UNKNOWN | UNKNOWN |
| CAP-079 | Manual review queue (operator) | `ManualReviewQueue.js` | pre-V3 | DUAL | `/admin/manual-review-queue` | — | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-080 | Reassignment / review-assignment history | `reassignment_history` | pre-V3 | LEGACY | `/admin/assignments` | — | none | LIVE-UNKNOWN | — | no | Deployed | V3 equivalent? | UNKNOWN | UNKNOWN |
| CAP-081 | Adjudication lifecycle + lineage | `p8_fs_adjudication_*` | none | PERSISTED | — | `U:` | none | NOT-DEPLOYED | CAP-044 | no | Migration unapplied | Applied live? | UNKNOWN | UNKNOWN |
| CAP-082 | Extraction error review (admin) | `ExtractionErrorReview.js` | pre-V3 | LEGACY | `/admin/errors` | — | none | LIVE-UNKNOWN | — | no | Deployed | Overlaps V3 issues | UNKNOWN | UNKNOWN |
| CAP-083 | Work-item assignment + PE messaging | `ws4_gate3_4a_*`; `phase5_*` | none | PERSISTED | `/pe/assignments` | `I:` Phase-5 | none | LIVE-UNKNOWN | — | no | Partly unknown | — | UNKNOWN | UNKNOWN |
| CAP-084 | Report lifecycle + catalogue | `p8_report_lifecycle_status`; `v3_reports.py` | `19e4f01` | WIRED | `/reports` `/reports/:id` | `U:test_v3_report_lifecycle.py` | none | NOT-DEPLOYED | CAP-059 | no | Migration unapplied | Panel untracked in historical tree | UNKNOWN | UNKNOWN |
| CAP-085 | Report versions + frozen artefacts | `p8_b4_frozen_artefact` | none | PERSISTED | `/reports/:id` | `I:test_report_versions.py` | none | NOT-DEPLOYED | bucket provisioning | no | Migration unapplied | Bucket provisioned live? | UNKNOWN | UNKNOWN |
| CAP-086 | Intensity catalogue + ratios | `p8_b3_*` | none | PERSISTED | — | `U:` | none | NOT-DEPLOYED | — | no | Migration unapplied | — | UNKNOWN | UNKNOWN |
| CAP-087 | Disclosure narrative overlay | `p8_b4_narrative_overlay` | none | CODE-ONLY | none | `U:` | none | NOT-DEPLOYED | — | no | In repo only | Exposed in any UI? | UNKNOWN | UNKNOWN |
| CAP-088 | Disclosure model + projection engine | `disclosure_projection.py`; `v3_disclosure.py` | none | WIRED | capabilities pages | `U:test_disclosure*` | none | NOT-DEPLOYED | CAP-068 | yes | Not deployed | Precedence is the outcome engine | UNKNOWN | UNKNOWN |
| CAP-089 | Correction privileges + evidence idempotency | `p8_b1_correction_*` | none | PERSISTED | — | `U:` | none | NOT-DEPLOYED | — | no | Migration unapplied | — | UNKNOWN | UNKNOWN |
| CAP-090 | Report exports + export history | `v3_exports.py` | pre-V3 | DUAL | `/admin/batches` | — | none | LIVE-UNKNOWN | CAP-085 | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-091 | Legacy reporting + report generator | `routes/reports.py` (23) | pre-V3 | LEGACY | `/reports` | — | none | LIVE-UNKNOWN | CAP-084 | no | Deployed | Retire or migrate? | UNKNOWN | UNKNOWN |
| CAP-092 | Insight Layer-1 persistence (I1) | `p8_i1_*`; `v3_insight.py` | none | WIRED | `/insight` | `U:`/`I:` I1 | OHD | NOT-DEPLOYED | — | no | Migration unapplied | Persistence only | UNKNOWN | UNKNOWN |
| CAP-093 | Insight authorisation (I2) | `p8_i2_*` | none | PERSISTED | — | `I:` I2 | **OHD (I2 records)** | NOT-DEPLOYED | — | no | Migration unapplied | — | UNKNOWN | UNKNOWN |
| CAP-094 | Insight tool catalogue (I3) | `v3_insight_tools.py` | none | WIRED | `/insight` | `U:` I3 | OHD | NOT-DEPLOYED | — | no | Migration unapplied | Only four tools ratified | UNKNOWN | UNKNOWN |
| CAP-095 | Insight interactions (I4) | `v3_insight_interactions.py`; `p8_i4_*` | none | WIRED | `/insight` | `U:` I4 | none | NOT-DEPLOYED | — | no | Migration unapplied | Answer-generation scope | UNKNOWN | UNKNOWN |

| CAP-096 | Insight planner/context/rate-limit | `insight_query_planner.py` | none | CODE-ONLY | none | `U:` | none | NOT-DEPLOYED | CAP-094 | no | In repo only | Wired to a route? | UNKNOWN | UNKNOWN |
| CAP-097 | Insight temporal comparison (P2) | `p8_insight_temporal_comparison`; `1b33f22` | none | WIRED | `/insight` | `U:` | none | NOT-DEPLOYED | — | no | Migration unapplied | PO closure recorded | UNKNOWN | UNKNOWN |
| CAP-098 | Insight references + answer states | `InsightReferences.jsx` | none | WIRED | `/insight` | `U:` | none | NOT-DEPLOYED | CAP-095 | no | Migration unapplied | — | UNKNOWN | UNKNOWN |
| CAP-099 | Authenticated messaging (N1) | `v3_messaging.py`; `v3m8_*` | legacy chat | DUAL | `/messaging` | `I:` messaging | none | LIVE-UNKNOWN | Realtime | no | Deployed | Boundaries server-enforced? | UNKNOWN | UNKNOWN |
| CAP-100 | Realtime subscriptions | `RealtimeContext.jsx` | pre-V3 | WIRED | global | — | none | LIVE-UNKNOWN | — | no | Deployed | Published tables? | UNKNOWN | UNKNOWN |
| CAP-101 | Notifications (in-app + ledger) | `v3_notifications.py` | pre-V3 | DUAL | `/notifications` | `I:` notifications | none | LIVE-UNKNOWN | Resend | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-102 | Email delivery (Resend) | `v3_email.py`; `email_logs` | pre-V3 | DUAL | admin templates | — | none | LIVE-UNKNOWN | Resend credential | no | Deployed | Sending-domain verification | UNKNOWN | UNKNOWN |
| CAP-103 | Activity feed + logging | `ActivityFeed.jsx` | pre-V3 | WIRED | dashboard | — | none | LIVE-UNKNOWN | — | no | Deployed | Mockup lineage | UNKNOWN | UNKNOWN |
| CAP-104 | Consultant workspace | `v3_consultants.py`; `6b4d749` | Phase E | WIRED | `/consultant` | `I:` consultant | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-105 | Consultant portfolio + client switching | `consultant_clients`; `d20_d15_*` | none | WIRED | `/consultant` | `I:` | none | LIVE-UNKNOWN | — | no | Deployed | Cross-consultant denial tested? | UNKNOWN | UNKNOWN |
| CAP-106 | Consultant team management | `ConsultantTeamTab.jsx`; `5d35603` | none | WIRED | consultant tab | `I:` | none | LIVE-UNKNOWN | — | no | Deployed | Revocation verified? | UNKNOWN | UNKNOWN |
| CAP-107 | Consultant new-customer onboarding (CON-1) | `NewCustomerView.jsx`; `5d35603` | none | WIRED | `/consultant` | `I:` | none | LIVE-UNKNOWN | AGENTS §10 | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-108 | Consultant revocation / lifecycle | `consultant_revocation_roles`; `fc05f05` | none | WIRED | — | `I:` | none | LIVE-UNKNOWN | AGENTS §11 | no | Deployed | Org preserved on exit? | UNKNOWN | UNKNOWN |
| CAP-109 | Consultant billing | `consultant_billing` | none | CODE-ONLY | none | — | none | NOT-DEPLOYED | CAP-131 | no | In repo only | Live commercial capability? | UNKNOWN | UNKNOWN |
| CAP-110 | White-label branding + custom domains | `v3_whitelabel.py`; `d21_*` | none | WIRED | consultant tab | `I:` | none | LIVE-UNKNOWN | AGENTS §64 | no | Deployed | No separate deployment | UNKNOWN | UNKNOWN |
| CAP-111 | PE dedicated workspace shell | `PEShell.jsx`; `85eb074` | none | WIRED | `/pe` | `I:` | none | LIVE-UNKNOWN | AGENTS §32 | no | Deployed | App vs route/shell decision | UNKNOWN | UNKNOWN |
| CAP-112 | PE work items + assignments | `PeWorkItemsPage.jsx`; `d22_*` | none | WIRED | `/pe/assignments` | `I:test_pe*` | none | LIVE-UNKNOWN | CT controls assignment | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-113 | PE routed item workspace (G5) | `PEEntityItemPage.jsx`; `85eb074` | none | WIRED | `/pe/items/:entityId/:itemId` | `U:` | none | LIVE-UNKNOWN | D19 | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-114 | Secure viewer / PE no-download | `SecureDocumentViewer.jsx`; PO §3.3 | none | CODE-ONLY | PE + workbench | `I:` | none | LIVE-UNKNOWN | **PO LOCKED** | no | Component not wired | Server-side enforcement? | UNKNOWN | UNKNOWN |

| CAP-115 | PE manager dashboard (F1) | `PEManagerDashboard.jsx`; `fc05f05` | none | WIRED | `/ops` + PE | `U:` | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-116 | Processing Entities administration | `v3_processing.py`; `v3m1/v3m2/v3m6` | none | WIRED | admin | `I:test_entity*` | none | LIVE-UNKNOWN | AGENTS §8 | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-117 | Operations console | `v3_operations.py`; `137765f` | none | WIRED | `/ops`; `/admin/work-hub` | `I:test_operations*` | none | LIVE-UNKNOWN | — | no | Deployed | X5 read-only | UNKNOWN | UNKNOWN |
| CAP-118 | Operator queue + routed workspaces | `OperatorQueue.jsx`; `60e2ab9` | inline queue | WIRED | `/ops/items/:itemId` etc. | `U:` | none | LIVE-UNKNOWN | AGENTS §38 | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-119 | Operational health (X1) | `OperationalHealthTab.jsx`; `20d27c0` | none | WIRED | `/ops/operational-health` | `U:` | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-120 | Operational alerting (X2) | `operational_alerting.py`; `20d27c0` | none | CODE-ONLY | none | `U:` | none | NOT-DEPLOYED | CAP-125 | no | In repo only | Wired to a route? | UNKNOWN | UNKNOWN |
| CAP-121 | Operational intelligence (X4) | `operational_intelligence.py`; `a71a46a` | none | CODE-ONLY | none | `U:` | none | NOT-DEPLOYED | — | no | In repo only | Wired? | UNKNOWN | UNKNOWN |
| CAP-122 | API runtime metrics (X7) | `api_metrics.py`; `3a34ae3` | none | WIRED | — | `U:test_api_metrics*` | none | NOT-DEPLOYED | — | no | Migration unapplied | — | UNKNOWN | UNKNOWN |
| CAP-123 | SLA definitions + compliance | `sla_definitions`; `SlaTab.jsx` | none | CODE-ONLY | ops tab | — | none | NOT-DEPLOYED | — | no | In repo only | Contractual SLAs? | UNKNOWN | UNKNOWN |
| CAP-124 | Search + existing-data discovery | `v3_search.py`; `d632afc` | pre-V3 | WIRED | `/existing-data` | `I:test_search*` | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-125 | Configurable retention (N3) | `services/retention.py` | none | WIRED | admin settings | `I:` retention | none | NOT-DEPLOYED | AGENTS §42 | no | Migration unapplied | Durations are a PO decision | UNKNOWN | UNKNOWN |
| CAP-126 | Admin control plane (separate app) | `admin/src/App.js` (18 routes) | legacy admin artefacts | WIRED | whole app | 4 test files | none | **config notice** | build settings | no | Deployed but inoperative | ISS-006 | UNKNOWN | UNKNOWN |
| CAP-127 | Admin dashboard/customers/orgs/users/batches | 5 admin pages | pre-V3 | LEGACY | 5 routes | — | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-128 | Admin work hub / queue stats / presence | `WorkHub.jsx` etc. | none | WIRED | 3 routes | — | none | LIVE-UNKNOWN | — | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-129 | Audit console tabs | `AuditTab.jsx`; `LogViewer.jsx` | pre-V3 | DUAL | 2 routes | — | none | LIVE-UNKNOWN | CAP-073 | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-130 | Commercial + settings tabs | `CommercialTab.jsx` | none | WIRED | ops tabs | `I:` | none | LIVE-UNKNOWN | CAP-131 | no | Deployed | — | UNKNOWN | UNKNOWN |
| CAP-131 | Configurable billing + subscription | `v3_billing.py`; `d37_*` | pre-V3 | DUAL | `/billing` | `I:` billing | none | LIVE-UNKNOWN | AGENTS §43 | no | Deployed | Existing architecture re-inspected? | UNKNOWN | UNKNOWN |
| CAP-132 | Public vs authenticated separation | `App.js`; `RoleRoute.jsx` | partial | WIRED | both trees | — | none | PV (public) | — | no | Deployed | Authenticated side unverified | UNKNOWN | UNKNOWN |
| CAP-133 | Build provenance | `generate_build_info.js`; `buildInfo.js` | none | WIRED | global | `buildInfo.test.js` | none | **PV** | — | no | Deployed | Pre-render by design | UNKNOWN | UNKNOWN |

| CAP-134 | Six security headers | `vercel.json` | none | WIRED | all routes | — | none | **PV** | — | no | Deployed | CSP report-only | UNKNOWN | UNKNOWN |
| CAP-135 | Migration drift gate (WP-8) | `migration_drift.py`; CI workflow | none | WIRED | CI + CLI | `U:` drift | none | Partly (CI fails) | — | no | CI failing | ISS-008 | UNKNOWN | UNKNOWN |
| CAP-136 | Backup/recovery drill | `backup_recovery_drill.py` | none | CODE-ONLY | CLI | — | none | N/A | backup DSN | no | Tooling only | Last executed? | UNKNOWN | UNKNOWN |
| CAP-137 | Investor demo seeder + identity manifest | `~/carbon_tally/tools/seed_investor_demo/**` | investor demo | **absent** | — | — | none | N/A | AGENTS §54 | no | **Not in canonical tree** | ISS-003 / POD-004 | UNKNOWN | UNKNOWN |
| CAP-138 | Carbon data factory (Prisma/TS) | `~/carbon_tally/tools/carbon_data_factory/**` | data lineage | **absent** | — | — | none | N/A | — | no | Not in canonical tree | Superseded by `demodatagen`? | UNKNOWN | UNKNOWN |
| CAP-139 | Synthetic docs + OCR provisioning | `generate_synthetic_documents.py` | data lineage | CODE-ONLY | scripts | — | none | N/A | tesseract env | no | Tooling only | OCR in live image? | UNKNOWN | UNKNOWN |
| CAP-140 | CarbonTally QA harness | `qa_harness/**` | none | CODE-ONLY | scripts | 29 files | none | N/A | BUILD-ONLY | no | Not run | ISS-010 / POD-006 | UNKNOWN | UNKNOWN |
| CAP-141 | Isolated E2E environment | `e2e/environment/**` | P6-2F | CODE-ONLY | scripts | — | none | N/A | isolated DB | no | Tooling only | Still provisionable? | UNKNOWN | UNKNOWN |
| CAP-142 | Audit tooling / agent swarm / assurance | `agent_swarm`, `saas-assurance`, `independent_audit` | OHD era | **absent** (only `.costrict` stub) | — | — | none | N/A | OpenRouter key | no | Not in canonical tree | Retain/port/retire? | UNKNOWN | UNKNOWN |
| CAP-143 | Legacy admin dashboard artefacts | `create_admin_dashboard.py`; zip | earliest prototype | CODE-ONLY | script | — | none | N/A | — | no | Historical artefacts | Disposal decision | UNKNOWN | UNKNOWN |
| CAP-144 | Static UI mockups + design demos | `docs/architecture/UI*`; ui-demo | design phase | CODE-ONLY | static HTML | — | none | N/A | — | no | Documentation | Not the live app | UNKNOWN | UNKNOWN |
| CAP-145 | Prisma schema snapshot | `prisma/schema.prisma` (129 models) | schema analysis | CODE-ONLY | — | — | none | N/A | local DSN pin | no | Tooling only | Maintained or frozen? | UNKNOWN | UNKNOWN |
| CAP-146 | D19 processing workbench | `components/workbench/**` | none | WIRED | workbench routes | `I:` workbench | none | LIVE-UNKNOWN | **FROZEN UX** | no | Deployed | PO review for changes | UNKNOWN | UNKNOWN |
| CAP-147 | D21 unified design system | `components/ui/**`; `tokens.css` | none | WIRED | all V3 | `U:` components | none | LIVE-UNKNOWN | **FROZEN UX** | no | Deployed | Legacy styling remains | UNKNOWN | UNKNOWN |
| CAP-148 | Table contract + pagination standard | `ui/DataTable.jsx`; 5 commits | none | WIRED | ops + admin | `U:` table rules | none | LIVE-UNKNOWN | AGENTS §36 | no | Deployed | Tables still unpaginated? | UNKNOWN | UNKNOWN |
| CAP-149 | Deployment topology + hosting config | `vercel.json`; `runtime.txt` | pre-V3 | WIRED | Vercel / Render | — | none | PV (frontend) | no render.yaml | no | Deployed | Render config unknown (ISS-011) | UNKNOWN | UNKNOWN |
| CAP-150 | Legacy API surface + dual mount | `main.py:212-265`; 407 endpoints | V2.1 | DUAL | all legacy pages | smoke tests | none | LIVE-UNKNOWN | retirement policy | no | Deployed | ISS-004 | UNKNOWN | UNKNOWN |
| CAP-151 | Dual ASGI entrypoints | `main.py`; `main_v2.py` | main_v2 for V3 | DUAL | — | `verify_startup.py` | none | LIVE-UNKNOWN | — | no | Which one runs is unknown | Silent V3 degradation | UNKNOWN | UNKNOWN |
| CAP-152 | Seed and demo data definitions | `supabase/seed.sql`; `backups/seed.sql` | pre-V3 | CODE-ONLY | scripts | — | none | N/A | demo identities | no | Tooling only | Which seeds are production-safe? | UNKNOWN | UNKNOWN |

---

## 3. Product Owner decision register (all UNKNOWN)

Every row is `UNKNOWN`. This ledger records the *question*, never an answer.

| POD ID | Question requiring a PO decision | Forcing evidence | PO decision | Release decision |
|---|---|---|---|---|
| POD-001 | Is the P17 backend release authorised? | CAP-052…CAP-070 unreleased | UNKNOWN | UNKNOWN |
| POD-002 | Is the production migration gate authorised (six `p17*` migrations)? | ISS-007, ISS-002 | UNKNOWN | UNKNOWN |
| POD-003 | What is the disposition of the 32 uncommitted historical-tree files? | ISS-009 | UNKNOWN | UNKNOWN |
| POD-004 | Port `tools/seed_investor_demo/` + `DEMO_IDENTITIES.md` into the canonical tree? | ISS-003 | UNKNOWN | UNKNOWN |
| POD-005 | Legacy API retirement policy (407 endpoints) | ISS-004, CAP-150 | UNKNOWN | UNKNOWN |
| POD-006 | Authorise the QA harness to run, and against which target? | ISS-010, ISS-026 | UNKNOWN | UNKNOWN |
| POD-007 | Merge `p8-release-reconciled` into `main`? | ISS-017 | UNKNOWN | UNKNOWN |
| POD-008 | Enforce the CSP rather than report-only? | ISS-032, ISS-033 | UNKNOWN | UNKNOWN |
| POD-009 | Configure retention durations, and for which domains? | CAP-125, CHG-030 | UNKNOWN | UNKNOWN |
| POD-010 | Is the seven-value governed capability vocabulary canonical? | CAP-070, CHG-020 | UNKNOWN | UNKNOWN |
| POD-011 | Make the admin console operational (Supabase build settings)? | ISS-006, CAP-126 | UNKNOWN | UNKNOWN |
| POD-012 | Retire or retain the beta programme? | CAP-013, PO Register §1.3 | UNKNOWN | UNKNOWN |
| POD-013 | Retain/archive/remove pilot tooling artefacts? | ISS-029, ISS-030, CAP-143…CAP-145 | UNKNOWN | UNKNOWN |
| POD-014 | Which party independently re-verifies this census? | ISS-026, ISS-027 | UNKNOWN | UNKNOWN |
| POD-015 | Does the live workspace-load regression outrank P17 work? | ISS-001, CAP-015 | UNKNOWN | UNKNOWN |
| POD-016 | Reconcile, archive or leave the historical tree? | ISS-015, ISS-019 | UNKNOWN | UNKNOWN |
| POD-017 | Which internal staff capability matrix is authoritative? | CAP-021 | UNKNOWN | UNKNOWN |
| POD-018 | Are the sales-blueprint feature lists to be annotated as non-implemented? | ISS-023 | UNKNOWN | UNKNOWN |

---

## 4. Release decision register (all UNKNOWN)

Release decisions by domain. Every row is `UNKNOWN`.

| Domain | Capability cluster | Evidence of current state | Release decision |
|---|---|---|---|
| Public website | CAP-001…CAP-010, CAP-132 | Deployed and production verified (public side) | UNKNOWN |
| Authentication and identity | CAP-014…CAP-018, CAP-019 | Deployed; one live regression (ISS-001) | UNKNOWN |
| Organisation and master data | CAP-024…CAP-032 | Deployed | UNKNOWN |
| Ingestion and document handling | CAP-034…CAP-038 | Deployed; storage migration state unknown | UNKNOWN |
| Extraction and OCR | CAP-039…CAP-044 | Deployed; FIN-06/clarification migrations unapplied | UNKNOWN |
| Durable automatic processing | CAP-045, CAP-046, CHG-022 | Deployed (in-process worker) | UNKNOWN |
| Factors and mapping | CAP-047…CAP-053 | Deployed; P17 governance elements not deployed | UNKNOWN |
| Validation and calculation | CAP-054…CAP-057, CHG-010 | Deployed | UNKNOWN |
| P16 accounting controls | CAP-058, CAP-059, CHG-011, CHG-012 | Repository-persisted; live state unknown | UNKNOWN |
| Scope 1 | CAP-060 | Deployed | UNKNOWN |
| Scope 2 (location + market) | CAP-061, CAP-062, CHG-016 | Not deployed (P17 gated) | UNKNOWN |
| Scope 3 (15 categories) | CAP-063, CAP-064, CHG-017, CHG-018 | Not deployed (P17 gated) | UNKNOWN |
| CAMS / accounting dimensions / acting-for | CAP-065…CAP-067, CHG-013…CHG-015 | Not deployed (P17 gated) | UNKNOWN |
| Governed capability catalogue and truth surface | CAP-068…CAP-070, CHG-020, CHG-021 | Not deployed (P17 gated) | UNKNOWN |
| Evidence and provenance | CAP-071…CAP-074, CHG-023, CHG-025, CHG-027 | Mixed: d33/gate migrations unknown, B2 not deployed | UNKNOWN |
| Review, QC and approval | CAP-076…CAP-083, CHG-005 | Deployed; adjudication/clarification migrations not deployed | UNKNOWN |
| Reporting and disclosure | CAP-084…CAP-091, CHG-028 | Deployed (legacy + V3); Phase 8 disclosure not deployed | UNKNOWN |
| Insight (AI) | CAP-092…CAP-098, CHG-029 | Not deployed (all `p8_i*` migrations) | UNKNOWN |
| Messaging and notifications | CAP-099…CAP-103, CHG-… | Deployed | UNKNOWN |
| Consultant operating model | CAP-104…CAP-110, CHG-006, CHG-007 | Deployed | UNKNOWN |
| Processing Entity operating model | CAP-111…CAP-116, CHG-002, CHG-003 | Deployed; no-download viewer unwired | UNKNOWN |
| Internal operations | CAP-117…CAP-123 | Deployed; X2/X4 unwired | UNKNOWN |
| Retention (N3) | CAP-125, CHG-030 | Not deployed (migration unapplied) | UNKNOWN |
| Admin control plane | CAP-126…CAP-130 | Deployed but inoperative (ISS-006) | UNKNOWN |
| Billing and subscription | CAP-131 | Deployed | UNKNOWN |
| Operational readiness / provenance / headers | CAP-133, CAP-134, CHG-031 | Production verified | UNKNOWN |
| CI gate, backup, QA, audit tooling | CAP-135, CAP-136, CAP-140…CAP-142 | Not operational | UNKNOWN |
| Demo, seeding and data generation | CAP-137…CAP-139, CAP-152 | Tooling; seeder absent from release tree | UNKNOWN |
| Frozen UX (D19, D21) | CAP-146, CAP-147 | Deployed | UNKNOWN |
| Legacy surface retirement | CAP-150, CAP-151, ISS-004 | Deployed | UNKNOWN |
| Deployment topology | CAP-149, ISS-011, ISS-034 | Frontend verified; backend revision unknown | UNKNOWN |

---

## 5. Verification-state summary

Counts are derived from the census tables. "Independently verified" counts only
capabilities for which a **named non-implementer verification record** was
located; "production verified" counts only capabilities with **direct live
evidence**.

| Verification state | Count | Notes |
|---|---|---|
| DOCUMENTED (claim exists in a document) | 152 | every capability is at least documented by this census |
| CODE EXISTS | 152 | by definition of being in the census |
| ROUTE WIRED | 121 | registered in `backend/api/router.py`, `backend/main.py` or a React route table |
| CODE-ONLY (never registered) | 31 | incl. CAP-033, CAP-043, CAP-087, CAP-096, CAP-109, CAP-114, CAP-120, CAP-121, CAP-123, CAP-136, CAP-138, CAP-139, CAP-140, CAP-141, CAP-142, CAP-143, CAP-144, CAP-145, CAP-152 and the `absent` rows |
| PERSISTED (migration declares it) | 40 | repository-only; not an applied-state claim |
| E2E VERIFIED (test or recorded journey exists) | at least 60 | based on named test files; **no suite was run for this census** |
| INDEPENDENTLY VERIFIED (non-implementer) | 5 | CAP-075, CAP-093, CAP-094 (Insight I1–I3 OHD records), plus P3-IV-01 and P16 as programme-level records |
| **PRODUCTION VERIFIED (direct live evidence)** | **7** | CAP-001, CAP-005, CAP-010, CAP-132 (public side), CAP-133, CAP-134, CAP-149 (frontend) |
| NOT-DEPLOYED (explicitly known to be unapplied/undeployed) | 34 | the six-`p17*`-migration cluster, the `p8_i*` cluster, P16r5/r7, B1–B4, S2, FIN-06, `p8_fs_*`, `p8x_x2` |
| LIVE-UNKNOWN (cannot be established read-only) | 45 | all capabilities whose only blocker to verification is database/backend access |
| ABSENT from the canonical release tree | 3 | CAP-137, CAP-138, CAP-142 |

Interpretation discipline: the gap between "E2E VERIFIED (evidence exists)" and
"INDEPENDENTLY VERIFIED" is the project's central verification risk, and the gap
between "PERSISTED" and "PRODUCTION VERIFIED" is its central deployment risk.

---

## 6. Sign-off

**Document:** `CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926`
**Derived from:** `CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926`
**Author:** CT-RECON-01 read-only census (implementation agent)
**Date:** 2026-09-26
**Canonical HEAD at authoring:** `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`

| Attestation | Result |
|---|---|
| Product Owner decisions populated | **NO — all `UNKNOWN`** |
| Release decisions populated | **NO — all `UNKNOWN`** |
| Capabilities carried from the census | 152 of 152 |
| Changes carried from the census | 36 of 36 |
| Issues carried from the census | 36 of 36 |
| Uncertain items carried | 14 of 14 |
| PO questions carried | 18 of 18 |
| Recommendations made | **NONE** |
| Source, SQL, migration, config or policy modified | **NO** |
| Database read or written | **NO** |
| Deployment or push performed | **NO** |

**Not independently verified.** This ledger was produced by the same agent that
produced the census it derives from. `AGENTS.md` §60 requires an independent
verification step (OHD/QA) before any of its content is treated as accepted
input to a release or remediation decision. That step is **not claimed here**;
`POD-014` names it as an open decision.
