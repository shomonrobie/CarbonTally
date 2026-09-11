# CarbonTally — Blueprint Implementation Gap Assessment

> **Type:** Controlled implementation-gap assessment against the authoritative
> `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.0.md` (read in full).
> **Date:** 2026-09-02
> **Git HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (branch `main`)
> **Mode:** Read-only assessment. No application/database/migration/RLS/configuration changes were
> made. Only this documentation artifact is created. Phase 1 implementation is NOT started.
> **Classification:** A = already compliant · B = partially compliant / migration required ·
> C = missing · D = conflicting legacy implementation · E = unclear / requires targeted
> investigation. Severity P0–P3 defined in §4.

---

# 1. Executive Summary

The blueprint ratifies the architecture documented across the preceding forensic, product and
decision-register assessments. **No technical contradiction was found** that would make any
explicit blueprint requirement impossible: the one-platform/one-domain/one-database model, the
V3 FastAPI backend, Supabase identity + RLS, the D21 UI foundation, and the verified PE backend
boundary all exist and match the blueprint. The blueprint's own "Current Known Implementation
Gates" (§30) are consistent with the gaps found by the independent product audit.

Headline position:

- **A (already compliant):** identity/auth, server-side authorization, RLS (org/consultant/
  entity), the PE backend boundary, customer/consultant/operations boundaries, document security
  (private storage + signed URLs), evidence/provenance, emission factors (7,049 intact), billing
  (provider-neutral), retention (configurable, destructive deferred), messaging (N1 boundaries),
  V3-canonical and D21 UI foundation.
- **B (partially compliant):** customer surface routing (`/app` prefix), document preview
  (render-scope defect), automatic AI extraction (not yet in the durable pipeline), calculation
  unit-normalisation + methodology (defects on some paths), white-label (foundation only —
  correctly not over-claimed), DataTable/UI convergence, responsive foundation.
- **C (missing):** the dedicated `/pe` application surface, the `/api/v3/pe/*` contract, the
  PE-side role vocabulary, and frontend readiness for independent PE deployment.

---

# 2. Current Repository Baseline

| Item | Value | Evidence |
|---|---|---|
| Branch / HEAD | `main` / `16391217103b98dcea520070c5a22c68f12fe607` | `git rev-parse HEAD` |
| Working tree | Pre-existing modifications only (`.agents/skills/*`, `.claude/skills/*`, etc.); **none made by this assessment** | `git status --short` |
| Migration files | 41 (`supabase/migrations/*.sql`) | `ls \| wc -l` |
| Applied migrations | 41; latest `20260831040000` (consultant revocation roles) | `supabase_migrations.schema_migrations` |
| Schema markers | `vehicles`, `system_settings`, `customer_factors`, `issues`, durable dpq columns present | information_schema / schema inspection |
| Factor count | **7,049 — INTACT** | `select count(*) from emission_factors` |
| Factor checksum | Reference MD5 `93668772…` **not reproducible** from current DB with common serialisations (newline-separated, concatenated, dashed/undashed, with/without psql headers). Count gate holds; checksum method UNVERIFIED (E) | md5sum probes |
| Backend | Running on `127.0.0.1:8050` (uvicorn `main:app`, 621 routes, health OK) | `curl /health` |
| Supabase | Local stack running (PostgREST/GoTrue/Storage/Realtime on `127.0.0.1:54425`; Postgres `54426`) | prior live probes |
| Backup | `/home/shomonrobie/carbontally_db_backups/carbontally_dev_20260901T125134.dump` exists (not touched) | filesystem |
| Demo identities | 1,183 demo users; all personas authenticate (fallback local password) | prior live probes |
| Blueprint | `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.0.md` read in full | status: PROPOSED — FREEZE CANDIDATE |

---

# 3. Blueprint Compliance Matrix

| # | Blueprint requirement (section) | Class | Evidence / gap |
|---|---|---|---|
| 1 | Public surface `/` | A | public routes exist |
| 2 | Customer surface `/app` | B | customer app under flat routes (`/home`, `/documents`, …); `/app` prefix not adopted (decision E) |
| 3 | Consultant surface `/consultant` | A | implemented + client grants |
| 4 | PE surface `/pe` + PEShell | C/D | only a stray `/pe/items/:entityId/:itemId` route under the shared shell; PE UI lives in `/ops` branch (D) |
| 5 | Operations surface `/ops` | A | canonical staff app (D-P2-02) |
| 6 | Admin surface `/admin` | D | legacy `admin/` CRA quarantined (not target); no V3 admin control plane; modern admin tabs inside `/ops` |
| 7 | Explicit per-surface route guards/shells | B | `RoleRoute` exists; per-surface shells not yet (PE/Admin) |
| 8 | One Supabase identity (no separate user DBs) | A | verified |
| 9 | Token audience/scope separation | E | blueprint §33 — optional future hardening, not a gate |
| 10 | Server-authoritative authorization | A | `require_*` + RLS + per-resource checks (STRONG) |
| 11 | Frontend never the security boundary | A | route guards UX-only; backend denies (verified) |
| 12 | RLS org/consultant/entity; FORCE RLS deferred | A | verified; blueprint §14 confirms deferral |
| 13 | Customer org isolation + roles | A | verified (owner/admin/member/viewer) |
| 14 | Consultant relationships + non-destructive revocation | A | WS6/SEC-0003 + lifecycle implemented |
| 15 | PE is not a customer; dedicated entity model | A | `processing_entities` + `entity_id` convention |
| 16 | PE backend boundary (RLS+API+auth) | A | verified sound — PRESERVE |
| 17 | PE cannot enumerate customers / cross-PE / escalate | A | live 403s |
| 18 | PE application surface + PEShell | C | missing (see #4) |
| 19 | PE API `/api/v3/pe/*` thin contract | C | missing; currently `/api/v3/ops/entities/*` |
| 20 | PE role vocabulary (Owner/Admin/Manager/Staff) | C | only `pe_manager` vs generic entity staff today |
| 21 | PE document security (no download; render) | A/B | private storage + signed URLs (A); render-scope defect (B, P0) |
| 22 | Document preview inline (no download control) | B | P0 render-scope fix required before PE acceptance |
| 23 | Durable processing pipeline canonical | A | implemented (V3M9) |
| 24 | AI extraction integrated into durable pipeline + deterministic fallback | B | AI engine exists but wired only to legacy workflow engine |
| 25 | Deterministic calculation authority | A | server-authoritative; snapshots immutable |
| 26 | Unit normalisation on all calculation paths | B | defect on ≥1 path (`m3` vs `cubic metres`); P0 |
| 27 | Methodology normalised server-side | B | client-supplied on manual/customer paths; P0 |
| 28 | Evidence/provenance chain | A | snapshots + `source_item_id` + audit immutability |
| 29 | Emission factors preserved (7,049) | A | count verified intact |
| 30 | Billing provider-neutral | A | D37 implemented |
| 31 | Retention configurable; destructive deferred | A | matches blueprint §22 |
| 32 | Messaging N1; PE↔customer prohibited; entity-scoped PE ops messaging "if implemented" | A | PE denied; entity-scoped threads = PO decision (not a gate) |
| 33 | White-label foundation; full rendering future | B (correct posture) | foundation implemented; not over-claimed |
| 34 | Independent PE deployment readiness | C | PE components embedded in `v3/ops` + `App.js` route table; needs isolation |
| 35 | D21 UI foundation; no shadcn | A/B | foundation exists (A); convergence incomplete (B) |
| 36 | Canonical DataTable (server paging/sort/filter/search/states/a11y) | B | DataTable canonical but fragmentation remains; server filter/search surface to verify |
| 37 | Responsive at 100% zoom (1920…390) | B | duplicate form-grid CSS + foundation fixes; P0 |
| 38 | Workbench desktop-first; top workflow nav; source left / workspace right; no left sidebar | A | D19 `WorkbenchShell` matches |
| 39 | Legacy transitional; removal dependency-gated | D (in progress per policy) | legacy routes + admin CRA remain; policy correct |
| 40 | PE QC ≠ customer approval | A | verified (D-P2-03) |

- **D (conflicting legacy):** PE UI currently lives inside `/ops`; Admin has no V3 control plane

**Count summary (40-item matrix):** A = 20 · B = 10 · C = 4 · D = 3 · E = 3.

---

# 4. P0 / P1 / P2 / P3 Findings

**P0 = security/data-integrity/blocking production issues** (matches blueprint §30 P0 gates):

| ID | Finding | Classification |
|---|---|---|
| P0-1 | Document preview render scope: signed URLs carry `scope=download` → browser downloads instead of rendering; `SecureDocumentViewer` iframe renders blank | B (blueprint §8/§30 P0.1–P0.2) |
| P0-2 | Calculation unit normalisation bypass on ≥1 path (`m3` vs `cubic metres`); blocked jobs evidence | B (blueprint §30 P0.3) |
| P0-3 | Methodology values not normalised server-side on manual/customer calculate paths (`customer_factor`, `keyword_search` reach enum validation) | B (blueprint §30 P0.4) |
| P0-4 | Responsive foundation: duplicate `.v3-form-grid` rules; missing `min-width:0`/`overflow-wrap` guards; raw tables unwrapped | B (blueprint §30 P0.5) |

**P1 = major functional/architectural gaps** (blueprint §30 P1 items 6–10):

| ID | Finding | Classification |
|---|---|---|
| P1-1 | AI/LLM extraction not integrated into the durable automatic pipeline (deterministic extraction only; completeness gate blocks most uploads) | B |
| P1-2 | Dedicated PE application (`/pe` + PEShell) missing; PE UI in `/ops` | C/D |
| P1-3 | Deliberate PE API contract `/api/v3/pe/*` missing (thin layer over shared domain) | C |
| P1-4 | DataTable/UI convergence incomplete (DataTable 13 · `v3-ops-table` 11 · raw tables 22) | B |
| P1-5 | Functional acceptance testing (blueprint §29) not yet run as a suite | B/E |

**P2 = important convergence/UX/maintainability** (blueprint §30 P2 items 11–15):

| ID | Finding | Classification |
|---|---|---|
| P2-1 | V3 Admin control plane (`/admin`) not implemented | D |
| P2-2 | Quarantined legacy `admin/` CRA removal (dependency-gated) | D |
| P2-3 | Legacy route removal (~405 endpoints; dependency-gated) | D |
| P2-4 | PE privacy/pseudonymization layer (server-side) — design only | C |
| P2-5 | Production security hardening (MFA posture, token scopes, FORCE RLS decision) | E |

**P3 = cleanup/future hardening:**

| ID | Finding | Classification |
|---|---|---|
| P3-1 | Dead endpoint families (`/api/v3/admin/review-queue` zero consumers; unused QC admin client helpers) | B |
| P3-2 | Component-primitive dead code (Tabs, CheckboxField, PermissionState, Card/StatCard 0 consumers; local StatCard/LoadingBlock duplicates) | B |
| P3-3 | Legacy unrouted `Dashboard` function + embedded upload path | D |
| P3-4 | `customer_documents` empty vs `organization_files`/dpq document-state duality | B |
| P3-5 | Factor-checksum method verification (count intact) | E |

---

# 5. Current → Target Architecture Mapping

| Current | Target (blueprint) | Path |
|---|---|---|
| Public `/` (A) | `/` | — |
| Customer flat routes `/home`, `/documents`, … (B) | Customer `/app` | mount current customer pages under a CustomerApp shell at `/app` (bridge `/home*` redirects) |
| Consultant `/consultant` (A) | `/consultant` | — |

---

# 6. Database Impact

- **No database migration is required** for any blueprint requirement classified A/B/C in this
  assessment. Application-surface separation, PE `/pe`, the `/api/v3/pe/*` contract, the Admin
  control plane and the frontend changes are all additive at the API/UI layer.
- Optional future additive candidates (all deferred, none required for this phase):
  - PE-side role vocabulary storage (e.g. `staff_profiles.entity_role` or a PE role table) — only
    if the PO approves the PE Owner/Admin/Manager/Staff vocabulary (blueprint §6.3).
  - Entity-scoped conversation scope for PE↔Operations messaging — only if the PO approves entity
    messaging (blueprint §23: "if implemented").
  - Document-state reconciliation (`customer_documents` vs `organization_files` vs dpq) — P3
    engineering decision, additive only.
- **Protect:** 7,049 factors (count verified), all migrations/RLS, customer/consultant/PE/
  audit/billing data. No destructive migration is recommended anywhere.
- **FORCE RLS:** remains deferred (blueprint §14). Not a prerequisite.

---

# 7. API Impact

- New **`/api/v3/pe/*` router** (P1-3): thin access-contract layer that delegates to the shared
  domain/service/engine layer and the existing entity-scoped authorization
  (`require_staff`-style entity guard → `require_entity_scope`). It must NOT duplicate business
  logic; it may reuse the same repository/engine calls as `/api/v3/ops/entities/*`.
- Classification of the 14 current `/api/v3/ops/entities/*` endpoints: dashboard/batches/items/
  workspace/start/extract/map/calculate/status/clarify → PE API (exposed through `/pe` contract);
  `GET /entities` (PE list/CRUD) → stays Operations-internal (CarbonTally controls PE management);
  shared domain services for extraction/mapping/calculation used by both; dead families
  (`/api/v3/admin/review-queue`) → retire later (P3-1).
- Add `GET /api/v3/pe/me` context endpoint (mirror of `/api/v3/ops/me`) so the PE shell never
  calls ops aggregates.
- API contract consistency (error envelope, `limit/offset/total`, auth semantics) is preserved;
  the legacy surface remains transitional (dependency-gated removal).

---

# 8. Frontend Impact

- **Customer `/app`:** create a `CustomerApp` shell and mount current customer pages under `/app`;
  keep `/home*` working via redirect bridge (or adopt `/app` as canonical and redirect old flat
  routes). Engineering decision on prefix adoption (§18).
- **PE `/pe`:** create `PEShell` + `RoleRoute requirePE`; move `EntityExtractionWorkspace`,
  `PEManagerDashboard`, `PEEntityItemPage` into `v3/pe/*` (git mv, preserve history); reuse
  `ExtractionPanel`/`WorkbenchShell`/`SecureDocumentViewer`; redirect `/ops` PE branch until
  verified.
- **Admin `/admin`:** (after PO ruling) build AdminApp shell over the V3 API + D21 primitives;
  migrate modern admin tabs (Commercial/QC/Issues/Audit/Settings/Staff/Roles/Entities/SLA).
- **Convergence:** DataTable standard (§12), StateViews, FormControls, `ui/Tabs` adoption; remove

---

# 9. PE Migration Plan (non-destructive, blueprint §27)

1. Build `/pe` surface (shell + routes + `requirePE` + `/api/v3/pe/me`) while the `/ops` PE
   branch remains fully functional.
2. Move PE components to `v3/pe/*`; keep shared workbench/extraction/viewer imports.
3. Add `/ops`→`/pe` redirect for entity staff (bridge).
4. Run blueprint §29 acceptance tests (PE block) against `/pe`.
5. After green acceptance for a defined period, remove the `/ops` PE branch and the bridge.
6. Never delete users, entities, assignments, work items, documents, extraction data, QC, audit
   history, provenance or factors.

---

# 10. Admin Migration Plan

1. Await the PO ruling on the Admin surface scope (§18) — the blueprint decides `/admin` is the
   target control plane; implementation of the surface layout/authority granularity is the
   decision item.
2. Build the V3 AdminApp (dedicated shell over the V3 API; `require_admin`; D21 primitives).
3. Migrate the modern admin tabs out of `/ops` into `/admin` (Ops retains operational workflows;
   Admin retains privileged governance — separation of duties).
4. Retire the quarantined legacy `admin/` CRA only after dependency inventory (blueprint §26).
5. All privileged operations must go through the secured API/service layer — never direct Supabase.

---

# 11. Processing / AI Integration Plan

1. Keep the durable pipeline canonical (V3M9) — complete it, don't replace it.
2. Wire `AIExtractionEngine` (LLM-assisted extraction/classification/suggestion) into the durable
   extract stage **with a deterministic fallback** and the existing completeness gate; AI output
   must never be authoritative without validation (blueprint §10/§28-26).
3. Keep deterministic calculation authority, evidence/provenance, retry/audit durability.
4. Regression-verify: one representative upload reaches `customer_review` with an immutable
   snapshot + emissions row.

| PE inside `/ops` + stray `/pe/items/:entityId/:itemId` (D) | PE `/pe` | build `/pe` shell; move PE components non-destructively; redirect bridge; then remove old branch |
| Ops `/ops` (A) | `/ops` | remove PE branch after bridge verified |
| Admin: legacy CRA quarantined + admin tabs in `/ops` (D) | `/admin` | build V3 AdminApp on V3 API (PO ruling pending on surface scope); retire legacy CRA |
| `/api/v3/ops/entities/*` (A, entity-scoped) | `/api/v3/pe/*` thin contract | add PE router delegating to shared domain; classify endpoints (PE / ops / shared / retire) |
| Durable pipeline (A) | + AI extraction in pipeline | wire AIExtractionEngine into durable extract stage with deterministic fallback |
| V3 API (A) | shared across surfaces | unchanged |
| D21 (A) | converged | incremental component/table convergence |
| Single DB + RLS + Auth (A) | unchanged | no database migration required for surface separation |

  (legacy `admin/` CRA is quarantined and must not be revived; modern admin tabs sit inside
  `/ops`); ~405 legacy endpoints remain mounted (removal dependency-gated per blueprint §26).
- **E (requires decision/investigation):** the `/app` customer prefix adoption, the PE-role
  storage mapping, the optional token audience/scope hardening (blueprint §33 — not a gate), and
  the factor-ID checksum method (count verified; reference MD5 not reproducible with documented
  serialisations).

**Nothing in this assessment alters the blueprint; nothing is redesigned.** The recommended
implementation sequence (§16) is additive, non-destructive and migration-bridged, matching the
blueprint's migration safety requirements (§27).

# 12. UI / D21 Convergence Plan

1. Adopt shared primitives as canonical: `ui/Button`, `ui/FormControls`, `ui/StateViews`,
   `ui/Dialog`/`ConfirmationDialog`, `ui/StatusBadge`, `ui/Icon`, `ui/DataTable`, and adopt
   `ui/Tabs` + `ui/Card`/`StatCard` (currently 0 consumers).
2. Remove local duplicates (`DashboardPage` `StatCard`, `ConsultantPage`
   `LoadingBlock`/`ErrorBlock`) incrementally.
3. Retire `v3-btn`-class-only controls where `ui/Button` suffices (keep for DataTable pagination
   styling if needed).
4. Standardize page headers, navigation shells, form layouts, and status presentation per
   surface.
5. No shadcn/ui; no per-application component systems (blueprint §17).

---

# 13. Document Security / Preview Plan

1. **P0-1:** change `services/storage.py:storage_signed_url` to issue a **render-scope** signed
   URL (no `scope=download`); align `SecureDocumentViewer` sandbox or render via `react-pdf`
   (already a dependency); preserve the PE no-download policy (no download control rendered).
2. Distinguish original customer document vs PE-visible processing document; PE receives only the
   signed render of assigned work; no unrestricted original-document URLs.
3. Keep private bucket + short TTL + authorize-before-issue unchanged.
4. Backlog: future sanitized/redacted derivatives and pseudonymized PE-visible metadata (blueprint
   §7 — server-side; not in this phase).

---

# 14. Legacy Quarantine Plan

1. Legacy routes (~405 endpoints) and the legacy `admin/` CRA remain **transitional only**;
   no new features built on them (blueprint §26).
2. Dependency inventory gates removal; replacement functionality must pass acceptance before
   deletion; removal is non-destructive.
3. Legacy public/unauthenticated document/upload surfaces must not remain for real personal data.
4. The legacy `admin/` CRA is quarantined and never revived as the target Admin.


---

# 15. Test and Acceptance Strategy

Per implementation phase (when approved), the suite must include:

- **Unit tests:** engines (calculation/unit normalization, methodology), storage signed-URL scope,
  extraction fallback logic.
- **API tests:** PE router contract, ops router (unchanged), customer/consultant regression.
- **Authorization tests:** allow/deny matrix (PE→customer, PE→other PE, PE→admin/staff,
  customer→customer, consultant→unauthorized client, staff→org) — both ALLOW and DENY.
- **Database/RLS tests:** entity isolation row-denial checks; factor count = 7,049; no migration
  drift.
- **Integration tests:** durable pipeline end-to-end (enqueue→…→snapshot→review state) with AI
  extraction fallback.
- **Browser/UX tests:** blueprint §29 acceptance (per surface) at 1920/1440/1280/1024/768/390,
  100% zoom; document viewer inline render; PE no-download.
- **Data-integrity checks:** 7,049 factors; existing organizations/consultant relationships/PE
  relationships/audit history intact before and after each phase.
- **Security gates:** no unauthorized PE access; PE cannot reach customer users; customer cannot
  communicate with PE; privileged admin actions never bypass authorization; frontend-only
  authorization never trusted.

---

# 16. Recommended Implementation Phases

**Phase 1 (P0 cluster — pre-requisites):** P0-1 document preview render scope +
SecureDocumentViewer · P0-2 unit normalisation at engine boundary · P0-3 methodology derived
server-side · P0-4 responsive foundation. Each with unit/API/browser tests.

**Phase 2 (P1-1 — durable AI extraction):** integrate AI extraction into the durable extract
stage with deterministic fallback; verify end-to-end; keep calculation authority.

**Phase 3 (P1-2/P1-3 — PE surface + PE API):** `/pe` + PEShell + `requirePE` + `/api/v3/pe/*`
thin contract + `/api/v3/pe/me`; non-destructive migration with bridge; PE acceptance tests.

**Phase 4 (P2-1/P2-2 — Admin control plane):** after PO ruling; build V3 AdminApp; migrate admin
tabs; retire legacy admin CRA (dependency-gated).

**Phase 5 (P1-4/P1-5 — convergence + acceptance):** DataTable standard; D21 component
convergence; full blueprint §29 acceptance suite; customer `/app` adoption (if approved).

**Phase 6 (P2-3/P2-4 + P3):** legacy route removal (dependency-gated); PE privacy layer (future);
dead code/family cleanup; document-state reconciliation.

No database reset; no rewrite-from-scratch; no destructive operations at any point.

  local duplicates incrementally.
- **Responsive foundation:** reconcile `.v3-form-grid`; add `min-width:0` + `overflow-wrap` to
  shared layout primitives; table scroll wrappers (P0-4).

---

# 17. Risks and Dependencies

| Risk | Mitigation |
|---|---|
| Factor data drift during phases | Non-destructive work only; count check (7,049) before/after every phase; backup untouched |
| PE migration breaks entity users | Bridge + retain old branch until acceptance green (blueprint §27) |
| Duplicate logic across API contracts | `/api/v3/pe/*` delegates to shared domain; no second implementation |
| Admin ambiguity blocks P2 | Phase 4 waits on the PO ruling; structural separation is prepared regardless |
| Document preview regression | P0-1 with browser test before any PE milestone |
| AI extraction cost/authority drift | Deterministic fallback + validation gate; AI never authoritative |
| Layout regressions | Shared responsive foundation + acceptance widths |
| Legacy removal risk | Dependency-gated; acceptance before deletion |

**Dependencies:** Phase 1 → none. Phase 2 → Phase 1 (calculation authority intact). Phase 3 →
Phase 1 (document viewer must render before PE acceptance). Phase 4 → PO ruling (Admin). Phase 5 →
Phase 3 (surface stability). Phase 6 → dependency inventories.

---

# 18. Items Requiring Explicit Product Owner Decision

The blueprint has already decided the architecture. The following are **decision items the
blueprint leaves open or that require product-level approval** — none are invented here:

1. **Customer surface prefix** — adopt `/app` as the canonical customer prefix (with redirects
   from `/home*`) or keep current flat customer routes (blueprint lists `/app`; E classification).
2. **Admin surface scope** — approve the V3 AdminApp build and the boundary between `/admin`
   (privileged governance) and `/ops` (operations) page sets (blueprint §5.5/§16; decision
   register §39 #1).
3. **PE-side role storage mapping** — approve the PE Owner/Admin/Manager/Staff vocabulary and how
   it is stored/resolved (blueprint §6.3; decision register §39 #3).
4. **Entity-scoped PE ↔ Operations messaging** — approve implementation (blueprint §23 "if
   implemented"; decision register §39 #2). Until approved: PE messaging remains denied (N1).
5. **AI extraction provider/cost model** — confirm provider and cost posture before wiring into
   the durable pipeline (blueprint §33 leaves the exact provider/cost open; decision register
   §39 #5).
6. **Factor-checksum method** — confirm the reference command for the factor-ID MD5 so the checksum
   gate can be automated (count already verified).
7. **Optional hardening items (not gates):** token audience/scope separation, MFA enforcement
   posture, FORCE RLS enablement (blueprint §33/§14).

**Explicitly NOT new product decisions:** everything the blueprint already settles (application
surfaces, PE-as-third-party, `/admin` target, `/pe` target, D21, non-destructive migration,
security invariants). These are treated as decided.

---
