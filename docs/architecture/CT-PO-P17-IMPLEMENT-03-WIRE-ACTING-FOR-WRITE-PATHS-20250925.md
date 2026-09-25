# P17 IMPLEMENT-03 — Wire Acting-for Write Paths

**Task ID:** `P17-IMPLEMENT-03-20260925-WIRE-ACTING-FOR-WRITE-PATHS`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
**Starting SHA:** `d6f45489919f9370438c2817b6ca3bb4e76c8bea` (verified as actual HEAD before any change)
**Ending SHA:** this report's commit.
**Nature:** IMPLEMENTATION. No UI, no Scope 2/3 calculation, no migration, no RLS change, no production contact.

---

## 1. Task ID

`P17-IMPLEMENT-03-20260925-WIRE-ACTING-FOR-WRITE-PATHS`

## 2. Starting SHA

`d6f45489919f9370438c2817b6ca3bb4e76c8bea` — the P17-IMPLEMENT-02 head, confirmed with
`git rev-parse HEAD` before any edit. The only pre-existing working-tree change was `.gitignore`.

## 3. Ending SHA

The commit carrying this report (commit 4 in §4); its parent is `a4b9a2f`.

## 4. Commit SHA(s)

| # | SHA | Message | Contents |
|---|---|---|---|
| 1 | `df52233` | `feat(p17): accept server-resolved acting-for provenance on the supplier write` | `backend/data/suppliers.py` |
| 2 | `eb402d5` | `feat(p17): attribute supplier creation to the resolved accounting context` | `backend/api/v3_suppliers.py` |
| 3 | `a4b9a2f` | `test(p17-03): cover acting-for attribution on the supplier write path` | 1 test module (7 tests) |
| 4 | *(this report)* | `docs(p17): record IMPLEMENT-03 report` | this report |

**Not pushed.** No amend/rebase/reset; all prior P17 history preserved.

## 5. Actual write-path mapping discovered

This is the principal deliverable of the mandatory discovery phase, and it changes the task's premise. **Only
one of the eight carriers has a real, reachable, application-level write call site that an authenticated actor
drives.** The evidence, per carrier:

| # | Carrier | Real write site found | Callers | Verdict |
|---|---|---|---|---|
| 1 | `customer_documents` | `DocumentsRepository.create_from_upload` (asyncpg INSERT) and `DocumentsRepository.save` (upsert INSERT) | `create_from_upload`: **only `tests/integration/*`**. `save`: **no callers in `api/`, `services/`, `engines/`, `routes/`, `workers/`** | **NO REACHABLE CALL SITE** |
| 2 | `suppliers` | `SuppliersRepository.create` | **exactly one: `api/v3_suppliers.py:72`** (authenticated route) | **WIREABLE — WIRED** |
| 3 | `calculation_snapshots` | snapshot INSERT in `data/emissions_logs.py` | no `logs.create(` / snapshot-create caller resolvable in `api/`, `services/`, `engines/` under the names searched | **NOT LOCATED IN BUDGET** |
| 4 | `emissions_logs` | `EmissionsLogsRepository.create` (`data/emissions_logs.py:237`) | same as #3 | **NOT LOCATED IN BUDGET** |
| 5 | `evidence_line_items` | module-level `_INSERT_SQL` used by `materialise_for_item` (l.333) and `backfill` (l.473) | **no callers in `api/`, `services/`, `engines/`, `workers/`, `routes/`** | **NO REACHABLE CALL SITE** |
| 6 | `review_audit_trail` | **none — the table is populated by a DATABASE TRIGGER** (`supabase/migrations/20260805000000_rc2_triggers.sql`, audit-trigger list including `review_audit_trail`) | application code only **reads** it (`routes/admin/review_history.py:114`, `:146`) | **TRIGGER-OWNED — NOT AN APPLICATION WRITE PATH** |
| 7 | `review_assignment_history` | written via the **Supabase PostgREST client** (not asyncpg): `routes/admin/workload.py:291`, `routes/admin/assignments.py:319` | those two authenticated admin routes | **WIREABLE — NOT WIRED (see §12, §20)** |
| 8 | `report_versions` | `ReportVersionsRepository.create` (`data/report_versions.py:59`, INSERT l.103) | **two: `api/v3_reports.py:328`, `:918`** | **WIREABLE — NOT WIRED (see §13, §20)** |

### 5.1 What this means

Three of the eight carriers (#1, #5, #6) **cannot be wired by this task at all** — not for lack of effort, but
because there is no application write path to wire:

- `review_audit_trail` is **trigger-owned**. The trigger fires on row changes and has no access to the acting-for
  context (no session-variable propagation exists in this codebase), so the attribution the architecture wanted
  on this table cannot be supplied by the application through this table. The authoritative durable acting-for
  record for review actions is therefore the **`audit_trail` ledger (carrier 9, already wired in
  IMPLEMENT-02)**, which carries `actor_organization_id` / `acting_for_organization_id` for every audited
  review action. **Decision (permitted by the task's ambiguity rule): follow the existing P17 contract, do not
  change the trigger, and treat the audit ledger as the durable authoritative source.**
- `customer_documents.create_from_upload` is exercised **only by integration tests**; `save` has no caller in
  the application layer. `evidence_line_items.materialise_for_item` / `backfill` likewise have no caller in
  `api/`, `services/`, `engines/`, `routes/` or `workers/`. These may be invoked by an out-of-process worker,
  a script, or a path I could not locate within this task's budget — **and adding attribution to a call site
  that is not on the production path is exactly what the task forbids** ("Do NOT create fake/demo-only call
  sites"). So they were left unwired and are reported as unresolved rather than papered over.

I deliberately did **not** invent call sites, and I did **not** mark a carrier wired because its columns exist.

## 6. Customer-document implementation

**NOT WIRED — no reachable application write path (§5).** The columns
(`actor_organization_id`, `acting_for_organization_id`) exist on `customer_documents` from the P17-A migration
and are addressable through the IMPLEMENT-02 carrier allowlist (`POST /api/v3/accounting/acting-for/attribute`
with `carrier: "customer_document"`), but the document **creation** flow does not resolve or persist
attribution. Document extraction semantics were not touched.

## 7. Supplier implementation (the one carrier genuinely WIRED)

Two additive changes, both backwards-compatible:

**`data/suppliers.py::SuppliersRepository.create`** gained an optional
`provenance: Optional[dict] = None` parameter. When supplied, `actor_organization_id` and
`acting_for_organization_id` are written **inside the same INSERT** as the row (parameters `$12`/`$13`, with
`NULLIF(...,'')::uuid`). When `None` — every pre-existing caller and every background/system write — both
columns stay NULL, so behaviour is byte-for-byte unchanged and no attribution is guessed. A test asserts the
parameter's default is `None`.

**`api/v3_suppliers.py::create_supplier`** now resolves the accounting context **before** the write:

1. the pre-existing `ensure_org_access(current_user, payload.organization_id)` is retained unchanged;
2. `ensure_record_owner_authorized(current_user, repos, payload.organization_id)` re-authorises the actor
   against the **data-owning organisation** and returns the server-resolved context;
3. `repos.suppliers.create(..., provenance=context.provenance_columns())`;
4. `record_acting_for_attribution(...)` writes the attribution to the existing **audit ledger**.

**Supplier resolution rules were not changed.** No matching, reuse or duplicate-prevention behaviour was
altered; the only change is that the row now carries attribution and the audit ledger records it.

**Discovered blocker (documented, not worked around).** `POST /api/v3/suppliers` is gated by the
pre-existing `require_org_admin()`, which admits only an internal CarbonTally admin or an organisation member
with role `owner`/`admin`. A consultant firm member therefore cannot reach this route at all — the refusal
happens in the P16 dependency before the accounting context is resolved. **Widening that gate would change
existing business behaviour, which this task forbids**, so it was left as-is and the limitation is recorded in
§20 and §21. A test proves the separation: the same consultant actor + client organisation **is** authorised by
the P17 accounting context (`resolve_accounting_context` returns the delegated acting-for organisation and
`is_delegated=True`), and a second test proves the consultant's own firm organisation resolves with kind
`CONSULTANT_TEAM_FOR_FIRM`. So the blocker is the route's P16 gate, not the P17 layer.

## 8. Calculation-snapshot implementation

**NOT WIRED.** The snapshot INSERT exists at `data/emissions_logs.py` (l.711), but no caller of a snapshot- or
log-creation method could be resolved in `api/`, `services/`, `engines/` or `routes/` by the names searched
within this task's budget. **Nothing about `request_id`, idempotency, factor precedence, the factor year
guard, the factor scope guard, invalidation or supersession was touched** — there was no edit to make, and
making a speculative one would have risked the P16 guarantees the task requires me to preserve.

## 9. Emissions-log implementation

**NOT WIRED**, for the same reason as §8. `EmissionsLogsRepository.create` (l.237) exists and is addressable
through the carrier allowlist, but no authenticated application caller was located. The consistency
requirement (a log cannot be attributed to a different acting-for organisation than its snapshot) was
therefore **not implemented**, and is recorded as remaining work in §20 — I am not claiming consistency that
does not exist.

## 10. Evidence-line-item implementation

**NOT WIRED — no reachable application call site (§5).** `materialise_for_item` and `backfill` have no caller
in `api/`, `services/`, `engines/`, `routes/` or `workers/`. Source lineage was not touched and **no source
line or provenance was fabricated**.

## 11. Review-audit-trail implementation

**NOT APPLICABLE — trigger-owned table.** `review_audit_trail` is written by the RC2 audit trigger
(`20260805000000_rc2_triggers.sql`); the application only reads it. The trigger cannot see an acting-for
context, and no session-propagation mechanism exists in this codebase to give it one. Per the task's ambiguity
rule the P17 contract was followed and P16 behaviour preserved: the trigger is unchanged, and the
**authoritative durable acting-for record for review actions remains the audit ledger** (carrier 9, wired in
IMPLEMENT-02), which records actor organisation, acting-for organisation, owner, action, entity and timestamp
for every audited review action.

## 12. Review-assignment-history implementation

**NOT WIRED — but this is the clearest remaining opportunity.** Unlike the asyncpg repositories, this table is
written through the **Supabase PostgREST client** at two authenticated admin routes:
`routes/admin/workload.py:291` and `routes/admin/assignments.py:319`. Both have an authenticated actor and an
organisation context available, so each is a small, well-defined change (resolve the accounting context for the
assignment's organisation, add the two columns to the existing payload, and audit). It was **not** completed
because the budget was consumed by the discovery phase — which was mandatory and which produced the finding
that reframes the task. Recorded as the top remaining item in §20.

## 13. Report-version implementation

**NOT WIRED — two clean call sites identified.** `ReportVersionsRepository.create`
(`data/report_versions.py:59`) is called from exactly two places, both authenticated:
`api/v3_reports.py:328` and `api/v3_reports.py:918`. The repository already has the pattern needed (an
explicit `create` with named parameters), so wiring is the same shape as the supplier change: add the optional
`provenance` parameter to the INSERT, resolve the context in each route, and audit. Not completed for the same
budget reason as §12. No new reporting functionality was implemented.

## 14. Acting-for persistence details

The persistence mechanism is the one built in IMPLEMENT-02 and reused unchanged — **no duplicate write
mechanism was created**:

- `domain/acting_for.py` / `api/accounting_context_auth.py` resolve the context server-side;
- `AccountingContext.provenance_columns()` produces the exact two-column payload
  (`actor_organization_id`, `acting_for_organization_id`) shared by all nine ARCH-04 §10.3 carriers;
- `data/accounting_context.py` owns the closed `ACTING_FOR_CARRIERS` allowlist and the writer;
- `api/audit_helpers.record_acting_for_attribution` records the attribution on the existing audit ledger.

For the supplier path the payload is written **in the row INSERT itself** rather than by a second UPDATE,
which is strictly better for the consistency requirement: attribution cannot be partially applied, and there
is no window in which a row exists without its attribution.

## 15. Data-owner enforcement

For the wired carrier the **data-owning organisation is the authority**:
`ensure_record_owner_authorized(current_user, repos, payload.organization_id)` authorises the actor against the
owner before any write, and the persisted acting-for value comes from that resolved context. Consequences,
proven by test:

- writing an unrelated organisation's supplier returns **403 and writes nothing** (no row, no audit entry);
- a forged `acting_for_organization_id` in the request body cannot change the persisted attribution (the field
  is not part of `SupplierCreate`, and nothing from the body reaches the attribution);
- actor and acting-for organisations are never confused: for a consultant they are *different* values (firm vs
  client), for a member they are the same value.

## 16. Security / authorization behavior

| Task §Security case | Status |
|---|---|
| 1 direct customer writing own record | Proven for the **supplier** carrier (201 + own-org attribution). Not applicable to documents (carrier not wireable) |
| 2 consultant writing for authorized client | Proven at the **accounting-context** layer; **blocked at the supplier route by the pre-existing `require_org_admin()` gate** (§7) |
| 3 consultant writing for unauthorized client | **403**, nothing written (proven) |
| 4 consultant writing for own organization | Proven at the **accounting-context** layer (`CONSULTANT_TEAM_FOR_FIRM`) |
| 5 client cannot write another client's records | **403**, nothing written, no audit entry (proven) |
| 6 forged `acting_for_organization_id` rejected | Proven — ignored; the server value is persisted |
| 7 data-owner override rejected | Proven — owner authorisation is the gate |
| 8 acting-for cannot bypass tenant isolation | Proven for the wired carrier; the P17 layer was proven for all personas in IMPLEMENT-02 |
| 9 inactive consultant-client relationship rejected | Proven at the accounting-context layer and parametrized over `pending`/`suspended`/`ended`/`inactive` |
| 10 attribution cannot be changed by manipulating a downstream payload | Proven — the payload cannot carry attribution and the value is written in the same INSERT |

**No RLS was changed, weakened or bypassed. No service-role bypass was used to make a test pass.** One honest
gap: cases 2 and 4 could not be demonstrated **end-to-end through the supplier HTTP route** because of the
pre-existing admin gate, so those rows say "proven at the accounting-context layer" rather than claiming a
route-level success that was not achieved.

## 17. Transaction / consistency behavior

- The supplier attribution is written **inside the same INSERT** as the supplier row, so the
  "row exists but attribution is missing" partial state is impossible for that carrier.
- The audit ledger write is **best-effort by design** (`record_acting_for_attribution` swallows and logs audit
  failures), matching the existing `api/audit_helpers` convention so audit can never fail a business write. The
  consequence — stated plainly — is that a supplier row can be attributed while its audit entry is missing if
  the audit insert fails. That is the established trade-off of this codebase, not a new one.
- For the **unwired** carriers the consistency requirement (snapshot vs emissions log, document vs evidence) is
  **not satisfied and not claimed**. There is no cross-record attribution to be inconsistent *yet*, because
  neither record in each pair is attributed.

## 18. Tests executed with exact counts/results

| Suite | Result |
|---|---|
| `tests/unit/api/test_p17_03_supplier_write_path.py` (new) | **7 tests, 7 passed, 0 failed** |
| `tests/unit/api -k supplier` (existing supplier surface) | **passed** — no regression |
| `tests/unit/api/test_p17_02_*` (IMPLEMENT-02 suites) | **passed** — unaffected |

The 7 new tests exercise the **real route** through `TestClient` — context resolution → repository call →
persisted attribution → audit — not the attribution helper in isolation:

1. direct customer supplier write records acting-for own organisation (**201**, exact provenance payload, audit
   entry carrying acting-for + owner + entity + action);
2. writing an unrelated organisation's supplier → **403**, no row, no audit entry;
3. forged `acting_for_organization_id` in the payload does not change the attribution;
4. consultant cannot reach the route through the existing admin gate (**403**, nothing written) — the
   documented blocker;
5. the accounting context **does** authorise consultant delegation for the same actor + client (delegated
   acting-for, `is_delegated=True`);
6. consultant own firm organisation resolves with kind `CONSULTANT_TEAM_FOR_FIRM`;
7. the repository's `provenance` parameter defaults to `None`, so P16 callers are unchanged.

**No superficial test that merely calls the helper.** The fakes replace only the database, not the route.

## 19. P16 regression results

**NO REGRESSIONS OBSERVED in the affected surface.** The only production-code change to an existing write path
is the supplier repository and its route, and both are strictly additive:

- the repository's new parameter is optional and defaults to `None`, asserted by test — every pre-existing
  caller (including `tests/integration/*`) behaves identically and writes NULL attribution;
- the route retains its existing `ensure_org_access` guard and its existing response shape; the added
  authorisation is *additional* and fail-closed, and the 403 tests prove nothing is written when it fails.

**Budget limitation, disclosed honestly:** a full 3542-test suite re-run was **not** completed within this
task's budget. The regression evidence above is limited to the directly affected suites plus the previously
established baseline. **A full-suite run is required before any verdict beyond PARTIAL.** No existing test was
modified, weakened, skipped or deleted; the only test file added is the new P17-03 module.

## 20. Remaining unimplemented paths

In priority order, with the exact site to change:

1. **`review_assignment_history`** — `routes/admin/workload.py:291`, `routes/admin/assignments.py:319`
   (Supabase-client writes on authenticated admin routes). Highest value: real call sites, actor and
   organisation already available.
2. **`report_versions`** — `data/report_versions.py::create` INSERT (l.103) plus callers
   `api/v3_reports.py:328`, `:918`. Same shape as the supplier change.
3. **`calculation_snapshots` + `emissions_logs`** — `data/emissions_logs.py` (l.711 snapshot INSERT, l.237
   `create`). **The caller must be identified first**; until then neither can be attributed and the
   snapshot/log consistency requirement cannot be met.
4. **`customer_documents`** — the real creation path must be identified. `create_from_upload` is test-only and
   `save` has no application caller; production upload happens elsewhere (likely a route or worker not reached
   in budget).
5. **`evidence_line_items`** — `materialise_for_item` / `backfill` have no caller in the searched layers; the
   real trigger of materialisation must be identified.
6. **`review_audit_trail`** — **not an application write path** (trigger-owned). Requires either a trigger
   change (a migration, outside this task's scope) or acceptance that the audit ledger is the durable source.
   **A PO/architecture decision is needed here, not an implementation task.**

Also outstanding from IMPLEMENT-02: no UI; no Scope 2/3 calculation; `consolidation_approach` cannot be set by
any endpoint (so DC-07 fails closed for categories 8/13); `consultant_profiles.organization_id` is readable but
not writable through the API.

## 21. Known risks

| # | Risk | Severity |
|---|---|---|
| R1 | **Only 1 of 8 carriers is wired.** Attribution exists for suppliers and the audit ledger only; any expectation of complete acting-for coverage is currently unmet. | **High** |
| R2 | **Three carriers have no application write path** (trigger-owned `review_audit_trail`; test-only or unreachable `customer_documents` / `evidence_line_items`). "Wiring" them may be impossible without a schema/trigger decision. | **High** (needs a decision) |
| R3 | The supplier route's `require_org_admin()` gate makes **consultant-delegated supplier creation impossible**, although the P17 layer would allow it. | **Medium** |
| R4 | Audit writes are best-effort, so a row can be attributed while its audit entry is missing. | Medium (pre-existing pattern) |
| R5 | The record-owner check is an application-layer guard, not a database constraint; a caller bypassing `resolve_accounting_context` is unprotected. | Medium |
| R6 | Full-suite regression verification was not completed in-budget (§19). | Medium |
| R7 | `actor_organization_id` on the supplier row duplicates information also held in the audit ledger. Accepted deliberately so the row is self-describing without a join. | Low |

## 22. Production-contact statement

**NO PRODUCTION SYSTEM WAS CONTACTED.**

- No production database, migration, credential, deployment or customer data.
- No external production API call; no push to any remote; no release path triggered.
- **No database was opened at all** — the tests use in-memory fakes and FastAPI's `TestClient`, and no
  migration was added or applied. The Demo Lab, `carbontally_qa_phase8`, `carbontally_test` and every other
  persistent local database were untouched.
- The destructive integration harness was **not run**.

## 23. Final implementation verdict

```
P17_IMPLEMENTATION_PARTIAL
```

**Why PARTIAL.** The task's verdict rule is explicit: use `P17_IMPLEMENTATION_COMPLETE` *"only if all eight
required write paths are genuinely wired and tested."* **One of eight is wired and tested** (suppliers); the
audit ledger was already wired by IMPLEMENT-02; the remaining six are not:

- 3 wireable but not completed in budget (`review_assignment_history`, `report_versions`, and the snapshot/log
  pair once its caller is identified);
- 3 with **no application write path to wire at all** (`review_audit_trail` is trigger-owned;
  `customer_documents` and `evidence_line_items` have no reachable application call site in the searched
  layers).

Claiming COMPLETE would be false, and the task instructs explicitly: *"Do not inflate the verdict."*

**What is genuinely delivered and verified:**

- the **mandatory write-path discovery mapping** (§5) for all eight carriers with file:line evidence — the
  deliverable that reframes the task and makes the remaining work deterministic rather than speculative;
- the **supplier write path wired end-to-end** and tested through the real route: server-resolved context →
  same-INSERT attribution → audit ledger, with 403-and-nothing-written on refusal and forgery resistance;
- a **reusable, backwards-compatible provenance pattern** (`provenance: Optional[dict] = None` plus a
  same-statement write) that the remaining carriers can adopt directly;
- **two concrete blockers documented rather than worked around**: the trigger-owned `review_audit_trail` and the
  supplier route's pre-existing admin gate. Neither was "fixed" by changing P16 behaviour, which this task
  forbids.

**What is NOT delivered:** attribution on seven of the eight record paths. No UI, no calculation, no migration,
no RLS change — all excluded by instruction.

**No `PASS`, `E2E VERIFIED` or `PRODUCTION READY` claim is made.** These are implementation tests; independent
verification remains a separate activity.




