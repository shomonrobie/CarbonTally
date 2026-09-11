# CarbonTally — P6-2D Independent Verification Report (CP1 / IV)

**Prompt Ref:** `CT-P6-2D-IV-20260910-001`
**Response Ref:** `CT-P6-2D-IV-20260910-001-R1`
**Verification date/time:** 2026-09-10, 19:46 → 20:35 (+0600)
**Verifier role:** Independent verifier (fresh session; **not** the implementation agent; read-only, no remediation)
**Verification scope:** independently re-derive repository, schema, runtime, authorization, provenance, entitlement, mode, origin, billing, test, working-tree and scope-compliance state for the completed P6-2D (CP1) implementation against the ratified PO decisions and the Phase-6 Remainder Implementation Contract V1.0.
**Final verdict:** **P6-2D INDEPENDENTLY VERIFIED — PASS WITH NON-BLOCKING FINDINGS**

---

## 1. Authority documents inspected

`CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (§9 processing model + dimensional clarification; §11 evidence/provenance); `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (§9 Phase 6 gates); `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` (`PO-PHASE6-D6-R-`, `-D7-R-`, `-D7b-R-`, `-D7c-R-`, `-BILL-DEFER-`, `-D4-`, `-F-ACC-`, `-F-ENV-`, `-CAMPAIGN-20260910` + frozen P6-2C invariants); `CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md` (§4, §6, §8, §10, §15, §17, §19); `CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md`; `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4; `CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`; `docs/cline/CARBONTALLY_P6_2D_IMPLEMENTATION_REPORT.md`; `docs/cline/prompt-history/CT-P6-2D-IMPL-20260910-001.md`.

## 2. Repository baseline (independently captured)

| Item | Observed |
|---|---|
| Branch | `main` |
| HEAD | `1639121` |
| Porcelain entries | **668**; tracked `M` entries **284**; untracked 232 |
| Pre-existing modifications | Yes — substantial (uncommitted work from earlier gates; the `git diff` vs HEAD is ~650k lines and **cannot** be attributed to P6-2D) |
| Independent attribution method | **File-modification window scan** (`find … -newermt '2026-09-10 19:12'`), independent of `git`: exactly **7** files were modified inside the P6-2D window (19:21–19:30) |

## 3. Actual files created/changed (IV-attributed)

**Created in the P6-2D window:** `supabase/migrations/20260910120000_p6_2d_consultant_provenance.sql` (19:21); `backend/tests/unit/api/test_p6_2d_provenance.py` (19:29); `backend/tests/unit/api/test_p6_2d_entitlement.py` (19:30); `docs/cline/CARBONTALLY_P6_2D_IMPLEMENTATION_REPORT.md`; `docs/cline/prompt-history/CT-P6-2D-IMPL-20260910-001.md`.
**Modified in the P6-2D window:** `backend/api/consultant_auth.py` (19:22); `backend/data/manual_extraction.py` (19:22); `backend/api/v3_processing_workflow.py` (19:24); `backend/tests/unit/api/fakes.py` (19:26).

**Unexpected changes inside the window: NONE.** No frontend file, no other migration, no `billing.py`, no `processing_mode.py`, no `domain/processing_origin.py`, no RLS/policy file and no architecture/roadmap/register file has an mtime inside the P6-2D window. `backend/api/v3_manual_extraction.py` (present in porcelain) has mtime **2026-09-05** → pre-existing, not P6-2D.

## 4. Migration verification — **VERIFIED**

Read directly (`20260910120000_p6_2d_consultant_provenance.sql`, 82 lines):

| Requirement | Evidence |
|---|---|
| Additive | `ALTER TABLE public.manual_extraction_items ADD COLUMN IF NOT EXISTS …` ×3 only |
| Nullable | no `NOT NULL` in the file |
| Intended table only | `public.manual_extraction_items` only |
| No backfill | no `UPDATE`, no `INSERT` in the executable SQL |
| No fabricated defaults | no `DEFAULT` |
| No RLS change | no `POLICY` / `ENABLE ROW LEVEL SECURITY` statement at all |
| No origin change | no `processing_origin` statement; the name appears only inside descriptive `COMMENT` literals |
| Intended fields | `consultant_firm_id uuid`, `processing_mode text`, `consultant_provenance_at timestamptz` |
| FK behaviour | `REFERENCES public.consultant_profiles(id) ON DELETE SET NULL` (cannot block an existing firm-deletion flow) |
| Constraint | `manual_extraction_items_processing_mode_check` → `processing_mode IS NULL OR processing_mode IN ('automatic','manual')` (drop-if-exists then add → idempotent) |
| Applied state | **NOT APPLIED** — no database was contacted or modified by this verification (limitation L1) |

## 5. Firm provenance verification — **VERIFIED**

Traced executable code (not comments):

1. **Resolution point:** `resolve_consultant_firm_id(current_user, repos)` — `backend/api/consultant_auth.py:184`.
2. **Authorization context:** the existing canonical `_resolve_context` (active `consultant_firm_members` membership → single distinct firm → active firm profile); returns `str(context.firm_member.firm_id)`.
3. **Request influence: NONE** — the resolver's only inputs are the authenticated user and the repository bundle. Probe **P1**: body + query-string + header firm claims are all ignored; stored `firm-c1`.
4. **Organization context enforced:** routes resolve the batch/item server-side (`_get_checked_item` → `ensure_processing_org_access(batch.organization_id)`); the consultant gate re-checks the active grant for that server-derived org.
5. **Cross-firm access rejected:** probe **P6** → 403, no provenance, no charge.
6. **Cross-organisation access rejected:** probe **P7** → 403, no provenance.
7. **Written only when NULL:** SQL `WHERE id = $1 AND consultant_firm_id IS NULL` (`backend/data/manual_extraction.py:611`).
8. **Existing value cannot be overwritten:** probe **P5** — a direct second repository write returned `False` and left `(firm-c1, manual)`; probe **P4** — a second firm's later authorised action left `firm-c1` intact.

## 6. Processing-mode verification — **VERIFIED**

1. **Derivation point:** `_record_consultant_provenance` → `mode = "automatic" if await item_is_automatic(repos, item) else "manual"` (`v3_processing_workflow.py:192–227`).
2. **Authoritative logic reused:** yes — the existing `item_is_automatic` predicate (`api/processing_mode.py:39`); no parallel mode logic was introduced.
3. **Request influence: NONE** — probe **P2**: body claims `processing_mode="automatic"` / `mode="AUTOMATIC"` on a manual item → stored **`manual`**.
4. **Actor influence: NONE** — probe **P10**: a **consultant** acting on automatic work stored **`automatic`** (actor-agnostic); the same actor on manual work stores `manual` (P1/P2).
5. **Actor-agnostic and stored separately from origin** — distinct column; probe **P9** confirms the origin vocabulary is untouched.

## 7. Processing-origin verification (D7b) — **VERIFIED**

- `domain/processing_origin.py` exposes exactly `CARBONTALLY_INTERNAL` / `PROCESSING_ENTITY`; `ORIGIN_LABELS` has exactly those two keys, no `CONSULTANT` (probe **P9**).
- Repository-wide scan for a `CONSULTANT` origin value in `supabase/migrations/**` → **no match**.
- The P6-2D migration contains no origin statement and no consultant value (executable SQL verified).
- No origin CHECK constraint, routing, queue, state-machine or stage-mapping change exists in the P6-2D file set (`_STAGE_PERMISSION` unchanged: source/extraction→extract, mapping→map, validation→validate, calculation→calculate, review→submit).
- The new `processing_mode` column is a **mode** record, never consulted for origin routing.

## 8. Seven-action coverage matrix — **VERIFIED**

Independently derived from current source (line numbers are current):

| # | Action | Route (line) | Authorization before provenance | Provenance | Mode | Mutation after | Alternate route |
|---|---|---|---|---|---|---|---|
| 1 | start | `POST /items/{id}/start` (L393) | `_get_checked_item` → org access (L184) + consultant gate `_STAGE_PERMISSION` (L186/L370) + CT-QC prerequisite (L425) | L428 | yes | `set_item_status` L429 | none found |
| 2 | extract | L432 | `_get_checked_item(permission="extract")` | L444 | yes | `save_extracted_data` L445 | none found |
| 3 | map | L450 | `_get_checked_item(permission="map")` | L470 | yes | `save_mapped_data` L471 | none found |
| 4 | validate | L481 | `_get_checked_item(permission="validate")` | L506 | yes | `set_item_status` L507 | none found |
| 5 | consultant-review | L587 | `ensure_consultant_review_authorized` (L613) + state eligibility | L636 | yes | `set_item_status` L637 | none found |
| 6 | consultant-submit | L699 | `ensure_consultant_submission_authorized` (L729) + state + **entitlement preflight** (L757) | L763 | yes | `set_item_status` L764 | none found |
| 7 | calculate | L780 | `_get_checked_item(permission="calculate")` + batch-state check | L805 | yes | `save_calculation` L883 | none found |

Supplementary: `start` with `stage="qc"` returns **before** the provenance call (no working status → early return) → no provenance for a non-action. Route registration independently confirmed at runtime for all seven paths (+ `customer-review`), 335 routes total.

## 9. Authorization-before-provenance verification — **VERIFIED**

Observed order at every wired boundary:

```
authentication (require_auth)
 → organization access (ensure_processing_org_access on server-derived batch.organization_id)
 → consultant authorization (ensure_consultant_processing_authorized / _review_ / _submission_)
 → workflow-state eligibility (_require_transition / status checks)
 → [submit only] non-charging entitlement preflight
 → PROVENANCE RECORD
 → data/state mutation
```

Denied-request evidence (no provenance written): **P6** (cross-firm → 403, `None`), **P7** (cross-org → 403, `None`), **P11** (unauthenticated → 401, `None`), **P8** (org-member/staff → no firm provenance). **No route was found in which provenance precedes authorization.**

## 10. Write-once verification — **VERIFIED**

Persistence-level guarantee (not a Python-only check): the repository issues

```sql
UPDATE public.manual_extraction_items
   SET consultant_firm_id = $2, processing_mode = $3,
       consultant_provenance_at = NOW(), updated_at = NOW()
 WHERE id = $1 AND consultant_firm_id IS NULL
```

so a row already carrying provenance matches zero rows and is left untouched. Independently exercised: **P5** (second direct write returned `False`; stored `firm-c1`/`manual` unchanged), **P4** (later authorised action by a different firm left the original value), **P2** (mode not rewritten by a claim).

## 11. D6 entitlement/billing verification — **VERIFIED**

| Check | Evidence |
|---|---|
| Client Organisation owns entitlement | `ensure_processing_entitlement(batch.organization_id)` at `v3_processing_workflow.py:757`; org resolved server-side |
| Non-charging submission preflight intact | preflight performs no mutation; probe **P6** shows `org-a` ledger `0` after a denied submission |
| Approval-time enforcement canonical | single charge site `v3_processing_workflow.py:966`; repository-wide scan finds only the definition (`services/billing.py:693`) plus this one call |
| No alternative/duplicate charging path | exactly one `charge_processing(` call site in `api/` |
| No charge on denial | probe P6 (403 ⇒ ledger 0); existing P6-2B-2 / P6-BILL-1 suites pass in the IV run |
| Consultant cannot substitute for org entitlement | probe P6/P7 (another org's grant is irrelevant); IV-observed D6 tests pass |
| Billing not redesigned by P6-2D | `backend/services/billing.py` mtime is **outside** the P6-2D window |

## 12. Security attack matrix — independently executed

Probes were written by the verifier in `/tmp/iv_probe.py` (outside the repository) and executed against the **real application wiring** (`create_app()` + real route handlers + dependency overrides to the in-memory repository implementation; no database, no repository writes).

**Result: 11/11 PASS, EXIT=0**

| # | Attack | Method | Observed | Verdict |
|---|---|---|---|---|
| P1 | **Firm injection** | body (`consultant_firm_id`, `firm_id`, `firm`, `organization_id`, `consultant_client_id`) + query string + headers | extract 200; stored firm `firm-c1` (never `firm-evil`) | **PASS** |
| P2 | **Mode injection** | body `processing_mode="automatic"`, `mode="AUTOMATIC"` on a manual item | stored mode `manual` | **PASS** |
| P3 | **Actor injection** | extra body actor fields (`extracted_by`, `actor`) | item `extracted_by = u-c1` (authenticated identity) | **PASS** |
| P4 | **Provenance overwrite** | a second firm (legitimately granted for the same client) acts later | map 200; stored firm still `firm-c1` | **PASS** |
| P5 | **Write-once (persistence)** | direct second repository write with a different firm/mode | returned `False`; stored `(firm-c1, manual)` unchanged | **PASS** |
| P6 | **Cross-firm** | firm granted only for `org-b` acts on an `org-a` item | 403; provenance `None`; `org-a` ledger 0 | **PASS** |
| P7 | **Cross-organisation** | consultant granted `org-a` acts on an `org-b` item | 403; provenance `None` | **PASS** |
| P8 | **Non-consultant actors** | organisation member, then internal staff, extract | 200; provenance `None` (no firm recorded) | **PASS** |
| P9 | **Origin injection / vocabulary** | inspect `domain.processing_origin` + repo-wide migration scan | exactly `{CARBONTALLY_INTERNAL, PROCESSING_ENTITY}`; no `CONSULTANT` origin anywhere | **PASS** |
| P10 | **Actor-agnostic mode** | consultant acts on **automatic** work | stored mode `automatic`, firm `firm-c1` | **PASS** |
| P11 | **Unauthenticated** | no identity | 401; provenance `None` | **PASS** |

**Alternate-route bypass scan (independent):** every item-mutating API surface outside `v3_processing_workflow.py` was enumerated with its guard: `api/v3_operations.py` → `require_staff()` / `require_internal_staff` (consultants are not staff); `api/v3_pe.py` → `require_pe_member` / `require_pe_capability(...)` (consultants are not PE); `api/v3_manual_extraction.py:120` → `require_org_member()` + `ensure_org_access(batch.organization_id)` (consultants are not org members); `api/v3_automatic_processing.py` → `require_auth` + `_authorize_consultant_job_action(...)` (see finding F1). **No route was found that lets a consultant mutate an item while bypassing authorization or the entitlement/CT-QC guards.**

## 13. RLS verification — **VERIFIED (static) / LIMITATION (live)**

- The P6-2D migration contains **no** RLS statement (no `POLICY`, no `ALTER POLICY`, no `ENABLE/DISABLE ROW LEVEL SECURITY`) — read directly.
- No RLS/policy file was modified inside the P6-2D window (mtime scan); in particular no `*rls*` migration appears.
- **Limitation L1:** no live Supabase/PostgreSQL instance was contacted, so *live* RLS behaviour around the new columns was **not** exercised. Static evidence is consistent with the contract's "no RLS change required" (the new nullable column inherits the table's existing posture). No test-only bypass and no policy relaxation was introduced.

## 14. Focused test results (independently executed)

**Command:** `cd backend && ./.venv/bin/python -m pytest tests/unit/api/test_p6_2d_provenance.py tests/unit/api/test_p6_2d_entitlement.py tests/unit/api/test_p6_2c_approval_boundary.py -q -p no:cacheprovider --tb=short`
**Result:** **51 tests, all passing** (progress line `...................................................` to 100%), **EXIT=0** — the new D7/D7b/D7c suite (19), the new D6 suite (2) and the pre-existing P6-2C approval-boundary suite (30) all pass in a fresh session, with no skips and no errors.

## 15. Full regression results (independently executed)

**Command:** `cd backend && nohup bash -c './.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --tb=short > /tmp/iv_full.txt 2>&1; echo "EXIT=$?" >> /tmp/iv_full.txt'`

| Measure | IV-observed value |
|---|---|
| Progress characters | **1,627 `.`**, **0 `F`**, **0 `E`**, **0 `s`** (character-frequency count over the progress lines) |
| Exit code | **0** (`EXIT=0` marker written after pytest returned) |
| Passed / failed / skipped / errors | **1,627 / 0 / 0 / 0** |
| Collected count (separate run) | **1,627** — `pytest tests/unit -q --collect-only` succeeded (`DONE=0`); per-file counts summed by the verifier |

### Test-count claim assessment

| Claim element | Verdict | Basis |
|---|---|---|
| Current collected count = **1,627** | **VERIFIED** | independently re-measured (sum of per-file collection counts) |
| New tests added = **21** | **VERIFIED** | `test_p6_2d_provenance.py` (19) + `test_p6_2d_entitlement.py` (2), independently counted; consistent with 1,627 − 1,606 |
| Baseline **1,606** | **INFERRED (not directly observed)** | arithmetic (1,627 − 21) matches the carried-forward P6-2C figure; no pre-change execution count was captured in this environment (L2) |
| Pre-change *executed* count | **NOT VERIFIED** | never captured by either session |

**No PASS in this report rests on the implementation report's own assertions.**

## 16. Runtime / import results — **VERIFIED**

- `python -m compileall` on `api/v3_processing_workflow.py`, `api/consultant_auth.py`, `data/manual_extraction.py` → **OK**.
- `create_app()` → **335 routes**, no import/runtime error.
- Route existence verified at runtime: `/api/v3/processing/items/{item_id}/start|extract|map|validate|calculate|consultant-review|consultant-submit|customer-review` → **all FOUND**.
- `resolve_consultant_firm_id`, `record_consultant_provenance`, `get_item_consultant_provenance` import and exist on the real symbols.

## 17. Scope-creep verification — **VERIFIED (no creep)**

| Out-of-scope item | IV finding |
|---|---|
| P6-2E (D8 conversation kind / D11 lifecycle notifications) | No conversation kind added; no lifecycle event keys added; no messaging/notification file inside the P6-2D window |
| P6-2F / frontend | **No frontend file** inside the P6-2D window (mtime scan) |
| Phase 7 / Phase 8 | nothing added |
| PE↔Consultant handoff | nothing added |
| Billing redesign | `services/billing.py` untouched in the window; exactly one charge call site (pre-existing) |
| New roles/capabilities/permissions | none added (no permission/flag/role change in the window) |
| RLS redesign | none (no policy statement, no policy file touched) |
| New origin vocabulary / historical backfill | none (probe P9; migration has no `UPDATE`/`INSERT`/`DEFAULT`) |

## 18. Documentation / history verification — **VERIFIED**

- `docs/cline/CARBONTALLY_P6_2D_IMPLEMENTATION_REPORT.md` exists (18 `##` sections) and contains the required elements (objective, documents read, areas inspected, baseline, exact changes, provenance design, D6, D7, D7c, D7b, tests, regression, risks, unresolved findings, files, commit status, stop-condition, verdict).
- `docs/cline/prompt-history/CT-P6-2D-IMPL-20260910-001.md` exists and contains the Prompt Ref, Response Ref, the **complete prompt text**, the response, execution evidence and the verdict/stop-condition statement.
- Neither record was modified by this verification.

## 19. Evidence limitations

| # | Limitation | Impact |
|---|---|---|
| L1 | **No live database / no RLS runtime**: the migration is unapplied and no Supabase instance was contacted (correctly — verification must not mutate). | Live RLS behaviour, the actual DB constraint enforcement and DB-level write-once behaviour are **NOT VERIFIED** at the database tier. Application-tier and static SQL evidence is complete. |
| L2 | **Local runner instability**: this environment's shell kills long pytest runs and its pytest configuration prints no `N passed` summary line. | Counts were derived from per-file collection sums and progress-character frequency (strong, but not a summary line). The **pre-change executed baseline (1,606)** is INFERRED, not observed. |
| L3 | **Working-tree attribution**: `git diff` vs HEAD includes ~650k lines of pre-existing uncommitted work from earlier gates, so a diff-based attribution of P6-2D alone is impossible. | Attribution was instead established by an mtime window scan (19:12–19:35) — independent of git and disclosed. Residual risk: an edit made inside the window by another process would be mis-attributed; none was found. |
| L4 | **No browser/E2E tier** (reserved for P6-2F). | UI/behavioural acceptance is out of scope for this gate; no UI change was expected or found. |

## 20. Findings

| # | Finding | Evidence | Class |
|---|---|---|---|
| F1 | **Consultant-reachable automation job actions (`POST /api/v3/automatic-processing/jobs/{job_id}/confirm` and `/retry`) do not record D7 firm/mode provenance.** They are guarded by the canonical `_authorize_consultant_job_action(permission="confirm_automation")` and they mutate item data (`save_extracted_data` / `save_mapped_data`), but they carry no `_record_consultant_provenance` call. | `api/v3_automatic_processing.py:134–172, 293–345, 415+`; provenance call-site scan finds the helper only in `v3_processing_workflow.py` (7 sites) | **NON-BLOCKING** (coverage extension). The implementation contract §6.2 scoped D7 capture to the seven item-workflow actions and described consultant-triggered automation `confirm` as conditional ("if the PO later extends it"). It is **not** a security bypass: authorization is fully enforced, actor attribution exists via the append-only `_record_human_gate_audit`, and no client-controlled firm/mode/origin path exists. **Recommendation:** PO/contract clarification at the next gate on whether D7 should cover automation confirm/retry; if yes, this is a small additive follow-up. |
| F2 | **Item-level provenance records the establishing firm only.** A different firm acting later is not separately attributed on the item. | SQL guard `consultant_firm_id IS NULL`; probe P4 | **NON-BLOCKING** — required by the ratified "must not rewrite historical firm provenance"; per-action firm attribution would need an append-only store (not required by D7: "no database field name is prescribed"). Disclosed by the implementer; confirmed accurate. |
| F3 | **`processing_mode` inherits the pre-existing P1 containment limitation** (mixed/corrected automatic work is classified `automatic`). | `api/processing_mode.py` module docstring (pre-existing); probe P10 | **NON-BLOCKING** — pre-existing, documented, out of P6-2D's required scope. |
| F4 | **Migration is not applied to any database**, and live DB/RLS behaviour was not exercised. | L1 | **ENVIRONMENTAL / DEPLOYMENT** — deploy prerequisite, not a defect. |
| F5 | **Pre-change executed baseline (1,606) is inferred**, not observed; pytest emits no summary line here. | L2 | **ENVIRONMENTAL** (evidence quality), disclosed in both the implementation report and this one. |
| F6 | **P6-2D changes cannot be isolated by `git diff`** (large pre-existing working tree). | L3 | **ENVIRONMENTAL** — attribution done by mtime window; disclosed. |
| F7 | **Minor documentation drift:** the implementation report lists the `calculate` provenance call at `L803`; the current line is `L805` (later edits shifted lines by +2). All other listed line numbers match. | Report §5.2 vs current source | **NON-BLOCKING** (documentation accuracy, no behavioural impact). Deliberately **not** corrected (read-only verification). |
| F8 | Pre-existing stale wording in the roadmap (P6-2C "NEXT") and register (self-superseded D7/D7c "pending", contract "not created yet") remains. | Read during this IV | **NON-BLOCKING / PRE-EXISTING** — not introduced by P6-2D; documentation cleanup is deferred by governance. Not modified. |

## 21. Blocking / non-blocking classification

| Classification | Count | Items |
|---|---|---|
| **BLOCKING** | **0** | none |
| NON-BLOCKING | 5 | F1 (coverage extension, needs PO/contract clarification), F2, F3, F7, F8 |
| ENVIRONMENTAL (evidence limitations) | 3 | L1/F4, L2/F5, L3/F6 (plus L4 scope note) |

**No ratified Phase-6 security, entitlement, provenance, origin, authorization or scope invariant was found violated.** All client-input, cross-tenant, overwrite, origin and alternate-route attack paths tested were closed; no blocking defect was found; no stop condition was triggered.

## 22. Final verdict

> **P6-2D INDEPENDENTLY VERIFIED — PASS WITH NON-BLOCKING FINDINGS**

Justification: every material invariant ratified for P6-2D was independently verified at code, runtime, probe and test tiers (D6 ownership/preflight/charge boundary; D7 server-derived, write-once, actor-agnostic, request-independent provenance across the seven boundaries with authorization-before-provenance ordering; D7b origin vocabulary unchanged; D7c no backfill and no fabricated provenance), with 11/11 independent attack probes and a green 1,627-test suite. The remaining items are a disclosed coverage observation (F1) requiring PO/contract clarification and non-blocking documentation/evidence limitations — none of which is a security or invariant defect.

## 23. Explicit stop-condition confirmation

**CONFIRMED — the verifier stopped at the P6-2D boundary.**

- No production code, test code, migration, schema, frontend, architecture document, roadmap, PO register, implementation report or prompt-history record was modified.
- No defect was fixed; F1/F2/F3/F7/F8 are **recorded only**.
- No database was contacted or mutated; the migration was **not** applied.
- No `git add`, `git commit` or `git push` was used; HEAD remains `1639121` on `main`.
- No work was begun on P6-2E, P6-2F, Phase 7 or Phase 8; the roadmap was not advanced.
- Verifier probes were written outside the repository (`/tmp/iv_probe.py`) and used only in-memory repositories.

**Scope-decision note for the project owner:** F1 (consultant-reachable automation confirm/retry not recording D7 firm provenance) is the one item that may warrant an explicit decision — either "D7 covers only the seven item-workflow actions (no action required)" or "extend D7 coverage to automation confirm/retry" (a small additive follow-up). It does not block P6-2D acceptance as scoped, and it must not be treated as authorization for new work without that decision.




