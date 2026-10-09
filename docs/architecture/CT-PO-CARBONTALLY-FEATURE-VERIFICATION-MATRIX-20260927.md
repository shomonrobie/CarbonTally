# CT-FEATURE-02 — FEATURE VERIFICATION MATRIX & DOMAIN METRICS

**Task ID:** `CT-FEATURE-02-20260927-INDEPENDENT-VERIFICATION-…`
**Type:** READ-ONLY verification output.
**Companion documents:** `CT-PO-CARBONTALLY-FEATURE-CATALOGUE-INDEPENDENT-VERIFICATION-20260927.md` (primary), `CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md` (FIEW register).
**Authority:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`, branch `p8-release-reconciled`.

---

## §1 Method

- Catalogue parsed mechanically: `354` rows, `354` unique contiguous IDs, all 7-field well-formed.
- `COSTRICT_STATUS` assigned by the downgrade rule (unapplied-migration or clone-only persistence ⇒ not durably wired), plus manual inspection of every high-risk cluster.
- Domain metrics computed from the catalogue's own domain ranges.
- `CONFIDENCE`: High = object independently confirmed `ABSENT` in the flagship and named in the map of the 43 unapplied migrations; Med = base feature works but a named hardening/governance migration is unapplied.

## §2 Master reclassification matrix (high-risk / schema / config / security / processing / reporting / Admin / consultant / P17 / P16R / commercial / Insight)

Full per-row detail is in the FIEW register. Summary of the 57 downgrades:

| FTR_ID | FEATURE | DOMAIN | CLINE_STATUS | COSTRICT_STATUS | CONF | WHY | REQUIRED_CORRECTION |
|---|---|---|---|---|---|---|---|
| FTR-036 | Anon/public grant containment | D03 Security | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA (partial) | High | p8_rls_* (20260920-23) unapplied | token → IN_CODE_BLOCKED_BY_SCHEMA |
| FTR-044 | Org type & consolidation | D04 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a unapplied; cols ABSENT | token → blocked |
| FTR-076 | Acting-for attribution | D09 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a unapplied; cols ABSENT | token → blocked |
| FTR-085 | Facility accounting dimension | D11 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a unapplied | token → blocked |
| FTR-111 | Activity clarifications | D15 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | table ABSENT (verified) | token → blocked |
| FTR-127 | Evidence line items | D18 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | table ABSENT (verified) | token → blocked |
| FTR-128 | Provenance line links | D18 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | p8_b2 links unapplied | token → blocked |
| FTR-130 | Evidence idempotency/correction | D18 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | Med-High | p8_b1 20260915 unapplied | token → blocked |
| FTR-135 | Data-quality dimension | D19 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a unapplied | token → blocked |
| FTR-142 | emission_factors containment | D20 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | p8_d4 20260926 unapplied | token → blocked |
| FTR-144 | Factor governance attrs | D21 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a unapplied | token → blocked |
| FTR-146 | Provider ownership/updates | D21 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA (partial) | Med | containment 20260926 unapplied | token → partial |
| FTR-147 | Governed capability statement | D21 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | disclosure_requirement_versions ABSENT (verified) | token → blocked |
| FTR-149 | Scope 1 energy-type dim | D22 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a unapplied | token → blocked |
| FTR-153 | Location-based enforcement | D23 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a unapplied | token → blocked |
| FTR-157 | Contractual instrument repo | D25 | IMPLEMENTED_AND_WIRED (repo) | DISPOSABLE_ENVIRONMENT_ONLY | High | p17c unapplied; table ABSENT | token → disposable |
| FTR-158 | Instrument allocations | D25 | IMPLEMENTED_AND_WIRED (repo) | DISPOSABLE_ENVIRONMENT_ONLY | High | p17c unapplied | token → disposable |
| FTR-161 | Instrument allocation | D26 | IMPLEMENTED_AND_WIRED (repo) | DISPOSABLE_ENVIRONMENT_ONLY | High | p17c unapplied | token → disposable |
| FTR-164 | Scope 3 category taxonomy | D27 | IMPLEMENTED_AND_WIRED (repo) | DISPOSABLE_ENVIRONMENT_ONLY | High | p17d unapplied; table ABSENT | token → disposable |
| FTR-167 | Scope 3 category dimensions | D27 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a/p17_10 unapplied | token → blocked |
| FTR-169 | Scope 3 estimation | D27 | IMPLEMENTED_AND_WIRED (repo) | DISPOSABLE_ENVIRONMENT_ONLY | High | p17h unapplied | token → disposable |
| FTR-170 | Accounting-dimension columns | D28 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a unapplied | token → blocked |
| FTR-173 | Consolidation/org-type context | D28 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17a unapplied | token → blocked |
| FTR-174 | Product-contract reporting dims | D28 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p17_10 unapplied | token → blocked |
| FTR-175 | Estimation records | D29 | IMPLEMENTED_AND_WIRED (repo) | DISPOSABLE_ENVIRONMENT_ONLY | High | p17h unapplied | token → disposable |
| FTR-178 | Disclosure narrative integration | D29 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | p8_b4 20260918 unapplied | token → blocked |
| FTR-181 | Calculation idempotency | D30 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p16r7 unapplied | token → blocked |
| FTR-182 | Result reportability lifecycle | D30 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | p16r5 unapplied | token → blocked |
| FTR-184 | Gate 4 actor attribution | D30 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20260905 unapplied | token → blocked |
| FTR-185 | Gate 5 automation provenance | D30 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20260905* unapplied | token → blocked |
| FTR-186 | Gate 6 extracted output | D30 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20260906 unapplied | token → blocked |
| FTR-193 | Manual-processing governance | D31 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | table ABSENT (verified) | token → blocked |
| FTR-211 | Report lifecycle status | D34 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA (partial) | High | 20260913 unapplied | token → partial |
| FTR-219 | Intensity catalogue | D34 | IMPLEMENTED_AND_WIRED | DISPOSABLE_ENVIRONMENT_ONLY | High | 20260917 unapplied | token → disposable |
| FTR-220 | Frozen report artefact | D34 | IMPLEMENTED_AND_WIRED | DISPOSABLE_ENVIRONMENT_ONLY | High | table ABSENT (verified) | token → disposable |
| FTR-223 | report_versions is_current | D35 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20260921 unapplied | token → blocked |
| FTR-224 | Version artefacts | D35 | IMPLEMENTED_AND_WIRED | DISPOSABLE_ENVIRONMENT_ONLY | High | table ABSENT (verified) | token → disposable |
| FTR-226 | Disclosure model foundation | D36 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20260914 unapplied | token → blocked |
| FTR-227 | Governed requirement rows | D36 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | table ABSENT (verified) | token → blocked |
| FTR-228 | Disclosure values/evidence | D36 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20260914/15 unapplied | token → blocked |
| FTR-229 | Disclosure narrative overlay | D36 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20260918 unapplied | token → blocked |
| FTR-230 | Disclosure projection engine | D36 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | depends disclosure tables | token → blocked |
| FTR-231 | Disclosure purposes/binding | D36 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20260914 unapplied | token → blocked |
| FTR-232 | Applicability assessments | D36 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20260914 unapplied | token → blocked |
| FTR-233 | Disclosure finalisation | D36 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | depends disclosure tables | token → blocked |
| FTR-234 | Insight L1 persistence | D37 | IMPLEMENTED_AND_WIRED (repo) | BLOCKED_BY_SCHEMA | High | tables ABSENT (verified) | token → blocked |
| FTR-235 | Insight L1 authorization | D37 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20261002 unapplied | token → blocked |
| FTR-236 | Insight tools | D37 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | Med-High | depends Insight | token → blocked |
| FTR-237 | Insight L2 interactions | D37 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20261003 unapplied | token → blocked |
| FTR-238 | Insight planner/rate-limit | D37 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20261005 unapplied | token → blocked |
| FTR-239 | Insight temporal comparison | D37 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20261006 unapplied | token → blocked |
| FTR-240 | Insight data-quality/repro | D37 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | 20261007 unapplied | token → blocked |
| FTR-241 | Insight customer UI | D37 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA | High | backend ABSENT | token → blocked |
| FTR-306 | RLS hardening suite | D46 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA (partial) | High | p8_rls_* unapplied | token → partial |
| FTR-327 | Entitlement RLS gating | D49 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA (partial) | Med | 20260925 unapplied | token → partial |
| FTR-331 | Governed capability catalogue | D50 | IMPLEMENTED_AND_WIRED | DOCUMENTED_ONLY | High | reference data; no object; unapplied | token → documented |
| FTR-334 | Plan→capability entitlement | D50 | IMPLEMENTED_AND_WIRED | BLOCKED_BY_SCHEMA (partial) | Med | 20260925 unapplied | token → partial |

**Secondary (lower-confidence) reclassifications** (not counted in the 57) are listed in the FIEW register §9 (`FTR-124/129/191/200/204/251/323/056/067/194`).

## §3 Capability join verification

### §3.1 Cross-deliverable contradictions (D1 residual register §7.2 vs D3 join §3)

8 of the 11 capabilities present in **both** disagree on the mapped FTR set:

| CAP_ID | FEATURE_ID (D1 catalogue) | D3 mapping | Independent | Status | Reason |
|---|---|---|---|---|---|
| CAP-005 | Cookie consent banner | FTR-342 | FTR-344 | DISPUTED | D1 says 342, D3 says 344 |
| CAP-070 | Seven governed capability values | FTR-330,331 | FTR-335 | DISPUTED | disjoint mappings |
| CAP-074 | Actor/automation/write-once gates | FTR-202…210 | FTR-206,207 | DISPUTED | D1 = audit cluster, D3 = 2 rows |
| CAP-091 | Legacy reporting & generator | FTR-211…222 | FTR-219…222,351 | DISPUTED | different ranges + historical row |
| CAP-133 | Build provenance | FTR-350 | FTR-347 | DISPUTED | different feature |
| CAP-145 | Prisma schema lineage | FTR-353 | FTR-352 | DISPUTED | different feature |
| CAP-150 | Legacy API surface & dual mount | FTR-273…280 | FTR-273,354 | DISPUTED | different ranges |
| CAP-151 | Dual ASGI entrypoints | FTR-273…280 | FTR-346,280 | DISPUTED | different features |

### §3.2 Capabilities joined to inappropriate features (zero lexical overlap, 43 rows)

Independent check: the capability name shares **no** significant token with any referenced feature name. Demonstrative cases (the remainder are public-website / broad-name false alarms):

| CAP_ID | CAPABILITY | D3 FTR | Actual feature(s) referenced | Status | Reason |
|---|---|---|---|---|---|
| CAP-013 | Beta access programme | FTR-010…014 | GA4 / bulk ops / import mgmt / provider admin / glossary | DISPUTED | Beta is FTR-019 |
| CAP-015 | Google OAuth | FTR-024 | Password reset | DISPUTED | OAuth is FTR-022 |
| CAP-016 | Magic-link auth | FTR-021 | Email+password | DISPUTED | magic-link is FTR-023 |
| CAP-017 | TOTP MFA | FTR-023,302 | magic-link / system-admin role | DISPUTED | MFA is FTR-025 |
| CAP-018 | Password reset | FTR-022,025 | Google OAuth / MFA | DISPUTED | reset is FTR-024 |
| CAP-020 | Customer roles | FTR-054…056 | staff / PE / consultant role models | DISPUTED | customer roles = FTR-053 |
| CAP-047 | Factor matching engine | FTR-136…139 | DEFRA / SEAI / aliases / customer factors | DISPUTED | engine = FTR-112 |
| CAP-049 | DEFRA provider | FTR-141 | factor import batches | DISPUTED | DEFRA = FTR-136 |
| CAP-051 | Customer custom factors | FTR-143,147 | EF-E refinement / governed statement | DISPUTED | factors = FTR-139/140 |
| CAP-058 | Calculation idempotency | FTR-184,185 | actor attribution / automation provenance | DISPUTED | idempotency = FTR-181 |
| CAP-100 | Realtime subscriptions | FTR-270,271 | LLM runtime / webhook settings | DISPUTED | realtime = FTR-261 |
| CAP-104 | Consultant workspace | FTR-064…066 | onboarding / engagement / lifecycle | DISPUTED | workspace = FTR-060 |
| CAP-124 | Search & discovery | FTR-244…248 | dashboards / benchmarking | DISPUTED | search = FTR-047 |
| CAP-146 | D19 workbench | FTR-123,124 | QC queue / quality chain | DISPUTED | workbench = FTR-120 |

**Verdict:** `152/152` is a correct **row count** but an inaccurate **mapping**; the join must be regenerated or ratified before use as an index (new decision **POD-P**).

## §4 Domain-level metrics

`conf = I&W − downgraded` (durably-wired estimate). Domains with I&W ≥ 9 or ≥ 1 downgrade shown; the remainder have 0 downgrades.

| Dom | Domain | rows | I&W | downgraded | confirmed | false rate |
|---:|---|---:|---:|---:|---:|---:|
| 01 | Platform Admin | 20 | 19 | 0 | 19 | 0% |
| 03 | Authorization | 7 | 7 | 1 | 6 | 14% |
| 04 | Organizations | 11 | 10 | 1 | 9 | 10% |
| 07 | Consultant Mgmt | 10 | 9 | 0 | 9 | 0% |
| 09 | Acting-For | 3 | 2 | 1 | 1 | 50% |
| 11 | Facilities & Locations | 3 | 2 | 1 | 1 | 50% |
| 14 | Documents | 10 | 10 | 0 | 10 | 0% |
| 15 | Extraction | 10 | 8 | 1 | 7 | 12% |
| 18 | Evidence | 5 | 5 | 3 | 2 | **60%** |
| 19 | Data Quality | 5 | 5 | 1 | 4 | 20% |
| 20 | Emission Factors | 8 | 7 | 1 | 6 | 14% |
| 21 | Factor Governance | 4 | 4 | 3 | 1 | **75%** |
| 22 | Scope 1 | 3 | 2 | 1 | 1 | 50% |
| 23 | Scope 2 LB | 3 | 3 | 1 | 2 | 33% |
| 25 | Contractual Instruments | 4 | 3 | 2 | 1 | 67% |
| 26 | Allocations | 3 | 1 | 1 | 0 | **100%** |
| 27 | Scope 3 | 6 | 6 | 3 | 3 | 50% |
| 28 | Accounting Dimensions | 5 | 5 | 3 | 2 | 60% |
| 29 | Estimation | 4 | 3 | 2 | 1 | 67% |
| 30 | Calculations | 9 | 9 | 5 | 4 | **56%** |
| 31 | Workflow & Jobs | 9 | 9 | 1 | 8 | 11% |
| 34 | Reporting | 12 | 11 | 3 | 8 | 27% |
| 35 | Report Versions | 3 | 2 | 2 | 0 | **100%** |
| 36 | Disclosures | 8 | 8 | 8 | 0 | **100%** |
| 37 | Insight | 9 | 9 | 8 | 1 | **89%** |
| 44 | Operations | 9 | 9 | 0 | 9 | 0% |
| 46 | Security/IAM | 11 | 11 | 1 | 10 | 9% |
| 48 | QA | 9 | 9 | 0 | 9 | 0% |
| 49 | Billing/Commercial | 7 | 7 | 1 | 6 | 14% |
| 50 | Capability Model | 6 | 4 | 2 | 2 | 50% |
| — | *(29 further domains)* | — | — | 0 | — | 0% |
| | **TOTAL** | **354** | **313** | **57** | **256** | **18.2%** |

**Domains with zero downgrades (29):** 01, 02, 05, 06, 07, 08, 10, 12, 13, 14, 16, 17, 24, 32, 33, 38, 39, 40, 41, 42, 43, 44, 45, 47, 48, 51, 52, 53, 54.

## §5 Overall false-positive metrics

| Metric | Value |
|---|---:|
| A. Total FTR rows (independent) | 354 |
| B. Total Cline `IMPLEMENTED_AND_WIRED` | 313 |
| C. Independently confirmed (durable + reachable) | 256 |
| D. Downgraded | 57 |
| &nbsp;&nbsp;· disclosed in the Truth cell (schema caveat present) | 20 |
| &nbsp;&nbsp;· undisclosed at row level (plain token) | 37 |
| E. Upgraded (catalogue under-claimed) | 1 (`FTR-248`) |
| F. Unverified (runtime not executed) | 313 |
| G. Schema-blocked | 57 |
| H. Runtime-unverified | 313 |
| I. Historical-only (correctly classified) | 5 |
| J. Disposable-only | 19 |
| K. Documentation-only (correctly classified) | 9 |
| L. **False/too-strong `IMPLEMENTED_AND_WIRED` rate** | **18.2%** (57/313) |
| M. **Undisclosed overclaim rate** | **11.8%** (37/313) |

## §6 Contradiction register (five deliverables)

| # | Contradiction | Deliverables | Severity |
|---|---|---|---|
| C-1 | 8 capabilities mapped to different FTR sets | D1 §7.2 vs D3 §3 | Material |
| C-2 | `system_settings` = 63 columns (claimed) vs 60 (measured) | D1/D2 §1.1 vs live | Minor |
| C-3 | Admin routes 21 (claimed) vs 22 measured; frontend 52 vs 55 | D1 §2/§4 vs source | Minor |
| C-4 | `CODE_ONLY` = 1 (D1 §6.2) vs 0 Truth-token rows | D1 §6.2 vs D1 §4 | Minor |
| C-5 | Headline `313 IMPLEMENTED_AND_WIRED` vs `256` durably-wired | D1 §1/D5 §2 vs this verification | Material |

**Total cross-deliverable contradictions: 5** (2 material, 3 minor).

## §7 Under-claims (catalogue too conservative)

| FTR_ID | FEATURE | CLINE | INDEPENDENT | Evidence |
|---|---|---|---|---|
| FTR-248 | Benchmarking domain | IMPLEMENTED_BACKEND_ONLY (no API/UI located) | IMPLEMENTED_AND_WIRED (legacy API) | `backend/api/business.py` L182 `POST /benchmark`; `/api/v2/benchmark` |

## §8 New gaps discovered by this verification

| ID | Gap | Severity | Fix |
|---|---|---|---|
| FTRGAP-7 | The `CAP→FTR` join contains demonstrable misjoins (43 low-overlap rows) and 8 cross-deliverable contradictions | Material | Regenerate the join mechanically from the FTR table |
| FTRGAP-8 | The headline `313 IMPLEMENTED_AND_WIRED` counts 57 schema/disposable-blocked rows (37 undisclosed) | Material | Apply the FIEW corrections; publish `256` durable-wired until W1 completes |
| FTRGAP-9 | Minor count errors (`system_settings` 63→60; route counts) | Low | Correct the catalogue |

<!--CTEOF-->
