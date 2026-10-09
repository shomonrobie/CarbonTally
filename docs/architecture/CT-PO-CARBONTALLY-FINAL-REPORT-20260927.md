# CarbonTally — Forensic Catalogue Set: Final Report (Deliverable 5 of 5)

**Document:** `docs/architecture/CT-PO-CARBONTALLY-FINAL-REPORT-20260927.md`
**Audience:** Product Owner · engineering · independent QA/audit (OHD)
**Date:** 2026-09-27
**Git state at time of writing:** branch `p8-release-reconciled`, HEAD `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`; all five deliverables are **untracked new files** — nothing was committed, no history was rewritten, no existing file was deleted.
**Posture:** read-only forensic discovery. **No** DDL, DML, migration, seed, configuration change, deployment, endpoint execution or Git mutation was performed in producing this set.

---

## 1. What this set is — and what it is not

This set was commissioned to answer, from evidence rather than memory:

1. **What does CarbonTally contain?** (Deliverable 1 — feature catalogue)
2. **How is it configured, and does that configuration actually work?** (Deliverable 2 — configuration catalogue)
3. **How does declared functionality trace from capability to persistence to role to boundary?** (Deliverable 3 — functionality traceability)
4. **Where does it fall short of its own ratified requirements?** (Deliverable 4 — gap analysis)
5. **What is the verified state of the platform today?** (this document)

It is **not** a product demo, an acceptance certificate, or a security verdict.
Consistent with AGENTS §73, the words *implemented*, *tested*, *verified* and
*accepted* are used strictly and never interchangeably.

## 2. Verdict of the set

> **CarbonTally is a substantially built, multi-tenant emissions-processing platform
> with a real feature inventory, a real tenant population, and a real calculation
> history — whose core automatic processing pipeline, evidence materialisation,
> approval/QC stages and boundary refusals are currently traced in source and
> unexercised in data.**

| Dimension | Verdict |
|---|---|
| Feature inventory | **Substantial and traceable** — 54 domains, 354 feature rows, 313 `IMPLEMENTED_AND_WIRED` |
| Schema/durability | **Divergent** — 43 unapplied migrations; 6 local environments with 116–145 public tables and 4 unreadable ledgers |
| Live tenant/calculation data | **Real** — 975 organisations, 1,344 users, 917 consultant–client links, 100 calculation snapshots, 100 emissions logs |
| Core automatic pipeline | **Unproven at runtime** — state-machine, evidence, approval, QC objects are `0 rows` or absent |
| Configuration | **Partly nominal** — 2 HIGH findings: wired to columns that exist in no durable database |
| Security posture | **Designed, not tested** — 16 boundary paths traced; 0 executed; 174 RLS policies present |
| Overall | `CATALOGUE_SET_COMPLETE_AWAITING_PO_DECISIONS_AND_EXECUTION` |

## 3. The five deliverables

| # | Document | Scope | Key counts | Verdict |
|---|---|---|---|---|
| **1** | `CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` | Complete feature catalogue from schema, code and historical evidence | 54 domains · **354 `FTR` rows** · truth states · persistence classes `A–E` · `T1–T6` · `R1–R7` · `POD-A…POD-J` | `FEATURE_CATALOGUE_COMPLETE` |
| **2** | `CT-PO-CARBONTALLY-CONFIGURATION-CATALOGUE-20260927.md` | Every configuration surface and its live value | 8 classes `C1–C8` · 11 platform setting rows/keys · **63 `system_settings` columns** · 7 commercial keys · 6 plan rows · ~45 env vars · **174 RLS policies** · `CFG-1…CFG-10` · `POD-K…POD-O` | `CONFIGURATION_CATALOGUE_COMPLETE_WITH_OBSERVATIONS` |
| **3** | `CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md` | Capability → feature → persistence → role → boundary traces + live population baseline | **152/152 capabilities joined** · 354 rows referenced · 15 roles · **8 workflows `W1–W8`** · **16 boundary paths** · live baseline (§5.0) · `FTR-GAP-1…6` | `FUNCTIONALITY_TRACEABILITY_COMPLETE_WITH_DECLARED_GAPS` |
| **4** | `CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md` | Consolidated, severity-ranked gap register and remediation sequence | **29 gaps** — 6 HIGH / 13 MEDIUM / 7 LOW-MED / 3 LOW · 15 PO decisions unified · 7 remediation waves | `GAP_ANALYSIS_COMPLETE_WITH_29_REGISTERED_GAPS` |
| **5** | *this document* | Final report and acceptance posture | — | `FINAL_REPORT_COMPLETE` |

---

## 4. Verified state of the platform (what is genuinely real)

Drawn from live read-only counts and the three catalogues.

### 4.1 Populated and durably evidenced (flagship `postgres`, 116 public tables)

| Area | Evidence |
|---|---|
| Tenancy | `organizations` **975** · `organization_members` **1125** · `users` **1344** |
| Consultant operating model | `consultant_clients` **917** · `consultant_profiles` **55** · `consultant_firm_members` **54** |
| Processing entities | `processing_entities` **11** · `staff_profiles` **21** |
| Master data | `facilities` **157** · `assets` **310** · `suppliers` **156** · `vehicles` **3** · `organization_files` **263** |
| Factors | `emission_factors` **7049** · `customer_factors` **245** |
| Upload & documents | `upload_batches` **52** · `document_processing_queue` **40** |
| Manual processing path | `manual_extraction_batches` **57** · `manual_extraction_items` **264** · `manual_review_queue` **2** |
| Calculation | `calculation_snapshots` **100** · `emissions_logs` **100** |
| Reporting | `report_versions` **17** · `report_generation_queue` **14** |
| Messaging | `conversations` **36** · `conversation_participants` **65** · `messages` **54** · `notifications` **3** |
| Audit | `audit_trail` **563** |

### 4.2 Empty, absent or unexercised

| Area | Evidence |
|---|---|
| Automatic processing state machine | `processing_queue`, `processing_steps`, `processing_logs`, `processing_assignments`, `processing_audit_trail` = **0** |
| Evidence | `evidence_line_items` **absent** in the flagship; **0** in the clone |
| Approval / QC | `approval_requests`, `approval_decisions`, `qc_checks`, `qc_checklists`, `qc_errors`, `review_audit_trail` = **0** |
| Audit targets that carry the configured retention key | `audit_logs` **0** · `activity_logs` **0** (writes land in `audit_trail`) |
| Role catalogue | `roles` **0** in both environments |
| Commercial / SLA / white-label | every `billing_*` transactional table, `customer_subscriptions`, `consultant_billing`, `sla_definitions`, `sla_compliance`, `consultant_custom_domains`, `consultant_senders` = **0** |
| Disclosure / scope-3 / Insight | present **only** in the disposable clone (`disclosure_frameworks` 3 · `requirement_versions` 55 · `values` 12 · `scope3_categories` 15) — **absent** from the flagship |

**This is the single most consequential factual finding of the set**, and it is why
Deliverable 3 carries a live population baseline (§5.0) and Deliverable 4 exists at
all.

---

## 5. The verified gaps — headline view

Full register: Deliverable 4 §2. Severity arithmetic: **6 HIGH · 13 MEDIUM ·
7 LOW-MEDIUM · 3 LOW** = **29**.

| Rank | Gap | Why it matters | Closing wave |
|---|---|---|---|
| 1 | **GA-01** — 43 unapplied migrations; 6 divergent environments; 4 unreadable ledgers | Nothing downstream of the applied set is durable or verifiable | W1 |
| 2 | **GA-04** — durable automatic pipeline never executed (`0 rows`) | The platform's core commercial value chain is unproven at runtime | W3 |
| 3 | **GA-05** — no durable evidence store | AGENTS §17's provenance chain cannot be demonstrated | W3 |
| 4 | **GA-02** — retention API reads a column that exists in no durable database | A ratified configurable surface (N3) cannot be administered | W1 |
| 5 | **GA-03** — upload limits fall back to hard-coded literals | Upload policy is a code constant, not administered policy | W2 |
| 6 | **GA-06** — approval and QC tables empty everywhere | "Complete" or "reviewed" statuses are unsupported by records | W3 |
| 7 | **GA-29** — 16 boundary refusals traced but never executed | Security posture is a design claim, not a tested one | W4 |

### 5.1 What is *not* being claimed

Per Deliverable 4 §5: no workflow is asserted to run end-to-end; no boundary is
asserted to refuse; the platform is not asserted to be insecure; production is
neither asserted to match nor to differ from the release tree (`UNKNOWN`, not
`ABSENT`); `0 rows` is asserted to mean *unexercised*, never *broken*; no data loss
or corruption was observed; no secret, key, JWT or signed URL appears in any
deliverable.

---

## 6. Acceptance posture (AGENTS §73 applied strictly)

| Level | Statement | Supported? |
|---|---|---|
| **IMPLEMENTED** | The feature surface exists in code and is reachable from wired routes (313/354 `IMPLEMENTED_AND_WIRED`) | **Yes** — evidence in Deliverable 1 |
| **TESTED** | Automated verification has been run against the implementation | **Partially** — per-surface tests are not consolidated in this set; no test suite was executed here |
| **VERIFIED** | Independent, evidence-backed confirmation that the behaviour produces the business outcome | **No** — not for the pipeline, evidence, approval, QC, commercial or boundary paths (GA-04…GA-06, GA-27…GA-29) |
| **ACCEPTED** | Product Owner acceptance of a working commercial outcome | **No** — 15 PO decisions remain open (§7) and the core pipeline is unexecuted |

**Therefore:** this set establishes **IMPLEMENTED** and documents **what would have
to be executed** to reach **VERIFIED**. It does not confer acceptance (AGENTS §74).

---

## 7. Product Owner decision queue (15 open)

Full detail and engineering input: Deliverable 4 §4. **None was answered by this
analysis** (AGENTS §62). Grouped by what they unblock:

| Group | Decisions | Unblocks |
|---|---|---|
| **Environment & durability** | POD-A (where the 43 migrations land) · POD-I (production inspection) | GA-01, GA-02, GA-07, GA-16, W1 |
| **Retention & policy values** | POD-N (retention set incl. PX-7 90 days) · POD-E (audit retention = 1 day?) · POD-M (authoritative upload-limit object) | GA-03, GA-08, GA-17, W2 |
| **Commercial terms** | POD-K (overage/allowance/credit values) · POD-L (currency model) | GA-10, GA-25, GA-28, W5 |
| **Model & naming** | POD-B (`accounting_dimensions`) · POD-C (`roles` catalogue) · POD-D (Locations vs Facilities) · POD-F (PE terminology) · POD-J (residual capabilities) | GA-13, GA-14, GA-15, GA-18, GA-23, W6 |
| **Legacy & platform identity** | POD-G (legacy admin retirement) · POD-H (legacy artefacts) · POD-O (notification sender identity) | GA-19, GA-20, GA-26, W6 |

**Ratified decisions explicitly preserved:** `N3` (configurable server-side
retention) · `PX-7 Option (a) 2026-09-14` (telemetry retention configurable,
initial 90 days, as a schema default — not a code literal) · PO `D-P2-02` (legacy
admin CRA deprecated) · P8X-X2's own constraint **"Production is PROHIBITED
(G0-D open)"**.

---

## 8. Recommended next steps

| Order | Action | Agent | Output expected |
|---|---|---|---|
| 1 | Answer the 15 decisions in §7 — start with POD-A, POD-N, POD-M | **PO** | Written decisions; each `GA` row becomes `IMPL` with a ratified target |
| 2 | Apply migrations to **one declared durable environment** (backed up, filename order), then re-run the ledger arithmetic and the environment table in Deliverable 1 §5.3 | **Cline** | GA-01/GA-07 closed or narrowed; GA-02 endpoint re-probed |
| 3 | Execute the automatic pipeline end-to-end on a **disposable clone** with per-stage row counts, `attempt_count`/retry and resume evidence, then materialise one evidence set, one approval cycle and one QC cycle | **Cline** | GA-04/GA-05/GA-06/GA-27 → `VERIFIED` or converted into precise defects |
| 4 | Execute all **16 boundary paths** and record ALLOW/DENY per row, raising every unexpected ALLOW as a serious finding | **OHD / QA** | GA-29 closed; security posture becomes *tested* |
| 5 | Re-catalogue the affected Deliverable 1/3 rows with dated dispositions | **Cline** | Catalogue drift removed |

**Environment safety (mandatory, AGENTS §55.1):** the integration harness's `pool`
fixture runs `TRUNCATE … RESTART IDENTITY CASCADE`, and the code refuses targets
whose names match `qa`/`demo`/`investor`/`prod`/`live`. Every execution step above
must therefore target a disposable `ct_*` clone or `carbontally_test` — **never** the
flagship investor-demo database, and never production. The investor dataset
(1,185 identities, `tools/seed_investor_demo/DEMO_IDENTITIES.md`) was read-only
throughout and was not mutated.

---

## 9. Method, reproducibility and limitations

| Aspect | Detail |
|---|---|
| Evidence base | Applied-schema inventory (116 public tables, flagship) · clone inventory (145 public tables) · 89 migration files vs 46 ledger rows vs 43 unapplied · OpenAPI contract · source tree · configuration surfaces · historical audits/decisions |
| Population evidence | Live read-only `SELECT count(*)` per table in both environments, plus one bounded duplicate-detection probe |
| Databases touched | Read-only only; no writes, no DDL, no seeds, no truncates |
| Secrets | None captured, logged or reproduced |
| Reproducibility | Every claim is anchored to a named object (table, column, file, key, route) or a live count; a re-run of the same read-only probes should reproduce the same baseline |
| Limitation 1 | Live counts describe *point-in-time* environments; they do not constitute testing |
| Limitation 2 | `PREDICTED(runtime)` rows in Deliverable 2 remain predicted until their endpoints are executed |
| Limitation 3 | The 43 unapplied migrations mean class-C capabilities are only observable in the clone — the flagship understates the release tree |
| Limitation 4 | The `CAP → FTR` join is analyst-derived (GA-22), not machine-generated |
| Limitation 5 | Production was never contacted: every `PROD:` truth state remains `UNKNOWN` |

## 10. Hand-back

| Artefact | Path |
|---|---|
| Deliverable 1 — Feature catalogue | `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` |
| Deliverable 2 — Configuration catalogue | `docs/architecture/CT-PO-CARBONTALLY-CONFIGURATION-CATALOGUE-20260927.md` |
| Deliverable 3 — Functionality traceability | `docs/architecture/CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md` |
| Deliverable 4 — Gap analysis | `docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md` |
| Deliverable 5 — Final report | `docs/architecture/CT-PO-CARBONTALLY-FINAL-REPORT-20260927.md` |

| Item | Value |
|---|---|
| Deliverables | **5 of 5 complete** |
| Features catalogued | 354 rows across 54 domains |
| Capabilities traced | 152/152 joined |
| Gaps registered | 29 (6 HIGH · 13 MEDIUM · 7 LOW-MED · 3 LOW) |
| PO decisions open | 15 (`POD-A…POD-O`) |
| Remediation waves | 7 (W0–W6) |
| Writes / destructive operations | **None** |
| Secrets reproduced | **None** |
| Git mutations | **None** (no commit, no reset, no force-push) |
| Verification posture | Forensic catalogue: **CONSOLIDATED + LIVE-READ-VERIFIED**; workflows beyond that: **UNVERIFIED** |
| Set verdict | `FORENSIC_CATALOGUE_SET_COMPLETE_AWAITING_PO_DECISIONS_AND_EXECUTION` |

**Final sentence.** The inventory work is done and the evidence is captured: the
remaining distance to a defensible commercial claim is *execution* (W1–W4) plus
*fifteen decisions* (W0) — not more documentation.

<!--CTEOF-->
