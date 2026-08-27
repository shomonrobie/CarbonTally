# CarbonTally V3 — Platform Finalization Report

**Author:** Cline (implementation engineer)
**Date:** 26 August 2026
**Scope:** Master Platform Finalization Program (Phases 0–19)
**Status:** Interim — substantial hardening completed; deployment dependencies and legal/policy items remain open (see §18–§20).

> **CORRECTION (26 Aug 2026):** The earlier finding "`emission_factors` = 0 rows in the local DB" was an **environment/instance mismatch**, not data loss. The actual CarbonTally database contains **7,049 rows (7,029 DEFRA-2025 + 20 SEAI-2025)**, as verified by the Product Owner. See the **DATABASE ENVIRONMENT DISCREPANCY** section (§11a) for the full explanation.

---

## 1. Baseline

| Item | Value |
|---|---|
| Working tree HEAD (local) | `9458067c073bdaedae2a621b9cee42e419f14a75` (`feat(v3): commit D20-D37 commercial platform release`) |
| Canonical `origin/main` (remote) | `d4dcca1eb11f86bcae497815c8592d688a7e305f` (same commit message) |
| Tree equivalence | `git diff --stat 9458067 d4dcca1` shows **only 2 files** removed in the canonical tree (`backend - backup.zip`, `create_admin_dashboard.py`). Content is otherwise identical; the SHA divergence is a consequence of the earlier git-history secret remediation rewrite. |
| Worktree state at start | 760 changed/untracked entries — the vast majority are a skills-framework reorganisation (`.agents/`, `.claude/`, `.windsurf/`), line-ending churn across `backend/` and `frontend/` (balanced `+N/-N` per file, no content change), and untracked documentation. **None of these were touched, reset, cleaned or stashed.** |
| Local stacks | New Supabase stack (Docker `supabase_*_carbon_ledger`) at `127.0.0.1:54425` (API) / `54426` (Postgres), Studio `54423`; older stack at `54323–54326` still running. |

**Baseline test run:** full `tests/unit` suite → **exit code 0** (no failures) before any change.

---

## 2. Findings Reviewed

All reports in `docs/audit/openhands/` were read, including the two sub-directory audits:

- `CARBONTALLY_V3_INDEPENDENT_PRODUCT_PLATFORM_AUDIT_FLASH.md`
- `CARBONTALLY_V3_PE_SECURITY_AUDIT.md` (F1–F6 findings)
- `CARBONTALLY_V3_INDEPENDENT_REGULATORY_AND_DATA_RESIDENCY_AUDIT.md`
- `CARBONTALLY_V3_BANGLADESH_PROCESSING_ENTITY_LEGAL_POLICY_RESEARCH.md` (legal/policy, read-only)
- `extraction-mapping-calculation/CARBONTALLY_V3_EXTRACTION_MAPPING_CALCULATION_CAPABILITY_AUDIT.md`
- `extraction-recovery/CARBONTALLY_V3_HISTORICAL_EXTRACTION_RECOVERY_AUDIT.md`
- `CARBONTALLY_V3_WEBSITE_PRELAUNCH_REFACTOR_REPORT.md` + `_FLASH.md`
- `QA_REPORT_V3_FINAL.md`
- Supporting `docs/audit/cline/` reports (D28–D37, identity/workspace, security hardening).

Findings were **cross-checked against the code** (not taken at face value). Verified independently:

- Scanned-PDF OCR bug (`convert_from_path(io.BytesIO(...))`) — confirmed present in `backend/pdf_engine.py`.
- Forced Windows tesseract path in `PDFExtractor.__init__` — confirmed (this additionally broke OCR on Linux/Render).
- Legacy `/upload` route calls the PDF method for images — confirmed (`routes/upload.py`).
- F2 IDOR (batch stats/progress) — confirmed.
- F3 (`require_org_admin` 500-vs-403) — confirmed at `auth.py`.
- F4 (`current_user.id` AttributeError sweep) — confirmed, 171 references.
- F1 (entity read endpoints not gated on `entity.status='active'`) — confirmed.
- Additional latent defects found: `get_batch_stats` lacked `except HTTPException: raise` (403→500) and shadowed the FastAPI `status` import with a loop variable (`UnboundLocalError` → 500); three legacy batch endpoints dereferenced a possibly-`None` `maybe_single` result (`if not member.data` → AttributeError → 500).

---

## 3. Existing Capabilities Preserved (no rebuild)

- CSV/Excel mapping (`utils/emissions.py` `process_*_data`, `routes/upload.py` `/upload-csv`) — untouched.
- Customer Custom Emission Factors — untouched (verified path via `repos.customer_factors`).
- DEFRA / Irish-SEAI factor architecture (single `emission_factors` table, discriminated by `factor_source/factor_set/country`) — untouched.
- `CalculationEngine` (immutable SHA-256 snapshots, `verify()`) — untouched.
- Row-level traceability chain (D33: `organization_files → manual_extraction_items → calculation_snapshots → emissions_logs`) — untouched.
- V3 extraction engines (`engines/extraction.py`, `ai_extraction.py`, `workflow.py`) — untouched (still engine-level; wiring assessed below).
- Processing Entity workflow, review/QC/approval, private storage + signed URLs (D32), billing (D37) — untouched.
- Demo identities — preserved; **password reset only** (see §16).
---

## 4. Changes Made

### 4.1 Extraction recovery (Phase 3)
`backend/pdf_engine.py`
- `_extract_text_ocr` now uses `pdf2image.convert_from_bytes` (the bytes API) instead of `convert_from_path(io.BytesIO(...))` — fixes scanned-PDF OCR silently returning no text.
- Page-boundary markers (`[page N]`) added to OCR output; empty pages skipped.
- Tesseract binary is resolved from `TESSERACT_CMD` or the system PATH — the unconditional Windows path that broke OCR on Linux/Render was removed.

`backend/routes/upload.py`
- Legacy `/upload` now dispatches image files to `extract_and_parse_image` (was calling the PDF method → images could never be OCR'd).

New tests: `backend/tests/unit/engines/test_pdf_engine.py` (OCR bytes-API, page markers, tesseract resolution, OCR fallback, image path, image error surfacing).

### 4.2 PE security audit fixes (Phase 10)
- **F1 (P2):** entity-staff read access now requires `entity.status == 'active'` on the entity dashboard (`api/v3_operations.py`), entity performance report (`api/v3_reporting.py`) and entity issues list (`api/issues.py`). CarbonTally internal staff retain read access for administration/oversight.
- **F2 (P2):** `GET /api/batches/{id}/progress` now enforces org membership (it had **no** authorization check); `GET /api/batches/stats?organization_id=…` now verifies the caller is a member of the requested org (or a global admin).
- **F3 (P3):** `require_org_admin`'s authoritative fallback no longer calls `get_supabase_client()` outside its `try/except` — Supabase-init failure now fails closed with 403 instead of 500.
- **F4 (P3):** 171 `current_user.id` references swept to `current_user.user_id` across 17 legacy route files (all `AuthUser` usages; the one comment referencing the old name preserved).
- **Additional latent fixes:** `get_batch_stats` gained `except HTTPException: raise`; the `status` loop variable was renamed to `batch_status` (un-shadowing FastAPI's `status`); `get_batch_status` / `get_batch_progress` / `cancel_batch` / `get_batch_stats` now guard a possibly-`None` `maybe_single` result before reading `.data` (fail closed 403).

New tests: `backend/tests/unit/api/test_legacy_upload_idor.py` (6 cases) and F1 regression tests in `test_reporting.py`, `test_v3_operations.py`, `test_v3_issues.py`.

### 4.3 Public website integration (Phase 14)
- Copied the verified OpenHands website candidate (`website_candidate/`, source branch `openhands/public-website-visual-refactor`, HEAD `2fd4345`) into the canonical frontend:
  - New `frontend/src/public/**` (PageShell, Platform, Services, Processing, Consultants, Contact pages, glossary data, interactive demos, `public-site.css`).
  - Replaced the public marketing/legal root pages (Landing, Pricing, About, Glossary, CarbonReductionPlan, CookieBanner, CookiePolicy, Privacy, Terms) and the shared public-only `AppHeader`/`AppFooter` and `App.css`.
  - Copied public static assets (`index.html`, favicon, logos, manifest, robots, sitemap).
- `frontend/src/App.js`: added routes `/platform`, `/services`, `/processing-services`, `/consultants`, `/pricing`, `/contact`; **removed the duplicate `/privacy` route** (the audit's C7: `/privacy` rendered PricingPage, leaving Privacy unreachable); **removed the duplicate legacy `/dashboard/*` route** (kept the redirect to `/home`). All V3 authenticated routes are preserved untouched.
- Verified: `npm run build` → success ("Compiled with warnings", exit 0). The built bundle contains the new pages.
- **STOP-condition consideration:** `AppHeader`/`AppFooter`/`App.css` are consumed **only** by public pages in the canonical app (authenticated workspace uses `V3Layout`'s own chrome), so authenticated-application behavior is unchanged.

---

## 5. Legacy Routes Removed

No legacy route was hard-deleted in this pass; instead the legacy document surface was **hardened and de-scoped**:

- The only legacy document/upload endpoints that remain exposed are now authorization-scoped (F2 fix) and the image/OCR dispatch regression was repaired (so the remaining legacy extraction path actually works).
- The duplicate/legacy `/dashboard/*` application route was removed from the frontend (replaced by the `/home` redirect) and the duplicate `/privacy` route was removed.
- `backend/routes/upload.py` `/test-upload`, `/repair-pdf`, `/upload-batch`, `/upload`, `/upload-pdf`, `/upload-csv`, and the batch endpoints remain registered and are catalogued in `API_ENDPOINTS.md`.

**Recommendation (needs a controlled follow-up, not done here):** the legacy upload surface (`/api/upload*`, `/api/upload-pdf`, `/api/upload-batch`, `/api/repair-pdf`, `/api/test-upload`, `/api/batches/*`) is superseded by `/api/v3/uploads`, `/api/v3/batches`, `/api/v3/documents` and should be decommissioned in a dedicated change after (a) the still-rendered legacy `PDFIngestionPortal.jsx` and its routes are removed from `App.js`, and (b) CSV/Excel processing is verified to have a V3 or retained-legacy home. Removing them now would break the legacy portal and the `/upload-csv` capability (a locked core capability). This is the correct, non-destructive sequence.

No **public/unauthenticated** legacy document path remains reachable: legacy document endpoints require `require_auth()` / `require_org_member()` and the V3 surface uses private storage + signed URLs (D32).

---

## 6. Onboarding Result (Phase 1)

Product Owner requested a real demo-credential acceptance. **Result: PASS, with one defect fixed.**

Verified against the live local stack (frontend `localhost:3000`, backend `localhost:8050`, Supabase `127.0.0.1:54425`):

- **Valid credential** → GoTrue returns a session for all 11 demo actors (owner/admin/member/viewer/consultant/consultant-member/operator/reviewer/qc/staff-admin/entity-staff).
- **Invalid credential** → `400 invalid_credentials` (fail closed).
- **Session refresh** → `grant_type=refresh_token` rotates a new access + refresh token.
- **Session persistence / logout** → GoTrue session lifecycle (client-side sign-out + refresh-token revocation) is standard Supabase behavior; refresh rotation verified.
- **Post-login routing** (server-authoritative, `resolvePostLoginPath`): owner→`/home` (resolve-org 200), operator→`/ops` (`/api/v3/ops/me` 200), consultant→`/consultant` (`/api/v3/consultants/me` 200).
- **Organisation context / role enforcement:** org-profile 200; foreign-org access 403; entity-staff cannot pass internal-staff gates (unit-tested).
- **Defect found and fixed:** the demo accounts in the local stack had been seeded with a password different from the documented one, so the documented credential failed. The password was reset (GoTrue Admin API) to the documented value for all 11 demo accounts and re-verified. **No credential is exposed in this report.**

---

## 7. Extraction Recovery (Phase 3)

Per the historical-extraction recovery audit, the capability was *disconnected, not deleted*:

- **Digital PDF text extraction** — engine (`pdf_engine.PDFExtractor.extract_and_parse`) already worked and remains wired.
- **Scanned-PDF OCR** — broken by `convert_from_path(io.BytesIO(...))` + a forced Windows tesseract path. **Both fixed** (§4.1).
- **Image (JPG/PNG) OCR** — `extract_and_parse_image` existed but was dead code; the only route that classified images called the PDF method. **Re-wired** (§4.1).
- **V3 production wiring gap (documented, not closed in this pass):** `POST /api/v3/uploads` stores + enqueues a manual-extraction item but does **not** run OCR. The audit's recommended adapter (OCR text → `engines/extraction.py` → `manual_extraction_items`) remains the required next step (~2–3 engineering days per the audit). The engine layer is ready; the HTTP wiring is the remaining gap. **No production claim of automated OCR is made.**

---

## 8. Synthetic Extraction Evaluation (Phase 4)

**NOT COMPLETED — dependency documented.** The canonical synthetic generator (`shomonrobie/carbon_tally_synthetic_documents_generator`) is an external repository; the 1,688-document corpus is not in this checkout. Additionally the local runtime lacks the **tesseract binary** (`which tesseract` → absent; poppler `pdftoppm` present), so live OCR evaluation cannot be executed here.

The deterministic unit tests added in §4.1 (mocked OCR layer) verify the *dispatch and API* of the recovered engines. **A representative corpus evaluation (digital PDF, scanned PDF, JPG, PNG, multi-page, edge cases) is a required follow-up once tesseract is provisioned and the corpus is available.** No extraction claim is made beyond what is unit-tested.

---

## 9. CSV / Excel Regression (Phase 5)

- No changes were made to the CSV/Excel mapping path.
- Full `tests/unit` suite passes (exit 0) including the CSV/Excel mapping tests.
- The legacy `/upload-csv` route and `utils/emissions.py` processors remain intact.
- **Note:** CSV/Excel currently converge at the standardized-activity layer, not at `manual_extraction_items`; the audit's convergence point (§15 of the extraction audit) is via the V3 manual-extraction pipeline. Not changed here (preserve working functionality).

---

## 10. Custom Emission Factors Regression (Phase 6)

- Customer-factor architecture (`customer_factors` + `repos.customer_factors`) is untouched.
- The calculation engine resolves custom factors explicitly when the mapped `factor_id` is not in `emission_factors` and verifies `status == 'active'` (`v3_processing_workflow.py`).
- Unit suite for customer factors (`test_v3_customer_factors.py`, `test_customer_factor_integration.py`) passes.
- **Live DB check:** the local stack has **no factor rows at all** (see §11), so custom-factor calculation could not be re-verified against a live org factor in this environment — covered by unit tests only.

---

## 11. DEFRA / Irish-SEAI Factor Verification (Phase 7)

**Blocking deployment finding:**

| Stack | `emission_factors` rows |
|---|---|
| New local (54426) | **0** |
| Old local (54326) | 1 |

- The audits describe a 7,029-row DEFRA-2025 artifact and a 20-row SEAI-2025 import. **Neither is present in the local databases, and no V3-format factor seed exists in this checkout** (only legacy-format backup rows in `backend/carbon_tally_backup_data.sql` under the old `defra_conversion_factors` columns — no `country/factor_source/factor_set/scope/unit`).
- The factor **matching/calculation engine** is code-verified and unit-tested (DEFRA GB and SEAI IE at engine level).
- The **data** is a deployment/data-load dependency: the authoritative DEFRA-DESNZ and SEAI/EPA factor loads must be imported into `emission_factors` (V3 columns) for the feature to function in any environment. **No factor data was fabricated or modified.**

---

## 11a. DATABASE ENVIRONMENT DISCREPANCY (Investigation Report)

**Trigger:** The finalization report stated `emission_factors` = 0 rows in "the local DB". The Product Owner verified **7,049 rows** directly against the actual CarbonTally database. This section documents the investigation (read-only; **no application code, database data, or migrations were modified**).

### 1. Which database instance the finalization tests were connected to

The finalization run used the **local (Docker) Supabase stack `supabase_*_carbon_ledger`**:

- Backend configuration source: `backend/.env` → `SUPABASE_URL=http://127.0.0.1:54425`, `DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/postgres`.
- Frontend configuration: `frontend/.env` / `.env.local` → `REACT_APP_SUPABASE_URL=http://127.0.0.1:54425`.
- All live tests and factor counts in §11 were performed against **127.0.0.1:54426/postgres** (new Docker stack) and, for comparison, **127.0.0.1:54326/postgres** (older native stack). Both are **local development instances only**.

### 2. Database URL / Supabase project reference in use

- The **running local app** used the local stacks above (no remote project involved).
- The repository also references the **hosted CarbonTally project** `pvwiojoyaqywtydzcpbg.supabase.co` (London) in `admin/.env`, `admin/.env.local` and the `frontend/src/supabaseClient.js` fallback, and the Supabase CLI is **linked** to that project (`supabase projects list` → CarbonTally, `pvwiojoyaqywtydzcpbg`, London). No credentials/keys are reproduced in this report. The Product Owner's direct verification was against the actual CarbonTally database (this linked project's database).

### 3. Was the local instance freshly initialized without factor data? — YES

Evidence that both local stacks were re-initialized from **migrations only** (data-loads such as the factor import and demo data are **not** part of migrations):

- The **new Docker stack** (`supabase_*_carbon_ledger`) was created **2026-08-23 16:47** — after the factor import (2026-08-15).
- The **old native stack**'s Postgres was (re)started **2026-08-26 17:14–17:15** against a fresh `/etc/postgresql` data directory — the standard `supabase start` behaviour that rebuilds from migrations and drops data-loads.
- **Direct before/after proof:** the repository contains a live probe result, `backend/_v3m12_probe3.txt` (2026-08-11), captured against the old-stack DEV DB:
  ```
  === DEV DB (postgres): 127.0.0.1:54326/postgres ===
  {"pe_table": null, "staff_entity_col": 0, "mrw_entity_col": 0, "ub_entity_col": 0,
   "factor_total": 7049, "factor_defra": 7029, "factor_seai": 20, "pe_policies": 0}
  ```
  Today the same instance returns **1 row** — `D331-TEST | TEST` (id `d3333333-…`), a migration/test fixture, not factor data. The 7,049 real rows are gone from the local instances only because those instances were re-created after the data-load.

### 4. Is there an existing approved factor seed/import mechanism? — YES

Two idempotent SQL seeds (generated by the repo's import tooling; `output/reports/import_summary.md` documents the 2026-08-15 run):

- **DEFRA-2025:** `output/sql/emission_factors.sql` — **7,029** `INSERT INTO public.emission_factors` statements (`factor_source='DEFRA-DESNZ'`, `factor_set='DEFRA-2025'`, `country='GB'`), each guarded by `WHERE NOT EXISTS` on the natural key (re-runnable, no duplicates).
- **SEAI-2025:** `output/seai_2025/sql/emission_factors_seai_2025.sql` — **20** INSERT statements (`factor_source='SEAI'`, `country='IE'`).
- Import tooling: `src/providers/defra`, `src/providers/seai` (with tests), Admin Dashboard DEFRA import UI (`admin/src/components/admin/ImportDefraModal.jsx`).
- Schema support: `supabase/migrations/20260807010000_add_emission_factors_import_batch.sql` references "Existing 7029 rows untouched".

### 5. Schema / factor-table structure comparison

The local stacks have the **same `emission_factors` schema** as the target of the seed SQL (verified via `\d emission_factors` on 127.0.0.1:54426):

`id, reporting_year, activity_type, co2e_multiplier, unit, scope, factor_source, factor_set, country, region_deprecated, import_batch_id, created_at, updated_at` — plus the natural-key unique index `emission_factors_year_activity_country_uniq` and the `country IN ('GB','IE')` CHECK constraint. The seed SQL targets exactly these columns. **Schema parity: confirmed** — only the data was absent locally.

### 6. Is 7,049 consistent with the DEFRA + SEAI baseline? — YES

| Set | Rows |
|---|---|
| DEFRA-2025 (`output/sql/emission_factors.sql`) | 7,029 |
| SEAI-2025 (`output/seai_2025/sql/emission_factors_seai_2025.sql`) | 20 |
| **Total** | **7,049** |

This matches (a) the Product Owner's direct count of 7,049, (b) the audit's "7,049 total in dev DB" figure, and (c) the 2026-08-11 probe (`factor_defra: 7029, factor_seai: 20`).

### 7. Does application code assume an empty/different baseline? — NO

- The factor search index is loaded **from the repository at runtime** (`api/dependencies.py` → `EmissionFactorsRepository.load_all_for_index()`); if the table is empty the index is simply empty. There is **no hard-coded fallback factor baseline** and **no startup seeding** in application code.
- Calculation/matching endpoints fail closed with "factor not found" / "no emission factor mapped" when the table lacks the required factor — they do not substitute invented values.
- The only `INSERT INTO public.emission_factors` in application code (`backend/data/emission_factors.py`) belongs to the import/orchestration path, not to normal operation.

### Conclusion

- **Environment tested:** two local Supabase development instances (Docker `carbon_ledger` at 5442x; native at 5432x), both re-initialized from migrations **after** the factor data-load.
- **Why they contained 0 (and 1) rows:** fresh `supabase start` rebuilds apply migrations only; the factor import (and demo/emissions data) is a **data-load, not a migration**, so it was not reapplied.
- **Actual CarbonTally database:** contains the full baseline — **7,049 rows (7,029 DEFRA-2025 + 20 SEAI-2025)** — verified by the Product Owner and consistent with repo artifacts.
- **Is this data loss?** **NO.** No evidence of loss in the actual database; the repo contains the complete approved, idempotent seed artifacts to reproduce the baseline.
- **What must be done for local/test environments to reproduce the correct factor baseline:** after a fresh `supabase start`, load the two approved seeds (documented in `output/reports/import_summary.md` and the seed file headers):
  1. `psql ... -d postgres -f output/sql/emission_factors.sql` (DEFRA-2025, 7,029 rows), then
  2. `psql ... -d postgres -f output/seai_2025/sql/emission_factors_seai_2025.sql` (SEAI-2025, 20 rows).
  Both are idempotent (natural-key guarded) so re-running is safe. The same two files are the approved import path for any environment.

---

## 12. Traceability / Evidence Verification (Phase 9)

- Row-level traceability chain (D33) is preserved and code-verified: `organization_files` → `manual_extraction_items.file_id` → `calculation_snapshots.source_item_id` → `emissions_logs.snapshot_id`.
- Evidence completeness classification (`domain/evidence.py`) remains honest (no fabricated pages).
- Unit tests `test_evidence_traceability.py`, `test_evidence_record.py` pass.
- **Known gap (documented, unchanged):** human extract/map edits are not recorded with before/after values (audit §16; decision register §7.2). This is a product decision (retain original + corrected + reviewer/time/reason) that should reuse the existing `audit_trail` machinery — not a new evidence system.

## 13. Processing Entity Security (Phase 10)

Verified/enforced server-side (not UI hiding):

- Scope-first authorization chain (`staff_profiles.entity_id`, `require_staff` + `require_entity_scope`).
- **No-download:** entity staff receive signed-URL views (V3 documents) and never raw storage credentials; legacy `get_public_url` usage on the private bucket is superseded by D32 signed URLs.
- **F1 closed:** entity read surfaces now require `entity.status == 'active'` for entity staff.
- **F2 closed:** legacy upload batch endpoints are org-scoped.
- Assignment model (`assigned_to` XOR `entity_id`, audited reassignment) preserved.
- Tests: `test_scope_aware_authorization.py`, `test_operations_auth.py`, `test_v3_entity_extraction.py`, `test_storage_security.py` all pass.
- **Residual (documented):** F6 (dual-scope provisioning guard) is a provisioning-time control not implemented here — it requires an internal-admin policy decision (the audit's recommendation) rather than a schema change; F5 (DB CHECK for the XOR invariant) is defense-in-depth.

---

## 14. Billing Verification (Phase 12)

- Billing architecture (D37) is untouched and code-verified: versioned `billing_plans`, `billing_commercial_config`, `billing_credit_ledger`, CREDIT/STANDARD modes, orders, storage metering, D37-0 write lockdown.
- **Mixed-currency issue — left unchanged, dependency documented:** `billing_plans` seeds Starter/Business v2 in **USD** ($49/$399) while Professional v1 remains **GBP** (£149); `assisted_pricing` is seeded USD while `storage` is seeded GBP. The D37 migration re-versioned starter and business to USD but did not publish a Professional v2 — the asymmetry appears to be an omission, but correcting it is a **commercial decision** (UK vs international pricing), which this program forbids guessing. A Product Owner decision is required: (a) adopt a single currency for the plan catalogue, or (b) confirm mixed-currency by design; and (c) confirm whether Professional should be re-versioned to USD.
- **Public pricing consistency:** the new website presents all plans in GBP (£49/£149/£399) and explicitly labels them *indicative / subject to final commercial terms* with **no online checkout** — truthful and consistent with a pre-launch state. This resolves the audit's C4/C5 public contradiction at the presentation layer.

---

## 15. Website Integration (Phase 14) — see §4.3

Independent review result: the candidate is **clean and approved for integration** against the decision register §10 and the website refactor/QA reports:

- Public claims verified truthful; no "under construction", no internal development status, no roadmap/phase messaging.
- Extraction wording is careful ("data is read … by you, by CarbonTally specialists, or with AI-assisted help — and reviewed by people"); it does not claim automated OCR that is not wired.
- Pricing is indicative and contact-gated; the fake waitlist was replaced by a Contact page.
- Legal links fixed (Privacy reachable at `/privacy`; new `/pricing`).
- Team/legal claims: About page no longer fabricates team members (candidate reviewed).
- Integrated into canonical frontend; build passes; authenticated routes preserved.
- **Remaining dependency:** final legal/trust wording (privacy, terms, cookie policy) should receive Product Owner/counsel sign-off before public launch (decision register §17).

---

## 16. Demo Verification (Phase 15)

- **Demo identities:** all 11 demo accounts verified (login + role resolution), after password reset to the documented value.
- **Demo data present (new stack):** 1 demo org (`CarbonTally Demo Ltd`), 4 org members, 4 org documents.
- **Known demo figure 10,732.4 kg CO₂e:** reproduced as a calculation (4,258.9 L red diesel × 2.52 kg CO₂e/L = 10,732.428 kg CO₂e) and is defined consistently in the new website demo data. **It is not persisted as an emission in the local DB** (`emissions_logs` = 0 rows for the demo org).
- **End-to-end pipeline:** a live upload→extract→map→validate→calculate→evidence run could **not** be completed because the local DB has no `emission_factors` rows (a factor selection is mandatory for map/calculate). This is the same deployment dependency as §11. The full unit+integration test suite covers the pipeline logic with in-memory fakes.
- **Recommendation:** load the approved DEFRA factor set, then run the live end-to-end demo (document → OCR/entry → factor → calculation → snapshot → evidence → review) via the V3 API.

---

## 17. Tests

| Suite | Result |
|---|---|
| Backend `tests/unit` (full) — before changes | exit 0 |
| Backend `tests/unit` (full) — after changes | exit 0 |
| New `tests/unit/engines/test_pdf_engine.py` | pass (7 tests) |
| New `tests/unit/api/test_legacy_upload_idor.py` | pass (6 tests) |
| Updated `test_reporting.py` / `test_v3_operations.py` / `test_v3_issues.py` (F1 + existing) | pass |
| Security suites (`test_scope_aware_authorization`, `test_operations_auth`, `test_v3_entity_extraction`, `test_storage_security`) | pass |
| Frontend `npm run build` | exit 0 (Compiled with warnings) |
| Live stack: backend `/health` | healthy, supabase_connected=true, 595 routes |
| Live stack: owner login + resolve-org + org-profile + documents | 200 |
| Live stack: legacy batch stats with foreign org | **403** (F2 live) |

Note on the audit's "1051 passed / 5 failed": the 5 failures were the F3 bug (500-vs-403), which is now fixed; the full suite passes in this environment.

---

## 18. Remaining Issues

**Blockers / deployment dependencies:**
1. **No factor data in any local DB** — the DEFRA/SEAI factor load must be imported into `emission_factors` (V3 columns). Blocks live end-to-end calculation demo and factor-selection UX.
2. **tesseract runtime absent** locally — required for live OCR evaluation (poppler present). Provision `tesseract-ocr` in the deployment/container and set `TESSERACT_CMD` if not on PATH.
3. **V3 OCR wiring** — OCR text is not yet fed from `/api/v3/uploads` into `manual_extraction_items` (adapter per extraction audit). Not done here because it is a multi-day, cross-layer change (upload pipeline, workspace surface, persistence) that deserves its own change with the OCR runtime available.

**Requires Product Owner decision:**
4. Billing plan currency mix (§14) — single currency vs confirmed mixed; Professional v2 omission.
5. Extract/map edit audit trail (original+corrected+reason) — decision register §7.2.
6. F5 DB CHECK for the entity/batch XOR invariant and F6 dual-scope provisioning guard (both defense-in-depth, P3).
7. Legacy upload surface decommissioning sequence (§5) — requires removing the legacy `PDFIngestionPortal` from `App.js` first.
8. Final legal/trust website copy sign-off (§15).

---

## 19. Legal / Policy Dependencies

From decision register §17 (no legal conclusions implemented):
- UK controller/processor/subprocessor structure, IDTA/Addendum, EU SCC module, transfer assessment, Bangladesh legal position, special-category policy, customer DPA wording, PE agreement, **retention periods** (Phase 13 — no arbitrary retention numbers invented; `data_retention_days` default of 365 remains a config value, not a policy), sector requirements, external-AI-provider terms, final public privacy/security claims.
- The "no-download" control is implemented as a **technical/security control** and is not described as eliminating international-transfer obligations (decision register §3.3 honoured).

---

## 20. Deployment Readiness

- **Code:** backend unit suite green; frontend production build green; live stack healthy.
- **Security:** the audit's P2 findings F1/F2 are fixed; P3 F3/F4 fixed; F5/F6 documented. No known cross-tenant data exposure on the V3 surface.
- **NOT launch-ready for public commercial launch** until: factor data is loaded (§11), OCR runtime + V3 OCR wiring are delivered and evaluated (§7/§8), billing currency decision is made (§14), legal copy is approved (§19), and the legacy surface decommissioning is completed (§5). Consistent with the independent audit verdict (CONDITIONAL — ready for a controlled, provisioned/partner launch).

---

---

## 21. OCR Runtime + V3 Document Extraction Pipeline (dedicated task update)

**Date:** 26 August 2026. Full details: `docs/audit/cline/CARBONTALLY_V3_OCR_SYNTHETIC_TEST_REPORT.md`.

- **OCR runtime status — PROVISIONED (reproducible):** Tesseract 5.5.0 + Leptonica 1.86.0
  provisioned locally without root via `tools/provision_tesseract_local.sh` (extracts Ubuntu
  `.deb`s to a user prefix; emits `tesseract-env.sh`). Container/Render provisioning documented
  in the script (`apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract5 poppler-utils`).
- **V3 OCR wiring status — IMPLEMENTED + LIVE-VERIFIED:**
  - `POST /api/v3/uploads` runs deterministic text/OCR inline (best-effort; never fails the
    upload) and persists the summary on `organization_files.metadata.ocr` (JSONB — no schema change).
  - New `POST /api/v3/uploads/{file_id}/ocr` re-run endpoint (org-scoped).
  - Item-workspace responses (`/api/v3/ops/items/{id}/workspace`,
    `/api/v3/processing/items/{id}/workspace`) now surface `source.ocr_text` for human review.
  - The existing engine (`pdf_engine.PDFExtractor`) was preserved; an additive
    `extract_image_text` primitive was added and reused by `extract_and_parse_image`.
- **Synthetic test status — COMPLETE:** text PDF, scanned PDF, JPG, PNG extracted 6/6 target
  fields (supplier, invoice no., date, 12500 kWh, amounts, activity). Failure handling verified
  (`unsupported`, `no_text`, `404`, `403`, engine-failure → `error` without raising).
- **End-to-end pipeline verified live:** synthetic document → upload → inline OCR (`pdf_text`) →
  manual-extraction item → human-equivalent extract → map to DEFRA factor (0.177 kg CO₂e/kWh,
  GB 2025) → validate → **calculate = 2,212.5 kg CO₂e** (12,500 kWh × 0.177) → immutable snapshot
  (content-hash) → emissions log → **evidence COMPLETE** (document + line + page + factor + calc).
  Full traceability chain persisted (`organization_files → manual_extraction_items →
  calculation_snapshots → emissions_logs`).
- **Factor baseline:** the local dev DB was restored to the approved **7,049-row** baseline using
  only the approved seed files (`output/sql/emission_factors.sql`, `output/seai_2025/sql/emission_factors_seai_2025.sql`).
  No factor values were invented or modified.
- **Remaining OCR limitations:** OCR is a human-review reference (not auto-accepted); deterministic
  field pre-fill is the natural next increment; broader synthetic corpus coverage remains dependent
  on the external generator corpus; production tesseract provisioning must be applied to the
  deployment image.


---

## 22. OCR Gap Closure — Field Pre-fill, Corpus Evaluation, Deployment (26 Aug 2026)

Continuation of the OCR task. Full detail: `docs/audit/cline/CARBONTALLY_V3_OCR_SYNTHETIC_TEST_REPORT.md` (UPDATE 2).

- **Gap 1 — deterministic field pre-fill: COMPLETED + VERIFIED.** New `services/extraction_suggestions.py::suggest(text)` reuses the existing `DocumentExtractionEngine` (additive, side-effect-free `suggest_fields`). Suggestions map to the existing V3 `extracted_data` subset and are persisted in `organization_files.metadata.ocr.suggested_data` + surfaced as `source.ocr_suggestions` in both workspaces. **Human-reviewed contract preserved:** items stay `pending` with empty `extracted_data`; nothing is auto-approved; a later OCR run never overwrites human-confirmed `extracted_data` (regression-tested). Missing fields are reported in `unresolved` (never fabricated) — verified live (supplier correctly left unresolved when the document has no "Supplier:" label).
- **Gap 2 — broader synthetic corpus: COMPLETED.** The external generator repo (`HEAD 8ade2bf`, 1,909 PDFs + 1,896 ground-truth JSONs) was available; a deterministic 54-document evaluation ran with **0 extraction failures**. Field-level: supplier 97.5%, invoice_number 97.5%, invoice_date 32.5%, quantity+unit 47.5%; currency/document_type "misses" are formatting (ISO code / semantic label not printed). Full 1,895-pair corpus remains for a larger run.
- **Gap 3 — production Tesseract provisioning: INVESTIGATED — blocked on authorized deployment access (precise handoff delivered).** The backend deployment was verified as Render **Native Python runtime**, dashboard-configured (start `uvicorn main:app --host 0.0.0.0 --port $PORT` from `backend/`, `pip install -r backend/requirements.txt`, Python 3.11 via `runtime.txt`). No authorized Render access exists in this environment (no CLI, no API key, no blueprint; production endpoint unreachable from here), and Render's docs do not bundle tesseract/poppler in native runtimes (Docker is their documented path for such tools). The exact dashboard settings / reference Dockerfile, unchanged env vars, and verification commands are in `docs/audit/cline/CARBONTALLY_V3_RENDER_OCR_PRODUCTION_PROVISIONING_HANDOFF.md`.
- **Tests:** new `tests/unit/engines/test_extraction_suggestions.py` (7) + 4 new wiring tests in `tests/unit/api/test_v3_ocr_wiring.py` (suggestions surfaced; no auto-approval; human data never overwritten; suggestions persisted). Full backend unit suite re-run after the changes.


## Git Status / Commits

- **No commits were created.** The working tree contains ~760 pre-existing unrelated changes (skills reorganisation, line-ending churn, untracked docs) that must not be swept into an implementation commit, and several files I edited also carry that pre-existing churn, so a clean logical commit requires a controlled staged step. Commits are left to the operator per the GIT RULE ("do not push until all work is complete and verified").
- **Exact files changed (this program):**
  - Backend: `auth.py`, `pdf_engine.py`, `routes/upload.py`, `api/issues.py`, `api/v3_operations.py`, `api/v3_reporting.py`, and 14 legacy route files swept for `current_user.id→user_id` (`routes/admin/{beta,bulk,dashboard,document-types,settings,workload}.py`, `routes/communication.py`, `routes/customer_dashboard.py`, `routes/customer_documents.py`, `routes/customer_verifications.py`, `routes/document_activity.py`, `routes/drafts_enhanced.py`, `routes/emissions.py`, `routes/organizations/{exports,files,metadata}.py`, `routes/reports.py`).
  - Tests: `tests/unit/engines/test_pdf_engine.py` (new), `tests/unit/api/test_legacy_upload_idor.py` (new), `tests/unit/api/test_reporting.py`, `test_v3_operations.py`, `test_v3_issues.py`.
  - Frontend: `src/App.js`, `src/public/**` (new), `src/{LandingPage,PricingPage,AboutUs,Glossary,CarbonReductionPlan,CookieBanner,CookiePolicy,PrivacyPolicy,TermsPage}.jsx`, `src/components/{AppHeader,AppFooter}.jsx`, `src/App.css`, `public/{index.html,favicon.ico,logo192.png,logo512.png,manifest.json,robots.txt,sitemap.xml}`.
  - Untracked source material: `website_candidate/**` (handoff manifest + candidate copy; not part of the app build).
- **No secrets committed** (the password used for demo-account reset is the pre-existing documented local-only credential, not reproduced here).

