# CT-P8 — CURRENT-STATE GAP RECONCILIATION + CONSULTANT CLIENT FEATURE-PARITY AUDIT

**Report ID:** `CT-P8-CURRENT-STATE-GAP-RECONCILIATION-AND-CONSULTANT-CLIENT-PARITY-20260915`
**Type:** READ-ONLY forensic audit. **No code, schema, migration, configuration or data was modified.**
**Audit date:** 2026-09-15 (repository/commit timeline). Local sandbox wall-clock differed from the
repo's commit timeline; every claim below is pinned to a **commit SHA** rather than to a date.
**Executor:** OHD (independent audit) — no implementation performed.

---

## 1. Executive verdict

**The single most important finding of this audit is that the baseline moved while the audit ran.**
Two commits landed *during* this session (`3a34ae3` X7, `20d27c0` X1+X2 banking), and X8's final
verification report appeared mid-audit. The "final" Phase 8 programme report (`…057`) is therefore
**materially stale**: it declares X4, X5 and X7 *UNBUILT* and X8 *BLOCKED*; all four now exist,
are committed, and are independently verified. Everything in this report is pinned to
**HEAD `20d27c0`** (and, where relevant, to the worktree above it).

### 1.1 Counts (material historical findings reconciled in §4)

| Class | Count | Meaning |
|---|---|---|
| **A — STILL PRESENT** | **18** | Documented gap/defect remains in the current repository |
| **B — IMPLEMENTED, VERIFICATION PENDING** | **1** | Code appears to implement it; no adequate independent verification |
| **C — IMPLEMENTED + VERIFIED** | **21** | Implementation exists **and** credible verification evidence exists |
| **D — PARTIALLY RESOLVED** | **6** | Part fixed; a material portion remains |
| **E — OBSOLETE / SUPERSEDED** | **4** | Finding no longer applies (ruled, or superseded by a later decision) |
| **F — HISTORICALLY INCORRECT / REFINED** | **1 primary + 8 refinements** | The source document's claim is now inaccurate (e.g. `GOV-3`); 8 further rows carry an `F` refinement note because the *finding exists* but the *source claim about it* is stale |
| **G — BLOCKED BY EVIDENCE / ENVIRONMENT** | **7** | Cannot be established without external evidence/access |
| **H — PO DECISION REQUIRED** | **8** | Technical state understood; closure depends on a PO/governance decision |
| **Total reconciled rows in §4** | **66** | Some rows carry a primary class plus a secondary note (e.g. RLS-4A-2 is `C` in QA + `F` against 057's text) |

### 1.2 Consultant Client parity — headline

> **Consultant Client parity does NOT currently hold.** A Consultant Client receives **processing
> parity** (upload → automatic processing → extraction → mapping → validation → calculation →
> customer review → evidence → audit-package export → messaging) but **not reporting parity**:
> a consultant **cannot** generate a report, open a report, read report versions, run any
> report-lifecycle action, download a report, or touch the Phase 8 **disclosure model** for a
> client. The report/disclosure surface is guarded by `require_org_member()` +
> `ensure_org_access(...)`, and `ensure_org_access` grants **internal staff only** — a consultant
> is denied by construction. The consultant also has **no** client-scoped emissions API, exports
> beyond the audit package, master data, billing or settings surface.

### 1.3 Production status

**Production was not accessed, queried or exercised.** No production readiness claim is made.
Production migration state remains **unverified**, and the programme record (`…057` §6 `D-PO-1`,
`D-PO-3`, `D-PO-8`; G0-D) states production is **NOT AUTHORISED**.

---

## 2. Repository baseline

| Item | Value |
|---|---|
| Branch | `main` |
| **HEAD (audit close)** | **`20d27c0b9bc0204159cac5473b93072b9f1cc77b`** — `feat(phase8x): bank X1 operational health and X2 operational alerting` |
| HEAD at audit **open** | `137765f` (X5) — the repository advanced **three times** while this audit ran |
| Commits landed during the audit | `3a34ae3` (X7, 10:54) · `20d27c0` (X1+X2 banking, 11:15) |
| `origin/main` | `9e13236149b8132d737258abc0aa7d69a974a85b` (2026-09-11) |
| Divergence | **0 behind / 19 ahead** — fast-forward possible, nothing pushed since 2026-09-11 |
| Staged | **0** |
| Tracked modifications | **236** (69 of them under `.agents/skills/**`) |
| Untracked files | **923** |
| Stashes | none |
| Datum DB used for read-only queries | `11.0.0.0/54426 :: postgres` (see §2.1) |

**A third party (an implementation agent) is committing to this working tree concurrently.**
Noted as an audit-integrity risk, not a defect: the report is SHA-pinned and the moving baseline is
disclosed rather than hidden.

### 2.1 Database reality (read-only)

`.env` `DATABASE_URL` points at `127.0.0.1:54326`, which **is not listening** in this environment.
The reachable local cluster is `127.0.0.1:54426`. Verified identities:

| Database | Newest applied migration | `anon` table grants | `authenticated` TRUNCATE/REFERENCES/TRIGGER | `public.disclosure*` tables |
|---|---|---|---|---|
| **`postgres`** (canonical) | `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | **455** | **345** | **0** |
| `carbontally_qa_phase8` | untracked (applied out-of-band) | **4** | **0** | **15** |
| `ct_4a1b_20260914` | untracked | **4** | **0** | **15** |
| `ct_x7_20260915` | untracked | **4** | **0** | **15** |

Consequences, stated plainly:

* **No Phase 8 migration is applied to the canonical `postgres` database** — not even the *committed*
  `20260913000000_p8_report_lifecycle_status.sql` (S6).
* `public.evidence_line_items` **does not exist** in `postgres`; `calculation_snapshots.source_line_item_id`
  **does not exist** in `postgres`.
* RLS hardening (RLS-4A-1 / 4A-1b / 4A-2) is present **only** in QA/clone databases. In `postgres`,
  `anon` still holds 455 grants (including `TRUNCATE`) and `authenticated` still holds 345
  blanket `TRUNCATE`/`REFERENCES`/`TRIGGER` grants.
* These are **environment/state facts**, not authorization to change anything.

---

## 3. Documents reviewed

Used as historical baseline (all under `docs/cline/reports/`, `docs/ohd/reports/`, `docs/architecture/`):

| # | Document | Role in this reconciliation |
|---|---|---|
| 1 | `CT-P8-FINAL-PROGRAMME-REPORT-20260914-057.md` | **Primary** historical ledger: §3 closed, §4 verification-pending (**"None"**), §5 external, §6 `D-PO-1…D-PO-11`, §14.4 register, §15 PO declaration of Phase 8 complete |
| 2 | `CT-P8-FINAL-PHASE8-PHASE8X-COMPLETION-REPORT-20260913.md` | Earlier completion claim; superseded by 057 |
| 3 | `CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-049.md` | Batch sequencing / allocation |
| 4 | `CT-P8-DISCLOSURE-MODEL-DESIGN-20260912-004.md` | B1 disclosure model design |
| 5 | `CT-P8-DISCLOSURE-DECISION-RECORD-20260912-006.md` | Disclosure decisions |
| 6 | `CT-P8-P1-PDF-IMAGE-EXTRACTION-FORENSIC-ARCHITECTURE-20260913-020.md` | **P1** forensic findings (§9) |
| 7 | `CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037.md` | P1 remediation contract |
| 8 | `CT-P8-P1-CLOSURE-20260913-053.md` | P1 closure claim |
| 9 | `CT-P8-P2-FACTOR-CATALOGUE-CENSUS-20260913-038.md` | P2 / EF-A / EF-D |
| 10 | `CT-P8-P2-EFE-CLOSURE-20260914-054.md` | **EF-E** closure claim (§10) |
| 11 | `CT-P8-RLS-4A-2-HARDENING-20260914-059.md` | RLS-4A-2 implementation/IV (§13) |
| 12 | `CT-P8-RLS-4A-1-DURABILITY-20260914-060.md` | RLS-4A-1 durability (§13) |
| 13 | `CT-P8-P8X-X1-IMPLEMENTATION-AND-IV-20260914-061.md` | X1 |
| 14 | `CT-P8-P8X-X2-IMPLEMENTATION-AND-IV-20260914-062.md` | X2 |
| 15 | `CT-P8-P8X-X5-IMPLEMENTATION-AND-IV-20260915-065.md` | X5 |
| 16 | `CT-P8-P8X-X7-IMPLEMENTATION-AND-IV-20260915-066.md` | X7 |
| 17 | **`CT-P8-P8X-X8-FINAL-VERIFICATION-20260915.md`** | X8 — appeared **during** this audit |
| 18 | **`CT-GIT-PHASE1-8X-IMPLEMENTATION-COMMIT-PUSH-RECONCILIATION-20260915.md`** | Git/banking truth (§2) |
| 19 | `CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md` (OHD) | Phase 8-X discovery |
| 20 | `CT-SEC-RLS-HOLD-REGISTER-20260912-001.md` (OHD) | RLS hold register |
| 21 | `CT-SYSTEM-BLINDSPOTS-CONSULTANT-WHITELABEL-AUDIT-20260914-001.md` (OHD) | SB-01…SB-12 source findings |
| 22 | `CT-PRODUCT-UX-FUNCTIONAL-AUDIT-20260824-001.md` (OHD) | §6 Consultant Client parity requirement |
| 23 | `CARBONTALLY_PHASE8X_X1_FEASIBILITY_20260914.md`, `…X2_ALERTING_CONTRACT…`, `…X4_AGGREGATION_CONTRACT…`, `…X7_API_RUNTIME_METRICS_CONTRACT_20260915.md` | Stage contracts |

Where documents conflict (057 §4/§6 vs 057 §14.4 on RLS-4A-2; 057 §14.4 vs the 2026-09-15 commits on
X4/X5/X7/X8), the conflict is recorded in §4 and current reality is taken from the repository.

---

## 4. Master gap reconciliation

Classification: **A** present · **B** implemented/verification pending · **C** implemented+verified ·
**D** partial · **E** obsolete/superseded · **F** historically incorrect/refined ·
**G** blocked by evidence/environment · **H** PO decision required.

| ID | Historical finding | Source | Historical status | Current implementation (evidence) | Current evidence | Class | Remaining gap | Owner / workstream | PO? |
| -- | ------------------ | ------ | ----------------- | --------------------------------- | ---------------- | ----- | ------------- | ------------------ | --- |
| B1-1 | Disclosure Model foundation missing | 004 / 006 / 057 §3 | Closed + IV PASS | `domain/disclosure.py`, `domain/disclosure_exposure.py`, `data/disclosure.py`, `api/v3_disclosure.py` (all **untracked**); migration `20260914000000_p8_b1_disclosure_model_foundation.sql` (**untracked**) | 15 `public.disclosure*` tables in QA/clone; **0** in `postgres` | **C** (verification) / **A** (banking+apply) | Unbanked; unapplied to canonical DB | Phase 8 banking + `D-PO-8` | Yes |
| B1-2 | Correction privileges / evidence idempotency | 057 §3 | Closed | migration `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` (untracked) | not in `postgres`; QA/clone only | **A** | same as B1-1 | Phase 8 banking | Yes |
| B2-1 | Evidence line items + provenance line links | 057 §3 | Closed + IV PASS | `data/evidence_line_items.py` (untracked); migrations `20260916000000_p8_b2_evidence_line_items.sql`, `20260916010000_p8_b2_provenance_line_links.sql` | `to_regclass('public.evidence_line_items')` → **NULL** in `postgres`; present in QA | **C**/**A** | Unbanked; unapplied to canonical DB | Phase 8 banking | Yes |
| B2-2 | `…028` B2 closure record (`F-049-1`) | 057 §6 `D-PO-2` | Open | n/a — an explicit PO closure statement | 057 §6 `D-PO-2` | **H** | PO must restate closure + authorise `…028` | PO | Yes |
| B3-1 | Intensity catalogue + ratios | 057 §3 | Closed + V3 PASS | migrations `20260917000000_p8_b3_intensity_catalogue.sql`, `20260917010000_p8_b3_intensity_ratios.sql` (untracked) | QA/clone only | **C**/**A** | Unbanked; unapplied | Phase 8 banking | Yes |
| B4-1 | Narrative overlay + frozen artefact | 057 §3 | Closed + V4 PASS | `data/disclosure_narrative.py`, `domain/disclosure_projection.py`, `data/report_artefacts.py` (untracked); migrations `20260918000000_p8_b4_narrative_overlay.sql`, `20260919000000_p8_b4_frozen_artefact.sql` | QA/clone only | **C**/**A** | Unbanked; unapplied | Phase 8 banking | Yes |
| S1 | Requirements/applicability | 057 §3 | Closed + IV PASS `…056` | disclosure projection code (untracked) | `…056`, 057 §3 | **C** | Unbanked | banking | Yes |
| S2 | `is_current` single-valued | 057 §3 | Verified | migration `20260921000000_p8_s2_is_current_single_valued.sql` (untracked) | QA/clone only | **C**/**A** | Unbanked; unapplied | banking | Yes |
| S3 | Values / mappings | 057 §3 | Closed + IV PASS `…056` | `domain/disclosure.py`, `data/disclosure.py` | `…056` | **C** | Unbanked | banking | Yes |
| S4/S5/S7 | Purpose / narrative / intensity surface | 057 §3 | Verified inside gate V4 | disclosure + narrative modules | 057 §3 | **C** | Unbanked | banking | Yes |
| S6-1 | Report lifecycle backend missing | 057 §14.4 | PO CLOSED (`…063` §12) | `domain/report_lifecycle.py` (6 states `DRAFT…FINAL`, transitions, `allowed_actions`, `can_create_new_version`, `is_immutable`, `required_authority`), `data/report_versions.py`, `api/v3_reports.py` (`/versions`, `/submit`, `/request-changes`, `/reject`, `/approve`, `/finalize`, `POST /versions`) — **all committed** `19e4f01` | `git show HEAD:backend/api/v3_reports.py` §775–910; committed tests `tests/integration/test_report_lifecycle.py`, `tests/unit/api/test_v3_report_lifecycle.py` | **C** | Migration `20260913000000` **not applied** to any reachable DB | apply + PO closure record | Yes |
| S6-2 | S6 **frontend** lifecycle panel | 057 §6 `D-PO-4` | Allocation decision required | `frontend/src/v3/reports/ReportLifecyclePanel.jsx` (**untracked**), mounted at `ReportDetailPage.jsx:234`; unit test `__tests__/report-lifecycle-panel.test.jsx` (**untracked**) | panel reads server `allowed_actions`, renders only performable actions; no independent verification exists | **B** | Unbanked + unverified | banking + IV | Yes |
| S6-3 | `new_version` exposure (`S6-ACTION-1`) | 057 §14.4 | Ruled: future increment, **not** a defect | backend `can_create_new_version` + `POST /versions` exist; the panel intentionally renders `new_version` as **guidance, not a button** (`ReportLifecyclePanel.jsx:71-77`) | code comment states it is outside the approved action list | **E** | None (deferred by ruling) | future increment | Yes (already ruled) |
| S6-4 | Comments scope / `A7` visibility | 057 §6 `D-PO-4` | Undecided | `report_comments` stays dormant | 057 §6 `D-PO-4` | **H** | Product decision | PO | Yes |
| P1-1 | PDF/IMAGE deterministic extraction collapses multiple source lines into one record | `…020` | Open defect | `services/extraction_fidelity.py` (**untracked**) `build_line_items()`; wired at `services/automatic_extraction.py:250` | **default mode is `shadow`** (`extraction_fidelity.py:101-107`, env `CARBONTALLY_P1_EXTRACTION_SHAPE`) → measurement only, collapsing still occurs in customer-visible output | **D** | Enablement requires real documents | external → enablement | Yes |
| P1-2 | Activity and quantity/unit from different source rows | `…020` | Open | per-source-line `line_items[]` in `build_line_items` (enabled mode only) | same shadow gate | **D** | as P1-1 | enablement | Yes |
| P1-3 | Completeness measures produced-record presence, not source coverage | `…020` | Open | `_completeness()` gained a `line_items` branch; a **separate** `coverage` block now reports source coverage (`automatic_extraction.py:236-299`) | `confidence` semantics unchanged; `coverage` added | **D** (partially corrected) | two metrics coexist; naming still conflates | P1 enablement | Yes |
| P1-4 | AI rescue suppressed by the completeness score | `…020` | Open | unchanged in shadow mode; enabled mode gates a suspect document (`status: multi_line_unresolved` + `block_reason`) instead of silently collapsed | `automatic_extraction.py:279-288` | **A** | rescue policy unresolved | P1 enablement | Yes |
| P1-5 | Positional AI/deterministic merge, AI truncation, AI token limits | `…020` | Open | `ai_fanout_plan()` + `PAGE_CAP = 20` + char-cap constants exist in `extraction_fidelity.py:44-48` | shadow mode only | **D** | enablement | enablement | Yes |
| P1-6 | Missing OCR dependencies | `…020` | Environment dependency | PDF text path `_pdf_text` / `_render_pdf_pages_pypdfium` present (`automatic_extraction.py:302+`) | not exercised in this audit (no runtime, no documents) | **G** | runtime/provider proof | environment | No |
| P1-7 | `source_page` conflation / `source_location` persistence | `…020` | Open | `domain/evidence.py:54 source_location_precision()`, `:150`, `:168`, `:344` | page *basis* is disclosed (`marker`/`formfeed`/`document` — `extraction_fidelity.py:110-120`), i.e. never guessed | **D** | precision available only in enabled mode | enablement | Yes |
| P1-8 | `mapped_data.line_items` semantic inconsistency / silent re-extraction / historical re-extraction policy | `…020` | Open | no unification found in the current tree | grep: no single canonical `line_items` contract shared by mapper and extractor | **A** | remains | P1 follow-up | Yes |
| P1-9 | CSV/XLSX header/unit issues | `…020` | Open | `_normalise_columns()` maps headers → `(field, unit_hint)` (`automatic_extraction.py:367+`) | present but the `…020` findings (unit_hint loss) were not disproved | **D** | not re-verified | P1 follow-up | Yes |
| P1-10 | P1 customer-visible enablement | 057 §5 | External dependency | shadow-first by design | `…057` §5 | **G** | needs real non-production documents | external | Yes |
| P2-1 | EF-E exact-unit matching defect | 054 | Closed + verified | `data/emission_factors.py:114-160` `find_by_activity(..., unit_qualifier_tolerant=True)` (PO D-B **T2**); applied at **both** picker sites `api/v3_processing_workflow.py:1117`, `api/v3_emissions.py:558` | dedicated EF-E tests green (`tests/unit/data/test_emission_factors_unit_selection.py`, `tests/unit/services/test_efe_selection_sites.py` — 4 tests, static source assertion included) | **C** | 2 unrelated regression tests fail on a stale double (§14) | EF-E closed | No |
| P2-2 | EF-A / EF-D factor-catalogue magnitude | 038 / 057 §5 | External dependency | n/a | requires the real catalogue behind the production boundary | **G** | cannot be judged locally | external | Yes |
| RLS-4A-1 | `anon` blanket `GRANT ALL` | `…001` hold register | Closed + verified (QA) | migration `20260920000000_p8_rls_anon_grant_containment.sql` (untracked) | QA/clone: `anon` = **4** grants (1 `TRUNCATE`); **`postgres` still 455** | **C** (QA) / **A** (`postgres`) / **G** (prod) | not applied to canonical DB or production | RLS workstream | Yes |
| RLS-4A-1b | default-privilege hardening | `…060` | Verified | migration `20260923000000_p8_rls_4a1b_anon_default_privilege_hardening.sql` (untracked) | QA/clone only | **C**/**A** | as above | RLS workstream | Yes |
| RLS-4A-2 | `authenticated` blanket `TRUNCATE/REFERENCES/TRIGGER` | 057 §6 `D-PO-1` | 057: **NOT AUTHORISED — NOT IMPLEMENTED**; 059: implemented + IV | migration `20260922000000_p8_rls_4a2_authenticated_grant_hardening.sql` (untracked) | QA/clone: authenticated privileged grants = **0**; **`postgres` = 345** | **C** (QA) with **F** (057 §4/§6 now stale) | closure record + apply elsewhere | RLS workstream | Yes |
| RLS-5/3/2/1 | RLS steps 3–5 (policy correctness, reference/operational/critical tables) | 057 §6 `D-PO-3` | Gate **HELD** | none | 116 tables RLS-enabled / 174 policies in `postgres`; `anon` holds 455 grants | **H** | PO rulings on `D-4…D-10`, `D-12` | PO | Yes |
| F-4A1B-1 | latent anon sequence-default exposure | 057 §14.4 | Optional hardening | none authorised | by inheritance only; not anonymous-reachable | **E** | future bounded decision | PO | Yes |
| B4-D12 | commercial gating of finalisation | 057 §6 `D-PO-10` | Deferred | billing gates exist for other flows (§8 SB-07) | `services/billing.py` | **H** | commercial decision | PO | Yes |
| N3-n | remaining retention domains | 057 §6 `D-PO-10` | Deferred | `services/retention.py` enforces **only** `document_retention_days` + `operational_telemetry_retention_days`; audit/evidence explicitly excluded | `_ELIGIBLE_DOMAINS` (`retention.py:35`), `_TELEMETRY_EXCLUDED_TABLES` (`:40-50`) | **H** | no durations approved for other domains | PO | Yes |
| S8 | AI-assisted narrative | 057 §6 `D-PO-9` | Deferred, preconditions unmet | none | 057 §6 | **H**/E | separate authorisation | PO | Yes |
| D16 | legacy disposition (`D-19`) | 057 §14.4 | Never ruled | legacy routes still present (`routes/upload.py` etc.) | `routes/upload.py:288` hard-codes `premium_feature` (SB-09) | **H** | disposition undecided | PO | Yes |
| I1 | authorisation/evidence contradiction (`…041`) | 057 §6 `D-PO-5` | Unresolved | n/a | commit `d91ace5` subject vs ratified D2 | **H** | PO must rule | PO | Yes |
| `…048` | G0-A E1 ESRS evidence closure | 057 §5 | External | n/a | needs authoritative ESRS sources | **G** | cannot be manufactured | external | Yes |
| G0-D | production deployment (34 + 2 migrations unapplied) | 057 §7/§14.4 | **NOT AUTHORISED** | n/a | 12 untracked P8 migrations + 2 committed-but-unapplied; production never accessed in this audit | **G** | authorisation + RLS gate | PO | Yes |
| M5/G-23 | runtime & deployment introspection | 057 §14.4 | **PO-EXCLUDED** (`PX-4`) | 0 provider references in the committed X4/X5/X7 boundary (X8 §F) | `…057`, X8 §F | **E** | none (ruled out) | — | Yes (ruled) |
| Phase 9 | Phase 9 operational intelligence | 057 §7 | **Ruled out** | `b471286` baseline commit remains an unratified artefact (`domain/operational_intelligence.py` is Phase 8-X X4's own module) | 057 §7 | **E** | none | — | Yes (ruled) |
| X1 | operational health / heartbeat / queue visibility | 057 §14.4 (**UNBUILT**) | **Stale** | `domain/operational_health.py`, `data/document_processing.py` (`queue_visibility_rows`, `record_worker_heartbeat`), routes `GET /api/v3/ops/operational-health/queue\|worker` | **committed `20d27c0`**; unit + real-DB runtime suites green (X8 run 1: 83 passed; run 2: 19 passed) | **C** + **F** (057 stale) | none | Phase 8-X | Yes (closure record) |
| X2 | alerting / telemetry / retention / delivery | 057 §14.4 | Previously delivered+closed | `domain/operational_alerts.py`, `services/operational_alerting.py`, `services/retention.py`; migration `20260924000000_p8x_x2_operational_telemetry_retention.sql` **now tracked** | committed `20d27c0` (21 files, +2706) | **C** | none | Phase 8-X | Yes (closure record) |
| X3/X6 | health/liveness, thresholds/alerting | 057 §14.4 | Delivered + closed | folded into X1/X2 | 057 §14.4 | **C** | none | Phase 8-X | No |
| X4 | failures + SLA aggregation (G-20) | 057 §14.4 (**UNBUILT**) | **Stale** | `services/operational_intelligence.py`, `GET /api/v3/ops/operational-intelligence` | committed `a71a46a`; PO-CLOSED; 26 unit + 10 endpoint + 6 runtime tests green (X8) | **C** + **F** | none | Phase 8-X | No |
| X5 | operations console extension (G-25) | 057 §14.4 (**UNBUILT**) | **Stale** | `frontend/src/v3/ops/OperationalHealthTab.jsx`, `OperationsPage.jsx`, `App.js` alias, `ops/ops.css` | committed `137765f`; PO-CLOSED; 13 frontend tests green (X8) | **C** + **F** | no live-browser/a11y run (accepted at closure) | Phase 8-X | No |
| X7 | API runtime metrics (S2) | 057 §14.4 (**UNBUILT**) | **Stale** | `domain/api_metrics.py`, `data/api_metrics.py`, `services/api_metrics.py`, middleware in `api/router.py`, init in `main.py`, `GET /api/v3/ops/api-runtime-metrics` | committed `3a34ae3`; PO-CLOSED; 15 unit + 7 endpoint + 5 runtime tests green (X8) | **C** + **F** | bucket-resolution p95; activity-triggered flush (labelled, accepted) | Phase 8-X | No |
| X8 | testing/security/operational verification | 057 §14.4 (**BLOCKED**) | **Stale** | `CT-P8-P8X-X8-FINAL-VERIFICATION-20260915.md` | 83 + 19 + 13 tests green; scope-creep scan clean | **C** + **F** | none | Phase 8-X | Yes (closure record) |
| F-X8-1 | X1/X2 PO-closed but **unbanked** | X8 §G | Open at X8 | resolved by commit `20d27c0` | `git show --stat 20d27c0` | **C** | discharged | — | No |
| SB-01 | **Every unhandled 500 loses its CORS header** → users see "Network error" | `…001` | Open | `backend/main.py:398 @app.exception_handler(Exception)` is served by Starlette's `ServerErrorMiddleware`, **outside** `CORSMiddleware` (`main.py:173`) | **Reproduced empirically on this repo's FastAPI version with a standalone probe**: `/ok` 200 ACAO set · `/forbidden` 403 ACAO set · `/nope` 404 ACAO set · **`/boom` 500 ACAO = `None`**; frontend converts this to `new Error('Network error — please check your connection and try again.')` at `frontend/src/v3/api.js:56` | **A** | any 500 is mislabelled as a network failure | backend reliability | No |
| SB-02 | DB/code schema skew breaks the client workspace | `…001` | Open (was "consultant-specific") | `_SNAPSHOT_COLUMNS` gains `source_line_item_id` in the **worktree only** (`data/emissions_logs.py:57,465,497`); **absent at HEAD** (`git show HEAD:backend/data/emissions_logs.py` → no match) and **absent in `postgres`** | `information_schema.columns` → 0; therefore **HEAD is DB-consistent** and only the *uncommitted worktree* is broken | **A** + **F** (refined: not consultant-specific, and HEAD is safe) | uncommitted work must not be run against `postgres` | backend | No |
| SB-03 | `find_snapshot_by_request_id` unguarded duplicate-prevention guard | `…001` | Latent P0 | `domain/automatic_processing.py` (modified, uncommitted) | no job has reached `calculating` (`document_processing_queue`: 20 approved, 17 manual_review, 3 customer_review, **0 queued/processing**) → not yet triggered | **A** (latent) | breaks the first job that reaches calculation | backend | No |
| SB-05 | 245 clients listed but every workspace endpoint 403s | `…001` | Open | `api/consultant_auth.py:212-243` requires `client.status == 'active'`; RLS `is_org_consultant()` requires `cc.status = 'active'` | `consultant_clients`: **active 672, onboarding 244, inactive 1** → 245 listed-but-inaccessible | **A** | UX + product semantics | PO/backend | Yes |
| SB-06 | White-label gated by nothing | `…001` | Open (commercial gap) | only `require_consultant` + `ensure_consultant_permission("manage_team")`; `white_label_enabled` is read for **presentation** (`domain/branding.py`); `ConsultantPage.jsx` renders `<WhiteLabelTab/>` unconditionally | `consultant_profiles.white_label_enabled` exists; entitlement table `billing_plans.features` has no `whitelabel` key | **A** | commercial gating absent | PO/commercial | Yes |
| SB-07 | Entitlement resolves against an **empty** table | `…001` | P0 | `services/billing.py` `ensure_processing_entitlement` / `charge_processing` read `customer_subscriptions` | **`customer_subscriptions` = 0 rows** → both gates always 403 | **A** | the ratified chain through CUSTOMER APPROVAL cannot complete for any org | PO/backend | Yes |
| SB-08 | Dual subscription representation | `…001` | Open | `organizations.subscription_status/tier` populated but unread by the entitlement engine | `organizations`: active/pro **941**, active/enterprise **12**, trial/enterprise 5, trial/pro 4, NULL 13 | **A** | source-of-truth conflict | PO/backend | Yes |
| SB-09 | Batch upload hard-returns `premium_feature` | `…001` | Open | `routes/upload.py:288`; `customer_subscriptions.batch_upload_limit` is dead schema | grep | **A** | product decision | PO | Yes |
| SB-10 | PE auto-assignment has no rule model | `…001` | Open | `organizations` / `consultant_clients` have **no** PE column | schema inspection | **A** | rule model + persistence | PO | Yes |
| SB-11 | `AUDIT-TEMP Consulting Client Ltd` residue in demo data | `…001` | Open (§55 cleanup unverified) | still present | `select count(*) from organizations where name ilike '%AUDIT-TEMP%'` → **1** | **A** | demo-data hygiene | PO | Yes |
| SB-12 | Render cold start > frontend 25 s timeout; dead CORS entries | `…001` | Production reality | `frontend/src/v3/api.js:17 REQUEST_TIMEOUT_MS = 25000` unchanged | production not accessed in this audit | **G** | provider access | PO/ops | Yes |
| NEW-1 | `client_access` documented as an authorization branch but **not implemented** | this audit | n/a | `api/consultant_auth.py:9-11` documents *"firm member's `client_access` contains the org id **OR** the firm has a `consultant_clients` row"*; the implemented `ensure_consultant_org_access` (`:212-243`) requires the **active grant row** and states `client_access` "does not independently grant organisation access" | `grep client_access` → only `data/consultants.py:54,127` (round-trip) and `v3_consultants.py:951` (read-only echo); **no enforcement site** | **A** | per-member client scoping is unenforced; doc/implementation divergence | backend/docs | Yes |
| NEW-2 | Stale retention invariant test left failing by the X2 change | this audit | n/a | `tests/unit/services/test_retention.py:28` asserts `set(_ELIGIBLE_DOMAINS) == {"document_retention_days"}` | X2 (PO-closed) legitimately added `operational_telemetry_retention_days` → assertion stale. **Security invariant itself is intact** (audit/evidence still excluded) | **A** | test hygiene, not a defect | test hygiene | No |
| F-X1-2 | 2 failing unit tests (stale EF-E test double) | X8 §G `F-X8-2` | Recorded, PO-excluded | `tests/unit/api/fakes.py:285 find_by_activity` lacks `unit_qualifier_tolerant` | `TypeError: MemoryFactors.find_by_activity() got an unexpected keyword argument 'unit_qualifier_tolerant'` ×2 | **A** | test hygiene | test hygiene | No |
| F-B3-7 | Flaky assertion in closed B2 suite | 057 §14.4 | Recorded, PO-excluded | n/a | did not appear in this audit's unit run | **G** | intermittent | test hygiene | No |
| GOV-1 | Phase 8 implementation + 12 migrations **unbanked** | this audit | n/a | 12 untracked migrations; 17 untracked backend modules; S6 frontend untracked | `git ls-files --others` | **A** | commit boundary decision | PO/impl | Yes |
| GOV-2 | Nothing pushed since 2026-09-11 | `CT-GIT-…20260915` | Recorded | local `main` 19 ahead / 0 behind `origin/main` | `git rev-list --left-right --count origin/main...main` → `0 19` | **A** | PO scope decision on publishing | PO | Yes |
| GOV-3 | Concurrent implementation agent writing to the same worktree during audit | this audit | n/a | HEAD advanced `137765f → 3a34ae3 → 20d27c0` mid-audit | reflog | **F** (baseline instability) | coordinate audit vs implementation | PO/process | Yes |

---

## 5. Consultant Client architecture (current, traced)

### 5.1 Identity / data model

| Concept | Storage | Notes |
|---|---|---|
| Consultant **firm** | `consultant_profiles` (`id`, `user_id`, `company_name`, …, `white_label_enabled`, `co_branding_enabled`, `is_active`) | 55 firms |
| Consultant **firm member** | `consultant_firm_members` (`firm_id`, `user_id`, `role`, `is_active`, `client_access`, `can_manage_clients`, `can_upload_documents`, `can_generate_reports`, `can_manage_team`, **plus 6 processing flags** `can_extract`/`can_map`/`can_validate`/`can_calculate`/`can_confirm_automation`/`can_submit`) | 54 members (54 active) |
| Consultant **client** | `consultant_clients` (`consultant_id` → firm, `organization_id` → **the client *is* a normal organisation**, `status`, lifecycle fields, `relationship_origin`) | 917 rows: 672 active / 244 onboarding / 1 inactive |

**Answer to §7.1 explicitly:** a *Consultant Client* **is an organisation** with a `consultant_clients`
grant row. There is **no** separate consultant-client workspace model, no cloned organisation, and no
separate tenant — consistent with AGENTS.md §11 ("do NOT clone the organisation"). Client staff get the
ordinary customer workspace (verified previously: `client.owner.demo0001.1` → `actor_type: customer`).

### 5.2 Authorization / scope flow (server-side)

```
Supabase JWT
  → api/auth.py AuthUser (is_org_member | is_internal_staff | is_entity_staff | consultant)
  → api/consultant_auth._resolve_context()      # active consultant_profiles + active firm membership
  → ensure_consultant_org_access(user, repos, organization_id)
        repos.consultants.get_client_by_org(context.profile.id, organization_id)
        require client is not None AND client.status == 'active'
  → consultant capability gates:
        ensure_consultant_processing_authorized()   # engagement + capability + scope + D38 conflict
        ensure_consultant_review_authorized()
        ensure_consultant_submission_authorized()
  → RLS mirror: public.is_org_consultant(org)   # firm member active + consultant_clients.status='active'
```

Key properties established by tracing (not by grep alone):

* the org id is **derived server-side** from the loaded resource (`batch.organization_id` / server-derived
  job org); a caller-supplied `organization_id` that disagrees is a **DENY**, never a silent substitution;
* the firm identity comes from `resolve_consultant_firm_id()` (authoritative membership), never from the
  request;
* client switching is by URL `client_id` only for lookups — every endpoint re-resolves the grant.

### 5.3 Which API families consultants can actually reach

| API module | Consultant-aware? | Mechanism |
|---|---|---|
| `v3_consultants.py` | **Yes** (31 routes) | `require_consultant` + capability flags + per-client grant |
| `v3_processing_workflow.py` | **Yes** | `ensure_processing_org_access` + `ensure_consultant_*` capability gates |
| `v3_automatic_processing.py` | **Yes** | `ensure_processing_org_access` (3 sites) + processing gate |
| `v3_reporting.py` | **Partial** | `ensure_org_audit_access` for audit-readiness/audit-activity; `consultant-client/*` read summaries |
| `v3_exports.py` | **Partial** | only `audit-package.json` (`ensure_org_audit_access`); csv/json exports use `require_org_member` |
| `v3_messaging.py` | **Yes** | `ensure_consultant_org_access` (2 sites) |
| `v3_whitelabel.py` | **Yes** | `require_consultant` (but see SB-06: not *entitled*) |
| `v3_reports.py` | **No** | 15× `require_org_member()` + `ensure_org_access` → **consultant DENIED** |
| `v3_disclosure.py` | **No** | 15× `require_org_member()` → **consultant DENIED** |
| `v3_emissions.py` | **No** | 10× `require_org_member()` → **consultant DENIED** |
| `v3_organizations.py` | **No** | 11× | 
| `v3_billing.py` | **No** | 11× |
| `v3_documents.py` | **No** | 10× |
| `v3_manual_extraction.py` | **No** | 5× |
| `v3_vehicles.py` / `v3_suppliers.py` / facilities / assets | **No** | 4/3/… |
| `v3_verifications.py`, `issues.py`, `customer_factors.py`, `v3_search.py`, `v3_discovery.py` | **No** | — |
| `v3_settings.py` (retention control plane) | **No** | consultant cannot read/configure retention |

`ensure_org_access()` (`api/dependencies.py:150-185`) bubbles: entity staff → 403, **internal staff →
allow-all**, otherwise membership-only. Consultants are therefore denied on every
`require_org_member() + ensure_org_access()` route. Of the 29 `v3_*.py` modules, only **8** contain any
consultant-awareness.

---

## 6. Consultant Client feature-parity matrix

Legend: ✅ present · ⚠️ partial/limited · ❌ absent for consultants

| Capability | Organization | Consultant Client | Same backend path? | Same UI? | Same permissions? | Gap? |
|---|---|---|---|---|---|---|
| Document upload | ✅ `POST /api/v3/documents` | ✅ `POST /api/v3/consultants/clients/{id}/documents` | ❌ separate route, same pipeline | ⚠️ single-PDF button in client workspace | ⚠️ `can_upload_documents` | Minor (route duplication) |
| Batch upload | ❌ (hard `premium_feature` — SB-09) | ❌ | n/a | ❌ | ❌ | Same defect both sides |
| Automatic processing | ✅ | ✅ `ensure_processing_org_access` | ✅ shared domain | ⚠️ | ⚠️ `can_confirm_automation` | No |
| Extraction (AI + manual) | ✅ | ✅ scope-aware `/api/v3/processing/items/{id}/workspace` | ✅ | ⚠️ separate `ConsultantItemPage` | ⚠️ `can_extract` | No |
| Manual extraction / correction | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | No |
| Line-item handling (B2) | ✅ (QA-schema) | ❌ **0 evidence of any consultant path** | ❌ | ❌ | — | **Yes** |
| Mapping | ✅ | ✅ | ✅ | ⚠️ | ⚠️ `can_map` | No |
| Emission factors (customer factors read) | ✅ | ⚠️ only via item workspace | ❌ `/api/v3/emissions` denies | ❌ | — | **Yes** |
| Calculations | ✅ | ✅ (`calculate` in item workflow) | ✅ | ⚠️ | ⚠️ `can_calculate` | No |
| Emissions / evidence read | ✅ `v3_emissions` | ⚠️ `GET …/clients/{id}/evidence` only | ❌ different route | ⚠️ read-only table | ❌ no consultant branch in `v3_emissions` | **Yes (partial)** |
| Provenance | ✅ | ✅ evidence provenance columns | ⚠️ | ⚠️ | — | No |
| Audit trail | ✅ (owner/admin) | ✅ `ensure_org_audit_access` + `/reporting/consultant-client/{id}/audit-activity` | ✅ shared helper | ✅ audit tab | ✅ active grant | No |
| Validation / issues | ✅ | ✅ `GET …/clients/{id}/issues` | ⚠️ | ⚠️ | ⚠️ | No |
| Review | ✅ | ✅ `ensure_consultant_review_authorized` | ✅ | ✅ | ✅ | No |
| Customer approval | ✅ | ✅ `ensure_consultant_submission_authorized` / `can_submit` | ✅ | ✅ | ✅ | No |
| **Report generation** | ✅ `POST /api/v3/reports` | ❌ **403** | ❌ | ❌ | ❌ | **Yes — critical** |
| **Report types** | ✅ `GET /reports/types` | ❌ | ❌ | ❌ | ❌ | **Yes** |
| **Report list / detail** | ✅ `GET /reports`, `/reports/{id}` | ⚠️ **name+period+status row only** (`…/clients/{id}/reports`) | ❌ | ❌ no link/detail | ❌ | **Yes** |
| **Report content / download** | ✅ `/content`, `/download` | ❌ | ❌ | ❌ | ❌ | **Yes** |
| **Report PDF (white-label)** | ✅ `/reports/{id}/pdf` | ❌ | ❌ | ❌ | ❌ | **Yes — the ironclad gap** |
| **Report versions** | ✅ `/versions` | ❌ | ❌ | ❌ | ❌ | **Yes** |
| **Report lifecycle** (submit / request-changes / reject / approve / finalize) | ✅ 5 endpoints | ❌ **all 403** | ❌ | ❌ panel unreachable | ❌ | **Yes — critical** |
| **Create new version** | ✅ `POST /versions` | ❌ | ❌ | ❌ | ❌ | **Yes** |
| **Disclosure model (B1)** | ✅ `v3_disclosure.py` | ❌ 403 | ❌ | ❌ | ❌ | **Yes — critical** |
| **Disclosure narrative overlay (B4)** | ✅ | ❌ | ❌ | ❌ | ❌ | **Yes** |
| **Frozen / export artefact** | ✅ | ❌ | ❌ | ❌ | ❌ | **Yes** |
| **Intensity (B3)** | ✅ | ❌ | ❌ | ❌ | ❌ | **Yes** |
| **Finalisation** | ✅ `/finalize` | ❌ | ❌ | ❌ | ❌ | **Yes** |
| Exports — emissions csv/json, documents csv | ✅ | ❌ `require_org_member` | ❌ | ❌ | ❌ | **Yes** |
| Exports — audit package | ✅ | ✅ `ensure_org_audit_access` | ✅ | ⚠️ | ✅ | No |
| Dashboards | ✅ customer dashboard | ✅ `GET …/clients/{id}/dashboard` | ⚠️ separate | ⚠️ | ⚠️ | Minor |
| Operational views | ✅ processing page | ✅ client workspace + item page | ⚠️ | ⚠️ | ⚠️ | Minor |
| Messaging | ✅ | ✅ N1 consultant↔client | ✅ shared | ✅ | ✅ | No |
| Notifications | ✅ | ⚠️ not client-scoped for consultants | ⚠️ | ⚠️ | — | Minor |
| Master data (facilities/assets/vehicles/suppliers) | ✅ | ❌ **none** | ❌ | ❌ | ❌ | **Yes** |
| Organisation profile / member admin | ✅ | ❌ (by design — belongs to the client's own staff) | ❌ | ❌ | ❌ | Intended |
| Settings / retention control plane | ✅ (`/settings/retention`) | ❌ | ❌ | ❌ | ❌ | **Yes** |
| Billing / subscription | ✅ (but SB-07/SB-08) | ❌ | ❌ | ❌ | ❌ | **Yes** |
| White-label | n/a | ⚠️ exists, ungated (SB-06) | ✅ | ✅ | ❌ no entitlement check | **Yes** |
| Phase 8-X ops telemetry (X1/X2/X4/X7) | ❌ (internal-staff only) | ❌ | ✅ same guard | ❌ | ✅ `can_view_all` only | Intended — see §7.4 |

---

## 7. Consultant Client security / isolation assessment

### 7.1 What holds (evidence-traced, positive)

* **Cross-firm isolation is enforced server-side at two independent layers.**
  App layer: `ensure_consultant_org_access` resolves the grant through
  `get_client_by_org(context.profile.id, org)` — i.e. **the caller's own firm profile**, never a
  request-supplied firm id. RLS layer: `public.is_org_consultant(p_org)` joins
  `consultant_firm_members.user_id = auth.uid()` → `consultant_clients.consultant_id = cfm.firm_id`
  → `cc.organization_id = p_org AND cc.status='active'`. A consultant of firm B cannot satisfy the
  join for firm A's client.
* **Organisation-member bypass of the consultant rule does not exist**: a customer owner hitting a
  consultant route fails `require_consultant`.
* **PE staff are excluded from every customer/consultant path** (`is_entity_staff` → 403 early).
* **Internal staff retain the documented operational bypass** (deliberate, AGENTS.md §8/§13).
* **The URL is not the boundary**: `client_id` in the path is only a lookup key; the grant is
  re-resolved per request. A stale/incorrect `client_id` yields 403/404, not another client's data.
* **Report/evidence/audit cannot leak between clients through the consultant surface** — because the
  consultant cannot reach those endpoints at all (§6). This is *isolation by exclusion*: secure, but
  the reason parity fails.

### 7.2 Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| C-1 | **High (functional)** | Reporting + disclosure + finalisation are unreachable for consultants → a Consultant Client cannot complete the ratified chain `… → CUSTOMER APPROVAL → REPORTING` through its consultant | `v3_reports.py` 15× `require_org_member()`; `v3_disclosure.py` 15×; `ensure_org_access` internal-staff-only bypass |
| C-2 | Medium | The consultant client workspace blanks entirely if **any one** of 7 parallel calls fails (`Promise.all`) — a single 403/500 shows an empty workspace | `consultant/ConsultantPage.jsx:207-231` |
| C-3 | Medium | 245 clients (244 `onboarding` + 1 `inactive`) are **listed** in the consultant directory but every workspace call 403s; no UI explanation | `consultant_clients` status distribution; `consultant_auth.py:212-243`; `is_org_consultant()` |
| C-4 | Medium | `client_access` is documented as an authorization branch (`consultant_auth.py:9-11`) but is never enforced anywhere; per-member client scoping is therefore absent | `grep client_access` → round-trip + echo only |
| C-5 | Low | Consultant route duplication: a parallel `/consultants/clients/{id}/*` surface exists for documents/reports/evidence/dashboard/status/issues, so parity requires two implementations per capability and can drift | `api.js:464-526` vs `v3_*.py` |
| C-6 | Low | `v3_exports` mixes `ensure_org_access` (csv/json → consultant denied, `:49,69,85`) with `ensure_org_audit_access` (`:107` → consultant allowed) — inconsistent within one file | `v3_exports.py` |
| C-7 | Info | Consultant **global** observability is correctly **not** granted: X1/X2/X4/X7 all sit behind internal-staff `can_view_all`; consultants receive only client-scoped operational data | X7 endpoint tests (200 with `can_view_all`, 403 without, 403 PE, 403 customer, 401 anon) |

### 7.3 §7.5 data isolation — explicit answers

| Question | Answer | Basis |
|---|---|---|
| Consultant A can only access authorized clients? | ✅ | grant join on firm id, both layers |
| Consultant A cannot access Consultant B's clients? | ✅ | `get_client_by_org(profile.id, org)` + RLS join |
| Client A data cannot appear in Client B? | ✅ for consultant routes (each resolves one org); not proven by a live cross-client UI test | code trace |
| Reports / evidence / audit / documents / calculations / exports cannot cross clients? | ✅ by exclusion for reports/disclosure (403); documents/evidence/audit via per-client grant | code trace |
| Operational telemetry cannot expose another client's data? | ✅ | internal-staff-only guard |
| Frontend filtering used as a boundary anywhere? | ❌ no — all boundaries are server-side | code trace |

### 7.4 §7.6 client-context switching

Active client context is **explicit** in the URL/`client_id`, and **every** API call re-derives scope
server-side, so manipulating the id switches *attempt*, not *authority*. Frontend state
(`activeClientId`) does not cache another client's payload across a switch — `ClientWorkspace` reloads
all 7 datasets on `clientId` change (`ConsultantPage.jsx:234-236`). **No cross-client leak found.**

### 7.5 §7.8 Phase 8-X scoping — explicit distinction (documented here as required)

* **Global/internal staff operational intelligence** (X1 queue/worker health, X2 alerting, X4 SLA
  aggregation, X7 API runtime metrics): internal `can_view_all` staff **only**.
* **Consultant-visible client operational information**: the consultant's *client* dashboard/processing
  status/items/issues for granted clients.
* **Organisation-visible operational information**: the customer's own processing/issues/evidence.

The three tiers are **not** conflated in code. Consultants gain **no** global telemetry — correct.

---

## 8. Phase 8 current state

| Capability | State | Evidence |
|---|---|---|
| B1 disclosure model | Implemented + IV'd; **untracked**; applied to QA/clone **only** | §4 B1-1/B1-2 |
| B2 evidence line items + provenance links | Implemented + IV'd; **untracked**; not in `postgres` | `to_regclass` → NULL |
| B3 intensity catalogue + ratios | Implemented + V3 PASS; untracked | migrations 20260917* |
| B4 narrative overlay + frozen artefact | Implemented + V4 PASS; untracked | migrations 20260918*/19* |
| Requirements / applicability / values / purpose / narrative / intensity / SECR denominator | Covered by B1/B3/B4 + S1/S3/S4/S5/S7 rows | 057 §3 |
| Evidence linkage / line-item addressability / source-line linkage | Implemented (B2), **unapplied to canonical DB** | §4 |
| Report lifecycle (S6, backend) | **Committed + PO-closed**; migration unapplied anywhere reachable | `19e4f01` |
| Report lifecycle (S6, frontend) | Present but **untracked, unverified** | §4 S6-2 |
| Report templates / frozen export artefact | Implemented (B4 artefact modules, untracked) | §4 B4-1 |
| Report finalisation / immutability / version history / supersede | Backend complete (`domain/report_lifecycle.py`), server-derived `allowed_actions` | §11 |
| Historical reproducibility | Not re-verified in this audit | — |
| Legacy routes | Present, undisposed (`D-19` never ruled) | SB-09 |
| Phase 8-X aggregation / heartbeat / health / telemetry (X1/X2/X4/X5/X7) | **Committed + PO-closed + X8-verified** | §12 |
| Retention configurability | Two domains configurable, enforced server-side, audit/evidence excluded | §4 N3-n |
| Notification delivery (X2) | Implemented (`notifications.create_idempotent` + email retry + audit) | `services/operational_alerting.py` |
| Billing / usage (Phase 8 gates) | Entitlement engine present but resolves against an **empty** table (SB-07) | §4 |
| RLS | Hardened in QA/clone only; `postgres` unhardened | §13 |

**Net:** Phase 8 **build** scope is complete **in the working tree**. What is *not* true is that Phase 8
is **banked** (12 migrations + 17 modules untracked), **applied** (canonical DB has none of it),
**pushed** (nothing since 2026-09-11), or **production-ready** (G0-D unauthorised, RLS gate held).

---

## 9. P1 extraction reassessment

**Verdict: the P1 remediation contract IS implemented, but only in `shadow` mode (fail-safe), so every
customer-visible symptom in the forensic report remains.**

* Implementation: `backend/services/extraction_fidelity.py` (**untracked**) — `classify()`,
  `build_line_items()`, `split_pages()`, `ai_fanout_plan()`, `block_reason()`, `shape_mode()`,
  `PIPELINE_VERSION_P1 = "v3-auto-1.1"`, `MULTI_LINE_MIN_LINES = 2`, `PAGE_CAP = 20`.
* Wiring: `services/automatic_extraction.py:250` (PDF path) — coverage is attached in shadow mode;
  in enabled mode a multi-line-suspect document emits `line_items[]`, or is gated with
  `status: "multi_line_unresolved"` + `block_reason` (**never silently collapsed** — `P1-D2`).
* Mode: `shape_mode()` returns `shadow` unless `CARBONTALLY_P1_EXTRACTION_SHAPE` is `enabled`/`off`
  (`extraction_fidelity.py:33,101-107`).

Finding-by-finding (§9 of the task):

| Task §9 finding | Current state |
|---|---|
| multiple source lines collapsed into one record | code exists, **off by default** → **D** |
| activity vs quantity/unit from different source rows | fixed only in enabled mode → **D** |
| completeness measures produced-record fields, not source coverage | **partially corrected** — separate `coverage` block added; `confidence` semantics unchanged → **D** |
| AI rescue suppressed by completeness score | unchanged in shadow mode; enabled mode gates rather than rescues → **A** |
| positional AI/deterministic merge | fan-out plan + page cap exist; merge not re-verified → **D** |
| AI text truncation / token limits | constants present (`DEFAULT_MAX_TEXT_CHARS` mirror, `PAGE_CAP`) → partially addressed |
| missing OCR dependencies | **not verifiable here** (no runtime, no documents) → **G** |
| page-boundary loss | `split_pages()` returns an explicit `page_basis` (`marker`/`formfeed`/`document`) and states the loss instead of guessing → **D** |
| `source_page` conflation | page basis explicitly disclosed → **D** |
| `source_location` persistence gap | `domain/evidence.py:54,150,168,344` present; precision only in enabled mode → **D** |
| `mapped_data.line_items` semantic inconsistency | no unified contract found → **A** |
| silent re-extraction behaviour | not re-verified; no re-extraction guard found in the traced path → **A (unproven)** |
| CSV/XLSX header/unit issues | `_normalise_columns()` maps header→`(field, unit_hint)`; the `…020` unit-loss findings were not disproved → **D** |
| historical re-extraction policy | no policy artefact located → **A** |

**Enablement blocker (unchanged, external):** `…057` §5 requires **real non-production customer
documents**; manufacturing them is prohibited. Class **G**.

---

## 10. EF-E reassessment

**Verdict: the EF-E defect does NOT still exist. It is implemented, wired at both picker sites, and
covered by dedicated tests.**

* `data/emission_factors.py:114-160` — `find_by_activity(..., unit_qualifier_tolerant: bool = False)`
  (`:123`), with the PO `D-B` **T2** semantics documented at `:131`; the strict path (`:151`) and the
  tolerant path (`:153`) are distinct.
* Both mapping *picker* sites use it: `api/v3_processing_workflow.py:1117` and
  `api/v3_emissions.py:558` (`unit_qualifier_tolerant=True`).
* Dedicated evidence: `tests/unit/data/test_emission_factors_unit_selection.py` (4 tests, incl. the
  tolerant comparison and a "no kwargs / `unit_substring` / tolerant" triple), and
  `tests/unit/services/test_efe_selection_sites.py` which **asserts the call sites pass the flag** —
  these pass.
* Caveat: the flag is **uncommitted** (`data/emission_factors.py` and `core/units.py` are worktree-modified),
  so the improvement is not in `HEAD`. Two *pre-existing* regression tests
  (`test_v3_phase_c_regressions.py`) still fail because the test double `tests/unit/api/fakes.py:285`
  was not updated (`F-X1-2`/`F-X8-2`, PO-excluded) — **test hygiene, not an EF-E defect**.

---

## 11. S6 / report-lifecycle reassessment

| Property | State | Evidence |
|---|---|---|
| States | `DRAFT, REVIEWED, CHANGES_REQUESTED, REJECTED, APPROVED, FINAL` | `domain/report_lifecycle.py:32-37` |
| Transitions | `submit_review`, `request_changes`, `reject`, `approve`, `finalize`, `new_version` with explicit T-numbers | `:61-66` |
| submit / request-changes / reject / approve / finalize | 5 endpoints, committed | `v3_reports.py:775,794,813,832,857` |
| new-version / supersede | `POST /versions` guarded by `can_create_new_version(source["status"])` | `v3_reports.py:882-910` |
| Immutability | `is_immutable(state)` + `is_terminal(state)` | `:181-190` |
| Version history | `GET /{report_id}/versions`, each row carries `allowed_actions` for its **persisted** status | `v3_reports.py:392-415` |
| **Server-derived allowed actions** | ✅ `allowed_actions(version["status"])` — the UI never invents rules | `:400,415,688` |
| Authority model | `AUTHORITY_MEMBER` / `AUTHORITY_ADMIN`; `required_authority(action)` | `:101-105,191` |
| UI lifecycle panel | Present, reads `allowed_actions`, renders only performable actions, handles 403/409 gracefully | `ReportLifecyclePanel.jsx:54-120`, mounted `ReportDetailPage.jsx:234`; **untracked** |
| `new_version` exposure (`S6-ACTION-1`) | **Still not offered as an action** — deliberately surfaced as *guidance* | `ReportLifecyclePanel.jsx:71-77` |

**Conclusion:** the previously deferred `new_version` exposure **remains unexposed, by ratified ruling**
(`…057` §14.4: a future, separately bounded increment; its absence is **not** a defect). Class **E**.
The *only* genuine S6 gap is that the frontend panel is unbanked/unverified and the S6 migration is
applied nowhere reachable.

---

## 12. Phase 8-X reassessment (X1–X8)

| Stage | 057 §14.4 (2026-09-14) | **Current (2026-09-15)** | Evidence | Class |
|---|---|---|---|---|
| X1 operational health / heartbeat / queue visibility | UNBUILT | **Implemented, committed, PO-closed, X8-verified** | `20d27c0`; `domain/operational_health.py`; routes `/ops/operational-health/queue\|worker` | C |
| X2 alerting / telemetry / retention / delivery | delivered earlier | **Committed** (+ migration now tracked) | `20d27c0` (21 files, +2706); `20260924000000_…sql` tracked | C |
| X3 health/liveness | delivered + closed | unchanged | 057 §14.4 | C |
| X4 failures + SLA aggregation | UNBUILT | **Implemented + committed + PO-closed + verified** | `a71a46a`; `services/operational_intelligence.py`; `GET /ops/operational-intelligence` | C |
| X5 operations console extension | UNBUILT | **Implemented + committed + PO-closed + verified** | `137765f`; `ops/OperationalHealthTab.jsx` | C |
| X6 thresholds/alerting | delivered + closed | unchanged | 057 §14.4 | C |
| X7 API runtime metrics | UNBUILT | **Implemented + committed + PO-closed + verified** | `3a34ae3`; `domain|data|services/api_metrics.py`; middleware `api/router.py`; `GET /ops/api-runtime-metrics` | C |
| X8 verification | BLOCKED | **Executed** — `PHASE 8-X VERIFIED WITH NON-BLOCKING LIMITATIONS` | `CT-P8-P8X-X8-FINAL-VERIFICATION-20260915.md` (83 + 19 + 13 tests green) | C |
| `F-X8-1` (X1/X2 unbanked) | Medium | **DISCHARGED** by `20d27c0` | reflog | C |
| M5 / G-23 runtime & deployment introspection | PO-EXCLUDED | still excluded (0 provider references) | X8 §F | E |

§12 sub-questions answered:

* aggregation exists → ✅ X4 (`operational_intelligence.py`, read-time composition).
* failures/SLA aggregation → ✅ X4 (flag-only SLA by design; `truncated`/`read_limit` honesty fields).
* operational alerting → ✅ X2 (`operational_alerts.py`, thresholds 100/900 s/3600 s cooldown, 3-attempt
  delivery, `notifications.create_idempotent` dedup, internal-only recipients).
* worker heartbeat → ✅ X1 (`record_worker_heartbeat`, single-row).
* health path tests the correct pool → ✅ X1 (repository-level `document_processing.py` visibility +
  `/health` pool check at `main.py:340-348`).
* operations console surfaces current info → ✅ X5 (read-only tab + route alias).
* runtime/deployment introspection → ❌ **PO-excluded** (`PX-4` declined) — correctly absent.
* retention configurable → ✅ two domains, server-side, audit/evidence excluded.
* operational telemetry correctly scoped → ✅ internal `can_view_all` only.

---

## 13. RLS / security reassessment (no remediation performed)

| Aspect | `postgres` (canonical) | QA / clone DBs | Production |
|---|---|---|---|
| RLS-enabled tables | 116 | (same schema + P8) | **unverified** |
| Policies | 174 | — | **unverified** |
| `anon` table grants | **455** (incl. 116 `TRUNCATE`) | **4** (1 `TRUNCATE`) | **unverified** |
| `authenticated` `TRUNCATE/REFERENCES/TRIGGER` | **345** | **0** | **unverified** |
| `service_role` | 808 grants (116 `TRUNCATE`) — expected | 133 `TRUNCATE` | **unverified** |
| RLS-4A-1 (anon containment) | ❌ not applied | ✅ applied | ❌ / unknown |
| RLS-4A-1b (default privileges) | ❌ | ✅ | ❌ / unknown |
| RLS-4A-2 (authenticated hardening) | ❌ | ✅ | ❌ / unknown |
| RLS steps 3–5 | gate **HELD** | — | — |

* The consultant RLS helper `public.is_org_consultant(uuid)` is present and mirrors the app-layer rule
  (firm member active + `consultant_clients.status='active'`). **The recorded production baseline
  (97/104 tables RLS-disabled, `anon` `GRANT ALL`) could not be re-measured** because production is not
  accessible/authorised → class **G**.
* **Feature correctness ≠ production security readiness.** The feature layer is correctly authorised
  server-side; the *privilege* layer in the canonical and production databases is not yet hardened.

---

## 14. Verification status (implemented vs verified vs applied vs production)

| State | What currently qualifies |
|---|---|
| **Implemented in repository** | All Phase 8 (B1–B4, S1–S7) in the **worktree**; S6 backend **committed**; all Phase 8-X (X1, X2, X4, X5, X7) **committed**; P1 (shadow mode); EF-E (worktree) |
| **Independently verified** | Phase 8 B1–B4/S1–S7 (per 057 + stage IV reports); S6 backend (057 `…063` §12); EF-E (054 + dedicated suites); RLS-4A-1/4A-1b/4A-2 (QA scope); X1/X2/X4/X5/X7/X8 (X8 re-verification) |
| **Migration exists** | 15 Phase 8/8-X migrations (12 untracked, 3 tracked: S6 lifecycle, X2 retention, plus earlier P7/P6) |
| **Migration applied to canonical `postgres`** | **NONE of the Phase 8 set.** Newest applied = `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` |
| **Migration applied to QA/clone** | B1–B4, S2, RLS-4A-1/1b/2 ✅ (by out-of-band psql; `supabase_migrations.schema_migrations` empty there) |
| **Applied to production** | **NO** (unauthorised; unverified) |
| **Production/runtime verified** | **NO** — production never accessed |

### 14.1 Test inventory and execution status (this audit)

* **Backend unit:** `backend/.venv/bin/python -m pytest tests/unit` → **2,278 items collected** across
  151 files; **exactly 3 FAILED**:
  1. `tests/unit/api/test_v3_phase_c_regressions.py::TestCl44MappingOptionsCustomerFactors::test_spend_activity_returns_actionable_suggestion`
     — `TypeError: MemoryFactors.find_by_activity() got an unexpected keyword argument 'unit_qualifier_tolerant'` (stale double, `F-X1-2`, PO-excluded).
  2. `…::test_unrelated_customer_factor_does_not_mask_spend_dead_end` — same cause.
  3. `tests/unit/services/test_retention.py::test_audit_and_evidence_domains_are_excluded_from_enforcement`
     — stale assertion `set(_ELIGIBLE_DOMAINS) == {"document_retention_days"}` invalidated by the PO-closed
     X2 addition of `operational_telemetry_retention_days` (**NEW-2**; the security invariant itself is intact).
  * Earlier failures in this session caused by a wrong interpreter (no `pytest-asyncio`, no `asyncpg`) are
    **not** code defects; `backend/.venv` is the correct interpreter (Python 3.14.4, `asyncpg 0.30.0`,
    `pytest-asyncio 1.4.0`).
* **Backend integration:** not re-run in full; the X8 run executed 19 real-DB runtime tests against the
  disposable clone `ct_x7_20260915` (all green). The destructive-setup guard **`F-046-1`** in
  `tests/integration/conftest.py` correctly refuses `qa`/`demo`/`investor`/`prod` targets — **no
  persistent database was truncated during this audit** (no integration suite was run against
  `postgres`).
* **Frontend:** 26 suites passed / 1 failed; 277 tests passed. `src/App.test.js` fails with
  `Cannot find module 'react-router/dom' from 'node_modules/react-router-dom/dist/index.js'` —
  a dependency-resolution problem in this environment, **not** evidence about the audited requirements.
  (recorded, not fixed)
* **X suites (from X8):** 83 unit + 19 real-DB + 13 frontend — all green.
* **Not executed:** any production check, any live-browser/a11y run, any OCR pipeline run, any
  end-to-end report/disclosure flow against a provisioned database.

---

## 15. Remaining gaps (only those that survive current-code reconciliation)

1. **Consultant Client reporting/disclosure parity (C-1)** — the only *product-scope* parity gap.
2. **Canonical/QA/repository state skew** — Phase 8 code + 12 migrations untracked; no Phase 8 migration
   applied to `postgres`; HEAD and the canonical DB are consistent, the *worktree* is not.
3. **Unbanked work + unpushed history** — 923 untracked files, 236 tracked modifications, 19 local-only commits.
4. **SB-07 / SB-08 entitlement dead-end** — `customer_subscriptions` empty (0). No org can pass the
   Customer Approval billing gate.
5. **SB-01 500-without-CORS** — every unhandled server error is user-visible as a bogus "Network error".
6. **SB-05 245 inaccessible-but-listed clients**; **SB-06 ungated white-label**; **SB-09 premium_feature
   batch upload**; **SB-10 no PE assignment rule model**; **SB-11 demo residue**.
7. **SB-03 latent duplicate-guard failure** — will fire the first time a job reaches `calculating`.
8. **NEW-1 `client_access` unenforced** (doc/implementation divergence).
9. **Test hygiene** — 2 stale-double failures (`F-X1-2`) + 1 stale-assertion failure (NEW-2).
10. **P1 enablement** — shadow-only; all customer-visible extraction symptoms persist.
11. **RLS steps 3–5 held**; RLS-4A-* applied to QA/clone only.
12. **Production** — G0-D unauthorised; migration + runtime + security state unverified.

---

## 16. New PO decisions required

| # | Decision | Why it cannot be an agent call |
|---|---|---|
| P-1 | **Consultant Client reporting/disclosure parity** — do Consultant Clients get the Phase 8 report + disclosure surface (via a consultant-scoped route family, or by making report routes consultant-aware under an active grant)? | Changes who may author/finalise regulated reporting output |
| P-2 | **Phase 8 banking boundary** — commit the 12 migrations + 17 untracked modules (and the S6 panel) as one boundary, or per-workstream? | Publishing an incomplete Phase 8 with four Phase 8-X layers on top is a scope decision |
| P-3 | **Push / publication** — `main` is 19 ahead / 0 behind; nothing pushed since 2026-09-11 | Outward-facing act |
| P-4 | **Canonical/QA database target** (`D-PO-8`) — name the non-production persistent environment that should hold B1/B2 (a skip is not a PASS) | Names an environment |
| P-5 | **RLS-4A-2 closure record** (`D-PO-1`) — implementation + IV exist; the register still says NOT AUTHORISED/NOT IMPLEMENTED | Closure is a PO act |
| P-6 | **RLS steps 3–5 rulings** (`D-PO-3`: `D-4…D-10`, `D-12`) — gate still held | Security posture |
| P-7 | **Entitlement source of truth** (SB-07/SB-08) — populate `customer_subscriptions`, or make `organizations.subscription_*` authoritative | Commercial policy |
| P-8 | **Batch upload gating** (SB-09 / `whitelabel`+`batch_upload` absent from `billing_plans.features`) | Commercial policy |
| P-9 | **Non-active client semantics** (SB-05) — hide, explain, or make `onboarding` operational | Product UX |
| P-10 | **PE assignment rule model** (SB-10) | Operational policy |
| P-11 | **`…028` B2 closure record** (`D-PO-2`), **I1** (`D-PO-5`), **S8** (`D-PO-9`), **B4-D12/D16/N3** (`D-PO-10`) | Pre-existing open PO items — unchanged |
| P-12 | **Phase 8-X closure declaration** — X8 verdict is "READY FOR PO CLOSURE"; `F-X8-1` is now discharged | Closure is a PO act |
| P-13 | **Concurrent-writer policy** — an implementation agent and an audit agent are using one worktree | Process/governance |

---

## 17. Recommended workstream ordering (NOT an authorisation)

Dependency-aware only; **nothing here is authorised by this report**.

1. **Freeze / synchronise the repository** — stop concurrent writes; record a single HEAD; decide the
   Phase 8 banking boundary (P-2). *Everything else is unsafe while HEAD moves mid-audit.*
2. **Decide Consultant Client parity** (P-1) — the largest genuine product gap; it gates any
   "consultant can complete reporting" claim.
3. **Provision the named non-production target** (P-4) and apply B1/B2 there, so runtime suites stop
   SKIPping; then re-run the S6/B1/B2/S6-frontend integration suites.
4. **Independent verification of the S6 frontend panel** (§4 S6-2) and of the unbanked Phase 8 modules.
5. **Decide the entitlement source of truth** (P-7) — it currently blocks the ratified chain end-to-end.
6. **Fix SB-01** (500 CORS) — cheap, high leverage: it converts every server error into a misdiagnosis.
7. **Retire the test-hygiene debt** (`F-X1-2`, NEW-2) so the suite is green and trustworthy.
8. **P1 enablement** once real non-production documents exist (external gate).
9. **RLS closure** (P-5/P-6) — required before any production readiness statement.
10. **Production readiness assessment** — only after 3 + 9.

---

## 18. Explicit exclusions (must remain out of scope)

* Phase 9 — ruled out by the PO (`…040`); `b471286` stays an unratified artefact.
* M5 / G-23 runtime & deployment introspection — PO-excluded (`PX-4`).
* S6 `new_version` *exposure* (`S6-ACTION-1`) — future bounded increment; **do not reopen**.
* D16 legacy disposition, S8 AI narrative, Insight I1, `F-4A1B-1`, B4-D12, N3 remaining retention
  domains — pre-existing held/deferred items; no new work without a PO ruling.
* RLS steps 3–5 — gate held; cannot be reopened by Phase 8/8-X completion.
* Production — any access, migration, deployment or configuration.
* Demo/investor dataset — no reset, truncate, reseed, or credential change. This audit issued
  read-only `SELECT`s only.
* The 2 stale-double unit failures and the `react-router/dom` frontend resolver failure — recorded, not
  fixed (outside authorisation; unrelated to the audited requirements).
* Any migration application, RLS change, or commit/push.

---

## 19. Final verdict

### `AUDIT COMPLETE — MATERIAL GAPS REMAIN`

Rationale: Consultant Client **reporting/disclosure parity does not hold** (§6, C-1); Phase 8 is
implemented but **unbanked and unapplied** in the canonical database (§2.1, §8); the entitlement chain
is dead-ended by an empty subscription table (§4 SB-07); every unhandled 500 surfaces to users as a
bogus network error (§4 SB-01, empirically reproduced); and RLS hardening exists only in QA/clone
databases. Phase 8-X, by contrast, is genuinely complete, committed, PO-closed and independently
verified (X1–X8), and EF-E and S6-backend reconcile as implemented + verified.

**Production readiness is neither claimed nor implied anywhere in this report.**

---

# WHAT WE SHOULD DO NEXT

### Already complete — do not touch
* **Phase 8-X X1, X2, X3, X4, X5, X6, X7, X8** — committed, PO-closed, X8-verified (`a71a46a`, `137765f`, `3a34ae3`, `20d27c0`). `F-X8-1` is discharged.
* **Phase 8 B1, B2, B3, B4, S1–S7** — implemented and independently verified (per 057 + stage IV reports).
* **S6 report lifecycle, backend** — committed, PO-closed (`19e4f01`).
* **P2 EF-E** — implemented, wired at both picker sites, dedicated tests green.
* **Phase 9** — ruled out. **M5/G-23** — PO-excluded. **S6 `new_version`** — ruled a future increment.

### Still missing — needs implementation
* **Consultant Client reporting/disclosure parity** (P-1): reports (list/detail/content/versions/download/PDF), report lifecycle actions, disclosure model, narrative, intensity, frozen artefact, finalisation.
* **SB-01** — make unhandled 500s carry the CORS header (or handle them inside the CORS layer).
* **SB-07 / SB-08** — align entitlement with a populated authoritative subscription source.
* **NEW-1** — either enforce `client_access` or correct the documented authorization contract.
* **SB-03** — guard `find_snapshot_by_request_id` before a job reaches `calculating`.
* **SB-05 / SB-09 / SB-10** — client-status semantics, batch-upload gating, PE assignment rule model.
* **SB-11** — verify/close the `AUDIT-TEMP` demo-data cleanup per §55.

### Implemented but needs independent verification
* **S6 frontend lifecycle panel** (+ its test file) — present, untracked, unverified.
* **All unbanked Phase 8 modules** — re-verify against a provisioned non-production database (not a clone-only pass).
* **SB-02 worktree change** — `source_line_item_id` must either be migrated into the canonical DB or kept out of any run against it.

### Requires PO decision
* P-1 parity scope · P-2 banking boundary · P-3 push/publication · P-4 named non-production target ·
  P-5 RLS-4A-2 closure record · P-6 RLS steps 3–5 · P-7 entitlement source of truth · P-8 batch-upload
  gating · P-9 non-active client semantics · P-10 PE assignment policy · P-11 (`…028`, I1, S8, B4-D12,
  D16, N3) · P-12 Phase 8-X closure declaration · P-13 concurrent-writer policy.

### Blocked by external evidence / environment
* **P1 enablement** (real non-production customer documents).
* **`…048` ESRS sources**; **EF-A / EF-D** (real factor catalogue behind the production boundary).
* **Production state** — migration, runtime, RLS and provider behaviour (Render cold start, CORS origins).
* **OCR dependency proof** — requires a runtime and real documents.

### Consultant Client parity gaps
* No client-scoped **report generation, report detail/versions, lifecycle actions, content/download, white-label PDF**.
* No **disclosure model, narrative, intensity, frozen artefact or finalisation** access for clients.
* No client-scoped **emissions API**, **emissions/documents exports**, **master data**, **billing** or **settings**.
* 245 clients are listed but unusable; `client_access` per-member scoping is unenforced.
* *What already holds:* upload → processing → extraction → mapping → validation → calculation →
  customer review → evidence → audit package → messaging → audit trail, all with server-side
  cross-firm isolation verified at both the app and RLS layers.

### Explicitly deferred / do not reopen
* S6 `new_version` exposure · Phase 9 · M5/G-23 · RLS steps 3–5 (held) · D16 legacy · S8 ·
  Insight I1 · `F-4A1B-1` · B4-D12 · N3 remaining retention domains · production deployment (G0-D) ·
  the investor-demo dataset (§55).

> **End of report.** No implementation code, prompt or patch was produced. No commit, no push. No
> database, migration, RLS, configuration or application file was modified. All database interaction in
> this audit was read-only, and no integration suite was run against any persistent database.
