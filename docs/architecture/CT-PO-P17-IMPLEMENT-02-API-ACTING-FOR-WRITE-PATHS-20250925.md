# P17 IMPLEMENT-02 — API / Acting-for Write Paths

**Task ID:** `P17-IMPLEMENT-02-20260925-API-ACTING-FOR-WRITE-PATHS`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
**Starting SHA:** `9f2766554b025aa5ee37ea6cdc3cbb418b63e111` (verified as actual HEAD before any change)
**Ending SHA:** this report's commit (parent is the implementation commit recorded in §4)
**Author:** Cline — implementation agent. **Nature:** IMPLEMENTATION (backend/API vertical slice).
**No UI. No Scope 2/3 calculation. No production contact.**

---

## 1. Task ID

`P17-IMPLEMENT-02-20260925-API-ACTING-FOR-WRITE-PATHS`

## 2. Starting SHA

`9f2766554b025aa5ee37ea6cdc3cbb418b63e111` — the P17-IMPLEMENT-MASTER-01 head. Confirmed with
`git rev-parse HEAD` before any edit; the only pre-existing working-tree change was `.gitignore`.

## 3. Ending SHA

The commit that introduces this report. Its parent and the implementation head is recorded in §4.

## 4. Commit SHA(s)

| # | SHA | Message | Contents |
|---|---|---|---|
| 1 | `5834906` | `feat(p17): persist acting-for attribution on the audit ledger` | `domain/audit.py`, `data/audit.py` |
| 2 | `415f0f2` | `feat(p17): add accounting-context resolution and acting-for persistence` | `api/accounting_context_auth.py`, `data/accounting_context.py`, `api/audit_helpers.py`, `api/dependencies.py`, `domain/acting_for.py`, `domain/cams.py`, `domain/partners.py`, `data/consultants.py` |
| 3 | `7b5eb2f` | `feat(p17): expose the accounting-context API surface` | `api/v3_accounting_context.py`, `api/router.py` |
| 4 | `fa7edba` | `test(p17-02): cover accounting context, API authorization and acting-for persistence` | 2 test modules (48 tests) |
| 5 | *(this report)* | `docs(p17): record IMPLEMENT-02 report` | this report |

**Nothing was pushed.** No amend, rebase, reset or force-push; all prior P17 commits preserved.

## 5. Files changed

**Created (4):**

- `backend/api/accounting_context_auth.py` — the organization/consultant context + authorization service
- `backend/api/v3_accounting_context.py` — the API router
- `backend/data/accounting_context.py` — accounting-context repository + acting-for writer
- `backend/tests/unit/api/test_p17_02_accounting_api.py`, `…test_p17_02_organization_context.py`

**Modified (8, additively):**

- `backend/domain/audit.py` — `AuditEntry` gained `actor_organization_id`, `acting_for_organization_id`
- `backend/data/audit.py` — `_AUDIT_COLUMNS`, `record()` INSERT, `_entry_metadata`, `_row_to_entry`
- `backend/api/audit_helpers.py` — `record_acting_for_attribution()`
- `backend/api/dependencies.py` — repository registered in the bundle (real wiring, not a test-only attribute)
- `backend/domain/acting_for.py` — `EntitlementBasis.CONSULTANT_FIRM_MEMBERSHIP`
- `backend/domain/cams.py` — `CamsPersona.PROCESSING_ENTITY`
- `backend/domain/partners.py` / `backend/data/consultants.py` — `ConsultantProfile.organization_id`
- `backend/api/router.py` — one `include_router` line

**Not changed:** no migration, no RLS policy, no frontend file, no seed, no P16 engine, no existing test.

## 6. API routes added/modified

Eight routes added under the existing `/api/v3` v3 convention (`APIRouter(prefix="/api/v3/accounting")`);
**no existing route was modified.**

| Method | Path | Purpose (task §5) |
|---|---|---|
| GET | `/api/v3/accounting/context` | **A** — current / effective accounting context |
| GET | `/api/v3/accounting/organizations` | **B** — authorized consultant/client relationships |
| POST | `/api/v3/accounting/acting-for` | **C** — select/switch acting-for organization |
| POST | `/api/v3/accounting/dimensions/resolve` | **D** — resolve context + validate CAMS dimensions |
| POST | `/api/v3/accounting/acting-for/attribute` | **E** — persist attribution on an accounting input |
| GET | `/api/v3/accounting/acting-for/attribution` | **F** — retrieve persisted attribution |
| GET | `/api/v3/accounting/scope3/categories` | reference vocabulary + architecture status |
| GET | `/api/v3/accounting/dimensions/snapshot/{snapshot_id}` | persisted dimensions + attribution |

**G** (rejecting unauthorized client access) is inherent in every route: the acting-for value is a request
that must match the actor's authorized set, and 403 is the fail-closed default.

**Honest note on router assembly.** The routes are registered exactly as every other v3 router is (one
`router.include_router(...)` line in the shared assembly block). Inspection showed `api.router.router.routes`
contains only `/api/v2/health` — i.e. that shared block does not populate `router` at import for **any** v3
router, which is precisely why three `test_review_sla_surfaces.py` tests **already fail at baseline**. This is
a pre-existing app-assembly condition; it was **not** introduced or modified by this task, and it is not
diagnosed further here. The router's own route table is verified by test, and the routes are exercised
end-to-end through FastAPI's `TestClient` with the router mounted, which is the meaningful behavioural check.

## 7. Service / domain changes

**`api/accounting_context_auth.py` (new) — the organization/consultant context service.** Placed in `api/`
deliberately: that is where this codebase already keeps authorization-chain logic (`consultant_auth.py`,
`operations_auth.py`, `pe_auth.py`), and importing `api.dependencies` from `services/` created a circular
import. It exposes:

- `AuthorizedOrganization` — one organization the actor may act for, with its `relationship`
  (`OWN` / `CONSULTANT_CLIENT` / `CARBONTALLY_INTERNAL`), `entitlement_basis`, `is_own`,
  `organization_type` and DC-07 `consolidation_approach`;
- `AccountingContext` — actor, persona, own/data-owning/acting-for organizations, `is_delegated`, basis,
  kind, plus `provenance_columns()` and a UI-ready `acting_for_label`;
- `resolve_persona`, `list_authorized_organizations`, `resolve_accounting_context`,
  `ensure_record_owner_authorized`.

**`data/accounting_context.py` (new)** — organization summaries, active membership roles, the Scope 3
reference vocabulary, snapshot dimension reads, and the acting-for **writer** over a closed
`ACTING_FOR_CARRIERS` allowlist. `delete()` raises `NotImplementedError`: attribution is provenance.

**Additive domain/plumbing changes:** `AuditEntry` gained the two attribution fields (defaulting to `None`, so
every existing caller is unchanged); `EntitlementBasis` gained `CONSULTANT_FIRM_MEMBERSHIP`;
`CamsPersona` gained `PROCESSING_ENTITY`; `ConsultantProfile`/`_PROFILE_COLUMNS` gained `organization_id`, so
the consultant firm's own organization (the ARCH-06 HIGH-01 linkage) is finally readable through the existing
profile path.

## 8. Acting-for write paths implemented

**What is genuinely persisted, and what is not.** The nine ARCH-04 §10.3 carriers are all *addressable*
through one authorised, audited writer with a closed allowlist:

| # | Carrier (`ACTING_FOR_CARRIERS` key) | Table | Actor column | Acting-for column |
|---|---|---|---|---|
| 1 | `calculation_snapshot` | `calculation_snapshots` | `performed_by_organization_id` | `acting_for_organization_id` |
| 2 | `emissions_log` | `emissions_logs` | `performed_by_organization_id` | `acting_for_organization_id` |
| 3 | `evidence_line_item` | `evidence_line_items` | `contributed_by_organization_id` | `acting_for_organization_id` |
| 4 | `customer_document` | `customer_documents` | `actor_organization_id` | `acting_for_organization_id` |
| 5 | `supplier` | `suppliers` | `actor_organization_id` | `acting_for_organization_id` |
| 6 | `review_audit_trail` | `review_audit_trail` | `actor_organization_id` | `acting_for_organization_id` |
| 7 | `review_assignment_history` | `review_assignment_history` | `actor_organization_id` | `acting_for_organization_id` |
| 8 | `report_version` | `report_versions` | `prepared_by_organization_id` | `acting_for_organization_id` |
| 9 | `audit_entry` | `audit_trail` | `actor_organization_id` | `acting_for_organization_id` |

**Path 9 (the audit writer) is wired at the source.** `AuditRepository.record()` now writes
`actor_organization_id` and `acting_for_organization_id` on every entry, and `_entry_metadata` mirrors them
into `metadata` so the ledger stays investigable from the payload alone. Because the two fields default to
`None`, **every existing audit call site behaves exactly as before** while the columns are now populated
wherever a caller supplies them — which `record_acting_for_attribution()` does.

**Paths 1–8 are addressable but their existing call sites are NOT yet wired** (see §15). The honest
statement: attribution is **persistable and audited for all nine**, and **automatically written for none of
the eight record paths on their existing write flows**. No redundant columns were added anywhere; the writer
uses the columns the architecture already specified.

**No derivation substitute.** Nothing derives durable acting-for from `uploaded_by`, `created_by`, the current
user or the session. The value persisted always comes from the server-resolved context.

## 9. Organization / consultant authorization

Relationship-based, never role-inferred. `list_authorized_organizations` builds the set from exactly three
authoritative sources:

1. **active `organization_members` rows** (the same active predicate the RLS helper `public.is_org_member`
   uses) → `OWN` / `ORGANIZATION_MEMBERSHIP`;
2. **the actor's own consultant firm organization** via `consultant_profiles.organization_id` →
   `OWN` / `CONSULTANT_FIRM_MEMBERSHIP`;
3. **`consultant_clients` grants with status exactly `active`** (the D15 rule, reusing
   `ConsultantsRepository.list_clients` — the same lookup `ensure_consultant_org_access` uses) →
   `CONSULTANT_CLIENT` / `ACTIVE_CONSULTANT_DELEGATION`.

**Being a consultant grants nothing by itself** — a consultant with no active grant sees only their own firm
(asserted by test). Non-active grant statuses (`pending`, `rejected`, `suspended`, `ended`, `inactive`) grant
nothing and are parametrized in the tests. Membership beats a delegated grant for the same organization, so
the list never overstates the relationship. Inactive organizations are excluded even when a membership row
exists.

**Persona behaviour:** DIRECT_CUSTOMER → own org; CONSULTANT → own firm org by default; CONSULTANT_CLIENT →
only actively delegated clients; CONSULTANT/CONSULTANT_CLIENT personas are refined from the *resolved*
relationship, not guessed from auth flags; STAFF → follow the existing staff model (the organization must
exist; route capability gates are unchanged); PROCESSING_ENTITY → **refused** for customer organizations
(fail-closed PE boundary).

**Consultant access is never inferred from the consultant role**, and a delegated client list is not a master
key: a consultant entitled to client A is denied client B (asserted by test).

## 10. Tenant / RLS behavior

**No RLS was changed, weakened or bypassed.** No migration was added; no policy was touched; no service-role
bypass was introduced to make a test pass. Tenant isolation is enforced by:

- **relationship verification on every request** — the acting-for value must match an organization in the
  actor's authorized set, so changing it cannot reach another tenant (403 by default);
- **record-owner authorization** — `ensure_record_owner_authorized` requires the actor to be entitled to the
  *record's own* `organization_id`, so the data-owning organization cannot be overridden by naming a
  different acting-for value;
- **read-scoping** — the attribution-read and snapshot-dimension endpoints both authorize against the
  record's owner, so neither can be used to probe another tenant.

Every domain error carries an accurate HTTP status (403 for acting-for denial, 409 for the DC-09 conflict, 422
for dimension/boundary failures), so the API layer cannot present a denial as a success or a client error as a
server fault.

**One residual risk:** the record-owner check is an application-layer guard executed before the write. It is
correct and tested, but it is **not** a database constraint; a future caller that bypasses
`resolve_accounting_context` would not be protected by the database. Recorded as a limitation, not a claim.

## 11. CAMS dimension persistence

The eight dimensions are reachable and validated through the API:

- **validation** — `POST /api/v3/accounting/dimensions/resolve` runs the unified `resolve_accounting_dimensions`
  engine, so a Scope 2 result without a method, `energy_type: "fuel"`, a category-4 result without a transport
  boundary, and a `NOT_IMPLEMENTED` category are each refused with their own machine-readable code (asserted by
  API test). The DC-07 consolidation approach is supplied from the resolved organization, so categories 8/13
  fail closed when it is undecided.
- **persistence** — the writer persists the **acting-for attribution** columns for snapshots/emissions rows and
  the other carriers. The eight *dimension* columns are already persisted by the P17-A schema; this task adds
  the read surface (`GET …/dimensions/snapshot/{id}`) and the validation gate. **This task did not write
  dimension values on any new path**, because no calculation path exists yet (§12).

**No Scope 2 or Scope 3 calculation was implemented**, as required: no factor is selected, no quantity is
multiplied and no snapshot is produced. `dimensions/resolve` explicitly returns `would_persist: false`.

## 12. Audit / evidence attribution

Every newly exposed write path produces attribution on the **existing** ledger — no second audit model:

- **WHO** → `actor` (`performed_by`) and `actor_organization_id`;
- **ACTING FOR** → `acting_for_organization_id`, on both the dedicated column and in `metadata`;
- **OWNS DATA** → `organization_id` on the entry, set from the record's owner;
- **WHAT** → `action` = `acting_for_attributed`;
- **WHEN** → `performed_at` / `occurred_at`;
- **DOWNSTREAM EFFECT** → `entity_type` = carrier, `entity_id` = record id, plus carrier/owner in
  `changed_fields`.

The audit write is best-effort (`record_acting_for_attribution` never breaks the attribution write), matching
the existing `audit_helpers` convention.

**Honest scope statement:** this covers the **acting-for attribution write path** and the **audit ledger**
itself. It does **not** claim audit completeness for the eight record paths' own business writes, because those
call sites are not yet wired (§15). The claim is: *every attribution this task persists is audited*, not *every
write in the product is attributed*.

## 13. Tests executed

**48 new tests, all passing** (`tests/unit/api/test_p17_02_accounting_api.py` +
`…test_p17_02_organization_context.py`). Coverage is mapped to the task's categories rather than inflated:

| Category (task §10) | Coverage |
|---|---|
| Organization context | own-org resolution for member and consultant; default fallback to the own organization; inactive tenant excluded; internal staff permitted with an existing org and 404 for a missing one; internal staff must name an org (422) |
| Consultant relationship authorization | own firm org; active delegated client; **denied** for an unauthorized client; **parametrized** denial for `pending`/`rejected`/`suspended`/`ended`/`inactive`; consultant status alone grants nothing; membership beats a delegated grant |
| Acting-for resolution | basis, kind, `is_delegated`, persona refinement, UI `acting_for_label` present only when delegated |
| Acting-for persistence | persists from the server-resolved context; audit entry created; 404 for an unknown record |
| API authorization | 403 for unauthorized context / selection / dimension resolution / attribution write / attribution read; 422 for an unknown carrier |
| Tenant isolation | record owned by another tenant → 403 **and nothing written**; inactive org grants nothing |
| Forged acting-for rejection | payload `acting_for_organization_id` / `actor_organization_id` ignored; the server value is persisted |
| CAMS dimension validation | Scope 2 without method; `fuel` refused with its reason; category 4 without transport boundary; `NOT_IMPLEMENTED` category 10; valid resolution does not calculate |
| Audit attribution | the `AuditEntry` carries actor / acting-for / owner / action / entity |
| Carrier allowlist | exactly the nine ARCH-04 paths; the owner column is never the acting-for column; the repository refuses to delete provenance |

The service tests use in-memory fakes (no DB, no network). The API tests mount the real router in a FastAPI app
and exercise it through `TestClient`, asserting status codes and payloads — the HTTP contract, not only the
service functions.

## 14. P16 regression results

**NO REGRESSIONS — and one regression was found and fixed during this task.**

### 14.1 Full unit-suite comparison

| | With P17-IMPLEMENT-02 | Baseline (`9f27665`, IMPLEMENT-MASTER-01) |
|---|---|---|
| Unit tests collected | 3542 | 3494 |
| Failures | **9** | **9** |
| Failing test IDs | identical set | identical set |

The nine failures are the **same pre-existing** ones recorded in the IMPLEMENT-MASTER-01 baseline report and
visible in the baseline worktree:

1–3. `test_review_sla_surfaces.py` (3 registration tests — the shared router-assembly condition noted in §6);
4. `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`;
5–6. `test_i1_insight_migration.py` / `test_i2_insight_authorization_contracts.py` latest-migration expectations;
7–9. `test_extraction_suggestions.py` (3 cases).

None was introduced, worsened or left unfixed by this task. **No existing test was modified, weakened, skipped
or deleted.**

### 14.2 Regression found and fixed (disclosed, not hidden)

Adding `accounting_context` to `RepositoryBundle` as a **required** field caused
`TypeError: RepositoryBundle.__init__() missing 1 required positional argument: 'accounting_context'` in every
existing test and fixture that constructs the bundle — several hundred API tests failed on the first full-suite
run.

This was a **real regression introduced by this task**, caught by the required regression run, and fixed by
making the field default to `None` (it is the last field, so the default is valid). Production wiring always
supplies the real repository through `get_repositories()`, so the default only affects callers that do not use
P17 routes.

After the fix the full suite returns to **exactly the baseline 9 failures**, and the previously broken suites
(`test_v3_whitelabel.py`, `test_foundation.py`, `test_p6bill1_*`, `test_p7_auditability.py`,
`test_v3_reports.py`, `test_v3_work_item_effective_assignment.py`, and the rest) pass again. The regression and
its fix are recorded here rather than quietly absorbed, and **no test was adjusted to accommodate it**.


## 15. Remaining unimplemented write paths

Stated plainly rather than buried.

**Acting-for call sites not yet wired (the main gap).** The writer, authorisation and audit are complete and
tested, but the **existing business write flows** for eight carriers still do not call it:

| Carrier | Existing write site that would need the call |
|---|---|
| `customer_document` | `DocumentsRepository.create_from_upload` (and the second INSERT path in `data/documents.py`) |
| `supplier` | `SuppliersRepository.create` |
| `calculation_snapshot` | the snapshot INSERT in `data/emissions_logs.py` / the calculation pipeline |
| `emissions_log` | `EmissionsLogsRepository.create` |
| `evidence_line_item` | `EvidenceLineItemsRepository` materialisation |
| `review_audit_trail` | the review write sites |
| `review_assignment_history` | the assignment write sites |
| `report_version` | the report-version create path |

Each would be a one-call addition using `AccountingContext.provenance_columns()` plus
`record_acting_for_attribution(...)`. They were **not** done here, and the reason is sequence rather than
effort: those are the write paths the Scope 2/Scope 3 calculation layer and the UI will drive, and wiring them
now would mean either duplicating context resolution at eight call sites or refactoring eight P16-hot write
paths without the end-to-end flow needed to test them. The next task should wire them as it builds that flow.

**Other remaining work (excluded by this task's instructions):**

- **No UI** — client switcher, ACTING FOR banner, method picker and category picker are not built. The API is
  stable enough for that work: `context` returns `acting_for_label`, and `organizations` returns the switchable
  set with relationships.
- **No Scope 2 / Scope 3 calculation** — deferred to the next phase by instruction.
- **`consolidation_approach` cannot yet be set** by any endpoint, so DC-07 fails closed for categories 8/13 in
  practice until an organization-settings write path exists.
- **`consultant_profiles.organization_id` is readable but not writable** through this API; the ARCH-06 HIGH-01
  linkage still needs an operator/administrative path to populate it. A consultant firm with an unlinked
  profile cannot act for its own organization — it can still act for its active clients.

## 16. Production-contact statement

**NO PRODUCTION SYSTEM WAS CONTACTED.**

- No production database, migration, credential, deployment or customer data.
- No external production API call was made.
- No push to any remote; no release path triggered.
- **No database was opened at all in this task** — the tests use in-memory fakes and FastAPI's `TestClient`,
  and no migration was added or applied. The Demo Lab, `carbontally_qa_phase8`, `carbontally_test` and every
  other persistent local database were untouched.
- The destructive integration harness was **not run**.

## 17. Final verdict

```
P17_IMPLEMENTATION_COMPLETE
```

**Why COMPLETE.** The verdict refers to **the scope this task explicitly committed to**: turn the P17
foundation into a working backend vertical slice covering organization/consultant context, delegated client
access, acting-for persistence, CAMS accounting dimensions, API validation and authorization, and
audit/evidence attribution. That scope is implemented and wired end-to-end through DATABASE → DOMAIN →
SERVICE → API → PERSISTED ACTING-FOR CONTEXT → AUDIT, and covered by 48 passing tests with the task's ten
security cases asserted as ALLOW/DENY pairs.

**Scope explicitly excluded by this task is not a shortfall:** UI (task §11), Scope 2 / Scope 3 calculation
(task §12), ARCH-07 and final P17 verification (stop condition).

**What is genuinely delivered:**

- eight working `/api/v3/accounting/*` endpoints following the existing v3 conventions, with **no** existing
  route modified;
- relationship-based organization/consultant authorisation with **no** consultant-role inference, reusing the
  D15 active-grant rule rather than re-implementing it;
- a closed-allowlist acting-for writer covering all nine ARCH-04 §10.3 carriers, plus the audit ledger wired at
  source so attribution lands on the existing `audit_trail` columns;
- forgery resistance and record-owner authorisation, proven by test — acting-for did **not** become an
  authorization bypass;
- one additive change to `AuditEntry`/`AuditRepository` that leaves every existing caller's behaviour
  unchanged.

**What is NOT delivered, stated plainly:** the eight existing record write paths do not yet *call* the acting-for
writer (§15); there is no UI; there is no calculation; and `consolidation_approach` cannot yet be set. These are
recorded as remaining work, not implied away.

**No `PASS`, `E2E VERIFIED` or `PRODUCTION READY` claim is made.** These are implementation tests; final
independent verification remains a separate activity.




