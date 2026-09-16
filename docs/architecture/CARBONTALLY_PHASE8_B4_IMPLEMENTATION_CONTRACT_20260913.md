# CarbonTally — Phase 8 Reporting / Disclosure

## Batch B4 — Narrative, Finalisation and Frozen Artefact — IMPLEMENTATION CONTRACT

**Task identity:** `CT-P8-B4-CONTRACT-AND-PO-DECISIONS-20260913-034`
**Type:** ARCHITECTURE + IMPLEMENTATION CONTRACT (+ PO decision register). Implementation is **not** authorised by this document beyond what it explicitly records as already ratified.
**Date:** 2026-09-13
**Repository baseline:** branch `main` · HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400` · staged 0
**Environment baseline:** `carbontally_qa_phase8` (B1+B2+B3 applied) · `ct_b3_v3_20260913` (fresh clone)
**Predecessors (authoritative):** B1/B2/B3 contracts; **B3 closure (`-051`)**, B3 V3 verification (`-033`); Report lifecycle spec (`CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912`, esp. §10, §15, §17–§20, §21–§26, §28, §33–§35, §37); Disclosure Model Decision Record (`A1`, `A3`, `P3`, `DM-5`, `DM-6`, `DM-7`, `D15`); Product & report ratification (§§8.3.1, 9.1–9.3, 10, D-18/D-19, `A1`); S4 narrative-overlay report (`CT-P8-REPORTING-S4-NARRATIVE-OVERLAY-20260912-001`, the hard stop); P8X readiness §20 B4 row; PO rulings `…040` (**no Phase 9**) and `…050`.
**Evidence tags:** **[R]** repository/live fact · **[D]** ratified decision · **[V]** verified · **[U]** unresolved · **[DECISION REQUIRED]** PO ruling needed

---

## 1. The single sentence that defines B4

> **B4 lets the organisation author permitted narrative against the ratified requirement spine, finalise a report version honestly, and freeze an immutable artefact — without ever editing a calculated value, a provenance record or a regulatory claim.**

## 2. Root boundary (binding)

| Concern | Owner | B4's position |
|---|---|---|
| Calculation / emissions numbers | Calculation engine + `calculation_snapshots` | consume only; **no narrative write path may reach them** |
| Evidence / line addressability | **B2** (closed) | consume the B2 links for drill-down only |
| Disclosure values / requirements / purposes / intensity | **B3** (closed) | B4 binds narrative **to requirement versions** produced by B3; B4 changes no B3 object |
| Report version lifecycle states | **S1/S3** (verified) | consume; B4 adds the finalisation *gate* and the frozen artefact — it does not redefine the state machine |
| Extraction fidelity | **P1** (unauthorised) | not B4 |
| Factor matching | **P2** (unauthorised) | not B4 |
| Operational intelligence | **Phase 8-X** (in-programme) | not B4 |
| Production RLS remediation | separate held security workstream | not B4 |

## 3. Verified current state (live)

| Item | State |
|---|---|
| B3 objects | present: 14 disclosure tables incl. the three B3 intensity tables; `disclosure_values` + `disclosure_value_evidence` + the B2 value→line read model **[R]** |
| Narrative store | **absent** — no `narrative`/`commentary` table or column exists in any migration or in the live schema **[R]** |
| `report_comments` | present but **dormant** (no writer; E16) **[R]** |
| `report_generation_queue.user_edits` | dormant and unexposed **[R]** |
| `final_report_url` | dormant (no producer) **[R]** |
| Report version states | `DRAFT` → `REVIEWED` → `APPROVED` → `FINAL` (+ `CHANGES_REQUESTED`/`REJECTED`), immutability at `APPROVED`/`FINAL`, append-only audit **[D]/[V]** |
| Frozen artefact | no storage, no hash, no metadata model **[R]** |

## 4. B4 deliverables

| # | Deliverable | Kind | Status of its governing policy |
|---|---|---|---|
| **A** | Narrative overlay store: **requirement-bound**, typed, DRAFT-only | migration | **policy RATIFIED** (`A1`, `A3`, `P3`) → implementable now |
| **B** | Narrative domain layer: validation, allowlist enforcement, role enforcement | domain | **RATIFIED** (`A1`, `P3`) |
| **C** | Finalisation gate per `DM-5` (`CUSTOMER_INPUT_REQUIRED` blocks vs `NOT_SUPPORTED` surfaces; never collapsed) | domain/service | **RATIFIED** (`DM-5`) |
| **D** | Drill-down exposure per `DM-6` (Owner/Admin full; Viewer controlled; Consultant bounded; PE/cross-tenant denied) | API boundary | **RATIFIED** (`DM-6`) — read model already delivered in B3 |
| **E** | Approval workflow (who approves, revocation, review gating) | service/API | **[DECISION REQUIRED]** → `B4-D1…B4-D4` |
| **F** | Frozen export artefact (mandate, storage, hash, metadata, immutability) | migration/service/storage | **[DECISION REQUIRED]** → `B4-D5…B4-D7` |
| **G** | Retention/deletion for report versions and artefacts | policy + service | **[DECISION REQUIRED]** (legal review outstanding; N3 configurable) → `B4-D8` |
| **H** | Audit for every B4 write (reuse `audit_trail`) | audit | **RATIFIED** (existing taxonomy) |
| **I** | Authorization/RLS on new objects | security | **RATIFIED** posture (B1/B2/B3 pattern) + `DM-6` |
| **J** | API/service responsibilities (narrative CRUD, finalise, artefact retrieval) | API | **RATIFIED** except the approval/artefact specifics |
| **K** | Tests: static, pure, runtime, security ALLOW/DENY, regression | tests | **RATIFIED** requirement |
| **L** | Independent verification (gate **V4**) | verification | **RATIFIED** requirement |

## 5. Explicit non-scope

1. Any edit path to calculated emissions, provenance, factor data or system-derived values (`P3`).
2. Report-wide free-form editing; arbitrary narrative character limits (`A3`).
3. **AI-assisted narrative (S8)** — separate, PO-gated; B4 is deterministic only.
4. Per-gas / base-year functionality (`GP-GAS`, `GP-BY`).
5. Activation of `report_comments` unless the PO decides it (`B4-D9`).
6. P1, P2, RLS remediation, Phase 8-X, Insight, D16 legacy reporting.
7. Historical re-extraction or any backfill.
6a. Production deployment (G0-D open).

## 6. S4 hard-stop resolution (recorded, not silently reconciled)

The S4 report blocked on two stated grounds. Both are now addressed by **later ratified records**:

| S4 stated hard-stop condition | Resolution | Authority |
|---|---|---|
| "the existing narrative allowlist is missing/ambiguous" — the exact field allowlist was marked `PO DECISION REQUIRED` in the ratification (§9.1.2) and the lifecycle spec (§33 `P3`, §34 `A1`/`A3`) | **RESOLVED** — the Disclosure Model Decision Record **ratifies** `A1` (narrative bounded and requirement-specific; Owner/Admin authoring; no report-wide editing), `A3` (no arbitrary character limits; typed fields; evidence-backed limits only) and `P3` (customer-editable boundary; never calculations/provenance/factors). The *shape* of the allowlist is therefore decided: it is the **requirement-bound namespace**, not a free field list | `A1`, `A3`, `P3` (Decision Record §6) |
| "required authorization rules cannot be determined" | **RESOLVED for authoring** (`A1`/`P3`: Owner/Admin author; customers cannot edit authoritative values) and **for drill-down** (`DM-6`). The **approver** set for approval/finalisation remains **OPEN** (`B4-D1`) | `A1`, `P3`, `DM-6`; open: lifecycle spec `P4`/`A2`/`A5`/`A6` |

**Consequence:** the narrative and finalisation *policy spine* is ratified; B4 is **not** blocked wholesale. Only the approval, frozen-artefact and retention decisions (`B4-D1…B4-D8`) require PO rulings, and they gate deliverables **E, F, G** — not A, B, C, D, H, I, J(partly), K, L.

---

## 7. Narrative overlay model (deliverable A/B — policy RATIFIED, implementable)

### 7.1 `public.disclosure_narrative_entries` (additive, org-scoped)

| Column | Type | Rule |
|---|---|---|
| `id` | `uuid` | PK, `gen_random_uuid()` |
| `organization_id` | `uuid` | NOT NULL, FK → `organizations(id)` `ON DELETE CASCADE` (B1 convention) |
| `report_version_id` | `uuid` | NOT NULL, FK → `report_versions(id)` `ON DELETE CASCADE` |
| `requirement_version_id` | `uuid` | NOT NULL, FK → `disclosure_requirement_versions(id)` `ON DELETE RESTRICT` — **the binding that makes narrative requirement-scoped (`A1`)** |
| `disclosure_value_id` | `uuid` | NULL, FK → `disclosure_values(id)` `ON DELETE SET NULL` (context, never a value source) |
| `narrative_kind` | `varchar(30)` | NOT NULL — enumerated: `CUSTOMER_COMMENTARY` · `METHODOLOGY_NOTE` · `EXPLANATION` (closed set; no generic rules engine — D4) |
| `body` | `text` | NOT NULL, **plain text only** (no HTML/markup — lifecycle spec §10.3) |
| `authored_by` / `authored_at` / `updated_by` / `updated_at` | | attribution |
| `state` | `varchar(20)` | NOT NULL DEFAULT `DRAFT`; CHECK `IN ('DRAFT','SUPERSEDED')` — **DRAFT-only authoring**; a narrative entry is never written on an `APPROVED`/`FINAL` version (enforced application-side + by the version-immutability guard) |

**Uniqueness:** `UNIQUE (report_version_id, requirement_version_id, narrative_kind)` — one current entry per requirement+kind (upsert semantics, mirroring B1's value upsert).
**Hard rules:** no `CHECK` on length beyond non-empty (`A3`: no arbitrary character limits); no trigger; no retention artefact (the B2-D11/posture analogue); the table never references or writes `calculation_snapshots`, `emissions_logs`, `emission_factors`, `customer_factors` or any provenance object.

### 7.2 Domain rules (enforce in the domain layer, test-locked)

1. **Binding required:** an entry must name a `requirement_version_id`; there is **no** report-wide narrative path (`A1`).
2. **Authoring roles:** organisation **Owner/Admin** only (`A1`, `P3`, D5) — Members/Viewers are denied; PE staff and CarbonTally internal staff are denied.
3. **Never authoritative:** the narrative can never alter `disclosure_values`, provenance or factor data (`P3`) — enforced by the absence of any such write path.
4. **No arbitrary limits:** reject only empty/whitespace bodies; any length/format limit must be traceable to authoritative evidence (`A3`).
5. **Plain text:** markup/script content is rejected at the API boundary.
6. **Immutability:** authoring is impossible once the version is `APPROVED`/`FINAL` (`D15`; the S1/S3 `assert_report_version_mutable` guard).

## 8. Finalisation gate (deliverable C — RATIFIED by `DM-5`)

The gate is the ratified rule, implemented literally:

1. Gather the version's `disclosure_values` with `effective_class = 'REQUIRED'`.
2. `value_status = 'RESOLVED'` → satisfied.
3. `effective_class = 'CUSTOMER_INPUT_REQUIRED'` and unresolved → **BLOCK finalisation** unless an approved resolving workflow supplied the input.
4. `effective_class = 'NOT_SUPPORTED'` and applicable+required → **SURFACE the limitation honestly**; never silently omit, never present as satisfied, and never block-and-hide.
5. The two states are **never collapsed** (`DM-5` §8 of the record).

**Output shape:** `{ can_finalise: bool, blocking: [...], surfaced_limitations: [...] }` with a reason per item — no opaque boolean.

## 9. Drill-down exposure (deliverable D — RATIFIED by `DM-6`)

| Actor | Depth |
|---|---|
| Customer Owner/Admin | full authorised chain (Disclosure → Calculation → Evidence line → Source document/line), as far as evidence granularity exists |
| Customer Member | read of the disclosure set; drill-down **not** widened by this contract |
| Viewer | **controlled** (not full) — the API must not expose the full chain to a Viewer |
| Consultant | bounded to engagement scope; never widened |
| PE / internal staff | **denied** |
| Cross-tenant | **denied** |

The B2 value→line read model delivered in B3 is the mechanism; B4 adds only the **role-aware exposure rule** and the finalisation/approval context. `DM-6`'s acceptance criterion (ALLOW **and** DENY tests) is part of gate V4.

## 10. Approval workflow (deliverable E — **[DECISION REQUIRED]**)

The lifecycle spec records the following as **open** (`P4`–`P7`, `A2`, `A4`–`A6`, `A9`). They are registered as **`B4-D1…B4-D4`** and must be ruled by the PO before the approval/finalisation implementation is written:

* **approver authority** (`P4`, `A2`) — who may approve/finalise (and whether consultants or internal staff may ever do so; the recommendation is **no** to both for staff);
* **post-approval change invalidation** (`P5`) and **revocation** (`A6`);
* **review gate** (`A4`, `A5`) — is review a required state before approval, one-step or two-step;
* **comments** (`A7`, `A9`, `B4-D9`) — visibility split, whether unresolved change-requests block approval, and whether the dormant `report_comments` is activated.

Nothing in this section is implemented until ruled.

## 11. Frozen artefact (deliverable F — **[DECISION REQUIRED]**)

The lifecycle spec's §19 analysis and §37.2 record: **is a frozen final PDF mandatory** (`P6`), **where does it live**, **what is hashed**, and how is immutability enforced? Also recorded as outstanding: *"Storage plan for the frozen artefact (private bucket, naming, lifecycle) — NOT DEFINED"*.

Design constraints that any ruling must satisfy (non-negotiable, from ratified material):

* the artefact is **immutable** once produced, bound to one `report_version_id`;
* its **content hash** is recorded (the lifecycle spec's §19.4 "hashing question" is a material finding);
* storage is **private** and org-scoped; a signed URL is sensitive and never logged (AGENTS.md §68);
* production/storage configuration changes require separate authorisation;
* no external AI/LLM may touch the artefact.

Registered as **`B4-D5…B4-D7`**.

## 12. Retention (deliverable G — **[DECISION REQUIRED]**)

* Retention is **configurable and server-side** (N3) and must **never** weaken auditability, evidence or regulatory traceability.
* The lifecycle spec records legal review of report-version/artefact retention as **OUTSTANDING** (`A10`, §28.4).
* Registered as **`B4-D8`**. No retention duration is invented here.

## 13. Historical immutability and reproducibility (RATIFIED)

* `APPROVED`/`FINAL` versions are immutable (S1/S3, `D15`); B4 must not rewrite, re-project or back-fill them.
* Narrative and frozen artefacts bind to `report_version_id` (+ `requirement_version_id` for entries) so a historical report is reproducible exactly as approved.
* No retro-writing of narrative for past versions; no silent replacement of an artefact.

## 14. Authorization / RLS (RATIFIED posture)

* New table(s): RLS **enabled**; `anon` revoked; org-member read; **Owner/Admin write**; PE denied; no cross-tenant visibility — identical to the B1/B2/B3 pattern.
* Server-side authorization on every write; the UI is never the boundary.
* No `FORCE RLS`; no production RLS remediation; `A-RLS` remains a separate open decision.

## 15. Audit (RATIFIED)

Reuse the canonical append-only `audit_trail` (no new mechanism): `narrative.created` / `narrative.updated` / `narrative.superseded`, `report.finalised`, `report.artefact.frozen`, `report.downloaded` (per `A11` once ruled). No secrets, tokens or signed URLs in any payload.

## 16. API / service responsibilities (deliverable J)

| Endpoint (proposed) | Method | Who | Notes |
|---|---|---|---|
| `/api/v3/reports/{report_id}/narrative` | GET | org member | requirement-bound entries for the current version |
| `/api/v3/reports/{report_id}/narrative/{requirement_version_id}` | PUT | Owner/Admin | upsert one requirement's narrative (DRAFT versions only) |
| `/api/v3/reports/{report_id}/finalisation-check` | GET | org member | the §8 gate output (blocking + surfaced limitations) |
| `/api/v3/reports/{report_id}/finalise` | POST | **per `B4-D1`** | transitions the version once the gate passes |
| `/api/v3/reports/{report_id}/artefact` | GET | org member (signed URL issued server-side after authorization) | the frozen artefact, per `B4-D5…D7` |

Rules: no endpoint writes a calculated value; unknown requirement/version → meaningful 4xx; absent artefact → meaningful 404.

---

## 17. Test / verification contract (deliverable K/L)

| Layer | Content |
|---|---|
| Static | migration guards (RLS enabled, additive-only, guarded constraints, no destructive statement); no narrative write path to any authoritative object |
| Pure/unit | narrative binding required; markup rejection; empty-body rejection; **no arbitrary length constant** (`A3`); finalisation gate matrix (RESOLVED / CUSTOMER_INPUT_REQUIRED / NOT_SUPPORTED / NOT_APPLICABLE / UNDETERMINED); the two limitation states never collapsed |
| Runtime (QA/clone) | migration apply + re-apply (`rc=0`, zero schema delta); upsert idempotency; DRAFT-only authoring; immutability after `APPROVED`/`FINAL`; artefact immutability and hash reproducibility (once `B4-D5…D7` are ruled) |
| Security | Owner/Admin ALLOW; Member/Viewer write DENY; PE and internal staff DENY; cross-tenant DENY; Viewer drill-down controlled; `DM-6` ALLOW **and** DENY matrix |
| Regression | B3 (41) + B3 V3 (9) + B1/B2 (36 + 75) + S1/S3 (89) suites remain green |

**Gate V4** is the independent verification of the above on a fresh clone (the V3 method), producing its own report; **a skipped suite is never a PASS**, and the verification is executed, not asserted.

## 18. Migration strategy

| # | Migration | Shape |
|---|---|---|
| B4-1 | `20260918000000_p8_b4_narrative_overlay.sql` | the §7.1 table + constraints + indexes + RLS policies (implementable now — policy ratified) |
| B4-2 | `…_p8_b4_artefact.sql` | artefact metadata/storage binding — **only after `B4-D5…D7`** |

Ordering strictly after B3's `20260917010000`. Additive-only, idempotent, non-production first; documented rollback by dropping the new table(s) (nothing pre-existing is rewritten).

## 19. Environment and deployment

* Implement and verify on `carbontally_qa_phase8`; independent verification on a fresh clone (V3 method).
* **Production prohibited** (G0-D open). **Backfill prohibited.** No storage configuration change without separate authorisation.

## 20. Decision register (`B4-Dn`)

| ID | Decision | Status | Basis / recommendation |
|---|---|---|---|
| **B4-D1** | **Approver authority** for report approval/finalisation (and whether consultants or CarbonTally staff may ever approve) | **OPEN — PO DECISION REQUIRED** | lifecycle spec `P4` recommends **Owner + Admin**; `A2` recommends **no** consultant/staff approval; `A1` already fixes *authoring* to Owner/Admin |
| **B4-D2** | Post-approval change invalidation (`P5`) and approval **revocation** (`A6`) | **OPEN** | spec recommends: **any post-approval edit invalidates approval and requires re-approval**; revocation permitted before finalisation with a recorded reason, never after |
| **B4-D3** | Review gate: is `REVIEWED` mandatory before approval; one-step or two-step (`A4`, `A5`) | **OPEN** | spec recommends keeping review a required state, auto-review allowed by org policy; two-step where >1 authorised actor |
| **B4-D4** | Comments: activate the dormant `report_comments`? visibility split? do unresolved change-requests block approval (`A7`, `A9`, `B4-D9`) | **OPEN** | spec recommends a visibility split and yes-to-blocking; the table is currently dormant |
| **B4-D5** | Is a **frozen final artefact mandatory** (`P6`)? | **OPEN** | spec recommends **YES** (the frozen model is the integrity anchor) |
| **B4-D6** | Frozen artefact **storage model** (private bucket/path/naming/lifecycle) | **OPEN** | explicitly recorded as **NOT DEFINED**; storage config change needs its own authorisation |
| **B4-D7** | **Hashing** model for the artefact (content hash only vs artefact + content) and metadata | **OPEN** | lifecycle spec §19.4 records a material hashing finding; the plan's `B4-PO-3` |
| **B4-D8** | **Retention** for report versions and frozen artefacts (`A10`), beyond the N3 configurable mechanism | **OPEN** | legal review **OUTSTANDING**; no duration may be invented |
| **B4-D9** | Activation of `report_comments` / comment lifecycle (part of `B4-D4`) | **OPEN** | dormant table; activating it is a scope decision |
| **B4-D10** | Batch allocation: does B4 absorb **S4 (narrative)** and **S5 (frozen artefact)**, and where do **S6 (UI)** and **S7 (security/regression tests)** live? | **OPEN — PO DECISION REQUIRED** | plan `D-14`; roadmap §20 places narrative + frozen artefact in B4 but does not allocate S6/S7 |
| **B4-D11** | Download audit (`A11`) and staleness flag + "data as of" (`A12`), drill-down exposure of evidence to the reader (`A13`) | **OPEN** | recommendations: audit downloads **yes**; flag stale, never auto-invalidate; expose drill-down subject to the viewer's authorization |
| **B4-D12** | Entitlement/billing gating of finalisation (`A14`) | **OPEN** | recorded as out of scope for the lifecycle spec; `usage_tracking.reports_generated` exists but is never incremented (E31) |
| **B4-D13** | Narrative binding requires a `requirement_version_id`; no report-wide narrative; Owner/Admin authoring; no arbitrary limits; plain text | **RATIFIED** | `A1`, `A3`, `P3` |
| **B4-D14** | Finalisation semantics: unresolved required `CUSTOMER_INPUT_REQUIRED` blocks; required `NOT_SUPPORTED` is surfaced, never masked; never collapsed | **RATIFIED** | `DM-5` |
| **B4-D15** | Drill-down depth per role (Owner/Admin full; Viewer controlled; Consultant bounded; PE/cross-tenant denied) | **RATIFIED** | `DM-6` |
| **B4-D16** | Historical immutability: approved/final versions and their narrative/artefacts are never rewritten | **RATIFIED** | `D15`, `DM-7`, S1/S3 |
| **B4-D17** | Narrative strategy for B4 is **deterministic/template-first only**; AI narrative remains S8 and outside B4 | **DECIDED (this contract)** | plan `B4-PO-8`; S8 is explicitly separate and gated on unmet AI safety preconditions |
| **B4-D18** | No triggers; app-layer validation; no retention artefact on the new table | **DECIDED (this contract)** | the B2-D11/B3-D10 posture |
| **B4-D19** | RLS posture on new objects (member read / Owner-Admin write / PE denied / no FORCE RLS) | **DECIDED (this contract)** | the B1/B2/B3 pattern |

**Genuinely open PO decisions: `B4-D1…B4-D12`** (with `B4-D10` a batch-boundary decision). **`B4-D13…B4-D19` are ratified or contract-decided**, so deliverables A, B, C, D, H, I, K and the narrative part of J are **implementable now**.

## 21. Acceptance criteria (gate **V4**)

| # | Criterion |
|---|---|
| A1 | B4 migrations apply and re-apply (`rc=0`) with zero schema delta on a fresh clone |
| A2 | Pre-existing objects unchanged (parity; zero removed lines) |
| A3 | Narrative is requirement-bound: no report-wide narrative path exists |
| A4 | Owner/Admin can author; Member/Viewer/PE/internal staff cannot (ALLOW **and** DENY) |
| A5 | No narrative write path reaches a calculated value, provenance or factor object |
| A6 | Finalisation gate: `CUSTOMER_INPUT_REQUIRED` blocks; `NOT_SUPPORTED` is surfaced; the two are never collapsed |
| A7 | Authoring is impossible on an `APPROVED`/`FINAL` version (immutability) |
| A8 | Drill-down follows `DM-6` per role, with cross-tenant/PE denial proven |
| A9 | Artefact (once ruled) is immutable and hash-reproducible |
| A10 | Every B4 write is audited; no secrets in payloads |
| A11 | No regression: B3 (41) + V3 (9) + B1/B2 (111) + S1/S3 (89) suites stay green |

## 22. Verdict

### `B4 CONTRACT COMPLETE — 12 PO DECISIONS REQUIRED (B4-D1…B4-D12); NARRATIVE + FINALISATION SPINE RATIFIED AND IMPLEMENTABLE NOW`

B4 is fully specified. The narrative overlay, its authorization posture, the `DM-5` finalisation gate, the `DM-6` drill-down rules, audit and the test/verification contract are all governed by **already-ratified** decisions, so implementation can begin without waiting. The approval workflow, frozen-artefact model, retention and the S4/S5/S6/S7 allocation require PO rulings (`B4-D1…B4-D12`), which are raised in the compact format as they block.

---

## 23. Amendment 1 — `B4-D1` ANSWERED by PO (2026-09-13)

> **PO ruling:** **Option A approved.** Customer **Owner and Admin** may approve/finalise a customer report version. **Consultants and CarbonTally internal staff may never approve or finalise** a customer report version.

The ruling is recorded verbatim as the authoritative decision **`B4-D1`**, and it is **not** to be reinterpreted as granting approval authority to consultants or internal staff.

### 23.1 Status change

| ID | Was | Now |
|---|---|---|
| **`B4-D1`** | OPEN — PO DECISION REQUIRED | **DECIDED — PO RATIFIED (Option A)** |
| `B4-D2` post-approval invalidation / revocation | OPEN | OPEN |
| `B4-D3` review gate | OPEN | OPEN |
| `B4-D4`/`B4-D9` comments | OPEN | OPEN |
| `B4-D5…D8` artefact/retention | OPEN | OPEN |
| `B4-D10` S4/S5/S6/S7 allocation | OPEN | OPEN (next question) |

### 23.2 What this authorises and what it does not

* **Authorises:** enforcement of a finalisation/approval boundary in which organisation Owner/Admin act, matching the authority already used by the S3 lifecycle transitions and the `A1` narrative-authoring set.
* **Does not authorise:** consultants or CarbonTally internal staff approving/finalising; any bypass of the `DM-5` finalisation gate; any change to the S3 state machine; production deployment; the Class-1 backfill.
* **Not decided here:** `B4-D2` (does a post-approval edit invalidate approval / may an approval be revoked?), which remains open and is raised separately.

---

## 24. Amendment 2 — `B4-D10` ANSWERED by PO (2026-09-13)

> **PO ruling:** **Option A approved.** B4 **absorbs S4 (narrative)** and **S5 (frozen artefact)**; **S7 (regression/security verification) stays inside B4 and is included in gate V4**; B4 does **not** absorb **S6 (frontend lifecycle UI)**.

S6 remains a separate Phase 8 / Phase 8-X backlog item, to be implemented against the **ratified B4 lifecycle APIs** once the frozen-artefact model and related decisions are settled.

### 24.1 Status change

| ID | Was | Now |
|---|---|---|
| **`B4-D10`** | OPEN — PO DECISION REQUIRED | **DECIDED — PO RATIFIED (Option A)** |
| `B4-D2` post-approval invalidation/revocation | OPEN | OPEN |
| `B4-D3` review gate | OPEN | OPEN |
| `B4-D4`/`B4-D9` comments | OPEN | OPEN |
| `B4-D5` frozen artefact mandatory | OPEN | OPEN (**next blocking item — S5 is now confirmed in B4**) |
| `B4-D6`/`B4-D7` artefact storage/hashing/immutability | OPEN | OPEN |
| `B4-D8` retention/deletion | OPEN | OPEN |
| `B4-D11` download audit / staleness flag | OPEN | OPEN |
| `B4-D12` entitlement gating of finalisation | OPEN | OPEN |

### 24.2 What this authorises and what it does not

* **Authorises:** S4 and S5 as B4 scope; **S7 negative/regression testing as part of B4 verification and gate V4** — i.e. the security/regression tests are *not* deferred and acceptance of B4 is not possible without them.
* **Does not authorise:** any S6 frontend lifecycle UI work inside B4; deferral of security/regression testing; production deployment; the Class-1 backfill.
* **Still blocking S5:** the frozen-artefact model (`B4-D5…D7`) — storage location/bucket, naming, hashing algorithm(s), immutability enforcement, and the retention interaction (`B4-D8`).

---

## 25. Amendment 3 — `B4-D5`/`B4-D6`/`B4-D7` ANSWERED by PO (2026-09-13)

> **PO ruling:** **Option A approved.** The frozen artefact is **mandatory** at finalisation; finalisation **must fail** if the immutable PDF cannot be produced and stored. It is stored in a **private** Supabase Storage bucket (`report-artifacts`), never publicly accessible; object key `{organization_id}/{report_id}/{version_id}.pdf`; access only through **short-lived signed URLs** issued after normal authorization. A new **append-only** `report_version_artifacts` table holds **exactly one** record per finalised report version, recording **SHA-256**; the object key and hash are **immutable and never updated**; immutability is enforced by the append-only record plus the version's `FINAL` state; corrections create a **new version**; the live-render route is retained for **DRAFT versions only** (`A15`). **SHA-512, MD5 fallback, optional artefacts, external storage and any FINAL-without-artefact exception path are expressly forbidden.**

### 25.1 Status change

| ID | Was | Now |
|---|---|---|
| **`B4-D5`** frozen artefact mandatory | OPEN | **DECIDED — PO RATIFIED (Option A)** |
| **`B4-D6`** storage/bucket/key/single-record | OPEN | **DECIDED — PO RATIFIED** |
| **`B4-D7`** SHA-256 + immutability enforcement | OPEN | **DECIDED — PO RATIFIED** |
| `B4-D8` retention/deletion for versions and artefacts | OPEN | OPEN — **must be raised as its own PO decision after this increment (no invented duration)** |
| `B4-D2`/`B4-D3`/`B4-D4`/`B4-D9`/`B4-D11`/`B4-D12` | OPEN | OPEN |

### 25.2 Constraints honoured

Preserved S1/S3 lifecycle semantics and the ratified Owner+Admin authority (`B4-D1`). No B3 authoritative value, provenance, factor or calculation change. No production access or production storage write; migrations applied only in the persistent non-production QA environment. RLS/authorization remains fail-closed. No retention duration invented. Phase 8-X remains inside Phase 8; **no Phase 9**. No commit or push.

---

## 26. Amendment 4 — `B4-D8` ANSWERED by PO (2026-09-13)

> **PO ruling:** **Option A approved.** Report versions and frozen artefacts are **retained indefinitely** for now. **B4 introduces NO deletion path** for either. **No finite retention duration is invented or hard-coded.** Retention remains **configurable and server-side**, to be established later through the **Settings/Admin control plane**. Any future retention/deletion mechanism **must not** weaken auditability, evidence, regulatory traceability, or the immutability of `FINAL` artefacts. **No scheduled deletion job and no automatic expiry in B4.** The append-only/immutable artefact model ratified under `B4-D5/D6/D7` is **not** altered.

| ID | Was | Now |
|---|---|---|
| **`B4-D8`** retention/deletion | OPEN | **DECIDED — PO RATIFIED (Option A: retain indefinitely)** |

---

## 27. Amendment 5 — dispositions for `B4-D2`, `B4-D3`, `B4-D11`, `B4-D12` (2026-09-13)

PO instruction: apply the existing contract recommendations **where they are already ratified**, and stop only at a genuine unresolved decision.

| ID | Disposition | Basis | Evidence |
|---|---|---|---|
| **`B4-D2`** post-approval invalidation / revocation | **SETTLED BY THE RATIFIED SPINE — no new product decision** | `D15`/`DM-7` (approved/final content and artefacts are never rewritten), the ratified S3 state machine (from `APPROVED` the only forward action is `FINALIZE`; there is **no** revocation transition, so corrections require a **new version**), and `B4-D5/D6/D7` (the frozen artefact is immutable) | runtime: `test_frozen_artefact_survives_a_new_version` proves the FINAL artefact is byte-identical after version 2 is created and the new draft has no artefact; `test_finalise_refused_when_existing_artefact_hash_differs` proves a changed render is refused |
| **`B4-D3`** review gate | **SATISFIED BY S3 — no change needed** | the ratified lifecycle blocks approval from any state other than `REVIEWED`; an unreviewed version cannot be approved or finalised | `test_state_machine_refuses_invalid_transition` (DRAFT → approve ⇒ 409, no transition attempted) |
| **`B4-D11`** download audit + staleness flag | **APPLIED per the contract recommendation** | auditability is a ratified principle (AGENTS §4/§77; B1/B2 use the existing append-only `audit_trail` — **no new audit table**); the contract recommends auditing downloads, flagging staleness, and never auto-invalidating; drill-down exposure is already `DM-6` | audit: `frozen_artefact.created` and `frozen_artefact.signed_url_issued` entries (payload = object key/hash/TTL, **never** the signed URL); staleness: `artefact_status` reports `data_as_of` + `stale` and states that it never auto-invalidates. Runtime: `test_signed_url_is_audited_without_recording_the_url`, `test_staleness_is_reported_and_never_auto_invalidates` |
| **`B4-D12`** entitlement/billing gating of finalisation | **OUT OF SCOPE FOR B4 — recorded, not implemented** | the lifecycle spec records it as outside lifecycle scope; `usage_tracking.reports_generated` is unused (E31); gating finalisation commercially is a commercial-policy decision that must come from the PO before any code | none (deliberately no code) |

### 27.1 The one genuinely open item

**`B4-D4` / `B4-D9` — comments:** the `report_comments` table exists but is dormant, and the lifecycle spec marks comment authoring/visibility (`A7`) as `PO DECISION REQUIRED`. Whether report comments are in B4 scope at all, and who may see whose comments, is a genuine product/governance decision — raised to the PO rather than invented.

All the other ratified-register entries (`B4-D13…B4-D19`) and answered entries (`B4-D1`, `B4-D5`, `B4-D6`, `B4-D7`, `B4-D8`, `B4-D10`) are implemented as recorded.

---

## 28. Amendment 6 — `B4-D4`/`B4-D9` ANSWERED by PO (2026-09-13)

> **PO ruling:** **Option A approved.** Report comments remain **outside B4**. No comment authoring or comment-reading API is implemented in B4; no comment UI is added or modified as part of B4; the existing `report_comments` schema **remains dormant**; the unresolved **`A7` comment-visibility policy is neither invented nor partially implemented**. The dormancy and the open `A7` decision are recorded **against the S6 backlog item**, which will decide and implement comment scope/visibility together with the frontend lifecycle UI, against the **already-ratified B4 lifecycle APIs**. **`B4-D4`/`B4-D9` is therefore CLOSED with no new B4 comment surface.**

| ID | Was | Now |
|---|---|---|
| **`B4-D4`** comments in scope | OPEN | **CLOSED — PO RATIFIED (Option A: outside B4)** |
| **`B4-D9`** comment visibility (`A7`) | OPEN | **CLOSED — deferred to the S6 backlog item; not invented here** |

### 28.1 S6 backlog record (created by this decision)

| Item | Detail |
|---|---|
| Backlog item | **S6 — frontend lifecycle UI** (explicitly **not** absorbed by B4, per `B4-D10`) |
| Carried obligations | (1) decide + implement comment scope and **`A7` visibility**; (2) build the lifecycle UI against the ratified B4 APIs (`finalisation-check`, `approve`, `finalise`, `frozen-artefact`, `frozen-artefact/signed-url`, narrative read/write); (3) surface the `DM-6` drill-down depth and `DM-5` surfaced limitations honestly; (4) present the frozen-artefact hash/staleness metadata that B4 already returns |
| Current state of `report_comments` | **dormant** (present in the initial schema; never written by any B4 or B-phase code path) |
| B4 obligation | none — recorded only |
