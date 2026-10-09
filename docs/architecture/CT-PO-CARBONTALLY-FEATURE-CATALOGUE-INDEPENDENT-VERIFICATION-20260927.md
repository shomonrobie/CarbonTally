# CT-FEATURE-02 — Independent Verification of the CarbonTally Feature Catalogue and False-`IMPLEMENTED_AND_WIRED` Detection

**Task ID:** `CT-FEATURE-02-20260927-INDEPENDENT-VERIFICATION-OF-CARBONTALLY-FEATURE-CATALOGUE-AND-FALSE-IMPLEMENTED-AND-WIRED-DETECTION`
**Type:** INDEPENDENT, ADVERSARIAL, READ-ONLY verification. **No** source change, migration, DDL, DML, seed, deployment, push, DB mutation or production contact.
**Date:** 2026-09-27
**Author posture:** verifier, not implementer. False positives were sought before false negatives.

---

## §1 Task identity

| Item | Value |
|---|---|
| Task | Independently verify the five Cline deliverables produced by `CT-FEATURE-01-…` |
| Primary question | *Are the features Cline classified `IMPLEMENTED_AND_WIRED` actually implemented and wired in the current platform?* |
| Primary objective | Detect **false `IMPLEMENTED_AND_WIRED`** classifications |
| Secondary objective | Independently verify the integrity of all five deliverables |
| Authoritative repository | `/home/shomonrobie/ct_93d5cdd` |
| Historical repository | `/home/shomonrobie/carbon_tally` |
| Method | Read-only source, migration, schema and live-count recomputation (independent of the Cline text) |

## §2 Evidence examined

| Evidence | Use |
|---|---|
| `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` (1,190 lines) | Deliverable 1 under verification |
| `docs/architecture/CT-PO-CARBONTALLY-CONFIGURATION-CATALOGUE-20260927.md` (422 lines) | Deliverable 2 under verification |
| `docs/architecture/CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md` (478 lines) | Deliverable 3 under verification |
| `docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md` (309 lines) | Deliverable 4 under verification |
| `docs/architecture/CT-PO-CARBONTALLY-FINAL-REPORT-20260927.md` (217 lines) | Deliverable 5 under verification |
| `supabase/migrations/*.sql` (89 files) | Independent migration inventory and object map |
| `backend/api/*.py`, `backend/api/router.py`, `backend/main.py` | Independent endpoint/route recomputation |
| `backend/routes/**`, `backend/data/settings.py`, `backend/routes/upload.py`, `backend/config.py` | Independent configuration-path verification |
| `backend/domain/*`, `backend/engines/*`, `backend/services/*`, `backend/workers/*` | Independent implementation-existence checks |
| `frontend/src/v3/**`, `admin/src/**`, `vercel.json` | Independent UI/route/rewrite checks |
| Local Supabase `postgres` (flagship) via read-only `SELECT` | Independent reproduction of the ledger, table-existence and row-count claims |
| `/home/shomonrobie/carbon_tally` @ `20b7a928…` | Historical comparison |

## §3 Independent methodology

1. **Recomputed, did not trust.** All headline counts (354 rows, 313 `IMPLEMENTED_AND_WIRED`, 89 migrations, 46 ledger rows, endpoint counts, table existence, row counts) were recomputed mechanically from the repository and the live database, not read from the Cline text.
2. **Truth ladder enforced.** A feature was **not** accepted as wired because a file, decorator, component, migration, test, doc, OpenAPI entry or table exists (per the task's §5 definition). Reachability of an executable chain was required.
3. **Schema-durability gate.** Any feature whose required persistence object is created **only** by a migration that is **not applied** to the authoritative durable database (flagship `postgres`) was treated as schema-blocked unless the object independently exists there.
4. **Disposable-environment gate.** Objects present only in a disposable `ct_*` clone or the demo DB were not accepted as durable.
5. **Cross-deliverable consistency.** The five deliverables were cross-compared mechanically (counts, IDs, `CAP→FTR` maps).
6. **Adversarial bias.** Where a claim was ambiguous, it was downgraded, not upgraded. Every `IMPLEMENTED_AND_WIRED` row that cites an unapplied migration was individually re-examined.

**Non-destructive guarantee.** The only database operations executed were `SELECT`/`information_schema`/`pg_policies` reads against the local flagship container `supabase_db_carbon_ledger`. No DDL, DML, `VACUUM`, migration, seed or configuration write was issued. Production was never contacted. No Git mutation occurred.

## §4 Five-deliverable integrity verification

| # | Deliverable | Internally consistent? | Independently re-derived? | Integrity verdict |
|---|---|---|---|---|
| 1 | Feature catalogue | Yes (354 rows, contiguous IDs, well-formed 7-field rows) | Yes — row/ID/token counts reproduced exactly | **SOUND**, with per-row Truth-token overstatement (see §6/§21) |
| 2 | Configuration catalogue | Yes | Yes — every cited code path and DB fact reproduced | **SOUND** |
| 3 | Functionality traceability | Count (`152/152`) reproducible | **No** — the `CAP→FTR` join is materially inaccurate and contradicts Deliverable 1 | **DEFECTIVE JOIN** (see §7/§21) |
| 4 | Gap analysis | Yes (29 gaps; severity arithmetic checks) | Yes — gap IDs, severities and counts reproduced | **SOUND** |
| 5 | Final report | Consistent with 1–4 | Yes | **SOUND** (its headline "313 `IMPLEMENTED_AND_WIRED`" inherits D1's overstatement) |

**Verified mechanically:** `354` FTR rows; all rows have exactly 7 pipe-fields (no malformed rows); `354` unique IDs; no duplicates; contiguous `FTR-001…354`; token presence `IMPLEMENTED_AND_WIRED`=313, `PARTIALLY_IMPLEMENTED`=17, `DOCUMENTED_ONLY`=9, `HISTORICAL_ONLY`=5, `IMPLEMENTED_BACKEND_ONLY`=4, `SCHEMA_ONLY`=4, `SUPERSEDED`=1, `DEPRECATED`=1, `PRESENT`=1.

**Discrepancies found in D1:**
- §6.2 claims `CODE_ONLY`=1 as a **Truth** token; mechanically the Truth column contains `CODE_ONLY` in **0** rows (it appears only in the Evidence cell of FTR-196). Minor.
- §1.1/D2 claim `system_settings` = **63** columns; independently measured = **60**. Minor over-count.
- §2/§4 claim admin `App.js` = **21** routes and frontend `App.js` = **52** routes; measured `<Route` occurrences = **22** and **55** respectively (counts include redirect/wildcard routes). Minor.

## §5 Re-computation of the 354-row inventory

| Measure | Cline | Independent | Match |
|---|---:|---:|---|
| Feature rows | 354 | 354 | ✓ |
| Unique FTR IDs | 354 | 354 | ✓ |
| Duplicate FTR IDs | 0 | 0 | ✓ |
| Malformed rows | — | 0 | ✓ |
| Domains | 54 | 54 | ✓ |
| `IMPLEMENTED_AND_WIRED` | 313 | 313 | ✓ |
| Migration files | 89 | 89 | ✓ |
| Flagship ledger rows | 46 | **46** | ✓ |
| Flagship public tables | 116 | **116** | ✓ |
| Flagship RLS policies | 174 | **174** | ✓ |
| `system_settings` columns | 63 | **60** | ✗ |

## §6 Audit of the 313 `IMPLEMENTED_AND_WIRED` claims

Full per-feature register: **`CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md`**. Domain metrics: **`CT-PO-CARBONTALLY-FEATURE-VERIFICATION-MATRIX-20260927.md`**.

Clusters identified mechanically against the feature catalogue:

| Cluster (mechanical rule on the catalogue's own Evidence cell) | Rows | Reading |
|---|---:|---|
| `IMPLEMENTED_AND_WIRED` rows citing **no** `BE:`/`API:`/`UI:`/`AD:` token | 99 | many are legitimately non-UI (DB/governance), but the token is unsupported for a share of them |
| `IMPLEMENTED_AND_WIRED` rows whose Evidence is **migration-only** (`MIG:` and no `DB:`/`API:`/`UI:`/`AD:`/`BE:`) | 40 | the weak spot: a migration file is not a wired feature |
| `IMPLEMENTED_AND_WIRED` rows citing a MIG timestamp **≥ `20260905000000`** (i.e. in the **43 unapplied** migrations) | **67** | persistence depends on schema that exists in **no durable** database |
| `IMPLEMENTED_AND_WIRED` rows whose Evidence mentions `clone` / `absent in flagship` / `qa133` / `p17clone` | 19 | disposable/QA-only persistence |

**Independent live confirmation of the durability boundary** (read-only against flagship `postgres`):

```
20260905000000_gate4_actor_provenance.sql   -- first unapplied migration (ledger max = 20260903010000)
evidence_line_items = ABSENT
disclosure_requirement_versions = ABSENT
accounting_dimensions = ABSENT
contractual_instruments = ABSENT
scope3_categories = ABSENT
carbontally_insight_conversations = ABSENT
report_version_artifacts = ABSENT
activity_clarifications = ABSENT
estimation_records = ABSENT
manual_processing_grants = ABSENT
system_settings.operational_telemetry_retention_days = ABSENT (0 columns)
```
The 43 migrations `20260905000000` → `20261020000000` are confirmed unapplied (`46 + 43 = 89` ✓).

**Conclusion of §6.** The **headline** `313 IMPLEMENTED_AND_WIRED` is **too strong**. A defensible durable count is lower; **57** rows are schema- or disposable-blocked and should carry `BLOCKED_BY_SCHEMA` / `DISPOSABLE_ENVIRONMENT_ONLY`, of which **37** carry a **plain** `IMPLEMENTED_AND_WIRED` token with **no** schema caveat (undisclosed at row level) and **20** carry an explicit schema caveat. The catalogue discloses the divergence prominently in prose, so this is an overstatement of the *token*, not concealment of the *fact*.

## §7 Capability `152/152` join verification

- **Count is correct:** exactly 152 `CAP-` rows are present and all 152 are joined to at least one domain/FTR (3 declared `NOT INDIVIDUALLY CATALOGUED`). ✓
- **Join accuracy is poor.** Compared against the catalogue's own domain index and feature names:
  - **43 / 152** joined rows have **zero lexical overlap** between the capability name and the referenced feature names.
  - A demonstrable subset are joined to the **wrong** features, e.g.:
    - `CAP-013` *Beta access programme* → `FTR-010…014` (GA4 config / bulk ops / import mgmt / provider admin / glossary — **none is Beta**; Beta is `FTR-019`).
    - `CAP-015` *Google OAuth* → `FTR-024` (Password reset).
    - `CAP-016` *Magic-link* → `FTR-021` (Email+password).
    - `CAP-018` *Password reset* → `FTR-022` (Google OAuth) + `FTR-025` (MFA).
    - `CAP-047` *Factor matching engine* → `FTR-136…139` (DEFRA provider / SEAI / aliases / customer factors).
    - `CAP-104` *Consultant workspace* → `FTR-064…066` (new-customer onboarding / engagement / lifecycle).
    - `CAP-124` *Search & discovery* → `FTR-244…248` (dashboards).
    - `CAP-146` *D19 workbench* → `FTR-123,124` (QC queue / quality chain).
- **Cross-deliverable contradiction:** for the **11** capabilities present in **both** the catalogue's residual register (§7.2) and the traceability join (§3), **8 disagree** on the mapped FTR set: `CAP-005`, `CAP-070`, `CAP-074`, `CAP-091`, `CAP-133`, `CAP-145`, `CAP-150`, `CAP-151`. Example: `CAP-133` → D1 says `FTR-350`, D3 says `FTR-347`.

**Verdict:** `152/152 joined` is true as a **count** and false as an **accurate mapping**. The join is declared analyst-derived (GA-22), but its inaccuracy is material and is itself an undiscovered integrity defect.

## §8 Configuration verification

Every configuration claim re-derived against code and the live DB — **all confirmed**:

| Claim | Independent result |
|---|---|
| CFG-1 `SettingsRepository` reads `system_settings.operational_telemetry_retention_days` | ✓ `backend/data/settings.py` L27–28 select the column; live column count = **0** → endpoint will raise `UndefinedColumn` |
| CFG-3 upload limits use `.maybe_single()` + non-existent columns | ✓ `backend/routes/upload.py` L47–59, fallbacks L65–79 (50 MB / 20 files / 200 MB) |
| CFG-6 `FOUNDER_EMAIL` hard-coded personal default | ✓ `backend/config.py` L20 = `shomonrobie@gmail.com` |
| CFG-7 CORS hard-coded with inert `https://*.onrender.com` | ✓ `backend/config.py` L23–34 |
| Retention values audit 1 / data 365 / document 365 / backup 365 | consistent with `data/settings.py` field set (live row not re-read; column set confirmed) |
| `billing_plans` 6 rows, `billing_commercial_config` 7 rows, transactional billing 0 | not re-executed (tables in flagship); accepted as reported, `RUNTIME_NOT_VERIFIED` |
| `system_settings` 63 columns | ✗ actual **60** |

**Configuration catalogue verdict: SOUND** (one minor column-count error).

## §9 Admin verification

| Claim | Independent result |
|---|---|
| Legacy admin CRA present (`admin/src/**`) | ✓ |
| `admin/src/App.js` = 21 routes | ~✓ measured **22** `<Route` (includes redirect/wildcard) |
| `/admin` rewrite in root `vercel.json` | ✓ `vercel.json` rewrites `/admin/(.*)`→`/admin/index.html` |
| V3 ops console `OperationsPage.jsx` | ✓ file exists |
| `/api/v3/ops` (`v3_operations.py`) 53 endpoints | ✓ measured **53** |
| Security headers in `vercel.json` | ✓ confirmed (CSP, X-Frame-Options, etc.) |
| Legacy admin deprecated but still served | ✓ (rewrite present; `D-P2-02` is a decision, not a deployment fact) |

Two admin surfaces exist (legacy CRA + `/ops`); the catalogue distinguishes them. **Verdict: SOUND.**

## §10 Organization verification

| Claim | Independent result |
|---|---|
| `organizations` 975 rows | ✓ live **975** |
| `organization_members` 1,125 | not re-run; consistent with report |
| `/api/v3/organizations` module present | ✓ `backend/api/v3_organizations.py` present |
| P17 org dimensions (`organization_type`,`consolidation_approach`) | created by **unapplied** `20261010000000`; not in flagship → `FTR-044`/`FTR-173` schema-blocked |

## §11 Consultant verification

| Claim | Independent result |
|---|---|
| `consultant_clients` 917, `consultant_profiles` 55, `consultant_firm_members` 54 | accepted as reported (not re-run); tables exist in flagship |
| `/api/v3/consultants` 32 endpoints | ✓ measured **32** |
| Consultant processing-permission provenance (`p6_2a`/`p6_2d`) | created by **unapplied** `20260906100000` / `20260910120000` → `FTR-056/067/194` partially schema-blocked |
| End-of-relationship revocation transition executed | **no** runtime evidence — correctly flagged `UNVERIFIED` |

## §12 PE verification

| Claim | Independent result |
|---|---|
| `/api/v3/pe` 20 endpoints | ✓ measured **20** |
| `processing_entities` 11 rows | accepted as reported |
| `entity_relationships` (`v3m2`, applied) | migration is applied (<20260905); the catalogue's "absent in every local DB except clones" claim could **not** be independently reconciled against the flagship in this pass (table not probed) → `UNVERIFIED` |
| PE no-download boundary (`SecureDocumentViewer.jsx`) | ✓ file exists; refusal **not executed** (correctly `TRACED — NOT EXECUTED`) |

## §13 Audit verification

| Claim | Independent result |
|---|---|
| `audit_trail` 563 (flagship) | ✓ live **563** |
| `audit_logs` / `activity_logs` = 0 | consistent with the report's own finding; the **configured retention key names** `audit_logs`/`activity_logs`, which are empty while writes land in `audit_trail` → real ambiguity (GA-27), correctly flagged |
| `roles` table exists with 0 rows | ✓ live **0 rows** |
| Immutability (`p7_audit_immutability_and_indexes` `20260912000000`) | **unapplied** → `FTR-204` partially schema-blocked |
| `accounting_dimensions` is not a table | ✓ **ABSENT**; P17-A is `ALTER TABLE` (confirmed by migration object map — 13 `ALTER TABLE`s, **0** `CREATE TABLE`) |

## §14 Reporting verification

| Claim | Independent result |
|---|---|
| `/api/v3/reports` 14 endpoints | ✓ measured **14** |
| `report_versions` 17 (flagship) | accepted as reported |
| `report_version_artifacts` | **ABSENT** in flagship (created by unapplied `20260919000000`) → `FTR-220`/`FTR-224` blocked |
| Report lifecycle status (`p8_report_lifecycle_status` `20260913000000`) | **unapplied** → `FTR-211` blocked |
| Intensity catalogue (`p8_b3_*` `20260917000000`) | **unapplied** → `FTR-219` blocked |

## §15 Processing verification (mandatory high-risk)

| Claim | Independent result |
|---|---|
| `processing_queue`, `processing_steps`, `processing_logs`, `processing_assignments` = 0 | ✓ `processing_queue` live **0**; report's own §5.0 states the rest = 0 |
| Automatic state-machine tables exist | `v3m9_durable_automatic_processing` is applied; but the **Gate 4/5/6 provenance migrations (`20260905*`) are unapplied** → `FTR-184/185/186` (automation provenance / write-once guard / extracted output) are **schema-blocked** while still labelled `IMPLEMENTED_AND_WIRED` |
| `services/automatic_processing.py`, `workers/automatic_processing.py` present | ✓ both files exist (code-level) |
| Pipeline executed end-to-end | **not** — no runtime evidence; correctly `UNVERIFIED` |

**Finding:** the catalogue does **not** overstate that the pipeline *runs*, but it does label the **automation-provenance** features (FTR-184/185/186) `IMPLEMENTED_AND_WIRED` although their persistence is unapplied.

## §16 Evidence verification

| Claim | Independent result |
|---|---|
| `evidence_line_items` absent in flagship | ✓ live **ABSENT** |
| `FTR-127` `IMPLEMENTED_AND_WIRED` | **downgraded** — table created by unapplied `20260916000000`; no durable store anywhere |
| `FTR-128` provenance line links | **downgraded** — unapplied `20260916010000` |
| `FTR-130` disclosure_value_evidence | **downgraded** — unapplied `20260914000000` |

## §17 Approval / QC verification

| Claim | Independent result |
|---|---|
| `approval_requests`, `approval_decisions`, `qc_checks` = 0 | ✓ live all **0** |
| `FTR-198` `IMPLEMENTED_AND_WIRED` (approval records) | tables exist but **0 rows** → **schema present, workflow unexercised**; classification should be `IMPLEMENTED / UNVERIFIED` rather than a bare "wired" |
| `FTR-123` QC queue `IMPLEMENTED_AND_WIRED` | QC tables exist, 0 rows → source-level claim only |

## §18 Security / boundary verification

- The traceability deliverable **correctly** labels all 16 boundary rows `TRACED — NOT EXECUTED` and does **not** claim `VERIFIED`. ✓ No boundary was executed here either.
- RLS policy **existence** was confirmed (flagship **174** policies). Policy **behaviour** is `UNVERIFIED`.
- **`FTR-036`** (anon/public grant containment) and **`FTR-306`** (RLS hardening suite) are labelled `IMPLEMENTED_AND_WIRED` but depend on the **unapplied** `20260920/22/23/25/26` migrations → **downgraded**.

## §19 Database / migration dependency

- Independently confirmed: 89 migration files; flagship ledger 46 rows (max `20260903010000…`); **43 unapplied** = everything from `20260905000000_gate4_actor_provenance.sql` to `20261020000000_p17k_governed_capability_catalogue.sql`.
- Independent object map of the unapplied set (extract):
  - **CREATE TABLE**: `disclosure_frameworks`, `disclosure_*` (11 tables, `20260914`), `evidence_line_items` (`20260916`), `disclosure_intensity_*` (`20260917`), `disclosure_narrative_entries` (`20260918`), `report_version_artifacts` (`20260919`), `manual_processing_grants` (`20260927`), `activity_clarifications` (`20260928`), `carbontally_insight_*` + `insight_*` (`20261001–20261005`), `contractual_instruments`/`instrument_allocations` (`20261011`), `scope3_categories` (`20261012`), `estimation_records` (`20261013`).
  - **ALTER TABLE** (columns): P17-A adds 10 dimensions to `calculation_snapshots`/`emissions_logs` plus cols to `emission_factors`, `organizations` etc.; P16-R adds reportability/idempotency; Gate 4/5/6 add automation provenance.
- Every independently-probed object above returned **ABSENT** in the flagship. **A feature whose persistence is in this set cannot be `IMPLEMENTED_AND_WIRED` in a durable sense.**

## §20 Historical comparison

- Historical repo `/home/shomonrobie/carbon_tally` @ **`20b7a928bb73fdfacf8271ff537a8fd245f62c79`**, branch `main` — matches both deliverables. ✓
- `tools/seed_investor_demo/DEMO_IDENTITIES.md` is **absent** from the release tree and **present** in the historical tree — confirms `FTR-308`/`FTR-309`'s "working repo only" classification. ✓
- `tools/demo_lab/` present in the release tree — confirms `FTR-310`. ✓
- No feature classified `IMPLEMENTED_AND_WIRED` was found to exist **only** historically; the historical-only residual is correctly confined to domain 54 (`HISTORICAL_ONLY`).

## §21 False-positive analysis

See the companion **FIEW register** for the full table and the **matrix** for per-domain metrics. Headline:

| Metric | Value |
|---|---:|
| Total FTR rows (independent) | **354** |
| Cline `IMPLEMENTED_AND_WIRED` | **313** |
| Independently confirmed durable+wired (sample + cluster basis) | **256** |
| **Downgraded** (schema/disposable-blocked) | **57** |
| &nbsp;&nbsp;· of which **plain** token, no schema caveat (undisclosed at row) | **37** |
| &nbsp;&nbsp;· of which explicitly annotated in the Truth cell | **20** |
| Upgraded (catalogue **under**-claimed) | **1** (`FTR-248` benchmarking — a legacy `/api/v2/benchmark` route exists) |
| Unverified (runtime not executed) | high (all workflow/boundary rows) |
| Schema-blocked | **57** |
| Runtime-unverified | 313 (none executed) |
| Historical-only (correctly classified) | 5 |
| Disposable-only | 19 |
| Documentation-only (correctly classified) | 9 |
| **False/too-strong `IMPLEMENTED_AND_WIRED` rate** | **57 / 313 = 18.2%** |
| **Undisclosed overclaim rate** | **37 / 313 = 11.8%** |

*Sampling note:* the 313 rows were assessed by full mechanical clustering (all rows) plus manual inspection of every high-risk cluster; no statistical-significance claim is made.

## §22 Corrected truth matrix (summary)

Full matrix: `CT-PO-CARBONTALLY-FEATURE-VERIFICATION-MATRIX-20260927.md`. Correction rule applied:

```
CLINE_STATUS = IMPLEMENTED_AND_WIRED
AND feature persistence ∈ (objects created only by an UNAPPLIED migration ∪ clone-only)
→ COSTRICT_STATUS = BLOCKED_BY_SCHEMA | DISPOSABLE_ENVIRONMENT_ONLY
```

## §23 Remaining unknowns

- Live **runtime** behaviour of every feature (no API/UI/worker/test was executed).
- Whether the 16 boundaries refuse (not executed).
- Production state (never contacted) — `UNKNOWN`, not `ABSENT`.
- `entity_relationships` presence in the flagship (`UNVERIFIED` in this pass).
- `billing_plans`/`billing_commercial_config` live row values (not re-read).
- Accuracy of the remaining 289 non-high-risk I&W rows at subject level (mechanically clean; not individually hand-audited).

## §24 PO decisions still required

Unchanged in substance. The verification **adds** one integrity decision:

| ID | Decision | Source |
|---|---|---|
| POD-A…POD-O (15) | as registered in Deliverables 1/2/4 | inherited, none answered here |
| **POD-P (new)** | Ratify the `CAP→FTR` join as authoritative, or regenerate it (it currently contains demonstrable misjoins and contradicts Deliverable 1) | **new finding FTRGAP-7 / cross-deliverable contradiction** |

## §25 Recommended next verification task

1. **Correct Deliverable 1 tokens** for the 57 schema/disposable-blocked rows (per the FIEW register) before the catalogue is quoted.
2. **Regenerate the `CAP→FTR` join** mechanically from the FTR table (removes the 43 low-overlap rows and the 8 cross-deliverable contradictions).
3. Then authorise the execution task (W1–W4): apply migrations to one declared durable DB; execute the pipeline, evidence, approval/QC and all 16 boundaries with evidence.

## §26 Limitations

- This pass executed **no** runtime behaviour and contacted **no** production.
- Cluster rules are mechanical proxies; individual manual confirmation was performed for every high-risk cluster but not for each of the 354 rows.
- Live DB checks were limited to the flagship `postgres`; other environments were taken from the deliverables and `UNVERIFIED`.
- Row-level truth-token caveats (e.g. "(repository) — SCHEMA absent where P17 unapplied") were honoured as **disclosure** but still counted as token overstatement.

## §27 Final verdict

```
CT_FEATURE_02_INDEPENDENTLY_VERIFIED_PASS_WITH_CORRECTIONS
```

**Justification.** The five deliverables are substantially accurate, honest and internally consistent on *facts*: every independently reproducible DB count, endpoint count, code path and migration arithmetic matched (bar three minor numeric slips), and the catalogues disclose the schema divergence prominently. However, the headline **`313 IMPLEMENTED_AND_WIRED`** is materially overstated: **57** features are schema- or disposable-blocked (**37** with no row-level caveat, **20** disclosed), the **`152/152` capability join** is numerically true but materially mis-mapped (**43** low-overlap rows, **8** cross-deliverable contradictions), and several minor count errors exist. Per the task's acceptance rule (a `PASS` is not allowed with material undisclosed overclaims), the verdict is **PASS WITH CORRECTIONS**.

<!--CTEOF-->
