# CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY-20260924

**Type:** READ-ONLY FORENSIC / ARCHITECTURE / PRODUCT-RECOMMENDATION STUDY. **Authorizes nothing.**
**Date of execution:** 2026-09-24 (session local, UTC+06:00) · **Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Remote:** `github`
**Scope:** establish one factual baseline for taking CarbonTally from its current state to a genuinely investor-demonstrable platform. No code, test, migration, configuration, Demo Lab data, database or deployment state was modified.

**Evidence labels:** `CODE-TRACED` · `DATABASE-OBSERVED` · `BROWSER-VERIFIED` · `GIT-VERIFIED` · `DOCUMENT-SOURCED` · `INFERENCE` · `UNKNOWN`.

---

## 1. Executive conclusion

**The engine is real; the demonstration surface is not yet assembled — and two of its load-bearing layers are absent from every database a presenter can reach.**

1. **No local database carries the Insight schema.** All six Insight migrations (`20261001000000` I1 → `20261007000000` P3) are **unapplied** everywhere locally: `carbontally_insight_conversations / interactions / messages / tool_calls`, `insight_rate_limit_buckets`, `insight_concurrency_leases` do not exist. **INS-01, P2 and P3 therefore cannot execute in any local environment**; their verification to date is unit/contract-level (P2's closure explicitly recorded "no live-DB execution"). `DATABASE-OBSERVED` + `CODE-TRACED` + `DOCUMENT-SOURCED`.
2. **The evidence-line layer has never been populated anywhere.** `evidence_line_items = 0` in every local database; in the historical dataset the table **does not exist**. This is architectural, not a bug: online processing only *looks up* already-materialised lines (`v3_operations.py:487`, `automatic_processing.py:1822` — "a LOOKUP, never an inference"); materialisation lives in `EvidenceLineItemsRepository`; the only invoker in the repository is the **offline, dry-run-by-default CLI** `backend/tools/backfill_evidence_line_items.py`, whose docstring states "*Execution against any environment is separately authorised*". The Source Evidence Viewer — whose code passed independent verification (`PASS WITH NON-BLOCKING OBSERVATIONS`, 2026-09-22) — currently has **nothing to display**. `CODE-TRACED` + `DATABASE-OBSERVED`.
3. **There is no canonical demo environment.** The historical investor dataset exists as *data* in the local stack's `postgres` database (975 organisations, 1,205 auth users, 263 documents, 100 snapshots) but on an **older schema revision** (116 tables; no `evidence_line_items`, no `source_line_item_id`, no disclosure tables) and **without its tooling**: `tools/seed_investor_demo/` and `DEMO_IDENTITIES.md` are absent from this checkout. The current `tools/demo_lab/` Demo Lab is the opposite: current-ish schema (136 tables) but thin data (4 orgs, 14 documents, **1** calculation, 0 master data, 0 issues, 0 messaging, 0 evidence). `DATABASE-OBSERVED` + `DOCUMENT-SOURCED`.
4. **The configured environment is local-only and mostly down.** `backend/.env` → `ENVIRONMENT=local`, DB `127.0.0.1:54426/ct_local_93d5cdd`, `SUPABASE_URL=http://127.0.0.1:19999`, API `http://localhost:8060`. Only 54426 (Postgres) and 54430 (Demo Lab gateway) listen: the configured Supabase-compatible API (19999) and both backends (8060 release / 8070 lab) are **not running**. `CODE-TRACED` + `DATABASE-OBSERVED`.
5. **Live Supabase is not accessible and is not inspectable read-only from this configuration** (§7). No hosted Supabase URL/key exists in the configured environment; no Render/Vercel/Supabase credential or project link exists in the repository; the only live-path record concludes `BLOCKED — PRODUCTION STATE UNKNOWN` (2026-09-21). Per the study's stop condition, live inspection was **not attempted**. `CODE-TRACED` + `DOCUMENT-SOURCED`.
6. **Most high-severity historical defects are fixed in current code**, confirmed by reading code and, where data exists, the data: ISC-1 (`source_item_id` written at three calculate sites; 99/100 historical snapshots and the one Demo Lab snapshot carry it), ISC-2 (`resolve_open_for_item/_batch`), ISC-3 (activity/factor joins), ISC-6 (`/api/v3/notifications`), ISC-8 (409 on duplicate factor), SEC-1 (Viewer upload denied), PRC-1 (aliased review-queue SQL), MSG-1 (no `ON CONFLICT` in the conversation insert), MD-2 (`vehicles` now present in all four databases), CAL-3 (`emission_factors`-backed reference route). **Two material exceptions persist:** **ISC-9** (spend-based documents still unmappable — **0** £/GBP or spend-activity factors in both databases, no browse fallback) and **ISC-10** (system-admin/billing role model — data/seed + PO decision). `CODE-TRACED` + `DATABASE-OBSERVED` + `DOCUMENT-SOURCED`.
7. **The core deterministic story is demonstrable and browser-verified for one record** (DR-003…DR-006): real login, real document, real extraction, real factor, `12181.4 kWh (Net CV) × 0.2027 = 2469.169780 kg CO₂e`, real report + downloadable artefact, real exports, honest machine-readable block reasons. `DOCUMENT-SOURCED`.
8. **Nothing in the current state authorizes a credible Insight or evidence demonstration**, because both depend on layers that are absent (Insight schema) or empty (evidence lines) in every reachable environment. `INFERENCE` from (1) and (2).

**Category summary (no category silently upgraded):**

| Domain | Category |
| --- | --- |
| Calculation engine, snapshots, validation, reporting, exports | IMPLEMENTED + VERIFIED (browser + data) |
| Automatic pipeline (upload→queue→extract→map→validate→calculate→review) | IMPLEMENTED + VERIFIED for the one record that completed; PARTIAL as a general capability (2/11 corpus families map; 13/14 documents block) |
| Evidence-line layer / Source Evidence Viewer data | **DATA/SEEDING + PROCESS GAP** (code verified; data empty; online writers absent by design; backfill separately authorized) |
| Insight (INS-01, P2, P3) | IMPLEMENTED (P2 PO-closed; P3 independently verified, not closed) — **non-functional in every local environment** (missing schema = environment/schema gap) |
| Multi-tenant isolation, role boundaries, authorization | IMPLEMENTED + VERIFIED (unit/API suites, demo probes, DR-005 browser) |
| Master data, issues, messaging in the demo | **DATA/SEEDING GAP** (0 rows in the Demo Lab) |
| Live/production environment | **UNKNOWN / NOT ACCESSIBLE** (environment-deployment gap) |
| Demo script, runbook, reset rehearsal, canonical dataset | **MISSING** (documentation + governance gap) |
| Scope 2 market-based, Scope 3 taxonomy, Scope 1 decomposition, variance, supplier persistence, knowledge, reduction | **NOT YET AUTHORIZED / PRODUCT-POLICY DECISION REQUIRED** |
| Billing/PSP, L7 lifecycle, L8 SLO governance | **NOT YET AUTHORIZED** |

---

## 2. Repository / Git baseline

| Item | Value | Evidence |
| --- | --- | --- |
| Repository | `/home/shomonrobie/ct_93d5cdd` | `GIT-VERIFIED` |
| Branch | `p8-release-reconciled` (unchanged throughout) | `GIT-VERIFIED` |
| HEAD | `53367cf73c24ef0b22b682438c8bdd037c7eeb4f` — `docs(p12): read-only investor-demo readiness preflight (planning artifact only)` | `GIT-VERIFIED` |
| `github/p8-release-reconciled` | identical SHA | `GIT-VERIFIED` |
| Alignment | `git rev-list --left-right --count HEAD...github/p8-release-reconciled` → `0 0` | `GIT-VERIFIED` |
| Working tree | ` M .gitignore` (pre-existing PO modification) + untracked: `.costrict/`, `8`, `=`, `costrict-p3-ov-01-independent-re-verification.txt`, 8 untracked `docs/` PO/ChatGPT reference documents + this study's report | `GIT-VERIFIED` |
| Remotes | `github` = `https://github.com/shomonrobie/CarbonTally.git` (authoritative); `origin` = `/tmp/ct_step2` (not contacted) | `GIT-VERIFIED` |
| Recent history | `53367cf` (P12 preflight) ← `2be9033` (P3-IV-01 re-verification, PASS WITH NON-BLOCKING OBSERVATIONS) ← `b39caad` ← `8554b78` (P3-IV-01 fix) ← `0c34908` (P3 independent verification) | `GIT-VERIFIED` |
| Release migration count | **81** files in `supabase/migrations/` | `GIT-VERIFIED` |

No Git state was modified by this study (no branch switch, no reset/stash/clean, no history rewrite).

---

## 3. Documents and evidence reviewed

### 3.1 Reviewed in this study (all present in the repository)

| Group | Artefacts (with size) | What was taken from them |
| --- | --- | --- |
| Investor/demo data | `docs/audit/cline/CARBONTALLY_V3_INVESTOR_DEMO_DATA_REPORT.md` (203) | historical dataset spec (50 direct orgs, 50 consultants, 916 clients, 219 documents, 156 facilities, 310 assets, 156 suppliers, 245 customer factors, 48 issues, 37 conversations), seeder command, local-only safety gate, vehicles blocker |
| Investor-scale audit | `docs/audit/openhands/previous-session/CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md` (298) | origin/definition of ISC-1…ISC-16, PRC-1, CAL-3, MSG-1, SEC-1 re-confirmations |
| Persona/UI audits | `docs/audit/openhands/CARBONTALLY_V3_UI_VISUAL_ACCEPTANCE_AUDIT.md` (614), `…FULL_PERSONA_ACCEPTANCE_AUDIT.md` (615), `…PERSONA_TEST_MATRIX.md`, `…POST_RESTORATION_ACCEPTANCE_AUDIT.md` (1130) | finding registers, reconfirmation table, persona matrix, post-restoration statuses |
| Security audit | `docs/audit/openhands/CARBONTALLY_V3_SECURITY_ACCEPTANCE_FINDINGS.md` (98) | SEC-1 (Viewer upload allowed) and the negative-test table |
| Phase-1 restoration | `docs/audit/cline/CARBONTALLY_V3_PHASE_1_CORE_WORKFLOW_RESTORATION_REPORT.md` (190) | which historical defects were fixed, in which files |
| Demo verification | `docs/demo-investor/DR-001…DR-007` (146–289 each) | browser-verified journeys, CORS gap, report/artefact/export evidence, defect triage |
| Demo Lab | `tools/demo_lab/{README.md,manifest.json,t3_manifest.json,lab.py,t3_scenarios.py,verify.py,run_demo_lab.sh,reset_demo_lab.sh,…}`; `docs/architecture/CARBONTALLY_DEMO_T3_IMPLEMENTATION_20260920.md` (260), `…T3_REM_001_IMPLEMENTATION_20260920.md` (157), `…T3_REMEDIATION_20260920.md` (112); `docs/verification/OHD_TASK_079_DEMO_T3_INDEPENDENT_VERIFICATION_20260920.md` (562) | demo topology, T3 scenario contract, generators/reset, OHD-079 FAIL and REM-001 blocked status |
| Phase 8 / Insight | `docs/verification/OHD-P8-I1…I3*` (31–43 KB each), `docs/verification/phase8/CT-P8-SOURCE-EVIDENCE-VIEWER-OHD-VERIFICATION-20260922.md` (26 KB), `docs/verification/CT-P8-I2-PRODUCTION-DEPLOYMENT-STATE-20260921.md` (134), `docs/verification/QA-AI-001-…` (47 KB) | I1/I2/I3 verification and re-verification, viewer verdict `PASS WITH NON-BLOCKING OBSERVATIONS`, production state `BLOCKED`, NL-verify verdict `NOT IMPLEMENTED` (pre-INS-01) |
| Insight architecture/governance | `CarbonTally_Insight_Architecture_Reference_2026-09-22(-v2).md` (741), `CarbonTally_Insight_Question_Library_2026-09-22.md` (971), `CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md` (1245), `CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md`, `CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md` (534), `CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md` (572) | family model, evidence depth E0–E4, NL boundary, 19-family statuses, package sequence, D-01…D-29 register, demo gate proposal |
| P1/P2/P3 records | `CT-PO-INSIGHT-CAPABILITY-COVERAGE-MATRIX-IMPLEMENTATION-20260922.md` (216), `CarbonTally_PO_P2_Temporal_Comparison_Closure_2026-09-23.md` (183), `CT-P8-INSIGHT-DATA-QUALITY-AUDIT-REPRODUCIBILITY-IMPLEMENTATION-20260923.md` (291), `CT-P8-INSIGHT-P3-INDEPENDENT-VERIFICATION-20260923.md` (740), `CT-P8-INSIGHT-P3-IV01-REMEDIATION-20260923.md` (391), `CT-P8-INSIGHT-P3-IV01-REVERIFICATION-20260923.md` (549) | P2 closed; P3 verified-not-closed; P3-IV-01 remediated/re-verified; open P3-IV items |
| P12 preflight | `docs/architecture/CT-PO-P12-INVESTOR-DEMO-READINESS-PREFLIGHT-20260923.md` (698) | prior read-only demo readiness findings (this study supersedes its narrower scope) |
| Governance | `AGENTS.md` (§54/§55 investor-dataset claims; §55.1 F-046-1), `docs/operations/*`, `docs/legal/*` | constitution claims that diverge from the checkout (§15 below) |

### 3.2 Explicit limitation on conversation evidence

* **No live ChatGPT conversation was accessed, read or relied upon.** The three `docs/ChatGPT/*.md` files in the working tree are **untracked repository artefacts** (233, 413 and 314 lines: an incremental PO-history checkpoint, an Insight-strategy-v2 note and a resume-point note). Their headers were read; their bodies were **not** relied upon as evidence for any conclusion in this study. `DOCUMENT-SOURCED` (headers only).
* The untracked `docs/architecture/CarbonTally_*2026-09-22*.md` reference documents **were** used (they are the PO Insight reference set present in the checkout).
* Anything a referenced conversation may contain beyond these files is **UNKNOWN** and is not reconstructed here.

---

## 4. Historical investor-demo reconciliation

### 4.1 The seven systems and how they actually relate

| # | System | Where it lives now | Status | Evidence |
| --- | --- | --- | --- | --- |
| 1 | `tools/demo_lab/` (Demo Lab, DEMO-T1/T2-C/T3) | **In the checkout** (15 files, ~4.3k lines) | **CURRENT** (the only current demo tooling) | `CODE-TRACED` |
| 2 | `tools/seed_investor_demo/` | **NOT in the checkout** — no directory; `AGENTS.md:1494` and `.gitignore:49` still reference `tools/seed_investor_demo/DEMO_IDENTITIES.md` | **RETIRED/MISSING TOOLING**; its *dataset* survives (see #6) | `GIT-VERIFIED` (absent) + `CODE-TRACED` (references) |
| 3 | External synthetic-document generator (`carbon_tally_synthetic_documents_generator`) | Offline, external; pinned commit **`8ade2bf778d518d59924905849ab114ab2d082a0`** recorded in `t3_scenarios.py:50` and `t3_manifest.json` | **CURRENT (pin matches exactly)**; the local checkout `/tmp/extgen` no longer exists | `CODE-TRACED` |
| 4 | T3 corpus (`t3-uk-curated-v1`, 11 scenarios) | Corpus copies live **outside** the repo in `$HOME/ct_local_env/demo_lab/corpus/t3-uk-curated-v1` (49 files incl. `corpus_provenance.json`); contract in `t3_manifest.json` | **CURRENT but only 2/11 scenarios map to a factor** | `DATABASE-OBSERVED` + `CODE-TRACED` |
| 5 | Demo Lab manifest (identities) | `tools/demo_lab/manifest.json` — 4 orgs, 1 PE, 1 consultant firm, **13 actors**, no credentials | **CURRENT** (contradicts `AGENTS.md` §54's 1,185-identity claim) | `CODE-TRACED` |
| 6 | Historical investor-scale dataset | **Data present** in the local stack's `postgres` database: 975 organisations, 1,205 `auth.users`, 1,125 members, 917 consultant_clients, 263 documents, 100 snapshots, 17 report versions | **LEGACY / SUPERSEDED SCHEMA, RICH DATA** (116 tables; no `evidence_line_items`, no `source_line_item_id`, no disclosure tables) | `DATABASE-OBSERVED` |
| 7 | Current release database(s) | `carbontally_demo_local` (136 tables), `ct_local_93d5cdd` (135, configured), `carbontally_qa_phase8` (133) | **CURRENT SCHEMA minus the six Insight migrations** | `DATABASE-OBSERVED` |

### 4.2 Lineage

```text
Historical investor-demo system  (tools/seed_investor_demo — TOOLING ABSENT from this checkout)
        │  seeded via `python -m tools.seed_investor_demo` against the local stack
        │  (documented target: supabase=127.0.0.1:54425, api=127.0.0.1:8050)
        ▼
Historical dataset as DATA      (local stack DB `postgres`: 975 orgs / 263 docs / 100 snapshots)
        │  ← OLD schema revision (116 tables; no evidence_line_items, no source_line_item_id)
        │  ← NOT regenerable here (seeder + manifest missing; dataset drifted from its own report)
        ▼
Current demo tooling            (tools/demo_lab — DEMO-T1 identities → T2-C factors → T3 corpus/scenarios)
        │  ← provisioned into `carbontally_demo_local` (136 tables; Insight migrations ABSENT)
        ▼
Current local database(s)       (carbontally_demo_local=23 MB thin · ct_local_93d5cdd=configured, near-empty
        │                        · carbontally_qa_phase8=empty · plus ~55 older ct_* test clones)
        ▼
Current release                 (HEAD 53367cf · 81 migrations · Insight/P2/P3 implemented in code)
        │
        ▼
Live Supabase                   **UNKNOWN — no configured live credentials; prior record: BLOCKED**
```

### 4.3 Reconciliation verdicts (explicit, not silent)

| Question | Verdict | Evidence |
| --- | --- | --- |
| Are `tools/demo_lab` and `tools/seed_investor_demo` duplicates? | **No — different generations with different intents.** The historical system seeded a broad, static, investor-scale dataset for persona/UAT acceptance; the Demo Lab provisions an identity + pipeline lab with a deterministic curated corpus. Only the Demo Lab's tooling exists in this checkout. | `CODE-TRACED` + `DATABASE-OBSERVED` |
| Is the historical dataset "current"? | **Data: yes (present, non-trivial). Tooling: no. Schema: no.** It is a legacy-schema dataset that cannot be regenerated from this checkout. | `DATABASE-OBSERVED` |
| Is the T3 corpus complementary or superseding? | **Complementary in intent; currently the only pipeline corpus** — 11 deterministic scenarios, of which 2 map to a factor. | `CODE-TRACED` |
| Does the external generator remain outside the runtime? | **Yes** — no import/execution; only generated documents (plus truth sidecars as a verification oracle) are copied; the pin matches exactly. | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| Is the `AGENTS.md` §54 "investor demo dataset / DEMO_IDENTITIES.md" statement accurate? | **No.** Neither the file nor the directory exists; the dataset exists only as data in `postgres`; the current identity manifest is 13 actors. | `GIT-VERIFIED` + `DATABASE-OBSERVED` |
| Is the historical dataset consistent with its own report? | **No — it has drifted.** Report: 219 documents / 156 facilities / 37 conversations / 1,323 users. Database now: 263 documents / 157 facilities / 36 conversations / 1,205 auth users, with items across 11 statuses. The report is a point-in-time run, not the current contents. | `DOCUMENT-SOURCED` vs `DATABASE-OBSERVED` |
| Which database does the *configured application* use? | **Neither of the above**: `ct_local_93d5cdd` (25 orgs, **0** documents, 0 snapshots, 0 factors, 5 customer factors). | `DATABASE-OBSERVED` |
| Are the ~55 other local `ct_*` databases relevant? | They are **disposable verification clones** (14–25 MB, dated 2026-09-13…09-21). Not demo environments; none carries the Insight schema. | `DATABASE-OBSERVED` |

**Undocumented/ambiguous:** the provenance of `ct_local_93d5cdd` (25 organisations, no data) is **UNKNOWN**; the cause of the historical dataset's drift from its report is **UNKNOWN**; whether any live environment holds the historical dataset is **UNKNOWN** (§7).

---

## 5. Current Demo Lab architecture

### 5.1 Topology (as documented and as found)

| Element | Documented | As found | Evidence |
| --- | --- | --- | --- |
| Lab database | `carbontally_demo_local` inside the developer's local Supabase cluster | exists (23 MB), reachable at `127.0.0.1:54426` | `DATABASE-OBSERVED` |
| Lab gateway | nginx at `127.0.0.1:54430` exposing `/auth/v1` + `/rest/v1` (+`/storage/v1`) | **listening**; containers `carbontally_demo_lab_gateway`, `…_storage`, `…_postgrest` up 3 days | `DATABASE-OBSERVED` |
| Release backend | `127.0.0.1:8070` (lab env file) | **NOT running** (port not listening) | `DATABASE-OBSERVED` |
| Configured release backend | `http://localhost:8060` (`backend/.env`) | **NOT running** | `DATABASE-OBSERVED` |
| Configured Supabase-compatible API | `http://127.0.0.1:19999` | **NOT running** | `DATABASE-OBSERVED` |
| Lab state dir | `$HOME/ct_local_env/demo_lab` | exists: `credentials.local.json` (0600), `backend.env`, `backend.log`, `corpus/t3-uk-curated-v1/` (49 files), `evidence/` (T2-C + T3 JSON evidence) | `DATABASE-OBSERVED` |
| Identity model | 13 actors across 4 orgs, 1 PE, 1 consultant firm; e-mail domain `@demo-lab.carbontally.local` | matches `manifest.json`; 8 `organization_members` rows | `CODE-TRACED` |
| Factor substrate | DEMO-T2-C: DEFRA-2025 + SEAI-2025, serial, idempotent, SHA-256-verified | **7,049** `emission_factors` present | `DATABASE-OBSERVED` |
| Reset | `reset_demo_lab.sh` (lab DB + containers + lab auth users; `--purge-state`) | code-traced; **not executed** (read-only study) | `CODE-TRACED` |

### 5.2 What the Demo Lab actually contains (read-only counts, 2026-09-24)

| Object | Rows | Note |
| --- | --- | --- |
| `organizations` | 4 | Demo Lab Organisation A/B, Client A/B |
| `organization_members` | 8 | identities per manifest (13 actors incl. platform/PE/consultant identities outside orgs) |
| `organization_files` | 14 | 12 × `t3imp_*` corpus PDFs + `scope2_water_plus_commercial_invoice.pdf` + `ohd079-invalid-probe.txt` (all status `uploaded`) |
| `document_processing_queue` | 14 | **13 `manual_review`**, 1 `customer_review` |
| `manual_extraction_items` | 14 | same items |
| `manual_extraction_batches` | 4 | uploads batches |
| `calculation_snapshots` | **1** | the natural-gas record (below) |
| `emissions_logs` | **1** | linked to that snapshot |
| `evidence_line_items` | **0** | ← the evidence gap |
| `disclosure_value_evidence` | **0** | ← the disclosure-evidence gap |
| `report_versions` | 2 | both `DRAFT` |
| `emission_factors` | 7,049 | DEFRA/SEAI |
| `customer_factors` | 0 | — |
| `facilities` / `assets` / `suppliers` | **0 / 0 / 0** | master data absent |
| `issues` | **0** | —
| `consultant_clients` | 2 | Client A/B engagements |
| `conversations` / `messages` | **0 / 0** | messaging absent |
| `audit_trail` | 113 | append-only log present |
| Insight tables | **absent** | 0 tables matching `%insight%` |

**Demonstrable today in the Demo Lab:** 13 personas (auth), the customer shell, document upload, one complete deterministic calculation with factor/methodology provenance, honest block reasons for 13 documents, reports/exports for the one record, tenant-isolation probes. **Not demonstrable:** Insight (any family), evidence viewer (no line items), master data, issues, messaging, aggregation/temporal/data-quality over a meaningful population.

---

## 6. Local Supabase findings (read-only)

### 6.1 The local environment

* One local Supabase stack (`carbon_ledger`, Docker) provides Postgres (`127.0.0.1:54426`), GoTrue/PostgREST/Storage/Realtime/Kong containers, and hosts **61 databases** (1 stack DB `postgres` + `_supabase` + `storage_vectors` + 4 "current" databases + ~55 disposable `ct_*` verification clones). `DATABASE-OBSERVED`
* The Demo Lab adds three lab-owned containers (`carbontally_demo_lab_gateway`, `…_storage`, `…_postgrest`) publishing only `127.0.0.1:54430`. `DATABASE-OBSERVED`
* No backend is running (8060, 8070 not listening); the configured `SUPABASE_URL` port (19999) is not listening. `DATABASE-OBSERVED`

### 6.2 The four relevant databases

| Database | Size | Tables | Insight tables | `evidence_line_items` | `source_line_item_id` column | storage schema | Role |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `carbontally_demo_local` | 23 MB | **136** | **0** | present, **0 rows** | present, NULL in the 1 snapshot | 10 tables | Demo Lab (the only current demo DB) |
| `ct_local_93d5cdd` | 16 MB | **135** | **0** | present, 0 rows | present | **2 tables** | the database `backend/.env` points at (near-empty) |
| `carbontally_qa_phase8` | 19 MB | **133** | **0** | present, 0 rows | present | 10 tables | P8 QA shell (0 snapshots, 0 documents) |
| `postgres` | 38 MB | **116** | **0** | **ABSENT** | **ABSENT** | 10 tables | historical investor-scale dataset (975 orgs) |

`DATABASE-OBSERVED` for every cell.

### 6.3 Migration state

* Release chain: **81** migration files; the last six are the Insight chain (`20261001000000` I1, `20261002000000` I2, `20261003000000` I4, `20261005000000` discovery/aggregation/rate-limit, `20261006000000` P2, `20261007000000` P3).
* **None of those six is applied in any local database** (`carbontally_insight_*`, `insight_rate_limit_buckets`, `insight_concurrency_leases` all absent; `DATABASE-OBSERVED`).
* There is **no migration-ledger table in the local databases** that records applied revisions (`supabase_migrations.schema_migrations` does not exist in the lab DB), so the applied revision must be inferred from object presence. Marker objects place all four databases **before** `20261001`: they *do* have `disclosure_report_instance_binding`, `report_version_artifacts`, `vehicles`, `customer_factors`, `source_line_item_id` (except `postgres`) and billing/retention tables. `DATABASE-OBSERVED` + `INFERENCE`
* `postgres` sits much earlier: no `evidence_line_items`, no `source_line_item_id`, no `disclosure_*` tables (116 tables). `DATABASE-OBSERVED`

### 6.4 Integrity and lineage observations

* The one Demo Lab calculation is internally consistent and traceable: snapshot `af640887…` → `source_item_id=2b41b332…` **resolves to a real `manual_extraction_items` row** → `emissions_logs.eb88e764…` references that snapshot → factor `b9d1ed06-…` (DEFRA-2025) → `2469.169780` kg CO₂e → `audit_trail` rows exist (113). `DATABASE-OBSERVED`
* `emissions_logs.file_id` is **NULL** for that record → the emissions row is linked to the document only *indirectly* (via snapshot → extraction item), which is why ISC-1's D33 chain matters. `DATABASE-OBSERVED`
* `supplier_id` is NULL in the only emissions row → supplier analytics remain structurally empty (`no_data`), as documented. `DATABASE-OBSERVED`
* The Demo Lab contains two **non-corpus** documents (`scope2_water_plus_commercial_invoice.pdf`, `ohd079-invalid-probe.txt`) plus 12 corpus PDFs — i.e. the lab carries artefacts from earlier probes, not only T3 output. `DATABASE-OBSERVED`

---

## 7. Live Supabase findings

```text
LIVE SUPABASE ACCESS — NOT AVAILABLE
```

**Why (evidence, not assumption):**

| Check | Finding | Evidence |
| --- | --- | --- |
| Configured environment | `backend/.env` `ENVIRONMENT=local`; `DATABASE_URL` host = `127.0.0.1` (port 54426, database `ct_local_93d5cdd`); `SUPABASE_URL` = `http://127.0.0.1:19999`; `REACT_APP_API_URL` = `http://localhost:8060` | `CODE-TRACED` (structure only; **no credential value was read, printed or transmitted**) |
| Hosted Supabase project URL/key in the configured environment | **none present** (every configured endpoint is a loopback address or `localhost`) | `CODE-TRACED` |
| Frontend environment | `frontend/.env.local` keys: `REACT_APP_API_URL`, `REACT_APP_SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY`, `PORT`, `BROWSER`, `WATCHPACK_POLLING` — values not read; the repository contains no hosted project link or CLI credential | `CODE-TRACED` |
| Deployment tooling / credentials | no `render`/`vercel`/`supabase` CLI credential or project link found; the repository's `vercel.json` files are static rewrite rules only | `DOCUMENT-SOURCED` (CT-P8-I2 production state §2–§3) |
| Prior authoritative position | `docs/verification/CT-P8-I2-PRODUCTION-DEPLOYMENT-STATE-20260921.md`: **`BLOCKED — PRODUCTION STATE UNKNOWN`** — Render revision, Vercel revision and production DB applied-state (`20261001000000`/`20261002000000`) all UNKNOWN, with no authorised production inspection path | `DOCUMENT-SOURCED` |
| Documented hostnames | the Render API hostname (`carbontally-api.onrender.com`) and the public site are documented in the repository, but **a documented hostname is not access** and no request was made to it | `DOCUMENT-SOURCED` |

**Stop-condition compliance:** this study's §21 requires a stop if "live Supabase cannot be safely inspected read-only", if "credentials would require mutation privileges", or if "a live query risks exposing customer/PII data". Here (a) **no live credential exists at all** in the configured environment, and (b) the only available credentials are *local* ones with superuser/service privileges, which are both non-live and mutation-capable. Live inspection was therefore **not attempted** — no connection, no probe, no query, no hostname request.

**Consequences for this study:**

* §8 (local vs live vs release schema comparison) can only be completed as **local vs release**; the live column is `UNKNOWN` by construction, not by omission.
* §9 (data comparison) likewise: live counts are `UNKNOWN`.
* Every live-environment statement in this study is an `UNKNOWN`, never an assumption.

**To unblock (PO action, not performed here):** provide an authorised read-only production inspection path — a hosted Supabase project URL plus a **read-only** (not service-role) credential, or an approved migration ledger and anonymised aggregate report, plus the deployed Render/Vercel revision. Until then, no conclusion about live schema, live data, live drift or live readiness may be drawn.

---

## 8. Local vs live vs release schema comparison

| Dimension | Release (migrations) | `carbontally_demo_local` | `ct_local_93d5cdd` | `carbontally_qa_phase8` | `postgres` (historical) | Live |
| --- | --- | --- | --- | --- | --- | --- |
| Migration files | 81 | subset | subset | subset | much smaller subset | **UNKNOWN** |
| Public tables | — | 136 | 135 | 133 | 116 | **UNKNOWN** |
| Insight schema (I1/I2/I4/analytics/P2/P3) | **present** in files `20261001…20261007` | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **UNKNOWN** |
| Rate-limit tables (`insight_rate_limit_buckets`, `insight_concurrency_leases`) | present | ABSENT | ABSENT | ABSENT | ABSENT | **UNKNOWN** |
| `evidence_line_items` | present | present (0 rows) | present | present | **ABSENT** | **UNKNOWN** |
| `disclosure_value_evidence` | present | present (0 rows) | present | present | **ABSENT** | **UNKNOWN** |
| `calculation_snapshots.source_line_item_id` | present | present | present | present | **ABSENT** | **UNKNOWN** |
| disclosure/report tables (`disclosure_report_*`, `report_version_artifacts`) | present | present | present | present | **ABSENT** | **UNKNOWN** |
| `vehicles` | present (`20260825000000`) | present | present | present | present | **UNKNOWN** |
| `customer_factors` | present | present | present | present | present | **UNKNOWN** |
| billing/commercial tables | present | present | present | present | present | **UNKNOWN** |
| retention config (`system_settings`) | present | present | present | present | present | **UNKNOWN** |
| storage substrate | 10 tables in the platform clone | 10 | **2** | 10 | 10 | **UNKNOWN** |
| RLS/policy parity | defined in migrations | assumed applied | assumed applied | assumed applied | older policy set | **UNKNOWN** |

**Findings:**

1. **The single largest schema gap is the Insight chain**: it exists in the release and in **no** local database. `DATABASE-OBSERVED`
2. `ct_local_93d5cdd` (the *configured* database) additionally lacks the storage substrate (2 tables vs 10) → any storage-backed path (document preview, signed URLs, evidence artefacts) cannot work there without re-provisioning. `DATABASE-OBSERVED`
3. `postgres` is a **pre-evidence, pre-disclosure schema** — it predates `evidence_line_items`, `disclosure_*` and `source_line_item_id`; it therefore cannot host the evidence story at all. `DATABASE-OBSERVED`
4. Live drift **cannot be assessed** (`UNKNOWN`): the release contains 81 migrations and the last production record (2026-09-21) could not confirm even `20261001`/`20261002`. `DOCUMENT-SOURCED`

---

## 9. Current data comparison

All local figures are `DATABASE-OBSERVED` on 2026-09-24. Live is `UNKNOWN` (§7). Only counts and already-published non-sensitive identifiers are reported; no customer/PII rows were read.

| Object | `carbontally_demo_local` (Demo Lab) | `ct_local_93d5cdd` (configured) | `carbontally_qa_phase8` | `postgres` (historical investor dataset) | Live |
| --- | --- | --- | --- | --- | --- |
| `organizations` | 4 | 25 | — | **975** | UNKNOWN |
| `auth.users` | **13** | — | — | **1,205** | UNKNOWN |
| `organization_members` | 8 | 16 | — | **1,125** | UNKNOWN |
| documents (`organization_files`) | 14 | **0** | 0 | **263** | UNKNOWN |
| `storage.objects` | 15 (2 buckets) | — | — | **685** | UNKNOWN |
| `document_processing_queue` | 14 (13 `blocked`, 1 `review`) | 0 | 0 | **40** | UNKNOWN |
| `manual_extraction_items` | 14 (1 calculated, 11 extracted, 2 pending) | 1 | 0 | **264** across 11 statuses | UNKNOWN |
| batches | 4 | — | — | — | UNKNOWN |
| mapped / validated | 0 / 0 | 0 | 0 | **12 / 10** | UNKNOWN |
| calculated items | **1** | 0 | 0 | **14** | UNKNOWN |
| approved / rejected items | 0 / 0 | 0 | 0 | **30 / 3** | UNKNOWN |
| `calculation_snapshots` | **1** | 0 | 0 | **100** | UNKNOWN |
| `emissions_logs` | **1** | 0 | 0 | **100** | UNKNOWN |
| `evidence_line_items` | **0** | 0 | 0 | table **ABSENT** | UNKNOWN |
| `disclosure_value_evidence` | **0** | 0 | 0 | table **ABSENT** | UNKNOWN |
| `report_versions` | 2 (both `DRAFT`) | 0 | 0 | **17** (all `DRAFT`) | UNKNOWN |
| `audit_trail` | 113 | 0 | 0 | 563 | UNKNOWN |
| `emission_factors` | **7,049** | **0** | 0 | **7,049** | UNKNOWN |
| `customer_factors` | 0 | 5 | 0 | 245 | UNKNOWN |
| facilities / assets / suppliers | **0 / 0 / 0** | — | 0 | 157 / 310 / 156 | UNKNOWN |
| `consultant_clients` | 2 | — | 0 | **917** | UNKNOWN |
| consultant profiles / firms | 1 firm | — | 0 | **55** | UNKNOWN |
| `processing_entities` | 1 | — | 0 | **11** | UNKNOWN |
| `staff_profiles` / `staff_roles` | 3 / 3 | — | — | 21 / 6 | UNKNOWN |
| `conversations` / `messages` | **0 / 0** | — | 0 | 36 / 54 (incl. **2 orphan** conversations with zero participants = the MSG-1 side effect) | UNKNOWN |
| `issues` | **0** | — | 0 | 69 (33 open, 11 resolved, 6 in_progress, 6 escalated, 6 closed) | UNKNOWN |
| Insight records | table **ABSENT** | ABSENT | ABSENT | ABSENT | UNKNOWN |

**Readiness reading (`INFERENCE` from the counts):** the historical dataset is the only local dataset with *breadth* (975 orgs, 917 client engagements, 30 approved items, 100 snapshots), but it sits on a schema that **cannot express** the evidence/disclosure layer and cannot be regenerated here. The Demo Lab has the *current* schema but almost no data. Neither database alone is investor-grade; choosing between "adapt the rich legacy dataset" and "re-provision and populate the Demo Lab" is the central demo-data decision (§16).

---

## 10. End-to-end customer journey

`Code` = implementation exists (file evidence). `Local DB` = Demo Lab data state. `Live DB` = `UNKNOWN` throughout (§7). `Browser/demo verified` = evidence from DR-001…DR-007 (2026-09-21).

| Stage | Code | Local DB (Demo Lab) | Live DB | Browser/demo verified | Status |
| --- | --- | --- | --- | --- | --- |
| Authentication (email/password, roles) | lab GoTrue + frontend `/login`, `/auth/*` | 13 identities; sessions issuable; **backend not running** | UNKNOWN | ✔ DR-003 (real login, session, org context) | **IMPLEMENTED + VERIFIED** (needs the backend started) |
| Organisation / workspace | `/home`, `/dashboard/*`, v3 layout | 4 orgs, 8 memberships | UNKNOWN | ✔ DR-003 / DR-005 | **IMPLEMENTED + VERIFIED** |
| Document upload | `POST /api/v3/uploads` + consultant-client route | 14 documents, 15 storage objects | UNKNOWN | ✔ T3 (201s), DR-004/005 | **IMPLEMENTED + VERIFIED** |
| Extraction | `services/automatic_extraction.py`, `ai_document_extraction.py` | 11 `extracted`, 2 `pending` | UNKNOWN | ✔ DR-004 (fields read verbatim) | **IMPLEMENTED + VERIFIED** (text-native PDFs only; OCR deferred) |
| Mapping | `engines/matching_stages.py`, `data/emission_factors.py` | **0 mapped**; 13 blocked (`no_match`/ambiguous) | UNKNOWN | ✔ DR-005 (machine reason on screen) | **PARTIAL** — 2/11 corpus families resolve; spend impossible (ISC-9) |
| Validation | `engines/validation.py` (A1/A2/A5) | blocking reasons recorded in the queue | UNKNOWN | ✔ DR-005 | **IMPLEMENTED + VERIFIED** |
| Calculation | `engines/calculation.py`, immutable snapshots | **1 snapshot** (`2469.169780`) | UNKNOWN | ✔ DR-004 (arithmetic on screen) | **IMPLEMENTED + VERIFIED** (1 record) |
| Review / approval | `/review`, `/processing/*`, customer-review route | 1 `customer_review`; **never executed** | UNKNOWN | ➖ wired only (DR-005 §17) | **IMPLEMENTED + NOT VERIFIED (execution)** |
| Dashboard | `/home` metrics | counts from real rows | UNKNOWN | ✔ DR-003 | **IMPLEMENTED + VERIFIED** |
| Emissions history | `EmissionsPage`, `data/emissions_logs.py` (activity/factor joins — ISC-3 fixed) | **1 row** | UNKNOWN | ✔ DR-005 (export CSV contains it) | **IMPLEMENTED + VERIFIED** (1 row) |
| Evidence / provenance (lineage panels) | `api/v3_emissions.py`, snapshot lineage | chain exists for 1 record; **0 evidence lines** | UNKNOWN | ✔ DR-004 (COMPLETE lineage panel) | **PARTIAL** |
| **Source Evidence Viewer** | `v3/evidence/SourceEvidenceViewer.jsx` + `GET /api/v3/evidence/line-items/{id}` — **independently verified code** | **0 rows → nothing to resolve** | UNKNOWN | ➖ never shown from live data | **CODE VERIFIED + DATA ABSENT (not demonstrable)** |
| Report generation | `engines/reporting`, `report_versions`, artefacts | 2 versions (both `DRAFT`) | UNKNOWN | ✔ DR-006 (real total, real downloadable artefact) | **IMPLEMENTED + VERIFIED** |
| Export | `api/v3_exports.py` (CSV/JSON/audit-package) | 1 emissions row exportable | UNKNOWN | ✔ DR-005 (server-side fetch proves content) | **IMPLEMENTED + VERIFIED** |
| **Insight** (identified calculation, discovery, aggregation, provenance, temporal, data quality, reproducibility) | I1–I6, INS-01, P2, P3 code + tests | **schema ABSENT → cannot run** | UNKNOWN | ➖ never demonstrated | **IMPLEMENTED + NOT RUNNABLE LOCALLY (environment/schema gap)** |
| Messaging | messaging surfaces + Realtime | **0 conversations** | UNKNOWN | ➖ live delivery blocked (no `/realtime/v1` on the lab gateway) | **PARTIAL** |
| Master data (facilities/assets/suppliers/vehicles) | D17 CRUD | **0 / 0 / 0** (vehicles table present) | UNKNOWN | ✔ facilities/assets exercised in the historical dataset context (DR-005 era) | **IMPLEMENTED + DATA GAP in the Demo Lab** |
| Billing / commercial surfaces | `api/v3_billing.py`, `BillingPage.jsx` | billing tables present, no rows | UNKNOWN | ✔ DR-005 (provider-neutral surfaces, no payment integration) | **PARTIAL (surfaces only)** |

---

## 11. Evidence-chain forensic result (priority investigation)

### 11.1 The chain in the Demo Lab, traced end-to-end

```text
source document            organization_files: 14 rows (12 × t3imp_* corpus + 2 probe artefacts), status 'uploaded'
        │                  storage.objects: 15 objects in 2 buckets
        ▼
extraction item            manual_extraction_items: 2b41b332-98ef-4f99-9ea0-5d40d1da0a6c   ✔ row EXISTS
        │                  (11 other items 'extracted', 2 'pending')
        ▼
mapped factor              emission_factors: b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5 (DEFRA-2025, 'kWh (Net CV)')
        ▼
validation                 validation findings recorded for the blocked items; the calculated item passed
        ▼
calculation snapshot       af640887-5818-47ad-b351-1505ac049c32
        │                  activity='Natural gas' · qty=12181.4 · unit='kWh (Net CV)' · co2e=2469.169780
        │                  scope='Scope 1' · fy=2025 · factor_kind='emission_factor'
        │                  source_item_id=2b41b332…  ✔ POPULATED      source_line_item_id=NULL ✖
        ▼
emissions log              eb88e764-b93a-4bd6-8b66-a24fd6e45ca9
        │                  snapshot_id=af640887… ✔   factor_id=b9d1ed06… ✔
        │                  file_id=NULL ✖  (document linked only indirectly)   supplier_id=NULL ✖
        ▼
evidence_line_item         *** 0 ROWS: the link does not exist ***
        ▼
provenance / viewer        GET /api/v3/evidence/line-items/{id} — nothing to resolve
        ▼
report                     report_versions: 2 rows, both status 'DRAFT', linked to 2 report ids
        ▼
Insight                    unavailable: carbontally_insight_* tables do not exist
```

**Where the chain breaks:** (i) at `source_line_item_id` (NULL) — the *line*-level link; (ii) at `evidence_line_item` — the whole table is empty, so the Source Evidence Viewer has no addressable object; (iii) at `Insight` — the schema is absent. The document→snapshot link itself (`source_item_id`) **is** present and resolves to a real extraction item.

### 11.2 ISC-1 (`source_item_id` never written) — precise root-cause conclusion

| Question from the brief | Answer | Evidence |
| --- | --- | --- |
| Does the problem still exist in current code? | **No.** `source_item_id=item.id` is now set at **three** calculate sites: `backend/api/v3_operations.py:573` (D33), `:1280` (Gate-4 remediation F2), `:1911` (D33); the automatic pipeline propagates `job.source_item_id` (`services/automatic_processing.py:780,910,1505`) | `CODE-TRACED` |
| Does it still exist in the local Demo Lab? | **No.** The single snapshot carries `source_item_id=2b41b332…`, which resolves to a real `manual_extraction_items` row | `DATABASE-OBSERVED` |
| Does it exist in live? | **UNKNOWN** (§7) | — |
| Was it fixed? | **Yes** — the Phase-1 core-workflow restoration added it to both manual calculate paths, and the automatic path propagates the job's item id | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| Was it fixed only in one environment? | **Not applicable** — the fix is application-level, environment-independent. What differs is *data*: pre-fix rows remain (1 of 100 historical snapshots still NULL) | `DATABASE-OBSERVED` |
| Is it caused by seed data / workflow code / schema / an incomplete migration? | **Historical cause: workflow code** (the calculate path built `CalculationRequest` without `source_item_id`). **Residual cause: legacy data** (1 pre-fix row in the historical dataset) | `DOCUMENT-SOURCED` + `DATABASE-OBSERVED` |
| Investor impact now | **LOW for `source_item_id`** (fixed); **HIGH for the line/evidence gap** (§11.3) | `INFERENCE` |

### 11.3 The evidence-line layer — precise root-cause conclusion

| Question | Answer | Evidence |
| --- | --- | --- |
| Is there a code defect? | **No defect was found in the viewer or its repository**; the Shared Source Evidence Viewer passed independent verification (`PASS WITH NON-BLOCKING OBSERVATIONS`, 2026-09-22) | `DOCUMENT-SOURCED` |
| Why is `evidence_line_items` empty everywhere? | Because **online processing deliberately does not create evidence lines** — it only *resolves* already-materialised ones (`v3_operations.py:487`, `automatic_processing.py:1822`: "a LOOKUP, never an inference"). Materialisation is implemented in `data/evidence_line_items.py` (`_INSERT_SQL`, `_BACKFILL_SQL`), and the **only invoker in the repository** is the offline CLI `tools/backfill_evidence_line_items.py` (dry-run by default; `--apply` gated). That backfill **has never been run** against any local database | `CODE-TRACED` + `DATABASE-OBSERVED` |
| Where is the gap? | **PROCESS + AUTHORIZATION + DATA**, not code: the CLI's own docstring states "*Execution against any environment is separately authorised*", and B2's contract records production as **not** authorised (G0-D outstanding) | `DOCUMENT-SOURCED` |
| Does the historical dataset have the problem too? | **Worse**: it has **no `evidence_line_items` table at all** (pre-B2 schema), so the evidence chain cannot exist there without a schema upgrade (81-migration catch-up) | `DATABASE-OBSERVED` |
| Live? | **UNKNOWN** | — |
| Investor impact | **HIGH** — the "single document, fully evidenced" story depends on this link; today the viewer cannot be shown with live data in any reachable environment | `INFERENCE` |
| Implied but not-yet-proven secondary cause | `evidence_line_items` materialisation requires persisted line-level extraction (`extracted_data.line_items[]`); the demo corpus's extraction items are mostly `extracted` but not mapped, so *whether* a backfill would find line data in the Demo Lab is **UNKNOWN** and must be established by a dry run before any `--apply` | `INFERENCE` |

---

## 12. Insight readiness

### 12.1 The implemented surface (verified against code)

| Element | State | Evidence |
| --- | --- | --- |
| I3 tool catalogue | **10 tools**: 4 ratified (`report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`) + 3 INS-01 (`insight_discovery`, `insight_aggregation`, `insight_aggregate_provenance`) + P2 (`insight_temporal_comparison`) + P3 (`insight_data_quality`, `insight_calculation_reproducibility`); pinned by `assert len(TOOL_REGISTRY) == 10` | `CODE-TRACED` + test pin |
| Status vocabulary / answer states | 6 `ToolStatus` values; 15 I4 `AnswerStatus` values; `reason` is a free-form contract string | `CODE-TRACED` |
| NL boundary | planner → closed tool schema; **never** SQL, never authorization, never tenant selection, never calculation (`Architecture Reference v2 §12`) | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| Bounds | 25 discovery results, 50 groups, 100 provenance snapshots, 3,660-day period, tolerance ceilings, 4 calls/interaction, 2 provider attempts | `DOCUMENT-SOURCED` (matrix §3.3) |
| Rate limiting | PostgreSQL buckets + concurrency leases; closed under INS-01; **tables absent locally** | `DOCUMENT-SOURCED` + `DATABASE-OBSERVED` |
| Frontend | `/insight` (customer only), `InsightPage/Interaction/AnswerState/References` + **`InsightComparison` (P2 only)**; **no P3 renderer** | `CODE-TRACED` |
| Public "Ask" surface | prior NL verification concluded **`NOT IMPLEMENTED`** for a backend Ask (the only NL UI at that time was a frontend-only FAQ/mock with 0 network calls). The authenticated `/insight` workspace is the real implementation and post-dates that finding | `DOCUMENT-SOURCED` |
| Data dependency | `backend/data/insight_interactions.py` INSERTs/SELECTs `carbontally_insight_interactions` / `_tool_calls` — **absent in every local database** | `CODE-TRACED` + `DATABASE-OBSERVED` |

### 12.2 Family-by-family readiness

| # | Family | Implementation | Verification | UI | Local-demo readiness | Investor value | Remaining blocker | Authorization |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Identified calculation | EXISTS | INS-01 closed (I3 verified) | ✔ | **NOT RUNNABLE** (schema absent) | HIGH | Insight schema missing | provisioning only |
| 2 | Discovery | EXISTS | INS-01 closed | ✔ | NOT RUNNABLE | HIGH | schema; thin data | provisioning only |
| 3 | Aggregation | EXISTS | INS-01 closed | ✔ | NOT RUNNABLE | HIGH | schema; 1 snapshot | provisioning only |
| 4 | Aggregate provenance | EXISTS | INS-01 closed | ✔ | NOT RUNNABLE | HIGH | schema; evidence lines empty | provisioning only |
| 5 | Scope analysis (totals) | PARTIAL | — | ✔ | NOT RUNNABLE | MED–HIGH | no cross-scope comparison semantics | policy |
| 6 | Scope 3 categories | MISSING | — | ✖ | n/a | HIGH | taxonomy (D-13) | **NOT AUTHORIZED** |
| 7 | Scope 2 market-based | MISSING | — | ✖ | n/a | HIGH | methodology (D-10) | **NOT AUTHORIZED** |
| 8 | Scope 1 decomposition | MISSING | — | ✖ | n/a | HIGH | model (D-15) | **NOT AUTHORIZED** |
| 9 | Supplier intelligence | PARTIAL (NO DATA) | — | ✔ | NOT RUNNABLE | MED–HIGH | persistence (D-09); 0 suppliers in lab | **NOT AUTHORIZED** |
| 10 | Facility/asset intelligence | PARTIAL | — | ✔ | NOT RUNNABLE | HIGH | 0 facilities/assets in lab | provisioning + data |
| 11 | Temporal comparison (**P2**) | EXISTS | **verified PASS + PO CLOSED** | ✔ dedicated view | NOT RUNNABLE; zero-baseline data | HIGH | schema; single-period data | provisioning only |
| 12 | Variance / attribution | MISSING | — | ✖ | n/a | HIGH | D-12 (+D-13) | **NOT AUTHORIZED** |
| 13 | Factor intelligence | PARTIAL | — | ✔ | NOT RUNNABLE | MED–HIGH | candidate/rejection history not retained (D-13) | partial |
| 14 | Data quality (**P3**) | EXISTS | verified PASS + observations; P3-IV-01 remediated & re-verified; **NOT PO-closed** | **no renderer** | NOT RUNNABLE | HIGH | schema; no UI; closure wording | provisioning + PO closure |
| 15 | Methodology / boundary | MISSING | — | ✖ | n/a | MED | no D-ID; boundary model absent | **NOT AUTHORIZED** |
| 16 | Evidence / audit (E3, not E4) | PARTIAL | viewer independently verified | ✔ | NOT RUNNABLE (0 rows) | HIGH | evidence lines unpopulated; E4 undefined (D-16) | backfill authorization |
| 17 | Knowledge (Mode E) | MISSING | — | ✖ | n/a | LOW–MED | content governance (D-17) | **NOT AUTHORIZED** |
| 18 | Reporting / disclosure assistance | PARTIAL | — | ✔ | NOT RUNNABLE | MED | framework mapping (D-18) | **NOT AUTHORIZED** |
| 19 | Decision / reduction | MISSING | — | ✖ | n/a | LOW–MED | methodology (D-19) | **NOT AUTHORIZED** |

### 12.3 Answer-to-evidence chain — the ten points in the brief

| Point | Finding |
| --- | --- |
| 1 identified calculation · 2 discovery · 3 aggregation · 4 aggregate provenance | Code complete and verified; **not runnable locally** (schema) and data-thin |
| 5 temporal comparison | P2 closed; needs two populated periods to be *interesting* |
| 6 data quality · 7 reproducibility | Implemented + independently verified; **no UI**; not runnable locally; P3 not PO-closed |
| 8 Source Evidence Viewer | Code independently verified; **no data** to resolve |
| 9 unsupported / ambiguous questions | 15-state vocabulary + honest block reasons exist; `unsupported`/`no_data` unit-verified; not demonstrable in the current lab |
| 10 answer-to-evidence chain | Broken at the evidence-line link (§11) — the most important demo gap after the Insight schema |

---

## 13. Accounting capability readiness

Statuses are kept strictly separate. "PO-approved in principle" is **not** implementation authorization: the PO decision matrix itself states "*For each row marked APPROVE/REQUIRED, the next artifact must be a bounded Cline implementation authorization*" and "*No Cline task may interpret 'APPROVE' as permission to implement all dependent capabilities at once*" (`CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md` §7). `DOCUMENT-SOURCED`.

| Capability | Actually implemented | Architecturally planned | PO-approved in principle | Implementation-authorized | Verified | NOT AUTHORIZED / blocked |
| --- | --- | --- | --- | --- | --- | --- |
| **Scope 1 totals** | ✔ engine + `scope` dimension; the Demo Lab's one snapshot is `Scope 1` | ✔ | C-01 (bounded Insight exposure) | ✔ (via INS-01 aggregation) | ✔ (data + browser) | — |
| **Scope 2 location-based** | ✔ as the default/only method (no method dimension exists) | ✔ | C-15 (dual reporting) | partial | ✔ as "scope totals" | market-based is NOT AUTHORIZED |
| **Scope 2 market-based** | ✖ (only a disclosure vocabulary: `SCOPE2_METHODS`, `scope2_method_hint`) — vocabulary ≠ methodology | ✔ | ✔ (C-15 "as product target") | ✖ | ✖ | **NOT AUTHORIZED** (D-10) |
| **Scope 3 Categories 1–15** | ✖ (no category dimension) | ✔ | ✔ (C-03) | ✖ | ✖ | **NOT AUTHORIZED** (D-13) |
| **Supplier intelligence** | PARTIAL — dimension structurally present, permanently empty (`supplier_id` never written; 0 suppliers in the Demo Lab) | ✔ | ✔ conditional (C-06) | ✖ | ✖ | **NOT AUTHORIZED** (D-09) |
| **Facility / asset intelligence** | ✔ lineage-based support (facility/asset dimensions + labels) — but **0 facilities/assets in the Demo Lab** | ✔ | C-04 | ✔ | partial (historical dataset context) | demo data gap |
| **Temporal comparison** | ✔ `insight_temporal_comparison` | ✔ | C-10/C-11 | ✔ (P2) | ✔ + **PO CLOSED** | — |
| **Variance / attribution** | ✖ | ✔ | ✔ in principle (C-10, C-11) | ✖ | ✖ | **NOT AUTHORIZED** (D-12/D-13) |
| **Emission-factor intelligence** | PARTIAL — factor *used* explainable; candidate/stage history not retained | ✔ | ✔ (C-09; factor history per §3.10) | ✖ | partial | **NOT AUTHORIZED** (D-13) |
| **Data quality** | ✔ `insight_data_quality` (+ partial-coverage observation) | ✔ | C-12 | ✔ (P3) | ✔ (independent, not closed) | PO closure only |
| **Reproducibility** | ✔ `insight_calculation_reproducibility` (10 conditions) | ✔ | C-12/C-18 | ✔ (P3) | ✔ (independent, not closed) | PO closure only |
| **Methodology / boundary intelligence** | ✖ (no boundary model, no explanation contract) | partial | **no D-ID exists** | ✖ | ✖ | **NOT AUTHORIZED** (needs a new decision) |
| **Evidence / audit** | PARTIAL — E3 lineage; the viewer is independently verified; **E4 does not exist** | ✔ | C-18 (aggregate→evidence) | partial | viewer ✔ | E4 **NOT AUTHORIZED** (D-16) |
| **Reporting / disclosure assistance** | PARTIAL — real reports/versions/artefacts; **no framework/obligation mapping** | ✔ | — | partial | ✔ for generation | framework mapping **NOT AUTHORIZED** (D-18) |
| **Decision / reduction intelligence** | ✖ (no target/scenario model) | ✔ | "APPROVED FUTURE" (C-19) | ✖ | ✖ | **NOT AUTHORIZED** (D-19) |
| **Knowledge layer (Mode E)** | ✖ | ✔ | "APPROVED FUTURE" | ✖ | ✖ | **NOT AUTHORIZED** (D-17) |
| **Commercial / billing** | PARTIAL — configurable commercial data model + admin API + UI surfaces; **no PSP, no entitlements, no invoicing** | ✔ | — | ✖ | ✖ | **NOT AUTHORIZED** (D-20…D-26) |
| **L7 lifecycle (retention/erasure/hold)** | PARTIAL — configurable retention, 2 of 5 domains enforced, soft-delete only | ✔ | N3 configurability | ✖ | ✖ | values **NOT AUTHORIZED** (D-01…D-08) |
| **Consultant / auditor Insight personas** | ✖ (consultant APIs exist; Insight personas do not) | ✔ | — | ✖ | ✖ | **DEFERRED / NOT AUTHORIZED** (P-01/P-02) |

---

## 14. Historical defect reconciliation

Each row: historical position → **current code** → **current local database** → live (`UNKNOWN` unless noted) → verified? → investor impact → required action and authorization. No historical finding is assumed fixed merely because newer code exists.

| Finding | Historical position | Current code status | Current local DB status | Verified? | Investor impact | Required action | Authorization |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **ISC-1** (P1) `source_item_id` never written → document→emissions lookup broken | Broken for every calculated item | **FIXED** — written at `v3_operations.py:573,1280,1911`; automatic path propagates `job.source_item_id` | Demo Lab populated ✔; historical dataset **99/100** populated (1 legacy NULL) | Code ✔ + data ✔ | LOW now (was HIGH) | accept the 1 legacy NULL or re-audit | none |
| **ISC-2** (P2) blocking validation issues never closed on approval | Open blocking issues survived an `approved` item | **FIXED** — `issues.py::resolve_open_for_item/_batch` wired to clean validate/approve | Demo Lab: 0 issues | Code ✔ | MED | demonstrate issue open→resolve | demo data |
| **ISC-3** (P2) emissions history lacked activity/factor | Neither shown | **FIXED** — `emissions_logs.py:72` joins `COALESCE(cs.activity_type,'unknown')` + factor | Demo Lab: 1 row (renders activity/factor) | Code ✔ | MED | none | none |
| **ISC-4** (P3) asset create 500 without facility; no facility name | Raw 500 + UUID display | **Not re-verified** in this study | Demo Lab: **0 assets / 0 facilities** | **UNKNOWN** | LOW | re-verify when master data is populated | code re-check |
| **ISC-6** (P3) notifications hook called the removed legacy route | Bell never loaded (404 everywhere) | **FIXED** — `useNotifications.js:65` → `/api/v3/notifications` | n/a (frontend) | Code ✔ | LOW | none | none |
| **ISC-7** (P3) new facility displayed `Inactive` | Status contradiction | **Not re-verified** | Demo Lab: 0 facilities | **UNKNOWN** | LOW | re-verify with master data | code re-check |
| **ISC-8** (P2) duplicate custom factor → raw 500 | Unhandled unique violation | **FIXED** — clean **409** paths ("never a raw 500") | configured DB: 5 customer factors, no duplicates | Code ✔ | MED | none | none |
| **ISC-9** (P2) spend-based mapping dead-end | `factors: []` then 422; no browse fallback | **PARTIAL** — `mapping-options` returns an explicit `no_factors_reason`; **no browse/search fallback** | **0** £/GBP units and **0** spend activities in *both* databases | Code partially ✔ | **HIGH (investor-critical)** | PO decision on spend-factor coverage (C-06/D-09 area) **+** a bounded fallback-picker implementation if authorized | **PO DECISION + authorization** |
| **ISC-10** (P2) `system_admin` inconsistent (no `can_manage_billing`) | Seed role lacked the permission staff-admin had | Code enforces `can_manage_billing` (`v3_commercial.py:59`; default False in `auth.py:38`); divergence was **seeded role data** | historical dataset has 6 `staff_roles` rows (JSONB permissions); the specific divergence **not re-queried** | Code ✔; data **UNKNOWN** | LOW–MED | PO decision on the staff role model, then bounded seed alignment | **PO DECISION** |
| **ISC-11 / 12 / 13** (positive) consultant portfolio, client isolation, factor approval gates | Verified working at investor scale | no conflicting change found | Demo Lab: 2 consultant_clients, 4 orgs | `DOCUMENT-SOURCED` (not re-run) | HIGH (isolation story) | re-demonstrate in the chosen environment | none |
| **ISC-14** (positive + demo note) PE boundaries; **PE queues empty** | Boundaries correct; only 1 batch entity-assigned | PE routes/boundaries code-traced | Demo Lab: 1 PE; 13 blocked items **not PE-assigned** | `DOCUMENT-SOURCED` | MED | assign batches to a PE if the PE story is shown | demo data |
| **ISC-15** (P3) no item ever reached `customer_review` | Customer approval unrepresented (seed wrote `approved` directly) | state machine permits `calculated → customer_review → approved` | Demo Lab: **1 item in `customer_review`** (queue `review`), **never approved** | data partially resolved; action unexercised | MED | execute one approval walkthrough (DR-005 §20 item 2) | **PO DECISION (mutation)** |
| **ISC-16** (P3) ISC-1 breadth (25/27 NULL) | Dataset-wide breakage | same as ISC-1 | historical dataset now **1/100** NULL | `DATABASE-OBSERVED` | LOW | none | none |
| **PRC-1** (P1) customer review queue → 500 ("id" ambiguous) | Review screen unusable | **FIXED** — `list_customer_review` uses aliased, qualified SQL (`i.`/`b.`, CL-1/D5 rationale) | Demo Lab: 1 review item; route not executed (no backend running) | Code ✔ | HIGH (was demo-blocking) | none | none |
| **MSG-1** (P2) conversation create → 500 + orphan rows | `ON CONFLICT` with no matching constraint; orphans left | **FIXED** — the insert no longer uses `ON CONFLICT` (`data/messaging.py:110-118`) | historical dataset still holds **2 orphan** conversations (of 36); Demo Lab 0 | Code ✔; legacy data ✔ | LOW | optional bounded cleanup of the 2 orphan rows (mutation) | optional |
| **MD-2** (blocker) `vehicles` migration not applied | Vehicles surface blocked | migration `20260825000000_v3m7_vehicles.sql` present in the release | **`vehicles` exists in all four databases** | `DATABASE-OBSERVED` | LOW | none | none |
| **SEC-1** (P1) Viewer could upload a document | Write on a read-only role | **FIXED** — explicit viewer denial, `403` (`v3_documents.py:221-227`, CL-42) | n/a | Code ✔ + `BROWSER-VERIFIED` (DR-005 "View only") | HIGH (security story) | demonstrate ALLOW+DENY in the demo | none |
| **CAL-3** (P2) `/api/reference/fuel-types` → 500 | Legacy factor table missing | **FIXED** — queries `emission_factors.activity_type`. **Caveat:** it uses the Supabase REST client, so it needs the configured API endpoint (19999, currently down) | n/a | Code ✔ | LOW | none (note the endpoint dependency) | none |
| **P3-IV-01** | `insight_data_quality` reported `all_checks_passed` when nothing was checkable | **REMEDIATED** (`8554b78`) → `no_checkable_records` | not runnable locally (schema) | **independently re-verified** (`2be9033`) | MED (honesty) | none; P3 closure wording | **PO closure** |
| **P3-IV-02 / 03 / 04 / 05** | foreign-id oracle · stale migration filename · unenumerated regression set · D17 pin `81 == 71` | open (governance / documentation / test pin) | n/a | `DOCUMENT-SOURCED` | LOW each | bounded corrections if the PO wants them | **PO DECISION** |
| **DR-004 / DR-005 / DR-007 findings** | 6 display discrepancies; realtime route missing; approval never executed; report staleness; 3 PO items; jest `canvas` limitation | DR-007's 3 defects fixed and browser-verified; others unchanged | reports both `DRAFT`; 0 conversations | `BROWSER-VERIFIED` | MED–HIGH | PO decisions 1–6 of DR-005 §20 and the 3 DR-007 items | **PO DECISION** |
| **CON-1…3, D19-2, D21-2, RET-1, SA-4, AUTH-1** | carried from earlier audits | **not re-audited in this study** | — | **UNKNOWN** | variable | re-audit before any claim touching them | re-audit |
| **P12 preflight blockers** | Insight schema absent; evidence lines empty; corpus 2/11; harness verification FAIL; no script/runbook; reset unverified; live unknown | unchanged by this study | re-confirmed by fresh queries | ✔ | HIGH | see §18 | mixed |

**Reconciliation summary:** of the findings named in the brief, **ISC-1, 2, 3, 6, 8, 16, PRC-1, MSG-1, MD-2, SEC-1 and CAL-3 are fixed in code** (with data evidence where data exists); **ISC-9 and ISC-10 remain materially open** (data/policy); **ISC-4 and ISC-7 are unverified either way** (no master data to exercise them); **ISC-5 and ISC-11…14 are positives** with demo-data caveats; **ISC-15 is data-resolved in the Demo Lab but never executed**; and the **P3-IV, DR and P12 items remain open governance**.

---

## 15. Security findings

| Area | Position | Evidence |
| --- | --- | --- |
| Tenant isolation (platform-wide) | Strong and layered: RLS in migrations + server-side org predicates + I2 authorization for Insight; suites and demo probes assert ALLOW **and** DENY | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| Viewer write-path (SEC-1) | Fixed — viewer upload denied (`403`) | `CODE-TRACED` |
| PE boundary | PE users cannot reach customer documents/conversations (`403`); entity-scoped staff profiles | `DOCUMENT-SOURCED` (ISC-14) |
| Consultant / client boundaries | Cross-consultant and same-consultant cross-client isolation verified at investor scale | `DOCUMENT-SOURCED` (ISC-11/12) |
| Signed URLs / raw document exposure | Storage objects private; workspace shows "View only — download disabled for this role"; storage-security tests exist; **no signed URL appears in any reviewed report** | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| Insight authorization | I2 boundary + object re-check + references-as-locators (never grants); viewer DM-6 independently verified | `DOCUMENT-SOURCED` |
| Pre-existing cross-tenant exposure | `snapshot_count_for_factor()` / `factor_usage_span()` via `GET /api/v3/emissions/factors/{id}` remains **separately tracked** (INS-01 closure §8.6) — not worsened, not fixed | `DOCUMENT-SOURCED` |
| Security-adjacent product defects still open | **F-T1-001** (`audit-activity` 500 for an authorised owner) and **P3-IV-02** (foreign-id existence oracle) | `DOCUMENT-SOURCED` |
| Live/production security posture | **UNKNOWN** — no access (§7); the production state record is `BLOCKED` | `DOCUMENT-SOURCED` |
| Demo credentials | Lab credentials live **outside** the repo (`$HOME/ct_local_env/demo_lab/credentials.local.json`, mode 0600); manifests contain **no** secrets; the historical dataset's credentials live in a gitignored local file | `CODE-TRACED` + `DATABASE-OBSERVED` |
| Credentials handling in this study | Key **names** only were inspected (never values); no hosted credential exists to leak; nothing was transmitted; **no secret, token, JWT or signed URL appears in this report** | method statement |
| `F-046-1` invariant | The destructive integration harness must never target persistent QA, the investor demo or production. The fixture's name guard rejects `qa`/`demo`/`investor`/`prod`, **but the historical dataset's database is named `postgres`**, which that guard does **not** match — a residual risk to record | `DOCUMENT-SOURCED` + `CODE-TRACED` |

**No security finding was fixed, probed destructively or "verified" by mutation in this study.** All database access was read-only `SELECT`; no endpoint was invoked; no RLS policy was touched.

---

## 16. Demo data strategy

### 16.1 The three candidate datasets compared on capability coverage (not size)

| Criterion | Historical investor dataset (`postgres`) | Demo Lab (`carbontally_demo_local`) | External generator + T3 corpus |
| --- | --- | --- | --- |
| Breadth | **High** (975 orgs, 917 client engagements, 263 docs, 100 snapshots, 30 approvals, 69 issues, 36 conversations, 157 facilities, 310 assets, 156 suppliers, 245 customer factors) | **Very low** (4 orgs, 14 docs, 1 snapshot) | corpus only (11 scenarios, 49 files) |
| Schema currency | **Old** (116 tables; **no evidence/disclosure layer**, no `source_line_item_id`) | **Current minus Insight** (136 tables) | n/a |
| Deterministic calculations | 100 snapshots (76 with a factor; 1 NULL `source_item_id`) | 1 snapshot, fully documented | 2/11 scenarios reach a matched factor |
| Evidence lineage | **Impossible** (no `evidence_line_items`) | table present but **empty** | possible once populated |
| Report coherence | 17 versions, all `DRAFT` | 2 versions, both `DRAFT` | n/a |
| Insight coverage | none (no Insight tables) | none (no Insight tables) | none |
| Security boundaries demonstrable | High (many orgs/roles/consultants/PEs) | Low (13 identities, 4 orgs) | isolation scenarios only |
| Failure honesty | mixed (historical rows include pre-fix defects) | **strong** (13 honest blocks with machine reasons) | strong by design |
| Reset / repeatability | **Tooling missing** → not reproducible | **Tooling present** (idempotent seeder + `reset_demo_lab.sh`) | reproducible from the pinned generator |
| Regenerable here? | **No** | **Yes** | Yes (needs a pinned checkout at `8ade2bf`) |

### 16.2 Recommendation

1. **Retire `tools/seed_investor_demo` as a demo mechanism** (it is already absent from the checkout), but **do not delete its data artefact**: treat `postgres` as a **read-only historical reference/UAT dataset** for regression context and persona research — never as the investor demo environment. Retiring the *mechanism* removes the temptation to treat an unregenerable dataset as canonical. `INFERENCE`
2. **The canonical investor-demo environment should be a freshly provisioned Demo Lab on the current release schema** (all 81 migrations including the six Insight migrations), populated by the existing deterministic tooling: `run_demo_lab.sh` → `provision.py` → `seed_factors.py` → `t3_scenarios.py sync-corpus/seed`, plus — once authorized — the evidence-line backfill. It is the only environment whose schema can express the evidence and Insight layers and whose state can be recreated deterministically. `INFERENCE`
3. **Extend the demo dataset beyond the current 14 documents** so it carries the stories the platform promises: several **mapped→validated→calculated→approved** items across **two periods** and **two scopes**, at least one **facility/asset-linked** item, at least one **consultant-client** item, at least one **PE-assigned** batch, and a small **issue** set — while keeping the honest ambiguous/no-match scenarios as first-class *truthfulness* moments. Exact composition is a PO decision. `INFERENCE`
4. **Never use production/customer data as demo data.** Even if live access is later granted, live data is a *verification* target (read-only), never a demo source. `DOCUMENT-SOURCED` (AGENTS.md §55) + `INFERENCE`
5. **Spend-based documents**: either load a spend-factor set and implement a factor browser (ISC-9, PO decision) or **exclude spend documents from the demo script and say so**. `INFERENCE`
6. **Hygiene items** — the 2 orphan conversations in the historical dataset and the two non-corpus probe artefacts in the Demo Lab (`ohd079-invalid-probe.txt`, `scope2_water_plus_commercial_invoice.pdf`) — leave them, or clean them only under an explicit mutation authorization. `DATABASE-OBSERVED`

---

## 17. Investor-ready acceptance definition

"Investor ready" is used below as a precise, bounded set of conditions — not as a label. Passing it is **not** production authorization, certification, or a commercial commitment.

### Must work (a real investor can be shown it, live, deterministically)
1. Authentication for every persona used in the script, landing each in the correct workspace.
2. Upload → extraction → **mapping → validation → calculation** completing for **at least two** real scenarios (ideally across two periods and two scopes), with the deterministic figure, factor, methodology and algorithm version visible on screen.
3. A blocked document explaining, on screen, exactly what was attempted and why it stopped, with a next step.
4. Reports generated from persisted emissions with a **downloadable artefact whose numbers match the dashboard and export**.
5. Exports (CSV/JSON) returning the same authoritative numbers.
6. **Insight**: identified-calculation explanation, discovery, aggregation and aggregate provenance working against real data through the customer `/insight` surface.
7. **Source Evidence Viewer**: at least one answer traceable to an evidence line item and from there to the source document/page.

### Must be demonstrable (not merely claimed)
8. P2 temporal comparison over two explicit periods, including its zero-baseline and empty-period behaviour.
9. P3 data quality and calculation reproducibility, presented with their true status (implemented, independently verified, **not PO-closed**) and with the partial-coverage observation stated rather than hidden.
10. Tenant isolation with **ALLOW *and* DENY** shown for at least one cross-organisation pair and one plane boundary.
11. Consultant/client isolation and the PE boundary, each as at least one visible denial.
12. One **`unsupported`/`no_data`** moment and one **ambiguous/no-match** moment — deliberately scripted.

### Must be truthful
13. Every number on screen traces to a persisted record the audience can see.
14. No fabricated emissions, no invented evidence, no implied certification, no implied production readiness, no implied payment capability.
15. Billing is described as configuration/surfaces only; retention is described with its enforced/unenforced reality; scope coverage gaps (Scope 3, market-based Scope 2, Scope 1 decomposition, variance, supplier analytics) are stated as *not yet implemented*.
16. Synthetic/demo data is identified as such (generator pin, corpus provenance, demo domain, `t3imp_` prefixes).

### Must be independently verified
17. The demo harness (corpus selection, seeding, reset, ground-truth comparison) has an **independent verification that is not a FAIL** — today it is FAIL-then-implementer-verified (§14).
18. Any capability called "closed"/"verified" has a hash-identified independent verification record; anything else is described with its real status.
19. The pre-demo verification run is recorded with Git SHA, database identity, migration count, scenario list and raw output.

### Can remain visibly limited (and must be *spoken*, not discovered)
20. One calculation record is not enough — but where coverage is thin (e.g. a single period), the limitation is stated.
21. OCR/scanned documents unsupported; spend-based mapping unsupported or covered by a PO decision.
22. Messaging live delivery, deeper consultant/client journeys, PE queues and the billing/PSP path may remain out of the script **if** the presenter says so.
23. Live/production environment state may remain UNKNOWN and unshown.

### Must not be claimed
24. Production readiness, security certification, audit assurance, ISO/SOC compliance, commercial/pricing commitments, L7 erasure/legal hold, or any "AI calculated this" framing.
25. Any capability in §13 marked **NOT AUTHORIZED**, and anything the demo does not actually show.

---

## 18. Recommended implementation roadmap

Sequence from the current state to an investor-demonstrable platform. **None of this is implemented or authorized by this study.** Each package states objective, capabilities, dependencies, code areas, DB implications, demo implications, security implications, verification requirement, PO decisions, whether it can be authorized *now*, and its L7/L8/commercial coupling.

### A. Forensic / reconciliation (documentation + narrow code re-checks)
* **Objective:** remove the divergences that currently make "what is true" ambiguous.
* **Capabilities:** reconcile `AGENTS.md` §54 (missing `seed_investor_demo` path; 1,185-identity claim); decide the fate of untracked PO reference documents (D-27); record the Demo Lab's schema revision in its evidence; re-verify ISC-4/ISC-7 once master data exists; enumerate the P3-IV-04 set; correct the P3-IV-03 filename; re-pin P3-IV-05 (D17 count).
* **Dependencies:** none. **Code areas:** docs; `AGENTS.md`; possibly `backend/tests/unit/data/test_d17_*` (re-pin only under authorization).
* **DB implications:** none. **Demo implications:** prevents a presenter citing the wrong dataset. **Security implications:** none.
* **Verification:** corrected records reviewed against current code (no silent edits to ratified documents).
* **PO decisions:** D-27; which dataset is canonical; whether constitution text is corrected.
* **Authorizable now?** Yes (documentation subset). **L7/L8/commercial:** none. **Priority:** architecture-critical; not investor-visible.

### B. Foundation repairs (small, high-leverage)
* **Objective:** close the narrow gaps that make the core story fragile.
* **Capabilities:** (i) **ISC-9** — factor browse/search fallback in `mapping-options` (plus spend-factor coverage if the PO decides); (ii) make the `evidence_line_items` materialisation/backfill **runnable and authorized** for a chosen environment; (iii) confirm ISC-4/ISC-7.
* **Dependencies:** (i) independent; (ii) couples to D; (iii) needs A. **Code areas:** `api/v3_processing_workflow.py` (`mapping_options`), `data/emission_factors.py`, `tools/backfill_evidence_line_items.py` (execution, not code), `api/v3_organizations.py` if defects confirm.
* **DB implications:** possibly a factor-set data load; **no schema change** expected. **Demo implications:** removes the two most common dead-ends (spend documents, empty evidence). **Security implications:** the browse fallback must preserve the closed allowlist and org scoping.
* **Verification:** unit tests for fallback semantics; **dry-run then applied** backfill report.
* **PO decisions:** spend coverage policy; backfill authorization target.
* **Authorizable now?** Partially — the fallback and the backfill **dry run** now; `--apply` and spend coverage need PO decisions. **L7/L8/commercial:** none. **Priority:** investor-critical (evidence) + customer-critical (mapping).

### C. Demo environment and data
* **Objective:** one canonical, reproducible, populated demo environment.
* **Capabilities:** define it; re-provision the Demo Lab to the current schema (all 81 migrations incl. Insight); restore a pinned generator checkout (`8ade2bf`); rebuild the corpus; seed the §17 stories (two periods, two scopes, facility/asset linkage, consultant-client item, PE-assigned batch, small issue set); keep the honest ambiguity/missing-evidence scenarios.
* **Dependencies:** A (canonical-dataset decision); PO authorization because it **resets/mutates lab data**. **Code areas:** `tools/demo_lab/*` (run, not rewrite, unless a provisioning gap appears).
* **DB implications:** lab database rebuilt and populated (lab-local only). **Demo implications:** enables every demo story. **Security implications:** lab-only; must never touch the stack `postgres` dataset or production.
* **Verification:** pre-demo verification run (SHA, DB identity, migration count, scenario list, raw output); reset→re-provision→re-seed rehearsal with second-run idempotency.
* **PO decisions:** authorize re-provision (current lab data is lost); approve dataset composition; decide report-artefact handling.
* **Authorizable now?** Only as a proposal — it is inherently mutating. **L7/L8/commercial:** none. **Priority:** investor-critical + architecture-critical.

### D. Evidence and provenance
* **Objective:** make the answer-to-evidence chain demonstrable with real rows.
* **Capabilities:** run the Class-1 evidence-line backfill (dry run → applied) in the demo environment; confirm `source_item_id` **and** `source_line_item_id` population on the demo items; demonstrate the Source Evidence Viewer from an Insight answer and from entity surfaces; show DM-6 re-authorization with a live ALLOW/DENY pair.
* **Dependencies:** C; B (outcomes worth evidencing). **Code areas:** none expected — `data/evidence_line_items.py` and `api/v3_evidence.py` are implemented and the viewer is independently verified.
* **DB implications:** inserts into `evidence_line_items` **in the demo lab only**; no schema change. **Demo implications:** unlocks the strongest differentiator ("ask → deterministic answer → evidence → source"). **Security implications:** show the viewer's per-read re-authorization; no signed URLs on screen.
* **Verification:** the backfill's dry-run report is the operation's own evidence; the **demo narrative** must then be verified end-to-end.
* **PO decisions:** authorize `--apply` against the demo lab; confirm E3-only language.
* **Authorizable now?** After C. **L7/L8/commercial:** none. **Priority:** investor-critical + audit-critical.

### E. Insight presentation
* **Objective:** make the Insight layer runnable and presentable.
* **Capabilities:** (i) the six Insight migrations applied in the demo environment (part of C, restated as a hard dependency); (ii) one scripted customer `/insight` journey per implemented family (identified calculation, discovery, aggregation, aggregate provenance); (iii) **P2** with a genuine two-period delta; (iv) **P3** with its true status and the partial-coverage caveat respected; (v) a decision on a minimal P3 presenter path (generic tool-call + narration vs a small renderer) — **no** new evidence viewer, **no** NL/SQL surface.
* **Dependencies:** C; D for provenance answers. **Code areas:** none for (i)–(iii); a small frontend addition only if (v) is authorized (`frontend/src/v3/insight/*`).
* **DB implications:** none beyond C. **Demo implications:** converts "Insight exists in code" into "Insight answers questions". **Security implications:** the I2 boundary and the rate limiter must behave (their tables come from the same migration set).
* **Verification:** an Insight verification step added to the demo tooling (absent today); P2/P3 suites already green.
* **PO decisions:** P3 presentation wording; whether a minimal P3 UI is authorized; whether to demonstrate `rate_limited`.
* **Authorizable now?** Design/planning yes; implementation after C. **L7/L8/commercial:** none. **Priority:** investor-critical (differentiation).

### F. Accounting capability expansion (Scope 3 / market-based Scope 2 / Scope 1 decomposition / variance / supplier persistence / factor history / methodology-boundary)
* **Objective:** (future) broaden accounting coverage.
* **Capabilities:** the §13 rows marked NOT AUTHORIZED. **Dependencies:** each requires an **accounting policy decision** (D-09, D-10, D-12, D-13, D-15, plus a new D-ID for methodology/boundary) **before** any code.
* **Code areas (indicative only, not designed here):** engines, dimensions, migrations. **DB implications:** new taxonomy/dimension storage (migrations).
* **Demo implications:** **none required for the investor demo** — the demo must instead return `unsupported`/`no_data` honestly. **Security implications:** every new dimension must remain organisation-owned and immutable once used.
* **Verification:** not specified until authorized. **PO decisions:** the taxonomy/methodology decisions themselves.
* **Authorizable now?** **No** — policy-blocked. **L7/L8/commercial:** none. **Priority:** architecture-critical for the product, **explicitly out of scope for the investor demo**.

### G. Governance / L7 (retention, deletion, legal hold, erasure, export scope, provider/privacy retention)
* **Objective:** make lifecycle claims defensible. **Capabilities:** enforce the remaining retention domains or surface their unenforced state; legal hold; erasure/organisation deletion; storage-object propagation; formal export scope.
* **Dependencies:** **PO decisions D-01…D-08**. **Code areas:** `services/retention.py`, `data/settings.py`, deletion paths.
* **DB implications:** soft-delete/lifecycle paths, possibly new tables. **Demo implications:** today only "configurable retention; 2 of 5 domains enforced" may be described — **no erasure/hold claim**. **Security implications:** the never-purge invariant for audit/evidence must be preserved; erasure must not weaken evidence.
* **Verification:** bounded enforcement + negative tests. **PO decisions:** all of D-01…D-08.
* **Authorizable now?** **No** — policy-blocked. **L7/L8:** this *is* L7. **Priority:** audit-critical long-term; **customer-critical before any retention claim**.

### H. Operational / L8-A (SLO/SLA, alert thresholds/recipients, incident runbook, secrets policy, RTO/RPO, restore cadence)
* **Objective:** operational governance beyond demo scope. **Capabilities:** configure alerting/SLO, incident response, secrets ownership/rotation, restore-verification cadence.
* **Dependencies:** PO decisions (D-08, D-20…D-26 area; X2/X7 record reconciliation = D-28). **Code areas:** `services/operational_alerting.py`, `services/api_metrics.py` (configuration surfaces).
* **DB implications:** configuration rows. **Demo implications:** none — but **no SLO/SLA commitment may be presented**. **Security implications:** the missing secrets policy is a genuine gap.
* **Verification:** configuration + alert-firing evidence. **PO decisions:** thresholds, recipients, cadence, ownership.
* **Authorizable now?** **No** — policy-blocked. **L7/L8:** this *is* L8-A. **Priority:** customer-critical post-demo; optional for P12.

### I. Commercial / billing (PSP, entitlements, invoicing, dunning, tax, refunds, plans/pricing)
* **Objective:** (future) commercial capability beyond demo scope. **Capabilities:** the L8-B set.
* **Dependencies:** **PO decisions D-20…D-26**. **Code areas:** `domain/billing.py`, `data/billing.py`, `api/v3_billing.py`, `BillingPage.jsx`.
* **DB implications:** none new required for surfacing; a PSP integration is a separate, security-heavy authorization. **Demo implications:** **surfaces only**, explicitly without implied payment. **Security implications:** webhook authentication, replay defence, PCI-scope avoidance.
* **Verification:** not specified until authorized. **PO decisions:** the whole commercial model.
* **Authorizable now?** **No** — policy-blocked. **L7/L8:** this *is* L8-B. **Priority:** commercial-critical long-term; **optional for P12**.

### J. Investor verification gate (the demo gate itself)
* **Objective:** prove the demo is truthful, repeatable and reproducible.
* **Capabilities:** scripted demo flow with truthful-limitation sentences; pre-demo verification run recorded (SHA, DB identity, migration count, scenario list, raw output); reset→re-seed rehearsal; independent re-audit of the DR-001…DR-007 findings; explicit statement that passing is **not** production authorization.
* **Dependencies:** C, D, E (+ B). **Code areas:** `tools/demo_lab/verify.py` plus a small Insight check; the demo-script artefact (new).
* **DB implications:** none. **Demo implications:** this *is* the gate. **Security implications:** show ALLOW+DENY; no secrets on screen.
* **Verification:** an **independent** pass (not the implementing agent); the harness's own verification status must stop being FAIL.
* **PO decisions:** the acceptance checklist (§17) and the limitation script.
* **Authorizable now?** The planning/design half yes; the run requires the other packages. **L7/L8/commercial:** none. **Priority:** investor-critical.

### K. Production readiness (deployment, environment promotion, migration-drift gating, OCR capacity, live RLS verification, backup/restore, monitoring)
* **Objective:** (separate track) make the platform deployable.
* **Capabilities:** production deployment authorization (G0-D), environment promotion, deploy-time migration-drift gating, OCR memory/capacity remediation, live RLS verification on a real database, restore cadence, external monitoring.
* **Dependencies:** **explicit production authorization** plus the L7/L8 policy layer. **Code areas:** deployment configuration, rendering memory handling, drift gates.
* **DB implications:** production migrations (34 + 2 undeployed per B2's record) — **no production migration is authorized here**. **Demo implications:** **none** — production readiness is excluded from the demo gate. **Security implications:** secrets management, drift gating, RLS verification.
* **Verification:** a separate production gate. **PO decisions:** authorization plus all of the above.
* **Authorizable now?** **No — NOT AUTHORIZED**. **L7/L8/commercial:** all three. **Priority:** production-critical; **explicitly out of scope for the investor demo**.

### 18.1 Prioritisation by kind (with the dependency that justifies it)

| Class | Items | Justification (dependency-based, not a rank) |
| --- | --- | --- |
| **Investor-critical** | B (ISC-9 fallback, evidence backfill), C, D, E, J | without C nothing Insight/evidence can run; without D the evidence promise is empty; without B the two most common dead-ends remain; J is the gate itself |
| **Customer-critical** | B (mapping fallback), ISC-15 approval walkthrough, master-data seeding, report-artefact coherence | these are the day-to-day customer workflows on which the demo also depends |
| **Audit-critical** | D (evidence/lineage), A (record reconciliation), the open P3-IV items | auditability claims must be backed; P3-IV items are honesty debts |
| **Security-critical** | a live-RLS verification path, the F-046-1 target-guard residual risk (`postgres` name), the secrets policy (H) | isolation is the strongest demo asset; the guard gap is a narrow but real operational risk |
| **Architecture-critical** | A (which dataset/authority is canonical), F (taxonomy decisions), matrix/preflight staleness | sequencing errors here cascade into every later package |
| **Cosmetic** | remaining display polish, empty-state polish, dead-end copy | improves the demo; blocks nothing |
| **Optional** | messaging live delivery, PE/internal journey depth, rate-limit demo, responsive/a11y audit, browser automation | valuable if time allows; none is required for a truthful demo |

---

## 19. PO decisions required

Nothing below may be decided by an implementing agent. Existing registers are referenced rather than restated in full.

### 19.1 Decisions specific to reaching an investor demonstration (new, from this study)

| ID | Decision | Why it blocks | If deferred |
| --- | --- | --- | --- |
| **P12-D1** | **Which dataset is canonical** — the 13-actor Demo Lab (tooling present, schema current, data thin) or the historical 975-organisation dataset (data rich, schema old, tooling absent) | every demo story depends on this | the demo cannot be scripted coherently |
| **P12-D2** | **Authorize re-provisioning the Demo Lab** to the current release schema (all 81 migrations, incl. the six Insight migrations), accepting that current lab data is destroyed | without it **no** Insight capability can run | Insight remains undemonstrable |
| **P12-D3** | **Authorize demo-data population/extension** (corpus re-sync + seed + the §17 story set) | the demo otherwise shows one calculation | thin, unconvincing demo |
| **P12-D4** | **Authorize the evidence-line backfill** (`python -m tools.backfill_evidence_line_items --apply`) against the demo environment, after a dry run | without it the Source Evidence Viewer has nothing to show | the evidence story cannot be told |
| **P12-D5** | **Spend-factor coverage policy** (load a spend factor set and/or authorize a factor browse fallback) | ISC-9 leaves a large document class unmappable | spend documents must be excluded and named unsupported |
| **P12-D6** | **P3 presentation wording** — "implemented + independently verified, PO closure outstanding" (recommended) vs waiting for closure | affects the honesty of the Insight narrative | risk of over- or under-claiming |
| **P12-D7** | **Whether to authorize a minimal P3 presenter surface**, or present P3 through the generic tool-call + narration view only | affects how much of P3 an audience can see | P3 stays API-layer only |
| **P12-D8** | **Whether to execute one approval walkthrough** (a real state change on a demo identity) | ISC-15 means the approval step has never been executed | the approval story stays "wired but unexercised" |
| **P12-D9** | **PE work assignment** (assign batches to a PE) if the PE story is to be shown | the Demo Lab has no PE-assigned work | the PE workspace shows an empty queue |
| **P12-D10** | **Live-environment introspection path** — supply an authorised **read-only** production route, or accept live state as permanently UNKNOWN for this phase | every live statement is UNKNOWN | live drift cannot be assessed |
| **P12-D11** | **Reconcile the documentation divergences** (`AGENTS.md` §54; the P1 matrix's 7-tool count and MISSING family statuses; master-preflight §9.4/§17.1 staleness; the T3 record inconsistency) — inside P12 or in the governance track | agents/presenters may cite the wrong authority | recurring confusion |
| **P12-D12** | **The demo's truthful-limitation script** (which limitations are spoken aloud) | truthfulness is a gate condition (§17) | risk of implying capabilities that do not exist |
| **P12-D13** | **Report-artefact coherence** (regenerate the stale annual report; handle the duplicate and the unrefreshable `ghg_inventory`) | investor-visible incoherence | the demo shows a stale/duplicate artefact |
| **P12-D14** | **Independent verification of the remediated demo harness** (corpus selection/reset/ground-truth) | its only independent verdict is FAIL | the demo's own evidence producer is unverified |

### 19.2 Existing decision registers (unchanged, still open)

* **D-01…D-08** L7 (retention, deletion semantics, legal hold, erasure scope, storage propagation, export scope, provider/privacy retention, backup RTO/RPO) — master preflight §12.1.
* **D-09** supplier persistence · **D-10** Scope 2 market-based · **D-11** temporal-comparison basis *(partly satisfied by P2; restatement semantics remain open)* · **D-12** variance/attribution · **D-13** Scope 3 taxonomy + factor history · **D-14** authoritative data-quality signals · **D-15** Scope 1 decomposition · **D-16** E4 audit-package definition · **D-17** knowledge-source governance · **D-18** reporting frameworks · **D-19** decision/reduction methodology — master preflight §12.2.
* **D-20…D-26** commercial (provider, model, catalogue, entitlements, overage, refunds, invoicing/tax, metering, SLO) — master preflight §12.3.
* **D-27** durability of untracked PO documents · **D-28** X2/X7 record reconciliation · **D-29** pre-existing reviewer/SLA failures — matrix §9.2.
* **FAC-1 / PO-1** single-admin custom-factor deadlock (ISC-5) · **ISC-10** staff role model · **P-01/P-02** consultant/auditor Insight · **P-03/P-04/P-05** I7/I8/production — decision matrix §2.

---

## 20. Explicitly NOT AUTHORIZED work

This study authorizes **nothing**. The following remain unauthorized or explicitly out of scope and must not be started on the strength of this report:

| Not authorized | Basis |
| --- | --- |
| Any implementation, fix, refactor, test change, migration, frontend change or configuration change | this is a read-only forensic study |
| **Production deployment**, environment promotion, production configuration or production migrations | G0-D outstanding; master preflight; B2 record; decision-matrix P-05 |
| Any **database mutation** — Demo Lab reset/re-provision, corpus re-seed, evidence backfill `--apply`, orphan-row cleanup, report regeneration | requires explicit PO authorization (P12-D2/D3/D4/D13) |
| **Live Supabase** connection, query, migration or inspection | no authorised read-only path exists (§7) |
| Scope 3 taxonomy, market-based Scope 2, Scope 1 decomposition, variance/attribution, supplier persistence, factor-history intelligence | policy-blocked (D-09…D-15) |
| Knowledge/RAG layer, reporting-framework mapping, reduction/decision intelligence | D-17/D-18/D-19 |
| **L7** retention values/enforcement, legal hold, erasure, storage-object deletion propagation, export scope | D-01…D-08 |
| **L8-A** SLO/SLA commitments, alert thresholds/recipients, incident runbook, secrets policy, RTO/RPO | D-08, D-28 |
| **L8-B** billing/PSP/invoicing/entitlements/overage/refunds/tax | D-20…D-26 |
| Consultant Insight, auditor direct Insight | DEFERRED / NOT AUTHORIZED (P-01/P-02) |
| Creating a second evidence viewer or any new evidence surface | INS-01 §7 / AGENTS.md |
| Unrestricted NL → SQL/database access, or any general NL query engine | Architecture Reference v2 §12 |
| Any new accounting methodology, score, grade, weighting or confidence metric | architecture boundary |
| Modifying the external generator, the seeders, `tools/demo_lab/*`, or the historical dataset | task boundary + AGENTS.md §55 |
| Fixing the review-SLA failures, the D17 pin, F-T1-001 or the P3-IV items | separate governance items |
| Committing the untracked PO/CoStrict artefacts | D-27 |
| Declaring investor readiness, certification or production readiness | not authorized by this task |

---

## 21. Risks and unknowns

| # | Risk / unknown | Type | Impact if unmanaged | Mitigation (proposed, not authorized) |
| --- | --- | --- | --- | --- |
| R1 | **Insight has never run against any database** — all Insight verification is unit/contract-level; a first live provisioning may surface runtime issues (RLS interactions, SQL typing, rate-limiter behaviour) | technical unknown | the Insight demo could fail on the day | provision into a **disposable clone first**, run the suites + a smoke journey, then apply to the demo environment |
| R2 | **The evidence backfill may find no line data** in the Demo Lab (its extraction items are mostly unmapped) | technical unknown | the evidence story stays empty after D | run the **dry run** first and report counts before authorizing `--apply` |
| R3 | **The demo harness's verification status is FAIL** (pre-remediation) and its remediation is implementer-verified only | verification debt | the tooling that *produces* demo evidence is itself unverified | P12-D14 independent pass |
| R4 | **Two divergent datasets**, no tooling for the legacy one, and the legacy DB name `postgres` is **not matched** by the F-046-1 destructive-fixture guard | data governance + safety | accidental destructive targeting of a persistent dataset | rename it or extend the guard under authorization; keep the dataset read-only |
| R5 | **Live/production state is unknowable** from this configuration | environment unknown | any live claim would be unfounded | P12-D10; until then state UNKNOWN explicitly |
| R6 | **Corpus coverage is thin** (2/11 families map; spend unsupported) | data/capability | a viewer may conclude the platform cannot process common documents | script the honest-failure narrative; P12-D5 |
| R7 | **`AGENTS.md` §54/§55 describes a dataset and manifest that do not exist in the checkout** | documentation governance | an agent or presenter may act on a false premise | P12-D11 reconciliation |
| R8 | **P3 is PO-unclosed** with a live partial-coverage observation | governance | over-claiming in the demo | P12-D6 wording; narrate the observation |
| R9 | **Master data, issues and messaging are absent from the Demo Lab** | data gap | three platform surfaces look empty | P12-D3 population |
| R10 | **Legacy Supabase-REST routes depend on a configured API gateway** (port 19999 currently down) | environment coupling | some legacy reference routes error even when the database is healthy | start the configured gateway, or retire the legacy routes (separate decision) |
| R11 | **Report lifecycle never reaches approval** (all 17 + 2 versions are `DRAFT`) | data/process | an "approved report" cannot be shown | decide whether an approval walkthrough is in scope (mutation) |
| R12 | **Unknown breadth of carried findings** (CON-1…3, D19-2, D21-2, RET-1, SA-4, AUTH-1, ISC-4/7) | evidence gap | a hidden defect could surface in a live demo | bounded re-audit before the demo |
| R13 | **61 local databases**, many persistent-looking clones, raise the chance of targeting the wrong one | operational safety | destructive-test risk | keep F-046-1 discipline; verify target identity before every run |
| R14 | **No demo script, runbook or golden-state artefact exists** | process gap | the demo is not repeatable | P12-D12 + package J |

---

## 22. Final recommendation

### A. What is actually working today?
The deterministic core and the customer-facing application: authentication with real personas; the customer workspace and processing/exception workspace with honest machine-readable blocking reasons; upload (direct and consultant-client); extraction; validation; the calculation engine with immutable provenance-bearing snapshots (`2469.169780 kg CO₂e` from a real synthetic gas invoice, with factor, methodology and algorithm version on screen); report generation with a downloadable artefact; exports; and multi-tenant/role isolation, which is independently strong and demo-readable. `BROWSER-VERIFIED` + `DATABASE-OBSERVED` + `CODE-TRACED`.

### B. What is actually broken today?
* **Insight is non-functional in every local environment** — the six Insight migrations are unapplied and the Insight tables do not exist. `DATABASE-OBSERVED`
* **The evidence-line layer is empty everywhere**, so the Source Evidence Viewer (verified code) has nothing to display. `DATABASE-OBSERVED`
* **Spend-based documents cannot be mapped** — no spend factors in either dataset and no browse fallback (ISC-9). `CODE-TRACED` + `DATABASE-OBSERVED`
* **The demo harness's independent verification is a FAIL** and its remediation is unverified. `DOCUMENT-SOURCED`
* The configured development environment is largely **not running** (backends 8060/8070 and the configured Supabase API 19999 are down). `DATABASE-OBSERVED`

### C. What is merely implemented but unverified?
Approval/rejection execution (never run); PE and internal-ops journeys (no browser verification); report lifecycle states beyond `DRAFT`; legacy reference routes behind the unused Supabase client; the remediated T3 harness; and everything Insight-related in a live environment.

### D. What is missing?
A canonical demo environment on the current schema; a demo dataset with evidence, two periods, master data, issues and messaging; a demo script with truthful-limitation sentences; a pre-demo verification record; a verified reset→re-seed rehearsal; an evidence-line population; a factor browse fallback (or a spend-coverage decision); a live-environment introspection path; and any P12-specific permanent record beyond planning artifacts.

### E. What is environment/data/schema drift rather than application functionality?
The Insight schema gap; the Demo Lab's thin population; the legacy-schema historical dataset (no evidence/disclosure tables); `ct_local_93d5cdd`'s missing storage substrate; the unapplied Insight migrations; the historical dataset's drift from its own report; and the absence of `tools/seed_investor_demo` from the checkout. **None of these is an application-code defect.**

### F. What is required for a credible investor demonstration?
Exactly packages **B → C → D → E → J**, plus decisions **P12-D1…P12-D14**: a canonically provisioned demo environment with real evidence rows, at least two completed calculations across two periods, a scripted honest-failure narrative, a live ALLOW/DENY isolation demonstration, and an independent verification that is not a FAIL.

### G. What should we NOT build before the investor demo?
Nothing from packages **F (accounting taxonomy), G (L7), H (L8-A SLO), I (commercial/PSP), K (production)**. Also: no new evidence viewer, no NL→SQL surface, no RAG, no new scores, and no presentation polish that pretends unbuilt capability exists.

### H. What should be the canonical investor-demo environment?
A **freshly provisioned Demo Lab on the current release schema** (`carbontally_demo_local`, provisioned by `tools/demo_lab`), whose state is reproducible, with the historical `postgres` dataset retained **read-only** as a reference/UAT corpus and explicitly excluded from the demo.

### I. What should be the canonical demo dataset strategy?
**Tooling present + data extended.** Keep the deterministic, generator-pinned T3 corpus and its honest failures as the *truthfulness* backbone; extend the seeded population so every §17 story has real rows (two periods, two scopes, facility/asset linkage, a consultant-client item, a PE-assigned batch, a small issue set, an approved report); populate evidence lines through the supported backfill; never use production/customer data.

### J. What is the recommended implementation sequence?
`A` (reconciliation/decisions) → `B` (mapping fallback + evidence-line dry run) → `C` (provision + populate the Demo Lab) → `D` (evidence backfill + viewer demonstration) → `E` (Insight presentation incl. P2/P3 wording) → `J` (gate: script, runbook, rehearsal, independent pass). `F/G/H/I/K` remain separate, policy- and authorization-gated tracks.

### K. Which decisions must the PO make before implementation?
**P12-D1…P12-D14** (§19.1) — above all the canonical dataset, the lab re-provision, the demo-data population, the evidence backfill, the spend-coverage policy, the P3 wording and the demo's limitation script. The existing registers D-01…D-29 remain open for their own packages.

### L. What should be the next bounded Cline implementation authorization?
A bounded package that is **non-mutating first**, then explicitly mutating under named authorizations:

1. **A1 (documentation/forensic):** reconcile the `AGENTS.md` §54 divergence and the P1-matrix / master-preflight staleness in a separate governance note (proposal), and enumerate the P3-IV-04 regression set. No code.
2. **B1 (bounded code):** implement a factor **browse/search fallback** in `mapping-options` (`backend/api/v3_processing_workflow.py`) with unit tests, preserving the closed allowlist and organisation scoping — the smallest change that removes the most common dead-end.
3. **B2 (dry run only):** run `python -m tools.backfill_evidence_line_items` in **dry-run** against the Demo Lab and report counts, establishing whether evidence lines can be materialised (no writes).
4. **C0 (proposal only):** a re-provision-and-populate plan for the Demo Lab, including the six Insight migrations, for PO authorization — **no execution**.

**None of the above is authorized by this study.** The next step is a PO decision, not an implementation.

---

## Appendix — Verification of this study's own repository impact

| Check | Result |
| --- | --- |
| Files created | `docs/architecture/CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY-20260924.md` — **the only change** |
| Application code / tests / migrations / frontend / demo tooling / configuration modified | **none** |
| Database writes | **none** — read-only `SELECT`s against four local databases (`carbontally_demo_local`, `ct_local_93d5cdd`, `carbontally_qa_phase8`, `postgres`); the investor/stack databases were queried **only** for aggregate counts of non-PII tables |
| PII / customer data read | **none** — counts and non-sensitive identifiers only; no row dumps, no credentials, no emails |
| Endpoints invoked | **none** |
| Containers created/removed/reconfigured | **none** (read-only `docker ps` and `docker exec … psql -tAc "SELECT …"`) |
| Secrets, tokens, JWTs or signed URLs in this report | **none** |
| Git state | unchanged by this study (no branch switch, reset, stash, clean, rebase or force-push) |
| Live Supabase | **not contacted** (no credential; stop condition honoured) |
| Commit content | this report only |

---

**COMPREHENSIVE INVESTOR-READY STUDY COMPLETE — READY FOR PO DECISION**

*No investor-readiness declaration is made or authorized by this study. No production deployment, database mutation, billing/payment integration or L7/L8 implementation is authorized. Live Supabase state remains UNKNOWN and is reported as such.*

























