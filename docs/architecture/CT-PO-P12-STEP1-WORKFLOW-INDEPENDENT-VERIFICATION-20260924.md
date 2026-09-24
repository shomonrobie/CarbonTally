# CT-PO-P12-STEP1-WORKFLOW-INDEPENDENT-VERIFICATION-20260924

**Reference:** `CT-PO-P12-STEP1-WORKFLOW-INDEPENDENT-VERIFICATION-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-WORKFLOW-INDEPENDENT-VERIFICATION` — **STEP 1**, workstream **1.2**
**Repository:** `/home/shomonrobie/ct_93d5cdd` @ `3c38cbc59c95c04ea434ae128f86c94fd4b69190`, branch `p8-release-reconciled`
**Status:** STEP-1 DELIVERABLE — independent verification record
**Verifier role:** **verifier only. No defect was fixed.**
**Production deployment:** **NOT AUTHORIZED**

---

## 1. Executive position (read this first)

**The verifier role in Step 1 is explicitly non-fixing and non-mutating.** The
workplan §1.2 states the verifier must not fix defects, and §3 of the task
methodology authorizes read-only inspection, forensic analysis, reconciliation,
independent verification and report creation — while explicitly excluding Demo Lab
reset, destructive database operations, evidence backfill and production access,
and §10 restricts execution to tests relevant to the verification work.

Consequently this report deliberately distinguishes three verification strengths,
and **never upgrades one into another**:

| Strength | Meaning | Used where |
| --- | --- | --- |
| `RUNTIME-VERIFIED (EXERCISED)` | The workflow was actually exercised against a live environment and the outcome observed | **Nowhere in this session** — see §2 |
| `DATA-VERIFIED` | The persisted state that the workflow consumes/produces was read directly from the database | Most planes below |
| `CODE-TRACED` | The route, guard and repository path were read in the release source | All planes below |
| `TEST-VERIFIED (UNIT)` | A non-database automated test that asserts the behaviour passed in this session | §9 |

**Honest headline:** in this session the verifier could establish **what exists and
what the data permits**, and **what the code enforces** — but it could **not**
exercise the workflows end-to-end, because the release backend is not running and
the available automated integration harness is destructive by construction. Those
two facts are environment limitations, **not** product results. Every untested plane
is therefore reported as **UNVERIFIED**, not as passing.

---

## 2. Environment constraints (what limited verification)

| Constraint | Detail | Evidence |
| --- | --- | --- |
| Release backend not running | `127.0.0.1:8070` refused connections; only the Demo Lab gateway (`54430`), the stack DB (`54426`) and the demo-lab containers were listening | `ss -ltnp`; `curl` → `000` |
| Demo Lab harness needs the backend | `tools/demo_lab/verify.py` performs password grants and read-only GET probes **against the release API**; with no backend it cannot run | `verify.py` docstring/README §5 |
| Integration harness is destructive | `backend/tests/integration/conftest.py` runs `TRUNCATE … RESTART IDENTITY CASCADE` on its target (PO control **F-046-1**), so it must only ever be pointed at a disposable clone or `carbontally_test` | `conftest.py` lines 46–139 |
| Step-1 read-only boundary | Demo Lab mutation, destructive database operations and evidence backfill are **not authorized** in Step 1 | workplan §7 |
| Workflow exercise requires mutation | Assigning a work item, sending a message, approving a report version and creating a facility are all **writes** | inherent |

**Therefore:** the verification performed here is `DATA-VERIFIED` +
`CODE-TRACED` + `TEST-VERIFIED (UNIT)`, and every end-to-end workflow is recorded
as **UNVERIFIED — requires an authorized live/destructive-capable environment
as **UNVERIFIED — requires an authorized live/destructive-capable environment
session (Step 2 / Step 4)**.

---

## 3. Verification matrix (summary)

| Plane | Exists in release? | Enforceable boundary verified in code? | Demonstrable from current data? | End-to-end exercised? | Step-1 result |
| --- | --- | --- | --- | --- | --- |
| PE assignment / reassignment / release | **YES** | YES (`work_item_assignments` lease + guards) | **NO** (0 assignment rows) | **NO** | **UNVERIFIED (no data)** |
| PE workspace visibility | **YES** | YES (`work_item_effective_entity`, entity-scoped) | **NO** (0 assigned items) | **NO** | **UNVERIFIED (no data)** |
| Messaging — organisation plane | **YES** | YES (org member / ACTIVE consultant grant / server-resolved support) | **NO** (0 conversations, 0 messages) | **NO** | **UNVERIFIED (no data)** |
| Messaging — PE operational plane | **YES** | YES (`is_staff` + active entity; Operations needs `can_manage_staff`) | **NO** (1 such conversation exists only in `postgres`) | **NO** | **UNVERIFIED (no data)** |
| Messaging — customer↔PE | **NO — does not exist** | n/a (D18 boundary is absolute) | n/a | n/a | **CONFIRMED ABSENT BY DESIGN** |
| Consultant/client relationship | **YES** | YES (`ensure_consultant_org_access`, ACTIVE grant) | **PARTIAL** (4 orgs, 2 firm members) | **NO** | **PARTIAL / UNVERIFIED END-TO-END** |
| Reporting lifecycle | **YES** | YES (`DRAFT→REVIEWED→APPROVED→FINAL`, expected-state guard, FINAL terminal) | **NO** — every candidate version is `DRAFT` | **NO** | **UNVERIFIED (no non-DRAFT state exists)** |
| Master-data CRUD | **YES** | YES (org-scoped repositories) | **NO** (0 facilities/assets/suppliers in the lab) | **NO** | **UNVERIFIED (no data)** |
| Authorization / tenant isolation | **YES** | YES | **NOT RE-RUN** (last recorded harness run: 0/18 isolation failures) | **NO** | **PARTIAL** |
| Demo Lab harness usability | **YES** | n/a | state dir + 14 prior runs present | **NO** (backend down) | **PARTIAL** |

---

## 4. Processing-entity plane

### 4.1 What exists (`CODE-TRACED`)

`backend/api/v3_pe.py` (prefix `/api/v3/pe`) exposes:

```text
GET  /me
GET  /work                                   # the entity's work queue
GET  /batches/{batch_id}/items
GET  /items/{item_id}/workspace
GET  /items/{item_id}/work
POST /items/{item_id}/work/claim
POST /items/{item_id}/work/release
POST /items/{item_id}/work/complete
POST /items/{item_id}/start | extract | map | validate | calculate | status
POST /items/{item_id}/pe-review | pe-qc | clarify
GET  /issues | /issues/{issue_id} | /team
```

Assignment/reassignment for internal operations lives in
`backend/api/v3_operations.py`:

```text
POST /api/v3/ops/batches/{batch_id}/assign
POST /api/v3/ops/items/{item_id}/work/claim | assign | reassign | recover | release | complete
GET  /api/v3/ops/review/{review_id}/... ; POST /api/v3/ops/review/{review_id}/assign | complete
```

Persistence: `public.work_item_assignments` (`data/manual_extraction.py` maintains
insert/update/lease/recovery paths). Additional PE/assignment tables present in the
lab schema: `processing_assignments`, `reassignment_history`,
`review_assignment_history`, `processing_audit_trail`.

### 4.2 What the data permits (`DATA-VERIFIED`)

| Environment | `work_item_assignments` | `processing_assignments` | `reassignment_history` | `processing_entities` |
| --- | --- | --- | --- | --- |
| `carbontally_demo_local` | **0** | 0 | 0 | 1 |
| `postgres` | **2** | 0 | 0 | 11 |

**Conclusion:** the PE assignment/reassignment/release capability is
**implemented and code-verifiable**, but **there is no assignment state to
demonstrate** in the Demo Lab, and the historical dataset contains only 2 rows.
Partial release/completion and reassignment **cannot** be shown from current data.

---

## 5. Messaging planes

### 5.1 Who can send / who can receive (`CODE-TRACED`, `backend/api/v3_messaging.py`)

| Plane | Endpoints | Sender authorization | Recipient/participant resolution | Cross-tenant guarantee |
| --- | --- | --- | --- | --- |
| **Organisation (customer/consultant ↔ client)** | `POST/GET /api/v3/messaging/conversations`, `…/{id}/messages`, `…/{id}/read` | organisation members (`require_org_member` / `ensure_org_access`); **or** consultant firm members holding an **ACTIVE** consultant-client grant (`ensure_consultant_org_access`) | participants are server-created; an optional `counterparty="support"` causes the server to add **one** authorised internal support/admin (staff role granting `can_manage_staff`). The client **never** supplies a staff identity, and any other value is **422** | Yes — conversation is bound to `organization_id`; consultants must hold an active grant for *that* organisation |
| **PE operational (PE ↔ CarbonTally Operations)** | `GET/POST /api/v3/messaging/entity-conversations`, `…/{id}/messages`, `…/{id}/read` | `_resolve_entity_actor`: caller must be **staff** (`is_staff`) and either (a) have an **active** `processing_entity_id` (PE member), or (b) be internal staff holding `can_manage_staff` (**Operations**) | PE members are forced to their **own** entity id — a client-supplied entity id is never trusted for PE callers; Operations may target any active entity | Yes — conversation bound to `processing_entity_id`; PE A cannot act for PE B |
| **Customer ↔ PE** | — | **does not exist** | — | D18 boundary is absolute; the platform deliberately provides no such plane |

### 5.2 Persistence and state (`DATA-VERIFIED`)

`conversations` carries `conversation_kind` (`org` / `entity`) and
`processing_entity_id`; messages live in `public.messages` with
`conversation_participants`.

| Environment | `conversations` | `conversation_kind` split | `messages` | `conversation_participants` |
| --- | --- | --- | --- | --- |
| `carbontally_demo_local` | **0** | — | **0** | 0 |
| `postgres` | 36 | `org 35`, `entity 1` | 54 | 65 |

**Conclusion:** both messaging planes are **implemented with server-side
authorization** and are demonstrable in principle, but **neither plane has any data
in the Demo Lab**, and the historical dataset holds only a single PE-operational
conversation. Messaging **cannot** be demonstrated end-to-end today.

### 5.3 Documentation divergence found (`CONFIRMED`)

The module docstring asserts *"General employees and Processing Entity staff never
get messaging access (entity staff are neither org members nor consultants; RLS has
no entity messaging storey) — the D18 boundary is absolute (D19 §17)"*, while the
same module implements PE operational messaging for active PE members and migration
`20260902040000_phase5_pe_operational_messaging.sql` exists. Recorded as divergence
**D-09** in the Documentation Reconciliation report. **Not fixed** (verifier rule).

---

## 6. Consultant / client relationship

`CODE-TRACED`: `backend/api/v3_consultants.py` + `api/consultant_auth.py`
(`ensure_consultant_org_access`), with `consultant_firm_members`,
`consultant_clients`, and grants carrying an ACTIVE state (D15). A consultant
operates a client organisation **only** through an active grant for that specific
organisation.

`DATA-VERIFIED` (Demo Lab): `organizations = 4` (Org A, Org B, Client A, Client B —
matching the harness manifest's declared topology), `consultant_firm_members = 2`,
`organization_members = 8`, `users = 13`.

**Result: PARTIAL.** The relationship model and its enforcement point are verified
in code and the topology exists in data; the *behaviour* (consultant operating a
client workspace, a grant being revoked) was **not exercised** in this session.

---

## 7. Reporting lifecycle

`CODE-TRACED`:

```text
docstring:  status moves DRAFT → REVIEWED → APPROVED → FINAL under server-side
            guards, with CHANGES_REQUESTED / REJECTED review outcomes and
            supersession by a new DRAFT version after approval/finalisation
routes:     POST /api/v3/reports/{id}/versions/{n}/submit
            POST /api/v3/reports/{id}/versions/{n}/request-changes
            POST /api/v3/reports/{id}/versions/{n}/reject
            POST /api/v3/reports/{id}/versions/{n}/approve
            POST /api/v3/reports/{id}/versions/{n}/finalize
            POST /api/v3/reports/{id}/versions        (new DRAFT version)
            GET  /api/v3/reports, /{id}, /{id}/content, /{id}/versions,
                 /{id}/download, /{id}/pdf
tests:      tests/integration/test_report_lifecycle.py — draft default, guarded
            transition updates only the expected state, per-report version
            isolation, unratified status rejected before write, check-constraint
            blocks unratified state, FINAL is terminal for the guard
```

`DATA-VERIFIED`:

| Environment | `report_versions` | states present | `report_generation_queue` |
| --- | --- | --- | --- |
| `carbontally_demo_local` | 2 | **`DRAFT` × 2** | 3 × `completed` |
| `postgres` | 17 | **`DRAFT` × 17** | `completed 11`, `failed 2`, `pending 1` |

**Result: UNVERIFIED END-TO-END, and NOT DEMONSTRABLE.** The state machine, its
guards and its tests exist; **no non-`DRAFT` report version exists in any candidate
environment**, so an approval/rejection/finalisation screen cannot be shown from
real records. (This is new evidence: divergence **D-07**.)

---

## 8. Master-data CRUD

`CODE-TRACED`: route families exist for organisations, facilities, assets, suppliers
and vehicles (`api/v3_organizations.py`, `api/v3_suppliers.py`, `api/v3_vehicles.py`,
`api/v3_emissions.py`), plus D17 master-data migration(s). The D17 investigation also
shows an org-scoped ownership model (`test_d17_provider_ownership_migration_revision.py`).

`DATA-VERIFIED`:

| Environment | `facilities` | `assets` | `suppliers` |
| --- | --- | --- | --- |
| `carbontally_demo_local` | **0** | **0** | **0** |
| `postgres` | 157 | 310 | 156 |

**Result: UNVERIFIED END-TO-END, and NOT DEMONSTRABLE in the Demo Lab.** Only the
CRUD *surface* is verified; no facility/asset/supplier exists to read, edit or relate.
The preflight's `X-5`-family concern about raw UUIDs vs human-readable relationships
therefore cannot be assessed from Demo Lab data at all (no rows).

---

## 9. Authorization / tenant isolation

### 9.1 What is enforced in code (`CODE-TRACED`)

| Concern | Enforcement point |
| --- | --- |
| Organisation isolation | `ensure_org_access` / `require_org_member` (`api/dependencies.py`) on org-scoped reads/writes |
| Consultant↔client boundary | `ensure_consultant_org_access` + ACTIVE grant (`api/consultant_auth.py`) |
| PE boundary | entity-scoped resolution (`work_item_effective_entity`, `is_entity_member`) and `_resolve_entity_actor` forcing a PE caller to its own entity |
| Internal-staff permissions | `ensure_staff_permission` (e.g. `can_manage_staff`) — "admin" is not a universal shortcut |
| Evidence-line read | `v3_evidence.py` re-authorizes on every read; the stored line id is a locator, **not** a grant; signed URL issued at FULL DM-6 depth only |
| Insight scope | `authorize_insight_scope` + per-object organisation re-check (per the tool definitions) |

### 9.2 What was actually observed (`DATA-VERIFIED` / `OBSERVATION`)

The Demo Lab harness contains a **30-probe authorization matrix and 18 isolation
rules**, and the verifier read its **last recorded run (2026-09-20 21:29Z)** from
the state directory:

```text
summary = { contexts: 13, contexts_failed: 0,
            probes: 30, probes_failed: 0, probes_failed_identity: 0,
            known_product_defects: [],
            isolation_rules: 18, isolation_rules_failed: 0,
            auth_methods: ["password_grant"] }
database = carbontally_demo_local
```

Earlier runs (e.g. `verify_20260919T170235Z.json`) are the same size and shape;
one recorded run surfaces `known_product_defects` (the preflight's `F-T1-001`,
`GET /api/v3/reporting/audit-activity` → HTTP 500 for an authorised owner), and the
**latest** run lists `known_product_defects: []`.

**Two honest qualifiers:**

1. This evidence is **historical** (2026-09-20). The verifier **did not re-run** the
   harness, because the release backend is not running. It is therefore
   `OBSERVATION`, not `VERIFIED`.
2. It covers identity contexts, authorization probes and isolation rules — it does
   **not** cover the demo workflows (assignment, messaging, report approval).

**Result: PARTIAL.** Last recorded result was clean (0 failures across 30 probes and
18 isolation rules) against `carbontally_demo_local`; **not re-verified in this
session**; and whether `F-T1-001` is fixed or merely absent from the current probe
set is **UNKNOWN** (no code change addressing it was inspected, and the API could not
be called).

---

## 10. Demo Lab harness assessment

| Question | Answer | Evidence |
| --- | --- | --- |
| Is the harness present in the release? | **Yes** — `lab.py`, `stack.py`, `provision.py`, `storage.py`, `seed_factors.py`, `t3_scenarios.py`, `t3_manifest.json`, `t3_extract_probe.py`, `verify.py`, `run_demo_lab.sh`, `reset_demo_lab.sh`, `README.md` | `ls tools/demo_lab/` |
| Is its state/credentials material present? | **Yes** — `$HOME/ct_local_env/demo_lab` with `backend.env` (mode 600), `credentials.local.json` (mode 600), `corpus/t3-uk-curated-v1`, 14 `verify_*.json`, T2-C factor evidence | `ls -la` on the state dir |
| Is the lab infrastructure up? | **Partly** — gateway `carbontally_demo_lab_gateway` on `54430` and the PostgREST/storage containers exist; the **release backend on 8070 does not** | `docker ps`; `ss -ltnp` |
| Is the factor dataset loaded? | **Yes** — `emission_factors = 7,049` in `carbontally_demo_local` (7,029 DEFRA + 20 SEAI) | `DATABASE-OBSERVED` |
| **Can the harness be used against the current release, today?** | **NOT PROVEN.** `verify.py` needs the release backend; `t3_scenarios.py` needs a pinned generator checkout (`/tmp/extgen`, absent) for `sync-corpus`; and both would touch lab data. | `verify.py`; preflight §4.3 / §18.2 B8; `ls /tmp/extgen` |
| Does the harness perform destructive setup? | `reset_demo_lab.sh` drops the lab DB and lab auth users; `t3_scenarios.py` has a **hard `assert_lab_database()` guard** limited to `carbontally_demo_local` | `reset_demo_lab.sh`; `t3_scenarios.py` |
| Does the integration **test** harness perform destructive setup? | **Yes** — `TRUNCATE … RESTART IDENTITY CASCADE` on its target, refused for `qa`/`demo`/`investor`/`prod`/`live` markers and the forbidden main DBs (F-046-1) | `backend/tests/integration/conftest.py` |

**Assessment: the harness is present, previously exercised (last clean run
2026-09-20), and still *not proven usable* against the current HEAD.** Its usability
is the single largest open environment question for Step 2.

---

## 11. Tests executed

### 11.1 Unit suite (executed, `TEST-VERIFIED`)

```text
command : backend/.venv/bin/python -m pytest tests/unit -q --tb=no -p no:cacheprovider
result  : 3220 tests -- 4 failed, 8 skipped, 0 errors -- 266.35 s
```

`~3208` unit tests **passed**. **No test was modified.** The 4 failures were
classified by inspection, not by changing the tests:

| Failing test | Actual error | Classification |
| --- | --- | --- |
| `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered` | `assert '/api/v3/ops/sla/settings' in {'/api/v2/health'}` | **PRE-EXISTING / obsolete test fixture.** The test asserts on the module-level `api.router.router`, but routes are mounted in `create_app()`. The routes **do** exist (`v3_operations.py:2332` `@router.get("/sla/settings")`). Not a product defect; unrelated to the investor-demo workflows |
| `…::test_canonical_ops_review_assign_registered` | same root cause | same |
| `…::test_admin_legacy_compat_surface_retained` | same root cause | same |
| `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | `assert len(names) == 71` — actual **81** | **PRE-EXISTING / stale expectation.** The hard-coded migration count predates 10 later migrations. Not a product defect; unrelated |

**Separated, as required:** newly discovered failures **none**; pre-existing
failures **4**; environment failures **0**; test-harness (fixture) failures **4**
(the same 4); genuine product defects **0 identified in this run**.

### 11.2 Integration suite (NOT executed — deliberate)

The integration harness performs `TRUNCATE … RESTART IDENTITY CASCADE` on its target
(PO control **F-046-1**). Running it would be a destructive database operation, which
Step 1 explicitly does not authorize. It was therefore **not run**, and no evidence
is claimed from it.

Relevant suites that *exist* and would provide genuine end-to-end workflow evidence
once a disposable clone (or `carbontally_test`, the designated test DB) is
authorized:

```text
tests/integration/test_evidence_line_items_b2_runtime.py
tests/integration/test_report_lifecycle.py
tests/integration/test_report_versions.py
tests/integration/test_reports.py
tests/integration/test_consultants.py
tests/integration/test_documents.py
tests/integration/test_extraction.py
tests/integration/test_workflow.py
tests/integration/test_v3m1_v3m2_processing_entities.py
tests/integration/test_v3_rls_behavior.py
tests/integration/test_calculation.py
tests/integration/test_emissions_logs.py
tests/integration/test_disclosure_b3_v3_security.py
tests/integration/test_operational_alerting_x2_runtime.py
tests/integration/test_api_metrics_x7_runtime.py
```

**`RECOMMENDATION`:** a Step-2 verification pass should run these against a
**disposable clone** (`ct_p12_*`) created from the re-provisioned demo schema, which
satisfies F-046-1 and yields `RUNTIME-VERIFIED (EXERCISED)` evidence for the frozen
stories. **`AUTHORIZATION REQUIRED`.**

### 11.3 Demo Lab harness verification (NOT executed)

`tools/demo_lab/verify.py` could not run (release backend down). Last recorded clean
run: 2026-09-20 21:29Z (§9.2). Not re-verified.

---

## 12. Workflows that FAILED or remain UNVERIFIED

| Workflow | Status | Why |
| --- | --- | --- |
| Upload → extraction → mapping → validation → calculation → emissions | **PARTIAL** — 1 real completed record exists (`2469.169780` kg CO₂e); not re-exercised this session | Backend not running; read-only boundary |
| PE assignment / reassignment / partial release / completion | **UNVERIFIED** | Zero assignment rows in the Demo Lab |
| PE workspace visibility | **UNVERIFIED** | No assigned work items |
| Messaging (either plane), including live delivery | **UNVERIFIED** | Zero conversations/messages in the Demo Lab |
| Report review / approval / finalisation | **UNVERIFIED and NOT DEMONSTRABLE** | Every candidate report version is `DRAFT` |
| Master-data CRUD (facility/asset/supplier) | **UNVERIFIED and NOT DEMONSTRABLE** | Zero master-data rows in the Demo Lab |
| Consultant operating a client workspace | **UNVERIFIED** | Topology present; behaviour not exercised |
| Insight (any question) | **UNVERIFIED and BLOCKED** | No Insight tables in any candidate environment |
| P2 temporal comparison | **UNVERIFIED and BLOCKED** | Migration not applied |
| P3 data quality / reproducibility | **UNVERIFIED and BLOCKED** | Migration not applied; no UI renderer |
| Source Evidence Viewer | **UNVERIFIED and BLOCKED** | Zero evidence line items (EV-01) |
| Cross-tenant DENY matrix | **PARTIAL** | Code-verified; last recorded harness run clean but not re-run |

**No workflow tested in this session produced an unexpected ALLOW.** No security
finding of that class was identified (it could not be tested live).

---

## 13. Verdict

**Workflow verification: PASS WITH OBSERVATIONS — at the boundary the Step-1
authorization permits.**

- **Verified:** route surfaces, authorization/guard wiring, persistence model,
  state-machine semantics, test coverage, and the *absence* of the data required
  for almost every demo workflow.
- **Not verified:** every end-to-end workflow (blocked by environment, not by
  evidence of a defect).
- **Defects fixed:** none (verifier rule).
- **Defects found:** none in this workstream; the findings are **capability/data
  gaps** and **documentation divergences**, not proven product defects.
- **Zero rows / unrun harness**: every untested plane is reported `UNVERIFIED`, never
  as passing.
