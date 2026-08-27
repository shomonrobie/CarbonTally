# CarbonTally V3 — POST-IMPLEMENTATION MASTER UX / SECURITY RECONCILIATION AUDIT

| | |
|---|---|
| Document type | Independent post-implementation audit + reconciliation |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Date | 2026-08-27 |
| Status | AUDIT — evidence-based; no code changes made during this pass |
| Overall status | **GREEN WITH CONDITIONS** |

## Executive Summary

The four-phase implementation claim is **largely correct but not unconditionally
complete**. The core product decisions (D1–D17, D18, D20, N1, N2, N3) are
implemented and server-authoritative; the canonical workflow is UI-complete
end-to-end; the frontend builds, 109 frontend tests and the full backend unit
suite pass, and the security-relevant RLS integration suite
(`test_v3_rls_behavior.py`) passes against the dedicated test database.

However, independent verification found **one security-adjacent P1 finding** and
several **P2 completeness gaps** that the earlier "genuinely complete" claim did
not surface:

- **P1 — D32 signed-URL boundary is not applied on the operator/PE item
  endpoints.** The internal `item_workspace` and customer workspace sign
  document URLs correctly, but `/api/v3/ops/batches/{id}/items`,
  `/api/v3/ops/entities/{eid}/extraction/batches/{bid}/items` and
  `/api/v3/ops/entities/{eid}/extraction/items/{iid}` return the raw persisted
  `file_url`. Current local data stores bare storage paths (no active public
  download vector today), but the "documents are served only via short-lived
  signed URLs" invariant is not enforced on these paths, and any legacy/future
  public URL in `file_url` would be returned to operators and PE staff verbatim.
  The same root cause **functionally breaks the source viewer** in the operator
  and PE extraction workbenches.
- **P2 — D19 workbench features partially wired**: field-confidence badges
  (`ConfidenceBadge` unused), source↔field linking (absent), inline validation
  (absent), lock states (prop never passed), keyboard pane resizing (pointer-only).
- **P2 — D21 tokenization incomplete**: `ct-*` tokens exist and dual-green is
  consolidated, but component rules still use raw hex values and `ops.css` still
  uses the legacy `#2563eb` blue instead of the unified `#2b6cb0` accent.
- **Environment verification limits (NOT VERIFIED, not failures)**: the local
  Supabase auth/storage gateway (127.0.0.1:54325) is not running, so
  authenticated-page browser QA and live end-to-end messaging/storage could not
  be exercised. Public-page headless Chrome QA showed no horizontal overflow at
  1280/768/375px. Production state is **PRODUCTION NOT VERIFIED**.

No critical (P0) security defect was found. The PE no-download boundary is
structurally protected (private bucket, signed-URL convention, PE denied
messaging/RLS), but the API-level signed-URL application on the operator/PE
workbench paths must be completed (P1) before "complete" is claimed without
conditions.

---

## 1. Source-of-Truth Verification

Authoritative documents used (all under `docs/audit/openhands/ui-ux/`):
`MASTER_INDEX.md`, `README.md`, `MASTER_SCREEN_INVENTORY.md`,
`MASTER_WORKFLOW_MAP.md`, `MASTER_UI_UX_ASCII_DESIGNS.md`,
`MASTER_UX_RECOMMENDATION.md`, `MASTER_UX_DECISION_RECONCILIATION_REPORT.md`,
`CARBONTALLY_V3_DESIGN_SYSTEM.md`, `UI_UX_IMPLEMENTATION_MATRIX.md`,
`UI_UX_OPTION_A/B/C_*.md`, `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md`,
`CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (reference copy).

The current Product Owner decision register is authoritative. No obsolete
document overrides it.

---

## 2. Decision Verification

| Decision | Status | Evidence |
|---|---|---|
| D1 Viewer permissions | **PASS** | Viewer read-only; mutation guards deny; RLS org scope |
| D2 Customer processing participation | **PASS** | Review vs approval distinct surfaces/APIs; `customer-review` separate and gated |
| D3 Consultant operating model | **PASS** | Active-client model; server re-authorises per request |
| D4 Owner vs Admin | **PASS** | Org roles distinct from staff/admin |
| D5 Customer approver | **PASS** | `customer-review` requires `require_org_admin()`; unit-tested |
| D6 PE validation/review/QC | **PARTIAL** | Entity workspace + QC gates; **PE source viewer broken / signed-URL not applied (P1)** |
| D7 Report model | **PASS** | Reports + versions + evidence |
| D8 Multi-org consultant | **PASS** | Client grants + active-client context |
| D9 Custom factors | **PASS** | API+RLS+UI; app DB has NO DELETE policy (verified live) |
| D10 Invitation acceptance | **PASS** | Members/invitations + onboarding |
| D11 Payment provider | **PASS** | Provider-neutral; none claimed |
| D12 Public pricing | **PASS** | `/pricing` present; `/privacy` fixed (U3) |
| D13 Public acquisition | **PASS** | No fake waitlist |
| D14 Consultant acquisition | **PASS** | Consultant surfaces |
| D15 Data retention → N3 | **PASS** | See N3 |
| D16 AI governance | **PASS** | No AI backend, no credentials, no fabricated assistant |
| D17 Master data | **PASS** | Facilities/Locations/Assets/Vehicles/Suppliers present |
| D18 Workflow-first nav | **PASS** | Top rail only; no left sidebar in workbenches |

## 3. Screen Coverage

Classification legend: IMPLEMENTED · PARTIALLY_IMPLEMENTED · MISSING ·
INTENTIONALLY_NOT_IMPLEMENTED · DUPLICATE · OBSOLETE · BLOCKED_BY_BACKEND ·
BLOCKED_BY_PO_DECISION.

### Public / auth / onboarding
| Screen | Route | Classification | Notes |
|---|---|---|---|
| Landing | `/` | IMPLEMENTED | |
| Platform overview | `/platform` | IMPLEMENTED | |
| Services / Processing services / Consultants | `/services` `/processing-services` `/consultants` | IMPLEMENTED | |
| Pricing | `/pricing` | IMPLEMENTED | U3 fixed |
| About / Contact / Glossary | `/about` `/contact` `/glossary` | IMPLEMENTED | |
| Privacy / Cookies / Terms | `/privacy` `/cookies` `/terms` | IMPLEMENTED | |
| Sign in / Signup / Beta signup | `/login` `/signup` `/beta/signup` | IMPLEMENTED | |
| Auth callback / Magic link | `/auth/callback` `/auth/magic` | IMPLEMENTED | |
| Onboarding | `/onboarding` | IMPLEMENTED | |

### Customer workspace
| Screen | Route | Classification | Notes |
|---|---|---|---|
| Dashboard | `/home` | IMPLEMENTED | |
| Emissions | `/emissions` | IMPLEMENTED | |
| Documents | `/documents` | IMPLEMENTED | |
| Processing | `/processing` | IMPLEMENTED | |
| Existing data discovery | `/existing-data` | IMPLEMENTED | |
| Issues | `/issues` | IMPLEMENTED | |
| Messaging | `/messaging` | IMPLEMENTED | API+RLS verified; live E2E NOT VERIFIED (gateway down) |
| Notifications | `/notifications` | IMPLEMENTED | |
| Reports / Report detail | `/reports` `/reports/:id` | IMPLEMENTED | evidence trail added |
| Billing | `/billing` | IMPLEMENTED | |
| Organisation hub | `/organization` | IMPLEMENTED | 8 tabs |
| Org — Members | tab | IMPLEMENTED | |
| Org — Facilities & Assets | tab | IMPLEMENTED | |
| Org — Suppliers | tab | IMPLEMENTED | |
| Org — Custom Factors | tab | IMPLEMENTED (was UI MISSING) | |
| Org — Vehicles | tab | IMPLEMENTED (was DESIGN ONLY) | table+RLS+API+UI; migration verified |
| Org — Locations | tab | IMPLEMENTED (facilities reuse, N2) | |
| Org — Activity | tab | IMPLEMENTED (was DESIGN ONLY) | |
| Org — Settings | tab | PARTIALLY_IMPLEMENTED | ProfileTab covers org profile/metadata; platform retention under Ops Settings |
| Customer Review & Approve | `/review` `/review/:id` | IMPLEMENTED (was target) | evidence-first; D5 gate |

### Consultant / Staff / PE / Admin
| Screen | Route | Classification | Notes |
|---|---|---|---|
| Consultant dashboard/workspace/messaging/branding/whitelabel | `/consultant` views | IMPLEMENTED | |
| Ops dashboard / Data entry / Review / QC / Staff / Roles / Entities / SLA / Commercial | `/ops` tabs | IMPLEMENTED | |
| Work item workspace / Extraction panel | `/ops` queues | PARTIALLY_IMPLEMENTED | D19 shell present; **source viewer broken (raw file_url)** |
| Ops Issues triage | `/ops` tab | IMPLEMENTED | |
| Ops Messaging | `/ops` tab | IMPLEMENTED | staff-admin gated |
| Ops Audit console | `/ops` tab | IMPLEMENTED | |
| Ops Settings (retention) | `/ops` tab | IMPLEMENTED | |
| PE extraction workspace | `/ops` (entity staff) | PARTIALLY_IMPLEMENTED | entity scope + D19 shell; **source viewer broken (raw file_url)** |
| Entity dashboard | `/ops/entities/{id}/dashboard` | IMPLEMENTED | |
| Admin audit console | `/ops` → Audit | IMPLEMENTED | |
| Platform admin console (consolidated) | target | PARTIALLY_IMPLEMENTED | dense tabs exist; no single consolidated console |

No inventory screen is MISSING at the route level; remaining gaps are
functional (see §16).

| D19 Workbench | **PARTIAL** | Shell+presets+viewer exist; confidence/source↔field/inline-validation/lock unwired; operator/PE viewer broken |
| D20 Responsive | **PASS** | Media queries + tray; public overflow clean |
| D21 Design system | **PARTIAL** | Tokens + green consolidated; rules not tokenized; stray `#2563eb` |
| N1 Messaging | **PASS** (gap documented) | API+RLS+UI enforced; staff path gated; PE denied; PE-internal messaging is a documented data-model gap |
| N2 Locations | **PASS** | Facilities reuse |
| N3 Retention | **PASS** | Config + enforcement command + dry-run + exclusions |

## 4. Workflow Coverage

Canonical pipeline: Upload → Classify → Extract → Map → Validate → PE Review/QC
→ CarbonTally QC → Calculate → Evidence → Customer Review → Customer Approval →
Reporting.

| Workflow | Classification | Notes |
|---|---|---|
| Upload | IMPLEMENTED | Documents/Processing; D32 private storage |
| Classification | IMPLEMENTED | Backend classifier (`utils/document_classifier.py`) |
| Extraction | PARTIALLY_IMPLEMENTED | Workbench + form work; **source viewer broken for operator/PE (raw file_url)** |
| Mapping | IMPLEMENTED | Factor candidates; server-authoritative selection |
| Validation | PARTIALLY_IMPLEMENTED | Backend ValidationEngine A1–A9; **no inline field-validation UI in the workbench** |
| PE review/QC | IMPLEMENTED | Entity workspace + status transitions |
| CarbonTally QC | IMPLEMENTED | QC queue |
| Calculation | IMPLEMENTED | Server engine; client never supplies result; snapshot persisted |
| Evidence | IMPLEMENTED | EvidenceRecordPanel + EvidenceTrail (report detail) |
| Customer review | IMPLEMENTED | `/review` queue + evidence-first detail |
| Customer approval | IMPLEMENTED | Approve/Reject with reason; `require_org_admin` (D5); audit |
| Reporting | IMPLEMENTED | Reports + versions + exports |
| Rework / rejection loops | IMPLEMENTED | Backend `ITEM_STATUS_FLOW`; reasons recorded |
| Clarification (mediated) | IMPLEMENTED | Entity-scoped issues → CarbonTally → customer; no direct chat |
| Assignment (D22) | IMPLEMENTED | Exactly-one-party; audit trail |
| Issue workflow | IMPLEMENTED | open→…→closed; ops triage UI |
| Onboarding | IMPLEMENTED | Self-service + discovery |
| Messaging | IMPLEMENTED | N1 boundaries (API+RLS); live E2E NOT VERIFIED |
| Billing | IMPLEMENTED | D37 commercial; provider-neutral |
| Master data | IMPLEMENTED | D17 all five entities |
| Admin workflows | PARTIALLY_IMPLEMENTED | Dense tabs + audit + settings; no consolidated console |
| Retention | IMPLEMENTED | Config + enforcement command (deployment scheduler pending) |
| AI escalation | INTENTIONALLY_NOT_IMPLEMENTED | Assistant programme decision; no fabricated AI |

**Frontend/backend state consistency:** the workbench stage is *derived* from the
server item status (never independently asserted by the frontend); approve is a
distinct server-gated transition. No frontend-only state transition was found.

## 5. Role Matrix

| Role | Navigation | Data visibility | Actions | Messaging | Documents | Notes |
|---|---|---|---|---|---|---|
| PUBLIC | Public pages | Public content | None | — | — | |
| CUSTOMER OWNER | Customer + organisation admin | Own org | Org mutations, approve/reject (D5) | Own org | Own org (signed) | |
| CUSTOMER ADMIN | Customer | Own org | Org mutations, approve/reject (D5) | Own org | Own org | |
| CUSTOMER MEMBER | Customer | Own org | Create issues/batches, review (read) | Own org | Own org | Approve denied (403 tested) |
| CUSTOMER VIEWER | Customer (read) | Own org | Read only | Own org | Own org (view) | |
| CONSULTANT | Consultant workspace | Active-client orgs only | Client work, messaging | Active clients | Clients (signed) | Server re-auth per request |
| PE USER | Entity workspace | Assigned work only | Extract/map/calculate on assigned items | DENIED (403 tested) | **View broken (raw path)**; no download control | |
| PE MANAGER | Entity workspace | Entity scope | Same as PE user | DENIED (documented data-model gap for PE-internal) | As above | |
| CARBONTALLY OPERATOR | Ops | Queues (can_process) | Extract/map/calculate | denied (no perms) | **View broken (raw path)** | |
| CARBONTALLY REVIEWER | Ops | Review queue | Validate/review | denied | signed via item_workspace (if used) | |
| CARBONTALLY QC | Ops | QC queue | QC actions | denied | signed | |
| STAFF ADMIN | Ops (admin tabs) | Ops-wide | Staff/entities/SLA/settings/audit/issues/messaging | staff-admin scoped (N1) | signed | |
| CARBONTALLY ADMIN | Ops/control plane | Ops-wide | Same as staff admin + billing | staff-admin scoped | signed | |

**One-account-one-role:** `get_current_user` resolves staff and org-membership
independently; a dual-seeded identity would carry both flags. No privilege
escalation path was found (each surface still enforces its own scope), but the
principle is not a hard invariant. Noted as P3.


## 6. D17 Verification (master data)

| Entity | Table | RLS (verified live) | API | UI | Status |
|---|---|---|---|---|---|
| Facilities | `facilities` | org-scoped (is_org_member/consultant SELECT) | `/api/v3/organizations/{id}/facilities` + CRUD | Facilities & Assets tab | PASS |
| Locations | **reuses `facilities`** (N2) | same | same | Locations tab | PASS |
| Assets | `assets` | org-scoped | `/api/v3/organizations/{id}/assets` + CRUD | Facilities & Assets tab | PASS |
| Vehicles | `vehicles` (migration `20260825000000_v3m7_vehicles.sql`) | **verified live**: RLS enabled, 4 policies (org member; select also consultant) | `/api/v3/vehicles` CRUD (reads member, writes admin) | Vehicles tab | PASS |
| Suppliers | `suppliers` | org-scoped | `/api/v3/suppliers` | Suppliers tab | PASS |

Vehicles migration: **VERIFIED** against local app DB (table=1, policies=4,
RLS=true). Production: **PRODUCTION NOT VERIFIED**.

## 7. D19 Verification (processing workbench)

| Required feature | State | Evidence |
|---|---|---|
| Top workflow navigation | **PRESENT** | `WorkflowNav`; stage derived from status; steps not clickable in current consumers (presentational) |
| Split-screen workbench | **PRESENT** | `SplitPane` flex panes |
| PDF/source viewer one side | **PRESENT (component) / BROKEN (operator & PE flows)** | `SecureDocumentViewer` iframe; operator queue + PE workspace feed it the raw `file_url` (bare path) |
| Structured data other side | **PRESENT** | Extraction form / data pane |
| Presets 40/60 · 50/50 · 60/40 | **PRESENT** | Code + tests |
| Adjustable panes | **PRESENT (pointer-only)** | Drag divider; no keyboard resize |
| Secure view-only source | **PARTIAL** | Sandboxed iframe + view-only; but operator/PE endpoints return raw `file_url` (P1) |
| Field confidence | **MISSING (unwired)** | `ConfidenceBadge` never used by a screen |
| Source ↔ field linking | **MISSING** | No mechanism |
| Inline validation | **MISSING** | Backend validation exists; no inline field-error UI |
| Autosave | **PRESENT** | `AutosaveIndicator` |
| Lock/approve states | **PARTIAL** | `locked` prop never passed by any consumer |
| Evidence traceability | **PRESENT** | Review + report detail; not inside extraction pane |
| Keyboard/accessibility | **PARTIAL** | Steps/presets buttons + focus-visible; divider pointer-only |
| Responsive tablet/mobile | **PRESENT** | Tray toggle ≤900px |

**Horizontal space:** full-width split panes with a top workflow bar; **no left
sidebar** inside the workbench. PASS on the layout model.

## 8. D21 Verification (design system)

| Aspect | State | Evidence |
|---|---|---|
| `ct-*` colour tokens | **PRESENT** | `tokens.css`; green unified `#2f855a`; accent `#2b6cb0` |
| Dual-green consolidation | **PASS** | `#2d6a4f` only in `App copy.css` (backup) + a comment; live App.css/v3.css on `#2f855a` |
| Component-rule token usage | **PARTIAL/FAIL** | Raw hex remains: v3.css 128, ops.css 50, admin.css 25, consultant.css 37, reports.css 57. Tokens not actually consumed by most rules |
| Stray legacy blues | **FAIL** | `ops.css` PE buttons still `#2563eb`/`#eff6ff` (legacy) instead of `#2b6cb0` |
| Status semantics | **PASS** | `statusConfig.js` label+icon+tone |
| Buttons/forms/tables | **PRESENT** | ui/ library + existing classes |
| Icons | **PASS** | single react-icons/feather set |
| Spacing/radii/shadows | **PRESENT** | tokens defined; partial usage |
| Responsive | **PASS** | breakpoints + tray |
| Accessibility | **PARTIAL** | focus-visible/aria/focus traps; workbench keyboard gaps |

## 9. N1 Messaging Verification

- **Authorization (API)**: `_authorize_org_actor` — org member (own org) OR
  active-grant consultant OR internal staff with `can_manage_staff`. PE and
  general staff denied (403). Unit tests cover allow/deny cases.
- **RLS (verified live)**: conversations/messages SELECT =
  `is_org_member OR is_org_consultant`; conversation_participants SELECT =
  `can_view_conversation_participants(...)`. RLS enabled on all three tables.
  No entity-staff storey.
- **UI**: customer `/messaging`, consultant client messaging, ops messaging
  (staff-admin). No Customer↔PE chat; clarification via issues.
- **Assistant inheritance**: N/A (no authenticated assistant).
- **Live E2E**: NOT VERIFIED (local gateway down).
- **Documented gap**: PE-internal messaging needs an entity-scoped conversation
  model (beyond the current org-scoped schema).

## 10. N3 Retention Verification

- **Config surface**: `/api/v3/settings/retention` (staff admin) + Ops Settings
  tab; unset = "Not configured"; **no invented durations** (tested).
- **Server-side enforcement**: `services/retention.py` +
  `tools/enforce_retention.py`; **dry-run by default**; `--apply` to execute.
  CLI verified live (dry-run, no configured duration).
- **Exclusions**: audit/evidence tables excluded (unit-tested).
- **Document expiration**: soft-expire via `deleted_at` (never hard delete).
- **Scheduler**: not configured — deployment work.
- **Note**: expiration is platform-wide (not per-org); per-org retention would
  be a product change beyond N3.


## 11. Security Verification (RLS / API / storage / PE boundary)

| Check | Result | Evidence |
|---|---|---|
| RLS deny-by-default on new tables | PASS | vehicles: 4 org-scoped policies, no bypass |
| customer_factors no-DELETE (app DB) | PASS | 3 policies (select/insert/update); NO delete (verified live) |
| Org isolation | PASS | `is_org_member(organization_id)` across tables; RLS integration suite passes |
| Search org scoping | PASS | every search query bound to `organization_id` |
| Audit access | PASS | `require_internal_staff` + `can_manage_staff` |
| Messaging authorization | PASS | API gate + RLS (see §9) |
| PE assignment scoping | PASS | `ensure_entity_batch_access` on every entity endpoint |
| Customer approval (D5) | PASS | `require_org_admin` on customer-review |
| Calculation authority | PASS | server engine; client never supplies result |
| Storage — signed URLs | **PARTIAL (P1)** | internal `item_workspace` + customer workspace sign; **operator/PE batch/item endpoints return raw `file_url`** |
| PE no-download boundary | **PARTIAL (P1)** | Structurally safe today (private bucket, bare paths, no download control, PE messaging denied) but NOT enforced at the API layer on the PE item endpoints |
| Document viewer sandbox | PASS | `sandbox="allow-same-origin"` iframes |

## 12. Calculation Integrity

- Server engine builds an immutable `CalculationSnapshot` (content_hash,
  `ON DELETE RESTRICT` factor FKs, exactly-one-source check).
- No client-supplied result: calculate payloads exclude `co2e_kg`; frontend
  reads the server-returned value only.
- Factor precedence: approved customer factor → CarbonTally factor (backend).
- **Residual note**: immutability enforced by convention/API (no UPDATE
  endpoint, RESTRICT FKs), not a DB-level UPDATE trigger. Low risk; P3.

## 13. Database / API / UX Reconciliation — mismatches

1. **Operator/PE workbench source viewer** (P1): UX promises "secure view-only
   source"; operator queue and PE workspace feed the viewer a raw storage path
   and the backing endpoints do not sign URLs. Backend can safely support it
   (the signed-URL convention exists); it is simply not applied there.
2. **D19 confidence / source↔field / inline validation** (P2): absent or unused
   in the workbench despite the spec; backend `ocr_suggestions` exist but
   confidence is not surfaced.
3. **D21 token usage** (P2): rules remain hex-based; stray `#2563eb`.
4. **Org Settings** (P3): covered by "Overview & Settings" but not labelled per
   inventory.
5. **Platform admin console** (P3): dense tabs serve the function; no single
   console.


## 14. Browser QA

Headless Chrome (`/opt/google/chrome`) against the production build served
locally. **Public pages only** — the local Supabase auth/storage gateway
(127.0.0.1:54325) is **not running**, so authenticated V3 pages could not be
rendered or interacted with.

| Width | Pages | Horizontal overflow |
|---|---|---|
| 1280 (desktop) | `/`, `/login`, `/about`, `/glossary`, `/pricing` | none |
| 768 (tablet) | same | none |
| 375 (mobile; Chrome min 500) | same | none |

Authenticated V3 surfaces and interactive D19 behaviour (presets, resizing,
tray) are covered by jsdom component tests and static CSS verification but
**NOT VERIFIED in a real browser** in this environment.

## 15. Test Results

| Suite | Command | Result |
|---|---|---|
| Frontend build | `npm run build` | PASS |
| Frontend V3 tests | `react-scripts test --testPathPattern='v3/__tests__'` | 109 passed (6 suites) |
| Backend unit | `pytest tests/unit` | PASS (exit 0, ~1108 tests) |
| RLS behavior integration | `pytest tests/integration/test_v3_rls_behavior.py` | PASS (27 tests) |
| Integration (factors/entities/issues/consultants) | `pytest tests/integration/...` | 5 **PRE-EXISTING** failures |

Integration failures classified:
- `test_factor_baseline_unchanged` — **environment**: test DB has only 2
  factors (no 7,049 seed); pre-existing.
- `test_consultants.py` (3) — **pre-existing code/test drift**:
  `add_client` signature changed; tests not updated.
- `test_customer_factors_rls_enabled_no_delete` — **environment (test-DB drift)**:
  the test DB has `customer_factors_tenant_delete`; the **app DB does NOT**
  (verified live). Test DB schema is stale.

`App.test.js` fails in jest (`react-router/dom` resolution) — **pre-existing**.

## 16. Remaining Gaps (genuine)

- **P1** — Sign document URLs on the operator/PE workbench endpoints and/or
  route those viewers through the signed workspace contract; fixes the broken
  source viewer and completes the D32 boundary.
- **P2** — Wire field confidence, source↔field linking, inline validation and
  lock states into the D19 data pane.
- **P2** — Complete D21 token migration; replace stray `#2563eb`.
- **P3** — Optional UPDATE guard on `calculation_snapshots`; one-account-one-role
  invariant; remove vestigial `compute_expired`; consolidated admin console.
- **BLOCKED_BY_PO_DECISION** — PE-internal messaging (entity-scoped
  conversations); authenticated AI assistant (provider/tool-call programme
  decision).
- **Deployment** — retention scheduler wiring; vehicles migration to
  production; integration-suite test-DB refresh.

## 17. Production Deployment Gaps

- **PRODUCTION NOT VERIFIED** for migrations, RLS, storage or any live
  behaviour. Only the local app DB (127.0.0.1:54326) and the dedicated test DB
  (54426) were inspected.
- Local Supabase gateway (54325) is down — live E2E of auth, storage, messaging
  and the workbench source viewer could not be exercised.

## 18. Regression Risks

- The `ExtractionPanel` D19 retrofit changed the operator/PE workbench layout;
  the source pane currently receives a raw path — **viewer regression** and P1
  if not completed.
- New ops tabs are `can_manage_staff`-gated — no regression observed.
- No test was weakened or deleted during the four-phase work; integration
  failures are pre-existing drift.

## 19. Recommended Fix Queue

**P0** — none identified.

**P1**
1. Apply `signed_item()` to the operator/PE item payloads (`ops_batch_items`,
   `entity_extraction_batch_items`, `entity_extraction_item_workspace`) or
   switch those consumers to the signed workspace contract; re-verify the PE
   no-download boundary end-to-end.

**P2**
2. Wire confidence badges (from workspace `ocr_suggestions`/D33) into the D19
   data pane.
3. Add source↔field linking and inline validation affordances to the workbench
   (backend already provides validation findings).
4. Wire the `locked` state from server status into the workbench shell.
5. Migrate remaining raw hex in `v3.css`/`ops.css`/`admin.css`/
   `consultant.css`/`reports.css` to `ct-*` tokens; replace `#2563eb`.

**P3**
6. Optional: UPDATE trigger on `calculation_snapshots`; one-account-one-role
   check; remove vestigial `compute_expired`; consolidated platform admin
   console; org Settings tab labelling.

*End of audit. Evidence gathered without code changes. No commit/push
performed.*

