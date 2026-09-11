# CT-PHASE6-REMAINDER-RA-20260910-001 — Unified P6-2D/P6-2E/P6-2F Readiness Analysis (durable prompt-history record)

## 1. Prompt Ref

`CT-PHASE6-REMAINDER-RA-20260910-001`

## 2. Response Ref

`CT-PHASE6-REMAINDER-RA-20260910-001-R`

## 3. Prompt datetime

10 September 2026 (session date; wall-clock not stated in the prompt). Received
and executed approx. 17:10–17:55 local (Asia/Dhaka +0600).

## 4. Exact complete prompt text

````text
CARBONTALLY — UNIFIED P6-2D / P6-2E / P6-2F READINESS, DEPENDENCY & EXECUTION-PLAN ANALYSIS
PROMPT REF: CT-PHASE6-REMAINDER-RA-20260910-001

DATE:
10 September 2026

ROLE:
You are acting as the CarbonTally architecture/readiness-analysis agent.

THIS IS A READINESS AND PLANNING TASK ONLY.

DO NOT IMPLEMENT ANY CODE.

DO NOT MODIFY TESTS.

DO NOT MODIFY DATABASE/SCHEMA/RLS.

DO NOT MODIFY FRONTEND.

DO NOT MODIFY BILLING.

DO NOT COMMIT.

DO NOT PUSH.

Your task is to determine whether the remaining Phase 6 work currently designated as P6-2D, P6-2E and P6-2F can safely be consolidated into ONE controlled implementation campaign, while preserving mandatory internal gates and independent verification.

============================================================
SECTION 1 — CURRENT AUTHORITATIVE STATUS
============================================================

P6-2C is CLOSED.

P6-2C status:

P6-2C VERIFIED — PASS WITH NON-BLOCKING FINDINGS

Verified contract:

CARBONTALLY-P6-2C-IC-20260910-001

The independent verification report is:

docs/cline/CARBONTALLY_P6_2C_INDEPENDENT_VERIFICATION_REPORT.md

Do NOT reopen P6-2C unless a material dependency conflict is discovered.

The remaining Phase 6 sequence is currently:

P6-2D → P6-2E → P6-2F

P6-2F is the final Phase 6 UI/UX + E2E security acceptance gate.

The Product Owner is considering consolidating these remaining gates into one implementation campaign.

IMPORTANT:

This task must determine whether that consolidation is safe and practical.

Do NOT assume that consolidation is automatically appropriate.

Do NOT recommend consolidation merely because it reduces the number of prompts.

============================================================
SECTION 2 — AUTHORITATIVE DOCUMENT HIERARCHY
============================================================

Use the existing hierarchy:

1. Product Owner = final policy authority.
2. docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md
   = architecture authority.
3. docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md
   = product roadmap authority.
4. Phase-specific architecture/gate documents
   = authoritative for their respective gates.
5. PO decision registers
   = authoritative for explicit PO decisions.
6. Implementation reports
   = evidence of what exists.
7. Verification reports
   = evidence of what has been independently verified.
8. Prompt-history records
   = durable evidence/history, not authority.

Do not create a competing authority hierarchy.

============================================================
SECTION 3 — REQUIRED DOCUMENT REVIEW
============================================================

Read the current versions of:

A. Architecture authority
- docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md

B. Roadmap authority
- docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md

C. Phase 6 documents
- docs/architecture/CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md
- docs/architecture/CARBONTALLY_PHASE6_P0_PO_RATIFICATION_REPORT.md

D. P6-2 documents
- docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md
- docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md
- docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md

E. P6-2C records
- docs/architecture/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_CONTRACT.md
- docs/cline/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_REPORT.md
- docs/cline/CARBONTALLY_P6_2C_INDEPENDENT_VERIFICATION_REPORT.md

F. Relevant P6-2A/R1 and P6-2B-1/2/3/4 implementation and verification reports.

G. Existing prompt-history records for the relevant Phase 6 work.

If a filename differs, locate the actual authoritative equivalent.

Do not invent missing documents.

============================================================
SECTION 4 — P6-2D ANALYSIS
============================================================

Determine precisely what P6-2D means according to the authoritative documents.

Do NOT infer its scope merely from the phase number.

Identify:

1. Official P6-2D name.
2. Authoritative definition.
3. Requirements.
4. Existing implementation.
5. Existing verification.
6. Remaining implementation.
7. Remaining tests.
8. Remaining security requirements.
9. Relevant D-items.
10. Relevant API routes.
11. Relevant backend files.
12. Relevant database/schema/RLS dependencies.
13. Relevant frontend dependencies.
14. Relevant billing dependencies.
15. Provenance/audit implications.
16. Dependencies on P6-2C.
17. Dependencies on P6-2E.
18. Dependencies on P6-2F.
19. PO decisions already ratified.
20. New PO decisions still required.

For every requirement classify it:

- COMPLETE
- IMPLEMENTED / NOT INDEPENDENTLY VERIFIED
- PARTIAL
- NOT STARTED
- DEFERRED
- OUT OF SCOPE
- BLOCKED

Do not invent status.

============================================================
SECTION 5 — P6-2E ANALYSIS
============================================================

Determine precisely what P6-2E means according to the authoritative documents.

Identify:

1. Official P6-2E name.
2. Authoritative definition.
3. Requirements.
4. Existing implementation.
5. Existing verification.
6. Remaining implementation.
7. Remaining tests.
8. Security implications.
9. Relevant D-items.
10. API/backend dependencies.
11. frontend dependencies.
12. notification dependencies.
13. audit/provenance implications.
14. dependencies on P6-2D.
15. dependencies on P6-2F.
16. PO decisions already ratified.
17. New PO decisions required.

Classify every requirement using the same status categories.

============================================================
SECTION 6 — P6-2F ANALYSIS
============================================================

Determine precisely what P6-2F means according to the authoritative documents.

Pay particular attention to the fact that P6-2F is the final UI/UX + E2E security acceptance gate.

Identify:

1. Official P6-2F name.
2. Authoritative definition.
3. UI/UX requirements.
4. User workflow requirements.
5. E2E requirements.
6. API/security requirements that must be exercised end-to-end.
7. Customer workflows.
8. Consultant workflows.
9. Processing Entity workflows.
10. Operations workflows.
11. Organization/role boundaries.
12. Billing behavior that must be verified.
13. provenance/audit behavior that must be verified.
14. cross-organization isolation.
15. negative security flows.
16. relevant D-items.
17. existing implementation.
18. existing verification.
19. remaining implementation.
20. remaining E2E tests.
21. dependencies on P6-2D.
22. dependencies on P6-2E.
23. final Phase 6 acceptance requirements.
24. PO decisions already ratified.
25. new PO decisions required.

Classify every requirement using the same status categories.

============================================================
SECTION 7 — CONSOLIDATION FEASIBILITY
============================================================

Now answer the central question:

CAN P6-2D + P6-2E + P6-2F BE IMPLEMENTED AS ONE CONTROLLED CAMPAIGN?

Evaluate this rigorously.

Consider:

- dependency ordering
- architectural coupling
- authorization risk
- workflow risk
- database risk
- RLS risk
- billing risk
- provenance risk
- frontend risk
- E2E complexity
- regression risk
- rollback complexity
- ability to isolate failures
- ability to independently verify each internal gate
- Cline context/workload limitations
- repository working-tree complexity
- existing pre-Phase-6 changes
- ability to produce clear evidence
- ability to stop safely after each internal gate

Do NOT answer merely "yes" or "no."

Provide:

### A. Recommended consolidation model

For example:

ONE IMPLEMENTATION CAMPAIGN
containing:

P6-2D
→ internal verification checkpoint

P6-2E
→ internal verification checkpoint

P6-2F
→ final Phase 6 acceptance preparation

But determine whether this model is actually appropriate based on the evidence.

### B. What must remain separately gated

Identify anything that must remain a hard checkpoint even if implementation is consolidated.

### C. What must NOT be combined

Identify any work that should remain separate because combining it would create unacceptable risk.

============================================================
SECTION 8 — DEPENDENCY GRAPH
============================================================

Produce a dependency graph such as:

P6-2C
  ↓
P6-2D
  ↓
P6-2E
  ↓
P6-2F

But replace this with the actual dependency graph discovered from the repository.

If P6-2E and P6-2D can run partially in parallel, say so.

If they must remain sequential, explain why.

Do not assume the roadmap order is technically necessary without evidence.

The roadmap sequence remains authoritative unless a PO decision changes it.

============================================================
SECTION 9 — UNIFIED IMPLEMENTATION CONTRACT PROPOSAL
============================================================

Determine whether it is appropriate to create one unified implementation contract for:

P6-2D + P6-2E + P6-2F.

If YES, propose:

CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001

The proposed contract should contain:

1. P6-2D scope
2. P6-2E scope
3. P6-2F scope
4. dependencies
5. internal checkpoints
6. security invariants
7. workflow invariants
8. authorization invariants
9. billing invariants
10. provenance invariants
11. audit invariants
12. RLS invariants
13. frontend/UI requirements
14. E2E requirements
15. regression requirements
16. rollback/stop conditions
17. explicit out-of-scope work
18. PO decision requirements
19. acceptance criteria
20. independent verification requirements

Do NOT create the contract yet unless you determine that doing so is appropriate.

This task is a readiness analysis.

If the contract should not yet be created, explain why.

============================================================
SECTION 10 — PO DECISION ANALYSIS
============================================================

Identify every decision that requires Product Owner input before implementation.

For each decision provide:

- Decision Ref proposal
- Exact question
- Why it matters
- Options
- Recommended option
- Reason for recommendation
- Impact if chosen
- Whether it blocks implementation

Do not make decisions on behalf of the PO.

Do not silently convert recommendations into policy.

============================================================
SECTION 11 — CODE / FILE IMPACT
============================================================

For each of P6-2D, P6-2E and P6-2F identify:

- files that MUST change
- files that MAY change
- files that MUST remain unchanged
- tests that MUST be added
- tests that MUST remain untouched
- documentation that must be created
- migrations expected
- RLS changes expected
- frontend changes expected
- E2E changes expected

Pay particular attention to avoiding accidental modification of the large set of pre-existing Phase-6 working-tree changes.

Do not modify any of them.

============================================================
SECTION 12 — SECURITY INVARIANTS
============================================================

Create a unified security-invariant checklist for the remaining Phase 6.

At minimum evaluate:

- authentication
- organization isolation
- firm isolation
- consultant grants
- consultant capabilities
- PE authorization
- Operations authorization
- customer/org-admin authority
- approval boundary
- CT-QC
- processing origin
- provenance
- audit
- billing
- RLS
- IDOR
- actor injection
- alternate-route bypass
- concurrency
- replay/idempotency
- UI-only authorization assumptions

Explicitly identify which P6-2C invariants must remain frozen while implementing 2D/2E/2F.

============================================================
SECTION 13 — TEST / VERIFICATION STRATEGY
============================================================

Design a unified test strategy.

Separate:

A. Unit tests
B. API authorization tests
C. Workflow tests
D. Billing regression
E. Provenance/audit regression
F. RLS/integration testing
G. Frontend tests
H. E2E tests
I. Security-negative tests
J. Final Phase 6 acceptance tests

Identify what can be run after each internal gate and what must wait until P6-2F.

Do not run tests that require modifying production code.

This is a planning task.

============================================================
SECTION 14 — IMPLEMENTATION CAMPAIGN DESIGN
============================================================

If consolidation is recommended, propose an execution model such as:

PHASE 6 REMAINDER — IMPLEMENTATION CAMPAIGN

CHECKPOINT 1
P6-2D implementation
↓
P6-2D focused tests
↓
P6-2D regression
↓
P6-2D internal evidence checkpoint

STOP IF FAILED.

CHECKPOINT 2
P6-2E implementation
↓
P6-2E focused tests
↓
P6-2E regression
↓
P6-2E internal evidence checkpoint

STOP IF FAILED.

CHECKPOINT 3
P6-2F implementation
↓
UI tests
↓
E2E
↓
security acceptance
↓
full Phase 6 regression

STOP.

Then independent verification.

Determine the actual checkpoints required from the evidence.

The implementation agent must NOT independently declare the entire Phase 6 complete merely because its tests pass.

============================================================
SECTION 15 — CLINE WORKLOAD ASSESSMENT
============================================================

Explicitly assess whether the unified campaign is realistically manageable for Cline.

Consider:

- estimated files
- estimated code surface
- estimated tests
- frontend complexity
- E2E complexity
- documentation burden
- context requirements
- number of independent security invariants
- likelihood of context loss
- likelihood of scope drift
- ability to maintain durable records

Give a practical recommendation:

- SAFE FOR ONE CAMPAIGN
- SAFE ONLY WITH HARD INTERNAL CHECKPOINTS
- TOO LARGE — KEEP SEPARATE

Explain the recommendation.

============================================================
SECTION 16 — NO IMPLEMENTATION
============================================================

STRICT:

Do NOT modify:

- backend code
- frontend code
- tests
- database
- schema
- migrations
- RLS
- billing
- configuration

Do not create implementation code.

Documentation changes are allowed ONLY for the readiness-analysis artifact and its mandatory prompt-history record.

Do not modify the Master Roadmap or Architecture Blueprint.

Do not create the unified implementation contract yet unless explicitly justified by the analysis and clearly labeled as a proposal rather than an authorized contract.

============================================================
SECTION 17 — DURABLE READINESS REPORT
============================================================

Create:

docs/cline/CARBONTALLY_PHASE6_REMAINDER_UNIFIED_READINESS_ANALYSIS.md

The report must include:

1. Prompt Ref
2. Date/time
3. Executive verdict
4. Current Phase 6 status
5. P6-2D analysis
6. P6-2E analysis
7. P6-2F analysis
8. Consolidation feasibility
9. Dependency graph
10. Proposed campaign model
11. Required internal checkpoints
12. PO decisions required
13. Code/file impact
14. Security invariants
15. Test strategy
16. Cline workload assessment
17. Risks
18. Evidence limitations
19. Recommended next step
20. Explicit no-implementation statement

Do not fabricate information.

============================================================
SECTION 18 — MANDATORY PROMPT-HISTORY RECORD
============================================================

Create:

docs/cline/prompt-history/CT-PHASE6-REMAINDER-RA-20260910-001.md

Use:

Prompt Ref:
CT-PHASE6-REMAINDER-RA-20260910-001

Response Ref:
CT-PHASE6-REMAINDER-RA-20260910-001-R

The prompt-history record MUST contain:

1. Exact Prompt Ref
2. Exact Response Ref
3. Prompt datetime
4. Exact complete prompt text
5. Complete Cline response
6. Detailed analysis breakdown
7. Documents inspected
8. Files inspected
9. Files changed
10. Files unchanged
11. Commands executed
12. Tests executed, if any
13. Findings
14. PO decisions identified
15. Risks
16. Evidence limitations
17. Consolidation recommendation
18. Final verdict
19. Stop-condition confirmation

No leftover placeholders or markers.

============================================================
SECTION 19 — FINAL RESPONSE FORMAT
============================================================

Return:

# PHASE 6 REMAINDER — UNIFIED READINESS ANALYSIS

## 1. Executive Verdict

Choose one:

SAFE FOR ONE CAMPAIGN

SAFE ONLY WITH HARD INTERNAL CHECKPOINTS

TOO LARGE — KEEP SEPARATE

BLOCKED — AUTHORITY/DEPENDENCY ISSUE

## 2. Current Phase 6 Status

Include P6-2C as independently verified and closed.

## 3. P6-2D Status

[complete analysis]

## 4. P6-2E Status

[complete analysis]

## 5. P6-2F Status

[complete analysis]

## 6. Consolidation Recommendation

[yes/no + exact model]

## 7. Required Internal Checkpoints

[list]

## 8. Dependency Graph

[graph]

## 9. PO Decisions Required

[list]

## 10. Code/File Impact

[list]

## 11. Security Invariants

[list]

## 12. Test / Verification Strategy

[list]

## 13. Cline Workload Assessment

[assessment]

## 14. Risks

[list]

## 15. Evidence Limitations

[list]

## 16. Recommended Next Step

[exact next action]

## 17. Readiness Report

docs/cline/CARBONTALLY_PHASE6_REMAINDER_UNIFIED_READINESS_ANALYSIS.md

## 18. Prompt History

docs/cline/prompt-history/CT-PHASE6-REMAINDER-RA-20260910-001.md

Response Ref:
CT-PHASE6-REMAINDER-RA-20260910-001-R

## 19. Git State

Report actual:

- branch
- HEAD
- git status
- changed files
- unexpected changes

## 20. STOP CONDITION

State explicitly:

"No P6-2D, P6-2E, or P6-2F implementation was started. This task is complete and stopped at the readiness-analysis boundary."

============================================================
FINAL INSTRUCTION
============================================================

Perform ONLY the unified P6-2D/P6-2E/P6-2F readiness, dependency, consolidation, and workload analysis.

Do not implement anything.

Do not modify code, tests, frontend, schema, migrations, RLS, billing, or configuration.

Do not commit.

Do not push.

Create the durable readiness report.

Create the mandatory prompt-history record.

Determine objectively whether the remaining Phase 6 work can safely be handled as one implementation campaign with hard internal checkpoints.

Then STOP.
````

## 5. Complete Cline response

The complete final response is reproduced in the readiness report's §1–§19 and
returned verbatim in the final answer for this prompt. Its substance:

- **Verdict:** `SAFE ONLY WITH HARD INTERNAL CHECKPOINTS`.
- **P6-2D:** D6 already implemented (`ensure_processing_entitlement`, read-only,
  fail-closed, wired into consultant submit before mutation); **D7 not started**
  (no firm on item/audit/snapshot provenance; no `CONSULTANT` origin value; no
  origin queue labels). Blocked on PO ratification of D6/D7. One additive
  migration expected.
- **P6-2E:** D8's recommended reuse model already implemented (consultants
  participate in org conversations via active grant); **D11 not started** (only
  `work_item.assigned` exists). Depends on D7. Blocked on PO-D8/PO-D11.
- **P6-2F:** consultant UI partially exists (routed item workspace reusing
  `ExtractionPanel`; six components; jest page test) but the **review/submit UI is
  absent**, firm/origin display depends on D7, notification surfacing depends on
  D11, and **no E2E acceptance suite exists** (only `tests/example.spec.ts`)
  despite a mature `qa_harness/browser/**` + Playwright infrastructure.
- **Consolidation:** one campaign, four checkpoints (0 PO ratification, 1 P6-2D,
  2 P6-2E, 3 P6-2F in a fresh session), STOP-IF-FAILED after each, independent
  verification per gate, mandatory independent verification of the P6-2F final
  gate.
- **PO decisions:** eleven proposed decisions listed with options,
  recommendations and blocking status; none made on the PO's behalf.
- **No implementation performed.**

- **No implementation performed.**

## 6. Detailed analysis breakdown

| Question | Method | Finding |
|---|---|---|
| What is P6-2D? | roadmap §9/§14 + P6-2 §13 + register D6/D7 + code inspection | D6 = entitlement availability at submit (**already implemented**); D7 = consultant firm/origin provenance (**not started**) |
| What is P6-2E? | roadmap §9 + P6-2 §13 + register D8/D11 + code inspection | D8 reuse model already implemented; D11 notification vocabulary **absent** |
| What is P6-2F? | roadmap §9/§13 + readiness §27 P6-6/§28 + frontend/harness inspection | UI partially present; review/submit UI absent; **E2E acceptance suite absent** |
| Can they be one campaign? | dependency + risk + workload analysis | YES with four hard checkpoints (incl. PO ratification gate); P6-2F in a fresh session |
| Is D6/D7/D8/D11 ratified? | PO register header + ratified-entries section | **NO** — recommendations only; only P6-2C D1/D2/D3 (and the separate P6-0 D-1…D-7 package) are ratified |

## 7. Documents inspected

Blueprint V1.3; Master Roadmap V1.0 (§0, §9, §12, §13, §14, §18); Phase-6
readiness report (§26–§30); P6-0 PO ratification report; P6-2 processing workflow
architecture (§13, §14); P6-2B review/QC architecture (§21, §22, §23); P6-2 PO
decision register (D1–D11, cross-dependencies, P6-2C ratified section); the P6-2C
contract, implementation report and independent verification report; P6-2A/R1 and
P6-2B-1/2/3/4 reports; prompt-history records
`CT-P6-2C-RA/PO/IMPL/IV-20260910-001.md`.

## 8. Files inspected (code/config — read-only)

`backend/api/v3_processing_workflow.py`, `backend/api/v3_consultants.py`,
`backend/api/v3_operations.py`, `backend/api/v3_qc.py`,
`backend/api/v3_messaging.py`, `backend/api/consultant_auth.py`,
`backend/api/v3_automatic_processing.py`, `backend/services/billing.py`,
`backend/services/work_items.py`, `backend/domain/processing_origin.py`,
`backend/domain/partners.py`, `backend/data/manual_extraction.py`,
`backend/data/messaging.py`, `backend/data/notifications.py`,
`backend/data/consultants.py`; `frontend/src/v3/consultant/*` (6 components),
`frontend/src/v3/api.js`, `frontend/src/v3/NotificationsPage.jsx`,
`frontend/src/v3/pe/PeNotificationsBell.jsx`,
`frontend/src/v3/__tests__/consultant-page.test.jsx`; `qa_harness/**` (scripts +
browser modules), `playwright.config.ts`, `tests/example.spec.ts`;
`supabase/migrations/` (inventory).

## 9. Files changed by this task

- **Created:** `docs/cline/CARBONTALLY_PHASE6_REMAINDER_UNIFIED_READINESS_ANALYSIS.md`
- **Created:** `docs/cline/prompt-history/CT-PHASE6-REMAINDER-RA-20260910-001.md`

Nothing else was created, modified or deleted.

## 10. Files confirmed unchanged

All backend code, all frontend code, all tests, `supabase/**` (schema, migrations,
RLS), billing, authentication, configuration, seed/demo data,
`docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`,
`docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`,
`docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`, the P6-2C contract,
the P6-2C implementation report and the P6-2C independent verification report —
plus the pre-existing 657-entry working-tree change set.

## 11. Commands executed (representative, all read-only)

```
ls docs/architecture/ ; ls docs/cline/ ; ls docs/cline/prompt-history/
grep -rn 'P6-2D\|P6-2E\|P6-2F' docs/ --include=*.md
grep -n '^#\{1,3\} ' <roadmap/architecture/register docs>
grep -rn 'consultant_firm_id\|firm_id' --include=*.py api data domain services engines
grep -rn 'entitlement\|availability' --include=*.py api services domain
grep -rn 'conversation_kind' --include=*.py .
grep -rn 'notification_type=\|event_key=' --include=*.py .
grep -rn 'PROCESSING_ENTITY\|CARBONTALLY_INTERNAL\|CONSULTANT' --include=*.py domain data api
find frontend/src -iname '*consultant*' ; ls frontend/src/v3
grep -rn 'consultant-review\|consultant-submit\|consultant_reviewed' frontend/src
ls qa_harness ; find qa_harness -name 'run_all.py' ; ls -R qa_harness/browser
grep -n 'testDir' playwright.config.ts ; ls tests/
git rev-parse --abbrev-ref HEAD ; git rev-parse --short HEAD ; git status --porcelain=v1 | wc -l
```

No test suite was executed (planning task), no application was started, no
migration was applied, no write command was issued.

## 12. Tests executed

**None.** Deliberately: this was a readiness/planning task. The only test figure
quoted (1,606 unit tests, EXIT 0) is the *previously verified* P6-2C baseline,
cited as such and not re-measured here.

## 13. Findings

1. **D6 is already implemented** (`ensure_processing_entitlement`, non-charging,
   fail-closed, called before mutation on the consultant submit route) — P6-2D is
   therefore half-complete.
2. **D7 is entirely unimplemented** (no firm provenance on items/audit/snapshots,
   no `CONSULTANT` origin value, no origin queue labels).
3. **D8's recommended model already exists** (consultant participation in org
   conversations via active grant) — D8 may resolve to a PO "no new kind" decision.
4. **D11 is entirely unimplemented** (only `work_item.assigned` exists).
5. **The consultant UI is further along than "not started"** (routed processing
   workspace reusing `ExtractionPanel`, 6 components ≈ 1,973 lines, jest test) but
   the **review/submit UI is absent** and **no E2E acceptance suite exists**.
6. **Governance gap:** D6/D7/D8/D11 are register recommendations, not ratified PO
   decisions; implementation is blocked on ratification.
7. **Numbering hazard:** `PO-D7 (ratified, Phase 6)` in `services/billing.py`
   refers to the P6-0 package decision, not the P6-2 register's D7 (firm
   provenance).
8. **Verification-artifact gaps carry into Phase 6 acceptance:** P6-1B, P6-1C and
   P6-2B-4 lack on-disk independent verification artifacts.

## 14. PO decisions identified

Eleven (full table in the readiness report §10): `PO-P6-2D-D6-R`,
`PO-P6-2D-D7-R`, `PO-P6-2D-D7b-R`, `PO-P6-2D-D7c-R`, `PO-P6-2E-D8`,
`PO-P6-2E-D11`, `PO-PHASE6-DEFER`, `PO-PHASE6-D4`, `PO-P6-2F-ACC`,
`PO-P6-2F-ENV`, `PO-PHASE6-CAMPAIGN`. **None was decided by this task.**

## 15. Risks

Twelve (readiness report §16): unratified-policy implementation; provenance
regression; migration/RLS interaction; notification leakage or denial-path
emission; drive-by backend changes during UI work; demo-data mutation;
self-accepted final gate; working-tree contamination; scope creep (D4, charging
question); D8 "just-in-case" schema drift; unverified P6-1B/1C surfaces; baseline
drift.

## 16. Evidence limitations

Seven (readiness report §17): no runtime verification in this task; static
frontend assessment only; P6-1B/1C/P6-2B-4 verification artifacts absent; D6 not
re-exercised here; E2E harness readiness inferred not measured; no ratified
D1–D11; effort estimates are estimates.

## 17. Consolidation recommendation

**One authorised campaign with four hard checkpoints** (0 PO ratification → 1
P6-2D → 2 P6-2E → 3 P6-2F in a fresh session), STOP-IF-FAILED after each
implementation checkpoint, independent verification per gate, and **mandatory**
independent verification of the P6-2F final gate. A lower-risk variant is to keep
P6-2D + P6-2E as one campaign and P6-2F as a separate campaign; that changes only
the authorisation wrapper. The unified contract
(`CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001`) was **not** created — it is
appropriate only after Checkpoint 0 ratification and appears here as a proposal.

## 18. Final verdict

`SAFE ONLY WITH HARD INTERNAL CHECKPOINTS`

## 19. Stop-condition confirmation

**"No P6-2D, P6-2E, or P6-2F implementation was started. This task is complete and
stopped at the readiness-analysis boundary."** No code, test, frontend, schema,
migration, RLS, billing or configuration file was modified; no contract was
created; nothing was committed or pushed.
