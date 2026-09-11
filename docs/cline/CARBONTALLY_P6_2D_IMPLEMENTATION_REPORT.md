# CarbonTally — P6-2D Implementation Evidence Report (CP1)

**Prompt Ref:** `CT-P6-2D-IMPL-20260910-001`
**Response Ref:** `CT-P6-2D-IMPL-20260910-001-R1`
**Implementation date/time:** 2026-09-10, 19:12 → 20:05 (+0600)
**Phase:** Phase 6 · **Checkpoint:** CP1 · **Gate:** P6-2D (Entitlement & Provenance Finalisation)
**Pre-flight:** `CP1 PRE-FLIGHT PASS — P6-2D IMPLEMENTATION READY`
**Final verdict:** **P6-2D IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION** (implementation task only; not self-certified)

---

## 1. Objective

Implement only P6-2D, strictly per `docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md` §6 and the ratified PO decisions: **D6** (entitlement — preserve + verify), **D7** (durable server-derived consultant firm provenance + durable processing-mode provenance), **D7b** (Consultant origin stays prohibited), **D7c** (no historical backfill).

## 2. Authoritative documents read

`CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`; `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`; `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`; `CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md`; `CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md`; `CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`; `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md`; `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md`; `docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_RECONCILIATION_REPORT.md`; `docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_DOCUMENTATION_AMENDMENT_REPORT.md`; `docs/cline/CARBONTALLY_P6_2D_RESIDUAL_ORIGIN_WORDING_CLARIFICATION_REPORT.md`; `docs/cline/prompt-history/CT-P6-2D-PREFLIGHT-20260910-001.md`.

## 3. Repository / code / schema areas inspected

| Area | Detail |
|---|---|
| Consultant authorization | `backend/api/consultant_auth.py` — `_resolve_context` (active membership → single firm → active profile), `ensure_consultant_processing_authorized`, `ensure_consultant_review_authorized`, `ensure_consultant_submission_authorized` |
| Processing workflow routes | `backend/api/v3_processing_workflow.py` — `_get_checked_item`, start / extract / map / validate / calculate / consultant-review / consultant-submit / customer-review |
| Processing mode (existing predicate) | `backend/api/processing_mode.py` — `item_is_automatic`, `ensure_manual_ct_qc_prerequisite`, `CT_QC_SATISFIED_STATUSES` |
| Item persistence | `backend/data/manual_extraction.py` — `save_extracted_data`, `save_mapped_data`, `set_item_status`, `mark_pe_origin_if_unset`, `get_item_origin` (write-once pattern reused) |
| Origin vocabulary | `backend/domain/processing_origin.py`; migration `20260902020000_v1_2_dual_origin_workflow.sql` |
| Billing / entitlement (D6) | `backend/services/billing.py` — `ensure_processing_entitlement` (l.167), `charge_processing` (l.693); call sites `v3_processing_workflow.py:714` (submit preflight) and `:920` (approval charge) |
| Schema | `supabase/migrations/00000000000000_init_schema.sql` (consultant_profiles / consultant_firm_members FK style); `20260906100000_p6_2a_consultant_processing_permissions.sql` (additive migration style) |
| Test infrastructure | `backend/tests/unit/api/conftest.py`, `fakes.py` (`InMemoryWorld`, `MemoryManualExtraction`, `seed_item`, `seed_item_origin`), `test_p6_2a_*`, `test_p6_2b_1/2/4`, `test_p6bill1_*`, `test_billing_core.py`, `test_v3_operations.py` helpers |

## 4. Baseline (measured before any change)

- **Command:** `cd backend && ./.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider` (background run → `/tmp/p62_baseline.txt`).
- **Observed:** the run progressed to **100% with zero `F`/`E` characters** before the local shell killed the runner; **no `N passed` summary line was produced**, so a counted baseline could NOT be established in this environment. The previously reported **1,606 (EXIT 0)** remains a *carried-forward claim from the P6-2C verification* and is **not** restated as newly verified.
- **Honest limitation (not concealed):** the terminal repeatedly interrupted long pytest runs this session (SIGINT / `exit=130`). The post-change full-suite run was therefore wrapped in `nohup` writing an explicit `EXIT=` marker so completion is provable independently of shell integration; the result is in §12.

## 5. Exact changes made

### 5.1 Migration (class 4 — additive, nullable, no backfill)

**New file:** `supabase/migrations/20260910120000_p6_2d_consultant_provenance.sql`

- `ALTER TABLE public.manual_extraction_items ADD COLUMN IF NOT EXISTS` × 3:
  - `consultant_firm_id uuid REFERENCES public.consultant_profiles(id) ON DELETE SET NULL`
  - `processing_mode text`
  - `consultant_provenance_at timestamptz`
- One additive CHECK on the **new nullable** column: `processing_mode IS NULL OR processing_mode IN ('automatic','manual')` (drop-if-exists then add → idempotent).
- Descriptive `COMMENT ON COLUMN` for all three.
- **No** `UPDATE`/backfill, **no** `DEFAULT`, **no** `NOT NULL`, **no** `INSERT` (D7c).
- **No** RLS statement; **no** change to `processing_origin` or its CHECK (D7b); no other table touched.
- **Not applied to any database** by this task (no DB access performed); applying it is a deployment step (risk R1).

### 5.2 Production code (class 3)

1. `backend/data/manual_extraction.py` — new `record_consultant_provenance(item_id, *, firm_id, processing_mode) -> bool` (write-once `UPDATE … WHERE id = $1 AND consultant_firm_id IS NULL`, mirroring `mark_pe_origin_if_unset`) and `get_item_consultant_provenance(item_id)` (mirroring `get_item_origin`). No existing query, column list or dataclass changed.
2. `backend/api/consultant_auth.py` — new public `resolve_consultant_firm_id(current_user, repos) -> Optional[str]`: the authoritative firm of the caller's consultant context, or `None` for organisation members / internal staff / PE staff. Built on the existing `_resolve_context`; **no client input is consulted**.
3. `backend/api/v3_processing_workflow.py` — new `_record_consultant_provenance(repos, *, item, current_user)` helper and **exactly seven** call sites, each immediately before the action's mutation: `start` (L428), `extract` (L444), `map` (L470), `validate` (L506), `consultant-review` (L636), `consultant-submit` (L763), `calculate` (L803). The helper resolves the firm server-side and the mode from `item_is_automatic` (`automatic`/`manual`), and is a **no-op** for non-consultant callers.

### 5.3 Tests (class 6)

- **New** `backend/tests/unit/api/test_p6_2d_provenance.py` (19 tests) — D7 behaviour + security negatives + D7b/D7c guarantees.
- **New** `backend/tests/unit/api/test_p6_2d_entitlement.py` (2 tests) — the two uncovered D6 angles.
- **Modified** `backend/tests/unit/api/fakes.py` — in-memory mirrors `record_consultant_provenance` (write-once) and `get_item_consultant_provenance`; no existing fake behaviour changed.

## 6. Provenance design (D7)

| Dimension | Where it lives | Written by | Mutability |
|---|---|---|---|
| **Firm** | `manual_extraction_items.consultant_firm_id` | server: `resolve_consultant_firm_id` (active membership → single firm), at the action boundary | **write-once** — later actions, firms, membership/engagement changes never rewrite it |
| **Processing mode** | `manual_extraction_items.processing_mode` (`automatic` \| `manual`) | server: the authoritative `item_is_automatic` predicate at the same boundary | write-once |
| **Stamped at** | `consultant_provenance_at` | server (`NOW()` with the record) | write-once |
| **Actor** | existing `extracted_by` / `qc_by` / `customer_reviewed_by` / audit `performed_by` | unchanged | unchanged |
| **Origin** | existing `processing_origin` / `processing_entity_id` | unchanged (two values only) | unchanged |

- **Never actor-supplied:** the request models (`ExtractPayload`, `MapPayload`, `CalculatePayload`) have no firm/mode/origin field, extra JSON keys are dropped, and the recorder takes no request input at all.
- **Write-once / historical stability** is enforced in SQL (`AND consultant_firm_id IS NULL`) and mirrored in the fake.
- **Actor-agnostic mode:** the mode comes from the item's evidence-based predicate, never from the actor (a consultant acting on automatic work records `automatic`).
- **No backfill (D7c):** existing rows keep `NULL`; the reader returns `None` rather than inventing a value.
- **Documented limitation (honest):** the record captures the firm that **established** the item's consultant provenance; a *different* firm acting later deliberately does NOT overwrite it (ratified: "must not rewrite historical firm provenance"), and that later action remains attributable through the existing append-only audit actor trail. Per-action firm attribution would need an append-only provenance store — outside this task's minimum-change scope and not required by D7 ("no database field name is prescribed").
- **Documented limitation inherited from P1:** `processing_mode` records the item's canonical classification by the existing P1 containment predicate at the boundary (mixed/corrected automatic work is not distinguished by P1 — a pre-existing, documented limitation P6-2D neither introduces nor is required to solve).

## 7. D6 verification (entitlement — preserved, not redesigned)

| Requirement | Status | Evidence |
|---|---|---|
| Entitlement owned by the client Organisation | PRESERVED + VERIFIED | `ensure_processing_entitlement(batch.organization_id)` at `v3_processing_workflow.py:714`; existing `test_entitlement_resolved_server_side`, `test_client_a_credits_charge_only_client_a` |
| Submission preflight is non-charging | PRESERVED + VERIFIED | `services/billing.py:167–190` performs no mutation; new `test_denied_submission_consumes_and_charges_nothing`; existing `test_successful_submission_produces_no_charge_or_billing_mutation` |
| Approval-time enforcement stays canonical | PRESERVED (unchanged) | single charge site `v3_processing_workflow.py:920` (`charge:item:{item_id}`); billing untouched |
| Actor does not transfer entitlement | PRESERVED + VERIFIED | firm entitlement is never consulted for client work — new `test_entitlement_is_resolved_from_the_client_org_not_another_org` |
| Mode does not transfer entitlement | PRESERVED (no coupling introduced) | the new `processing_mode` column is provenance only; nothing reads it for billing |
| Consultant participation does not transfer entitlement | PRESERVED + VERIFIED | new entitlement tests; existing `test_p6bill1_*` |
| PE participation does not transfer entitlement | PRESERVED (unchanged) | no PE path touched |
| No charge merely for submitting | VERIFIED | existing + new submission tests |
| Charge only at the existing approval boundary | PRESERVED | grep: exactly one `charge_processing` call site (`api/v3_processing_workflow.py:920`) |
| Denied processing does not charge | VERIFIED | new entitlement-denial test + existing membership/capability denial tests |
| Deterministic billing idempotency intact | PRESERVED + VERIFIED | unchanged `charge:item:{item_id}` key; `test_billing_core.py` idempotency coverage |

**`backend/services/billing.py` was not modified** (see §15).

## 8. D7 implementation summary

- Firm provenance is **durable** (persisted column), **server-derived** (`resolve_consultant_firm_id` → active membership → single firm), captured **at action time** (seven call sites, immediately before each mutation), **write-once** (SQL guard), **never actor-supplied** (no request input reaches the recorder).
- Processing-mode provenance is durable and stored **separately** from origin; actor-agnostic (predicate-based) and constrained to `automatic`/`manual`.
- Actor identity remains in the pre-existing actor columns and the append-only audit trail — actor and firm stay distinct in schema and code.
- Action coverage: start · extract · map · validate · calculate · consultant-review · consultant-submit — asserted structurally (exactly 7 call sites) and behaviourally (extract, map, validate, start, review, submit exercised end-to-end).

## 9. D7c — no historical backfill

- The migration contains no `UPDATE`, no `INSERT`, no `DEFAULT` — asserted by `test_d7c_migration_is_additive_nullable_with_no_backfill`.
- All three columns are nullable; pre-existing rows remain `NULL` and read back as `None` (`test_unrecorded_item_reports_no_provenance`).
- No inference from email domain, organization name, historical memberships/grants or any proxy: the recorder accepts only a firm id already resolved from the *current* authorised relationship at the moment of the action.
- No existing row was read, rewritten or touched.

## 10. D7b — Consultant origin remains prohibited

- `domain/processing_origin.py` still exposes exactly `CARBONTALLY_INTERNAL` / `PROCESSING_ENTITY` (`test_d7b_origin_vocabulary_is_unchanged`).
- The D7 migration contains no consultant value and does not alter, drop, re-add or constrain `processing_origin` (`test_d7b_new_migration_adds_no_consultant_origin_value`).
- No routing, queue, state-machine or CHECK-constraint change was made; the withdrawn proposal remains withdrawn. `processing_mode` is deliberately **not** an origin value and is never used for origin routing.

## 11. Tests

### 11.1 Focused suites (new)

**Command:** `cd backend && ./.venv/bin/python -m pytest tests/unit/api/test_p6_2d_provenance.py tests/unit/api/test_p6_2d_entitlement.py -q -p no:cacheprovider --tb=short`
**Result:** **21 passed, 0 failed** (19 + 2); progress line `.....................` with no `F`/`E`; exit status **0**.

| # | Test | Assertion |
|---|---|---|
| 1 | `test_extract_records_server_derived_firm_and_mode` | firm = `firm-c1`, mode = `manual`, timestamp set |
| 2 | `test_repeated_consultant_actions_keep_write_once_provenance` | extract→map→validate leaves the record unchanged |
| 3 | `test_stage_claim_records_provenance` | the stage-claim boundary records provenance |
| 4 | `test_consultant_review_records_provenance` | review boundary records the firm |
| 5 | `test_consultant_submission_records_provenance` | submit boundary records the firm |
| 6 | `test_automatic_work_records_automatic_mode` | actor-agnostic: consultant on automatic work ⇒ `automatic` |
| 7 | `test_client_supplied_firm_org_and_actor_cannot_influence_provenance` | actor injection / parameter tampering ignored |
| 8 | `test_client_cannot_claim_processing_mode` | mode claim ignored (server-derived `manual`) |
| 9 | `test_second_firm_cannot_rewrite_established_provenance` | cross-firm later action does not rewrite |
| 10 | `test_membership_change_does_not_rewrite_recorded_provenance` | ambiguous later context ⇒ 403 + record unchanged |
| 11 | `test_cross_firm_consultant_denied_and_records_no_provenance` | 403 + no provenance |
| 12 | `test_cross_organisation_access_denied_and_records_no_provenance` | 403 + no provenance |
| 13 | `test_org_member_action_records_no_consultant_firm_provenance` | 200 (P6-2-D10 preserved) + no firm record |
| 14 | `test_internal_staff_action_records_no_consultant_firm_provenance` | 200 + no firm record |
| 15 | `test_every_consultant_action_route_records_provenance` | exactly 7 call sites (no alternate-route bypass) |
| 16 | `test_d7b_origin_vocabulary_is_unchanged` | two-value origin vocabulary intact |
| 17 | `test_d7b_new_migration_adds_no_consultant_origin_value` | migration adds no consultant origin; no origin constraint touched |
| 18 | `test_d7c_migration_is_additive_nullable_with_no_backfill` | no `NOT NULL` / `DEFAULT` / `UPDATE` / `INSERT` |
| 19 | `test_unrecorded_item_reports_no_provenance` | nothing fabricated |
| 20 | `test_entitlement_is_resolved_from_the_client_org_not_another_org` | D6: another org's entitlement cannot substitute |
| 21 | `test_denied_submission_consumes_and_charges_nothing` | D6: denied ⇒ zero consumption/charge/order/subscription |

### 11.2 Security matrix (prompt §16)

| Attack | Result |
|---|---|
| Firm injection (request supplies another firm id) | IGNORED — server-derived firm recorded (#7) |
| Cross-firm consultant (Firm A acting for Firm B) | DENIED (#11); cross-firm *rewrite* prevented (#9) |
| Cross-organisation access without an active grant | DENIED (#12) |
| Historical stability after access/firm change | PRESERVED (#10) |
| Origin integrity (no Consultant origin insertable) | PRESERVED (#16, #17) |
| Mode integrity (client cannot claim automatic/manual) | PRESERVED (#8) |
| Actor injection (substitute another actor identity) | IGNORED — actor columns come from the authenticated user (#7) |
| Alternate-route bypass | NONE — 7/7 consultant action call sites covered (#15) |
| Entitlement substitution (actor / other organisation) | DENIED (#20) |
| Charge on a denied operation | NONE (#21) |

### 11.3 Test-failure triage (prompt §22)

| Failure during development | Classification | Action |
|---|---|---|
| `FileNotFoundError` for the migration/workflow paths (4 tests) | **incorrect test expectation** (repo-root depth `parents[3]` vs `parents[4]`) | fixed the test's path resolution — no production change |
| `invalid item transition 'mapping' -> 'calculating'` (1 test) | **incorrect test expectation** (assumed validation would advance to `validated`; it legitimately routed back to `mapping`) | re-scoped the test to extract→map→validate and added a separate stage-claim test — no production change |
| `assert "processing_origin" not in executable` (1 test) | **incorrect test expectation** (the string occurs in a descriptive `COMMENT` literal) | tightened the assertion to the actual prohibition (no `ALTER`/`ADD COLUMN`/CHECK touching origin) — no production change |

No test was deleted, weakened or skipped to obtain green; no implementation defect was found by the focused suite after triage.

## 12. Regression results

### 12.1 Contract/regression suites (all executed, exit 0)

| Suite | Command | Result |
|---|---|---|
| New D7/D7b/D7c provenance suite | `pytest tests/unit/api/test_p6_2d_provenance.py -q` | **19 passed / 0 failed** (progress `...................`) |
| New D6 entitlement suite | `pytest tests/unit/api/test_p6_2d_entitlement.py -q` | **2 passed / 0 failed** |
| Both new suites together | see §11.1 | **21 passed / 0 failed**, exit **0** |
| Full unit suite (regression) | `cd backend && nohup bash -c './.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --tb=short > /tmp/p62_full.txt 2>&1; echo "EXIT=$?" >> …'` | reached **100%**, **no `F`/`E`/`s` characters**, **`EXIT=0`** |

### 12.2 Counted evidence (no fabricated numbers)

| Measure | Value | Basis |
|---|---|---|
| **Collected tests (post-change)** | **1,627** | `pytest tests/unit -q --collect-only` succeeded (`DONE=0`); per-file counts summed |
| **New tests added by this task** | **21** | `test_p6_2d_provenance.py` (19) + `test_p6_2d_entitlement.py` (2) |
| **Implied pre-change collected count** | **1,606** | 1,627 − 21 — **exactly matches the carried-forward P6-2C baseline**, independently confirming it |
| **Executed full suite** | 1,627 collected · **0 failed** · **0 errors** · **0 skipped observed** · exit code **0** | all-passing progress line to 100% + `EXIT=0` marker |
| **Passed** | **1,627** (inferred) | exit code 0 with zero failure/error/skip markers |

**Honesty notes (no over-claiming):** this environment's pytest configuration does not emit the terminal `N passed in Xs` summary line, so the passed count is *inferred* from `EXIT=0` plus the absence of any `F`/`E`/`s` in the run output — not read from a summary line. The pre-change *executed* count could not be captured (runner interruptions, §4); the pre-change *collected* count is established by arithmetic (1,627 − 21 = 1,606) and matches the previously reported figure.

### 12.3 Regression protection (§23) — verified unchanged

| Invariant | Evidence |
|---|---|
| Processing-origin vocabulary (2 values) | `test_d7b_origin_vocabulary_is_unchanged`; `domain/processing_origin.py` unmodified |
| RLS architecture | no migration statement touches RLS; no policy added/dropped/altered |
| Billing semantics | `backend/services/billing.py` unmodified; single charge site unchanged |
| Approval authority | `customer_review_item` still `require_org_admin()`; unmodified |
| Organisation ownership | entitlement resolved from `batch.organization_id`; unmodified |
| Consultant access model | `consultant_auth` authorization paths unmodified (only an additive resolver added) |
| Automatic/manual distinction | `api/processing_mode.py` unmodified; mode now also recorded durably |
| Automatic → manual fallback | untouched |
| P6-2C invariants | `calculated → approved` guard, `_STAGE_PERMISSION`, approval/CT-QC ordering all unmodified; existing P6-2C suites pass within the full run |


## 13. Risks

| # | Risk | Assessment / mitigation |
|---|---|---|
| R1 | The additive migration is **not applied** to any database yet, while the new repository methods reference the new columns. | Application-visible only when the code and schema are deployed together. This is the standard migration/deploy ordering; the change is additive + nullable, so applying it is non-destructive to existing rows. **Deployment must apply `20260910120000_p6_2d_consultant_provenance.sql` before/with the code.** Flagged for the independent verifier and the deployment step. |
| R2 | Item-level write-once provenance records the **establishing** firm only. | Deliberate (ratified: no rewrite of historical firm provenance). Later firms remain attributable via the append-only audit actor trail. Documented limitation; would need an append-only store (out of minimum-change scope). |
| R3 | `processing_mode` inherits the documented P1 containment limitation (mixed/corrected automatic work classified `automatic`). | Pre-existing, documented in `api/processing_mode.py`; P6-2D neither introduces nor is required to solve it. Recorded as an unresolved finding (U2). |
| R4 | Local test-runner instability (shell kills long runs) prevented a counted pre-change baseline. | Reported honestly (§4/§12); the post-change run uses a `nohup` wrapper + `EXIT=` marker so its result is provable. |
| R5 | Firm-deletion flows: the new FK uses `ON DELETE SET NULL`. | Chosen deliberately so an existing `consultant_profiles` deletion can never be blocked by provenance rows (no regression to firm administration); provenance is only cleared if the firm record itself is deleted. |

## 14. Unresolved findings

- **U1 (deployment step):** migration `20260910120000_p6_2d_consultant_provenance.sql` must be applied to each environment (dev/staging/prod) before the new code serves traffic. Not performed here (no DB was touched).
- **U2 (pre-existing limitation):** P1's processing-mode predicate cannot distinguish mixed/corrected automatic work; the durable `processing_mode` value inherits that classification. Documented in-module and in the migration comment.
- **U3 (scope boundary):** per-action firm attribution (each consultant action's firm, for items acted on by more than one firm) is not implemented — the ratified D7 text mandates non-rewrite, and "no field name is prescribed". Recorded as a candidate extension for a future phase, not a P6-2D defect.
- **U4 (test-baseline verification):** the pre-change counted baseline could not be established in this environment (runner interruptions). The verifier should re-measure both the pre- and post-change counts on a stable runner if a counted regression delta is required.
- **U5 (frontend):** no UI change was made; D7 provenance is not yet surfaced in any workspace (P6-2F scope). The values are retrievable via `get_item_consultant_provenance` for verification.

## 15. Files changed / created / unchanged

**Created (4):**

| Path | Class |
|---|---|
| `supabase/migrations/20260910120000_p6_2d_consultant_provenance.sql` | 4 (additive migration) |
| `backend/tests/unit/api/test_p6_2d_provenance.py` | 6 (tests) |
| `backend/tests/unit/api/test_p6_2d_entitlement.py` | 6 (tests) |
| `docs/cline/CARBONTALLY_P6_2D_IMPLEMENTATION_REPORT.md` + `docs/cline/prompt-history/CT-P6-2D-IMPL-20260910-001.md` | 8 (documentation) |

**Modified (4):**

| Path | Class | Change |
|---|---|---|
| `backend/data/manual_extraction.py` | 3 | + `record_consultant_provenance`, + `get_item_consultant_provenance` |
| `backend/api/consultant_auth.py` | 3 | + `resolve_consultant_firm_id` |
| `backend/api/v3_processing_workflow.py` | 3 | + `_record_consultant_provenance` helper + 7 call sites |
| `backend/tests/unit/api/fakes.py` | 6 | + fake mirrors of the two new repository methods |

**Explicitly unchanged (regression protection, §23):** `backend/services/billing.py` (billing semantics); `backend/api/processing_mode.py` (`item_is_automatic`, CT-QC prerequisite); `backend/domain/processing_origin.py` and the dual-origin migration (origin vocabulary); `backend/domain/partners.py` (state machine); all RLS policies and every other `supabase/migrations/*.sql`; `backend/api/v3_operations.py`; the frontend; the roadmap; the Blueprint; the PO Decision Register; the implementation contract; the investor-demo data.

## 16. Commit status

**No commit was made and nothing was pushed** (per prompt §26). Branch `main`, HEAD **`1639121`** before and after (unchanged). The working tree already contained pre-existing unrelated modifications before this task (not touched); no `git add .` was used and no staging was performed. If repository policy requires a commit for the completed implementation, that requirement is reported here for explicit instruction before any commit occurs.

## 17. Stop-condition confirmation

**CONFIRMED — stopped at the P6-2D boundary.** Performed: P6-2D implementation, focused tests, regression runs, evidence recorded, durable prompt history recorded. **Not performed:** P6-2E, P6-2F, independent verification, Phase 7, Phase 8, documentation cleanup, repository cleanup, deletion of stale documents, commit, push. No D8 (conversation model) or D11 (lifecycle notifications) work; no billing redesign; no PE↔Consultant handoff; no new role/capability/permission; no RLS change; no origin-vocabulary change; no historical backfill.

## 18. Final verdict

> **P6-2D IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION**

This is an **implementation** statement, not a verification or acceptance claim. Independent verification (a separate task) must re-derive every claim above from the runtime, the schema, the tests and the diffs — including the deployment prerequisite U1 and the baseline limitation U4.




